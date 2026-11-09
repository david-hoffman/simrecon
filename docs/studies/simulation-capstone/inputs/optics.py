"""Frozen scalar pupil, exposure synthesis and detector camera."""

import math

import numpy as np
from numpy.polynomial.legendre import leggauss

N, Z = 128, 32  # Detector X/Y and Z samples.
NA, INDEX, EM, EX = 1.40, 1.515, 0.525, 0.488
R = 2 * NA / EM
DZ, XY, BXY = 0.125, 0.080, 0.090
PHASES = 2 * np.pi * np.arange(5) / 5
NOMINAL = np.deg2rad([0, 60, 120])
ANGLES = np.deg2rad([4, 56, 124])
MAGNITUDES = np.array([2.493, 2.389, 2.510])
CARRIERS = MAGNITUDES[:, None] * np.stack((np.cos(ANGLES), np.sin(ANGLES)), axis=1)
PHASE_ORIGINS = np.array([0.37, -0.52, 0.81])
OUTER = np.array([0.94, 1.02, 0.88])
CENTER = np.array([0.83, 0.76, 0.93])
BEAD_K, BEAD_ANGLE, BEAD_PHASE = 1.20 / EX, np.deg2rad(11), 0.43
BEAD_OUTER, BEAD_CENTER, BEAD_RADIUS = 1.0, 0.85, 0.050
BACKGROUND, ADU_PER_E, READ, MAX_CODE = 512, 4.0, 1.4, 2**20 - 1
DARK_E = 6.0
E_PER_SU, BEAD_E_UM = 30_000.0, 3_700.0
BASE = (2, 640, 0.025, 28, 16)  # padding, radial intervals, s step, pupil rule, source rule


def axis(n, spacing):
    """Return evenly spaced samples centered on index n // 2."""
    return (np.arange(n) - n // 2) * spacing


def axial_shift(k):
    """Return the illumination axial frequency difference."""
    return INDEX / EX - np.sqrt((INDEX / EX) ** 2 - k**2)


def coefficients(s, k, outer, center):
    """Return normalized real intensity coefficients for +m and -m."""
    denominator = 2 * outer**2 + center**2
    return (
        np.ones_like(s),
        2 * outer * center / denominator * np.cos(2 * np.pi * axial_shift(k) * s),
        np.full_like(s, outer**2 / denominator),
    )


def pupil_otf(radius, displacement, count):
    """Lateral transform of plane-normalized |pupil amplitude|² at defocus s."""
    radius = np.asarray(radius)
    displacement = np.asarray(displacement)
    assert np.all((radius >= 0) & (radius <= R))
    a = R / 2
    f = INDEX / EM
    nodes, weights = leggauss(count)
    t, w = (nodes + 1) / 2, weights / 2
    length = a - radius[:, None, None] / 2
    x = length * (1 - t[None, :, None] ** 2)
    jacobian = 2 * length * t[None, :, None]
    ymax = np.sqrt(np.maximum(0, a * a - (x + radius[:, None, None] / 2) ** 2))
    y = ymax * t[None, None, :]
    wp = np.sqrt(f * f - (x + radius[:, None, None] / 2) ** 2 - y * y)
    wm = np.sqrt(f * f - (x - radius[:, None, None] / 2) ** 2 - y * y)
    weight = (4 / (np.pi * a * a)) * jacobian * ymax * w[None, :, None] * w[None, None, :]
    delta = (wp - wm).reshape(len(radius), -1)
    weight = weight.reshape(len(radius), -1)
    return np.stack([np.sum(weight * np.cos(2 * np.pi * s * delta), axis=1) for s in displacement])


class Pupil:
    """Tabulate the scalar pupil transfer in radius and defocus."""

    def __init__(self, radial, ds, count):
        self.radius = np.linspace(0, R, radial + 1)
        self.s = np.arange(math.ceil(5.5 / ds) + 1) * ds
        self.table = pupil_otf(self.radius, self.s, count)
        self.ds = ds

    def at_s(self, displacement):
        """Interpolate the transfer between defocus samples."""
        u = np.abs(displacement) / self.ds
        i = np.floor(u).astype(int)
        assert i.max() + 1 < len(self.s), "defocus table overflow"
        t = (u - i)[..., None]
        return (1 - t) * self.table[i] + t * self.table[i + 1]


def gaussian(qx, qy, cx, cy, sx, sy, angle):
    """Evaluate the analytic lateral transform of one Gaussian."""
    c, s = np.cos(angle), np.sin(angle)
    u, v = c * qx + s * qy, -s * qx + c * qy
    return (
        2
        * np.pi
        * sx
        * sy
        * np.exp(-2 * np.pi**2 * ((sx * u) ** 2 + (sy * v) ** 2) - 2j * np.pi * (qx * cx + qy * cy))
    )


def layer_spectrum(qx, qy, features):
    """Sum the analytic spectra of features in one axial layer."""
    result = np.zeros_like(qx, dtype=complex)
    for a, cx, cy, sx, sy, angle, fx, fy, contrast in features:
        result += a * gaussian(qx, qy, cx, cy, sx, sy, angle)
        if contrast:
            for sign in (-1, 1):
                translation = np.exp(-2j * np.pi * sign * (fx * cx + fy * cy))
                result += (
                    a
                    * contrast
                    / 2
                    * translation
                    * gaussian(qx - sign * fx, qy - sign * fy, cx, cy, sx, sy, angle)
                )
    return result


def disk_jinc(t):
    """2 J1(t)/t using the absolutely convergent series on this bounded domain."""
    assert np.max(np.abs(t)) < 4
    term = np.ones_like(t)
    result = term.copy()
    for j in range(1, 18):
        term *= (-t * t / 4) / (j * (j + 1))
        result += term
    return result


def camera(signal, seed):
    """Return native little-endian float32 ADU, using PCG64 for the noisy arm."""
    if not np.isfinite(signal).all() or signal.min() < -0.05:
        raise ValueError("expected signal is nonfinite or below the modeled budget")
    if (signal + DARK_E).min() < 0:
        raise ValueError("negative Poisson mean")
    offset = BACKGROUND - DARK_E * ADU_PER_E
    expectation = offset + ADU_PER_E * (signal + DARK_E)
    if expectation.min() < 0 or expectation.max() > MAX_CODE:
        raise ValueError("ideal detector counts exceed the ADC range")
    if seed is None:
        return expectation.astype("<f4")
    rng = np.random.Generator(np.random.PCG64(seed))
    noisy_before_adc = offset + ADU_PER_E * (
        rng.poisson(signal + DARK_E) + rng.normal(0, READ, signal.shape)
    )
    quantized = np.rint(noisy_before_adc)
    if quantized.min() < 0 or quantized.max() > MAX_CODE:
        raise ValueError("noisy detector counts require clipping")
    return quantized.astype("<f4")


def conventional(raw):
    """Equal positive dose on all 15 planes. Real trigonometric interpolation."""
    corrected = raw.astype(np.float64) - BACKGROUND
    image = corrected.mean(axis=(0, 1))
    nz, n, nx = image.shape
    assert n == nx and n % 2 == 0
    transformed = np.fft.fft2(image)
    # One-dimensional symmetric split at each Nyquist gives a real interpolant,
    # including the four-way corner split, with exact detector-grid reproduction.
    for a in (-1, -2):
        t = np.moveaxis(transformed, a, -1)
        u = np.zeros(t.shape[:-1] + (2 * n,), dtype=complex)
        mid = n // 2
        u[..., :mid] = t[..., :mid]
        u[..., mid] = u[..., -mid] = t[..., mid] / 2
        u[..., -(mid - 1) :] = t[..., mid + 1 :]
        transformed = np.moveaxis(u, -1, a)
    return 4 * np.fft.ifft2(transformed).real / (ADU_PER_E * E_PER_SU)
