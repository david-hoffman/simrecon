"""Selected middle-stack and within-2D drift, cubic mutation and Fourier ramps."""

from __future__ import annotations

import math

import numpy as np

from .layout import AcquisitionModeError, Array, ModeEvent, event, finite, signed
from .preparation import _edge


def frequencies(length: int) -> Array:
    """Return unshifted integer labels with the positive even Nyquist lift."""
    indices = np.arange(length, dtype=np.float64)
    return np.where(indices <= length // 2, indices, indices - length)


def ramp(displacement: Array, z: int, y: int, x: int) -> Array:
    """Build the positive first-sample-origin detector-pixel correction."""
    phase = displacement[0] * np.arange(x // 2 + 1)[None, None, :] / x
    phase = phase + displacement[1] * frequencies(y)[None, :, None] / y
    if len(displacement) == 3:
        phase = phase + displacement[2] * frequencies(z)[:, None, None] / z
    result = np.exp(2j * np.pi * phase)
    finite(result, "drift correction ramp")
    return result


def correlation(
    reference: Array,
    moving: Array,
    *,
    x: int,
    dxy: float,
    radius: float,
    hpf: float,
    exponent: float,
    trace: list[ModeEvent],
    t: int,
    d: int,
    scope: str,
    moving_index: int,
    z_index: int | None = None,
) -> Array:
    """Evaluate the strict optical-mask absolute-real correlation estimator."""
    nz, ny, _ = reference.shape
    radial = np.hypot(
        np.arange(x // 2 + 1)[None, :] / (x * dxy), frequencies(ny)[:, None] / (ny * dxy)
    )
    finite(radial, "drift radial frequencies")
    selected = radial < radius
    cross = np.zeros(reference.shape, dtype=np.complex128)
    # The branch mask precedes multiplication/polar power, as in the caller.
    values = np.conjugate(reference[:, selected]) * moving[:, selected]
    magnitudes = np.abs(values)
    nonzero = magnitudes != 0
    weighted = np.zeros_like(values)
    weighted[nonzero] = magnitudes[nonzero] ** exponent * np.exp(1j * np.angle(values[nonzero]))
    if hpf > 0:
        weighted *= (1 - np.exp(-((radial[selected] / (hpf * radius)) ** 2))) ** 2
    cross[:, selected] = weighted
    finite(cross, "drift cross spectrum")
    real = np.fft.irfftn(cross, s=(nz, ny, x), axes=(0, 1, 2), norm="forward")
    finite(real, "drift real inverse correlation")
    absolute = np.abs(real)
    peak = [nz // 2, ny // 2, x // 2]
    best = 0.0
    for h, i, j in np.ndindex(absolute.shape):
        value = float(absolute[h, i, j])
        if value > best:
            best, peak = value, [h, i, j]
    neighbors = np.empty((3, 3), dtype=np.float64)
    offsets = np.zeros(3, dtype=np.float64)
    statuses = []
    # Source refines z, y, x, always about the unchanged integer peak.
    statuses_zyx = []
    for axis, length in enumerate((nz, ny, x)):
        low, high = list(peak), list(peak)
        low[axis], high[axis] = (peak[axis] - 1) % length, (peak[axis] + 1) % length
        minus, center, plus = (
            float(absolute[tuple(low)]),
            float(absolute[tuple(peak)]),
            float(absolute[tuple(high)]),
        )
        neighbors[2 - axis] = minus, center, plus
        if axis == 0 and nz == 1:
            status = "not-fitted"
        else:
            slope, curvature = (plus - minus) / 2, plus + minus - 2 * center
            finite((slope, curvature), "drift peak parabola")
            if curvature == 0:
                status = "zero-curvature"
            else:
                offset = -slope / curvature
                finite(offset, "drift peak offset")
                if not -1.5 <= offset <= 1.5:
                    status = "outside-range"
                else:
                    offsets[2 - axis], status = offset, "fitted"
        statuses_zyx.append(status)
    statuses = tuple(reversed(statuses_zyx))
    displacement = np.array(peak[::-1], dtype=np.float64) + offsets
    for axis, length in enumerate((x, ny, nz)):
        if displacement[axis] > length // 2:
            displacement[axis] -= length
    if nz == 1:
        displacement[2] = 0
    event(
        trace,
        "drift-correlation",
        t,
        d,
        z_index,
        None,
        scope=scope,
        moving_index=moving_index,
        exponent=exponent,
        cross_spectrum=cross,
        correlation=real,
        absolute_correlation=absolute,
        integer_peak_xyz=tuple(int(v) for v in peak[::-1]),
        neighbors_xyz=neighbors,
        offsets_xyz=offsets,
        offset_status_xyz=statuses,
        wrapped_displacement_xyz=displacement,
    )
    return displacement


def between(
    images: Array,
    off: Array | None,
    background: Array,
    *,
    t: int,
    dxy: float,
    dz: float,
    wavelength: int,
    na: float,
    immersion: float,
    hpf: float,
    trace: list[ModeEvent],
) -> Array:
    """Measure the selected raw middle stack before ordinary camera loading."""
    _, directions, phases, z, y, x = images.shape
    subz = max(z // 2, 1)
    first = (z - subz) // 2
    radius = 2 * na / (wavelength / 1000)
    dkz = 1 / (z * dz)
    aperture = math.asin(na / immersion)
    medium_lambda = (wavelength / immersion) / 1000
    raw_cutoff = ((1 - math.cos(aperture)) / medium_lambda) / dkz
    finite((radius, dkz, raw_cutoff), "between optical radial/unused axial cutoff")
    cutoff = min(signed(math.ceil(raw_cutoff), "unused axial cutoff"), z // 2)
    centers = np.zeros((directions, subz, y, x), dtype=np.float64)
    volume = x * y * z
    for d in range(directions):
        for h in range(subz):
            for p in range(phases):
                inputs = (
                    (images[t, d, p, first + h],)
                    if off is None
                    else (off[t, d, p, first + h, 0], images[t, d, p, first + h])
                )
                for source in inputs:
                    raw = np.array(source, dtype=np.float64, copy=True)
                    if raw[-1, -1] == -1:
                        raw[-1, -1] = raw[-1, -2]
                    centers[d, h] += (raw - background) / (phases * volume)
            _edge(centers[d, h], 10)
    finite(centers, "between prepass centers")
    fourier = np.fft.rfftn(centers, axes=(1, 2, 3))
    finite(fourier, "between prepass transform")
    event(
        trace,
        "between-build",
        t,
        0,
        subz=subz,
        first_z=first,
        centers=centers,
        fourier=fourier,
        optical_radial_cutoff=radius,
        unused_axial_cutoff=cutoff,
    )
    result = np.zeros((directions, 3), dtype=np.float64)
    for d in range(1, directions):
        result[d] = correlation(
            fourier[0],
            fourier[d],
            x=x,
            dxy=dxy,
            radius=radius,
            hpf=hpf,
            exponent=0.25,
            trace=trace,
            t=t,
            d=d,
            scope="between",
            moving_index=d,
        )
    return result


def cubic(
    samples: Array,
    evaluation: Array,
    displacement: Array,
    *,
    scope: str,
    trace: list[ModeEvent],
    t: int,
    d: int,
) -> Array:
    """Fit the forced-zero cubic and retain literal sample/evaluation mutation."""
    sample_before, evaluation_before = samples.copy(), evaluation.copy()
    n = len(samples)
    if n < 4:
        raise AcquisitionModeError("cubic fit requires at least four allocated sample points")
    for i in range(1, n):
        samples[i] -= samples[0]
    relative = samples[1:]
    if np.unique(relative[relative != 0]).size < 3:
        raise AcquisitionModeError("cubic fit has rank-deficient relative timestamps")
    matrix = np.column_stack((relative, relative**2, relative**3))
    rhs = displacement[1:] - displacement[0]
    finite(matrix, "cubic power design")
    finite(rhs, "cubic displacement differences")
    q, r = np.linalg.qr(matrix, mode="reduced")
    coefficients = np.linalg.solve(r, q.T @ rhs)
    finite(coefficients, "cubic coefficients")
    for i in range(len(evaluation)):
        evaluation[i] -= samples[0]
    evaluation_design = np.column_stack((evaluation, evaluation**2, evaluation**3))
    finite(evaluation_design, "cubic evaluation powers")
    evaluated = displacement[0] + evaluation_design @ coefficients
    finite(evaluated, "cubic evaluated displacement")
    event(
        trace,
        "cubic-fit",
        t,
        d,
        scope=scope,
        sample_timestamps_before=sample_before,
        sample_timestamps_after=samples,
        evaluation_timestamps_before=evaluation_before,
        evaluation_timestamps_after=evaluation,
        sample_displacements_xy=displacement,
        matrix=matrix,
        coefficients=coefficients,
        evaluated_xy=evaluated,
    )
    return evaluated
