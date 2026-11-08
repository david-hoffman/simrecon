"""Project the frozen continuous sources through one scalar focal-scan model."""

import numpy as np
from numpy.polynomial.hermite import hermgauss
from numpy.polynomial.legendre import leggauss
from optics import (
    BASE,
    BEAD_ANGLE,
    BEAD_CENTER,
    BEAD_E_UM,
    BEAD_K,
    BEAD_OUTER,
    BEAD_PHASE,
    BEAD_RADIUS,
    BXY,
    CARRIERS,
    CENTER,
    DZ,
    E_PER_SU,
    OUTER,
    PHASE_ORIGINS,
    PHASES,
    XY,
    N,
    R,
    Z,
    axis,
    coefficients,
    disk_jinc,
    layer_spectrum,
)
from scenes import SPHERE_MASS, SPHERE_R, cell_groups, centres, structured_groups


def _sphere_rule(radius, order):
    nodes, weights = leggauss(order)
    angle = np.pi / 2 * nodes
    return (
        radius * np.sin(angle),
        radius * np.cos(angle),
        0.75 * (np.pi / 2) * weights * np.cos(angle) ** 3,
    )


def _calibration_band(pupil, z, order, shifted_x, shifted_y, k, outer, center, m, interp):
    depths, radii, weights = _sphere_rule(BEAD_RADIUS, order)
    depth = 0.037 + depths
    defocus = z[:, None] - depth
    harmonic = coefficients(defocus, k, outer, center)[m]
    freq = np.hypot(shifted_x, shifted_y)
    sphere = disk_jinc(2 * np.pi * radii[:, None] * freq)
    sphere = sphere * np.exp(-2j * np.pi * (shifted_x * 0.023 + shifted_y * (-0.017)))
    band = np.zeros((Z, len(freq)), complex)
    for j, w in enumerate(weights):
        h = pupil.at_s(defocus[:, j])
        band += w * interp(h) * harmonic[:, j, None] * sphere[j]
    return band


def _sphere_layers(pupil, z, order):
    depths, radii, weights = _sphere_rule(SPHERE_R, order)
    points = centres()
    layers = []
    for depth in np.unique(points[:, 2]):
        s = z[:, None] - depth - depths
        layers.append((s, points[points[:, 2] == depth, :2], pupil.at_s(s)))
    return layers, radii, weights * SPHERE_MASS


def _sphere_band(layers, radii, weights, shifted_x, shifted_y, k, outer, center, m, interp):
    freq = np.hypot(shifted_x, shifted_y)
    disk = disk_jinc(2 * np.pi * radii[:, None] * freq)
    band = np.zeros((Z, len(freq)), complex)
    for defocus, points, h in layers:
        harmonic = coefficients(defocus, k, outer, center)[m]
        shifted = sum(np.exp(-2j * np.pi * (shifted_x * x + shifted_y * y)) for x, y in points)
        for i, w in enumerate(weights):
            band += interp(h[:, i]) * (w * harmonic[:, i, None]) * disk[i] * shifted
    return band


def _gaussian_layers(pupil, z, order, is_cell):
    nodes, weights = hermgauss(order)
    groups = cell_groups() if is_cell else structured_groups()
    layers = []
    for depth, sz, features in groups:
        defocus = z[:, None] - depth - np.sqrt(2) * sz * nodes
        layers.append((defocus, sz, features, pupil.at_s(defocus)))
    return layers, weights


def _gaussian_band(layers, weights, shifted_x, shifted_y, k, outer, center, m, interp, is_cell):
    band = np.zeros((Z, len(shifted_x)), complex)
    for defocus, sz, features, h in layers:
        harmonic = coefficients(defocus, k, outer, center)[m]
        profile = np.sum(h * (harmonic * weights)[..., None], axis=1)
        spectrum = layer_spectrum(shifted_x, shifted_y, features)
        # Preserve each frozen evaluator's multiplication and interpolation order.
        if is_cell:
            band += interp(profile) * (sz * np.sqrt(2) * spectrum)
        else:
            profile *= sz * np.sqrt(2)
            band += interp(profile) * spectrum
    return band


def render(kind, pupil):
    """Return expected signal electrons in (direction, phase, Z, Y, X) order."""
    pad, radial, _, _, order = BASE
    calibration = kind == "calibration"
    phantom = kind in ("beads", "cell")
    xy = BXY if calibration else XY
    side = pad * N
    z = axis(Z, DZ)
    q = np.fft.fftfreq(side, xy)
    radius_grid = np.hypot(q[:, None], q[None, :])
    inside = radius_grid < R
    iy, ix = np.nonzero(inside)
    qx, qy, radius = q[ix], q[iy], radius_grid[inside]
    origin = np.where((ix + iy) % 2, -1, 1)
    window = np.sinc(qx * xy) * np.sinc(qy * xy)
    # The phantom adapter and the structured/calibration renderer rounded
    # this coordinate differently. Keep both original evaluation orders.
    u = radius * radial / R if phantom else radius / (R / radial)
    j = np.floor(u).astype(int)
    t = u - j

    def interp(h):
        return h[:, j] * (1 - t) + h[:, j + 1] * t

    if calibration:
        kxy = BEAD_K * np.array([np.cos(BEAD_ANGLE), np.sin(BEAD_ANGLE)])
        directions = [(kxy, BEAD_PHASE, BEAD_OUTER, BEAD_CENTER)]
    else:
        directions = zip(CARRIERS, PHASE_ORIGINS, OUTER, CENTER, strict=True)
        if kind == "beads":
            layers, radii, weights = _sphere_layers(pupil, z, order)
        else:
            layers, weights = _gaussian_layers(pupil, z, order, kind == "cell")
    raw = np.empty((1 if calibration else 3, 5, Z, N, N))
    crop = slice((side - N) // 2, (side + N) // 2)
    for d, (kxy, theta, outer, center) in enumerate(directions):
        k = np.linalg.norm(kxy)
        for m in range(3):
            shifted_x, shifted_y = qx + m * kxy[0], qy + m * kxy[1]
            args = shifted_x, shifted_y, k, outer, center, m, interp
            if calibration:
                band = _calibration_band(pupil, z, order, *args)
            elif kind == "beads":
                band = _sphere_band(layers, radii, weights, *args)
            else:
                band = _gaussian_band(layers, weights, *args, kind == "cell")
            band *= window * origin * np.exp(-1j * m * theta) / xy**2
            plane = np.zeros((side, side), complex)
            for iz, values in enumerate(band):
                plane[inside] = values
                image = np.fft.ifft2(plane)[crop, crop]
                if m == 0:
                    if np.max(np.abs(image.imag)) >= 1e-11:
                        raise ValueError("zero-order image is not real to the frozen tolerance")
                    raw[d, :, iz] = image.real
                elif phantom:
                    raw[d, :, iz] += (
                        2 * (image[None] * np.exp(-1j * m * PHASES[:, None, None])).real
                    )
                else:
                    for p, phase in enumerate(PHASES):
                        raw[d, p, iz] += 2 * (image * np.exp(-1j * m * phase)).real
    raw *= BEAD_E_UM if calibration else E_PER_SU / (Z * DZ)
    return raw
