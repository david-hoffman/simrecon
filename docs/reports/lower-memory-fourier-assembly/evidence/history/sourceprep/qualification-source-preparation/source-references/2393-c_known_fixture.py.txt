"""Independent finite controls for the CE04 public contract.

No production Fourier, filter, sampler or assembly helper is an oracle.
"""

from __future__ import annotations

import importlib
import itertools
import math
from typing import Any

import numpy as np
from numpy.testing import assert_allclose

SETTINGS: dict[str, Any] = {
    "wavelength_nm": 520,
    "numerical_aperture": 0.8,
    "immersion_index": 1.33,
    "wiener": 0.5,
    "suppress_singularities": False,
    "suppression_radius_bins": 10.0,
    "dampen_order0": False,
    "omit_order0": False,
    "omit_kz0": False,
    "output_taper": "none",
}

SOURCE = (
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


def public(name: str) -> Any:
    """Look up only a named public entry during the owning test invocation."""
    module = importlib.import_module("simrecon")
    assert hasattr(module, name), f"CE04 public entry absent: {name}"
    return getattr(module, name)


def known(bands: Any, transfer: Any, **changes: Any) -> Any:
    """Call the public boundary with explicit shared parameters."""
    quadratures = getattr(bands, "quadratures", None)
    noise = getattr(bands, "noise_variance_factors", None)
    nd = (
        quadratures.shape[1] if isinstance(quadratures, np.ndarray) and quadratures.ndim == 6 else 1
    )
    orders = noise.shape[1] if isinstance(noise, np.ndarray) and noise.ndim == 2 else 2
    options = SETTINGS | {
        "carriers_cyc_um": np.zeros((nd, 2)),
        "modulation": np.ones((nd, orders - 1)),
    }
    options.update(changes)
    return public("reconstruct_known")(bands, transfer, **options)


def bands_from(raw: np.ndarray, orders: int = 2, **changes: Any) -> Any:
    """Prepare real input through the accepted public CE02 entry."""
    options = dict(
        dxy_um=0.5,
        dz_um=0.3,
        norders=orders,
        background=0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )
    options.update(changes)
    return public("prepare_bands")(raw, **options)


def blank(orders: int = 2, shape: tuple[int, ...] | None = None, **changes: Any) -> Any:
    """Create writable valid records without fabricating a production type."""
    if shape is None:
        shape = (1, 1, 2 * orders - 1, 6, 4, 4)
    return bands_from(np.zeros(shape, dtype=np.float32), orders, **changes)


def table(orders: int = 2, layout: str = "radial", constant: bool = False) -> Any:
    """Declare dyadic complex tables with ample actual interpolation vertices."""
    shape = (orders, 32, 32) if layout == "radial" else (orders, 32, 32, 24)
    values = np.ones(shape, dtype=np.complex64)
    if not constant:
        for index in np.ndindex(shape):
            m, *axes = index
            values[index] = (1 + m / 4 + sum(axes) / 128) + 1j * (
                (m + 1) / 8 + sum((j + 1) * v for j, v in enumerate(axes)) / 256
            )
    return public("declare_otf")(values, layout=layout, dkr_cyc_um=0.25, dkz_cyc_um=0.25)


def signed(n: int, length: int) -> int:
    """Use the specified positive even endpoint."""
    return n if n <= length // 2 else n - length


def raw_quadratures(raw: np.ndarray, orders: int, scale: float) -> np.ndarray:
    """Compute raw uniform-phase controls by explicit separable finite sums."""
    nt, nd, np_, nz, ny, nx = raw.shape
    result = np.zeros((nt, nd, 2 * orders - 1, nz, ny, nx // 2 + 1), complex)
    phase = 2 * np.pi * np.arange(np_) / np_
    rows = [np.ones(np_)]
    for m in range(1, orders):
        rows.extend([np.cos(m * phase), np.sin(m * phase)])
    pixels = np.array(list(itertools.product(range(nz), range(ny), range(nx))))
    for iz, iy, ix in itertools.product(range(nz), range(ny), range(nx // 2 + 1)):
        kernel = np.exp(-2j * np.pi * (pixels @ np.array([iz / nz, iy / ny, ix / nx])))
        for t, d, q in itertools.product(range(nt), range(nd), range(2 * orders - 1)):
            weights = np.eye(np_)[q] if ix == nx // 2 else rows[q]
            result[t, d, q, iz, iy, ix] = scale * sum(
                weights[p] * np.dot(raw[t, d, p].ravel(), kernel) for p in range(np_)
            )
    return result


def supports(bands: Any, settings: dict[str, Any]) -> tuple[float, list[int]]:
    """Evaluate the scalar optical cutoffs independently."""
    nz = bands.input_shape[3]
    o = bands.noise_variance_factors.shape[1]
    le = settings["wavelength_nm"] / (1000 * settings["immersion_index"])
    angle = math.asin(settings["numerical_aperture"] / settings["immersion_index"])
    c0 = math.ceil((1 - math.cos(angle)) / le * nz * bands.dz_um)
    cuts = [c0] + [math.trunc((1 + 1 / 0.88) * c0)] * (o - 2) + [math.trunc(1.3 * c0)]
    cuts = [max(nz // 2 - 1, 0) if c >= nz // 2 else c for c in cuts]
    radius = min(
        2000 * settings["numerical_aperture"] / settings["wavelength_nm"], 1 / (2 * bands.dxy_um)
    )
    return radius, cuts


def transfer_value(transfer: Any, order: int, x: float, y: float, z: int, dzf: float) -> complex:
    """Evaluate a declared tensor table as a sum of vertex basis weights."""
    data = transfer.samples[order]
    tz = z * dzf / transfer.dkz_cyc_um
    reflect = transfer.layout == "full" and x < 0
    if reflect:
        x, y, tz = -x, -y, -tz
    if transfer.layout == "radial":
        coords = [math.hypot(x, y) / transfer.dkr_cyc_um, tz]
    else:
        coords = [tz, y / transfer.dkr_cyc_um, x / transfer.dkr_cyc_um]
    # Wrap only the periodic coordinates once, matching the permitted query domain.
    periodic = [1] if transfer.layout == "radial" else [0, 1]
    for axis in periodic:
        if coords[axis] < 0:
            coords[axis] += data.shape[axis]
    lower = [math.floor(c) for c in coords]
    fraction = [c - a for c, a in zip(coords, lower, strict=True)]
    value = 0j
    for corner in itertools.product((0, 1), repeat=data.ndim):
        indices = [i + b for i, b in zip(lower, corner, strict=True)]
        for axis in periodic:
            if corner[axis]:
                indices[axis] %= data.shape[axis]
        flat = int(np.ravel_multi_index(tuple(indices), data.shape, mode="raise"))
        weight = math.prod(f if b else 1 - f for f, b in zip(fraction, corner, strict=True))
        value += weight * data.ravel()[flat]
    return complex(value.conjugate() if reflect else value)


def expectation(
    bands: Any, transfer: Any, *, original: np.ndarray | None = None, **changes: Any
) -> tuple[np.ndarray, np.ndarray, float]:
    """Evaluate sparse signed bands and direct spatial finite sums.

    Write events below preserve the explicitly specified odd-row quirks. The
    independent assembly evaluates frequencies directly, without FFT/embedding.
    """
    settings = SETTINGS | changes
    q0 = bands.quadratures.copy() if original is None else original.copy()
    filtered = q0.copy()
    nt, nd, _, nz, ny, nh = q0.shape
    nx = 2 * (nh - 1)
    orders = bands.noise_variance_factors.shape[1]
    carriers = np.asarray(settings.get("carriers_cyc_um", np.zeros((nd, 2))), dtype=np.float64)
    mods = np.asarray(settings.get("modulation", np.ones((nd, orders - 1))), dtype=np.complex128)
    amplitude = np.column_stack([np.ones(nd), mods])
    radius, cuts = supports(bands, settings)
    dx, dy, dzf = 1 / (nx * bands.dxy_um), 1 / (ny * bands.dxy_um), 1 / (nz * bands.dz_um)
    sr = settings["suppression_radius_bins"] * min(dx, dy)
    rp = radius + np.linalg.norm(carriers[0]) * (orders - 1)

    def weight(d: int, m: int, r: float, z: int) -> float:
        gain = 1 / bands.noise_variance_factors[d, m]
        suppress = settings["suppress_singularities"] and r <= sr
        if suppress and (m or not (settings["dampen_order0"] or settings["omit_order0"])):
            gain *= (r * r + 0.2) / (r * r + 1000.2)
        elif m == 0 and settings["dampen_order0"]:
            gain *= (r / radius) ** 2 + abs(z / cuts[0]) ** 3
        elif m == 0 and settings["omit_order0"]:
            gain = 0.0
        if m == 0 and z == 0 and settings["omit_kz0"]:
            gain = 0.0
        return float(gain)

    def coefficient(d: int, m: int, x: int, y: int, z: int) -> complex:
        k = np.array([x * dx, y * dy])
        obj = k + m * carriers[d]
        r = float(np.linalg.norm(k))
        h = transfer_value(transfer, m, float(k[0]), float(k[1]), z, dzf)
        g = weight(d, m, r, z)
        terms = [abs(h * amplitude[d, m]) ** 2 * g]
        for e, n in itertools.product(range(nd), range(1 - orders, orders)):
            if (e, n) == (d, m):
                continue
            other = obj - n * carriers[e]
            rr = float(np.linalg.norm(other))
            if rr < radius:
                hh = transfer_value(transfer, abs(n), float(other[0]), float(other[1]), z, dzf)
                terms.append(abs(hh * amplitude[e, abs(n)]) ** 2 * weight(e, abs(n), rr, z))
        taper = 1.0
        if settings["output_taper"] == "cosine":
            rho2 = float(np.dot(obj, obj)) / rp**2
            if cuts[1] > 0:
                rho2 += (abs(z) / cuts[1]) ** 2
            taper = math.cos(math.pi / 2 * min(math.sqrt(rho2), 1))
        return (
            taper
            * g
            * h.conjugate()
            * amplitude[d, m].conjugate()
            / (math.fsum(terms) + settings["wiener"] ** 2)
        )

    ys = range(1 - ny // 2, ny // 2 + 1) if ny > 1 else range(0)
    for t, d, m in itertools.product(range(nt), range(nd), range(orders)):
        slots = [0] if m == 0 else [2 * m - 1, 2 * m]
        positive: dict[tuple[int, int, int], complex] = {}
        for y, x in itertools.product(ys, range(1 - nx // 2, nx // 2 + 1)):
            if m == 0 and x < 0:
                continue
            iy, ix = (y % ny, x) if x >= 0 else (-y % ny, -x)
            for z in range(-cuts[m], cuts[m] + 1):
                if math.hypot(x * dx, y * dy) > radius:
                    filtered[t, d, slots, z % nz, iy, ix] = 0
                    continue
                iz = z % nz if x >= 0 else -z % nz
                values = q0[t, d, slots, iz, iy, ix]
                if x < 0:
                    values = values.conjugate()
                value = values[0] if m == 0 else values[0] + 1j * values[1]
                c = value * coefficient(d, m, x, y, z)
                if m == 0:
                    filtered[t, d, 0, z % nz, iy, ix] = c
                else:
                    positive[z % nz, y % ny, x % nx] = c
            filtered[t, d, slots, cuts[m] + 1 : nz - cuts[m], iy, ix] = 0
        if m:
            for z, y, x in itertools.product(range(-cuts[m], cuts[m] + 1), ys, range(nh)):
                p = positive.get((z % nz, y % ny, x), 0j)
                n = positive.get((-z % nz, -y % ny, -x % nx), 0j).conjugate()
                filtered[t, d, 2 * m - 1, z % nz, y % ny, x] = (p + n) / 2
                filtered[t, d, 2 * m, z % nz, y % ny, x] = (p - n) / 2j
    image, budget = assemble(filtered, bands, carriers, settings["omit_order0"])
    return filtered, image, budget


def assemble(
    quadratures: np.ndarray, bands: Any, carriers: np.ndarray, omit_order0: bool = False
) -> tuple[np.ndarray, float]:
    """Evaluate a frequency dictionary directly on the enlarged spatial grid."""
    nt, nd, nq, nz, ny, nh = quadratures.shape
    nx = 2 * (nh - 1)
    az, ly = bands.axial_zoom, bands.lateral_zoom
    zz, yy, xx = np.indices((az * nz, ly * ny, ly * nx))
    xc = (xx - (ly * nx) // 2) * bands.dxy_um / ly
    yc = (yy - (ly * ny) // 2) * bands.dxy_um / ly
    image = np.zeros((nt, *xx.shape))
    budget = 0.0
    for t, d, m in itertools.product(range(nt), range(nd), range((nq + 1) // 2)):
        if m == 0 and omit_order0:
            continue
        u = np.zeros(xx.shape, complex)
        for iz, iy, ix in itertools.product(range(nz), range(ny), range(nx)):
            z, y, x = signed(iz, nz), signed(iy, ny), signed(ix, nx)
            indices = (z % nz, y % ny, x) if x >= 0 else (-z % nz, -y % ny, -x)
            slots = [0] if m == 0 else [2 * m - 1, 2 * m]
            vals = quadratures[t, d, slots, *indices]
            if x < 0:
                vals = vals.conjugate()
            c = vals[0] if m == 0 else vals[0] + 1j * vals[1]
            u += c * np.exp(
                2j * np.pi * (z * zz / (az * nz) + y * yy / (ly * ny) + x * xx / (ly * nx))
            )
            budget += abs(c) * (1 if m == 0 else 2)
        image[t] += (
            np.real(u)
            if m == 0
            else 2
            * np.real(u * np.exp(2j * np.pi * m * (carriers[d, 0] * xc + carriers[d, 1] * yc)))
        )
    return image, budget


def compare(bands: Any, transfer: Any, **changes: Any) -> Any:
    """Observe the real public result against preregistered finite expectations."""
    filtered, image, budget = expectation(bands, transfer, **changes)
    result = known(bands, transfer, **changes)
    assert_allclose(
        result.filtered_quadratures,
        filtered,
        rtol=2e-10,
        atol=2e-10 * max(1.0, float(np.max(np.abs(filtered)))),
    )
    assert_allclose(result.image, image, rtol=3e-10, atol=3e-10 * max(1, budget))
    return result
