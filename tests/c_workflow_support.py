"""Real public-entry callers and assertions shared by the owned CE07 tests."""

from __future__ import annotations

import copy
import struct
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any

import numpy as np

from c_workflow_oracle import (
    ACQ_DEFAULTS,
    CARRIER_DEFAULTS,
    FILTER_DEFAULTS,
    LIMITS,
    OPTICS,
    Case,
    array_digest,
    error_budget,
    gamma,
    observe,
    reinterpret,
)

RESULT_FIELDS = (
    "image",
    "x_um",
    "y_um",
    "z_um",
    "intensity_unit",
    "intensity_semantics",
    "bands",
    "parameters",
    "transfer",
    "calibration",
    "layout",
    "reconstructions",
    "initial_carriers_cyc_um",
    "phase_linkage_carriers_cyc_um",
    "effective_wiener",
    "input_identities",
    "source_declarations",
    "resolved_settings",
    "trace",
    "limitations",
    "source_revision",
    "reference_sha256",
)
RESOLVED_KEYS = (
    "acquisition",
    "optics",
    "carrier",
    "filtering",
    "plane_policy",
    "original_shape",
    "effective_shape",
    "norders_in",
    "phase_policy",
    "calibration_selection",
    "header_timestamp_unit",
)
SOURCE_KEYS = (
    "specimen_identity",
    "transfer_identity",
    "calibration_identity",
    "selected_channel",
    "raw_acquisition_metadata",
    "decoded_transfer_binding",
)
ESTIMATOR_KEYS = (
    "wavelength_nm",
    "numerical_aperture",
    "immersion_index",
    "search_carriers",
    "use_time0_carriers",
    "amplitude_floors",
    "fit_all_phases",
    "omit_kz0",
    "dxy_um",
    "dz_um",
    "lateral_zoom",
    "axial_zoom",
    "input_scale",
    "acquisition_mode",
    "acquisition_reference_sha256",
)
ESTIMATOR_SOURCE = (
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)
ACQUISITION_SOURCE = (
    ("mainfile.c", "b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8"),
    ESTIMATOR_SOURCE[1],
    ESTIMATOR_SOURCE[2],
    ESTIMATOR_SOURCE[0],
    ESTIMATOR_SOURCE[3],
    ESTIMATOR_SOURCE[4],
    (
        "usr_local/include/sfftw.h",
        "72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138",
    ),
    (
        "usr_local/include/srfftw.h",
        "d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a",
    ),
    ESTIMATOR_SOURCE[5],
    ("drift_n_phasestep.c", "13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2"),
)


def public() -> Any:
    import simrecon

    return simrecon


def entry() -> Any:
    module = public()
    function = getattr(module, "reconstruct_workflow", None)
    assert callable(function), (
        "CE07 public reconstruct_workflow is absent; downstream proof cannot execute"
    )
    return function


def keywords(case: Case, *, selection: str = "accepted-transfer") -> dict[str, Any]:
    module = public()
    kwargs: dict[str, Any] = dict(
        acquisition=copy.deepcopy(case.acquisition),
        optics=OPTICS.copy(),
        carrier=copy.deepcopy(case.carrier),
        filtering=copy.deepcopy(case.filtering),
        specimen_identity={"id": "raw-observations", "intensity_unit": "detector-counts"},
        **copy.deepcopy(case.extras),
    )
    if selection == "raw-beads":
        assert case.bead is not None
        raw, settings = case.bead
        kwargs["calibration"] = dict(
            raw=raw.copy(),
            settings=copy.deepcopy(settings),
            identity={"id": "selected-asymmetric-beads", "intensity_unit": "detector-counts"},
        )
    else:
        if selection == "prepared-otf":
            assert case.bead is not None
            kwargs["transfer"] = module.prepare_bead_otf(case.bead[0], **case.bead[1])
        else:
            table = case.table
            kwargs["transfer"] = module.declare_otf(
                table.samples, layout=table.layout, dkr_cyc_um=table.dkr, dkz_cyc_um=table.dkz
            )
        kwargs["transfer_identity"] = dict(
            id="selected-transfer", intensity_unit="dimensionless-transfer", optics=OPTICS.copy()
        )
    return kwargs


def run(
    case: Case,
    *,
    selection: str | None = None,
    specimen: Any = None,
    overrides: dict[str, Any] | None = None,
) -> Any:
    function = entry()
    if selection is None:
        selection = "raw-beads" if case.bead is not None else "accepted-transfer"
    kwargs = keywords(case, selection=selection)
    if overrides:
        kwargs.update(overrides)
    actual_specimen = case.raw if specimen is None else specimen
    before = snapshot_input((actual_specimen, kwargs))
    numpy_errors = np.geterr().copy()
    try:
        return function(actual_specimen, **kwargs)
    finally:
        assert snapshot_input((actual_specimen, kwargs)) == before, "workflow mutated caller values"
        assert np.geterr() == numpy_errors, "workflow changed caller NumPy error settings"


def snapshot_input(value: Any) -> Any:
    """Observe only documented public input fields and exact caller array bits."""
    if isinstance(value, np.ndarray):
        return ("array", array_digest(value), value.strides, value.flags.writeable)
    if isinstance(value, Mapping):
        return ("mapping", tuple((key, snapshot_input(value[key])) for key in sorted(value)))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(snapshot_input(item) for item in value))
    module = public()
    records = (
        (
            module.RawAcquisition,
            (
                "data",
                "axes",
                "source_axes",
                "source_shape",
                "acquisition_kind",
                "sampling_um",
                "wavelengths_nm",
                "nominal_phases_rad",
                "nominal_phase_axes",
                "intensity_unit",
                "acquisition_id",
                "calibration_id",
                "original_config",
                "original_metadata",
                "provenance",
            ),
        ),
        (
            module.OpticalTransfer,
            (
                "samples",
                "layout",
                "dkr_cyc_um",
                "dkz_cyc_um",
                "norders",
                "source_revision",
                "reference_sha256",
            ),
        ),
        (
            module.PreparedOtf,
            (
                "transfer",
                "center_pixels_xyz",
                "background_counts",
                "phase_angles_rad",
                "quadratures",
                "normalization_factors",
                "quadrature_angles_rad",
                "resolved_settings",
            ),
        ),
    )
    for record_type, names in records:
        if isinstance(value, record_type):
            return (
                record_type.__name__,
                tuple((name, snapshot_input(getattr(value, name))) for name in names),
            )
    if isinstance(value, np.generic):
        return (value.dtype.str, value.tobytes())
    if type(value) is float:
        return ("float", struct.pack("<d", value))
    if type(value) is complex:
        return ("complex", struct.pack("<dd", value.real, value.imag))
    assert value is None or type(value) in (str, bytes, int, bool)
    return (type(value).__name__, value)


def close(actual: Any, expected: Any, absolute: Any, *, label: str) -> None:
    error = abs(np.asarray(actual) - np.asarray(expected))
    limit = np.broadcast_to(absolute, error.shape)
    assert np.isfinite(error).all() and np.isfinite(limit).all(), label
    assert np.all(limit >= 0), label
    assert np.all(error <= limit), f"{label}: absolute error exceeds independently frozen bound"


def immutable_array(value: Any, dtype: str, shape: tuple[int, ...]) -> None:
    assert type(value) is np.ndarray
    assert value.dtype == np.dtype(dtype)
    assert value.shape == shape
    assert value.flags.owndata
    assert not value.flags.writeable
    assert np.isfinite(value).all()


def named(value: Any, keys: tuple[str, ...]) -> dict[str, Any]:
    assert type(value) is tuple
    assert tuple(pair[0] for pair in value) == keys
    assert all(type(pair) is tuple and len(pair) == 2 for pair in value)
    return dict(value)


def fields_of(value: Any) -> tuple[str, ...]:
    if is_dataclass(value):
        return tuple(field.name for field in fields(value))
    return tuple(value._fields)


def frozen(value: Any) -> Any:
    """Independently snapshot documented built-in/array declaration values."""
    if isinstance(value, np.ndarray):
        return frozen(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return tuple((key, frozen(value[key])) for key in sorted(value))
    if isinstance(value, (list, tuple)):
        return tuple(frozen(item) for item in value)
    return value


def finite_details(value: Any) -> None:
    """Check the documented finite, immutable diagnostic value domain."""
    if isinstance(value, np.ndarray):
        assert type(value) is np.ndarray
        assert np.isfinite(value).all()
        assert not value.flags.writeable
        return
    if type(value) is tuple:
        for item in value:
            finite_details(item)
        return
    assert value is None or type(value) in (str, bool, int, float, complex)
    if isinstance(value, (float, complex)):
        assert np.isfinite(value)


def assert_scientific(
    case: Case,
    result: Any,
    expected: dict[str, Any] | None = None,
    *,
    budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Absolute raw-observation proof, conditional on the declared arithmetic model.

    Returned-stage consumption checks live in separately named supplemental
    tests. No actual transfer, carrier, fit, gain or image defines truth here.
    """
    if expected is None:
        expected = observe(case)
    if budget is None:
        budget = error_budget(case, expected)
    prep, est = expected["preparation"], expected["parameters"]
    pe, ke, ne = (
        budget[key] for key in ("preparation_bounds", "parameter_bounds", "native_bounds")
    )
    for key in (
        "quadratures",
        "noise_variance_factors",
        "frame_sums",
        "equalization_gains",
        "off_frame_sums",
        "off_equalization_gains",
        "off_quadratures",
        "separation_matrices",
        "phase_angles_rad",
        "background_after",
        "slope_after",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
        "header_timestamps_after",
    ):
        actual, truth = getattr(result.bands, key), prep[key]
        if truth is None:
            assert actual is None, key
        elif key in ("background_after", "slope_after", "header_timestamps_after"):
            np.testing.assert_array_equal(actual, truth)
        else:
            close(actual, truth, pe[key], label=f"{case.name}: {key}")
    assert result.bands.sentinel_frames == prep["sentinel_frames"]
    close(
        result.bands.input_scale, prep["input_scale"], gamma(8) * prep["input_scale"], label="alpha"
    )
    if case.bead is not None:
        cal = expected["calibration"]
        ce = budget["calibration_bounds"]
        close(
            result.transfer.samples,
            cal["table"].samples,
            ce["samples"],
            label="raw empirical transfer",
        )
        assert result.transfer.dkr_cyc_um == cal["table"].dkr
        assert result.transfer.dkz_cyc_um == cal["table"].dkz
    assert result.parameters.branches == est["branches"]
    close(
        result.parameters.carriers_cyc_um,
        est["carriers_cyc_um"],
        ke["carrier_radius"][..., None],
        label="carrier cycles/um from raw observations",
    )
    for key in ("raw_modulation", "modulation"):
        close(getattr(result.parameters, key), est[key], ke[key], label=f"absolute {key}")
    actual_coarse = [ev for ev in result.parameters.trace if ev.kind == "coarse"]
    expected_coarse = [ev for ev in est["decisions"] if ev["kind"] == "coarse"]
    assert len(actual_coarse) == len(expected_coarse) == len(ke["coarse"])
    for actual, truth, eb in zip(actual_coarse, expected_coarse, ke["coarse"], strict=True):
        details = dict(actual.details)
        assert details["integer_peak_xy"] == truth["integer_peak_xy"]
        assert details["alias_decisions"] == truth["alias_decisions"]
        close(
            details["carrier_cyc_um"],
            truth["carrier_cyc_um"],
            eb["carrier_radius"],
            label="coarse carrier cycles/um",
        )
    actual_brackets = [
        dict(ev.details)
        for ev in result.parameters.trace
        if ev.kind == "bracket" and dict(ev.details)["branch"] in ("initial", "shift")
    ]
    expected_brackets = [ev for ev in est["decisions"] if ev["kind"] in ("initial", "shift")]
    bounds_brackets = [ev for ev in ke["decision_bounds"] if ev["kind"] in ("initial", "shift")]
    assert len(actual_brackets) == len(expected_brackets) == len(bounds_brackets)
    for actual, truth, eb in zip(actual_brackets, expected_brackets, bounds_brackets, strict=True):
        assert actual["stage"] == truth["stage"]
        assert actual["strict_improvement"] == truth["strict_improvement"]
        for key, value, error in zip(
            ("x1", "amp1", "x2", "amp2", "x3", "amp3"), truth["points"], eb["points"], strict=True
        ):
            close(
                actual[key],
                value,
                error,
                label=f"literal {truth['stage']} bracket {key}; original units",
            )
    actual_parabolas = [dict(ev.details) for ev in result.parameters.trace if ev.kind == "parabola"]
    expected_parabolas = [ev for ev in est["decisions"] if ev["kind"] == "parabola"]
    assert len(actual_parabolas) == len(expected_parabolas) == len(ke["parabolas"])
    for actual, truth, eb in zip(
        actual_parabolas, expected_parabolas, ke["parabolas"], strict=True
    ):
        assert actual["stage"] == truth["stage"]
        close(
            actual["result"],
            truth["result"],
            eb["error"],
            label=f"{truth['stage']} source parabola",
        )
    assert len(result.parameters.overlaps) == len(est["overlaps"])
    for actual, truth, eb in zip(
        result.parameters.overlaps, est["overlaps"], ke["overlaps"], strict=True
    ):
        for key in ("orders", "purpose", "time_index", "direction_index"):
            assert getattr(actual, key) == truth[key]
        np.testing.assert_array_equal(actual.written, truth["written"])
        close(
            actual.fourier, truth["fourier"], eb["fourier"], label="absolute overlap coefficients"
        )
        close(
            actual.spatial,
            truth["spatial"],
            eb["spatial_point"][:, None, None, None],
            label="absolute overlap spatial values",
        )
    evaluations = [ev for ev in result.parameters.trace if ev.kind == "evaluation"]
    for event in (*result.bands.trace, *result.parameters.trace):
        finite_details(event.details)
    assert len(evaluations) == len(est["evaluations"])
    for actual, truth, eb in zip(evaluations, est["evaluations"], ke["evaluations"], strict=True):
        details = dict(actual.details)
        assert details["stage"] == truth["stage"]
        assert details["orders"] == truth["orders"]
        assert (details["objective"] is None) == (truth["objective"] is None)
        for key in ("SX", "SY", "cross", "forward", "reverse", "combined", "correlation"):
            close(details[key], truth[key], eb[key], label=f"independent regression {key}")
        if truth["objective"] is not None:
            close(
                details["objective"], truth["objective"], eb["objective"], label="forward objective"
            )
        # Supplemental returned-field algebra; these relations prove no raw accuracy.
        close(
            details["forward"] * details["SX"],
            details["cross"],
            gamma(16) * max(1, abs(details["cross"])),
            label="supplemental forward relation",
        )
        close(
            details["reverse"] * details["SY"],
            details["cross"].conjugate(),
            gamma(16) * max(1, abs(details["cross"])),
            label="supplemental reverse relation",
        )
    close(result.image, expected["image"], ne["image"], label=f"{case.name}: absolute signed image")
    for key in ("x_um", "y_um", "z_um"):
        close(getattr(result, key), expected[key], budget["coordinates"], label=key)
    close(
        result.effective_wiener,
        expected["effective_wiener"],
        gamma(8) * max(abs(expected["effective_wiener"])),
        label="preincrement schedule",
    )
    for it, reconstruction in enumerate(result.reconstructions):
        np.testing.assert_array_equal(result.image[it : it + 1], reconstruction.image)
        close(
            reconstruction.filtered_quadratures,
            expected["filtered_quadratures"][it : it + 1],
            ne["filtered"][it : it + 1],
            label="absolute native filtering",
        )
        np.testing.assert_array_equal(
            reconstruction.carriers_cyc_um, result.parameters.carriers_cyc_um[it]
        )
        np.testing.assert_array_equal(reconstruction.modulation, result.parameters.modulation[it])
        settings = dict(reconstruction.resolved_settings)
        assert settings["wiener_increment"] == 0
        assert settings["effective_wiener"] == (result.effective_wiener[it],)
    return budget


def search_bound(case: Case, expected: dict[str, Any]) -> float:
    """Carrier radius only, in cycles/um; never an angle or fit tolerance."""
    return float(np.max(error_budget(case, expected)["parameter_bounds"]["carrier_radius"]))


def search_stability(case: Case, expected: dict[str, Any]) -> tuple[bool, str]:
    """All finite comparisons must resolve; no conditional bypass is available."""
    error_budget(case, expected)
    return True, "resolved under the preregistered arithmetic and equality premises"


def assert_records(case: Case, result: Any) -> None:
    assert isinstance(result, public().WorkflowReconstruction)
    assert set(fields_of(result)) == set(RESULT_FIELDS)
    effective = reinterpret(case)
    a, c, f = effective.resolved()
    t, d, p, z, y, x = effective.raw.shape
    assert result.intensity_unit == "detector-counts"
    assert result.intensity_semantics == "C-scaled-camera-corrected-equalized-phase-reconstruction"
    immutable_array(
        result.image,
        "float64",
        (t, a["axial_zoom"] * z, int(a["lateral_zoom"] * y), int(a["lateral_zoom"] * x)),
    )
    for key in (
        "x_um",
        "y_um",
        "z_um",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
        "effective_wiener",
    ):
        value = getattr(result, key)
        immutable_array(value, "float64", value.shape)
        assert not np.shares_memory(value, case.raw)
        assert not np.shares_memory(value, result.bands.quadratures)
        if key != "image":
            assert not np.shares_memory(value, result.image)
    arrays = [
        getattr(result, key)
        for key in (
            "image",
            "x_um",
            "y_um",
            "z_um",
            "initial_carriers_cyc_um",
            "phase_linkage_carriers_cyc_um",
            "effective_wiener",
        )
    ]
    for i, first in enumerate(arrays):
        for second in arrays[i + 1 :]:
            assert not np.shares_memory(first, second)
    assert result.bands.quadratures.flags.writeable
    assert result.bands.noise_variance_factors.flags.writeable
    assert not result.bands.frame_sums.flags.writeable
    assert type(result.reconstructions) is tuple and len(result.reconstructions) == t
    settings = named(result.resolved_settings, RESOLVED_KEYS)
    # Required order is contractual, independent of caller dict insertion order.
    required_a = (
        "acquisition_mode",
        "dxy_um",
        "dz_um",
        "norders",
        "background",
        "lateral_zoom",
        "axial_zoom",
        "phase_policy",
    )
    named(settings["acquisition"], required_a + tuple(ACQ_DEFAULTS))
    named(settings["optics"], tuple(OPTICS))
    named(settings["carrier"], ("linespacing_um",) + tuple(CARRIER_DEFAULTS))
    named(settings["filtering"], ("wiener",) + tuple(FILTER_DEFAULTS))
    for config_key, config in (
        ("acquisition", a),
        ("optics", OPTICS),
        ("carrier", c),
        ("filtering", f),
    ):
        for key, value in settings[config_key]:
            assert value == frozen(config[key]), (config_key, key)
    assert settings["original_shape"] == case.raw.shape
    assert settings["effective_shape"] == effective.raw.shape
    assert settings["norders_in"] == p // 2 + 1
    assert settings["phase_policy"] == a["phase_policy"]
    assert settings["header_timestamp_unit"] == case.extras.get("header_timestamp_unit")
    sources = named(result.source_declarations, SOURCE_KEYS)
    assert sources["selected_channel"] is None
    assert result.source_revision == result.parameters.source_revision == "SVN307"
    assert result.reference_sha256 == result.bands.reference_sha256
    assert result.reference_sha256 == ACQUISITION_SOURCE
    assert result.transfer.reference_sha256 == ACQUISITION_SOURCE[:-1]
    assert result.parameters.reference_sha256 == ESTIMATOR_SOURCE
    estimator_settings = named(result.parameters.resolved_settings, ESTIMATOR_KEYS)
    assert estimator_settings["acquisition_reference_sha256"] == result.bands.reference_sha256
    assert estimator_settings["acquisition_mode"] == a["acquisition_mode"]
    limitations: list[str] = list(LIMITS)
    if case.extras.get("plane_policy") == "literal-2d-stack":
        limitations.append("literal-2d-stream-regrouping")
    if a["acquisition_mode"] == "2d" and a["axial_zoom"] > 1:
        limitations.append("true2d-extra-axial-planes-zero")
    if a["acquisition_mode"] == "2d" and a["dz_um"] == 0:
        limitations.append("true2d-axial-pitch-undeclared")
    assert result.limitations == tuple(limitations)
    kinds = (
        ["declaration", "layout", "transfer", "preparation", "estimation"]
        + ["reconstruction"] * t
        + ["result"]
    )
    assert tuple(event.kind for event in result.trace) == tuple(kinds)
    detail_keys = dict(
        declaration=("selected_channel", "original_shape"),
        layout=("plane_policy", "effective_shape"),
        transfer=("selection", "consumed_transfer_sha256"),
        preparation=("input_scale", "phase_policy"),
        estimation=("branches",),
        reconstruction=("effective_wiener", "parameter_time_index"),
        result=("output_shape",),
    )
    for event in result.trace:
        assert fields_of(event) == ("kind", "stage", "time_index", "details")
        assert event.stage == event.kind
        named(event.details, detail_keys[event.kind])
        assert (
            event.time_index is None
            if event.kind != "reconstruction"
            else type(event.time_index) is int
        )
        finite_details(event.details)
    assert dict(result.trace[0].details) == dict(
        selected_channel=None, original_shape=case.raw.shape
    )
    assert dict(result.trace[1].details) == dict(
        plane_policy=case.extras.get("plane_policy", "native"), effective_shape=effective.raw.shape
    )
    assert dict(result.trace[-1].details)["output_shape"] == result.image.shape
    assert dict(result.trace[3].details)["phase_policy"] == a["phase_policy"]
    assert dict(result.trace[4].details)["branches"] == result.parameters.branches
    for it, event in enumerate(result.trace[5:-1]):
        assert event.time_index == it
        assert dict(event.details) == dict(
            effective_wiener=result.effective_wiener[it], parameter_time_index=it
        )
    for known in result.reconstructions:
        for event in known.mode_trace:
            finite_details(event.details)
    identities = result.input_identities
    assert type(identities) is tuple
    assert tuple(i.name for i in identities) == tuple(sorted(i.name for i in identities))
    by_name = {i.name: i for i in identities}
    for name, array in (
        ("specimen", case.raw),
        ("selected_specimen", case.raw),
        ("prepared_quadratures", result.bands.quadratures),
        ("consumed_transfer", result.transfer.samples),
    ):
        record = by_name[name]
        assert fields_of(record) == ("name", "shape", "dtype", "sha256")
        assert (record.shape, record.dtype, record.sha256) == array_digest(array)
    for mapping_name, mapping in (("acquisition", case.acquisition), ("carrier", case.carrier)):
        for key, value in mapping.items():
            if isinstance(value, np.ndarray):
                record = by_name[f"{mapping_name}.{key}"]
                assert (record.shape, record.dtype, record.sha256) == array_digest(value)
