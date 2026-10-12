"""Compact preservation observer and independent auxiliary finite sums.

No exporter output supplies expectations. The digest encodes JSON types, exact
integers, big-endian binary64 bits, UTF-8 strings, and ordered containers with
length framing. JSON formatting is deliberately outside this representation.
"""

from __future__ import annotations

import hashlib
import math
import struct
from decimal import Decimal, localcontext
from functools import cache
from typing import Any

import numpy as np

import reconstruction_fixture as reconstruction


def representation(value: Any) -> bytes:
    """Injectively encode the finite JSON domain, retaining dictionary order."""
    if value is None:
        return b"n"
    if isinstance(value, bool):
        return b"t" if value else b"f"
    if isinstance(value, int):
        encoded = str(value).encode("ascii")
        return b"i" + struct.pack(">Q", len(encoded)) + encoded
    if isinstance(value, float):
        assert math.isfinite(value), "nonfinite JSON number"
        return b"d" + struct.pack(">d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + struct.pack(">Q", len(encoded)) + encoded
    if isinstance(value, list):
        return b"l" + struct.pack(">Q", len(value)) + b"".join(map(representation, value))
    assert isinstance(value, dict), "unsupported JSON representation"
    return (
        b"m"
        + struct.pack(">Q", len(value))
        + b"".join(representation(key) + representation(item) for key, item in value.items())
    )


def digest(value: Any) -> str:
    return hashlib.sha256(representation(value)).hexdigest()


def assert_exact(actual: Any, expected: Any, label: str) -> None:
    """Keep arrays out of diagnostic output; require exact complete bits/types."""
    assert digest(actual) == digest(expected), f"exact representation mismatch: {label}"


def complex_layout(array: Any) -> dict[str, Any]:
    values = np.asarray(array, dtype=np.complex128)
    return {"real": values.real.tolist(), "imag": values.imag.tolist()}


def historical_display(case_id: str, ys: list[int], xs: list[int]) -> tuple[Any, Any]:
    """Derive documentary values from algebraic roots, not high-precision roots.

    The sixth roots use binary64 sqrt(3)/2 before weighting, as historically
    displayed. These scalar root identities are not payload/array fixtures.
    """
    real, imag = [], []
    for j in ys:
        real_row, imag_row = [], []
        for k in xs:
            if case_id in ("delta-odd", "singleton"):
                re, im = 1.0, 0.0
            elif case_id == "uniform-even":
                re, im = float(j == 0 and k == 0), 0.0
            elif case_id == "separable-mixed":
                re = (1.0 if j == 0 else 0.25) * float(k % 2 == 0)
                im = 0.0
            else:
                assert case_id in ("asymmetric-even", "asymmetric-translated")
                yr, yi = ((1, 0), (0, -1), (-1, 0), (0, 1))[j % 4]
                xr = (1, 0.5, -0.5, -1, -0.5, 0.5)[k % 6]
                xi = (0, -1, -1, 0, 1, 1)[k % 6] * (math.sqrt(3) / 2)
                re, im = 3 / 8 + yr / 8 + xr / 2, yi / 8 + xi / 2
            real_row.append(re)
            imag_row.append(im)
        real.append(real_row)
        imag.append(imag_row)
    return real, imag


@cache
def auxiliary_planes() -> tuple[Any, Any, Any]:
    """Return rounded PSF, exact conventional recipe, and ideal Decimal anchor.

    Use the approved 85-digit roots. Form the real object in coefficient order.
    Round each kernel/object scalar to binary64, then left-fold separate
    binary64 products and additions with hy outer, hx inner. Also accumulate
    the unrounded Decimal products independently as a mathematical anchor.
    Neither observation uses stored acquisitions or product numerical calls.
    """
    with localcontext() as context:
        context.prec = 85
        z = reconstruction.Z
        root = reconstruction.root
        coefficients = {
            (0, 0): z(Decimal(4)),
            (1, 0): z(Decimal("0.25"), Decimal("0.4")),
            (0, 3): z(Decimal("-0.35"), Decimal("0.2")),
            (2, 1): z(Decimal("0.15"), Decimal("-0.3")),
        }
        for (j, k), value in list(coefficients.items()):
            if (j, k) != (0, 0):
                coefficients[-j, -k] = value.conj()
        kernel, obj = [], []
        for y in range(7):
            kernel_row, object_row = [], []
            for x in range(9):
                vy = 1 + Decimal("0.8") * root(Decimal(y - 1) / 7).re
                vx = (
                    1
                    + Decimal("0.6") * root(Decimal(x - 1) / 9).re
                    + Decimal("0.2") * root(Decimal(2 * (x - 1)) / 9).re
                )
                kernel_row.append(vy * vx / 63)
                total = z()
                for (j, k), coefficient in coefficients.items():
                    total += coefficient * root(Decimal(j * y) / 7 + Decimal(k * x) / 9)
                object_row.append(total.re)
            kernel.append(kernel_row)
            obj.append(object_row)
        rounded_kernel = [[float(value) for value in row] for row in kernel]
        rounded_object = [[float(value) for value in row] for row in obj]
        observation, ideal = [], []
        for y in range(7):
            row, ideal_row = [], []
            for x in range(9):
                total = 0.0
                ideal_total = Decimal(0)
                for hy in range(7):
                    for hx in range(9):
                        yy, xx = (y - hy) % 7, (x - hx) % 9
                        product = rounded_kernel[hy][hx] * rounded_object[yy][xx]
                        total = total + product
                        ideal_total += kernel[hy][hx] * obj[yy][xx]
                row.append(total)
                ideal_row.append(ideal_total)
            observation.append(row)
            ideal.append(ideal_row)
        return rounded_kernel, observation, ideal
