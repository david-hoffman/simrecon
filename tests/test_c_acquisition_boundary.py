"""Public validation, structural unsafe paths, precise boundary and representation."""

from copy import copy
from math import atan2, pi
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    close,
    events,
    known_options,
    optics,
    options,
    raw_pattern,
    transfer,
)
from c_acquisition_fixture import (
    numerical_case as numerical_case,
)


def reject(raw: Any = None, match: str | None = None, /, **changes: Any) -> None:
    if raw is None:
        raw = raw_pattern(y=10, x=10)
    error = api("AcquisitionModeError")
    assert issubclass(error, ValueError) and issubclass(error, api("SimreconError"))
    with pytest.raises(error, match=".+" if match is None else match) as caught:
        api("prepare_acquisition_bands")(raw, **options(**changes))
    if match is not None:
        assert caught.type is error, f"Wrong exact class: {caught.type.__name__}"


def assert_finite_bands(raw: Any, settings: dict[str, Any]) -> None:
    bands = api("prepare_acquisition_bands")(raw, **options(**settings))
    assert bands.quadratures.size and np.isfinite(bands.quadratures).all()
    assert np.isfinite(bands.noise_variance_factors).all()
    assert (bands.noise_variance_factors > 0).all()


@pytest.mark.parametrize(
    "field,bad",
    [
        ("acquisition_mode", "2D"),
        ("acquisition_mode", None),
        ("storage_order", "inferred"),
        ("dxy_um", 0),
        ("dxy_um", True),
        ("dz_um", -0.5),
        ("lateral_zoom", 0.5),
        ("lateral_zoom", 1.25),
        ("lateral_zoom", 1 + 2**-30),
        ("axial_zoom", 0),
        ("axial_zoom", 1.0),
        ("axial_zoom", True),
        ("norders", 0),
        ("norders", 3),
        ("norders", True),
        ("edge_pixels", 11),
        ("edge_pixels", 0.5),
        ("wavelength_nm", 0),
        ("wavelength_nm", 32768),
        ("wavelength_nm", 520.0),
        ("numerical_aperture", 0),
        ("numerical_aperture", 2.1),
        ("immersion_index", 0.9),
        ("immersion_index", 2.1),
        ("drift_filter_fraction", True),
        ("drift_filter_fraction", np.nan),
        ("phase_start_angle_rad", np.inf),
        ("linespacing_um", 0),
        ("phase_steps_rad", np.zeros((1, 1))),
        ("phases_rad", np.zeros((1, 2))),
        ("header_timestamps", np.zeros(2)),
        ("header_phases_rad", np.zeros((1, 3))),
        ("combine_off_orders", np.array([True, False])),
        ("combine_off_orders", [0, 0]),
        ("combine_off_orders", np.array([2**31, 0], dtype=np.int64)),
        ("combine_off_orders", np.array([1, 0], dtype=np.int32)),
    ],
)
def test_invalid_declarations_are_not_inferred_or_truncated(field: str, bad: Any) -> None:
    if field == "combine_off_orders" and isinstance(bad, np.ndarray):
        raw = raw_pattern(y=10, x=10)
        # Keep optics valid. The positive signed32 declaration alone lacks N;
        # the invalid bool/overflow arrays have an otherwise valid off route.
        valid_off = (np.roll(raw, 1, axis=-1) + 3)[..., None, :, :]
        off = None if bad.dtype == np.int32 else valid_off
        settings = dict(dxy_um=0.2, off_exposures=off, **optics(), **{field: bad})
        repair = (
            {"off_exposures": valid_off}
            if off is None
            else {field: np.array([1, 0], dtype=np.int32)}
        )
        selector = (
            r"combine[ _-]+off[ _-]+orders|"
            r"(?:off[ _-]+(?:combination[ _-]+)?|combination[ _-]+)"
            r"(?:order[ _-]+)?(?:selectors?|flags?)"
        )
        target = selector
        if off is None:
            target = (
                rf"{selector}|off[ _-]+(?:exposures?|frames?|images?|data|reference|combination)|"
                r"combining[ _-]+order[ _-]+(?:zero|\d+)\s+"
                r"(?:requires?|needs?) N\s*(?:>\s*0|>=\s*1)"
            )
        reject(raw, rf"(?i)\b(?:{target})\b", **settings)
        assert_finite_bands(raw, settings | repair)
    else:
        reject(**{field: bad})


@pytest.mark.parametrize(
    "field",
    [
        "equalize",
        "equalize_z",
        "equalize_time",
        "drift_between",
        "drift_within",
        "fit_drift",
        "adjust_phases",
        "negative_angle_step",
    ],
)
@pytest.mark.parametrize("bad", [0, 1, None, "false"])
def test_flags_actual_booleans(field: str, bad: Any) -> None:
    raw = raw_pattern(y=10, x=10)
    off = (np.roll(raw, 1, axis=-1) + 3)[..., None, :, :]
    # Valid optics and off reference leave a truthy invalid drift flag as
    # the rejected declaration, without a missing numerical prerequisite.
    settings = dict(off_exposures=off, **optics(), **{field: bad})
    selected_drift = field in {"drift_between", "drift_within"} and bad in (1, "false")
    match = None
    if selected_drift:
        axis = field.removeprefix("drift_")
        match = (
            rf"(?i)\b(?:drift[ _-]+{axis}|{axis}(?:[ _-]+(?:direction|angle|exposure))?"
            r"[ _-]+(?:drift|motion correction))\b"
        )
    reject(raw, match, **settings)
    # Both malformed values repair to the same request for each flag.
    if selected_drift and bad == 1:
        assert_finite_bands(raw, settings | {field: True})


@pytest.mark.parametrize(
    "kind",
    [
        "bool",
        "complex",
        "object",
        "string",
        "longdouble",
        "nan",
        "infinity",
        "inexact",
        "empty",
        "oddx",
        "wrongz",
        "rank",
        "list",
    ],
)
def test_raw_shape_type_finite_and_float32_exact_domain(kind: str) -> None:
    raw = raw_pattern(y=2, x=4)
    binary64_alias = False
    if kind in {"bool", "complex", "object", "string", "longdouble"}:
        raw = raw.astype(
            {
                "bool": bool,
                "complex": complex,
                "object": object,
                "string": str,
                "longdouble": np.longdouble,
            }[kind]
        )
        if kind == "longdouble":
            wide, ordinary = np.finfo(raw.dtype), np.finfo(np.float64)
            binary64_alias = (
                raw.dtype.itemsize == np.dtype(np.float64).itemsize
                and wide.nmant == ordinary.nmant
                and wide.maxexp == ordinary.maxexp
            )
    elif kind in {"nan", "infinity", "inexact"}:
        raw.flat[0] = {"nan": np.nan, "infinity": np.inf, "inexact": -1 + 2**-30}[kind]
    elif kind == "empty":
        raw = raw[:0]
    elif kind == "oddx":
        raw = raw[..., :3]
    elif kind == "wrongz":
        raw = np.repeat(raw, 2, axis=3)
    elif kind == "rank":
        raw = raw[0]
    else:
        raw = raw.tolist()
    if binary64_alias:
        accepted = api("prepare_acquisition_bands")(raw, **options())
        assert accepted.quadratures.dtype == np.complex128
    else:
        reject(raw, edge_pixels=0)


@pytest.mark.parametrize(
    "field",
    [
        "background",
        "flatfield_slope",
        "exposure_background",
        "off_exposures",
        "phases_rad",
        "phase_steps_rad",
        "header_timestamps",
        "header_phases_rad",
    ],
)
@pytest.mark.parametrize("kind", ["shape", "bool", "complex", "nonfinite"])
def test_all_supplied_arrays_validate_even_if_numerically_unused(field: str, kind: str) -> None:
    shapes = {
        "background": (10, 10),
        "flatfield_slope": (10, 10),
        "exposure_background": (1, 1, 3, 1),
        "off_exposures": (1, 1, 3, 1, 1, 10, 10),
        "phases_rad": (1, 3),
        "phase_steps_rad": (1,),
        "header_timestamps": (3,),
        "header_phases_rad": (3,),
    }
    value = np.ones(shapes[field])
    if kind == "shape":
        value = np.ones((2,))
    elif kind == "bool":
        value = value.astype(bool)
    elif kind == "complex":
        value = value.astype(complex)
    else:
        value.flat[0] = np.nan
    reject(**{field: value})


@pytest.mark.parametrize(
    "mode,z,d,changes,reason",
    [
        (
            "2d",
            1,
            2,
            {"storage_order": "z-major", "drift_between": True},
            "fast|z[- ]major|uninitial|storage[ _-]order",
        ),
        (
            "3d",
            2,
            1,
            {"storage_order": "z-major", "drift_within": True},
            "fast|z[- ]major|uninitial|storage[ _-]order",
        ),
        (
            "3d",
            2,
            4,
            {"storage_order": "z-major", "drift_within": True},
            "fast|z[- ]major|uninitial|storage[ _-]order",
        ),
        ("3d", 2, 3, {"drift_within": True, "adjust_phases": True}, "cubic|four|4|alloc|metadata"),
        ("2d", 1, 1, {"drift_within": True}, r"\boff\b|reference|\bN\b"),
        (
            "2d",
            1,
            1,
            {"drift_within": True, "fit_drift": True},
            "phase|timestamp|null|alloc|metadata",
        ),
        ("2d", 1, 1, {"drift_between": True, "dz_um": 0.0}, "dz|pitch|axial"),
    ],
)
def test_structural_unsafe_branch_rejects_before_numeric_work(
    mode: str, z: int, d: int, changes: dict[str, Any], reason: str
) -> None:
    # Zero raw energy cannot hide the structural selector behind a no-energy error.
    phases = 4 if changes.get("fit_drift") else 3
    raw = np.zeros((1, d, phases, z, 10, 10))
    prerequisites: dict[str, Any] = {}
    if changes.get("fit_drift") or (mode == "3d" and changes.get("drift_within")):
        # The fitted 2D row has a usable clock, phase vector and N1, but
        # deliberately lacks the flag that allocates the source clock.
        # In 3D supply the clock/phase route so storage or D is decisive.
        n = int(mode == "2d")
        size = d * phases * z * (n + 1)
        prerequisites.update(
            off_exposures=np.ones((*raw.shape[:4], 1, 10, 10)) if n else None,
            header_timestamps=np.arange(size, dtype=float),
            header_phases_rad=np.arange(size) * (pi / 4),
            adjust_phases=mode == "3d",
            linespacing_um=100.0,
        )
    with pytest.raises(api("AcquisitionModeError"), match="(?i)" + reason):
        api("prepare_acquisition_bands")(
            raw, **(options(acquisition_mode=mode) | optics() | prerequisites | changes)
        )


@pytest.mark.parametrize("side", ["x", "y"])
def test_selected_fixed10_prepass_small_dimension_is_unsafe(side: str) -> None:
    shape = (1, 1, 3, 1, 9 if side == "y" else 10, 8 if side == "x" else 10)
    reject(np.zeros(shape), drift_between=True, **optics())
    # Without that selected prepass the ordinary normal-edge0 domain survives.
    actual = api("prepare_acquisition_bands")(np.zeros(shape), **options())
    assert actual.quadratures.shape[-2:] == shape[-2:-1] + (shape[-1] // 2 + 1,)


def test_prepass_off_loop_limit_not_a_normal_off_count_limit() -> None:
    raw = raw_pattern(y=10, x=10)
    off = np.ones((1, 1, 3, 1, 12, 10, 10))
    reject(raw, off_exposures=off, drift_between=True, **optics())
    actual = api("prepare_acquisition_bands")(raw, **options(off_exposures=off))
    assert actual.off_quadratures is not None


@pytest.mark.parametrize(
    "field,bad",
    [
        ("input_scale", 1.0),
        ("dxy_um", 0.0),
        ("dz_um", -0.1),
        ("lateral_zoom", 0.5),
        ("axial_zoom", True),
        ("noise_variance_factors", np.zeros((1, 1, 2))),
        ("noise_variance_factors", np.ones((1, 2))),
        ("quadratures", np.ones((1, 1, 3, 1, 2, 3), dtype=np.complex64)),
        ("source_revision", "other"),
        ("acquisition_mode", "other"),
    ],
)
def test_invalid_used_records_both_consumers(field: str, bad: Any) -> None:
    original = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    forged = copy(original)
    object.__setattr__(forged, field, bad)
    with pytest.raises(api("ParameterEstimationError"), match=".+"):
        api("estimate_parameters")(
            forged,
            transfer(),
            initial_carriers_cyc_um=np.zeros((1, 2)),
            search_carriers=False,
            **optics(),
        )
    with pytest.raises(api("ReconstructionError"), match=".+"):
        api("reconstruct_known")(
            forged,
            transfer(),
            carriers_cyc_um=np.zeros((1, 2)),
            modulation=np.ones((1, 1)),
            **known_options(),
        )


@pytest.mark.parametrize(
    "field,bad",
    [
        ("wiener_increment", -0.5),
        ("wiener_increment", np.inf),
        ("wiener_increment", True),
        ("explode_factor", np.nan),
        ("explode_factor", True),
        ("filter_overlaps", 1),
        ("precise_taper", 1),
        ("power_taper_exponent", np.inf),
        ("output_taper", "polygon"),
        ("output_taper", "power"),
    ],
)
def test_new_known_options_invalid_or_nonpositive_schedule(field: str, bad: Any) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    table = transfer()
    settings = known_options() | dict(
        carriers_cyc_um=np.zeros((1, 2)), modulation=np.ones((1, 1)), **{field: bad}
    )
    missing_power = (field, bad) == ("output_taper", "power")
    match = (
        r"(?i)\b(?:power[ _-]+(?:taper(?:[ _-]+exponent)?|exponent|parameter)|output[ _-]+taper)\b"
        if missing_power
        else ".+"
    )
    error = api("ReconstructionError")
    with pytest.raises(error, match=match) as caught:
        api("reconstruct_known")(bands, table, **settings)
    if missing_power:
        assert caught.type is error, f"Wrong exact class: {caught.type.__name__}"
        repaired = settings | {"power_taper_exponent": 1.0}
        result = api("reconstruct_known")(bands, table, **repaired)
        assert result.image.size and np.isfinite(result.image).all()


def test_power_negative_at_zero_base_rejects_and_exponent_zero_constant() -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    args = dict(carriers_cyc_um=np.zeros((1, 2)), modulation=np.ones((1, 1)))
    with pytest.raises(api("ReconstructionError"), match="(?i)power|taper|zero|singular"):
        api("reconstruct_known")(
            bands,
            transfer(),
            **args,
            **known_options(output_taper="power", power_taper_exponent=-1.0),
        )
    zero = api("reconstruct_known")(
        bands, transfer(), **args, **known_options(output_taper="power", power_taper_exponent=0.0)
    )
    none = api("reconstruct_known")(bands, transfer(), **args, **known_options())
    np.testing.assert_array_equal(zero.image, none.image)


@pytest.mark.parametrize(
    "mode,z,y,taper", [("2d", 1, 2, "none"), ("2d", 1, 1, "cosine"), ("3d", 8, 2, "cosine")]
)
def test_precise_precompute_finite_positive_and_ordered_boundaries(
    mode: str, z: int, y: int, taper: str
) -> None:
    bands = api("prepare_acquisition_bands")(
        raw_pattern(d=3, z=z, y=y, x=4), **options(acquisition_mode=mode, dz_um=2.0)
    )
    carriers = np.array([[0.1, 0.02], [-0.04, 0.1], [0.03, -0.12]])
    settings = known_options(output_taper=taper, precise_taper=True)
    if mode == "3d":
        settings["numerical_aperture"] = 1.0
    actual = api("reconstruct_known")(
        bands, transfer(k=z), carriers_cyc_um=carriers, modulation=np.ones((3, 1)), **settings
    )
    if mode == "3d":
        # le=.52 um, theta=pi/2, dzf=1/16 cycles/um. c0=ceil(16/.52)=31
        # and c1=trunc(1.3*31)=40. Both exceed the native half-size 4
        # and independently clip to 3. In 2D the other filter keeps c=0.
        cutoffs = actual.axial_cutoffs_bins
        assert isinstance(cutoffs, np.ndarray) and cutoffs.dtype.kind in "iu"
        assert cutoffs.shape == (2,)
        np.testing.assert_array_equal(cutoffs, [3, 3])
    angles = np.array([atan2(ky, kx) for kx, ky in carriers])
    bounds = np.r_[angles - pi / 6, angles - pi / 6 + pi]
    bounds = np.array([b - 2 * pi if b > pi else b + 2 * pi if b < -pi else b for b in bounds])
    entries = events(actual, "sector-boundaries")
    assert len(entries) == 1
    close(entries[0]["carrier_angles_rad"], angles)
    close(entries[0]["boundary_angles_rad"], bounds)
    assert not events(actual, "precise-query")


@pytest.mark.parametrize("omit", [False, True])
def test_active_precise_2d_dc_undefined_even_when_center_omitted(omit: bool) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    with pytest.raises(api("ReconstructionError"), match="(?i)polar|precise|origin|atan|DC"):
        api("reconstruct_known")(
            bands,
            transfer(),
            carriers_cyc_um=np.array([[0.1, 0.02]]),
            modulation=np.ones((1, 1)),
            **known_options(output_taper="cosine", precise_taper=True, omit_order0=omit),
        )


def test_precise_zero_carrier_fails_precompute_even_taper_off_empty_loop() -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=1, x=4), **options())
    with pytest.raises(api("ReconstructionError"), match="(?i)polar|carrier|angle|atan"):
        api("reconstruct_known")(
            bands,
            transfer(),
            carriers_cyc_um=np.zeros((1, 2)),
            modulation=np.ones((1, 1)),
            **known_options(precise_taper=True),
        )


@pytest.mark.parametrize(
    "shape", [(1, 1, 3, 1, 2, 2**30), (2**30, 1, 3, 1, 1, 2), (1, 1, 3, 1, 2**30, 2)]
)
def test_source_signed_extents_reject_before_materialization(shape: tuple[int, ...]) -> None:
    raw = np.broadcast_to(np.array(1, dtype=np.float32), shape)
    reject(raw)


@pytest.mark.parametrize("zoom,axial", [(32768.0, 1), (1.0, 2**30)])
def test_unsigned_workspace_and_signed_lookup_representation(zoom: float, axial: int) -> None:
    reject(raw_pattern(y=2, x=4), lateral_zoom=zoom, axial_zoom=axial)


def test_reduced_order_preparation_positive_but_downstream_order1_unsupported() -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(p=1, y=2, x=4), **options(norders=1))
    assert bands.quadratures.shape[2] == 1
    with pytest.raises(api("ParameterEstimationError"), match="(?i)order|O|2"):
        api("estimate_parameters")(
            bands,
            transfer(1),
            initial_carriers_cyc_um=np.zeros((1, 2)),
            search_carriers=False,
            **optics(),
        )
    with pytest.raises(api("ReconstructionError"), match="(?i)order|O|2"):
        api("reconstruct_known")(
            bands,
            transfer(1),
            carriers_cyc_um=np.zeros((1, 2)),
            modulation=np.zeros((1, 0)),
            **known_options(),
        )


@pytest.mark.parametrize(
    "kind",
    ["shape", "off-shape", "background-shape", "bool", "complex", "nonfinite", "inexact", "layout"],
)
def test_layout_helper_rejects_invalid_values_without_camera_or_estimation(kind: str) -> None:
    raw = raw_pattern(z=2, y=2, x=4)
    settings: dict[str, Any] = dict(storage_order="direction-major")
    if kind == "shape":
        raw = raw[0]
    elif kind == "off-shape":
        settings["off_exposures"] = np.ones((1, 1, 3, 1, 1, 2, 4))
    elif kind == "background-shape":
        settings["exposure_background"] = np.zeros((1, 1, 3, 1))
    elif kind in {"bool", "complex"}:
        raw = raw.astype(bool if kind == "bool" else complex)
    elif kind in {"nonfinite", "inexact"}:
        raw.flat[0] = np.nan if kind == "nonfinite" else 1 + 2**-30
    else:
        settings["storage_order"] = "nominal-plane"
    with pytest.raises(api("AcquisitionModeError"), match=".+"):
        api("reinterpret_2d_planes")(raw, **settings)


def test_k1_sampler_last_vertex_error_and_interior_complex_positive() -> None:
    samples = np.array([[[1 + 2j], [3 - 1j], [2 + 4j]], [[2 - 3j], [4 + 1j], [3 - 2j]]])
    table = api("declare_otf")(samples, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=1 / 0.7)
    positive = api("sample_otf")(table, 0.375, 0, 0, dkz_cyc_um=1 / 0.7, order=0)
    close(positive, 2.5 + 1.5j)
    with pytest.raises(api("OtfError"), match="(?i)stencil|vertex|alloc|bound|index"):
        api("sample_otf")(table, 0.5, 0, 0, dkz_cyc_um=1 / 0.7, order=0)
    # Every used zero-weight vertex matters downstream too; no data=0 bypass.
    bands = api("prepare_acquisition_bands")(np.zeros((1, 1, 3, 1, 2, 4)), **options())
    with pytest.raises(api("ReconstructionError"), match="(?i)stencil|vertex|alloc|bound|index"):
        api("reconstruct_known")(
            bands,
            table,
            carriers_cyc_um=np.zeros((1, 2)),
            modulation=np.zeros((1, 1)),
            **known_options(),
        )


def test_known_negative_raw_signed_output_and_raw_dtype_positive_endpoints() -> None:
    raw = np.full((1, 1, 3, 1, 2, 4), -2, dtype=np.int16)
    bands = api("prepare_acquisition_bands")(raw, **options(dz_um=0.0))
    actual = api("reconstruct_known")(
        bands,
        transfer(),
        carriers_cyc_um=np.zeros((1, 2)),
        modulation=np.zeros((1, 1)),
        **known_options(filter_overlaps=False),
    )
    close(actual.image, -4.8)
    assert np.max(actual.image) < 0


def test_selector_fixed25_allocation_is_not_an_order_count_cap() -> None:
    raw = raw_pattern(p=51, y=1, x=2)
    with pytest.raises(api("AcquisitionModeError"), match="(?i)25|selector|combin|alloc"):
        api("prepare_acquisition_bands")(
            raw, **options(norders=26, combine_off_orders=np.zeros(26, dtype=np.int32))
        )
    actual = api("prepare_acquisition_bands")(raw, **options(norders=26))
    assert actual.noise_variance_factors.shape[-1] == 26
    edge = api("prepare_acquisition_bands")(
        raw[:, :, :49], **options(norders=25, combine_off_orders=np.zeros(25, dtype=np.int32))
    )
    assert edge.quadratures.shape[2] == 49


def test_unused_fit_phase_flags_do_not_evaluate_metadata_or_optical_numerics() -> None:
    raw = raw_pattern(y=2, x=4)
    plain = api("prepare_acquisition_bands")(raw, **options())
    flagged = api("prepare_acquisition_bands")(
        raw,
        **options(
            fit_drift=True,
            adjust_phases=True,
            wavelength_nm=32767,
            numerical_aperture=2.0,
            immersion_index=2.0,
            drift_filter_fraction=-1.0,
        ),
    )
    np.testing.assert_array_equal(flagged.quadratures, plain.quadratures)
    assert not events(flagged, "cubic-fit") and not events(flagged, "drift-correlation")
    assert flagged.header_timestamps_after is None


def test_selected_linked_phase_rank_failure_and_uniform_header_positive() -> None:
    raw = np.zeros((1, 1, 3, 1, 10, 10))
    raw[:, :, :, 0, 4, 5] = 32
    off = raw[..., None, :, :].copy()
    settings = (
        options(
            storage_order="z-major",
            off_exposures=off,
            drift_within=True,
            adjust_phases=True,
            header_timestamps=np.ones(6),
            linespacing_um=5.0,
        )
        | optics()
    )
    with pytest.raises(api("AcquisitionModeError"), match="(?i)rank|phase|matrix|design|singular"):
        api("prepare_acquisition_bands")(raw, **(settings | {"header_phases_rad": np.zeros(6)}))
    positive = api("prepare_acquisition_bands")(
        raw, **(settings | {"header_phases_rad": np.repeat(2 * np.pi * np.arange(3) / 3, 2)})
    )
    assert positive.phase_policies == ((("drift",),),)
    assert not events(positive, "cubic-fit")


def test_prepass_off_loop_exact_y_plus_one_endpoint_positive() -> None:
    raw = np.ones((1, 1, 3, 1, 10, 10))
    off = np.ones((1, 1, 3, 1, 11, 10, 10))
    actual = api("prepare_acquisition_bands")(
        raw, **(options(off_exposures=off, drift_between=True) | optics())
    )
    build = events(actual, "between-build")[0]
    close(build["centers"], 0.02)
    close(actual.off_quadratures[0, 0, 0, 0, 0, 0], 33, proof=actual.off_quadratures)


def test_outside_scope_keyword_does_not_silently_enable_unsafe_modes() -> None:
    raw = raw_pattern(y=2, x=4)
    for keyword in ["padding_z", "bessel", "two_objective", "automatic_wiener", "reference_type"]:
        with pytest.raises(TypeError):
            api("prepare_acquisition_bands")(raw, **options(), **{keyword: True})


def test_true_2d_requires_k1_in_both_consumers_and_later_wiener_failure() -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(t=2, y=2, x=4), **options())
    carriers = np.array([[0.1, 0.02]])
    for k in [1, 2]:
        table = transfer(k=k)
        if k == 2:
            with pytest.raises(api("ParameterEstimationError"), match="(?i)2d|axial|K|plane"):
                api("estimate_parameters")(
                    bands,
                    table,
                    initial_carriers_cyc_um=carriers,
                    search_carriers=False,
                    **optics(),
                )
            with pytest.raises(api("ReconstructionError"), match="(?i)2d|axial|K|plane"):
                api("reconstruct_known")(
                    bands,
                    table,
                    carriers_cyc_um=carriers,
                    modulation=np.ones((1, 1)),
                    **known_options(),
                )
        else:
            estimate = api("estimate_parameters")(
                bands, table, initial_carriers_cyc_um=carriers, search_carriers=False, **optics()
            )
            assert np.isfinite(estimate.modulation).all()
            positive = api("reconstruct_known")(
                bands,
                table,
                carriers_cyc_um=carriers,
                modulation=np.ones((1, 1)),
                **known_options(),
            )
            assert np.isfinite(positive.image).all()
            # Effective sequence(.05,-.1): the first time is valid, the second
            # invalidates the entire operation, never a partial image.
            with pytest.raises(api("ReconstructionError"), match="(?i)wiener|positive|time"):
                api("reconstruct_known")(
                    bands,
                    table,
                    carriers_cyc_um=carriers,
                    modulation=np.ones((1, 1)),
                    **known_options(wiener=0.2, wiener_increment=-0.3),
                )


def test_complex_workspace_unsigned_limit_is_independently_binding() -> None:
    # All preceding signed element/lookup counts remain representable.
    xo = yo = 16384
    zo = 2
    assert xo * yo * zo == 536870912 < 2**31
    assert 4 * xo * yo == 1073741824 < 2**31
    assert 8 * xo * yo * zo == 2**32
    assert 4 * xo * yo * zo == 2147483648 < 2**32
    with pytest.raises(
        api("AcquisitionModeError"), match="(?i)unsigned|uint32|workspace|byte|represent"
    ) as caught:
        api("prepare_acquisition_bands")(
            np.ones((1, 1, 3, 1, 4, 4)), **options(lateral_zoom=4096.0, axial_zoom=2)
        )
    cause = caught.value.__cause__
    while cause is not None:
        assert not isinstance(cause, MemoryError), (
            "allocation failure is not early representation rejection"
        )
        cause = cause.__cause__


@pytest.fixture(params=["estimate", "reconstruct"])
def acquisition_record_consumer(request: pytest.FixtureRequest) -> tuple[Any, type[ValueError]]:
    from functools import partial

    from simrecon import (
        ParameterEstimationError,
        ReconstructionError,
        estimate_parameters,
        reconstruct_known,
    )

    carriers = np.array([[0.1, 0.02]])
    if request.param == "estimate":
        return (
            partial(
                estimate_parameters,
                initial_carriers_cyc_um=carriers,
                search_carriers=False,
                **optics(),
            ),
            ParameterEstimationError,
        )
    return (
        partial(
            reconstruct_known,
            carriers_cyc_um=carriers,
            modulation=np.ones((1, 1)),
            **known_options(),
        ),
        ReconstructionError,
    )


@pytest.mark.parametrize("valid", [True, False], ids=["exact-string", "mutable-lookalike"])
def test_acquisition_provenance_requires_exact_strings(
    acquisition_record_consumer: tuple[Any, type[ValueError]], valid: bool
) -> None:
    from collections import UserString

    from c_acquisition_fixture import SOURCE10
    from simrecon import prepare_acquisition_bands

    bands = copy(prepare_acquisition_bands(raw_pattern(y=2, x=4), **options()))
    source, digest = SOURCE10[0]
    if valid:
        provenance = SOURCE10
    else:
        provenance = ((source, UserString(digest)), *SOURCE10[1:])
        assert provenance == SOURCE10
    object.__setattr__(bands, "reference_sha256", provenance)

    consume, error = acquisition_record_consumer
    table = transfer()
    if valid:
        assert consume(bands, table) is not None
    else:
        with pytest.raises(
            error,
            match=(
                r"(?im)\b(?:acquisition|acquisitionbands|bands|ten[ -]file)[ ._-]+"
                r"(?:reference_sha256|(?:input[ -]+)?provenance|"
                r"reference[ -]+(?:hashes|digests))\b|"
                r"^(?=.*\b(?:reference_sha256|mainfile\.c)\b)"
                r"(?=.*\b(?:digest|hash|pairs?|paired|str(?:ing)?s?|UserString)\b).+"
            ),
        ) as caught:
            consume(bands, table)
        assert caught.type is error


@pytest.mark.parametrize("valid", [True, False], ids=["last-fitting", "first-overflow"])
def test_acquisition_declared_on_frame_count_fits_signed32(
    acquisition_record_consumer: tuple[Any, type[ValueError]], valid: bool
) -> None:
    from simrecon import prepare_acquisition_bands

    bands = copy(prepare_acquisition_bands(raw_pattern(t=5, y=2, x=4), **options()))
    times, directions, _, sections, height, width = bands.input_shape
    signed_max = 2**31 - 1
    max_phases = signed_max // (times * directions * sections)
    phases = max_phases if valid else max_phases + 1
    # The per-section design and the one-time frame count fit in both cases.
    assert bands.quadratures.shape[2] * phases <= signed_max
    assert directions * sections * phases <= signed_max
    object.__setattr__(bands, "input_shape", (times, directions, phases, sections, height, width))

    consume, error = acquisition_record_consumer
    table = transfer()
    if valid:
        assert consume(bands, table) is not None
    else:
        with pytest.raises(
            error,
            match=(
                r"(?i)\b(?:T\s*[*×]\s*D\s*[*×]\s*(?:Z\s*[*×]\s*P|P\s*[*×]\s*Z)|"
                r"(?:aggregate|declared|total)[ _-]+"
                r"(?:on[ _-]+frames?|frame[ _-]+count|number[ _-]+of[ _-]+frames)|"
                r"number[ _-]+of[ _-]+on[ _-]+frames|"
                r"on[ _-]+frames?[ _-]+(?:count|product|total))\b"
            ),
        ) as caught:
            consume(bands, table)
        assert caught.type is error


class MutableSelector(str):
    """Supported selector text with caller-owned metadata."""

    note: str


class EqualToSelector(str):
    """Selector text that compares like a different supported literal."""

    claimed_literal: str

    def __eq__(self, other: object) -> bool:
        """Compare as the claimed literal."""
        return self.claimed_literal == other

    def __hash__(self) -> int:
        """Use the claimed literal hash for hashed membership too."""
        return hash(self.claimed_literal)


_MODE_REASON = (
    r"(?i)\bacquisition[ _-]+(?:modes?|dimensionality)\b|"
    r"""^\s*mode\s*(?::|=|must be)\s*['"]?(?:2d|3d)\b"""
)
_LAYOUT_REASON = (
    r"(?i)\b(?:storage[ _-]+(?:orders?|layouts?)|"
    r"raw[ _-]+(?:frame|stream|section)[ _-]+(?:order|layout))\b|"
    r"""^\s*(?:invalid[ _-]+frame[ _-]+order\b|"""
    r"""layout\s*(?::|=|must be)\s*['"]?(?:direction[ _-]+major|z[ _-]+major)\b)"""
)
_OFF_SAMPLE_SUBJECT = (
    r"\boff(?:\s*\(\s*reference\s*\))?[ _-]+(?:exposures?|frames?|images?|samples?|data)\b"
)
_SAMPLE_FLOAT32 = r"(?:float[ _-]*32|binary[ _-]*32|single[ _-]+precision|32[ _-]*bit[ _-]+float)"
_SAMPLE_REPRESENTATION = (
    r"\b(?:(?:exact(?:ly)?|lossless(?:ly)?)[ _-]+(?:convert\w*|conversion|represent\w*)|"
    r"(?:convert\w*|represent\w*)[ _-]+(?:exactly|losslessly)|"
    rf"{_SAMPLE_FLOAT32}[ _-]+(?:conversion|represent\w*|exact)|"
    r"(?:convert\w*|represent\w*|round[ _-]+trip) (?:to|as|in|through|via) "
    rf"(?:a )?{_SAMPLE_FLOAT32})\b"
)
# Keep the subject and operation together within the same clause.
_SAME_CLAUSE = r"(?:(?![.!?](?:\s|$)|[;\n]).)*"
_OFF_SAMPLE_REASON = (
    rf"(?i)(?:{_OFF_SAMPLE_SUBJECT}{_SAME_CLAUSE}{_SAMPLE_REPRESENTATION}|"
    rf"{_SAMPLE_REPRESENTATION}{_SAME_CLAUSE}{_OFF_SAMPLE_SUBJECT})"
)


def assert_resolved_selector(literal: str, **observed: object) -> None:
    for field, value in observed.items():
        assert type(value) is str, f"{field} resolved to {type(value).__name__}"
        assert value == literal, f"{field} resolved to {value!r}"


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)], ids=["2d", "3d"])
@pytest.mark.parametrize("kind", ["plain", "numpy", "mutable"])
def test_acquisition_consumer_resolves_literal_mode(
    acquisition_record_consumer: tuple[Any, type[ValueError]], mode: str, z: int, kind: str
) -> None:
    original = api("prepare_acquisition_bands")(
        raw_pattern(z=z, y=4, x=6), **options(acquisition_mode=mode)
    )
    consume, error = acquisition_record_consumer
    table = transfer(k=z)
    expected = consume(original, table)
    field = "modulation" if error.__name__ == "ParameterEstimationError" else "image"
    expected_values = getattr(expected, field)
    assert expected_values.size and np.isfinite(expected_values).all()
    assert_resolved_selector(mode, result=dict(expected.resolved_settings)["acquisition_mode"])
    if kind == "plain":
        return

    # Preserve every other used field on a real prepared record. The public
    # consumer validates the selected mode without replaying raw preparation.
    candidate = copy(original)
    selector = np.str_(mode) if kind == "numpy" else MutableSelector(mode)
    if isinstance(selector, MutableSelector):
        selector.note = "before"
    object.__setattr__(candidate, "acquisition_mode", selector)
    result = consume(candidate, table)
    if isinstance(selector, MutableSelector):
        selector.note = "after"
    np.testing.assert_array_equal(getattr(result, field), expected_values)
    assert_resolved_selector(mode, result=dict(result.resolved_settings)["acquisition_mode"])


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)], ids=["2d", "3d"])
def test_prepare_acquisition_resolves_literal_mode(mode: str, z: int) -> None:
    from simrecon import prepare_acquisition_bands as prepare

    raw = raw_pattern(z=z, y=4, x=6)
    plain = prepare(raw, **options(acquisition_mode=mode))
    selector = MutableSelector(mode)
    selector.note = "before"
    actual = prepare(raw, **options(acquisition_mode=selector))
    selector.note = "after"
    assert actual.input_shape == raw.shape
    np.testing.assert_array_equal(actual.quadratures, plain.quadratures)
    assert_resolved_selector(
        mode,
        record=actual.acquisition_mode,
        settings=dict(actual.resolved_settings)["acquisition_mode"],
    )


@pytest.mark.parametrize("layout", ["direction-major", "z-major"])
def test_prepare_acquisition_resolves_literal_layout(layout: str) -> None:
    from simrecon import prepare_acquisition_bands as prepare

    raw = raw_pattern(y=10, x=10)
    settings = options(drift_between=True) | optics()
    plain = prepare(raw, storage_order=layout, **settings)
    selector = MutableSelector(layout)
    selector.note = "before"
    actual = prepare(raw, storage_order=selector, **settings)
    selector.note = "after"
    # At D=1 the selected z-major prepass is skipped. The ordinary layout
    # still builds its prepass, even though there is no moving direction.
    assert len(events(actual, "between-build")) == int(layout == "direction-major")
    np.testing.assert_array_equal(actual.quadratures, plain.quadratures)
    assert_resolved_selector(
        layout,
        record=actual.storage_order,
        settings=dict(actual.resolved_settings)["storage_order"],
    )


@pytest.mark.parametrize("layout", ["direction-major", "z-major"])
def test_regrouping_resolves_literal_layout(layout: str) -> None:
    from simrecon import reinterpret_2d_planes as regroup

    raw = raw_pattern(d=2, z=2, y=2, x=4)
    selector = MutableSelector(layout)
    selector.note = "before"
    plain = regroup(raw, storage_order=layout)
    actual = regroup(raw, storage_order=selector)
    selector.note = "after"

    source = (
        [[[0, 0], [0, 1]], [[1, 0], [1, 1]]]
        if layout == "direction-major"
        else [[[0, 0], [1, 0]], [[0, 1], [1, 1]]]
    )
    np.testing.assert_array_equal(actual.source_direction_z, source)
    for t, d in np.ndindex(2, 2):
        original_direction, original_z = source[t][d]
        np.testing.assert_array_equal(
            actual.images[t, d, :, 0], raw[0, original_direction, :, original_z]
        )
    np.testing.assert_array_equal(actual.images, plain.images)
    assert_resolved_selector(layout, record=actual.storage_order)


@pytest.mark.parametrize(
    "entry,field,legal,reason",
    [
        ("prepare_acquisition_bands", "acquisition_mode", "2d", _MODE_REASON),
        ("prepare_acquisition_bands", "storage_order", "direction-major", _LAYOUT_REASON),
        ("reinterpret_2d_planes", "storage_order", "direction-major", _LAYOUT_REASON),
    ],
    ids=["prepare-mode", "prepare-layout", "regroup-layout"],
)
def test_acquisition_declarations_validate_underlying_selector_text(
    entry: str, field: str, legal: str, reason: str
) -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands, reinterpret_2d_planes

    declare = (
        prepare_acquisition_bands if entry == "prepare_acquisition_bands" else reinterpret_2d_planes
    )
    raw = raw_pattern(y=2, x=4)
    settings = options() if entry == "prepare_acquisition_bands" else dict[str, Any]()
    settings[field] = legal
    positive = declare(raw, **settings)
    assert_resolved_selector(legal, record=getattr(positive, field))
    selector = EqualToSelector("unsupported")
    selector.claimed_literal = legal
    assert str.__str__(selector) == "unsupported" and selector == legal
    settings[field] = selector
    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        declare(raw, **settings)
    assert caught.type is AcquisitionModeError


def test_acquisition_power_result_resolves_literal_taper() -> None:
    from simrecon import prepare_acquisition_bands
    from simrecon import reconstruct_known as reconstruct

    bands = prepare_acquisition_bands(raw_pattern(y=4, x=6), **options())
    args = dict(
        carriers_cyc_um=np.array([[0.11, 0.02]]),
        modulation=np.array([[0.5 + 0.2j]]),
    )
    table = transfer()
    plain = reconstruct(
        bands, table, **args, **known_options(output_taper="power", power_taper_exponent=1)
    )
    untapered = reconstruct(bands, table, **args, **known_options())
    assert np.any(plain.image != untapered.image)
    selector = MutableSelector("power")
    selector.note = "before"
    actual = reconstruct(
        bands, table, **args, **known_options(output_taper=selector, power_taper_exponent=1)
    )
    selector.note = "after"
    np.testing.assert_array_equal(actual.image, plain.image)
    np.testing.assert_array_equal(actual.filtered_quadratures, plain.filtered_quadratures)
    assert_resolved_selector("power", result=dict(actual.resolved_settings)["output_taper"])


@pytest.mark.parametrize(
    "entry", ["prepare_acquisition_bands", "reinterpret_2d_planes"], ids=["prepare", "regroup"]
)
def test_inexact_off_sample_names_the_off_field(entry: str) -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands, reinterpret_2d_planes

    raw = raw_pattern(y=2, x=4)
    off = np.ones((*raw.shape[:4], 1, *raw.shape[4:]), dtype=np.float64)
    malformed = off.copy()
    malformed.flat[0] = 1 + 2**-30
    assert malformed.flat[0] != 1 and np.float32(malformed.flat[0]) == 1

    settings: dict[str, Any]
    if entry == "prepare_acquisition_bands":
        declare, settings = prepare_acquisition_bands, options()
        repaired = prepare_acquisition_bands(raw, off_exposures=off, **settings)
        assert repaired.off_quadratures is not None
        assert np.isfinite(repaired.off_quadratures).all()
    else:
        declare, settings = reinterpret_2d_planes, {"storage_order": "direction-major"}
        repaired = reinterpret_2d_planes(raw, off_exposures=off, **settings)
        np.testing.assert_array_equal(repaired.off_exposures, off)

    with pytest.raises(AcquisitionModeError, match=_OFF_SAMPLE_REASON) as caught:
        declare(raw, off_exposures=malformed, **settings)
    assert caught.type is AcquisitionModeError


def test_regrouping_routes_by_underlying_selector_text() -> None:
    from simrecon import reinterpret_2d_planes as regroup

    raw = raw_pattern(d=2, z=2, y=2, x=4)
    direction_major = regroup(raw, storage_order="direction-major")
    z_major = regroup(raw, storage_order="z-major")
    assert not np.array_equal(direction_major.source_direction_z, z_major.source_direction_z)
    assert not np.array_equal(direction_major.images, z_major.images)

    selector = EqualToSelector("direction-major")
    selector.claimed_literal = "z-major"
    assert str.__str__(selector) == "direction-major"
    matches_direction_major = selector == "direction-major"
    assert selector == "z-major" and not matches_direction_major
    actual = regroup(raw, storage_order=selector)

    np.testing.assert_array_equal(actual.source_direction_z, direction_major.source_direction_z)
    np.testing.assert_array_equal(actual.images, direction_major.images)
    assert_resolved_selector("direction-major", record=actual.storage_order)
