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


# Fresh interpreters arm public controls before product/fixture-bound imports.
# Blind probes run this same literal directly through the admitted tool entry.
SOLVER_FAILURE_PAYLOAD = r"""
import json
import sys
import warnings
import numpy as np
import scipy.linalg
import scipy.linalg.lapack
import scipy.optimize

api_name, boundary, kind = sys.argv[1:4]
assert 'simrecon' not in sys.modules, 'controls require a fresh product import'
assert 'observable_volume_phase_estimation_fixture' not in sys.modules
state = {'active': False, 'fault': False, 'calls': 0, 'delivered': 0}
errors = {
    'linalg': np.linalg.LinAlgError('controlled public numerical exception'),
    'floating': FloatingPointError('controlled public numerical exception'),
    'overflow': OverflowError('controlled public numerical exception'),
    'memory': MemoryError('controlled public allocation exception'),
    'runtime': RuntimeError('controlled public unrelated exception'),
    'type': TypeError('controlled public unrelated exception'),
    'value': ValueError('controlled public unrelated exception'),
}
assert kind in (*errors, 'none', 'runtime_warning', 'user_warning',
                'zero', 'nonzero', 'deficient')
error = errors.get(kind)
originals = []
def diagnostic(error):
    frames = []
    cursor = error.__traceback__
    while cursor is not None:
        frames.append({'filename': cursor.tb_frame.f_code.co_filename,
                       'lineno': cursor.tb_lineno,
                       'function': cursor.tb_frame.f_code.co_name})
        cursor = cursor.tb_next
    item = {'type': type(error).__module__+'.'+type(error).__name__,
            'message': str(error), 'frames': frames}
    chained = error.__cause__ if error.__cause__ is not None else (
        error.__context__ if not error.__suppress_context__ else None)
    if chained is not None and chained is not error:
        item['chained'] = diagnostic(chained)
    return item
def control(original):
    def invoke(*args, **kwargs):
        if state['active']:
            state['calls'] += 1
            if state['fault'] and kind != 'none':
                state['delivered'] += 1
                if kind == 'runtime_warning':
                    warnings.warn('controlled public arithmetic warning', RuntimeWarning,
                                  stacklevel=1)
                elif kind == 'user_warning':
                    warnings.warn('controlled public unrelated warning', UserWarning,
                                  stacklevel=1)
                else:
                    raise error
        return original(*args, **kwargs)
    return invoke

# Finite instrumentation, NOT an exhaustive SVD-family or mathematical-role claim.
# Neither LAPACK adapters nor private helpers are controlled or selected.
if boundary == 'svd':
    for module in (np.linalg, scipy.linalg):
        for name in ('svd', 'svdvals', 'pinv', 'lstsq'):
            if hasattr(module, name):
                original = getattr(module, name)
                originals.append((module, name, original))
                setattr(module, name, control(original))
else:
    module, name = (np.fft, 'fftn') if boundary == 'fft' else (
        scipy.optimize, 'least_squares')
    assert boundary in ('fft', 'optimizer', 'no_optimizer')
    original = getattr(module, name)
    originals.append((module, name, original))
    setattr(module, name, control(original))

installed = [module.__name__ + '.' + name for module, name, _ in originals]
def measured(operation, fault, arrays, metadata_check):
    before = [(a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable)
              for a in arrays]
    row = {'phase': 'measured_public_operation', 'requested_fault': fault and kind != 'none'}
    state.update(active=False, fault=fault, calls=0, delivered=0)
    with np.errstate(all='raise'), warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter('ignore', RuntimeWarning)
        warnings.simplefilter('always', UserWarning)
        mode, filters = np.geterr(), list(warnings.filters)
        state['active'] = True
        result = None
        try:
            result = operation()
        except Exception as caught:
            row.update(outcome='exception', exception_type=type(caught).__name__,
                       message=str(caught), code=getattr(caught, 'code', None),
                       identical=caught is error, diagnostic=diagnostic(caught))
            if 'sr' in globals():
                row['domain_error'] = isinstance(caught, sr.SimreconError)
        else:
            row['outcome'] = 'normal'
        finally:
            state['active'] = False
        row['mode_preserved'] = np.geterr() == mode
        row['filters_preserved'] = warnings.filters == filters
        row['warnings'] = [{'category': w.category.__name__, 'message': str(w.message),
                            'filename': w.filename, 'lineno': w.lineno} for w in observed]
    row.update(calls=state['calls'], delivered=state['delivered'],
        inputs_preserved=before == [
            (a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable) for a in arrays],
        metadata_preserved=metadata_check())
    return row, result

report = {'schema': 'public-dependency-control.v2', 'api': api_name,
          'boundary': boundary, 'kind': kind, 'installed': installed}
if api_name in ('lapack_direct', 'lapack_selected'):
    assert boundary == 'svd'
    matrix = np.array([[1., 2.], [2., -1.], [0., 3.]])
    matrix.setflags(write=False)
    # A.T A=diag(5,14); signs of singular vectors are intentionally unspecified.
    routine = scipy.linalg.lapack.dgesdd if api_name == 'lapack_direct' else (
        scipy.linalg.get_lapack_funcs('gesdd', (matrix,)))
    def operation():
        return routine(matrix, compute_uv=1, full_matrices=0, overwrite_a=0)
    def scientific(result):
        u, singular, vt, info = result
        assert info == 0
        np.testing.assert_allclose(singular, np.sqrt([14., 5.]), atol=2e-14, rtol=2e-14)
        np.testing.assert_allclose((u * singular) @ vt, matrix, atol=3e-14, rtol=2e-14)
        np.testing.assert_allclose(u.T @ u, np.eye(2), atol=2e-14, rtol=0)
        np.testing.assert_allclose(vt @ vt.T, np.eye(2), atol=2e-14, rtol=0)
        return {'checked': True, 'info': int(info), 'singular': singular.tolist(),
                'reconstruction_error': float(np.max(np.abs((u * singular) @ vt-matrix)))}
    arrays = [matrix]
    metadata_check = lambda: True
else:
    # Controls precede BOTH product and fixture imports, and remain inactive here.
    import simrecon as sr
    sys.path.insert(0, 'tests')
    from observable_volume_phase_estimation_fixture import canonical, observe
    images = np.array([1., -.2, .5, -.4, .8, .1]).reshape(6, 1, 1, 1)
    phases = np.array([-2.7, -1.4, -.2, .9, 2.2, 2.9])
    values = np.array([1., .23+.08j, .11-.04j], dtype=np.complex128).reshape(3,1,1,1)
    # |c(phi)| >= 1-2|F1|-2|F2| > .27, so the nuisance rank cannot change.
    def prepare():
        frequencies = [np.arange(-(n//2), (n+1)//2)/n for n in images.shape[1:]]
        orders = sr.VolumeOrderOtf(values=values, fz_per_um=frequencies[0],
            fy_per_um=frequencies[1], fx_per_um=frequencies[2], voxel_size_um=(1.,1.,1.),
            origin_zyx=(0,0,0), source='supplied public dependency control')
        arrays = [images, phases, values, *frequencies]
        for array in arrays:
            array.setflags(write=False)
        metadata = (orders.voxel_size_um, orders.origin_zyx, orders.source)
        def metadata_check():
            return metadata == (orders.voxel_size_um, orders.origin_zyx, orders.source) and (
                orders.values is values and all(getattr(orders, name) is original
                for name, original in zip(('fz_per_um','fy_per_um','fx_per_um'),
                                          frequencies, strict=True)))
        def operation():
            return getattr(sr, api_name)(images, order_otf=orders, carrier_bins_yx=(0,0),
                initial_phases_rad=phases, max_nfev=1, gradient_tolerance=1e-9,
                step_tolerance=1e-10, source='public dependency control')
        def scientific(result):
            # Independent stored-input targets at the prescribed unadvanced point.
            truth = observe(images, values, (0,0), canonical(phases))
            np.testing.assert_allclose(result.phases_rad, canonical(phases), atol=2e-14, rtol=0)
            np.testing.assert_allclose(result.phasors, np.cos(phases)+1j*np.sin(phases),
                                       atol=2e-14, rtol=0)
            np.testing.assert_allclose(result.phase_deviations_rad, 0, atol=2e-14, rtol=0)
            np.testing.assert_allclose(result.specimen_normalized.ravel(), truth.u,
                                       atol=2e-11, rtol=2e-11)
            expected_singular = (np.zeros(images[0].size) if api_name == 'estimate_volume_phases'
                                 and not np.any(truth.mask) else truth.singular)
            np.testing.assert_allclose(result.nuisance_singular_values, expected_singular,
                                       atol=2e-11, rtol=2e-11)
            np.testing.assert_allclose(result.phase_singular_values, truth.phase_singular,
                                       atol=2e-11, rtol=2e-10)
            assert result.nuisance_rank == truth.rank
            assert result.phase_design_rank == truth.design_rank
            if truth.phase_singular[0] > 1e-9:
                assert result.phase_rank == truth.phase_rank
            for field, expected in (
                ('relative_residual', truth.relative), ('normalized_residual_rms', truth.rms),
                ('normalized_imaginary_rms', truth.imaginary),
                ('calibration_reality_defect', truth.defect),
                ('gradient_inf_norm', truth.gradient)):
                np.testing.assert_allclose(getattr(result,field), expected, atol=2e-11, rtol=2e-10)
            if api_name == 'estimate_observable_volume_phases':
                np.testing.assert_array_equal(result.observable_fourier_mask, truth.mask)
                assert result.observable_dimension == int(np.count_nonzero(truth.mask))
                assert result.unobservable_dimension == images[0].size-result.observable_dimension
            expected_termination = (('no_observable_specimen' if (
                 api_name == 'estimate_observable_volume_phases')
                 else 'nuisance_rank_deficient') if not np.any(truth.mask) else
                'nuisance_rank_deficient' if truth.rank < len(truth.singular) else
                'stationary' if truth.gradient <= 1e-9 else 'evaluation_limit')
            assert result.termination == expected_termination
            assert result.image_scale == (float(np.max(np.abs(images))) if np.any(images) else 1.)
            assert result.transfer_scale == (float(max(np.max(np.abs(values.real)),
                np.max(np.abs(values.imag)))) if np.any(values) else 1.)
            assert result.global_ambiguity == 'unassessed'
            assert result.carrier_bins_yx == (0,0) and result.source == 'public dependency control'
            assert result.nfev >= 0 and result.njev >= 0
            if not np.any(truth.mask):
                assert result.phase_rank == result.nuisance_rank == 0
                assert result.nuisance_singular_values.shape == expected_singular.shape
                np.testing.assert_array_equal(result.phase_singular_values, np.zeros(6))
                np.testing.assert_array_equal(result.specimen_normalized, 0)
                assert result.gradient_inf_norm == result.normalized_imaginary_rms == 0
            return {'checked': True, 'termination': result.termination,
                'rank': truth.rank, 'phase_rank': truth.phase_rank,
                'gradient': truth.gradient, 'condition':
                float(truth.singular[0]/truth.singular[-1]) if truth.rank == len(
                    truth.singular) and truth.rank else None,
                'allowance': truth.allowance, 'rms': truth.rms,
                'specimen': truth.u.tolist(), 'nuisance_singular': truth.singular.tolist()}
        return operation, scientific, arrays, metadata_check
    operation, scientific, arrays, metadata_check = prepare()

# Matched genuine pass-through companion in the same fresh interpreter.
baseline, result = measured(operation, False, arrays, metadata_check)
assert baseline['outcome'] == 'normal', baseline
baseline['science'] = scientific(result)
report['baseline'] = baseline
if boundary == 'no_optimizer':
    assert kind in ('zero','nonzero','deficient')
    assert baseline['calls'] >= 1 and baseline['science']['gradient'] > 1e-4
    if kind in ('zero','nonzero'):
        images = (np.arange(36, dtype=float).reshape(6,1,2,3)-18
                  if kind == 'nonzero' else np.zeros((6,1,2,3)))
        values = np.zeros((3,1,2,3), dtype=np.complex128)
    else:
        images = np.tile(np.array([[[1.,-.25]]]), (6,1,1,1))
        values = np.zeros((3,1,1,2), dtype=np.complex128)
        values[0,0,0] = [1,1]
        values[1,0,0,0] = -.5
        phases = np.zeros(6)
    operation, scientific, arrays, metadata_check = prepare()
    # Count only; no fault or synthetic solver output is needed for no-call proof.
    observed, result = measured(operation, False, arrays, metadata_check)
else:
    observed, result = measured(operation, kind != 'none', arrays, metadata_check)
if observed['outcome'] == 'normal':
    observed['science'] = scientific(result)
report['observed'] = observed
report['fault_evidence'] = ('delivered' if observed['delivered'] else
    'unexercised' if kind != 'none' and boundary != 'no_optimizer' else 'not_requested')
for module, name, original in originals:
    setattr(module, name, original)
print('SOLVER_PUBLIC_PROBE ' + json.dumps(report, sort_keys=True))
"""
