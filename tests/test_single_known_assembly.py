"""Signed DC, conditional selected-default methods and controlled semantics.

The public SciPy backend protocol is an existing numerical interface, not a
production test seam. Controlled-transform tests qualify mapping only. They do
not qualify the default FFT backend's nontrivial numerical error or workspace.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import scipy.fft

import simrecon as sr

from .single_known_fixture import (
    HALF_SUB32, PI64, U32, U64, add, arrays, call, cardinal_fft_envelope,
    conjugate, cos_point_reference, cq, declare, multiply, pi_machin_interval,
    quarter_dft_reference, rn32, rn64, rotate, rounded_interval, sin_point_reference,
    rounding_margin32, sincos_point_program, sqrt_small_interval, to_complex, unit_scale,
)


def exact_quarter_dft(spectrum: Any) -> Any:
    """Independent positive, unnormalized sum with exact quarter roots.

    Only length1/2/4 axes are admitted, and the selected fixtures have small
    dyadic integer components. All exact sums are binary32-representable.
    """
    shape = spectrum.shape
    assert all(n in (1, 2, 4) for n in shape)
    roots = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)),
        (Fraction(-1), Fraction(0)), (Fraction(0), Fraction(-1)))
    output = np.empty(shape, dtype=np.complex64)
    for position in np.ndindex(shape):
        total = (Fraction(0), Fraction(0))
        for index in np.ndindex(shape):
            turns = sum((Fraction(k * j, n) for k, j, n in zip(index, position, shape, strict=True)), Fraction(0))
            quarter = turns * 4
            assert quarter.denominator == 1
            root = roots[quarter.numerator % 4]
            value = cq(complex(spectrum[index]))
            # Exact algebra here, with one final representability check.
            term = (value[0] * root[0] - value[1] * root[1], value[0] * root[1] + value[1] * root[0])
            total = total[0] + term[0], total[1] + term[1]
        assert rn32(total[0]) == total[0] and rn32(total[1]) == total[1]
        output[position] = to_complex(total)
    return output


class ExactBackend:
    __ua_domain__ = "numpy.scipy.fft"

    def __init__(self) -> None:
        self.spectra: list[Any] = []

    def __ua_function__(self, method: Any, args: Any, kwargs: Any) -> Any:
        if method.__name__ != "ifftn":
            return NotImplemented
        spectrum = args[0]
        assert type(spectrum) is np.ndarray and spectrum.dtype == np.complex64
        assert spectrum.ndim == 3
        assert kwargs.get("axes") == (0, 1, 2)
        assert kwargs.get("norm") == "forward"
        assert kwargs.get("workers") == 1
        assert kwargs.get("overwrite_x", False) is False
        self.spectra.append(spectrum.copy())
        return exact_quarter_dft(spectrum)


def test_dc_units_unnormalized_inverse_and_no_phase_or_direction_reaverage() -> None:
    q, v = arrays(d=2, y=1, x=2)
    # Alpha=1/(2*1*2*D)=1/8 is metadata; supplied Fourier values already
    # include it. No preparation-derived arrays or implied camera data exist.
    q[0, 0, 0, 0, 0, 0] = 3
    q[0, 1, 0, 0, 0, 0] = -5
    result = call(declare(q, v), modulation=np.zeros((2, 1)))
    assert np.all(result.image == -2)
    assert result.image.dtype == np.float32


def test_per_time_noise_reaches_each_public_dc_image_without_time_zero_reuse() -> None:
    q, v = arrays(t=2)
    q[:, 0, 0, 0, 0, 0] = 1
    v[0, 0], v[1, 0] = (1, 1), (2, 3)
    expected = (unit_scale((Fraction(1), Fraction(1)), 0), unit_scale((Fraction(2), Fraction(3)), 0))
    assert expected[0] != expected[1]
    result = call(declare(q, v))
    for t, scale in enumerate(expected):
        assert np.all(result.image[t] == float(scale))
    # Each image is a single c64 DC copied exactly by the transform, with zero
    # side data, exact f64 accumulation and an already-f32 final real component.


def test_positive_nyquist_zero_padding_and_centered_labels_with_controlled_transform() -> None:
    q, v = arrays(y=1, x=2)
    q[0, 0, 0, 1, 0, 1] = 1j
    bands = declare(q, v, lateral_zoom=2, axial_zoom=1, dxy_um=2.0, dz_um=3.0)
    backend = ExactBackend()
    with scipy.fft.set_backend(backend, only=True):
        result = call(bands, modulation=np.zeros((1, 1)))
    expected = np.zeros((2, 2, 4), dtype=np.complex64)
    expected[1, 0, 1] = 1j
    np.testing.assert_array_equal(backend.spectra[0], expected)
    # No negative Nyquist endpoint split, checkerboard or shifted inverse.
    np.testing.assert_array_equal(result.image[0], exact_quarter_dft(expected).real)
    np.testing.assert_array_equal(result.x_um, [-2, -1, 0, 1])
    np.testing.assert_array_equal(result.y_um, [-1, 0])
    np.testing.assert_array_equal(result.z_um, [-3, 0])
    assert bands.input_scale == 1 / 16


def test_all_axis_half_reflection_and_positive_axial_nyquist_with_controlled_transform() -> None:
    q, v = arrays(z=4, y=1, x=4)
    q[0, 0, 0, 1, 0, 1] = 1 + 2j
    q[0, 0, 0, 3, 0, 1] = -3 + 4j
    backend = ExactBackend()
    with scipy.fft.set_backend(backend, only=True):
        result = call(declare(q, v), modulation=np.zeros((1, 1)))
    expected = np.zeros((4, 1, 4), dtype=np.complex64)
    expected[1, 0, 1], expected[3, 0, 1] = 1 + 2j, -3 + 4j
    expected[3, 0, 3], expected[1, 0, 3] = 1 - 2j, -3 - 4j
    np.testing.assert_array_equal(backend.spectra[0], expected)
    np.testing.assert_array_equal(result.image[0], exact_quarter_dft(expected).real)
    q2, v2 = arrays(y=1, x=2)
    q2[0, 0, 0, 1, 0, 0] = 1j
    second = ExactBackend()
    with scipy.fft.set_backend(second, only=True):
        axial = call(declare(q2, v2, axial_zoom=2), modulation=np.zeros((1, 1)))
    expected_z = np.zeros((4, 1, 2), dtype=np.complex64)
    expected_z[1, 0, 0] = 1j
    np.testing.assert_array_equal(second.spectra[0], expected_z)
    np.testing.assert_array_equal(axial.image[0], exact_quarter_dft(expected_z).real)


def test_positive_lateral_y_nyquist_is_embedded_once_at_positive_lift() -> None:
    q, v = arrays(y=2, x=2)
    q[0, 0, 0, 0, 1, 0] = 1j
    backend = ExactBackend()
    with scipy.fft.set_backend(backend, only=True):
        result = call(declare(q, v, lateral_zoom=2), modulation=np.zeros((1, 1)))
    expected = np.zeros((2, 4, 4), dtype=np.complex64)
    expected[0, 1, 0] = complex(0, float(rn32(Fraction(4, 5))))
    np.testing.assert_array_equal(backend.spectra[0], expected)
    np.testing.assert_array_equal(result.image[0], exact_quarter_dft(expected).real)


def test_side_harmonic_reads_then_complex_product_and_positive_carrier_phase() -> None:
    q, v = arrays(z=4, y=1, x=4)
    q[0, 0, 1, 1, 0, 1] = 1 + 2j
    q[0, 0, 2, 3, 0, 1] = 3 - 1j
    # Unit carrier relative to 4um output has quarter-turn centered ramps.
    # Carrier1/4 cycles/um is noninteger and sign-sensitive.
    backend = ExactBackend()
    bands = declare(q, v)
    with scipy.fft.set_backend(backend, only=True):
        result = call(bands, carriers_cyc_um=np.array([[-0.25, 0.0]]), omit_order0=True)
    expected = np.zeros((4, 1, 4), dtype=np.complex64)
    expected[1, 0, 1] = 1 + 2j
    expected[3, 0, 1] = 1 + 3j  # i*(3-i)
    expected[3, 0, 3] = 1 - 2j
    expected[1, 0, 3] = -1 + 3j  # i*conj(3-i)
    # Center omission means only the side transform is requested.
    np.testing.assert_array_equal(backend.spectra[-1], expected)
    native = exact_quarter_dft(expected)
    # The finite ramp is RN32(exp(i*phase64)); actual libm evaluation near
    # quarter turns can have small residual components. This witness uses the
    # real sign at x=0 (phase exactly0) and x=-1 (strictly separated signs).
    np.testing.assert_array_equal(result.image[0, :, 0, 2], 2 * native[:, 0, 2].real)
    # Full pointwise phase accuracy awaits a certified scalar/libm enclosure.
    assert np.any(result.image < 0) and np.any(result.image > 0)


def test_widen_before_side_factor_two_and_accumulate_in_f64() -> None:
    maximum = np.finfo(np.float32).max
    q, v = arrays(y=1, x=2)
    q[0, 0, 0, 0, 0, 0] = -maximum
    q[0, 0, 1, 0, 0, 0] = maximum
    # c64 inverse/product are finite; side contribution2*maximum needs f64.
    result = call(declare(q, v))
    assert np.all(result.image == maximum)
    q2, v2 = arrays(d=2, y=1, x=2)
    q2[0, 0, 0, 0, 0, 0] = maximum
    q2[0, 0, 1, 0, 0, 0] = maximum / 2
    q2[0, 1, 0, 0, 0, 0] = -maximum
    q2[0, 1, 1, 0, 0, 0] = -maximum / 2
    # Direction-major accumulator temporarily reaches2*maximum, then cancels.
    assert np.all(call(declare(q2, v2)).image == 0)


def test_centered_positive_carrier_phase_sign_and_axial_invariance_on_dc() -> None:
    q, v = arrays(z=4, y=1, x=4)
    q[0, 0, 1, 0, 0, 0] = 1j
    bands = declare(q, v)
    for carrier, expected_sign in ((0.25, 1), (-0.25, -1)):
        result = call(bands, carriers_cyc_um=np.array([[carrier, 0.0]]), omit_order0=True)
        # Every side inverse is the constant i. At centered x=-1,
        # real(i*exp(-/+i*pi/2)) has the sign below; at x=0 it is0.
        assert expected_sign * float(result.image[0, 0, 0, 1]) > 0
        assert result.image[0, 0, 0, 2] == 0
        for z in range(1, 4):
            np.testing.assert_array_equal(result.image[0, z], result.image[0, 0])


def test_zero_and_weak_signed_dc_have_no_energy_floor_or_clipping() -> None:
    for amplitude in (0.0, -2**-140, 2**-140, -3.0):
        q, v = arrays(y=1, x=2)
        q[0, 0, 0, 0, 0, 0] = amplitude
        result = call(declare(q, v), modulation=np.zeros((1, 1)))
        assert np.all(result.image == np.float32(amplitude))


def test_default_cardinal_fft_nontrivial_signed_image_has_stage_separated_envelope(record_property: Any) -> None:
    """Conditional on the supplied source/binary/RNE method applicability.

    The default backend is exercised without substitution. Passing values do
    not establish the separate material-dependency assumptions in the report.
    """
    shape = (4, 1, 4)
    a = (Fraction(1) + Fraction(1, 2**23), Fraction(2) - Fraction(1, 2**22))
    b = (Fraction(-13, 4) + Fraction(1, 2**22), Fraction(4) + Fraction(1, 2**21))
    e = (Fraction(1) + Fraction(1, 2**23), Fraction(-3, 4))
    o = (Fraction(-1, 2), Fraction(1, 2**25))
    center_entries = {(1, 0, 1): a, (3, 0, 1): b,
        (3, 0, 3): conjugate(a), (1, 0, 3): conjugate(b)}
    exact_positive = e[0] - o[1], e[1] + o[0]
    exact_negative = e[0] + o[1], -e[1] + o[0]
    side_entries = {(1, 0, 1): exact_positive, (3, 0, 3): exact_negative}
    represented_side = {
        (1, 0, 1): add(e, rotate(o)),
        (3, 0, 3): add(conjugate(e), rotate(conjugate(o))),
    }
    coefficient_error = sum(
        (abs(exact[0] - represented_side[index][0]) + abs(exact[1] - represented_side[index][1])
         for index, exact in side_entries.items()), Fraction(0),
    )
    assert coefficient_error == Fraction(1, 2**24)
    # Sbar is fixed prior to the call, with no measured candidate maximum.
    center_sbar, side_sbar = Fraction(21), Fraction(4)
    assert sum((abs(re) + abs(im) for re, im in center_entries.values()), Fraction(0)) < center_sbar
    assert sum((abs(re) + abs(im) for re, im in represented_side.values()), Fraction(0)) < side_sbar
    center_fft = cardinal_fft_envelope(shape, center_sbar)
    side_fft = cardinal_fft_envelope(shape, side_sbar)
    before_accumulation = center_fft + 2 * (coefficient_error + side_fft)
    actual_term_sum = center_sbar + center_fft + 2 * (side_sbar + side_fft)
    accumulation = (2 * U64 / (1 - 2 * U64)) * actual_term_sum + 2 * Fraction(1, 2**1075)
    final_rounding = U32 * (actual_term_sum + accumulation) + HALF_SUB32
    complete_bound = before_accumulation + accumulation + final_rounding
    center_reference = quarter_dft_reference(shape, center_entries)
    side_reference = quarter_dft_reference(shape, side_entries)
    reference = {index: center_reference[index][0] + 2 * side_reference[index][0] for index in center_reference}
    q, v = arrays(z=4, y=1, x=4)
    q[0, 0, 0, 1, 0, 1], q[0, 0, 0, 3, 0, 1] = to_complex(a), to_complex(b)
    q[0, 0, 1, 1, 0, 1], q[0, 0, 2, 1, 0, 1] = to_complex(e), to_complex(o)
    result = call(declare(q, v))
    assert result.filtered_quadratures.tobytes() == q.tobytes()
    assert np.all(np.isfinite(result.image))
    actual = {index: Fraction(float(result.image[(0, *index)])) for index in reference}
    errors = {index: abs(actual[index] - expected) for index, expected in reference.items()}
    maximum_error = max(errors.values())
    assert maximum_error <= complete_bound
    assert min(actual.values()) < 0 < max(actual.values())
    rms = sqrt_small_interval(sum((error * error for error in errors.values()), Fraction(0)) / 16)
    conditions = [
        (abs(center_reference[index][0]) + 2 * abs(side_reference[index][0])) / abs(expected)
        for index, expected in reference.items() if expected
    ]
    record_property("sp113_default_cardinal_fft_metrics", {
        "shape": "4,1,4", "N": "16", "d": "4", "Sbar_center": "21", "Sbar_side": "4",
        "input_representation_error": "0", "scalar_filter_error": "0",
        "coefficient_error": str(coefficient_error), "phase_product_error": "0",
        "fft_center_bound": str(center_fft), "fft_side_bound": str(side_fft),
        "accumulation_bound": str(accumulation), "final_rounding_bound": str(final_rounding),
        "complete_bound": str(complete_bound), "reference_width": "0",
        "max_absolute_error": str(maximum_error), "rms_lower": str(rms[0]), "rms_upper": str(rms[1]),
        "interval_distance": str(maximum_error), "far_endpoint_upper_bound": str(maximum_error),
        "signed_minimum": str(min(actual.values())), "signed_maximum": str(max(actual.values())),
        "signal_scale": "29", "error_over_signal_scale": str(maximum_error / 29),
        "maximum_cancellation_condition": "infinite" if any(not value for value in reference.values()) else str(max(conditions)),
        "qualification": "conditional; dependency source/binary/RNE applicability remains separate",
    })


def test_default_cardinal_fft_enlarged_positive_nyquist_has_its_own_envelope(record_property: Any) -> None:
    shape = (2, 2, 4)
    entries = {(0, 0, 0): cq(Fraction(-1, 2)), (1, 0, 1): cq(1j)}
    reference = quarter_dft_reference(shape, entries)
    sbar = Fraction(3, 2)
    fft_bound = cardinal_fft_envelope(shape, sbar)
    q, v = arrays(y=1, x=2)
    q[0, 0, 0, 0, 0, 0], q[0, 0, 0, 1, 0, 1] = -0.5, 1j
    result = call(declare(q, v, lateral_zoom=2), modulation=np.zeros((1, 1)))
    assert np.all(np.isfinite(result.image))
    errors = [abs(Fraction(float(result.image[(0, *index)])) - expected[0]) for index, expected in reference.items()]
    # Only a center contribution: widening a c64 real component, adding to0
    # and casting back to f32 are exact. No phase/local/f64/final term is hidden.
    assert max(errors) <= fft_bound
    assert np.min(result.image) < 0 and np.max(result.image) > 0
    rms = sqrt_small_interval(sum((error * error for error in errors), Fraction(0)) / 16)
    record_property("sp113_default_enlarged_nyquist_metrics", {
        "shape": "2,2,4", "N": "16", "d": "4", "Sbar": "3/2",
        "coefficient_error": "0", "phase_product_error": "0", "accumulation_error": "0", "final_rounding_error": "0",
        "fft_bound": str(fft_bound), "reference_width": "0", "max_absolute_error": str(max(errors)),
        "rms_lower": str(rms[0]), "rms_upper": str(rms[1]), "interval_distance": str(max(errors)),
        "far_endpoint_upper_bound": str(max(errors)), "signed_minimum": str(Fraction(float(np.min(result.image)))),
        "signed_maximum": str(Fraction(float(np.max(result.image)))), "cancellation_condition": "3 (at the smallest |reference|=1/2)",
        "signal_scale": "3/2", "error_over_signal_scale": str(max(errors) / sbar),
        "qualification": "conditional; dependency source/binary/RNE applicability remains separate",
    })


def test_default_cardinal_axial_mode_with_full_signed_noninteger_carrier_ramp(record_property: Any) -> None:
    """Full pointwise oracle; source/binary FFT and primitive applicability held."""
    multipliers = (Fraction(-1, 2), Fraction(-1, 4), Fraction(0), Fraction(1, 4), Fraction(1, 2))
    program = {value: sincos_point_program(value) for value in multipliers}
    consumed: dict[Fraction, tuple[Fraction, Fraction]] = {}
    nonzero_bin_margins: list[Fraction] = []
    for value, components in program.items():
        c, s = (rounded_interval(component, bits=24) for component in components)
        assert c[0] == c[1] and s[0] == s[1], "independent consumed ramp bin is unresolved"
        for source, represented in zip(components, (c[0], s[0]), strict=True):
            margin = rounding_margin32(source, represented)
            if represented:
                nonzero_bin_margins.append(margin)
        consumed[value] = c[0], s[0]
    root = sqrt_small_interval(Fraction(2))
    eighth = root[0] / 2, root[1] / 2
    pi_interval = pi_machin_interval()
    pi_error = max(abs(PI64 - pi_interval[0]), abs(PI64 - pi_interval[1]))
    a = (Fraction(1), Fraction(1, 2))
    axial_values = (a, rotate(a), (-a[0], -a[1]), (-rotate(a)[0], -rotate(a)[1]))
    # Each source-plan intermediate is0 or a quarter rotation of the sole
    # dyadic coefficient a. Its components are integer multiples1/2,<=1;
    # every actual cardinal add/subtract/rotation is exact normal-or-zero.
    # This is a fixture-specific zero FFT term, conditional on the supplied
    # actual source/binary plan assumptions: N16,d4,Sbar3/2.
    for sign in (1, -1):
        x_multipliers = tuple(sign * value for value in (Fraction(-1, 2), Fraction(-1, 4), Fraction(0), Fraction(1, 4)))
        expected: dict[tuple[int, int, int], Fraction] = {}
        reference: dict[tuple[int, int, int], tuple[Fraction, Fraction]] = {}
        stage_bounds: list[Fraction] = []
        phase_bounds: list[Fraction] = []
        library_bounds: list[Fraction] = []
        conversion_bounds: list[Fraction] = []
        local_bounds: list[Fraction] = []
        for z, u in enumerate(axial_values):
            for x, value in enumerate(x_multipliers):
                c, s = consumed[value]
                product = multiply(u, (c, s))
                expected[z, 0, x] = 2 * product[0]
                if not value:
                    ideal_c, ideal_s = (Fraction(1), Fraction(1)), (Fraction(0), Fraction(0))
                elif abs(value) == Fraction(1, 2):
                    ideal_c = Fraction(0), Fraction(0)
                    sine = Fraction(1) if value > 0 else Fraction(-1)
                    ideal_s = sine, sine
                else:
                    ideal_c = eighth
                    ideal_s = eighth if value > 0 else (-eighth[1], -eighth[0])
                c_terms = (u[0] * ideal_c[0], u[0] * ideal_c[1])
                s_terms = (u[1] * ideal_s[0], u[1] * ideal_s[1])
                reference[z, 0, x] = 2 * (min(c_terms) - max(s_terms)), 2 * (max(c_terms) - min(s_terms))
                cosine_source, sine_source = program[value]
                cosine_math = cos_point_reference(abs(value))
                sine_math = sin_point_reference(value)
                c_library = max(abs(cosine_source[0] - cosine_math[1]), abs(cosine_source[1] - cosine_math[0]))
                s_library = max(abs(sine_source[0] - sine_math[1]), abs(sine_source[1] - sine_math[0]))
                c_conversion = max(abs(c - cosine_source[0]), abs(c - cosine_source[1]))
                s_conversion = max(abs(s - sine_source[0]), abs(s - sine_source[1]))
                phase = 2 * (abs(u[0]) + abs(u[1])) * abs(value) * pi_error
                library = 2 * (abs(u[0]) * c_library + abs(u[1]) * s_library)
                conversion = 2 * (abs(u[0]) * c_conversion + abs(u[1]) * s_conversion)
                local = 2 * abs(product[0] - (u[0] * c - u[1] * s))
                phase_bounds.append(phase)
                library_bounds.append(library)
                conversion_bounds.append(conversion)
                local_bounds.append(local)
                stage_bounds.append(phase + library + conversion + local)
        q, v = arrays(z=4, y=1, x=4)
        q[0, 0, 1, 1, 0, 0] = to_complex(a)
        result = call(declare(q, v), carriers_cyc_um=np.array([[sign * 0.125, 0.0]]), omit_order0=True)
        assert np.all(np.isfinite(result.image))
        actual = {index: Fraction(float(result.image[(0, *index)])) for index in expected}
        assert actual == expected
        distances: list[Fraction] = []
        far: list[Fraction] = []
        for index, value in actual.items():
            lower, upper = reference[index]
            distances.append(max(lower - value, value - upper, Fraction(0)))
            far.append(max(abs(value - lower), abs(value - upper)))
        width = max(upper - lower for lower, upper in reference.values())
        assert max(far) <= max(stage_bounds) + width
        rms_lower = sqrt_small_interval(sum((value * value for value in distances), Fraction(0)) / 16)[0]
        rms_upper = sqrt_small_interval(sum((value * value for value in far), Fraction(0)) / 16)[1]
        record_property(f"sp113_full_ramp_{sign}", {
            "shape": "4,1,4", "N": "16", "d": "4", "Sbar": "3/2", "input_representation_error": "0",
            "pi_constant_bound": str(pi_error), "phase_argument_rounding_error": "0",
            "minimum_nonzero_ramp_bin_margin": str(min(nonzero_bin_margins)),
            "phase_pi_image_bound": str(max(phase_bounds)), "library_image_bound": str(max(library_bounds)),
            "ramp_conversion_image_bound": str(max(conversion_bounds)), "local_product_image_bound": str(max(local_bounds)),
            "fft_error": "0 (all selected plan intermediates proved exact)", "f64_accumulation_error": "0", "final_rounding_error": "0",
            "reference_width": str(width), "interval_distance": str(max(distances)), "far_endpoint_upper_bound": str(max(far)),
            "max_absolute_error_lower": str(max(distances)), "max_absolute_error_upper": str(max(far)),
            "rms_lower": str(rms_lower), "rms_upper": str(rms_upper), "signed_minimum": str(min(actual.values())),
            "signed_maximum": str(max(actual.values())), "signal_scale": "3", "far_error_over_signal_scale": str(max(far) / 3),
            "qualification": "conditional; actual FFT/cexp/sincos source/binary/RNE correspondence remains separate",
        })


def test_native_complex_filter_to_default_fft_and_carrier_is_one_public_composition(record_property: Any) -> None:
    # At native x1/4, carrier-1/8 gives object K1/8. Hself=(5/4)*(3+4i),
    # other(-1) at q0 has norm5, other0 at q1/8 has norm45/8. With w1/2,
    # the exact denominator is6141/64, in the prescribed signed order.
    p_reference = Fraction(240, 6141), Fraction(-320, 6141)
    p64 = rn64(p_reference[0]), rn64(p_reference[1])
    p32 = rn32(p64[0]), rn32(p64[1])
    assert p_reference != (Fraction(108, 2833), Fraction(-144, 2833))
    scalar_error = 2 * (abs(p64[0] - p_reference[0]) + abs(p64[1] - p_reference[1]))
    scale_conversion = 2 * (abs(p32[0] - p64[0]) + abs(p32[1] - p64[1]))
    pi_interval = pi_machin_interval()
    pi_error = max(abs(PI64 - pi_interval[0]), abs(PI64 - pi_interval[1]))
    root = sqrt_small_interval(Fraction(2))
    eighth = root[0] / 2, root[1] / 2
    expected: dict[tuple[int, int, int], Fraction] = {}
    reference: dict[tuple[int, int, int], tuple[Fraction, Fraction]] = {}
    bounds: list[Fraction] = []
    for x, value in enumerate((Fraction(1, 2), Fraction(1, 4), Fraction(0), Fraction(-1, 4))):
        u, ideal_u = p32, p_reference
        for _ in range(x):
            u, ideal_u = rotate(u), rotate(ideal_u)
        c_source, s_source = sincos_point_program(value)
        c_interval, s_interval = rounded_interval(c_source, bits=24), rounded_interval(s_source, bits=24)
        assert c_interval[0] == c_interval[1] and s_interval[0] == s_interval[1]
        c, s = c_interval[0], s_interval[0]
        rounding_margin32(c_source, c)
        rounding_margin32(s_source, s)
        product = multiply(u, (c, s))
        if value == Fraction(1, 2):
            ideal_c, ideal_s = (Fraction(0), Fraction(0)), (Fraction(1), Fraction(1))
        elif not value:
            ideal_c, ideal_s = (Fraction(1), Fraction(1)), (Fraction(0), Fraction(0))
        else:
            ideal_c = eighth
            ideal_s = eighth if value > 0 else (-eighth[1], -eighth[0])
        c_terms = (ideal_u[0] * ideal_c[0], ideal_u[0] * ideal_c[1])
        s_terms = (ideal_u[1] * ideal_s[0], ideal_u[1] * ideal_s[1])
        lower, upper = 2 * (min(c_terms) - max(s_terms)), 2 * (max(c_terms) - min(s_terms))
        c_math, s_math = cos_point_reference(abs(value)), sin_point_reference(value)
        library = 2 * (abs(u[0]) * max(abs(c_source[0] - c_math[1]), abs(c_source[1] - c_math[0]))
            + abs(u[1]) * max(abs(s_source[0] - s_math[1]), abs(s_source[1] - s_math[0])))
        ramp_conversion = 2 * (abs(u[0]) * max(abs(c - c_source[0]), abs(c - c_source[1]))
            + abs(u[1]) * max(abs(s - s_source[0]), abs(s - s_source[1])))
        phase = 2 * (abs(u[0]) + abs(u[1])) * abs(value) * pi_error
        local = 2 * abs(product[0] - (u[0] * c - u[1] * s))
        bounds.append(scalar_error + scale_conversion + library + ramp_conversion + phase + local)
        for z in range(2):
            for y in range(2):
                expected[z, y, x], reference[z, y, x] = 2 * product[0], (lower, upper)
    q, v = arrays()
    q[0, 0, 1, 0, 0, 1], q[0, 0, 2, 0, 0, 1] = 0.5, -0.5j
    source = np.empty((2, 8, 8), dtype=np.complex128)
    for r in range(8):
        source[:, r, :] = (r + 1) * (3 + 4j)
    otf = sr.declare_otf(source, layout="radial", dkr_cyc_um=1.0, dkz_cyc_um=1.0)
    result = call(declare(q, v), otf, carriers_cyc_um=np.array([[-0.125, 0.0]]))
    assert np.all(np.isfinite(result.image))
    actual = {index: Fraction(float(result.image[(0, *index)])) for index in expected}
    assert actual == expected
    distances = [max(lo - actual[index], actual[index] - hi, Fraction(0)) for index, (lo, hi) in reference.items()]
    far = [max(abs(actual[index] - lo), abs(actual[index] - hi)) for index, (lo, hi) in reference.items()]
    width = max(hi - lo for lo, hi in reference.values())
    assert max(far) <= max(bounds) + width
    assert min(actual.values()) < 0 < max(actual.values())
    rms = sqrt_small_interval(sum((error * error for error in far), Fraction(0)) / 16)
    rms_lower = sqrt_small_interval(sum((error * error for error in distances), Fraction(0)) / 16)[0]
    record_property("sp113_native_filter_full_composition", {
        "shape": "2,2,4", "N": "16", "d": "4", "Sbar": str(abs(p32[0]) + abs(p32[1])),
        "input_representation_error": "0", "interpolation_error": "0 (dyadic affine weights)",
        "scalar_image_bound": str(scalar_error), "scale_conversion_image_bound": str(scale_conversion),
        "complete_bound": str(max(bounds)), "reference_width": str(width), "interval_distance": str(max(distances)),
        "far_endpoint_upper_bound": str(max(far)), "max_absolute_error_lower": str(max(distances)), "max_absolute_error_upper": str(max(far)),
        "rms_lower": str(rms_lower), "rms_upper": str(rms[1]),
        "fft_error": "0 (single coefficient and exact quarter rotations)", "f64_accumulation_error": "0", "final_rounding_error": "0",
        "signed_minimum": str(min(actual.values())), "signed_maximum": str(max(actual.values())),
        "signal_scale": "1", "error_over_signal_scale": str(max(far)), "maximum_cancellation_condition": "7",
        "qualification": "conditional; actual Pythagorean/zero-axis hypot, selected ramp and cardinal FFT source/binary/RNE correspondence remains separate",
    })
