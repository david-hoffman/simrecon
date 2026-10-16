"""Shared finite-component checks and scoped scientific conversion errors."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import numpy as np

from ._model import SimreconError


def require_finite(value: Any, code: str, message: str) -> None:
    """Reject nonfinite real or imaginary components without magnitude tests."""
    if not np.isfinite(value).all():
        raise SimreconError(code, message)


@contextmanager
def conversion_errors(code: str, message: str) -> Iterator[None]:
    """Translate only expected errors from the enclosed conversion operation."""
    try:
        yield
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, message) from error
