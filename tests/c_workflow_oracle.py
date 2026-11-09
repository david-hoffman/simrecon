"""Independent CE07 finite observer, specified from the allowed public contracts.

No product imports. Deliberately uses dense finite Fourier matrices, scalar
stencils and explicit traversal instead of the product's numerical backends.
All fixture definitions and error-budget rules precede product observations.
"""

from __future__ import annotations

import copy
import hashlib
import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

import numpy as np

U = 2.0**-53
OPTICS = {"wavelength_nm": 500, "numerical_aperture": 1.0, "immersion_index": 1.0}
LIMITS = (
    "mathematical-source-target-only",
    "historical-binary-agreement-unqualified",
    "recovery-and-resolution-unqualified",
    "selected-channel-independent-state",
    "external-IVE-file-binding-unqualified",
    "input-unit-label-not-specimen-mass",
)
ACQ_DEFAULTS = dict(
    flatfield_slope=None,
    phases_rad=None,
    phase_steps_rad=None,
    edge_pixels=10,
    equalize=True,
    equalize_z=False,
    equalize_time=False,
    storage_order="direction-major",
    combine_off_orders=None,
    drift_between=False,
    drift_within=False,
    fit_drift=False,
    adjust_phases=False,
    drift_filter_fraction=0.0,
)
CARRIER_DEFAULTS = dict(
    phase_start_angle_rad=1.57193,
    negative_angle_step=False,
    angles_rad=None,
    search_carriers=True,
    use_time0_carriers=True,
    amplitude_floors=None,
    fit_all_phases=True,
)
FILTER_DEFAULTS = dict(
    wiener_increment=0.0,
    suppress_singularities=True,
    suppression_radius_bins=10.0,
    dampen_order0=False,
    omit_order0=False,
    omit_kz0=False,
    output_taper="cosine",
    power_taper_exponent=None,
    precise_taper=False,
    filter_overlaps=True,
    explode_factor=1.0,
)
BEAD_DEFAULTS = dict(
    bead_diameter_um=0.12,
    carrier_angle_rad=0.0,
    background_counts=None,
    background_map=None,
    slope_map=None,
    exposure_background_counts=None,
    compensate_bead=True,
    fix_axial_axis=True,
    fix_radial_from=0,
    cleanup_axial_bins=(0, 0, 0),
    origin_fit_bins=None,
    rescale_each=False,
    forced_pi_shift=False,
    conjugate=False,
)


def gamma(n: int) -> float:
    return n * U / (1 - n * U)


def lift(j: int, n: int) -> int:
    return j if j <= n // 2 else j - n


def finite_transform(a: np.ndarray, axes: tuple[int, ...], sign: int) -> np.ndarray:
    """Unnormalized sums; no FFT and no inverse normalization."""
    out = np.asarray(a, dtype=np.complex128)
    for axis in axes:
        n = out.shape[axis]
        j = np.arange(n, dtype=float)
        matrix = np.exp(sign * 2j * np.pi * np.outer(j, j) / n)
        out = np.moveaxis(np.tensordot(matrix, out, axes=(1, axis)), 0, axis)
    return out


def array_digest(a: np.ndarray) -> tuple[tuple[int, ...], str, str]:
    dtype = a.dtype.newbyteorder("<")
    data = np.asarray(a, dtype=dtype).tobytes(order="C")
    return a.shape, dtype.str, hashlib.sha256(data).hexdigest()


def edge(a: np.ndarray, width: int, *, bead: bool = False) -> np.ndarray:
    y, x = a.shape
    if width == -1:
        return a * np.outer(
            np.sin(np.pi * (np.arange(y) + 0.5) / y), np.sin(np.pi * (np.arange(x) + 0.5) / x)
        )
    if width < -1:
        return a.copy()
    padded = np.zeros((y, x + 2), dtype=float)
    padded[:, :x] = a
    for ix in range(x):
        delta = (padded[y - 1, ix] - padded[0, ix]) / 2
        for k in range(width):
            h = 1 - math.sin(np.pi * (k + 0.5) / (2 * width))
            padded[k, ix] += delta * h
            padded[y - 1 - k, ix] -= delta * h
    flat = padded.ravel()
    for iy in range(y):
        delta = (padded[iy, x - 1] - padded[iy, 0]) / 2
        for k in range(width):
            h = 1 - math.sin(np.pi * (k + 0.5) / (2 * width))
            flat[iy * (x + 2) + k] += delta * h
            flat[iy * (x + 2) + (y if bead else x) - 1 - k] -= delta * h
    return padded[:, :x].copy()


def phase_matrix(phases: np.ndarray, orders: int, uniform: bool) -> tuple[np.ndarray, np.ndarray]:
    p = len(phases)
    rows = [np.ones(p)]
    for m in range(1, orders):
        rows.extend((np.cos(m * phases), np.sin(m * phases)))
    matrix = np.asarray(rows)
    if uniform:
        return matrix, np.ones(orders)
    design = matrix.T.copy() / p
    design[:, 1:] *= 2
    # SVD-based least squares is independent of the contract's normal-equation
    # presentation, with the same uniquely defined left inverse.
    matrix = np.linalg.lstsq(design, np.eye(p), rcond=None)[0]
    variance = [np.sum(matrix[0] ** 2) / p]
    for m in range(1, orders):
        variance.append(np.sum(matrix[2 * m - 1 : 2 * m + 1] ** 2) / p)
    return matrix, np.asarray(variance)


@dataclass
class Table:
    """Hold independent order-major coefficients and explicit frequency steps."""

    samples: np.ndarray
    layout: str = "radial"
    dkr: float = 0.25
    dkz: float = 0.5

    def sample(self, kx: float, ky: float, z: int, native_dkz: float, m: int) -> complex:
        values = self.samples[m]
        t = z * native_dkz / self.dkz
        conjugate = False
        if self.layout == "radial":
            r, k = values.shape
            u = math.hypot(kx, ky) / self.dkr
            if t < 0:
                t += k
            i, j = math.floor(u), math.floor(t)
            a, b = u - i, t - j
            j1 = 0 if j == k - 1 else j + 1
            offsets = (i * k + j, i * k + j1, (i + 1) * k + j, (i + 1) * k + j1)
            assert all(0 <= v < r * k for v in offsets), ("unsafe radial observer stencil", offsets)
            v00, v01, v10, v11 = values.ravel()[list(offsets)]
            return complex((1 - a) * ((1 - b) * v00 + b * v01) + a * ((1 - b) * v10 + b * v11))
        k, y, x = values.shape
        u, v = kx / self.dkr, ky / self.dkr
        if u < 0:
            u, v, t = -u, -v, -t
            conjugate = True
        if v < 0:
            v += y
        if t < 0:
            t += k
        i, j, axial = math.floor(u), math.floor(v), math.floor(t)
        a, b, c = u - i, v - j, t - axial
        j1, l1 = (j + 1) % y, (axial + 1) % k
        total = 0j
        for iz, wz in ((axial, 1 - c), (l1, c)):
            for iy, wy in ((j, 1 - b), (j1, b)):
                for ix, wx in ((i, 1 - a), (i + 1, a)):
                    index = iz * y * x + iy * x + ix
                    assert 0 <= index < k * y * x, ("unsafe full observer stencil", index)
                    total += values.ravel()[index] * wz * wy * wx
        return complex(total.conjugate() if conjugate else total)


@dataclass
class Case:
    """Declare raw observations and settings before any product observation."""

    raw: np.ndarray
    acquisition: dict[str, Any]
    carrier: dict[str, Any]
    filtering: dict[str, Any]
    table: Table
    extras: dict[str, Any] = field(default_factory=dict)
    bead: tuple[np.ndarray, dict[str, Any]] | None = None
    name: str = "control"

    def resolved(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        return (
            ACQ_DEFAULTS | self.acquisition,
            CARRIER_DEFAULTS | self.carrier,
            FILTER_DEFAULTS | self.filtering,
        )


def constant_case(*, complex_table: bool = False, mode: str = "3d", times: int = 1) -> Case:
    z = 1 if mode == "2d" else 2
    raw = np.empty((times, 1, 3, z, 2, 4), dtype=np.float64)
    for t in range(times):
        raw[t, 0] = np.asarray([6 + t, 3, 3])[:, None, None, None]
    h = np.ones((2, 8, z), dtype=np.complex128)
    if complex_table:
        h[1] += 1j * np.arange(8)[:, None]
    return Case(
        raw,
        dict(
            acquisition_mode=mode,
            dxy_um=1.0,
            dz_um=1.0,
            norders=2,
            background=0.0,
            lateral_zoom=1.0,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        dict(linespacing_um=8.0, phase_start_angle_rad=0.0, search_carriers=False),
        dict(wiener=1.0, suppress_singularities=False, output_taper="none"),
        Table(h, dkz=1.0 / z),
        name="constant-complex" if complex_table else "constant-unit",
    )


def patterned_case(
    *,
    mode: str = "3d",
    directions: int = 3,
    times: int = 2,
    y: int = 10,
    x: int = 10,
    orders: int = 3,
) -> Case:
    """Integer observations, no shared forward model, no random seed selection."""
    z = 1 if mode == "2d" else 2
    p = 2 * orders - 1
    t0, d, ph, zz, yy, xx = np.indices((times, directions, p, z, y, x))
    raw = (
        80
        + 7 * t0
        + 3 * d
        + 2 * ph
        + zz
        + ((xx * xx + 3 * yy + ph * xx + 2 * d * yy) % 17)
        + (xx == (2 + ph) % x) * 9
        + (yy == (3 + d) % y) * 5
    ).astype(np.float64)
    h = np.empty((orders, 24, z), dtype=np.complex128)
    for m in range(orders):
        r, k = np.indices(h[m].shape)
        h[m] = (1 + m / 4 + r / 32) + 1j * (m * r / 64 + k / 16)
    return Case(
        raw,
        dict(
            acquisition_mode=mode,
            dxy_um=1.0,
            dz_um=1.0,
            norders=orders,
            background=3.0,
            lateral_zoom=1.0,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        dict(linespacing_um=9.0, phase_start_angle_rad=0.21, search_carriers=False),
        dict(wiener=0.4, wiener_increment=0.2, suppress_singularities=False, output_taper="none"),
        Table(h, dkr=0.125, dkz=1 / z),
        name=f"pattern-{mode}",
    )


def b2_cases() -> dict[str, Case]:
    """Four-order 2D recurrence on known, searched and time0-reused fits.

    Integer raw construction is patterned_case's fixed polynomial/modular
    formula. No original control, data choice or numerical model is changed.
    """
    cases = {}
    for route in ("known", "searched-reused"):
        case = patterned_case(mode="2d", directions=1, times=2, orders=4)
        case.carrier["search_carriers"] = route == "searched-reused"
        case.name = f"b2-four-orders-{route}"
        cases[case.name] = case
    return cases


def b3_cases() -> dict[str, Case]:
    """Minimal declarations and the six explicitly supplied default values.

    Raw observations retain patterned_case's fixed integer formula. Required
    acquisition, optics, carrier spacing and Wiener settings stay declared.
    Omission is passed to the workflow; only our observer resolves its values.
    """
    case = patterned_case(directions=1, times=2)
    required = (
        "acquisition_mode",
        "dxy_um",
        "dz_um",
        "norders",
        "background",
        "lateral_zoom",
        "axial_zoom",
        "phase_policy",
    )
    case.acquisition = {key: case.acquisition[key] for key in required}
    case.carrier = {"linespacing_um": case.carrier["linespacing_um"]}
    case.filtering = {"wiener": case.filtering["wiener"]}
    case.name = "b3-omitted-defaults"
    explicit = copy.deepcopy(case)
    explicit.name = "b3-explicit-defaults"
    explicit.acquisition.update(edge_pixels=10, equalize=True)
    explicit.carrier.update(phase_start_angle_rad=1.57193, search_carriers=True)
    explicit.filtering.update(suppress_singularities=True, output_taper="cosine")
    return {case.name: case, explicit.name: explicit}


def bead_fixture(
    *, z: int = 1, y: int = 32, x: int = 32, phases: int = 3
) -> tuple[np.ndarray, dict[str, Any]]:
    raw = np.zeros((phases, z, y, x), dtype=np.float64)
    for p in range(phases):
        for iz in range(z):
            raw[p, iz, y // 2, x // 2] = 3 * (p + 1) * (iz + 1)
            raw[p, iz, y // 2, x // 2 + 2] = (p + 1) * (iz + 1)
            # Asymmetry changes by phase: not a scalar copy of one bead.
            raw[p, iz, y // 2 + 1, x // 2 - 1] = (p % 2) * (iz + 1)
    settings = dict(
        dxy_um=0.25,
        dz_um=0.75,
        linespacing_um=3.0,
        **OPTICS,
        background_counts=0.0,
        compensate_bead=False,
        fix_axial_axis=False,
    )
    return raw, settings


def initial_vectors(case: Case) -> tuple[np.ndarray, np.ndarray]:
    a, c, _ = case.resolved()
    d, p = case.raw.shape[1:3]
    angle = (
        c["phase_start_angle_rad"]
        + np.arange(d) * (-1 if c["negative_angle_step"] else 1) * np.pi / d
    )
    phase = np.column_stack((np.cos(angle), np.sin(angle))) / c["linespacing_um"]
    if c["angles_rad"] is not None:
        angle = c["angles_rad"]
    magnitude = 1 / c["linespacing_um"] / (1 if a["acquisition_mode"] == "2d" else p // 2)
    return magnitude * np.column_stack((np.cos(angle), np.sin(angle))), phase


def reinterpret(case: Case) -> Case:
    if case.extras.get("plane_policy", "native") == "native":
        return case
    result = copy.deepcopy(case)
    result.extras["plane_policy"] = "native"
    t, d, p, z, y, x = case.raw.shape
    result.raw = np.empty((t * z, d, p, 1, y, x))
    for it in range(t):
        for q in range(z):
            for dn in range(d):
                od, oz = (
                    (dn, q)
                    if case.acquisition.get("storage_order", "direction-major") == "z-major"
                    else divmod(q * d + dn, z)
                )
                result.raw[it * z + q, dn, :, 0] = case.raw[it, od, :, oz]
    for key in ("off_exposures", "exposure_background"):
        if key in case.extras:
            source = case.extras[key]
            shape = (t * z, d, p, 1, *source.shape[4:])
            target = np.empty(shape, dtype=source.dtype)
            for it in range(t):
                for q in range(z):
                    for dn in range(d):
                        od, oz = (
                            (dn, q)
                            if case.acquisition.get("storage_order", "direction-major") == "z-major"
                            else divmod(q * d + dn, z)
                        )
                        target[it * z + q, dn, :, 0] = source[it, od, :, oz]
            result.extras[key] = target
    return result


def peak_offset(values: np.ndarray) -> tuple[float, str]:
    lo, mid, hi = (float(v) for v in values)
    curvature = hi + lo - 2 * mid
    if curvature == 0:
        return 0.0, "zero-curvature"
    result = -(hi - lo) / 2 / curvature
    return (0.0, "outside-range") if abs(result) > 1.5 else (result, "fitted")


def drift_correlate(
    reference: np.ndarray, moving: np.ndarray, case: Case, exponent: float
) -> tuple[np.ndarray, dict[str, Any]]:
    a, _, _ = case.resolved()
    z, y, xh = reference.shape
    x = (xh - 1) * 2
    rd = 2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000)
    cross = np.zeros_like(reference)
    for iy in range(y):
        for ix in range(xh):
            r = math.hypot(ix / (x * a["dxy_um"]), lift(iy, y) / (y * a["dxy_um"]))
            if r < rd:
                c = reference[:, iy, ix].conj() * moving[:, iy, ix]
                value = np.abs(c) ** exponent * np.exp(1j * np.angle(c))
                hpf = a["drift_filter_fraction"]
                if hpf > 0:
                    value *= (1 - math.exp(-((r / (hpf * rd)) ** 2))) ** 2
                cross[:, iy, ix] = value
    full = np.empty((z, y, x), dtype=complex)
    for iz, iy, ix in np.ndindex(full.shape):
        full[iz, iy, ix] = (
            cross[iz, iy, ix] if ix <= x // 2 else cross[-iz % z, -iy % y, x - ix].conj()
        )
    corr = np.real(finite_transform(full, (0, 1, 2), 1))
    absolute = abs(corr)
    if np.max(absolute) == 0:
        iz, iy, ix = z // 2, y // 2, x // 2
    else:
        iz, iy, ix = np.unravel_index(np.argmax(absolute), absolute.shape)
    neighbors = np.array(
        [
            [absolute[iz, iy, (ix + k) % x] for k in (-1, 0, 1)],
            [absolute[iz, (iy + k) % y, ix] for k in (-1, 0, 1)],
            [absolute[(iz + k) % z, iy, ix] for k in (-1, 0, 1)],
        ]
    )
    offsets = [peak_offset(row)[0] for row in neighbors]
    if z == 1:
        offsets[2] = 0.0
    positions = np.array([ix, iy, iz]) + offsets
    for axis, n in enumerate((x, y, z)):
        if positions[axis] > n // 2:
            positions[axis] -= n
    return positions, dict(
        cross_spectrum=cross,
        correlation=corr,
        neighbors_xyz=neighbors,
        integer_peak_xyz=(int(ix), int(iy), int(iz)),
        reference_fourier=reference.copy(),
        moving_fourier=moving.copy(),
        exponent=exponent,
    )


def cubic(
    samples: np.ndarray, values: np.ndarray, evaluation: np.ndarray, *, alias: bool = False
) -> dict[str, np.ndarray]:
    tau = samples.copy()
    eta = tau if alias else evaluation.copy()
    tau[1:] -= tau[0]
    design = np.column_stack([tau[1:] ** j for j in (1, 2, 3)])
    coefficients = np.linalg.lstsq(design, values[1:] - values[0], rcond=None)[0]
    for i in range(len(eta)):
        eta[i] -= tau[0]
    evaluated = values[0] + np.column_stack([eta**j for j in (1, 2, 3)]) @ coefficients
    return dict(
        matrix=design,
        sample_displacements_xy=values.copy(),
        coefficients=coefficients,
        evaluated_xy=evaluated,
        sample_timestamps_after=tau.copy(),
        evaluation_timestamps_after=eta.copy(),
    )


def prepare(case: Case) -> dict[str, Any]:
    case = reinterpret(case)
    a, c, _ = case.resolved()
    raw = case.raw
    t, d, p, z, y, x = raw.shape
    orders = a["norders"]
    q = 2 * orders - 1
    off = case.extras.get("off_exposures")
    n = 0 if off is None else off.shape[4]
    extra = case.extras.get("exposure_background", np.zeros((t, d, p, z)))
    alpha = 1 / (x * y * z * a["lateral_zoom"] ** 2 * a["axial_zoom"] * d)
    bg = np.broadcast_to(a["background"], (y, x)).astype(float).copy()
    slope = np.ones((y, x)) if a["flatfield_slope"] is None else a["flatfield_slope"].copy()
    bands = np.zeros((t, d, q, z, y, x // 2 + 1), dtype=complex)
    off_bands = None if n == 0 else np.zeros_like(bands)
    sums = np.zeros((t, d, p, z))
    off_sums = np.zeros_like(sums)
    gains, off_gains = np.ones_like(sums), np.ones_like(sums)
    matrices = np.zeros((t, d, z, q, p))
    phases_all = np.zeros((t, d, z, p))
    noises = np.zeros((t, d, orders))
    between = np.zeros((t, d, 3))
    exposure = np.zeros((t, d, z, p, 2))
    timestamps = case.extras.get("header_timestamps")
    timestamps = None if timestamps is None else timestamps.copy()
    events: list[dict[str, Any]] = []
    sentinels: list[tuple[int, ...]] = []
    previous_offset = 0.0
    on_edge = np.zeros((t, d, z, p, y, x))
    off_edge = None if n == 0 else np.zeros_like(on_edge)
    before_ramp = np.zeros((t, d, z, p, y, x // 2 + 1), dtype=complex)
    off_before_ramp = None if n == 0 else np.zeros_like(before_ramp)
    after_ramp = np.zeros_like(before_ramp)
    off_after_ramp = None if n == 0 else np.zeros_like(before_ramp)
    separated = np.zeros_like(bands)
    off_separated = None if n == 0 else np.zeros_like(bands)
    pre_axial = np.zeros_like(bands)
    prepass_backgrounds = np.zeros((t, y, x))
    mixtures: list[dict[str, Any]] = []
    _, linkage = initial_vectors(case)
    xx, yy = np.meshgrid(np.arange(x // 2 + 1) / x, np.array([lift(j, y) for j in range(y)]) / y)

    def load(frame: np.ndarray, offset: float, index: tuple[int, ...]) -> np.ndarray:
        frame = frame.copy()
        if frame[-1, -1] == -1:
            frame[-1, -1] = frame[-1, -2]
            bg[-1, -1] = bg[-1, -2]
            slope[-1, -1] = 1
            sentinels.append(index)
        return alpha * slope * (frame - bg - offset)

    for it in range(t):
        prepass_backgrounds[it] = bg
        if (a["drift_between"] or a["drift_within"]) and a["storage_order"] == "direction-major":
            subz = max(z // 2, 1)
            first = (z - subz) // 2
            centers = np.zeros((d, subz, y, x))
            for di in range(d):
                for h in range(subz):
                    for ph in range(p):
                        frame = raw[it, di, ph, first + h].copy()
                        if frame[-1, -1] == -1:
                            frame[-1, -1] = frame[-1, -2]
                        centers[di, h] += (frame - bg) / (p * x * y * z)
                        if off is not None:
                            frame = off[it, di, ph, first + h, 0].copy()
                            if frame[-1, -1] == -1:
                                frame[-1, -1] = frame[-1, -2]
                            centers[di, h] += (frame - bg) / (p * x * y * z)
                    centers[di, h] = edge(centers[di, h], 10)
            fourier = finite_transform(centers, (1, 2, 3), -1)[..., : x // 2 + 1]
            for di in range(1, d):
                between[it, di], diagnostic = drift_correlate(fourier[0], fourier[di], case, 0.25)
                events.append(dict(kind="between", time=it, direction=di, **diagnostic))
        if a["drift_within"] and z > 1:
            assert timestamps is not None
            samples = timestamps[np.arange(d) * z * p + (z * p) // 2]
            fit = cubic(samples, between[it, :, :2], timestamps[: d * z * p])
            timestamps[: d * z * p] = fit["evaluation_timestamps_after"]
            exposure[it] = fit["evaluated_xy"].reshape(d, z, p, 2)
            exposure[it, 1:] -= between[it, 1:, None, None, :2]
            events.append(dict(kind="cubic", time=it, direction=None, **fit))
        for di in range(d):
            for zi in range(z):
                frames, off_frames = [], []
                for ph in range(p):
                    if off is not None:
                        summed = np.zeros((y, x))
                        for e in range(n):
                            summed += load(
                                off[it, di, ph, zi, e], previous_offset, (it, di, zi, ph, e)
                            )
                        off_frames.append(edge(summed, a["edge_pixels"]))
                    frames.append(
                        edge(
                            load(
                                raw[it, di, ph, zi],
                                float(extra[it, di, ph, zi]),
                                (it, di, zi, ph, n),
                            ),
                            a["edge_pixels"],
                        )
                    )
                    previous_offset = float(extra[it, di, ph, zi])
                frames = np.array(frames)
                on_edge[it, di, zi] = frames
                sums[it, di, :, zi] = np.sum(frames, axis=(1, 2))
                if a["equalize"]:
                    anchor = sums[
                        0 if a["equalize_time"] else it, 0, 0, 0 if a["equalize_z"] else zi
                    ]
                    gains[it, di, :, zi] = anchor / sums[it, di, :, zi]
                    frames *= gains[it, di, :, zi, None, None]
                lateral = finite_transform(frames, (1, 2), -1)[..., : x // 2 + 1]
                before_ramp[it, di, zi] = lateral
                off_lateral = None
                if off is not None:
                    off_frames = np.asarray(off_frames)
                    assert off_edge is not None
                    off_edge[it, di, zi] = off_frames
                    off_sums[it, di, :, zi] = np.sum(off_frames, axis=(1, 2))
                    if a["equalize"] and n > 1:
                        anchor = off_sums[
                            0 if a["equalize_time"] else it, 0, 0, 0 if a["equalize_z"] else zi
                        ]
                        off_gains[it, di, :, zi] = anchor / off_sums[it, di, :, zi]
                        off_frames *= off_gains[it, di, :, zi, None, None]
                    off_lateral = finite_transform(off_frames, (1, 2), -1)[..., : x // 2 + 1]
                    assert off_before_ramp is not None
                    off_before_ramp[it, di, zi] = off_lateral
                if a["drift_within"] and z == 1:
                    assert off_lateral is not None
                    ref = lateral[0] + off_lateral[0]
                    for ph in range(p):
                        disp, diagnostic = drift_correlate(
                            ref[None], (lateral[ph] + off_lateral[ph])[None], case, 0.5
                        )
                        exposure[it, di, zi, ph] = disp[:2]
                        events.append(
                            dict(kind="within", time=it, direction=di, phase=ph, **diagnostic)
                        )
                    if a["fit_drift"]:
                        assert timestamps is not None
                        sample = timestamps[di * p * (n + 1) + np.arange(p) * (n + 1) + n]
                        fit = cubic(sample, exposure[it, di, zi], sample, alias=True)
                        exposure[it, di, zi] = fit["evaluated_xy"]
                        events.append(dict(kind="cubic", time=it, direction=di, **fit))
                if a["drift_within"]:
                    for ph in range(p):
                        dx, dy = exposure[it, di, zi, ph]
                        ramp = np.exp(2j * np.pi * (dx * xx + dy * yy))
                        lateral[ph] *= ramp
                        if off_lateral is not None:
                            off_lateral[ph] *= ramp
                uniform = a["phase_steps_rad"] is None and a["phases_rad"] is None
                after_ramp[it, di, zi] = lateral
                if off_lateral is not None:
                    assert off_after_ramp is not None
                    off_after_ramp[it, di, zi] = off_lateral
                phases = 2 * np.pi * np.arange(p) / p
                if a["phase_steps_rad"] is not None:
                    phases = np.arange(p) * a["phase_steps_rad"][di]
                elif a["phases_rad"] is not None:
                    phases = a["phases_rad"][di].copy()
                if a["drift_within"] and a["adjust_phases"]:
                    if z == 1:
                        phases = case.extras["header_phases_rad"][
                            di * p * (n + 1) + np.arange(p) * (n + 1)
                        ].copy()
                    phases += 2 * np.pi * a["dxy_um"] * (exposure[it, di, zi] @ linkage[di])
                    uniform = False
                matrix, variance = phase_matrix(phases, orders, uniform)
                matrices[it, di, zi], phases_all[it, di, zi], noises[it, di] = (
                    matrix,
                    phases,
                    variance,
                )
                for slot in range(q):
                    bands[it, di, slot, zi, :, :-1] = np.tensordot(
                        matrix[slot], lateral[..., :-1], axes=1
                    )
                    bands[it, di, slot, zi, :, -1] = lateral[slot, :, -1]
                    if off_bands is not None and off_lateral is not None:
                        off_bands[it, di, slot, zi, :, :-1] = np.tensordot(
                            matrix[slot], off_lateral[..., :-1], axes=1
                        )
                        off_bands[it, di, slot, zi, :, -1] = off_lateral[slot, :, -1]
                separated[it, di, :, zi] = bands[it, di, :, zi]
                if off_bands is not None:
                    assert off_separated is not None
                    off_separated[it, di, :, zi] = off_bands[it, di, :, zi]
                selectors = a["combine_off_orders"]
                if selectors is not None and np.any(selectors > 0):
                    assert off_bands is not None
                    cutoff = math.trunc(
                        2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000)
                    )
                    mask = np.array(
                        [
                            [
                                math.trunc(ix / (x * a["dxy_um"])) ** 2
                                + math.trunc(lift(iy, y) / (y * a["dxy_um"])) ** 2
                                <= cutoff**2
                                for ix in range(x // 2 + 1)
                            ]
                            for iy in range(y)
                        ]
                    )
                    assert mask.any() and (~mask).any(), "fixture needs both statistic regions"
                    for m in range(orders):
                        if selectors[m] <= 0:
                            continue
                        slots = slice(0, 1) if m == 0 else slice(2 * m - 1, 2 * m + 1)
                        on = bands[it, di, slots, 0]
                        ob = off_bands[it, di, slots, 0]
                        mixtures.append(
                            dict(
                                time=it,
                                direction=di,
                                z=zi,
                                order=m,
                                on=on.copy(),
                                off=ob.copy(),
                                mask=mask.copy(),
                            )
                        )
                        power_on, power_off = (
                            np.sum(abs(on) ** 2, axis=0),
                            np.sum(abs(ob) ** 2, axis=0),
                        )
                        no, nf = np.mean(power_on[~mask]), np.mean(power_off[~mask])
                        so, sf = (
                            max(np.mean(power_on[mask]) - no, 0),
                            max(np.mean(power_off[mask]) - nf, 0),
                        )
                        if so == sf == 0:
                            so = sf = 1
                        u, v = math.sqrt(so) / no, math.sqrt(sf) / nf
                        bands[it, di, slots, 0] = (
                            u / (u + v) * on + (1 if m == 0 else -1) * v / (u + v) * ob
                        )
            pre_axial[it, di] = bands[it, di]
            if a["acquisition_mode"] == "3d":
                bands[it, di] = finite_transform(bands[it, di], (1,), -1)
            if a["drift_between"] and di > 0:
                dx, dy, dz = between[it, di]
                axial = np.asarray([lift(k, z) / z for k in range(z)])
                bands[it, di] *= np.exp(
                    2j * np.pi * (dx * xx[None] + dy * yy[None] + dz * axial[:, None, None])
                )
    return dict(
        quadratures=bands,
        noise_variance_factors=noises,
        frame_sums=sums,
        equalization_gains=gains,
        off_frame_sums=None if n == 0 else off_sums,
        off_equalization_gains=None if n == 0 else off_gains,
        off_quadratures=off_bands,
        separation_matrices=matrices,
        phase_angles_rad=phases_all,
        input_scale=alpha,
        background_after=bg,
        slope_after=slope,
        sentinel_frames=tuple(sentinels),
        between_displacements_pixels=between,
        exposure_displacements_pixels=exposure,
        header_timestamps_after=timestamps,
        events=events,
        on_edge=on_edge,
        off_edge=off_edge,
        before_ramp=before_ramp,
        off_before_ramp=off_before_ramp,
        after_ramp=after_ramp,
        off_after_ramp=off_after_ramp,
        separated=separated,
        off_separated=off_separated,
        pre_axial=pre_axial,
        prepass_backgrounds=prepass_backgrounds,
        mixtures=mixtures,
    )


def full_band(quadratures: np.ndarray, m: int) -> np.ndarray:
    z, y, xh = quadratures.shape[1:]
    x = (xh - 1) * 2
    result = np.empty((z, y, x), dtype=complex)
    for iz, iy, ix in np.ndindex(result.shape):
        if ix <= x // 2:
            v = quadratures[:, iz, iy, ix]
        else:
            v = quadratures[:, -iz % z, -iy % y, x - ix].conj()
        result[iz, iy, ix] = v[0] if m == 0 else v[2 * m - 1] + 1j * v[2 * m]
    return result


def overlap(
    case: Case, quadratures: np.ndarray, carrier: np.ndarray, pair: tuple[int, int]
) -> tuple[np.ndarray, dict[str, Any]]:
    a, _, f = case.resolved()
    z, y, xh = quadratures.shape[1:]
    x = (xh - 1) * 2
    mode2 = a["acquisition_mode"] == "2d"
    dzf = 1 / (z * a["dz_um"]) if a["dz_um"] > 0 else case.table.dkz
    le = OPTICS["wavelength_nm"] / OPTICS["immersion_index"] / 1000
    theta = math.asin(OPTICS["numerical_aperture"] / OPTICS["immersion_index"])
    cutoff = math.ceil((1 - math.cos(theta)) / le / dzf)
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    radius = min(
        2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000), 1 / (2 * a["dxy_um"])
    )
    lo, hi = pair
    delta = (hi - lo) * carrier
    band_lo, band_hi = full_band(quadratures, lo), full_band(quadratures, hi)
    fourier = np.zeros((2, z, y, x), dtype=complex)
    written = np.zeros(fourier.shape, dtype=bool)
    weight_sensitivity = 0.0
    threshold_margin = math.inf
    factor = 1 if mode2 else 5
    for iy in range(y):
        for ix in range(x):
            kx, ky = lift(ix, x) / (x * a["dxy_um"]), lift(iy, y) / (y * a["dxy_um"])
            if math.hypot(kx, ky) > radius:
                continue
            for branch in (0, 1):
                shift = -delta if branch == 0 else delta
                sx, sy = kx + shift[0], ky + shift[1]
                if math.hypot(sx, sy) > radius:
                    continue
                for iz in range(-cutoff, cutoff + 1):
                    if f["omit_kz0"] and iz == 0:
                        continue
                    order = lo if branch == 0 else hi
                    other = hi if branch == 0 else lo
                    first = case.table.sample(kx, ky, iz, dzf, order)
                    threshold_margin = min(
                        threshold_margin, abs((1 if order == 0 else factor) * abs(first) - 0.006)
                    )
                    if (1 if order == 0 else factor) * abs(first) <= 0.006:
                        continue
                    second = case.table.sample(sx, sy, iz, dzf, other)
                    threshold_margin = min(
                        threshold_margin, abs((1 if other == 0 else factor) * abs(second) - 0.006)
                    )
                    if (1 if other == 0 else factor) * abs(second) <= 0.006:
                        continue
                    band = band_lo if branch == 0 else band_hi
                    weight_sensitivity = max(
                        weight_sensitivity,
                        abs(band[iz % z, iy, ix]) / math.sqrt(abs(first) ** 2 + abs(second) ** 2),
                    )
                    fourier[branch, iz % z, iy, ix] = (
                        band[iz % z, iy, ix]
                        * second
                        / math.sqrt(abs(first) ** 2 + abs(second) ** 2)
                    )
                    written[branch, iz % z, iy, ix] = True
    spatial = finite_transform(fourier, (1, 2, 3), 1)
    return spatial, dict(
        fourier=fourier,
        spatial=spatial,
        written=written,
        orders=pair,
        carrier_cyc_um=carrier.copy(),
        weight_sensitivity=weight_sensitivity,
        threshold_margin=threshold_margin,
    )


def regression(
    spatial: np.ndarray, carrier: np.ndarray, pair: tuple[int, int], pitch: float
) -> dict[str, Any]:
    _, _, y, x = spatial.shape
    xx, yy = np.meshgrid((np.arange(x) - x // 2) * pitch, (np.arange(y) - y // 2) * pitch)
    lower = spatial[0]
    higher = (
        spatial[1]
        * np.exp(2j * np.pi * (pair[1] - pair[0]) * (carrier[0] * xx + carrier[1] * yy))[None]
    )
    sx, sy = float(np.sum(abs(lower) ** 2)), float(np.sum(abs(higher) ** 2))
    cross = complex(np.sum(lower.conj() * higher))
    assert sx > 0 and sy > 0 and sx != sy, ("invalid independently designed regression", sx, sy)
    forward, reverse = cross / sx, cross.conjugate() / sy
    if cross == 0:
        combined = 0j
    else:
        beta = math.atan(2 * abs(cross) / (sx - sy)) / 2
        if beta < 0:
            beta += np.pi / 2
        combined = math.tan(beta) * cross / abs(cross)
    return dict(
        SX=sx,
        SY=sy,
        cross=cross,
        forward=forward,
        reverse=reverse,
        combined=combined,
        correlation=abs(cross) / math.sqrt(sx * sy),
        carrier_cyc_um=carrier.copy(),
    )


def parabola(points: list[float]) -> float:
    x1, y1, x2, y2, x3, y3 = points
    if x1 in (x2, x3) or x2 == x3:
        return 0.0
    b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
    s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
    curvature = (s2 - s1) / (b2 - b1)
    return 0.0 if curvature == 0 else b2 - s2 / curvature


def estimate(case: Case, prep: dict[str, Any]) -> dict[str, Any]:
    a, c, _ = case.resolved()
    t, d, p, z, y, x = case.raw.shape
    orders = a["norders"]
    initial, _ = initial_vectors(case)
    carriers = np.empty((t, d, 2))
    raw = np.empty((t, d, orders - 1), dtype=complex)
    modulation = np.empty_like(raw)
    builds: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    branches: list[tuple[str, ...]] = []
    mode2 = a["acquisition_mode"] == "2d"
    fitorder = 1 if mode2 else 2
    for it in range(t):
        row = []
        for di in range(d):
            first_decision = len(decisions)
            bands = prep["quadratures"][it, di]

            def build(
                k: np.ndarray,
                pair: tuple[int, int],
                purpose: str,
                *,
                bands: np.ndarray = bands,
                it: int = it,
                di: int = di,
            ) -> np.ndarray:
                spatial, record = overlap(case, bands, k, pair)
                builds.append(dict(time_index=it, direction_index=di, purpose=purpose, **record))
                return spatial

            def fit(
                spatial: np.ndarray,
                k: np.ndarray,
                pair: tuple[int, int],
                stage: str,
                angle: float | None = None,
                magnitude: float | None = None,
                *,
                it: int = it,
                di: int = di,
            ) -> dict[str, Any]:
                result = regression(spatial, k, pair, a["dxy_um"])
                result.update(
                    stage=stage,
                    orders=pair,
                    time_index=it,
                    direction_index=di,
                    angle_rad=angle,
                    magnitude_cyc_um=magnitude,
                    objective=None if stage == "known" else abs(result["forward"]) ** 2,
                    overlap_index=len(builds) - 1,
                )
                evaluations.append(result)
                return result

            searched = c["search_carriers"] and not (it > 0 and c["use_time0_carriers"])
            k = (
                initial[di].copy()
                if not (it > 0 and c["search_carriers"] and c["use_time0_carriers"])
                else carriers[0, di].copy()
            )
            if searched:
                row.append("searched")
                pair = (0, fitorder)
                spatial = build(k, pair, "coarse")
                corr = finite_transform(np.sum(spatial[0] * spatial[1].conj(), axis=0), (0, 1), -1)
                power = abs(corr) ** 2
                iy, ix = np.unravel_index(np.argmax(power), power.shape)
                ox, _ = peak_offset(power[iy, [(ix - 1) % x, ix, (ix + 1) % x]])
                oy, _ = peak_offset(power[[(iy - 1) % y, iy, (iy + 1) % y], ix])
                px, py = ix + ox, iy + oy
                aliases = []
                for axis, extent, step in (
                    (0, x, 1 / (x * a["dxy_um"])),
                    (1, y, 1 / (y * a["dxy_um"])),
                ):
                    value = px if axis == 0 else py
                    lower = bool(k[axis] * step < value - extent // 2)
                    if lower:
                        value -= extent
                    upper = bool(k[axis] * step > value + extent // 2)
                    if upper:
                        value += extent
                    aliases.extend((lower, upper))
                    if axis == 0:
                        px = value
                    else:
                        py = value
                k = np.array([px / (x * a["dxy_um"]), py / (y * a["dxy_um"])]) / fitorder
                assert np.linalg.norm(k) > 0, "frozen fixture has zero coarse polar vector"
                decisions.append(
                    dict(
                        kind="coarse",
                        time_index=it,
                        direction_index=di,
                        integer_peak_xy=(int(ix), int(iy)),
                        alias_decisions=tuple(aliases),
                        carrier_cyc_um=k.copy(),
                        correlation_power=power,
                    )
                )
                mag0, angle0 = float(np.linalg.norm(k)), math.atan2(k[1], k[0])
                spatial = build(k, pair, "refinement")
                x1 = amp1 = 0.0
                angle, magnitude = angle0, mag0
                for stage, origin, step in (
                    ("angle", angle0, 0.001),
                    ("magnitude", mag0, 0.1 / (max(x, y) * a["dxy_um"])),
                ):

                    def objective(
                        value: float,
                        *,
                        mag0: float = mag0,
                        stage: str = stage,
                        angle: float = angle,
                        spatial: np.ndarray = spatial,
                        pair: tuple[int, int] = pair,
                    ) -> float:
                        ang, mag = (value, mag0) if stage == "angle" else (angle, value)
                        vector = np.array([math.cos(ang), math.sin(ang)]) * mag
                        result = fit(spatial, vector, pair, stage, ang, mag)
                        return float(result["objective"])

                    x2, x3 = origin, origin + step
                    amp2, amp3 = objective(x2), objective(x3)
                    positive = amp3 > amp2
                    decisions.append(
                        dict(
                            kind="initial",
                            stage=stage,
                            points=(x1, amp1, x2, amp2, x3, amp3),
                            strict_improvement=positive,
                        )
                    )
                    candidate = origin + step if positive else origin
                    if not positive:
                        x2, x3, amp2, amp3 = x3, x2, amp3, amp2
                    while amp3 > amp2:
                        x1, amp1, x2, amp2 = x2, amp2, x3, amp3
                        candidate += step if positive else -step
                        x3, amp3 = candidate, objective(candidate)
                        decisions.append(
                            dict(
                                kind="shift",
                                stage=stage,
                                points=(x1, amp1, x2, amp2, x3, amp3),
                                strict_improvement=amp3 > amp2,
                            )
                        )
                    points = [x1, amp1, x2, amp2, x3, amp3]
                    if stage == "angle":
                        angle = parabola(points)
                    else:
                        magnitude = parabola(points)
                    decisions.append(
                        dict(
                            kind="parabola",
                            stage=stage,
                            points=tuple(points),
                            result=angle if stage == "angle" else magnitude,
                        )
                    )
                k = magnitude * np.array([math.cos(angle), math.sin(angle)])
                result = fit(spatial, k, pair, "final", angle, magnitude)
                raw[it, di, fitorder - 1] = result["forward"]
                for m in range(1, orders):
                    if m == fitorder:
                        continue
                    pair = (m - 1, m) if mode2 else (0, m)
                    spatial = build(k, pair, "later-order")
                    raw[it, di, m - 1] = fit(spatial, k, pair, "later-order", angle, magnitude)[
                        "forward"
                    ]
            else:
                row.append("time0-reused" if c["search_carriers"] and it > 0 else "known")
                for m in range(1, orders):
                    pair = (0, m)
                    spatial = build(k, pair, "known")
                    raw[it, di, m - 1] = fit(spatial, k, pair, "known")["forward"]
            carriers[it, di] = k
            final = raw[it, di].copy()
            if mode2:
                for m in range(1, orders - 1):
                    final[m] *= final[m - 1]
            floors = c["amplitude_floors"]
            if floors is not None:
                for m in range(orders - 1):
                    if abs(final[m]) < floors[m]:
                        final[m] *= floors[m] / abs(final[m])
            if not c["fit_all_phases"]:
                phi = np.angle(final[0])
                for m in range(1, orders - 1):
                    final[m] = abs(final[m]) * np.exp(1j * (m + 1) * phi)
            modulation[it, di] = final
            for decision in decisions[first_decision:]:
                decision.update(time_index=it, direction_index=di)
        branches.append(tuple(row))
    return dict(
        carriers_cyc_um=carriers,
        raw_modulation=raw,
        modulation=modulation,
        branches=tuple(branches),
        overlaps=builds,
        evaluations=evaluations,
        decisions=decisions,
    )


def filter_and_assemble(
    case: Case,
    prep: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    a, _, f = case.resolved()
    t, d, p, z, y, x = case.raw.shape
    orders = a["norders"]
    dzf = 1 / (z * a["dz_um"]) if a["dz_um"] > 0 else case.table.dkz
    dx, dy = 1 / (x * a["dxy_um"]), 1 / (y * a["dxy_um"])
    le = OPTICS["wavelength_nm"] / OPTICS["immersion_index"] / 1000
    theta = math.asin(OPTICS["numerical_aperture"] / OPTICS["immersion_index"])
    radius = min(
        2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000), 1 / (2 * a["dxy_um"])
    )
    c0 = math.ceil((1 - math.cos(theta)) / le / dzf)
    cutoffs = np.array(
        [c0] + [math.trunc((1 + 1 / 0.88) * c0)] * (orders - 2) + [math.trunc(1.3 * c0)]
    )
    cutoffs[cutoffs >= z // 2] = max(z // 2 - 1, 0)
    yo, xo, zo = int(a["lateral_zoom"] * y), int(a["lateral_zoom"] * x), a["axial_zoom"] * z
    xv = (np.arange(xo) - xo // 2) * a["dxy_um"] / a["lateral_zoom"]
    yv = (np.arange(yo) - yo // 2) * a["dxy_um"] / a["lateral_zoom"]
    zv = (np.arange(zo) - zo // 2) * a["dz_um"] / a["axial_zoom"]
    effective = f["wiener"] + (np.arange(t) + 1) * f["wiener_increment"] / t
    filtered = prep["quadratures"].copy()
    image = np.zeros((t, zo, yo, xo))
    for it in range(t):
        carriers = parameters["carriers_cyc_um"][it]
        modulation = np.column_stack((np.ones(d), parameters["modulation"][it]))
        apo = radius + np.linalg.norm(carriers[0]) * (orders - 1)

        def weight(di: int, m: int, r: float, iz: int, *, it: int = it) -> float:
            g = 1 / prep["noise_variance_factors"][it, di, m]
            within = r <= f["suppression_radius_bins"] * min(dx, dy)
            if (
                f["suppress_singularities"]
                and m != 0
                and within
                or m == 0
                and f["suppress_singularities"]
                and not f["dampen_order0"]
                and not f["omit_order0"]
                and within
            ):
                g /= 1 + 1000 / (r * r + 0.2)
            elif m == 0 and f["dampen_order0"]:
                assert cutoffs[0] > 0
                g *= (r / radius) ** 2 + abs(iz / cutoffs[0]) ** 3
            elif m == 0 and f["omit_order0"]:
                g = 0.0
            if m == 0 and iz == 0 and f["omit_kz0"]:
                g = 0.0
            return float(g)

        for di in range(d):
            for m in range(orders):
                slots = [0] if m == 0 else [2 * m - 1, 2 * m]
                temp = np.zeros((z, y, x), dtype=complex)
                for iy in range(-(y // 2 - 1), y // 2 + 1):
                    for ix in range(-(x // 2 - 1), x // 2 + 1):
                        if m == 0 and ix < 0:
                            continue
                        reflected = ix < 0
                        sy, sx = (-iy) % y if reflected else iy % y, abs(ix)
                        r = math.hypot(ix * dx, iy * dy)
                        for iz in range(-int(cutoffs[m]), int(cutoffs[m]) + 1):
                            if r > radius:
                                filtered[it, di, slots, iz % z, sy, sx] = 0
                                continue
                            self_h = case.table.sample(ix * dx, iy * dy, iz, dzf, m)
                            g = weight(di, m, r, iz)
                            denominator = abs(self_h) ** 2 * abs(modulation[di, m]) ** 2 * g
                            object_xy = np.array([ix * dx, iy * dy]) + m * carriers[di]
                            for other_d in range(d):
                                for signed_m in range(-(orders - 1), orders):
                                    if (other_d, signed_m) == (di, m):
                                        continue
                                    if not f["filter_overlaps"] and not (m == 0 and signed_m == 0):
                                        continue
                                    qxy = object_xy - signed_m * carriers[other_d]
                                    qrad = float(np.linalg.norm(qxy))
                                    if qrad < radius:
                                        h = case.table.sample(
                                            qxy[0], qxy[1], iz, dzf, abs(signed_m)
                                        )
                                        other_g = weight(other_d, abs(signed_m), qrad, iz)
                                        other_a = abs(modulation[other_d, abs(signed_m)])
                                        denominator += abs(h) ** 2 * other_a**2 * other_g
                            denominator += effective[it] ** 2
                            taper = 1.0
                            if f["output_taper"] != "none":
                                # Successful active precise tests use c1>0; finite
                                # inactive and empty-traversal cases need no query.
                                assert not f["precise_taper"] or cutoffs[1] > 0
                                rho = float(np.linalg.norm(object_xy)) / apo
                                if cutoffs[1] > 0:
                                    rho = math.hypot(rho, abs(iz) / cutoffs[1])
                                rho = min(rho, 1)
                                taper = (
                                    math.cos(np.pi * rho / 2)
                                    if f["output_taper"] == "cosine"
                                    else (1 - rho) ** f["power_taper_exponent"]
                                )
                            scale = (
                                taper
                                * g
                                * self_h.conjugate()
                                * modulation[di, m].conjugate()
                                / denominator
                            )
                            sz = -iz % z if reflected else iz % z
                            if m == 0:
                                filtered[it, di, 0, sz, sy, sx] *= scale
                            else:
                                e, o = filtered[it, di, slots, sz, sy, sx]
                                if reflected:
                                    e, o = e.conjugate(), o.conjugate()
                                temp[iz % z, iy % y, ix % x] = (e + 1j * o) * scale
                        for iz in range(int(cutoffs[m]) + 1, z - int(cutoffs[m])):
                            filtered[it, di, slots, iz, sy, sx] = 0
                if m > 0:
                    for iy in range(-(y // 2 - 1), y // 2 + 1):
                        for ix in range(x // 2 + 1):
                            for iz in range(-int(cutoffs[m]), int(cutoffs[m]) + 1):
                                positive = temp[iz % z, iy % y, ix]
                                negative = temp[-iz % z, -iy % y, -ix % x].conjugate()
                                filtered[it, di, 2 * m - 1, iz % z, iy % y, ix] = (
                                    positive + negative
                                ) / 2
                                filtered[it, di, 2 * m, iz % z, iy % y, ix] = (
                                    positive - negative
                                ) / (2j)
                if m == 0 and f["omit_order0"]:
                    continue
                native = full_band(filtered[it, di], m)
                output = np.zeros((zo, yo, xo), dtype=complex)
                for iz, iy, ix in np.ndindex(native.shape):
                    output[lift(iz, z) % zo, lift(iy, y) % yo, lift(ix, x) % xo] = native[
                        iz, iy, ix
                    ]
                if a["acquisition_mode"] == "2d":
                    spatial = np.zeros_like(output)
                    spatial[0] = finite_transform(output[0], (0, 1), 1)
                else:
                    spatial = finite_transform(output, (0, 1, 2), 1)
                if m > 0:
                    xx, yy = np.meshgrid(xv, yv)
                    spatial *= (
                        2
                        * np.exp(
                            2j
                            * np.pi
                            * f["explode_factor"]
                            * m
                            * (carriers[di, 0] * xx + carriers[di, 1] * yy)
                        )[None]
                    )
                image[it] += np.real(spatial)
    return dict(
        image=image,
        filtered_quadratures=filtered,
        x_um=xv,
        y_um=yv,
        z_um=zv,
        effective_wiener=effective,
        axial_cutoffs_bins=cutoffs,
    )


def empirical(raw: np.ndarray, settings: dict[str, Any]) -> dict[str, Any]:
    """Independent radialft observer for the chosen no-cleanup fixture family."""
    s: dict[str, Any] = BEAD_DEFAULTS | settings
    p, z, y, x = raw.shape
    corrected = np.empty_like(raw)
    backgrounds = np.zeros((z, p))
    for iz in range(z):
        for ph in range(p):
            frame = raw[ph, iz].copy()
            if frame[-1, -1] < 0:
                frame[-1, -1] = frame[-1, -2]
            if s["exposure_background_counts"] is not None:
                b = s["exposure_background_counts"][iz, ph]
            elif s["background_map"] is not None:
                frame = (frame - s["background_map"]) * s["slope_map"]
                b = 0
            elif s["background_counts"] is not None:
                b = s["background_counts"]
            else:
                yy, xx = np.indices((y, x))
                mask = ((yy < 20) | (yy > y - 20)) & ((xx < 20) | (xx > x - 20))
                b = frame[mask].mean()
            backgrounds[iz, ph] = b
            corrected[ph, iz] = edge(frame, 10, bead=True)
    average = corrected.mean(axis=0)
    if np.max(average) > 0:
        zi, yi, xi = np.unravel_index(np.argmax(average), average.shape)
    else:
        zi = yi = xi = 0
    peak = average[zi, yi, xi] if np.max(average) > 0 else 0
    center = np.array([float(xi), float(yi), float(zi)])
    for axis, n in enumerate((x, y, z)):
        indices = [zi, yi, xi]
        at = [zi, yi, xi][2 - axis]
        neighbors = []
        for k in (-1, 1):
            indices[2 - axis] = (at + k) % n
            neighbors.append(average[tuple(indices)])
        center[axis] += peak_offset(np.array([neighbors[0], peak, neighbors[1]]))[0]
    corrected -= backgrounds.T[:, :, None, None]
    matrix, _ = phase_matrix(2 * np.pi * np.arange(p) / p, (p + 1) // 2, True)
    separated = np.tensordot(matrix / p, corrected, axes=1)
    transformed = finite_transform(separated, (1, 2, 3), -1)[..., : x // 2 + 1]
    radial = np.zeros((p, x // 2 + 1, z), dtype=complex)
    counts = np.zeros(x // 2 + 1)
    for iy in range(y):
        for ix in range(x // 2 + 1):
            r = round(math.hypot(ix, lift(iy, y)))
            if r > x // 2:
                continue
            counts[r] += 1
            for iz in range(z):
                ramp = np.exp(
                    2j
                    * np.pi
                    * (
                        ix * center[0] / x
                        + lift(iy, y) * center[1] / y
                        + lift(iz, z) * center[2] / z
                    )
                )
                values = transformed[:, iz, iy, ix] * ramp
                if s["compensate_bead"]:
                    for slot in range(p):
                        order = (slot + 1) // 2
                        radius_frequency = math.sqrt(
                            (
                                ix / (y * s["dxy_um"])
                                + order
                                * math.cos(s["carrier_angle_rad"])
                                / (((p + 1) // 2 - 1) * s["linespacing_um"])
                            )
                            ** 2
                            + (
                                lift(iy, y) / (y * s["dxy_um"])
                                + order
                                * math.sin(s["carrier_angle_rad"])
                                / (((p + 1) // 2 - 1) * s["linespacing_um"])
                            )
                            ** 2
                            + (lift(iz, z) / (z * s["dz_um"])) ** 2
                        )
                        argument = np.pi * s["bead_diameter_um"] * radius_frequency
                        if abs(argument) <= 2:
                            sphere = sum(
                                6
                                * (k + 1)
                                * (-1) ** k
                                * argument ** (2 * k)
                                / math.factorial(2 * k + 3)
                                for k in range(20)
                            )
                        else:
                            sphere = (
                                3
                                * (math.sin(argument) - argument * math.cos(argument))
                                / argument**3
                            )
                        values[slot] /= sphere
                radial[:, r, iz] += values
    for r in range(x // 2 + 1):
        if counts[r] != 0:
            radial[:, r] /= counts[r]
        radial[:, r, 0] = np.real(radial[:, r, 0])
        for j in range(1, z // 2 + 1):
            value = (radial[:, r, j] + radial[:, r, z - j].conj()) / 2
            radial[:, r, j], radial[:, r, z - j] = value, value.conj()
    if s["fix_axial_axis"]:
        for slot in range(p):
            for j in range(z):
                if slot != 0 or j != 0:
                    radial[slot, 0, j] = radial[slot, 1, j]
    if s["fix_radial_from"] > 0:
        for r in range(s["fix_radial_from"], x // 2 + 1):
            for slot in range(p):
                flat = radial[slot].ravel()
                assert r * z + 1 < flat.size
                radial[slot, r, 0] = (flat[r * z + 1] + flat[r * z + z - 1]) / 2
    l11, l12, l2 = s["cleanup_axial_bins"]
    if l11:
        for slot in range(p):
            order = (slot + 1) // 2
            aperture = s["numerical_aperture"] * (1 if order == 0 else 0.92)
            alpha = math.asin(aperture / s["immersion_index"])
            wavelength = s["wavelength_nm"] / 1000
            flat = radial[slot].ravel()
            for r in range(x // 2 + 1):
                kr = r / (y * s["dxy_um"])
                if kr > 2 * aperture / wavelength:
                    radial[slot, r] = 0
                    continue
                beta = math.asin((aperture - kr * wavelength) / s["immersion_index"])
                width = (
                    s["immersion_index"]
                    / wavelength
                    * (math.cos(beta) - math.cos(alpha))
                    * z
                    * s["dz_um"]
                )
                indices = []
                if order == 0:
                    j0 = round(width + 1)
                    indices = list(range(j0, z - j0 + 1))
                elif order == 1:
                    h = round(width + 0.999)
                    for j in range(l11 - h + 1):
                        indices.extend([j] if j == 0 else [j, z - j])
                    for j in range(l12 + h + 1, z // 2 + 1):
                        indices.extend([j, z - j])
                else:
                    for j in range(l2 + round(width + 0.999), z // 2 + 1):
                        indices.extend([j, z - j])
                for j in indices:
                    address = r * z + j
                    assert 0 <= address < flat.size, "unsafe empirical cleanup observer address"
                    flat[address] = 0
    if s["origin_fit_bins"] is not None:
        first, last = s["origin_fit_bins"]
        radii = np.arange(first, last + 1)
        values = np.sum(np.real(radial[0, first : last + 1]), axis=1)
        midpoint = (first + last) / 2
        mean = float(np.mean(values))
        slope = float(np.sum((radii - midpoint) * values) / np.sum((radii - midpoint) ** 2))
        for r in range(first):
            axial_sum = np.real(radial[0, r, 0]) if r == 0 else np.sum(np.real(radial[0, r]))
            radial[0, r, 0] += -axial_sum + mean + (r - midpoint) * slope
    pre_normalization = radial.copy()
    factors = np.empty(p)
    scale = 1.0
    for slot in range(p):
        if slot == 0 or s["rescale_each"]:
            scale = 1 / np.max(abs(radial[slot]))
        factors[slot] = scale
        radial[slot] *= scale
    samples = [radial[0]]
    angles = []
    for m in range(1, (p + 1) // 2):
        cosine, sine = radial[2 * m - 1], radial[2 * m]
        angle = math.atan(np.sum(abs(sine)) / np.sum(abs(cosine)))
        c0, s0 = cosine[x // 8, 0].real, sine[x // 8, 0].real
        if c0 < 0 and s0 > 0:
            angle += np.pi
        elif c0 < 0 and s0 < 0:
            angle = np.pi - angle
        elif c0 > 0 and s0 > 0:
            angle = -angle
        if m == 1 and s["forced_pi_shift"]:
            angle = np.pi - angle
        samples.append(cosine * math.cos(angle) - sine * math.sin(angle))
        angles.append(angle)
    table_values = np.asarray(samples)
    if s["conjugate"]:
        table_values = table_values.conj()
    return dict(
        table=Table(table_values, dkr=1 / (y * s["dxy_um"]), dkz=1 / (z * s["dz_um"])),
        center_pixels_xyz=center,
        background_counts=backgrounds,
        quadratures=radial,
        normalization_factors=factors,
        quadrature_angles_rad=np.asarray(angles),
        radial_counts=counts,
        pre_normalization=pre_normalization,
        center_average=average,
    )


def empirical_error(case: Case, calibration: dict[str, Any]) -> float:
    """Summarize the independently propagated raw-calibration cell bounds."""
    return float(np.max(calibration_errors(case, calibration)["samples"]))


def observe(case: Case) -> dict[str, Any]:
    effective = reinterpret(case)
    calibration = None
    if case.bead is not None:
        calibration = empirical(*case.bead)
        effective = copy.deepcopy(effective)
        effective.table = calibration["table"]
    prep = prepare(effective)
    parameters = estimate(effective, prep)
    output = filter_and_assemble(effective, prep, parameters)
    return dict(preparation=prep, parameters=parameters, calibration=calibration, **output)


def control_cases() -> dict[str, Case]:
    """Return fixed composition controls; require a new freeze for changes."""
    cases: dict[str, Case] = {}
    for mode in ("3d", "2d"):
        for complex_table in (False, True):
            name = f"algebra-{mode}-{'complex' if complex_table else 'unit'}"
            case = constant_case(mode=mode, complex_table=complex_table)
            case.name = name
            cases[name] = case
    general = patterned_case()
    yy, xx = np.indices(general.raw.shape[-2:])
    general.acquisition.update(
        background=2 + xx / 8 - yy / 16,
        flatfield_slope=1 + (xx - yy) / 32,
        edge_pixels=3,
        equalize=True,
        equalize_z=True,
        equalize_time=True,
        phase_policy="supplied",
        phases_rad=np.array(
            [[0, 1, 2.5, 3.7, 5.3], [0.1, 1.2, 2.3, 3.9, 5.5], [0.2, 1.5, 2.7, 4.1, 5.8]]
        ),
    )

    general.raw[0, 0, 0, 0, -1, -1] = -1
    general.extras["exposure_background"] = np.arange(2 * 3 * 5 * 2).reshape(2, 3, 5, 2) / 16
    cases["ordinary-camera-phase"] = general
    for name, changes in (
        (
            "cosine-suppression",
            dict(output_taper="cosine", suppress_singularities=True, suppression_radius_bins=2.0),
        ),
        (
            "power-zero-no-overlap",
            dict(output_taper="power", power_taper_exponent=0.0, filter_overlaps=False),
        ),
        (
            "power-positive",
            dict(output_taper="power", power_taper_exponent=1.5, explode_factor=-0.75),
        ),
        ("signed-power-interior", dict(output_taper="power", power_taper_exponent=-0.5)),
        (
            "omit-and-signed-radius",
            dict(
                omit_order0=True,
                suppress_singularities=True,
                suppression_radius_bins=-2.0,
                explode_factor=0.0,
            ),
        ),
    ):
        case = constant_case(complex_table=True)
        case.filtering.update(changes)
        if name == "signed-power-interior":
            case.carrier["phase_start_angle_rad"] = 0.21
        cases[name] = case
    for name, y in (("odd-y", 3), ("empty-y-precise", 1)):
        case = patterned_case(directions=1, times=1, y=y, x=4)
        if y == 1:
            case.filtering.update(precise_taper=True, dampen_order0=True)
        cases[name] = case
    zoom = patterned_case(mode="2d", directions=2, times=1)
    zoom.acquisition.update(lateral_zoom=1.5, axial_zoom=2, dz_um=0.0)
    zoom.filtering.update(explode_factor=-1.0)
    cases["true2d-fractional-zero-dz"] = zoom
    reduced = patterned_case(directions=2, times=1)
    reduced.acquisition["norders"] = 2
    reduced.carrier.update(angles_rad=np.array([0.3, -0.7]), negative_angle_step=True)
    cases["p5-o2-initialization"] = reduced
    seven = patterned_case(directions=1, times=1, orders=4)
    seven.acquisition["norders"] = 3
    cases["p7-o3-initialization"] = seven
    steps = patterned_case(directions=3, times=1)
    steps.acquisition.update(
        phase_policy="steps",
        phase_steps_rad=np.array([1.0, 1.15, 1.3]),
        phases_rad=np.zeros((3, 5)),
        adjust_phases=True,
    )
    cases["steps-supersede-singular-list"] = steps
    repeated = patterned_case(directions=4, times=1, orders=2)
    repeated.raw = np.concatenate((repeated.raw, repeated.raw[:, :, :1]), axis=2)
    repeated.acquisition.update(
        phase_policy="supplied", phases_rad=np.tile([0, 1.5, 3.1, 0], (4, 1))
    )
    cases["d4-repeated-full-rank-list"] = repeated
    full = patterned_case(mode="2d", directions=2, times=1)
    m, k, j, i = np.indices((3, 1, 16, 16))
    full.table = Table(
        (1 + m / 4 + i / 32 + j / 64) + 1j * (m / 8 + j / 32 - i / 64), "full", 0.125, 0.75
    )
    full.acquisition["dz_um"] = 0.0
    full.carrier.update(amplitude_floors=np.array([0.3, 0.4]), fit_all_phases=False)
    cases["true2d-full-floors-products"] = full
    off_case = patterned_case(directions=2, times=2)
    off_case.acquisition.update(
        dxy_um=0.1,
        edge_pixels=-1,
        equalize=True,
        equalize_z=True,
        equalize_time=True,
        combine_off_orders=np.array([1, 1, 1], dtype=np.int32),
    )
    off_case.table.dkr = 1.0
    off_case.carrier["linespacing_um"] = 3.0
    off_case.extras["off_exposures"] = np.stack((off_case.raw / 2, off_case.raw / 4), axis=4)
    off_case.extras["off_exposures"][0, 0, 0, 0, 0, -1, -1] = -1
    off_case.extras["exposure_background"] = np.arange(2 * 2 * 5 * 2).reshape(2, 2, 5, 2) / 8
    cases["off-sum-offset-plane0"] = off_case
    single_off = patterned_case(mode="2d", directions=1, times=1)
    single_off.acquisition.update(
        equalize=True, edge_pixels=-2, combine_off_orders=np.array([0, -1, 0])
    )
    single_off.extras["off_exposures"] = single_off.raw[:, :, :, :, None] / 4
    cases["off-n1-no-equalization"] = single_off
    for storage in ("direction-major", "z-major"):
        literal = patterned_case(directions=2, times=1)
        literal.acquisition.update(
            acquisition_mode="2d", storage_order=storage, equalize=True, equalize_time=True
        )
        literal.table.samples = literal.table.samples[..., :1]
        literal.table.dkz = 0.5
        literal.extras.update(
            plane_policy="literal-2d-stack",
            off_exposures=literal.raw[:, :, :, :, None] / 2,
            exposure_background=np.arange(20).reshape(1, 2, 5, 2) / 8,
        )
        cases[f"literal-{storage}"] = literal
    for mode in ("3d", "2d"):
        search = patterned_case(mode=mode, directions=1, times=2)
        t, d, p, z, y, x = search.raw.shape
        ph, yy, xx = np.indices((p, y, x))
        harmonic = 1 if mode == "2d" else 2
        for it in range(t):
            values = 100 + np.rint(
                (10 + 4 * it) * np.cos(2 * np.pi * (harmonic * xx / x - ph / p))
                + 5 * np.cos(2 * np.pi * (yy / y - ph / p))
                + 3 * np.cos(2 * np.pi * (xx / x + yy / y))
            ).astype(float)
            search.raw[it, 0] = values[:, None]
        search.carrier.update(search_carriers=True, linespacing_um=10.0, phase_start_angle_rad=0.0)
        cases[f"search-{mode}-reuse"] = search
        all_times = copy.deepcopy(search)
        all_times.carrier["use_time0_carriers"] = False
        cases[f"search-{mode}-all-times"] = all_times
    for z in (1, 2):
        cal = patterned_case(
            mode="2d" if z == 1 else "3d", directions=1, times=1, orders=2 if z == 1 else 3
        )
        cal.bead = bead_fixture(z=z, phases=2 * cal.acquisition["norders"] - 1)
        cases[f"empirical-z{z}"] = cal
    between = patterned_case(directions=3, times=2, x=12, y=10)
    for it in range(2):
        for di in range(3):
            between.raw[it, di] = np.roll(between.raw[it, 0], (di, -di), axis=(-2, -1))
    between.acquisition.update(drift_between=True, drift_filter_fraction=0.2, edge_pixels=0)
    cases["between-current-background"] = between
    for fitted in (False, True):
        within = patterned_case(mode="2d", directions=1, times=2)
        within.acquisition.update(
            drift_within=True,
            fit_drift=fitted,
            adjust_phases=fitted,
            phase_policy="drift" if fitted else "uniform",
            storage_order="z-major",
        )
        within.extras["off_exposures"] = within.raw[:, :, :, :, None] / 4
        if fitted:
            within.extras.update(
                header_timestamps=np.arange(20, dtype=float) + 7,
                header_timestamp_unit="seconds",
                header_phases_rad=np.tile(np.repeat(2 * np.pi * np.arange(5) / 5, 2), 2),
            )
        cases[f"within2d-{'fitted' if fitted else 'unfitted'}"] = within
    cubic3d = patterned_case(directions=4, times=2)
    for it in range(2):
        for di in range(4):
            cubic3d.raw[it, di] = np.roll(cubic3d.raw[it, 0], di, axis=-1)
    cubic3d.acquisition.update(
        drift_within=True, drift_between=True, adjust_phases=True, phase_policy="drift"
    )
    cubic3d.extras.update(
        header_timestamps=np.arange(80, dtype=float) + 2,
        header_timestamp_unit="seconds",
        header_phases_rad=np.zeros(80),
    )
    cases["within3d-cubic-first-block"] = cubic3d
    precise_off = constant_case()
    precise_off.filtering["precise_taper"] = True
    cases["inactive-precise"] = precise_off
    negative_w = constant_case(times=2)
    negative_w.filtering.update(wiener=1.0, wiener_increment=-0.5)
    cases["negative-wiener-increment"] = negative_w
    damped = patterned_case(directions=1, times=1)
    damped.raw = np.repeat(damped.raw, 3, axis=3)
    damped.table.samples = np.repeat(damped.table.samples, 3, axis=-1)
    damped.table.dkz = 1 / 6
    damped.filtering.update(
        dampen_order0=True, omit_order0=True, precise_taper=True, output_taper="cosine"
    )
    cases["dampen-before-omit-precise3d"] = damped
    full3d = patterned_case(directions=2, times=1)
    m, k, j, i = np.indices((3, 2, 16, 16))
    full3d.table = Table(
        (1 + m / 4 + i / 32 + j / 64) + 1j * (m / 8 + j / 32 - i / 64 + k / 16), "full", 0.125, 0.5
    )
    cases["full3d-asymmetric"] = full3d
    empirical_search = copy.deepcopy(cases["search-3d-reuse"])
    ph, yy, xx = np.indices((5, 10, 10))
    for it in range(2):
        values = 100 + np.rint(
            (12 + 4 * it) * np.cos(2 * np.pi * (2 * xx / 10 - 2 * ph / 5))
            + 5 * np.cos(2 * np.pi * (yy / 10 - ph / 5))
            + 3 * np.cos(2 * np.pi * (xx / 10 + yy / 10))
        )
        empirical_search.raw[it, 0] = values[:, None]
    empirical_search.acquisition.update(
        background=2 + np.indices((10, 10))[1] / 8,
        flatfield_slope=1 + (np.indices((10, 10))[1] - np.indices((10, 10))[0]) / 32,
        edge_pixels=3,
        equalize=True,
        phase_policy="supplied",
        phases_rad=np.array([[0.0, 1.0, 2.5, 3.7, 5.3]]),
    )
    empirical_search.bead = bead_fixture(z=2, phases=5)
    cases["empirical-search-camera-phase"] = empirical_search
    tight = constant_case(mode="2d")
    tight.acquisition["dxy_um"] = 2.0
    tight_raw = np.zeros((3, 1, 10, 8))
    tight_raw[:, 0, 5, 4] = [1, 2, 3]
    tight.bead = (
        tight_raw,
        dict(
            dxy_um=1.0,
            dz_um=1.0,
            linespacing_um=1.0,
            **OPTICS,
            background_counts=0.0,
            compensate_bead=False,
            fix_axial_axis=False,
        ),
    )
    cases["empirical-tight-x8-y10"] = tight
    k1_3d = constant_case()
    k1_3d.table.samples = k1_3d.table.samples[..., :1]
    cases["k1-transfer-does-not-select-2d"] = k1_3d
    negative_table = constant_case()
    negative_table.table.samples[1] = -1
    cases["signed-transfer-no-normalization"] = negative_table
    for label, changes in (
        ("rescale-each", dict(rescale_each=True)),
        ("forced-pi", dict(forced_pi_shift=True)),
        ("conjugate", dict(conjugate=True)),
        (
            "exposure-priority",
            dict(
                exposure_background_counts=np.arange(15).reshape(3, 5) / 16,
                background_counts=2.0,
                background_map=np.full((32, 32), 3.0),
                slope_map=np.full((32, 32), -0.5),
            ),
        ),
        (
            "camera-priority",
            dict(
                background_map=np.full((32, 32), 0.125),
                slope_map=np.full((32, 32), 0.75),
                background_counts=2.0,
            ),
        ),
    ):
        calibration_options = patterned_case(directions=1, times=1)
        calibration_options.raw = np.repeat(calibration_options.raw, 3, axis=3)
        calibration_options.bead = bead_fixture(z=3, phases=5)
        calibration_options.bead[1].update(changes)
        cases[f"empirical-{label}"] = calibration_options
    cubic_impulses = constant_case(mode="2d")
    cubic_impulses.raw = np.zeros((1, 1, 4, 1, 10, 64))
    off_impulses = np.zeros((1, 1, 4, 1, 1, 10, 64))
    for ph, amplitude in enumerate((60, 30, 20, 40)):
        cubic_impulses.raw[0, 0, ph, 0, 5, 20 + ph**3] = amplitude
        off_impulses[0, 0, ph, 0, 0, 5, 20 + ph**3] = 5
    cubic_impulses.acquisition.update(
        storage_order="z-major",
        drift_within=True,
        fit_drift=True,
        adjust_phases=True,
        phase_policy="drift",
    )
    cubic_impulses.carrier["linespacing_um"] = 1000.0
    cubic_impulses.extras.update(
        off_exposures=off_impulses,
        header_timestamps=np.repeat(np.arange(4, dtype=float), 2),
        header_timestamp_unit="seconds",
        header_phases_rad=np.repeat(np.arange(4) * np.pi / 2, 2),
    )
    cubic_impulses.table = Table(np.ones((2, 24, 1), dtype=complex), dkr=0.125, dkz=0.75)
    cases["within2d-exact-cubic-impulses"] = cubic_impulses
    cubic_volume = constant_case()
    cubic_volume.raw = np.zeros((1, 4, 3, 2, 20, 64))
    for di in range(4):
        cubic_volume.raw[0, di, :, :, 10, 20 + di**3] = np.array([6.0, 3.0, 3.0])[:, None]
    cubic_volume.carrier["linespacing_um"] = 1000.0
    cubic_volume.acquisition.update(
        drift_within=True, drift_between=True, adjust_phases=True, phase_policy="drift"
    )
    cubic_volume.extras.update(
        header_timestamps=np.arange(24, dtype=float),
        header_timestamp_unit="seconds",
        header_phases_rad=np.zeros(24),
    )
    cubic_volume.table = Table(np.ones((2, 24, 2), dtype=complex), dkr=0.125, dkz=0.5)
    cases["within3d-exact-cubic-impulses"] = cubic_volume
    between_off = copy.deepcopy(cases["between-current-background"])
    between_off.acquisition["background"] = np.full((10, 12), 3.0)
    between_off.acquisition["background"][-1, -1] = 5.0
    between_off.acquisition["background"][-1, -2] = 3.5
    between_off.acquisition["flatfield_slope"] = np.full((10, 12), 0.75)
    between_off.raw[0, 0, 0, 0, -1, -1] = -1
    between_off.extras["off_exposures"] = np.stack(
        (
            np.roll(between_off.raw / 4, (1, 2), axis=(-2, -1)),
            np.roll(between_off.raw / 2, (-2, -1), axis=(-2, -1)),
        ),
        axis=4,
    )
    cases["between-first-off-and-persistent-sentinel"] = between_off
    fast_between = constant_case()
    fast_between.acquisition.update(storage_order="z-major", drift_between=True)
    cases["fast-d1-between-bypass-small-grid"] = fast_between
    negative_counts = constant_case()
    negative_counts.raw *= -1
    cases["signed-negative-counts"] = negative_counts
    compensated = patterned_case(directions=1, times=1)
    compensated.bead = bead_fixture(z=2, phases=5)
    del compensated.bead[1]["compensate_bead"]
    del compensated.bead[1]["fix_axial_axis"]
    compensated.bead[1]["carrier_angle_rad"] = 0.3
    cases["empirical-compensation-defaults"] = compensated
    for name, changes, axial in (
        ("radial-repair", dict(fix_radial_from=2), 2),
        ("cleanup", dict(cleanup_axial_bins=(1, 5, 5)), 6),
        ("origin-fit", dict(origin_fit_bins=(1, 3)), 2),
        ("auto-background", dict(), 2),
    ):
        variant = patterned_case(directions=1, times=1)
        variant.bead = bead_fixture(z=axial, phases=5)
        variant.bead[1].update(changes)
        if name == "auto-background":
            del variant.bead[1]["background_counts"]
        cases[f"empirical-{name}"] = variant
    complex_search = copy.deepcopy(cases["empirical-search-camera-phase"])
    original = complex_search.raw[:, :, :, :1]
    zz = np.arange(6)[None, None, None, :, None, None]
    complex_search.raw = original * (1 + zz / 8) + 3 * zz
    complex_search.bead = bead_fixture(z=3, phases=5)
    cases["empirical-complex-search-camera-phase"] = complex_search
    for name, case in cases.items():
        case.name = name
    return cases


# Corrected conditional numerical model. No product imports or observations.
# The short-operation reserve encloses two evaluations of <=4096 real
# operations, with four-ulp elementary errors on the enumerated arguments.
SHORT = 2 * gamma(4096)


def _nonnegative_inverse(k: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Bound (I-K)^-1 v by its nonnegative Neumann series, componentwise."""
    rows = np.sum(k, axis=1)
    norm = float(np.max(rows))
    assert norm < 1, "unresolved numerical-model inverse perturbation"
    return v + rows.reshape((-1,) + (1,) * (v.ndim - 1)) * np.max(v, axis=0) / (1 - norm)


def _edge_model(
    frame: np.ndarray, error: np.ndarray, width: int, *, bead: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Carry real input and operation errors through the literal edge writes."""
    y, x = frame.shape
    if width < -1:
        return frame.copy(), error.copy()
    if width == -1:
        window = np.outer(
            np.sin(np.pi * (np.arange(y) + 0.5) / y), np.sin(np.pi * (np.arange(x) + 0.5) / x)
        )
        ew = 2 * gamma(128) * (1 + 2 * np.pi)
        return frame * window, abs(window) * error + (abs(frame) + error) * ew + 2 * gamma(8) * abs(
            frame * window
        )
    data = np.zeros((y, x + 2))
    errs = np.zeros_like(data)
    data[:, :x], errs[:, :x] = frame, error
    for axis in (0, 1):
        count = x if axis == 0 else y
        for column in range(count):
            last, first = (
                ((y - 1, column), (0, column)) if axis == 0 else ((column, x - 1), (column, 0))
            )
            delta = (data[last] - data[first]) / 2
            ed = (errs[last] + errs[first]) / 2 + 2 * gamma(4) * (
                abs(data[last]) + abs(data[first])
            ) / 2
            for j in range(width):
                arg = np.pi * (j + 0.5) / (2 * width)
                h = 1 - math.sin(arg)
                eh = 2 * gamma(64) * (1 + abs(arg))
                write1 = (j, column) if axis == 0 else (column, j)
                if axis == 0:
                    write2 = (y - 1 - j, column)
                else:
                    flat = column * (x + 2) + (y if bead else x) - 1 - j
                    write2 = divmod(flat, x + 2)
                term = delta * h
                et = abs(h) * ed + (abs(delta) + ed) * eh + 2 * gamma(4) * abs(term)
                for address, sign in ((write1, 1), (write2, -1)):
                    errs[address] += et + 2 * gamma(4) * (abs(data[address]) + abs(term))
                    data[address] += sign * term
    return data[:, :x].copy(), errs[:, :x].copy()


def _fourier_error(data: np.ndarray, error: np.ndarray, axes: tuple[int, ...]) -> np.ndarray:
    """Unnormalized transform: propagated L1 input plus a separate FFT model."""
    term = np.sum(error, axis=axes, keepdims=True)
    magnitude = np.sum(abs(data) + error, axis=axes, keepdims=True)
    operations = 32 * sum(data.shape[axis] for axis in axes)
    return np.broadcast_to(term + 2 * gamma(operations) * magnitude, data.shape).copy()


def _phase_inverse_model(
    phases: np.ndarray, matrix: np.ndarray, phase_error: np.ndarray, orders: int, uniform: bool
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p, q = len(phases), 2 * orders - 1
    if uniform:
        em = np.zeros_like(matrix)
        for m in range(1, orders):
            em[2 * m - 1 : 2 * m + 1] = 2 * gamma(128) * (1 + abs(m * phases))[None]
        return em, np.ones((p, q)), np.zeros((p, q))
    design = np.empty((p, q))
    design[:, 0] = 1 / p
    ed = np.full_like(design, 2 * gamma(32 * p * q))
    for m in range(1, orders):
        design[:, 2 * m - 1] = 2 * np.cos(m * phases) / p
        design[:, 2 * m] = 2 * np.sin(m * phases) / p
        ed[:, 2 * m - 1 : 2 * m + 1] += (2 * m / p * phase_error)[:, None]
    if p == q:
        k = abs(matrix) @ ed
        em = _nonnegative_inverse(k, k @ abs(matrix))
    else:
        ginv = np.linalg.inv(design.T @ design)
        eg = abs(design).T @ ed + ed.T @ abs(design) + ed.T @ ed
        k = abs(ginv) @ eg
        residual = np.eye(p) - design @ matrix
        rhs = (abs(design) + ed).T @ (ed @ abs(matrix)) + ed.T @ abs(residual)
        em = _nonnegative_inverse(k, abs(ginv) @ rhs)
    return em, design, ed


def _separate_error(
    values: np.ndarray,
    errors: np.ndarray,
    matrix: np.ndarray,
    design: np.ndarray,
    ed: np.ndarray,
    em: np.ndarray,
    uniform: bool,
) -> np.ndarray:
    q, p = matrix.shape
    flat = values.reshape(p, -1)
    ef = errors.reshape(p, -1)
    separated = matrix @ flat
    if uniform:
        result = abs(matrix) @ ef + em @ (abs(flat) + ef)
    elif p == q:
        k = abs(matrix) @ ed
        result = _nonnegative_inverse(k, abs(matrix) @ (ef + ed @ abs(separated)))
    else:
        ginv = np.linalg.inv(design.T @ design)
        eg = abs(design).T @ ed + ed.T @ abs(design) + ed.T @ ed
        k = abs(ginv) @ eg
        residual = flat - design @ separated
        rhs = (abs(design) + ed).T @ (ef + ed @ abs(separated)) + ed.T @ abs(residual)
        result = _nonnegative_inverse(k, abs(ginv) @ rhs)
    result += 2 * gamma(8 * p) * (abs(matrix) + em) @ (abs(flat) + ef)
    result = result.reshape((q, *values.shape[1:]))
    # The physical x-Nyquist slots are raw, not separated.
    result[..., -1] = errors[:q, ..., -1]
    return result


def _correlation_error(
    event: dict[str, Any], er: np.ndarray, em: np.ndarray, case: Case
) -> tuple[np.ndarray, dict[str, Any]]:
    reference, moving = event["reference_fourier"], event["moving_fourier"]
    a, _, _ = case.resolved()
    z, y, xh = reference.shape
    x = (xh - 1) * 2
    v = abs(reference) * abs(moving)
    ec = abs(reference) * em + abs(moving) * er + er * em
    ec += 2 * gamma(8) * (abs(reference) + er) * (abs(moving) + em)
    exponent = event["exponent"]
    ew = (v + ec) ** exponent + v**exponent
    safe = v > ec
    ew[safe] = np.minimum(ew[safe], ec[safe] * (v[safe] - ec[safe]) ** (exponent - 1))
    radius = 2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000)
    for iy in range(y):
        for ix in range(xh):
            r = math.hypot(ix / (x * a["dxy_um"]), lift(iy, y) / (y * a["dxy_um"]))
            if r >= radius:
                ew[:, iy, ix] = 0
            else:
                factor = 1.0
                if a["drift_filter_fraction"] > 0:
                    factor = (
                        1 - math.exp(-((r / (a["drift_filter_fraction"] * radius)) ** 2))
                    ) ** 2
                ew[:, iy, ix] *= factor
                ew[:, iy, ix] += 2 * gamma(160) * (v[:, iy, ix] + ec[:, iy, ix]) ** exponent
    multiplicity = np.ones(xh)
    multiplicity[1:-1] = 2
    inverse_error = float(np.sum(ew * multiplicity))
    inverse_error += (
        2
        * gamma(32 * (x + y + z))
        * float(np.sum((abs(event["cross_spectrum"]) + ew) * multiplicity))
    )
    absolute = abs(event["correlation"])
    peak = event["integer_peak_xyz"]
    ordered = np.sort(absolute.ravel())
    gap = float(ordered[-1] - ordered[-2]) if ordered.size > 1 else math.inf
    assert gap > 2 * inverse_error, "unresolved independent drift peak"
    coordinate_error = np.zeros(3)
    wrap_margin = math.inf
    for axis, extent in enumerate((x, y, z)):
        if extent == 1:
            continue
        lo, mid, hi = event["neighbors_xyz"][axis]
        curvature, slope = abs(hi + lo - 2 * mid), abs(hi - lo) / 2
        assert curvature > 4 * inverse_error, "unresolved independent drift parabola"
        coordinate_error[axis] = (
            inverse_error * (1 + 4 * slope / curvature) / (curvature - 4 * inverse_error)
        )
        coordinate_error[axis] += SHORT * (1 + peak[axis])
        offset = peak_offset(event["neighbors_xyz"][axis])[0]
        margin = abs(peak[axis] + offset - extent // 2) - coordinate_error[axis]
        assert margin > 0, "unresolved drift wrap decision"
        wrap_margin = min(wrap_margin, float(margin))
    return coordinate_error, dict(
        peak_gap=gap,
        correlation=inverse_error,
        peak_margin=gap - 2 * inverse_error,
        wrap_margin=wrap_margin,
        coordinate=coordinate_error,
    )


def _rational_inverse(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix)
    rows = [row.copy() + [Fraction(int(i == j)) for j in range(n)] for i, row in enumerate(matrix)]
    for i in range(n):
        pivot = next(j for j in range(i, n) if rows[j][i])
        rows[i], rows[pivot] = rows[pivot], rows[i]
        divisor = rows[i][i]
        rows[i] = [v / divisor for v in rows[i]]
        for j in range(n):
            if j != i:
                factor = rows[j][i]
                rows[j] = [v - factor * w for v, w in zip(rows[j], rows[i], strict=True)]
    return [row[n:] for row in rows]


def _cubic_error(
    event: dict[str, Any], sample_error: np.ndarray, subtract_directions: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    design = event["matrix"]
    eta = event["evaluation_timestamps_after"]
    values = event["sample_displacements_xy"]
    assert np.all(design == np.rint(design)) and np.all(eta == np.rint(eta)), (
        "noninteger-clock proof not supplied"
    )
    af = [[Fraction(float(v)) for v in row] for row in design]
    gram = [[sum((row[i] * row[j] for row in af), Fraction(0)) for j in range(3)] for i in range(3)]
    inverse = _rational_inverse(gram)
    plus = [
        [sum((inverse[i][k] * af[j][k] for k in range(3)), Fraction(0)) for j in range(len(af))]
        for i in range(3)
    ]
    cf = [[-sum(row, Fraction(0)), *row] for row in plus]
    hf = [
        [
            sum((Fraction(float(time)) ** (k + 1) * plus[k][j] for k in range(3)), Fraction(0))
            for j in range(len(af))
        ]
        for time in eta
    ]
    wf = [[1 - sum(row, Fraction(0)), *row] for row in hf]
    applied_wf = [row.copy() for row in wf]
    if subtract_directions is not None:
        for i, direction in enumerate(subtract_directions):
            if direction > 0:
                applied_wf[i][int(direction)] -= 1

    def floats(rows: list[list[Fraction]]) -> np.ndarray:
        return np.array([[float(value) for value in row] for row in rows])

    def absolute_upper(rows: list[list[Fraction]]) -> np.ndarray:
        # Preserve exact zero dependencies. Round each nonzero rational
        # magnitude outward when converting the exact maps to binary64.
        values = abs(floats(rows))
        return np.where(values == 0, 0.0, np.nextafter(values, np.inf))

    bf = [[Fraction(float(v)) for v in row] for row in values]
    qf = [
        [sum((cf[i][j] * bf[j][axis] for j in range(len(bf))), Fraction(0)) for axis in range(2)]
        for i in range(3)
    ]
    df = [
        [Fraction(int(j == i + 1)) - Fraction(int(j == 0)) for j in range(len(bf))]
        for i in range(len(af))
    ]
    rf = [
        [
            df[i][j] - sum((af[i][k] * cf[k][j] for k in range(3)), Fraction(0))
            for j in range(len(bf))
        ]
        for i in range(len(af))
    ]
    residual_f = [
        [sum((rf[i][j] * bf[j][axis] for j in range(len(bf))), Fraction(0)) for axis in range(2)]
        for i in range(len(af))
    ]
    coefficient_data = absolute_upper(cf) @ sample_error
    q_upper = absolute_upper(qf) + coefficient_data
    residual_upper = absolute_upper(residual_f) + absolute_upper(rf) @ sample_error
    rhs_f = [[bf[i + 1][axis] - bf[0][axis] for axis in range(2)] for i in range(len(af))]
    rhs_upper = absolute_upper(rhs_f) + absolute_upper(df) @ sample_error
    # Same conditional column-scaled backward model as before. Its RHS,
    # coefficient and residual magnitudes now cover ALL measured data in E.
    relative = 2 * gamma(32 * design.size)
    norm_reserve = 1 + gamma(8 * len(af))
    da = np.broadcast_to(relative * norm_reserve * np.linalg.norm(design, axis=0), design.shape)
    db = np.broadcast_to(
        relative * norm_reserve * np.linalg.norm(rhs_upper, axis=0), rhs_upper.shape
    ).copy()
    db += 2 * gamma(2) * rhs_upper
    forcing = db + da @ q_upper
    if len(af) == 3:
        # Square identity (A+dA)(c_actual-c_data)=d_rhs-dA*c_data.
        # A Gram bound would discard useful inverse dependencies here.
        k = absolute_upper(plus) @ da
        z = absolute_upper(plus) @ forcing
        solver_kind = "square-direct"
    else:
        eg = abs(design).T @ da + da.T @ abs(design) + da.T @ da
        k = absolute_upper(inverse) @ eg
        # G A.T=P is retained before taking absolute values. The second
        # term includes the perturbed-data least-squares residual, plus
        # mixed dA*d_rhs and dA*dA*c terms.
        z = absolute_upper(plus) @ forcing
        z += absolute_upper(inverse) @ da.T @ (forcing + residual_upper)
        solver_kind = "rectangular-normal-equations"
    joint_solver = _nonnegative_inverse(k, z)
    # The independent observer's floating nominal coefficient is centered
    # against exact rational Cb explicitly, rather than assuming its residual
    # vanishes exactly. This is source-free observer arithmetic, not product.
    offset_f = [
        [Fraction(float(event["coefficients"][i, axis])) - qf[i][axis] for axis in range(2)]
        for i in range(3)
    ]
    observer_offset = absolute_upper(offset_f)
    solve = joint_solver + observer_offset
    coefficients = coefficient_data + solve
    powers = np.column_stack([eta**j for j in (1, 2, 3)])
    operands = abs(values[0]) + sample_error[0] + abs(powers) @ (q_upper + solve)
    fitted_rounding = 2 * gamma(16) * operands
    applied_rounding = fitted_rounding.copy()
    if subtract_directions is not None:
        for i, direction in enumerate(subtract_directions):
            if direction > 0:
                applied_rounding[i] += (
                    2 * gamma(16) * (abs(values[int(direction)]) + sample_error[int(direction)])
                )
    # A zero-power row with no subtraction returns the shared intercept
    # exactly; no arithmetic reserve or solve error is needed on that row.
    for i, time in enumerate(eta):
        if time == 0 and (subtract_directions is None or subtract_directions[i] == 0):
            fitted_rounding[i] = 0
            applied_rounding[i] = 0
    fitted = absolute_upper(wf) @ sample_error + abs(powers) @ solve + fitted_rounding
    evaluation = absolute_upper(applied_wf) @ sample_error + abs(powers) @ solve + applied_rounding
    return (
        coefficients,
        evaluation,
        dict(
            data_map=floats(applied_wf),
            coefficient_map=floats(cf),
            fitted_data_map=floats(wf),
            fitted_evaluation=fitted,
            solve_arithmetic=solve,
            joint_solver=joint_solver,
            observer_coefficient_offset=observer_offset,
            coefficient_data_error=coefficient_data,
            coefficient_upper_magnitude=q_upper,
            residual_upper_magnitude=residual_upper,
            rhs_upper_magnitude=rhs_upper,
            rhs_error=db,
            design_error=da,
            solver_kind=solver_kind,
            contraction=float(np.max(np.sum(k, axis=1))),
            fitted_evaluation_rounding=fitted_rounding,
            applied_evaluation_rounding=applied_rounding,
            max_data_row_sum=float(np.max(np.sum(abs(floats(applied_wf)), axis=1))),
        ),
    )


def _off_mix_error(
    on: np.ndarray, off: np.ndarray, eo: np.ndarray, ef: np.ndarray, mask: np.ndarray, sign: int
) -> tuple[np.ndarray, dict[str, Any]]:
    def statistics(values: np.ndarray, error: np.ndarray) -> tuple[float, float, float, float]:
        power = np.sum(abs(values) ** 2, axis=0)
        ep = np.sum((2 * abs(values) + error) * error, axis=0)
        ep += 2 * gamma(8 * values.shape[0]) * np.sum((abs(values) + error) ** 2, axis=0)
        means = []
        errors = []
        for region in (mask, ~mask):
            n = int(np.count_nonzero(region))
            assert n > 0
            means.append(float(np.mean(power[region])))
            errors.append(
                float(
                    np.sum(ep[region]) / n + 2 * gamma(8 * n) * np.mean(power[region] + ep[region])
                )
            )
        return (
            means[1],
            means[0] - means[1],
            errors[1],
            sum(errors) + 2 * gamma(4) * sum(abs(v) for v in means),
        )

    no, so, eno, eso = statistics(on, eo)
    nf, sf, enf, esf = statistics(off, ef)
    assert no > eno and nf > enf, "unresolved off noise divisor"
    bothzero = so <= 0 and sf <= 0
    if bothzero:
        assert so + eso < 0 and sf + esf < 0, "unresolved both-zero off decision"
        so = sf = 1.0
        eso = esf = 0.0
    else:
        if so <= 0:
            assert so + eso < 0, "unresolved on signal clip"
            so, eso = 0.0, 0.0
        else:
            assert so > eso, "unresolved positive on signal"
        if sf <= 0:
            assert sf + esf < 0, "unresolved off signal clip"
            sf, esf = 0.0, 0.0
        else:
            assert sf > esf, "unresolved positive off signal"

    def ratio(s: float, es: float, noise: float, en: float) -> tuple[float, float]:
        root = math.sqrt(s)
        eroot = math.sqrt(s + es) - math.sqrt(max(s - es, 0)) if es else 0.0
        eroot += SHORT * root
        value = root / noise
        return value, (eroot + abs(value) * en) / (noise - en) + SHORT * abs(value)

    u, eu = ratio(so, eso, no, eno)
    v, ev = ratio(sf, esf, nf, enf)
    den = u + v
    ed = eu + ev + 2 * gamma(4) * (abs(u) + abs(v) + eu + ev)
    assert den > ed, "unresolved off mixture denominator"
    a, b = u / den, v / den
    ea = (eu + abs(a) * ed) / (den - ed) + SHORT * abs(a)
    eb = (ev + abs(b) * ed) / (den - ed) + SHORT * abs(b)
    error = (abs(a) + ea) * eo + (abs(b) + eb) * ef + abs(on) * ea + abs(off) * eb
    error += SHORT * ((abs(a) + ea) * (abs(on) + eo) + (abs(b) + eb) * (abs(off) + ef))
    return error, dict(
        both_zero=bothzero,
        on_noise=no,
        off_noise=nf,
        on_weight=a,
        off_weight=b,
        weight_error=(ea, eb),
        signal_squared=(so, sf),
        signal_error=(eso, esf),
        sign=sign,
    )


def preparation_errors(case: Case, prep: dict[str, Any]) -> dict[str, Any]:
    case = reinterpret(case)
    a, c, _ = case.resolved()
    raw = case.raw
    t, d, p, z, y, x = raw.shape
    off = case.extras.get("off_exposures")
    n = 0 if off is None else off.shape[4]
    extra = case.extras.get("exposure_background", np.zeros((t, d, p, z)))
    alpha = prep["input_scale"]
    bg = np.broadcast_to(a["background"], (y, x)).astype(float).copy()
    slope = np.ones((y, x)) if a["flatfield_slope"] is None else a["flatfield_slope"].copy()
    e_on = np.zeros_like(prep["quadratures"], dtype=float)
    e_off = None if n == 0 else np.zeros_like(e_on)
    e_sums = np.zeros((t, d, p, z))
    e_off_sums = np.zeros_like(e_sums)
    e_gains = np.zeros_like(e_sums)
    e_off_gains = np.zeros_like(e_sums)
    e_matrices = np.zeros_like(prep["separation_matrices"])
    e_noise = np.zeros_like(prep["noise_variance_factors"])
    e_phases = np.zeros_like(prep["phase_angles_rad"])
    e_between = np.zeros_like(prep["between_displacements_pixels"])
    e_exposure = np.zeros_like(prep["exposure_displacements_pixels"])
    cubics = []
    correlations = []
    mix_reports = []
    previous = 0.0
    _, linkage = initial_vectors(case)
    fx, fy = np.meshgrid(np.arange(x // 2 + 1) / x, np.array([lift(i, y) for i in range(y)]) / y)

    def load(frame: np.ndarray, offset: float) -> tuple[np.ndarray, np.ndarray]:
        data = frame.copy()
        if data[-1, -1] == -1:
            data[-1, -1] = data[-1, -2]
            bg[-1, -1] = bg[-1, -2]
            slope[-1, -1] = 1
        result = alpha * slope * (data - bg - offset)
        error = 2 * gamma(32) * alpha * abs(slope) * (abs(data) + abs(bg) + abs(offset))
        return result, error

    for it in range(t):
        between_events = [
            ev for ev in prep["events"] if ev["kind"] == "between" and ev["time"] == it
        ]
        if between_events:
            subz = max(z // 2, 1)
            first = (z - subz) // 2
            centers = np.zeros((d, subz, y, x))
            errors = np.zeros_like(centers)
            for di in range(d):
                for h in range(subz):
                    for ph in range(p):
                        inputs = [raw[it, di, ph, first + h]]
                        if off is not None:
                            inputs.append(off[it, di, ph, first + h, 0])
                        for frame in inputs:
                            data = frame.copy()
                            if data[-1, -1] == -1:
                                data[-1, -1] = data[-1, -2]
                            term = (data - bg) / (p * x * y * z)
                            errors[di, h] += 2 * gamma(32) * (abs(data) + abs(bg)) / (p * x * y * z)
                            errors[di, h] += 2 * gamma(4) * (abs(centers[di, h]) + abs(term))
                            centers[di, h] += term
                    centers[di, h], errors[di, h] = _edge_model(centers[di, h], errors[di, h], 10)
            e_ft = _fourier_error(centers, errors, (1, 2, 3))[..., : x // 2 + 1]
            for event in between_events:
                di = event["direction"]
                vector, report = _correlation_error(event, e_ft[0], e_ft[di], case)
                e_between[it, di] = vector
                correlations.append(dict(kind="between", time=it, direction=di, **report))
        if a["drift_within"] and z > 1:
            event = next(ev for ev in prep["events"] if ev["kind"] == "cubic" and ev["time"] == it)
            directions = np.repeat(np.arange(d), z * p)
            ec, ee, report = _cubic_error(event, e_between[it, :, :2], directions)
            e_exposure[it] = ee.reshape(d, z, p, 2)
            cubics.append(dict(time=it, direction=None, coefficients=ec, evaluated=ee, **report))
        for di in range(d):
            for zi in range(z):
                on_values = []
                on_errors = []
                off_values = []
                off_errors = []
                for ph in range(p):
                    if off is not None:
                        total = np.zeros((y, x))
                        etotal = np.zeros_like(total)
                        for exposure in range(n):
                            value, error = load(off[it, di, ph, zi, exposure], previous)
                            etotal += error + 2 * gamma(4) * (abs(total) + abs(value))
                            total += value
                        value, error = _edge_model(total, etotal, a["edge_pixels"])
                        off_values.append(value)
                        off_errors.append(error)
                    value, error = load(raw[it, di, ph, zi], float(extra[it, di, ph, zi]))
                    value, error = _edge_model(value, error, a["edge_pixels"])
                    on_values.append(value)
                    on_errors.append(error)
                    previous = float(extra[it, di, ph, zi])

                def equalized(
                    values: list[np.ndarray],
                    errors: list[np.ndarray],
                    sums: np.ndarray,
                    sums_error: np.ndarray,
                    gains: np.ndarray,
                    gain_error: np.ndarray,
                    enabled: bool,
                    *,
                    it: int = it,
                    di: int = di,
                    zi: int = zi,
                ) -> tuple[np.ndarray, np.ndarray]:
                    data = np.array(values)
                    error = np.array(errors)
                    sums_error[it, di, :, zi] = np.sum(error, axis=(1, 2)) + 2 * gamma(
                        8 * x * y
                    ) * np.sum(abs(data) + error, axis=(1, 2))
                    if enabled:
                        index = (
                            0 if a["equalize_time"] else it,
                            0,
                            0,
                            0 if a["equalize_z"] else zi,
                        )
                        er = sums_error[index]
                        for ph in range(p):
                            s = sums[it, di, ph, zi]
                            es = sums_error[it, di, ph, zi]
                            assert abs(s) > es, "unresolved equalization divisor"
                            g = gains[it, di, ph, zi]
                            eg = (er + abs(g) * es) / (abs(s) - es) + SHORT * abs(g)
                            gain_error[it, di, ph, zi] = eg
                            error[ph] = (
                                (abs(g) + eg) * error[ph]
                                + abs(data[ph]) * eg
                                + SHORT * abs(g * data[ph])
                            )
                            data[ph] *= g
                    ef = _fourier_error(data, error, (1, 2))[..., : x // 2 + 1]
                    return data, ef

                _, e_lateral = equalized(
                    on_values,
                    on_errors,
                    prep["frame_sums"],
                    e_sums,
                    prep["equalization_gains"],
                    e_gains,
                    a["equalize"],
                )
                e_off_lateral = None
                if off is not None:
                    _, e_off_lateral = equalized(
                        off_values,
                        off_errors,
                        prep["off_frame_sums"],
                        e_off_sums,
                        prep["off_equalization_gains"],
                        e_off_gains,
                        a["equalize"] and n > 1,
                    )
                if a["drift_within"] and z == 1:
                    assert e_off_lateral is not None
                    before = prep["before_ramp"][it, di, zi]
                    off_before = prep["off_before_ramp"][it, di, zi]
                    e_ref = (
                        e_lateral[0]
                        + e_off_lateral[0]
                        + SHORT * (abs(before[0]) + abs(off_before[0]))
                    )
                    for event in prep["events"]:
                        if (
                            event["kind"] == "within"
                            and event["time"] == it
                            and event["direction"] == di
                        ):
                            ph = event["phase"]
                            e_mov = (
                                e_lateral[ph]
                                + e_off_lateral[ph]
                                + SHORT * (abs(before[ph]) + abs(off_before[ph]))
                            )
                            vector, report = _correlation_error(
                                event, e_ref[None], e_mov[None], case
                            )
                            e_exposure[it, di, zi, ph] = vector[:2]
                            correlations.append(
                                dict(kind="within", time=it, direction=di, phase=ph, **report)
                            )
                    if a["fit_drift"]:
                        event = next(
                            ev
                            for ev in prep["events"]
                            if ev["kind"] == "cubic" and ev["time"] == it and ev["direction"] == di
                        )
                        ec, ee, report = _cubic_error(event, e_exposure[it, di, zi].copy(), None)
                        e_exposure[it, di, zi] = ee
                        cubics.append(
                            dict(time=it, direction=di, coefficients=ec, evaluated=ee, **report)
                        )
                if a["drift_within"]:
                    for ph in range(p):
                        ex, ey = e_exposure[it, di, zi, ph]
                        dx, dy = prep["exposure_displacements_pixels"][it, di, zi, ph]
                        phase_error = 2 * np.pi * (abs(fx) * ex + abs(fy) * ey) + SHORT * (
                            1 + abs(2 * np.pi * (dx * fx + dy * fy))
                        )
                        e_lateral[ph] += (
                            abs(prep["before_ramp"][it, di, zi, ph]) + e_lateral[ph]
                        ) * phase_error
                        if e_off_lateral is not None:
                            e_off_lateral[ph] += (
                                abs(prep["off_before_ramp"][it, di, zi, ph]) + e_off_lateral[ph]
                            ) * phase_error
                phases = prep["phase_angles_rad"][it, di, zi]
                ep = 2 * gamma(16) * (1 + abs(phases))
                if a["drift_within"] and a["adjust_phases"]:
                    ep += 2 * np.pi * a["dxy_um"] * (e_exposure[it, di, zi] @ abs(linkage[di]))
                    link_error = (
                        SHORT
                        * float(np.linalg.norm(linkage[di]))
                        * (1 + abs(c["phase_start_angle_rad"]) + np.pi)
                    )
                    ep += (
                        2
                        * np.pi
                        * a["dxy_um"]
                        * np.sum(abs(prep["exposure_displacements_pixels"][it, di, zi]), axis=1)
                        * link_error
                    )
                    ep += SHORT * (1 + abs(phases))
                e_phases[it, di, zi] = ep
                uniform = not (
                    a["phases_rad"] is not None
                    or a["phase_steps_rad"] is not None
                    or (a["drift_within"] and a["adjust_phases"])
                )
                matrix = prep["separation_matrices"][it, di, zi]
                em, design, ed = _phase_inverse_model(phases, matrix, ep, a["norders"], uniform)
                e_matrices[it, di, zi] = em
                on_after = prep["after_ramp"][it, di, zi]
                e_on[it, di, :, zi] = _separate_error(
                    on_after, e_lateral, matrix, design, ed, em, uniform
                )
                if e_off is not None and e_off_lateral is not None:
                    e_off[it, di, :, zi] = _separate_error(
                        prep["off_after_ramp"][it, di, zi],
                        e_off_lateral,
                        matrix,
                        design,
                        ed,
                        em,
                        uniform,
                    )
                if not uniform:
                    row_error = np.sum((2 * abs(matrix) + em) * em, axis=1) / p
                    row_error += 2 * gamma(8 * p) * np.sum((abs(matrix) + em) ** 2, axis=1) / p
                    e_noise[it, di, 0] = row_error[0]
                    for m in range(1, a["norders"]):
                        e_noise[it, di, m] = row_error[2 * m - 1] + row_error[2 * m]
                for event in prep["mixtures"]:
                    if (event["time"], event["direction"], event["z"]) == (it, di, zi):
                        assert e_off is not None
                        m = event["order"]
                        slots = slice(0, 1) if m == 0 else slice(2 * m - 1, 2 * m + 1)
                        error, report = _off_mix_error(
                            event["on"],
                            event["off"],
                            e_on[it, di, slots, 0],
                            e_off[it, di, slots, 0],
                            event["mask"],
                            1 if m == 0 else -1,
                        )
                        e_on[it, di, slots, 0] = error
                        mix_reports.append(dict(time=it, direction=di, z=zi, order=m, **report))
            if a["acquisition_mode"] == "3d":
                e_on[it, di] = _fourier_error(prep["pre_axial"][it, di], e_on[it, di], (1,))
            if a["drift_between"] and di > 0:
                ez = np.array([abs(lift(k, z) / z) for k in range(z)])
                ex, ey, ezz = e_between[it, di]
                ephase = (
                    2 * np.pi * (abs(fx)[None] * ex + abs(fy)[None] * ey + ez[:, None, None] * ezz)
                    + SHORT
                )
                e_on[it, di] += (abs(prep["quadratures"][it, di]) + e_on[it, di]) * ephase
    return dict(
        quadratures=e_on,
        off_quadratures=e_off,
        noise_variance_factors=e_noise,
        separation_matrices=e_matrices,
        phase_angles_rad=e_phases,
        frame_sums=e_sums,
        off_frame_sums=None if n == 0 else e_off_sums,
        equalization_gains=e_gains,
        off_equalization_gains=None if n == 0 else e_off_gains,
        between_displacements_pixels=e_between,
        exposure_displacements_pixels=e_exposure,
        cubics=cubics,
        correlations=correlations,
        mixtures=mix_reports,
    )


def calibration_errors(case: Case, cal: dict[str, Any]) -> dict[str, Any]:
    """Propagate raw empirical observations, including normalization and phase."""
    assert case.bead is not None
    raw, settings = case.bead
    s: dict[str, Any] = BEAD_DEFAULTS | settings
    p, z, y, x = raw.shape
    frames = np.empty_like(raw)
    errors = np.zeros_like(raw)
    bg = cal["background_counts"]
    ebg = np.zeros_like(bg)
    prebackground = np.empty_like(raw)
    preerror = np.zeros_like(raw)
    for iz in range(z):
        for ph in range(p):
            data = raw[ph, iz].copy()
            if data[-1, -1] < 0:
                data[-1, -1] = data[-1, -2]
            error = np.zeros((y, x))
            if s["exposure_background_counts"] is not None:
                pass
            elif s["background_map"] is not None:
                error = 2 * gamma(16) * (abs(data) + abs(s["background_map"])) * abs(s["slope_map"])
                data = (data - s["background_map"]) * s["slope_map"]
            elif s["background_counts"] is None:
                yy, xx = np.indices((y, x))
                mask = ((yy < 20) | (yy > y - 20)) & ((xx < 20) | (xx > x - 20))
                count = int(np.count_nonzero(mask))
                ebg[iz, ph] = float(
                    np.sum(error[mask]) / count
                    + 2 * gamma(8 * count) * np.mean(abs(data[mask]) + error[mask])
                )
            data, error = _edge_model(data, error, 10, bead=True)
            prebackground[ph, iz], preerror[ph, iz] = data, error
            frames[ph, iz] = data - bg[iz, ph]
            errors[ph, iz] = error + ebg[iz, ph] + 2 * gamma(4) * (abs(data) + abs(bg[iz, ph]))
    average = cal["center_average"]
    eaverage = np.mean(preerror, axis=0) + 2 * gamma(8 * p) * np.mean(
        abs(prebackground) + preerror, axis=0
    )
    maximum = np.max(average)
    index = np.unravel_index(np.argmax(average), average.shape)
    ordered = np.sort(average.ravel())
    peak_gap = float(ordered[-1] - ordered[-2])
    assert peak_gap > 2 * float(np.max(eaverage)), "unresolved empirical center peak"
    center_error = np.zeros(3)
    for axis, n in enumerate((x, y, z)):
        if n == 1:
            continue
        positions = list(index)
        aindex = 2 - axis
        values = []
        ev = []
        for offset in (-1, 0, 1):
            positions[aindex] = (index[aindex] + offset) % n
            values.append(float(average[tuple(positions)]))
            ev.append(float(eaverage[tuple(positions)]))
        lo, mid, hi = values
        el, ec, eh = ev
        curvature = hi + lo - 2 * mid
        slope = (hi - lo) / 2
        ed = eh + el + 2 * ec
        es = (eh + el) / 2
        assert abs(curvature) > ed, "unresolved empirical center curvature"
        center_error[axis] = (es + abs(slope / curvature) * ed) / (abs(curvature) - ed) + 2 * gamma(
            64
        ) * (1 + abs(slope / curvature))
    phases = 2 * np.pi * np.arange(p) / p
    matrix, _ = phase_matrix(phases, (p + 1) // 2, True)
    matrix = matrix / p
    separated = np.tensordot(matrix, frames, axes=1)
    e_sep = np.tensordot(abs(matrix), errors, axes=1)
    e_sep += (
        2
        * gamma(128)
        * np.sum(abs(frames), axis=0)[None]
        / p
        * (1 + max(1.0, float(np.max(abs(phases))) * (p // 2)))
    )
    transformed = finite_transform(separated, (1, 2, 3), -1)[..., : x // 2 + 1]
    # Direct observer and external backend each obey this explicitly counted
    # transform model; no assertion about an unexamined FFT implementation.
    transform_ops = 0
    for length in (z, y, x):
        maxarg = 2 * np.pi * (length - 1) ** 2 / length
        transform_ops += math.ceil(2 * maxarg + 8 * length + 16)
    e_transform = np.sum(e_sep, axis=(1, 2, 3))
    e_transform += 2 * gamma(transform_ops) * np.sum(abs(separated) + e_sep, axis=(1, 2, 3))
    radial = np.zeros((p, x // 2 + 1, z), dtype=complex)
    er = np.zeros(radial.shape)
    counts = np.zeros(x // 2 + 1, dtype=int)
    center = cal["center_pixels_xyz"]
    for iy in range(y):
        for ix in range(x // 2 + 1):
            radius = round(math.hypot(ix, lift(iy, y)))
            if radius > x // 2:
                continue
            counts[radius] += 1
            for iz in range(z):
                phase = (
                    2
                    * np.pi
                    * (
                        ix * center[0] / x
                        + lift(iy, y) * center[1] / y
                        + lift(iz, z) * center[2] / z
                    )
                )
                ep = (
                    2
                    * np.pi
                    * (
                        ix * center_error[0] / x
                        + abs(lift(iy, y)) * center_error[1] / y
                        + abs(lift(iz, z)) * center_error[2] / z
                    )
                )
                ep += 2 * gamma(128) * (1 + abs(phase))
                values = transformed[:, iz, iy, ix] * np.exp(1j * phase)
                error = e_transform + (abs(transformed[:, iz, iy, ix]) + e_transform) * ep
                if s["compensate_bead"]:
                    for slot in range(p):
                        order = (slot + 1) // 2
                        rho = math.sqrt(
                            (
                                ix / (y * s["dxy_um"])
                                + order
                                * math.cos(s["carrier_angle_rad"])
                                / ((p // 2) * s["linespacing_um"])
                            )
                            ** 2
                            + (
                                lift(iy, y) / (y * s["dxy_um"])
                                + order
                                * math.sin(s["carrier_angle_rad"])
                                / ((p // 2) * s["linespacing_um"])
                            )
                            ** 2
                            + (lift(iz, z) / (z * s["dz_um"])) ** 2
                        )
                        argument = np.pi * s["bead_diameter_um"] * rho
                        if argument == 0:
                            sphere, es = 1.0, 0.0
                        else:
                            terms = [
                                6
                                * (k + 1)
                                * (-1) ** k
                                * argument ** (2 * k)
                                / math.factorial(2 * k + 3)
                                for k in range(20)
                            ]
                            sphere = (
                                sum(terms)
                                if abs(argument) <= 2
                                else 3
                                * (math.sin(argument) - argument * math.cos(argument))
                                / argument**3
                            )
                            direct = 6 * gamma(32) * (
                                abs(math.sin(argument)) + abs(argument * math.cos(argument))
                            ) / abs(argument) ** 3 + 2 * gamma(16) * abs(sphere)
                            tail = 6 * 21 * abs(argument) ** 40 / math.factorial(43)
                            series = 2 * gamma(160) * sum(abs(v) for v in terms) + tail
                            es = max(direct, series) + SHORT * abs(argument)
                        assert abs(sphere) > es, "unresolved bead compensation divisor"
                        error[slot] = (error[slot] + abs(values[slot] / sphere) * es) / (
                            abs(sphere) - es
                        ) + SHORT * abs(values[slot] / sphere)
                        values[slot] /= sphere
                er[:, radius, iz] += error + 2 * gamma(4) * (
                    abs(radial[:, radius, iz]) + abs(values)
                )
                radial[:, radius, iz] += values
    for r in range(x // 2 + 1):
        if counts[r]:
            radial[:, r] /= counts[r]
            er[:, r] = er[:, r] / counts[r] + 2 * gamma(4) * abs(radial[:, r])
        radial[:, r, 0] = np.real(radial[:, r, 0])
        for j in range(1, z // 2 + 1):
            value = (radial[:, r, j] + radial[:, r, z - j].conj()) / 2
            error = (er[:, r, j] + er[:, r, z - j]) / 2 + 2 * gamma(8) * (
                abs(radial[:, r, j]) + abs(radial[:, r, z - j])
            ) / 2
            radial[:, r, j], radial[:, r, z - j] = value, value.conj()
            er[:, r, j], er[:, r, z - j] = error, error
    if s["fix_axial_axis"]:
        for slot in range(p):
            for iz in range(z):
                if slot or iz:
                    radial[slot, 0, iz] = radial[slot, 1, iz]
                    er[slot, 0, iz] = er[slot, 1, iz]
    if s["fix_radial_from"]:
        for r in range(s["fix_radial_from"], x // 2 + 1):
            for slot in range(p):
                flat = radial[slot].ravel()
                ef = er[slot].ravel()
                assert r * z + 1 < flat.size
                value = (flat[r * z + 1] + flat[r * z + z - 1]) / 2
                error = (ef[r * z + 1] + ef[r * z + z - 1]) / 2 + 2 * gamma(8) * (
                    abs(flat[r * z + 1]) + abs(flat[r * z + z - 1])
                ) / 2
                radial[slot, r, 0], er[slot, r, 0] = value, error
    cleanup_margin = math.inf
    l11, l12, l2 = s["cleanup_axial_bins"]
    if l11:
        for slot in range(p):
            m = (slot + 1) // 2
            aperture = s["numerical_aperture"] * (1 if m == 0 else 0.92)
            theta = math.asin(aperture / s["immersion_index"])
            wavelength = s["wavelength_nm"] / 1000
            for r in range(x // 2 + 1):
                kr = r / (y * s["dxy_um"])
                if kr > 2 * aperture / wavelength:
                    radial[slot, r] = 0
                    er[slot, r] = 0
                    continue
                beta = math.asin((aperture - kr * wavelength) / s["immersion_index"])
                width = (
                    s["immersion_index"]
                    / wavelength
                    * (math.cos(beta) - math.cos(theta))
                    * z
                    * s["dz_um"]
                )
                indices = []
                argument = width + 1 if m == 0 else width + 0.999
                margin = abs(argument - (math.floor(argument) + 0.5))
                cleanup_margin = min(cleanup_margin, margin)
                assert margin > SHORT * (1 + abs(argument)), "unresolved cleanup integer decision"
                if m == 0:
                    start = round(width + 1)
                    indices = list(range(start, z - start + 1))
                elif m == 1:
                    h = round(width + 0.999)
                    for j in range(l11 - h + 1):
                        indices.extend([j] if j == 0 else [j, z - j])
                    for j in range(l12 + h + 1, z // 2 + 1):
                        indices.extend([j, z - j])
                else:
                    for j in range(l2 + round(width + 0.999), z // 2 + 1):
                        indices.extend([j, z - j])
                for j in indices:
                    address = r * z + j
                    assert 0 <= address < radial[slot].size
                    radial[slot].ravel()[address] = 0
                    er[slot].ravel()[address] = 0
    if s["origin_fit_bins"] is not None:
        first, last = s["origin_fit_bins"]
        rr = np.arange(first, last + 1, dtype=float)
        midpoint = (first + last) / 2
        delta = rr - midpoint
        for r in range(first):
            weights = np.ones(len(rr)) / len(rr) + (r - midpoint) * delta / np.sum(delta**2)
            ev = np.sum(er[0, first : last + 1], axis=1) + 2 * gamma(8 * z) * np.sum(
                abs(radial[0, first : last + 1]) + er[0, first : last + 1], axis=1
            )
            fit = float(np.dot(weights, np.sum(np.real(radial[0, first : last + 1]), axis=1)))
            fit_error = float(np.dot(abs(weights), ev)) + SHORT * float(
                np.dot(abs(weights), np.sum(abs(radial[0, first : last + 1]), axis=1))
            )
            unchanged = 0.0 if r == 0 else float(np.sum(er[0, r, 1:]))
            value = fit if r == 0 else fit - np.sum(np.real(radial[0, r, 1:]))
            radial[0, r, 0] = value + 1j * np.imag(radial[0, r, 0])
            er[0, r, 0] = fit_error + unchanged + er[0, r, 0] + SHORT * (abs(value) + abs(fit))
    normalized = np.zeros_like(er)
    factor_error = np.zeros(p)
    for slot in range(p):
        source = slot if s["rescale_each"] else 0
        maximum = float(np.max(abs(cal["pre_normalization"][source])))
        em = float(np.max(er[source])) + 2 * gamma(8) * maximum
        assert maximum > em, "unresolved empirical normalization"
        factor_error[slot] = em / (maximum * (maximum - em)) + 2 * gamma(8) / (maximum - em)
        normalized[slot] = er[slot] / (maximum - em) + abs(cal["pre_normalization"][slot]) * em / (
            maximum * (maximum - em)
        )
        normalized[slot] += 2 * gamma(8) * (abs(cal["quadratures"][slot]) + normalized[slot])
    transfer = [normalized[0]]
    angle_errors = []
    sign_margins = []
    for m in range(1, (p + 1) // 2):
        cosine, sine = cal["quadratures"][2 * m - 1 : 2 * m + 1]
        ec, es = normalized[2 * m - 1 : 2 * m + 1]
        a0, b0 = float(np.sum(abs(cosine))), float(np.sum(abs(sine)))
        ea = float(np.sum(ec)) + 2 * gamma(8 * cosine.size) * float(np.sum(abs(cosine) + ec))
        eb = float(np.sum(es)) + 2 * gamma(8 * sine.size) * float(np.sum(abs(sine) + es))
        norm = math.hypot(a0, b0)
        assert a0 > ea and math.hypot(ea, eb) < norm, "unresolved empirical side angle"
        ephi = math.asin(math.hypot(ea, eb) / norm) + SHORT * (
            1 + abs(cal["quadrature_angles_rad"][m - 1])
        )
        sign_margin = min(
            abs(float(np.real(cosine[x // 8, 0]))) - ec[x // 8, 0],
            abs(float(np.real(sine[x // 8, 0]))) - es[x // 8, 0],
        )
        assert sign_margin > 0, "unresolved empirical quadrant"
        sign_margins.append(float(sign_margin))
        phi = cal["quadrature_angles_rad"][m - 1]
        value = abs(math.cos(phi)) * ec + abs(math.sin(phi)) * es
        value += (np.hypot(abs(cosine), abs(sine)) + np.hypot(ec, es)) * ephi
        value += SHORT * (abs(cosine) + abs(sine) + ec + es)
        transfer.append(value)
        angle_errors.append(ephi)
    return dict(
        samples=np.asarray(transfer),
        quadratures=normalized,
        normalization_factors=factor_error,
        center_pixels_xyz=center_error,
        background_counts=ebg,
        quadrature_angles_rad=np.asarray(angle_errors),
        peak_margin=peak_gap - 2 * float(np.max(eaverage)),
        quadrant_margin=min(sign_margins),
        cleanup_margin=cleanup_margin,
        model=(
            "counted two-evaluation arithmetic/FFT; stable center and quadrant; "
            "not a backend certificate"
        ),
    )


def _table_slopes(table: Table, order: int) -> tuple[float, float]:
    h = table.samples[order]
    if table.layout == "radial":
        lateral = float(np.max(abs(np.diff(h, axis=0)))) / table.dkr if h.shape[0] > 1 else 0.0
        axial = float(np.max(abs(np.roll(h, -1, axis=1) - h))) / table.dkz
    else:
        gx = float(np.max(abs(np.diff(h, axis=2)))) / table.dkr if h.shape[2] > 1 else 0.0
        gy = float(np.max(abs(np.roll(h, -1, axis=1) - h))) / table.dkr
        lateral = math.hypot(gx, gy)
        axial = float(np.max(abs(np.roll(h, -1, axis=0) - h))) / table.dkz
    return lateral, axial


@dataclass
class _SampleFacts:
    """Own lazily reached facts for one unchanged table/error-array pair."""

    table: Table
    table_error: np.ndarray
    slopes: dict[int, tuple[float, float]] = field(default_factory=dict)
    maxima: dict[int, float] = field(default_factory=dict)
    sample_implementation: Any = field(
        default_factory=lambda original=Table.sample: original, init=False, repr=False
    )


def _sample_error(
    table: Table,
    order: int,
    xy: np.ndarray,
    iz: int,
    dkz: float,
    table_error: np.ndarray,
    position_error: float,
    *,
    facts: _SampleFacts | None = None,
) -> tuple[complex, float]:
    value = table.sample(float(xy[0]), float(xy[1]), iz, dkz, order)
    cached = (
        facts
        if facts is not None
        and facts.table is table
        and facts.table_error is table_error
        and type(table) is Table
        and type(table.samples) is np.ndarray
        and type(table_error) is np.ndarray
        and getattr(table.sample, "__func__", None) is facts.sample_implementation
        else None
    )
    if cached is None:
        lateral, axial = _table_slopes(table, order)
    else:
        if order not in cached.slopes:
            cached.slopes[order] = _table_slopes(table, order)
        lateral, axial = cached.slopes[order]
    er = position_error + SHORT * float(np.linalg.norm(xy))
    ez = SHORT * abs(iz * dkz)
    if table.layout == "full" and xy[0] != 0:
        assert abs(xy[0]) > position_error + SHORT * abs(xy[0]), "unresolved full-table reflection"
    if cached is None:
        maximum = float(np.max(table_error[order]))
    else:
        if order not in cached.maxima:
            cached.maxima[order] = float(np.max(table_error[order]))
        maximum = cached.maxima[order]
    error = maximum + lateral * er + axial * ez + SHORT * (1 + abs(value))
    return value, error


def _radius_decision(
    xy: np.ndarray, radius: float, uncertainty: float, *, inclusive: bool
) -> tuple[bool, float, bool]:
    r = math.hypot(float(xy[0]), float(xy[1]))
    margin = abs(r - radius)
    if r == radius and uncertainty == 0:
        # Exact rational certificate for correctly rounded norm on these
        # concrete binary64 coordinates. A four-ulp norm premise alone is
        # insufficient; this extra finite-decision premise is explicit.
        rr = Fraction(float(radius))
        lower = (rr + Fraction(float(np.nextafter(radius, -np.inf)))) / 2
        upper = (rr + Fraction(float(np.nextafter(radius, np.inf)))) / 2
        square = Fraction(float(xy[0])) ** 2 + Fraction(float(xy[1])) ** 2
        assert lower * lower < square < upper * upper, (
            "equality norm rounding certificate unavailable"
        )
        return inclusive, 0.0, True
    arithmetic = SHORT * (r + radius)
    assert margin > uncertainty + arithmetic, "unresolved support comparison"
    return (r <= radius if inclusive else r < radius), margin - uncertainty - arithmetic, False


def _full_error(quadratures: np.ndarray, order: int) -> np.ndarray:
    z, y, xh = quadratures.shape[1:]
    x = (xh - 1) * 2
    result = np.empty((z, y, x))
    for iz, iy, ix in np.ndindex(result.shape):
        values = (
            quadratures[:, iz, iy, ix] if ix <= x // 2 else quadratures[:, -iz % z, -iy % y, x - ix]
        )
        result[iz, iy, ix] = values[0] if order == 0 else values[2 * order - 1] + values[2 * order]
    return result


def overlap_errors(
    case: Case,
    prep: dict[str, Any],
    prep_error: dict[str, Any],
    build: dict[str, Any],
    table_error: np.ndarray,
    carrier_error: float,
    *,
    sample_facts: _SampleFacts | None = None,
) -> dict[str, Any]:
    if sample_facts is None:
        sample_facts = _SampleFacts(case.table, table_error)
    a, _, f = case.resolved()
    quadratures = prep["quadratures"][build["time_index"], build["direction_index"]]
    eq = prep_error["quadratures"][build["time_index"], build["direction_index"]]
    z, y, xh = quadratures.shape[1:]
    x = (xh - 1) * 2
    lo, hi = build["orders"]
    bands = (full_band(quadratures, lo), full_band(quadratures, hi))
    errors = (_full_error(eq, lo), _full_error(eq, hi))
    for branch, m in enumerate((lo, hi)):
        if m:
            errors[branch][:] += SHORT * (abs(full_band(quadratures, m)))
    delta = (hi - lo) * build["carrier_cyc_um"]
    edelta = (hi - lo) * carrier_error
    dkz = 1 / (z * a["dz_um"]) if a["dz_um"] > 0 else case.table.dkz
    le = OPTICS["wavelength_nm"] / OPTICS["immersion_index"] / 1000
    theta = math.asin(OPTICS["numerical_aperture"] / OPTICS["immersion_index"])
    cutoff = math.ceil((1 - math.cos(theta)) / le / dkz)
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    radius = min(
        2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000), 1 / (2 * a["dxy_um"])
    )
    factor = 1 if a["acquisition_mode"] == "2d" else 5
    ef = np.zeros_like(build["fourier"], dtype=float)
    margin = math.inf
    threshold = math.inf
    equalities = 0
    for iy in range(y):
        for ix in range(x):
            xy = np.array([lift(ix, x) / (x * a["dxy_um"]), lift(iy, y) / (y * a["dxy_um"])])
            native, mg, eq0 = _radius_decision(xy, radius, 0.0, inclusive=True)
            if not eq0:
                margin = min(margin, mg)
            equalities += int(eq0)
            if not native:
                continue
            for branch in (0, 1):
                shifted = xy + (-delta if branch == 0 else delta)
                inside, mg, eq0 = _radius_decision(shifted, radius, edelta, inclusive=True)
                if not eq0:
                    margin = min(margin, mg)
                equalities += int(eq0)
                if not inside:
                    continue
                m, other = (lo, hi) if branch == 0 else (hi, lo)
                for iz in range(-cutoff, cutoff + 1):
                    if f["omit_kz0"] and iz == 0:
                        continue
                    h1, e1 = _sample_error(
                        case.table, m, xy, iz, dkz, table_error, 0.0, facts=sample_facts
                    )
                    scale1 = 1 if m == 0 else factor
                    gap = abs(scale1 * abs(h1) - 0.006) - scale1 * e1
                    assert gap > 0, "unresolved first overlap threshold"
                    threshold = min(threshold, gap)
                    if scale1 * abs(h1) <= 0.006:
                        continue
                    h2, e2 = _sample_error(
                        case.table, other, shifted, iz, dkz, table_error, edelta, facts=sample_facts
                    )
                    scale2 = 1 if other == 0 else factor
                    gap = abs(scale2 * abs(h2) - 0.006) - scale2 * e2
                    assert gap > 0, "unresolved second overlap threshold"
                    threshold = min(threshold, gap)
                    if scale2 * abs(h2) <= 0.006:
                        continue
                    den = math.hypot(abs(h1), abs(h2))
                    ed = math.hypot(e1, e2)
                    assert den > ed
                    weight = abs(h2) / den
                    ew = (e2 + weight * ed) / (den - ed) + SHORT
                    value = bands[branch][iz % z, iy, ix]
                    eb = errors[branch][iz % z, iy, ix]
                    ef[branch, iz % z, iy, ix] = (
                        weight * eb + (abs(value) + eb) * ew + SHORT * (1 + abs(value))
                    )
    n = z * y * x
    spatial = []
    point = []
    for branch in (0, 1):
        arithmetic = (
            2 * gamma(32 * (x + y + z)) * float(np.sum(abs(build["fourier"][branch]) + ef[branch]))
        )
        spatial.append(
            math.sqrt(n) * float(np.linalg.norm(ef[branch].ravel())) + math.sqrt(n) * arithmetic
        )
        point.append(min(float(np.sum(ef[branch])) + arithmetic, spatial[-1]))
    return dict(
        fourier=ef,
        spatial_l2=np.asarray(spatial),
        spatial_point=np.asarray(point),
        support_margin=margin,
        threshold_margin=threshold,
        exact_equalities=equalities,
        carrier_radius=carrier_error,
        units=dict(fourier="C-scaled counts", spatial_l2="C-scaled counts, vector L2 norm"),
    )


def regression_errors(
    build: dict[str, Any],
    errors: dict[str, Any],
    event: dict[str, Any],
    pitch: float,
    carrier_error: float,
) -> dict[str, Any]:
    _, z, y, x = build["spatial"].shape
    n = x * y * z
    xx, yy = np.meshgrid((np.arange(x) - x // 2) * pitch, (np.arange(y) - y // 2) * pitch)
    radius = np.hypot(xx, yy)
    order = event["orders"][1] - event["orders"][0]
    vector = event["carrier_cyc_um"]
    arg = 2 * np.pi * order * (vector[0] * xx + vector[1] * yy)
    eramp = 2 * np.pi * order * radius * carrier_error + SHORT * (1 + abs(arg))
    el = float(errors["spatial_l2"][0])
    eh = float(errors["spatial_l2"][1])
    lower, higher = build["spatial"]
    eh = (
        (1 + float(np.max(eramp))) * eh
        + float(np.linalg.norm((abs(higher) * eramp[None]).ravel()))
        + 2 * gamma(8) * float(np.linalg.norm(higher.ravel()))
    )
    ell, h = math.sqrt(event["SX"]), math.sqrt(event["SY"])
    ex = (2 * ell + el) * el + 2 * gamma(16 * n) * (ell + el) ** 2
    ey = (2 * h + eh) * eh + 2 * gamma(16 * n) * (h + eh) ** 2
    lower_x = (ell - el) ** 2 - 2 * gamma(16 * n) * (ell + el) ** 2 if ell > el else -1.0
    lower_y = (h - eh) ** 2 - 2 * gamma(16 * n) * (h + eh) ** 2 if h > eh else -1.0
    assert lower_x > 0 and lower_y > 0, "independent overlap energy lower bound unavailable"
    cross = ell * eh + h * el + el * eh + 2 * gamma(32 * n) * (ell + el) * (h + eh)
    forward = (cross + abs(event["forward"]) * ex) / lower_x + SHORT * abs(event["forward"])
    reverse = (cross + abs(event["reverse"]) * ey) / lower_y + SHORT * abs(event["reverse"])
    gap = event["SX"] - event["SY"]
    egap = ex + ey
    assert abs(gap) > egap, "independent unequal-energy margin unresolved"
    cabs = abs(event["cross"])
    if gap > 0:
        den = gap + math.hypot(gap, 2 * cabs)
        ed = egap + math.hypot(egap, 2 * cross)
        assert den > ed
        combined = (2 * cross + abs(event["combined"]) * ed) / (den - ed) + SHORT * abs(
            event["combined"]
        )
    else:
        assert cabs > cross, "negative-gap combined phase unresolved"
        en = egap + math.hypot(egap, 2 * cross)
        combined = (en + 2 * abs(event["combined"]) * cross) / (2 * (cabs - cross)) + SHORT * abs(
            event["combined"]
        )
    norm = ell * h
    norm_low = math.sqrt(lower_x * lower_y)
    norm_high = math.sqrt((event["SX"] + ex) * (event["SY"] + ey))
    enorm = max(norm_high - norm, norm - norm_low)
    correlation = (cross + abs(event["correlation"]) * enorm) / norm_low + SHORT * abs(
        event["correlation"]
    )
    objective = (2 * abs(event["forward"]) + forward) * forward + 2 * gamma(8) * (
        abs(event["forward"]) + forward
    ) ** 2
    return dict(
        forward=forward,
        reverse=reverse,
        combined=combined,
        correlation=correlation,
        SX=ex,
        SY=ey,
        cross=cross,
        SX_lower=lower_x,
        SY_lower=lower_y,
        gap_lower=abs(gap) - egap,
        objective=objective,
        spatial_l2=(el, eh),
        carrier_radius=carrier_error,
    )


@dataclass
class _Ball:
    """Scalar absolute-error algebra, retaining explicit physical units at callers."""

    value: float
    error: float

    def plus(self, other: _Ball, sign: int = 1) -> _Ball:
        return _Ball(
            self.value + sign * other.value,
            self.error + other.error + 2 * gamma(4) * (abs(self.value) + abs(other.value)),
        )

    def multiply(self, other: _Ball) -> _Ball:
        value = self.value * other.value
        return _Ball(
            value,
            abs(self.value) * other.error
            + abs(other.value) * self.error
            + self.error * other.error
            + 2 * gamma(4) * abs(value),
        )

    def divide(self, other: _Ball) -> _Ball:
        assert abs(other.value) > other.error, "independent parabola denominator unresolved"
        value = self.value / other.value
        return _Ball(
            value,
            (self.error + abs(value) * other.error) / (abs(other.value) - other.error)
            + 2 * gamma(4) * abs(value),
        )


def _shared_difference(
    build: dict[str, Any],
    errors: dict[str, Any],
    first: dict[str, Any],
    second: dict[str, Any],
    pitch: float,
    angle_error: float,
    magnitude_error: float,
    event_bounds: dict[int, dict[str, Any]],
) -> float:
    a2, a3 = first["forward"], second["forward"]
    difference = a3 - a2
    low, high = build["spatial"]
    _, y, x = low.shape
    xx, yy = np.meshgrid((np.arange(x) - x // 2) * pitch, (np.arange(y) - y // 2) * pitch)
    rr = np.hypot(xx, yy)
    order = first["orders"][1] - first["orders"][0]
    v2, v3 = first["carrier_cyc_um"], second["carrier_cyc_um"]
    q = np.sum(low.conj() * high, axis=0)
    ell, h = float(np.linalg.norm(low.ravel())), float(np.linalg.norm(high.ravel()))
    el, eh = errors["spatial_l2"]
    p = ell * eh + h * el + el * eh
    sx = (2 * ell + el) * el
    n = low.size
    slo = (ell - el) ** 2 - 2 * gamma(16 * n) * (ell + el) ** 2
    assert slo > 0
    dv = (
        magnitude_error
        + (max(abs(first["magnitude_cyc_um"]), abs(second["magnitude_cyc_um"])) + magnitude_error)
        * angle_error
    )
    arg2 = 2 * np.pi * order * (v2[0] * xx + v2[1] * yy)
    er2 = 2 * np.pi * order * rr * dv + SHORT * (1 + abs(arg2))
    if first["stage"] == "angle":
        step = abs(second["angle_rad"] - first["angle_rad"])
        estep = (
            2
            * abs(math.sin(step / 2))
            * (magnitude_error + abs(first["magnitude_cyc_um"]) * angle_error)
        )
    else:
        step = abs(second["magnitude_cyc_um"] - first["magnitude_cyc_um"])
        estep = step * angle_error
    estep += 2 * gamma(128) * (float(np.linalg.norm(v2)) + float(np.linalg.norm(v3)) + step)
    arg_step = 2 * np.pi * order * ((v3[0] - v2[0]) * xx + (v3[1] - v2[1]) * yy)
    dr = abs(np.exp(1j * arg_step) - 1)
    edr = er2 * dr + 2 * np.pi * order * rr * estep + 2 * SHORT
    dround = 2 * gamma(32 * n) * (ell + el) * (h + eh)
    ed = (
        p * float(np.max(dr + edr))
        + float(np.sum(abs(q) * edr))
        + abs(difference) * sx
        + 2 * dround
    ) / slo
    ed += (abs(a2) + abs(a3)) * 2 * gamma(16 * n) + 2 * SHORT
    ea = event_bounds[id(first)]["forward"]
    result = (
        2 * abs(difference) * ea + (2 * abs(a2) + 2 * abs(difference)) * ed + 2 * ea * ed + ed * ed
    )
    result += 4 * gamma(8) * (abs(a2) + abs(a3) + ea + ed) ** 2
    return float(result)


def _coarse_errors(
    case: Case, build: dict[str, Any], error: dict[str, Any], coarse: dict[str, Any]
) -> dict[str, Any]:
    a, _, _ = case.resolved()
    low, high = build["spatial"]
    ell, h = float(np.linalg.norm(low.ravel())), float(np.linalg.norm(high.ravel()))
    el, eh = error["spatial_l2"]
    z, y, x = low.shape
    ec = ell * eh + h * el + el * eh + 2 * gamma(32 * (x + y + z)) * (ell + el) * (h + eh)
    power = coarse["correlation_power"]
    ep = (2 * np.sqrt(power) + ec) * ec + 2 * gamma(8) * (power + ec * ec)
    ix, iy = coarse["integer_peak_xy"]
    others = (power + ep).copy()
    others[iy, ix] = -np.inf
    gap = float(power[iy, ix] - ep[iy, ix] - np.max(others))
    assert gap > 0, "independent coarse peak unresolved"
    components = []
    alias_margins = []
    initial, _ = initial_vectors(case)
    direction = coarse["direction_index"]
    initial_error = _initial_error(case)[direction]
    for axis, extent in ((0, x), (1, y)):
        indices = [((ix + k) % x, iy) if axis == 0 else (ix, (iy + k) % y) for k in (-1, 0, 1)]
        values = np.array([power[j, i] for i, j in indices])
        errors = np.array([ep[j, i] for i, j in indices])
        s = (values[2] - values[0]) / 2
        c = values[2] + values[0] - 2 * values[1]
        es = (errors[2] + errors[0]) / 2
        ed = errors[2] + errors[0] + 2 * errors[1]
        assert abs(c) > ed, "independent coarse curvature unresolved"
        eo = (es + abs(s / c) * ed) / (abs(c) - ed) + SHORT
        fitorder = 1 if a["acquisition_mode"] == "2d" else 2
        components.append(eo / (extent * a["dxy_um"] * fitorder))
        coordinate = (ix if axis == 0 else iy) - s / c
        step = 1 / (extent * a["dxy_um"])
        old = initial[direction, axis] * step
        eold = initial_error * abs(step) + SHORT * abs(old)
        first_margin = abs(old - (coordinate - extent // 2)) - (
            eo + eold + SHORT * (1 + abs(coordinate))
        )
        assert first_margin > 0, "independent first alias comparison unresolved"
        lower = old < coordinate - extent // 2
        if lower:
            coordinate -= extent
        second_margin = abs(old - (coordinate + extent // 2)) - (
            eo + eold + SHORT * (1 + abs(coordinate))
        )
        assert second_margin > 0, "independent second alias comparison unresolved"
        upper = old > coordinate + extent // 2
        assert (lower, upper) == tuple(coarse["alias_decisions"][2 * axis : 2 * axis + 2])
        alias_margins.extend((first_margin, second_margin))
    ek = math.hypot(*components) + SHORT * float(np.linalg.norm(coarse["carrier_cyc_um"]))
    magnitude = float(np.linalg.norm(coarse["carrier_cyc_um"]))
    assert magnitude > ek, "independent coarse polar domain unresolved"
    angle = math.atan2(coarse["carrier_cyc_um"][1], coarse["carrier_cyc_um"][0])
    # The principal-angle branch must be stable, not silently wrapped away.
    if coarse["carrier_cyc_um"][0] < 0:
        assert abs(coarse["carrier_cyc_um"][1]) > components[1], (
            "coarse principal-angle branch unresolved"
        )
    et = math.asin(ek / magnitude) + SHORT * (1 + abs(angle))
    return dict(
        carrier_radius=ek,
        components=np.asarray(components),
        angle_rad=et,
        magnitude_cyc_um=ek,
        peak_margin=gap,
        alias_margins=tuple(alias_margins),
        correlation=ec,
        power=ep,
    )


def _initial_error(case: Case) -> np.ndarray:
    a, c, _ = case.resolved()
    initial, _ = initial_vectors(case)
    result = SHORT * np.linalg.norm(initial, axis=1) * (1 + abs(c["phase_start_angle_rad"]) + np.pi)
    if case.raw.shape[1] == 1 and c["angles_rad"] is None and c["phase_start_angle_rad"] == 0:
        divisor = 1 if a["acquisition_mode"] == "2d" else case.raw.shape[2] // 2
        if divisor in (1, 2, 4):
            # Correctly rounded reciprocal, exact binary scaling and exact
            # sin(0)=0/cos(0)=1 give the same declared binary64 vector.
            result[0] = 0.0
    return result


def parameter_errors(
    case: Case,
    prep: dict[str, Any],
    prep_error: dict[str, Any],
    est: dict[str, Any],
    table_error: np.ndarray,
    *,
    sample_facts: _SampleFacts | None = None,
) -> dict[str, Any]:
    if sample_facts is None:
        sample_facts = _SampleFacts(case.table, table_error)
    a, c, _ = case.resolved()
    t, d, p, z, y, x = case.raw.shape
    o = a["norders"]
    carrier = np.zeros((t, d))
    angle = np.zeros((t, d))
    magnitude = np.zeros((t, d))
    raw = np.zeros((t, d, o - 1))
    final = np.zeros_like(raw)
    known = _initial_error(case)
    builds = {}
    evaluations = {}
    comparisons = []
    parabolas = []
    coarse_reports = []
    decision_bounds = []
    events = est["evaluations"]

    def evaluate(event: dict[str, Any], overlap_error: dict[str, Any], ek: float) -> dict[str, Any]:
        record = regression_errors(
            est["overlaps"][event["overlap_index"]], overlap_error, event, a["dxy_um"], ek
        )
        evaluations[id(event)] = record
        return record

    for it in range(t):
        for di in range(d):
            local_builds = [
                (i, b)
                for i, b in enumerate(est["overlaps"])
                if (b["time_index"], b["direction_index"]) == (it, di)
            ]
            local_events = [
                ev for ev in events if (ev["time_index"], ev["direction_index"]) == (it, di)
            ]
            searched = est["branches"][it][di] == "searched"
            if searched:
                coarse_index, coarse_build = next(
                    (i, b) for i, b in local_builds if b["purpose"] == "coarse"
                )
                ce = overlap_errors(
                    case,
                    prep,
                    prep_error,
                    coarse_build,
                    table_error,
                    known[di],
                    sample_facts=sample_facts,
                )
                builds[coarse_index] = ce
                coarse = next(
                    ev
                    for ev in est["decisions"]
                    if ev["kind"] == "coarse"
                    and (ev["time_index"], ev["direction_index"]) == (it, di)
                )
                co = _coarse_errors(case, coarse_build, ce, coarse)
                coarse_reports.append(dict(time=it, direction=di, **co))
                refine_index, refine = next(
                    (i, b) for i, b in local_builds if b["purpose"] == "refinement"
                )
                re = overlap_errors(
                    case,
                    prep,
                    prep_error,
                    refine,
                    table_error,
                    co["carrier_radius"],
                    sample_facts=sample_facts,
                )
                builds[refine_index] = re
                ea0, em0 = co["angle_rad"], co["magnitude_cyc_um"]
                angle_final = ea0
                magnitude_final = em0
                x1_ref = None
                x1_error = 0.0
                local_decisions = [
                    ev
                    for ev in est["decisions"]
                    if ev["kind"] in ("initial", "shift", "parabola")
                    and (ev["time_index"], ev["direction_index"]) == (it, di)
                ]
                for stage in ("angle", "magnitude"):
                    stage_events = [ev for ev in local_events if ev["stage"] == stage]
                    et, em = (ea0, em0) if stage == "angle" else (angle_final, em0)
                    coordinate_error = et if stage == "angle" else em
                    for event in stage_events:
                        ek = (
                            em
                            + (abs(event["magnitude_cyc_um"]) + em) * et
                            + SHORT * abs(event["magnitude_cyc_um"])
                        )
                        evaluate(event, re, ek)
                    stage_decisions = [ev for ev in local_decisions if ev["stage"] == stage]
                    point2, point3 = stage_events[:2]
                    position = 2

                    def difference_error(
                        first: dict[str, Any] | None,
                        second: dict[str, Any] | None,
                        *,
                        refine: dict[str, Any] = refine,
                        re: dict[str, Any] = re,
                        et: float = et,
                        em: float = em,
                    ) -> float:
                        if first is None:
                            assert second is not None
                            return evaluations[id(second)]["objective"]
                        if second is None:
                            return evaluations[id(first)]["objective"]
                        if (
                            first["stage"] == second["stage"]
                            and first["overlap_index"] == second["overlap_index"]
                        ):
                            return _shared_difference(
                                refine, re, first, second, a["dxy_um"], et, em, evaluations
                            )
                        return (
                            evaluations[id(first)]["objective"]
                            + evaluations[id(second)]["objective"]
                        )

                    initial = stage_decisions[0]
                    decision_bounds.append(
                        dict(
                            kind="initial",
                            stage=stage,
                            points=(
                                x1_error,
                                0.0 if x1_ref is None else evaluations[id(x1_ref)]["objective"],
                                coordinate_error,
                                evaluations[id(point2)]["objective"],
                                coordinate_error,
                                evaluations[id(point3)]["objective"],
                            ),
                        )
                    )
                    de = difference_error(point2, point3)
                    change = point3["objective"] - point2["objective"]
                    assert abs(change) > de, "independent initial search comparison unresolved"
                    comparisons.append(
                        dict(
                            time=it,
                            direction=di,
                            stage=stage,
                            kind="initial",
                            change=change,
                            error=de,
                            margin=abs(change) - de,
                            decision=initial["strict_improvement"],
                        )
                    )
                    assert (change > 0) == initial["strict_improvement"]
                    if not initial["strict_improvement"]:
                        point2, point3 = point3, point2
                    for decision in stage_decisions[1:]:
                        if decision["kind"] == "shift":
                            x1_ref, x1_error = point2, coordinate_error
                            point2, point3 = point3, stage_events[position]
                            position += 1
                            decision_bounds.append(
                                dict(
                                    kind="shift",
                                    stage=stage,
                                    points=(
                                        x1_error,
                                        evaluations[id(x1_ref)]["objective"],
                                        coordinate_error,
                                        evaluations[id(point2)]["objective"],
                                        coordinate_error,
                                        evaluations[id(point3)]["objective"],
                                    ),
                                )
                            )
                            de = difference_error(point2, point3)
                            change = point3["objective"] - point2["objective"]
                            assert abs(change) > de, "independent search continuation unresolved"
                            assert (change > 0) == decision["strict_improvement"]
                            comparisons.append(
                                dict(
                                    time=it,
                                    direction=di,
                                    stage=stage,
                                    kind="shift",
                                    change=change,
                                    error=de,
                                    margin=abs(change) - de,
                                    decision=decision["strict_improvement"],
                                )
                            )
                        else:
                            assert decision["kind"] == "parabola"
                            x1, y1, x2, y2, x3, y3 = decision["points"]
                            e_u = difference_error(point2, x1_ref)
                            e_v = difference_error(point2, point3)
                            # Relative abscissae cancel the shared uncertain
                            # origin when all three probes belong to this stage.
                            same1 = x1_ref is not None and x1_ref["stage"] == stage
                            spacing_round = 2 * gamma(128) * (1 + abs(x1) + abs(x2) + abs(x3))
                            ed1 = (
                                spacing_round
                                if same1
                                else x1_error + coordinate_error + spacing_round
                            )
                            ed3 = spacing_round
                            if x1 in (x2, x3) or x2 == x3:
                                assert same1 and x1_ref is point2, (
                                    "duplicate-coordinate equality proof unavailable"
                                )
                                vertex_error = 0.0
                            else:
                                d1 = _Ball(x1 - x2, ed1)
                                d3 = _Ball(x3 - x2, ed3)
                                u = _Ball(y1 - y2, e_u)
                                v = _Ball(y3 - y2, e_v)
                                s1 = u.divide(d1)
                                s2 = v.divide(d3)
                                delta = d3.plus(d1, -1).multiply(_Ball(0.5, 0.0))
                                relative = d3.multiply(_Ball(0.5, 0.0)).plus(
                                    s2.multiply(delta).divide(s2.plus(s1, -1)), -1
                                )
                                vertex_error = (
                                    coordinate_error
                                    + relative.error
                                    + SHORT * (1 + abs(decision["result"]))
                                )
                            parabolas.append(
                                dict(
                                    time=it,
                                    direction=di,
                                    stage=stage,
                                    error=vertex_error,
                                    ordinate_difference_errors=(e_u, e_v),
                                    coordinate_errors=(ed1, ed3),
                                    result=decision["result"],
                                )
                            )
                            if stage == "angle":
                                angle_final = vertex_error
                            else:
                                magnitude_final = vertex_error
                    assert position == len(stage_events)
                selected = next(ev for ev in local_events if ev["stage"] == "final")
                m = abs(selected["magnitude_cyc_um"])
                ek = magnitude_final + (m + magnitude_final) * angle_final + SHORT * m
                carrier[it, di], angle[it, di], magnitude[it, di] = ek, angle_final, magnitude_final
                evaluate(selected, re, ek)
                for event in local_events:
                    if event["stage"] == "later-order":
                        index = event["overlap_index"]
                        build = est["overlaps"][index]
                        be = overlap_errors(
                            case,
                            prep,
                            prep_error,
                            build,
                            table_error,
                            ek,
                            sample_facts=sample_facts,
                        )
                        builds[index] = be
                        evaluate(event, be, ek)
            else:
                ek = carrier[0, di] if est["branches"][it][di] == "time0-reused" else known[di]
                carrier[it, di] = ek
                for index, build in local_builds:
                    be = overlap_errors(
                        case, prep, prep_error, build, table_error, ek, sample_facts=sample_facts
                    )
                    builds[index] = be
                for event in local_events:
                    evaluate(event, builds[event["overlap_index"]], ek)
            for event in local_events:
                if event["stage"] in ("final", "later-order", "known"):
                    raw[it, di, event["orders"][1] - 1] = evaluations[id(event)]["forward"]
            values = est["raw_modulation"][it, di].copy()
            errors = raw[it, di].copy()
            if a["acquisition_mode"] == "2d":
                for j in range(1, o - 1):
                    errors[j] = (
                        abs(values[j]) * errors[j - 1]
                        + abs(values[j - 1]) * errors[j]
                        + errors[j] * errors[j - 1]
                        + SHORT * abs(values[j] * values[j - 1])
                    )
                    values[j] *= values[j - 1]
            if c["amplitude_floors"] is not None:
                for j, floor in enumerate(c["amplitude_floors"]):
                    size = abs(values[j])
                    assert abs(size - floor) > errors[j], (
                        "independent amplitude-floor decision unresolved"
                    )
                    if size < floor:
                        assert size > errors[j], "independent positive-floor phase unresolved"
                        errors[j] = 2 * floor * errors[j] / (size - errors[j]) + SHORT * floor
                        values[j] *= floor / size
            if not c["fit_all_phases"]:
                assert abs(values[0]) > errors[0], "independent base phase unresolved"
                ephase = math.asin(errors[0] / abs(values[0])) + SHORT
                for j in range(1, o - 1):
                    errors[j] += (abs(values[j]) + errors[j]) * (j + 1) * ephase + SHORT * abs(
                        values[j]
                    )
            final[it, di] = errors
    return dict(
        carrier_radius=carrier,
        angle_rad=angle,
        magnitude_cyc_um=magnitude,
        raw_modulation=raw,
        modulation=final,
        overlaps=[builds[i] for i in range(len(est["overlaps"]))],
        evaluations=[evaluations[id(event)] for event in events],
        comparisons=comparisons,
        parabolas=parabolas,
        coarse=coarse_reports,
        decision_bounds=decision_bounds,
        units=dict(
            carrier_radius="cycles/um",
            angle_rad="rad",
            magnitude_cyc_um="cycles/um",
            raw_modulation="dimensionless",
        ),
    )


def _weight_error(
    case: Case,
    prep: dict[str, Any],
    ev: np.ndarray,
    it: int,
    di: int,
    m: int,
    radius: float,
    er: float,
    iz: int,
    cutoff: np.ndarray,
    support: float,
    spacing: float,
) -> tuple[float, float]:
    _, _, f = case.resolved()
    variance = prep["noise_variance_factors"][it, di, m]
    error = float(ev[it, di, m])
    assert variance > error, "independent variance lower bound unavailable"
    base = 1 / variance
    eb = error / (variance * (variance - error)) + SHORT / (variance - error)
    sr = f["suppression_radius_bins"] * spacing
    suppress = False
    if f["suppress_singularities"]:
        if radius == sr and er == 0:
            within = True
        else:
            assert abs(radius - sr) > er + SHORT * (abs(radius) + abs(sr)), (
                "unresolved suppression selector"
            )
            within = radius < sr
        suppress = (m != 0 or (not f["dampen_order0"] and not f["omit_order0"])) and within
    if suppress:
        factor = (radius * radius + 0.2) / (radius * radius + 1000.2)
        lo = max(0.0, radius - er)
        hi = radius + er
        ef = max(
            (hi * hi + 0.2) / (hi * hi + 1000.2) - factor,
            factor - (lo * lo + 0.2) / (lo * lo + 1000.2),
        ) + SHORT * abs(factor)
    elif m == 0 and f["dampen_order0"]:
        assert cutoff[0] > 0
        factor = (radius / support) ** 2 + abs(iz / cutoff[0]) ** 3
        ef = (2 * radius + er) * er / support**2 + SHORT * abs(factor)
    elif m == 0 and f["omit_order0"]:
        return 0.0, 0.0
    else:
        factor, ef = 1.0, 0.0
    if m == 0 and iz == 0 and f["omit_kz0"]:
        return 0.0, 0.0
    value = base * factor
    return value, (abs(factor) + ef) * eb + base * ef + SHORT * abs(value)


def _power_error(h: float, a: float, g: float, eh: float, ea: float, eg: float) -> float:
    error = (
        (2 * h + eh) * eh * (a + ea) ** 2 * (g + eg)
        + h * h * (2 * a + ea) * ea * (g + eg)
        + h * h * a * a * eg
    )
    return error + SHORT * (h + eh) ** 2 * (a + ea) ** 2 * (g + eg)


def native_errors(
    case: Case,
    prep: dict[str, Any],
    parameters: dict[str, Any],
    nominal: dict[str, Any],
    bands_error: np.ndarray,
    variance_error: np.ndarray,
    modulation_error: np.ndarray,
    carrier_error: np.ndarray,
    table_error: np.ndarray,
    *,
    sample_facts: _SampleFacts | None = None,
) -> dict[str, Any]:
    if sample_facts is None:
        sample_facts = _SampleFacts(case.table, table_error)
    a, _, f = case.resolved()
    t, d, p, z, y, x = case.raw.shape
    o = a["norders"]
    dx, dy = 1 / (x * a["dxy_um"]), 1 / (y * a["dxy_um"])
    dkz = 1 / (z * a["dz_um"]) if a["dz_um"] > 0 else case.table.dkz
    radius = min(
        2 * OPTICS["numerical_aperture"] / (OPTICS["wavelength_nm"] / 1000), 1 / (2 * a["dxy_um"])
    )
    cutoff = nominal["axial_cutoffs_bins"]
    errors = bands_error.copy()
    image_error = np.zeros_like(nominal["image"])
    contribution_upper = np.zeros_like(image_error)
    filter_margin = math.inf
    equalities = 0
    coefficients_by_order = []
    for it in range(t):
        carriers = parameters["carriers_cyc_um"][it]
        amplitudes = np.column_stack((np.ones(d), parameters["modulation"][it]))
        ea = np.column_stack((np.zeros(d), modulation_error[it]))
        apo = radius + np.linalg.norm(carriers[0]) * (o - 1)
        eapo = (o - 1) * carrier_error[it, 0] + SHORT * apo
        w = nominal["effective_wiener"][it]
        ew = 2 * gamma(16) * (abs(f["wiener"]) + (it + 1) * abs(f["wiener_increment"]) / t)
        assert w > ew
        for di in range(d):
            for m in range(o):
                slots = [0] if m == 0 else [2 * m - 1, 2 * m]
                temporary = np.zeros((z, y, x), dtype=complex)
                etemporary = np.zeros((z, y, x))
                for iy in range(-(y // 2 - 1), y // 2 + 1):
                    for ix in range(-(x // 2 - 1), x // 2 + 1):
                        if m == 0 and ix < 0:
                            continue
                        reflected = ix < 0
                        sy = (-iy) % y if reflected else iy % y
                        sx = abs(ix)
                        xy = np.array([ix * dx, iy * dy])
                        r = math.hypot(*xy)
                        inside, margin, eq0 = _radius_decision(xy, radius, 0.0, inclusive=True)
                        if not eq0:
                            filter_margin = min(filter_margin, margin)
                        equalities += int(eq0)
                        for iz in range(-int(cutoff[m]), int(cutoff[m]) + 1):
                            if not inside:
                                errors[it, di, slots, iz % z, sy, sx] = 0
                                continue
                            h, eh = _sample_error(
                                case.table, m, xy, iz, dkz, table_error, 0.0, facts=sample_facts
                            )
                            g, eg = _weight_error(
                                case,
                                prep,
                                variance_error,
                                it,
                                di,
                                m,
                                r,
                                0.0,
                                iz,
                                cutoff,
                                radius,
                                min(dx, dy),
                            )
                            amp = abs(amplitudes[di, m])
                            eamp = ea[di, m]
                            den = abs(h) ** 2 * amp**2 * g
                            eden = _power_error(abs(h), amp, g, eh, eamp, eg)
                            object_xy = xy + m * carriers[di]
                            for other in range(d):
                                for signed in range(-(o - 1), o):
                                    if (other, signed) == (di, m):
                                        continue
                                    if not f["filter_overlaps"] and not (m == 0 and signed == 0):
                                        continue
                                    query = object_xy - signed * carriers[other]
                                    eqxy = (
                                        m * carrier_error[it, di]
                                        + abs(signed) * carrier_error[it, other]
                                    )
                                    # Identical carrier terms cancel exactly.
                                    if other == di:
                                        eqxy = abs(m - signed) * carrier_error[it, di]
                                    included, margin, eq0 = _radius_decision(
                                        query, radius, float(eqxy), inclusive=False
                                    )
                                    if not eq0:
                                        filter_margin = min(filter_margin, margin)
                                    equalities += int(eq0)
                                    if not included:
                                        continue
                                    hh, eeh = _sample_error(
                                        case.table,
                                        abs(signed),
                                        query,
                                        iz,
                                        dkz,
                                        table_error,
                                        float(eqxy),
                                        facts=sample_facts,
                                    )
                                    rr = math.hypot(*query)
                                    gg, eeg = _weight_error(
                                        case,
                                        prep,
                                        variance_error,
                                        it,
                                        other,
                                        abs(signed),
                                        rr,
                                        float(eqxy),
                                        iz,
                                        cutoff,
                                        radius,
                                        min(dx, dy),
                                    )
                                    aa = abs(amplitudes[other, abs(signed)])
                                    eaa = ea[other, abs(signed)]
                                    term = abs(hh) ** 2 * aa**2 * gg
                                    den += term
                                    eden += _power_error(
                                        abs(hh), aa, gg, eeh, eaa, eeg
                                    ) + 2 * gamma(8) * abs(den)
                            den += w * w
                            eden += (2 * w + ew) * ew + 2 * gamma(8) * abs(den)
                            lower = max((w - ew) ** 2, den - eden)
                            numerator = g * h.conjugate() * amplitudes[di, m].conjugate()
                            en = (
                                eh * (amp + eamp) * (g + eg)
                                + abs(h) * eamp * (g + eg)
                                + abs(h) * amp * eg
                            )
                            en += SHORT * (abs(h) + eh) * (amp + eamp) * (g + eg)
                            quotient = numerator / den
                            es = (en + abs(quotient) * eden) / lower + SHORT * abs(quotient)
                            taper, et = 1.0, 0.0
                            if f["output_taper"] != "none":
                                rabs = float(np.linalg.norm(object_xy))
                                erabs = m * carrier_error[it, di] + SHORT * rabs
                                assert apo > eapo
                                ratio = rabs / apo
                                eratio = (erabs + abs(ratio) * eapo) / (apo - eapo) + SHORT * abs(
                                    ratio
                                )
                                rho = (
                                    math.hypot(ratio, abs(iz) / cutoff[1])
                                    if cutoff[1] > 0
                                    else ratio
                                )
                                erho = eratio + SHORT * (1 + abs(rho))
                                rho = min(rho, 1.0)
                                if f["output_taper"] == "cosine":
                                    taper = math.cos(np.pi * rho / 2)
                                    et = np.pi / 2 * erho + SHORT
                                else:
                                    exponent = f["power_taper_exponent"]
                                    base = max(0.0, 1 - rho)
                                    taper = base**exponent
                                    if exponent == 0:
                                        et = 0.0
                                    elif exponent > 0:
                                        if exponent >= 1:
                                            et = exponent * erho + SHORT * abs(taper)
                                        else:
                                            et = erho**exponent + SHORT * abs(taper)
                                    else:
                                        assert base > erho, (
                                            "negative-power taper precision unresolved"
                                        )
                                        et = abs(exponent) * (base - erho) ** (
                                            exponent - 1
                                        ) * erho + SHORT * abs(taper)
                            scale = taper * quotient
                            escale = (
                                (abs(taper) + et) * es
                                + abs(quotient) * et
                                + SHORT * (abs(taper) + et) * (abs(quotient) + es)
                            )
                            sz = -iz % z if reflected else iz % z
                            if m == 0:
                                b = prep["quadratures"][it, di, 0, sz, sy, sx]
                                eb = errors[it, di, 0, sz, sy, sx]
                                errors[it, di, 0, sz, sy, sx] = (
                                    abs(b) * escale
                                    + (abs(scale) + escale) * eb
                                    + SHORT * (abs(b) + eb) * (abs(scale) + escale)
                                )
                            else:
                                e, odd = prep["quadratures"][it, di, slots, sz, sy, sx]
                                if reflected:
                                    e, odd = e.conjugate(), odd.conjugate()
                                b = e + 1j * odd
                                eb = float(np.sum(errors[it, di, slots, sz, sy, sx])) + 2 * gamma(
                                    8
                                ) * (abs(e) + abs(odd))
                                temporary[iz % z, iy % y, ix % x] = b * scale
                                etemporary[iz % z, iy % y, ix % x] = (
                                    abs(b) * escale
                                    + (abs(scale) + escale) * eb
                                    + SHORT * (abs(b) + eb) * (abs(scale) + escale)
                                )
                        for iz in range(int(cutoff[m]) + 1, z - int(cutoff[m])):
                            errors[it, di, slots, iz, sy, sx] = 0
                if m > 0:
                    for iy in range(-(y // 2 - 1), y // 2 + 1):
                        for ix in range(x // 2 + 1):
                            for iz in range(-int(cutoff[m]), int(cutoff[m]) + 1):
                                positive = temporary[iz % z, iy % y, ix]
                                negative = temporary[-iz % z, -iy % y, -ix % x].conjugate()
                                ee = (
                                    etemporary[iz % z, iy % y, ix]
                                    + etemporary[-iz % z, -iy % y, -ix % x]
                                ) / 2
                                ee += 2 * gamma(8) * (abs(positive) + abs(negative)) / 2
                                errors[it, di, 2 * m - 1 : 2 * m + 1, iz % z, iy % y, ix] = ee
                if m == 0 and f["omit_order0"]:
                    continue
                full = full_band(nominal["filtered_quadratures"][it, di], m)
                efull = _full_error(errors[it, di], m)
                if m:
                    efull += 2 * gamma(8) * abs(full)
                sum_error = float(np.sum(efull))
                absolute_sum = float(np.sum(abs(full) + efull))
                zo, yo, xo = nominal["image"].shape[1:]
                dims = (yo, xo) if a["acquisition_mode"] == "2d" else (zo, yo, xo)
                inverse_error = sum_error + 2 * gamma(32 * sum(dims)) * absolute_sum
                phase = 0.0
                if m:
                    max_radius = math.hypot(
                        float(np.max(abs(nominal["x_um"]))), float(np.max(abs(nominal["y_um"])))
                    )
                    phase = (
                        2
                        * np.pi
                        * abs(f["explode_factor"])
                        * m
                        * max_radius
                        * carrier_error[it, di]
                    )
                    phase += SHORT * (
                        1
                        + 2
                        * np.pi
                        * abs(f["explode_factor"])
                        * m
                        * max_radius
                        * float(np.linalg.norm(carriers[di]))
                    )
                multiplier = 1 if m == 0 else 2
                error = multiplier * (
                    inverse_error + (absolute_sum + inverse_error) * phase + SHORT * absolute_sum
                )
                image_error[it] += error
                contribution_upper[it] += multiplier * (absolute_sum + inverse_error)
                coefficients_by_order.append(
                    dict(
                        time=it,
                        direction=di,
                        order=m,
                        coefficient_error_sum=sum_error,
                        coefficient_absolute_sum=absolute_sum,
                        inverse_error=inverse_error,
                        assembly_phase_rad=phase,
                        image_error=error,
                    )
                )
        image_error[it] += 2 * gamma(8 * d * o) * contribution_upper[it]
        if a["acquisition_mode"] == "2d" and image_error.shape[1] > 1:
            image_error[it, 1:] = 0
    return dict(
        filtered=errors,
        image=image_error,
        image_by_time=np.max(image_error, axis=(1, 2, 3)),
        coefficients=coefficients_by_order,
        support_margin=filter_margin,
        exact_equalities=equalities,
    )


def error_budget(case: Case, observation: dict[str, Any]) -> dict[str, Any]:
    """Derive quantity-specific conditional bounds from unchanged raw controls.

    No product value supplies an energy premise, numerical target or fitted
    tolerance. Detailed arrays and finite margins are part of the protocol.
    """
    effective = reinterpret(case)
    cal_error = None
    if case.bead is not None:
        cal_error = calibration_errors(case, observation["calibration"])
        effective = copy.deepcopy(effective)
        effective.table = observation["calibration"]["table"]
        table_error = cal_error["samples"]
    else:
        table_error = np.zeros_like(effective.table.samples, dtype=float)
    prep = observation["preparation"]
    pe = preparation_errors(effective, prep)
    sample_facts = _SampleFacts(effective.table, table_error)
    parameters = parameter_errors(
        effective, prep, pe, observation["parameters"], table_error, sample_facts=sample_facts
    )
    native = native_errors(
        effective,
        prep,
        observation["parameters"],
        observation,
        pe["quadratures"],
        pe["noise_variance_factors"],
        parameters["modulation"],
        parameters["carrier_radius"],
        table_error,
        sample_facts=sample_facts,
    )
    a, _, _ = effective.resolved()
    t, d, p, z, y, x = effective.raw.shape
    coefficients = np.zeros((3, 2))
    for record in pe["cubics"]:
        coefficients = np.maximum(coefficients, record["coefficients"])
    overlap_fourier = max(float(np.max(item["fourier"])) for item in parameters["overlaps"])
    overlap_spatial = max(float(np.max(item["spatial_point"])) for item in parameters["overlaps"])
    fit = max(record["forward"] for record in parameters["evaluations"])
    phase_condition = max(
        float(np.linalg.cond(m))
        for m in prep["separation_matrices"].reshape(-1, 2 * a["norders"] - 1, p)
    )
    cubic_condition = max(
        (float(np.linalg.cond(ev["matrix"])) for ev in prep["events"] if ev["kind"] == "cubic"),
        default=1.0,
    )
    coordinate_error = (
        2 * gamma(8) * max(float(np.max(abs(observation[key]))) for key in ("x_um", "y_um", "z_um"))
    )
    return dict(
        bands=float(np.max(pe["quadratures"])),
        modulation=float(np.max(parameters["modulation"])),
        raw_modulation=float(np.max(parameters["raw_modulation"])),
        image=float(np.max(native["image"])),
        filtered=float(np.max(native["filtered"])),
        fit=fit,
        coordinates=coordinate_error,
        phase_condition=phase_condition,
        cubic_condition=cubic_condition,
        min_energy_gap=min(ev["gap_lower"] for ev in parameters["evaluations"]),
        min_raw_modulation=float(np.min(abs(observation["parameters"]["raw_modulation"]))),
        representation_error=0.0,
        observer_unit_roundoff=U,
        transfer=float(np.max(table_error)),
        overlap_fourier=overlap_fourier,
        overlap_spatial=overlap_spatial,
        drift=max(
            float(np.max(pe[key]))
            for key in ("between_displacements_pixels", "exposure_displacements_pixels")
        ),
        phase=float(np.max(pe["phase_angles_rad"])),
        matrix=float(np.max(pe["separation_matrices"])),
        cubic_coefficients=coefficients,
        separation=float(np.max(pe["separation_matrices"])),
        noise=float(np.max(pe["noise_variance_factors"])),
        frame_sums=float(np.max(pe["frame_sums"])),
        equalization_gains=float(np.max(pe["equalization_gains"])),
        preparation_bounds=pe,
        parameter_bounds=parameters,
        native_bounds=native,
        calibration_bounds=cal_error,
        units=dict(
            bands="C-scaled counts, Fourier coefficient",
            image="declared processed intensity units",
            filtered="C-scaled counts, Fourier coefficient",
            fit="dimensionless forward modulation",
            coordinates="um",
            drift="detector pixels",
            phase="rad",
            noise="dimensionless variance factor",
            cubic_coefficients=("pixels/clock", "pixels/clock^2", "pixels/clock^3"),
        ),
        premises=(
            "binary64 round-to-nearest; exact declared raw values",
            "two-evaluation counted FFT bound on absolute input sums",
            "four-ulp elementary evaluation and explicitly counted argument operations",
            "stated phase-inverse and column-scaled least-squares backward models",
            "correct norm rounding on independently certified equality cells",
            "no claim of an unexamined backend theorem",
        ),
    )


def literal_metadata_cases() -> dict[str, Case]:
    """Additive WF066 examples; the original 56 controls remain unchanged.

    Headers already label the physical stream: effective q,d,p,e in that
    order. Drift is inactive, so clocks remain unchanged and supplied phase
    lists, rather than the inactive header phases, define NEW directions.
    """
    examples = {}
    originals = control_cases()
    for storage in ("direction-major", "z-major"):
        case = copy.deepcopy(originals[f"literal-{storage}"])
        case.name = f"literal-metadata-{storage}"
        case.acquisition.update(
            phase_policy="supplied",
            phases_rad=np.array([[0.0, 0.875, 2.125, 3.5, 5.0], [0.25, 1.5, 2.75, 4.0, 5.5]]),
        )
        case.carrier["angles_rad"] = np.array([0.125, 1.0])
        # F=T*D*Zstack*P*(N+1)=1*2*2*5*2=40, already physical.
        section = np.arange(40, dtype=float)
        case.extras.update(
            header_timestamps=101 + 3 * section + section**2,
            header_timestamp_unit=" physical ticks ",
            header_phases_rad=(section + 1) / 64,
        )
        examples[case.name] = case
    return examples


def coordinate_case(*, mode: str = "3d") -> Case:
    """B1 independent integer labels for every p,z,y,x, including unsigned high bit."""
    case = constant_case(mode=mode)
    _, _, phase, z, y, x = np.indices(case.raw.shape)
    case.raw = np.asarray(40000 + 100 * phase + 20 * z + 4 * y + x, dtype=np.uint16)
    case.name = f"b1-coordinate-{mode}"
    return case


def b1_cases() -> dict[str, Case]:
    """Additive B1 positive witnesses; preserve all original58 declarations."""
    original = control_cases()
    omit = copy.deepcopy(original["empirical-complex-search-camera-phase"])
    omit.name = "b1-omit-kz0-3d"
    omit.carrier["search_carriers"] = False
    omit.filtering["omit_kz0"] = True
    linked = copy.deepcopy(original["within3d-cubic-first-block"])
    linked.name = "b1-linked-distinct-initial-angles"
    linked.carrier["angles_rad"] = np.array([0.125, 0.625, 1.125, 1.625])
    negative = copy.deepcopy(original["ordinary-camera-phase"])
    negative.name = "b1-negative-step-no-angle-override"
    negative.carrier.update(negative_angle_step=True, angles_rad=None)
    header = copy.deepcopy(original["within2d-fitted"])
    header.name = "b1-active-first-off-first-time-phases"
    time, phase, exposure = np.indices((2, 5, 2))
    perturbation = np.array([0.0, 0.0625, -0.03125, 0.09375, -0.0625])
    header.extras["header_phases_rad"] = (
        2 * np.pi * phase / 5
        + perturbation[phase]
        + exposure * (0.25 + phase / 32)
        + time * (0.5 + phase / 64)
    ).ravel()
    cases = {case.name: case for case in (omit, linked, negative, header)}
    for mode in ("3d", "2d"):
        case = coordinate_case(mode=mode)
        cases[case.name] = case
    return cases
