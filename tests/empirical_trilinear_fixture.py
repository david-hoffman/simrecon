"""Independent exact geometry and high-precision observers for the public contract.

No product interpolation, transform or phase output is used by these oracles.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

PRECISION = 800
EPS = Fraction(1, 2**52)
QUANTUM = Fraction(1, 2**1074)
FMAX = Fraction.from_float(float(np.finfo(np.float64).max))
FREQUENCY_FIELDS = ("fz_per_um", "fy_per_um", "fx_per_um")


def rational(value: Any) -> Fraction:
    """Interpret a converted binary64 component exactly."""
    return Fraction.from_float(float(value))


def decimal(value: Fraction | int) -> Decimal:
    value = Fraction(value)
    return Decimal(value.numerator) / Decimal(value.denominator)


def modes(size: int) -> range:
    return range(-(size // 2), (size + 1) // 2)


def coordinates(size: int, spacing: Any) -> list[Fraction]:
    return [Fraction(k, size) / rational(spacing) for k in modes(size)]


def frequency_arrays(shape: tuple[int, ...], spacing: Any) -> tuple[NDArray[np.float64], ...]:
    return tuple(
        np.array([float(f) for f in coordinates(n, d)], dtype=np.float64)
        for n, d in zip(shape, spacing, strict=True)
    )


@lru_cache(maxsize=1)
def pi() -> Decimal:
    """Machin identity: pi = 16 atan(1/5) - 4 atan(1/239)."""
    with localcontext() as context:
        context.prec = PRECISION + 30

        def atan_inverse(n: int) -> Decimal:
            x = Decimal(1) / Decimal(n)
            term = x
            result = term
            k = 1
            while True:
                term *= -(x * x)
                updated = result + term / Decimal(2 * k + 1)
                if updated == result:
                    return result
                result = updated
                k += 1

        return 16 * atan_inverse(5) - 4 * atan_inverse(239)


@lru_cache(maxsize=4096)
def phasor(cycles: Fraction = Fraction(0), angle: float = 0.0) -> tuple[Decimal, Decimal]:
    """Return exp(i*(2*pi*cycles+angle)), reducing before Taylor summation."""
    with localcontext() as context:
        context.prec = PRECISION
        period = 2 * pi()
        x = (period * decimal(cycles % 1) + Decimal.from_float(angle)) % period
        if x > pi():
            x -= period
        if x < -pi():
            x += period
        sine_term = x
        cosine_term = Decimal(1)
        sine = sine_term
        cosine = cosine_term
        k = 1
        while True:
            sine_term *= -(x * x) / Decimal((2 * k) * (2 * k + 1))
            cosine_term *= -(x * x) / Decimal((2 * k - 1) * (2 * k))
            next_sine = sine + sine_term
            next_cosine = cosine + cosine_term
            if (next_sine, next_cosine) == (sine, cosine):
                return +cosine, +sine
            sine, cosine = next_sine, next_cosine
            k += 1


def multiply(
    left: tuple[Decimal, Decimal], right: tuple[Decimal, Decimal]
) -> tuple[Decimal, Decimal]:
    a, b = left
    c, d = right
    return a * c - b * d, a * d + b * c


def stencil(nodes: list[Fraction], point: Fraction) -> list[tuple[int, Fraction]]:
    if point in nodes:
        return [(nodes.index(point), Fraction(1))]
    for i in range(len(nodes) - 1):
        if nodes[i] < point < nodes[i + 1]:
            t = (point - nodes[i]) / (nodes[i + 1] - nodes[i])
            return [(i, 1 - t), (i + 1, t)]
    raise ValueError("observer point outside the closed source hull")


def oracle(
    response: Any, kwargs: dict[str, Any]
) -> dict[tuple[int, int, int, int], tuple[Decimal, Decimal, Decimal]]:
    """Map output index to exact-stored-input (real, imaginary, Delta)."""
    shape = tuple(int(n) for n in response.values.shape[1:])
    target = tuple(int(n) for n in kwargs["target_shape_zyx"])
    source_axes = [coordinates(n, d) for n, d in zip(shape, response.voxel_size_um, strict=True)]
    target_axes = [
        coordinates(n, d) for n, d in zip(target, kwargs["target_voxel_size_um"], strict=True)
    ]
    carriers = kwargs["calibration_carrier_bins"]
    offsets = kwargs["coordinate_offset_yx"]
    rho = sum(
        (
            Fraction(int(k) * (int(b) + int(o)), n)
            for k, b, o, n in zip(
                carriers, response.origin_zyx[1:], offsets, shape[1:], strict=True
            )
        ),
        Fraction(0),
    )
    result: dict[tuple[int, int, int, int], tuple[Decimal, Decimal, Decimal]] = {}
    with localcontext() as context:
        context.prec = PRECISION
        fundamental = phasor(-rho, -float(kwargs["phase_reference_shift_rad"]))
        rotations = [(Decimal(1), Decimal(0)), fundamental, multiply(fundamental, fundamental)]
        for index in product(*(range(n) for n in target)):
            axis_stencils = [
                stencil(nodes, targets[i])
                for nodes, targets, i in zip(source_axes, target_axes, index, strict=True)
            ]
            for order in range(3):
                real = Fraction(0)
                imag = Fraction(0)
                mass = Fraction(0)
                for vertices in product(*axis_stencils):
                    source_index = tuple(v[0] for v in vertices)
                    weight = vertices[0][1] * vertices[1][1] * vertices[2][1]
                    sample = response.values[(order, *source_index)]
                    re, im = rational(sample.real), rational(sample.imag)
                    real += weight * re
                    imag += weight * im
                    mass += weight * (abs(re) + abs(im))
                re_out, im_out = multiply((decimal(real), decimal(imag)), rotations[order])
                allowance = decimal(1024 * EPS * mass + 64 * QUANTUM)
                result[(order, index[0], index[1], index[2])] = re_out, im_out, allowance
    return result


def assert_budget(values: Any, expected: Any, *, sufficient: bool = True) -> None:
    with localcontext() as context:
        context.prec = PRECISION
        for index, (real, imag, allowance) in expected.items():
            if sufficient:
                assert abs(real) + allowance < decimal(FMAX)
                assert abs(imag) + allowance < decimal(FMAX)
            got = values[index]
            assert np.isfinite(got.real) and np.isfinite(got.imag)
            dr = Decimal.from_float(float(got.real)) - real
            di = Decimal.from_float(float(got.imag)) - imag
            assert dr * dr + di * di <= allowance * allowance, (index, "contract budget")


def asymmetric_values(shape: tuple[int, ...]) -> NDArray[np.complex128]:
    values = np.empty((3, *shape), dtype=np.complex128)
    for m, z, y, x in np.ndindex(values.shape):
        values[m, z, y, x] = complex(
            (-1) ** (m + y) * (3 + 2 * z + 5 * y + x + z * y * x) / 16,
            (m + 1) * (2 - 3 * z + y - 2 * x + z * x) / 32,
        )
    return values


def affine_value(order: int, z: Fraction, y: Fraction, x: Fraction) -> complex:
    real = (order + 1) * (1 + z + 2 * y - 3 * x + z * y - 2 * y * x + z * y * x)
    imag = (order - 1) + 2 * z - y + x + z * x + 3 * z * y * x
    return complex(float(real / 8), float(imag / 16))


def sampled_affine(shape: tuple[int, int, int], spacing: Any) -> NDArray[np.complex128]:
    axes = [coordinates(n, d) for n, d in zip(shape, spacing, strict=True)]
    values = np.empty((3, *shape), dtype=np.complex128)
    for m, z, y, x in np.ndindex(values.shape):
        values[m, z, y, x] = affine_value(m, axes[0][z], axes[1][y], axes[2][x])
    return values


def direct_dft(values: Any, *, inverse: bool = False) -> NDArray[np.complex128]:
    """Finite sum with high-precision rational roots; no FFT dependency."""
    shape = values.shape
    result = np.empty(shape, dtype=np.complex128)
    with localcontext() as context:
        context.prec = PRECISION
        for out_index in np.ndindex(shape):
            total = (Decimal(0), Decimal(0))
            for in_index in np.ndindex(shape):
                if inverse:
                    cycles = sum(
                        (
                            Fraction(k - n // 2, n) * j
                            for k, j, n in zip(in_index, out_index, shape, strict=True)
                        ),
                        Fraction(0),
                    )
                else:
                    cycles = -sum(
                        (
                            Fraction(k - n // 2, n) * j
                            for k, j, n in zip(out_index, in_index, shape, strict=True)
                        ),
                        Fraction(0),
                    )
                sample = values[in_index]
                term = multiply(
                    (
                        Decimal.from_float(float(sample.real)),
                        Decimal.from_float(float(sample.imag)),
                    ),
                    phasor(cycles),
                )
                total = total[0] + term[0], total[1] + term[1]
            result[out_index] = complex(float(total[0]), float(total[1]))
    return result


def smooth_transfer(point: tuple[Fraction, ...], order: int, phase: float = 0.0) -> complex:
    """Evaluate the declared three-site kernel's continuous Fourier polynomial.

    Displacements are (0,0,0), (0,1,0), (0,0,1) micrometres with
    masses 3/4,1/8,1/8. g0=1, g1=(2+i)/16, g2=(-1+2i)/32.
    This comparison is selected for this demonstration, not inferred optics.
    """
    with localcontext() as context:
        context.prec = PRECISION
        y = phasor(-point[1])
        x = phasor(-point[2])
        h = (Decimal(3) / 4 + (y[0] + x[0]) / 8, (y[1] + x[1]) / 8)
        g = [
            (Decimal(1), Decimal(0)),
            (Decimal(2) / 16, Decimal(1) / 16),
            (-Decimal(1) / 32, Decimal(2) / 32),
        ][order]
        value = multiply(h, g)
        fundamental = phasor(angle=-phase)
        rotation = [(Decimal(1), Decimal(0)), fundamental, multiply(fundamental, fundamental)][
            order
        ]
        value = multiply(value, rotation)
        return complex(float(value[0]), float(value[1]))


def smooth_samples(
    shape: tuple[int, int, int], spacing: Any, phase: float = 0.0
) -> NDArray[np.complex128]:
    axes = [coordinates(n, d) for n, d in zip(shape, spacing, strict=True)]
    values = np.empty((3, *shape), dtype=np.complex128)
    for m, z, y, x in np.ndindex(values.shape):
        values[m, z, y, x] = smooth_transfer((axes[0][z], axes[1][y], axes[2][x]), m, phase)
    return values


def phase_images(bands: Any, phases: Any) -> NDArray[np.float64]:
    """Forward observations use the prerequisite's represented phase columns."""
    c = np.cos(phases)
    s = np.sin(phases)
    c2 = c * c - s * s
    s2 = (2 * c) * s
    return np.array(
        [
            bands[0].real
            + 2 * bands[1].real * a
            - 2 * bands[1].imag * b
            + 2 * bands[2].real * d
            - 2 * bands[2].imag * e
            for a, b, d, e in zip(c, s, c2, s2, strict=True)
        ],
        dtype=np.float64,
    )


def specimen_example() -> dict[str, Any]:
    """Independent signed-window forward data and ideal interpolant estimator.

    Finite supported object modes are chosen so each side order relocates into
    the detector without aliasing. No production transfer/output enters this.
    """
    target = (1, 3, 3)
    spacing = (2.0, 2.5, 2.5)
    output = (1, 15, 3)
    alpha_s = 0.35
    gain = 1.5
    penalty = 0.25
    phases = np.array([-0.8, -0.1, 0.6, 1.5, 2.4, 3.2, 4.7, 5.5])
    truth = np.zeros(output, dtype=np.complex128)
    truth[0, 7, 1] = 1.0
    for ky, kx, coefficient in [(3, 1, 0.2 + 0.1j), (6, -1, -0.15 + 0.05j)]:
        truth[0, 7 + ky, 1 + kx] = coefficient
        truth[0, 7 - ky, 1 - kx] = coefficient.conjugate()
    physical = smooth_samples(target, spacing, alpha_s)
    measurements = np.zeros((3, *target), dtype=np.complex128)
    for m, z, y, x in np.ndindex(measurements.shape):
        ky, kx = y - 1 - 3 * m, x - 1
        if -7 <= ky <= 7:
            measurements[m, z, y, x] = gain * physical[m, z, y, x] * truth[0, 7 + ky, 1 + kx]
    bands = np.array([direct_dft(row, inverse=True) for row in measurements])
    assert np.max(abs(bands[0].imag)) < 1e-15
    images = phase_images(bands, phases)[None]
    return {
        "target": target,
        "spacing": spacing,
        "output": output,
        "alpha_s": alpha_s,
        "gain": gain,
        "penalty": penalty,
        "phases": phases,
        "truth": truth,
        "physical": physical,
        "measurements": measurements,
        "images": images,
    }


def signed_estimator(example: Any, transfers: Any) -> NDArray[np.complex128]:
    """Direct five-order ridge sum on generated coefficients, including negatives."""
    output = example["output"]
    numerator = np.zeros(output, dtype=np.complex128)
    denominator = np.zeros(output, dtype=np.float64)
    for m in range(-2, 3):
        for z, y, x in np.ndindex(example["target"]):
            ky, kx = y - 1 - 3 * m, x - 1
            if -7 <= ky <= 7:
                if m < 0:
                    opposite = (0, 2 - y, 2 - x)
                    e = transfers[(-m, *opposite)].conjugate()
                    d = example["measurements"][(-m, *opposite)].conjugate()
                else:
                    e = transfers[m, z, y, x]
                    d = example["measurements"][m, z, y, x]
                t = example["gain"] * e
                index = (0, 7 + ky, 1 + kx)
                numerator[index] += t.conjugate() * d
                denominator[index] += t.real * t.real + t.imag * t.imag
    return numerator / (denominator + example["penalty"])
