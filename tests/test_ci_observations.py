"""Exercise verifier import and native complementary CI report propagation."""

import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_verifier_import_does_not_execute_cli(tmp_path):
    # --help makes an accidental CLI invocation harmless, but prevents the marker.
    program = """
import importlib.util
import sys
sys.argv = [sys.argv[1], "--help"]
spec = importlib.util.spec_from_file_location("ci_verifier", sys.argv[0])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("verifier import returned")
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(ROOT / "scripts/verify.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "verifier import returned\n"
    assert result.stderr == ""


def test_native_complementary_reports_preserve_semantic_identity(tmp_path):
    for package, expected in (
        ("pytest", "9.1.1"),
        ("pytest-split", "0.11.0"),
        ("pytest-xdist", "3.8.0"),
        ("pytest-reportlog", "1.0.0"),
    ):
        assert version(package) == expected

    shipped_hook = ROOT / "tests/conftest.py"
    copied_hook = tmp_path / "conftest.py"
    copied_hook.write_bytes(shipped_hook.read_bytes())
    assert copied_hook.read_bytes() == shipped_hook.read_bytes()
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\n"
        "addopts = --strict-config --strict-markers -p simrecon._pytest_policy\n"
        "disable_test_id_escaping_and_forfeit_all_rights_to_community_support = true\n",
        encoding="utf-8",
    )
    (tmp_path / "ci_observer.py").write_text(
        "import json\nfrom pathlib import Path\nimport pytest\n\n"
        "@pytest.hookimpl(tryfirst=True)\n"
        "def pytest_itemcollected(item):\n"
        '    item.user_properties.append(("owner.note", "untouched@λ"))\n\n'
        "def pytest_collection_finish(session):\n"
        '    if session.config.getoption("collectonly"):\n'
        '        Path("reference-nodeids.json").write_text(\n'
        '            json.dumps([item.nodeid for item in session.items]), encoding="utf-8")\n',
        encoding="utf-8",
    )
    (tmp_path / "test_imagej_export.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.parametrize("value", ["plain", "literal@id", "punctuation![]", "λ"])\n'
        "def test_value(value):\n"
        '    assert value in ("plain", "literal@id", "punctuation![]", "λ")\n',
        encoding="utf-8",
    )
    (tmp_path / "test_native.py").write_text(
        "import pytest\n\n"
        '@pytest.mark.parametrize("value", [0, 1, 2, 3])\n'
        "def test_value(value):\n"
        "    assert 0 <= value <= 3\n",
        encoding="utf-8",
    )
    timing = tmp_path / "timing.json"
    timing.write_bytes(b"{}\n")
    environment = os.environ.copy()
    for name in ("SIMRECON_MEASUREMENTS_PATH", "SIMRECON_MEASUREMENTS_RUN_ID"):
        environment.pop(name, None)
    commands = []

    def invoke(name, arguments):
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pytest.ini",
            "-p",
            "ci_observer",
            f"--report-log={name}.jsonl",
            *arguments,
        ]
        commands.append(command)
        (tmp_path / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        result = subprocess.run(
            command,
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        (tmp_path / f"{name}.stdout").write_text(result.stdout, encoding="utf-8")
        (tmp_path / f"{name}.stderr").write_text(result.stderr, encoding="utf-8")
        assert result.returncode == 0, result.stdout + result.stderr

    invoke("reference", ["--collect-only", "-n", "0"])
    grouped = {
        f"test_imagej_export.py::test_value[{value}]"
        for value in ("plain", "literal@id", "punctuation![]", "λ")
    }
    expected = grouped | {f"test_native.py::test_value[{value}]" for value in range(4)}
    reference = json.loads((tmp_path / "reference-nodeids.json").read_text(encoding="utf-8"))
    assert len(reference) == len(expected)
    assert set(reference) == expected
    selections = []
    for group in (1, 2):
        invoke(
            f"group-{group}",
            [
                "--splits=2",
                f"--group={group}",
                "--splitting-algorithm=least_duration",
                f"--durations-path={timing}",
                "-n",
                "4",
                "--dist=loadgroup",
                "--max-worker-restart=0",
            ],
        )
        reports = [
            json.loads(line)
            for line in (tmp_path / f"group-{group}.jsonl").read_text().splitlines()
        ]
        assert reports[-1] == {"exitstatus": 0, "$report_type": "SessionFinish"}
        phases = {}
        workers = {}
        for report in reports:
            if report["$report_type"] != "TestReport":
                continue
            properties = report["user_properties"]
            identities = [value for key, value in properties if key == "simrecon.semantic_nodeid"]
            assert len(identities) == 1
            semantic = identities[0]
            assert semantic in expected
            assert [key for key, _ in properties].count("owner.note") == 1
            assert ["owner.note", "untouched@λ"] in properties
            transport = semantic + "@imagej_reader_cache" if semantic in grouped else semantic
            assert report["nodeid"] == transport
            assert report["worker_id"] in {"gw0", "gw1", "gw2", "gw3"}
            assert report["outcome"] == "passed"
            phases.setdefault(semantic, []).append(report["when"])
            workers.setdefault(semantic, set()).add(report["worker_id"])
        assert phases
        assert all(value == ["setup", "call", "teardown"] for value in phases.values())
        assert all(len(value) == 1 for value in workers.values())
        assert len({next(iter(workers[item])) for item in grouped & phases.keys()}) == 1
        selections.append(set(phases))
    assert selections[0].isdisjoint(selections[1])
    assert selections[0] | selections[1] == set(reference)
    assert timing.read_bytes() == b"{}\n"
    assert copied_hook.read_bytes() == shipped_hook.read_bytes()
