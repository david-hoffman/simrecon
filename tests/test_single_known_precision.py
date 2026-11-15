"""Rounding, cancellation, identity and real numerical-interface failure drafts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
import scipy
import scipy.fft

import simrecon as sr

from .single_known_fixture import (
    HALF_SUB32,
    PRECISION_VALUES,
    PROFILE,
    U32,
    arrays,
    assert_public_equal,
    call,
    declare,
    identities,
    legacy_acquisition,
    legacy_known_options,
    legacy_raw,
    legacy_transfer,
    legacy_workflow_options,
    public_values,
    rn32,
    rn64,
    snapshot,
    transfer,
)
from .test_single_known_boundary import rejected


def test_correlated_dc_exact_and_near_cancellation_with_preregistered_bound(
    record_property: Any,
) -> None:
    s = rn32(rn64(Fraction(4, 13)))
    for offset in (Fraction(0), Fraction(1, 2**20)):
        q, v = arrays()
        q[0, 0, 0, 0, 0, 0] = 1
        q[0, 0, 1, 0, 0, 0] = float(-(1 - offset) / 2)
        result = call(declare(q, v))
        mathematical = Fraction(4, 13) * offset
        # x0=x32: all declared coefficients here are exactly representable.
        # Scalar RN64(4/13), scale onceRN32, side multiplication then
        # recombination form the candidate rational procedure separately.
        side = rn32(s * (-(1 - offset) / 2))
        finite = rn32(s + 2 * side)
        assert np.all(result.image == float(finite))
        absolute_error = abs(finite - mathematical)
        record_property(
            "sp113_dc_metrics",
            {
                "input_representation_error": "0",
                "reference_width": "0",
                "max_absolute_error": str(absolute_error),
                "rms_error": str(absolute_error),
                "interval_distance": str(absolute_error),
                "far_endpoint_upper_bound": str(absolute_error),
                "signal_scale": "4/13",
                "error_over_signal_scale": str(absolute_error / Fraction(4, 13)),
                "signed_minimum": str(finite),
                "signed_maximum": str(finite),
                "cancellation_condition": str((2 - offset) / offset) if offset else "infinite",
                "phase_at_zero_amplitude": "undefined",
            },
        )
        if not offset:
            assert finite == mathematical == 0
            assert np.all(result.image == 0)
        else:
            # Fixed coefficient/scalar-bin derivation from public context.
            # DC transforms and zero-carrier ramp have zero transform/phase
            # error. f64 adds exact dyadic terms; final rounding is separate.
            before_final = (Fraction(1, 2**55) + Fraction(1, 2**26)) * (2 - offset) + 2 * Fraction(
                1, 2**27
            )
            final_round = U32 * abs(s + 2 * side) + HALF_SUB32
            assert abs(finite - mathematical) <= before_final + final_round
            assert mathematical > 0
            assert (2 - offset) / offset == 2097151
            assert np.all(result.image > 0)


def test_profile_schema_and_independent_framed_identities() -> None:
    q, v = arrays(y=1, x=2)
    q[0, 0, 0, 0, 0, 0] = complex(-0.0, -0.0)
    bands = declare(q, v, provenance=(("formula", "DC"), ("conversion", "none")))
    otf = transfer(value=1 + 0.5j, empirical_delta=2**-30)
    result = call(bands, otf)
    entries = result.precision_provenance
    assert type(entries) is tuple
    assert all(type(pair) is tuple and len(pair) == 2 for pair in entries)
    assert all(type(key) is str and type(value) is str for key, value in entries)
    assert tuple(key for key, _ in entries) == tuple(key for key, _ in PRECISION_VALUES)
    actual = dict(entries)
    for key, expected in PRECISION_VALUES:
        if expected is not None:
            assert actual[key] == expected
        else:
            assert actual[key]
    assert actual["scipy_version"] == scipy.__version__
    assert actual["numpy_version"] == np.__version__
    for key, expected in identities(bands, otf, result).items():
        assert actual[key] == expected
        assert len(expected) == 64 and set(expected) <= set("0123456789abcdef")
    q_positive = np.array(q, copy=True)
    q_positive[0, 0, 0, 0, 0, 0] = 0j
    plus_bands = declare(q_positive, v, provenance=bands.provenance)
    plus = call(plus_bands, otf)
    assert dict(plus.precision_provenance)["bands_sha256"] != actual["bands_sha256"]
    changed_note = replace(bands, provenance=(("formula", "DC"), ("conversion", "caller c64")))
    assert (
        dict(call(changed_note, otf).precision_provenance)["bands_sha256"] != actual["bands_sha256"]
    )
    changed_source = transfer(value=1 + 0.5j, empirical_delta=2**-29)
    assert (
        dict(call(bands, changed_source).precision_provenance)["transfer_sha256"]
        != actual["transfer_sha256"]
    )
    changed_parameter = call(bands, otf, modulation=np.array([[-1 + 0.5j]]))
    assert (
        dict(changed_parameter.precision_provenance)["parameters_sha256"]
        != actual["parameters_sha256"]
    )


def test_subnormal_complete_scale_may_round_finitely_to_zero() -> None:
    # h=2^-149 is the smallest positive c64 component. With w=2, complete
    # center scale is approximately h/4, below half-subnormal; RN32 is0.
    q, v = arrays()
    q[0, 0, 0, 0, 0, 0] = 1
    result = call(declare(q, v), transfer(value=complex(2**-149, 0)), wiener=2.0)
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 0] == 0
    assert np.all(result.image == 0)
    # Absolute rather than relative error is bounded by the local half-spacing.
    assert Fraction(1, 2**151) < HALF_SUB32


def test_consumed_scale_and_native_addition_overflow_reject_before_hidden_cancellation() -> None:
    rejected(
        lambda: call(otf=transfer(value=complex(2**-140, 0)), wiener=2**-140),
        (PROFILE, "scale", "conversion"),
    )
    assert call(otf=transfer(value=complex(2**-120, 0)), wiener=2**-120).image.dtype == np.float32
    q, v = arrays()
    maximum = np.finfo(np.float32).max
    q[0, 0, 1, 0, 0, 0] = maximum
    q[0, 0, 2, 0, 0, 0] = -1j * maximum
    bands = declare(q, v)
    before = snapshot(bands.quadratures, bands.noise_variance_factors)
    rejected(
        lambda: call(bands, modulation=np.zeros((1, 1))),
        (PROFILE, "coefficient", "overflow", "native", "finite"),
    )
    assert snapshot(bands.quadratures, bands.noise_variance_factors) == before
    q[0, 0, 2, 0, 0, 0] = 0
    assert np.all(call(declare(q, v), modulation=np.zeros((1, 1))).image == 0)


def test_ordered_power_product_and_recombination_intermediate_overflow() -> None:
    q, v = arrays()
    v[...] = 2**-1000
    rejected(
        lambda: call(declare(q, v), modulation=np.array([[2**100]], dtype=np.float64)),
        (PROFILE, "power", "denominator", "finite", "overflow"),
    )
    v[...] = 2**-100
    assert (
        call(declare(q, v), modulation=np.array([[2**100]], dtype=np.float64)).image.dtype
        == np.float32
    )
    maximum = np.finfo(np.float32).max
    q[0, 0, 0, 0, 0, 0] = maximum
    rejected(
        lambda: call(
            declare(q, np.ones_like(v)), transfer(value=complex(2**-120, 0)), wiener=2**-120
        ),
        (PROFILE, "coefficient", "native", "finite", "overflow"),
    )
    q[...] = 0
    q[0, 0, 0, 0, 0, 0] = -maximum
    q[0, 0, 1, 0, 0, 0] = maximum
    # H=1/2,w=1/4 gives scale8/13: p and n are finite, p+n is not.
    # The later factor1/2 must not conceal that required primitive overflow.
    rejected(
        lambda: call(declare(q, np.ones_like(v)), transfer(value=0.5), wiener=0.25),
        (PROFILE, "recombination", "native", "finite", "overflow"),
    )


def test_complete_float64_scale_can_overflow_before_consumed_conversion() -> None:
    q, v = arrays()
    # Valid prepared-style c128 source2^-1073, below the c64 component range.
    # Its squared magnitude rounds0; w²=2^-1074 is the smallest positive f64.
    # With v1, quotient2 is finite. With v2^-1023, inverse noise2^1023
    # makes numerator2^-50, so division by2^-1074 overflows at2^1024.
    otf = transfer(value=0j, empirical_delta=2**-1073)
    assert np.all(call(declare(q, v), otf, wiener=2**-537).image == 0)
    v[...] = 2**-1023
    bands = declare(q, v)
    before = snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples)
    rejected(
        lambda: call(bands, otf, wiener=2**-537), (PROFILE, "scalar", "filter scale", "float64")
    )
    assert snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples) == before
    rejected(
        lambda: call(declare(q, np.ones_like(v)), otf, wiener=2**-538),
        (PROFILE, "wiener", "square"),
    )


def test_y1_embedding_still_checks_c64_harmonic_addition() -> None:
    q, v = arrays(d=2, y=1, x=2)
    maximum = np.finfo(np.float32).max
    q[0, 0, 0, 0, 0, 0] = -maximum
    q[0, 0, 1, 0, 0, 0] = maximum
    q[0, 0, 2, 0, 0, 0] = -1j * maximum
    q[0, 1, 0, 0, 0, 0] = -maximum
    q[0, 1, 1, 0, 0, 0] = -maximum
    bands = declare(q, v)
    before = snapshot(bands.quadratures)
    rejected(lambda: call(bands), (PROFILE, "embed", "coefficient", "native", "harmonic", "finite"))
    assert snapshot(bands.quadratures) == before
    q[0, 0, 2, 0, 0, 0] = 0
    q[0, 1, 1, 0, 0, 0] = 0
    assert np.all(call(declare(q, v)).image == 0)


def test_final_image_overflow_is_distinct_from_finite_f64_accumulation() -> None:
    q, v = arrays(d=2, y=1, x=2)
    q[:, :, 0, 0, 0, 0] = np.finfo(np.float32).max
    bands = declare(q, v)
    before = snapshot(bands.quadratures)
    rejected(
        lambda: call(bands, modulation=np.zeros((2, 1))), (PROFILE, "image", "final", "float32")
    )
    assert snapshot(bands.quadratures) == before


class FailureBackend:
    """Expose controlled faults through the existing SciPy FFT backend interface."""

    __ua_domain__ = "numpy.scipy.fft"

    def __init__(self, failure: BaseException | None) -> None:
        self.failure = failure
        self.calls = 0

    def __ua_function__(self, method: Any, args: Any, kwargs: Any) -> Any:
        """Handle only the declared inverse transform with the selected fault."""
        if method.__name__ != "ifftn":
            return NotImplemented
        self.calls += 1
        assert args[0].dtype == np.complex64
        assert kwargs.get("axes") == (0, 1, 2)
        assert kwargs.get("norm") == "forward" and kwargs.get("workers") == 1
        if self.failure is not None:
            raise self.failure
        if self.calls == 1:
            # Imaginary-only nonfinite center output could otherwise disappear
            # when center assembly consumes its real part. Later FFTs are0.
            return np.full(args[0].shape, complex(0, np.inf), dtype=np.complex64)
        return np.zeros(args[0].shape, dtype=np.complex64)


def test_backend_exception_cause_nonfinite_result_and_interruption_are_public() -> None:
    bands, otf = declare(), transfer()
    before = snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples)
    original = RuntimeError("SP113 controlled existing FFT interface failure")
    memory = MemoryError("SP113 controlled FFT-boundary allocation failure")
    for failure in (original, memory):
        backend = FailureBackend(failure)
        with scipy.fft.set_backend(backend, only=True):
            error = rejected(
                lambda: call(bands, otf), (PROFILE, "fft", "transform", "allocation", "memory")
            )
        assert backend.calls == 1 and error.__cause__ is failure
        assert snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples) == before
    nonfinite = FailureBackend(None)
    with scipy.fft.set_backend(nonfinite, only=True):
        rejected(lambda: call(bands, otf), (PROFILE, "fft", "transform", "finite"))
    assert nonfinite.calls == 1
    interrupt = KeyboardInterrupt("SP113 controlled caller interruption")
    interrupted = FailureBackend(interrupt)
    with scipy.fft.set_backend(interrupted, only=True), pytest.raises(KeyboardInterrupt) as caught:
        call(bands, otf)
    assert caught.value is interrupt
    assert snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples) == before
    # Static invalid declarations are rejected without invoking the backend.
    untouched = FailureBackend(original)
    with scipy.fft.set_backend(untouched, only=True):
        rejected(lambda: call(bands, otf, wavelength_nm=0), "wavelength")
    assert untouched.calls == 0
    assert np.all(call(bands, otf).image == 0)


def test_omitted_and_explicit_double_are_exact_same_environment_controls() -> None:
    # The only use of product preparation: a separate old-schema compatibility
    # control. It supplies neither a single-mode input nor scientific truth.
    raw = np.zeros((1, 1, 3, 2, 2, 4), dtype=np.float32)
    raw[:, :, :, :, :, :] = 2
    old = sr.prepare_bands(
        raw,
        dxy_um=1.0,
        dz_um=1.0,
        norders=2,
        background=0.0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )
    otf = transfer()
    options: dict[str, Any] = dict(
        carriers_cyc_um=np.zeros((1, 2)),
        modulation=np.ones((1, 1)),
        wavelength_nm=500,
        numerical_aperture=1.0,
        immersion_index=1.0,
        wiener=0.5,
        suppress_singularities=False,
        output_taper="none",
    )
    known: Any = sr.reconstruct_known
    omitted = known(old, otf, **options)
    explicit = known(old, otf, precision="double", **options)
    assert type(omitted) is type(explicit) is sr.KnownReconstruction
    assert tuple(field.name for field in fields(omitted)) == tuple(
        field.name for field in fields(explicit)
    )
    for field in fields(omitted):
        left, right = getattr(omitted, field.name), getattr(explicit, field.name)
        if isinstance(left, np.ndarray):
            assert left.dtype == right.dtype and left.shape == right.shape
            assert left.tobytes() == right.tobytes()
        else:
            assert left == right
    assert not hasattr(omitted, "precision_profile")
    rejected(
        lambda: known(old, otf, precision=PROFILE, **options),
        ("bands", "precision", "PreparedBands32"),
    )
    masquerade = replace(old, quadratures=old.quadratures.astype(np.complex64))
    omitted_error = rejected(
        lambda: known(masquerade, otf, **options), ("quadrature", "complex128", "dtype")
    )
    explicit_error = rejected(
        lambda: known(masquerade, otf, precision="double", **options),
        ("quadrature", "complex128", "dtype"),
    )
    assert type(omitted_error) is type(explicit_error) and str(omitted_error) == str(explicit_error)
    extended = options | {
        "output_taper": "power",
        "power_taper_exponent": 0.0,
        "wiener_increment": 0.125,
        "filter_overlaps": False,
        "explode_factor": -1.0,
        "precise_taper": False,
    }
    omitted_extended = known(old, otf, **extended)
    explicit_extended = known(old, otf, precision="double", **extended)
    assert_public_equal(omitted_extended, explicit_extended)
    assert dict(omitted_extended.resolved_settings)["output_taper"] == "power"


def test_legacy_acquisition_3d_and_true_2d_keep_double_records_options_and_errors() -> None:
    known: Any = sr.reconstruct_known
    for two_dimensional in (False, True):
        raw = legacy_raw(two_dimensional=two_dimensional)
        original_raw = snapshot(raw)
        bands = legacy_acquisition(raw, two_dimensional=two_dimensional)
        otf = legacy_transfer(two_dimensional=two_dimensional)
        options = legacy_known_options()
        assert type(bands) is sr.AcquisitionBands
        assert bands.quadratures.dtype == np.complex128
        assert bands.noise_variance_factors.dtype == np.float64
        assert bands.noise_variance_factors.shape == (1, 1, 2)
        assert not hasattr(bands, "precision_profile")
        before = snapshot(
            bands.quadratures,
            bands.noise_variance_factors,
            otf.samples,
            options["carriers_cyc_um"],
            options["modulation"],
        )
        omitted = known(bands, otf, **options)
        explicit = known(bands, otf, precision="double", **options)
        assert type(omitted) is sr.KnownReconstruction
        assert_public_equal(omitted, explicit)
        assert omitted.image.dtype == np.float64
        assert omitted.filtered_quadratures.dtype == np.complex128
        assert not hasattr(omitted, "precision_profile")
        extended = options | {
            "output_taper": "power",
            "power_taper_exponent": 0.0,
            "wiener_increment": 0.125,
            "filter_overlaps": False,
            "explode_factor": -1.0,
            "precise_taper": False,
        }
        assert_public_equal(
            known(bands, otf, **extended),
            known(bands, otf, precision="double", **extended),
        )
        rejected(
            lambda bands=bands, otf=otf, options=options: known(
                bands, otf, precision=PROFILE, **options
            ),
            ("bands", "precision", "PreparedBands32"),
        )
        masquerade = replace(bands, quadratures=bands.quadratures.astype(np.complex64))
        omitted_error = rejected(
            lambda masquerade=masquerade, otf=otf, options=options: known(
                masquerade, otf, **options
            ),
            ("quadrature", "complex128", "dtype"),
        )
        explicit_error = rejected(
            lambda masquerade=masquerade, otf=otf, options=options: known(
                masquerade, otf, precision="double", **options
            ),
            ("quadrature", "complex128", "dtype"),
        )
        assert type(omitted_error) is type(explicit_error) and str(omitted_error) == str(
            explicit_error
        )
        # Record/profile compatibility precedes a malformed used c128 field.
        rejected(
            lambda masquerade=masquerade, otf=otf, options=options: known(
                masquerade, otf, precision=PROFILE, **options
            ),
            ("bands", "precision", "PreparedBands32"),
        )
        assert snapshot(raw) == original_raw
        assert (
            snapshot(
                bands.quadratures,
                bands.noise_variance_factors,
                otf.samples,
                options["carriers_cyc_um"],
                options["modulation"],
            )
            == before
        )


def test_existing_full_and_summary_keep_exact_double_projection_and_retention() -> None:
    raw, otf = legacy_raw(), legacy_transfer()
    options = legacy_workflow_options(otf)
    declarations = {key: deepcopy(value) for key, value in options.items() if key != "transfer"}
    before = snapshot(raw, otf.samples)
    full = sr.reconstruct_workflow(raw, **options)
    summary = sr.reconstruct_summary(raw, **options)
    assert type(full) is sr.WorkflowReconstruction
    assert type(summary) is sr.ReconstructionSummary
    assert summary.diagnostics == "summary"
    for name in ("image", "x_um", "y_um", "z_um"):
        full_array, summary_array = getattr(full, name), getattr(summary, name)
        assert full_array.dtype == summary_array.dtype == np.float64
        assert_public_equal(full_array, summary_array)
        assert not np.shares_memory(full_array, summary_array)
        assert not np.shares_memory(summary_array, raw)
    assert summary.image.flags.owndata and not summary.image.flags.writeable
    assert_public_equal(full.intensity_unit, summary.intensity_unit)
    assert_public_equal(full.intensity_semantics, summary.intensity_semantics)
    for name in (
        "carriers_cyc_um",
        "modulation",
        "raw_modulation",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
    ):
        assert_public_equal(getattr(full.parameters, name), getattr(summary, name))
    assert summary.carriers_cyc_um.dtype == np.float64
    assert summary.modulation.dtype == np.complex128
    for reconstruction in full.reconstructions:
        assert type(reconstruction) is sr.KnownReconstruction
        assert reconstruction.filtered_quadratures.dtype == np.complex128
    forbidden_full_records = (sr.PreparedBands, sr.AcquisitionBands, sr.KnownReconstruction)
    assert not any(isinstance(value, forbidden_full_records) for value in public_values(summary))
    assert not hasattr(full, "precision_profile") and not hasattr(summary, "precision_profile")
    assert snapshot(raw, otf.samples) == before
    assert_public_equal(
        declarations, {key: value for key, value in options.items() if key != "transfer"}
    )
    # No precision selector is added to either composed entry.
    workflow: Any = sr.reconstruct_workflow
    compact: Any = sr.reconstruct_summary
    with pytest.raises(TypeError):
        workflow(raw, precision=PROFILE, **options)
    with pytest.raises(TypeError):
        compact(raw, precision=PROFILE, **options)
