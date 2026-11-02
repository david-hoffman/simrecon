"""Independent CE02 mathematics; no production oracle or FFT implementation."""

from __future__ import annotations

import cmath
import math
from typing import Any

import numpy as np
from numpy.typing import NDArray

Real = NDArray[np.float64]
ORDINARY_TOL = 2e-11
CLUSTERED_TOL = 2e-7

REFERENCE = (
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    (
        "small_math_funcs.c",
        "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e",
    ),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)


def close(actual: Any, expected: Any, tol: float = ORDINARY_TOL) -> None:
    """Cancellation-aware budget declared before product observations."""
    expected = np.asarray(expected)
    scale = max(1.0, float(np.max(np.abs(expected))))
    np.testing.assert_allclose(actual, expected, rtol=tol, atol=tol * scale)


def options(**changes: Any) -> dict[str, Any]:
    result: dict[str, Any] = dict(
        dxy_um=0.125,
        dz_um=0.375,
        norders=3,
        background=0.0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )
    result.update(changes)
    return result


def uniform_rows(directions: int, phases: int, orders: int) -> tuple[Real, Real]:
    angles = np.tile(2 * np.pi * np.arange(phases) / phases, (directions, 1))
    rows = np.ones((directions, 2 * orders - 1, phases))
    for m in range(1, orders):
        rows[:, 2 * m - 1] = np.cos(m * angles)
        rows[:, 2 * m] = np.sin(m * angles)
    return angles, rows


def square_rows() -> tuple[Real, Real]:
    """Cardinal plus diagonal design, with different column order per direction."""
    t = math.sqrt(0.5)
    base = np.array(
        [
            [1.25, 1.25, 1.25, 1.25, 0],
            [1.25, 0, -1.25, 0, 0],
            [0, 1.25, 0, -1.25, 0],
            [0.625, -0.625, 0.625, -0.625, 0],
            [-0.625 - 1.25 * t, -0.625 - 1.25 * t, -0.625 + 1.25 * t, -0.625 + 1.25 * t, 2.5],
        ]
    )
    phi = np.array([0, np.pi / 2, np.pi, 3 * np.pi / 2, np.pi / 4])
    perms = ([0, 1, 2, 3, 4], [4, 2, 0, 3, 1], [1, 3, 4, 0, 2])
    return np.array([phi[p] for p in perms]), np.array([base[:, p] for p in perms])


def repeated_rows() -> tuple[Real, Real]:
    return np.array([[0, np.pi / 2, np.pi, np.pi]]), np.array(
        [[[2, 0, 1, 1], [1, 0, -0.5, -0.5], [-1, 2, -0.5, -0.5]]]
    )


def edge_plane(plane: Real, width: int) -> Real:
    """Scalar update observer, preserving sequential overlap writes."""
    out = plane.copy()
    height, size = out.shape
    if width == -1:
        return out * np.outer(
            np.sin(np.pi * (np.arange(height) + 0.5) / height),
            np.sin(np.pi * (np.arange(size) + 0.5) / size),
        )
    if width < 0:
        return out
    for axis in (0, 1):
        length = out.shape[axis]
        for other in range(out.shape[1 - axis]):
            line = out[:, other] if axis == 0 else out[other, :]
            delta = float(line[-1] - line[0]) / 2
            for k in range(width):
                adjustment = delta * (1 - math.sin(math.pi * (k + 0.5) / (2 * width)))
                line[k] += adjustment
                line[length - 1 - k] -= adjustment
    return out


def direct_volume(volume: Real) -> NDArray[np.complex128]:
    """One direct 3D sum. No FFT or staged product transformation."""
    nz, ny, nx = volume.shape
    result = np.zeros((nz, ny, nx // 2 + 1), dtype=np.complex128)
    for kz, ky, kx in np.ndindex(result.shape):
        terms = (
            float(volume[z, y, x])
            * cmath.exp(-2j * math.pi * (kz * z / nz + ky * y / ny + kx * x / nx))
            for z, y, x in np.ndindex(volume.shape)
        )
        values = list(terms)
        result[kz, ky, kx] = complex(
            math.fsum(v.real for v in values), math.fsum(v.imag for v in values)
        )
    return result


def expected(images: Any, rows: Real, **kw: Any) -> dict[str, Any]:
    """Raw to final quadratures via spatial phase combination and direct sums."""
    nt, nd, np_, nz, ny, nx = images.shape
    alpha = 1 / (nx * ny * nz * kw["lateral_zoom"] ** 2 * kw["axial_zoom"] * nd)
    background = (
        np.full((ny, nx), kw["background"], dtype=np.float64)
        if np.ndim(kw["background"]) == 0
        else np.array(kw["background"], dtype=np.float64, copy=True)
    )
    slope = (
        np.ones((ny, nx))
        if kw.get("flatfield_slope") is None
        else np.array(kw["flatfield_slope"], dtype=np.float64, copy=True)
    )
    extra = kw.get("exposure_background")
    frames = np.empty(images.shape, dtype=np.float64)
    events = []
    for t in range(nt):
        for d in range(nd):
            for z in range(nz):
                for p in range(np_):
                    raw = np.array(images[t, d, p, z], dtype=np.float64, copy=True)
                    if raw[-1, -1] == -1:
                        raw[-1, -1] = raw[-1, -2]
                        background[-1, -1] = background[-1, -2]
                        slope[-1, -1] = 1
                        events.append((t, d, z, p))
                    offset = 0 if extra is None else extra[t, d, p, z]
                    frames[t, d, p, z] = edge_plane(
                        alpha * slope * (raw - background - offset), kw["edge_pixels"]
                    )
    sums = frames.sum(axis=(-2, -1))
    gains = np.ones_like(sums)
    if kw["equalize"]:
        for t, d, p, z in np.ndindex(sums.shape):
            ref_t = 0 if kw.get("equalize_time", False) else t
            ref_z = 0 if kw.get("equalize_z", False) else z
            gains[t, d, p, z] = sums[ref_t, 0, 0, ref_z] / sums[t, d, p, z]
    frames *= gains[..., None, None]
    nq = rows.shape[1]
    output = np.zeros((nt, nd, nq, nz, ny, nx // 2 + 1), dtype=np.complex128)
    for t, d, q in np.ndindex((nt, nd, nq)):
        volume = np.zeros((nz, ny, nx))
        for p in range(np_):
            volume += rows[d, q, p] * frames[t, d, p]
        output[t, d, q] = direct_volume(volume)
        endpoint = direct_volume(frames[t, d, q])
        output[t, d, q, :, :, -1] = endpoint[:, :, -1]
    return dict(
        quadratures=output,
        frame_sums=sums,
        equalization_gains=gains,
        background_after=background,
        slope_after=slope,
        sentinel_frames=tuple(events),
        input_scale=alpha,
    )


def composition() -> tuple[Real, dict[str, Any], Real]:
    shape = (2, 3, 5, 3, 3, 4)
    t, d, p, z, y, x = np.indices(shape)
    images = (30 + 11 * t + 7 * d + 3 * p + 5 * z + 2 * y + x * x).astype(float)
    # t,d,z,p traversal differs observably from C-contiguous phase/z storage.
    for tt, dd, pp, zz in ((0, 0, 3, 0), (0, 0, 1, 1), (0, 2, 4, 2), (1, 1, 0, 0)):
        images[tt, dd, pp, zz, -1, -1] = -1
    images[1, 2, 2, 1, 0, 0] = -1  # ordinary negative count, not sentinel
    phases, rows = square_rows()
    kw = options(
        background=np.array([[2, 4, 3, 7], [1, 5, 2, 4], [6, 3, 8, 11.0]]),
        flatfield_slope=np.array([[1, 2, 0.5, 1.5], [2, 1, 3, 0.25], [1, 2, 1.5, 4]]),
        exposure_background=(np.indices(shape[:4]).sum(axis=0) % 4).astype(float),
        phases_rad=phases,
        lateral_zoom=2,
        axial_zoom=3,
        edge_pixels=2,
        equalize=True,
        equalize_z=True,
        equalize_time=True,
    )
    return images, kw, rows
