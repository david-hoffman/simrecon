"""Public pytest CLI acceptance for the approved failed-only retention policy."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from fixture_lifecycle_fixture import PAYLOAD, ChildRun, make_child_run
from fixture_lifecycle_fixture import child_run as child_run_fixture  # noqa: F401


def assert_neighbor(record: dict[str, object]) -> None:
    assert (Path(str(record["neighbor"])) / "keep.bin").read_bytes() == PAYLOAD


def test_passing_call_releases_before_next_consumer(child_run: ChildRun) -> None:
    status = child_run.pytest(
        """
        def test_01_first(tmp_path, tmp_path_factory, module_data, session_data):
            assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
            assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
            observe('first', tmp_path, tmp_path_factory,
                    module=str(module_data), session=str(session_data))

        def test_02_remaining_consumer(module_data, session_data):
            first = json.loads((RECORDS / 'first.json').read_text())
            assert Path(first['base']).is_dir(), 'session ended before live observation'
            assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
            assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
            save('live-observer', module=str(module_data), session=str(session_data))
            assert not Path(first['path']).exists(), 'passing function retained during session'
        """
    )
    first = child_run.record("first")
    assert_neighbor(first)
    assert status == 0, f"Passing child did not pass: {child_run.records}"
    assert child_run.record("live-observer")["module"] == first["module"]
    assert child_run.record("module-release-master")["path"] == first["module"]
    assert child_run.record("session-release-master")["path"] == first["session"]


def test_successful_default_session_releases_factory_after_all_consumers(
    child_run: ChildRun,
) -> None:
    status = child_run.pytest(
        """
        def test_01_factory_consumer(tmp_path_factory, module_data, session_data):
            assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
            assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
            observe('factory-first', module_data, tmp_path_factory, session=str(session_data))

        def test_02_factory_consumer(module_data, session_data):
            first = json.loads((RECORDS / 'factory-first.json').read_text())
            assert first['path'] == str(module_data)
            assert first['session'] == str(session_data)
            assert (module_data / 'payload.bin').read_bytes() == PAYLOAD
            assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
            assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
            save('factory-second', module=str(module_data), session=str(session_data))
        """
    )
    assert status == 0, f"Factory-only default session must genuinely pass: {child_run.records}"
    first = child_run.record("factory-first")
    assert child_run.record("factory-second")["module"] == first["path"]
    assert child_run.record("module-release-master")["path"] == first["path"]
    assert child_run.record("session-release-master")["path"] == first["session"]
    assert_neighbor(first)
    assert not Path(first["base"]).exists(), f"Default session retained: {child_run.records}"
    assert not Path(first["path"]).exists()
    assert not Path(first["session"]).exists()


def test_failed_call_keeps_payload_and_unsuccessful_session(child_run: ChildRun) -> None:
    status = child_run.pytest(
        """
        def test_call_failure(tmp_path, tmp_path_factory):
            observe('failed', tmp_path, tmp_path_factory)
            assert False, 'intentional call failure for retention observation'
        """
    )
    assert status == 1, f"Intentional failing call must remain nonpassing: {child_run.records}"
    observed = child_run.record("failed")
    path = Path(observed["path"])
    assert (path / "payload.bin").read_bytes() == PAYLOAD
    assert Path(observed["base"]).is_dir()
    assert (path / "file-link").read_bytes() == PAYLOAD
    assert (path / "directory-link" / "input.bin").read_bytes() == PAYLOAD
    assert_neighbor(observed)


def test_failed_session_history_keeps_three_actual_payloads(child_run: ChildRun) -> None:
    """Carry real completed-session snapshots into fresh, private temp namespaces."""
    relative_payloads: list[Path] = []
    current = child_run
    workspaces = [current]
    for index in range(4):
        if index:
            following = make_child_run(child_run.home.parent)
            # Copy only this test's closed child TMPDIR. Keep original evidence intact.
            shutil.copytree(
                current.temporary, following.temporary, dirs_exist_ok=True, symlinks=True
            )
            current = following
            workspaces.append(current)
        status = current.pytest(
            """
            def test_failed_history(tmp_path, tmp_path_factory):
                observe('history', tmp_path, tmp_path_factory)
                assert False, 'intentional failed call for count-three compatibility'
            """
        )
        assert status == 1, f"Intentional history failure must remain nonpassing: {current.records}"
        observed = current.record("history")
        payload = Path(observed["path"]) / "payload.bin"
        relative_payloads.append(payload.relative_to(current.temporary))
        assert payload.read_bytes() == PAYLOAD
        assert_neighbor(observed)
    retained = [(current.temporary / relative).exists() for relative in relative_payloads]
    assert retained == [False, True, True, True], f"Count-three history changed: {current.records}"
    for relative in relative_payloads[1:]:
        assert (current.temporary / relative).read_bytes() == PAYLOAD
    # Copied symlinks still refer to the original external targets. Pruning a later
    # snapshot must preserve earlier workspaces' targets and original link bytes too.
    for workspace in workspaces:
        expected = json.loads((workspace.records / "preservation-before.json").read_text())
        assert workspace.preserved() == expected


@pytest.mark.parametrize("outcome", ["setup_error", "setup_skip", "late_teardown_error"])
def test_no_call_failure_allows_function_release(child_run: ChildRun, outcome: str) -> None:
    setup = {
        "setup_error": "raise RuntimeError('intentional setup error after construction')",
        "setup_skip": "pytest.skip('intentional setup skip after construction')",
        "late_teardown_error": (
            "yield tmp_path\n    raise RuntimeError('intentional late teardown error')"
        ),
    }[outcome]
    source = (
        "@pytest.fixture\n"
        "def affected(tmp_path, tmp_path_factory):\n"
        "    observe('affected', tmp_path, tmp_path_factory)\n"
        f"    {setup}\n\n"
        "def test_affected(affected):\n"
        "    assert (affected / 'payload.bin').read_bytes() == PAYLOAD\n"
    )
    status = child_run.pytest(source)
    assert status == 1, (
        f"Strict policy must keep intentional error/skip nonpassing: {child_run.records}"
    )
    observed = child_run.record("affected")
    assert not Path(observed["path"]).exists(), f"Eligible scratch retained: {child_run.records}"
    assert_neighbor(observed)


@pytest.mark.parametrize("outcome", ["skip", "xfail", "xpass"])
def test_call_outcome_policy_stays_strict_without_overpromising_retention(
    child_run: ChildRun, outcome: str
) -> None:
    action = {
        "skip": "pytest.skip('intentional call skip')",
        "xfail": "pytest.xfail('intentional expected failure')",
        "xpass": "assert True",
    }[outcome]
    decorator = (
        "@pytest.mark.xfail(reason='intentional unexpected pass')\n" if outcome == "xpass" else ""
    )
    status = child_run.pytest(
        decorator
        + "def test_outcome(tmp_path, tmp_path_factory):\n"
        + "    observe('outcome', tmp_path, tmp_path_factory)\n"
        + f"    {action}\n"
    )
    assert status == 1, f"Strict policy must reject {outcome}: {child_run.records}"
    observed = child_run.record("outcome")
    # The contract permits retention for skip/xfail; it does not require it.
    path = Path(observed["path"])
    if path.exists():
        assert (path / "payload.bin").read_bytes() == PAYLOAD
    assert_neighbor(observed)


def test_explicit_base_keeps_factory_data_but_releases_passing_function(
    child_run: ChildRun,
) -> None:
    status = child_run.pytest(
        """
        def test_explicit(tmp_path, tmp_path_factory, module_data, session_data):
            observe('explicit', tmp_path, tmp_path_factory,
                    module=str(module_data), session=str(session_data))
            assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
            assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
        """,
        explicit=True,
    )
    assert status == 0, f"Explicit-base positive child failed: {child_run.records}"
    observed = child_run.record("explicit")
    assert Path(observed["base"]) == child_run.home / "explicit-unused-base"
    assert Path(observed["base"]).is_dir()
    assert (Path(observed["module"]) / "factory.bin").read_bytes() == PAYLOAD
    assert (Path(observed["session"]) / "factory.bin").read_bytes() == PAYLOAD
    assert not Path(observed["path"]).exists(), f"Passing scratch retained: {child_run.records}"
    assert_neighbor(observed)


def test_four_real_workers_keep_groups_and_factory_consumers_until_release(
    child_run: ChildRun,
) -> None:
    source = ""
    for group in range(4):
        source += f"""
@pytest.mark.xdist_group(name='resource-{group}')
def test_group_{group}_first(tmp_path, tmp_path_factory, module_data, session_data, worker_id):
    assert worker_id != 'master'
    assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
    assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
    observe('group-{group}-first', tmp_path, tmp_path_factory,
            worker=worker_id, module=str(module_data), session=str(session_data))

@pytest.mark.xdist_group(name='resource-{group}')
def test_group_{group}_second(module_data, session_data, worker_id):
    first = json.loads((RECORDS / 'group-{group}-first.json').read_text())
    assert first['worker'] == worker_id
    assert first['module'] == str(module_data)
    assert first['session'] == str(session_data)
    assert (module_data / 'factory.bin').read_bytes() == PAYLOAD
    assert (session_data / 'factory.bin').read_bytes() == PAYLOAD
    save('group-{group}-second', worker=worker_id)
    assert not Path(first['path']).exists(), 'passing function retained while worker still live'
"""
    status = child_run.pytest(source, parallel=True)
    observations = [child_run.record(f"group-{group}-first") for group in range(4)]
    assert len({item["worker"] for item in observations}) == 4
    for group, observed in enumerate(observations):
        worker = observed["worker"]
        # Worker bases sit below the controller's numbered session base.
        assert not Path(observed["base"]).parent.exists(), (
            f"Controller base retained: {child_run.records}"
        )
        assert not Path(observed["module"]).exists()
        assert not Path(observed["session"]).exists()
        assert child_run.record(f"module-release-{worker}")["path"] == observed["module"]
        assert child_run.record(f"session-release-{worker}")["path"] == observed["session"]
        assert_neighbor(observed)
        if status == 0:
            assert child_run.record(f"group-{group}-second")["worker"] == worker
    assert status == 0, f"Four-worker positive child failed: {child_run.records}"
