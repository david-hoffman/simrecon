"""Independent finite-model and exact represented-phasor references for blind A."""

import math
from decimal import Decimal, localcontext
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

EPS = 2.0**-52
CIRCULAR_BUDGET = 512 * EPS


def indexed_images(images: NDArray, displacements: NDArray) -> NDArray[np.float64]:
    """Literal public index equation; no roll or transform-based reference."""
    n, ny, nx = images.shape
    result = np.empty((n, ny, nx), dtype=np.float64)
    for p in range(n):
        dy, dx = (int(v) for v in displacements[p])
        for y in range(ny):
            for x in range(nx):
                result[p, y, x] = float(images[p, (y + dy) % ny, (x + dx) % nx])
    return result


def represented_phasors(
    phases: NDArray, carrier: NDArray, shifts: NDArray, shape: tuple[int, int]
) -> NDArray[np.complex128]:
    """Exact rational rounding, then high-precision real product/normalization.

    Decimal receives exact represented NumPy sin/cos values. Its 90 digits make
    observer rounding negligible beside the contract's 512*2**-52 budget.
    """
    return np.array(
        [
            complex(float(real), float(imag))
            for real, imag in decimal_phasors(phases, carrier, shifts, shape)
        ],
        dtype=np.complex128,
    )


def decimal_phasors(
    phases: NDArray, carrier: NDArray, shifts: NDArray, shape: tuple[int, int]
) -> list[tuple[Decimal, Decimal]]:
    ny, nx = shape
    ky, kx = (int(v) for v in carrier)
    result = []
    with localcontext() as ctx:
        ctx.prec = 90
        for phi, shift in zip(phases.astype(np.float64), shifts, strict=True):
            dy, dx = (int(v) for v in shift)
            cycles = Fraction(ky * dy, ny) + Fraction(kx * dx, nx)
            cycles -= math.floor(cycles)
            alpha = np.float64((2 * np.pi) * float(cycles))
            a, b, c, d = (
                Decimal.from_float(float(v))
                for v in (np.cos(phi), np.sin(phi), np.cos(alpha), np.sin(alpha))
            )
            real, imag = a * c - b * d, a * d + b * c
            length = (real * real + imag * imag).sqrt()
            result.append((real / length, imag / length))
    return result


def circular_errors(
    returned: NDArray,
    phases: NDArray,
    carrier: NDArray,
    shifts: NDArray,
    shape: tuple[int, int],
) -> list[Decimal]:
    """Keep the target and distance in Decimal, avoiding a float oracle margin."""
    target = decimal_phasors(phases, carrier, shifts, shape)
    errors = []
    with localcontext() as ctx:
        ctx.prec = 90
        for angle, (real, imag) in zip(returned, target, strict=True):
            dr = Decimal.from_float(float(np.cos(angle))) - real
            di = Decimal.from_float(float(np.sin(angle))) - imag
            errors.append((dr * dr + di * di).sqrt())
    return errors


def phasors(phases: NDArray) -> NDArray[np.complex128]:
    return np.cos(phases) + 1j * np.sin(phases)


def specimen(y: float, x: float, ny: int, nx: int) -> float:
    """Low-mode real object, also defined on the doubled synthesis grid."""
    return (
        2.0
        + 0.3 * math.cos(2 * math.pi * y / ny)
        + 0.2 * math.sin(2 * math.pi * x / nx)
        + 0.1 * math.cos(2 * math.pi * (y / ny + x / nx))
    )


def kernel(shape: tuple[int, int]) -> NDArray[np.float64]:
    """Asymmetric, unit-mass kernel with index-zero origin."""
    ny, nx = shape
    h = np.zeros((ny, nx))
    h[0, 0] += 4 / 8
    h[1 % ny, 0] += 1 / 8
    h[0, 1 % nx] += 3 / 8
    return h


def convolve(values: NDArray, h: NDArray) -> NDArray:
    """Finite circular sum, independent of FFTs and production solvers."""
    ny, nx = values.shape
    result = np.empty((ny, nx), dtype=values.dtype)
    for y in range(ny):
        for x in range(nx):
            terms = [
                h[v, u] * values[(y - v) % ny, (x - u) % nx] for v in range(ny) for u in range(nx)
            ]
            if np.iscomplexobj(values):
                result[y, x] = complex(
                    math.fsum(float(t.real) for t in terms),
                    math.fsum(float(t.imag) for t in terms),
                )
            else:
                result[y, x] = math.fsum(float(t) for t in terms)
    return result


def acquire(
    shape: tuple[int, int],
    phases: NDArray,
    carrier: NDArray,
    shifts: NDArray,
    *,
    brightness: float = 1.25,
    modulation: float = 0.6,
) -> NDArray[np.float64]:
    """Translate specimen before multiplying stationary illumination."""
    ny, nx = shape
    ky, kx = (int(v) for v in carrier)
    h = kernel(shape)
    frames = []
    for phi, shift in zip(phases, shifts, strict=True):
        dy, dx = (int(v) for v in shift)
        illuminated = np.empty(shape)
        for y in range(ny):
            for x in range(nx):
                moving = specimen((y - dy) % ny, (x - dx) % nx, ny, nx)
                illumination = brightness * (
                    1
                    + modulation * math.cos(2 * math.pi * (ky * y / ny + kx * x / nx) + float(phi))
                )
                illuminated[y, x] = moving * illumination
        frames.append(convolve(illuminated, h))
    return np.array(frames)


def expected_components(
    shape: tuple[int, int], carrier: NDArray, brightness: float, modulation: float
) -> tuple[NDArray, NDArray]:
    ny, nx = shape
    ky, kx = (int(v) for v in carrier)
    obj = np.array([[specimen(y, x, ny, nx) for x in range(nx)] for y in range(ny)])
    harmonic = np.array(
        [
            [
                obj[y, x]
                * complex(
                    math.cos(2 * math.pi * (ky * y / ny + kx * x / nx)),
                    math.sin(2 * math.pi * (ky * y / ny + kx * x / nx)),
                )
                for x in range(nx)
            ]
            for y in range(ny)
        ]
    )
    h = kernel(shape)
    return brightness * convolve(obj, h), brightness * modulation / 2 * convolve(harmonic, h)


def doubled_truth(shape: tuple[int, int]) -> tuple[NDArray, NDArray]:
    ny, nx = shape
    image = np.array(
        [[specimen(y / 2, x / 2, ny, nx) for x in range(2 * nx)] for y in range(2 * ny)]
    )
    spectrum = np.zeros((2 * ny, 2 * nx), dtype=np.complex128)
    spectrum[ny, nx] = 2
    spectrum[ny - 1, nx] = spectrum[ny + 1, nx] = 0.15
    spectrum[ny, nx - 1], spectrum[ny, nx + 1] = 0.1j, -0.1j
    spectrum[ny - 1, nx - 1] = spectrum[ny + 1, nx + 1] = 0.05
    return image, spectrum
