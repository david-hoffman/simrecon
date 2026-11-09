"""Configure distributed test affinity and reject incomplete test execution."""

from typing import cast

import pytest
from _pytest.terminal import TerminalReporter

# One group protects the live reader cache across its mutator and consumers.
_IMAGEJ_CACHE_MODULES = {
    "test_imagej_export",
    "test_shared_node_baseline_infrastructure",
    "test_shared_node_baseline_infrastructure_supplement",
    "test_shared_node_baseline_public_callers",
}

# Preserve expensive process-local reuse independently for each module.
_FILE_AFFINITY_MODULES = {
    "test_empirical_frequency_sampling",
    "test_empirical_shared_nodes",
    "test_empirical_transfer_adapter",
    "test_empirical_trilinear_transfer",
    "test_empirical_volume_response",
    "test_finite_bead_compensation",
    "test_full_noisy_study",
    "test_image_only_bead_calibration",
    "test_image_only_calibration_pilot",
    "test_image_only_specimen_fit",
    "test_observable_volume_phase_estimation",
    "test_phase_separation",
    "test_reconstruction",
    "test_reference_fixture_export",
    "test_simulation_inverse_operator",
    "test_simulation_inverse_operator_range_correction",
    "test_simulation_optics",
    "test_simulation_optics_aggregates",
    "test_simulation_optics_certification",
    "test_simulation_optics_memory",
    "test_verification_evidence_outputs",
    "test_verification_output_protection",
    "test_volume_carrier_diagnostics",
    "test_volume_carrier_selection",
    "test_volume_order_gain",
    "test_volume_otf",
    "test_volume_phase_estimation",
    "test_volume_phases",
    "test_volume_reconstruction",
}


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Mark only declared files before xdist records loadgroup node IDs."""
    if not (hasattr(config, "workerinput") and config.getoption("loadgroup", default=False)):
        return

    tests = config.rootpath / "tests"
    for item in items:
        if item.path.parent != tests or item.path.suffix != ".py":
            continue
        module = item.path.stem
        if module in _IMAGEJ_CACHE_MODULES:
            item.add_marker(pytest.mark.xdist_group("imagej-cache"))
        elif module in _FILE_AFFINITY_MODULES:
            item.add_marker(pytest.mark.xdist_group(module))


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Keep diagnostic reports while making omitted or marked failures nonzero."""
    terminal = cast(TerminalReporter, session.config.pluginmanager.get_plugin("terminalreporter"))
    if any(terminal.stats.get(outcome) for outcome in ("skipped", "xfailed", "xpassed")):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
