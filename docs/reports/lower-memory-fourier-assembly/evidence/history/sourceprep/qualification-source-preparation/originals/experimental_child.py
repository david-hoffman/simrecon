"""FA120 EXPERIMENTAL CHILD SOURCE PROPOSAL. No execution authority.

Unvalidated source: syntax, imports, behavior and measurement qualification are
unknown. Only a later independently reviewed ROOT-bound source revision may
remove the unconditional hold. No environment variable, argument or grant can
disable it. This file creates no descendants, monitor, parser or admission API.
"""

raise SystemExit("FA120 UNCONDITIONAL EXECUTION HOLD: SOURCE PREPARATION ONLY")

import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import cast

import numpy as np
from scipy.fft import ifftn

from simrecon.reconstruction import known_parameters as kp
from reconstruction_summary_fixture import identity


SOURCE_REFERENCE = "158776ade28079276304d49a6b973eccbf4109c9"
SOURCE_SHA256 = "edb87b64e1691b7f437194aabc0df8d4ab22e3e67b6b05639dbd3bad26e2c645"
ACTUAL_119_PARENT = "UNBOUND"
ACTUAL_CANDIDATE = "UNBOUND"
ACTUAL_ENVIRONMENT = "UNBOUND"
ACTUAL_GRANT = "UNBOUND"
OUTPUT_IMAGE_PATH = "UNBOUND"
FIXTURE_ROOT = "UNBOUND"
FIXTURE_FILE_HASHES = "UNBOUND"
CONDITIONS = {
    "Ksmall": ((1, 3, 8, 32, 32), "3d", 1),
    "Kmedium": ((1, 3, 8, 64, 64), "3d", 1),
    "K2D": ((2, 2, 1, 12, 16), "2d", 2),
}
VARIANTS = ("baseline", "candidate", "retained-control")
REPETITIONS = (1, 2, 3)

# These are existing source bindings, not new scientific helper implementations.
_finite = kp._finite
signed_fourier_index = kp.signed_fourier_index
_C128 = kp._C128
baseline = kp.assemble_signed_image


def candidate(filtered, grid, carriers, omit, x_um, y_um, explode=1.0):
    """Literal baseline loop with disposable inverse storage changes only."""
    tcount, directions, _, zsize, ysize, _ = filtered.shape
    xsize = grid.shape[-1]
    oz, oy, ox = grid.output_shape
    image = np.zeros((tcount, oz, oy, ox), np.float64)
    for t in range(tcount):
        for d in range(directions):
            for m in range(int(omit), grid.orders):
                padded = np.zeros(grid.output_shape, np.complex128)
                for k in range(zsize):
                    z = signed_fourier_index(k, zsize)
                    for i in range(ysize):
                        y = signed_fourier_index(i, ysize)
                        for j in range(xsize):
                            x = signed_fourier_index(j, xsize)
                            if x < 0:
                                zi, yi, xi = -z % zsize, -y % ysize, -x
                            else:
                                zi, yi, xi = z % zsize, y % ysize, x
                            even = filtered[t, d, 0 if m == 0 else 2 * m - 1, zi, yi, xi]
                            if x < 0:
                                even = even.conjugate()
                            value = even
                            if m:
                                odd = filtered[t, d, 2 * m, zi, yi, xi]
                                if x < 0:
                                    odd = odd.conjugate()
                                value += 1j * odd
                            padded[z % oz, y % oy, x % ox] = value
                _finite(padded, "embedded coefficients")
                # Same inverse interface, sign, default axes and normalization.
                # overwrite_x is permission; allocation/sharing is unestablished.
                if zsize == 1:
                    # Reuse initialized zeros; ONLY plane0 is transformed, A2 too.
                    spatial = padded
                    spatial[0] = cast(_C128, ifftn(padded[0], norm="forward", overwrite_x=True))
                else:
                    spatial = cast(_C128, ifftn(padded, norm="forward", overwrite_x=True))
                del padded
                _finite(spatial, "inverse transform result")
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * explode
                        * m
                        * (carriers[d, 0] * x_um[None, :] + carriers[d, 1] * y_um[:, None])
                    )
                    _finite(phase, "assembly carrier phase")
                    image[t] += 2 * (spatial * np.exp(1j * phase)).real
                _finite(image[t], "assembled image result")
                del spatial
    return image


def retained_control(filtered, grid, carriers, omit, x_um, y_um, explode=1.0):
    """Negative lifetime control; whole private buffer cleared each harmonic."""
    tcount, directions, _, zsize, ysize, _ = filtered.shape
    xsize = grid.shape[-1]
    oz, oy, ox = grid.output_shape
    image = np.zeros((tcount, oz, oy, ox), np.float64)
    padded = np.zeros(grid.output_shape, np.complex128)
    for t in range(tcount):
        for d in range(directions):
            for m in range(int(omit), grid.orders):
                padded[...] = 0
                for k in range(zsize):
                    z = signed_fourier_index(k, zsize)
                    for i in range(ysize):
                        y = signed_fourier_index(i, ysize)
                        for j in range(xsize):
                            x = signed_fourier_index(j, xsize)
                            if x < 0:
                                zi, yi, xi = -z % zsize, -y % ysize, -x
                            else:
                                zi, yi, xi = z % zsize, y % ysize, x
                            even = filtered[t, d, 0 if m == 0 else 2 * m - 1, zi, yi, xi]
                            if x < 0:
                                even = even.conjugate()
                            value = even
                            if m:
                                odd = filtered[t, d, 2 * m, zi, yi, xi]
                                if x < 0:
                                    odd = odd.conjugate()
                                value += 1j * odd
                            padded[z % oz, y % oy, x % ox] = value
                _finite(padded, "embedded coefficients")
                if zsize == 1:
                    spatial = np.zeros_like(padded)
                    spatial[0] = cast(_C128, ifftn(padded[0], norm="forward"))
                else:
                    spatial = cast(_C128, ifftn(padded, norm="forward"))
                # Keep padded alive through phase/accumulation and next embedding.
                _finite(spatial, "inverse transform result")
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * explode
                        * m
                        * (carriers[d, 0] * x_um[None, :] + carriers[d, 1] * y_um[:, None])
                    )
                    _finite(phase, "assembly carrier phase")
                    image[t] += 2 * (spatial * np.exp(1j * phase)).real
                _finite(image[t], "assembled image result")
                del spatial
    del padded
    return image


def child(condition, variant, repetition):
    """One proposed direct child, one closed row, no launch or grant validation.

    Existing independently rebound exact-PID apparatus would call this entry.
    The module hold makes that impossible in this source revision. A later
    reviewed revision must bind material identities before runtime admission.
    """
    if condition not in CONDITIONS or variant not in VARIANTS or repetition not in REPETITIONS:
        raise ValueError("outside closed FA120 proposed row inventory")
    # SOURCE CORRECTION1 / event2: qualification is a SEPARATE later ROOT
    # process. This child performs no preparation, filtering or public reference
    # reconstruction. Exact NPY/JSON bytes and bindings are currently UNBOUND.
    fixture_directory = Path(FIXTURE_ROOT) / condition
    load_started_ns = time.monotonic_ns()
    with (fixture_directory / "grid.json").open(encoding="utf-8") as source:
        metadata = json.load(source)
    filtered = np.load(fixture_directory / "filtered.npy", allow_pickle=False)
    resolved_carriers = np.load(fixture_directory / "carriers.npy", allow_pickle=False)
    x_um = np.load(fixture_directory / "x_um.npy", allow_pickle=False)
    y_um = np.load(fixture_directory / "y_um.npy", allow_pickle=False)
    # The public KnownReconstruction arrays are read-only. Qualification must
    # establish these exact C-contiguous values/layouts before freezing files.
    for value in (filtered, resolved_carriers, x_um, y_um):
        value.setflags(write=False)
    grid = kp._Grid(
        tuple(metadata["grid_shape"]),
        metadata["orders"],
        metadata["lateral_zoom"],
        metadata["axial_zoom"],
        metadata["dxy_um"],
        metadata["dz_um"],
        metadata["input_scale"],
        metadata["acquisition_mode"],
    )
    load_ended_ns = time.monotonic_ns()
    # This is one declared kernel caller: four arrays and the existing grid.
    # No raw/bands/transfer/modulation/reference image is loaded or retained.
    # File qualification and material binding are external review obligations;
    # json.load/np.load here are not a general validator or admission mechanism.
    before_identities = {
        "filtered": identity(filtered, "filtered"),
        "carriers": identity(resolved_carriers, "carriers"),
        "x_um": identity(x_um, "x_um"),
        "y_um": identity(y_um, "y_um"),
    }
    operation = {"baseline": baseline, "candidate": candidate, "retained-control": retained_control}[variant]
    # Do not add profiler/ownership probes here. ROOT's existing external
    # apparatus supplies separately sampled RSS and terminal direct-child wait4.
    pre_call_ns = time.monotonic_ns()
    pre_call_high_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with kp._operation():
        started_ns = time.monotonic_ns()
        image = operation(filtered, grid, resolved_carriers, metadata["omit_order0"], x_um, y_um, metadata["explode_factor"])
        ended_ns = time.monotonic_ns()
    call_end_high_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    call_end_observed_ns = time.monotonic_ns()
    output_identity = identity(image, "image")
    after_identities = {
        "filtered": identity(filtered, "filtered"),
        "carriers": identity(resolved_carriers, "carriers"),
        "x_um": identity(x_um, "x_um"),
        "y_um": identity(y_um, "y_um"),
    }
    if before_identities != after_identities:
        raise RuntimeError("FA120 caller or filtered-input identity changed")
    # A later ROOT-bound revision supplies a unique exclusive-create artifact
    # path for this row. Retain complete canonical bytes for exact comparison;
    # hashes alone do not perform a byte comparison. Archival is outside timing
    # and can contaminate whole-process high-water equally for all variants.
    with open(OUTPUT_IMAGE_PATH, "xb") as output:
        output.write(np.ascontiguousarray(image, dtype=image.dtype.newbyteorder("<")).tobytes())
    post_observation_high_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    post_observation_ns = time.monotonic_ns()
    payload = {
        "status": "OBSERVATION_ONLY_NOT_ACCEPTANCE",
        "condition": condition,
        "variant": variant,
        "repetition": repetition,
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "actual119_parent": ACTUAL_119_PARENT,
        "candidate": ACTUAL_CANDIDATE,
        "environment": ACTUAL_ENVIRONMENT,
        "grant": ACTUAL_GRANT,
        "fixture_directory": str(fixture_directory),
        "fixture_file_hashes": FIXTURE_FILE_HASHES,
        "fixture_loading_started_ns": load_started_ns,
        "fixture_loading_ended_ns": load_ended_ns,
        "fixture_loading_seconds": (load_ended_ns - load_started_ns) / 1_000_000_000,
        "input_identities_before": before_identities,
        "input_identities_after": after_identities,
        "output_identity": output_identity,
        "output_complete_little_endian_bytes_path": OUTPUT_IMAGE_PATH,
        "output_shape": image.shape,
        "output_dtype": image.dtype.str,
        "output_strides": image.strides,
        "output_owns_data": bool(image.flags.owndata),
        "output_writeable": bool(image.flags.writeable),
        "native_high_water_units": "Linux KiB",
        "native_high_water_multiplier_to_bytes": 1024,
        "pre_call_high_water_native": pre_call_high_kib,
        "call_end_high_water_native": call_end_high_kib,
        "post_observation_high_water_native": post_observation_high_kib,
        "pre_call_snapshot_ns": pre_call_ns,
        "kernel_started_ns": started_ns,
        "kernel_ended_ns": ended_ns,
        "call_end_snapshot_ns": call_end_observed_ns,
        "post_observation_snapshot_ns": post_observation_ns,
        "kernel_seconds": (ended_ns - started_ns) / 1_000_000_000,
        "terminal_direct_child_usage": "EXTERNAL_EXISTING_WAIT_OWNER_REQUIRED",
        "sampled_current_rss": "EXTERNAL_EXISTING_OBSERVER_REQUIRED",
        "limits": "whole-process includes imports/loading/hash/archive/observation; cumulative highs are not kernel peaks; masked effects are inconclusive",
    }
    print(json.dumps(payload, sort_keys=True), flush=True)
    return None


def _fixed_cli():
    """UNAPPLIED owner proposal: one exact config and one child call, no driver.

    The unconditional module HOLD remains before imports. Actual executable
    child source identity is UNBOUND; this held proposal is not that revision.
    Existing apparatus hashes/reconciles the one ROOT-frozen config and fixture
    files externally. This fixed entry does not supply resource authority.
    """
    global ACTUAL_119_PARENT, ACTUAL_CANDIDATE, ACTUAL_ENVIRONMENT, ACTUAL_GRANT
    global FIXTURE_ROOT, FIXTURE_FILE_HASHES, OUTPUT_IMAGE_PATH
    if len(sys.argv) != 3 or sys.argv[1] != "--fa120-config":
        raise ValueError("one literal --fa120-config path required")
    with open(sys.argv[2], encoding="utf-8") as source:
        config = json.load(source)
    if set(config) != {
        "condition", "variant", "repetition", "actual119_parent", "candidate",
        "environment", "grant", "fixture_root", "fixture_file_hashes", "output_image_path",
    }:
        raise ValueError("exact fixed FA120 config fields required")
    if type(config["repetition"]) is not int:
        raise ValueError("integer fixed repetition required")
    ACTUAL_119_PARENT = config["actual119_parent"]
    ACTUAL_CANDIDATE = config["candidate"]
    ACTUAL_ENVIRONMENT = config["environment"]
    ACTUAL_GRANT = config["grant"]
    FIXTURE_ROOT = config["fixture_root"]
    FIXTURE_FILE_HASHES = config["fixture_file_hashes"]
    OUTPUT_IMAGE_PATH = config["output_image_path"]
    child(config["condition"], config["variant"], config["repetition"])


if __name__ == "__main__":
    _fixed_cli()
