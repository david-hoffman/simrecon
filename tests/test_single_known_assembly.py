"""Signed DC accuracy and exact controlled-transform assembly semantics.

The public SciPy backend protocol is an existing numerical interface, not a
production test seam. Controlled-transform tests qualify mapping only. They do
not qualify the default FFT backend's nontrivial numerical error or workspace.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import scipy.fft

from .single_known_fixture import arrays, call, cq, declare, rn32, to_complex


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
