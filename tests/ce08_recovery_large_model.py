"""Independent finite D3 physical acquisition, fitting and native assembly.

Only three dimension-generic, immutable A-authored utilities are reused:
compensated finite_sum, signed lift and real-quadrature half-space read_band.
No product imports, Fourier transform backend or production forward helper.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ce08_finite_math import Array, finite_sum, read_band, signed

ROOT = Path(__file__).parent
SPEC = ROOT / "data/ce08-large-recovery-v1.json"


def registration() -> dict[str, Any]:
    return json.loads(SPEC.read_text())


def coordinates(output: bool) -> tuple[Array, Array, Array]:
    n, step = (48, 0.5) if output else (24, 1.0)
    return np.arange(n) * step - 12, np.arange(n) * step - 12, np.arange(8) - 4


def carriers(p: dict[str, Any]) -> Array:
    b = 1 / (2 * p["carrier"]["linespacing_um"])
    return b * np.array([(math.cos(t), math.sin(t)) for t in p["carrier"]["angles_rad"]])


def source_modes(p: dict[str, Any]) -> list[tuple[tuple[int, int, int], complex]]:
    result = [((0, 0, 0), complex(p["source"]["density_dc"]))]
    for x, y, z, re, im in p["source"]["positive_modes_kxyz_real_imag"]:
        k, c = (x, y, z), complex(re, im)
        result.extend(((k, c), (tuple(-j for j in k), c.conjugate())))
    return result


def wave(f: tuple[float, float, float], output: bool) -> Array:
    x, y, z = coordinates(output)
    return np.exp(
        2j * np.pi * (f[0] * x[None, None, :] + f[1] * y[None, :, None] + f[2] * z[:, None, None])
    )


def truth(p: dict[str, Any]) -> Array:
    return np.asarray(
        np.real(sum(c * wave((k[0] / 24, k[1] / 24, k[2] / 8), True) for k, c in source_modes(p))),
        dtype=float,
    )


def project(image: Array, p: dict[str, Any]) -> Array:
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]
    return np.array(
        [np.mean(image * np.conj(wave((k[0] / 24, k[1] / 24, k[2] / 8), True))) for k in keys]
    )


def transfer_table(p: dict[str, Any]) -> Array:
    h = np.zeros(p["transfer"]["shape_ORK"], complex)
    hz = np.array([1, 0.25 + 0.125j, 0.0625, 0, 0, 0, 0.0625, 0.25 - 0.125j])
    for m, r, z in np.ndindex(h.shape):
        v = r / 12
        radial = 2 * (math.acos(v) - v * math.sqrt(1 - v * v)) / math.pi if v < 1 else 0
        h[m, r, z] = float(np.float32(radial)) * hz[z % 8]
    return h.astype(np.complex64).astype(np.complex128)


def sample(h: Array, m: int, x: float, y: float, z: int) -> complex:
    """Literal radial vertices, dkr=1/24 and native/table dkz=1/8."""
    u = math.hypot(x, y) / (1 / 24)
    t = z if z >= 0 else z + h.shape[2]
    i, j = math.floor(u), math.floor(t)
    ar, az = u - i, t - j
    j1 = 0 if j == h.shape[2] - 1 else j + 1
    offsets = [
        i * h.shape[2] + j,
        i * h.shape[2] + j1,
        (i + 1) * h.shape[2] + j,
        (i + 1) * h.shape[2] + j1,
    ]
    assert min(offsets) >= 0 and max(offsets) < h[m].size
    v00, v01, v10, v11 = (h[m].ravel()[o] for o in offsets)
    return complex((1 - ar) * ((1 - az) * v00 + az * v01) + ar * ((1 - az) * v10 + az * v11))


def cutoffs(p: dict[str, Any]) -> tuple[int, list[int]]:
    o = p["optics"]
    le = o["wavelength_nm"] / o["immersion_index"] / 1000
    c = math.ceil(
        (1 - math.cos(math.asin(o["numerical_aperture"] / o["immersion_index"]))) / le * 8
    )
    fit = 3 if c > 4 else c
    return fit, [3 if j >= 4 else j for j in (c, int((1 + 1 / 0.88) * c), int(1.3 * c))]


def acquisition_bounds(p: dict[str, Any]) -> dict[str, float]:
    density = sum(abs(c) for _, c in source_modes(p))
    a = np.array([complex(*v) for v in p["source"]["side_modulation_pairs"]])
    ell = 1 + 2 * sum(abs(a))
    raw = 10 + 0.4 * density * ell
    return {
        "density_abs": density,
        "illumination_abs": float(ell),
        "illumination_min": float(2 - ell),
        "raw_abs": float(raw),
        "raw_quantization_abs": float(raw * 2**-24),
        "axial_kernel_min_bound": 1 - 2 * abs(0.25 + 0.125j) - 2 * 0.0625,
    }


def acquire(p: dict[str, Any], h: Array) -> dict[str, Array]:
    """Continuous modes -> illumination shifts -> optics -> detector -> ONE cast."""
    a = np.r_[1 + 0j, [complex(*v) for v in p["source"]["side_modulation_pairs"]]]
    bounds = acquisition_bounds(p)
    assert bounds["illumination_min"] > 0 and bounds["axial_kernel_min_bound"] > 0
    assert p["source"]["reference_density"] > bounds["density_abs"]

    def detected(modes: list[tuple[tuple[int, int, int], complex]]) -> Array:
        result: Array = np.zeros((3, 5, 8, 24, 24), dtype=np.complex128)
        for d, k0 in enumerate(carriers(p)):
            for m in range(-2, 3):
                am = a[abs(m)] if m >= 0 else a[-m].conjugate()
                spatial = np.zeros((8, 24, 24), complex)
                for k, c in modes:
                    q = (k[0] / 24 - m * k0[0], k[1] / 24 - m * k0[1], k[2] / 8)
                    if math.hypot(q[0], q[1]) <= 0.5:
                        spatial += c * am * sample(h, abs(m), q[0], q[1], k[2]) * wave(q, False)
                for phase in range(5):
                    result[d, phase] += spatial * np.exp(-2j * np.pi * m * phase / 5)
        assert np.max(abs(np.imag(result))) < 1e-11
        return np.real(result)

    contrast = detected(source_modes(p))
    reference = detected([((0, 0, 0), complex(p["source"]["reference_density"]))])
    specimen = reference + contrast
    assert reference.min() > 0 and specimen.min() > 0
    exact = (10 + 0.4 * contrast)[None]
    raw = exact.astype(np.float32)
    assert np.max(abs(raw - exact)) <= bounds["raw_quantization_abs"]
    assert np.all(raw[..., -1, -1] != -1)
    return {
        "raw": raw,
        "unquantized_raw": exact,
        "truth": truth(p),
        "reference_corrected_counts": 0.8 * reference,
        "specimen_corrected_counts": 0.8 * specimen,
    }


def prepare(raw: Array) -> Array:
    """Uniform CE02 rows and alpha INCLUDING D3, no edge/equalization."""
    phases = 2 * np.pi * np.arange(5) / 5
    rows = np.stack(
        (np.ones(5), np.cos(phases), np.sin(phases), np.cos(2 * phases), np.sin(2 * phases))
    )
    bands = []
    for direction in raw[0]:
        transformed = np.stack(
            [
                finite_sum(2 * (frame.astype(float) - 10) / (24 * 24 * 8 * 4 * 3), -1)
                for frame in direction
            ]
        )
        separated = np.tensordot(rows, transformed, axes=(1, 0))[..., :13]
        separated[..., -1] = transformed[..., 12]
        bands.append(separated)
    return np.stack(bands)


def overlap(bands: Array, h: Array, k: Array, d: int, m: int, c: int) -> dict[str, Any]:
    f = np.zeros((2, 8, 24, 24), complex)
    written = np.zeros(f.shape, bool)
    for iy, ix in np.ndindex((24, 24)):
        q = np.array((signed(ix, 24) / 24, signed(iy, 24) / 24))
        if np.linalg.norm(q) > 0.5:
            continue
        for side, shift in ((0, -m * k), (1, m * k)):
            other = q + shift
            if np.linalg.norm(other) > 0.5:
                continue
            for iz in range(-c, c + 1):
                first = sample(h, 0 if side == 0 else m, float(q[0]), float(q[1]), iz)
                if abs(first) * (1 if side == 0 else 5) <= 0.006:
                    continue
                second = sample(h, m if side == 0 else 0, float(other[0]), float(other[1]), iz)
                if abs(second) * (5 if side == 0 else 1) <= 0.006:
                    continue
                value = read_band(bands, 0 if side == 0 else m, iz, signed(iy, 24), signed(ix, 24))
                f[side, iz % 8, iy, ix] = value * second / math.hypot(abs(first), abs(second))
                written[side, iz % 8, iy, ix] = True
    spatial = np.stack([finite_sum(v, +1) for v in f])
    yy, xx = np.indices((24, 24))
    higher = spatial[1] * np.exp(2j * np.pi * m * ((xx - 12) * k[0] + (yy - 12) * k[1]))
    lower = spatial[0]
    sx, sy = float(np.sum(abs(lower) ** 2)), float(np.sum(abs(higher) ** 2))
    cross = complex(np.sum(np.conj(lower) * higher))
    assert sx > 0 and sy > 0 and sx != sy
    beta = 0.5 * math.atan(2 * abs(cross) / (sx - sy))
    if beta < 0:
        beta += math.pi / 2
    return {
        "direction": d,
        "order": m,
        "fourier": f,
        "spatial": spatial,
        "written": written,
        "SX": sx,
        "SY": sy,
        "cross": cross,
        "forward": cross / sx,
        "reverse": cross.conjugate() / sy,
        "combined": 0j if cross == 0 else math.tan(beta) * cross / abs(cross),
        "correlation": math.sqrt(abs(cross) ** 2 / (sx * sy)),
    }


def powers(
    h: Array, k: Array, a: Array, d: int, m: int, q: Array, z: int
) -> tuple[float, list[tuple[int, int, float]]]:
    """Self inclusive, ALL other signed directions strict; g=1 throughout."""
    obj = q + m * k[d]
    terms = [(d, m, abs(a[d, m] * sample(h, m, float(q[0]), float(q[1]), z)) ** 2)]
    for e in range(3):
        for n in range(-2, 3):
            if (e, n) == (d, m):
                continue
            other = obj - n * k[e]
            if np.linalg.norm(other) < 0.5:
                terms.append(
                    (
                        e,
                        n,
                        abs(a[e, abs(n)] * sample(h, abs(n), float(other[0]), float(other[1]), z))
                        ** 2,
                    )
                )
    return sum(v for _, _, v in terms), terms


def reconstruct(
    bands: Array, h: Array, p: dict[str, Any], modulation: Array
) -> tuple[Array, Array]:
    k, a = carriers(p), np.column_stack((np.ones(3), modulation))
    _, cuts = cutoffs(p)
    filtered = bands.copy()
    for d in range(3):
        for m, c in enumerate(cuts):
            full = np.zeros((8, 24, 24), complex)
            slots = [0] if m == 0 else [2 * m - 1, 2 * m]
            for iy in range(-11, 13):
                for ix in range(-11, 13):
                    if m == 0 and ix < 0:
                        continue
                    hx, hy = abs(ix), (-iy if ix < 0 else iy) % 24
                    q = np.array((ix / 24, iy / 24))
                    for iz in range(-c, c + 1):
                        hz = (-iz if ix < 0 else iz) % 8
                        if np.linalg.norm(q) > 0.5:
                            filtered[d, slots, iz % 8, hy, hx] = 0
                            continue
                        power, _ = powers(h, k, a, d, m, q, iz)
                        scale = np.conj(a[d, m] * sample(h, m, float(q[0]), float(q[1]), iz)) / (
                            power + p["filtering"]["wiener"] ** 2
                        )
                        value = read_band(bands[d], m, iz, iy, ix) * scale
                        if m == 0:
                            filtered[d, 0, hz, hy, hx] = value
                        else:
                            full[iz % 8, iy % 24, ix % 24] = value
                    filtered[d, slots, c + 1 : 8 - c, hy, hx] = 0
            if m:
                for iz in range(-c, c + 1):
                    for iy in range(-11, 13):
                        for ix in range(13):
                            pos = full[iz % 8, iy % 24, ix]
                            neg = np.conj(full[-iz % 8, -iy % 24, -ix % 24])
                            filtered[d, 2 * m - 1, iz % 8, iy % 24, ix] = (pos + neg) / 2
                            filtered[d, 2 * m, iz % 8, iy % 24, ix] = (pos - neg) / (2j)
    image = np.zeros((8, 48, 48))
    x, y, _ = coordinates(True)
    for d in range(3):
        for m in range(3):
            padded = np.zeros(image.shape, complex)
            for iz, iy, ix in np.ndindex((8, 24, 24)):
                qz, qy, qx = signed(iz, 8), signed(iy, 24), signed(ix, 24)
                padded[qz % 8, qy % 48, qx % 48] = read_band(filtered[d], m, qz, qy, qx)
            spatial = finite_sum(padded, +1)
            ramp = np.exp(2j * np.pi * m * (k[d, 0] * x[None, :] + k[d, 1] * y[:, None]))
            image += np.real(spatial) if m == 0 else 2 * np.real(spatial * ramp)
    return filtered, image


def expected(p: dict[str, Any], raw: Array, h: Array) -> dict[str, Any]:
    bands = prepare(raw)
    fitcut, _ = cutoffs(p)
    builds = [
        overlap(bands[d], h, k, d, m, fitcut) for d, k in enumerate(carriers(p)) for m in (1, 2)
    ]
    modulation = np.array([v["forward"] for v in builds]).reshape(3, 2)
    filtered, image = reconstruct(bands, h, p, modulation)
    return {
        "bands": bands,
        "builds": builds,
        "modulation": modulation,
        "filtered": filtered,
        "image": image,
        "density_image": 3 * image,
    }


def conventional(raw: Array) -> Array:
    # SAME D*P exposures, direction mean as well as phase mean, fixed gain.
    native = np.mean(2 * (raw[0].astype(float) - 10), axis=(0, 1)) / 0.8
    spectrum = finite_sum(native, -1) / (24 * 24 * 8)
    output = np.zeros((8, 48, 48), complex)
    for iz, iy, ix in np.ndindex(spectrum.shape):
        output[signed(iz, 8) % 8, signed(iy, 24) % 48, signed(ix, 24) % 48] = spectrum[iz, iy, ix]
    return np.real(finite_sum(output, +1))


def physical_response(p: dict[str, Any], h: Array) -> tuple[Array, Array]:
    """Diagonal response justified for interior lattice signal modes only.

    g=1, T=1, no cutoff loss at declared kz0,+/-1, H(R)=0 eliminates
    self-inclusive/other-strict differences, native Nyquist has zero signal.
    All signed terms share the same denominator BEFORE assembly across D.
    Source origin phase follows centered physical labels on every axis.
    P*gain/(D*L²*A)=1/3; density conversion3 restores the common unit.
    """
    a = np.r_[1 + 0j, [complex(*v) for v in p["source"]["side_modulation_pairs"]]]
    powers_out = []
    for k in [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]:
        power = 0.0
        for k0 in carriers(p):
            for n in range(-2, 3):
                q = np.array((k[0] / 24, k[1] / 24)) - n * k0
                if np.linalg.norm(q) < 0.5:
                    power += abs(a[abs(n)] * sample(h, abs(n), float(q[0]), float(q[1]), k[2])) ** 2
        powers_out.append(power)
    values = np.array(powers_out)
    return values, values / (values + p["filtering"]["wiener"] ** 2)


def capture(actual_workflow_image: Array, destination: Path) -> None:
    """Later explicit observer: retain every plane/mode and signed value."""
    from ce08_recovery_large_freeze import fixture_evidence

    p = registration()
    arrays, _ = fixture_evidence(p)
    density = 3 * np.asarray(actual_workflow_image)
    arrays.update(
        actual_workflow_image=actual_workflow_image,
        actual=density,
        numerical_residual=density - arrays["expected_density_image"],
        source_residual=density - arrays["truth"],
        actual_modes=project(density, p),
        signed_actual_coefficients=np.array(
            [
                np.mean(density * np.conj(wave((k[0] / 24, k[1] / 24, k[2] / 8), True)))
                for k, _ in source_modes(p)
            ]
        ),
    )
    np.savez_compressed(destination, **arrays)
