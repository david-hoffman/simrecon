"""Reject incomplete test execution through pytest's native session hook."""

from typing import cast

import pytest
from _pytest.terminal import TerminalReporter

# Measured, isolated array/workflow and disposable verifier files have affinity.
# Reader-cache users and every unlisted/new file retain the serial-rest group.
# Two cheap validation files frontload composition in xdist's case-count ordering.
PARALLEL_GROUPS: dict[str, str] = {
    f"tests/test_{name}.py": (
        "science-composition"
        if name in ("c_acquisition_composition", "c_otf_validation", "c_workflow_validation")
        else f"science-test_{name}"
    )
    for name in (
        "c_acquisition_2d",
        "c_acquisition_boundary",
        "c_acquisition_composition",
        "c_acquisition_drift",
        "c_acquisition_filter",
        "c_acquisition_fitted_drift",
        "c_acquisition_preparation",
        "c_acquisition_transfer",
        "c_estimation_boundary",
        "c_estimation_composition",
        "c_estimation_overlap",
        "c_estimation_search",
        "c_independent_large_recovery",
        "c_independent_matched_recovery",
        "c_independent_small_controls",
        "c_known_assembly",
        "c_known_boundary",
        "c_known_filter",
        "c_otf",
        "c_otf_validation",
        "c_preparation",
        "c_workflow_00_known",
        "c_workflow_compatibility",
        "c_workflow_failures",
        "c_workflow_numerical",
        "c_workflow_records",
        "c_workflow_validation",
    )
}
PARALLEL_GROUPS.update(
    {
        f"tests/test_{name}.py": f"infrastructure-test_{name}"
        for name in (
            "verification_evidence_outputs",
            "verification_receipt",
            "measurements_export",
            "verification_output_protection",
            "shared_node_baseline_external_native_evidence",
            "source_free_check",
        )
    }
)


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
