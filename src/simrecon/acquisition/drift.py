"""Selected middle-stack/within-2D correlation, cubic drift and Fourier ramps.

These implement the restricted acquisition paths, not general motion recovery.
See docs/architecture/reconstruction-walkthrough.md#selected-acquisition-extensions
(repository-relative) for placement before/after phase separation.
"""

from __future__ import annotations

import math

import numpy as np

from .layout import AcquisitionModeError, Array, ModeEvent, event, finite, signed
from .preparation import apodize_frame_edges_inplace


def signed_frequency_indices(length: int) -> Array:
    """Return unshifted signed Fourier-bin labels with positive even Nyquist.

    Parameters
    ----------
    length : int
        Positive native axis length, validated by the caller.

    Returns
    -------
    numpy.ndarray
        Owned float64 (length,) integer-valued labels: j for j<=length//2,
        otherwise j-length. Divide by length*pitch for cycles per micrometre;
        these labels themselves are dimensionless, not physical frequencies.
    """
    indices = np.arange(length, dtype=np.float64)
    return np.where(indices <= length // 2, indices, indices - length)


def build_drift_correction_ramp(displacement: Array, z: int, y: int, x: int) -> Array:
    """Build the positive Fourier multiplier correcting a measured displacement.

    Parameters
    ----------
    displacement : numpy.ndarray
        Float64 (2,) x/y detector pixels or (3,) x/y pixels and native z sections.
    z, y, x : int
        Native volume extents, with even x; independent of output zoom.

    Returns
    -------
    numpy.ndarray
        Owned complex128 (z,y,x//2+1) multiplier for three components; with two
        components its shape is (1,y,x//2+1), broadcastable over z. The factor
        is exp(+2*pi*i*(dx*kx/x+dy*ky/y+dz*kz/z)), without normalization.

    Notes
    -----
    Uses a first-sample origin and positive even Nyquist labels. The positive
    sign corrects moving samples g[n]=f[n-displacement]. Inputs are unchanged;
    no Hermitian endpoint projection or spatial interpolation is performed.
    """
    phase = displacement[0] * np.arange(x // 2 + 1)[None, None, :] / x
    phase = phase + displacement[1] * signed_frequency_indices(y)[None, :, None] / y
    if len(displacement) == 3:
        phase = phase + displacement[2] * signed_frequency_indices(z)[:, None, None] / z
    result = np.exp(2j * np.pi * phase)
    finite(result, "drift correction ramp")
    return result


def estimate_correlation_displacement(
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
    """Estimate displacement from the masked, power-weighted cross spectrum.

    Parameters
    ----------
    reference, moving : numpy.ndarray
        Complex128 (nz,ny,x//2+1) unshifted half-spectra; nz=1 for within-2D.
    x : int
        Even native detector width.
    dxy, radius : float
        Lateral pitch in micrometres and strict radial cutoff in cycles per
        micrometre. No axial support mask is applied.
    hpf, exponent : float
        Positive hpf selects the squared Gaussian high-pass factor. Cross
        magnitudes use exponent 1/4 between directions or 1/2 within 2D.
    trace : list of ModeEvent
        Appended with owned snapshots of the actual correlation/peak decisions.
    t, d, scope, moving_index, z_index : int or str or None
        Caller-supplied diagnostic context; not used as array offsets here.

    Returns
    -------
    numpy.ndarray
        Owned float64 (3,) displacement in x/y detector pixels and native axial
        sections; axial displacement is zero for nz=1. Inputs stay unchanged.

    Notes
    -----
    Forms conj(reference)*moving only inside the strict radial mask, then uses
    an unnormalized positive-exponential real inverse. Peaks and periodic
    parabolic neighbors use absolute real correlation, not a complex modulus.
    Strict z/y/x scanning keeps the first nonzero maximum; all-zero maps retain
    the initialized center. Refinement precedes strict-half wrapping, leaving
    the even half-length endpoint positive. This is a selected estimator, not
    a guarantee of identifiable or physically valid motion.
    """
    nz, ny, _ = reference.shape
    radial = np.hypot(
        np.arange(x // 2 + 1)[None, :] / (x * dxy),
        signed_frequency_indices(ny)[:, None] / (ny * dxy),
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


def estimate_between_direction_drift(
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
    """Estimate between-direction drift from the selected raw middle stack.

    Parameters
    ----------
    images, off : numpy.ndarray or None
        Raw on (T,D,P,Z,Y,X) and optional off (T,D,P,Z,N,Y,X) arrays.
    background : numpy.ndarray
        Current float64 (Y,X) background map in detector counts.
    t : int
        Time selected before its ordinary camera loading.
    dxy, dz : float
        Positive native pitches in micrometres, including dz for the computed
        but unused axial optical cutoff.
    wavelength, na, immersion, hpf : int or float
        Wavelength in nanometres, numerical aperture, immersion index and
        high-pass fraction. The caller validates this selected optical path.
    trace : list of ModeEvent
        Appended with prepass and actual correlation snapshots.

    Returns
    -------
    numpy.ndarray
        Owned float64 (D,3) x/y pixel and native-z-section displacements relative
        to direction zero, whose vector remains zero.

    Notes
    -----
    Uses max(Z//2,1) middle sections, phase averaging and 1/(X*Y*Z), then fixed
    width10 edges and unnormalized negative forward transforms. Only off
    exposure zero is included. Sentinel replacement is local: background maps,
    slope and on-offset carry are not modified or applied. Quarter-power
    correlation measures native sections without a Z/subz rescaling. Caller
    safety checks require X,Y>=10 and terminate the off loop only for N<=Y+1.
    """
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
            apodize_frame_edges_inplace(centers[d, h], 10)
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
        result[d] = estimate_correlation_displacement(
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


def fit_cubic_drift_inplace(
    samples: Array,
    evaluation: Array,
    displacement: Array,
    *,
    scope: str,
    trace: list[ModeEvent],
    t: int,
    d: int,
) -> Array:
    """Fit unweighted cubic x/y drift while mutating timestamp vectors in order.

    Parameters
    ----------
    samples, evaluation : numpy.ndarray
        Mutable float64 timestamp vectors (n,) and (n_eval,) in a common time
        unit. They may alias; n>=4 with three distinct nonzero relative times.
    displacement : numpy.ndarray
        Float64 (n,2) measured x/y displacements in detector pixels.
    scope, trace, t, d : str, list of ModeEvent, int
        Diagnostic scope, appended owned snapshots and actual caller context.

    Returns
    -------
    numpy.ndarray
        Owned float64 (n_eval,2) fitted x/y displacements in detector pixels.

    Notes
    -----
    Subtract samples[0] from sample entries 1 onward; fit powers 1,2,3 to
    displacement-displacement[0] by QR, without a fitted constant. Then subtract
    the current samples[0] from each evaluation entry in sequence. If vectors
    alias, evaluation[0] sets that shared origin to zero, so later entries are
    not shifted twice. A distinct 3D header-prefix view stays mutated for later
    times; the caller subtracts measured direction midpoints after this fit.
    Inputs other than the two timestamp vectors remain unchanged. No smoothing,
    clock inference or condition-number cutoff is added.
    """
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
