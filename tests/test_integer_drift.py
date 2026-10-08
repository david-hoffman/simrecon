"""INTEGER-DRIFT-01 blind public-contract tests (D01--D12)."""

import builtins
import json
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pytest
from numpy.typing import NDArray

import simrecon
from integer_drift_fixture import (
    CIRCULAR_BUDGET,
    EPS,
    acquire,
    circular_errors,
    doubled_truth,
    expected_components,
    indexed_images,
    kernel,
    phasors,
    represented_phasors,
)


@pytest.fixture
def correct() -> Callable[..., Any]:
    operation = getattr(simrecon, "correct_integer_drift", None)
    assert callable(operation), "D01: missing public correct_integer_drift API"
    return operation


def inputs(n: int = 4, ny: int = 3, nx: int = 4) -> dict[str, NDArray]:
    return {
        "images": np.arange(n * ny * nx, dtype=np.float64).reshape(n, ny, nx) - 17,
        "phases_rad": np.linspace(-0.7, 4.1, n),
        "carrier_bins_yx": np.array([1, -2], dtype=np.int64),
        "displacements_pixels_yx": np.array([(p - 2, 3 - p) for p in range(n)], dtype=np.int64),
    }


def assert_prepared(result: Any, args: dict[str, NDArray]) -> None:
    images = args["images"]
    expected_images = indexed_images(images, args["displacements_pixels_yx"])
    np.testing.assert_array_equal(result.images, expected_images)
    np.testing.assert_array_equal(np.signbit(result.images), np.signbit(expected_images))
    phase = result.phases_rad
    assert phase.shape == args["phases_rad"].shape
    assert np.all(np.isfinite(phase))
    assert np.all((-np.pi <= phase) & (phase <= np.pi))
    errors = circular_errors(
        phase,
        args["phases_rad"],
        args["carrier_bins_yx"],
        args["displacements_pixels_yx"],
        images.shape[1:],
    )
    assert all(error <= CIRCULAR_BUDGET for error in errors)
    for array in (result.images, phase):
        assert type(array) is np.ndarray
        assert array.dtype == np.dtype(np.float64) and array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable


def test_exports_record_and_ownership(correct: Callable[..., Any]) -> None:
    """D01/D09: frozen bindings, mutable independent snapshots and repeat calls."""
    record = getattr(simrecon, "DriftCorrection", None)
    assert isinstance(record, type), "missing public DriftCorrection record"
    args = inputs()
    before = {name: value.copy() for name, value in args.items()}
    result, another = correct(**args), correct(**args)
    assert isinstance(result, record)
    assert {
        name
        for name in dir(result)
        if not name.startswith("_") and not callable(getattr(result, name))
    } == {"images", "phases_rad"}
    assert_prepared(result, args)
    for name in ("images", "phases_rad"):
        original = getattr(result, name)
        try:
            setattr(result, name, np.zeros_like(original))
        except MemoryError:
            raise
        except Exception:
            # The contract fixes binding immutability, not its diagnostic type.
            pass
        assert getattr(result, name) is original
    outputs = (result.images, result.phases_rad, another.images, another.phases_rad)
    for i, value in enumerate(outputs):
        for other in (*args.values(), *outputs[i + 1 :]):
            assert not np.shares_memory(value, other)
    result.images.fill(91)
    result.phases_rad.fill(0.123)
    for name in args:
        np.testing.assert_array_equal(args[name], before[name])
    assert_prepared(another, args)
    args["images"].fill(-9)
    args["phases_rad"].fill(-0.4)
    args["carrier_bins_yx"].fill(0)
    args["displacements_pixels_yx"].fill(0)
    np.testing.assert_array_equal(
        another.images, indexed_images(before["images"], before["displacements_pixels_yx"])
    )
    np.testing.assert_array_equal(result.images, np.full(result.images.shape, 91.0))
    np.testing.assert_array_equal(result.phases_rad, np.full(result.phases_rad.shape, 0.123))


@pytest.mark.parametrize(
    "call",
    [
        "missing-all",
        "missing-phases",
        "missing-carrier",
        "missing-shifts",
        "positional-keywords",
        "unknown-keyword",
    ],
)
def test_binding(correct: Callable[..., Any], call: str) -> None:
    """D01: ordinary Python binding errors, without default metadata."""
    args = inputs()
    with pytest.raises(TypeError):
        if call == "missing-all":
            correct()
        elif call == "positional-keywords":
            correct(*args.values())
        elif call == "unknown-keyword":
            correct(**args, phase_offset_rad=0)
        else:
            name = {
                "missing-phases": "phases_rad",
                "missing-carrier": "carrier_bins_yx",
                "missing-shifts": "displacements_pixels_yx",
            }[call]
            del args[name]
            correct(**args)


REAL_DTYPES = [
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
    np.float16,
    np.float32,
    np.float64,
    np.longdouble,
]


@pytest.mark.parametrize("dtype", REAL_DTYPES)
@pytest.mark.parametrize("byteorder", ["<", ">"])
def test_all_real_widths_and_endians(
    correct: Callable[..., Any], dtype: Any, byteorder: Literal["<", ">"]
) -> None:
    """D02/D03: converted values define the operation; no width whitelist."""
    args = inputs()
    dt = np.dtype(dtype).newbyteorder(byteorder)
    values = np.arange(48).reshape(4, 3, 4)
    if dt.kind != "u":
        values = values - 21
    args["images"] = values.astype(dt)
    args["phases_rad"] = np.array([0, 1, 7, 31], dtype=dt)
    assert_prepared(correct(**args), args)


@pytest.mark.parametrize(
    "dtype", [np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64]
)
@pytest.mark.parametrize("byteorder", ["<", ">"])
def test_all_integer_metadata_widths(
    correct: Callable[..., Any], dtype: Any, byteorder: Literal["<", ">"]
) -> None:
    """D04/D05: unsigned and signed widths, nonnative byte order."""
    args = inputs()
    dt = np.dtype(dtype).newbyteorder(byteorder)
    args["carrier_bins_yx"] = np.array([13, 17], dtype=dt)
    args["displacements_pixels_yx"] = np.array([[0, 1], [7, 19], [3, 4], [9, 0]], dtype=dt)
    assert_prepared(correct(**args), args)


@pytest.mark.parametrize("layout", ["fortran", "negative-stride", "strided", "readonly"])
def test_storage_layouts_all_inputs(correct: Callable[..., Any], layout: str) -> None:
    """D02--D05/D09: snapshot noncontiguous and immutable caller storage."""
    args = inputs()
    for name, value in args.items():
        if layout == "fortran":
            args[name] = np.asfortranarray(value)
        elif layout == "negative-stride":
            args[name] = value[(slice(None, None, -1),) * value.ndim]
        elif layout == "strided":
            backing = np.empty(tuple(2 * n for n in value.shape), dtype=value.dtype)
            view = backing[(slice(None, None, 2),) * value.ndim]
            view[...] = value
            args[name] = view
        else:
            value.flags.writeable = False
    before = {name: value.copy() for name, value in args.items()}
    writeable = {name: value.flags.writeable for name, value in args.items()}
    assert_prepared(correct(**args), args)
    for name in args:
        np.testing.assert_array_equal(args[name], before[name])
        assert args[name].flags.writeable == writeable[name]


def test_overlapping_caller_inputs(correct: Callable[..., Any]) -> None:
    """D09: callers may share storage among separate input arguments."""
    shared_real = np.arange(48, dtype=np.float64)
    shared_integer = np.arange(8, dtype=np.int64)
    args = {
        "images": shared_real.reshape(4, 3, 4),
        "phases_rad": shared_real[::12],
        "carrier_bins_yx": shared_integer[:2],
        "displacements_pixels_yx": shared_integer.reshape(4, 2),
    }
    before = {name: value.copy() for name, value in args.items()}
    assert_prepared(correct(**args), before)
    for name in args:
        np.testing.assert_array_equal(args[name], before[name])


@pytest.mark.parametrize("shape", [(1, 1), (1, 6), (5, 1), (3, 4), (4, 5), (5, 7)])
def test_exact_all_pixel_permutation(correct: Callable[..., Any], shape: tuple[int, int]) -> None:
    """D06: nonsquare odd/even/singleton axes, signs and periodic wrap."""
    args = inputs(5, *shape)
    args["displacements_pixels_yx"] = np.array([[0, 0], [1, -2], [-2, 1], [17, -23], [-19, -31]])
    assert_prepared(correct(**args), args)


@pytest.mark.parametrize("unsigned", [False, True])
def test_integer_extrema_exact_and_analytic(correct: Callable[..., Any], unsigned: bool) -> None:
    """D04--D07: extrema cannot pass through float64 or fixed-width products."""
    if unsigned:
        args = inputs(1, 4, 8)
        args["carrier_bins_yx"] = np.array([2**64 - 1, 2**64 - 2], dtype=np.uint64)
        args["displacements_pixels_yx"] = np.array([[2**64 - 1, 2**64 - 2]], dtype=np.uint64)
        expected = -1j  # 9/4 + 36/8 = 27/4 turns -> 3/4 turn.
    else:
        args = inputs(1, 3, 4)
        args["carrier_bins_yx"] = np.array([-(2**63), 2**63 - 1], dtype=np.int64)
        args["displacements_pixels_yx"] = np.array([[-(2**63), 2**63 - 1]], dtype=np.int64)
        expected = complex(-np.sqrt(3) / 2, -0.5)  # 1/3 + 1/4 = 7/12 turn.
    args["phases_rad"] = np.zeros(1)
    # Ideal roots validate the observer, not product accuracy. The contract's
    # represented trigonometric target differs slightly from an ideal root.
    reference = represented_phasors(
        args["phases_rad"],
        args["carrier_bins_yx"],
        args["displacements_pixels_yx"],
        args["images"].shape[1:],
    )
    np.testing.assert_allclose(reference, [expected], atol=8 * EPS, rtol=0)
    result = correct(**args)
    assert_prepared(result, args)


@pytest.mark.parametrize(
    "carrier_dtype,shift_dtype", [(np.int64, np.uint64), (np.uint64, np.int64)]
)
def test_mixed_integer_domains_and_aliases(
    correct: Callable[..., Any], carrier_dtype: Any, shift_dtype: Any
) -> None:
    """D04/D05: independent domains and simultaneous carrier/shift aliases."""
    args = inputs(3, 3, 4)
    args["carrier_bins_yx"] = np.array([2**63 - 1, 2**63 - 2], dtype=carrier_dtype)
    values = [[2**63 - 1, 2**63 - 2], [0, 2**63 - 3], [2, 1]]
    if np.dtype(shift_dtype).kind == "i":
        values[0][0], values[1][1] = -(2**63), -7
    args["displacements_pixels_yx"] = np.array(values, dtype=shift_dtype)
    result = correct(**args)
    assert_prepared(result, args)
    alias = {name: value.copy() for name, value in args.items()}
    alias["carrier_bins_yx"] = np.array(
        [int(args["carrier_bins_yx"][0]) % 3 - 9, int(args["carrier_bins_yx"][1]) % 4 + 16]
    )
    alias["displacements_pixels_yx"] = np.array(
        [[int(y) % 3 + 15, int(x) % 4 - 20] for y, x in args["displacements_pixels_yx"]]
    )
    equivalent = correct(**alias)
    np.testing.assert_array_equal(result.images, equivalent.images)
    assert np.all(
        np.abs(phasors(result.phases_rad) - phasors(equivalent.phases_rad)) <= 2 * CIRCULAR_BUDGET
    )


def test_analytic_rational_cycles_and_positive_sign(correct: Callable[..., Any]) -> None:
    """D07: distinct analytic roots, not just repeating modular arithmetic."""
    args = inputs(7, 4, 6)
    args["phases_rad"] = np.zeros(7)
    args["carrier_bins_yx"] = np.array([1, 1])
    args["displacements_pixels_yx"] = np.array(
        [[1, 0], [0, 1], [-1, 0], [-1, 3], [4, -6], [2, 0], [0, -1]]
    )
    expected = np.array([1j, 0.5 + np.sqrt(3) / 2 * 1j, -1j, 1j, 1, -1, 0.5 - np.sqrt(3) / 2 * 1j])
    # Confine ideal-root comparisons to observer sanity. Returned phases are
    # judged solely against the unchanged strict represented-input target.
    reference = represented_phasors(
        args["phases_rad"],
        args["carrier_bins_yx"],
        args["displacements_pixels_yx"],
        args["images"].shape[1:],
    )
    np.testing.assert_allclose(reference, expected, atol=8 * EPS, rtol=0)
    result = correct(**args)
    assert_prepared(result, args)


def test_huge_phases_and_branch_cut(correct: Callable[..., Any]) -> None:
    """D03/D07: evaluate represented trig before adding phase increment."""
    phases = np.array(
        [
            np.finfo(float).max,
            -np.finfo(float).max,
            1e200,
            -1e200,
            2.0**80,
            -(2.0**80),
            np.pi,
            -np.pi,
            np.nextafter(np.pi, 0),
            np.nextafter(-np.pi, -np.inf),
        ]
    )
    args = inputs(len(phases), 4, 6)
    args["phases_rad"] = phases
    args["displacements_pixels_yx"] = np.array(
        [[1, 1], [-1, 0], [0, 1], [1, -1], [2, 0], [-2, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
    )
    assert_prepared(correct(**args), args)


def test_zero_carrier_retains_direct_phase_meaning(correct: Callable[..., Any]) -> None:
    """D04/D07: zero illumination carrier still aligns translated pixels."""
    args = inputs()
    args["carrier_bins_yx"] = np.zeros(2, dtype=np.uint8)
    args["phases_rad"] = np.array([1e200, -np.finfo(float).max, np.pi, -np.pi])
    result = correct(**args)
    assert_prepared(result, args)
    assert np.all(
        np.abs(phasors(result.phases_rad) - phasors(args["phases_rad"])) <= CIRCULAR_BUDGET
    )


def test_float_conversion_rounding_underflow_and_extremes(correct: Callable[..., Any]) -> None:
    """D02/D03: no intensity cap; converted finite values are the problem."""
    args = inputs(4, 1, 2)
    maximum, q = np.finfo(float).max, np.nextafter(0.0, 1.0)
    args["images"] = np.array([[[maximum, -maximum]], [[q, -q]], [[-0.0, 0.0]], [[1, -1]]])
    assert_prepared(correct(**args), args)
    for name in ("images", "phases_rad"):
        for dtype in (np.int64, np.uint64):
            modified = {key: value.copy() for key, value in args.items()}
            modified[name] = np.full(args[name].shape, np.iinfo(dtype).max, dtype=dtype)
            assert_prepared(correct(**modified), modified)
    args = inputs(1, 1, 2)
    args["images"] = np.array(
        [[[np.longdouble(1) / 3, np.finfo(np.longdouble).smallest_subnormal]]], dtype=np.longdouble
    )
    args["phases_rad"] = np.array(
        [-np.finfo(np.longdouble).smallest_subnormal], dtype=np.longdouble
    )
    with np.errstate(all="ignore"):
        assert_prepared(correct(**args), args)


@pytest.mark.parametrize("case", ["n1", "repeated", "corrected-degenerate"])
def test_no_hidden_rank_or_frame_minimum(correct: Callable[..., Any], case: str) -> None:
    """D08/D11: preparation accepts rank loss; separation owns rank rejection."""
    args = inputs(1 if case == "n1" else 4, 1, 4)
    if case == "repeated":
        args["phases_rad"] = np.full(4, 0.3)
        args["displacements_pixels_yx"] = np.zeros((4, 2), dtype=int)
    elif case == "corrected-degenerate":
        args["carrier_bins_yx"] = np.array([0, 1])
        args["phases_rad"] = np.arange(4) * np.pi / 2
        args["displacements_pixels_yx"] = np.array([[0, -p] for p in range(4)])
        # Original supplied phases are identifiable through the actual API.
        simrecon.separate_phases(args["images"], phases_rad=args["phases_rad"])
    result = correct(**args)
    assert_prepared(result, args)
    if case != "n1":
        with pytest.raises(simrecon.SimreconError) as exc:
            simrecon.separate_phases(result.images, phases_rad=result.phases_rad)
        assert exc.value.code == "rank_deficient_phases"


class ArraySubclass(np.ndarray):
    """Explicitly outside plain-ndarray public domain."""


def invalid_arrays(shape: tuple[int, ...]) -> list[Any]:
    base = np.ones(shape)
    return [
        None,
        1,
        base.tolist(),
        base.view(ArraySubclass),
        np.ma.array(base),
        np.ones(shape, dtype=bool),
        np.ones(shape, dtype=complex),
        np.full(shape, "1"),
        np.full(shape, b"1"),
        np.ones(shape, dtype=object),
        np.zeros(shape, dtype=[("value", "f8")]),
        np.zeros(shape, dtype="datetime64[D]"),
        np.zeros(shape, dtype="timedelta64[D]"),
    ]


BAD_CASES: list[tuple[str, Any, str]] = []
for _name, _shape, _code in [
    ("images", (4, 3, 4), "invalid_drift_images"),
    ("phases_rad", (4,), "invalid_drift_phases"),
    ("carrier_bins_yx", (2,), "invalid_drift_carrier"),
    ("displacements_pixels_yx", (4, 2), "invalid_drift_displacements"),
]:
    BAD_CASES.extend((_name, _value, _code) for _value in invalid_arrays(_shape))
    if _name in {"carrier_bins_yx", "displacements_pixels_yx"}:
        BAD_CASES.append((_name, np.ones(_shape, dtype=float), _code))
        BAD_CASES.append((_name, np.ones(_shape, dtype=np.longdouble), _code))
for _shape in [(), (4,), (3, 4), (1, 4, 3, 4), (0, 3, 4), (4, 0, 4), (4, 3, 0)]:
    BAD_CASES.append(("images", np.zeros(_shape), "invalid_drift_images"))
for _shape in [(), (0,), (3,), (5,), (4, 1), (1, 4)]:
    BAD_CASES.append(("phases_rad", np.zeros(_shape), "invalid_drift_phases"))
for _shape in [(), (0,), (1,), (3,), (1, 2), (2, 1)]:
    BAD_CASES.append(("carrier_bins_yx", np.zeros(_shape, dtype=int), "invalid_drift_carrier"))
for _shape in [(), (2,), (0, 2), (3, 2), (5, 2), (4, 1), (4, 3), (4, 2, 1)]:
    BAD_CASES.append(
        ("displacements_pixels_yx", np.zeros(_shape, dtype=int), "invalid_drift_displacements")
    )
for _name, _shape, _code in [
    ("images", (4, 3, 4), "invalid_drift_images"),
    ("phases_rad", (4,), "invalid_drift_phases"),
]:
    for _nonfinite in [np.nan, np.inf, -np.inf]:
        _value = np.zeros(_shape)
        _value.flat[-1] = _nonfinite
        BAD_CASES.append((_name, _value, _code))


@pytest.mark.parametrize(
    "name,value,code", BAD_CASES, ids=[f"{name}-{i}" for i, (name, _, _) in enumerate(BAD_CASES)]
)
def test_invalid_inputs_preserve_storage(
    correct: Callable[..., Any], name: str, value: Any, code: str
) -> None:
    """D02--D05/D09: single-invalid obligations; prose/precedence unconstrained."""
    args: dict[str, Any] = inputs()
    args[name] = value
    arrays = [v for v in args.values() if isinstance(v, np.ndarray)]
    snapshots = [v.copy() for v in arrays]
    with pytest.raises(simrecon.SimreconError) as exc:
        correct(**args)
    assert exc.value.code == code
    assert isinstance(exc.value, ValueError)
    for array, before in zip(arrays, snapshots, strict=True):
        np.testing.assert_array_equal(array, before)


def test_wider_finite_conversion_overflow(correct: Callable[..., Any]) -> None:
    """D02/D03: capability-dependent wider overflow, never a fabricated float."""
    if np.finfo(np.longdouble).max > np.longdouble(np.finfo(float).max):
        overflow = np.longdouble(np.finfo(float).max) * np.longdouble(2)
        assert np.isfinite(overflow)
        for name, code in (
            ("images", "invalid_drift_images"),
            ("phases_rad", "invalid_drift_phases"),
        ):
            args = inputs()
            args[name] = np.full(args[name].shape, overflow, dtype=np.longdouble)
            before = args[name].copy()
            with warnings.catch_warnings(record=True) as seen, np.errstate(all="raise"):
                warnings.simplefilter("always")
                with pytest.raises(simrecon.SimreconError) as exc:
                    correct(**args)
            assert exc.value.code == code
            assert not any(issubclass(w.category, RuntimeWarning) for w in seen)
            np.testing.assert_array_equal(args[name], before)
    else:
        # Equal-width longdouble is a permitted positive, not a skipped test.
        args = inputs()
        args["images"] = np.full(args["images"].shape, np.finfo(float).max, dtype=np.longdouble)
        args["phases_rad"] = np.full(4, np.finfo(float).max, dtype=np.longdouble)
        assert_prepared(correct(**args), args)


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_numpy_error_modes_and_handled_warnings(
    correct: Callable[..., Any], mode: Literal["ignore", "warn", "raise", "call", "print", "log"]
) -> None:
    """D09: operation-scoped handling must leave all caller error policy intact."""

    class Log:
        def write(self, message: str) -> None:
            raise AssertionError(f"unexpected handled arithmetic log: {message}")

    def callback(error: str, flag: int) -> None:
        raise AssertionError(f"unexpected handled arithmetic callback: {error}, {flag}")

    previous = np.geterrcall()
    target: Any = Log() if mode == "log" else callback
    np.seterrcall(target)
    try:
        with np.errstate(all=mode), warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always")
            original = np.geterr().copy()
            args = inputs()
            args["phases_rad"] = np.array([np.finfo(float).max, -np.finfo(float).max, 0, 1e200])
            args["images"].flat[0] = np.finfo(float).max
            correct(**args)
            underflow = inputs()
            underflow["images"] = np.full(
                underflow["images"].shape,
                np.finfo(np.longdouble).smallest_subnormal,
                dtype=np.longdouble,
            )
            underflow["phases_rad"] = np.full(
                4, -np.finfo(np.longdouble).smallest_subnormal, dtype=np.longdouble
            )
            correct(**underflow)
            if np.finfo(np.longdouble).max > np.longdouble(np.finfo(float).max):
                overflow = inputs()
                overflow["images"] = np.full(
                    overflow["images"].shape,
                    np.longdouble(np.finfo(float).max) * np.longdouble(2),
                    dtype=np.longdouble,
                )
                with pytest.raises(simrecon.SimreconError) as conversion_exc:
                    correct(**overflow)
                assert conversion_exc.value.code == "invalid_drift_images"
            args["images"].flat[0] = np.inf
            with pytest.raises(simrecon.SimreconError) as exc:
                correct(**args)
            assert exc.value.code == "invalid_drift_images"
            assert np.geterr() == original
            assert np.geterrcall() is target
            assert not any(issubclass(w.category, RuntimeWarning) for w in seen)
    finally:
        np.seterrcall(previous)


@pytest.mark.parametrize("shape,carrier", [((5, 6), (1, -1)), ((4, 5), (-1, 1))])
def test_specimen_before_illumination_identity_and_separation(
    correct: Callable[..., Any], shape: tuple[int, int], carrier: tuple[int, int]
) -> None:
    """D10/D11: asymmetric finite convolution, independent known object."""
    phases = np.array([0.0, 0.7, 2.0, 3.4, 5.2])
    shifts = np.array([[0, 0], [1, -2], [-1, 1], [2, 3], [-3, -2]])
    k = np.array(carrier)
    raw = acquire(shape, phases, k, shifts)
    result = correct(raw, phases_rad=phases, carrier_bins_yx=k, displacements_pixels_yx=shifts)
    dc, c1 = expected_components(shape, k, 1.25, 0.6)
    expected = dc[None] + 2 * (c1[None] * phasors(result.phases_rad)[:, None, None]).real
    scale = float(np.max(np.abs(raw)))
    # Circular budget enters the physical model linearly. 128*eps covers
    # these small finite sums and elementary rounded forward evaluations.
    model_budget = (4 * CIRCULAR_BUDGET + 128 * EPS) * scale
    np.testing.assert_allclose(result.images, expected, atol=model_budget, rtol=0)
    matrix = np.column_stack((np.ones(5), np.cos(result.phases_rad), np.sin(result.phases_rad)))
    singular = np.linalg.svd(matrix, compute_uv=False)
    assert singular[0] / singular[-1] < 10  # Informative existing accuracy regime.
    components = simrecon.separate_phases(result.images, phases_rad=result.phases_rad)
    # Forward consequence with cond(H)<10, stored-observation roundoff and
    # phase budget, with ample margin; units remain input intensity units.
    component_budget = 256 * (CIRCULAR_BUDGET + 128 * 5 * EPS) * scale
    np.testing.assert_allclose(components.dc, dc, atol=component_budget, rtol=0)
    np.testing.assert_allclose(components.c1, c1, atol=component_budget, rtol=0)
    wrong = simrecon.separate_phases(result.images, phases_rad=phases)
    wrong_error = max(float(np.max(np.abs(wrong.dc - dc))), float(np.max(np.abs(wrong.c1 - c1))))
    assert wrong_error > 1000 * component_budget


def test_real_reconstruction_composition(correct: Callable[..., Any]) -> None:
    """D11/D12: two orientations, unequal N>3 phases, units and object truth."""
    shape = (5, 6)
    ny, nx = shape
    phases = np.array([0.0, 0.7, 2.0, 3.4, 5.2])
    shifts = np.array([[0, 0], [1, -2], [-1, 1], [2, 3], [-3, -2]])
    carriers = np.array([[1, 0], [0, 1]])
    brightness, modulation = np.array([1.25, 0.75]), np.array([0.6, 0.8])
    raw, prepared = [], []
    for r, carrier in enumerate(carriers):
        frames = acquire(
            shape,
            phases,
            carrier,
            shifts,
            brightness=float(brightness[r]),
            modulation=float(modulation[r]),
        )
        raw.append(frames)
        prepared.append(
            correct(
                frames, phases_rad=phases, carrier_bins_yx=carrier, displacements_pixels_yx=shifts
            )
        )
    dy, dx = 0.5, 0.25  # micrometres/pixel; waves below are cycles/micrometre.
    otf = simrecon.prepare_otf(
        kernel(shape),
        pixel_size_um=(dy, dx),
        origin_yx=(0, 0),
        source="blind-A finite asymmetric kernel",
    )
    waves = carriers / np.array([ny * dy, nx * dx])
    mask = np.zeros((2 * ny, 2 * nx))
    mask[ny - 1 : ny + 2, nx - 1 : nx + 2] = 1
    args = {
        "otf": otf,
        "wavevectors_per_um": waves,
        "brightness": brightness,
        "modulation": modulation,
        "regularization": 0.0,
        "apodization": mask,
    }
    images = np.array([value.images for value in prepared])
    angles = np.array([value.phases_rad for value in prepared])
    for row in angles:
        matrix = np.column_stack((np.ones(5), np.cos(row), np.sin(row)))
        assert np.linalg.cond(matrix) < 10
    result = simrecon.reconstruct(images, phases_rad=angles, **args)
    truth, spectrum = doubled_truth(shape)
    # R=2,N=5,Mout=120: existing informative reconstruction budget.
    budget = (
        8192
        * 2
        * 5
        * (4 * ny * nx)
        * EPS
        * float(np.max(np.abs(images)))
        / float(np.min(brightness))
    )
    # All masked modes have a DC transfer magnitude >= 3/8, so V>=
    # (0.75*3/8)**2 > 0.07, comfortably above the 1e-6 accuracy floor.
    # The contract budget is against the exact stored-data estimator, whereas
    # this oracle is the independent object. Add a separate model/storage
    # allowance: <=10 amplification in phase inversion, <=9 in band fusion,
    # <=9 retained modes in synthesis, times the finite-model phase residual.
    model_budget = (
        4096 * CIRCULAR_BUDGET * float(np.max(np.abs(images))) / float(np.min(brightness))
    )
    np.testing.assert_allclose(result.image, truth, atol=budget + model_budget, rtol=0)
    np.testing.assert_allclose(result.spectrum, spectrum, atol=budget + model_budget, rtol=0)
    assert result.pixel_size_um == (dy / 2, dx / 2)
    np.testing.assert_allclose(
        result.fy_per_um, np.arange(-ny, ny) / (ny * dy), atol=0, rtol=8 * EPS
    )
    np.testing.assert_allclose(
        result.fx_per_um, np.arange(-nx, nx) / (nx * dx), atol=0, rtol=8 * EPS
    )
    wrong = simrecon.reconstruct(images, phases_rad=np.tile(phases, (2, 1)), **args)
    wrong_error = float(np.max(np.abs(wrong.image - truth)))
    assert wrong_error > 1000 * budget
    # Keep the actual measured comparison durable and source-free in A output.
    print(
        "PUBLIC_RESULT "
        + json.dumps(
            {
                "corrected_image_max_error": float(np.max(np.abs(result.image - truth))),
                "corrected_spectrum_max_error": float(np.max(np.abs(result.spectrum - spectrum))),
                "pixel_only_image_max_error": wrong_error,
                "contract_budget": budget,
                "independent_model_allowance": model_budget,
            }
        )
    )


def test_no_file_io(correct: Callable[..., Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """D12: array preparation performs no Python file access."""
    args = inputs()

    def deny(*unused_args: Any, **unused_kwargs: Any) -> Any:
        raise AssertionError("pure drift preparation attempted file I/O")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", deny)
        patch.setattr(Path, "open", deny)
        result = correct(**args)
    assert_prepared(result, args)


def test_oracle_analytic_sanity_without_product() -> None:
    """Observer self-checks: analytic phase roots, circular sum and object DFT."""
    phases = np.zeros(2)
    roots = represented_phasors(phases, np.array([1, 1]), np.array([[1, 0], [0, 1]]), (4, 6))
    np.testing.assert_allclose(roots, [1j, 0.5 + np.sqrt(3) / 2 * 1j], atol=8 * EPS, rtol=0)
    errors = circular_errors(
        np.array([np.pi / 2, np.pi / 3]),
        phases,
        np.array([1, 1]),
        np.array([[1, 0], [0, 1]]),
        (4, 6),
    )
    assert all(error <= 8 * EPS for error in errors)
    for grid, k, shift, expected_root in [
        (
            (4, 8),
            np.array([2**64 - 1, 2**64 - 2], dtype=np.uint64),
            np.array([[2**64 - 1, 2**64 - 2]], dtype=np.uint64),
            -1j,
        ),
        (
            (3, 4),
            np.array([-(2**63), 2**63 - 1], dtype=np.int64),
            np.array([[-(2**63), 2**63 - 1]], dtype=np.int64),
            complex(-np.sqrt(3) / 2, -0.5),
        ),
    ]:
        root = represented_phasors(np.zeros(1), k, shift, grid)[0]
        assert abs(root - expected_root) <= 8 * EPS
    shape = (5, 6)
    truth, spectrum = doubled_truth(shape)
    # Explicit positive synthesis from the seven analytically listed object modes.
    rebuilt = np.zeros_like(spectrum)
    for y in range(10):
        for x in range(12):
            total = 0j
            for j, col in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
                angle = 2 * np.pi * (j * y / 10 + col * x / 12)
                total += spectrum[j + 5, col + 6] * complex(np.cos(angle), np.sin(angle))
            rebuilt[y, x] = total
    np.testing.assert_allclose(rebuilt, truth, atol=16 * EPS, rtol=0)
    dc, c1 = expected_components(shape, np.array([1, -1]), 1.25, 0.6)
    stationary = acquire(
        shape, np.array([0.0, 0.7, 2.0]), np.array([1, -1]), np.zeros((3, 2), dtype=int)
    )
    expected = dc[None] + 2 * (c1[None] * phasors(np.array([0.0, 0.7, 2.0]))[:, None, None]).real
    np.testing.assert_allclose(
        stationary, expected, atol=64 * EPS * float(np.max(np.abs(stationary))), rtol=0
    )
