"""Recombine known first-harmonic bands on a doubled two-dimensional grid."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._otf import Otf2D
from ._phase import separate_phases


@dataclass(frozen=True)
class Reconstruction2D:
    """Signed complex reconstruction with independently owned mutable arrays.

    Attributes
    ----------
    image, spectrum : numpy.ndarray
        Native complex128 spatial samples and centered Fourier-series amplitudes.
    fy_per_um, fx_per_um : numpy.ndarray
        Native float64 centered frequencies in cycles per micrometre.
    pixel_size_um : tuple of float
        Output (dy, dx) spacings in micrometres, half the detector spacings.
    source : str
        Supplied calibration label, retained verbatim without authentication.
    """

    image: npt.NDArray[np.complex128]
    spectrum: npt.NDArray[np.complex128]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    pixel_size_um: tuple[float, float]
    source: str


def _real_array(value: Any, name: str, shape: tuple[int, ...]) -> npt.NDArray[np.float64]:
    """Validate and copy one acquisition parameter into its stored problem."""
    if type(value) is not np.ndarray:
        raise SimreconError(f"invalid_reconstruction_{name}", f"{name} must be a plain ndarray")
    dtype_code = "dtype" if name == "images" else f"{name}_dtype"
    shape_code = "shape" if name == "images" else f"{name}_shape"
    if value.dtype.kind not in "iuf":
        raise SimreconError(f"invalid_reconstruction_{dtype_code}", "real dtype required")
    if value.shape != shape:
        raise SimreconError(f"invalid_reconstruction_{shape_code}", "array shape mismatch")
    converted = value.astype(np.float64, order="C", copy=True)
    if not (np.isfinite(value).all() and np.isfinite(converted).all()):
        raise SimreconError(f"nonfinite_reconstruction_{name}", "finite source/conversion required")
    if name == "apodization" and np.any((value < 0) | (value > 1)):
        raise SimreconError("invalid_reconstruction_apodization_range", "source mask outside [0,1]")
    return converted


def _scalar(value: object, code: str, *, positive: bool) -> float:
    """Convert a nonboolean real scalar and check its finite range."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "nonboolean real scalar required")
    try:
        result = float(value)
    except OverflowError as error:
        raise SimreconError(code, "scalar conversion overflow") from error
    if not np.isfinite(result) or result < 0 or (positive and result == 0):
        raise SimreconError(code, "scalar outside finite permitted range")
    return result


def _pair(value: object) -> tuple[Any, Any]:
    """Validate a calibration pair without invoking array subclass behavior."""
    code = "invalid_reconstruction_otf"
    if type(value) is np.ndarray:
        if value.ndim != 1:
            raise SimreconError(code, "pair array must be one-dimensional")
    elif not isinstance(value, (tuple, list)):
        raise SimreconError(code, "pair must be tuple, list or plain ndarray")
    if len(value) != 2:  # type: ignore[arg-type]
        raise SimreconError(code, "pair must contain two coordinates")
    return value[0], value[1]  # type: ignore[index]


def _frequencies(length: int, spacing: float, code: str) -> npt.NDArray[np.float64]:
    """Form signed frequencies without first multiplying an axis extent."""
    modes = np.arange(-(length // 2), (length + 1) // 2, dtype=np.float64)
    values = (modes / length) / spacing
    if (
        not np.isfinite(values).all()
        or np.any((modes != 0) & (values == 0))
        or not np.all(np.diff(values) > 0)
    ):
        raise SimreconError(code, "frequency axis must be finite, distinct and noncollapsed")
    return values


def _calibration(otf: Otf2D, shape: tuple[int, int]) -> Otf2D:
    """Validate even directly constructed calibration records before consuming."""
    code = "invalid_reconstruction_otf"
    if not isinstance(otf, Otf2D):
        raise SimreconError(code, "Otf2D required")
    copies = []
    for value, expected, kind, width in (
        (otf.values, shape, "c", 16),
        (otf.fy_per_um, (shape[0],), "f", 8),
        (otf.fx_per_um, (shape[1],), "f", 8),
    ):
        if (
            type(value) is not np.ndarray
            or value.shape != expected
            or value.dtype.kind != kind
            or value.dtype.itemsize != width
            or not np.isfinite(value).all()
        ):
            raise SimreconError(code, "invalid calibration array representation")
        copies.append(
            np.array(
                value, dtype=np.complex128 if kind == "c" else np.float64, order="C", copy=True
            )
        )
    spacing = tuple(_scalar(v, code, positive=True) for v in _pair(otf.pixel_size_um))
    origin = _pair(otf.origin_yx)
    for coordinate, length in zip(origin, shape, strict=True):
        if (
            isinstance(coordinate, (bool, np.bool_))
            or not isinstance(coordinate, (int, np.integer))
            or not 0 <= coordinate < length
        ):
            raise SimreconError(code, "origin must be an in-bounds integer pair")
    if not isinstance(otf.source, str) or not otf.source.strip():
        raise SimreconError(code, "nonblank calibration source required")
    h, fy, fx = copies
    grid_code = "incompatible_reconstruction_otf_grid"
    for values, length, delta in zip((fy, fx), shape, spacing, strict=True):
        exact = _frequencies(length, delta, grid_code)
        tolerance = 8 * np.finfo(float).eps * np.abs(exact) + np.nextafter(0.0, 1.0)
        if (
            np.any(np.abs(values - exact) > tolerance)
            or not np.all(np.diff(values) > 0)
            or np.any((exact != 0) & (values == 0))
        ):
            raise SimreconError(grid_code, "calibration frequencies do not match detector")
    ny, nx = shape
    tau = 128 * ny * nx * np.finfo(float).eps + 4 * ny * nx * np.nextafter(0.0, 1.0)
    unshifted = np.fft.ifftshift(h)
    conjugate_partner = np.conjugate(
        unshifted[np.ix_((-np.arange(ny)) % ny, (-np.arange(nx)) % nx)]
    )
    if (
        abs(h[ny // 2, nx // 2] - 1) > tau
        or np.any(np.abs(h) > 1 + tau)
        or np.any(np.abs(unshifted - conjugate_partner) > 2 * tau)
    ):
        raise SimreconError(code, "transfer must be normalized, bounded and modular Hermitian")
    return Otf2D(h, fy, fx, (spacing[0], spacing[1]), (int(origin[0]), int(origin[1])), otf.source)


def _interpolate(
    plane: npt.NDArray[np.complex128], y: npt.NDArray[np.float64], x: npt.NDArray[np.float64]
) -> npt.NDArray[np.complex128]:
    """Interpolate closed signed axes; outside queries return exact zero."""
    ny, nx = plane.shape
    valid_y = (y >= -(ny // 2)) & (y <= (ny - 1) // 2)
    valid_x = (x >= -(nx // 2)) & (x <= (nx - 1) // 2)
    # Clip before integer conversion; invalid queries never contribute a stencil.
    yy = np.clip(y, -(ny // 2), (ny - 1) // 2)
    xx = np.clip(x, -(nx // 2), (nx - 1) // 2)
    lower_y, lower_x = np.floor(yy), np.floor(xx)
    iy, ix = lower_y.astype(np.intp) + ny // 2, lower_x.astype(np.intp) + nx // 2
    jy, jx = np.minimum(iy + 1, ny - 1), np.minimum(ix + 1, nx - 1)
    wy, wx = yy - lower_y, xx - lower_x
    result = (1 - wy[:, None]) * (
        (1 - wx) * plane[iy[:, None], ix] + wx * plane[iy[:, None], jx]
    ) + wy[:, None] * ((1 - wx) * plane[jy[:, None], ix] + wx * plane[jy[:, None], jx])
    return np.where(valid_y[:, None] & valid_x, result, 0)


def _scaled_complex(
    values: npt.NDArray[np.complex128], exponent: Any
) -> npt.NDArray[np.complex128]:
    """Apply a binary exponent to coordinates without complex-magnitude overflow."""
    result = np.empty(values.shape, dtype=np.complex128)
    result.real = np.ldexp(values.real, exponent)
    result.imag = np.ldexp(values.imag, exponent)
    return result


def _transform(plane: npt.NDArray[Any], *, inverse: bool = False) -> npt.NDArray[np.complex128]:
    """Execute only the numerical transform inside the specified failure boundary."""
    try:
        result = (
            np.fft.ifft2(np.fft.ifftshift(plane), norm="forward")
            if inverse
            else np.fft.fftshift(np.fft.fft2(plane, norm="forward"))
        )
    except (ValueError, FloatingPointError, OverflowError) as error:
        raise SimreconError(
            "reconstruction_solver_failure", "numerical transform failed"
        ) from error
    if not np.isfinite(result).all():
        raise SimreconError("reconstruction_solver_failure", "transform returned nonfinite values")
    return result


def _estimate(
    data: list[npt.NDArray[np.complex128]],
    transfers: list[npt.NDArray[np.complex128]],
    data_exponents: list[int],
    gain_mantissas: list[float],
    gain_exponents: list[int],
    ridge: float,
    mask: npt.NDArray[np.float64],
) -> npt.NDArray[np.complex128]:
    """Accumulate U and V with separate binary scales at every output mode."""
    d, h = np.stack(data), np.stack(transfers)
    _, de = np.frexp(np.maximum(np.abs(d.real), np.abs(d.imag)))
    _, he = np.frexp(np.maximum(np.abs(h.real), np.abs(h.imag)))
    ds, hs = _scaled_complex(d, -de), _scaled_complex(h, -he)
    hs *= np.array(gain_mantissas)[:, None, None]
    product = np.conjugate(hs) * ds
    ue = de + he + np.array(data_exponents)[:, None, None] + np.array(gain_exponents)[:, None, None]
    ve = 2 * (he + np.array(gain_exponents)[:, None, None])
    # Zero terms must not dominate the scale of extremely weak nonzero terms.
    ue = np.where(product != 0, ue, -10000)
    ve = np.where(h != 0, ve, -10000)
    umax = ue.max(axis=0)
    lm, le = np.frexp(ridge)
    vmax = np.maximum(ve.max(axis=0), le if ridge != 0 else -10000)
    u = _scaled_complex(product, ue - umax).sum(axis=0)
    v = np.ldexp(hs.real**2 + hs.imag**2, ve - vmax).sum(axis=0)
    v += np.ldexp(lm, le - vmax)
    estimate = np.zeros(mask.shape, dtype=np.complex128)
    np.divide(u.real, v, out=estimate.real, where=v > 0)
    np.divide(u.imag, v, out=estimate.imag, where=v > 0)
    mask_mantissa, mask_exponent = np.frexp(mask)
    estimate *= mask_mantissa
    return _scaled_complex(estimate, umax - vmax + mask_exponent)


def reconstruct(
    images: npt.NDArray[Any],
    *,
    otf: Otf2D,
    phases_rad: npt.NDArray[Any],
    wavevectors_per_um: npt.NDArray[Any],
    modulation: npt.NDArray[Any],
    brightness: npt.NDArray[Any],
    regularization: object,
    apodization: npt.NDArray[Any],
) -> Reconstruction2D:
    """Reconstruct explicit known-parameter first-harmonic 2D acquisitions.

    Parameters
    ----------
    images : numpy.ndarray
        Plain real array (R, N, Ny, Nx), R >= 1, N >= 3, positive spatial sizes.
    otf : Otf2D
        Full complex normalized transfer on the matching detector grid.
    phases_rad : numpy.ndarray
        Explicit known phases (R, N), in radians; passed to separate_phases.
    wavevectors_per_um : numpy.ndarray
        Signed (ky, kx) illumination vectors (R, 2), in cycles per micrometre.
    modulation, brightness : numpy.ndarray
        Explicit (R,) contrast in (0,1] and positive absolute acquisition gain.
    regularization : real scalar
        Nonnegative ridge penalty in squared effective-transfer units.
    apodization : numpy.ndarray
        Explicit output amplitude mask (2*Ny, 2*Nx), entries in [0,1].

    Returns
    -------
    Reconstruction2D
        Signed complex image and Fourier-series spectrum at half the input
        spacings and the same field of view. Index (0,0) is the spatial origin.

    Raises
    ------
    SimreconError
        For invalid inputs, unrepresentable grids/results or specified numerical
        execution failures. Existing phase errors propagate unchanged.

    Notes
    -----
    Fractional illumination shifts use closed-axis complex bilinear interpolation,
    an approximation rather than exact inversion of noncommensurate acquisition.
    Outside queries are zero, with no wrapping or partial stencil. Equal separated
    band weights, explicit ridge and amplitude mask define the estimator. There is
    no real forcing, clipping, inferred support, noise estimate or file access.
    Inputs and NumPy error policy are preserved. Allocation/unrelated errors
    propagate. See docs/contracts/known-parameter-reconstruction-v1.md for the
    informative coordinate accuracy envelope and finite periodic model limits.
    """
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_reconstruction_images", "plain ndarray required")
    if images.dtype.kind not in "iuf":
        raise SimreconError("invalid_reconstruction_dtype", "real acquisition dtype required")
    if images.ndim != 4 or images.shape[0] < 1 or images.shape[1] < 3 or 0 in images.shape[2:]:
        raise SimreconError("invalid_reconstruction_shape", "expected (R>=1,N>=3,Ny>=1,Nx>=1)")
    rcount, n, ny, nx = images.shape
    with np.errstate(all="ignore"):
        values = _real_array(images, "images", images.shape)
        phases = _real_array(phases_rad, "phases", (rcount, n))
        waves = _real_array(wavevectors_per_um, "wavevectors", (rcount, 2))
        contrast = _real_array(modulation, "modulation", (rcount,))
        gains = _real_array(brightness, "brightness", (rcount,))
        mask = _real_array(apodization, "apodization", (2 * ny, 2 * nx))
        for name, invalid in (
            ("modulation", (contrast <= 0) | (contrast > 1)),
            ("brightness", gains <= 0),
            ("apodization", (mask < 0) | (mask > 1)),
        ):
            if np.any(invalid):
                raise SimreconError(
                    f"invalid_reconstruction_{name}_range", "parameter out of range"
                )
        ridge = _scalar(regularization, "invalid_reconstruction_regularization", positive=False)
        calibration = _calibration(otf, (ny, nx))
        dy, dx = calibration.pixel_size_um
        grid_code = "unrepresentable_reconstruction_grid"
        output_spacing = (dy / 2, dx / 2)
        if 0 in output_spacing:
            raise SimreconError(grid_code, "halved spacing collapsed")
        fy = _frequencies(2 * ny, output_spacing[0], grid_code)
        fx = _frequencies(2 * nx, output_spacing[1], grid_code)
        y, x = np.arange(-ny, ny, dtype=float), np.arange(-nx, nx, dtype=float)
        wave_mantissa, wave_exponent = np.frexp(waves)
        spacing_mantissa, spacing_exponent = np.frexp([dy, dx])
        shifts = np.ldexp(
            wave_mantissa * np.array([ny, nx]) * spacing_mantissa, wave_exponent + spacing_exponent
        )
        data, transfers, data_exponents, gain_mantissas, gain_exponents = [], [], [], [], []
        for r in range(rcount):
            queries = [
                (y, x),
                (y + shifts[r, 0], x + shifts[r, 1]),
                (y - shifts[r, 0], x - shifts[r, 1]),
            ]
            for qy, qx in queries:
                if (
                    not np.isfinite(qy).all()
                    or not np.isfinite(qx).all()
                    or not np.all(np.diff(qy) > 0)
                    or not np.all(np.diff(qx) > 0)
                ):
                    raise SimreconError(grid_code, "shifted coordinates overflowed or collapsed")
            components = separate_phases(values[r], phases_rad=phases[r])
            am, ae = np.frexp(gains[r])
            mm, me = np.frexp(contrast[r])
            planes: tuple[npt.NDArray[np.complex128], ...] = (
                components.dc.astype(np.complex128),
                components.c1,
                np.conjugate(components.c1),
            )
            for plane, query, gm, ge in zip(
                planes,
                queries,
                (am, am * mm / 2, am * mm / 2),
                (ae, ae + me, ae + me),
                strict=True,
            ):
                complex_plane = np.asarray(plane, dtype=np.complex128)
                _, exponent = np.frexp(
                    max(np.max(np.abs(complex_plane.real)), np.max(np.abs(complex_plane.imag)))
                )
                scaled = _scaled_complex(complex_plane, -exponent)
                band = _transform(scaled)
                data.append(_interpolate(band, *query))
                transfers.append(_interpolate(calibration.values, *query))
                data_exponents.append(int(exponent))
                gain_mantissas.append(float(gm))
                gain_exponents.append(int(ge))
        spectrum = _estimate(
            data, transfers, data_exponents, gain_mantissas, gain_exponents, ridge, mask
        )
        if not np.isfinite(spectrum).all():
            raise SimreconError("unrepresentable_reconstruction", "spectrum coordinates overflowed")
        _, exponent = np.frexp(max(np.max(np.abs(spectrum.real)), np.max(np.abs(spectrum.imag))))
        image = _scaled_complex(
            _transform(_scaled_complex(spectrum, -exponent), inverse=True), exponent
        )
        if not np.isfinite(image).all():
            raise SimreconError("unrepresentable_reconstruction", "image coordinates overflowed")
    return Reconstruction2D(image, spectrum, fy, fx, output_spacing, calibration.source)
