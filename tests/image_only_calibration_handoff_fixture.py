"""RA12 public fixtures and independent finite-field/rational geometry observers.

No implementation discovery. Generator values stay in this evaluator fixture.
"""

import math
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product

import numpy as np
from scripts.image_only_calibration_pilot import PilotCandidate
from scripts.simulation_optics import expected_images
from scripts.simulation_sources import make_sources

from simrecon import estimate_scalar_camera

D = (0.125, 0.080, 0.080)
SMALL = (1, 3, 7)
SPEC = (3, 2, 3)
SD = (0.21, 0.17, 0.11)
ORIGIN = (-0.25, 0.31, -0.27)
SPEC_ORIGIN = (0.12, -0.19, 0.43)
# 410 decimal digits leave >90 digits after reducing float64-scale angles.
PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647093844609550582231725359408128481117450284102701938521105559644622948954930381964428810975665933446128475648233786783165271201909145648566923460348610454326648213393607260249141273724587006606315588174881520920962829254091715364367892590360011330530548820466521384146951941511609433057270365759591953092186117381932611793"
)
FIELD_ATOL = 2e-11
PHASE_ATOL = 2e-12
# Direct finite optical allowance is 1e-5*T per prediction. Comparing two
# predictions costs 2e-5*T. Symmetric-pair controls use 8e-5*T to include
# separate response assembly, summation and the independent reference peak.
OPTICAL_BUDGET = 8e-5


def camera():
    """Measured finite constant frames: blank=7, flat=11; no gain estimate."""
    return estimate_scalar_camera(
        np.full((2, 2, 2), -2.0),
        blank_counts=np.full((2, 2, 2), 7.0),
        flat_counts=np.full((2, 2, 2), 11.0),
        source=" RA12 finite primary-camera control ",
    )


def candidate(*, beams=(4.0, 2.0, 1.0), shape=SMALL, zero=False):
    centers = np.array([[0.0625, 0.12, x] for x in (0.08, 0.28, 0.48)])
    if shape != SMALL:
        centers[:, 2] = (0.20, 0.96, 1.72)
    return PilotCandidate(
        centers_um_zyx=centers,
        brightness_relative=np.array([0.7, 1.1, 0.9]) * (0 if zero else 1),
        carriers_yx_per_um=np.array([[0.6, 1.1], [-0.8, 0.5], [1.0, -0.4]]),
        phases_rad=np.array([[0.17 + 0.29 * o + 0.61 * p for p in range(9)] for o in range(3)]),
        beam_amplitudes=np.array(beams),
        # Deliberately untrusted but well-shaped metadata; audit must rebuild it.
        occupied_counts=(1, 1, 1),
        stored_unit_masses_e=np.array([99.0, 98.0, 97.0]),
    )


def audit_kwargs(**changes):
    values = dict(
        calibration_shape_zyx=SMALL,
        calibration_origin_um_zyx=ORIGIN,
        specimen_detector_shape_zyx=SPEC,
        specimen_detector_spacing_um_zyx=SD,
        specimen_origin_um_zyx=SPEC_ORIGIN,
        camera_estimate=camera(),
        calibration_atol=1e-4,
        operator_atol=1e-7,
        source=" RA12 supplied diagnostic ",
    )
    values.update(changes)
    return values


def physical_transfer(phases, carriers, origin, destination):
    """Independent exact-float-input Decimal modular transfer; no rounded tau."""
    out = np.empty((3, 5))
    with localcontext() as ctx:
        ctx.prec = 440
        tau = 2 * PI
        for o, p in product(range(3), range(5)):
            turns = sum(
                Decimal.from_float(float(carriers[o, a]))
                * (
                    Decimal.from_float(float(destination[a + 1]))
                    - Decimal.from_float(float(origin[a + 1]))
                )
                for a in range(2)
            )
            v = Decimal.from_float(float(phases[o, p])) + tau * turns
            r = v % tau
            if r < -PI:
                r += tau
            if r >= PI:
                r -= tau
            f = float(r)
            out[o, p] = -math.pi if f >= math.pi else f
    return out


def physical_shift(phases, pi_multiple, *, carrier_anchor=None):
    """Reduce the complete physical phase expression before float64 storage.

    carrier_anchor=(sign, axis_size, spacing, bead0_center) subtracts the
    signed calibration-box frequency times its bead-0 anchor in cycles.
    """
    out = np.empty(phases.shape)
    with localcontext() as ctx:
        ctx.prec = 440
        tau = 2 * PI
        offset = Decimal.from_float(float(pi_multiple)) * PI
        if carrier_anchor is not None:
            sign, size, spacing, center = carrier_anchor
            offset -= (
                tau
                * Decimal(sign)
                * Decimal.from_float(float(center))
                / (Decimal(size) * Decimal.from_float(float(spacing)))
            )
        for index in np.ndindex(phases.shape):
            value = Decimal.from_float(float(phases[index])) + offset
            reduced = value % tau
            if reduced < -PI:
                reduced += tau
            if reduced >= PI:
                reduced -= tau
            stored = float(reduced)
            out[index] = -math.pi if stored >= math.pi else stored
    return out


def field(c, *, shape=SPEC, spacing=SD, origin=ORIGIN, destination=SPEC_ORIGIN):
    """Evaluate all finite sites with Decimal sqrt and Taylor trigonometry."""
    phases = physical_transfer(c.phases_rad, c.carriers_yx_per_um, origin, destination)
    values = np.empty((3, 5, 2 * shape[0] - 1, 2 * shape[1], 2 * shape[2]))
    with localcontext() as ctx:
        ctx.prec = 75

        def dec(x):
            return Decimal.from_float(float(x))

        a0, ap, am = (dec(a) for a in c.beam_amplitudes)
        s = a0 * a0 + ap * ap + am * am
        u, v, w = 2 * a0 * (ap + am) / s, 2 * a0 * (ap - am) / s, 2 * ap * am / s
        dz = [j * dec(spacing[0]) for j in range(1 - shape[0], shape[0])]
        yy = [(Decimal(j) + Decimal("0.5")) * dec(spacing[1]) / 2 for j in range(2 * shape[1])]
        xx = [(Decimal(j) + Decimal("0.5")) * dec(spacing[2]) / 2 for j in range(2 * shape[2])]
        for o in range(3):
            qy, qx = (dec(q) for q in c.carriers_yx_per_um[o])
            k0 = dec(1.515) / dec(0.488)
            kappa = (qy * qy + qx * qx) / (k0 + (k0 * k0 - qy * qy - qx * qx).sqrt())
            axial = [decimal_sincos(2 * PI * kappa * d) for d in dz]
            for p, y, x in product(range(5), range(len(yy)), range(len(xx))):
                theta = 2 * PI * (qy * yy[y] + qx * xx[x]) + dec(phases[o, p])
                st, ct = decimal_sincos(theta)
                _, c2t = decimal_sincos(2 * theta)
                for z, (sa, ca) in enumerate(axial):
                    values[o, p, z, y, x] = float(1 + u * ca * ct + v * sa * st + w * c2t)
    return values


def decimal_sincos(value):
    """Bound Taylor tails below 1e-65 after physical reduction to [-pi,pi]."""
    r = value % (2 * PI)
    if r > PI:
        r -= 2 * PI
    if r < -PI:
        r += 2 * PI
    square = r * r
    sine, cosine = r, Decimal(1)
    ts, tc = r, Decimal(1)
    for j in range(1, 100):
        ts *= -square / ((2 * j) * (2 * j + 1))
        tc *= -square / ((2 * j - 1) * (2 * j))
        sine += ts
        cosine += tc
        if max(abs(ts), abs(tc)) < Decimal("1e-68"):
            return sine, cosine
    raise AssertionError("independent Taylor observer did not complete")


def exact_occupied(center, shape=SMALL):
    """Rational closed-sphere membership, bounded to a tiny enclosing cube."""
    cf = tuple(Fraction(float(x)) for x in center)
    dd = tuple(Fraction(x) / 8 for x in D)
    radius = Fraction(0.050)
    axes = []
    for a in range(3):
        axes.append(
            [
                (j, (Fraction(j) + Fraction(1, 2)) * dd[a])
                for j in range(shape[a] * 8)
                if abs((Fraction(j) + Fraction(1, 2)) * dd[a] - cf[a]) <= radius
            ]
        )
    sites = []
    for items in product(*axes):
        if sum((items[a][1] - cf[a]) ** 2 for a in range(3)) <= radius**2:
            sites.append(tuple(item[0] for item in items))
    return sites


def unit_source(center, shape):
    row = np.array([[*center, 0.050, 1.0]])
    return make_sources(
        row, detector_shape_zyx=shape, detector_spacing_um_zyx=D, source_refinement_zyx=(8, 8, 8)
    )


def optical(source, carriers, phases, beams, *, spacing=D, refinement=(8, 8, 8)):
    return expected_images(
        source,
        detector_spacing_um_zyx=spacing,
        source_refinement_zyx=refinement,
        carriers_yx_per_um=carriers,
        phases_rad=phases,
        beam_amplitudes=tuple(float(x) for x in beams),
        excitation_um=0.488,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=128,
        pixel_subsamples_yx=(2, 2),
    )


def prediction(c, shape=SMALL):
    central = np.zeros(shape)
    structured = np.zeros((3, 9, *shape))
    for center, brightness in zip(c.centers_um_zyx, c.brightness_relative, strict=True):
        src = unit_source(center, shape)
        central += brightness * optical(src, np.zeros((1, 2)), np.zeros((1, 1)), (1, 0, 0))[0, 0]
        structured += brightness * optical(
            src, c.carriers_yx_per_um, c.phases_rad, c.beam_amplitudes
        )
    return central, structured


def alternatives(c, shape=SMALL):
    """Enumerate transformations in order using observer labels, not API IDs."""
    cases = []

    def add(label, **updates):
        cases.append((label, replace(c, **updates)))

    swap = c.beam_amplitudes[[0, 2, 1]].copy()
    add(
        "global",
        carriers_yx_per_um=-c.carriers_yx_per_um,
        phases_rad=physical_shift(-c.phases_rad, 0),
        beam_amplitudes=swap,
    )
    add("beam_swap", beam_amplitudes=swap)
    centers = c.centers_um_zyx.copy()
    centers[:, 0] = shape[0] * D[0] - centers[:, 0]
    add("reflection", centers_um_zyx=centers, beam_amplitudes=swap)
    a0, ap, am = (float(a) for a in c.beam_amplitudes)
    discriminant = a0 * a0 - 4 * ap * am
    if discriminant >= 0:
        norm = math.sqrt(a0 * a0 + ap * ap + am * am)
        root = np.array(
            [
                (ap + am) / norm,
                (a0 + math.sqrt(discriminant)) / (2 * norm),
                (a0 - math.sqrt(discriminant)) / (2 * norm),
            ]
        )
        add("root", beam_amplitudes=root)
        add("root_swap", beam_amplitudes=root[[0, 2, 1]])
    else:
        cases.extend([("root", None), ("root_swap", None)])
    for b, a, sign in product(range(3), range(3), (-1, 1)):
        centers = c.centers_um_zyx.copy()
        centers[b, a] += sign * D[a] / 8
        add(f"center:{b}:{a}:{sign}", centers_um_zyx=centers)
    for o, a, sign in product(range(3), range(2), (-1, 1)):
        q, ph = c.carriers_yx_per_um.copy(), c.phases_rad.copy()
        delta = sign / (shape[a + 1] * D[a + 1])
        q[o, a] += delta
        ph[o] = physical_shift(
            c.phases_rad[o],
            0,
            carrier_anchor=(sign, shape[a + 1], D[a + 1], c.centers_um_zyx[0, a + 1]),
        )
        add(f"carrier:{o}:{a}:{sign}", carriers_yx_per_um=q, phases_rad=ph)
    for o, a in product(range(3), range(2)):
        q = c.carriers_yx_per_um.copy()
        q[o, a] *= -1
        add(f"component:{o}:{a}", carriers_yx_per_um=q)
    for o, p in product(range(3), range(9)):
        ph = c.phases_rad.copy()
        ph[o, p] = physical_shift(-c.phases_rad[o, p : p + 1], 0)[0]
        add(f"phase_neg:{o}:{p}", phases_rad=ph)
        ph = c.phases_rad.copy()
        ph[o, p] = physical_shift(c.phases_rad[o, p : p + 1], 1)[0]
        add(f"phase_pi:{o}:{p}", phases_rad=ph)
    for o, multiple in product(range(3), (0.5, 1.0, 1.5)):
        ph = c.phases_rad.copy()
        ph[o] = physical_shift(c.phases_rad[o], multiple)
        add(f"common:{o}:{multiple * math.pi}", phases_rad=ph)
    return cases


def feasible(c, shape=SMALL):
    if c is None:
        return False
    with localcontext() as ctx:
        ctx.prec = 100
        for row in c.carriers_yx_per_um:
            if (
                sum(Decimal.from_float(float(v)) ** 2 for v in row)
                > (Decimal.from_float(1.515) / Decimal.from_float(0.488)) ** 2
            ):
                return False
        radius = Fraction(0.050)
        centers = [[Fraction(float(x)) for x in row] for row in c.centers_um_zyx]
        for row in centers:
            if any(
                v - radius < 0 or v + radius > shape[a] * Fraction(D[a]) for a, v in enumerate(row)
            ):
                return False
        for i, j in ((0, 1), (0, 2), (1, 2)):
            if sum((centers[i][a] - centers[j][a]) ** 2 for a in range(3)) < (2 * radius) ** 2:
                return False
    return True
