"""Blind RA07 public-contract tests. Expectations are fixed before product calls.

Each family covers an observable contract decision at the public reconstruction
boundary. Independent fixture checks qualify the custom oracle, not production.
No source inspection, private seam, skipped absence or fixed FFT count is used.
"""

from __future__ import annotations

import copy
import dataclasses
import importlib
import inspect
import math
import warnings
from fractions import Fraction
from typing import Any, cast

import numpy as np
import pytest

from reference_alignment_ra07_fixture import (
    Case,
    allowance,
    analytic_case,
    analytic_volume,
    basis,
    bins,
    csum,
    dense_relocation,
    fit,
    five_phase_case,
    interpolate,
    make_case,
    modes,
    oracle,
    phasor,
    samples,
    signed_transfer,
    transform,
    weights,
)


@pytest.fixture
def public() -> Any:
    return importlib.import_module("simrecon")


@pytest.fixture
def api(public: Any) -> Any:
    # Missing additive API is setup/feature-absence evidence, never numerical red.
    return public.reconstruct_volume_fractional


def frequency(size: int, spacing: float) -> np.ndarray[Any, Any]:
    return np.array([float(Fraction(j, size) / Fraction.from_float(spacing)) for j in bins(size)])


def arguments(case: Case, public: Any) -> dict[str, Any]:
    otfs = []
    for r, values in enumerate(case.transfers):
        otfs.append(
            public.VolumeOrderOtf(
                values=values,
                fz_per_um=frequency(case.native[0], case.spacing[0]),
                fy_per_um=frequency(case.native[1], case.spacing[1]),
                fx_per_um=frequency(case.native[2], case.spacing[2]),
                voxel_size_um=case.spacing,
                origin_zyx=tuple((r + a) % k for a, k in enumerate(case.native)),
                source=f"opaque arbitrary complex row {r}",
            )
        )
    return dict(
        order_otfs=otfs,
        phases_rad=case.phases,
        carriers_per_um=case.carriers,
        gains=case.gains,
        regularization=case.penalty,
        output_shape_yx=case.output_yx,
        apodization=case.taper,
    )


def assert_output_shapes(case: Case, result: Any) -> None:
    assert result.volume.shape == case.output
    assert result.spectrum.shape == case.output
    for name, size in zip(("fz_per_um", "fy_per_um", "fx_per_um"), case.output, strict=True):
        assert getattr(result, name).shape == (size,)


def assert_matches(
    case: Case,
    result: Any,
    expected_s: Any,
    expected_v: Any,
    budget_s: float,
    budget_v: float,
) -> None:
    assert_output_shapes(case, result)
    assert expected_s.shape == case.output and expected_v.shape == case.output
    assert np.max(np.abs(result.spectrum - expected_s)) <= budget_s
    assert np.max(np.abs(result.volume - expected_v)) <= budget_v


def evaluate(case: Case, api: Any, public: Any) -> Any:
    expected_s, expected_v = oracle(case)
    budget_s, budget_v = allowance(case)
    result = api(case.images, **arguments(case, public))
    assert_matches(case, result, expected_s, expected_v, budget_s, budget_v)
    return result


def rejects(
    api: Any,
    public: Any,
    images: Any,
    kwargs: dict[str, Any],
    code: str | frozenset[str],
) -> None:
    before = np.geterr().copy()
    filters = list(warnings.filters)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(public.SimreconError) as error:
            api(images, **kwargs)
    accepted = frozenset((code,)) if isinstance(code, str) else code
    assert error.value.code in accepted
    assert isinstance(error.value, ValueError)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.geterr() == before
    assert warnings.filters == filters


def test_oracle_analytic_offbin_wave_and_wrong_sign_factor() -> None:
    case, amplitude = analytic_case()
    expected = analytic_volume(case, amplitude)
    spectrum, volume = oracle(case)
    assert np.max(np.abs(volume - expected)) < 2e-13
    assert np.max(np.abs(transform(expected, forward=True) - spectrum)) < 2e-13
    assert np.count_nonzero(np.abs(spectrum) > 1e-5) == spectrum.size
    assert np.max(np.abs(expected - analytic_volume(case, amplitude, sign=1))) > 0.1
    assert np.max(np.abs(expected - 2 * expected)) > 0.1
    budget_s, budget_v = allowance(case)
    assert 0 < budget_s < 1e-7
    assert 0 < budget_v < 1e-6


def test_oracle_phase_projection_uses_stored_matrix() -> None:
    case = make_case()
    h = basis(case.phases[0])
    dc, c1, c2 = fit(case.images[0], case.phases[0])
    coordinates = np.array([dc.real, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag]).reshape(
        5, -1
    )
    residual = case.images[0].reshape(7, -1) - h @ coordinates
    assert np.max(np.abs(h.T @ residual)) < 1e-13
    assert np.max(np.abs(residual)) > 1e-3
    assert np.max(np.abs(dc.real - np.mean(case.images[0], axis=0))) > 0.01
    permutation = np.array([6, 0, 3, 1, 5, 2, 4])
    for original, permuted in zip(
        fit(case.images[0], case.phases[0]),
        fit(case.images[0, permutation], case.phases[0, permutation]),
        strict=True,
    ):
        assert np.max(np.abs(original - permuted)) < 2e-15


def test_oracle_five_exposures_have_full_rank_and_stored_input_budget() -> None:
    case = five_phase_case()
    h = basis(case.phases[0])
    assert h.shape == (5, 5) and np.linalg.matrix_rank(h) == 5
    assert 7.0 < np.linalg.cond(h) < 7.1
    dc, c1, c2 = fit(case.images[0], case.phases[0])
    coordinates = np.array([dc.real, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag])
    assert np.max(np.abs(h @ coordinates.reshape(5, -1) - case.images[0].reshape(5, -1))) < 1e-13
    assert case.images.shape == (1, 5, 1, 1, 1)
    assert case.images.size <= 512 and math.prod(case.output) <= 512
    assert np.max(np.abs(case.images)) <= 16
    assert np.all((case.gains >= 0.5) & (case.gains <= 2))
    assert all(np.max(np.abs(e.real)) <= 1 and np.max(np.abs(e.imag)) <= 1 for e in case.transfers)
    assert 0 <= case.penalty <= 1 and weights(case)[1] >= 1 / 16
    expected_s, expected_v = oracle(case)
    assert expected_s.shape == case.output and expected_v.shape == case.output
    bs, bv = allowance(case)
    assert 0 < bs < 1e-7 and 0 < bv < 1e-6


def test_five_exposures_stored_input_estimator(api: Any, public: Any) -> None:
    # Exact N=5 endpoint; oracle/budget are computed before the public call.
    evaluate(five_phase_case(), api, public)


def test_oracle_complex_interpolation_modular_reflection_and_closed_hull() -> None:
    grid = (np.arange(12).reshape(2, 2, 3) + 1j * np.arange(12, 24).reshape(2, 2, 3)).astype(
        np.complex128
    )
    point = (Fraction(-1, 2), Fraction(-1, 4), Fraction(1, 2))
    expected = csum(
        [
            complex(grid[z, y, x]) * wz * wy * wx
            for z, wz in [(0, 0.5), (1, 0.5)]
            for y, wy in [(0, 0.25), (1, 0.75)]
            for x, wx in [(1, 0.5), (2, 0.5)]
        ]
    )
    assert interpolate(grid, point) == expected
    assert interpolate(grid, (Fraction(-1), Fraction(-1), Fraction(-1))) == grid[0, 0, 0]
    assert interpolate(grid, (Fraction(0), Fraction(0), Fraction(1))) == grid[-1, -1, -1]
    assert interpolate(grid, (Fraction(1, 1000), Fraction(0), Fraction(0))) is None
    singleton = np.array([[[1 + 2j]]])
    assert interpolate(singleton, (Fraction(0),) * 3) == 1 + 2j
    assert interpolate(singleton, (Fraction(0), Fraction(0), Fraction(1, 10**30))) is None
    rows = np.array([grid, grid * (1 + 1j), grid * (2 - 1j)])
    neg = signed_transfer(rows, -1)
    # Even z/y Nyquist reflects to itself; x=-1 reflects to x=+1.
    assert neg[0, 0, 0] == rows[1, 0, 0, 2].conjugate()
    assert neg[1, 1, 1] == rows[1, 1, 1, 1].conjugate()
    assert not np.array_equal(neg, rows[1, ::-1, ::-1, ::-1].conjugate())


def test_oracle_dense_synthesis_adjoint_and_filter_order_discrimination() -> None:
    case = make_case((1, 2, 2), output_yx=(4, 4))
    ws, _ = weights(case)
    bands = [fit(b, p) for b, p in zip(case.images, case.phases, strict=True)]
    total = np.zeros(math.prod(case.output), dtype=np.complex128)
    numerator = np.zeros_like(total)
    for r, m, w in ws:
        spatial = bands[r][abs(m)] if m >= 0 else bands[r][-m].conjugate()
        d = transform(spatial, forward=True).ravel()
        matrix = dense_relocation(case, r, m)
        total += matrix @ (w.ravel() * d)
        t = case.gains[r] * signed_transfer(case.transfers[r], m)
        numerator += matrix @ (t.conjugate().ravel() * d)
        # Arbitrary complex signed-boundary probes; no public adjoint export.
        x = np.array([complex(0.13 + i * 0.07, -0.19 + i * 0.03) for i in range(d.size)])
        y = np.array([complex(0.17 - i * 0.009, 0.11 + i * 0.005) for i in range(total.size)])
        y *= case.taper.ravel()
        synth_y = transform(y.reshape(case.output), forward=False).ravel() / y.size
        cy, cx = case.shifts[r]
        adjoint = (
            np.array(
                [
                    csum(
                        [
                            complex(v)
                            * phasor(
                                -Fraction(j[0] * n[0], case.output[0])
                                - (j[1] - m * cy) * Fraction(n[1], case.output[1])
                                - (j[2] - m * cx) * Fraction(n[2], case.output[2])
                            )
                            for n, v in zip(samples(case.output), synth_y, strict=True)
                        ]
                    )
                    for j in modes(case.native)
                ]
            )
            * w.conjugate().ravel()
        )
        assert abs(np.vdot(matrix @ (w.ravel() * x), y) - np.vdot(x, adjoint)) < 2e-13
    expected_s, _ = oracle(case)
    assert np.max(np.abs(total.reshape(case.output) * case.taper - expected_s)) < 2e-13
    # Plausible wrong filter-after-relocation: native numerator relocated, then
    # divide at output integer q by the continuous transfer denominator.
    after = []
    for q, value in zip(modes(case.output), numerator, strict=True):
        denominator = case.penalty
        for r, m, _ in ws:
            cy, cx = case.shifts[r]
            e = interpolate(
                signed_transfer(case.transfers[r], m),
                (Fraction(q[0]), Fraction(q[1]) + m * cy, Fraction(q[2]) + m * cx),
            )
            if e is not None:
                denominator += abs(case.gains[r] * e) ** 2
        after.append(value / denominator)
    wrong = np.array(after).reshape(case.output) * case.taper
    margin = float(np.max(np.abs(wrong - expected_s)))
    assert margin > 1e-3
    assert margin > 1000 * allowance(case)[0]


def test_public_required_bindings_and_existing_exports(public: Any) -> None:
    fn = public.reconstruct_volume_fractional
    assert callable(public.reconstruct_volume)
    assert callable(public.reconstruct_volume_weighted)
    signature = inspect.signature(fn)
    assert tuple(signature.parameters) == (
        "images",
        "order_otfs",
        "phases_rad",
        "carriers_per_um",
        "gains",
        "regularization",
        "output_shape_yx",
        "apodization",
    )
    for name, parameter in signature.parameters.items():
        assert parameter.default is inspect.Parameter.empty
        if name != "images":
            assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        fn()
    with pytest.raises(TypeError):
        fn(np.zeros((1, 7, 1, 1, 1)), None)


@pytest.mark.parametrize(
    "native,out",
    [((2, 2, 3), (4, 5)), ((3, 3, 2), (5, 4)), ((1, 1, 1), (3, 3)), ((1, 3, 4), (5, 6))],
)
def test_stored_input_direct_estimator_complex_anisotropic(
    api: Any, public: Any, native: tuple[int, int, int], out: tuple[int, int]
) -> None:
    case = make_case(native, output_yx=out)
    # F05: true N>5 off-model input. F06/07: unequal orientations, gains,
    # asymmetric complex transfer, even modular endpoints and anisotropic units.
    result = evaluate(case, api, public)
    assert np.max(np.abs(result.volume.imag)) > 1e-4
    permutation = np.array([5, 0, 6, 2, 4, 1, 3])
    case.images = case.images[:, permutation]
    case.phases = case.phases[:, permutation]
    again = evaluate(case, api, public)
    assert np.max(np.abs(again.volume - result.volume)) <= 2 * allowance(case)[1]


def test_analytic_negative_fractional_order_two_full_tails_and_origin(
    api: Any, public: Any
) -> None:
    case, amplitude = analytic_case()
    expected = analytic_volume(case, amplitude)
    result = evaluate(case, api, public)
    assert np.max(np.abs(result.volume - expected)) < 2e-10
    assert abs(result.volume[0, 0, 0] - 2 * amplitude.real) < 2e-10
    assert np.count_nonzero(np.abs(result.spectrum) > 1e-5) == result.spectrum.size


@pytest.mark.parametrize("carrier", [(0.0, 0.0), (-1.0, 0.0), (0.0, 1.0)])
def test_exact_integer_limit_and_complex_nyquist(
    api: Any, public: Any, carrier: tuple[float, float]
) -> None:
    case = make_case((1, 2, 4), orientations=1, output_yx=(6, 8), off_model=False)
    case.spacing = (0.75, 0.5, 1.0)
    case.carriers[0] = [
        carrier[0] / (case.native[1] * case.spacing[1]),
        carrier[1] / (case.native[2] * case.spacing[2]),
    ]
    assert all(c.denominator == 1 for c in case.shifts[0])
    kwargs = arguments(case, public)
    integer_kwargs = kwargs.copy()
    integer_kwargs.pop("carriers_per_um")
    integer_kwargs["carriers_bins"] = np.array([carrier], dtype=np.int64)
    result = evaluate(case, api, public)
    previous = public.reconstruct_volume(case.images, **integer_kwargs)
    assert_output_shapes(case, previous)
    bs, bv = allowance(case)
    assert np.max(np.abs(result.spectrum - previous.spectrum)) <= 2 * bs
    assert np.max(np.abs(result.volume - previous.volume)) <= 2 * bv
    if carrier == (0.0, 0.0):
        case.gains[:] = 1
        case.transfers[0][:] = 0
        case.transfers[0][0] = 1
        case.images[:] = np.array([1.0, -1.0, 1.0, -1.0])
        case.penalty = 0
        case.taper[:] = 1
        # Unit gain/transfer and zero lambda give Q(kx=-2)=1.
        expected = np.broadcast_to(
            np.array([phasor(Fraction(-2 * x, 8)) for x in range(8)]), case.output
        )
        nyquist = api(case.images, **arguments(case, public))
        assert_output_shapes(case, nyquist)
        assert np.max(np.abs(nyquist.volume - expected)) < 2e-10
        assert np.max(np.abs(nyquist.volume.imag)) > 0.99


def test_exact_geometry_no_tolerance_snapping_and_zero_guard(api: Any, public: Any) -> None:
    case = make_case((1, 2, 1), orientations=1, output_yx=(6, 1))
    case.images[:] = 0
    case.transfers[0][:] = 0
    case.taper[:] = 0
    case.carriers[:] = [np.nextafter(1.0, math.inf), 0.0]
    assert case.shifts[0][0] > 1
    rejects(
        api,
        public,
        case.images,
        arguments(case, public),
        "invalid_volume_reconstruction_output_shape",
    )
    case.output_yx = (7, 1)
    case.taper = np.zeros(case.output)
    # The size inequality passes at seven, but the lower native even endpoint
    # is just below -3, so the separate closed-anchor guard still rejects.
    rejects(
        api,
        public,
        case.images,
        arguments(case, public),
        "invalid_volume_reconstruction_output_shape",
    )
    case.output_yx = (8, 1)
    case.taper = np.zeros(case.output)
    result = api(case.images, **arguments(case, public))
    assert_output_shapes(case, result)
    assert np.array_equal(result.volume, np.zeros(case.output))
    # Rounded multiplication is exactly 1, but converted rational product >1.
    case.spacing = (0.75, 0.1, 1.25)
    case.carriers[:] = [5.0, 0.0]
    assert 2 * case.spacing[1] * case.carriers[0, 0] == 1.0
    assert case.shifts[0][0] > 1
    case.output_yx = (6, 1)
    case.taper = np.zeros(case.output)
    rejects(
        api,
        public,
        case.images,
        arguments(case, public),
        "invalid_volume_reconstruction_output_shape",
    )


@pytest.mark.parametrize(
    "kind",
    [
        "zero-images",
        "zero-transfers",
        "zero-taper",
        "zero-lambda",
        "repeated-carrier",
        "huge-phases",
    ],
)
def test_permitted_zero_and_nonunit_choices(api: Any, public: Any, kind: str) -> None:
    case = make_case()
    if kind == "zero-images":
        case.images[:] = 0
    elif kind == "zero-transfers":
        for e in case.transfers:
            e[:] = 0
        case.penalty = 0
    elif kind == "zero-taper":
        case.taper[:] = 0
    elif kind == "zero-lambda":
        case.penalty = 0
    elif kind == "repeated-carrier":
        case.carriers[:] = case.carriers[0]
    else:
        case.phases[:] = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, np.finfo(float).max])
        assert np.linalg.cond(basis(case.phases[0])) < 10
    result = evaluate(case, api, public)
    if kind in ("zero-images", "zero-transfers", "zero-taper"):
        assert np.array_equal(result.volume, np.zeros(case.output))
        assert np.array_equal(result.spectrum, np.zeros(case.output))


@pytest.mark.parametrize(
    "dtype", [np.int8, np.uint16, np.float16, np.float32, np.float64, np.longdouble, ">f8"]
)
def test_valid_widths_endian_and_conversion(api: Any, public: Any, dtype: Any) -> None:
    case = make_case()
    case.images = case.images.astype(dtype)
    case.phases = case.phases.astype(dtype)
    case.gains = np.array([1, 2], dtype=dtype)
    case.carriers = case.carriers.astype(dtype)
    # UInt/small integer phases remain full rank here. Conversion defines data.
    case.images = case.images.astype(np.float64)
    case.phases = case.phases.astype(np.float64)
    case.gains = case.gains.astype(np.float64)
    case.carriers = case.carriers.astype(np.float64)
    expected_s, expected_v = oracle(case)
    bs, bv = allowance(case)
    kwargs = arguments(case, public)
    for key in ("phases_rad", "gains", "carriers_per_um", "apodization"):
        if key != "apodization":
            kwargs[key] = kwargs[key].astype(dtype)
    result = api(case.images.astype(dtype), **kwargs)
    assert_matches(case, result, expected_s, expected_v, bs, bv)


def test_readonly_strided_fortran_inputs_and_output_record(api: Any, public: Any) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    arrays = [
        case.images,
        *[kwargs[key] for key in ("phases_rad", "gains", "carriers_per_um", "apodization")],
    ]
    replacement = []
    for value in arrays:
        backing = np.empty((*value.shape[:-1], 2 * value.shape[-1]), dtype=value.dtype)
        view = backing[..., ::2]
        view[:] = value
        view.flags.writeable = False
        replacement.append(view)
    images = replacement[0]
    for key, value in zip(
        ("phases_rad", "gains", "carriers_per_um", "apodization"), replacement[1:], strict=True
    ):
        kwargs[key] = value
    for index, record in enumerate(kwargs["order_otfs"]):
        changes = {
            name: np.asfortranarray(
                getattr(record, name).astype(">c16" if name == "values" else ">f8")
            )
            for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
        }
        for value in changes.values():
            value.flags.writeable = False
        kwargs["order_otfs"][index] = dataclasses.replace(record, **changes)
    input_arrays = replacement + [
        getattr(record, name)
        for record in kwargs["order_otfs"]
        for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
    ]
    snapshots = [(a.copy(), a.strides, a.flags.writeable) for a in input_arrays]
    expected_s, expected_v = oracle(case)
    result = api(images, **kwargs)
    bs, bv = allowance(case)
    assert_matches(case, result, expected_s, expected_v, bs, bv)
    fields = ("volume", "spectrum", "fz_per_um", "fy_per_um", "fx_per_um", "voxel_size_um")
    assert tuple(f.name for f in dataclasses.fields(result)) == fields
    assert isinstance(result, public.Reconstruction3D)
    outputs = [getattr(result, name) for name in fields[:-1]]
    repeat = api(images, **kwargs)
    assert_output_shapes(case, repeat)
    for i, (name, value) in enumerate(zip(fields[:-1], outputs, strict=True)):
        assert value.dtype == (np.dtype(np.complex128) if i < 2 else np.dtype(np.float64))
        assert (
            value.dtype.isnative
            and value.flags.owndata
            and value.flags.c_contiguous
            and value.flags.writeable
        )
        assert not any(np.shares_memory(value, a) for a in input_arrays + outputs[:i])
        assert not np.shares_memory(value, getattr(repeat, name))
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, value)
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, name)
    outputs[0].flat[0] = 12 + 3j
    assert repeat.volume.flat[0] != 12 + 3j
    with pytest.raises((AttributeError, TypeError)):
        result.voxel_size_um = (1.0, 1.0, 1.0)
    for a, (saved, strides, writable) in zip(input_arrays, snapshots, strict=True):
        assert np.array_equal(a, saved) and a.strides == strides and a.flags.writeable == writable
    expected_spacing = (
        case.spacing[0],
        float(Fraction(case.native[1]) * Fraction.from_float(case.spacing[1]) / case.output_yx[0]),
        float(Fraction(case.native[2]) * Fraction.from_float(case.spacing[2]) / case.output_yx[1]),
    )
    assert result.voxel_size_um == expected_spacing
    for k, d, length, returned in zip(
        case.native,
        case.spacing,
        case.output,
        (result.fz_per_um, result.fy_per_um, result.fx_per_um),
        strict=True,
    ):
        assert returned.shape == (length,)
        for j, value in zip(bins(length), returned, strict=True):
            exact = Fraction(j, k) / Fraction.from_float(d)
            error = abs(Fraction.from_float(float(value)) - exact)
            budget = 8 * Fraction(1, 2**52) * abs(exact) + Fraction(1, 2**1074)
            assert error <= budget
        assert returned[length // 2] == 0
        assert np.all(np.diff(returned) > 0)


class ArraySubclass(np.ndarray):
    """Supply a rejected ndarray subclass through public argument binding."""


def invalid_array(kind: str, original: np.ndarray[Any, Any]) -> Any:
    if kind == "list":
        return original.tolist()
    if kind == "subclass":
        return original.view(ArraySubclass)
    if kind == "masked":
        return np.ma.array(original)
    if kind == "bool":
        return original.astype(bool)
    if kind == "complex":
        return original.astype(np.complex128)
    if kind == "object":
        return original.astype(object)
    if kind == "shape":
        return original[..., None]
    bad = original.copy()
    bad.flat[0] = {"nan": np.nan, "inf": np.inf, "negative": -1.0, "zero": 0.0, "above": 1.01}[kind]
    return bad


@pytest.mark.parametrize(
    "field,representation_code,value_code",
    [
        (
            "images",
            "invalid_volume_reconstruction_images",
            "nonfinite_volume_reconstruction_images",
        ),
        (
            "phases_rad",
            "invalid_volume_reconstruction_phases",
            "nonfinite_volume_reconstruction_phases",
        ),
        (
            "gains",
            "invalid_volume_reconstruction_gains",
            "invalid_volume_reconstruction_gain_values",
        ),
        (
            "carriers_per_um",
            "invalid_fractional_volume_carriers",
            "invalid_fractional_volume_carriers",
        ),
        (
            "apodization",
            "invalid_volume_reconstruction_apodization",
            "invalid_volume_reconstruction_apodization_values",
        ),
    ],
)
@pytest.mark.parametrize(
    "kind", ["list", "subclass", "masked", "bool", "complex", "object", "shape", "nan", "inf"]
)
def test_inherited_array_decisions(
    api: Any, public: Any, field: str, representation_code: str, value_code: str, kind: str
) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    images = case.images
    original = images if field == "images" else kwargs[field]
    value = invalid_array(kind, original)
    code: str | frozenset[str] = value_code if kind in ("nan", "inf") else representation_code
    if field == "images":
        images = value
        if kind in ("bool", "complex", "object"):
            code = "invalid_volume_reconstruction_dtype"
        elif kind == "shape":
            # A six-dimensional image cannot have a valid three-spatial-axis
            # calibration. Neither simultaneous-error precedence is selected.
            code = frozenset(
                ("invalid_volume_reconstruction_shape", "invalid_volume_reconstruction_otfs")
            )
    else:
        kwargs[field] = value
    rejects(api, public, images, kwargs, code)


@pytest.mark.parametrize(
    "field,kind,code",
    [
        ("gains", "zero", "invalid_volume_reconstruction_gain_values"),
        ("gains", "negative", "invalid_volume_reconstruction_gain_values"),
        ("apodization", "negative", "invalid_volume_reconstruction_apodization_values"),
        ("apodization", "above", "invalid_volume_reconstruction_apodization_values"),
    ],
)
def test_value_boundaries(api: Any, public: Any, field: str, kind: str, code: str) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    kwargs[field] = invalid_array(kind, kwargs[field])
    rejects(api, public, case.images, kwargs, code)


@pytest.mark.parametrize(
    "shape", [(0, 7, 1, 1, 1), (1, 4, 1, 1, 1), (1, 7, 0, 1, 1), (1, 7, 1, 0, 1), (1, 7, 1, 1, 0)]
)
def test_image_dimension_decisions(api: Any, public: Any, shape: tuple[int, ...]) -> None:
    # Match every representable companion dimension. Zero-length native axes
    # cannot have valid calibration nodes/origin; N<5 cannot supply valid
    # five-column separation. Accept the remaining simultaneous input errors.
    native = tuple(max(k, 1) for k in shape[2:])
    case = make_case(cast(tuple[int, int, int], native), orientations=1, output_yx=(3, 3))
    case.carriers[:] = 0
    kwargs = arguments(case, public)
    kwargs["apodization"] = np.zeros((shape[2], *case.output_yx))
    codes = {"invalid_volume_reconstruction_shape"}
    if shape[0] == 0:
        # Nonempty peers conflict with R=0 in exactly these public shapes.
        codes.update(
            (
                "invalid_volume_reconstruction_phases",
                "invalid_volume_reconstruction_gains",
                "invalid_fractional_volume_carriers",
                "invalid_volume_reconstruction_otfs",
            )
        )
    if shape[1] < 5:
        # Keep the valid seven-angle vector; its count conflicts with N=4.
        codes.add("invalid_volume_reconstruction_phases")
    if 0 in shape[2:]:
        codes.update(
            (
                "invalid_volume_reconstruction_otfs",
                "invalid_volume_phase_shape",
                "unrepresentable_volume_reconstruction_grid",
            )
        )
    rejects(api, public, np.zeros(shape), kwargs, frozenset(codes))


@pytest.mark.parametrize("penalty", [True, 1j, [], np.array(0.1), -1.0, math.nan, math.inf])
def test_regularization_decisions(api: Any, public: Any, penalty: Any) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    kwargs["regularization"] = penalty
    rejects(api, public, case.images, kwargs, "invalid_volume_reconstruction_regularization")


@pytest.mark.parametrize(
    "shape,mask_yx",
    [
        ((True, 5), (1, 5)),
        ((4.0, 5), (4, 5)),
        (np.array([4, 5]), (4, 5)),
        ((4,), None),
        ((0, 5), (0, 5)),
        ((-1, 5), None),
        ((3, 5), (3, 5)),
        ((4, 4), (4, 4)),
        ((int(np.iinfo(np.intp).max) + 1, 5), None),
    ],
)
def test_output_window_grammar_and_each_axis_guard(
    api: Any,
    public: Any,
    shape: Any,
    mask_yx: tuple[int, int] | None,
) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    kwargs["output_shape_yx"] = shape
    if mask_yx is not None:
        kwargs["apodization"] = np.zeros((case.native[0], *mask_yx))
    # Guard errors must survive zero observations, transfers and taper.
    case.images[:] = 0
    for e in case.transfers:
        e[:] = 0
    case.taper[:] = 0
    codes = {"invalid_volume_reconstruction_output_shape"}
    if mask_yx is None and len(shape) == 2:
        # Negative or unrepresentable dimensions cannot have a matching ndarray.
        codes.add("invalid_volume_reconstruction_apodization")
    rejects(api, public, case.images, kwargs, frozenset(codes))


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "  "),
        ("source", 3),
        ("voxel_size_um", (True, 0.5, 1.25)),
        ("voxel_size_um", (0.75, 0.0, 1.25)),
        ("voxel_size_um", (0.75, math.inf, 1.25)),
        ("voxel_size_um", np.ones(3)),
        ("origin_zyx", (0, 0, 3)),
        ("origin_zyx", (0, 0, 1.0)),
        ("origin_zyx", (False, 0, 0)),
        ("values", np.zeros((3, 2, 2, 3), dtype=np.complex64)),
        ("values", np.zeros((2, 2, 2, 3), dtype=np.complex128)),
        ("values", np.full((3, 2, 2, 3), complex(math.nan, 0))),
        ("values", np.full((3, 2, 2, 3), complex(0, math.inf))),
        ("fz_per_um", np.array([0.0, 1.0])),
        ("fy_per_um", np.array([0.0, -1.0])),
        ("fx_per_um", np.array([-1.0, 0.0, 1.0], dtype=np.float32)),
        ("fx_per_um", np.array([-1.0, 0.0, 1.0])),
        ("fx_per_um", np.array([-0.2, 0.0, math.inf])),
    ],
)
def test_direct_transfer_field_validation_even_when_ineffective(
    api: Any, public: Any, field: str, value: Any
) -> None:
    case = make_case()
    case.images[:] = 0
    case.taper[:] = 0
    kwargs = arguments(case, public)
    kwargs["order_otfs"][0] = dataclasses.replace(kwargs["order_otfs"][0], **{field: value})
    rejects(api, public, case.images, kwargs, "invalid_volume_reconstruction_otfs")


@pytest.mark.parametrize("kind", ["noncontainer", "count", "type", "spacing-mismatch", "rank"])
def test_otf_container_spacing_and_phase_rank(api: Any, public: Any, kind: str) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    code = "invalid_volume_reconstruction_otfs"
    if kind == "noncontainer":
        kwargs["order_otfs"] = iter(kwargs["order_otfs"])
    elif kind == "count":
        kwargs["order_otfs"] = kwargs["order_otfs"][:1]
    elif kind == "type":
        kwargs["order_otfs"][0] = object()
    elif kind == "spacing-mismatch":
        second = kwargs["order_otfs"][1]
        spacing = (0.5, 0.5, 1.25)
        kwargs["order_otfs"][1] = dataclasses.replace(
            second, voxel_size_um=spacing, fz_per_um=frequency(2, 0.5)
        )
    else:
        kwargs["phases_rad"] = np.zeros_like(case.phases)
        code = "rank_deficient_volume_phases"
    rejects(api, public, case.images, kwargs, code)


def test_output_grid_underflow_and_large_finite_geometry(api: Any, public: Any) -> None:
    case = make_case((1, 1, 1), orientations=1, output_yx=(3, 3))
    case.carriers[:] = 0
    case.spacing = (1.0, np.nextafter(0.0, 1.0), 1.0)
    rejects(
        api,
        public,
        case.images,
        arguments(case, public),
        "unrepresentable_volume_reconstruction_grid",
    )
    case.spacing = (1.0, np.finfo(float).max, 1.0)
    evaluate(case, api, public)


@pytest.mark.parametrize("stage", ["gain", "square", "H-sum", "denominator", "quotient"])
def test_operational_range_not_rescued_by_zero_taper(api: Any, public: Any, stage: str) -> None:
    case = make_case((1, 1, 1), orientations=1, output_yx=(1, 1))
    case.carriers[:] = 0
    case.taper[:] = 0
    case.gains[:] = 1
    case.penalty = 0
    if stage == "gain":
        case.transfers[0][:] = 1e308
        case.gains[:] = 2
    elif stage == "square":
        case.transfers[0][:] = 1e160
    elif stage == "H-sum":
        case.transfers[0][:] = 8e153
    elif stage == "denominator":
        case.transfers[0][:] = 0
        case.transfers[0][0] = 1e154
        case.penalty = np.finfo(float).max
    else:
        case.transfers[0][:] = 0
        case.transfers[0][0] = 1e-154
        case.images[:] = 1e155
    old = np.seterr(all="raise")
    try:
        rejects(
            api,
            public,
            case.images,
            arguments(case, public),
            "unrepresentable_volume_reconstruction",
        )
        assert np.geterr() == dict.fromkeys(("divide", "over", "under", "invalid"), "raise")
    finally:
        np.seterr(**old)


def test_safe_scaled_transform_large_dc_and_exact_zero(api: Any, public: Any) -> None:
    case = make_case((1, 2, 4), orientations=1, output_yx=(4, 8))
    case.carriers[:] = 0
    case.gains[:] = 1
    case.transfers[0][:] = 0
    case.transfers[0][0] = 1
    case.penalty = 0
    case.taper[:] = 1
    amplitude = np.finfo(float).max / 2
    case.images[:] = amplitude
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = api(case.images, **arguments(case, public))
    assert_output_shapes(case, result)
    assert np.all(np.isfinite(result.volume))
    assert np.max(np.abs(result.volume.real / amplitude - 1)) < 1e-10
    assert np.max(np.abs(result.volume.imag / amplitude)) < 1e-10
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    case.images[:] = 0
    result = api(case.images, **arguments(case, public))
    assert_output_shapes(case, result)
    assert np.array_equal(result.volume, np.zeros(case.output))
    assert np.array_equal(result.spectrum, np.zeros(case.output))


@pytest.mark.parametrize(
    "failure,code",
    [
        (FloatingPointError, "volume_reconstruction_transform_failure"),
        (OverflowError, "volume_reconstruction_transform_failure"),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
        (MemoryError, None),
    ],
)
def test_transform_failure_scope_without_call_count_assumption(
    api: Any,
    public: Any,
    monkeypatch: pytest.MonkeyPatch,
    failure: type[Exception],
    code: str | None,
) -> None:
    case = make_case()
    expected_s, expected_v = oracle(case)
    bs, bv = allowance(case)
    touched = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        touched.append(True)
        raise failure("RA07 dependency failure")

    monkeypatch.setattr(np.fft, "fftn", fail)
    monkeypatch.setattr(np.fft, "ifftn", fail)
    try:
        result = api(case.images, **arguments(case, public))
    except Exception as error:
        assert touched
        if code is None:
            assert type(error) is failure
        else:
            assert isinstance(error, public.SimreconError) and cast(Any, error).code == code
    else:
        # Direct finite sums are explicitly permitted and use no FFT dependency.
        assert not touched
        assert_matches(case, result, expected_s, expected_v, bs, bv)


@pytest.mark.parametrize("event", ["runtime-warning", "nonfinite", "unrelated-warning"])
def test_transform_warning_policy_and_nonfinite(
    api: Any, public: Any, monkeypatch: pytest.MonkeyPatch, event: str
) -> None:
    case = make_case()
    original = np.fft.fftn
    touched = []

    def injected(*args: Any, **kwargs: Any) -> Any:
        touched.append(True)
        if event == "runtime-warning":
            warnings.warn("RA07 numerical dependency warning", RuntimeWarning, stacklevel=2)
        if event == "unrelated-warning":
            warnings.warn("RA07 unrelated warning", UserWarning, stacklevel=2)
        output = original(*args, **kwargs)
        if event == "nonfinite":
            output = np.full_like(output, complex(math.nan, 0))
        return output

    monkeypatch.setattr(np.fft, "fftn", injected)
    before = np.geterr().copy()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("ignore", RuntimeWarning)
        warnings.simplefilter("always", UserWarning)
        try:
            result = api(case.images, **arguments(case, public))
        except public.SimreconError as error:
            assert touched and event != "unrelated-warning"
            assert error.code == "volume_reconstruction_transform_failure"
        else:
            assert_output_shapes(case, result)
            if touched:
                assert event == "unrelated-warning"
                assert any(issubclass(w.category, UserWarning) for w in caught)
            assert np.all(np.isfinite(result.volume))
        assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.geterr() == before


def test_input_preservation_on_rejection(api: Any, public: Any) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    kwargs["regularization"] = -1.0
    arrays = [case.images, case.phases, case.carriers, case.gains, case.taper, *case.transfers]
    saved = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    rejects(api, public, case.images, kwargs, "invalid_volume_reconstruction_regularization")
    for array, (snapshot, strides, writable) in zip(arrays, saved, strict=True):
        assert (
            np.array_equal(array, snapshot)
            and array.strides == strides
            and array.flags.writeable == writable
        )


def test_input_snapshot_before_transform_if_fft_path(
    api: Any, public: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = make_case()
    frozen = copy.deepcopy(case)
    expected_s, expected_v = oracle(frozen)
    bs, bv = allowance(frozen)
    kwargs = arguments(case, public)
    original = np.fft.fftn

    def changed(*args: Any, **kw: Any) -> Any:
        case.images[:] = 0
        case.phases[:] = 0
        case.carriers[:] = 0
        case.gains[:] = 0
        case.taper[:] = 0
        for record in kwargs["order_otfs"]:
            record.values[:] = 0
            record.fz_per_um[:] = 0
        return original(*args, **kw)

    monkeypatch.setattr(np.fft, "fftn", changed)
    result = api(case.images, **kwargs)
    assert_matches(case, result, expected_s, expected_v, bs, bv)


@pytest.mark.parametrize(
    "choice",
    ["containers-scalars", "repeated-phases", "weak-full-rank", "negative-gauge", "signed-inputs"],
)
def test_inherited_permitted_alternatives(api: Any, public: Any, choice: str) -> None:
    case = make_case()
    if choice == "repeated-phases":
        case.phases[:, -1] = case.phases[:, 0]
        assert all(np.linalg.matrix_rank(basis(p)) == 5 for p in case.phases)
    elif choice == "weak-full-rank":
        case.phases[:] = np.linspace(0, 0.12, 7)
        assert 10 < np.linalg.cond(basis(case.phases[0])) < 1e9
        assert np.linalg.matrix_rank(basis(case.phases[0])) == 5
        result = api(case.images, **arguments(case, public))
        assert_output_shapes(case, result)
        # The contract promises no uniform digits outside the condition regime.
        assert np.all(np.isfinite(result.volume)) and np.all(np.isfinite(result.spectrum))
        return
    elif choice == "negative-gauge":
        for e in case.transfers:
            e *= -1j
    elif choice == "signed-inputs":
        case.images -= 1.5
        case.phases -= 4
    expected_s, expected_v = oracle(case)
    bs, bv = allowance(case)
    kwargs = arguments(case, public)
    if choice == "containers-scalars":
        kwargs["regularization"] = np.float32(case.penalty)
        kwargs["output_shape_yx"] = [np.int32(4), np.uint64(5)]
        kwargs["order_otfs"] = tuple(
            dataclasses.replace(
                record,
                voxel_size_um=list(map(np.float64, case.spacing)),
                origin_zyx=list(map(np.int64, record.origin_zyx)),
            )
            for record in kwargs["order_otfs"]
        )
    result = api(case.images, **kwargs)
    assert_matches(case, result, expected_s, expected_v, bs, bv)


@pytest.mark.parametrize("name", ["values", "fz_per_um", "fy_per_um", "fx_per_um"])
@pytest.mark.parametrize("kind", ["list", "subclass", "masked", "nan", "shape"])
def test_each_transfer_array_plainness_finiteness_and_shape(
    api: Any, public: Any, name: str, kind: str
) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    record = kwargs["order_otfs"][0]
    value = invalid_array(kind, getattr(record, name))
    kwargs["order_otfs"][0] = dataclasses.replace(record, **{name: value})
    rejects(api, public, case.images, kwargs, "invalid_volume_reconstruction_otfs")


@pytest.mark.parametrize(
    "field,code",
    [
        ("images", "nonfinite_volume_reconstruction_images"),
        ("phases_rad", "nonfinite_volume_reconstruction_phases"),
        ("gains", "invalid_volume_reconstruction_gain_values"),
        ("carriers_per_um", "invalid_fractional_volume_carriers"),
        ("apodization", "invalid_volume_reconstruction_apodization_values"),
    ],
)
def test_source_and_converted_finiteness_at_available_widest_float(
    api: Any, public: Any, field: str, code: str
) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    original = case.images if field == "images" else kwargs[field]
    value = original.astype(np.longdouble)
    # On wide-longdouble hosts this is finite at source and overflows f64;
    # on equal-width hosts the paired source-nonfinite rejection applies.
    value.flat[0] = np.finfo(np.longdouble).max
    if field == "images":
        images = value
    else:
        images = case.images
        kwargs[field] = value
    if np.finfo(np.longdouble).max > np.longdouble(np.finfo(float).max):
        rejects(api, public, images, kwargs, code)
    else:
        value.flat[0] = np.inf
        rejects(api, public, images, kwargs, code)


def test_finite_carrier_is_not_modulo_reduced_or_rejected_by_dtype(api: Any, public: Any) -> None:
    case = make_case()
    kwargs = arguments(case, public)
    kwargs["carriers_per_um"] = np.full((2, 2), np.iinfo(np.uint64).max, dtype=np.uint64)
    rejects(api, public, case.images, kwargs, "invalid_volume_reconstruction_output_shape")


@pytest.mark.parametrize(
    "failure,expected",
    [
        (np.linalg.LinAlgError, "volume_phase_solver_failure"),
        (RuntimeError, None),
        (MemoryError, None),
    ],
)
def test_separator_dependency_failure_propagates_without_relabeling(
    api: Any,
    public: Any,
    monkeypatch: pytest.MonkeyPatch,
    failure: type[Exception],
    expected: str | None,
) -> None:
    case = make_case()
    touched = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        touched.append(True)
        raise failure("RA07 phase dependency failure")

    monkeypatch.setattr(np.linalg, "svd", fail)
    monkeypatch.setattr(np.linalg, "lstsq", fail)
    try:
        result = api(case.images, **arguments(case, public))
    except Exception as error:
        assert touched
        if expected is None:
            assert type(error) is failure
        else:
            assert isinstance(error, public.SimreconError)
            assert cast(Any, error).code == expected
    else:
        # Equivalent SVD execution APIs are not forbidden by this packet.
        assert_output_shapes(case, result)
        assert not touched and np.all(np.isfinite(result.volume))


def test_subnormal_images_are_not_a_hidden_input_reject(api: Any, public: Any) -> None:
    case = make_case((1, 1, 1), orientations=1, output_yx=(1, 1))
    case.carriers[:] = 0
    case.transfers[0][:] = 0
    case.transfers[0][0] = 1
    case.gains[:] = 1
    case.penalty = 0
    case.taper[:] = 1
    case.images[:] = np.nextafter(0.0, 1.0)
    result = api(case.images, **arguments(case, public))
    assert_output_shapes(case, result)
    # Underflow is allowed. No relative/subnormal-retention promise is invented.
    assert np.all(np.isfinite(result.volume)) and np.all(np.isfinite(result.spectrum))


def test_endpoint_guard_is_stricter_than_size_bound_for_even_native(api: Any, public: Any) -> None:
    case = make_case((1, 2, 1), orientations=1, output_yx=(3, 1))
    case.carriers[:] = [0.125, 0.0]
    case.images[:] = 0
    case.taper[:] = 0
    # Native y=-1 shifted by -2*(1/8)=-1.25 lies below output hull [-1,1].
    assert case.output_yx[0] == case.native[1] + math.ceil(4 * abs(case.shifts[0][0]))
    rejects(
        api,
        public,
        case.images,
        arguments(case, public),
        "invalid_volume_reconstruction_output_shape",
    )
    case.output_yx = (4, 1)
    case.taper = np.ones(case.output)
    evaluate(case, api, public)


@pytest.mark.parametrize("stage", ["band-accumulation", "native-synthesis"])
def test_finite_native_quotients_do_not_waive_later_range_failure(
    api: Any, public: Any, stage: str
) -> None:
    if stage == "band-accumulation":
        case = make_case((1, 1, 1), orientations=2, output_yx=(1, 1))
        transfer, amplitude = 0.125, np.finfo(float).max * 0.1875
        # H=2*(1/8)^2, each native quotient = .75*float_max;
        # summing the two DC bands cannot be represented.
    else:
        case = make_case((1, 1, 2), orientations=1, output_yx=(1, 2))
        transfer, amplitude = 0.25, np.finfo(float).max * 0.375
        # Two coefficients = .75*float_max; their positive synthesis overflows.
    case.carriers[:] = 0
    case.gains[:] = 1
    case.penalty = 0
    case.taper[:] = 0
    case.images[:] = amplitude
    if stage == "native-synthesis":
        case.images[..., 1] = 0
    for e in case.transfers:
        e[:] = 0
        e[0] = transfer
    rejects(
        api, public, case.images, arguments(case, public), "unrepresentable_volume_reconstruction"
    )


@pytest.mark.parametrize(
    "native,out",
    [
        ((2, 2, 3), (4, 5)),
        ((3, 3, 2), (5, 4)),
        ((1, 1, 1), (3, 3)),
        ((1, 3, 4), (5, 6)),
        ((1, 2, 2), (4, 4)),
    ],
)
def test_oracle_nominal_inputs_meet_exact_window_and_moderate_regime(
    native: tuple[int, int, int], out: tuple[int, int]
) -> None:
    case = make_case(native, output_yx=out)
    for axis in range(2):
        maximum = max(abs(c[axis]) for c in case.shifts)
        assert out[axis] >= native[axis + 1] + math.ceil(4 * maximum)
        low, high = bins(out[axis])[0], bins(out[axis])[-1]
        for c in case.shifts:
            for m in range(-2, 3):
                for j in bins(native[axis + 1]):
                    assert low <= j - m * c[axis] <= high
    assert all(np.linalg.cond(basis(p)) <= 10 for p in case.phases)
    assert np.max(np.abs(case.images)) <= 16
    assert np.all((case.gains >= 0.5) & (case.gains <= 2))
    assert all(np.max(np.abs(e.real)) <= 1 and np.max(np.abs(e.imag)) <= 1 for e in case.transfers)
    assert case.images.size <= 512 and math.prod(case.output) <= 512
    assert 0 <= case.penalty <= 1
    assert weights(case)[1] >= 1 / 16
