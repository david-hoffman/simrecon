"""Exact carrier-orbit variable projection with block-local nuisance storage."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_phase_estimation import (
    _EPS,
    _SOLVER,
    Complex,
    Real,
    _dependency,
    _finite,
    _Point,
    _powers,
    _Profile,
    _RankChanged,
    _svd,
)


@dataclass
class _Block:
    """One closed frequency set and its real Hermitian coordinates."""

    indices: npt.NDArray[np.intp]
    basis: Complex
    operators: Complex
    coordinates: slice
    rows: npt.NDArray[np.intp]


def _blocks(
    signed: list[Complex], carrier: tuple[int, int], shape: tuple[int, int, int], n: int
) -> tuple[npt.NDArray[np.bool_], list[_Block]]:
    """Partition all frequencies before constructing any dense numeric block."""
    size = int(np.prod(shape))
    cy, cx = carrier[0] % shape[1], carrier[1] % shape[2]
    visible = np.zeros(shape, dtype=np.bool_)
    for m, row in zip(range(-2, 3), signed, strict=True):
        visible |= np.roll((row.real != 0) | (row.imag != 0), (-m * cy, -m * cx), (1, 2))
    sites = np.array(list(np.ndindex(shape)), dtype=np.intp)
    opposite = np.asarray(np.ravel_multi_index(tuple((-sites % shape).T), shape)).ravel()
    mask = visible.ravel() | visible.ravel()[opposite]
    shift = np.asarray(
        np.ravel_multi_index(tuple(((sites + (0, cy, cx)) % shape).T), shape)
    ).ravel()
    seen = np.zeros(size, dtype=np.bool_)
    blocks = []
    offset = 0
    for seed in range(size):
        if seen[seed]:
            continue
        pending = [seed]
        found = []
        seen[seed] = True
        while pending:
            j = pending.pop()
            found.append(j)
            for neighbor in (shift[j], opposite[j]):
                if not seen[neighbor]:
                    seen[neighbor] = True
                    pending.append(int(neighbor))
        indices = np.array(sorted(found), dtype=np.intp)
        lookup = {int(j): i for i, j in enumerate(indices)}
        dimension = int(np.count_nonzero(mask[indices]))
        basis = np.zeros((len(indices), dimension), dtype=np.complex128)
        column = 0
        for i, j in enumerate(indices):
            k = opposite[j]
            if not mask[j] or k < j:
                continue
            if k == j:
                basis[i, column] = 1
                column += 1
            else:
                other = lookup[int(k)]
                amplitude = 1 / np.sqrt(2.0)
                basis[i, column] = basis[other, column] = amplitude
                basis[i, column + 1] = 1j * amplitude
                basis[other, column + 1] = -1j * amplitude
                column += 2
        operators = np.empty((5, len(indices), dimension), dtype=np.complex128)
        for order, row in zip(range(-2, 3), signed, strict=True):
            sources = np.asarray(
                np.ravel_multi_index(
                    tuple(((sites[indices] - (0, order * cy, order * cx)) % shape).T), shape
                )
            ).ravel()
            local = np.array([lookup[int(j)] for j in sources], dtype=np.intp)
            operators[order + 2] = row.ravel()[indices, None] * basis[local]
        rows = (np.arange(2 * n)[:, None] * size + indices).ravel()
        blocks.append(_Block(indices, basis, operators, slice(offset, offset + dimension), rows))
        offset += dimension
    return np.fft.fftshift(mask.reshape(shape)), blocks


class _BlockProfile(_Profile):
    """Share evaluator accounting and one optimizer across exact local factors."""

    def __init__(
        self,
        signed: list[Complex],
        carrier: tuple[int, int],
        shape: tuple[int, int, int],
        y: Real,
        n: int,
    ) -> None:
        self.mask, self.blocks = _blocks(signed, carrier, shape, n)
        self.shape = shape
        self.y = y
        self.n = n
        self.size = int(np.prod(shape))
        self.dimension = int(np.count_nonzero(self.mask))
        self.nfev = 0
        self.njev = 0
        self.require_full_rank = False
        self.cached_phases = None
        self.cached_point = None

    def point(self, phases: Real) -> _Point:
        """Factor locally, choose the same-point global cutoff, then assemble."""
        if self.cached_phases is not None and np.array_equal(phases, self.cached_phases):
            assert self.cached_point is not None
            return self.cached_point
        _finite(phases, code=_SOLVER)
        powers = _powers(phases)
        factors = []
        for block in self.blocks:
            dimension = block.basis.shape[1]
            if not dimension:
                continue
            model = np.einsum("mp,mkj->pkj", powers, block.operators)
            derivative = np.einsum(
                "mp,mkj->pkj", (1j * np.arange(-2, 3))[:, None] * powers, block.operators
            )
            a = np.concatenate(
                (model.real.reshape(-1, dimension), model.imag.reshape(-1, dimension))
            )
            _finite(a, derivative)
            left, singular, right = _svd(a)
            factors.append((block, a, derivative, left, singular, right))
        singular = np.sort(np.concatenate([item[4] for item in factors]))[::-1].copy()
        cutoff = _EPS * (2 * self.n * self.size) * singular[0]
        rank = int(np.count_nonzero(singular > cutoff))
        if self.require_full_rank and rank != self.dimension:
            raise _RankChanged
        specimen = np.empty(self.dimension)
        residual = self.y.copy()
        information = np.zeros((len(self.y), self.n))
        jacobian = np.zeros_like(information)
        imaginary = np.zeros(self.n * self.size)
        for block, a, derivative, left, local_s, right in factors:
            local_rank = int(np.count_nonzero(local_s > cutoff))
            plus = (right[:local_rank].T / local_s[:local_rank]) @ left[:, :local_rank].T
            v = plus @ self.y[block.rows]
            prediction = a @ v
            r = self.y[block.rows] - prediction
            c = len(block.indices)
            d_complex = derivative @ v
            d = np.zeros((2 * self.n * c, self.n))
            ap_r = np.empty((len(v), self.n))
            for p in range(self.n):
                rr = slice(p * c, (p + 1) * c)
                ir = slice((self.n + p) * c, (self.n + p + 1) * c)
                d[rr, p], d[ir, p] = d_complex[p].real, d_complex[p].imag
                ap_r[:, p] = derivative[p].real.T @ r[rr] + derivative[p].imag.T @ r[ir]
            k = d - a @ (plus @ d)
            j = -k - plus.T @ ap_r
            _finite(plus, v, prediction, r, d, k, j)
            specimen[block.coordinates] = v
            residual[block.rows] = r
            information[block.rows] = k
            jacobian[block.rows] = j
            imaginary[block.rows[self.n * c :] - self.n * self.size] = prediction[self.n * c :]
        point = _Point(specimen, residual, jacobian, information, singular, rank, imaginary)
        self.cached_phases, self.cached_point = phases.copy(), point
        return point

    def lift(self, specimen: Real) -> Real:
        """Lift Hermitian coordinates using one unitary inverse transform."""
        spectrum = np.zeros(self.size, dtype=np.complex128)
        for block in self.blocks:
            spectrum[block.indices] = block.basis @ specimen[block.coordinates]
        code = "volume_phase_estimation_transform_failure"
        with _dependency(code):
            spatial = np.fft.ifftn(spectrum.reshape(self.shape), norm="ortho")
        if (
            not isinstance(spatial, np.ndarray)
            or spatial.shape != self.shape
            or spatial.dtype.kind not in "fc"
        ):
            raise SimreconError(code, "unusable inverse transform result")
        _finite(spatial, code=code)
        return spatial.real.ravel().copy()
