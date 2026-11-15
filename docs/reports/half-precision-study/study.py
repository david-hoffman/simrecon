#!/usr/bin/env python3
"""HP114 finite scientific harness, outside product and test discovery.

SOURCE PREPARATION ONLY: no execution, including syntax/import checks, until the
coordinator grants the numerical window. See manifest.md for frozen formulas,
commands, branch qualification, lifecycle accounting and interpretation limits.
Each invocation selects one diagnostic row or one parent-owned workload child.
There is no batch/retry runner, growth search or environment repair. Standalone
resource and finite control methods are unexecuted source preparation v2.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import platform
import resource
import signal
import struct
import subprocess
import sys
import time
import traceback
import warnings
from fractions import Fraction
from pathlib import Path

BASE = "b344e41a8b52de76d7cbbf8450319893904c3b8f"
ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path("/workspace/work/campaign/evidence/114/study")
EXPECTED = {
    "src/simrecon/acquisition/preparation.py": (
        "2c5bb8eb536f8b1edd0c4d155da603bb66c838ce2298a899cdd6f23a3eedd0da"
    ),
    "src/simrecon/acquisition/modes.py": (
        "4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1"
    ),
    "src/simrecon/reconstruction/parameter_estimation.py": (
        "f9a924d277518cdb0717c7fe82961f3d36a480109bcbef9f8d19b42fdae7d7e8"
    ),
    "src/simrecon/reconstruction/known_parameters.py": (
        "34fbc93aa5ac9a1f4eb24b1f39ce576a1bb7770238c62cab72412de120722295"
    ),
    "src/simrecon/workflow/reconstruct.py": (
        "50a4ce199f0cceca6ba9147a1ee218441b1b5588c03beabecef95828802e28fa"
    ),
    "src/simrecon/workflow/summary.py": (
        "f0ccb2f0c566ba255eb02b0047c7000c3fe6530a0a7c797224e185d3f31ebb2e"
    ),
    "uv.lock": ("222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b"),
    "docs/contracts/half-precision-feasibility-v1.md": (
        "bb5963ce268e81dabf8773f8bce5f1b37e8153e2d18886ddef1e5766bd384284"
    ),
    "docs/packets/half-precision-study/investigator.md": (
        "712f72dec72690ed87a2a8228884e8fcecbf4185665676a93e62ee66528d1afd"
    ),
}
SHAPES = {
    "W01": (1, 1, 3, 1, 16, 16),
    "W02": (1, 3, 5, 4, 16, 16),
    "W03": (1, 3, 5, 4, 16, 16),
    "W04": (2, 3, 5, 4, 16, 16),
    "W05": (1, 3, 5, 4, 32, 32),
    "W06": (1, 3, 5, 4, 16, 16),
}
STRATEGIES = (
    "QUALIFY",
    "WIDER",
    "H1",
    "H1_PROMOTED",
    "H2_CORRECTED",
    "H2_PREPARED",
    "H2_FILTERED",
    "H2_EMBEDDED",
    "KERNEL",
    "CPU",
)
THREAD_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
OPTICS = dict(wavelength_nm=520, numerical_aperture=1.2, immersion_index=1.33)
KEEP = []  # Explicit conservative caller/conversion/result retention for RSS.
ARRAYS = {}
TIMINGS = []
np = scipy = sim = None  # Numerical imports occur only after explicit authorization.
OBSERVATION_BYTES = 65536  # Per numeric buffer, never a total-scratch ceiling.
RESOURCE_STRATEGIES = ("WIDER", "H1", "H1_PROMOTED", "PREPARED_WIDER", "PREPARED_HALF")
RECORD_LIMIT_BYTES = 4 * 1024 * 1024  # Finite JSON admission bound, not a human limit.
RESOURCE_LAUNCH_HOLD = (
    "HP114 resource launch is quarantined: campaign root's #116 Q1 in the same "
    "pinned CPython 3.13.12 raised NotImplementedError: posix_spawn: setsid "
    "unavailable on this platform, before a child PID. No retry/fallback is "
    "authorized. Await root's diagnosed accepted launch route and scoped review."
)
SNAPSHOT_SCOPES = {
    "pre_call": "after caller setup/identity; before conversion-inclusive and call clocks",
    "call_end": "after operation clock; before output observers",
    "post_observation": "after bounded output observations; before JSON serialization/teardown",
}


def digest(path):
    """Hash one file without loading its entire contents."""
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def text_file(path):
    """Read an optional operating-system text record."""
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def authorize(args):
    """Check the root receipt; provide audit evidence, not technical isolation."""
    receipt = json.loads(Path(args.grant).read_text())
    if receipt.get("authorization") != "HP114_NUMERICAL_WINDOW":
        raise RuntimeError("missing explicit root numerical-window authorization")
    if receipt.get("baseline") != BASE:
        raise RuntimeError("grant does not identify the approved public baseline")
    for key, path in (
        ("harness_sha256", __file__),
        ("manifest_sha256", Path(__file__).with_name("manifest.md")),
    ):
        if receipt.get(key) != digest(path):
            raise RuntimeError(f"grant {key} differs from frozen artifact")
    if receipt.get("environment") != "simrecon-campaign-ubuntu":
        raise RuntimeError("grant is not for pinned Ubuntu environment")
    if (args.row, args.strategy, args.repetition) not in [tuple(x) for x in receipt["runs"]]:
        raise RuntimeError("this exact finite run is not in the root grant")
    for name, expected in EXPECTED.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"material source identity changed: {name}")
    osrelease = text_file("/etc/os-release") or ""
    if "ID=ubuntu" not in osrelease and 'ID="ubuntu"' not in osrelease:
        raise RuntimeError("host is not Ubuntu; host Debian cannot qualify")
    if "24.04" not in osrelease:
        raise RuntimeError("wrong Ubuntu series; record exact point release separately")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("interpreter is not the root-provisioned per-worktree .venv")
    for key in THREAD_KEYS:
        if os.environ.get(key) != "1":
            raise RuntimeError(f"set {key}=1 before launching the fresh interpreter")
    if os.environ.get("SCIPY_ARRAY_API") not in (None, "0"):
        raise RuntimeError("unqualified SciPy array-API backend selection")
    candidate = receipt.get("candidate", {})
    if not all(
        candidate.get(key)
        for key in ("commit", "tree", "tracked_status", "integration_base", "parent")
    ):
        raise RuntimeError("missing actual candidate/base/parent attestation")
    if getattr(args, "route", "diagnostic") in ("resource", "resource-child"):
        if args.row not in SHAPES or args.strategy not in RESOURCE_STRATEGIES:
            raise RuntimeError("resource route is limited to W rows and named matched paths")
        control = receipt.get("method_control")
        if receipt.get("route") != "resource":
            raise RuntimeError("resource route lacks exact root route authorization")
        if control is None and not receipt.get("qualification_sha256", {}).get(args.row):
            raise RuntimeError(
                "resource grant must name reviewed qualification without loading it in child"
            )
        if control is not None and (
            receipt.get("control_release") is not True
            or control
            not in (
                "missing-record",
                "self-term",
                "timeout",
                "timeout-ignore-term",
                "child-error",
                "malformed-record",
                "oversized-record",
            )
        ):
            raise RuntimeError("unknown or unreleased finite lifecycle control")
        admission = receipt.get("resource_admission", {})
        if (
            admission.get("accepted") is not True
            or not admission.get("rationale")
            or len(admission.get("evidence_sha256", "")) != 64
        ):
            raise RuntimeError("root has not admitted this attempt's current headroom and method")
        if receipt.get("run_id") != args.run_id or receipt["runs"] != [
            [args.row, args.strategy, args.repetition]
        ]:
            raise RuntimeError(
                "resource grant must identify exactly one attempt, not a batch/retry"
            )
        return receipt
    if getattr(args, "route", "diagnostic") == "controls":
        if (
            receipt.get("route") != "controls"
            or receipt.get("control_release") is not True
            or (args.row, args.strategy, args.repetition) != ("K01", "KERNEL", 1)
        ):
            raise RuntimeError("finite observer controls require a separate root control grant")
        return receipt
    if args.strategy not in STRATEGIES:
        raise RuntimeError(
            "prepared-stage resource strategies cannot silently become diagnostic baselines"
        )
    if args.row in SHAPES:
        if args.strategy in ("KERNEL", "CPU"):
            raise RuntimeError("kernel strategy cannot select a workflow row")
        if args.strategy != "QUALIFY":
            qualified = json.loads(Path(args.qualification).read_text())
            if (
                qualified.get("row") != args.row
                or qualified.get("status") != "branch-qualified-oracle-review-required"
                or qualified["identities"]["harness"] != digest(__file__)
                or qualified["identities"]["manifest"]
                != digest(Path(__file__).with_name("manifest.md"))
            ):
                raise RuntimeError("missing applicable wider branch-qualification record")
            if receipt.get("qualification_sha256", {}).get(args.row) != digest(args.qualification):
                raise RuntimeError(
                    "root grant did not accept this qualification record for comparison"
                )
    elif args.strategy not in ("KERNEL", "CPU"):
        raise RuntimeError("K rows require KERNEL; CPU bounded transforms use K01 only")
    if args.strategy == "CPU" and args.row != "K01":
        raise RuntimeError("CPU feasibility is bounded to K01")
    return receipt


def timed(label, operation):
    """Record elapsed monotonic seconds even for a failed call."""
    start = time.monotonic_ns()
    try:
        return operation()
    finally:
        TIMINGS.append(dict(operation=label, seconds=(time.monotonic_ns() - start) / 1e9))


def remember(name, value):
    """Retain caller/conversion storage and name an exported array."""
    KEEP.append(value)
    ARRAYS[name] = value
    return value


def encode(value, path="record"):
    """Lossless numeric arrays are separate NPY files; no enormous JSON lists."""
    if isinstance(value, np.ndarray):
        key = f"{len(ARRAYS):05d}-{path.replace('/', '_')}"
        ARRAYS[key] = value
        return {"array": key, "shape": value.shape, "dtype": value.dtype.str}
    if dataclasses.is_dataclass(value):
        return {
            field.name: encode(getattr(value, field.name), path + "." + field.name)
            for field in dataclasses.fields(value)
        }
    if isinstance(value, dict):
        return {str(k): encode(v, path + "." + str(k)) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v, path + f".{i}") for i, v in enumerate(value)]
    if isinstance(value, np.generic):
        return encode(value.item(), path)
    if isinstance(value, complex):
        return {"real": encode(value.real), "imag": encode(value.imag)}
    if isinstance(value, float) and (not math.isfinite(value) or value == 0):
        return {"float64_bits_be": struct.pack(">d", value).hex()}
    if isinstance(value, Path):
        return str(value)
    return value


def numeric_chunks(a, dtype=None):
    """Visit C-order values with bounded slices and explicit canonical endian."""
    a = np.asarray(a)
    target = a.dtype.newbyteorder("<") if dtype is None else np.dtype(dtype)
    if target.kind not in "biufc" or target.itemsize > 16:
        raise ValueError("unsupported numeric observation kind/width")
    count = max(1, OBSERVATION_BYTES // max(a.dtype.itemsize, target.itemsize))
    with np.nditer(
        a,
        flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=["readonly"],
        op_dtypes=[target],
        order="C",
        buffersize=count,
    ) as iterator:
        for view in iterator:
            # External-loop views may exceed buffersize when no buffering is
            # needed. Slice before any conversion or byte serialization.
            for offset in range(0, view.size, count):
                yield np.asarray(view[offset : offset + count], dtype=target)


def array_identity(a):
    """Record shape/dtype/content, preserving signed zeros in canonical bytes."""
    a = np.asarray(a)
    h = hashlib.sha256()
    for values in numeric_chunks(a):
        h.update(values.tobytes(order="C"))
    return dict(
        shape=list(a.shape),
        canonical_dtype=a.dtype.newbyteorder("<").str,
        content_sha256=h.hexdigest(),
    )


def array_hash(a):
    """Hash bounded canonical C-order sample bytes outside call-only timing."""
    return array_identity(a)["content_sha256"]


def paired_chunks(a, b, dtype):
    """Keep equal-shaped operands aligned even when their strides differ."""
    target = np.dtype(dtype)
    count = max(1, OBSERVATION_BYTES // max(a.dtype.itemsize, b.dtype.itemsize, target.itemsize))
    with np.nditer(
        [a, b],
        flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=[["readonly"], ["readonly"]],
        op_dtypes=[target, target],
        order="C",
        buffersize=count,
    ) as iterator:
        for left, right in iterator:
            for offset in range(0, left.size, count):
                yield (
                    np.asarray(left[offset : offset + count], dtype=target),
                    np.asarray(right[offset : offset + count], dtype=target),
                )


def scalar_stats(a):
    """Observe signed real components and binary16 range boundaries."""
    a = np.asarray(a)
    counts = dict(
        nonfinite=0,
        negative=0,
        zeros=0,
        negative_zeros=0,
        positive_zeros=0,
        binary16_subnormal_range=0,
    )
    minimum = maximum = None
    for chunk in numeric_chunks(a):
        finite = np.isfinite(chunk)
        selected = chunk[finite]
        counts["nonfinite"] += int((~finite).sum())
        counts["negative"] += int((chunk < 0).sum())
        counts["zeros"] += int((chunk == 0).sum())
        counts["negative_zeros"] += int(((chunk == 0) & np.signbit(chunk)).sum())
        counts["positive_zeros"] += int(((chunk == 0) & ~np.signbit(chunk)).sum())
        counts["binary16_subnormal_range"] += int(
            ((np.abs(chunk) > 0) & (np.abs(chunk) < 2**-14)).sum()
        )
        if selected.size:
            low, high = float(selected.min()), float(selected.max())
            minimum = low if minimum is None else min(minimum, low)
            maximum = high if maximum is None else max(maximum, high)
    return dict(
        dtype=a.dtype.str,
        shape=a.shape,
        strides=a.strides,
        aligned=bool(a.flags.aligned),
        own=bool(a.flags.owndata),
        writeable=bool(a.flags.writeable),
        payload_bytes=a.nbytes,
        sha256=array_hash(a),
        canonical_identity=array_identity(a),
        minimum=minimum,
        maximum=maximum,
        **counts,
    )


def stats(a):
    """Observe real and imaginary component ranges separately."""
    return (
        {"real": scalar_stats(a.real), "imag": scalar_stats(a.imag)}
        if np.iscomplexobj(a)
        else scalar_stats(a)
    )


def error_metrics(reference, candidate):
    """Compare finite arrays with explicit zero-reference and sign rules."""
    a, b = np.asarray(reference), np.asarray(candidate)
    if a.shape != b.shape:
        return {"status": "shape-change", "reference": a.shape, "candidate": b.shape}
    common_dtype = "<c16" if np.iscomplexobj(a) or np.iscomplexobj(b) else "<f8"
    finite_pairs, energy_parts, squared_parts, maxima = 0, [], [], []
    nonzero_lost = {"real": 0, "imag": 0}
    sign_changed = {"real": 0, "imag": 0}
    for x, y in paired_chunks(a, b, common_dtype):
        finite = np.isfinite(x) & np.isfinite(y)
        finite_pairs += int(finite.sum())
        if not finite.all():
            continue
        delta = y - x
        energy_parts.append(float(np.vdot(x, x).real))
        squared_parts.append(float(np.vdot(delta, delta).real))
        maxima.append(float(np.max(np.abs(delta), initial=0)))
        for name, u, v in (("real", x.real, y.real), ("imag", x.imag, y.imag)):
            nonzero_lost[name] += int(((u != 0) & (v == 0)).sum())
            sign_changed[name] += int(
                ((u != 0) & (v != 0) & (np.signbit(u) != np.signbit(v))).sum()
            )
    if finite_pairs != a.size:
        return {
            "status": "nonfinite",
            "finite_pairs": finite_pairs,
            "reference": stats(a),
            "candidate": stats(b),
        }
    energy, squared = math.fsum(energy_parts), math.fsum(squared_parts)
    result = dict(
        status="finite",
        max_absolute=max(maxima, default=0.0),
        rms=math.sqrt(squared / a.size) if a.size else 0.0,
        relative_l2=math.sqrt(squared / energy) if energy else (0.0 if squared == 0 else None),
        zero_reference_rule="0 for both zero; undefined otherwise",
        reference_l2=math.sqrt(energy),
        candidate=stats(b),
    )
    for component, x, y in (("real", a.real, b.real), ("imag", a.imag, b.imag)):
        result[component] = dict(
            nonzero_to_zero=nonzero_lost[component],
            sign_changes_nonzero=sign_changed[component],
            reference=scalar_stats(x),
            candidate=scalar_stats(y),
        )
    return result


def pack(a, label):
    """Explicit little-endian IEEE half encoding; original/packed/promoted live."""
    a = np.asarray(a)
    if np.iscomplexobj(a):
        packed = np.empty((*a.shape, 2), dtype="<f2")
        packed[..., 0] = a.real
        packed[..., 1] = a.imag
        remember(label + ".packed", packed)
        promoted = np.empty(a.shape, np.complex128)
        promoted.real = packed[..., 0]
        promoted.imag = packed[..., 1]
    else:
        packed = remember(label + ".packed", a.astype("<f2"))
        promoted = packed.astype(np.float64)
    remember(label + ".promoted", promoted)
    return packed, promoted


def phases_for(row):
    """Return the frozen uniform or perturbed phase declaration."""
    p = SHAPES[row][2]
    base = 2 * np.pi * np.arange(p) / p
    if row == "W06":
        base = base + np.array([0.0, 1 / 32, -1 / 64, 1 / 128, -1 / 32])
    return np.tile(base, (SHAPES[row][1], 1))


def generator(row):
    """Independent finite multifrequency signed specimen, no stochastic seed."""
    tcount, directions, phases, nz, ny, nx = SHAPES[row]
    z, y, x = np.indices((nz, ny, nx), dtype=np.float64)
    specimen = np.full((nz, ny, nx), 3.0)
    # The finite coefficients, angles and amplitude schedule are frozen in manifest.
    for kz in range(0, min(nz, 2)):
        for ky in range(-3, 4):
            for kx in range(0, 4):
                if (kz, ky, kx) == (0, 0, 0):
                    continue
                amplitude = 32 / (1 + kx * kx + ky * ky + kz * kz)
                offset = (kx + 2 * ky + 3 * kz) * np.pi / 7
                angle = 2 * np.pi * (kx * x / nx + ky * y / ny + kz * z / nz) + offset
                specimen += amplitude * np.cos(angle)
    if row == "W06":
        angle = 2 * np.pi * (x / nx + y / ny)
        specimen = (
            8 * np.cos(angle)
            + (-8 + 2**-9) * np.cos(angle + 2**-10)
            + 2 * np.cos(2 * np.pi * y / ny)
            + np.sin(2 * np.pi * x / nx)
            + 0.25 * np.cos(2 * np.pi * z / max(nz, 1))
        )
    background = 128.0 if row == "W06" else 256.0
    angles = np.arange(directions) * np.pi / directions
    magnitude = 1.25
    carriers = magnitude * np.column_stack((np.cos(angles), np.sin(angles)))
    phi = phases_for(row)
    analytic = np.empty(SHAPES[row], np.float64)
    for t in range(tcount):
        first = 0.55 if t == 0 else 0.37
        second = 0.23 if t == 0 else 0.16
        shift = 0.0 if t == 0 else 0.41
        for d in range(directions):
            carrier_angle = 2 * np.pi * (carriers[d, 0] * x * 0.1 + carriers[d, 1] * y * 0.1)
            for p in range(phases):
                theta = carrier_angle + phi[d, p]
                illumination = 1 + first * np.cos(theta + shift)
                if phases == 5:
                    illumination = illumination + second * np.cos(2 * theta + 0.3 + 2 * shift)
                analytic[t, d, p] = background + specimen * illumination
    raw = analytic.astype(np.float32)  # Public raw boundary requires exact float32.
    remember("generator.analytic64", analytic)
    remember("generator.raw32", raw)
    remember("generator.specimen", specimen)
    return raw, analytic, carriers, background


def settings(row, background):
    """Declare every scientifically selected workflow setting."""
    orders = 2 if row == "W01" else 3
    acquisition = dict(
        acquisition_mode="2d" if row == "W01" else "3d",
        dxy_um=0.1,
        dz_um=0.0 if row == "W01" else 0.2,
        norders=orders,
        background=background,
        lateral_zoom=2.0,
        axial_zoom=1,
        phase_policy="supplied" if row == "W06" else "uniform",
        edge_pixels=0,
        equalize=False,
        equalize_z=False,
        equalize_time=False,
    )
    if row == "W06":
        acquisition["phases_rad"] = phases_for(row)
    carrier = dict(
        linespacing_um=0.8 if row == "W01" else 0.4,
        phase_start_angle_rad=0.0,
        search_carriers=row in ("W03", "W04"),
        use_time0_carriers=True,
        fit_all_phases=row != "W03",
        amplitude_floors=np.array([0.75, 0.5]) if row == "W03" else None,
    )
    filtering = dict(
        wiener=0.125,
        wiener_increment=0.0,
        suppress_singularities=False,
        output_taper="none",
        omit_kz0=False,
        filter_overlaps=True,
    )
    return acquisition, carrier, filtering


def make_transfer(orders):
    """Declare the complete constant complex analytic transfer."""
    # Constant but genuinely complex, complete radial table; complex64 exact.
    samples = np.empty((orders, 64, 64), np.complex64)
    for m in range(orders):
        samples[m] = complex(1 - m / 8, m / 32)
    remember("transfer.caller", samples)
    return sim.declare_otf(samples, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.25)


def workflow(raw, acquisition, carrier, filtering, transfer, label):
    """Call only the root-facade full workflow entry."""
    return timed(
        label,
        lambda: sim.reconstruct_workflow(
            raw,
            acquisition=acquisition,
            optics=OPTICS,
            carrier=carrier,
            filtering=filtering,
            specimen_identity={"id": "HP114-analytic-v1", "intensity_unit": "detector-counts"},
            transfer=transfer,
            transfer_identity={
                "id": "HP114-constant-complex-v1",
                "intensity_unit": "dimensionless-transfer",
                "optics": OPTICS,
            },
        ),
    )


def one_time(bands, t):
    """Construct a public one-time band record with rebased diagnostics."""
    # Public record construction, no imports/calls to private product helpers.
    names = (
        "quadratures",
        "noise_variance_factors",
        "separation_matrices",
        "phase_angles_rad",
        "frame_sums",
        "equalization_gains",
        "off_frame_sums",
        "off_equalization_gains",
        "off_quadratures",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
    )
    values = {
        name: None if getattr(bands, name) is None else getattr(bands, name)[t : t + 1]
        for name in names
    }
    return dataclasses.replace(
        bands,
        **values,
        input_shape=(1, *bands.input_shape[1:]),
        phase_policies=bands.phase_policies[t : t + 1],
        header_timestamps_after=None,
        sentinel_frames=tuple((0, *s[1:]) for s in bands.sentinel_frames if s[0] == t),
        trace=tuple(dataclasses.replace(e, time_index=0) for e in bands.trace if e.time_index == t),
    )


def compose(bands, transfer, baseline, carrier, filtering, label):
    """Compose public estimation and time-specific known reconstruction."""
    parameters = timed(
        label + ".estimate",
        lambda: sim.estimate_parameters(
            bands,
            transfer,
            initial_carriers_cyc_um=baseline.initial_carriers_cyc_um,
            **OPTICS,
            search_carriers=carrier["search_carriers"],
            use_time0_carriers=carrier["use_time0_carriers"],
            amplitude_floors=carrier["amplitude_floors"],
            fit_all_phases=carrier["fit_all_phases"],
            omit_kz0=False,
        ),
    )
    reconstructions = []
    for t in range(bands.input_shape[0]):
        single = one_time(bands, t)
        result = timed(
            label + f".known.{t}",
            lambda single=single, t=t: sim.reconstruct_known(
                single,
                transfer,
                carriers_cyc_um=parameters.carriers_cyc_um[t],
                modulation=parameters.modulation[t],
                **OPTICS,
                **filtering,
            ),
        )
        reconstructions.append(result)
    image = np.concatenate([r.image for r in reconstructions], axis=0)
    return dict(image=image, bands=bands, parameters=parameters, reconstructions=reconstructions)


def corrected_replay(raw, bands, background, quantize=False):
    """Replay the frozen camera/separation formulas without interception."""
    corrected = remember(
        "corrected.source", bands.input_scale * (raw.astype(np.float64) - background)
    )
    used = (
        timed("H2_CORRECTED.pack-unpack", lambda: pack(corrected, "corrected"))[1]
        if quantize
        else corrected
    )
    lateral = np.fft.rfft2(used, axes=(-2, -1))
    q = np.empty_like(bands.quadratures)
    for t in range(q.shape[0]):
        for d in range(q.shape[1]):
            for z in range(q.shape[3]):
                matrix = bands.separation_matrices[t, d, z]
                q[t, d, :, z, :, :-1] = np.einsum(
                    "qp,pyx->qyx", matrix, lateral[t, d, :, z, :, :-1]
                )
                q[t, d, :, z, :, -1] = lateral[t, d, : q.shape[2], z, :, -1]
            if q.shape[3] > 1:
                q[t, d] = np.fft.fft(q[t, d], axis=1)
    remember("corrected.replay.quadratures", q)
    return dataclasses.replace(
        bands, quadratures=q, frame_sums=used.sum(axis=(-2, -1), dtype=np.float64)
    )


def index_frequency(i, n):
    """Keep the positive native Nyquist endpoint."""
    return i if i <= n // 2 else i - n


def assemble_replay(filtered, raw_shape, carriers, x_um, y_um, quantize_embedding=False):
    """Source-identified assembly replay, independently checked by finite sums.

    Isolated filtered/embedded storage experiment, never a public half mode.
    """
    tcount, directions, slots, nz, ny, _ = filtered.shape
    nx = raw_shape[-1]
    output_shape = (nz, 2 * ny, 2 * nx)
    image = np.zeros((tcount, *output_shape), np.float64)
    witness = []
    for t in range(tcount):
        for d in range(directions):
            for m in range((slots + 1) // 2):
                padded = np.zeros(output_shape, np.complex128)
                for iz in range(nz):
                    kz = index_frequency(iz, nz)
                    for iy in range(ny):
                        ky = index_frequency(iy, ny)
                        for ix in range(nx):
                            kx = index_frequency(ix, nx)
                            src = (iz, iy, kx) if kx >= 0 else ((-kz) % nz, (-ky) % ny, -kx)
                            even = filtered[t, d, 0 if m == 0 else 2 * m - 1][src]
                            odd = 0j if m == 0 else filtered[t, d, 2 * m][src]
                            if kx < 0:
                                even, odd = even.conjugate(), complex(odd).conjugate()
                            padded[
                                kz % output_shape[0], ky % output_shape[1], kx % output_shape[2]
                            ] = even + 1j * odd
                label = f"embedding.{t}.{d}.{m}"
                remember(label + ".source", padded)
                if quantize_embedding:
                    used = timed(
                        label + ".pack-unpack",
                        lambda padded=padded, label=label: pack(padded, label),
                    )[1]
                else:
                    used = padded
                spatial = (
                    np.fft.ifft2(used[0], norm="forward")[None]
                    if nz == 1
                    else np.fft.ifftn(used, norm="forward")
                )
                # u(0)=sum F(k), independent of any FFT. Also one nonzero coordinate.
                for point in ((0, 0, 0), (0, 1, 2)):
                    real_terms, imag_terms = [], []
                    for index in np.ndindex(used.shape):
                        angle = (
                            2
                            * math.pi
                            * sum(index[j] * point[j] / output_shape[j] for j in range(3))
                        )
                        value = complex(used[index]) * complex(math.cos(angle), math.sin(angle))
                        real_terms.append(value.real)
                        imag_terms.append(value.imag)
                    finite = complex(math.fsum(real_terms), math.fsum(imag_terms))
                    witness.append(
                        dict(
                            site=label,
                            point=point,
                            finite_sum=finite,
                            transform=complex(spatial[point]),
                            sum_absolute_terms=math.fsum(
                                math.hypot(a, b)
                                for a, b in zip(real_terms, imag_terms, strict=True)
                            ),
                        )
                    )
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * m
                        * (carriers[d, 0] * x_um[None, :] + carriers[d, 1] * y_um[:, None])
                    )
                    image[t] += 2 * (spatial * np.exp(1j * phase)).real
    return image, witness


def exact_inverse(matrix):
    """Exact rational Gauss-Jordan inverse of declared binary64 matrix values."""
    n = len(matrix)
    a = [
        [Fraction.from_float(float(v)) for v in row] + [Fraction(int(i == j)) for j in range(n)]
        for i, row in enumerate(matrix)
    ]
    for column in range(n):
        pivot = next(i for i in range(column, n) if a[i][column])
        a[column], a[pivot] = a[pivot], a[column]
        factor = a[column][column]
        a[column] = [v / factor for v in a[column]]
        for i in range(n):
            if i != column:
                factor = a[i][column]
                a[i] = [v - factor * w for v, w in zip(a[i], a[column], strict=True)]
    return np.array([[float(v) for v in row[n:]] for row in a], np.float64)


def oracle_checks(raw, analytic, baseline, row, background):
    """Observe independent finite sums and exact finite-matrix inverses."""
    bands = baseline.bands
    replay = corrected_replay(raw, bands, background)
    phase_checks = []
    p, slots = raw.shape[2], bands.quadratures.shape[2]
    for d in range(raw.shape[1]):
        angles = phases_for(row)[d]
        design = np.array(
            [
                [1 / p]
                + [
                    v
                    for m in range(1, (slots + 1) // 2)
                    for v in (2 * math.cos(m * a) / p, 2 * math.sin(m * a) / p)
                ]
                for a in angles
            ]
        )
        left = bands.separation_matrices[0, d, 0]
        # Both routes resolve I against this scaled forward design.
        target = np.eye(slots)
        residual = (
            np.array(
                [
                    [
                        math.fsum(float(left[i, k]) * float(design[k, j]) for k in range(p))
                        for j in range(slots)
                    ]
                    for i in range(slots)
                ]
            )
            - target
        )
        exact = exact_inverse(design)

        def row_energy(rows):
            return math.fsum(float(v) * float(v) for value in rows for v in value) / p

        independent_noise = (
            np.array(
                [row_energy(exact[0:1])]
                + [row_energy(exact[2 * m - 1 : 2 * m + 1]) for m in range(1, (slots + 1) // 2)]
            )
            if row == "W06"
            else np.ones((slots + 1) // 2)
        )
        observed_row_noise = np.array(
            [row_energy(left[0:1])]
            + [row_energy(left[2 * m - 1 : 2 * m + 1]) for m in range(1, (slots + 1) // 2)]
        )
        phase_checks.append(
            dict(
                direction=d,
                condition=float(np.linalg.cond(design)),
                finite_sum_left_residual=residual,
                exact_rational_inverse=exact,
                source_left_vs_exact=error_metrics(exact, left),
                independent_noise=independent_noise,
                observed_row_noise=observed_row_noise,
                source_noise_error=error_metrics(
                    independent_noise, bands.noise_variance_factors[0, d]
                ),
                noise_scope=(
                    "uniform contract gives one; supplied squared inverse row sums/P, "
                    "scalar fsum observer"
                ),
            )
        )
    # Direct compensated phase/spatial sums, selected signed Fourier coordinates.
    corrected = bands.input_scale * (raw.astype(np.float64) - background)
    fourier_checks = []
    nz, ny, nx = raw.shape[-3:]
    for d in range(raw.shape[1]):
        for slot in (0, 1, 2):
            for kz, ky, kx in ((0, 0, 0), (0, 1, 1), (nz - 1, ny - 1, nx // 2)):
                terms = []
                for iz, iy, ix in np.ndindex((nz, ny, nx)):
                    if kx == nx // 2:
                        value = float(corrected[0, d, slot, iz, iy, ix])
                    else:
                        value = math.fsum(
                            float(bands.separation_matrices[0, d, iz, slot, p0])
                            * float(corrected[0, d, p0, iz, iy, ix])
                            for p0 in range(p)
                        )
                    angle = -2 * math.pi * (kz * iz / nz + ky * iy / ny + kx * ix / nx)
                    terms.append(value * complex(math.cos(angle), math.sin(angle)))
                expected = complex(
                    math.fsum(v.real for v in terms), math.fsum(v.imag for v in terms)
                )
                fourier_checks.append(
                    dict(
                        direction=d,
                        slot=slot,
                        index=(kz, ky, kx),
                        finite_sum=expected,
                        prepared=complex(bands.quadratures[0, d, slot, kz, ky, kx]),
                        sum_absolute_terms=math.fsum(abs(v) for v in terms),
                    )
                )
    assembly_checks = []
    for t, known in enumerate(baseline.reconstructions):
        replay_image, witnesses = assemble_replay(
            known.filtered_quadratures,
            (1, *raw.shape[1:]),
            baseline.parameters.carriers_cyc_um[t],
            known.x_um,
            known.y_um,
        )
        assembly_checks.append(
            dict(
                time=t,
                formula_replay_vs_public=error_metrics(known.image, replay_image),
                finite_inverse_sums=witnesses,
            )
        )
    return dict(
        generator_float32_cast_error=error_metrics(analytic, raw),
        phase=phase_checks,
        preparation_replay_error=error_metrics(bands.quadratures, replay.quadratures),
        finite_forward_sums=fourier_checks,
        assembly=assembly_checks,
        scope=(
            "finite sums validate mapping sign/scale, not physical recovery; "
            "residuals require review"
        ),
    )


def decision_projection(parameters):
    """Keep ordered discrete outcomes separate from continuous fit values."""
    names = (
        "stage",
        "orders",
        "integer_peak_xy",
        "x_offset_status",
        "y_offset_status",
        "alias_decisions",
        "branch",
        "strict_improvement",
        "status",
        "order",
        "floor_applied",
        "phase_replaced",
        "source_time",
        "remake_overlaps",
    )
    return dict(
        branches=parameters.branches,
        ordered_events=[
            dict(
                kind=e.kind,
                time=e.time_index,
                direction=e.direction_index,
                details={k: v for k, v in e.details if k in names},
            )
            for e in parameters.trace
        ],
    )


def parameter_comparison(a, b, shape):
    """Report carrier, modulation and exact decision changes."""
    ca, cb = a.carriers_cyc_um, b.carriers_cyc_um
    ma, mb = a.modulation, b.modulation
    valid = (np.abs(ma) != 0) & (np.abs(mb) != 0)
    wrapped = np.full(ma.shape, np.nan)
    wrapped[valid] = np.angle(mb[valid] * np.conjugate(ma[valid]))
    return dict(
        carrier_cyc_um=error_metrics(ca, cb),
        carrier_bin_components=(cb - ca) * np.array([shape[-1] * 0.1, shape[-2] * 0.1]),
        modulation=error_metrics(ma, mb),
        raw_modulation=error_metrics(a.raw_modulation, b.raw_modulation),
        amplitude_error=np.abs(mb) - np.abs(ma),
        wrapped_phase_error_rad=wrapped,
        phase_defined=valid,
        decisions_reference=decision_projection(a),
        decisions_candidate=decision_projection(b),
        decisions_equal=encode(decision_projection(a)) == encode(decision_projection(b)),
    )


def expected_branches(row):
    """Name the intended wider known/search/reuse routes before observation."""
    t, d = SHAPES[row][:2]
    return tuple(
        tuple(
            "searched"
            if row in ("W03", "W04") and i == 0
            else "time0-reused"
            if row == "W04"
            else "known"
            for _ in range(d)
        )
        for i in range(t)
    )


def public_boundaries(raw, acquisition, carrier, filtering, transfer, background, row):
    """Check selected same-value ownership and invalid public-input boundaries."""
    result = {}
    if row != "W01":
        return result
    # Both examples preserve values, source ownership and exact float32 representation.
    wide = np.zeros((*raw.shape[:-1], raw.shape[-1] * 2), np.float32)
    wide[..., ::2] = raw
    strided = remember("boundary.strided", wide[..., ::2])
    strided.flags.writeable = False
    contiguous = remember("boundary.readonly", raw.copy())
    contiguous.flags.writeable = False
    for name, value in (("strided-readonly", strided), ("contiguous-readonly", contiguous)):
        result[name] = workflow(
            value, acquisition, carrier, filtering, transfer, "boundary." + name
        ).image
    half = remember("boundary.half", raw.astype(np.float16))
    result["half_workflow"] = workflow(
        half, acquisition, carrier, filtering, transfer, "boundary.half.workflow"
    ).image
    prep_options = {k: v for k, v in acquisition.items() if k != "phase_policy"}
    result["half_acquisition_dtype"] = sim.prepare_acquisition_bands(
        half, **prep_options
    ).quadratures.dtype.str
    # prepare_bands is intrinsically 3D; use W02 for its chosen accepted half path later.
    bad = raw.copy()
    bad.flat[0] = np.nan
    for name, value in (("nonfinite", bad), ("unsupported-shape", raw[..., 0])):
        try:
            workflow(value, acquisition, carrier, filtering, transfer, "boundary." + name)
        except Exception as error:
            result[name] = failure(error, "expected-public-boundary")
        else:
            result[name] = {"unexpected_success": True}
    return result


def run_workflow(args):
    """Execute one finite diagnostic comparison, retaining its wider reference."""
    raw, analytic, nominal_carriers, background = generator(args.row)
    acquisition, carrier, filtering = settings(args.row, background)
    transfer = make_transfer(acquisition["norders"])
    KEEP.append(transfer)
    baseline_start = time.monotonic_ns()
    baseline = workflow(raw, acquisition, carrier, filtering, transfer, "wider.workflow")
    baseline_inclusive = (time.monotonic_ns() - baseline_start) / 1e9
    KEEP.append(baseline)
    if baseline.parameters.branches != expected_branches(args.row):
        raise RuntimeError("study-fixture: wider intended branches not reached")
    if not np.isfinite(baseline.image).all() or not (baseline.image < 0).any():
        raise RuntimeError("study-fixture: wider image did not demonstrate finite signed negatives")
    base = dict(
        image=baseline.image,
        bands=baseline.bands,
        parameters=baseline.parameters,
        reconstructions=baseline.reconstructions,
    )
    if args.strategy == "QUALIFY":
        qualification = dict(
            status="branch-qualified-oracle-review-required",
            wider=baseline,
            nominal_generator_carriers_cyc_um=nominal_carriers,
            independent_oracles=oracle_checks(raw, analytic, baseline, args.row, background),
            public_boundaries=public_boundaries(
                raw, acquisition, carrier, filtering, transfer, background, args.row
            ),
        )
        if args.row == "W02":
            half = remember("prepare_bands.half", raw.astype(np.float16))
            options = {
                k: v
                for k, v in acquisition.items()
                if k not in ("phase_policy", "acquisition_mode")
            }
            qualification["half_prepare_bands"] = sim.prepare_bands(half, **options)
        summary = timed(
            "wider.summary",
            lambda: sim.reconstruct_summary(
                raw,
                acquisition=acquisition,
                optics=OPTICS,
                carrier=carrier,
                filtering=filtering,
                specimen_identity={"id": "HP114-analytic-v1", "intensity_unit": "detector-counts"},
                transfer=transfer,
                transfer_identity={
                    "id": "HP114-constant-complex-v1",
                    "intensity_unit": "dimensionless-transfer",
                    "optics": OPTICS,
                },
            ),
        )
        KEEP.append(summary)
        qualification["summary"] = summary
        qualification["summary_compatibility"] = dict(
            image=error_metrics(baseline.image, summary.image),
            carrier=error_metrics(baseline.parameters.carriers_cyc_um, summary.carriers_cyc_um),
            modulation=error_metrics(baseline.parameters.modulation, summary.modulation),
            branches_equal=baseline.parameters.branches == summary.branches,
        )
        return qualification
    begin = time.monotonic_ns()
    if args.strategy in ("H1", "H1_PROMOTED"):
        half, promoted = timed("H1.pack-unpack", lambda: pack(raw, "H1.raw"))
        candidate_result = workflow(
            half if args.strategy == "H1" else promoted,
            acquisition,
            carrier,
            filtering,
            transfer,
            "candidate.workflow",
        )
        KEEP.append(candidate_result)
        candidate = dict(
            image=candidate_result.image,
            bands=candidate_result.bands,
            parameters=candidate_result.parameters,
            reconstructions=candidate_result.reconstructions,
        )
        scope = "public full workflow; H1 caller half storage with wider computation"
    elif args.strategy in ("H2_CORRECTED", "H2_PREPARED"):
        if args.strategy == "H2_CORRECTED":
            bands = timed(
                "corrected.formula-replay",
                lambda: corrected_replay(raw, baseline.bands, background, True),
            )
        else:
            _, q = timed(
                "prepared.pack-unpack", lambda: pack(baseline.bands.quadratures, "prepared")
            )
            bands = dataclasses.replace(baseline.bands, quadratures=q)
        KEEP.append(bands)
        candidate = compose(bands, transfer, baseline, carrier, filtering, "candidate")
        scope = (
            "camera/separation wider-compute formula replay + public downstream stages"
            if args.strategy == "H2_CORRECTED"
            else "public band-record pack/unpack + public downstream stages"
        )
    elif args.strategy in ("H2_FILTERED", "H2_EMBEDDED"):
        images, witnesses = [], []
        for t, known in enumerate(baseline.reconstructions):
            filtered = known.filtered_quadratures
            if args.strategy == "H2_FILTERED":
                _, filtered = timed(
                    f"filtered.{t}.pack-unpack",
                    lambda filtered=filtered, t=t: pack(filtered, f"filtered.{t}"),
                )
            image, witness = timed(
                f"assembly-replay.{t}",
                lambda filtered=filtered, t=t, known=known: assemble_replay(
                    filtered,
                    (1, *raw.shape[1:]),
                    baseline.parameters.carriers_cyc_um[t],
                    known.x_um,
                    known.y_um,
                    args.strategy == "H2_EMBEDDED",
                ),
            )
            images.append(image)
            witnesses.extend(witness)
        candidate = dict(
            image=np.concatenate(images),
            bands=baseline.bands,
            parameters=baseline.parameters,
            reconstructions=baseline.reconstructions,
            isolated_inverse_witnesses=witnesses,
        )
        scope = (
            "isolated assembly formula replay; parameters/filtering fixed wider, "
            "no public half workflow"
        )
    else:
        candidate = base
        scope = "existing wider full workflow baseline"
    inclusive = (
        baseline_inclusive if args.strategy == "WIDER" else (time.monotonic_ns() - begin) / 1e9
    )
    KEEP.append(candidate)
    return dict(
        status="completed",
        scope=scope,
        baseline=base,
        candidate=candidate,
        conversion_and_candidate_seconds=inclusive,
        image_error_count_units=error_metrics(baseline.image, candidate["image"]),
        prepared_error=error_metrics(baseline.bands.quadratures, candidate["bands"].quadratures),
        noise_error=error_metrics(
            baseline.bands.noise_variance_factors, candidate["bands"].noise_variance_factors
        ),
        frame_sum_error=error_metrics(baseline.bands.frame_sums, candidate["bands"].frame_sums),
        gain_error=error_metrics(
            baseline.bands.equalization_gains, candidate["bands"].equalization_gains
        ),
        phase_matrix_error=error_metrics(
            baseline.bands.separation_matrices, candidate["bands"].separation_matrices
        ),
        parameters=parameter_comparison(baseline.parameters, candidate["parameters"], raw.shape),
    )


def failure(error, classification):
    """Preserve exception category, operation context and cause chain."""
    return dict(
        classification=classification,
        exception=type(error).__name__,
        message=str(error),
        code=getattr(error, "code", None),
        stage=getattr(error, "stage", None),
        time_index=getattr(error, "time_index", None),
        direction_index=getattr(error, "direction_index", None),
        cause=None if error.__cause__ is None else failure(error.__cause__, classification),
    )


def fit_equal_power(values):
    """Evaluate the frozen equally spaced three-power formula witness."""
    minus, center, plus = map(float, values)
    slope = (plus - minus) / 2
    curvature = plus + minus - 2 * center
    if curvature == 0:
        return 0.0, "zero-curvature"
    result = -slope / curvature
    return (0.0, "outside-range") if abs(result) > 1.5 else (result, "fitted")


def fit_general(points):
    """Evaluate the frozen general three-point parabola witness."""
    (x1, y1), (x2, y2), (x3, y3) = points
    if len({x1, x2, x3}) != 3:
        return 0.0, "duplicate-coordinate"
    s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
    b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
    curvature = (s2 - s1) / (b2 - b1)
    return (0.0, "zero-curvature") if curvature == 0 else (b2 - s2 / curvature, "fitted")


def run_kernel(row):
    """Execute exactly one declared K row without a growth search."""
    if row == "K01":
        values = np.array(
            [
                0.0,
                -0.0,
                2**-25,
                -(2**-25),
                2**-24,
                -(2**-24),
                2**-14,
                -(2**-14),
                1.0,
                -1.0,
                65504.0,
                -65504.0,
                65520.0,
                -65520.0,
                70000.0,
                -70000.0,
            ]
        )
        complex_values = values + 1j * values[::-1]
        _, real = pack(values, "K01.real")
        _, paired = pack(complex_values, "K01.complex")
        return dict(
            values=values,
            complex_values=complex_values,
            real_error=error_metrics(values, real),
            paired_error=error_metrics(complex_values, paired),
            half_limits=dict(
                maximum=float(np.finfo(np.float16).max),
                smallest_normal=float(np.finfo(np.float16).tiny),
                smallest_subnormal=float(np.nextafter(np.float16(0), np.float16(1))),
                epsilon=float(np.finfo(np.float16).eps),
            ),
            classification="intentional nonfinite conversions retained; no pipeline continuation",
        )
    if row == "K02":
        result = []
        for label, d, z, y, x, lateral, a in (
            ("W02", 3, 4, 16, 16, 2, 1),
            ("W05", 3, 4, 32, 32, 2, 1),
            ("metadata-only", 3, 32, 512, 512, 2, 1),
        ):
            alpha = 1 / (x * y * z * lateral * lateral * a * d)
            values = alpha * np.array([0.0, -0.0, -128.0, -1.0, -(2**-12), 2**-12, 1.0, 128.0])
            _, promoted = pack(values, "K02." + label)
            result.append(
                dict(label=label, alpha=alpha, values=values, error=error_metrics(values, promoted))
            )
        return result
    if row == "K03":
        result = []
        for n in (16, 4096):
            for magnitude in (2**-12, 1.0, 256.0, 1024.0):
                for pattern in ("constant", "alternating"):
                    signs = (
                        np.ones(n)
                        if pattern == "constant"
                        else np.where(np.arange(n) % 2, -1.0, 1.0)
                    )
                    lower = np.full(n, complex(magnitude, magnitude / 8), np.complex128)
                    higher = signs * complex(magnitude * 3 / 4, -magnitude / 16)
                    label = f"K03.{n}.{magnitude}.{pattern}"
                    packed_l, wide_l = pack(lower, label + ".lower")
                    packed_h, wide_h = pack(higher, label + ".higher")
                    wide_sx = float(np.vdot(wide_l, wide_l).real)
                    wide_cross = np.vdot(wide_l, wide_h)
                    exact_sx = n * (
                        Fraction.from_float(magnitude) ** 2
                        + Fraction.from_float(magnitude / 8) ** 2
                    )
                    exact_cross = (
                        (n if pattern == "constant" else 0)
                        * complex(magnitude, -magnitude / 8)
                        * complex(magnitude * 3 / 4, -magnitude / 16)
                    )
                    # Explicit component half ufuncs, product rounding and half reduction.
                    real_product = np.add(
                        np.multiply(packed_l[..., 0], packed_h[..., 0], dtype=np.float16),
                        np.multiply(packed_l[..., 1], packed_h[..., 1], dtype=np.float16),
                        dtype=np.float16,
                    )
                    half_sx = np.sum(
                        np.add(
                            np.multiply(packed_l[..., 0], packed_l[..., 0], dtype=np.float16),
                            np.multiply(packed_l[..., 1], packed_l[..., 1], dtype=np.float16),
                            dtype=np.float16,
                        ),
                        dtype=np.float16,
                    )
                    result.append(
                        dict(
                            n=n,
                            magnitude=magnitude,
                            pattern=pattern,
                            exact_sx=float(exact_sx),
                            exact_cross=exact_cross,
                            original_sx=float(np.vdot(lower, lower).real),
                            original_cross=np.vdot(lower, higher),
                            quantized_operands_wide_sx=wide_sx,
                            quantized_operands_wide_cross=wide_cross,
                            explicit_half_energy=half_sx,
                            explicit_half_real_cross=np.sum(real_product, dtype=np.float16),
                            explicit_half_real_product_stats=stats(real_product),
                        )
                    )
        return result
    # K04 is formula witnesses, not private helper calls or public branch coverage.
    result = {}
    spectrum = np.array([complex(1024.0, -256.0)] * 16)
    _, quantized = pack(spectrum, "K04.spectrum")
    inverse = np.fft.ifft(quantized, norm="forward")
    result["inverse_growth"] = dict(
        spectrum=spectrum, inverse=inverse, exact_origin=complex(16384.0, -4096.0)
    )
    result["equal_power_fits"] = []
    for label, values in (
        ("fitted", [1.0, 4.0, 3.0]),
        ("zero-curvature", [1.0, 2.0, 3.0]),
        ("outside-range", [1.0, 2.0, 3.0 + 2**-12]),
        ("near-tie", [1.0, 1.0 + 2**-12, 1.0]),
    ):
        _, quantized = pack(np.array(values), "K04.fit." + label)
        result["equal_power_fits"].append(
            dict(
                label=label,
                values=values,
                wider=fit_equal_power(values),
                quantized_wider=fit_equal_power(quantized),
            )
        )
    result["general_fits"] = []
    for label, points in (
        ("fitted", [(0.0, 1.0), (1.0, 4.0), (2.0, 3.0)]),
        ("duplicate-coordinate", [(0.0, 1.0), (0.0, 4.0), (2.0, 3.0)]),
        ("zero-curvature", [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]),
    ):
        result["general_fits"].append(dict(label=label, points=points, result=fit_general(points)))
    objectives = np.array([1.0, 1.0 + 2**-12, 1.0])
    _, quantized = pack(objectives, "K04.objectives")
    result["ordered_objectives"] = dict(
        wider=objectives,
        quantized=quantized,
        wider_first_max=int(np.argmax(objectives)),
        quantized_first_max=int(np.argmax(quantized)),
        wider_strict=bool(objectives[1] > objectives[0]),
        quantized_strict=bool(quantized[1] > quantized[0]),
    )
    result["regression_pairs"] = []
    for label, gain in (("equal-energy-singular", 1.0), ("unequal-energy", 1.0 + 2**-12)):
        lower = np.array([1.0, -1.0, 1.0, -1.0], np.complex128)
        higher = lower * gain
        _, wide = pack(higher, "K04.regression." + label)
        result["regression_pairs"].append(
            dict(
                label=label,
                wider_sx=float(np.vdot(lower, lower).real),
                wider_sy=float(np.vdot(higher, higher).real),
                quantized_sy=float(np.vdot(wide, wide).real),
                wider_equal=bool(np.vdot(lower, lower) == np.vdot(higher, higher)),
                quantized_equal=bool(np.vdot(lower, lower) == np.vdot(wide, wide)),
            )
        )
    result["phase_designs"] = []
    for label, angles in (
        ("uniform", [0.0, 2 * math.pi / 3, 4 * math.pi / 3]),
        ("singular", [0.0, 0.0, 0.0]),
        ("near-conditioned", [0.0, 2**-8, 2**-7]),
    ):
        design = np.array([[1 / 3, 2 * math.cos(a) / 3, 2 * math.sin(a) / 3] for a in angles])
        _, wide = pack(design, "K04.design." + label)
        entries = dict(
            label=label, design=design, condition=float(np.linalg.cond(design)), quantized=wide
        )
        for name, value in (("wider", design), ("quantized", wide)):
            try:
                inverse = exact_inverse(value)
                entries[name] = dict(inverse=inverse, residual=inverse @ value - np.eye(3))
            except (StopIteration, ZeroDivisionError) as error:
                entries[name] = failure(error, "intentional-singular-formula-witness")
        result["phase_designs"].append(entries)
    return result


def cpu_feasibility():
    """Observe bounded CPU dtype routes without inferring half arithmetic."""
    values = np.arange(16, dtype=np.float16) - np.float16(7)
    result = {
        "scope": (
            "bounded transform-only; arithmetic/workspace internals not inferred from output dtype"
        )
    }
    try:
        result["complex32_dtype"] = str(np.dtype("complex32"))
    except TypeError as error:
        result["complex32_dtype"] = failure(error, "unsupported-dtype")
    for backend in (np.fft, scipy.fft):
        label = backend.__name__
        transformed = backend.rfft(values, norm="backward")
        inverse = backend.irfft(transformed, n=values.size, norm="backward")
        result[label] = dict(
            input=stats(values),
            forward=stats(transformed),
            inverse=stats(inverse),
            reconstruction=error_metrics(values, inverse),
            api="public rfft/irfft",
            forward_norm="backward",
            inverse_norm="backward",
            scipy_effective_workers=scipy.fft.get_workers(),
            internal_arithmetic_precision="unknown",
        )
        try:
            backend.rfft(values, norm="HP114-unsupported")
        except ValueError as error:
            result[label]["unsupported_norm"] = failure(error, "expected-backend-boundary")
    return result


def memory_state():
    """Record live physical and cgroup headroom before fixture allocation."""
    mem = {}
    for line in (text_file("/proc/meminfo") or "").splitlines():
        name, value = line.split(":", 1)
        if name in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            mem[name + "_bytes"] = int(value.split()[0]) * 1024
    cgroup = {}
    for name in (
        "memory.max",
        "memory.current",
        "memory.swap.max",
        "memory.swap.current",
        "memory.events",
    ):
        cgroup[name] = text_file(Path("/sys/fs/cgroup") / name)
    return dict(
        physical=mem,
        cgroup=cgroup,
        pressure=text_file("/proc/pressure/memory"),
        self_cgroup=text_file("/proc/self/cgroup"),
    )


def resource_plan(row):
    """Enumerate conservative simultaneous array payload for one small row."""
    if row not in SHAPES:
        # K03 stores 16 small vector variants including conversion operands.
        return {"finite_kernel_arrays": 16 * 4096 * (16 * 4 + 4 * 2 + 2 * 3)}
    t, d, p, z, y, x = SHAPES[row]
    n = t * d * p * z * y * x
    v = z * y * x
    q = t * d * p * z * y * (x // 2 + 1)
    output = t * z * (2 * y) * (2 * x)
    builds = t * d * (p // 2 + 1)
    # Payload inventory includes baseline+candidate+summary qualification, retained
    # source/replay embeddings and hash/stat conversion buffers. Metadata and
    # backend workspace remain unknown, never silently treated as zero.
    return dict(
        generator_and_caller_and_hash=n * (8 + 4 + 2 + 8 + 8),
        camera_and_lateral_work=n * (8 * 3 + 16 * 2),
        bands_and_filtered=q * 16 * 12,
        diagnostic_overlap_snapshots=builds * 66 * v * 3,
        live_overlap_work=2 * 2 * 16 * v * 3,
        retained_embedding_source_and_packed_and_promoted=t
        * d
        * ((p + 1) // 2)
        * (4 * v)
        * (16 + 4 + 16),
        inverse_and_phase_and_signed_results=output * (16 * 3 + 8 * 8),
        transfer_callers_and_promoted=((p + 1) // 2) * 64 * 64 * (8 + 16),
        finite_sum_observer_and_statistics_buffers=output * (16 * 2 + 8 * 6),
    )


def standalone_plan(row, strategy):
    """Describe one caller/result child, including released setup high-water costs."""
    t, d, p, z, y, x = SHAPES[row]
    n, v = t * d * p * z * y * x, z * y * x
    q = t * d * p * z * y * (x // 2 + 1)
    output = t * z * 2 * y * 2 * x
    orders = (p + 1) // 2
    caller = (
        q * (4 if strategy == "PREPARED_HALF" else 16)
        if strategy.startswith("PREPARED_")
        else (n * {"WIDER": 4, "H1": 2, "H1_PROMOTED": 8}[strategy])
    )
    return dict(
        declared_caller=caller,
        bounded_generator_rows=x * (8 * 12 + 4 + 2),
        prepared_stage_raw_setup=n * 4 if strategy.startswith("PREPARED_") else 0,
        camera_preparation_and_public_validation_work=n * (8 * 3 + 4),
        prepared_transform_filter_sources_and_results=q * 16 * 6,
        prepared_metadata_and_trace_arrays=t * d * z * (p * p * 8 + p * 8 * 5) * 4,
        overlap_snapshots=t * d * orders * 66 * v,
        active_overlap_work=2 * 2 * 16 * v,
        inverse_phase_and_signed_output=output * (16 * 3 + 8 * 4),
        transfer_caller_and_declaration=orders * 64 * 64 * (8 + 16) * 2,
        observation_numeric_buffer_envelope=16 * OBSERVATION_BYTES,
    )


def guard_resource(row, strategy=None):
    """Stop if modeled payload already exhausts known current headroom."""
    state = memory_state()
    ledger = resource_plan(row) if strategy is None else standalone_plan(row, strategy)
    payload = sum(ledger.values())
    bounds = []
    available = state["physical"].get("MemAvailable_bytes")
    if available is not None:
        bounds.append(available)
    maximum, current = state["cgroup"].get("memory.max"), state["cgroup"].get("memory.current")
    if maximum and maximum != "max" and current:
        bounds.append(max(0, int(maximum) - int(current)))
    if not bounds or payload >= min(bounds):
        raise RuntimeError(
            "resource-skip: modeled simultaneous payload does not fit known current headroom"
        )
    return dict(
        state=state,
        payload_ledger_bytes=ledger,
        modeled_payload_bytes=payload,
        minimum_observed_headroom_bytes=min(bounds),
        unmodeled_bytes=None,
        qualification=(
            "small finite row only; unknown native workspace, metadata "
            "and background reserves; no 16 GiB claim"
        ),
    )


def retained_payload():
    """Count reachable ndarray backing storage once and disclose unknown extent."""
    seen_objects = set()
    backing = {}

    def visit(value):
        if id(value) in seen_objects:
            return
        seen_objects.add(id(value))
        if isinstance(value, np.ndarray):
            root = value
            while isinstance(root.base, np.ndarray):
                root = root.base
            # Non-ndarray backing allocation extent is not always discoverable.
            backing[id(root)] = dict(nbytes=root.nbytes, external_base=root.base is not None)
        elif dataclasses.is_dataclass(value):
            for f in dataclasses.fields(value):
                visit(getattr(value, f.name))
        elif isinstance(value, dict):
            for v in value.values():
                visit(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                visit(v)

    visit(KEEP)
    visit(ARRAYS)
    return dict(
        unique_array_backings=len(backing),
        reachable_array_payload_bytes=sum(v["nbytes"] for v in backing.values()),
        undiscovered_external_backing_extent=any(v["external_base"] for v in backing.values()),
        python_metadata_and_allocator_overhead_bytes=None,
    )


def environment():
    """Record the provisioned numerical route and material process settings."""
    binary_modules = {}
    for name in ("numpy.fft._pocketfft_umath", "scipy.fft._duccfft.pyduccfft"):
        path = getattr(sys.modules.get(name), "__file__", None)
        binary_modules[name] = dict(path=path, sha256=digest(path) if path else None)
    return dict(
        python=sys.version,
        executable=sys.executable,
        prefix=sys.prefix,
        platform=platform.platform(),
        os_release=text_file("/etc/os-release"),
        numpy=np.__version__,
        scipy=scipy.__version__,
        loaded_fft_binary_modules=binary_modules,
        internal_fft_arithmetic_precision="unknown",
        numpy_file=np.__file__,
        scipy_file=scipy.__file__,
        scipy_fft_workers=scipy.fft.get_workers(),
        threads={k: os.environ.get(k) for k in THREAD_KEYS},
        material_env={
            k: os.environ.get(k)
            for k in ("SCIPY_ARRAY_API", "PYTHONPATH", "MALLOC_ARENA_MAX", "LD_PRELOAD")
        },
        cpuinfo=text_file("/proc/cpuinfo"),
        affinity=sorted(os.sched_getaffinity(0)),
        transform_source={
            str(path.relative_to(ROOT)): digest(path)
            for path in (
                ROOT / ".venv/lib/python3.13/site-packages/numpy/fft/_pocketfft.py",
                ROOT / ".venv/lib/python3.13/site-packages/scipy/fft/_basic_backend.py",
                ROOT / ".venv/lib/python3.13/site-packages/scipy/fft/_duccfft/helper.py",
            )
        },
    )


def resource_snapshot(name):
    """Observe cumulative self high-water at one named child boundary."""
    native = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return dict(
        monotonic_ns=time.monotonic_ns(),
        native_ru_maxrss=native,
        native_units="Linux KiB",
        multiplier_to_bytes=1024,
        bytes=int(native) * 1024,
        scope=SNAPSHOT_SCOPES[name],
    )


def resource_materials():
    """Hash the explicitly named materials, including the method sources."""
    paths = list(EXPECTED) + [
        str(Path(__file__).relative_to(ROOT)),
        str(Path(__file__).with_name("manifest.md").relative_to(ROOT)),
    ]
    return {name: digest(ROOT / name) for name in paths}


def resource_git():
    """Capture actual Git identity only outside the numerical child lifetime."""

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT)

    status = git("status", "--porcelain", "--untracked-files=no").decode().strip()
    return dict(
        commit=git("rev-parse", "HEAD").decode().strip(),
        tree=git("rev-parse", "HEAD^{tree}").decode().strip(),
        parent=git("rev-parse", "HEAD^").decode().strip(),
        tracked_status=status or "clean",
        tracked_diff_sha256=hashlib.sha256(git("diff", "--binary", "HEAD")).hexdigest(),
    )


def child_identity(pid):
    """Preserve PID birth facts without treating a stale PID as ownership."""
    record = dict(pid=pid, boot_id=text_file("/proc/sys/kernel/random/boot_id"))
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        record.update(
            start_ticks=int(fields[19]),
            process_group=int(fields[2]),
            session=int(fields[3]),
            observed_monotonic_ns=time.monotonic_ns(),
        )
    except (OSError, ValueError, IndexError) as error:
        record["identity_gap"] = type(error).__name__ + ": " + str(error)
    return record


def write_once(path, value):
    """Persist one small record without overwriting an earlier attempt."""
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def resource_caller(row, strategy):
    """Generate only the declared raw representation, one bounded x-row at a time."""
    shape = SHAPES[row]
    tcount, directions, phases, nz, ny, nx = shape
    dtype = {"WIDER": np.float32, "H1": np.float16, "H1_PROMOTED": np.float64}.get(
        strategy, np.float32
    )
    raw = np.empty(shape, dtype=dtype)
    phases_rad = phases_for(row)
    background = 128.0 if row == "W06" else 256.0
    x = np.arange(nx, dtype=np.float64)
    for iz in range(nz):
        for iy in range(ny):
            specimen = np.full(nx, 3.0)
            for kz in range(min(nz, 2)):
                for ky in range(-3, 4):
                    for kx in range(4):
                        if (kz, ky, kx) == (0, 0, 0):
                            continue
                        amplitude = 32 / (1 + kx * kx + ky * ky + kz * kz)
                        offset = (kx + 2 * ky + 3 * kz) * np.pi / 7
                        angle = 2 * np.pi * (kx * x / nx + ky * iy / ny + kz * iz / nz) + offset
                        specimen += amplitude * np.cos(angle)
            if row == "W06":
                angle = 2 * np.pi * (x / nx + iy / ny)
                specimen = (
                    8 * np.cos(angle)
                    + (-8 + 2**-9) * np.cos(angle + 2**-10)
                    + 2 * np.cos(2 * np.pi * iy / ny)
                    + np.sin(2 * np.pi * x / nx)
                    + 0.25 * np.cos(2 * np.pi * iz / nz)
                )
            for t in range(tcount):
                first, second, shift = (0.55, 0.23, 0.0) if t == 0 else (0.37, 0.16, 0.41)
                for d in range(directions):
                    theta_d = d * np.pi / directions
                    carrier_angle = (
                        2
                        * np.pi
                        * (1.25 * np.cos(theta_d) * x * 0.1 + 1.25 * np.sin(theta_d) * iy * 0.1)
                    )
                    for p in range(phases):
                        theta = carrier_angle + phases_rad[d, p]
                        illumination = 1 + first * np.cos(theta + shift)
                        if phases == 5:
                            illumination = illumination + second * np.cos(
                                2 * theta + 0.3 + 2 * shift
                            )
                        admitted = (background + specimen * illumination).astype(np.float32)
                        if strategy in ("H1", "H1_PROMOTED"):
                            admitted = admitted.astype(np.float16)
                        raw[t, d, p, iz, iy] = admitted
    # No analytic truth volume, alternate caller or wider reference survives.
    return raw, background


def resource_stage(bands, transfer, carrier, filtering):
    """Run the explicitly matched prepared-band-to-image stage interval."""
    d = bands.input_shape[1]
    angles = [direction * (math.pi / d) for direction in range(d)]
    initial = np.array(
        [(1.25 * math.cos(angle), 1.25 * math.sin(angle)) for angle in angles], dtype=np.float64
    )
    parameters = sim.estimate_parameters(
        bands,
        transfer,
        initial_carriers_cyc_um=initial,
        **OPTICS,
        search_carriers=carrier["search_carriers"],
        use_time0_carriers=True,
        amplitude_floors=carrier["amplitude_floors"],
        fit_all_phases=carrier["fit_all_phases"],
        omit_kz0=False,
    )
    known = [
        sim.reconstruct_known(
            one_time(bands, t),
            transfer,
            carriers_cyc_um=parameters.carriers_cyc_um[t],
            modulation=parameters.modulation[t],
            **OPTICS,
            **filtering,
        )
        for t in range(bands.input_shape[0])
    ]
    return dict(
        image=np.concatenate([value.image for value in known]),
        parameters=parameters,
        reconstructions=known,
    )


def refuse_quarantined_resource_launch():
    """Refuse the known unsupported route without spawning or probing anything."""
    raise RuntimeError(RESOURCE_LAUNCH_HOLD)


def resource_child(args):
    """Retain one caller and one result, with no numerical reference workflow."""
    refuse_quarantined_resource_launch()  # Also blocks direct internal-route invocation.
    grant = authorize(args)  # Unexecuted draft below, retained for affected-scope review.
    directory = EVIDENCE / args.run_id
    record = dict(
        schema="HP114-resource-child-v1",
        pid=os.getpid(),
        row=args.row,
        strategy=args.strategy,
        repetition=args.repetition,
        status="child-started",
        identity=child_identity(os.getpid()),
        snapshots={},
        materials_before=resource_materials(),
    )
    started = time.monotonic_ns()
    caught = []
    global np, scipy, sim
    try:
        control = grant.get("method_control")
        if control is not None:
            record["method_control"] = control
            if grant.get("control_release") is not True:
                raise ValueError("lifecycle control lacks explicit root release")
            if control == "missing-record":
                return 3  # finally writes below: explicit deletion is not used.
            if control == "self-term":
                os.kill(os.getpid(), signal.SIGTERM)
            elif control in ("timeout", "timeout-ignore-term"):
                if control == "timeout-ignore-term":
                    signal.signal(signal.SIGTERM, signal.SIG_IGN)
                # Parent should stop earlier. If it disappears, even this
                # control has a finite fallback lifetime, not an orphan loop.
                time.sleep(
                    2 * grant["deadline_seconds"]
                    + grant["term_grace_seconds"]
                    + grant["kill_reap_seconds"]
                )
                record["status"] = "timeout-control-returned-without-parent-stop"
                return 3
            elif control == "child-error":
                raise ValueError("intentional finite lifecycle-control failure")
            elif control not in ("malformed-record", "oversized-record"):
                raise ValueError("unknown lifecycle control")
            record["status"] = "lifecycle-control-only"
            return 3
        import numpy as numpy_module
        import scipy as scipy_module
        import scipy.fft

        import simrecon as simrecon_module

        np, scipy, sim = numpy_module, scipy_module, simrecon_module
        if (np.__version__, scipy.__version__) != ("2.5.3", "1.18.1"):
            raise RuntimeError("numerical dependency identity changed")
        if Path(sim.__file__).resolve() != ROOT / "src/simrecon/__init__.py":
            raise RuntimeError("product import belongs to another checkout")
        record["environment"] = environment()
        record["resource_before_setup"] = guard_resource(args.row, args.strategy)
        with warnings.catch_warnings(record=True) as caught, scipy.fft.set_workers(1):
            warnings.simplefilter("always")
            record["environment"]["scipy_fft_workers_during_call"] = scipy.fft.get_workers()
            caller, background = resource_caller(args.row, args.strategy)
            acquisition, carrier, filtering = settings(args.row, background)
            transfer = make_transfer(acquisition["norders"])
            if args.strategy.startswith("PREPARED_"):
                prep_options = {k: v for k, v in acquisition.items() if k != "phase_policy"}
                bands = sim.prepare_acquisition_bands(caller, **prep_options)
                del caller  # Raw setup caller is not a prepared-stage caller.
                metadata = dataclasses.replace(bands, quadratures=None)
                source = bands.quadratures
                if args.strategy == "PREPARED_HALF":
                    caller = np.empty((*source.shape, 2), dtype="<f2")
                    caller[..., 0], caller[..., 1] = source.real, source.imag
                    del source, bands
                else:
                    caller = source
                    del bands, source
                record["entry"] = "prepared-band public estimation + per-time known reconstruction"
                record["setup_scope"] = (
                    "public preparation and pack are included in cumulative/terminal peak; "
                    "raw setup released"
                )
            else:
                metadata = None
                record["entry"] = "reconstruct_workflow full result"
                record["setup_scope"] = "one declared caller generated with bounded x-row scratch"
            KEEP.append(caller)
            if metadata is not None:
                KEEP.append(metadata)
            record["caller"] = array_identity(caller)
            record["caller_stats"] = stats(caller)
            if record["caller_stats"].get("nonfinite", 0) or any(
                not np.isfinite(chunk).all() for chunk in numeric_chunks(caller)
            ):
                record["status"] = "nonfinite-conversion"
                raise ValueError("nonfinite caller conversion; no numerical continuation")
            record["snapshots"]["pre_call"] = resource_snapshot("pre_call")
            record["conversion_start_ns"] = time.monotonic_ns()
            if metadata is not None:
                if args.strategy == "PREPARED_HALF":
                    working = np.empty(caller.shape[:-1], dtype=np.complex128)
                    working.real, working.imag = caller[..., 0], caller[..., 1]
                else:
                    working = caller
                bands = dataclasses.replace(metadata, quadratures=working)
                KEEP.append(bands)  # Packed caller and required promoted work coexist.
            record["call_start_ns"] = time.monotonic_ns()
            if metadata is None:
                result = sim.reconstruct_workflow(
                    caller,
                    acquisition=acquisition,
                    optics=OPTICS,
                    carrier=carrier,
                    filtering=filtering,
                    specimen_identity={
                        "id": "HP114-analytic-v1",
                        "intensity_unit": "detector-counts",
                    },
                    transfer=transfer,
                    transfer_identity={
                        "id": "HP114-constant-complex-v1",
                        "intensity_unit": "dimensionless-transfer",
                        "optics": OPTICS,
                    },
                )
            else:
                result = resource_stage(bands, transfer, carrier, filtering)
            record["call_end_ns"] = time.monotonic_ns()
            record["snapshots"]["call_end"] = resource_snapshot("call_end")
            KEEP.append(result)
            if metadata is None:
                parameters = result.parameters
                outputs = {
                    name: getattr(result, name) for name in ("image", "x_um", "y_um", "z_um")
                }
            else:
                parameters = result["parameters"]
                outputs = {"image": result["image"]}
                outputs.update(
                    {
                        name: getattr(result["reconstructions"][0], name)
                        for name in ("x_um", "y_um", "z_um")
                    }
                )
            outputs.update(
                {
                    name: getattr(parameters, name)
                    for name in ("carriers_cyc_um", "modulation", "raw_modulation")
                }
            )
            record["outputs"] = {
                name: dict(identity=array_identity(value), statistics=stats(value))
                for name, value in outputs.items()
            }
            record["finite_outputs"] = all(
                np.isfinite(chunk).all()
                for value in outputs.values()
                for chunk in numeric_chunks(value)
            )
            record["branches"] = parameters.branches
            record["retained_payload"] = retained_payload()
            record["status"] = (
                "observed-pending-scientific-qualification"
                if record["finite_outputs"]
                else "nonfinite-result"
            )
    except Exception as error:
        if record["status"] != "nonfinite-conversion":
            record["status"] = "child-operation-or-observer-failure"
        record["failure"] = failure(error, "diagnosis-required")
        record["traceback"] = traceback.format_exc()
    finally:
        record["warnings"] = [
            dict(category=w.category.__name__, message=str(w.message)) for w in caught
        ]
        record["materials_after"] = resource_materials()
        record["material_identity_matches"] = (
            record["materials_before"] == record["materials_after"]
        )
        record["grant_sha256_after"] = digest(args.grant)
        record["whole_child_until_json_seconds"] = (time.monotonic_ns() - started) / 1e9
        record["qualification_receipt_loaded"] = False
        record["reference_workflow_loaded"] = False
        if "call_end" in record["snapshots"]:
            record["call_only_seconds"] = (record["call_end_ns"] - record["call_start_ns"]) / 1e9
            record["conversion_and_call_seconds"] = (
                record["call_end_ns"] - record["conversion_start_ns"]
            ) / 1e9
            record["snapshots"]["post_observation"] = resource_snapshot("post_observation")
        # Scalars/identities only: full retained result is not reloaded or copied
        # into a serialized reference. All JSON work remains in terminal wait4 RSS.
        control = grant.get("method_control")
        if control == "missing-record":
            pass
        elif control in ("malformed-record", "oversized-record"):
            # Small fixed protocol controls only; preserve raw bytes for parser
            # refusal, without modifying scientific sources or prior attempts.
            with (directory / "child.json").open("x") as stream:
                stream.write(
                    "{" if control == "malformed-record" else " " * (RECORD_LIMIT_BYTES + 1)
                )
        else:
            write_once(directory / "child.json", record)
    return 0 if record["status"] == "observed-pending-scientific-qualification" else 2


def validate_resource_record(record, args, pid, materials, grant_hash):
    """Validate this one finite observation protocol, not scientific success."""
    required_outputs = {
        "image",
        "x_um",
        "y_um",
        "z_um",
        "carriers_cyc_um",
        "modulation",
        "raw_modulation",
    }
    if (
        record.get("schema") != "HP114-resource-child-v1"
        or record.get("pid") != pid
        or record.get("row") != args.row
        or record.get("strategy") != args.strategy
        or record.get("repetition") != args.repetition
    ):
        raise ValueError("child record does not identify this exact attempt")
    if record.get("status") != "observed-pending-scientific-qualification":
        return record.get("status", "incomplete-child-record")
    if (
        record.get("materials_before") != materials
        or record.get("materials_after") != materials
        or record.get("grant_sha256_after") != grant_hash
        or record.get("material_identity_matches") is not True
    ):
        raise ValueError("changed child identities")
    times, peaks = [], []
    for name, meaning in SNAPSHOT_SCOPES.items():
        snap = record["snapshots"][name]
        if (
            snap["scope"] != meaning
            or snap["native_units"] != "Linux KiB"
            or snap["multiplier_to_bytes"] != 1024
            or type(snap["native_ru_maxrss"]) is not int
            or snap["native_ru_maxrss"] < 0
            or snap["bytes"] != 1024 * snap["native_ru_maxrss"]
            or type(snap["monotonic_ns"]) is not int
            or snap["monotonic_ns"] <= 0
        ):
            raise ValueError("missing/unusable snapshot or mismatched scope/units")
        times.append(snap["monotonic_ns"])
        peaks.append(snap["native_ru_maxrss"])
    if not (
        times == sorted(times)
        and peaks == sorted(peaks)
        and times[0]
        <= record["conversion_start_ns"]
        <= record["call_start_ns"]
        <= record["call_end_ns"]
        <= times[1]
        <= times[2]
    ):
        raise ValueError("snapshot/call boundaries are inconsistent")
    if (
        record.get("finite_outputs") is not True
        or set(record["outputs"]) != required_outputs
        or record.get("qualification_receipt_loaded") is not False
        or record.get("reference_workflow_loaded") is not False
        or not all(
            key in record
            for key in (
                "caller",
                "caller_stats",
                "environment",
                "retained_payload",
                "branches",
                "entry",
            )
        )
    ):
        raise ValueError("incomplete resource observations")
    shape = SHAPES[args.row]
    t, d, p, z, y, x = shape
    expected_shapes = dict(
        image=[t, z, 2 * y, 2 * x],
        x_um=[2 * x],
        y_um=[2 * y],
        z_um=[z],
        carriers_cyc_um=[t, d, 2],
        modulation=[t, d, (p - 1) // 2],
        raw_modulation=[t, d, (p - 1) // 2],
    )
    caller_shape = list(shape)
    caller_dtype = {"WIDER": "<f4", "H1": "<f2", "H1_PROMOTED": "<f8"}.get(args.strategy, "<c16")
    expected_entry = "reconstruct_workflow full result"
    if args.strategy.startswith("PREPARED_"):
        caller_shape = [t, d, p, z, y, x // 2 + 1]
        expected_entry = "prepared-band public estimation + per-time known reconstruction"
        if args.strategy == "PREPARED_HALF":
            caller_shape.append(2)
            caller_dtype = "<f2"
    if (
        record["caller"]["shape"] != caller_shape
        or record["caller"]["canonical_dtype"] != caller_dtype
        or record["entry"] != expected_entry
        or record["branches"] != [list(row) for row in expected_branches(args.row)]
        or record["environment"].get("numpy") != "2.5.3"
        or record["environment"].get("scipy") != "1.18.1"
        or record["environment"].get("scipy_fft_workers_during_call") != 1
    ):
        raise ValueError("caller/entry/branch/environment shape differs from frozen route")
    for name, output in record["outputs"].items():
        identity = output["identity"]
        if (
            not isinstance(identity["shape"], list)
            or len(identity["content_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in identity["content_sha256"])
            or identity["shape"] != expected_shapes[name]
            or identity["canonical_dtype"]
            != ("<c16" if name in ("modulation", "raw_modulation") else "<f8")
        ):
            raise ValueError("invalid common-output identity")
    return "observed-pending-independent-scientific-qualification"


def resource_parent(args):
    """Own one exact-PID wait4 lifecycle; never poll/wait with Popen."""
    refuse_quarantined_resource_launch()  # Unconditional, before raw writes or any spawn.
    if not EVIDENCE.is_dir():
        raise RuntimeError("root has not prepared raw destination")
    directory = EVIDENCE / args.run_id
    directory.mkdir(exist_ok=False)
    receipt = dict(
        schema="HP114-resource-attempt-v1",
        row=args.row,
        strategy=args.strategy,
        repetition=args.repetition,
        run_id=args.run_id,
        status="admission-started",
        terminal=None,
        attempt_start_ns=time.monotonic_ns(),
        parent_identity=child_identity(os.getpid()),
        parent_samples=None,
        parent_sampling_scope="none; no sampled maximum is substituted for terminal native usage",
    )
    pid = None
    terminal = None
    wait_lost = False
    grant = {}

    def collect():
        nonlocal terminal, wait_lost
        if terminal is not None:
            return terminal
        if wait_lost:
            raise RuntimeError("exact-PID wait ownership lost")
        now = time.monotonic_ns()
        previous = receipt.get("last_wait_poll_ns")
        if previous is not None:
            receipt["largest_observed_poll_gap_ns"] = max(
                receipt.get("largest_observed_poll_gap_ns", 0), now - previous
            )
        receipt["last_wait_poll_ns"] = now
        receipt["wait_poll_count"] = receipt.get("wait_poll_count", 0) + 1
        try:
            got, status, usage = os.wait4(pid, os.WNOHANG)
        except InterruptedError:
            return None
        except ChildProcessError:
            wait_lost = True
            raise
        if not got:
            return None
        if not (os.WIFEXITED(status) or os.WIFSIGNALED(status)):
            receipt.setdefault("nonterminal_wait_events", []).append(dict(raw_status=status))
            return None
        terminal = dict(
            pid=got,
            raw_wait_status=status,
            exit_code=os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
            signal=os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
            native_ru_maxrss=usage.ru_maxrss,
            native_units="Linux KiB",
            multiplier_to_bytes=1024,
            terminal_child_peak_bytes=int(usage.ru_maxrss) * 1024,
            user_seconds=usage.ru_utime,
            system_seconds=usage.ru_stime,
            reaped_monotonic_ns=time.monotonic_ns(),
            scope=(
                "maximum resident direct-child process size through exit/JSON/teardown; "
                "excludes external observer; no concurrent tree aggregate"
            ),
        )
        return terminal

    def stop(signum):
        if collect() is None:
            try:
                os.killpg(pid, signum)  # Unreaped exact child, with new session from spawn.
                delivery = "sent"
            except ProcessLookupError:
                delivery = "group-absent-race"
                collect()  # Preserve terminal usage if exit raced with the signal.
            receipt.setdefault("signals", []).append(
                dict(signal=signum, delivery=delivery, monotonic_ns=time.monotonic_ns())
            )

    def bounded_cleanup():
        if pid is None or terminal is not None or wait_lost:
            return
        stop(signal.SIGTERM)
        until = time.monotonic() + grant["term_grace_seconds"]
        while collect() is None and time.monotonic() < until:
            time.sleep(0.05)
        if terminal is None:
            stop(signal.SIGKILL)
            until = time.monotonic() + grant["kill_reap_seconds"]
            while collect() is None and time.monotonic() < until:
                time.sleep(0.05)

    try:
        if Path(args.grant).stat().st_size > RECORD_LIMIT_BYTES:
            raise ValueError(
                "grant exceeds finite parse bound; raw source file retained externally"
            )
        with (
            Path(args.grant).open("rb") as source,
            (directory / "grant.original.json").open("xb") as target,
        ):
            for block in iter(lambda: source.read(OBSERVATION_BYTES), b""):
                target.write(block)
        grant = authorize(args)
        receipt["grant"], receipt["grant_sha256"] = grant, digest(args.grant)
        receipt["materials_before"] = resource_materials()
        receipt["git_before"] = resource_git()
        if any(
            receipt["git_before"][key] != grant["candidate"].get(key)
            for key in receipt["git_before"]
        ):
            raise ValueError("actual Git candidate differs from grant")
        if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise ValueError("nondefault SIGCHLD risks competing/automatic reap")
        if signal.getsignal(signal.SIGINT) != signal.default_int_handler:
            raise ValueError(
                "supported observer cancellation requires Python default SIGINT handler"
            )
        for key in ("deadline_seconds", "term_grace_seconds", "kill_reap_seconds"):
            if (
                type(grant.get(key)) not in (int, float)
                or not math.isfinite(grant[key])
                or grant[key] <= 0
            ):
                raise ValueError("root must supply positive finite lifecycle bound: " + key)
        # This source guard is necessary, not sufficient; root admission must
        # explain unknown workspaces/ancestor/caller/OS reserves with actual facts.
        receipt["headroom_before_spawn"] = guard_resource(args.row, args.strategy)
        receipt["parent_pre_spawn"] = dict(
            monotonic_ns=time.monotonic_ns(),
            native_ru_maxrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            native_units="Linux KiB",
            scope="external observer only; inherited/pre-exec contribution not isolated",
        )
        write_once(
            directory / "spawn-intent.json",
            dict(
                parent=receipt["parent_identity"],
                argv=sys.argv,
                grant_sha256=receipt["grant_sha256"],
                monotonic_ns=time.monotonic_ns(),
            ),
        )
        argv = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--route",
            "resource-child",
            "--grant",
            str(directory / "grant.original.json"),
            "--row",
            args.row,
            "--strategy",
            args.strategy,
            "--repetition",
            str(args.repetition),
            "--run-id",
            args.run_id,
        ]
        actions = [
            (
                os.POSIX_SPAWN_OPEN,
                fd,
                str(directory / name),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            for fd, name in ((1, "child.stdout"), (2, "child.stderr"))
        ]
        receipt["phase"] = "spawn-requested"
        receipt["spawn_call_start_ns"] = time.monotonic_ns()
        pid = os.posix_spawn(
            sys.executable,
            argv,
            dict(os.environ),
            file_actions=actions,
            setsid=True,
            setsigdef=(signal.SIGTERM, signal.SIGINT),
        )
        receipt["spawn_return_ns"] = time.monotonic_ns()
        receipt["phase"] = "child-owned"
        receipt["owned_child"] = child_identity(pid)
        write_once(directory / "owned-child.json", receipt["owned_child"])
        deadline = time.monotonic() + grant["deadline_seconds"]
        while collect() is None:
            if time.monotonic() >= deadline:
                receipt["status"] = "timeout"
                bounded_cleanup()
                break
            # No parent process-RSS sampling is commissioned. This live
            # headroom check is separate from child native peak observation.
            receipt["latest_headroom_check"] = guard_resource(args.row, args.strategy)
            time.sleep(0.05)
        if receipt["status"] != "timeout":
            if terminal["signal"] is not None:
                receipt["status"] = "child-signaled"
            else:
                path = directory / "child.json"
                if not path.is_file():
                    receipt["status"] = "missing-child-record"
                elif path.stat().st_size > RECORD_LIMIT_BYTES:
                    receipt["status"] = "oversized-child-record"
                else:

                    def invalid_constant(value):
                        raise ValueError("nonstandard JSON constant: " + value)

                    receipt["phase"] = "read-and-validate-child-record"
                    record = json.loads(path.read_text(), parse_constant=invalid_constant)
                    receipt["child_record_sha256"] = digest(path)
                    if record.get("status") == "observed-pending-scientific-qualification":
                        owned = receipt["owned_child"]
                        if any(
                            owned.get(key) is None
                            or record.get("identity", {}).get(key) != owned[key]
                            for key in ("pid", "boot_id", "start_ticks", "process_group", "session")
                        ):
                            raise ValueError(
                                "child birth identity missing or differs from owned marker"
                            )
                    receipt["status"] = validate_resource_record(
                        record, args, pid, receipt["materials_before"], receipt["grant_sha256"]
                    )
                    if (
                        receipt["status"] == "observed-pending-independent-scientific-qualification"
                        and terminal["native_ru_maxrss"]
                        < record["snapshots"]["post_observation"]["native_ru_maxrss"]
                    ):
                        raise ValueError("terminal native peak is below child cumulative snapshot")
                    if terminal["exit_code"] != 0:
                        receipt["status"] = "child-nonzero-exit: " + str(receipt["status"])
    except BaseException as error:
        receipt["status"] = (
            "spawn-failure"
            if pid is None and receipt.get("phase") == "spawn-requested"
            else "admission-refused"
            if pid is None
            else "malformed-or-incomplete-child-record"
            if receipt.get("phase") == "read-and-validate-child-record"
            else "observer-cancelled"
            if isinstance(error, KeyboardInterrupt)
            else "observer-or-record-failure"
        )
        receipt["failure"] = dict(exception=type(error).__name__, message=str(error))
    finally:
        try:
            bounded_cleanup()
        except BaseException as error:
            receipt["cleanup_failure"] = dict(exception=type(error).__name__, message=str(error))
        receipt["terminal"] = terminal  # None means unknown, never zero RSS.
        if terminal is not None:
            receipt["spawn_to_terminal_observed_seconds"] = (
                terminal["reaped_monotonic_ns"] - receipt["spawn_call_start_ns"]
            ) / 1e9
            receipt["terminal_time_scope"] = (
                "includes spawn, monitoring/scheduling and nominal 50 ms sleeps; "
                "reap delay is not bounded by sleep interval; not exact child death time"
            )
        receipt["wait_ownership_lost"] = wait_lost
        receipt["coordinator_recovery_required"] = (pid is not None and terminal is None) or (
            pid is None and receipt.get("phase") == "spawn-requested"
        )
        if receipt["coordinator_recovery_required"]:
            receipt["status"] = "terminal-usage-or-ownership-lost-recovery-required"
        try:
            receipt["materials_after"] = resource_materials()
            receipt["git_after"] = resource_git()  # Child already reaped or explicitly lost.
            if (
                receipt.get("materials_before") != receipt["materials_after"]
                or receipt.get("git_before") != receipt["git_after"]
                or receipt.get("grant_sha256") != digest(args.grant)
            ):
                receipt["identity_changed"] = True
                if receipt["status"] == "observed-pending-independent-scientific-qualification":
                    receipt["status"] = "changed-identities"
        except BaseException as error:
            receipt["identity_observation_failure"] = type(error).__name__ + ": " + str(error)
            if receipt["status"] == "observed-pending-independent-scientific-qualification":
                receipt["status"] = "identity-observer-failure"
        write_once(directory / "attempt.json", receipt)
    return 0 if receipt["status"] == "observed-pending-independent-scientific-qualification" else 2


def decode_scalar(value):
    """Decode only the finite scalar wire representation used by these controls."""
    if isinstance(value, dict) and set(value) == {"float64_bits_be"}:
        return struct.unpack(">d", bytes.fromhex(value["float64_bits_be"]))[0]
    if isinstance(value, dict) and set(value) == {"real", "imag"}:
        return complex(decode_scalar(value["real"]), decode_scalar(value["imag"]))
    return value


def finite_controls(directory):
    """Prepare concrete finite observer controls; this function is unexecuted."""
    scalars = [
        0.0,
        -0.0,
        1.25,
        float("inf"),
        -float("inf"),
        float("nan"),
        complex(-0.0, float("inf")),
    ]
    scalar_rows = []
    for value in scalars:
        serialized = json.dumps(encode(value), allow_nan=False)
        roundtrip = decode_scalar(json.loads(serialized))
        components = (value.real, value.imag) if isinstance(value, complex) else (value,)
        returned = (
            (roundtrip.real, roundtrip.imag) if isinstance(roundtrip, complex) else (roundtrip,)
        )
        scalar_rows.append(
            dict(
                wire=serialized,
                identical_ieee_components=all(
                    struct.pack(">d", a) == struct.pack(">d", b)
                    for a, b in zip(components, returned, strict=True)
                ),
            )
        )
    values = [0.0, -0.0, 1.0, -2.0]
    base = np.array(values, dtype="<f8")
    strided = np.zeros(8, dtype="<f8")
    strided[::2] = base
    expected_bytes = b"".join(struct.pack("<d", v) for v in values)
    expected_sha = hashlib.sha256(expected_bytes).hexdigest()
    hash_rows = []
    for name, array in (
        ("contiguous", base),
        ("strided", strided[::2]),
        ("big-endian", base.astype(">f8")),
        ("reshaped", base.reshape(2, 2)),
        ("transposed-storage", base.reshape(2, 2).T.copy().T),
        ("empty", np.empty((0, 2), dtype=">f8")),
        ("scalar", np.array(-0.0)),
    ):
        observed = array_identity(array)
        expected = (
            hashlib.sha256(b"").hexdigest()
            if array.size == 0
            else (
                hashlib.sha256(struct.pack("<d", -0.0)).hexdigest()
                if array.ndim == 0
                else expected_sha
            )
        )
        hash_rows.append(
            dict(
                case=name,
                identity=observed,
                expected_content_sha256=expected,
                content_equal=observed["content_sha256"] == expected,
                shape_preserved=observed["shape"] == list(array.shape),
            )
        )
    arrays = [
        base,
        np.array([0.0, -0.0, float("inf"), float("nan")], dtype=">f4"),
        np.array([complex(-0.0, 1.0), complex(2.0, -0.0)], dtype=">c16"),
        np.empty((0, 2), dtype="<f2"),
    ]
    array_rows = []
    for i, array in enumerate(arrays):
        path = directory / f"control-array-{i}.npy"
        with path.open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
        with path.open("rb") as stream:
            returned = np.load(stream, allow_pickle=False)
        array_rows.append(
            dict(
                original=array_identity(array),
                roundtrip=array_identity(returned),
                dtype_endian_equal=array.dtype.str == returned.dtype.str,
                shape_content_equal=array_identity(array) == array_identity(returned),
                file_sha256=digest(path),
            )
        )
    generation = []
    for row in SHAPES:
        admitted, analytic, _, _ = generator(row)  # Separate diagnostic process only.
        for strategy in ("WIDER", "H1", "H1_PROMOTED"):
            generated, _ = resource_caller(row, strategy)
            expected = admitted if strategy == "WIDER" else admitted.astype(np.float16)
            if strategy == "H1_PROMOTED":
                expected = expected.astype(np.float64)
            generation.append(
                dict(
                    row=row,
                    strategy=strategy,
                    expected=array_identity(expected),
                    observed=array_identity(generated),
                    identical=array_identity(expected) == array_identity(generated),
                )
            )
        del admitted, analytic  # Diagnostic KEEP intentionally preserves its actual high-water.
    cancellation = np.array([2048.0, 1.0, -2048.0], dtype=np.float16)
    half_left = np.add(
        np.add(cancellation[0], cancellation[1], dtype=np.float16),
        cancellation[2],
        dtype=np.float16,
    )
    incomplete = []
    for example in (
        {"schema": "HP114-resource-child-v1", "status": "child-started"},
        {
            "schema": "HP114-resource-child-v1",
            "pid": 123,
            "row": "W01",
            "strategy": "WIDER",
            "repetition": 1,
            "status": "observed-pending-scientific-qualification",
            "materials_before": {},
            "materials_after": {},
            "grant_sha256_after": "0" * 64,
            "material_identity_matches": True,
            "snapshots": {"pre_call": None},
        },
    ):
        try:
            observed = validate_resource_record(
                example,
                argparse.Namespace(row="W01", strategy="WIDER", repetition=1),
                123,
                {},
                "0" * 64,
            )
            incomplete.append(
                dict(
                    input=example,
                    disposition=observed,
                    wrongly_completed=observed
                    == "observed-pending-independent-scientific-qualification",
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            incomplete.append(
                dict(input=example, disposition="rejected", exception=type(error).__name__)
            )
    return dict(
        status="controls-observed-pending-review",
        scope="finite method controls attached to existing W/K rows; no product checkpoint",
        scalar_wire=scalar_rows,
        canonical_hashes=hash_rows,
        numpy_serialization=array_rows,
        raw_generation=generation,
        K01_range=run_kernel("K01"),
        K03_products=run_kernel("K03"),
        K03_cancellation=dict(
            values=cancellation,
            exact_dyadic_sum=1,
            quantized_operands_wider=float(
                np.sum(cancellation.astype(np.float64), dtype=np.float64)
            ),
            explicit_half_left_association=half_left,
            expected_half_left_association=0,
        ),
        error_observer=dict(
            reference=[1.0, -2.0, 0.0],
            candidate=[1.5, -1.0, 0.0],
            expected_max_absolute=1.0,
            expected_rms=math.sqrt(5 / 12),
            expected_relative_l2=0.5,
            observed=error_metrics(np.array([1.0, -2.0, 0.0]), np.array([1.5, -1.0, 0.0])),
            zero_rule=error_metrics(np.zeros(2), np.zeros(2)),
            strided_same_values=error_metrics(base, strided[::2]),
            transposed_storage_same_values=error_metrics(
                base.reshape(2, 2), base.reshape(2, 2).T.copy().T
            ),
            empty_rule=error_metrics(np.empty(0), np.empty(0)),
        ),
        K01_fft_policy=cpu_feasibility(),
        incomplete_record_controls=incomplete,
        controls_pass_is_not_scientific_qualification=True,
    )


def main():
    """Authorize, execute and retain one future finite numerical attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", required=True)
    parser.add_argument("--row", choices=(*SHAPES, "K01", "K02", "K03", "K04"), required=True)
    parser.add_argument(
        "--strategy",
        choices=tuple(dict.fromkeys((*STRATEGIES, *RESOURCE_STRATEGIES))),
        required=True,
    )
    parser.add_argument(
        "--route",
        choices=("diagnostic", "resource", "resource-child", "controls"),
        default="diagnostic",
    )
    parser.add_argument("--repetition", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--qualification", default="")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not args.run_id.replace("-", "").replace("_", "").isalnum():
        raise RuntimeError("run id must contain only letters, numbers, hyphens, underscores")
    if args.route == "resource":
        return resource_parent(args)
    if args.route == "resource-child":
        return resource_child(args)
    grant = authorize(args)
    if not EVIDENCE.is_dir():
        raise RuntimeError("root has not prepared the external raw evidence destination")
    target = EVIDENCE / args.run_id
    target.mkdir(exist_ok=False)  # Every attempt is retained; no overwrite/retry hiding.
    record = dict(
        schema="HP114-study-v2-source-method",
        row=args.row,
        strategy=args.strategy,
        repetition=args.repetition,
        run_id=args.run_id,
        grant=grant,
        grant_sha256=digest(args.grant),
        status="started",
        identities={
            "baseline": BASE,
            "harness": digest(__file__),
            "manifest": digest(Path(__file__).with_name("manifest.md")),
            "sources": EXPECTED,
            "task_at_run": digest(ROOT / "docs/tasks/half-precision-study.md"),
        },
    )
    start = time.monotonic_ns()
    global np, scipy, sim
    caught = []
    try:
        import numpy as numpy_module
        import scipy as scipy_module
        import scipy.fft

        import simrecon as simrecon_module

        np, scipy, sim = numpy_module, scipy_module, simrecon_module
        if (np.__version__, scipy.__version__) != ("2.5.3", "1.18.1"):
            raise RuntimeError("pinned numerical dependency versions differ")
        if Path(sim.__file__).resolve() != ROOT / "src/simrecon/__init__.py":
            raise RuntimeError("imported product does not belong to this source checkout")
        record["environment"] = environment()
        record["resource_preallocation"] = guard_resource(
            "W05" if args.route == "controls" else args.row
        )
        record["pre_call_high_water_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        with warnings.catch_warnings(record=True) as caught, scipy.fft.set_workers(1):
            warnings.simplefilter("always")
            if args.route == "controls":
                record["result"] = finite_controls(target)
            elif args.row in SHAPES:
                record["result"] = run_workflow(args)
            elif args.strategy == "CPU":
                record["result"] = cpu_feasibility()
            else:
                record["result"] = run_kernel(args.row)
            record["warnings"] = [
                dict(
                    category=w.category.__name__,
                    message=str(w.message),
                    filename=w.filename,
                    lineno=w.lineno,
                )
                for w in caught
            ]
        record["status"] = (
            record["result"].get("status", "completed")
            if isinstance(record["result"], dict)
            else "completed"
        )
    except Exception as error:
        record["status"] = "failed-retained"
        record["failure"] = failure(error, "diagnosis-required")
        record["traceback"] = traceback.format_exc()
    finally:
        record["warnings"] = [
            dict(
                category=w.category.__name__,
                message=str(w.message),
                filename=w.filename,
                lineno=w.lineno,
            )
            for w in caught
        ]
        record["whole_run_before_export_seconds"] = (time.monotonic_ns() - start) / 1e9
        record["timings"] = TIMINGS
        record["native_peak_rss_kib_before_export"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        record["native_peak_rss_bytes_before_export"] = (
            record["native_peak_rss_kib_before_export"] * 1024
        )
        record["rss_interpretation"] = (
            "diagnostic comparison-harness whole-process Linux KiB; "
            "baseline retained before candidate; unmatched between modes; "
            "actual whole-pipeline storage/speed benefit UNMEASURED"
        )
        if np is not None:
            encoded = encode(record)
            encoded["retained_payload"] = retained_payload()
            directory = target / "arrays"
            directory.mkdir()
            index = {}
            for i, (key, value) in enumerate(ARRAYS.items()):
                path = directory / f"{i:05d}.npy"
                np.save(path, value, allow_pickle=False)
                index[key] = dict(
                    path=str(path.relative_to(target)),
                    sha256=digest(path),
                    nbytes=path.stat().st_size,
                )
            encoded["array_index"] = index
        else:
            encoded = record
        encoded["native_peak_rss_kib_after_export"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        encoded["native_peak_rss_bytes_after_export"] = (
            encoded["native_peak_rss_kib_after_export"] * 1024
        )
        encoded["including_export_seconds"] = (time.monotonic_ns() - start) / 1e9
        (target / "run.json").write_text(json.dumps(encoded, indent=2, allow_nan=False) + "\n")
        print(
            json.dumps(
                {
                    "run": str(target / "run.json"),
                    "sha256": digest(target / "run.json"),
                    "status": record["status"],
                }
            )
        )
    return 2 if record["status"] == "failed-retained" else 0


if __name__ == "__main__":
    raise SystemExit(main())
