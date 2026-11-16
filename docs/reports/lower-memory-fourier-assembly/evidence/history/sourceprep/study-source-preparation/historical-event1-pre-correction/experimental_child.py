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
import time
from typing import cast

import numpy as np
from scipy.fft import ifftn

from simrecon import prepare_acquisition_bands, reconstruct_known
from simrecon.reconstruction import known_parameters as kp
from reconstruction_summary_fixture import identity, workload


SOURCE_REFERENCE = "158776ade28079276304d49a6b973eccbf4109c9"
SOURCE_SHA256 = "edb87b64e1691b7f437194aabc0df8d4ab22e3e67b6b05639dbd3bad26e2c645"
ACTUAL_119_PARENT = "UNBOUND"
ACTUAL_CANDIDATE = "UNBOUND"
ACTUAL_ENVIRONMENT = "UNBOUND"
ACTUAL_GRANT = "UNBOUND"
OUTPUT_IMAGE_PATH = "UNBOUND"
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
    shape, mode, axial = CONDITIONS[condition]
    case = workload(shape, search=False, mode=mode, layout="radial")
    case["acquisition"]["axial_zoom"] = axial
    # phase_policy is a workflow adapter declaration. Direct CE06 preparation
    # uses phases_rad=None (uniform) and has no phase_policy argument.
    acquisition = dict(case["acquisition"])
    del acquisition["phase_policy"]
    bands = prepare_acquisition_bands(case["specimen"], **acquisition)
    directions = shape[1]
    angles = np.arange(directions, dtype=np.float64) * np.pi / directions
    carriers = np.column_stack((np.cos(angles), np.sin(angles))) / 8
    modulation = np.empty((directions, 2), dtype=np.complex128)
    for d in range(directions):
        modulation[d] = np.array([0.5 + 0.25j, 0.25 - 0.125j]) * (1 + d / 16)
    # Parameters are explicit supplied values, NOT fitted truth/recovery claims.
    # Public filtering supplies exact native inputs for all three variants.
    known = reconstruct_known(
        bands,
        case["transfer"],
        carriers_cyc_um=carriers,
        modulation=modulation,
        **case["optics"],
        **case["filtering"],
    )
    filtered = known.filtered_quadratures
    x_um, y_um, z_um = known.x_um, known.y_um, known.z_um
    resolved_carriers, resolved_modulation = known.carriers_cyc_um, known.modulation
    # This baseline public setup image is never retained during the kernel call.
    # Its earlier high-water can mask the kernel peak; no subtraction repairs it.
    # BLOCKING METHOD REVIEW: equal terminal peaks with setup dominance cannot
    # justify a lower-peak no-go; whole-process effect would be inconclusive.
    del known
    grid, used = kp._validate_bands(bands)
    del used
    before_identities = {
        "specimen": identity(case["specimen"], "specimen"),
        "transfer": identity(case["transfer"].samples, "transfer.samples"),
        "bands": identity(bands.quadratures, "bands.quadratures"),
        "noise": identity(bands.noise_variance_factors, "bands.noise_variance_factors"),
        "filtered": identity(filtered, "filtered"),
        "carriers": identity(resolved_carriers, "carriers"),
        "modulation": identity(resolved_modulation, "modulation"),
        "x_um": identity(x_um, "x_um"),
        "y_um": identity(y_um, "y_um"),
        "z_um": identity(z_um, "z_um"),
    }
    operation = {"baseline": baseline, "candidate": candidate, "retained-control": retained_control}[variant]
    # Do not add profiler/ownership probes here. ROOT's existing external
    # apparatus supplies separately sampled RSS and terminal direct-child wait4.
    pre_call_ns = time.monotonic_ns()
    pre_call_high_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with kp._operation():
        started_ns = time.monotonic_ns()
        image = operation(filtered, grid, resolved_carriers, False, x_um, y_um, 1.0)
        ended_ns = time.monotonic_ns()
    call_end_high_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    call_end_observed_ns = time.monotonic_ns()
    output_identity = identity(image, "image")
    after_identities = {
        "specimen": identity(case["specimen"], "specimen"),
        "transfer": identity(case["transfer"].samples, "transfer.samples"),
        "bands": identity(bands.quadratures, "bands.quadratures"),
        "noise": identity(bands.noise_variance_factors, "bands.noise_variance_factors"),
        "filtered": identity(filtered, "filtered"),
        "carriers": identity(resolved_carriers, "carriers"),
        "modulation": identity(resolved_modulation, "modulation"),
        "x_um": identity(x_um, "x_um"),
        "y_um": identity(y_um, "y_um"),
        "z_um": identity(z_um, "z_um"),
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
        "limits": "setup includes public baseline reconstruction; cumulative highs are not kernel peaks",
    }
    print(json.dumps(payload, sort_keys=True), flush=True)
    return None


# No __main__ runner: no default row, argv parser, launcher or resource authority.
# PENDING existing-apparatus target: import this exact module; child(closed row).
