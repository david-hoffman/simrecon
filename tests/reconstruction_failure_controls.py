"""Source-free runner and operation-failure probes at public backend boundaries."""

from __future__ import annotations

import contextlib
import importlib
import json
import re
import sys
import warnings
from collections.abc import Callable, Iterable
from typing import Any

from reconstruction_fixture import (
    accuracy_budget,
    assert_coordinates,
    basic,
    public,
    source_free_diagnostics,
)

source_free_diagnostics()


def warning_records(captured: Iterable[warnings.WarningMessage]) -> list[dict[str, Any]]:
    """Keep warning evidence without requesting a source line from Python."""
    return [
        {
            "category": item.category.__name__,
            "message": str(item.message),
            "filename": item.filename,
            "line": item.lineno,
            "runtime_warning": issubclass(item.category, RuntimeWarning),
        }
        for item in captured
    ]


def assert_no_arithmetic_warnings(evidence: dict[str, Any]) -> None:
    """Reject identified arithmetic RuntimeWarnings, retaining other diagnostics.

    The warning category alone does not make an arbitrary diagnostic arithmetic.
    NumPy reports an error kind AND the operation where it was encountered.
    Match that complete report, including the documented scalar-operation form.
    A configuration/fallback diagnostic mentioning an error kind is not such a
    report. Preserve unmatched diagnostics rather than inventing a warning ban.
    """
    arithmetic = re.compile(
        r"(?:overflow|underflow|invalid value|divide by zero) encountered in "
        r"(?:scalar )?[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*",
        re.I,
    )
    assert not any(
        item["runtime_warning"] and arithmetic.fullmatch(item["message"].strip())
        for item in evidence["warnings"]
    ), evidence


def numerical_probe(
    failure: str, phase: bool = False, *, operation: Callable[[], Any] | None = None
) -> dict[str, Any]:
    """Patch public numerical backends before importing the public product API.

    A backend-free implementation is allowed: if no patched boundary is called,
    its ordinary constant result is checked instead. This is not evidence of a
    simulated failure path. Never inspect or patch private product objects.

    An owned operation may be supplied solely to validate this observer. The
    production-control subprocess always uses the real public entry instead.
    """
    events: list[str] = []
    originals: list[tuple[Any, str, Any]] = []
    names = (
        [("numpy.linalg", ("svd", "lstsq")), ("scipy.linalg", ("svd", "lstsq"))]
        if phase
        else [
            ("numpy.fft", ("fft", "fft2", "fftn", "ifft", "ifft2", "ifftn")),
            ("scipy.fft", ("fft", "fft2", "fftn", "ifft", "ifft2", "ifftn")),
            ("scipy.fftpack", ("fft", "fft2", "fftn", "ifft", "ifft2", "ifftn")),
        ]
    )
    import numpy as np

    def wrapper(original: Any, name: str) -> Any:
        def invoke(*args: Any, **kwargs: Any) -> Any:
            events.append(name)
            kinds = {
                "value": ValueError,
                "floating": FloatingPointError,
                "overflow": OverflowError,
                "memory": MemoryError,
                "unrelated": RuntimeError,
                "linalg": np.linalg.LinAlgError,
            }
            if failure in kinds:
                raise kinds[failure]("public backend control")
            result = original(*args, **kwargs)
            if isinstance(result, tuple):
                return tuple(
                    np.full_like(item, np.nan) if isinstance(item, np.ndarray) else item
                    for item in result
                )
            return np.full_like(result, np.nan)

        return invoke

    captured = []
    try:
        for module_name, attributes in names:
            module = importlib.import_module(module_name)
            for name in attributes:
                original = getattr(module, name)
                originals.append((module, name, original))
                setattr(module, name, wrapper(original, f"{module_name}.{name}"))
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            arguments = basic()
            if operation is None:
                api = public()
                assert hasattr(api, "Reconstruction2D"), "Missing public Reconstruction2D"
                result = api.reconstruct(**arguments)
            else:
                result = operation()
            budget = accuracy_budget(arguments)
            expected = np.zeros((6, 8), dtype=np.complex128)
            expected[3, 4] = -2.5 / 1.125
            assert_coordinates(result.spectrum, expected, budget)
            assert_coordinates(result.image, -2.5 / 1.125, budget)
            return {"outcome": "normal", "events": events, "warnings": warning_records(captured)}
    except BaseException as error:
        frames = []
        traceback = error.__traceback__
        while traceback is not None:
            frames.append(
                {"filename": traceback.tb_frame.f_code.co_filename, "line": traceback.tb_lineno}
            )
            traceback = traceback.tb_next
        return {
            "outcome": "error",
            "type": type(error).__name__,
            "code": getattr(error, "code", None),
            "message": str(error),
            "events": events,
            "frames": frames,
            "warnings": warning_records(captured),
        }
    finally:
        for module, name, original in reversed(originals):
            setattr(module, name, original)


class SourceFreeWarnings:
    """Retain pytest warning diagnostics without pytest's source-line summary."""

    def __init__(self) -> None:
        self.diagnostics: list[dict[str, Any]] = []
        self.statuses: list[dict[str, Any]] = []

    def pytest_runtest_logreport(self, report: Any) -> None:
        self.statuses.append(
            {"nodeid": report.nodeid, "phase": report.when, "outcome": report.outcome}
        )

    def pytest_exception_interact(self, node: Any, call: Any, report: Any) -> None:
        error = call.excinfo.value
        frames = []
        traceback = error.__traceback__
        while traceback is not None:
            frames.append(
                {"filename": traceback.tb_frame.f_code.co_filename, "line": traceback.tb_lineno}
            )
            traceback = traceback.tb_next
        self.diagnostics.append(
            {
                "nodeid": report.nodeid,
                "phase": report.when,
                "outcome": report.outcome,
                "category": type(error).__name__,
                "message": str(error),
                "code": getattr(error, "code", None),
                "frames": frames,
            }
        )

    def pytest_warning_recorded(
        self, warning_message: Any, when: Any, nodeid: Any, location: Any
    ) -> None:
        item = warning_message
        print(f"{item.filename}:{item.lineno}: {item.category.__name__}: {item.message}")


def main() -> int:
    """Run narrow pytest or print only structured, source-free probe evidence."""
    if sys.argv[1:2] == ["--simulate"]:
        print(json.dumps(numerical_probe(sys.argv[2], phase="--phase" in sys.argv[3:])))
        return 0
    if sys.argv[1:2] == ["--pytest"]:
        import pytest

        arguments = sys.argv[2:]
        diagnostics = SourceFreeWarnings()
        if "--diagnostic-log" in arguments:
            index = arguments.index("--diagnostic-log")
            path = arguments[index + 1]
            arguments = arguments[:index] + arguments[index + 2 :]
            with open(path, "w", encoding="utf-8") as stream:
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    status = pytest.main(
                        [
                            "tests/test_reconstruction.py",
                            "--tb=no",
                            "--disable-warnings",
                            *arguments,
                        ],
                        plugins=[diagnostics],
                    )
                stream.write("\nSOURCE-FREE EXCEPTION DIAGNOSTICS\n")
                for item in diagnostics.diagnostics:
                    stream.write(json.dumps(item) + "\n")
                stream.write("\nTEST PHASE STATUSES\n")
                for item in diagnostics.statuses:
                    stream.write(json.dumps(item) + "\n")
                stream.write(json.dumps({"pytest_exit_status": int(status)}) + "\n")
            outcomes: dict[str, int] = {}
            categories: dict[str, int] = {}
            for item in diagnostics.statuses:
                if item["phase"] == "call":
                    outcome = item["outcome"]
                    outcomes[outcome] = outcomes.get(outcome, 0) + 1
            for item in diagnostics.diagnostics:
                category = item["category"]
                categories[category] = categories.get(category, 0) + 1
            print(
                json.dumps(
                    {
                        "exit_status": int(status),
                        "call_outcomes": outcomes,
                        "exception_categories": categories,
                        "log": path,
                    }
                )
            )
            return int(status)
        return int(
            pytest.main(
                ["tests/test_reconstruction.py", "--tb=no", "--disable-warnings", *arguments],
                plugins=[diagnostics],
            )
        )
    return 2


if __name__ == "__main__":
    with contextlib.suppress(BrokenPipeError):
        raise SystemExit(main())
