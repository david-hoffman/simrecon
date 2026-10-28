"""Supplemental S1/S2/S3 public-contract regressions, authored after implementation.

S1 certifies feasibility independently, then accepts any faithful returned cache.
S2/S3 protect exact zero and caller policy for valid tiny continuous carriers.
No implementation, private injection, FFT observer or coefficient oracle is used.
"""

from __future__ import annotations

import importlib
import math
import traceback
import warnings
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from fractions import Fraction
from functools import lru_cache
from itertools import product
from typing import Any, Literal

import numpy as np
import pytest

SHAPE = (1, 2, 2)
TARGET = Fraction(1, 10000)


@lru_cache(maxsize=1)
def pi_interval() -> tuple[Fraction, Fraction]:
    """Bound Machin's identity with alternating rational arctangent series.

    For positive z<1, the 100-term partial sum is a lower bound and adding
    its next positive term is an upper bound. No binary floating pi is truth.
    """
    bounds = []
    for denominator in (5, 239):
        z = Fraction(1, denominator)
        lower = sum((-1) ** k * z ** (2 * k + 1) / (2 * k + 1) for k in range(100))
        bounds.append((lower, lower + z**201 / 201))
    a, b = bounds
    return 16 * a[0] - 4 * b[1], 16 * a[1] - 4 * b[0]


def physical_interval(dy: int, dx: int, terms: int) -> tuple[Fraction, Fraction]:
    """Bound H_Q / 2**124 at Q=1, zero defocus, in scaled um**-2.

    J0(t)=sum (-1)**k * w**k/(k!)**2, with
    w=t**2/4=pi**2 * 2**-77 * (dy**2+dx**2).
    J0 is positive and decreasing here: its derivative in w is negative by
    the paired alternating derivative series for 0<=w<1. Evaluate endpoint
    alternating bounds, square positive bounds, then multiply pi bounds.
    """
    lo, hi = pi_interval()
    radius2 = dy * dy + dx * dx
    wl, wh = lo * lo * radius2 / 2**77, hi * hi * radius2 / 2**77
    assert 0 <= wl <= wh < 1

    def bessel_bounds(w: Fraction) -> tuple[Fraction, Fraction]:
        # An even number of terms ends with a negative term.
        assert terms % 2 == 0
        lower = sum(((-1) ** k * w**k / math.factorial(k) ** 2 for k in range(terms)), Fraction(0))
        return lower, lower + w**terms / math.factorial(terms) ** 2

    lower, upper = bessel_bounds(wh)[0], bessel_bounds(wl)[1]
    assert 0 < lower <= upper <= 1
    return lo * lower * lower, hi * upper * upper


def exact_required_kernel(payload: Any) -> dict[tuple[int, int], Fraction]:
    """Invert a 4x4 real half-spectrum exactly on all nine required lags.

    Exact stored-y symmetry cancels sine terms. The remaining roots are
    1,0,-1,0. Complete x reflection using weights 1,2,1 before dividing by16.
    """
    cosine = (1, 0, -1, 0)
    return {
        (y, x): sum(
            (
                Fraction.from_float(float(payload[0, ly, k]))
                * cosine[ly * y % 4]
                * cosine[k * x % 4]
                * (2 if k == 1 else 1)
                for ly, k in product(range(4), range(3))
            ),
            Fraction(0),
        )
        / 16
        / 2**124
        for y, x in product(range(-1, 2), repeat=2)
    }


def complete_norm_intervals(
    kernel: dict[tuple[int, int], Fraction], terms: int
) -> tuple[tuple[Fraction, Fraction], ...]:
    """Enumerate all16 interactions, absolute per-lag error before pixel sum.

    One detector row has four source columns. Each column has four fine
    detector sites. Common dy*dx*2**124=2**-76 cancels in BOTH error ratios.
    Returned norms are scaled dimensionless norms (divide each by2**76).
    """
    truth = {(y, x): physical_interval(y, x, terms) for y, x in kernel}
    errors: list[tuple[Fraction, Fraction]] = []
    bases: list[tuple[Fraction, Fraction]] = []
    for jy, jx in product(range(2), repeat=2):
        el, eu, bl, bu = (Fraction(0) for _ in range(4))
        for ny, nx in product(range(2), repeat=2):
            lag = ny - jy, nx - jx
            h, (lo, hi) = kernel[lag], truth[lag]
            el += max(lo - h, h - hi, Fraction(0))
            eu += max(abs(h - lo), abs(h - hi))
            bl, bu = bl + lo, bu + hi
        errors.append((el, eu))
        bases.append((bl, bu))
    row_e = sum((e[0] for e in errors), Fraction(0)), sum((e[1] for e in errors), Fraction(0))
    col_e = max(e[0] for e in errors), max(e[1] for e in errors)
    row_b = sum((b[0] for b in bases), Fraction(0)), sum((b[1] for b in bases), Fraction(0))
    col_b = max(b[0] for b in bases), max(b[1] for b in bases)
    assert row_b[0] > 0 and col_b[0] > 0
    return row_e, col_e, row_b, col_b


def certify_feasibility() -> None:
    """Construct a permitted witness; never prescribe its returned coefficients."""
    lo, hi = pi_interval()
    eta = Fraction(1, 2**70)
    # Max t**2/2 = 2*pi**2*2**-76; J0 series gives 1-J0**2<=t**2/2.
    assert 2 * hi * hi / 2**76 < eta
    # 4*A lies in binade127, with binary32 ULP2**104. Round using rationals.
    lower_index = (lo * 2**22 + Fraction(1, 2)).numerator // (
        lo * 2**22 + Fraction(1, 2)
    ).denominator
    upper_index = (hi * 2**22 + Fraction(1, 2)).numerator // (
        hi * 2**22 + Fraction(1, 2)
    ).denominator
    assert lower_index == upper_index
    tau = lower_index * 2**104
    assert 2**127 < 4 * lo * 2**124 <= 4 * hi * 2**124 < (2 - Fraction(1, 2**23)) * 2**127
    assert tau < (2 - Fraction(1, 2**23)) * 2**127
    error = max(abs(Fraction(tau, 4 * 2**124) / p - 1) for p in (lo, hi))
    assert error <= Fraction(1, 2**24)
    assert (Fraction(1, 2**24) + eta) / (1 - eta) < Fraction(1, 2**23) < TARGET
    signs = (1, 1, -1, 1)
    # The four-point DFT of signs is exactly 2*signs (imaginary parts cancel).
    cosine = (1, 0, -1, 0)
    assert all(
        sum(signs[j] * cosine[k * j % 4] for j in range(4)) == 2 * signs[k] for k in range(4)
    )
    witness = np.array(
        [[[tau * signs[ly] * signs[k] for k in range(3)] for ly in range(4)]], dtype=np.float32
    )
    assert np.isfinite(witness).all()
    assert np.array_equal(witness, witness[:, [0, 3, 2, 1], :])
    kernel = exact_required_kernel(witness)
    assert set(kernel.values()) == {Fraction(tau, 4 * 2**124)}
    er, ec, br, bc = complete_norm_intervals(kernel, 4)
    assert er[1] <= TARGET * br[0] and ec[1] <= TARGET * bc[0]
    print(
        "S1_QUALIFIED: normal finite binary32 witness;16 interactions; row/column ratio bounds",
        float(er[1] / br[0]),
        float(ec[1] / bc[0]),
    )


def assert_storage(value: Any, shape: tuple[int, ...], dtype: Any) -> None:
    assert type(value) is np.ndarray
    assert value.shape == shape
    assert value.dtype == np.dtype(dtype) and value.dtype.isnative
    assert value.flags.owndata and value.flags.writeable and value.flags.c_contiguous
    assert np.isfinite(value).all()


@contextmanager
def observe_arithmetic_ownership(
    unrelated_errors: tuple[Exception, ...] = (),
) -> Iterator[list[warnings.WarningMessage]]:
    """Collect evidence; neither wording nor attribution proves causality.

    Only qualification controls may supply an exact exception instance issued
    at an entered public dependency boundary. Unknown exceptions block scientific
    classification. Assertions about values/state keep their original meaning.
    """
    with warnings.catch_warnings(record=True) as caught:
        try:
            yield caught
        except Exception as error:
            if any(error is sentinel for sentinel in unrelated_errors):
                traceback.print_exception(error)
                print("QUALIFIED_UNRELATED_EXCEPTION", type(error).__name__, str(error))
                raise
            if isinstance(error, AssertionError):
                raise
            traceback.print_exception(error)
            pytest.fail(
                "OBSERVER_INCONCLUSIVE: public exception ownership is unqualified; "
                f"{type(error).__name__}: {error}",
                pytrace=False,
            )
        finally:
            for warning in caught:
                print(
                    warnings.formatwarning(
                        warning.message, warning.category, warning.filename, warning.lineno
                    ),
                    end="",
                )


def assert_arithmetic_ownership_resolved(
    caught: list[warnings.WarningMessage], unrelated_warnings: tuple[Warning, ...] = ()
) -> None:
    """Block unknown RuntimeWarnings without claiming success or product-red.

    Exact identity qualifies only test-issued dependency sentinels. No phrase,
    filename, stacklevel or warning count constitutes an ownership certificate.
    """
    unresolved = []
    for warning in caught:
        if any(warning.message is sentinel for sentinel in unrelated_warnings):
            print("QUALIFIED_UNRELATED_WARNING", warning.category.__name__, str(warning.message))
        elif issubclass(warning.category, RuntimeWarning):
            unresolved.append(warning)
    if unresolved:
        pytest.fail(
            "OBSERVER_INCONCLUSIVE: RuntimeWarning ownership is unqualified; "
            "retain category/message/location and route causal diagnosis",
            pytrace=False,
        )


def test_s1_upper_range_builder_accepts_any_faithful_representation() -> None:
    certify_feasibility()  # Must succeed before any target import/observation.
    operator = importlib.import_module("scripts.simulation_inverse_operator")

    fields = dict(
        source_shape_zyx=SHAPE,
        source_spacing_um_zyx=(1.0, 2.0**-100, 2.0**-100),
        emission_um=2.0**-62,
        refractive_index=1.0,
        detection_na=1.0,
        pupil_order=1,
    )
    try:
        cache = operator.build_kernel_cache(**fields)
    except Exception as error:
        print("S1_PUBLIC_EXCEPTION", type(error).__name__, getattr(error, "code", None), str(error))
        raise
    assert isinstance(cache, operator.InverseKernelCache)
    for name, expected in fields.items():
        assert getattr(cache, name) == expected
    payload = cache.lateral_spectra
    assert_storage(payload, (1, 4, 3), np.float32)
    assert np.array_equal(payload, payload[:, [0, 3, 2, 1], :])
    kernel = exact_required_kernel(payload)
    for terms in (4, 8, 16):
        er, ec, br, bc = complete_norm_intervals(kernel, terms)
        print(
            "S1_RETURNED_COMPLETE_RATIO_INTERVALS",
            (float(er[0] / br[1]), float(er[1] / br[0])),
            (float(ec[0] / bc[1]), float(ec[1] / bc[0])),
        )
        if er[1] <= TARGET * br[0] and ec[1] <= TARGET * bc[0]:
            return
        assert er[0] <= TARGET * br[1], "S1_PRODUCT_FIDELITY: complete row norm exceeds target"
        assert ec[0] <= TARGET * bc[1], "S1_PRODUCT_FIDELITY: complete column norm exceeds target"
    pytest.fail(
        "S1_OBSERVER_INCONCLUSIVE: rational intervals straddle inclusive target; "
        "route for refinement"
    )


def observe_zero_call(
    operation: str,
    carrier: tuple[float, float],
    underflow: Literal["warn", "raise"],
    *,
    unrelated_warnings: tuple[Warning, ...] = (),
    unrelated_errors: tuple[Exception, ...] = (),
    dependency_scope: Any = nullcontext,
) -> list[warnings.WarningMessage]:
    q = np.array(carrier, dtype=np.float64)
    # Exact normalized binary64 values, without a squared binary64 norm.
    q2 = sum(Fraction.from_float(float(v)) ** 2 for v in q)
    assert 0 <= q2 <= 1
    assert all(math.isfinite(float(v)) for v in q)
    assert (q2 > 0) == (carrier[0] != 0)
    print("S2_S3_QUALIFIED", operation, carrier, underflow, "domain q**2<=1 exact")
    operator = importlib.import_module("scripts.simulation_inverse_operator")
    payload = np.ones((1, 4, 3), dtype=np.float32)

    fields = dict(
        lateral_spectra=payload,
        source_shape_zyx=SHAPE,
        source_spacing_um_zyx=(1.0, 1.0, 1.0),
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=1.0,
        pupil_order=1,
    )
    cache = operator.InverseKernelCache(**fields)
    phases = np.array([0.0], dtype=np.float64)
    source_shape = SHAPE if operation == "forward" else (1, 1, 1, 1)
    output_shape = (1, 1, 1, 1) if operation == "forward" else SHAPE
    data = np.zeros(source_shape, dtype=np.float32)
    arrays = (data, payload, q, phases)
    saved = [a.copy() for a in arrays]
    state = np.random.get_state()
    original_policy = np.geterr().copy()
    try:
        np.seterr(under=underflow)
        policy = np.geterr().copy()
        with observe_arithmetic_ownership(unrelated_errors) as caught:
            warnings.simplefilter("always")
            filters = list(warnings.filters)
            try:
                with dependency_scope():
                    result = getattr(operator, operation)(
                        data,
                        kernel_cache=cache,
                        carrier_yx_per_um=q,
                        phases_rad=phases,
                        beam_amplitudes=(1.0, 0.0, 0.0),
                        excitation_um=1.0,
                    )
            finally:
                assert np.geterr() == policy
                assert warnings.filters == filters
                for original, before in zip(arrays, saved, strict=True):
                    np.testing.assert_array_equal(original, before)
                after = np.random.get_state()
                assert state[0] == after[0] and state[2:] == after[2:]
                np.testing.assert_array_equal(state[1], after[1])
                for name, expected in fields.items():
                    if name != "lateral_spectra":
                        assert getattr(cache, name) == expected
                assert cache.lateral_spectra is payload
        assert_storage(result, output_shape, np.float64)
        assert np.equal(result, 0).all()  # Both signed-zero encodings are valid.
        assert all(not np.shares_memory(result, a) for a in arrays)
        print("S2_S3_OUTPUT_QUALIFIED", operation, carrier, underflow, result.shape)
        assert_arithmetic_ownership_resolved(caught, unrelated_warnings)
        return caught
    finally:
        np.seterr(**original_policy)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("carrier", [(1e-200, 1e-200), (0.0, 0.0)], ids=["tiny", "zero-control"])
@pytest.mark.parametrize("underflow", ["warn", "raise"])
def test_s2_s3_zero_preserves_output_inputs_random_and_caller_policy(
    operation: str, carrier: tuple[float, float], underflow: Literal["warn", "raise"]
) -> None:
    observe_zero_call(operation, carrier, underflow)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "outcome", ["warning-local", "warning-caller", "floating-point-error", "other-error"]
)
def test_s2_s3_observer_admits_causally_unrelated_dependency_outcomes(
    monkeypatch: pytest.MonkeyPatch, operation: str, outcome: str
) -> None:
    """Qualify the same zero/state observer, without requiring any backend.

    Wrappers issue exact sentinels for unrelated work, then delegate unchanged
    on the warning path. Caller attribution deliberately cannot establish owner.
    A correct dependency bypass is valid, but is reported as no entry evidence.
    """
    sentinel: Exception
    if outcome.startswith("warning"):
        sentinel = RuntimeWarning("underflow encountered in multiply")
    elif outcome == "floating-point-error":
        sentinel = FloatingPointError("underflow encountered in multiply")
    else:
        sentinel = ValueError("unrelated public numerical dependency failure")
    entered = False
    observing_public_call = False

    @contextmanager
    def dependency_scope() -> Iterator[None]:
        nonlocal observing_public_call
        observing_public_call = True
        try:
            yield
        finally:
            observing_public_call = False

    def qualify(original: Any) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            nonlocal entered
            if not observing_public_call:
                return original(*args, **kwargs)
            entered = True
            if isinstance(sentinel, Warning):
                warnings.warn(sentinel, stacklevel=2 if outcome == "warning-caller" else 1)
                return original(*args, **kwargs)
            raise sentinel

        return wrapped

    # These are real public numerical dependency boundaries, never private
    # product attributes. No entered boundary or count is a numerical obligation.
    for module_name in ("numpy.fft", "scipy.fft"):
        module = importlib.import_module(module_name)
        for name in (
            "fft",
            "ifft",
            "rfft",
            "irfft",
            "fft2",
            "ifft2",
            "rfft2",
            "irfft2",
            "fftn",
            "ifftn",
            "rfftn",
            "irfftn",
            "hfft",
            "ihfft",
        ):
            monkeypatch.setattr(module, name, qualify(getattr(module, name)))
    special = importlib.import_module("scipy.special")
    for name in ("j0", "roots_legendre"):
        monkeypatch.setattr(special, name, qualify(getattr(special, name)))
    monkeypatch.setattr(
        np.polynomial.legendre, "leggauss", qualify(np.polynomial.legendre.leggauss)
    )
    # Validation is also real public dependency work. Limit issuance to the
    # public call: observer storage/state checks must never supply entry proof.
    monkeypatch.setattr(np, "isfinite", qualify(np.isfinite))
    try:
        caught = observe_zero_call(
            operation,
            (0.0, 0.0),
            "raise",
            unrelated_warnings=(sentinel,) if isinstance(sentinel, Warning) else (),
            unrelated_errors=() if isinstance(sentinel, Warning) else (sentinel,),
            dependency_scope=dependency_scope,
        )
    except Exception as error:
        assert entered and error is sentinel
        print("DEPENDENCY_EXCEPTION_IDENTITY_PRESERVED", operation, outcome)
    else:
        if isinstance(sentinel, Warning):
            assert any(w.message is sentinel for w in caught) == entered
            print("DEPENDENCY_WARNING_IDENTITY_PRESERVED", operation, outcome, "entered", entered)
        else:
            assert not entered, "An entered dependency exception was swallowed"
            print("DEPENDENCY_BYPASS_VALID_ZERO", operation, outcome)
