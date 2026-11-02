"""Independent finite-equation observers for the image-only pilot contract.

These observers do not call simulation sources, optics, camera or the pilot.
Fraction arithmetic determines closed source membership and inward containment.
The optical observer sums complex fields directly, without a harmonic inverse.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.special import j0, roots_legendre

from simrecon import ScalarCameraEstimate
from simulation_optics_fixture import Interval, OracleInconclusive, pi_interval, sin_cos
from simulation_optics_q128_fixture import legendre_sign

F64 = NDArray[np.float64]
D = (0.125, 0.080, 0.080)
REFINEMENT = (8, 8, 8)
RADIUS = 0.050
SHAPE = (1, 2, 15)
COMMANDS = np.array(
    [
        *(2 * math.pi * j / 5 for j in range(5)),
        math.pi / 5,
        3 * math.pi / 5,
        7 * math.pi / 5,
        9 * math.pi / 5,
    ]
)
EPS = np.finfo(np.float64).eps
E = Fraction(float(EPS))
TINY = Fraction(1, 2**1074)


def gamma(count: int) -> Fraction:
    """Conservative binary64 basic-operation bound (eps, rather than eps/2)."""
    if count * E >= 1:
        raise OracleInconclusive("pilot observer operation bound is unresolved")
    return count * E / (1 - count * E)


def upper_float(value: Fraction) -> float:
    """Convert a nonnegative bound outward, never rounding a tolerance down."""
    result = float(value)
    if not math.isfinite(result):
        raise OracleInconclusive("pilot observer bound is not finite")
    return float(np.nextafter(result, np.inf)) if Fraction(result) < value else result


def interval_midpoint(value: Interval) -> tuple[float, Fraction]:
    """Represent an interval by a binary64 center and exact rational radius."""
    lo, hi = Fraction(value.lo), Fraction(value.hi)
    center = float((lo + hi) / 2)
    return center, max(abs(Fraction(center) - lo), abs(Fraction(center) - hi))


@dataclass(frozen=True)
class OpticalEnclosure:
    """Complete floating image with a uniform absolute reference-error bound."""

    values: F64
    radius: Fraction


@dataclass(frozen=True)
class PredictionAllowance:
    """Separate unchanged product allowance from uncertainty of the observer."""

    product_lo: Fraction
    product_hi: Fraction
    reference: Fraction

    @property
    def total(self) -> Fraction:
        return self.product_hi + self.reference


def prediction_decision(observed: float, expected: float, bound: PredictionAllowance) -> str:
    """Three-way exact decision: interval ambiguity is never a product violation."""
    if not math.isfinite(observed):
        return "violation"
    difference = abs(Fraction(observed) - Fraction(expected))
    if difference + bound.reference <= bound.product_lo:
        return "within"
    if difference > bound.product_hi + bound.reference:
        return "violation"
    return "inconclusive"


def assert_prediction_close(actual: F64, expected: F64, bound: PredictionAllowance) -> None:
    """Reject only proved violations; unresolved precision blocks the check."""
    assert actual.shape == expected.shape
    unresolved = False
    for observed, target in zip(actual.flat, expected.flat, strict=True):
        decision = prediction_decision(float(observed), float(target), bound)
        assert decision != "violation", "certified pilot prediction-envelope violation"
        unresolved |= decision == "inconclusive"
    if unresolved:
        raise OracleInconclusive("pilot prediction comparison overlaps its reference uncertainty")


def assert_scalar_close(actual: float, expected: float, allowance: Fraction) -> None:
    """Compare represented scalar values without rounding their difference/bound."""
    assert math.isfinite(actual) and math.isfinite(expected)
    assert abs(Fraction(actual) - Fraction(expected)) <= allowance


@lru_cache(maxsize=1)
def bessel_polynomials() -> tuple[F64, Fraction]:
    """Certified local J0 Taylor polynomials for |t|<=24, degree20, |h|<=1/2.

    Each coefficient is the exact 100-term differentiated defining series at
    an integer anchor. The remaining k-series has a decreasing geometric
    majorant. From J0(t)=mean_theta cos(t*cos(theta)), |J0^(m)|<=1; hence the
    local Taylor remainder is <=(1/2)^21/21!. This identity follows directly
    by integrating the cosine series and its even powers.
    """
    coefficients = np.empty((25, 21))
    coefficient_error = Fraction(0)
    for anchor in range(25):
        errors = Fraction(0)
        for degree in range(21):

            def term(k: int, degree: int = degree, anchor: int = anchor) -> Fraction:
                return Fraction(
                    (-1) ** k * math.comb(2 * k, degree) * anchor ** (2 * k - degree),
                    4**k * math.factorial(k) ** 2,
                )

            first = (degree + 1) // 2
            partial = sum((term(k) for k in range(first, 101)), Fraction(0))
            ratio = Fraction(anchor**2 * 204 * 203, 4 * 102**2 * (204 - degree) * (203 - degree))
            assert ratio < 1
            tail = abs(term(101)) / (1 - ratio)
            represented = float(partial)
            coefficients[anchor, degree] = represented
            errors += (abs(Fraction(represented) - partial) + tail) / 2**degree
        coefficient_error = max(coefficient_error, errors)
    # Horner has 40 operations, exact h subtraction, |h|<=1/2 and
    # sum |J0^(m)/m!|*(1/2)^m <= exp(1/2)<2. 64 ops also cover
    # coefficient rounding in this majorant; subnormal errors are additive.
    error = coefficient_error + Fraction(1, 2**21 * math.factorial(21))
    error += gamma(64) * 2 + 256 * TINY
    return coefficients, error


def bounded_j0(arguments: F64) -> F64:
    """Evaluate the certified local polynomials, without a special-function oracle."""
    if not np.isfinite(arguments).all() or np.max(np.abs(arguments)) > 24:
        raise OracleInconclusive("pilot J0 observer domain is |argument|<=24")
    arguments = np.abs(arguments)
    anchors = np.rint(arguments).astype(np.int64)
    h = arguments - anchors  # Exact by Sterbenz, or subtraction of zero.
    coefficients, _ = bessel_polynomials()
    result = coefficients[anchors, -1]
    with np.errstate(under="ignore"):
        for degree in range(19, -1, -1):
            result = result * h + coefficients[anchors, degree]
    return result


@lru_cache(maxsize=1)
def trig_error() -> Fraction:
    """Uniform per-component error for bounded_cis on |angle|<=128."""
    pi = pi_interval(60)
    pi_error = max(abs(Fraction(math.pi) - Fraction(v)) for v in (pi.lo, pi.hi))
    # Integer-turn choice need not be exact-nearest. The checked remainder
    # lies in [-4,4]; |turns|<=21. Include subtraction/multiplication error.
    reduction = 42 * pi_error + gamma(4) * 512 + 16 * TINY
    # Degree35 sine/degree34 cosine: remainder <=4^36/36!.
    # Absolute monomial sum <=exp(4)<64; 128 operations cover powers,
    # Horner, coefficient conversion and the final sine multiplication.
    return reduction + Fraction(4**36, math.factorial(36)) + gamma(128) * 64 + 1024 * TINY


def bounded_cis(angles: F64) -> NDArray[np.complex128]:
    """Independently bounded cos+i*sin; no assumed libm/complex-exp accuracy."""
    if not np.isfinite(angles).all() or np.max(np.abs(angles)) > 128:
        raise OracleInconclusive("pilot phase observer domain is |angle|<=128")
    with np.errstate(under="ignore"):
        turns = np.rint(angles / (2 * math.pi))
        reduced = angles - turns * (2 * math.pi)
    if np.max(np.abs(reduced)) > 4 or np.max(np.abs(turns)) > 21:
        raise OracleInconclusive("pilot phase reduction did not meet its finite bound")
    with np.errstate(under="ignore"):
        square = reduced * reduced
        results = []
        for odd in (False, True):
            value = np.zeros_like(reduced)
            for k in range(17, -1, -1):
                value = value * square + float(
                    Fraction((-1) ** k, math.factorial(2 * k + int(odd)))
                )
            results.append(value * reduced if odd else value)
    return results[0] + 1j * results[1]


def legendre_value(order: int, x: Fraction) -> Fraction:
    """Exact P_order(x), via the independently checked integer recurrence."""
    if order == 0:
        return Fraction(1)
    a, b = x.numerator, x.denominator
    previous, current = 1, a
    for n in range(2, order + 1):
        previous, current = current, (2 * n - 1) * a * current - (n - 1) ** 2 * b * b * previous
    return Fraction(current, math.factorial(order) * b**order)


@lru_cache(maxsize=4)
def enclosed_rule(order: int) -> tuple[F64, F64, F64, Fraction, Fraction, Fraction]:
    """Certify Q=1/128/256/512 from proposals; retain all weight uncertainty.

    Exact sign changes and disjoint intervals exhaust the polynomial degree.
    |P'_(n-1)|<=(n-1)n/2 bounds P_(n-1) over each bracket, giving canonical
    weights without relying on SciPy weight accuracy or renormalization.
    A fixed dyadic proposal is refined to width<=2^-64 by exact signs.
    Proposal failure is an observer limit, never a product-domain cap.
    """
    if order not in (1, 128, 256, 512):
        raise OracleInconclusive("pilot observer supports only Q=1,128,256,512")
    proposals, _ = roots_legendre(order)
    positive = []
    # The three-term recurrence gives P_n(-x)=(-1)^n P_n(x).
    # For these even orders, positive sign-changing brackets reflect exactly.
    # Disjointness and the final degree count certify every reflected root.
    for proposed in proposals[order // 2 :] if order > 1 else ():
        center = Fraction(float(proposed))
        lo, hi = center - Fraction(1, 2**48), center + Fraction(1, 2**48)
        left, right = legendre_sign(order, lo), legendre_sign(order, hi)
        if left * right != -1:
            raise OracleInconclusive("pilot Legendre proposal has no certified local bracket")
        while hi - lo > Fraction(1, 2**64):
            middle = (lo + hi) / 2
            sign = legendre_sign(order, middle)
            if sign == 0:
                raise OracleInconclusive("unexpected exact rational Legendre root")
            if sign == left:
                lo = middle
            else:
                hi = middle
        if not 0 < lo < hi < 1:
            raise OracleInconclusive("pilot Legendre positive bracket is outside (0,1)")
        positive.append((lo, hi, (lo + hi) / 2))
    brackets = (
        [(Fraction(0), Fraction(0), Fraction(0))]
        if order == 1
        else sorted(positive + [(-hi, -lo, -center) for lo, hi, center in positive])
    )
    if (
        len(brackets) != order
        or any(not (-1 < lo <= hi < 1) for lo, hi, _ in brackets)
        or any(a[1] >= b[0] for a, b in zip(brackets, brackets[1:], strict=False))
    ):
        raise OracleInconclusive("pilot Legendre brackets do not exhaust distinct roots")
    pi = pi_interval(60)
    r, nu, beta = (
        Fraction(1.4) / Fraction(0.525),
        Fraction(1.515) / Fraction(0.525),
        Fraction(1.4) / Fraction(1.515),
    )
    weights, radial, axial = [], [], []
    weight_error = radial_error = axial_error = Fraction(0)
    reflected_weights: dict[Fraction, tuple[float, Fraction]] = {}
    for lo, hi, center in brackets:
        x = Interval(Interval.rational(lo, 60).lo, Interval.rational(hi, 60).hi, 60)
        if abs(center) not in reflected_weights:
            value = legendre_value(order - 1, center)
            perturbation = Fraction((order - 1) * order, 2) * max(center - lo, hi - center)
            p = Interval(
                Interval.rational(value - perturbation, 60).lo,
                Interval.rational(value + perturbation, 60).hi,
                60,
            )
            if p.lo <= 0 <= p.hi:
                raise OracleInconclusive("pilot weight denominator is unresolved")
            # Both x^2 and P_(n-1)(x)^2 are invariant under exact reflection.
            reflected_weights[abs(center)] = interval_midpoint(
                (1 - x.squared()) / (order**2 * p.squared())
            )
        weight, ew = reflected_weights[abs(center)]
        u = (1 + x) / 2
        radial_factor, er = interval_midpoint(2 * pi * r * u.sqrt())
        axial_factor, ea = interval_midpoint(2 * pi * nu * ((1 - beta**2 * u).sqrt() - 1))
        weights.append(weight)
        radial.append(radial_factor)
        axial.append(axial_factor)
        weight_error += ew
        radial_error, axial_error = max(radial_error, er), max(axial_error, ea)
    return (
        np.array(weights),
        np.array(radial),
        np.array(axial),
        weight_error,
        radial_error,
        axial_error,
    )


def camera(**changes: Any) -> ScalarCameraEstimate:
    """Construct the real public record; unused fields deliberately carry no truth."""
    values: dict[str, Any] = {
        "means_counts": np.array([-7.0, 5.0, 7.0]),
        "variances_counts2": np.array([3.0, 4.0, 2.0]),
        "frame_means_counts": tuple(np.zeros(2) for _ in range(3)),
        "frame_variances_counts2": tuple(np.zeros(2) for _ in range(3)),
        "empirical_mean_se_counts": np.zeros(3),
        "contrast_counts": 2.0,
        "gain_counts_per_e": None,
        "information_codes": ("nonpositive_variance_contrast",),
        "source": "opaque estimated camera",
    }
    values.update(changes)
    return ScalarCameraEstimate(**values)


def observations(
    *, edge: bool = False, shape: tuple[int, int, int] = SHAPE
) -> tuple[F64, F64, F64]:
    """Provide three resolvable peaks, signed tails, and asymmetric training data."""
    y = np.full(shape, -0.03125, dtype=np.float64)
    peaks = (0, 7, 14)
    for x, height in zip(peaks, (8.0, 6.0, 4.0), strict=True):
        y[0, 0, x] = height
    structured = np.empty((3, 9, *shape))
    for o in range(3):
        for p in range(9):
            structured[o, p] = (o + 1) / 8 + (p - 4) / 16 + y / (4 + o)
    heldout = np.arange(15 * math.prod(shape), dtype=np.float64).reshape(3, 5, *shape)
    heldout = (heldout % 17 - 8) / 16
    return 5 + 2 * y, 5 + 2 * structured, 5 + 2 * heldout


def inward_upper(n: int, spacing: float) -> float:
    """Round the exact normalized-input containment upper bound toward the interior."""
    exact = n * Fraction(spacing) - Fraction(RADIUS)
    value = float(exact)
    return float(np.nextafter(value, -np.inf)) if Fraction(value) > exact else value


def finite_gaussian(y: F64) -> F64:
    """Apply the normalized finite nine-tap product kernel with a zero exterior."""
    weights = [math.exp(-i * i / 2) for i in range(-4, 5)]
    total = math.fsum(weights)
    weights = [v / total for v in weights]
    out = y.copy()
    for axis in range(3):
        old = out
        out = np.zeros_like(old)
        for index in np.ndindex(y.shape):
            terms = []
            for shift, weight in zip(range(-4, 5), weights, strict=True):
                other = list(index)
                other[axis] += shift
                if 0 <= other[axis] < y.shape[axis]:
                    terms.append(weight * float(old[tuple(other)]))
            out[index] = math.fsum(terms)
    return out


def initialization(y: F64) -> tuple[F64, F64, tuple[tuple[int, int, int], ...]]:
    """Calculate observation-only peaks, clipped windows, clamped centroids and maxima."""
    smooth = finite_gaussian(y)
    available = np.ones(y.shape, dtype=bool)
    sites = np.stack(np.meshgrid(*(np.arange(n) for n in y.shape), indexing="ij"), axis=-1)
    centers, maxima, selected = [], [], []
    for _ in range(3):
        ordered = sorted(np.ndindex(y.shape), key=lambda i: (-smooth[i], i))
        peak = next((i for i in ordered if available[i] and smooth[i] > 0), None)
        if peak is None:
            raise ValueError("fewer than three positive peaks")
        selected.append(peak)
        distance2 = np.sum(((sites - np.array(peak)) * np.array(D)) ** 2, axis=-1)
        available[distance2 <= 0.5**2] = False
        slices = tuple(
            slice(max(0, p - r), min(n, p + r + 1))
            for p, r, n in zip(peak, (2, 3, 3), y.shape, strict=True)
        )
        indices = list(itertools.product(*(range(s.start, s.stop) for s in slices)))
        weights = [max(float(y[i]), 0.0) for i in indices]
        mass = math.fsum(weights)
        if mass <= 0:
            raise ValueError("zero centroid weight")
        center = []
        for axis in range(3):
            raw = (
                math.fsum(
                    w * (i[axis] + 0.5) * D[axis] for i, w in zip(indices, weights, strict=True)
                )
                / mass
            )
            center.append(min(max(raw, RADIUS), inward_upper(y.shape[axis], D[axis])))
        centers.append(center)
        maxima.append(max(float(y[i]) for i in indices))
    c = np.array(centers)
    if any(math.dist(c[a], c[b]) < 2 * RADIUS for a, b in itertools.combinations(range(3), 2)):
        raise ValueError("overlapping centroids")
    return c, np.array(maxima), tuple(selected)


@lru_cache(maxsize=256)
def unit_sites(
    center: tuple[float, float, float], shape: tuple[int, int, int]
) -> tuple[F64, int, float]:
    """Count exact closed midpoint sphere membership and round one-electron weights."""
    c = tuple(Fraction(v) for v in center)
    a2 = Fraction(RADIUS) ** 2
    ranges = []
    for axis in range(3):
        step = Fraction(D[axis]) / 8
        # A conservative index box only accelerates the exact final predicate.
        lo = max(0, math.floor((c[axis] - Fraction(RADIUS)) / step - Fraction(1, 2)) - 1)
        hi = min(shape[axis] * 8, math.ceil((c[axis] + Fraction(RADIUS)) / step) + 1)
        ranges.append(range(lo, hi))
    sites = []
    for index in itertools.product(*ranges):
        point = tuple(
            (Fraction(j) + Fraction(1, 2)) * Fraction(d) / 8 for j, d in zip(index, D, strict=True)
        )
        if sum((r - v) ** 2 for r, v in zip(point, c, strict=True)) <= a2:
            sites.append(tuple(float(r) for r in point))
    count = len(sites)
    if not count:
        raise ValueError("no occupied midpoint")
    weight = float(Fraction(1, count))
    mass = float(count * Fraction(weight))
    return np.array(sites), count, mass


@lru_cache(maxsize=16)
def detector_reference(
    site_shape: tuple[int, ...],
    site_bytes: bytes,
    shape: tuple[int, int, int],
    order: int,
) -> bytes:
    """Immutable detector sums keyed by exact sites, shape and finite pupil order.

    D, 2x2 pixel samples and the optical constants in enclosed_rule are fixed
    reference inputs. Illumination, source weight and brightness do not enter
    this detector-only equation. Bytes preserve represented sites exactly and
    prevent callers from exposing writable cached state.
    """
    sites = np.frombuffer(site_bytes, dtype=np.float64).reshape(site_shape)
    w, radial_factor, axial_factor, _, _, _ = enclosed_rule(order)
    scale, _ = interval_midpoint(pi_interval(60) * (Fraction(1.4) / Fraction(0.525)) ** 2)
    detector = np.empty((*shape, len(sites)))
    with np.errstate(under="ignore"):
        for z in range(shape[0]):
            displacement = sites[:, 0] - (z + 0.5) * D[0]
            axial = bounded_cis(displacement[:, None] * axial_factor)
            for y, x in itertools.product(range(shape[1]), range(shape[2])):
                h = np.zeros(len(sites))
                for py, px in itertools.product(range(2), repeat=2):
                    ry = (y + (py + 0.5) / 2) * D[1] - sites[:, 1]
                    rx = (x + (px + 0.5) / 2) * D[2] - sites[:, 2]
                    radial = np.sqrt(ry * ry + rx * rx)
                    a = np.sum(
                        w * bounded_j0(radial[:, None] * radial_factor) * axial,
                        axis=1,
                    )
                    h += scale * (a.real * a.real + a.imag * a.imag)
                detector[z, y, x] = h
    return detector.tobytes()


def uncached_optical_enclosure(
    sites: F64,
    weight: float,
    shape: tuple[int, int, int],
    carriers: F64,
    phases: F64,
    amplitudes: F64,
    order: int,
) -> OpticalEnclosure:
    """Complete direct sum with certified finite-domain forward uncertainty.

    Observer domain only: shape <=(9,5,16), <=1024 rounded source sites,
    positive represented weight with total mass <=2, Q=1/128/256/512,
    |phase|<=8, exact legal carriers and 1/4<=sum(amplitude^2)<=32.
    Sites are exact coordinates or correctly rounded midpoint coordinates;
    their coordinate error is <=eps times the corresponding box length.
    This restricts the test observer, never the product's public domain.
    """
    if (
        len(shape) != 3
        or any(not 1 <= n <= limit for n, limit in zip(shape, (9, 5, 16), strict=True))
        or not 1 <= len(sites) <= 1024
        or not np.isfinite(sites).all()
        or not np.isfinite(phases).all()
        or not np.isfinite(carriers).all()
        or np.max(np.abs(phases)) > 8
    ):
        raise OracleInconclusive("pilot optical observer finite geometry domain exceeded")
    lengths = tuple(n * Fraction(d) for n, d in zip(shape, D, strict=True))
    if np.any(sites < 0) or any(np.max(sites[:, a]) > upper_float(lengths[a]) for a in range(3)):
        raise OracleInconclusive("pilot observer sites exceed the declared box")
    mass = len(sites) * Fraction(weight)
    norm_exact = sum((Fraction(float(a)) ** 2 for a in amplitudes), Fraction(0))
    if not 0 < mass <= 2 or not Fraction(1, 4) <= norm_exact <= 32 or np.any(amplitudes < 0):
        raise OracleInconclusive("pilot optical observer mass/amplitude domain exceeded")
    _, radial_factor, axial_factor, ew, er, ea = enclosed_rule(order)
    pi = pi_interval(60)
    pi_hi = Fraction(pi.hi)
    k0 = Fraction(1.515) / Fraction(0.488)
    kappa, kappa_error = [], Fraction(0)
    for row in carriers:
        q2 = sum((Fraction(float(q)) ** 2 for q in row), Fraction(0))
        if q2 > k0**2:
            raise OracleInconclusive("pilot observer received an inadmissible represented carrier")
        value, uncertainty = interval_midpoint(
            Interval.rational(k0, 60) - Interval.rational(k0**2 - q2, 60).sqrt()
        )
        kappa.append(value)
        kappa_error = max(kappa_error, uncertainty)
    kappa_array = np.array(kappa)
    scale, scale_error = interval_midpoint(pi * (Fraction(1.4) / Fraction(0.525)) ** 2)
    scale_hi = Fraction(scale) + scale_error
    # Contain only expected own underflow, already included in the absolute
    # bounds. Domain/overflow errors, dependency warnings and MemoryError are
    # not caught or translated. The caller's arithmetic policy is restored.
    with np.errstate(under="ignore"):
        detector = np.frombuffer(
            detector_reference(sites.shape, sites.tobytes(), shape, order), dtype=np.float64
        ).reshape((*shape, len(sites)))
        theta = 2 * math.pi * (carriers @ sites[:, 1:].T)[:, None, :] + phases[:, :, None]
        side_phase = bounded_cis(theta)
        side = amplitudes[1] * side_phase + amplitudes[2] * side_phase.conjugate()
        out = np.zeros((*phases.shape, *shape))
        single_beam = np.count_nonzero(amplitudes) == 1
        for z in range(shape[0]):
            displacement = sites[:, 0] - (z + 0.5) * D[0]
            field = (
                amplitudes[0] * bounded_cis(2 * math.pi * kappa_array[:, None] * displacement)
            )[:, None, :] + side
            illumination = (
                np.ones(field.shape)
                if single_beam
                else (field.real * field.real + field.imag * field.imag) / float(norm_exact)
            )
            for y, x in itertools.product(range(shape[1]), range(shape[2])):
                h = detector[z, y, x]
                out[:, :, z, y, x] = D[1] * D[2] / 4 * weight * np.sum(illumination * h, axis=-1)

    # Bounds below use rational arithmetic. All norms are absolute majorants;
    # cancellation never produces a smaller error allowance. Basic binary64
    # operations/sqrt are RN; gamma uses twice unit roundoff. The norm floor
    # 2^-530 exceeds sqrt(8*2^-1074), covering underflow in a 2D squared norm.
    lateral = lengths[1] + lengths[2]
    coordinate = gamma(16) * lateral + Fraction(1, 2**530)
    radial_max = max(Fraction(float(v)) for v in radial_factor)
    argument_error = er * lateral + (radial_max + er) * coordinate
    argument_error += gamma(4) * radial_max * (lateral + coordinate)
    j_error = bessel_polynomials()[1] + argument_error  # |J0'|=|J1|<=1.
    z_error = gamma(8) * lengths[0] + Fraction(1, 2**530)
    axial_max = max(abs(Fraction(float(v))) for v in axial_factor)
    detection_phase_error = ea * lengths[0] + (axial_max + ea) * z_error
    detection_phase_error += gamma(4) * axial_max * (lengths[0] + z_error)
    cis_error = 2 * (trig_error() + detection_phase_error)  # Complex modulus <=L1 norm.
    pupil_error = j_error + cis_error + j_error * cis_error
    pupil_error += ew * (1 + j_error) * (1 + cis_error)
    pupil_error += gamma(16 * order + 32) * (1 + ew) * (1 + j_error) * (1 + cis_error)
    density_error = scale_hi * (2 * pupil_error + pupil_error**2)
    density_error += (scale_error + gamma(8) * scale_hi) * (1 + pupil_error) ** 2
    field_phase_error = gamma(32) * (2 * pi_hi * k0 * sum(lengths) + 9)
    field_phase_error += 2 * pi_hi * kappa_error * lengths[0]
    field_error = 2 * (trig_error() + field_phase_error)
    field_error += gamma(16) * (1 + field_error)
    maximum_illumination = (
        sum((Fraction(float(a)) for a in amplitudes), Fraction(0)) ** 2 / norm_exact
    )
    illumination_error = (
        Fraction(0)
        if single_beam
        else maximum_illumination
        * ((2 + field_error) * field_error + gamma(32) * (1 + field_error) ** 2)
    )
    area = Fraction(D[1]) * Fraction(D[2])
    error = (
        area
        * mass
        * (
            maximum_illumination * density_error
            + scale_hi * illumination_error
            + density_error * illumination_error
        )
    )
    error += (
        gamma(16 * len(sites) + 128)
        * area
        * mass
        * (maximum_illumination + illumination_error)
        * (scale_hi + density_error)
    )
    error += Fraction(1, 2**530)
    if not np.isfinite(out).all():
        raise OracleInconclusive("pilot observer arithmetic did not produce finite values")
    return OpticalEnclosure(out, error)


def enclosure_array_key(array: F64) -> tuple[tuple[int, ...], str, bytes]:
    return array.shape, array.dtype.str, array.tobytes(order="C")


@lru_cache(maxsize=128)
def immutable_enclosure(
    sites: tuple[tuple[int, ...], str, bytes],
    weight_hex: str,
    shape: tuple[int, int, int],
    carriers: tuple[tuple[int, ...], str, bytes],
    phases: tuple[tuple[int, ...], str, bytes],
    amplitudes: tuple[tuple[int, ...], str, bytes],
    order: int,
    spacing: tuple[float, float, float],
) -> tuple[tuple[int, ...], str, bytes, Fraction]:
    assert spacing == D
    arrays = [
        np.frombuffer(raw, dtype=np.dtype(dtype)).reshape(dimensions).copy()
        for dimensions, dtype, raw in (sites, carriers, phases, amplitudes)
    ]
    result = uncached_optical_enclosure(
        arrays[0], float.fromhex(weight_hex), shape, arrays[1], arrays[2], arrays[3], order
    )
    return result.values.shape, result.values.dtype.str, result.values.tobytes(), result.radius


def optical_enclosure(
    sites: F64,
    weight: float,
    shape: tuple[int, int, int],
    carriers: F64,
    phases: F64,
    amplitudes: F64,
    order: int,
) -> OpticalEnclosure:
    dimensions, dtype, raw, radius = immutable_enclosure(
        enclosure_array_key(sites),
        float(weight).hex(),
        shape,
        enclosure_array_key(carriers),
        enclosure_array_key(phases),
        enclosure_array_key(amplitudes),
        order,
        D,
    )
    return OpticalEnclosure(
        np.frombuffer(raw, dtype=np.dtype(dtype)).reshape(dimensions).copy(), radius
    )


def optical_sum(
    sites: F64,
    weight: float,
    shape: tuple[int, int, int],
    carriers: F64,
    phases: F64,
    amplitudes: F64,
    order: int,
) -> F64:
    """Floating centers for analytic controls; assertions use the enclosure too."""
    return optical_enclosure(sites, weight, shape, carriers, phases, amplitudes, order).values


def predictions(
    candidate: Any, shape: tuple[int, int, int], order: int
) -> tuple[F64, F64, PredictionAllowance]:
    """Carry independent prediction/T uncertainty alongside the product allowance."""
    central = np.zeros(shape)
    structured = np.zeros((3, 9, *shape))
    product_lo = product_hi = reference_error = scale_bound = Fraction(0)
    for center, brightness in zip(
        candidate.centers_um_zyx, candidate.brightness_relative, strict=True
    ):
        if float(brightness) == 0:
            continue
        sites, count, _ = unit_sites(tuple(float(v) for v in center), shape)
        unit = optical_enclosure(
            sites,
            float(Fraction(1, count)),
            shape,
            np.zeros((1, 2)),
            np.zeros((1, 1)),
            np.array([1.0, 0.0, 0.0]),
            order,
        )
        modulated = optical_enclosure(
            sites,
            float(Fraction(1, count)),
            shape,
            candidate.carriers_yx_per_um,
            candidate.phases_rad,
            candidate.beam_amplitudes,
            order,
        )
        central += float(brightness) * unit.values[0, 0]
        structured += float(brightness) * modulated.values
        b = Fraction(float(brightness))
        peak = Fraction(float(np.max(unit.values)))
        product_lo += b * max(Fraction(0), peak - unit.radius) / 100000
        product_hi += b * (peak + unit.radius) / 100000
        reference_error += b * max(unit.radius, modulated.radius)
        scale_bound += b * max(
            max(abs(Fraction(float(v))) for v in unit.values.flat) + unit.radius,
            max(abs(Fraction(float(v))) for v in modulated.values.flat) + modulated.radius,
        )
    # Three positive brightness products and their additions (or fewer in
    # helper controls). Keep combined-image rounding in reference uncertainty.
    reference_error += gamma(2 * len(candidate.brightness_relative) + 2) * scale_bound
    if scale_bound:
        reference_error += 32 * TINY
    return central, structured, PredictionAllowance(product_lo, product_hi, reference_error)


def objective(y: F64, structured: F64, central_prediction: F64, prediction: F64) -> float:
    """Reduce the complete signed residual square with an independent scalar sum."""
    values = itertools.chain((y - central_prediction).flat, (structured - prediction).flat)
    return math.fsum(float(v) ** 2 for v in values) / (2 * 28 * y.size)


def loss_allowance(
    y: F64, structured: F64, central: F64, prediction: F64, delta: PredictionAllowance
) -> Fraction:
    """Propagate pointwise optical error through squared loss plus bounded reductions."""
    residuals = tuple(
        Fraction(float(a)) - Fraction(float(b))
        for a, b in itertools.chain(
            zip(y.flat, central.flat, strict=True),
            zip(structured.flat, prediction.flat, strict=True),
        )
    )
    residual_l1 = sum(map(abs, residuals), Fraction(0))
    m = 28 * y.size
    radius = delta.total
    optical = radius * residual_l1 / m + radius**2 / 2
    scale = sum((v * v for v in residuals), Fraction(0)) / (2 * m)
    # gamma_(8M+64) bounds a deliberately conservative number of basic float64 ops.
    operations = 8 * m + 64
    reduction = gamma(operations)
    # Also cover computing the independent floating objective used as center.
    reference_rounding = abs(Fraction(objective(y, structured, central, prediction)) - scale)
    return (
        optical
        + reduction * (scale + residual_l1 / m * radius + radius**2)
        + reference_rounding
        + operations * TINY
    )


def correction_reference_controls() -> dict[str, float | str | int]:
    """Reproduce B's permitted-output witness and distinguish actual violations.

    The enclosed truth below is retained independent public evidence for this
    exact finite sphere, not a coefficient or tolerance fitted to the witness.
    Other inputs use the same analytic observer-error derivation above.
    """
    from types import SimpleNamespace

    with np.errstate(all="raise"):
        settings = np.geterr().copy()
        assert bounded_j0(np.array([1e-300]))[0] == 1
        tiny_phase = bounded_cis(np.array([1e-300]))[0]
        assert tiny_phase.real == 1 and tiny_phase.imag == 1e-300
        assert np.geterr() == settings
    # Independently evaluate the defining series at anchor, half-interval and
    # domain endpoints. These checks do not establish the uniform bound; the
    # derivative/tail/rounding derivation above does. They catch mistakes in
    # the piecewise evaluator and range reduction without product output.
    for t in (0.0, 0.5, 1.0, 1.5, 8.0, 15.5, 16.0, 23.5, 24.0):
        z = Fraction(t) ** 2 / 4
        partial = sum(((-z) ** k / math.factorial(k) ** 2 for k in range(101)), Fraction(0))
        tail = z**101 / math.factorial(101) ** 2 / (1 - z / 102**2)
        value = float(bounded_j0(np.array([t]))[0])
        assert abs(Fraction(value) - partial) + tail <= bessel_polynomials()[1]
    for angle in (-128.0, -math.pi, 0.0, math.pi, 2 * math.pi, 128.0):
        sine, cosine = sin_cos(Interval.rational(Fraction(angle), 60))
        value = bounded_cis(np.array([angle]))[0]
        for observed, target in ((value.real, cosine), (value.imag, sine)):
            assert (
                max(
                    abs(Fraction(float(observed)) - Fraction(endpoint))
                    for endpoint in (target.lo, target.hi)
                )
                <= trig_error()
            )
    center = (0.0625, 0.05, 0.12)
    sites, count, _ = unit_sites(center, SHAPE)
    assert count == 336
    candidate = SimpleNamespace(
        centers_um_zyx=np.array([center]),
        brightness_relative=np.array([1.0]),
        carriers_yx_per_um=np.tile([0.0, 1.2 / 0.488], (3, 1)),
        phases_rad=np.zeros((3, 9)),
        beam_amplitudes=np.ones(3) / math.sqrt(3),
    )
    central, structured, allowance = predictions(candidate, SHAPE, 128)
    observer = float(structured[0, 0, 0, 0, 1])
    target_lo = Fraction("0.02618469567759606758184809954183007745460")
    target_hi = Fraction("0.02618469567759606758184809954183007745461")
    peak_lo = Fraction("0.1250652169002366497858609141442702167992")
    assert (
        max(abs(Fraction(observer) - target_lo), abs(Fraction(observer) - target_hi))
        <= allowance.reference
    )
    permitted = float.fromhex("0x1.ad07d1c679471p-6")
    assert (
        max(abs(Fraction(permitted) - target_lo), abs(Fraction(permitted) - target_hi))
        <= peak_lo / 100000
    )
    old_observer = float.fromhex("0x1.ad0292e5d2bdep-6")
    old_delta = float.fromhex("0x1.4fb829a24a067p-20")
    assert abs(permitted - old_observer) > old_delta  # Original false rejection.
    decision = prediction_decision(permitted, observer, allowance)
    assert decision in ("within", "inconclusive")
    try:
        assert_prediction_close(np.array([permitted]), np.array([observer]), allowance)
    except OracleInconclusive:
        assert decision == "inconclusive"
    else:
        assert decision == "within"
    # No silent passing of an unresolved comparison; exactly represented
    # zero uncertainty has exact decisions, including the T=0 case.
    assert (
        prediction_decision(0.0, 0.0, PredictionAllowance(Fraction(0), Fraction(0), Fraction(0)))
        == "within"
    )
    for wrong in (0.0, observer + upper_float(100 * allowance.total)):
        assert prediction_decision(wrong, observer, allowance) == "violation"
        try:
            assert_prediction_close(np.array([wrong]), np.array([observer]), allowance)
        except AssertionError:
            pass
        else:
            raise AssertionError("materially wrong physical response was not distinguished")
    y, s = np.zeros(SHAPE), np.zeros_like(structured)
    loss = objective(y, s, central, structured)
    loss_radius = loss_allowance(y, s, central, structured, allowance)
    assert_scalar_close(loss, loss, loss_radius)
    try:
        assert_scalar_close(loss + upper_float(100 * loss_radius), loss, loss_radius)
    except AssertionError:
        pass
    else:
        raise AssertionError("materially wrong loss was not distinguished")
    return {
        "occupied_sites": len(sites),
        "permitted_output_decision": decision,
        "reference_radius": upper_float(allowance.reference),
        "product_allowance_lower": upper_float(allowance.product_lo),
        "product_allowance_upper": upper_float(allowance.product_hi),
        "loss_radius": upper_float(loss_radius),
    }


def reference_controls() -> None:
    """Exercise observer normalization, Gaussian exterior and exact physical geometry."""
    impulse = np.zeros((1, 1, 1))
    impulse[0, 0, 0] = 1
    k0 = 1 / math.fsum(math.exp(-i * i / 2) for i in range(-4, 5))
    assert math.isclose(float(finite_gaussian(impulse)[0, 0, 0]), k0**3, rel_tol=16 * EPS)
    # A point exactly at focus/lateral center, one pupil node, and unit pixel area
    # are checked algebraically through the illumination field (25/21 vs 9/21).
    amplitudes = (4, 2, 1)
    plus = abs(4j + 2j - 1j) ** 2 / sum(a * a for a in amplitudes)
    minus = abs(-4j + 2j - 1j) ** 2 / sum(a * a for a in amplitudes)
    assert plus == 25 / 21 and minus == 9 / 21
    for n, spacing in zip(SHAPE, D, strict=True):
        upper = inward_upper(n, spacing)
        exact = n * Fraction(spacing) - Fraction(RADIUS)
        assert Fraction(upper) <= exact < Fraction(float(np.nextafter(upper, np.inf)))
    y = (observations(edge=True)[0] - 5) / 2
    centers, maxima, peaks = initialization(y)
    assert peaks == ((0, 0, 0), (0, 0, 7), (0, 0, 14))
    np.testing.assert_array_equal(maxima, [8, 6, 4])
    assert centers[0, 2] == RADIUS and centers[-1, 2] == inward_upper(SHAPE[2], D[2])
    sites, count, mass = unit_sites(tuple(centers[0]), SHAPE)
    assert count == len(sites) and count > 0
    assert mass == float(Fraction(float(Fraction(1, count))) * count)
    # Independent on-axis pupil value: h_Q(0,0)=pi*R^2 for every finite Q.
    for order in (1, 128, 256, 512):
        _, weights = roots_legendre(order)
        np.testing.assert_allclose(math.fsum(weights / 2), 1, rtol=16 * EPS, atol=0)
    # Four equal-radius pixel samples and Q=1 give sqrt(u)*r = 0.020 um.
    point = np.array([[D[0] / 2, D[1] / 2, D[2] / 2]])
    value = optical_sum(
        point, 1.0, (1, 1, 1), np.zeros((1, 2)), np.zeros((1, 1)), np.array([1.0, 0.0, 0.0]), 1
    )[0, 0, 0, 0, 0]
    r_frequency = 1.4 / 0.525
    analytic = D[1] * D[2] * math.pi * r_frequency**2 * j0(2 * math.pi * r_frequency * 0.020) ** 2
    assert math.isclose(float(value), float(analytic), rel_tol=128 * EPS)
    # Two legal midpoint sites reflect about focus z=0.1875 um. Their pupil
    # responses agree; unequal side beams distinguish the signed axial phase.
    k0 = 1.515 / 0.488
    displacement = 23 / 128
    kappa = 1 / (4 * displacement)
    qx = math.sqrt(2 * k0 * kappa - kappa**2)
    carriers = np.array([[0.0, qx]])
    phase = np.array([[math.pi / 2 - 2 * math.pi * qx * 0.005]])
    for sign, expected in ((-1, 9 / 21), (1, 25 / 21)):
        site = np.array([[0.1875 + sign * displacement, 0.005, 0.005]])
        signal = optical_sum(site, 1.0, (3, 2, 2), carriers, phase, np.array([4.0, 2.0, 1.0]), 128)
        unlit = optical_sum(
            site, 1.0, (3, 2, 2), np.zeros((1, 2)), np.zeros((1, 1)), np.array([1.0, 0.0, 0.0]), 128
        )
        np.testing.assert_allclose(
            signal[0, 0, 1] / unlit[0, 0, 1], expected, rtol=256 * EPS, atol=0
        )
