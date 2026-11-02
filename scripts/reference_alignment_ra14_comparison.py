"""Replay the declared production operator and summarize full-array differences."""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, NoReturn

import numpy as np
from numpy.typing import NDArray
from scripts.simulation_inverse_operator import build_kernel_cache, forward

from simrecon import SimreconError

Array = NDArray[Any]
Scaled = tuple[float, int]
_BLOCK = 65536


@dataclass(frozen=True)
class UnavailableMetric:
    """Identify one statistic whose declared finite value is unavailable."""

    field: str
    reason: str


@dataclass(frozen=True)
class MetricSummary:
    """Bind descriptive statistics without imposing an acceptance threshold."""

    count: int
    reference_l2: float | None
    error_l2: float | None
    relative_l2: float | None
    error_rms: float | None
    error_max_abs: float | None
    error_mean: float | None
    unavailable_fields: tuple[UnavailableMetric, ...]


def _invalid(field: str) -> NoReturn:
    raise SimreconError("invalid_reference_alignment_ra14", f"Invalid {field}.")


def _array(value: Any, field: str, widths: tuple[int, ...], *, native: bool = True) -> Array:
    if (
        type(value) is not np.ndarray
        or value.dtype.kind != "f"
        or value.dtype.itemsize not in widths
        or (native and not value.dtype.isnative)
        or value.size == 0
        or not np.all(np.isfinite(value))
    ):
        _invalid(field)
    return value


def replay_source(
    source_relative: Array,
    *,
    source_spacing_um_zyx: tuple[float, float, float],
    carriers_yx_per_um: Array,
    phases_at_specimen_origin_rad: Array,
    beam_amplitudes: Array,
    pupil_order: int,
) -> NDArray[np.float64]:
    """Apply all supplied orientations and phases in source-relative units."""
    source = _array(source_relative, "source_relative", (4,), native=False)
    if source.ndim != 3 or source.shape[1] % 2 or source.shape[2] % 2:
        _invalid("source_relative shape")
    spacing = source_spacing_um_zyx
    if type(spacing) is not tuple or len(spacing) != 3:
        _invalid("source_spacing_um_zyx")
    for value in spacing:
        if type(value) not in (int, float):
            _invalid("source_spacing_um_zyx")
        try:
            step = float(value)
        except OverflowError:
            _invalid("source_spacing_um_zyx")
        if not math.isfinite(step) or step <= 0:
            _invalid("source_spacing_um_zyx")
    carriers = _array(carriers_yx_per_um, "carriers_yx_per_um", (8,))
    phases = _array(phases_at_specimen_origin_rad, "phases_at_specimen_origin_rad", (8,))
    beams = _array(beam_amplitudes, "beam_amplitudes", (8,))
    if carriers.shape != (3, 2):
        _invalid("carriers_yx_per_um shape")
    if phases.shape != (3, 5):
        _invalid("phases_at_specimen_origin_rad shape")
    if beams.shape != (3,) or np.any(beams < 0) or not np.any(beams > 0):
        _invalid("beam_amplitudes")
    # Exact represented-value domain check, including points on the boundary.
    wave_squared = (Fraction(1.515) / Fraction(0.488)) ** 2
    for qy, qx in carriers:
        if Fraction(float(qy)) ** 2 + Fraction(float(qx)) ** 2 > wave_squared:
            _invalid("carriers_yx_per_um propagating domain")
    if type(pupil_order) is not int or pupil_order < 1:
        _invalid("pupil_order")

    cache = build_kernel_cache(
        source_shape_zyx=source.shape,
        source_spacing_um_zyx=tuple(float(v) for v in spacing),
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=pupil_order,
    )
    z, y, x = source.shape
    result = np.empty((3, 5, z, y // 2, x // 2), dtype=np.float64)
    amplitudes = tuple(float(v) for v in beams)
    for orientation in range(3):
        result[orientation] = forward(
            source,
            kernel_cache=cache,
            carrier_yx_per_um=carriers[orientation],
            phases_rad=phases[orientation],
            beam_amplitudes=amplitudes,
            excitation_um=0.488,
        )
    return result


def _sum_units(values: NDArray[np.float64]) -> int:
    """Sum binary64 values exactly in units of 2**-1074 using exponent bins.

    Split each 53-bit significand into 26/27-bit integers. Each bin's
    partial sum over at most 65536 values fits exactly in binary64, so
    bincount is exact even under cancellation. Only the populated bins
    enter Python integer arithmetic; there is no per-element Python loop.
    """
    bits = values.view(np.uint64)
    exponents = ((bits >> 52) & 2047).astype(np.intp)
    significands = (bits & ((1 << 52) - 1)) | np.where(exponents != 0, np.uint64(1 << 52), 0)
    signs = np.where(bits >> 63, -1.0, 1.0)
    low = np.bincount(exponents, weights=(significands & ((1 << 26) - 1)) * signs)
    high = np.bincount(exponents, weights=(significands >> 26) * signs)
    occupied = np.flatnonzero((low != 0) | (high != 0))
    return sum(((int(high[e]) << 26) + int(low[e])) << max(int(e) - 1, 0) for e in occupied)


def _norm_part(values: NDArray[np.float64], extra_exponent: int = 0) -> Scaled:
    maximum = float(np.max(np.abs(values)))
    if maximum == 0:
        return 0.0, 0
    # Underflow of negligible squared contributions cannot affect this norm.
    with np.errstate(under="ignore"):
        scaled = values / maximum
        squares = float(np.dot(scaled, scaled))
    mantissa, exponent = math.frexp(maximum)
    mantissa, adjustment = math.frexp(mantissa * math.sqrt(squares))
    return mantissa, exponent + adjustment + extra_exponent


def _norm(parts: list[Scaled]) -> Scaled:
    exponent = max((e for m, e in parts if m), default=0)
    squares = math.fsum(math.ldexp(m, e - exponent) ** 2 for m, e in parts if m)
    mantissa, adjustment = math.frexp(math.sqrt(squares))
    return mantissa, exponent + adjustment


def _float(mantissa: float, exponent: int) -> float | None:
    try:
        return math.ldexp(mantissa, exponent)
    except OverflowError:
        return None


def compare_arrays(estimated: Array, reference: Array) -> MetricSummary:
    """Reduce exact-width finite arrays without scaling or registering inputs."""
    estimate = _array(estimated, "estimated", (4, 8))
    truth = _array(reference, "reference", (4, 8))
    if estimate.shape != truth.shape:
        _invalid("estimated / reference shape")
    count = int(truth.size)
    reference_parts: list[Scaled] = []
    error_parts: list[Scaled] = []
    maximum: Scaled = (0.0, 0)
    signed_units = 0
    # Buffered C-order traversal bounds workspace and supports scalar/strided
    # inputs without making full-volume copies or changing caller flags.
    with np.nditer(
        [estimate, truth],
        flags=["external_loop", "buffered"],
        op_flags=[["readonly"], ["readonly"]],
        op_dtypes=[np.float64, np.float64],
        order="C",
        buffersize=_BLOCK,
    ) as blocks:
        for e, r in blocks:
            reference_parts.append(_norm_part(r))
            signed_units += _sum_units(e) - _sum_units(r)
            with np.errstate(over="ignore", under="ignore"):
                difference = e - r
                extra = 0
                if not np.all(np.isfinite(difference)):
                    # Overflowing differences require one extra exponent bit.
                    # Smaller underflowed terms cannot affect norm/max here;
                    # the signed mean uses the exact original operands above.
                    difference = e * 0.5 - r * 0.5
                    extra = 1
            error_parts.append(_norm_part(difference, extra))
            magnitude, exponent = math.frexp(float(np.max(np.abs(difference))))
            candidate = (magnitude, exponent + extra)
            if magnitude and (not maximum[0] or candidate[::-1] > maximum[::-1]):
                maximum = candidate

    rm, re = _norm(reference_parts)
    em, ee = _norm(error_parts)
    try:
        mean = float(Fraction(signed_units, count << 1074))
    except OverflowError:
        mean = None
    metrics = {
        "reference_l2": _float(rm, re),
        "error_l2": _float(em, ee),
        "relative_l2": _float(em / rm, ee - re) if rm else None,
        "error_rms": _float(em / math.sqrt(count), ee),
        "error_max_abs": _float(*maximum),
        "error_mean": mean,
    }
    unavailable = tuple(
        UnavailableMetric(
            field,
            "zero_reference" if field == "relative_l2" and not rm else "unrepresentable",
        )
        for field, value in metrics.items()
        if value is None
    )
    return MetricSummary(count=count, **metrics, unavailable_fields=unavailable)
