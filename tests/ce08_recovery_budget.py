"""Conditional binary64 error propagation for the fixed CE08 recovery case."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ce08_error_budget import gamma, norm
from ce08_finite_math import Array, read_band, sample, signed


def bounds(raw: Array, h: Array, p: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    n = 256
    eta = gamma(64 * n * math.ceil(math.log2(2 * n)) + 32 * n)
    corrected = 2 * (raw.astype(float) - 10) / (4 * n)
    # The row absolute values are <=1. Euclidean DFT norm sqrt(N),
    # five phase rows; this covers product FFT and compensated oracle.
    eb = eta * 5 * math.sqrt(n) * norm(corrected)
    fit_errors = []
    overlap_errors = []
    energy = []
    for build, fitted in zip(reference["builds"], reference["fits"], strict=True):
        nx, ny = (norm(v) for v in build["spatial"])
        ex = math.sqrt(2 * n) * eb + eta * nx
        ey = math.sqrt(2 * n) * eb + eta * ny
        esx = 2 * nx * ex + ex**2 + gamma(8 * n) * nx**2
        esy = 2 * ny * ey + ey**2 + gamma(8 * n) * ny**2
        ec = nx * ey + ny * ex + ex * ey + gamma(16 * n) * nx * ny
        assert nx**2 > esx and ny**2 > esy
        assert abs(nx**2 - ny**2) > esx + esy
        ea = (ec + abs(fitted["forward"]) * esx) / (nx**2 - esx)
        ea += eta * abs(fitted["forward"])
        fit_errors.append(ea)
        overlap_errors.append(max(ex, ey))
        energy.append(
            {
                "SX": nx**2,
                "SY": ny**2,
                "energy_gap": abs(nx**2 - ny**2),
                "SX_error": esx,
                "SY_error": esy,
                "cross_error": ec,
            }
        )

    a = np.r_[1 + 0j, reference["modulation"]]
    ea = np.r_[0.0, fit_errors]
    band = reference["bands"]
    filtered_error_sum = 0.0
    maximum_filter_error = 0.0
    min_den = math.inf
    max_scale = 0.0
    for m in range(3):
        for iz, iy, ix in np.ndindex((4, 8, 8)):
            qz, qy, qx = signed(iz, 4), signed(iy, 8) / 8, signed(ix, 8) / 8
            if abs(qz) > 1 or math.hypot(qx, qy) > 0.5:
                continue
            obj = np.array((qx + m / 8, qy))
            hh = sample(h, m, qx, qy, qz)
            denominator = p["filtering"]["wiener"] ** 2
            ed = 0.0
            for order in range(-2, 3):
                shifted = obj - np.array((order / 8, 0))
                if order == m or np.linalg.norm(shifted) < 0.5:
                    other_h = (
                        hh
                        if order == m
                        else sample(h, abs(order), float(shifted[0]), float(shifted[1]), qz)
                    )
                    denominator += abs(a[abs(order)] * other_h) ** 2
                    ed += abs(other_h) ** 2 * (
                        2 * abs(a[abs(order)]) * ea[abs(order)] + ea[abs(order)] ** 2
                    )
            assert denominator > ed
            numerator = abs(a[m] * hh)
            scale = numerator / denominator
            es = abs(hh) * ea[m] / (denominator - ed)
            es += numerator * ed / (denominator * (denominator - ed))
            es += eta * (1 + scale)
            data = abs(read_band(band, m, qz, signed(iy, 8), signed(ix, 8)))
            error = math.sqrt(2) * eb * (scale + es) + data * es
            # Factor4 covers side E/O recombination/reflection and the
            # positive-Nyquist lift. It is conservative for the active modes.
            error *= 4
            filtered_error_sum += error * (1 if m == 0 else 2)
            maximum_filter_error = max(maximum_filter_error, error)
            min_den = min(min_den, denominator)
            max_scale = max(max_scale, scale)
    image_error = filtered_error_sum + eta * 5 * math.sqrt(1024) * norm(reference["filtered"])
    assert 0 < image_error < 0.001
    return {
        "eta": eta,
        "bands_atol": eb,
        "overlap_atol": max(overlap_errors),
        "modulation_atol": max(fit_errors),
        "filtered_atol": maximum_filter_error,
        "image_atol": image_error,
        "mode_atol": image_error + eta * max(1.0, norm(reference["image"])),
        "minimum_denominator": min_den,
        "maximum_native_scale": max_scale,
        "energies": energy,
    }


def physical_observer_bounds(p: dict[str, Any], h: Array) -> dict[str, Any]:
    """Bound TWO regenerated observers, independently of product bounds().

    Fixed coefficient/coordinate inputs are binary64 values. Each real sin,
    cos or complex exponential has absolute error <=8u on the finite angles
    here; hypot has relative error <=gamma(8). Algebraic reassociation and
    real-trigonometric synthesis are included through absolute term sums.
    Complex product/reduction costs use eight real operations per term.
    These are conditional libm bounds, not claims about arbitrary platforms.
    """
    u = 2.0**-53
    source = p["source"]
    coefficients = [((0, 0, 0), complex(source["density_dc"]))]
    for kx, ky, kz, re, im in source["positive_modes_kxyz_real_imag"]:
        coefficients.extend((((kx, ky, kz), complex(re, im)), ((-kx, -ky, -kz), complex(re, -im))))
    amplitudes = np.array([1, *(complex(*v) for v in source["side_modulation_pairs"])])
    density_abs = math.fsum(abs(c) for _, c in coefficients)
    illumination_abs = 1 + 2 * math.fsum(abs(a) for a in amplitudes[1:])
    hmax = float(np.max(np.abs(h)))
    slope = float(np.max(np.abs(np.diff(h, axis=1)))) / 0.125
    # Four-vertex interpolation, including complex multiply/add and radial
    # hypot error. Integer axial arguments and dyadic lattice coordinates
    # are exact here. The piecewise-linear table is globally Lipschitz.
    interpolation_error = gamma(32) * hmax + slope * gamma(8) * 0.5
    truth_error = 0.0
    for k, c in coefficients:
        angle = 2 * math.pi * (abs(k[0]) / 8 * 4 + abs(k[1]) / 8 * 4 + abs(k[2]) / 4 * 2)
        truth_error += abs(c) * (gamma(16) * angle + 8 * u)
    truth_error += gamma(8 * len(coefficients) + 16) * density_abs

    def detected_error(items: list[tuple[tuple[int, int, int], complex]]) -> tuple[float, float]:
        total, term_error, count = 0.0, 0.0, 0
        for m in range(-2, 3):
            for k, c in items:
                qx, qy, qz = (k[0] - m) / 8, k[1] / 8, k[2] / 4
                if math.hypot(qx, qy) > 0.5 or abs(k[2]) > 1:
                    continue
                ca = abs(c) * abs(amplitudes[abs(m)])
                angle = 2 * math.pi * (abs(qx) * 4 + abs(qy) * 4 + abs(qz) * 2)
                phase = abs(m) * 2 * math.pi * 4 / 5
                phase_error = gamma(16) * (angle + phase) + 16 * u
                total += ca * hmax
                term_error += ca * (
                    interpolation_error + (hmax + interpolation_error) * (phase_error + gamma(16))
                )
                count += 1
        return total, term_error + gamma(8 * count + 16) * total

    contrast_abs, contrast_error = detected_error(coefficients)
    reference_abs, reference_error = detected_error(
        [((0, 0, 0), complex(source["reference_density"]))]
    )
    raw_abs = 10 + 0.4 * density_abs * illumination_abs
    raw_error = 0.4 * contrast_error + gamma(4) * raw_abs
    reference_counts_error = 0.8 * reference_error + gamma(2) * 0.8 * reference_abs
    specimen_counts_error = 0.8 * (reference_error + contrast_error)
    specimen_counts_error += gamma(4) * 0.8 * (reference_abs + contrast_abs)

    # Conventional regeneration starts at EXACT frozen float32 samples,
    # unlike the physical acquisition. Bound normalized forward coefficients
    # then the 256 nonzero embedded inverse terms. Separate direct-sum
    # twiddle/reduction envelopes are used, not product FFT bounds().
    def transform_error(shape: tuple[int, ...]) -> float:
        error = sum(
            gamma(8 * length) + 8 * u + gamma(16) * 2 * math.pi * (length - 1) ** 2 / length
            for length in shape
        )
        return error / (1 - error)

    native_abs = density_abs * illumination_abs + 2 * raw_abs * 2**-24 / 0.8
    native_error = gamma(16) * 2.5 * (raw_abs + 10)
    forward_error, inverse_error = transform_error((4, 8, 8)), transform_error((4, 16, 16))
    conventional_error = 256 * (
        native_error + (forward_error + inverse_error + forward_error * inverse_error) * native_abs
    )

    power_errors, response_errors = [], []
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in source["positive_modes_kxyz_real_imag"])]
    for kx, ky, kz in keys:
        terms, errors = [], []
        for m in range(-2, 3):
            qx, qy = (kx - m) / 8, ky / 8
            if math.hypot(qx, qy) < 0.5:
                product = abs(amplitudes[abs(m)] * sample(h, abs(m), qx, qy, kz))
                ep = abs(amplitudes[abs(m)]) * interpolation_error
                ep += gamma(8) * (product + ep)
                terms.append(product**2)
                errors.append(2 * product * ep + ep**2 + gamma(8) * product**2)
        power = math.fsum(terms)
        power_error = math.fsum(errors) + gamma(2 * len(terms) + 4) * power
        w2 = p["filtering"]["wiener"] ** 2
        denominator = power + w2
        denominator_error = power_error + gamma(1) * w2 + gamma(1) * denominator
        assert denominator > denominator_error
        response = power / denominator
        response_error = (power_error + response * denominator_error) / (
            denominator - denominator_error
        ) + gamma(2) * response
        power_errors.append(2 * power_error)
        response_errors.append(2 * response_error)
    return {
        "truth": 2 * truth_error,
        "unquantized_raw": 2 * raw_error,
        "reference_corrected_counts": 2 * reference_counts_error,
        "specimen_corrected_counts": 2 * specimen_counts_error,
        "conventional": 2 * conventional_error,
        "mode_power": np.array(power_errors),
        "ideal_response": np.array(response_errors),
        "single_raw": raw_error,
        "interpolation_error": interpolation_error,
    }


def assert_float32_rounding(
    quantized: Array, regenerated: Array, observer_error: float | Array
) -> float:
    """Prove exact frozen rounding using a TWO-observer midpoint margin.

    Float32 adjacent-value midpoints are exactly representable in float64.
    The distance must exceed the full two-observer forward-error envelope;
    exact byte equality is then a justified representation assertion. A
    midpoint/uncertainty conflict fails instead of choosing another sample.
    """
    assert quantized.dtype == np.dtype("float32")
    assert regenerated.shape == quantized.shape
    lower = (np.nextafter(quantized, np.float32(-np.inf)).astype(float) + quantized) / 2
    upper = (np.nextafter(quantized, np.float32(np.inf)).astype(float) + quantized) / 2
    margin = np.minimum(regenerated - lower, upper - regenerated)
    assert np.all(margin > observer_error), "unresolved float32 rounding midpoint"
    np.testing.assert_array_equal(regenerated.astype(np.float32), quantized)
    return float(np.min(margin))


def assert_transfer_regeneration(h: Array, p: dict[str, Any]) -> float:
    """Qualify analytic radial-cell rounding; axial dyadic products are exact.

    The four nonzero radial cells have v=0,1/4,1/2,3/4 exactly. Conditional
    acos and sqrt absolute errors <=8u*(1+abs(value)); cancellation is
    bounded by absolute terms, not by the small final difference. Remaining
    radial cells and axial zeros are structurally exact zeros. Axial factors
    are signed powers of two, so no final complex64 rounding is incurred.
    """
    u = 2.0**-53
    radial, errors = [], []
    for index in range(4):
        v = index / 4
        angle, root = math.acos(v), math.sqrt(1 - v * v)
        value = 2 * (angle - v * root) / math.pi
        error = 2 / math.pi * (
            8 * u * (1 + abs(angle))
            + v * 8 * u * (1 + abs(root))
            + gamma(16) * (abs(angle) + abs(v * root))
        ) + gamma(8) * abs(value)
        radial.append(value)
        errors.append(2 * error)
    minimum = assert_float32_rounding(
        np.real(h[0, :4, 0]).astype(np.float32), np.array(radial), np.array(errors)
    )
    assert h.shape == tuple(p["transfer"]["shape_ORK"])
    hz = np.array([1, 0.25 + 0.125j, 0, 0.25 - 0.125j])
    cells = np.r_[np.real(h[0, :4, 0]), np.zeros(h.shape[1] - 4)]
    for m, r, z in np.ndindex(h.shape):
        assert h[m, r, z] == cells[r] * hz[z % 4]
    np.testing.assert_array_equal(h, h.astype(np.complex64).astype(np.complex128))
    return minimum
