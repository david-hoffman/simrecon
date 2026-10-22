"""Independent finite-grid generators and decimal observers for finite beads.

No product FFT, solver, calibration output or existing fixture supplies truth.
Decimal calculations use 110 significant digits; exact binary64 decisions use
Fraction. The trigonometric series stops below 1e-115 on bounded angles.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from itertools import product
from math import nextafter, prod
from typing import Any

import numpy as np
from numpy.typing import NDArray

PRECISION = 110
EPS = Decimal.from_float(2**-52)
Q0 = Decimal.from_float(float.fromhex("0x0.0000000000001p-1022"))
FMAX = Decimal.from_float(float.fromhex("0x1.fffffffffffffp+1023"))
FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]
Index = tuple[int, int, int]


def d(value: Any) -> Decimal:
    """Interpret a finite stored scalar, without a decimal string conversion."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, np.integer)):
        return Decimal(int(value))
    return Decimal.from_float(float(value))


def rational(value: Fraction) -> Decimal:
    """Convert an exact rational in the active observer precision."""
    return Decimal(value.numerator) / Decimal(value.denominator)


@dataclass(frozen=True)
class Z:
    """Small decimal complex type with explicit component-safe arithmetic."""

    re: Decimal = Decimal(0)
    im: Decimal = Decimal(0)

    def __add__(self, other: Z) -> Z:
        """Add components at the active decimal precision."""
        return Z(self.re + other.re, self.im + other.im)

    def __sub__(self, other: Z) -> Z:
        """Subtract components at the active decimal precision."""
        return Z(self.re - other.re, self.im - other.im)

    def __mul__(self, other: Z) -> Z:
        """Multiply without binary64 range restrictions."""
        return Z(self.re * other.re - self.im * other.im, self.re * other.im + self.im * other.re)

    def __truediv__(self, other: Z) -> Z:
        """Divide using the high-precision observer's unbounded exponent."""
        square = other.re * other.re + other.im * other.im
        return Z(
            (self.re * other.re + self.im * other.im) / square,
            (self.im * other.re - self.re * other.im) / square,
        )

    def scale(self, value: Decimal) -> Z:
        return Z(self.re * value, self.im * value)

    def conjugate(self) -> Z:
        return Z(self.re, -self.im)

    def magnitude(self) -> Decimal:
        return (self.re * self.re + self.im * self.im).sqrt()

    def l1(self) -> Decimal:
        return abs(self.re) + abs(self.im)

    def native(self) -> complex:
        return complex(float(self.re), float(self.im))


def z(value: Any) -> Z:
    """Read represented real and imaginary components independently."""
    return Z(d(np.real(value)), d(np.imag(value)))


@cache
def pi() -> Decimal:
    """Evaluate Machin's pi=16 atan(1/5)-4 atan(1/239) independently."""
    with localcontext() as context:
        context.prec = PRECISION + 15

        def atan_inverse(n: int) -> Decimal:
            x = Decimal(1) / n
            power = x
            result = x
            index = 1
            while abs(power) > Decimal("1e-125"):
                power *= -x * x
                result += power / (2 * index + 1)
                index += 1
            return result

        return 16 * atan_inverse(5) - 4 * atan_inverse(239)


@cache
def angle_phasor(angle: Decimal) -> Z:
    """Evaluate exp(i angle) with a decimal Taylor remainder below 1e-115."""
    angle %= 2 * pi()
    if angle > pi():
        angle -= 2 * pi()
    cosine = cos_term = Decimal(1)
    sine = sin_term = angle
    index = 1
    while max(abs(cos_term), abs(sin_term)) > Decimal("1e-115"):
        cos_term *= -angle * angle / ((2 * index - 1) * (2 * index))
        sin_term *= -angle * angle / ((2 * index) * (2 * index + 1))
        cosine += cos_term
        sine += sin_term
        index += 1
    return Z(cosine, sine)


@cache
def root(cycles: Fraction) -> Z:
    """Evaluate a rational-cycle root; exact quarter turns need no pi."""
    reduced = cycles % 1
    quarters = reduced * 4
    if quarters.denominator == 1:
        return (Z(d(1)), Z(d(0), d(1)), Z(d(-1)), Z(d(0), d(-1)))[int(quarters)]
    with localcontext() as context:
        context.prec = PRECISION
        return angle_phasor(2 * pi() * rational(reduced))


def indices(shape: Index) -> list[Index]:
    """Enumerate native spatial coordinates without frequency conventions."""
    return [(a, b, c) for a, b, c in product(*(range(n) for n in shape))]


def modes(shape: Index) -> list[Index]:
    """Enumerate full fftshift integer modes in z/y/x order."""
    return [(a, b, c) for a, b, c in product(*(range(-(n // 2), (n + 1) // 2) for n in shape))]


def cycles(k: Index, j: Index, shape: Index) -> Fraction:
    """Form the exact rational dot product, including singleton axes."""
    return sum((Fraction(ka * ja, n) for ka, ja, n in zip(k, j, shape, strict=True)), Fraction())


def transform(values: list[Z], shape: Index) -> list[Z]:
    """Compute the negative-exponent finite sum directly in 110 digits."""
    return [
        sum(
            (
                value * root(-cycles(k, j, shape))
                for j, value in zip(indices(shape), values, strict=True)
            ),
            Z(),
        )
        for k in modes(shape)
    ]


def inverse(values: list[Z], shape: Index) -> list[Z]:
    """Compute the normalized positive-exponent finite sum directly."""
    return [
        sum(
            (
                value * root(cycles(k, j, shape))
                for k, value in zip(modes(shape), values, strict=True)
            ),
            Z(),
        ).scale(Decimal(1) / prod(shape))
        for j in indices(shape)
    ]


def represented_basis(phases: FloatArray) -> FloatArray:
    """Implement only the public, explicitly rounded phase-matrix definition."""
    converted = np.asarray(phases, dtype=np.float64)
    c = np.cos(converted)
    s = np.sin(converted)
    return np.column_stack((np.ones_like(c), c, s, c * c - s * s, (2 * c) * s))


def solve(matrix: list[list[Decimal]], rhs: list[list[Decimal]]) -> list[list[Decimal]]:
    """Solve a small independent decimal system by pivoted elimination."""
    rows = [a.copy() + b.copy() for a, b in zip(matrix, rhs, strict=True)]
    n = len(rows)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        assert divisor != 0
        rows[col] = [x / divisor for x in rows[col]]
        for row in range(n):
            if row != col:
                factor = rows[row][col]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[col], strict=True)]
    return [row[n:] for row in rows]


def fit(images: FloatArray, phases: FloatArray) -> list[list[Z]]:
    """Find exact represented-model least squares independently of product SVD."""
    h = [[d(value) for value in row] for row in represented_basis(phases)]
    converted = np.asarray(images, dtype=np.float64)
    observations = [[d(value) for value in row] for row in converted.reshape(len(phases), -1)]
    gram = [[sum((row[a] * row[b] for row in h), Decimal()) for b in range(5)] for a in range(5)]
    rhs = [
        [
            sum((row[a] * obs[v] for row, obs in zip(h, observations, strict=True)), Decimal())
            for v in range(len(observations[0]))
        ]
        for a in range(5)
    ]
    x = solve(gram, rhs)
    return [
        [Z(value) for value in x[0]],
        [Z(a / 2, -b / 2) for a, b in zip(x[1], x[2], strict=True)],
        [Z(a / 2, -b / 2) for a, b in zip(x[3], x[4], strict=True)],
    ]


def exact_mass(values: Any) -> Fraction:
    """Sum represented real samples exactly, even beyond binary64 range."""
    return sum((Fraction.from_float(float(value)) for value in np.asarray(values).flat), Fraction())


def normalized_profile(profile: FloatArray) -> tuple[FloatArray, list[Z]]:
    """Return correctly rounded applied weights and the unrounded exact profile."""
    mass = exact_mass(profile)
    assert mass > 0
    exact = [Fraction.from_float(float(value)) / mass for value in profile.flat]
    applied = np.array([rounded_weight(value) for value in exact], dtype=np.float64).reshape(
        profile.shape
    )
    return applied, [Z(rational(value)) for value in exact]


def rounded_weight(value: Fraction) -> float:
    """Certify nearest-even binary64 conversion by exact adjacent midpoints.

    Normalized nonnegative weights lie in [0,1], so all three observed floats
    are finite. Fraction distances prove the conversion without trusting the
    float converter as an unexamined rounding oracle.
    """
    assert 0 <= value <= 1
    candidate = float(value)
    distance = abs(Fraction.from_float(candidate) - value)
    even = int(np.array([candidate], dtype=np.float64).view(np.uint64)[0]) % 2 == 0
    for neighbor in (nextafter(candidate, -float("inf")), nextafter(candidate, float("inf"))):
        other_distance = abs(Fraction.from_float(neighbor) - value)
        assert distance < other_distance or (distance == other_distance and even)
    return candidate


def certificate(transfer: ComplexArray, profile: FloatArray, minimum: float) -> bool:
    """Check only the observable returned-diagnostic policy with exact dyadics."""
    size = profile.size
    origin_point = np.count_nonzero(profile) == 1 and profile.flat[0] > 0
    eta = 128 * size * Fraction(1, 2**52) + 4 * size * Fraction(1, 2**1074)
    for index, value in np.ndenumerate(transfer):
        allowance = (
            Fraction() if origin_point or index == tuple(n // 2 for n in profile.shape) else eta
        )
        boundary = Fraction.from_float(minimum) + allowance
        square = (
            Fraction.from_float(float(value.real)) ** 2
            + Fraction.from_float(float(value.imag)) ** 2
        )
        if square < boundary * boundary:
            return False
    return True


@dataclass
class Case:
    """Closed public generator inputs, without any product records or output."""

    images: NDArray[Any]
    phases: NDArray[Any]
    profile: FloatArray
    carrier: tuple[int, int]
    spacing: tuple[float, float, float]
    anchor: Index
    kernel: FloatArray


def model_case(
    shape: Index = (2, 3, 4),
    anchor: Index = (1, 2, 1),
    profile_shift: Index = (0, 0, 0),
    phase_shift: float = 0.0,
) -> Case:
    """Generate finite-profile raw exposures by the squared three-field model."""
    profile = np.zeros(shape, dtype=np.float64)
    profile[0, 0, 0] = 1
    profile[0, 0, 1 % shape[2]] += 4
    profile[0, (shape[1] - 1) % shape[1], 0] += 0.5
    profile = np.roll(profile, profile_shift, axis=(0, 1, 2))
    kernel = np.full(shape, 1 / 128, dtype=np.float64)
    secondary = (0, (shape[1] - 1) % shape[1], 1 % shape[2])
    if secondary != (0, 0, 0):
        kernel[secondary] += 1 / 16
    kernel[0, 0, 0] = 0
    kernel[0, 0, 0] = 1 - np.sum(kernel)
    phases = np.array([0.13, 0.84, 1.91, 2.76, 3.69, 4.82, 5.63], dtype=np.float64)
    carrier = (1, -1)
    brightness = Decimal(16)
    with localcontext() as context:
        context.prec = PRECISION
        _, weights = normalized_profile(profile)
        images = np.empty((len(phases), *shape))
        sites = indices(shape)
        for phase_index, phase in enumerate(phases):
            for n in sites:
                total = Decimal()
                for j, weight in zip(sites, weights, strict=True):
                    emission = tuple(
                        (ja + ba) % na for ja, ba, na in zip(j, anchor, shape, strict=True)
                    )
                    displacement = tuple(
                        (na - ja) % sa for na, ja, sa in zip(n, emission, shape, strict=True)
                    )
                    theta = 2 * pi() * (
                        Decimal(carrier[0] * emission[1]) / shape[1]
                        + Decimal(carrier[1] * emission[2]) / shape[2]
                    ) + d(phase)
                    axial = 2 * pi() * Decimal(displacement[0]) / shape[0]
                    field = angle_phasor(axial) + angle_phasor(theta) + angle_phasor(-theta)
                    intensity = (field.re * field.re + field.im * field.im) / 3
                    total += brightness * weight.re * d(kernel[displacement]) * intensity
                images[phase_index][n] = float(total)
    return Case(images, phases + phase_shift, profile, carrier, (0.5, 0.25, 0.125), anchor, kernel)


def algebra_case(
    dc: FloatArray, c1: ComplexArray | None = None, c2: ComplexArray | None = None
) -> Case:
    """Generate arbitrary signed observations with the represented public basis."""
    shape: Index = (dc.shape[0], dc.shape[1], dc.shape[2])
    phases = np.array([0.13, 0.84, 1.91, 2.76, 3.69, 4.82, 5.63])
    first = np.zeros(shape, dtype=np.complex128) if c1 is None else c1
    second = np.zeros(shape, dtype=np.complex128) if c2 is None else c2
    h = represented_basis(phases)
    images = np.empty((len(phases), *shape))
    for p, row in enumerate(h):
        images[p] = dc + 2 * first.real * row[1] - 2 * first.imag * row[2]
        images[p] += 2 * second.real * row[3] - 2 * second.imag * row[4]
    profile = np.zeros(shape)
    profile.flat[0] = 1
    return Case(images, phases, profile, (0, 0), (0.5, 0.25, 0.125), (0, 0, 0), dc.copy())


def declare(
    case: Case, *, grouped: bool = False, source_layout: bool = False, kind: str = "sim_beads"
) -> Any:
    """Use only the real public raw-declaration entry, with distinct groups."""
    from simrecon import declare_acquisition

    if grouped:
        canonical = np.empty((2, 1, 2, *case.images.shape))
        for t, c, o in product(range(2), range(1), range(2)):
            canonical[t, c, o] = case.images * (1 + t + 2 * o)
        names = ["time", "channel", "orientation", "phase", "z", "y", "x"]
    else:
        canonical = case.images[None]
        names = ["orientation", "phase", "z", "y", "x"]
    if source_layout:
        permutation = [
            names.index("z"),
            *[i for i, name in enumerate(names) if name not in ("z", "y", "x")],
            names.index("y"),
            names.index("x"),
        ]
        data = canonical.transpose(permutation)
        axes = [names[i] for i in permutation]
    else:
        data, axes = canonical, names
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": kind,
        "axes": axes,
        "sampling_um": {"z": 3.0, "y": None, "x": 7.0},
        "intensity_unit": "count",
        "acquisition_id": "finite-observations",
        "calibration_id": "declared-profile",
        "wavelengths_nm": {"0": 500.0},
        "overrides": {"sampling_um": {"z": None, "y": 9.0, "x": 8.0}},
    }
    return declare_acquisition(
        data, config=config, original_metadata={"opaque": [b"retained", (1, None)]}
    )


def arguments(case: Case, **changes: Any) -> dict[str, Any]:
    """Supply every required declaration explicitly."""
    result: dict[str, Any] = {
        "group": {"orientation": 0},
        "offset": 0,
        "response": 1,
        "output_unit": "electron",
        "phases_rad": case.phases,
        "voxel_size_um": case.spacing,
        "bead_profile": case.profile,
        "calibration_carrier_bins": case.carrier,
        "min_profile_transfer": 0.1,
    }
    result.update(changes)
    return result


@dataclass
class Truth:
    """Independent raw fit, finite response and conservative composition bounds."""

    components: list[list[Z]]
    profile: list[Z]
    spectra: list[list[Z]]
    localization: list[Decimal]
    origin: Index
    spectral_budget: list[list[Decimal]]
    spatial_budget: Decimal
    separation_budget: Decimal


def expected(case: Case, minimum: float = 0.1) -> Truth:
    """Propagate separation, original-mass, profile and arithmetic budgets.

    First bound the raw fit against its represented-matrix solution. Its mass
    perturbation is M*e0. Normalize with (M*em+abs(A)*M*e0)/(S-M*e0), then
    divide by the independent ideal profile. Product diagnostic fields never
    supply expected truth or a numerical-accuracy certificate.
    """
    with localcontext() as context:
        context.prec = PRECISION
        shape: Index = (case.profile.shape[0], case.profile.shape[1], case.profile.shape[2])
        size = prod(shape)
        components = fit(case.images, case.phases)
        mass = sum((value.re for value in components[0]), Decimal())
        assert mass > 0
        _, p = normalized_profile(case.profile)
        profile = transform(p, shape)
        frequency = modes(shape)
        locations = indices(shape)
        lookup = {
            tuple(ka % na for ka, na in zip(k, shape, strict=True)): i
            for i, k in enumerate(frequency)
        }
        a = [transform([value.scale(1 / mass) for value in row], shape) for row in components]
        shifted_profile = [
            [
                profile[
                    lookup[
                        (
                            k[0] % shape[0],
                            (k[1] - order * case.carrier[0]) % shape[1],
                            (k[2] - order * case.carrier[1]) % shape[2],
                        )
                    ]
                ]
                for k in frequency
            ]
            for order in range(3)
        ]
        q = [
            [numerator / divisor for numerator, divisor in zip(row, divisors, strict=True)]
            for row, divisors in zip(a, shifted_profile, strict=True)
        ]
        localization = [value.re for value in inverse(q[0], shape)]
        peak = max(localization)
        assert peak > 0 and localization.count(peak) == 1
        origin = locations[localization.index(peak)]
        spectra = [
            [
                value * root(cycles(k, origin, shape))
                for k, value in zip(frequency, row, strict=True)
            ]
            for row in q
        ]
        identity = np.count_nonzero(case.profile) == 1 and case.profile.flat[0] > 0
        eta = Decimal() if identity else 128 * size * EPS + 4 * size * Q0
        e = (
            8192 * len(case.phases) * EPS * max(abs(d(value)) for value in case.images.flat)
            + 8 * Q0
        )
        mass_error = size * e
        assert mass > mass_error
        # Each complex side coordinate has two real errors; 2e is a safe modulus bound.
        numerator_errors = [size * e, 2 * size * e, 2 * size * e]
        bounds: list[list[Decimal]] = []
        dq0: list[Decimal] = []
        for order in range(3):
            lam = (
                sum((value.l1() for value in components[order]), Decimal())
                + (1 if order == 0 else 2) * size * e
            ) / (mass - mass_error)
            da = 512 * size * EPS * lam + 16 * size * Q0
            row_bounds = []
            for node, (numerator, divisor) in enumerate(
                zip(a[order], shifted_profile[order], strict=True)
            ):
                k = frequency[node]
                shifted = (
                    k[0] % shape[0],
                    (k[1] - order * case.carrier[0]) % shape[1],
                    (k[2] - order * case.carrier[1]) % shape[2],
                )
                p_error = Decimal() if identity or shifted == (0, 0, 0) else eta
                mu_lower = divisor.magnitude() - p_error
                assert mu_lower >= d(minimum)
                a_error = (numerator_errors[order] + numerator.magnitude() * mass_error) / (
                    mass - mass_error
                )
                a_upper = numerator.magnitude() + a_error
                dq = da / mu_lower + a_upper * p_error / (d(minimum) * mu_lower)
                dq += 128 * EPS * (a_upper + da) / mu_lower + 16 * Q0
                delta = dq + 128 * EPS * (a_upper / divisor.magnitude() + dq) + 16 * Q0
                row_bounds.append(delta + a_error / divisor.magnitude())
                if order == 0:
                    dq0.append(dq)
            bounds.append(row_bounds)
        inverse_l1 = sum((value.l1() for value in q[0]), Decimal()) / size
        spatial = (
            sum(dq0, Decimal()) / size
            + 512 * size * EPS * (inverse_l1 + 2 * max(bounds[0]))
            + 16 * size * Q0
        )
        spatial += max(bounds[0])
        ordered = sorted(localization, reverse=True)
        if len(ordered) > 1:
            assert ordered[0] - ordered[1] > 2 * spatial
        return Truth(components, profile, spectra, localization, origin, bounds, spatial, e)


def assert_close(actual: Any, target: Z, budget: Decimal) -> None:
    """Compare complex error in decimal units; never round a tiny budget to zero."""
    with localcontext() as context:
        context.prec = PRECISION
        assert (z(actual) - target).magnitude() <= budget


def specimen_images(case: Case, specimen: FloatArray, phases: FloatArray) -> FloatArray:
    """Generate specimen exposures by real-space squared fields and convolution.

    Kernel, specimen and physical carrier are generator truth, never calibration
    operation inputs. The axial field has one periodic turn, as in model_case.
    """
    shape: Index = (specimen.shape[0], specimen.shape[1], specimen.shape[2])
    sites = indices(shape)
    images = np.empty((len(phases), *shape))
    with localcontext() as context:
        context.prec = PRECISION
        for p, phase in enumerate(phases):
            for n in sites:
                total = Decimal()
                for j in sites:
                    u = tuple((na - ja) % size for na, ja, size in zip(n, j, shape, strict=True))
                    theta = 2 * pi() * (
                        Decimal(case.carrier[0] * j[1]) / shape[1]
                        + Decimal(case.carrier[1] * j[2]) / shape[2]
                    ) + d(phase)
                    field = (
                        root(Fraction(u[0], shape[0])) + angle_phasor(theta) + angle_phasor(-theta)
                    )
                    total += d(specimen[j]) * d(case.kernel[u]) * (field.re**2 + field.im**2) / 3
                images[p][n] = float(total)
    return images


def extreme_components_case() -> Case:
    """Use a well-conditioned raw fit with finite components and |c1|>Fmax.

    These fixed phases and signed observations were selected using only the
    independent represented-matrix observer. No product outputs selected them.
    """
    case = algebra_case(np.ones((1, 1, 1)))
    case.phases = np.array(
        [
            -2.7028908244147267,
            -1.9599870331024496,
            0.2389641531911577,
            0.5675629086470617,
            1.1030167089891814,
            1.4285528836688266,
            1.8682326012516297,
        ]
    )
    case.images = (np.array([-0.95, 0.95, 0.95, 0.95, -0.95, -0.95, -0.95]) * float(FMAX)).reshape(
        7, 1, 1, 1
    )
    return case


def estimator(
    images: FloatArray,
    phases: FloatArray,
    transfers: list[list[Z]],
    carrier: tuple[int, int],
    output_shape: Index,
    penalty: Decimal,
    mask: FloatArray,
    transfer_errors: list[list[Decimal]],
) -> tuple[list[Z], list[Z], list[Decimal]]:
    """Evaluate the five-order finite estimator and transfer perturbation bound.

    Direct sums implement both signs, all-axis modular reflection and nonwrapping
    placement. Ridge bounds the perturbed denominator below by penalty. For
    |dt|<=e, dU<=sum(e*|D|), dV<=sum(2*|t|*e+e**2), hence
    |dQ|<=dU/penalty+|U|*dV/(penalty*(V+penalty)). This separates
    calibration error from reconstruction's own stored-input arithmetic budget.
    """
    with localcontext() as context:
        context.prec = PRECISION
        shape: Index = (images.shape[1], images.shape[2], images.shape[3])
        detector = modes(shape)
        lookup = {k: i for i, k in enumerate(detector)}
        modular = {
            tuple(v % n for v, n in zip(k, shape, strict=True)): i for i, k in enumerate(detector)
        }
        bands = [transform(row, shape) for row in fit(images, phases)]
        spectrum: list[Z] = []
        errors: list[Decimal] = []
        for q, amplitude in zip(modes(output_shape), mask.flat, strict=True):
            numerator = Z()
            denominator = Decimal()
            du = dv = Decimal()
            for order in range(-2, 3):
                j = (q[0], q[1] + order * carrier[0], q[2] + order * carrier[1])
                if j not in lookup:
                    continue
                node = lookup[j]
                if order < 0:
                    node = modular[tuple(-v % n for v, n in zip(j, shape, strict=True))]
                t = transfers[abs(order)][node]
                measurement = bands[abs(order)][node].scale(Decimal(1) / prod(shape))
                if order < 0:
                    t, measurement = t.conjugate(), measurement.conjugate()
                allowance = transfer_errors[abs(order)][node]
                numerator += t.conjugate() * measurement
                denominator += t.re**2 + t.im**2
                du += allowance * measurement.magnitude()
                dv += 2 * t.magnitude() * allowance + allowance**2
            spectrum.append((numerator / Z(denominator + penalty)).scale(d(amplitude)))
            errors.append(
                d(amplitude)
                * (du / penalty + numerator.magnitude() * dv / (penalty * (denominator + penalty)))
            )
        # inverse() contains 1/P; reconstruction uses the unnormalized sum.
        volume = [value.scale(d(prod(output_shape))) for value in inverse(spectrum, output_shape)]
        return spectrum, volume, errors
