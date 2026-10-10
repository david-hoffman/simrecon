"""Prepare full signed transfer functions from sampled intensity kernels."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class Otf2D:
    """Sampled transfer with frozen bindings and independently mutable arrays.

    Attributes
    ----------
    values : numpy.ndarray
        Native C-contiguous complex128 transfer in full fftshift order.
    fy_per_um, fx_per_um : numpy.ndarray
        Native C-contiguous float64 frequencies in cycles per micrometre.
    pixel_size_um : tuple of float
        Converted spatial sample sizes (dy, dx), in micrometres.
    origin_yx : tuple of int
        Explicit spatial zero-displacement sample (oy, ox).
    source : str
        Caller label retained verbatim; not verified provenance.

    Notes
    -----
    Direct construction performs no validation. Frozen bindings do not freeze
    the contents of the arrays.
    """

    values: npt.NDArray[np.complex128]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    pixel_size_um: tuple[float, float]
    origin_yx: tuple[int, int]
    source: str


def _pair(value: object, code: str) -> tuple[object, object]:
    """Extract a pair from a permitted plain container without changing it."""
    if type(value) is np.ndarray:
        if value.ndim != 1:
            raise SimreconError(code, "pair array must be one-dimensional")
        items = value
    elif isinstance(value, (tuple, list)):
        items = value
    else:
        raise SimreconError(code, "pair must be a tuple, list or plain ndarray")
    if len(items) != 2:
        raise SimreconError(code, "pair must contain exactly two coordinates")
    return items[0], items[1]


def _spacing(value: object) -> float:
    """Convert a real nonboolean scalar to finite positive binary64 spacing."""
    code = "invalid_otf_pixel_size"
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "pixel size must be a real nonboolean scalar")
    try:
        converted = float(value)
    except OverflowError as error:
        raise SimreconError(code, "pixel size overflows float64") from error
    if not np.isfinite(converted) or converted <= 0:
        raise SimreconError(code, "converted pixel size must be finite and positive")
    return converted


def _origin(value: object, length: int) -> int:
    """Validate a nonboolean integer sample coordinate without rounding."""
    code = "invalid_otf_origin"
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise SimreconError(code, "origin must be a nonboolean integer scalar")
    converted = int(value)
    if not 0 <= converted < length:
        raise SimreconError(code, "origin must lie within the supplied spatial axis")
    return converted


def _frequencies(length: int, spacing: float) -> npt.NDArray[np.float64]:
    """Build ordered signed cycles/um without overflowing the axis extent."""
    modes = np.arange(-(length // 2), (length + 1) // 2, dtype=np.float64)
    frequencies = (modes / length) / spacing
    if (
        not np.isfinite(frequencies).all()
        or np.any((modes != 0) & (frequencies == 0))
        or not np.all(frequencies[1:] > frequencies[:-1])
    ):
        raise SimreconError(
            "unrepresentable_otf_frequencies", "final frequencies must be finite and distinct"
        )
    return frequencies


def _transform(
    working_psf: npt.NDArray[np.float64], origin_yx: tuple[int, int]
) -> npt.NDArray[np.complex128]:
    """Transform normalized mass after rolling the declared origin to zero."""
    rolled = np.roll(working_psf, (-origin_yx[0], -origin_yx[1]), axis=(0, 1))
    return np.fft.fftshift(np.fft.fft2(rolled))


def _check_finite_psf(samples: npt.NDArray[Any]) -> None:
    """Require finite samples in either the source or converted representation."""
    if not np.isfinite(samples).all():
        raise SimreconError("nonfinite_psf", "psf samples must be finite")


def prepare_otf(
    psf: npt.NDArray[Any],
    *,
    pixel_size_um: object,
    origin_yx: object,
    source: str,
) -> Otf2D:
    """Normalize a sampled nonnegative intensity PSF and prepare its full OTF.

    Parameters
    ----------
    psf : numpy.ndarray
        Plain real integer or floating array of shape (Ny, Nx), both positive.
        Source samples must be finite and nonnegative. An independent float64
        copy defines the numerical problem after conversion rounding/underflow.
    pixel_size_um : tuple, list or numpy.ndarray
        Required pair of finite positive real nonboolean spacings (dy, dx),
        converted to float64, in micrometres.
    origin_yx : tuple, list or numpy.ndarray
        Required pair of in-bounds nonboolean integer coordinates (oy, ox).
    source : str
        Required nonblank caller label, retained without file access or checks.

    Returns
    -------
    Otf2D
        Full negative-sign discrete Fourier transfer normalized to unit mass,
        with signed real and imaginary values and centered physical frequencies.
        Each array owns separate mutable storage; inputs remain unchanged.

    Raises
    ------
    SimreconError
        If input validation fails, converted mass is zero, final frequencies
        cannot be represented, or the transform has a numerical failure or
        nonfinite output. Allocation and unrelated programming errors propagate.

    Notes
    -----
    Normalization discards absolute throughput. The supplied grid is periodic;
    no background correction, origin inference, support clipping, interpolation
    or continuous optical model is applied. Increasing rows mean positive y.
    Scoped arithmetic preserves the caller's NumPy floating-error policy.
    """
    if type(psf) is not np.ndarray:
        raise SimreconError("invalid_psf", "psf must be a plain NumPy ndarray")
    if psf.dtype.kind not in "iuf":
        raise SimreconError("invalid_psf_dtype", "psf must have real integer or floating dtype")
    if psf.ndim != 2 or 0 in psf.shape:
        raise SimreconError("invalid_psf_shape", "psf must have two positive spatial dimensions")
    if not isinstance(source, str) or not source.strip():
        raise SimreconError("invalid_otf_source", "source must be a nonblank string")

    # Conversion loss and final frequency overflow have specified outcomes,
    # independent of the caller's warning modes and arithmetic callback.
    with np.errstate(all="ignore"):
        _check_finite_psf(psf)
        if np.any(psf < 0):
            raise SimreconError("negative_psf", "source samples must be nonnegative")
        working = psf.astype(np.float64, order="C", copy=True)
        _check_finite_psf(working)
        maximum = working.max()
        if maximum == 0:
            raise SimreconError("zero_psf_mass", "converted psf must have positive mass")

        dy, dx = (_spacing(v) for v in _pair(pixel_size_um, "invalid_otf_pixel_size"))
        oy, ox = _pair(origin_yx, "invalid_otf_origin")
        origin = (_origin(oy, psf.shape[0]), _origin(ox, psf.shape[1]))
        fy = _frequencies(psf.shape[0], dy)
        fx = _frequencies(psf.shape[1], dx)

        # Nonnegative scaling avoids raw-sum overflow, including all-max input,
        # and preserves normalization when every positive sample is subnormal.
        working /= maximum
        working /= working.sum()
        try:
            transformed = _transform(working, origin)
        except FloatingPointError as error:
            raise SimreconError("otf_transform_failure", "numerical transform failure") from error
        values = np.array(transformed, dtype=np.complex128, order="C", copy=True)
        if not np.isfinite(values).all():
            raise SimreconError("otf_transform_failure", "transform returned nonfinite values")
    return Otf2D(values, fy, fx, (dy, dx), origin, source)
