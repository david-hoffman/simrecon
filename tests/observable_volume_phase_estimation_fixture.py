"""Independent finite Fourier and spatial observers for the public phase contract.

No product numerical output supplies expected scientific values.  Small matrices
are deliberately explicit; these are observers, not scalable implementations.
"""

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

import simrecon as sr

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
Bool = NDArray[np.bool_]
EPS = 2.0**-52
QUANTUM = float.fromhex("0x0.0000000000001p-1022")


def canonical(angles: Real) -> Real:
    """Apply the specified native fundamental, without reducing huge angles."""
    result = np.arctan2(np.sin(angles), np.cos(angles))
    return np.where(result == np.pi, -np.pi, result)


def powers(angles: Real) -> dict[int, Complex]:
    """Represent the two harmonics with the contract's rounded operations."""
    c, s = np.cos(angles), np.sin(angles)
    z = c + 1j * s
    z2 = (c * c - s * s) + 1j * ((2 * c) * s)
    return {-2: z2.conj(), -1: z.conj(), 0: np.ones_like(z), 1: z, 2: z2}


def make_orders(values: Complex, **changes: Any) -> Any:
    """Construct a public algebraic record with canonical unit-spacing bins."""
    shape = values.shape[1:]
    fields: dict[str, Any] = {
        "values": values,
        "fz_per_um": np.arange(-(shape[0] // 2), (shape[0] + 1) // 2) / shape[0],
        "fy_per_um": np.arange(-(shape[1] // 2), (shape[1] + 1) // 2) / shape[1],
        "fx_per_um": np.arange(-(shape[2] // 2), (shape[2] + 1) // 2) / shape[2],
        "voxel_size_um": (1.0, 1.0, 1.0),
        "origin_zyx": tuple(n - 1 for n in shape),
        "source": "independent signed algebraic calibration",
    }
    fields.update(changes)
    return sr.VolumeOrderOtf(**fields)


def record_fields(record: Any) -> dict[str, Any]:
    """Copy only the explicitly published calibration fields."""
    return {
        name: getattr(record, name)
        for name in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }


def geometry(shape: tuple[int, ...]) -> tuple[Real, list[tuple[int, ...]], Complex]:
    """Return centered modes, modular labels and a direct unitary DFT matrix."""
    sites = np.array(list(np.ndindex(shape)), dtype=np.float64)
    modes = np.array(
        list(product(*(range(-(n // 2), (n + 1) // 2) for n in shape))),
        dtype=np.float64,
    )
    labels = [tuple(int(k) % n for k, n in zip(mode, shape, strict=True)) for mode in modes]
    matrix = np.exp(-2j * np.pi * ((modes / np.array(shape)) @ sites.T)) / np.sqrt(
        float(np.prod(shape))
    )
    return modes, labels, matrix


def normalize(values: Complex, images: Real) -> tuple[Complex, Real, float, float]:
    """Scale real components separately, avoiding a complex magnitude overflow."""
    t = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag)))) or 1.0
    b = float(np.max(np.abs(images))) or 1.0
    with np.errstate(under="ignore"):
        scaled = np.empty(values.shape, dtype=np.complex128)
        scaled.real = values.real / t
        scaled.imag = values.imag / t
        data = np.asarray(images / b, dtype=np.float64)
    return scaled, data, b, t


def signed_rows(values: Complex) -> dict[int, Complex]:
    """Reflect by modular labels on all axes, rather than reversing storage."""
    shape = values.shape[1:]
    _, labels, _ = geometry(shape)
    lookup = {label: i for i, label in enumerate(labels)}
    negative = [lookup[tuple((-j) % n for j, n in zip(k, shape, strict=True))] for k in labels]
    return {
        -2: values[2].ravel()[negative].conj(),
        -1: values[1].ravel()[negative].conj(),
        0: values[0].ravel(),
        1: values[1].ravel(),
        2: values[2].ravel(),
    }


def support(values: Complex, carrier: tuple[int, int]) -> Bool:
    """Evaluate V(j) then its full Hermitian closure by the contract equation."""
    shape = values.shape[1:]
    _, labels, _ = geometry(shape)
    lookup = {label: i for i, label in enumerate(labels)}
    rows = signed_rows(values)
    visible = np.zeros(len(labels), dtype=np.bool_)
    shift = (0, *carrier)
    for i, j in enumerate(labels):
        for m, row in rows.items():
            k = tuple((a + m * e) % n for a, e, n in zip(j, shift, shape, strict=True))
            value = row[lookup[k]]
            visible[i] |= value.real != 0 or value.imag != 0
    return np.array(
        [
            visible[i] or visible[lookup[tuple((-a) % n for a, n in zip(j, shape, strict=True))]]
            for i, j in enumerate(labels)
        ],
        dtype=np.bool_,
    ).reshape(shape)


def orbit_basis(mask: Bool) -> Real:
    """Construct real cosine/sine columns; self-conjugate orbits count once."""
    shape = mask.shape
    _, labels, transform = geometry(shape)
    lookup = {label: i for i, label in enumerate(labels)}
    seen: set[int] = set()
    columns: list[Real] = []
    for i, j in enumerate(labels):
        if not mask.ravel()[i] or i in seen:
            continue
        opposite = lookup[tuple((-a) % n for a, n in zip(j, shape, strict=True))]
        seen.update((i, opposite))
        if opposite == i:
            columns.append(transform[i].real)
        else:
            columns.extend((np.sqrt(2.0) * transform[i].real, np.sqrt(2.0) * transform[i].imag))
    return np.column_stack(columns) if columns else np.empty((len(labels), 0))


def operator(
    values: Complex,
    carrier: tuple[int, int],
    phases: Real,
) -> tuple[Real, list[Real]]:
    """Build every full real/imaginary row and each analytic phase derivative."""
    shape = values.shape[1:]
    _, labels, transform = geometry(shape)
    lookup = {label: i for i, label in enumerate(labels)}
    rows = signed_rows(values)
    z = powers(phases)
    n, size = len(phases), len(labels)
    forward = np.zeros((n, size, size), dtype=np.complex128)
    differential = np.zeros_like(forward)
    shift = (0, *carrier)
    for p in range(n):
        for k_index, k in enumerate(labels):
            for m, row in rows.items():
                j = tuple(
                    (a - m * e) % length for a, e, length in zip(k, shift, shape, strict=True)
                )
                term = z[m][p] * row[k_index] * transform[lookup[j]]
                forward[p, k_index] += term
                differential[p, k_index] += (1j * m) * term
    realified = np.concatenate(
        (forward.real.reshape(n * size, size), forward.imag.reshape(n * size, size))
    )
    derivatives = []
    for p in range(n):
        part = np.zeros_like(forward)
        part[p] = differential[p]
        derivatives.append(
            np.concatenate((part.real.reshape(n * size, size), part.imag.reshape(n * size, size)))
        )
    return realified, derivatives


@dataclass
class Profile:
    """Independent stored-input objective and diagnostic targets at given phases."""

    mask: Bool
    q: Real
    a: Real
    b: Real
    y: Real
    u: Real
    residual: Real
    prediction: Real
    singular: Real
    rank: int
    jacobian: Real
    information: Real
    phase_singular: Real
    phase_rank: int
    design_rank: int
    gradient: float
    relative: float
    rms: float
    imaginary: float
    defect: float
    allowance: float


def observe(
    images: Real,
    values: Complex,
    carrier: tuple[int, int],
    phases: Real,
) -> Profile:
    """Solve an explicit reduced matrix and evaluate all defined diagnostics."""
    normalized, data, _, _ = normalize(values, images)
    mask = support(normalized, carrier)
    q = orbit_basis(mask)
    a, derivatives = operator(normalized, carrier, phases)
    b = a @ q
    _, _, transform = geometry(values.shape[1:])
    yf = data.reshape(len(phases), -1) @ transform.T
    y = np.concatenate((yf.real.ravel(), yf.imag.ravel()))
    left, singular, right = np.linalg.svd(b, full_matrices=False)
    rank = int(np.count_nonzero(singular > EPS * len(y) * singular[0])) if singular.size else 0
    pinv = (right[:rank].T / singular[:rank]) @ left[:, :rank].T
    v = pinv @ y
    u = q @ v
    prediction = b @ v
    residual = y - prediction
    d = np.column_stack([ap @ u for ap in derivatives])
    information = d - b @ (pinv @ d)
    jacobian = -information - np.column_stack(
        [pinv.T @ ((ap @ q).T @ residual) for ap in derivatives]
    )
    phase_singular = np.linalg.svd(information, compute_uv=False)
    phase_rank = int(
        np.count_nonzero(phase_singular > EPS * max(len(y), len(phases)) * phase_singular[0])
    )
    z = powers(phases)
    design = np.column_stack((np.ones(len(phases)), z[1].real, z[1].imag, z[2].real, z[2].imag))
    design_singular = np.linalg.svd(design, compute_uv=False)
    design_rank = int(
        np.count_nonzero(design_singular > EPS * max(design.shape) * design_singular[0])
    )
    size = images[0].size
    allowance = (
        2.0**20
        * len(y)
        * (size + len(phases) + 1)
        * EPS
        * (1 + np.linalg.norm(y) + np.linalg.norm(u) + np.linalg.norm(d)) ** 2
        + 256 * len(y) * (size + len(phases) + 1) * QUANTUM
    )
    f0 = normalized[0].ravel()
    _, labels, _ = geometry(values.shape[1:])
    lookup = {label: i for i, label in enumerate(labels)}
    reflected = f0[
        [lookup[tuple((-a) % n for a, n in zip(j, mask.shape, strict=True))] for j in labels]
    ].conj()
    return Profile(
        mask,
        q,
        a,
        b,
        y,
        u,
        residual,
        prediction,
        singular,
        rank,
        jacobian,
        information,
        phase_singular,
        phase_rank,
        design_rank,
        float(np.linalg.norm(jacobian.T @ residual, ord=np.inf)),
        float(np.linalg.norm(residual) / np.linalg.norm(y)) if np.any(y) else 0.0,
        float(np.linalg.norm(residual) / np.sqrt(len(phases) * size)),
        float(np.linalg.norm(prediction[len(y) // 2 :]) / np.sqrt(len(phases) * size)),
        float(np.linalg.norm(f0 - reflected) / np.sqrt(size)),
        float(allowance),
    )


def spatial_images(
    specimen: Real,
    kernels: Complex,
    carrier: tuple[int, int],
    phases: Real,
) -> Real:
    """Generate independently by real-space illumination and circular convolution."""
    shape = specimen.shape
    result = np.zeros((len(phases), *shape), dtype=np.float64)
    for n in np.ndindex(shape):
        for j in np.ndindex(shape):
            delta = tuple((a - b) % length for a, b, length in zip(n, j, shape, strict=True))
            lateral = 2 * np.pi * (carrier[0] * j[1] / shape[1] + carrier[1] * j[2] / shape[2])
            for p, phase in enumerate(phases):
                angle = lateral + phase
                result[(p, *n)] += specimen[j] * (
                    kernels[(0, *delta)].real
                    + 2
                    * (
                        kernels[(1, *delta)] * np.exp(1j * angle)
                        + kernels[(2, *delta)] * np.exp(2j * angle)
                    ).real
                )
    return result


def kernel_transfers(kernels: Complex) -> Complex:
    """Transform independent spatial kernels with an explicit nonunitary sum."""
    _, _, unitary = geometry(kernels.shape[1:])
    return (kernels.reshape(3, -1) @ unitary.T * np.sqrt(kernels[0].size)).reshape(kernels.shape)


def inference_group(which: int) -> tuple[Real, Complex, Real, Real, Real, Complex]:
    """Create two actual groups with distinct objects, phases, kernels and grids."""
    shape = (1, 2, 3) if which == 0 else (2, 1, 3)
    sites = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    specimen = 0.7 + 0.13 * sites + 0.21 * np.cos(1.2 * sites + which)
    h = (1 + 0.17 * sites).astype(np.complex128)
    h.flat[0] += 8 + which
    h /= np.sum(h)
    kernels = np.stack((h, h * (0.23 + 0.08j + 0.012j * sites), h * (0.11 - 0.04j - 0.009 * sites)))
    actual = np.array([-2.65, -1.6, -0.5, 0.45, 1.5, 2.6])
    if which:
        actual = actual + np.array([0.04, -0.02, 0.03, -0.06, 0.01, -0.03])
    nominal = actual + np.array([0.021, -0.027, 0.016, 0.032, -0.019, 0.011])
    images = spatial_images(specimen, kernels, (0, 1), actual)
    return images, kernel_transfers(kernels), actual, nominal, specimen, kernels


def rank_change_fixture(nz: int) -> tuple[Real, Complex, Real]:
    """Supply a real solver trial that extinguishes one retained spatial mode.

    On the observable axial-constant subspace the illumination is
    1+cos(phi+2*pi*x/4). Symmetric initial +/-0.1 rad commands have full
    nuisance rank. Equal zero-phase data drive the real solver to zero, where
    x=2 is invisible. With nz=2 the axial-varying modes are structurally absent.
    """
    images = np.tile(np.array([2.0, 1.0, 0.0, 1.0]), (6, nz, 1, 1)).reshape(6, nz, 1, 4)
    values = np.zeros((3, nz, 1, 4), dtype=np.complex128)
    values[0, nz // 2] = 1
    values[1, nz // 2] = 0.5
    phases = np.array([-0.1, 0.1, -0.1, 0.1, -0.1, 0.1])
    return images, values, phases


def empirical_pair_fixture() -> dict[str, Any]:
    """Generate a selected-model raw point bead and independent specimen group.

    Camera values are counts; corrected signals are electrons. Kernels are
    dimensionless. Calibration/specimen phases use two explicitly different
    reference origins; neither true bead location nor kernels reach calibration.
    """
    shape = (2, 3, 3)
    carrier = (1, -1)
    spacing = (0.7, 0.4, 0.6)
    sites = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    h = 1 + 0.03 * sites
    h.flat[0] += 40
    h /= np.sum(h)
    a0, ap, am = 1 + 0.1j, 0.6 + 0.2j, 0.45 - 0.15j
    power = abs(a0) ** 2 + abs(ap) ** 2 + abs(am) ** 2
    axial = np.exp(2j * np.pi * np.arange(shape[0]) / shape[0])[:, None, None]
    g1 = (ap * a0.conjugate() * axial.conj() + a0 * am.conjugate() * axial) / power
    g2 = ap * am.conjugate() / power
    kernels = np.stack((h.astype(np.complex128), h * g1, h * np.full(shape, g2))).astype(
        np.complex128
    )
    origin = (1, 1, 2)
    bead = np.zeros(shape)
    bead[origin] = 7
    calibration_physical = np.array([-2.8, -1.9, -0.7, 0.3, 1.35, 2.45])
    alpha_c, alpha_s = 0.17, -0.24
    calibration_images = spatial_images(bead, kernels, carrier, calibration_physical)
    raw = (13.0 + 1.7 * calibration_images)[None]
    specimen = 0.8 + 0.025 * sites + 0.15 * np.cos(1.2 * sites)
    actual = np.array([-2.65, -1.6, -0.5, 0.45, 1.5, 2.6])
    images = spatial_images(specimen, kernels, carrier, actual)
    initial = actual + alpha_s + np.array([0.021, -0.027, 0.016, 0.032, -0.019, 0.011])
    transfer = kernel_transfers(kernels)
    bead_angle = 2 * np.pi * (carrier[0] * origin[1] / shape[1] + carrier[1] * origin[2] / shape[2])
    expected_response, expected_orders = transfer.copy(), transfer.copy()
    components = np.empty_like(kernels)
    for m in range(3):
        components[m] = 7 * np.roll(kernels[m], origin, axis=(0, 1, 2))
        components[m] *= np.exp(1j * m * (bead_angle - alpha_c))
        expected_response[m] *= np.exp(1j * m * (bead_angle - alpha_c))
        expected_orders[m] *= np.exp(-1j * m * alpha_s)
    return {
        "raw_counts": raw,
        "calibration_images": calibration_images,
        "calibration_phases_rad": calibration_physical + alpha_c,
        "specimen_images": images,
        "specimen_initial_rad": initial,
        "specimen_actual_rad": actual + alpha_s,
        "kernels": kernels,
        "expected_components": components,
        "expected_response": expected_response,
        "expected_orders": expected_orders,
        "origin": origin,
        "voxel_size_um": spacing,
        "carrier": carrier,
        "phase_reference_shift_rad": alpha_s - alpha_c,
        "config": {
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "nominal_phases_rad": [[0.0] * 6],
            "intensity_unit": "counts",
        },
    }


def reduced_inference_fixture(exposures: int) -> dict[str, Any]:
    """Hide axial-antisymmetric specimen content from all supplied order maps."""
    _, base_values, actual, nominal, base_specimen, base_kernels = inference_group(0)
    kernels = np.repeat(base_kernels, 2, axis=1) / 2
    observable = np.repeat(base_specimen, 2, axis=0)
    amplitude = 0.07 + 0.013 * np.arange(base_specimen.size).reshape(base_specimen.shape)
    invisible = np.concatenate((amplitude, -amplitude), axis=0)
    hidden = observable + invisible
    values = np.zeros((3, *hidden.shape), dtype=np.complex128)
    values[:, 1] = base_values[:, 0]  # Axial DC only; other bins are exact stored zeros.
    images = spatial_images(hidden, kernels, (0, 1), actual[:exposures])
    return {
        "images": images,
        "values": values,
        "actual": actual[:exposures].copy(),
        "nominal": nominal[:exposures].copy(),
        "observable": observable,
        "hidden": hidden,
        "invisible": invisible,
        "kernels": kernels,
    }


# The CI test starts a fresh interpreter so public dependency controls are in
# place before product-bound imports. Blind probes execute this exact literal
# directly as fresh tool-level source-free entries, never as nested children.
SOLVER_FAILURE_PAYLOAD = r"""
import json
import sys
import warnings
import numpy as np
import scipy.linalg
import scipy.optimize

api_name, boundary, kind = sys.argv[1:4]
assert 'simrecon' not in sys.modules, 'controls require a fresh product import'
state = {'active': False, 'hits': 0}
errors = {
    'linalg': np.linalg.LinAlgError('controlled public solver numerical exception'),
    'floating': FloatingPointError('controlled public solver numerical exception'),
    'overflow': OverflowError('controlled public solver numerical exception'),
    'memory': MemoryError('controlled public solver allocation exception'),
    'runtime': RuntimeError('controlled public solver unrelated exception'),
    'type': TypeError('controlled public solver unrelated exception'),
    'value': ValueError('controlled public solver unrelated exception'),
}
error = errors.get(kind)
originals = []
def control(original):
    def invoke(*args, **kwargs):
        if state['active']:
            state['hits'] += 1
            if kind == 'runtime_warning':
                warnings.warn('controlled public solver arithmetic warning', RuntimeWarning,
                              stacklevel=1)
            elif kind == 'user_warning':
                warnings.warn('controlled public solver unrelated warning', UserWarning,
                              stacklevel=1)
            else:
                raise error
        return original(*args, **kwargs)
    return invoke

# Arm public SVD-based alternatives without selecting a particular backend or
# requiring a module lookup at call time. Imports can legitimately do their own
# work: controls remain inactive until the public operation is invoked.
if boundary == 'svd':
    for module in (np.linalg, scipy.linalg):
        for name in ('svd', 'svdvals', 'pinv', 'lstsq'):
            if hasattr(module, name):
                original = getattr(module, name)
                originals.append((module, name, original))
                setattr(module, name, control(original))
else:
    assert boundary == 'optimizer'
    original = scipy.optimize.least_squares
    originals.append((scipy.optimize, 'least_squares', original))
    scipy.optimize.least_squares = control(original)

import simrecon as sr
images = np.array([1., -.2, .5, -.4, .8, .1]).reshape(6, 1, 1, 1)
phases = np.array([-2.7, -1.4, -.2, .9, 2.2, 2.9])
values = np.array([1., .23+.08j, .11-.04j], dtype=np.complex128).reshape(3, 1, 1, 1)
frequencies = [np.zeros(1) for _ in range(3)]
orders = sr.VolumeOrderOtf(values=values, fz_per_um=frequencies[0],
    fy_per_um=frequencies[1], fx_per_um=frequencies[2], voxel_size_um=(1.,1.,1.),
    origin_zyx=(0,0,0), source='supplied public solver exception control')
arrays = [images, phases, values, *frequencies]
for array in arrays:
    array.setflags(write=False)
before = [(a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable) for a in arrays]
metadata = (orders.voxel_size_um, orders.origin_zyx, orders.source)
report = {'api': api_name, 'boundary': boundary, 'kind': kind}
with np.errstate(all='raise'), warnings.catch_warnings(record=True) as observed:
    warnings.simplefilter('ignore', RuntimeWarning)
    warnings.simplefilter('always', UserWarning)
    mode, filters = np.geterr(), list(warnings.filters)
    state['active'] = True
    try:
        result = getattr(sr, api_name)(images, order_otf=orders, carrier_bins_yx=(0,0),
            initial_phases_rad=phases, max_nfev=3, gradient_tolerance=1e-9,
            step_tolerance=1e-10, source='public exception-only controls')
    except Exception as caught:
        report.update(outcome='exception', exception_type=type(caught).__name__,
                      message=str(caught), code=getattr(caught, 'code', None),
                      identical=caught is error, domain_error=isinstance(caught, sr.SimreconError))
    else:
        report.update(outcome='finite_result', finite=bool(
            np.isfinite(result.specimen_normalized).all()
            and np.isfinite(result.phases_rad).all()
            and np.isfinite(result.normalized_residual_rms)))
    finally:
        state['active'] = False
    report['mode_preserved'] = np.geterr() == mode
    report['filters_preserved'] = warnings.filters == filters
    report['warnings'] = [{'category': w.category.__name__, 'message': str(w.message),
                           'filename': w.filename, 'lineno': w.lineno} for w in observed]
report['hits'] = state['hits']
report['inputs_preserved'] = before == [
    (a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable) for a in arrays]
report['metadata_preserved'] = metadata == (
    orders.voxel_size_um, orders.origin_zyx, orders.source) and orders.values is values and all(
        getattr(orders, name) is original for name, original in zip(
            ('fz_per_um', 'fy_per_um', 'fx_per_um'), frequencies, strict=True))
for module, name, original in originals:
    setattr(module, name, original)
print('SOLVER_PUBLIC_PROBE ' + json.dumps(report, sort_keys=True))
"""
