"""ILLUMINATION-01 blind A public-entry acceptance tests.

Run through artifacts/illumination-execution/blind_pytest.py for source-free diagnostics.
No expectations use simrecon's separation, calibration or estimation output.
"""

import json
from collections.abc import Callable
from typing import Any, Literal

import numpy as np
import pytest

import simrecon
from illumination_fixture import (
    Acquisition,
    acquisition,
    circular_error,
    continuous_specimen,
    fault_subprocess_report,
    finite_dft,
    grid,
    rotated_phases,
    stored_fit,
)

EPS = 2.0**-52


class ArraySubclass(np.ndarray):
    """An explicitly disallowed ndarray subclass."""


def public(name: str) -> Any:
    value = getattr(simrecon, name, None)
    if value is None:
        pytest.fail(f"Missing public simrecon export: {name}", pytrace=False)
    return value


def calibration(fixture: Acquisition, **changes: Any) -> Any:
    fy, fx = grid(fixture.transfer.shape, fixture.pixel_size)
    fields: dict[str, Any] = {
        "values": fixture.transfer.copy(),
        "fy_per_um": fy,
        "fx_per_um": fx,
        "pixel_size_um": fixture.pixel_size,
        "origin_yx": fixture.origin,
        "source": fixture.source,
    }
    fields.update(changes)
    return public("Otf2D")(**fields)


def estimate(fixture: Acquisition, **changes: Any) -> Any:
    fields: dict[str, Any] = {
        "otf": calibration(fixture),
        "phase_steps_rad": fixture.steps,
        "carrier_bins_yx": fixture.carrier,
    }
    images = changes.pop("images", fixture.images)
    fields.update(changes)
    record = fields["otf"]
    caller_values = [images, fields["phase_steps_rad"], fields["carrier_bins_yx"]]
    caller_values += [
        getattr(record, name, None)
        for name in ("values", "fy_per_um", "fx_per_um", "pixel_size_um", "origin_yx")
    ]
    snapshots = [(array, array.copy()) for array in caller_values if isinstance(array, np.ndarray)]
    try:
        result = public("estimate_illumination")(images, **fields)
        assert -np.pi <= result.phase_offset_rad <= np.pi
        return result
    finally:
        for array, snapshot in snapshots:
            np.testing.assert_array_equal(array, snapshot)


def assert_code(code: str, operation: Callable[[], Any]) -> None:
    with pytest.raises(public("SimreconError")) as caught:
        operation()
    assert caught.value.code == code
    assert isinstance(caught.value.message, str)
    assert caught.value.message


def assert_fit(fixture: Acquisition, result: Any, *, informative: bool = True) -> None:
    assert -np.pi <= result.phase_offset_rad <= np.pi
    truth = stored_fit(fixture.images, fixture.steps, fixture.transfer, fixture.carrier)
    if informative:
        assert truth.informative, "Fixture must qualify before applying normative budget"
    delta = 8192 * len(fixture.steps) * fixture.transfer.size * EPS
    gain = 0.5 * result.modulation * np.exp(1j * result.phase_offset_rad)
    assert abs(gain - truth.gain) <= delta * max(1, abs(truth.gain))
    assert abs(result.relative_residual - truth.residual) <= delta
    assert result.overlap_count == truth.overlap
    expected_phases = rotated_phases(fixture.steps, result.phase_offset_rad)
    assert np.max(np.abs(circular_error(result.phases_rad, expected_phases))) <= 64 * EPS
    assert np.all(result.phases_rad >= -np.pi)
    assert np.all(result.phases_rad <= np.pi)


def test_e01_exports_record_and_success() -> None:
    fixture = acquisition()
    result = estimate(fixture)
    assert isinstance(result, public("IlluminationEstimate"))
    assert_fit(fixture, result)
    assert result.source == fixture.source
    for name in ("phase_offset_rad", "modulation", "relative_residual"):
        assert type(getattr(result, name)) is float
    assert type(result.overlap_count) is int


@pytest.mark.parametrize(
    "case", ["no-images", "no-otf", "no-steps", "no-carrier", "positional", "extra"]
)
def test_e01_required_keyword_only_binding(case: str) -> None:
    fixture = acquisition()
    function = public("estimate_illumination")
    fields = {
        "otf": calibration(fixture),
        "phase_steps_rad": fixture.steps,
        "carrier_bins_yx": fixture.carrier,
    }
    with pytest.raises(TypeError):
        if case == "no-images":
            function(**fields)
        elif case == "positional":
            function(fixture.images, *fields.values())
        elif case == "extra":
            function(fixture.images, **fields, extra=True)
        else:
            del fields[
                {"no-otf": "otf", "no-steps": "phase_steps_rad", "no-carrier": "carrier_bins_yx"}[
                    case
                ]
            ]
            function(fixture.images, **fields)


@pytest.mark.parametrize(
    "case,code",
    [
        ("image-list", "invalid_phase_images"),
        ("image-subclass", "invalid_phase_images"),
        ("image-bool", "invalid_phase_dtype"),
        ("image-complex", "invalid_phase_dtype"),
        ("image-object", "invalid_phase_dtype"),
        ("image-2d", "invalid_phase_shape"),
        ("image-few", "invalid_phase_shape"),
        ("image-empty", "invalid_phase_shape"),
        ("image-nan", "nonfinite_phase_images"),
        ("image-inf", "nonfinite_phase_images"),
        ("steps-list", "invalid_phase_angles"),
        ("steps-subclass", "invalid_phase_angles"),
        ("steps-bool", "invalid_phase_angles_dtype"),
        ("steps-complex", "invalid_phase_angles_dtype"),
        ("steps-object", "invalid_phase_angles_dtype"),
        ("steps-column", "invalid_phase_angles_shape"),
        ("steps-count", "invalid_phase_angles_shape"),
        ("steps-nan", "nonfinite_phase_angles"),
        ("steps-inf", "nonfinite_phase_angles"),
        ("rank-identical", "rank_deficient_phases"),
        ("rank-roundoff", "rank_deficient_phases"),
    ],
)
def test_e02_inherited_validation_codes(case: str, code: str) -> None:
    fixture = acquisition()
    images: Any = fixture.images.copy()
    steps: Any = fixture.steps.copy()
    if case == "image-list":
        images = images.tolist()
    elif case == "image-subclass":
        images = images.view(ArraySubclass)
    elif case.startswith("image-") and case[6:] in {"bool", "complex", "object"}:
        images = images.astype({"bool": bool, "complex": complex, "object": object}[case[6:]])
    elif case == "image-2d":
        images = images[0]
    elif case == "image-few":
        images, steps = images[:2], steps[:2]
    elif case == "image-empty":
        images = images[:, :0]
    elif case in {"image-nan", "image-inf"}:
        images[0, 0, 0] = np.nan if case.endswith("nan") else -np.inf
    elif case == "steps-list":
        steps = steps.tolist()
    elif case == "steps-subclass":
        steps = steps.view(ArraySubclass)
    elif case.startswith("steps-") and case[6:] in {"bool", "complex", "object"}:
        steps = steps.astype({"bool": bool, "complex": complex, "object": object}[case[6:]])
    elif case == "steps-column":
        steps = steps[:, None]
    elif case == "steps-count":
        steps = steps[:-1]
    elif case in {"steps-nan", "steps-inf"}:
        steps[0] = np.nan if case.endswith("nan") else np.inf
    elif case == "rank-identical":
        steps[:] = 0
    elif case == "rank-roundoff":
        steps[:] = np.resize([0.0, np.pi, 2 * np.pi], len(steps))
    assert_code(code, lambda: estimate(fixture, images=images, phase_steps_rad=steps))


# Unsupported representations are reported by A, not discovered as skipped tests.
# Same-width longdouble remains in REAL_DTYPES for both permitted-input tests.
if np.finfo(np.longdouble).max > np.finfo(np.float64).max:

    @pytest.mark.parametrize("target", ["images", "steps"])
    def test_e02_wider_source_conversion_overflow(target: str) -> None:
        fixture = acquisition()
        value = np.finfo(np.longdouble).max  # An actually available finite source.
        if target == "images":
            data = fixture.images.astype(np.longdouble)
            data[0, 0, 0] = value
            assert_code("nonfinite_phase_images", lambda: estimate(fixture, images=data))
        else:
            steps = fixture.steps.astype(np.longdouble)
            steps[0] = value
            assert_code("nonfinite_phase_angles", lambda: estimate(fixture, phase_steps_rad=steps))


REAL_DTYPES = [
    "i1",
    "u1",
    "i2",
    "u2",
    "i4",
    "u4",
    "i8",
    "u8",
    "f2",
    "f4",
    "f8",
    ">f8",
    ">i4",
    np.longdouble,
]


@pytest.mark.parametrize("dtype", REAL_DTYPES)
def test_e02_permitted_image_dtypes_use_stored_values(dtype: Any) -> None:
    fixture = acquisition()
    images = (fixture.images * 32).astype(dtype)
    rounded = Acquisition(
        images,
        fixture.steps,
        fixture.transfer,
        fixture.carrier,
        fixture.specimen,
        fixture.brightness,
        fixture.modulation,
        fixture.theta,
    )
    assert_fit(rounded, estimate(rounded))


@pytest.mark.parametrize("dtype", REAL_DTYPES)
def test_e02_permitted_step_dtypes_use_stored_values(dtype: Any) -> None:
    steps = np.array([0, 1, 2, 3, 4, 5], dtype=dtype)
    fixture = acquisition(steps=steps.astype(np.float64))
    assert_fit(fixture, estimate(fixture, phase_steps_rad=steps))


def test_e02_int64_uint64_rounding_is_converted_problem() -> None:
    for dtype in (np.int64, np.uint64):
        fixture = acquisition()
        images = (fixture.images * 2.0**54).astype(dtype)
        images += 1  # Nonrepresentable low bit distinguishes stored integer truth.
        rounded = Acquisition(
            images,
            fixture.steps,
            fixture.transfer,
            fixture.carrier,
            fixture.specimen,
            fixture.brightness,
            fixture.modulation,
            fixture.theta,
        )
        assert any(
            int(original) != int(converted)
            for original, converted in zip(images.flat, images.astype(np.float64).flat, strict=True)
        )
        assert_fit(rounded, estimate(rounded))


@pytest.mark.parametrize("span", [0.2, 2e-4])
def test_e02_full_rank_small_span_is_accepted_without_condition_cutoff(span: float) -> None:
    fixture = acquisition(steps=np.array([0.0, span / 2, span]))
    result = estimate(fixture)
    assert np.isfinite(result.modulation) and result.modulation > 0
    assert np.isfinite(result.phase_offset_rad)
    assert np.isfinite(result.relative_residual)


@pytest.mark.parametrize(
    "carrier",
    [
        (1.0, -1),
        (True, 1),
        (1, np.bool_(False)),
        [1],
        [1, 2, 3],
        "1,2",
        1,
        np.array([[1, 2]]),
        np.array([1, 2], dtype=float),
        np.array([1, 2]).view(ArraySubclass),
    ],
)
def test_e03_invalid_carrier(carrier: Any) -> None:
    assert_code(
        "invalid_illumination_carrier", lambda: estimate(acquisition(), carrier_bins_yx=carrier)
    )


@pytest.mark.parametrize("container", ["tuple", "list", "array", "object-array", "readonly-view"])
def test_e03_permitted_integer_pair_containers(container: str) -> None:
    fixture = acquisition(carrier=(-1, 1))
    carrier: Any = (np.int64(-1), np.int32(1))
    if container == "list":
        carrier = list(carrier)
    elif container == "array":
        carrier = np.array(carrier, dtype=">i8")
    elif container == "object-array":
        carrier = np.array(carrier, dtype=object)
    elif container == "readonly-view":
        carrier = np.array([-1, 99, 1, 99])[::2]
        carrier.flags.writeable = False
    assert_fit(fixture, estimate(fixture, carrier_bins_yx=carrier))


@pytest.mark.parametrize(
    "case",
    [
        "record-type",
        "values-list",
        "values-subclass",
        "values-real",
        "values-c64",
        "values-shape",
        "values-nan",
        "values-inf",
        "fy-list",
        "fx-subclass",
        "fy-f32",
        "fx-shape",
        "fy-nan",
        "fx-inf",
        "spacing-container",
        "spacing-bool",
        "spacing-zero",
        "spacing-negative",
        "spacing-inf",
        "spacing-nan",
        "origin-fraction",
        "origin-bool",
        "origin-negative",
        "origin-end",
        "origin-shape",
        "source-type",
        "source-blank",
        "dc",
        "magnitude",
        "hermitian",
    ],
)
def test_e04_invalid_direct_otf_record(case: str) -> None:
    fixture = acquisition()
    record = calibration(fixture)
    changes: dict[str, Any] = {}
    if case == "record-type":
        invalid = object()
    else:
        if case.startswith("values-"):
            values: Any = record.values.copy()
            suffix = case[7:]
            if suffix == "list":
                values = values.tolist()
            elif suffix == "subclass":
                values = values.view(ArraySubclass)
            elif suffix in {"real", "c64"}:
                values = values.real.copy() if suffix == "real" else values.astype(np.complex64)
            elif suffix == "shape":
                values = values[:, :-1]
            else:
                values[0, 0] = np.nan if suffix == "nan" else np.inf
            changes["values"] = values
        elif case.startswith(("fy-", "fx-")):
            axis, suffix = case.split("-")
            name = f"{axis}_per_um"
            vector: Any = getattr(record, name).copy()
            if suffix == "list":
                vector = vector.tolist()
            elif suffix == "subclass":
                vector = vector.view(ArraySubclass)
            elif suffix == "f32":
                vector = vector.astype(np.float32)
            elif suffix == "shape":
                vector = vector[:, None]
            else:
                vector[0] = np.nan if suffix == "nan" else np.inf
            changes[name] = vector
        elif case.startswith("spacing-"):
            changes["pixel_size_um"] = {
                "spacing-container": 1,
                "spacing-bool": (True, 1),
                "spacing-zero": (0, 1),
                "spacing-negative": (-1, 1),
                "spacing-inf": (np.inf, 1),
                "spacing-nan": (np.nan, 1),
            }[case]
        elif case.startswith("origin-"):
            changes["origin_yx"] = {
                "origin-fraction": (0.5, 0),
                "origin-bool": (False, 0),
                "origin-negative": (-1, 0),
                "origin-end": (fixture.images.shape[1], 0),
                "origin-shape": [0],
            }[case]
        elif case.startswith("source-"):
            changes["source"] = 17 if case == "source-type" else " \t "
        else:
            transfer = record.values.copy()
            if case == "dc":
                transfer[2, 3] = 0.8
            elif case == "magnitude":
                transfer[2, 2] = transfer[2, 4] = 1.1
            else:
                transfer[2, 2] += 0.1j
            changes["values"] = transfer
        invalid = calibration(fixture, **changes)
    assert_code("invalid_illumination_otf", lambda: estimate(fixture, otf=invalid))


@pytest.mark.parametrize(
    "case", ["wrong-spacing", "reversed", "collapsed", "nonzero-dc", "wrong-axis"]
)
def test_e04_incompatible_physical_grid(case: str) -> None:
    fixture = acquisition()
    fy, fx = grid(fixture.transfer.shape, fixture.pixel_size)
    if case == "wrong-spacing":
        fy *= 1.01
    elif case == "reversed":
        fx = fx[::-1]
    elif case == "collapsed":
        fy[0] = fy[1]
    elif case == "nonzero-dc":
        fx[len(fx) // 2] = 0.01
    else:
        fx *= 2 * np.pi
    assert_code(
        "incompatible_illumination_otf_grid",
        lambda: estimate(fixture, otf=calibration(fixture, fy_per_um=fy, fx_per_um=fx)),
    )


def test_e04_direct_endian_strided_readonly_otf_and_metadata_pairs() -> None:
    fixture = acquisition()
    record = calibration(fixture)

    def storage(array: Any, dtype: str) -> Any:
        backing = np.zeros(tuple(2 * n for n in array.shape), dtype=dtype)
        view = backing[tuple(slice(None, None, 2) for _ in array.shape)]
        view[...] = array
        view.flags.writeable = False
        return view

    record = calibration(
        fixture,
        values=storage(record.values, ">c16"),
        fy_per_um=storage(record.fy_per_um, ">f8"),
        fx_per_um=storage(record.fx_per_um, ">f8"),
        pixel_size_um=np.array(fixture.pixel_size),
        origin_yx=[0, 0],
    )
    assert_fit(fixture, estimate(fixture, otf=record))
    assert np.any(fixture.transfer.real < 0)
    assert np.max(np.abs(fixture.transfer.imag)) > 0.1


def test_e04_prepared_otf_is_input_only_independently_confirmed() -> None:
    fixture = acquisition()
    kernel = np.zeros(fixture.transfer.shape)
    kernel[0, 0], kernel[1, 0], kernel[0, 1] = 3, 1, 4
    record = public("prepare_otf")(
        kernel,
        pixel_size_um=fixture.pixel_size,
        origin_yx=(0, 0),
        source=fixture.source,
    )
    assert np.max(np.abs(record.values - fixture.transfer)) <= 128 * kernel.size * EPS
    assert_fit(fixture, estimate(fixture, otf=record))


@pytest.mark.parametrize("case", ["singleton-q", "multi-point-max", "combined"])
def test_e04_direct_extreme_spacing_grid_is_accepted(case: str) -> None:
    from decimal import Decimal, localcontext

    base = acquisition((1, 4), carrier=(0, 0))
    quantum = np.nextafter(0.0, 1.0)
    largest = np.finfo(np.float64).max
    spacing = (
        float(quantum) if case != "multi-point-max" else 0.2,
        float(largest) if case != "singleton-q" else 0.35,
    )
    fixture = Acquisition(
        base.images,
        base.steps,
        base.transfer,
        base.carrier,
        base.specimen,
        base.brightness,
        base.modulation,
        base.theta,
        pixel_size=spacing,
    )
    # Independent finite frequency truth: divide signed bin by N, then spacing.
    # Never form N*spacing, and never require reconstruction's halved spacing.
    with localcontext() as context:
        context.prec = 90
        fx = np.array([float(Decimal(k) / 4 / Decimal(spacing[1])) for k in (-2, -1, 0, 1)])
    fy = np.array([0.0])
    assert np.all(np.isfinite(fx)) and np.all(np.diff(fx) > 0)
    assert np.all(fx[[0, 1, 3]] != 0)
    truth = stored_fit(fixture.images, fixture.steps, fixture.transfer, fixture.carrier)
    assert truth.informative
    record = calibration(fixture, fy_per_um=fy, fx_per_um=fx)
    assert_fit(fixture, estimate(fixture, otf=record))


def test_e04_accepted_grid_transfer_tolerances_and_encoded_origin() -> None:
    fixture = acquisition()
    fy, fx = grid(fixture.transfer.shape, fixture.pixel_size)
    fy = np.nextafter(fy, np.where(fy == 0, 0, np.inf))
    fx = np.nextafter(fx, np.where(fx == 0, 0, -np.inf))
    transfer = np.ones(fixture.transfer.shape, dtype=np.complex128)
    tau = 128 * transfer.size * EPS
    transfer += tau / 4
    # A valid consumer record need not be exactly realizable as a nonnegative PSF.
    record = calibration(
        fixture,
        values=transfer,
        fy_per_um=fy,
        fx_per_um=fx,
        origin_yx=np.array([3, 5], dtype=np.int32),
        pixel_size_um=list(fixture.pixel_size),
    )
    changed = Acquisition(
        fixture.images,
        fixture.steps,
        transfer,
        fixture.carrier,
        fixture.specimen,
        fixture.brightness,
        fixture.modulation,
        fixture.theta,
    )
    assert_fit(changed, estimate(changed, otf=record))


def test_e04_nonzero_hermitian_difference_within_two_tau_is_accepted() -> None:
    base = acquisition()
    transfer = base.transfer.copy()
    tau = 128 * transfer.size * EPS
    transfer[2, 2] += 1.5j * tau
    # On this odd centered grid, modular frequency negation reverses both axes.
    difference = np.max(np.abs(transfer - transfer[::-1, ::-1].conj()))
    assert tau < difference < 2 * tau
    assert np.all(np.isfinite(transfer))
    assert transfer[2, 3] == 1 + 0j
    assert np.max(np.abs(transfer)) <= 1
    changed = Acquisition(
        base.images,
        base.steps,
        transfer,
        base.carrier,
        base.specimen,
        base.brightness,
        base.modulation,
        base.theta,
    )
    truth = stored_fit(changed.images, changed.steps, transfer, changed.carrier)
    assert truth.informative
    assert np.isfinite(truth.gain) and np.isfinite(truth.residual)
    # The shared public entry snapshots the perturbed transfer and other inputs.
    assert_fit(changed, estimate(changed))


def test_e05_overlap_count_includes_zero_transfer_pairs() -> None:
    fixture = acquisition(carrier=(0, 0))
    transfer = np.zeros(fixture.transfer.shape, dtype=np.complex128)
    transfer[2, 3] = 1
    changed = Acquisition(
        fixture.images,
        fixture.steps,
        transfer,
        fixture.carrier,
        fixture.specimen,
        fixture.brightness,
        fixture.modulation,
        fixture.theta,
    )
    result = estimate(changed)
    assert_fit(changed, result)
    assert result.overlap_count == transfer.size


@pytest.mark.parametrize(
    "shape,carrier,count",
    [
        ((1, 1), (0, 0), 1),
        ((1, 4), (0, -3), 1),
        ((4, 1), (3, 0), 1),
        ((3, 4), (1, -1), 6),
        ((4, 6), (-1, 2), 12),
        ((4, 6), (0, 0), 24),
        ((3, 5), (2, 4), 1),
        ((3, 5), (-2, -4), 1),
    ],
)
def test_e05_closed_overlap_signed_endpoints_no_wrap(
    shape: tuple[int, int], carrier: tuple[int, int], count: int
) -> None:
    base = acquisition(shape, carrier=carrier)
    ny, nx = shape
    yy, xx = np.indices(shape)
    qy = -(ny // 2) if carrier[0] > 0 else (ny - ny // 2 - 1 if carrier[0] < 0 else 0)
    qx = -(nx // 2) if carrier[1] > 0 else (nx - nx // 2 - 1 if carrier[1] < 0 else 0)
    dc = np.cos(2 * np.pi * (qy * yy / ny + qx * xx / nx))
    c1 = 0.6 * np.exp(
        1j * (2 * np.pi * ((qy + carrier[0]) * yy / ny + (qx + carrier[1]) * xx / nx) + 0.4)
    )
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in base.steps])
    fixture = Acquisition(
        images,
        base.steps,
        np.ones(shape, dtype=np.complex128),
        carrier,
        dc,
        1.0,
        1.2,
        0.4,
    )
    # These explicit nonphysical endpoint bands follow the stored-data fit.
    result = estimate(fixture)
    assert_fit(fixture, result)
    assert result.overlap_count == count


@pytest.mark.parametrize("carrier", [(5, 0), (0, -7), (0, 10**400), (-(10**400), 0)])
def test_e05_no_overlap_including_unbounded_python_integers(carrier: tuple[int, int]) -> None:
    assert_code("no_illumination_overlap", lambda: estimate(acquisition(), carrier_bins_yx=carrier))


@pytest.mark.parametrize("shape,carrier", [((1, 4), (1, 0)), ((4, 1), (0, -1)), ((1, 1), (0, 1))])
def test_e05_singleton_nonzero_shift_has_no_overlap(
    shape: tuple[int, int], carrier: tuple[int, int]
) -> None:
    assert_code(
        "no_illumination_overlap", lambda: estimate(acquisition(shape), carrier_bins_yx=carrier)
    )


def test_e05_huge_integer_object_array_is_valid_representation_without_overlap() -> None:
    carrier = np.array([10**400, 0], dtype=object)
    assert_code("no_illumination_overlap", lambda: estimate(acquisition(), carrier_bins_yx=carrier))


@pytest.mark.parametrize(
    "carrier,theta,brightness", [((1, -1), 0.7, 0.2), ((-1, 1), -1.2, 3.0), ((0, 1), 2.7, 1.0)]
)
def test_e06_model_sign_factor_two_specimen_brightness_cancellation(
    carrier: tuple[int, int], theta: float, brightness: float
) -> None:
    fixture = acquisition(carrier=carrier, theta=theta, brightness=brightness)
    truth = stored_fit(fixture.images, fixture.steps, fixture.transfer, fixture.carrier)
    analytic = fixture.modulation / 2 * np.exp(1j * theta)
    assert abs(truth.gain - analytic) < 2e-13
    assert truth.residual < 2e-13
    result = estimate(fixture)
    assert_fit(fixture, result)
    assert abs(result.modulation - fixture.modulation) < 2e-11
    assert abs(circular_error(result.phase_offset_rad, theta)) < 2e-11


def test_e07_off_model_complex_regression_and_direct_small_residual() -> None:
    for perturbation in (1.0, 1e-6):
        base = acquisition()
        altered = acquisition(off_model=True)
        images = base.images + perturbation * (altered.images - base.images)
        fixture = Acquisition(
            images,
            base.steps,
            base.transfer,
            base.carrier,
            base.specimen,
            base.brightness,
            base.modulation,
            base.theta,
        )
        truth = stored_fit(images, base.steps, base.transfer, base.carrier)
        assert truth.informative
        assert truth.residual > (1e-3 if perturbation == 1 else 1e-9)
        result = estimate(fixture)
        assert_fit(fixture, result)
        assert result.relative_residual > 0
        if perturbation == 1e-6:
            assert abs(result.relative_residual - truth.residual) < 2e-12


def test_e06_distinct_signed_specimen_cancels() -> None:
    yy, xx = np.indices((5, 7))
    specimen = -2 - 0.8 * np.cos(2 * np.pi * xx / 7) + 0.45 * np.sin(2 * np.pi * yy / 5)
    fixture = acquisition(specimen=specimen, brightness=2.3)
    result = estimate(fixture)
    assert_fit(fixture, result)
    assert abs(result.modulation - fixture.modulation) < 2e-11
    assert abs(circular_error(result.phase_offset_rad, fixture.theta)) < 2e-11


@pytest.mark.parametrize("case", ["all-zero", "x-zero", "y-zero", "cross-zero"])
def test_e08_structurally_exact_zero_information(case: str) -> None:
    # Exact OTF zero factors, not a demand that an FFT cancel roundoff to zero.
    fixture = acquisition((1, 3), carrier=(0, 1))
    transfer = np.array([[0, 1, 0]], dtype=np.complex128)
    spatial = np.array([[1.0, -0.5, -0.5]])
    images = np.array([spatial * (1 + np.cos(p)) for p in fixture.steps])
    carrier = (0, 1)
    if case == "all-zero":
        images = np.zeros_like(images)
    elif case == "x-zero":
        # Q has only q=0; H(q+k)=0, H(q)=1.
        fixture = acquisition((1, 2), carrier=(0, -1))
        transfer = np.array([[0, 1]], dtype=np.complex128)
        images = np.array(
            [np.array([[1.0, 1.0]]) + np.cos(p) * np.array([[1.0, -1.0]]) for p in fixture.steps]
        )
        carrier = (0, -1)
    elif case == "y-zero":
        # Q has only q=-1; H(q)=0, H(q+k)=1.
        fixture = acquisition((1, 2), carrier=(0, 1))
        transfer = np.array([[0, 1]], dtype=np.complex128)
        images = np.array([np.array([[1.0, -1.0]]) + np.cos(p) for p in fixture.steps])
    # cross-zero: disjoint x/y supports on q=-1 and q=0, each informative.
    assert_code(
        "unidentifiable_illumination",
        lambda: estimate(
            fixture,
            images=images,
            otf=calibration(fixture, values=transfer),
            carrier_bins_yx=carrier,
        ),
    )


def test_e08_weak_nonzero_overlap_and_tiny_gain_are_accepted() -> None:
    fixture = acquisition((1, 2), carrier=(0, 1))
    tiny = 2.0**-500
    transfer = np.array([[tiny, 1]], dtype=np.complex128)
    images = np.array([np.array([[1.0, -1.0]]) + 0.6 * np.cos(p) for p in fixture.steps]) * tiny
    result = estimate(fixture, images=images, otf=calibration(fixture, values=transfer))
    # Outside the informative regime: assert acceptance/representation, no digits.
    assert 0 < result.modulation < 1
    assert np.isfinite(result.phase_offset_rad)
    assert np.isfinite(result.relative_residual)
    assert result.overlap_count == 1


@pytest.mark.parametrize("aligned", [0.0, 1e-8])
def test_e08_cancelling_and_nearly_cancelling_nonzero_products(aligned: float) -> None:
    fixture = acquisition((1, 4), carrier=(0, 0))
    dc = np.array([[1.0, 0.0, -1.0, 0.0]])
    c1 = np.array([[0.0, 1.0, 0.0, -1.0]]) + aligned * dc
    images = np.array([dc + 2 * c1 * np.cos(p) for p in fixture.steps])
    # Exact opposite imaginary Fourier products cancel when aligned=0. Computed
    # roundoff may leave a nonzero gain; no uniform digits apply in this regime.
    try:
        result = estimate(
            fixture, images=images, otf=calibration(fixture, values=np.ones((1, 4), complex))
        )
    except public("SimreconError") as error:
        assert aligned == 0
        assert error.code == "unidentifiable_illumination"
    else:
        assert result.modulation > 0
        assert np.isfinite(result.modulation)
        assert np.isfinite(result.phase_offset_rad)
        assert np.isfinite(result.relative_residual)


def test_e09_modulation_above_one_is_unconstrained() -> None:
    fixture = acquisition(modulation=2.4)
    result = estimate(fixture)
    assert_fit(fixture, result)
    assert abs(result.modulation - 2.4) < 2e-11
    assert result.modulation > 1
    assert np.min(fixture.images) < 0


def test_e10_large_steps_rotate_represented_trigonometry() -> None:
    steps = np.array([1e20, -1e20, 1e100, -1e100, 1e200, -1e200, 1e300, -1e300])
    fixture = acquisition(steps=steps, theta=0.73)
    result = estimate(fixture)
    assert_fit(fixture, result)
    assert np.max(np.abs(circular_error(result.phases_rad, steps + result.phase_offset_rad))) > 0.1
    assert (
        np.max(
            np.abs(
                circular_error(
                    result.phases_rad, np.remainder(steps, 2 * np.pi) + result.phase_offset_rad
                )
            )
        )
        > 0.1
    )


@pytest.mark.parametrize("theta", [np.pi, -np.pi, np.pi - 1e-10, -np.pi + 1e-10])
def test_e10_branch_cut_is_compared_circularly(theta: float) -> None:
    fixture = acquisition(theta=theta)
    assert_fit(fixture, estimate(fixture))


@pytest.mark.parametrize("exponent", [-1000, -900, -500, 0, 500, 900, 1018])
def test_e11_common_gain_extremes_avoid_raw_norm_transform_overflow(exponent: int) -> None:
    base = acquisition()
    images = np.ldexp(base.images, exponent)
    fixture = Acquisition(
        images,
        base.steps,
        base.transfer,
        base.carrier,
        base.specimen,
        base.brightness,
        base.modulation,
        base.theta,
    )
    assert np.all(np.isfinite(images))
    assert_fit(fixture, estimate(fixture))


def test_e11_subnormal_stored_observations_have_no_invented_cutoff() -> None:
    fixture = acquisition((1, 1), carrier=(0, 0))
    quantum = np.nextafter(0.0, 1.0)
    images = np.array([100, 130, 160, 150, 90, 60], dtype=np.float64)[:, None, None] * quantum
    result = estimate(fixture, images=images)
    assert 0 < result.modulation < np.inf
    assert np.isfinite(result.phase_offset_rad)
    assert np.isfinite(result.relative_residual)


def test_e11_finite_modulation_when_intermediate_norm_ratio_overflows() -> None:
    fixture = acquisition((1, 4), carrier=(0, 2))
    tiny = 1e-310
    transfer = np.array([[1, tiny, 1, tiny]], dtype=np.complex128)
    dc = np.array([[1.0, 1.0, 2.0, 2.0]])
    c1 = np.array([[0.6, 0.6, 0.2, 0.2]]) * np.exp(0.4j)
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in fixture.steps])
    # Pairwise-identical spatial columns make D0(-2) exactly zero, independently
    # of pointwise phase-solver roundoff. x is only at q=-1 with scale tiny;
    # y has O(1) energy at q=-2 and scale tiny at q=-1. norm(y)/norm(x)>max,
    # but fitted modulation is 2*abs((.6-.2)/(1-2))=.8, safely finite.
    result = estimate(fixture, images=images, otf=calibration(fixture, values=transfer))
    assert 0 < result.modulation < np.inf
    assert np.isfinite(result.relative_residual)
    assert np.isfinite(result.phase_offset_rad)


def test_e11_final_modulation_survives_unrepresentable_intermediate_gain() -> None:
    fixture = acquisition((1, 2), carrier=(0, 1))
    quantum = np.nextafter(0.0, 1.0)
    transfer = np.array([[quantum, 1]], dtype=np.complex128)
    images = np.array([np.array([[3.0, -3.0]]) + 2 * np.cos(p) for p in fixture.steps])
    # x=3, y=q, z=q/3 rounds to zero, but modulation=2*q/3 rounds to q.
    # Final modulation, not a materialized complex gain, defines range.
    result = estimate(fixture, images=images, otf=calibration(fixture, values=transfer))
    assert result.modulation == quantum
    assert np.isfinite(result.relative_residual)
    assert np.isfinite(result.phase_offset_rad)


def test_e11_finite_observations_unrepresentable_final_modulation() -> None:
    fixture = acquisition((1, 2), carrier=(0, -1))
    transfer = np.array([[1e-310, 1]], dtype=np.complex128)
    images = np.array(
        [np.array([[1.0, 1.0]]) + 0.6 * np.cos(p) * np.array([[1.0, -1.0]]) for p in fixture.steps]
    )
    # x=1e-310*D0(0) ~1e-310; y=Dplus(-1) ~0.3 -> m~6e309.
    assert_code(
        "unrepresentable_illumination",
        lambda: estimate(fixture, images=images, otf=calibration(fixture, values=transfer)),
    )


def assert_injected_fault(
    report: dict[str, Any],
    *,
    action: str,
    code: str | None = None,
    exception: type[Exception] | None = None,
) -> None:
    """Assess only protected JSON; setup/reachability failure is incomplete evidence."""
    if report["status"] == "missing_export":
        pytest.fail(report["exception"]["message"], pytrace=False)
    if report["status"] in {
        "setup_exception",
        "diagnostic_failure",
        "bootstrap_failure",
        "child_startup_failure",
        "child_protocol_defect",
        "preimport_defect",
    }:
        pytest.fail(
            "HARNESS_SETUP_DEFECT: incomplete evidence; " + json.dumps(report), pytrace=False
        )
    if not report.get("injections"):
        pytest.fail(
            "HARNESS_REACHABILITY_DEFECT: incomplete evidence, not product-red; "
            "diagnose valid backend and return correction to A/fresh B; " + json.dumps(report),
            pytrace=False,
        )
    assert report["returncode"] == 0
    assert report["stage"] == "call"
    assert report["status"] == "call_exception"
    assert report["inputs_preserved"] is True
    assert all(event["action"] == action for event in report["injections"])
    error = report["exception"]
    assert isinstance(error["type"], str) and error["type"]
    assert isinstance(error["message"], str) and error["message"]
    assert error["locations"]
    if code is not None:
        assert report["is_domain_error"] is True
        assert error["code"] == code
        assert isinstance(error["domain_message"], str) and error["domain_message"]
    else:
        assert exception is not None
        assert error["type"] == exception.__name__
        assert error["code"] is None
        assert error["message"] == "controlled public numerical boundary failure"


@pytest.mark.parametrize("action", ["value", "floating", "overflow", "nonfinite"])
def test_e12_transform_failure_classification(action: str) -> None:
    report = fault_subprocess_report("transform", action)
    assert_injected_fault(report, action=action, code="illumination_solver_failure")


@pytest.mark.parametrize("action", ["linalg", "nonfinite"])
def test_e12_inherited_phase_solver_failure(action: str) -> None:
    report = fault_subprocess_report("phase", action)
    assert_injected_fault(report, action=action, code="phase_solver_failure")


@pytest.mark.parametrize("family", ["transform", "phase"])
@pytest.mark.parametrize("action,exception", [("memory", MemoryError), ("unrelated", RuntimeError)])
def test_e12_unrelated_and_allocation_failures_propagate(
    family: str,
    action: str,
    exception: type[Exception],
) -> None:
    report = fault_subprocess_report(family, action)
    assert_injected_fault(report, action=action, exception=exception)


def test_e12_inherited_final_phase_output_range() -> None:
    fixture = acquisition((1, 1), carrier=(0, 0), steps=np.array([-0.01, 0, 0.01]))
    images = np.array([0.0, np.finfo(float).max / 4, 0.0])[:, None, None]
    # The narrow full-rank phase fit needs A~ -5000*max/4, safely beyond range.
    assert_code("unrepresentable_phase_components", lambda: estimate(fixture, images=images))


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_e12_preserve_numpy_error_policy_success_rejection(
    mode: Literal["ignore", "warn", "raise", "call", "print", "log"],
    capsys: Any,
) -> None:
    original = np.geterr()
    callback = np.geterrcall()

    class Sink:
        def write(self, message: str) -> None:
            pytest.fail(f"Leaked NumPy arithmetic diagnostic: {message}", pytrace=False)

    def arithmetic_callback(*args: Any) -> None:
        pytest.fail("Leaked NumPy arithmetic callback", pytrace=False)

    try:
        handler = Sink() if mode == "log" else arithmetic_callback
        np.seterrcall(handler)
        np.seterr(all=mode)
        base = acquisition()
        images = np.ldexp(base.images, 1018)
        result = estimate(base, images=images)
        assert np.isfinite(result.modulation)
        assert np.geterr() == dict.fromkeys(original, mode)
        assert np.geterrcall() is handler
        assert_code(
            "unidentifiable_illumination", lambda: estimate(base, images=np.zeros_like(images))
        )
        assert np.geterr() == dict.fromkeys(original, mode)
        assert np.geterrcall() is handler
        range_fixture = acquisition((1, 2), carrier=(0, -1))
        transfer = np.array([[1e-310, 1]], dtype=np.complex128)
        range_images = np.array(
            [
                np.array([[1.0, 1.0]]) + 0.6 * np.cos(p) * np.array([[1.0, -1.0]])
                for p in range_fixture.steps
            ]
        )
        assert_code(
            "unrepresentable_illumination",
            lambda: estimate(
                range_fixture, images=range_images, otf=calibration(range_fixture, values=transfer)
            ),
        )
        assert np.geterr() == dict.fromkeys(original, mode)
        assert np.geterrcall() is handler
        captured = capsys.readouterr()
        assert captured.out == captured.err == ""
    finally:
        np.seterr(**original)
        np.seterrcall(callback)


def test_e13_frozen_record_independent_mutable_storage_and_inputs() -> None:
    fixture = acquisition()
    images = np.empty((len(fixture.steps), 10, 14))[:, ::2, ::2]
    images[...] = fixture.images
    steps = np.empty(2 * len(fixture.steps))[::2]
    steps[...] = fixture.steps
    record = calibration(fixture)
    inputs = [images, steps, record.values, record.fy_per_um, record.fx_per_um]
    before = [array.copy() for array in inputs]
    for array in inputs:
        array.flags.writeable = False
    result = estimate(fixture, images=images, phase_steps_rad=steps, otf=record)
    assert_fit(fixture, result)
    output = result.phases_rad
    assert type(output) is np.ndarray
    assert output.dtype == np.dtype(np.float64) and output.dtype.isnative
    assert output.shape == steps.shape
    assert output.flags.owndata and output.flags.c_contiguous and output.flags.writeable
    for array, snapshot in zip(inputs, before, strict=True):
        assert not np.shares_memory(output, array)
        np.testing.assert_array_equal(array, snapshot)
    for name in (
        "phase_offset_rad",
        "modulation",
        "relative_residual",
        "phases_rad",
        "overlap_count",
        "source",
    ):
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, getattr(result, name))
    second = estimate(fixture, images=images, phase_steps_rad=steps, otf=record)
    snapshot = second.phases_rad.copy()
    output[:] = 0
    np.testing.assert_array_equal(second.phases_rad, snapshot)
    for array, snapshot in zip(inputs, before, strict=True):
        np.testing.assert_array_equal(array, snapshot)
    assert_code(
        "no_illumination_overlap",
        lambda: estimate(
            fixture, images=images, phase_steps_rad=steps, otf=record, carrier_bins_yx=(100, 0)
        ),
    )
    for array, snapshot in zip(inputs, before, strict=True):
        np.testing.assert_array_equal(array, snapshot)


def test_e14_joint_unequal_phase_observation_permutation() -> None:
    fixture = acquisition()
    order = np.array([5, 1, 3, 0, 4, 2])
    permuted = Acquisition(
        fixture.images[order],
        fixture.steps[order],
        fixture.transfer,
        fixture.carrier,
        fixture.specimen,
        fixture.brightness,
        fixture.modulation,
        fixture.theta,
    )
    first, second = estimate(fixture), estimate(permuted)
    assert_fit(fixture, first)
    assert_fit(permuted, second)
    assert abs(first.modulation - second.modulation) < 2e-11
    assert abs(circular_error(first.phase_offset_rad, second.phase_offset_rad)) < 2e-11
    assert np.max(np.abs(circular_error(second.phases_rad, first.phases_rad[order]))) < 2e-11


@pytest.mark.parametrize("count", [3, 11])
def test_e14_three_and_more_unequal_observations(count: int) -> None:
    steps = (
        np.array([0.0, 2.0, 4.3])
        if count == 3
        else np.linspace(-2.4, 3.7, count) + 0.04 * np.sin(np.arange(count))
    )
    fixture = acquisition(steps=steps)
    assert_fit(fixture, estimate(fixture))


def test_e15_actual_reconstruct_with_estimated_parameters() -> None:
    fixture = acquisition(brightness=1.7)
    result = estimate(fixture)
    assert_fit(fixture, result)
    ny, nx = fixture.transfer.shape
    wave = np.array(
        [
            [
                fixture.carrier[0] / (ny * fixture.pixel_size[0]),
                fixture.carrier[1] / (nx * fixture.pixel_size[1]),
            ]
        ]
    )
    reconstruction = public("reconstruct")(
        fixture.images[None],
        otf=calibration(fixture),
        phases_rad=result.phases_rad[None],
        wavevectors_per_um=wave,
        modulation=np.array([result.modulation]),
        brightness=np.array([fixture.brightness]),
        regularization=0.0,
        apodization=np.ones((2 * ny, 2 * nx)),
    )
    expected = continuous_specimen((ny, nx))
    # Smooth object modes lie in alias-free detector coverage; H has no zeros.
    assert np.max(np.abs(reconstruction.image - expected)) < 2e-10
    expected_spectrum = finite_dft(expected).astype(np.complex128)
    assert np.max(np.abs(reconstruction.spectrum - expected_spectrum)) < 2e-10
    assert reconstruction.pixel_size_um == tuple(d / 2 for d in fixture.pixel_size)


def test_e15_unconstrained_estimate_keeps_reconstruction_physical_domain() -> None:
    fixture = acquisition(modulation=2.4)
    result = estimate(fixture)
    ny, nx = fixture.transfer.shape
    wave = np.array(
        [
            [
                fixture.carrier[0] / (ny * fixture.pixel_size[0]),
                fixture.carrier[1] / (nx * fixture.pixel_size[1]),
            ]
        ]
    )
    assert_code(
        "invalid_reconstruction_modulation_range",
        lambda: public("reconstruct")(
            fixture.images[None],
            otf=calibration(fixture),
            phases_rad=result.phases_rad[None],
            wavevectors_per_um=wave,
            modulation=np.array([result.modulation]),
            brightness=np.array([fixture.brightness]),
            regularization=0.0,
            apodization=np.ones((2 * ny, 2 * nx)),
        ),
    )


def test_e16_existing_public_numeric_exports_remain_available() -> None:
    for name in (
        "PhaseComponents",
        "separate_phases",
        "Otf2D",
        "prepare_otf",
        "Reconstruction2D",
        "reconstruct",
        "SimreconError",
    ):
        assert public(name) is not None


def test_independent_oracle_roots_and_known_phase_coefficients() -> None:
    # A fixture self-check is passing evidence, not product-red evidence.
    from illumination_fixture import phase_coefficients, roots

    for n in (1, 2, 3, 4, 5, 6, 7, 10, 14):
        matrix = roots(n)
        assert np.max(np.abs(matrix @ matrix.conj().T / n - np.eye(n))) < 64 * n * EPS
    fixture = acquisition()
    data = (10 + 4 * np.cos(fixture.steps) + 2 * np.sin(fixture.steps))[:, None, None]
    dc, c1 = phase_coefficients(data, fixture.steps)
    precise_dc, precise_c1 = phase_coefficients(data, fixture.steps, precision=120)
    np.testing.assert_array_equal(dc, precise_dc)
    np.testing.assert_array_equal(c1, precise_c1)
    peak = float(np.max(np.abs(data)))
    assert abs(dc[0, 0] * peak - 10) < 2e-14
    assert abs(c1[0, 0] * peak - (2 - 1j)) < 2e-14


def test_independent_model_fixture_sign_normalization_and_conditions() -> None:
    for fixture in (
        acquisition(),
        acquisition(carrier=(-1, 1), brightness=3, theta=-1.2),
        acquisition(carrier=(0, 1), theta=2.7),
        acquisition(modulation=2.4),
        acquisition(steps=np.array([1e20, -1e20, 1e100, -1e100, 1e200, -1e200, 1e300, -1e300])),
    ):
        truth = stored_fit(fixture.images, fixture.steps, fixture.transfer, fixture.carrier)
        assert truth.informative
        analytic = fixture.modulation / 2 * np.exp(1j * fixture.theta)
        assert abs(truth.gain - analytic) < 2e-13
        assert truth.residual < 2e-13
    altered = acquisition(off_model=True)
    truth = stored_fit(altered.images, altered.steps, altered.transfer, altered.carrier)
    assert truth.informative
    assert truth.residual > 0.1


def test_independent_dtype_scale_and_small_residual_fixture_conditions() -> None:
    base = acquisition()
    for dtype in REAL_DTYPES:
        images = (base.images * 32).astype(dtype)
        truth = stored_fit(images, base.steps, base.transfer, base.carrier)
        assert truth.informative
        steps = np.array([0, 1, 2, 3, 4, 5], dtype=dtype).astype(np.float64)
        fixture = acquisition(steps=steps)
        truth = stored_fit(fixture.images, steps, fixture.transfer, fixture.carrier)
        assert truth.informative
    for exponent in (-1000, -900, -500, 0, 500, 900, 1018):
        truth = stored_fit(np.ldexp(base.images, exponent), base.steps, base.transfer, base.carrier)
        assert truth.informative
        assert abs(truth.gain - base.modulation / 2 * np.exp(1j * base.theta)) < 2e-13
    altered = acquisition(off_model=True)
    images = base.images + 1e-6 * (altered.images - base.images)
    truth = stored_fit(images, base.steps, base.transfer, base.carrier)
    assert truth.informative
    assert 1e-9 < truth.residual < 1e-5
