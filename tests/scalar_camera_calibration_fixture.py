"""Independent exact-real finite-statistic observers for the public camera API.

No simulator, product reduction, random recipe or implementation seam is used.
Every input scalar is first normalized to binary64, as the contract requires.
"""

from fractions import Fraction
from math import sqrt
from typing import Any

import numpy as np


def finite_targets(groups: tuple[np.ndarray, ...]) -> dict[str, Any]:
    """Use rational finite sums, not a second floating variance implementation."""
    frame_means = []
    frame_variances = []
    for group in groups:
        means = []
        variances = []
        for frame in group:
            pixels = [Fraction(float(value)) for value in frame.flat]
            mean = sum(pixels, Fraction()) / len(pixels)
            means.append(mean)
            variances.append(
                sum(((value - mean) ** 2 for value in pixels), Fraction()) / (len(pixels) - 1)
            )
        frame_means.append(means)
        frame_variances.append(variances)
    return {
        "frame_means": frame_means,
        "frame_variances": frame_variances,
        "means": [sum(v, Fraction()) / len(v) for v in frame_means],
        "variances": [sum(v, Fraction()) / len(v) for v in frame_variances],
    }


def allowances(groups: tuple[np.ndarray, ...]) -> tuple[Fraction, Fraction]:
    """Integer ceil(log2) and rational bounds never overflow or become vacuous."""
    pixels = groups[0].shape[1] * groups[0].shape[2]
    ell = (pixels - 1).bit_length() + max((group.shape[0] - 1).bit_length() for group in groups) + 8
    scale = max(abs(Fraction(float(value))) for g in groups for value in g.flat)
    eps = Fraction(1, 2**52)
    q0 = Fraction(1, 2**1074)
    return (
        256 * ell * eps * scale + 16 * ell * q0,
        4096 * ell * eps * scale**2 + 128 * ell * q0,
    )


def assert_near_exact(actual: Any, expected: Any, allowance: Fraction) -> None:
    assert len(actual) == len(expected)
    for value, target in zip(actual, expected, strict=True):
        assert np.isfinite(value)
        assert abs(Fraction(float(value)) - target) <= allowance


def assert_statistics(estimate: Any, groups: tuple[np.ndarray, ...]) -> None:
    targets = finite_targets(groups)
    mean_bound, variance_bound = allowances(groups)
    assert_near_exact(estimate.means_counts, targets["means"], mean_bound)
    assert_near_exact(estimate.variances_counts2, targets["variances"], variance_bound)
    for index, group in enumerate(groups):
        assert_near_exact(
            estimate.frame_means_counts[index],
            targets["frame_means"][index],
            mean_bound,
        )
        assert_near_exact(
            estimate.frame_variances_counts2[index],
            targets["frame_variances"][index],
            variance_bound,
        )
        # This diagnostic explicitly uses the returned points, not exact moments.
        mean = Fraction(float(estimate.means_counts[index]))
        squared_se = sum(
            ((Fraction(float(v)) - mean) ** 2 for v in estimate.frame_means_counts[index]),
            Fraction(),
        ) / (group.shape[0] * (group.shape[0] - 1))
        observed = float(estimate.empirical_mean_se_counts[index])
        assert np.isfinite(observed) and observed >= 0
        # Bound sqrt rounding independently via the exact rational square.
        lower = max(Fraction(), Fraction(observed) - mean_bound)
        upper = Fraction(observed) + mean_bound
        assert lower**2 <= squared_se <= upper**2


def assert_decisions(estimate: Any) -> None:
    """Returned-point relations are decision tests, not accuracy oracles."""
    dm = float(estimate.means_counts[2]) - float(estimate.means_counts[1])
    dv = float(estimate.variances_counts2[2]) - float(estimate.variances_counts2[1])
    db = float(estimate.means_counts[1]) - float(estimate.means_counts[0])
    assert type(estimate.contrast_counts) is float
    assert estimate.contrast_counts == dm
    codes = []
    if dm <= 0:
        codes.append("nonpositive_flat_contrast")
    if dv <= 0:
        codes.append("nonpositive_variance_contrast")
    gain = None
    if dm > 0 and dv > 0:
        quotient = dv / dm
        if np.isfinite(quotient) and quotient > 0:
            gain = quotient
        else:
            codes.append("unrepresentable_gain")
    if db < 0:
        codes.append("negative_background_estimate")
    assert type(estimate.information_codes) is tuple
    assert estimate.information_codes == tuple(codes)
    if gain is None:
        assert estimate.gain_counts_per_e is None
    else:
        assert type(estimate.gain_counts_per_e) is float
        assert estimate.gain_counts_per_e == gain


def small_groups() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Asymmetric signed frames; unequal T; nonzero frame repeatability."""
    dark = np.array([[[-4, -2, 0]], [[2, 4, 6]]], dtype=np.float64)
    blank = np.array([[[1, 3, 5]], [[3, 5, 7]], [[5, 7, 9]]], dtype=np.float64)
    flat = np.array([[[2, 6, 10]], [[4, 8, 12]]], dtype=np.float64)
    return dark, blank, flat


def literal_se() -> tuple[float, float, float]:
    return 3.0, 2.0 / sqrt(3.0), 1.0
