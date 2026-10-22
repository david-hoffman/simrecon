"""Reject incomplete test execution through pytest's native session hook."""

from typing import cast

import pytest
from _pytest.terminal import TerminalReporter
from xdist import is_xdist_worker


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Keep diagnostic reports while making omitted or marked failures nonzero."""
    if is_xdist_worker(session):
        return
    terminal = cast(TerminalReporter, session.config.pluginmanager.get_plugin("terminalreporter"))
    if any(terminal.stats.get(outcome) for outcome in ("skipped", "xfailed", "xpassed")):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
