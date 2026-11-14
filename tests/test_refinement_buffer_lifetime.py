"""RB117 real public workflow parity and independent searched2D witnesses."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import simrecon
from c_estimation_fixture import (
    assert_expected,
    close,
    estimate,
    events,
    expected_estimate,
    overlap,
)
from refinement_buffer_lifetime_fixture import (
    assert_capture_projection,
    assert_image_oracle,
    exact,
    expected_plane,
    finite_bands,
    independent_images,
    initial_vectors,
    plane_build,
    public_arrays,
    workflow_case,
)


def assert_frozen(record, name, value):
    with pytest.raises((AttributeError, TypeError)):
        setattr(record, name, value)


def exercise(raw, settings, *, unique_coarse=False):
    """Use contract sums first, then actual complete and compact public entries."""
    independent = finite_bands(raw, settings)
    initial = initial_vectors(raw, settings)
    options = {
        key: settings["carrier"][key]
        for key in ("search_carriers", "use_time0_carriers", "amplitude_floors", "fit_all_phases")
    }
    two_d = settings["acquisition"]["acquisition_mode"] == "2d"
    oracle = expected_plane if two_d else expected_estimate
    expected = oracle(independent, settings["transfer"], initial, **options)
    images = independent_images(independent, settings["transfer"], expected)
    if raw.shape[-1] == 8:
        # The constructed low-bin cases must qualify using the independent
        # oracle BEFORE any product call. These margins diagnose fixture-domain
        # mistakes; they do not relax the approved production domain.
        orders = settings["acquisition"]["norders"]
        for vector in expected.carriers_cyc_um.reshape(-1, 2):
            assert 0.5 - (orders - 1) * float(np.linalg.norm(vector)) > 0.025
        for evaluation in events(expected, "evaluation"):
            sx, sy = evaluation["SX"], evaluation["SY"]
            assert min(sx, sy) > 0
            assert abs(sx - sy) > 64 * 3e-11 * max(sx, sy)
        if unique_coarse:
            for coarse in events(expected, "coarse"):
                powers = np.sort(coarse["correlation_power"].ravel())
                assert powers[-1] - powers[-2] > 64 * 3e-11 * powers[-1]
        remade = (
            plane_build(
                independent,
                settings["transfer"],
                expected.carriers_cyc_um[0, 0],
                (0, 1),
                0,
                0,
                "counterfactual",
                0,
            )
            if two_d
            else overlap(independent, settings["transfer"], expected.carriers_cyc_um[0, 0], 2)
        )
        assert np.max(np.abs(remade.fourier - expected.overlaps[1].fourier)) > 1e-8
    raw_before = raw.copy()
    full = simrecon.reconstruct_workflow(raw, **settings)
    summary = simrecon.reconstruct_summary(raw, **settings)
    exact(raw, raw_before)
    close(full.bands.quadratures, independent.quadratures)
    assert_expected(full.parameters, expected)
    assert_image_oracle(full.image, images, expected)
    assert_capture_projection(summary, full)
    assert summary.diagnostics == "summary"
    assert summary.omitted_diagnostics == (
        "stage-images",
        "quadratures",
        "overlap-arrays",
        "correlation-arrays",
        "camera-maps",
        "transfer-samples",
        "calibration-arrays",
        "layout-pixels",
        "precise-query-events",
    )
    assert_frozen(summary, "diagnostics", "changed")
    assert_frozen(summary.overlap_builds[0], "index", -1)
    # Direct estimator remains a full-record operation on the actual mutable
    # public AcquisitionBands. Equality here includes every scalar/array bit.
    direct = estimate(full.bands, full.transfer, full.initial_carriers_cyc_um, **options)
    exact(direct, full.parameters)
    assert full.bands.quadratures.flags.writeable
    assert full.bands.noise_variance_factors.flags.writeable
    assert not np.shares_memory(full.image, full.reconstructions[0].image)
    arrays = public_arrays(summary)
    allowed = {
        id(getattr(summary, name))
        for name in (
            "image",
            "x_um",
            "y_um",
            "z_um",
            "carriers_cyc_um",
            "modulation",
            "raw_modulation",
            "initial_carriers_cyc_um",
            "phase_linkage_carriers_cyc_um",
            "effective_wiener",
        )
    }
    assert {id(array) for array in arrays} == allowed
    for index, array in enumerate(arrays):
        assert array.flags.owndata and not array.flags.writeable
        assert not np.shares_memory(array, raw)
        assert not np.shares_memory(array, settings["transfer"].samples)
        for other in arrays[:index]:
            assert not np.shares_memory(array, other)
    for build in full.parameters.overlaps:
        for name in ("fourier", "spatial", "written", "carrier_cyc_um"):
            array = getattr(build, name)
            assert array.flags.owndata and not array.flags.writeable
    return summary, full, independent, expected


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("reuse", [True, False])
def test_native_three_direction_search_exact_compact_full_and_finite_image(layout, reuse):
    raw, settings = workflow_case("3d", 3, directions=3, times=2, layout=layout, reuse=reuse)
    summary, full, _, _ = exercise(raw, settings)
    assert summary.branches == (("searched",) * 3, ("time0-reused" if reuse else "searched",) * 3)
    assert np.max(np.abs(summary.raw_modulation[0] - summary.raw_modulation[1])) > 1e-6
    if reuse:
        exact(summary.carriers_cyc_um[0], summary.carriers_cyc_um[1])
    for d in range(3):
        builds = [
            b for b in full.parameters.overlaps if b.time_index == 0 and b.direction_index == d
        ]
        assert [(b.purpose, b.orders) for b in builds] == [
            ("coarse", (0, 2)),
            ("refinement", (0, 2)),
            ("later-order", (0, 1)),
        ]
    assert_frozen_reference(full, 2)


def assert_frozen_reference(full, order):
    for t, row in enumerate(full.parameters.branches):
        for d, branch in enumerate(row):
            if branch != "searched":
                continue
            builds = [
                b for b in full.parameters.overlaps if (b.time_index, b.direction_index) == (t, d)
            ]
            evaluations = [
                dict(e.details)
                for e in full.parameters.trace
                if e.kind == "evaluation" and (e.time_index, e.direction_index) == (t, d)
            ]
            frozen = [e for e in evaluations if e["stage"] in ("angle", "magnitude", "final")]
            assert all(
                e["orders"] == (0, order) and e["overlap_index"] == builds[1].index for e in frozen
            )
            assert frozen[0]["remake_overlaps"] is True
            assert all(e["remake_overlaps"] is False for e in frozen[1:])
            assert len([e for e in frozen if e["stage"] == "final"]) == 1


@pytest.mark.parametrize("mode,orders", [("3d", 5), ("2d", 4), ("2d", 2)])
@pytest.mark.parametrize("layout", ["radial", "full"])
def test_searched_later_orders_frozen_final_fit_products_and_no_later_case(mode, orders, layout):
    raw, settings = workflow_case(
        mode,
        orders,
        layout=layout,
        adjustments=orders > 2,
        dz=0.0 if mode == "2d" else 1.0,
        low_bin=mode == "3d",
    )
    _, full, independent, expected = exercise(raw, settings)
    fitorder = 1 if mode == "2d" else 2
    pairs = [(0, fitorder), (0, fitorder)] + (
        [(b - 1, b) for b in range(2, orders)]
        if mode == "2d"
        else [(0, b) for b in range(1, orders) if b != 2]
    )
    assert [build.orders for build in full.parameters.overlaps] == pairs
    assert len(pairs) == orders
    assert_frozen_reference(full, fitorder)
    final = next(e for e in events(full.parameters, "evaluation") if e["stage"] == "final")
    exact(final["forward"], complex(full.parameters.raw_modulation[0, 0, fitorder - 1]))
    if mode == "2d":
        remade = plane_build(
            independent,
            full.transfer,
            expected.carriers_cyc_um[0, 0],
            (0, 1),
            0,
            0,
            "counterfactual",
            0,
        )
        products = events(full.parameters, "cumulative-product")
        assert [event["order"] for event in products] == list(range(2, orders))
        for event in products:
            close(event["product"], event["direct_forward"] * event["previous_cumulative"])
    else:
        remade = overlap(independent, full.transfer, expected.carriers_cyc_um[0, 0], 2)
        assert not events(full.parameters, "cumulative-product")
    # Public finite oracle witnesses that rebuilding at final carrier changes
    # the pair. This is a fixture discriminator, not an execution-memory claim.
    assert np.max(np.abs(remade.fourier - expected.overlaps[1].fourier)) > 1e-8


@pytest.mark.parametrize("reuse", [True, False])
def test_true_two_dimensional_time_policy_refits_or_restarts_without_adjacent_reuse(reuse):
    raw, settings = workflow_case(
        "2d", 4, times=2, reuse=reuse, dz=0.2, low_bin=True, odd_phase=True
    )
    summary, full, _, _ = exercise(raw, settings, unique_coarse=True)
    assert summary.branches == (("searched",), ("time0-reused" if reuse else "searched",))
    assert np.max(np.abs(summary.raw_modulation[0] - summary.raw_modulation[1])) > 1e-6
    later = [b for b in full.parameters.overlaps if b.time_index == 1]
    assert [b.orders for b in later] == (
        [(0, 1), (0, 2), (0, 3)] if reuse else [(0, 1), (0, 1), (1, 2), (2, 3)]
    )
    if reuse:
        evaluations = [
            dict(e.details)
            for e in full.parameters.trace
            if e.time_index == 1 and e.kind == "evaluation"
        ]
        assert all(e["objective"] is None for e in evaluations)
    else:
        coarse = [b for b in full.parameters.overlaps if b.purpose == "coarse"]
        exact(coarse[0].carrier_cyc_um, coarse[1].carrier_cyc_um)


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_known_repeated_builds_keep_distinct_descriptors_and_caller_storage(mode):
    raw, settings = workflow_case(mode, 4, times=2, search=False)
    raw[1] = raw[0]
    backing = np.zeros((*raw.shape[:-1], raw.shape[-1] * 2), dtype=np.float64)
    backing[..., ::2] = raw
    caller = backing[..., ::2]
    caller.flags.writeable = False
    summary, full, _, _ = exercise(caller, settings)
    assert summary.branches == (("known",), ("known",))
    assert all(e["objective"] is None for e in events(full.parameters, "evaluation"))
    builds = full.parameters.overlaps
    assert [b.orders for b in builds] == [(0, 1), (0, 2), (0, 3)] * 2
    for first, repeated in zip(builds[:3], builds[3:], strict=True):
        assert first.index != repeated.index
        for name in ("fourier", "spatial", "written", "carrier_cyc_um"):
            exact(getattr(first, name), getattr(repeated, name))
            assert not np.shares_memory(getattr(first, name), getattr(repeated, name))
    snapshots = [(a, a.tobytes()) for a in public_arrays(summary) + public_arrays(full.parameters)]
    backing.fill(99)
    full.bands.quadratures.fill(123)
    full.bands.noise_variance_factors.fill(2)
    settings["carrier"]["angles_rad"].fill(0.75)
    assert all(array.tobytes() == before for array, before in snapshots)


@pytest.mark.parametrize("mode", ["2d", "3d"])
@pytest.mark.parametrize("searched", [True, False])
def test_omit_kz0_empty_overlap_preserves_estimation_error_stage_and_cause(mode, searched):
    raw, settings = workflow_case(mode, 3, search=searched)
    if mode == "3d":
        # Z3 at these optics clips c to0, so omission removes every sample.
        assert raw.shape[3] == 3
    settings["filtering"]["omit_kz0"] = True
    before = raw.copy()
    observed = []
    for entry in (simrecon.reconstruct_workflow, simrecon.reconstruct_summary):
        with pytest.raises(simrecon.WorkflowError) as caught:
            entry(raw, **settings)
        error = caught.value
        assert error.code == "workflow_operation" and error.stage == "estimation"
        assert isinstance(error.__cause__, simrecon.ParameterEstimationError)
        assert str(error) and str(error.__cause__)
        assert error.time_index in (None, 0) and error.direction_index in (None, 0)
        observed.append(
            (
                error.code,
                error.stage,
                error.time_index,
                error.direction_index,
                type(error.__cause__),
                str(error.__cause__),
            )
        )
    assert observed[0] == observed[1]
    exact(raw, before)


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_late_known_time_failure_preserves_context_whole_call_and_inputs(mode):
    raw, settings = workflow_case(mode, 3, times=2, search=False)
    # All-zero later data reaches missing lower energy after valid t0 fits.
    raw[1] = 0
    before = raw.copy()
    for entry in (simrecon.reconstruct_workflow, simrecon.reconstruct_summary):
        with pytest.raises(simrecon.WorkflowError) as caught:
            entry(raw, **settings)
        error = caught.value
        assert error.code == "workflow_operation" and error.stage == "estimation"
        assert error.time_index == 1 and error.direction_index == 0
        assert isinstance(error.__cause__, simrecon.ParameterEstimationError)
        exact(raw, before)


@pytest.mark.parametrize("mode", ["2d", "3d"])
def test_direct_search_accepts_readonly_strided_used_bands_and_remains_full(mode):
    raw, settings = workflow_case(mode, 3)
    _, full, _, _ = exercise(raw, settings)
    bands = full.bands
    storage = np.zeros(
        (*bands.quadratures.shape[:-1], bands.quadratures.shape[-1] * 2), dtype=np.complex128
    )
    storage[..., ::2] = bands.quadratures
    view = storage[..., ::2]
    view.flags.writeable = False
    noise = bands.noise_variance_factors.copy()
    noise.flags.writeable = False
    declared = dataclasses.replace(bands, quadratures=view, noise_variance_factors=noise)
    result = estimate(declared, full.transfer, full.initial_carriers_cyc_um)
    exact(result, full.parameters)
    frozen = [(a, a.tobytes()) for a in public_arrays(result)]
    storage.fill(42)
    assert all(a.tobytes() == snapshot for a, snapshot in frozen)


@pytest.mark.parametrize("mode", ["2d", "3d"])
@pytest.mark.parametrize("invalid", ["raw-finite", "flag", "stencil"])
def test_compact_preserves_single_invalid_declarations_and_actual_zero_weight_stencil(
    mode, invalid
):
    raw, settings = workflow_case(mode, 3, search=False)
    if invalid == "raw-finite":
        raw[0, 0, 0, 0, 0, 0] = np.nan
        wanted_code, wanted_stage = "workflow_input", "declaration"
    elif invalid == "flag":
        settings["carrier"]["search_carriers"] = 1
        wanted_code, wanted_stage = "workflow_config", "declaration"
    else:
        # R1 retains valid complete metadata but the actual DC stencil must
        # request radial row1 even when that vertex has zero weight.
        settings["transfer"] = simrecon.declare_otf(
            np.ones((4, 1, 1 if mode == "2d" else 8)),
            layout="radial",
            dkr_cyc_um=1.0,
            dkz_cyc_um=1.0,
        )
        wanted_code, wanted_stage = "workflow_representation", "estimation"
    before = raw.copy()
    signatures = []
    for entry in (simrecon.reconstruct_workflow, simrecon.reconstruct_summary):
        with pytest.raises(simrecon.WorkflowError) as caught:
            entry(raw, **settings)
        error = caught.value
        assert (error.code, error.stage) == (wanted_code, wanted_stage)
        if invalid == "stencil":
            assert isinstance(error.__cause__, simrecon.ParameterEstimationError)
        signatures.append(
            (
                error.code,
                error.stage,
                error.time_index,
                error.direction_index,
                type(error.__cause__),
                str(error.__cause__),
            )
        )
        exact(raw, before)
    assert signatures[0] == signatures[1]
