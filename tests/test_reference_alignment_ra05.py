"""RA05 corrected-pair calibration and matched physical-frequency consumption.

All numerical truth comes from the companion finite-sum fixture. Primitive
contracts retain their full suites; these tests target adapter composition.
"""

import warnings
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from fractions import Fraction
from typing import Any, cast

import numpy as np
import pytest

import simrecon as sc
from reference_alignment_ra05_fixture import (
    EPS,
    direct_dft,
    exact_mass,
    expected_response,
    expected_samples,
    extended,
    fit_components,
    interpolate,
    make_case,
    normalized_profile,
    phase_basis,
    phasor,
    response_budget,
)


@pytest.fixture(scope="session")
def api():
    required = (
        "AlignmentBeadCalibration",
        "calibrate_alignment_bead",
        "sample_alignment_order_transfer",
    )
    missing = [name for name in required if not hasattr(sc, name)]
    if missing:
        pytest.fail("RA05 feature absence (setup evidence, not product-red): " + ", ".join(missing))
    return sc


@pytest.fixture(scope="session")
def case():
    return make_case()


def pair_for(case, *, all_groups=False, no_z=False, scale=1.0, equalization="disabled"):
    """Use real raw declaration/correction with nonidentity camera/exposure."""
    bead_images = np.stack((case.exposures * 0.3 + 1.0, case.exposures * scale))
    axes = ["orientation", "phase", "z", "y", "x"]
    if all_groups:
        bead_images = bead_images[None, None]
        axes = ["time", "channel", *axes]
    if no_z:
        bead_images = np.take(bead_images, 0, axis=axes.index("z"))
        axes.remove("z")
    # Maps vary by pixel/phase; all operations remain exactly the RA04 sequence.
    coords = np.indices(bead_images.shape)
    offset = 7.0 + coords[-1] / 8
    response = 2.0 + coords[-2] / 8
    exposure = 0.5 + coords[axes.index("phase")] / 8
    raw = np.asarray(offset + response * exposure * bead_images, dtype=np.float64)
    declared = sc.declare_acquisition(
        raw,
        config={
            "version": 1,
            "axes": axes,
            "acquisition_kind": "sim_beads",
            "intensity_unit": "bead_counts",
            "calibration_id": "opaque-bead-id",
            "sampling_um": {"z": 9.0 if not no_z else None, "y": 8.0, "x": 7.0},
            "nominal_phases_rad": np.zeros(
                bead_images.shape[:-3] if not no_z else bead_images.shape[:-2]
            ).tolist(),
        },
        original_metadata={
            "caller": ["bead", {"setting": 17}],
            "noise": "not removed by subtraction",
        },
    )
    # Specimen intentionally has different groups, phase count, shape and sampling.
    specimen = sc.declare_acquisition(
        np.arange(30, dtype=float).reshape(1, 5, 1, 2, 3) - 12,
        config={
            "version": 1,
            "axes": ["orientation", "phase", "z", "y", "x"],
            "acquisition_kind": "specimen_sim",
            "intensity_unit": "specimen_counts",
            "calibration_id": "different-opaque-id",
        },
    )
    pair = sc.correct_alignment_pair(
        specimen,
        bead=declared,
        mode="declared",
        output_unit="reference_signal",
        gauge_source="explicit shared gauge",
        specimen_exposure_factor=2.0,
        bead_exposure_factor=exposure,
        reference_sum_equalization=equalization,
        specimen_offset=-3.0,
        specimen_response=4.0,
        bead_offset=offset,
        bead_response=response,
    )
    corrected = ((raw - offset) / response) / exposure
    selected = corrected[(0, 0, 1) if all_groups else (1,)]
    return pair, selected


def estimated_pair_for(case):
    """Prepare a real estimated pair with inspectable nonzero noise statistics."""
    dark = np.array([[[-2, 0], [1, 3]], [[-1, 1], [2, 4]], [[0, 2], [3, 5]]], dtype=float)
    blank = np.array([[[6, 8], [10, 12]], [[8, 10], [12, 14]], [[4, 6], [8, 10]]], dtype=float)
    flat = np.array([[[16, 17], [18, 19]], [[18, 19], [20, 21]], [[14, 15], [16, 17]]], dtype=float)
    estimate = sc.estimate_scalar_camera(
        dark, blank_counts=blank, flat_counts=flat, source=" stationary camera ensemble "
    )
    # These returned statistics define the declared relative-count gauge. They
    # are not independent scientific truth about an instrument or estimator.
    baseline, contrast = float(estimate.means_counts[1]), estimate.contrast_counts
    bead_counts = baseline + contrast * np.stack((case.exposures * 0.5, case.exposures))
    specimen_counts = baseline + contrast * np.arange(30, dtype=float).reshape(1, 5, 1, 2, 3) / 16
    config = {
        "version": 1,
        "axes": ["orientation", "phase", "z", "y", "x"],
        "intensity_unit": "stationary_counts",
    }
    bead = sc.declare_acquisition(bead_counts, config={**config, "acquisition_kind": "sim_beads"})
    specimen = sc.declare_acquisition(
        specimen_counts, config={**config, "acquisition_kind": "specimen_sim"}
    )
    pair = sc.correct_alignment_pair(
        specimen,
        bead=bead,
        mode="estimated",
        output_unit="reference_flat_relative",
        gauge_source=" caller stationary camera pairing ",
        specimen_exposure_factor=1.0,
        bead_exposure_factor=1.0,
        reference_sum_equalization="disabled",
        camera_estimate=estimate,
    )
    return estimate, pair


def calibrate(api, pair, case, **changes):
    kwargs = dict(
        group={"orientation": 1},
        phases_rad=case.phases,
        voxel_size_um=case.spacing,
        calibration_carrier_bins=case.carrier,
        bead_mode="discrete_profile",
        bead_profile=case.profile,
        min_profile_transfer=0.15,
        source=" calibration source ",
    )
    kwargs.update(changes)
    return api.calibrate_alignment_bead(pair, **kwargs)


def sample(api, calibration, **changes):
    kwargs = dict(
        order=1,
        frequencies_zyx_per_um=np.array([[0.0, 0.0, 0.0]]),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source=" specimen physical pairing ",
    )
    kwargs.update(changes)
    return api.sample_alignment_order_transfer(calibration, **kwargs)


def reject(code, function, *args, **kwargs):
    with pytest.raises(sc.SimreconError) as error:
        function(*args, **kwargs)
    assert error.value.code == code


@pytest.fixture(scope="session")
def calibrated(api, case):
    pair, images = pair_for(case)
    result = calibrate(api, pair, case)
    components = fit_components(images, case.phases)
    expected, profile, localization = expected_response(
        components, case.profile, case.carrier, case.anchor
    )
    budget = response_budget(images, components, case.profile, 0.15)
    return result, pair, images, components, expected, profile, localization, budget


def assert_close(actual, expected, allowance):
    error = np.abs(np.asarray(actual, dtype=np.clongdouble) - expected)
    assert np.all(error <= allowance), (
        f"independent error {np.max(error)} exceeds allowance {np.max(allowance)}"
    )


def arrays_in(value):
    if isinstance(value, np.ndarray):
        return [value]
    if isinstance(value, dict):
        return [array for item in value.values() for array in arrays_in(item)]
    if isinstance(value, (list, tuple)):
        return [array for item in value for array in arrays_in(item)]
    if hasattr(value, "__dataclass_fields__"):
        return [array for field in fields(value) for array in arrays_in(getattr(value, field.name))]
    return []


def assert_snapshot_equal(actual, expected):
    if isinstance(expected, np.ndarray):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape
        assert np.array_equal(actual, expected)
    elif isinstance(expected, dict):
        assert type(actual) is dict and actual.keys() == expected.keys()
        for key, value in expected.items():
            assert_snapshot_equal(actual[key], value)
    elif isinstance(expected, (list, tuple)):
        assert type(actual) is type(expected) and len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            assert_snapshot_equal(a, b)
    else:
        assert actual == expected


def assert_camera_snapshot_preserved(snapshot, estimate):
    """Check public field preservation without prescribing snapshot packaging."""
    for field in fields(estimate):
        actual = (
            snapshot[field.name] if isinstance(snapshot, dict) else getattr(snapshot, field.name)
        )
        assert_snapshot_equal(actual, getattr(estimate, field.name))


def test_estimated_camera_fixture_public_preparation(case):
    estimate, pair = estimated_pair_for(case)
    assert isinstance(estimate, sc.ScalarCameraEstimate)
    assert estimate.contrast_counts > 0
    assert estimate.variances_counts2[1] > estimate.variances_counts2[2] > 0
    assert np.all(estimate.empirical_mean_se_counts > 0)
    assert estimate.gain_counts_per_e is None
    assert "nonpositive_variance_contrast" in estimate.information_codes
    assert pair.status == "corrected" and pair.mode == "estimated"
    assert pair.output_unit == "reference_flat_relative"
    assert pair.specimen is not None and pair.bead is not None
    assert pair.specimen.input_unit == pair.bead.input_unit == "stationary_counts"
    assert pair.specimen_exposure_factor == pair.bead_exposure_factor == 1.0
    assert_camera_snapshot_preserved(pair.camera_estimate, estimate)
    for a in arrays_in(pair.camera_estimate):
        for b in arrays_in(estimate):
            assert not np.shares_memory(a, b)


def test_estimated_camera_record_preserved_without_alias_or_uncertainty_reinterpretation(api, case):
    estimate, pair = estimated_pair_for(case)
    expected = deepcopy(estimate)
    result = calibrate(api, pair, case)
    again = calibrate(api, pair, case)
    correction = result.provenance["correction"]
    snapshot = correction["camera_estimate"]
    other = again.provenance["correction"]["camera_estimate"]
    assert correction["mode"] == "estimated"
    assert result.provenance["output_unit"] == "reference_flat_relative"
    assert result.provenance["gauge_source"] == pair.gauge_source
    assert_camera_snapshot_preserved(snapshot, expected)
    assert_camera_snapshot_preserved(other, expected)
    assert_camera_snapshot_preserved(estimate, expected)
    assert_camera_snapshot_preserved(pair.camera_estimate, expected)
    assert snapshot is not pair.camera_estimate and snapshot is not other
    for a in arrays_in(snapshot):
        for b in arrays_in(estimate) + arrays_in(pair.camera_estimate) + arrays_in(again):
            assert not np.shares_memory(a, b)
        for b in arrays_in(result.components) + arrays_in(result.response):
            assert not np.shares_memory(a, b)
    # Mutate only after every public call. No corrupted estimate is ever passed
    # to an estimator, pair correction or calibration operation.
    for index, array in enumerate(arrays_in(estimate)):
        array.fill(-100 - index)
    for index, array in enumerate(arrays_in(pair.camera_estimate)):
        array.fill(-200 - index)
    if isinstance(pair.camera_estimate, dict):
        pair.camera_estimate["source"] = "changed after calibration"
    assert_camera_snapshot_preserved(snapshot, expected)
    assert_camera_snapshot_preserved(other, expected)
    for index, array in enumerate(arrays_in(snapshot)):
        array.fill(-300 - index)
    if isinstance(snapshot, dict):
        snapshot["source"] = "changed first result only"
    assert_camera_snapshot_preserved(other, expected)


def test_independent_fixture_exposures_and_discriminating_controls(case):
    """Validate observer algebra before an absent/future RA05 API is involved."""
    basis = phase_basis(case.phases)
    assert np.linalg.cond(basis) < 10
    predicted = np.asarray(
        [
            case.physical_components[0].real
            + 2 * case.physical_components[1].real * row[1]
            - 2 * case.physical_components[1].imag * row[2]
            + 2 * case.physical_components[2].real * row[3]
            - 2 * case.physical_components[2].imag * row[4]
            for row in basis
        ]
    )
    assert_close(case.exposures, predicted, 256 * EPS * np.max(abs(case.exposures)))
    fitted = fit_components(case.exposures, case.phases)
    assert_close(fitted, case.physical_components, 512 * EPS * np.max(abs(case.exposures)))
    expected, p, v0 = expected_response(fitted, case.profile, case.carrier, case.anchor)
    assert np.min(abs(p)) > 0.15 + 128 * case.profile.size * EPS
    assert np.unravel_index(np.argmax(fitted[0].real), case.shape) != case.anchor
    assert np.unravel_index(np.argmax(v0), case.shape) == case.anchor
    assert np.max(abs(expected[1].imag)) > 0.01
    # Independent physical H_m, with retained bead and calibration-phase gauge.
    rho = sum(
        (
            Fraction(k * b, n)
            for k, b, n in zip(case.carrier, case.anchor[1:], case.shape[1:], strict=False)
        ),
        Fraction(),
    )
    for m in range(3):
        truth = (
            direct_dft(case.kernels[m])
            * phasor(m * rho)
            * np.exp(np.clongdouble(-1j) * m * extended(case.alpha))
        )
        assert_close(expected[m], truth, 1024 * EPS * np.max(abs(case.exposures)))
    # Wrong compensation shifts and uncorrected interpolation differ materially.
    wrong_second = direct_dft(fitted[2]) / p / np.sum(fitted[0].real)
    assert np.max(abs(wrong_second) - abs(expected[2])) > 0.001


def test_independent_fixture_exact_interpolation_control():
    values = np.empty((3, 3, 4, 5), dtype=np.clongdouble)
    for z, y, x in np.ndindex(values.shape[1:]):
        fz, fy, fx = (z - 1) / 1.5, y - 2, (x - 2) / 0.625
        values[:, z, y, x] = (1 + 0.2j) + (0.3 - 0.1j) * fz + 0.07j * fy * fx
    points = np.array([[0.125, -0.25, 0.375], [-0.25, 0.125, -0.5]])
    expected = (1 + 0.2j) + (0.3 - 0.1j) * points[:, 0] + 0.07j * points[:, 1] * points[:, 2]
    observed = expected_samples(values, (0.5, 0.25, 0.125), (0, 0, 0), (0, 0), (0, 0), 0, 0, points)
    assert_close(observed, expected, 32 * EPS)


def test_independent_fixture_camera_pair_boundary(case):
    for options in ({}, {"all_groups": True}, {"no_z": True}):
        pair, expected = pair_for(
            case, all_groups=options.get("all_groups", False), no_z=options.get("no_z", False)
        )
        assert pair.bead is not None and pair.specimen is not None
        selector = (0, 0, 1) if options.get("all_groups") else (1,)
        assert np.array_equal(pair.bead.data[selector], expected)
        assert pair.specimen.data.shape != pair.bead.data.shape


def test_independent_fixture_native_division_precedes_interpolation(case):
    fitted = fit_components(case.exposures, case.phases)
    response, profile, _ = expected_response(fitted, case.profile, case.carrier, case.anchor)
    points = np.array([[0.125, -0.25, 0.375], [-0.125, 0.125, -0.5]])
    # A tempting wrong implementation interpolates numerator and denominator
    # separately, then divides. Interpolation and division do not commute.
    shifted = np.roll(profile, (case.carrier[0], case.carrier[1]), axis=(1, 2))
    wrong = interpolate(response[1] * shifted, case.spacing, points) / interpolate(
        shifted, case.spacing, points
    )
    truth = interpolate(response[1], case.spacing, points)
    assert np.max(abs(truth - wrong)) > 0.001


@pytest.mark.parametrize("phase_kind", ["repeated", "huge", "off_model"])
def test_represented_actual_phase_domains_and_least_squares_projection(api, phase_kind):
    case = make_case(shape=(1, 2, 3), kind="point")
    phases = case.phases.copy()
    if phase_kind == "repeated":
        phases[-1] = phases[0]
    elif phase_kind == "huge":
        phases[0] = np.finfo(float).max
    basis = phase_basis(phases)
    assert np.linalg.cond(basis) < 10
    c = case.physical_components
    images = np.asarray(
        [
            c[0].real
            + 2 * c[1].real * row[1]
            - 2 * c[1].imag * row[2]
            + 2 * c[2].real * row[3]
            - 2 * c[2].imag * row[4]
            for row in basis
        ],
        dtype=float,
    )
    if phase_kind == "off_model":
        images[0, 0, 0, 0] += 0.125
    case = replace(case, phases=phases, exposures=images)
    pair, corrected = pair_for(case)
    result = calibrate(api, pair, case)
    expected = fit_components(corrected, phases)
    bound = 8192 * len(phases) * EPS * np.max(abs(corrected))
    for m, observed in enumerate(
        (result.components.dc, result.components.c1, result.components.c2)
    ):
        assert_close(observed, expected[m], bound * (1 if m == 0 else np.sqrt(2)))


def test_overflowing_original_dc_mass_still_has_finite_response(api):
    case = make_case(shape=(1, 1, 2), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    maximum = np.finfo(float).max
    dc = np.array([[[maximum * 0.75, maximum * 0.5]]])
    assert pair.bead is not None
    pair.bead.data[1] = np.broadcast_to(dc, case.exposures.shape)
    result = calibrate(api, pair, case)
    assert exact_mass(result.components.dc) > Fraction(maximum)
    # Exact ideal two-site Fourier values, centered at the first sample.
    s = exact_mass(dc)
    side = extended((Fraction(float(dc[0, 0, 0])) - Fraction(float(dc[0, 0, 1]))) / s)
    expected = np.array([[[side, 1.0]]])
    sep_relative = 8192 * len(case.phases) * EPS
    bound = 8 * sep_relative + 512 * dc.size * EPS
    assert_close(result.response.values[0], expected, bound)
    assert result.response.values[0, 0, 0, 1] == 1 + 0j


def test_sampler_component_safe_extremes_and_real_range_failure(api):
    case = make_case(shape=(1, 1, 1), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    result = calibrate(api, pair, case)
    maximum = np.finfo(float).max
    result.response.values[:] = complex(maximum, maximum)
    # Identity complete-node path copies components despite an infinite magnitude.
    copied = sample(api, result, order=2, phase_reference_shift_rad=-0.0)
    assert copied.values[0].real == maximum and copied.values[0].imag == maximum
    reflected = sample(api, result, order=-2)
    assert reflected.values[0].real == maximum and reflected.values[0].imag == -maximum
    result.response.values[:] = complex(maximum * 0.75, maximum * 0.75)
    reject(
        "unrepresentable_empirical_interpolation",
        sample,
        api,
        result,
        order=1,
        phase_reference_shift_rad=np.pi / 4,
    )


def test_public_records_and_required_bindings(api, calibrated, case):
    result, pair, *_ = calibrated
    assert isinstance(result, api.AlignmentBeadCalibration)
    assert [f.name for f in fields(result)] == ["components", "response", "provenance"]
    assert isinstance(result.components, sc.VolumePhaseComponents)
    assert isinstance(result.response, sc.EmpiricalVolumeResponse)
    with pytest.raises(FrozenInstanceError):
        result.response = None
    kwargs = dict(
        group={"orientation": 1},
        phases_rad=case.phases,
        voxel_size_um=case.spacing,
        calibration_carrier_bins=case.carrier,
        bead_mode="point",
        bead_profile=None,
        min_profile_transfer=None,
        source="s",
    )
    for key in kwargs:
        with pytest.raises(TypeError):
            api.calibrate_alignment_bead(pair, **{k: v for k, v in kwargs.items() if k != key})
    with pytest.raises(TypeError):
        api.calibrate_alignment_bead(pair, {}, **kwargs)
    sampled = sample(api, result)
    assert isinstance(sampled, sc.EmpiricalFrequencySamples)
    assert [f.name for f in fields(sampled)] == [
        "values",
        "frequencies_zyx_per_um",
        "order",
        "source",
        "provenance",
    ]
    with pytest.raises(FrozenInstanceError):
        cast(Any, sampled).values = None

    class CalibrationSubclass(api.AlignmentBeadCalibration):
        pass

    subclass = CalibrationSubclass(
        **{field.name: getattr(result, field.name) for field in fields(result)}
    )
    sample(api, subclass)
    consumer = dict(
        order=0,
        frequencies_zyx_per_um=np.zeros((1, 3)),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source="s",
    )
    for key in consumer:
        with pytest.raises(TypeError):
            api.sample_alignment_order_transfer(
                result, **{k: v for k, v in consumer.items() if k != key}
            )


def test_corrected_arrays_compensation_common_mass_and_native_frequencies(api, calibrated, case):
    result, _, images, components, expected, profile, localization, budget = calibrated
    sep = 8192 * len(images) * EPS * np.max(abs(images))
    for m, actual in enumerate((result.components.dc, result.components.c1, result.components.c2)):
        assert_close(actual, components[m], sep * (1 if m == 0 else np.sqrt(2)))
        assert_close(result.response.values[m], expected[m], budget[m])
    assert result.response.origin_zyx == case.anchor
    assert result.response.voxel_size_um == case.spacing
    assert result.response.values[(0, *(n // 2 for n in case.shape))] == 1 + 0j
    assert_close(result.provenance["profile_transfer"], profile, 128 * case.profile.size * EPS)
    # Localization is unnormalized again only by mistake; target remains h[n-b].
    assert_close(result.provenance["compensated_dc"], localization, budget[0] * 2)
    for n, d, vector in zip(
        case.shape,
        case.spacing,
        (result.response.fz_per_um, result.response.fy_per_um, result.response.fx_per_um),
        strict=False,
    ):
        truth = np.array(
            [extended(Fraction(k) / (n * Fraction(d))) for k in range(-(n // 2), (n + 1) // 2)]
        )
        assert_close(vector, truth, 8 * EPS * abs(truth) + extended(Fraction(1, 2**1074)))


@pytest.mark.parametrize(
    "kind,mode",
    [("point", "point"), ("point", "discrete_profile"), ("translated", "discrete_profile")],
)
def test_point_limit_and_translated_profile_anchor(api, kind, mode):
    case = make_case(shape=(1, 3, 4), kind=kind)
    pair, images = pair_for(case)
    result = calibrate(
        api,
        pair,
        case,
        bead_mode=mode,
        bead_profile=None if mode == "point" else case.profile,
        min_profile_transfer=None if mode == "point" else 0.15,
    )
    components = fit_components(images, case.phases)
    expected, _, _ = expected_response(components, case.profile, case.carrier, case.anchor)
    budget = response_budget(images, components, case.profile, 0.15)
    assert result.response.origin_zyx == case.anchor
    for m in range(3):
        assert_close(result.response.values[m], expected[m], budget[m])
    if mode == "point":
        assert all(
            result.provenance[key] is None
            for key in (
                "bead_profile",
                "min_profile_transfer",
                "profile_transfer",
                "compensated_dc",
            )
        )
        assert result.provenance["response_gauge"] == "observed_dc_peak_with_supplied_phase_origin"
    elif kind == "point":
        assert np.array_equal(
            result.provenance["profile_transfer"], np.ones(case.shape, dtype=complex)
        )


def test_tied_raw_peak_is_not_an_early_rejection(api):
    case = make_case(shape=(1, 1, 5), carrier=(0, 0), alpha=0)
    profile = np.array([[[0.0, 2.0, 2.0, 1.0, 0.0]]])
    images = np.broadcast_to(profile, (len(case.phases), *profile.shape)).copy()
    case = replace(case, profile=profile, exposures=images, anchor=(0, 0, 0))
    pair, _ = pair_for(case)
    # Preserve an exact represented tie through a valid mutable corrected record.
    assert pair.bead is not None
    pair.bead.data[1] = images
    result = calibrate(api, pair, case, min_profile_transfer=0.1)
    assert result.response.origin_zyx == (0, 0, 0)
    bound = response_budget(images, fit_components(images, case.phases), profile, 0.1)[0]
    assert_close(result.response.values[0], np.ones(profile.shape), bound)


def test_explicit_bead_groups_not_specimen_groups_and_signed_mutation(api, case):
    pair, images = pair_for(case, all_groups=True)
    result = calibrate(api, pair, case, group={"time": 0, "channel": 0, "orientation": 1})
    assert result.provenance["group"] == {"time": 0, "channel": 0, "orientation": 1}
    assert_close(
        result.components.dc,
        fit_components(images, case.phases)[0],
        8192 * len(images) * EPS * np.max(abs(images)),
    )
    # Signed corrected samples are accepted directly, not revalidated as raw intensity.
    point = make_case(shape=(1, 1, 3), kind="point", carrier=(0, 0))
    signed_pair, _ = pair_for(point)
    assert signed_pair.bead is not None
    signed_pair.bead.data[1] = np.broadcast_to([[[2.0, -0.25, 0.125]]], point.exposures.shape)
    signed = calibrate(
        api, signed_pair, point, bead_mode="point", bead_profile=None, min_profile_transfer=None
    )
    assert signed.components.dc[0, 0, 1] < 0
    assert np.max(abs(signed.response.values[0])) > 1


@pytest.mark.parametrize(
    "group",
    [
        None,
        [],
        {"orientation": True},
        {"orientation": np.int64(1)},
        {"orientation": -1},
        {"orientation": 2},
        {},
        {"orientation": 1, "channel": 0},
    ],
)
def test_group_rejections(api, case, group):
    pair, _ = pair_for(case)
    reject("invalid_alignment_bead_group", calibrate, api, pair, case, group=group)


def test_present_singleton_groups_and_explicit_z(api):
    case = make_case(shape=(1, 1, 3), kind="point")
    pair, _ = pair_for(case, all_groups=True)
    reject("invalid_alignment_bead_group", calibrate, api, pair, case, group={"orientation": 1})
    calibrate(api, pair, case, group={"time": 0, "channel": 0, "orientation": 1})
    without_z, _ = pair_for(case, no_z=True)
    reject("invalid_alignment_bead_axes", calibrate, api, without_z, case)


def test_unavailable_and_wrong_records(api, case, calibrated):
    pair, _ = pair_for(case)
    # RA04 publicly supports this complete unavailable value outcome.
    unavailable, _ = pair_for(case, equalization="per_frame_sum")
    reject("alignment_bead_correction_unavailable", calibrate, api, unavailable, case)
    for wrong in (None, pair.bead, calibrated[0].response):
        reject("invalid_alignment_bead_calibration", calibrate, api, wrong, case)
        reject("invalid_alignment_bead_calibration", sample, api, wrong)

    class PairSubclass(sc.AlignmentCameraPair):
        pass

    subclass = PairSubclass(**{field.name: getattr(pair, field.name) for field in fields(pair)})
    calibrate(api, subclass, case)


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"bead_mode": "sphere"}, "invalid_alignment_bead_calibration"),
        ({"bead_mode": "point"}, "invalid_alignment_bead_calibration"),
        ({"bead_profile": None}, "invalid_alignment_bead_calibration"),
        ({"min_profile_transfer": None}, "invalid_alignment_bead_calibration"),
        ({"source": "  "}, "invalid_otf_source"),
        ({"calibration_carrier_bins": (1.0, 0)}, "invalid_empirical_transfer_carrier"),
        ({"calibration_carrier_bins": (True, 0)}, "invalid_empirical_transfer_carrier"),
        ({"calibration_carrier_bins": np.array([1, 0])}, "invalid_empirical_transfer_carrier"),
        ({"voxel_size_um": (0.5, 0, 0.1)}, "invalid_otf_voxel_size"),
        ({"voxel_size_um": (True, 1, 1)}, "invalid_otf_voxel_size"),
        ({"voxel_size_um": (np.nextafter(0.0, 1.0), 1, 1)}, "unrepresentable_otf_frequencies"),
        ({"phases_rad": [0, 1, 2, 3, 4, 5, 6]}, "invalid_volume_phase_angles"),
        ({"phases_rad": np.zeros(7, dtype=bool)}, "invalid_volume_phase_angles_dtype"),
        ({"phases_rad": np.zeros(5)}, "invalid_volume_phase_angles_shape"),
        ({"phases_rad": np.full(7, np.nan)}, "nonfinite_volume_phase_angles"),
        ({"phases_rad": np.zeros(7)}, "rank_deficient_volume_phases"),
    ],
)
def test_calibration_declaration_errors_through_adapter(api, case, changes, code):
    pair, _ = pair_for(case)
    reject(code, calibrate, api, pair, case, **changes)


@pytest.mark.parametrize(
    "problem", ["list", "subclass", "float32", "complex", "shape", "negative", "nan", "zero"]
)
def test_profile_grammar_through_adapter(api, case, problem):
    profile = case.profile.copy()
    if problem == "list":
        profile = profile.tolist()
    elif problem == "subclass":
        profile = profile.view(type("ProfileSubclass", (np.ndarray,), {}))
    elif problem == "float32":
        profile = profile.astype(np.float32)
    elif problem == "complex":
        profile = profile.astype(complex)
    elif problem == "shape":
        profile = profile[:, :, :-1]
    elif problem == "negative":
        profile.flat[0] = -1
    elif problem == "nan":
        profile.flat[0] = np.nan
    else:
        profile.fill(0)
    pair, _ = pair_for(case)
    reject("invalid_finite_bead_profile", calibrate, api, pair, case, bead_profile=profile)


@pytest.mark.parametrize("minimum", [True, 0.0, -1, 1.01, np.inf, np.nan, np.array(0.1), "0.1"])
def test_threshold_grammar_through_adapter(api, case, minimum):
    pair, _ = pair_for(case)
    reject(
        "invalid_finite_bead_transfer_threshold",
        calibrate,
        api,
        pair,
        case,
        min_profile_transfer=minimum,
    )


@pytest.mark.parametrize(
    "profile,minimum,accepted",
    [
        (np.array([[[1.0, 0.0]]]), 1.0, True),
        (np.array([[[0.0, 1.0]]]), 1.0, False),
        (np.array([[[0.0, 1.0]]]), 0.9, True),
        (np.array([[[1.0, 1.0]]]), 0.01, False),
        (np.array([[[1.0, 0.99]]]), 0.1, False),
    ],
)
def test_full_grid_certificate_zero_numerators_and_identity_equality(
    api, profile, minimum, accepted
):
    case = make_case(shape=profile.shape, kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    # Constant exposures yield only zero-order DC. Unused nodes still certify.
    assert pair.bead is not None
    pair.bead.data[1] = 1.0
    if accepted:
        # Use a non-tied compensated peak for successful cases.
        pair.bead.data[1] = np.broadcast_to(np.array([[[2.0, 1.0]]]), case.exposures.shape)
        calibrate(api, pair, case, bead_profile=profile, min_profile_transfer=minimum)
    else:
        reject(
            "unstable_finite_bead_transfer",
            calibrate,
            api,
            pair,
            case,
            bead_profile=profile,
            min_profile_transfer=minimum,
        )


@pytest.mark.parametrize(
    "profile_layout",
    ["big_endian", "fortran", "readonly", "strided", "overflow_mass", "subnormal_mass"],
)
def test_profile_legitimate_layouts_and_exact_mass_extremes(api, profile_layout):
    case = make_case(shape=(1, 2, 3), kind="point", carrier=(0, 1))
    profile = case.profile.copy()
    if profile_layout == "big_endian":
        profile = profile.astype(">f8")
    elif profile_layout == "fortran":
        profile = np.asfortranarray(profile)
    elif profile_layout == "readonly":
        profile.flags.writeable = False
    elif profile_layout == "strided":
        padded = np.zeros((1, 2, 6))
        padded[..., ::2] = profile
        profile = padded[..., ::2]
    elif profile_layout == "overflow_mass":
        profile[0, 0, 0], profile[0, 0, 1] = np.finfo(float).max, np.finfo(float).max / 2
    else:
        profile *= np.nextafter(0.0, 1.0)
    pair, images = pair_for(case)
    # This is an algebraic valid-profile input; the physical profile need not match.
    result = calibrate(api, pair, case, bead_profile=profile, min_profile_transfer=0.1)
    expected, _, _ = expected_response(
        fit_components(images, case.phases), profile, case.carrier, result.response.origin_zyx
    )
    # Conditional origin only: this assertion claims accuracy at the computed origin.
    budget = response_budget(images, fit_components(images, case.phases), profile, 0.1)
    for m in range(3):
        assert_close(result.response.values[m], expected[m], budget[m])


def test_original_exact_mass_and_compensated_peak_failures(api):
    case = make_case(shape=(1, 1, 2), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    assert pair.bead is not None
    for dc in ([[[2.0, -3.0]]], [[[2.0, -2.0]]]):
        pair.bead.data[1] = np.broadcast_to(dc, case.exposures.shape)
        reject("nonpositive_empirical_response_mass", calibrate, api, pair, case)
    pair.bead.data[1] = 1.0
    reject("ambiguous_bead_peak", calibrate, api, pair, case)
    pair.bead.data[1] = -1.0
    reject(
        "no_positive_bead_peak",
        calibrate,
        api,
        pair,
        case,
        bead_mode="point",
        bead_profile=None,
        min_profile_transfer=None,
    )


def test_positive_common_scale_components_mass_and_response(api, case, calibrated):
    base, pair, *_ = calibrated
    # Supported mutable array edit preserves the valid corrected-record invariants.
    scaled_pair = replace(pair, bead=replace(pair.bead, data=pair.bead.data * 8))
    scaled = calibrate(api, scaled_pair, case)
    for name in ("dc", "c1", "c2"):
        sep = 16 * 8192 * len(case.phases) * EPS * np.max(abs(pair.bead.data[1]))
        assert_close(getattr(scaled.components, name), 8 * getattr(base.components, name), sep)
    assert_close(scaled.response.values, base.response.values, 2 * max(calibrated[-1]))
    masses = []
    for result in (base, scaled):
        record = result.provenance["dc_mass"]
        mass = Fraction(record["numerator"], record["denominator"])
        assert mass == exact_mass(result.components.dc)
        masses.append(mass)
    # Independent separations need not be bitwise homogeneous. Each dc real
    # coordinate has error <=8192*N*eps*max_p(abs(images[p,j]))+8*q0.
    # The represented observations here scale exactly by eight, so triangle
    # inequality gives |S8-8*S1| <= sum_j(e8,j+8*e1,j).
    coefficient = Fraction(8192 * len(case.phases), 2**52)
    floor = Fraction(8, 2**1074)
    bound = Fraction()
    for base_peak, scaled_peak in zip(
        np.max(abs(pair.bead.data[1]), axis=0).flat,
        np.max(abs(scaled_pair.bead.data[1]), axis=0).flat,
        strict=True,
    ):
        e1 = coefficient * Fraction(float(base_peak)) + floor
        e8 = coefficient * Fraction(float(scaled_peak)) + floor
        bound += e8 + 8 * e1
    assert abs(masses[1] - 8 * masses[0]) <= bound


@pytest.mark.parametrize("order", [-2, -1, 0, 1, 2])
def test_distinct_specimen_grid_detector_queries_and_native_compensation(
    api, calibrated, case, order
):
    result, _, _, _, expected, _, _, budget = calibrated
    # Specimen grid: (5,7,9), spacing (0.4,0.5,0.25), qs=(2/7,-4/9).
    object_points = np.array([[0.05, -0.0625, 0.125], [-0.125, 0.125, -0.25]])
    qs = np.array([0, 2 / 7, -4 / 9])
    detector = np.asarray(object_points + order * qs, dtype=np.float64)
    offset, delta = (2, -3), -0.31
    observed = sample(
        api,
        result,
        order=order,
        frequencies_zyx_per_um=detector,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=delta,
    )
    truth = expected_samples(
        expected, case.spacing, case.anchor, case.carrier, offset, delta, order, detector
    )
    allowance = budget[abs(order)] + 1024 * EPS * np.max(
        abs(expected[abs(order)].real) + abs(expected[abs(order)].imag)
    )
    assert_close(observed.values, truth, allowance)
    if order:
        wrong = expected_samples(
            expected, case.spacing, case.anchor, case.carrier, offset, delta, order, object_points
        )
        assert np.max(abs(truth - wrong)) > 0.001
    assert np.array_equal(observed.frequencies_zyx_per_um, detector)
    assert set(observed.provenance) == {
        "sampling",
        "source_shape_zyx",
        "source_voxel_size_um",
        "source_origin_zyx",
        "calibration_carrier_bins",
        "coordinate_offset_yx",
        "phase_reference_shift_rad",
    }
    assert observed.provenance["calibration_carrier_bins"] == case.carrier
    assert observed.provenance["source_shape_zyx"] == case.shape
    assert observed.source == " specimen physical pairing "


def test_physical_movement_storage_roll_and_phase_reference_sign_order_two(api):
    base_case = make_case(shape=(3, 4, 5), anchor=(1, 1, 2))
    moved_case = make_case(shape=base_case.shape, anchor=(1, 2, 3))
    pair, images = pair_for(base_case)
    moved_pair, _ = pair_for(moved_case)
    base = calibrate(api, pair, base_case)
    moved = calibrate(api, moved_pair, moved_case)
    shift = (1, 1, -1)
    assert pair.bead is not None
    rolled_pair = replace(
        pair, bead=replace(pair.bead, data=np.roll(pair.bead.data, shift, axis=(-3, -2, -1)))
    )
    rolled = calibrate(api, rolled_pair, base_case)
    bound = 4 * max(
        response_budget(images, fit_components(images, base_case.phases), base_case.profile, 0.15)
    )
    points = np.array([[0.125, -0.25, 0.375], [-0.125, 0.125, -0.5]])
    for m in (1, 2):
        assert_close(rolled.response.values[m], base.response.values[m], bound)
        movement = sum(
            (
                Fraction(k * (b - a), n)
                for k, a, b, n in zip(
                    base_case.carrier,
                    base_case.anchor[1:],
                    moved_case.anchor[1:],
                    base_case.shape[1:],
                    strict=False,
                )
            ),
            Fraction(),
        )
        assert_close(
            moved.response.values[m], base.response.values[m] * phasor(m * movement), bound
        )
        original = sample(api, base, order=m, frequencies_zyx_per_um=points)
        physical = sample(api, moved, order=m, frequencies_zyx_per_um=points)
        storage = sample(
            api,
            rolled,
            order=m,
            frequencies_zyx_per_um=points,
            coordinate_offset_yx=tuple(-s for s in shift[1:]),
        )
        assert_close(physical.values, original.values, bound)
        assert_close(storage.values, original.values, bound)
        shifted = sample(
            api, base, order=m, frequencies_zyx_per_um=points, phase_reference_shift_rad=0.41
        )
        assert_close(shifted.values, original.values * np.exp(-1j * m * 0.41), bound)
    # A calibration phase-origin change is a separate declaration from movement.
    changed = calibrate(api, pair, base_case, phases_rad=base_case.phases + 0.23)
    for m in (1, 2):
        assert_close(
            changed.response.values[m], base.response.values[m] * np.exp(-1j * m * 0.23), bound
        )
        matched = sample(
            api, changed, order=m, frequencies_zyx_per_um=points, phase_reference_shift_rad=-0.23
        )
        assert_close(
            matched.values, sample(api, base, order=m, frequencies_zyx_per_um=points).values, bound
        )


def test_negative_order_reflects_all_physical_axes(api, calibrated, case):
    result, _, _, _, expected, _, _, budget = calibrated
    points = np.array([[0.125, -0.25, 0.375], [-0.25, 0.125, -0.5]])
    for m in (-1, -2):
        truth = expected_samples(
            expected, case.spacing, case.anchor, case.carrier, (1, 2), 0.29, m, points
        )
        observed = sample(
            api,
            result,
            order=m,
            frequencies_zyx_per_um=points,
            coordinate_offset_yx=(1, 2),
            phase_reference_shift_rad=0.29,
        )
        assert_close(observed.values, truth, budget[-m] + 4096 * EPS)
        wrong = np.conj(
            expected_samples(
                expected, case.spacing, case.anchor, case.carrier, (1, 2), 0.29, -m, points
            )
        )
        assert np.max(abs(truth - wrong)) > 0.01


def test_even_endpoints_closed_hull_singletons_and_no_zero_fill(api):
    case = make_case(shape=(1, 4, 4), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    result = calibrate(api, pair, case)
    for axis, endpoint in ((1, 2.0), (2, 4.0)):
        negative = np.zeros((1, 3))
        negative[0, axis] = -endpoint
        positive = -negative
        sample(api, result, order=1, frequencies_zyx_per_um=negative)
        sample(api, result, order=-1, frequencies_zyx_per_um=positive)
        reject(
            "incomplete_empirical_transfer_coverage",
            sample,
            api,
            result,
            order=1,
            frequencies_zyx_per_um=positive,
        )
        reject(
            "incomplete_empirical_transfer_coverage",
            sample,
            api,
            result,
            order=-1,
            frequencies_zyx_per_um=negative,
        )
    result.response.values.fill(0)
    outside = np.zeros((2, 3))
    outside[1, 0] = np.nextafter(0.0, 1.0)
    reject(
        "incomplete_empirical_transfer_coverage",
        sample,
        api,
        result,
        frequencies_zyx_per_um=outside,
    )
    outside[:] = 0
    outside[1, 1] = np.nextafter(-2.0, -np.inf)
    reject(
        "incomplete_empirical_transfer_coverage",
        sample,
        api,
        result,
        frequencies_zyx_per_um=outside,
    )
    inside = np.zeros((1, 3))
    inside[0, 1] = -2.0
    assert sample(api, result, frequencies_zyx_per_um=inside).values[0] == 0


def test_rounded_exported_endpoint_is_not_the_exact_lattice(api):
    case = make_case(shape=(1, 1, 3), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    result = calibrate(api, pair, case, voxel_size_um=(1, 1, 0.1))
    exact_endpoint = Fraction(1) / (3 * Fraction(0.1))
    rounded = float(exact_endpoint)
    outside = rounded if Fraction(rounded) > exact_endpoint else np.nextafter(rounded, np.inf)
    inside = rounded if Fraction(rounded) <= exact_endpoint else np.nextafter(rounded, -np.inf)
    reject(
        "incomplete_empirical_transfer_coverage",
        sample,
        api,
        result,
        frequencies_zyx_per_um=np.array([[0, 0, outside]]),
    )
    sample(api, result, frequencies_zyx_per_um=np.array([[0, 0, inside]]))
    # Tolerated metadata perturbations do not move the canonical ideal hull.
    result.response.fx_per_um[-1] = outside
    reject(
        "incomplete_empirical_transfer_coverage",
        sample,
        api,
        result,
        frequencies_zyx_per_um=np.array([[0, 0, outside]]),
    )


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"order": True}, "invalid_empirical_transfer_order"),
        ({"order": 1.0}, "invalid_empirical_transfer_order"),
        ({"order": 3}, "invalid_empirical_transfer_order"),
        ({"frequencies_zyx_per_um": [[0, 0, 0]]}, "invalid_empirical_transfer_frequencies"),
        (
            {"frequencies_zyx_per_um": np.zeros((1, 3), np.float32)},
            "invalid_empirical_transfer_frequencies",
        ),
        ({"frequencies_zyx_per_um": np.empty((0, 3))}, "invalid_empirical_transfer_frequencies"),
        ({"frequencies_zyx_per_um": np.zeros((3,))}, "invalid_empirical_transfer_frequencies"),
        (
            {"frequencies_zyx_per_um": np.full((1, 3), np.inf)},
            "invalid_empirical_transfer_frequencies",
        ),
        ({"coordinate_offset_yx": (True, 0)}, "invalid_empirical_transfer_coordinate_offset"),
        ({"coordinate_offset_yx": (0.5, 0)}, "invalid_empirical_transfer_coordinate_offset"),
        ({"phase_reference_shift_rad": np.inf}, "invalid_empirical_transfer_phase_shift"),
        ({"phase_reference_shift_rad": True}, "invalid_empirical_transfer_phase_shift"),
        ({"source": ""}, "invalid_otf_source"),
    ],
)
def test_sampler_declaration_errors_through_wrapper(api, calibrated, changes, code):
    reject(code, sample, api, calibrated[0], **changes)


def test_sampler_valid_edits_full_response_validation_and_exact_node_bits(api, calibrated):
    # Copy every array before editing so the session calibration remains unchanged.
    original = calibrated[0]
    response = replace(
        original.response,
        values=original.response.values.copy(),
        fz_per_um=original.response.fz_per_um.copy(),
        fy_per_um=original.response.fy_per_um.copy(),
        fx_per_um=original.response.fx_per_um.copy(),
    )
    result = replace(original, response=response)
    dc = tuple(n // 2 for n in response.values.shape[1:])
    response.values[(0, *dc)] = complex(-0.0, 0.75)
    observed = sample(api, result, order=0)
    assert (
        observed.values.view(np.uint64).tolist()
        == np.array([response.values[(0, *dc)]]).view(np.uint64).tolist()
    )
    response.values[(2, 0, 0, 0)] = np.nan
    reject("invalid_empirical_transfer_response", sample, api, result, order=0)
    response.values[(2, 0, 0, 0)] = 0
    response.fx_per_um[-1] = 1000
    reject("invalid_empirical_transfer_response", sample, api, result, order=0)


def test_huge_unreduced_integer_gauge_and_permitted_phase_extremes(api):
    case = make_case(shape=(1, 3, 4), kind="point")
    pair, images = pair_for(case)
    carrier = (10**200 + 1, -(10**180) - 1)
    offset = [10**220 + 2, -(10**240) + 1]
    result = calibrate(api, pair, case, calibration_carrier_bins=carrier)
    assert result.provenance["calibration_carrier_bins"] == carrier
    expected, _, _ = expected_response(
        fit_components(images, case.phases), case.profile, carrier, case.anchor
    )
    bound = max(response_budget(images, fit_components(images, case.phases), case.profile, 0.15))
    points = np.array([[0.0, 0.0, 0.0], [0, 0.125, -0.25]])
    for delta in (-0.0, np.nextafter(0.0, 1.0), np.finfo(float).max):
        for order in (np.int64(2), np.int8(-2)):
            actual = sample(
                api,
                result,
                order=order,
                frequencies_zyx_per_um=points,
                coordinate_offset_yx=offset,
                phase_reference_shift_rad=delta,
            )
            truth = expected_samples(
                expected, case.spacing, case.anchor, carrier, offset, delta, int(order), points
            )
            assert_close(actual.values, truth, bound + 4096 * EPS)
            assert actual.provenance["coordinate_offset_yx"] == tuple(offset)
    # Nonidentity finite profile indexing also retains huge declarations exactly.
    finite = make_case(shape=(1, 3, 4))
    finite_pair, finite_images = pair_for(finite)
    finite_result = calibrate(api, finite_pair, finite, calibration_carrier_bins=carrier)
    finite_expected, _, _ = expected_response(
        fit_components(finite_images, finite.phases),
        finite.profile,
        carrier,
        finite_result.response.origin_zyx,
    )
    bound = max(
        response_budget(
            finite_images, fit_components(finite_images, finite.phases), finite.profile, 0.15
        )
    )
    assert_close(finite_result.response.values, finite_expected, bound)


def test_provenance_snapshot_schema_and_output_ownership(api, calibrated, case):
    result, pair, *_ = calibrated
    p = result.provenance
    assert type(p) is dict
    assert set(p) == {
        "model",
        "source",
        "bead_mode",
        "group",
        "output_unit",
        "gauge_source",
        "calibration_carrier_bins",
        "correction",
        "phases_rad",
        "voxel_size_um",
        "dc_mass",
        "bead_profile",
        "min_profile_transfer",
        "profile_transfer",
        "compensated_dc",
        "response_gauge",
    }
    assert p["model"] == "alignment_bead_calibration_v1"
    assert p["source"] == " calibration source "
    assert p["bead_mode"] == "discrete_profile"
    assert p["response_gauge"] == "compensated_dc_peak_with_supplied_phase_origin"
    assert p["output_unit"] == "reference_signal"
    assert p["gauge_source"] == "explicit shared gauge"
    assert set(p["correction"]) == {
        "mode",
        "reference_sum_equalization",
        "camera_estimate",
        "bead",
        "specimen",
    }
    assert p["correction"]["camera_estimate"] is None
    for name in ("bead", "specimen"):
        member = p["correction"][name]
        assert set(member) == {"axes", "input_unit", "output_unit", "source_metadata", "provenance"}
        assert member["provenance"]["operations"] == (
            "subtract_offset",
            "divide_response",
            "divide_exposure",
        )
        assert member["source_metadata"]["calibration_id"] == (
            "opaque-bead-id" if name == "bead" else "different-opaque-id"
        )
        assert member["output_unit"] == "reference_signal"
        for key in member:
            assert_snapshot_equal(member[key], getattr(getattr(pair, name), key))
    assert set(p["dc_mass"]) == {"numerator", "denominator", "unit"}
    assert type(p["dc_mass"]["numerator"]) is int
    assert type(p["dc_mass"]["denominator"]) is int
    assert Fraction(p["dc_mass"]["numerator"], p["dc_mass"]["denominator"]) == exact_mass(
        result.components.dc
    )
    assert p["dc_mass"]["unit"] == "reference_signal"
    assert set(p["phases_rad"]) == {"source", "supplied", "applied"}
    assert p["phases_rad"]["source"] == "supplied_actual"
    assert set(p["voxel_size_um"]) == {"source", "supplied", "applied"}
    assert p["voxel_size_um"]["source"] == "supplied"
    assert p["voxel_size_um"]["applied"] == case.spacing
    assert set(p["bead_profile"]) == {"source", "supplied", "applied", "normalization"}
    assert p["bead_profile"]["normalization"] == "exact_converted_sum"
    assert_close(p["bead_profile"]["applied"], normalized_profile(case.profile), EPS)
    for array in (
        result.components.dc,
        result.components.c1,
        result.components.c2,
        result.response.values,
        result.response.fz_per_um,
        result.response.fy_per_um,
        result.response.fx_per_um,
        p["profile_transfer"],
        p["compensated_dc"],
    ):
        assert type(array) is np.ndarray and array.flags.owndata and array.flags.c_contiguous
        assert array.flags.writeable and array.dtype.isnative
    again = calibrate(api, pair, case)
    for a in arrays_in(result):
        for b in arrays_in(pair) + [case.phases, case.profile] + arrays_in(again):
            assert not np.shares_memory(a, b)
    for a in arrays_in(p):
        for b in arrays_in(result.components) + arrays_in(result.response):
            assert not np.shares_memory(a, b)
    owned = (
        arrays_in(result.components)
        + arrays_in(result.response)
        + [p["profile_transfer"], p["compensated_dc"]]
    )
    for index, a in enumerate(owned):
        for b in owned[index + 1 :]:
            assert not np.shares_memory(a, b)
    assert not np.shares_memory(p["phases_rad"]["supplied"], p["phases_rad"]["applied"])
    assert not np.shares_memory(p["bead_profile"]["supplied"], p["bead_profile"]["applied"])


def test_singleton_spacing_extremes_and_numpy_integer_carrier(api):
    case = make_case(shape=(1, 1, 1), kind="point", carrier=(0, 0))
    pair, _ = pair_for(case)
    spacing = [np.nextafter(0.0, 1.0), np.finfo(float).max, np.finfo(float).max]
    carrier = [np.uint64(2**64 - 1), np.int64(-9)]
    result = calibrate(api, pair, case, voxel_size_um=spacing, calibration_carrier_bins=carrier)
    assert result.response.voxel_size_um == tuple(spacing)
    assert result.provenance["calibration_carrier_bins"] == (2**64 - 1, -9)
    assert all(type(k) is int for k in result.provenance["calibration_carrier_bins"])
    for vector in (result.response.fz_per_um, result.response.fy_per_um, result.response.fx_per_um):
        assert np.array_equal(vector, [0.0])
    sample(api, result, order=-2)


def test_mutable_declaration_containers_are_snapshotted(api, case):
    pair, _ = pair_for(case)
    phases, profile = case.phases.copy(), case.profile.copy()
    group, spacing, carrier = {"orientation": 1}, list(case.spacing), list(case.carrier)
    result = calibrate(
        api,
        pair,
        case,
        phases_rad=phases,
        bead_profile=profile,
        group=group,
        voxel_size_um=spacing,
        calibration_carrier_bins=carrier,
    )
    phases.fill(0)
    profile.fill(0)
    group["orientation"] = 0
    spacing[0] = 99
    carrier[0] = 999
    assert pair.bead is not None
    pair.bead.source_metadata["original_metadata"]["caller"][1]["setting"] = -1
    assert np.array_equal(result.provenance["phases_rad"]["supplied"], case.phases)
    assert np.array_equal(result.provenance["bead_profile"]["supplied"], case.profile)
    assert result.provenance["group"] == {"orientation": 1}
    assert result.provenance["voxel_size_um"]["supplied"] == list(case.spacing)
    assert result.provenance["calibration_carrier_bins"] == case.carrier
    assert (
        result.provenance["correction"]["bead"]["source_metadata"]["original_metadata"]["caller"][
            1
        ]["setting"]
        == 17
    )


def test_caller_state_and_query_snapshots_across_success_rejection(api, case):
    pair, _ = pair_for(case)
    phases = case.phases.astype(">f8")
    phases.flags.writeable = False
    profile = np.asfortranarray(case.profile)
    profile.flags.writeable = False
    spacing = np.array(case.spacing, dtype=">f8")
    assert pair.bead is not None and pair.specimen is not None
    inputs = [pair.bead.data, pair.specimen.data, phases, profile, spacing]
    before = [(a.tobytes(), a.strides, a.flags.writeable) for a in inputs]
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("error", RuntimeWarning)
        filters = list(warnings.filters)
        mode = np.geterr().copy()
        result = calibrate(
            api, pair, case, phases_rad=phases, bead_profile=profile, voxel_size_um=spacing
        )
        reject(
            "invalid_finite_bead_transfer_threshold",
            calibrate,
            api,
            pair,
            case,
            min_profile_transfer=0,
        )
        assert np.geterr() == mode and warnings.filters == filters
        assert not caught
    assert before == [(a.tobytes(), a.strides, a.flags.writeable) for a in inputs]
    base = np.array([[0.0, -0.0, 0.0], [0.125, -0.25, 0.5], [0.0, -0.0, 0.0]], dtype=">f8")
    points = base[::-1]
    points.flags.writeable = False
    queries = points.tobytes()
    first = sample(api, result, frequencies_zyx_per_um=points, order=np.uint8(1))
    second = sample(api, result, frequencies_zyx_per_um=points)
    assert points.tobytes() == queries and not points.flags.writeable
    assert first.frequencies_zyx_per_um.dtype == np.dtype(float)
    assert np.array_equal(
        first.frequencies_zyx_per_um.view(np.uint64),
        np.asarray(points, dtype=float).view(np.uint64),
    )
    for a in arrays_in(first):
        assert a.flags.owndata and a.flags.c_contiguous and a.flags.writeable
        for b in [points, *arrays_in(result), *arrays_in(second)]:
            assert not np.shares_memory(a, b)


@pytest.mark.parametrize(
    "failure",
    [
        FloatingPointError,
        OverflowError,
        RuntimeWarning,
        MemoryError,
        RuntimeError,
        TypeError,
        ValueError,
    ],
)
def test_public_fft_operation_time_translation_and_propagation(api, case, monkeypatch, failure):
    pair, _ = pair_for(case)

    def fail(*args, **kwargs):
        if failure is RuntimeWarning:
            warnings.warn(
                "overflow encountered in RA05 public FFT control", RuntimeWarning, stacklevel=2
            )
            return np.zeros(case.shape, dtype=complex)
        raise failure("RA05 public FFT control")

    monkeypatch.setattr(np.fft, "fftn", fail)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        if failure in (FloatingPointError, OverflowError, RuntimeWarning):
            reject("finite_bead_transform_failure", calibrate, api, pair, case)
        else:
            with pytest.raises(failure, match="RA05 public FFT control"):
                calibrate(api, pair, case)


def test_nonfinite_inverse_transform_and_unrelated_warning(api, case, monkeypatch):
    pair, _ = pair_for(case)

    def nonfinite(array, *args, **kwargs):
        return np.full(array.shape, complex(0, np.inf))

    monkeypatch.setattr(np.fft, "ifftn", nonfinite)
    reject("finite_bead_transform_failure", calibrate, api, pair, case)
    monkeypatch.undo()
    original = np.fft.fftn

    def warn_and_transform(*args, **kwargs):
        warnings.warn("RA05 unrelated warning", UserWarning, stacklevel=2)
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn_and_transform)
    with pytest.warns(UserWarning, match="RA05 unrelated warning"):
        calibrate(api, pair, case)
