"""CE04 public declaration, representation and reachable operation failures."""

from __future__ import annotations

import copy
import importlib
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from c_known_fixture import blank, compare, known, public, table


def changed(record: Any, **fields: Any) -> Any:
    """Forge only documented public fields on a separate real record."""
    result = copy.copy(record)
    for name, value in fields.items():
        object.__setattr__(result, name, value)
    return result


def rejects(bands: Any, transfer: Any, names: tuple[str, ...], **changes: Any) -> None:
    """Require domain error, informative argument/operation and unchanged inputs."""
    error = public("ReconstructionError")
    assert issubclass(error, public("SimreconError"))
    assert issubclass(error, ValueError)
    originals = []
    for record, name in (
        (bands, "quadratures"),
        (bands, "noise_variance_factors"),
        (transfer, "samples"),
    ):
        value = getattr(record, name, None)
        if isinstance(value, np.ndarray):
            originals.append((record, name, value.copy()))
    supplied_arrays = [
        (value, value.copy()) for value in changes.values() if isinstance(value, np.ndarray)
    ]
    with pytest.raises(error) as caught:
        known(bands, transfer, **changes)
    message = str(caught.value).lower()
    assert message
    assert any(n.lower() in message for n in names), message
    for record, name, original in originals:
        assert_array_equal(getattr(record, name), original)
    for value, original in supplied_arrays:
        assert_array_equal(value, original)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("wavelength_nm", 0),
        ("wavelength_nm", -1),
        ("wavelength_nm", 32768),
        ("wavelength_nm", 520.0),
        ("wavelength_nm", True),
        ("wavelength_nm", np.inf),
        ("wavelength_nm", "520"),
        ("numerical_aperture", 0),
        ("numerical_aperture", -0.5),
        ("numerical_aperture", 1.34),
        ("numerical_aperture", 2.01),
        ("immersion_index", 0.99),
        ("immersion_index", 2.01),
        ("wiener", 0),
        ("wiener", -1),
        ("wiener", None),
        ("wiener", "auto"),
        ("wiener", 1 + 0j),
        ("output_taper", "power"),
        ("output_taper", "precise"),
        ("output_taper", None),
        ("output_taper", np.ones((2, 2))),
        ("output_taper", lambda x: x),
    ],
)
def test_invalid_scalar_integer_and_taper_declarations(name: str, bad: Any) -> None:
    rejects(blank(), table(), (name,), **{name: bad})


@pytest.mark.parametrize(
    "name", ["numerical_aperture", "immersion_index", "wiener", "suppression_radius_bins"]
)
@pytest.mark.parametrize("bad", [True, "1", 1 + 0j, np.nan, np.inf, -np.inf, 1e39, np.array([1.0])])
def test_invalid_real_scalar_kinds_and_finiteness(name: str, bad: Any) -> None:
    rejects(blank(), table(), (name,), **{name: bad})


@pytest.mark.parametrize(
    "name", ["suppress_singularities", "dampen_order0", "omit_order0", "omit_kz0"]
)
@pytest.mark.parametrize("bad", [0, 1, None, "false", np.array([True])])
def test_flags_require_actual_boolean(name: str, bad: Any) -> None:
    rejects(blank(), table(), (name,), **{name: bad})


@pytest.mark.parametrize(
    "name,bad",
    [
        ("carriers_cyc_um", [[0, 0]]),
        ("carriers_cyc_um", np.zeros(2)),
        ("carriers_cyc_um", np.zeros((2, 2))),
        ("carriers_cyc_um", np.zeros((1, 3))),
        ("carriers_cyc_um", np.zeros((1, 2), bool)),
        ("carriers_cyc_um", np.zeros((1, 2), complex)),
        ("carriers_cyc_um", np.zeros((1, 2), object)),
        ("carriers_cyc_um", np.array([["0", "0"]])),
        ("carriers_cyc_um", np.zeros((1, 2), np.longdouble)),
        ("carriers_cyc_um", np.array([[np.nan, 0]])),
        ("carriers_cyc_um", np.array([[0, np.inf]])),
        ("carriers_cyc_um", np.array([[1e39, 0]])),
        ("modulation", [[1]]),
        ("modulation", np.ones(1)),
        ("modulation", np.ones((1, 2))),
        ("modulation", np.ones((2, 1))),
        ("modulation", np.ones((1, 1), bool)),
        ("modulation", np.ones((1, 1), object)),
        ("modulation", np.array([["1"]])),
        ("modulation", np.ones((1, 1), np.clongdouble)),
        ("modulation", np.array([[complex(0, np.nan)]])),
        ("modulation", np.array([[complex(np.inf, 0)]])),
        ("modulation", np.array([[complex(0, 1e39)]])),
    ],
)
def test_carrier_modulation_arrays_kinds_shapes_and_components(name: str, bad: Any) -> None:
    rejects(blank(), table(), (name,), **{name: bad})


@pytest.mark.parametrize(
    "dtype",
    [
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
    ],
)
def test_supported_real_array_kinds_zero_carriers_signed_zero_modulation(dtype: Any) -> None:
    b = blank()
    b.quadratures[:] = 1 - 0.5j
    # Integer carrier is zero; fractional metadata need not round-trip float32.
    compare(
        b,
        table(),
        carriers_cyc_um=np.zeros((1, 2), dtype),
        modulation=np.zeros((1, 1), dtype),
        suppression_radius_bins=-0.123456789,
    )


@pytest.mark.parametrize("dtype", [np.complex64, np.complex128])
def test_supported_complex_noncontiguous_readonly_inputs_and_mutated_bands(dtype: Any) -> None:
    b = blank()
    b.quadratures[:] = -0.125 + 0.5j
    b.noise_variance_factors[:] = [0.125, 8]
    carrier = np.array([[0.123456789, 9, -0.0625, 9]])[:, ::2]
    modulation = np.array([[-0.5 + 0.25j, 9]], dtype=dtype)[:, ::2]
    carrier.flags.writeable = False
    modulation.flags.writeable = False
    b.quadratures.flags.writeable = False
    b.noise_variance_factors.flags.writeable = False
    compare(b, table(), carriers_cyc_um=carrier, modulation=modulation)


@pytest.mark.parametrize("immersion,na,wavelength", [(1, 1, 1), (2, 2, 32767), (1, 0.5, 520)])
def test_permitted_optical_endpoints(immersion: float, na: float, wavelength: int) -> None:
    compare(
        blank(), table(), immersion_index=immersion, numerical_aperture=na, wavelength_nm=wavelength
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_shape", (1, 1, 3, 6, 4)),
        ("input_shape", (1, 1, 3, 1, 4, 4)),
        ("input_shape", (1, 1, 3, 6, 4, 3)),
        ("input_shape", (0, 1, 3, 6, 4, 4)),
        ("input_shape", (1, 0, 3, 6, 4, 4)),
        ("input_shape", (1, 1, 2, 6, 4, 4)),
        ("input_shape", (1, 1, 3, 6, 0, 4)),
        ("input_shape", (1, 1, 3, 6, 4, 2.0)),
        ("input_shape", (1, True, 3, 6, 4, 4)),
        ("quadratures", []),
        ("quadratures", np.zeros((1, 1, 4, 6, 4, 3), np.complex128)),
        ("quadratures", np.zeros((1, 1, 3, 6, 4, 3), np.complex64)),
        ("quadratures", np.zeros((1, 1, 3, 6, 4, 3), np.float64)),
        ("quadratures", np.zeros((1, 1, 3, 6, 4, 2), np.complex128)),
        ("quadratures", np.full((1, 1, 3, 6, 4, 3), complex(0, np.inf))),
        ("noise_variance_factors", np.ones((1, 2), np.float32)),
        ("noise_variance_factors", []),
        ("noise_variance_factors", np.ones(2)),
        ("noise_variance_factors", np.ones((2, 2))),
        ("noise_variance_factors", np.array([[0, 1.0]])),
        ("noise_variance_factors", np.array([[1, -1.0]])),
        ("noise_variance_factors", np.array([[np.nan, 1]])),
        ("noise_variance_factors", np.array([[1, np.inf]])),
        ("input_scale", 0),
        ("input_scale", True),
        ("input_scale", np.nan),
        ("input_scale", np.inf),
        ("input_scale", 1),
        ("dxy_um", 0),
        ("dxy_um", True),
        ("dxy_um", np.nan),
        ("dxy_um", 1e39),
        ("dz_um", -1),
        ("dz_um", True),
        ("dz_um", np.inf),
        ("dz_um", 1e39),
        ("lateral_zoom", 0),
        ("lateral_zoom", 1.5),
        ("lateral_zoom", True),
        ("axial_zoom", -1),
        ("axial_zoom", 2.0),
        ("axial_zoom", True),
        ("source_revision", "wrong"),
        ("reference_sha256", ()),
    ],
)
def test_invalid_used_prepared_record_fields(field: str, value: Any) -> None:
    b = changed(blank(), **{field: value})
    rejects(b, table(), ("bands", field, "shape", "noise", "source", "scale", "zoom"))


def test_nonrecord_and_one_order_are_rejected_without_new_seam() -> None:
    error = public("ReconstructionError")
    for b in (None, np.zeros(1), object()):
        with pytest.raises(error, match="(?i)bands|PreparedBands"):
            known(b, table(), carriers_cyc_um=np.zeros((1, 2)), modulation=np.ones((1, 1)))
    rejects(blank(1), table(), ("order", "bands"))
    with pytest.raises(error, match="(?i)transfer|OpticalTransfer"):
        known(blank(), object())


@pytest.mark.parametrize(
    "field,value",
    [
        ("layout", "other"),
        ("samples", np.ones((2, 32, 32), np.complex64)),
        ("samples", np.ones((2, 32), np.complex128)),
        ("samples", np.full((2, 32, 32), complex(np.nan, 0))),
        ("norders", 3),
        ("dkr_cyc_um", 0),
        ("dkz_cyc_um", np.inf),
        ("source_revision", "other"),
        ("reference_sha256", ()),
    ],
)
def test_full_transfer_record_validation(field: str, value: Any) -> None:
    rejects(
        blank(), changed(table(), **{field: value}), ("transfer", "otf", field, "order", "source")
    )


def test_transfer_missing_order_rejects_but_unused_extra_orders_are_valid() -> None:
    rejects(blank(3), table(2), ("order", "transfer"))
    b = blank()
    b.quadratures[:] = 1 + 0.25j
    a = compare(b, table(2))
    c = compare(b, table(4))
    assert_array_equal(a.image, c.image)
    assert_array_equal(a.filtered_quadratures, c.filtered_quadratures)


def test_complete_unused_transfer_tail_is_validated_before_zero_data() -> None:
    transfer = table(3)
    samples = transfer.samples.copy()
    samples[-1, -1, -1] = complex(0, np.nan)
    samples.flags.writeable = False
    rejects(blank(), changed(transfer, samples=samples), ("transfer", "otf", "sample", "finite"))


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("zero_case", ["data", "modulation", "damping", "transfer"])
def test_all_actual_zero_weight_stencil_vertices_are_required(layout: str, zero_case: str) -> None:
    b = blank()
    if zero_case != "data":
        b.quadratures[:] = 1
    # The native x=R=1 query is exactly at the last radial/x coordinate.
    # Its extra x vertex is out of allocation at the final axial/y row.
    shape = (2, 3, 1) if layout == "radial" else (2, 1, 1, 3)
    samples = np.ones(shape, np.complex64)
    if zero_case == "transfer":
        samples[:] = 0
    tr = public("declare_otf")(samples, layout=layout, dkr_cyc_um=0.5, dkz_cyc_um=1)
    options: dict[str, Any] = {
        "modulation": np.zeros((1, 1))
        if zero_case in ("modulation", "damping")
        else np.ones((1, 1))
    }
    if zero_case == "damping":
        options["omit_order0"] = True
        options["omit_kz0"] = True
    rejects(b, tr, ("stencil", "sample", "transfer", "otf", "offset", "index"), **options)


def test_zero_modulation_does_not_waive_axial_stencil() -> None:
    b = blank(3, shape=(1, 1, 5, 12, 2, 4))
    # c=[2,4,2]. Side order1 reaches z=-4: one-time wrapping by K=2
    # leaves t=-2 at the origin, an unsafe negative flat vertex. Zero
    # side modulation does not waive that request.
    samples = np.ones((3, 8, 2), np.complex64)
    tr = public("declare_otf")(samples, layout="radial", dkr_cyc_um=0.5, dkz_cyc_um=1 / 3.6)
    rejects(
        b,
        tr,
        ("stencil", "sample", "transfer", "otf", "offset", "index"),
        modulation=np.zeros((1, 2)),
    )


@pytest.mark.parametrize("omit", [False, True], ids=["center-weight", "all-zero-powers"])
def test_zero_modulation_other_term_stencil_rejects_with_safe_self_samples(omit: bool) -> None:
    b = blank(shape=(1, 1, 3, 2, 2, 2))
    if omit:
        # Nonzero inputs isolate zero effective weights from a zero-data shortcut.
        b.quadratures[0, 0, 0, 0, 0, 0] = 1
        b.quadratures[0, 0, 1, 0, 0, 0] = 1
    # R=.5 while dx=dy=1, so only the native origin is inside self support.
    # Its own full-table stencil is safe. Signed side overlap qy=+.25
    # dereferences y=2 in Y=1: offset8 is outside the four-cell order.
    transfer = public("declare_otf")(
        np.ones((2, 1, 1, 4), np.complex64),
        layout="full",
        dkr_cyc_um=0.125,
        dkz_cyc_um=1,
    )
    rejects(
        b,
        transfer,
        ("stencil", "sample", "transfer", "otf", "offset", "index"),
        numerical_aperture=0.125,
        wavelength_nm=500,
        carriers_cyc_um=np.array([[0, 0.25]]),
        modulation=np.zeros((1, 1)),
        omit_order0=omit,
    )


def test_zero_effective_overlap_weights_are_valid_with_safe_full_stencils() -> None:
    b = blank(shape=(1, 1, 3, 2, 2, 2))
    b.quadratures[0, 0, 0, 0, 0, 0] = 1
    b.quadratures[0, 0, 1, 0, 0, 0] = 1
    # Three table y rows admit both shifted requests at +/-.25 cycles/um.
    # Every power is zero, but all actual vertices must still be valid.
    transfer = public("declare_otf")(
        np.ones((2, 1, 3, 4), np.complex64),
        layout="full",
        dkr_cyc_um=0.125,
        dkz_cyc_um=1,
    )
    r = known(
        b,
        transfer,
        numerical_aperture=0.125,
        wavelength_nm=500,
        carriers_cyc_um=np.array([[0, 0.25]]),
        modulation=np.zeros((1, 1)),
        omit_order0=True,
    )
    assert_array_equal(r.filtered_quadratures, 0)
    assert_array_equal(r.image, 0)


@pytest.mark.parametrize(
    "axial_planes", [2, 3], ids=["unsafe-zero-side-power", "safe-zero-side-power"]
)
def test_zero_modulation_opposite_signed_overlap_stencil_without_center_omission(
    axial_planes: int,
) -> None:
    b = blank(shape=(1, 1, 3, 2, 2, 2), dz_um=0.5)
    b.quadratures[0, 0, 0, 0, 0, 0] = 1
    b.quadratures[0, 0, 1, 0, 0, 0] = 1
    transfer = public("declare_otf")(
        np.ones((2, axial_planes, 1, 2), np.complex64),
        layout="full",
        dkr_cyc_um=0.5,
        dkz_cyc_um=1,
    )
    options = dict(
        carriers_cyc_um=np.array([[0, 0.3]]),
        modulation=np.zeros((1, 1)),
        wavelength_nm=500,
        numerical_aperture=0.2,
        immersion_index=1.5,
        wiener=0.5,
        suppress_singularities=False,
        dampen_order0=False,
        omit_order0=False,
        omit_kz0=False,
        output_taper="none",
    )
    # R=.8<dx=dy=1 and c=[0,0]: self origin and shifted center qy=.3
    # are safe. Only the opposite signed side qy=.6 reaches offsets4,5.
    # K2 has four cells/order; K3 has six. That side's modulation is zero.
    if axial_planes == 2:
        rejects(b, transfer, ("stencil", "sample", "transfer", "otf", "offset", "index"), **options)
    else:
        r = known(b, transfer, **options)
        expected = np.zeros_like(b.quadratures)
        expected[0, 0, 0, 0, 0, 0] = 0.8
        np.testing.assert_allclose(r.filtered_quadratures, expected, rtol=2e-12, atol=2e-12)
        np.testing.assert_allclose(r.image, 0.8, rtol=2e-12, atol=2e-12)
        assert_array_equal(r.axial_cutoffs_bins, [0, 0])


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_safe_flat_cross_axis_stencils_remain_permitted(layout: str) -> None:
    if layout == "radial":
        b = blank()
        samples = np.ones((2, 8, 1), np.complex64)
        dkr, dkz = 0.5, 1 / 1.8
    else:
        b = blank(shape=(1, 1, 3, 2, 2, 2))
        samples = np.ones((2, 3, 1, 12), np.complex64)
        dkr, dkz = 1, 1
    b.quadratures[0, 0, 0, 0, 0, 0] = 1
    transfer = public("declare_otf")(samples, layout=layout, dkr_cyc_um=dkr, dkz_cyc_um=dkz)
    result = known(b, transfer, modulation=np.zeros((1, 1)))
    np.testing.assert_allclose(result.image, 0.8, atol=2e-12, rtol=2e-12)


def test_only_actual_inside_self_queries_need_safe_stencils() -> None:
    b = blank(shape=(1, 1, 3, 2, 2, 2))
    b.quadratures[:] = 1
    transfer = public("declare_otf")(
        np.ones((2, 2, 1), np.complex64),
        layout="radial",
        dkr_cyc_um=0.125,
        dkz_cyc_um=1,
    )
    # R=.5,dx=dy=1,c=[0,0]. Only the origin is queried. The x/y
    # native endpoints would have unsafe stencils but are outside self.
    r = known(b, transfer, numerical_aperture=0.125, wavelength_nm=500, modulation=np.zeros((1, 1)))
    np.testing.assert_allclose(r.image, 0.8, rtol=2e-12, atol=2e-12)
    assert_array_equal(r.filtered_quadratures[0, 0, 0, :, :, 1], 0)
    assert_array_equal(r.filtered_quadratures[0, 0, 0, :, 1, :], 0)


def test_unused_finite_diagnostics_are_not_raw_consistency_checks() -> None:
    b = blank()
    b.quadratures[:] = 0.5 + 0.25j
    b.frame_sums[:] = 123
    b.equalization_gains[:] = -2
    b.separation_matrices[:] = 0
    b.phase_angles_rad[:] = 0.123
    compare(b, table())


@pytest.mark.parametrize(
    "lateral,axial", [(65536, 1), (6000, 1), (8192, 1), (16777217, 1), (1, 2**31)]
)
def test_output_source_integer_unsigned_workspace_and_zoom_representation(
    lateral: int, axial: int
) -> None:
    b = blank(shape=(1, 1, 3, 2, 2, 4))
    b = changed(
        b, lateral_zoom=lateral, axial_zoom=axial, input_scale=1 / (4 * 2 * 2 * lateral**2 * axial)
    )
    rejects(
        b, table(), ("represent", "size", "integer", "32", "byte", "zoom", "dimension", "overflow")
    )


@pytest.mark.parametrize("case", ["phase_product", "volume_product", "direction_order_product"])
def test_used_source_products_reject_before_copying_virtual_arrays(case: str) -> None:
    # Zero-stride public NumPy views occupy one scalar of backing storage.
    # No huge caller allocation or artificial product injection seam is needed.
    error = public("ReconstructionError")
    b = blank(shape=(1, 1, 3, 2, 2, 2))
    shape = (1, 1, 3, 2, 2, 2)
    if case == "phase_product":
        shape = (1, 1, 2**31 - 1, 2, 2, 2)
    elif case == "volume_product":
        shape = (1, 1, 3, 2, 2, 2**30)
    else:
        shape = (1, 2**30, 3, 2, 2, 2)
    nt, nd, phases, nz, ny, nx = shape
    backing = np.zeros((), np.complex128)
    q = np.broadcast_to(backing, (nt, nd, 3, nz, ny, nx // 2 + 1))
    noise = np.broadcast_to(np.ones((), np.float64), (nd, 2))
    b = changed(
        b,
        input_shape=shape,
        quadratures=q,
        noise_variance_factors=noise,
        input_scale=1 / (nx * ny * nz * nd),
    )
    with pytest.raises(
        error, match="(?i)represent|integer|32|size|product|dimension|overflow|byte"
    ):
        public("reconstruct_known")(
            b,
            table(),
            carriers_cyc_um=np.broadcast_to(np.zeros(()), (nd, 2)),
            modulation=np.broadcast_to(np.ones(()), (nd, 1)),
            wavelength_nm=520,
            numerical_aperture=0.8,
            immersion_index=1.33,
            wiener=0.5,
        )
    assert backing.item() == 0


@pytest.mark.parametrize(
    "case", ["asin", "square", "sampling", "noise", "arithmetic", "axial_sampling", "cutoff"]
)
def test_reachable_undefined_derived_operations(case: str) -> None:
    b = blank()
    options: dict[str, Any] = {}
    if case == "asin":
        options["carriers_cyc_um"] = np.array([[10.0, 0]])
    elif case == "square":
        options["wiener"] = np.nextafter(0.0, 1.0)
    elif case == "sampling":
        b = changed(b, dxy_um=np.nextafter(0.0, 1.0))
    elif case == "noise":
        b.noise_variance_factors[0, 0] = np.nextafter(0.0, 1.0)
    elif case == "axial_sampling":
        b = changed(b, dz_um=np.nextafter(0.0, 1.0))
    elif case == "cutoff":
        b = changed(b, dz_um=1e38)
    else:
        b.quadratures[:] = np.finfo(float).max * (1 + 0j)
        options["wiener"] = 0.25
        b.noise_variance_factors[:] = np.finfo(float).tiny
    rejects(
        b,
        table(),
        (
            "asin",
            "carrier",
            "domain",
            "finite",
            "square",
            "wiener",
            "sampling",
            "dxy",
            "dz",
            "cutoff",
            "integer",
            "noise",
            "weight",
            "overflow",
            "denominator",
            "scale",
            "result",
        ),
        **options,
    )


@pytest.mark.parametrize("omit,kz0", [(False, False), (True, False), (False, True), (True, True)])
def test_visited_zero_cutoff_damping_is_undefined_before_omission(omit: bool, kz0: bool) -> None:
    rejects(
        blank(shape=(1, 1, 3, 2, 2, 4)),
        table(),
        ("dampen", "damping", "cutoff", "zero", "division"),
        dampen_order0=True,
        omit_order0=omit,
        omit_kz0=kz0,
    )


def test_tiny_positive_wiener_zero_transfer_and_data_remain_valid() -> None:
    b = blank()
    tr = public("declare_otf")(
        np.zeros((2, 16, 16), np.complex64), layout="radial", dkr_cyc_um=0.5, dkz_cyc_um=0.5
    )
    result = known(b, tr, wiener=1e-150)
    assert_array_equal(result.image, 0)
    assert_array_equal(result.filtered_quadratures, 0)


@pytest.mark.parametrize(
    "option",
    [
        "drift",
        "estimate_carriers",
        "automatic_wiener",
        "axial_padding",
        "two_objective",
        "bessel",
        "explode",
        "overlap",
    ],
)
def test_deferred_modes_and_signature_errors_stay_type_errors(option: str) -> None:
    with pytest.raises(TypeError):
        known(blank(), table(), **{option: True})


def test_missing_required_keyword_and_retired_public_names_and_modules() -> None:
    with pytest.raises(TypeError):
        public("reconstruct_known")(blank(), table())
    module = importlib.import_module("simrecon")
    for name in ("reconstruct", "reconstruct_volume", "prepare_otf"):
        assert not hasattr(module, name)
    for name in ("simrecon._reconstruction", "simrecon._otf"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(name)
