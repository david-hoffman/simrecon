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


class AdvertisedClass:
    """Forward public data and conversions while claiming the backing value's class."""

    def __init__(self, value: Any, *, slice_backing: Any = None) -> None:
        self.value = value
        self.slice_backing = value if slice_backing is None else slice_backing

    def __getattribute__(self, name: str) -> Any:
        """Advertise the backing class without changing the actual type."""
        if name == "__class__":
            return type(self.value)
        return super().__getattribute__(name)

    def __getattr__(self, name: str) -> Any:
        """Forward attributes to the genuine backing value."""
        return getattr(self.value, name)

    def __getitem__(self, key: Any) -> Any:
        """Read from the selected slice backing."""
        return self.slice_backing[key]

    def __iter__(self) -> Any:
        """Iterate over the genuine backing value."""
        return iter(self.value)

    def __len__(self) -> int:
        """Report the genuine backing length."""
        return len(self.value)

    def __int__(self) -> int:
        """Convert the genuine backing value to an integer."""
        return int(self.value)

    def __float__(self) -> float:
        """Convert the genuine backing value to a float."""
        return float(self.value)

    def __index__(self) -> int:
        """Return the integral backing value for indexing."""
        return self.value.__index__()

    def __bool__(self) -> bool:
        """Return the genuine backing truth value."""
        return bool(self.value)

    def __abs__(self) -> Any:
        """Return the genuine backing magnitude."""
        return abs(self.value)

    def __le__(self, other: Any) -> Any:
        """Compare the genuine backing value with the supplied bound."""
        return self.value <= other

    def __gt__(self, other: Any) -> Any:
        """Compare the genuine backing value with the supplied lower bound."""
        return self.value > other


def advertise(value: Any, *, slice_backing: Any = None) -> Any:
    proxy = AdvertisedClass(value, slice_backing=slice_backing)
    assert not issubclass(type(proxy), type(value))
    assert isinstance(proxy, type(value))
    return proxy


class ConsistentArray(np.ndarray):
    """A real NumPy subclass with ordinary array behavior."""


def assert_public_control(result: Any, error: type[ValueError]) -> None:
    if error is api("ParameterEstimationError"):
        assert issubclass(type(result), api("EstimatedParameters"))
        data = result.modulation
    else:
        assert issubclass(type(result), api("KnownReconstruction"))
        data = result.image
    assert data.size and np.isfinite(data).all()


@pytest.mark.parametrize(
    "field,reason",
    [
        ("bands", r"bands|AcquisitionBands|PreparedBands"),
        ("transfer", r"transfer|OpticalTransfer|otf"),
        ("input_shape", r"input[ _-]+shape|on[ _-]+shape"),
        ("quadratures", r"quadratures?|bands[ _-]+(?:array|coefficients)"),
        ("noise_variance_factors", r"noise(?:[ _-]+(?:variance|factors?))?"),
        ("declared_samples", r"(?:transfer|otf|table)[ ._-]+samples?|samples?"),
        ("computed_samples", r"(?:transfer|otf|table)[ ._-]+samples?|samples?"),
    ],
    ids=["bands", "transfer", "shape", "quadratures", "noise", "declared", "computed"],
)
def test_actual_used_records_and_arrays(
    acquisition_record_consumer: tuple[Any, type[ValueError]], field: str, reason: str
) -> None:
    from simrecon import prepare_acquisition_bands, prepare_bands, prepare_bead_otf
    from test_c_acquisition_transfer import bead_options, bead_raw

    consume, error = acquisition_record_consumer
    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    assert issubclass(type(bands), api("AcquisitionBands"))
    table = (
        prepare_bead_otf(bead_raw(10, 8), **bead_options()).transfer
        if field == "computed_samples"
        else transfer()
    )
    assert_public_control(consume(bands, table), error)

    candidate_bands, candidate_table = bands, table
    if field == "bands":
        legacy_options = options(lateral_zoom=1)
        del legacy_options["acquisition_mode"]
        legacy = prepare_bands(raw_pattern(z=2, y=2, x=4), **legacy_options)
        assert issubclass(type(legacy), api("PreparedBands"))
        assert_public_control(consume(legacy, transfer(k=2)), error)
        candidate_bands = advertise(bands)
    elif field == "transfer":
        candidate_table = advertise(table)
    elif field.endswith("_samples"):
        samples = table.samples
        assert samples.dtype == np.complex128
        if field == "computed_samples":
            assert np.any(samples != samples.astype(np.complex64))
        genuine_samples = ConsistentArray(samples.shape, dtype=samples.dtype)
        np.copyto(genuine_samples, samples)
        genuine_samples.flags.writeable = False
        subclass_table = copy(table)
        object.__setattr__(subclass_table, "samples", genuine_samples)
        assert_public_control(consume(bands, subclass_table), error)
        candidate_table = copy(table)
        object.__setattr__(candidate_table, "samples", advertise(samples))
    else:
        candidate_bands = copy(bands)
        object.__setattr__(candidate_bands, field, advertise(getattr(bands, field)))

    with pytest.raises(error, match=rf"(?i)\b(?:{reason})\b") as caught:
        consume(candidate_bands, candidate_table)
    assert caught.type is error


def assert_estimator_acquisition_provenance(result: Any) -> None:
    from c_acquisition_fixture import ESTIMATE_KEYS, SOURCE6, SOURCE10

    settings = result.resolved_settings
    assert type(settings) is tuple
    assert all(type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str for pair in settings)
    assert tuple(key for key, _ in settings) == (
        *ESTIMATE_KEYS,
        "acquisition_mode",
        "acquisition_reference_sha256",
    )
    provenance = settings[-1][1]
    for actual, expected in ((provenance, SOURCE10), (result.reference_sha256, SOURCE6)):
        assert type(actual) is tuple
        assert all(type(pair) is tuple for pair in actual)
        assert all(type(part) is str for pair in actual for part in pair), (
            "Provenance leaf types",
            [type(part).__name__ for pair in actual for part in pair],
        )
        assert actual == expected


def test_estimator_publishes_only_validated_acquisition_provenance() -> None:
    from collections import UserString
    from dataclasses import fields

    from c_acquisition_fixture import SOURCE10
    from simrecon import (
        AcquisitionBands,
        ParameterEstimationError,
        estimate_parameters,
        prepare_acquisition_bands,
    )

    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    table = transfer()
    name, digest = SOURCE10[0]
    later = ((name, UserString(digest)), *SOURCE10[1:])
    assert later == SOURCE10

    class StableBands(AcquisitionBands):
        """Genuine subclass with ordinary stable provenance."""

    class UnstableBands(AcquisitionBands):
        """Genuine record exposing different provenance on repeated reads."""

        def __getattribute__(self, field: str) -> Any:
            if field == "reference_sha256":
                if getattr(self, "_provenance_seen", False):
                    return later
                object.__setattr__(self, "_provenance_seen", True)
            return super().__getattribute__(field)

    def estimate(candidate: AcquisitionBands) -> Any:
        return estimate_parameters(
            candidate,
            table,
            initial_carriers_cyc_um=np.array([[0.1, 0.02]]),
            search_carriers=False,
            **optics(),
        )

    values = {field.name: getattr(bands, field.name) for field in fields(bands)}
    stable = estimate(StableBands(**values))
    assert_public_control(stable, ParameterEstimationError)
    assert_estimator_acquisition_provenance(stable)

    unstable = UnstableBands(**values)
    try:
        actual = estimate(unstable)
    except ParameterEstimationError as error:
        import re

        assert type(error) is ParameterEstimationError
        assert re.search(
            r"(?i)\b(?:provenance|reference_sha256|source[ _-]+identity|"
            r"reference[ _-]+(?:hashes|digests)|digest|"
            r"(?:invalid|inconsistent)[ _-]+(?:AcquisitionBands|bands|record))\b",
            str(error),
        ), str(error)
    else:
        assert_public_control(actual, ParameterEstimationError)
        assert_estimator_acquisition_provenance(actual)


@pytest.mark.parametrize(
    "entry,field",
    [
        ("prepare_acquisition_bands", "images"),
        ("prepare_acquisition_bands", "off_exposures"),
        ("reinterpret_2d_planes", "off_exposures"),
    ],
    ids=["prepare-on", "prepare-off", "regroup-off"],
)
def test_actual_acquisition_raw_arrays(entry: str, field: str) -> None:
    import simrecon

    raw = raw_pattern(y=2, x=4)
    off = np.ones((*raw.shape[:4], 1, *raw.shape[4:]), dtype=np.float64)
    args = {"images": raw, "off_exposures": off}
    declare: Any
    settings: dict[str, Any]
    if entry == "prepare_acquisition_bands":
        declare, settings = simrecon.prepare_acquisition_bands, options()
    else:
        declare, settings = simrecon.reinterpret_2d_planes, {"storage_order": "direction-major"}

    genuine = args[field]
    result = declare(**(args | {field: genuine.view(ConsistentArray)}), **settings)
    if entry == "prepare_acquisition_bands":
        assert result.off_quadratures is not None and np.isfinite(result.off_quadratures).all()
    else:
        np.testing.assert_array_equal(result.off_exposures, off)
    reason = (
        r"\b(?:images?|on[ _-]+(?:frames?|exposures?))\b"
        if field == "images"
        else (_OFF_SAMPLE_SUBJECT)
    )
    with pytest.raises(simrecon.AcquisitionModeError, match=rf"(?i){reason}") as caught:
        declare(**(args | {field: advertise(genuine)}), **settings)
    assert caught.type is simrecon.AcquisitionModeError


_RAW_IMAGE_SUBJECT = r"\b(?:(?<!\boff[ _-])images?|on[ _-]+(?:frames?|exposures?))\b"
_RAW_ARRAY_KIND = (
    r"(?:an?\s+)?(?:instance\s+of\s+)?(?:(?:actual|genuine)\s+)?"
    r"(?:numpy[ ._-]+)?(?:ndarray|array)\b(?!\s+(?:of\b|with\s+(?:a\s+)?dtype\b))"
)
_RAW_NONARRAY_REASON = (
    rf"(?i)(?:{_RAW_IMAGE_SUBJECT}(?:[ _-]+input)?\s*(?::\s*)?(?:"
    rf"(?:must\s+be|expected|requires?|(?:(?:is|are)\s+)?not)\s+{_RAW_ARRAY_KIND}|"
    rf"{_RAW_ARRAY_KIND}\s+(?:is\s+)?required\b|non[ _-]?array\b)|"
    rf"\bexpected\s+{_RAW_ARRAY_KIND}\s+for\s+{_RAW_IMAGE_SUBJECT})"
)


def test_regrouping_rejects_split_backing_raw_images() -> None:
    from simrecon import AcquisitionModeError, reinterpret_2d_planes

    legal = np.ones((1, 2, 3, 2, 2, 4), dtype=np.float64)
    inexact = legal.copy()
    sample = 1 + 2**-30
    inexact.flat[0] = sample
    assert sample != 1 and np.float32(sample) == 1
    split = advertise(legal, slice_backing=inexact)
    np.testing.assert_array_equal(np.asarray(split), legal)
    assert split[0, 0, :, 0].flat[0] == sample

    settings = {"storage_order": "direction-major"}
    for images in (legal, legal.view(ConsistentArray)):
        np.testing.assert_array_equal(reinterpret_2d_planes(images, **settings).images, 1)
    with pytest.raises(
        AcquisitionModeError,
        match=rf"(?i)(?=.*\bimages?\b)(?=.*{_SAMPLE_REPRESENTATION})",
    ) as caught:
        reinterpret_2d_planes(inexact, **settings)
    assert caught.type is AcquisitionModeError

    with pytest.raises(AcquisitionModeError, match=_RAW_NONARRAY_REASON) as caught:
        reinterpret_2d_planes(split, **settings)
    assert caught.type is AcquisitionModeError


@pytest.mark.parametrize(
    "field,legal,neighbor,reason",
    [
        ("norders", 2, np.int64(2), r"norders|order[ _-]+count|number[ _-]+of[ _-]+orders"),
        ("dxy_um", 1.0, np.float64(1), r"dxy(?:_um)?|lateral[ _-]+(?:pitch|sampling|spacing)"),
        ("equalize", False, np.bool_(False), r"equaliz\w*"),
        (
            "combine_off_orders",
            np.zeros(2, dtype=np.int32),
            np.zeros(2, dtype=np.int64).view(ConsistentArray),
            r"combine[ _-]+off[ _-]+orders|"
            r"off[ _-]+(?:combination[ _-]+)?(?:order[ _-]+)?selectors?",
        ),
    ],
    ids=["count", "real", "boolean", "selectors"],
)
def test_actual_acquisition_declaration_categories(
    field: str, legal: Any, neighbor: Any, reason: str
) -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands

    raw = raw_pattern(y=2, x=4)
    expected = (0, 0) if field == "combine_off_orders" else legal
    for value in (legal, neighbor):
        result = prepare_acquisition_bands(raw, **options(**{field: value}))
        assert result.quadratures.size and np.isfinite(result.quadratures).all()
        assert dict(result.resolved_settings)[field] == expected

    with pytest.raises(AcquisitionModeError, match=rf"(?i)\b(?:{reason})\b") as caught:
        prepare_acquisition_bands(raw, **options(**{field: advertise(legal)}))
    assert caught.type is AcquisitionModeError


def test_actual_single_plane_rectangular_bead_input() -> None:
    from simrecon import OtfError, prepare_bead_otf
    from test_c_acquisition_transfer import bead_options, bead_raw

    raw = bead_raw(10, 8)
    assert raw.shape == (3, 1, 10, 8)
    settings = bead_options()
    result = prepare_bead_otf(raw, **settings)
    assert result.transfer.samples.shape == (2, 5, 1)
    assert np.isfinite(result.transfer.samples).all()

    with pytest.raises(
        OtfError, match=r"(?i)\b(?:raw|bead[ _-]+(?:images?|frames?|data))\b"
    ) as caught:
        prepare_bead_otf(advertise(raw), **settings)
    assert caught.type is OtfError


def has_off_representation_reason(message: str) -> bool:
    import re

    # Keep an explicit contrast between inputs from joining an unrelated reason.
    parts = re.split(
        r"\b(?:but|whereas|while)\b|(?:,|\band\b)\s+(?=(?:on|off)[ _-])",
        message,
        flags=re.IGNORECASE,
    )
    on_reason = rf"(?i){_RAW_IMAGE_SUBJECT}{_SAME_CLAUSE}{_SAMPLE_REPRESENTATION}"
    # An off label on a wrapper cannot relabel an explicitly named on-image failure.
    if any(
        re.search(on_reason, segment)
        for part in parts
        for segment in re.split(rf"(?i){_OFF_SAMPLE_SUBJECT}", part)
    ):
        return False
    return any(re.search(_OFF_SAMPLE_REASON, part) is not None for part in parts)


@pytest.mark.parametrize(
    "entry", ["prepare_acquisition_bands", "reinterpret_2d_planes"], ids=["prepare", "regroup"]
)
def test_inexact_off_diagnostic_chain_identifies_off_input(entry: str) -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands, reinterpret_2d_planes

    raw = raw_pattern(y=2, x=4)
    off = np.ones((*raw.shape[:4], 1, *raw.shape[4:]), dtype=np.float64)
    malformed = off.copy()
    malformed.flat[0] = 1 + 2**-30
    assert malformed.flat[0] != 1 and np.float32(malformed.flat[0]) == 1
    declare: Any
    settings: dict[str, Any]
    if entry == "prepare_acquisition_bands":
        declare, settings = prepare_acquisition_bands, options()
        repaired = declare(raw, off_exposures=off, **settings)
        assert repaired.off_quadratures is not None and np.isfinite(repaired.off_quadratures).all()
    else:
        declare, settings = reinterpret_2d_planes, {"storage_order": "direction-major"}
        repaired = declare(raw, off_exposures=off, **settings)
        np.testing.assert_array_equal(repaired.off_exposures, off)

    with pytest.raises(AcquisitionModeError, match=_OFF_SAMPLE_REASON) as caught:
        declare(raw, off_exposures=malformed, **settings)
    assert caught.type is AcquisitionModeError

    frame: BaseException | None = caught.value
    while frame is not None:
        message = str(frame)
        assert has_off_representation_reason(message), f"{type(frame).__name__}: {message}"
        frame = frame.__cause__ or (None if frame.__suppress_context__ else frame.__context__)


def has_used_array_reason(field: str, message: str) -> bool:
    import re

    # A bare field label can identify a direct validation error. A bare word
    # inside an operation message (for example overlap samples) cannot.
    direct = (
        r"""(?:^|:\s+)\s*['"]?{}['"]?"""
        r"(?:\s*[:=]|\s+(?:changed|must\s+be|(?:is|are)\s+(?:invalid|inconsistent|"
        r"not\s+(?:an?\s+)?(?:numpy\s+)?(?:ndarray|array)))\b)"
    )
    reasons = {
        "quadratures": (
            r"\b(?:quadratures?|bands[ _-]+arrays?|(?:bands|side[ _-]?bands?)[ _-]+coefficients?)\b"
        ),
        "samples": (
            r"\b(?:optical[ _-]?transfer|transfer|otf|table)[ ._-]+(?:samples?|coefficients?)\b"
            r"|" + direct.format("samples")
        ),
        "noise_variance_factors": (
            r"\bnoise[ _-]+(?:variance(?:[ _-]+factors?)?|factors?|arrays?)\b"
            r"|" + direct.format("noise")
        ),
    }
    return re.search(reasons[field], message, re.IGNORECASE) is not None


@pytest.mark.parametrize(
    "acquisition_record_consumer,field",
    [
        ("estimate", "quadratures"),
        ("estimate", "samples"),
        ("reconstruct", "quadratures"),
        ("reconstruct", "noise_variance_factors"),
        ("reconstruct", "samples"),
    ],
    indirect=["acquisition_record_consumer"],
    ids=[
        "estimate-quadratures",
        "estimate-transfer-samples",
        "reconstruct-quadratures",
        "reconstruct-noise",
        "reconstruct-transfer-samples",
    ],
)
def test_consumers_use_the_validated_acquisition_arrays(
    acquisition_record_consumer: tuple[Any, type[ValueError]], field: str
) -> None:
    from dataclasses import fields, replace

    from simrecon import ParameterEstimationError, prepare_acquisition_bands

    consume, error = acquisition_record_consumer
    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    table = transfer()
    original = table if field == "samples" else bands
    original_type: Any = type(original)

    class UsedArrayRecord(original_type):
        """Genuine record with an optional inconsistent read of one used field."""

        def __getattribute__(self, name: str) -> Any:
            if name == field and (later := getattr(self, "_later_value", None)) is not None:
                if getattr(self, "_selected_array_seen", False):
                    return later
                object.__setattr__(self, "_selected_array_seen", True)
            return super().__getattribute__(name)

    def observe(record: Any) -> np.ndarray:
        result = consume(bands, record) if field == "samples" else consume(record, table)
        assert_public_control(result, error)
        return result.modulation if error is ParameterEstimationError else result.image

    control = observe(original)
    values = {item.name: getattr(original, item.name) for item in fields(original)}
    stable = UsedArrayRecord(**values)
    np.testing.assert_array_equal(observe(stable), control)

    alternate = values[field].copy()
    if field == "quadratures":
        alternate[:, :, 1:] *= 2
    elif field == "noise_variance_factors":
        alternate *= 2
    else:
        alternate[1:] *= 2
        alternate.flags.writeable = False
    alternate_control = observe(replace(original, **{field: alternate}))
    assert not np.array_equal(alternate_control, control), f"{field} control must affect the result"

    unstable = UsedArrayRecord(**values)
    later = advertise(alternate) if field == "samples" else alternate.tolist()
    assert not issubclass(type(later), np.ndarray)
    object.__setattr__(unstable, "_later_value", later)
    try:
        actual = observe(unstable)
    except error as rejected:
        assert type(rejected) is error
        assert has_used_array_reason(field, str(rejected)), str(rejected)
    else:
        assert np.array_equal(actual, control), (
            f"{field}: result differs from the validated input; "
            f"matches genuine alternate: {np.array_equal(actual, alternate_control)}"
        )


@pytest.mark.parametrize(
    "z,y,x",
    [(1, 10, 8), (1, 10, 10), (2, 10, 8), (2, 10, 10)],
    ids=["single-rectangular", "single-square", "multi-rectangular", "original-square"],
)
def test_bead_numeric_lists_match_identical_arrays(z: int, y: int, x: int) -> None:
    from simrecon import prepare_bead_otf
    from test_c_acquisition_transfer import bead_options, bead_raw

    raw = bead_raw(y, x, z)
    nested = raw.tolist()
    np.testing.assert_array_equal(np.asarray(nested), raw)
    settings = bead_options()

    original = prepare_bead_otf(raw, **settings).transfer.samples
    assert original.dtype == np.complex128
    assert original.shape == (2, x // 2 + 1, z)
    assert np.isfinite(original).all()
    decoded = prepare_bead_otf(nested, **settings).transfer.samples
    assert decoded.dtype == np.complex128
    np.testing.assert_array_equal(decoded, original)


class SplitIndexArray(np.ndarray):
    """Genuine storage whose indexing can expose a different genuine array."""

    indexed_values: np.ndarray

    def __getitem__(self, key: Any) -> Any:
        """Return the selected indexed values, falling back to genuine storage."""
        values = getattr(self, "indexed_values", None)
        if values is None:
            return super().__getitem__(key)
        return values[key]


@pytest.mark.parametrize(
    "entry",
    ["prepare_acquisition_bands", "reinterpret_2d_planes"],
    ids=["prepare", "regroup"],
)
@pytest.mark.parametrize("field", ["images", "off_exposures"], ids=["on", "off"])
def test_raw_array_indexing_preserves_checked_values(entry: str, field: str) -> None:
    import re

    from simrecon import AcquisitionModeError, prepare_acquisition_bands, reinterpret_2d_planes

    images = np.ones((1, 1, 3, 1, 2, 4), dtype=np.float64)
    off = np.ones((*images.shape[:4], 1, *images.shape[4:]), dtype=np.float64)
    inputs = {"images": images, "off_exposures": off}
    legal = inputs[field]
    inexact = legal.copy()
    sample = 1 + 2**-30
    inexact.flat[0] = sample
    assert float(inexact.flat[0]) == sample and float(np.float32(sample)) == 1.0

    split = legal.view(SplitIndexArray)
    split.indexed_values = inexact
    np.testing.assert_array_equal(np.asarray(split), legal)
    assert float(np.asarray(split).flat[0]) == 1.0
    assert float(split[0, 0, :, 0].flat[0]) == sample

    prepare = entry == "prepare_acquisition_bands"
    output_field = (
        {"images": "quadratures", "off_exposures": "off_quadratures"}[field] if prepare else field
    )

    def observe(candidate: np.ndarray) -> np.ndarray:
        selected = inputs | {field: candidate}
        on, off = selected["images"], selected["off_exposures"]
        if prepare:
            result = prepare_acquisition_bands(on, off_exposures=off, **options())
        else:
            result = reinterpret_2d_planes(on, off_exposures=off, storage_order="direction-major")
        observed = getattr(result, output_field)
        assert isinstance(observed, np.ndarray) and observed.size and np.isfinite(observed).all()
        return observed

    checked = observe(legal)
    if not prepare:
        np.testing.assert_array_equal(checked, legal)
    np.testing.assert_array_equal(observe(legal.view(ConsistentArray)), checked)

    reason = _RAW_IMAGE_SUBJECT if field == "images" else _OFF_SAMPLE_SUBJECT
    with pytest.raises(AcquisitionModeError, match=rf"(?i){reason}") as caught:
        observe(inexact)
    assert caught.type is AcquisitionModeError

    try:
        actual = observe(split)
    except AcquisitionModeError as rejected:
        assert type(rejected) is AcquisitionModeError
        assert re.search(reason, str(rejected), re.IGNORECASE), str(rejected)
    else:
        assert np.array_equal(actual, checked), (
            f"{entry} used substituted {field}: checked first output {checked.flat[0]!r}, "
            f"actual {actual.flat[0]!r}; substituted input {sample!r}"
        )


def test_transfer_sample_indexing_preserves_checked_values(
    acquisition_record_consumer: tuple[Any, type[ValueError]],
) -> None:
    from dataclasses import replace

    from simrecon import ParameterEstimationError, prepare_acquisition_bands

    consume, error = acquisition_record_consumer
    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    table = transfer(complex_values=True)
    original = table.samples
    assert original.dtype == np.complex128
    alternate = original.copy()
    alternate[1:] *= 2
    alternate.flags.writeable = False

    stable = ConsistentArray(original.shape, dtype=np.complex128)
    split = SplitIndexArray(original.shape, dtype=np.complex128)
    for samples in (stable, split):
        np.copyto(samples, original)
        samples.flags.writeable = False
        assert samples.dtype == np.complex128 and samples.flags.owndata
        assert not samples.flags.writeable
        np.testing.assert_array_equal(np.asarray(samples), original)
    split.indexed_values = alternate
    np.testing.assert_array_equal(split[1:], alternate[1:])
    assert not np.array_equal(split[1:], original[1:])

    def observe(samples: np.ndarray) -> np.ndarray:
        result = consume(bands, replace(table, samples=samples))
        assert_public_control(result, error)
        return result.modulation if error is ParameterEstimationError else result.image

    checked = observe(original)
    np.testing.assert_array_equal(observe(stable), checked)
    alternate_result = observe(alternate)
    assert not np.array_equal(alternate_result, checked), "Doubled samples must affect the result"

    invalid = original.copy()
    invalid[1, 0, 0] = complex(np.inf)
    invalid.flags.writeable = False
    with pytest.raises(error) as caught:
        observe(invalid)
    assert caught.type is error
    assert has_used_array_reason("samples", str(caught.value)), str(caught.value)

    try:
        actual = observe(split)
    except error as rejected:
        assert type(rejected) is error
        assert has_used_array_reason("samples", str(rejected)), str(rejected)
    else:
        assert np.array_equal(actual, checked), (
            "Result differs from the checked transfer samples; "
            f"matches the genuine doubled table: {np.array_equal(actual, alternate_result)}"
        )


def test_masked_negative_noise_fails_used_field_validation(
    acquisition_record_consumer: tuple[Any, type[ValueError]],
) -> None:
    from dataclasses import replace

    from simrecon import ParameterEstimationError, prepare_acquisition_bands

    consume, error = acquisition_record_consumer
    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    table = transfer()
    positive = np.ones((1, 1, 2), dtype=np.float64)
    negative = positive.copy()
    negative[0, 0, 1] = -1e6
    masked_negative = np.ma.array(negative, mask=[[[False, True]]])
    np.testing.assert_array_equal(np.asarray(masked_negative), negative)
    np.testing.assert_array_equal(np.ma.getmaskarray(masked_negative), [[[False, True]]])
    positive_unmasked = np.ma.array(positive, mask=False)

    def observe(noise: np.ndarray) -> np.ndarray:
        result = consume(replace(bands, noise_variance_factors=noise), table)
        assert_public_control(result, error)
        return result.modulation if error is ParameterEstimationError else result.image

    checked = observe(positive)
    np.testing.assert_array_equal(observe(positive_unmasked), checked)
    if error is not ParameterEstimationError:
        alternate = positive.copy()
        alternate[0, 0, 1] = 2.0
        assert not np.array_equal(observe(alternate), checked), "Side-order noise must affect image"

    reason = r"(?i)\bnoise(?:_variance_factors)?\b"
    with pytest.raises(error, match=reason) as caught:
        observe(negative)
    assert caught.type is error

    with pytest.raises(error, match=reason) as caught:
        actual = observe(masked_negative)
        pytest.fail(
            "Masked negative backing noise was accepted; "
            f"result equals the positive control: {np.array_equal(actual, checked)}"
        )
    assert caught.type is error


def test_superseded_phase_list_rejects_masked_nonfinite_value() -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands

    images = np.ones((1, 1, 3, 1, 2, 4), dtype=np.float64)
    settings = options(phase_steps_rad=np.array([2.0]))
    legal = np.zeros((1, 3), dtype=np.float64)
    unmasked = np.ma.array(legal, mask=False)
    invalid = legal.copy()
    invalid[0, 1] = np.nan
    mask = [[False, True, False]]
    masked = np.ma.array(invalid, mask=mask)
    np.testing.assert_array_equal(np.asarray(masked), invalid)
    np.testing.assert_array_equal(np.ma.getmaskarray(masked), mask)
    assert np.isnan(np.ma.getdata(masked)[0, 1]) and np.ma.is_masked(masked[0, 1])

    for phases in (legal, unmasked):
        result = prepare_acquisition_bands(images, phases_rad=phases, **settings)
        assert result.phase_policies == ((("steps",),),)
        np.testing.assert_array_equal(result.phase_angles_rad, [[[[0.0, 2.0, 4.0]]]])

    reason = (
        r"(?i)\b(?:phases[ _-]+rad|phase[ _-]+list|"
        r"(?:explicit|supplied)[ _-]+(?:phases|phase[ _-]+(?:angles|array)))\b"
    )
    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        prepare_acquisition_bands(images, phases_rad=invalid, **settings)
    assert caught.type is AcquisitionModeError

    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        result = prepare_acquisition_bands(images, phases_rad=masked, **settings)
        pytest.fail(f"Masked nonfinite phases_rad accepted with policy {result.phase_policies!r}")
    assert caught.type is AcquisitionModeError


def test_regrouped_exposure_background_rejects_masked_out_of_magnitude_value() -> None:
    from simrecon import AcquisitionModeError, reinterpret_2d_planes

    images = np.ones((1, 1, 3, 1, 2, 4), dtype=np.float64)
    legal = np.ones((1, 1, 3, 1), dtype=np.float64)
    unmasked = np.ma.array(legal, mask=False)
    invalid = legal.copy()
    selected = (0, 0, 1, 0)
    invalid[selected] = float(2**128)
    mask = np.zeros(legal.shape, dtype=bool)
    mask[selected] = True
    masked = np.ma.array(invalid, mask=mask)
    np.testing.assert_array_equal(np.asarray(masked), invalid)
    np.testing.assert_array_equal(np.ma.getmaskarray(masked), mask)
    actual = np.ma.getdata(masked)[selected]
    assert actual == float(2**128) and actual > float(np.finfo(np.float32).max)
    assert np.ma.is_masked(masked[selected])

    for background in (legal, unmasked):
        result = reinterpret_2d_planes(
            images, storage_order="z-major", exposure_background=background
        )
        np.testing.assert_array_equal(result.exposure_background, legal)

    reason = r"(?i)\b(?:exposure|(?:per[ _-]+)?frame|per[ _-]+exposure)[ _-]+backgrounds?\b"
    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        reinterpret_2d_planes(images, storage_order="z-major", exposure_background=invalid)
    assert caught.type is AcquisitionModeError

    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        result = reinterpret_2d_planes(images, storage_order="z-major", exposure_background=masked)
        pytest.fail(
            f"Masked out-of-magnitude exposure_background accepted: {result.exposure_background!r}"
        )
    assert caught.type is AcquisitionModeError


def test_lateral_pitch_checks_magnitude_of_actual_float_value() -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands

    class Pitch(float):
        """A genuine float whose magnitude operation reports one micrometre."""

        def __abs__(self) -> float:
            return 1.0

    images = np.ones((1, 1, 3, 1, 2, 4), dtype=np.float64)
    legal = 1.0
    stable = Pitch(legal)
    invalid = 1e100
    out_of_range = Pitch(invalid)
    assert float(stable) == abs(stable) == legal
    assert float.__float__(out_of_range) == float(out_of_range) == invalid
    assert np.isfinite(invalid) and invalid > float(np.finfo(np.float32).max)
    assert abs(out_of_range) == legal

    for pitch in (legal, stable):
        result = prepare_acquisition_bands(images, **options(dxy_um=pitch))
        assert result.dxy_um == legal

    reason = r"(?i)\b(?:dxy(?:[ _-]+um)?|lateral[ _-]+(?:pixel[ _-]+)?(?:pitch|sampling|spacing))\b"
    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        prepare_acquisition_bands(images, **options(dxy_um=invalid))
    assert caught.type is AcquisitionModeError

    with pytest.raises(AcquisitionModeError, match=reason) as caught:
        result = prepare_acquisition_bands(images, **options(dxy_um=out_of_range))
        pytest.fail(f"Out-of-magnitude lateral pitch published as dxy_um={result.dxy_um!r}")
    assert caught.type is AcquisitionModeError


def test_off_combination_validates_signed_selector_backing() -> None:
    from collections.abc import Iterator

    from simrecon import AcquisitionModeError, prepare_acquisition_bands

    class SkipOrderIteration(np.ndarray):
        """Iteration presents two skipped orders regardless of the stored selectors."""

        def __iter__(self) -> Iterator[Any]:
            return iter((0, 0))

    images = raw_pattern(y=2, x=4)
    settings = options()
    legal = np.array([0, 0], dtype=np.int32)
    positive = np.array([1, 0], dtype=np.int32)
    inconsistent = positive.view(SkipOrderIteration)
    np.testing.assert_array_equal(np.asarray(inconsistent), [1, 0])
    assert inconsistent.dtype == np.int32 and inconsistent.shape == (2,)
    assert tuple(inconsistent) == (0, 0)

    plain = prepare_acquisition_bands(images, combine_off_orders=legal, **settings)
    stable = prepare_acquisition_bands(
        images, combine_off_orders=legal.view(ConsistentArray), **settings
    )
    assert plain.off_quadratures is None and stable.off_quadratures is None
    assert plain.quadratures.size and np.isfinite(plain.quadratures).all()
    np.testing.assert_array_equal(stable.quadratures, plain.quadratures)

    with pytest.raises(AcquisitionModeError) as caught:
        prepare_acquisition_bands(images, combine_off_orders=positive, **settings)
    assert caught.type is AcquisitionModeError

    with pytest.raises(AcquisitionModeError) as caught:
        prepare_acquisition_bands(images, combine_off_orders=inconsistent, **settings)
        pytest.fail("Positive backing combine_off_orders accepted without off exposures")
    assert caught.type is AcquisitionModeError


@pytest.mark.parametrize(
    "acquisition_record_consumer,field",
    [
        ("estimate", "dkr_cyc_um"),
        ("estimate", "dkz_cyc_um"),
        ("reconstruct", "dkr_cyc_um"),
    ],
    indirect=["acquisition_record_consumer"],
    ids=["estimate-lateral", "estimate-axial", "reconstruct-lateral"],
)
def test_acquisition_consumers_use_checked_transfer_increment(
    acquisition_record_consumer: tuple[Any, type[ValueError]], field: str
) -> None:
    from dataclasses import replace

    from simrecon import ParameterEstimationError, prepare_acquisition_bands

    class Increment(float):
        """A float with a consistent reflected division by default."""

        division_scale = 1

        def __rtruediv__(self, numerator: float) -> float:
            return numerator / (float(self) * self.division_scale)

    class DoubledDivision(Increment):
        """Reflected division behaves as if the declared increment were doubled."""

        division_scale = 2

    consume, error = acquisition_record_consumer
    axial = field == "dkz_cyc_um"
    z = 3 if axial else 1
    bands = prepare_acquisition_bands(
        raw_pattern(z=z, y=2, x=4), **options(acquisition_mode="3d" if axial else "2d")
    )
    table = transfer(k=z, complex_values=True)
    increment = getattr(table, field)
    doubled = 2 * increment
    stable = Increment(increment)
    inconsistent = DoubledDivision(increment)
    assert np.isfinite(increment) and 0 < increment < doubled
    assert float(stable) == float.__float__(inconsistent) == float(inconsistent) == increment
    assert 1.0 / stable == 1.0 / increment
    assert 1.0 / inconsistent == 1.0 / doubled != 1.0 / increment

    def observe(candidate: Any) -> np.ndarray:
        result = consume(bands, candidate)
        assert_public_control(result, error)
        return result.modulation if error is ParameterEstimationError else result.image

    legal = observe(table)
    np.testing.assert_array_equal(observe(replace(table, **{field: stable})), legal)
    alternate = observe(replace(table, **{field: doubled}))
    assert alternate.shape == legal.shape
    assert not np.array_equal(alternate, legal), f"Doubled {field} must affect the result"

    try:
        actual = observe(replace(table, **{field: inconsistent}))
    except error as rejected:
        assert type(rejected) is error
    else:
        assert np.array_equal(actual, legal), (
            f"Result differs from the checked {field}; "
            f"matches doubled ordinary increment: {np.array_equal(actual, alternate)}"
        )


@pytest.mark.parametrize(
    "acquisition_record_consumer",
    ["estimate", "reconstruct"],
    indirect=True,
)
def test_acquisition_consumers_validate_transfer_layout_text(
    acquisition_record_consumer: tuple[Any, type[ValueError]],
) -> None:
    from dataclasses import replace

    from simrecon import ParameterEstimationError, prepare_acquisition_bands

    consume, error = acquisition_record_consumer
    bands = prepare_acquisition_bands(raw_pattern(y=2, x=4), **options())
    table = transfer(complex_values=True)
    stable = MutableSelector("radial")
    inconsistent = EqualToSelector("full")
    inconsistent.claimed_literal = "radial"
    assert table.layout == str(stable) == "radial" and table.samples.ndim == 3
    assert str.__str__(inconsistent) == "full" and inconsistent == "radial"

    def observe(candidate: Any) -> np.ndarray:
        result = consume(bands, candidate)
        assert_public_control(result, error)
        return result.modulation if error is ParameterEstimationError else result.image

    np.testing.assert_array_equal(observe(replace(table, layout=stable)), observe(table))

    with pytest.raises(error) as caught:
        consume(bands, replace(table, layout="full"))
    assert caught.type is error

    with pytest.raises(error) as caught:
        consume(bands, replace(table, layout=inconsistent))
        pytest.fail("Rank-three radial samples accepted with underlying transfer layout 'full'")
    assert caught.type is error


def test_known_acquisition_requires_enough_transfer_orders_without_filter_visits() -> None:
    from dataclasses import replace

    from simrecon import ReconstructionError, prepare_acquisition_bands, reconstruct_known

    class StableOrderCount(int):
        """An integer subclass with ordinary comparison."""

    class HiddenShortage(int):
        """A genuine integer whose less-than comparison conceals the shortage."""

        def __lt__(self, other: int) -> bool:
            return False

    bands = prepare_acquisition_bands(raw_pattern(y=1, x=4), **options())
    settings = known_options(carriers_cyc_um=np.array([[0.1, 0.02]]), modulation=np.ones((1, 1)))
    sufficient = transfer()
    insufficient = transfer(orders=1)
    inconsistent = HiddenShortage(insufficient.norders)
    assert bands.input_shape[-2] == 1 and bands.quadratures.shape[2] == 3
    assert sufficient.norders == sufficient.samples.shape[0] == 2
    assert int(inconsistent) == insufficient.norders == insufficient.samples.shape[0] == 1
    assert int(inconsistent) < sufficient.norders and (inconsistent < sufficient.norders) is False

    legal = reconstruct_known(bands, sufficient, **settings)
    stable = reconstruct_known(bands, replace(sufficient, norders=StableOrderCount(2)), **settings)
    assert_public_control(legal, ReconstructionError)
    assert_public_control(stable, ReconstructionError)
    np.testing.assert_array_equal(stable.image, legal.image)

    with pytest.raises(ReconstructionError) as caught:
        reconstruct_known(bands, insufficient, **settings)
    assert caught.type is ReconstructionError

    with pytest.raises(ReconstructionError) as caught:
        reconstruct_known(bands, replace(insufficient, norders=inconsistent), **settings)
        pytest.fail("One-order transfer accepted for a two-order one-row acquisition")
    assert caught.type is ReconstructionError


def public_declaration_inputs() -> tuple[Any, Any, np.ndarray, dict[str, Any]]:
    """Build the shared two-dimensional inputs of the paired public observer."""
    from simrecon import prepare_acquisition_bands

    bands = prepare_acquisition_bands(raw_pattern(y=4, x=6), **options())
    table = transfer(complex_values=True)
    carriers = np.array([[0.1, 0.02]])
    known = known_options(carriers_cyc_um=carriers, modulation=np.ones((1, 1)))
    return bands, table, carriers, known


@pytest.mark.parametrize("entry", ["estimate_parameters", "reconstruct_known"])
@pytest.mark.parametrize("field", ["dkr_cyc_um", "norders"])
def test_public_transfer_scalar_declarations(entry: str, field: str) -> None:
    from dataclasses import replace

    from simrecon import (
        ParameterEstimationError,
        ReconstructionError,
        estimate_parameters,
        reconstruct_known,
    )

    class StableFloat(float):
        """A genuine float subclass with ordinary behavior."""

    class StableInt(int):
        """A genuine integer subclass with ordinary behavior."""

    class AdvertisedFloat:
        def __init__(self, value: float) -> None:
            self.value = value

        @property
        def __class__(self) -> type[float]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return float

        def __abs__(self) -> float:
            return abs(self.value)

        def __float__(self) -> float:
            return float(self.value)

    class AdvertisedInt:
        def __init__(self, value: int) -> None:
            self.value = value

        @property
        def __class__(self) -> type[int]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return int

        def __int__(self) -> int:
            return int(self.value)

    bands, table, carriers, known = public_declaration_inputs()
    assert type(bands) is api("AcquisitionBands")
    assert type(table) is api("OpticalTransfer")
    if entry == "estimate_parameters":
        consume = estimate_parameters
        settings = optics()
        settings.update(initial_carriers_cyc_um=carriers, search_carriers=False)
        output = "modulation"
        error = ParameterEstimationError
    else:
        consume = reconstruct_known
        settings = known
        output = "image"
        error = ReconstructionError

    if field == "dkr_cyc_um":
        value = table.dkr_cyc_um
        assert type(value) is float and np.isfinite(value) and value > 0
        stable = StableFloat(value)
        advertised = AdvertisedFloat(value)
        assert abs(advertised) == float(advertised) == float(stable) == value
    else:
        value = table.norders
        assert type(value) is int and value == table.samples.shape[0] == 2
        stable = StableInt(value)
        advertised = AdvertisedInt(value)
        assert int(advertised) == int(stable) == value
    assert issubclass(type(stable), type(value))
    assert not issubclass(type(advertised), type(value))
    assert isinstance(advertised, type(value))

    legal = consume(bands, table, **settings)
    stable_result = consume(bands, replace(table, **{field: stable}), **settings)
    assert_public_control(legal, error)
    assert_public_control(stable_result, error)
    assert np.array_equal(getattr(stable_result, output), getattr(legal, output))

    with pytest.raises(error) as caught:
        consume(bands, replace(table, **{field: advertised}), **settings)
        pytest.fail(f"{entry} accepted a foreign object advertising the type of {field}")
    assert caught.type is error


@pytest.mark.parametrize("field", ["power_taper_exponent", "wiener_increment", "explode_factor"])
def test_public_known_option_checks_converted_magnitude(field: str) -> None:
    from simrecon import ReconstructionError, reconstruct_known

    class StableFloat(float):
        """A genuine float subclass with ordinary behavior."""

    class WideConversion(float):
        def __float__(self) -> float:
            return 2.0**128

    bands, table, _, known = public_declaration_inputs()
    if field == "power_taper_exponent":
        known["output_taper"] = "power"

    def reconstruct(value: float) -> Any:
        settings = known.copy()
        settings[field] = value
        return reconstruct_known(bands, table, **settings)

    invalid = 2.0**128
    inconsistent = WideConversion(1.0)
    assert float(np.finfo(np.float32).max) == invalid - 2.0**104 < invalid
    assert float.__float__(inconsistent) == abs(inconsistent) == 1.0
    assert float(inconsistent) == invalid

    legal = reconstruct(1.0)
    stable = reconstruct(StableFloat(1.0))
    assert_public_control(legal, ReconstructionError)
    assert_public_control(stable, ReconstructionError)
    assert dict(legal.resolved_settings)[field] == dict(stable.resolved_settings)[field] == 1.0
    assert np.array_equal(stable.image, legal.image)

    with pytest.raises(ReconstructionError) as invalid_control:
        reconstruct(invalid)
    assert invalid_control.type is ReconstructionError

    with pytest.raises(ReconstructionError) as caught:
        result = reconstruct(inconsistent)
        pytest.fail(
            f"{field} accepted a conversion outside float32 magnitude and reported "
            f"{dict(result.resolved_settings)[field]!r}"
        )
    assert caught.type is ReconstructionError


def test_public_known_overlap_flag_requires_actual_boolean() -> None:
    from simrecon import ReconstructionError, reconstruct_known

    class AdvertisedBoolean:
        @property
        def __class__(self) -> type[bool]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return bool

        def __bool__(self) -> bool:
            return False

    bands, table, _, known = public_declaration_inputs()

    def reconstruct(value: Any) -> Any:
        return reconstruct_known(bands, table, **(known | {"filter_overlaps": value}))

    legal, alternate = reconstruct(True), reconstruct(False)
    stable = reconstruct(np.bool_(True))
    for result, flag in ((legal, True), (alternate, False), (stable, True)):
        assert_public_control(result, ReconstructionError)
        assert dict(result.resolved_settings)["filter_overlaps"] == flag
    assert np.array_equal(stable.image, legal.image)
    assert legal.image.shape == alternate.image.shape
    assert not np.array_equal(legal.image, alternate.image)

    advertised = AdvertisedBoolean()
    assert isinstance(advertised, bool) and type(advertised) is not bool
    assert bool(advertised) is False
    with pytest.raises(ReconstructionError) as caught:
        reconstruct(advertised)
        pytest.fail("filter_overlaps accepted a non-Boolean object advertising bool")
    assert caught.type is ReconstructionError


def test_public_preparation_reports_applied_background() -> None:
    from simrecon import AcquisitionModeError, prepare_acquisition_bands

    class StableFloat(float):
        """A genuine float subclass with ordinary behavior."""

    class ChangingBackground(float):
        reads = 0

        def __float__(self) -> float:
            self.reads += 1
            return 1.0 if self.reads == 1 else 2.0

    raw = raw_pattern(y=4, x=6)

    def prepare(value: float) -> Any:
        return prepare_acquisition_bands(raw, **options(background=value))

    one, two = prepare(1.0), prepare(2.0)
    stable = prepare(StableFloat(1.0))
    for result, background in ((one, 1.0), (two, 2.0), (stable, 1.0)):
        assert result.quadratures.size and np.isfinite(result.quadratures).all()
        assert dict(result.resolved_settings)["background"] == background
        assert result.background_after.shape == (4, 6)
        assert np.all(result.background_after == background)
    assert np.array_equal(stable.quadratures, one.quadratures)
    assert one.quadratures.shape == two.quadratures.shape
    assert not np.array_equal(one.quadratures, two.quadratures)

    witness = ChangingBackground(1.0)
    try:
        result = prepare(witness)
    except AcquisitionModeError as rejected:
        assert type(rejected) is AcquisitionModeError
    else:
        reported = dict(result.resolved_settings)["background"]
        assert reported in (1.0, 2.0), f"Unexpected resolved background: {reported!r}"
        expected = one if reported == 1.0 else two
        camera_matches = np.array_equal(result.background_after, expected.background_after)
        quadratures_match = np.array_equal(result.quadratures, expected.quadratures)
        assert camera_matches and quadratures_match, (
            f"Reported background {reported!r} counts disagrees with the legal control: "
            f"camera map matches={camera_matches}, quadratures match={quadratures_match}"
        )


def adjacent_acquisition_consumer(
    entry: str,
) -> tuple[Any, Any, np.ndarray, type[ValueError], str]:
    """Bind the adjacent observer's public consumer and its unchanged options."""
    from simrecon import (
        ParameterEstimationError,
        ReconstructionError,
        estimate_parameters,
        reconstruct_known,
    )

    bands, table, carriers, known = public_declaration_inputs()
    assert type(bands) is api("AcquisitionBands")
    assert type(table) is api("OpticalTransfer")
    if entry == "estimate_parameters":
        settings = optics()
        settings.update(initial_carriers_cyc_um=carriers, search_carriers=False)

        def consume(candidate: Any, **changes: Any) -> Any:
            return estimate_parameters(bands, candidate, **(settings | changes))

        return consume, table, carriers, ParameterEstimationError, "modulation"

    def reconstruct(candidate: Any, **changes: Any) -> Any:
        return reconstruct_known(bands, candidate, **(known | changes))

    return reconstruct, table, carriers, ReconstructionError, "image"


def assert_adjacent_checked_input(
    call: Any,
    *,
    field: str,
    legal: Any,
    stable: Any,
    invalid: Any,
    inconsistent: Any,
    error: type[ValueError],
    output: str,
    check_reported: bool = False,
) -> None:
    """Compare genuine controls and require the exact public class for both rejections."""
    ordinary_result, stable_result = call(legal), call(stable)
    ordinary_output = getattr(ordinary_result, output)
    stable_output = getattr(stable_result, output)
    for values in (ordinary_output, stable_output):
        assert isinstance(values, np.ndarray) and values.size and np.isfinite(values).all()
    assert np.array_equal(stable_output, ordinary_output)
    if check_reported:
        assert dict(ordinary_result.resolved_settings)[field] == legal
        assert dict(stable_result.resolved_settings)[field] == legal

    with pytest.raises(error) as invalid_control:
        call(invalid)
    assert invalid_control.type is error

    with pytest.raises(error) as caught:
        result = call(inconsistent)
        detail = (
            f" and reported {dict(result.resolved_settings)[field]!r}" if check_reported else ""
        )
        pytest.fail(f"Public call accepted inconsistent {field}{detail}")
    assert caught.type is error


@pytest.mark.parametrize(
    "entry,field",
    [
        ("estimate_parameters", "source_revision"),
        ("estimate_parameters", "reference_sha256"),
        ("reconstruct_known", "source_revision"),
        ("reconstruct_known", "reference_sha256"),
    ],
)
def test_adjacent_transfer_requires_genuine_provenance(entry: str, field: str) -> None:
    from dataclasses import replace

    class StableStr(str):
        """A genuine string subclass with ordinary comparison."""

    class StableTuple(tuple):
        """A genuine tuple subclass with ordinary comparison."""

    class SameIdentity:
        def __ne__(self, other: object) -> bool:
            return False

    consume, table, _, error, output = adjacent_acquisition_consumer(entry)
    legal = getattr(table, field)
    if field == "source_revision":
        assert type(legal) is str
        stable, invalid = StableStr(legal), "OTHER"
    else:
        assert type(legal) is tuple
        stable, invalid = StableTuple(legal), ()
    inconsistent = SameIdentity()
    assert stable == legal and invalid != legal
    assert not issubclass(type(inconsistent), type(legal))
    assert (inconsistent != legal) is False

    assert_adjacent_checked_input(
        lambda value: consume(replace(table, **{field: value})),
        field=field,
        legal=legal,
        stable=stable,
        invalid=invalid,
        inconsistent=inconsistent,
        error=error,
        output=output,
    )


@pytest.mark.parametrize("entry", ["estimate_parameters", "reconstruct_known"])
def test_adjacent_acquisition_requires_genuine_wavelength_integer(entry: str) -> None:
    class StableInt(int):
        """A genuine integer subclass with ordinary conversion."""

    class IntClaim:
        @property
        def __class__(self) -> type[int]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return int

        def __int__(self) -> int:
            return 520

    consume, table, _, error, output = adjacent_acquisition_consumer(entry)
    inconsistent = IntClaim()
    assert isinstance(inconsistent, int) and not issubclass(type(inconsistent), int)
    assert int(inconsistent) == 520

    assert_adjacent_checked_input(
        lambda value: consume(table, wavelength_nm=value),
        field="wavelength_nm",
        legal=520,
        stable=StableInt(520),
        invalid=1.5,
        inconsistent=inconsistent,
        error=error,
        output=output,
        check_reported=True,
    )


@pytest.mark.parametrize(
    "entry,field",
    [
        ("estimate_parameters", "initial_carriers_cyc_um"),
        ("reconstruct_known", "carriers_cyc_um"),
    ],
)
def test_adjacent_acquisition_requires_genuine_carrier_array(entry: str, field: str) -> None:
    class StableArray(np.ndarray):
        """A genuine NumPy array subclass with ordinary behavior."""

    class ArrayClaim:
        def __init__(self, value: np.ndarray) -> None:
            self.value = value

        @property
        def __class__(self) -> type[np.ndarray]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return np.ndarray

        def __getattr__(self, name: str) -> Any:
            return getattr(self.value, name)

        def __array__(self, dtype: Any = None, copy: bool | None = None) -> np.ndarray:
            return np.asarray(self.value, dtype=dtype, copy=copy)

    consume, table, carriers, error, output = adjacent_acquisition_consumer(entry)
    inconsistent = ArrayClaim(carriers)
    assert type(carriers) is np.ndarray
    assert isinstance(inconsistent, np.ndarray) and not issubclass(type(inconsistent), np.ndarray)
    assert np.array_equal(np.asarray(inconsistent), carriers)

    assert_adjacent_checked_input(
        lambda value: consume(table, **{field: value}),
        field=field,
        legal=carriers,
        stable=carriers.view(StableArray),
        invalid=carriers.tolist(),
        inconsistent=inconsistent,
        error=error,
        output=output,
    )


class AdjacentStableFloat(float):
    """A genuine float subclass with ordinary magnitude and conversion."""


class AdjacentWideFloat(float):
    """A genuine float whose magnitude operation hides its stored value."""

    def __abs__(self) -> float:
        """Report a small magnitude regardless of the stored value."""
        return 1.0


@pytest.mark.parametrize("field", ["wiener", "suppression_radius_bins"])
def test_adjacent_known_option_checks_actual_magnitude(field: str) -> None:
    consume, table, _, error, output = adjacent_acquisition_consumer("reconstruct_known")
    inconsistent = AdjacentWideFloat(1e40)
    assert abs(inconsistent) == 1.0
    assert float(inconsistent) == 1e40 > float(np.finfo(np.float32).max)

    assert_adjacent_checked_input(
        lambda value: consume(table, **{field: value}),
        field=field,
        legal=1.0,
        stable=AdjacentStableFloat(1.0),
        invalid=1e40,
        inconsistent=inconsistent,
        error=error,
        output=output,
        check_reported=True,
    )


def test_adjacent_known_precise_taper_requires_actual_boolean() -> None:
    class BooleanClaim:
        @property
        def __class__(self) -> type[bool]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return bool

        def __bool__(self) -> bool:
            return False

    consume, table, _, error, output = adjacent_acquisition_consumer("reconstruct_known")
    inconsistent = BooleanClaim()
    assert isinstance(inconsistent, bool) and not issubclass(type(inconsistent), bool)
    assert bool(inconsistent) is False

    assert_adjacent_checked_input(
        lambda value: consume(table, precise_taper=value),
        field="precise_taper",
        legal=False,
        stable=np.bool_(False),
        invalid=1,
        inconsistent=inconsistent,
        error=error,
        output=output,
        check_reported=True,
    )


def test_adjacent_rectangular_bead_checks_actual_pitch_magnitude() -> None:
    from simrecon import OtfError, prepare_bead_otf
    from test_c_acquisition_transfer import bead_options, bead_raw

    bead = bead_raw(10, 8, z=1)
    legal = bead_options()["dxy_um"]
    inconsistent = AdjacentWideFloat(1e40)
    assert bead.shape == (3, 1, 10, 8) and type(legal) is float and legal == 0.25
    assert abs(inconsistent) == 1.0
    assert float(inconsistent) == 1e40 > float(np.finfo(np.float32).max)

    assert_adjacent_checked_input(
        lambda value: prepare_bead_otf(bead, **bead_options(dxy_um=value)),
        field="dxy_um",
        legal=legal,
        stable=AdjacentStableFloat(legal),
        invalid=1e40,
        inconsistent=inconsistent,
        error=OtfError,
        output="quadratures",
        check_reported=True,
    )


class BeadAdvertisedFloat:
    """A foreign object advertising float and resolving to 1.0."""

    @property
    def __class__(self) -> type[float]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Advertise float while retaining the foreign runtime type."""
        return float

    def __abs__(self) -> float:
        """Report the magnitude of the advertised value."""
        return 1.0

    def __float__(self) -> float:
        """Convert to the legal scalar value."""
        return 1.0


class BeadAdvertisedInteger:
    """A foreign object advertising int and converting to a selected integer."""

    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def __class__(self) -> type[int]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Advertise int while retaining the foreign runtime type."""
        return int

    def __int__(self) -> int:
        """Convert to the selected legal integer."""
        return self.value


class BeadAdvertisedFalse:
    """A foreign object advertising bool and converting to false."""

    @property
    def __class__(self) -> type[bool]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Advertise bool while retaining the foreign runtime type."""
        return bool

    def __bool__(self) -> bool:
        """Convert to the legal disabled flag."""
        return False


class BeadStableInteger(int):
    """A genuine integer subclass with ordinary conversion."""


class BeadGenuineArrayLike:
    """Supply the supported public array protocol without claiming an array type."""

    def __init__(self, array: np.ndarray) -> None:
        self.array = array

    def __array__(self, dtype: Any = None, copy: bool | None = None) -> np.ndarray:
        """Return the backing array through the ordinary NumPy protocol."""
        if copy is True:
            return np.array(self.array, dtype=dtype, copy=True)
        return np.asarray(self.array, dtype=dtype)


@pytest.mark.parametrize(
    "shape,field,witness",
    [
        pytest.param((3, 1, 10, 8), "dxy_um", BeadAdvertisedFloat(), id="rectangular-Z1-dxy"),
        pytest.param(
            (3, 1, 10, 8),
            "background_counts",
            BeadAdvertisedFloat(),
            id="rectangular-Z1-background",
        ),
        pytest.param(
            (3, 1, 10, 8),
            "wavelength_nm",
            BeadAdvertisedInteger(500),
            id="rectangular-Z1-wavelength",
        ),
        pytest.param(
            (3, 1, 10, 8),
            "compensate_bead",
            BeadAdvertisedFalse(),
            id="rectangular-Z1-compensation",
        ),
        pytest.param(
            (3, 1, 10, 8), "fix_radial_from", BeadAdvertisedInteger(0), id="rectangular-Z1-radial"
        ),
        pytest.param(
            (3, 1, 10, 8),
            "cleanup_axial_bins",
            [BeadAdvertisedInteger(0), 0, 0],
            id="rectangular-Z1-cleanup",
        ),
        pytest.param(
            (3, 1, 10, 8),
            "origin_fit_bins",
            [BeadAdvertisedInteger(1), 2],
            id="rectangular-Z1-origin",
        ),
        pytest.param((3, 1, 10, 10), "dxy_um", BeadAdvertisedFloat(), id="square-Z1-dxy"),
        pytest.param((3, 2, 10, 8), "dxy_um", BeadAdvertisedFloat(), id="rectangular-Z2-dxy"),
    ],
)
def test_added_bead_requires_genuine_declaration(
    shape: tuple[int, int, int, int], field: str, witness: Any
) -> None:
    from simrecon import OtfError, prepare_bead_otf

    p, z, y, x = shape
    raw = np.zeros(shape, dtype=np.float64)
    for phase in range(p):
        raw[phase, z - 1, y // 2, x // 2] = phase + 1

    defaults: dict[str, Any] = dict(
        dxy_um=1.0,
        dz_um=1.0,
        linespacing_um=1.0,
        wavelength_nm=500,
        background_counts=0.0,
        compensate_bead=False,
        fix_axial_axis=False,
        fix_radial_from=0,
        cleanup_axial_bins=(0, 0, 0),
        numerical_aperture=1.0,
        immersion_index=1.0,
        origin_fit_bins=None,
        rescale_each=False,
        forced_pi_shift=False,
    )

    def prepare(raw_input: Any, **changes: Any) -> Any:
        return prepare_bead_otf(raw_input, **(defaults | changes))

    def check_same_transfer(result: Any, control: Any) -> None:
        samples = result.transfer.samples
        assert samples.size and np.isfinite(samples).all()
        assert np.array_equal(samples, control.transfer.samples)
        assert np.array_equal(result.center_pixels_xyz, control.center_pixels_xyz)
        assert result.transfer.dkr_cyc_um == control.transfer.dkr_cyc_um
        assert result.transfer.dkz_cyc_um == control.transfer.dkz_cyc_um

    ordinary = prepare(raw)
    check_same_transfer(prepare(raw.tolist()), ordinary)
    check_same_transfer(prepare(BeadGenuineArrayLike(raw)), ordinary)

    # The stable control enables origin fitting. Compare against the same values in plain lists.
    plain_lists = prepare(raw, cleanup_axial_bins=[0, 0, 0], origin_fit_bins=[1, 2])
    stable = prepare(
        raw,
        dxy_um=AdjacentStableFloat(1.0),
        background_counts=np.float64(0.0),
        wavelength_nm=BeadStableInteger(500),
        compensate_bead=np.bool_(False),
        fix_radial_from=np.int64(0),
        cleanup_axial_bins=[np.int32(0), BeadStableInteger(0), 0],
        origin_fit_bins=[np.int64(1), BeadStableInteger(2)],
    )
    check_same_transfer(stable, plain_lists)

    wide = AdjacentWideFloat(1e40)
    assert abs(wide) == 1.0 and float(wide) > float(np.finfo(np.float32).max)
    with pytest.raises(OtfError) as invalid_control:
        prepare(raw, dxy_um=wide)
    assert invalid_control.type is OtfError

    candidate = witness[0] if isinstance(witness, list) else witness
    advertised = candidate.__class__
    assert advertised in (float, int, bool)
    assert isinstance(candidate, advertised) and not issubclass(type(candidate), advertised)
    with pytest.raises(OtfError) as caught:
        prepare(raw, **{field: witness})
        pytest.fail(f"Added bead geometry {shape} accepted a false-class declaration for {field}")
    assert caught.type is OtfError
