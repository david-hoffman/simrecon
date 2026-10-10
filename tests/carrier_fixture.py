"""Independent finite-sum acquisitions and stored-value scan oracles.

No production solver, separation, transform or calibration builds expectations.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

Real = npt.NDArray[np.float64]
Complex = npt.NDArray[np.complex128]


def modes(n: int) -> range:
    return range(-(n // 2), (n + 1) // 2)


def synthesize(coefficients: Complex) -> Complex:
    """Positive-sign Fourier SERIES, with index-zero origin and no 1/M."""
    ny, nx = coefficients.shape
    result = np.zeros((ny, nx), dtype=np.complex128)
    for j, ky in enumerate(modes(ny)):
        for column, kx in enumerate(modes(nx)):
            for y in range(ny):
                for x in range(nx):
                    angle = 2 * np.pi * (ky * y / ny + kx * x / nx)
                    result[y, x] += coefficients[j, column] * complex(np.cos(angle), np.sin(angle))
    return result


def direct_dft(values: Complex) -> Complex:
    """Long-double finite sums; independent of the runtime FFT backend."""
    ny, nx = values.shape
    out = np.zeros((ny, nx), dtype=np.complex128)
    pi = np.arccos(np.longdouble(-1))
    for j, ky in enumerate(modes(ny)):
        for column, kx in enumerate(modes(nx)):
            total = np.clongdouble(0)
            for y in range(ny):
                for x in range(nx):
                    angle = -2 * pi * (np.longdouble(ky * y) / ny + np.longdouble(kx * x) / nx)
                    total += np.clongdouble(values[y, x]) * (
                        np.cos(angle) + np.clongdouble(1j) * np.sin(angle)
                    )
            out[j, column] = total / (ny * nx)
    return out


def solve_three(matrix: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction]:
    """Exact rational elimination on the represented 3-column Gram system.

    Normal equations are exact here, not a float product solver. This independently
    defines the stored-input minimizer, including off-model observations.
    """
    a = [row.copy() + [b] for row, b in zip(matrix, rhs, strict=True)]
    for j in range(3):
        pivot = next(i for i in range(j, 3) if a[i][j])
        a[j], a[pivot] = a[pivot], a[j]
        divisor = a[j][j]
        a[j] = [v / divisor for v in a[j]]
        for i in range(3):
            if i != j:
                factor = a[i][j]
                a[i] = [v - factor * w for v, w in zip(a[i], a[j], strict=True)]
    return [row[3] for row in a]


def stored_bands(images: Real, steps: Real) -> tuple[Complex, Complex]:
    """Exact represented-trigonometric least squares, then direct finite DFT.

    Scale BEFORE solving/DFT; gain and residual are invariant under this common
    factor. This also avoids oracle overflow for huge/tiny acquisitions.
    """
    converted = images.astype(np.float64)
    scale = float(np.max(np.abs(converted)))
    if scale == 0:
        zero = np.zeros(images.shape[1:], dtype=np.complex128)
        return zero, zero.copy()
    h = [
        [Fraction(1), Fraction(float(c)), Fraction(float(s))]
        for c, s in zip(np.cos(steps), np.sin(steps), strict=True)
    ]
    gram = [[sum((row[i] * row[j] for row in h), Fraction()) for j in range(3)] for i in range(3)]
    dc = np.zeros(images.shape[1:], dtype=np.complex128)
    c1 = dc.copy()
    denominator = Fraction(scale)
    for y in range(images.shape[1]):
        for x in range(images.shape[2]):
            b = [Fraction(float(v)) / denominator for v in converted[:, y, x]]
            rhs = [
                sum((row[j] * v for row, v in zip(h, b, strict=True)), Fraction()) for j in range(3)
            ]
            a, cosine, sine = solve_three(gram, rhs)
            dc[y, x] = float(a)
            c1[y, x] = complex(float(cosine / 2), -float(sine / 2))
    return direct_dft(dc), direct_dft(c1)


@dataclass
class Acquisition:
    """Independent converted acquisition and explicit calibration record inputs."""

    images: npt.NDArray[Any]
    steps: Real
    transfer: Complex
    dc_coefficients: Complex
    plus_coefficients: Complex
    true_carrier: tuple[int, int] = (1, 1)
    theta: float = 0.63
    modulation: float = 0.72
    spacing: tuple[float, float] = (0.2, 0.35)
    source: str = "  independent finite-sum calibration  "

    def otf(self, public: Any, **changes: Any) -> Any:
        ny, nx = self.transfer.shape
        fields = {
            "values": self.transfer.copy(),
            "fy_per_um": np.array(list(modes(ny)), dtype=np.float64) / (ny * self.spacing[0]),
            "fx_per_um": np.array(list(modes(nx)), dtype=np.float64) / (nx * self.spacing[1]),
            "pixel_size_um": self.spacing,
            "origin_yx": (0, 0),
            "source": self.source,
        }
        fields.update(changes)
        record_name = "Otf2D"
        return getattr(public, record_name)(**fields)


def acquisition(
    shape: tuple[int, int] = (5, 7),
    *,
    steps: Real | None = None,
    off_model: bool = False,
    modulation: float = 0.72,
) -> Acquisition:
    """Real asymmetric object, explicit complex OTF and alias-free illumination.

    Object modes fit strictly inside the grid after shifts +/- (1,1). The
    three nonnegative kernel masses 0.55,0.15,0.30 define the transfer directly.
    """
    ny, nx = shape
    if steps is None:
        steps = np.array([-0.8, 0.17, 1.6, 3.1, 4.7], dtype=np.float64)
    ky = np.array(list(modes(ny)))[:, None]
    kx = np.array(list(modes(nx)))[None, :]
    transfer = (
        0.55 + 0.15 * np.exp(-2j * np.pi * ky / ny) + 0.30 * np.exp(-2j * np.pi * kx / nx)
    ).astype(np.complex128)
    specimen = np.zeros(shape, dtype=np.complex128)
    cy, cx = ny // 2, nx // 2
    specimen[cy, cx] = 3
    for (y, x), value in {
        (1, 0): 0.32 + 0.11j,
        (0, 1): -0.27 + 0.19j,
        (1, -1): 0.13 - 0.08j,
    }.items():
        specimen[cy + y, cx + x] = value
        specimen[cy - y, cx - x] = value.conjugate()
    dc = 1.3 * transfer * specimen
    plus = np.zeros(shape, dtype=np.complex128)
    theta = 0.63
    for j, y in enumerate(modes(ny)):
        for column, x in enumerate(modes(nx)):
            if y - 1 in modes(ny) and x - 1 in modes(nx):
                plus[j, column] = (
                    1.3
                    * modulation
                    / 2
                    * np.exp(1j * theta)
                    * transfer[j, column]
                    * specimen[cy + y - 1, cx + x - 1]
                )
    if off_model:
        # A mixture of relative-phase harmonics on DIFFERENT carriers is a
        # legitimate arbitrary input, not a claim of one physical carrier.
        # Each distractor now has independently informative nonzero overlap.
        for (shift_y, shift_x), gain in {
            (0, 1): 0.28 - 0.16j,
            (-1, -1): -0.24 + 0.23j,
            (0, 0): 0.31 + 0.08j,
        }.items():
            for j, y in enumerate(modes(ny)):
                for column, x in enumerate(modes(nx)):
                    if y - shift_y in modes(ny) and x - shift_x in modes(nx):
                        plus[j, column] += (
                            1.3
                            * gain
                            * transfer[j, column]
                            * specimen[cy + y - shift_y, cx + x - shift_x]
                        )
    spatial_dc = synthesize(dc).real
    spatial_plus = synthesize(plus)
    images = np.array(
        [
            spatial_dc + 2 * (spatial_plus.real * np.cos(p) - spatial_plus.imag * np.sin(p))
            for p in steps
        ]
    )
    if off_model:
        # A second temporal harmonic makes the stored-data projection oracle necessary.
        images[:, 0, 1] += 0.08 * np.cos(2 * steps + 0.2)
    return Acquisition(images, steps.copy(), transfer, dc, plus, modulation=modulation)


def two_pixel(
    *, transfer_edge: float = 1.0, dc_odd: bool = False, plus: complex = 0.2 + 0.1j
) -> Acquisition:
    steps = np.array([-0.8, 0.17, 1.6, 3.1, 4.7])
    dc = np.array([[1.0, -1.0] if dc_odd else [1.0, 1.0]])
    c1: Complex = np.array([[plus, -plus]], dtype=np.complex128)
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in steps])
    return Acquisition(
        images,
        steps,
        np.array([[transfer_edge, 1]], dtype=np.complex128),
        direct_dft(dc.astype(np.complex128)),
        direct_dft(c1),
        true_carrier=(0, 0) if dc_odd else (0, -1),
    )


@dataclass(frozen=True)
class Fit:
    """Independent scalar diagnostic and oracle conditioning measurements."""

    gain: complex
    residual: float
    overlap: int
    norm_x: float
    norm_y: float
    correlation: float


def fit(dc: Complex, plus: Complex, transfer: Complex, carrier: tuple[int, int]) -> Fit | str:
    ny, nx = transfer.shape
    ky, kx = (int(v) for v in carrier)
    pairs = [
        (j, column, j + ky, column + kx)
        for j in range(ny)
        for column in range(nx)
        if 0 <= j + ky < ny and 0 <= column + kx < nx
    ]
    if not pairs:
        return "no_illumination_overlap"
    x = np.array([transfer[a, b] * dc[j, column] for j, column, a, b in pairs])
    y = np.array([transfer[j, column] * plus[a, b] for j, column, a, b in pairs])
    sx, sy = float(np.max(np.abs(x))), float(np.max(np.abs(y)))
    if not sx or not sy:
        return "unidentifiable_illumination"
    xn, yn = x / sx, y / sy
    nxnorm, nynorm = float(np.linalg.norm(xn)), float(np.linalg.norm(yn))
    u, v = xn / nxnorm, yn / nynorm
    correlation = complex(np.vdot(u, v))
    if correlation == 0:
        return "unidentifiable_illumination"
    gain = (sy / sx) * (nynorm / nxnorm) * correlation
    residual = float(np.linalg.norm(v - correlation * u))
    return Fit(gain, residual, len(pairs), sx * nxnorm, sy * nynorm, abs(correlation))


def stored_fits(case: Acquisition, carriers: list[tuple[int, int]]) -> list[Fit | str]:
    dc, plus = stored_bands(case.images, case.steps)
    return [fit(dc, plus, case.transfer, carrier) for carrier in carriers]


def delta(case: Acquisition) -> float:
    n, ny, nx = case.images.shape
    return 8192 * n * ny * nx * 2.0**-52


def informative(case: Acquisition, expected: Fit) -> bool:
    """Check ALL selected accuracy premises for B-normalized stored_fits output.

    A small 3x3 Gram eigenproblem checks phase conditioning independently of the
    SVD/lstsq fault seams. Fixtures are far from condition=10; no threshold-edge
    classification theorem is claimed for this observer.
    """
    steps = case.steps.astype(np.float64)
    h = np.column_stack([np.ones(len(steps)), np.cos(steps), np.sin(steps)])
    eigenvalues = np.linalg.eigvalsh(h.T @ h)
    condition_ok = eigenvalues[0] > 0 and eigenvalues[-1] <= 100 * eigenvalues[0]
    return bool(
        condition_ok
        and expected.norm_x >= 1 / 8
        and expected.norm_y >= 1 / 8
        and expected.correlation >= 1 / 4
        and 1e-4 <= abs(expected.gain) <= 10
        and np.isfinite(expected.gain)
        and np.isfinite(expected.residual)
    )


def image_dtype_acquisition(dtype: Any) -> Acquisition:
    """Keep unsigned values positive AND their fitted norms informative."""
    case = acquisition(off_model=np.dtype(dtype).kind != "u")
    case.images = (case.images * 4).astype(dtype)
    return case


def large_step_acquisition() -> Acquisition:
    """Retain all original enormous steps with added identifiable phase support."""
    return acquisition(
        steps=np.array([1e20, -1e21, 1e22, -1e23, 1e24, 0.0, 2.0, 4.0]),
        off_model=True,
    )


@dataclass(frozen=True)
class RangeWitness:
    """Dedicated Decimal range proof; never materialize an overflowing ratio."""

    exact_dc: tuple[Fraction, ...]
    exact_cosine: tuple[Fraction, ...]
    norm_ratio_lower: Decimal
    modulation: Decimal
    modulation_lower: Decimal
    modulation_upper: Decimal


def decimal_pi() -> Decimal:
    """Machin identity from rational arctangent series, with ample guard digits.

    tan(4*atan(1/5))=120/119; subtracting atan(1/239) gives tan=1
    in the first quadrant. Thus pi=16*atan(1/5)-4*atan(1/239).
    Alternating series are stopped below 1e-115, at precision 120.
    """
    with localcontext() as context:
        context.prec = 120

        def arctangent(denominator: int) -> Decimal:
            x = Decimal(1) / denominator
            power = x
            result = x
            for index in range(1, 1000):
                power *= -(x * x)
                term = power / (2 * index + 1)
                result += term
                if abs(term) < Decimal("1e-115"):
                    return result
            raise AssertionError("independent arctangent series did not converge")

        return 16 * arctangent(5) - 4 * arctangent(239)


def decimal_sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    """Taylor finite sums for range-witness angles |angle|<17, at 120 digits."""
    with localcontext() as context:
        context.prec = 120
        sine_term, cosine_term = angle, Decimal(1)
        sine, cosine = sine_term, cosine_term
        square = -(angle * angle)
        for index in range(1, 1000):
            sine_term *= square / ((2 * index) * (2 * index + 1))
            cosine_term *= square / ((2 * index - 1) * (2 * index))
            sine += sine_term
            cosine += cosine_term
            if max(abs(sine_term), abs(cosine_term)) < Decimal("1e-110"):
                return sine, cosine
        raise AssertionError("independent trigonometric series did not converge")


def overflow_ratio_acquisition() -> tuple[Acquisition, RangeWitness]:
    """Reachable stored-input case with huge norm ratio and finite modulation.

    Opposite-step pair sums prove exact DC=1 and cosine=0. The Fourier transform
    of that constant is supplied by the exact root-sum identity, so finite DFT
    rounding cannot invent a spurious non-DC x component. Only the sideband uses
    direct finite sums. Decimal arithmetic handles the independent range proof;
    the old generic fit's raw sy/sx is deliberately not used for this fixture.
    """
    steps = np.array([-0.4, 0.4, -1.2, 1.2])
    coordinate = np.arange(7)
    g = 0.1 * np.cos(2 * np.pi * 3 * coordinate / 7) + 1e-8 * np.cos(2 * np.pi * coordinate / 7)
    quantum = 2.0**-52
    images = np.array([1 + np.rint(-2 * g * np.sin(step) / quantum) * quantum for step in steps])[
        :, None, :
    ]
    h = [[Fraction(1), Fraction(float(np.cos(p))), Fraction(float(np.sin(p)))] for p in steps]
    gram = [[sum((row[i] * row[j] for row in h), Fraction()) for j in range(3)] for i in range(3)]
    exact_dc, exact_cosine, exact_plus_imag = [], [], []
    spatial_plus = np.zeros((1, 7), dtype=np.complex128)
    for column in range(7):
        b = [Fraction(float(v)) for v in images[:, 0, column]]
        assert b[0] + b[1] == 2 and b[2] + b[3] == 2
        rhs = [sum((row[j] * v for row, v in zip(h, b, strict=True)), Fraction()) for j in range(3)]
        a, cosine, sine = solve_three(gram, rhs)
        exact_dc.append(a)
        exact_cosine.append(cosine)
        exact_plus_imag.append(-sine / 2)
        spatial_plus[0, column] = complex(float(cosine / 2), -float(sine / 2))
    dc = np.zeros((1, 7), dtype=np.complex128)
    dc[0, 3] = 1  # Exact finite Fourier transform of the independently proved constant.
    plus = direct_dft(spatial_plus)
    transfer = np.array([[1, 1, 1e-310, 1, 1e-310, 1, 1]], dtype=np.complex128)
    with localcontext() as context:
        context.prec = 120
        x_norm = Decimal.from_float(float(transfer[0, 4].real))
        pi = decimal_pi()

        def sideband(mode: int) -> tuple[Decimal, Decimal]:
            real, imag = Decimal(0), Decimal(0)
            for coordinate, value in enumerate(exact_plus_imag):
                coefficient = Decimal(value.numerator) / Decimal(value.denominator)
                sine, cosine = decimal_sin_cos(-2 * pi * mode * coordinate / 7)
                real -= coefficient * sine
                imag += coefficient * cosine
            return real / 7, imag / 7

        # The series' truncation and precision-120 roundoff are far below this
        # conservative coordinate margin (angles<17; terms bounded by exp(17)).
        margin = Decimal("1e-60")
        _, large_imag = sideband(3)
        norm_ratio_lower = (abs(large_imag) - margin) / x_norm
        # Only q=0 contributes to x/cross: gain=Dplus(1)/H(1).
        real, imag = sideband(1)
        modulation = 2 * (real * real + imag * imag).sqrt() / x_norm
        modulation_lower = 2 * (abs(imag) - margin) / x_norm
        modulation_upper = 2 * (abs(real) + abs(imag) + 2 * margin) / x_norm
    case = Acquisition(images, steps, transfer, dc, plus, true_carrier=(0, 1))
    witness = RangeWitness(
        tuple(exact_dc),
        tuple(exact_cosine),
        norm_ratio_lower,
        modulation,
        modulation_lower,
        modulation_upper,
    )
    return case, witness
