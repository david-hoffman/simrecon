"""Blind public-contract proofs for known-profile raw finite-bead calibration."""

from __future__ import annotations

import copy
import dataclasses
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
from math import prod
from typing import Any, Literal

import numpy as np
import pytest

import simrecon
from finite_bead_compensation_fixture import (
    EPS,
    FMAX,
    PRECISION,
    Q0,
    Case,
    Index,
    Truth,
    Z,
    algebra_case,
    angle_phasor,
    arguments,
    assert_close,
    certificate,
    d,
    declare,
    estimator,
    exact_mass,
    expected,
    extreme_components_case,
    fit,
    indices,
    inverse,
    model_case,
    modes,
    normalized_profile,
    pi,
    rational,
    represented_basis,
    root,
    rounded_weight,
    specimen_images,
    transform,
)


@pytest.fixture(scope="module")
def case() -> Case:
    """Provide a closed asymmetric raw-input case, never a product result."""
    return model_case()


def calibrate(acquisition: Any, **kwargs: Any) -> Any:
    """Resolve the new public API so independent oracles run before it exists."""
    api_name = "calibrate_raw_finite_bead"
    operation = getattr(simrecon, api_name)
    return operation(acquisition, **kwargs)


def run(case: Case, **changes: Any) -> Any:
    """Compose the actual public declaration and new calibration boundaries."""
    acquisition, kwargs = declare(case), arguments(case, **changes)
    before = caller_state((acquisition, kwargs))
    result = calibrate(acquisition, **kwargs)
    assert caller_state((acquisition, kwargs)) == before
    return result


def error(code: str, acquisition: Any, kwargs: dict[str, Any]) -> None:
    """Check a stable public error and whole-call rejection, without prose pins."""
    before = caller_state((acquisition, kwargs))
    with pytest.raises(simrecon.SimreconError) as caught:
        calibrate(acquisition, **kwargs)
    assert caught.value.code == code
    assert caller_state((acquisition, kwargs)) == before


def caller_state(value: Any) -> Any:
    """Snapshot only public caller values, storage and write permissions."""
    if isinstance(value, np.ndarray):
        return (value.dtype.str, value.shape, value.strides, value.flags.writeable, value.tobytes())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (field.name, caller_state(getattr(value, field.name)))
            for field in dataclasses.fields(value)
        )
    if isinstance(value, dict):
        return tuple((key, caller_state(member)) for key, member in value.items())
    if isinstance(value, (tuple, list)):
        return type(value), tuple(caller_state(member) for member in value)
    return type(value), repr(value)


def check_truth(result: Any, case: Case, minimum: float = 0.1) -> Truth:
    """Compare all complex bins and localization against independent raw truth."""
    truth = expected(case, minimum)
    shape = case.profile.shape
    assert result.components.dc.shape == shape and result.components.dc.dtype == np.dtype("float64")
    for side in (result.components.c1, result.components.c2):
        assert side.shape == shape and side.dtype == np.dtype("complex128")
    assert result.response.values.shape == (3, *shape)
    assert result.response.values.dtype == np.dtype("complex128")
    assert result.response.origin_zyx == truth.origin
    for actual, exact in zip(
        (result.components.dc, result.components.c1, result.components.c2),
        truth.components,
        strict=True,
    ):
        for value, target in zip(actual.flat, exact, strict=True):
            assert abs(d(value.real) - target.re) <= truth.separation_budget
            assert abs(d(value.imag) - target.im) <= truth.separation_budget
    for order in range(3):
        for value, target, budget in zip(
            result.response.values[order].flat,
            truth.spectra[order],
            truth.spectral_budget[order],
            strict=True,
        ):
            assert_close(value, target, budget)
    diagnostic = result.provenance["profile_transfer"]
    assert diagnostic.shape == shape and diagnostic.dtype == np.dtype("complex128")
    assert result.provenance["compensated_dc"].shape == shape
    assert result.provenance["compensated_dc"].dtype == np.dtype("float64")
    identity = np.count_nonzero(case.profile) == 1 and case.profile.flat[0] > 0
    eta = 128 * case.profile.size * EPS + 4 * case.profile.size * Q0
    for k, value, target in zip(modes(shape), diagnostic.flat, truth.profile, strict=True):
        if identity or k == (0, 0, 0):
            assert value == 1 + 0j
        else:
            assert_close(value, target, eta)
    for value, target in zip(
        result.provenance["compensated_dc"].flat, truth.localization, strict=True
    ):
        assert abs(d(value) - target) <= truth.spatial_budget
    # This conditional check proves selection policy only, not diagnostic accuracy.
    assert certificate(diagnostic, case.profile, result.provenance["min_profile_transfer"])
    assert result.response.values[(0, *(n // 2 for n in shape))] == 1 + 0j
    for size, spacing, vector in zip(
        shape,
        case.spacing,
        (result.response.fz_per_um, result.response.fy_per_um, result.response.fx_per_um),
        strict=True,
    ):
        assert vector.shape == (size,)
        for k, value in zip(range(-(size // 2), (size + 1) // 2), vector, strict=True):
            exact = Decimal(k) / (size * d(spacing))
            assert abs(d(value) - exact) <= 8 * EPS * abs(exact) + Q0

    return truth


def assert_positive_margin(truth: Truth) -> None:
    """Retain the positive cohort's independent profile and inverse-budget facts."""
    assert truth.spatial_budget > 0
    assert min(value.magnitude() for value in truth.profile) > Decimal("0.1")


def test_independent_roots_transforms_and_inverse() -> None:
    """Check oracle signs, normalization, rational roots and native indexing."""
    with localcontext() as context:
        context.prec = PRECISION
        assert str(pi()).startswith("3.14159265358979323846264338327950288419716939937510")
        assert root(Fraction(1, 4)) == Z(d(0), d(1))
        assert root(Fraction(3, 4)) == Z(d(0), d(-1))
        for cycles_value in (Fraction(1, 3), Fraction(-5, 7)):
            value = root(cycles_value)
            assert abs(value.magnitude() - 1) < Decimal("1e-105")
        shape = (1, 2, 4)
        impulse = [Z(d(0))] * 8
        impulse[1] = Z(d(1))
        transformed = transform(impulse, shape)
        for k, value in zip(modes(shape), transformed, strict=True):
            assert value == root(Fraction(-k[2], 4))
        assert inverse(transformed, shape) == impulse
        constant = transform([Z(d(2), d(-3))] * 8, shape)
        assert constant[6] == Z(d(16), d(-24))
        assert all(value == Z() for i, value in enumerate(constant) if i != 6)


def test_independent_represented_phase_least_squares() -> None:
    """Verify decimal fit with an exactly representable constant and a residual."""
    with localcontext() as context:
        context.prec = PRECISION
        phases = np.array([0.13, 0.84, 1.91, 2.76, 3.69, 4.82, 5.63, 0.13])
        basis = represented_basis(phases)
        # Public condition-number calculation selects the informative test regime.
        assert np.linalg.cond(basis) < 10
        images = np.full((len(phases), 1, 1, 1), 8.0)
        result = fit(images, phases)
        assert abs(result[0][0].re - 8) < Decimal("1e-100")
        assert max(value.magnitude() for row in result[1:] for value in row) < Decimal("1e-100")
        images[-1, 0, 0, 0] += 1
        fitted = fit(images, phases)
        coordinates = [
            fitted[0][0].re,
            2 * fitted[1][0].re,
            -2 * fitted[1][0].im,
            2 * fitted[2][0].re,
            -2 * fitted[2][0].im,
        ]
        residual = [
            d(value)
            - sum(
                (d(h) * coefficient for h, coefficient in zip(row, coordinates, strict=True)),
                Decimal(),
            )
            for row, value in zip(basis, images.flat, strict=True)
        ]
        assert max(abs(value) for value in residual) > Decimal("0.1")
        for column in range(5):
            assert abs(
                sum(
                    (d(row[column]) * value for row, value in zip(basis, residual, strict=True)),
                    Decimal(),
                )
            ) < Decimal("1e-100")


def test_independent_exact_mass_normalization_and_certificate() -> None:
    """Check overflow/subnormal observers and exact certificate equality."""
    maximum = float(FMAX)
    for profile in (
        np.array([maximum, maximum]).reshape(1, 1, 2),
        np.array([float(Q0), 0.0]).reshape(1, 1, 2),
    ):
        with localcontext() as context:
            context.prec = PRECISION
            applied, exact = normalized_profile(profile)
            assert exact_mass(applied) == 1
            assert sum((value.re for value in exact), Decimal()) == 1
    point = np.array([1.0, 0.0]).reshape(1, 1, 2)
    assert certificate(np.ones((1, 1, 2), dtype=np.complex128), point, 1.0)
    transfer = np.ones((1, 1, 2), dtype=np.complex128)
    transfer[0, 0, 0] = complex(0.5, 0.0)
    # Nonidentity eta includes q0. Exactly represented mu=0.5 is uncertifiable
    # against minimum=0.5; the exact sum is greater even when float addition ties.
    nonidentity = np.array([3.0, 1.0]).reshape(1, 1, 2)
    assert not certificate(transfer, nonidentity, 0.5)
    assert certificate(transfer, nonidentity, 0.25)
    assert rounded_weight(Fraction(1, 2) + Fraction(1, 2**54)) == 0.5
    assert rounded_weight(Fraction(1, 2) + Fraction(3, 2**54)) == 0.5 + 2**-52
    assert rounded_weight(Fraction(1, 2**1075)) == 0.0
    assert rounded_weight(Fraction(3, 2**1075)) == 2 * float(Q0)


def test_public_exports_binding_and_frozen_records(case: Case) -> None:
    type_name, api_name = "FiniteBeadCalibration", "calibrate_raw_finite_bead"
    result_type = getattr(simrecon, type_name)
    operation = getattr(simrecon, api_name)
    acquisition = declare(case)
    kwargs = arguments(case)
    result = operation(acquisition, **kwargs)
    assert type(result) is result_type
    assert {field.name for field in dataclasses.fields(result)} == {
        "components",
        "response",
        "provenance",
    }
    assert isinstance(result.components, simrecon.VolumePhaseComponents)
    assert isinstance(result.response, simrecon.EmpiricalVolumeResponse)
    assert [field.name for field in dataclasses.fields(result.components)] == ["dc", "c1", "c2"]
    assert {field.name for field in dataclasses.fields(result.response)} == {
        "values",
        "fz_per_um",
        "fy_per_um",
        "fx_per_um",
        "voxel_size_um",
        "origin_zyx",
    }
    for record in (result, result.components, result.response):
        for field in dataclasses.fields(record):
            with pytest.raises((AttributeError, TypeError)):
                setattr(record, field.name, getattr(record, field.name))
            with pytest.raises((AttributeError, TypeError)):
                delattr(record, field.name)
    direct = result_type(components=None, response=None, provenance=None)
    assert direct.components is None and direct.response is None and direct.provenance is None
    for missing in kwargs:
        incomplete = kwargs.copy()
        del incomplete[missing]
        with pytest.raises(TypeError):
            operation(acquisition, **incomplete)
    with pytest.raises(TypeError):
        operation(
            acquisition,
            kwargs["group"],
            **{key: value for key, value in kwargs.items() if key != "group"},
        )
    with pytest.raises(TypeError):
        operation(acquisition, **kwargs, true_center=case.anchor)
    with pytest.raises(TypeError):
        operation(**kwargs)


@pytest.mark.parametrize(
    "shape,anchor",
    [
        ((2, 3, 4), (1, 2, 1)),
        ((3, 4, 3), (2, 3, 2)),
        ((1, 3, 4), (0, 1, 3)),
        ((2, 1, 3), (1, 0, 2)),
        ((1, 1, 1), (0, 0, 0)),
    ],
)
def test_raw_finite_model_all_bins_geometry(shape: Index, anchor: Index) -> None:
    generated = model_case(shape, anchor)
    truth = check_truth(run(generated), generated)
    assert_positive_margin(truth)
    if shape == (2, 3, 4) and anchor == (1, 2, 1):
        with localcontext() as context:
            context.prec = PRECISION
            raw_peak = max(
                range(generated.profile.size), key=lambda index: truth.components[0][index].re
            )
            assert indices(generated.profile.shape)[raw_peak] != truth.origin
            assert truth.origin == generated.anchor
            assert min(value.magnitude() for value in truth.profile) > Decimal("0.1")
            assert np.linalg.cond(represented_basis(generated.phases)) < 10
            # Independent exact finite model, distinct from the rounded raw fit.
            for n, actual in zip(indices(generated.profile.shape), truth.localization, strict=True):
                offset = tuple(
                    (na - ba) % size
                    for na, ba, size in zip(
                        n, generated.anchor, generated.profile.shape, strict=True
                    )
                )
                assert abs(actual - d(generated.kernel[offset])) <= truth.spatial_budget
            assert exact_mass(generated.kernel) == 1


@pytest.mark.parametrize(
    "profile_kind",
    [
        "asymmetric",
        "wrapped",
        "translated_delta",
        "origin_point",
        "anchor_empty",
        "tied_profile_peak",
    ],
)
def test_profile_anchor_and_three_shifted_divisors(case: Case, profile_kind: str) -> None:
    generated = copy.deepcopy(case)
    if profile_kind == "wrapped":
        generated = model_case(profile_shift=(1, 2, 3))
    elif profile_kind == "anchor_empty":
        generated.profile[0, 0, 0] = 0
    elif profile_kind == "tied_profile_peak":
        generated.profile.fill(0)
        generated.profile[0, 0, :3] = (3, 3, 1)
    elif profile_kind in ("translated_delta", "origin_point"):
        generated.profile.fill(0)
        generated.profile[(1, 2, 3) if profile_kind == "translated_delta" else (0, 0, 0)] = 2
    # An arbitrary valid stored acquisition remains an estimator input even when
    # its declared profile is not the generating specimen. Truth uses that input.
    result = run(generated)
    truth = check_truth(result, generated)
    assert_positive_margin(truth)
    if profile_kind == "origin_point":
        assert np.array_equal(
            result.provenance["profile_transfer"],
            np.ones_like(result.provenance["profile_transfer"]),
        )


@pytest.mark.parametrize(
    "carrier",
    [(0, 0), (-1, 2), (1 + 3 * 10**90, -1 - 4 * 10**100), [np.uint64(2**64 - 1), np.int8(-1)]],
)
def test_exact_unreduced_carrier_and_modular_profile_shifts(case: Case, carrier: Any) -> None:
    generated = copy.deepcopy(case)
    generated.carrier = (int(carrier[0]), int(carrier[1]))
    result = run(generated, calibration_carrier_bins=carrier)
    check_truth(result, generated)
    assert result.provenance["calibration_carrier_bins"] == generated.carrier
    assert all(type(value) is int for value in result.provenance["calibration_carrier_bins"])


@pytest.mark.parametrize(
    "bad",
    [
        None,
        (1,),
        (1, 2, 3),
        np.array([1, 2]),
        (True, 1),
        (np.bool_(False), 1),
        (1.0, 2),
        (1 + 0j, 2),
        ("1", 2),
    ],
)
def test_carrier_grammar(case: Case, bad: Any) -> None:
    error(
        "invalid_empirical_transfer_carrier",
        declare(case),
        arguments(case, calibration_carrier_bins=bad),
    )


@pytest.mark.parametrize(
    "storage", ["native", "big_endian", "fortran", "reversed", "readonly", "signed_zero"]
)
def test_profile_supported_storage(case: Case, storage: str) -> None:
    generated = copy.deepcopy(case)
    if storage == "big_endian":
        generated.profile = generated.profile.astype(">f8")
    elif storage == "fortran":
        generated.profile = np.asfortranarray(generated.profile)
    elif storage == "reversed":
        generated.profile = generated.profile[:, :, ::-1]
    elif storage == "readonly":
        generated.profile.flags.writeable = False
    elif storage == "signed_zero":
        generated.profile[generated.profile == 0] = -0.0
    before = generated.profile.tobytes()
    strides, writable = generated.profile.strides, generated.profile.flags.writeable
    result = run(generated)
    truth = check_truth(result, generated)
    if storage == "reversed":
        assert_positive_margin(truth)
    assert generated.profile.tobytes() == before
    assert generated.profile.strides == strides and generated.profile.flags.writeable == writable
    supplied = result.provenance["bead_profile"]["supplied"]
    assert supplied.dtype == generated.profile.dtype and supplied.tobytes() == before


def invalid_profiles(case: Case) -> list[Any]:
    """List distinct profile grammar/domain outcomes with valid other inputs."""
    negative = case.profile.copy()
    negative.flat[-1] = -float(Q0)
    nan = case.profile.copy()
    nan.flat[-1] = np.nan
    infinite = case.profile.copy()
    infinite.flat[-1] = np.inf
    return [
        None,
        case.profile.tolist(),
        np.ma.array(case.profile),
        case.profile.view(ProfileSubclass),
        case.profile.astype("f4"),
        case.profile.astype("i8"),
        case.profile.astype("c16"),
        case.profile.astype("bool"),
        np.zeros((1, 2)),
        np.zeros((0, 3, 4)),
        np.zeros((2, 3, 5)),
        np.zeros_like(case.profile),
        negative,
        nan,
        infinite,
    ]


class ProfileSubclass(np.ndarray):
    """Represent a caller ndarray subclass outside the plain-array boundary."""


@pytest.mark.parametrize("index", range(15))
def test_profile_rejections(case: Case, index: int) -> None:
    bad = invalid_profiles(case)[index]
    error("invalid_finite_bead_profile", declare(case), arguments(case, bead_profile=bad))


@pytest.mark.parametrize("scale", [float.fromhex("0x1p+1000"), float.fromhex("0x1p-1000")])
def test_exact_profile_scale_invariance(case: Case, scale: float) -> None:
    generated = copy.deepcopy(case)
    generated.profile *= scale
    result = run(generated)
    check_truth(result, generated)
    applied, _ = normalized_profile(generated.profile)
    assert np.array_equal(result.provenance["bead_profile"]["applied"], applied)
    assert np.array_equal(applied, normalized_profile(case.profile)[0])


@pytest.mark.parametrize("weights", [(float(FMAX), float(FMAX) / 4), (float(Q0), 0.0)])
def test_profile_mass_overflow_and_least_subnormal(weights: tuple[float, float]) -> None:
    generated = algebra_case(np.array([4.0, 1.0]).reshape(1, 1, 2))
    generated.profile = np.array(weights).reshape(1, 1, 2)
    result = run(generated)
    check_truth(result, generated)
    assert np.array_equal(
        result.provenance["bead_profile"]["applied"], normalized_profile(generated.profile)[0]
    )


@pytest.mark.parametrize("minimum", [1, np.int64(1), np.float32(0.5), np.float64(0.1), float(Q0)])
def test_threshold_accepted_scalars_and_point_equality(case: Case, minimum: Any) -> None:
    generated = copy.deepcopy(case)
    generated.profile.fill(0)
    generated.profile.flat[0] = float(Q0)
    result = run(generated, min_profile_transfer=minimum)
    assert result.provenance["min_profile_transfer"] == float(minimum)
    assert type(result.provenance["min_profile_transfer"]) is float
    assert np.all(result.provenance["profile_transfer"] == 1 + 0j)


@pytest.mark.parametrize(
    "bad",
    [
        True,
        np.bool_(False),
        0,
        -1,
        1.0000000000000002,
        float("nan"),
        float("inf"),
        1 + 0j,
        "0.1",
        np.array(0.1),
        [0.1],
        Fraction(1, 2),
        Decimal("0.1"),
        10**1000,
    ],
)
def test_threshold_rejections(case: Case, bad: Any) -> None:
    error(
        "invalid_finite_bead_transfer_threshold",
        declare(case),
        arguments(case, min_profile_transfer=bad),
    )


@pytest.mark.parametrize(
    "profile,minimum",
    [
        ([1.0, 1.0], 0.1),
        ([3.0, 1.0], 0.5),
        ([3.0, 1.0], np.nextafter(0.5, 0.0)),
        ([3.0, 1.0], 0.75),
        ([0.0, 1.0], 1.0),
    ],
)
@pytest.mark.parametrize("carrier", [(0, 0), (0, 10**80 + 1)])
def test_all_node_weak_singular_uncertifiable_profile_gate(
    profile: list[float], minimum: float, carrier: tuple[int, int]
) -> None:
    generated = algebra_case(np.array([4.0, 1.0]).reshape(1, 1, 2))
    generated.profile = np.array(profile).reshape(1, 1, 2)
    # Both side rows are mathematically zero. Every native profile node still
    # needs certification, independently of which shifted numerators use it.
    error(
        "unstable_finite_bead_transfer",
        declare(generated),
        arguments(generated, min_profile_transfer=minimum, calibration_carrier_bins=carrier),
    )


def test_safely_certified_nonidentity_near_policy(case: Case) -> None:
    generated = algebra_case(np.array([4.0, 1.0]).reshape(1, 1, 2))
    generated.profile = np.array([3.0, 1.0]).reshape(1, 1, 2)
    minimum = 0.5 - 2**-40
    result = run(generated, min_profile_transfer=minimum)
    assert certificate(result.provenance["profile_transfer"], generated.profile, minimum)
    check_truth(result, generated)


EXACT_CERTIFICATE_WITNESSES = (
    pytest.param(
        (3, 1),
        "0x1.ffffffffffc00p-2",
        (0.5 + 0j, 1 + 0j),
        False,
        id="exact-eta-tail-rejects",
    ),
    pytest.param(
        (6, 0, 1, 1),
        "0x1.465655f122bf6p-1",
        (0.75 + 0j, 0.625 - 0.125j, 1 + 0j, 0.625 + 0.125j),
        True,
        id="rounded-magnitude-false-rejection",
    ),
    pytest.param(
        (1, 0, 14, 1),
        "0x1.a13a9cb996251p-1",
        (0.875 + 0j, -0.8125 - 0.0625j, 1 + 0j, -0.8125 + 0.0625j),
        False,
        id="rounded-magnitude-and-boundary-false-acceptance",
    ),
)


def exact_certificate_case(weights: tuple[int, ...], carrier: tuple[int, int]) -> Case:
    """Build valid stored raw data with fixed dc and mathematically zero sides."""
    dc = np.zeros((1, 1, len(weights)), dtype=np.float64)
    dc.flat[:2] = (8, 1)
    generated = algebra_case(dc)
    generated.profile = np.array(weights, dtype=np.float64).reshape(dc.shape)
    generated.carrier = carrier
    return generated


@pytest.mark.parametrize("weights,minimum_hex,transfer,accepted", EXACT_CERTIFICATE_WITNESSES)
def test_independent_exact_certificate_witnesses(
    weights: tuple[int, ...],
    minimum_hex: str,
    transfer: tuple[complex, ...],
    accepted: bool,
) -> None:
    """Prove exact policy and native public-input attainability before the API exists."""
    generated = exact_certificate_case(weights, (0, 0))
    acquisition = declare(generated)
    assert acquisition.acquisition_kind == "sim_beads"
    assert acquisition.axes == ("orientation", "phase", "z", "y", "x")
    assert acquisition.data.shape == (1, len(generated.phases), 1, 1, len(weights))
    assert np.array_equal(acquisition.data[0], generated.images)
    assert np.all(generated.images == generated.kernel[None])
    assert np.linalg.cond(represented_basis(generated.phases)) <= 10
    assert exact_mass(generated.kernel) == 9

    minimum = float.fromhex(minimum_hex)
    target = np.array(transfer, dtype=np.complex128).reshape(generated.profile.shape)
    with localcontext() as context:
        context.prec = PRECISION
        applied, profile = normalized_profile(generated.profile)
        assert [value.native() for value in transform(profile, generated.profile.shape)] == list(
            transfer
        )
        assert all(
            Fraction.from_float(float(value)) == Fraction(weight, sum(weights))
            for value, weight in zip(applied.flat, weights, strict=True)
        )
        # Both singleton permutations and the four-site transform have exact
        # dyadic outputs here. Verify every allowed spatial-axis permutation
        # through the native public dependency, never a finite-value mock.
        for axes in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)):
            assert np.array_equal(np.fft.fftshift(np.fft.fftn(applied, axes=axes)), target)

        eta = Fraction(128 * len(weights), 2**52) + Fraction(4 * len(weights), 2**1074)
        boundary = Fraction.from_float(minimum) + eta
        squares = [
            Fraction.from_float(value.real) ** 2 + Fraction.from_float(value.imag) ** 2
            for value in transfer
        ]
        decisions = [
            square >= (Fraction.from_float(minimum) if i == len(weights) // 2 else boundary) ** 2
            for i, square in enumerate(squares)
        ]
        assert all(decisions) is accepted
        assert certificate(target, generated.profile, minimum) is accepted
        limiting = min(range(len(transfer)), key=squares.__getitem__)
        value = transfer[limiting]
        rounded_mu = Fraction.from_float(float(np.hypot(value.real, value.imag)))
        rounded_boundary = Fraction.from_float(rounded_weight(boundary))
        assert rounded_mu >= rounded_boundary
        assert rounded_mu < boundary
        if accepted:
            # The legitimate positive differs from a policy that rounds only
            # magnitude, while preserving the exact threshold plus eta.
            assert rounded_mu**2 < squares[limiting]
            truth = expected(generated, minimum)
            size = len(weights)
            mass_lower = 9 - size * truth.separation_budget
            lambda_upper = (9 + 2 * size * truth.separation_budget) / mass_lower
            da_upper = 512 * size * EPS * lambda_upper + 16 * size * Q0
            assert 64 * (lambda_upper + da_upper) / d(minimum) < FMAX
            assert truth.origin == (0, 0, 0)
            ordered = sorted(truth.localization, reverse=True)
            assert ordered[0] - ordered[1] > 2 * truth.spatial_budget
        elif len(weights) == 2:
            assert boundary == Fraction(1, 2) + Fraction(8, 2**1074)
            assert squares[limiting] == Fraction(1, 4)
        else:
            assert squares[limiting] == Fraction(170, 256)
            assert rounded_mu**2 > squares[limiting]


@pytest.mark.parametrize("weights,minimum_hex,transfer,accepted", EXACT_CERTIFICATE_WITNESSES)
@pytest.mark.parametrize("carrier", [(0, 0), (10**80 + 1, -(10**90) + 3)])
def test_raw_exact_profile_certificate_decisions(
    weights: tuple[int, ...],
    minimum_hex: str,
    transfer: tuple[complex, ...],
    accepted: bool,
    carrier: tuple[int, int],
) -> None:
    generated = exact_certificate_case(weights, carrier)
    minimum = float.fromhex(minimum_hex)
    if accepted:
        result = run(generated, min_profile_transfer=minimum)
        assert np.array_equal(
            result.provenance["profile_transfer"],
            np.array(transfer, dtype=np.complex128).reshape(generated.profile.shape),
        )
        check_truth(result, generated, minimum)
    else:
        error(
            "unstable_finite_bead_transfer",
            declare(generated),
            arguments(generated, min_profile_transfer=minimum),
        )


@pytest.mark.parametrize("bad", [None, {}, np.zeros((1, 1, 1))])
def test_nonacquisition_rejected(case: Case, bad: Any) -> None:
    error("invalid_finite_bead_acquisition", bad, arguments(case))


@pytest.mark.parametrize("kind", ["specimen_sim", "detection_psf"])
def test_wrong_valid_acquisition_kind(case: Case, kind: str) -> None:
    if kind == "specimen_sim":
        acquisition = declare(case, kind=kind)
    else:
        acquisition = simrecon.declare_acquisition(
            case.images[0],
            config={
                "version": 1,
                "acquisition_kind": kind,
                "axes": ["z", "y", "x"],
                "intensity_unit": "count",
            },
        )
    error("invalid_finite_bead_kind", acquisition, arguments(case))


def test_explicit_z_required(case: Case) -> None:
    acquisition = simrecon.declare_acquisition(
        case.images[:, 0][None],
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "y", "x"],
            "intensity_unit": "count",
        },
    )
    error("invalid_finite_bead_axes", acquisition, arguments(case, bead_profile=case.profile[:1]))


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {"orientation": 0, "absent": 0},
        {},
        {"orientation": True},
        {"orientation": np.int64(0)},
        {"orientation": -1},
        {"orientation": 1},
        {"orientation": 0.0},
        {"orientation": [0]},
    ],
)
def test_group_grammar_and_bounds(case: Case, bad: Any) -> None:
    error("invalid_finite_bead_group", declare(case), arguments(case, group=bad))


@pytest.mark.parametrize("source_layout", [False, True])
@pytest.mark.parametrize(
    "offset_map,response_map", [(False, False), (False, True), (True, False), (True, True)]
)
def test_canonical_full_correction_selection(
    case: Case, source_layout: bool, offset_map: bool, response_map: bool
) -> None:
    acquisition = declare(case, grouped=True, source_layout=source_layout)
    signal = acquisition.data.copy()
    shape = signal.shape
    offset = np.arange(prod(shape), dtype=np.float64).reshape(shape) % 3 if offset_map else 2
    response = np.where(np.indices(shape)[-1] % 2, 2.0, 4.0) if response_map else 2
    if offset_map:
        offset = np.asfortranarray(np.asarray(offset).astype(">f8"))
        offset.flags.writeable = False
    if response_map:
        response = np.asarray(response).astype(">f8")
        response.flags.writeable = False
    acquisition.data[...] = offset + response * signal
    selected = copy.deepcopy(case)
    # The inherited stored problem uses sequential RN64 subtraction/division,
    # including rounding of the generated raw camera values.
    corrected = (acquisition.data.astype(np.float64) - offset) / response
    selected.images = corrected[1, 0, 1]
    before = caller_state((acquisition, offset, response, case.phases, case.profile))
    result = calibrate(
        acquisition,
        **arguments(
            selected,
            group={"time": 1, "channel": 0, "orientation": 1},
            offset=offset,
            response=response,
        ),
    )
    check_truth(result, selected)
    assert before == caller_state((acquisition, offset, response, case.phases, case.profile))
    assert result.provenance["group"] == {"time": 1, "channel": 0, "orientation": 1}
    correction = result.provenance["linear_response"]
    assert set(correction) == {
        "model",
        "equation",
        "input_unit",
        "output_unit",
        "offset",
        "response",
    }
    assert correction["model"] == "linear_response_v1"
    assert correction["equation"] == "raw=offset+response*signal"
    assert correction["input_unit"] == "count" and correction["output_unit"] == "electron"
    for name, value in (("offset", offset), ("response", response)):
        snapshot = correction[name]
        assert set(snapshot) == {"source", "supplied", "applied"}
        assert snapshot["source"] == "supplied"
        if isinstance(value, np.ndarray):
            assert snapshot["supplied"].dtype == value.dtype
            assert np.array_equal(snapshot["supplied"], value)
            assert np.array_equal(snapshot["applied"], value.astype(np.float64))
            assert snapshot["supplied"].flags.c_contiguous
            assert snapshot["applied"].dtype.isnative and snapshot["applied"].flags.c_contiguous
            assert not np.shares_memory(snapshot["supplied"], snapshot["applied"])
            assert not np.shares_memory(value, snapshot["supplied"])
            assert not np.shares_memory(value, snapshot["applied"])
        else:
            assert type(snapshot["supplied"]) is type(value)
            assert snapshot["supplied"] == value and snapshot["applied"] == float(value)
    for missing in ("time", "channel", "orientation"):
        group = {"time": 1, "channel": 0, "orientation": 1}
        del group[missing]
        error(
            "invalid_finite_bead_group",
            acquisition,
            arguments(selected, group=group, offset=offset, response=response),
        )


@pytest.mark.parametrize(
    "failure",
    ["pixels", "offset", "response", "subtract", "divide", "selected_shape", "source_shape"],
)
def test_nonselected_complete_correction_failures(case: Case, failure: str) -> None:
    acquisition = declare(case, grouped=True, source_layout=True)
    kwargs = arguments(case, group={"time": 1, "channel": 0, "orientation": 1})
    nonselected = (0, 0, 0, 0, 0, 0, 0)
    if failure == "pixels":
        acquisition.data[nonselected] = np.inf
        code = "invalid_linear_response_data"
    elif failure in ("offset", "response"):
        coefficient = np.ones(acquisition.data.shape)
        coefficient[nonselected] = np.nan if failure == "offset" else 0
        kwargs[failure] = coefficient
        code = f"invalid_linear_response_{failure}"
    elif failure == "subtract":
        acquisition.data[nonselected] = float(FMAX)
        offset = np.zeros(acquisition.data.shape)
        offset[nonselected] = -float(FMAX)
        kwargs.update(offset=offset, response=4)
        code = "linear_response_range"
    elif failure == "divide":
        acquisition.data[nonselected] = float(FMAX)
        response = np.ones(acquisition.data.shape)
        response[nonselected] = float(Q0)
        kwargs["response"] = response
        code = "linear_response_range"
    else:
        kwargs["offset"] = np.zeros(
            case.images.shape if failure == "selected_shape" else acquisition.source_shape
        )
        code = "invalid_linear_response_shape"
    error(code, acquisition, kwargs)


@pytest.mark.parametrize(
    "name,bad,code",
    [
        ("offset", True, "invalid_linear_response_offset"),
        ("offset", np.float64(0), "invalid_linear_response_offset"),
        ("response", -1, "invalid_linear_response_response"),
        ("response", np.array(1), "invalid_linear_response_shape"),
        ("output_unit", "", "invalid_linear_response_unit"),
        ("output_unit", None, "invalid_linear_response_unit"),
    ],
)
def test_correction_domain_propagates(case: Case, name: str, bad: Any, code: str) -> None:
    error(code, declare(case), arguments(case, **{name: bad}))


@pytest.mark.parametrize(
    "bad,code",
    [
        (None, "invalid_volume_phase_angles"),
        ([0.0] * 7, "invalid_volume_phase_angles"),
        (np.zeros(7, dtype=complex), "invalid_volume_phase_angles_dtype"),
        (np.zeros((7, 1)), "invalid_volume_phase_angles_shape"),
        (np.zeros(6), "invalid_volume_phase_angles_shape"),
        (np.full(7, np.inf), "nonfinite_volume_phase_angles"),
        (np.zeros(7), "rank_deficient_volume_phases"),
    ],
)
def test_phase_rejections(case: Case, bad: Any, code: str) -> None:
    error(code, declare(case), arguments(case, phases_rad=bad))


def test_actual_unequal_repeated_and_off_model_phases(case: Case) -> None:
    generated = copy.deepcopy(case)
    generated.images = np.concatenate((case.images, case.images[:1]), axis=0)
    generated.images[-1, 0, 0, 0] += 0.125
    generated.phases = np.concatenate((case.phases, case.phases[:1]))
    acquisition = declare(generated)
    # Valid nominal command tensor is intentionally unidentifiable and differs
    # from the actual identifiable phase declaration used by the estimator.
    config = copy.deepcopy(acquisition.original_config)
    config["nominal_phases_rad"] = [[0.0] * len(generated.phases)]
    acquisition = simrecon.declare_acquisition(acquisition.data, config=config)
    result = calibrate(acquisition, **arguments(generated))
    check_truth(result, generated)
    assert np.all(result.provenance["source_metadata"]["nominal_phases_rad"] == 0)
    assert result.provenance["phases_rad"]["source"] == "supplied_actual"


@pytest.mark.parametrize(
    "bad",
    [
        None,
        (1, 2),
        np.ones((1, 3)),
        (True, 1, 1),
        (1 + 0j, 1, 1),
        (0, 1, 1),
        (-1, 1, 1),
        (float("inf"), 1, 1),
        (10**1000, 1, 1),
    ],
)
def test_spacing_grammar(case: Case, bad: Any) -> None:
    error("invalid_otf_voxel_size", declare(case), arguments(case, voxel_size_um=bad))


@pytest.mark.parametrize(
    "spacing",
    [
        (float(FMAX), float(FMAX), float(FMAX)),
        [np.int64(2), np.float32(0.25), np.float64(0.125)],
        np.array([0.5, 0.25, 0.125], dtype=">f8"),
    ],
)
def test_supplied_spacing_authoritative_extreme_and_container(case: Case, spacing: Any) -> None:
    generated = copy.deepcopy(case)
    generated.spacing = (float(spacing[0]), float(spacing[1]), float(spacing[2]))
    result = run(generated, voxel_size_um=spacing)
    check_truth(result, generated)
    assert result.response.voxel_size_um == generated.spacing
    assert result.provenance["source_metadata"]["sampling_um"] == {"z": None, "y": 9.0, "x": 8.0}


def test_singleton_minimum_spacing_and_frequency_overflow() -> None:
    generated = algebra_case(np.ones((1, 1, 1)))
    result = run(generated, voxel_size_um=(float(Q0),) * 3, min_profile_transfer=1)
    assert all(
        np.array_equal(vector, np.array([0.0]))
        for vector in (
            result.response.fz_per_um,
            result.response.fy_per_um,
            result.response.fx_per_um,
        )
    )
    generated = algebra_case(np.array([2.0, 1.0]).reshape(1, 1, 2))
    error(
        "unrepresentable_otf_frequencies",
        declare(generated),
        arguments(generated, voxel_size_um=(1, 1, float(Q0))),
    )


@pytest.mark.parametrize("values", [[2.0, -3.0], [1.0, -1.0], [0.0, 0.0], [-1.0, -2.0]])
def test_original_nonpositive_mass(values: list[float]) -> None:
    generated = algebra_case(np.array(values).reshape(1, 1, 2))
    error("nonpositive_empirical_response_mass", declare(generated), arguments(generated))


def test_original_raw_tie_allowed_after_compensation() -> None:
    generated = algebra_case(np.array([5.0, 5.0, 1.0, 1.0]).reshape(1, 1, 4))
    generated.profile = np.array([5.0, 2.0, 0.0, 1.0]).reshape(1, 1, 4)
    assert_positive_margin(check_truth(run(generated), generated))


def test_compensated_exact_positive_tie_rejected() -> None:
    # An exactly constant phase stack produces the same separated dc at every
    # site; an origin-point profile leaves the exact computed tie intact.
    generated = algebra_case(np.ones((1, 1, 2)))
    error("ambiguous_bead_peak", declare(generated), arguments(generated))


@pytest.mark.parametrize("scale", [1.0, float.fromhex("0x1p+1000"), float.fromhex("0x1p-1000")])
def test_original_mass_once_zero_sides_and_relative_complex_gain(scale: float) -> None:
    dc = np.array([8.0, -1.0, 2.0, 1.0]).reshape(1, 1, 4) * scale
    first = (
        np.array([1 + 2j, -2 + 1j, 3 - 2j, -2 - 1j], dtype=np.complex128).reshape(1, 1, 4) * scale
    )
    second = np.zeros((1, 1, 4), dtype=np.complex128)
    generated = algebra_case(dc, first, second)
    generated.profile = np.array([3.0, 1.0, 0.0, 0.0]).reshape(1, 1, 4)
    check_truth(run(generated), generated)


def test_mass_above_fmax_and_subnormal_signal() -> None:
    for dc in (
        np.array([0.75, 0.5]).reshape(1, 1, 2) * float(FMAX),
        np.array([float(Q0)]).reshape(1, 1, 1),
    ):
        generated = algebra_case(dc)
        result = run(generated)
        assert np.all(np.isfinite(result.response.values.real))
        assert np.all(np.isfinite(result.response.values.imag))
        assert result.response.values[(0, *(n // 2 for n in dc.shape))] == 1 + 0j
        if dc.size > 1:
            check_truth(result, generated)


@pytest.mark.parametrize("stage", ["profile_forward", "observed_forward", "inverse"])
@pytest.mark.parametrize(
    "failure",
    [
        "floating",
        "overflow",
        "warning",
        "nonfinite_real",
        "nonfinite_imag",
        "nonfinite_dc_real",
        "nonfinite_dc_imag",
        "memory",
        "runtime",
        "type",
        "value",
    ],
)
def test_public_transform_failure_contract(
    case: Case, monkeypatch: pytest.MonkeyPatch, stage: str, failure: str
) -> None:
    # The public forward inputs distinguish these stages without a call-count
    # or layout assumption: this profile has max(r)<1, while every nonzero
    # observed order scaled by its largest component has max(abs(component))=1.
    # The profile's three nonzero normalized weights also identify it if a
    # caller batches it with observed rows. Axes permutations preserve these
    # value predicates. Injection proves
    # dependency handling only; finite bogus values never supply scientific truth.
    boundary = "ifftn" if stage == "inverse" else "fftn"
    original = getattr(np.fft, boundary)
    exceptions = {
        "floating": FloatingPointError,
        "overflow": OverflowError,
        "memory": MemoryError,
        "runtime": RuntimeError,
        "type": TypeError,
        "value": ValueError,
    }
    sentinel = exceptions.get(failure, RuntimeError)("public FFT failure sentinel")
    injected = False

    def dependency(*args: Any, **kwargs: Any) -> Any:
        nonlocal injected
        source = np.asarray(args[0] if args else kwargs["a"])
        maximum = max(float(np.max(np.abs(source.real))), float(np.max(np.abs(source.imag))))
        profile_present = maximum < 1 or all(
            np.any(source.real == float(weight))
            for weight in (Fraction(8, 11), Fraction(2, 11), Fraction(1, 11))
        )
        if (stage == "profile_forward" and not profile_present) or (
            stage == "observed_forward" and maximum != 1
        ):
            return original(*args, **kwargs)
        injected = True
        if failure in exceptions:
            raise sentinel
        result = original(*args, **kwargs)
        if failure == "warning":
            warnings.warn("overflow encountered in public FFT", RuntimeWarning, stacklevel=2)
        elif failure in ("nonfinite_real", "nonfinite_dc_real"):
            result.real.flat[0 if failure == "nonfinite_dc_real" else -1] = np.inf
        else:
            result.imag.flat[0 if failure == "nonfinite_dc_imag" else -1] = np.nan
        return result

    monkeypatch.setattr(np.fft, boundary, dependency)
    acquisition, kwargs = declare(case), arguments(case)
    before = caller_state((acquisition, kwargs))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        settings, filters = np.geterr().copy(), list(warnings.filters)
        if failure in ("memory", "runtime", "type", "value"):
            with pytest.raises(exceptions[failure], match="public FFT failure sentinel") as caught:
                calibrate(acquisition, **kwargs)
            assert caught.value is sentinel
        else:
            error("finite_bead_transform_failure", acquisition, kwargs)
        assert np.geterr() == settings and warnings.filters == filters
    assert injected
    assert caller_state((acquisition, kwargs)) == before


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore"])
@pytest.mark.parametrize("reject", [False, True])
def test_floating_warning_policy_and_preservation(
    case: Case,
    mode: Literal["raise", "warn", "ignore"],
    reject: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = np.fft.fftn

    def external_warning(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("unrelated public dependency warning", UserWarning, stacklevel=2)
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", external_warning)
    acquisition = declare(case)
    profile = case.profile.copy()
    if reject:
        profile.fill(1)
    before = (acquisition.data.tobytes(), profile.tobytes(), case.phases.tobytes())
    with np.errstate(all=mode), warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        filters = list(warnings.filters)
        settings = np.geterr().copy()
        if reject:
            error(
                "unstable_finite_bead_transfer", acquisition, arguments(case, bead_profile=profile)
            )
        else:
            calibrate(acquisition, **arguments(case, bead_profile=profile))
        assert np.geterr() == settings and warnings.filters == filters
        assert any(
            item.category is UserWarning
            and str(item.message) == "unrelated public dependency warning"
            for item in recorded
        )
        assert not any(issubclass(item.category, RuntimeWarning) for item in recorded)
    assert before == (acquisition.data.tobytes(), profile.tobytes(), case.phases.tobytes())


def arrays(value: Any) -> list[np.ndarray[Any, Any]]:
    """Walk only public output records and metadata to audit storage ownership."""
    if isinstance(value, np.ndarray):
        return [value]
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return [
            array
            for field in dataclasses.fields(value)
            for array in arrays(getattr(value, field.name))
        ]
    if isinstance(value, dict):
        return [array for member in value.values() for array in arrays(member)]
    if isinstance(value, (list, tuple)):
        return [array for member in value for array in arrays(member)]
    return []


def test_exact_provenance_and_independent_owned_arrays(case: Case) -> None:
    acquisition = declare(case)
    phases = case.phases.astype(">f8")
    profile = case.profile.astype(">f8")
    spacing = np.array(case.spacing, dtype=">f8")
    group = {"orientation": 0}
    result = calibrate(
        acquisition,
        **arguments(
            case, phases_rad=phases, bead_profile=profile, voxel_size_um=spacing, group=group
        ),
    )
    again = calibrate(
        acquisition,
        **arguments(
            case, phases_rad=phases, bead_profile=profile, voxel_size_um=spacing, group=group
        ),
    )
    provenance = result.provenance
    assert type(provenance) is dict
    assert set(provenance) == {
        "model",
        "group",
        "source_metadata",
        "linear_response",
        "phases_rad",
        "voxel_size_um",
        "bead_compensation",
        "response_gauge",
        "bead_profile",
        "calibration_carrier_bins",
        "min_profile_transfer",
        "profile_transfer",
        "compensated_dc",
    }
    assert provenance["model"] == "discrete_finite_bead_v1"
    assert provenance["bead_compensation"] == "native_periodic_profile_division_v1"
    assert provenance["response_gauge"] == "compensated_dc_peak_with_supplied_phase_origin"
    assert set(provenance["bead_profile"]) == {"source", "supplied", "applied", "normalization"}
    assert provenance["bead_profile"]["source"] == "supplied_relative_site_weights"
    assert provenance["bead_profile"]["normalization"] == "exact_converted_sum"
    assert np.array_equal(provenance["bead_profile"]["applied"], normalized_profile(profile)[0])
    assert set(provenance["source_metadata"]) == {
        field.name for field in dataclasses.fields(acquisition) if field.name != "data"
    }
    for field in dataclasses.fields(acquisition):
        if field.name != "data":
            assert field.name in provenance["source_metadata"]
            original, snapshot = (
                getattr(acquisition, field.name),
                provenance["source_metadata"][field.name],
            )
            if isinstance(original, np.ndarray):
                assert np.array_equal(original, snapshot)
            else:
                assert snapshot == original
    assert "data" not in provenance["source_metadata"]
    assert provenance["phases_rad"]["source"] == "supplied_actual"
    assert set(provenance["phases_rad"]) == {"source", "supplied", "applied"}
    assert provenance["phases_rad"]["supplied"].dtype == phases.dtype
    assert np.array_equal(provenance["phases_rad"]["applied"], phases.astype("f8"))
    assert provenance["voxel_size_um"]["source"] == "supplied"
    assert set(provenance["voxel_size_um"]) == {"source", "supplied", "applied"}
    assert provenance["voxel_size_um"]["supplied"].dtype == spacing.dtype
    assert provenance["voxel_size_um"]["applied"] == case.spacing
    caller_arrays = [acquisition.data, profile, phases, spacing]
    output_arrays = arrays(result)
    # Metadata fields may share snapshots under the inherited contract; only
    # numerical observations/spectra/diagnostics and explicit supplied/applied
    # pairs have the stronger pairwise no-alias guarantee.
    numerical = [
        result.components.dc,
        result.components.c1,
        result.components.c2,
        result.response.values,
        result.response.fz_per_um,
        result.response.fy_per_um,
        result.response.fx_per_um,
        provenance["bead_profile"]["supplied"],
        provenance["bead_profile"]["applied"],
        provenance["profile_transfer"],
        provenance["compensated_dc"],
        provenance["phases_rad"]["supplied"],
        provenance["phases_rad"]["applied"],
        provenance["voxel_size_um"]["supplied"],
    ]
    for a, b in combinations(numerical, 2):
        assert not np.shares_memory(a, b)
    for array in numerical:
        assert type(array) is np.ndarray and array.flags.c_contiguous and array.flags.writeable
    for array in [
        result.components.dc,
        result.components.c1,
        result.components.c2,
        result.response.values,
        result.response.fz_per_um,
        result.response.fy_per_um,
        result.response.fx_per_um,
        provenance["bead_profile"]["applied"],
        provenance["profile_transfer"],
        provenance["compensated_dc"],
    ]:
        assert array.dtype.isnative
    assert provenance["profile_transfer"].dtype == np.dtype("complex128")
    assert provenance["compensated_dc"].dtype == np.dtype("float64")
    for array in output_arrays:
        assert all(not np.shares_memory(array, caller) for caller in caller_arrays)
        assert all(not np.shares_memory(array, other) for other in arrays(again))
    phases.fill(0)
    profile.fill(0)
    spacing.fill(1)
    group["orientation"] = 9
    acquisition.original_metadata["opaque"][0] = b"changed"
    assert provenance["group"] == {"orientation": 0}
    assert provenance["source_metadata"]["original_metadata"]["opaque"][0] == b"retained"
    assert provenance["bead_profile"]["supplied"].tobytes() == case.profile.astype(">f8").tobytes()


def test_origin_point_limit_keeps_existing_point_api(case: Case) -> None:
    generated = copy.deepcopy(case)
    generated.profile.fill(0)
    generated.profile.flat[0] = 1
    acquisition = declare(generated)
    finite = calibrate(acquisition, **arguments(generated, min_profile_transfer=1))
    old_kwargs = {
        key: value
        for key, value in arguments(generated).items()
        if key not in {"bead_profile", "calibration_carrier_bins", "min_profile_transfer"}
    }
    point = simrecon.calibrate_raw_point_bead(acquisition, **old_kwargs)
    # Each API is compared with independent truth, not used as the other's oracle.
    check_truth(finite, generated)
    truth = expected(generated)
    for order in range(3):
        for value, target, budget in zip(
            point.response.values[order].flat,
            truth.spectra[order],
            truth.spectral_budget[order],
            strict=True,
        ):
            assert_close(value, target, budget)
    assert point.provenance["model"] == "point_bead_identity_v1"
    assert finite.provenance["model"] == "discrete_finite_bead_v1"


def test_bead_movement_storage_roll_and_phase_reference(case: Case) -> None:
    baseline = run(case)
    moved = model_case(anchor=(0, 1, 3))
    shifted_phase = model_case(phase_shift=0.37)
    rolled = copy.deepcopy(case)
    roll = (1, -1, 2)
    rolled.images = np.roll(rolled.images, roll, axis=(1, 2, 3))
    results = [
        (case, baseline),
        (moved, run(moved)),
        (shifted_phase, run(shifted_phase)),
        (rolled, run(rolled)),
    ]
    for generated, result in results:
        check_truth(result, generated)
    for generated, result in results:
        offset = (-roll[1], -roll[2]) if generated is rolled else (0, 0)
        delta = -0.37 if generated is shifted_phase else 0.0
        adapted = simrecon.adapt_empirical_volume_response(
            result.response,
            carrier_bins=case.carrier,
            coordinate_offset_yx=offset,
            phase_reference_shift_rad=delta,
            source="declared same instrument and phase reference",
        )
        with localcontext() as context:
            context.prec = PRECISION
            truth = expected(generated)
            rho = Fraction(
                case.carrier[0] * (truth.origin[1] + offset[0]), case.profile.shape[1]
            ) + Fraction(case.carrier[1] * (truth.origin[2] + offset[1]), case.profile.shape[2])
            for order in range(3):
                phasor = root(-order * rho) * angle_phasor(-order * d(delta))
                for value, target, budget in zip(
                    adapted.values[order].flat,
                    truth.spectra[order],
                    truth.spectral_budget[order],
                    strict=True,
                ):
                    assert_close(
                        value,
                        target * phasor,
                        budget + 128 * EPS * (target.l1() + 2 * budget) + 16 * Q0,
                    )


def test_native_compensation_before_physical_point_interpolation(case: Case) -> None:
    result = run(case)
    shape = case.profile.shape
    # Dyadic spacing makes these off-node coordinates exactly inside the hull.
    points = np.array([[0.0, 0.0, 0.5], [0.0, -0.5, -1.0]])
    truth = expected(case)
    source_modes = modes(shape)
    for order in (-2, -1, 0, 1, 2):
        sampled = simrecon.sample_empirical_volume_transfer(
            result.response,
            order=order,
            frequencies_zyx_per_um=points,
            calibration_carrier_bins=case.carrier,
            coordinate_offset_yx=(0, 0),
            phase_reference_shift_rad=0.0,
            source="known finite-grid calibration pairing",
        )
        with localcontext() as context:
            context.prec = PRECISION
            rho = Fraction(case.carrier[0] * truth.origin[1], shape[1]) + Fraction(
                case.carrier[1] * truth.origin[2], shape[2]
            )
            gauge = root(-abs(order) * rho)
            for point, actual in zip(points, sampled.values, strict=True):
                coordinate = [
                    Fraction.from_float(float(value)) * (-1 if order < 0 else 1) for value in point
                ]
                target = Z()
                budget = Decimal()
                stencil_l1 = Decimal()
                for node, k in enumerate(source_modes):
                    weight = Fraction(1)
                    for axis in range(3):
                        scaled = (
                            coordinate[axis] * shape[axis] * Fraction.from_float(case.spacing[axis])
                        )
                        weight *= max(Fraction(), 1 - abs(scaled - k[axis]))
                    if weight:
                        target += truth.spectra[abs(order)][node].scale(rational(weight))
                        budget += truth.spectral_budget[abs(order)][node] * rational(weight)
                        stencil_l1 += rational(weight) * (
                            truth.spectra[abs(order)][node].l1()
                            + 2 * truth.spectral_budget[abs(order)][node]
                        )
                if order:
                    target *= gauge
                if order < 0:
                    target = target.conjugate()
                assert_close(actual, target, budget + 1024 * EPS * stencil_l1 + 64 * Q0)
    endpoint = np.array([[0.0, 0.0, 1 / (2 * case.spacing[2])]])
    with pytest.raises(simrecon.SimreconError) as caught:
        simrecon.sample_empirical_volume_transfer(
            result.response,
            order=1,
            frequencies_zyx_per_um=endpoint,
            calibration_carrier_bins=case.carrier,
            coordinate_offset_yx=(0, 0),
            phase_reference_shift_rad=0,
            source="positive physical endpoint",
        )
    assert caught.value.code == "incomplete_empirical_transfer_coverage"
    reflected = simrecon.sample_empirical_volume_transfer(
        result.response,
        order=-1,
        frequencies_zyx_per_um=endpoint,
        calibration_carrier_bins=case.carrier,
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0,
        source="reflected negative physical endpoint",
    )
    assert reflected.values.shape == (1,)


def mass_witness() -> tuple[Case, float]:
    """Choose safe raw mass and a certifiable near-uniform discrete profile."""
    generated = algebra_case(
        np.array([7.0, 2.0, 1.0]).reshape(1, 1, 3),
        np.array([1 + 2j, 0.5 - 1j, -0.25 + 0.5j]).reshape(1, 1, 3),
    )
    generated.profile = np.array([1.0, 1.0, 1 - 2**-28]).reshape(1, 1, 3)
    return generated, 2**-30


def test_original_mass_not_rounded_compensated_array_sum() -> None:
    generated, minimum = mass_witness()
    truth = check_truth(run(generated, min_profile_transfer=minimum), generated, minimum)
    with localcontext() as context:
        context.prec = PRECISION
        rounded = np.array([float(value) for value in truth.localization])
        rounded_mass = rational(exact_mass(rounded))
        assert rounded_mass > 0 and rounded_mass != 1
        # The masses differ on independently computed data. This is a witness
        # to the distinction, not proof that the broad profile-error allowance
        # separates every implementation that renormalizes by this tiny error.
        discrepancy = max(
            value.magnitude() * abs(1 / rounded_mass - 1) for row in truth.spectra for value in row
        )
        assert discrepancy > 0


def reconstruction_case(
    case: Case, offset: tuple[int, int] = (0, 0), delta: float = 0.0
) -> tuple[Any, ...]:
    """Return independent known-parameter generator and estimator inputs."""
    specimen = (
        np.arange(1, case.profile.size + 1, dtype=np.float64).reshape(case.profile.shape) / 16
    )
    phases = np.array([0.21, 1.12, 1.88, 2.97, 3.83, 4.71, 5.92])
    images = specimen_images(case, specimen, phases)
    output_shape = (case.profile.shape[0], case.profile.shape[1] + 4, case.profile.shape[2] + 4)
    mask = np.where(np.indices(output_shape)[-1] % 2, 0.75, 0.5)
    with localcontext() as context:
        context.prec = PRECISION
        truth = expected(case)
        rho = Fraction(
            case.carrier[0] * (truth.origin[1] + offset[0]), case.profile.shape[1]
        ) + Fraction(case.carrier[1] * (truth.origin[2] + offset[1]), case.profile.shape[2])
        transfers = [
            [value * root(-order * rho) * angle_phasor(-order * d(delta)) for value in row]
            for order, row in enumerate(truth.spectra)
        ]
        errors = [
            [
                budget + 128 * EPS * (value.l1() + 2 * budget) + 16 * Q0
                for value, budget in zip(row, budgets, strict=True)
            ]
            for row, budgets in zip(truth.spectra, truth.spectral_budget, strict=True)
        ]
        dc = modes(case.profile.shape).index((0, 0, 0))
        transfers[0][dc], errors[0][dc] = Z(d(1)), Decimal()
        spectrum, volume, calibration_error = estimator(
            images, phases, transfers, case.carrier, output_shape, Decimal("0.25"), mask, errors
        )
    return (
        images,
        phases,
        output_shape,
        mask,
        spectrum,
        volume,
        calibration_error,
        transfers,
        errors,
    )


def test_independent_estimator_signed_singleton() -> None:
    """Check a hand-solvable ridge estimator, gain placement and 1/P removal."""
    generated = algebra_case(np.full((1, 1, 1), 6.0))
    with localcontext() as context:
        context.prec = PRECISION
        transfers = [[Z(d(1))], [Z(d(0), d(0.5))], [Z(d(0.25))]]
        spectrum, volume, _ = estimator(
            generated.images,
            generated.phases,
            transfers,
            (0, 0),
            (1, 1, 1),
            d(0.25),
            np.ones((1, 1, 1)),
            [[Decimal()]] * 3,
        )
        # Only dc=6 contributes U. V=1+2*(1/2)^2+2*(1/4)^2.
        target = Z(Decimal(6) / (1 + Decimal("0.5") + Decimal("0.125") + Decimal("0.25")))
        assert (spectrum[0] - target).magnitude() < Decimal("1e-100")
        assert volume == spectrum


def calibration_variant(case: Case, variant: str) -> tuple[Case, tuple[int, int], float]:
    """Declare common-reference controls using public coordinate meanings."""
    if variant == "moved":
        return model_case(anchor=(0, 1, 3)), (0, 0), 0.0
    if variant == "phase":
        return model_case(phase_shift=0.37), (0, 0), -0.37
    if variant == "rolled":
        generated = copy.deepcopy(case)
        generated.images = np.roll(generated.images, (1, -1, 2), axis=(1, 2, 3))
        return generated, (1, -2), 0.0
    return case, (0, 0), 0.0


@pytest.mark.parametrize("variant", ["base", "moved", "rolled", "phase"])
def test_raw_finite_calibration_adapter_and_known_parameter_reconstruction(
    case: Case, variant: str
) -> None:
    case, offset, delta = calibration_variant(case, variant)
    calibrated = run(case)
    adapted = simrecon.adapt_empirical_volume_response(
        calibrated.response,
        carrier_bins=case.carrier,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=delta,
        source="declared common finite grid, instrument and phase reference",
    )
    images, phases, shape, mask, spectrum, volume, calibration_errors, transfers, errors = (
        reconstruction_case(case, offset, delta)
    )
    with localcontext() as context:
        context.prec = PRECISION
        assert np.linalg.cond(represented_basis(phases)) <= 10
        assert all(
            max(abs(value.re), abs(value.im)) + budget <= 1
            for row, budgets in zip(transfers, errors, strict=True)
            for value, budget in zip(row, budgets, strict=True)
        )
        assert 65536 * 5 * (len(phases) + case.profile.size + prod(shape)) * EPS <= d(2**-10)
        assert 64 * 5 * prod(shape) * max(d(value) for value in images.flat) < FMAX
        assert any(abs(value.im) > Decimal("1e-6") for value in spectrum)
        assert any(abs(value.im) > Decimal("1e-6") for value in volume)
    reconstructed = simrecon.reconstruct_volume(
        images[None],
        order_otfs=[adapted],
        phases_rad=phases[None],
        carriers_bins=np.array([case.carrier]),
        gains=np.ones(1),
        regularization=0.25,
        output_shape_yx=shape[1:],
        apodization=mask,
    )
    with localcontext() as context:
        context.prec = PRECISION
        size = case.profile.size
        peak = max(abs(d(value)) for value in images.flat)
        beta = 65536 * 5 * (len(phases) + size) * EPS * peak + 256 * 5 * (len(phases) + size) * Q0
        for actual, target, error_bound in zip(
            reconstructed.spectrum.flat, spectrum, calibration_errors, strict=True
        ):
            assert_close(actual, target, beta + error_bound)
        spatial_budget = (
            prod(shape) * beta
            + 16384 * 5 * prod(shape) * EPS * peak
            + 64 * prod(shape) * Q0
            + sum(calibration_errors, Decimal())
        )
        for actual, target in zip(reconstructed.volume.flat, volume, strict=True):
            assert_close(actual, target, spatial_budget)
    # The target is the declared ridge/masked finite estimator. It is not an
    # exact recovery assertion for the specimen or continuous optical response.


@pytest.mark.parametrize("dtype", ["<f8", ">f8", "f4", "i8", "u8"])
def test_raw_conversion_and_actual_phase_storage(case: Case, dtype: str) -> None:
    generated = copy.deepcopy(case)
    generated.images = np.asarray(case.images * 16, dtype=dtype)
    generated.phases = generated.phases.astype(">f8")
    generated.phases.flags.writeable = False
    acquisition = declare(generated)
    acquisition.data.flags.writeable = False
    before = acquisition.data.tobytes(), generated.phases.tobytes()
    result = calibrate(acquisition, **arguments(generated))
    assert_positive_margin(check_truth(result, generated))
    assert before == (acquisition.data.tobytes(), generated.phases.tobytes())
    assert not acquisition.data.flags.writeable and not generated.phases.flags.writeable


def test_joint_exposure_permutation_and_signed_integer_phases(case: Case) -> None:
    generated = copy.deepcopy(case)
    generated.phases = np.array([-3, -2, -1, 0, 1, 2, 3], dtype=np.int64)
    # Stored arbitrary observations remain a valid estimator input. No generating
    # physical model is claimed when this phase declaration is changed.
    permutation = np.array([6, 2, 4, 0, 5, 1, 3])
    generated.phases = generated.phases[permutation]
    generated.images = generated.images[permutation]
    check_truth(run(generated), generated)


class GroupSubclass(dict[str, int]):
    """Represent a mapping outside the plain group grammar."""


class PairSubclass(tuple[int, int]):
    """Represent a sequence outside the exact pair-container grammar."""


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("group", GroupSubclass(orientation=0), "invalid_finite_bead_group"),
        ("calibration_carrier_bins", PairSubclass((0, 0)), "invalid_empirical_transfer_carrier"),
        ("phases_rad", np.ma.array(np.arange(7.0)), "invalid_volume_phase_angles"),
        ("phases_rad", np.zeros(7, dtype=bool), "invalid_volume_phase_angles_dtype"),
        ("phases_rad", np.zeros(7, dtype=object), "invalid_volume_phase_angles_dtype"),
        ("offset", [0], "invalid_linear_response_offset"),
        ("offset", 1 + 0j, "invalid_linear_response_offset"),
        ("offset", float("inf"), "invalid_linear_response_offset"),
        ("offset", 10**1000, "invalid_linear_response_offset"),
        ("response", True, "invalid_linear_response_response"),
        ("response", np.float64(1), "invalid_linear_response_response"),
        ("response", float("nan"), "invalid_linear_response_response"),
        ("response", 0, "invalid_linear_response_response"),
        ("response", 10**1000, "invalid_linear_response_response"),
        ("output_unit", 7, "invalid_linear_response_unit"),
    ],
)
def test_additional_inherited_declaration_decisions(
    case: Case, field: str, value: Any, code: str
) -> None:
    error(code, declare(case), arguments(case, **{field: value}))


def test_missing_input_unit_and_too_few_exposures(case: Case) -> None:
    acquisition = declare(case)
    config = copy.deepcopy(acquisition.original_config)
    del config["intensity_unit"]
    unitless = simrecon.declare_acquisition(acquisition.data, config=config)
    error("invalid_linear_response_unit", unitless, arguments(case))
    generated = copy.deepcopy(case)
    generated.images, generated.phases = generated.images[:4], generated.phases[:4]
    error("invalid_volume_phase_shape", declare(generated), arguments(generated))


def extended_thresholds() -> list[Any]:
    """Include source-wide conversion boundaries only when natively available."""
    result: list[Any] = [np.float16(0.5), np.uint64(1)]
    if np.finfo(np.longdouble).minexp < -1074:
        result.append(np.ldexp(np.longdouble(1), -1075))
    return result


@pytest.mark.parametrize("threshold", extended_thresholds())
def test_native_source_width_threshold_conversion(case: Case, threshold: Any) -> None:
    if float(threshold) == 0:
        assert threshold > 0
        error(
            "invalid_finite_bead_transfer_threshold",
            declare(case),
            arguments(case, min_profile_transfer=threshold),
        )
    else:
        generated = copy.deepcopy(case)
        generated.profile.fill(0)
        generated.profile.flat[0] = 1
        result = run(generated, min_profile_transfer=threshold)
        assert result.provenance["min_profile_transfer"] == float(threshold)


def test_existing_point_pipeline_independent_baseline(case: Case) -> None:
    """Exercise an initially available prerequisite without the new API."""
    generated = copy.deepcopy(case)
    generated.profile.fill(0)
    generated.profile.flat[0] = 1
    kwargs = {
        name: value
        for name, value in arguments(generated).items()
        if name not in {"bead_profile", "calibration_carrier_bins", "min_profile_transfer"}
    }
    result = simrecon.calibrate_raw_point_bead(declare(generated), **kwargs)
    truth = expected(generated)
    assert result.response.origin_zyx == truth.origin
    for order in range(3):
        for actual, target, budget in zip(
            result.response.values[order].flat,
            truth.spectra[order],
            truth.spectral_budget[order],
            strict=True,
        ):
            assert_close(actual, target, budget)


def test_existing_consumer_pipeline_from_independent_public_record(case: Case) -> None:
    """Validate the custom finite estimator through real existing consumers.

    This algebraic-record compatibility proof can run before finite calibration
    exists. It does not establish raw compensation/localization or its provenance;
    the raw-input composition tests own those obligations.
    """
    truth = expected(case)
    values = np.array(
        [[value.native() for value in row] for row in truth.spectra], dtype=np.complex128
    ).reshape(3, *case.profile.shape)
    values[(0, *(n // 2 for n in case.profile.shape))] = 1 + 0j
    with localcontext() as context:
        context.prec = PRECISION
        frequencies = [
            np.array(
                [
                    float(Decimal(k) / (size * d(spacing)))
                    for k in range(-(size // 2), (size + 1) // 2)
                ]
            )
            for size, spacing in zip(case.profile.shape, case.spacing, strict=True)
        ]
    response = simrecon.EmpiricalVolumeResponse(
        values=values,
        fz_per_um=frequencies[0],
        fy_per_um=frequencies[1],
        fx_per_um=frequencies[2],
        voxel_size_um=case.spacing,
        origin_zyx=truth.origin,
    )
    adapted = simrecon.adapt_empirical_volume_response(
        response,
        carrier_bins=case.carrier,
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source="independent algebraic-record oracle compatibility",
    )
    images, phases, shape, mask, spectrum, volume, calibration_errors, _, _ = reconstruction_case(
        case
    )
    actual = simrecon.reconstruct_volume(
        images[None],
        order_otfs=[adapted],
        phases_rad=phases[None],
        carriers_bins=np.array([case.carrier]),
        gains=np.ones(1),
        regularization=0.25,
        output_shape_yx=shape[1:],
        apodization=mask,
    )
    with localcontext() as context:
        context.prec = PRECISION
        peak = max(abs(d(value)) for value in images.flat)
        beta = (
            65536 * 5 * (len(phases) + case.profile.size) * EPS * peak
            + 256 * 5 * (len(phases) + case.profile.size) * Q0
        )
        for value, target, allowance in zip(
            actual.spectrum.flat, spectrum, calibration_errors, strict=True
        ):
            assert_close(value, target, beta + allowance)
        budget = (
            prod(shape) * beta
            + 16384 * 5 * prod(shape) * EPS * peak
            + 64 * prod(shape) * Q0
            + sum(calibration_errors, Decimal())
        )
        for value, target in zip(actual.volume.flat, volume, strict=True):
            assert_close(value, target, budget)


def test_finite_components_with_overflowing_complex_magnitude() -> None:
    generated = extreme_components_case()
    truth = check_truth(run(generated), generated)
    with localcontext() as context:
        context.prec = PRECISION
        assert np.linalg.cond(represented_basis(generated.phases)) <= 10
        first = truth.components[1][0]
        assert first.magnitude() > FMAX
        assert all(
            max(abs(value.re), abs(value.im)) + truth.separation_budget < FMAX
            for row in truth.components
            for value in row
        )
        assert (
            64
            * max(
                sum((value.l1() for value in row), Decimal()) / truth.components[0][0].re
                for row in truth.components
            )
            < FMAX
        )


@pytest.mark.parametrize(
    "dtype",
    ["f2", "O", "U1", "V8", "datetime64[D]"]
    + ([np.dtype(np.longdouble).str] if np.dtype(np.longdouble).itemsize != 8 else []),
)
def test_additional_profile_dtype_rejections(case: Case, dtype: str) -> None:
    error(
        "invalid_finite_bead_profile",
        declare(case),
        arguments(case, bead_profile=np.zeros(case.profile.shape, dtype=dtype)),
    )


@pytest.mark.parametrize("shape", [(), (24,), (1, 2, 3, 4), (2, 0, 4), (2, 3, 0)])
def test_additional_profile_rank_empty_rejections(case: Case, shape: tuple[int, ...]) -> None:
    error(
        "invalid_finite_bead_profile", declare(case), arguments(case, bead_profile=np.zeros(shape))
    )


@pytest.mark.parametrize(
    "axis,index", [("time", -1), ("time", 2), ("channel", 1), ("orientation", 2)]
)
def test_present_group_axis_bounds(case: Case, axis: str, index: int) -> None:
    acquisition = declare(case, grouped=True)
    group = {"time": 1, "channel": 0, "orientation": 1}
    group[axis] = index
    error("invalid_finite_bead_group", acquisition, arguments(case, group=group))


def test_huge_finite_phase_uses_represented_phasor_square(case: Case) -> None:
    generated = copy.deepcopy(case)
    generated.phases[0] = float(FMAX)
    check_truth(run(generated), generated)


# A04 SUPPLEMENTAL_POST_IMPLEMENTATION: public required-stage range witnesses.
def required_finite_bead_range_case(stage: Literal["normalized", "division"]) -> Case:
    """Supply real raw data, not a substituted phase/FFT/policy result."""
    amplitude = float(FMAX) / (64 if stage == "normalized" else 8)
    dc = np.array([0.0, 0.0, 1e-5 if stage == "normalized" else 1.0, 0.0]).reshape(1, 1, 4)
    first = np.array([amplitude, -amplitude, 0.0, 0.0], dtype=np.complex128).reshape(1, 1, 4)
    generated = algebra_case(dc, first)
    if stage == "division":
        generated.profile = np.array([9.0, 7.0, 0.0, 0.0]).reshape(1, 1, 4)
    return generated


def assert_required_finite_bead_range_policy(
    generated: Case,
    observed: simrecon.VolumePhaseComponents,
    stage: Literal["normalized", "division"],
) -> None:
    """Qualify a range witness from public stored observations, not scientific truth.

    The public separator's numerical domain permits mass cancellation. Its
    observed mass is a policy-applicability observation; no local BLAS bits or
    tight mass accuracy are promised. A failed applicability assertion requires
    witness/backend diagnosis, not an automatic finite-calibration bug finding.
    """
    mass = exact_mass(observed.dc)
    assert mass > 0, "F25 witness needs positive observed mass; diagnose applicability"
    eps, quantum = Fraction(1, 2**52), Fraction(1, 2**1074)
    maximum = Fraction.from_float(float(FMAX))
    rows = (observed.dc, observed.c1, observed.c2)
    lambdas = []
    allowances = []
    for row in rows:
        assert np.all(np.isfinite(row.real)) and np.all(np.isfinite(row.imag))
        lam = (
            sum(
                (
                    Fraction.from_float(float(abs(value.real)))
                    + Fraction.from_float(float(abs(value.imag)))
                    for value in row.flat
                ),
                Fraction(),
            )
            / mass
        )
        lambdas.append(lam)
        allowances.append(512 * 4 * eps * lam + 16 * 4 * quantum)
        scale = max(float(np.max(np.abs(row.real))), float(np.max(np.abs(row.imag)))) or 1.0
        scaled = np.empty(row.shape, dtype=np.complex128)
        scaled.real, scaled.imag = row.real / scale, row.imag / scale
        # Genuine native scaled transforms are finite. The expected range code
        # concerns restoration/division, not a manufactured dependency failure.
        transformed = np.fft.fftn(scaled)
        assert np.all(np.isfinite(transformed.real))
        assert np.all(np.isfinite(transformed.imag))

    # The real Nyquist Fourier sum is exact for every represented sample,
    # including any observed phase residual. No product FFT supplies this value.
    nyquist = (
        sum(
            (
                Fraction.from_float(float(value.real)) * (1 if i % 2 == 0 else -1)
                for i, value in enumerate(observed.c1.flat)
            ),
            Fraction(),
        )
        / mass
    )
    applied, _ = normalized_profile(generated.profile)
    profile = np.fft.fftshift(np.fft.fftn(applied))
    assert certificate(profile, generated.profile, 0.1)
    if stage == "normalized":
        assert np.array_equal(profile, np.ones((1, 1, 4), dtype=np.complex128))
        lower = abs(nyquist) - allowances[1]
    else:
        target = np.array([0.125 + 0j, 9 / 16 + 7j / 16, 1 + 0j, 9 / 16 - 7j / 16])
        assert np.array_equal(profile.reshape(-1), target)
        # |DFT(a)/S| <= Lambda. Thus every normalized A component, including
        # its allowance, is finite before the Nyquist division by exactly 1/8.
        assert all(
            lam + allowance < maximum for lam, allowance in zip(lambdas, allowances, strict=True)
        ), "F25 division witness needs finite normalized A; diagnose applicability"
        mu, minimum = Fraction(1, 8), Fraction.from_float(0.1)
        eta = 128 * 4 * eps + 4 * 4 * quantum
        upper, da = lambdas[1], allowances[1]
        dq = da / mu + upper * eta / (minimum * mu)
        dq += 128 * eps * (upper + da) / mu + 16 * quantum
        delta = dq + 128 * eps * (upper / mu + dq) + 16 * quantum
        # Nyquist recentering is +/-1 at every possible grid origin. Even the
        # conservative final spectral allowance cannot make its real part finite.
        lower = abs(nyquist) / mu - delta
    assert lower > maximum, "F25 range margin not certified; diagnose public-stage applicability"


@pytest.mark.parametrize("stage", ["normalized", "division"])
def test_independent_required_finite_bead_range_witness(
    stage: Literal["normalized", "division"],
) -> None:
    """Separate independent phase accuracy from observed range applicability."""
    generated = required_finite_bead_range_case(stage)
    acquisition = declare(generated)
    assert acquisition.axes == ("orientation", "phase", "z", "y", "x")
    assert acquisition.acquisition_kind == "sim_beads"
    assert np.all(np.isfinite(acquisition.data))
    assert np.array_equal(generated.images[:, 0, 0, 0], -generated.images[:, 0, 0, 1])
    assert np.linalg.cond(represented_basis(generated.phases)) <= 10
    before = caller_state((acquisition, generated.phases, generated.profile))
    observed = simrecon.separate_volume_phases(acquisition.data[0], phases_rad=generated.phases)
    with localcontext() as context:
        context.prec = PRECISION
        truth = fit(generated.images, generated.phases)
        for voxel in range(4):
            magnitude = max(abs(d(value)) for value in generated.images[:, 0, 0, voxel])
            allowance = 8192 * len(generated.phases) * EPS * magnitude + 8 * Q0
            for actual, row in zip((observed.dc, observed.c1, observed.c2), truth, strict=True):
                target = row[voxel]
                assert max(abs(target.re), abs(target.im)) + allowance < FMAX
                assert abs(d(actual.flat[voxel].real) - target.re) <= allowance
                assert abs(d(actual.flat[voxel].imag) - target.im) <= allowance
    assert_required_finite_bead_range_policy(generated, observed, stage)
    assert caller_state((acquisition, generated.phases, generated.profile)) == before


@pytest.mark.parametrize("stage", ["normalized", "division"])
def test_raw_finite_bead_required_stage_range_rejection(
    stage: Literal["normalized", "division"],
) -> None:
    """Supplemental public range regression; no original product-red claim."""
    generated = required_finite_bead_range_case(stage)
    acquisition = declare(generated)
    kwargs = arguments(generated)
    before = caller_state((acquisition, kwargs))
    observed = simrecon.separate_volume_phases(acquisition.data[0], phases_rad=generated.phases)
    assert_required_finite_bead_range_policy(generated, observed, stage)
    error("unrepresentable_finite_bead_response", acquisition, kwargs)
    assert caller_state((acquisition, kwargs)) == before
