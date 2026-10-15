"""C80/R11/P11: configured external native evidence and safe receipt outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from coverage import CoverageData

from shared_node_baseline_external_native_evidence_fixture import PHASES, invoke, prepare


def assert_current_evidence(case: dict) -> dict:
    """Bind real measurement and emitted bytes to this invocation, not stale data."""
    observations = case["observations"]
    snapshot = json.loads((observations / "snapshot.json").read_text())
    assert snapshot["nonce"] == case["nonce"]
    assert snapshot["database"] == str(case["database"])
    assert snapshot["contexts"] == [case["nonce"]]
    assert set(snapshot["records"]) == {"src/simrecon/__init__.py", "scripts/probe.py"}
    assert snapshot["records"]["src/simrecon/__init__.py"]["lines"] == [1]
    assert snapshot["records"]["scripts/probe.py"]["lines"] == [1, 2, 3, 4, 6]
    assert snapshot["records"]["scripts/probe.py"]["arcs"]
    assert case["database"].read_bytes() == (observations / "native-before.bin").read_bytes(), (
        "Verifier persistence replaced the actual current configured native database"
    )
    data = CoverageData(basename=str(case["database"]))
    data.read()
    assert sorted(data.measured_contexts()) == [case["nonce"]]
    actual = {
        name: {
            "lines": sorted(data.lines(name) or []),
            "arcs": sorted([list(arc) for arc in data.arcs(name) or []]),
        }
        for name in data.measured_files()
    }
    assert actual == snapshot["records"]
    assert "artifacts/coverage/coverage.json" in snapshot["reports"]
    assert "artifacts/coverage/html/index.html" in snapshot["reports"]
    assert len(snapshot["reports"]) > 2
    for name, digest in (snapshot["reports"] | snapshot["wheels"]).items():
        assert hashlib.sha256((case["repo"] / name).read_bytes()).hexdigest() == digest
    return snapshot


def assert_passed_truth(case: dict, snapshot: dict) -> None:
    receipt = json.loads(case["receipt"].read_text())
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    assert [phase["name"] for phase in receipt["phases"]] == list(PHASES)
    for phase in receipt["phases"]:
        assert phase["returncode"] == 0
        assert phase["name"] in phase["command"]
        assert "UV=" + str(case["driver"]) in phase["command"]
        assert (case["repo"] / phase["log"]).read_bytes() == (
            case["observations"] / (phase["name"] + ".txt")
        ).read_bytes()
    assert receipt["artifact"]["sha256"] == snapshot["wheels"][receipt["artifact"]["path"]]
    assert receipt["before"] == receipt["after"]
    assert receipt["before"]["dirty"] is False
    trace = [
        json.loads(line) for line in (case["observations"] / "trace.jsonl").read_text().splitlines()
    ]
    assert [item["phase"] for item in trace] == list(PHASES)
    assert all(item["nonce"] == case["nonce"] for item in trace)
    # Independent counts from the two tiny owned sources: one assignment plus
    # five executable probe lines; loop and if each have two branch destinations.
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 6, "total": 6},
        "branches": {"covered": 4, "total": 4},
    }


@pytest.mark.parametrize("selector", ["coveragerc", "pyproject", "rcfile"])
@pytest.mark.parametrize(
    "destination", ["neighbor", "stale", "collision", "native-neighbor", "native-stale"]
)
def test_configured_external_native_receipt_preservation(
    tmp_path: Path,
    selector: str,
    destination: str,
) -> None:
    """Safe alternatives must pass; collision may reject honestly or preserve data."""
    case = prepare(tmp_path, selector, destination)
    result = invoke(case)
    # Keep child output out of assertion diagnostics: third-party text is not an oracle.
    snapshot_path = case["observations"] / "snapshot.json"
    if destination == "collision" and not snapshot_path.exists():
        assert result.returncode == 1, "Early evidence rejection must use status 1"
        measured = case["observations"] / "native-measured.bin"
        if measured.exists():
            assert case["database"].read_bytes() == measured.read_bytes(), (
                "Rejection after measurement must preserve the current native data"
            )
        elif case["receipt"].exists():
            # A receipt before data emission must honestly report failure.
            assert not (case["observations"] / "tests.txt").exists(), (
                "Native measurement ran: early rejection cannot excuse losing its data"
            )
            receipt = json.loads(case["receipt"].read_text())
            assert receipt["result"] == "failed"
            assert receipt["problems"]
        return
    assert snapshot_path.exists(), "The valid control must reach actual measurement and audit"
    snapshot = assert_current_evidence(case)
    if destination == "collision":
        assert result.returncode == 1, "A database cannot simultaneously be a passed JSON receipt"
    else:
        assert result.returncode == 0, "A legitimate external neighbor/stale output must pass"
        assert_passed_truth(case, snapshot)


@pytest.mark.parametrize("selector", ["coveragerc", "pyproject", "rcfile"])
@pytest.mark.parametrize("destination", ["neighbor", "collision"])
def test_project_local_python_preserves_external_native_evidence(
    tmp_path: Path, selector: str, destination: str
) -> None:
    """The ordinary local interpreter cannot weaken preservation or safe outputs."""
    case = prepare(tmp_path, selector, destination, local_python=True)
    assert (case["repo"] / ".venv/bin/python").is_file()
    assert (case["observations"] / "local-python-health.txt").read_bytes()
    result = invoke(case)
    if destination == "collision":
        assert_rejected_collision(case, result.returncode)
    else:
        assert result.returncode == 0, "A supported local interpreter and safe neighbor must pass"
        assert_passed_truth(case, assert_current_evidence(case))


def assert_rejected_collision(case: dict, status: int) -> None:
    """Allow early rejection; preserve genuine bytes whenever measurement ran."""
    assert status == 1, "A current database cannot also be a passed JSON receipt"
    observations = case["observations"]
    if (observations / "snapshot.json").exists():
        assert_current_evidence(case)
    elif (observations / "native-measured.bin").exists():
        assert case["database"].read_bytes() == (observations / "native-measured.bin").read_bytes()
    elif case["receipt"].exists():
        assert not (observations / "tests.txt").exists()
        receipt = json.loads(case["receipt"].read_text())
        assert receipt["result"] == "failed"
        assert receipt["problems"]


@pytest.mark.parametrize("loss", ["missing", "invalid"])
@pytest.mark.parametrize("destination", ["neighbor", "collision"])
def test_configuration_loss_after_emission_preserves_native_evidence(
    tmp_path: Path, loss: str, destination: str
) -> None:
    """Losing genuine configuration cannot authorize destroying current evidence."""
    case = prepare(tmp_path, "rcfile", destination, local_python=True, configuration_loss=loss)
    result = invoke(case)
    if destination == "collision":
        # Rejection before audit is legitimate: no private lookup order is required.
        assert_rejected_collision(case, result.returncode)
        return
    observations = case["observations"]
    event = json.loads((observations / "configuration-loss.json").read_text())
    assert event == {
        "nonce": case["nonce"],
        "phase": "audit",
        "loss": loss,
        "exists_after": loss != "missing",
    }
    snapshot = assert_current_evidence(case)
    receipt = json.loads(case["receipt"].read_text())
    # Reports are already genuine and complete. Either independent collection
    # can still prove their identity, or unavailable configuration fails honestly.
    if result.returncode == 0:
        assert_passed_truth(case, snapshot)
    else:
        assert result.returncode == 1
        assert receipt["result"] == "failed"
        assert receipt["problems"]
        assert receipt["before"] == receipt["after"]
        assert receipt["before"]["dirty"] is False


@pytest.mark.parametrize("loss", ["missing", "invalid"])
def test_configuration_loss_before_reporting_fails_without_losing_native_data(
    tmp_path: Path, loss: str
) -> None:
    """Real Coverage configuration errors stop verification and preserve its data."""
    case = prepare(
        tmp_path,
        "rcfile",
        "neighbor",
        local_python=True,
        configuration_loss=loss,
        loss_phase="coverage-combine",
    )
    result = invoke(case)
    observations = case["observations"]
    event = json.loads((observations / "configuration-loss.json").read_text())
    assert event["phase"] == "coverage-combine"
    assert event["loss"] == loss
    assert event["nonce"] == case["nonce"]
    assert result.returncode == 1
    assert case["database"].read_bytes() == (observations / "native-measured.bin").read_bytes()
    receipt = json.loads(case["receipt"].read_text())
    assert receipt["result"] == "failed"
    assert receipt["problems"]
    assert receipt["before"] == receipt["after"]
    assert receipt["before"]["dirty"] is False
    trace = [json.loads(line) for line in (observations / "trace.jsonl").read_text().splitlines()]
    attempted = [item["phase"] for item in trace]
    # An evidence check may reject before the next reporting command. If the
    # command runs, its real failure must be retained and no later phase may run.
    assert attempted in [list(PHASES[:7]), list(PHASES[:8])]
    assert [phase["name"] for phase in receipt["phases"]] == attempted
    if attempted[-1] == "coverage-json":
        assert receipt["phases"][-1]["returncode"] == 1
        assert (case["repo"] / receipt["phases"][-1]["log"]).read_bytes() == (
            observations / "coverage-json.txt"
        ).read_bytes()
