"""BEAD-PEAK-01 initial blind A tests of the approved public boundary.

The locator uses exact converted values. Numerical tolerances occur only in the
inherited known-phase composition. No source, private API, physical-center fit,
percentage target, or product-produced expected index is used.
"""

import gc
import itertools
import warnings
import weakref
from typing import Any, Literal

import numpy as np
import pytest
from numpy.typing import NDArray

import simrecon
from bead_peak_fixture import (
    composition_evidence,
    separator_dc_budget,
    stored_dc_oracle,
    synthetic_bead,
)

Array = NDArray[Any]
ErrorMode = Literal["ignore", "warn", "raise", "call", "print", "log"]
Q = float.fromhex("0x0.0000000000001p-1022")
FMAX = float.fromhex("0x1.fffffffffffffp+1023")


def public(name: str) -> Any:
    value = getattr(simrecon, name, None)
    assert callable(value), f"missing public export: simrecon.{name}"
    return value


@pytest.fixture
def locate() -> Any:
    return public("locate_bead_peak")


@pytest.mark.parametrize("name", ["locate_bead_peak", "BeadPeak"])
def test_public_exports(name: str) -> None:
    public(name)


def assert_peak(result: Any, index: tuple[int, int, int], value: float) -> None:
    assert type(result) is public("BeadPeak")
    assert type(result.index_zyx) is tuple
    assert len(result.index_zyx) == 3
    assert all(type(i) is int for i in result.index_zyx)
    assert result.index_zyx == index
    assert type(result.value) is float
    assert result.value == value
    assert result.value > 0 and np.isfinite(result.value)


def reject(locate: Any, volume: Any, code: str) -> None:
    before = volume.tobytes() if type(volume) is np.ndarray else None
    with pytest.raises(public("SimreconError")) as error:
        locate(volume)
    assert error.value.code == code
    if before is not None:
        assert volume.tobytes() == before


def test_public_binding_and_frozen_two_field_record(locate: Any) -> None:
    a = np.array([[[3.5]]])
    positional, keyword = locate(a), locate(volume=a)
    assert_peak(positional, (0, 0, 0), 3.5)
    assert_peak(keyword, (0, 0, 0), 3.5)
    assert {
        name
        for name in dir(positional)
        if not name.startswith("_") and not callable(getattr(positional, name))
    } == {"index_zyx", "value"}
    for field, replacement in [("index_zyx", (1, 1, 1)), ("value", 0.0)]:
        with pytest.raises((AttributeError, TypeError)):
            setattr(positional, field, replacement)
    # Exercise direct construction without inventing an invalid-record policy.
    record = public("BeadPeak")(index_zyx=(0, 0, 0), value=2.0)
    assert record.index_zyx == (0, 0, 0) and record.value == 2.0
    with pytest.raises(TypeError):
        locate()
    with pytest.raises(TypeError):
        locate(a, a)
    with pytest.raises(TypeError):
        locate(a, unknown=a)
    with pytest.raises(TypeError):
        locate(a, volume=a)


_COORDINATES = [
    (shape, index)
    for shape in [(3, 4, 5), (2, 3, 4), (1, 1, 1), (1, 2, 3), (2, 1, 3), (2, 3, 1)]
    for index in itertools.product(*(range(n) for n in shape))
]


@pytest.mark.parametrize(("shape", "index"), _COORDINATES)
def test_named_global_coordinate_including_every_edge_and_singleton(
    locate: Any, shape: tuple[int, int, int], index: tuple[int, int, int]
) -> None:
    a = np.full(shape, -7.0)
    a[index] = 13.25
    assert_peak(locate(a), index, 13.25)


def test_signed_asymmetric_multiple_peaks_and_lower_ties(locate: Any) -> None:
    a = np.full((4, 3, 7), -11.0)
    a[1, 1, 1] = 12.0
    a[2, 1, 5] = 17.0
    a[0, 2, 4] = a[3, 0, 2] = 9.0
    a[0, 0, 0], a[0, 0, 1] = -0.0, 0.0
    assert_peak(locate(a), (2, 1, 5), 17.0)


_REAL_DTYPES = sorted(
    {
        np.dtype(t).str
        for t in [
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
        for t in [np.dtype(t).newbyteorder("<"), np.dtype(t).newbyteorder(">")]
    }
)


@pytest.mark.parametrize("dtype", _REAL_DTYPES)
def test_all_available_real_widths_and_byte_orders(locate: Any, dtype: str) -> None:
    a = np.ones((2, 3, 4), dtype=dtype)
    a[1, 0, 2] = 19
    assert_peak(locate(a), (1, 0, 2), 19.0)


@pytest.mark.parametrize(
    "storage",
    ["c", "fortran", "readonly", "strided", "reversed", "transposed", "broadcast_readonly"],
)
def test_supported_storage_and_logical_axes(locate: Any, storage: str) -> None:
    if storage == "broadcast_readonly":
        a = np.broadcast_to(np.array([[[2.0, 7.0, 3.0]]]), (1, 1, 3))
        index = (0, 0, 1)
    else:
        a = np.full((2, 3, 4), -1.0)
        a[1, 0, 2] = 7.0
        index = (1, 0, 2)
        if storage == "fortran":
            a = np.asfortranarray(a)
        elif storage == "readonly":
            a.flags.writeable = False
        elif storage == "strided":
            backing = np.full((4, 6, 8), -50.0)
            backing[::2, ::2, ::2] = a
            a = backing[::2, ::2, ::2]
        elif storage == "reversed":
            a = a[::-1, ::-1, ::-1]
            index = (0, 2, 1)
        elif storage == "transposed":
            a = a.transpose(2, 0, 1)
            index = (2, 1, 0)
    before = a.tobytes()
    assert_peak(locate(a), index, 7.0)
    assert a.tobytes() == before


@pytest.mark.parametrize("dtype", [np.int64, np.uint64])
def test_integer_conversion_value_not_raw_integer(locate: Any, dtype: Any) -> None:
    a = np.array([[[2**53 + 3, 2**53, 1]]], dtype=dtype)
    assert float(int(a[0, 0, 0])) == float(2**53 + 4)
    assert_peak(locate(a), (0, 0, 0), float(2**53 + 4))


@pytest.mark.parametrize("dtype", [np.int64, np.uint64])
def test_integer_rounding_created_tie(locate: Any, dtype: Any) -> None:
    a = np.array([[[2**53, 2**53 + 1, 0]]], dtype=dtype)
    assert int(a[0, 0, 0]) != int(a[0, 0, 1])
    assert float(int(a[0, 0, 0])) == float(int(a[0, 0, 1]))
    reject(locate, a, "ambiguous_bead_peak")


class ArraySubclass(np.ndarray[Any, Any]):
    """A legal ndarray subclass that the plain-array API must reject."""


@pytest.mark.parametrize(
    "volume",
    [
        None,
        3.0,
        [[[1.0]]],
        (1, 2),
        np.float64(2),
        np.ones((1, 1, 1)).view(ArraySubclass),
        np.ma.array([[[2.0]]], mask=False),
    ],
)
def test_reject_nonplain_array(locate: Any, volume: Any) -> None:
    reject(locate, volume, "invalid_bead_peak_volume")


@pytest.mark.parametrize(
    "dtype",
    ["?", "c8", "c16", "O", "S2", "U2", [("v", "f8")], "datetime64[D]", "timedelta64[D]", "V4"],
)
def test_reject_nonreal_dtype(locate: Any, dtype: Any) -> None:
    reject(locate, np.zeros((1, 2, 3), dtype=dtype), "invalid_bead_peak_dtype")


@pytest.mark.parametrize(
    "shape", [(), (3,), (2, 3), (1, 2, 3, 4), (0, 2, 3), (2, 0, 3), (2, 3, 0), (0, 0, 0)]
)
def test_reject_wrong_rank_or_empty_axis(locate: Any, shape: tuple[int, ...]) -> None:
    reject(locate, np.ones(shape), "invalid_bead_peak_shape")


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("index", [(0, 0, 0), (1, 2, 3)])
def test_reject_any_nonfinite_source_even_away_from_peak(
    locate: Any, bad: float, index: tuple[int, int, int]
) -> None:
    a = np.zeros((2, 3, 4))
    a[0, 1, 2] = 4.0
    a[index] = bad
    reject(locate, a, "nonfinite_bead_peak_volume")


@pytest.mark.parametrize(
    "values", [[-9.0, -2.0, -3.0], [0.0, -0.0, 0.0], [-FMAX, -Q, -0.0], [-Q, -2 * Q, -3 * Q]]
)
def test_reject_no_positive_converted_maximum(locate: Any, values: list[float]) -> None:
    reject(locate, np.array([[values]]), "no_positive_bead_peak")


@pytest.mark.parametrize(
    "pattern", ["adjacent", "separated", "plateau", "constant", "subnormal", "maximum"]
)
def test_reject_exact_positive_global_ties(locate: Any, pattern: str) -> None:
    a = np.full((3, 4, 5), -1.0)
    if pattern == "constant":
        a.fill(6.0)
    elif pattern == "plateau":
        a[1, 1:3, 2:4] = 6.0
    else:
        value = Q if pattern == "subnormal" else FMAX if pattern == "maximum" else 6.0
        a[0, 0, 0] = value
        a[(0, 0, 1) if pattern == "adjacent" else (2, 3, 4)] = value
    reject(locate, a, "ambiguous_bead_peak")


@pytest.mark.parametrize("peak", [Q, float.fromhex("0x1p-1022"), 1.0, FMAX])
def test_positive_extrema_without_sum_norm_or_epsilon_floor(locate: Any, peak: float) -> None:
    # Near-equal positives distinguish epsilon-based tie rejection; huge signed
    # backgrounds distinguish unnecessary sum/magnitude arithmetic.
    previous = float(np.nextafter(peak, 0.0))
    a = np.full((2, 3, 4), -FMAX)
    a[0, 0, 0] = previous
    a[1, 2, 3] = peak
    with np.errstate(all="raise"):
        assert_peak(locate(a), (1, 2, 3), peak)


def test_snapshot_preservation_and_scalar_ownership(locate: Any) -> None:
    backing = np.full((4, 6, 8), -2.0)
    a = backing[::2, ::2, ::2]
    a[1, 2, 3] = 6.5
    before, shape, strides, dtype = backing.tobytes(), a.shape, a.strides, a.dtype
    first, second = locate(a), locate(a)
    assert_peak(first, (1, 2, 3), 6.5)
    assert_peak(second, (1, 2, 3), 6.5)
    assert backing.tobytes() == before
    assert (a.shape, a.strides, a.dtype) == (shape, strides, dtype)
    a.fill(-100)
    assert_peak(first, (1, 2, 3), 6.5)
    assert_peak(second, (1, 2, 3), 6.5)
    # Rejection must preserve the entire backing storage as well.
    before = backing.tobytes()
    reject(locate, a, "no_positive_bead_peak")
    assert backing.tobytes() == before


def test_result_does_not_retain_caller_storage(locate: Any) -> None:
    backing = np.full((4, 6, 8), -1.0)
    volume = backing[::2, ::2, ::2]
    volume[1, 2, 3] = 7.0
    backing_reference, volume_reference = weakref.ref(backing), weakref.ref(volume)
    result = locate(volume)
    assert_peak(result, (1, 2, 3), 7.0)
    del volume, backing
    gc.collect()
    assert backing_reference() is None
    assert volume_reference() is None
    assert_peak(result, (1, 2, 3), 7.0)


class ErrorObserver:
    """Record NumPy callback and log diagnostics without printing internals."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    def __call__(self, *args: Any) -> None:
        self.events.append(args)

    def write(self, message: str) -> None:
        self.events.append(message)


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_modes_warnings_and_callbacks_preserved(locate: Any, mode: ErrorMode, capsys: Any) -> None:
    observer = ErrorObserver()
    old_handler = np.geterrcall()
    np.seterrcall(observer)
    try:
        with np.errstate(all=mode):
            expected_modes = np.geterr().copy()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                assert_peak(locate(np.array([[[-FMAX, 0.0, Q]]])), (0, 0, 2), Q)
                assert np.geterr() == expected_modes and np.geterrcall() is observer
                reject(locate, np.array([[[0.0, -0.0]]]), "no_positive_bead_peak")
                assert np.geterr() == expected_modes and np.geterrcall() is observer
                reject(locate, np.array([[[Q, Q]]]), "ambiguous_bead_peak")
                assert np.geterr() == expected_modes and np.geterrcall() is observer
                reject(locate, np.array([[[np.inf, 1.0]]]), "nonfinite_bead_peak_volume")
                assert np.geterr() == expected_modes
                assert np.geterrcall() is observer
                assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
                # Detect leaked global warning filters; this does not claim an
                # unrelated warning can be injected inside the plain-array API.
                warnings.warn("owned observer warning", UserWarning, stacklevel=1)
                assert any(
                    w.category is UserWarning and str(w.message) == "owned observer warning"
                    for w in caught
                )
            assert observer.events == []
            captured = capsys.readouterr()
            assert captured.err == captured.out == ""
    finally:
        np.seterrcall(old_handler)


_WIDE = np.finfo(np.longdouble)
_DOUBLE = np.finfo(np.float64)
# Register only actual native capabilities. No skip/xfail stands in for evidence.
_WIDER_CASES = []
if _WIDE.nmant > _DOUBLE.nmant:
    _WIDER_CASES += ["precision_tie", "finite_rounding"]
if _WIDE.maxexp > _DOUBLE.maxexp:
    _WIDER_CASES += ["range_overflow"]
if _WIDE.minexp - _WIDE.nmant < _DOUBLE.minexp - _DOUBLE.nmant:
    _WIDER_CASES += ["positive_underflow", "negative_underflow", "underflow_with_peak"]


if _WIDER_CASES:

    @pytest.mark.parametrize("case", _WIDER_CASES)
    @pytest.mark.parametrize("mode", ["warn", "raise"])
    def test_supported_native_wider_conversion(locate: Any, case: str, mode: ErrorMode) -> None:
        if case == "precision_tie":
            a = np.array([[[np.longdouble(1), np.longdouble(1) + np.longdouble(2) ** -53]]])
            assert a[0, 0, 1] > a[0, 0, 0]
            code = "ambiguous_bead_peak"
        elif case == "finite_rounding":
            a = np.array([[[np.longdouble(1) + np.longdouble(2) ** -54, np.longdouble(0)]]])
            code = None
        elif case == "range_overflow":
            a = np.array([[[np.longdouble(FMAX) * np.longdouble(2), np.longdouble(1)]]])
            assert np.all(np.isfinite(a))
            code = "nonfinite_bead_peak_volume"
        elif case == "underflow_with_peak":
            tiny = np.longdouble(2) ** -1075
            assert tiny > 0 and np.isfinite(tiny)
            a = np.array([[[tiny, np.longdouble(1), -tiny]]])
            code = None
        else:
            tiny = np.longdouble(2) ** -1075
            assert tiny > 0 and np.isfinite(tiny)
            a = np.array([[[tiny if case == "positive_underflow" else -tiny, np.longdouble(0)]]])
            code = "no_positive_bead_peak"
        with np.errstate(all=mode), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            before_modes = np.geterr().copy()
            if code is None:
                index = (0, 0, 1) if case == "underflow_with_peak" else (0, 0, 0)
                assert_peak(locate(a), index, 1.0)
            else:
                reject(locate, a, code)
            assert np.geterr() == before_modes
            assert not any(issubclass(w.category, RuntimeWarning) for w in caught)


@pytest.mark.parametrize(
    ("asymmetric", "mapped_camera", "truth"),
    [(False, False, (1, 2, 3)), (True, True, (2, 0, 4)), (False, True, (0, 3, 0))],
)
def test_real_public_corrected_true_phase_composition(
    locate: Any, asymmetric: bool, mapped_camera: bool, truth: tuple[int, int, int]
) -> None:
    fixture = synthetic_bead(asymmetric=asymmetric, mapped_camera=mapped_camera, truth=truth)
    evidence = composition_evidence(fixture)
    acquisition = public("declare_acquisition")(fixture.raw, config=fixture.config)
    assert acquisition.axes == ("orientation", "phase", "z", "y", "x")
    assert np.array_equal(acquisition.nominal_phases_rad[0], fixture.commands)
    corrected = public("correct_linear_response")(
        acquisition, offset=fixture.offset, response=fixture.response, output_unit="electrons"
    )
    assert corrected.output_unit == "electrons"
    assert np.array_equal(corrected.data[0], fixture.corrected)
    # Actual truth is supplied explicitly. Nominal commands are never reused as
    # truth. The bead index is passed only to the observer, never the locator.
    observed = public("separate_volume_phases")(corrected.data[0], phases_rad=fixture.phases)
    expected_dc = stored_dc_oracle(fixture.corrected, fixture.phases)
    assert np.all(np.abs(observed.dc - expected_dc) <= separator_dc_budget(fixture.corrected))
    model_allowance = (
        evidence["stored_model_error_electrons"] + evidence["separator_budget_electrons"]
    )
    assert np.max(np.abs(observed.dc - fixture.ideal_dc)) <= model_allowance
    assert evidence["peak_margin_electrons"] > 2 * model_allowance
    before = observed.dc.tobytes()
    assert_peak(locate(observed.dc), truth, float(observed.dc[truth]))
    assert observed.dc.tobytes() == before
