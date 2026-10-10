"""Independent stored-input Decimal DFT observers for VOLUME-ORDER-01."""

import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from itertools import permutations, product
from typing import Any

import numpy as np
import pytest

import simrecon

type Array = np.ndarray[Any, Any]
type Pair = tuple[Decimal, Decimal]
PRECISION = 120
PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647093844609550582"
)
FIELDS = (
    "values",
    "fz_per_um",
    "fy_per_um",
    "fx_per_um",
    "voxel_size_um",
    "origin_zyx",
    "source",
)
EPS = Decimal.from_float(2.0**-52)
# Exact constants must not be rounded by Decimal's default 28-digit context.
Q = Decimal.from_float(float.fromhex("0x0.0000000000001p-1022"))
F = Decimal.from_float(float(np.finfo(np.float64).max))


def dec(value: Any) -> Decimal:
    return Decimal.from_float(float(value))


@cache
def root(turn: Fraction) -> Pair:
    """exp(-2*pi*i*turn), with exact quarter roots and 120-digit Taylor sums."""
    turn %= 1
    exact = {
        Fraction(0): (Decimal(1), Decimal(0)),
        Fraction(1, 4): (Decimal(0), Decimal(-1)),
        Fraction(1, 2): (Decimal(-1), Decimal(0)),
        Fraction(3, 4): (Decimal(0), Decimal(1)),
    }
    if turn in exact:
        return exact[turn]
    if turn > Fraction(1, 2):
        turn -= 1
    with localcontext() as ctx:
        ctx.prec = PRECISION
        x = -2 * PI * Decimal(turn.numerator) / Decimal(turn.denominator)
        sin_term = x
        cos_term = Decimal(1)
        sine, cosine = sin_term, cos_term
        for n in range(1, 240):
            sin_term *= -x * x / ((2 * n) * (2 * n + 1))
            cos_term *= -x * x / ((2 * n - 1) * (2 * n))
            sine += sin_term
            cosine += cos_term
        return +cosine, +sine


def mul(a: Pair, b: Pair) -> Pair:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def modes(n: int) -> list[int]:
    return list(range(-(n // 2), (n + 1) // 2))


def gains(coefficients: Array) -> list[Decimal]:
    converted = np.array(coefficients, dtype=np.complex128)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        return [Decimal(1)] + [
            max([abs(dec(v.real)) for v in row] + [abs(dec(v.imag)) for v in row]) or Decimal(1)
            for row in converted
        ]


def direct(
    psf: Array, coefficients: Array, origin: tuple[int, int, int]
) -> dict[tuple[int, ...], Pair]:
    """Exact-real stored snapshots; no FFT, product result or legacy oracle."""
    a = np.array(psf, dtype=np.float64)
    g = np.array(coefficients, dtype=np.complex128)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        mass = sum((dec(v) for v in a.flat), Decimal(0))
        result = {}
        for index in product(*(range(n) for n in a.shape)):
            k = tuple(modes(n)[j] for n, j in zip(a.shape, index, strict=True))
            sums = [[Decimal(0), Decimal(0)] for _ in range(3)]
            for r in product(*(range(n) for n in a.shape)):
                turn = sum(
                    (
                        Fraction(ki * (ri - oi), ni)
                        for ki, ri, oi, ni in zip(k, r, origin, a.shape, strict=True)
                    ),
                    Fraction(0),
                )
                phase = root(turn)
                weight = dec(a[r]) / mass
                for m in range(3):
                    coefficient = (
                        (Decimal(1), Decimal(0))
                        if m == 0
                        else (dec(g[m - 1, r[0]].real), dec(g[m - 1, r[0]].imag))
                    )
                    term = mul(coefficient, phase)
                    sums[m][0] += weight * term[0]
                    sums[m][1] += weight * term[1]
            for m in range(3):
                result[(m, *index)] = (sums[m][0], sums[m][1])
        return result


def budget(size: int, gain: Decimal, detection: bool = False) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        return (128 if detection else 256) * size * EPS * gain + (4 if detection else 8) * size * Q


def assert_values(
    values: Array, expected: dict[tuple[int, ...], Pair], gs: list[Decimal], size: int
) -> None:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index, target in expected.items():
            v = values[index]
            assert np.isfinite(v.real) and np.isfinite(v.imag)
            dr, di = dec(v.real) - target[0], dec(v.imag) - target[1]
            error = (dr * dr + di * di).sqrt()
            assert error <= budget(size, gs[index[0]], index[0] == 0), f"DFT error at {index}"


def assert_frequencies(result: Any, shape: tuple[int, ...], spacing: Any) -> None:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for name, n, d in zip(FIELDS[1:4], shape, spacing, strict=True):
            grid = getattr(result, name)
            assert grid.shape == (n,)
            assert np.isfinite(grid).all()
            assert np.all(grid[1:] > grid[:-1])
            for value, k in zip(grid, modes(n), strict=True):
                exact = Decimal(k) / (n * dec(d))
                if k == 0:
                    assert value == 0
                else:
                    assert value != 0
                assert abs(dec(value) - exact) <= 8 * EPS * abs(exact) + Q


def storage(result: Any, psf: Array, coefficients: Array, other: Any = None) -> None:
    arrays = [getattr(result, name) for name in FIELDS[:4]]
    for j, array in enumerate(arrays):
        assert isinstance(array, np.ndarray)  # Output subclasses are permitted.
        assert array.dtype == np.dtype(np.complex128 if j == 0 else np.float64)
        assert array.dtype.isnative and array.flags.c_contiguous
        assert array.flags.owndata and array.flags.writeable
        assert not np.shares_memory(array, psf)
        assert not np.shares_memory(array, coefficients)
        for peer in arrays[:j]:
            assert not np.shares_memory(array, peer)
        if other is not None:
            for name in FIELDS[:4]:
                assert not np.shares_memory(array, getattr(other, name))


def input_state(value: Any) -> tuple[Any, ...]:
    if isinstance(value, np.ndarray):
        return (value.tobytes(), value.dtype, value.shape, value.strides, value.flags.writeable)
    if isinstance(value, (list, tuple)):
        return tuple(value)  # Retain original elements, including their identities.
    view = memoryview(value)
    return (view.tobytes(), view.format, view.shape, view.strides, view.readonly)


def snapshot_inputs(*values: Any) -> list[tuple[Any, tuple[Any, ...]]]:
    """Observe mutable metadata, caller arrays and reachable backing storage."""
    pending: list[Any] = [value for value in values if isinstance(value, (np.ndarray, list, tuple))]
    saved: list[tuple[Any, tuple[Any, ...]]] = []
    seen: set[int] = set()
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        saved.append((value, input_state(value)))
        if isinstance(value, np.ndarray):
            base = value.base
        elif isinstance(value, memoryview):
            base = value.obj
        else:
            base = None
            if isinstance(value, (list, tuple)):
                pending.extend(
                    child for child in value if isinstance(child, (np.ndarray, list, tuple))
                )
        if isinstance(base, (np.ndarray, memoryview, bytes, bytearray)):
            pending.append(base)
    return saved


def assert_inputs_preserved(saved: list[tuple[Any, tuple[Any, ...]]]) -> None:
    for value, before in saved:
        if isinstance(value, (list, tuple)):
            assert len(value) == len(before) and all(
                current is original for current, original in zip(value, before, strict=True)
            ), "caller metadata container changed"
        else:
            assert input_state(value) == before, "caller array or backing buffer changed"


@contextmanager
def preserved_inputs(*values: Any) -> Iterator[None]:
    saved = snapshot_inputs(*values)
    try:
        yield
    finally:
        assert_inputs_preserved(saved)


def state(result: Any) -> list[Any]:
    saved = []
    for name in FIELDS:
        value = getattr(result, name)
        if name in FIELDS[:4]:
            saved.append(
                (
                    id(value),
                    value.tobytes(),
                    value.shape,
                    value.strides,
                    value.dtype,
                    value.flags.owndata,
                    value.flags.c_contiguous,
                    value.flags.writeable,
                )
            )
        else:
            saved.append(value)
    return saved


def unchanged(result: Any, before: list[Any]) -> None:
    assert state(result) == before


def assert_frozen_bindings(record: Any) -> None:
    before = state(record)
    for name in FIELDS:
        for operation in ("assign", "delete"):
            try:
                if operation == "assign":
                    setattr(record, name, None)
                else:
                    delattr(record, name)
            except Exception:
                pass  # Exception type and silent refusal are both unspecified.
            unchanged(record, before)  # Includes every field, identity and array metadata.


def normalized_transform_observer(
    psf: Array, g: Array, origin: tuple[int, int, int], original: Any
) -> tuple[Any, set[int]]:
    gs, expected = gains(g), direct(psf, g, origin)
    normalized = []
    with localcontext() as ctx:
        ctx.prec = PRECISION
        mass = sum((dec(v) for v in psf.flat), Decimal(0))
        for m in range(3):
            kernel = np.empty(psf.shape, dtype=np.complex128)
            for index in product(*(range(n) for n in psf.shape)):
                v = 1 + 0j if m == 0 else g[m - 1, index[0]]
                kernel[index] = complex(
                    float(dec(psf[index]) * dec(v.real) / mass / gs[m]),
                    float(dec(psf[index]) * dec(v.imag) / mass / gs[m]),
                )
            normalized.append(np.roll(kernel, tuple(-o for o in origin), (0, 1, 2)))
    observed: set[int] = set()

    def observe(a: Any, s: Any = None, axes: Any = None, norm: Any = None, out: Any = None) -> Any:
        data = np.asarray(a)
        if axes is None:
            # NumPy chooses trailing len(s) axes when sizes are provided;
            # with neither sizes nor axes, it transforms every axis.
            first = 0 if s is None else data.ndim - len(s)
            raw_axes = tuple(range(first, data.ndim))
        else:
            raw_axes = tuple(axes)
        assert all(-data.ndim <= axis < data.ndim for axis in raw_axes)
        chosen = tuple(axis % data.ndim for axis in raw_axes)
        assert len(chosen) == 3 and len(set(chosen)) == 3
        assert norm in (None, "backward")
        if s is not None:
            assert all(
                length in (None, -1, data.shape[axis])
                for length, axis in zip(s, chosen, strict=True)
            )
        batch_axes = tuple(axis for axis in range(data.ndim) if axis not in chosen)
        layouts = [
            (*batch_axes, *spatial)
            for spatial in permutations(chosen)
            if tuple(data.shape[axis] for axis in spatial) == psf.shape
        ]
        assert layouts, "transformed spatial sizes changed"
        # These fixtures have unequal dimensions, so their canonical z/y/x
        # arrangement is unambiguous. Shape alone never establishes order identity.
        assert len(layouts) == 1
        layout = layouts[0]
        inputs = data.transpose(layout).reshape((-1, *psf.shape))
        matches = []
        for kernel in inputs:
            candidates = [
                m
                for m in range(3)
                if np.max(np.abs(kernel - normalized[m]))
                <= float(budget(psf.size, Decimal(1), True))
            ]
            assert len(candidates) == 1, (
                "fftn input is not a declared normalized origin-rolled order kernel"
            )
            matches.append(candidates[0])
        transformed = original(a, s=s, axes=axes, norm=norm, out=out)
        assert transformed.shape == data.shape
        outputs = transformed.transpose(layout).reshape((-1, *psf.shape))
        for m, transform in zip(matches, outputs, strict=True):
            centered = np.fft.fftshift(transform)
            with localcontext() as ctx:
                ctx.prec = PRECISION
                for index in product(*(range(n) for n in psf.shape)):
                    target = expected[(m, *index)]
                    dr = dec(centered[index].real) - target[0] / gs[m]
                    di = dec(centered[index].imag) - target[1] / gs[m]
                    assert (dr * dr + di * di).sqrt() <= budget(psf.size, Decimal(1), True)
            observed.add(m)
        return transformed

    return observe, observed


@pytest.fixture
def api() -> Any:
    # Missing API is setup evidence; it does not prevent collection.
    prepare = getattr(simrecon, "prepare_volume_order_otfs", None)
    record = getattr(simrecon, "VolumeOrderOtf", None)
    assert callable(prepare), "public prepare_volume_order_otfs API absent (setup)"
    assert record is not None, "public VolumeOrderOtf API absent (setup)"
    return prepare


def call(api: Any, psf: Any, coefficients: Any, **kwargs: Any) -> Any:
    return api(
        psf,
        axial_coefficients=coefficients,
        voxel_size_um=kwargs.pop("voxel_size_um", (0.3, 0.7, 1.1)),
        origin_zyx=kwargs.pop("origin_zyx", (0, 0, 0)),
        source=kwargs.pop("source", " caller identity "),
        **kwargs,
    )


def reject(api: Any, code: str, psf: Any, coefficients: Any, **kwargs: Any) -> None:
    floating, filters = np.geterr(), list(warnings.filters)
    with (
        pytest.raises(simrecon.SimreconError) as caught,
        preserved_inputs(psf, coefficients, *kwargs.values()),
    ):
        call(api, psf, coefficients, **kwargs)
    assert np.geterr() == floating and warnings.filters == filters
    error: Any = caught.value
    assert isinstance(error, ValueError)
    assert getattr(error, "code", None) == code
    assert isinstance(getattr(error, "message", None), str)
