"""Independent tiny finite-pupil matrix, derived only from public contracts.

This observer uses explicit source/pixel sums and a J0 power series. It does not
read the production cache, use FFTs, fit a source, or use replay as optical truth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

F64 = NDArray[np.float64]
F32 = NDArray[np.float32]
SPACING = (0.173, 0.071, 0.053)  # micrometres; deliberately anisotropic
ORIGIN = (0.23, -0.37, 0.19)  # only lateral origin enters supplied phases


@dataclass(frozen=True)
class TinyCase:
    """Tiny signed source and explicitly supplied physical illumination."""

    source: F32
    carriers: F64
    phases: F64
    local_phases: F64
    beams: F64
    order: int

    def kwargs(self) -> dict[str, object]:
        return {
            "source_spacing_um_zyx": SPACING,
            "carriers_yx_per_um": self.carriers,
            "phases_at_specimen_origin_rad": self.phases,
            "beam_amplitudes": self.beams,
            "pupil_order": self.order,
        }


def tiny_case(order: int = 3) -> TinyCase:
    source = np.zeros((2, 4, 6), dtype=np.float32)
    source[0, 0, 5] = 1.75
    source[1, 3, 0] = -0.625
    source[1, 1, 4] = 0.3125
    source[0, 2, 1] = -0.09375
    carriers = np.array([[0.83, -0.47], [-0.62, 1.13], [1.21, 0.29]])
    local = np.array(
        [
            [0.17, 1.32, -0.91, 3.22, 5.73],
            [-0.41, 0.93, 2.46, 4.11, 5.81],
            [0.61, 1.88, 3.07, -1.18, 5.43],
        ],
        dtype=np.float64,
    )
    phases = local + 2 * math.pi * (carriers @ np.array(ORIGIN[1:]))[:, None]
    return TinyCase(source, carriers, phases, local, np.array([4.0, 2.0, 1.0]), order)


def j0_series(x: float) -> float:
    """J0(x)=sum (-x*x/4)^k/(k!)^2, with a bounded tiny domain."""
    assert abs(x) < 6.0
    terms = [1.0]
    for k in range(1, 80):
        terms.append(terms[-1] * (-x * x / 4) / (k * k))
    assert abs(terms[-1]) < 1e-140
    return math.fsum(terms)


def pupil(radius_um: float, source_minus_focus_um: float, order: int) -> float:
    """Clear finite-Q h in inverse square micrometres, not pixel integrated."""
    if order == 1:
        nodes, weights = (0.5,), (1.0,)
    else:
        assert order == 3
        t = math.sqrt(3 / 5)
        nodes, weights = ((1 - t) / 2, 0.5, (1 + t) / 2), (5 / 18, 4 / 9, 5 / 18)
    radius = 1.4 / 0.525
    beta = 1.4 / 1.515
    real, imag = [], []
    for u, w in zip(nodes, weights, strict=True):
        a = w * j0_series(2 * math.pi * radius * math.sqrt(u) * radius_um)
        angle = (
            2
            * math.pi
            * (1.515 / 0.525)
            * source_minus_focus_um
            * (math.sqrt(1 - beta * beta * u) - 1)
        )
        real.append(a * math.cos(angle))
        imag.append(a * math.sin(angle))
    return math.pi * radius * radius * (math.fsum(real) ** 2 + math.fsum(imag) ** 2)


def direct_matrices(case: TinyCase) -> tuple[F64, F64]:
    """Return all15 illuminated matrices and the full unilluminated B_Q.

    Rows are finite detector sites; columns are every declared source site.
    Four midpoint samples have weight dy*dx each, with no axial/volume factor.
    The direct squared field uses source-minus-focus defocus and unequal sides.
    """
    shape = case.source.shape
    detector_shape = (shape[0], shape[1] // 2, shape[2] // 2)
    source_indices = list(np.ndindex(shape))
    detector_indices = list(np.ndindex(detector_shape))
    b = np.empty((len(detector_indices), len(source_indices)), dtype=np.float64)
    a = np.empty((3, 5, *b.shape), dtype=np.float64)
    dz, dy, dx = SPACING
    a0, plus, minus = (float(v) for v in case.beams)
    s = a0 * a0 + plus * plus + minus * minus
    k0 = 1.515 / 0.488
    for ni, (nz, ny, nx) in enumerate(detector_indices):
        for ji, (jz, jy, jx) in enumerate(source_indices):
            d = (jz - nz) * dz
            samples = [
                pupil(math.hypot((2 * ny + sy - jy) * dy, (2 * nx + sx - jx) * dx), d, case.order)
                for sy in (0, 1)
                for sx in (0, 1)
            ]
            b[ni, ji] = dy * dx * math.fsum(samples)
            for o, (qy, qx) in enumerate(case.carriers):
                kappa = k0 - math.sqrt(k0 * k0 - float(qy * qy + qx * qx))
                axial = 2 * math.pi * kappa * d
                for p in range(5):
                    theta = 2 * math.pi * (
                        float(qy) * (jy + 0.5) * dy + float(qx) * (jx + 0.5) * dx
                    ) + float(case.phases[o, p])
                    re = a0 * math.cos(axial) + (plus + minus) * math.cos(theta)
                    im = a0 * math.sin(axial) + (plus - minus) * math.sin(theta)
                    a[o, p, ni, ji] = b[ni, ji] * (re * re + im * im) / s
    return a, b


def direct_prediction(case: TinyCase, matrix: F64) -> F64:
    x = case.source.ravel()
    values = [
        math.fsum(float(v) * float(w) for v, w in zip(row, x, strict=True))
        for row in matrix.reshape(-1, x.size)
    ]
    z, y, xsize = case.source.shape
    return np.array(values).reshape(3, 5, z, y // 2, xsize // 2)


def scales(case: TinyCase, b: F64) -> dict[str, float]:
    cr = max(math.fsum(float(v) for v in row) for row in b)
    cc = max(math.fsum(float(v) for v in col) for col in b.T)
    beams = [float(v) for v in case.beams]
    illumination_bound = math.fsum(beams) ** 2 / math.fsum(v * v for v in beams)
    scale = illumination_bound * cr * float(np.max(np.abs(case.source)))
    # Observer budget is separate from the selected inherited product allowance.
    return {
        "row_norm": cr,
        "column_norm": cc,
        "illumination_bound": illumination_bound,
        "physical_scale": scale,
        "observer": 2e-10 * scale,
        "inverse_bound": (2e-4 + 1e-8) * scale,
    }
