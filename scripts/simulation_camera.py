"""Sample synthetic camera counts from explicit electron-domain parameters."""

import math

import numpy as np
from numpy.typing import NDArray

from simrecon import SimreconError


def _coefficient(value: float, name: str) -> float:
    """Normalize a plain built-in numeric coefficient to finite binary64."""
    if type(value) is not int and type(value) is not float:
        raise SimreconError("invalid_simulation_camera", f"{name} must be a plain int or float")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise SimreconError("invalid_simulation_camera", f"{name} exceeds float64 range") from error
    if not math.isfinite(normalized):
        raise SimreconError("invalid_simulation_camera", f"{name} must normalize to a finite value")
    return normalized


def _check_range(values: NDArray[np.float64]) -> None:
    """Reject a nonfinite intermediate before subsequent camera arithmetic."""
    if not np.isfinite(values).all():
        raise SimreconError("simulation_camera_range", "Camera arithmetic exceeds float64 range")


def sample_camera(
    expected_signal_e: object,
    *,
    background_e: float,
    read_noise_e: float,
    gain_counts_per_e: float,
    offset_counts: float,
    seed: int,
    shot_noise: bool = True,
) -> NDArray[np.float64]:
    """Sample independent photon and Gaussian read noise, returning raw counts.

    Parameters
    ----------
    expected_signal_e : numpy.ndarray
        Plain, nonempty real array of finite nonnegative expected electrons.
        Values are normalized to native float64 before arithmetic.
    background_e : int or float
        Finite nonnegative background electrons per pixel per exposure.
    read_noise_e : int or float
        Finite nonnegative Gaussian standard deviation in electrons.
    gain_counts_per_e : int or float
        Finite strictly positive conversion gain in counts per electron.
    offset_counts : int or float
        Finite signed camera offset in counts.
    seed : int
        Plain nonnegative integer seed for a per-call PCG64 generator.
    shot_noise : bool, optional
        Draw Poisson signal-plus-background electrons when True (default).

    Returns
    -------
    numpy.ndarray
        Independently owned C-contiguous native float64 counts with the input
        shape. Negative values are retained without clipping or quantization.

    Raises
    ------
    SimreconError
        With code ``invalid_simulation_camera`` for input-domain failures or
        ``simulation_camera_range`` for Poisson or intermediate range failures.
    """
    if type(expected_signal_e) is not np.ndarray:
        raise SimreconError("invalid_simulation_camera", "Signal must be a plain NumPy ndarray")
    if (
        expected_signal_e.ndim == 0
        or expected_signal_e.size == 0
        or expected_signal_e.dtype.kind not in "iuf"
    ):
        raise SimreconError("invalid_simulation_camera", "Signal needs nonempty real numeric axes")

    background = _coefficient(background_e, "background_e")
    read_noise = _coefficient(read_noise_e, "read_noise_e")
    gain = _coefficient(gain_counts_per_e, "gain_counts_per_e")
    offset = _coefficient(offset_counts, "offset_counts")
    if background < 0 or read_noise < 0 or gain <= 0:
        raise SimreconError(
            "invalid_simulation_camera", "Background/noise must be >= 0 and gain > 0"
        )
    if type(seed) is not int or seed < 0:
        raise SimreconError("invalid_simulation_camera", "Seed must be a plain nonnegative int")
    if type(shot_noise) is not bool:
        raise SimreconError("invalid_simulation_camera", "Shot-noise mode must be a plain bool")

    # Local error policy contains expected overflow and permitted underflow;
    # unrelated warnings/exceptions and the caller's policy remain untouched.
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        counts = expected_signal_e.astype(np.float64, order="C", copy=True)
        if not np.isfinite(counts).all() or np.any(counts < 0):
            raise SimreconError(
                "invalid_simulation_camera", "Signal must be finite and nonnegative"
            )
        counts += background
        _check_range(counts)

        rng = np.random.Generator(np.random.PCG64(seed))
        if shot_noise:
            try:
                photons = rng.poisson(counts)
            except ValueError as error:
                raise SimreconError(
                    "simulation_camera_range", "Expected electrons exceed Poisson draw range"
                ) from error
            counts = photons.astype(np.float64)
        counts += rng.normal(0.0, abs(read_noise), size=counts.shape)
        _check_range(counts)
        counts *= gain
        _check_range(counts)
        counts += offset
        _check_range(counts)
    return counts
