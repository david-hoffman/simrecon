"""Portable subset of the accepted bead and revised cell score definitions."""

from typing import Any

import numpy as np

N, Z, PITCH, DZ = 128, 32, 0.04, 0.125


def axis(n, spacing):
    """Return the signed coordinate labels of a fixed grid."""
    return (np.arange(n) - n // 2) * spacing


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
    """Convert degrees to a lateral unit direction."""
    return np.array([np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))])


def path_points(path, t):
    """Sample a frozen quadratic path."""
    _, start, bend, end, _ = path
    t = np.asarray(t)[..., None]
    return (1 - t) ** 2 * np.array(start) + 2 * (1 - t) * t * np.array(bend) + t * t * np.array(end)


CLUSTER_CENTERS = {
    "northeast": (
        (1.18, 2.49, 0.625),
        (1.63, 2.68, 0.625),
        (1.91, 2.34, 0.625),
        (2.22, 2.77, 0.625),
        (2.7, 2.96, 0.625),
        (2.48, 2.33, 0.625),
    ),
    "southwest": (
        (-2.66, -2.12, -0.75),
        (-2.36, -2.55, -0.75),
        (-2.72, -2.84, -0.75),
        (-1.95, -2.77, -0.75),
        (-1.54, -2.62, -0.75),
        (-1.7, -2.19, -0.75),
        (-1.25, -2.37, -0.75),
    ),
}
CLUSTER_SHOULDER = {"northeast": 0.22, "southwest": -0.22}

GXY, GZ = axis(2 * N, PITCH), axis(Z, DZ)
BEAD_STEP = 0.005
PAIR_PROMINENCE = 0.15
PAIR_MIN_DISTANCE = 0.10
MIN_PEAK_SU = 0.005
ISO_CORE = 0.16
# Projection is the signed line profile through each catalogue center.
LATERAL_T = np.arange(-140, 141) * BEAD_STEP
AXIAL_T = np.arange(-7, 8) * DZ
CELL_SLICES = dict(xy_z_um=[-0.75, -0.375, 0.25, 0.625], xz_y_um=[-0.52, 0.44, 1.72])


def interpolate(image, xyz):
    """Trilinear samples at signed physical coordinates, without extension."""
    xyz = np.asarray(xyz)
    bins = (xyz[..., ::-1] - np.array([GZ[0], GXY[0], GXY[0]])) / [DZ, PITCH, PITCH]
    index = np.floor(bins).astype(int)
    assert np.all(index >= 0) and np.all(index + 1 < image.shape)
    frac = bins - index
    result = np.zeros(index.shape[:-1])
    for oz, oy, ox in np.ndindex(2, 2, 2):
        offset = np.array([oz, oy, ox])
        weight = np.prod(np.where(offset, frac, 1 - frac), axis=-1)
        result += weight * image[tuple(np.moveaxis(index + offset, -1, 0))]
    return result


def extrema(v):
    """Find leftmost maxima on any flat top."""
    # A flat top has one peak at its left edge, with ambiguity exposed by width.
    return np.flatnonzero((v[1:-1] > v[:-2]) & (v[1:-1] >= v[2:])) + 1


def crossings(t, v, peak):
    """First bracketing half-height crossing on either side; retain nulls."""
    h = v[peak] / 2
    lower = np.flatnonzero(v[:peak] <= h)
    upper = np.flatnonzero(v[peak + 1 :] <= h)
    if not len(lower) or not len(upper):
        return None
    i, j = lower[-1], peak + 1 + upper[0]
    if v[peak] < MIN_PEAK_SU:
        return None
    left = t[i] + (t[i + 1] - t[i]) * (h - v[i]) / (v[i + 1] - v[i])
    right = t[j - 1] + (t[j] - t[j - 1]) * (h - v[j - 1]) / (v[j] - v[j - 1])
    return [float(left), float(right)]


def pair_rule(t, v, truth_separation) -> dict[str, Any]:
    """Classify a pair or detect a false split under the accepted rule."""
    window = abs(t) <= (truth_separation / 2 + 0.12 if truth_separation else ISO_CORE)
    peaks = [p for p in extrema(v) if window[p] and v[p] >= MIN_PEAK_SU]
    peaks.sort(key=lambda p: (-v[p], p))
    result: dict[str, Any] = dict(
        status="unresolved",
        reason="fewer than two eligible maxima",
        peaks_um=[],
        separation_um=None,
        separation_error_um=None,
        position_errors_um=None,
        valley_dip_fraction=None,
    )
    if len(peaks) < 2:
        return result
    left, right = sorted(peaks[:2])
    low = min(v[left], v[right])
    valley = np.min(v[left : right + 1])
    dip = float((low - valley) / low)
    separation = float(t[right] - t[left])
    result.update(peaks_um=[float(t[left]), float(t[right])], valley_dip_fraction=dip)
    if separation + 1e-12 < PAIR_MIN_DISTANCE:
        result["reason"] = "peak spacing below 0.10 µm"
    elif dip < PAIR_PROMINENCE:
        result["reason"] = "valley drop below 15% of weaker height"
    elif truth_separation and (
        not t[left] < 0 < t[right]
        or max(abs(t[left] + truth_separation / 2), abs(t[right] - truth_separation / 2)) > 0.12
    ):
        result["reason"] = "peaks miss ordered truth neighborhoods"
    else:
        result.update(
            status="resolved" if truth_separation else "false-split",
            reason=None,
            separation_um=separation,
            separation_error_um=separation - truth_separation if truth_separation else None,
            position_errors_um=[
                float(t[left] + truth_separation / 2),
                float(t[right] - truth_separation / 2),
            ]
            if truth_separation
            else None,
        )
    return result


def shape_profile(
    t, v, core, baseline_start, baseline_end, side_start, side_end
) -> tuple[np.ndarray, dict[str, Any]]:
    """Measure signed baseline-relative width and sidelobes."""
    background = (abs(t) >= baseline_start - 1e-12) & (abs(t) <= baseline_end + 1e-12)
    baseline = float(np.median(v[background]))
    signed = v - baseline
    window = np.flatnonzero(abs(t) <= core + 1e-12)
    peak = window[np.argmax(signed[window])]
    sides = signed[(abs(t) >= side_start - 1e-12) & (abs(t) <= side_end + 1e-12)]
    limits = crossings(t, signed, peak)
    return signed, dict(
        peak_offset_um=float(t[peak]),
        peak_height_su=float(signed[peak]),
        baseline_su=baseline,
        half_height_crossings_um=limits,
        fwhm_um=limits[1] - limits[0] if limits is not None else None,
        sidelobe_min_su=float(sides.min()),
        sidelobe_max_su=float(sides.max()),
        sidelobe_min_over_peak=float(sides.min() / signed[peak])
        if signed[peak] >= MIN_PEAK_SU
        else None,
        sidelobe_max_over_peak=float(sides.max() / signed[peak])
        if signed[peak] >= MIN_PEAK_SU
        else None,
    )


def bead_scores(image):
    """Measure accepted bead profiles on their physical windows."""
    scores = {}
    for label, x, y, z, angle, dist in OBJECTS:
        xy = np.array([x, y])
        trace = xy + LATERAL_T[:, None] * unit(angle)
        profile = interpolate(image, np.column_stack((trace, np.full(len(trace), z))))
        center = np.array([x, y, z])
        signed, lateral = shape_profile(LATERAL_T, profile, ISO_CORE, 0.575, 0.70, 0.25, 0.55)
        pair = pair_rule(LATERAL_T, signed, dist)
        if dist:
            # Single-peak width is not a pair property.
            scores[label] = dict(
                pair,
                truth_separation_um=dist,
                baseline_su=lateral["baseline_su"],
                profile_su=profile.tolist(),
            )
            continue
        transverse = xy + LATERAL_T[:, None] * unit(angle + 90)
        cross = interpolate(image, np.column_stack((transverse, np.full(len(trace), z))))
        signed_cross, other = shape_profile(LATERAL_T, cross, ISO_CORE, 0.575, 0.70, 0.25, 0.55)
        ax = interpolate(image, center + AXIAL_T[:, None] * [0, 0, 1])
        _, axial = shape_profile(AXIAL_T, ax, 0.25, 0.75, 0.875, 0.375, 0.625)
        scores[label] = dict(
            lateral=lateral,
            transverse=other,
            axial=axial,
            lateral_false_split=pair,
            transverse_false_split=pair_rule(LATERAL_T, signed_cross, 0),
            profiles_su=dict(
                lateral=profile.tolist(), transverse=cross.tolist(), axial=ax.tolist()
            ),
        )
    return scores


def disk_offsets(radius, step):
    """Return the fixed sampling offsets in a disk."""
    v = np.arange(-int(radius / step), int(radius / step) + 1) * step
    xx, yy = np.meshgrid(v, v)
    return np.column_stack(
        (xx[(xx * xx + yy * yy) <= radius**2], yy[(xx * xx + yy * yy) <= radius**2])
    )


def cell_landmarks():
    """Return the accepted original and corrected-cell physical landmarks."""
    nuclear_xy = np.array([-0.96, 0.44]) + disk_offsets(0.36, PITCH)
    result = {
        "nuclear-interior": np.column_stack((nuclear_xy, np.full(len(nuclear_xy), RIM_Z))),
        "nuclear-rim": np.column_stack((RIM, np.full(len(RIM), RIM_Z))),
        "puncta": np.array(PUNCTA),
        "puncta-shoulder": np.array(PUNCTA) + [0.22, 0.14, 0.0],
        "diffuse-cytoplasm": np.array(
            [[2.05, 0.37, -0.20], [-1.77, -1.20, 0.22], [-0.22, 2.36, 0.38]]
        ),
    }
    for path in PATHS:
        t = np.linspace(0.16, 0.90, 12)
        xy = path_points(path, t)
        tangent = path_points(path, t + 0.001) - path_points(path, t - 0.001)
        normal = tangent[:, ::-1] * [-1, 1]
        normal /= np.linalg.norm(normal, axis=1)[:, None]
        z = np.full(len(t), path[-1])
        result[path[0]] = np.column_stack((xy, z))
        result[path[0] + "-shoulder"] = np.column_stack((xy + 0.21 * normal, z))
    for name, centers in CLUSTER_CENTERS.items():
        points = np.array(centers)
        result[name] = points
        result[f"{name}-shoulder"] = points + [0.0, CLUSTER_SHOULDER[name], 0.0]
    return result


def landmark_scores(image, truth):
    """Measure the accepted rim, branch, puncta and cluster windows."""
    values = {}
    for label, points in cell_landmarks().items():
        reference = interpolate(truth, points)
        observation = interpolate(image, points)
        delta = observation - reference
        values[label] = dict(
            mean_su=float(observation.mean()),
            signed_bias_su=float(delta.mean()),
            rms_su=float(np.sqrt(np.mean(delta**2))),
            profile_su=observation.tolist(),
        )
    contrasts = {}
    pairs = [("nuclear-rim", "nuclear-interior"), ("puncta", "puncta-shoulder")]
    pairs.extend((p[0], p[0] + "-shoulder") for p in PATHS)
    pairs.extend((name, f"{name}-shoulder") for name in CLUSTER_CENTERS)
    for signal, background in pairs:
        contrasts[signal] = values[signal]["mean_su"] - values[background]["mean_su"]
    return values, contrasts


def band_scores(image, truth, mask):
    """Compare signed spectra in the independently conditioned low band."""
    ref = np.fft.fftn(truth, norm="ortho")[mask]
    observed = np.fft.fftn(image, norm="ortho")[mask]
    diff = observed - ref
    ref_norm = np.linalg.norm(ref)
    if not np.isfinite(ref_norm) or ref_norm == 0:
        raise ValueError("unconditioned low-band truth")
    return dict(
        bins=int(mask.sum()),
        truth_rms_su=float(ref_norm / np.sqrt(truth.size)),
        signed_mean_error_su=float(np.mean(image - truth)),
        relative_error=float(np.linalg.norm(diff) / ref_norm),
        coherent_response=float(np.vdot(ref, observed).real / np.vdot(ref, ref).real),
        absolute_rms_error_su=float(np.linalg.norm(diff) / np.sqrt(truth.size)),
    )


def cell_scores(image, truth, mask) -> dict[str, Any]:
    """Combine the accepted conditioned low band and physical window measurements."""
    values, contrasts = landmark_scores(image, truth)
    return dict(landmarks=values, contrast_su=contrasts, low_band=band_scores(image, truth, mask))


def field_summary(image, truth):
    """Summarize signed image and image-minus-truth residuals."""
    error = image - truth
    return dict(
        range_su=[float(image.min()), float(image.max())],
        residual_range_su=[float(error.min()), float(error.max())],
        signed_mean_error_su=float(error.mean()),
        rms_error_su=float(np.sqrt(np.mean(error**2))),
        negatives=int(np.count_nonzero(image < 0)),
    )


OUTPUT_SHAPE = (Z, 2 * N, 2 * N)
BEAD_SLICES = {"xy_z_um": (-0.75, -0.50, -0.375, -0.125, 0.125, 0.375, 0.625, 0.875)}
SCORE_GAIN_SU_PER_COUNT = 2e-5


def conditioned_low_mask(reference_table):
    """Select the accepted cell low band from its independent noisy transfer."""
    q = np.fft.fftfreq(2 * N, PITCH)
    fz = np.fft.fftfreq(Z, DZ)
    radial = np.hypot(q[:, None], q[None, :])
    lateral = radial <= 1.8
    location = radial[lateral] * (128 * 0.09)
    row = np.floor(location).astype(int)
    fraction = location - row
    mask = np.zeros(OUTPUT_SHAPE, bool)
    for iz in np.flatnonzero(abs(fz) <= 0.5):
        h0 = (1 - fraction) * reference_table[0, row, iz]
        h0 += fraction * reference_table[0, row + 1, iz]
        mask[iz, lateral] = abs(h0) >= 0.08
    mask[0, 0, 0] = False
    reflection = np.ix_(*[(-np.arange(n)) % n for n in OUTPUT_SHAPE])
    if not np.array_equal(mask, mask[reflection]):
        raise ValueError("cell low-band mask is not conjugate-symmetric")
    return mask


def measure(case, image, truth, mask):
    """Return signed scientific scalars with the accepted feature definitions."""
    if image.shape != OUTPUT_SHAPE or not np.isfinite(image).all():
        raise ValueError("expected a finite signed z,y,x volume on the frozen grid")
    field = field_summary(image, truth)
    if case == "beads":
        features = bead_scores(image)
        for row in features.values():
            row.pop("profile_su", None)
            row.pop("profiles_su", None)
        return {"field": field, "beads": features}
    if case != "cell" or mask is None:
        raise ValueError("cell scores require the independent low-band mask")
    features = cell_scores(image, truth, mask)
    for row in features["landmarks"].values():
        row.pop("profile_su")
    _, reference_contrasts = landmark_scores(truth, truth)
    features["contrast_error_su"] = {
        key: value - reference_contrasts[key] for key, value in features["contrast_su"].items()
    }
    return {"field": field, "cell": features}


def slice_planes(case, image):
    """Extract each frozen plane by physical position with lateral axes unaltered."""
    windows = BEAD_SLICES if case == "beads" else CELL_SLICES
    planes = {f"xy_z={z:.3f}": image[int(round(z / DZ)) + Z // 2, :, :] for z in windows["xy_z_um"]}
    for y in windows.get("xz_y_um", ()):
        planes[f"xz_y={y:.2f}"] = image[:, int(round(y / PITCH)) + N, :]
    return planes


def display_ranges(truth, conventional):
    """Use one signed image and residual range fixed by the independent inputs."""
    extent = max(float(np.max(abs(truth))), float(np.max(abs(conventional))))
    residual = float(np.max(abs(conventional - truth)))
    if extent <= 0 or residual <= 0:
        raise ValueError("unconditioned independent display range")
    return {"signed_su": [-extent, extent], "residual_su": [-residual, residual]}


def display_planes(case, image, truth, ranges):
    """Return actual and signed residual planes plus explicit clipping counts."""
    observed = slice_planes(case, image)
    reference = slice_planes(case, truth)
    residual = {label: value - reference[label] for label, value in observed.items()}
    clipping = {
        name: {
            label: int(np.count_nonzero((plane < low) | (plane > high)))
            for label, plane in planes.items()
        }
        for name, planes in (("signed_su", observed), ("residual_su", residual))
        for low, high in (ranges[name],)
    }
    return observed, residual, clipping
