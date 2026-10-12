"""Independent stored-input observers for the public point-bead composition."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]
D = Decimal
PRECISION = 110
PI = D(
    "3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651"
)
EPS = D.from_float(float.fromhex("0x1p-52"))
Q = D.from_float(float.fromhex("0x0.0000000000001p-1022"))
ACTUAL = np.array([0.13, 0.82, 1.91, 2.76, 3.64, 4.73, 5.81])
SPACING = (0.31, 0.17, 0.09)
CANONICAL = ("time", "channel", "orientation", "phase", "z", "y", "x")


def represented_matrix(phases: Array) -> Array:
    """Normative rounded basis entries; no product solver or output is used."""
    angles = np.empty(phases.shape, dtype=np.float64)
    angles[:] = phases
    c, s = np.cos(angles), np.sin(angles)
    return np.column_stack((np.ones(angles.size), c, s, c * c - s * s, (2 * c) * s))


def _solve(matrix: list[list[Decimal]], rhs: list[Decimal]) -> list[Decimal]:
    rows = [row.copy() + [value] for row, value in zip(matrix, rhs, strict=True)]
    for col in range(5):
        pivot = max(range(col, 5), key=lambda r: abs(rows[r][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        assert scale != 0, "Observer requires a full-rank phase matrix"
        rows[col] = [v / scale for v in rows[col]]
        for r in range(5):
            if r != col:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col], strict=True)]
    return [rows[r][-1] for r in range(5)]


def fit_stored(images: Array, phases: Array) -> tuple[list[list[Decimal]], Decimal]:
    """110-digit normal equations are an observer, never the production solver."""
    h = represented_matrix(phases)
    assert np.linalg.cond(h) <= 10, "Only informative-regime budgets are claimed"
    with localcontext() as ctx:
        ctx.prec = PRECISION
        hd = [[D.from_float(float(v)) for v in row] for row in h]
        gram = [[sum((row[i] * row[j] for row in hd), D(0)) for j in range(5)] for i in range(5)]
        converted = np.asarray(images, dtype=np.float64).reshape(len(phases), -1)
        result: list[list[Decimal]] = [[] for _ in range(5)]
        for column in converted.T:
            b = [D.from_float(float(v)) for v in column]
            rhs = [sum((row[j] * v for row, v in zip(hd, b, strict=True)), D(0)) for j in range(5)]
            a, b1, c1, b2, c2 = _solve(gram, rhs)
            for row, value in zip(result, (a, b1 / 2, -c1 / 2, b2 / 2, -c2 / 2), strict=True):
                row.append(value)
        error = max(coordinate_budgets(images, phases))
        return result, error


def coordinate_budgets(images: Array, phases: Array) -> list[Decimal]:
    """Per-voxel native-input intensity budgets; no global-brightness dilution."""
    converted = np.asarray(images, dtype=np.float64).reshape(len(phases), -1)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        return [
            D(8192) * len(phases) * EPS * D.from_float(float(np.max(np.abs(column)))) + 8 * Q
            for column in converted.T
        ]


@cache
def root(turns: Fraction) -> tuple[Decimal, Decimal]:
    """Negative-exponent Fourier root from independent high-precision series."""
    with localcontext() as ctx:
        ctx.prec = PRECISION
        reduced = turns % 1
        if reduced > Fraction(1, 2):
            reduced -= 1
        x = -2 * PI * D(reduced.numerator) / D(reduced.denominator)
        cosine, sine = D(1), x
        ct, st = D(1), x
        for n in range(1, 190):
            ct *= -(x * x) / D((2 * n - 1) * (2 * n))
            st *= -(x * x) / D((2 * n) * (2 * n + 1))
            cosine += ct
            sine += st
            if abs(ct) + abs(st) < D("1e-108"):
                break
        else:
            raise AssertionError("Fourier observer series did not converge")
        return +cosine, +sine


@dataclass
class Oracle:
    """Independent expectations and contract-derived absolute budgets."""

    coordinates: list[list[Decimal]]
    component_error: Decimal
    coordinate_errors: list[Decimal]
    values: Array
    budgets: Array
    origin: tuple[int, int, int]
    frequencies: tuple[list[Fraction], list[Fraction], list[Fraction]]
    exact_mass: Decimal


def observe(images: Array, phases: Array, spacing: Any) -> Oracle:
    """Fit represented observations, choose observed peak, sum every signed bin."""
    shape = images.shape[1:]
    sites = list(product(*(range(n) for n in shape)))
    coordinates, error = fit_stored(images, phases)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        dc = coordinates[0]
        peak = max(range(len(dc)), key=dc.__getitem__)
        sorted_dc = sorted(dc, reverse=True)
        assert dc[peak] > 0
        if len(dc) > 1:
            assert sorted_dc[0] - sorted_dc[1] > 2 * error
        mass = sum(dc, D(0))
        count = D(len(dc))
        assert mass > count * error, "A stable positive-mass oracle is required"
        peak_site = sites[peak]
        origin = (peak_site[0], peak_site[1], peak_site[2])
        values = np.empty((3, *shape), dtype=np.complex128)
        budgets = np.empty((3, *shape), dtype=np.float64)
        modes = [list(range(-(n // 2), (n + 1) // 2)) for n in shape]
        for order in range(3):
            re = coordinates[0 if order == 0 else 2 * order - 1]
            im = [D(0)] * len(dc) if order == 0 else coordinates[2 * order]
            sample_error = error if order == 0 else D(2).sqrt() * error
            absolute_sum = sum((abs(a) + abs(b) for a, b in zip(re, im, strict=True)), D(0))
            lam = (absolute_sum + 2 * count * sample_error) / (mass - count * error)
            inherited = 512 * count * EPS * lam + 16 * count * Q
            for index in product(*(range(n) for n in shape)):
                mode = tuple(modes[a][index[a]] for a in range(3))
                real, imag = D(0), D(0)
                for j, site in enumerate(sites):
                    turns = sum(
                        (Fraction(mode[a] * (site[a] - origin[a]), shape[a]) for a in range(3)),
                        Fraction(0),
                    )
                    cosine, sine = root(turns)
                    real += re[j] * cosine - im[j] * sine
                    imag += re[j] * sine + im[j] * cosine
                real, imag = real / mass, imag / mass
                magnitude_bound = abs(real) + abs(imag)
                propagated = (count * sample_error + magnitude_bound * count * error) / (
                    mass - count * error
                )
                observer = 4 * EPS * magnitude_bound + Q + D("1e-90") * (1 + lam)
                values[(order, *index)] = complex(float(real), float(imag))
                budgets[(order, *index)] = float(propagated + inherited + observer)
        frequencies: list[list[Fraction]] = []
        for n, d, axis_modes in zip(shape, spacing, modes, strict=True):
            step = Fraction.from_float(float(d))
            frequencies.append([Fraction(k) / (n * step) for k in axis_modes])
        return Oracle(
            coordinates,
            error,
            coordinate_budgets(images, phases),
            values,
            budgets,
            origin,
            (frequencies[0], frequencies[1], frequencies[2]),
            mass,
        )


def assert_frequency_axis(actual: Array, expected: list[Fraction]) -> None:
    """Exact rational error/bound in cycles/um; no rounded expectation slack."""
    assert type(actual) is np.ndarray
    assert actual.dtype == np.dtype(np.float64)
    assert actual.shape == (len(expected),)
    assert np.all(np.isfinite(actual))
    eps = Fraction.from_float(float(EPS))
    quantum = Fraction.from_float(float(Q))
    for value, exact in zip(actual, expected, strict=True):
        error = abs(Fraction.from_float(float(value)) - exact)
        assert error <= 8 * eps * abs(exact) + quantum
        if exact != 0:
            assert value != 0
    assert actual[len(actual) // 2] == 0
    assert np.all(np.diff(actual) > 0)


def assert_observation(result: Any, oracle: Oracle) -> None:
    """Budgets constrain real fitted coordinates and complex Fourier errors."""
    components = result.components
    # Oracle dimensions come from supplied images, never the returned record.
    shape = oracle.values.shape[1:]
    for component in (components.dc, components.c1, components.c2):
        assert component.shape == shape
    assert result.response.values.shape == (3, *shape)
    actual = (
        components.dc,
        components.c1.real,
        components.c1.imag,
        components.c2.real,
        components.c2.imag,
    )
    for observed, expected in zip(actual, oracle.coordinates, strict=True):
        with localcontext() as ctx:
            ctx.prec = PRECISION
            for value, exact, error in zip(
                observed.ravel(), expected, oracle.coordinate_errors, strict=True
            ):
                observer_error = (abs(exact) + error) * D("1e-90")
                assert abs(D.from_float(float(value)) - exact) <= (error + observer_error)
    assert result.response.origin_zyx == oracle.origin
    assert np.all(np.abs(result.response.values - oracle.values) <= oracle.budgets)
    center = tuple(n // 2 for n in shape)
    assert result.response.values[(0, *center)] == 1 + 0j
    for actual_axis, expected_axis in zip(
        (result.response.fz_per_um, result.response.fy_per_um, result.response.fx_per_um),
        oracle.frequencies,
        strict=True,
    ):
        assert_frequency_axis(actual_axis, expected_axis)


def kernel(shape: tuple[int, int, int]) -> Array:
    """Asymmetric, nonseparable admissible detection kernel; unique peak at zero."""
    h = np.array(
        [
            1 + ((11 * z + 7 * y + 3 * x + 5 * y * x) % 13)
            for z, y, x in product(*(range(n) for n in shape))
        ],
        dtype=np.float64,
    ).reshape(shape)
    h[(0, 0, 0)] = 61
    return h / h.sum()


def physical_images(
    phases: Array,
    *,
    shape: tuple[int, int, int] = (2, 3, 4),
    bead: tuple[int, int, int] = (1, 2, 3),
    brightness: float = 128.0,
    orientation: int = 0,
) -> Array:
    """Squared-field forward generator; physical truth never enters calibration."""
    h = np.roll(kernel(shape), bead, axis=(0, 1, 2))
    z = np.arange(shape[0])[:, None, None]
    axial = 2 * np.pi * (z - bead[0]) / shape[0]
    lateral = 2 * np.pi * ((orientation + 1) * bead[1] / shape[1] + bead[2] / shape[2])
    a0, plus, minus = 1 + 0.2j, 0.47 - 0.31j, -0.26 + 0.39j
    power = abs(a0) ** 2 + abs(plus) ** 2 + abs(minus) ** 2
    rows = []
    for phase in phases:
        theta = lateral + phase
        field = a0 * np.exp(1j * axial) + plus * np.exp(1j * theta) + minus * np.exp(-1j * theta)
        rows.append(brightness * h * np.abs(field) ** 2 / power)
    return np.array(rows)


def forward_images(
    dc: Array, *, phases: Array = ACTUAL, c1: Array | None = None, c2: Array | None = None
) -> Array:
    c1 = np.zeros_like(dc, dtype=np.complex128) if c1 is None else c1
    c2 = np.zeros_like(dc, dtype=np.complex128) if c2 is None else c2
    h = represented_matrix(phases)
    coordinates = np.stack(
        (dc, 2 * np.real(c1), -2 * np.imag(c1), 2 * np.real(c2), -2 * np.imag(c2))
    )
    return np.einsum("pj,jzyx->pzyx", h, coordinates)


def converted_correction(raw: Array, offset: Any, response: Any) -> Array:
    """Two rounded operations; distinguishes correction order and conversion."""
    with np.errstate(all="ignore"):
        numerator = np.asarray(raw, dtype=np.float64) - np.asarray(offset, dtype=np.float64)
        return numerator / np.asarray(response, dtype=np.float64)
