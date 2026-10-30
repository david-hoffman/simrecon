"""Evaluate RA03 source representations and fixed-gauge illumination controls.

This module composes the public finite optical and inverse maps. It estimates
nothing and performs no archive access, registration or fitted rescaling.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scripts.simulation_inverse_operator import build_kernel_cache, forward
from scripts.simulation_optics import expected_images

Array = NDArray[np.float64]


def _finite(value: Any, name: str) -> None:
    if not np.isfinite(value).all():
        raise ValueError(f"{name} contains nonfinite values")


def _array(value: Any, name: str, *, width: int | None = None) -> Array:
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        raise ValueError(f"{name} must be a plain real ndarray")
    if width is not None and (value.dtype.kind != "f" or value.dtype.itemsize != width):
        raise ValueError(f"{name} must have float{8 * width} dtype")
    _finite(value, name)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = np.asarray(value, dtype=np.float64)
    _finite(result, name)
    return result


def _scalar(value: Any, name: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be an ordinary numerical scalar")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} is not finite float64") from error
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _triple(value: Any, name: str, *, positive: bool = False) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name} must contain three ordinary numerical coordinates")
    return tuple(_scalar(v, name, positive=positive) for v in value)


def _shape(value: Array, shape: tuple[int, ...], name: str) -> None:
    if value.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")


def _metric_row(reference: Array, prediction: Array) -> dict[str, Any]:
    # Work on one frame at a time; do not retain a full-volume difference for
    # every arm. Extreme-range reductions have no universal success promise.
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        delta = prediction - reference
        error = float(np.linalg.norm(delta.ravel()))
        norm = float(np.linalg.norm(reference.ravel()))
        maximum = float(np.max(np.abs(delta)))
        mean = float(np.mean(delta))
        relative = None if norm == 0 else error / norm
    values = [error, norm, maximum, mean]
    if relative is not None:
        values.append(relative)
    _finite(values, "metric reductions")
    return dict(
        count=reference.size,
        error_l2=error,
        reference_l2=norm,
        relative_l2=relative,
        max_abs=maximum,
        mean_difference=mean,
        rms_difference=error / math.sqrt(reference.size),
    )


def summarize_errors(reference: Any, predictions: Any) -> dict[str, Any]:
    """Report signed frame errors and ratios of global norms, without fitting."""
    ref = _array(reference, "reference")
    if ref.ndim not in (4, 5) or 0 in ref.shape:
        raise ValueError("reference must be nonempty rank four or five")
    if type(predictions) is not dict or not predictions:
        raise ValueError("predictions must be a nonempty plain dict")
    ref5 = ref[None] if ref.ndim == 4 else ref
    result = {}
    for name, value in predictions.items():
        if type(name) is not str or not name:
            raise ValueError("prediction arm names must be nonempty strings")
        pred = _array(value, f"prediction {name}")
        _shape(pred, ref.shape, f"prediction {name}")
        pred5 = pred[None] if pred.ndim == 4 else pred
        frames = [
            dict(orientation=o, phase=p, **_metric_row(ref5[o, p], pred5[o, p]))
            for o in range(ref5.shape[0])
            for p in range(ref5.shape[1])
        ]
        error = math.hypot(*(row["error_l2"] for row in frames))
        norm = math.hypot(*(row["reference_l2"] for row in frames))
        relative = None if norm == 0 else error / norm
        # Weight frame means by element count; all frames here have equal size.
        mean = math.fsum(row["mean_difference"] / len(frames) for row in frames)
        _finite([error, norm, mean], "aggregate metric reductions")
        if relative is not None:
            _finite(relative, "aggregate relative_l2")
        result[name] = dict(
            frames=frames,
            aggregate=dict(
                count=ref.size,
                error_l2=error,
                reference_l2=norm,
                relative_l2=relative,
                max_abs=max(row["max_abs"] for row in frames),
                mean_difference=mean,
                rms_difference=error / math.sqrt(ref.size),
            ),
        )
    return result


def fixed_center_views(
    volume: Any, *, spacing_um_zyx: Any, origin_um_zyx: Any, center_um_zyx: Any
) -> dict[str, Any]:
    """Return unnormalized projections and nearest fixed half-cell planes."""
    data = _array(volume, "volume")
    if data.ndim != 3 or 0 in data.shape:
        raise ValueError("volume must be nonempty rank three")
    spacing = _triple(spacing_um_zyx, "spacing_um_zyx", positive=True)
    origin = _triple(origin_um_zyx, "origin_um_zyx")
    center = _triple(center_um_zyx, "center_um_zyx")
    indices, coordinates = [], []
    for n, d, start, target in zip(data.shape, spacing, origin, center, strict=True):
        # Rational geometry preserves inclusive faces and first-index ties even
        # when rounded physical coordinates would erase the distinction.
        distance = (Fraction(target) - Fraction(start)) / Fraction(d)
        if not 0 <= distance <= n:
            raise ValueError("center_um_zyx lies outside the volume field")
        lower = math.floor(distance)
        index = lower - 1 if distance == lower else lower
        index = min(n - 1, max(0, index))
        try:
            coordinate = float(Fraction(start) + Fraction(2 * index + 1, 2) * Fraction(d))
        except OverflowError as error:
            raise ValueError("nonfinite selected plane coordinate") from error
        _finite(coordinate, "selected plane coordinate")
        indices.append(index)
        coordinates.append(coordinate)
    return dict(
        indices_zyx=tuple(indices),
        coordinates_um_zyx=tuple(coordinates),
        xy_mip=data.max(axis=0).copy(),
        xz_mip=data.max(axis=1).copy(),
        xy_slice=data[indices[0]].copy(),
        xz_slice=data[:, indices[1]].copy(),
    )


def _transfer(
    carrier: Array, phases: Array, calibration: tuple[float, ...], specimen: tuple[float, ...]
) -> Array:
    # Only the origin products are cycle-valued and may be reduced modulo one.
    # Evaluate each radian phase directly, then rotate its phasor. Dividing a
    # huge radian angle by rounded 2*pi changes its period; adding the small
    # origin angle directly to that huge phase can instead lose the shift.
    turns = sum(
        (
            Fraction(float(carrier[a])) * (Fraction(specimen[a + 1]) - Fraction(calibration[a + 1]))
            for a in (0, 1)
        ),
        Fraction(),
    )
    turns = (turns + Fraction(1, 2)) % 1 - Fraction(1, 2)
    origin_angle = float(turns) * math.tau
    origin_cos, origin_sin = math.cos(origin_angle), math.sin(origin_angle)
    transferred = []
    for phi in phases:
        phase_cos, phase_sin = math.cos(float(phi)), math.sin(float(phi))
        transferred.append(
            math.atan2(
                phase_sin * origin_cos + phase_cos * origin_sin,
                phase_cos * origin_cos - phase_sin * origin_sin,
            )
        )
    return np.array(transferred)


def evaluate_orientation(
    fine_source_e: Any,
    reference_signal_e: Any,
    original_source_relative: Any,
    original_prediction_relative: Any,
    *,
    detector_spacing_um_zyx: Any,
    true_carrier_yx_per_um: Any,
    estimated_carrier_yx_per_um: Any,
    true_phases_at_calibration_origin_rad: Any,
    estimated_phases_at_calibration_origin_rad: Any,
    true_beam_amplitudes: Any,
    estimated_beam_amplitudes: Any,
    calibration_origin_um_zyx: Any,
    specimen_origin_um_zyx: Any,
    source_to_relative: Any,
    excitation_um: Any,
    emission_um: Any,
    refractive_index: Any,
    detection_na: Any,
    pupil_order: Any,
) -> dict[str, Any]:
    """Compose one orientation's paired-source and calibration-gauge controls.

    Archived fine means are converted by the supplied camera gauge, never
    regenerated. Generator/inverse discrepancies combine their stated errors;
    they do not isolate kernel rounding or establish physical accuracy.
    """
    fine = _array(fine_source_e, "fine_source_e", width=8)
    reference = _array(reference_signal_e, "reference_signal_e", width=8)
    original = _array(original_source_relative, "original_source_relative", width=4)
    prediction = _array(original_prediction_relative, "original_prediction_relative", width=8)
    if fine.ndim != 3 or 0 in fine.shape or any(n % 2 for n in fine.shape):
        raise ValueError("fine_source_e must have nonempty shape (2Nz,2Ny,2Nx)")
    if np.any(fine < 0):
        raise ValueError("fine_source_e must be nonnegative")
    detector_shape = tuple(n // 2 for n in fine.shape)
    if reference.ndim != 4 or reference.shape[0] == 0:
        raise ValueError("reference_signal_e must have nonempty shape (P,Nz,Ny,Nx)")
    _shape(reference, (reference.shape[0], *detector_shape), "reference_signal_e")
    if np.any(reference < 0):
        raise ValueError("reference_signal_e must be nonnegative")
    _shape(original, (detector_shape[0], fine.shape[1], fine.shape[2]), "original_source_relative")
    _shape(prediction, reference.shape, "original_prediction_relative")
    tq = _array(true_carrier_yx_per_um, "true_carrier_yx_per_um")
    eq = _array(estimated_carrier_yx_per_um, "estimated_carrier_yx_per_um")
    tp = _array(true_phases_at_calibration_origin_rad, "true_phases_at_calibration_origin_rad")
    ep = _array(
        estimated_phases_at_calibration_origin_rad, "estimated_phases_at_calibration_origin_rad"
    )
    _shape(tq, (2,), "true_carrier_yx_per_um")
    _shape(eq, (2,), "estimated_carrier_yx_per_um")
    _shape(tp, (len(reference),), "true_phases_at_calibration_origin_rad")
    _shape(ep, (len(reference),), "estimated_phases_at_calibration_origin_rad")
    calibration = _triple(calibration_origin_um_zyx, "calibration_origin_um_zyx")
    specimen = _triple(specimen_origin_um_zyx, "specimen_origin_um_zyx")
    scale = _scalar(source_to_relative, "source_to_relative", positive=True)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        paired64 = (fine[0::2] + fine[1::2]) * scale
        paired32 = paired64.astype(np.float32)
        fine_reference = reference * scale
    _finite(paired64, "paired64")
    _finite(paired32, "paired32")
    _finite(fine_reference, "fine_reference")
    # Validate physical settings at their existing public boundary before using
    # normalized detector spacing to derive the inverse source spacing.
    true_specimen_phases = _transfer(tq, tp, calibration, specimen)
    optics = dict(
        excitation_um=excitation_um,
        emission_um=emission_um,
        refractive_index=refractive_index,
        detection_na=detection_na,
        pupil_order=pupil_order,
    )
    generator_settings = dict(
        detector_spacing_um_zyx=detector_spacing_um_zyx,
        source_refinement_zyx=(1, 2, 2),
        carriers_yx_per_um=tq[None],
        phases_rad=true_specimen_phases[None],
        beam_amplitudes=true_beam_amplitudes,
        pixel_subsamples_yx=(2, 2),
        **optics,
    )
    arrays = dict(
        fine_reference=fine_reference,
        paired_generator64_true=expected_images(paired64, **generator_settings)[0].copy(),
        paired_generator32_true=expected_images(paired32.astype(np.float64), **generator_settings)[
            0
        ].copy(),
    )
    dz, dy, dx = map(float, detector_spacing_um_zyx)
    cache = build_kernel_cache(
        source_shape_zyx=paired32.shape,
        source_spacing_um_zyx=(dz, dy / 2, dx / 2),
        emission_um=emission_um,
        refractive_index=refractive_index,
        detection_na=detection_na,
        pupil_order=pupil_order,
    )
    settings = {
        "paired_inverse_true": (tq, tp, true_beam_amplitudes),
        "paired_inverse_estimated": (eq, ep, estimated_beam_amplitudes),
        "paired_inverse_carrier_only": (eq, tp, true_beam_amplitudes),
        "paired_inverse_phase_only": (tq, ep, true_beam_amplitudes),
        "paired_inverse_beam_only": (tq, tp, estimated_beam_amplitudes),
        "original_fit_reapplied": (eq, ep, estimated_beam_amplitudes),
    }
    interpretations = {
        "paired_inverse_true": "True illumination on the represented paired source.",
        "paired_inverse_estimated": "All estimated illumination settings; no fit.",
        "paired_inverse_carrier_only": "Estimated carrier with true calibration phases and beams.",
        "paired_inverse_phase_only": "Estimated calibration phases with true carrier and beams.",
        "paired_inverse_beam_only": "Estimated ordered beams with true carrier and phases.",
        "original_fit_reapplied": "Archived source reapplied with estimated settings; no refit.",
    }
    arms = {}
    for name, (q, phases, beams) in settings.items():
        transferred = _transfer(q, phases, calibration, specimen)
        use_original = name == "original_fit_reapplied"
        arrays[name] = forward(
            original_source_relative if use_original else paired32,
            kernel_cache=cache,
            carrier_yx_per_um=q,
            phases_rad=transferred,
            beam_amplitudes=beams,
            excitation_um=excitation_um,
        )
        arms[name] = dict(
            carrier_yx_per_um=q.copy(),
            phases_at_calibration_origin_rad=phases.copy(),
            phases_at_specimen_origin_rad=transferred.copy(),
            calibration_origin_um_zyx=tuple(calibration_origin_um_zyx),
            specimen_origin_um_zyx=tuple(specimen_origin_um_zyx),
            beam_amplitudes=tuple(beams),
            source="original_source_relative" if use_original else "paired32",
            interpretation=interpretations[name],
        )
    arrays["original_prediction"] = prediction.copy()
    for name, value in arrays.items():
        _finite(value, name)
    cast_metrics = _metric_row(paired64, paired32.astype(np.float64))
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        delta = paired32.astype(np.float64) - paired64
    try:
        sum_change = math.fsum(delta.flat)
    except OverflowError as error:
        raise ValueError("nonfinite rounding sum_change") from error
    _finite(sum_change, "rounding sum_change")
    return dict(
        arrays=arrays,
        sources=dict(paired64=paired64, paired32=paired32),
        arms=arms,
        metrics=summarize_errors(
            fine_reference,
            {name: value for name, value in arrays.items() if name != "fine_reference"},
        ),
        rounding=dict(
            relative_l2=cast_metrics["relative_l2"],
            max_abs=cast_metrics["max_abs"],
            sum_change=sum_change,
            nonzero_lost=int(np.count_nonzero((paired64 != 0) & (paired32 == 0))),
            changed_coefficients=int(np.count_nonzero(paired32 != paired64)),
        ),
    )
