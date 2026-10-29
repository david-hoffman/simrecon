"""Public runner regressions for fixed parallel affinity and truthful outcomes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from parallel_runner_fixture import ROOT, observations, run, suite

# The approved whole-file contract is independent of the implementation mapping.
SCIENCE = (
    "image_only_bead_calibration",
    "image_only_calibration_pilot",
    "simulation_optics_certification",
    "empirical_frequency_sampling",
    "empirical_shared_nodes",
    "full_noisy_study",
    "volume_phase_estimation",
    "observable_volume_phase_estimation",
    "reconstruction",
    "volume_order_gain",
    "empirical_volume_response",
    "finite_bead_compensation",
    "empirical_trilinear_transfer",
    "empirical_transfer_adapter",
    "volume_carrier_diagnostics",
    "volume_carrier_selection",
    "phase_separation",
    "simulation_inverse_operator",
)


def test_real_make_tests_delivers_fixed_flags_to_selected_uv(tmp_path: Path) -> None:
    make = shutil.which("make")
    assert make is not None
    selected = tmp_path / "selected uv with spaces"
    observed = tmp_path / "argv.json"
    selected.write_text(
        f"#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\n"
        f"Path({str(observed)!r}).write_text(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    selected.chmod(0o755)
    result = subprocess.run(
        [make, "--no-print-directory", "tests", f"UV={selected}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(observed.read_text()) == [
        "run",
        "--locked",
        "coverage",
        "run",
        "-m",
        "pytest",
        "-n",
        "2",
        "--dist=loadgroup",
        "--max-worker-restart=0",
    ]


def test_whole_file_groups_preserve_exact_nodes_and_serial_mode(tmp_path: Path) -> None:
    names = sorted((*SCIENCE, "unclassified", "new_file"))
    files = {
        f"tests/test_{name}.py": "import pytest\ndef test_first():\n    assert True\n\n"
        '@pytest.mark.parametrize("label", ["original@science-test_volume_phase_estimation"])\n'
        "def test_second(label):\n"
        '    assert label == "original@science-test_volume_phase_estimation"\n'
        for name in names
    }
    expected = [
        f"tests/test_{name}.py::test_{case}"
        for name in names
        for case in ("first", "second[original@science-test_volume_phase_estimation]")
    ]
    catalogs = []
    for workers in (False, True):
        root = suite(tmp_path / str(workers), files)
        result = run(root, workers=workers)
        assert result.returncode == 0, result.stdout + result.stderr
        records = observations(root)
        collections = [row for row in records if row["kind"] == "collection"]
        assert len(collections) == (2 if workers else 1)
        for row in collections:
            normalized = [node.rsplit("@", 1)[0] if workers else node for node in row["nodes"]]
            assert normalized == expected
            groups = [
                [f"science-test_{name}" if name in SCIENCE else "serial-rest"]
                for name in names
                for _ in range(2)
            ]
            assert row["groups"] == (groups if workers else [[] for _ in expected])
        worker_pids = {row["pid"] for row in collections}
        assert len(worker_pids) == (2 if workers else 1)
        assert {row["worker"] for row in collections} == ({"gw0", "gw1"} if workers else {None})
        calls = [
            row["node"]
            for row in records
            if row["kind"] == "report" and row["when"] == "call" and row["pid"] in worker_pids
        ]
        normalized_calls = [node.rsplit("@", 1)[0] if workers else node for node in calls]
        catalogs.append(Counter(normalized_calls))
        for name in names:
            prefix = f"tests/test_{name}.py::"
            assert [node for node in normalized_calls if node.startswith(prefix)] == [
                node for node in expected if node.startswith(prefix)
            ]
    assert catalogs == [Counter(expected), Counter(expected)]


@pytest.mark.parametrize(
    ("source", "diagnostic"),
    [
        ('import pytest\ndef test_omitted():\n    pytest.skip("planned skip")\n', "1 skipped"),
        (
            "import pytest\n@pytest.mark.xfail(strict=False)\ndef test_omitted():\n    pass\n",
            "1 xpassed",
        ),
    ],
    ids=("runtime-skip", "non-strict-xpass"),
)
def test_distributed_omissions_fail_without_internal_error(
    tmp_path: Path, source: str, diagnostic: str
) -> None:
    root = suite(tmp_path / "suite", {"tests/test_case.py": source})
    result = run(root)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert diagnostic in output
    assert "INTERNALERROR" not in output
    finishes = [row for row in observations(root) if row["kind"] == "finish"]
    assert len(finishes) == 3
    controller = next(row for row in finishes if row["worker"] is None)
    assert controller["reporter"] and controller["status"] != 0
