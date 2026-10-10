"""Independent stored-input least squares and finite sums; no product oracle."""

from decimal import Decimal as D
from decimal import localcontext
from functools import cache
from itertools import product
from typing import Any

import numpy as np

PI = D(
    "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
)
ZERO = (D(0), D(0))
Pair = tuple[D, D]


def decimal(value: Any) -> D:
    return D.from_float(float(value))


def add(a: Pair, b: Pair) -> Pair:
    return a[0] + b[0], a[1] + b[1]


def mul(a: Pair, b: Pair) -> Pair:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def conj(a: Pair) -> Pair:
    return a[0], -a[1]


def scale(a: Pair, b: D) -> Pair:
    return a[0] * b, a[1] * b


@cache
def root(turns: D, precision: int) -> Pair:
    """Taylor root at rational turns; precision is part of the cache key."""
    with localcontext() as ctx:
        ctx.prec = precision + 12
        turns %= 1
        if turns > D("0.5"):
            turns -= 1
        if turns < D("-0.5"):
            turns += 1
        x = 2 * PI * turns
        cosine, sine = D(1), x
        ct, st = D(1), x
        for n in range(1, 250):
            ct *= -x * x / D((2 * n - 1) * (2 * n))
            st *= -x * x / D((2 * n) * (2 * n + 1))
            cosine += ct
            sine += st
            if max(abs(ct), abs(st)) < D(10) ** (-precision - 8):
                break
        return cosine, sine


def modes(size: int) -> range:
    # Exact Python arithmetic avoids fixed-width negation and endpoint overflow.
    size = int(size)
    return range(-(size // 2), (size + 1) // 2)


def basis(phases: Any) -> Any:
    # On this host equal-width longdouble can survive np.array(dtype=float64) as 'g'.
    # Build from Python binary64 scalars to ensure native 'd' trigonometric operations.
    phi = np.fromiter((float(v) for v in phases), dtype=np.float64, count=len(phases))
    c, s = np.cos(phi), np.sin(phi)
    return np.column_stack((np.ones(len(phi)), c, s, c * c - s * s, (2 * c) * s))


def solve(matrix: list[list[D]], rhs: list[D]) -> list[D]:
    """Pivoted Decimal elimination, independent of product SVD/NumPy linalg."""
    rows = [row[:] + [value] for row, value in zip(matrix, rhs, strict=True)]
    n = len(rows)
    for col in range(n):
        pivot = max(range(col, n), key=lambda j: abs(rows[j][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        assert divisor != 0, "oracle requires full-rank represented phase matrix"
        rows[col] = [value / divisor for value in rows[col]]
        for j in range(n):
            if j != col:
                factor = rows[j][col]
                rows[j] = [a - factor * b for a, b in zip(rows[j], rows[col], strict=True)]
    return [row[-1] for row in rows]


def coordinates(images: Any, phases: Any) -> dict[tuple[int, ...], tuple[Pair, Pair, Pair]]:
    h = [[decimal(v) for v in row] for row in basis(phases)]
    gram = [[sum((row[i] * row[j] for row in h), D(0)) for j in range(5)] for i in range(5)]
    result = {}
    for x in np.ndindex(images.shape[1:]):
        b = [decimal(images[(p, *x)]) for p in range(len(h))]
        rhs = [
            sum((row[i] * value for row, value in zip(h, b, strict=True)), D(0)) for i in range(5)
        ]
        a, b1, c1, b2, c2 = solve(gram, rhs)
        result[x] = ((a, D(0)), (b1 / 2, -c1 / 2), (b2 / 2, -c2 / 2))
    return result


def direct_oracle(
    case: dict[str, Any], precision: int = 70, *, decimal_output: bool = False
) -> tuple[Any, Any]:
    """Evaluate the exact represented LS estimator with independent finite DFT sums."""
    with localcontext() as ctx:
        ctx.prec = precision
        images = np.array(case["images"], dtype=np.float64)
        r_count, _, nz, ny, nx = images.shape
        detector = (nz, ny, nx)
        output = (nz, *map(int, case["output_shape_yx"]))
        q_modes = list(product(*(modes(k) for k in output)))
        numerator = dict.fromkeys(q_modes, ZERO)
        denominator = dict.fromkeys(q_modes, D(0))
        for r in range(r_count):
            spatial = coordinates(images[r], case["phases_rad"][r])
            record = case["order_otfs"][r]
            gain = decimal(case["gains"][r])
            cy, cx = map(int, case["carriers_bins"][r])
            for m in (-2, -1, 0, 1, 2):
                for j in product(*(modes(k) for k in detector)):
                    q = (j[0], j[1] - m * cy, j[2] - m * cx)
                    assert q in numerator, "fixture output window must retain all bands"
                    d = ZERO
                    for x, bands in spatial.items():
                        band = bands[abs(m)]
                        if m < 0:
                            band = conj(band)
                        turns = -sum(
                            D(jj) * D(xx) / D(k) for jj, xx, k in zip(j, x, detector, strict=True)
                        )
                        d = add(d, mul(band, root(turns, precision)))
                    d = scale(d, D(1) / D(nz * ny * nx))
                    lookup = j
                    if m < 0:
                        lookup = tuple(
                            ((-jj + k // 2) % k) - k // 2 for jj, k in zip(j, detector, strict=True)
                        )
                    index = tuple(jj + k // 2 for jj, k in zip(lookup, detector, strict=True))
                    e = record.values[(abs(m), *index)]
                    t = scale((decimal(e.real), decimal(e.imag)), gain)
                    if m < 0:
                        t = conj(t)
                    numerator[q] = add(numerator[q], mul(conj(t), d))
                    denominator[q] += t[0] ** 2 + t[1] ** 2
        spectrum = np.empty(output, dtype=object if decimal_output else np.complex128)
        exact = {}
        ridge = decimal(case["regularization"])
        for q in q_modes:
            index = tuple(j + k // 2 for j, k in zip(q, output, strict=True))
            den = denominator[q] + ridge
            value = scale(numerator[q], D(1) / den) if den > 0 else ZERO
            value = scale(value, decimal(case["apodization"][index]))
            exact[q] = value
            spectrum[index] = value if decimal_output else complex(float(value[0]), float(value[1]))
        volume = np.empty(output, dtype=object if decimal_output else np.complex128)
        for x in np.ndindex(output):
            value = ZERO
            for q, coefficient in exact.items():
                turns = sum(D(jj) * D(xx) / D(k) for jj, xx, k in zip(q, x, output, strict=True))
                value = add(value, mul(coefficient, root(turns, precision)))
            volume[x] = value if decimal_output else complex(float(value[0]), float(value[1]))
        return spectrum, volume


def accuracy_bounds(case: dict[str, Any]) -> tuple[D, D]:
    with localcontext() as ctx:
        ctx.prec = 90
        r, n, nz, ny, nx = case["images"].shape
        ly, lx = map(int, case["output_shape_yx"])
        j, m, p = D(5 * r), D(nz * ny * nx), D(int(nz * ly * lx))
        b = max(decimal(abs(v)) for v in np.array(case["images"], dtype=np.float64).flat)
        eps, tiny = D(2) ** -52, D(2) ** -1074
        beta = 65536 * j * (D(n) + m) * eps * b + 256 * j * (D(n) + m) * tiny
        return beta, p * beta + 16384 * j * p * eps * b + 64 * p * tiny


def condition_upper(phases: Any) -> D:
    """Bound represented-H conditioning using a high-precision SVD residual observer."""
    with localcontext() as ctx:
        ctx.prec = 90
        h = basis(phases)
        u, singular, vt = np.linalg.svd(h, full_matrices=False)
        hd = [[decimal(v) for v in row] for row in h]
        ud = [[decimal(v) for v in row] for row in u]
        vd = [[decimal(v) for v in row] for row in vt]
        sd = [decimal(v) for v in singular]
        assert len(sd) == 5
        u_defect = sum(
            (
                (sum((row[i] * row[j] for row in ud), D(0)) - D(int(i == j))) ** 2
                for i in range(5)
                for j in range(5)
            ),
            D(0),
        ).sqrt()
        v_defect = sum(
            (
                (sum((vd[i][k] * vd[j][k] for k in range(5)), D(0)) - D(int(i == j))) ** 2
                for i in range(5)
                for j in range(5)
            ),
            D(0),
        ).sqrt()
        residual = sum(
            (
                (hd[i][j] - sum((ud[i][k] * sd[k] * vd[k][j] for k in range(5)), D(0))) ** 2
                for i in range(len(hd))
                for j in range(5)
            ),
            D(0),
        ).sqrt()
        assert max(u_defect, v_defect) < 1
        largest = max(sd) * ((1 + u_defect) * (1 + v_defect)).sqrt() + residual
        smallest = min(sd) * ((1 - u_defect) * (1 - v_defect)).sqrt() - residual
        assert smallest > 0
        # Guard Decimal observer rounding; fixture margins are many orders larger.
        return largest / smallest + D("1e-60")


def assert_informative_regime(case: dict[str, Any]) -> None:
    """Check sufficient accuracy conditions for these fixtures, never product rejection rules."""
    with localcontext() as ctx:
        ctx.prec = 90
        images = np.array(case["images"], dtype=np.float64)
        r_count, n, nz, ny, nx = images.shape
        detector = (nz, ny, nx)
        output = (nz, *map(int, case["output_shape_yx"]))
        denominator = dict.fromkeys(product(*(modes(k) for k in output)), D(0))
        for r in range(r_count):
            assert condition_upper(case["phases_rad"][r]) <= 10
            gain = decimal(case["gains"][r])
            assert D("0.5") <= gain <= 2
            values = case["order_otfs"][r].values
            assert max(abs(decimal(v)) for v in values.real.flat) <= 1
            assert max(abs(decimal(v)) for v in values.imag.flat) <= 1
            cy, cx = map(int, case["carriers_bins"][r])
            for m in (-2, -1, 0, 1, 2):
                for j in product(*(modes(k) for k in detector)):
                    q = (j[0], j[1] - m * cy, j[2] - m * cx)
                    lookup = (
                        j
                        if m >= 0
                        else tuple(
                            ((-jj + k // 2) % k) - k // 2 for jj, k in zip(j, detector, strict=True)
                        )
                    )
                    index = tuple(jj + k // 2 for jj, k in zip(lookup, detector, strict=True))
                    e = values[(abs(m), *index)]
                    denominator[q] += (gain * decimal(e.real)) ** 2 + (gain * decimal(e.imag)) ** 2
        ridge = decimal(case["regularization"])
        assert 0 <= ridge <= 1
        assert all(v + ridge == 0 or v + ridge >= D("0.25") for v in denominator.values())
        j_count, m_count = D(5 * r_count), D(nz * ny * nx)
        p_count = D(int(nz * output[1] * output[2]))
        b = max(decimal(abs(v)) for v in images.flat)
        assert 65536 * j_count * (D(n) + m_count + p_count) * D(2) ** -52 <= D(2) ** -10
        assert 64 * j_count * p_count * max(b, D(2) ** -1074) <= decimal(np.finfo(float).max)


def assert_complex_error(actual: Any, expected: Pair, budget: D) -> None:
    """Compare complex modulus in Decimal without complex-magnitude overflow."""
    with localcontext() as ctx:
        ctx.prec = 90
        assert budget.is_finite() and budget > 0
        assert np.isfinite(actual.real) and np.isfinite(actual.imag)
        error = (
            (decimal(actual.real) - expected[0]) ** 2 + (decimal(actual.imag) - expected[1]) ** 2
        ).sqrt()
        assert error <= budget


def assert_phase_accuracy(images: Any, phases: Any, separated: Any) -> None:
    """Use the prerequisite's per-real-coordinate stored-input budget."""
    with localcontext() as ctx:
        ctx.prec = 90
        assert condition_upper(phases) <= 10
        converted = np.array(images, dtype=np.float64)
        exact = coordinates(converted, phases)
        for x, bands in exact.items():
            b = max(decimal(abs(converted[(p, *x)])) for p in range(len(phases)))
            budget = 8192 * D(len(phases)) * D(2) ** -52 * b + 8 * D(2) ** -1074
            actual = (
                separated.dc[x],
                separated.c1[x].real,
                separated.c1[x].imag,
                separated.c2[x].real,
                separated.c2[x].imag,
            )
            expected = (bands[0][0], bands[1][0], bands[1][1], bands[2][0], bands[2][1])
            for got, want in zip(actual, expected, strict=True):
                assert abs(decimal(got) - want) <= budget


def effective_order_mode(psf: Any, axial: Any, mode: tuple[int, int, int]) -> Pair:
    """Independent stored-kernel direct sum for the origin-zero composition fixture."""
    with localcontext() as ctx:
        ctx.prec = 90
        mass = sum((decimal(v) for v in psf.flat), D(0))
        value = ZERO
        for x in np.ndindex(psf.shape):
            g = axial[x[0]]
            kernel = scale((decimal(g.real), decimal(g.imag)), decimal(psf[x]) / mass)
            turns = -sum(D(j) * D(v) / D(k) for j, v, k in zip(mode, x, psf.shape, strict=True))
            value = add(value, mul(kernel, root(turns, 90)))
        return value


def make_record(
    values: Any, spacing: Any = (0.7, 1.3, 0.4), origin: Any = None, source: str = "opaque"
) -> Any:
    from simrecon import VolumeOrderOtf

    shape = values.shape[1:]
    vectors = []
    with localcontext() as ctx:
        ctx.prec = 90
        for k, d in zip(shape, spacing, strict=True):
            vectors.append(np.array([float(D(j) / D(k) / decimal(d)) for j in modes(k)]))
    return VolumeOrderOtf(
        values=values,
        fz_per_um=vectors[0],
        fy_per_um=vectors[1],
        fx_per_um=vectors[2],
        voxel_size_um=spacing,
        origin_zyx=origin or (0, 0, 0),
        source=source,
    )


def make_case(
    shape: tuple[int, int, int] = (2, 3, 4), carriers: Any = ((1, -1), (-1, 1)), n: int = 7
) -> dict[str, Any]:
    carriers = np.array(carriers, dtype=np.int64)
    r = len(carriers)
    phases = np.tile(np.array([0.05, 0.82, 1.9, 2.71, 3.48, 4.65, 5.61])[:n], (r, 1))
    images = np.empty((r, n, *shape))
    x = np.arange(np.prod(shape)).reshape(shape)
    for orientation in range(r):
        h = basis(phases[orientation])
        coeff = np.stack(
            (1 + x / 32, (x % 3 - 1) / 8, (x % 5 - 2) / 16, (x % 7 - 3) / 32, (x % 4 - 1) / 16)
        )
        images[orientation] = (
            np.einsum("pi,izyx->pzyx", h, coeff)
            + (orientation + 1) * np.arange(n)[:, None, None, None] ** 2 / 1024
        )
    records = []
    for orientation in range(r):
        idx = np.arange(3 * np.prod(shape)).reshape((3, *shape))
        values = (0.6 + (idx % 5) / 40 + 1j * ((idx % 7) - 3) / 32) * np.exp(0.17j * orientation)
        records.append(
            make_record(
                values.astype(np.complex128),
                origin=(shape[0] - 1, 0, shape[2] - 1),
                source=" label with whitespace ",
            )
        )
    ly = shape[1] + 4 * max(abs(int(v)) for v in carriers[:, 0])
    lx = shape[2] + 4 * max(abs(int(v)) for v in carriers[:, 1])
    mask = np.linspace(0.1, 1, shape[0] * ly * lx).reshape(shape[0], ly, lx)
    return dict(
        images=images,
        order_otfs=records,
        phases_rad=phases,
        carriers_bins=carriers,
        gains=np.linspace(0.75, 1.5, r),
        # Unobserved output modes have V=0: this ridge keeps the fixture informative.
        regularization=0.5,
        output_shape_yx=(ly, lx),
        apodization=mask,
    )


def call(reconstruct: Any, case: dict[str, Any]) -> Any:
    return reconstruct(
        case["images"], **{key: value for key, value in case.items() if key != "images"}
    )


def input_arrays(case: dict[str, Any]) -> list[Any]:
    arrays = [
        case[key]
        for key in ("images", "phases_rad", "carriers_bins", "gains", "apodization")
        if isinstance(case[key], np.ndarray)
    ]
    for record in case["order_otfs"]:
        if hasattr(record, "values"):
            arrays.extend(
                getattr(record, key)
                for key in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
                if isinstance(getattr(record, key), np.ndarray)
            )
    return arrays
