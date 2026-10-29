"""Supplemental dense-source case fixed before observing the public product."""

from __future__ import annotations

from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Bounds,
    Interval,
    Reference,
    bessel_from_square,
    exact,
    pi_interval,
    sin_cos,
)

SOURCE_SHAPE = (4, 4, 6)
DETECTOR_SHAPE = (2, 2, 3)
REFINEMENT = (2, 2, 2)
SPACING = (0.625, 0.25, 0.1875)
PIXELS = (2, 3)
CARRIERS = ((0.83, -0.61), (-0.47, 0.89))
PHASES = ((0.23, -0.87, 2.4), (-0.53, 1.31, -2.2))
BEAMS = (4.0, 2.0, 1.0)


def weight(z: int, y: int, x: int) -> Fraction:
    """Positive asymmetric integrated electrons, exactly binary representable."""
    return Fraction(1 + (7 * z + 3 * y + 5 * x + z * y + 2 * y * x) % 37, 8)


def arguments(*, reverse_sides: bool = False) -> dict[str, Any]:
    """Two algebraically equivalent, ordinary public input representations."""
    source = np.array(
        [[[float(weight(z, y, x)) for x in range(6)] for y in range(4)] for z in range(4)]
    )
    sign = -1 if reverse_sides else 1
    return {
        "source_e": source,
        "detector_spacing_um_zyx": SPACING,
        "source_refinement_zyx": REFINEMENT,
        "carriers_yx_per_um": sign * np.array(CARRIERS),
        "phases_rad": sign * np.array(PHASES),
        "beam_amplitudes": (4.0, 1.0, 2.0) if reverse_sides else BEAMS,
        "excitation_um": 0.5,
        "emission_um": 0.625,
        "refractive_index": 1.25,
        "detection_na": 0.75,
        "pupil_order": 2,
        "pixel_subsamples_yx": PIXELS,
    }


AxisWeights = tuple[tuple[Fraction, ...], tuple[Fraction, ...], tuple[Fraction, ...]]
LARGE_SPACING = (0.125, 0.08, 0.08)
LARGE_WEIGHTS: AxisWeights = (
    tuple(Fraction(z + 1, 16) for z in range(17)),
    tuple(Fraction(1 + (3 * y) % 11, 8) for y in range(8)),
    tuple(Fraction(1 + (5 * x) % 13, 8) for x in range(8)),
)


def large_arguments() -> dict[str, Any]:
    """All 17 axial planes contribute positive nonconstant dyadic weights."""
    args = arguments()
    wz, wy, wx = LARGE_WEIGHTS
    args.update(
        source_e=np.array([[[float(z * y * x) for x in wx] for y in wy] for z in wz]),
        detector_spacing_um_zyx=LARGE_SPACING,
        source_refinement_zyx=(1, 2, 2),
        pupil_order=1,
        pixel_subsamples_yx=(2, 2),
    )
    return args


@cache
def separable_reference(
    weights: AxisWeights,
    spacing: tuple[float, float, float],
    refinement: tuple[int, int, int],
    *,
    carriers: tuple[tuple[float, float], ...] = CARRIERS,
    phases: tuple[tuple[float, ...], ...] = PHASES,
    beams: tuple[float, float, float] = BEAMS,
    pixels: tuple[int, int] = (2, 2),
) -> Reference:
    """Exact Q=1 finite-sum factorization, retaining signed axial interference.

    K includes pixel area and the mean of all midpoint sites. For each pixel,
    integrate K*wy*wx against 1, cos(theta), sin(theta), cos(2theta), sin(2theta),
    with theta excluding the phase input. Separately sum wz*cos(alpha) and
    wz*sin(alpha) for each focus, with alpha=2*pi*kappa*(source_z-focus_z).
    Phase addition and the squared-field cross terms then give every image.
    All arithmetic and series tails are enclosed; no output sets an allowance.
    """
    wz, wy, wx = weights
    fz, fy, fx = refinement
    assert all(len(w) % f == 0 for w, f in zip(weights, refinement, strict=True))
    nz, ny, nx = len(wz) // fz, len(wy) // fy, len(wx) // fx
    dz, dy, dx = map(exact, spacing)
    source_z = tuple(dz * Fraction(2 * z + 1, 2 * fz) for z in range(len(wz)))
    source_y = tuple(dy * Fraction(2 * y + 1, 2 * fy) for y in range(len(wy)))
    source_x = tuple(dx * Fraction(2 * x + 1, 2 * fx) for x in range(len(wx)))
    focuses = tuple(dz * Fraction(2 * k + 1, 2) for k in range(nz))
    py, px = pixels
    a0, plus, minus = map(exact, beams)
    norm = a0**2 + plus**2 + minus**2
    axial_mass = sum(wz, Fraction(0))
    frequency = exact(0.75) / exact(0.625)
    k0 = exact(1.25) / exact(0.5)

    @cache
    def evaluate(digits: int) -> Bounds:
        pi = pi_interval(digits)
        zero = Interval.rational(0, digits)

        @cache
        def density(radius_squared: Fraction) -> Interval:
            # The sole pupil phasor has unit modulus for every defocus.
            j0 = bessel_from_square(pi.squared() * (frequency**2 * radius_squared / 2))
            return pi * frequency**2 * j0.squared()

        @cache
        def kernel(delta_y: Fraction, delta_x: Fraction) -> Interval:
            return sum(
                (
                    density(
                        (delta_y + dy * Fraction(2 * sy + 1, 2 * py)) ** 2
                        + (delta_x + dx * Fraction(2 * sx + 1, 2 * px)) ** 2
                    )
                    for sy in range(py)
                    for sx in range(px)
                ),
                start=zero,
            ) * (dy * dx / (py * px))

        # Independent spatial Fourier moments, before adding any exposure phase.
        basis = []
        axial = []
        for qy_float, qx_float in carriers:
            qy, qx = exact(qy_float), exact(qx_float)
            basis.append(
                tuple(
                    (
                        *reversed(sin_cos(2 * pi * (qy * y + qx * x))),
                        *reversed(sin_cos(4 * pi * (qy * y + qx * x))),
                    )
                    for y in source_y
                    for x in source_x
                )
            )
            kappa = k0 - Interval.rational(k0**2 - qy**2 - qx**2, digits).sqrt()
            planes = []
            for focus in focuses:
                cosine, sine = zero, zero
                for z, weight_z in zip(source_z, wz, strict=True):
                    sz, cz = sin_cos(2 * pi * kappa * (z - focus))
                    cosine += weight_z * cz
                    sine += weight_z * sz
                planes.append((cosine, sine))
            axial.append(tuple(planes))

        lateral = []
        for iy in range(ny):
            for ix in range(nx):
                mass = zero
                moments = [[zero, zero, zero, zero] for _ in carriers]
                for jy, y in enumerate(source_y):
                    for jx, x in enumerate(source_x):
                        contribution = kernel(iy * dy - y, ix * dx - x) * (wy[jy] * wx[jx])
                        mass += contribution
                        j = jy * len(wx) + jx
                        for o, row in enumerate(basis):
                            for harmonic, factor in enumerate(row[j]):
                                moments[o][harmonic] += contribution * factor
                lateral.append((mass, tuple(tuple(row) for row in moments)))

        targets = []
        for o, phase_row in enumerate(phases):
            for phase in phase_row:
                sp, cp = sin_cos(Interval.rational(exact(phase), digits))
                s2p, c2p = sin_cos(Interval.rational(2 * exact(phase), digits))
                for axial_cosine, axial_sine in axial[o]:
                    for mass, moments in lateral:
                        c1, s1, c2, s2 = moments[o]
                        cos_theta = c1 * cp - s1 * sp
                        sin_theta = s1 * cp + c1 * sp
                        cos_twice_theta = c2 * c2p - s2 * s2p
                        targets.append(
                            axial_mass * (mass + (2 * plus * minus / norm) * cos_twice_theta)
                            + (2 * a0 / norm)
                            * (
                                (plus + minus) * axial_cosine * cos_theta
                                + (plus - minus) * axial_sine * sin_theta
                            )
                        )
        unilluminated = tuple(axial_mass * mass for mass, _ in lateral)
        peak = Interval(max(u.lo for u in unilluminated), max(u.hi for u in unilluminated), digits)
        return tuple(targets), peak

    return Reference((len(carriers), len(phases[0]), nz, ny, nx), evaluate)


@cache
def large_reference() -> Reference:
    return separable_reference(LARGE_WEIGHTS, LARGE_SPACING, (1, 2, 2))


REFINEMENT_WEIGHTS: AxisWeights = (
    tuple(Fraction(z, 8) for z in (1, 2, 3, 5)),
    tuple(Fraction(y, 4) for y in (1, 3, 2, 5)),
    tuple(Fraction(x, 4) for x in (2, 1, 5, 3)),
)


def refinement_arguments(beams: tuple[float, float, float]) -> dict[str, Any]:
    """Complete independent source/pixel refinement and beam-positive family."""
    args = arguments()
    wz, wy, wx = REFINEMENT_WEIGHTS
    args.update(
        source_e=np.array([[[float(z * y * x) for x in wx] for y in wy] for z in wz]),
        detector_spacing_um_zyx=SPACING,
        beam_amplitudes=beams,
        pupil_order=1,
        pixel_subsamples_yx=(2, 3),
    )
    return args


@cache
def refinement_reference(beams: tuple[float, float, float]) -> Reference:
    return separable_reference(REFINEMENT_WEIGHTS, SPACING, (2, 2, 2), beams=beams, pixels=(2, 3))
