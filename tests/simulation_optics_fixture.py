"""Tiny exact-input finite equations with refinable outward-rounded enclosures."""

from __future__ import annotations

import math
import operator
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from fractions import Fraction
from functools import cache


def decimal_pi() -> Decimal:
    """Machin's identity; alternating-series error and rounding below 1e-90."""
    with localcontext() as context:
        context.prec = 100

        def arctangent_inverse(denominator: int) -> Decimal:
            x = Decimal(1) / denominator
            power = x
            total = power
            for k in range(1, 200):
                power *= -(x * x)
                term = power / (2 * k + 1)
                total += term
                if abs(term) < Decimal("1e-98"):
                    return total
            raise AssertionError("fixture arctangent series did not converge")

        return 16 * arctangent_inverse(5) - 4 * arctangent_inverse(239)


def exact(value: int | float) -> Fraction:
    """Interpret the normalized float64 input as an exact rational."""
    return Fraction.from_float(float(value))


class OracleInconclusive(RuntimeError):
    """An oracle limitation, never evidence of a product target violation."""


@dataclass(frozen=True)
class Interval:
    """Closed Decimal bounds, with arithmetic operations rounded outward."""

    lo: Decimal
    hi: Decimal
    digits: int

    @classmethod
    def rational(cls, value: Fraction | int, digits: int) -> Interval:
        value = Fraction(value)
        with localcontext() as context:
            context.prec = digits
            context.rounding = ROUND_FLOOR
            lo = Decimal(value.numerator) / Decimal(value.denominator)
            context.rounding = ROUND_CEILING
            hi = Decimal(value.numerator) / Decimal(value.denominator)
        return cls(lo, hi, digits)

    def _binary(
        self,
        other: Interval | Fraction | int,
        operation: Callable[[Decimal, Decimal], Decimal],
    ) -> Interval:
        right = other if isinstance(other, Interval) else self.rational(other, self.digits)
        assert right.digits == self.digits
        with localcontext() as context:
            context.prec = self.digits
            context.rounding = ROUND_FLOOR
            lo = min(operation(a, b) for a in (self.lo, self.hi) for b in (right.lo, right.hi))
            context.rounding = ROUND_CEILING
            hi = max(operation(a, b) for a in (self.lo, self.hi) for b in (right.lo, right.hi))
        return Interval(lo, hi, self.digits)

    def __add__(self, other: Interval | Fraction | int) -> Interval:
        """Enclose addition."""
        return self._binary(other, operator.add)

    __radd__ = __add__

    def __neg__(self) -> Interval:
        """Negate endpoints exactly without the ambient Decimal context."""
        return Interval(self.hi.copy_negate(), self.lo.copy_negate(), self.digits)

    def __sub__(self, other: Interval | Fraction | int) -> Interval:
        """Enclose subtraction."""
        return self._binary(other, operator.sub)

    def __rsub__(self, other: Fraction | int) -> Interval:
        """Enclose subtraction from an exact rational."""
        return -self + other

    def __mul__(self, other: Interval | Fraction | int) -> Interval:
        """Enclose multiplication."""
        return self._binary(other, operator.mul)

    __rmul__ = __mul__

    def __truediv__(self, other: Interval | Fraction | int) -> Interval:
        """Enclose division when the denominator excludes zero."""
        right = other if isinstance(other, Interval) else self.rational(other, self.digits)
        if right.lo <= 0 <= right.hi:
            raise OracleInconclusive("oracle divisor interval contains zero")
        return self._binary(right, operator.truediv)

    def absolute(self) -> Interval:
        if self.lo >= 0:
            return self
        if self.hi <= 0:
            return -self
        return Interval(Decimal(0), max(self.lo.copy_negate(), self.hi), self.digits)

    def squared(self) -> Interval:
        absolute = self.absolute()
        with localcontext() as context:
            context.prec = self.digits
            context.rounding = ROUND_FLOOR
            lo = absolute.lo * absolute.lo
            context.rounding = ROUND_CEILING
            hi = absolute.hi * absolute.hi
        return Interval(lo, hi, self.digits)

    def sqrt(self) -> Interval:
        if self.lo < 0:
            raise OracleInconclusive("oracle square-root interval reaches negative values")
        if self.hi == 0:
            return self
        with localcontext() as context:
            context.prec = self.digits
            # Decimal.sqrt is correctly rounded; adjacent values enclose endpoints.
            lo = max(Decimal(0), self.lo.sqrt().next_minus())
            hi = self.hi.sqrt().next_plus()
        assert Fraction(lo) ** 2 <= Fraction(self.lo)
        assert Fraction(hi) ** 2 >= Fraction(self.hi)
        return Interval(lo, hi, self.digits)

    def padded(self, radius: Decimal) -> Interval:
        return self + Interval(radius.copy_negate(), radius, self.digits)


@cache
def pi_interval(digits: int) -> Interval:
    """Exact rational alternating arctangent bounds in Machin's identity."""
    threshold = Fraction(1, 10 ** (digits + 8))

    def arctangent_inverse(denominator: int) -> Interval:
        total = Fraction(0)
        k = 0
        while True:
            total += Fraction((-1) ** k, (2 * k + 1) * denominator ** (2 * k + 1))
            k += 1
            following = Fraction((-1) ** k, (2 * k + 1) * denominator ** (2 * k + 1))
            if abs(following) < threshold:
                a = Interval.rational(min(total, total + following), digits)
                b = Interval.rational(max(total, total + following), digits)
                return Interval(a.lo, b.hi, digits)

    return 16 * arctangent_inverse(5) - 4 * arctangent_inverse(239)


def _tail(term: Interval, ratio: Interval) -> Decimal | None:
    """Geometric majorant for subsequent terms with decreasing absolute ratios."""
    if ratio.lo < 0 or ratio.hi >= 1:
        return None
    upper_ratio = Interval(ratio.hi, ratio.hi, term.digits)
    return (term.absolute() * upper_ratio / (1 - upper_ratio)).hi


def sin_cos(angle: Interval) -> tuple[Interval, Interval]:
    """Taylor sums after a mathematically equivalent integer-turn reduction."""
    pi = pi_interval(angle.digits)
    with localcontext() as context:
        context.prec = angle.digits
        turns = int(((angle.lo + angle.hi) / (2 * (pi.lo + pi.hi))).to_integral_value())
    reduced = angle - 2 * turns * pi
    square = reduced.squared()
    threshold = Decimal(1).scaleb(-(angle.digits - 8))
    answers: list[Interval] = []
    for odd in (True, False):
        term = reduced if odd else Interval.rational(1, angle.digits)
        total = term
        for k in range(1, 10 * angle.digits + 100):
            denominator = (2 * k) * (2 * k + 1) if odd else (2 * k - 1) * (2 * k)
            term = -term * square / denominator
            total += term
            next_denominator = (2 * k + 2) * (2 * k + 3) if odd else (2 * k + 1) * (2 * k + 2)
            tail = _tail(term, square / next_denominator)
            if tail is not None and tail <= threshold:
                answers.append(total.padded(tail))
                break
        else:
            raise OracleInconclusive("oracle trigonometric series did not enclose its tail")
    return answers[0], answers[1]


def bessel_from_square(quarter_argument_square: Interval) -> Interval:
    """J0(t)=sum (-t²/4)^k/(k!)², with an enclosed geometric tail."""
    z = quarter_argument_square
    if z.lo < 0 or z.hi > 64:
        raise OracleInconclusive("oracle J0 domain is limited to |argument| <= 16")
    term = Interval.rational(1, z.digits)
    total = term
    threshold = Decimal(1).scaleb(-(z.digits - 8))
    for k in range(1, 10 * z.digits + 100):
        term = -term * z / (k * k)
        total += term
        tail = _tail(term, z / ((k + 1) ** 2))
        if tail is not None and tail <= threshold:
            return total.padded(tail)
    raise OracleInconclusive("oracle Bessel series did not enclose its tail")


def radial_intervals(order: int, digits: int) -> tuple[tuple[Interval, Fraction], ...]:
    half = Interval.rational(Fraction(1, 2), digits)
    if order == 1:
        return ((half, Fraction(1)),)
    if order == 2:
        offset = Interval.rational(Fraction(1, 12), digits).sqrt()
        return ((half - offset, Fraction(1, 2)), (half + offset, Fraction(1, 2)))
    if order == 3:
        offset = Interval.rational(Fraction(3, 20), digits).sqrt()
        return (
            (half - offset, Fraction(5, 18)),
            (half, Fraction(4, 9)),
            (half + offset, Fraction(5, 18)),
        )
    raise OracleInconclusive("only closed Q=1,2,3 finite-reference rules are provided")


@dataclass(frozen=True)
class Source:
    """Explicit exact source midpoint in micrometres and integrated electrons."""

    z: Fraction
    y: Fraction
    x: Fraction
    electrons: Fraction


Bounds = tuple[tuple[Interval, ...], Interval]


@dataclass(frozen=True)
class Reference:
    """Refinable enclosures of flattened mu and max(unilluminated U)."""

    shape: tuple[int, ...]
    evaluate: Callable[[int], Bounds]

    def zero_target(self) -> Reference:
        def evaluate(digits: int) -> Bounds:
            values, peak = self.evaluate(digits)
            return tuple(Interval.rational(0, digits) for _ in values), peak

        return Reference(self.shape, evaluate)


def compare_reference(
    observations: tuple[Fraction, ...], reference: Reference, *, multiplier: int = 1
) -> int:
    """Deciding digits; raise AssertionError only for a proved target violation.

    An unresolved 640-digit enclosure raises OracleInconclusive. This is an
    oracle computation limit, not a product or human execution limit.
    """
    assert len(observations) == math.prod(reference.shape)
    for digits in (40, 80, 160, 320, 640):
        targets, peak = reference.evaluate(digits)
        assert len(targets) == len(observations)
        allowance = peak * Fraction(multiplier, 100000)
        ambiguous = False
        for index, (observed, target) in enumerate(zip(observations, targets, strict=True)):
            error = (Interval.rational(observed, digits) - target).absolute()
            if error.lo > allowance.hi:
                raise AssertionError(
                    f"certified target violation at flat entry {index}: "
                    f"error >= {error.lo}, allowance <= {allowance.hi}"
                )
            if error.hi > allowance.lo:
                ambiguous = True
        if not ambiguous:
            return digits
    raise OracleInconclusive("mu/T comparison unresolved after 640 digits; no product verdict")


def direct_factors(
    phases: tuple[float, ...], beams: tuple[float, float, float]
) -> Callable[[int], tuple[Interval, ...]]:
    """Independent q=d=0 real/imaginary field factors, exact binary phases."""
    a0, plus, minus = (exact(a) for a in beams)
    norm = a0 * a0 + plus * plus + minus * minus

    def evaluate(digits: int) -> tuple[Interval, ...]:
        if sum(a != 0 for a in (a0, plus, minus)) == 1:
            return tuple(Interval.rational(1, digits) for _ in phases)
        values = []
        for phase in phases:
            sine, cosine = sin_cos(Interval.rational(exact(phase), digits))
            real = a0 + (plus + minus) * cosine
            imaginary = (plus - minus) * sine
            values.append((real.squared() + imaginary.squared()) / norm)
        return tuple(values)

    return evaluate


DEFAULT_APERTURE = exact(0.8)
DEFAULT_EMISSION = exact(0.6)


def on_axis_reference(
    shape: tuple[int, ...],
    electrons: Fraction,
    area: Fraction,
    *,
    aperture: Fraction = DEFAULT_APERTURE,
    emission: Fraction = DEFAULT_EMISSION,
    factors: Callable[[int], tuple[Interval, ...]] | None = None,
) -> Reference:
    """Analytic h(0,0)=pi*R²; optional independent illumination factors."""

    @cache
    def evaluate(digits: int) -> Bounds:
        peak = pi_interval(digits) * (electrons * area * (aperture / emission) ** 2)
        multipliers = (
            factors(digits)
            if factors is not None
            else tuple(Interval.rational(1, digits) for _ in range(math.prod(shape)))
        )
        assert len(multipliers) == math.prod(shape)
        return tuple(peak * factor for factor in multipliers), peak

    return Reference(shape, evaluate)


def huge_geometry_reference() -> Reference:
    """Three unit on-axis sources, Dz=float(1e308), Q=2, central beam only.

    Pairwise pupil interference gives h(d)=pi*R²*(1+cos(omega*d/Dz))/2.
    Working precision includes 320 digits to resolve the ~1e308-radian phase;
    final bounds are projected outward to the requested comparison precision.
    """

    @cache
    def evaluate(digits: int) -> Bounds:
        working = digits + 320
        pi = pi_interval(working)
        half = Interval.rational(Fraction(1, 2), working)
        offset = Interval.rational(Fraction(1, 12), working).sqrt()
        beta_squared = (exact(0.8) / exact(1.25)) ** 2
        difference = (1 - beta_squared * (half - offset)).sqrt() - (
            1 - beta_squared * (half + offset)
        ).sqrt()
        omega = 2 * pi * (exact(1.25) / exact(0.6) * exact(1e308)) * difference
        _, cosine = sin_cos(omega)
        _, cosine_twice = sin_cos(2 * omega)
        scale = pi * ((exact(0.8) / exact(0.6)) ** 2 * exact(0.3) * exact(0.4))
        edge = scale * (2 + (cosine + cosine_twice) / 2)
        middle = scale * (2 + cosine)

        def project(value: Interval) -> Interval:
            lower = Interval.rational(Fraction(value.lo), digits).lo
            upper = Interval.rational(Fraction(value.hi), digits).hi
            return Interval(lower, upper, digits)

        values = tuple(project(value) for value in (edge, middle, edge))
        peak = Interval(max(v.lo for v in values), max(v.hi for v in values), digits)
        return values, peak

    return Reference((1, 1, 3, 1, 1), evaluate)


def finite_images(
    sources: tuple[Source, ...],
    focuses: tuple[Fraction, ...],
    pixel_sites: tuple[tuple[tuple[Fraction, Fraction], ...], ...],
    lateral_shape: tuple[int, int],
    area: Fraction,
    carriers: tuple[tuple[float, float], ...],
    phases: tuple[tuple[float, ...], ...],
    *,
    beams: tuple[float, float, float] = (4.0, 2.0, 1.0),
    excitation: float = 0.5,
    emission: float = 0.6,
    index: float = 1.25,
    aperture: float = 0.8,
    order: int = 2,
) -> Reference:
    """Explicit finite quadrature; no array-to-coordinate production logic."""
    assert len(pixel_sites) == math.prod(lateral_shape)
    assert len(phases) == len(carriers) and len({len(row) for row in phases}) == 1
    a0, plus, minus = (exact(a) for a in beams)
    norm = a0 * a0 + plus * plus + minus * minus
    frequency = exact(aperture) / exact(emission)
    nu = exact(index) / exact(emission)
    beta = exact(aperture) / exact(index)
    k0 = exact(index) / exact(excitation)
    shape = (len(carriers), len(phases[0]), len(focuses), *lateral_shape)

    @cache
    def evaluate(digits: int) -> Bounds:
        pi = pi_interval(digits)
        zero = Interval.rational(0, digits)
        rule = radial_intervals(order, digits)

        @cache
        def density(radius_squared: Fraction, d: Fraction) -> Interval:
            real, imaginary = zero, zero
            for node, weight in rule:
                j0 = bessel_from_square(pi.squared() * (frequency**2 * radius_squared) * node)
                angle = 2 * pi * (nu * d) * ((1 - beta**2 * node).sqrt() - 1)
                sine, cosine = sin_cos(angle)
                real += weight * j0 * cosine
                imaginary += weight * j0 * sine
            return pi * frequency**2 * (real.squared() + imaginary.squared())

        @cache
        def illumination(source: Source, focus: Fraction, o: int, p: int) -> Interval:
            if sum(a != 0 for a in (a0, plus, minus)) == 1:
                return Interval.rational(1, digits)
            qy, qx = (exact(q) for q in carriers[o])
            kappa = k0 - Interval.rational(k0**2 - qy**2 - qx**2, digits).sqrt()
            cycles = (qy * source.y + qx * source.x) % 1
            theta = 2 * pi * cycles + exact(phases[o][p])
            side_sine, side_cosine = sin_cos(theta)
            axial_sine, axial_cosine = sin_cos(2 * pi * kappa * (source.z - focus))
            real = a0 * axial_cosine + (plus + minus) * side_cosine
            imaginary = a0 * axial_sine + (plus - minus) * side_sine
            return (real.squared() + imaginary.squared()) / norm

        contributions: dict[tuple[int, int], tuple[Interval, ...]] = {}
        unilluminated: list[Interval] = []
        for k, focus in enumerate(focuses):
            for pixel, sites in enumerate(pixel_sites):
                values = tuple(
                    sum(
                        (
                            density((y - source.y) ** 2 + (x - source.x) ** 2, source.z - focus)
                            for y, x in sites
                        ),
                        start=zero,
                    )
                    * (source.electrons * area / len(sites))
                    for source in sources
                )
                contributions[k, pixel] = values
                unilluminated.append(sum(values, start=zero))
        expected = tuple(
            sum(
                (
                    contribution * illumination(source, focus, o, p)
                    for source, contribution in zip(sources, contributions[k, pixel], strict=True)
                ),
                start=zero,
            )
            for o in range(len(carriers))
            for p in range(len(phases[0]))
            for k, focus in enumerate(focuses)
            for pixel in range(len(pixel_sites))
        )
        peak = Interval(max(u.lo for u in unilluminated), max(u.hi for u in unilluminated), digits)
        return expected, peak

    return Reference(shape, evaluate)
