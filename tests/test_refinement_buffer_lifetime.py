"""RB117 exact public retention relationships; science keepers remain separate.

No parity assertion below is an independent mathematical-accuracy claim.
S05 later-equality preservation and in-call last use require explicit C/D proof.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import simrecon
from c_estimation_fixture import estimate, events
from refinement_buffer_lifetime_fixture import (
    assert_capture_projection,
    emit_input_record,
    exact,
    public_arrays,
    retention_case,
)


def assert_frozen(record, name, value):
    with pytest.raises((AttributeError, TypeError)):
        setattr(record, name, value)


def assert_fit_links(parameters):
    """Check public scalar references without adding a numerical fit oracle."""
    for t, row in enumerate(parameters.branches):
        for d, _ in enumerate(row):
            trace = [e for e in parameters.trace if (e.time_index, e.direction_index) == (t, d)]
            raw = parameters.raw_modulation[t, d]
            for event in trace:
                value = dict(event.details)
                if event.kind == "evaluation" and value["stage"] in (
                    "known",
                    "final",
                    "later-order",
                ):
                    exact(value["forward"], complex(raw[value["orders"][1] - 1]))
            products = [dict(e.details) for e in trace if e.kind == "cumulative-product"]
            entering = [complex(value) for value in raw]
            if products:
                assert [value["order"] for value in products] == list(range(2, len(raw) + 1))
                for value in products:
                    index = value["order"] - 1
                    exact(value["direct_forward"], complex(raw[index]))
                    exact(value["previous_cumulative"], entering[index - 1])
                    entering[index] = value["product"]
            adjustments = [dict(e.details) for e in trace if e.kind == "adjustment"]
            assert [value["order"] for value in adjustments] == list(range(1, len(raw) + 1))
            for index, value in enumerate(adjustments):
                exact(value["raw_forward"], entering[index])
                exact(value["final"], complex(parameters.modulation[t, d, index]))


def exercise(raw, settings):
    """Compare actual full/compact/direct results at the same declared input."""
    emit_input_record(raw, settings)
    before = raw.copy()
    full = simrecon.reconstruct_workflow(raw, **settings)
    summary = simrecon.reconstruct_summary(raw, **settings)
    exact(raw, before)
    assert_capture_projection(summary, full)
    assert_fit_links(full.parameters)
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
    options = {
        key: settings["carrier"][key]
        for key in ("search_carriers", "use_time0_carriers", "amplitude_floors", "fit_all_phases")
    }
    options["omit_kz0"] = settings["filtering"].get("omit_kz0", False)
    # The actual workflow vector is this direct call's declared public input.
    # Equality of these calls does not certify its independent scientific truth.
    direct = estimate(full.bands, full.transfer, full.initial_carriers_cyc_um, **options)
    exact(direct, full.parameters)
    assert full.bands.quadratures.flags.writeable
    assert full.bands.noise_variance_factors.flags.writeable
    assert not np.shares_memory(full.image, full.reconstructions[0].image)
    arrays = public_arrays(summary)
    names = (
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
    assert {id(array) for array in arrays} == {id(getattr(summary, name)) for name in names}
    for name in names:
        expected_dtype = np.complex128 if name in ("modulation", "raw_modulation") else np.float64
        assert getattr(summary, name).dtype == expected_dtype
    for index, array in enumerate(arrays):
        assert array.flags.owndata and not array.flags.writeable
        assert not np.shares_memory(array, raw)
        assert not np.shares_memory(array, settings["transfer"].samples)
        for other in arrays[:index]:
            assert not np.shares_memory(array, other)
    for array in public_arrays(full.parameters):
        assert array.flags.owndata and not array.flags.writeable
        assert not np.shares_memory(array, full.bands.quadratures)
        assert not np.shares_memory(array, full.transfer.samples)
    for build in full.parameters.overlaps:
        assert build.fourier.shape == build.spatial.shape == build.written.shape
        assert build.fourier.shape == (2, *full.bands.input_shape[3:])
        assert build.fourier.dtype == build.spatial.dtype == np.complex128
        assert build.written.dtype == np.bool_
    return summary, full


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


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("reuse", [True, False])
def test_native_three_direction_search_exact_compact_full_records(layout, reuse):
    raw, settings = retention_case("native", layout=layout, reuse=reuse)
    summary, full = exercise(raw, settings)
    assert summary.branches == (("searched",) * 3, ("time0-reused" if reuse else "searched",) * 3)
    assert summary.raw_modulation[0].tobytes() != summary.raw_modulation[1].tobytes()
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


@pytest.mark.parametrize("mode,orders", [("3d", 5), ("2d", 4), ("2d", 2)])
@pytest.mark.parametrize("layout", ["radial", "full"])
def test_searched_later_orders_frozen_final_fit_products_and_no_later_case(mode, orders, layout):
    raw, settings = retention_case("later", mode, orders, layout=layout)
    _, full = exercise(raw, settings)
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
    products = events(full.parameters, "cumulative-product")
    assert [event["order"] for event in products] == (
        list(range(2, orders)) if mode == "2d" else []
    )


@pytest.mark.parametrize("reuse", [True, False])
def test_true_two_dimensional_time_policy_refits_or_restarts_without_adjacent_reuse(reuse):
    raw, settings = retention_case("time", "2d", 4, reuse=reuse)
    summary, full = exercise(raw, settings)
    assert summary.branches == (("searched",), ("time0-reused" if reuse else "searched",))
    assert summary.raw_modulation[0].tobytes() != summary.raw_modulation[1].tobytes()
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
    raw, settings = retention_case("repeated", mode, 4)
    summary, full = exercise(raw, settings)
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
    raw.flags.writeable = True
    raw.fill(99)
    full.bands.quadratures.fill(123)
    full.bands.noise_variance_factors.fill(2)
    settings["carrier"]["angles_rad"].fill(0.75)
    assert all(array.tobytes() == before for array, before in snapshots)


@pytest.mark.parametrize("mode", ["2d", "3d"])
@pytest.mark.parametrize("searched", [True, False])
def test_omit_kz0_empty_overlap_preserves_estimation_error_stage_and_cause(mode, searched):
    raw, settings = retention_case("omit", mode, search=searched)
    emit_input_record(raw, settings)
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
    raw, settings = retention_case("late", mode)
    emit_input_record(raw, settings)
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
    raw, settings = retention_case("strided", mode)
    _, full = exercise(raw, settings)
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
    raw, settings = retention_case("invalid", mode, invalid=invalid)
    emit_input_record(raw, settings)
    wanted_code, wanted_stage = {
        "raw-finite": ("workflow_input", "declaration"),
        "flag": ("workflow_config", "declaration"),
        "stencil": ("workflow_representation", "estimation"),
    }[invalid]
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
