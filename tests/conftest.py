"""Keep shared test resources together under pytest-xdist loadgroup scheduling."""

import pytest

_READER_CACHE_USERS = {
    "test_shared_node_baseline_public_callers.py": frozenset(
        {
            "test_actual_reader_cached_identity_and_standard_loading",
            "test_actual_reader_path_selected_java",
            "test_actual_reader_selected_java_rejection",
            "test_actual_reader_invalid_cached_jar_preserved",
            "test_transport_actual_reader_authenticated_download",
            "test_parent_deadline_actual_reader_slow_active_transport",
            "test_owned_invoke_exception_cleanup_before_cache_restore",
        }
    ),
    "test_shared_node_baseline_infrastructure.py": frozenset(
        {
            "test_authentic_cached_reader_with_real_selected_java",
            "test_reader_failure_removes_stale_identity_without_replacing_cache",
        }
    ),
    "test_shared_node_baseline_infrastructure_supplement.py": frozenset(
        {
            "test_reader_authentic_cached_acceptance",
            "test_reader_selected_java_requires_identity_and_source_launcher",
            "test_reader_transport_authentic_missing_input_acceptance_and_public_url_binding",
            "test_reader_transport_rejections_preserve_cache_and_cleanup_scoped_bytes",
        }
    ),
}
_EVIDENCE_BASELINES = frozenset(
    {
        "_observed_success_baseline",
        "_native_success_baseline",
        "_observed_tests_failure_baseline",
        "_observed_late_failure_baseline",
        "_current_log_failure_baseline",
        "_current_partial_failure_baseline",
        "_current_stronger_wheel_failure_baseline",
    }
)


def pytest_itemcollected(item: pytest.Item) -> None:
    """Retain original identity before grouping changes xdist transport IDs."""
    item.user_properties.append(("simrecon.semantic_nodeid", item.nodeid))


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Assign each shared-resource consumer one group before xdist reads marks."""
    for item in items:
        if not isinstance(item, pytest.Function):
            continue
        module = item.path.name
        name = item.originalname or item.name
        if module == "test_imagej_export.py" or name in _READER_CACHE_USERS.get(
            module, frozenset()
        ):
            item.add_marker(pytest.mark.xdist_group(name="imagej_reader_cache"))
        elif module == "test_verification_evidence_outputs.py" and _EVIDENCE_BASELINES.intersection(
            item.fixturenames
        ):
            item.add_marker(pytest.mark.xdist_group(name="verification_evidence_baselines"))
