"""Blind public-contract tests for VOLUME-RECOMBINE-01 (W01–W26)."""

import warnings
from dataclasses import fields, is_dataclass
from decimal import Decimal as D
from decimal import localcontext
from itertools import combinations
from types import SimpleNamespace
from typing import Any, Literal, cast

import numpy as np
import pytest

from volume_reconstruction_fixture import (
    accuracy_bounds,
    assert_complex_error,
    assert_informative_regime,
    assert_phase_accuracy,
    basis,
    call,
    coordinates,
    decimal,
    direct_oracle,
    effective_order_mode,
    input_arrays,
    make_case,
    make_record,
    modes,
    root,
)


@pytest.fixture
def reconstruct() -> Any:
    # Lazy resolution leaves collection and oracle validation independent of feature absence.
    import simrecon

    return cast(Any, simrecon).reconstruct_volume


def replace_record(record: Any, **changes: Any) -> Any:
    from simrecon import VolumeOrderOtf

    data = {
        key: getattr(record, key)
        for key in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }
    return VolumeOrderOtf(**(data | changes))


def assert_error(reconstruct: Any, case: dict[str, Any], code: str | tuple[str, ...]) -> None:
    from simrecon import SimreconError

    arrays = input_arrays(case) if isinstance(case["order_otfs"], (list, tuple)) else []
    before = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
        warnings.simplefilter("always", RuntimeWarning)
        with pytest.raises(SimreconError) as exc:
            call(reconstruct, case)
    assert isinstance(exc.value, ValueError)
    assert exc.value.code in ((code,) if isinstance(code, str) else code)
    assert isinstance(exc.value.message, str)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    for a, (value, strides, writable) in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(a, value)
        assert a.strides == strides and a.flags.writeable == writable


def accuracy_expectation(case: dict[str, Any]) -> tuple[Any, tuple[D, D]]:
    assert_informative_regime(case)
    return direct_oracle(case, 75, decimal_output=True), accuracy_bounds(case)


def assert_result_accuracy(result: Any, expected: Any, budgets: tuple[D, D]) -> None:
    for got, want, budget in zip((result.spectrum, result.volume), expected, budgets, strict=True):
        assert got.shape == want.shape
        for actual, exact in zip(got.flat, want.flat, strict=True):
            assert_complex_error(actual, exact, budget)


def compare(reconstruct: Any, case: dict[str, Any]) -> Any:
    expected, budgets = accuracy_expectation(case)
    result = call(reconstruct, case)
    assert_result_accuracy(result, expected, budgets)
    return result


def dc_case(
    shape: tuple[int, int, int] = (1, 1, 4), output: tuple[int, int] = (1, 8)
) -> dict[str, Any]:
    case = make_case(shape, ((0, 0),), n=5)
    case["images"][:] = 1
    values = np.zeros((3, *shape), dtype=np.complex128)
    values[0] = 1
    case.update(
        order_otfs=[make_record(values)],
        gains=np.ones(1),
        regularization=0.0,
        output_shape_yx=output,
        apodization=np.ones((shape[0], *output)),
    )
    return case


def assert_constant_restoration(result: Any, case: dict[str, Any], intensity: float) -> None:
    """Check analytic brightness of the selected constant fixture without floating overflow."""
    unit_case = case | {"images": np.ones_like(case["images"], dtype=np.float64)}
    assert_informative_regime(unit_case)
    with localcontext() as ctx:
        ctx.prec = 90
        # Conservative margins for this homogeneous identity-DC problem only.
        # They exceed separator/normalized-transform roundoff and retain the input scale.
        beta_s, beta_v = (v * decimal(intensity) for v in accuracy_bounds(unit_case))
        shape = (case["images"].shape[2], *case["output_shape_yx"])
        assert result.spectrum.shape == result.volume.shape == shape
        dc_index = tuple(k // 2 for k in shape)
        for index in np.ndindex(shape):
            spectrum_exact = (decimal(intensity) if index == dc_index else D(0), D(0))
            assert_complex_error(result.spectrum[index], spectrum_exact, beta_s)
            assert_complex_error(result.volume[index], (decimal(intensity), D(0)), beta_v)


def test_oracle_budgeted_coherent_perturbation_and_wrong_outcomes() -> None:
    case = make_case((1, 1, 3), ((0, 0), (0, 0)))
    case["regularization"] = 0.125  # retain the exact public counterexample's fixture
    spectrum, volume = direct_oracle(case)
    spectrum[0, 0, 1] += 1e-10
    volume += 1e-10  # changing DC by delta changes every synthesis sample by delta
    permitted = SimpleNamespace(spectrum=spectrum, volume=volume)
    compare(lambda *args, **kwargs: permitted, case)
    for wrong in (
        SimpleNamespace(spectrum=-spectrum, volume=-volume),
        SimpleNamespace(spectrum=2 * spectrum, volume=2 * volume),
        SimpleNamespace(spectrum=spectrum.conjugate(), volume=volume.conjugate()),
    ):
        with pytest.raises(AssertionError):
            compare(lambda *args, value=wrong, **kwargs: value, case)


def test_oracle_large_constant_restoration_observer() -> None:
    case = dc_case((2, 8, 8), (8, 16))
    intensity = np.finfo(float).max / 64
    case["images"][:] = intensity
    shape = (2, 8, 16)
    spectrum = np.zeros(shape, dtype=np.complex128)
    spectrum[1, 4, 8] = intensity
    correct = SimpleNamespace(
        spectrum=spectrum, volume=np.full(shape, intensity, dtype=np.complex128)
    )
    assert_constant_restoration(correct, case, intensity)
    for wrong_scale in (1.0, intensity / 128, intensity / 256):
        wrong_spectrum = np.zeros(shape, dtype=np.complex128)
        wrong_spectrum[1, 4, 8] = wrong_scale
        wrong = SimpleNamespace(
            spectrum=wrong_spectrum, volume=np.full(shape, wrong_scale, dtype=np.complex128)
        )
        with pytest.raises(AssertionError):
            assert_constant_restoration(wrong, case, intensity)


def test_oracle_roots_and_exact_stored_ls() -> None:
    with localcontext() as ctx:
        ctx.prec = 70
        assert abs(root(D("0.25"), 70)[0]) < D("1e-69")
        assert abs(root(D("0.25"), 70)[1] - 1) < D("1e-69")
        phi = np.array([0.0, 0.7, 1.8, 2.9, 4.0, 5.2, 6.0])
        h = basis(phi)
        stored = (h @ np.array([10.0, 4, 2, 6, -8]))[:, None, None, None]
        bands = coordinates(stored, phi)[(0, 0, 0)]
        for got, want in zip(bands, ((10, 0), (2, -1), (3, 4)), strict=True):
            assert max(abs(got[i] - D(want[i])) for i in (0, 1)) < D("2e-14")


def test_oracle_precision_convergence_and_analytic_nyquist() -> None:
    case = make_case((2, 2, 3), ((1, 0), (-1, 0)))
    a, b = direct_oracle(case, 55), direct_oracle(case, 75)
    for x, y in zip(a, b, strict=True):
        np.testing.assert_array_equal(x, y)
    case = dc_case()
    case["images"][:] = np.array([1, -1, 1, -1])
    spectrum, volume = direct_oracle(case)
    assert abs(spectrum[0, 0, 2] - 1) < 1e-14
    np.testing.assert_allclose(
        volume[0, 0], np.exp(-2j * np.pi * 2 * np.arange(8) / 8), rtol=0, atol=2e-14
    )


@pytest.mark.parametrize(
    "shape,carriers",
    [
        ((2, 3, 4), ((1, -1), (-1, 1))),
        ((3, 2, 1), ((-1, 0), (-1, 0))),
        ((1, 1, 3), ((0, 0), (0, 0))),
        ((1, 2, 2), ((0, 1), (0, -1))),
    ],
)
def test_five_order_direct_estimator(reconstruct: Any, shape: Any, carriers: Any) -> None:
    case = make_case(shape, carriers)
    compare(reconstruct, case)
    # N>5 observations deliberately include a nonzero off-model residual.
    h = basis(case["phases_rad"][0])
    b = case["images"][0, :, 0, 0, 0]
    fitted = h @ np.linalg.lstsq(h, b, rcond=None)[0]
    assert np.linalg.norm(fitted - b) > 1e-4


def test_nyquist_remains_complex_single_signed_lift(reconstruct: Any) -> None:
    case = dc_case()
    case["images"][:] = np.array([1, -1, 1, -1])
    result = compare(reconstruct, case)
    beta_s, beta_v = accuracy_bounds(case)
    assert_complex_error(result.volume[0, 0, 1], (D(0), D(-1)), beta_v)
    assert_complex_error(result.spectrum[0, 0, 6], (D(0), D(0)), beta_s)


@pytest.mark.parametrize("ridge", [0, np.float32(0.5), np.int64(1)])
def test_ridge_mask_zero_denominator_and_zero_sides(reconstruct: Any, ridge: Any) -> None:
    case = dc_case()
    case["regularization"] = ridge
    case["apodization"][:] = 0.25
    compare(reconstruct, case)
    case["order_otfs"][0].values[:] = 0
    result = call(reconstruct, case)
    assert np.count_nonzero(result.spectrum) == np.count_nonzero(result.volume) == 0


def test_gauge_gain_and_origin_encoded_once(reconstruct: Any) -> None:
    case = make_case((2, 2, 3), ((0, 1),))
    compare(reconstruct, case)
    # Changing opaque origin/source metadata alone must not rephase supplied values.
    record = case["order_otfs"][0]
    case["order_otfs"] = [replace_record(record, origin_zyx=(0, 1, 0), source="other label")]
    compare(reconstruct, case)
    # Gauge shifts are represented jointly in data and E_m, not inferred by reconstruction.
    theta = 0.37
    h = basis(case["phases_rad"][0])
    coefficients = np.array([1.0, 0.3, -0.2, 0.4, 0.1])
    base = dc_case((1, 1, 1), (1, 1))
    base["images"][0, :, 0, 0, 0] = basis(base["phases_rad"][0]) @ coefficients
    base["order_otfs"][0].values[:] = np.array([1, 0.7 + 0.2j, -0.3 + 0.4j])[:, None, None, None]
    compare(reconstruct, base)
    for m in (1, 2):
        band = (coefficients[2 * m - 1] - 1j * coefficients[2 * m]) / 2 * np.exp(1j * m * theta)
        coefficients[2 * m - 1], coefficients[2 * m] = 2 * band.real, -2 * band.imag
        base["order_otfs"][0].values[m] *= np.exp(1j * m * theta)
    base["images"][0, :, 0, 0, 0] = basis(base["phases_rad"][0]) @ coefficients
    compare(reconstruct, base)
    assert h.shape[1] == 5


@pytest.mark.parametrize("key", ["images", "phases_rad", "gains", "apodization"])
@pytest.mark.parametrize(
    "dtype",
    [
        np.int8,
        np.uint8,
        np.int16,
        np.uint16,
        np.int32,
        np.uint32,
        np.int64,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        np.longdouble,
        ">f8",
        ">i4",
    ],
)
def test_real_widths_endian_and_converted_truth(reconstruct: Any, key: str, dtype: Any) -> None:
    case = dc_case((1, 2, 2), (2, 2))
    if key == "phases_rad" and np.dtype(dtype).kind in "iu":
        case[key] = np.array([[0, 1, 2, 3, 4]], dtype=dtype)
    else:
        case[key] = case[key].astype(dtype)
    if key == "images" and np.dtype(dtype).kind == "u":
        case[key][:] = np.iinfo(dtype).max
    # Integer extrema are compared after float64 conversion, never unrounded truth.
    compare(reconstruct, case)


@pytest.mark.parametrize("layout", ["fortran", "strided", "readonly", "big_endian"])
def test_all_inputs_and_calibration_storage_alternatives(reconstruct: Any, layout: str) -> None:
    case = make_case((1, 2, 3), ((0, 1),))

    def convert(a: Any) -> Any:
        if layout == "fortran":
            return np.asfortranarray(a)
        if layout == "strided":
            holder = np.empty((*a.shape[:-1], a.shape[-1] * 2), dtype=a.dtype)
            holder[..., ::2] = a
            return holder[..., ::2]
        if layout == "readonly":
            a = a.copy()
            a.flags.writeable = False
            return a
        return a.astype(a.dtype.newbyteorder(">"))

    for key in ("images", "phases_rad", "carriers_bins", "gains", "apodization"):
        case[key] = convert(case[key])
    case["order_otfs"] = [
        replace_record(
            rec,
            **{
                key: convert(getattr(rec, key))
                for key in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
            },
            voxel_size_um=list(rec.voxel_size_um),
            origin_zyx=list(rec.origin_zyx),
        )
        for rec in case["order_otfs"]
    ]
    before = [(a.copy(), a.strides, a.flags.writeable) for a in input_arrays(case)]
    compare(reconstruct, case)
    for a, (value, strides, writable) in zip(input_arrays(case), before, strict=True):
        np.testing.assert_array_equal(a, value)
        assert a.strides == strides and a.flags.writeable == writable


class ArraySubclass(np.ndarray):
    """Forbidden ndarray subtype used only in representation rejection examples."""


def invalid_value(case: dict[str, Any], key: str, variant: str) -> Any:
    a = case[key]
    if variant == "list":
        return a.tolist()
    if variant == "subclass":
        return a.view(ArraySubclass)
    if variant == "masked":
        return np.ma.array(a)
    if variant in ("bool", "complex", "object", "string", "datetime", "structured"):
        dtype = {
            "bool": "?",
            "complex": "c16",
            "object": "O",
            "string": "U4",
            "datetime": "datetime64[D]",
            "structured": [("a", "f8")],
        }[variant]
        # Isolate forbidden gain representation from the strictly positive value rule.
        if key == "gains":
            return np.full(a.shape, 1, dtype=dtype)
        return np.zeros(a.shape, dtype=dtype)
    if variant == "shape":
        return a.reshape(-1)
    if variant in ("nan", "inf", "-inf", "negative", "zero", "above"):
        a = a.copy()
        a.flat[0] = {
            "nan": np.nan,
            "inf": np.inf,
            "-inf": -np.inf,
            "negative": -0.1,
            "zero": 0,
            "above": 1.01,
        }[variant]
        return a
    raise AssertionError("unknown authored invalid example")


@pytest.mark.parametrize(
    "key,code",
    [
        ("images", "invalid_volume_reconstruction_images"),
        ("phases_rad", "invalid_volume_reconstruction_phases"),
        ("carriers_bins", "invalid_volume_reconstruction_carriers"),
        ("gains", "invalid_volume_reconstruction_gains"),
        ("apodization", "invalid_volume_reconstruction_apodization"),
    ],
)
@pytest.mark.parametrize("variant", ["list", "subclass", "masked"])
def test_plain_array_rejections(reconstruct: Any, key: str, code: str, variant: str) -> None:
    case = dc_case()
    case[key] = invalid_value(case, key, variant)
    assert_error(reconstruct, case, code)


@pytest.mark.parametrize(
    "key,code",
    [
        ("images", "invalid_volume_reconstruction_dtype"),
        ("phases_rad", "invalid_volume_reconstruction_phases"),
        ("carriers_bins", "invalid_volume_reconstruction_carriers"),
        ("gains", "invalid_volume_reconstruction_gains"),
        ("apodization", "invalid_volume_reconstruction_apodization"),
    ],
)
@pytest.mark.parametrize(
    "variant", ["bool", "complex", "object", "string", "datetime", "structured"]
)
def test_array_dtype_rejections(reconstruct: Any, key: str, code: str, variant: str) -> None:
    case = dc_case()
    case[key] = invalid_value(case, key, variant)
    assert_error(reconstruct, case, code)


@pytest.mark.parametrize(
    "key,code",
    [
        ("images", "nonfinite_volume_reconstruction_images"),
        ("phases_rad", "nonfinite_volume_reconstruction_phases"),
        ("gains", "invalid_volume_reconstruction_gain_values"),
        ("apodization", "invalid_volume_reconstruction_apodization_values"),
    ],
)
@pytest.mark.parametrize("variant", ["nan", "inf", "-inf"])
def test_nonfinite_source_rejections(reconstruct: Any, key: str, code: str, variant: str) -> None:
    case = dc_case()
    case[key] = invalid_value(case, key, variant)
    assert_error(reconstruct, case, code)


@pytest.mark.parametrize(
    "key,code",
    [
        ("phases_rad", "invalid_volume_reconstruction_phases"),
        ("carriers_bins", "invalid_volume_reconstruction_carriers"),
        ("gains", "invalid_volume_reconstruction_gains"),
        ("apodization", "invalid_volume_reconstruction_apodization"),
    ],
)
def test_array_shape_rejections(reconstruct: Any, key: str, code: str) -> None:
    case = dc_case()
    # Deterministic finite values avoid a simultaneous gain/mask value violation.
    case[key] = np.ones((2, 3, 4))
    assert_error(reconstruct, case, code)


@pytest.mark.parametrize(
    "shape",
    [
        (5, 1, 1, 4),
        (0, 5, 1, 1, 4),
        (1, 4, 1, 1, 4),
        (1, 5, 0, 1, 4),
        (1, 5, 1, 0, 4),
        (1, 5, 1, 1, 0),
        (1, 5, 1, 1, 4, 1),
    ],
)
def test_image_shape_rejections(reconstruct: Any, shape: Any) -> None:
    case = dc_case()
    case["images"] = np.zeros(shape)
    codes = ("invalid_volume_reconstruction_shape",)
    if len(shape) == 5:
        r, n, nz, ny, nx = shape
        case["phases_rad"] = np.tile(np.arange(n, dtype=float), (r, 1))
        case["gains"] = np.ones(r)
        case["carriers_bins"] = np.zeros((r, 2), dtype=np.int64)
        case["order_otfs"] = case["order_otfs"] * r
        case["apodization"] = np.ones((nz, *case["output_shape_yx"]))
        # Empty detector axes cannot have an in-bounds calibration origin.
        # The shape and incompatible-calibration obligations both fail; no precedence is selected.
        if min(nz, ny, nx) == 0:
            codes += ("invalid_volume_reconstruction_otfs",)
    assert_error(reconstruct, case, codes)


@pytest.mark.parametrize(
    "key,variant,code",
    [
        ("gains", "zero", "invalid_volume_reconstruction_gain_values"),
        ("gains", "negative", "invalid_volume_reconstruction_gain_values"),
        ("apodization", "negative", "invalid_volume_reconstruction_apodization_values"),
        ("apodization", "above", "invalid_volume_reconstruction_apodization_values"),
    ],
)
def test_gain_and_mask_value_boundaries(
    reconstruct: Any, key: str, variant: str, code: str
) -> None:
    case = dc_case()
    case[key] = invalid_value(case, key, variant)
    assert_error(reconstruct, case, code)


@pytest.mark.parametrize(
    "value", [True, np.bool_(False), 1j, "0", [0], np.array(0.0), -1, np.inf, np.nan]
)
def test_regularization_rejections(reconstruct: Any, value: Any) -> None:
    case = dc_case()
    case["regularization"] = value
    assert_error(reconstruct, case, "invalid_volume_reconstruction_regularization")


@pytest.mark.parametrize(
    "value",
    [
        (1,),
        (1, 8, 9),
        np.array([1, 8]),
        (True, 8),
        (1, 8.0),
        (0, 8),
        (-1, 8),
        (1, int(np.iinfo(np.intp).max) + 1),
    ],
)
def test_output_shape_representation(reconstruct: Any, value: Any) -> None:
    case = dc_case()
    case["output_shape_yx"] = value
    codes = ("invalid_volume_reconstruction_output_shape",)
    if (
        type(value) in (tuple, list)
        and len(value) == 2
        and all(
            isinstance(v, (int, np.integer)) and not isinstance(v, (bool, np.bool_)) for v in value
        )
        and tuple(value) != case["apodization"].shape[1:]
    ):
        codes += ("invalid_volume_reconstruction_apodization",)
    assert_error(reconstruct, case, codes)


@pytest.mark.parametrize("axis", [0, 1])
def test_complete_window_even_for_zero_transfers_and_mask(reconstruct: Any, axis: int) -> None:
    case = make_case((1, 2, 4), ((-2, 1),))
    case["order_otfs"][0].values[:] = 0
    size = list(case["output_shape_yx"])
    size[axis] -= 1
    case["output_shape_yx"] = size
    case["apodization"] = np.zeros((1, *size))
    assert_error(reconstruct, case, "invalid_volume_reconstruction_output_shape")


def test_exact_carriers_and_no_practical_output_cap(reconstruct: Any) -> None:
    case = dc_case((1, 1, 1), (1, 1025))
    case["output_shape_yx"] = [np.int64(1), np.uint64(1025)]
    case["carriers_bins"] = np.zeros((1, 2), dtype=np.uint64)
    compare(reconstruct, case)
    case["carriers_bins"][0, 1] = np.iinfo(np.uint64).max
    assert_error(reconstruct, case, "invalid_volume_reconstruction_output_shape")
    case["carriers_bins"] = np.zeros((1, 2), dtype=float)
    assert_error(reconstruct, case, "invalid_volume_reconstruction_carriers")


@pytest.mark.parametrize(
    "variant",
    [
        "container",
        "count",
        "record",
        "values_list",
        "values_subclass",
        "values_dtype",
        "values_shape",
        "values_nan",
        "values_inf_imag",
        "frequency_list",
        "frequency_dtype",
        "frequency_shape",
        "frequency_nan",
        "frequency_noncanonical",
        "frequency_zero",
        "frequency_reverse",
        "spacing_container",
        "spacing_bool",
        "spacing_zero",
        "spacing_inf",
        "origin_container",
        "origin_float",
        "origin_bool",
        "origin_bounds",
        "source_type",
        "source_blank",
        "spacing_mismatch",
    ],
)
def test_direct_record_full_validation(reconstruct: Any, variant: str) -> None:
    case = make_case((2, 3, 4), ((0, 0), (0, 0)))
    # Mask/side values cannot waive record validation.
    case["apodization"][:] = 0
    rec = case["order_otfs"][0]
    if variant in ("container", "count", "record"):
        case["order_otfs"] = {
            "container": np.array(case["order_otfs"], dtype=object),
            "count": [rec],
            "record": [object(), rec],
        }[variant]
    else:
        values = rec.values.copy()
        frequency = rec.fx_per_um.copy()
        changes: dict[str, Any] = {}
        if variant.startswith("values_"):
            if variant == "values_list":
                values = values.tolist()
            elif variant == "values_subclass":
                values = values.view(ArraySubclass)
            elif variant == "values_dtype":
                values = values.astype(np.complex64)
            elif variant == "values_shape":
                values = values[:2]
            else:
                values.flat[0] = np.nan if variant == "values_nan" else complex(0, np.inf)
            changes["values"] = values
        elif variant.startswith("frequency_"):
            if variant == "frequency_list":
                frequency = frequency.tolist()
            elif variant == "frequency_dtype":
                frequency = frequency.astype(np.float32)
            elif variant == "frequency_shape":
                frequency = frequency[:, None]
            elif variant == "frequency_reverse":
                frequency = frequency[::-1]
            else:
                frequency[0 if variant != "frequency_zero" else 2] = {
                    "frequency_nan": np.nan,
                    "frequency_noncanonical": frequency[0] + 1e-4,
                    "frequency_zero": 1e-10,
                }[variant]
            changes["fx_per_um"] = frequency
        else:
            changes = {
                "spacing_container": {"voxel_size_um": np.array(rec.voxel_size_um)},
                "spacing_bool": {"voxel_size_um": (True, 1.3, 0.4)},
                "spacing_zero": {"voxel_size_um": (0, 1.3, 0.4)},
                "spacing_inf": {"voxel_size_um": (np.inf, 1.3, 0.4)},
                "origin_container": {"origin_zyx": np.array([0, 0, 0])},
                "origin_float": {"origin_zyx": (0, 0, 0.0)},
                "origin_bool": {"origin_zyx": (False, 0, 0)},
                "origin_bounds": {"origin_zyx": (2, 0, 0)},
                "source_type": {"source": 1},
                "source_blank": {"source": "  "},
                "spacing_mismatch": {"voxel_size_um": (0.8, 1.3, 0.4)},
            }[variant]
            if variant == "spacing_mismatch":
                changes["fz_per_um"] = np.array(
                    [float(D(j) / D(2) / decimal(0.8)) for j in modes(2)]
                )
        case["order_otfs"][0] = replace_record(rec, **changes)
    assert_error(reconstruct, case, "invalid_volume_reconstruction_otfs")


def test_frequency_validation_budget_permitted_positive(reconstruct: Any) -> None:
    case = dc_case()
    rec = case["order_otfs"][0]
    fx = rec.fx_per_um.copy()
    fx[0] = np.nextafter(fx[0], -np.inf)
    case["order_otfs"] = (
        replace_record(
            rec,
            fx_per_um=fx,
            voxel_size_um=[np.float64(0.7), np.float32(1.3), np.float64(0.4)],
            fy_per_um=np.zeros(1),
        ),
    )
    # Singleton y has no nonzero frequency; float32 converted spacing is valid.
    call(reconstruct, case)


def test_record_ownership_fields_mutability_and_coordinates(reconstruct: Any) -> None:
    import simrecon

    case = make_case((2, 3, 4), ((1, -1),))
    result, other = call(reconstruct, case), call(reconstruct, case)
    record_type = cast(Any, simrecon).Reconstruction3D
    assert isinstance(result, record_type)
    names = ("volume", "spectrum", "fz_per_um", "fy_per_um", "fx_per_um", "voxel_size_um")
    assert all(hasattr(result, name) for name in names)
    if is_dataclass(type(result)):
        assert {f.name for f in fields(result)} == set(names)
    output_arrays = [getattr(result, key) for key in names[:-1]]
    for key in names:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, key, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, key)
    for index, a in enumerate(output_arrays):
        assert a.dtype == np.dtype("complex128" if index < 2 else "float64")
        assert a.dtype.isnative and a.flags.c_contiguous and a.flags.owndata and a.flags.writeable
    for a, b in combinations(
        output_arrays + input_arrays(case) + [getattr(other, key) for key in names[:-1]], 2
    ):
        if any(a is out or b is out for out in output_arrays):
            assert not np.shares_memory(a, b)
    nz, ny, nx = case["images"].shape[-3:]
    ly, lx = case["output_shape_yx"]
    dz, dy, dx = case["order_otfs"][0].voxel_size_um
    assert result.voxel_size_um == (dz, float(ny * dy / ly), float(nx * dx / lx))
    assert all(type(v) is float for v in result.voxel_size_um)
    with localcontext() as ctx:
        ctx.prec = 90
        for vector, length, field_length, spacing in zip(
            output_arrays[2:], (nz, ly, lx), (nz, ny, nx), (dz, dy, dx), strict=True
        ):
            assert vector.shape == (length,)
            assert vector[length // 2] == 0
            assert np.all(np.diff(vector) > 0)
            for value, mode in zip(vector, modes(length), strict=True):
                exact = D(mode) / D(field_length) / decimal(spacing)
                assert abs(decimal(value) - exact) <= 8 * D(2) ** -52 * abs(exact) + D(2) ** -1074
    saved = other.volume.copy()
    result.volume.flat[0] = 123 + 456j
    np.testing.assert_array_equal(other.volume, saved)
    # Direct construction has no validation duty.
    direct = record_type(**dict.fromkeys(names, None))
    assert direct.volume is None


@pytest.mark.parametrize(
    "spacing,output,code",
    [
        ((np.nextafter(0.0, 1.0), 1.0, 1.0), (1, 1), None),
        ((np.finfo(float).max, np.finfo(float).max, np.finfo(float).max), (2, 2), None),
        ((1.0, 1.0, np.nextafter(0.0, 1.0)), (1, 2), "unrepresentable_volume_reconstruction_grid"),
        ((1.0, 1.0, 1e-308), (1, 8), "unrepresentable_volume_reconstruction_grid"),
    ],
)
def test_extreme_output_grid(reconstruct: Any, spacing: Any, output: Any, code: Any) -> None:
    case = dc_case((1, 1, 1), output)
    case["order_otfs"] = [make_record(case["order_otfs"][0].values, spacing=spacing)]
    if code:
        assert_error(reconstruct, case, code)
    else:
        result = compare(reconstruct, case)
        assert all(
            np.isfinite(getattr(result, key)).all()
            for key in ("fz_per_um", "fy_per_um", "fx_per_um")
        )


def test_phase_dependency_rank_solver_and_range_codes(reconstruct: Any, monkeypatch: Any) -> None:
    case = dc_case((1, 1, 1), (1, 1))
    case["phases_rad"][:] = 0
    assert_error(reconstruct, case, "rank_deficient_volume_phases")
    case = dc_case((1, 1, 1), (1, 1))

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise np.linalg.LinAlgError("controlled phase dependency")

    with monkeypatch.context() as patch:
        patch.setattr(np.linalg, "lstsq", fail)
        patch.setattr(np.linalg, "svd", fail)
        assert_error(reconstruct, case, "volume_phase_solver_failure")
    case["phases_rad"] = np.array([[0, 0.01, 0.02, 0.03, 0.04]])
    case["images"][0, :, 0, 0, 0] = np.array([1, -1, 1, -1, 1]) * (np.finfo(float).max / 32)
    assert_error(reconstruct, case, "unrepresentable_volume_phase_components")


def test_separator_composition_and_joint_permutation(reconstruct: Any) -> None:
    from simrecon import separate_volume_phases

    case = make_case((2, 2, 3), ((0, -1),))
    separated = separate_volume_phases(case["images"][0], phases_rad=case["phases_rad"][0])
    assert_phase_accuracy(case["images"][0], case["phases_rad"][0], separated)
    compare(reconstruct, case)
    order = [6, 2, 0, 5, 1, 4, 3]
    case["images"] = case["images"][:, order]
    case["phases_rad"] = case["phases_rad"][:, order]
    compare(reconstruct, case)


def composition_case() -> dict[str, Any]:
    from simrecon import prepare_volume_order_otfs, separate_volume_phases

    # Uniform detection kernel has only DC. g2 shifts its axial support to kz=1.
    # Specimen q=(1,0,4), carrier x=-2: order +2 reaches detector j=(1,0,0).
    # qx=4 lies outside detector window [-2,2]; g0=1 alone cannot observe this mode.
    nz, nx = 3, 5
    psf = np.ones((nz, 1, nx))
    g = np.zeros((2, nz), dtype=np.complex128)
    g[1] = 0.8 * np.exp(2j * np.pi * np.arange(nz) / nz)
    calibration = prepare_volume_order_otfs(
        psf,
        axial_coefficients=g,
        voxel_size_um=(0.7, 1.3, 0.4),
        origin_zyx=(0, 0, 0),
        source="finite circular focal-plane-relative example",
    )
    phase = np.array([0.05, 0.82, 1.9, 2.71, 3.48, 4.65, 5.61])
    z, x = np.indices((nz, nx))
    specimen = 1 + 0.2 * np.cos(2 * np.pi * (z / nz + 4 * x / nx) + 0.3)
    kernels = [
        psf / psf.sum(),
        psf / psf.sum() * g[0, :, None, None],
        psf / psf.sum() * g[1, :, None, None],
    ]
    components = []
    for m, kernel in enumerate(kernels):
        modulated = specimen[:, None, :] * np.exp(2j * np.pi * m * (-2) * x[:, None, :] / nx)
        filtered = np.zeros_like(modulated, dtype=np.complex128)
        for displacement in np.ndindex(psf.shape):
            filtered += kernel[displacement] * np.roll(modulated, displacement, axis=(0, 1, 2))
        components.append(filtered)
    h = basis(phase)
    data = (
        components[0].real[None]
        + 2 * components[1].real[None] * h[:, 1, None, None, None]
        - 2 * components[1].imag[None] * h[:, 2, None, None, None]
        + 2 * components[2].real[None] * h[:, 3, None, None, None]
        - 2 * components[2].imag[None] * h[:, 4, None, None, None]
    )
    separated = separate_volume_phases(data, phases_rad=phase)
    assert_phase_accuracy(data, phase, separated)
    case = dict(
        images=data[None],
        order_otfs=[calibration],
        phases_rad=phase[None],
        carriers_bins=np.array([[0, -2]]),
        gains=np.ones(1),
        regularization=0.25,
        output_shape_yx=(1, 13),
        apodization=np.ones((3, 1, 13)),
    )
    with localcontext() as ctx:
        ctx.prec = 90
        m = D(psf.size)
        eps, tiny = D(2) ** -52, D(2) ** -1074
        assert_complex_error(
            calibration.values[0, 2, 0, 2], (D(0), D(0)), 128 * m * eps + 4 * m * tiny
        )
        gain = max(abs(decimal(v)) for v in np.concatenate((g[1].real, g[1].imag)))
        assert_complex_error(
            calibration.values[2, 2, 0, 2],
            effective_order_mode(psf, g[1], (1, 0, 0)),
            256 * m * eps * gain + 8 * m * tiny,
        )
    return case


def test_oracle_actual_forward_fixture_and_second_order_information() -> None:
    spectrum, _ = direct_oracle(composition_case())
    # Ridge biases the mode. This is stored-input agreement, not universal recovery.
    expected = (0.1 * np.exp(0.3j)) * 0.8**2 / (0.8**2 + 0.25)
    assert abs(spectrum[2, 0, 10] - expected) < 3e-13


def test_actual_effective_transfer_forward_composition_second_order_information(
    reconstruct: Any,
) -> None:
    result = compare(reconstruct, composition_case())
    assert abs(result.spectrum[2, 0, 10]) > 0.05


def test_inputs_snapshotted_before_transform_and_caller_policy_preserved(
    reconstruct: Any, monkeypatch: Any
) -> None:
    case = make_case((1, 2, 3), ((0, 1),))
    expected, budgets = accuracy_expectation(case)
    arrays = input_arrays(case)
    original = np.fft.fftn
    touched = False

    def observing(a: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal touched
        if not touched:
            touched = True
            for source in arrays:
                source[...] = 0
        return original(a, *args, **kwargs)

    old_filters = list(warnings.filters)
    with np.errstate(all="raise"):
        policy = np.geterr().copy()
        with monkeypatch.context() as patch:
            patch.setattr(np.fft, "fftn", observing)
            result = call(reconstruct, case)
        assert np.geterr() == policy and warnings.filters == old_filters
    assert touched
    assert_result_accuracy(result, expected, budgets)


@pytest.mark.parametrize("scale", [0.0, np.nextafter(0.0, 1.0), 1e-300, 1.0])
def test_informative_accuracy_zero_subnormal_mandatory_success(
    reconstruct: Any, scale: float
) -> None:
    case = make_case((1, 2, 3), ((0, 0),))
    case["images"] *= scale
    case["regularization"] = 0.5  # positive denominator everywhere >=1/4
    result = compare(reconstruct, case)
    if scale == 0:
        assert np.count_nonzero(result.spectrum) == np.count_nonzero(result.volume) == 0


def test_safe_large_components_transform_scaling(reconstruct: Any) -> None:
    case = dc_case((2, 8, 8), (8, 16))
    intensity = np.finfo(float).max / 64
    case["images"][:] = intensity
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = call(reconstruct, case)
    assert not caught
    # Specific analytic restoration obligation; no general out-of-regime budget.
    assert_constant_restoration(result, case, intensity)


@pytest.mark.parametrize(
    "stage",
    ["gain_transfer", "square", "sum", "product", "quotient_zero_mask", "quotient_tiny_mask"],
)
def test_operational_range_no_mask_rescue(reconstruct: Any, stage: str) -> None:
    case = dc_case((1, 1, 1), (1, 1))
    values = case["order_otfs"][0].values
    if stage == "gain_transfer":
        values[0] = 2
        case["gains"][0] = np.finfo(float).max
        case["images"][:] = 0  # zero data does not waive range outside informative regime
    elif stage == "square":
        values[0] = 1e200
    elif stage == "sum":
        values[:] = 1e154
    elif stage == "product":
        values[0] = 4
        case["images"][:] = np.finfo(float).max / 2
    else:
        values[0] = 1e-160
        case["images"][:] = 1e160
        case["apodization"][:] = 0 if stage == "quotient_zero_mask" else np.nextafter(0.0, 1.0)
    assert_error(reconstruct, case, "unrepresentable_volume_reconstruction")


@pytest.mark.parametrize("seam", ["fftn", "ifftn"])
@pytest.mark.parametrize("failure", ["floating", "overflow", "warning", "nan", "inf"])
@pytest.mark.parametrize("filter_mode", ["always", "ignore"])
def test_handled_transform_failures(
    reconstruct: Any,
    monkeypatch: Any,
    seam: str,
    failure: str,
    filter_mode: Literal["always", "ignore"],
) -> None:
    case = make_case((1, 2, 3), ((0, 0),))
    original = getattr(np.fft, seam)

    def failing(a: Any, *args: Any, **kwargs: Any) -> Any:
        if failure == "floating":
            raise FloatingPointError("controlled FFT arithmetic")
        if failure == "overflow":
            raise OverflowError("controlled FFT arithmetic")
        if failure == "warning":
            warnings.warn("controlled FFT arithmetic", RuntimeWarning, stacklevel=2)
        output = original(a, *args, **kwargs)
        if failure in ("nan", "inf"):
            output = output.copy()
            output.flat[0] = np.nan if failure == "nan" else complex(0, np.inf)
        return output

    from simrecon import SimreconError

    arrays = input_arrays(case)
    snapshots = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter(filter_mode, RuntimeWarning)
        policy, filters = np.geterr().copy(), list(warnings.filters)
        with monkeypatch.context() as patch:
            patch.setattr(np.fft, seam, failing)
            with pytest.raises(SimreconError) as exc:
                call(reconstruct, case)
        assert exc.value.code == "volume_reconstruction_transform_failure"
        assert np.geterr() == policy and warnings.filters == filters
    for a, (saved, strides, writable) in zip(arrays, snapshots, strict=True):
        np.testing.assert_array_equal(a, saved)
        assert a.strides == strides and a.flags.writeable == writable


@pytest.mark.parametrize("seam", ["fftn", "ifftn"])
@pytest.mark.parametrize("kind", [RuntimeError, TypeError, ValueError, MemoryError])
def test_unrelated_transform_exceptions_propagate(
    reconstruct: Any, monkeypatch: Any, seam: str, kind: Any
) -> None:
    case = make_case((1, 2, 3), ((0, 0),))
    sentinel = kind("controlled unrelated FFT exception")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    monkeypatch.setattr(np.fft, seam, fail)
    with pytest.raises(kind) as exc:
        call(reconstruct, case)
    assert exc.value is sentinel


def test_finite_coefficients_but_unrepresentable_synthesis(reconstruct: Any) -> None:
    case = dc_case((1, 1, 2), (1, 2))
    case["images"][:] = np.array([2e148, 0.0])
    case["order_otfs"][0].values[0] = 1e-160
    # Each coefficient is ~1e308; their positive-exponent sum at x=0 exceeds F.
    assert_error(reconstruct, case, "unrepresentable_volume_reconstruction")


def test_fft_axes_sizes_and_unrelated_warnings(reconstruct: Any, monkeypatch: Any) -> None:
    case = make_case((2, 3, 4), ((1, 0),))
    original_forward, original_inverse = np.fft.fftn, np.fft.ifftn
    seen: set[str] = set()

    def observe(name: str, original: Any, a: Any, *args: Any, **kwargs: Any) -> Any:
        s = kwargs.get("s", args[0] if args else None)
        axes = kwargs.get("axes", args[1] if len(args) > 1 else None)
        if axes is None:
            axes = tuple(range(a.ndim - (len(s) if s is not None else a.ndim), a.ndim))
        axes = tuple(int(axis) % a.ndim for axis in axes)
        assert len(axes) == 3 and len(set(axes)) == 3
        expected = case["images"].shape[-3:] if name == "forward" else (2, *case["output_shape_yx"])
        assert sorted(a.shape[axis] for axis in axes) == sorted(expected)
        if s is not None:
            assert all(size in (-1, a.shape[axis]) for size, axis in zip(s, axes, strict=True))
        seen.add(name)
        warnings.warn("controlled unrelated category", UserWarning, stacklevel=2)
        return original(a, *args, **kwargs)

    with monkeypatch.context() as patch, warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        patch.setattr(
            np.fft,
            "fftn",
            lambda a, *args, **kwargs: observe("forward", original_forward, a, *args, **kwargs),
        )
        patch.setattr(
            np.fft,
            "ifftn",
            lambda a, *args, **kwargs: observe("inverse", original_inverse, a, *args, **kwargs),
        )
        compare(reconstruct, case)
    assert seen == {"forward", "inverse"}
    assert any(w.category is UserWarning for w in caught)


def test_conversion_overflow_and_underflow_when_wider_float_available(reconstruct: Any) -> None:
    # No skip: on equal-width platforms the conditional wider examples are unavailable.
    wide = np.finfo(np.longdouble)
    if wide.max > np.longdouble(np.finfo(float).max):
        for key, code in (
            ("images", "nonfinite_volume_reconstruction_images"),
            ("phases_rad", "nonfinite_volume_reconstruction_phases"),
            ("gains", "invalid_volume_reconstruction_gain_values"),
            ("apodization", "invalid_volume_reconstruction_apodization_values"),
        ):
            case = dc_case((1, 1, 1), (1, 1))
            case[key] = case[key].astype(np.longdouble)
            case[key].flat[0] = np.longdouble(np.finfo(float).max) * 2
            assert_error(reconstruct, case, code)
        case = dc_case((1, 1, 1), (1, 1))
        tiny = np.longdouble(np.nextafter(0.0, 1.0)) / 4
        case["images"] = np.full(case["images"].shape, tiny, dtype=np.longdouble)
        result = call(reconstruct, case)
        assert np.count_nonzero(result.volume) == np.count_nonzero(result.spectrum) == 0
        case["gains"] = np.array([tiny], dtype=np.longdouble)
        assert_error(reconstruct, case, "invalid_volume_reconstruction_gain_values")
        case = dc_case((1, 1, 1), (1, 1))
        case["apodization"] = np.array([[[-tiny]]], dtype=np.longdouble)
        assert_error(reconstruct, case, "invalid_volume_reconstruction_apodization_values")


def test_ordinary_binding_and_public_exports(reconstruct: Any) -> None:
    import simrecon

    assert callable(simrecon.prepare_volume_order_otfs)
    assert callable(simrecon.separate_volume_phases)
    assert callable(simrecon.prepare_volume_otf)
    case = dc_case()
    keywords = {key: value for key, value in case.items() if key != "images"}
    for key in keywords:
        with pytest.raises(TypeError):
            reconstruct(case["images"], **{k: v for k, v in keywords.items() if k != key})
    with pytest.raises(TypeError):
        reconstruct(
            case["images"],
            case["order_otfs"],
            **{k: v for k, v in keywords.items() if k != "order_otfs"},
        )
    with pytest.raises(TypeError):
        reconstruct(case["images"], unexpected=True, **keywords)


def test_signed_samples_phases_large_gain_and_unreduced_carrier(reconstruct: Any) -> None:
    case = make_case((1, 1, 2), ((2, -3),))
    case["images"] *= -1
    case["phases_rad"] *= -1
    compare(reconstruct, case)
    case = dc_case((1, 1, 1), (1, 1))
    case["gains"][0] = 1e100  # no upper gain cutoff; arithmetic stages stay finite
    result = call(reconstruct, case)
    assert np.isfinite(result.volume).all() and result.volume.item().real > 0
    case["apodization"][:] = -0.0
    result = call(reconstruct, case)
    assert np.count_nonzero(result.volume) == 0


def test_valid_repeated_phase_rows_and_huge_represented_angles(reconstruct: Any) -> None:
    case = make_case((1, 1, 2), ((0, 0),))
    case["phases_rad"] = np.concatenate((case["phases_rad"], case["phases_rad"][:, :1]), axis=1)
    case["images"] = np.concatenate((case["images"], case["images"][:, :1]), axis=1)
    compare(reconstruct, case)
    case = make_case((1, 1, 1), ((0, 0),))
    case["phases_rad"] = np.array(
        [[np.finfo(float).max, -np.finfo(float).max, 0.0, 0.8, 1.9, 3.0, 4.4]]
    )
    assert np.linalg.cond(basis(case["phases_rad"][0])) < 10
    compare(reconstruct, case)


class TupleSubclass(tuple):
    """Forbidden exact-container subtype."""


class ListSubclass(list):
    """Forbidden exact-container subtype."""


@pytest.mark.parametrize("key", ["output_shape_yx", "order_otfs"])
@pytest.mark.parametrize("kind", [TupleSubclass, ListSubclass])
def test_exact_container_subclasses_rejected(reconstruct: Any, key: str, kind: Any) -> None:
    case = dc_case()
    case[key] = kind(case[key])
    suffix = "output_shape" if key == "output_shape_yx" else "otfs"
    assert_error(reconstruct, case, "invalid_volume_reconstruction_" + suffix)


def test_extreme_components_accepted_despite_complex_magnitude_overflow(reconstruct: Any) -> None:
    # Operational square boundary still rejects F+iF; classification must be range, not validation.
    case = dc_case((1, 1, 1), (1, 1))
    f = np.finfo(float).max
    case["order_otfs"][0].values[0] = complex(f, f)
    assert_error(reconstruct, case, "unrepresentable_volume_reconstruction")


def scalar_overlap_case() -> tuple[dict[str, Any], complex]:
    case = make_case((1, 1, 1), ((0, 0), (0, 0)))
    bands = [(10.0, 2 - 1j, 3 + 4j), (2.0, -0.25 + 0.75j, 1 - 0.5j)]
    transfers = [(1 + 0.25j, 0.5 + 0.25j, -0.25 + 0.5j), (0.7 - 0.2j, -0.5 + 0.4j, 0.2 + 0.3j)]
    gains = [0.5, 1.5]
    numerator, denominator = 0j, 0.5
    for r, (dc, c1, c2) in enumerate(bands):
        coefficients = np.array([dc, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag])
        case["images"][r, :, 0, 0, 0] = basis(case["phases_rad"][r]) @ coefficients
        case["order_otfs"][r].values[:, 0, 0, 0] = transfers[r]
        t0, t1, t2 = [gains[r] * e for e in transfers[r]]
        numerator += (
            t0.conjugate() * dc + 2 * (t1.conjugate() * c1).real + 2 * (t2.conjugate() * c2).real
        )
        denominator += abs(t0) ** 2 + 2 * abs(t1) ** 2 + 2 * abs(t2) ** 2
    case.update(gains=np.array(gains), regularization=0.5, apodization=np.full((1, 1, 1), 0.25))
    return case, 0.25 * numerator / denominator


def test_oracle_analytic_complex_overlap() -> None:
    case, expected = scalar_overlap_case()
    spectrum, volume = direct_oracle(case)
    assert abs(spectrum.item() - expected) < 1e-13
    assert abs(volume.item() - expected) < 1e-13
    assert abs(expected.imag) > 0.01


def test_analytic_complex_overlap_weighting(reconstruct: Any) -> None:
    case, _ = scalar_overlap_case()
    compare(reconstruct, case)


def test_representable_grid_despite_overflowing_field_length_product(reconstruct: Any) -> None:
    case = dc_case((2, 3, 4), (3, 4))
    f = np.finfo(float).max
    case["order_otfs"] = [make_record(case["order_otfs"][0].values, spacing=(f, f, f))]
    result = compare(reconstruct, case)
    assert result.voxel_size_um == (f, f, f)
    with localcontext() as ctx:
        ctx.prec = 90
        for vector, length in zip(
            (result.fz_per_um, result.fy_per_um, result.fx_per_um), (2, 3, 4), strict=True
        ):
            for value, mode in zip(vector, modes(length), strict=True):
                expected = D(mode) / D(length) / decimal(f)
                assert (
                    abs(decimal(value) - expected)
                    <= 8 * D(2) ** -52 * abs(expected) + D(2) ** -1074
                )
