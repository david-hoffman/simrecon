"""CE03 public validation, paired permitted inputs, and operation failures.

No production internals, retained C, backend hooks, skips or fabricated results.
"""

from copy import copy
from math import isqrt
from typing import Any

import numpy as np
import pytest

import simrecon as sr


def api(name: str) -> Any:
    assert hasattr(sr, name), f"approved public CE03 entry missing: {name}"
    return getattr(sr, name)


def raw_bead() -> Any:
    raw = np.zeros((5, 5, 24, 24), dtype=np.float64)
    raw[:, 1, 11, 11] = [12, 20, 10, 6, 8]
    raw[:, 2, 12, 12] = [4, 6, 8, 10, 2]
    return raw


def options(**changes: Any) -> dict[str, Any]:
    result = {
        "dxy_um": 0.25,
        "dz_um": 0.5,
        "linespacing_um": 0.75,
        "wavelength_nm": 520,
        "compensate_bead": False,
        "fix_axial_axis": False,
        "background_counts": 0,
    }
    result.update(changes)
    return result


def reject_prepare(raw: Any, **changes: Any) -> None:
    error = api("OtfError")
    assert issubclass(error, ValueError)
    with pytest.raises(error, match=".+"):
        api("prepare_bead_otf")(raw, **options(**changes))


@pytest.mark.parametrize(
    "kind",
    [
        "bool",
        "object",
        "string",
        "complex",
        "nan",
        "inf",
        "float32_inexact",
        "magnitude",
        "ndim",
        "n8",
        "p0",
        "p11",
        "empty",
    ],
)
def test_invalid_raw_numeric_representation_and_shape(kind: str) -> None:
    raw = raw_bead()
    if kind in {"bool", "object", "string", "complex"}:
        raw = raw.astype({"bool": bool, "object": object, "string": str, "complex": complex}[kind])
    elif kind in {"nan", "inf", "float32_inexact", "magnitude"}:
        raw.flat[0] = {
            "nan": np.nan,
            "inf": np.inf,
            "float32_inexact": 1 + 2**-30,
            "magnitude": 1e100,
        }[kind]
    elif kind == "ndim":
        raw = raw[0]
    else:
        shape = {
            "n8": (5, 5, 8, 8),
            "p0": (0, 5, 24, 24),
            "p11": (11, 5, 24, 24),
            "empty": (5, 0, 24, 24),
        }[kind]
        raw = np.ones(shape)
    reject_prepare(raw)


@pytest.mark.parametrize(
    "shape,branch",
    [((5, 5, 23, 23), "odd"), ((4, 5, 24, 24), "phase")],
)
def test_unsupported_dimensions_name_branch(shape: tuple[int, ...], branch: str) -> None:
    with pytest.raises(api("OtfError"), match=".+") as caught:
        api("prepare_bead_otf")(np.ones(shape), **options())
    text = str(caught.value).lower()
    assert any(
        word in text
        for word in {
            "odd": ("odd", "even"),
            "phase": ("phase", "odd"),
        }[branch]
    )


def test_single_phase_compensation_unsupported_and_off_permitted() -> None:
    raw = raw_bead()[:1]
    reject_prepare(raw, compensate_bead=True)
    actual = api("prepare_bead_otf")(raw, **options())
    assert actual.transfer.norders == 1 and actual.quadrature_angles_rad.shape == (0,)


@pytest.mark.parametrize(
    "name", ["dxy_um", "dz_um", "linespacing_um", "numerical_aperture", "immersion_index"]
)
@pytest.mark.parametrize("bad", [0, -1, np.inf, np.nan, True, "1", 1e100])
def test_invalid_positive_physical_scalars(name: str, bad: Any) -> None:
    reject_prepare(raw_bead(), **{name: bad})


@pytest.mark.parametrize("bad", [0, -1, 520.5, True, "520", np.inf, 2**31])
def test_wavelength_is_explicit_positive_signed32_integer(bad: Any) -> None:
    reject_prepare(raw_bead(), wavelength_nm=bad)


def test_missing_wavelength_has_no_guessed_default() -> None:
    settings = options()
    del settings["wavelength_nm"]
    # Required Python keyword absence is signature validation, not OtfError.
    with pytest.raises((TypeError, api("OtfError"))):
        api("prepare_bead_otf")(raw_bead(), **settings)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("bead_diameter_um", -1),
        ("bead_diameter_um", True),
        ("bead_diameter_um", np.nan),
        ("carrier_angle_rad", True),
        ("carrier_angle_rad", np.inf),
        ("carrier_angle_rad", 1e100),
        ("background_counts", -1),
        ("background_counts", True),
        ("background_counts", np.nan),
        ("background_counts", 1e100),
        ("background_counts", "0"),
    ],
)
def test_other_scalar_kinds_and_ranges(name: str, bad: Any) -> None:
    reject_prepare(raw_bead(), **{name: bad})


@pytest.mark.parametrize(
    "name", ["compensate_bead", "fix_axial_axis", "rescale_each", "forced_pi_shift", "conjugate"]
)
@pytest.mark.parametrize("bad", [0, 1, "false", None])
def test_flags_require_actual_booleans(name: str, bad: Any) -> None:
    reject_prepare(raw_bead(), **{name: bad})


@pytest.mark.parametrize(
    "name,bad",
    [
        ("fix_radial_from", -1),
        ("fix_radial_from", 1.0),
        ("fix_radial_from", True),
        ("fix_radial_from", 2**31),
        ("cleanup_axial_bins", (1, 2)),
        ("cleanup_axial_bins", (1, 2, 3, 4)),
        ("cleanup_axial_bins", (1, -1, 1)),
        ("cleanup_axial_bins", (1, 1.0, 1)),
        ("cleanup_axial_bins", (False, 0, 0)),
        ("cleanup_axial_bins", (0, 0, 2**31)),
        ("origin_fit_bins", (0, 2)),
        ("origin_fit_bins", (2, 2)),
        ("origin_fit_bins", (3, 2)),
        ("origin_fit_bins", (1, 13)),
        ("origin_fit_bins", (True, 2)),
        ("origin_fit_bins", (1.0, 2)),
        ("origin_fit_bins", (1,)),
        ("origin_fit_bins", (1, 2, 3)),
    ],
)
def test_integer_and_optional_sequence_validation(name: str, bad: Any) -> None:
    reject_prepare(raw_bead(), **{name: bad})


@pytest.mark.parametrize(
    "kind",
    [
        "missing_slope",
        "missing_background",
        "shape",
        "complex",
        "bool",
        "nan",
        "magnitude",
        "exposure_shape",
        "exposure_bool",
        "exposure_complex",
        "exposure_nan",
        "exposure_magnitude",
    ],
)
def test_all_maps_validate_even_when_superseded(kind: str) -> None:
    settings: dict[str, Any] = {
        "background_map": np.zeros((24, 24)),
        "slope_map": np.ones((24, 24)),
        "exposure_background_counts": np.zeros((5, 5)),
    }
    if kind == "missing_slope":
        del settings["slope_map"]
    elif kind == "missing_background":
        del settings["background_map"]
    elif kind == "shape":
        settings["background_map"] = np.zeros((24, 23))
    elif kind in {"complex", "bool", "nan", "magnitude"}:
        settings["slope_map"] = np.full(
            (24, 24), {"complex": 1j, "bool": True, "nan": np.nan, "magnitude": 1e100}[kind]
        )
    else:
        settings["exposure_background_counts"] = {
            "exposure_shape": np.zeros((5, 4)),
            "exposure_bool": np.ones((5, 5), dtype=bool),
            "exposure_complex": np.ones((5, 5), dtype=complex),
            "exposure_nan": np.full((5, 5), np.nan),
            "exposure_magnitude": np.full((5, 5), 1e100),
        }[kind]
    reject_prepare(raw_bead(), **settings)


def test_superseded_scalar_and_physical_optics_still_validate() -> None:
    reject_prepare(raw_bead(), exposure_background_counts=np.zeros((5, 5)), background_counts=-1)
    reject_prepare(raw_bead(), numerical_aperture=1.6, immersion_index=1.515)
    reject_prepare(raw_bead(), compensate_bead=True, bead_diameter_um=0)
    positive = api("prepare_bead_otf")(
        raw_bead(),
        **options(
            bead_diameter_um=0,
            carrier_angle_rad=-0.5,
            fix_radial_from=np.int64(40),
            wavelength_nm=np.int32(520),
        ),
    )
    assert np.isfinite(positive.transfer.samples).all()


def test_valid_signed_maps_and_exposure_values_and_zero_slopes() -> None:
    raw = raw_bead()
    slope = np.ones((24, 24))
    slope[:3] = 0
    slope[-3:] = -1
    actual = api("prepare_bead_otf")(
        raw, **options(background_map=np.full((24, 24), -1), slope_map=slope)
    )
    assert np.isfinite(actual.transfer.samples).all()
    exposure = api("prepare_bead_otf")(
        raw, **options(exposure_background_counts=np.full((5, 5), -0.25))
    )
    np.testing.assert_array_equal(exposure.background_counts, -0.25)


@pytest.mark.parametrize("kind", ["yc20", "fractional_negative_z"])
def test_unsafe_unused_diagnostic_operation_rejects(kind: str) -> None:
    raw = np.zeros((1, 3, 48, 48))
    if kind == "yc20":
        raw[0, 1, 20, 24] = 10
    else:
        # zc<0 makes floor(zc)=-1. y>20 makes the unused diagnostic read it.
        raw[0, 0, 24, 24] = 10
        raw[0, -1, 24, 24] = 4
        raw[0, 1, 24, 24] = 1
    reject_prepare(raw)


def test_zero_normalization_rejects_while_direct_zero_tables_are_valid() -> None:
    reject_prepare(np.zeros((5, 3, 24, 24)))
    for layout, shape in [("radial", (1, 2, 1)), ("full", (1, 2, 2, 2))]:
        transfer = api("declare_otf")(np.zeros(shape), layout=layout, dkr_cyc_um=1, dkz_cyc_um=1)
        actual = api("sample_otf")(transfer, 0, 0, 0, dkz_cyc_um=1)
        np.testing.assert_array_equal(actual, 0j)


def test_cleanup_unsafe_actual_write_and_singular_side_norm_reject() -> None:
    # h(r0)=1, l11=7 => j=6 and Z-j=-1, outside allocation at r0.
    reject_prepare(raw_bead(), cleanup_axial_bins=(7, 1, 1))
    # Low NA, l11=3 covers every side axial cell (end=2, Z=5).
    reject_prepare(raw_bead(), numerical_aperture=0.22, cleanup_axial_bins=(3, 1, 1))


@pytest.mark.parametrize(
    "changes", [{"dxy_um": 2**-1070}, {"dz_um": 2**-1070}, {"linespacing_um": 2**-1070}]
)
def test_sphere_nonfinite_or_unresolved_arithmetic_rejects(changes: dict[str, Any]) -> None:
    reject_prepare(raw_bead(), compensate_bead=True, **changes)


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize(
    "kind",
    [
        "bool",
        "object",
        "string",
        "nan",
        "inf",
        "complex64_inexact",
        "magnitude",
        "ndim",
        "empty_order",
        "empty_axis",
    ],
)
def test_invalid_complete_tables(layout: str, kind: str) -> None:
    shape = (2, 3, 4) if layout == "radial" else (2, 3, 4, 5)
    samples = np.ones(shape, dtype=np.complex128)
    if kind in {"bool", "object", "string"}:
        samples = np.ones(shape, dtype={"bool": bool, "object": object, "string": str}[kind])
    elif kind in {"nan", "inf", "complex64_inexact", "magnitude"}:
        samples.flat[0] = {
            "nan": np.nan,
            "inf": 1j * np.inf,
            "complex64_inexact": 1 + 1j * (1 + 2**-30),
            "magnitude": 1e100,
        }[kind]
    elif kind == "ndim":
        samples = samples[0]
    elif kind == "empty_order":
        samples = samples[:0]
    else:
        samples = samples[:, :0]
    with pytest.raises(api("OtfError"), match=".+"):
        api("declare_otf")(samples, layout=layout, dkr_cyc_um=1, dkz_cyc_um=1)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("layout", "five-quadrature"),
        ("layout", None),
        ("dkr_cyc_um", 0),
        ("dkz_cyc_um", -1),
        ("dkr_cyc_um", True),
        ("dkz_cyc_um", np.nan),
        ("dkr_cyc_um", np.inf),
        ("dkz_cyc_um", 1e100),
        ("dkr_cyc_um", "1"),
    ],
)
def test_invalid_table_declarations(name: str, bad: Any) -> None:
    settings = {"layout": "radial", "dkr_cyc_um": 1, "dkz_cyc_um": 1} | {name: bad}
    with pytest.raises(api("OtfError"), match=".+"):
        api("declare_otf")(np.ones((1, 2, 2)), **settings)


@pytest.mark.parametrize(
    "layout,shape,scalar_safe",
    [
        ("radial", (1, 1, 1), False),
        ("radial", (1, 3, 1), True),
        ("full", (1, 1, 2, 1), False),
        ("full", (1, 1, 3, 1), True),
    ],
)
def test_permitted_length_one_axes_and_empty_queries(
    layout: str, shape: tuple[int, ...], scalar_safe: bool
) -> None:
    transfer = api("declare_otf")(np.ones(shape), layout=layout, dkr_cyc_um=1, dkz_cyc_um=1)
    empty = api("sample_otf")(transfer, np.array([]), 0, 0, dkz_cyc_um=1)
    assert empty.shape == (0,)
    # Full K1/X1 reads [0,1,1,2,0,1,1,2]: Y2 is unsafe, Y3 is safe.
    # Declarations and empty queries remain valid for both complete tables.
    if scalar_safe:
        np.testing.assert_array_equal(api("sample_otf")(transfer, 0, 0, 0, dkz_cyc_um=1), 1)
    else:
        with pytest.raises(api("OtfError"), match=".+"):
            api("sample_otf")(transfer, 0, 0, 0, dkz_cyc_um=1)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("kx", True),
        ("kx", [1j]),
        ("kx", ["1"]),
        ("kx", [object()]),
        ("kx", np.nan),
        ("ky", np.inf),
        ("kz", 1.0),
        ("kz", True),
        ("kz", [1j]),
        ("kz", ["1"]),
        ("kz", np.inf),
        ("order", -1),
        ("order", 2),
        ("order", True),
        ("order", 0.0),
        ("order", [0]),
        ("dkz_cyc_um", 0),
        ("dkz_cyc_um", -1),
        ("dkz_cyc_um", True),
        ("dkz_cyc_um", np.nan),
        ("dkz_cyc_um", 1e100),
    ],
)
def test_invalid_query_types_and_scalar_settings(field: str, bad: Any) -> None:
    transfer = api("declare_otf")(np.ones((2, 4, 4)), layout="radial", dkr_cyc_um=1, dkz_cyc_um=1)
    args: dict[str, Any] = {"kx": 0, "ky": 0, "kz": 0, "order": 0, "dkz_cyc_um": 1}
    args[field] = bad
    with pytest.raises(api("OtfError"), match=".+"):
        api("sample_otf")(
            transfer,
            args["kx"],
            args["ky"],
            args["kz"],
            dkz_cyc_um=args["dkz_cyc_um"],
            order=args["order"],
        )


def test_incompatible_broadcast_and_source_integer_overflow() -> None:
    transfer = api("declare_otf")(np.ones((1, 3, 3)), layout="radial", dkr_cyc_um=1, dkz_cyc_um=1)
    for x, y, z in [
        (np.ones(2), np.ones(3), 0),
        (2**31, 0, 0),
        (0, 0, 2**31),
        (0, 0, -(2**31) - 1),
        (1e308, 1e308, 0),
    ]:
        with pytest.raises(api("OtfError"), match=".+"):
            api("sample_otf")(transfer, x, y, z, dkz_cyc_um=1)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("layout", "invalid"),
        ("dkr_cyc_um", 0),
        ("dkz_cyc_um", np.nan),
        ("norders", 9),
        ("samples", np.ones((1, 2))),
        ("samples", np.full((1, 3, 3), np.nan)),
        ("source_revision", "other"),
        ("reference_sha256", ()),
    ],
)
def test_forged_or_mutated_transfer_records_reject(field: str, bad: Any) -> None:
    original = api("declare_otf")(np.ones((1, 3, 3)), layout="radial", dkr_cyc_um=1, dkz_cyc_um=1)
    forged = copy(original)
    object.__setattr__(forged, field, bad)
    with pytest.raises(api("OtfError"), match=".+"):
        api("sample_otf")(forged, 0, 0, 0, dkz_cyc_um=1)
    with pytest.raises(api("OtfError"), match=".+"):
        api("sample_otf")({"samples": original.samples}, 0, 0, 0, dkz_cyc_um=1)


@pytest.mark.parametrize("amplitudes", [[1, 1, 1], [3, 4, 2]])
def test_singular_cosine_quadrature_including_positive_sine(amplitudes: list[int]) -> None:
    # For P=3, C=(a0-(a1+a2)/2)/3=0 exactly. The second S=(4-2)*sqrt(3)/6>0.
    # These exact mathematical singularities are not ordinary small sidebands.
    # Numerical trig residuals cannot resolve the undefined ratio b/a.
    spatial = raw_bead()[0] / 12
    # raw_bead()[0] has a secondary amplitude4, which division by12 would not
    # preserve float32 exactly. Use a single declared integer bead instead.
    spatial[:] = 0
    spatial[1, 11, 11] = 10
    raw = np.array(amplitudes)[:, None, None, None] * spatial
    reject_prepare(raw)


def test_each_quadrature_scale_rejects_zero_sine_slot() -> None:
    raw = raw_bead()
    raw[1:] = 0
    reject_prepare(raw, rescale_each=True)


def test_nonfinite_inverse_empirical_scale_rejects() -> None:
    reject_prepare(
        raw_bead(),
        background_map=np.zeros((24, 24)),
        slope_map=np.full((24, 24), 2**-1070),
    )


@pytest.mark.parametrize("entry", ["raw", "radial", "full"])
def test_actual_source_element_products_exceed_signed32(entry: str) -> None:
    # Real caller zero-stride views backed by one scalar. The source counts,
    # rather than sizeof byte products, must reject before scan/copy/allocation.
    limit = 2**31 - 1
    scalar = np.array(1, dtype=np.float32)
    if entry == "raw":
        n = isqrt(limit // 3)
        n -= n % 2
        assert n**2 * 3 <= limit < (n + 2) * n * 3
        raw = np.broadcast_to(scalar, (1, 3, n, n))
        reject_prepare(raw, compensate_bead=False)
    else:
        if entry == "radial":
            shape = (1, 2, 2**30)
            assert shape[1] * shape[2] > limit
        else:
            shape = (1, 2, 32768, 32768)
            assert shape[2] * shape[3] <= limit < shape[1] * shape[2] * shape[3]
        table = np.broadcast_to(scalar, shape)
        with pytest.raises(api("OtfError"), match=".+"):
            api("declare_otf")(table, layout=entry, dkr_cyc_um=1, dkz_cyc_um=1)


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_empty_query_owned_complex_extent_exceeds_native_intp(layout: str) -> None:
    limit = int(np.iinfo(np.intp).max)
    real_size = np.dtype(np.float64).itemsize
    complex_size = np.dtype(np.complex128).itemsize
    valid_extent = limit // complex_size
    invalid_extent = valid_extent + 1
    assert real_size * invalid_extent <= limit
    assert complex_size * valid_extent <= limit < complex_size * invalid_extent
    shape = (1, 2, 2) if layout == "radial" else (1, 2, 2, 2)
    transfer = api("declare_otf")(np.ones(shape), layout=layout, dkr_cyc_um=1, dkz_cyc_um=1)
    scalar = np.array(0, dtype=np.float64)
    valid = np.broadcast_to(scalar, (0, valid_extent))
    invalid = np.broadcast_to(scalar, (0, invalid_extent))
    assert valid.nbytes == invalid.nbytes == 0
    assert valid.strides == invalid.strides == (0, 0)
    actual = api("sample_otf")(transfer, valid, 0, 0, dkz_cyc_um=1)
    assert actual.shape == valid.shape and actual.dtype == np.complex128
    assert actual.flags.owndata
    with pytest.raises(api("OtfError"), match=".+"):
        api("sample_otf")(transfer, invalid, 0, 0, dkz_cyc_um=1)
