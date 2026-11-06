"""External operation faults; never replace a scientific decision or expected value."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import scipy.fft

from c_workflow_oracle import constant_case, observe
from c_workflow_support import assert_scientific, entry, keywords, public


class BackendFailure(RuntimeError):
    """Represent an unavailable external numerical backend."""


def chain_contains(error: BaseException, target: BaseException) -> bool:
    seen: set[int] = set()
    while id(error) not in seen:
        if error is target:
            return True
        seen.add(id(error))
        if error.__cause__ is None:
            return False
        error = error.__cause__
    return False


@pytest.mark.parametrize("kind", [MemoryError, KeyboardInterrupt])
def test_external_allocation_or_interruption_propagates(
    kind: type[BaseException], monkeypatch: Any
) -> None:
    function = entry()
    case = constant_case()
    kwargs = keywords(case)
    expected = observe(case)
    sentinel = kind("CE07 injected external array allocation/interruption")
    calls: list[str] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        calls.append("external-array-operation")
        raise sentinel

    outcome = None
    caught: BaseException | None = None
    # NumPy allocation is an external dependency, not a product injection
    # seam. Do not prescribe how a legitimate implementation binds imports.
    with monkeypatch.context() as patch:
        for name in (
            "array",
            "empty",
            "zeros",
            "ones",
            "full",
            "empty_like",
            "zeros_like",
            "ones_like",
            "copy",
            "stack",
            "concatenate",
        ):
            patch.setattr(np, name, fail)
        try:
            outcome = function(case.raw, **kwargs)
        except BaseException as error:
            caught = error
    if calls:
        assert caught is not None and isinstance(caught, kind)
        assert chain_contains(caught, sentinel)
    else:
        # No interception is an admissible import/backend alternative, not
        # evidence that allocation-failure translation has been exercised.
        assert caught is None
        assert_scientific(case, outcome, expected)


def test_external_fft_failure_retains_original_cause(monkeypatch: Any) -> None:
    function = entry()
    case = constant_case()
    kwargs = keywords(case)
    expected = observe(case)
    sentinel = BackendFailure("CE07 external transform backend unavailable")
    calls: list[str] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        calls.append("fft")
        raise sentinel

    class FailingBackend:
        """Implement SciPy's public FFT dispatcher backend protocol."""

        __ua_domain__ = "numpy.scipy.fft"

        @staticmethod
        def __ua_function__(method: Any, args: Any, kwargs: Any) -> Any:
            return fail()

    caught: BaseException | None = None
    outcome = None
    with monkeypatch.context() as patch, scipy.fft.set_backend(FailingBackend(), only=True):
        for module in (np.fft, scipy.fft):
            for name in (
                "fft",
                "ifft",
                "fftn",
                "ifftn",
                "fft2",
                "ifft2",
                "rfft",
                "irfft",
                "rfftn",
                "irfftn",
                "rfft2",
                "irfft2",
            ):
                patch.setattr(module, name, fail)
        try:
            outcome = function(case.raw, **kwargs)
        except Exception as error:
            caught = error
    if calls:
        assert caught is not None
        assert isinstance(caught, public().WorkflowError)
        workflow_error: Any = caught
        assert workflow_error.code == "workflow_operation"
        assert workflow_error.stage in ("preparation", "estimation", "reconstruction")
        assert caught.__cause__ is not None
        assert chain_contains(caught, sentinel)
    else:
        assert caught is None
        assert_scientific(case, outcome, expected)
