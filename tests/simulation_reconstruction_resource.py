"""Algebraic resource witness; explicit standalone execution, stdout evidence only.

No full-size allocation occurs on import. See A/report.md for the error model,
proof limits and coordinator commands. Runtime is reached only through public APIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import product
from typing import Any, cast

import numpy as np

from volume_reconstruction_fixture import root

Mode = tuple[int, int, int]
Pair = tuple[F, F]
ZERO: Pair = (F(0), F(0))
SIZES = {
    "small": (4, 8, 8),
    "stage32": (8, 32, 32),
    "stage128": (16, 128, 128),
    "full": (64, 512, 512),
}
PHASES = (0.0, 0.75, 2.0, 3.5, 5.0)
GAINS = (0.5, 1.0, 1.5)
RIDGE = F(1, 2)
SPACING = (0.5, 0.25, 0.125)


def add(a: Pair, b: Pair) -> Pair:
    return a[0] + b[0], a[1] + b[1]


def mul(a: Pair, b: Pair) -> Pair:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def scale(a: Pair, value: F) -> Pair:
    return a[0] * value, a[1] * value


def conj(a: Pair) -> Pair:
    return a[0], -a[1]


def represented_matrix() -> list[list[F]]:
    phi = np.array(PHASES, dtype=np.float64)
    c, s = np.cos(phi), np.sin(phi)
    h = np.column_stack((np.ones(5), c, s, c * c - s * s, (2 * c) * s))
    return [[F(float(value)) for value in row] for row in h]


def inverse(h: list[list[F]]) -> list[list[F]]:
    """Exact rational elimination, independent of the product SVD solver."""
    rows = [row[:] + [F(i == j) for j in range(5)] for i, row in enumerate(h)]
    for i in range(5):
        pivot = next(j for j in range(i, 5) if rows[j][i])
        rows[i], rows[pivot] = rows[pivot], rows[i]
        divisor = rows[i][i]
        rows[i] = [v / divisor for v in rows[i]]
        for j in range(5):
            if j != i:
                factor = rows[j][i]
                rows[j] = [a - factor * b for a, b in zip(rows[j], rows[i], strict=True)]
    return [row[5:] for row in rows]


def condition_bound(h: list[list[F]], inv: list[list[F]]) -> float:
    def norms(matrix: list[list[F]]) -> F:
        one = max(sum((abs(matrix[i][j]) for i in range(5)), F(0)) for j in range(5))
        infinity = max(sum((abs(v) for v in row), F(0)) for row in matrix)
        return one * infinity

    return math.nextafter(math.sqrt(float(norms(h) * norms(inv))), math.inf)


def signal_cell() -> Any:
    """Dyadic measured patterns, not phase-model truth synthesized with rounded trig."""
    c = np.array([1, 0, -1, 0], dtype=np.float64)
    s = np.array([0, 1, 0, -1], dtype=np.float64)
    n = np.array([1, -1, 1, -1], dtype=np.float64)
    z, y, x = np.indices((4, 4, 4))
    patterns = (c[z], s[y], c[x], n[x], s[z] * c[y], n[z] * s[x])
    # Distinct phase rows excite all represented coordinates, including their signs.
    weights = (
        (4, 1, 2, 1, -1, 2),
        (1, 3, -2, 2, 1, -1),
        (-3, 2, 1, -1, 2, 1),
        (2, -2, 3, 1, -2, 3),
        (-1, -3, -1, 3, 3, -2),
    )
    result = np.empty((3, 5, 4, 4, 4), dtype=np.float64)
    for r, p in product(range(3), range(5)):
        result[r, p] = (1 + r) / 2
        for k, pattern in enumerate(patterns):
            result[r, p] += (r + 1) * weights[p][k] * pattern / 32
    return result


def carrier_table(shape: Mode) -> Any:
    step = shape[1] // 8
    return np.array(((step, -step), (-step, 0), (0, step)), dtype=np.int64)


def transfer(r: int, m: int, j: Mode, shape: Mode) -> Pair:
    """Finite dyadic, asymmetric directly supplied E; no physical support assumption."""
    return (
        F(8 + r + m, 16) + F(j[0], 8 * shape[0]) + F(j[2], 16 * shape[2]),
        F(1 + 2 * r - m, 16) + F(j[1], 8 * shape[1]),
    )


def mask_value(q: Mode) -> F:
    if q[1] > 0 and q[2] > 0:
        return F(0)
    if q[2] < 0:
        return F(1, 4)
    return F(1, 2) if q[0] < 0 else F(1)


def digest(array: Any) -> str:
    """Hash existing C storage without a second full bytes/array allocation."""
    assert array.flags.c_contiguous
    view = memoryview(array).cast("B")
    value = hashlib.sha256()
    for start in range(0, len(view), 1024 * 1024):
        value.update(view[start : start + 1024 * 1024])
    return value.hexdigest()


def inputs(case: dict[str, Any]) -> list[Any]:
    arrays = [case[k] for k in ("images", "phases_rad", "carriers_bins", "gains", "apodization")]
    for record in case["order_otfs"]:
        arrays.extend(getattr(record, k) for k in ("values", "fz_per_um", "fy_per_um", "fx_per_um"))
    return arrays


def make_case(shape: Mode) -> tuple[dict[str, Any], dict[str, Any]]:
    from simrecon import VolumeOrderOtf, correct_linear_response, declare_acquisition

    assert all(k >= 4 and k % 4 == 0 and k & (k - 1) == 0 for k in shape)
    assert shape[1] == shape[2] and shape[1] >= 8
    cell = signal_cell()
    raw = np.tile(32 + 2 * cell, (1, 1, shape[0] // 4, shape[1] // 4, shape[2] // 4))
    raw_id = digest(raw)
    config = {
        "version": 1,
        "acquisition_kind": "specimen_sim",
        "axes": ["orientation", "phase", "z", "y", "x"],
        "intensity_unit": "count",
        "sampling_um": dict(zip(("z", "y", "x"), SPACING, strict=True)),
    }
    acquisition = declare_acquisition(raw, config=config)
    assert acquisition.axes == tuple(config["axes"])
    assert digest(acquisition.data) == raw_id and digest(raw) == raw_id
    corrected = correct_linear_response(
        acquisition, offset=32.0, response=2.0, output_unit="signal"
    )
    assert digest(acquisition.data) == raw_id and digest(raw) == raw_id
    assert corrected.axes == acquisition.axes
    assert corrected.input_unit == "count" and corrected.output_unit == "signal"
    # Every sample, not just a support/subset check. Expected slabs stay at one plane.
    for r, p, z in product(range(3), range(5), range(shape[0])):
        expected = np.tile(cell[r, p, z % 4], (shape[1] // 4, shape[2] // 4))
        np.testing.assert_array_equal(corrected.data[r, p, z], expected)
    camera = {
        "raw_sha256": raw_id,
        "corrected_sha256": digest(corrected.data),
        "offset": 32.0,
        "response": 2.0,
        "units": [corrected.input_unit, corrected.output_unit],
        "source_axes": list(acquisition.source_axes),
    }
    # Completed operations: release only redundant owners. Actual reconstruction
    # images remain strongly referenced by case throughout the product call.
    del raw, acquisition
    records = []
    nz, ny, nx = shape
    jx = np.arange(-nx // 2, nx // 2)[None, :]
    jy = np.arange(-ny // 2, ny // 2)[:, None]
    for r in range(3):
        values = np.empty((3, *shape), dtype=np.complex128)
        for m, zi in product(range(3), range(nz)):
            values[m, zi].real = (8 + r + m) / 16 + (zi - nz // 2) / (8 * nz) + jx / (16 * nx)
            values[m, zi].imag = (1 + 2 * r - m) / 16 + jy / (8 * ny)
        vectors = [
            np.arange(-k // 2, k // 2, dtype=np.float64) / k / d
            for k, d in zip(shape, SPACING, strict=True)
        ]
        records.append(
            VolumeOrderOtf(
                values=values,
                fz_per_um=vectors[0],
                fy_per_um=vectors[1],
                fx_per_um=vectors[2],
                voxel_size_um=SPACING,
                origin_zyx=(r % nz, (r + 1) % ny, (2 * r) % nx),
                source=f"algebraic dyadic transfer {r}",
            )
        )
    output = (nz, 2 * ny, 2 * nx)
    mask = np.empty(output, dtype=np.float64)
    qy = np.arange(-ny, ny)[:, None]
    qx = np.arange(-nx, nx)[None, :]
    for zi in range(nz):
        mask[zi] = np.where(
            (qy > 0) & (qx > 0), 0, np.where(qx < 0, 0.25, 0.5 if zi < nz // 2 else 1.0)
        )
    case = dict(
        images=corrected.data,
        order_otfs=records,
        phases_rad=np.tile(np.array(PHASES), (3, 1)),
        carriers_bins=carrier_table(shape),
        gains=np.array(GAINS),
        regularization=float(RIDGE),
        output_shape_yx=output[1:],
        apodization=mask,
    )
    return case, camera


def sparse_bands() -> tuple[list[dict[Mode, tuple[Pair, Pair, Pair]]], float]:
    """Exact DFT of finite stored observations, then exact represented H inverse.

    Periodic extension multiplies the geometric sum by zero off quarter modes;
    on them its normalized DFT equals the 4^3 cell DFT. No product output is read.
    """
    cell = signal_cell()
    h = represented_matrix()
    inv = inverse(h)
    cond = condition_bound(h, inv)
    assert cond <= 10
    roots: tuple[Pair, ...] = ((F(1), F(0)), (F(0), F(-1)), (F(-1), F(0)), (F(0), F(1)))
    result = []
    for r in range(3):
        bands = {}
        for k in product(range(-2, 2), repeat=3):
            b = []
            for p in range(5):
                value = ZERO
                for x in product(range(4), repeat=3):
                    phase = roots[sum(a * v for a, v in zip(k, x, strict=True)) % 4]
                    value = add(value, scale(phase, F(float(cell[(r, p, *x)])) / 64))
                b.append(value)
            coordinates = [ZERO] * 5
            for i in range(5):
                for p in range(5):
                    coordinates[i] = add(coordinates[i], scale(b[p], inv[i][p]))
            dc, b1, c1, b2, c2 = coordinates
            cm = (
                dc,
                scale(add(b1, mul((F(0), F(-1)), c1)), F(1, 2)),
                scale(add(b2, mul((F(0), F(-1)), c2)), F(1, 2)),
            )
            if any(v != ZERO for v in cm):
                bands[k] = cm
        result.append(bands)
    return result, cond


def sparse_estimator(shape: Mode) -> tuple[dict[Mode, Pair], dict[str, float]]:
    bands, cond = sparse_bands()
    carriers = carrier_table(shape)
    support: set[Mode] = set()
    for r, m in product(range(3), range(-2, 3)):
        for k in bands[r]:
            # Conjugation maps the periodic cell's support by modular negation.
            kk = k if m >= 0 else tuple((-v + 2) % 4 - 2 for v in k)
            j = tuple(v * n // 4 for v, n in zip(kk, shape, strict=True))
            support.add((j[0], j[1] - m * int(carriers[r, 0]), j[2] - m * int(carriers[r, 1])))
    answer = {}
    for q in sorted(support):
        numerator, denominator = ZERO, RIDGE
        for r, m in product(range(3), range(-2, 3)):
            j = (q[0], q[1] + m * int(carriers[r, 0]), q[2] + m * int(carriers[r, 1]))
            if not all(-n // 2 <= v < n // 2 for v, n in zip(j, shape, strict=True)):
                continue
            lookup = cast(
                Mode,
                (
                    j
                    if m >= 0
                    else tuple((-v + n // 2) % n - n // 2 for v, n in zip(j, shape, strict=True))
                ),
            )
            t = scale(transfer(r, abs(m), lookup, shape), F(GAINS[r]))
            if m < 0:
                t = conj(t)
            denominator += t[0] ** 2 + t[1] ** 2
            # Zero off the analytically proved quarter-mode support; no threshold.
            d = ZERO
            if all(4 * v % n == 0 for v, n in zip(lookup, shape, strict=True)):
                k = cast(Mode, tuple(4 * v // n for v, n in zip(lookup, shape, strict=True)))
                d = bands[r].get(k, (ZERO, ZERO, ZERO))[abs(m)]
                if m < 0:
                    d = conj(d)
            numerator = add(numerator, mul(conj(t), d))
        value = scale(numerator, mask_value(q) / denominator)
        if value != ZERO:
            answer[q] = value
    energy = F(0)
    for band in bands:
        for values in band.values():
            for m, value in enumerate(values):
                energy += (1 if m == 0 else 2) * (value[0] ** 2 + value[1] ** 2)
    return answer, {
        "phase_condition_upper": cond,
        "band_l2": math.nextafter(math.sqrt(float(energy)), math.inf),
        "image_abs_max": float(np.max(np.abs(signal_cell()))),
    }


def as_decimal(value: F) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def reference_tile(spectrum: dict[Mode, Pair], shape: Mode) -> Any:
    """80-digit finite synthesis; exact quarter/sixteenth modes repeat 4x16x16."""
    output = (shape[0], 2 * shape[1], 2 * shape[2])
    tile = np.empty((4, 16, 16), dtype=np.complex128)
    with localcontext() as ctx:
        ctx.prec = 80
        roots = [root(Decimal(i) / 16, 80) for i in range(16)]
        terms = []
        for q, value in spectrum.items():
            turns = tuple(F(v, n) for v, n in zip(q, output, strict=True))
            assert all((16 * v).denominator == 1 for v in turns)
            assert (4 * turns[0]).denominator == 1
            terms.append((tuple(int(16 * v) for v in turns), tuple(as_decimal(v) for v in value)))
        for x in np.ndindex(tile.shape):
            re, im = Decimal(0), Decimal(0)
            for k, (a, b) in terms:
                c, s = roots[sum(v * w for v, w in zip(k, x, strict=True)) % 16]
                re += a * c - b * s
                im += a * s + b * c
            tile[x] = complex(float(re), float(im))
    return tile


def budgets(shape: Mode, spectrum: dict[Mode, Pair], facts: dict[str, float]) -> dict[str, float]:
    """Derive the selected fixture evaluation envelope.

    Separator: inherited per-real-coordinate bound. Parseval + ridge operator
    norm propagate it without P times a per-bin worst case. FFT/weighted stages
    use the conservative operation envelopes explicitly stated in the report.
    """
    with localcontext() as ctx:
        ctx.prec = 90
        eps, tiny = Decimal(2) ** -52, Decimal(2) ** -1074
        j, n = 15, 5
        output = (shape[0], 2 * shape[1], 2 * shape[2])
        p = math.prod(output)

        def gamma(k: int) -> Decimal:
            return k * eps / (1 - k * eps)

        delta = 8192 * n * eps * Decimal(facts["image_abs_max"]) + 8 * tiny
        separator = Decimal(27).sqrt() * delta
        forward_eta = gamma(64 * sum(k.bit_length() - 1 for k in shape) + 32)
        inverse_eta = gamma(64 * sum(k.bit_length() - 1 for k in output) + 32)
        band_norm = Decimal(facts["band_l2"])
        transform = forward_eta * (band_norm + separator)
        # Every transfer component <1; maximum gain=1.5, so |t|<1.5*sqrt(2).
        weighted = (
            gamma(64 * j + 32)
            * Decimal(j).sqrt()
            * Decimal("1.5")
            * Decimal(2).sqrt()
            / as_decimal(RIDGE)
            * (band_norm + separator + transform)
        )
        e2 = (separator + transform) / (2 * as_decimal(RIDGE).sqrt()) + weighted
        energies = [as_decimal(a * a + b * b) for a, b in spectrum.values()]
        norm_t = sum(energies, Decimal(0)).sqrt()
        l1_t = sum((v.sqrt() for v in energies), Decimal(0))
        # Reference final binary64 conversion + 80-digit finite-sum/root observer.
        observer = eps * l1_t + len(spectrum) * (1 + l1_t) * Decimal(10) ** -75
        spectrum_error = e2 + observer + 64 * math.prod(shape) * tiny
        volume_error = (
            Decimal(p).sqrt() * (e2 + inverse_eta * (norm_t + e2)) + observer + 64 * p * tiny
        )
        assert spectrum_error.is_finite() and volume_error.is_finite()
        assert spectrum_error > 0 and volume_error > 0
        values = {
            "spectrum": spectrum_error,
            "volume": volume_error,
            "separator_coordinate": delta,
            "forward_relative_l2_envelope": forward_eta,
            "inverse_relative_l2_envelope": inverse_eta,
            "spectrum_l2_envelope": e2,
            "reference_l1": l1_t,
            "old_regime_left": 65536 * j * (n + math.prod(shape) + p) * eps,
            "old_regime_right": Decimal(2) ** -10,
        }
        # One binary64 step upward also dominates the 90-digit observer rounding.
        return {key: math.nextafter(float(value), math.inf) for key, value in values.items()}


def compare_outputs(
    result: Any,
    case: dict[str, Any],
    spectrum: dict[Mode, Pair],
    tile: Any,
    limits: dict[str, float],
) -> dict[str, Any]:
    """Observe every complex output in one-plane slabs, including zero support."""
    shape = (case["images"].shape[2], *case["output_shape_yx"])
    source_arrays = inputs(case)
    outputs = [
        getattr(result, k) for k in ("spectrum", "volume", "fz_per_um", "fy_per_um", "fx_per_um")
    ]
    for i, array in enumerate(outputs):
        assert type(array) is np.ndarray
        assert array.dtype == np.dtype("complex128" if i < 2 else "float64")
        assert (
            array.dtype.isnative
            and array.flags.c_contiguous
            and array.flags.owndata
            and array.flags.writeable
        )
        assert array.shape == (shape if i < 2 else (shape[i - 2],))
        assert not any(np.shares_memory(array, other) for other in source_arrays + outputs[:i])
    assert result.voxel_size_um == (SPACING[0], SPACING[1] / 2, SPACING[2] / 2)
    eps, tiny = F(1, 2**52), F(1, 2**1074)
    spacing = case["order_otfs"][0].voxel_size_um
    for axis, array in enumerate(outputs[2:]):
        assert np.isfinite(array).all()
        assert np.all(array[1:] > array[:-1])
        assert array[shape[axis] // 2] == 0
        # Exact represented field length; no binary64 product/division or
        # observer underflow may narrow the public coordinate error budget.
        field_length = F(int(case["images"].shape[axis + 2])) * F(float(spacing[axis]))
        for index, actual in enumerate(array):
            mode = index - shape[axis] // 2
            exact = F(mode) / field_length
            if mode:
                assert actual != 0
            assert abs(F(float(actual)) - exact) <= 8 * eps * abs(exact) + tiny
    maximum_s = maximum_v = imaginary = 0.0
    for zi in range(shape[0]):
        expected_s = np.zeros(shape[1:], dtype=np.complex128)
        for q, (a, b) in spectrum.items():
            if q[0] + shape[0] // 2 == zi:
                expected_s[q[1] + shape[1] // 2, q[2] + shape[2] // 2] = complex(float(a), float(b))
        expected_v = np.tile(tile[zi % 4], (shape[1] // 16, shape[2] // 16))
        for actual in (result.spectrum[zi], result.volume[zi]):
            assert np.isfinite(actual).all()
        maximum_s = max(maximum_s, float(np.max(np.abs(result.spectrum[zi] - expected_s))))
        maximum_v = max(maximum_v, float(np.max(np.abs(result.volume[zi] - expected_v))))
        imaginary = max(imaginary, float(np.max(np.abs(np.imag(expected_v)))))
    assert maximum_s <= limits["spectrum"], (maximum_s, limits["spectrum"])
    assert maximum_v <= limits["volume"], (maximum_v, limits["volume"])
    # Fixture diagnostic: a real projection is distinguishable by a wide margin.
    assert imaginary > 1000 * limits["volume"]
    return {
        "shape": list(shape),
        "dtypes": [str(a.dtype) for a in outputs],
        "all_finite": True,
        "independent_owned_mutable_c_arrays": True,
        "spectrum_max_complex_error": maximum_s,
        "volume_max_complex_error": maximum_v,
        "expected_max_abs_imaginary": imaginary,
        "spectrum_sha256": digest(result.spectrum),
        "volume_sha256": digest(result.volume),
        "checked_spectrum_samples": math.prod(shape),
        "checked_volume_samples": math.prod(shape),
        "slab_shape": list(shape[1:]),
    }


def run_witness(size: str = "small") -> dict[str, Any]:
    from simrecon import reconstruct_volume

    shape = SIZES[size]
    spectrum, facts = sparse_estimator(shape)
    tile = reference_tile(spectrum, shape)
    limits = budgets(shape, spectrum, facts)
    print(
        json.dumps(
            {
                "event": "reference_ready",
                "size": size,
                "shape": list(shape),
                "support_count": len(spectrum),
                "facts": facts,
                "evaluation_budgets": limits,
            }
        ),
        flush=True,
    )
    case, camera = make_case(shape)
    arrays = inputs(case)
    before = [(digest(a), a.strides, a.flags.writeable) for a in arrays]
    print(
        json.dumps(
            {
                "event": "reconstruction_start",
                "camera": camera,
                "input_sha256": [v[0] for v in before],
            }
        ),
        flush=True,
    )
    # No monkeypatch, private seam or substituted product callable.
    completed = False
    try:
        result = reconstruct_volume(
            case["images"], **{k: v for k, v in case.items() if k != "images"}
        )
        completed = True
    finally:
        after = [(digest(a), a.strides, a.flags.writeable) for a in arrays]
        print(
            json.dumps(
                {
                    "event": "reconstruction_end",
                    "returned": completed,
                    "inputs_preserved": after == before,
                    "input_sha256": [v[0] for v in after],
                }
            ),
            flush=True,
        )
        assert after == before
    evidence = compare_outputs(result, case, spectrum, tile, limits)
    evidence.update(
        size=size,
        camera=camera,
        facts=facts,
        budgets=limits,
        input_sha256=[v[0] for v in before],
        inputs_preserved=True,
        support_count=len(spectrum),
    )
    print(json.dumps({"event": "complete", **evidence}), flush=True)
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=tuple(SIZES), required=True)
    run_witness(parser.parse_args().size)
