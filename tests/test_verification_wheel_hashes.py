"""Blind public-CLI proof of secure per-member wheel RECORD evidence."""

import base64
import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from pathlib import Path

import pytest

from test_verification_receipt import TOOLS, git, invoke
from test_verification_receipt import repository as repository
from verification_fixture_dispatch import install_dispatch, read_calls
from verification_fixture_tools import PHASES

SECURE_EXAMPLES = (
    "sha256",
    "sha384",
    "sha512",
    "sha3_256",
    "sha3_384",
    "sha3_512",
    "blake2b",
    "blake2s",
)
INFO = "simrecon-1.2.0.dist-info"
RECORD = f"{INFO}/RECORD"
WHEEL_NAME = "simrecon-1.2.0-py3-none-any.whl"
MEMBERS = {
    f"{INFO}/METADATA": b"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.0\n",
    f"{INFO}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    "simrecon/__init__.py": b"__version__ = '1.2.0'\n",
    **{
        f"simrecon/payload{index}.dat": bytes([index, 0, 255]) + b"wheel payload\n"
        for index in range(5)
    },
}
TARGET = "simrecon/payload4.dat"
UNAVAILABLE = "simrecon_wh_no_such_hash"

# These executables supply external command behavior, never verifier decisions.
# The frozen helper supplies the native-report fixtures and authentic argv trace.
COMMAND = """
import os
import shutil
import sys
from pathlib import Path

from verification_fixture_tools import PHASES, main

status = main()
phase = next((arg for arg in sys.argv[1:] if arg in PHASES), None)
if phase == "wheel" and status == 0:
    root = Path.cwd()
    shutil.copyfile(
        root / "artifacts/wheel-source.whl", root / "dist/simrecon-1.2.0-py3-none-any.whl"
    )
    print("controlled hash wheel emitted in this phase")
    if os.environ.get("HASH_WHEEL_FAILURE") == "1":
        print("controlled hash wheel phase failure", file=sys.stderr)
        status = 37
sys.exit(status)
"""


@pytest.fixture
def hash_repository(repository):
    """Extend the frozen real-CLI fixture only through external executables."""
    root, bin_dir = repository
    for name in ("make", "uv"):
        executable = bin_dir / name
        install_dispatch(
            executable,
            f"import sys\nsys.path.insert(0, {str(TOOLS.parent)!r})\n" + COMMAND,
            profile="hash",
        )
    return root, bin_dir


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_source(root: Path, algorithms: tuple[str, ...], defect: str | None = None) -> Path:
    """Construct independently known bytes, with at most one isolated defect."""
    assert len(algorithms) == len(MEMBERS)
    records = io.StringIO(newline="")
    writer = csv.writer(records, lineterminator="\n")
    for (name, data), algorithm in zip(MEMBERS.items(), algorithms, strict=True):
        # An unavailable algorithm has no defined digest; retain an otherwise
        # well-formed SHA-256-sized value while changing only its declared name.
        value = hashlib.new("sha256" if algorithm == UNAVAILABLE else algorithm, data).digest()
        if name == TARGET and defect == "digest":
            value = bytes([value[0] ^ 1]) + value[1:]
        encoded = base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
        size = len(data) + (1 if name == TARGET and defect == "size" else 0)
        writer.writerow((name, f"{algorithm}={encoded}", size))
    writer.writerow((RECORD, "", ""))
    source = root / "artifacts/wheel-source.whl"
    source.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in MEMBERS.items():
            archive.writestr(name, data)
        archive.writestr(RECORD, records.getvalue().encode("ascii"))
    return source


def assert_fixture(source: Path, algorithms: tuple[str, ...], defect: str | None = None) -> None:
    """Check known member truth before relying on any production outcome."""
    with zipfile.ZipFile(source) as archive:
        assert set(archive.namelist()) == {*MEMBERS, RECORD}
        assert len(archive.namelist()) == len(MEMBERS) + 1
        rows = list(csv.reader(io.StringIO(archive.read(RECORD).decode("ascii"))))
        assert rows[-1] == [RECORD, "", ""]
        assert len(rows) == len(MEMBERS) + 1
        for row, (name, data), algorithm in zip(
            rows[:-1], MEMBERS.items(), algorithms, strict=True
        ):
            assert archive.read(name) == data
            assert row[0] == name
            declared, encoded = row[1].split("=", 1)
            assert declared == algorithm
            assert "=" not in encoded
            raw = base64.b64decode(
                encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True
            )
            if algorithm == UNAVAILABLE:
                with pytest.raises(ValueError):
                    hashlib.new(algorithm)
                expected = hashlib.sha256(data).digest()
            else:
                # Direct documented constructors provide truth independently
                # of both the fixture's generic constructor and product output.
                expected = getattr(hashlib, algorithm)(data).digest()
            if name == TARGET and defect == "digest":
                assert len(raw) == len(expected)
                assert raw != expected
                assert raw[0] == expected[0] ^ 1
                assert raw[1:] == expected[1:]
            else:
                assert raw == expected
            assert row[2] == str(len(data) + (1 if name == TARGET and defect == "size" else 0))
            if algorithm in SECURE_EXAMPLES:
                assert len(expected) * 8 >= 256


def run_hash_cli(hash_repository, algorithms, defect=None, *, wheel_failure=False):
    root, bin_dir = hash_repository
    source = write_source(root, algorithms, defect)
    assert_fixture(source, algorithms, defect)
    input_files = {
        "wheel-fixture": source,
        "make-fixture": bin_dir / "make",
        "uv-fixture": bin_dir / "uv",
        "command-fixture": bin_dir / "make-dynamic.py",
        "receipt-fixture": TOOLS,
        "dispatch-fixture": TOOLS.with_name("verification_fixture_dispatch.py"),
    }
    expected_inputs = {
        alias: {
            "before": {"size_bytes": path.stat().st_size, "sha256": sha256(path)},
            "after": {"size_bytes": path.stat().st_size, "sha256": sha256(path)},
        }
        for alias, path in input_files.items()
    }
    expected_identity = {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "manifest": {name: sha256(root / name) for name in git(root, "ls-files").splitlines()},
    }
    # A stale valid wheel differs from this invocation's staged wheel. The
    # real coverage-clean command must clear it; the wheel phase emits source.
    if wheel_failure:
        stale = root / "dist" / WHEEL_NAME
        stale.parent.mkdir()
        shutil.copyfile(source, stale)
        with zipfile.ZipFile(stale, "a") as archive:
            archive.comment = b"stale prior invocation"
        assert sha256(stale) != sha256(source)
    extra = tuple(
        arg for alias, path in input_files.items() for arg in ("--input", f"{alias}={path}")
    )
    # invoke uses the running explicit interpreter and inherited source-free
    # child environment, as in the frozen public test checkpoint.
    previous = os.environ.get("HASH_WHEEL_FAILURE")
    try:
        os.environ["HASH_WHEEL_FAILURE"] = "1" if wheel_failure else "0"
        result, receipt = invoke(hash_repository, extra=extra)
    finally:
        if previous is None:
            os.environ.pop("HASH_WHEEL_FAILURE", None)
        else:
            os.environ["HASH_WHEEL_FAILURE"] = previous
    assert receipt is not None
    expected_phases = PHASES[: PHASES.index("wheel") + 1] if wheel_failure else PHASES
    assert [phase["name"] for phase in receipt["phases"]] == expected_phases
    calls = read_calls(root / "calls.jsonl")
    actual_calls = [call for call in calls if any(arg in PHASES for arg in call)]
    assert [[arg for arg in call if arg in PHASES] for call in actual_calls] == [
        [phase] for phase in expected_phases
    ]
    for phase, call in zip(receipt["phases"], actual_calls, strict=True):
        # Match the authentic full argv, allowing legitimate Make options.
        assert phase["command"] == [str(bin_dir / "make"), *call]
        assert call.count(f"UV={bin_dir / 'uv'}") == 1
        assert phase["returncode"] == (37 if wheel_failure and phase["name"] == "wheel" else 0)
        assert f"controlled phase {phase['name']}" in (root / phase["log"]).read_text()
    for state in (receipt["before"], receipt["after"]):
        assert state["dirty"] is False
        assert state["untracked"] == []
        for key, expected in expected_identity.items():
            assert state[key] == expected
    assert receipt["inputs"] == expected_inputs
    assert git(root, "status", "--porcelain", "--untracked-files=no") == ""
    wheel = root / "dist" / WHEEL_NAME
    assert wheel.read_bytes() == source.read_bytes()
    assert_fixture(wheel, algorithms, defect)
    # Synthetic native counts are frozen command-fixture evidence, not actual
    # runtime instrumentation or a full-gate measurement claim.
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    return result, receipt, wheel


def assert_artifact(receipt, wheel: Path) -> None:
    """Outer identity always hashes the complete ZIP with SHA-256."""
    assert receipt["artifact"] == {
        "path": f"dist/{WHEEL_NAME}",
        "size_bytes": wheel.stat().st_size,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "version": "1.2.0",
    }


def test_mixed_secure_record_algorithms_complete_public_cli(hash_repository):
    result, receipt, wheel = run_hash_cli(hash_repository, SECURE_EXAMPLES)
    assert result.returncode == 0, json.dumps(receipt["problems"])
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    assert_artifact(receipt, wheel)


@pytest.mark.parametrize("algorithm", ("md5", "sha224", UNAVAILABLE))
def test_one_weak_or_unavailable_record_algorithm_cannot_pass(hash_repository, algorithm):
    algorithms = ("sha256",) * (len(MEMBERS) - 1) + (algorithm,)
    result, receipt, _ = run_hash_cli(hash_repository, algorithms)
    assert result.returncode == 1
    assert receipt["result"] == "failed"
    assert receipt["problems"]
    assert receipt["artifact"] is None


@pytest.mark.parametrize("algorithms", (SECURE_EXAMPLES,), ids=("mixed",))
def test_valid_current_wheel_retained_after_wheel_phase_failure(hash_repository, algorithms):
    result, receipt, wheel = run_hash_cli(hash_repository, algorithms, wheel_failure=True)
    assert result.returncode == 37
    assert receipt["result"] == "failed"
    assert receipt["problems"]
    assert "controlled hash wheel phase failure" in result.stdout + result.stderr
    assert_artifact(receipt, wheel)


@pytest.mark.parametrize("defect", ("digest", "size"))
def test_one_later_mixed_secure_record_member_cannot_pass(hash_repository, defect):
    target_index = tuple(MEMBERS).index(TARGET)
    assert target_index > 0
    assert SECURE_EXAMPLES[target_index] != SECURE_EXAMPLES[0]
    result, receipt, _ = run_hash_cli(hash_repository, SECURE_EXAMPLES, defect)
    assert result.returncode == 1
    assert receipt["result"] == "failed"
    assert receipt["problems"]
    assert receipt["artifact"] is None
