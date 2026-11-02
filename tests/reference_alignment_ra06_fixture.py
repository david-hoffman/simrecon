"""Independent finite-sum, real-coordinate RA06 observer (no product helpers)."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from itertools import product
from typing import Any

import numpy as np

D = Decimal
PRECISION = 70
PI = D("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
EPS = 2.0**-52


def dec(value: Any) -> Decimal:
    return D.from_float(float(value))


def matrix(value: Any) -> np.ndarray:
    return np.array([dec(v) for v in np.asarray(value).flat], dtype=object).reshape(np.shape(value))


def solve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pivoted elimination at observer precision, including multiple right sides."""
    n = len(a)
    rhs = b.reshape(n, -1).copy()
    aug = np.concatenate((a.copy(), rhs), axis=1)
    for k in range(n):
        pivot = max(range(k, n), key=lambda j: abs(aug[j, k]))
        if not aug[pivot, k]:
            raise ArithmeticError("singular independent observer system")
        aug[[k, pivot]] = aug[[pivot, k]]
        aug[k, k:] = aug[k, k:] / aug[k, k]
        for j in range(n):
            if j != k:
                aug[j, k:] = aug[j, k:] - aug[j, k] * aug[k, k:]
    return aug[:, n:].reshape(b.shape)


def identity(n: int) -> np.ndarray:
    return matrix(np.eye(n))


def phasor(turns: Decimal) -> tuple[Decimal, Decimal]:
    """70-digit Taylor sums; argument reduced in exact rational turns."""
    turns = turns % D(1)
    if turns > D("0.5"):
        turns -= 1
    angle = 2 * PI * turns
    cosine = term_c = D(1)
    sine = term_s = angle
    for k in range(1, 150):
        term_c *= -(angle * angle) / D((2 * k - 1) * (2 * k))
        term_s *= -(angle * angle) / D((2 * k) * (2 * k + 1))
        cosine += term_c
        sine += term_s
        if abs(term_c) + abs(term_s) < D("1e-75"):
            break
    return cosine, sine


def bins(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(product(*(range(-(n // 2), (n + 1) // 2) for n in shape)))


def pixels(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(product(*(range(n) for n in shape)))


def fourier(shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    real = np.empty((int(np.prod(shape)),) * 2, dtype=object)
    imag = np.empty_like(real)
    for j, q in enumerate(bins(shape)):
        for k, v in enumerate(pixels(shape)):
            turns = sum((D(a * b) / D(n) for a, b, n in zip(q, v, shape, strict=True)), D(0))
            real[j, k], imag[j, k] = phasor(turns)
    return real, imag


def design(phases: np.ndarray) -> np.ndarray:
    """Build the normative represented basis, without exact-real trigonometry."""
    p = np.asarray(phases, dtype=np.float64)
    c, s = np.cos(p), np.sin(p)
    return np.stack(
        (np.ones_like(c), 2 * c, -2 * s, 2 * (c * c - s * s), -2 * ((2 * c) * s)), axis=-1
    )


@dataclass
class Case:
    """Only public caller values; transfers are raw arrays until API invocation."""

    images: np.ndarray
    phases: np.ndarray
    carriers: np.ndarray
    gains: np.ndarray
    transfers: np.ndarray
    covariance: np.ndarray
    alpha: float
    out: tuple[int, int]
    taper: np.ndarray
    spacing: tuple[float, float, float] = (0.7, 0.4, 0.25)

    @property
    def detector(self) -> tuple[int, int, int]:
        return self.images.shape[-3:]

    @property
    def output(self) -> tuple[int, int, int]:
        return (self.detector[0], *self.out)

    def arguments(self) -> dict[str, Any]:
        # Public record construction only. Positional fields avoid inferring private helpers.
        from simrecon import VolumeOrderOtf

        frequencies = [
            np.array([float(D(q[0]) / (D(n) * dec(d))) for q in bins((n,))], dtype=np.float64)
            for n, d in zip(self.detector, self.spacing, strict=True)
        ]
        records = tuple(
            VolumeOrderOtf(
                values.copy(),
                frequencies[0].copy(),
                frequencies[1].copy(),
                frequencies[2].copy(),
                self.spacing,
                (self.detector[0] - 1, self.detector[1] - 1, self.detector[2] - 1),
                f"independent-ra06-{r}",
            )
            for r, values in enumerate(self.transfers)
        )
        return {
            "order_otfs": records,
            "phases_rad": self.phases,
            "carriers_bins": self.carriers,
            "gains": self.gains,
            "exposure_covariance": self.covariance,
            "regularization": self.alpha,
            "output_shape_yx": self.out,
            "apodization": self.taper,
        }


def case(
    detector: tuple[int, int, int] = (1, 1, 3),
    carriers: tuple[tuple[int, int], ...] = ((0, 0),),
    n: int = 7,
    alpha: float = 0.17,
) -> Case:
    r = len(carriers)
    m = int(np.prod(detector))
    p = np.array([0.12, 0.91, 2.07, 3.16, 4.51, 5.34, 0.12, 2.83, 5.91])[:n]
    phases = np.stack([p + 0.13 * j for j in range(r)])
    images = (np.arange(r * n * m).reshape(r, n, *detector) % 17 - 8) / 7
    transfers = np.empty((r, 3, *detector), dtype=np.complex128)
    index = np.arange(m).reshape(detector)
    for j in range(r):
        for order in range(3):
            transfers[j, order] = (0.35 + 0.04 * index + 0.07 * order) + 1j * (
                -0.21 + 0.03 * index - 0.02 * j + 0.06 * order
            )
    covariance = []
    for j in range(r):
        lower = np.eye(n) + np.tril(np.full((n, n), 0.035 * (j + 1)), -1)
        raw = lower @ np.diag(np.linspace(0.7, 1.8, n)) @ lower.T
        covariance.append((raw + raw.T) / 2)
    cy = max(abs(v[0]) for v in carriers)
    cx = max(abs(v[1]) for v in carriers)
    out = (detector[1] + 4 * cy, detector[2] + 4 * cx)
    return Case(
        images.astype(float),
        phases,
        np.array(carriers, dtype=np.int64),
        np.linspace(0.8, 1.3, r),
        transfers,
        np.array(covariance),
        alpha,
        out,
        np.ones((detector[0], *out)),
    )


def real_map(c: Case) -> tuple[np.ndarray, np.ndarray]:
    """Assemble h and A by independent finite synthesis of each real source delta."""
    det_r, det_i = fourier(c.detector)
    out_r, out_i = fourier(c.output)
    out_lookup = {q: i for i, q in enumerate(bins(c.output))}
    r, n = c.phases.shape
    m, p = int(np.prod(c.detector)), int(np.prod(c.output))
    h = np.full((r, 5, m, p), D(0), dtype=object)
    for orientation in range(r):
        for order in range(3):
            for j, mode in enumerate(bins(c.detector)):
                q = (
                    mode[0],
                    mode[1] - order * int(c.carriers[orientation, 0]),
                    mode[2] - order * int(c.carriers[orientation, 1]),
                )
                qi = out_lookup[q]
                transfer = c.transfers[orientation, order].flat[j]
                tr = dec(c.gains[orientation]) * dec(transfer.real) / D(p)
                ti = dec(c.gains[orientation]) * dec(transfer.imag) / D(p)
                for v in range(m):
                    for k in range(p):
                        # exp(+j.v) * exp(-q.k): no detector divisor in synthesis.
                        er = det_r[j, v] * out_r[qi, k] + det_i[j, v] * out_i[qi, k]
                        ei = det_i[j, v] * out_r[qi, k] - det_r[j, v] * out_i[qi, k]
                        re, im = tr * er - ti * ei, tr * ei + ti * er
                        if order == 0:
                            h[orientation, 0, v, k] += re
                        else:
                            h[orientation, 2 * order - 1, v, k] += re
                            h[orientation, 2 * order, v, k] += im
    k_design = matrix(design(c.phases))
    a = np.stack([k_design[j] @ h[j].reshape(5, -1) for j in range(r)])
    return h, a.reshape(r * n * m, p)


@dataclass
class Oracle:
    """Retain independent expectations and pre-observation numerical budgets."""

    x: np.ndarray
    spectrum: np.ndarray
    a: np.ndarray
    normal: np.ndarray
    rhs: np.ndarray
    coordinates: np.ndarray
    covariance: np.ndarray
    predicted: np.ndarray
    residual: np.ndarray
    data_objective: float
    penalty_objective: float
    separated_objective: float
    constant: float
    rank: int
    singular: np.ndarray
    tolerance: float
    objective_tolerance: float


def observe(c: Case) -> Oracle:
    """70-digit weighted normal solve, before any reconstruction is observed."""
    with localcontext() as context:
        context.prec = PRECISION
        h, a = real_map(c)
        r, n = c.phases.shape
        m, p = int(np.prod(c.detector)), int(np.prod(c.output))
        y = matrix(c.images).reshape(r, n, m)
        k = matrix(design(c.phases))
        weights = [solve(matrix(c.covariance[j]), identity(n)) for j in range(r)]
        psi, z, constant = [], [], D(0)
        normal, rhs = np.full((p, p), D(0), dtype=object), np.full(p, D(0), dtype=object)
        for j in range(r):
            metric = k[j].T @ weights[j] @ k[j]
            covariance = solve(metric, identity(5))
            coordinates = solve(metric, k[j].T @ weights[j] @ y[j])
            psi.append(covariance)
            z.append(coordinates)
            off = y[j] - k[j] @ coordinates
            constant += np.sum(off * (weights[j] @ off)) / D(m)
            aj = a[j * n * m : (j + 1) * n * m].reshape(n, m, p)
            for v in range(m):
                normal += aj[:, v].T @ weights[j] @ aj[:, v] / D(m)
                rhs += aj[:, v].T @ weights[j] @ y[j, :, v] / D(m)
        normal += dec(c.alpha) * identity(p) / D(p)
        # Singular alpha=0 examples use analytic expectations, not this solve.
        x = solve(normal, rhs)
        predicted = (a @ x).reshape(r, n, m)
        residual = y - predicted
        data = sum(
            (np.sum(residual[j] * (weights[j] @ residual[j])) / D(m) for j in range(r)), D(0)
        )
        penalty = dec(c.alpha) * np.sum(x * x) / D(p)
        separated = D(0)
        for j in range(r):
            diff = z[j] - (h[j].reshape(5 * m, p) @ x).reshape(5, m)
            separated += np.sum(diff * solve(psi[j], diff)) / D(m)
        fr, fi = fourier(c.output)
        spectrum = (np.asarray(fr @ x, float) - 1j * np.asarray(fi @ x, float)) / p
        af = np.asarray(a, float)
        whitened = np.concatenate(
            [
                np.linalg.solve(
                    np.linalg.cholesky(np.asarray(c.covariance[j], float)),
                    af[j * n * m : (j + 1) * n * m].reshape(n, -1),
                ).reshape(n * m, p)
                for j in range(r)
            ]
        ) * np.sqrt(p / m)
        singular = np.linalg.svd(whitened, compute_uv=False)
        cutoff = EPS * max(r * n * m, p) * singular[0]
        rank = int(np.count_nonzero(singular > cutoff))
        # Prior budget: backward-error allowance times augmented-system condition squared.
        low = c.alpha + (singular[-1] ** 2 if len(singular) == p else 0)
        condition_squared = (singular[0] ** 2 + c.alpha) / low
        scale = max(1.0, float(np.max(np.abs(c.images))), float(np.max(np.abs(x))))
        tolerance = 8192 * EPS * max(r * n * m, p) * condition_squared * scale
        objective_scale = max(1.0, float(data + penalty), float(np.max(np.abs(af))))
        objective_tolerance = tolerance * 64 * max(1, p) * objective_scale
        assert 0 < tolerance < 0.001, "fixture must keep a useful prior discriminator"
        assert abs(data - separated - constant) < D("1e-55")
        return Oracle(
            np.asarray(x, float).reshape(c.output),
            spectrum.reshape(c.output),
            af,
            np.asarray(normal, float),
            np.asarray(rhs, float),
            np.asarray(z, float).reshape(r, 5, *c.detector),
            np.asarray(psi, float),
            np.asarray(predicted, float).reshape(c.images.shape),
            np.asarray(residual, float).reshape(c.images.shape),
            float(data),
            float(penalty),
            float(separated),
            float(constant),
            rank,
            singular,
            tolerance,
            objective_tolerance,
        )


def synthesize(spectrum: np.ndarray) -> np.ndarray:
    with localcontext() as context:
        context.prec = PRECISION
        fr, fi = fourier(spectrum.shape)
        re, im = matrix(np.real(spectrum).ravel()), matrix(np.imag(spectrum).ravel())
        return (
            np.asarray(fr.T @ re - fi.T @ im, float) + 1j * np.asarray(fi.T @ re + fr.T @ im, float)
        ).reshape(spectrum.shape)


def matched_case(variance: float = 0.6) -> Case:
    c = case(detector=(1, 1, 3), n=5, alpha=0.23)
    c.transfers[:] = 0
    c.transfers[:, 0] = 0.7
    c.transfers[:, 1] = 0.4
    c.transfers[:, 2] = 0.3
    k = design(c.phases)[0]
    psi = np.diag([variance, variance / 2, variance / 2, variance / 2, variance / 2])
    raw = k @ psi @ k.T
    c.covariance[0] = (raw + raw.T) / 2
    return c
