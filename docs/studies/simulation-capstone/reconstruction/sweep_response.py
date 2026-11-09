"""Independent finite axial Fourier projections of the signed reconstruction."""

import math

import numpy as np
from sweep_scoring import DZ, PITCH, SCORE_GAIN_SU_PER_COUNT

# Labels are portable filenames only. Use the keys for computation and numeric JSON.
WIENER_FILES = {
    0.002: "w-0.002.npz",
    0.002 * math.sqrt(10): "w-0.006325.npz",
    0.020: "w-0.020.npz",
    0.020 * math.sqrt(10): "w-0.063246.npz",
    0.200: "w-0.200.npz",
}
WIENERS = tuple(WIENER_FILES)
AXIAL_BINS = (0, 1, 2, 4)
# Output (y, x) indices nearest the named features on the frozen signed grid.
POINTS_YX = {
    "beads": ((70, 49), (115, 162), (141, 97), (173, 144)),  # I1, P23, P32, P45
    "cell": ((139, 135), (114, 171), (186, 190), (75, 62)),  # rim, trunk, NE, SW
}
RADIUS_CYC_UM = 2 * 1.4 / 0.525
PROJECTION_ATOL_SU = 2e-9
PROJECTION_RTOL = 2e-8


def _radial_sample(table, radius, kz, radial_step):
    # The contracted radial interpolation has zero axial fraction on this grid.
    position = radius / radial_step
    i = np.floor(position).astype(int)
    weight = position - i
    return (1 - weight) * table[i, kz] + weight * table[i + 1, kz]


def _native_axial_modes(raw_direction, kz):
    phases, z, y, x = raw_direction.shape
    axial = np.exp(-2j * np.pi * kz * np.arange(z) / z)
    per_phase = np.fft.fft2(np.einsum("z,pzyx->pyx", axial, raw_direction))
    if kz == 0:
        per_phase[:, 0, 0] -= 512 * z * y * x
    phase_angles = 2 * np.pi * np.arange(phases) / phases
    harmonics = np.exp(1j * np.arange(3)[:, None] * phase_angles)
    return np.einsum("mp,pyx->myx", harmonics, per_phase)


def predicted(raw, table, radial_step, carriers, modulation, variances, points_yx, bins):
    """Project every registered Wiener image from raw data at the declared probes."""
    directions, _, z, y, x = raw.shape
    shape = (2 * y, 2 * x)
    alpha = 1 / (z * shape[0] * shape[1] * directions)
    # R is below native Nyquist. Its selected cells never use the endpoint.
    fy, fx = np.meshgrid(np.fft.fftfreq(y, 2 * PITCH), np.fft.fftfreq(x, 2 * PITCH), indexing="ij")
    support = np.hypot(fx, fy) <= RADIUS_CYC_UM
    qx, qy = fx[support], fy[support]
    native_radius = np.hypot(qx, qy)
    points = np.asarray(points_yx)
    spatial = np.exp(2j * np.pi * PITCH * (points[:, 1, None] * qx + points[:, 0, None] * qy))
    coords = (points[:, ::-1] - np.array([x, y])) * PITCH
    amplitudes = np.column_stack((np.ones(directions), modulation))
    inverse_variance = 1 / variances
    native_dkz = 1 / (z * DZ)
    c0 = int(np.ceil((1.515 - np.sqrt(1.515**2 - 1.4**2)) / (0.525 * native_dkz)))
    cutoffs = np.minimum([c0, int((1 + 1 / 0.88) * c0), int(1.3 * c0)], z // 2 - 1)
    axial_bins = sorted(set(bins) | {-k for k in bins})
    terms = {k: np.zeros((len(WIENERS), len(points)), complex) for k in axial_bins}
    w_squared = np.square(WIENERS)

    for direction, carrier in enumerate(carriers):
        modes = {k: _native_axial_modes(raw[direction], k)[:, support] for k in axial_bins}
        for order, cutoff in enumerate(cutoffs):
            object_x, object_y = qx + order * carrier[0], qy + order * carrier[1]
            overlaps = []
            for other, other_carrier in enumerate(carriers):
                for signed_order in range(-2, 3):
                    if (other, signed_order) == (direction, order):
                        continue
                    radius = np.hypot(
                        object_x - signed_order * other_carrier[0],
                        object_y - signed_order * other_carrier[1],
                    )
                    eligible = radius < RADIUS_CYC_UM
                    overlaps.append((other, abs(signed_order), eligible, radius[eligible]))
            ramp = np.exp(2j * np.pi * order * (coords @ carrier))
            projected = spatial * (ramp * (2 if order else 1))[:, None]
            g = inverse_variance[direction, order]
            for k in axial_bins:
                if abs(k) > cutoff:
                    continue
                self_h = _radial_sample(table[order], native_radius, k, radial_step)
                gain = self_h * amplitudes[direction, order]
                power = g * abs(gain) ** 2
                for other, m, eligible, radius in overlaps:
                    h = _radial_sample(table[m], radius, k, radial_step)
                    power[eligible] += (
                        inverse_variance[other, m] * abs(h * amplitudes[other, m]) ** 2
                    )
                filtered = (modes[k][order] * g * gain.conj())[None, :] / (
                    power[None, :] + w_squared[:, None]
                )
                terms[k] += filtered @ projected.T

    return np.stack(
        [0.5 * alpha * SCORE_GAIN_SU_PER_COUNT * (terms[k] + terms[-k].conj()) for k in bins],
        axis=1,
    )


def observed(image_counts, points_yx, bins):
    """Read normalized axial Fourier coefficients from the actual signed image."""
    y, x = np.asarray(points_yx).T
    return np.fft.fft(image_counts[:, y, x], axis=0, norm="forward")[list(bins)] * (
        SCORE_GAIN_SU_PER_COUNT
    )


def prediction_margin(predictions):
    """Require every registered value to differ beyond both acceptance envelopes."""
    tolerance = PROJECTION_ATOL_SU + PROJECTION_RTOL * abs(predictions)
    ratios = [
        float(np.max(abs(left - right) / (tolerance[i] + tolerance[j])))
        for i, left in enumerate(predictions)
        for j, right in enumerate(predictions)
        if i < j
    ]
    if not np.isfinite(predictions).all() or min(ratios) <= 1:
        raise ValueError("independent projection does not distinguish all five Wiener values")
    return min(ratios)


def check_projection(actual, expected):
    """Reject a signed response outside the fixed per-coefficient error allowance."""
    error = abs(actual - expected)
    limit = PROJECTION_ATOL_SU + PROJECTION_RTOL * abs(expected)
    if not np.isfinite(actual).all() or np.any(error > limit):
        raise ValueError("signed finite response differs from the independent Wiener projection")
    return float(np.max(error))
