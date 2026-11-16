"""SP113 public declaration, selection, validation and ownership drafts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

import simrecon as sr
from simrecon.reconstruction.known_parameters import _extent
from single_known_fixture import (
    BAND_FIELDS,
    CE04_SOURCES,
    I32,
    NATIVE_MAX,
    PROFILE,
    RESULT_FIELDS,
    SETTING_KEYS,
    arrays,
    assert_owned,
    call,
    declare,
    identities,
    known_options,
    owned,
    rn64,
    run_bounded_declaration_experiment,
    snapshot,
    transfer,
)


class ArraySubclass(np.ndarray[Any, np.dtype[Any]]):
    """Accepted for parameters; deliberately disallowed for new band arrays."""


class StringSubclass(str):
    """Exercise rejection of a string subclass with permissive equality."""

    def __eq__(self, other: object) -> bool:
        """Report equality irrespective of the other value."""
        return True

    __hash__ = str.__hash__


class IntSubclass(int):
    """Exercise integer scalar subclass handling."""

    pass


class MisleadingTaper(StringSubclass):
    """Misrepresent supported and unsupported underlying taper contents."""

    def __str__(self) -> str:
        """Return the opposite support class without changing string contents."""
        return "none" if str.__str__(self) == "unknown" else "power"


class RaisingTaper(StringSubclass):
    """Expose an incorrectly invoked overridable taper conversion."""

    def __str__(self) -> str:
        """Reject invocation of the subclass conversion hook."""
        raise RuntimeError("SP113 taper subclass __str__ must not be invoked")


class FloatSubclass(float):
    """Exercise floating scalar subclass handling."""

    pass


class TupleSubclass(tuple[Any, ...]):
    """Exercise exact metadata tuple-kind validation."""

    pass


def rejected(action: Any, term: str | tuple[str, ...]) -> sr.ReconstructionError:
    with pytest.raises(sr.ReconstructionError) as caught:
        action()
    error = caught.value
    assert isinstance(error, ValueError)
    assert error.code == "reconstruction-domain"
    message = str(error)
    assert message
    terms = (term,) if isinstance(term, str) else term
    assert any(word.lower() in message.lower() for word in terms)
    return error


def test_constructor_snapshot_direct_record_and_subclass() -> None:
    q, v = arrays(t=2, d=2, o=3, y=3)
    # Logical values include signed, arbitrary complex and all-zero slots.
    q[0, 0, 0, 0, 0, 0] = -3 + 2j
    q[1, 1, 4, 1, 2, 1] = 2**-140 * (1 - 1j)
    v[...] = np.array([[[1, 2, 4], [3, 5, 7]], [[2, 3, 5], [7, 11, 13]]])
    q_view, v_view = q[..., ::-1], v[..., ::-1]
    q_view.flags.writeable = False
    v_view.flags.writeable = False
    before = snapshot(q_view, v_view)
    provenance = (("conversion", "caller declared c64"), ("formula", "signed sparse modes"))
    bands = declare(q_view, v_view, provenance=provenance)
    assert tuple(field.name for field in fields(bands)) == BAND_FIELDS
    assert_owned(bands.quadratures, np.complex64, q.shape)
    assert_owned(bands.noise_variance_factors, np.float64, v.shape)
    assert snapshot(bands.quadratures, bands.noise_variance_factors) == before
    assert bands.provenance == provenance
    assert bands.input_scale == 1 / (4 * 3 * 2 * 2)
    assert type(bands.input_scale) is float
    assert type(bands.input_shape) is tuple
    assert all(type(n) is int for n in bands.input_shape)
    assert type(bands.dxy_um) is float and type(bands.dz_um) is float
    assert bands.mapping_revision == "ce04-svn307-v1"
    assert bands.precision_profile == PROFILE
    assert not np.shares_memory(bands.quadratures, q)
    assert not np.shares_memory(bands.noise_variance_factors, v)
    q[...] = 0
    v[...] = 19
    assert snapshot(bands.quadratures, bands.noise_variance_factors) == before
    with pytest.raises(FrozenInstanceError):
        bands.input_scale = 1.0
    new_type = sr.PreparedBands32
    direct = new_type(**{field.name: getattr(bands, field.name) for field in fields(bands)})
    assert call(direct).precision_profile == PROFILE

    derived = type("Derived", (new_type,), {})
    subclass = derived(**{field.name: getattr(bands, field.name) for field in fields(bands)})
    assert call(subclass).precision_profile == PROFILE


@pytest.mark.parametrize(
    "precision",
    [None, True, 1, [], StringSubclass(PROFILE), "", "single", "float32", "SINGLE-MIXED-V1"],
)
def test_precision_rejects_before_record_or_domain(precision: Any) -> None:
    reconstruction: Any = sr.reconstruct_known
    rejected(
        lambda: reconstruction(
            None,
            None,
            precision=precision,
            carriers_cyc_um=None,
            modulation=None,
            wavelength_nm=0,
            numerical_aperture=0,
            immersion_index=0,
            wiener=0,
        ),
        "precision",
    )


def test_explicit_selection_and_incompatible_records() -> None:
    reconstruction: Any = sr.reconstruct_known
    bands = declare()
    assert type(call(bands)) is sr.KnownReconstruction32
    for precision in ("double",):
        rejected(
            lambda precision=precision: call(bands, precision=precision),
            ("bands", "precision", "PreparedBands"),
        )
    options: dict[str, Any] = dict(
        carriers_cyc_um=np.zeros((1, 2)),
        modulation=np.ones((1, 1)),
        wavelength_nm=500,
        numerical_aperture=1.0,
        immersion_index=1.0,
        wiener=0.5,
    )
    rejected(
        lambda: sr.reconstruct_known(bands, transfer(), **options),
        ("bands", "precision", "PreparedBands"),
    )
    rejected(lambda: reconstruction(object(), transfer(), precision=PROFILE, **options), "bands")
    malformed = replace(bands, input_scale=0.0)
    rejected(lambda: call(malformed, precision="double"), ("bands", "precision", "PreparedBands"))


@pytest.mark.parametrize(
    "field,dtype",
    [
        ("quadratures", np.complex128),
        ("quadratures", np.float32),
        ("quadratures", np.bool_),
        ("quadratures", object),
        ("quadratures", ">c8"),
        ("noise_variance_factors", np.float32),
        ("noise_variance_factors", np.int64),
        ("noise_variance_factors", np.complex128),
        ("noise_variance_factors", np.bool_),
        ("noise_variance_factors", ">f8"),
    ],
)
def test_exact_array_dtypes_at_both_boundaries(field: str, dtype: Any) -> None:
    q, v = arrays()
    bad = np.zeros(q.shape if field == "quadratures" else v.shape, dtype=dtype)
    # Metadata/structure rejects before nonfinite/value scans or copying.
    rejected(
        lambda: declare(
            bad if field == "quadratures" else q, bad if field == "noise_variance_factors" else v
        ),
        field,
    )
    bands = declare()
    rejected(lambda: call(replace(bands, **{field: owned(bad)})), field)


@pytest.mark.parametrize("field", ["quadratures", "noise_variance_factors"])
def test_arrays_require_ordinary_ndarray(field: str) -> None:
    q, v = arrays()
    bands, otf = declare(q, v), transfer()
    options = known_options(bands)
    original = q if field == "quadratures" else v
    for bad in (original.tolist(), original.view(ArraySubclass)):
        rejected(
            lambda bad=bad: declare(
                bad if field == "quadratures" else q,
                bad if field == "noise_variance_factors" else v,
            ),
            field,
        )
        # Form valid call metadata before forging the array kind: convenience
        # helpers must not inspect the malformed field before its consumer.
        rejected(
            lambda bad=bad: sr.reconstruct_known(replace(bands, **{field: bad}), otf, **options),
            field,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_shape", [1, 1, 3, 2, 2, 4]),
        ("input_shape", (1, 1, 3, 2, 4)),
        ("input_shape", TupleSubclass((1, 1, 3, 2, 2, 4))),
        ("input_shape", (True, 1, 3, 2, 2, 4)),
        ("input_shape", (np.int64(1), 1, 3, 2, 2, 4)),
        ("input_shape", (IntSubclass(1), 1, 3, 2, 2, 4)),
        ("input_shape", (1.0, 1, 3, 2, 2, 4)),
        ("input_shape", (0, 1, 3, 2, 2, 4)),
        ("input_shape", (1, 0, 3, 2, 2, 4)),
        ("input_shape", (1, 1, 0, 2, 2, 4)),
        ("input_shape", (1, 1, 3, 1, 2, 4)),
        ("input_shape", (1, 1, 3, 2, 0, 4)),
        ("input_shape", (1, 1, 3, 2, 2, 3)),
        ("input_shape", (1, 1, 3, 2, 2, 0)),
        ("lateral_zoom", True),
        ("axial_zoom", np.int64(1)),
        ("lateral_zoom", 1.0),
        ("axial_zoom", IntSubclass(1)),
        ("lateral_zoom", 0),
        ("axial_zoom", -1),
        ("mapping_revision", StringSubclass("ce04-svn307-v1")),
        ("mapping_revision", "wrong"),
        ("mapping_revision", None),
        ("provenance", []),
        ("provenance", (["key", "value"],)),
        ("provenance", TupleSubclass((("key", "value"),))),
        ("provenance", (TupleSubclass(("key", "value")),)),
        ("provenance", (("only",),)),
        ("provenance", (("", "value"),)),
        ("provenance", ((1, "value"),)),
        ("provenance", ((StringSubclass("key"), "value"),)),
        ("provenance", (("key", StringSubclass("value")),)),
        ("provenance", (("key", 1),)),
        ("provenance", (("dup", "one"), ("dup", "two"))),
    ],
)
def test_metadata_structure_at_constructor_and_consumer(field: str, value: Any) -> None:
    rejected(lambda: declare(**{field: value}), (field, "shape", "dimension"))
    rejected(lambda: call(replace(declare(), **{field: value})), (field, "shape", "dimension"))


@pytest.mark.parametrize("field", ["dxy_um", "dz_um"])
@pytest.mark.parametrize(
    "value", [True, np.bool_(False), 1j, "1", np.nan, np.inf, -np.inf, 0.0, -1.0, 2.0**128, 2**2048]
)
def test_sampling_original_domain(field: str, value: Any) -> None:
    rejected(lambda: declare(**{field: value}), field)
    rejected(lambda: call(replace(declare(), **{field: value})), field)


def test_constructor_scalar_kinds_are_canonicalized_but_consumer_metadata_is_exact() -> None:
    bands = declare(dxy_um=np.float32(1), dz_um=FloatSubclass(1))
    assert type(bands.dxy_um) is float and type(bands.dz_um) is float
    for field in ("dxy_um", "dz_um", "input_scale"):
        rejected(
            lambda field=field: call(
                replace(bands, **{field: FloatSubclass(getattr(bands, field))})
            ),
            field,
        )
    for field, bad in (
        ("precision_profile", StringSubclass(PROFILE)),
        ("precision_profile", "double"),
        ("precision_profile", None),
        ("input_scale", 0.0),
        ("input_scale", -1.0),
        ("input_scale", np.inf),
        ("input_scale", np.nan),
        ("input_scale", bands.input_scale * 2),
        ("input_scale", np.float64(bands.input_scale)),
    ):
        rejected(
            lambda field=field, bad=bad: call(replace(bands, **{field: bad})),
            (field, "scale", "profile"),
        )
    reduced = declare(input_shape=(1, 1, 4, 2, 2, 4), provenance=())
    assert reduced.input_shape[2] == 4 and reduced.quadratures.shape[2] == 3
    assert reduced.provenance == ()
    assert call(reduced).precision_profile == PROFILE


@pytest.mark.parametrize(
    "which", ["axes", "even-q", "one-order", "q-over-p", "half-x", "noise-shape"]
)
def test_shape_consistency(which: str) -> None:
    q, v = arrays()
    options: dict[str, Any] = {}
    if which == "axes":
        q = q[0]
        options["input_shape"] = (1, 1, 3, 2, 2, 4)
    elif which == "even-q":
        q = q[:, :, :2]
    elif which == "one-order":
        q, v = arrays(o=1)
    elif which == "q-over-p":
        options["input_shape"] = (1, 1, 2, 2, 2, 4)
    elif which == "half-x":
        options["input_shape"] = (1, 1, 3, 2, 2, 6)
    else:
        v = v[0]
    # Direct public constructor avoids the fixture's convenience shape unpack.
    base: dict[str, Any] = dict(
        input_shape=(1, 1, 3, 2, 2, 4), dxy_um=1.0, dz_um=1.0, lateral_zoom=1, axial_zoom=1
    )
    base.update(options)
    constructor = sr.declare_prepared_bands32
    rejected(lambda: constructor(q, v, **base), ("shape", "quadrature", "noise", "order", "Q"))


@pytest.mark.parametrize("field", ["quadratures", "noise_variance_factors"])
@pytest.mark.parametrize("fault", ["view", "writable", "strided", "nan", "inf"])
def test_consumer_array_ownership_and_values(field: str, fault: str) -> None:
    bands = declare()
    original = getattr(bands, field)
    bad = np.array(original, copy=True)
    if fault == "view":
        bad = bad.view()
    elif fault == "strided":
        bad = bad[..., ::-1]
    elif fault in ("nan", "inf"):
        bad.flat[0] = np.nan if fault == "nan" else np.inf
    if fault != "writable":
        bad.flags.writeable = False
    rejected(lambda: call(replace(bands, **{field: bad})), field)


@pytest.mark.parametrize("value", [0.0, -1.0, np.nan, np.inf])
def test_noise_values_at_both_boundaries(value: float) -> None:
    q, v = arrays()
    v[0, 0, 1] = value
    rejected(lambda: declare(q, v), "noise")
    bands = declare()
    rejected(lambda: call(replace(bands, noise_variance_factors=owned(v))), "noise")


def test_nonfinite_coefficients_and_consumer_shapes_reject_without_mutation() -> None:
    for value in (complex(np.nan, 0), complex(0, np.inf)):
        q, v = arrays()
        q[0, 0, 2, 0, 0, 0] = value
        before = snapshot(q, v)
        rejected(lambda q=q, v=v: declare(q, v), "quadrature")
        assert snapshot(q, v) == before
    bands = declare()
    rejected(
        lambda: call(replace(bands, quadratures=owned(bands.quadratures[0]))),
        ("shape", "quadrature"),
    )
    rejected(
        lambda: call(replace(bands, noise_variance_factors=owned(bands.noise_variance_factors[0]))),
        ("shape", "noise"),
    )
    for slots in (1, 2, 5):
        q = np.zeros((1, 1, slots, 2, 2, 3), dtype=np.complex64)
        rejected(
            lambda q=q: call(replace(bands, quadratures=owned(q))),
            ("shape", "quadrature", "order", "Q"),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("wavelength_nm", True),
        ("wavelength_nm", np.bool_(True)),
        ("wavelength_nm", 500.0),
        ("wavelength_nm", 0),
        ("wavelength_nm", 32768),
        ("numerical_aperture", True),
        ("numerical_aperture", 1j),
        ("numerical_aperture", np.nan),
        ("numerical_aperture", np.inf),
        ("numerical_aperture", 0.0),
        ("numerical_aperture", -1.0),
        ("numerical_aperture", 1.1),
        ("numerical_aperture", 2.0**128),
        ("immersion_index", False),
        ("immersion_index", 1j),
        ("immersion_index", np.nan),
        ("immersion_index", np.inf),
        ("immersion_index", 0.9),
        ("immersion_index", 2.1),
        ("immersion_index", 2.0**128),
        ("wiener", True),
        ("wiener", 1j),
        ("wiener", np.nan),
        ("wiener", np.inf),
        ("wiener", 0.0),
        ("wiener", -0.5),
        ("wiener", 2.0**128),
        ("suppression_radius_bins", True),
        ("suppression_radius_bins", 1j),
        ("suppression_radius_bins", np.nan),
        ("suppression_radius_bins", np.inf),
        ("suppression_radius_bins", 2.0**128),
        ("output_taper", 1),
        ("output_taper", "unknown"),
        ("wiener_increment", True),
        ("wiener_increment", 1j),
        ("wiener_increment", np.nan),
        ("wiener_increment", np.inf),
        ("wiener_increment", 2.0**128),
        ("explode_factor", True),
        ("explode_factor", 1j),
        ("explode_factor", np.nan),
        ("explode_factor", np.inf),
        ("explode_factor", 2.0**128),
    ],
)
def test_scalar_declarations(field: str, value: Any) -> None:
    rejected(lambda: call(**{field: value}), (field, "aperture", "immersion"))


@pytest.mark.parametrize(
    "field",
    [
        "suppress_singularities",
        "dampen_order0",
        "omit_order0",
        "omit_kz0",
        "precise_taper",
        "filter_overlaps",
    ],
)
@pytest.mark.parametrize("bad", [0, 1, "false", None])
def test_actual_booleans_even_with_zero_bands(field: str, bad: Any) -> None:
    rejected(lambda: call(**{field: bad}), field)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("wiener_increment", 0.1),
        ("wiener_increment", -0.1),
        ("power_taper_exponent", 0),
        ("power_taper_exponent", "unused"),
        ("precise_taper", True),
        ("filter_overlaps", False),
        ("explode_factor", 0),
        ("explode_factor", -1),
        ("explode_factor", 2),
        ("output_taper", "power"),
    ],
)
def test_unsupported_options_cannot_hide_behind_zero_data(field: str, bad: Any) -> None:
    rejected(lambda: call(modulation=np.zeros((1, 1)), omit_order0=True, **{field: bad}), field)


def test_valid_scalar_flag_taper_and_option_equivalents() -> None:
    result = call(
        wavelength_nm=np.int32(500),
        numerical_aperture=np.float32(1),
        immersion_index=np.float64(1),
        wiener=np.float32(0.5),
        suppress_singularities=np.bool_(False),
        suppression_radius_bins=-2.0,
        dampen_order0=np.bool_(False),
        omit_order0=np.bool_(False),
        omit_kz0=np.bool_(False),
        output_taper=StringSubclass("none"),
        wiener_increment=-0.0,
        power_taper_exponent=None,
        precise_taper=np.bool_(False),
        filter_overlaps=np.bool_(True),
        explode_factor=np.int64(1),
    )
    settings = dict(result.resolved_settings)
    assert type(settings["output_taper"]) is str and settings["output_taper"] == "none"
    for key in ("suppress_singularities", "dampen_order0", "omit_order0", "omit_kz0"):
        assert type(settings[key]) is bool
    for wavelength in (1, 32767):
        assert call(wavelength_nm=wavelength, numerical_aperture=0.5).image.shape == (1, 2, 2, 4)
    for immersion in (1.0, 2.0):
        assert (
            call(immersion_index=immersion, numerical_aperture=immersion).image.dtype == np.float32
        )
    assert call(output_taper="cosine").image.dtype == np.float32
    # A str subclass lying about equality cannot enable an unsupported taper.
    rejected(lambda: call(output_taper=StringSubclass("unknown")), "taper")


@pytest.mark.parametrize("taper_type", [MisleadingTaper, RaisingTaper])
def test_taper_uses_base_content_for_settings_identity_and_rejection(taper_type: type[str]) -> None:
    q, v = arrays(y=1, x=2)
    bands, otf = declare(q, v), transfer()
    for underlying in ("none", "cosine"):
        supplied = taper_type(underlying)
        assert type(str.__str__(supplied)) is str
        options = known_options(bands, output_taper=supplied)
        result = call(bands, otf, output_taper=supplied)
        canonical = dict(result.resolved_settings)["output_taper"]
        assert type(canonical) is str and canonical == underlying
        expected_id = identities(bands, otf, options)["parameters_sha256"]
        assert dict(result.precision_provenance)["parameters_sha256"] == expected_id
    rejected(lambda: call(bands, otf, output_taper=taper_type("unknown")), "taper")


@pytest.mark.parametrize("field,shape", [("carriers_cyc_um", (1, 2)), ("modulation", (1, 1))])
@pytest.mark.parametrize(
    "fault", ["list", "shape", "bool", "object", "string", "extended", "nan", "inf", "range"]
)
def test_parameter_original_domains(field: str, shape: tuple[int, ...], fault: str) -> None:
    bad: Any = np.ones(shape)
    if fault == "list":
        bad = bad.tolist()
    elif fault == "shape":
        bad = np.ones(shape[-1:])
    elif fault in ("bool", "object", "string", "extended"):
        dtype = {"bool": np.bool_, "object": object, "string": "U1", "extended": np.longdouble}[
            fault
        ]
        bad = np.ones(shape, dtype=dtype)
    else:
        bad.flat[0] = {"nan": np.nan, "inf": np.inf, "range": 2.0**128}[fault]
    rejected(lambda: call(**{field: bad}), (field, "carrier", "modulation"))


def test_parameter_complex_rules_and_permitted_subclasses_strides_and_byte_orders() -> None:
    rejected(lambda: call(carriers_cyc_um=np.zeros((1, 2), dtype=np.complex128)), "carrier")
    for dtype in (
        np.int8,
        np.uint8,
        np.int16,
        np.uint16,
        np.int32,
        np.uint32,
        np.int64,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        ">f8",
    ):
        carriers = np.zeros((1, 4), dtype=dtype)[:, ::-2].view(ArraySubclass)
        carriers.flags.writeable = False
        modulation = np.ones((1, 2), dtype=dtype)[:, ::-2].view(ArraySubclass)
        modulation.flags.writeable = False
        result = call(carriers_cyc_um=carriers, modulation=modulation)
        np.testing.assert_array_equal(result.carriers_cyc_um, carriers)
        np.testing.assert_array_equal(result.modulation, modulation)
    for value in (0j, -1 + 0j, 1j, (1 + 2**-30) + 0.5j):
        result = call(
            carriers_cyc_um=np.array([[-0.0, -(2**-30)]]),
            modulation=np.array([[value]], dtype=">c16"),
        )
        assert result.modulation[0, 0] == value
        assert result.carriers_cyc_um[0, 1] == -(2**-30)
    for dtype in (np.complex64, np.complex128, ">c8", ">c16"):
        values = np.array([[1 + 0.5j, -1j]], dtype=dtype)[:, ::-2].view(ArraySubclass)
        values.flags.writeable = False
        result = call(modulation=values)
        np.testing.assert_array_equal(result.modulation, values)
    rejected(lambda: call(modulation=np.ones((1, 1), dtype=np.clongdouble)), "modulation")
    rejected(lambda: call(modulation=np.array([[complex(0, -np.inf)]])), "modulation")
    integer_modulation = np.array([[2**53 + 1]], dtype=np.uint64)
    before_integer = snapshot(integer_modulation)
    converted = call(modulation=integer_modulation)
    assert converted.modulation[0, 0] == complex(2**53, 0)
    assert snapshot(integer_modulation) == before_integer


def test_phase_precedence_and_failure_immutability() -> None:
    bands, otf = declare(), transfer()
    q_bad = np.array(bands.quadratures, copy=True)
    q_bad.flat[0] = np.nan
    bad_bands = replace(bands, quadratures=owned(q_bad))
    rejected(lambda: call(bad_bands, object(), wiener=0), "quadrature")
    rejected(lambda: call(bands, object(), wiener=0), ("transfer", "OpticalTransfer"))
    rejected(
        lambda: call(bands, replace(otf, source_revision="wrong"), wiener=0),
        ("transfer", "otf", "revision"),
    )
    rejected(
        lambda: call(bands, otf, wavelength_nm=0, numerical_aperture=0, carriers_cyc_um=None),
        "wavelength",
    )
    rejected(lambda: call(bands, otf, wiener=0, carriers_cyc_um=None), "wiener")
    rejected(lambda: call(bands, otf, carriers_cyc_um=None, modulation=None), "carrier")
    rejected(
        lambda: call(
            bands, otf, carriers_cyc_um=np.array([[np.nan, 0.0]]), modulation=np.ones((2, 2))
        ),
        "carrier",
    )
    rejected(
        lambda: call(bands, transfer(radial=1, axial=1), modulation=np.ones((2, 2))), "modulation"
    )
    sources = (bands.quadratures, bands.noise_variance_factors, otf.samples)
    before = snapshot(*sources)
    rejected(lambda: call(bands, otf, modulation=np.ones((2, 2))), "modulation")
    assert snapshot(*sources) == before


def test_scalar_signature_order_precedence_even_for_unsupported_values() -> None:
    ordered_invalid: tuple[tuple[str, Any], ...] = (
        ("wavelength_nm", 0),
        ("numerical_aperture", 0.0),
        ("immersion_index", 0.0),
        ("wiener", 0.0),
        ("suppress_singularities", 0),
        ("suppression_radius_bins", np.nan),
        ("dampen_order0", 0),
        ("omit_order0", 0),
        ("omit_kz0", 0),
        ("output_taper", "unknown"),
        ("wiener_increment", 1.0),
        ("power_taper_exponent", 1.0),
        ("precise_taper", True),
        ("filter_overlaps", False),
        ("explode_factor", 0.0),
    )
    for (first, bad_first), (second, bad_second) in zip(
        ordered_invalid, ordered_invalid[1:], strict=False
    ):
        rejected(
            lambda first=first, bad_first=bad_first, second=second, bad_second=bad_second: call(
                **{first: bad_first, second: bad_second}
            ),
            first,
        )


def test_original_unbounded_integer_reals_reject_before_binary64_conversion() -> None:
    for field in (
        "numerical_aperture",
        "immersion_index",
        "wiener",
        "suppression_radius_bins",
        "wiener_increment",
        "explode_factor",
    ):
        rejected(lambda field=field: call(**{field: 2**2048}), field)


def test_adjacent_band_metadata_and_structure_value_precedence() -> None:
    bands = declare()
    ordered_invalid: tuple[tuple[str, Any], ...] = (
        ("input_shape", (1, 1, 3, 2, 2)),
        ("input_scale", 0.0),
        ("dxy_um", 0.0),
        ("dz_um", 0.0),
        ("lateral_zoom", 0),
        ("axial_zoom", 0),
        ("mapping_revision", "wrong"),
        ("precision_profile", "wrong"),
        ("provenance", (("dup", "one"), ("dup", "two"))),
    )
    for (first, bad_first), (second, bad_second) in zip(
        ordered_invalid, ordered_invalid[1:], strict=False
    ):
        rejected(
            lambda first=first, bad_first=bad_first, second=second, bad_second=bad_second: call(
                replace(bands, **{first: bad_first, second: bad_second})
            ),
            (first, "shape" if first == "input_shape" else first),
        )
    bad_q = np.array(bands.quadratures, copy=True)
    bad_q.flat[0] = np.nan
    # Complete array structure/dtype checks precede original-value scans.
    rejected(
        lambda: call(
            replace(
                bands,
                quadratures=owned(bad_q),
                noise_variance_factors=owned(bands.noise_variance_factors.astype(np.float32)),
            )
        ),
        "noise",
    )
    # Metadata domains precede ownership flags; original q finite scans precede
    # positive-noise scans. They are different public fields, not message aliases.
    writable = np.array(bands.quadratures, copy=True)
    rejected(lambda: call(replace(bands, dxy_um=0.0, quadratures=writable)), "dxy")
    rejected(
        lambda: call(
            replace(
                bands, quadratures=owned(bad_q), noise_variance_factors=owned(np.zeros((1, 1, 2)))
            )
        ),
        "quadrature",
    )


def test_transfer_record_validation_and_unused_orders() -> None:
    bands = declare()
    otf = transfer(orders=3)
    assert call(bands, otf).image.dtype == np.float32
    for field, bad in (
        ("layout", "unknown"),
        ("dkr_cyc_um", 0.0),
        ("dkz_cyc_um", np.nan),
        ("norders", 4),
        ("source_revision", "wrong"),
        ("reference_sha256", ()),
        ("samples", np.ones(otf.samples.shape, dtype=np.complex64)),
    ):
        rejected(
            lambda field=field, bad=bad: call(bands, replace(otf, **{field: bad})),
            ("transfer", "otf", field),
        )
    samples = np.array(otf.samples, copy=True)
    samples[2, -1, -1] = np.nan
    rejected(
        lambda: call(bands, replace(otf, samples=owned(samples))), ("transfer", "otf", "finite")
    )
    rejected(lambda: call(bands, transfer(orders=1)), ("order", "transfer"))
    for field in ("dkr_cyc_um", "dkz_cyc_um"):
        for bad_value in (True, 1j, "bad", -1.0, np.inf, 2**128):
            rejected(
                lambda field=field, bad_value=bad_value: call(
                    bands, replace(otf, **{field: bad_value})
                ),
                ("transfer", "otf", field),
            )
    for bad_samples in (
        np.array(otf.samples, copy=True),
        otf.samples.view(),
        owned(np.zeros((0, 8, 8), dtype=np.complex128)),
    ):
        rejected(
            lambda bad_samples=bad_samples: call(bands, replace(otf, samples=bad_samples)),
            ("transfer", "otf", "samples", "shape"),
        )


@pytest.mark.parametrize(
    "shape,itemsize",
    [
        ((NATIVE_MAX,), 1),
        ((NATIVE_MAX - 1,), 1),
        ((NATIVE_MAX // 8,), 8),
        ((NATIVE_MAX // 16,), 16),
        ((2**29, 2), 8),
        ((2**30,), 4),
        ((2**30,), 8),
        ((2**16, 2**16), 8),
    ],
)
def test_integer_only_native_admission_has_no_legacy_byte_cap(
    shape: tuple[int, ...], itemsize: int
) -> None:
    # This approved real-caller validator creates no target array.
    _extent(shape, itemsize)


@pytest.mark.parametrize(
    "shape,itemsize",
    [
        ((NATIVE_MAX + 1,), 1),
        ((NATIVE_MAX // 8 + 1,), 8),
        ((NATIVE_MAX // 16 + 1,), 16),
        ((2**32, 2**32), 1),
        ((2**30, 2**30), 16),
    ],
)
def test_integer_only_native_rejection_uses_exact_aggregate_products(
    shape: tuple[int, ...], itemsize: int
) -> None:
    rejected(
        lambda: _extent(shape, itemsize), ("extent", "native", "representation", "array", "byte")
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"input_shape": (I32 + 1, 1, 3, 2, 2, 4)},
        {"input_shape": (1, 1, 3, 2, 2, 2**30)},
        {"input_shape": (1, 1, 3, 2, 2**30, 4)},
        {"input_shape": (1, 1, I32, 2, 2, 4)},
        {"lateral_zoom": 2**24 + 1},
        {"lateral_zoom": 2**30},
        {"axial_zoom": 2**30},
    ],
)
def test_invalid_metadata_with_tiny_backing_never_reaches_large_work(
    changes: dict[str, Any],
) -> None:
    # Deliberately tiny backing; no huge successful allocation or transform.
    rejected(
        lambda: declare(**changes),
        ("shape", "dimension", "extent", "zoom", "representation", "phase", "Q"),
    )


def test_wide_output_and_lookup_bytes_admit_tiny_declaration_before_scalar_failure(
    record_property: Any,
) -> None:
    # Output(2,16384,32768) has2**30 elements, 8*volume=2**33 bytes,
    # and4*plane=2**31 bytes. Signed counts and native extents still fit.
    # Declaration copies only tiny q/v; invalid Wiener stops the consumer
    # before output allocation/FFT. No large successful operation is attempted.
    # The same capped case also rejects A2's volumeI+1 at the constructor and
    # a matching canonical forged-record consumer, with all other inputs valid.
    # It separately rejects D*O=I+1 with physically backed zero-stride views;
    # no logical-wide copying, scanning, hashing or successful array is requested.
    report, diagnostics = run_bounded_declaration_experiment("wide")
    record_property("sp113_wide_bounded_child", report)
    record_property("sp113_wide_bounded_child_diagnostics", diagnostics)


def test_qp_limit_remains_but_absent_preparation_frame_count_does_not_apply(
    record_property: Any,
) -> None:
    # Q3*P=I-1 fits; D*P*Z exceeds I but no frame/preparation storage exists.
    # All actual arrays and all native/output spatial volumes remain tiny.
    report, diagnostics = run_bounded_declaration_experiment("phase")
    record_property("sp113_phase_bounded_child", report)
    record_property("sp113_phase_bounded_child_diagnostics", diagnostics)


def test_operation_domains_have_no_tiny_noise_or_wiener_floor() -> None:
    q, v = arrays(y=1, x=2)
    # Y1 avoids all filtering; reciprocal noise and required w² still bind.
    v[...] = 2**-100
    assert call(declare(q, v), wiener=2**-100).image.dtype == np.float32
    v[...] = np.nextafter(np.float64(0), np.float64(1))
    rejected(lambda: call(declare(q, v)), (PROFILE, "noise", "reciprocal"))
    rejected(lambda: call(wiener=2**-600), (PROFILE, "wiener", "square"))
    assert call(wiener=2**-500).image.dtype == np.float32
    rejected(
        lambda: call(carriers_cyc_um=np.array([[16.0, 0.0]])), (PROFILE, "asin", "beta", "carrier")
    )


def test_derived_sampling_cutoff_and_suppression_domains_are_not_silent_fallbacks() -> None:
    q, v = arrays(y=1, x=2)
    for field in ("dxy_um", "dz_um"):
        rejected(
            lambda field=field: call(declare(q, v, **{field: 2**-1074})),
            (PROFILE, "sampling", "spacing", "finite", "frequency"),
        )
    rejected(lambda: call(declare(dz_um=2**100)), (PROFILE, "cutoff", "representation", "integer"))
    rejected(
        lambda: call(declare(dxy_um=2**-1000), suppression_radius_bins=2**100),
        (PROFILE, "radius", "suppression", "finite"),
    )


def test_reachable_source_asin_upper_endpoint_and_positive_taper_radius_neighbor() -> None:
    q, v = arrays(y=1, x=2)
    # wavelength1000,immersion1 give le1 and lx=the binary64 literal.88.
    # The oracle resolves the exact rounded carrier product before any call.
    lx = Fraction(0.88)
    endpoint = rn64(Fraction(2) / lx)
    outside = endpoint + Fraction(1, 2**51)
    assert rn64(rn64(endpoint * lx) / 2) == 1
    assert rn64(rn64(outside * lx) / 2) > 1
    bands = declare(q, v)
    valid = call(bands, carriers_cyc_um=np.array([[float(endpoint), 0.0]]), wavelength_nm=1000)
    assert np.all(valid.image == 0)
    rejected(
        lambda: call(bands, carriers_cyc_um=np.array([[float(outside), 0.0]]), wavelength_nm=1000),
        (PROFILE, "asin", "beta", "carrier"),
    )
    # NA min-subnormal permits zero intermediate sin/theta factors but no NA
    # floor. At wavelength1000 R=2^-1073 remains positive; at32767 it rounds0,
    # so b0 gives invalid required Rp0. Y1 still requires other domains defined.
    assert np.all(
        call(bands, numerical_aperture=2**-1074, wavelength_nm=1000, output_taper="cosine").image
        == 0
    )
    rejected(
        lambda: call(
            bands, numerical_aperture=2**-1074, wavelength_nm=32767, output_taper="cosine"
        ),
        (PROFILE, "radius", "cutoff", "taper", "support"),
    )


def test_result_schema_values_and_success_immutability() -> None:
    q, v = arrays(t=2)
    bands, otf = declare(q, v), transfer()
    carriers = np.array([[0.125, -0.25]])
    modulation = np.array([[-0.5 + 0.25j]])
    originals = (
        q,
        v,
        bands.quadratures,
        bands.noise_variance_factors,
        otf.samples,
        carriers,
        modulation,
    )
    before = snapshot(*originals)
    result = call(bands, otf, carriers_cyc_um=carriers, modulation=modulation)
    assert snapshot(*originals) == before
    assert tuple(field.name for field in fields(result)) == RESULT_FIELDS
    outputs = (
        result.image,
        result.filtered_quadratures,
        result.x_um,
        result.y_um,
        result.z_um,
        result.carriers_cyc_um,
        result.modulation,
        result.axial_cutoffs_bins,
    )
    for output, dtype, shape in zip(
        outputs,
        (
            np.float32,
            np.complex64,
            np.float64,
            np.float64,
            np.float64,
            np.float64,
            np.complex128,
            np.int64,
        ),
        ((2, 2, 2, 4), q.shape, (4,), (2,), (2,), (1, 2), (1, 1), (2,)),
        strict=True,
    ):
        assert_owned(output, dtype, shape)
        assert all(not np.shares_memory(output, original) for original in originals)
    for i, output in enumerate(outputs):
        assert all(not np.shares_memory(output, other) for other in outputs[i + 1 :])
    np.testing.assert_array_equal(result.carriers_cyc_um, carriers)
    np.testing.assert_array_equal(result.modulation, modulation)
    np.testing.assert_array_equal(result.x_um, [-2, -1, 0, 1])
    np.testing.assert_array_equal(result.y_um, [-1, 0])
    np.testing.assert_array_equal(result.z_um, [-1, 0])
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [0, 0])
    assert type(result.radial_cutoff_cyc_um) is float
    assert result.radial_cutoff_cyc_um == 0.5
    assert result.mode_trace == ()
    assert result.source_revision == "SVN307"
    assert result.reference_sha256 == CE04_SOURCES
    assert result.precision_profile == PROFILE
    assert tuple(key for key, _ in result.resolved_settings) == SETTING_KEYS
    expected_kinds = (
        int,
        float,
        float,
        float,
        bool,
        float,
        bool,
        bool,
        bool,
        str,
        float,
        float,
        int,
        int,
        float,
    )
    assert all(
        type(value) is kind
        for (_, value), kind in zip(result.resolved_settings, expected_kinds, strict=True)
    )
    with pytest.raises(FrozenInstanceError):
        result.image = np.zeros((1,))


def test_signature_binding_stays_python_type_error() -> None:
    reconstruction: Any = sr.reconstruct_known
    declaration = sr.declare_prepared_bands32
    with pytest.raises(TypeError):
        reconstruction(declare(), transfer())
    with pytest.raises(TypeError):
        call(unknown_option=True)
    with pytest.raises(TypeError):
        declaration(*arrays())
    with pytest.raises(TypeError):
        reconstruction(declare(), transfer(), precision=PROFILE, **{"precision": PROFILE})
