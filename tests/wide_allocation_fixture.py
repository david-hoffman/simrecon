"""Exact, allocation-free public geometry arithmetic for issue 115."""

from __future__ import annotations

from fractions import Fraction
from math import prod
from typing import Any

SIGNED_MAX = 2**31 - 1
M = 2**63 - 1
U = 2**32 - 1


def stride_bytes(shape: tuple[int, ...], itemsize: int) -> int:
    return itemsize * prod(max(d, 1) for d in shape)


def geometry(
    shape: tuple[int, ...], orders: int, lateral: int | float, axial: int
) -> dict[str, Any]:
    """Derive contract quantities without a production return value or float product."""
    t, d, p, z, y, x = shape
    lx, ly = Fraction(lateral) * x, Fraction(lateral) * y
    assert lx.denominator == ly.denominator == 1
    xo, yo, zo = int(lx), int(ly), axial * z
    q = 2 * orders - 1
    signed = dict(
        T=t,
        D=d,
        P=p,
        Z=z,
        Y=y,
        X=x,
        O=orders,
        Q=q,
        A=axial,
        Xo=xo,
        Yo=yo,
        Zo=zo,
        native_volume=x * y * z,
        padded_real=(x + 2) * y * z,
        half_volume=(x // 2 + 1) * y * z,
        output_plane=xo * yo,
        output_volume=xo * yo * zo,
        direction_z_phase=d * z * p,
        time_direction_z_phase=t * d * z * p,
        direction_phase_off=d * p,
        phase_matrix=q * p,
        direction_order=d * orders,
    )
    byte_counts = dict(
        complex_native=8 * x * y * z,
        complex_output=8 * xo * yo * zo,
        real_output=4 * xo * yo * zo,
        orders=8 * orders,
        lookup=4 * xo * yo,
    )
    arrays = dict(
        raw=(shape, 8),
        quadratures=((t, d, q, z, y, x // 2 + 1), 16),
        noise=((t, d, orders), 8),
        image=((t, zo, yo, xo), 8),
        complex_workspace=((zo, yo, xo), 16),
        lookup=((yo, xo), 8),
        all_order_half=((t, d, q, zo, yo, xo // 2 + 1), 16),
    )
    return dict(
        output_shape=(zo, yo, xo),
        signed=signed,
        bytes=byte_counts,
        arrays=arrays,
        native_bytes={name: stride_bytes(*value) for name, value in arrays.items()},
    )
