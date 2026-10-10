"""Blind contract tests for known-parameter 2D reconstruction.

The estimator fixture uses independent 85-digit scalar arithmetic. Analytic
constant, single-mode, ridge and boundary tests additionally discriminate
normalization/sign/masking errors without trusting a copied estimator.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import subprocess
import sys
import warnings
from decimal import Decimal, localcontext
from types import SimpleNamespace
from typing import Any, Literal

from reconstruction_fixture import (
    accuracy_budget,
    assert_coordinates,
    assert_frequency_coordinates,
    basic,
    dec,
    effective_denominators,
    estimator,
    modes,
    phantom,
    phase_forward_envelope,
    public,
    record,
    source_free_diagnostics,
)

source_free_diagnostics()
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from reconstruction_failure_controls import (  # noqa: E402
    assert_no_arithmetic_warnings,
    numerical_probe,
    warning_records,
)

SMALL = float.fromhex("0x0.0000000000001p-1022")

ARITHMETIC_VOCABULARY_DIAGNOSTICS = (
    "invalid value for optional backend cache setting; using the default",
    "overflow avoided by scaled arithmetic",
    "underflow is permitted; selecting the configured backend",
    "divide by zero checking is disabled for the optional cache setting",
    "backend option describes 'overflow encountered in add' handling",
)
NUMPY_WARNING_CONTROLS = ("overflow", "scalar_overflow", "underflow", "invalid", "divide")


class ArraySubclass(np.ndarray):
    """A rejected ndarray subclass, independent of all product code."""


def call(arguments: dict[str, Any]) -> Any:
    """Call only the public entry and require the new public record export."""
    api = public()
    assert hasattr(api, "Reconstruction2D"), "Missing public Reconstruction2D"
    assert callable(getattr(api, "reconstruct", None)), "Missing public reconstruct"
    result = api.reconstruct(**arguments)
    assert isinstance(result, api.Reconstruction2D)
    return result


def rejects(arguments: dict[str, Any], code: str, *, alternatives: tuple[str, ...] = ()) -> None:
    """Check the applicable stable codes without choosing simultaneous-fault precedence."""
    api = public()
    with pytest.raises(api.SimreconError) as caught:
        call(arguments)
    assert isinstance(caught.value, ValueError)
    assert getattr(caught.value, "code", None) in (code, *alternatives)
    assert isinstance(getattr(caught.value, "message", None), str)


def caller_arrays(arguments: dict[str, Any]) -> dict[str, np.ndarray]:
    """Observe all six acquisition arrays and all three public OTF arrays."""
    return {
        **{field: arguments[field] for field in ARRAY_FIELDS},
        **{
            f"otf.{field}": getattr(arguments["otf"], field)
            for field in ("values", "fy_per_um", "fx_per_um")
        },
    }


def input_snapshot(arguments: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Record exact logical bytes and public storage metadata, without aliasing."""
    return {
        field: {
            "array": value,
            "bytes": value.tobytes(),
            "shape": value.shape,
            "dtype": value.dtype,
            "strides": value.strides,
            "writeable": value.flags.writeable,
        }
        for field, value in caller_arrays(arguments).items()
    }


def assert_inputs_preserved(arguments: dict[str, Any], before: dict[str, dict[str, Any]]) -> None:
    """Preserve exact bits, including signed zero, on success and rejection."""
    current = caller_arrays(arguments)
    assert current.keys() == before.keys()
    for field, value in current.items():
        snapshot = before[field]
        assert value is snapshot["array"], field
        assert value.shape == snapshot["shape"], field
        assert value.dtype == snapshot["dtype"], field
        assert value.strides == snapshot["strides"], field
        assert value.flags.writeable == snapshot["writeable"], field
        assert value.tobytes() == snapshot["bytes"], field


def synthesis_overflow_arguments() -> dict[str, Any]:
    """Build a valid calibration and finite bands whose final synthesis overflows."""
    arguments = basic((1, 3))
    arguments["otf"] = record(np.array([[0.25, 1, 0.25]], dtype=np.complex128))
    arguments["images"][:] = np.array([6e307, -3e307, -3e307])
    return arguments


def assert_informative(arguments: dict[str, Any]) -> None:
    """Check eligibility for the declared reconstruction coordinate budget."""
    for angles in arguments["phases_rad"].astype(np.float64):
        design = np.column_stack((np.ones(len(angles)), np.cos(angles), np.sin(angles)))
        assert np.linalg.cond(design) <= 10, "Fixture outside informative phase regime"
    assert np.all((arguments["brightness"] >= 0.1) & (arguments["brightness"] <= 10))
    v = effective_denominators(arguments)
    lam = float(arguments["regularization"])
    den = v + lam
    positive = den[den > 0]
    assert np.all(positive >= 1e-6 * max(1, float(np.max(v)), lam))


def assert_reference(arguments: dict[str, Any]) -> Any:
    """Use the approved budget once, with no tighter secondary production bound."""
    assert_informative(arguments)
    spectrum, image = estimator(arguments)
    result = call(arguments)
    budget = accuracy_budget(arguments)
    assert_coordinates(result.spectrum, spectrum, budget)
    assert_coordinates(result.image, image, budget)
    return result


def assert_analytic(
    arguments: dict[str, Any], result: Any, *, spectrum: Any = None, image: Any = None
) -> None:
    """Rebase the same approved envelope using independent stored/analytic bias."""
    assert_informative(arguments)
    stored_spectrum, stored_image = estimator(arguments)
    budget = accuracy_budget(arguments)
    if spectrum is not None:
        assert_coordinates(result.spectrum, stored_spectrum, budget, analytic=spectrum)
    if image is not None:
        assert_coordinates(result.image, stored_image, budget, analytic=image)


def test_public_exports_and_binding() -> None:
    api = public()
    assert hasattr(api, "Reconstruction2D")
    assert callable(api.reconstruct)
    arguments = basic()
    for missing in arguments:
        reduced = arguments.copy()
        del reduced[missing]
        with pytest.raises(TypeError):
            api.reconstruct(**reduced)
    with pytest.raises(TypeError):
        api.reconstruct(arguments["images"], arguments["otf"], arguments["phases_rad"])
    with pytest.raises(TypeError):
        api.reconstruct(**arguments, phase_offset_rad=0.0)
    with pytest.raises(TypeError):
        api.reconstruct(**arguments, unknown=1)
    keys = [key for key in arguments if key != "images"]
    for key in keys:
        with pytest.raises(TypeError):
            api.reconstruct(
                arguments["images"], arguments[key], **{k: arguments[k] for k in keys if k != key}
            )


@pytest.mark.parametrize("shape", [(1, 1), (1, 5), (4, 1), (3, 4), (4, 3), (5, 7)])
@pytest.mark.parametrize("value", [-2.5, 0.0, 7.0])
def test_constant_normalization_shape_origin_and_sampling(
    shape: tuple[int, int], value: float
) -> None:
    arguments = basic(shape)
    arguments["images"][:] = value * (1 + 0.5 * np.cos(arguments["phases_rad"]))[:, :, None, None]
    result = call(arguments)
    ny, nx = shape
    assert result.image.shape == (2 * ny, 2 * nx)
    assert result.spectrum.shape == result.image.shape
    expected = np.zeros(result.spectrum.shape, dtype=np.complex128)
    expected[ny, nx] = value
    if value == 0:
        assert np.all(result.image == 0), "Zero acquisition must give exact zero image"
        assert np.all(result.spectrum == 0), "Zero acquisition must give exact zero spectrum"
    else:
        assert_analytic(arguments, result, spectrum=expected, image=value)
    assert result.pixel_size_um == (0.25, 0.125)
    assert all(type(v) is float for v in result.pixel_size_um)
    assert result.source == arguments["otf"].source
    for output, size, spacing in ((result.fy_per_um, ny, 0.5), (result.fx_per_um, nx, 0.25)):
        assert_frequency_coordinates(output, size, spacing)
        assert output[size] == 0
        assert np.all(np.diff(output) > 0)
    # Same field: 2*Ny*(dy/2)=Ny*dy, independently of doubled sample count.
    assert 2 * ny * result.pixel_size_um[0] == ny * 0.5
    assert 2 * nx * result.pixel_size_um[1] == nx * 0.25


@pytest.fixture(scope="module")
def exact_phantom() -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    return phantom()


def test_end_to_end_recovery_beyond_dc_support(exact_phantom: Any) -> None:
    arguments, truth_spectrum, truth_image = exact_phantom
    ny, nx = arguments["otf"].values.shape
    assert arguments["otf"].values[ny // 2, nx // 2 + 3] == 0
    assert arguments["otf"].values[ny // 2 + 2, nx // 2 + 1] == 0
    assert np.any(arguments["otf"].values.real < 0)
    assert np.any(arguments["otf"].values.imag > 0)
    # Rounded acquisitions, analytic object truth and stored estimator truth are
    # distinct. Analytic comparisons use the approved estimator budget plus
    # independently measured stored-data bias, not an exact-physical tolerance.
    result = assert_reference(arguments)
    assert_analytic(arguments, result, spectrum=truth_spectrum, image=truth_image)
    stored_spectrum, stored_image = estimator(arguments)
    budget = accuracy_budget(arguments)
    assert_coordinates(
        result.spectrum[ny, nx + 3],
        stored_spectrum[ny, nx + 3],
        budget,
        analytic=complex(-0.35, 0.2),
    )
    assert_coordinates(
        result.spectrum[ny + 2, nx + 1],
        stored_spectrum[ny + 2, nx + 1],
        budget,
        analytic=complex(0.15, -0.3),
    )
    # Index-zero origin, observed under the same permitted estimator envelope.
    assert_coordinates(result.image[0, 0], stored_image[0, 0], budget, analytic=4.1)


def test_prepare_otf_origin_is_already_encoded() -> None:
    api = public()
    psf = np.zeros((3, 5))
    psf[1, 2], psf[2, 3], psf[1, 4] = 3, 1, 4
    calibration = api.prepare_otf(
        psf, pixel_size_um=(0.5, 0.25), origin_yx=(1, 2), source="shifted asymmetric PSF"
    )
    arguments = basic(psf.shape)
    arguments["otf"] = calibration
    # Circular acquisition of a signed impulse. Written as spatial sums, no FFT.
    obj = np.zeros(psf.shape)
    obj[0, 1], obj[1, 3], obj[2, 2] = -3, 1, 2
    observation = np.zeros(psf.shape)
    for y, x in itertools.product(range(3), range(5)):
        for hy, hx in itertools.product(range(3), range(5)):
            observation[y, x] += psf[hy, hx] / 8 * obj[(y - (hy - 1)) % 3, (x - (hx - 2)) % 5]
    arguments["images"][:] = observation
    # At k=0, sidebands of a constant phase stack vanish; DC is deconvolved
    # then multiplied by 1/(1+m^2/2), because all bands participate in V.
    result = assert_reference(arguments)
    assert np.min(result.image.real) < 0


@pytest.mark.parametrize("ridge", [0.0, 0.125, 3.0])
def test_scalar_ridge_joint_gains_and_zero_wave(ridge: float) -> None:
    arguments = basic((1, 1), 2)
    arguments["brightness"] = np.array([0.5, 2.0])
    arguments["modulation"] = np.array([0.25, 1.0])
    phases = arguments["phases_rad"]
    for r in range(2):
        a, m = arguments["brightness"][r], arguments["modulation"][r]
        arguments["images"][r, :, 0, 0] = -3 * a * (1 + m * np.cos(phases[r]))
    arguments["regularization"] = ridge
    result = call(arguments)
    v = 0.5**2 * (1 + 0.25**2 / 2) + 2**2 * (1 + 1**2 / 2)
    expected = -3 * v / (v + ridge)
    stored_spectrum, _ = estimator(arguments)
    assert_coordinates(
        result.spectrum[1, 1], stored_spectrum[1, 1], accuracy_budget(arguments), analytic=expected
    )
    assert_analytic(arguments, result, image=expected)


@pytest.mark.parametrize(
    "shift",
    [
        0.0,
        1.0,
        -1.0,
        0.5,
        -0.5,
        1.25,
        -1.25,
        float.fromhex("0x1.ffffffffffffep-1"),
        np.nextafter(1.0, 2.0),
        4.0,
    ],
)
def test_bilinear_signed_endpoints_no_wrap_or_partial_stencil(shift: float) -> None:
    arguments = basic((1, 3))
    # Frequency increment is 1/(3*0.25). These computed shifts define boundaries.
    arguments["wavevectors_per_um"][0, 1] = shift / (3 * 0.25)
    computed_query = float(arguments["wavevectors_per_um"][0, 1]) * 3 * 0.25
    if shift == float.fromhex("0x1.ffffffffffffep-1"):
        assert computed_query < 1, "Represented query must really be below the endpoint"
    elif shift == np.nextafter(1.0, 2.0):
        assert computed_query > 1, "Represented query must really be above the endpoint"
    arguments["images"][0] = np.array([1, -2, 4])[None, None, :]
    assert_reference(arguments)


@pytest.mark.parametrize("shift", [0.0, SMALL, 0.5, -0.5, 2.0])
def test_singleton_axis_requires_exact_zero_query(shift: float) -> None:
    arguments = basic((1, 3))
    arguments["wavevectors_per_um"][0, 0] = shift / 0.5
    assert_reference(arguments)


def test_fractional_physical_acquisition_matches_estimator_not_exact_object() -> None:
    arguments, _, truth = phantom(fractional=True)
    result = assert_reference(arguments)
    _, stored_image = estimator(arguments)
    # The approximation gap exceeds both the stated threshold and all allowed
    # coordinate error (complex error is at most sqrt(2) times that budget).
    assert np.max(np.abs(stored_image - truth)) > 0.05 + 2 * float(accuracy_budget(arguments))
    assert np.max(np.abs(result.image - truth)) > 0.05


def test_off_model_projection_large_direct_angles_and_reorderings() -> None:
    arguments = basic((2, 3), 2)
    arguments["phases_rad"] = np.array(
        [[1e15, -8e14, 3e14, 7e13, -2e12, 5e11, 9e10], [-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81]]
    )
    arguments["images"] = (np.arange(84).reshape(2, 7, 2, 3) % 13 - 6).astype(float)
    original = assert_reference(arguments)
    permutation = np.array([6, 1, 4, 0, 5, 2, 3])
    reordered = arguments.copy()
    reordered["images"] = arguments["images"][::-1][:, permutation]
    reordered["phases_rad"] = arguments["phases_rad"][::-1][:, permutation]
    for name in ("wavevectors_per_um", "brightness", "modulation"):
        reordered[name] = arguments[name][::-1]
    result = assert_reference(reordered)
    assert_coordinates(
        result.image, original.image, accuracy_budget(arguments) + accuracy_budget(reordered)
    )


def test_three_clustered_full_rank_phases_no_span_cutoff() -> None:
    arguments = basic((1, 1))
    arguments["phases_rad"] = np.array([[0.0, 0.01, 0.02]])
    arguments["images"] = (2 * (1 + 0.5 * np.cos(arguments["phases_rad"])))[:, :, None, None]
    result = call(arguments)
    # Outside the reconstruction informative regime: acceptance and finite
    # coordinates are guaranteed here, not a fixed number of useful digits.
    assert np.all(np.isfinite(result.image))
    assert np.all(np.isfinite(result.spectrum))


@pytest.mark.parametrize("phases", [[0, 0, 0], [0, np.pi, 2 * np.pi]])
def test_phase_rank_error_propagates(phases: list[float]) -> None:
    arguments = basic((1, 1))
    arguments["phases_rad"] = np.array([phases], dtype=float)
    arguments["images"] = np.zeros((1, 3, 1, 1))
    rejects(arguments, "rank_deficient_phases")


def test_phase_output_range_error_propagates() -> None:
    arguments = basic((1, 1))
    arguments["phases_rad"] = np.array([[0.0, 0.01, 0.02]])
    arguments["images"] = np.array([[[[1e308]], [[-1e308]], [[1e308]]]])
    rejects(arguments, "unrepresentable_phase_components")


@pytest.mark.parametrize("mask", [0.0, 0.25, 1.0])
def test_explicit_amplitude_mask_scalar(mask: float) -> None:
    arguments = basic((1, 1))
    phi = arguments["phases_rad"][0]
    arguments["images"][0, :, 0, 0] = -2 * (1 + 0.5 * np.cos(phi))
    arguments["apodization"].fill(mask)
    result = call(arguments)
    if mask == 0:
        assert np.all(result.spectrum == 0)
        assert np.all(result.image == 0)
    else:
        assert_analytic(arguments, result, image=-2 * mask)


def test_asymmetric_mask_preserves_complex_image_and_signed_spectrum(exact_phantom: Any) -> None:
    arguments, truth_spectrum, _ = exact_phantom
    arguments = arguments.copy()
    arguments["apodization"] = np.ones_like(arguments["apodization"])
    ny, nx = arguments["otf"].values.shape
    arguments["apodization"][ny, nx - 3] = 0
    arguments["apodization"][ny + 2, nx + 1] = 0.375
    result = assert_reference(arguments)
    assert result.spectrum[ny, nx - 3] == 0
    stored_spectrum, _ = estimator(arguments)
    assert_coordinates(
        result.spectrum[ny + 2, nx + 1],
        stored_spectrum[ny + 2, nx + 1],
        accuracy_budget(arguments),
        analytic=0.375 * truth_spectrum[ny + 2, nx + 1],
    )
    assert np.max(np.abs(result.image.imag)) > 0.2
    assert result.spectrum[ny, nx + 3].real < 0


def test_no_support_threshold_and_exact_zero_denominator() -> None:
    arguments = basic((1, 3))
    # A direct record is valid without proving a nonnegative physical PSF.
    arguments["otf"] = record(np.array([[1e-12, 1, 1e-12]], dtype=np.complex128))
    arguments["images"][0] = np.array([2, -1, -1])[None, None, :] * 1e-12
    result = call(arguments)
    # Weak transfer is outside the informative digit regime. The no-threshold
    # observation distinguishes retained nonzero signal, without a tight amplitude.
    assert result.spectrum[1, 4] != 0
    arguments["otf"] = record(np.array([[0, 1, 0]], dtype=np.complex128))
    result = call(arguments)
    assert result.spectrum[1, 2] == result.spectrum[1, 4] == 0
    assert np.all(result.spectrum[:, [0, 1, 5]] == 0)


ARRAY_FIELDS = {
    "images": ("R02", "images", "dtype", "shape"),
    "phases_rad": ("R04", "phases", "phases_dtype", "phases_shape"),
    "wavevectors_per_um": ("R06", "wavevectors", "wavevectors_dtype", "wavevectors_shape"),
    "modulation": ("R07", "modulation", "modulation_dtype", "modulation_shape"),
    "brightness": ("R08", "brightness", "brightness_dtype", "brightness_shape"),
    "apodization": ("R10", "apodization", "apodization_dtype", "apodization_shape"),
}


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("form", ["list", "subclass", "scalar"])
def test_plain_array_rejections(field: str, form: str) -> None:
    arguments = basic()
    array = arguments[field]
    arguments[field] = {
        "list": lambda: array.tolist(),
        "subclass": lambda: array.view(ArraySubclass),
        "scalar": lambda: 1.0,
    }[form]()
    rejects(arguments, f"invalid_reconstruction_{ARRAY_FIELDS[field][1]}")


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("dtype", ["bool", "complex128", "object", "U4", "S4", "M8[D]", "V8"])
def test_nonreal_dtype_rejections(field: str, dtype: str) -> None:
    arguments = basic()
    arguments[field] = np.zeros(arguments[field].shape, dtype=dtype)
    rejects(arguments, f"invalid_reconstruction_{ARRAY_FIELDS[field][2]}")


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("shape_case", ["rank", "empty", "mismatch"])
def test_shape_rejections(field: str, shape_case: str) -> None:
    arguments = basic()
    shapes = {
        "images": {"rank": (7, 3, 4), "empty": (1, 7, 0, 4), "mismatch": (1, 2, 3, 4)},
        "phases_rad": {"rank": (7,), "empty": (1, 0), "mismatch": (1, 6)},
        "wavevectors_per_um": {"rank": (2,), "empty": (0, 2), "mismatch": (1, 3)},
        "modulation": {"rank": (1, 1), "empty": (0,), "mismatch": (2,)},
        "brightness": {"rank": (1, 1), "empty": (0,), "mismatch": (2,)},
        "apodization": {"rank": (24,), "empty": (0, 8), "mismatch": (6, 7)},
    }
    arguments[field] = np.zeros(shapes[field][shape_case])
    rejects(arguments, f"invalid_reconstruction_{ARRAY_FIELDS[field][3]}")


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_source_nonfinite_rejections(field: str, value: float) -> None:
    arguments = basic()
    arguments[field].flat[0] = value
    suffix = ARRAY_FIELDS[field][1]
    alternatives = ()
    if field in {"modulation", "apodization"} or (field == "brightness" and not value > 0):
        # Every nonfinite modulation/mask value also lies outside its bounded
        # mathematical domain; NaN is unordered, not inside the required range.
        alternatives = (f"invalid_reconstruction_{suffix}_range",)
    rejects(arguments, f"nonfinite_reconstruction_{suffix}", alternatives=alternatives)


@pytest.mark.parametrize("field", ARRAY_FIELDS)
def test_converted_nonfinite_rejections_when_wider_float_exists(field: str) -> None:
    arguments = basic()
    wide = np.finfo(np.longdouble)
    if wide.max <= np.finfo(np.float64).max:
        # No skip or fictitious capability: this platform exercises a permitted
        # wider-width conversion instead; the report records overflow unavailable.
        arguments[field] = arguments[field].astype(np.longdouble)
        call(arguments)
        return
    values = arguments[field].astype(np.longdouble)
    values.flat[0] = np.longdouble(np.finfo(np.float64).max) * np.longdouble(2)
    arguments[field] = values
    suffix = ARRAY_FIELDS[field][1]
    alternatives = (
        (f"invalid_reconstruction_{suffix}_range",)
        if field in {"modulation", "apodization"}
        else ()
    )
    rejects(arguments, f"nonfinite_reconstruction_{suffix}", alternatives=alternatives)


@pytest.mark.parametrize(
    "field,code,values",
    [
        (
            "modulation",
            "invalid_reconstruction_modulation_range",
            [0.0, -0.1, np.nextafter(1.0, 2.0)],
        ),
        ("brightness", "invalid_reconstruction_brightness_range", [0.0, -0.1]),
        (
            "apodization",
            "invalid_reconstruction_apodization_range",
            [-1e-12, np.nextafter(1.0, 2.0)],
        ),
    ],
)
def test_parameter_ranges(field: str, code: str, values: list[float]) -> None:
    for value in values:
        arguments = basic()
        arguments[field].flat[0] = value
        rejects(arguments, code)


@pytest.mark.parametrize(
    "value", [True, np.bool_(False), 1j, "0", [0], np.array(0.0), np.nan, np.inf, -np.inf, -1.0]
)
def test_regularization_rejections(value: Any) -> None:
    arguments = basic()
    arguments["regularization"] = value
    rejects(arguments, "invalid_reconstruction_regularization")


@pytest.mark.parametrize(
    "value",
    [
        0,
        1,
        np.int64(2),
        np.uint64(1),
        np.float16(0),
        np.float32(0.25),
        np.float64(0),
        np.longdouble(0),
        -0.0,
    ],
)
def test_regularization_positive_scalar_alternatives(value: Any) -> None:
    arguments = basic((1, 1))
    arguments["regularization"] = value
    assert_reference(arguments)


REAL_DTYPES = sorted(
    {
        np.dtype(name).str
        for name in (
            "int8",
            "int16",
            "int32",
            "int64",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "float16",
            "float32",
            "float64",
            "longdouble",
        )
    }
    | {
        np.dtype(name).newbyteorder(">").str
        for name in (
            "int16",
            "int32",
            "int64",
            "uint16",
            "uint32",
            "uint64",
            "float16",
            "float32",
            "float64",
            "longdouble",
        )
    }
)


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("dtype", REAL_DTYPES)
def test_all_real_widths_endians_and_converted_values(field: str, dtype: str) -> None:
    arguments = basic((1, 1))
    # Each integer domain needs a *valid* positive example. Do not reject valid
    # integer masks/gains or round unequal phases to a deficient phase grid.
    values = {
        "images": np.array([[[[5]]]] * 7).reshape(1, 7, 1, 1),
        "phases_rad": np.array([[0, 1, 2, 3, 4, 5, 6]]),
        "wavevectors_per_um": np.array([[0, 0]]),
        "brightness": np.array([2]),
        "modulation": np.array([1]),
        "apodization": np.array([[0, 1], [1, 1]]),
    }
    arguments[field] = values[field].astype(dtype)
    assert_reference(arguments)


@pytest.mark.parametrize("dtype,value", [("int64", 2**53 + 1), ("uint64", 2**64 - 1)])
def test_large_integer_rounding_defines_image_problem(dtype: str, value: int) -> None:
    arguments = basic((1, 1))
    arguments["images"] = np.full((1, 7, 1, 1), value, dtype=dtype)
    expected = float(value) / 1.125
    result = call(arguments)
    assert_analytic(arguments, result, image=expected)


@pytest.mark.parametrize("storage", ["readonly", "stride", "reverse"])
def test_storage_and_input_preservation(storage: str) -> None:
    arguments = basic((2, 3))
    arrays = [*ARRAY_FIELDS]
    for field in arrays:
        value = arguments[field]
        if storage == "stride":
            expanded = np.empty((*value.shape[:-1], value.shape[-1] * 2))
            expanded[..., ::2] = value
            value = expanded[..., ::2]
        elif storage == "reverse":
            value = value[..., ::-1].copy()[..., ::-1]
        else:
            value.setflags(write=False)
        arguments[field] = value
    before = input_snapshot(arguments)
    result = assert_reference(arguments)
    assert_inputs_preserved(arguments, before)
    arguments["regularization"] = -1
    rejects(arguments, "invalid_reconstruction_regularization")
    assert_inputs_preserved(arguments, before)
    assert result.image.flags.owndata


def test_result_bindings_mutability_native_dtype_and_independent_storage() -> None:
    arguments = basic((2, 3))
    result = call(arguments)
    outputs = [result.image, result.spectrum, result.fy_per_um, result.fx_per_um]
    inputs = [arguments[k] for k in ARRAY_FIELDS]
    inputs += [arguments["otf"].values, arguments["otf"].fy_per_um, arguments["otf"].fx_per_um]
    for index, output in enumerate(outputs):
        assert output.dtype == np.dtype("complex128" if index < 2 else "float64")
        assert output.dtype.isnative
        assert output.flags.c_contiguous and output.flags.owndata and output.flags.writeable
        for other in inputs + outputs[:index]:
            assert not np.shares_memory(output, other)
    for name in ("image", "spectrum", "fy_per_um", "fx_per_um", "pixel_size_um", "source"):
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError, TypeError)):
            setattr(result, name, None)
    snapshots = [item.copy() for item in outputs]
    for index, output in enumerate(outputs):
        output.flat[0] = 123
        for other_index, other in enumerate(outputs):
            if other_index != index:
                np.testing.assert_array_equal(other, snapshots[other_index])
        output[...] = snapshots[index]


def alter_otf(arguments: dict[str, Any], field: str, value: Any) -> None:
    otf = arguments["otf"]
    values = {
        name: getattr(otf, name)
        for name in ("values", "fy_per_um", "fx_per_um", "pixel_size_um", "origin_yx", "source")
    }
    values[field] = value
    arguments["otf"] = public().Otf2D(**values)


@pytest.mark.parametrize("value", [None, {}, np.ones((3, 4))])
def test_otf_type_validation(value: Any) -> None:
    arguments = basic()
    arguments["otf"] = value
    rejects(arguments, "invalid_reconstruction_otf")


@pytest.mark.parametrize("field", ["values", "fy_per_um", "fx_per_um"])
@pytest.mark.parametrize(
    "fault", ["list", "subclass", "rank", "shape", "width", "kind", "nonfinite"]
)
def test_direct_otf_array_validation(field: str, fault: str) -> None:
    arguments = basic()
    value = getattr(arguments["otf"], field)
    changes = {
        "list": lambda: value.tolist(),
        "subclass": lambda: value.view(ArraySubclass),
        "rank": lambda: value[None],
        "shape": lambda: value[..., :-1],
        "width": lambda: value.astype("complex64" if field == "values" else "float32"),
        "kind": lambda: np.ones(value.shape, dtype="float64" if field == "values" else "int64"),
        "nonfinite": lambda: np.full(value.shape, np.nan, dtype=value.dtype),
    }
    alter_otf(arguments, field, changes[fault]())
    alternatives = (
        ("incompatible_reconstruction_otf_grid",)
        if fault == "nonfinite" and field != "values"
        else ()
    )
    rejects(arguments, "invalid_reconstruction_otf", alternatives=alternatives)


@pytest.mark.parametrize("field", ["values", "fy_per_um", "fx_per_um"])
@pytest.mark.parametrize("storage", ["bigendian", "readonly", "strided"])
def test_permitted_otf_array_storage(field: str, storage: str) -> None:
    def stored(value: np.ndarray) -> np.ndarray:
        if storage == "bigendian":
            return value.astype(value.dtype.newbyteorder(">"))
        if storage == "strided":
            expanded = np.empty((*value.shape[:-1], 2 * value.shape[-1]), dtype=value.dtype)
            expanded[..., ::2] = value
            return expanded[..., ::2]
        value.setflags(write=False)
        return value

    # Keep the original nonsingleton grid: its strided frequency vectors are
    # genuinely noncontiguous. A singleton-only replacement would lose that
    # distinguishing permitted-positive example.
    arguments = basic()
    alter_otf(arguments, field, stored(getattr(arguments["otf"], field)))
    if storage == "strided":
        assert not getattr(arguments["otf"], field).flags.c_contiguous
    before = input_snapshot(arguments)
    call(arguments)
    assert_inputs_preserved(arguments, before)
    arguments["regularization"] = -1
    rejects(arguments, "invalid_reconstruction_regularization")
    assert_inputs_preserved(arguments, before)
    arguments = synthesis_overflow_arguments()
    alter_otf(arguments, field, stored(getattr(arguments["otf"], field)))
    before = input_snapshot(arguments)
    rejects(arguments, "unrepresentable_reconstruction")
    assert_inputs_preserved(arguments, before)


@pytest.mark.parametrize(
    "field,value",
    [
        ("pixel_size_um", 1),
        ("pixel_size_um", (1,)),
        ("pixel_size_um", (1, 2, 3)),
        ("pixel_size_um", np.ones((1, 2))),
        ("pixel_size_um", np.ones(2).view(ArraySubclass)),
        ("pixel_size_um", (True, 1)),
        ("pixel_size_um", (1j, 1)),
        ("pixel_size_um", ("1", 1)),
        ("pixel_size_um", (0, 1)),
        ("pixel_size_um", (-1, 1)),
        ("pixel_size_um", (np.inf, 1)),
        ("pixel_size_um", (np.nan, 1)),
        ("origin_yx", 1),
        ("origin_yx", (1,)),
        ("origin_yx", (1, 2, 3)),
        ("origin_yx", np.ones((1, 2), dtype=int)),
        ("origin_yx", (True, 0)),
        ("origin_yx", (0.0, 0)),
        ("origin_yx", (-1, 0)),
        ("origin_yx", (3, 0)),
        ("origin_yx", (0, 4)),
        ("source", None),
        ("source", ""),
        ("source", " \t\n"),
    ],
)
def test_otf_metadata_validation(field: str, value: Any) -> None:
    arguments = basic()
    alter_otf(arguments, field, value)
    rejects(arguments, "invalid_reconstruction_otf")


@pytest.mark.parametrize(
    "spacing",
    [
        (0.5, 0.25),
        [np.float32(0.5), np.int64(1)],
        np.array([0.5, 0.25]),
        (np.longdouble(0.5), 0.25),
    ],
)
@pytest.mark.parametrize("origin", [(0, 0), [np.int64(2), np.uint64(3)], np.array([1, 2])])
def test_permitted_metadata_pairs_and_nonzero_origin(spacing: Any, origin: Any) -> None:
    arguments = basic()
    arguments["otf"] = record(np.ones((3, 4), dtype=np.complex128), spacing=spacing, origin=origin)
    result = call(arguments)
    assert result.pixel_size_um == (float(spacing[0]) / 2, float(spacing[1]) / 2)
    assert_analytic(arguments, result, image=-2.5 / 1.125)


@pytest.mark.parametrize("field", ["fy_per_um", "fx_per_um"])
@pytest.mark.parametrize(
    "fault", ["offset", "reversed", "collapsed", "nonzero_lost", "wrong_spacing"]
)
def test_incompatible_otf_grid(field: str, fault: str) -> None:
    arguments = basic()
    value = getattr(arguments["otf"], field).copy()
    if fault == "offset":
        value += 1e-8
    elif fault == "reversed":
        value = value[::-1]
    elif fault == "collapsed":
        value[:] = 0
    elif fault == "nonzero_lost":
        value[0] = 0
    else:
        value *= 2
    alter_otf(arguments, field, value)
    rejects(arguments, "incompatible_reconstruction_otf_grid")


@pytest.mark.parametrize("fault", ["dc", "magnitude", "hermitian", "imaginary_self_pair"])
def test_otf_transfer_sanity_rejections(fault: str) -> None:
    arguments = basic()
    values = arguments["otf"].values.copy()
    if fault == "dc":
        values[1, 2] = 0.99
    elif fault == "magnitude":
        values[1, 1] = values[1, 3] = 1.01
    elif fault == "hermitian":
        values[0, 1] = 0.5j
    else:
        values[1, 0] = 0.5j
    alter_otf(arguments, "values", values)
    rejects(arguments, "invalid_reconstruction_otf")


def test_otf_tolerances_accept_nearby_legitimate_record() -> None:
    arguments = basic()
    ny, nx = arguments["otf"].values.shape
    tau = 128 * ny * nx * np.finfo(float).eps
    values = arguments["otf"].values.copy()
    values[ny // 2, nx // 2] = 1 + tau / 4
    alter_otf(arguments, "values", values)
    for field in ("fy_per_um", "fx_per_um"):
        vector = getattr(arguments["otf"], field).copy()
        vector *= 1 + 2 * np.finfo(float).eps
        alter_otf(arguments, field, vector)
    assert_reference(arguments)


@pytest.mark.parametrize("spacing", [(SMALL, 1.0), (1e-309, 1e-309), (1.0, SMALL)])
def test_unrepresentable_output_grid(spacing: Any) -> None:
    # SMALL/2 collapses output spacing. At 1e-309 the halved spacing is
    # positive, but the singleton output's -1/d frequency exceeds float64 max.
    arguments = basic((1, 1))
    arguments["otf"] = record(np.ones((1, 1), dtype=np.complex128), spacing=spacing)
    rejects(arguments, "unrepresentable_reconstruction_grid")


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((1, 1), (np.finfo(float).max, np.finfo(float).max)),
        ((1, 1), (1e300, 1e300)),
        ((3, 4), (1e307, 1e307)),
        ((1, 1), (1e-300, 1e-300)),
    ],
)
def test_extreme_but_representable_output_grid(shape: Any, spacing: Any) -> None:
    arguments = basic(shape)
    arguments["otf"] = record(np.ones(shape, dtype=np.complex128), spacing=spacing)
    result = call(arguments)
    assert np.all(np.isfinite(result.fy_per_um)) and np.all(np.isfinite(result.fx_per_um))
    assert np.all(np.diff(result.fy_per_um) > 0) and np.all(np.diff(result.fx_per_um) > 0)
    assert np.all(result.fy_per_um[np.array(modes(2 * shape[0])) != 0] != 0)
    assert np.all(result.fx_per_um[np.array(modes(2 * shape[1])) != 0] != 0)
    assert result.pixel_size_um == (spacing[0] / 2, spacing[1] / 2)


def test_unrepresentable_shift_coordinates() -> None:
    arguments = basic()
    arguments["wavevectors_per_um"].fill(np.finfo(float).max)
    rejects(arguments, "unrepresentable_reconstruction_grid")


@pytest.mark.parametrize("policy", ["ignore", "warn", "raise", "call", "print", "log"])
@pytest.mark.parametrize(
    "case", ["raw_transform", "squared_gain", "subnormal", "overflow", "nonfinite"]
)
def test_range_and_arithmetic_policy(
    policy: Literal["ignore", "warn", "raise", "call", "print", "log"], case: str
) -> None:
    arguments = basic((3, 4))
    expected: float | None = None
    code = None
    if case == "raw_transform":
        arguments["images"].fill(3e307)
        expected = 3e307 / 1.125
    elif case == "squared_gain":
        arguments["images"].fill(1e300)
        arguments["brightness"].fill(1e300)
        expected = 1 / 1.125
    elif case == "subnormal":
        arguments["images"].fill(SMALL * 16)
        expected = float(Decimal(2) ** -1074 * 16 / Decimal("1.125"))
    elif case == "overflow":
        arguments["images"].fill(1e300)
        arguments["brightness"].fill(1e-100)
        code = "unrepresentable_reconstruction"
    else:
        arguments["images"].flat[0] = np.inf
        code = "nonfinite_reconstruction_images"

    class ErrorObserver:
        def __init__(self) -> None:
            self.messages: list[Any] = []

        def __call__(self, *values: Any) -> None:
            self.messages.append(values)

        def write(self, text: str) -> None:
            self.messages.append(text)

    observer = ErrorObserver()
    previous = np.geterr()
    previous_callback = np.geterrcall()
    try:
        np.seterrcall(observer)
        np.seterr(all=policy)
        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter("always")
            if code:
                rejects(arguments, code)
            else:
                result = call(arguments)
                assert expected is not None
                assert np.all(np.isfinite(result.image))
                assert np.all(np.isfinite(result.spectrum))
                if case != "squared_gain":
                    # Raw-transform and subnormal cases remain informative.
                    # Extremely large brightness is outside that regime and
                    # supplies a finite-range guarantee, not a digit bound.
                    assert_informative(arguments)
                    stored_spectrum, stored_image = estimator(arguments)
                    budget = accuracy_budget(arguments)
                    assert_coordinates(result.spectrum, stored_spectrum, budget)
                    assert_coordinates(result.image, stored_image, budget)
            assert_no_arithmetic_warnings({"warnings": warning_records(emitted)})
        assert np.geterr() == dict.fromkeys(previous, policy)
        assert np.geterrcall() is observer
        assert not observer.messages
    finally:
        np.seterr(**previous)
        np.seterrcall(previous_callback)


@pytest.mark.parametrize("failure", ["value", "floating", "overflow", "nan", "memory", "unrelated"])
def test_public_transform_failure_controls(failure: str) -> None:
    completed = subprocess.run(
        [sys.executable, "tests/reconstruction_failure_controls.py", "--simulate", failure],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, "Source-free control subprocess did not complete"
    evidence = json.loads(completed.stdout)
    assert_no_arithmetic_warnings(evidence)
    if not evidence["events"]:
        assert evidence["outcome"] == "normal", evidence
        return
    if failure in {"memory", "unrelated"}:
        assert (
            evidence["type"] == {"memory": "MemoryError", "unrelated": "RuntimeError"}[failure]
        ), evidence
        assert evidence["message"] == "public backend control"
    else:
        assert evidence["code"] == "reconstruction_solver_failure", evidence


@pytest.mark.parametrize("failure", ["linalg", "nan", "memory", "unrelated"])
def test_public_phase_backend_failures_propagate(failure: str) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "tests/reconstruction_failure_controls.py",
            "--simulate",
            failure,
            "--phase",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0
    evidence = json.loads(completed.stdout)
    assert_no_arithmetic_warnings(evidence)
    if not evidence["events"]:
        assert evidence["outcome"] == "normal", evidence
    elif failure in {"memory", "unrelated"}:
        assert (
            evidence["type"] == {"memory": "MemoryError", "unrelated": "RuntimeError"}[failure]
        ), evidence
    else:
        assert evidence["code"] == "phase_solver_failure", evidence


@pytest.mark.parametrize("phase", [False, True])
@pytest.mark.parametrize("warning_kind", ["arithmetic", "user", "runtime_diagnostic"])
def test_warning_observer_retains_normal_return_and_selects_arithmetic(
    phase: bool, warning_kind: str
) -> None:
    """Observer evidence only: correct backend-free output can still warn."""

    def boundary() -> Any:
        if warning_kind == "arithmetic":
            # Generate an actual floating-point arithmetic warning independently
            # of the product and of the patched transform/phase boundaries.
            with np.errstate(over="warn"):
                np.add(np.finfo(float).max, np.finfo(float).max)
        else:
            category = UserWarning if warning_kind == "user" else RuntimeWarning
            warnings.warn("optional backend diagnostic", category, stacklevel=1)
        spectrum = np.zeros((6, 8), dtype=np.complex128)
        spectrum[3, 4] = -2.5 / 1.125
        return SimpleNamespace(
            spectrum=spectrum, image=np.full((6, 8), -2.5 / 1.125, dtype=np.complex128)
        )

    evidence = numerical_probe("memory", phase=phase, operation=boundary)
    assert evidence["outcome"] == "normal" and evidence["events"] == [], evidence
    assert len(evidence["warnings"]) == 1
    item = evidence["warnings"][0]
    assert item["filename"] == boundary.__code__.co_filename
    assert isinstance(item["line"], int) and item["line"] > 0
    assert item["category"] == ("UserWarning" if warning_kind == "user" else "RuntimeWarning")
    if warning_kind == "arithmetic":
        assert item["message"] == "overflow encountered in add"
        with pytest.raises(AssertionError):
            assert_no_arithmetic_warnings(evidence)
    else:
        assert item["message"] == "optional backend diagnostic"
        assert_no_arithmetic_warnings(evidence)


@pytest.mark.parametrize("phase", [False, True])
def test_warning_observer_retains_diagnostic_before_memory_error(phase: bool) -> None:
    """A permitted diagnostic must not invalidate public allocation propagation."""

    def boundary() -> Any:
        warnings.warn("optional backend diagnostic", UserWarning, stacklevel=1)
        if phase:
            return np.linalg.svd(np.ones((3, 3)))
        return np.fft.fft2(np.ones((3, 4)))

    evidence = numerical_probe("memory", phase=phase, operation=boundary)
    assert evidence["outcome"] == "error" and evidence["type"] == "MemoryError", evidence
    assert evidence["message"] == "public backend control"
    assert evidence["events"] == ["numpy.linalg.svd" if phase else "numpy.fft.fft2"]
    assert evidence["frames"]
    assert len(evidence["warnings"]) == 1
    item = evidence["warnings"][0]
    assert item["category"] == "UserWarning"
    assert item["message"] == "optional backend diagnostic"
    assert item["filename"] == boundary.__code__.co_filename
    assert isinstance(item["line"], int) and item["line"] > 0
    assert_no_arithmetic_warnings(evidence)


def emit_numpy_arithmetic_control(kind: str) -> None:
    """Generate real floating errors with independently known result classes."""
    with np.errstate(all="warn"):
        if kind == "overflow":
            value = np.add(np.finfo(float).max, np.finfo(float).max)
            assert np.isposinf(value)
        elif kind == "scalar_overflow":
            value = np.float64(np.finfo(float).max) * np.float64(2)
            assert np.isposinf(value)
        elif kind == "underflow":
            # 2**-1022 * 2**-53 = 2**-1075, halfway below the smallest
            # representable positive float64. Rounding to zero loses precision.
            value = np.multiply(np.finfo(float).tiny, np.finfo(float).eps / 2)
            assert value == 0
        elif kind == "invalid":
            value = np.sqrt(np.float64(-1))
            assert np.isnan(value)
        elif kind == "divide":
            value = np.divide(np.float64(1), np.float64(0))
            assert np.isposinf(value)
        else:
            raise AssertionError("Unknown owned arithmetic control")


def warning_semantic_control(
    phase: bool,
    outcome: Literal["normal", "memory"],
    *,
    diagnostic: str | None = None,
    arithmetic_kind: str | None = None,
) -> dict[str, Any]:
    """Observe owned semantic controls without replacing any product attribute."""

    def boundary() -> Any:
        if arithmetic_kind is not None:
            emit_numpy_arithmetic_control(arithmetic_kind)
        else:
            assert diagnostic is not None
            warnings.warn(diagnostic, RuntimeWarning, stacklevel=1)
        if outcome == "memory":
            if phase:
                return np.linalg.svd(np.ones((3, 3)))
            return np.fft.fft2(np.ones((3, 4)))
        spectrum = np.zeros((6, 8), dtype=np.complex128)
        spectrum[3, 4] = -2.5 / 1.125
        return SimpleNamespace(
            spectrum=spectrum, image=np.full((6, 8), -2.5 / 1.125, dtype=np.complex128)
        )

    evidence = numerical_probe("memory", phase=phase, operation=boundary)
    if outcome == "normal":
        assert evidence["outcome"] == "normal" and evidence["events"] == [], evidence
    else:
        assert evidence["outcome"] == "error" and evidence["type"] == "MemoryError", evidence
        assert evidence["message"] == "public backend control"
        assert evidence["events"] == ["numpy.linalg.svd" if phase else "numpy.fft.fft2"]
        assert evidence["frames"]
    assert len(evidence["warnings"]) == 1
    item = evidence["warnings"][0]
    assert item["category"] == "RuntimeWarning" and item["runtime_warning"]
    assert item["filename"] == boundary.__code__.co_filename
    assert isinstance(item["line"], int) and item["line"] > 0
    return evidence


@pytest.mark.parametrize("phase", [False, True])
@pytest.mark.parametrize("outcome", ["normal", "memory"])
@pytest.mark.parametrize("diagnostic", ARITHMETIC_VOCABULARY_DIAGNOSTICS)
def test_warning_observer_permits_arithmetic_vocabulary_diagnostics(
    phase: bool, outcome: Literal["normal", "memory"], diagnostic: str
) -> None:
    evidence = warning_semantic_control(phase, outcome, diagnostic=diagnostic)
    assert evidence["warnings"][0]["message"] == diagnostic
    assert_no_arithmetic_warnings(evidence)


@pytest.mark.parametrize("phase", [False, True])
@pytest.mark.parametrize("outcome", ["normal", "memory"])
@pytest.mark.parametrize("kind", NUMPY_WARNING_CONTROLS)
def test_warning_observer_rejects_real_numpy_error_reports(
    phase: bool, outcome: Literal["normal", "memory"], kind: str
) -> None:
    evidence = warning_semantic_control(phase, outcome, arithmetic_kind=kind)
    # The operation/result defines the expected semantics independently of the
    # classifier. Retain actual NumPy prose; do not invent runtime message rules.
    with pytest.raises(AssertionError):
        assert_no_arithmetic_warnings(evidence)


@pytest.mark.parametrize("field", ["values", "fy_per_um", "fx_per_um"])
def test_preservation_observer_detects_each_calibration_array_change(field: str) -> None:
    """Owned observer validation: even a changed zero sign must be detected."""
    arguments = basic((2, 3))
    before = input_snapshot(arguments)
    assert_inputs_preserved(arguments, before)
    value = getattr(arguments["otf"], field)
    if field == "values":
        # All imaginary coordinates initially +0. This changes bits without
        # changing numerical equality, so array_equal alone would miss it.
        value.flat[0] = complex(float(value.flat[0].real), -0.0)
    else:
        value[value == 0] = -0.0
    with pytest.raises(AssertionError, match=f"otf.{field}"):
        assert_inputs_preserved(arguments, before)


def test_no_file_access_during_public_numerical_call(monkeypatch: Any) -> None:
    import builtins
    import io

    arguments = basic((1, 1))

    def fail_io(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Numerical reconstruction attempted file I/O")

    # Import public runtime first; import machinery itself legitimately reads.
    api = public()
    assert hasattr(api, "Reconstruction2D")
    with monkeypatch.context() as scoped:
        scoped.setattr(builtins, "open", fail_io)
        scoped.setattr(io, "open", fail_io)
        scoped.setattr(np, "load", fail_io)
        scoped.setattr(np, "save", fail_io)
        call(arguments)


def test_fixture_derivation_and_informative_regime(exact_phantom: Any) -> None:
    """Validate oracle prerequisites independently; does not imply product red."""
    arguments, truth_spectrum, truth_image = exact_phantom
    for phases in arguments["phases_rad"]:
        matrix = np.column_stack((np.ones(len(phases)), np.cos(phases), np.sin(phases)))
        assert np.linalg.cond(matrix) < 10
    spectrum, image = estimator(arguments)
    np.testing.assert_allclose(spectrum, truth_spectrum, rtol=0, atol=3e-13)
    np.testing.assert_allclose(image, truth_image, rtol=0, atol=3e-13)
    # Separate scalar sanity check. No transform or phase product result used.
    arguments = basic((1, 1))
    spectrum, image = estimator(arguments)
    assert abs(spectrum[1, 1] + 2.5 / 1.125) < 1e-15
    assert abs(image[0, 0] + 2.5 / 1.125) < 1e-15


@pytest.mark.parametrize("field", ["images", "phases_rad", "wavevectors_per_um"])
def test_source_to_float64_underflow_is_permitted(field: str) -> None:
    arguments = basic((1, 1))
    values = arguments[field].astype(np.longdouble)
    # A genuine wider source underflow exists only when longdouble extends the
    # float64 exponent range. Otherwise exercise a finite stored subnormal.
    if np.finfo(np.longdouble).tiny < np.finfo(np.float64).tiny:
        tiny = np.longdouble(SMALL) / np.longdouble(4)
    else:
        tiny = np.longdouble(SMALL)
    if field == "images":
        values.fill(-tiny)
    elif field == "phases_rad":
        values[0, 0] = -tiny
    else:
        values.fill(-tiny)
    arguments[field] = values
    converted = arguments.copy()
    with np.errstate(all="ignore"):
        converted[field] = values.astype(np.float64)
    result, reference = call(arguments), call(converted)
    if not np.any(converted["images"]):
        for output in (result.spectrum, result.image, reference.spectrum, reference.image):
            assert np.all(output == 0)
    else:
        # Same stored problem admits different valid arithmetic paths. Each call
        # gets its own budget; their difference gets the sum, not bitwise equality.
        assert_reference(arguments)
        assert_reference(converted)
        combined_budget = accuracy_budget(arguments) + accuracy_budget(converted)
        assert_coordinates(result.spectrum, reference.spectrum, combined_budget)
        assert_coordinates(result.image, reference.image, combined_budget)


@pytest.mark.parametrize("field", ["brightness", "modulation", "apodization"])
def test_wider_underflow_source_and_converted_range_checks(field: str) -> None:
    arguments = basic((1, 1))
    if np.finfo(np.longdouble).tiny >= np.finfo(np.float64).tiny:
        # Relevant converted-zero rejection is still observable without a
        # nonexistent platform capability. Mask negative source uses -SMALL.
        tiny = np.longdouble(0 if field != "apodization" else SMALL)
    else:
        tiny = np.longdouble(SMALL) / np.longdouble(4)
    values = arguments[field].astype(np.longdouble)
    values.flat[0] = -tiny if field == "apodization" else tiny
    arguments[field] = values
    rejects(arguments, f"invalid_reconstruction_{field}_range")


@pytest.mark.parametrize("field", ["regularization", "pixel_size_um"])
def test_scalar_conversion_overflow_and_underflow(field: str) -> None:
    for value in (10**500, np.longdouble(np.finfo(np.longdouble).max)):
        arguments = basic((1, 1))
        if field == "regularization":
            arguments[field] = value
            # Wider dtype may not have a wider exponent range.
            if np.isfinite(value) if isinstance(value, np.floating) else False:
                with np.errstate(all="ignore"):
                    finite_conversion = np.isfinite(np.float64(value))
                if finite_conversion:
                    call(arguments)
                    continue
            rejects(arguments, "invalid_reconstruction_regularization")
        else:
            alter_otf(arguments, field, (value, 0.25))
            if isinstance(value, np.floating):
                with np.errstate(all="ignore"):
                    finite_conversion = np.isfinite(np.float64(value))
                if finite_conversion:
                    # A singleton detector has only zero frequency. A finite
                    # positive spacing is compatible even when it is huge.
                    call(arguments)
                    continue
            rejects(arguments, "invalid_reconstruction_otf")
    if np.finfo(np.longdouble).tiny < np.finfo(np.float64).tiny:
        arguments = basic((1, 1))
        tiny = np.longdouble(SMALL) / 4
        if field == "regularization":
            arguments[field] = tiny
            call(arguments)
        else:
            alter_otf(arguments, field, (tiny, 0.25))
            rejects(arguments, "invalid_reconstruction_otf")


def test_otf_nonfinite_imaginary_and_frequency_sources() -> None:
    for field in ("values", "fy_per_um", "fx_per_um"):
        for value in (np.inf, -np.inf):
            arguments = basic()
            values = getattr(arguments["otf"], field).copy()
            values.flat[0] = complex(0, value) if field == "values" else value
            alter_otf(arguments, field, values)
            alternatives = ("incompatible_reconstruction_otf_grid",) if field != "values" else ()
            rejects(arguments, "invalid_reconstruction_otf", alternatives=alternatives)


def test_empty_orientation_and_second_empty_spatial_axis() -> None:
    for shape in ((0, 7, 3, 4), (1, 7, 3, 0), (1, 7, 3, 4, 1)):
        arguments = basic()
        arguments["images"] = np.zeros(shape)
        rejects(arguments, "invalid_reconstruction_shape")


def test_modular_hermitian_and_tolerance_positive_alternatives() -> None:
    arguments = basic((3, 4))
    ny, nx = 3, 4
    tau = 128 * ny * nx * np.finfo(float).eps
    values = np.ones((ny, nx), dtype=np.complex128)
    # Even negative Nyquist is self paired modulo detector size. Complex
    # transfer is permitted when its imaginary self-difference is <=2*tau.
    values[ny // 2, 0] = complex(-0.5, tau / 4)
    values[0, 1] = complex(-0.25, 0.5)
    values[2, 3] = complex(-0.25, -0.5 + tau / 4)
    values[ny // 2, nx // 2] = complex(1, tau / 4)
    alter_otf(arguments, "values", values)
    assert_reference(arguments)


def test_origin_pair_subclass_and_noninteger_rejections() -> None:
    for origin in (
        np.array([0, 0]).view(ArraySubclass),
        ("0", 0),
        (1j, 0),
        np.array([0.0, 0.0]),
        (np.bool_(False), 0),
    ):
        arguments = basic()
        alter_otf(arguments, "origin_yx", origin)
        rejects(arguments, "invalid_reconstruction_otf")


def test_public_prerequisite_apis_remain_callable() -> None:
    """Check public compatibility without reading or running existing tests."""
    api = public()
    phi = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
    images = (10 + 4 * np.cos(phi) + 2 * np.sin(phi))[:, None, None]
    separated = api.separate_phases(images, phases_rad=phi)
    phase_truth, phase_bound = phase_forward_envelope(phi, images[:, 0, 0])
    with localcontext() as ctx:
        ctx.prec = 85
        returned = (separated.dc[0, 0], separated.c1[0, 0].real, separated.c1[0, 0].imag)
        for actual, stored_truth, analytic in zip(returned, phase_truth, (10, 2, -1), strict=True):
            assert abs(dec(actual) - dec(analytic)) <= (
                phase_bound + abs(stored_truth - dec(analytic)) + phase_bound * Decimal("1e-40")
            )
    calibration = api.prepare_otf(
        np.ones((1, 1)), pixel_size_um=(0.5, 0.25), origin_yx=(0, 0), source="unchanged public API"
    )
    with localcontext() as ctx:
        ctx.prec = 85
        otf_budget = 128 * Decimal(2) ** -52 + 4 * Decimal(2) ** -1074
    assert_coordinates(calibration.values, [[1]], otf_budget)


def test_even_negative_nyquist_synthesis_retains_complex_residue() -> None:
    arguments = basic((4, 6))
    row = np.array([1, -1, 1, -1, 1, -1], dtype=float)
    arguments["images"][:] = row
    result = assert_reference(arguments)
    expected = np.zeros((8, 12), dtype=np.complex128)
    expected[4, 3] = 1 / 1.125  # kx=-3, no duplicate positive Nyquist endpoint.
    assert_analytic(arguments, result, spectrum=expected)
    x = np.arange(12)
    image = np.exp(-2j * np.pi * 3 * x / 12) / 1.125
    assert_analytic(arguments, result, image=np.tile(image, (8, 1)))


def test_synthesis_overflow_rejects_whole_result() -> None:
    arguments = synthesis_overflow_arguments()
    # Each +/-1 spectrum amplitude is 3e307/(0.25*1.125) = 1.0667e308,
    # safely finite. Their sum at spatial index zero is 2.1333e308, outside
    # float64 coordinate range. No exact-real edge classification is assumed.
    before = input_snapshot(arguments)
    rejects(arguments, "unrepresentable_reconstruction")
    assert_inputs_preserved(arguments, before)


def test_large_complex_magnitude_does_not_reject_finite_coordinates() -> None:
    arguments = basic((1, 3))
    arguments["otf"] = record(np.array([[0.125, 1, 0.125]], dtype=np.complex128))
    x = np.arange(3)
    unit = np.exp(2j * np.pi * x / 3)
    arguments["images"][:] = (2 * np.real((1 + 1j) * unit) * 0.125 * 1.125) * 1.3e308
    arguments["apodization"][1, 2] = 0  # Suppress conjugate q=-1, retain q=+1.
    result = call(arguments)
    # Spectrum coordinates 1.3e308 are finite though their complex magnitude
    # exceeds max. On the 6-sample synthesis grid the largest coordinate is
    # 1.3e308*(sqrt(3)+1)/2 < max, so rejection would be avoidable.
    assert np.all(np.isfinite(result.spectrum.real))
    assert np.all(np.isfinite(result.spectrum.imag))
    assert np.all(np.isfinite(result.image.real))
    assert np.all(np.isfinite(result.image.imag))
    # Brightness is ordinary, but B is extreme and this fixture's denominator
    # is informative. Check coordinates using Decimal budget arithmetic rather
    # than a new normalized relative tolerance or overflowing complex magnitude.
    assert_reference(arguments)


def test_known_brightness_scaling_invariance(exact_phantom: Any) -> None:
    arguments, _, truth = exact_phantom
    arguments = arguments.copy()
    arguments["images"] = arguments["images"] * 2
    arguments["brightness"] = arguments["brightness"] * 2
    result = call(arguments)
    assert_analytic(arguments, result, image=truth)


def test_numeric_observer_accepts_envelope_and_distinguishes_wrong_conventions() -> None:
    """Exercise observer alternatives independently, without product mutation."""
    arguments = basic((1, 1))
    budget = accuracy_budget(arguments)
    expected = np.array([[complex(2, -1)]])
    admitted = expected + complex(float(budget / 2), float(-budget / 2))
    assert_coordinates(admitted, expected, budget)
    # A permitted result differing by more than the former fixed 2e-12 bound
    # still passes the contract observer. Sign/gain/normalization changes do not.
    assert_coordinates(expected + 1.2e-11, expected, budget)
    for wrong in (expected.conjugate(), expected * 2, expected / 4):
        with pytest.raises(AssertionError):
            assert_coordinates(wrong, expected, budget)
    for unusable_reference in (np.inf, np.nan):
        with pytest.raises(AssertionError):
            assert_coordinates(expected, unusable_reference, budget)
    # Rebasing to analytic truth includes stored-data bias, not a tighter test.
    assert_coordinates(admitted, expected, budget, analytic=expected + 0.01)
