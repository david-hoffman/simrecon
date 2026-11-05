"""Pure array camera preparation and native SVN307 phase quadratures."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ._model import SimreconError

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
_INT_MAX = 2**31 - 1
_REFERENCE = (
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)


@dataclass
class PreparedBands:
    """Prepared quadratures, scalar noise factors and explicit preparation metadata.

    Arrays own writable storage independent of the caller and of one another.
    Quadratures use detector-count units and unnormalized forward Fourier sums.
    The slot order is zero, even first, odd first, even second, odd second, etc.
    """

    quadratures: ComplexArray
    noise_variance_factors: FloatArray
    separation_matrices: FloatArray
    phase_angles_rad: FloatArray
    frame_sums: FloatArray
    equalization_gains: FloatArray
    background_after: FloatArray
    slope_after: FloatArray
    sentinel_frames: tuple[tuple[int, int, int, int], ...]
    input_shape: tuple[int, ...]
    input_scale: float
    dxy_um: float
    dz_um: float
    lateral_zoom: int
    axial_zoom: int
    edge_pixels: int
    equalize: bool
    equalize_z: bool
    equalize_time: bool
    phase_policy: str
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = _REFERENCE


def _invalid(name: str, message: str) -> SimreconError:
    """Construct an argument-domain error without exposing a partial result."""
    return SimreconError("preparation-domain", f"{name}: {message}")


def _integer(value: Any, name: str, *, positive: bool = True) -> int:
    """Resolve a source signed 32-bit integer scalar."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise _invalid(name, "must be an integer scalar")
    result = int(value)
    if not -(2**31) <= result <= _INT_MAX or (positive and result <= 0):
        raise _invalid(name, "outside the positive count/zoom or signed 32-bit index range")
    return result


def _real(value: Any, name: str, *, positive: bool = False) -> float:
    """Resolve a finite real scalar without accepting booleans or arrays."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise _invalid(name, "must be a finite real scalar")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise _invalid(name, "not representable as a finite real scalar") from error
    if not math.isfinite(result) or (positive and result <= 0):
        raise _invalid(name, "must be finite" + (" and positive" if positive else ""))
    return result


def _array_metadata(value: Any, name: str, shape: tuple[int, ...]) -> None:
    """Check shape and standard real dtype before any array-sized operation."""
    if not isinstance(value, np.ndarray):
        raise _invalid(name, "must be a NumPy array")
    if value.shape != shape:
        raise _invalid(name, f"shape must be {shape}")
    dtype = value.dtype
    if not (
        (dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        or (dtype.kind == "f" and dtype.itemsize in (2, 4, 8))
    ):
        raise _invalid(name, "dtype must be a standard real integer or float16/32/64")


def _finite(value: NDArray[Any], name: str) -> None:
    """Reject nonfinite input values or numerical operation results."""
    if not np.isfinite(value).all():
        raise _invalid(name, "nonfinite values or numerical overflow")


def _array(value: Any, name: str, shape: tuple[int, ...]) -> FloatArray:
    """Copy a validated real array to owned binary64 storage."""
    _array_metadata(value, name, shape)
    _finite(value, name)
    return np.array(value, dtype=np.float64, copy=True)


def _index_domain(shape: tuple[int, ...], orders: int) -> None:
    """Reject source integer products and platform array limits using metadata."""
    t, d, p, z, y, x = shape
    q = 2 * orders - 1
    source_products = (*shape, q, x * y * z, (x + 2) * y * z, d * p * z, q * p, d * orders)
    if any(value > _INT_MAX for value in source_products):
        raise _invalid("images/norders", "dimension or product exceeds signed 32-bit index range")
    # Include byte addressing for the binary64 workspaces and complex128 output.
    platform_sizes = (math.prod(shape) * 8, t * d * q * z * y * (x // 2 + 1) * 16, d * q * p * 8)
    if any(value > np.iinfo(np.intp).max for value in platform_sizes):
        raise _invalid("images/norders", "array size exceeds platform intp index range")


def _raw_samples(images: NDArray[Any], name: str = "images") -> None:
    """Check exact float32 representation against the original sample dtype."""
    _finite(images, name)
    with np.errstate(over="ignore", invalid="ignore"):
        decoded = images.astype(np.float32)
    _finite(decoded, f"{name} float32 representation")
    if images.dtype.kind in "iu":
        # Float-to-integer round trips are safe only inside the original domain.
        # Comparing integer inputs with floats would silently round uint64 values.
        bits = images.dtype.itemsize * 8
        low = 0 if images.dtype.kind == "u" else -(2 ** (bits - 1))
        high = 2**bits if images.dtype.kind == "u" else 2 ** (bits - 1)
        if np.any(decoded < low) or np.any(decoded >= high):
            raise _invalid(name, "samples are not exactly float32 representable")
        restored = decoded.astype(images.dtype)
    else:
        restored = decoded.astype(images.dtype)
    if not np.array_equal(images, restored):
        raise _invalid(name, "samples are not exactly float32 representable")


def _phase_matrices(
    angles: FloatArray, orders: int, supplied: bool
) -> tuple[FloatArray, FloatArray]:
    """Build selected separation rows and scalar order noise without a rank cutoff."""
    directions, phases = angles.shape
    slots = 2 * orders - 1
    rows = np.ones((directions, slots, phases), dtype=np.float64)
    noise = np.ones((directions, orders), dtype=np.float64)
    for m in range(1, orders):
        rows[:, 2 * m - 1] = np.cos(m * angles)
        rows[:, 2 * m] = np.sin(m * angles)
    _finite(rows, "phase matrix")
    if supplied:
        for d in range(directions):
            if np.unique(angles[d]).size < slots:
                raise _invalid("phases_rad", "rank-deficient phase design")
            design = rows[d].T.copy()
            design[:, 0] /= phases
            design[:, 1:] *= 2 / phases
            if slots == phases:
                rows[d] = np.linalg.inv(design)
            else:
                # A = U R gives the same unweighted left inverse R^-1 U.T
                # without squaring the conditioning by forming A.T @ A.
                orthogonal, triangular = np.linalg.qr(design, mode="reduced")
                rows[d] = np.linalg.solve(triangular, orthogonal.T)
            _finite(rows[d], "phase matrix inverse")
            # Check achieved resolution, not phase spacing or numerical rank.
            # gamma_(2P) bounds the roundoff of P products and additions in
            # each observer dot product, using binary64 unit roundoff. Use
            # the normwise scale since factorization couples matrix entries.
            unit_roundoff = np.finfo(np.float64).eps / 2
            gamma = 2 * phases * unit_roundoff / (1 - 2 * phases * unit_roundoff)
            residual = np.abs(rows[d] @ design - np.eye(slots))
            envelope = gamma * (np.abs(rows[d]) @ np.abs(design))
            _finite(residual, "phase inverse residual")
            _finite(envelope, "phase inverse roundoff envelope")
            residual_norm = np.linalg.norm(residual, ord=np.inf)
            # ||I-LA|| < 1 is the Neumann-series inverse-resolution boundary,
            # not a condition-number admission rule or an accuracy guarantee.
            if residual_norm >= 1 or residual_norm > np.linalg.norm(envelope, ord=np.inf):
                raise np.linalg.LinAlgError("Phase inverse failed numerical left-inverse check")
            squares = rows[d] ** 2
            noise[d, 0] = squares[0].sum() / phases
            for m in range(1, orders):
                noise[d, m] = squares[2 * m - 1 : 2 * m + 1].sum() / phases
        _finite(noise, "noise variance factors")
    return rows, noise


def _edge(frame: FloatArray, width: int) -> None:
    """Apply y then x edge updates, retaining sequential overlap writes."""
    y, x = frame.shape
    if width == -1:
        frame *= np.sin(np.pi * (np.arange(y) + 0.5) / y)[:, None]
        frame *= np.sin(np.pi * (np.arange(x) + 0.5) / x)[None, :]
    elif width > 0:
        delta = (frame[-1, :] - frame[0, :]) / 2
        weights = 1 - np.sin(np.pi * (np.arange(width) + 0.5) / (2 * width))
        for k, weight in enumerate(weights):
            adjustment = delta * weight
            frame[k, :] += adjustment
            frame[y - 1 - k, :] -= adjustment
        delta = (frame[:, -1] - frame[:, 0]) / 2
        for k, weight in enumerate(weights):
            adjustment = delta * weight
            frame[:, k] += adjustment
            frame[:, x - 1 - k] -= adjustment


def prepare_bands(
    images: Any,
    *,
    dxy_um: Any,
    dz_um: Any,
    norders: Any,
    background: Any,
    lateral_zoom: Any,
    axial_zoom: Any,
    flatfield_slope: Any = None,
    exposure_background: Any = None,
    phases_rad: Any = None,
    edge_pixels: Any = 10,
    equalize: Any = True,
    equalize_z: Any = False,
    equalize_time: Any = False,
) -> PreparedBands:
    """Prepare decoded detector exposures as native 3D phase quadratures.

    Parameters
    ----------
    images : numpy.ndarray
        Exact finite-float32 samples in (time, direction, phase, z, y, x) order.
        The axial length is at least two; the x length is positive and even.
    dxy_um, dz_um : real scalar
        Positive detector pitches in micrometres.
    norders : int
        Retained orders including zero; 2*norders-1 must not exceed phases.
    background : real scalar or numpy.ndarray
        Background counts, scalar or a (y, x) map.
    lateral_zoom, axial_zoom : int
        Positive future sampling factors used here only in the input scale.
    flatfield_slope : numpy.ndarray, optional
        Multiplicative dimensionless (y, x) map; defaults to ones.
    exposure_background : numpy.ndarray, optional
        Extra background counts in (time, direction, phase, z) order.
    phases_rad : numpy.ndarray, optional
        Declared (direction, phase) angles in radians. None selects uniform rows.
    edge_pixels : int, optional
        Edge width, -1 for a half-sample sine window, or below -1 for bypass.
    equalize, equalize_z, equalize_time : bool, optional
        Enable frame-sum equalization and share its anchor across z or time.

    Returns
    -------
    PreparedBands
        Owned writable arrays, settings and source identity. Quadratures have
        shape (time, direction, 2*norders-1, z, y, x//2+1) and complex128 dtype.
        The stored lateral Nyquist slots retain raw phase identity, then undergo
        the axial forward transform with every other stored sample.

    Raises
    ------
    SimreconError
        Invalid input, unresolved factorization or nonfinite numerical operation.
    MemoryError
        Array allocation fails. Caller interruption also propagates unchanged.

    Notes
    -----
    Implements the CE02 mathematical mapping, not bitwise C rounding. Inputs
    remain unchanged. No estimation, resampling or reconstruction is performed.
    """
    if not isinstance(images, np.ndarray) or images.ndim != 6:
        raise _invalid("images", "must be a six-dimensional NumPy array")
    shape = images.shape
    t_count, directions, phases, z_count, y, x = shape
    if any(n <= 0 for n in shape) or z_count < 2 or x < 2 or x % 2:
        raise _invalid("images", "positive axes, Z >= 2 and even X >= 2 are required")
    orders = _integer(norders, "norders")
    lateral = _integer(lateral_zoom, "lateral_zoom")
    axial = _integer(axial_zoom, "axial_zoom")
    width = _integer(edge_pixels, "edge_pixels", positive=False)
    _index_domain(shape, orders)
    slots = 2 * orders - 1
    if slots > phases:
        raise _invalid("norders", "2*norders-1 must not exceed phase count")
    if int(np.float32(lateral)) != lateral:
        raise _invalid("lateral_zoom", "must be exactly float32 representable")
    if width > min(x, y):
        raise _invalid("edge_pixels", "width exceeds lateral dimensions")
    pitch_xy = _real(dxy_um, "dxy_um", positive=True)
    pitch_z = _real(dz_um, "dz_um", positive=True)
    for name, flag in (
        ("equalize", equalize),
        ("equalize_z", equalize_z),
        ("equalize_time", equalize_time),
    ):
        if not isinstance(flag, (bool, np.bool_)):
            raise _invalid(name, "must be a boolean")
    _array_metadata(images, "images", shape)
    _raw_samples(images)
    camera_background = (
        _array(background, "background", (y, x))
        if isinstance(background, np.ndarray)
        else np.full((y, x), _real(background, "background"), dtype=np.float64)
    )
    slope = (
        np.ones((y, x), dtype=np.float64)
        if flatfield_slope is None
        else _array(flatfield_slope, "flatfield_slope", (y, x))
    )
    extra = (
        np.zeros(shape[:4], dtype=np.float64)
        if exposure_background is None
        else _array(exposure_background, "exposure_background", shape[:4])
    )
    supplied = phases_rad is not None
    angles = (
        _array(phases_rad, "phases_rad", (directions, phases))
        if supplied
        else np.tile(2 * np.pi * np.arange(phases) / phases, (directions, 1)).copy()
    )
    alpha = 1 / (x * y * z_count * lateral**2 * axial * directions)
    if not math.isfinite(alpha) or alpha <= 0:
        raise _invalid("input scale", "zero or nonfinite numerical alpha")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            rows, noise = _phase_matrices(angles, orders, supplied)
            frames = np.empty(shape, dtype=np.float64)
            sums = np.empty(shape[:4], dtype=np.float64)
            events: list[tuple[int, int, int, int]] = []
            for t in range(t_count):
                for d in range(directions):
                    for z in range(z_count):
                        for p in range(phases):
                            raw = np.array(images[t, d, p, z], dtype=np.float64, copy=True)
                            if raw[-1, -1] == -1:
                                raw[-1, -1] = raw[-1, -2]
                                camera_background[-1, -1] = camera_background[-1, -2]
                                slope[-1, -1] = 1
                                events.append((t, d, z, p))
                            frame = alpha * slope * (raw - camera_background - extra[t, d, p, z])
                            _finite(frame, "camera correction")
                            _edge(frame, width)
                            _finite(frame, "edge operation")
                            sums[t, d, p, z] = frame.sum()
                            frames[t, d, p, z] = frame
            _finite(sums, "frame sums")
            gains = np.ones(shape[:4], dtype=np.float64)
            if equalize:
                if np.any(sums == 0):
                    raise _invalid("equalization sums", "zero divisor")
                for t in range(t_count):
                    for z in range(z_count):
                        anchor = sums[0 if equalize_time else t, 0, 0, 0 if equalize_z else z]
                        gains[t, :, :, z] = anchor / sums[t, :, :, z]
                _finite(gains, "equalization gains")
                frames *= gains[..., None, None]
                _finite(frames, "equalization operation")
            quadratures = np.empty(
                (t_count, directions, slots, z_count, y, x // 2 + 1), dtype=np.complex128
            )
            for t in range(t_count):
                for d in range(directions):
                    lateral_fft = np.fft.rfft2(frames[t, d], axes=(-2, -1))
                    _finite(lateral_fft, "lateral transform")
                    separated = np.empty((slots, z_count, y, x // 2 + 1), dtype=np.complex128)
                    separated[..., :-1] = np.einsum("qp,pzyx->qzyx", rows[d], lateral_fft[..., :-1])
                    separated[..., -1] = lateral_fft[:slots, ..., -1]
                    _finite(separated, "phase separation transform")
                    axial_fft = np.fft.fft(separated, axis=1)
                    _finite(axial_fft, "axial transform")
                    quadratures[t, d] = axial_fft
    except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
        raise SimreconError(
            "preparation-numerical", f"Numerical preparation failure: {error}"
        ) from error
    return PreparedBands(
        quadratures=quadratures,
        noise_variance_factors=noise,
        separation_matrices=rows,
        phase_angles_rad=angles,
        frame_sums=sums,
        equalization_gains=gains,
        background_after=camera_background,
        slope_after=slope,
        sentinel_frames=tuple(events),
        input_shape=shape,
        input_scale=alpha,
        dxy_um=pitch_xy,
        dz_um=pitch_z,
        lateral_zoom=lateral,
        axial_zoom=axial,
        edge_pixels=width,
        equalize=bool(equalize),
        equalize_z=bool(equalize_z),
        equalize_time=bool(equalize_time),
        phase_policy="supplied" if supplied else "uniform",
    )
