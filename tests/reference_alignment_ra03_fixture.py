"""RA03 independent tiny finite sums and reusable numerical figure controls.

Expected truth uses explicit fields, analytic radial rules, a J0 power series,
and a direct interpretation of the public cache payload. No product numerical
helper supplies expected truth. Distances are micrometres; weights are electrons.
"""

import math
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from typing import Any

import numpy as np

SPACING = (0.5, 1.0, 1.0)
OPTICS: dict[str, Any] = dict(
    excitation_um=1.0, emission_um=1.0, refractive_index=1.0, detection_na=0.5, pupil_order=2
)
TRUE_BEAMS = (4.0, 2.0, 1.0)
ESTIMATED_BEAMS = (1.0, 3.0, 0.5)
OBSERVER_REL = 4096 * np.finfo(np.float64).eps


def radial_rule(order):
    """Closed-form Gauss rules on [0,1], only for our three tiny controls."""
    if order == 1:
        return [(0.5, 1.0)]
    if order == 2:
        a = 1 / (2 * math.sqrt(3))
        return [(0.5 - a, 0.5), (0.5 + a, 0.5)]
    if order == 3:
        a = math.sqrt(3 / 5) / 2
        return [(0.5 - a, 5 / 18), (0.5, 4 / 9), (0.5 + a, 5 / 18)]
    raise ValueError("independent tiny oracle supports orders 1,2,3")


def bessel0(x):
    """J0(x)=sum (-x*x/4)^m/(m!)^2; tiny domain |x|<5 here.

    48 terms bound the omitted tail far below binary64 rounding in this domain.
    math.fsum reduces cancellation without borrowing a product special function.
    """
    terms = [1.0]
    for m in range(1, 48):
        terms.append(terms[-1] * (-x * x / 4) / (m * m))
    return math.fsum(terms)


def pupil(
    radius, displacement, *, emission_um=1.0, refractive_index=1.0, detection_na=0.5, pupil_order=2
):
    r = detection_na / emission_um
    nu = refractive_index / emission_um
    beta = detection_na / refractive_index
    terms = []
    for u, weight in radial_rule(pupil_order):
        angle = 2 * math.pi * nu * displacement * (math.sqrt(1 - beta * beta * u) - 1)
        terms.append(
            weight
            * bessel0(2 * math.pi * r * math.sqrt(u) * radius)
            * complex(math.cos(angle), math.sin(angle))
        )
    amplitude = complex(math.fsum(t.real for t in terms), math.fsum(t.imag for t in terms))
    return math.pi * r * r * abs(amplitude) ** 2


def illumination(y, x, displacement, q, phase, beams, *, excitation_um=1.0, refractive_index=1.0):
    k0 = refractive_index / excitation_um
    kappa = k0 - math.sqrt(k0 * k0 - float(q[0]) ** 2 - float(q[1]) ** 2)
    theta = 2 * math.pi * (float(q[0]) * y + float(q[1]) * x) + phase
    axial = 2 * math.pi * kappa * displacement
    a0, plus, minus = beams
    field = complex(
        a0 * math.cos(axial) + (plus + minus) * math.cos(theta),
        a0 * math.sin(axial) + (plus - minus) * math.sin(theta),
    )
    return abs(field) ** 2 / math.fsum(a * a for a in beams)


def physical_images(source, *, spacing, refinement, q, phases, beams, pixels=(2, 2), optics=None):
    """Literal source/pixel/pupil finite sum, independent of product factoring.

    Returns images and the unilluminated finite reference U. Signed source is
    supported for inverse controls, but generator callers use nonnegative input.
    """
    cfg = OPTICS if optics is None else optics
    shape = tuple(n // f for n, f in zip(source.shape, refinement, strict=True))
    images = np.zeros((len(phases), *shape), dtype=np.float64)
    unilluminated = np.zeros(shape, dtype=np.float64)
    pupil_cfg = {
        k: cfg[k] for k in ("emission_um", "refractive_index", "detection_na", "pupil_order")
    }
    for n in np.ndindex(shape):
        zfocus = (n[0] + 0.5) * spacing[0]
        base_terms = []
        phase_terms = [[] for _ in phases]
        for j in np.ndindex(source.shape):
            if source[j] == 0:
                continue
            z, y, x = [(v + 0.5) * d / f for v, d, f in zip(j, spacing, refinement, strict=True)]
            displacement = z - zfocus
            h = []
            for sy, sx in product(range(pixels[0]), range(pixels[1])):
                ty = (n[1] + (sy + 0.5) / pixels[0]) * spacing[1]
                tx = (n[2] + (sx + 0.5) / pixels[1]) * spacing[2]
                h.append(pupil(math.hypot(ty - y, tx - x), displacement, **pupil_cfg))
            coefficient = (
                spacing[1] * spacing[2] / math.prod(pixels) * float(source[j]) * math.fsum(h)
            )
            base_terms.append(coefficient)
            for p, phase in enumerate(phases):
                phase_terms[p].append(
                    coefficient
                    * illumination(
                        y,
                        x,
                        displacement,
                        q,
                        phase,
                        beams,
                        excitation_um=cfg["excitation_um"],
                        refractive_index=cfg["refractive_index"],
                    )
                )
        unilluminated[n] = math.fsum(base_terms)
        for p in range(len(phases)):
            images[(p, *n)] = math.fsum(phase_terms[p])
    return images, unilluminated


def represented_kernel(cache):
    """Evaluate the inverse real DFT as finite cosine sums, without an FFT.

    Exact y-even real half spectra imply a separately even real plane. Interior
    x frequencies have multiplicity 2; DC and Nyquist have multiplicity 1.
    """
    nz, ny, nx = cache.source_shape_zyx
    fy, fx = 2 * ny, 2 * nx
    c = cache.lateral_spectra
    h = np.empty((nz, fy, fx), dtype=np.float64)
    for d, y, x in np.ndindex(h.shape):
        h[d, y, x] = math.fsum(
            float(c[d, frequency_y, k])
            * (1 if k in (0, nx) else 2)
            * math.cos(2 * math.pi * frequency_y * y / fy)
            * math.cos(2 * math.pi * k * x / fx)
            for frequency_y in range(fy)
            for k in range(nx + 1)
        ) / (fy * fx)
    return h


def cache_matrices(cache):
    """B_Q, G_C, E and represented H, with abs before the pixel sum."""
    shape = cache.source_shape_zyx
    detector = (shape[0], shape[1] // 2, shape[2] // 2)
    dz, dy, dx = cache.source_spacing_um_zyx
    h = represented_kernel(cache)
    physical, absolute, error = [
        np.zeros((math.prod(detector), math.prod(shape))) for _ in range(3)
    ]
    cfg = {
        key: getattr(cache, key)
        for key in ("emission_um", "refractive_index", "detection_na", "pupil_order")
    }
    for ni, n in enumerate(np.ndindex(detector)):
        for ji, j in enumerate(np.ndindex(shape)):
            b, g, e = [], [], []
            for sy, sx in product((0, 1), repeat=2):
                lag = (n[0] - j[0], 2 * n[1] + sy - j[1], 2 * n[2] + sx - j[2])
                hc = h[abs(lag[0]), lag[1] % (2 * shape[1]), lag[2] % (2 * shape[2])]
                hq = pupil(math.hypot(lag[1] * dy, lag[2] * dx), -lag[0] * dz, **cfg)
                b.append(hq)
                g.append(abs(hc))
                e.append(abs(hc - hq))
            physical[ni, ji] = dy * dx * math.fsum(b)
            absolute[ni, ji] = dy * dx * math.fsum(g)
            error[ni, ji] = dy * dx * math.fsum(e)
    return physical, absolute, error, h


def cache_images(source, cache, q, phases, beams, *, excitation_um=1.0):
    """Exact represented-kernel map observed through direct finite sums."""
    h = represented_kernel(cache)
    nz, ny, nx = source.shape
    dz, dy, dx = cache.source_spacing_um_zyx
    result = np.empty((len(phases), nz, ny // 2, nx // 2))
    for p, k, iy, ix in np.ndindex(result.shape):
        terms = []
        for j in np.ndindex(source.shape):
            z, y, x = [(v + 0.5) * d for v, d in zip(j, (dz, dy, dx), strict=True)]
            intensity = illumination(
                y,
                x,
                z - (k + 0.5) * dz,
                q,
                phases[p],
                beams,
                excitation_um=excitation_um,
                refractive_index=cache.refractive_index,
            )
            for sy, sx in product((0, 1), repeat=2):
                terms.append(
                    float(source[j])
                    * intensity
                    * dy
                    * dx
                    * h[
                        abs(k - j[0]),
                        (2 * iy + sy - j[1]) % (2 * ny),
                        (2 * ix + sx - j[2]) % (2 * nx),
                    ]
                )
        result[p, k, iy, ix] = math.fsum(terms)
    return result


def transfer(q, phases, calibration, specimen):
    shift = (
        2
        * math.pi
        * math.fsum(float(q[a]) * (specimen[a + 1] - calibration[a + 1]) for a in (0, 1))
    )
    return np.asarray(phases, dtype=np.float64) + shift


def orientation_case() -> dict[str, Any]:
    fine = np.zeros((6, 2, 2), dtype=np.float64)
    fine[0, 0, 0] = 0.1
    fine[1, 0, 0] = 0.2
    fine[2, 1, 0] = 1.25
    fine[3, 1, 1] = 0.375
    fine[4, 0, 1] = 2**-152
    fine[5, 1, 0] = 0.625
    original = np.zeros((3, 2, 2), dtype=np.float32)
    original[0, 0, 1] = -0.25
    original[2, 1, 0] = 0.75
    return dict(
        fine_source_e=fine,
        reference_signal_e=(np.arange(9, dtype=np.float64).reshape(3, 3, 1, 1) + 0.125),
        original_source_relative=original,
        original_prediction_relative=-np.arange(9, dtype=np.float64).reshape(3, 3, 1, 1) / 8,
        detector_spacing_um_zyx=SPACING,
        true_carrier_yx_per_um=np.array([0.375, -0.25]),
        estimated_carrier_yx_per_um=np.array([0.25, 0.125]),
        true_phases_at_calibration_origin_rad=np.array([0.1, math.pi / 2, -0.7]),
        estimated_phases_at_calibration_origin_rad=np.array([-0.3, 0.6, 1.1]),
        true_beam_amplitudes=TRUE_BEAMS,
        estimated_beam_amplitudes=ESTIMATED_BEAMS,
        calibration_origin_um_zyx=(0.125, -0.25, 0.5),
        specimen_origin_um_zyx=(0.5, 0.375, -0.125),
        source_to_relative=1.25,
        **OPTICS,
    )


def pairing_control() -> dict[str, Any]:
    """Return the three rounding stages with exact dyadic total observers.

    Each normalized float64 input is interpreted as a rational number. This
    separates pair-addition, camera-gauge multiplication and float32 cast error.
    Fractions are for ledger observers only, not a new product representation.
    """
    case = orientation_case()
    fine, scale = case["fine_source_e"], case["source_to_relative"]
    pair = fine[0::2] + fine[1::2]
    paired64 = pair * scale
    paired32 = paired64.astype(np.float32)
    exact_pairs = [
        Fraction.from_float(float(a)) + Fraction.from_float(float(b))
        for a, b in zip(fine[0::2].flat, fine[1::2].flat, strict=True)
    ]
    stored_pair_total = sum((Fraction.from_float(float(v)) for v in pair.flat), Fraction())
    exact_pair_total = sum(exact_pairs, Fraction())
    represented64_total = sum((Fraction.from_float(float(v)) for v in paired64.flat), Fraction())
    represented32_total = sum((Fraction.from_float(float(v)) for v in paired32.flat), Fraction())
    gauge = Fraction.from_float(scale)
    return dict(
        pair_actual=pair,
        paired64=paired64,
        paired32=paired32,
        exact_pair_total=exact_pair_total,
        stored_pair_total=stored_pair_total,
        pair_sum_change=stored_pair_total - exact_pair_total,
        gauge_sum_change=represented64_total - stored_pair_total * gauge,
        cast32_sum_change=represented32_total - represented64_total,
        exact_gauged_total=exact_pair_total * gauge,
        represented64_total=represented64_total,
        represented32_total=represented32_total,
        geometry=dict(
            spacing_um_zyx=SPACING, origin_um_zyx=(0.0, 0.0, 0.0), center_um_zyx=(0.75, 0.5, 0.5)
        ),
        provenance="exact dyadic totals for separate pair, gauge and cast32 stages",
    )


def arm_settings(case) -> dict[str, Any]:
    tq, eq = case["true_carrier_yx_per_um"], case["estimated_carrier_yx_per_um"]
    tp = case["true_phases_at_calibration_origin_rad"]
    ep = case["estimated_phases_at_calibration_origin_rad"]
    tb, eb = case["true_beam_amplitudes"], case["estimated_beam_amplitudes"]
    return {
        "paired_inverse_true": (tq, tp, tb),
        "paired_inverse_estimated": (eq, ep, eb),
        "paired_inverse_carrier_only": (eq, tp, tb),
        "paired_inverse_phase_only": (tq, ep, tb),
        "paired_inverse_beam_only": (tq, tp, eb),
        "original_fit_reapplied": (eq, ep, eb),
    }


def make_cache(shape=(3, 2, 2), spacing=(0.5, 0.5, 0.5)):
    from scripts.simulation_inverse_operator import build_kernel_cache

    return build_kernel_cache(
        source_shape_zyx=shape,
        source_spacing_um_zyx=spacing,
        **{k: v for k, v in OPTICS.items() if k != "excitation_um"},
    )


def point_sign_control() -> dict[str, Any]:
    """R13: middle source, unequal sides, focus below/at/above; Q=1 analytic.

    k0=1, |q|=sqrt(3)/2 gives kappa about 1/2. dz=1/2
    makes kappa*d about +/-1/4. theta=pi/2 at source (y,x)=(1/4,1/4).
    The evaluated normalized q, not ideal sqrt(3)/2, defines numerical truth.
    """
    from scripts.simulation_inverse_operator import build_kernel_cache, forward
    from scripts.simulation_optics import expected_images

    source = np.zeros((3, 2, 2), dtype=np.float32)
    source[1, 0, 0] = 1
    q = np.array([math.sqrt(3) / 2, 0.0])
    phases = np.array([math.pi / 2 - 2 * math.pi * q[0] * 0.25])
    cfg = {**OPTICS, "pupil_order": 1}
    expected, u = physical_images(
        source,
        spacing=(0.5, 1.0, 1.0),
        refinement=(1, 2, 2),
        q=q,
        phases=phases,
        beams=TRUE_BEAMS,
        optics=cfg,
    )
    cache = build_kernel_cache(
        source_shape_zyx=source.shape,
        source_spacing_um_zyx=(0.5, 0.5, 0.5),
        **{k: v for k, v in cfg.items() if k != "excitation_um"},
    )
    actual = expected_images(
        source.astype(np.float64),
        detector_spacing_um_zyx=(0.5, 1.0, 1.0),
        source_refinement_zyx=(1, 2, 2),
        carriers_yx_per_um=q[None],
        phases_rad=phases[None],
        beam_amplitudes=TRUE_BEAMS,
        pixel_subsamples_yx=(2, 2),
        **cfg,
    )[0]
    inverse = forward(
        source,
        kernel_cache=cache,
        carrier_yx_per_um=q,
        phases_rad=phases,
        beam_amplitudes=TRUE_BEAMS,
        excitation_um=1.0,
    )
    represented = cache_images(source, cache, q, phases, TRUE_BEAMS)
    return dict(
        actual=actual,
        expected=expected,
        unilluminated=u,
        inverse_actual=inverse,
        inverse_expected=represented,
        source=source,
        cache=cache,
        geometry=dict(
            spacing_um_zyx=(0.5, 1.0, 1.0),
            origin_um_zyx=(0.0, 0.0, 0.0),
            center_um_zyx=(0.75, 0.25, 0.25),
            focus_displacements_um=(0.5, 0.0, -0.5),
        ),
        provenance="Q1 analytic pupil, direct squared field, source-minus-focus",
    )


def kernel_application_control() -> dict[str, Any]:
    """R14: distinguish builder norm bounds from represented application bound."""
    from scripts.simulation_inverse_operator import forward

    cache = make_cache()
    b, g, e, h = cache_matrices(cache)
    source = np.zeros(cache.source_shape_zyx, dtype=np.float32)
    source[0, 0, 0], source[2, 1, 1] = 0.75, -0.25
    q, phases = np.array([0.375, -0.25]), np.array([0.1, 1.3])
    actual = forward(
        source,
        kernel_cache=cache,
        carrier_yx_per_um=q,
        phases_rad=phases,
        beam_amplitudes=TRUE_BEAMS,
        excitation_um=1.0,
    )
    expected = cache_images(source, cache, q, phases, TRUE_BEAMS)
    physical, _ = physical_images(
        source, spacing=SPACING, refinement=(1, 2, 2), q=q, phases=phases, beams=TRUE_BEAMS
    )
    return dict(
        actual=actual,
        expected=expected,
        physical_expected=physical,
        physical_matrix=b,
        absolute_matrix=g,
        error_matrix=e,
        represented_kernel=h,
        source=source,
        cache=cache,
        beams=TRUE_BEAMS,
        geometry=dict(
            spacing_um_zyx=SPACING, origin_um_zyx=(0.0, 0.0, 0.0), center_um_zyx=(0.75, 0.5, 0.5)
        ),
        provenance="finite physical Q2 vs direct cosine DFT of represented float32 payload",
    )


def signed_cache_control() -> dict[str, Any]:
    """Exercise a legitimate nonphysical cache with exact dyadic values.

    DC payloads (16,-8,4) divided by Fy*Fx=16 define constant lateral
    kernels (1,-1/2,1/4) at axial lags 0,1,2. Pixel area is exactly 1.
    """
    from scripts.simulation_inverse_operator import InverseKernelCache, forward

    payload = np.zeros((3, 4, 3), dtype=np.float32)
    payload[:, 0, 0] = (16, -8, 4)
    cache = InverseKernelCache(
        lateral_spectra=payload,
        source_shape_zyx=(3, 2, 2),
        source_spacing_um_zyx=(0.5, 0.5, 0.5),
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=0.5,
        pupil_order=2,
    )
    source = np.zeros((3, 2, 2), dtype=np.float32)
    source[0, 0, 0], source[2, 1, 1] = 0.75, -0.25
    q, phases, beams = np.zeros(2), np.zeros(1), (1.0, 0.0, 0.0)
    actual = forward(
        source,
        kernel_cache=cache,
        carrier_yx_per_um=q,
        phases_rad=phases,
        beam_amplitudes=beams,
        excitation_um=1.0,
    )
    expected = np.array([11 / 16, -1 / 4, -1 / 16]).reshape(1, 3, 1, 1)
    interpreted = cache_images(source, cache, q, phases, beams)
    _, g, _, _ = cache_matrices(cache)
    return dict(
        actual=actual,
        expected=expected,
        interpreted=interpreted,
        application_scale=float(g.sum(axis=1).max()) * 0.75,
        cache=cache,
        source=source,
        geometry=dict(
            spacing_um_zyx=SPACING, origin_um_zyx=(0.0, 0.0, 0.0), center_um_zyx=(0.75, 0.5, 0.5)
        ),
        provenance="analytic dyadic signed cache, independently constructed public record",
    )


def rational_sphere(refinement):
    """Place the same B=1 sphere in the same box by rational midpoint tests."""
    shape = tuple(n * refinement for n in (3, 1, 1))
    center = (Fraction(3, 4), Fraction(1, 2), Fraction(1, 2))
    radius = Fraction.from_float(0.43)
    spacing = (Fraction(1, 2), Fraction(1), Fraction(1))
    occupied = [
        j
        for j in np.ndindex(shape)
        if sum(
            ((Fraction(2 * j[a] + 1, 2) * spacing[a] / refinement) - center[a]) ** 2
            for a in range(3)
        )
        <= radius**2
    ]
    expected = np.zeros(shape, dtype=np.float64)
    for j in occupied:
        expected[j] = float(Fraction(1, len(occupied)))
    return expected, len(occupied)


def refinement_controls() -> dict[str, Any]:
    """R15 reusable same-object source and separate pixel changes, all tiny.

    Three values in each sequence are observations, never continuum truth.
    Each product array is paired with an independently computed finite target.
    """
    from scripts.simulation_optics import expected_images
    from scripts.simulation_sources import make_sources

    catalogue = np.array([[0.75, 0.5, 0.5, 0.43, 1.0]])
    q, phases, beams = np.array([0.375, -0.25]), np.array([0.1]), TRUE_BEAMS
    source_rows, pixel_rows = [], []

    def image_row(source, f, pixels, expected_source=None) -> dict[str, Any]:
        expected, u = physical_images(
            source if expected_source is None else expected_source,
            spacing=SPACING,
            refinement=(f, f, f),
            q=q,
            phases=phases,
            beams=beams,
            pixels=(pixels, pixels),
        )
        actual = expected_images(
            source,
            detector_spacing_um_zyx=SPACING,
            source_refinement_zyx=(f, f, f),
            carriers_yx_per_um=q[None],
            phases_rad=phases[None],
            beam_amplitudes=beams,
            pixel_subsamples_yx=(pixels, pixels),
            **OPTICS,
        )[0]
        return dict(
            actual=actual,
            expected=expected,
            unilluminated=u,
            source_refinement=f,
            pixels=pixels,
            pupil_order=2,
        )

    for f in (1, 2, 4):
        expected_source, count = rational_sphere(f)
        actual_source = make_sources(
            catalogue,
            detector_shape_zyx=(3, 1, 1),
            detector_spacing_um_zyx=SPACING,
            source_refinement_zyx=(f, f, f),
        )
        row = image_row(actual_source, f, 2, expected_source=expected_source)
        row.update(
            source_actual=actual_source,
            source_expected=expected_source,
            occupied_count=count,
            mass_exact=sum(map(Fraction.from_float, actual_source.flat), Fraction()),
            occupied_volume_um3=count * math.prod(SPACING) / (f**3),
        )
        source_rows.append(row)
    fixed_source, _ = rational_sphere(2)
    for pixels in (1, 2, 4):
        pixel_rows.append(image_row(fixed_source, 2, pixels))
    return dict(
        source_rows=source_rows,
        pixel_rows=pixel_rows,
        catalogue=catalogue,
        geometry=dict(
            detector_shape_zyx=(3, 1, 1),
            spacing_um_zyx=SPACING,
            origin_um_zyx=(0.0, 0.0, 0.0),
            center_um_zyx=(0.75, 0.5, 0.5),
            focus_centers_um=(0.25, 0.75, 1.25),
        ),
        provenance="rational closed sphere sites, B/K rounding, explicit finite pupil/field sum",
    )


# Post-implementation supplement: these observers do not extend the bounded
# phase assumptions of illumination(), transfer(), or physical_images().
def _supplement_pi():
    """Evaluate Machin's identity with Decimal arithmetic in the caller context."""

    def arctangent(reciprocal):
        x = Decimal(1) / reciprocal
        power, total = x, Decimal(0)
        for k in range(460):
            total += power / (2 * k + 1)
            power *= -x * x
        return total

    return 16 * arctangent(5) - 4 * arctangent(239)


def _supplement_trig(angle, pi):
    """Return high-precision cosine/sine after high-precision range reduction."""
    angle %= 2 * pi
    if angle > pi:
        angle -= 2 * pi
    elif angle < -pi:
        angle += 2 * pi
    cosine, sine = Decimal(1), angle
    cterm, sterm = cosine, sine
    for k in range(1, 300):
        cterm *= -angle * angle / ((2 * k - 1) * (2 * k))
        sterm *= -angle * angle / ((2 * k) * (2 * k + 1))
        cosine += cterm
        sine += sterm
    return cosine, sine


def large_phase_phasor(phase_rad):
    """Observe a finite float phase without subtracting a rounded float 2*pi.

    Precision reserves 120 digits beyond a binary64 phase's decimal exponent;
    fixed series lengths cover the largest required context (428 digits).
    This supplemental observer is independent of every product phase helper.
    """
    value = Decimal.from_float(float(phase_rad))
    with localcontext() as context:
        context.prec = max(160, value.adjusted() + 120)
        cosine, sine = _supplement_trig(value, _supplement_pi())
        return float(cosine), float(sine)


def large_phase_control(displaced) -> dict[str, Any]:
    """Build one of two supplemental large-phase targets before product calls.

    The only source coefficient pairs exactly to a unit at (.5,.25,.25) um.
    Q1 four-site integration gives K=pi/16*(1+2*J0(pi/(2*sqrt(2)))**2
    +J0(pi/2)**2). For beams (1,1,0) and d=0 the field factor is 1+cos(theta).
    All target arithmetic, including the origin/local offsets, uses 160 digits.
    """
    fine = np.zeros((2, 2, 2), dtype=np.float64)
    fine[0, 0, 0] = 1
    q = np.array([0.0, 0.25 if displaced else 0.0])
    origin_x = 1.0 if displaced else 0.0
    case = dict(
        fine_source_e=fine,
        reference_signal_e=np.zeros((1, 1, 1, 1)),
        original_source_relative=np.zeros((1, 2, 2), dtype=np.float32),
        original_prediction_relative=np.zeros((1, 1, 1, 1)),
        detector_spacing_um_zyx=(1.0, 1.0, 1.0),
        true_carrier_yx_per_um=q.copy(),
        estimated_carrier_yx_per_um=q.copy(),
        true_phases_at_calibration_origin_rad=np.array([1e20]),
        estimated_phases_at_calibration_origin_rad=np.array([1e20]),
        true_beam_amplitudes=(1.0, 1.0, 0.0),
        estimated_beam_amplitudes=(1.0, 1.0, 0.0),
        calibration_origin_um_zyx=(0.0, 0.0, 0.0),
        specimen_origin_um_zyx=(0.0, 0.0, origin_x),
        source_to_relative=1.0,
        excitation_um=1.0,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=0.5,
        pupil_order=1,
    )
    with localcontext() as context:
        context.prec = 160
        pi = _supplement_pi()

        def j0(argument):
            term, total = Decimal(1), Decimal(1)
            for k in range(1, 200):
                term *= -argument * argument / (4 * k * k)
                total += term
            return total

        base = pi / 16 * (1 + 2 * j0(pi / (2 * Decimal(2).sqrt())) ** 2 + j0(pi / 2) ** 2)
        phase = Decimal.from_float(1e20)
        carrier_x = Decimal.from_float(float(q[1]))
        origin_turns = carrier_x * Decimal.from_float(origin_x)
        local_turns = carrier_x / 4
        cosine, _ = _supplement_trig(phase + 2 * pi * (origin_turns + local_turns), pi)
        expected = float(base * (1 + cosine))
        calibration_pair = tuple(float(v) for v in _supplement_trig(phase, pi))
        specimen_pair = tuple(float(v) for v in _supplement_trig(phase + 2 * pi * origin_turns, pi))
        no_origin_cosine, _ = _supplement_trig(phase + 2 * pi * local_turns, pi)
        no_origin_prediction = float(base * (1 + no_origin_cosine))
        kappa = float(1 - (1 - carrier_x * carrier_x).sqrt())
    observer_rel = 64 * np.finfo(np.float64).eps
    return dict(
        case=case,
        expected=np.full((1, 1, 1, 1), expected),
        base_e=float(base),
        generator_allowance_e=(1e-5 + observer_rel) * float(base),
        # Four source sites each have unilluminated pixel coefficient K, so
        # Cr(B_Q)=4*K. L=2 and max(source)=1 give physical forward scale 8*K.
        inverse_allowance_e=(2e-4 + 1e-8 + observer_rel) * 8 * float(base),
        manifest_allowance=observer_rel,
        calibration_phasor=calibration_pair,
        specimen_phasor=specimen_pair,
        kappa_per_um=kappa,
        source_minus_focus_um=0.0,
        no_origin_prediction_e=no_origin_prediction,
        origin_turns=float(origin_turns),
        local_turns=float(local_turns),
        provenance=(
            "POST-IMPLEMENTATION SUPPLEMENT: independent Decimal Machin/trig/J0 finite control"
        ),
    )
