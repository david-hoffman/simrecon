"""Independent CE08 finite acquisition, native filter and sampled assembly.

Only the public contracts supply equations. This module imports no product and
uses direct compensated exponential sums, never a production FFT/model.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]
LD = np.float64
CD = np.complex128
TAU = 2 * np.arccos(LD(-1))
REGISTRATION = Path(__file__).parent / "data/ce08-small-controls-v1.json"


def registration() -> dict[str, Any]:
    return json.loads(REGISTRATION.read_text())


def signed(index: int, length: int) -> int:
    return index if index <= length // 2 else index - length


def finite_sum(values: Array, sign: int) -> Array:
    """Compensated separable direct exponential sums, no inverse gain."""
    result = np.asarray(values, dtype=CD)
    for axis, length in enumerate(values.shape):
        phases = np.outer(np.arange(length, dtype=LD), np.arange(length, dtype=LD))
        kernel = np.exp(CD(1j) * sign * TAU * phases / length)
        columns = np.moveaxis(result, axis, 0).reshape(length, -1)
        transformed = np.empty(columns.shape, dtype=CD)
        for row in range(length):
            terms = kernel[row, :, None] * columns
            for column in range(columns.shape[1]):
                transformed[row, column] = complex(
                    math.fsum(terms[:, column].real), math.fsum(terms[:, column].imag)
                )
        moved_shape = np.moveaxis(result, axis, 0).shape
        result = np.moveaxis(transformed.reshape(moved_shape), 0, axis)
    return result


def table(p: dict[str, Any]) -> Array:
    spec = p["transfer"]
    result = np.zeros(tuple(spec["shape_ORK"]), dtype=CD)
    for m, r, z in np.ndindex(result.shape):
        qz = signed(z, result.shape[2])
        lateral = max(LD(1) - LD(r) / 4, LD(0))
        base = complex(*spec["base_complex_pairs"][m])
        result[m, r, z] = base * lateral * max(1 - LD(abs(qz)) / 8, LD(0))
        if m == 0:
            result[m, r, z] += CD(1j) * qz * lateral / 32
    # The declared table boundary is exactly complex64; all constructed values
    # are dyadic, so this cast has no data-dependent approximation.
    assert np.array_equal(result, result.astype(np.complex64).astype(CD))
    return result


def sample(h: Array, m: int, x: float, y: float, z: int) -> complex:
    """Four explicit radial vertices; increments both 1/8 and 1/4 here."""
    u = np.hypot(LD(x), LD(y)) / LD("0.125")
    t = LD(z)
    if t < 0:
        t += h.shape[2]
    i, j = int(np.floor(u)), int(np.floor(t))
    a, b = u - i, t - j
    j1 = 0 if j == h.shape[2] - 1 else j + 1
    flat = h[m].ravel()
    offsets = (
        i * h.shape[2] + j,
        i * h.shape[2] + j1,
        (i + 1) * h.shape[2] + j,
        (i + 1) * h.shape[2] + j1,
    )
    assert min(offsets) >= 0 and max(offsets) < flat.size
    v00, v01, v10, v11 = (flat[k] for k in offsets)
    return complex((1 - a) * ((1 - b) * v00 + b * v01) + a * ((1 - b) * v10 + b * v11))


def geometry(p: dict[str, Any]) -> tuple[int, int, int, float, int]:
    z, y, x = p["shape_TDPZYX"][3:]
    o = p["optics"]
    radial = min(2 * o["numerical_aperture"] / (o["wavelength_nm"] / 1000), 0.5)
    le = o["wavelength_nm"] / o["immersion_index"] / 1000
    cut = math.ceil(
        (1 - math.cos(math.asin(o["numerical_aperture"] / o["immersion_index"]))) / le * z
    )
    return z, y, x, radial, cut


def acquire(p: dict[str, Any], control: dict[str, Any]) -> dict[str, Array | float]:
    """Finite sampled object times illumination, followed by declared optics."""
    z, y, x, radial, cut = geometry(p)
    zz, yy, xx = np.indices((z, y, x), dtype=LD)
    center = (xx - x // 2, yy - y // 2, zz - z // 2)
    density = np.full((z, y, x), LD(control.get("density_dc", p["source"]["density_dc"])))
    for kx, ky, kz, re, im in p["source"]["positive_modes_kxyz_real_imag"]:
        arg = TAU * (kx * center[0] / x + ky * center[1] / y + kz * center[2] / z)
        density += 2 * np.real(CD(complex(re, im)) * np.exp(CD(1j) * arg))
    h = table(p)
    kx, ky = control["carrier_cyc_um"]
    amplitudes = [1 + 0j] + [complex(*v) for v in p["source"]["side_modulation_pairs"]]
    detected: list[Array] = []
    for m, amplitude in enumerate(amplitudes):
        illumination = amplitude * np.exp(-CD(1j) * TAU * m * (kx * center[0] + ky * center[1]))
        coefficients = finite_sum(density * illumination, -1) / (x * y * z)
        for iz, iy, ix in np.ndindex(coefficients.shape):
            qx, qy, qz = signed(ix, x) / x, signed(iy, y) / y, signed(iz, z)
            if math.hypot(qx, qy) <= radial and abs(qz) <= cut:
                coefficients[iz, iy, ix] *= sample(h, m, qx, qy, qz)
            else:
                coefficients[iz, iy, ix] = 0
        detected.append(finite_sum(coefficients, +1))
    phases = TAU * np.arange(5, dtype=LD) / 5
    signal = np.repeat(np.real(detected[0])[None], 5, axis=0)
    for m in (1, 2):
        signal += 2 * np.real(detected[m][None] * np.exp(-CD(1j) * m * phases[:, None, None, None]))
    signal *= p["source"]["detector_gain_counts_per_density"]
    exact = (
        p["preparation"]["background"]
        + p["preparation"]["exposure_background"]
        + signal / p["preparation"]["flatfield_slope"]
    )
    raw = exact.astype(np.float32)[None, None]
    quantization_bound = float(np.max(np.abs(exact))) * 2**-24
    assert np.max(np.abs(raw[0, 0].astype(LD) - exact)) <= quantization_bound
    return {
        "raw": raw,
        "unquantized": exact,
        "density": density,
        "conventional": np.mean((raw[0, 0].astype(float) - 10) * 2, axis=0),
        "quantization_bound": quantization_bound,
    }


def prepare(raw: Array, p: dict[str, Any]) -> Array:
    """Independent uniform-harmonic sums, retaining raw Nyquist slots."""
    z, y, x, _, _ = geometry(p)
    alpha = LD(1) / (x * y * z * 4)
    corrected = alpha * p["preparation"]["flatfield_slope"] * (raw[0, 0].astype(LD) - 10)
    transformed = np.stack([finite_sum(frame, -1) for frame in corrected])
    phases = TAU * np.arange(5, dtype=LD) / 5
    rows = np.stack(
        (np.ones(5), np.cos(phases), np.sin(phases), np.cos(2 * phases), np.sin(2 * phases))
    )
    bands = np.tensordot(rows, transformed, axes=(1, 0))[:, :, :, : x // 2 + 1]
    bands[:, :, :, -1] = transformed[:, :, :, x // 2]
    return bands


def read_band(bands: Array, m: int, iz: int, iy: int, ix: int) -> complex:
    z, y, half = bands.shape[1:]
    x = 2 * (half - 1)
    if ix < 0:
        values = np.conj(bands[:, (-iz) % z, (-iy) % y, -ix])
    else:
        values = bands[:, iz % z, iy % y, ix % x]
    return complex(values[0] if m == 0 else values[2 * m - 1] + 1j * values[2 * m])


def reconstruct(
    bands: Array,
    h: Array,
    p: dict[str, Any],
    carrier: Array,
    amplitudes: Array,
    *,
    wiener_power: int = 2,
    taper_native: bool = False,
) -> tuple[Array, Array]:
    """Literal full-side visitation, then independent exponential assembly."""
    z, y, x, radial, cut = geometry(p)
    cutoffs = [cut, int((1 + 1 / 0.88) * cut), int(1.3 * cut)]
    cutoffs = [max(z // 2 - 1, 0) if c >= z // 2 else c for c in cutoffs]
    k = np.asarray(carrier, dtype=float)
    a = np.r_[1 + 0j, amplitudes]
    filtered = bands.copy()
    for m in range(3):
        full = np.zeros((z, y, x), dtype=CD)
        c = cutoffs[m]
        for iy in range(-(y // 2 - 1), y // 2 + 1):
            for ix in range(-(x // 2 - 1), x // 2 + 1):
                if m == 0 and ix < 0:
                    continue
                reflected = ix < 0
                hx, hy = abs(ix), (-iy if reflected else iy) % y
                r = math.hypot(ix / x, iy / y)
                slots = [0] if m == 0 else [2 * m - 1, 2 * m]
                for iz in range(-c, c + 1):
                    hz = (-iz if reflected else iz) % z
                    if r > radial:
                        filtered[slots, iz % z, hy, hx] = 0
                        continue
                    obj = np.array((ix / x, iy / y)) + m * k
                    self_h = sample(h, m, ix / x, iy / y, iz)
                    powers = abs(a[m] * self_h) ** 2
                    for n in range(-2, 3):
                        if n == m:
                            continue
                        other = obj - n * k
                        if np.linalg.norm(other) < radial:
                            powers += (
                                abs(
                                    a[abs(n)]
                                    * sample(h, abs(n), float(other[0]), float(other[1]), iz)
                                )
                                ** 2
                            )
                    denominator = powers + p["filtering"]["wiener"] ** wiener_power
                    taper_xy = np.array((ix / x, iy / y)) if taper_native else obj
                    rho = math.sqrt(
                        (np.linalg.norm(taper_xy) / (radial + 2 * np.linalg.norm(k))) ** 2
                        + (abs(iz) / cutoffs[1]) ** 2
                    )
                    taper = (
                        math.cos(math.pi * min(rho, 1) / 2)
                        if p["filtering"]["output_taper"] == "cosine"
                        else 1
                    )
                    scale = taper * np.conj(a[m] * self_h) / denominator
                    value = read_band(bands, m, iz, iy, ix) * scale
                    if m == 0:
                        filtered[0, hz, hy, hx] = value
                    else:
                        full[iz % z, iy % y, ix % x] = value
                filtered[slots, c + 1 : z - c, hy, hx] = 0
        if m:
            for iz in range(-c, c + 1):
                for iy in range(-(y // 2 - 1), y // 2 + 1):
                    for ix in range(x // 2 + 1):
                        pos = full[iz % z, iy % y, ix]
                        neg = np.conj(full[(-iz) % z, (-iy) % y, (-ix) % x])
                        filtered[2 * m - 1, iz % z, iy % y, ix] = (pos + neg) / 2
                        filtered[2 * m, iz % z, iy % y, ix] = (pos - neg) / (2j)
    image = assemble(filtered, p, k)
    return filtered, image


def assemble(filtered: Array, p: dict[str, Any], carrier: Array) -> Array:
    z, y, x, _, _ = geometry(p)
    out_shape = (z, 2 * y, 2 * x)
    yy, xx = np.indices(out_shape[1:], dtype=LD)
    image = np.zeros(out_shape, dtype=LD)
    for m in range(3):
        padded = np.zeros(out_shape, dtype=CD)
        for iz, iy, ix in np.ndindex((z, y, x)):
            qz, qy, qx = signed(iz, z), signed(iy, y), signed(ix, x)
            padded[qz % z, qy % (2 * y), qx % (2 * x)] = read_band(filtered, m, qz, qy, qx)
        spatial = finite_sum(padded, +1)
        if m == 0:
            image += np.real(spatial)
        else:
            ramp = np.exp(
                CD(1j) * TAU * m * (carrier[0] * (xx - x) / 2 + carrier[1] * (yy - y) / 2)
            )
            image += 2 * np.real(spatial * ramp)
    return image
