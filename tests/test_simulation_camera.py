"""NS01 public camera contract; analytic oracles, never a copied RNG recipe."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from importlib import import_module
from typing import Any, Literal, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from simrecon import SimreconError

# Keep owned-test typing independent of product availability. Import failure is
# still a real collection error; flexible arguments allow binding-rejection tests.
sample_camera = cast(
    "Callable[..., NDArray[np.float64]]", import_module("scripts.simulation_camera").sample_camera
)

# Fixed before observing sampler output. At most 50 stochastic scalar checks,
# each with Chebyshev failure probability <= 1/80**2: family bound < 0.008.
N = 1_000_000
K = 80.0


def camera(signal: Any, **overrides: Any) -> Any:
    """Supply explicit ordinary caller parameters, except in binding tests."""
    arguments: dict[str, Any] = {
        "background_e": 0.0,
        "read_noise_e": 0.0,
        "gain_counts_per_e": 1.0,
        "offset_counts": 0.0,
        "seed": 20261022,
        "shot_noise": False,
    }
    arguments.update(overrides)
    return sample_camera(signal, **arguments)


def rejected(signal: Any, code: str = "invalid_simulation_camera", **kw: Any) -> None:
    """Every rejected ndarray must preserve its original bytes and metadata."""
    before = None
    if isinstance(signal, np.ndarray):
        before = (signal.tobytes(), signal.shape, signal.strides, signal.dtype)
    with pytest.raises(SimreconError) as caught:
        camera(signal, **kw)
    assert caught.value.code == code
    if isinstance(signal, np.ndarray):
        assert (signal.tobytes(), signal.shape, signal.strides, signal.dtype) == before


def owned(result: Any, signal: Any) -> None:
    assert type(result) is np.ndarray
    assert result.shape == signal.shape
    assert result.dtype == np.dtype("float64")
    assert result.dtype.isnative
    assert result.flags.c_contiguous
    assert not np.shares_memory(result, signal)


def moments(values: Any, mean: float, variance: float, fourth: float) -> None:
    """Known-mean second moment avoids sample-variance estimator conventions."""
    count = values.size
    centered = values - mean
    assert abs(float(values.mean()) - mean) <= K * math.sqrt(variance / count)
    second = float(np.mean(centered * centered))
    assert abs(second - variance) <= K * math.sqrt((fourth - variance**2) / count)


def frequency(observed: Any, probability: float) -> None:
    tolerance = K * math.sqrt(probability * (1.0 - probability) / observed.size)
    assert abs(float(observed.mean()) - probability) <= tolerance


def independent_pairs(left: Any, right: Any, mean: float, variance: float) -> None:
    # Each side contains disjoint samples. Under independence, product mean is
    # zero and its variance is variance**2, including non-Gaussian laws.
    products = (left - mean) * (right - mean)
    assert abs(float(products.mean())) <= K * variance / math.sqrt(products.size)


def test_exact_sequential_camera_arithmetic() -> None:
    # Binary fractions permit exact independently written count expectations.
    signal = np.array([[0.0, 0.5, 3.0], [8.0, 16.0, 31.5]])
    result = camera(signal, background_e=0.25, gain_counts_per_e=2.0, offset_counts=-7)
    np.testing.assert_array_equal(result, [[-6.5, -5.5, -0.5], [9.5, 25.5, 56.5]])
    owned(result, signal)
    # Separate multiply/add rounding differs from a fused multiply-add here.
    rounded = camera(np.array([1.0 + 2.0**-52]), gain_counts_per_e=3, offset_counts=-3)
    assert rounded[0] == 2.0**-50
    assert camera(np.array([0.0]), offset_counts=-9)[0] == -9.0


@pytest.mark.parametrize("lam,seed", [(0.4, 101), (2.0, 103), (20.0, 107)])
def test_photon_law_includes_background(lam: float, seed: int) -> None:
    # Zero signal makes a noiseless-background implementation distinguishable.
    values = camera(np.zeros(N), background_e=lam, seed=seed, shot_noise=True)
    moments(values, lam, lam, lam + 3.0 * lam**2)
    assert np.all(values >= 0)
    np.testing.assert_array_equal(values, np.floor(values))
    for integer in (0, 1):
        probability = math.exp(-lam) * lam**integer / math.factorial(integer)
        frequency(values == integer, probability)
    independent_pairs(values[::2], values[1::2], lam, lam)


def test_gaussian_law_signed_values_and_spatial_independence() -> None:
    # Standard deviation 3 e, gain 2 counts/e -> variance 36 counts**2.
    values = camera(np.zeros((1000, 1000)), read_noise_e=3, gain_counts_per_e=2, seed=109)
    moments(values, 0.0, 36.0, 3.0 * 36.0**2)
    for threshold in (-6.0, 0.0, 6.0):
        probability = 0.5 * (1.0 + math.erf(threshold / (6.0 * math.sqrt(2.0))))
        frequency(values <= threshold, probability)
    independent_pairs(values[:, ::2], values[:, 1::2], 0.0, 36.0)
    independent_pairs(values[:500], values[500:], 0.0, 36.0)


def test_combined_noise_adds_variances_and_gain_squares() -> None:
    values = camera(
        np.full((1000, 1000), 3.0),
        background_e=2,
        read_noise_e=3,
        gain_counts_per_e=2,
        offset_counts=-11,
        seed=113,
        shot_noise=True,
    )
    # lambda=5 e; v=5+9=14 e**2; mean=-11+2*5=-1 counts.
    moments(values, -1.0, 56.0, 2.0**4 * (5.0 + 3.0 * 14.0**2))
    independent_pairs(values[:, ::2], values[:, 1::2], -1.0, 56.0)
    independent_pairs(values[:500], values[500:], -1.0, 56.0)


def test_combined_distribution_is_poisson_gaussian_convolution() -> None:
    lam, sigma, threshold = 0.4, 0.1, 0.5
    # Condition on P=k: Pr(P+R <= t) = sum Pr(P=k)*Phi((t-k)/sigma).
    # Sum k=0..12; omitted terms are bounded by the Poisson upper tail.
    probability = math.fsum(
        math.exp(-lam)
        * lam**k
        / math.factorial(k)
        * 0.5
        * math.erfc((k - threshold) / (sigma * math.sqrt(2.0)))
        for k in range(13)
    )
    # Successive Poisson tail masses have ratio <= lam/14 after k=13.
    tail_bound = math.exp(-lam) * lam**13 / math.factorial(13) / (1.0 - lam / 14)
    values = camera(np.zeros(N), background_e=lam, read_noise_e=sigma, seed=167, shot_noise=True)
    # Bernoulli variance <= 1/4; preserve 80-SE Chebyshev control and allow
    # series truncation plus a conservative 1e-12 numerical evaluation error.
    tolerance = K / (2.0 * math.sqrt(N)) + tail_bound + 1e-12
    assert abs(float(np.mean(values <= threshold)) - probability) <= tolerance


def test_seeded_repeatability_default_mode_and_legacy_rng_isolation() -> None:
    signal = np.arange(1, 25, dtype=np.float64).reshape(2, 3, 4)
    signal_before = signal.tobytes()
    state = np.random.get_state()
    try:
        for mode in (False, True):
            first = camera(signal, read_noise_e=2, seed=127, shot_noise=mode)
            camera(signal, read_noise_e=4, seed=131, shot_noise=mode)
            second = camera(signal, read_noise_e=2, seed=127, shot_noise=mode)
            np.testing.assert_array_equal(first, second)
            owned(first, signal)
            assert not np.shares_memory(first, second)
        default = sample_camera(
            signal,
            background_e=0,
            read_noise_e=2,
            gain_counts_per_e=1,
            offset_counts=0,
            seed=127,
        )
        np.testing.assert_array_equal(
            default, camera(signal, read_noise_e=2, seed=127, shot_noise=True)
        )
        after = np.random.get_state()
        assert after[0] == state[0]
        np.testing.assert_array_equal(after[1], state[1])
        assert after[2:] == state[2:]
        assert signal.tobytes() == signal_before
    finally:
        np.random.set_state(state)
    np.testing.assert_array_equal(camera(signal, seed=0), camera(signal, seed=2**256))


def test_repeatability_uses_normalized_values() -> None:
    integer = np.array([[2**53 + 1, 3], [0, 7]], dtype=np.uint64)
    normalized = np.asfortranarray(integer.astype(">f8"))
    normalized.flags.writeable = False
    for mode in (False, True):
        first = camera(integer, read_noise_e=2, gain_counts_per_e=3, shot_noise=mode)
        second = camera(normalized, read_noise_e=2.0, gain_counts_per_e=3.0, shot_noise=mode)
        np.testing.assert_array_equal(first, second)


@pytest.mark.parametrize("mode", [False, True])
def test_predetermined_stochastic_seeds_do_not_share_a_fixed_stream(mode: bool) -> None:
    # Zero lambda and sigma=1 give independent symmetric normal signs in either
    # mode. Independent seed streams match all 128 signs with probability 2^-128.
    signal = np.zeros(128)
    first = camera(signal, read_noise_e=1, seed=157, shot_noise=mode)
    second = camera(signal, read_noise_e=1, seed=163, shot_noise=mode)
    assert np.any(np.signbit(first) != np.signbit(second))


@pytest.mark.parametrize("layout", ["strided", "fortran", "readonly", "big-endian"])
@pytest.mark.parametrize("dtype", ["i1", "i8", "u8", "f2", "f4", "f8", "longdouble"])
def test_supported_normalization_layouts_and_ownership(layout: str, dtype: str) -> None:
    signal = np.arange(24, dtype=dtype).reshape(4, 6)
    if layout == "strided":
        signal = signal[::-1, ::2]
    elif layout == "fortran":
        signal = np.asfortranarray(signal)
    elif layout == "readonly":
        signal.flags.writeable = False
    else:
        signal = signal.astype(signal.dtype.newbyteorder(">"))
    before = (signal.tobytes(), signal.strides, signal.flags.writeable)
    expected = signal.astype(np.float64) + 0.5
    result = camera(signal, background_e=0.5)
    owned(result, signal)
    np.testing.assert_array_equal(result, expected)
    assert (signal.tobytes(), signal.strides, signal.flags.writeable) == before


def test_integer_rounding_and_wider_float_underflow_are_permitted() -> None:
    signal = np.array([2**53 + 1, 2**64 - 1], dtype=np.uint64)
    np.testing.assert_array_equal(camera(signal), [float(2**53), float(2**64)])
    # Normalize before adding background; adding in the input dtype loses 1 e.
    for dtype, value, expected in [("f4", 2**24, 16777217), ("f2", 2048, 2049)]:
        np.testing.assert_array_equal(
            camera(np.array([value], dtype=dtype), background_e=1), [expected]
        )
    # Half the smallest longdouble subnormal is already zero in longdouble.
    # Accept that finite zero; N12 separately exercises nonzero wider-to-f64
    # underflow on platforms where longdouble actually has wider range.
    with np.errstate(all="ignore"):
        tiny = np.nextafter(np.longdouble(0), np.longdouble(1))
        signal_wide = np.array([tiny / np.longdouble(2)], dtype=np.longdouble)
    result = camera(signal_wide)
    np.testing.assert_array_equal(result, signal_wide.astype(np.float64))


class ArraySubclass(np.ndarray):
    """A caller-provided subclass, excluded even when values are valid."""


class IntSubclass(int):
    """A numeric subclass is not a plain built-in coefficient or seed."""


class FloatSubclass(float):
    """A float subclass is outside the coefficient domain."""


@pytest.mark.parametrize(
    "signal",
    [
        [1.0],
        (1.0,),
        1.0,
        np.float64(1),
        np.array(1.0),
        np.empty((0,)),
        np.empty((2, 0, 3)),
        np.array([True]),
        np.array([1j]),
        np.array([1], dtype=object),
        np.array(["1"]),
        np.array([b"1"]),
        np.array(["2026-10-22"], dtype="datetime64[D]"),
        np.array([1], dtype="timedelta64[s]"),
        np.array([(1,)], dtype=[("x", "i8")]),
        np.array([1.0]).view(ArraySubclass),
        np.ma.array([1.0], mask=[False]),
        np.array([-1.0]),
        np.array([-1], dtype=np.int64),
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([-np.inf]),
    ],
)
def test_invalid_signal_domains(signal: Any) -> None:
    rejected(signal)


def test_maximum_finite_longdouble_normalization_boundary() -> None:
    # Only this finite maximum's representability depends on platform width.
    signal = np.array([np.finfo(np.longdouble).max], dtype=np.longdouble) * np.longdouble(1)
    if np.finfo(np.longdouble).max <= np.finfo(np.float64).max:
        np.testing.assert_array_equal(camera(signal), signal.astype(np.float64))
    else:
        rejected(signal)


@pytest.mark.parametrize(
    "name", ["background_e", "read_noise_e", "gain_counts_per_e", "offset_counts"]
)
@pytest.mark.parametrize(
    "value",
    [
        True,
        IntSubclass(1),
        FloatSubclass(1),
        np.float64(1),
        np.int64(1),
        np.array(1),
        [1],
        "1",
        1j,
        None,
        math.nan,
        math.inf,
        -math.inf,
        10**400,
    ],
)
def test_invalid_coefficient_types_and_nonfinite_normalization(name: str, value: Any) -> None:
    rejected(np.array([1.0]), **{name: value})


@pytest.mark.parametrize(
    "name,value",
    [
        ("background_e", -1),
        ("read_noise_e", -1),
        ("gain_counts_per_e", -1),
        ("gain_counts_per_e", 0),
        ("gain_counts_per_e", -0.0),
    ],
)
def test_coefficient_sign_domains(name: str, value: Any) -> None:
    rejected(np.array([1.0]), **{name: value})


def test_legitimate_zero_subnormal_gain_and_signed_offsets() -> None:
    smallest = float.fromhex("0x0.0000000000001p-1022")
    result = camera(
        np.array([-0.0, 0.0, 1.0]), background_e=-0.0, read_noise_e=-0.0, gain_counts_per_e=smallest
    )
    np.testing.assert_array_equal(result, [0.0, 0.0, smallest])
    for offset in (-123, -0.0, 0, 123):
        assert camera(np.array([0.0]), offset_counts=offset)[0] == offset
    for mode in (False, True):
        np.testing.assert_array_equal(camera(np.zeros(3), shot_noise=mode), np.zeros(3))


@pytest.mark.parametrize(
    "seed", [-1, True, False, IntSubclass(1), 1.0, np.int64(1), np.uint64(1), "1", None, [1]]
)
def test_invalid_seed_domain(seed: Any) -> None:
    rejected(np.array([1.0]), seed=seed)


@pytest.mark.parametrize("mode", [0, 1, np.bool_(True), "True", None, np.array(True)])
def test_invalid_noise_mode(mode: Any) -> None:
    rejected(np.array([1.0]), shot_noise=mode)


def test_large_plain_integer_seed_is_valid_for_stochastic_calls() -> None:
    signal = np.ones(16)
    first = camera(signal, seed=2**1024 + 17, shot_noise=True, read_noise_e=1)
    np.testing.assert_array_equal(
        first, camera(signal, seed=2**1024 + 17, shot_noise=True, read_noise_e=1)
    )


def test_ordinary_python_argument_binding_errors() -> None:
    valid: dict[str, Any] = dict(
        background_e=0, read_noise_e=0, gain_counts_per_e=1, offset_counts=0, seed=1
    )
    for name in valid:
        incomplete = valid.copy()
        del incomplete[name]
        with pytest.raises(TypeError):
            sample_camera(np.ones(1), **incomplete)
    with pytest.raises(TypeError):
        sample_camera(**valid)
    with pytest.raises(TypeError):
        sample_camera(np.ones(1), unexpected=1, **valid)
    with pytest.raises(TypeError):
        sample_camera(np.ones(1), 0, 0, 1, 0, 1)


def test_lambda_overflow_and_paired_poisson_draw_range() -> None:
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    for mode in (False, True):
        rejected(
            np.array([1.0, maximum]),
            "simulation_camera_range",
            background_e=maximum,
            shot_noise=mode,
        )
    # Well beyond NumPy's int64 draw range, still finite binary64 arithmetic.
    for lam in (float(2**63), 1e20, maximum):
        rejected(np.array([lam]), "simulation_camera_range", shot_noise=True)
        np.testing.assert_array_equal(camera(np.array([lam])), [lam])
    # A large supported Poisson mean must not face an invented small cap.
    result = camera(np.array([1e12]), shot_noise=True, seed=137)
    assert result.shape == (1,)
    assert np.isfinite(result).all()


@pytest.mark.parametrize(
    "signal,kw",
    [
        (np.array([1.0, 1e308]), {"gain_counts_per_e": 2}),
        (np.array([0.0, 1e308]), {"offset_counts": 1e308}),
        (np.array([1e308]), {"gain_counts_per_e": 2, "offset_counts": -1e308}),
    ],
)
def test_intermediate_product_and_offset_overflow(signal: Any, kw: Any) -> None:
    rejected(signal, "simulation_camera_range", **kw)


def test_electron_sum_overflow_rejects_whole_call() -> None:
    # A million independent normals make failure to reach overflow negligible:
    # lambda=1e308, sigma=1e308; R>~0.798 sigma overflows P+R.
    rejected(np.full(N, 1e308), "simulation_camera_range", read_noise_e=1e308, seed=139)


@pytest.mark.parametrize("policy", ["ignore", "warn", "raise", "call", "print", "log"])
def test_numpy_policy_preserved_and_expected_warnings_contained(
    policy: Literal["ignore", "warn", "raise", "call", "print", "log"],
) -> None:
    before = np.geterr()
    callback = np.geterrcall()
    try:
        np.seterr(all=policy)
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always")
            rejected(np.array([1e308]), "simulation_camera_range", gain_counts_per_e=2)
            rejected(np.array([1e308]), "simulation_camera_range", background_e=1e308)
            rejected(np.array([1e20]), "simulation_camera_range", shot_noise=True)
            rejected(np.full(4096, 1e308), "simulation_camera_range", read_noise_e=1e308, seed=151)
            rejected(np.array([1.0]), background_e=10**400)
            rejected(np.array([np.inf]))
            if np.finfo(np.longdouble).max > np.finfo(np.float64).max:
                rejected(np.array([np.finfo(np.longdouble).max], dtype=np.longdouble))
            with np.errstate(all="ignore"):
                half_smallest = np.longdouble(float.fromhex("0x0.0000000000001p-1022")) / 2
                sub_float64 = np.array([half_smallest, -half_smallest], dtype=np.longdouble)
            np.testing.assert_array_equal(camera(sub_float64), [0.0, 0.0])
            # Underflow is a permitted complete result, even for policy=raise.
            smallest = float.fromhex("0x0.0000000000001p-1022")
            np.testing.assert_array_equal(
                camera(np.array([smallest]), gain_counts_per_e=0.5), [0.0]
            )
            assert camera(np.array([1.0]))[0] == 1.0
        assert not [warning for warning in seen if issubclass(warning.category, RuntimeWarning)]
        assert np.geterr() == dict.fromkeys(before, policy)
        assert np.geterrcall() is callback
    finally:
        np.seterr(**before)
        np.seterrcall(callback)


def test_real_caller_photon_budget_and_camera_correction() -> None:
    # Two exposures, two pixels, 100 e total signal budget. Fractions sum to 1.
    fractions = np.array([[0.125, 0.375], [0.25, 0.25]])
    photons = 100.0 * fractions
    counts = camera(photons, background_e=2, gain_counts_per_e=4, offset_counts=10)
    np.testing.assert_array_equal(counts, [[68, 168], [118, 118]])
    corrected = (counts - 10.0) / 4.0 - 2.0
    np.testing.assert_array_equal(corrected, [[12.5, 37.5], [25.0, 25.0]])
    assert float(corrected.sum()) == 100.0
    # Repeated exposures assess corrected moments independently per pixel.
    repeated = np.broadcast_to(photons, (250_000, 2, 2))
    noisy = camera(
        repeated,
        background_e=2,
        read_noise_e=1.5,
        gain_counts_per_e=4,
        offset_counts=10,
        seed=149,
        shot_noise=True,
    )
    recovered = (noisy - 10.0) / 4.0 - 2.0
    for row, column, truth in [(0, 0, 12.5), (0, 1, 37.5), (1, 0, 25.0), (1, 1, 25.0)]:
        lam = truth + 2.0
        variance = lam + 1.5**2
        moments(recovered[:, row, column], truth, variance, lam + 3.0 * variance**2)
