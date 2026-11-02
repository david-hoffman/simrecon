"""Reject incomplete test execution through pytest's native session hook."""

from typing import cast

import pytest
from _pytest.terminal import TerminalReporter

PARALLEL_GROUPS: dict[str, str] = {}


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Assign whole-file affinity before xdist appends its loadgroup suffix."""
    if not (hasattr(config, "workerinput") and config.getoption("loadgroup", default=False)):
        return
    for item in items:
        relative = item.nodeid.partition("::")[0]
        item.add_marker(pytest.mark.xdist_group(PARALLEL_GROUPS.get(relative, "serial-rest")))


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Keep diagnostic reports while making omitted or marked failures nonzero."""
    terminal = cast(TerminalReporter, session.config.pluginmanager.get_plugin("terminalreporter"))
    if any(terminal.stats.get(outcome) for outcome in ("skipped", "xfailed", "xpassed")):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
