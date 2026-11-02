"""Physical-period phase arithmetic shared by inference and study tools."""

from __future__ import annotations

import math
from decimal import ROUND_FLOOR, Decimal, localcontext
from functools import lru_cache
from typing import Any

import numpy as np


def _dec(value: Any) -> Decimal:
    return Decimal.from_float(float(value))


@lru_cache(maxsize=1)
def _physical_pi() -> Decimal:
    # Chudnovsky, evaluated past the precision needed for all finite binary64
    # phases and origin products. Decimal avoids the rounded-2*pi period.
    with localcontext() as ctx:
        ctx.prec = 820
        m, series_term, x, k = 1, 13591409, 1, 6
        total = Decimal(series_term)
        for n in range(1, 60):
            m = m * (k**3 - 16 * k) // n**3
            series_term += 545140134
            x *= -262537412640768000
            total += Decimal(m * series_term) / Decimal(x)
            k += 12
        return +(426880 * Decimal(10005).sqrt() / total)


def _wrap(value: Decimal) -> float:
    pi = _physical_pi()
    reduced = value - ((value + pi) / (2 * pi)).to_integral_value(rounding=ROUND_FLOOR) * (2 * pi)
    result = float(reduced)
    return -math.pi if result >= math.pi else result


def _transfer(phases: Any, q: Any, origin: Any, destination: Any) -> Any:
    with localcontext() as ctx:
        ctx.prec = 800
        shift = [_dec(destination[i]) - _dec(origin[i]) for i in (1, 2)]
        return np.array(
            [
                [
                    _wrap(
                        _dec(phases[o][p])
                        + 2
                        * _physical_pi()
                        * sum((_dec(q[o][i]) * shift[i] for i in range(2)), Decimal(0))
                    )
                    for p in range(5)
                ]
                for o in range(3)
            ],
            dtype=np.float64,
        )
