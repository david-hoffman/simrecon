"""Independent public inputs for BASELINE-PUBLIC-FAILURES-01 only."""

import hashlib
import multiprocessing
import os
import struct
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import cast

import numpy as np

from simrecon import Otf2D, SimreconError, export_imagej


def illumination_case(source):
    """Build unit transfer and a constant specimen with z=(1+0.5j)/4."""
    steps = np.arange(4, dtype=np.float64) * (np.pi / 2)
    values = 4 + 2 * np.cos(steps) - np.sin(steps)
    images = np.broadcast_to(values[:, None, None], (4, 1, 3)).copy()
    otf = Otf2D(
        values=np.ones((1, 3), dtype=np.complex128),
        fy_per_um=np.array([0.0]),
        fx_per_um=np.array([-1 / 3, 0.0, 1 / 3]),
        pixel_size_um=(1.0, 1.0),
        origin_yx=(0, 0),
        source=source,
    )
    return images, steps, otf


def illumination_expected_gain(images, steps):
    """Solve the tiny exact represented problem using rational elimination."""
    rows = [
        [Fraction(1), Fraction(float(np.cos(step))), Fraction(float(np.sin(step)))]
        for step in steps
    ]
    observations = [Fraction(float(value)) for value in images[:, 0, 0]]
    augmented = cast(
        list[list[Fraction]],
        [
            [sum(row[i] * row[j] for row in rows) for j in range(3)]
            + [sum(row[i] * value for row, value in zip(rows, observations, strict=True))]
            for i in range(3)
        ],
    )
    for column in range(3):
        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(3):
            if row != column:
                factor = augmented[row][column]
                augmented[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(augmented[row], augmented[column], strict=True)
                ]
    dc, cosine, sine = (row[-1] for row in augmented)
    return complex(float(cosine / (2 * dc)), float(-sine / (2 * dc)))


def translation_scores(moving, reference):
    """Small finite sum from the public periodic objective; no product oracle."""
    ny, nx = reference.shape
    scale = max(float(np.max(np.abs(moving))), float(np.max(np.abs(reference))))
    scores = []
    for dy in range(-(ny // 2), (ny + 1) // 2):
        for dx in range(-(nx // 2), (nx + 1) // 2):
            total = sum(
                (
                    float(moving[(y + dy) % ny, (x + dx) % nx]) / scale
                    - float(reference[y, x]) / scale
                )
                ** 2
                for y in range(ny)
                for x in range(nx)
            )
            scores.append((total / (ny * nx)) ** 0.5)
    return np.array(scores).reshape(ny, nx)


def write_priism(path: Path, *, extension_bytes: int = 4096):
    """Genuine one-plane little-endian mode-6 Priism, independently encoded."""
    pixels = np.array([[[0, 32768, 65535], [5, 1024, 60000]]], dtype="<u2")
    header = bytearray(1024)
    struct.pack_into("<4i", header, 0, 3, 2, 1, 6)
    struct.pack_into("<3i", header, 28, 3, 2, 1)
    struct.pack_into("<3f", header, 40, 0.25, 0.5, 1.0)
    struct.pack_into("<3i", header, 64, 1, 2, 3)
    struct.pack_into("<i", header, 92, extension_bytes)
    struct.pack_into("<h", header, 96, -16224)
    struct.pack_into("<h", header, 180, 1)
    struct.pack_into("<h", header, 196, 1)
    digest = hashlib.sha256()
    chunk = bytes(range(256)) * 4096
    with path.open("wb") as stream:
        stream.write(header)
        remaining = extension_bytes
        while remaining:
            piece = chunk[: min(remaining, len(chunk))]
            stream.write(piece)
            digest.update(piece)
            remaining -= len(piece)
        stream.write(pixels.tobytes())
    config = {
        "version": 1,
        "data_kind": "spatial_image",
        "plane_axes": [],
        "plane_shape": [],
        "spatial_fields": "direct_um",
        "extended_header": "opaque" if extension_bytes else "none",
        "overrides": {},
    }
    return bytes(header), pixels, config, digest.hexdigest()


def export_source_change_child(channel, info, destination):
    """Observe owned source access without replacing any product dependency."""
    source_stat = info.source.stat()
    source_identity = (source_stat.st_dev, source_stat.st_ino)
    armed = True
    observer_incomplete_reason = None

    def observe_open(event, args):
        nonlocal armed, observer_incomplete_reason
        if not armed or event != "open":
            return
        try:
            # Accept str, bytes and Path/PathLike audit names, including relative
            # paths and aliases. File identity, not pathname spelling, selects
            # our disposable source. Integer file descriptors are not pathnames.
            candidate = os.fspath(args[0])
            candidate_stat = os.stat(candidate)
        except (TypeError, OSError):
            return
        if (candidate_stat.st_dev, candidate_stat.st_ino) != source_identity:
            return
        armed = False
        try:
            channel.send({"audit_event_ns": time.monotonic_ns()})
            if not channel.poll(10):
                observer_incomplete_reason = "owned intervention acknowledgement unavailable"
                return
            channel.recv()
        except (EOFError, OSError):
            # Resume the operation without injecting a synthetic exception.
            observer_incomplete_reason = "owned intervention channel unavailable"

    sys.addaudithook(observe_open)
    start = time.monotonic_ns()
    try:
        report = export_imagej(destination, info, block_planes=1)
    except BaseException as error:
        outcome = {
            "success": False,
            "domain_error": isinstance(error, SimreconError),
            "type": type(error).__name__,
            "code": getattr(error, "code", None),
            "message": str(error),
        }
    else:
        outcome = {"success": True, "planes_written": report.planes_written}
    finally:
        armed = False
    channel.send(
        {
            "operation_start_ns": start,
            "operation_end_ns": time.monotonic_ns(),
            "observer_incomplete_reason": observer_incomplete_reason,
            "outcome": outcome,
        }
    )
    channel.close()


def observe_operation_time_shortening(info, destination, *, shortened_size):
    """Apply one parent-owned truncation within an observed export operation."""
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=export_source_change_child, args=(child, info, destination))
    observation = {
        "mutation": None,
        "operation": None,
        "audit_event_ns": None,
        "extension_read_stage_proven": False,
        "mechanism": "owned child audit observation and parent real-file truncation",
        "incomplete_reason": None,
    }
    process.start()
    child.close()
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if parent.poll(0.1):
                try:
                    message = parent.recv()
                except EOFError:
                    observation["incomplete_reason"] = "child closed without operation evidence"
                    break
                if "audit_event_ns" in message:
                    observation["audit_event_ns"] = message["audit_event_ns"]
                    stat_before = info.source.stat()
                    header_before = info.source.read_bytes()[:1024]
                    start = time.monotonic_ns()
                    with info.source.open("r+b") as stream:
                        stream.truncate(shortened_size)
                        stream.flush()
                        os.fsync(stream.fileno())
                    end = time.monotonic_ns()
                    stat_after = info.source.stat()
                    header_after = info.source.read_bytes()[:1024]
                    observation["mutation"] = {
                        "start_ns": start,
                        "end_ns": end,
                        "actor_pid": os.getpid(),
                        "size_before": stat_before.st_size,
                        "size_after": stat_after.st_size,
                        "mtime_before_ns": stat_before.st_mtime_ns,
                        "mtime_after_ns": stat_after.st_mtime_ns,
                        "header_sha256_before": hashlib.sha256(header_before).hexdigest(),
                        "header_sha256_after": hashlib.sha256(header_after).hexdigest(),
                    }
                    parent.send("parent-owned mutation completed")
                if "operation_end_ns" in message:
                    observation["operation"] = message
                    observation["incomplete_reason"] = message["observer_incomplete_reason"]
                    break
            elif not process.is_alive():
                observation["incomplete_reason"] = (
                    "child exited without complete operation evidence"
                )
                break
        else:
            observation["incomplete_reason"] = "bounded observation deadline expired"
        process.join(timeout=2)
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join(timeout=2)
        observation["child_pid"] = process.pid
        observation["child_exitcode"] = process.exitcode
        parent.close()
        if not process.is_alive():
            process.close()
    observation["destination_exists_after"] = destination.exists()
    observation["destination_size_after"] = (
        destination.stat().st_size if destination.exists() else None
    )
    return observation
