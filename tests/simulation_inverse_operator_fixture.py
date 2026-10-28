"""Independent finite-sum references for the public inverse-operator contract.

No production output defines expected truth. Small dense matrices are deliberate:
this observer enumerates every source, focus, and four-sample pixel interaction.
"""

from __future__ import annotations

import math
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache, lru_cache
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]
Shape = tuple[int, int, int]
Spacing = tuple[float, float, float]


@lru_cache(maxsize=1)
def reference_pi() -> Decimal:
    """Compute pi independently with ample digits for finite float64 products."""
    with localcontext() as context:
        context.prec = 760
        a = Decimal(1)
        b = 1 / Decimal(2).sqrt()
        t = Decimal(1) / 4
        p = Decimal(1)
        for _ in range(12):
            next_a = (a + b) / 2
            b = (a * b).sqrt()
            t -= p * (a - next_a) ** 2
            a = next_a
            p *= 2
        return +((a + b) ** 2) / (4 * t)


def reduced_cis(angle: Decimal) -> complex:
    """Reduce at precision 730, then bound Taylor tails before float64 conversion."""
    with localcontext() as context:
        context.prec = 730
        tau = 2 * reference_pi()
        remainder = angle % tau
        if remainder > reference_pi():
            remainder -= tau
        if remainder < -reference_pi():
            remainder += tau
    with localcontext() as context:
        context.prec = 110
        cosine, sine = decimal_cis(remainder)
        return complex(float(cosine), float(sine))


def decimal(value: Any) -> Decimal:
    """Interpret normalized float64 settings as their exact real values."""
    return Decimal.from_float(float(value))


def illumination(
    source: tuple[int, int, int],
    focus: int,
    spacing: Spacing,
    carrier: Array,
    phase: Any,
    amplitudes: tuple[float, float, float],
    excitation: float,
    index: float,
) -> float:
    """Use the squared three-beam field, independently of harmonic application."""
    with localcontext() as context:
        context.prec = 730
        qy, qx = map(decimal, carrier)
        dz, dy, dx = map(decimal, spacing)
        k0 = decimal(index) / decimal(excitation)
        q2 = qy * qy + qx * qx
        # Rationalization avoids cancellation when q is small.
        kappa = q2 / (k0 + (k0 * k0 - q2).sqrt()) if q2 else Decimal(0)
        turns = qy * (Decimal(source[1]) + Decimal("0.5")) * dy
        turns += qx * (Decimal(source[2]) + Decimal("0.5")) * dx
        lateral = 2 * reference_pi() * turns + decimal(phase)
        axial = 2 * reference_pi() * kappa * Decimal(source[0] - focus) * dz
        maximum = max(map(float, amplitudes))
        a0, plus, minus = (float(a) / maximum for a in amplitudes)
        field = a0 + plus * reduced_cis(lateral - axial)
        field += minus * reduced_cis(-lateral - axial)
        return abs(field) ** 2 / math.fsum((a0 * a0, plus * plus, minus * minus))


def kernel_from_spectra(spectra: Array, shape: Shape) -> Array:
    """Invert tiny half spectra with exact algebraic accumulation, never FFT.

    These observers use lateral periods four/eight only. Their cosine roots
    lie in Q(sqrt(1/2)). Accumulate both rational coefficients exactly BEFORE
    evaluating the radical. This also resolves exact cancellations of arbitrary
    finite float32 unused-lag payloads, which float64 cosine sums cannot certify.
    The final 400-digit evaluation covers float32's entire exponent span and
    the binary rescalings used below; it is not a general-shape DFT oracle.
    """
    nz, ny, nx = shape
    fy, fx = 2 * ny, 2 * nx
    assert fy in (4, 8) and fx in (4, 8)
    roots = {
        4: [(1, 0), (0, 0), (-1, 0), (0, 0)],
        8: [(1, 0), (0, 1), (0, 0), (0, -1), (-1, 0), (0, -1), (0, 0), (0, 1)],
    }
    result = np.empty((nz, fy, fx), dtype=np.float64)
    for d, y, x in np.ndindex(result.shape):
        rational, radical = Fraction(0), Fraction(0)
        for frequency_y in range(fy):
            ay, by = roots[fy][frequency_y * y % fy]
            for k in range(nx + 1):
                ax, bx = roots[fx][k * x % fx]
                coefficient = Fraction.from_float(float(spectra[d, frequency_y, k]))
                coefficient *= 1 if k in (0, nx) else 2
                rational += coefficient * (ay * ax + Fraction(by * bx, 2))
                radical += coefficient * (ay * bx + by * ax)
        with localcontext() as context:
            context.prec = 400
            value = Decimal(rational.numerator) / Decimal(rational.denominator)
            value += (
                Decimal(radical.numerator) / Decimal(radical.denominator) * Decimal("0.5").sqrt()
            )
            result[d, y, x] = float(value / (fy * fx))
    return result


def lattice_cos(numerator: int, period: int) -> float:
    """Preserve exact quarter-turn values and reflected roots without clamping."""
    residue = numerator % period
    residue = min(residue, period - residue)
    sign = 1
    if 4 * residue > period:
        residue = period // 2 - residue
        sign = -1
    if residue == 0:
        return float(sign)
    if 4 * residue == period:
        return 0.0
    return sign * math.cos(2 * math.pi * residue / period)


def spectra_from_plane(plane: Array, shape: Shape) -> Array:
    """Direct forward DFT for a separately even test plane, with float32 storage."""
    nz, ny, nx = shape
    fy, fx = 2 * ny, 2 * nx
    result = np.empty((nz, fy, nx + 1), dtype=np.float32)
    # Assign mirrored rows from the same number to guarantee exact symmetry.
    for d, frequency_y, k in product(range(nz), range(ny + 1), range(nx + 1)):
        value = math.fsum(
            float(plane[d, y, x])
            * math.cos(2 * math.pi * frequency_y * y / fy)
            * math.cos(2 * math.pi * k * x / fx)
            for y in range(fy)
            for x in range(fx)
        )
        result[d, frequency_y, k] = value
        result[d, (-frequency_y) % fy, k] = value
    return result


def signed_spectra(shape: Shape) -> Array:
    """Represent signed low modes with exactly stored dyadic coefficients.

    For M=(2*Ny)*(2*Nx), the exact inverse is
    (d+1)/16 + (-1)**(d+y)/8 + (-1)**x/4
    + cos(pi*y/Ny)/16 + cos(pi*x/Nx)/32.
    DC, the two Nyquist modes, and the two cosine pairs are disjoint because
    Ny,Nx>=2. Both coefficients of each full-spectrum cosine pair are M*a/2.
    """
    nz, ny, nx = shape
    size = 4 * ny * nx
    result = np.zeros((nz, 2 * ny, nx + 1), dtype=np.float32)
    for d in range(nz):
        result[d, 0, 0] = size * (d + 1) / 16
        result[d, ny, 0] = size * (-1) ** d / 8
        result[d, 0, nx] = size / 4
        result[d, 1, 0] = result[d, 2 * ny - 1, 0] = size / 32
        result[d, 0, 1] = size / 64
    return result


def signed_kernel(shape: Shape) -> Array:
    """Evaluate the main fixture's analytic inverse independently of DFT sums."""
    nz, ny, nx = shape
    result = np.empty((nz, 2 * ny, 2 * nx), dtype=np.float64)
    for d, y, x in np.ndindex(result.shape):
        result[d, y, x] = (
            (d + 1) / 16
            + (-1) ** (d + y) / 8
            + (-1) ** x / 4
            + lattice_cos(y, 2 * ny) / 16
            + lattice_cos(x, 2 * nx) / 32
        )
    return result


def null_support_spectra(shape: Shape) -> Array:
    """Retain the old valid payload whose required finite kernel is exactly zero.

    In the full spectrum, each separated term has either (-1)**kx as its
    entire x factor or (-1)**ly as its entire y factor. Its inverse is thus
    supported on x=Nx or y=Ny. Neither index is a required finite lag.
    Expected finite H, B, G and every optical matrix are exactly zero. Never
    use a floating cancellation residue as this payload's truth or scale.
    """
    nz, ny, nx = shape
    result = np.empty((nz, 2 * ny, nx + 1), dtype=np.float32)
    for d, frequency_y, k in np.ndindex(result.shape):
        ly = min(frequency_y, 2 * ny - frequency_y)
        result[d, frequency_y, k] = ((-1) ** (d + ly + k)) * (1 + 3 * d + 2 * ly + k) / 8
    return result


def padding_only_spectra(shape: Shape, magnitude: float) -> Array:
    """Represent two unused-lag lines with exactly zero DC coefficient.

    In the full spectrum C[l,k]=a*(-1)**l*[k=0]-a*(-1)**k*[l=0].
    Its inverse is a/Fx*[y=Ny]-a/Fy*[x=Nx], identically zero on
    every required lag. DC cancellation leaves room for a separate tiny signal.
    """
    nz, ny, nx = shape
    result = np.zeros((nz, 2 * ny, nx + 1), dtype=np.float32)
    for ly in range(2 * ny):
        result[:, ly, 0] = magnitude * (-1) ** ly
    for k in range(nx + 1):
        result[:, 0, k] -= magnitude * (-1) ** k
    return result


def legendre_value_derivative(order: int, x: Decimal) -> tuple[Decimal, Decimal]:
    """Evaluate the canonical Legendre recurrence and its derivative."""
    previous, value = Decimal(1), x
    for n in range(2, order + 1):
        previous, value = value, ((2 * n - 1) * x * value - (n - 1) * previous) / n
    return value, order * (x * value - previous) / (x * x - 1)


@cache
def canonical_rule(order: int) -> tuple[tuple[Decimal, Decimal], ...]:
    """Isolate every canonical root; qualify weights by all exact moments.

    Domain Q<=37. Each root has a disjoint sign bracket of radius 1e-85.
    At precision 110 the recurrence's conservative 3**37 error amplification
    stays below 1e-89; endpoint values must exceed 1e-87. Q disjoint brackets
    exhaust the Q roots. The weight formula then fixes the canonical rule.
    """
    assert 1 <= order <= 37
    with localcontext() as context:
        context.prec = 110
        pairs = []
        brackets = []
        for i in range(1, order + 1):
            root = decimal(math.cos(math.pi * (i - 0.25) / (order + 0.5)))
            for _ in range(30):
                value, derivative = legendre_value_derivative(order, root)
                correction = value / derivative
                root -= correction
                if abs(correction) < Decimal("1e-100"):
                    break
            else:
                raise AssertionError("Canonical quadrature reference did not converge")
            low, high = root - Decimal("1e-85"), root + Decimal("1e-85")
            left = legendre_value_derivative(order, low)[0]
            right = legendre_value_derivative(order, high)[0]
            assert -1 < low < high < 1
            assert left * right < 0 and min(abs(left), abs(right)) > Decimal("1e-87")
            brackets.append((low, high))
            _, derivative = legendre_value_derivative(order, root)
            weight = 1 / ((1 - root * root) * derivative * derivative)
            pairs.append(((root + 1) / 2, weight))
        brackets.sort()
        assert all(a[1] < b[0] for a, b in zip(brackets, brackets[1:], strict=False))
        pairs.sort()
        assert all(weight > 0 for _, weight in pairs)
        for power in range(2 * order):
            moment = sum((w * u**power for u, w in pairs), Decimal(0))
            assert abs(moment - Decimal(1) / (power + 1)) < Decimal("1e-95")
        return tuple(pairs)


def bessel_zero(argument: Decimal) -> Decimal:
    """Sum J0 on |argument|<=8 with an alternating tail below 1e-95."""
    assert abs(argument) <= 8
    term = total = Decimal(1)
    for k in range(1, 180):
        term *= -(argument * argument) / (4 * k * k)
        total += term
        if k >= 4 and abs(term) < Decimal("1e-95"):
            return total
    raise AssertionError("Bessel reference tail not bounded")


def decimal_cis(angle: Decimal) -> tuple[Decimal, Decimal]:
    """Evaluate sine/cosine after reduction, with alternating tails below 1e-95."""
    angle %= 2 * reference_pi()
    if angle > reference_pi():
        angle -= 2 * reference_pi()
    if angle < -reference_pi():
        angle += 2 * reference_pi()
    cosine_term, sine_term = Decimal(1), angle
    cosine, sine = cosine_term, sine_term
    for k in range(1, 180):
        cosine_term *= -angle * angle / ((2 * k - 1) * (2 * k))
        sine_term *= -angle * angle / ((2 * k) * (2 * k + 1))
        cosine += cosine_term
        sine += sine_term
        if k >= 2 and max(abs(cosine_term), abs(sine_term)) < Decimal("1e-95"):
            return cosine, sine
    raise AssertionError("Trigonometric reference tail not bounded")


def physical_kernel(
    shape: Shape, spacing: Spacing, emission: float, index: float, na: float, order: int
) -> Array:
    """Evaluate the finite canonical pupil with qualified roots and series.

    Only the test domain (Q<=37, Bessel argument<=8, axial angle<=20) is claimed.
    No SciPy pupil, FFT or product-generated value supplies expected truth.
    Root/weight uncertainty is below 1e-78; series tails below 1e-95; float64
    conversion dominates. Tiny-NA fixtures rescale BOTH E and B after conversion.
    """
    nz, ny, nx = shape
    result = np.zeros((nz, 2 * ny, 2 * nx), dtype=np.float64)
    with localcontext() as context:
        context.prec = 110
        dz, dy, dx = map(decimal, spacing)
        radius, nu, beta = (
            decimal(na) / decimal(emission),
            decimal(index) / decimal(emission),
            decimal(na) / decimal(index),
        )
        for d, y, x in product(range(nz), range(-(ny - 1), ny), range(-(nx - 1), nx)):
            r = ((y * dy) ** 2 + (x * dx) ** 2).sqrt()
            real = imag = Decimal(0)
            for node, weight in canonical_rule(order):
                # Rationalization retains tiny but nonzero axial phase.
                root = (1 - beta * beta * node).sqrt()
                angle = 2 * reference_pi() * nu * (-d * dz) * (-beta * beta * node / (1 + root))
                assert abs(angle) <= 20
                radial = bessel_zero(2 * reference_pi() * radius * node.sqrt() * r)
                cosine, sine = decimal_cis(angle)
                real += weight * radial * cosine
                imag += weight * radial * sine
            result[d, y % (2 * ny), x % (2 * nx)] = float(
                reference_pi() * radius**2 * (real**2 + imag**2)
            )
    return result


def pixel_matrix(kernel: Array, shape: Shape, spacing: Spacing, *, absolute: bool = False) -> Array:
    """Form B_H, or G_H when absolute precedes the four-point pixel sum."""
    nz, ny, nx = shape
    result = np.empty((nz * (ny // 2) * (nx // 2), nz * ny * nx), dtype=np.float64)
    sites = list(np.ndindex(shape))
    for row, (z, y, x) in enumerate(np.ndindex((nz, ny // 2, nx // 2))):
        for column, (jz, jy, jx) in enumerate(sites):
            points = [
                float(
                    kernel[abs(z - jz), (2 * y + sy - jy) % (2 * ny), (2 * x + sx - jx) % (2 * nx)]
                )
                for sy, sx in product(range(2), repeat=2)
            ]
            if absolute:
                points = list(map(abs, points))
            result[row, column] = spacing[1] * spacing[2] * math.fsum(points)
    return result


def operator_matrix(
    kernel: Array,
    shape: Shape,
    spacing: Spacing,
    carrier: Array,
    phases: Array,
    amplitudes: tuple[float, float, float],
    excitation: float,
    index: float,
) -> Array:
    """Enumerate the finite optical matrix; its transpose is a real adjoint oracle."""
    base = pixel_matrix(kernel, shape, spacing)
    detector_shape = (shape[0], shape[1] // 2, shape[2] // 2)
    result = np.empty((len(phases) * base.shape[0], base.shape[1]), dtype=np.float64)
    # Illumination depends on source and focus, not the four lateral sample sites.
    for p, phase in enumerate(phases):
        factors = [
            [
                illumination(site, z, spacing, carrier, phase, amplitudes, excitation, index)
                for site in np.ndindex(shape)
            ]
            for z in range(shape[0])
        ]
        for row, (z, _, _) in enumerate(np.ndindex(detector_shape)):
            for column in range(base.shape[1]):
                result[p * base.shape[0] + row, column] = base[row, column] * factors[z][column]
    return result


def row_column_norms(matrix: Array) -> tuple[float, float]:
    """Compute tiny-reference absolute row and column sums without float32 work."""
    rows = max(math.fsum(abs(float(v)) for v in row) for row in matrix)
    columns = max(math.fsum(abs(float(v)) for v in column) for column in matrix.T)
    return rows, columns


def apply_reference(matrix: Array, values: Array, *, transpose: bool = False) -> Array:
    """Use fsum rather than a product BLAS/FFT path for independent values."""
    selected = matrix.T if transpose else matrix
    flat = values.ravel()
    return np.array(
        [
            math.fsum(float(a) * float(b) for a, b in zip(row, flat, strict=True))
            for row in selected
        ],
        dtype=np.float64,
    )


def light_bound(amplitudes: tuple[float, float, float]) -> float:
    """Evaluate L stably, including amplitudes whose raw square would overflow."""
    maximum = max(amplitudes)
    normalized = [a / maximum for a in amplitudes]
    return math.fsum(normalized) ** 2 / math.fsum(a * a for a in normalized)


def validate_reference_arithmetic() -> None:
    """Cross-check observers against analytic controls independent of production."""
    assert abs(float(reference_pi()) - math.pi) < 1e-15
    for angle in (-7.0, 0.0, 0.2, math.pi / 2, 12.5):
        assert abs(reduced_cis(decimal(angle)) - complex(math.cos(angle), math.sin(angle))) < 2e-15
    with localcontext() as context:
        context.prec = 730
        # More than 300 digits of reduction, with a known residual.
        angle = 2 * reference_pi() * Decimal(10) ** 310 + Decimal("0.125")
        assert abs(reduced_cis(angle) - complex(math.cos(0.125), math.sin(0.125))) < 2e-15
    shape = (2, 2, 4)
    spectra = np.full((2, 4, 5), 32.0, dtype=np.float32)
    recovered = kernel_from_spectra(spectra, shape)
    expected = np.zeros_like(recovered)
    expected[:, 0, 0] = 32
    np.testing.assert_allclose(recovered, expected, atol=8e-14, rtol=0)
    constant = np.full((2, 4, 8), 0.25)
    roundtrip = kernel_from_spectra(spectra_from_plane(constant, shape), shape)
    np.testing.assert_allclose(roundtrip, constant, atol=2e-14, rtol=0)
    spacing = (0.23, 0.17, 0.11)
    pupil = physical_kernel(shape, spacing, 0.6, 1.3, 0.8, 1)
    peak = math.pi * (0.8 / 0.6) ** 2
    np.testing.assert_allclose(pupil[:, 0, 0], peak, rtol=5e-16)
    # Q=1 has unit-modulus axial phase; every radial value is independent of z.
    np.testing.assert_allclose(pupil[0], pupil[1], atol=2e-15, rtol=2e-15)
    two_node = physical_kernel(shape, spacing, 0.6, 1.3, 0.8, 2)
    offset = 1 / (2 * math.sqrt(3))
    phase_difference = (
        2
        * math.pi
        * (1.3 / 0.6)
        * spacing[0]
        * (
            math.sqrt(1 - (0.8 / 1.3) ** 2 * (0.5 + offset))
            - math.sqrt(1 - (0.8 / 1.3) ** 2 * (0.5 - offset))
        )
    )
    assert abs(two_node[1, 0, 0] - peak * math.cos(phase_difference / 2) ** 2) < 3e-15
    # Challenge half-spectrum completion with an independent full complex DFT.
    general_spectrum = signed_spectra(shape)
    cosine_inverse = kernel_from_spectra(general_spectrum, shape)
    for d, y, x in np.ndindex(cosine_inverse.shape):
        terms = []
        for ly, kx in product(range(4), range(8)):
            value = (
                general_spectrum[d, ly, kx] if kx <= 4 else (general_spectrum[d, (-ly) % 4, 8 - kx])
            )
            angle = 2 * math.pi * (ly * y / 4 + kx * x / 8)
            terms.append(float(value) * complex(math.cos(angle), math.sin(angle)))
        full_inverse = (
            complex(math.fsum(v.real for v in terms), math.fsum(v.imag for v in terms)) / 32
        )
        assert abs(full_inverse.imag) < 1e-14
        assert abs(full_inverse.real - cosine_inverse[d, y, x]) < 1e-14
    site, focus, carrier, phase = (1, 1, 3), 0, np.array([-0.73, 0.41]), 0.27
    theta = 2 * math.pi * (carrier[0] * 1.5 * spacing[1] + carrier[1] * 3.5 * spacing[2]) + phase
    k0 = 1.3 / 0.5
    alpha_d = 2 * math.pi * (k0 - math.sqrt(k0 * k0 - math.fsum(carrier**2))) * spacing[0]
    a0, plus, minus = 0.7, 1.2, 0.25
    harmonic = 1 + 2 * (
        a0 * plus * math.cos(theta - alpha_d)
        + a0 * minus * math.cos(theta + alpha_d)
        + plus * minus * math.cos(2 * theta)
    ) / (a0 * a0 + plus * plus + minus * minus)
    assert (
        abs(
            illumination(site, focus, spacing, carrier, phase, (a0, plus, minus), 0.5, 1.3)
            - harmonic
        )
        < 2e-15
    )
    matrix = pixel_matrix(constant, shape, spacing)
    np.testing.assert_allclose(matrix, 4 * spacing[1] * spacing[2] * 0.25, rtol=2e-16)
    phases = np.array([0.1, 0.8])
    optical = operator_matrix(
        constant, shape, spacing, np.array([0.0, 0.0]), phases, (0.0, 2.0, 0.0), 0.5, 1.3
    )
    np.testing.assert_allclose(optical, np.tile(matrix, (2, 1)), rtol=5e-16)
    residual = np.arange(optical.shape[0], dtype=np.float32) - 3
    expected_adjoint = 4 * spacing[1] * spacing[2] * 0.25 * math.fsum(map(float, residual))
    np.testing.assert_allclose(
        apply_reference(optical, residual, transpose=True), expected_adjoint, atol=1e-15, rtol=0
    )
    checker = np.fromfunction(lambda d, y, x: (-1.0) ** x, (1, 4, 4))
    canceled = pixel_matrix(checker, (1, 2, 2), (1.0, 1.0, 1.0))
    uncanceled = pixel_matrix(checker, (1, 2, 2), (1.0, 1.0, 1.0), absolute=True)
    assert np.array_equal(canceled, np.zeros((1, 4)))
    assert np.array_equal(uncanceled, np.full((1, 4), 4.0))
    print(
        "reference arithmetic: analytic DFT, pupil, pixel/adjoint, "
        "phase reduction and scales passed"
    )


def validate_corrected_signed_reference() -> None:
    """Prove support, scales and scientifically distinct effects after B1 diagnosis."""
    spacing = (0.23, 0.17, 0.11)
    carrier, phases = np.array([-0.73, 0.41]), np.array([0.21, 1.37, -0.82])
    amplitudes = (0.7, 1.2, 0.25)
    # Independent algebraic roots for all grids used by the signed-cache tests.
    root = math.sqrt(0.5)
    roots = {4: [1.0, 0.0, -1.0, 0.0], 8: [1.0, root, 0.0, -root, -1.0, -root, 0.0, root]}
    for shape in ((1, 2, 4), (2, 4, 2), (3, 2, 4), (2, 2, 4)):
        nz, ny, nx = shape
        spectra = signed_spectra(shape)
        observed = kernel_from_spectra(spectra, shape)
        independent = np.empty_like(observed)
        for d, y, x in np.ndindex(observed.shape):
            independent[d, y, x] = (
                (d + 1) / 16
                + (-1) ** (d + y) / 8
                + (-1) ** x / 4
                + roots[2 * ny][y] / 16
                + roots[2 * nx][x] / 32
            )
        np.testing.assert_allclose(observed, independent, rtol=0, atol=2e-16)
        np.testing.assert_allclose(signed_kernel(shape), independent, rtol=0, atol=2e-16)
        required = [
            independent[d, y % (2 * ny), x % (2 * nx)]
            for d, y, x in product(range(nz), range(-ny + 1, ny), range(-nx + 1, nx))
        ]
        assert min(required) < 0 < max(required)
        # Opposite corners across the largest required axial separation are real interactions.
        far = independent[nz - 1, ny - 1, nx - 1]
        assert abs(far) > 0.01
        g = pixel_matrix(independent, shape, spacing, absolute=True)
        b = pixel_matrix(independent, shape, spacing)
        cr, cc = row_column_norms(g)
        assert cr > 0.01 and cc > 0.01
        assert float(np.max(g - np.abs(b))) > 0.001
        matrix = operator_matrix(observed, shape, spacing, carrier, phases, amplitudes, 0.48, 1.33)
        far_column = np.ravel_multi_index((nz - 1, ny - 1, nx - 1), shape)
        assert abs(matrix[0, far_column]) > 1e-4
        print(
            "signed shape",
            shape,
            "required min/max",
            min(required),
            max(required),
            "distant axial corner H",
            far,
            "G row/column",
            cr,
            cc,
            "opposite-corner coefficient",
            matrix[0, far_column],
        )
        # Verify the retained null payload's exact dyadic full-spectrum decomposition.
        null = null_support_spectra(shape)
        for d, frequency_y, frequency_x in np.ndindex((nz, 2 * ny, 2 * nx)):
            ly = min(frequency_y, 2 * ny - frequency_y)
            kx = min(frequency_x, 2 * nx - frequency_x)
            value = float(
                null[d, frequency_y, frequency_x]
                if frequency_x <= nx
                else null[d, (-frequency_y) % (2 * ny), 2 * nx - frequency_x]
            )
            separated = (
                (-1) ** d
                / 8
                * (
                    (1 + 3 * d) * (-1) ** frequency_y * (-1) ** frequency_x
                    + 2 * ly * (-1) ** frequency_y * (-1) ** frequency_x
                    + kx * (-1) ** frequency_y * (-1) ** frequency_x
                )
            )
            assert value == separated
        # Exact inverse support is y=Ny OR x=Nx, disjoint from ALL required lags.
        assert all(
            y % (2 * ny) != ny and x % (2 * nx) != nx
            for y, x in product(range(-ny + 1, ny), range(-nx + 1, nx))
        )
        print("null shape", shape, "exact finite H/B/G/operator = 0; dyadic support proof passed")

    shape = (3, 2, 4)
    kernel = signed_kernel(shape)
    base = operator_matrix(kernel, shape, spacing, carrier, phases, amplitudes, 0.48, 1.33)
    cr, cc = row_column_norms(pixel_matrix(kernel, shape, spacing, absolute=True))
    lbound = light_bound(amplitudes)
    x = ((np.arange(24) % 11 - 5) / 3).astype(np.float32).reshape(shape)
    y = ((np.arange(18) % 11 - 5) / 3).astype(np.float32).reshape((3, 3, 1, 2))
    for label, q, phi, beams in [
        ("signed carrier", -carrier, phases, amplitudes),
        ("source-minus-focus / unequal sides", carrier, phases, (0.7, 0.25, 1.2)),
        ("phase sign", carrier, -phases, amplitudes),
        ("continuous carrier versus zero-bin rounding", np.zeros(2), phases, amplitudes),
        (
            "half-cell anchor",
            carrier,
            phases - math.pi * math.fsum((carrier[0] * spacing[1], carrier[1] * spacing[2])),
            amplitudes,
        ),
    ]:
        alternative = operator_matrix(kernel, shape, spacing, q, phi, beams, 0.48, 1.33)
        forward_gap = float(np.max(np.abs(apply_reference(base - alternative, x))))
        adjoint_gap = float(np.max(np.abs(apply_reference(base - alternative, y, transpose=True))))
        fscale = lbound * cr * float(np.max(np.abs(x)))
        jscale = len(phases) * lbound * cc * float(np.max(np.abs(y)))
        assert forward_gap > 4e-4 * fscale and adjoint_gap > 4e-4 * jscale
        print(
            label,
            "forward / adjoint gap divided by scale",
            forward_gap / fscale,
            adjoint_gap / jscale,
        )
    # Normalized uint64 phase target has an independently specified original-value alternative.
    integer = 2**63 + 1
    normalized = 1 + reduced_cis(decimal(integer)).real
    original = 1 + reduced_cis(Decimal(integer)).real
    assert abs(normalized - 1.0118000765128001) < 5e-16
    assert abs(original - 0.16496320975055412) < 5e-16
    assert abs(normalized - original) > 0.8
    print("uint64 phase normalized/original illumination", normalized, original)
    print("corrected signed/null reference and positive sensitivity controls passed")


def validate_padding_oracles() -> None:
    """Qualify free-padding alternatives, canonical roots and finite observer domains."""
    with localcontext() as context:
        context.prec = 800

        def atan_inverse(inverse: int, count: int) -> Decimal:
            x = Decimal(1) / inverse
            return sum(
                ((-1) ** k * x ** (2 * k + 1) / (2 * k + 1) for k in range(count)),
                Decimal(0),
            )

        # Machin's identity; first omitted alternating terms are <1e-790.
        independent_pi = 16 * atan_inverse(5, 570) - 4 * atan_inverse(239, 170)
        assert abs(reference_pi() - independent_pi) < Decimal("1e-750")
    for order in (1, 2, 3, 5, 37):
        rule = canonical_rule(order)
        print("canonical Q", order, "isolated roots", len(rule), "moments", 2 * order)
    for shape in ((2, 2, 2), (3, 2, 4), (2, 4, 2)):
        # This tests the OBSERVER, imposing no success demand on a product
        # algorithm with a concrete precision obstruction on this extreme input.
        # Exact unused-lag terms span 80 decimal orders above the finite target.
        payload = padding_only_spectra(shape, math.ldexp(1.0, 120))
        payload[:, 0, 0] = math.ldexp(1.0, -140)
        recovered = kernel_from_spectra(payload, shape)
        target = math.ldexp(1.0, -140) / (4 * shape[1] * shape[2])
        required = [
            recovered[d, y % (2 * shape[1]), x % (2 * shape[2])]
            for d, y, x in product(
                range(shape[0]), range(-shape[1] + 1, shape[1]), range(-shape[2] + 1, shape[2])
            )
        ]
        assert all(value == target for value in required)
        print("exact cancellation observer", shape, "required value", target)

    spacing = (0.375, 0.125, 0.25)
    positives = [((3, 2, 4), math.ldexp(1.0, exponent)) for exponent in (-64, -68, -71)]
    positives += [
        ((2, 2, 2), math.sqrt(quanta / math.pi) * math.ldexp(1.0, -74) * math.sqrt(0.5))
        for quanta in (1500.49, 402.123, 300.49)
    ]
    delta = math.ldexp(1.0, -149)
    for shape, na in positives:
        physical = physical_kernel(shape, spacing, 1.0, 1.0, na, 1) / delta
        with localcontext() as context:
            context.prec = 110
            dc = float(4 * shape[1] * shape[2] * reference_pi() * decimal(na) ** 2)
        witness = np.zeros((shape[0], 2 * shape[1], shape[2] + 1), dtype=np.float32)
        witness[:, 0, 0] = dc
        represented = kernel_from_spectra(witness.astype(np.float64) / delta, shape)
        errors = row_column_norms(
            pixel_matrix(represented - physical, shape, spacing, absolute=True)
        )
        norms = row_column_norms(pixel_matrix(physical, shape, spacing))
        ratios = tuple(error / norm for error, norm in zip(errors, norms, strict=True))
        assert max(ratios) < 1e-4 - 5e-13
        # These witnesses are spatially constant, including nonzero unused lines.
        assert np.all(represented > 0)
        print("faithful free-padding DC witness", shape, na.hex(), "E row/column over B", ratios)
    print("padding oracle qualification passed; witnesses prescribe no builder strategy")
