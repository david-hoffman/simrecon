"""Blind A preservation evidence for BASELINE-COMPATIBILITY-01.

Run through scripts/source_free_check.py. Expectations use the public packet,
small finite sums, exact integer arithmetic and independent Decimal fits.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import warnings
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
import tifffile

import simrecon as sr
from shared_node_baseline_fixture import (
    decimal_fit,
    finite_dft,
    frequencies,
    priism_file,
    represented_matrix,
    signed_modes,
)

EPS = 2.0**-52
PHASES = np.array([0.0, 0.7, 1.8, 2.9, 4.0, 5.1, 6.0])
ROOT = Path(__file__).resolve().parents[1]


class ArraySubclass(np.ndarray[Any, Any]):
    """A real ndarray subclass, explicitly rejected at plain-array boundaries."""


class IntSubclass(int):
    """Lawful nonboolean integer scalar at scalar-int boundaries."""


class FloatSubclass(float):
    """Lawful nonboolean real scalar at scalar-real boundaries."""


def error(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(sr.SimreconError) as caught:
        operation()
    assert caught.value.code == code, f"expected={code}; actual={caught.value.code}"


def owned(array: np.ndarray[Any, Any], dtype: str, *inputs: np.ndarray[Any, Any]) -> None:
    assert type(array) is np.ndarray
    assert array.dtype == np.dtype(dtype)
    assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
    for source in inputs:
        assert not np.shares_memory(array, source)


def calibration(shape: tuple[int, int, int], values: np.ndarray[Any, Any] | None = None) -> Any:
    return sr.VolumeOrderOtf(
        values=np.ones((3, *shape), dtype=np.complex128) if values is None else values,
        fz_per_um=frequencies(shape[0], 1.0),
        fy_per_um=frequencies(shape[1], 1.0),
        fx_per_um=frequencies(shape[2], 1.0),
        voxel_size_um=(1.0, 1.0, 1.0),
        origin_zyx=(0, 0, 0),
        source=" opaque ",
    )


def volume_record_fields(record: Any) -> dict[str, Any]:
    return {
        field: getattr(record, field)
        for field in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }


def image_record_fields(record: Any) -> dict[str, Any]:
    return {
        field: getattr(record, field)
        for field in (
            "values",
            "fy_per_um",
            "fx_per_um",
            "pixel_size_um",
            "origin_yx",
            "source",
        )
    }


def image_calibration(shape: tuple[int, int]) -> Any:
    return sr.Otf2D(
        values=np.ones(shape, dtype=np.complex128),
        fy_per_um=frequencies(shape[0], 1.0),
        fx_per_um=frequencies(shape[1], 1.0),
        pixel_size_um=(1.0, 1.0),
        origin_yx=(0, 0),
        source=" caller ",
    )


def volume_signal(shape: tuple[int, int, int] = (1, 1, 2)) -> np.ndarray[Any, Any]:
    h = represented_matrix(PHASES)
    signal = h @ np.array([10.0, 4.0, 2.0, 6.0, -8.0])
    return np.broadcast_to(signal[:, None, None, None], (len(PHASES), *shape)).copy()


def scientific_call(name: str, data: Any) -> object:
    if name == "bead":
        return sr.locate_bead_peak(data)
    if name == "otf":
        return sr.prepare_volume_otf(
            data, voxel_size_um=(1, 1, 1), origin_zyx=(0, 0, 0), source="s"
        )
    if name == "empirical":
        return sr.prepare_empirical_volume_response(
            data, c1=np.zeros((1, 1, 2)), c2=np.zeros((1, 1, 2)), voxel_size_um=(1, 1, 1)
        )
    if name == "translation":
        return sr.estimate_translation(data, reference=np.ones((1, 2)), ambiguity_tolerance=0)
    if name == "drift":
        return sr.correct_integer_drift(
            data,
            phases_rad=np.zeros(1),
            carrier_bins_yx=np.zeros(2, dtype=int),
            displacements_pixels_yx=np.zeros((1, 2), dtype=int),
        )
    if name == "separation":
        return sr.separate_volume_phases(data, phases_rad=PHASES)
    if name == "gain":
        return sr.estimate_volume_order_gain(
            data,
            order_otf=calibration((1, 1, 2)),
            phase_steps_rad=PHASES,
            carrier_bins_yx=(0, 0),
            order=1,
        )
    if name == "scan":
        return sr.scan_carriers(
            data,
            otf=image_calibration((1, 2)),
            phase_steps_rad=PHASES,
            candidate_carriers_bins_yx=[(0, 0)],
        )
    if name == "reconstruction":
        return sr.reconstruct_volume(
            data,
            order_otfs=[calibration((1, 1, 2))],
            phases_rad=PHASES[None],
            carriers_bins=np.zeros((1, 2), dtype=int),
            gains=np.ones(1),
            regularization=0,
            output_shape_yx=(1, 2),
            apodization=np.ones((1, 1, 2)),
        )
    raise AssertionError("unknown public case")


@pytest.mark.parametrize(
    "name,shape,type_code,dtype_code,shape_code,finite_code",
    [
        (
            "gain",
            (7, 1, 1, 2),
            "invalid_volume_phase_images",
            "invalid_volume_phase_dtype",
            "invalid_volume_phase_shape",
            "nonfinite_volume_phase_images",
        ),
        (
            "scan",
            (7, 1, 2),
            "invalid_phase_images",
            "invalid_phase_dtype",
            "invalid_phase_shape",
            "nonfinite_phase_images",
        ),
        (
            "reconstruction",
            (1, 7, 1, 1, 2),
            "invalid_volume_reconstruction_images",
            "invalid_volume_reconstruction_dtype",
            "invalid_volume_reconstruction_shape",
            "nonfinite_volume_reconstruction_images",
        ),
        (
            "bead",
            (1, 1, 2),
            "invalid_bead_peak_volume",
            "invalid_bead_peak_dtype",
            "invalid_bead_peak_shape",
            "nonfinite_bead_peak_volume",
        ),
        (
            "otf",
            (1, 1, 2),
            "invalid_psf",
            "invalid_psf_dtype",
            "invalid_psf_shape",
            "nonfinite_psf",
        ),
        (
            "empirical",
            (1, 1, 2),
            "invalid_empirical_response_array",
            "invalid_empirical_response_dtype",
            "invalid_empirical_response_shape",
            "nonfinite_empirical_response_array",
        ),
        (
            "translation",
            (1, 2),
            "invalid_translation_images",
            "invalid_translation_images",
            "invalid_translation_images",
            "invalid_translation_images",
        ),
        (
            "drift",
            (1, 1, 2),
            "invalid_drift_images",
            "invalid_drift_images",
            "invalid_drift_images",
            "invalid_drift_images",
        ),
        (
            "separation",
            (7, 1, 1, 2),
            "invalid_volume_phase_images",
            "invalid_volume_phase_dtype",
            "invalid_volume_phase_shape",
            "nonfinite_volume_phase_images",
        ),
    ],
)
def test_operation_specific_array_validation(
    name: str,
    shape: tuple[int, ...],
    type_code: str,
    dtype_code: str,
    shape_code: str,
    finite_code: str,
) -> None:
    base = np.ones(shape)
    for invalid in (base.tolist(), base.view(ArraySubclass), np.ma.array(base)):
        error(type_code, lambda invalid=invalid: scientific_call(name, cast(Any, invalid)))
    for dtype in (bool, object, complex, "U1", "datetime64[D]"):
        bad = np.ones(shape).astype(dtype)
        error(dtype_code, lambda bad=bad: scientific_call(name, cast(Any, bad)))
    error(shape_code, lambda: scientific_call(name, np.empty((0, *shape[1:]))))
    for value in (np.nan, np.inf, -np.inf):
        bad = base.copy()
        bad.flat[0] = value
        before = bad.tobytes()
        error(finite_code, lambda bad=bad: scientific_call(name, cast(Any, bad)))
        assert bad.tobytes() == before


@pytest.mark.parametrize(
    "dtype",
    ["i1", ">i2", "<i4", ">i8", "u1", ">u2", "u4", ">u8", "f2", ">f4", ">f8", np.longdouble],
)
def test_real_widths_endian_and_readonly_storage(dtype: Any) -> None:
    data = np.array([[[1, 3, 2, 0]]], dtype=dtype)[:, :, ::-1]
    data.flags.writeable = False
    before, strides = data.tobytes(), data.strides
    peak = sr.locate_bead_peak(data)
    assert peak.index_zyx == (0, 0, 2) and peak.value == 3.0
    result = sr.prepare_volume_otf(
        data, voxel_size_um=[1, 2, 3], origin_zyx=np.array([0, 0, 2]), source=" label "
    )
    expected = finite_dft(data.astype(np.float64) / 6.0, (0, 0, 2))
    np.testing.assert_allclose(result.values, expected, rtol=0, atol=128 * 4 * EPS)
    owned(result.values, "complex128", data)
    assert result.source == " label "
    assert data.tobytes() == before and data.strides == strides and not data.flags.writeable


def test_bead_exact_peak_tie_and_conversion_decisions() -> None:
    q = np.nextafter(0.0, 1.0)
    for value in (q, np.finfo(float).max):
        peak = sr.locate_bead_peak(np.array([[[value, -1, -1]]]))
        assert peak.index_zyx == (0, 0, 0) and peak.value == float(value)
        assert type(peak.value) is float and all(type(i) is int for i in peak.index_zyx)
        with pytest.raises((AttributeError, TypeError)):
            cast(Any, peak).value = 4
    for values in ([0, -0.0, -1], [-1, -2, -3]):
        error(
            "no_positive_bead_peak",
            lambda values=values: sr.locate_bead_peak(np.array([[cast(Any, values)]])),
        )
    error("ambiguous_bead_peak", lambda: sr.locate_bead_peak(np.array([[[2, 2]]])))
    error(
        "ambiguous_bead_peak",
        lambda: sr.locate_bead_peak(np.array([[[2**53, 2**53 + 1]]], dtype=np.uint64)),
    )
    near = sr.locate_bead_peak(np.array([[[1, np.nextafter(1.0, 2.0), -1]]]))
    assert near.index_zyx == (0, 0, 1)


def test_available_native_float_source_conversion_boundaries() -> None:
    ordinary = np.array([[[np.nextafter(0.0, 1.0), -0.0]]], dtype=np.longdouble)
    assert sr.locate_bead_peak(ordinary).value == float(ordinary[0, 0, 0])
    error("negative_psf", lambda: scientific_call("otf", -ordinary))
    if np.finfo(np.longdouble).max <= np.longdouble(np.finfo(float).max):
        # This platform cannot represent the wider-only examples. Their risk
        # remains explicitly unsupported in the handoff; ordinary checks ran.
        return
    tiny = np.nextafter(np.longdouble(0), np.longdouble(1))
    big = np.longdouble(np.finfo(float).max) * 2
    assert tiny > 0 and float(tiny) == 0.0
    error(
        "negative_psf",
        lambda: scientific_call("otf", np.array([[[-tiny, 1]]], dtype=np.longdouble)),
    )
    error(
        "zero_psf_mass",
        lambda: scientific_call("otf", np.array([[[tiny, tiny]]], dtype=np.longdouble)),
    )
    for name, shape, code in (
        ("bead", (1, 1, 2), "nonfinite_bead_peak_volume"),
        ("otf", (1, 1, 2), "nonfinite_psf"),
        ("empirical", (1, 1, 2), "nonfinite_empirical_response_array"),
        ("translation", (1, 2), "invalid_translation_images"),
        ("drift", (1, 1, 2), "invalid_drift_images"),
        ("separation", (7, 1, 1, 2), "nonfinite_volume_phase_images"),
    ):
        error(
            code,
            lambda name=name, shape=shape: scientific_call(
                cast(Any, name), np.full(cast(Any, shape), big, dtype=np.longdouble)
            ),
        )
    error(
        "invalid_translation_tolerance",
        lambda: sr.estimate_translation(
            np.zeros((1, 1)), reference=np.zeros((1, 1)), ambiguity_tolerance=-tiny
        ),
    )
    result = sr.estimate_translation(
        np.zeros((1, 1)), reference=np.zeros((1, 1)), ambiguity_tolerance=tiny
    )
    assert result.displacement_pixels_yx == (0, 0)


@pytest.mark.parametrize(
    "dtype,carrier,shift",
    [
        (np.int64, (-(2**63), 2**63 - 1), (2**63 - 1, -(2**63))),
        (np.uint64, (2**64 - 1, 2**64 - 2), (2**64 - 3, 2**64 - 1)),
        (np.int16, (0, 1), (0, 1)),
    ],
)
def test_drift_exact_integer_permutation_and_circular_phase(
    dtype: Any, carrier: tuple[int, int], shift: tuple[int, int]
) -> None:
    images = np.arange(12.0).reshape(1, 3, 4)[:, :, ::-1]
    phases = np.array([np.finfo(float).max])
    k = np.array(carrier, dtype=dtype)
    d = np.array([shift], dtype=dtype)
    original = [a.tobytes() for a in (images, phases, k, d)]
    result = sr.correct_integer_drift(
        images, phases_rad=phases, carrier_bins_yx=k, displacements_pixels_yx=d
    )
    expected = np.array(
        [[images[0, (y + shift[0]) % 3, (x + shift[1]) % 4] for x in range(4)] for y in range(3)]
    )
    np.testing.assert_array_equal(result.images[0], expected)
    residue = (carrier[0] * shift[0] * 4 + carrier[1] * shift[1] * 3) % 12
    alpha = (2 * np.pi) * float(Fraction(residue, 12))
    target = complex(np.cos(phases[0]), np.sin(phases[0])) * complex(np.cos(alpha), np.sin(alpha))
    target /= abs(target)
    actual = complex(np.cos(result.phases_rad[0]), np.sin(result.phases_rad[0]))
    assert abs(actual - target) <= 512 * EPS
    for a, b in zip((images, phases, k, d), original, strict=True):
        assert a.tobytes() == b
    owned(result.images, "float64", images, phases, k, d)
    owned(result.phases_rad, "float64", images, phases, k, d, result.images)


def test_drift_degenerate_phases_and_exact_container_rules() -> None:
    args = dict(
        phases_rad=np.zeros(3),
        carrier_bins_yx=np.zeros(2, dtype=int),
        displacements_pixels_yx=np.zeros((3, 2), dtype=int),
    )
    result = sr.correct_integer_drift(np.ones((3, 1, 1)), **args)
    error(
        "rank_deficient_phases",
        lambda: sr.separate_phases(result.images, phases_rad=result.phases_rad),
    )
    for key, invalid, code in (
        ("carrier_bins_yx", [0, 0], "invalid_drift_carrier"),
        ("carrier_bins_yx", np.array([0.0, 0.0]), "invalid_drift_carrier"),
        ("displacements_pixels_yx", np.zeros((3, 2), dtype=bool), "invalid_drift_displacements"),
        ("phases_rad", np.zeros(3, dtype=complex), "invalid_drift_phases"),
    ):
        error(
            code,
            lambda invalid=invalid, key=key: sr.correct_integer_drift(
                np.ones((3, 1, 1)), **cast(Any, args | {cast(Any, key): cast(Any, invalid)})
            ),
        )


@pytest.mark.parametrize("mass_case", ["signed", "overflow", "subnormal"])
def test_empirical_shared_exact_mass_origin_and_side_rows(mass_case: str) -> None:
    q, f = np.nextafter(0.0, 1.0), np.finfo(float).max
    dc = (
        np.array([[[2.0, -1.0]]])
        if mass_case == "signed"
        else np.array([[[f, f / 2]]])
        if mass_case == "overflow"
        else np.array([[[q, 0.0]]])
    )
    c1, c2 = dc.astype(complex) * 1j, np.zeros(dc.shape, dtype=complex)
    response = sr.prepare_empirical_volume_response(dc, c1=c1, c2=c2, voxel_size_um=(1, 1, 1))
    mass = sum(Fraction(float(v)) for v in dc.flat)
    normalized = np.array([float(Fraction(float(v)) / mass) for v in dc.flat]).reshape(dc.shape)
    expected = finite_dft(normalized)
    budget = float(
        512 * dc.size * Fraction(1, 2**52) * sum(abs(Fraction(float(v))) for v in dc.flat) / mass
    )
    np.testing.assert_allclose(response.values[0], expected, rtol=0, atol=budget)
    np.testing.assert_allclose(response.values[1], 1j * expected, rtol=0, atol=budget)
    np.testing.assert_array_equal(response.values[2], np.zeros(dc.shape))
    assert response.values[0, 0, 0, 1] == 1 + 0j
    assert response.origin_zyx == (0, 0, 0)
    owned(response.values, "complex128", dc, c1, c2)
    if mass_case == "signed":
        error(
            "nonpositive_empirical_response_mass",
            lambda: sr.prepare_empirical_volume_response(
                np.array([[[2, -3]]]), c1=c1, c2=c2, voxel_size_um=(1, 1, 1)
            ),
        )


def test_empirical_roll_and_phase_gauge() -> None:
    dc = np.array([[[1, 4, -1]], [[0, 2, 1]]], dtype=float)
    c1 = (dc + 1j * np.arange(6).reshape(dc.shape)).astype(complex)
    c2 = np.zeros_like(c1)
    first = sr.prepare_empirical_volume_response(dc, c1=c1, c2=c2, voxel_size_um=(1, 1, 1))
    second = sr.prepare_empirical_volume_response(
        np.roll(dc, (1, 0, 1), (0, 1, 2)),
        c1=np.roll(-1j * c1, (1, 0, 1), (0, 1, 2)),
        c2=c2,
        voxel_size_um=(1, 1, 1),
    )
    np.testing.assert_allclose(
        second.values[0], first.values[0], rtol=0, atol=512 * 6 * EPS * 9 / 7
    )
    np.testing.assert_allclose(
        second.values[1], -1j * first.values[1], rtol=0, atol=512 * 6 * EPS * 24 / 7
    )


@pytest.mark.parametrize(
    "spacing", [(np.nextafter(0.0, 1.0), np.finfo(float).max, 1.0), (1.0, 2.0, 3.0)]
)
def test_singleton_spacing_and_large_component_delta_orders(
    spacing: tuple[float, float, float],
) -> None:
    f = np.finfo(float).max
    coeff = np.array([[complex(f, f)], [0j]])
    result = sr.prepare_volume_order_otfs(
        np.ones((1, 1, 1)),
        axial_coefficients=coeff,
        voxel_size_um=spacing,
        origin_zyx=(0, 0, 0),
        source=" delta ",
    )
    assert result.values[0, 0, 0, 0] == 1
    assert result.values[1, 0, 0, 0] == complex(f, f)
    assert result.values[2, 0, 0, 0] == 0
    for vector in (result.fz_per_um, result.fy_per_um, result.fx_per_um):
        np.testing.assert_array_equal(vector, [0.0])


def test_otf_mass_and_frequency_boundaries() -> None:
    for amplitude in (np.nextafter(0.0, 1.0), np.finfo(float).max):
        result = sr.prepare_volume_otf(
            np.full((1, 1, 2), amplitude),
            voxel_size_um=(1, 1, np.finfo(float).max),
            origin_zyx=(0, 0, 0),
            source="s",
        )
        np.testing.assert_allclose(result.values, [[[0, 1]]], rtol=0, atol=128 * 2 * EPS)
        assert result.fx_per_um[0] < 0 and result.fx_per_um[1] == 0
    error(
        "unrepresentable_otf_frequencies",
        lambda: sr.prepare_volume_otf(
            np.ones((1, 1, 2)),
            voxel_size_um=(1, 1, np.nextafter(0.0, 1.0)),
            origin_zyx=(0, 0, 0),
            source="s",
        ),
    )
    for args, code in (
        ({"voxel_size_um": (1, True, 1)}, "invalid_otf_voxel_size"),
        ({"origin_zyx": (0, 0, 0.0)}, "invalid_otf_origin"),
        ({"source": " \t"}, "invalid_otf_source"),
    ):
        base = dict(voxel_size_um=(1, 1, 1), origin_zyx=(0, 0, 0), source="s")
        error(
            code,
            lambda args=args, base=base: sr.prepare_volume_otf(
                np.ones((1, 1, 2)), **cast(Any, cast(Any, base) | cast(Any, args))
            ),
        )


def test_order_displacement_frame_finite_sum_and_roll() -> None:
    psf = np.array([[[1, 2, 0]], [[3, 0, 1]]], dtype=float)
    coefficients = np.array([[2j, -2j], [0, 0]], dtype=complex)
    origin = (1, 0, 1)
    result = sr.prepare_volume_order_otfs(
        psf, axial_coefficients=coefficients, voxel_size_um=(1, 2, 3), origin_zyx=origin, source="s"
    )
    for m in range(3):
        row = np.ones(2) if m == 0 else coefficients[m - 1]
        expected = finite_dft(psf / 7 * row[:, None, None], origin)
        np.testing.assert_allclose(
            result.values[m],
            expected,
            rtol=0,
            atol=256 * 6 * EPS * max(1, float(np.max(np.abs(row)))),
        )
    shifted = sr.prepare_volume_order_otfs(
        np.roll(psf, 1, axis=0),
        axial_coefficients=np.roll(coefficients, 1, axis=1),
        voxel_size_um=(1, 2, 3),
        origin_zyx=(0, 0, 1),
        source="s",
    )
    np.testing.assert_allclose(shifted.values, result.values, rtol=0, atol=256 * 6 * EPS * 2)


def transform_call(name: str) -> object:
    psf = np.array([[[1.0, 2.0]]])
    if name == "detection":
        return sr.prepare_volume_otf(psf, voxel_size_um=(1, 1, 1), origin_zyx=(0, 0, 0), source="s")
    if name == "order":
        return sr.prepare_volume_order_otfs(
            psf,
            axial_coefficients=np.ones((2, 1), dtype=complex),
            voxel_size_um=(1, 1, 1),
            origin_zyx=(0, 0, 0),
            source="s",
        )
    if name == "empirical":
        return sr.prepare_empirical_volume_response(
            psf, c1=psf.astype(complex), c2=np.zeros_like(psf), voxel_size_um=(1, 1, 1)
        )
    if name == "recombination":
        return sr.reconstruct_volume(
            volume_signal()[None],
            order_otfs=[calibration((1, 1, 2))],
            phases_rad=PHASES[None],
            carriers_bins=np.zeros((1, 2), dtype=int),
            gains=np.ones(1),
            regularization=0,
            output_shape_yx=(1, 2),
            apodization=np.ones((1, 1, 2)),
        )
    if name == "gain":
        return sr.estimate_volume_order_gain(
            volume_signal(),
            order_otf=calibration((1, 1, 2)),
            phase_steps_rad=PHASES,
            carrier_bins_yx=(0, 0),
            order=1,
        )
    raise AssertionError("unknown transform case")


@pytest.mark.parametrize(
    "name,code",
    [
        ("detection", "otf_transform_failure"),
        ("order", "volume_order_transform_failure"),
        ("empirical", "empirical_response_transform_failure"),
        ("recombination", "volume_reconstruction_transform_failure"),
        ("gain", "volume_order_gain_transform_failure"),
    ],
)
@pytest.mark.parametrize("failure", ["floating", "overflow", "warning", "nonfinite"])
def test_named_fft_failure_taxonomy_and_caller_policy(
    monkeypatch: pytest.MonkeyPatch, name: str, code: str, failure: str
) -> None:
    original = np.fft.fftn

    def controlled(*args: Any, **kwargs: Any) -> Any:
        if failure == "floating":
            raise FloatingPointError("controlled public transform")
        if failure == "overflow":
            raise OverflowError("controlled public transform")
        if failure == "warning":
            warnings.warn("controlled arithmetic transform", RuntimeWarning, stacklevel=2)
        output = original(*args, **kwargs)
        if failure == "nonfinite":
            output.flat[0] = complex(np.nan, 0)
        return output

    monkeypatch.setattr(np.fft, "fftn", controlled)
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("ignore", RuntimeWarning)
        prior_mode, prior_filters = np.geterr().copy(), list(warnings.filters)
        error(code, lambda: transform_call(name))
        assert np.geterr() == prior_mode and warnings.filters == prior_filters
        assert not any(issubclass(item.category, RuntimeWarning) for item in emitted)


@pytest.mark.parametrize("name", ["detection", "order", "empirical", "recombination", "gain"])
@pytest.mark.parametrize("exception_type", [MemoryError, RuntimeError, TypeError, ValueError])
def test_unrelated_fft_exception_identity(
    monkeypatch: pytest.MonkeyPatch, name: str, exception_type: type[Exception]
) -> None:
    sentinel = exception_type("public dependency sentinel")

    def controlled(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    monkeypatch.setattr(np.fft, "fftn", controlled)
    with pytest.raises(exception_type) as caught:
        transform_call(name)
    assert caught.value is sentinel


@pytest.mark.parametrize("name", ["detection", "order", "empirical", "recombination", "gain"])
def test_unrelated_fft_warning_remains_observable(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original = np.fft.fftn

    def controlled(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("public user warning", UserWarning, stacklevel=2)
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", controlled)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always", UserWarning)
        transform_call(name)
        assert any(
            item.category is UserWarning and str(item.message) == "public user warning"
            for item in emitted
        )


def test_inverse_recombination_fft_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def controlled(*args: Any, **kwargs: Any) -> Any:
        raise FloatingPointError("public inverse synthesis")

    monkeypatch.setattr(np.fft, "ifftn", controlled)
    error("volume_reconstruction_transform_failure", lambda: transform_call("recombination"))


def test_empirical_and_order_natural_restoration_range() -> None:
    f = float(np.finfo(float).max)
    # Exact dc mass is 1. A side-order DC sum 2*F is genuinely out of range.
    error(
        "unrepresentable_empirical_response",
        lambda: sr.prepare_empirical_volume_response(
            np.array([[[2.0, -1.0]]]),
            c1=np.full((1, 1, 2), f, dtype=complex),
            c2=np.zeros((1, 1, 2)),
            voxel_size_um=(1, 1, 1),
        ),
    )
    # A delta one axial sample away from the declared origin rotates F+iF
    # by a cube root. One component is -(1+sqrt(3))*F/2, safely beyond F.
    error(
        "unrepresentable_volume_order_otf",
        lambda: sr.prepare_volume_order_otfs(
            np.array([0.0, 1.0, 0.0])[:, None, None],
            axial_coefficients=np.full((2, 3), complex(f, f)),
            voxel_size_um=(1, 1, 1),
            origin_zyx=(0, 0, 0),
            source="s",
        ),
    )


def test_raw_named_axes_preserve_nan_payloads_and_metadata() -> None:
    words = np.array(
        [0x80000000, 0x7F800000, 0xFF800000, 0x7FC12345, 0x3F800000, 0x00000000], dtype=">u4"
    )
    data = words.view(">f4").reshape(2, 1, 1, 3)
    data.flags.writeable = False
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "detection_psf",
        "axes": ["z", "channel", "y", "x"],
        "sampling_um": {"x": 0.25, "y": 0.5},
        "intensity_unit": "  ",
    }
    metadata: dict[str, Any] = {"opaque": [b"\x00\xff", (float("inf"), "label")], "unknown": None}
    result = sr.declare_acquisition(data, config=config, original_metadata=metadata)
    assert result.axes == ("channel", "z", "y", "x")
    assert result.source_axes == ("z", "channel", "y", "x")
    assert result.data.dtype.str == ">f4"
    assert result.data.tobytes() == data.transpose(1, 0, 2, 3).tobytes()
    assert result.sampling_um == {"x": 0.25, "y": 0.5, "z": None}
    assert result.intensity_unit == "  " and result.nominal_phases_rad is None
    owned(result.data, ">f4", data)
    metadata["opaque"].append("later")
    config["sampling_um"]["x"] = 9
    assert len(result.original_metadata["opaque"]) == 2
    assert result.original_config["sampling_um"]["x"] == 0.25
    assert not data.flags.writeable and data.tobytes() == words.tobytes()


def test_raw_wider_padding_bytes_survive_coordinate_reorder() -> None:
    data = np.arange(12, dtype=np.longdouble).reshape(2, 2, 1, 3)[:, ::-1]
    result = sr.declare_acquisition(
        data,
        config={
            "version": 1,
            "acquisition_kind": "detection_psf",
            "axes": ["z", "channel", "y", "x"],
        },
    )
    assert result.data.dtype == data.dtype
    for channel in range(2):
        for z in range(2):
            assert result.data[channel, z].tobytes() == data[z, channel].tobytes()


def test_raw_overrides_group_commands_and_schema() -> None:
    data = np.arange(12, dtype=np.int16).reshape(3, 2, 1, 2)
    commands = [[float(10 * p + o) for o in range(2)] for p in range(3)]
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "specimen_sim",
        "axes": ["phase", "orientation", "y", "x"],
        "sampling_um": {"x": -1},
        "nominal_phases_rad": commands,
        "intensity_unit": "counts",
        "overrides": {
            "sampling_um": {"x": 0.25},
            "intensity_unit": "counts",
            "calibration_id": None,
        },
    }
    result = sr.declare_acquisition(data, config=config)
    assert result.axes == ("orientation", "phase", "y", "x")
    np.testing.assert_array_equal(result.data, data.transpose(1, 0, 2, 3))
    np.testing.assert_array_equal(result.nominal_phases_rad, np.array(commands).T)
    assert result.nominal_phase_axes == ("orientation", "phase")
    assert result.sampling_um == {"x": 0.25, "y": None, "z": None}
    initial = sorted(key for key in config if key not in ("version", "overrides"))
    overridden = sorted(config["overrides"])
    assert [p["field"] for p in result.provenance] == initial + overridden
    assert [p["source"] for p in result.provenance] == ["config"] * len(initial) + [
        "override"
    ] * len(overridden)
    for change, code in (
        ({"version": True}, "invalid_acquisition_config"),
        ({"extra": 1}, "invalid_acquisition_config"),
        ({"axes": ["phase", "phase", "y", "x"]}, "invalid_acquisition_axes"),
        ({"acquisition_kind": "detection_psf"}, "invalid_acquisition_kind"),
        ({"nominal_phases_rad": [0, 1, 2]}, "invalid_acquisition_phase_commands"),
        ({"wavelengths_nm": {"00": 488}}, "invalid_acquisition_wavelengths"),
        ({"overrides": {"axes": ["y", "x"]}}, "invalid_acquisition_config"),
    ):
        error(
            code,
            lambda change=change: sr.declare_acquisition(data, config=config | cast(Any, change)),
        )
    for bad in ({"value": np.array([1])}, {"value": object()}):
        error(
            "invalid_acquisition_metadata",
            lambda bad=bad: sr.declare_acquisition(
                data, config=config, original_metadata=cast(Any, bad)
            ),
        )
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic
    error(
        "invalid_acquisition_metadata",
        lambda: sr.declare_acquisition(data, config=config, original_metadata=cyclic),
    )


def raw(data: np.ndarray[Any, Any]) -> Any:
    return sr.declare_acquisition(
        data,
        config={
            "version": 1,
            "acquisition_kind": "detection_psf",
            "axes": ["y", "x"],
            "intensity_unit": " count ",
            "acquisition_id": " opaque ",
        },
        original_metadata={"opaque": [b"bytes", (float("nan"),)]},
    )


@pytest.mark.parametrize(
    "offset_array,response_array", [(False, False), (False, True), (True, False), (True, True)]
)
def test_linear_scalar_and_full_map_alignment_snapshots(
    offset_array: bool, response_array: bool
) -> None:
    data = np.array([[110, 14], [-6, 22]], dtype=">i2")
    acquisition = raw(data)
    offset: Any = np.array([[10, 2], [-2, 6]], dtype=">i2") if offset_array else 10
    response: Any = np.array([[2, 4], [2, 8]], dtype=">f4") if response_array else 2.0
    expected = (data.astype(float) - offset) / response
    result = sr.correct_linear_response(
        acquisition, offset=offset, response=response, output_unit=" electron "
    )
    np.testing.assert_array_equal(result.data, expected)
    owned(result.data, "float64", data, acquisition.data)
    assert (
        result.axes == acquisition.axes
        and result.input_unit == " count "
        and result.output_unit == " electron "
    )
    assert result.provenance["model"] == "linear_response_v1"
    assert result.provenance["equation"] == "raw=offset+response*signal"
    for name, supplied in (("offset", offset), ("response", response)):
        entry = result.provenance[name]
        assert entry["source"] == "supplied"
        if isinstance(supplied, np.ndarray):
            assert entry["supplied"].dtype == supplied.dtype
            assert entry["supplied"].tobytes() == supplied.tobytes()
            owned(entry["supplied"], supplied.dtype.str, supplied)
            owned(entry["applied"], "float64", supplied)
            supplied[...] = 0
        else:
            assert type(entry["supplied"]) is type(supplied)
            assert type(entry["applied"]) is float
    acquisition.original_metadata["opaque"].append("mutated")
    assert len(result.source_metadata["original_metadata"]["opaque"]) == 2
    assert "data" not in result.source_metadata
    np.testing.assert_array_equal(result.data, expected)


def test_linear_range_underflow_scalar_representations_and_source_nonfinite() -> None:
    f, q = float(np.finfo(float).max), float(np.nextafter(0.0, 1.0))
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as emitted:
        mode = np.geterr().copy()
        negative = sr.correct_linear_response(
            raw(np.array([[-q]])), offset=0, response=f, output_unit="e"
        )
        assert negative.data[0, 0] == 0 and np.signbit(negative.data[0, 0])
        error(
            "linear_response_range",
            lambda: sr.correct_linear_response(
                raw(np.array([[f]])), offset=-f, response=f, output_unit="e"
            ),
        )
        error(
            "linear_response_range",
            lambda: sr.correct_linear_response(
                raw(np.array([[1.0]])), offset=0, response=q, output_unit="e"
            ),
        )
        assert np.geterr() == mode and not any(
            issubclass(w.category, RuntimeWarning) for w in emitted
        )
    acquisition = raw(np.ones((1, 1)))
    for value in (np.float64(1), [1], True, complex(1)):
        error(
            "invalid_linear_response_offset",
            lambda value=value: sr.correct_linear_response(
                acquisition, offset=cast(Any, value), response=1, output_unit="e"
            ),
        )
    error(
        "invalid_linear_response_shape",
        lambda: sr.correct_linear_response(
            acquisition, offset=np.array(1.0), response=1, output_unit="e"
        ),
    )
    for value in (0, -1, np.nan, True):
        error(
            "invalid_linear_response_response",
            lambda value=value: sr.correct_linear_response(
                acquisition, offset=0, response=cast(Any, value), output_unit="e"
            ),
        )
    error(
        "invalid_linear_response_shape",
        lambda: sr.correct_linear_response(
            acquisition, offset=np.ones((1, 2)), response=1, output_unit="e"
        ),
    )
    error(
        "invalid_linear_response_unit",
        lambda: sr.correct_linear_response(acquisition, offset=0, response=1, output_unit=""),
    )
    for value in (np.nan, np.inf):
        declared = raw(np.array([[value]]))
        error(
            "invalid_linear_response_data",
            lambda declared=declared: sr.correct_linear_response(
                cast(Any, declared), offset=0, response=1, output_unit="e"
            ),
        )


def test_translation_full_canonical_grid_objective_and_same_call_boundary() -> None:
    reference = np.array([[0, 1, 8, -2], [3, 5, -4, 7]], dtype=float)
    moving = np.array([[1, -3, 5, 2], [9, 0, 4, -7]], dtype=float)
    result = sr.estimate_translation(moving, reference=reference, ambiguity_tolerance=0)
    scale = 9.0
    expected = np.array(
        [
            [
                math.sqrt(
                    math.fsum(
                        (moving[(y + dy) % 2, (x + dx) % 4] / scale - reference[y, x] / scale) ** 2
                        for y in range(2)
                        for x in range(4)
                    )
                    / 8
                )
                for dx in signed_modes(4)
            ]
            for dy in signed_modes(2)
        ]
    )
    np.testing.assert_allclose(result.normalized_rms, expected, rtol=0, atol=4096 * 8 * EPS)
    scores = result.normalized_rms
    minimum = float(np.min(scores))
    tolerance = float(np.sort(scores.ravel())[2] - minimum)
    boundary = sr.estimate_translation(
        moving, reference=reference, ambiguity_tolerance=np.array(tolerance)
    )
    wanted = tuple(
        (dy, dx)
        for iy, dy in enumerate(signed_modes(2))
        for ix, dx in enumerate(signed_modes(4))
        if boundary.normalized_rms[iy, ix] - boundary.minimum_normalized_rms <= tolerance
    )
    assert boundary.candidate_displacements_pixels_yx == wanted
    assert (
        boundary.displacement_pixels_yx is None and boundary.failure_code == "ambiguous_translation"
    )
    owned(result.normalized_rms, "float64", moving, reference, boundary.normalized_rms)
    shifted = np.roll(reference, (1, 2), axis=(0, 1))
    motion = sr.estimate_translation(shifted, reference=reference, ambiguity_tolerance=0)
    assert motion.displacement_pixels_yx == (-1, -2)
    assert motion.minimum_normalized_rms == 0.0


@pytest.mark.parametrize(
    "tolerance", [0, -0.0, np.int16(0), FloatSubclass(2), np.array(2, dtype=">i2")]
)
def test_translation_scalar_and_constant_positives(tolerance: Any) -> None:
    singleton = sr.estimate_translation(
        np.array([[2.0]]), reference=np.array([[-2.0]]), ambiguity_tolerance=tolerance
    )
    assert singleton.displacement_pixels_yx == (0, 0) and singleton.minimum_normalized_rms == 2
    constant = sr.estimate_translation(
        np.zeros((2, 3)), reference=np.zeros((2, 3)), ambiguity_tolerance=tolerance
    )
    assert len(constant.candidate_displacements_pixels_yx) == 6
    assert constant.displacement_pixels_yx is None
    for bad in (True, [0], np.array([0]), np.array(0).view(ArraySubclass), complex(0), np.nan, -1):
        error(
            "invalid_translation_tolerance",
            lambda bad=bad: sr.estimate_translation(
                np.zeros((1, 1)), reference=np.zeros((1, 1)), ambiguity_tolerance=cast(Any, bad)
            ),
        )
    error(
        "incompatible_translation_shape",
        lambda: sr.estimate_translation(
            np.zeros((1, 2)), reference=np.zeros((2, 1)), ambiguity_tolerance=0
        ),
    )


@pytest.mark.parametrize("huge", [False, True])
def test_volume_represented_offmodel_fit_and_repeated_phase_rank(huge: bool) -> None:
    phases = PHASES.copy()
    if huge:
        phases[0] = np.finfo(float).max
    matrix = represented_matrix(phases)
    assert np.linalg.cond(matrix) < 10
    observations = matrix @ np.array([10, 4, 2, 6, -8], dtype=float) + np.array(
        [0, 1, -1, 0.5, 0, -0.5, 0]
    )
    exact = decimal_fit(matrix, observations)
    expected = np.array([exact[0], exact[1] / 2, -exact[2] / 2, exact[3] / 2, -exact[4] / 2])
    images = observations[:, None, None, None]
    result = sr.separate_volume_phases(images, phases_rad=phases)
    actual = np.array(
        [
            result.dc.item(),
            result.c1.real.item(),
            result.c1.imag.item(),
            result.c2.real.item(),
            result.c2.imag.item(),
        ]
    )
    budget = 8192 * len(phases) * EPS * float(np.max(np.abs(observations)))
    np.testing.assert_allclose(actual, expected, rtol=0, atol=budget)
    for array, dtype in (
        (result.dc, "float64"),
        (result.c1, "complex128"),
        (result.c2, "complex128"),
    ):
        owned(array, dtype, images, phases)
    repeated = np.concatenate((phases, phases[:1]))
    repeated_images = np.concatenate((images, images[:1]))
    accepted = sr.separate_volume_phases(repeated_images, phases_rad=repeated)
    repeated_exact = decimal_fit(represented_matrix(repeated), repeated_images[:, 0, 0, 0])
    assert abs(accepted.dc.item() - repeated_exact[0]) <= 8192 * 8 * EPS * float(
        np.max(np.abs(observations))
    )
    error(
        "rank_deficient_volume_phases",
        lambda: sr.separate_volume_phases(np.ones((7, 1, 1, 1)), phases_rad=np.zeros(7)),
    )


def recombination_args(otf: Any, *, mask: np.ndarray[Any, Any] | None = None) -> dict[str, Any]:
    return dict(
        order_otfs=[otf],
        phases_rad=PHASES[None],
        carriers_bins=np.zeros((1, 2), dtype=int),
        gains=np.ones(1),
        regularization=0,
        output_shape_yx=(1, 8),
        apodization=np.ones((1, 1, 8)) if mask is None else mask,
    )


def test_complex_signed_nyquist_lift_field_of_view_and_weighted_mask() -> None:
    values = np.zeros((3, 1, 1, 4), dtype=complex)
    values[0] = 1
    otf = calibration((1, 1, 4), values)
    images = np.broadcast_to(np.array([1, -1, 1, -1]), (1, 7, 1, 1, 4)).copy()
    args = recombination_args(otf)
    result = sr.reconstruct_volume(images, **args)
    expected_spectrum = np.zeros((1, 1, 8), dtype=complex)
    expected_spectrum[0, 0, 2] = 1
    expected_volume = np.array([np.exp(-2j * np.pi * 2 * x / 8) for x in range(8)])[None, None]
    n, m, p, j = 7, 4, 8, 5
    spectrum_budget = 65536 * j * (n + m) * EPS
    volume_budget = p * spectrum_budget + 16384 * j * p * EPS
    np.testing.assert_allclose(result.spectrum, expected_spectrum, rtol=0, atol=spectrum_budget)
    np.testing.assert_allclose(result.volume, expected_volume, rtol=0, atol=volume_budget)
    assert result.voxel_size_um == (1.0, 1.0, 0.5)
    np.testing.assert_array_equal(result.fx_per_um, np.arange(-4, 4) / 4)
    assert abs(result.volume[0, 0, 1].imag) > 0.99
    for array in (result.spectrum, result.volume):
        owned(array, "complex128", images, values)
    assert not np.shares_memory(result.spectrum, result.volume)
    weighted = sr.reconstruct_volume(
        images,
        **(
            cast(
                Any,
                args
                | {
                    "gains": np.array([2.0]),
                    "regularization": 1.0,
                    "apodization": np.full((1, 1, 8), 0.5),
                },
            )
        ),
    )
    # U=2, V=4, ridge=1, amplitude mask=1/2: T=(2/5)*(1/2)=1/5.
    np.testing.assert_allclose(
        weighted.spectrum, expected_spectrum / 5, rtol=0, atol=spectrum_budget
    )
    np.testing.assert_allclose(weighted.volume, expected_volume / 5, rtol=0, atol=volume_budget)
    zero = sr.reconstruct_volume(np.zeros_like(images), **args)
    np.testing.assert_array_equal(zero.volume, np.zeros((1, 1, 8)))
    np.testing.assert_array_equal(zero.spectrum, np.zeros((1, 1, 8)))


def test_recombination_window_and_operational_range_before_zero_mask() -> None:
    images = np.ones((1, 7, 1, 1, 4))
    otf = calibration((1, 1, 4))
    args = recombination_args(otf, mask=np.zeros((1, 1, 8)))
    error(
        "invalid_volume_reconstruction_output_shape",
        lambda: sr.reconstruct_volume(
            images, **(cast(Any, args | {"carriers_bins": np.array([[0, 2]])}))
        ),
    )
    # Operational squared transfer overflows despite all-zero data and mask.
    large = calibration((1, 1, 4), np.full((3, 1, 1, 4), np.finfo(float).max, dtype=complex))
    error(
        "unrepresentable_volume_reconstruction",
        lambda: sr.reconstruct_volume(
            np.zeros_like(images), **(cast(Any, args | {"order_otfs": [large]}))
        ),
    )
    # E0=2^-530: E0 squared remains positive subnormal; dc=2^500.
    # U/(V+0) exceeds binary64, so masking to zero cannot rescue it.
    tiny_values = np.zeros((3, 1, 1, 4), dtype=complex)
    tiny_values[0] = 2.0**-530
    tiny = calibration((1, 1, 4), tiny_values)
    error(
        "unrepresentable_volume_reconstruction",
        lambda: sr.reconstruct_volume(
            np.full_like(images, 2.0**500), **(cast(Any, args | {"order_otfs": [tiny]}))
        ),
    )


@pytest.mark.parametrize(
    "field,invalid",
    [
        ("values", np.full((3, 1, 1, 2), complex(np.inf, 0))),
        ("values", np.ones((3, 1, 1, 2), dtype=np.complex64)),
        ("fz_per_um", np.array([1.0])),
        ("fy_per_um", np.array([0], dtype=int)),
        ("fx_per_um", np.array([0.0, -0.5])),
        ("voxel_size_um", (1, True, 1)),
        ("origin_zyx", (0, 0, 2)),
        ("source", " \n"),
    ],
)
def test_all_direct_transfer_fields_validated_by_each_consumer(field: str, invalid: Any) -> None:
    otf = sr.VolumeOrderOtf(**(volume_record_fields(calibration((1, 1, 2))) | {field: invalid}))
    error(
        "invalid_volume_order_gain_otf",
        lambda: sr.estimate_volume_order_gain(
            volume_signal(), order_otf=otf, phase_steps_rad=PHASES, carrier_bins_yx=(0, 0), order=1
        ),
    )
    args = recombination_args(otf)
    error(
        "invalid_volume_reconstruction_otfs",
        lambda: sr.reconstruct_volume(volume_signal()[None], **args),
    )


def test_unused_positive_transfer_row_validation_and_arbitrary_gauge_acceptance() -> None:
    values = np.ones((3, 1, 1, 2), dtype=complex)
    values[0] = 2j
    values[1] = -3 + 2j
    values[2] = 0
    otf = calibration((1, 1, 2), values)
    fit = sr.estimate_volume_order_gain(
        volume_signal(), order_otf=otf, phase_steps_rad=PHASES, carrier_bins_yx=(0, 0), order=1
    )
    assert fit.status == "fitted"
    result = sr.reconstruct_volume(volume_signal()[None], **recombination_args(otf))
    assert np.all(np.isfinite(result.volume.real)) and np.all(np.isfinite(result.volume.imag))
    bad_values = values.copy()
    bad_values[2, 0, 0, 0] = complex(0, np.nan)
    bad = sr.VolumeOrderOtf(**cast(Any, volume_record_fields(otf) | {"values": bad_values}))
    error(
        "invalid_volume_order_gain_otf",
        lambda: sr.estimate_volume_order_gain(
            volume_signal(), order_otf=bad, phase_steps_rad=PHASES, carrier_bins_yx=(0, 0), order=1
        ),
    )


def test_gain_fitted_order_selection_and_zero_information_distinctions() -> None:
    images = (represented_matrix(PHASES) @ np.array([2.0, 2.0, -2.0, -2.0, -1.0]))[
        :, None, None, None
    ]
    matrix = represented_matrix(PHASES)
    coordinates = decimal_fit(matrix, images[:, 0, 0, 0])
    # Independently solved columns of H+ give kappa_2(H) <= ||H||F ||H+||F.
    # The 85-digit observer has ample margin to the informative ceiling of 10.
    left_inverse = np.column_stack([decimal_fit(matrix, column) for column in np.eye(len(PHASES))])
    condition_bound = math.sqrt(
        math.fsum(float(v) ** 2 for v in matrix.flat)
        * math.fsum(float(v) ** 2 for v in left_inverse.flat)
    )
    assert condition_bound < 6 < 10
    b = max(abs(float(value)) for value in images.flat)
    predictor_norm = abs(float(coordinates[0]))  # E1=E2=1; one geometric pair.
    assert predictor_norm > b / 8
    expected_gains = [
        complex(coordinates[2 * order - 1], -coordinates[2 * order]) / (2 * coordinates[0])
        for order in (1, 2)
    ]
    n, m = len(PHASES), math.prod(images.shape[1:])
    delta = 65536 * n * m * EPS
    assert 0 < delta <= 2.0**-10
    assert abs(expected_gains[0] - expected_gains[1]) > 1
    assert abs(expected_gains[1] - expected_gains[0] ** 2) > 0.5
    otf = calibration((1, 1, 1))
    for order in (IntSubclass(1), np.int16(2)):
        expected = expected_gains[order - 1]
        response_norm = (
            math.hypot(float(coordinates[2 * order - 1]), float(coordinates[2 * order])) / 2
        )
        assert response_norm > b / 8  # A0=Am=1 for the supplied unit transfers.
        assert 1.0e-4 < abs(expected) < 10
        # Nonzero scalar x,y have exact amplitude correlation 1 and residual 0.
        assert 1 >= 1 / 4
        gain_budget = delta * max(1.0, abs(expected)) + 8 * float(np.nextafter(0.0, 1.0))
        fit = sr.estimate_volume_order_gain(
            images,
            order_otf=otf,
            phase_steps_rad=PHASES,
            carrier_bins_yx=[IntSubclass(0), np.int64(0)],
            order=order,
        )
        # Analytic singleton overlap: y/x=cm/dc; informative fit has one pair.
        # The nearest zero/half/double/conjugate/squared-order wrong answers
        # lie at least four times this radius away for these declared inputs.
        radius = abs(expected) / 8
        assert abs(fit.gain - expected) < radius
        assert abs(fit.gain - expected) <= gain_budget
        assert fit.status == "fitted" and fit.overlap_count == 1 and fit.order == order
        assert 0.75 < fit.coherence < 1.25
        assert fit.relative_residual < 0.25
        assert abs(fit.coherence - 1.0) <= delta
        assert abs(fit.relative_residual - 0.0) <= delta
        assert type(fit.gain) is complex and type(fit.overlap_count) is int
        with pytest.raises((AttributeError, TypeError)):
            cast(Any, fit).status = "other"
    values = np.ones((3, 1, 1, 1), dtype=complex)
    values[0] = 0
    zero_response = sr.estimate_volume_order_gain(
        images,
        order_otf=calibration((1, 1, 1), values),
        phase_steps_rad=PHASES,
        carrier_bins_yx=(0, 0),
        order=1,
    )
    assert (
        zero_response.gain,
        zero_response.relative_residual,
        zero_response.coherence,
        zero_response.status,
    ) == (0j, 0.0, 0.0, "zero_response")
    values[0], values[1] = 1, 0
    error(
        "unidentifiable_volume_order_gain",
        lambda: sr.estimate_volume_order_gain(
            images,
            order_otf=calibration((1, 1, 1), values),
            phase_steps_rad=PHASES,
            carrier_bins_yx=(0, 0),
            order=1,
        ),
    )
    error(
        "no_volume_order_gain_overlap",
        lambda: sr.estimate_volume_order_gain(
            images, order_otf=otf, phase_steps_rad=PHASES, carrier_bins_yx=(0, 10**100), order=2
        ),
    )
    for carrier in (
        np.array([0, 0], dtype=object),
        [False, 0],
        [0.0, 0],
        np.zeros(2, dtype=int).view(ArraySubclass),
    ):
        error(
            "invalid_volume_order_gain_carrier",
            lambda carrier=carrier: sr.estimate_volume_order_gain(
                images,
                order_otf=otf,
                phase_steps_rad=PHASES,
                carrier_bins_yx=cast(Any, carrier),
                order=1,
            ),
        )
    for order in (True, 1.0, 0, 3):
        error(
            "invalid_volume_order_gain_order",
            lambda order=order: sr.estimate_volume_order_gain(
                images,
                order_otf=otf,
                phase_steps_rad=PHASES,
                carrier_bins_yx=(0, 0),
                order=cast(Any, order),
            ),
        )


def test_gain_exact_orthogonal_cross_weighted_vectors() -> None:
    images = np.stack(
        [
            np.array([1.0, -1.0])[None, None] * v
            for v in (represented_matrix(PHASES) @ np.array([10, 4, 2, 0, 0]))
        ]
    )
    values = np.zeros((3, 1, 1, 2), dtype=complex)
    # Disjoint geometric supports: x only at k=-1, y only at k=0.
    # Add a constant harmonic term so Dm at k=0 is nonzero as well.
    images += (represented_matrix(PHASES) @ np.array([0, 2, 0, 0, 0]))[:, None, None, None]
    values[1, 0, 0, 0] = 1
    values[0, 0, 0, 1] = 1
    fit = sr.estimate_volume_order_gain(
        images,
        order_otf=calibration((1, 1, 2), values),
        phase_steps_rad=PHASES,
        carrier_bins_yx=(0, 0),
        order=1,
    )
    assert (fit.gain, fit.relative_residual, fit.coherence, fit.status) == (
        0j,
        1.0,
        0.0,
        "zero_correlation",
    )


def test_illumination_modulation_above_one_and_scan_exact_candidates() -> None:
    steps = PHASES.copy()
    matrix = represented_matrix(steps)[:, :3]
    assert np.linalg.cond(matrix) < 10
    observations = matrix @ np.array([2, 4, 2], dtype=float)
    images = observations[:, None, None]
    exact = decimal_fit(matrix, observations)
    expected_gain = complex(exact[1], -exact[2]) / (2 * exact[0])
    assert abs(exact[0]) >= max(abs(observations)) / 8
    assert abs(complex(exact[1], -exact[2]) / 2) >= max(abs(observations)) / 8
    otf = image_calibration((1, 1))
    estimate = sr.estimate_illumination(
        images, otf=otf, phase_steps_rad=steps, carrier_bins_yx=(0, 0)
    )
    delta = 8192 * len(steps) * EPS
    actual_gain = (
        0.5
        * estimate.modulation
        * complex(np.cos(estimate.phase_offset_rad), np.sin(estimate.phase_offset_rad))
    )
    assert abs(actual_gain - expected_gain) <= delta * max(1, abs(expected_gain))
    assert estimate.modulation > 1 and estimate.relative_residual <= delta
    corrected = np.cos(estimate.phases_rad) + 1j * np.sin(estimate.phases_rad)
    target = (np.cos(steps) + 1j * np.sin(steps)) * expected_gain / abs(expected_gain)
    np.testing.assert_allclose(corrected, target, rtol=0, atol=4 * delta)
    candidates = np.array([[0, 0], [0, 10**100], [0, 0], [0, -(10**100)]], dtype=object)
    records = sr.scan_carriers(
        images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=candidates
    )
    assert tuple(item.carrier_bins_yx for item in records) == tuple(
        tuple(row) for row in candidates
    )
    assert [item.failure_code for item in records] == [
        None,
        "no_illumination_overlap",
        None,
        "no_illumination_overlap",
    ]
    first, duplicate = records[0].estimate, records[2].estimate
    assert first is not None and duplicate is not None
    owned(first.phases_rad, "float64", steps, images, duplicate.phases_rad)
    first.phases_rad[:] = 0
    assert np.any(duplicate.phases_rad != 0)
    for candidates_bad in (
        [(0, 10**100), (0.5, 0)],
        [(0, 0), (True, 0)],
        np.array([[0, 0]]).view(ArraySubclass),
    ):
        error(
            "invalid_carrier_candidates",
            lambda candidates_bad=candidates_bad: sr.scan_carriers(
                images,
                otf=otf,
                phase_steps_rad=steps,
                candidate_carriers_bins_yx=cast(Any, candidates_bad),
            ),
        )
    all_failed = sr.scan_carriers(
        images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=[(0, 1), (0, -1)]
    )
    assert all(
        item.estimate is None and item.failure_code == "no_illumination_overlap"
        for item in all_failed
    )
    zero_information = sr.scan_carriers(
        np.zeros_like(images),
        otf=otf,
        phase_steps_rad=steps,
        candidate_carriers_bins_yx=[(0, 0), (0, 1)],
    )
    assert [item.failure_code for item in zero_information] == [
        "unidentifiable_illumination",
        "no_illumination_overlap",
    ]
    error(
        "rank_deficient_phases",
        lambda: sr.scan_carriers(
            images,
            otf=otf,
            phase_steps_rad=np.zeros_like(steps),
            candidate_carriers_bins_yx=[(0, 1)],
        ),
    )


@pytest.mark.parametrize(
    "field,bad,code",
    [
        ("values", np.array([[2 + 0j]]), "invalid_illumination_otf"),
        ("values", np.array([[complex(0, np.nan)]]), "invalid_illumination_otf"),
        ("fy_per_um", np.array([1.0]), "incompatible_illumination_otf_grid"),
        ("pixel_size_um", (True, 1), "invalid_illumination_otf"),
        ("origin_yx", (0, 1), "invalid_illumination_otf"),
        ("source", " ", "invalid_illumination_otf"),
    ],
)
def test_illumination_direct_otf_fields_before_no_overlap(field: str, bad: Any, code: str) -> None:
    otf = sr.Otf2D(**(image_record_fields(image_calibration((1, 1))) | {field: bad}))
    error(
        code,
        lambda: sr.estimate_illumination(
            np.ones((7, 1, 1)), otf=otf, phase_steps_rad=PHASES, carrier_bins_yx=(0, 10**100)
        ),
    )
    error(
        code,
        lambda: sr.scan_carriers(
            np.ones((7, 1, 1)),
            otf=otf,
            phase_steps_rad=PHASES,
            candidate_carriers_bins_yx=[(0, 10**100)],
        ),
    )


def file_config(
    *, axes: list[str] | None = None, shape: list[int] | None = None, extension: bool = False
) -> dict[str, Any]:
    return {
        "version": 1,
        "data_kind": "spatial_image",
        "plane_axes": [] if axes is None else axes,
        "plane_shape": [] if shape is None else shape,
        "spatial_fields": "direct_um",
        "extended_header": "opaque" if extension else "none",
        "overrides": {},
    }


@pytest.mark.parametrize("dtype", ["<u2", ">u2", "<f4", ">f4"])
def test_real_file_bigtiff_scalar_bits_and_setting_mapping(tmp_path: Path, dtype: str) -> None:
    import base64
    import hashlib
    import xml.etree.ElementTree as ET

    source = tmp_path / "source.dv"
    if np.dtype(dtype).kind == "u":
        pixels = (np.arange(12, dtype=np.uint16) + 40000).astype(dtype).reshape(2, 2, 3)
    else:
        endian = dtype[0]
        words = np.array(
            [
                0x80000000,
                0x7F800000,
                0xFF800000,
                0x7FC12345,
                0,
                0x3F800000,
                0x7FA12345,
                0xFFC54321,
                0x40000000,
                0x40400000,
                0x40800000,
                0x40A00000,
            ],
            dtype=endian + "u4",
        )
        pixels = words.view(dtype).reshape(2, 2, 3)
    extension = b"opaque\x00\xff" * 7
    original = priism_file(source, pixels, extension=extension)
    config = file_config(axes=["phase", "orientation"], shape=[2, 1], extension=True)
    info = sr.harmonize(sr.inspect(source), config=config)
    destination = tmp_path / "copy.ome.tif"
    report = sr.export_imagej(destination, info, block_planes=1)
    assert destination.read_bytes()[:8] == b"II+\x00\x08\x00\x00\x00"
    assert report.series_count == 2 and report.planes_written == 2
    assert [item.name for item in report.series] == [
        "orientation=0; phase=0",
        "orientation=0; phase=1",
    ]
    assert [item.shape for item in report.series] == [(1, 1, 1, 2, 3)] * 2
    assert all(item.orientation_index == 0 for item in report.series)
    namespace = {"o": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
    with tifffile.TiffFile(destination) as reader:
        assert reader.is_bigtiff and reader.byteorder == "<" and len(reader.pages) == 2
        for page, expected in zip(reader.pages, pixels, strict=True):
            assert int(page.compression) == 1
            kind = "u4" if expected.dtype.kind == "f" else "u2"
            words = expected.view(expected.dtype.byteorder + kind)
            native_words = words.astype(kind)
            assert page.asarray().tobytes() == native_words.tobytes()
        xml = ET.fromstring(cast(Any, reader.pages[0]).description)
        images = xml.findall("o:Image", namespace)
        assert len(images) == 2
        for index, image in enumerate(images):
            assert image.attrib["Name"] == report.series[index].name
            node = image.find("o:Pixels", namespace)
            assert node is not None
            assert node.attrib["DimensionOrder"] == "XYCZT"
            assert [node.attrib["Size" + axis] for axis in "XYZCT"] == ["3", "2", "1", "1", "1"]
            assert (
                float(node.attrib["PhysicalSizeX"]) == 0.25
                and float(node.attrib["PhysicalSizeY"]) == 0.5
            )
            assert "PhysicalSizeZ" not in node.attrib
            mappings = node.findall("o:TiffData", namespace)
            assert len(mappings) == 1 and int(mappings[0].attrib["IFD"]) == index
        values = xml.findall(".//o:MapAnnotation/o:Value/o:M", namespace)
        metadata = [
            json.loads(item.text or "")
            for item in values
            if item.attrib.get("K") == "metadata_json"
        ]
        assert metadata and all(item == metadata[0] for item in metadata)
        document = metadata[0]
        assert document["schema"] == "org.simrecon.imagej-copy"
        assert document["logical_axes"] == ["orientation", "phase", "y", "x"]
        assert document["logical_shape"] == [1, 2, 2, 3]
        assert document["source_identity"]["source_name"] == source.name
        assert str(tmp_path) not in json.dumps(document)
        assert base64.b64decode(document["original_header_base64"]) == original[:1024]
        assert document["original_extension"] == {
            "schema": "opaque",
            "bytes": len(extension),
            "sha256": hashlib.sha256(extension).hexdigest(),
            "content_retained": False,
        }
        assert document["series_layout"]["orientation_present"] is True
        assert document["series_layout"]["z_present"] is False
    assert source.read_bytes() == original


def test_file_precreation_rejections_and_genuine_os_failures(tmp_path: Path) -> None:
    source = tmp_path / "input.dv"
    original = priism_file(source, np.array([[[50000, 3]]], dtype=">u2"))
    inspected = sr.inspect(source)
    info = sr.harmonize(inspected, config=file_config())
    destination = tmp_path / "new.tif"
    error("config_required", lambda: sr.export_imagej(destination, inspected))
    assert not destination.exists()
    for block in (0, -1, True, 1.5):
        error(
            "invalid_block_size",
            lambda block=block: sr.export_imagej(destination, info, block_planes=cast(Any, block)),
        )
        assert not destination.exists()
    for sampling in (1.0e-100, 1.0e100):
        changed = sr.harmonize(
            inspected, config=file_config() | {"overrides": {"sampling_um": {"x": sampling}}}
        )
        error(
            "imagej_unrepresentable",
            lambda changed=changed: sr.export_imagej(destination, cast(Any, changed)),
        )
        assert not destination.exists()
    destination.write_bytes(b"existing marker")
    with pytest.raises(FileExistsError):
        sr.export_imagej(destination, info)
    assert destination.read_bytes() == b"existing marker"
    with pytest.raises(FileExistsError):
        sr.export_imagej(source, info)
    assert source.read_bytes() == original
    with pytest.raises(FileNotFoundError):
        sr.export_imagej(tmp_path / "missing-parent" / "new.tif", info)
    assert source.read_bytes() == original
    alias = tmp_path / "source-alias.tif"
    alias.symlink_to(source)
    with pytest.raises(FileExistsError):
        sr.export_imagej(alias, info)
    assert source.read_bytes() == original
    # A genuine header edit after inspection must reject without creating output.
    altered = bytearray(original)
    altered[300] ^= 1
    source.write_bytes(altered)
    error("source_changed", lambda: sr.export_imagej(tmp_path / "changed.tif", info))
    assert not (tmp_path / "changed.tif").exists() and source.read_bytes() == altered


def test_later_payload_io_failure_preserves_owned_source(tmp_path: Path) -> None:
    import contextlib
    import os
    import signal

    if os.name != "posix":
        pytest.fail("incomplete_io_fixture: POSIX child containment unavailable")
    source = tmp_path / "input.dv"
    original = priism_file(source, np.arange(2 * 256 * 256, dtype=np.uint16).reshape(2, 256, 256))
    destination = tmp_path / "partial.tif"
    probe = tmp_path / "owned_io_probe.py"
    probe.write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, sys.argv[3])\n"
        "from shared_node_baseline_fixture import imagej_write_failure\n"
        "imagej_write_failure(Path(sys.argv[1]), Path(sys.argv[2]), json.loads(sys.argv[4]))\n",
        encoding="utf-8",
    )
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                str(probe),
                str(source),
                str(destination),
                str(ROOT / "tests"),
                json.dumps(file_config(axes=["z"], shape=[2])),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as failure:
        pytest.fail("incomplete_io_fixture: child launch failed: " + type(failure).__name__)
    try:
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                pytest.fail("incomplete_io_fixture: timed-out child cleanup incomplete")
            pytest.fail("incomplete_io_fixture: intervention child timed out")
    finally:
        # Contain the child and workers inheriting its new process group even
        # when the child exits early. No persistent export process is requested.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pytest.fail("incomplete_io_fixture: owned child could not be reaped")
    if process.returncode != 0:
        pytest.fail(f"incomplete_io_fixture: child status={process.returncode}; {stderr}")
    try:
        evidence = json.loads(stdout)
    except json.JSONDecodeError:
        pytest.fail("incomplete_io_fixture: child did not emit a complete evidence document")
    if evidence["classification"] == "incomplete_fixture":
        pytest.fail("incomplete_io_fixture: " + evidence["incomplete_reason"])
    assert evidence["classification"] == "witnessed_expected_failure", (
        "witnessed operation-time outcome failure: " + stdout
    )
    assert evidence["unrestricted_planes"] == 2
    assert evidence["unrestricted_bytes"] > evidence["limit_bytes"] == 65536
    assert evidence["limit_verified"] is True and evidence["sigxfsz_count"] > 0
    assert evidence["export_succeeded"] is False
    assert evidence["failure_is_os_error"] is True and evidence["errno_is_efbig"] is True
    assert evidence["signal_handler_restored"] is True
    assert evidence["limits_restored"] is True and evidence["source_preserved"] is True
    assert source.read_bytes() == original


def child(args: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    """Inherit the source-free Python-child environment; never replace it."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60, check=False)


@pytest.mark.parametrize(
    "body,category",
    [
        ("raise ValueError('ordinary failure')", "ValueError"),
        (
            (
                "try:\n    raise KeyError('first failure')\nexcept KeyError as "
                "cause:\n    raise RuntimeError('second failure') from cause"
            ),
            "RuntimeError",
        ),
        (
            "raise ExceptionGroup('group failure', [ValueError('one'), TypeError('two')])",
            "ExceptionGroup",
        ),
        (
            (
                "raise SyntaxError('invalid syntax', ('owned_syntax.py', 3, 2"
                ", 'HIDDEN_SOURCE_MARKER\\n'))"
            ),
            "SyntaxError",
        ),
        (
            (
                "import subprocess\nraise subprocess.TimeoutExpired(['owned-ex"
                "ecutable', '-c', 'HIDDEN_SOURCE_MARKER'], 0.25)"
            ),
            "TimeoutExpired",
        ),
        (
            (
                "import subprocess\nraise subprocess.CalledProcessError(7, ['o"
                "wned-executable', '-c', 'HIDDEN_SOURCE_MARKER'])"
            ),
            "CalledProcessError",
        ),
        (
            "import subprocess\nraise subprocess.CalledProcessError(7, 'HIDDEN_SOURCE_MARKER')",
            "CalledProcessError",
        ),
    ],
)
def test_source_free_standard_exception_channels(tmp_path: Path, body: str, category: str) -> None:
    probe = tmp_path / "owned_probe.py"
    probe.write_text("hidden_local = 'HIDDEN_SOURCE_MARKER'\n" + body + "\n", encoding="utf-8")
    result = child(
        [sys.executable, str(ROOT / "scripts/source_free_check.py"), "python", str(probe)]
    )
    rendered = result.stdout + result.stderr
    assert result.returncode != 0 and category in rendered
    assert "HIDDEN_SOURCE_MARKER" not in rendered and "hidden_local" not in rendered
    if category in ("CalledProcessError", "TimeoutExpired"):
        assert "owned-executable" in rendered or "not recorded" in rendered.lower(), rendered
    else:
        assert "owned_probe.py" in rendered or "owned_syntax.py" in rendered


def test_source_free_warning_child_and_literal_program_arguments(tmp_path: Path) -> None:
    probe = tmp_path / "warning_probe.py"
    probe.write_text(
        (
            "import warnings, sys\nwarnings.warn('observable warning', Use"
            "rWarning) # HIDDEN_SOURCE_MARKER\nassert sys.argv[1:] == ['-S"
            "', '-I', '-E']\n"
        ),
        encoding="utf-8",
    )
    harness = str(ROOT / "scripts/source_free_check.py")
    result = child([sys.executable, harness, "python", str(probe), "-S", "-I", "-E"])
    assert result.returncode == 0
    assert "observable warning" in result.stderr and "UserWarning" in result.stderr
    assert "warning_probe.py" in result.stderr and "HIDDEN_SOURCE_MARKER" not in result.stderr
    nested = tmp_path / "nested_probe.py"
    nested.write_text(
        (
            "import subprocess, sys\nsubprocess.run([sys.executable, '-c',"
            " \"raise ValueError('child failure') # HIDDEN_SOURCE_MARKER\"]"
            ", check=True)\n"
        ),
        encoding="utf-8",
    )
    outcome = child([sys.executable, harness, "python", str(nested)])
    assert outcome.returncode != 0
    assert "ValueError" in outcome.stderr and "CalledProcessError" in outcome.stderr
    assert "HIDDEN_SOURCE_MARKER" not in outcome.stderr
    for option in ("-I", "-S", "-E", "-IS", "-ES"):
        rejected = child([sys.executable, harness, "python", option, str(probe)])
        assert rejected.returncode != 0
    for duration in ("0", "-1", "nan"):
        rejected = child([sys.executable, harness, "--timeout", duration, "python", str(probe)])
        assert rejected.returncode != 0


def disposable_verifier(
    tmp_path: Path, phase_failure: int = 9, temporal_alias: bool = False
) -> tuple[Path, Path]:
    """Copy runtime opaquely; commands/evidence are independently authored."""
    repo = tmp_path / "repository"
    (repo / "scripts").mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/verify.py", repo / "scripts/verify.py")
    (repo / ".gitignore").write_text("artifacts/\n", encoding="utf-8")
    (repo / "marker.txt").write_bytes(b"unchanged tracked marker\n")
    runner = repo / "owned_make.py"
    runner.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, sys\n"
        "if '--version' in sys.argv:\n    print('GNU Make owned fixture'); sys.exit(0)\n"
        + (
            "phases = ['sync', 'coverage-clean', 'lint', 'format', 'types"
            "', 'tests', 'coverage-combine', 'coverage-json', 'coverage-h"
            "tml', 'coverage-report', 'wheel', 'wheel-import', 'audit']\n"
        )
        + (
            "phase = next(a for a in sys.argv[1:] if a in phases)\nprint('"
            "attempted phase=' + phase, flush=True)\n"
        )
        + (
            (
                "if phase == 'coverage-clean':\n    p=pathlib.Path('artifacts/"
                "verification/custom.json')\n    p.parent.mkdir(parents=True, "
                "exist_ok=True)\n    p.symlink_to(pathlib.Path('marker.txt').r"
                "esolve())\n"
            )
            if temporal_alias
            else ""
        )
        + f"sys.exit({phase_failure} if phase == 'coverage-clean' else 0)\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        [
            "git",
            "-c",
            "user.name=Owned Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "owned fixture",
        ],
    ):
        result = child(list(command), cwd=repo)
        assert result.returncode == 0
    return repo, runner


def test_verifier_genuine_failed_phase_status_order_and_safe_receipt(tmp_path: Path) -> None:
    repo, runner = disposable_verifier(tmp_path)
    result = child(
        [
            sys.executable,
            "scripts/verify.py",
            "--make",
            str(runner),
            "--uv",
            str(Path(sys.executable)),
            "--receipt",
            "artifacts/verification/custom.json",
            "--contract",
            "BASELINE-COMPATIBILITY-01",
        ],
        cwd=repo,
    )
    assert result.returncode == 9, f"status={result.returncode}; {result.stdout}; {result.stderr}"
    receipt = json.loads((repo / "artifacts/verification/custom.json").read_text())
    assert receipt["result"] == "failed" and receipt["schema"] == "org.simrecon.verification"
    assert [phase["name"] for phase in receipt["phases"]] == ["sync", "coverage-clean"]
    assert [phase["returncode"] for phase in receipt["phases"]] == [0, 9]
    for phase in receipt["phases"]:
        assert phase["command"][0] == str(runner)
        assert phase["name"] in phase["command"] and f"UV={sys.executable}" in phase["command"]
        assert (repo / phase["log"]).read_text() == "attempted phase=" + phase["name"] + "\n"
    assert receipt["context"]["contract"] == "BASELINE-COMPATIBILITY-01"
    assert receipt["context"]["reviewed_tests"] is None
    assert receipt["problems"] and receipt["before"]["commit"] == receipt["after"]["commit"]
    assert (repo / "marker.txt").read_bytes() == b"unchanged tracked marker\n"


def test_verifier_phase_introduced_receipt_alias_on_failed_run(tmp_path: Path) -> None:
    repo, runner = disposable_verifier(tmp_path, temporal_alias=True)
    marker = repo / "marker.txt"
    result = child(
        [
            sys.executable,
            "scripts/verify.py",
            "--make",
            str(runner),
            "--receipt",
            "artifacts/verification/custom.json",
        ],
        cwd=repo,
    )
    assert result.returncode != 0
    assert marker.read_bytes() == b"unchanged tracked marker\n"
    assert "attempted phase=coverage-clean" in result.stdout, (
        f"status={result.returncode}; {result.stdout}; {result.stderr}"
    )


@pytest.mark.parametrize("selector", ["otf", "reconstruction"])
def test_reference_selectors_complete_deterministic_stdout_no_files(
    tmp_path: Path, selector: str
) -> None:
    command = [sys.executable, str(ROOT / "scripts/generate_reference_fixtures.py"), selector]
    first = child(command, cwd=tmp_path)
    second = child(command, cwd=tmp_path)
    assert first.returncode == second.returncode == 0
    document = json.loads(first.stdout)
    assert isinstance(document, dict) and document
    assert first.stdout == second.stdout
    assert list(tmp_path.iterdir()) == []
    assert first.stderr == second.stderr == ""
    bad = child(command + ["--scientific-knob", "1"], cwd=tmp_path)
    assert bad.returncode != 0 and list(tmp_path.iterdir()) == []


def test_gain_finite_components_with_overflowing_complex_magnitude() -> None:
    images = (represented_matrix(PHASES) @ np.array([2, 4, 0, 0, 0]))[:, None, None, None]
    f = float(np.finfo(float).max)
    values = np.ones((3, 1, 1, 1), dtype=complex)
    values[0] = complex(0.75 * f, 0.75 * f)
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as emitted:
        mode = np.geterr().copy()
        fit = sr.estimate_volume_order_gain(
            images,
            order_otf=calibration((1, 1, 1), values),
            phase_steps_rad=PHASES,
            carrier_bins_yx=(0, 0),
            order=1,
        )
        assert fit.status == "fitted"
        assert math.isfinite(fit.gain.real) and math.isfinite(fit.gain.imag)
        assert 0.5 * f < fit.gain.real < f and 0.5 * f < fit.gain.imag < f
        assert np.geterr() == mode and not emitted


def test_recombination_all_orders_modular_negation_and_nonwrapping_placement() -> None:
    import itertools

    shape = (1, 2, 2)
    coordinates = np.array(
        [
            [[2.0, -1.0], [3.0, 4.0]],
            [[1.0, 0.0], [-1.0, 2.0]],
            [[0.0, 2.0], [1.0, -1.0]],
            [[-1.0, 1.0], [2.0, 0.0]],
            [[2.0, 0.0], [-1.0, 1.0]],
        ]
    )
    matrix = represented_matrix(PHASES)
    assert np.linalg.cond(matrix) < 10
    images = np.einsum("pa,ayx->pyx", matrix, coordinates)[:, None]
    exact = np.empty((5, *shape))
    for y, x in np.ndindex(2, 2):
        exact[:, 0, y, x] = decimal_fit(matrix, images[:, 0, y, x])
    dc = exact[0]
    c1 = (exact[1] - 1j * exact[2]) / 2
    c2 = (exact[3] - 1j * exact[4]) / 2
    bands = {
        0: finite_dft(dc) / 4,
        1: finite_dft(c1) / 4,
        2: finite_dft(c2) / 4,
        -1: finite_dft(np.conj(c1)) / 4,
        -2: finite_dft(np.conj(c2)) / 4,
    }
    values = np.array(
        [
            [[[0.5 + 0.2j, -0.3j], [0.7, -0.4 + 0.1j]]],
            [[[0.2j, 0.6 - 0.3j], [-0.4 + 0.5j, 0.1]]],
            [[[0.4 - 0.2j, -0.3], [0.1 + 0.6j, 0.2j]]],
        ]
    )
    modes = list(itertools.product(*(signed_modes(n) for n in shape)))
    indices = dict(zip(modes, np.ndindex(shape), strict=True))
    expected = np.zeros((1, 2, 6), dtype=complex)
    for output_index, q in zip(
        np.ndindex(expected.shape),
        itertools.product(*(signed_modes(n) for n in expected.shape)),
        strict=True,
    ):
        numerator, denominator = 0j, 0.5
        for order in range(-2, 3):
            j = (q[0], q[1], q[2] + order)
            if j not in indices:
                continue
            index = indices[j]
            if order >= 0:
                transfer = values[(order, *index)]
            else:
                negated = tuple(((-v + n // 2) % n) - n // 2 for v, n in zip(j, shape, strict=True))
                transfer = np.conj(values[(-order, *indices[negated])])
            numerator += np.conj(transfer) * bands[order][index]
            denominator += transfer.real**2 + transfer.imag**2
        expected[output_index] = 0.6 * numerator / denominator
    volume = np.empty(expected.shape, dtype=complex)
    for position in np.ndindex(volume.shape):
        volume[position] = sum(
            expected[index]
            * np.exp(
                2j
                * np.pi
                * sum(
                    Fraction(k * r, n) for k, r, n in zip(mode, position, volume.shape, strict=True)
                )
            )
            for index, mode in zip(
                np.ndindex(expected.shape),
                itertools.product(*(signed_modes(n) for n in expected.shape)),
                strict=True,
            )
        )
    otf = calibration(shape, values)
    result = sr.reconstruct_volume(
        images[None],
        order_otfs=[otf],
        phases_rad=PHASES[None],
        carriers_bins=np.array([[0, 1]], dtype=np.int16),
        gains=np.ones(1),
        regularization=0.5,
        output_shape_yx=(2, 6),
        apodization=np.full((1, 2, 6), 0.6),
    )
    b = float(np.max(np.abs(images)))
    spectrum_budget = 65536 * 5 * (7 + 4) * EPS * b
    volume_budget = 12 * spectrum_budget + 16384 * 5 * 12 * EPS * b
    np.testing.assert_allclose(result.spectrum, expected, rtol=0, atol=spectrum_budget)
    np.testing.assert_allclose(result.volume, volume, rtol=0, atol=volume_budget)


@pytest.mark.parametrize(
    "name",
    [
        "correct_integer_drift",
        "prepare_empirical_volume_response",
        "correct_linear_response",
        "estimate_translation",
        "prepare_volume_order_otfs",
        "prepare_volume_otf",
        "separate_volume_phases",
        "reconstruct_volume",
        "declare_acquisition",
        "scan_carriers",
        "estimate_illumination",
        "estimate_volume_order_gain",
    ],
)
def test_required_keyword_binding_remains_python_typeerror(name: str) -> None:
    operation = getattr(sr, name)
    with pytest.raises(TypeError):
        operation(np.ones((1, 1, 1)))
    with pytest.raises(TypeError):
        operation(np.ones((1, 1, 1)), unexpected_keyword=0)


def test_imagej_cli_domain_and_io_statuses_preserve_source(tmp_path: Path) -> None:
    source = tmp_path / "input.dv"
    original = priism_file(source, np.ones((1, 2, 3), dtype="<u2"))
    config = tmp_path / "config.json"
    config.write_text(json.dumps(file_config()), encoding="utf-8")
    command = [
        str(ROOT / ".venv/bin/simrecon"),
        "export-imagej",
        str(source),
        str(tmp_path / "absent" / "output.tif"),
        "--config",
        str(config),
    ]
    io_failure = child(command)
    assert io_failure.returncode == 1
    assert json.loads(io_failure.stderr)["code"] == "io_error"
    domain_failure = child(command + ["--block-planes", "0"])
    assert domain_failure.returncode == 2
    assert json.loads(domain_failure.stderr)["code"] == "invalid_block_size"
    assert source.read_bytes() == original


def test_volume_final_coordinate_range_is_not_rank_or_solver_failure() -> None:
    phases = np.arange(7.0) / 10
    matrix = represented_matrix(phases)
    singular = np.linalg.svd(matrix, compute_uv=False)
    assert np.all(singular > EPS * 7 * singular[0])
    normalized = np.array([1.0, -1, 1, -1, 1, -1, 1])
    exact = decimal_fit(matrix, normalized)
    # This is far outside the maximum boundary, not a rounding-edge classifier.
    coordinates = [exact[0], exact[1] / 2, exact[2] / 2, exact[3] / 2, exact[4] / 2]
    assert max(abs(value) for value in coordinates) > 2
    observations = normalized * np.finfo(float).max
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as emitted:
        error(
            "unrepresentable_volume_phase_components",
            lambda: sr.separate_volume_phases(observations[:, None, None, None], phases_rad=phases),
        )
        assert not emitted


def test_imagej_complete_xyzct_and_setting_plane_permutation(tmp_path: Path) -> None:
    source = tmp_path / "all_axes.dv"
    pixels = (np.arange(72 * 2 * 3, dtype=np.uint16) + 40000).reshape(72, 2, 3)
    original = priism_file(source, pixels)
    config = file_config(
        axes=["phase", "z", "time", "channel", "orientation"], shape=[3, 3, 2, 2, 2]
    )
    info = sr.harmonize(sr.inspect(source), config=config)
    destination = tmp_path / "all_axes.tif"
    report = sr.export_imagej(destination, info, block_planes=3)
    assert report.series_count == 6 and report.planes_written == 72
    assert all(series.shape == (2, 2, 3, 2, 3) for series in report.series)
    with tifffile.TiffFile(destination) as reader:
        assert len(reader.pages) == 72
        for orientation in range(2):
            for phase in range(3):
                series = orientation * 3 + phase
                assert report.series[series].name == f"orientation={orientation}; phase={phase}"
                for time in range(2):
                    for z in range(3):
                        for channel in range(2):
                            ordinal = channel + 2 * (z + 3 * time)
                            source_plane = (
                                ((phase * 3 + z) * 2 + time) * 2 + channel
                            ) * 2 + orientation
                            decoded = reader.pages[series * 12 + ordinal].asarray()
                            assert decoded.tobytes() == pixels[source_plane].tobytes()
    assert source.read_bytes() == original
