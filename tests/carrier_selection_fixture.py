"""Independent finite-sum, stored-input fixtures for CARRIER-SELECT-01.

No product numerical helpers supply expected values. Fraction arithmetic solves
only the tiny represented phase fit; explicit Fourier sums avoid the FFT backend.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np


@dataclass
class SelectionFixture:
    """Converted input arrays and independently specified transfer."""

    images: np.ndarray
    steps: np.ndarray
    transfer: np.ndarray
    spacing: tuple[float, float] = (0.7, 1.3)
    source: str = "  independent selector finite-sum fixture  "

    def calibration(self, public: Any) -> Any:
        ny, nx = self.transfer.shape
        record_type: Any = getattr(public, "Otf2D", None)
        return record_type(
            values=self.transfer.copy(),
            fy_per_um=np.arange(-(ny // 2), (ny + 1) // 2, dtype=float) / (ny * self.spacing[0]),
            fx_per_um=np.arange(-(nx // 2), (nx + 1) // 2, dtype=float) / (nx * self.spacing[1]),
            pixel_size_um=self.spacing,
            origin_yx=(0, 0),
            source=self.source,
        )


def modes(n: int) -> range:
    return range(-(n // 2), (n + 1) // 2)


def synthesize(spectrum: np.ndarray) -> np.ndarray:
    """Fourier SERIES synthesis: no inverse M factor."""
    ny, nx = spectrum.shape
    return np.array(
        [
            [
                sum(
                    spectrum[j, column] * cmath.exp(2j * math.pi * (ky * y / ny + kx * x / nx))
                    for j, ky in enumerate(modes(ny))
                    for column, kx in enumerate(modes(nx))
                )
                for x in range(nx)
            ]
            for y in range(ny)
        ],
        dtype=complex,
    )


def finite_dft(array: np.ndarray) -> np.ndarray:
    """Negative forward sign; divide by M to return series amplitudes."""
    ny, nx = array.shape
    return np.array(
        [
            [
                sum(
                    array[y, x] * cmath.exp(-2j * math.pi * (ky * y / ny + kx * x / nx))
                    for y in range(ny)
                    for x in range(nx)
                )
                / (ny * nx)
                for kx in modes(nx)
            ]
            for ky in modes(ny)
        ],
        dtype=complex,
    )


def landscape(*, off_model: bool = True, steps: np.ndarray | None = None) -> SelectionFixture:
    """Alias-free (0,+1) illumination, asymmetric real object and complex H.

    H is the unit-mass PSF with masses .5,.3,.2 at (0,0),(1,0),(0,1).
    Its nonzero phase and unequal y/x terms distinguish magnitude-only fits.
    """
    ny, nx = 5, 7
    transfer = np.array(
        [
            [
                0.5
                + 0.3 * cmath.exp(-2j * math.pi * ky / ny)
                + 0.2 * cmath.exp(-2j * math.pi * kx / nx)
                for kx in modes(nx)
            ]
            for ky in modes(ny)
        ],
        dtype=complex,
    )
    object_modes = {(0, 0): 2 + 0j}
    for key, value in [((0, 1), 0.3 + 0.1j), ((1, 0), 0.2 - 0.05j), ((1, 1), 0.12 + 0.07j)]:
        object_modes[key] = value
        object_modes[-key[0], -key[1]] = value.conjugate()
    gain = 0.4 * cmath.exp(0.63j)
    d0 = np.zeros((ny, nx), dtype=complex)
    plus = np.zeros_like(d0)
    for j, ky in enumerate(modes(ny)):
        for column, kx in enumerate(modes(nx)):
            d0[j, column] = transfer[j, column] * object_modes.get((ky, kx), 0j)
            plus[j, column] = gain * transfer[j, column] * object_modes.get((ky, kx - 1), 0j)
    if off_model:
        plus[1, 1] += 0.035 - 0.021j
        plus[3, 4] += -0.025 + 0.017j
    dc = np.real(synthesize(d0))
    c1 = synthesize(plus)
    if steps is None:
        steps = np.array([-0.4, 0.7, 1.9, 3.4, 5.2])
    images = np.array([dc + 2 * (np.real(c1) * np.cos(p) - np.imag(c1) * np.sin(p)) for p in steps])
    return SelectionFixture(images, steps.copy(), transfer)


def sparse_landscape(*, modulation: float = 2.4) -> SelectionFixture:
    """One informative frequency pair despite many geometric pairs.

    Delta OTF and DC-only object, shifted plus mode at +1. Multiple candidate
    overlaps can fit or fail; geometric counts are not informative support.
    """
    steps = np.array([0.0, 0.8, 2.2, 3.7, 5.5])
    dc = np.full((1, 5), 2.0)
    c1 = modulation * np.exp(0.4j + 2j * np.pi * np.arange(5) / 5)[None, :]
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in steps])
    return SelectionFixture(images, steps, np.ones((1, 5), dtype=complex))


def represented_components(fixture: SelectionFixture) -> tuple[np.ndarray, np.ndarray]:
    """Exact rational least squares of represented sin/cos and stored images.

    Normal equations are an ORACLE in exact arithmetic, not a float solver.
    Gauss-Jordan elimination has no rounding until final float conversion.
    """
    h = [
        [Fraction(1), Fraction(float(np.cos(p))), Fraction(float(np.sin(p)))] for p in fixture.steps
    ]
    gram: list[list[Fraction]] = [
        [sum((row[i] * row[j] for row in h), Fraction(0)) for j in range(3)] for i in range(3)
    ]
    inverse: list[list[Fraction]] = [
        row[:] + [Fraction(int(i == j)) for j in range(3)] for i, row in enumerate(gram)
    ]
    for i in range(3):
        pivot = inverse[i][i]
        assert pivot != 0
        inverse[i] = [v / pivot for v in inverse[i]]
        for j in range(3):
            if j != i:
                factor = inverse[j][i]
                inverse[j] = [a - factor * b for a, b in zip(inverse[j], inverse[i], strict=True)]
    ny, nx = fixture.images.shape[1:]
    dc = np.empty((ny, nx))
    c1 = np.empty((ny, nx), dtype=complex)
    for y in range(ny):
        for x in range(nx):
            b = [Fraction(float(value)) for value in fixture.images[:, y, x]]
            rhs = [sum(row[j] * value for row, value in zip(h, b, strict=True)) for j in range(3)]
            solution = [sum(inverse[i][j + 3] * rhs[j] for j in range(3)) for i in range(3)]
            dc[y, x] = float(solution[0])
            c1[y, x] = complex(float(solution[1] / 2), -float(solution[2] / 2))
    return dc, c1


@dataclass(frozen=True)
class FitTruth:
    """Independent stored-input fit plus conditioning evidence."""

    gain: complex
    residual: float
    count: int
    norm_x: float
    norm_y: float
    correlation: float


def expected_fit(fixture: SelectionFixture, carrier: tuple[int, int]) -> FitTruth:
    dc, c1 = represented_components(fixture)
    d0, plus = finite_dft(dc), finite_dft(c1)
    ny, nx = dc.shape
    ky, kx = carrier
    pairs = [
        (
            fixture.transfer[j + ky, column + kx] * d0[j, column],
            fixture.transfer[j, column] * plus[j + ky, column + kx],
        )
        for j in range(ny)
        for column in range(nx)
        if 0 <= j + ky < ny and 0 <= column + kx < nx
    ]
    assert pairs
    x = [pair[0] for pair in pairs]
    y = [pair[1] for pair in pairs]
    xx = math.fsum(abs(v) ** 2 for v in x)
    yy = math.fsum(abs(v) ** 2 for v in y)
    cross = sum(a.conjugate() * b for a, b in pairs)
    gain = cross / xx
    residual = math.sqrt(math.fsum(abs(b - gain * a) ** 2 for a, b in pairs) / yy)
    return FitTruth(
        gain, residual, len(pairs), math.sqrt(xx), math.sqrt(yy), abs(cross) / math.sqrt(xx * yy)
    )
