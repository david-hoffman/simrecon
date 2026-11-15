"""Rounding, cancellation, identity and real numerical-interface failure drafts."""

from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
import scipy
import scipy.fft

import simrecon as sr

from .single_known_fixture import (
    HALF_SUB32, PRECISION_VALUES, PROFILE, U32, arrays, call, declare,
    identities, rn32, rn64, snapshot, transfer,
)
from .test_single_known_boundary import rejected


def test_correlated_dc_exact_and_near_cancellation_with_preregistered_bound(record_property: Any) -> None:
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
        record_property("sp113_dc_metrics", {
            "input_representation_error": "0", "reference_width": "0",
            "max_absolute_error": str(absolute_error),
            "rms_error": str(absolute_error),
            "interval_distance": str(absolute_error),
            "far_endpoint_upper_bound": str(absolute_error),
            "signal_scale": "4/13",
            "error_over_signal_scale": str(absolute_error / Fraction(4, 13)),
            "signed_minimum": str(finite), "signed_maximum": str(finite),
            "cancellation_condition": str((2 - offset) / offset) if offset else "infinite",
            "phase_at_zero_amplitude": "undefined",
        })
        if not offset:
            assert finite == mathematical == 0
            assert np.all(result.image == 0)
        else:
            # Fixed coefficient/scalar-bin derivation from public context.
            # DC transforms and zero-carrier ramp have zero transform/phase
            # error. f64 adds exact dyadic terms; final rounding is separate.
            before_final = (Fraction(1, 2**55) + Fraction(1, 2**26)) * (2 - offset) + 2 * Fraction(1, 2**27)
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
    assert dict(call(changed_note, otf).precision_provenance)["bands_sha256"] != actual["bands_sha256"]
    changed_source = transfer(value=1 + 0.5j, empirical_delta=2**-29)
    assert dict(call(bands, changed_source).precision_provenance)["transfer_sha256"] != actual["transfer_sha256"]
    changed_parameter = call(bands, otf, modulation=np.array([[-1 + 0.5j]]))
    assert dict(changed_parameter.precision_provenance)["parameters_sha256"] != actual["parameters_sha256"]


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
    rejected(lambda: call(otf=transfer(value=complex(2**-140, 0)), wiener=2**-140), (PROFILE, "scale", "conversion"))
    assert call(otf=transfer(value=complex(2**-120, 0)), wiener=2**-120).image.dtype == np.float32
    q, v = arrays()
    maximum = np.finfo(np.float32).max
    q[0, 0, 1, 0, 0, 0] = maximum
    q[0, 0, 2, 0, 0, 0] = -1j * maximum
    bands = declare(q, v)
    before = snapshot(bands.quadratures, bands.noise_variance_factors)
    rejected(lambda: call(bands, modulation=np.zeros((1, 1))), (PROFILE, "coefficient", "overflow", "native", "finite"))
    assert snapshot(bands.quadratures, bands.noise_variance_factors) == before
    q[0, 0, 2, 0, 0, 0] = 0
    assert np.all(call(declare(q, v), modulation=np.zeros((1, 1))).image == 0)


def test_ordered_power_product_and_recombination_intermediate_overflow() -> None:
    q, v = arrays()
    v[...] = 2**-1000
    rejected(lambda: call(declare(q, v), modulation=np.array([[2**100]], dtype=np.float64)), (PROFILE, "power", "denominator", "finite", "overflow"))
    v[...] = 2**-100
    assert call(declare(q, v), modulation=np.array([[2**100]], dtype=np.float64)).image.dtype == np.float32
    maximum = np.finfo(np.float32).max
    q[0, 0, 0, 0, 0, 0] = maximum
    rejected(lambda: call(declare(q, np.ones_like(v)), transfer(value=complex(2**-120, 0)), wiener=2**-120), (PROFILE, "coefficient", "native", "finite", "overflow"))
    q[...] = 0
    q[0, 0, 1, 0, 0, 0] = maximum
    # H=1/2,w=1/4 gives scale8/13: p and n are finite, p+n is not.
    # The later factor1/2 must not conceal that required primitive overflow.
    rejected(lambda: call(declare(q, np.ones_like(v)), transfer(value=0.5), wiener=0.25), (PROFILE, "recombination", "native", "finite", "overflow"))


def test_final_image_overflow_is_distinct_from_finite_f64_accumulation() -> None:
    q, v = arrays(d=2, y=1, x=2)
    q[:, :, 0, 0, 0, 0] = np.finfo(np.float32).max
    bands = declare(q, v)
    before = snapshot(bands.quadratures)
    rejected(lambda: call(bands, modulation=np.zeros((2, 1))), (PROFILE, "image", "final", "float32"))
    assert snapshot(bands.quadratures) == before


class FailureBackend:
    __ua_domain__ = "numpy.scipy.fft"

    def __init__(self, failure: BaseException | None) -> None:
        self.failure = failure
        self.calls = 0

    def __ua_function__(self, method: Any, args: Any, kwargs: Any) -> Any:
        if method.__name__ != "ifftn":
            return NotImplemented
        self.calls += 1
        assert args[0].dtype == np.complex64
        assert kwargs.get("axes") == (0, 1, 2)
        assert kwargs.get("norm") == "forward" and kwargs.get("workers") == 1
        if self.failure is not None:
            raise self.failure
        return np.full(args[0].shape, complex(np.inf, 0), dtype=np.complex64)


def test_backend_exception_cause_nonfinite_result_and_interruption_are_public() -> None:
    bands, otf = declare(), transfer()
    before = snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples)
    original = RuntimeError("SP113 controlled existing FFT interface failure")
    backend = FailureBackend(original)
    with scipy.fft.set_backend(backend, only=True):
        error = rejected(lambda: call(bands, otf), (PROFILE, "fft", "transform"))
    assert backend.calls == 1 and error.__cause__ is original
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


def test_omitted_and_explicit_double_are_exact_same_environment_controls() -> None:
    # The only use of product preparation: a separate old-schema compatibility
    # control. It supplies neither a single-mode input nor scientific truth.
    raw = np.zeros((1, 1, 3, 2, 2, 4), dtype=np.float32)
    raw[:, :, :, :, :, :] = 2
    old = sr.prepare_bands(raw, dxy_um=1.0, dz_um=1.0, norders=2,
        background=0.0, lateral_zoom=1, axial_zoom=1, edge_pixels=0, equalize=False)
    otf = transfer()
    options: dict[str, Any] = dict(carriers_cyc_um=np.zeros((1, 2)), modulation=np.ones((1, 1)),
        wavelength_nm=500, numerical_aperture=1.0, immersion_index=1.0,
        wiener=0.5, suppress_singularities=False, output_taper="none")
    omitted = sr.reconstruct_known(old, otf, **options)
    explicit = sr.reconstruct_known(old, otf, precision="double", **options)
    assert type(omitted) is type(explicit) is sr.KnownReconstruction
    assert tuple(field.name for field in fields(omitted)) == tuple(field.name for field in fields(explicit))
    for field in fields(omitted):
        left, right = getattr(omitted, field.name), getattr(explicit, field.name)
        if isinstance(left, np.ndarray):
            assert left.dtype == right.dtype and left.shape == right.shape
            assert left.tobytes() == right.tobytes()
        else:
            assert left == right
    assert not hasattr(omitted, "precision_profile")
    rejected(lambda: sr.reconstruct_known(old, otf, precision=PROFILE, **options), ("bands", "precision", "PreparedBands32"))
    masquerade = replace(old, quadratures=old.quadratures.astype(np.complex64))
    rejected(lambda: sr.reconstruct_known(masquerade, otf, **options), ("quadrature", "complex128", "dtype"))
