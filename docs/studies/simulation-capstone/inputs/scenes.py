"""Frozen specimen geometry and continuous-source truth."""

import numpy as np
from numpy.polynomial.legendre import leggauss
from optics import ANGLES, DZ, XY, N, Z, axis

PITCH = XY / 2
SPHERE_R = 0.050
SPHERE_MASS = 0.013  # source-unit micrometres cubed per sphere
# (label, center x/y/z in µm, profile angle in degrees, center distance in µm)
OBJECTS = (
    ("I1", -3.173, -2.306, -0.6875, 0, 0),
    ("I2", 2.770, -2.137, 0.314, 56, 0),
    ("I3", -2.882, 2.341, 0.936, 124, 0),
    ("I4", 2.927, 2.519, -0.370, 90, 0),
    ("P14", -0.897, -1.658, -0.548, 4, 0.14),
    ("P23", 1.359, -0.519, 0.657, 56, 0.23),
    ("P32", -1.239, 0.518, -0.143, 124, 0.32),
    ("P45", 0.658, 1.815, 0.185, 27, 0.45),
)
RIM_Z = -0.41
RIM_ANGLES = 2 * np.pi * np.arange(32) / 32
RIM = np.column_stack(
    (
        -0.96 + (1.11 + 0.14 * np.cos(3 * RIM_ANGLES + 0.4)) * np.cos(RIM_ANGLES),
        0.44 + (0.82 + 0.13 * np.sin(2 * RIM_ANGLES)) * np.sin(RIM_ANGLES),
    )
)
# Quadratic paths in the lateral plane: start, bend control, end, depth.
PATHS = (
    ("trunk", (0.56, -0.85), (1.48, -0.41), (1.71, -0.56), -0.70),
    ("branch_up", (1.71, -0.56), (2.03, 0.08), (2.55, 0.75), -0.70),
    ("branch_down", (1.71, -0.56), (2.17, -0.70), (2.69, -1.56), -0.70),
    ("upper_arc", (-2.63, 1.58), (-0.50, 2.83), (0.70, 1.74), 0.68),
    ("lower_hook", (-2.18, -1.52), (-0.33, -2.83), (0.67, -1.71), 0.25),
)
PUNCTA = (
    (-2.27, -0.93, 0.96),
    (0.55, -0.04, 0.53),
    (2.46, 1.63, 0.30),
    (-1.93, 1.71, -0.69),
    (0.77, 2.55, -0.28),
    (1.91, -1.93, 0.87),
    (0.89, -0.88, -0.17),
    (-0.84, -1.76, 0.91),
)


def unit(angle):
    """Return the lateral unit vector at an angle in degrees."""
    return np.array([np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))])


def centres():
    """Return the ordered sphere centers in micrometers."""
    points = []
    for _, x, y, z, angle, separation in OBJECTS:
        offsets = (-separation / 2, separation / 2) if separation else (0.0,)
        for offset in offsets:
            point = np.array([x, y]) + offset * unit(angle)
            points.append((*point, z))
    return np.array(points)


def path_points(path, t):
    """Sample a quadratic path in the lateral plane."""
    _, start, bend, end, _ = path
    t = np.asarray(t)[..., None]
    return (1 - t) ** 2 * np.array(start) + 2 * (1 - t) * t * np.array(bend) + t * t * np.array(end)


def gaussian_group(amplitude, points, sx, sy=None, angle=0.0):
    """Assign the same profile to each given spot center."""
    return [(amplitude, x, y, sx, sy or sx, angle, 0.0, 0.0, 0.0) for x, y in points]


def cell_groups():
    """Return the Gaussian layers of the corrected cell interior."""
    rim = [
        feature
        for j, point in enumerate(RIM)
        for feature in gaussian_group(0.70 + 0.19 * np.cos(3 * RIM_ANGLES[j] + 0.7), [point], 0.137)
    ]
    groups = [(RIM_Z, 0.18, rim)]
    # Group equal depths/widths. Each chain uses densely overlapping positive spots.
    tubes = {}
    for path in PATHS:
        z = path[-1]
        segment = path_points(path, np.linspace(0, 1, 19))
        if path[0].startswith("branch"):
            segment = segment[1:]  # the common origin is already in the trunk
        tubes.setdefault(z, []).extend(gaussian_group(0.37, segment, 0.084))
    groups.extend((z, 0.115, features) for z, features in tubes.items())
    groups.extend(
        (z, 0.091, gaussian_group(1.23, [(x, y)], 0.078, 0.091, 0.31)) for x, y, z in PUNCTA
    )
    # Diffuse asymmetric lobes leave a low-signal nuclear interior at the rim depth.
    groups.extend(
        [
            (-0.20, 0.35, gaussian_group(0.22, [(1.61, 0.32)], 0.85, 1.02, 0.31)),
            (0.22, 0.31, gaussian_group(0.16, [(-1.67, -1.35)], 0.92, 0.61, -0.54)),
            (0.38, 0.29, gaussian_group(0.13, [(-0.21, 1.72)], 1.19, 0.61, 0.22)),
            (0.25, 0.30, gaussian_group(0.041, [(-0.63, 0.32)], 1.24, 1.11, 0.0)),
        ]
    )
    return groups + cluster_groups()


# Cell revision 2, in the preregistered layer and feature order.
# Rows contain x, y, amplitude, lateral sigma x/y, and angle in radians.
CELL_CLUSTERS = (
    (
        0.625,
        0.105,
        (
            (1.18, 2.49, 1.78, 0.075, 0.098, 0.33),
            (1.63, 2.68, 2.42, 0.102, 0.083, -0.47),
            (1.91, 2.34, 1.91, 0.086, 0.114, 0.72),
            (2.22, 2.77, 2.18, 0.107, 0.091, -0.18),
            (2.70, 2.96, 1.62, 0.081, 0.102, 0.49),
            (2.48, 2.33, 2.57, 0.095, 0.119, -0.66),
        ),
    ),
    (
        -0.750,
        0.115,
        (
            (-2.66, -2.12, 2.20, 0.093, 0.076, -0.31),
            (-2.36, -2.55, 1.85, 0.110, 0.092, 0.66),
            (-2.72, -2.84, 1.69, 0.080, 0.098, -0.58),
            (-1.95, -2.77, 2.48, 0.099, 0.115, 0.26),
            (-1.54, -2.62, 1.95, 0.085, 0.112, 0.84),
            (-1.70, -2.19, 2.34, 0.103, 0.090, -0.73),
            (-1.25, -2.37, 1.68, 0.077, 0.096, 0.15),
        ),
    ),
)


def cluster_groups():
    """Return the two added Gaussian layers in frozen feature order."""
    return [
        (
            depth,
            sz,
            [(amp, x, y, sx, sy, angle, 0.0, 0.0, 0.0) for x, y, amp, sx, sy, angle in rows],
        )
        for depth, sz, rows in CELL_CLUSTERS
    ]


def structured_groups():
    """Analytic nonnegative fields. Tuples are amplitude, cx,cy,sx,sy,angle,fx,fy,contrast."""
    stretch = 2.35
    groups = [(-0.94, 0.16, []), (-0.20, 0.18, []), (0.55, 0.17, []), (1.08, 0.14, [])]
    centers = [(-1.02, -0.72), (1.04, -0.57), (0.16, 0.98)]
    for d, (cx, cy) in enumerate(centers):
        angle = ANGLES[d]
        fx, fy = 7.47 * np.array([np.cos(angle), np.sin(angle)])
        groups[d][2].append((0.85, stretch * cx, stretch * cy, 0.31, 0.64, angle, fx, fy, 0.82))
        for t in np.linspace(-0.9, 0.9, 7):
            groups[d][2].append(
                (
                    0.16,
                    stretch * cx + 0.66 * t,
                    stretch * cy + 0.43 * t * t + 0.32,
                    0.094,
                    0.071,
                    0.3 + t,
                    0,
                    0,
                    0,
                )
            )
    for cx, cy in [(-1.63, 1.15), (1.55, 1.21), (0.45, -1.66)]:
        groups[-1][2].append((1.15, stretch * cx, stretch * cy, 0.095, 0.085, 0.2, 0, 0, 0))
    groups[-1][2].append((0.36, 0.13, -0.15, 0.91, 0.69, 0.38, 0, 0, 0))
    return groups


def structured_truth():
    """Independent point evaluation of continuous source, at requested spacing."""
    n, nz, refinement = N, Z, 2
    x = axis(n * refinement, XY / refinement)[None, :]
    y = x.T
    z = axis(nz, DZ)[:, None, None]
    result = np.zeros((nz, n * refinement, n * refinement))
    for depth, sz, features in structured_groups():
        plane = np.zeros((n * refinement, n * refinement))
        for a, cx, cy, sx, sy, angle, fx, fy, contrast in features:
            xx, yy = x - cx, y - cy
            c, s = np.cos(angle), np.sin(angle)
            radius2 = ((c * xx + s * yy) / sx) ** 2 + ((-s * xx + c * yy) / sy) ** 2
            plane += (
                a * np.exp(-radius2 / 2) * (1 + contrast * np.cos(2 * np.pi * (fx * xx + fy * yy)))
            )
        result += plane * np.exp(-0.5 * ((z - depth) / sz) ** 2)
    return result


def cell_truth():
    """Evaluate the revised continuous cell on the output grid."""
    x = axis(2 * N, PITCH)[None, None, :]
    y = axis(2 * N, PITCH)[None, :, None]
    z = axis(Z, DZ)[:, None, None]
    result = np.zeros(np.broadcast_shapes(np.shape(x), np.shape(y), np.shape(z)))
    for depth, sz, features in cell_groups():
        plane = np.zeros(np.broadcast_shapes(np.shape(x), np.shape(y)))
        for amp, cx, cy, sx, sy, angle, *_ in features:
            xx, yy = x - cx, y - cy
            c, s = np.cos(angle), np.sin(angle)
            plane += amp * np.exp(
                -0.5 * (((c * xx + s * yy) / sx) ** 2 + ((-s * xx + c * yy) / sy) ** 2)
            )
        result += plane * np.exp(-0.5 * ((z - depth) / sz) ** 2)
    return result


def sphere_truth(order):
    """Voxel averages from continuous chord lengths; integrate only intersecting cells."""
    gx, gz = axis(2 * N, PITCH), axis(Z, DZ)
    u, w = leggauss(order)
    out = np.zeros((Z, 2 * N, 2 * N))
    r = SPHERE_R
    for x, y, z in centres():
        xs = np.flatnonzero(abs(gx - x) < r + PITCH / 2)
        ys = np.flatnonzero(abs(gx - y) < r + PITCH / 2)
        zs = np.flatnonzero(abs(gz - z) < r + DZ / 2)
        for iz in zs:
            za, zb = max(-r, gz[iz] - z - DZ / 2), min(r, gz[iz] - z + DZ / 2)
            zn = (zb + za) / 2 + (zb - za) / 2 * u
            disk_r = np.sqrt(r * r - zn * zn)
            ya = np.maximum(-disk_r[:, None], gx[ys] - y - PITCH / 2)
            yb = np.minimum(disk_r[:, None], gx[ys] - y + PITCH / 2)
            dy = np.maximum(yb - ya, 0)
            yn = ya[..., None] + dy[..., None] * (1 + u) / 2
            half = np.sqrt(np.maximum(0, disk_r[:, None, None] ** 2 - yn**2))
            lower = np.maximum(-half[..., None], gx[xs] - x - PITCH / 2)
            upper = np.minimum(half[..., None], gx[xs] - x + PITCH / 2)
            chord = np.maximum(upper - lower, 0)
            volume = np.einsum("i,j,ik,ijkx->kx", w, w, dy, chord.transpose(0, 2, 1, 3))
            volume *= (zb - za) / 4
            density = SPHERE_MASS / (4 * np.pi * r**3 / 3)
            out[iz][np.ix_(ys, xs)] += volume * density / (PITCH**2 * DZ)
    return out
