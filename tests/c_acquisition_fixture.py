"""Independent CE06 finite observers; public contracts are the only science source.

Each observer is test-owned. No production internals or retained implementation
are imported. Direct sums are accompanied by closed algebraic controls in tests.
"""

from __future__ import annotations

from copy import copy
from math import asin, ceil, cos, hypot, pi, sin, sqrt
from typing import Any

import numpy as np

U = 2.0**-53
SOURCE6 = (
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)
SOURCE10 = (
    ("mainfile.c", "b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8"),
    SOURCE6[1],
    SOURCE6[2],
    SOURCE6[0],
    SOURCE6[3],
    SOURCE6[4],
    (
        "usr_local/include/sfftw.h",
        "72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138",
    ),
    (
        "usr_local/include/srfftw.h",
        "d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a",
    ),
    SOURCE6[5],
    ("drift_n_phasestep.c", "13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2"),
)
ESTIMATE_KEYS = (
    "wavelength_nm",
    "numerical_aperture",
    "immersion_index",
    "search_carriers",
    "use_time0_carriers",
    "amplitude_floors",
    "fit_all_phases",
    "omit_kz0",
    "dxy_um",
    "dz_um",
    "lateral_zoom",
    "axial_zoom",
    "input_scale",
)
MODE_KEYS = {
    "between-build": "subz first_z centers fourier optical_radial_cutoff unused_axial_cutoff",
    "drift-correlation": (
        "scope moving_index exponent cross_spectrum correlation absolute_correlation "
        "integer_peak_xyz neighbors_xyz offsets_xyz offset_status_xyz wrapped_displacement_xyz"
    ),
    "cubic-fit": (
        "scope sample_timestamps_before sample_timestamps_after evaluation_timestamps_before "
        "evaluation_timestamps_after sample_displacements_xy matrix coefficients evaluated_xy"
    ),
    "exposure-correction": "displacement_xy phase_multiplier",
    "phase-design": "policy phases_rad separation_matrix noise_variance_factors",
    "off-combination": (
        "call_z affected_z order cutoff_integer inside_count outside_count on_noise off_noise "
        "on_signal2_before_clip off_signal2_before_clip both_zero_replaced on_scale off_scale "
        "denominator on_fraction off_fraction quadratures_after"
    ),
    "between-correction": "displacement_xyz phase_multiplier",
    "wiener-step": "previous increment effective",
    "sector-boundaries": "carrier_angles_rad boundary_angles_rad",
    "precise-query": (
        "object_frequency_xy angle_rad next_boundaries selected_direction discriminant limit rho"
    ),
}


def api(name: str) -> Any:
    import simrecon

    assert hasattr(simrecon, name), f"approved public CE06 entry missing: {name}"
    return getattr(simrecon, name)


def gamma(n: int) -> float:
    return n * U / (1 - n * U)


def close(actual: Any, expected: Any, *, work: int, scale: float, condition: float = 1) -> None:
    # 512 accounts for two observed FFT/observer chains, complex products,
    # transcendental evaluations and error propagation. Each caller supplies
    # its actual finite reduction extent and an independent absolute sum scale.
    bound = 512 * gamma(64 * work) * max(scale, np.finfo(float).tiny) * condition
    np.testing.assert_allclose(actual, expected, rtol=0, atol=bound)


def lift(n: int) -> Any:
    return np.array([j if j <= n // 2 else j - n for j in range(n)])


def transform(value: Any, *, inverse: bool = False, axes: tuple[int, ...] | None = None) -> Any:
    result = np.asarray(value, dtype=np.complex128)
    if axes is None:
        axes = tuple(range(result.ndim))
    for axis in axes:
        n = result.shape[axis]
        # Finite direct sums; deliberately no FFT or product transform helper.
        matrix = np.exp((2j if inverse else -2j) * pi * np.outer(np.arange(n), np.arange(n)) / n)
        result = np.moveaxis(np.tensordot(matrix, result, axes=(1, axis)), 0, axis)
    return result


def full(half: Any, x: int) -> Any:
    z, y, _ = half.shape
    result = np.empty((z, y, x), dtype=np.complex128)
    for h, i, j in np.ndindex(result.shape):
        result[h, i, j] = half[h, i, j] if j <= x // 2 else np.conj(half[-h % z, -i % y, x - j])
    return result


def matrix(phases: Any, orders: int, policy: str) -> tuple[Any, Any]:
    p = len(phases)
    rows = [np.ones(p)]
    for m in range(1, orders):
        rows.extend([np.cos(m * phases), np.sin(m * phases)])
    uniform = np.array(rows)
    if policy == "uniform":
        return uniform, np.ones(orders)
    design = uniform.T.copy() * (2 / p)
    design[:, 0] /= 2
    # Algebraic special-case controls independently check these rows in tests.
    left = np.linalg.lstsq(design, np.eye(p), rcond=None)[0]
    noise = [np.sum(left[0] ** 2) / p]
    noise.extend(np.sum(left[2 * m - 1 : 2 * m + 1] ** 2) / p for m in range(1, orders))
    return left, np.array(noise)


def edge(plane: Any, width: int, *, bead: bool = False) -> Any:
    y, x = plane.shape
    if width < -1:
        return plane.copy()
    if width == -1:
        return (
            plane
            * np.sin(pi * (np.arange(y) + 0.5) / y)[:, None]
            * np.sin(pi * (np.arange(x) + 0.5) / x)
        )
    padded = np.zeros((y, x + 2))
    padded[:, :x] = plane
    for j in range(x):
        delta = (padded[-1, j] - padded[0, j]) / 2
        for k in range(width):
            v = delta * (1 - sin(pi * (k + 0.5) / (2 * width)))
            padded[k, j] += v
            padded[y - 1 - k, j] -= v
    flat = padded.reshape(-1)
    for i in range(y):
        delta = (padded[i, x - 1] - padded[i, 0]) / 2
        for k in range(width):
            v = delta * (1 - sin(pi * (k + 0.5) / (2 * width)))
            flat[i * (x + 2) + k] += v
            flat[i * (x + 2) + (y if bead else x) - 1 - k] -= v
    return padded[:, :x].copy()


def options(**changes: Any) -> dict[str, Any]:
    result = dict(
        acquisition_mode="2d",
        dxy_um=1.0,
        dz_um=0.5,
        norders=2,
        background=0.0,
        lateral_zoom=1.0,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )
    result.update(changes)
    return result


def optics(**changes: Any) -> dict[str, Any]:
    result = dict(wavelength_nm=520, numerical_aperture=0.25, immersion_index=1.0)
    result.update(changes)
    return result


def known_options(**changes: Any) -> dict[str, Any]:
    result = optics() | dict(wiener=0.5, suppress_singularities=False, output_taper="none")
    result.update(changes)
    return result


def transfer(
    orders: int = 2, *, layout: str = "radial", k: int = 1, complex_values: bool = False
) -> Any:
    if layout == "radial":
        samples = np.ones((orders, 32, k), dtype=complex)
        if complex_values:
            for m, r, z in np.ndindex(samples.shape):
                samples[m, r, z] = 1 + m / 4 + r / 64 + 1j * (m / 8 - z / 16)
    else:
        samples = np.ones((orders, k, 32, 32), dtype=complex)
        if complex_values:
            for m, z, y, x in np.ndindex(samples.shape):
                samples[m, z, y, x] = 1 + m / 4 + x / 64 + 1j * (y / 128 - z / 16)
    return api("declare_otf")(samples, layout=layout, dkr_cyc_um=0.125, dkz_cyc_um=2.0)


def raw_pattern(*, t: int = 1, d: int = 1, p: int = 3, z: int = 1, y: int = 10, x: int = 10) -> Any:
    # Integer parameterized observations, not a generated product forward model.
    index = np.indices((t, d, p, z, y, x))
    return (
        11
        + (3 * index[0] + 5 * index[1] + 7 * index[2] + index[3] + 2 * index[4] + index[5] ** 2)
        % 17
    ).astype(float)


def prepare_expected(images: Any, settings: dict[str, Any]) -> dict[str, Any]:
    tcount, dcount, pcount, zcount, y, x = images.shape
    o = settings["norders"]
    q = 2 * o - 1
    alpha = 1 / (x * y * zcount * settings["lateral_zoom"] ** 2 * settings["axial_zoom"] * dcount)
    bg = np.broadcast_to(settings["background"], (y, x)).copy().astype(float)
    slope = np.broadcast_to(settings.get("flatfield_slope", 1), (y, x)).copy().astype(float)
    extra = settings.get("exposure_background", np.zeros(images.shape[:4]))
    off = settings.get("off_exposures")
    n = 0 if off is None else off.shape[4]
    frames = np.zeros(images.shape)
    off_frames = np.zeros(images.shape)
    sums = np.zeros(images.shape[:4])
    osums = np.zeros(images.shape[:4])
    events = []
    carry = 0.0
    for t, d, z, p in np.ndindex(tcount, dcount, zcount, pcount):
        total = np.zeros((y, x))
        for e in range(n + 1):
            if e == n:
                image = images[t, d, p, z].copy()
            else:
                assert off is not None
                image = off[t, d, p, z, e].copy()
            if image[-1, -1] == -1:
                image[-1, -1] = image[-1, -2]
                slope[-1, -1] = 1
                bg[-1, -1] = bg[-1, -2]
                events.append((t, d, z, p, e))
            if e == n:
                carry = float(extra[t, d, p, z])
            corrected = alpha * slope * (image - bg - carry)
            if e < n:
                total += corrected
            else:
                frames[t, d, p, z] = edge(corrected, settings["edge_pixels"])
        off_frames[t, d, p, z] = edge(total, settings["edge_pixels"])
        sums[t, d, p, z] = np.sum(frames[t, d, p, z])
        osums[t, d, p, z] = np.sum(off_frames[t, d, p, z])
    gains = np.ones(sums.shape)
    ogains = np.ones(sums.shape)
    if settings.get("equalize", True):
        for t, d, p, z in np.ndindex(sums.shape):
            anchor = (
                0 if settings.get("equalize_time", False) else t,
                0,
                0,
                0 if settings.get("equalize_z", False) else z,
            )
            gains[t, d, p, z] = sums[anchor] / sums[t, d, p, z]
            if n > 1:
                ogains[t, d, p, z] = osums[anchor] / osums[t, d, p, z]
    frames *= gains[..., None, None]
    off_frames *= ogains[..., None, None]
    out = np.empty((tcount, dcount, q, zcount, y, x // 2 + 1), dtype=complex)
    oout = np.empty_like(out)
    matrices = np.empty((tcount, dcount, zcount, q, pcount))
    phases_out = np.empty((tcount, dcount, zcount, pcount))
    noise = np.empty((tcount, dcount, o))
    policies = []
    for t in range(tcount):
        td = []
        for d in range(dcount):
            phase = 2 * pi * np.arange(pcount) / pcount
            policy = "uniform"
            if settings.get("phases_rad") is not None:
                phase, policy = settings["phases_rad"][d], "supplied"
            if settings.get("phase_steps_rad") is not None:
                phase, policy = np.arange(pcount) * settings["phase_steps_rad"][d], "steps"
            left, nv = matrix(phase, o, policy)
            td.append(tuple(policy for _ in range(zcount)))
            noise[t, d] = nv
            for z in range(zcount):
                matrices[t, d, z], phases_out[t, d, z] = left, phase
                for src, dst in [(frames, out), (off_frames, oout)]:
                    fourier = transform(src[t, d, :, z], axes=(1, 2))[..., : x // 2 + 1]
                    dst[t, d, :, z] = np.tensordot(left, fourier, axes=(1, 0))
                    dst[t, d, :, z, :, -1] = fourier[:q, :, -1]
            if settings["acquisition_mode"] == "3d":
                out[t, d] = transform(out[t, d], axes=(1,))
        policies.append(tuple(td))
    return dict(
        quadratures=out,
        off_quadratures=oout if n else None,
        frame_sums=sums,
        equalization_gains=gains,
        off_frame_sums=osums if n else None,
        off_equalization_gains=ogains if n else None,
        background_after=bg,
        slope_after=slope,
        sentinel_frames=tuple(events),
        separation_matrices=matrices,
        phase_angles_rad=phases_out,
        noise_variance_factors=noise,
        phase_policies=tuple(policies),
        input_scale=alpha,
    )


def sample(table: Any, kx: float, ky: float, z: int, native_dkz: float, order: int) -> complex:
    h = table.samples[order]
    t = z * native_dkz / table.dkz_cyc_um
    conjugate = table.layout == "full" and kx < 0
    if table.layout == "radial":
        u = hypot(kx, ky) / table.dkr_cyc_um
        if t < 0:
            t += h.shape[1]
        i, j = int(np.floor(u)), int(np.floor(t))
        a, b = u - i, t - j
        j1 = 0 if j == h.shape[1] - 1 else j + 1
        values = h.reshape(-1)
        offsets = [
            i * h.shape[1] + j,
            i * h.shape[1] + j1,
            (i + 1) * h.shape[1] + j,
            (i + 1) * h.shape[1] + j1,
        ]
        assert all(0 <= ix < len(values) for ix in offsets), "independent unsafe radial stencil"
        v = values[offsets]
        return complex((1 - a) * ((1 - b) * v[0] + b * v[1]) + a * ((1 - b) * v[2] + b * v[3]))
    u, v = kx / table.dkr_cyc_um, ky / table.dkr_cyc_um
    if conjugate:
        u, v, t = -u, -v, -t
    k, y, x = h.shape
    if v < 0:
        v += y
    if t < 0:
        t += k
    ix, iy, iz = int(np.floor(u)), int(np.floor(v)), int(np.floor(t))
    weights = (u - ix, v - iy, t - iz)
    result = 0j
    flat = h.reshape(-1)
    for ax, ay, az in np.ndindex(2, 2, 2):
        offset = (
            ((iz if az == 0 else (iz + 1) % k) * y + (iy if ay == 0 else (iy + 1) % y)) * x
            + ix
            + ax
        )
        assert 0 <= offset < len(flat), "independent unsafe full stencil"
        w = np.prod(
            [
                weights[0] if ax else 1 - weights[0],
                weights[1] if ay else 1 - weights[1],
                weights[2] if az else 1 - weights[2],
            ]
        )
        result += flat[offset] * w
    return complex(np.conj(result) if conjugate else result)


def overlaps(
    bands: Any,
    table: Any,
    carrier: Any,
    pair: tuple[int, int],
    t: int = 0,
    d: int = 0,
    *,
    omit: bool = False,
    **op: Any,
) -> dict[str, Any]:
    _, _, _, z, y, x = bands.input_shape
    pitch = bands.dxy_um
    dzf = 1 / (z * bands.dz_um) if bands.dz_um > 0 else table.dkz_cyc_um
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    angle = asin(op["numerical_aperture"] / op["immersion_index"])
    radius = min(2 * op["numerical_aperture"] / (op["wavelength_nm"] / 1000), 1 / (2 * pitch))
    cutoff = ceil((1 - cos(angle)) / le / dzf)
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    fourier = np.zeros((2, z, y, x), dtype=complex)
    written = np.zeros(fourier.shape, dtype=bool)
    a, b = pair
    delta = (b - a) * np.asarray(carrier)
    multiplier = 1 if z == 1 else 5
    native = bands.quadratures[t, d]

    def band(m: int, h: int, i: int, j: int) -> complex:
        value = (
            full(native[0], x)[h % z, i, j]
            if m == 0
            else full(native[2 * m - 1], x)[h % z, i, j] + 1j * full(native[2 * m], x)[h % z, i, j]
        )
        return complex(value)

    # Cache full quadratures, independent all-axis reflection, for finite loops.
    complete = [full(slot, x) for slot in native]

    def read(m: int, h: int, i: int, j: int) -> complex:
        return complex(
            complete[0][h % z, i, j]
            if m == 0
            else complete[2 * m - 1][h % z, i, j] + 1j * complete[2 * m][h % z, i, j]
        )

    for i, j in np.ndindex(y, x):
        qxy = np.array([lift(x)[j] / (x * pitch), lift(y)[i] / (y * pitch)])
        if np.linalg.norm(qxy) > radius:
            continue
        for side in range(2):
            shifted = qxy + (delta if side else -delta)
            if np.linalg.norm(shifted) > radius:
                continue
            for h in range(-cutoff, cutoff + 1):
                if omit and h == 0:
                    continue
                first = b if side else a
                h1 = sample(table, qxy[0], qxy[1], h, dzf, first)
                if (multiplier if side else 1) * abs(h1) <= 0.006:
                    continue
                h2 = sample(table, shifted[0], shifted[1], h, dzf, a if side else b)
                if (1 if side else multiplier) * abs(h2) <= 0.006:
                    continue
                fourier[side, h % z, i, j] = (
                    read(first, h, i, j) * h2 / sqrt(abs(h1) ** 2 + abs(h2) ** 2)
                )
                written[side, h % z, i, j] = True
    return dict(
        fourier=fourier, spatial=transform(fourier, inverse=True, axes=(1, 2, 3)), written=written
    )


def regression(spatial: Any, carrier: Any, pair: tuple[int, int], pitch: float) -> dict[str, Any]:
    _, _, y, x = spatial.shape
    xx, yy = np.meshgrid((np.arange(x) - x // 2) * pitch, (np.arange(y) - y // 2) * pitch)
    left = spatial[0]
    right = spatial[1] * np.exp(2j * pi * (pair[1] - pair[0]) * (xx * carrier[0] + yy * carrier[1]))
    sx, sy = float(np.sum(abs(left) ** 2)), float(np.sum(abs(right) ** 2))
    cross = complex(np.sum(np.conj(left) * right))
    assert sx > 0 and sy > 0 and sx != sy, "independent regression outside finite domain"
    beta = 0.5 * np.arctan(2 * abs(cross) / (sx - sy))
    if beta < 0:
        beta += pi / 2
    combined = 0j if cross == 0 else complex(np.tan(beta) * cross / abs(cross))
    return dict(
        SX=sx,
        SY=sy,
        cross=cross,
        forward=cross / sx,
        reverse=np.conj(cross) / sy,
        combined=combined,
        correlation=abs(cross) / sqrt(sx * sy),
    )


def one_time(bands: Any, t: int) -> Any:
    result = copy(bands)
    object.__setattr__(result, "input_shape", (1, *bands.input_shape[1:]))
    for name in (
        "quadratures",
        "noise_variance_factors",
        "frame_sums",
        "equalization_gains",
        "off_frame_sums",
        "off_equalization_gains",
        "off_quadratures",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
        "separation_matrices",
        "phase_angles_rad",
    ):
        value = getattr(bands, name)
        if value is not None:
            object.__setattr__(result, name, value[t : t + 1].copy())
    object.__setattr__(result, "phase_policies", bands.phase_policies[t : t + 1])
    object.__setattr__(
        result, "sentinel_frames", tuple((0, *e[1:]) for e in bands.sentinel_frames if e[0] == t)
    )
    events = []
    for event in bands.trace:
        if event.time_index == t:
            event = copy(event)
            object.__setattr__(event, "time_index", 0)
            events.append(event)
    object.__setattr__(result, "trace", tuple(events))
    if bands.header_timestamps_after is not None:
        n = dict(bands.resolved_settings)["n_off_exposures"]
        f = int(np.prod(bands.input_shape[1:4])) * (n + 1)
        object.__setattr__(
            result, "header_timestamps_after", bands.header_timestamps_after[:f].copy()
        )
    return result


def events(result: Any, kind: str) -> list[dict[str, Any]]:
    trace = (
        result.mode_trace
        if kind in {"wiener-step", "sector-boundaries", "precise-query"}
        else result.trace
    )
    return [dict(e.details) for e in trace if e.kind == kind]


def assert_mode_trace(result: Any) -> None:
    arrays = []
    for event in result.trace:
        assert type(event.kind) is str and type(event.time_index) is int
        assert type(event.direction_index) is int
        assert type(event.z_index) in {int, type(None)} and type(event.phase_index) in {
            int,
            type(None),
        }
        assert type(event.details) is tuple
        assert tuple(k for k, _ in event.details) == tuple(MODE_KEYS[event.kind].split())
        for _, value in event.details:
            if isinstance(value, np.ndarray):
                assert value.dtype in (np.dtype(float), np.dtype(complex), np.dtype(bool))
                assert value.flags.owndata and not value.flags.writeable
                assert np.isfinite(value).all()
                arrays.append(value)
    for i, a in enumerate(arrays):
        assert not any(np.shares_memory(a, b) for b in arrays[i + 1 :])


def reconstruct_expected(
    bands: Any, table: Any, carriers: Any, modulation: Any, **settings: Any
) -> dict[str, Any]:
    tcount, dcount, _, z, y, x = bands.input_shape
    o = modulation.shape[1] + 1
    zoom, a = bands.lateral_zoom, bands.axial_zoom
    xo, yo, zo = int(zoom * x), int(zoom * y), a * z
    dx, dy = 1 / (x * bands.dxy_um), 1 / (y * bands.dxy_um)
    dzf = 1 / (z * bands.dz_um) if bands.dz_um > 0 else table.dkz_cyc_um
    op = optics() | settings
    radius = min(
        2 * op["numerical_aperture"] / (op["wavelength_nm"] / 1000), 1 / (2 * bands.dxy_um)
    )
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    c0 = ceil((1 - cos(asin(op["numerical_aperture"] / op["immersion_index"]))) / le / dzf)
    cut = [c0] + [int((1 + 1 / 0.88) * c0)] * (o - 2) + [int(1.3 * c0)]
    cut = [max(z // 2 - 1, 0) if c >= z // 2 else c for c in cut]
    xlabels = (np.arange(xo) - xo // 2) * bands.dxy_um / zoom
    ylabels = (np.arange(yo) - yo // 2) * bands.dxy_um / zoom
    zlabels = (np.arange(zo) - zo // 2) * bands.dz_um / a
    filtered = bands.quadratures.copy()
    image = np.zeros((tcount, zo, yo, xo))
    effective = []
    w = op["wiener"]
    for t in range(tcount):
        w += op.get("wiener_increment", 0) / tcount
        effective.append(w)
        for d in range(dcount):

            def gain(e: int, m: int, r: float, h: int, time: int = t) -> float:
                nv = bands.noise_variance_factors[time, e, m]
                g = 1 / nv
                sr = op.get("suppression_radius_bins", 10.0) * min(dx, dy)
                if (
                    op.get("suppress_singularities", True)
                    and r <= sr
                    and (
                        m > 0
                        or not (op.get("dampen_order0", False) or op.get("omit_order0", False))
                    )
                ):
                    g /= 1 + 1000 / (r * r + 0.2)
                elif m == 0 and op.get("dampen_order0", False):
                    assert cut[0] > 0
                    g *= (r / radius) ** 2 + abs(h / cut[0]) ** 3
                elif m == 0 and op.get("omit_order0", False):
                    g = 0.0
                if m == 0 and h == 0 and op.get("omit_kz0", False):
                    g = 0.0
                return g

            for m in range(o):
                target = filtered[t, d, 0 if m == 0 else 2 * m - 1 : 1 if m == 0 else 2 * m + 1]
                temporary = np.zeros((z, y, x), dtype=complex)
                for iy in range(-(y // 2 - 1), y // 2 + 1):
                    for ix in range(-(x // 2 - 1), x // 2 + 1):
                        if m == 0 and ix < 0:
                            continue
                        reflected = ix < 0
                        row, col = ((-iy) % y, -ix) if reflected else (iy % y, ix)
                        r = hypot(ix * dx, iy * dy)
                        for h in range(-cut[m], cut[m] + 1):
                            if r > radius:
                                target[:, h % z, row, col] = 0
                                continue
                            stored_z = (-h if reflected else h) % z
                            values = bands.quadratures[t, d, :, stored_z, row, col]
                            if reflected:
                                values = np.conj(values)
                            b = values[0] if m == 0 else values[2 * m - 1] + 1j * values[2 * m]
                            h1 = sample(table, ix * dx, iy * dy, h, dzf, m)
                            am = 1 if m == 0 else modulation[d, m - 1]
                            g = gain(d, m, r, h)
                            denominator = abs(h1) ** 2 * abs(am) ** 2 * g
                            kxy = np.array([ix * dx, iy * dy]) + m * carriers[d]
                            for e in range(dcount):
                                for n in range(-(o - 1), o):
                                    if e == d and n == m:
                                        continue
                                    if not op.get("filter_overlaps", True) and not (
                                        m == 0 and n == 0
                                    ):
                                        continue
                                    qxy = kxy - n * carriers[e]
                                    qr = float(np.linalg.norm(qxy))
                                    if qr < radius:
                                        h2 = sample(table, qxy[0], qxy[1], h, dzf, abs(n))
                                        an = 1 if n == 0 else modulation[e, abs(n) - 1]
                                        denominator += (
                                            abs(h2) ** 2 * abs(an) ** 2 * gain(e, abs(n), qr, h)
                                        )
                            denominator += w * w
                            rho = float(np.linalg.norm(kxy)) / (
                                radius + np.linalg.norm(carriers[0]) * (o - 1)
                            )
                            if cut[1] > 0:
                                rho = sqrt(rho * rho + (abs(h) / cut[1]) ** 2)
                            rho = min(rho, 1.0)
                            taper = 1.0
                            if op.get("output_taper", "cosine") == "cosine":
                                taper = cos(pi * rho / 2)
                            elif op["output_taper"] == "power":
                                taper = (1 - rho) ** op["power_taper_exponent"]
                            value = b * taper * g * np.conj(h1) * np.conj(am) / denominator
                            if m == 0:
                                target[0, stored_z, row, col] = value
                            else:
                                temporary[h % z, iy % y, ix % x] = value
                        target[:, cut[m] + 1 : z - cut[m], row, col] = 0
                if m > 0:
                    for iy in range(-(y // 2 - 1), y // 2 + 1):
                        for ix in range(x // 2 + 1):
                            for h in range(-cut[m], cut[m] + 1):
                                p = temporary[h % z, iy % y, ix]
                                n = np.conj(temporary[-h % z, -iy % y, -ix % x])
                                target[0, h % z, iy % y, ix] = (p + n) / 2
                                target[1, h % z, iy % y, ix] = (p - n) / (2j)
            for m in range(o):
                if m == 0 and op.get("omit_order0", False):
                    continue
                slots = filtered[t, d]
                coefficients = (
                    full(slots[0], x)
                    if m == 0
                    else full(slots[2 * m - 1], x) + 1j * full(slots[2 * m], x)
                )
                # Evaluate native Fourier polynomial at output points directly.
                # This avoids sharing the product's embedding and FFT algorithm.
                ex = np.exp(2j * pi * np.outer(np.arange(xo) / xo, lift(x)))
                ey = np.exp(2j * pi * np.outer(np.arange(yo) / yo, lift(y)))
                if bands.acquisition_mode == "2d":
                    u = np.zeros((zo, yo, xo), dtype=complex)
                    u[0] = ey @ coefficients[0] @ ex.T
                else:
                    ez = np.exp(2j * pi * np.outer(np.arange(zo) / zo, lift(z)))
                    u = np.einsum("hk,iv,jw,kvw->hij", ez, ey, ex, coefficients)
                if m == 0:
                    image[t] += np.real(u)
                else:
                    xx, yy = np.meshgrid(xlabels, ylabels)
                    ramp = np.exp(
                        2j
                        * pi
                        * op.get("explode_factor", 1.0)
                        * m
                        * (carriers[d, 0] * xx + carriers[d, 1] * yy)
                    )
                    image[t] += 2 * (u * ramp).real
    return dict(
        image=image,
        filtered_quadratures=filtered,
        x_um=xlabels,
        y_um=ylabels,
        z_um=zlabels,
        axial_cutoffs_bins=np.array(cut),
        radial_cutoff_cyc_um=radius,
        effective_wiener=tuple(effective),
    )


def peak(correlation: Any) -> dict[str, Any]:
    z, y, x = correlation.shape
    absolute = abs(correlation)
    best = (z // 2, y // 2, x // 2)
    height = 0.0
    for h, i, j in np.ndindex(z, y, x):
        if absolute[h, i, j] > height:
            best, height = (h, i, j), absolute[h, i, j]
    neighbors, offsets, status = [], [], []
    for axis, n in [(2, x), (1, y), (0, z)]:
        coords = list(best)
        values = []
        for delta in [-1, 0, 1]:
            coords[axis] = (best[axis] + delta) % n
            values.append(absolute[tuple(coords)])
        neighbors.append(values)
        slope = (values[2] - values[0]) / 2
        curvature = values[2] + values[0] - 2 * values[1]
        offset = 0.0 if curvature == 0 else -slope / curvature
        reason = "zero-curvature" if curvature == 0 else "fitted"
        if abs(offset) > 1.5:
            offset, reason = 0.0, "outside-range"
        if axis == 0 and z == 1:
            offset, reason = 0.0, "not-fitted"
        offsets.append(offset)
        status.append(reason)
    xyz = np.array(best[::-1], dtype=float) + offsets
    for axis, n in enumerate([x, y, z]):
        if xyz[axis] > n // 2:
            xyz[axis] -= n
    if z == 1:
        xyz[2] = 0
    return dict(
        integer_peak_xyz=best[::-1],
        neighbors_xyz=np.array(neighbors),
        offsets_xyz=np.array(offsets),
        offset_status_xyz=tuple(status),
        wrapped_displacement_xyz=xyz,
    )


def correlate(
    reference: Any, moving: Any, *, exponent: float, pitch: float, rd: float, highpass: float
) -> dict[str, Any]:
    z, y, x = reference.shape
    f0, fd = transform(reference), transform(moving)
    cross = np.zeros((z, y, x // 2 + 1), dtype=complex)
    for h, i, j in np.ndindex(cross.shape):
        radius = hypot(j / (x * pitch), lift(y)[i] / (y * pitch))
        if radius < rd:
            c = np.conj(f0[h, i, j]) * fd[h, i, j]
            if c != 0:
                cross[h, i, j] = c * abs(c) ** (exponent - 1)
                if highpass > 0:
                    cross[h, i, j] *= (1 - np.exp(-((radius / (highpass * rd)) ** 2))) ** 2
    correlation = transform(full(cross, x), inverse=True).real
    return dict(
        cross_spectrum=cross,
        correlation=correlation,
        absolute_correlation=abs(correlation),
        **peak(correlation),
    )


def between_expected(
    images: Any,
    *,
    background: Any = 0.0,
    off: Any = None,
    dz: float = 0.5,
    pitch: float = 1.0,
    highpass: float = 0.0,
    **op: Any,
) -> dict[str, Any]:
    d, p, z, y, x = images.shape
    subz = max(z // 2, 1)
    first = (z - subz) // 2
    centers = np.zeros((d, subz, y, x))
    for direction, h, phase in np.ndindex(d, subz, p):
        on = images[direction, phase, first + h].copy()
        if on[-1, -1] == -1:
            on[-1, -1] = on[-1, -2]
        centers[direction, h] += (on - background) / (p * x * y * z)
        if off is not None:
            plane = off[direction, phase, first + h, 0].copy()
            if plane[-1, -1] == -1:
                plane[-1, -1] = plane[-1, -2]
            centers[direction, h] += (plane - background) / (p * x * y * z)
    for direction, h in np.ndindex(d, subz):
        centers[direction, h] = edge(centers[direction, h], 10)
    rd = 2 * op["numerical_aperture"] / (op["wavelength_nm"] / 1000)
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    cz = min(
        ceil((1 - cos(asin(op["numerical_aperture"] / op["immersion_index"]))) / le * z * dz),
        z // 2,
    )
    correlations = [
        correlate(centers[0], centers[i], exponent=0.25, pitch=pitch, rd=rd, highpass=highpass)
        for i in range(1, d)
    ]
    vectors = np.zeros((d, 3))
    for i, entry in enumerate(correlations, 1):
        vectors[i] = entry["wrapped_displacement_xyz"]
    return dict(
        centers=centers,
        fourier=transform(centers, axes=(1, 2, 3))[..., : x // 2 + 1],
        subz=subz,
        first_z=first,
        optical_radial_cutoff=rd,
        unused_axial_cutoff=cz,
        correlations=correlations,
        vectors=vectors,
    )


def cubic(samples: Any, values: Any, evaluation: Any, *, alias: bool) -> dict[str, Any]:
    tau = samples.copy()
    eta = tau if alias else evaluation.copy()
    tau[1:] -= tau[0]
    design = np.array([[v, v * v, v * v * v] for v in tau[1:]])
    coefficients = np.linalg.lstsq(design, values[1:] - values[0], rcond=None)[0]
    for i in range(len(eta)):
        eta[i] -= tau[0]
    fitted = values[0] + np.array([[v, v * v, v * v * v] for v in eta]) @ coefficients
    return dict(
        sample_timestamps_before=samples,
        sample_timestamps_after=tau,
        evaluation_timestamps_before=samples if alias else evaluation,
        evaluation_timestamps_after=eta,
        sample_displacements_xy=values,
        matrix=design,
        coefficients=coefficients,
        evaluated_xy=fitted,
    )


def correlation_budget(reference: Any, moving: Any, exponent: float) -> float:
    """Propagate two transform bounds through the Holder/derivative split."""
    f0, fd = transform(reference), transform(moving)
    work = sum(reference.shape)
    e0 = 2 * gamma(128 * work) * float(np.sum(abs(reference)))
    ed = 2 * gamma(128 * work) * float(np.sum(abs(moving)))
    total = 0.0
    for a, b in zip(f0.flat, fd.flat, strict=True):
        c = abs(a * b)
        e = abs(a) * ed + abs(b) * e0 + e0 * ed + gamma(16) * c
        if c > e:
            total += e * (c - e) ** (exponent - 1)
        else:
            total += (c + e) ** exponent + c**exponent
    return total + 2 * gamma(128 * work) * float(np.sum(abs(f0 * fd) ** exponent))


def finite_search(
    bands: Any, table: Any, initial: Any, *, t: int = 0, d: int = 0, **op: Any
) -> dict[str, Any]:
    """Literal finite 2D procedure, challenged separately by ordered-state rules."""
    _, _, _, z, y, x = bands.input_shape
    assert z == 1
    coarse = overlaps(bands, table, initial, (0, 1), t, d, **op)
    c = transform(np.sum(coarse["spatial"][0] * np.conj(coarse["spatial"][1]), axis=0))
    power = abs(c) ** 2
    i, j = np.unravel_index(np.argmax(power), power.shape)
    refined = []
    for values in (
        [power[i, (j - 1) % x], power[i, j], power[i, (j + 1) % x]],
        [power[(i - 1) % y, j], power[i, j], power[(i + 1) % y, j]],
    ):
        curvature = values[2] + values[0] - 2 * values[1]
        refined.append(0.0 if curvature == 0 else -(values[2] - values[0]) / (2 * curvature))
    peakxy = np.array([j, i], dtype=float) + refined
    dx, dy = 1 / (x * bands.dxy_um), 1 / (y * bands.dxy_um)
    if initial[0] * dx < peakxy[0] - x // 2:
        peakxy[0] -= x
    if initial[0] * dx > peakxy[0] + x // 2:
        peakxy[0] += x
    if initial[1] * dy < peakxy[1] - y // 2:
        peakxy[1] -= y
    if initial[1] * dy > peakxy[1] + y // 2:
        peakxy[1] += y
    vector = peakxy * np.array([dx, dy])
    assert np.linalg.norm(vector) > 0, "independent coarse zero polar domain"
    mag, angle = float(np.linalg.norm(vector)), float(np.arctan2(vector[1], vector[0]))
    frozen = overlaps(bands, table, vector, (0, 1), t, d, **op)
    trace = []
    x1, amp1 = 0.0, 0.0

    def evaluate(a: float, m: float, stage: str) -> float:
        k = m * np.array([cos(a), sin(a)])
        fit = regression(frozen["spatial"], k, (0, 1), bands.dxy_um)
        objective = abs(fit["forward"]) ** 2
        trace.append(
            dict(kind="evaluation", stage=stage, carrier_cyc_um=k, objective=objective, **fit)
        )
        return objective

    def parabola(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> float:
        if len({x1, x2, x3}) < 3:
            return 0.0
        b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
        s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
        curvature = (s2 - s1) / (b2 - b1)
        return 0.0 if curvature == 0 else b2 - s2 / curvature

    for stage, center, step in [
        ("angle", angle, 0.001),
        ("magnitude", mag, 0.1 / (max(x, y) * bands.dxy_um)),
    ]:

        def objective(
            v: float, magnitude: float = mag, phase: float = angle, selected: str = stage
        ) -> float:
            return (
                evaluate(v, magnitude, selected)
                if selected == "angle"
                else evaluate(phase, v, selected)
            )

        x2, x3 = center, center + step
        amp2, amp3 = objective(x2), objective(x3)
        trace.append(
            dict(
                kind="bracket", stage=stage, branch="initial", values=(x1, amp1, x2, amp2, x3, amp3)
            )
        )
        positive = amp3 > amp2
        candidate = center + step if positive else center
        if not positive:
            x2, x3, amp2, amp3 = x3, x2, amp3, amp2
        trace.append(
            dict(
                kind="bracket",
                stage=stage,
                branch="positive" if positive else "negative-swap",
                values=(x1, amp1, x2, amp2, x3, amp3),
            )
        )
        while amp3 > amp2:
            x1, amp1, x2, amp2 = x2, amp2, x3, amp3
            new = candidate + (step if positive else -step)
            assert new != candidate and np.isfinite(new), "independent stagnant search"
            candidate, x3 = new, new
            amp3 = objective(candidate)
            trace.append(
                dict(
                    kind="bracket",
                    stage=stage,
                    branch="shift",
                    values=(x1, amp1, x2, amp2, x3, amp3),
                )
            )
        trace.append(
            dict(kind="bracket", stage=stage, branch="stop", values=(x1, amp1, x2, amp2, x3, amp3))
        )
        result = parabola(x1, amp1, x2, amp2, x3, amp3)
        trace.append(
            dict(kind="parabola", stage=stage, result=result, values=(x1, amp1, x2, amp2, x3, amp3))
        )
        if stage == "angle":
            angle = result
        else:
            mag = result
    evaluate(angle, mag, "final")
    carrier = mag * np.array([cos(angle), sin(angle)])
    factors = [trace[-1]["forward"]]
    builds = [coarse, frozen]
    o = bands.noise_variance_factors.shape[-1]
    for b in range(2, o):
        build = overlaps(bands, table, carrier, (b - 1, b), t, d, **op)
        factors.append(regression(build["spatial"], carrier, (b - 1, b), bands.dxy_um)["forward"])
        builds.append(build)
    return dict(
        carrier=carrier,
        raw=np.array(factors),
        modulation=np.cumprod(factors),
        coarse_carrier=vector,
        builds=builds,
        trace=trace,
        coarse_power=power,
    )
