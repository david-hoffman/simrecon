"""Independent physical CE08 acquisition and frozen workflow observer.

No product imports. The approved A-authored finite sums/traversal are reused;
new analytic acquisition and physical mode response are derived here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ce08_finite_math import Array, finite_sum, prepare, reconstruct, sample, signed
from ce08_finite_search import overlap, regression

ROOT = Path(__file__).parent
SPEC = ROOT / "data/ce08-matched-recovery-v1.json"
FIXTURE = ROOT / "data/ce08-matched-recovery-v1.npz"


def registration() -> dict[str, Any]:
    return json.loads(SPEC.read_text())


def transfer_table(p: dict[str, Any]) -> Array:
    h = np.zeros(p["transfer"]["shape_ORK"], dtype=np.complex128)
    hz = np.array([1, 0.25 + 0.125j, 0, 0.25 - 0.125j])
    for m, r, z in np.ndindex(h.shape):
        v = r / 4
        radial = 2 * (math.acos(v) - v * math.sqrt(1 - v * v)) / math.pi if v < 1 else 0
        h[m, r, z] = float(np.float32(radial)) * hz[z % 4]
    return h.astype(np.complex64).astype(np.complex128)


def coordinates(output: bool) -> tuple[Array, Array, Array]:
    size, pitch = (16, 0.5) if output else (8, 1.0)
    return np.arange(size) * pitch - 4, np.arange(size) * pitch - 4, np.arange(4) - 2


def modes(p: dict[str, Any]) -> list[tuple[tuple[int, int, int], complex]]:
    result = [((0, 0, 0), complex(p["source"]["density_dc"]))]
    for kx, ky, kz, re, im in p["source"]["positive_modes_kxyz_real_imag"]:
        k = (kx, ky, kz)
        c = complex(re, im)
        result.extend(((k, c), (tuple(-v for v in k), c.conjugate())))
    return result


def wave(k: tuple[float, float, float], output: bool) -> Array:
    x, y, z = coordinates(output)
    return np.exp(
        2j * np.pi * (k[0] * x[None, None, :] + k[1] * y[None, :, None] + k[2] * z[:, None, None])
    )


def truth(p: dict[str, Any]) -> Array:
    values = sum(c * wave((k[0] / 8, k[1] / 8, k[2] / 4), True) for k, c in modes(p))
    return np.asarray(values.real, dtype=float)


def acquisition_bounds(p: dict[str, Any]) -> dict[str, float]:
    """Coefficient absolute-sum bounds; evaluated before acquiring any sample."""
    a = [complex(*v) for v in p["source"]["side_modulation_pairs"]]
    density = sum(abs(c) for _, c in modes(p))
    illumination = 1 + 2 * sum(abs(v) for v in a)
    raw = 10 + 0.4 * density * illumination
    quantization = raw * 2**-24
    return {
        "density_abs": density,
        "illumination_abs": illumination,
        "illumination_min": 2 - illumination,
        "raw_abs": raw,
        "raw_quantization_abs": quantization,
        "conventional_density_abs": 2 * quantization / 0.8,
    }


def acquire(p: dict[str, Any], h: Array) -> dict[str, Array]:
    """Synthesize CONTINUOUS object modes, shift, mask, then sample detector.

    High source frequencies are never multiplied on an undersampled native
    object grid. Both signed illumination orders pass the optical transfer
    before sampling, so unsupported high frequencies cannot alias into raw.
    """
    bounds = acquisition_bounds(p)
    assert bounds["illumination_min"] > 0
    assert p["source"]["reference_density"] > bounds["density_abs"]
    a = np.array([1, *(complex(*v) for v in p["source"]["side_modulation_pairs"])])

    def detected(source_modes: list[tuple[tuple[int, int, int], complex]]) -> Array:
        result = np.zeros((5, 4, 8, 8), dtype=np.complex128)
        for phase in range(5):
            phi = 2 * np.pi * phase / 5
            for m in range(-2, 3):
                am = a[abs(m)] if m >= 0 else a[-m].conjugate()
                for k, c in source_modes:
                    q = (k[0] / 8 - m / 8, k[1] / 8, k[2] / 4)
                    if math.hypot(q[0], q[1]) > 0.5 or abs(k[2]) > 1:
                        continue
                    optical = sample(h, abs(m), q[0], q[1], k[2])
                    result[phase] += c * am * np.exp(-1j * m * phi) * optical * wave(q, False)
        assert np.max(abs(result.imag)) < 1e-12
        return result.real

    contrast = detected(modes(p))
    reference = detected([((0, 0, 0), complex(p["source"]["reference_density"]))])
    specimen = reference + contrast
    assert np.min(reference) > 0 and np.min(specimen) > 0
    exact = 10 + 0.4 * contrast
    raw = exact.astype(np.float32)[None, None]
    assert np.max(abs(raw[0, 0].astype(float) - exact)) <= bounds["raw_quantization_abs"]
    assert np.all(raw[..., -1, -1] != -1)
    return {
        "raw": raw,
        "unquantized_raw": exact[None, None],
        "reference_corrected_counts": 0.8 * reference,
        "specimen_corrected_counts": 0.8 * specimen,
        "truth": truth(p),
    }


def fit(bands: Array, h: Array, p: dict[str, Any]) -> dict[str, Any]:
    """Actual search=False finite procedure: two fresh known-vector fits."""
    k = np.array(p["carrier_cyc_um"])
    builds, fits = [], []
    for m in (1, 2):
        build = overlap(bands, h, p, k, m, "known", m - 1)
        builds.append(build)
        fits.append(regression(build, k, p, False))
    return {"builds": builds, "fits": fits, "modulation": np.array([v["forward"] for v in fits])}


def conventional(raw: Array) -> Array:
    native = np.mean(2 * (raw[0, 0].astype(float) - 10), axis=0) / 0.8
    spectrum = finite_sum(native, -1) / 256
    output = np.zeros((4, 16, 16), dtype=np.complex128)
    for iz, iy, ix in np.ndindex(spectrum.shape):
        output[signed(iz, 4) % 4, signed(iy, 8) % 16, signed(ix, 8) % 16] = spectrum[iz, iy, ix]
    return np.real(finite_sum(output, +1))


def project(image: Array, p: dict[str, Any]) -> Array:
    """Signed complex Fourier coefficients in the physical centered labels."""
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]
    return np.array(
        [np.mean(image * np.conj(wave((k[0] / 8, k[1] / 8, k[2] / 4), True))) for k in keys]
    )


def mode_response(p: dict[str, Any], h: Array) -> tuple[Array, Array]:
    """Derive diagonal ideal response ONLY for this periodic interior case.

    Every signal-bearing shifted sample has |qx|<native Nyquist, |qy|<it,
    kz0, even Y and no suppressed/damped weights. Uniform phases give g1.
    Self-inclusive/other-strict powers coincide because H=0 at R equality.
    Signed traversals recover both real partners. Centered integer ramps
    restore the original physical mode. Thus P*gain/L^2=1 and T1 yield the
    derived sum-power/(sum-power+w^2). The complete quantized expectation
    still uses literal traversal with FITTED modulation, not this simplification.
    """
    a = np.array([1, *(complex(*v) for v in p["source"]["side_modulation_pairs"])])
    powers, responses = [], []
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]
    for kx, ky, kz in keys:
        power = 0.0
        for n in range(-2, 3):
            qx, qy = (kx - n) / 8, ky / 8
            # H is exactly zero at the physical support equality; there is
            # no signal-bearing unseparated x Nyquist or duplicated endpoint.
            if math.hypot(qx, qy) < 0.5:
                power += abs(a[abs(n)] * sample(h, abs(n), qx, qy, kz)) ** 2
        powers.append(power)
        responses.append(power / (power + p["filtering"]["wiener"] ** 2))
    return np.array(powers), np.array(responses)


def expected(p: dict[str, Any], raw: Array, h: Array) -> dict[str, Any]:
    bands = prepare(raw, p)
    fitted = fit(bands, h, p)
    filtered, image = reconstruct(bands, h, p, np.array(p["carrier_cyc_um"]), fitted["modulation"])
    return {"bands": bands, "filtered": filtered, "image": image, **fitted}


def capture(actual: Array, destination: Path) -> None:
    """Explicit later observer export; caller chooses path after authorization."""
    p = registration()
    with np.load(FIXTURE, allow_pickle=False) as frozen:
        arrays = {name: frozen[name] for name in frozen.files}
    arrays.update(
        actual=np.array(actual, copy=True),
        numerical_residual=actual - arrays["expected_image"],
        source_residual=actual - arrays["truth"],
        actual_modes=project(actual, p),
    )
    np.savez_compressed(destination, **arrays)
