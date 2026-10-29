"""Reject incomplete test execution through pytest's native session hook."""

from typing import cast

import pytest
from _pytest.terminal import TerminalReporter

PARALLEL_GROUPS = {
    "tests/test_image_only_bead_calibration.py": "science-test_image_only_bead_calibration",
    "tests/test_image_only_calibration_pilot.py": "science-test_image_only_calibration_pilot",
    "tests/test_simulation_optics_certification.py": "science-test_simulation_optics_certification",
    "tests/test_empirical_frequency_sampling.py": "science-test_empirical_frequency_sampling",
    "tests/test_empirical_shared_nodes.py": "science-test_empirical_shared_nodes",
    "tests/test_full_noisy_study.py": "science-test_full_noisy_study",
    "tests/test_volume_phase_estimation.py": "science-test_volume_phase_estimation",
    "tests/test_observable_volume_phase_estimation.py": (
        "science-test_observable_volume_phase_estimation"
    ),
    "tests/test_reconstruction.py": "science-test_reconstruction",
    "tests/test_volume_order_gain.py": "science-test_volume_order_gain",
    "tests/test_empirical_volume_response.py": "science-test_empirical_volume_response",
    "tests/test_finite_bead_compensation.py": "science-test_finite_bead_compensation",
    "tests/test_empirical_trilinear_transfer.py": "science-test_empirical_trilinear_transfer",
    "tests/test_empirical_transfer_adapter.py": "science-test_empirical_transfer_adapter",
    "tests/test_volume_carrier_diagnostics.py": "science-test_volume_carrier_diagnostics",
    "tests/test_volume_carrier_selection.py": "science-test_volume_carrier_selection",
    "tests/test_phase_separation.py": "science-test_phase_separation",
    "tests/test_simulation_inverse_operator.py": "science-test_simulation_inverse_operator",
}


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
