"""RA13 finite public-boundary controls; generator truth never enters workflow.

Settings were frozen in artifacts/ra13/A1/design-frozen.md before RA13 probes.
Calibration generation reuses the expressly permitted RA12 fixture. The sparse
specimen expectation below independently sums the public finite optical equation.
"""

import hashlib
import math
from typing import Any

import numpy as np
from scipy.special import j0, roots_legendre
from scripts.image_only_calibration_handoff import infer_calibration_handoff
from scripts.image_only_specimen_fit import fit_specimen

from image_only_calibration_handoff_fixture import (
    candidate,
    physical_transfer,
    prediction,
)
from simrecon import estimate_scalar_camera

CAL_SHAPE = (1, 3, 24)
CAL_D = (0.125, 0.080, 0.080)
CAL_ORIGIN = (-0.25, 0.31, -0.27)
SPEC_SHAPE = (2, 2, 3)
SPEC_D = (0.21, 0.17, 0.11)
SPEC_ORIGIN = (0.12, -0.19, 0.43)
ARRAY_NAMES = (
    "specimen_counts",
    "dark_counts",
    "blank_counts",
    "flat_counts",
    "central_counts",
    "structured_counts",
    "heldout_counts",
)
CONTROL_NAMES = (
    "sweep_scales",
    "max_refinement_evaluations",
    "training_rms_limit",
    "calibration_atol",
    "operator_atol",
    "regularization",
    "max_iterations",
    "max_backtracking_trials",
)


def controls() -> dict[str, Any]:
    return dict(
        calibration_id=" RA13 paired acquisition ",
        specimen_calibration_id=" RA13 paired acquisition ",
        calibration_origin_um_zyx=CAL_ORIGIN,
        specimen_detector_spacing_um_zyx=SPEC_D,
        specimen_origin_um_zyx=SPEC_ORIGIN,
        sweep_scales=(float.fromhex("0x0.0000000000001p-1022"),),
        max_refinement_evaluations=1,
        training_rms_limit=1_000_000,
        calibration_atol=1e-4,
        operator_atol=4,
        regularization=0.01,
        max_iterations=1,
        max_backtracking_trials=4,
        source=" RA13 observation-only finite control ",
    )


def unavailable_inputs() -> dict[str, Any]:
    """Small signed legal inputs with exactly zero observed camera contrast."""
    return dict(
        controls(),
        specimen_counts=np.full((3, 5, *SPEC_SHAPE), -3.0),
        dark_counts=np.full((2, 2, 2), -2.0),
        blank_counts=np.full((2, 2, 2), 7.0),
        flat_counts=np.full((2, 2, 2), 7.0),
        central_counts=np.full((1, 2, 2), -1.0),
        structured_counts=np.full((3, 9, 1, 2, 2), -2.0),
        heldout_counts=np.full((3, 5, 1, 2, 2), -3.0),
    )


def logical_sha256(array: np.ndarray) -> str:
    """Hash one original element slice at a time; preserve dtype/endian/zero bits."""
    digest = hashlib.sha256()
    for index in np.ndindex(array.shape):
        element = array[tuple(slice(i, i + 1) for i in index)]
        digest.update(element.tobytes())
    return digest.hexdigest()


def sparse_source() -> np.ndarray:
    source = np.zeros((2, 4, 6), dtype=np.float32)
    source[0, 1, 0] = 0.7
    source[1, 2, 4] = 1.1
    return source


def direct_specimen(source, carriers, phases, beams) -> np.ndarray:
    """Tiny independent complex-field/pupil/pixel finite sum, no inverse calls.

    Integrated weights; source-minus-focus z; half-cell coordinates; pixel area.
    Uses a canonical Q128 rule and public SciPy Bessel evaluation in float64.
    This observer does not assert continuum or source-grid accuracy.
    """
    nodes, weights = roots_legendre(128)
    u, weights = (nodes + 1) / 2, weights / 2
    radius = 1.4 / 0.525
    nu, beta = 1.515 / 0.525, 1.4 / 1.515
    out = np.zeros((3, 5, *SPEC_SHAPE))
    a0, ap, am = beams
    norm = sum(float(a) ** 2 for a in beams)
    for cell in np.argwhere(source != 0):
        z, y, x = (cell + 0.5) * np.array(SPEC_D) / (1, 2, 2)
        mass = float(source[tuple(cell)])
        for k, iy, ix in np.ndindex(SPEC_SHAPE):
            d = z - (k + 0.5) * SPEC_D[0]
            pixel_response = 0.0
            for py, px in np.ndindex(2, 2):
                ry = (iy + (py + 0.5) / 2) * SPEC_D[1] - y
                rx = (ix + (px + 0.5) / 2) * SPEC_D[2] - x
                radial = np.hypot(ry, rx)
                pupil = np.sum(
                    weights
                    * j0(2 * math.pi * radius * np.sqrt(u) * radial)
                    * np.exp(2j * math.pi * nu * d * (np.sqrt(1 - beta**2 * u) - 1))
                )
                pixel_response += math.pi * radius**2 * abs(pupil) ** 2
            pixel_response *= SPEC_D[1] * SPEC_D[2] / 4
            for o in range(3):
                qy, qx = carriers[o]
                k0 = 1.515 / 0.488
                q2 = qy * qy + qx * qx
                kappa = q2 / (k0 + math.sqrt(k0 * k0 - q2))
                theta = 2 * math.pi * (qy * y + qx * x) + phases[o]
                field = (
                    a0 * np.exp(2j * math.pi * kappa * d)
                    + ap * np.exp(1j * theta)
                    + am * np.exp(-1j * theta)
                )
                out[o, :, k, iy, ix] += mass * pixel_response * np.abs(field) ** 2 / norm
    return out


def finite_inputs(*, noisy=False, strict_diagnostic=False) -> dict[str, Any]:
    """Truth is used solely for observation generation, never included in kwargs."""
    truth = candidate(shape=CAL_SHAPE)
    central, structured = prediction(truth, CAL_SHAPE)
    phases = physical_transfer(truth.phases_rad, truth.carriers_yx_per_um, CAL_ORIGIN, SPEC_ORIGIN)
    specimen = direct_specimen(
        sparse_source(), truth.carriers_yx_per_um, phases, truth.beam_amplitudes
    )
    inputs = dict(
        controls(),
        dark_counts=np.full((2, 2, 2), -2.0),
        blank_counts=np.full((2, 2, 2), 7.0),
        flat_counts=np.full((2, 2, 2), 11.0),
        central_counts=7 + 4 * central,
        structured_counts=7 + 4 * structured,
        heldout_counts=7 + 4 * structured[:, :5],
        specimen_counts=7 + 4 * specimen,
    )
    if noisy:
        rng = np.random.default_rng(130013)

        def draw(signal):
            return -2 + 2 * (rng.poisson(4.5 + 2 * signal) + rng.normal(0, 0.25, signal.shape))

        inputs.update(
            dark_counts=-2 + 2 * rng.normal(0, 0.25, (8, 4, 4)),
            blank_counts=draw(np.zeros((8, 4, 4))),
            flat_counts=draw(np.ones((8, 4, 4))),
            central_counts=draw(central),
            structured_counts=draw(structured),
            heldout_counts=draw(structured[:, :5]),
            specimen_counts=draw(specimen),
        )
        inputs["source"] = " RA13 fixed noisy diagnostic; no recovery claim "
    if strict_diagnostic:
        inputs["training_rms_limit"] = 0
    return inputs


def explicit_handoff(inputs, camera):
    return infer_calibration_handoff(
        inputs["central_counts"],
        **{k: inputs[k] for k in ("structured_counts", "heldout_counts")},
        camera_estimate=camera,
        calibration_origin_um_zyx=inputs["calibration_origin_um_zyx"],
        specimen_detector_shape_zyx=inputs["specimen_counts"].shape[2:],
        **{
            k: inputs[k]
            for k in (
                "specimen_detector_spacing_um_zyx",
                "specimen_origin_um_zyx",
                "sweep_scales",
                "max_refinement_evaluations",
                "training_rms_limit",
                "calibration_atol",
                "operator_atol",
                "source",
            )
        },
    )


def explicit_fit(inputs, descriptor):
    return fit_specimen(
        inputs["specimen_counts"],
        camera_estimate=descriptor.camera_estimate,
        carriers_yx_per_um=descriptor.carriers_yx_per_um,
        phases_at_specimen_origin_rad=descriptor.phases_at_specimen_origin_rad,
        beam_amplitudes=descriptor.beam_amplitudes,
        illumination_source=descriptor.illumination_source,
        detector_spacing_um_zyx=descriptor.detector_spacing_um_zyx,
        specimen_origin_um_zyx=descriptor.specimen_origin_um_zyx,
        pupil_order=descriptor.pupil_order,
        **{k: inputs[k] for k in ("regularization", "max_iterations", "max_backtracking_trials")},
    )


def composition(inputs):
    camera = estimate_scalar_camera(
        inputs["dark_counts"],
        **{k: inputs[k] for k in ("blank_counts", "flat_counts", "source")},
    )
    handoff = explicit_handoff(inputs, camera)
    fit = (
        explicit_fit(inputs, handoff.specimen) if handoff.status == "predictive_estimate" else None
    )
    return camera, handoff, fit
