"""Independent RM84 scientific, projection, ownership and failure obligations."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import struct
from typing import Any

import numpy as np
import pytest

import simrecon
import test_c_workflow_validation as inherited_validation
from reconstruction_summary_fixture import (
    OMITTED,
    SCENARIOS,
    SPATIAL_DETAILS,
    SUMMARY_FIELDS,
    analytical_case,
    analytical_expected,
    identity,
    identity_values,
    scenario,
    walk_arrays,
    workload,
)


@pytest.fixture
def summary_entry() -> Any:
    entry = getattr(simrecon, "reconstruct_summary", None)
    assert callable(entry), "RM84 feature absent: simrecon.reconstruct_summary"
    return entry


def same(actual: Any, expected: Any) -> None:
    """Compare values and types exactly, including signed binary64 zeros."""
    if isinstance(expected, np.ndarray):
        assert isinstance(actual, np.ndarray)
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        assert actual.tobytes() == expected.tobytes()
    elif dataclasses.is_dataclass(expected) and not isinstance(expected, type):
        assert tuple(f.name for f in dataclasses.fields(actual)) == tuple(
            f.name for f in dataclasses.fields(expected)
        )
        for field in dataclasses.fields(expected):
            same(getattr(actual, field.name), getattr(expected, field.name))
    elif isinstance(expected, tuple):
        assert isinstance(actual, tuple) and len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            same(left, right)
    elif isinstance(expected, float):
        assert type(actual) is float
        assert struct.pack("d", actual) == struct.pack("d", expected)
    elif isinstance(expected, complex):
        assert type(actual) is complex
        same(actual.real, expected.real)
        same(actual.imag, expected.imag)
    else:
        assert type(actual) is type(expected)
        assert actual == expected


def scalar_tuple(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return scalar_tuple(value.tolist())
    if isinstance(value, (list, tuple)):
        return tuple(scalar_tuple(item) for item in value)
    return value


def check_projection(
    actual: Any, expected: Any, path: str, *, inputs: dict[str, np.ndarray] | None = None
) -> None:
    """Audit logical-key names before array conversion, including tiny numeric arrays."""
    if inputs is not None and path in inputs:
        assert identity_values(actual) == identity(inputs[path], path)
    elif isinstance(expected, np.ndarray):
        assert identity_values(actual) == identity(expected, path)
    elif dataclasses.is_dataclass(expected) and not isinstance(expected, type):
        fields = tuple(field.name for field in dataclasses.fields(expected))
        assert isinstance(actual, tuple)
        assert tuple(key for key, _ in actual) == fields
        for key, value in actual:
            check_projection(value, getattr(expected, key), f"{path}.{key}", inputs=inputs)
    elif isinstance(expected, tuple):
        assert isinstance(actual, tuple) and len(actual) == len(expected)
        named = bool(expected) and all(
            isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], str) for v in expected
        )
        for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
            if named:
                assert left[0] == right[0]
                check_projection(left[1], right[1], f"{path}.{right[0]}", inputs=inputs)
            else:
                check_projection(left, right, f"{path}.{index}", inputs=inputs)
    else:
        same(actual, expected)


def projected_record(actual: Any, full: Any, path: str, exclude: set[str]) -> None:
    names = tuple(f.name for f in dataclasses.fields(full) if f.name not in exclude)
    assert isinstance(actual, tuple)
    assert tuple(key for key, _ in actual) == names
    for key, value in actual:
        check_projection(value, getattr(full, key), f"{path}.{key}")


def event_equal(actual: Any, full: Any) -> None:
    for field in dataclasses.fields(full):
        if field.name != "details":
            same(getattr(actual, field.name), getattr(full, field.name))
    expected = tuple(
        (key, scalar_tuple(value))
        for key, value in full.details
        if key not in SPATIAL_DETAILS.get(full.kind, set())
    )
    same(actual.details, expected)
    assert not walk_arrays(actual)
    with pytest.raises(dataclasses.FrozenInstanceError):
        actual.kind = "mutated"


def filtering_events(actual: Any, full: Any) -> None:
    expected: list[Any] = []
    index = 0
    while index < len(full):
        event = full[index]
        if event.kind != "precise-query":
            expected.append(event)
            index += 1
            continue
        indices = (event.time_index, event.direction_index, event.z_index, event.phase_index)
        stop = index + 1
        while (
            stop < len(full)
            and full[stop].kind == "precise-query"
            and (
                full[stop].time_index,
                full[stop].direction_index,
                full[stop].z_index,
                full[stop].phase_index,
            )
            == indices
        ):
            stop += 1
        expected.append((indices, stop - index))
        index = stop
    assert len(actual) == len(expected)
    for compact, reference in zip(actual, expected, strict=True):
        if isinstance(reference, tuple):
            assert compact.kind == "precise-query-count"
            assert (
                compact.time_index,
                compact.direction_index,
                compact.z_index,
                compact.phase_index,
            ) == reference[0]
            assert compact.details == (("count", reference[1]),)
            assert type(compact.details[0][1]) is int and compact.details[0][1] > 0
        else:
            event_equal(compact, reference)


def assert_summary(result: Any, full: Any, case: dict[str, Any]) -> None:
    assert type(result) is getattr(simrecon, "ReconstructionSummary", None)
    assert tuple(f.name for f in dataclasses.fields(result)) == SUMMARY_FIELDS
    assert not (set(getattr(result, "__dict__", {})) - set(SUMMARY_FIELDS))
    assert result.diagnostics == "summary"
    assert result.omitted_diagnostics == OMITTED
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.diagnostics = "full"
    for name in (
        "image",
        "x_um",
        "y_um",
        "z_um",
        "intensity_unit",
        "intensity_semantics",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
        "effective_wiener",
        "input_identities",
        "trace",
        "source_revision",
        "reference_sha256",
        "limitations",
    ):
        same(getattr(result, name), getattr(full, name))
    for name in ("carriers_cyc_um", "modulation", "raw_modulation", "branches"):
        same(getattr(result, name), getattr(full.parameters, name))
    inputs: dict[str, np.ndarray] = {}
    for root in ("acquisition", "carrier", "filtering"):
        inputs.update(
            {
                f"resolved_settings.{root}.{key}": value
                for key, value in case[root].items()
                if isinstance(value, np.ndarray)
            }
        )
    check_projection(
        result.resolved_settings, full.resolved_settings, "resolved_settings", inputs=inputs
    )
    check_projection(result.source_declarations, full.source_declarations, "source_declarations")
    projected_record(
        result.preparation, full.bands, "preparation", {"quadratures", "off_quadratures", "trace"}
    )
    projected_record(result.estimation, full.parameters, "estimation", {"overlaps", "trace"})
    assert len(result.filtering) == len(full.reconstructions)
    for t, (compact, known) in enumerate(zip(result.filtering, full.reconstructions, strict=True)):
        projected_record(
            compact,
            known,
            f"filtering.{t}",
            {"image", "filtered_quadratures", "x_um", "y_um", "z_um", "mode_trace"},
        )
    check_projection(result.transfer, full.transfer, "transfer")
    if full.calibration is None:
        assert result.calibration is None
    else:
        check_projection(result.calibration, full.calibration, "calibration")
    if full.layout is None:
        assert result.layout is None
    else:
        projected_record(
            result.layout, full.layout, "layout", {"images", "off_exposures", "exposure_background"}
        )
    assert len(result.overlap_builds) == len(full.parameters.overlaps)
    for index, (compact, build) in enumerate(
        zip(result.overlap_builds, full.parameters.overlaps, strict=True)
    ):
        assert tuple(f.name for f in dataclasses.fields(compact)) == (
            "index",
            "time_index",
            "direction_index",
            "purpose",
            "orders",
            "carrier_cyc_um",
        )
        assert compact.index == index
        with pytest.raises(dataclasses.FrozenInstanceError):
            compact.index = -1
        for name in ("index", "time_index", "direction_index", "purpose", "orders"):
            same(getattr(compact, name), getattr(build, name))
        same(compact.carrier_cyc_um, scalar_tuple(build.carrier_cyc_um))
    assert len(result.search_trace) == len(full.parameters.trace)
    for compact, event in zip(result.search_trace, full.parameters.trace, strict=True):
        event_equal(compact, event)
        details = dict(compact.details)
        if "overlap_index" in details:
            target = result.overlap_builds[details["overlap_index"]]
            assert target.time_index == compact.time_index
            assert target.direction_index == compact.direction_index
    assert len(result.preparation_trace) == len(full.bands.trace)
    for compact, event in zip(result.preparation_trace, full.bands.trace, strict=True):
        event_equal(compact, event)
    assert len(result.filtering_trace) == len(full.reconstructions)
    for compact, known in zip(result.filtering_trace, full.reconstructions, strict=True):
        filtering_events(compact, known.mode_trace)
    from reconstruction_memory_benchmark import retained_payload

    arrays = walk_arrays(result)
    payload = retained_payload(result)
    assert payload["array_payload_bytes"] == sum(array.nbytes for array in arrays)
    assert payload["unique_backings"] == 10
    assert payload["array_payload_bytes"] < retained_payload(full)["array_payload_bytes"]
    assert len(arrays) == 10  # image, xyz, three parameters, two guesses, Wiener schedule
    for index, array in enumerate(arrays):
        assert array.flags.owndata and array.base is None and not array.flags.writeable
        assert all(not np.shares_memory(array, other) for other in arrays[index + 1 :])
        assert all(not np.shares_memory(array, source) for source in walk_arrays(case))
    for descriptor in result.input_identities:
        with pytest.raises(dataclasses.FrozenInstanceError):
            descriptor.name = "mutated"
    assert sorted(item.name for item in result.input_identities) == [
        item.name for item in result.input_identities
    ]
    assert identity_values(next(i for i in result.input_identities if i.name == "specimen")) == (
        identity(case["specimen"], "specimen")
    )


def test_entry_exports_and_signature(summary_entry: Any) -> None:
    module = importlib.import_module("simrecon.workflow.reconstruct")
    assert module.reconstruct_summary is summary_entry
    assert module.ReconstructionSummary is getattr(simrecon, "ReconstructionSummary", None)
    assert (
        inspect.signature(summary_entry).parameters
        == inspect.signature(simrecon.reconstruct_workflow).parameters
    )
    with pytest.raises(TypeError):
        summary_entry()
    with pytest.raises(TypeError):
        summary_entry(**analytical_case(), filename="image.tif")


@pytest.mark.parametrize("complex_table", [False, True])
@pytest.mark.parametrize("entry_name", ["reconstruct_workflow", "reconstruct_summary"])
def test_ce07_independent_closed_form(entry_name: str, complex_table: bool) -> None:
    entry: Any = getattr(simrecon, entry_name, None)
    assert callable(entry), f"RM84 feature absent: {entry_name}"
    case = analytical_case(complex_table=complex_table)
    result: Any = entry(**case)
    expected_image, factor = analytical_expected(complex_table)
    actual_factor = (
        result.raw_modulation
        if entry_name.endswith("summary")
        else result.parameters.raw_modulation
    )
    # CE07 9.1: <=16-term reductions, bounded table <=8, h>=2, no search decisions.
    # 2^-38 absolute image and 2^-42 factor bounds include trig/FFT residuals.
    np.testing.assert_allclose(result.image, expected_image, rtol=0, atol=2**-38)
    np.testing.assert_allclose(actual_factor, factor, rtol=0, atol=2**-42)
    np.testing.assert_array_equal(result.x_um, [-2, -1, 0, 1])
    np.testing.assert_array_equal(result.y_um, [-1, 0])
    np.testing.assert_array_equal(result.z_um, [-1, 0])
    assert result.intensity_unit == "camera counts"
    if complex_table:
        wrong = analytical_expected(False)[0]
        assert np.max(np.abs(wrong - expected_image)) > 0.01
        assert abs(factor - 0.25) > 0.01


@pytest.mark.parametrize("name", SCENARIOS)
def test_full_summary_exact_scientific_and_projection_matrix(summary_entry: Any, name: str) -> None:
    case = scenario(name)
    full = simrecon.reconstruct_workflow(**case)
    result = summary_entry(**case)
    assert_summary(result, full, case)
    if name == "searched-reuse":
        assert result.branches == (("searched",) * 3, ("time0-reused",) * 3)
        same(result.carriers_cyc_um[0], result.carriers_cyc_um[1])
        assert not np.array_equal(result.modulation[0], result.modulation[1])
    if name == "searched-independent":
        assert result.branches == (("searched",) * 3,) * 2
    if name == "2d-search":
        assert any(dict(e.details).get("orders") == (0, 1) for e in result.search_trace)
    if name == "fractional":
        assert not np.any(result.image[:, 1:])
        assert not np.any(result.z_um)
        assert result.image.shape == (2, 3, 18, 24)
    if name.startswith("literal"):
        assert result.image.shape[0] == 2
        mapping = dict(result.layout)["source_direction_z"]
        assert identity_values(mapping)[0] == "layout.source_direction_z"
    if name == "filtering":
        np.testing.assert_array_equal(result.effective_wiener, [0.4375, 0.375])


def test_readonly_strided_inputs_and_post_return_isolation(summary_entry: Any) -> None:
    case = workload((1, 1, 2, 12, 16))
    storage = np.repeat(case["specimen"], 2, axis=-1)
    case["specimen"] = storage[..., ::2]
    case["specimen"].flags.writeable = False
    original = storage.copy()
    result = summary_entry(**case)
    snapshot = [value.copy() for value in walk_arrays(result)]
    np.testing.assert_array_equal(storage, original)
    storage[...] = -999
    for actual, expected in zip(walk_arrays(result), snapshot, strict=True):
        same(actual, expected)


def test_full_debug_storage_and_mutable_direct_stage_inputs() -> None:
    case = workload((2, 1, 2, 12, 16))
    case["specimen"][1] = case["specimen"][0]
    full = simrecon.reconstruct_workflow(**case)
    assert full.bands.quadratures.flags.writeable
    assert full.bands.noise_variance_factors.flags.writeable
    assert not np.shares_memory(full.image, full.reconstructions[0].image)
    assert not np.shares_memory(full.x_um, full.reconstructions[0].x_um)
    overlaps = full.parameters.overlaps
    assert len(overlaps) == 4
    for a, b in zip(overlaps[:2], overlaps[2:], strict=True):
        same(a.spatial, b.spatial)
        assert a.index != b.index
        assert not np.shares_memory(a.spatial, b.spatial)
    full.bands.quadratures[...] *= 0.5
    full.bands.noise_variance_factors[...] *= 2
    before = full.bands.quadratures.copy()
    estimated = simrecon.estimate_parameters(
        full.bands,
        full.transfer,
        initial_carriers_cyc_um=full.initial_carriers_cyc_um,
        **case["optics"],
        search_carriers=False,
    )
    known = simrecon.reconstruct_known(
        full.bands,
        full.transfer,
        carriers_cyc_um=estimated.carriers_cyc_um[0],
        modulation=estimated.modulation[0],
        **case["optics"],
        **case["filtering"],
    )
    assert np.all(np.isfinite(known.image))
    same(full.bands.quadratures, before)
    assert not np.array_equal(known.image, full.image)


@pytest.mark.parametrize(
    "code,change",
    [
        ("workflow_config", "key"),
        ("workflow_config", "optics"),
        ("workflow_config", "superseded"),
        ("workflow_input", "raw-nan"),
        ("workflow_input", "odd-x"),
        ("workflow_selection", "neither"),
        ("workflow_selection", "both"),
        ("workflow_metadata", "clock-label"),
        ("workflow_metadata", "unused-clock"),
        ("workflow_unsupported", "path"),
        ("workflow_unsupported", "fast-drift"),
        ("workflow_representation", "zoom"),
        ("workflow_representation", "stencil"),
        ("workflow_operation", "singular"),
        ("workflow_operation", "late-time"),
    ],
)
@pytest.mark.parametrize("entry_name", ["reconstruct_workflow", "reconstruct_summary"])
def test_failure_categories_no_partial_or_input_mutation(
    entry_name: str, code: str, change: str
) -> None:
    entry: Any = getattr(simrecon, entry_name, None)
    assert callable(entry), f"RM84 feature absent: {entry_name}"
    case = workload((2, 3, 2, 12, 16))
    if change == "key":
        case["filtering"]["save_separated"] = True
    elif change == "optics":
        del case["optics"]["wavelength_nm"]
    elif change == "superseded":
        case["acquisition"].update(
            phase_steps_rad=np.ones(3), phase_policy="steps", phases_rad=np.full((3, 5), np.nan)
        )
    elif change == "raw-nan":
        case["specimen"][0, 0, 0, 0, 0, 0] = np.nan
    elif change == "odd-x":
        case["specimen"] = case["specimen"][..., :-1]
    elif change == "neither":
        case["transfer"] = None
    elif change == "both":
        from c_workflow_oracle import bead_fixture

        raw, settings = bead_fixture(z=2, phases=5)
        case["calibration"] = dict(
            raw=raw, settings=settings, identity=dict(id="bead", intensity_unit="counts")
        )
    elif change == "clock-label":
        case["header_timestamp_unit"] = "seconds"
    elif change == "unused-clock":
        case["header_timestamps"] = np.array([0.0])
        case["header_timestamp_unit"] = "seconds"
    elif change == "path":
        case["specimen"] = "decoded.mrc"
    elif change == "fast-drift":
        case["acquisition"].update(storage_order="z-major", drift_between=True)
    elif change == "zoom":
        case["acquisition"]["axial_zoom"] = 2**31
    elif change == "stencil":
        from simrecon import declare_otf

        case["transfer"] = declare_otf(
            np.ones((3, 1, 1)), layout="radial", dkr_cyc_um=0.001, dkz_cyc_um=0.125
        )
    elif change == "singular":
        case["acquisition"].update(phases_rad=np.zeros((3, 5)), phase_policy="supplied")
    elif change == "late-time":
        case["specimen"][1] = 0
    arrays = walk_arrays(case)
    snapshots = [array.copy() for array in arrays]
    with pytest.raises(simrecon.WorkflowError) as caught:
        entry(**case)
    assert caught.value.code == code
    assert caught.value.stage in {
        "declaration",
        "layout",
        "transfer",
        "calibration",
        "preparation",
        "estimation",
        "reconstruction",
        "result",
    }
    assert caught.value.message
    if change == "late-time":
        assert caught.value.stage == "estimation" and caught.value.time_index == 1
    for actual, before in zip(arrays, snapshots, strict=True):
        same(actual, before)


def test_summary_is_not_a_direct_stage_input(summary_entry: Any) -> None:
    case = analytical_case()
    result = summary_entry(**case)
    with pytest.raises(simrecon.ParameterEstimationError):
        simrecon.estimate_parameters(
            result,
            case["transfer"],
            initial_carriers_cyc_um=result.initial_carriers_cyc_um,
            **case["optics"],
            search_carriers=False,
        )
    with pytest.raises(simrecon.ReconstructionError):
        simrecon.reconstruct_known(
            result,
            case["transfer"],
            carriers_cyc_um=result.carriers_cyc_um[0],
            modulation=result.modulation[0],
            **case["optics"],
            wiener=1.0,
        )


@pytest.mark.parametrize(
    "name",
    [
        "empirical-z1",
        "empirical-z2",
        "empirical-complex-search-camera-phase",
        "within2d-fitted",
        "within2d-unfitted",
        "between-first-off-and-persistent-sentinel",
        "dampen-before-omit-precise3d",
        "true2d-full-floors-products",
        "odd-y",
        "empty-y-precise",
        "steps-supersede-singular-list",
        "signed-negative-counts",
    ],
)
def test_summary_reuses_independent_finite_observer(summary_entry: Any, name: str) -> None:
    from c_workflow_oracle import control_cases, error_budget, observe
    from c_workflow_support import close, keywords

    case = control_cases()[name]
    # Observe and freeze conditional bounds before any product execution.
    expected = observe(case)
    budget = error_budget(case, expected)
    selection = "raw-beads" if case.bead is not None else "accepted-transfer"
    inputs: dict[str, Any] = dict(specimen=case.raw, **keywords(case, selection=selection))
    result = summary_entry(**inputs)
    full = simrecon.reconstruct_workflow(**inputs)
    assert_summary(result, full, inputs)
    close(result.image, expected["image"], budget["native_bounds"]["image"], label=name)
    parameters, bounds = expected["parameters"], budget["parameter_bounds"]
    close(
        result.carriers_cyc_um,
        parameters["carriers_cyc_um"],
        bounds["carrier_radius"][..., None],
        label="independent summary carriers",
    )
    for key in ("raw_modulation", "modulation"):
        close(getattr(result, key), parameters[key], bounds[key], label=key)
    assert result.branches == parameters["branches"]
    if name.startswith("empirical"):
        samples = full.transfer.samples
        assert np.any(samples != samples.astype(np.complex64).astype(np.complex128))
        assert identity_values(dict(result.transfer)["samples"]) == identity(
            samples, "transfer.samples"
        )


@pytest.mark.parametrize("z", [1, 2])
def test_prepared_empirical_projection_and_ownership(summary_entry: Any, z: int) -> None:
    from c_workflow_oracle import control_cases
    from c_workflow_support import keywords

    case = control_cases()[f"empirical-z{z}"]
    inputs: dict[str, Any] = dict(specimen=case.raw, **keywords(case, selection="prepared-otf"))
    result = summary_entry(**inputs)
    full = simrecon.reconstruct_workflow(**inputs)
    assert_summary(result, full, inputs)
    snapshots = [value.copy() for value in walk_arrays(result)]
    for array in walk_arrays(inputs["transfer"]):
        array.setflags(write=True)
        array.flat[0] += 1
    for actual, expected in zip(walk_arrays(result), snapshots, strict=True):
        same(actual, expected)


@pytest.mark.parametrize(
    "mode,layout,sections",
    [
        ("3d", "radial", 2),
        ("2d", "radial", 1),
        ("2d", "full", 2),
        ("3d", "full", 7),
    ],
)
def test_decoded_summary_projection(
    summary_entry: Any, mode: str, layout: str, sections: int
) -> None:
    from c_workflow_support import keywords
    from test_c_workflow_records import decoded_case

    case, declaration, mapping, unused = decoded_case(mode, layout, sections)
    inputs: dict[str, Any] = dict(specimen=case.raw, **keywords(case))
    inputs["transfer"] = declaration
    full = simrecon.reconstruct_workflow(**inputs)
    result = summary_entry(**inputs)
    assert_summary(result, full, inputs)
    binding = dict(dict(result.source_declarations)["decoded_transfer_binding"])
    assert binding["section_map"] == mapping
    assert binding["unused_sections"] == unused


@pytest.mark.parametrize("which", ["allocation", "interruption", "backend"])
def test_summary_external_failure_semantics(
    summary_entry: Any, monkeypatch: Any, which: str
) -> None:
    import scipy.fft

    case = analytical_case()
    expected, _ = analytical_expected(False)
    kind = (
        MemoryError
        if which == "allocation"
        else KeyboardInterrupt
        if which == "interruption"
        else RuntimeError
    )
    sentinel = kind("RM84 external dependency unavailable")
    calls: list[bool] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        calls.append(True)
        raise sentinel

    outcome: Any = None
    caught: BaseException | None = None
    with monkeypatch.context() as patch:
        if which == "backend":
            for module in (np.fft, scipy.fft):
                for name in (
                    "fft",
                    "ifft",
                    "fftn",
                    "ifftn",
                    "fft2",
                    "ifft2",
                    "rfft",
                    "irfft",
                    "rfftn",
                    "irfftn",
                    "rfft2",
                    "irfft2",
                ):
                    patch.setattr(module, name, fail)
        else:
            for name in (
                "array",
                "empty",
                "zeros",
                "ones",
                "full",
                "empty_like",
                "zeros_like",
                "ones_like",
                "copy",
                "stack",
                "concatenate",
            ):
                patch.setattr(np, name, fail)
        try:
            outcome = summary_entry(**case)
        except BaseException as error:
            caught = error
    if calls:
        assert caught is not None
        if which == "backend":
            assert isinstance(caught, simrecon.WorkflowError)
            assert caught.code == "workflow_operation"
            assert caught.stage in {"preparation", "estimation", "reconstruction"}
        else:
            assert isinstance(caught, kind)
        chain: list[BaseException] = []
        while caught is not None and all(caught is not item for item in chain):
            chain.append(caught)
            caught = caught.__cause__
        assert any(error is sentinel for error in chain)
    else:
        # Import/backend alternatives are permitted; absence of interception
        # is a finite positive proof and is not fault-path coverage.
        assert caught is None
        np.testing.assert_allclose(outcome.image, expected, rtol=0, atol=2**-38)


@pytest.mark.parametrize(
    "fault",
    [
        "singular-phase",
        "zero-regression",
        "later-time-zero",
        "precise-dc",
        "negative-power-zero",
        "dampen-c0",
        "true2d-omit-kz0",
        "zero-slope-selected",
    ],
)
def test_summary_inherited_actual_numeric_failures(
    summary_entry: Any, monkeypatch: Any, fault: str
) -> None:
    import test_c_workflow_validation as inherited

    monkeypatch.setattr(inherited, "entry", lambda: summary_entry)
    inherited.test_real_operation_failures_preserve_cause_and_no_partial_result(fault)


@pytest.mark.parametrize("stage", ["preparation", "estimation"])
def test_summary_later_time_direction_failure_context(
    summary_entry: Any, monkeypatch: Any, stage: str
) -> None:
    import test_c_workflow_failures as inherited

    monkeypatch.setattr(inherited, "entry", lambda: summary_entry)
    inherited.test_real_later_time_direction_failure_keeps_local_context(stage)


@pytest.mark.parametrize(
    "fault",
    [
        "fast-d2",
        "within3d-d3",
        "within3d-fast-d1",
        "within2d-n0",
        "within2d-fit-no-adjust",
        "prepass-off-nontermination",
    ],
)
def test_summary_inherited_structurally_unsafe_paths(
    summary_entry: Any, monkeypatch: Any, fault: str
) -> None:
    import test_c_workflow_validation as inherited

    monkeypatch.setattr(inherited, "entry", lambda: summary_entry)
    inherited.test_recognized_unsafe_branches_are_unsupported(fault)


@pytest.mark.parametrize(
    "fault",
    ["fractional-extents", "source-byte-limit", "wide-complex-workspace", "unsafe-stencil"],
)
def test_summary_inherited_representation_limits(
    summary_entry: Any, monkeypatch: Any, fault: str
) -> None:
    import test_c_workflow_validation as inherited

    monkeypatch.setattr(inherited, "entry", lambda: summary_entry)
    inherited.test_representation_limits_with_real_small_backing(fault)


@pytest.mark.parametrize(
    "root",
    [
        "acquisition",
        "optics",
        "carrier",
        "filtering",
        "specimen_identity",
        "transfer_identity",
        "transfer_identity.optics",
        "calibration",
        "calibration.settings",
        "calibration.identity",
        "transfer",
    ],
)
@pytest.mark.parametrize("mutation", ["unknown", "missing"])
def test_summary_complete_mapping_boundaries(summary_entry: Any, root: str, mutation: str) -> None:
    from test_c_workflow_validation import REQUIRED, schema_input

    raw, kwargs, mapping = schema_input(root)
    if mutation == "unknown":
        mapping["save_separated"] = True
    elif mutation == "missing":
        for key in REQUIRED[root]:
            value = mapping.pop(key)
            with pytest.raises(simrecon.WorkflowError) as error:
                summary_entry(raw, **kwargs)
            assert error.value.code == "workflow_config"
            mapping[key] = value
        return
    with pytest.raises(simrecon.WorkflowError) as error:
        summary_entry(raw, **kwargs)
    assert error.value.code == "workflow_config"


@pytest.mark.parametrize("entry_name", ["reconstruct_workflow", "reconstruct_summary"])
def test_discarded_regression_correlation_must_remain_finite(entry_name: str) -> None:
    entry: Any = getattr(simrecon, entry_name, None)
    assert callable(entry), f"RM84 feature absent: {entry_name}"
    case = analytical_case()
    amplitudes = np.array([3e38, 1e38, 1e38], dtype=np.float32)
    case["specimen"][...] = amplitudes[None, None, :, None, None, None]
    case["acquisition"]["flatfield_slope"] = np.full((2, 4), float(np.float32(3e38)))
    # Corrected bands and forward factors are finite; squaring the cross
    # reduction for the required auxiliary correlation overflows binary64.
    # Omitting only that diagnostic/check would falsely turn failure into success.
    before = case["specimen"].copy()
    with pytest.raises(simrecon.WorkflowError) as error:
        entry(**case)
    assert error.value.code == "workflow_operation"
    assert error.value.stage == "estimation"
    assert error.value.__cause__ is not None
    same(case["specimen"], before)


@pytest.mark.parametrize("path,key,value", inherited_validation.BAD_MAPPED)
def test_summary_inherited_mapped_value_domain(
    summary_entry: Any, monkeypatch: Any, path: str, key: str, value: Any
) -> None:
    monkeypatch.setattr(inherited_validation, "entry", lambda: summary_entry)
    inherited_validation.test_single_invalid_mapped_value(path, key, value)


@pytest.mark.parametrize(
    "channels,no_time,no_z",
    [(None, False, False), (2, False, False), (None, True, True), (2, True, True)],
)
def test_summary_neutral_channel_selection(
    summary_entry: Any, channels: int | None, no_time: bool, no_z: bool
) -> None:
    from c_workflow_oracle import coordinate_case
    from c_workflow_support import keywords
    from test_c_workflow_records import declare_selected

    case = coordinate_case(mode="2d" if no_z else "3d")
    record = declare_selected(case, channels=channels, no_time=no_time, no_z=no_z)
    inputs = keywords(case)
    inputs.update(specimen=record, channel_index=None if channels is None else channels - 1)
    full = simrecon.reconstruct_workflow(**inputs)
    result = summary_entry(**inputs)
    same(result.image, full.image)
    same(result.input_identities, full.input_identities)
    check_projection(result.source_declarations, full.source_declarations, "source_declarations")
    assert identity_values(
        next(i for i in result.input_identities if i.name == "specimen.data")
    ) == (identity(record.data, "specimen.data"))
    assert dict(result.source_declarations)["selected_channel"] == (
        None if channels is None else channels - 1
    )


def test_original_nominal_array_is_projected_before_metadata_snapshot(summary_entry: Any) -> None:
    from test_c_workflow_records import original_identity_inputs

    _, specimen, inputs, arrays = original_identity_inputs("raw-nominal-phases", "plain")
    full = simrecon.reconstruct_workflow(specimen, **inputs)
    result = summary_entry(specimen, **inputs)
    same(result.image, full.image)
    same(result.input_identities, full.input_identities)
    path = "source_declarations.raw_acquisition_metadata.nominal_phases_rad"
    check_projection(
        result.source_declarations,
        full.source_declarations,
        "source_declarations",
        inputs={path: arrays["specimen.nominal_phases_rad"]},
    )
    descriptor = dict(dict(result.source_declarations)["raw_acquisition_metadata"])[
        "nominal_phases_rad"
    ]
    assert identity_values(descriptor) == identity(arrays["specimen.nominal_phases_rad"], path)


def test_direct_zero_and_signed_known_carriers_remain_permitted() -> None:
    case = analytical_case()
    full = simrecon.reconstruct_workflow(**case)
    for x_carrier in (0.0, -0.125):
        carriers = np.array([[x_carrier, 0.0]])
        estimated = simrecon.estimate_parameters(
            full.bands,
            full.transfer,
            initial_carriers_cyc_um=carriers,
            **case["optics"],
            search_carriers=False,
        )
        same(estimated.carriers_cyc_um[0], carriers)
        result = simrecon.reconstruct_known(
            full.bands,
            full.transfer,
            carriers_cyc_um=carriers,
            modulation=estimated.modulation[0],
            **case["optics"],
            **case["filtering"],
        )
        assert np.isfinite(result.image).all()
        if x_carrier == 0:
            np.testing.assert_allclose(estimated.modulation, 0.25, rtol=0, atol=2**-42)
            np.testing.assert_allclose(result.image, 13.5 / 2.125, rtol=0, atol=2**-38)
