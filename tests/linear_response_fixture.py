"""Public-contract fixtures and independent represented-arithmetic observers."""

from __future__ import annotations

import copy
import importlib
import math
import platform
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np

Array = np.ndarray[Any, Any]

SOURCE_FIELDS = (
    "axes",
    "source_axes",
    "source_shape",
    "acquisition_kind",
    "sampling_um",
    "wavelengths_nm",
    "nominal_phases_rad",
    "nominal_phase_axes",
    "intensity_unit",
    "acquisition_id",
    "calibration_id",
    "original_config",
    "original_metadata",
    "provenance",
)


def public_api() -> Any:
    """Lookup at runtime so absent exports produce source-free test failures."""
    module = importlib.import_module("simrecon")
    for name in ("correct_linear_response", "LinearResponseCorrection"):
        assert getattr(module, name, None) is not None, f"Missing public export: {name}"
    assert callable(module.correct_linear_response)
    assert isinstance(module.LinearResponseCorrection, type)
    return module


def acquisition(
    data: Array,
    *,
    axes: tuple[str, ...] = ("y", "x"),
    kind: str = "detection_psf",
    unit: Any = "count",
    config_extra: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Any:
    module = importlib.import_module("simrecon")
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": kind,
        "axes": list(axes),
        "intensity_unit": unit,
    }
    if config_extra:
        config.update(config_extra)
    return module.declare_acquisition(data, config=config, original_metadata=metadata)


def source_snapshot(record: Any) -> dict[str, Any]:
    """Only named R1 public fields; never inspect private record state."""
    return {name: copy.deepcopy(getattr(record, name)) for name in SOURCE_FIELDS}


def same_value(actual: Any, expected: Any) -> None:
    """Container-aware equality preserving dtype, signed zero and opaque NaNs."""
    assert type(actual) is type(expected)
    if isinstance(expected, np.ndarray):
        assert actual.shape == expected.shape
        assert actual.dtype == expected.dtype
        np.testing.assert_array_equal(actual, expected)
        if expected.dtype.kind == "f":
            np.testing.assert_array_equal(np.signbit(actual), np.signbit(expected))
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            same_value(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            same_value(left, right)
    elif isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(actual)
    elif isinstance(expected, float) and expected == 0.0:
        assert actual == 0.0
        assert math.copysign(1.0, actual) == math.copysign(1.0, expected)
    else:
        assert actual == expected


def mutable_arrays(value: Any) -> list[Array]:
    if isinstance(value, np.ndarray):
        return [value]
    if isinstance(value, dict):
        return [array for item in value.values() for array in mutable_arrays(item)]
    if isinstance(value, (list, tuple)):
        return [array for item in value for array in mutable_arrays(item)]
    return []


def rounded_signal(raw: Array, offset: Any, response: Any) -> Array:
    """Rational differences/quotients rounded separately by Python binary64.

    This observer uses neither NumPy subtraction/division nor product output.
    It is for finite nonzero ordinary examples; zero signs have analytic tests.
    """
    answer = np.empty(raw.shape, dtype=np.float64)
    for index in np.ndindex(raw.shape):
        pixel = float(raw[index])
        off = float(offset[index] if isinstance(offset, np.ndarray) else offset)
        gain = float(response[index] if isinstance(response, np.ndarray) else response)
        numerator = float(Fraction.from_float(pixel) - Fraction.from_float(off))
        answer[index] = float(Fraction.from_float(numerator) / Fraction.from_float(gain))
    return answer


def phase_design(phases: Array) -> Array:
    """Contract-defined binary64 phasor basis, not a product solver oracle."""
    c, s = np.cos(phases), np.sin(phases)
    return np.column_stack((np.ones(phases.size), c, s, c * c - s * s, (2 * c) * s))


def decimal_phase_coordinates(design: Array, images: Array) -> Array:
    """100-digit normal-equation oracle on the exact represented entries.

    Normal equations are permitted in the independent high-precision observer.
    Gaussian elimination with pivoting solves K'K z=K'b, K=H diag(1,2,-2,2,-2).
    """
    result = np.empty((5, *images.shape[1:]), dtype=np.float64)
    with localcontext() as context:
        context.prec = 100
        factors = (1, 2, -2, 2, -2)
        rows = [
            [Decimal.from_float(float(row[j])) * factors[j] for j in range(5)] for row in design
        ]
        gram = [
            [sum((row[i] * row[j] for row in rows), Decimal(0)) for j in range(5)] for i in range(5)
        ]
        for index in np.ndindex(images.shape[1:]):
            b = [Decimal.from_float(float(images[(p, *index)])) for p in range(len(rows))]
            rhs = [
                sum((row[j] * pixel for row, pixel in zip(rows, b, strict=True)), Decimal(0))
                for j in range(5)
            ]
            aug = [gram[j].copy() + [rhs[j]] for j in range(5)]
            for col in range(5):
                pivot = max(range(col, 5), key=lambda k: abs(aug[k][col]))
                aug[col], aug[pivot] = aug[pivot], aug[col]
                divisor = aug[col][col]
                assert divisor != 0
                aug[col] = [v / divisor for v in aug[col]]
                for row in range(5):
                    if row != col:
                        factor = aug[row][col]
                        aug[row] = [a - factor * v for a, v in zip(aug[row], aug[col], strict=True)]
            for j in range(5):
                result[(j, *index)] = float(aug[j][5])
    return result


if __name__ == "__main__":
    module = importlib.import_module("simrecon")
    print("Python", sys.version.split()[0], "NumPy", np.__version__, "platform", platform.system())
    for name in (
        "declare_acquisition",
        "RawAcquisition",
        "correct_linear_response",
        "LinearResponseCorrection",
        "separate_volume_phases",
        "SimreconError",
    ):
        print("public export", name, getattr(module, name, None) is not None)
    info = np.finfo(np.longdouble)
    print("longdouble bits/nmant/maxexp/minexp", info.bits, info.nmant, info.maxexp, info.minexp)
    declared = acquisition(np.array([[110]], dtype=">u2"))
    print("R1 prerequisite", declared.axes, declared.data.shape, declared.data.dtype.str)
