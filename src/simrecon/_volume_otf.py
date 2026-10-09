"""Prepare full complex transfer functions from sampled intensity volumes."""

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class Otf3D:
    """Volume transfer with frozen bindings and independently mutable arrays.

    Attributes
    ----------
    values : numpy.ndarray
        Native C-contiguous complex128 transfer in full centered z/y/x order.
    fz_per_um, fy_per_um, fx_per_um : numpy.ndarray
        Separately owned native float64 frequency axes, in cycles/micrometre.
    voxel_size_um : tuple of float
        Converted spatial sample sizes (dz, dy, dx), in micrometres.
    origin_zyx : tuple of int
        Explicit zero-displacement sample (oz, oy, ox).
    source : str
        Unchanged caller label; no provenance verification is performed.

    Notes
    -----
    Direct construction performs no validation. Array contents remain writable.
    """

    values: npt.NDArray[np.complex128]
    fz_per_um: npt.NDArray[np.float64]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    voxel_size_um: tuple[float, float, float]
    origin_zyx: tuple[int, int, int]
    source: str


def _triple(value: object, code: str) -> tuple[object, object, object]:
    """Extract three coordinates from an explicitly permitted container."""
    if type(value) is np.ndarray:
        if value.ndim != 1:
            raise SimreconError(code, "coordinate array must be one-dimensional")
        items = value
    elif isinstance(value, (tuple, list)):
        items = value
    else:
        raise SimreconError(code, "coordinates must be a tuple, list or plain ndarray")
    if len(items) != 3:
        raise SimreconError(code, "exactly three coordinates are required")
    return items[0], items[1], items[2]


def _spacing(value: object) -> float:
    """Convert an allowed real scalar to a finite positive float64 spacing."""
    code = "invalid_otf_voxel_size"
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "voxel size must be a real nonboolean scalar")
    try:
        converted = float(value)
    except OverflowError as error:
        raise SimreconError(code, "voxel size overflows float64") from error
    if not np.isfinite(converted) or converted <= 0:
        raise SimreconError(code, "converted voxel size must be finite and positive")
    return converted


def _origin(value: object, length: int) -> int:
    """Validate an integer origin without rounding or periodic wrapping."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise SimreconError("invalid_otf_origin", "origin must be a nonboolean integer")
    converted = int(value)
    if not 0 <= converted < length:
        raise SimreconError("invalid_otf_origin", "origin must lie within its spatial axis")
    return converted


def _frequencies(length: int, spacing: float) -> npt.NDArray[np.float64]:
    """Calculate signed centered frequencies without forming an axis extent."""
    modes = np.arange(-(length // 2), (length + 1) // 2, dtype=np.float64)
    frequencies = (modes / length) / spacing
    if (
        not np.isfinite(frequencies).all()
        or np.any((modes != 0) & (frequencies == 0))
        or not np.all(frequencies[1:] > frequencies[:-1])
    ):
        raise SimreconError(
            "unrepresentable_otf_frequencies", "final frequencies must be finite and ordered"
        )
    return frequencies


def prepare_volume_otf(
    psf: npt.NDArray[Any],
    *,
    voxel_size_um: object,
    origin_zyx: object,
    source: str,
) -> Otf3D:
    """Prepare the normalized full complex OTF of a sampled intensity volume.

    Parameters
    ----------
    psf : numpy.ndarray
        Plain real integer or floating ndarray with positive z/y/x dimensions.
        Finite nonnegative source samples are copied to native float64. Their
        converted values define the stored problem and must have positive mass.
    voxel_size_um : tuple, list or numpy.ndarray
        Required three finite positive real nonboolean spacings (dz, dy, dx),
        individually converted to float64, in micrometres.
    origin_zyx : tuple, list or numpy.ndarray
        Required three in-bounds nonboolean integer coordinates (oz, oy, ox).
    source : str
        Required nonblank opaque label retained unchanged.

    Returns
    -------
    Otf3D
        Negative-sign forward discrete Fourier transform of unit sample mass,
        with every axis in centered frequency order. All four output arrays
        independently own mutable storage. Inputs remain unchanged.

    Raises
    ------
    SimreconError
        If validation fails, final frequency grids are unrepresentable, or
        numerical transformation fails or returns nonfinite values.
        Memory errors and unrelated transform exceptions propagate.

    Notes
    -----
    The supplied grid is finite and periodic. Absolute throughput is discarded.
    No optical calibration, background correction, resampling, origin inference
    or order-specific illumination transfer is supplied. Scoped arithmetic and
    warning handling preserve the caller's floating-error and warning policies.
    """
    if type(psf) is not np.ndarray:
        raise SimreconError("invalid_psf", "psf must be a plain NumPy ndarray")
    if psf.dtype.kind not in "iuf":
        raise SimreconError("invalid_psf_dtype", "psf must have real integer or floating dtype")
    if psf.ndim != 3 or 0 in psf.shape:
        raise SimreconError("invalid_psf_shape", "psf must have three positive dimensions")
    if not isinstance(source, str) or not source.strip():
        raise SimreconError("invalid_otf_source", "source must be a nonblank string")

    # Conversion loss, discarded tiny contributions and rejected final-grid
    # overflow have defined outcomes regardless of the caller's error handlers.
    with np.errstate(all="ignore"):
        if not np.isfinite(psf).all():
            raise SimreconError("nonfinite_psf", "source psf samples must be finite")
        if np.any(psf < 0):
            raise SimreconError("negative_psf", "source psf samples must be nonnegative")
        working = psf.astype(np.float64, order="C", copy=True)
        if not np.isfinite(working).all():
            raise SimreconError("nonfinite_psf", "converted psf samples must be finite")
        maximum = working.max()
        if maximum == 0:
            raise SimreconError("zero_psf_mass", "converted psf must have positive mass")

        dz, dy, dx = (_spacing(v) for v in _triple(voxel_size_um, "invalid_otf_voxel_size"))
        oz, oy, ox = _triple(origin_zyx, "invalid_otf_origin")
        origin = (_origin(oz, psf.shape[0]), _origin(oy, psf.shape[1]), _origin(ox, psf.shape[2]))
        fz = _frequencies(psf.shape[0], dz)
        fy = _frequencies(psf.shape[1], dy)
        fx = _frequencies(psf.shape[2], dx)

        # Maximum scaling avoids overflow in the raw sum and preserves mass
        # when every positive source sample is subnormal.
        working /= maximum
        working /= working.sum()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                rolled = np.roll(working, tuple(-o for o in origin), axis=(0, 1, 2))
                transformed = np.fft.fftshift(np.fft.fftn(rolled, axes=(0, 1, 2)))
        except (FloatingPointError, OverflowError, RuntimeWarning) as error:
            raise SimreconError("otf_transform_failure", "numerical transform failure") from error
        values = np.array(transformed, dtype=np.complex128, order="C", copy=True)
        if not np.isfinite(values).all():
            raise SimreconError("otf_transform_failure", "transform returned nonfinite values")
    return Otf3D(values, fz, fy, fx, (dz, dy, dx), origin, source)
