"""Conditional binary64 propagation for the frozen D3 finite experiment."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ce08_finite_math import Array, read_band
from ce08_recovery_large_model import carriers, cutoffs, powers, sample


def gamma(n: int) -> float:
    u = 2**-53
    assert n * u < 1
    return n * u / (1 - n * u)


def norm(v: Array) -> float:
    return float(np.linalg.norm(v.ravel()))


def bounds(raw: Array, h: Array, p: dict[str, Any], ref: dict[str, Any]) -> dict[str, Any]:
    n = 24 * 24 * 8
    count = 64 * (48 + 48 + 8) * math.ceil(math.log2(2 * n)) + 32 * (48 + 48 + 8)
    eta = gamma(count)
    # Combined oracle+product envelope. Scalar phase rows <=1; DFT operator
    # norm sqrt(N); alpha includes D. Norm over all directions is conservative
    # for each individual direction/slot. Camera subtraction contributes eta.
    corrected = 2 * (raw.astype(float) - 10) / (n * 4 * 3)
    eb = eta * 5 * math.sqrt(n) * norm(corrected)
    errors, energies, overlaps = [], [], []
    for build in ref["builds"]:
        nx, ny = (norm(v) for v in build["spatial"])
        ex, ey = math.sqrt(2 * n) * eb + eta * nx, math.sqrt(2 * n) * eb + eta * ny
        esx = 2 * nx * ex + ex**2 + gamma(8 * n) * nx**2
        esy = 2 * ny * ey + ey**2 + gamma(8 * n) * ny**2
        ec = nx * ey + ny * ex + ex * ey + gamma(16 * n) * nx * ny
        assert nx**2 > esx and ny**2 > esy and abs(nx**2 - ny**2) > esx + esy
        ea = (ec + abs(build["forward"]) * esx) / (nx**2 - esx) + eta * abs(build["forward"])
        errors.append(ea)
        overlaps.append(max(ex, ey))
        energies.append(
            {
                "SX": nx**2,
                "SY": ny**2,
                "gap": abs(nx**2 - ny**2),
                "SX_error": esx,
                "SY_error": esy,
                "cross_error": ec,
            }
        )
    ea = np.column_stack((np.zeros(3), np.array(errors).reshape(3, 2)))
    a = np.column_stack((np.ones(3), ref["modulation"]))
    k = carriers(p)
    _, cuts = cutoffs(p)
    error_sum = 0.0
    maximum_error, min_den, max_scale = 0.0, math.inf, 0.0
    for d in range(3):
        for m, cut in enumerate(cuts):
            # Full signed enumeration overbounds order0's half storage and
            # explicitly preserves positive Nyquist. Coefficient L1 bounds
            # directly bound every unnormalized inverse output sample.
            for iy in range(-11, 13):
                for ix in range(-11, 13):
                    q = np.array((ix / 24, iy / 24))
                    if np.linalg.norm(q) > 0.5:
                        continue
                    for iz in range(-cut, cut + 1):
                        hh = sample(h, m, float(q[0]), float(q[1]), iz)
                        power, terms = powers(h, k, a, d, m, q, iz)
                        den = power + p["filtering"]["wiener"] ** 2
                        ed = 0.0
                        for e, order, _ in terms:
                            other = q + m * k[d] - order * k[e]
                            other_h = (
                                hh
                                if (e, order) == (d, m)
                                else sample(h, abs(order), float(other[0]), float(other[1]), iz)
                            )
                            ed += abs(other_h) ** 2 * (
                                2 * abs(a[e, abs(order)]) * ea[e, abs(order)]
                                + ea[e, abs(order)] ** 2
                            )
                        ed += eta * den
                        assert den > ed
                        numerator = abs(a[d, m] * hh)
                        scale = numerator / den
                        es = (
                            abs(hh) * ea[d, m] / (den - ed)
                            + numerator * ed / (den * (den - ed))
                            + eta * (1 + scale)
                        )
                        data = abs(read_band(ref["bands"][d], m, iz, iy, ix))
                        error = 4 * (math.sqrt(2) * eb * (scale + es) + data * es)
                        error_sum += error * (1 if m == 0 else 2)
                        maximum_error = max(maximum_error, error)
                        min_den, max_scale = min(min_den, den), max(max_scale, scale)
    image = error_sum + eta * 15 * math.sqrt(48 * 48 * 8) * norm(ref["filtered"])
    density = 3 * image
    mode = density + eta * max(1, norm(ref["density_image"]))
    assert 0 < mode < 0.001
    return {
        "eta": eta,
        "envelope_operation_count": count,
        "bands_atol": eb,
        "overlap_atol": max(overlaps),
        "modulation_atol": max(errors),
        "filtered_atol": maximum_error,
        "workflow_image_atol": image,
        "density_image_atol": density,
        "mode_atol": mode,
        "minimum_denominator": min_den,
        "maximum_native_scale": max_scale,
        "energies": energies,
    }


# Supplemental observer arithmetic only. The bounds() function above and its
# dependencies are preserved byte-for-byte. None of these tolerances is used
# for a product/stage comparison or to change a frozen observation.
def observer_bounds(p: dict[str, Any], h: Array, raw: Array) -> dict[str, Any]:
    """Derive D3 array-specific forward/observer errors, independently of eta.

    Assumptions: round-to-nearest binary64 elementary arithmetic, no underflow,
    and sin/cos/complex-exp components accurate to8u absolutely for |arg|<320;
    acos/sqrt likewise to8u on the twelve declared nonnegative radial cells.
    These conditional libm assumptions permit complex exponential versus real
    sine/cosine synthesis and different finite addition orders. They do not
    promise bitwise platform identity or unique raw float32 rounding.
    """
    from ce08_recovery_large_model import acquisition_bounds, source_modes

    u = 2**-53
    modes = source_modes(p)
    # Component L1 magnitudes avoid depending on rounded complex hypot values.
    mass = sum(abs(c.real) + abs(c.imag) for _, c in modes) * (1 + gamma(2 * len(modes)))
    reference_mass = p["source"]["reference_density"]
    a = [1 + 0j, *(complex(*v) for v in p["source"]["side_modulation_pairs"])]
    al1 = [abs(v.real) + abs(v.imag) for v in a]
    illumination = al1[0] + 2 * sum(al1[1:])
    maximum_bin_sum = max(sum(abs(v) for v in k) for k, _ in modes)
    theta_truth = math.pi * maximum_bin_sum
    truth_one = mass * (gamma(16) * (1 + theta_truth) + 16 * u + gamma(16 * len(modes) + 32))
    # <=32 scalar operations cover resolved b, sin/cos, k/24 and signed shifts;
    # each sin/cos has absolute error<=8u. Frequency units are cycles/um.
    b = 1 / (2 * p["carrier"]["linespacing_um"])
    max_frequency = max((abs(k[0]) + abs(k[1])) / 24 for k, _ in modes)
    eq = gamma(32) * (1 + max_frequency + 2 * b)
    hmax = float(np.max(abs(h)))
    # The radial interpolant, extended by zero at/outside R, is continuous.
    # Every axial cell has H(R)=0; hence support toggles at R are covered by
    # this Lipschitz bound instead of assuming identical radius decisions.
    lip = float(np.max(abs(h[:, 1:, :] - h[:, :-1, :]))) * 24
    eh = lip * (math.sqrt(2) * eq + gamma(8)) + gamma(32) * 2 * hmax
    theta_native = 2 * math.pi * (12 + 0.5)  # |qx|,|qy|<=.5; |kz/8|<=1/8
    theta_phase = 2 * math.pi * 2 * 4 / 5
    phase_one = 2 * math.pi * 24 * eq + gamma(16) * (1 + theta_native + theta_phase) + 32 * u
    # At most25 signed source terms times5 illumination orders;64 operations
    # per complex contribution generously cover4 complex products and sums.
    forward_factor = illumination * (eh + hmax * (phase_one + gamma(64 * len(modes) * 5 + 64)))
    contrast_one = mass * forward_factor
    reference_one = reference_mass * forward_factor
    raw_one = 0.4 * contrast_one + gamma(4) * (10 + 0.4 * mass * illumination)

    # Conventional is a linear observer of the EXACT frozen raw32. A native
    # coefficient error after DFT/N is bounded in infinity norm; zero embedding
    # preserves it. Sum over N native coefficients bounds the unnormalized
    # inverse. Each separable axis has <=16*n+32 complex elementary operations
    # per output and kernel argument<=2*pi*(n-1), including legitimate FFT
    # versus direct-sum evaluation under the same stability assumption.
    def axis_error(length: int) -> float:
        return gamma(16 * length + 32) + gamma(16) * (1 + 2 * math.pi * (length - 1)) + 16 * u

    native_abs = 2 * float(np.max(abs(raw.astype(float) - 10))) / 0.8
    native_one = gamma(40) * native_abs  # correction,15-term mean and fixed gain
    ef = 2 * sum(axis_error(n) for n in (8, 24, 24))
    ei = 2 * sum(axis_error(n) for n in (8, 48, 48))
    coefficient_one = native_one + native_abs * (ef + gamma(2))
    conventional_one = 4608 * (coefficient_one + native_abs * ei)

    # Power has15 signed direction/order terms. Regularized response derivative
    # is w²/(P+w²)²; use a strictly positive perturbed denominator, mode by mode.
    power_errors, response_errors = [], []
    w2 = p["filtering"]["wiener"] ** 2
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]
    for key in keys:
        total, propagation, magnitude_bound = 0.0, 0.0, 0.0
        for k0 in carriers(p):
            for order in range(-2, 3):
                q = np.array((key[0] / 24, key[1] / 24)) - order * k0
                hh = (
                    sample(h, abs(order), float(q[0]), float(q[1]), key[2])
                    if np.linalg.norm(q) < 0.5
                    else 0j
                )
                aa = al1[abs(order)]
                total += abs(a[abs(order)] * hh) ** 2
                propagation += aa**2 * (2 * abs(hh) * eh + eh**2)
                magnitude_bound += (aa * hmax) ** 2
        ep = propagation + gamma(64 * 15 + 32) * magnitude_bound
        den = total + w2
        assert den > ep
        er = w2 * ep / (den * (den - ep)) + gamma(8) * 2
        power_errors.append(2 * ep)
        response_errors.append(2 * er)
    return {
        "coefficient_l1_density": mass,
        "illumination_l1": illumination,
        "truth_atol": 2 * truth_one,
        "unquantized_raw_atol": 2 * raw_one,
        "raw_quantization_cell_radius": raw_one,
        "raw_physical_quantization_ceiling": acquisition_bounds(p)["raw_quantization_abs"],
        "reference_corrected_counts_atol": 2
        * (0.8 * reference_one + gamma(2) * 0.8 * reference_mass * illumination),
        "specimen_corrected_counts_atol": 2
        * (
            0.8 * (reference_one + contrast_one)
            + gamma(4) * 0.8 * (reference_mass + mass) * illumination
        ),
        "conventional_atol": 2 * conventional_one,
        "frequency_component_error_cyc_um": eq,
        "transfer_sample_error": eh,
        "mode_power_atol": np.array(power_errors),
        "ideal_response_atol": np.array(response_errors),
        "radial_formula_one_error": 4 * gamma(64),
    }


def float32_cells(values: Array) -> tuple[Array, Array]:
    """Exact binary64 midpoints of adjacent finite normal float32 samples."""
    assert values.dtype == np.dtype("float32")
    assert np.all(np.isfinite(values))
    lower = np.nextafter(values, np.float32(-np.inf)).astype(float)
    upper = np.nextafter(values, np.float32(np.inf)).astype(float)
    center = values.astype(float)
    assert np.all(np.isfinite(lower)) and np.all(np.isfinite(upper))
    # Used only for the declared normal raw/radial values (zero permitted).
    # The adjacent32 values and their midpoints fit exactly in53 binary bits.
    return (lower + center) / 2, (upper + center) / 2


def assert_raw_observer(raw: Array, unquantized: Array, radius: float) -> None:
    """Validate frozen observed input against a physical observer interval.

    Closed cells intentionally make no unique-rounding/tie-ownership claim.
    The fixture hash, raw dtype and later input-copy check remain exact.
    """
    lo, hi = float32_cells(raw)
    assert raw.shape == unquantized.shape
    # Outward rounding encloses the real interval endpoints; it does not
    # change the float32 quantizer or assert that its result is unique.
    assert np.all(unquantized >= np.nextafter(lo - radius, -np.inf))
    assert np.all(unquantized <= np.nextafter(hi + radius, np.inf))


def assert_transfer_observer(regenerated: Array, frozen: Array) -> dict[str, float]:
    """Prove unique radial32 rounding before retaining exact table equality."""
    radial = np.real(frozen[0, :, 0])
    np.testing.assert_array_equal(radial, radial.astype(np.float32).astype(float))
    margin = math.inf
    er = 4 * gamma(64)
    for r, cell in enumerate(radial):
        if r >= 12:
            assert cell == 0  # prescribed support branch, no transcendentals
            continue
        v = r / 12
        analytic = 2 * (math.acos(v) - v * math.sqrt(1 - v * v)) / math.pi
        lo, hi = float32_cells(np.asarray(cell, dtype=np.float32))
        gap = min(float(analytic - lo), float(hi - analytic))
        # v<=11/12 keeps sqrt>=sqrt(23)/12>.39. Derivative of the circle
        # function <=4/pi;64 scalar/libm operations at magnitude<=4 bound
        # both input-v and arithmetic error by4*gamma64, with8u libm error.
        assert gap > er
        margin = min(margin, gap)
    hz = np.array([1, 0.25 + 0.125j, 0.0625, 0, 0, 0, 0.0625, 0.25 - 0.125j] * 2)
    declared = np.broadcast_to(radial[None, :, None] * hz[None, None, :], frozen.shape)
    # Second stage is componentwise scaling by powers of2 of normal32 cells;
    # each product is exactly32-representable, without underflow or a midpoint.
    np.testing.assert_array_equal(declared, declared.astype(np.complex64).astype(complex))
    np.testing.assert_array_equal(frozen, declared)
    np.testing.assert_array_equal(regenerated, frozen)
    return {"minimum_radial_midpoint_margin": margin, "radial_one_error": er}


def assert_observer_arrays(data: dict[str, Array], frozen: Any, budget: dict[str, Any]) -> None:
    """Observer-only checks shared by later public test and oracle diagnostics."""
    assert data["raw"].dtype == frozen["raw"].dtype == np.dtype("float32")
    np.testing.assert_array_equal(data["raw"], data["unquantized_raw"].astype(np.float32))
    assert_raw_observer(
        frozen["raw"], data["unquantized_raw"], budget["raw_quantization_cell_radius"]
    )
    # Retain the original physical quantization ceiling with observer error
    # charged inside it, rather than adding slack to that physical limit.
    assert (
        np.max(abs(frozen["raw"].astype(float) - data["unquantized_raw"]))
        + budget["raw_quantization_cell_radius"]
        <= budget["raw_physical_quantization_ceiling"]
    )
    for name in (
        "truth",
        "unquantized_raw",
        "reference_corrected_counts",
        "specimen_corrected_counts",
    ):
        assert data[name].shape == frozen[name].shape
        assert data[name].dtype == frozen[name].dtype == np.dtype("float64")
        np.testing.assert_allclose(data[name], frozen[name], rtol=0, atol=budget[name + "_atol"])
