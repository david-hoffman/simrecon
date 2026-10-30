"""Independent finite-model data and observers for the RA05 public adapter.

No production numerical helper is used here. Arrays stay readable for later plots.
Represented least squares uses Decimal(70). Fourier sums have an explicit
observer-rounding allowance, including platforms whose longdouble is binary64.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from itertools import product
from typing import cast

import numpy as np

PI = np.longdouble("3.1415926535897932384626433832795028841971693993751")
EPS = 2.0**-52


@dataclass(frozen=True)
class BeadCase:
    """Declared model inputs and independently generated physical observations."""

    shape: tuple
    spacing: tuple
    phases: np.ndarray
    profile: np.ndarray
    h: np.ndarray
    kernels: np.ndarray
    anchor: tuple
    carrier: tuple
    brightness: float
    alpha: float
    exposures: np.ndarray
    physical_components: np.ndarray


def phase_basis(phases):
    """Exact contract operation order, including phasor-squared second order."""
    c, s = np.cos(phases), np.sin(phases)
    return np.column_stack((np.ones(len(phases)), c, s, c * c - s * s, (2 * c) * s))


def exact_mass(array):
    return sum((Fraction(float(x)) for x in np.asarray(array).flat), Fraction())


def extended(value):
    if isinstance(value, Fraction):
        return np.longdouble(str(value.numerator)) / np.longdouble(str(value.denominator))
    return np.longdouble(value)


def normalized_profile(profile):
    mass = exact_mass(profile)
    return np.array([extended(Fraction(float(x)) / mass) for x in profile.flat]).reshape(
        profile.shape
    )


def modes(shape):
    return tuple(tuple(range(-(n // 2), (n + 1) // 2)) for n in shape)


@cache
def decimal_pi():
    """Machin's formula with enough digits to reduce maximum binary64 radians."""
    with localcontext() as context:
        context.prec = 400

        def atan_inverse(n):
            x = Decimal(1) / n
            term, total, index = x, x, 1
            while True:
                term *= -x * x
                contribution = term / (2 * index + 1)
                updated = total + contribution
                if updated == total:
                    return total
                total = updated
                index += 1

        return 16 * atan_inverse(5) - 4 * atan_inverse(239)


def angle_phasor(angle):
    """Independent Decimal argument reduction and Taylor sine/cosine."""
    with localcontext() as context:
        context.prec = 400
        period = 2 * decimal_pi()
        reduced = Decimal(float(angle)) % period
        if reduced > decimal_pi():
            reduced -= period
        if reduced < -decimal_pi():
            reduced += period
        return decimal_phasor(reduced)


def decimal_phasor(angle):
    with localcontext() as context:
        context.prec = 80
        angle = +angle
        square = angle * angle
        sine_term, cosine_term = angle, Decimal(1)
        sine, cosine = sine_term, cosine_term
        for index in range(1, 160):
            sine_term *= -square / ((2 * index) * (2 * index + 1))
            cosine_term *= -square / ((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
        return np.clongdouble(complex(float(cosine), float(sine)))


@cache
def phasor(cycles):
    with localcontext() as context:
        context.prec = 80
        reduced = cycles % 1
        angle = 2 * decimal_pi() * Decimal(reduced.numerator) / Decimal(reduced.denominator)
        return decimal_phasor(angle)


def direct_dft(array):
    """Full centered forward finite sum, no FFT dependency or product outputs."""
    shape = array.shape
    result = np.empty(shape, dtype=np.clongdouble)
    sites = list(np.ndindex(shape))
    for index, k in zip(np.ndindex(shape), product(*modes(shape)), strict=True):
        result[index] = sum(
            (
                np.clongdouble(array[j])
                * phasor(
                    -sum(
                        (Fraction(ka * ja, n) for ka, ja, n in zip(k, j, shape, strict=False)),
                        Fraction(),
                    )
                )
                for j in sites
            ),
            np.clongdouble(0),
        )
    return result


def direct_inverse(spectrum):
    shape = spectrum.shape
    rows = list(zip(np.ndindex(shape), product(*modes(shape)), strict=True))
    result = np.empty(shape, dtype=np.clongdouble)
    for j in np.ndindex(shape):
        result[j] = sum(
            (
                spectrum[index]
                * phasor(
                    sum(
                        (Fraction(ka * ja, n) for ka, ja, n in zip(k, j, shape, strict=False)),
                        Fraction(),
                    )
                )
                for index, k in rows
            ),
            np.clongdouble(0),
        ) / np.prod(shape)
    return result


def make_case(
    *,
    shape=(3, 4, 5),
    kind="finite",
    anchor=None,
    carrier=(1, -1),
    brightness=32.0,
    alpha=0.17,
):
    """Generate exposures from squared fields and real-space circular sums."""
    anchor = anchor or tuple(n - 1 for n in shape)
    spacing = (0.5, 0.25, 0.125)
    phases = np.array([0.02, 0.77, 1.81, 2.63, 3.59, 4.72, 5.62])
    h = np.zeros(shape)
    for j, weight in [((0, 0, 0), 16), ((1, 0, 1), 3), ((0, 1, 0), 2), ((1, 1, 2), 1)]:
        h[tuple(a % n for a, n in zip(j, shape, strict=False))] += weight
    h /= h.sum()
    profile = np.zeros(shape)
    if kind == "point":
        profile[0, 0, 0] = 1
    elif kind == "translated":
        profile[0, -1, 1 % shape[2]] = 1
    else:
        profile[0, -1, 1 % shape[2]] += 8
        profile[-1, 0, -1] += 1
        profile[0, 0, 0] += 1
    p = normalized_profile(profile)
    a0, ap, am = 1 + 0.2j, 0.7 - 0.1j, 0.4 + 0.3j
    power = abs(a0) ** 2 + abs(ap) ** 2 + abs(am) ** 2
    kernels = np.empty((3, *shape), dtype=np.clongdouble)
    exposures = np.zeros((len(phases), *shape), dtype=np.longdouble)
    components = np.zeros((3, *shape), dtype=np.clongdouble)
    for u in np.ndindex(shape):
        axial = phasor(Fraction(u[0], shape[0]))
        g1 = (ap * a0.conjugate() / axial + a0 * am.conjugate() * axial) / power
        g2 = ap * am.conjugate() / power
        kernels[(slice(None), *u)] = h[u] * np.array([1, g1, g2])
    for n in np.ndindex(shape):
        for j in np.ndindex(shape):
            weight = (
                brightness
                * p[tuple((a - b) % size for a, b, size in zip(j, anchor, shape, strict=False))]
            )
            if weight == 0:
                continue
            u = tuple((a - b) % size for a, b, size in zip(n, j, shape, strict=False))
            lateral = sum(
                (
                    Fraction(k * a, size)
                    for k, a, size in zip(carrier, j[1:], shape[1:], strict=False)
                ),
                Fraction(),
            )
            for m in range(3):
                components[(m, *n)] += (
                    weight
                    * kernels[(m, *u)]
                    * phasor(m * lateral)
                    * np.exp(np.clongdouble(-1j * m * alpha))
                )
            for phase_index, phi in enumerate(phases):
                theta = phasor(lateral) * np.exp(np.clongdouble(1j) * extended(phi - alpha))
                field = a0 * phasor(Fraction(u[0], shape[0])) + ap * theta + am / theta
                exposures[(phase_index, *n)] += weight * h[u] * abs(field) ** 2 / power
    return BeadCase(
        shape,
        spacing,
        phases,
        profile,
        h,
        kernels,
        anchor,
        carrier,
        brightness,
        alpha,
        np.asarray(exposures, dtype=np.float64),
        components,
    )


def fit_components(images, phases):
    """Independent high-precision fit to exact represented H and observations."""
    with localcontext() as context:
        context.prec = 70
        h = [[Decimal(float(x)) for x in row] for row in phase_basis(phases)]
        gram = cast(
            list[list[Decimal]],
            [[sum(row[i] * row[j] for row in h) for j in range(5)] for i in range(5)],
        )
        # Invert the small Gram matrix in observer precision, never as product solver.
        aug = [row[:] + [Decimal(int(i == j)) for j in range(5)] for i, row in enumerate(gram)]
        for i in range(5):
            pivot = max(range(i, 5), key=lambda j: abs(aug[j][i]))
            aug[i], aug[pivot] = aug[pivot], aug[i]
            scale = aug[i][i]
            aug[i] = [x / scale for x in aug[i]]
            for j in range(5):
                if j != i:
                    scale = aug[j][i]
                    aug[j] = [a - scale * b for a, b in zip(aug[j], aug[i], strict=False)]
        inverse = [row[5:] for row in aug]
        out = np.empty((3, *images.shape[1:]), dtype=np.clongdouble)
        for site in np.ndindex(images.shape[1:]):
            b = [Decimal(float(images[(p, *site)])) for p in range(len(phases))]
            rhs = [sum(row[i] * value for row, value in zip(h, b, strict=False)) for i in range(5)]
            z = [sum(a * v for a, v in zip(row, rhs, strict=False)) for row in inverse]
            out[(0, *site)] = np.longdouble(str(z[0]))
            for m in (1, 2):
                out[(m, *site)] = np.longdouble(str(z[2 * m - 1] / 2)) - np.clongdouble(
                    1j
                ) * np.longdouble(str(z[2 * m] / 2))
        return out


def expected_response(components, profile, carrier, origin):
    shape = profile.shape
    # These components are independent Decimal-fit expectations, not product fields.
    mass = np.sum(components[0].real, dtype=np.longdouble)
    p = direct_dft(normalized_profile(profile))
    result = np.empty_like(components)
    q0 = None
    for m in range(3):
        a = direct_dft(components[m]) / mass
        for index, k in zip(np.ndindex(shape), product(*modes(shape)), strict=True):
            shifted = tuple(
                (ka - m * ca + size // 2) % size
                for ka, ca, size in zip(k, (0, *carrier), shape, strict=False)
            )
            result[(m, *index)] = a[index] / p[shifted]
        if m == 0:
            q0 = result[0].copy()
        for index, k in zip(np.ndindex(shape), product(*modes(shape)), strict=True):
            result[(m, *index)] *= phasor(
                sum(
                    (Fraction(ka * b, size) for ka, b, size in zip(k, origin, shape, strict=False)),
                    Fraction(),
                )
            )
    return result, p, direct_inverse(q0).real


def response_budget(images, components, profile, minimum):
    """Conservative uniform composite bound from public stage budgets."""
    size = profile.size
    separation = extended(8192 * len(images) * EPS) * np.max(np.abs(images))
    mass = np.sum(components[0].real, dtype=np.longdouble)
    eta = extended(128 * size * EPS)
    p = direct_dft(normalized_profile(profile))
    mu = np.min(np.abs(p)) - eta
    assert mu >= minimum and size * separation < mass
    bounds = []
    norms = []
    for m in range(3):
        norm = np.sum(abs(components[m].real) + abs(components[m].imag)) / mass
        norms.append(norm)
        em = separation * (1 if m == 0 else np.sqrt(extended(2)))
        dsep = (size * em + norm * size * separation) / (mass - size * separation)
        # L1 perturbations of a complex order add both coordinate errors;
        # spectral complex error above instead uses their Euclidean norm.
        norm_upper = (mass * norm + size * separation * (1 if m == 0 else 2)) / (
            mass - size * separation
        )
        da = 512 * size * EPS * norm_upper + dsep
        dq = da / mu + norm * eta / (minimum * mu) + 128 * EPS * (norm + da) / mu
        bounds.append(dq + 128 * EPS * (norm / mu + dq))
    # Finite sums/rounded phasors, profile division and normalized mass in the
    # observer. This remains conservative when longdouble has no extra bits.
    observer = 64 * size * EPS * max(1, *norms) * (1 / minimum + 1 / minimum**2)
    return np.asarray(bounds) + observer


def interpolate(values, spacing, points):
    """Exact represented-coordinate bracketing, independent tensor finite sum."""
    axes = [
        tuple(Fraction(k) / (n * Fraction(float(d))) for k in ks)
        for n, d, ks in zip(values.shape, spacing, modes(values.shape), strict=False)
    ]
    result = []
    for point in points:
        stencils = []
        for x, nodes in zip(point, axes, strict=False):
            x = Fraction(float(x))
            if not nodes[0] <= x <= nodes[-1]:
                raise ValueError("independent observer: outside exact hull")
            if x in nodes:
                stencils.append(((nodes.index(x), Fraction(1)),))
            else:
                lo = next(i for i in range(len(nodes) - 1) if nodes[i] < x < nodes[i + 1])
                t = (x - nodes[lo]) / (nodes[lo + 1] - nodes[lo])
                stencils.append(((lo, 1 - t), (lo + 1, t)))
        result.append(
            sum(
                (
                    values[tuple(v[0] for v in vertices)]
                    * extended(vertices[0][1] * vertices[1][1] * vertices[2][1])
                    for vertices in product(*stencils)
                ),
                np.clongdouble(0),
            )
        )
    return np.asarray(result, dtype=np.clongdouble)


def expected_samples(values, spacing, origin, carrier, offset, delta, order, points):
    positive = interpolate(values[abs(order)], spacing, points if order >= 0 else -points)
    if order:
        rho = sum(
            (
                Fraction(k * (b + o), n)
                for k, b, o, n in zip(carrier, origin[1:], offset, values.shape[2:], strict=False)
            ),
            Fraction(),
        )
        # Evaluate one finite angle then take the small integer power. Never
        # multiply a maximum binary64 phase by two in binary64 arithmetic.
        positive *= phasor(-abs(order) * rho) * angle_phasor(-float(delta)) ** abs(order)
    return np.conj(positive) if order < 0 else positive
