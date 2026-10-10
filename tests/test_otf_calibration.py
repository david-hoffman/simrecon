"""Fresh blind A public-entry tests; mapping and gaps are in the A handoff.

K25 uses the intake-declared always-used private production collaborator solely
for fault control through public prepare_otf. No transform backend is selected.
K28 existing-suite compatibility remains coordinator/C/D evidence; K29 usage
and product comparison remain C/D responsibilities.
Wider-range cases are added only when the native platform supports them.
"""

import builtins
import io
import os
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from decimal import Decimal, localcontext
from fractions import Fraction
from importlib import import_module
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

import simrecon
from otf_calibration_fixture import (
    EPS,
    ORACLE_GUARD,
    ComplexArray,
    ComplexReference,
    OtfRecord,
    PrepareOtf,
    Q,
    RealArray,
    RecordFactory,
    analytic_cases,
    as_factory,
    as_prepare,
    assert_frequency,
    assert_transfer,
    exact_frequency,
    modes,
    negative_root,
    permitted_dtypes,
    reference_transfer,
    transfer_budget,
    wider_source_cases,
)

SPACING = (0.125, 0.25)
LABEL = "  independent public calibration\n "
CASES = tuple(analytic_cases())
DTYPES = permitted_dtypes()
WIDER_CASES = wider_source_cases()
MAX = float(np.finfo(np.float64).max)
MIN_NORMAL = float(np.finfo(np.float64).tiny)


@pytest.fixture
def prepare() -> PrepareOtf:
    binding = getattr(simrecon, "prepare_otf", None)
    assert callable(binding), "missing public simrecon.prepare_otf"
    return as_prepare(binding)


@pytest.fixture
def record_factory() -> RecordFactory:
    binding = getattr(simrecon, "Otf2D", None)
    assert isinstance(binding, type), "missing public simrecon.Otf2D"
    return as_factory(binding)


def _snapshot(value: object) -> object:
    if isinstance(value, np.ndarray):
        return value.shape, value.dtype.str, value.tobytes(), value.flags.writeable
    if isinstance(value, (tuple, list)):
        return type(value), tuple(_snapshot(item) for item in value)
    return repr(value)


def _check_representation(result: OtfRecord, shape: tuple[int, int]) -> None:
    for array, dtype, required_shape in (
        (result.values, np.dtype(np.complex128), shape),
        (result.fy_per_um, np.dtype(np.float64), (shape[0],)),
        (result.fx_per_um, np.dtype(np.float64), (shape[1],)),
    ):
        assert type(array) is np.ndarray, "ordinary output ndarray"
        assert array.dtype == dtype and array.dtype.isnative, "native output dtype"
        assert array.shape == required_shape, "output shape"
        assert array.flags.c_contiguous, "C-contiguous output"
        assert array.flags.owndata, "output owns its storage"
        assert array.flags.writeable, "output content is mutable"
    arrays = (result.values, result.fy_per_um, result.fx_per_um)
    for i, first in enumerate(arrays):
        for second in arrays[i + 1 :]:
            assert not np.shares_memory(first, second), "output storage is separate"


def _check_result(
    result: OtfRecord,
    psf: RealArray,
    origin: tuple[int, int],
    spacing: tuple[float, float] = SPACING,
    source: str = LABEL,
) -> None:
    shape = cast(tuple[int, int], psf.shape)
    record_type = getattr(simrecon, "Otf2D", None)
    assert isinstance(record_type, type), "public Otf2D record type"
    assert isinstance(result, record_type), "preparation returns Otf2D"
    _check_representation(result, shape)
    assert_transfer(result.values, reference_transfer(psf, origin))
    assert_frequency(result.fy_per_um, shape[0], spacing[0])
    assert_frequency(result.fx_per_um, shape[1], spacing[1])
    assert type(result.pixel_size_um) is tuple, "converted pixel-size tuple"
    assert all(type(v) is float for v in result.pixel_size_um), "Python float spacings"
    assert result.pixel_size_um == spacing, "retain converted sampling"
    assert type(result.origin_yx) is tuple, "validated origin tuple"
    assert all(type(v) is int for v in result.origin_yx), "Python integer origin"
    assert result.origin_yx == origin, "retain explicit origin"
    assert result.source == source, "retain source text unchanged"
    assert not np.shares_memory(result.values, psf), "no PSF alias"
    assert not np.shares_memory(result.fy_per_um, psf), "no PSF alias"
    assert not np.shares_memory(result.fx_per_um, psf), "no PSF alias"
    # Sanity checks supplement, rather than replace, the complete signed sum.
    budget = float(transfer_budget(psf.size))
    assert bool((np.abs(result.values) <= 1 + budget).all()), "unit-mass modulus bound"
    my, mx = modes(shape[0]), modes(shape[1])
    for iy, ky in enumerate(my):
        jy = next(j for j, mode in enumerate(my) if (mode + ky) % shape[0] == 0)
        for ix, kx in enumerate(mx):
            jx = next(j for j, mode in enumerate(mx) if (mode + kx) % shape[1] == 0)
            difference = result.values[iy, ix] - result.values[jy, jx].conjugate()
            assert abs(difference) <= 2 * budget, "modular Hermitian symmetry"


def _call(
    prepare: PrepareOtf,
    psf: RealArray,
    origin: tuple[int, int],
    spacing: tuple[float, float] = SPACING,
    source: str = LABEL,
) -> OtfRecord:
    before = _snapshot(psf)
    result = prepare(psf, pixel_size_um=spacing, origin_yx=origin, source=source)
    assert _snapshot(psf) == before, "success must leave input unchanged"
    _check_result(result, psf, origin, spacing, source)
    return result


def _reject(
    prepare: PrepareOtf,
    psf: object,
    codes: str | tuple[str, ...],
    *,
    spacing: object = SPACING,
    origin: object = (0, 0),
    source: object = LABEL,
) -> None:
    inputs = (psf, spacing, origin, source)
    before = tuple(_snapshot(v) for v in inputs)
    with pytest.raises(ValueError) as caught:
        prepare(psf, pixel_size_um=spacing, origin_yx=origin, source=source)
    assert tuple(_snapshot(v) for v in inputs) == before, "rejection leaves inputs unchanged"
    error_type = getattr(simrecon, "SimreconError", None)
    assert isinstance(error_type, type), "existing public error binding"
    assert isinstance(caught.value, error_type), "structured public SimreconError"
    code = getattr(caught.value, "code", None)
    message = getattr(caught.value, "message", None)
    assert isinstance(code, str), "error code is a string"
    assert code in ((codes,) if isinstance(codes, str) else codes), "contract error code"
    assert isinstance(message, str), "error message is a string; exact prose unspecified"


def test_public_exports() -> None:
    """K07/K28 public import boundary; no runtime inspection."""
    assert callable(getattr(simrecon, "prepare_otf", None)), "public prepare_otf export"
    assert isinstance(getattr(simrecon, "Otf2D", None), type), "public Otf2D export"
    assert isinstance(getattr(simrecon, "SimreconError", None), type), "existing error export"
    assert callable(getattr(simrecon, "separate_phases", None)), "existing separation export"


def test_independent_root_and_budget_sanity() -> None:
    """Oracle qualification independent of a product/FFT/rounded JSON."""
    for turns, expected in (
        (Fraction(0), (1, 0)),
        (Fraction(1, 4), (0, -1)),
        (Fraction(1, 2), (-1, 0)),
        (Fraction(3, 4), (0, 1)),
        (Fraction(-7, 4), (0, -1)),
    ):
        assert negative_root(turns) == expected
    with localcontext() as context:
        context.prec = 110
        sqrt_three_over_two = Fraction(Decimal(3).sqrt() / 2)
    real, imag = negative_root(Fraction(1, 3))
    assert abs(real + Fraction(1, 2)) < ORACLE_GUARD
    assert abs(imag + sqrt_three_over_two) < ORACLE_GUARD
    assert transfer_budget(2) - 256 * EPS == 8 * Q, "retain exact subnormal budget term"
    assert exact_frequency(6, 0.25) == (
        Fraction(-2),
        Fraction(-4, 3),
        Fraction(-2, 3),
        Fraction(0),
        Fraction(2, 3),
        Fraction(4, 3),
    )


def test_independent_full_root_identities() -> None:
    """Full-array checks of independently derived constant/separable/asymmetric roots."""
    cases = {name: (psf, origin) for name, psf, origin in CASES}
    for name in ("delta-odd", "singleton"):
        reference = reference_transfer(*cases[name])
        assert all(value == (1, 0) for row in reference for value in row)
    uniform = reference_transfer(*cases["uniform-even"])
    for y, row in enumerate(uniform):
        for x, (real, imag) in enumerate(row):
            dc = Fraction(int((y, x) == (2, 3)))
            assert abs(real - dc) + abs(imag) < ORACLE_GUARD
    separable = reference_transfer(*cases["separable-mixed"])
    for y, wy in enumerate((Fraction(1, 4), Fraction(1), Fraction(1, 4))):
        for x, wx in enumerate((1, 0, 1, 0)):
            real, imag = separable[y][x]
            assert abs(real - wy * wx) + abs(imag) < ORACLE_GUARD
    with localcontext() as context:
        context.prec = 110
        h = Fraction(Decimal(3).sqrt() / 2)
    # Explicit roots, not a second trigonometric summation or an FFT.
    ry: tuple[ComplexReference, ...] = (
        (Fraction(-1), Fraction(0)),
        (Fraction(0), Fraction(1)),
        (Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(-1)),
    )
    rx: tuple[ComplexReference, ...] = (
        (Fraction(-1), Fraction(0)),
        (Fraction(-1, 2), h),
        (Fraction(1, 2), h),
        (Fraction(1), Fraction(0)),
        (Fraction(1, 2), -h),
        (Fraction(-1, 2), -h),
    )
    asymmetric = reference_transfer(*cases["asymmetric-even"])
    translated = reference_transfer(*cases["asymmetric-translated"])
    for y, (yr, yi) in enumerate(ry):
        for x, (xr, xi) in enumerate(rx):
            er, ei = Fraction(3, 8) + yr / 8 + xr / 2, yi / 8 + xi / 2
            for reference in (asymmetric, translated):
                real, imag = reference[y][x]
                assert abs(real - er) + abs(imag - ei) < ORACLE_GUARD


def test_independent_comparison_boundaries() -> None:
    """Qualify observers at the budget, across complex components and extreme grids."""
    expected = (((Fraction(1), Fraction(0)),),)
    assert_transfer(np.array([[1 + 128 * float(EPS)]], dtype=np.complex128), expected)
    with pytest.raises(AssertionError):
        assert_transfer(np.array([[1 + 129 * float(EPS)]], dtype=np.complex128), expected)
    with pytest.raises(AssertionError):
        assert_transfer(np.array([[1 + 100 * float(EPS) + 100 * float(EPS) * 1j]]), expected)
    for length, spacing in ((1, float(Q)), (1, MAX), (6, MAX), (3, MIN_NORMAL)):
        coordinates = np.array([float(v) for v in exact_frequency(length, spacing)])
        assert_frequency(coordinates, length, spacing)
    with pytest.raises(AssertionError):
        assert_frequency(np.array([-2.0, 0.0, 2.0]), 3, 1.0)


@pytest.mark.parametrize("name,psf,origin", CASES, ids=[case[0] for case in CASES])
def test_analytic_public_transfer(
    prepare: PrepareOtf, name: str, psf: RealArray, origin: tuple[int, int]
) -> None:
    """K01--K08; all six examples derived anew from the complete sum."""
    _call(prepare, psf, origin, source=name)


@pytest.mark.parametrize("shape", [(1, 5), (5, 1), (2, 3), (3, 2), (4, 7), (5, 6), (7, 11)])
def test_full_grid_and_anisotropic_sampling(prepare: PrepareOtf, shape: tuple[int, int]) -> None:
    """K01/K03/K05 nonsquare mixed parity and prime-length grids."""
    psf = ((np.arange(shape[0] * shape[1]).reshape(shape) * 7 + 3) % 19).astype(np.float64)
    origin = (shape[0] - 1, shape[1] // 3)
    _call(prepare, psf, origin, (0.3, 1.75))


@pytest.mark.parametrize("origin", [(y, x) for y in range(3) for x in range(4)])
def test_every_in_bounds_origin_and_wraparound(
    prepare: PrepareOtf, origin: tuple[int, int]
) -> None:
    """K02/K19 positive pair: fixed off-origin delta, every legal origin."""
    psf = np.zeros((3, 4))
    psf[2, 0] = 9
    _call(prepare, psf, origin)


@pytest.mark.parametrize("shift", [(-3, 5), (1, -4), (7, 13)])
def test_joint_circular_translation(prepare: PrepareOtf, shift: tuple[int, int]) -> None:
    """K02 translate both PSF and origin, with wrapping in either direction."""
    _, psf, origin = CASES[2]
    shifted = np.roll(psf, shift, axis=(0, 1))
    shifted_origin = ((origin[0] + shift[0]) % 4, (origin[1] + shift[1]) % 6)
    first = _call(prepare, psf, origin)
    second = _call(prepare, shifted, shifted_origin)
    assert_transfer(second.values, reference_transfer(psf, origin))
    assert_transfer(first.values, reference_transfer(shifted, shifted_origin))


@pytest.mark.parametrize("gain", [0.125, 1.0, 16.0, 2.0**500])
def test_exact_gain_and_pixel_area_cancel(prepare: PrepareOtf, gain: float) -> None:
    """K04 gain is exact; sampling changes frequencies, not normalized values."""
    _, psf, origin = CASES[2]
    scaled = psf.astype(np.float64) * gain
    result = _call(prepare, scaled, origin, (3.0, 7.0))
    assert_transfer(result.values, reference_transfer(psf, origin))


def test_small_resolved_tail_is_preserved(prepare: PrepareOtf) -> None:
    """K05 tiny changes well above tau distinguish thresholding/cropping."""
    psf = np.zeros((5, 7))
    psf[1, 2] = 1
    psf[4, 6] = 2.0**-24
    _call(prepare, psf, (1, 2))


@pytest.mark.parametrize("label,dtype", DTYPES, ids=[item[0] for item in DTYPES])
def test_all_real_widths_and_byte_orders(
    prepare: PrepareOtf, label: str, dtype: np.dtype[Any]
) -> None:
    """K06/K10 positive examples, all available real widths and byte orders."""
    samples = [[1, 2, 0, 7], [0, 3, 1, 0], [4, 0, 2, 1]]
    psf = np.array(samples, dtype=dtype)
    if dtype.kind == "f":
        psf[0, 0] = 0.1
        psf[1, 1] = 1 / 3
    _call(prepare, psf, (2, 1), source=label)


@pytest.mark.parametrize("dtype", [np.int64, np.uint64], ids=["int64", "uint64"])
def test_large_integer_conversion(
    prepare: PrepareOtf, dtype: type[np.signedinteger[Any]] | type[np.unsignedinteger[Any]]
) -> None:
    """K06 values rounded to binary64, not mathematical original integers."""
    psf = np.array([[2**53 + 1, 2**53 + 3, int(np.iinfo(dtype).max)], [1, 0, 7]], dtype=dtype)
    _call(prepare, psf, (1, 1))


def test_longdouble_converted_values(prepare: PrepareOtf) -> None:
    """K06 representable wider inputs, or honest equivalent-width positive input."""
    with np.errstate(all="ignore"):
        half_ulp = np.ldexp(np.longdouble(1), -53)
        psf = np.array(
            [[np.longdouble(1) + half_ulp, np.longdouble(1) + 3 * half_ulp, 0]],
            dtype=np.longdouble,
        )
    _call(prepare, psf, (0, 1))
    _call(prepare, np.array([[np.longdouble(MAX), 1]], dtype=np.longdouble), (0, 0))


def test_conversion_rounding_changes_gain_problem(prepare: PrepareOtf) -> None:
    """K06 no gain invariant when binary64 conversion changes sample ratios."""
    q = float(Q)
    first = np.array([[q, 2 * q, 4 * q]])
    with np.errstate(under="ignore"):
        second = first * 0.5
    _call(prepare, first, (0, 0))
    _call(prepare, second, (0, 0))
    assert reference_transfer(first, (0, 0)) != reference_transfer(second, (0, 0))


@pytest.mark.parametrize("layout", ["readonly", "strided", "reversed", "fortran"])
def test_input_layout_ownership_and_output_mutation(prepare: PrepareOtf, layout: str) -> None:
    """K07/K08 permitted layout and independent mutable output storage."""
    backing = np.arange(48, dtype=np.float64).reshape(6, 8)
    if layout == "strided":
        psf = backing[::2, ::2]
    elif layout == "reversed":
        psf = backing[::-1, ::-1]
    elif layout == "fortran":
        psf = np.asfortranarray(backing)
    else:
        psf = backing.view()
        psf.flags.writeable = False
    before = _snapshot(backing)
    spacing_input = np.array(SPACING)
    origin_input = np.array([1, 1], dtype=np.int64)
    input_snapshots = (_snapshot(psf), _snapshot(spacing_input), _snapshot(origin_input))
    result = prepare(psf, pixel_size_um=spacing_input, origin_yx=origin_input, source=LABEL)
    _check_result(result, psf, (1, 1))
    for array in (result.values, result.fy_per_um, result.fx_per_um):
        for input_array in (psf, backing, spacing_input, origin_input):
            assert not np.shares_memory(array, input_array), "no input/output alias"
    arrays = (result.values, result.fy_per_um, result.fx_per_um)
    for index, array in enumerate(arrays):
        other_before = [_snapshot(other) for i, other in enumerate(arrays) if i != index]
        array.flat[0] = 123
        assert [_snapshot(other) for i, other in enumerate(arrays) if i != index] == other_before
        assert (
            _snapshot(psf),
            _snapshot(spacing_input),
            _snapshot(origin_input),
        ) == input_snapshots
    assert _snapshot(backing) == before, "mutating outputs leaves backing storage unchanged"
    # A later call must not reuse the first call's arrays.
    repeated = _call(prepare, psf, (1, 1))
    for old in arrays:
        for new in (repeated.values, repeated.fy_per_um, repeated.fx_per_um):
            assert not np.shares_memory(old, new), "calls allocate independent storage"


@pytest.mark.parametrize(
    "attribute", ["values", "fy_per_um", "fx_per_um", "pixel_size_um", "origin_yx", "source"]
)
def test_record_bindings_are_frozen(prepare: PrepareOtf, attribute: str) -> None:
    """K07 frozen bindings; no unspecified exception class is required."""
    result = _call(prepare, np.array([[1]]), (0, 0))
    original = getattr(result, attribute)
    with suppress(Exception):
        setattr(result, attribute, object())
    assert getattr(result, attribute) is original, "attribute must not be rebound"
    with suppress(Exception):
        delattr(result, attribute)
    assert getattr(result, attribute) is original, "attribute must not be deleted"


def test_direct_record_construction_does_not_validate(record_factory: RecordFactory) -> None:
    """K07 unvalidated direct construction still binds its fields without rebinding."""
    result = record_factory(
        values=None,
        fy_per_um=None,
        fx_per_um=None,
        pixel_size_um=(-1, 0),
        origin_yx=(-2, 99),
        source="",
    )
    for attribute in ("values", "fy_per_um", "fx_per_um", "pixel_size_um", "origin_yx", "source"):
        original = getattr(result, attribute)
        with suppress(Exception):
            setattr(result, attribute, object())
        assert getattr(result, attribute) is original, "direct-record field must not be rebound"
        with suppress(Exception):
            delattr(result, attribute)
        assert getattr(result, attribute) is original, "direct-record field must not be deleted"


class _ArraySubclass(np.ndarray[Any, Any]):
    pass


@pytest.mark.parametrize(
    "psf",
    [None, [[1, 2]], 1, np.float64(1), np.array([[1]]).view(_ArraySubclass), np.ma.array([[1]])],
    ids=["none", "list", "python-scalar", "numpy-scalar", "subclass", "masked"],
)
def test_reject_nonplain_psf(prepare: PrepareOtf, psf: object) -> None:
    """K09 paired with ordinary/read-only/views in success tests."""
    _reject(prepare, psf, "invalid_psf")


@pytest.mark.parametrize(
    "dtype",
    ["?", "c8", "c16", "O", "S2", "U2", "V8", "M8[ns]", "m8[ns]", np.dtype([("mass", "f8")])],
    ids=[
        "bool",
        "complex64",
        "complex128",
        "object",
        "bytes",
        "unicode",
        "void",
        "datetime",
        "timedelta",
        "structured",
    ],
)
def test_reject_psf_dtype(prepare: PrepareOtf, dtype: object) -> None:
    """K10 rejected kinds, not rejected nonnegative values."""
    psf = np.ones((2, 3), dtype=cast(Any, dtype))
    _reject(prepare, psf, "invalid_psf_dtype")


@pytest.mark.parametrize("shape", [(), (4,), (2, 2, 2), (0, 2), (2, 0), (0, 0)])
def test_reject_psf_shape(prepare: PrepareOtf, shape: tuple[int, ...]) -> None:
    """K11 positive singleton/nonsquare pairs are exercised separately."""
    codes: str | tuple[str, ...] = "invalid_psf_shape"
    if 0 in shape:
        # An empty plane also has zero mass and no legal origin. Do not select
        # a validation order that the public contract deliberately leaves open.
        codes = ("invalid_psf_shape", "zero_psf_mass", "invalid_otf_origin")
    _reject(prepare, np.ones(shape), codes)


@pytest.mark.parametrize(
    "sample,codes",
    [
        (float("nan"), "nonfinite_psf"),
        (float("inf"), "nonfinite_psf"),
        (-float("inf"), ("nonfinite_psf", "negative_psf")),
    ],
    ids=["nan", "positive-infinity", "negative-infinity"],
)
def test_reject_nonfinite_psf(
    prepare: PrepareOtf, sample: float, codes: str | tuple[str, ...]
) -> None:
    """K12 -inf has two violations; the contract leaves precedence open."""
    _reject(prepare, np.array([[1, sample]]), codes)


@pytest.mark.parametrize(
    "dtype", [np.int8, np.int64, np.float16, np.float32, np.float64, np.longdouble]
)
def test_reject_negative_source(prepare: PrepareOtf, dtype: object) -> None:
    """K14 source negativity, paired with negative zero/nonnegative values."""
    _reject(prepare, np.array([[-1, 2]], dtype=cast(Any, dtype)), "negative_psf")


def test_signed_zero_is_permitted(prepare: PrepareOtf) -> None:
    _call(prepare, np.array([[-0.0, 1.0, 0.0]]), (0, 1))


@pytest.mark.parametrize(
    "psf", [np.zeros((2, 3)), np.full((1, 2), -0.0)], ids=["zero", "signed-zero"]
)
def test_reject_zero_converted_mass(prepare: PrepareOtf, psf: RealArray) -> None:
    """K15 paired with strictly positive subnormal samples."""
    _reject(prepare, psf, "zero_psf_mass")


# Wider cases deliberately have no pytest skip on unsupported platforms.
if WIDER_CASES:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log", "mixed"])
    @pytest.mark.parametrize("name,psf,code", WIDER_CASES, ids=[case[0] for case in WIDER_CASES])
    def test_wider_source_rejection(
        prepare: PrepareOtf, name: str, psf: RealArray, code: str, mode: str
    ) -> None:
        """K08/K13--K15/K26 source rejection under every caller arithmetic policy."""
        # Capability values and strided storage are prepared before observing
        # product execution. Setup arithmetic supplies no policy evidence.
        backing = np.ones((psf.shape[0], 2 * psf.shape[1]), dtype=psf.dtype)
        candidate = backing[:, ::2]
        candidate[...] = psf
        candidate.flags.writeable = False
        inputs: tuple[object, ...] = (candidate, backing, SPACING, (0, 0), LABEL)
        with _check_operation_preservation(mode, inputs):
            _reject(prepare, candidate, code)


WIDER_UNDERFLOW = tuple(case for case in WIDER_CASES if case[0] == "all-underflow")
if WIDER_UNDERFLOW:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log", "mixed"])
    @pytest.mark.parametrize("name,psf,code", WIDER_UNDERFLOW)
    def test_partial_wider_underflow_is_permitted(
        prepare: PrepareOtf, name: str, psf: RealArray, code: str, mode: str
    ) -> None:
        """K06/K08/K15/K26 permitted conversion loss under every arithmetic policy."""
        backing = np.ones((1, 4), dtype=np.longdouble)
        positive = backing[:, ::2]
        positive[0, 0] = psf[0, 0]
        positive.flags.writeable = False
        inputs: tuple[object, ...] = (positive, backing, SPACING, (0, 1), LABEL)
        with _check_operation_preservation(mode, inputs):
            result = _call(prepare, positive, (0, 1))
            # t converts to zero; the remaining mass is at the declared origin.
            # This exact identity supplements the unchanged converted-value oracle.
            assert_transfer(result.values, (((Fraction(1), Fraction(0)),) * 2,))


BAD_PAIRS: tuple[tuple[str, object], ...] = (
    ("none", None),
    ("scalar", 1),
    ("string", "12"),
    ("dict", {0: 1, 1: 2}),
    ("empty", ()),
    ("one", [1]),
    ("three", (1, 2, 3)),
    ("zero-rank", np.array(1)),
    ("two-rank", np.array([[1, 2]])),
    ("subclass", np.array([1, 2]).view(_ArraySubclass)),
)


@pytest.mark.parametrize("name,pair", BAD_PAIRS, ids=[pair[0] for pair in BAD_PAIRS])
def test_reject_pixel_size_container(prepare: PrepareOtf, name: str, pair: object) -> None:
    _reject(prepare, np.array([[1, 2]]), "invalid_otf_pixel_size", spacing=pair)


@pytest.mark.parametrize(
    "value",
    [True, np.bool_(False), 1 + 0j, np.complex64(1), "1", None, np.array(1.0)],
    ids=["bool", "numpy-bool", "complex", "numpy-complex", "string", "none", "zero-rank-array"],
)
@pytest.mark.parametrize("axis", [0, 1])
def test_reject_pixel_size_scalar(prepare: PrepareOtf, value: object, axis: int) -> None:
    pair: list[object] = [1.0, 1.0]
    pair[axis] = value
    _reject(prepare, np.array([[1, 2]]), "invalid_otf_pixel_size", spacing=pair)


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), -float("inf"), 0.0, -0.0, -1.0, 10**400],
    ids=["nan", "inf", "negative-inf", "zero", "negative-zero", "negative", "conversion-overflow"],
)
@pytest.mark.parametrize("axis", [0, 1])
def test_reject_pixel_size_range(prepare: PrepareOtf, value: object, axis: int) -> None:
    pair: list[object] = [1.0, 1.0]
    pair[axis] = value
    _reject(prepare, np.array([[1, 2]]), "invalid_otf_pixel_size", spacing=pair)


if WIDER_CASES:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log", "mixed"])
    @pytest.mark.parametrize(
        "name,psf,code",
        [case for case in WIDER_CASES if case[0] != "negative-underflow"],
        ids=[case[0] for case in WIDER_CASES if case[0] != "negative-underflow"],
    )
    def test_wider_spacing_rejection(
        prepare: PrepareOtf, name: str, psf: RealArray, code: str, mode: str
    ) -> None:
        """K08/K17/K26 wider spacing rejection under every arithmetic policy."""
        backing = np.ones(4, dtype=np.longdouble)
        spacing = backing[::2]
        spacing[0] = psf[0, 0]
        spacing.flags.writeable = False
        valid_psf = np.array([[1]])
        inputs: tuple[object, ...] = (valid_psf, spacing, backing, (0, 0), LABEL)
        with _check_operation_preservation(mode, inputs):
            _reject(prepare, valid_psf, "invalid_otf_pixel_size", spacing=spacing)


@pytest.mark.parametrize("name,pair", BAD_PAIRS, ids=[pair[0] for pair in BAD_PAIRS])
def test_reject_origin_container(prepare: PrepareOtf, name: str, pair: object) -> None:
    _reject(prepare, np.ones((3, 4)), "invalid_otf_origin", origin=pair)


@pytest.mark.parametrize(
    "value",
    [True, np.bool_(False), 1.0, np.float32(1), 0.5, 1 + 0j, "1", None, np.array(1)],
    ids=[
        "bool",
        "numpy-bool",
        "integral-float",
        "numpy-float",
        "fraction",
        "complex",
        "string",
        "none",
        "zero-rank-array",
    ],
)
@pytest.mark.parametrize("axis", [0, 1])
def test_reject_origin_scalar(prepare: PrepareOtf, value: object, axis: int) -> None:
    pair: list[object] = [1, 1]
    pair[axis] = value
    _reject(prepare, np.ones((3, 4)), "invalid_otf_origin", origin=pair)


@pytest.mark.parametrize(
    "origin",
    [(-1, 0), (0, -1), (3, 0), (0, 4), (10**400, 0), (0, np.uint64(2**64 - 1))],
    ids=["negative-y", "negative-x", "end-y", "end-x", "huge-y", "unsigned-end-x"],
)
def test_reject_out_of_bounds_origin(prepare: PrepareOtf, origin: object) -> None:
    _reject(prepare, np.ones((3, 4)), "invalid_otf_origin", origin=origin)


@pytest.mark.parametrize("container", ["tuple", "list", "array", "readonly-array", "object-array"])
def test_pair_containers_and_scalar_conversion(prepare: PrepareOtf, container: str) -> None:
    """K16/K18 permitted plain pair containers and Python/NumPy scalars."""
    if container == "tuple":
        spacing: object = (np.int64(2), np.float32(0.3))
        origin: object = (np.int32(1), np.uint64(2))
    elif container == "list":
        spacing = [np.uint16(2), 0.3]
        origin = [1, np.int8(2)]
    elif container in ("array", "readonly-array"):
        spacing = np.array([0.3, 1.5], dtype=">f4")[::-1]
        origin = np.array([2, 1], dtype=">i2")[::-1]
        if container == "readonly-array":
            spacing.flags.writeable = False
            origin.flags.writeable = False
    else:
        spacing = np.array([np.float16(0.3), np.uint16(2)], dtype=object)
        origin = np.array([np.int64(1), np.uint8(2)], dtype=object)
    before = (_snapshot(spacing), _snapshot(origin))
    result = prepare(np.ones((3, 4)), pixel_size_um=spacing, origin_yx=origin, source=LABEL)
    values = cast(Any, spacing)
    converted = (float(values[0]), float(values[1]))
    _check_result(result, np.ones((3, 4)), (1, 2), converted)
    assert (_snapshot(spacing), _snapshot(origin)) == before


@pytest.mark.parametrize(
    "source",
    [None, 3, b"label", [], "", " \t\n\r", "\u2003"],
    ids=["none", "integer", "bytes", "list", "empty", "whitespace", "unicode-whitespace"],
)
def test_reject_source_label(prepare: PrepareOtf, source: object) -> None:
    _reject(prepare, np.array([[1]]), "invalid_otf_source", source=source)


@pytest.mark.parametrize(
    "source", ["x", LABEL, "µm calibration", "not/a/real/file.psf", "\x00opaque"]
)
def test_retain_opaque_source(prepare: PrepareOtf, source: str) -> None:
    _call(prepare, np.array([[1]]), (0, 0), source=source)


@pytest.mark.parametrize(
    "psf",
    [
        np.array([[MAX, MAX]]),
        np.array([[float(Q), 3 * float(Q)]]),
        np.array([[MAX, float(Q)]]),
        np.array([[1, float(Q), 0, 0]]),
    ],
    ids=["raw-sum-overflow", "all-subnormal", "max-versus-q", "one-versus-q"],
)
def test_positive_range_and_cancellation(prepare: PrepareOtf, psf: RealArray) -> None:
    """K21/K22 exact converted ratios; no relative tiny-bin guarantee."""
    _call(prepare, psf, (0, 0))


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((1, 1), (float(Q), MAX)),
        ((1, 1), (MAX, float(Q))),
        ((1, 2), (float(Q), MAX)),
        ((2, 1), (MAX, float(Q))),
        ((3, 6), (MAX, MAX)),
        ((3, 6), (MIN_NORMAL, MAX)),
    ],
    ids=[
        "singleton-q-max",
        "singleton-max-q",
        "singleton-y-huge-x",
        "huge-y-singleton-x",
        "huge-both",
        "tiny-normal-and-huge",
    ],
)
def test_representable_extreme_frequency_grids(
    prepare: PrepareOtf, shape: tuple[int, int], spacing: tuple[float, float]
) -> None:
    """K23 avoid N*d overflow; final subnormal bins stay distinct/nonzero."""
    _call(prepare, np.ones(shape), (0, 0), spacing)


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((2, 1), (float(Q), 1.0)),
        ((1, 2), (1.0, float(Q))),
        ((3, 4), (float(Q), 1.0)),
        ((3, 4), (1.0, float(Q))),
    ],
    ids=["overflow-y-even", "overflow-x-even", "overflow-y-odd", "overflow-x-even-plane"],
)
def test_reject_unrepresentable_frequencies(
    prepare: PrepareOtf, shape: tuple[int, int], spacing: tuple[float, float]
) -> None:
    """K24 positive finite spacing whose exact final frequencies overflow."""
    _reject(prepare, np.ones(shape), "unrepresentable_otf_frequencies", spacing=spacing)


class _ArithmeticObserver:
    def __call__(self, message: str, flag: int) -> None:
        pass

    def write(self, message: str) -> None:
        pass


@contextmanager
def _check_operation_preservation(mode: str, inputs: tuple[object, ...]) -> Iterator[None]:
    """Observe caller inputs, error settings/callback and warnings across an operation."""
    input_before = tuple(_snapshot(value) for value in inputs)
    previous_callback = np.geterrcall()
    observer = _ArithmeticObserver()
    policy = dict.fromkeys(("divide", "over", "under", "invalid"), mode)
    if mode == "mixed":
        policy = {"divide": "raise", "over": "warn", "under": "log", "invalid": "call"}
    np.seterrcall(observer)
    try:
        with np.errstate(**cast(Any, policy)):
            before = np.geterr().copy()
            with warnings.catch_warnings(record=True) as observed:
                warnings.simplefilter("always", RuntimeWarning)
                try:
                    yield
                finally:
                    assert tuple(_snapshot(value) for value in inputs) == input_before, (
                        "operation leaves caller inputs and backing storage unchanged"
                    )
                    assert np.geterr() == before, "operation preserves caller arithmetic policy"
                    assert np.geterrcall() is observer, "operation preserves caller callback"
                    assert not any(issubclass(w.category, RuntimeWarning) for w in observed), (
                        "controlled operation emits no arithmetic RuntimeWarning"
                    )
    finally:
        np.seterrcall(previous_callback)


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log", "mixed"])
@pytest.mark.parametrize(
    "fault",
    ["floating-point", "nan-real", "nan-imag", "inf-real", "inf-imag", "memory", "lookup"],
)
def test_controlled_transform_faults(
    prepare: PrepareOtf, monkeypatch: pytest.MonkeyPatch, mode: str, fault: str
) -> None:
    """K25 public faults paired with real success; K08/K26 apply to both paths."""
    # This name and caller boundary come from the public intake declaration,
    # not source inspection. The collaborator is never invoked directly here.
    module = import_module("simrecon._otf")
    original_binding = getattr(module, "_transform", None)
    assert callable(original_binding), "declared production transform collaborator exists"
    original = cast(Callable[[RealArray, tuple[int, int]], ComplexArray], original_binding)

    _, source_psf, expected_origin = CASES[2]
    backing = np.zeros((8, 12), dtype=np.float64)
    psf = backing[::2, ::2]
    psf[...] = source_psf
    psf.flags.writeable = False
    spacing = np.array([SPACING[1], SPACING[0]], dtype=">f8")[::-1]
    origin = np.array([expected_origin[1], expected_origin[0]], dtype=">i4")[::-1]
    spacing.flags.writeable = False
    origin.flags.writeable = False
    inputs: tuple[object, ...] = (psf, backing, spacing, origin, LABEL)
    success_calls = 0
    fault_calls = 0

    def observe_arguments(working_psf: RealArray, origin_yx: tuple[int, int]) -> None:
        assert isinstance(working_psf, np.ndarray), "declared working array"
        assert working_psf.dtype == np.dtype(np.float64), "declared float64 working dtype"
        assert working_psf.shape == psf.shape, "working array retains supplied grid"
        assert type(origin_yx) is tuple and all(type(value) is int for value in origin_yx), (
            "collaborator receives validated Python-integer origin tuple"
        )
        assert origin_yx == expected_origin, "collaborator receives explicit validated origin"
        # Do not select normalization rounding, an exact sum, or a transform algorithm.

    def successful_transform(working_psf: RealArray, origin_yx: tuple[int, int]) -> ComplexArray:
        nonlocal success_calls
        success_calls += 1
        observe_arguments(working_psf, origin_yx)
        return original(working_psf, origin_yx)

    with monkeypatch.context() as patch:
        patch.setattr(module, "_transform", successful_transform)
        with _check_operation_preservation(mode, inputs):
            result = prepare(psf, pixel_size_um=spacing, origin_yx=origin, source=LABEL)
            assert success_calls > 0, "successful public call invokes declared collaborator"
            _check_result(result, psf, expected_origin)

    injected_exception: Exception | None = None
    if fault == "floating-point":
        injected_exception = FloatingPointError("controlled numerical transform failure")
    elif fault == "memory":
        injected_exception = MemoryError("controlled transform allocation failure")
    elif fault == "lookup":
        injected_exception = LookupError("controlled unrelated transform failure")

    def failed_transform(working_psf: RealArray, origin_yx: tuple[int, int]) -> ComplexArray:
        nonlocal fault_calls
        fault_calls += 1
        observe_arguments(working_psf, origin_yx)
        if injected_exception is not None:
            raise injected_exception
        values = np.zeros(working_psf.shape, dtype=np.complex128)
        nonfinite = {
            "nan-real": complex(float("nan"), 0),
            "nan-imag": complex(0, float("nan")),
            "inf-real": complex(float("inf"), 0),
            "inf-imag": complex(0, float("inf")),
        }
        values[0, -1] = nonfinite[fault]
        return values

    with monkeypatch.context() as patch:
        patch.setattr(module, "_transform", failed_transform)
        with _check_operation_preservation(mode, inputs):
            if fault in ("memory", "lookup"):
                assert injected_exception is not None, "selected propagation example"
                with pytest.raises(type(injected_exception)) as caught:
                    prepare(psf, pixel_size_um=spacing, origin_yx=origin, source=LABEL)
                assert caught.value is injected_exception, (
                    "unrelated/allocation exception propagates"
                )
            else:
                _reject(
                    prepare,
                    psf,
                    "otf_transform_failure",
                    spacing=spacing,
                    origin=origin,
                )
            assert fault_calls > 0, "faulted public call invokes declared collaborator"


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log", "mixed"])
def test_preserve_numpy_error_policy_and_no_runtime_warnings(
    prepare: PrepareOtf, mode: str
) -> None:
    """K26 every supported mode, extremes on success and handled rejection."""
    previous_callback = np.geterrcall()
    observer = _ArithmeticObserver()
    np.seterrcall(observer)
    policy = dict.fromkeys(("divide", "over", "under", "invalid"), mode)
    if mode == "mixed":
        policy = {"divide": "raise", "over": "warn", "under": "log", "invalid": "call"}
    try:
        with np.errstate(**cast(Any, policy)):
            before = np.geterr().copy()
            with warnings.catch_warnings(record=True) as observed:
                warnings.simplefilter("always", RuntimeWarning)
                for psf in (
                    np.array([[MAX, MAX]]),
                    np.array([[float(Q), 3 * float(Q)]]),
                    np.array([[MAX, float(Q)]]),
                ):
                    _call(prepare, psf, (0, 0), (1.0, MAX))
                    assert np.geterr() == before, "success preserves arithmetic policy"
                    assert np.geterrcall() is observer, "success preserves caller callback"
                _reject(
                    prepare,
                    np.array([[1, 2]]),
                    "unrepresentable_otf_frequencies",
                    spacing=(1.0, float(Q)),
                )
                assert np.geterr() == before, "rejection preserves arithmetic policy"
                assert np.geterrcall() is observer, "rejection preserves caller callback"
                assert not any(issubclass(w.category, RuntimeWarning) for w in observed), (
                    "handled arithmetic emits no RuntimeWarning"
                )
    finally:
        np.seterrcall(previous_callback)


@pytest.mark.parametrize(
    "invocation",
    [
        "missing-psf",
        "missing-spacing",
        "missing-origin",
        "missing-source",
        "positional-spacing",
        "all-positional",
        "extra-keyword",
    ],
)
def test_ordinary_python_argument_binding(prepare: PrepareOtf, invocation: str) -> None:
    """K27 TypeError, no custom rejection code/prose requirement."""
    dynamic = cast(Any, prepare)
    psf = np.array([[1]])
    with pytest.raises(TypeError):
        if invocation == "missing-psf":
            dynamic(pixel_size_um=SPACING, origin_yx=(0, 0), source=LABEL)
        elif invocation == "missing-spacing":
            dynamic(psf, origin_yx=(0, 0), source=LABEL)
        elif invocation == "missing-origin":
            dynamic(psf, pixel_size_um=SPACING, source=LABEL)
        elif invocation == "missing-source":
            dynamic(psf, pixel_size_um=SPACING, origin_yx=(0, 0))
        elif invocation == "positional-spacing":
            dynamic(psf, SPACING, origin_yx=(0, 0), source=LABEL)
        elif invocation == "all-positional":
            dynamic(psf, SPACING, (0, 0), LABEL)
        else:
            dynamic(psf, pixel_size_um=SPACING, origin_yx=(0, 0), source=LABEL, extra=1)


def test_preparation_does_not_open_files_or_import_simulator(
    prepare: PrepareOtf, monkeypatch: pytest.MonkeyPatch
) -> None:
    """K28 narrow side-effect smoke; not a dependency/CLI/full-suite verdict."""
    original_import = builtins.__import__

    def blocked_open(*args: object, **kwargs: object) -> Any:
        raise AssertionError("public preparation attempted file access")

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        assert name.split(".")[0] != "pyotf", "preparation imported optical simulator"
        return original_import(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", blocked_open)
        patch.setattr(io, "open", blocked_open)
        patch.setattr(os, "open", blocked_open)
        patch.setattr(Path, "open", blocked_open)
        patch.setattr(builtins, "__import__", guarded_import)
        result = prepare(
            np.array([[1, 2], [3, 4]]),
            pixel_size_um=SPACING,
            origin_yx=(1, 0),
            source="not/a/real/file.psf",
        )
    _check_result(result, np.array([[1, 2], [3, 4]]), (1, 0), source="not/a/real/file.psf")
