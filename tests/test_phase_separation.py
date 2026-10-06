"""Proposal 3 blind A public-entry tests, V01--V29.

V27 delegates pixel/storage preservation to the untouched complete MRC suite.
V28 supplies numeric fixture evidence; real rendering is C's later obligation.
An OracleUnresolved failure is deliberately not a product-defect verdict.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from collections.abc import Callable
from fractions import Fraction as F
from typing import Any, Literal, cast

import numpy as np
import pytest

from phase_separation_fixture import (
    EPS,
    PHASES,
    Q_HALF,
    Array,
    RationalFit,
    analytic_fixture,
    dot,
    expected_arrays,
    gram,
    mv,
    norm2,
    positive_definite,
    rational,
    represented_h,
    sqrt_interval,
    transpose,
)
from simrecon import PhaseComponents, SimreconError, separate_phases

# Callable cast avoids binding type-checks to a pre-amendment installed stub.
# All calls still use the actual public exported function.
separate = cast(Callable[..., PhaseComponents], separate_phases)


class ArraySubclass(np.ndarray[Any, Any]):
    """Exercise the explicit plain-array boundary."""


class NoCoercion:
    """Detect coercion of an input outside the plain-array domain."""

    def __array__(self, *args: Any, **kwargs: Any) -> Any:
        """Fail if a caller tries to coerce this invalid input."""
        raise AssertionError("non-ndarray must be rejected before coercion")


def phases() -> Array:
    return np.array(PHASES)


def observations(n: int = 7, shape: tuple[int, int] = (2, 3)) -> Array:
    return (np.arange(n * shape[0] * shape[1]).reshape(n, *shape) % 13 - 6).astype(np.float64)


def snapshot(value: Any) -> tuple[Any, ...] | None:
    if isinstance(value, np.ndarray):
        return value.tobytes(), value.shape, value.dtype.str, value.strides, value.flags.writeable
    return None


def domain(images: Any, angles: Any, code: str) -> None:
    before = snapshot(images), snapshot(angles)
    with pytest.raises(SimreconError) as caught:
        separate(images, phases_rad=angles)
    assert isinstance(caught.value, ValueError)
    assert caught.value.code == code
    assert isinstance(caught.value.message, str)
    assert (snapshot(images), snapshot(angles)) == before, "V23 rejection must preserve inputs"


def accurate(images: Array, angles: Array) -> PhaseComponents:
    before = snapshot(images), snapshot(angles)
    result = separate(images, phases_rad=angles)
    assert isinstance(result, PhaseComponents)
    for value, dtype in ((result.dc, np.float64), (result.c1, np.complex128)):
        assert type(value) is np.ndarray
        assert value.shape == images.shape[1:], "V21 spatial axes/order"
        assert value.dtype == np.dtype(dtype) and value.dtype.isnative
        assert value.flags.c_contiguous and value.flags.writeable
        assert not np.shares_memory(value, images)
        assert not np.shares_memory(value, angles)
    assert not np.shares_memory(result.dc, result.c1)
    assert (snapshot(images), snapshot(angles)) == before, "V23 success must preserve inputs"
    assert np.isfinite(result.dc).all() and np.isfinite(result.c1).all()
    with np.errstate(all="ignore"):
        converted = images.astype(np.float64)
    fit = RationalFit.from_phases(angles)
    for index in np.ndindex(images.shape[1:]):
        b = [rational(x) for x in converted[(slice(None), *index)]]
        z = [
            rational(result.dc[index]),
            rational(result.c1.real[index]),
            rational(result.c1.imag[index]),
        ]
        fit.certify(b, z)
    return result


@pytest.mark.parametrize("angles", [[-0.41, 1.13, 3.72], list(PHASES), [-0.2, 0.0, 0.27, 0.48]])
def test_v01_unequal_signed_asymmetric_recovery(angles: list[float]) -> None:
    p = np.array(angles)
    fixture = analytic_fixture((3, 5))
    h = represented_h(p)
    images = (
        fixture.generating_dc[None]
        + 2 * np.real(fixture.generating_c1)[None] * h[:, 1, None, None]
        - 2 * np.imag(fixture.generating_c1)[None] * h[:, 2, None, None]
    )
    accurate(images, p)


@pytest.mark.parametrize("constant", [0.0, 10.0, -17.0, 2.0**-1022, 2.0**900])
def test_v02_exact_model_constants_and_zero(constant: float) -> None:
    p = phases()
    images = np.full((p.size, 1, 2), constant)
    result = accurate(images, p)
    fit = RationalFit.from_phases(p)
    b = [rational(constant)] * p.size
    assert fit.expected(b) == [rational(constant), F(0), F(0)]
    if constant == 0:
        assert np.count_nonzero(result.dc) == np.count_nonzero(result.c1) == 0


def test_v03_off_model_fitted_constant_is_not_mean() -> None:
    p = phases()
    images = observations()
    fit = RationalFit.from_phases(p)
    b = [rational(v) for v in images[:, 0, 0]]
    star = fit.expected(b)
    residual = fit.residual(b, star)
    assert norm2(residual) > F(1, 10)
    assert abs(star[0] - sum(b) / len(b)) > F(1, 100)
    assert mv(transpose(fit.k), residual) == [F(0)] * 3
    accurate(images, p)


@pytest.mark.parametrize("n,offset", [(3, 0.0), (4, 0.0), (8, 0.37)])
def test_v04_orthogonal_cycle_special_case(n: int, offset: float) -> None:
    p = offset + np.arange(n) * (2 * np.pi / n)
    images = (10 + 4 * np.cos(p) + 2 * np.sin(p))[:, None, None]
    result = accurate(images, p)
    # Independent ideal formula is supplemental; the rational certificate above
    # applies to the actual represented problem, not ideal exact trig entries.
    np.testing.assert_allclose(result.dc, images.sum(axis=0) / n, rtol=0, atol=1e-11)
    formula = (images[:, 0, 0] * np.exp(-1j * p)).sum() / n
    np.testing.assert_allclose(result.c1, formula, rtol=0, atol=1e-11)
    np.testing.assert_allclose(result.c1, 2 - 1j, rtol=0, atol=1e-11)


def test_v05_joint_permutation_independent_fits() -> None:
    p, images = phases(), observations()
    order = np.array([4, 0, 6, 2, 5, 1, 3])
    first = accurate(images, p)
    second = accurate(images[order], p[order])
    left, right = RationalFit.from_phases(p), RationalFit.from_phases(p[order])
    for index in np.ndindex(images.shape[1:]):
        b = [rational(v) for v in images[(slice(None), *index)]]
        b2 = [b[int(i)] for i in order]
        star = left.expected(b)
        assert star == right.expected(b2)
        bound1, bound2 = left.forward_bound(b, star), right.forward_bound(b2, star)
        assert bound1 is not None and bound2 is not None
        for a, c in (
            (first.dc, second.dc),
            (first.c1.real, second.c1.real),
            (first.c1.imag, second.c1.imag),
        ):
            assert abs(rational(a[index]) - rational(c[index])) <= bound1 + bound2


@pytest.mark.parametrize(
    "p",
    [
        np.array([-19.3, -7.8, 0.9, 18.4, 41.1]),
        np.array([1e16, 1e16 + 4, 1e16 + 8, 1e16 + 12, 1e16 + 16]),
        np.array(PHASES) + 6 * np.pi,
    ],
)
def test_v06_direct_large_negative_periodic_angles(p: Array) -> None:
    h = represented_h(p)
    assert np.linalg.matrix_rank(h) == 3
    accurate(observations(p.size), p)


EXACT_DTYPES = ["i1", "u1", "<i2", ">u2", "<i4", ">u4", "f2", "<f4", ">f8"]


@pytest.mark.parametrize("dtype", EXACT_DTYPES)
@pytest.mark.parametrize("layout", ["plain", "strided_readonly"])
def test_v07_promotable_images_storage_examples(dtype: str, layout: str) -> None:
    images = np.arange(7 * 2 * 3).reshape(7, 2, 3).astype(dtype)
    if layout == "strided_readonly":
        images = images[::-1, :, ::-1]
        images.flags.writeable = False
    accurate(images, phases())


@pytest.mark.parametrize("dtype", EXACT_DTYPES)
def test_v07_promotable_angle_dtypes(dtype: str) -> None:
    p = np.arange(5).astype(dtype)[::-1]
    p.flags.writeable = False
    accurate(observations(5), p)


@pytest.mark.parametrize("dtype,base", [("i8", 2**53 + 1), ("u8", 2**63 + 1)])
def test_v08_lossy_integer_truth(dtype: str, base: int) -> None:
    images = np.array([base + 3 * i for i in range(7)], dtype=dtype)[:, None, None]
    with np.errstate(all="ignore"):
        converted = images.astype(np.float64)
    assert int(images[0, 0, 0]) != int(converted[0, 0, 0])
    accurate(images, phases())
    p = np.array([2**53 + 1 + 4 * i for i in range(5)], dtype=dtype)
    assert int(p[0]) != int(p.astype(np.float64)[0])
    accurate(observations(5), p)


def test_v08_available_wider_float_rounding_underflow() -> None:
    # No skip: same-width platforms still exercise allowed real floating dtype.
    wider = np.longdouble
    images = observations().astype(wider)
    if np.finfo(wider).nmant > np.finfo(np.float64).nmant:
        images += wider(2) ** -60
        assert images[0, 0, 0] != wider(float(images[0, 0, 0]))
    accurate(images, phases().astype(wider))
    if np.finfo(wider).smallest_subnormal < np.longdouble(2) ** -1074:
        tiny = np.full((7, 1, 1), np.finfo(wider).smallest_subnormal, dtype=wider)
        with np.errstate(all="ignore"):
            assert not tiny.astype(np.float64).any()
        accurate(tiny, phases())


@pytest.mark.parametrize("kind", ["list", "scalar", "subclass", "coercion"])
def test_v09_reject_nonplain_images(kind: str) -> None:
    valid = observations()
    values: dict[str, Any] = {
        "list": valid.tolist(),
        "scalar": 3,
        "subclass": valid.view(ArraySubclass),
        "coercion": NoCoercion(),
    }
    domain(values[kind], phases(), "invalid_phase_images")


BAD_DTYPES = ["?", "c16", "O", "U2", "S2", "M8[ns]", "m8[ns]", np.dtype([("a", "f8")])]


@pytest.mark.parametrize("dtype", BAD_DTYPES)
def test_v10_reject_image_dtype(dtype: Any) -> None:
    domain(np.zeros((7, 2, 3), dtype=dtype), phases(), "invalid_phase_dtype")


@pytest.mark.parametrize(
    "shape", [(7,), (7, 3), (7, 1, 2, 3), (2, 2, 3), (0, 2, 3), (7, 0, 3), (7, 2, 0), ()]
)
def test_v11_reject_image_shapes(shape: tuple[int, ...]) -> None:
    domain(np.zeros(shape), phases(), "invalid_phase_shape")


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_v12_reject_nonfinite_source_images(value: float) -> None:
    images = observations()
    images[2, 0, 1] = value
    domain(images, phases(), "nonfinite_phase_images")


@pytest.mark.parametrize("kind", ["list", "scalar", "subclass", "coercion"])
def test_v13_reject_nonplain_phases(kind: str) -> None:
    p = phases()
    values: dict[str, Any] = {
        "list": p.tolist(),
        "scalar": 0.1,
        "subclass": p.view(ArraySubclass),
        "coercion": NoCoercion(),
    }
    domain(observations(), values[kind], "invalid_phase_angles")


@pytest.mark.parametrize("dtype", BAD_DTYPES)
def test_v14_reject_phase_dtype(dtype: Any) -> None:
    domain(observations(), np.zeros(7, dtype=dtype), "invalid_phase_angles_dtype")


@pytest.mark.parametrize("shape", [(), (7, 1), (1, 7), (6,), (8,), (0,)])
def test_v15_reject_phase_shapes_counts(shape: tuple[int, ...]) -> None:
    domain(observations(), np.zeros(shape), "invalid_phase_angles_shape")


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_v16_reject_nonfinite_source_phases(value: float) -> None:
    p = phases()
    p[3] = value
    domain(observations(), p, "nonfinite_phase_angles")


@pytest.mark.parametrize(
    "p",
    [
        np.array([0.0, 0.0, 0.0]),
        np.array([0.0, np.pi, 2 * np.pi]),
        np.array([0, 0, 1, 1]),
        np.array([-1e-8, 0, 1e-8]),
    ],
)
def test_v17_reject_numerically_deficient_sets(p: Array) -> None:
    h = represented_h(p)
    singular = np.linalg.svd(h, compute_uv=False)
    cutoff = float(EPS) * max(p.size, 3) * singular[0]
    assert np.count_nonzero(singular > cutoff) < 3
    domain(observations(p.size), p, "rank_deficient_phases")


@pytest.mark.parametrize("width", [0.2, 1e-3, 2e-7])
def test_v17_clustered_full_rank_no_extra_condition_cutoff(width: float) -> None:
    p = np.array([-width, 0, width])
    singular = np.linalg.svd(represented_h(p), compute_uv=False)
    cutoff = float(EPS) * 3 * singular[0]
    assert singular[-1] > 5 * cutoff  # avoid ambiguous backend threshold band
    fit = RationalFit.from_phases(p)
    if width == 2e-7:
        assert fit.forward_bound([F(-1), F(2), F(4)], fit.expected([F(-1), F(2), F(4)])) is None
    accurate(np.array([-1.0, 2.0, 4.0])[:, None, None], p)


# Public numerical-dependency faults are installed BEFORE the first simrecon
# import in a fresh process, so direct-import aliases are covered. Patch both
# NumPy and SciPy SVD/LS interfaces to allow legitimate alternative solvers.
# We require an observed dependency call. Absence is an unresolved observer
# boundary, not a product failure. No runtime attributes/source are inspected.
SOURCE_FREE_SCRIPT = r"""
import sys
import warnings

def source_free_warning(message, category, filename, lineno, line=None):
    return f"{filename}:{lineno}: {category.__name__}: {message}\n"

def source_free_exception(kind, value, tb):
    seen = set()
    def render(exc):
        if id(exc) in seen:
            return
        seen.add(id(exc))
        prior = exc.__cause__ or (
            None if exc.__suppress_context__ else exc.__context__
        )
        if prior is not None:
            render(prior)
        current = exc.__traceback__
        while current is not None:
            code = current.tb_frame.f_code
            print(
                f"  {code.co_filename}:{current.tb_lineno}: {code.co_name}",
                file=sys.stderr,
            )
            current = current.tb_next
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    render(value)

warnings.formatwarning = source_free_warning
sys.excepthook = source_free_exception
"""

FAULT_SCRIPT = (
    SOURCE_FREE_SCRIPT
    + r"""
import json
import numpy as np
import scipy.linalg as sla
mode = sys.argv[1]
seen = []
def wrapper(original, name):
    def fault(*args, **kwargs):
        seen.append(name)
        if mode == 'linalg':
            raise np.linalg.LinAlgError('blind A injected numerical nonconvergence')
        if mode == 'memory':
            raise MemoryError('blind A injected numerical allocation failure')
        if mode == 'programming':
            raise RuntimeError('blind A injected unrelated programming exception')
        result = original(*args, **kwargs)
        if isinstance(result, tuple):
            factors = tuple(
                np.full_like(v, np.nan, dtype=np.float64)
                if isinstance(v, np.ndarray) else v
                for v in result
            )
            # Preserve public tuple-result records, including NumPy SVDResult.
            return factors if type(result) is tuple else type(result)(*factors)
        return np.full_like(result, np.nan, dtype=np.float64)
    return fault
for module, prefix in ((np.linalg, 'numpy.linalg'), (sla, 'scipy.linalg')):
    for name in ('svd', 'svdvals', 'lstsq', 'pinv'):
        if hasattr(module, name):
            setattr(module, name, wrapper(getattr(module, name), prefix + '.' + name))
from simrecon import separate_phases
p = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
i = np.arange(7., dtype=np.float64)[:, None, None]
with warnings.catch_warnings(record=True) as records:
    warnings.simplefilter('always')
    try:
        separate_phases(i, phases_rad=p)
    except BaseException as exc:
        locations = []
        tb = exc.__traceback__
        while tb is not None:
            locations.append([tb.tb_frame.f_code.co_filename, tb.tb_lineno])
            tb = tb.tb_next
        payload = {
            'type': type(exc).__name__,
            'code': getattr(exc, 'code', None),
            'message': str(exc), 'locations': locations,
            'seen': seen,
            'warnings': [
                [w.category.__name__, str(w.message), w.filename, w.lineno]
                for w in records
            ],
        }
    else:
        payload = {
            'type': 'success', 'code': None, 'seen': seen,
            'message': '', 'locations': [],
            'warnings': [
                [w.category.__name__, str(w.message), w.filename, w.lineno]
                for w in records
            ],
        }
print(json.dumps(payload))
"""
)


@pytest.mark.parametrize(
    "mode,error,code",
    [
        ("linalg", "SimreconError", "phase_solver_failure"),
        ("nonfinite", "SimreconError", "phase_solver_failure"),
        ("memory", "MemoryError", None),
        ("programming", "RuntimeError", None),
    ],
)
def test_v18_v26_numerical_operation_failure_boundary(
    mode: str, error: str, code: str | None
) -> None:
    env = os.environ.copy()
    completed = subprocess.run(
        [sys.executable, "-c", FAULT_SCRIPT, mode],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, (
        "source-free dependency observer subprocess failed; inspect only sanitized diagnostics"
    )
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, TypeError):
        pytest.fail("source-free dependency observer returned invalid JSON; raw output withheld")
    if payload["type"] == "TypeError" and not payload["seen"]:
        pytest.fail(
            "public entry TypeError before dependency stimulus; numerical boundary unobserved"
        )
    if not payload["seen"]:
        pytest.fail("UNRESOLVED: public numerical-dependency stimulus was not reached")
    assert payload["type"] == error and payload["code"] == code
    assert not any(item[0] == "RuntimeWarning" for item in payload["warnings"])


def test_v19_genuine_final_range_failure() -> None:
    # Invertible, far from rank cutoff. Unit observations produce |dc|>100;
    # scale by max/4 gives true returned lane >25*max, far outside edge band.
    p = np.array([-0.1, 0.0, 0.1])
    unit = [F(1), F(-1), F(1)]
    fit = RationalFit.from_phases(p)
    star = fit.expected(unit)
    assert abs(star[0]) > 100
    bound = fit.forward_bound(unit, star)
    assert bound is not None and bound < 1
    images = (np.array([1.0, -1.0, 1.0]) * (np.finfo(np.float64).max / 4))[:, None, None]
    domain(images, p, "unrepresentable_phase_components")


@pytest.mark.parametrize(
    "kind",
    [
        "large_constant",
        "internal_double_overflow",
        "complex_magnitude_overflow",
        "subnormal",
        "min_subnormal",
    ],
)
def test_v20_safe_returned_lanes_and_subnormal(kind: str) -> None:
    maxval = np.finfo(np.float64).max
    if kind == "large_constant":
        p = phases()
        images = np.full((7, 1, 1), maxval / 2)
    elif kind == "internal_double_overflow":
        # Three +/- quadrature-like samples. cos lane B exceeds max but
        # returned Re(c1)=B/2 is ~0.75*max; all inputs are <=0.75*max.
        p = np.array([0.0, np.pi / 2, -np.pi / 2])
        images = (np.array([1.0, -1.0, -1.0]) * (0.75 * maxval))[:, None, None]
    elif kind == "complex_magnitude_overflow":
        # Both returned harmonic lanes are .75*max, so |c1| exceeds max.
        # These identifiable first-quadrant samples keep each input finite.
        p = np.array([0.55, 0.78, 1.03])
        h = represented_h(p)
        unit = 1.5 * h[:, 1] - 1.5 * h[:, 2]
        assert np.max(np.abs(unit)) < 0.8
        images = (unit * maxval)[:, None, None]
    else:
        p = phases()
        q = np.finfo(np.float64).smallest_subnormal
        images = (
            np.array([1, -2, 3, 5, -4, 6, -7], dtype=np.float64)
            * (q if kind == "min_subnormal" else 2.0**-1060)
        )[:, None, None]
    fit = RationalFit.from_phases(p)
    b = [rational(v) for v in images[:, 0, 0]]
    star = fit.expected(b)
    bound = fit.forward_bound(b, star)
    assert bound is not None
    assert max(abs(v) for v in star) + bound < rational(maxval)
    if kind == "internal_double_overflow":
        assert 2 * abs(star[1]) > rational(maxval)
    if kind == "complex_magnitude_overflow":
        assert star[1] ** 2 + star[2] ** 2 > rational(maxval) ** 2
    accurate(images, p)


@pytest.mark.parametrize("shape", [(1, 1), (1, 5), (4, 1), (3, 7)])
def test_v21_output_representation_singleton_nonsquare(shape: tuple[int, int]) -> None:
    accurate(observations(shape=shape)[:, ::-1, ::-1], phases())


def test_v22_mutable_independent_outputs() -> None:
    images, p = observations(), phases()
    before = snapshot(images), snapshot(p)
    first = accurate(images, p)
    second = accurate(images, p)
    dc2, c2, first_c = second.dc.copy(), second.c1.copy(), first.c1.copy()
    first.dc[:] = -123.0
    np.testing.assert_array_equal(first.c1, first_c)
    first.c1[:] = 77 + 23j
    np.testing.assert_array_equal(second.dc, dc2)
    np.testing.assert_array_equal(second.c1, c2)
    assert (snapshot(images), snapshot(p)) == before


def test_v23_readonly_strided_success_and_rejection_preserve_storage() -> None:
    images = observations()[:, ::-1, ::-1]
    p = phases()[::-1]
    images.flags.writeable = p.flags.writeable = False
    accurate(images, p)
    bad = p.copy()
    bad[0] = np.inf
    bad.flags.writeable = False
    domain(images, bad, "nonfinite_phase_angles")


def test_v24_record_direct_construction_is_not_validation_api() -> None:
    dc, c1 = np.zeros((2, 3), dtype=np.int8), np.ones((1, 4), dtype=np.float32)
    record = PhaseComponents(dc=dc, c1=c1)  # type: ignore[arg-type]
    assert record.dc is dc and record.c1 is c1
    record.dc[0, 0] = 7
    record.c1[0, 0] = 8
    assert dc[0, 0] == 7 and c1[0, 0] == 8


@pytest.mark.parametrize(
    "binding", ["missing", "positional", "extra", "old_offset", "missing_images"]
)
def test_v25_required_keyword_only_signature(binding: str) -> None:
    images, p = observations(), phases()
    with pytest.raises(TypeError):
        if binding == "missing":
            separate(images)
        elif binding == "positional":
            separate(images, p)
        elif binding == "extra":
            separate(images, phases_rad=p, surprise=1)
        elif binding == "old_offset":
            separate(images, phases_rad=p, phase_offset_rad=0.0)
        else:
            separate(phases_rad=p)


def test_v27_public_mrc_exports_preserved_complete_suite_required() -> None:
    # Minimal public boundary observation; full preservation remains a later
    # full-local gate dependency on the untouched MRC suite, not duplicated here.
    from simrecon import DataBlock, DatasetInfo, WriteReport, harmonize, inspect, read, write

    assert all(
        callable(v) for v in (inspect, harmonize, read, write, DatasetInfo, DataBlock, WriteReport)
    )
    assert issubclass(SimreconError, ValueError)


def test_v28_reviewed_numeric_fixture_all_input_residuals() -> None:
    fixture = analytic_fixture()
    assert fixture.images.shape == (7, 9, 14)
    assert np.min(fixture.images) < 0
    assert fixture.expected_residuals.shape == fixture.images.shape
    assert np.ptp(np.diff(fixture.phases_rad)) > 0.1
    assert np.linalg.cond(fixture.h) < 3
    result = accurate(fixture.images, fixture.phases_rad)
    assert result.dc.shape == fixture.expected_dc.shape
    # Actual residual arrays are available to C through these public values.
    fitted = (
        result.dc[None]
        + 2 * result.c1.real[None] * fixture.h[:, 1, None, None]
        - 2 * result.c1.imag[None] * fixture.h[:, 2, None, None]
    )
    assert fitted.shape == fixture.expected_residuals.shape
    assert np.isfinite(fitted).all()


@pytest.mark.parametrize("mode", ["warn", "raise"])
@pytest.mark.parametrize(
    "case", ["valid", "subnormal", "range", "image_overflow", "phase_overflow"]
)
def test_v29_error_mode_and_no_arithmetic_warning(
    mode: Literal["warn", "raise"], case: str
) -> None:
    p, images = phases(), observations()
    code: str | None = None
    if case == "subnormal":
        images = np.full((7, 1, 1), np.finfo(np.float64).smallest_subnormal)
    elif case == "range":
        p = np.array([-0.1, 0.0, 0.1])
        images = (np.array([1.0, -1.0, 1.0]) * (np.finfo(np.float64).max / 4))[:, None, None]
        code = "unrepresentable_phase_components"
    elif case in ("image_overflow", "phase_overflow") and np.finfo(
        np.longdouble
    ).max > np.longdouble(np.finfo(np.float64).max):
        high = np.longdouble(np.finfo(np.float64).max) * np.longdouble(2)
        if case == "image_overflow":
            images = images.astype(np.longdouble)
            images[0, 0, 0] = high
            code = "nonfinite_phase_images"
        else:
            p = p.astype(np.longdouble)
            p[0] = high
            code = "nonfinite_phase_angles"
        # A same-width platform exercises a valid counterpart without a skip.
    prior = np.geterr()
    try:
        np.seterr(all=mode)
        selected = np.geterr()
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter("always")
            if code is None:
                accurate(images, p)
            else:
                domain(images, p, code)
        assert not any(issubclass(record.category, RuntimeWarning) for record in records)
        assert np.geterr() == selected
    finally:
        np.seterr(**prior)
    assert np.geterr() == prior


def test_oracle_exact_quantization_and_full_rank_certificates() -> None:
    # Supporting observer check: genuine permitted RHS and matrix perturbations,
    # including a near-cutoff regime where a small-norm argument cannot certify
    # rank. Exact Gram determinant must establish it there.
    assert Q_HALF != 0 and F(1, 2**1074) == 2 * Q_HALF
    for p in (phases(), np.array([-2e-7, 0.0, 2e-7])):
        fit = RationalFit.from_phases(p)
        b = [F(i - 2) for i in range(p.size)]
        star = fit.expected(b)
        rounded = [rational(float(v)) for v in star]
        fit.certify(b, rounded)
        eta = 128 * max(p.size, 3) * EPS
        changed = [[x * (1 + eta / 16) for x in row] for row in fit.k]
        assert positive_definite(gram(changed))
        alternate = RationalFit.from_k(changed).expected(b)
        fit.certify(b, [rational(float(v)) for v in alternate])
    # Nonzero E near the rank cutoff: the allowed norm bound itself cannot
    # guarantee rank. The exact Gram certificate must prove K+E full rank.
    p = np.array([-2e-7, 0.0, 2e-7])
    fit = RationalFit.from_phases(p)
    eta = 128 * 3 * EPS
    assert eta**2 * fit.a2_low > norm2(mv(fit.k, [F(-2), F(1), F(0)])) / 5
    e = [[eta * F(1 if i != 1 else -1, 32), F(0), F(0)] for i in range(3)]
    assert sum((norm2(row) for row in e), F(0)) < eta**2 * fit.a2_low
    changed = [
        [x + y for x, y in zip(row, erow, strict=True)] for row, erow in zip(fit.k, e, strict=True)
    ]
    assert positive_definite(gram(changed))
    alt = RationalFit.from_k(changed).expected([F(-1), F(2), F(4)])
    assert fit.certify([F(-1), F(2), F(4)], [rational(float(v)) for v in alt]) != "rhs-only"
    tiny_b = [F(1, 2**1074)] * 7
    fit = RationalFit.from_phases(phases())
    assert fit.certify(tiny_b, [F(1, 2**1074), F(0), F(0)]) == "rhs-only"
    # A halfway-subnormal final coordinate is allowed exactly, not rounded q/2=0.
    half_b = [Q_HALF] * 7
    assert fit.certify(half_b, [F(0), F(0), F(0)]) == "rhs-only"


@pytest.mark.parametrize("wrong", ["sign", "gain", "mean", "axis"])
def test_oracle_distinguishes_plausible_wrong_answers(wrong: str) -> None:
    p = phases()
    fit = RationalFit.from_phases(p)
    b = [F(v) for v in (-6, 0, 6, -1, 5, -2, 4)]
    star = fit.expected(b)
    altered = star.copy()
    if wrong == "sign":
        altered[2] *= -1
    elif wrong == "gain":
        altered[1] *= 2
    elif wrong == "mean":
        altered[0] = sum(b, F(0)) / len(b)
    else:
        altered[0], altered[1] = altered[1], altered[0]
    with pytest.raises(AssertionError, match="necessary finite forward"):
        fit.certify(b, altered)


def test_oracle_off_model_rotation_alternative() -> None:
    # Challenge against a legitimate column-space rotation, not just f-only or
    # a forward agreement test. This fit need not keep the original residual.
    fit = RationalFit.from_phases(np.array([-0.003, -0.001, 0, 0.002, 0.004]))
    b = [F(v) for v in (3, -7, 2, 9, -4)]
    eta = 128 * 5 * EPS
    e = [[eta * F(i - 2, 32), F(0), eta * F((i % 2) * 2 - 1, 32)] for i in range(5)]
    assert sum((norm2(row) for row in e), F(0)) < eta**2 * fit.a2_low
    changed = [
        [x + y for x, y in zip(row, erow, strict=True)] for row, erow in zip(fit.k, e, strict=True)
    ]
    alternate_fit = RationalFit.from_k(changed)
    alt = alternate_fit.expected(b)
    returned = [rational(float(v)) for v in alt]
    fit.certify(b, returned)
    residual = alternate_fit.residual(b, alt)
    assert dot(residual, mv(changed, alt)) == 0
    assert sqrt_interval(norm2(residual))[0] > 0
    # Harder legitimate alternative: start with b in col(K)^perp, z_star=0,
    # then rotate the nearly dependent columns by a permitted nonzero E.
    # A RHS-only or column-space certificate is inadequate for this example;
    # a residual-direction perturbation must retain exact full rank.
    fit = RationalFit.from_phases(np.array([-0.002, -0.001, 0, 0.001, 0.002]))
    b = fit.residual(b, fit.expected(b))
    assert fit.expected(b) == [F(0)] * 3
    e = [[r * eta * F(v, 32) for v in (-2, 1, 0)] for r in b]
    assert sum((norm2(row) for row in e), F(0)) < eta**2 * fit.a2_low
    changed = [
        [x + y for x, y in zip(row, erow, strict=True)] for row, erow in zip(fit.k, e, strict=True)
    ]
    assert positive_definite(gram(changed))
    alt = RationalFit.from_k(changed).expected(b)
    assert fit.certify(b, [rational(float(v)) for v in alt]) == "residual-projection"


def test_fixture_stored_oracle_not_unrounded_generating_signal() -> None:
    fixture = analytic_fixture((2, 3))
    dc, c1, residuals = expected_arrays(fixture.images, fixture.phases_rad)
    np.testing.assert_array_equal(dc, fixture.expected_dc)
    np.testing.assert_array_equal(c1, fixture.expected_c1)
    np.testing.assert_array_equal(residuals, fixture.expected_residuals)
    fit = RationalFit.from_phases(fixture.phases_rad)
    b = [rational(v) for v in fixture.images[:, 0, 0]]
    assert mv(transpose(fit.k), fit.residual(b, fit.expected(b))) == [F(0)] * 3


def test_subprocess_observer_portable_source_free() -> None:
    # -I ignores PYTHONPATH, so no temporary harness can supply these renderers.
    # The subprocess still inherits the required environment for blind work.
    script = (
        SOURCE_FREE_SCRIPT
        + r"""
assert sys.flags.isolated
warnings.warn("portable observer probe", RuntimeWarning)
raise ValueError("portable observer probe")
"""
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    lines = completed.stderr.splitlines()
    assert len(lines) == 3, "observer must emit only warning, location and exception"
    assert lines[0].startswith("<string>:")
    assert lines[0].endswith("RuntimeWarning: portable observer probe")
    assert lines[1].startswith("  <string>:") and lines[1].endswith(": <module>")
    assert lines[2] == "ValueError: portable observer probe"
    # Validate the nonfinite stimulus itself without any product import/solve.
    # The original dependency call supplies only return type/shape information,
    # never an expected phase coefficient. Keep legitimate tuple records intact.
    dependency_probe = (
        FAULT_SCRIPT.split("for module, prefix in", 1)[0]
        + r"""
matrix = np.eye(3)
rhs = np.ones(3)
for module in (np.linalg, sla):
    for name, args in (
        ('svd', (matrix,)), ('lstsq', (matrix, rhs)), ('pinv', (matrix,)),
    ):
        original = getattr(module, name)
        before = original(*args)
        after = wrapper(original, name)(*args)
        assert type(before) is type(after)
        if isinstance(before, tuple):
            for old, new in zip(before, after, strict=True):
                if isinstance(old, np.ndarray):
                    assert old.shape == new.shape and old.dtype == new.dtype
                    assert np.isnan(new).all()
        else:
            assert before.shape == after.shape and before.dtype == after.dtype
            assert np.isnan(after).all()
"""
    )
    proof = subprocess.run(
        [sys.executable, "-I", "-c", dependency_probe, "nonfinite"],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proof.returncode == 0, "source-free dependency return-form portability proof failed"
    assert proof.stdout == proof.stderr == ""
