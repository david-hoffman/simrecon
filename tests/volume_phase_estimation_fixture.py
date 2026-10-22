"""Small independent spatial generator and dense Fourier observer for P01–P24.

No SIMrecon numerical routine supplies expected values.  Spatial generation uses
circular sums; the observer constructs each real matrix column by Fourier sums.
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from itertools import product
from math import lcm
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
# A genuine public callable bound before the child installs fault observers.
# Fingerprint arithmetic must not be mistaken for product dependency work.
_FINGERPRINT_SVD = np.linalg.svd


def canonical(phases: Any) -> Real:
    p = np.asarray(phases, dtype=np.float64)
    a = np.arctan2(np.sin(p), np.cos(p))
    return np.where(a == np.pi, -np.pi, a)


def powers(phases: Real) -> dict[int, Complex]:
    c, s = np.cos(phases), np.sin(phases)
    z = c + 1j * s
    z2 = (c * c - s * s) + 1j * ((2 * c) * s)
    return {0: np.ones_like(z), 1: z, 2: z2, -1: z.conj(), -2: z2.conj()}


def modes(shape: tuple[int, ...]) -> Real:
    return np.array(list(product(*(range(-(n // 2), (n + 1) // 2) for n in shape))))


def fourier_matrix(shape: tuple[int, ...]) -> Complex:
    coords = np.array(list(np.ndindex(shape)))
    period = lcm(*shape)
    cycles = (modes(shape).astype(int) * np.array([period // n for n in shape])) @ coords.T
    cycles %= period
    roots = np.exp(-2j * np.pi * (cycles / period))
    # Exact quarter-turn roots prevent a spurious unobserved coordinate in
    # deliberately rank-deficient/cutoff examples. No product FFT is involved.
    for quarter, root in enumerate((1, -1j, -1, 1j)):
        roots[4 * cycles == quarter * period] = root
    return roots / np.sqrt(np.prod(shape))


def transfer_from_kernels(kernels: Complex) -> Complex:
    shape = kernels.shape[1:]
    transform = fourier_matrix(shape) * np.sqrt(np.prod(shape))
    return np.stack([(transform @ row.ravel()).reshape(shape) for row in kernels])


def periodic_carrier(carrier: tuple[int, int], shape: tuple[int, ...]) -> tuple[int, int]:
    """Extract exact integers before reducing to small centered periodic bins.

    A mixed NumPy vector may round unsigned-sized and negative integers to
    float64. NumPy scalar multiplication can also overflow before reduction.
    Neither operation belongs before exact Python-integer periodic reduction.
    Keep the caller's original carrier separately for provenance assertions.
    """
    ky, kx = (int(value) % length for value, length in zip(carrier, shape[1:], strict=True))
    return (
        ky - shape[1] if ky > shape[1] // 2 else ky,
        kx - shape[2] if kx > shape[2] // 2 else kx,
    )


def record(values: Complex, origin: tuple[int, int, int] = (0, 0, 0)) -> Any:
    import simrecon

    shape = values.shape[1:]
    spacing = (0.5, 0.25, 0.125)
    freq = [
        np.arange(-(n // 2), (n + 1) // 2, dtype=np.float64) / n / d
        for n, d in zip(shape, spacing, strict=True)
    ]
    return simrecon.VolumeOrderOtf(
        values=values.copy(),
        fz_per_um=freq[0],
        fy_per_um=freq[1],
        fx_per_um=freq[2],
        voxel_size_um=spacing,
        origin_zyx=origin,
        source="independent kernels; origin already encoded",
    )


def spatial_images(
    specimen: Real, kernels: Complex, phases: Real, carrier: tuple[int, int]
) -> Real:
    """Circular convolution of carrier-modulated specimen, without any FFT."""
    shape = specimen.shape
    ky, kx = periodic_carrier(carrier, shape)
    coords = list(np.ndindex(shape))
    bands = np.zeros((3, *shape), dtype=np.complex128)
    for n in coords:
        for j in coords:
            displacement = tuple((a - b) % k for a, b, k in zip(n, j, shape, strict=True))
            cycles = ky * j[1] / shape[1] + kx * j[2] / shape[2]
            for m in range(3):
                bands[(m, *n)] += (
                    kernels[(m, *displacement)] * specimen[j] * np.exp(2j * np.pi * m * cycles)
                )
    z = powers(phases)
    return np.stack(
        [
            bands[0].real + 2 * (z[1][p] * bands[1] + z[2][p] * bands[2]).real
            for p in range(len(phases))
        ]
    )


@dataclass
class Example:
    """Independent specimen, calibration, observations and hidden phase truth."""

    images: Real
    initial: Real
    truth: Real
    specimen: Real
    kernels: Complex
    orders: Any
    carrier: tuple[int, int]


def example(group: int = 0, n: int = 7, uniform: bool = False) -> Example:
    """Two separately specified asymmetric all-order finite examples."""
    shape = (2, 3, 4) if group == 0 else (3, 1, 5)
    coords = np.indices(shape)
    if group == 0:
        h = np.zeros(shape)
        h[0, 0, 0], h[1, 0, 1], h[0, 2, 3] = 0.83, 0.11, 0.06
        g1 = np.array([0.22 + 0.13j, -0.16 + 0.09j])[:, None, None]
        g2 = np.array([-0.11 + 0.08j, 0.17 - 0.04j])[:, None, None]
        specimen = 0.4 + ((3 * coords[0] + 5 * coords[1] + 7 * coords[2]) % 11) / 9
        carrier = (1, -1)
        errors = np.array([0.028, -0.041, 0.017, 0.036, -0.023, 0.012, -0.032])[:n]
    else:
        h = np.zeros(shape)
        h[0, 0, 0], h[2, 0, 1], h[1, 0, 4] = 0.79, 0.14, 0.07
        g1 = np.array([0.19 - 0.12j, -0.07 + 0.16j, 0.10 + 0.09j])[:, None, None]
        g2 = np.array([0.13 + 0.07j, -0.09 - 0.03j, 0.06 - 0.12j])[:, None, None]
        specimen = 0.3 + ((2 * coords[0] + 3 * coords[2]) % 7) / 6
        carrier = (0, 1)
        errors = np.array([-0.019, 0.033, -0.027, 0.014, 0.039, -0.021, 0.008])[:n]
    if uniform:
        specimen = np.ones(shape)
    initial = np.linspace(-2.6, 2.5, n)
    truth = initial + errors
    kernels = np.array([h, h * g1, h * g2], dtype=np.complex128)
    images = spatial_images(specimen, kernels, truth, carrier)
    orders = record(
        transfer_from_kernels(kernels),
        origin=(shape[0] - 1, shape[1] - 1, shape[2] - 1),
    )
    return Example(images, initial, truth, specimen, kernels, orders, carrier)


@dataclass
class Observation:
    """All-sample stored-input expectations, independent of product output."""

    a: Real
    ap: list[Real]
    y: Real
    u: Real
    r: Real
    d: Real
    k: Real
    jac: Real
    nuisance_s: Real
    phase_s: Real
    nuisance_rank: int
    phase_rank: int
    design_rank: int
    b: float
    t: float
    relative: float
    rms: float
    imaginary: float
    reality: float
    gradient: float
    allowance: float


def observe(images: Real, values: Complex, phases: Real, carrier: tuple[int, int]) -> Observation:
    """Dense independent observer; QR solves full-rank fits, SVD only deficient fits.

    Signed negative rows are looked up by mode dictionaries, including Nyquist.
    Column j is the response to an independent real spatial unit impulse at j.
    """
    shape = images.shape[1:]
    n, size = len(phases), int(np.prod(shape))
    b = float(np.max(np.abs(images))) or 1.0
    t = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag)))) or 1.0
    f = values.real / t + 1j * (values.imag / t)
    transform = fourier_matrix(shape)
    y_complex = (images.reshape(n, size) / b) @ transform.T
    y = np.concatenate([y_complex.real.ravel(), y_complex.imag.ravel()])
    bins = modes(shape).astype(int)
    index = {
        tuple(int(kv) % length for kv, length in zip(k, shape, strict=True)): i
        for i, k in enumerate(bins)
    }
    ky, kx = periodic_carrier(carrier, shape)
    rows = f.reshape(3, size)
    z = powers(phases)
    model = np.zeros((n, size, size), dtype=np.complex128)
    derivative = np.zeros_like(model)
    for ki, k in enumerate(bins):
        for m in range(-2, 3):
            fm = rows[m, ki] if m >= 0 else rows[-m, index[tuple(-k % np.array(shape))]].conjugate()
            source = index[
                tuple(
                    (int(kv) - m * shift) % length
                    for kv, shift, length in zip(k, (0, ky, kx), shape, strict=True)
                )
            ]
            term = z[m][:, None] * fm * transform[source][None, :]
            model[:, ki, :] += term
            derivative[:, ki, :] += (1j * m) * term
    a = np.concatenate([model.real.reshape(n * size, size), model.imag.reshape(n * size, size)])
    ap: list[Real] = []
    for p in range(n):
        masked = np.zeros_like(derivative)
        masked[p] = derivative[p]
        ap.append(
            np.concatenate(
                [masked.real.reshape(n * size, size), masked.imag.reshape(n * size, size)]
            )
        )
    left, s, right = np.linalg.svd(a, full_matrices=False)
    rank = int(np.count_nonzero(s > np.finfo(float).eps * max(a.shape) * s[0]))
    if rank == size:
        q, triangular = np.linalg.qr(a, mode="reduced")
        plus = np.linalg.solve(triangular, q.T)
    else:
        plus = (right[:rank].T / s[:rank]) @ left[:, :rank].T
    u = plus @ y
    r = y - a @ u
    d = np.column_stack([v @ u for v in ap])
    k = d - a @ (plus @ d)
    jac = -k - np.column_stack([plus.T @ (v.T @ r) for v in ap])
    phase_s = np.linalg.svd(k, compute_uv=False)
    phase_rank = int(np.count_nonzero(phase_s > np.finfo(float).eps * max(k.shape) * phase_s[0]))
    c, si = np.cos(phases), np.sin(phases)
    design = np.column_stack([np.ones(n), c, si, c * c - si * si, (2 * c) * si])
    ds = np.linalg.svd(design, compute_uv=False)
    design_rank = int(np.count_nonzero(ds > np.finfo(float).eps * max(design.shape) * ds[0]))
    prediction = (a @ u)[n * size :]
    mirror = np.array([rows[0, index[tuple(-kv % np.array(shape))]].conjugate() for kv in bins])
    eps = np.finfo(float).eps
    allowance = float(
        2**20
        * len(y)
        * (size + n + 1)
        * eps
        * (1 + np.linalg.norm(y) + np.linalg.norm(u) + np.linalg.norm(d)) ** 2
    )
    return Observation(
        a,
        ap,
        y,
        u,
        r,
        d,
        k,
        jac,
        s,
        phase_s,
        rank,
        phase_rank,
        design_rank,
        b,
        t,
        float(np.linalg.norm(r) / np.linalg.norm(y)) if np.any(y) else 0.0,
        float(np.linalg.norm(r) / np.sqrt(n * size)),
        float(np.linalg.norm(prediction) / np.sqrt(n * size)),
        float(np.linalg.norm(rows[0] - mirror) / np.sqrt(size)),
        float(np.max(np.abs(jac.T @ r))),
        allowance,
    )


def estimate(api: Any, e: Example, **changes: Any) -> Any:
    args = dict(
        order_otf=e.orders,
        carrier_bins_yx=e.carrier,
        initial_phases_rad=e.initial,
        max_nfev=200,
        gradient_tolerance=1e-9,
        step_tolerance=1e-10,
        source=" specimen/calibration pairing ",
    )
    images = changes.pop("images", e.images)
    args.update(changes)
    return api(images, **args)


def calibrated_example(group: int = 0) -> tuple[Example, Any]:
    """Real caller: raw finite bead -> compensated response -> existing adapter."""
    import simrecon

    e = example(group)
    shape = e.specimen.shape
    # The all-odd group is required by the trilinear adapter's endpoint policy.
    if any(k % 2 == 0 for k in shape):
        raise ValueError("calibrated_example requires the odd group")
    profile = np.zeros(shape)
    profile[0, 0, 0], profile[-1, 0, 1] = 0.9, 0.1
    anchor = (1, 0, 2)
    bead = 30 * np.roll(profile, anchor, axis=(0, 1, 2))
    calibration_phases = np.array([-2.7, -1.8, -0.9, 0.1, 1.0, 1.9, 2.8])
    corrected = spatial_images(bead, e.kernels, calibration_phases, e.carrier)
    raw = 8 + 2 * corrected[None, ...]
    acquisition = simrecon.declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "counts",
        },
    )
    calibration = simrecon.calibrate_raw_finite_bead(
        acquisition,
        group={"orientation": 0},
        offset=8,
        response=2,
        output_unit="electrons",
        phases_rad=calibration_phases,
        voxel_size_um=e.orders.voxel_size_um,
        bead_profile=profile,
        calibration_carrier_bins=e.carrier,
        min_profile_transfer=0.5,
    )
    adapted = simrecon.adapt_empirical_volume_response_trilinear(
        calibration.response,
        target_shape_zyx=shape,
        target_voxel_size_um=e.orders.voxel_size_um,
        calibration_carrier_bins=e.carrier,
        specimen_carrier_bins=e.carrier,
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0,
        source="finite-bead calibration paired to independent specimen",
    )
    return e, adapted.orders


def local_phase_budget(e: Example, radius: float = 1e-4) -> tuple[float, float]:
    """Bound local phase error from gradient on a fixture-specific convex ball.

    For unit phase direction v, ||A'(v)||<=a1, ||A''(v,v)||<=a2.
    Weyl and the projector perturbation bound give s and k below. Differentiating
    the least-squares normal orthogonality gives the residual Hessian correction
    bound used in mu. This normal-equation identity is analysis, not a solver.
    The radius is a checked local-basin condition, never a universal accuracy.
    """
    o = observe(e.images, e.orders.values, canonical(e.truth), e.carrier)
    f = e.orders.values / o.t
    gain1, gain2 = float(np.max(np.abs(f[1]))), float(np.max(np.abs(f[2])))
    a1 = 2 * (gain1 + 2 * gain2) * (1 + 64 * np.finfo(float).eps)
    a2 = 2 * (gain1 + 4 * gain2) * (1 + 64 * np.finfo(float).eps)
    s = float(o.nuisance_s[-1]) - a1 * radius
    assert s > 0
    u0, r0 = float(np.linalg.norm(o.u)), float(np.linalg.norm(o.r))
    residual_bound = r0 + a1 * radius * u0 + 1e-12
    du = residual_bound / s
    u_bound = u0 + du
    k_change = a2 * radius * u0 + a1 * du + 2 * a1 * radius / s * a1 * u0
    k_lower = float(o.phase_s[-1]) - k_change
    assert k_lower > 0
    correction = (
        residual_bound * (a2 * u_bound + 2 * a1**2 * u_bound / s) + residual_bound**2 * a1**2 / s**2
    )
    mu = k_lower**2 - correction
    assert mu > 0
    # Product gradient <=1e-9; the separate tight observer check allows 5e-10
    # per reported infinity norm. Account for the independent stored-data
    # truth gradient and a further 1e-12 roundoff margin.
    budget = (np.sqrt(len(e.truth)) * (1e-9 + 5e-10) + np.linalg.norm(o.jac.T @ o.r) + 1e-12) / mu
    return float(budget), float(mu)


ORDER_FIELDS = (
    "values",
    "fz_per_um",
    "fy_per_um",
    "fx_per_um",
    "voxel_size_um",
    "origin_zyx",
    "source",
)


def copy_order_record(orders: Any, **changes: Any) -> Any:
    """Construct an OTF through its public fields, without record metadata."""
    import simrecon

    fields = {name: getattr(orders, name) for name in ORDER_FIELDS}
    fields.update(changes)
    return simrecon.VolumeOrderOtf(**fields)


def forward_observed_callbacks(
    original: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    replacements: dict[str, Any],
) -> Any:
    """Replace supplied callbacks while preserving the actual public call form.

    Signature defaults are useful for observation, but a decorated callable may
    not support replaying those defaults as positional arguments. Copy only the
    caller's supplied containers and replace callback values in their original
    slots. Never materialize defaults or move the remaining controls.
    """
    positional_names = [
        parameter.name
        for parameter in inspect.signature(original).parameters.values()
        if parameter.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    forwarded_args = list(args)
    forwarded_kwargs = kwargs.copy()
    for name, value in replacements.items():
        if name in forwarded_kwargs:
            forwarded_kwargs[name] = value
        elif name in positional_names and positional_names.index(name) < len(args):
            forwarded_args[positional_names.index(name)] = value
        else:
            raise AssertionError(f"observer callback {name} was not supplied")
    return original(*forwarded_args, **forwarded_kwargs)


@dataclass
class _PublicObservation:
    """Preimport public callables; only an explicit estimator region is armed."""

    handlers: dict[str, Any] = field(default_factory=dict)
    events: list[tuple[str, str]] = field(default_factory=list)

    def wrap(self, category: str, name: str, original: Any) -> Any:
        """Keep real dependency execution unless this category is armed."""

        @wraps(original)
        def call(*args: Any, **kwargs: Any) -> Any:
            handler = self.handlers.get(category)
            if handler is None:
                return original(*args, **kwargs)
            self.events.append((category, name))
            return handler(original, *args, **kwargs)

        return call


_PUBLIC_OBSERVATION: _PublicObservation | None = None
_CHILD_FLAG = "SIMRECON_PHASE_PUBLIC_OBSERVATION_CHILD"


def _install_preimport_observation() -> _PublicObservation:
    if any(name == "simrecon" or name.startswith("simrecon.") for name in sys.modules):
        raise RuntimeError("setup: public observation must precede SIMrecon import")
    import scipy.linalg
    import scipy.linalg.interpolative
    import scipy.linalg.lapack
    import scipy.optimize
    import scipy.sparse.linalg

    state = _PublicObservation()
    for module, names, category in (
        (np.fft, ("fftn",), "fft"),
        (scipy.optimize, ("least_squares",), "optimizer"),
        (np.linalg, ("svd", "svdvals", "lstsq"), "svd"),
        (scipy.linalg, ("svd", "svdvals", "lstsq"), "svd"),
        (scipy.linalg.interpolative, ("svd",), "svd"),
        (scipy.sparse.linalg, ("svds",), "svd"),
        (
            scipy.linalg.lapack,
            tuple(
                prefix + driver
                for prefix in "sdcz"
                for driver in ("gesdd", "gesvd", "gelsd", "gelss")
            ),
            "svd",
        ),
    ):
        for name in names:
            original = getattr(module, name, None)
            if callable(original):
                setattr(module, name, state.wrap(category, f"{module.__name__}.{name}", original))

    # Public LAPACK factories can return a function independently of the named
    # module attribute. Cover those handles without touching private symbols.
    factory_module: Any
    for factory_module in (scipy.linalg, scipy.linalg.lapack):
        original_factory = factory_module.get_lapack_funcs

        def factory(
            names: Any, *args: Any, _original: Any = original_factory, **kwargs: Any
        ) -> Any:
            functions = _original(names, *args, **kwargs)

            def selected(name: str, function: Any) -> Any:
                if name in {"gesdd", "gesvd", "gelsd", "gelss"}:
                    return state.wrap("svd", f"scipy.linalg.lapack.factory.{name}", function)
                return function

            if isinstance(names, str):
                return selected(names, functions)
            return type(functions)(
                selected(name, function) for name, function in zip(names, functions, strict=True)
            )

        factory_module.get_lapack_funcs = factory
    return state


@contextmanager
def public_observation(**handlers: Any) -> Iterator[_PublicObservation]:
    """Arm public observers only after fixture/oracle setup has completed."""
    state = _PUBLIC_OBSERVATION
    assert state is not None, "setup: use the isolated preimport dependency child"
    assert not state.handlers, "overlapping public observations are unsupported"
    state.events.clear()
    state.handlers.update(handlers)
    try:
        yield state
    finally:
        state.handlers.clear()


@dataclass
class NuisanceSvdFailure:
    """Raise only on an independently recognized nuisance decomposition.

    Recognition observes public matrix operands, never private call order or
    production factors. The positive spectrum is invariant under orthogonal
    organization; common scaling is removed. Nontrivial blocks can match a
    spectral subset. A scalar alone has no scale-free fingerprint and is not
    accepted as evidence of nuisance reachability.
    """

    singular_values: Real
    marker: BaseException
    passed_shapes: list[tuple[int, ...]] = field(default_factory=list)
    matched_shapes: list[tuple[int, ...]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Snapshot independent expected values before observation is armed."""
        expected = np.array(self.singular_values, dtype=np.float64, copy=True)
        assert expected.ndim == 1 and len(expected) > 1
        assert np.all(np.isfinite(expected)) and np.all(expected > 0)
        self.singular_values = np.sort(expected)[::-1] / np.max(expected)

    def _matches(self, matrix: Any) -> bool:
        if not isinstance(matrix, np.ndarray):
            # LinearOperator.matmat is public; support genuine sparse-SVD
            # callers without reading operator internals.
            if not hasattr(matrix, "shape") or not callable(getattr(matrix, "matmat", None)):
                return False
            matrix = matrix.matmat(np.eye(matrix.shape[1]))
        if matrix.ndim < 2 or matrix.dtype.kind not in "fc":
            return False
        expected = self.singular_values
        for block in matrix.reshape((-1, *matrix.shape[-2:])):
            scale = max(float(np.max(np.abs(block.real))), float(np.max(np.abs(block.imag))))
            if not scale or not np.isfinite(scale):
                continue
            bounded = block.real / scale + 1j * (block.imag / scale)
            actual = _FINGERPRINT_SVD(bounded, compute_uv=False)
            if not len(actual) or not actual[0]:
                continue
            actual = actual[actual > np.finfo(float).eps * max(block.shape) * actual[0]]
            if len(actual) < 2 or len(actual) > len(expected):
                continue
            actual = actual / actual[0]
            for anchor in range(len(expected) - len(actual) + 1):
                scaled = actual * expected[anchor]
                remaining = list(expected[anchor:])
                for value in scaled:
                    nearest = int(np.argmin(np.abs(np.array(remaining) - value)))
                    if abs(remaining[nearest] - value) > 2e-10:
                        break
                    remaining.pop(nearest)
                else:
                    return True
        return False

    def __call__(self, original: Any, *args: Any, **kwargs: Any) -> Any:
        """Pass other genuine decompositions; raise at a nuisance witness."""
        matrix = args[0] if args else kwargs.get("a", kwargs.get("A"))
        matched = self._matches(matrix)
        shape = tuple(getattr(matrix, "shape", ()))
        if matched:
            self.matched_shapes.append(shape)
            raise self.marker
        self.passed_shapes.append(shape)
        return original(*args, **kwargs)


def run_dependency_child(request: Any) -> bool:
    """Run one node after preimport setup in the committed fixture.

    The existing source-free wrapper owns child diagnostics and true status.
    No ignored author artifact is imported or executed by this test harness.
    """
    if os.environ.get(_CHILD_FLAG) == "1":
        assert _PUBLIC_OBSERVATION is not None
        return False
    import pytest

    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env[_CHILD_FLAG] = "1"
    env["PYTHONPATH"] = str(root / "tests") + os.pathsep + env.get("PYTHONPATH", "")
    bootstrap = (
        "import volume_phase_estimation_fixture; import pytest; import sys; "
        "raise SystemExit(pytest.main(sys.argv[1:]))"
    )
    command = [
        sys.executable,
        "-B",
        str(root / "scripts/source_free_check.py"),
        "--timeout",
        "60",
        "python",
        "-c",
        bootstrap,
        "--assert=plain",
        "--tb=line",
        "-q",
        "-x",
        request.node.nodeid,
    ]
    child = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=90)
    if child.returncode:
        pytest.fail(
            f"source-free dependency child status={child.returncode}\n"
            f"{child.stdout}\n{child.stderr}",
            pytrace=False,
        )
    return True


if os.environ.get(_CHILD_FLAG) == "1":
    _PUBLIC_OBSERVATION = _install_preimport_observation()
