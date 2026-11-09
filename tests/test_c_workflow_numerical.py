"""Raw-to-fit-to-image proofs for the actual CE07 public entry."""

from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pytest

from c_workflow_oracle import (
    Table,
    b1_cases,
    b2_cases,
    b3_cases,
    constant_case,
    control_cases,
    error_budget,
    filter_and_assemble,
    gamma,
    initial_vectors,
    literal_metadata_cases,
    native_errors,
    observe,
)
from c_workflow_support import (
    assert_records,
    assert_scientific,
    close,
    immutable_array,
    keywords,
    run,
    snapshot_input,
)

CASES = (
    tuple(control_cases())
    + tuple(literal_metadata_cases())
    + tuple(b1_cases())
    + tuple(b2_cases())
    + tuple(b3_cases())
)
DRIFT_CONSUMPTION_CASES = (
    "between-current-background",
    "within2d-unfitted",
    "within2d-fitted",
    "within3d-cubic-first-block",
    "within2d-exact-cubic-impulses",
    "within3d-exact-cubic-impulses",
)


@pytest.mark.parametrize("name", CASES)
def test_complete_actual_workflow_against_raw_finite_observer(name: str) -> None:
    """Each configuration closes a distinct composition gap; see mapping.

    No returned stage value feeds the independent expected image. The observer
    starts at the fixed raw arrays and computes preparation, fit and filter.
    """
    cases = control_cases()
    cases.update(literal_metadata_cases())
    cases.update(b1_cases())
    cases.update(b2_cases())
    cases.update(b3_cases())
    case = cases[name]
    expected = observe(case)
    result = run(case)
    budget = assert_scientific(case, result, expected)
    assert_records(case, result)
    if name in DRIFT_CONSUMPTION_CASES:
        assert_drift_consumption(case, result, expected, budget)
    if name in b3_cases():
        settings = dict(result.resolved_settings)
        for group, values in (
            ("acquisition", {"edge_pixels": 10, "equalize": True}),
            ("carrier", {"phase_start_angle_rad": 1.57193, "search_carriers": True}),
            ("filtering", {"suppress_singularities": True, "output_taper": "cosine"}),
        ):
            for key, value in values.items():
                actual = dict(settings[group])[key]
                assert type(actual) is type(value) and actual == value
        assert result.parameters.branches == (("searched",), ("time0-reused",))
        # Initial vectors are independently checked below. Full bands, fits,
        # native coefficients and image already passed the raw finite observer.
        assert dict(result.bands.resolved_settings)["edge_pixels"] == 10
        assert dict(result.bands.resolved_settings)["equalize"] is True
        for reconstruction in result.reconstructions:
            assert dict(reconstruction.resolved_settings)["suppress_singularities"] is True
            assert dict(reconstruction.resolved_settings)["output_taper"] == "cosine"
    if name in b2_cases():
        direct = expected["parameters"]["raw_modulation"]
        recurrence = np.stack(
            (
                direct[..., 0],
                direct[..., 1] * direct[..., 0],
                direct[..., 2] * (direct[..., 1] * direct[..., 0]),
            ),
            axis=-1,
        )
        close(
            result.parameters.modulation,
            recurrence,
            budget["parameter_bounds"]["modulation"],
            label="third side order uses the already updated previous factor",
        )
        # Supplemental consumption proof. The raw absolute fit/filter/image
        # assertions above remain binding. Conditioning on the returned bands
        # and factors removes nuisance-search uncertainty from this relation;
        # it does not certify those inputs' absolute accuracy a second time.
        conditioned, relation_bounds = conditioned_native_expectation(case, result, expected)
        for it, reconstruction in enumerate(result.reconstructions):
            close(
                reconstruction.filtered_quadratures,
                conditioned["filtered_quadratures"][it : it + 1],
                relation_bounds["filtered"][it : it + 1],
                label="supplemental four-order fitted factors consumed by native filter",
            )
        close(
            result.image,
            conditioned["image"],
            relation_bounds["image"],
            label="supplemental four-order native signed image consumption",
        )
    if name == "signed-negative-counts":
        assert np.all(result.image < 0)
    initial, linkage = initial_vectors(case)
    bound = gamma(64) * max(1, float(np.max(abs(initial))))
    close(result.initial_carriers_cyc_um, initial, bound, label="P-derived initial vector")
    close(result.phase_linkage_carriers_cyc_um, linkage, bound, label="distinct phase-link vector")
    if name == "b1-omit-kz0-3d":
        assert dict(result.parameters.resolved_settings)["omit_kz0"] is True
        for overlap in result.parameters.overlaps:
            np.testing.assert_array_equal(overlap.written[:, 0], False)
            np.testing.assert_array_equal(overlap.fourier[:, 0], 0)
            assert np.any(overlap.written[:, 1:])
        for reconstruction in result.reconstructions:
            assert dict(reconstruction.resolved_settings)["omit_kz0"] is True
            np.testing.assert_array_equal(reconstruction.filtered_quadratures[:, :, 0, 0], 0)
    if name in ("b1-linked-distinct-initial-angles", "b1-active-first-off-first-time-phases"):
        prep = expected["preparation"]
        phase_truth = np.empty_like(prep["phase_angles_rad"])
        t, d, p, z = case.raw.shape[:4]
        for it, di, zi in np.ndindex(t, d, z):
            theta = case.carrier["phase_start_angle_rad"] + di * np.pi / d
            link = np.array([np.cos(theta), np.sin(theta)]) / case.carrier["linespacing_um"]
            base = (
                case.extras["header_phases_rad"][di * p * 2 + np.arange(p) * 2]
                if z == 1
                else 2 * np.pi * np.arange(p) / p
            )
            phase_truth[it, di, zi] = base + 2 * np.pi * case.acquisition["dxy_um"] * (
                prep["exposure_displacements_pixels"][it, di, zi] @ link
            )
        close(
            result.bands.phase_angles_rad,
            phase_truth,
            budget["preparation_bounds"]["phase_angles_rad"],
            label="active source phase selection",
        )
    if name == "b1-negative-step-no-angle-override":
        assert case.carrier["angles_rad"] is None
        theta = case.carrier["phase_start_angle_rad"] - np.arange(3) * np.pi / 3
        negative_guess = np.column_stack((np.cos(theta), np.sin(theta))) / (
            case.carrier["linespacing_um"] * (case.raw.shape[2] // 2)
        )
        close(
            result.initial_carriers_cyc_um,
            negative_guess,
            bound,
            label="unoverridden negative step",
        )
    if case.acquisition["acquisition_mode"] == "2d" and case.acquisition["axial_zoom"] > 1:
        np.testing.assert_array_equal(result.image[:, 1:], 0)
    if case.bead is not None:
        truth = expected["calibration"]
        close(
            result.transfer.samples,
            truth["table"].samples,
            budget["transfer"],
            label="consumed empirical table",
        )
        np.testing.assert_array_equal(result.calibration.transfer.samples, result.transfer.samples)
        assert result.transfer.dkz_cyc_um == truth["table"].dkz
        assert np.any(
            result.transfer.samples
            != result.transfer.samples.astype(np.complex64).astype(np.complex128)
        )
        for key in (
            "center_pixels_xyz",
            "background_counts",
            "quadratures",
            "normalization_factors",
            "quadrature_angles_rad",
        ):
            close(
                getattr(result.calibration, key),
                truth[key],
                budget["calibration_bounds"][key],
                label=f"actual calibration {key}",
            )
        if name == "empirical-complex-search-camera-phase":
            sampled = truth["table"].sample(0.1, 0.0, 1, 1 / 6, 1)
            assert abs(sampled.imag) > 100 * budget["transfer"]
            assert np.max(abs(np.imag(result.transfer.samples))) > 100 * budget["transfer"]


@pytest.mark.parametrize("complex_table", [False, True])
def test_closed_algebra_actual_modulation_and_image(complex_table: bool) -> None:
    """Section 9.1 closed algebra independently cross-checks the general observer."""
    case = constant_case(complex_table=complex_table)
    a0 = 1 + np.sqrt(2)
    mu = (a0 - 1j) / 4
    xv = np.arange(4) - 2
    if complex_table:
        amplitude = 3 * (2 - 1j) * mu / (20 * np.sqrt(2))
        h0, h1 = 2 + 2.5 * abs(amplitude) ** 2, 2 + 3 * abs(amplitude) ** 2
        image = 12 / h0 + 6 * np.real(amplitude.conjugate() * np.exp(1j * np.pi * xv / 4)) / h1
    else:
        amplitude = mu / 4
        image = (12 + (3 / 8) * np.array([1, a0, a0, 1])) / (2 + (2 + np.sqrt(2)) / 64)
    result = run(case)
    bound = gamma(65536) * 64
    close(
        result.parameters.raw_modulation[0, 0, 0],
        amplitude,
        gamma(4096) * 8,
        label="closed actual regression",
    )
    close(
        result.image,
        np.broadcast_to(image, (1, 2, 2, 4)),
        bound,
        label="closed finite signed image",
    )
    # Raw harmonic gain1/4 is not the accepted fitted gain; replacing the
    # asymmetric complex table by a unit/real table is independently wrong.
    assert abs(amplitude - 0.25) > 100 * bound


@pytest.mark.parametrize(
    "name", ["search-3d-reuse", "search-3d-all-times", "search-2d-reuse", "search-2d-all-times"]
)
def test_literal_finite_search_decisions_and_frozen_overlaps(name: str) -> None:
    case = control_cases()[name]
    expected = observe(case)
    budget = error_budget(case, expected)
    bounds = budget["parameter_bounds"]
    result = run(case)
    events = result.parameters.trace
    coarse = [event for event in events if event.kind == "coarse"]
    truth_coarse = [
        event for event in expected["parameters"]["decisions"] if event["kind"] == "coarse"
    ]
    assert len(coarse) == len(truth_coarse)
    for actual, truth, eb in zip(coarse, truth_coarse, bounds["coarse"], strict=True):
        values = dict(actual.details)
        assert values["integer_peak_xy"] == truth["integer_peak_xy"]
        assert values["alias_decisions"] == truth["alias_decisions"]
        close(
            values["carrier_cyc_um"],
            truth["carrier_cyc_um"],
            eb["carrier_radius"],
            label="coarse carrier cycles/um",
        )
    parabolas = [event for event in events if event.kind == "parabola"]
    truth_parabolas = [
        event for event in expected["parameters"]["decisions"] if event["kind"] == "parabola"
    ]
    assert len(parabolas) == len(truth_parabolas)
    for actual, truth, eb in zip(parabolas, truth_parabolas, bounds["parabolas"], strict=True):
        values = dict(actual.details)
        assert values["stage"] == truth["stage"]
        close(
            values["result"],
            truth["result"],
            eb["error"],
            label=f"literal source {truth['stage']} parabola",
        )
    actual_shifts = [
        (event.time_index, event.direction_index, dict(event.details)["stage"])
        for event in events
        if event.kind == "bracket" and dict(event.details)["branch"] == "shift"
    ]
    assert len(actual_shifts) == sum(
        event["kind"] == "shift" for event in expected["parameters"]["decisions"]
    )
    reused = case.resolved()[1]["use_time0_carriers"]
    if reused:
        np.testing.assert_array_equal(
            result.parameters.carriers_cyc_um[1], result.parameters.carriers_cyc_um[0]
        )
        assert (
            np.max(abs(result.parameters.modulation[1] - result.parameters.modulation[0]))
            > 10 * budget["modulation"]
        )


def conditioned_native_expectation(
    case: Any, result: Any, expected: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Preregistered finite native relation, conditional on exact supplied fields.

    The error formula is native_errors with zero uncertainty in conditioned
    operands. Its FFT/elementary arithmetic premises and exact decisions remain
    conditional; it is not a host replay theorem or a raw-accuracy substitute.
    No product function calculates the expected coefficients or image.
    """
    effective = copy.deepcopy(case)
    effective.table = Table(
        result.transfer.samples.copy(),
        layout=result.transfer.layout,
        dkr=result.transfer.dkr_cyc_um,
        dkz=result.transfer.dkz_cyc_um,
    )
    prep = dict(expected["preparation"])
    prep["quadratures"] = result.bands.quadratures.copy()
    prep["noise_variance_factors"] = result.bands.noise_variance_factors.copy()
    parameters = dict(
        carriers_cyc_um=result.parameters.carriers_cyc_um.copy(),
        modulation=result.parameters.modulation.copy(),
    )
    truth = filter_and_assemble(effective, prep, parameters)
    bounds = native_errors(
        effective,
        prep,
        parameters,
        truth,
        np.zeros_like(prep["quadratures"], dtype=float),
        np.zeros_like(prep["noise_variance_factors"]),
        np.zeros_like(parameters["modulation"], dtype=float),
        np.zeros(parameters["carriers_cyc_um"].shape[:-1]),
        np.zeros_like(effective.table.samples, dtype=float),
    )
    return truth, bounds


CALIBRATION_ARRAY_FIELDS = (
    "center_pixels_xyz",
    "background_counts",
    "phase_angles_rad",
    "quadratures",
    "normalization_factors",
    "quadrature_angles_rad",
)


def prepared_snapshot_expectation(prepared: Any) -> dict[str, Any]:
    """Independent before-call values for supplied-record preservation only.

    Raw absolute accuracy is separately checked against empirical finite sums.
    The expected arrays own their bytes; no result field defines this truth.
    """
    return dict(
        arrays={key: getattr(prepared, key).copy() for key in CALIBRATION_ARRAY_FIELDS},
        samples=prepared.transfer.samples.copy(),
        transfer={
            key: copy.deepcopy(getattr(prepared.transfer, key))
            for key in (
                "layout",
                "dkr_cyc_um",
                "dkz_cyc_um",
                "norders",
                "source_revision",
                "reference_sha256",
            )
        },
        settings=copy.deepcopy(prepared.resolved_settings),
    )


def assert_prepared_snapshot(actual: Any, supplied: Any, expected: dict[str, Any]) -> None:
    assert actual is not None and actual is not supplied
    assert actual.transfer is not supplied.transfer
    assert type(actual.resolved_settings) is tuple
    assert snapshot_input(actual.resolved_settings) == snapshot_input(expected["settings"])
    for key, value in expected["arrays"].items():
        array = getattr(actual, key)
        dtype = "complex128" if key == "quadratures" else "float64"
        assert value.dtype == np.dtype(dtype)
        immutable_array(array, dtype, value.shape)
        np.testing.assert_array_equal(array, value, strict=True)
        assert array.tobytes() == value.tobytes()
        assert not np.shares_memory(array, getattr(supplied, key))
    immutable_array(actual.transfer.samples, "complex128", expected["samples"].shape)
    np.testing.assert_array_equal(actual.transfer.samples, expected["samples"], strict=True)
    assert actual.transfer.samples.tobytes() == expected["samples"].tobytes()
    assert not np.shares_memory(actual.transfer.samples, supplied.transfer.samples)
    for key, value in expected["transfer"].items():
        assert snapshot_input(getattr(actual.transfer, key)) == snapshot_input(value)


@pytest.mark.parametrize("z", [1, 2])
def test_raw_and_precomputed_empirical_paths_preserve_computed_domain(z: int) -> None:
    case = control_cases()[f"empirical-z{z}"]
    assert case.bead is not None
    truth = observe(case)
    budget = error_budget(case, truth)
    # Real public preparation, not a forged value record. Snapshot every supplied
    # field BEFORE either workflow call, preserving computed complex128 bytes.
    kwargs = keywords(case, selection="prepared-otf")
    supplied = kwargs["transfer"]
    before = prepared_snapshot_expectation(supplied)
    raw = run(case)
    precomputed = run(case, selection="accepted-transfer", overrides=kwargs)
    assert_scientific(case, raw, truth, budget=budget)
    assert_scientific(case, precomputed, truth, budget=budget)
    assert_prepared_snapshot(precomputed.calibration, supplied, before)
    np.testing.assert_array_equal(
        precomputed.calibration.transfer.samples, precomputed.transfer.samples
    )
    for key in CALIBRATION_ARRAY_FIELDS:
        expected = (
            2 * np.pi * np.arange(case.bead[0].shape[0]) / case.bead[0].shape[0]
            if key == "phase_angles_rad"
            else truth["calibration"][key]
        )
        bound = (
            gamma(8) * 2 * np.pi if key == "phase_angles_rad" else budget["calibration_bounds"][key]
        )
        close(
            getattr(precomputed.calibration, key),
            expected,
            bound,
            label=f"prepared diagnostics independent raw accuracy {key}",
        )
    np.testing.assert_array_equal(raw.transfer.samples, precomputed.transfer.samples)
    np.testing.assert_array_equal(raw.image, precomputed.image)
    assert dict(raw.resolved_settings)["calibration_selection"] == "raw-beads"
    assert dict(precomputed.resolved_settings)["calibration_selection"] == "prepared-otf"
    assert raw.transfer.dkz_cyc_um == precomputed.transfer.dkz_cyc_um == 1 / (z * 0.75)
    # Owned readonly arrays have genuine caller backing. Re-enable writes only
    # AFTER the workflow returns; do not manufacture invalid pre-call records.
    for array in (
        supplied.transfer.samples,
        *(getattr(supplied, key) for key in CALIBRATION_ARRAY_FIELDS),
    ):
        array.setflags(write=True)
        array.flat[0] += 1
    assert_prepared_snapshot(precomputed.calibration, supplied, before)
    np.testing.assert_array_equal(precomputed.transfer.samples, before["samples"], strict=True)


def test_matching_prepared_identity_can_omit_optional_optics() -> None:
    case = control_cases()["empirical-z2"]
    truth = observe(case)
    kwargs = keywords(case, selection="prepared-otf")
    del kwargs["transfer_identity"]["optics"]
    supplied = kwargs["transfer"]
    before = prepared_snapshot_expectation(supplied)
    result = run(case, selection="accepted-transfer", overrides=kwargs)
    assert_scientific(case, result, truth)
    assert_prepared_snapshot(result.calibration, supplied, before)


def test_hidden_fit_class_and_native_filter_discriminators() -> None:
    case = control_cases()["empirical-complex-search-camera-phase"]
    expected = observe(case)
    result = run(case)
    budget = error_budget(case, expected)
    wrong = copy.deepcopy(case)
    wrong.bead = None
    actual_table = expected["calibration"]["table"]
    wrong.table = Table(
        np.ones_like(actual_table.samples), dkr=actual_table.dkr, dkz=actual_table.dkz
    )
    wrong_response = observe(wrong)["image"]
    # Concrete wrong-class model: unit response is a fitted all-real response
    # that discards measured unequal/asymmetric order coefficients. This is
    # not an observed comparison to an unavailable historical executable.
    difference = np.max(abs(expected["image"] - wrong_response))
    assert difference > 100 * budget["image"], (
        "oracle must distinguish response substitution before product observation"
    )
    # Raw calibration uncertainty and shared-field finite decisions propagate
    # independently through this original raw empirical/search witness.
    assert_scientific(case, result, expected)
    # Replaying the raw phase harmonic as modulation is independently wrong.
    parameters = copy.deepcopy(expected["parameters"])
    parameters["modulation"][:] = 0.25
    actual_case = copy.deepcopy(case)
    actual_case.bead = None
    actual_case.table = actual_table
    wrong_gains = filter_and_assemble(actual_case, expected["preparation"], parameters)["image"]
    assert np.max(abs(expected["image"] - wrong_gains)) > 100 * budget["image"]


def test_positive_wiener_schedule_and_no_time_slice_reprepare() -> None:
    case = constant_case(times=2)
    case.filtering.update(wiener=0.2, wiener_increment=0.2)
    expected = observe(case)
    result = run(case)
    assert_scientific(case, result, expected)
    close(result.effective_wiener, [0.3, 0.4], gamma(8), label="source preincrement")
    assert result.bands.input_shape[0] == 2
    assert len(result.reconstructions) == 2
    assert result.parameters.branches == (("known",), ("known",))


def assert_drift_consumption(
    case: Any, result: Any, expected: dict[str, Any], budget: dict[str, Any]
) -> None:
    """Prove stage consumption separately from the raw absolute error envelope.

    Genuine stage values condition this independent native-filter/assembly
    relation. They are not a new absolute raw-to-image oracle. The companion
    raw finite-sum test and exact cubic impulse controls supply that proof.
    """
    name = case.name
    prep = dict(expected["preparation"])
    prep["quadratures"] = result.bands.quadratures.copy()
    prep["noise_variance_factors"] = result.bands.noise_variance_factors.copy()
    parameters = dict(expected["parameters"])
    parameters["carriers_cyc_um"] = result.parameters.carriers_cyc_um.copy()
    parameters["modulation"] = result.parameters.modulation.copy()
    conditional = filter_and_assemble(case, prep, parameters)
    # All input values here are conditioned observations. N native finite
    # coefficients, <=D*(2O-1) powers per quotient, w²>=w_min². The factor
    # below counts complex arithmetic and both observer/backend reductions.
    n = int(np.prod(case.raw.shape[-3:]))
    d = case.raw.shape[1]
    o = case.acquisition["norders"]
    scale = max(1.0, float(np.sum(abs(conditional["filtered_quadratures"]))))
    bound = gamma(256 * n * d * o) * scale / min(conditional["effective_wiener"]) ** 4
    close(
        result.image,
        conditional["image"],
        bound,
        label="conditional consumed drift/filter/assembly",
    )
    if name.endswith("exact-cubic-impulses"):
        events = [event for event in result.bands.trace if event.kind == "cubic-fit"]
        assert len(events) == 1
        truth = np.array(
            [[0.0, 0.0], [0.0, 0.0], [1.0 if name.startswith("within2d") else 1 / 216, 0.0]]
        )
        close(
            dict(events[0].details)["coefficients"],
            truth,
            budget["cubic_coefficients"],
            label="absolute source cubic coefficients and units",
        )


def test_native_before_noninteger_relocation_has_independent_phase_discriminator() -> None:
    case = constant_case(complex_table=True)
    result = run(case)
    mu = (1 + np.sqrt(2) - 1j) / 4
    amplitude = 3 * (2 - 1j) * mu / (20 * np.sqrt(2))
    x = np.arange(4) - 2
    native = 12 / (2 + 2.5 * abs(amplitude) ** 2) + 6 * np.real(
        amplitude.conjugate() * np.exp(1j * np.pi * x / 4)
    ) / (2 + 3 * abs(amplitude) ** 2)
    relocated = 12 / (2 + 2.5 * abs(amplitude) ** 2) + 6 * np.real(
        amplitude.conjugate() * (1 - 0.5j) * np.exp(1j * np.pi * x / 4)
    ) / (2 + 3 * abs(amplitude) ** 2)
    bound = gamma(65536) * 64
    assert np.max(abs(native - relocated)) > 100 * bound
    close(
        result.image,
        np.broadcast_to(native, result.image.shape),
        bound,
        label="native coefficient before relocation",
    )
