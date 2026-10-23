"""Construct total-normalized finite midpoint spheres with exact membership."""

from collections.abc import Iterator
from fractions import Fraction
from math import isfinite, isqrt, lcm, prod

import numpy as np
from numpy.typing import NDArray

from simrecon import SimreconError

type Int3 = tuple[int, int, int]
type Rational3 = tuple[Fraction, Fraction, Fraction]

_INVALID = "invalid_simulation_source"
_RANGE = "simulation_source_range"


def _counts(value: object, name: str) -> Int3:
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or not all(type(item) is int and item > 0 for item in value)
    ):
        raise SimreconError(_INVALID, f"{name} must be three positive plain integers")
    return value[0], value[1], value[2]


def _spacing(value: object) -> Rational3:
    if (
        not isinstance(value, tuple)
        or len(value) != 3
        or not all(type(item) in (int, float) for item in value)
    ):
        raise SimreconError(_INVALID, "detector spacing must be three plain real numbers")
    try:
        normalized = tuple(float(item) for item in value)
    except OverflowError as error:
        raise SimreconError(_INVALID, "detector spacing cannot normalize to float64") from error
    if not all(isfinite(item) and item > 0 for item in normalized):
        raise SimreconError(_INVALID, "detector spacing must normalize to finite positive values")
    return Fraction(normalized[0]), Fraction(normalized[1]), Fraction(normalized[2])


def _catalogue(value: object) -> NDArray[np.float64]:
    if (
        type(value) is not np.ndarray
        or value.ndim != 2
        or value.shape[1] != 5
        or value.dtype.kind not in "iuf"
    ):
        raise SimreconError(_INVALID, "catalogue must be a plain real ndarray with shape (M,5)")
    # Real i/u/f conversion preserves every original NaN/infinity as nonfinite.
    # Thus this one finite check rejects both original and cast-created infinity.
    # A private copy also handles read-only, strided and nonnative-endian inputs.
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        normalized = np.array(value, dtype=np.float64, copy=True)
    if not np.isfinite(normalized).all():
        raise SimreconError(
            _INVALID, "catalogue values must be finite before and after normalization"
        )
    return normalized


def _integer_geometry(
    center: Rational3, radius: Fraction, half_steps: Rational3
) -> tuple[int, Int3, Int3]:
    # At index j, displacement is (2*j+1)*half_step-center. Clear
    # denominators once per sphere so all subsequent squared tests are integers.
    values = (*center, radius, *half_steps)
    scale = lcm(*(value.denominator for value in values))
    cz, cy, cx, a, hz, hy, hx = (value.numerator * (scale // value.denominator) for value in values)
    return a, (hz - cz, hy - cy, hx - cx), (2 * hz, 2 * hy, 2 * hx)


def _spans(radius: int, offsets: Int3, strides: Int3) -> Iterator[tuple[int, int, int, int]]:
    """Yield exact occupied x intervals, with exclusive stops, for each z/y row."""
    oz, oy, ox = offsets
    sz, sy, sx = strides
    # ceil((-r-o)/s) = -floor((r+o)/s). Containment already puts these
    # bounds inside the array: the bounding sphere never needs clipping.
    for z in range(-((radius + oz) // sz), (radius - oz) // sz + 1):
        yz_squared = radius * radius - (oz + z * sz) ** 2
        y_radius = isqrt(yz_squared)
        for y in range(-((y_radius + oy) // sy), (y_radius - oy) // sy + 1):
            x_radius = isqrt(yz_squared - (oy + y * sy) ** 2)
            start = -((x_radius + ox) // sx)
            stop = (x_radius - ox) // sx + 1
            if start < stop:
                yield z, y, start, stop


def make_sources(
    catalogue: object,
    *,
    detector_shape_zyx: object,
    detector_spacing_um_zyx: object,
    source_refinement_zyx: object,
) -> NDArray[np.float64]:
    """Build the finite, total-normalized midpoint source model.

    Parameters
    ----------
    catalogue : numpy.ndarray
        Plain real array with columns center z/y/x, positive radius (all in
        micrometres), and nonnegative integrated brightness in electrons.
    detector_shape_zyx : tuple of int
        Three positive plain integer detector dimensions.
    detector_spacing_um_zyx : tuple of int or float
        Three finite positive spacings in micrometres after float64 conversion.
    source_refinement_zyx : tuple of int
        Three positive plain integer source refinements.

    Returns
    -------
    numpy.ndarray
        Independently owned, writable, C-contiguous native float64 source
        weights, shaped as detector dimensions times source refinements.

    Raises
    ------
    SimreconError
        For invalid input, impossible ndarray representation, positive objects
        without sites, weights rounding to zero, or nonfinite overlap sums.
    MemoryError
        If actual allocation fails; unrelated dependency failures also propagate.

    Notes
    -----
    Membership uses exact normalized-input geometry at half-cell sites and
    includes ties. Each object contributes RN64(B/K); additions round separately
    in catalogue order. Stored mass need not equal the exact input brightness.
    This is not continuous sphere-cell integration. Two interval traversals per
    positive sphere count sites and then update them without a volume mask.
    """
    shape = _counts(detector_shape_zyx, "detector_shape_zyx")
    refinement = _counts(source_refinement_zyx, "source_refinement_zyx")
    spacing = _spacing(detector_spacing_um_zyx)
    rows = _catalogue(catalogue)
    source_shape = tuple(n * f for n, f in zip(shape, refinement, strict=True))
    # The byte count also bounds every positive dimension. Check exact Python
    # integers before NumPy attempts an allocation; real MemoryError is distinct.
    if prod(source_shape) * np.dtype(np.float64).itemsize > np.iinfo(np.intp).max:
        raise SimreconError(_RANGE, "source ndarray storage exceeds platform addressing")
    result = np.zeros(source_shape, dtype=np.float64)
    extents = tuple(n * d for n, d in zip(shape, spacing, strict=True))
    half_steps: Rational3 = (
        spacing[0] / (2 * refinement[0]),
        spacing[1] / (2 * refinement[1]),
        spacing[2] / (2 * refinement[2]),
    )
    for row in rows:
        center: Rational3 = (
            Fraction(float(row[0])),
            Fraction(float(row[1])),
            Fraction(float(row[2])),
        )
        radius = Fraction(float(row[3]))
        brightness = float(row[4])
        if radius <= 0 or brightness < 0:
            raise SimreconError(
                _INVALID, "sphere radius must be positive and brightness nonnegative"
            )
        if any(
            c < radius or c + radius > length for c, length in zip(center, extents, strict=True)
        ):
            raise SimreconError(_INVALID, "sphere must be wholly contained in the detector box")
        if brightness == 0:
            continue
        geometry = _integer_geometry(center, radius, half_steps)
        count = sum(stop - start for _, _, start, stop in _spans(*geometry))
        if count == 0:
            raise SimreconError(_RANGE, "positive sphere has no occupied source site")
        # Fraction conversion rounds the rational quotient once to nearest/even,
        # including subnormal results, without NumPy arithmetic-policy effects.
        weight = float(Fraction(brightness) / count)
        if weight == 0:
            raise SimreconError(_RANGE, "positive source weight rounds to zero")
        for z, y, start, stop in _spans(*geometry):
            target = result[z, y, start:stop]
            with np.errstate(over="ignore"):
                np.add(target, weight, out=target)
            if not np.isfinite(target).all():
                raise SimreconError(_RANGE, "source overlap addition is nonfinite")
    return result
