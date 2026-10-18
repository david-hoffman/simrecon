"""Small direct-sum observers for the contracted Fourier-block estimator.

These deliberately dense independent observers are not production algorithms.
All internal frequency labels are modular; public records use centered storage.
"""

from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from simrecon import VolumeOrderOtf, estimate_observable_volume_phases

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
PHASES = np.array([-2.7, -1.81, -0.62, 0.23, 1.39, 2.52])
EPS = 2.0**-52


def canonical(phases: Real) -> Real:
    """Use the public native-angle convention."""
    angles = np.arctan2(np.sin(phases), np.cos(phases))
    return np.where(angles == np.pi, -np.pi, angles)


def dft(shape: tuple[int, ...]) -> Complex:
    """Construct the unitary negative-exponent transform by finite sums."""
    sites = np.array(list(np.ndindex(shape)))
    return np.exp(-2j * np.pi * ((sites / np.array(shape)) @ sites.T)) / np.sqrt(len(sites))


def partition(shape: tuple[int, ...], carrier: tuple[int, int]) -> list[list[int]]:
    """Find the smallest shift-and-conjugation closed sets, including dark rows."""
    sites = list(np.ndindex(shape))
    lookup = {site: i for i, site in enumerate(sites)}
    shift = (0, carrier[0] % shape[1], carrier[1] % shape[2])
    unseen = set(range(len(sites)))
    blocks = []
    while unseen:
        pending = [min(unseen)]
        found: set[int] = set()
        while pending:
            i = pending.pop()
            if i in found:
                continue
            found.add(i)
            site = sites[i]
            for neighbor in (
                tuple((a + e) % n for a, e, n in zip(site, shift, shape, strict=True)),
                tuple(-a % n for a, n in zip(site, shape, strict=True)),
            ):
                pending.append(lookup[neighbor])
        unseen -= found
        blocks.append(sorted(found))
    return blocks


def signed(values: Complex) -> dict[int, Complex]:
    """Reflect negative orders on all three modular axes."""
    shape = values.shape[1:]
    negative = tuple(np.ix_(*(np.array([-i % n for i in range(n)]) for n in shape)))
    return {
        -2: values[2][negative].conj().ravel(),
        -1: values[1][negative].conj().ravel(),
        0: values[0].ravel(),
        1: values[1].ravel(),
        2: values[2].ravel(),
    }


def model(
    values: Complex, carrier: tuple[int, int], phases: Real
) -> tuple[Complex, list[Complex], NDArray[np.bool_]]:
    """Assemble each five-order Fourier coefficient and its phase derivative."""
    shape = values.shape[1:]
    sites = list(np.ndindex(shape))
    lookup = {site: i for i, site in enumerate(sites)}
    msize, nphase = len(sites), len(phases)
    c, s = np.cos(phases), np.sin(phases)
    z = c + 1j * s
    z2 = (c * c - s * s) + 1j * ((2 * c) * s)
    powers = {-2: z2.conj(), -1: z.conj(), 0: np.ones_like(z), 1: z, 2: z2}
    g = np.zeros((nphase * msize, msize), dtype=np.complex128)
    derivatives = [np.zeros_like(g) for _ in phases]
    visible = np.zeros(msize, dtype=np.bool_)
    shift = (0, carrier[0] % shape[1], carrier[1] % shape[2])
    for k, site in enumerate(sites):
        for order, transfer in signed(values).items():
            j = lookup[
                tuple((a - order * e) % n for a, e, n in zip(site, shift, shape, strict=True))
            ]
            visible[j] |= transfer[k].real != 0 or transfer[k].imag != 0
            for p in range(nphase):
                coefficient = powers[order][p] * transfer[k]
                g[p * msize + k, j] += coefficient
                derivatives[p][p * msize + k, j] += 1j * order * coefficient
    mask = visible.copy()
    for i, site in enumerate(sites):
        opposite = lookup[tuple(-a % n for a, n in zip(site, shape, strict=True))]
        mask[i] |= visible[opposite]
    return g, derivatives, mask


def hermitian_basis(shape: tuple[int, ...], mask: NDArray[np.bool_]) -> Complex:
    """Give pairs two unit real coordinates and self-conjugate modes one."""
    sites = list(np.ndindex(shape))
    lookup = {site: i for i, site in enumerate(sites)}
    columns = []
    for i, site in enumerate(sites):
        j = lookup[tuple(-a % n for a, n in zip(site, shape, strict=True))]
        if not mask[i] or j < i:
            continue
        column = np.zeros(len(sites), dtype=np.complex128)
        if j == i:
            column[i] = 1
            columns.append(column)
        else:
            column[[i, j]] = 1 / np.sqrt(2)
            columns.append(column)
            column = np.zeros(len(sites), dtype=np.complex128)
            column[i], column[j] = 1j / np.sqrt(2), -1j / np.sqrt(2)
            columns.append(column)
    return np.column_stack(columns) if columns else np.zeros((len(sites), 0), complex)


def realify(array: Complex) -> Real:
    """Stack real and imaginary observations without discarding any row."""
    return np.concatenate((array.real, array.imag), axis=0)


@dataclass
class Case:
    """Independent caller inputs, with modular transfer storage."""

    images: Real
    values: Complex
    carrier: tuple[int, int]
    initial: Real

    def orders(self) -> VolumeOrderOtf:
        """Build the public record with unit micrometre voxel spacing."""
        shape = self.values.shape[1:]
        frequencies = [(np.arange(n) - n // 2) / n for n in shape]
        return VolumeOrderOtf(
            values=np.fft.fftshift(self.values, axes=(1, 2, 3)).copy(),
            fz_per_um=frequencies[0],
            fy_per_um=frequencies[1],
            fx_per_um=frequencies[2],
            voxel_size_um=(1.0, 1.0, 1.0),
            origin_zyx=tuple(n - 1 for n in shape),
            source="independent block algebra; origin already encoded",
        )

    def kwargs(self, budget: int = 1) -> dict[str, Any]:
        """Supply every required estimator keyword, with no hidden truth."""
        return dict(
            order_otf=self.orders(),
            carrier_bins_yx=self.carrier,
            initial_phases_rad=self.initial,
            max_nfev=budget,
            gradient_tolerance=1e-9,
            step_tolerance=1e-10,
            source="FOURIER-BLOCK-PHASE independent public witness",
        )

    def estimate(self, budget: int = 1) -> Any:
        """Call only the real public estimator."""
        return estimate_observable_volume_phases(self.images, **self.kwargs(budget))


def coupled_case(dark: bool = False) -> Case:
    """Generate unequal axial blocks, five signed orders and off-model data."""
    shape = (3, 2, 4)
    sites = np.array(list(np.ndindex(shape)))
    index = np.arange(len(sites))
    values = np.empty((3, *shape), dtype=np.complex128)
    strength = np.array([1.0, 0.43, 0.71])[sites[:, 0]]
    for order, gain in enumerate((1.0, 0.23, 0.12)):
        values[order] = (
            strength
            * gain
            * (1 + 0.12 * np.cos(0.7 * index + order))
            * np.exp(1j * (0.13 * index + 0.21 * order))
        ).reshape(shape)
    carrier = (0, 2)
    if dark:
        values.reshape(3, -1)[:, partition(shape, carrier)[-1]] = 0
    # Truth generates data only; it is never an estimator input or expectation
    # for a phase-accuracy claim. Re(predict) deliberately makes this off-model.
    specimen = 1.2 + 0.4 * np.sin(0.6 * index) + 0.2 * np.cos(0.31 * index**2)
    actual = PHASES + np.array([0.08, -0.11, 0.05, 0.13, -0.07, -0.04])
    forward, _, _ = model(values, carrier, actual)
    transform = dft(shape)
    fourier_prediction = (forward @ (transform @ specimen)).reshape(len(PHASES), -1)
    prediction = (fourier_prediction @ transform.conj()).ravel()
    noise = 0.035 * np.sin(np.arange(len(prediction)) * 0.41)
    images = (prediction.real + noise).reshape((len(PHASES), *shape))
    return Case(images, values, carrier, PHASES.copy())


@dataclass
class Profile:
    """Independent global-cutoff target and its block contributions."""

    specimen: Real
    singular: Real
    rank: int
    residual: Real
    jacobian: Real
    information: Real
    phase_singular: Real
    mask: NDArray[np.bool_]
    basis: Complex
    design: Real
    data: Real
    prediction: Complex
    block_rows: list[NDArray[np.int64]]
    local_ranks: list[int]
    block_singular: list[Real]
    image_scale: float
    transfer_scale: float


def profile(case: Case, phases: Real) -> Profile:
    """Factor explicit small blocks, then apply one global strict cutoff."""
    shape = case.values.shape[1:]
    msize = case.images[0].size
    nphase = len(phases)
    image_scale = float(np.max(np.abs(case.images))) or 1.0
    transfer_scale = (
        max(float(np.max(np.abs(case.values.real))), float(np.max(np.abs(case.values.imag)))) or 1.0
    )
    values = np.empty_like(case.values)
    with np.errstate(under="ignore"):
        values.real = case.values.real / transfer_scale
        values.imag = case.values.imag / transfer_scale
    g, gp, mask = model(values, case.carrier, phases)
    t = hermitian_basis(shape, mask)
    b = realify(g @ t)
    bp = [realify(item @ t) for item in gp]
    spectrum = (dft(shape) @ (case.images / image_scale).reshape(nphase, msize).T).T
    y = realify(spectrum.ravel())
    factors = []
    block_rows = []
    block_singular = []
    for block in partition(shape, case.carrier):
        rows = np.array([p * msize + k for p in range(nphase) for k in block])
        rows = np.concatenate((rows, rows + nphase * msize))
        columns = np.flatnonzero(np.any(t[block] != 0, axis=0))
        matrix = b[np.ix_(rows, columns)]
        u, s, vh = np.linalg.svd(matrix, full_matrices=False)
        factors.append((rows, columns, u, s, vh))
        block_rows.append(rows)
        block_singular.append(s)
    singular = np.sort(np.concatenate(block_singular))[::-1]
    cutoff = EPS * len(y) * (singular[0] if singular.size else 0)
    inverse = np.zeros((t.shape[1], len(y)))
    local_ranks = []
    for rows, columns, u, s, vh in factors:
        keep = s > cutoff
        local_ranks.append(int(np.count_nonzero(s > EPS * len(rows) * (s[0] if s.size else 0))))
        inverse[np.ix_(columns, rows)] = (vh[keep].T / s[keep]) @ u[:, keep].T
    v = inverse @ y
    residual = y - b @ v
    d = np.column_stack([item @ v for item in bp])
    information = d - b @ (inverse @ d)
    correction = np.column_stack([inverse.T @ item.T @ residual for item in bp])
    jacobian = -information - correction
    specimen_complex = dft(shape).conj().T @ (t @ v)
    # Hermitian coordinates lift to real space without changing predictions.
    assert np.linalg.norm(specimen_complex.imag) <= 2e-13 * (1 + np.linalg.norm(v))
    return Profile(
        specimen_complex.real.reshape(shape),
        singular,
        int(np.count_nonzero(singular > cutoff)),
        residual,
        jacobian,
        information,
        np.linalg.svd(information, compute_uv=False),
        mask,
        t,
        b,
        y,
        (g @ t @ v).reshape(nphase, msize),
        block_rows,
        local_ranks,
        block_singular,
        image_scale,
        transfer_scale,
    )


def independent_fit(case: Case, budget: int, *, projected_only: bool = False) -> Any:
    """Run the contracted real SciPy solve with independent residuals/Jacobians."""

    def jacobian(phases: Real) -> Real:
        point = profile(case, phases)
        return -point.information if projected_only else point.jacobian

    return least_squares(
        lambda phases: profile(case, phases).residual,
        canonical(case.initial),
        jac=cast(Any, jacobian),
        method="trf",
        bounds=(-np.inf, np.inf),
        loss="linear",
        x_scale=1,
        tr_solver="exact",
        ftol=cast(Any, None),
        gtol=1e-9,
        xtol=1e-10,
        max_nfev=budget,
    )


def growing_global_cutoff_case(multiplier: float) -> Case:
    """Give a varying strong DC block and a constant weak Nyquist block.

    The two singular values are norm(1+cos(phi)) and sqrt(6)*w.
    Choosing w relative to the initial global cutoff separates a later
    cross-block rank loss from the retained-availability companion.
    """
    initial = canonical(PHASES.copy())
    values = np.zeros((3, 1, 1, 4), dtype=np.complex128)
    values[0, 0, 0, 0] = 1
    values[1, 0, 0, 0] = 0.5
    values[0, 0, 0, 2] = multiplier * EPS * 48 * np.linalg.norm(1 + np.cos(initial)) / np.sqrt(6)
    return Case(np.ones((6, 1, 1, 4)), values, (0, 0), initial)


def cutoff_growth_trajectory(case: Case) -> tuple[list[tuple[Real, Profile]], Any]:
    """Observe real independent solver trials, stopping only on global rank loss."""
    visits: list[tuple[Real, Profile]] = []

    class RankLoss(Exception):
        pass

    def residual(phases: Real) -> Real:
        point = profile(case, phases)
        visits.append((phases.copy(), point))
        if point.rank != 2:
            raise RankLoss("independent same-point global cutoff loses nuisance rank")
        return point.residual

    try:
        result = least_squares(
            residual,
            case.initial,
            jac=cast(Any, lambda phases: profile(case, phases).jacobian),
            method="trf",
            bounds=(-np.inf, np.inf),
            loss="linear",
            x_scale=1,
            tr_solver="exact",
            ftol=cast(Any, None),
            gtol=1e-9,
            xtol=1e-10,
            max_nfev=200,
        )
    except RankLoss:
        return visits, None
    return visits, result
