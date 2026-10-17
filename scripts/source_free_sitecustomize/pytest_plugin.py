"""Render pytest collection exceptions before source-bearing reports reach output."""

from __future__ import annotations

import traceback
from collections.abc import Generator
from typing import Any

import pytest
from _pytest.config import ConftestImportFailure
from _pytest.pathlib import ImportPathMismatchError
from _pytest.python import importtestmodule


@pytest.hookimpl(wrapper=True)
def pytest_load_initial_conftests(early_config: pytest.Config) -> Generator[None]:
    """Keep startup import failures at pytest's usage-error status without source."""
    try:
        yield
    except ConftestImportFailure as error:
        # Pytest handles help/version failures itself without printing a traceback.
        # These parsed early options precede Config.option being populated.
        options = early_config.known_args_namespace
        if options.help or options.version:
            raise
        diagnostic = "".join(traceback.format_exception(error.cause))
        raise pytest.UsageError(
            f"ImportError while loading conftest '{error.path}'.\n{diagnostic}"
        ) from error


def pytest_exception_interact(
    call: pytest.CallInfo[Any], report: pytest.CollectReport | pytest.TestReport
) -> None:
    """Replace collection rendering using the retained original exception chain."""
    if isinstance(report, pytest.CollectReport):
        assert call.excinfo is not None
        exception = call.excinfo.value
        origin = exception.__traceback__
        while origin is not None and origin.tb_next is not None:
            origin = origin.tb_next
        # Only pytest's own importer embeds rendered source in this wrapper.
        # Caller-authored CollectError messages and categories must survive.
        # Use the raising code's identity, never rendered text or source lines.
        if (
            type(exception) is pytest.Collector.CollectError
            and isinstance(exception.__cause__, (SyntaxError, ImportError))
            and not isinstance(exception.__cause__, ImportPathMismatchError)
            and origin is not None
            and origin.tb_frame.f_code is importtestmodule.__code__
        ):
            exception = exception.__cause__
        report.longrepr = "".join(traceback.format_exception(exception))
