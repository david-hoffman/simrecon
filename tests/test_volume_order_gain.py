"""Blind public-contract tests for one known-carrier complex volume-order gain."""

from __future__ import annotations

import warnings
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
import pytest
import scipy.linalg

import simrecon
from volume_order_gain_fixture import (
    EPS,
    QUANTUM,
    Oracle,
    alias_free_case,
    arbitrary_case,
    bins,
    constant_case,
    dec,
    exposures,
    fields,
    index,
    observe,
    phase_matrix,
    reconstruction_observer,
    separated_exact,
    steps_default,
    synthesize,
    z,
)


def public(name: str) -> Any:
    value = getattr(simrecon, name, None)
    assert value is not None, f"setup observation: missing public export {name}"
    return value


def calibration(data: dict[str, Any]) -> Any:
    return public("VolumeOrderOtf")(**data)


def fit(
    images: Any, steps: Any, data: dict[str, Any] | Any, carrier: Any = (0, 0), order: Any = 1
) -> Any:
    otf = calibration(data) if isinstance(data, dict) else data
    return public("estimate_volume_order_gain")(
        images, order_otf=otf, phase_steps_rad=steps, carrier_bins_yx=carrier, order=order
    )


def error(
    code: str, images: Any, steps: Any, data: Any, carrier: Any = (0, 0), order: Any = 1
) -> None:
    with warnings.catch_warnings(record=True) as emitted:
        policy, filters = np.geterr().copy(), list(warnings.filters)
        with pytest.raises(public("SimreconError")) as caught:
            fit(images, steps, data, carrier, order)
        assert np.geterr() == policy
        assert warnings.filters == filters
    assert not any(issubclass(w.category, RuntimeWarning) for w in emitted)
    assert caught.value.code == code
    assert isinstance(caught.value.message, str)
    assert isinstance(caught.value, ValueError)


def agreement(actual: Any, expected: Oracle, informative: bool = True) -> None:
    with localcontext() as ctx:
        ctx.prec = 80
        if informative:
            assert expected.informative(), "fixture must certify every informative inequality"
        budget = expected.delta * max(Decimal(1), expected.gain.modulus()) + 8 * QUANTUM
        assert (z(actual.gain) - expected.gain).modulus() <= budget
        assert abs(dec(actual.relative_residual) - expected.residual) <= expected.delta
        assert abs(dec(actual.coherence) - expected.coherence) <= expected.delta
        assert actual.overlap_count == expected.count
        assert actual.status == "fitted"


def assert_metadata(actual: Any, order: int, carrier: tuple[int, int]) -> None:
    assert type(actual.order) is int
    assert actual.order == order
    assert type(actual.carrier_bins_yx) is tuple
    assert actual.carrier_bins_yx == carrier
    assert all(type(value) is int for value in actual.carrier_bins_yx)


def test_exports() -> None:
    assert callable(public("estimate_volume_order_gain"))
    assert callable(public("VolumeOrderGainEstimate"))


@pytest.mark.parametrize(
    "kind",
    [
        "missing_otf",
        "missing_steps",
        "missing_carrier",
        "missing_order",
        "positional_keywords",
        "unexpected_keyword",
    ],
)
def test_binding(kind: str) -> None:
    images, steps, data = constant_case()
    operation = public("estimate_volume_order_gain")
    arguments = dict(
        order_otf=calibration(data), phase_steps_rad=steps, carrier_bins_yx=(0, 0), order=1
    )
    if kind.startswith("missing_"):
        key = {
            "otf": "order_otf",
            "steps": "phase_steps_rad",
            "carrier": "carrier_bins_yx",
            "order": "order",
        }[kind.removeprefix("missing_")]
        del arguments[key]
    elif kind == "unexpected_keyword":
        arguments["unknown"] = 1
    with pytest.raises(TypeError):
        if kind == "positional_keywords":
            operation(images, calibration(data), steps, (0, 0), 1)
        else:
            operation(images, **arguments)


def test_record() -> None:
    images, steps, data = constant_case()
    result = fit(images, steps, data, [np.int32(0), np.uint64(0)], np.int16(1))
    expected_types = {
        "gain": complex,
        "relative_residual": float,
        "coherence": float,
        "overlap_count": int,
        "status": str,
        "order": int,
        "carrier_bins_yx": tuple,
        "source": str,
    }
    assert isinstance(result, public("VolumeOrderGainEstimate"))
    for name, kind in expected_types.items():
        assert type(getattr(result, name)) is kind
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, getattr(result, name))
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, name)
    assert result.order == 1
    assert result.carrier_bins_yx == (0, 0)
    assert all(type(v) is int for v in result.carrier_bins_yx)
    assert result.source == data["source"]
    before = (result.gain, result.relative_residual, result.coherence, result.source)
    images.fill(0)
    data["values"].fill(0)
    assert (result.gain, result.relative_residual, result.coherence, result.source) == before


def test_record_direct() -> None:
    result = public("VolumeOrderGainEstimate")(
        gain=complex("nan"),
        relative_residual=-1.0,
        coherence=7.0,
        overlap_count=-5,
        status="caller",
        order=99,
        carrier_bins_yx=(999, -999),
        source="",
    )
    assert result.order == 99
    assert result.status == "caller"


class ArraySubclass(np.ndarray):
    """Representation rejected at public plain-array boundaries."""


class ListSubclass(list):
    """Sequence rejected where an exact built-in container is required."""


class TupleSubclass(tuple):
    """Tuple rejected where an exact built-in container is required."""


@pytest.mark.parametrize(
    "kind,code",
    [
        ("image_list", "invalid_volume_phase_images"),
        ("image_subclass", "invalid_volume_phase_images"),
        ("image_bool", "invalid_volume_phase_dtype"),
        ("image_complex", "invalid_volume_phase_dtype"),
        ("image_object", "invalid_volume_phase_dtype"),
        ("image_rank", "invalid_volume_phase_shape"),
        ("image_short", "invalid_volume_phase_shape"),
        ("image_empty_axis", "invalid_volume_phase_shape"),
        ("image_nan", "nonfinite_volume_phase_images"),
        ("image_inf", "nonfinite_volume_phase_images"),
        ("steps_list", "invalid_volume_phase_angles"),
        ("steps_subclass", "invalid_volume_phase_angles"),
        ("steps_complex", "invalid_volume_phase_angles_dtype"),
        ("steps_bool", "invalid_volume_phase_angles_dtype"),
        ("steps_shape", "invalid_volume_phase_angles_shape"),
        ("steps_count", "invalid_volume_phase_angles_shape"),
        ("steps_nan", "nonfinite_volume_phase_angles"),
        ("steps_inf", "nonfinite_volume_phase_angles"),
        ("steps_rank", "rank_deficient_volume_phases"),
    ],
)
def test_inherited_invalid(kind: str, code: str) -> None:
    images, steps, data = constant_case()
    if kind == "image_list":
        images = images.tolist()
    elif kind == "image_subclass":
        images = images.view(ArraySubclass)
    elif kind.startswith("image_") and kind[6:] in {"bool", "complex", "object"}:
        images = images.astype({"bool": bool, "complex": complex, "object": object}[kind[6:]])
    elif kind == "image_rank":
        images = images[:, 0]
    elif kind == "image_short":
        images, steps = images[:4], steps[:4]
    elif kind == "image_empty_axis":
        images = images[:, :, :, :0]
    elif kind in {"image_nan", "image_inf"}:
        images.flat[0] = np.nan if kind.endswith("nan") else np.inf
    elif kind == "steps_list":
        steps = steps.tolist()
    elif kind == "steps_subclass":
        steps = steps.view(ArraySubclass)
    elif kind == "steps_complex":
        steps = steps.astype(complex)
    elif kind == "steps_bool":
        steps = steps.astype(bool)
    elif kind == "steps_shape":
        steps = steps[:, None]
    elif kind == "steps_count":
        steps = steps[:-1]
    elif kind in {"steps_nan", "steps_inf"}:
        steps[0] = np.nan if kind.endswith("nan") else np.inf
    elif kind == "steps_rank":
        steps.fill(0)
    error(code, images, steps, data)


@pytest.mark.parametrize("subject", ["images", "steps"])
def test_wide_conversion(subject: str) -> None:
    images, steps, data = constant_case()
    if np.finfo(np.longdouble).max > np.finfo(np.float64).max:
        huge = np.longdouble(np.finfo(np.float64).max) * 2
        if subject == "images":
            images = images.astype(np.longdouble)
            images.flat[0] = huge
        else:
            steps = steps.astype(np.longdouble)
            steps[0] = huge
        error(
            "nonfinite_volume_phase_images"
            if subject == "images"
            else "nonfinite_volume_phase_angles",
            images,
            steps,
            data,
        )
    else:
        # No wider finite-to-nonfinite class exists on this platform. Do not skip.
        images = images.astype(np.longdouble)
        steps = steps.astype(np.longdouble)
        agreement(fit(images, steps, data), observe(images, steps, data["values"], (0, 0), 1))


@pytest.mark.parametrize(
    "dtype",
    [
        "i1",
        "i2",
        "i4",
        "i8",
        "u1",
        "u2",
        "u4",
        "u8",
        "f2",
        "f4",
        "f8",
        ">f8",
        ">i4",
        ">u8",
        np.longdouble,
    ],
)
def test_representations(dtype: Any) -> None:
    images, steps, data = arbitrary_case((1, 2, 3))
    if np.dtype(dtype).kind in "iu":
        # Signed inputs remain signed; unsigned inputs use a separate positive conversion.
        if np.dtype(dtype).kind == "u":
            images += 10
        images *= 9
    images = images.astype(dtype)
    # Integer phase arrays retain full rank for the represented values 0..6.
    steps = np.arange(7).astype(dtype)
    images = np.asfortranarray(images)
    images.flags.writeable = False
    steps = steps[::-1]
    steps.flags.writeable = False
    expected = observe(images, steps, data["values"], (0, 0), 1)
    agreement(fit(images, steps, data), expected, informative=False)


@pytest.mark.parametrize("order", [1, 2, np.int8(1), np.uint64(2)])
def test_order_valid(order: Any) -> None:
    images, steps, data = arbitrary_case()
    actual = fit(images, steps, data, order=order)
    assert_metadata(actual, int(order), (0, 0))
    agreement(
        actual,
        observe(images, steps, data["values"], (0, 0), int(order)),
    )


@pytest.mark.parametrize(
    "order", [True, np.bool_(False), 1.0, np.float64(2), "1", None, np.array(1), 0, -1, 3, 2**200]
)
def test_order_invalid(order: Any) -> None:
    images, steps, data = constant_case()
    error("invalid_volume_order_gain_order", images, steps, data, order=order)


@pytest.mark.parametrize(
    "carrier",
    [
        (0, 0),
        [np.int8(0), np.uint64(0)],
        np.array([0, 0], dtype=">i8"),
        np.array([0, 0], dtype=np.uint64),
    ],
)
def test_carrier_valid(carrier: Any) -> None:
    images, steps, data = constant_case()
    result = fit(images, steps, data, carrier)
    assert_metadata(result, 1, (int(carrier[0]), int(carrier[1])))
    agreement(result, observe(images, steps, data["values"], (0, 0), 1))


@pytest.mark.parametrize(
    "carrier",
    [
        (2**200, 0),
        [0, -(2**300)],
        np.array([np.iinfo(np.uint64).max, 0], dtype=np.uint64),
        (0, 1),
        (-1, 0),
    ],
)
def test_carrier_empty(carrier: Any) -> None:
    images, steps, data = constant_case()
    error("no_volume_order_gain_overlap", images, steps, data, carrier)


@pytest.mark.parametrize(
    "carrier",
    [
        None,
        "00",
        {0, 1},
        ListSubclass([0, 0]),
        TupleSubclass((0, 0)),
        (0,),
        (0, 0, 0),
        (0.0, 0),
        (True, 0),
        (np.bool_(False), 0),
        np.array([0, 0], dtype=float),
        np.array([False, False]),
        np.array([[0, 0]]),
        np.array([0, 0]).view(ArraySubclass),
    ],
)
def test_carrier_invalid(carrier: Any) -> None:
    images, steps, data = constant_case()
    error("invalid_volume_order_gain_carrier", images, steps, data, carrier)


class FailingInteger(int):
    """Accepted integer scalar whose extraction exercises conversion failure."""

    failure: BaseException = TypeError("controlled integer conversion")

    def __int__(self) -> int:
        """Raise the selected extraction failure."""
        raise self.failure


@pytest.mark.parametrize("kind", [TypeError, ValueError, OverflowError, RuntimeError, MemoryError])
def test_carrier_extraction(kind: type[Exception]) -> None:
    images, steps, data = constant_case()
    item = FailingInteger(0)
    item.failure = kind("controlled integer conversion")
    if kind in {TypeError, ValueError, OverflowError}:
        error("invalid_volume_order_gain_carrier", images, steps, data, (item, 0))
    else:
        with pytest.raises(kind) as caught:
            fit(images, steps, data, (item, 0))
        assert caught.value is item.failure


OTF_BAD = [
    "record",
    "values_list",
    "values_subclass",
    "values_real",
    "values_c64",
    "values_shape",
    "values_nan_unused",
    "values_inf_imag",
    "frequency_list",
    "frequency_subclass",
    "frequency_f32",
    "frequency_shape",
    "frequency_nan",
    "frequency_reverse",
    "frequency_dc",
    "frequency_inaccurate",
    "spacing_array",
    "spacing_subclass",
    "spacing_short",
    "spacing_bool",
    "spacing_complex",
    "spacing_zero",
    "spacing_inf",
    "origin_array",
    "origin_subclass",
    "origin_short",
    "origin_float",
    "origin_bool",
    "origin_negative",
    "origin_outside",
    "source_blank",
    "source_nonstring",
]


@pytest.mark.parametrize(
    "kind,axis",
    [
        (kind, axis)
        for kind in OTF_BAD
        for axis in (
            ["fz_per_um", "fy_per_um", "fx_per_um"] if kind.startswith("frequency_") else [""]
        )
    ],
)
def test_otf_invalid(kind: str, axis: str) -> None:
    images, steps, data = arbitrary_case()
    if kind == "record":
        error("invalid_volume_order_gain_otf", images, steps, object())
        return
    if kind == "values_list":
        data["values"] = data["values"].tolist()
    elif kind == "values_subclass":
        data["values"] = data["values"].view(ArraySubclass)
    elif kind == "values_real":
        data["values"] = data["values"].real.copy()
    elif kind == "values_c64":
        data["values"] = data["values"].astype(np.complex64)
    elif kind == "values_shape":
        data["values"] = data["values"][:, :, :, :-1]
    elif kind == "values_nan_unused":
        data["values"][2, 0, 0, 0] = np.nan
    elif kind == "values_inf_imag":
        data["values"][2, 0, 0, 0] = complex(0, np.inf)
    elif kind.startswith("frequency_"):
        name = axis
        if kind == "frequency_list":
            data[name] = data[name].tolist()
        elif kind == "frequency_subclass":
            data[name] = data[name].view(ArraySubclass)
        elif kind == "frequency_f32":
            data[name] = data[name].astype(np.float32)
        elif kind == "frequency_shape":
            data[name] = data[name][:, None]
        elif kind == "frequency_nan":
            data[name][0] = np.nan
        elif kind == "frequency_reverse":
            data[name] = data[name][::-1]
        elif kind == "frequency_dc":
            data[name][len(data[name]) // 2] = 1e-20
        else:
            data[name][0] += 0.01
    elif kind.startswith("spacing_"):
        data["voxel_size_um"] = {
            "spacing_array": np.array([0.7, 0.9, 1.1]),
            "spacing_subclass": TupleSubclass((0.7, 0.9, 1.1)),
            "spacing_short": (0.7, 0.9),
            "spacing_bool": (True, 0.9, 1.1),
            "spacing_complex": (0.7 + 0j, 0.9, 1.1),
            "spacing_zero": (0, 0.9, 1.1),
            "spacing_inf": (np.inf, 0.9, 1.1),
        }[kind]
    elif kind.startswith("origin_"):
        data["origin_zyx"] = {
            "origin_array": np.array([0, 0, 0]),
            "origin_subclass": ListSubclass([0, 0, 0]),
            "origin_short": (0, 0),
            "origin_float": (0.0, 0, 0),
            "origin_bool": (True, 0, 0),
            "origin_negative": (-1, 0, 0),
            "origin_outside": (2, 0, 0),
        }[kind]
    elif kind == "source_blank":
        data["source"] = " \n\t"
    else:
        data["source"] = 42
    error("invalid_volume_order_gain_otf", images, steps, data)


def test_frequency_tolerance() -> None:
    images, steps, data = arbitrary_case()
    baseline = data["fx_per_um"][0]
    data["fx_per_um"][0] = np.nextafter(baseline, np.inf)
    agreement(fit(images, steps, data), observe(images, steps, data["values"], (0, 0), 1))
    data["fx_per_um"][0] = baseline + 64 * np.spacing(abs(baseline))
    error("invalid_volume_order_gain_otf", images, steps, data)


def test_otf_valid() -> None:
    images, steps, data = arbitrary_case()
    data["values"] = data["values"].astype(">c16")
    data["values"][0] *= 0.7 + 0.6j
    data["values"][2].fill(0)
    data["values"] = np.asfortranarray(data["values"])
    for name in ["fz_per_um", "fy_per_um", "fx_per_um"]:
        original = data[name]
        backing = np.zeros(2 * len(original), dtype=">f8")
        backing[::2] = original
        data[name] = backing[::2]
        data[name].flags.writeable = False
    data["values"].flags.writeable = False
    data["voxel_size_um"] = [np.float64(0.7), np.float32(0.9), np.float64(1.1)]
    # Regenerate the y grid for the represented float32 spacing.
    data["fy_per_um"] = np.array([k / (3 * float(np.float32(0.9))) for k in bins(3)])
    data["origin_zyx"] = [np.int8(0), np.uint64(1), np.int64(2)]
    agreement(fit(images, steps, data), observe(images, steps, data["values"], (0, 0), 1))


@pytest.mark.parametrize(
    "shape,carrier,order",
    [
        ((2, 3, 4), (0, 0), 1),
        ((3, 4, 5), (-1, 1), 1),
        ((1, 5, 6), (1, -1), 2),
        ((2, 1, 5), (0, -1), 2),
        ((3, 5, 1), (-1, 0), 1),
        ((1, 1, 1), (0, 0), 1),
    ],
)
def test_geometry(shape: tuple[int, int, int], carrier: tuple[int, int], order: int) -> None:
    images, steps, data = arbitrary_case(shape)
    expected = observe(images, steps, data["values"], carrier, order)
    actual = fit(images, steps, data, carrier, order)
    assert_metadata(actual, order, carrier)
    agreement(actual, expected, informative=False)
    assert actual.overlap_count == shape[0] * max(shape[1] - abs(order * carrier[0]), 0) * max(
        shape[2] - abs(order * carrier[1]), 0
    )


@pytest.mark.parametrize("order,huge", [(1, False), (2, False), (1, True), (2, True)])
def test_stored_oracle(order: int, huge: bool) -> None:
    steps = steps_default()
    if huge:
        steps = np.array([0.0, 0.8, 1.9, 2.8, 3.7, 4.8, 1e308])
    images, steps, data = arbitrary_case(steps=steps)
    expected = observe(images, steps, data["values"], (0, 0), order)
    agreement(fit(images, steps, data, order=order), expected)
    # An independent tighter margin distinguishes factor, sign and magnitude-only fits.
    actual = fit(images, steps, data, order=order)
    assert abs(actual.gain - expected.gain.native()) <= 2e-11
    assert abs(actual.coherence - float(expected.coherence)) <= 2e-11


def test_axes() -> None:
    images, steps, data = arbitrary_case((2, 3, 4))
    transposed = images.transpose(0, 3, 1, 2)
    moved = fields((4, 2, 3), data["values"].transpose(0, 3, 1, 2))
    agreement(fit(transposed, steps, moved), observe(transposed, steps, moved["values"], (0, 0), 1))
    first, second = fit(images, steps, data), fit(transposed, steps, moved)
    assert abs(first.gain - second.gain) < 1e-11


def test_origin_metadata() -> None:
    images, steps, data = arbitrary_case()
    first = fit(images, steps, data)
    data["origin_zyx"] = (0, 1, 0)
    second = fit(images, steps, data)
    assert abs(first.gain - second.gain) < 1e-12


@pytest.mark.parametrize("kind", ["predictor", "both_zero", "response", "correlation"])
def test_information_outcomes(kind: str) -> None:
    images, steps, data = constant_case(shape=(1, 1, 2))
    if kind in {"predictor", "both_zero"}:
        if kind == "predictor":
            data["values"][1].fill(0)
        else:
            images.fill(0)
        error("unidentifiable_volume_order_gain", images, steps, data)
        return
    if kind == "response":
        data["values"][0].fill(0)
        result = fit(images, steps, data)
        assert (result.gain, result.relative_residual, result.coherence, result.status) == (
            0j,
            0.0,
            0.0,
            "zero_response",
        )
    else:
        # Disjoint predictor/response support makes computed correlation exactly zero.
        dc = np.ones((1, 1, 2))
        side = np.array([[[1, -1]]], dtype=complex)
        images = exposures(dc, side, np.zeros_like(side), steps)
        data["values"].fill(0)
        data["values"][1, 0, 0, 1] = 1  # predictor at DC
        data["values"][0, 0, 0, 0] = 1  # response at even Nyquist
        result = fit(images, steps, data)
        assert (result.gain, result.relative_residual, result.coherence, result.status) == (
            0j,
            1.0,
            0.0,
            "zero_correlation",
        )
    assert result.overlap_count == 2


def test_tiny_correlation() -> None:
    steps = steps_default()
    dc = np.ones((1, 1, 2))
    side = np.array([[[2.0 + 0j, 0j]]])
    images = exposures(dc, side, np.zeros_like(side), steps)
    data = fields((1, 1, 2), np.ones((3, 1, 1, 2), dtype=complex))
    data["values"][1, 0, 0, 0] = 0
    data["values"][0, 0, 0, 1] = 1e-100
    expected = observe(images, steps, data["values"], (0, 0), 1)
    assert Decimal(0) < expected.coherence < Decimal("1e-90")
    result = fit(images, steps, data)
    assert result.status == "fitted"
    assert result.coherence > 0
    agreement(result, expected, informative=False)


def test_direct_residual() -> None:
    steps = steps_default()
    dc = np.array([[[1.0, 0.0]]])
    side = np.array([[[0.4 + 0.3j, 2e-8 - 1e-8j]]])
    images = exposures(dc, side, np.zeros_like(side), steps)
    data = fields((1, 1, 2), np.ones((3, 1, 1, 2), dtype=complex))
    expected = observe(images, steps, data["values"], (0, 0), 1)
    assert Decimal("1e-8") < expected.residual < Decimal("1e-7")
    result = fit(images, steps, data)
    agreement(result, expected)
    assert abs(result.relative_residual - float(expected.residual)) < 2e-13


@pytest.mark.parametrize("scale,transfer", [(1e150, 1e250), (1e-150, 1e-250), (1e300, 1.0)])
def test_extremes(scale: float, transfer: float) -> None:
    images, steps, data = constant_case(shape=(2, 3, 4))
    images *= scale
    data["values"] *= transfer
    expected = observe(images, steps, data["values"], (0, 0), 1)
    agreement(fit(images, steps, data), expected)


def test_transform_scaling(monkeypatch: pytest.MonkeyPatch) -> None:
    images, steps, data = constant_case(dc=1e307, c1=2e306 + 3e306j, shape=(2, 3, 4))
    original = np.fft.fftn
    seen = []

    def guarded(a: Any, s: Any = None, axes: Any = None, norm: Any = None, out: Any = None) -> Any:
        array = np.asarray(a)
        selected = (
            tuple(range(array.ndim)) if axes is None else tuple(ax % array.ndim for ax in axes)
        )
        assert len(selected) == 3
        assert sorted(array.shape[ax] for ax in selected) == [2, 3, 4]
        if s is not None:
            assert all(n in (-1, array.shape[ax]) for n, ax in zip(s, selected, strict=True))
        assert np.max(np.abs(array.real)) <= 1
        assert np.max(np.abs(array.imag)) <= 1
        seen.append(True)
        return original(a, s=s, axes=axes, norm=norm, out=out)

    monkeypatch.setattr(np.fft, "fftn", guarded)
    result = fit(images, steps, data)
    assert seen
    agreement(result, observe(images, steps, data["values"], (0, 0), 1))


def test_extreme_ratio() -> None:
    # Raw ||y||/||x|| exceeds F, but correlation reduces each restored component.
    steps = steps_default()
    dc = np.ones((1, 1, 2))
    side = np.array([[[2.0 + 0j, 0j]]])
    images = exposures(dc, side, np.zeros_like(side), steps)
    values = np.ones((3, 1, 1, 2), dtype=complex)
    values[1] *= 1e-310
    values[1, 0, 0, 0] = 0
    values[0, 0, 0, 1] = 1e-8
    data = fields((1, 1, 2), values)
    expected = observe(images, steps, values, (0, 0), 1)
    assert expected.ny / expected.nx > dec(np.finfo(float).max)
    assert expected.gain.modulus() < dec(np.finfo(float).max) / 100
    result = fit(images, steps, data)
    assert result.status == "fitted"
    assert abs(result.gain.real / float(expected.gain.real) - 1) < 0.005
    assert np.isfinite(result.gain.real) and np.isfinite(result.gain.imag)


def test_extreme_components() -> None:
    images, steps, data = constant_case(c1=0.75 + 0.75j)
    data["values"][1] = 1 / np.finfo(float).max
    expected = observe(images, steps, data["values"], (0, 0), 1)
    assert expected.gain.modulus() > dec(np.finfo(float).max)
    assert max(abs(expected.gain.real), abs(expected.gain.imag)) < dec(np.finfo(float).max)
    result = fit(images, steps, data)
    assert result.status == "fitted"
    assert abs(result.gain.real / float(expected.gain.real) - 1) < 1e-12
    assert abs(result.gain.imag / float(expected.gain.imag) - 1) < 1e-12


def test_extreme_underflow() -> None:
    images, steps, data = constant_case()
    data["values"][0] = np.nextafter(0.0, 1.0)
    data["values"][1] = np.finfo(float).max
    result = fit(images, steps, data)
    assert result.gain == 0j
    assert result.status == "fitted"
    assert np.isfinite(result.relative_residual) and np.isfinite(result.coherence)


def test_extreme_range() -> None:
    images, steps, data = constant_case(c1=0.75 + 0.75j)
    data["values"][1] = np.nextafter(0.0, 1.0)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        error("unrepresentable_volume_order_gain", images, steps, data)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)


def test_snapshots(monkeypatch: pytest.MonkeyPatch, record_property: Any) -> None:
    images, steps, data = arbitrary_case()
    expected = observe(images, steps, data["values"], (0, 0), 1)
    data["voxel_size_um"] = list(data["voxel_size_um"])
    data["origin_zyx"] = list(data["origin_zyx"])
    original = np.cos
    seen = []

    def mutate(a: Any, *args: Any, **kwargs: Any) -> Any:
        if not seen:
            seen.append(True)
            images.fill(0)
            steps.fill(0)
            data["values"].fill(np.nan)
            for name in ["fz_per_um", "fy_per_um", "fx_per_um"]:
                data[name].fill(np.nan)
            data["voxel_size_um"][0] = -1
            data["origin_zyx"][0] = -1
        return original(a, *args, **kwargs)

    monkeypatch.setattr(np, "cos", mutate)
    result = fit(images, steps, data)
    # A retained np.cos alias computes the same represented matrix without
    # reaching this optional mutation seam. That route still owes the ordinary
    # fit; snapshot-at-mutation coverage is unexercised and needs D assessment.
    record_property("snapshot_mutation_seam", "reached" if seen else "unexercised")
    agreement(result, expected)


@pytest.mark.parametrize("failure", [False, True])
def test_preservation(failure: bool) -> None:
    images, steps, data = arbitrary_case()
    backing = np.zeros((*images.shape[:-1], images.shape[-1] * 2))
    backing[..., ::2] = images
    images = backing[..., ::2]
    images.flags.writeable = False
    steps.flags.writeable = False
    data["values"].flags.writeable = False
    arrays = [
        images,
        steps,
        data["values"],
        data["fz_per_um"],
        data["fy_per_um"],
        data["fx_per_um"],
    ]
    before = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    metadata = (data["source"], data["origin_zyx"], data["voxel_size_um"])
    if failure:
        error("no_volume_order_gain_overlap", images, steps, data, (10**100, 0))
    else:
        fit(images, steps, data)
    for array, (copy, strides, writeable) in zip(arrays, before, strict=True):
        assert np.array_equal(array, copy)
        assert array.strides == strides
        assert array.flags.writeable == writeable
    assert (data["source"], data["origin_zyx"], data["voxel_size_um"]) == metadata


def test_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    images, steps, data = constant_case()
    original = np.fft.fftn

    def warn(a: Any, *args: Any, **kwargs: Any) -> Any:
        warnings.warn("controlled unrelated category", UserWarning, stacklevel=2)
        return original(a, *args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn)
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        policy, filters = np.geterr().copy(), list(warnings.filters)
        fit(images, steps, data)
        assert np.geterr() == policy
        assert warnings.filters == filters
    assert any(w.category is UserWarning for w in caught)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)


@pytest.mark.parametrize("kind", ["floating", "overflow", "warning", "nan", "inf"])
def test_fft_failure(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    images, steps, data = constant_case()
    original = np.fft.fftn

    def fail(a: Any, *args: Any, **kwargs: Any) -> Any:
        if kind == "floating":
            raise FloatingPointError("controlled FFT floating")
        if kind == "overflow":
            raise OverflowError("controlled FFT overflow")
        if kind == "warning":
            warnings.warn("controlled arithmetic FFT warning", RuntimeWarning, stacklevel=2)
            return original(a, *args, **kwargs)
        result = original(a, *args, **kwargs)
        result.flat[0] = np.nan if kind == "nan" else np.inf
        return result

    monkeypatch.setattr(np.fft, "fftn", fail)
    with np.errstate(all="ignore"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("ignore", RuntimeWarning)
        policy, filters = np.geterr().copy(), list(warnings.filters)
        error("volume_order_gain_transform_failure", images, steps, data)
        assert np.geterr() == policy
        assert warnings.filters == filters
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)


@pytest.mark.parametrize("kind", [RuntimeError, TypeError, ValueError, MemoryError])
def test_fft_propagation(monkeypatch: pytest.MonkeyPatch, kind: type[Exception]) -> None:
    images, steps, data = constant_case()
    sentinel = kind("controlled unrelated FFT failure")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    monkeypatch.setattr(np.fft, "fftn", fail)
    with pytest.raises(kind) as caught:
        fit(images, steps, data)
    assert caught.value is sentinel


class FailingFloat(float):
    """Permitted spacing scalar whose float conversion raises a controlled error."""

    failure: BaseException = TypeError("controlled float conversion")

    def __float__(self) -> float:
        """Raise the selected conversion failure."""
        raise self.failure


@pytest.mark.parametrize("kind", [TypeError, ValueError, OverflowError, RuntimeError, MemoryError])
def test_conversion(kind: type[Exception]) -> None:
    images, steps, data = constant_case()
    item = FailingFloat(0.7)
    item.failure = kind("controlled float conversion")
    data["voxel_size_um"] = (item, 0.9, 1.1)
    if kind in {TypeError, ValueError, OverflowError}:
        error("invalid_volume_order_gain_otf", images, steps, data)
    else:
        with pytest.raises(kind) as caught:
            fit(images, steps, data)
        assert caught.value is item.failure


@pytest.mark.parametrize("kind", ["rank", "range"])
def test_phase_failure(kind: str) -> None:
    images, steps, data = constant_case()
    if kind == "rank":
        steps.fill(0)
        error("rank_deficient_volume_phases", images, steps, data)
    else:
        # A full rank but clustered phase basis can amplify finite data beyond F.
        steps = np.array([0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006])
        images = np.array([1, -1, 1, -1, 1, -1, 1], dtype=float).reshape(7, 1, 1, 1)
        images *= np.finfo(float).max / 4
        error("unrepresentable_volume_phase_components", images, steps, data)


@pytest.mark.parametrize("kind", ["linalg", "nonfinite", "runtime", "type", "value", "memory"])
def test_phase_dependency(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    images, steps, data = constant_case()
    expected = observe(images, steps, data["values"], (0, 0), 1)
    classes = {
        "linalg": np.linalg.LinAlgError,
        "runtime": RuntimeError,
        "type": TypeError,
        "value": ValueError,
        "memory": MemoryError,
    }
    sentinel = classes.get(kind, RuntimeError)("controlled public phase dependency")
    hits = []

    def replacement(original: Any) -> Any:
        def controlled(*args: Any, **kwargs: Any) -> Any:
            hits.append(True)
            if kind != "nonfinite":
                raise sentinel
            value = original(*args, **kwargs)
            if isinstance(value, tuple):
                return tuple(
                    np.full_like(a, np.nan) if isinstance(a, np.ndarray) else a for a in value
                )
            return np.full_like(value, np.nan)

        return controlled

    # Public SVD/LS alternatives are injected together, with no required call count.
    for module in [np.linalg, scipy.linalg]:
        for name in ["svd", "svdvals", "lstsq", "pinv"]:
            monkeypatch.setattr(module, name, replacement(getattr(module, name)))
    try:
        result = fit(images, steps, data)
    except public("SimreconError") as caught:
        assert hits
        assert kind in {"linalg", "nonfinite"}
        assert caught.code == "volume_phase_solver_failure"
    except (RuntimeError, TypeError, ValueError, MemoryError) as caught:
        assert hits
        assert kind not in {"linalg", "nonfinite"}
        assert caught is sentinel
    else:
        # A different valid SVD organization may avoid these non-normative seams.
        # It must not swallow an actually injected error or return bad factors.
        assert not hits
        agreement(result, expected)


def test_permutation() -> None:
    images, steps, data = arbitrary_case()
    permutation = [6, 2, 4, 1, 5, 0, 3]
    first = fit(images, steps, data)
    second = fit(images[permutation], steps[permutation], data)
    assert abs(first.gain - second.gain) < 1e-11
    agreement(second, observe(images[permutation], steps[permutation], data["values"], (0, 0), 1))


@pytest.mark.parametrize("kind", ["five", "repeated"])
def test_phase_valid(kind: str) -> None:
    steps = np.arange(5) * (2 * np.pi / 5)
    if kind == "repeated":
        steps = np.concatenate((steps, steps[:2], steps[:1]))
    images, steps, data = arbitrary_case((1, 2, 3), steps)
    agreement(fit(images, steps, data, order=2), observe(images, steps, data["values"], (0, 0), 2))


def test_full_rank_condition_above_ten() -> None:
    steps = np.arange(7) * 0.4
    images = exposures(
        np.ones((1, 1, 1)), np.full((1, 1, 1), 0.3 + 0.2j), np.zeros((1, 1, 1)), steps
    )
    data = fields((1, 1, 1), np.ones((3, 1, 1, 1), dtype=complex))
    singular = np.linalg.svd(phase_matrix(steps), compute_uv=False)
    threshold = 2**-52 * max(len(steps), 5) * singular[0]
    assert np.count_nonzero(singular > threshold) == 5
    expected = observe(images, steps, data["values"], (0, 0), 1)
    # For five columns, trace-product upper <= 5*cond_2(H), so upper/5
    # independently certifies that this case lies outside cond<=10.
    assert expected.condition_bound / 5 > 10
    assert not expected.informative()
    result = fit(images, steps, data)
    assert_metadata(result, 1, (0, 0))
    assert result.status == "fitted"
    assert result.overlap_count == 1
    with localcontext() as ctx:
        ctx.prec = 80
        # Case-specific margins, not the contract's uniform informative budget.
        # A 1e-8 coordinate allowance gives a scalar ratio error below 1.4e-8;
        # 1e-7 leaves ample room for alternate stable numerical organizations.
        assert (z(result.gain) - expected.gain).modulus() <= Decimal("1e-7")
        # One nonzero geometric sample has coherence one and residual zero
        # independently of the fitted phase-coordinate errors.
        assert abs(dec(result.coherence) - expected.coherence) <= Decimal("1e-12")
        assert abs(dec(result.relative_residual) - expected.residual) <= Decimal("1e-12")


@pytest.mark.parametrize("spacing", [np.nextafter(0.0, 1.0), np.finfo(float).max])
def test_singleton_metadata(spacing: float) -> None:
    images, steps, data = constant_case()
    data["voxel_size_um"] = (spacing, spacing, spacing)
    result = fit(images, steps, data, np.zeros(4, dtype=np.int64)[::2])
    agreement(result, observe(images, steps, data["values"], (0, 0), 1))


def test_oracle_selfcheck() -> None:
    images, steps, data = constant_case(dc=2, c1=0.4 - 0.3j)
    expected = observe(images, steps, data["values"], (0, 0), 1)
    assert abs(expected.gain.native() - (0.2 - 0.15j)) < 1e-15
    assert expected.residual < Decimal("1e-70")
    assert abs(expected.coherence - 1) < Decimal("1e-70")
    assert expected.informative()
    with localcontext() as ctx:
        ctx.prec = 80
        dc, c1, c2, _ = separated_exact(images, steps)
    actual = public("separate_volume_phases")(images, phases_rad=steps)
    for name, band in [("dc", dc), ("c1", c1), ("c2", c2)]:
        assert abs(complex(getattr(actual, name).flat[0]) - band[0].native()) < 2e-14


@pytest.mark.parametrize("ridge", [0.0, 0.2])
def test_composition(ridge: float) -> None:
    images, steps, data, specimen, truth = alias_free_case()
    original = data["values"].copy()
    separated = public("separate_volume_phases")(images, phases_rad=steps)
    with localcontext() as ctx:
        ctx.prec = 80
        exact = separated_exact(images, steps)
    for name, band in zip(["dc", "c1", "c2"], exact[:3], strict=True):
        independent = np.array([a.native() for a in band]).reshape(images.shape[1:])
        assert np.max(np.abs(getattr(separated, name) - independent)) < 2e-13
    fits = []
    copied = {
        name: value.copy() if isinstance(value, np.ndarray) else value
        for name, value in data.items()
    }
    for order in [1, 2]:
        result = fit(images, steps, data, (0, 1), order)
        assert_metadata(result, order, (0, 1))
        expected = observe(images, steps, original, (0, 1), order)
        agreement(result, expected)
        assert abs(result.gain - truth[order - 1]) < 3e-12
        fits.append(result)
        copied["values"][order] *= result.gain
        assert np.isfinite(copied["values"][order].real).all()
        assert np.isfinite(copied["values"][order].imag).all()
        assert np.array_equal(copied["values"][0], original[0])
        if order == 1:
            assert np.array_equal(copied["values"][2], original[2])
    assert abs(fits[1].gain - fits[0].gain ** 2) > 0.2
    assert np.array_equal(data["values"], original)
    output = (2, 4, 12)
    kwargs = dict(
        phases_rad=steps[None],
        carriers_bins=np.array([[0, 1]]),
        gains=np.ones(1),
        regularization=ridge,
        output_shape_yx=output[1:],
        apodization=np.ones(output),
    )
    reconstructed = public("reconstruct_volume")(
        images[None], order_otfs=(calibration(copied),), **kwargs
    )
    expected_spectrum, expected_volume = reconstruction_observer(
        images, steps, copied["values"], output, ridge
    )
    brightness = max(abs(dec(v)) for v in images.flat)
    beta = (
        Decimal(65536 * 5 * (len(steps) + 64)) * EPS * brightness
        + Decimal(256 * 5 * (len(steps) + 64)) * QUANTUM
    )
    # All component <=1, gains=1, denominator >=1/4 and finite safe inputs.
    assert np.max(np.abs(copied["values"].real)) < 1
    assert np.max(np.abs(copied["values"].imag)) < 1
    assert np.max(np.abs(reconstructed.spectrum - expected_spectrum)) <= float(beta)
    assert np.max(np.abs(reconstructed.volume - expected_volume)) < 2e-10
    extended_truth = np.zeros(output, dtype=complex)
    for q, amplitude in specimen.items():
        extended_truth[index(q, output)] = amplitude
    error_to_truth = np.max(np.abs(reconstructed.spectrum - extended_truth))
    if ridge == 0:
        assert error_to_truth < 3e-12
        assert np.max(np.abs(reconstructed.volume - synthesize(specimen, output))) < 2e-10
    else:
        assert error_to_truth > 0.02
    uncorrected = public("reconstruct_volume")(
        images[None], order_otfs=(calibration(data),), **kwargs
    )
    assert np.max(np.abs(uncorrected.spectrum - reconstructed.spectrum)) > 0.05


def test_alias_limit() -> None:
    # Different extended transfer weights fold onto one detector mode.
    # E0(0)=Em(0)=1; extended E0(4)=0.2, Em(4)=0.8.
    truth = 0.3 + 0.2j
    folded_dc = 0.7 + 0.2 * 0.3
    folded_side = truth * (0.7 + 0.8 * 0.3)
    images, steps, data = constant_case(dc=folded_dc, c1=folded_side, shape=(1, 1, 4))
    specimen = {(0, 0, 0): 0.7 + 0j, (0, 0, 4): 0.3 + 0j}
    assert np.max(np.abs(synthesize(specimen, (1, 1, 4)) - 1)) < 1e-14
    periodic = public("separate_volume_phases")(images, phases_rad=steps)
    assert np.max(np.abs(periodic.dc - folded_dc)) < 1e-13
    result = fit(images, steps, data)
    agreement(result, observe(images, steps, data["values"], (0, 0), 1))
    assert result.coherence > 1 - 1e-12
    assert abs(result.gain - folded_side / folded_dc) < 1e-12
    assert abs(result.gain - truth) > 0.05
    assert np.max(np.abs(synthesize(specimen, (1, 1, 8)) - 1)) > 0.59
