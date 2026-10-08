"""Fit illumination phase and contrast on a supplied integer carrier overlap."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._otf import Otf2D, _pair
from ._phase import separate_phases
from ._reconstruction import _calibration


@dataclass(frozen=True)
class IlluminationEstimate:
    """Common phase offset and unconstrained modulation of one orientation.

    Attributes
    ----------
    phase_offset_rad : float
        Principal phase of the fitted complex gain, in radians.
    modulation : float
        Twice the gain magnitude, without clipping to the physical interval.
    relative_residual : float
        Relative complex regression residual; not a confidence probability.
    phases_rad : numpy.ndarray
        Owned mutable native float64 principal corrected phases, shape (N,).
    overlap_count : int
        Geometric closed-grid pair count, including zero-transfer pairs.
    source : str
        Supplied OTF label retained unchanged, without authentication.
    """

    phase_offset_rad: float
    modulation: float
    relative_residual: float
    phases_rad: npt.NDArray[np.float64]
    overlap_count: int
    source: str


def _carrier(value: object) -> tuple[int, int]:
    """Retain arbitrary-size signed integer shifts without rounding or wrapping."""
    code = "invalid_illumination_carrier"
    coordinates = []
    for coordinate in _pair(value, code):
        if isinstance(coordinate, (bool, np.bool_)) or not isinstance(
            coordinate, (int, np.integer)
        ):
            raise SimreconError(code, "carrier must contain nonboolean integers")
        coordinates.append(int(coordinate))
    return coordinates[0], coordinates[1]


def _validated_otf(otf: Otf2D, shape: tuple[int, int]) -> Otf2D:
    """Use the shared supplied-record rules with this consumer's error names."""
    try:
        return _calibration(otf, shape)
    except SimreconError as error:
        if error.code == "incompatible_reconstruction_otf_grid":
            raise SimreconError(
                "incompatible_illumination_otf_grid", "OTF frequencies must match the detector"
            ) from None
        if error.code == "invalid_reconstruction_otf":
            raise SimreconError("invalid_illumination_otf", error.message) from None
        raise


def _scale_complex(values: npt.NDArray[np.complex128], exponent: Any) -> npt.NDArray[np.complex128]:
    """Scale coordinates by powers of two without a complex magnitude/product."""
    result = np.empty(values.shape, dtype=np.complex128)
    result.real = np.ldexp(values.real, exponent)
    result.imag = np.ldexp(values.imag, exponent)
    return result


def _transform(plane: npt.NDArray[Any]) -> tuple[npt.NDArray[np.complex128], int]:
    """Transform bounded spatial coordinates and retain their binary scale."""
    values = np.asarray(plane, dtype=np.complex128)
    peak = np.max(np.maximum(np.abs(values.real), np.abs(values.imag)))
    _, exponent = np.frexp(peak)
    scaled = _scale_complex(values, -int(exponent))
    try:
        result = np.fft.fftshift(np.fft.fft2(scaled, norm="forward"))
    except SimreconError:
        raise
    except (ValueError, FloatingPointError, OverflowError) as error:
        raise SimreconError("illumination_solver_failure", "numerical transform failed") from error
    if not np.isfinite(result).all():
        raise SimreconError("illumination_solver_failure", "transform returned nonfinite values")
    return result, int(exponent)


def _unit_product(
    transfer: npt.NDArray[np.complex128], data: npt.NDArray[np.complex128], data_exponent: int
) -> tuple[npt.NDArray[np.complex128], float, int]:
    """Normalize a cross-weighted band while retaining an unmaterialized norm."""
    _, te = np.frexp(np.maximum(np.abs(transfer.real), np.abs(transfer.imag)))
    _, de = np.frexp(np.maximum(np.abs(data.real), np.abs(data.imag)))
    product = _scale_complex(transfer, -te) * _scale_complex(data, -de)
    nonzero = product != 0
    if not np.any(nonzero):
        raise SimreconError("unidentifiable_illumination", "overlap band has zero information")
    # A zero factor must not set the scale of arbitrarily weak nonzero terms.
    exponent = int(np.max((te + de)[nonzero]))
    scaled = _scale_complex(product, te + de - exponent)
    norm = float(np.sqrt(np.sum(scaled.real**2 + scaled.imag**2)))
    mantissa, norm_exponent = np.frexp(norm)
    return scaled / norm, float(mantissa), exponent + int(norm_exponent) + data_exponent


def estimate_illumination(
    images: npt.NDArray[Any],
    *,
    otf: Otf2D,
    phase_steps_rad: npt.NDArray[Any],
    carrier_bins_yx: object,
) -> IlluminationEstimate:
    """Estimate common phase and modulation from full complex OTF overlap.

    Parameters
    ----------
    images : numpy.ndarray
        Plain real array (N, Ny, Nx), N >= 3, in acquisition intensity units.
        Representation, rank and separation errors follow separate_phases.
    otf : Otf2D
        Shared full signed complex transfer on the matching detector grid.
    phase_steps_rad : numpy.ndarray
        Required relative phases (N,), in radians, evaluated directly as stored.
    carrier_bins_yx : tuple, list or numpy.ndarray
        Required signed integer frequency-bin shift (ky, kx). No wrapping,
        fractional interpolation, carrier search or support threshold is used.

    Returns
    -------
    IlluminationEstimate
        Principal common phase, unconstrained modulation, direct relative fit
        residual and principal-equivalent corrected phases for one orientation.

    Raises
    ------
    SimreconError
        For inherited separation errors, invalid carrier or OTF, no overlap,
        computed zero information, numerical transform failure or nonfinite
        final outputs. Allocation and unrelated exceptions propagate.

    Notes
    -----
    The negative forward DFT and positive carrier use x=H(q+k)*D0(q),
    y=H(q)*Dplus(q+k). Unweighted complex least squares fits y=z*x, returning
    arg(z) and 2*abs(z). Independent binary scales protect transforms, products,
    norms and final modulation restoration. The residual is computed directly.
    Weak information can amplify noise; no confidence or unique recovery promise
    follows. Modulation above one is returned but cannot feed reconstruct.
    Carrier and brightness remain explicit. Inputs and NumPy error mode survive.
    """
    # Keep the inherited output-range decision as well as its rank/solver rules.
    components = separate_phases(images, phases_rad=phase_steps_rad)
    with np.errstate(all="ignore"):
        # The original-scale call above remains the validation/rank/solver/range
        # authority. Its rounded subnormal outputs must not quantize the
        # dimensionless fit. An exact common binary scaling of the converted
        # observations retains their stored ratios before coefficient rounding;
        # its scale cancels from gain and residual, so never restore it here.
        values = images.astype(np.float64, order="C", copy=True)
        peak = np.max(np.abs(values))
        if 0 < peak < np.finfo(np.float64).tiny:
            _, exponent = np.frexp(peak)
            components = separate_phases(
                np.ldexp(values, -int(exponent)), phases_rad=phase_steps_rad
            )
        shape = components.dc.shape
        calibration = _validated_otf(otf, shape)
        ky, kx = _carrier(carrier_bins_yx)
        ny, nx = shape
        if abs(ky) >= ny or abs(kx) >= nx:
            raise SimreconError("no_illumination_overlap", "carrier has no closed-grid overlap")
        q = (slice(max(0, -ky), min(ny, ny - ky)), slice(max(0, -kx), min(nx, nx - kx)))
        shifted = (
            slice(max(0, ky), min(ny, ny + ky)),
            slice(max(0, kx), min(nx, nx + kx)),
        )
        d0, e0 = _transform(components.dc)
        dp, ep = _transform(components.c1)
        u, xm, xe = _unit_product(calibration.values[shifted], d0[q], e0)
        v, ym, ye = _unit_product(calibration.values[q], dp[shifted], ep)
        correlation = np.sum(np.conjugate(u) * v)
        magnitude = float(abs(correlation))
        if magnitude == 0:
            raise SimreconError("unidentifiable_illumination", "fitted cross product is zero")
        cm, ce = np.frexp(magnitude)
        # Restore only the final modulation, not the norm ratio or complex gain.
        modulation = float(np.ldexp(2 * (ym / xm) * cm, ye - xe + int(ce)))
        theta = float(np.arctan2(correlation.imag, correlation.real))
        difference = v - correlation * u
        residual = float(np.sqrt(np.sum(difference.real**2 + difference.imag**2)))
        angles = phase_steps_rad.astype(np.float64, order="C", copy=True)
        c, s = np.cos(angles), np.sin(angles)
        ct, st = np.cos(theta), np.sin(theta)
        phases = np.array(np.arctan2(s * ct + c * st, c * ct - s * st), order="C", copy=True)
        if not (np.isfinite([modulation, theta, residual]).all() and np.isfinite(phases).all()):
            raise SimreconError(
                "unrepresentable_illumination", "final fitted outputs are nonfinite"
            )
    return IlluminationEstimate(
        theta, modulation, residual, phases, (ny - abs(ky)) * (nx - abs(kx)), calibration.source
    )
