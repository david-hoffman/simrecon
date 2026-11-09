"""Independent CE06 finite observers; public contracts are the only science source.

Each observer is test-owned. No production internals or retained implementation
are imported. Direct sums are accompanied by closed algebraic controls in tests.
"""

from __future__ import annotations

from copy import copy
from math import asin, ceil, pi
from math import cos as _plain_cos
from math import hypot as _plain_hypot
from math import sin as _plain_sin
from math import sqrt as _plain_sqrt
from typing import Any

import numpy as np
import pytest

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
    value = getattr(simrecon, name)
    return observe_public(name, value) if callable(value) and not isinstance(value, type) else value


def gamma(n: int) -> float:
    return n * U / (1 - n * U)


def close(actual: Any, expected: Any, *, proof: Any = None) -> None:
    # Freeze the independently propagated case-level certificate before the
    # real public call; prior allowances are retained only in prior evidence.
    certified_close(actual, expected, proof=proof)


def lift(n: int) -> Any:
    return np.array([j if j <= n // 2 else j - n for j in range(n)])


def transform(value: Any, *, inverse: bool = False, axes: tuple[int, ...] | None = None) -> Any:
    result = as_disc(value).astype(np.complex128)
    if axes is None:
        axes = tuple(range(result.ndim))
    for axis in axes:
        n = result.shape[axis]
        # Finite direct sums; deliberately no FFT or product transform helper.
        matrix = np.exp(
            (2j if inverse else -2j) * certified_pi() * np.outer(np.arange(n), np.arange(n)) / n
        )
        conditional_fft = gamma(8 * n) * np.sum(abs(np.asarray(result)), axis=axis, keepdims=True)
        result = np.moveaxis(np.tensordot(matrix, result, axes=(1, axis)), 0, axis)
        result = as_disc(result)
        result.backend += np.broadcast_to(conditional_fft, result.shape)
    return result


def full(half: Any, x: int) -> Any:
    z, y, _ = half.shape
    result = disc_empty((z, y, x), dtype=np.complex128)
    for h, i, j in np.ndindex(result.shape):
        result[h, i, j] = half[h, i, j] if j <= x // 2 else np.conj(half[-h % z, -i % y, x - j])
    return result


def matrix(phases: Any, orders: int, policy: str) -> tuple[Any, Any]:
    phases = as_disc(phases)
    p = len(phases)
    rows = [disc_ones(p)]
    for m in range(1, orders):
        rows.extend([np.cos(m * phases), np.sin(m * phases)])
    uniform = np.stack([as_disc(row) for row in rows])
    if policy == "uniform":
        return uniform, disc_ones(orders)
    design = uniform.T.copy() * (as_disc(2.0) / p)
    design[:, 0] /= 2
    # Algebraic special-case controls independently check these rows in tests.
    left = np.linalg.lstsq(as_disc(design), as_disc(np.eye(p)), rcond=None)[0]
    noise = [np.sum(left[0] ** 2) / p]
    noise.extend(np.sum(left[2 * m - 1 : 2 * m + 1] ** 2) / p for m in range(1, orders))
    return left, np.stack([as_disc(v) for v in noise])


def _ordinary_edge_values(plane: Any) -> bool:
    """Select quiet binary64 arithmetic; other inputs retain the scalar path."""
    if type(plane) is not Disc or plane.dtype != np.dtype(float) or min(plane.shape) == 0:
        return False
    for index, part in enumerate((np.asarray(plane), plane.observer, plane.backend)):
        if (
            type(part) is not np.ndarray
            or part.shape != plane.shape
            or part.dtype != np.dtype(float)
            or not np.all(np.isfinite(part))
            or index > 0
            and np.any(part < 0)
        ):
            return False
        magnitude = abs(part)
        if np.any((magnitude != 0) & ((magnitude < 2.0**-256) | (magnitude > 2.0**256))):
            return False
    return True


def edge(plane: Any, width: int, *, bead: bool = False) -> Any:
    plane = as_disc(plane)
    y, x = plane.shape
    if width < -1:
        return plane.copy()
    if width == -1:
        return (
            plane
            * np.sin(certified_pi() * (np.arange(y) + 0.5) / y)[:, None]
            * np.sin(certified_pi() * (np.arange(x) + 0.5) / x)
        )
    padded = disc_zeros((y, x + 2))
    padded[:, :x] = plane
    ordinary = type(width) is int and _ordinary_edge_values(plane)
    skip_unused = ordinary and width == 0
    reuse_factors = (
        ordinary and type(bead) is bool and 0 < width <= y and width <= (y if bead else x) <= x + 2
    )
    factors: dict[int, Any] = {}

    def factor(k: int) -> Any:
        if reuse_factors:
            if k not in factors:
                factors[k] = 1 - sin(certified_pi() * (k + 0.5) / (2 * width))
            return factors[k]
        return 1 - sin(certified_pi() * (k + 0.5) / (2 * width))

    for j in range(0 if skip_unused else x):
        delta = (padded[-1, j] - padded[0, j]) / 2
        for k in range(width):
            v = delta * factor(k)
            padded[k, j] += v
            padded[y - 1 - k, j] -= v
    flat = padded.reshape(-1)
    for i in range(0 if skip_unused else y):
        delta = (padded[i, x - 1] - padded[i, 0]) / 2
        for k in range(width):
            v = delta * factor(k)
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
    images = as_disc(images)
    tcount, dcount, pcount, zcount, y, x = images.shape
    o = settings["norders"]
    q = 2 * o - 1
    alpha = as_disc(1.0) / (
        x * y * zcount * as_disc(settings["lateral_zoom"]) ** 2 * settings["axial_zoom"] * dcount
    )
    bg = np.broadcast_to(as_disc(settings["background"]), (y, x)).copy().astype(float)
    slope = (
        np.broadcast_to(as_disc(settings.get("flatfield_slope", 1)), (y, x)).copy().astype(float)
    )
    extra = settings.get("exposure_background", disc_zeros(images.shape[:4]))
    off = settings.get("off_exposures")
    off = None if off is None else as_disc(off)
    n = 0 if off is None else off.shape[4]
    frames = disc_zeros(images.shape)
    off_frames = disc_zeros(images.shape)
    sums = disc_zeros(images.shape[:4])
    osums = disc_zeros(images.shape[:4])
    events = []
    backgrounds_before_time: dict[int, Any] = {}
    carry = 0.0
    for t, d, z, p in np.ndindex(tcount, dcount, zcount, pcount):
        if d == z == p == 0:
            backgrounds_before_time[t] = bg.copy()
        total = disc_zeros((y, x))
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
    gains = disc_ones(sums.shape)
    ogains = disc_ones(sums.shape)
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
    out = disc_empty((tcount, dcount, q, zcount, y, x // 2 + 1), dtype=complex)
    oout = np.empty_like(out)
    matrices = disc_empty((tcount, dcount, zcount, q, pcount))
    phases_out = disc_empty((tcount, dcount, zcount, pcount))
    noise = disc_empty((tcount, dcount, o))
    policies = []
    drift = preparation_drift(images, frames, off_frames, backgrounds_before_time, settings)
    for t in range(tcount):
        td = []
        for d in range(dcount):
            phase = 2 * certified_pi() * np.arange(pcount) / pcount
            policy = "uniform"
            linked = settings.get("drift_within", False) and settings.get("adjust_phases", False)
            if linked:
                phase, policy = drift["phases"][t, d, 0], "drift"
            elif settings.get("phases_rad") is not None:
                phase, policy = as_disc(settings["phases_rad"][d]), "supplied"
            if not linked and settings.get("phase_steps_rad") is not None:
                phase, policy = as_disc(np.arange(pcount)) * settings["phase_steps_rad"][d], "steps"
            left, nv = matrix(phase, o, policy)
            td.append(tuple(policy for _ in range(zcount)))
            noise[t, d] = nv
            for z in range(zcount):
                if settings.get("drift_within", False) and settings.get("adjust_phases", False):
                    phase = drift["phases"][t, d, z]
                    policy = "drift"
                    left, nv = matrix(phase, o, policy)
                    noise[t, d] = nv
                matrices[t, d, z], phases_out[t, d, z] = left, phase
                for src, dst in [(frames, out), (off_frames, oout)]:
                    fourier = transform(src[t, d, :, z], axes=(1, 2))[..., : x // 2 + 1]
                    if settings.get("drift_within", False):
                        for phase_index in range(pcount):
                            fourier[phase_index] *= exposure_ramp(
                                drift["exposure_displacements_pixels"][t, d, z, phase_index], y, x
                            )
                    dst[t, d, :, z] = np.tensordot(left, fourier, axes=(1, 0))
                    dst[t, d, :, z, :, -1] = fourier[:q, :, -1]
                combine_expected(out[t, d], oout[t, d], z, settings, drift["off_events"])
            if settings["acquisition_mode"] == "3d":
                out[t, d] = transform(out[t, d], axes=(1,))
            if settings.get("drift_between", False) and d > 0:
                out[t, d] *= between_ramp(drift["between_displacements_pixels"][t, d], zcount, y, x)
            td[-1] = tuple(
                "drift"
                if settings.get("drift_within", False) and settings.get("adjust_phases", False)
                else policy
                for _ in range(zcount)
            )
        policies.append(tuple(td))
    PREPARATION_AUDITS[id(out)] = drift
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
        between_displacements_pixels=drift["between_displacements_pixels"],
        exposure_displacements_pixels=drift["exposure_displacements_pixels"],
        header_timestamps_after=drift["header_timestamps_after"],
    )


def radial_interpolate(values: Any, k: int, i: int, j: int, a: Any, b: Any, j1: int) -> Any:
    """Evaluate the unchanged four-vertex radial expression in its original order."""
    offsets = [i * k + j, i * k + j1, (i + 1) * k + j, (i + 1) * k + j1]
    assert all(0 <= ix < len(values) for ix in offsets), "independent unsafe radial stencil"
    v = values[offsets]
    return (1 - a) * ((1 - b) * v[0] + b * v[1]) + a * ((1 - b) * v[2] + b * v[3])


def sample(table: Any, kx: float, ky: float, z: int, native_dkz: float, order: int) -> complex:
    h = as_disc(table.samples[order])
    t = as_disc(z) * native_dkz / table.dkz_cyc_um
    conjugate = table.layout == "full" and kx < 0
    if table.layout == "radial":
        u = np.hypot(as_disc(kx), as_disc(ky)) / table.dkr_cyc_um
        if t < 0:
            t += h.shape[1]
        i, j = int(np.floor(u)), int(np.floor(t))
        a, b = u - i, t - j
        j1 = 0 if j == h.shape[1] - 1 else j + 1
        values = h.reshape(-1)
        return radial_interpolate(values, h.shape[1], i, j, a, b, j1)
    u, v = as_disc(kx) / table.dkr_cyc_um, as_disc(ky) / table.dkr_cyc_um
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
        w = (
            (weights[0] if ax else 1 - weights[0])
            * (weights[1] if ay else 1 - weights[1])
            * (weights[2] if az else 1 - weights[2])
        )
        result += flat[offset] * w
    return np.conj(result) if conjugate else result


def local_samples(table: Any) -> Any:
    """Reuse identical pure queries for one caller-owned observer invocation.

    The table remains unchanged for this closure's lifetime.
    Coordinate keys include their complete nominal and uncertainty bits, so
    geometrically equal centers with different certificates remain distinct.
    Callers only read the returned scalar discs; no cached object is mutated.
    """
    cache: dict[Any, Any] = {}
    raw_cache: dict[Any, Any] = {}
    orders: dict[int, Any] = {}
    axials: dict[Any, Any] = {}

    def component(value: Any) -> Any:
        parts = (value, getattr(value, "observer", 0.0), getattr(value, "backend", 0.0))
        return tuple(
            (part.dtype.str, part.shape, part.tobytes()) for part in map(np.asarray, parts)
        )

    def query(kx: Any, ky: Any, z: int, native_dkz: Any, order: int) -> Any:
        axial_key = (component(z), component(native_dkz), component(order))
        raw_key = (component(kx), component(ky), axial_key)
        if raw_key in raw_cache:
            return raw_cache[raw_key]
        if table.layout == "radial":
            radial = np.hypot(as_disc(kx), as_disc(ky)) / table.dkr_cyc_um
            key = (component(radial), axial_key)
            if key not in cache:
                if order not in orders:
                    h = as_disc(table.samples[order])
                    orders[order] = (h.shape[1], h.reshape(-1))
                k, values = orders[order]
                if axial_key not in axials:
                    t = as_disc(z) * native_dkz / table.dkz_cyc_um
                    if t < 0:
                        t += k
                    j = int(np.floor(t))
                    axials[axial_key] = (j, t - j, 0 if j == k - 1 else j + 1)
                j, b, j1 = axials[axial_key]
                i = int(np.floor(radial))
                a = radial - i
                cache[key] = radial_interpolate(values, k, i, j, a, b, j1)
        else:
            xy = (component(kx), component(ky))
            key = (xy, axial_key)
            if key not in cache:
                cache[key] = sample(table, kx, ky, z, native_dkz, order)
        raw_cache[raw_key] = cache[key]
        return cache[key]

    # A batch observer may recognize only this unwrapped, table-owned pure
    # sampler. Unknown/custom callables retain their original scalar calls.
    vars(query).update(
        _local_sample_owner=query, _local_sample_table=table, _local_sample_factory=local_samples
    )
    return query


def _lane_pack(values: Any) -> Any:
    """Pack existing scalar bits without performing a new outward rounding."""
    return (
        [np.asarray(value) for value in values],
        np.array(
            [np.asarray(getattr(value, "observer", 0)).item() for value in values], dtype=float
        ),
        np.array(
            [np.asarray(getattr(value, "backend", 0)).item() for value in values], dtype=float
        ),
    )


def _lane_take(value: Any, indices: Any) -> Any:
    """Select independent lanes without adding a scalar indexing operation."""
    return [value[0][i] for i in indices], value[1][indices], value[2][indices]


def _lane_constant(value: Any, count: int) -> Any:
    """Repeat an unchanged scalar operand and its existing certificate bits."""
    return _lane_pack([value] * count)


def _lane_columns(nominal: Any, observer: Any, backend: Any) -> Any:
    """Perform precisely the error-column rounding of one Disc construction."""
    observer = np.array(observer, dtype=float, copy=True)
    backend = np.array(backend, dtype=float, copy=True)
    np.nextafter(observer, np.inf, out=observer, where=observer > 0)
    np.nextafter(backend, np.inf, out=backend, where=backend > 0)
    if not all(np.all(np.isfinite(column)) for column in (observer, backend)):
        raise RuntimeError("native lane finite-arithmetic headroom proof failed")
    return [np.asarray(value) for value in nominal], observer, backend


def _lane_op(operation: Any, *inputs: Any) -> Any:
    """Keep scalar nominal dispatch and batch the unchanged real error algebra."""
    count = len(inputs[0][0])
    if any(len(value[0]) != count for value in inputs):
        raise RuntimeError("native lane lengths disagree")
    # These are original zero-dimensional operands, not NumPy scalar operands.
    raw = [operation(*(value[0][i] for value in inputs)) for i in range(count)]
    magnitude = []
    for item in inputs:
        if (
            item[0]
            and item[0][0].dtype.kind != "c"
            and all(value.dtype == item[0][0].dtype for value in item[0])
        ):
            # Real absolute value only clears the sign bit; retain its dtype.
            magnitude.append(abs(np.array(item[0])))
        else:
            magnitude.append(np.array([abs(value) for value in item[0]]))
    result_magnitude = np.array([abs(value) for value in raw])
    real_gamma, complex_gamma, norm_gamma = gamma(1), gamma(8), gamma(4)
    rounding = np.array(
        [(complex_gamma if value.dtype.kind == "c" else real_gamma) * abs(value) for value in raw]
    )
    if operation is np.hypot:
        rounding = np.array([norm_gamma * abs(value) for value in raw])
    if operation is np.absolute:
        rounding = np.array(
            [
                (norm_gamma if inputs[0][0][i].dtype.kind == "c" else real_gamma) * abs(value)
                for i, value in enumerate(raw)
            ]
        )

    def propagate(errors: Any) -> Any:
        if operation in (np.add, np.subtract):
            return errors[0] + errors[1]
        if operation in (np.conjugate, np.absolute):
            return errors[0]
        if operation is np.multiply:
            return magnitude[0] * errors[1] + magnitude[1] * errors[0] + errors[0] * errors[1]
        if operation is np.square:
            return 2 * magnitude[0] * errors[0] + errors[0] ** 2
        if operation is np.hypot:
            # Keep each original 0D error-hypot evaluation, too: SIMD hypot
            # over an error column need not have identical final bits.
            return np.array(
                [np.hypot(np.asarray(errors[0][i]), np.asarray(errors[1][i])) for i in range(count)]
            )
        raise RuntimeError(f"unimplemented native lane primitive: {operation.__name__}")

    obs = [value[1] for value in inputs]
    total = [value[1] + value[2] for value in inputs]
    propagated = propagate(obs)
    observer = propagated + rounding
    backend = np.maximum(propagate(total) - propagated, 0) + rounding
    # result_magnitude deliberately uses abs of the raw scalar ufunc results;
    # magnitude above uses abs of the original 0D ndarray operands.
    if not np.all(np.isfinite(result_magnitude)):
        raise RuntimeError("native lane nominal finite-arithmetic headroom proof failed")
    return _lane_columns(raw, observer, backend)


def _lane_scalar(value: Any, index: int) -> Any:
    """Restore a scalar's already-rounded bits without rounding them again."""
    result = np.asarray(value[0][index]).copy().view(Disc)
    result.observer = np.array(value[1][index], dtype=float)
    result.backend = np.array(value[2][index], dtype=float)
    return result


def _lane_structural_round(value: Any) -> Any:
    """Reproduce one original stack/index Disc constructor's outward step."""
    return _lane_columns(value[0], value[1], value[2])


def _lane_vector_component(value: Any, component: int, count: int) -> Any:
    """Pack a vector operand component without introducing a new getter rounding."""
    nominal = np.asarray(value)[component]
    result = np.asarray(nominal).copy().view(Disc)
    result.observer = np.array(getattr(value, "observer", np.zeros(2))[component])
    result.backend = np.array(getattr(value, "backend", np.zeros(2))[component])
    return _lane_constant(result, count)


def _lane_norm2(x: Any, y: Any, index: int) -> Any:
    """Use precisely the original two-component norm and its separate columns."""
    value = np.array([x[0][index], y[0][index]])
    result = np.linalg.norm(value)
    observer = np.sum(np.array([x[1][index], y[1][index]]))
    backend = np.sum(np.array([x[2][index], y[2][index]]))
    rounding = gamma(8 * max(value.size, 1)) * abs(result)
    return Disc(result, observer + rounding, backend + rounding)


def _lane_quotient(numerator: Any, denominator: Any, lower: float) -> Any:
    """Evaluate the scalar positive_quotient expression and each divisor record."""
    count = len(numerator[0])
    raw = [numerator[0][i] / denominator[0][i] for i in range(count)]
    magnitude = np.array([abs(value) for value in raw])
    oe = (numerator[1] + magnitude * denominator[1]) / lower
    total = (numerator[1] + numerator[2] + magnitude * (denominator[1] + denominator[2])) / lower
    rounding = gamma(8) * magnitude
    result = _lane_columns(raw, oe + rounding, np.maximum(total - oe, 0) + rounding)
    records = [
        dict(
            kind="filter-divisor",
            lower=lower,
            observer=float(oe[i]),
            conditional_backend=float(total[i] - oe[i] + rounding[i]),
        )
        for i in range(count)
    ]
    return result, records


def _batch_range_limit(terms: int) -> float:
    """Reserve 32 powers and 64 exponent bits for the restricted expression."""
    # Interpolation error has degree <=3; denominator error degree <=9;
    # numerator/quotient error degree <=17 after the positive Wiener lower
    # bound. Degree32 plus64 bits covers constants, sums and outward steps.
    exponent = (np.finfo(float).maxexp - 1 - int(ceil(np.log2(max(terms, 1)))) - 64) // 32
    return float(2.0**exponent)


def _batch_in_range(value: Any, limit: float) -> bool:
    """Decline acceleration outside finite input headroom, retaining fallback."""
    plain = np.asarray(value)
    if plain.dtype.kind not in "biufc" or not np.all(np.isfinite(plain)):
        return False
    if (
        np.any(abs(plain.real) > limit)
        or np.iscomplexobj(plain)
        and np.any(abs(plain.imag) > limit)
    ):
        return False
    return all(
        np.all(np.isfinite(error)) and np.all(error >= 0) and np.all(error <= limit)
        for error in (getattr(value, "observer", 0), getattr(value, "backend", 0))
    )


def _radial_lane_interpolation(params: Any) -> Any:
    """Pack four existing vertices and retain both original getter rounds."""
    a = _lane_op(
        np.subtract,
        _lane_pack([item[0] for item in params]),
        _lane_pack([item[1] for item in params]),
    )
    b = _lane_pack([item[2] for item in params])
    vertices = []
    for vertex in range(4):
        values, observer, backend = [], [], []
        for _, _, _, flat, offsets in params:
            offset = offsets[vertex]
            values.append(np.asarray(flat)[offset])
            observer.append(flat.observer[offset])
            backend.append(flat.backend[offset])
        # values[offsets] and its following scalar getter each performed a
        # separate outward construction in the original radial expression.
        vertices.append(_lane_structural_round(_lane_columns(values, observer, backend)))
    v0, v1, v2, v3 = vertices
    one = _lane_constant(1, len(params))
    first = _lane_op(
        np.add,
        _lane_op(np.multiply, _lane_op(np.subtract, one, b), v0),
        _lane_op(np.multiply, b, v1),
    )
    second = _lane_op(
        np.add,
        _lane_op(np.multiply, _lane_op(np.subtract, one, b), v2),
        _lane_op(np.multiply, b, v3),
    )
    return _lane_op(
        np.add,
        _lane_op(np.multiply, _lane_op(np.subtract, one, a), first),
        _lane_op(np.multiply, a, second),
    )


def _native_radial_batch(
    bands: Any,
    table: Any,
    carriers: Any,
    modulation: Any,
    time: int,
    direction: int,
    order: int,
    dx: Any,
    dy: Any,
    dzf: Any,
    radius: Any,
    w: Any,
) -> Any:
    """Preflight and evaluate one zero-axial native component without side effects."""
    _, directions, _, z, y, x = bands.input_shape
    terms = 3 * directions + 1
    limit = _batch_range_limit(terms)
    if any(
        not _batch_in_range(value, limit)
        for value in (
            bands.quadratures,
            bands.noise_variance_factors,
            table.samples,
            carriers,
            modulation,
            dx,
            dy,
            dzf,
            radius,
            w,
            table.dkr_cyc_um,
            table.dkz_cyc_um,
        )
    ):
        return None
    if any(
        np.asarray(step).shape != () or np.asarray(step).dtype.kind not in "iuf"
        for step in (table.dkr_cyc_um, table.dkz_cyc_um)
    ):
        return None
    margin = float(abs(np.asarray(w))) - float(w.error)
    if margin < 1 / limit or table.dkr_cyc_um <= 0 or table.dkz_cyc_um <= 0:
        return None
    if min(table.dkr_cyc_um, table.dkz_cyc_um) < 1 / limit:
        return None
    lower = margin**2
    noises, amplitudes = {}, {}
    for di in range(directions):
        for m in range(2):
            nv = bands.noise_variance_factors[time, di, m]
            if (
                float(np.asarray(nv)) <= 0
                or float(abs(np.asarray(nv))) - float(nv.error) < 1 / limit
            ):
                return None
            noises[di, m] = 1 / nv
            amplitudes[di, m] = 1 if m == 0 else modulation[di, m - 1]
            if not _batch_in_range(noises[di, m], limit):
                return None
    prepared, sample_cache, raw_cache = {}, {}, {}

    def component(value: Any) -> Any:
        return tuple(
            (part.dtype.str, part.shape, part.tobytes())
            for part in map(
                np.asarray, (value, getattr(value, "observer", 0), getattr(value, "backend", 0))
            )
        )

    def samples(queries: Any) -> Any:
        pending, params, keys, missing = {}, [], [], []
        for kx, ky, m in queries:
            raw_key = (component(kx), component(ky), m)
            keys.append(raw_key)
            if raw_key not in raw_cache and raw_key not in pending:
                pending[raw_key] = len(missing)
                missing.append((kx, ky, m, raw_key))
        if missing:
            radial = _lane_op(
                np.hypot,
                _lane_pack([as_disc(item[0]) for item in missing]),
                _lane_pack([as_disc(item[1]) for item in missing]),
            )
            radial = _overlap_lane_divide(
                radial, _lane_constant(table.dkr_cyc_um, len(missing)), limit
            )
            if radial is None:
                return None
            if not _batch_in_range(np.array(radial[0]), limit) or any(
                np.any(column < 0) or np.any(column > limit) for column in radial[1:]
            ):
                return None
            pending = {}
            for index, (_, _, m, raw_key) in enumerate(missing):
                u = _lane_scalar(radial, index)
                key = (component(u), m)
                raw_cache[raw_key] = key
                if key in sample_cache or key in pending:
                    continue
                if m not in prepared:
                    h = as_disc(table.samples[m])
                    t = as_disc(0) * dzf / table.dkz_cyc_um
                    if t < 0:
                        t += h.shape[1]
                    j = int(np.floor(t))
                    prepared[m] = (
                        h.shape[1],
                        h.reshape(-1),
                        j,
                        t - j,
                        0 if j == h.shape[1] - 1 else j + 1,
                    )
                k, flat, j, b, j1 = prepared[m]
                i = int(np.floor(u))
                offsets = [i * k + j, i * k + j1, (i + 1) * k + j, (i + 1) * k + j1]
                if not all(0 <= ix < len(flat) for ix in offsets):
                    return None
                params.append((u, i, b, flat, offsets))
                pending[key] = len(params) - 1
        if params:
            result = _radial_lane_interpolation(params)
            for key, index in pending.items():
                sample_cache[key] = _lane_scalar(result, index)
        return _lane_pack([sample_cache[raw_cache[key]] for key in keys])

    cells = []
    for iy in range(-(y // 2 - 1), y // 2 + 1):
        for ix in range(-(x // 2 - 1), x // 2 + 1):
            if order == 0 and ix < 0:
                continue
            reflected = ix < 0
            row, col = ((-iy) % y, -ix) if reflected else (iy % y, ix)
            cells.append(dict(iy=iy, ix=ix, row=row, col=col, reflected=reflected))
    for start in range(0, len(cells), 64):
        tile = cells[start : start + 64]
        count = len(tile)
        xv = _lane_op(
            np.multiply, _lane_pack([cell["ix"] for cell in tile]), _lane_constant(dx, count)
        )
        yv = _lane_op(
            np.multiply, _lane_pack([cell["iy"] for cell in tile]), _lane_constant(dy, count)
        )
        rv = _lane_op(np.hypot, xv, yv)
        for index, cell in enumerate(tile):
            cell["r"] = _lane_scalar(rv, index)
            cell["inside"] = not bool(cell["r"] > radius)
        selected = [index for index, cell in enumerate(tile) if cell["inside"]]
        if not selected:
            continue
        active = [tile[index] for index in selected]
        xv, yv = _lane_take(xv, selected), _lane_take(yv, selected)
        count = len(active)
        # np.stack originally adds one outward step to each coordinate.
        native_x, native_y = _lane_structural_round(xv), _lane_structural_round(yv)
        multiple = order * carriers[direction]
        kx = _lane_op(np.add, native_x, _lane_vector_component(multiple, 0, count))
        ky = _lane_op(np.add, native_y, _lane_vector_component(multiple, 1, count))
        for index, cell in enumerate(active):
            iy, ix, row, col, reflected = (
                cell[key] for key in ("iy", "ix", "row", "col", "reflected")
            )
            values = bands.quadratures[time, direction, :, 0, row, col]
            if reflected:
                values = np.conj(values)
            cell["band"] = values[0] if order == 0 else values[1] + 1j * values[2]
            cell["queries"] = [(_lane_scalar(xv, index), _lane_scalar(yv, index), order)]
            cell["included"] = []
        for di in range(directions):
            for signed in range(-1, 2):
                if (di, signed) == (direction, order):
                    continue
                multiple = signed * carriers[di]
                qx = _lane_op(np.subtract, kx, _lane_vector_component(multiple, 0, count))
                qy = _lane_op(np.subtract, ky, _lane_vector_component(multiple, 1, count))
                included = []
                for index in range(count):
                    # The original norm still sees exactly two components,
                    # the same 0D reductions and gamma(16), not a batch size.
                    qr = _lane_norm2(qx, qy, index)
                    if bool(np.asarray(qr) < np.asarray(radius)):
                        included.append(index)
                if not included:
                    continue
                # Each original qxy[component] adds its own outward step.
                query_x = _lane_structural_round(_lane_take(qx, included))
                query_y = _lane_structural_round(_lane_take(qy, included))
                for offset, index in enumerate(included):
                    active[index]["queries"].append(
                        (_lane_scalar(query_x, offset), _lane_scalar(query_y, offset), abs(signed))
                    )
                    active[index]["included"].append((di, signed))
    inside = [cell for cell in cells if cell["inside"]]
    # Tiles bound intermediate arithmetic; cells/records are kept private until
    # the whole component succeeds, so a decline has no certificate/write prefix.
    for start in range(0, len(inside), 16):
        tile = inside[start : start + 16]
        queries = [query for cell in tile for query in cell["queries"]]
        sampled = samples(queries)
        if sampled is None:
            return None
        offsets = np.cumsum([0] + [len(cell["queries"]) for cell in tile[:-1]]).tolist()
        h1 = _lane_take(sampled, offsets)
        count = len(tile)
        am = amplitudes[direction, order]
        g = noises[direction, order]
        denominator = _lane_op(
            np.multiply,
            _lane_op(
                np.multiply,
                _lane_op(np.square, _lane_op(np.absolute, h1)),
                _lane_constant(abs(am) ** 2, count),
            ),
            _lane_constant(g, count),
        )
        positions = [offset + 1 for offset in offsets]
        for di in range(directions):
            for signed in range(-1, 2):
                if (di, signed) == (direction, order):
                    continue
                selected = [
                    i
                    for i, cell in enumerate(tile)
                    if positions[i] < offsets[i] + len(cell["queries"])
                    and cell["included"][positions[i] - offsets[i] - 1] == (di, signed)
                ]
                if not selected:
                    continue
                h2 = _lane_take(sampled, [positions[i] for i in selected])
                term = _lane_op(
                    np.multiply,
                    _lane_op(
                        np.multiply,
                        _lane_op(np.square, _lane_op(np.absolute, h2)),
                        _lane_constant(abs(amplitudes[di, abs(signed)]) ** 2, len(selected)),
                    ),
                    _lane_constant(noises[di, abs(signed)], len(selected)),
                )
                updated = _lane_op(np.add, _lane_take(denominator, selected), term)
                for at, index in enumerate(selected):
                    denominator[0][index] = updated[0][at]
                    denominator[1][index], denominator[2][index] = updated[1][at], updated[2][at]
                    positions[index] += 1
        denominator = _lane_op(np.add, denominator, _lane_constant(w * w, count))
        numerator = _lane_op(
            np.multiply, _lane_pack([cell["band"] for cell in tile]), _lane_constant(1.0, count)
        )
        numerator = _lane_op(np.multiply, numerator, _lane_constant(g, count))
        numerator = _lane_op(np.multiply, numerator, _lane_op(np.conjugate, h1))
        numerator = _lane_op(np.multiply, numerator, _lane_constant(np.conj(am), count))
        result, records = _lane_quotient(numerator, denominator, lower)
        for index, cell in enumerate(tile):
            cell["value"], cell["record"] = _lane_scalar(result, index), records[index]
    return {(cell["iy"], cell["ix"]): cell for cell in cells}


def _overlap_lane_divide(numerator: Any, denominator: Any, limit: float) -> Any:
    """Use ordinary Disc division, with no Wiener-specific lower bound."""
    count = len(numerator[0])
    magnitude = np.array([abs(value) for value in denominator[0]])
    total_denominator = denominator[1] + denominator[2]
    if np.any(magnitude - total_denominator < 1 / limit):
        return None
    raw = [np.true_divide(numerator[0][i], denominator[0][i]) for i in range(count)]
    absolute = np.array([abs(value) for value in raw])

    def propagate(ne: Any, de: Any) -> Any:
        return (ne + absolute * de) / (magnitude - de)

    observer = propagate(numerator[1], denominator[1])
    total = propagate(numerator[1] + numerator[2], total_denominator)
    rounding = np.array(
        [(gamma(8) if value.dtype.kind == "c" else gamma(1)) * abs(value) for value in raw]
    )
    return _lane_columns(raw, observer + rounding, np.maximum(total - observer, 0) + rounding)


def _overlap_lane_sqrt(value: Any) -> Any:
    """Keep each original scalar square-root and error-column expression."""
    if any(bool(item < 0) for item in value[0]):
        return None
    raw = [np.sqrt(item) for item in value[0]]

    def propagate(errors: Any) -> Any:
        result = []
        for nominal, error in zip(value[0], errors, strict=True):
            error = np.asarray(error)
            denominator = np.sqrt(nominal + error) + np.sqrt(np.maximum(nominal - error, 0))
            with np.errstate(divide="ignore", invalid="ignore"):
                result.append(np.where(denominator > 0, 2 * error / denominator, 0))
        return np.array(result)

    observer = propagate(value[1])
    total = propagate(value[1] + value[2])
    rounding = np.array([gamma(1) * abs(item) for item in raw])
    return _lane_columns(raw, observer + rounding, np.maximum(total - observer, 0) + rounding)


def _overlap_threshold(value: Any) -> Any:
    """Prepare the unchanged strict-threshold records without publishing them."""
    difference = _lane_op(np.subtract, value, _lane_constant(as_disc(0.006), len(value[0])))
    records, selected = [], []
    for index, nominal in enumerate(difference[0]):
        gap = float(abs(nominal))
        error = float(difference[1][index] + difference[2][index])
        resolved = gap > error or gap == error == 0
        if not resolved:
            return None
        records.append(
            dict(kind="decision", label="transfer-threshold", gap=gap, error=error, resolved=True)
        )
        if bool(value[0][index] > np.asarray(0.006)):
            selected.append(index)
    return records, selected


def _overlap_radial_samples(table: Any, dzf: Any, limit: float) -> Any:
    """Own exact radial-query reuse and interpolation lanes for one overlap."""
    prepared, axials, cache, raw_cache = {}, {}, {}, {}

    def component(value: Any) -> Any:
        return tuple(
            (part.dtype.str, part.shape, part.tobytes())
            for part in map(
                np.asarray, (value, getattr(value, "observer", 0), getattr(value, "backend", 0))
            )
        )

    def query(queries: Any) -> Any:
        keys, missing, pending, params = [], [], {}, []
        for kx, ky, h, order in queries:
            raw = (component(kx), component(ky), component(h), component(order))
            keys.append(raw)
            if raw not in raw_cache and raw not in pending:
                pending[raw] = len(missing)
                missing.append((kx, ky, h, order, raw))
        if missing:
            radial = _lane_op(
                np.hypot,
                _lane_pack([item[0] for item in missing]),
                _lane_pack([item[1] for item in missing]),
            )
            radial = _overlap_lane_divide(
                radial, _lane_constant(table.dkr_cyc_um, len(missing)), limit
            )
            if radial is None:
                return None
            if not _batch_in_range(np.array(radial[0]), limit) or any(
                np.any(column < 0) or np.any(column > limit) for column in radial[1:]
            ):
                return None
            pending = {}
            for index, (_, _, h, order, raw) in enumerate(missing):
                u = _lane_scalar(radial, index)
                key = (component(u), component(h), component(order))
                raw_cache[raw] = key
                if key in cache or key in pending:
                    continue
                if order not in prepared:
                    values = as_disc(table.samples[order])
                    prepared[order] = (values.shape[1], values.reshape(-1))
                k, flat = prepared[order]
                axial_key = (h, order)
                if axial_key not in axials:
                    t = as_disc(h) * dzf / table.dkz_cyc_um
                    if t < 0:
                        t += k
                    j = int(np.floor(t))
                    axials[axial_key] = (j, t - j, 0 if j == k - 1 else j + 1)
                j, b, j1 = axials[axial_key]
                i = int(np.floor(u))
                offsets = [i * k + j, i * k + j1, (i + 1) * k + j, (i + 1) * k + j1]
                if not all(0 <= offset < len(flat) for offset in offsets):
                    return None
                pending[key] = len(params)
                params.append((u, i, b, flat, offsets))
            if params:
                result = _radial_lane_interpolation(params)
                for key, index in pending.items():
                    cache[key] = _lane_scalar(result, index)
        return _lane_pack([cache[raw_cache[key]] for key in keys])

    return query


def _overlap_radial_batch(
    bands: Any,
    table: Any,
    carrier: Any,
    pair: Any,
    complete: Any,
    cutoff: int,
    radius: Any,
    dzf: Any,
    *,
    omit: bool,
) -> Any:
    """Prepare ordinary overlap visits; decline before any writes/certificates."""
    _, _, _, z, y, x = bands.input_shape
    limit = _batch_range_limit(1)
    if any(
        not _batch_in_range(value, limit)
        for value in (
            bands.quadratures,
            table.samples,
            carrier,
            bands.dxy_um,
            table.dkr_cyc_um,
            table.dkz_cyc_um,
            dzf,
            radius,
        )
    ):
        return None
    if any(
        np.asarray(value).shape != ()
        or np.asarray(value).dtype != np.dtype(float)
        or float(value) < 1 / limit
        for value in (bands.dxy_um, table.dkr_cyc_um, table.dkz_cyc_um)
    ):
        return None
    sample_at = _overlap_radial_samples(table, dzf, limit)
    delta = (pair[1] - pair[0]) * as_disc(carrier)
    multiplier = 1 if z == 1 else 5
    visits = []
    cells = list(np.ndindex(y, x))
    for start in range(0, len(cells), 128):
        tile = cells[start : start + 128]
        count = len(tile)
        qx = _overlap_lane_divide(
            _lane_pack([as_disc(lift(x)[j]) for _, j in tile]),
            _lane_constant(x * bands.dxy_um, count),
            limit,
        )
        qy = _overlap_lane_divide(
            _lane_pack([as_disc(lift(y)[i]) for i, _ in tile]),
            _lane_constant(y * bands.dxy_um, count),
            limit,
        )
        if qx is None or qy is None:
            return None
        qx, qy = _lane_structural_round(qx), _lane_structural_round(qy)
        selected = [
            index for index in range(count) if not bool(_lane_norm2(qx, qy, index) > radius)
        ]
        if not selected:
            continue
        tile = [tile[index] for index in selected]
        qx, qy = _lane_take(qx, selected), _lane_take(qy, selected)
        count = len(tile)
        for side in range(2):
            offset = delta if side else -delta
            sx = _lane_op(np.add, qx, _lane_vector_component(offset, 0, count))
            sy = _lane_op(np.add, qy, _lane_vector_component(offset, 1, count))
            selected = [
                index
                for index in range(count)
                if bool(np.asarray(_lane_norm2(sx, sy, index)) <= np.asarray(radius))
            ]
            if not selected:
                continue
            active = [tile[index] for index in selected]
            # Each original qxy/shifted scalar getter adds one outward step.
            ax = _lane_structural_round(_lane_take(qx, selected))
            ay = _lane_structural_round(_lane_take(qy, selected))
            bx = _lane_structural_round(_lane_take(sx, selected))
            by = _lane_structural_round(_lane_take(sy, selected))
            first, other = (pair[1], pair[0]) if side else pair
            for h in range(-cutoff, cutoff + 1):
                if omit and h == 0:
                    continue
                h1 = sample_at(
                    [
                        (_lane_scalar(ax, i), _lane_scalar(ay, i), h, first)
                        for i in range(len(active))
                    ]
                )
                if h1 is None:
                    return None
                threshold = _overlap_threshold(
                    _lane_op(
                        np.multiply,
                        _lane_constant(multiplier if side else 1, len(active)),
                        _lane_op(np.absolute, h1),
                    )
                )
                if threshold is None:
                    return None
                records, selected_first = threshold
                if len(selected_first) != len(active):
                    return None
                current = []
                for i, (row, col) in enumerate(active):
                    visit = dict(row=row, col=col, side=side, h=h, records=[records[i]])
                    visits.append(visit)
                    current.append(visit)
                if not selected_first:
                    continue
                h2 = sample_at(
                    [(_lane_scalar(bx, i), _lane_scalar(by, i), h, other) for i in selected_first]
                )
                if h2 is None:
                    return None
                threshold = _overlap_threshold(
                    _lane_op(
                        np.multiply,
                        _lane_constant(1 if side else multiplier, len(selected_first)),
                        _lane_op(np.absolute, h2),
                    )
                )
                if threshold is None:
                    return None
                records, selected_second = threshold
                if len(selected_second) != len(selected_first):
                    return None
                for index, original in enumerate(selected_first):
                    current[original]["records"].append(records[index])
                if not selected_second:
                    continue
                selected_h1 = _lane_take(h1, [selected_first[i] for i in selected_second])
                selected_h2 = _lane_take(h2, selected_second)
                denominator = _overlap_lane_sqrt(
                    _lane_op(
                        np.add,
                        _lane_op(np.square, _lane_op(np.absolute, selected_h1)),
                        _lane_op(np.square, _lane_op(np.absolute, selected_h2)),
                    )
                )
                if denominator is None:
                    return None
                band = []
                for index in selected_second:
                    row, col = active[selected_first[index]]
                    band.append(
                        complete[0][h % z, row, col]
                        if first == 0
                        else complete[2 * first - 1][h % z, row, col]
                        + 1j * complete[2 * first][h % z, row, col]
                    )
                numerator = _lane_op(np.multiply, _lane_pack(band), selected_h2)
                value = _overlap_lane_divide(numerator, denominator, limit)
                if value is None:
                    return None
                for index, selected_index in enumerate(selected_second):
                    current[selected_first[selected_index]]["value"] = _lane_scalar(value, index)
    visits.sort(key=lambda visit: (visit["row"], visit["col"], visit["side"], visit["h"]))
    return visits


def overlaps(
    bands: Any,
    table: Any,
    carrier: Any,
    pair: tuple[int, int],
    t: int = 0,
    d: int = 0,
    *,
    omit: bool = False,
    threshold_choices: tuple[bool, ...] | None = None,
    sampler: Any = None,
    **op: Any,
) -> dict[str, Any]:
    _, _, _, z, y, x = bands.input_shape
    pitch = bands.dxy_um
    dzf = (
        as_disc(1.0) / (z * as_disc(bands.dz_um)) if bands.dz_um > 0 else as_disc(table.dkz_cyc_um)
    )
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    angle = asin(op["numerical_aperture"] / op["immersion_index"])
    radius = min(2 * op["numerical_aperture"] / (op["wavelength_nm"] / 1000), 1 / (2 * pitch))
    cutoff = ceil((1 - cos(angle)) / le / dzf)
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    fourier = disc_zeros((2, z, y, x), dtype=complex)
    written = disc_zeros(fourier.shape, dtype=bool)
    a, b = pair
    delta = (b - a) * as_disc(carrier)
    varying = bool(np.any(as_disc(carrier).error > 0))
    multiplier = 1 if z == 1 else 5
    native = bands.quadratures[t, d]
    # Only a dedicated sensitivity proof supplies alternatives. Ordinary
    # callers still require every threshold decision to be certified.
    choices = None if threshold_choices is None else iter(threshold_choices)
    sample_at = local_samples(table) if sampler is None else sampler

    def band(m: int, h: int, i: int, j: int) -> complex:
        value = (
            full(native[0], x)[h % z, i, j]
            if m == 0
            else full(native[2 * m - 1], x)[h % z, i, j] + 1j * full(native[2 * m], x)[h % z, i, j]
        )
        return value

    # Cache full quadratures, independent all-axis reflection, for finite loops.
    complete = [full(slot, x) for slot in native]

    def read(m: int, h: int, i: int, j: int) -> complex:
        return (
            complete[0][h % z, i, j]
            if m == 0
            else complete[2 * m - 1][h % z, i, j] + 1j * complete[2 * m][h % z, i, j]
        )

    batch_eligible = (
        type(pair) is tuple
        and pair == (0, 1)
        and all(type(order) is int for order in pair)
        and z in (1, 2)
        and cutoff in (0, 1)
        and x % 2 == y % 2 == 0
        and table.layout == "radial"
        and not varying
        and threshold_choices is None
        and type(bands.quadratures) is Disc
        and np.asarray(bands.quadratures).dtype == np.dtype(complex)
        and np.asarray(carrier).shape == (2,)
        and np.asarray(carrier).dtype == np.dtype(float)
        and type(carrier) in (np.ndarray, Disc)
        and type(table.samples) in (np.ndarray, Disc)
        and table.samples.ndim == 3
        and table.samples.shape[0] >= 2
        and min(table.samples.shape[1:]) > 0
        and np.asarray(table.samples).dtype == np.dtype(complex)
        and (
            sampler is None
            or getattr(sampler, "_local_sample_owner", None) is sampler
            and getattr(sampler, "_local_sample_table", None) is table
            and getattr(sampler, "_local_sample_factory", None) is local_samples
        )
    )
    batch = (
        _overlap_radial_batch(bands, table, carrier, pair, complete, cutoff, radius, dzf, omit=omit)
        if batch_eligible
        else None
    )
    if batch is not None:
        for visit in batch:
            CERTIFICATES.extend(visit["records"])
            if "value" in visit:
                index = (visit["side"], visit["h"] % z, visit["row"], visit["col"])
                fourier[index] = visit["value"]
                written[index] = True

    for i, j in () if batch is not None else np.ndindex(y, x):
        qxy = np.stack([as_disc(lift(x)[j]) / (x * pitch), as_disc(lift(y)[i]) / (y * pitch)])
        if np.linalg.norm(qxy) > radius:
            continue
        for side in range(2):
            shifted = qxy + (delta if side else -delta)
            if not radial_decision(
                np.linalg.norm(shifted),
                radius,
                inclusive=True,
                varying=varying,
                label="overlap-support",
            ):
                continue
            for h in range(-cutoff, cutoff + 1):
                if omit and h == 0:
                    continue
                first = b if side else a
                h1 = sample_at(qxy[0], qxy[1], h, dzf, first)
                if not threshold_survives((multiplier if side else 1) * abs(h1), choices=choices):
                    continue
                h2 = sample_at(shifted[0], shifted[1], h, dzf, a if side else b)
                if not threshold_survives((1 if side else multiplier) * abs(h2), choices=choices):
                    continue
                fourier[side, h % z, i, j] = (
                    read(first, h, i, j) * h2 / sqrt(abs(h1) ** 2 + abs(h2) ** 2)
                )
                written[side, h % z, i, j] = True
    if choices is not None:
        assert next(choices, None) is None, "unused threshold alternative"
    spatial = closed_zero_overlap(bands, table, carrier, pair, native, written)
    if spatial is None:
        spatial = transform(fourier, inverse=True, axes=(1, 2, 3))
    return dict(fourier=fourier, spatial=spatial, written=written)


def closed_zero_overlap(
    bands: Any, table: Any, carrier: Any, pair: Any, native: Any, written: Any
) -> Any:
    """Return the exact binary64 butterfly for the two-point DC/Nyquist control."""
    if (
        bands.input_shape[-3:] != (1, 1, 2)
        or pair != (0, 1)
        or bands.dxy_um != 1
        or table.layout != "radial"
        or table.dkr_cyc_um != 0.125
        or not np.all(written)
        or np.any(carrier)
        or np.any(as_disc(carrier).error)
        or np.any(as_disc(native).error)
        or np.any(as_disc(table.samples).error)
        or not np.array_equal(np.asarray(native[:3]).reshape(3, 2), [[10, 10], [5, -5], [0, 0]])
        or not np.all(np.asarray(table.samples[0]) == 3)
        or not np.all(np.asarray(table.samples[1]) == 4)
    ):
        return None
    # Both samples are at integer radial cells and axial zero. The constant
    # transfers give sqrt(3**2+4**2)=5; products precede division, so
    # the Fourier rows are (8,8) and (3,-3). Their two-point inverse uses
    # only exact additions/subtractions, leaving disjoint spatial support.
    return as_disc(np.array([[[[16, 0]]], [[[0, 6]]]], dtype=np.complex128))


def regression(spatial: Any, carrier: Any, pair: tuple[int, int], pitch: float) -> dict[str, Any]:
    _, _, y, x = spatial.shape
    if (
        not np.any(carrier)
        and not np.any(as_disc(carrier).error)
        and not np.any(as_disc(spatial).error)
        and np.array_equal(np.asarray(spatial).reshape(2, -1), [[16, 0], [0, 6]])
    ):
        # Centered phase at k=0 is 1. Both pointwise cross terms are exactly
        # zero, while the integer squares give positive unequal energies.
        return {
            key: as_disc(value)
            for key, value in dict(
                SX=256.0,
                SY=36.0,
                cross=0j,
                forward=0j,
                reverse=0j,
                combined=0j,
                correlation=0.0,
            ).items()
        }
    xx, yy = np.meshgrid((np.arange(x) - x // 2) * pitch, (np.arange(y) - y // 2) * pitch)
    left = spatial[0]
    right = spatial[1] * np.exp(
        2j * certified_pi() * (pair[1] - pair[0]) * (xx * carrier[0] + yy * carrier[1])
    )
    sx, sy = np.sum(abs(left) ** 2), np.sum(abs(right) ** 2)
    cross = np.sum(np.conj(left) * right)
    assert sx > 0 and sy > 0 and sx != sy, "independent regression outside finite domain"
    beta = 0.5 * np.arctan(2 * abs(cross) / (sx - sy))
    if beta < 0:
        beta += certified_pi() / 2
    combined = 0j if cross == 0 else np.tan(beta) * cross / abs(cross)
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
    dx, dy = as_disc(1.0) / (x * bands.dxy_um), as_disc(1.0) / (y * bands.dxy_um)
    dzf = (
        as_disc(1.0) / (z * as_disc(bands.dz_um)) if bands.dz_um > 0 else as_disc(table.dkz_cyc_um)
    )
    op = optics() | settings
    radius = min(
        2 * op["numerical_aperture"] / (op["wavelength_nm"] / 1000), 1 / (2 * bands.dxy_um)
    )
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    c0 = ceil((1 - cos(asin(op["numerical_aperture"] / op["immersion_index"]))) / le / dzf)
    cut = [c0] + [int((1 + 1 / 0.88) * c0)] * (o - 2) + [int(1.3 * c0)]
    cut = [max(z // 2 - 1, 0) if c >= z // 2 else c for c in cut]
    xlabels = (as_disc(np.arange(xo)) - xo // 2) * bands.dxy_um / zoom
    ylabels = (as_disc(np.arange(yo)) - yo // 2) * bands.dxy_um / zoom
    zlabels = (as_disc(np.arange(zo)) - zo // 2) * bands.dz_um / a
    filtered = bands.quadratures.copy()
    image = disc_zeros((tcount, zo, yo, xo))
    # These finite-sum matrices and geometric declarations are unchanged by
    # time, direction and order. Reuse their identical certified values locally.
    ex = np.exp(2j * certified_pi() * np.outer(as_disc(np.arange(xo)) / xo, lift(x)))
    ey = np.exp(2j * certified_pi() * np.outer(as_disc(np.arange(yo)) / yo, lift(y)))
    ez = (
        np.exp(2j * certified_pi() * np.outer(as_disc(np.arange(zo)) / zo, lift(z)))
        if bands.acquisition_mode != "2d"
        else None
    )
    carrier_radius = np.linalg.norm(carriers[0])
    carriers_vary = bool(np.any(as_disc(carriers).error > 0))
    batch_eligible = (
        o == 2
        and cut == [0, 0]
        and x % 2 == y % 2 == 0
        and table.layout == "radial"
        and not carriers_vary
        and op.get("output_taper", "cosine") == "none"
        and op.get("filter_overlaps", True)
        and not any(
            op.get(flag, default)
            for flag, default in (
                ("suppress_singularities", True),
                ("dampen_order0", False),
                ("omit_order0", False),
                ("omit_kz0", False),
                ("precise_taper", False),
            )
        )
        # Plain native operands have distinct zero-error dispatch. Preserve
        # their existing scalar expression instead of injecting lane rounds.
        and isinstance(bands.quadratures, Disc)
        and isinstance(bands.noise_variance_factors, Disc)
        and all(
            isinstance(value, np.ndarray)
            for value in (
                bands.quadratures,
                bands.noise_variance_factors,
                table.samples,
                carriers,
                modulation,
            )
        )
        and bands.quadratures.shape == (tcount, dcount, 3, z, y, x // 2 + 1)
        and bands.noise_variance_factors.shape == (tcount, dcount, 2)
        and np.shape(carriers) == (dcount, 2)
        and np.shape(modulation) == (dcount, 1)
        and table.samples.ndim == 3
        and table.samples.shape[0] >= 2
        and min(table.samples.shape[1:]) > 0
        and all(
            np.asarray(value).dtype == dtype and np.asarray(value).flags.c_contiguous
            for value, dtype in (
                (bands.quadratures, np.complex128),
                (bands.noise_variance_factors, np.float64),
                (table.samples, np.complex128),
                (carriers, np.float64),
            )
        )
        and np.asarray(modulation).dtype in (np.dtype(np.float64), np.dtype(np.complex128))
    )
    suppression_radius = op.get("suppression_radius_bins", 10.0) * min(dx, dy)
    sample_at = local_samples(table)
    inverse_noise: dict[Any, Any] = {}
    amplitude_values: dict[Any, Any] = {}
    amplitude_powers: dict[Any, Any] = {}
    amplitude_conjugates: dict[Any, Any] = {}
    carrier_multiples: dict[Any, Any] = {}
    taper_denominator = None

    def amplitude(direction: int, order: int) -> Any:
        key = (direction, order)
        if key not in amplitude_values:
            amplitude_values[key] = 1 if order == 0 else modulation[direction, order - 1]
        return amplitude_values[key]

    def amplitude_power(direction: int, order: int, value: Any) -> Any:
        key = (direction, order)
        if key not in amplitude_powers:
            amplitude_powers[key] = abs(value) ** 2
        return amplitude_powers[key]

    def amplitude_conjugate(direction: int, order: int) -> Any:
        key = (direction, order)
        if key not in amplitude_conjugates:
            amplitude_conjugates[key] = np.conj(amplitude(direction, order))
        return amplitude_conjugates[key]

    def carrier_multiple(direction: int, order: int) -> Any:
        key = (direction, order)
        if key not in carrier_multiples:
            carrier_multiples[key] = order * carriers[direction]
        return carrier_multiples[key]

    effective = []
    w = as_disc(op["wiener"])
    for t in range(tcount):
        w += as_disc(op.get("wiener_increment", 0)) / tcount
        effective.append(w)
        w_squared = None
        w_margin = None
        for d in range(dcount):

            def gain(e: int, m: int, r: float, h: int, time: int = t) -> float:
                noise_key = (time, e, m)
                if noise_key not in inverse_noise:
                    inverse_noise[noise_key] = 1 / bands.noise_variance_factors[time, e, m]
                g = inverse_noise[noise_key]
                if (
                    op.get("suppress_singularities", True)
                    and r <= suppression_radius
                    and (
                        m > 0
                        or not (op.get("dampen_order0", False) or op.get("omit_order0", False))
                    )
                ):
                    g = g / (1 + 1000 / (r * r + 0.2))
                elif m == 0 and op.get("dampen_order0", False):
                    assert cut[0] > 0
                    g = g * ((r / radius) ** 2 + abs(h / cut[0]) ** 3)
                elif m == 0 and op.get("omit_order0", False):
                    g = 0.0
                if m == 0 and h == 0 and op.get("omit_kz0", False):
                    g = 0.0
                return g

            for m in range(o):
                target = filtered[t, d, 0 if m == 0 else 2 * m - 1 : 1 if m == 0 else 2 * m + 1]
                temporary = disc_zeros((z, y, x), dtype=complex)
                batch = (
                    _native_radial_batch(
                        bands, table, carriers, modulation, t, d, m, dx, dy, dzf, radius, w
                    )
                    if batch_eligible
                    else None
                )
                for iy in range(-(y // 2 - 1), y // 2 + 1):
                    for ix in range(-(x // 2 - 1), x // 2 + 1):
                        if m == 0 and ix < 0:
                            continue
                        reflected = ix < 0
                        row, col = ((-iy) % y, -ix) if reflected else (iy % y, ix)
                        r = batch[iy, ix]["r"] if batch is not None else hypot(ix * dx, iy * dy)
                        if batch is not None:
                            cell = batch[iy, ix]
                            if cell["inside"]:
                                CERTIFICATES.append(cell["record"])
                                if m == 0:
                                    target[0, 0, row, col] = cell["value"]
                                else:
                                    temporary[0, iy % y, ix % x] = cell["value"]
                            else:
                                target[:, 0, row, col] = 0
                            target[:, 1:z, row, col] = 0
                            continue
                        for h in range(-cut[m], cut[m] + 1):
                            if r > radius:
                                target[:, h % z, row, col] = 0
                                continue
                            stored_z = (-h if reflected else h) % z
                            values = bands.quadratures[t, d, :, stored_z, row, col]
                            if reflected:
                                values = np.conj(values)
                            b = values[0] if m == 0 else values[2 * m - 1] + 1j * values[2 * m]
                            h1 = sample_at(ix * dx, iy * dy, h, dzf, m)
                            am = amplitude(d, m)
                            g = gain(d, m, r, h)
                            denominator = abs(h1) ** 2 * amplitude_power(d, m, am) * g
                            kxy = np.stack([as_disc(ix * dx), as_disc(iy * dy)]) + carrier_multiple(
                                d, m
                            )
                            for e in range(dcount):
                                for n in range(-(o - 1), o):
                                    if e == d and n == m:
                                        continue
                                    if not op.get("filter_overlaps", True) and not (
                                        m == 0 and n == 0
                                    ):
                                        continue
                                    qxy = kxy - carrier_multiple(e, n)
                                    qr = np.linalg.norm(qxy)
                                    varying = carriers_vary and not (m == 0 and n == 0)
                                    if radial_decision(
                                        qr,
                                        radius,
                                        inclusive=False,
                                        varying=varying,
                                        label="other-order-support",
                                    ):
                                        h2 = sample_at(qxy[0], qxy[1], h, dzf, abs(n))
                                        an = amplitude(e, abs(n))
                                        denominator += (
                                            abs(h2) ** 2
                                            * amplitude_power(e, abs(n), an)
                                            * gain(e, abs(n), qr, h)
                                        )
                            if w_squared is None:
                                w_squared = w * w
                            denominator += w_squared
                            if taper_denominator is None:
                                taper_denominator = radius + carrier_radius * (o - 1)
                            rho = np.linalg.norm(kxy) / taper_denominator
                            if cut[1] > 0:
                                rho = sqrt(rho * rho + (abs(h) / cut[1]) ** 2)
                            rho = np.minimum(rho, 1.0)
                            taper = 1.0
                            if op.get("output_taper", "cosine") == "cosine":
                                taper = cos(certified_pi() * rho / 2)
                            elif op["output_taper"] == "power":
                                taper = (1 - rho) ** op["power_taper_exponent"]
                            numerator = b * taper * g * np.conj(h1) * amplitude_conjugate(d, m)
                            if w_margin is None:
                                w_margin = float(abs(np.asarray(w))) - float(w.error)
                            if w_margin <= 0:
                                raise CertificateError("positive Wiener value is uncertified")
                            lower = w_margin**2
                            value = positive_quotient(numerator, denominator, lower)
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
                if bands.acquisition_mode == "2d":
                    u = disc_zeros((zo, yo, xo), dtype=complex)
                    u[0] = ey @ coefficients[0] @ ex.T
                else:
                    assert ez is not None
                    u = np.tensordot(ez, coefficients, axes=(1, 0))
                    u = np.moveaxis(np.tensordot(ey, u, axes=(1, 1)), 0, 1)
                    u = np.moveaxis(np.tensordot(ex, u, axes=(1, 2)), 0, 2)
                if m == 0:
                    image[t] += np.real(u)
                else:
                    xx, yy = np.meshgrid(xlabels, ylabels)
                    ramp = np.exp(
                        2j
                        * certified_pi()
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
    if height == 0 and np.all(as_disc(correlation).error == 0):
        # Exact allzero data retain the integer-initialized center. Integer
        # dimensions here are exactly representable; adding an exact zero
        # offset does not create uncertainty at the strict half boundary.
        wrapped = np.array(best[::-1], dtype=float)
        if z == 1:
            wrapped[2] = 0
        return dict(
            integer_peak_xyz=best[::-1],
            neighbors_xyz=disc_zeros((3, 3)),
            offsets_xyz=disc_zeros(3),
            offset_status_xyz=(
                "zero-curvature",
                "zero-curvature",
                "not-fitted" if z == 1 else "zero-curvature",
            ),
            wrapped_displacement_xyz=as_disc(wrapped),
        )
    if height > 0:
        certify_unique_peak(absolute, best, "drift")
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
        if n > 1 and as_disc(curvature).error > 0 and abs(curvature) <= as_disc(curvature).error:
            raise CertificateError("drift parabola curvature interval reaches zero")
        offset = 0.0 if curvature == 0 else -slope / curvature
        reason = "zero-curvature" if curvature == 0 else "fitted"
        if decision_greater(abs(as_disc(offset)), 1.5, "drift-offset-range"):
            offset, reason = 0.0, "outside-range"
        if axis == 0 and z == 1:
            offset, reason = 0.0, "not-fitted"
        offsets.append(offset)
        status.append(reason)
    xyz = as_disc(np.array(best[::-1], dtype=float)) + np.stack([as_disc(v) for v in offsets])
    for axis, n in enumerate([x, y, z]):
        if decision_greater(xyz[axis], n // 2, "drift-wrap"):
            xyz[axis] -= n
    if z == 1:
        xyz[2] = 0
    return dict(
        integer_peak_xyz=best[::-1],
        neighbors_xyz=np.stack([np.stack([as_disc(v) for v in row]) for row in neighbors]),
        offsets_xyz=np.stack([as_disc(v) for v in offsets]),
        offset_status_xyz=tuple(status),
        wrapped_displacement_xyz=xyz,
    )


def correlate(
    reference: Any, moving: Any, *, exponent: float, pitch: float, rd: float, highpass: float
) -> dict[str, Any]:
    symbolic = symbolic_correlation(reference, moving, exponent, pitch, rd, highpass)
    if symbolic is not None:
        CORRELATION_AUDITS.append(
            (np.asarray(reference).copy(), np.asarray(moving).copy(), exponent, symbolic)
        )
        return symbolic
    result = correlation_field(
        reference, moving, exponent=exponent, pitch=pitch, rd=rd, highpass=highpass
    )
    return result | peak(result["correlation"])


def correlation_field(
    reference: Any, moving: Any, *, exponent: float, pitch: float, rd: float, highpass: float
) -> dict[str, Any]:
    """Independent field accuracy; selecting a peak is a separate obligation."""
    z, y, x = reference.shape
    f0, fd = transform(reference), transform(moving)
    cross = disc_zeros((z, y, x // 2 + 1), dtype=complex)
    for h, i, j in np.ndindex(cross.shape):
        radius = hypot(as_disc(j) / (x * pitch), as_disc(lift(y)[i]) / (y * pitch))
        if radius < rd:
            c = np.conj(f0[h, i, j]) * fd[h, i, j]
            cross[h, i, j] = fractional_cross(c, exponent)
            if highpass > 0:
                cross[h, i, j] *= (1 - np.exp(-((radius / (highpass * rd)) ** 2))) ** 2
    correlation = transform(full(cross, x), inverse=True).real
    result = dict(
        cross_spectrum=cross,
        correlation=correlation,
        absolute_correlation=abs(correlation),
    )
    CORRELATION_AUDITS.append(
        (np.asarray(reference).copy(), np.asarray(moving).copy(), exponent, result)
    )
    return result


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
    centers = disc_zeros((d, subz, y, x))
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
    rd = 2 * as_disc(op["numerical_aperture"]) / (as_disc(op["wavelength_nm"]) / 1000)
    le = op["wavelength_nm"] / op["immersion_index"] / 1000
    cz = min(
        ceil((1 - cos(asin(op["numerical_aperture"] / op["immersion_index"]))) / le * z * dz),
        z // 2,
    )
    correlations = [
        correlate(centers[0], centers[i], exponent=0.25, pitch=pitch, rd=rd, highpass=highpass)
        for i in range(1, d)
    ]
    vectors = disc_zeros((d, 3))
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
    samples, values, evaluation = as_disc(samples), as_disc(values), as_disc(evaluation)
    tau = samples.copy()
    eta = tau if alias else evaluation.copy()
    tau[1:] -= tau[0]
    design = np.stack([np.stack([v, v * v, v * v * v]) for v in tau[1:]])
    coefficients = np.linalg.lstsq(design, values[1:] - values[0], rcond=None)[0]
    for i in range(len(eta)):
        eta[i] -= tau[0]
    fitted = values[0] + np.stack([np.stack([v, v * v, v * v * v]) for v in eta]) @ coefficients
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
    """Use the actual independently propagated camera/edge/high-pass chain."""
    candidates = []
    for ref, mov, power, result in CORRELATION_AUDITS:
        if (
            power == exponent
            and np.array_equal(ref, np.asarray(reference))
            and np.array_equal(mov, np.asarray(moving))
        ):
            candidates.append(
                max(
                    float(np.max(result[field].error))
                    for field in ["cross_spectrum", "correlation", "absolute_correlation"]
                )
            )
    if not candidates:
        raise CertificateError("correlation has no matching precomputed propagation")
    return max(candidates)


def finite_search(
    bands: Any, table: Any, initial: Any, *, t: int = 0, d: int = 0, **op: Any
) -> dict[str, Any]:
    """Literal finite 2D procedure, challenged separately by ordered-state rules."""
    _, _, _, z, y, x = bands.input_shape
    fit_order = 1 if z == 1 else 2
    pair = (0, fit_order)
    native = np.asarray(bands.quadratures[t, d])
    algebraic_tie = (
        x == 4
        and y == 1
        and initial[0] == -0.25 / fit_order
        and initial[1] == 0
        and np.array_equal(native[0, 0, 0], [1, -1, 1])
        and np.array_equal(native[2 * fit_order - 1, 0, 0], [1, 0, 1])
        and np.count_nonzero(native[0, 1:]) == 0
        and np.count_nonzero(native[2 * fit_order - 1, 1:]) == 0
        and np.count_nonzero(native[2 * fit_order]) == 0
        and np.all(np.asarray(table.samples) == 1)
    )
    coarse = overlaps(bands, table, initial, pair, t, d, **op)
    c = transform(np.sum(coarse["spatial"][0] * np.conj(coarse["spatial"][1]), axis=0))
    power = abs(c) ** 2
    i, j = np.unravel_index(np.argmax(power), power.shape)
    if algebraic_tie:
        i, j = 0, 1
        CERTIFICATES.append(
            dict(
                kind="peak-decision",
                label="coarse",
                proof="independent closed powers (4,16,4,16)*Z**2; first strict tied peak1",
                resolved=True,
            )
        )
    else:
        certify_unique_peak(power, (i, j), "coarse")
    refined = []
    for values in (
        [power[i, (j - 1) % x], power[i, j], power[i, (j + 1) % x]],
        [power[(i - 1) % y, j], power[i, j], power[(i + 1) % y, j]],
    ):
        curvature = values[2] + values[0] - 2 * values[1]
        refined.append(0.0 if curvature == 0 else -(values[2] - values[0]) / (2 * curvature))
    peakxy = as_disc(np.array([j, i], dtype=float)) + np.stack([as_disc(v) for v in refined])
    dx, dy = as_disc(1.0) / (x * bands.dxy_um), as_disc(1.0) / (y * bands.dxy_um)
    if decision_greater(peakxy[0] - x // 2, initial[0] * dx, "alias-negative-x"):
        peakxy[0] -= x
    if decision_greater(initial[0] * dx, peakxy[0] + x // 2, "alias-positive-x"):
        peakxy[0] += x
    if decision_greater(peakxy[1] - y // 2, initial[1] * dy, "alias-negative-y"):
        peakxy[1] -= y
    if decision_greater(initial[1] * dy, peakxy[1] + y // 2, "alias-positive-y"):
        peakxy[1] += y
    vector = peakxy * np.stack([dx, dy]) / fit_order
    if algebraic_tie:
        vector = as_disc(np.array([0.25 / fit_order, 0.0]))
    assert np.linalg.norm(vector) > 0, "independent coarse zero polar domain"
    mag, angle = np.linalg.norm(vector), np.arctan2(vector[1], vector[0])
    frozen = overlaps(bands, table, vector, pair, t, d, **op)
    trace = []
    x1, amp1 = 0.0, 0.0

    def evaluate(a: float, m: float, stage: str) -> float:
        k = m * np.stack([as_disc(cos(a)), as_disc(sin(a))])
        fit = regression(frozen["spatial"], k, pair, bands.dxy_um)
        objective = abs(fit["forward"]) ** 2
        if algebraic_tie:
            # The frozen lower spatial overlap is supported only at centered
            # x0. Its product with the constant higher overlap is independent
            # of every phase probe: SX=8Z,SY=2Z,C=2Z, objective=1/16.
            objective = as_disc(1 / 16)
        trace.append(
            dict(
                kind="evaluation",
                stage=stage,
                orders=pair,
                overlap_index=1,
                remake_overlaps=not trace,
                angle_rad=as_disc(a),
                magnitude_cyc_um=as_disc(m),
                carrier_cyc_um=k,
                objective=objective,
                **fit,
            )
        )
        return objective

    def parabola(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> float:
        if len({float(np.asarray(v)) for v in [x1, x2, x3]}) < 3:
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
        positive = decision_greater(amp3, amp2, "initial-" + stage)
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
        while decision_greater(amp3, amp2, "continue-" + stage):
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
    carrier = mag * np.stack([as_disc(cos(angle)), as_disc(sin(angle))])
    builds = [coarse, frozen]
    o = bands.noise_variance_factors.shape[-1]
    factors = disc_empty((o - 1,), dtype=complex)
    factors[fit_order - 1] = trace[-1]["forward"]
    for b in range(1, o):
        if b == fit_order:
            continue
        later_pair = (b - 1, b) if z == 1 else (0, b)
        build = overlaps(bands, table, carrier, later_pair, t, d, **op)
        fit = regression(build["spatial"], carrier, later_pair, bands.dxy_um)
        trace.append(
            dict(
                kind="evaluation",
                stage="later-order",
                orders=later_pair,
                overlap_index=len(builds),
                remake_overlaps=True,
                angle_rad=as_disc(angle),
                magnitude_cyc_um=as_disc(mag),
                carrier_cyc_um=carrier,
                objective=abs(fit["forward"]) ** 2,
                **fit,
            )
        )
        factors[b - 1] = fit["forward"]
        builds.append(build)
    return dict(
        carrier=carrier,
        raw=factors,
        modulation=np.cumprod(factors) if z == 1 else factors.copy(),
        coarse_carrier=vector,
        builds=builds,
        trace=trace,
        coarse_power=power,
    )


class CertificateError(AssertionError):
    """The independent observer cannot certify a comparison or decision."""


CERTIFICATES: list[dict[str, Any]] = []


class Disc(np.ndarray):
    """Independent complex-norm enclosures, with separate observer/backend errors.

    The backend column is conditional on the primitive/FFT model recorded in
    correction-1/expectations.md. It is never a certification of installed code.
    """

    @property
    def __array_priority__(self) -> Any:
        """Keep uncertainty-aware operations ahead of plain array coercion."""
        return 1000

    def __new__(cls, value: Any, observer: Any = 0.0, backend: Any = 0.0) -> Any:
        base = np.asarray(value)

        def scalar_error(error: Any) -> bool:
            return isinstance(error, (int, float, np.integer, np.floating, np.bool_)) or (
                isinstance(error, np.ndarray) and error.shape == () and error.dtype.kind in "biuf"
            )

        if (
            cls is Disc
            and base.shape == ()
            and base.dtype.kind in "biufc"
            and base.flags.c_contiguous
            and scalar_error(observer)
            and scalar_error(backend)
        ):
            obj = np.ndarray.__new__(cls, (), dtype=base.dtype, buffer=base)
            oe = np.array(observer, dtype=float, order="C", copy=True)
            be = np.array(backend, dtype=float, order="C", copy=True)
        else:
            obj = base.view(cls)
            oe = np.broadcast_to(observer, obj.shape).astype(float, order="C", copy=True)
            be = np.broadcast_to(backend, obj.shape).astype(float, order="C", copy=True)
        np.nextafter(oe, np.inf, out=oe, where=oe > 0)
        np.nextafter(be, np.inf, out=be, where=be > 0)
        obj.observer = oe
        obj.backend = be
        return obj

    def __array_finalize__(self, source: Any) -> None:
        """Preserve independent uncertainty through this NumPy protocol."""
        if source is not None:
            self.observer = source.observer if hasattr(source, "observer") else np.zeros(self.shape)
            self.backend = source.backend if hasattr(source, "backend") else np.zeros(self.shape)

    @property
    def error(self) -> Any:
        return self.observer + self.backend

    def __getitem__(self, index: Any) -> Any:
        """Preserve independent uncertainty through this NumPy protocol."""
        return Disc(np.asarray(self)[index], self.observer[index], self.backend[index])

    def __setitem__(self, index: Any, value: Any) -> None:
        """Preserve independent uncertainty through this NumPy protocol."""
        np.ndarray.__setitem__(self, index, np.asarray(value))
        self.observer[index] = getattr(value, "observer", 0)
        self.backend[index] = getattr(value, "backend", 0)

    def copy(self, order: Any = "C") -> Any:
        return Disc(np.asarray(self).copy(order), self.observer, self.backend)

    def reshape(self, *shape: Any, **kwargs: Any) -> Any:
        return Disc(
            np.asarray(self).reshape(*shape, **kwargs),
            self.observer.reshape(*shape, **kwargs),
            self.backend.reshape(*shape, **kwargs),
        )

    def transpose(self, *axes: Any) -> Any:
        return Disc(
            np.asarray(self).transpose(*axes),
            self.observer.transpose(*axes),
            self.backend.transpose(*axes),
        )

    @property
    def T(self) -> Any:
        return self.transpose()

    @property
    def real(self) -> Any:
        return Disc(np.asarray(self, dtype=np.complex128).real, self.observer, self.backend)

    @real.setter
    def real(self, value: Any) -> None:
        target: Any = np.asarray(self)
        target.real[...] = np.asarray(value)
        self.observer = np.maximum(self.observer, getattr(value, "observer", 0))
        self.backend = np.maximum(self.backend, getattr(value, "backend", 0))

    @property
    def imag(self) -> Any:
        return Disc(np.asarray(self, dtype=np.complex128).imag, self.observer, self.backend)

    @imag.setter
    def imag(self, value: Any) -> None:
        target: Any = np.asarray(self)
        target.imag[...] = np.asarray(value)
        self.observer = np.maximum(self.observer, getattr(value, "observer", 0))
        self.backend = np.maximum(self.backend, getattr(value, "backend", 0))

    def __array_ufunc__(self, operation: Any, method: str, *inputs: Any, **kwargs: Any) -> Any:
        """Preserve independent uncertainty through this NumPy protocol."""
        if method != "__call__":
            if method == "reduce" and operation is np.add:
                return disc_sum(inputs[0], **kwargs)
            return NotImplemented
        target = kwargs.pop("out", None)
        values = [np.asarray(x) for x in inputs]
        result = operation(*values, **kwargs)
        if np.asarray(result).dtype.kind == "b" or operation in {
            np.floor,
            np.ceil,
            np.rint,
            np.sign,
            np.isfinite,
        }:
            return result
        obs = [
            x.observer
            if isinstance(x, Disc) and x.observer.shape == v.shape
            else np.broadcast_to(getattr(x, "observer", 0), v.shape)
            for x, v in zip(inputs, values, strict=True)
        ]
        back = [
            x.backend
            if isinstance(x, Disc) and x.backend.shape == v.shape
            else np.broadcast_to(getattr(x, "backend", 0), v.shape)
            for x, v in zip(inputs, values, strict=True)
        ]
        magnitude = [abs(x) for x in values]
        rounding = gamma(8 if np.iscomplexobj(result) else 1) * abs(result)

        def propagate(errors: list[Any]) -> Any:
            if operation in {np.add, np.subtract}:
                return errors[0] + errors[1]
            if operation in {np.negative, np.positive, np.conjugate, np.absolute}:
                return errors[0]
            if operation in {np.multiply, np.matmul}:
                if operation is np.matmul:
                    return (
                        magnitude[0] @ errors[1] + errors[0] @ magnitude[1] + errors[0] @ errors[1]
                    )
                return magnitude[0] * errors[1] + magnitude[1] * errors[0] + errors[0] * errors[1]
            if operation in {np.divide, np.true_divide}:
                margin = magnitude[1] - errors[1]
                if np.any(margin <= 0):
                    raise CertificateError("division interval contains zero")
                return (errors[0] + abs(result) * errors[1]) / margin
            if operation in {np.sin, np.cos, np.arctan}:
                return errors[0]
            if operation is np.tan:
                low, high = values[0] - errors[0], values[0] + errors[0]
                return errors[0] * np.maximum(1 / np.cos(low) ** 2, 1 / np.cos(high) ** 2)
            if operation is np.exp:
                return np.exp(np.real(values[0]) + errors[0]) * errors[0]
            if operation is np.sqrt:
                if np.any(values[0] < 0):
                    raise CertificateError("negative square-root observer input")
                denominator = np.sqrt(values[0] + errors[0]) + np.sqrt(
                    np.maximum(values[0] - errors[0], 0)
                )
                with np.errstate(divide="ignore", invalid="ignore"):
                    return np.where(denominator > 0, 2 * errors[0] / denominator, 0)
            if operation is np.square:
                return 2 * magnitude[0] * errors[0] + errors[0] ** 2
            if operation is np.power:
                if np.any(errors[1] != 0):
                    raise CertificateError("uncertain exponent needs an explicit certificate")
                exponent = values[1]
                low = magnitude[0] - errors[0]
                high = magnitude[0] + errors[0]
                if np.any((low <= 0) & (exponent < 0)):
                    raise CertificateError("negative power interval reaches zero")
                if np.any(values[0] < 0) and np.any(exponent != np.floor(exponent)):
                    raise CertificateError("fractional power of negative observer input")
                with np.errstate(divide="ignore", invalid="ignore"):
                    derivative = abs(exponent) * np.maximum(
                        np.maximum(low, 0) ** (exponent - 1), high ** (exponent - 1)
                    )
                    regular = derivative * errors[0]
                    holder = high**exponent + magnitude[0] ** exponent
                return np.where(
                    (low > 0) | (exponent >= 1), regular, np.where(exponent == 0, 0, holder)
                )
            if operation in {np.maximum, np.minimum}:
                difference = values[0] - values[1]
                stable = abs(difference) > errors[0] + errors[1]
                choose_first = difference >= 0 if operation is np.maximum else difference <= 0
                selected = np.where(choose_first, errors[0], errors[1])
                return np.where(stable, selected, np.maximum(errors[0], errors[1]))
            if operation is np.hypot:
                return np.hypot(errors[0], errors[1])
            if operation is np.arctan2:
                radius = np.hypot(*values)
                delta = np.hypot(*errors)
                if np.any(radius <= delta):
                    raise CertificateError("polar interval reaches the origin")
                return delta / (radius - delta)
            raise CertificateError(f"uncertified observer primitive: {operation.__name__}")

        if operation is np.matmul:
            n = np.shape(values[0])[-1]
            rounding = gamma(8 * n) * (magnitude[0] @ magnitude[1])
        if operation is np.hypot or operation is np.absolute and np.iscomplexobj(values[0]):
            # Two real squares, one sum, one square root. The conditional
            # primitive envelope also covers a stable library hypot.
            rounding = gamma(4) * abs(result)
        if operation is np.power and np.any(values[1] != np.floor(values[1])):
            rounding = 4 * U * abs(result)
        if operation in {np.sin, np.cos, np.tan, np.arctan, np.arctan2}:
            rounding = np.full(np.shape(result), 4 * U)
        if operation is np.exp:
            rounding = np.full(np.shape(result), sqrt(2) * 4 * U) * np.exp(np.real(values[0]))
        propagated_observer = propagate(obs)
        observer = propagated_observer + rounding
        total_input = [a + b for a, b in zip(obs, back, strict=True)]
        backend = np.maximum(propagate(total_input) - propagated_observer, 0) + rounding
        wrapped = Disc(result, observer, backend)
        if target is not None:
            destination = target[0]
            destination[...] = wrapped
            return destination
        return wrapped

    def __array_function__(self, function: Any, types: Any, args: Any, kwargs: Any) -> Any:
        """Preserve independent uncertainty through this NumPy protocol."""
        if function in {np.sum, np.mean}:
            result = disc_sum(*args, **kwargs)
            if function is np.mean:
                axis = kwargs.get("axis")
                axes = (axis,) if isinstance(axis, int) else axis
                n = args[0].size if axis is None else int(np.prod([args[0].shape[a] for a in axes]))
                result = result / n
            return result
        if function in {np.tensordot, np.einsum}:
            plain = [np.asarray(a) if isinstance(a, Disc) else a for a in args]
            result = function(*plain, **kwargs)
            arrays = [(i, a) for i, a in enumerate(args) if isinstance(a, np.ndarray)]
            if len(arrays) != 2:
                raise CertificateError("multioperand einsum requires explicit decomposition")
            (ia, a), (ib, b) = arrays
            av, bv = abs(np.asarray(a)), abs(np.asarray(b))
            ae = np.broadcast_to(getattr(a, "error", 0), av.shape)
            be = np.broadcast_to(getattr(b, "error", 0), bv.shape)
            ao = np.broadcast_to(getattr(a, "observer", 0), av.shape)
            bo = np.broadcast_to(getattr(b, "observer", 0), bv.shape)

            def contraction(x: Any, y: Any) -> Any:
                parameters = list(plain)
                parameters[ia], parameters[ib] = x, y
                return function(*parameters, **kwargs)

            terms = max(
                1, int(np.asarray(a).size * np.asarray(b).size // max(np.asarray(result).size, 1))
            )
            # The exact term count is the contraction of matching all-one arrays.
            counts = contraction(np.ones_like(av), np.ones_like(bv))
            n = int(np.max(counts)) if np.size(counts) else terms
            rounding = gamma(8 * n) * contraction(av, bv)
            oe = contraction(av, bo) + contraction(ao, bv) + contraction(ao, bo)
            te = contraction(av, be) + contraction(ae, bv) + contraction(ae, be)
            return Disc(result, oe + rounding, np.maximum(te - oe, 0) + rounding)
        if function is np.linalg.lstsq:
            return certified_lstsq(*args, **kwargs)
        if function is np.linalg.norm:
            value = args[0]
            result = np.linalg.norm(np.asarray(value), **kwargs)
            axis = kwargs.get("axis")
            oe = np.sum(value.observer, axis=axis)
            be = np.sum(value.backend, axis=axis)
            rounding = gamma(8 * max(value.size, 1)) * abs(result)
            return Disc(result, oe + rounding, be + rounding)
        if function in {np.real, np.imag}:
            return args[0].real if function is np.real else args[0].imag
        if function is np.outer:
            return as_disc(args[0]).reshape(-1, 1) * as_disc(args[1]).reshape(1, -1)
        if function in {np.stack, np.concatenate, np.column_stack}:
            values = args[0]
            value = function([np.asarray(v) for v in values], **kwargs)
            oe = function(
                [np.broadcast_to(getattr(v, "observer", 0), np.shape(v)) for v in values], **kwargs
            )
            be = function(
                [np.broadcast_to(getattr(v, "backend", 0), np.shape(v)) for v in values], **kwargs
            )
            return Disc(value, oe, be)
        if function in {np.moveaxis, np.broadcast_to, np.repeat, np.tile, np.reshape, np.transpose}:
            value = args[0]
            rest = args[1:]
            return Disc(
                function(np.asarray(value), *rest, **kwargs),
                function(value.observer, *rest, **kwargs),
                function(value.backend, *rest, **kwargs),
            )
        if function in {np.max, np.min, np.amax, np.amin}:
            value = args[0]
            return Disc(
                function(np.asarray(value), **kwargs),
                np.max(value.observer, **kwargs),
                np.max(value.backend, **kwargs),
            )
        if function in {np.zeros_like, np.empty_like, np.ones_like}:
            return Disc(function(np.asarray(args[0]), **kwargs))
        if function is np.meshgrid:
            v = function(*[np.asarray(a) for a in args], **kwargs)
            oe = function(
                *[np.broadcast_to(getattr(a, "observer", 0), np.shape(a)) for a in args], **kwargs
            )
            be = function(
                *[np.broadcast_to(getattr(a, "backend", 0), np.shape(a)) for a in args], **kwargs
            )
            return [Disc(x, o, b) for x, o, b in zip(v, oe, be, strict=True)]
        if function is np.cumprod:
            value = args[0]
            result = []
            product = Disc(1.0)
            for v in value:
                product = product * v
                result.append(product)
            return np.stack(result)
        # Queries do not perform uncertain arithmetic or produce a numeric oracle.
        if function in {
            np.shape,
            np.ndim,
            np.size,
            np.iscomplexobj,
            np.shares_memory,
            np.count_nonzero,
            np.argmax,
            np.unravel_index,
            np.argwhere,
            np.array_equal,
            np.all,
            np.any,
            np.isclose,
            np.allclose,
        }:
            return function(*[np.asarray(a) if isinstance(a, Disc) else a for a in args], **kwargs)
        raise CertificateError(f"uncertified observer array operation: {function.__name__}")


def disc_sum(value: Any, axis: Any = None, **kwargs: Any) -> Any:
    kwargs.pop("dtype", None)
    plain = np.asarray(value)
    result = np.sum(plain, axis=axis, **kwargs)
    axes = (
        tuple(range(plain.ndim)) if axis is None else ((axis,) if isinstance(axis, int) else axis)
    )
    n = int(np.prod([plain.shape[a] for a in axes]))
    rounding = gamma((8 if np.iscomplexobj(plain) else 1) * n) * np.sum(
        abs(plain), axis=axis, **kwargs
    )
    oe = np.sum(np.broadcast_to(getattr(value, "observer", 0), plain.shape), axis=axis, **kwargs)
    be = np.sum(np.broadcast_to(getattr(value, "backend", 0), plain.shape), axis=axis, **kwargs)
    return Disc(result, oe + rounding, be + rounding)


def certified_lstsq(a: Any, b: Any, **kwargs: Any) -> Any:
    av, bv = np.asarray(a), np.asarray(b)
    result = np.linalg.lstsq(av, bv, **kwargs)
    x = result[0]
    gram = av.T @ av
    inverse = np.linalg.inv(gram)
    residual = np.eye(gram.shape[0]) - inverse @ gram
    residual_error = gamma(8 * av.shape[0]) * (abs(av).T @ abs(av))
    multiply_error = gamma(8 * av.shape[1]) * (abs(inverse) @ abs(gram))
    subtract_error = U * (np.eye(gram.shape[0]) + abs(inverse @ gram))
    rho = float(
        np.linalg.norm(
            abs(residual) + abs(inverse) @ residual_error + multiply_error + subtract_error,
            ord=np.inf,
        )
    )
    if rho >= 1:
        raise CertificateError("normal-equation inverse residual certificate failed")
    inverse_norm = float(np.linalg.norm(inverse, ord=np.inf)) / (1 - rho)
    pseudo = inverse @ av.T
    norm = float(np.linalg.norm(pseudo, ord=np.inf))
    norm += gamma(8 * av.shape[1]) * float(np.linalg.norm(abs(inverse) @ abs(av.T), ord=np.inf))
    norm += rho * inverse_norm * float(np.linalg.norm(av.T, ord=np.inf))
    anorm = float(np.linalg.norm(av, ord=np.inf))
    transpose_norm = float(np.linalg.norm(av.T, ord=np.inf))
    primal = bv - av @ x
    normal_residual = av.T @ primal
    residual_round = gamma(8 * max(av.shape)) * (abs(av).T @ (abs(bv) + abs(av) @ abs(x)))
    residual_bound = float(np.max(abs(normal_residual) + residual_round))
    xnorm, bnorm = float(np.max(abs(x))), float(np.max(abs(bv)))

    def enclosure(ae: float, be: float, beta: float) -> tuple[float, float]:
        # A' = A + dA, b' = b + db. Bound the normal residual around
        # THIS independent x. The production residual envelope contains x',
        # so its delta-x coefficient belongs in the denominator as well.
        da, dat = av.shape[1] * ae, av.shape[0] * ae
        dg = transpose_norm * da + dat * anorm + dat * da
        feedback = beta * (transpose_norm + dat) * (anorm + da)
        denominator = 1 - inverse_norm * (dg + feedback)
        if denominator <= 0:
            raise CertificateError("solve perturbation certificate is unresolved")
        incoming = dat * float(np.max(abs(primal)))
        incoming += (transpose_norm + dat) * (be + da * xnorm)
        production = beta * (transpose_norm + dat) * (bnorm + be + (anorm + da) * xnorm)
        error = inverse_norm * (residual_bound + incoming + production) / denominator
        return error, denominator

    observer, observer_margin = enclosure(
        float(np.max(getattr(a, "observer", 0))),
        float(np.max(getattr(b, "observer", 0))),
        0.0,
    )
    total, backend_margin = enclosure(
        float(np.max(getattr(a, "error", 0))),
        float(np.max(getattr(b, "error", 0))),
        gamma(8 * max(av.shape)),
    )
    CERTIFICATES.append(
        dict(
            kind="solve",
            shape=list(av.shape),
            inverse_residual=rho,
            inverse_gram_norm=inverse_norm,
            pseudoinverse_norm=norm,
            residual=residual_bound,
            observer=observer,
            conditional_backend=max(total - observer, 0),
            observer_denominator=observer_margin,
            conditional_denominator=backend_margin,
            error=total,
        )
    )
    return Disc(x, observer, max(total - observer, 0)), *result[1:]


def as_disc(value: Any) -> Any:
    return value if isinstance(value, Disc) else Disc(value)


def disc_zeros(shape: Any, **kwargs: Any) -> Any:
    return Disc(np.zeros(shape, **kwargs))


def disc_ones(shape: Any, **kwargs: Any) -> Any:
    return Disc(np.ones(shape, **kwargs))


def disc_empty(shape: Any, **kwargs: Any) -> Any:
    return Disc(np.empty(shape, **kwargs))


def certified_pi() -> Any:
    return Disc(pi, U * pi, U * pi)


def fractional_cross(value: Any, exponent: float) -> Any:
    value = as_disc(value)
    plain = complex(np.asarray(value))
    magnitude = abs(plain)
    observed = 0j if plain == 0 else plain * magnitude ** (exponent - 1)

    def bound(error: float) -> float:
        if magnitude > error:
            return error * (magnitude - error) ** (exponent - 1)
        return (magnitude + error) ** exponent + magnitude**exponent

    oe = bound(float(value.observer))
    be = bound(float(value.error)) - oe
    rounding = gamma(12) * magnitude**exponent
    return Disc(observed, oe + rounding, be + rounding)


def sin(value: Any) -> Any:
    return np.sin(value) if isinstance(value, Disc) else _plain_sin(value)


def cos(value: Any) -> Any:
    return np.cos(value) if isinstance(value, Disc) else _plain_cos(value)


def sqrt(value: Any) -> Any:
    return np.sqrt(value) if isinstance(value, Disc) else _plain_sqrt(value)


def hypot(a: Any, b: Any) -> Any:
    return (
        np.hypot(as_disc(a), as_disc(b))
        if isinstance(a, Disc) or isinstance(b, Disc)
        else _plain_hypot(a, b)
    )


PREPARATION_AUDITS: dict[int, Any] = {}
CORRELATION_AUDITS: list[Any] = []


def exposure_ramp(displacement: Any, y: int, x: int) -> Any:
    yy, xx = np.meshgrid(lift(y), np.arange(x // 2 + 1), indexing="ij")
    return np.exp(2j * certified_pi() * (displacement[0] * xx / x + displacement[1] * yy / y))


def between_ramp(displacement: Any, z: int, y: int, x: int) -> Any:
    zz, yy, xx = np.meshgrid(lift(z), lift(y), np.arange(x // 2 + 1), indexing="ij")
    return np.exp(
        2j
        * certified_pi()
        * (displacement[0] * xx / x + displacement[1] * yy / y + displacement[2] * zz / z)
    )


def preparation_drift(
    images: Any, frames: Any, off_frames: Any, backgrounds: Any, settings: Any
) -> Any:
    tcount, dcount, pcount, zcount, y, x = images.shape
    between = disc_zeros((tcount, dcount, 3))
    exposure = disc_zeros((tcount, dcount, zcount, pcount, 2))
    phases = disc_zeros((tcount, dcount, zcount, pcount))
    clock = settings.get("header_timestamps")
    clock = None if clock is None else as_disc(clock).copy()
    audit: dict[str, Any] = dict(
        between_displacements_pixels=between,
        exposure_displacements_pixels=exposure,
        phases=phases,
        header_timestamps_after=clock,
        builds=[],
        correlations=[],
        fits=[],
        off_events=[],
    )
    active = settings.get("drift_between", False) or settings.get("drift_within", False)
    within = settings.get("drift_within", False)
    mode = settings["acquisition_mode"]
    off = settings.get("off_exposures")
    n = 0 if off is None else off.shape[4]
    for t in range(tcount):
        if active and settings.get("storage_order", "direction-major") == "direction-major":
            built = between_expected(
                images[t],
                background=backgrounds[t],
                off=None if off is None else as_disc(off[t]),
                dz=settings["dz_um"],
                pitch=settings["dxy_um"],
                highpass=settings.get("drift_filter_fraction", 0),
                **{k: settings[k] for k in optics()},
            )
            between[t] = built["vectors"]
            audit["builds"].append(built)
            audit["correlations"].extend(built["correlations"])
        if within and mode == "3d":
            if clock is None:
                raise CertificateError("missing cubic clock")
            indices = np.arange(dcount) * zcount * pcount + zcount * pcount // 2
            fit = cubic(
                clock[indices], between[t, :, :2], clock[: dcount * zcount * pcount], alias=False
            )
            clock[: dcount * zcount * pcount] = fit["evaluation_timestamps_after"]
            exposure[t] = fit["evaluated_xy"].reshape(dcount, zcount, pcount, 2)
            for d in range(1, dcount):
                exposure[t, d] -= between[t, d, :2]
            audit["fits"].append(fit)
        for d in range(dcount):
            if within and mode == "2d":
                if n == 0:
                    raise CertificateError("uninitialized within reference")
                prepared = frames[t, d, :, 0] + off_frames[t, d, :, 0]
                values = disc_empty((pcount, 2))
                for p in range(pcount):
                    corr = correlate(
                        prepared[0][None],
                        prepared[p][None],
                        exponent=0.5,
                        pitch=settings["dxy_um"],
                        rd=2 * settings["numerical_aperture"] / (settings["wavelength_nm"] / 1000),
                        highpass=settings.get("drift_filter_fraction", 0),
                    )
                    values[p] = corr["wrapped_displacement_xyz"][:2]
                    audit["correlations"].append(corr)
                if settings.get("fit_drift", False):
                    if clock is None:
                        raise CertificateError("missing within fit clock")
                    indices = d * pcount * (n + 1) + np.arange(pcount) * (n + 1) + n
                    fit = cubic(clock[indices], values, clock[indices], alias=True)
                    values = fit["evaluated_xy"]
                    audit["fits"].append(fit)
                exposure[t, d, 0] = values
            if within and settings.get("adjust_phases", False):
                theta = (
                    as_disc(settings.get("phase_start_angle_rad", 1.57193))
                    + (-1 if settings.get("negative_angle_step", False) else 1)
                    * certified_pi()
                    * d
                    / dcount
                )
                vector = np.stack([np.cos(theta), np.sin(theta)]) / settings["linespacing_um"]
                for z in range(zcount):
                    base = (
                        as_disc(settings["header_phases_rad"])[
                            d * pcount * (n + 1) + np.arange(pcount) * (n + 1)
                        ]
                        if zcount == 1
                        else 2 * certified_pi() * np.arange(pcount) / pcount
                    )
                    phases[t, d, z] = base + 2 * certified_pi() * settings["dxy_um"] * (
                        exposure[t, d, z] @ vector
                    )
    return audit


def combine_expected(on: Any, off: Any, call_z: int, settings: Any, events_list: Any) -> None:
    selectors = settings.get("combine_off_orders")
    if selectors is None or not any(v > 0 for v in selectors):
        return
    _, _, y, hx = on.shape
    x = 2 * (hx - 1)
    cutoff = int(2 * settings["numerical_aperture"] / (settings["wavelength_nm"] / 1000))
    pitch = settings["dxy_um"]
    cells = np.array(
        [
            [
                int(j / (x * pitch)) ** 2 + int(lift(y)[i] / (y * pitch)) ** 2 <= cutoff**2
                for j in range(hx)
            ]
            for i in range(y)
        ]
    )
    ni, no = int(np.count_nonzero(cells)), int(np.count_nonzero(~cells))
    if not ni or not no:
        raise CertificateError("empty off statistic set")
    for m, selected in enumerate(selectors):
        if selected <= 0:
            continue
        slots = slice(0, 1) if m == 0 else slice(2 * m - 1, 2 * m + 1)
        a, b = on[slots, 0].copy(), off[slots, 0]
        pa, pb = np.sum(abs(a) ** 2, axis=0), np.sum(abs(b) ** 2, axis=0)
        na, nb = np.sum(pa[~cells]) / no, np.sum(pb[~cells]) / no
        sa, sb = np.sum(pa[cells]) / ni - na, np.sum(pb[cells]) / ni - nb
        if abs(na) <= na.error or abs(nb) <= nb.error:
            raise CertificateError(
                f"off noise observer margin: call={call_z}, order={m}, "
                f"on={np.asarray(na)}, error={na.error}, "
                f"off={np.asarray(nb)}, error={nb.error}"
            )
        positive_a = decision_greater(sa, 0, "off-on-signal-clipping")
        positive_b = decision_greater(sb, 0, "off-off-signal-clipping")
        ca, cb = sa if positive_a else as_disc(0.0), sb if positive_b else as_disc(0.0)
        replaced = bool(ca == 0 and cb == 0)
        if replaced:
            ca, cb = as_disc(1.0), as_disc(1.0)
        u, v = np.sqrt(ca) / na, np.sqrt(cb) / nb
        fa, fb = u / (u + v), v / (u + v)
        CERTIFICATES.append(
            dict(
                kind="off-statistic",
                call_z=call_z,
                order=m,
                on_noise=float(np.asarray(na)),
                on_noise_error=float(na.error),
                off_noise=float(np.asarray(nb)),
                off_noise_error=float(nb.error),
                denominator=float(np.asarray(u + v)),
                denominator_error=float((u + v).error),
                on_fraction_error=float(fa.error),
                off_fraction_error=float(fb.error),
            )
        )
        on[slots, 0] = fa * a + (1 if m == 0 else -1) * fb * b
        events_list.append(
            dict(
                call_z=call_z,
                affected_z=0,
                order=m,
                cutoff_integer=cutoff,
                inside_count=ni,
                outside_count=no,
                on_noise=na,
                off_noise=nb,
                on_signal2_before_clip=sa,
                off_signal2_before_clip=sb,
                both_zero_replaced=replaced,
                on_scale=u,
                off_scale=v,
                denominator=u + v,
                on_fraction=fa,
                off_fraction=fb,
                quadratures_after=on[slots, 0].copy(),
            )
        )


# Public-call observation is explicit: predict with independent equations before
# invoking the unchanged real public entry. Never manufacture a product result.
PUBLIC_MODELS: dict[int, tuple[Any, Any, Any]] = {}
OBSERVATION_BINDINGS: list[tuple[Any, Any]] = []


def bind_observation(actual: Any, expected: Any) -> None:
    if isinstance(expected, Disc):
        OBSERVATION_BINDINGS.append((actual, expected))
        return
    if isinstance(expected, dict):
        for key, value in expected.items():
            if isinstance(actual, dict) and key in actual:
                bind_observation(actual[key], value)
            elif hasattr(actual, key):
                bind_observation(getattr(actual, key), value)
    elif isinstance(expected, (tuple, list)) and isinstance(actual, (tuple, list)):
        for a, b in zip(actual, expected, strict=False):
            bind_observation(a, b)
    elif hasattr(expected, "__dict__"):
        bind_observation(actual, vars(expected))


def model_bands(bands: Any) -> Any:
    from types import SimpleNamespace

    item = PUBLIC_MODELS.get(id(bands))
    if item is None:
        # This is a caller-declared value record. Accuracy of its creation is a
        # separate assertion; all used values remain explicit mathematical inputs.
        return SimpleNamespace(
            **{
                name: as_disc(getattr(bands, name))
                if name in {"quadratures", "noise_variance_factors"}
                else getattr(bands, name)
                for name in [
                    "quadratures",
                    "noise_variance_factors",
                    "input_shape",
                    "input_scale",
                    "dxy_um",
                    "dz_um",
                    "lateral_zoom",
                    "axial_zoom",
                    "acquisition_mode",
                ]
            }
        )
    _, model, snapshot = item
    result = copy(model)
    for name in ["quadratures", "noise_variance_factors"]:
        value = getattr(bands, name)
        if not np.array_equal(value, snapshot[name]):
            setattr(result, name, as_disc(value.copy()))
    return result


def model_table(table: Any) -> Any:
    item = PUBLIC_MODELS.get(id(table))
    return item[1] if item is not None else table


def predict_public(name: str, args: Any, kwargs: Any) -> Any:
    from types import SimpleNamespace

    if name in {"prepare_acquisition_bands", "prepare_bands"}:
        settings = options() | kwargs
        if name == "prepare_bands":
            settings["acquisition_mode"] = "3d"
        image = args[0]
        if not isinstance(image, np.ndarray) or image.ndim != 6 or image.dtype.kind not in "iuf":
            return None
        t, d, p, z, y, x = image.shape
        zoom, a = settings["lateral_zoom"], settings["axial_zoom"]
        if (
            t * d * p * z > 2**31 - 1
            or (x + 2) * y * z > 2**31 - 1
            or 8 * int(zoom * x) * int(zoom * y) * int(a * z) > 2**32 - 1
        ):
            return None
        if name == "prepare_acquisition_bands":
            # These invalid declarations must reach the public validator
            # before truthiness or selector arithmetic picks an operation.
            if any(
                type(settings.get(key, False)) is not bool
                for key in ("drift_between", "drift_within")
            ):
                return None
            selectors = settings.get("combine_off_orders")
            if selectors is not None and (
                not isinstance(selectors, np.ndarray)
                or selectors.dtype.kind not in "iu"
                or np.any(selectors > 2**31 - 1)
                or np.any(selectors < -(2**31))
                or (np.any(selectors > 0) and settings.get("off_exposures") is None)
            ):
                return None
        expected = prepare_expected(image, settings)
        model = SimpleNamespace(
            **expected,
            input_shape=image.shape,
            acquisition_mode=settings["acquisition_mode"],
            dxy_um=settings["dxy_um"],
            dz_um=settings["dz_um"],
            lateral_zoom=zoom,
            axial_zoom=a,
        )
        model.declared_settings = settings
        model.numeric_events = preparation_numeric_events(model)
        if name == "prepare_bands":
            model.noise_variance_factors = model.noise_variance_factors[0]
            model.separation_matrices = model.separation_matrices[0, :, 0]
            model.phase_angles_rad = model.phase_angles_rad[0, :, 0]
        return model
    if name == "declare_otf":
        return SimpleNamespace(
            samples=as_disc(args[0]),
            layout=kwargs["layout"],
            dkr_cyc_um=kwargs["dkr_cyc_um"],
            dkz_cyc_um=kwargs["dkz_cyc_um"],
        )
    if name == "prepare_bead_otf":
        from test_c_acquisition_transfer import bead_expected

        expected = bead_expected(args[0], kwargs)
        expected["transfer"] = SimpleNamespace(
            samples=expected["samples"],
            layout="radial",
            dkr_cyc_um=expected["dkr"],
            dkz_cyc_um=expected["dkz"],
        )
        return SimpleNamespace(**expected)
    if name == "sample_otf":
        return sample(
            model_table(args[0]),
            args[1],
            args[2],
            args[3],
            kwargs["dkz_cyc_um"],
            kwargs.get("order", 0),
        )
    if name == "estimate_parameters":
        return parameter_model(model_bands(args[0]), model_table(args[1]), **kwargs)
    if name == "reconstruct_known":
        if kwargs.get("output_taper") == "power" and kwargs.get("power_taper_exponent") is None:
            return None
        bands = model_bands(args[0])
        if bands.noise_variance_factors.ndim == 2:
            bands = copy(bands)
            bands.noise_variance_factors = np.broadcast_to(
                bands.noise_variance_factors,
                (bands.input_shape[0], *bands.noise_variance_factors.shape),
            )
        expected = reconstruct_expected(
            bands,
            model_table(args[1]),
            certify_parameter_argument(kwargs["carriers_cyc_um"]),
            certify_parameter_argument(kwargs["modulation"]),
            **{k: v for k, v in kwargs.items() if k not in {"carriers_cyc_um", "modulation"}},
        )
        model = SimpleNamespace(**expected)
        model.numeric_events = reconstruction_numeric_events(model, bands, kwargs)
        return model
    return None


def preparation_numeric_events(model: Any) -> Any:
    audit = PREPARATION_AUDITS[id(model.quadratures)]
    result = {
        "between-build": audit["builds"],
        "drift-correlation": audit["correlations"],
        "cubic-fit": audit["fits"],
        "off-combination": audit["off_events"],
        "phase-design": [],
        "exposure-correction": [],
        "between-correction": [],
    }
    t, d, p, z, y, x = model.input_shape
    for ti, di, zi in np.ndindex(t, d, z):
        left = model.separation_matrices[ti, di, zi]
        count = (left.shape[0] + 1) // 2
        if model.phase_policies[ti][di][zi] == "uniform":
            local_noise = disc_ones((count,))
        else:
            local_noise = np.stack(
                [np.sum(left[0] ** 2) / p]
                + [np.sum(left[2 * m - 1 : 2 * m + 1] ** 2) / p for m in range(1, count)]
            )
        result["phase-design"].append(
            dict(
                phases_rad=model.phase_angles_rad[ti, di, zi],
                separation_matrix=model.separation_matrices[ti, di, zi],
                noise_variance_factors=local_noise,
            )
        )
        if model.declared_settings.get("drift_within", False):
            for phase_index in range(p):
                shift = model.exposure_displacements_pixels[ti, di, zi, phase_index]
                result["exposure-correction"].append(
                    dict(displacement_xy=shift, phase_multiplier=exposure_ramp(shift, y, x))
                )
    for ti, di in np.ndindex(t, d):
        if di > 0 and model.declared_settings.get("drift_between", False):
            shift = model.between_displacements_pixels[ti, di]
            result["between-correction"].append(
                dict(displacement_xyz=shift, phase_multiplier=between_ramp(shift, z, y, x))
            )
    return result


def certify_parameter_argument(value: Any) -> Any:
    for actual, expected in reversed(OBSERVATION_BINDINGS):
        if (
            isinstance(actual, np.ndarray)
            and isinstance(value, np.ndarray)
            and np.shares_memory(actual, value)
        ):
            # Binding a prediction is not an accuracy assertion. Check the
            # full returned field before consuming any view, and propagate
            # the independent centers (never the returned numerical values).
            certified_close(actual, expected)
            addresses = {
                actual.ctypes.data
                + sum(i * s for i, s in zip(index, actual.strides, strict=True)): index
                for index in np.ndindex(actual.shape)
            }
            result = disc_empty(value.shape, dtype=expected.dtype)
            for index in np.ndindex(value.shape):
                address = value.ctypes.data + sum(
                    i * s for i, s in zip(index, value.strides, strict=True)
                )
                result[index] = expected[addresses[address]]
            return result
    return as_disc(value)


def observe_public(name: str, function: Any) -> Any:
    def call(*args: Any, **kwargs: Any) -> Any:
        model = None
        prediction_kwargs = kwargs.copy()
        if name == "reconstruct_known":
            # A failed comparison of an already returned estimate is a test
            # failure. It must not be swallowed as unavailable prediction for
            # an invalid-input call, nor manufacture a public rejection.
            for key in ["carriers_cyc_um", "modulation"]:
                if key in kwargs:
                    prediction_kwargs[key] = certify_parameter_argument(kwargs[key])
        try:
            model = predict_public(name, args, prediction_kwargs)
        except (
            ValueError,
            TypeError,
            IndexError,
            AssertionError,
            OverflowError,
            ZeroDivisionError,
        ) as error:
            # Invalid-input tests must still observe the real public rejection.
            # A successful numerical result without a certificate cannot pass close.
            CERTIFICATES.append(
                dict(kind="unavailable", entry=name, reason=f"{type(error).__name__}: {error}")
            )
        actual = function(*args, **kwargs)
        if model is not None:
            expected = (
                vars(model) if hasattr(model, "__dict__") and not isinstance(model, Disc) else model
            )
            bind_observation(actual, expected)
            if name in {
                "prepare_acquisition_bands",
                "prepare_bands",
                "declare_otf",
                "prepare_bead_otf",
            }:
                snapshot = {
                    k: getattr(actual, k).copy()
                    for k in ["quadratures", "noise_variance_factors"]
                    if hasattr(actual, k)
                }
                PUBLIC_MODELS[id(actual)] = (actual, model, snapshot)
                if name == "prepare_bead_otf":
                    PUBLIC_MODELS[id(actual.transfer)] = (
                        actual.transfer,
                        vars(model)["transfer"],
                        {},
                    )
            if name == "reconstruct_known":
                bind_observation(
                    dict(actual.resolved_settings),
                    {"effective_wiener": getattr(model, "effective_wiener", ())},
                )
            if (hasattr(actual, "trace") or hasattr(actual, "mode_trace")) and hasattr(
                model, "numeric_events"
            ):
                trace = getattr(actual, "trace", getattr(actual, "mode_trace", ()))
                for kind, expectations in vars(model)["numeric_events"].items():
                    observed = [dict(e.details) for e in trace if e.kind == kind]
                    # Original PreparedBands unchanged calls have no mode_trace.
                    if name == "reconstruct_known" and not trace:
                        continue
                    for a, e in zip(observed, expectations, strict=True):
                        bind_observation(a, e)
        assert_complete_record(actual, name, args, kwargs)
        return actual

    return call


def certified_close(actual: Any, expected: Any, *, proof: Any = None) -> None:
    budgets = []
    if isinstance(expected, Disc):
        budgets.append((float(np.max(expected.observer)), float(np.max(expected.backend))))
    for observed, predicted in OBSERVATION_BINDINGS:
        related = actual is observed or proof is observed
        if isinstance(actual, np.ndarray) and isinstance(observed, np.ndarray):
            related = related or np.shares_memory(actual, observed)
        if related:
            budgets.append((float(np.max(predicted.observer)), float(np.max(predicted.backend))))
    if isinstance(actual, (list, tuple)):
        for value in actual:
            for observed, predicted in OBSERVATION_BINDINGS:
                if value is observed:
                    budgets.append(
                        (float(np.max(predicted.observer)), float(np.max(predicted.backend)))
                    )
    if not budgets:
        raise CertificateError("comparison has no case-level independent uncertainty certificate")
    observer = max(x[0] for x in budgets)
    backend = max(x[1] for x in budgets)
    # Account for the independently evaluated reference as well as the frozen
    # public-chain prediction; no budget is selected from output values.
    reference = float(np.max(expected.observer)) if isinstance(expected, Disc) else 0.0
    bound = np.nextafter(observer + backend + reference, np.inf)
    CERTIFICATES.append(
        dict(
            kind="comparison",
            shape=list(np.shape(expected)),
            observer=observer,
            conditional_backend=backend,
            bound=bound,
        )
    )
    np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), rtol=0, atol=bound)


def decision_greater(left: Any, right: Any, label: str) -> bool:
    difference = as_disc(left) - as_disc(right)
    gap = float(abs(np.asarray(difference)))
    error = float(difference.error)
    resolved = gap > error or (gap == error == 0)
    CERTIFICATES.append(dict(kind="decision", label=label, gap=gap, error=error, resolved=resolved))
    if not resolved:
        raise CertificateError(f"unresolved strict decision: {label}, gap={gap}, error={error}")
    return bool(np.asarray(left) > np.asarray(right))


def threshold_survives(value: Any, *, choices: Any = None) -> bool:
    difference = as_disc(value) - as_disc(0.006)
    gap, error = float(abs(np.asarray(difference))), float(difference.error)
    if gap <= error and error > 0 and choices is not None:
        # An enclosure crossing the unchanged strict threshold permits both
        # outcomes. Enumerating them is a conditional sensitivity proof, not
        # an equality certificate or a tolerance on the production predicate.
        choice = next(choices)
        assert type(choice) is bool
        CERTIFICATES.append(
            dict(kind="threshold-alternative", gap=gap, error=error, survives=choice)
        )
        return choice
    return decision_greater(value, 0.006, "transfer-threshold")


def parameter_model(
    bands: Any, table: Any, *, initial_carriers_cyc_um: Any, **settings: Any
) -> Any:
    from types import SimpleNamespace

    tcount, dcount, _, z, _, _ = bands.input_shape
    orders = bands.noise_variance_factors.shape[-1]
    raw = disc_empty((tcount, dcount, orders - 1), dtype=complex)
    adjusted = disc_empty(raw.shape, dtype=complex)
    carriers = disc_empty((tcount, dcount, 2))
    numeric_events: dict[str, list[Any]] = {
        "evaluation": [],
        "bracket": [],
        "parabola": [],
        "coarse": [],
        "adjustment": [],
        "cumulative-product": [],
    }
    builds = []
    sample_at = local_samples(table)
    op = {k: settings[k] for k in optics()}
    for t, d in np.ndindex(tcount, dcount):
        search = settings.get("search_carriers", True) and (
            t == 0 or not settings.get("use_time0_carriers", True)
        )
        if search:
            result = finite_search(bands, table, initial_carriers_cyc_um[d], t=t, d=d, **op)
            carriers[t, d] = result["carrier"]
            raw[t, d] = result["raw"]
            build_offset = len(builds)
            builds.extend(result["builds"])
            numeric_events["coarse"].append(
                dict(
                    carrier_cyc_um=result["coarse_carrier"],
                    correlation_power=result["coarse_power"],
                )
            )
            for event in result["trace"]:
                kind = event["kind"]
                if kind == "bracket":
                    numeric_events[kind].append(
                        dict(
                            zip(
                                ["x1", "amp1", "x2", "amp2", "x3", "amp3"],
                                event["values"],
                                strict=True,
                            )
                        )
                    )
                elif kind == "evaluation":
                    numeric_events[kind].append(
                        event | {"overlap_index": build_offset + event["overlap_index"]}
                    )
                else:
                    numeric_events[kind].append(event)
        else:
            carrier = (
                carriers[0, d]
                if settings.get("search_carriers", True) and t > 0
                else as_disc(initial_carriers_cyc_um[d])
            )
            carriers[t, d] = carrier
            for b in range(1, orders):
                built = overlaps(
                    bands,
                    table,
                    carrier,
                    (0, b),
                    t,
                    d,
                    omit=settings.get("omit_kz0", False),
                    sampler=sample_at,
                    **op,
                )
                fit = regression(built["spatial"], carrier, (0, b), bands.dxy_um)
                builds.append(built)
                raw[t, d, b - 1] = fit["forward"]
                numeric_events["evaluation"].append(
                    dict(
                        stage="known",
                        orders=(0, b),
                        overlap_index=len(builds) - 1,
                        remake_overlaps=True,
                        angle_rad=None,
                        magnitude_cyc_um=None,
                        objective=None,
                        carrier_cyc_um=carrier,
                        **fit,
                    )
                )
        factors = raw[t, d].copy()
        if z == 1:
            for b in range(1, orders - 1):
                previous = factors[b - 1].copy()
                factors[b] *= previous
                numeric_events["cumulative-product"].append(
                    dict(
                        direct_forward=raw[t, d, b],
                        previous_cumulative=previous,
                        product=factors[b],
                    )
                )
        for b in range(orders - 1):
            entering = factors[b].copy()
            floors = settings.get("amplitude_floors")
            if floors is not None and abs(factors[b]) < floors[b]:
                magnitude = abs(factors[b])
                if magnitude.error == 0 and magnitude == 0:
                    raise CertificateError("selected amplitude floor on exact zero")
                factors[b] *= floors[b] / magnitude
            after = factors[b].copy()
            if not settings.get("fit_all_phases", True):
                phase = np.arctan2(factors[0].imag, factors[0].real)
                if b > 0:
                    factors[b] = abs(factors[b]) * np.exp(1j * (b + 1) * phase)
            numeric_events["adjustment"].append(
                dict(raw_forward=entering, after_floor=after, final=factors[b])
            )
        adjusted[t, d] = factors
    return SimpleNamespace(
        carriers_cyc_um=carriers,
        raw_modulation=raw,
        modulation=adjusted,
        numeric_events=numeric_events,
        overlaps=builds,
    )


def symbolic_correlation(
    reference: Any, moving: Any, exponent: float, pitch: float, rd: float, highpass: float
) -> Any:
    ref, mov = as_disc(reference), as_disc(moving)
    shape = ref.shape
    z, y, x = shape
    if highpass > 0:
        return None
    uniform = bool(
        np.all(np.asarray(ref) == np.asarray(ref).flat[0])
        and np.all(np.asarray(mov) == np.asarray(mov).flat[0])
    )
    nonzero_ref = np.argwhere(np.asarray(ref) != 0)
    nonzero_mov = np.argwhere(np.asarray(mov) != 0)
    impulse = len(nonzero_ref) == len(nonzero_mov) == 1 and rd > _plain_hypot(
        0.5 / pitch, 0.5 / pitch
    )
    if not uniform and not impulse:
        return None
    cross = disc_zeros((z, y, x // 2 + 1), dtype=complex)
    correlation = disc_zeros(shape)
    if uniform:
        amplitude = fractional_cross(np.conj(np.sum(ref)) * np.sum(mov), exponent)
        if abs(np.asarray(amplitude)) == 0:
            return None  # allzero initialized-center is a separate exact control
        cross[0, 0, 0] = amplitude
        correlation[:] = amplitude.real
        best = (0, 0, 0)
        statuses = (
            "zero-curvature",
            "zero-curvature",
            "not-fitted" if z == 1 else "zero-curvature",
        )
        offsets = as_disc(np.zeros(3))
        wrapped = as_disc(np.zeros(3))
    else:
        source = tuple(nonzero_ref[0])
        target = tuple(nonzero_mov[0])
        shift = tuple((target[i] - source[i]) % shape[i] for i in range(3))
        amplitude = fractional_cross(np.conj(ref[source]) * mov[target], exponent)
        for h, i, j in np.ndindex(cross.shape):
            cross[h, i, j] = amplitude * np.exp(
                -2j * certified_pi() * (h * shift[0] / z + i * shift[1] / y + j * shift[2] / x)
            )
        correlation[shift] = (x * y * z) * amplitude.real
        best = shift
        statuses = ("fitted", "fitted", "not-fitted" if z == 1 else "fitted")
        offsets = as_disc(np.zeros(3))
        wrapped = as_disc(np.array(shift[::-1], dtype=float))
        for i, n in enumerate([x, y, z]):
            if wrapped[i] > n // 2:
                wrapped[i] -= n
        # Independent exact translation identity fixes integer peak/even
        # neighbor symmetry. It is not a nearly-zero curvature tolerance.
        height = abs(float(np.asarray(correlation[shift])))
        ra, ma = abs(complex(np.asarray(ref[source]))), abs(complex(np.asarray(mov[target])))
        er = gamma(8 * sum(shape)) * ra
        em = gamma(8 * sum(shape)) * ma
        ec = ra * em + ma * er + er * em + gamma(8) * ra * ma
        assert ra * ma > ec
        ef = ec * (ra * ma - ec) ** (exponent - 1) + gamma(12) * (ra * ma) ** exponent
        cross.backend += ef
        complete = full(cross, x)
        co = float(np.sum(complete.observer))
        cb = float(np.sum(complete.backend)) + gamma(8 * sum(shape)) * float(
            np.sum(abs(np.asarray(complete)))
        )
        correlation.observer += co
        correlation.backend += cb
        uncertainty = float(correlation[shift].error)
        assert height > 2 * uncertainty
        denominator = 2 * height - 4 * uncertainty
        for axis, native_n in enumerate([x, y, z]):
            # Equality at the strict half-wrap boundary uses the independently
            # proved periodic neighbor symmetry. Else propagate regular offset
            # uncertainty, including into the subsequent cubic fit.
            if native_n > 1 and best[2 - axis] != native_n // 2:
                offsets.observer[axis] = co / denominator
                offsets.backend[axis] = cb / denominator
                wrapped.observer[axis] = co / denominator
                wrapped.backend[axis] = cb / denominator
        CERTIFICATES.append(
            dict(
                kind="symbolic-peak",
                gap=height,
                error=uncertainty,
                proof=(
                    "full-spectrum singleton translation; exact periodic neighbors "
                    "and strict half wrap"
                ),
            )
        )
    neighbors = []
    for axis, n in [(2, x), (1, y), (0, z)]:
        row = []
        for delta in [-1, 0, 1]:
            index = list(best)
            index[axis] = (index[axis] + delta) % n
            row.append(correlation[tuple(index)])
        neighbors.append(np.stack(row))
    return dict(
        cross_spectrum=cross,
        correlation=correlation,
        absolute_correlation=abs(correlation),
        integer_peak_xyz=best[::-1],
        neighbors_xyz=np.stack(neighbors),
        offsets_xyz=offsets,
        offset_status_xyz=statuses,
        wrapped_displacement_xyz=wrapped,
    )


ACQUISITION_SETTING_KEYS = tuple(
    [
        "acquisition_mode",
        "dxy_um",
        "dz_um",
        "norders",
        "background",
        "lateral_zoom",
        "axial_zoom",
        "phases_rad",
        "phase_steps_rad",
        "edge_pixels",
        "equalize",
        "equalize_z",
        "equalize_time",
        "combine_off_orders",
        "storage_order",
        "drift_between",
        "drift_within",
        "fit_drift",
        "adjust_phases",
        "drift_filter_fraction",
        "wavelength_nm",
        "numerical_aperture",
        "immersion_index",
        "linespacing_um",
        "phase_start_angle_rad",
        "negative_angle_step",
        "n_off_exposures",
    ]
)
KNOWN_SETTING_KEYS = tuple(
    [
        "wavelength_nm",
        "numerical_aperture",
        "immersion_index",
        "wiener",
        "suppress_singularities",
        "suppression_radius_bins",
        "dampen_order0",
        "omit_order0",
        "omit_kz0",
        "output_taper",
        "dxy_um",
        "dz_um",
        "lateral_zoom",
        "axial_zoom",
        "input_scale",
    ]
)
KNOWN_EXTRA_KEYS = tuple(
    [
        "acquisition_mode",
        "wiener_increment",
        "effective_wiener",
        "power_taper_exponent",
        "precise_taper",
        "filter_overlaps",
        "explode_factor",
    ]
)


def returned_arrays(value: Any, path: str = "result") -> list[Any]:
    arrays = []
    if isinstance(value, np.ndarray):
        return [(path, value)]
    names = public_record_fields(value)
    if names:
        for name in names:
            arrays.extend(returned_arrays(getattr(value, name), f"{path}.{name}"))
    elif isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            arrays.extend(returned_arrays(item, f"{path}[{i}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            arrays.extend(returned_arrays(item, f"{path}.{key}"))
    return arrays


def assert_frozen_value(value: Any, field: str) -> None:
    clone = copy(value)
    original = getattr(value, field)
    if type(original) is tuple:
        replacement = (*original, ("changed", None))
    else:
        replacement = original + 1 if type(original) is int else original + "-changed"
    try:
        setattr(clone, field, replacement)
    except (AttributeError, TypeError):
        assert getattr(clone, field) == original
        return
    raise AssertionError(f"{type(value).__name__}.{field} is not frozen")


def assert_complete_record(result: Any, entry: str, args: Any, kwargs: Any) -> None:
    if entry not in {
        "prepare_acquisition_bands",
        "reconstruct_known",
        "reinterpret_2d_planes",
        "estimate_parameters",
        "prepare_bead_otf",
    }:
        return
    public_types = {
        "prepare_acquisition_bands": "AcquisitionBands",
        "reconstruct_known": "KnownReconstruction",
        "reinterpret_2d_planes": "TwoDPlaneInputs",
        "estimate_parameters": "EstimatedParameters",
        "prepare_bead_otf": "PreparedOtf",
    }
    assert isinstance(result, api(public_types[entry]))
    arrays = returned_arrays(result)
    inputs = returned_arrays(args, "args") + returned_arrays(kwargs, "kwargs")
    for i, (name, array) in enumerate(arrays):
        assert array.flags.owndata, name
        assert np.isfinite(array).all(), name
        writable = entry == "prepare_acquisition_bands" and name in {
            "result.quadratures",
            "result.noise_variance_factors",
        }
        assert array.flags.writeable is writable, name
        assert all(not np.shares_memory(array, original) for _, original in inputs), name
        for other_name, other in arrays[i + 1 :]:
            assert not np.shares_memory(array, other), (name, other_name)
    if entry == "prepare_bead_otf":
        p, z, y, x = args[0].shape
        for field, shape in {
            "center_pixels_xyz": (3,),
            "background_counts": (z, p),
            "phase_angles_rad": (p,),
            "quadratures": (p, x // 2 + 1, z),
            "normalization_factors": (p,),
            "quadrature_angles_rad": ((p - 1) // 2,),
        }.items():
            array = getattr(result, field)
            assert array.shape == shape, field
            assert array.dtype == (np.complex128 if field == "quadratures" else np.float64)
        assert result.transfer.samples.shape == ((p + 1) // 2, x // 2 + 1, z)
        assert result.transfer.samples.dtype == np.complex128
        assert result.transfer.layout == "radial"
        assert_frozen_value(result, "resolved_settings")
        assert all(immutable_setting(value) for _, value in result.resolved_settings)
        return
    assert type(result.source_revision) is str and result.source_revision == "SVN307"
    assert type(result.reference_sha256) is tuple
    assert all(
        type(pair) is tuple and len(pair) == 2 and all(type(v) is str for v in pair)
        for pair in result.reference_sha256
    )
    assert_frozen_value(result, "source_revision")
    if entry == "reinterpret_2d_planes":
        assert result.reference_sha256 == SOURCE10
        t, d, p, z, y, x = result.original_shape
        assert result.original_shape == args[0].shape
        assert result.images.shape == (t * z, d, p, 1, y, x)
        assert result.images.dtype == args[0].dtype
        for field in ["off_exposures", "exposure_background"]:
            original = kwargs.get(field)
            returned = getattr(result, field)
            assert (returned is None) == (original is None)
            if original is not None:
                trailing = original.shape[4:] if field == "off_exposures" else ()
                assert returned.shape == (t * z, d, p, 1, *trailing)
                assert returned.dtype == (
                    original.dtype if field == "off_exposures" else np.float64
                )
        assert result.source_direction_z.shape == (z, d, 2)
        assert result.source_direction_z.dtype == np.int64
        assert type(result.original_shape) is tuple and all(
            type(n) is int for n in result.original_shape
        )
        assert type(result.storage_order) is str
        assert result.storage_order == kwargs.get("storage_order", "direction-major")
        return
    if entry == "prepare_acquisition_bands":
        assert tuple(k for k, _ in result.resolved_settings) == ACQUISITION_SETTING_KEYS
        defaults = (
            dict(
                flatfield_slope=None,
                exposure_background=None,
                phases_rad=None,
                phase_steps_rad=None,
                edge_pixels=10,
                equalize=True,
                equalize_z=False,
                equalize_time=False,
                off_exposures=None,
                combine_off_orders=None,
                storage_order="direction-major",
                drift_between=False,
                drift_within=False,
                fit_drift=False,
                adjust_phases=False,
                drift_filter_fraction=0.0,
                wavelength_nm=None,
                numerical_aperture=None,
                immersion_index=None,
                header_timestamps=None,
                header_phases_rad=None,
                linespacing_um=None,
                phase_start_angle_rad=1.57193,
                negative_angle_step=False,
            )
            | kwargs
        )
        n = 0 if defaults["off_exposures"] is None else defaults["off_exposures"].shape[4]
        defaults["n_off_exposures"] = n
        expected_settings = tuple(
            (key, canonical_setting(key, defaults[key])) for key in ACQUISITION_SETTING_KEYS
        )
        assert result.resolved_settings == expected_settings
        assert all(
            type(value) is type(expected)
            for (_, value), (_, expected) in zip(
                result.resolved_settings, expected_settings, strict=True
            )
        )
        assert result.reference_sha256 == SOURCE10
        t, d, p, z, y, x = result.input_shape
        o = (result.quadratures.shape[2] + 1) // 2
        shapes = {
            "quadratures": (t, d, 2 * o - 1, z, y, x // 2 + 1),
            "noise_variance_factors": (t, d, o),
            "separation_matrices": (t, d, z, 2 * o - 1, p),
            "phase_angles_rad": (t, d, z, p),
            "frame_sums": (t, d, p, z),
            "equalization_gains": (t, d, p, z),
            "off_frame_sums": (t, d, p, z),
            "off_equalization_gains": (t, d, p, z),
            "off_quadratures": (t, d, 2 * o - 1, z, y, x // 2 + 1),
            "background_after": (y, x),
            "slope_after": (y, x),
            "between_displacements_pixels": (t, d, 3),
            "exposure_displacements_pixels": (t, d, z, p, 2),
        }
        for field, shape in shapes.items():
            value = getattr(result, field)
            if field.startswith("off_"):
                assert (value is None) == (n == 0)
            else:
                assert isinstance(value, np.ndarray)
            if value is not None:
                assert value.shape == shape, field
                assert value.dtype == (np.complex128 if "quadratures" in field else np.float64), (
                    field
                )
        if defaults["header_timestamps"] is None:
            assert result.header_timestamps_after is None
        else:
            assert result.header_timestamps_after.shape == (t * d * p * z * (n + 1),)
            assert result.header_timestamps_after.dtype == np.float64
        assert all(type(v) is int for v in result.input_shape)
        assert type(result.phase_policies) is tuple
        for time in result.phase_policies:
            assert type(time) is tuple
            for direction in time:
                assert type(direction) is tuple
                assert all(
                    type(policy) is str and policy in {"uniform", "steps", "supplied", "drift"}
                    for policy in direction
                )
        assert type(result.sentinel_frames) is tuple
        assert all(
            type(event) is tuple and len(event) == 5 and all(type(v) is int for v in event)
            for event in result.sentinel_frames
        )
        assert_mode_trace_complete(result, result.trace, result.input_shape, o)
        designs = [
            (e.time_index, e.direction_index, e.z_index)
            for e in result.trace
            if e.kind == "phase-design"
        ]
        assert designs == list(np.ndindex(t, d, z))
        if defaults["drift_within"]:
            correction_indices = [
                (e.time_index, e.direction_index, e.z_index, e.phase_index)
                for e in result.trace
                if e.kind == "exposure-correction"
            ]
            assert correction_indices == list(np.ndindex(t, d, z, p))
        else:
            assert not any(e.kind in {"cubic-fit", "exposure-correction"} for e in result.trace)
        selected_orders = defaults["combine_off_orders"]
        selected_orders = (
            []
            if selected_orders is None
            else [m for m, flag in enumerate(selected_orders) if flag > 0]
        )
        assert [
            (e.time_index, e.direction_index, dict(e.details)["call_z"], dict(e.details)["order"])
            for e in result.trace
            if e.kind == "off-combination"
        ] == [(*index, m) for index in np.ndindex(t, d, z) for m in selected_orders]
        for ti in range(t):
            current = [e.kind for e in result.trace if e.time_index == ti]
            if "between-build" in current:
                assert current.index("between-build") < current.index("phase-design")
    elif entry == "estimate_parameters":
        assert_estimation_schema(result, args[0], kwargs)
        assert result.reference_sha256 == SOURCE6
        assert type(result.resolved_settings) is tuple
        keys = tuple(k for k, _ in result.resolved_settings)
        assert keys in {
            ESTIMATE_KEYS,
            (*ESTIMATE_KEYS, "acquisition_mode", "acquisition_reference_sha256"),
        }
    else:
        keys = tuple(k for k, _ in result.resolved_settings)
        assert keys in {KNOWN_SETTING_KEYS, (*KNOWN_SETTING_KEYS, *KNOWN_EXTRA_KEYS)}
        assert_mode_trace_complete(result, result.mode_trace, None, None)
        assert_known_settings(result, args[0], kwargs)
    assert type(result.resolved_settings) is tuple
    for key, value in result.resolved_settings:
        assert type(key) is str
        assert immutable_setting(value)


def immutable_setting(value: Any) -> bool:
    if value is None or type(value) in {str, bool, int, float, complex}:
        return True
    return type(value) is tuple and all(immutable_setting(item) for item in value)


def assert_mode_trace_complete(record: Any, trace: Any, shape: Any, orders: Any) -> None:
    assert type(trace) is tuple
    complex_fields = {"fourier", "cross_spectrum", "phase_multiplier", "quadratures_after"}
    real_array_fields = {
        "centers",
        "correlation",
        "absolute_correlation",
        "neighbors_xyz",
        "offsets_xyz",
        "wrapped_displacement_xyz",
        "sample_timestamps_before",
        "sample_timestamps_after",
        "evaluation_timestamps_before",
        "evaluation_timestamps_after",
        "sample_displacements_xy",
        "matrix",
        "coefficients",
        "evaluated_xy",
        "displacement_xy",
        "phases_rad",
        "separation_matrix",
        "noise_variance_factors",
        "displacement_xyz",
        "carrier_angles_rad",
        "boundary_angles_rad",
        "object_frequency_xy",
        "next_boundaries",
    }
    for event in trace:
        assert_frozen_value(event, "kind")
        assert type(event.kind) is str
        assert type(event.time_index) is int and type(event.direction_index) is int
        assert type(event.z_index) in {int, type(None)} and type(event.phase_index) in {
            int,
            type(None),
        }
        assert type(event.details) is tuple
        assert all(
            type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str
            for pair in event.details
        )
        assert tuple(key for key, _ in event.details) == tuple(MODE_KEYS[event.kind].split())
        data = dict(event.details)
        if event.kind == "wiener-step":
            assert event.direction_index == 0
            assert event.z_index is event.phase_index is None
        for key, value in data.items():
            if key in complex_fields or key in real_array_fields:
                assert isinstance(value, np.ndarray), (event.kind, key)
                assert value.dtype == np.dtype(complex if key in complex_fields else float)
                assert np.isfinite(value).all()
            elif key == "scope":
                assert type(value) is str
                if event.kind == "drift-correlation":
                    assert value in {"between", "within"}
            elif key == "policy":
                assert type(value) is str and value in {"uniform", "steps", "supplied", "drift"}
            elif key in {"offset_status_xyz"}:
                assert (
                    type(value) is tuple and len(value) == 3 and all(type(s) is str for s in value)
                )
            elif key in {"integer_peak_xyz"}:
                assert (
                    type(value) is tuple and len(value) == 3 and all(type(n) is int for n in value)
                )
            elif key in {
                "subz",
                "first_z",
                "unused_axial_cutoff",
                "moving_index",
                "call_z",
                "affected_z",
                "order",
                "cutoff_integer",
                "inside_count",
                "outside_count",
                "selected_direction",
            }:
                assert type(value) is int
            elif key == "both_zero_replaced":
                assert type(value) is bool
            else:
                assert type(value) is float, (event.kind, key, type(value))
                assert np.isfinite(value)
        if event.kind == "drift-correlation":
            axial_unfitted = data["scope"] == "within" or data["correlation"].shape[0] == 1
            statuses = {"zero-curvature", "outside-range", "fitted"}
            assert all(status in statuses for status in data["offset_status_xyz"][:2])
            assert data["offset_status_xyz"][2] in ({"not-fitted"} if axial_unfitted else statuses)
        if event.kind == "off-combination":
            assert data["affected_z"] == 0
        if shape is not None:
            _, d, p, z, y, x = shape
            hx = x // 2 + 1
            if event.kind == "between-build":
                s = data["subz"]
                assert data["centers"].shape == (d, s, y, x)
                assert data["fourier"].shape == (d, s, y, hx)
            elif event.kind == "drift-correlation":
                s = max(z // 2, 1) if data["scope"] == "between" else 1
                assert data["cross_spectrum"].shape == (s, y, hx)
                assert data["correlation"].shape == data["absolute_correlation"].shape == (s, y, x)
                assert data["neighbors_xyz"].shape == (3, 3)
                assert data["offsets_xyz"].shape == data["wrapped_displacement_xyz"].shape == (3,)
            elif event.kind == "cubic-fit":
                n = len(data["sample_timestamps_before"])
                ne = len(data["evaluation_timestamps_before"])
                assert data["matrix"].shape == (n - 1, 3)
                assert data["coefficients"].shape == (3, 2)
                assert data["sample_displacements_xy"].shape == (n, 2)
                assert data["evaluated_xy"].shape == (ne, 2)
                assert data["sample_timestamps_after"].shape == (n,)
                assert data["evaluation_timestamps_after"].shape == (ne,)
            elif event.kind == "exposure-correction":
                assert data["displacement_xy"].shape == (2,)
                assert data["phase_multiplier"].shape == (y, hx)
            elif event.kind == "phase-design":
                assert data["phases_rad"].shape == (p,)
                assert data["separation_matrix"].shape == (2 * orders - 1, p)
                assert data["noise_variance_factors"].shape == (orders,)
            elif event.kind == "off-combination":
                assert data["quadratures_after"].shape == ((1 if data["order"] == 0 else 2), y, hx)
            elif event.kind == "between-correction":
                assert data["displacement_xyz"].shape == (3,)
                assert data["phase_multiplier"].shape == (z, y, hx)
        elif event.kind == "sector-boundaries":
            d = record.carriers_cyc_um.shape[0]
            assert data["carrier_angles_rad"].shape == (d,)
            assert data["boundary_angles_rad"].shape == (2 * d,)


def canonical_setting(key: str, value: Any) -> Any:
    if value is None or type(value) in {str, bool}:
        return value
    if key == "background" and isinstance(value, np.ndarray):
        return "map"
    if isinstance(value, np.ndarray):
        conversion = int if key == "combine_off_orders" else float

        def nested(array: Any) -> Any:
            return tuple(nested(v) for v in array) if np.ndim(array) > 0 else conversion(array)

        return nested(value)
    return (
        int(value)
        if key in {"norders", "axial_zoom", "edge_pixels", "wavelength_nm", "n_off_exposures"}
        else float(value)
    )


# Imported explicitly by each owned acquisition test module. Independent probes
# export certificates; ordinary tests need no platform-specific artifact path.


@pytest.fixture(autouse=True)
def numerical_case() -> Any:
    CERTIFICATES.clear()
    PUBLIC_MODELS.clear()
    OBSERVATION_BINDINGS.clear()
    CORRELATION_AUDITS.clear()
    PREPARATION_AUDITS.clear()
    yield


def reconstruction_numeric_events(model: Any, bands: Any, settings: Any) -> Any:
    step = as_disc(settings.get("wiener_increment", 0.0)) / bands.input_shape[0]
    previous = as_disc(settings["wiener"])
    result: dict[str, list[Any]] = {"wiener-step": [], "sector-boundaries": []}
    for effective in model.effective_wiener:
        result["wiener-step"].append(dict(previous=previous, increment=step, effective=effective))
        previous = effective
        if settings.get("precise_taper", False):
            carrier = as_disc(settings["carriers_cyc_um"])
            d = carrier.shape[0]
            angles = np.arctan2(carrier[:, 1], carrier[:, 0])
            boundaries = np.concatenate(
                [
                    angles - certified_pi() / (2 * d),
                    angles - certified_pi() / (2 * d) + certified_pi(),
                ]
            )
            for j in range(2 * d):
                if boundaries[j] > pi:
                    boundaries[j] -= 2 * certified_pi()
                elif boundaries[j] < -pi:
                    boundaries[j] += 2 * certified_pi()
            result["sector-boundaries"].append(
                dict(carrier_angles_rad=angles, boundary_angles_rad=boundaries)
            )
    return result


def assert_estimation_schema(result: Any, bands: Any, settings: Any) -> None:
    defaults = (
        dict(
            search_carriers=True,
            use_time0_carriers=True,
            amplitude_floors=None,
            fit_all_phases=True,
            omit_kz0=False,
        )
        | settings
    )
    values = {key: canonical_setting(key, defaults[key]) for key in ESTIMATE_KEYS[:8]}
    for key in ESTIMATE_KEYS[8:]:
        values[key] = getattr(bands, key)
    expected = tuple((key, values[key]) for key in ESTIMATE_KEYS)
    if hasattr(bands, "acquisition_mode"):
        expected += (
            ("acquisition_mode", bands.acquisition_mode),
            ("acquisition_reference_sha256", bands.reference_sha256),
        )
    assert result.resolved_settings == expected
    assert all(
        type(value) is type(want)
        for (_, value), (_, want) in zip(result.resolved_settings, expected, strict=True)
    )
    t, d, _, z, y, x = bands.input_shape
    o = bands.noise_variance_factors.shape[-1]
    assert result.carriers_cyc_um.shape == (t, d, 2) and result.carriers_cyc_um.dtype == np.float64
    assert result.modulation.shape == result.raw_modulation.shape == (t, d, o - 1)
    assert result.modulation.dtype == result.raw_modulation.dtype == np.complex128
    assert (
        result.initial_carriers_cyc_um.shape == (d, 2)
        and result.initial_carriers_cyc_um.dtype == np.float64
    )
    assert type(result.branches) is tuple and all(
        type(row) is tuple
        and len(row) == d
        and all(type(v) is str and v in {"known", "searched", "time0-reused"} for v in row)
        for row in result.branches
    )
    schemas = {
        "coarse": (
            "overlap_index correlation_complex correlation_power integer_peak_xy "
            "x_neighbors y_neighbors x_offset y_offset x_offset_status y_offset_status "
            "peak_before_alias_xy alias_decisions peak_after_alias_xy carrier_cyc_um"
        ),
        "evaluation": (
            "stage orders overlap_index remake_overlaps angle_rad magnitude_cyc_um "
            "carrier_cyc_um SX SY cross forward reverse combined correlation objective"
        ),
        "bracket": "stage branch x1 amp1 x2 amp2 x3 amp3 strict_improvement",
        "parabola": "stage x1 y1 x2 y2 x3 y3 result status",
        "reuse": "source_time carrier_cyc_um",
        "adjustment": "order raw_forward floor floor_applied after_floor phase_replaced final",
        "cumulative-product": "order direct_forward previous_cumulative product",
    }
    offset_status = {"zero-curvature", "outside-range", "fitted"}
    event_strings = {
        "stage": {"angle", "magnitude"},
        "branch": {"initial", "positive", "negative-swap", "shift", "stop"},
        "status": {"duplicate-coordinate", "zero-curvature", "fitted"},
        "x_offset_status": offset_status,
        "y_offset_status": offset_status,
    }
    assert type(result.trace) is tuple
    assert type(result.overlaps) is tuple
    for event in result.trace:
        assert_frozen_value(event, "kind")
        assert (
            type(event.kind) is str
            and type(event.time_index) is int
            and type(event.direction_index) is int
        )
        assert type(event.details) is tuple
        assert all(
            type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str
            for pair in event.details
        )
        assert tuple(k for k, _ in event.details) == tuple(schemas[event.kind].split())
        known = event.kind == "evaluation" and dict(event.details)["stage"] == "known"
        for key, value in event.details:
            if key in {
                "correlation_complex",
                "correlation_power",
                "x_neighbors",
                "y_neighbors",
                "peak_before_alias_xy",
                "peak_after_alias_xy",
                "carrier_cyc_um",
            }:
                assert isinstance(value, np.ndarray), (event.kind, key)
                if key == "correlation_complex":
                    assert value.shape == (y, x) and value.dtype == np.complex128
                elif key == "correlation_power":
                    assert value.shape == (y, x) and value.dtype == np.float64
                else:
                    assert value.shape == ((3,) if key in {"x_neighbors", "y_neighbors"} else (2,))
                    assert value.dtype == np.float64
            elif key in event_strings:
                allowed = event_strings[key]
                if key == "stage" and event.kind == "evaluation":
                    allowed = allowed | {"final", "later-order", "known"}
                assert type(value) is str and value in allowed
            elif key in {"order", "overlap_index", "source_time"}:
                assert type(value) is int
            elif key in {
                "strict_improvement",
                "remake_overlaps",
                "floor_applied",
                "phase_replaced",
            }:
                assert type(value) is bool
            elif key in {"orders", "integer_peak_xy"}:
                assert (
                    type(value) is tuple and len(value) == 2 and all(type(v) is int for v in value)
                )
            elif key == "alias_decisions":
                assert (
                    type(value) is tuple and len(value) == 4 and all(type(v) is bool for v in value)
                )
            elif key in {
                "cross",
                "forward",
                "reverse",
                "combined",
                "raw_forward",
                "after_floor",
                "final",
                "direct_forward",
                "previous_cumulative",
                "product",
            }:
                assert type(value) is complex and np.isfinite(value)
            elif known and key in {"angle_rad", "magnitude_cyc_um", "objective"}:
                assert value is None
            elif key == "floor" and value is None:
                continue
            else:
                assert type(value) is float and np.isfinite(value), (event.kind, key)
    for index, build in enumerate(result.overlaps):
        assert_frozen_value(build, "index")
        assert type(build.index) is int and build.index == index
        assert type(build.time_index) is int and type(build.direction_index) is int
        assert type(build.purpose) is str and build.purpose in {
            "coarse",
            "refinement",
            "later-order",
            "known",
        }
        assert (
            type(build.orders) is tuple
            and len(build.orders) == 2
            and all(type(v) is int for v in build.orders)
        )
        assert build.carrier_cyc_um.shape == (2,) and build.carrier_cyc_um.dtype == np.float64
        assert build.fourier.shape == build.spatial.shape == build.written.shape == (2, z, y, x)
        assert (
            build.fourier.dtype == build.spatial.dtype == np.complex128
            and build.written.dtype == np.bool_
        )


def assert_known_settings(result: Any, bands: Any, settings: Any) -> None:
    defaults = (
        dict(
            suppress_singularities=True,
            suppression_radius_bins=10.0,
            dampen_order0=False,
            omit_order0=False,
            omit_kz0=False,
            output_taper="cosine",
            wiener_increment=0.0,
            power_taper_exponent=None,
            precise_taper=False,
            filter_overlaps=True,
            explode_factor=1.0,
        )
        | settings
    )
    values = {key: canonical_setting(key, defaults[key]) for key in KNOWN_SETTING_KEYS[:10]}
    for key in KNOWN_SETTING_KEYS[10:]:
        values[key] = getattr(bands, key)
    mode = getattr(bands, "acquisition_mode", "3d")
    values |= {
        key: canonical_setting(key, defaults[key])
        for key in KNOWN_EXTRA_KEYS
        if key not in {"acquisition_mode", "effective_wiener"}
    }
    values["acquisition_mode"] = mode
    t = bands.input_shape[0]
    w = defaults["wiener"]
    effective = []
    for _ in range(t):
        w += defaults["wiener_increment"] / t
        effective.append(float(w))
    values["effective_wiener"] = tuple(effective)
    expected = tuple((key, values[key]) for key, _ in result.resolved_settings)
    for (key, value), (_, want) in zip(result.resolved_settings, expected, strict=True):
        if key == "effective_wiener":
            certified_close(value, want)
        else:
            assert value == want, key
    assert all(
        type(value) is type(want)
        for (_, value), (_, want) in zip(result.resolved_settings, expected, strict=True)
    )
    assert result.image.dtype == np.float64 and result.filtered_quadratures.dtype == np.complex128
    assert result.filtered_quadratures.shape == bands.quadratures.shape
    assert result.image.shape == (
        t,
        bands.input_shape[3] * bands.axial_zoom,
        int(bands.input_shape[4] * bands.lateral_zoom),
        int(bands.input_shape[5] * bands.lateral_zoom),
    )
    for name in ["x_um", "y_um", "z_um"]:
        assert getattr(result, name).dtype == np.float64 and getattr(result, name).ndim == 1
    assert result.x_um.shape == (result.image.shape[-1],)
    assert result.y_um.shape == (result.image.shape[-2],)
    assert result.z_um.shape == (result.image.shape[-3],)
    d = bands.input_shape[1]
    o = (bands.quadratures.shape[2] + 1) // 2
    assert result.carriers_cyc_um.shape == (d, 2) and result.carriers_cyc_um.dtype == np.float64
    assert result.modulation.shape == (d, o - 1) and result.modulation.dtype == np.complex128
    assert result.axial_cutoffs_bins.shape == (o,) and result.axial_cutoffs_bins.dtype.kind in "iu"
    keys = tuple(k for k, _ in result.resolved_settings)
    selected = (
        hasattr(bands, "acquisition_mode")
        or defaults["wiener_increment"] != 0
        or defaults["power_taper_exponent"] is not None
        or defaults["precise_taper"]
        or not defaults["filter_overlaps"]
        or defaults["explode_factor"] != 1
    )
    if selected:
        assert keys == (*KNOWN_SETTING_KEYS, *KNOWN_EXTRA_KEYS)
    expected_kinds = []
    if keys != KNOWN_SETTING_KEYS:
        for _ in range(t):
            expected_kinds.append("wiener-step")
            if defaults["precise_taper"]:
                expected_kinds.append("sector-boundaries")
    assert [event.kind for event in result.mode_trace] == expected_kinds


def certify_unique_peak(values: Any, index: Any, label: str) -> None:
    array = np.asarray(values)
    errors = np.broadcast_to(getattr(values, "error", 0), array.shape)
    keep = np.ones(array.shape, dtype=bool)
    keep[index] = False
    if not np.any(keep):
        return
    gap = float(array[index] - np.max(array[keep]))
    error = float(errors[index] + np.max(errors[keep]))
    CERTIFICATES.append(
        dict(kind="peak-decision", label=label, gap=gap, error=error, resolved=gap > error)
    )
    if gap <= error:
        raise CertificateError(f"unresolved independent {label} peak: gap={gap}, error={error}")


def public_record_fields(value: Any) -> Any:
    # Public value records may use a frozen dataclass, named tuple or another
    # frozen implementation. Traverse fields, never class/source internals.
    if hasattr(value, "__dataclass_fields__"):
        return tuple(value.__dataclass_fields__)
    if hasattr(value, "_fields") and isinstance(value, tuple):
        return getattr(value, "_fields", ())
    if hasattr(value, "quadratures") and hasattr(value, "input_shape"):
        names = [
            "quadratures",
            "noise_variance_factors",
            "separation_matrices",
            "phase_angles_rad",
            "frame_sums",
            "equalization_gains",
            "background_after",
            "slope_after",
            "sentinel_frames",
            "input_shape",
            "input_scale",
            "dxy_um",
            "dz_um",
            "lateral_zoom",
            "axial_zoom",
            "resolved_settings",
            "source_revision",
            "reference_sha256",
        ]
        if hasattr(value, "acquisition_mode"):
            names += [
                "off_frame_sums",
                "off_equalization_gains",
                "off_quadratures",
                "between_displacements_pixels",
                "exposure_displacements_pixels",
                "header_timestamps_after",
                "trace",
                "acquisition_mode",
                "storage_order",
                "phase_policies",
            ]
        return tuple(name for name in names if hasattr(value, name))
    for marker, names in [
        (
            "normalization_factors",
            [
                "transfer",
                "center_pixels_xyz",
                "background_counts",
                "phase_angles_rad",
                "quadratures",
                "normalization_factors",
                "quadrature_angles_rad",
                "resolved_settings",
            ],
        ),
        (
            "filtered_quadratures",
            [
                "image",
                "filtered_quadratures",
                "x_um",
                "y_um",
                "z_um",
                "carriers_cyc_um",
                "modulation",
                "radial_cutoff_cyc_um",
                "axial_cutoffs_bins",
                "resolved_settings",
                "source_revision",
                "reference_sha256",
                "mode_trace",
            ],
        ),
        (
            "raw_modulation",
            [
                "carriers_cyc_um",
                "modulation",
                "raw_modulation",
                "initial_carriers_cyc_um",
                "branches",
                "overlaps",
                "trace",
                "radial_cutoff_cyc_um",
                "axial_cutoff_bins",
                "resolved_settings",
                "source_revision",
                "reference_sha256",
            ],
        ),
        (
            "source_direction_z",
            [
                "images",
                "off_exposures",
                "exposure_background",
                "source_direction_z",
                "original_shape",
                "storage_order",
                "source_revision",
                "reference_sha256",
            ],
        ),
        ("details", ["kind", "time_index", "direction_index", "z_index", "phase_index", "details"]),
        (
            "purpose",
            [
                "index",
                "time_index",
                "direction_index",
                "purpose",
                "orders",
                "carrier_cyc_um",
                "fourier",
                "spatial",
                "written",
            ],
        ),
        (
            "samples",
            [
                "samples",
                "layout",
                "dkr_cyc_um",
                "dkz_cyc_um",
                "norders",
                "source_revision",
                "reference_sha256",
            ],
        ),
    ]:
        if hasattr(value, marker):
            return tuple(name for name in names if hasattr(value, name))
    return ()


def radial_decision(value: Any, cutoff: Any, *, inclusive: bool, varying: bool, label: str) -> bool:
    if varying:
        difference = as_disc(value) - as_disc(cutoff)
        gap = float(abs(np.asarray(difference)))
        error = float(difference.error)
        CERTIFICATES.append(
            dict(kind="support-decision", label=label, gap=gap, error=error, resolved=gap > error)
        )
        if gap <= error:
            raise CertificateError(f"unresolved {label} interval: gap={gap}, error={error}")
    return (
        bool(np.asarray(value) <= np.asarray(cutoff))
        if inclusive
        else bool(np.asarray(value) < np.asarray(cutoff))
    )


def positive_quotient(numerator: Any, denominator: Any, lower: float) -> Any:
    numerator, denominator = as_disc(numerator), as_disc(denominator)
    if lower <= 0:
        raise CertificateError("Wiener denominator lower bound is unresolved")
    value = np.asarray(numerator) / np.asarray(denominator)
    oe = (numerator.observer + abs(value) * denominator.observer) / lower
    total = (numerator.error + abs(value) * denominator.error) / lower
    rounding = gamma(8) * abs(value)
    CERTIFICATES.append(
        dict(
            kind="filter-divisor",
            lower=lower,
            observer=float(np.max(oe)),
            conditional_backend=float(np.max(total - oe + rounding)),
        )
    )
    return Disc(value, oe + rounding, np.maximum(total - oe, 0) + rounding)
