"""Single-invalid categories with complete permitted-positive counterparts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from c_workflow_oracle import OPTICS, bead_fixture, constant_case, control_cases, patterned_case
from c_workflow_support import entry, keywords, public

STAGES = {
    "declaration",
    "layout",
    "transfer",
    "calibration",
    "preparation",
    "estimation",
    "reconstruction",
    "result",
}


def assert_error(
    code: str,
    raw: Any,
    kwargs: dict[str, Any],
    *,
    cause: bool = False,
    reason_words: tuple[str, ...] = (),
) -> Any:
    function = entry()
    error_type = getattr(public(), "WorkflowError", None)
    assert isinstance(error_type, type) and issubclass(error_type, public().SimreconError)
    with pytest.raises(error_type) as caught:
        function(raw, **kwargs)
    error = caught.value
    assert error.code == code
    assert isinstance(error.message, str) and error.message.strip()
    assert error.stage in STAGES
    for field in ("time_index", "direction_index"):
        value = getattr(error, field)
        assert value is None or (type(value) is int and value >= 0)
    if cause:
        assert error.__cause__ is not None
    for word in reason_words:
        assert word.lower() in str(error).lower()
    return error


def mappings() -> tuple[str, ...]:
    return (
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
    )


def schema_input(path: str) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    case = constant_case()
    if path.startswith("calibration"):
        case.bead = bead_fixture(z=2, phases=3)
        kwargs = keywords(case, selection="raw-beads")
    else:
        kwargs = keywords(case)
    if path == "transfer":
        kwargs["transfer"] = dict(
            kind="decoded-sections",
            layout="radial",
            samples=case.table.samples.copy(),
            dkr_cyc_um=case.table.dkr,
            dkz_cyc_um=case.table.dkz,
            order_encoding="combined-orders",
        )
    mapping: dict[str, Any] = kwargs
    for part in path.split("."):
        mapping = mapping[part]
    return case.raw, kwargs, mapping


@pytest.mark.parametrize("mapping_path", mappings())
@pytest.mark.parametrize(
    "unknown",
    [
        "unexpected",
        "filename",
        "save_separated",
        "shared_wave",
        "padding",
        "model",
        "bessel",
        "two_objective",
        "automatic_wiener",
    ],
)
def test_every_unlisted_key_is_config_not_reserved_unsupported(
    mapping_path: str, unknown: str
) -> None:
    entry()
    raw, kwargs, mapping = schema_input(mapping_path)
    mapping[unknown] = True
    assert_error("workflow_config", raw, kwargs)


REQUIRED = {
    "acquisition": (
        "acquisition_mode",
        "dxy_um",
        "dz_um",
        "norders",
        "background",
        "lateral_zoom",
        "axial_zoom",
        "phase_policy",
    ),
    "optics": tuple(OPTICS),
    "carrier": ("linespacing_um",),
    "filtering": ("wiener",),
    "specimen_identity": ("id", "intensity_unit"),
    "transfer_identity": ("id", "intensity_unit", "optics"),
    "transfer_identity.optics": tuple(OPTICS),
    "calibration": ("raw", "settings", "identity"),
    "calibration.settings": ("dxy_um", "dz_um", "linespacing_um", *OPTICS),
    "calibration.identity": ("id", "intensity_unit"),
    "transfer": ("kind", "layout", "samples", "dkr_cyc_um", "dkz_cyc_um", "order_encoding"),
}


@pytest.mark.parametrize(
    ("mapping_path", "key"), [(path, key) for path, keys in REQUIRED.items() for key in keys]
)
def test_each_missing_required_mapping_key_is_config(mapping_path: str, key: str) -> None:
    entry()
    raw, kwargs, mapping = schema_input(mapping_path)
    del mapping[key]
    assert_error("workflow_config", raw, kwargs)


@pytest.mark.parametrize(
    "top", ["acquisition", "optics", "carrier", "filtering", "specimen_identity"]
)
def test_required_top_level_binding_is_plain_typeerror(top: str) -> None:
    function = entry()
    case = constant_case()
    kwargs = keywords(case)
    del kwargs[top]
    with pytest.raises(TypeError) as caught:
        function(case.raw, **kwargs)
    assert not isinstance(caught.value, public().WorkflowError)


def test_unknown_top_keyword_is_plain_typeerror() -> None:
    function = entry()
    case = constant_case()
    with pytest.raises(TypeError) as caught:
        function(case.raw, filename="not-decoded.mrc", **keywords(case))
    assert not isinstance(caught.value, public().WorkflowError)


BAD_MAPPED: tuple[tuple[str, str, Any], ...] = (
    ("acquisition", "acquisition_mode", "1d"),
    ("acquisition", "dxy_um", 0),
    ("acquisition", "dz_um", -1),
    ("acquisition", "norders", True),
    ("acquisition", "norders", 1),
    ("acquisition", "norders", 1.5),
    ("acquisition", "norders", 3),
    ("acquisition", "background", np.nan),
    ("acquisition", "background", np.zeros((1, 4))),
    ("acquisition", "flatfield_slope", np.zeros((2, 3))),
    ("acquisition", "flatfield_slope", np.full((2, 4), np.inf)),
    ("acquisition", "phase_policy", "guess"),
    ("acquisition", "phase_policy", "supplied"),
    ("acquisition", "phases_rad", np.zeros((1, 2))),
    ("acquisition", "phase_steps_rad", np.array([np.nan])),
    ("acquisition", "edge_pixels", 5),
    ("acquisition", "edge_pixels", True),
    ("acquisition", "equalize", 1),
    ("acquisition", "equalize_z", 0),
    ("acquisition", "equalize_time", np.bool_(False)),
    ("acquisition", "drift_between", 1),
    ("acquisition", "drift_within", None),
    ("acquisition", "fit_drift", "yes"),
    ("acquisition", "adjust_phases", 0),
    ("acquisition", "drift_filter_fraction", np.inf),
    ("acquisition", "storage_order", "auto"),
    ("acquisition", "combine_off_orders", [0, 0]),
    ("optics", "wavelength_nm", True),
    ("optics", "wavelength_nm", 500.0),
    ("optics", "wavelength_nm", 32768),
    ("optics", "wavelength_nm", 0),
    ("optics", "numerical_aperture", 0),
    ("optics", "numerical_aperture", 1.5),
    ("optics", "immersion_index", 0.99),
    ("optics", "immersion_index", 2.01),
    ("carrier", "linespacing_um", 0),
    ("carrier", "phase_start_angle_rad", np.inf),
    ("carrier", "negative_angle_step", 1),
    ("carrier", "angles_rad", np.zeros(2)),
    ("carrier", "angles_rad", np.array([np.nan])),
    ("carrier", "search_carriers", 0),
    ("carrier", "use_time0_carriers", 1),
    ("carrier", "fit_all_phases", None),
    ("carrier", "amplitude_floors", np.array([0.0])),
    ("carrier", "amplitude_floors", np.array([-1.0])),
    ("carrier", "amplitude_floors", np.array([1.0, 1.0])),
    ("filtering", "wiener", 0),
    ("filtering", "wiener", True),
    ("filtering", "wiener", np.inf),
    ("filtering", "wiener_increment", -2.0),
    ("filtering", "wiener_increment", np.nan),
    ("filtering", "suppression_radius_bins", np.inf),
    ("filtering", "suppress_singularities", 1),
    ("filtering", "dampen_order0", 0),
    ("filtering", "omit_order0", 0),
    ("filtering", "omit_kz0", 0),
    ("filtering", "precise_taper", 1),
    ("filtering", "filter_overlaps", None),
    ("filtering", "output_taper", "gaussian"),
    ("filtering", "output_taper", "power"),
    ("filtering", "power_taper_exponent", np.inf),
    ("filtering", "explode_factor", np.nan),
    ("specimen_identity", "id", ""),
    ("specimen_identity", "intensity_unit", 1),
    (
        "specimen_identity",
        "files",
        [dict(name="/private/raw.mrc", bytes=0, sha256="a" * 64, role="raw")],
    ),
    ("specimen_identity", "files", [dict(name="raw.mrc", bytes=True, sha256="a" * 64, role="raw")]),
    ("specimen_identity", "files", [dict(name="raw.mrc", bytes=-1, sha256="a" * 64, role="raw")]),
    ("specimen_identity", "files", [dict(name="raw.mrc", bytes=0, sha256="A" * 64, role="raw")]),
    ("specimen_identity", "files", [dict(name="raw.mrc", bytes=0, sha256="a" * 64, role="")]),
    (
        "specimen_identity",
        "files",
        [dict(name="raw.mrc", bytes=0, sha256="a" * 64, role="raw", filename="x")],
    ),
    ("transfer_identity", "intensity_unit", "counts"),
)


@pytest.mark.parametrize(
    ("path", "key", "value"),
    BAD_MAPPED,
    ids=[f"{p}.{k}-{i}" for i, (p, k, _) in enumerate(BAD_MAPPED)],
)
def test_single_invalid_mapped_value(path: str, key: str, value: Any) -> None:
    entry()
    raw, kwargs, mapping = schema_input(path)
    mapping[key] = value
    assert_error("workflow_config", raw, kwargs)


@pytest.mark.parametrize(
    "which",
    [
        "neither",
        "both",
        "missing-identity",
        "identity-on-raw",
        "insufficient-orders",
        "true2d-positive-k2",
    ],
)
def test_selection_errors_are_distinct_from_schema_and_representation(which: str) -> None:
    entry()
    case = constant_case(mode="2d" if which == "true2d-positive-k2" else "3d")
    kwargs = keywords(case)
    if which == "neither":
        del kwargs["transfer"]
        del kwargs["transfer_identity"]
    elif which == "both":
        raw, settings = bead_fixture(z=2)
        kwargs["calibration"] = dict(
            raw=raw, settings=settings, identity=dict(id="b", intensity_unit="counts")
        )
    elif which == "missing-identity":
        del kwargs["transfer_identity"]
    elif which == "identity-on-raw":
        case.bead = bead_fixture(z=2)
        kwargs = keywords(case, selection="raw-beads")
        kwargs["transfer_identity"] = dict(id="t", intensity_unit="dimensionless-transfer")
    elif which == "insufficient-orders":
        kwargs["transfer"] = public().declare_otf(
            case.table.samples[:1], layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.5
        )
    else:
        kwargs["transfer"] = public().declare_otf(
            np.ones((2, 8, 2)), layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.5
        )
    assert_error("workflow_selection", case.raw, kwargs)


@pytest.mark.parametrize(
    "sample",
    [
        np.zeros((1, 1, 3, 2, 2, 3)),
        np.zeros((1, 1, 3, 1, 2, 4)),
        np.zeros((1, 1, 3, 2, 2, 4), dtype=bool),
        np.zeros((1, 1, 3, 2, 2, 4), dtype=np.complex128),
        np.full((1, 1, 3, 2, 2, 4), np.nan),
        np.full((1, 1, 3, 2, 2, 4), 0.1),
        np.zeros((1, 1, 3, 2, 2, 4), dtype=object),
        np.ma.array(np.ones((1, 1, 3, 2, 2, 4))),
        [[1, 2]],
        1,
        object(),
    ],
    ids=[f"raw-domain-{i}" for i in range(11)],
)
def test_raw_input_domain(sample: Any) -> None:
    entry()
    assert_error("workflow_input", sample, keywords(constant_case()))


@pytest.mark.parametrize(
    "field", ["specimen", "off_exposures", "exposure_background", "calibration.raw"]
)
def test_top_pixel_arrays_have_input_category(field: str) -> None:
    entry()
    case = constant_case()
    raw, kwargs = case.raw, keywords(case)
    if field == "specimen":
        raw = case.raw.astype(bool)
    elif field == "off_exposures":
        kwargs[field] = np.ones((1, 1, 3, 2, 1, 2, 3))
    elif field == "exposure_background":
        kwargs[field] = np.ones((1, 1, 3, 1))
    else:
        case.bead = bead_fixture(z=2)
        kwargs = keywords(case, selection="raw-beads")
        kwargs["calibration"]["raw"] = np.ones((3, 2, 8, 8))
    assert_error("workflow_input", raw, kwargs)


@pytest.mark.parametrize("value", [None, 1, "", " ", "\t\n"])
def test_unused_clock_requires_valid_nonblank_unit(value: Any) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    kwargs.update(header_timestamps=np.arange(6, dtype=float), header_timestamp_unit=value)
    assert_error("workflow_metadata", case.raw, kwargs)


@pytest.mark.parametrize(
    "key,value",
    [
        ("header_timestamp_unit", "seconds"),
        ("header_timestamps", np.zeros(5)),
        ("header_timestamps", np.full(6, np.inf)),
        ("header_timestamps", np.zeros(6, dtype=bool)),
        ("header_phases_rad", np.zeros(5)),
        ("header_phases_rad", np.full(6, np.nan)),
        ("header_phases_rad", np.zeros(6, dtype=complex)),
    ],
)
def test_metadata_single_invalid_even_when_unused(key: str, value: Any) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    kwargs[key] = value
    if key == "header_timestamps":
        kwargs["header_timestamp_unit"] = "seconds"
    assert_error("workflow_metadata", case.raw, kwargs)


@pytest.mark.parametrize("path", ["specimen", "transfer", "calibration.raw"])
@pytest.mark.parametrize("value", ["not-opened.mrc", Path("not-opened.mrc")])
def test_recognized_path_inputs_are_unsupported_without_io(path: str, value: Any) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    raw: Any = case.raw
    if path == "specimen":
        raw = value
    elif path == "transfer":
        kwargs["transfer"] = value
    else:
        case.bead = bead_fixture(z=2)
        kwargs = keywords(case, selection="raw-beads")
        kwargs["calibration"]["raw"] = value
    assert_error("workflow_unsupported", raw, kwargs)


@pytest.mark.parametrize(
    "which",
    [
        "zero-frame-equalization",
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
def test_real_operation_failures_preserve_cause_and_no_partial_result(which: str) -> None:
    entry()
    case = constant_case(
        times=2 if which == "later-time-zero" else 1,
        mode="2d" if which in ("precise-dc", "true2d-omit-kz0") else "3d",
    )
    if which == "zero-frame-equalization":
        case.raw[:] = 0
        case.acquisition["equalize"] = True
    elif which == "singular-phase":
        case.acquisition.update(phases_rad=np.zeros((1, 3)), phase_policy="supplied")
    elif which == "zero-regression":
        case.raw[:] = 0
    elif which == "later-time-zero":
        case.raw[1] = 0
    elif which == "precise-dc":
        case.filtering.update(precise_taper=True, output_taper="cosine")
    elif which == "negative-power-zero":
        case.filtering.update(output_taper="power", power_taper_exponent=-1.0)
    elif which == "dampen-c0":
        case.filtering["dampen_order0"] = True
    elif which == "true2d-omit-kz0":
        case.filtering["omit_kz0"] = True
    else:
        # Zero slopes are valid; the selected zero-sum equalization fails
        # at its operation, not at camera schema validation.
        case.acquisition.update(flatfield_slope=np.zeros((2, 4)), equalize=True)
    before = np.geterr().copy()
    error = assert_error("workflow_operation", case.raw, keywords(case), cause=True)
    assert np.geterr() == before
    if which == "later-time-zero":
        assert error.time_index == 1


@pytest.mark.parametrize(
    "which",
    [
        "fast-d2",
        "within3d-d3",
        "within3d-fast-d1",
        "within2d-n0",
        "within2d-fit-no-adjust",
        "prepass-off-nontermination",
    ],
)
def test_recognized_unsafe_branches_are_unsupported(which: str) -> None:
    entry()
    case = patterned_case(directions=2, times=1)
    reason: tuple[str, ...]
    if which == "fast-d2":
        case.acquisition.update(storage_order="z-major", drift_between=True)
        reason = ("uninitialized",)
    elif which == "within3d-d3":
        case = patterned_case(directions=3, times=1)
        case.acquisition.update(drift_within=True, adjust_phases=True, phase_policy="drift")
        case.extras.update(
            header_timestamps=np.arange(30, dtype=float),
            header_timestamp_unit="seconds",
            header_phases_rad=np.zeros(30),
        )
        reason = ("alloc",)
    elif which == "within3d-fast-d1":
        case = patterned_case(directions=1, times=1)
        case.acquisition.update(storage_order="z-major", drift_within=True)
        reason = ("uninitialized",)
    elif which in ("within2d-n0", "within2d-fit-no-adjust"):
        case = patterned_case(mode="2d", directions=1, times=1)
        case.acquisition.update(storage_order="z-major", drift_within=True)
        if which.endswith("no-adjust"):
            case.acquisition["fit_drift"] = True
            case.extras["off_exposures"] = case.raw[:, :, :, :, None] / 2
            case.extras.update(
                header_timestamps=np.arange(10, dtype=float), header_timestamp_unit="seconds"
            )
            reason = ("timestamp",)
        else:
            reason = ("reference",)
    else:
        case.acquisition["drift_between"] = True
        case.extras["off_exposures"] = np.repeat(case.raw[:, :, :, :, None], 12, axis=4)
        reason = ("terminat",)
    assert_error("workflow_unsupported", case.raw, keywords(case), reason_words=reason)


def workspace_limit_counts(axial_zoom: int) -> dict[str, Any]:
    """Independent nonoverflowing integer provenance for SMALL raw geometry.

    This computes no target array and calls no product numerical operation.
    The accepted source distinguishes signed counts, unsigned workspace bytes,
    signed lookup bytes and native64 byte/stride representation.
    """
    t, d, p, z, y, x, orders = 1, 1, 3, 2, 2, 4, 2
    xo, yo, zo = x, y, z * axial_zoom
    q = 2 * orders - 1
    signed = dict(
        T=t,
        D=d,
        P=p,
        Q=q,
        Z=z,
        Y=y,
        X=x,
        O=orders,
        A=axial_zoom,
        Xo=xo,
        Yo=yo,
        Zo=zo,
        input_padded=(x + 2) * y * z,
        input_half=(x // 2 + 1) * y * z,
        input_volume=x * y * z,
        direction_z_phase=d * z * p,
        direction_phase_off=d * p,  # N=0, D*P*(N+1)
        separation=q * p,
        direction_order=d * orders,
        output_volume=xo * yo * zo,
        output_padded=(xo + 2) * yo * zo,
        output_half=(xo // 2 + 1) * yo * zo,
        lookup_bytes=4 * xo * yo,
    )
    # Actual binary64/complex128 aggregate storage is a native-intp obligation,
    # separate from source's explicit unsigned sizeof(complex_float) cast.
    native_bytes = dict(
        raw_float64=8 * t * d * p * z * y * x,
        input_quadratures_complex128=16 * t * d * q * z * y * (x // 2 + 1),
        image_float64=8 * t * zo * yo * xo,
        padded_complex128=16 * (xo + 2) * yo * zo,
        all_order_complex128=16 * t * d * q * zo * yo * (xo // 2 + 1),
    )
    return dict(
        raw_shape=(t, d, p, z, y, x),
        signed_counts_and_lookup_bytes=signed,
        unsigned_complex_workspace_bytes=8 * xo * yo * zo,
        unsigned_real_workspace_bytes=4 * xo * yo * zo,
        native64_bytes=native_bytes,
        alpha=1 / (x * y * z * axial_zoom * d),
    )


@pytest.mark.parametrize(
    "which",
    ["fractional-extents", "source-byte-limit", "unsafe-stencil", "unsigned-complex-workspace"],
)
def test_representation_limits_with_real_small_backing(which: str) -> None:
    if which == "unsigned-complex-workspace":
        case = constant_case()
        assert case.raw.shape == (1, 1, 3, 2, 2, 4) and case.raw.nbytes == 384
        case.acquisition["axial_zoom"] = 2**25
        counts = workspace_limit_counts(2**25)
        assert all(0 < v <= 2**31 - 1 for v in counts["signed_counts_and_lookup_bytes"].values())
        assert counts["unsigned_complex_workspace_bytes"] == 2**32 > 2**32 - 1
        assert counts["unsigned_real_workspace_bytes"] == 2**31 <= 2**32 - 1
        assert all(0 < v <= 2**63 - 1 for v in counts["native64_bytes"].values())
        assert counts["alpha"] == 2.0**-29
        positive = workspace_limit_counts(1)
        assert positive["unsigned_complex_workspace_bytes"] == 128
        assert all(v <= 2**31 - 1 for v in positive["signed_counts_and_lookup_bytes"].values())
        # The small positive is the unchanged algebra-3d-unit whole-entry
        # control. Huge zoom goes ONLY to validation, never a lower numerical
        # entry, broadcast, target/workspace allocation or observer image.
        assert_error("workflow_representation", case.raw, keywords(case))
        return
    entry()
    case = constant_case()
    if which == "fractional-extents":
        case.acquisition["lateral_zoom"] = 1.25
    elif which == "source-byte-limit":
        # Keep the original node/value as earlier SIGNED-COUNT rejection:
        # (X+2)*Y*Z=2**31+8, output2**31, lookup bytes2**32.
        # Its legacy name is NOT an isolated unsigned-byte proof. This real
        # broadcast view retains small validated backing, without allocation.
        case.raw = np.broadcast_to(
            np.array([6, 3, 3], dtype=np.float32)[None, None, :, None, None, None],
            (1, 1, 3, 2, 2, 2**29),
        )
    else:
        case.table.samples = np.ones((2, 1, 2), dtype=np.complex128)
    assert_error("workflow_representation", case.raw, keywords(case))


@pytest.mark.parametrize("which", ["calibration-optics", "identity-optics"])
def test_valid_but_conflicting_optics_is_metadata(which: str) -> None:
    entry()
    case = constant_case()
    kwargs = keywords(case)
    if which == "calibration-optics":
        case.bead = bead_fixture(z=2)
        kwargs = keywords(case, selection="raw-beads")
        kwargs["calibration"]["settings"]["wavelength_nm"] = 501
    else:
        kwargs["transfer_identity"]["optics"]["wavelength_nm"] = 501
    assert_error("workflow_metadata", case.raw, kwargs)


def test_genuine_prepared_embedded_optics_conflict_is_metadata() -> None:
    case = control_cases()["empirical-z2"]
    kwargs = keywords(case)
    assert case.bead is not None
    settings = dict(case.bead[1], wavelength_nm=501)
    # Both optics declarations remain valid 500nm. The genuinely prepared
    # record alone embeds valid 501nm optics; no record field is fabricated.
    kwargs["transfer"] = public().prepare_bead_otf(case.bead[0], **settings)
    assert dict(kwargs["transfer"].resolved_settings)["wavelength_nm"] == 501
    assert kwargs["optics"]["wavelength_nm"] == 500
    assert kwargs["transfer_identity"]["optics"]["wavelength_nm"] == 500
    assert_error("workflow_metadata", case.raw, kwargs)


@pytest.mark.parametrize("which", ["selected-clock-absent", "selected-phase-absent"])
def test_selected_clock_or_phase_data_missing_is_metadata(which: str) -> None:
    entry()
    case = control_cases()["within2d-fitted"]
    kwargs = keywords(case)
    if which == "selected-clock-absent":
        del kwargs["header_timestamps"]
        del kwargs["header_timestamp_unit"]
    else:
        del kwargs["header_phases_rad"]
    assert_error("workflow_metadata", case.raw, kwargs)


@pytest.mark.parametrize(
    "fault",
    [
        "x8-y8",
        "x6-y10",
        "x8-y11",
        "missing-empirical-orders",
        "superseded-background",
        "superseded-map",
        "superseded-phase-array",
    ],
)
def test_empirical_geometry_and_superseded_configuration_are_validated(fault: str) -> None:
    entry()
    case = constant_case()
    case.bead = bead_fixture(z=2)
    kwargs = keywords(case, selection="raw-beads")
    calibration = kwargs["calibration"]
    code = "workflow_input"
    if fault in ("x8-y8", "x6-y10", "x8-y11"):
        y, x = {"x8-y8": (8, 8), "x6-y10": (10, 6), "x8-y11": (11, 8)}[fault]
        calibration["raw"] = np.ones((3, 1, y, x))
    elif fault == "missing-empirical-orders":
        calibration["raw"] = calibration["raw"][:1]
        code = "workflow_selection"
    elif fault in ("superseded-background", "superseded-map"):
        calibration["settings"]["exposure_background_counts"] = np.zeros((2, 3))
        if fault == "superseded-background":
            calibration["settings"]["background_counts"] = -1.0
        else:
            calibration["settings"].update(
                background_map=np.ones((32, 31)), slope_map=np.ones((32, 32))
            )
        code = "workflow_config"
    else:
        kwargs = keywords(case)
        kwargs["acquisition"].update(
            phase_policy="steps", phase_steps_rad=np.array([2.0]), phases_rad=np.zeros((1, 2))
        )
        code = "workflow_config"
    assert_error(code, case.raw, kwargs)


def test_steps_source_allocation_limit_keeps_d4_explicit_lists_supported() -> None:
    entry()
    case = patterned_case(directions=4, times=1)
    case.acquisition.update(phase_policy="steps", phase_steps_rad=np.ones(4))
    assert_error("workflow_unsupported", case.raw, keywords(case))
