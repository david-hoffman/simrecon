"""Fit volume phases after removing structurally invisible real Fourier modes."""

from dataclasses import dataclass
from typing import cast

import numpy as np
import numpy.typing as npt

from ._volume_order_otf import VolumeOrderOtf
from ._volume_phase_estimation import (
    Complex,
    Real,
    VolumePhaseEstimate,
    _estimate,
    _finite,
    _transform,
)


@dataclass(frozen=True)
class ObservableVolumePhaseEstimate(VolumePhaseEstimate):
    """Local phase fit and its structurally observable real nuisance domain.

    Attributes
    ----------
    observable_fourier_mask : numpy.ndarray
        Owned mutable native Boolean array in centered z/y/x frequency storage.
    observable_dimension, unobservable_dimension : int
        Retained and excluded real Fourier dimensions. The inherited specimen
        is the full-grid minimum-norm observable representative, not hidden
        physical specimen truth. All other fields inherit VolumePhaseEstimate.
    """

    observable_fourier_mask: npt.NDArray[np.bool_]
    observable_dimension: int
    unobservable_dimension: int


def _observable_subspace(
    signed: list[Complex], carrier: tuple[int, int], shape: tuple[int, int, int]
) -> tuple[npt.NDArray[np.bool_], Real]:
    """Build exact component support and a real orthonormal Fourier-orbit basis."""
    nz, ny, nx = shape
    cy, cx = carrier
    visible = np.zeros(shape, dtype=np.bool_)
    for m, row in zip(range(-2, 3), signed, strict=True):
        components = (row.real != 0) | (row.imag != 0)
        visible |= np.roll(components, (-m * (cy % ny), -m * (cx % nx)), axis=(1, 2))
    negative = np.ix_(*[(-np.arange(k)) % k for k in shape])
    hermitian = visible | visible[negative]
    dimension = int(np.count_nonzero(hermitian))
    size = nz * ny * nx
    # A self-conjugate orbit supplies one real column. A pair supplies two:
    # conjugate-symmetric Fourier coefficients for cosine and sine. The unitary
    # forward transform of these coefficients is real and orthonormal too;
    # using it rather than the inverse merely changes a sine column's sign.
    coefficients = np.zeros((*shape, dimension), dtype=np.complex128)
    seen = np.zeros(shape, dtype=np.bool_)
    column = 0
    for raw in np.argwhere(hermitian):
        j = tuple(int(v) for v in raw)
        if seen[j]:
            continue
        opposite = tuple((-v) % k for v, k in zip(j, shape, strict=True))
        seen[j] = seen[opposite] = True
        if j == opposite:
            coefficients[(*j, column)] = 1
            column += 1
        else:
            amplitude = 1 / np.sqrt(2.0)
            coefficients[(*j, column)] = coefficients[(*opposite, column)] = amplitude
            coefficients[(*j, column + 1)] = 1j * amplitude
            coefficients[(*opposite, column + 1)] = -1j * amplitude
            column += 2
    q = (
        _transform(coefficients, (0, 1, 2)).real.reshape(size, dimension).copy()
        if dimension
        else np.empty((size, 0), dtype=np.float64)
    )
    _finite(q)
    return np.fft.fftshift(hermitian), q


def estimate_observable_volume_phases(
    images: npt.NDArray[np.generic],
    *,
    order_otf: VolumeOrderOtf,
    carrier_bins_yx: tuple[int, int],
    initial_phases_rad: npt.NDArray[np.generic],
    max_nfev: int,
    gradient_tolerance: float,
    step_tolerance: float,
    source: str,
) -> ObservableVolumePhaseEstimate:
    """Fit all phases in a fixed calibration gauge on observable real modes.

    Parameters
    ----------
    images : numpy.ndarray
        Finite real observations, axes phase/z/y/x with at least five exposures.
    order_otf : VolumeOrderOtf
        Full complex positive-order transfers in the supplied fixed gauge.
    carrier_bins_yx : tuple of int
        Exact integer lateral carrier; only indexing is reduced periodically.
    initial_phases_rad : numpy.ndarray
        One finite real initial angle per exposure, in radians.
    max_nfev : int
        Positive residual evaluation limit for the single local TRF solve.
    gradient_tolerance, step_tolerance : float
        Binary64 tolerances strictly between machine epsilon and one.
    source : str
        Nonblank opaque caller label retained unchanged.

    Returns
    -------
    ObservableVolumePhaseEstimate
        Owned fit arrays and diagnostics. Zero structural dimension and initial
        numerical rank deficiency are unavailable outcomes without optimization.

    Raises
    ------
    SimreconError
        For inherited input, transform, numerical solver or derived range errors.
        Unrelated errors, warnings and allocation failures retain their behavior.

    Notes
    -----
    Structural visibility uses exact normalized signed transfer components and
    all-axis modular Hermitian closure. Retained weak modes still undergo the
    numerical SVD cutoff. The full real/imaginary objective and all phase
    coordinates remain in the supplied calibration gauge. The specimen is a
    minimum-norm observable representative; stationarity supplies no global
    uniqueness, physical accuracy or scalable-volume guarantee.
    """
    with np.errstate(all="ignore"):
        return cast(
            ObservableVolumePhaseEstimate,
            _estimate(
                images,
                order_otf,
                carrier_bins_yx,
                initial_phases_rad,
                max_nfev,
                gradient_tolerance,
                step_tolerance,
                source,
                observable=True,
            ),
        )
