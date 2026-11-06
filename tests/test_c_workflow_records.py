"""Selection, layout, snapshots, clock meaning and decoded-table composition."""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from c_workflow_oracle import (
    OPTICS,
    Case,
    Table,
    array_digest,
    constant_case,
    control_cases,
    coordinate_case,
    cubic,
    error_budget,
    gamma,
    literal_metadata_cases,
    observe,
    patterned_case,
)
from c_workflow_support import (
    assert_scientific,
    close,
    entry,
    fields_of,
    frozen,
    keywords,
    public,
    run,
)
from test_c_workflow_validation import assert_error


def decoded_case(
    mode: str, layout: str, sections: int
) -> tuple[Case, dict[str, Any], tuple[Any, ...], tuple[int, ...]]:
    case = patterned_case(mode=mode, directions=1, times=1)
    if layout == "radial":
        shape = (sections, 1, 24) if mode == "2d" else (sections, 24, 2)
    else:
        shape = (sections, 16, 16)
    section, row, col = np.indices(shape)
    values = (1 + section / 8 + row / 64 + col / 128) + 1j * (section / 16 + row / 128 - col / 256)
    dkz = 1.0 if mode == "2d" else 0.5
    declaration = dict(
        kind="decoded-sections",
        layout=layout,
        samples=values,
        dkr_cyc_um=0.125,
        dkz_cyc_um=dkz,
        order_encoding="combined-orders",
    )
    o = 3
    if mode == "3d" and layout == "full":
        k = sections // o
        mapping: tuple[Any, ...] = tuple(tuple(range(m * k, (m + 1) * k)) for m in range(o))
        unused = tuple(range(o * k, sections))
        samples = values[: o * k].reshape(o, k, *values.shape[1:])
    else:
        mapping = tuple(m if m < sections else 0 for m in range(o))
        unused = tuple(range(o, sections))
        if mode == "2d" and layout == "radial":
            samples = values[list(mapping), 0, :, None]
        elif mode == "2d":
            samples = values[list(mapping), None]
        else:
            samples = values[list(mapping)]
    case.table = Table(samples, layout, 0.125, dkz)
    return case, declaration, mapping, unused


@pytest.mark.parametrize(
    ("mode", "layout", "sections"),
    [
        ("3d", "radial", 1),
        ("3d", "radial", 2),
        ("3d", "radial", 4),
        ("2d", "radial", 1),
        ("2d", "radial", 2),
        ("2d", "full", 2),
        ("2d", "full", 4),
        ("3d", "full", 3),
        ("3d", "full", 6),
        ("3d", "full", 7),
    ],
)
def test_decoded_binding_is_consumed_by_real_workflow(
    mode: str, layout: str, sections: int
) -> None:
    case, declaration, section_map, unused = decoded_case(mode, layout, sections)
    expected = observe(case)
    result = run(case, overrides={"transfer": declaration})
    assert_scientific(case, result, expected)
    np.testing.assert_array_equal(result.transfer.samples, case.table.samples)
    binding = dict(dict(result.source_declarations)["decoded_transfer_binding"])
    assert tuple(binding) == (
        "original_shape",
        "layout",
        "effective_mode",
        "section_map",
        "unused_sections",
        "dkr_cyc_um",
        "dkz_cyc_um",
    )
    assert binding == dict(
        original_shape=declaration["samples"].shape,
        layout=layout,
        effective_mode=mode,
        section_map=section_map,
        unused_sections=unused,
        dkr_cyc_um=0.125,
        dkz_cyc_um=declaration["dkz_cyc_um"],
    )
    identity = next(i for i in result.input_identities if i.name == "transfer.samples")
    assert (identity.shape, identity.dtype, identity.sha256) == array_digest(declaration["samples"])


def test_full3d_remainder_is_hashed_but_not_consumed_or_duplicated() -> None:
    case7, declaration7, _, _ = decoded_case("3d", "full", 7)
    declaration6 = copy.deepcopy(declaration7)
    declaration6["samples"] = declaration7["samples"][:6].copy()
    result7 = run(case7, overrides={"transfer": declaration7})
    result6 = run(case7, overrides={"transfer": declaration6})
    changed = copy.deepcopy(declaration7)
    changed["samples"][6] = -31 + 17j
    result_changed = run(case7, overrides={"transfer": changed})
    for result in (result6, result_changed):
        np.testing.assert_array_equal(result.transfer.samples, result7.transfer.samples)
        np.testing.assert_array_equal(result.image, result7.image)
    digest7 = next(i.sha256 for i in result7.input_identities if i.name == "transfer.samples")
    digest_changed = next(
        i.sha256 for i in result_changed.input_identities if i.name == "transfer.samples"
    )
    assert digest7 != digest_changed
    changed["samples"][6, 0, 0] = np.nan
    entry()
    kwargs = keywords(case7)
    kwargs["transfer"] = changed
    assert_error("workflow_input", case7.raw, kwargs)


@pytest.mark.parametrize(
    "fault,code",
    [
        ("full3d-k0", "workflow_representation"),
        ("radial2d-plane", "workflow_representation"),
        ("decoded2d-dkz", "workflow_config"),
        ("encoding", "workflow_config"),
        ("kind", "workflow_config"),
        ("samples-kind", "workflow_input"),
        ("samples-rank", "workflow_input"),
        ("samples-nonexact", "workflow_input"),
    ],
)
def test_decoded_single_invalid_and_adjacent_positive(fault: str, code: str) -> None:
    entry()
    case, declaration, _, _ = decoded_case(
        "2d" if "2d" in fault else "3d", "radial" if "radial" in fault else "full", 3
    )
    if fault == "full3d-k0":
        declaration["samples"] = declaration["samples"][:2]
    elif fault == "radial2d-plane":
        declaration["samples"] = np.repeat(declaration["samples"], 2, axis=1)
    elif fault == "decoded2d-dkz":
        declaration["dkz_cyc_um"] = 0.5
    elif fault == "encoding":
        declaration["order_encoding"] = "five-quadratures"
    elif fault == "kind":
        declaration["kind"] = "magnitude-phase"
    elif fault == "samples-kind":
        declaration["samples"] = np.ones(declaration["samples"].shape, dtype=bool)
    elif fault == "samples-rank":
        declaration["samples"] = declaration["samples"][0]
    else:
        declaration["samples"] = np.full(declaration["samples"].shape, 0.1 + 0.1j)
    kwargs = keywords(case)
    kwargs["transfer"] = declaration
    assert_error(code, case.raw, kwargs)


@pytest.mark.parametrize("label", ["seconds", "milliseconds", "acquisition-clock-ticks", " ms "])
@pytest.mark.parametrize(
    "control",
    [
        "no-drift",
        "within2d-fitted",
        "within3d-cubic-first-block",
        "within2d-exact-cubic-impulses",
        "within3d-exact-cubic-impulses",
    ],
)
def test_clock_labels_preserve_numeric_meaning_and_cubic_units(label: str, control: str) -> None:
    if control == "no-drift":
        case = constant_case()
        case.extras.update(
            header_timestamps=np.arange(6, dtype=float), header_timestamp_unit="seconds"
        )
    else:
        case = control_cases()[control]
    expected = observe(case)
    budget = error_budget(case, expected)
    baseline = run(case)
    case.extras["header_timestamp_unit"] = label
    renamed = run(case)
    assert dict(renamed.resolved_settings)["header_timestamp_unit"] == label
    for left, right in (
        (baseline.image, renamed.image),
        (baseline.bands.quadratures, renamed.bands.quadratures),
        (baseline.parameters.modulation, renamed.parameters.modulation),
        (baseline.parameters.carriers_cyc_um, renamed.parameters.carriers_cyc_um),
        (baseline.bands.exposure_displacements_pixels, renamed.bands.exposure_displacements_pixels),
        (baseline.bands.header_timestamps_after, renamed.bands.header_timestamps_after),
    ):
        np.testing.assert_array_equal(left, right)
    assert baseline.input_identities == renamed.input_identities
    actual_events = [e for e in renamed.bands.trace if e.kind == "cubic-fit"]
    truth_events = [e for e in expected["preparation"]["events"] if e["kind"] == "cubic"]
    assert len(actual_events) == len(truth_events)
    cubic_bounds = budget["preparation_bounds"]["cubics"]
    assert len(cubic_bounds) == len(truth_events)
    for actual, truth, cubic_bound in zip(actual_events, truth_events, cubic_bounds, strict=True):
        details = dict(actual.details)
        for key in (
            "matrix",
            "coefficients",
            "evaluated_xy",
            "sample_timestamps_after",
            "evaluation_timestamps_after",
        ):
            if key in ("matrix", "sample_timestamps_after", "evaluation_timestamps_after"):
                np.testing.assert_array_equal(details[key], truth[key])
            else:
                # Diagnostic evaluated_xy is BEFORE the measured-direction
                # subtraction. Its error map differs from applied motion.
                bound = (
                    cubic_bound["coefficients"]
                    if key == "coefficients"
                    else cubic_bound["fitted_evaluation"]
                )
                close(details[key], truth[key], bound, label=f"clock/cubic {key}")
        # Rows correspond to eta,eta²,eta³. B0 is fixed, never a fitted
        # intercept or a converted seconds/milliseconds coefficient.
        assert details["coefficients"].shape == (3, 2)
    algebra = cubic(
        np.array([0.0, 1.0, 2.0, 3.0]),
        np.column_stack(([0.0, 1.0, 8.0, 27.0], [0.0, 2.0, 16.0, 54.0])),
        np.array([0.0, 1.0, 2.0, 3.0]),
    )
    close(
        algebra["coefficients"],
        [[0, 0], [0, 0], [1, 2]],
        gamma(4096) * 64,
        label="independent cubic units sanity check",
    )


def declare_selected(
    case: Case, *, channels: int | None = 2, no_time: bool = False, no_z: bool = False
) -> Any:
    raw = case.raw
    axes = ["time", "orientation", "phase", "z", "y", "x"]
    if no_z:
        raw = raw[:, :, :, 0]
        axes.remove("z")
    if no_time:
        raw = raw[0]
        axes.remove("time")
    if channels is not None:
        raw = np.stack([raw + 32 * c for c in range(channels)], axis=0)
        axes.insert(0, "channel")
    # Deliberately change source slow-axis order, retaining y,x terminals.
    permutation = list(range(len(axes) - 2))[::-1] + [len(axes) - 2, len(axes) - 1]
    source = np.transpose(raw, permutation)
    source_axes = [axes[i] for i in permutation]
    config = dict(
        version=1,
        acquisition_kind="specimen_sim",
        axes=source_axes,
        sampling_um=dict(x=1.0, y=1.0, z=None if no_z else 1.0),
        intensity_unit="detector-counts",
        acquisition_id="opaque-acq",
        calibration_id="not-an-automatic-selection",
        wavelengths_nm={"0": 777.0},
    )
    return public().declare_acquisition(
        source,
        config=config,
        original_metadata=dict(opaque=b"no clock unit", clock_unit="milliseconds"),
    )


@pytest.mark.parametrize("channels", [None, 1, 2])
@pytest.mark.parametrize("no_time,no_z", [(False, False), (True, False), (True, True)])
def test_neutral_named_layout_selection_preserves_actual_pixels(
    channels: int | None, no_time: bool, no_z: bool
) -> None:
    case = coordinate_case(mode="2d" if no_z else "3d")
    record = declare_selected(case, channels=channels, no_time=no_time, no_z=no_z)
    canonical = case.raw[:, :, :, 0] if no_z else case.raw
    if no_time:
        canonical = canonical[0]
    if channels is not None:
        canonical = np.stack(
            [canonical + 32 * c for c in range(channels)], axis=0 if no_time else 1
        )
    np.testing.assert_array_equal(record.data, canonical)
    channel = None if channels is None else channels - 1
    selected = copy.deepcopy(case)
    if channel is not None:
        selected.raw += 32 * channel
    expected = observe(selected)
    result = run(case, specimen=record, overrides=dict(channel_index=channel))
    assert_scientific(selected, result, expected)
    declarations = dict(result.source_declarations)
    assert declarations["selected_channel"] == channel
    metadata = dict(declarations["raw_acquisition_metadata"])
    assert metadata["axes"] == record.axes
    assert metadata["acquisition_id"] == "opaque-acq"
    identities = {i.name: i for i in result.input_identities}
    for name, array in (("specimen.data", record.data), ("selected_specimen", selected.raw)):
        identity = identities[name]
        assert (identity.shape, identity.dtype, identity.sha256) == array_digest(array)
    assert result.calibration is None
    assert dict(result.resolved_settings)["optics"] == tuple(OPTICS.items())


@pytest.mark.parametrize(
    "fault",
    [
        "present-channel-missing",
        "channel-bool",
        "channel-range",
        "channel-float",
        "absent-channel-index",
        "ndarray-channel-index",
        "known-x",
        "known-z",
        "known-unit",
        "invalid-kind",
        "invalid-used-data",
        "invalid-provenance",
    ],
)
def test_neutral_records_single_invalid_scientific_boundary(fault: str) -> None:
    entry()
    case = constant_case()
    record = declare_selected(case, channels=None if fault == "absent-channel-index" else 2)
    kwargs = keywords(case)
    kwargs["channel_index"] = 0
    raw: Any = record
    code = "workflow_input"
    if fault == "present-channel-missing":
        del kwargs["channel_index"]
    elif fault == "channel-bool":
        kwargs["channel_index"] = True
    elif fault == "channel-range":
        kwargs["channel_index"] = 2
    elif fault == "channel-float":
        kwargs["channel_index"] = 0.0
    elif fault == "ndarray-channel-index":
        raw = case.raw
    elif fault == "known-x":
        record.sampling_um["x"] = 0.5
        code = "workflow_metadata"
    elif fault == "known-z":
        record.sampling_um["z"] = 0.5
        code = "workflow_metadata"
    elif fault == "known-unit":
        object.__setattr__(record, "intensity_unit", "photoelectrons")
        code = "workflow_metadata"
    elif fault == "invalid-kind":
        object.__setattr__(record, "acquisition_kind", "detection_psf")
    elif fault == "invalid-used-data":
        record.data.flat[0] = np.nan
    elif fault == "invalid-provenance":
        object.__setattr__(record, "provenance", ({"field": "axes"},))
    assert_error(code, raw, kwargs)


@pytest.mark.parametrize(
    "representation",
    ["big-endian", "fortran", "strided-readonly", "float16", "float32", "uint16", "int32"],
)
def test_real_array_ownership_representations_and_endian_hashes(representation: str) -> None:
    case = constant_case()
    if representation == "big-endian":
        case.raw = case.raw.astype(">f8")
    elif representation == "fortran":
        case.raw = np.asfortranarray(case.raw)
    elif representation == "strided-readonly":
        backing = np.repeat(case.raw, 2, axis=-1)
        case.raw = backing[..., ::2]
        case.raw.setflags(write=False)
    else:
        case.raw = case.raw.astype(representation)
    # Mathematical maps preserve signed zero and binary64 values in hashes;
    # pixel raw representability remains a separate requirement.
    background = np.zeros((2, 4), dtype=">f8")
    background[0, 1] = -0.0
    case.acquisition["background"] = background
    before = array_digest(case.raw)
    result = run(case)
    assert_scientific(case, result)
    assert array_digest(case.raw) == before
    identities = {i.name: i for i in result.input_identities}
    for name, array in (("specimen", case.raw), ("acquisition.background", background)):
        i = identities[name]
        assert (i.shape, i.dtype, i.sha256) == array_digest(array)
    assert array_digest(background)[2] != array_digest(np.zeros((2, 4)))[2]
    assert not np.shares_memory(result.transfer.samples, case.table.samples)
    assert not np.shares_memory(result.bands.quadratures, case.raw)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        result.image = np.zeros_like(result.image)


def ownership_metadata_inputs() -> tuple[dict[str, Any], dict[str, Any], Any]:
    """Independent declarations and recursive expected raw metadata, before product calls."""
    axes = ("time", "orientation", "phase", "z", "y", "x")
    config = dict(
        version=1,
        acquisition_kind="specimen_sim",
        axes=list(axes),
        sampling_um=dict(x=1.0, y=1.0, z=1.0),
        intensity_unit="detector-counts",
    )
    metadata = dict(
        opaque=b"opaque\x00", nested=dict(records=[dict(value=7, ok=True), ("tail", None)])
    )
    provenance = tuple(
        dict(field=key, old=None, new=copy.deepcopy(config[key]), source="config")
        for key in sorted(config)
        if key != "version"
    )
    expected = dict(
        axes=axes,
        source_axes=axes,
        source_shape=(1, 1, 3, 2, 2, 4),
        acquisition_kind="specimen_sim",
        sampling_um=dict(x=1.0, y=1.0, z=1.0),
        wavelengths_nm={},
        nominal_phases_rad=None,
        nominal_phase_axes=(),
        intensity_unit="detector-counts",
        acquisition_id=None,
        calibration_id=None,
        original_config=copy.deepcopy(config),
        original_metadata=copy.deepcopy(metadata),
        provenance=provenance,
    )
    return config, metadata, frozen(expected)


def assert_recursive_snapshot(actual: Any, expected: Any) -> None:
    """Check value AND recursive immutable representation, without self-comparison."""
    assert type(actual) is type(expected)
    if type(expected) is tuple:
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            assert_recursive_snapshot(left, right)
    else:
        assert expected is None or type(expected) in (str, bytes, int, float, bool, complex)
        assert actual == expected


def ownership_expected_declarations(specimen_kind: str) -> Any:
    """Freeze independent literals, never a result reference."""
    _, _, expected_raw = ownership_metadata_inputs()
    return (
        (
            "specimen_identity",
            (
                (
                    "files",
                    (
                        (
                            ("bytes", 1234),
                            ("name", "raw.mrc"),
                            ("role", "specimen"),
                            ("sha256", "a" * 64),
                        ),
                    ),
                ),
                ("id", "raw-observations"),
                ("intensity_unit", "detector-counts"),
            ),
        ),
        (
            "transfer_identity",
            (
                ("id", "selected-transfer"),
                ("intensity_unit", "dimensionless-transfer"),
                (
                    "optics",
                    (("immersion_index", 1.0), ("numerical_aperture", 1.0), ("wavelength_nm", 500)),
                ),
            ),
        ),
        ("calibration_identity", None),
        ("selected_channel", None),
        ("raw_acquisition_metadata", expected_raw if specimen_kind == "named-record" else None),
        ("decoded_transfer_binding", None),
    )


def _assert_snapshot_mutable_records(specimen_kind: str) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    kwargs["specimen_identity"]["files"] = [
        dict(name="raw.mrc", bytes=1234, sha256="a" * 64, role="specimen")
    ]
    originals = copy.deepcopy(kwargs)
    config, raw_metadata, _ = ownership_metadata_inputs()
    specimen: Any = case.raw
    if specimen_kind == "named-record":
        specimen = public().declare_acquisition(
            case.raw, config=config, original_metadata=raw_metadata
        )
    expected_declarations = ownership_expected_declarations(specimen_kind)
    result = entry()(specimen, **kwargs)
    assert_recursive_snapshot(result.source_declarations, expected_declarations)
    settings = copy.deepcopy(result.resolved_settings)
    consumed = result.transfer.samples.copy()
    kwargs["specimen_identity"]["files"][0]["bytes"] = 9999
    kwargs["acquisition"]["background"] = 999
    # Accepted source records are snapshotted, including their writable
    # underlying values when a caller re-enables NumPy writes after return.
    kwargs["transfer"].samples.setflags(write=True)
    kwargs["transfer"].samples[:] = 0
    raw_metadata["nested"]["records"][0]["value"] = -3
    if specimen_kind == "named-record":
        # RawAcquisition nested metadata is mutable by public convention.
        # These are genuine neutral-record backing values, not forged fields.
        specimen.original_metadata["nested"]["records"][0]["value"] = 999
        specimen.original_config["sampling_um"]["x"] = 123.0
        specimen.sampling_um["y"] = 456.0
        specimen.provenance[0]["new"] = "caller-mutated"
    assert_recursive_snapshot(result.source_declarations, expected_declarations)
    assert result.resolved_settings == settings
    np.testing.assert_array_equal(result.transfer.samples, consumed)
    assert originals["acquisition"] == case.acquisition
    assert fields_of(result.input_identities[0]) == ("name", "shape", "dtype", "sha256")


def test_snapshot_mutable_records_settings_and_source_claims() -> None:
    _assert_snapshot_mutable_records("ndarray")


def test_snapshot_nested_named_raw_metadata_is_independent() -> None:
    _assert_snapshot_mutable_records("named-record")


@pytest.mark.parametrize(
    "variant",
    [
        "zero-signed-map",
        "numpy-scalars",
        "raw-float32-max",
        "raw-subnormal",
        "optics-lower-wavelength",
        "optics-upper-wavelength",
        "equalization-inert",
        "uniform-supplied",
        "positive-file-claim",
    ],
)
def test_permitted_positive_domains_are_not_blanket_rejected(variant: str) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    if variant == "zero-signed-map":
        kwargs["acquisition"]["flatfield_slope"] = np.array(
            [[0.0, -1.0, 2.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
        )
        kwargs["acquisition"]["background"] = -2.0
    elif variant == "numpy-scalars":
        kwargs["acquisition"].update(
            norders=np.int64(2), axial_zoom=np.int32(1), dxy_um=np.float32(1)
        )
        kwargs["optics"]["wavelength_nm"] = np.int16(500)
    elif variant == "raw-float32-max":
        maximum = float(np.finfo(np.float32).max)
        case.raw[0, 0] = np.array([maximum, maximum / 2, maximum / 2])[:, None, None, None]
    elif variant == "raw-subnormal":
        case.raw *= float(np.nextafter(np.float32(0), np.float32(1)))
    elif variant == "optics-lower-wavelength":
        kwargs["optics"].update(wavelength_nm=1, numerical_aperture=2.0, immersion_index=2.0)
        kwargs["transfer_identity"]["optics"] = kwargs["optics"].copy()
    elif variant == "optics-upper-wavelength":
        kwargs["optics"]["wavelength_nm"] = 32767
        kwargs["transfer_identity"]["optics"] = kwargs["optics"].copy()
        kwargs["carrier"]["linespacing_um"] = 1e6
    elif variant == "equalization-inert":
        kwargs["acquisition"].update(
            equalize=False, equalize_z=True, equalize_time=True, adjust_phases=True
        )
    elif variant == "uniform-supplied":
        kwargs["acquisition"].update(
            phase_policy="supplied", phases_rad=2 * np.pi * np.arange(3)[None] / 3
        )
    else:
        kwargs["specimen_identity"]["files"] = [
            dict(name="sample.mrc", bytes=0, sha256="0" * 64, role="raw")
        ]
    result = entry()(case.raw, **kwargs)
    assert np.isfinite(result.image).all()
    assert result.image.shape == (1, 2, 2, 4)
    if variant in ("raw-float32-max", "raw-subnormal"):
        factor = (
            float(np.finfo(np.float32).max) / 6
            if variant == "raw-float32-max"
            else float(np.nextafter(np.float32(0), np.float32(1)))
        )
        a0 = 1 + np.sqrt(2)
        expected_line = (
            factor * (12 + (3 / 8) * np.array([1.0, a0, a0, 1.0])) / (2 + (2 + np.sqrt(2)) / 64)
        )
        close(
            result.image,
            np.broadcast_to(expected_line, result.image.shape),
            gamma(65536) * 64 * factor,
            label="raw representation endpoint absolute scale",
        )
    if variant in ("equalization-inert", "uniform-supplied"):
        baseline = run(case)
        close(result.image, baseline.image, gamma(65536) * 64, label="permitted policy equivalence")
        assert dict(result.resolved_settings)["phase_policy"] == (
            "supplied" if variant == "uniform-supplied" else "uniform"
        )


def test_neutral_nominal_commands_unknown_sampling_and_opaque_metadata_are_not_guesses() -> None:
    entry()
    case = constant_case(mode="2d")
    raw = case.raw[0, :, :, 0]
    record = public().declare_acquisition(
        raw,
        config=dict(
            version=1,
            acquisition_kind="specimen_sim",
            axes=["orientation", "phase", "y", "x"],
            sampling_um=None,
            wavelengths_nm={"0": 999.0},
            nominal_phases_rad=[[0.0, 0.0, 0.0]],
            acquisition_id="unmeasured",
            calibration_id="does-not-select-beads",
        ),
        original_metadata=dict(
            clock_unit="seconds", timestamps=[0.0, 1.0, 2.0], phases="unknown", opaque=b"\x00\xff"
        ),
    )
    result = run(case, specimen=record)
    assert_scientific(case, result)
    assert dict(result.resolved_settings)["phase_policy"] == "uniform"
    assert dict(result.resolved_settings)["header_timestamp_unit"] is None
    assert result.bands.header_timestamps_after is None
    assert result.calibration is None
    source = dict(dict(result.source_declarations)["raw_acquisition_metadata"])
    assert source["nominal_phases_rad"] == ((0.0, 0.0, 0.0),)
    identity = next(i for i in result.input_identities if i.name == "specimen.nominal_phases_rad")
    assert (identity.shape, identity.dtype, identity.sha256) == array_digest(
        record.nominal_phases_rad
    )


def test_literal_direction_stream_is_distinct_from_nominal_z_major() -> None:
    direction = control_cases()["literal-direction-major"]
    nominal = control_cases()["literal-z-major"]
    expected_d, expected_z = observe(direction), observe(nominal)
    assert np.max(abs(expected_d["image"] - expected_z["image"])) > 100 * max(
        error_budget(direction, expected_d)["image"], error_budget(nominal, expected_z)["image"]
    )
    actual_d, actual_z = run(direction), run(nominal)
    for case, expected, actual in (
        (direction, expected_d, actual_d),
        (nominal, expected_z, actual_z),
    ):
        assert actual.layout is not None
        assert dict(actual.resolved_settings)["effective_shape"][:4] == (2, 2, 5, 1)
        assert_scientific(case, actual, expected)
        close(
            actual.bands.input_scale,
            1 / (10 * 10 * 2),
            gamma(8),
            label="literal alpha uses effective Z1",
        )


@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
def test_literal_physical_headers_and_new_direction_labels(storage: str) -> None:
    """WF066/W02: nonempty physical metadata, separate from active drift fits.

    The complete raw-to-image proof also runs these two additive examples.
    Here exact layout/header identities and new-label phase/carrier binding
    fill the original None-header gap without requiring a private observer.
    """
    case = literal_metadata_cases()[f"literal-metadata-{storage}"]
    expected = observe(case)
    budget = error_budget(case, expected)
    clocks = case.extras["header_timestamps"]
    header_phases = case.extras["header_phases_rad"]
    # Independent physical index s=q*D*P*E+(d_new*P+p)*E+e.
    q, direction, phase, exposure = np.indices((2, 2, 5, 2))
    section = q * 20 + (direction * 5 + phase) * 2 + exposure
    np.testing.assert_array_equal(section.ravel(), np.arange(40))
    np.testing.assert_array_equal(clocks, (101 + 3 * section + section**2).ravel())
    np.testing.assert_array_equal(header_phases, ((section + 1) / 64).ravel())
    # A canonical D,P,Z,E reshape followed by a nominal z-plane transpose
    # would alter each supplied vector. It is not the declared stream map.
    for vector in (clocks, header_phases):
        wrongly_reshuffled = vector.reshape(1, 2, 5, 2, 2).transpose(0, 3, 1, 2, 4).ravel()
        assert not np.array_equal(vector, wrongly_reshuffled)
    source = np.array(
        [[[0, 0], [0, 1]], [[1, 0], [1, 1]]]
        if storage == "direction-major"
        else [[[0, 0], [1, 0]], [[0, 1], [1, 1]]],
        dtype=np.int64,
    )
    result = run(case)
    assert result.layout is not None
    np.testing.assert_array_equal(result.layout.source_direction_z, source)
    for effective_time, new_direction in np.ndindex(2, 2):
        old_direction, old_z = source[effective_time, new_direction]
        np.testing.assert_array_equal(
            result.layout.images[effective_time, new_direction, :, 0],
            case.raw[0, old_direction, :, old_z],
        )
    np.testing.assert_array_equal(result.bands.header_timestamps_after, clocks)
    assert dict(result.resolved_settings)["header_timestamp_unit"] == " physical ticks "
    identities = {item.name: item for item in result.input_identities}
    for name, value in (("header_timestamps", clocks), ("header_phases_rad", header_phases)):
        item = identities[name]
        assert (item.shape, item.dtype, item.sha256) == array_digest(value)
    # No drift operation is selected: header phases remain metadata. The
    # supplied list indexes NEW d at both effective times, independently of
    # the original direction from which that image group happened to come.
    phases = case.acquisition["phases_rad"]
    np.testing.assert_array_equal(
        result.bands.phase_angles_rad, np.broadcast_to(phases[None, :, None], (2, 2, 1, 5))
    )
    designs = [event for event in result.bands.trace if event.kind == "phase-design"]
    assert len(designs) == 4
    assert {(event.time_index, event.direction_index) for event in designs} == set(np.ndindex(2, 2))
    for event in designs:
        assert event.z_index == 0
        assert event.direction_index in (0, 1)
        details = dict(event.details)
        assert details["policy"] == "supplied"
        np.testing.assert_array_equal(details["phases_rad"], phases[event.direction_index])
    angles = case.carrier["angles_rad"]
    initial = np.column_stack((np.cos(angles), np.sin(angles))) / case.carrier["linespacing_um"]
    radius = budget["parameter_bounds"]["carrier_radius"]
    close(result.initial_carriers_cyc_um, initial, radius[0, :, None], label="NEW direction angles")
    close(
        result.parameters.carriers_cyc_um,
        np.broadcast_to(initial, (2, 2, 2)),
        radius[..., None],
        label="known NEW direction carriers at both effective times",
    )
    assert result.parameters.branches == (("known", "known"), ("known", "known"))
    assert not any(event.kind == "cubic-fit" for event in result.bands.trace)


@pytest.mark.parametrize("selection", ["raw-beads", "prepared-otf", "accepted-transfer"])
def test_every_supplied_numerical_array_has_its_original_bit_identity(selection: str) -> None:
    function = entry()
    case = control_cases()[
        "empirical-exposure-priority"
        if selection != "accepted-transfer"
        else "ordinary-camera-phase"
    ]
    kwargs = keywords(case, selection=selection)
    expected_arrays: dict[str, np.ndarray] = {"specimen": case.raw, "selected_specimen": case.raw}

    def visit(path: str, value: Any) -> None:
        if isinstance(value, np.ndarray):
            expected_arrays[path] = value
        elif isinstance(value, dict):
            for key, item in value.items():
                visit(f"{path}.{key}" if path else key, item)

    for key, value in kwargs.items():
        visit(key, value)
    if selection == "prepared-otf":
        prepared = kwargs["transfer"]
        expected_arrays["transfer.transfer.samples"] = prepared.transfer.samples
        for key in (
            "center_pixels_xyz",
            "background_counts",
            "phase_angles_rad",
            "quadratures",
            "normalization_factors",
            "quadrature_angles_rad",
        ):
            expected_arrays[f"transfer.{key}"] = getattr(prepared, key)
    elif selection == "accepted-transfer":
        expected_arrays["transfer.samples"] = kwargs["transfer"].samples
    result = function(case.raw, **kwargs)
    identities = {identity.name: identity for identity in result.input_identities}
    for name, array in expected_arrays.items():
        identity = identities[name]
        assert (identity.shape, identity.dtype, identity.sha256) == array_digest(array), name


def test_complete_extra_orders_are_retained_but_unused() -> None:
    case = control_cases()["p7-o3-initialization"]
    baseline = run(case)
    case.table.samples[3] = -99 + 87j
    changed = run(case)
    assert changed.transfer.norders == 4
    np.testing.assert_array_equal(baseline.image, changed.image)
    np.testing.assert_array_equal(baseline.parameters.modulation, changed.parameters.modulation)
    assert next(
        i.sha256 for i in baseline.input_identities if i.name == "transfer.samples"
    ) != next(i.sha256 for i in changed.input_identities if i.name == "transfer.samples")


def test_readonly_mappings_and_nonempty_opaque_identity_labels_are_permitted() -> None:
    from types import MappingProxyType

    function = entry()
    case = constant_case()
    kwargs = keywords(case)
    kwargs["specimen_identity"].update(id=" ", intensity_unit=" ")
    kwargs["transfer_identity"]["optics"] = MappingProxyType(kwargs["transfer_identity"]["optics"])
    for key in (
        "acquisition",
        "optics",
        "carrier",
        "filtering",
        "specimen_identity",
        "transfer_identity",
    ):
        kwargs[key] = MappingProxyType(kwargs[key])
    result = function(case.raw, **kwargs)
    assert result.intensity_unit == " "
    expected = observe(case)
    close(
        result.image,
        expected["image"],
        error_budget(case, expected)["image"],
        label="readonly finite mappings",
    )


class StableIdentityArray(np.ndarray):
    """Owned ordinary ndarray storage; deliberately overrides no behavior."""


IDENTITY_PREPARED_FIELDS = (
    "center_pixels_xyz",
    "background_counts",
    "phase_angles_rad",
    "quadratures",
    "normalization_factors",
    "quadrature_angles_rad",
)


def identity_storage_copy(values: np.ndarray, storage: str, *, order: str = "C") -> np.ndarray:
    """Only the permitted backing class/layout changes, never numeric values."""
    array: np.ndarray
    assert order in ("C", "F")
    allocation_order = "F" if order == "F" else "C"
    if storage == "subclass":
        array = StableIdentityArray(values.shape, dtype=values.dtype, order=allocation_order)
    else:
        assert storage == "plain"
        array = np.empty(values.shape, dtype=values.dtype, order=allocation_order)
    np.copyto(array, values)
    array.flags.writeable = False
    assert array.flags.owndata and np.isfinite(array).all()
    return array


def frozen_original_array_identity(array: np.ndarray) -> tuple[tuple[int, ...], str, str]:
    """Independent exact byte oracle for these float64/complex128 inputs.

    Scalar struct packing follows logical C indices and explicit little endian.
    It preserves signed zero and both complex components without float32 casts,
    subclass methods, physical-buffer flattening or returned-stage identities.
    """
    import hashlib
    import struct

    assert array.dtype.kind in ("f", "c")
    assert array.dtype.itemsize == (8 if array.dtype.kind == "f" else 16)
    chunks = []
    for index in np.ndindex(array.shape):
        value: Any = array[index]
        chunks.append(
            struct.pack("<d", float(value))
            if array.dtype.kind == "f"
            else struct.pack("<dd", float(value.real), float(value.imag))
        )
    return (
        array.shape,
        array.dtype.newbyteorder("<").str,
        hashlib.sha256(b"".join(chunks)).hexdigest(),
    )


def original_identity_inputs(
    example: str, storage: str
) -> tuple[Case, Any, dict[str, Any], dict[str, np.ndarray]]:
    """Real public records and frozen caller leaves; no workflow call here."""
    from dataclasses import replace

    case = (
        control_cases()["empirical-z2"]
        if example == "prepared-all-fields"
        else constant_case(complex_table=example == "direct-complex-bits")
    )
    kwargs = keywords(
        case, selection="prepared-otf" if example == "prepared-all-fields" else "accepted-transfer"
    )
    specimen: Any = case.raw
    arrays: dict[str, np.ndarray] = {"specimen": case.raw}
    if example == "prepared-all-fields":
        prepared = kwargs["transfer"]
        transfer = replace(
            prepared.transfer,
            samples=identity_storage_copy(prepared.transfer.samples, storage),
        )
        diagnostics = {
            key: identity_storage_copy(getattr(prepared, key), "plain")
            for key in IDENTITY_PREPARED_FIELDS
        }
        kwargs["transfer"] = replace(prepared, transfer=transfer, **diagnostics)
        arrays["transfer.transfer.samples"] = transfer.samples
        arrays.update({f"transfer.{key}": value for key, value in diagnostics.items()})
    elif example in ("direct-unit", "direct-complex-bits"):
        transfer = kwargs["transfer"]
        samples = transfer.samples.copy()
        if example == "direct-complex-bits":
            samples.imag[samples.imag == 0] = -0.0
        samples = identity_storage_copy(
            samples, storage, order="F" if example == "direct-complex-bits" else "C"
        )
        kwargs["transfer"] = replace(transfer, samples=samples)
        arrays["transfer.samples"] = samples
    else:
        assert example == "raw-nominal-phases"
        # Neutral declaration/data arguments stay PLAIN arrays. Its canonical
        # data and nominal commands stay plain too. The storage variant applies
        # ONLY to direct transfer.samples; nominal commands remain provenance.
        source = np.array(np.stack((case.raw, case.raw + 16), axis=1), dtype=">f8", order="F")
        source[0, 1].flat[0] = -0.0
        source[0, 1].flat[1] = 2.0**-20
        nominal = [[[[-0.0, 0.125 + 2.0**-40, 1.5]], [[0.0, -0.25, 7.0]]]]
        config = dict(
            version=1,
            acquisition_kind="specimen_sim",
            axes=["time", "channel", "orientation", "phase", "z", "y", "x"],
            sampling_um=dict(x=1.0, y=1.0, z=1.0),
            intensity_unit="detector-counts",
            nominal_phases_rad=nominal,
        )
        assert type(source) is np.ndarray
        record = public().declare_acquisition(source, config=config)
        assert type(record.data) is np.ndarray and record.data.flags.c_contiguous
        assert frozen_original_array_identity(record.data) == frozen_original_array_identity(source)
        phase_truth = np.array(nominal, dtype=np.float64)
        assert frozen_original_array_identity(record.nominal_phases_rad) == (
            frozen_original_array_identity(phase_truth)
        )
        specimen = replace(
            record, nominal_phases_rad=identity_storage_copy(record.nominal_phases_rad, "plain")
        )
        transfer = kwargs["transfer"]
        kwargs["transfer"] = replace(
            transfer, samples=identity_storage_copy(transfer.samples, storage)
        )
        kwargs["channel_index"] = 0
        arrays = {
            "specimen.data": specimen.data,
            "specimen.nominal_phases_rad": specimen.nominal_phases_rad,
            "transfer.samples": kwargs["transfer"].samples,
        }
    return case, specimen, kwargs, arrays


@pytest.mark.parametrize(
    "example", ["direct-unit", "direct-complex-bits", "prepared-all-fields", "raw-nominal-phases"]
)
@pytest.mark.parametrize("storage", ["plain", "subclass"])
def test_original_record_array_identities_include_permitted_storage(
    example: str, storage: str
) -> None:
    """WF085: original supplied leaves survive independent of consumed data.

    These are identity/provenance regressions, not new scientific accuracy
    controls. The genuine prepared record defines input bytes before workflow.
    All previously accepted raw finite-sum calibration/image proofs remain.
    """
    case, specimen, kwargs, arrays = original_identity_inputs(example, storage)
    expected = {path: frozen_original_array_identity(value) for path, value in arrays.items()}
    selected = frozen_original_array_identity(case.raw)
    numpy_errors = np.geterr().copy()
    try:
        result = entry()(specimen, **kwargs)
    finally:
        assert np.geterr() == numpy_errors
        for path, value in arrays.items():
            assert frozen_original_array_identity(value) == expected[path], path
    assert result.image.shape == (case.raw.shape[0], *case.raw.shape[-3:])
    assert np.isfinite(result.image).all()
    assert result.intensity_unit == "detector-counts"
    assert kwargs["transfer_identity"]["intensity_unit"] == "dimensionless-transfer"
    names = [identity.name for identity in result.input_identities]
    assert names == sorted(set(names)), "identities must have unique lexicographically sorted names"
    identities = {identity.name: identity for identity in result.input_identities}
    missing = sorted(expected.keys() - identities.keys())
    assert not missing, f"missing original supplied array identities: {missing}"
    for path, value in expected.items():
        identity = identities[path]
        assert fields_of(identity) == ("name", "shape", "dtype", "sha256")
        assert (identity.shape, identity.dtype, identity.sha256) == value, path
    assert set(names) == expected.keys() | {
        "selected_specimen",
        "prepared_quadratures",
        "consumed_transfer",
    }
    identity = identities["selected_specimen"]
    assert (identity.shape, identity.dtype, identity.sha256) == selected


def identity_optics_scalar_values() -> dict[str, Any]:
    """Only finite supported float widths; dtype spelling grants no domain.

    A distinct longdouble scalar class can store ordinary binary64 on a given
    host. Include that lawful representation; never construct extended-width
    input when its actual format lies outside the inherited scalar domain.
    """
    values: dict[str, Any] = {
        "python-float": 1.0,
        "numpy-float16": np.float16(1.0),
        "numpy-float32": np.float32(1.0),
        "numpy-float64": np.float64(1.0),
    }
    formats = {2: (10, 16, -14), 4: (23, 128, -126), 8: (52, 1024, -1022)}
    dtype = np.dtype(np.longdouble)
    info = np.finfo(dtype)
    if (
        dtype.kind == "f"
        and dtype.itemsize in formats
        and (info.nmant, info.maxexp, info.minexp) == formats[dtype.itemsize]
    ):
        values[f"numpy-longdouble-{dtype.itemsize}-byte"] = np.longdouble(1.0)
    return values


@pytest.mark.parametrize("representation", tuple(identity_optics_scalar_values()))
def test_identity_optics_scalars_complete_an_independent_ordinary_snapshot(
    representation: str,
) -> None:
    """Existing finite scalar domain must complete immutable source snapshots."""
    case = constant_case()
    kwargs = keywords(case)
    supplied = identity_optics_scalar_values()[representation]
    assert float(supplied) == 1.0 and np.isfinite(supplied)
    if isinstance(supplied, np.generic):
        assert supplied.dtype.kind == "f" and supplied.dtype.itemsize in (2, 4, 8)
    optics_claim = kwargs["transfer_identity"]["optics"]
    optics_claim["immersion_index"] = supplied
    # Independent literals BEFORE the call: these real settings normalize to
    # ordinary Python binary64 values; wavelength retains its integral meaning.
    expected_optics = (
        ("immersion_index", 1.0),
        ("numerical_aperture", 1.0),
        ("wavelength_nm", 500),
    )
    raw_identity = frozen_original_array_identity(case.raw)
    transfer_identity = frozen_original_array_identity(kwargs["transfer"].samples)
    numpy_errors = np.geterr().copy()
    try:
        result = entry()(case.raw, **kwargs)
    finally:
        assert np.geterr() == numpy_errors
        assert frozen_original_array_identity(case.raw) == raw_identity
        assert frozen_original_array_identity(kwargs["transfer"].samples) == transfer_identity
        assert optics_claim["immersion_index"] is supplied
    assert result.image.shape == (1, 2, 2, 4) and np.isfinite(result.image).all()
    assert result.intensity_unit == "detector-counts"
    source_claim = dict(result.source_declarations)["transfer_identity"]
    assert type(source_claim) is tuple
    assert dict(source_claim)["id"] == "selected-transfer"
    assert dict(source_claim)["intensity_unit"] == "dimensionless-transfer"
    assert_recursive_snapshot(dict(source_claim)["optics"], expected_optics)
    # Mutate only the real caller's mapping AFTER return. The same independent
    # expected ordinary-number tree must remain unchanged and immutable.
    optics_claim.update(immersion_index=1.75, numerical_aperture=0.75, wavelength_nm=501)
    kwargs["transfer_identity"]["id"] = "caller-mutated"
    assert dict(source_claim)["id"] == "selected-transfer"
    assert_recursive_snapshot(dict(source_claim)["optics"], expected_optics)
