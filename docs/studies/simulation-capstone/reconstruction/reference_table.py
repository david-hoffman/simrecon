"""Regenerate the frozen design-r6 independent noisy calibration table."""

import sys
from pathlib import Path

import numpy as np

# The study runner is invoked as a script from reconstruction/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inputs.optics import BACKGROUND, BEAD_ANGLE, BEAD_K, BEAD_RADIUS, BXY, DZ, PHASES


def _signed_bins(size: int) -> np.ndarray:
    """Keep the positive Nyquist index used in the independent phase shift."""
    bins = np.arange(size)
    return np.where(bins <= size // 2, bins, bins - size)


def _edge_bead(raw: np.ndarray) -> np.ndarray:
    """Apply the ten-pixel edge correction in y, then x, on a binary64 copy."""
    result = np.asarray(raw, dtype=np.float64).copy()
    weight = 1 - np.sin(np.pi * (np.arange(10) + 0.5) / 20)
    dy = (result[..., -1, :] - result[..., 0, :]) / 2
    result[..., :10, :] += weight[:, None] * dy[..., None, :]
    result[..., -10:, :] -= weight[::-1, None] * dy[..., None, :]
    dx = (result[..., -1] - result[..., 0]) / 2
    result[..., :10] += weight * dx[..., None]
    result[..., -10:] -= weight[::-1] * dx[..., None]
    return result


def calibration_table(raw: np.ndarray) -> np.ndarray:
    """Apply the accepted independent recipe to the public calibration in counts."""
    phases, nz, n, nx = raw.shape
    assert phases == 5 and n == nx and n >= 20
    edge = _edge_bead(raw)
    image = edge.mean(axis=0)
    position = np.array(np.unravel_index(np.argmax(image), image.shape))
    peak = image[tuple(position)]
    center = position.astype(float)
    for axis, size in enumerate(image.shape):
        left, right = position.copy(), position.copy()
        left[axis], right[axis] = (position[axis] - 1) % size, (position[axis] + 1) % size
        a, b = image[tuple(left)], image[tuple(right)]
        curvature = a + b - 2 * peak
        assert curvature < 0
        center[axis] += (a - b) / (2 * curvature)
    assert center[1] != 20 and 0 <= np.floor(center[0]) < nz

    corrected = edge - BACKGROUND
    quadratures = np.stack(
        [corrected.mean(axis=0)]
        + [
            np.tensordot(function(order * PHASES) / 5, corrected, axes=1)
            for order in (1, 2)
            for function in (np.cos, np.sin)
        ]
    )
    spectrum = np.fft.rfftn(quadratures, axes=(1, 2, 3))
    ix = np.arange(n // 2 + 1)
    iy, iz = _signed_bins(n), _signed_bins(nz)
    phase = center[2] * ix / n + center[1] * iy[:, None] / n + center[0] * iz[:, None, None] / nz
    spectrum *= np.exp(2j * np.pi * phase)

    # Pitches and sphere radius are in micrometres. Frequencies are cycles per micrometre.
    dkr, dkz = 1 / (BXY * n), 1 / (DZ * nz)
    radial_bin = np.rint(np.hypot(ix, iy[:, None])).astype(int)
    keep = radial_bin <= n // 2
    bins = radial_bin[keep]
    counts = np.bincount(bins)
    radial_rows = []
    for slot, values in enumerate(spectrum):
        order = (slot + 1) // 2
        cx, cy = order * BEAD_K * np.array([np.cos(BEAD_ANGLE), np.sin(BEAD_ANGLE)])
        rho2 = (ix * dkr + cx) ** 2 + (iy[:, None] * dkr + cy) ** 2 + (iz[:, None, None] * dkz) ** 2
        u = 2 * np.pi * BEAD_RADIUS * np.sqrt(rho2)
        form = np.ones_like(u)
        nonzero = u > 0
        v = u[nonzero]
        form[nonzero] = 3 * (np.sin(v) - v * np.cos(v)) / v**3
        assert np.min(form) > 0.04, "sphere conditioning floor"
        planes = (values / form)[:, keep]
        row = np.stack(
            [
                np.bincount(bins, weights=z.real) + 1j * np.bincount(bins, weights=z.imag)
                for z in planes
            ],
            axis=1,
        )
        row /= counts[:, None]
        row = (row + np.conj(row[:, (-np.arange(nz)) % nz])) / 2
        radial_rows.append(row)

    radial = np.stack(radial_rows)
    scale = np.max(np.abs(radial[0]))
    assert scale > 0
    radial /= scale
    samples = [radial[0]]
    for order in (1, 2):
        c, s = radial[2 * order - 1 : 2 * order + 1]
        c0, s0 = c[n // 8, 0].real, s[n // 8, 0].real
        angle = np.arctan(np.sum(np.abs(s)) / np.sum(np.abs(c)))
        if c0 < 0 and s0 > 0:
            angle += np.pi
        elif c0 < 0 and s0 < 0:
            angle = np.pi - angle
        elif c0 > 0 and s0 > 0:
            angle = -angle
        samples.append(c * np.cos(angle) - s * np.sin(angle))
    return np.stack(samples)
