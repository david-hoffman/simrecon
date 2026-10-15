"""Disposable public CLI fixtures; no production module is imported here."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import sysconfig
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PHASES = (
    "sync",
    "coverage-clean",
    "lint",
    "format",
    "types",
    "tests",
    "coverage-combine",
    "coverage-json",
    "coverage-html",
    "coverage-report",
    "wheel",
    "wheel-import",
    "audit",
)

# This is an explicitly synthetic phase driver. Coverage execution, storage and
# reporting are real; lint/type/audit/build/install guarantees are not exercised.
DRIVER = r"""
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import coverage

root = Path.cwd()
observations = Path(os.environ["A13_OBSERVATIONS"])
nonce = os.environ["A13_NONCE"]
if "--version" in sys.argv:
    print("A13 disposable phase driver 1")
    raise SystemExit(0)
phase = next(arg for arg in sys.argv[1:] if not arg.startswith("-"))
with (observations / "trace.jsonl").open("a") as trace:
    trace.write(json.dumps({"nonce": nonce, "phase": phase, "argv": sys.argv[1:]}) + "\n")
output = f"{nonce}:{phase}\n"
output_stream = sys.stderr if os.environ["A15_OUTPUT_STREAM"] == "stderr" else sys.stdout

def command(*args):
    global output
    result = subprocess.run([sys.executable, "-m", "coverage", *args],
                            capture_output=True, text=True, timeout=30)
    output += result.stdout + result.stderr
    if result.returncode:
        (observations / (phase + ".txt")).write_text(output)
        print(output, end="", file=output_stream)
        raise SystemExit(result.returncode)

def lose_configuration():
    configuration = Path(os.environ["COVERAGE_RCFILE"])
    (observations / "configuration-before.ini").write_bytes(configuration.read_bytes())
    loss = os.environ["A14_CONFIG_LOSS"]
    if loss == "missing":
        configuration.unlink()
    else:
        configuration.write_text("[run\nbranch = True\n")
    (observations / "configuration-loss.json").write_text(json.dumps({
        "nonce": nonce, "phase": phase, "loss": loss,
        "exists_after": configuration.exists(),
    }))

if (phase == os.environ.get("A14_CONFIG_LOSS_PHASE")
        and os.environ["A16_CONFIG_LOSS_TIMING"] == "before"):
    lose_configuration()

if phase == "coverage-clean":
    command("erase")
elif phase == "tests":
    command("run", "--context=" + nonce, "scripts/probe.py")
    selected = coverage.Coverage()
    selected.load()
    data = selected.get_data()
    database = Path(data.data_filename()).resolve()
    assert database == Path(os.environ["A13_DATABASE"])
    assert sorted(data.measured_contexts()) == [nonce]
    (observations / "native-measured.bin").write_bytes(database.read_bytes())
    (observations / "native-measured.json").write_text(json.dumps({
        "nonce": nonce, "database": str(database),
        "contexts": sorted(data.measured_contexts()),
        "files": sorted(data.measured_files()),
    }))
elif phase == "coverage-combine":
    # One real measurement process, so there are no parallel shards to combine.
    pass
elif phase == "coverage-json":
    command("json", "-o", "artifacts/coverage/coverage.json")
elif phase == "coverage-html":
    command("html", "-d", "artifacts/coverage/html")
elif phase == "coverage-report":
    command("report")
elif phase == "wheel":
    dist = root / "dist"
    dist.mkdir()
    metadata = "simrecon-0.0.0.dist-info/"
    members = {
        "simrecon/__init__.py": b"VALUE = 7\n",
        metadata + "METADATA": b"Metadata-Version: 2.1\nName: simrecon\nVersion: 0.0.0\n",
        metadata + "WHEEL": (b"Wheel-Version: 1.0\nGenerator: A13-fixture\n"
                             b"Root-Is-Purelib: true\nTag: py3-none-any\n"),
    }
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for name, content in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        writer.writerow([name, "sha256=" + digest, len(content)])
    writer.writerow([metadata + "RECORD", "", ""])
    members[metadata + "RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(dist / "simrecon-0.0.0-py3-none-any.whl", "w") as wheel:
        for name, content in members.items():
            wheel.writestr(name, content)
elif phase == "audit":
    selected = coverage.Coverage()
    selected.load()
    data = selected.get_data()
    database = Path(data.data_filename()).resolve()
    records = {
        name: {"lines": sorted(data.lines(name) or []),
               "arcs": sorted([list(arc) for arc in data.arcs(name) or []])}
        for name in sorted(data.measured_files())
    }
    # Snapshot at the last phase, before verifier-owned final persistence.
    (observations / "native-before.bin").write_bytes(database.read_bytes())
    reports = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "artifacts/coverage").rglob("*")) if path.is_file()
    }
    wheels = {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "dist").glob("*.whl"))
    }
    snapshot = {"nonce": nonce, "database": str(database),
                "records": records, "contexts": sorted(data.measured_contexts()),
                "reports": reports, "wheels": wheels}
    (observations / "snapshot.json").write_text(json.dumps(snapshot))

if (phase == os.environ.get("A14_CONFIG_LOSS_PHASE")
        and os.environ["A16_CONFIG_LOSS_TIMING"] == "after"):
    lose_configuration()

(observations / (phase + ".txt")).write_text(output)
print(output, end="", file=output_stream)
"""


def prepare(
    root: Path,
    selector: str,
    destination: str,
    *,
    local_python: bool = False,
    configuration_loss: str | None = None,
    loss_phase: str = "audit",
    loss_timing: str = "after",
    output_stream: str = "stdout",
) -> dict:
    """Create only owned disposable inputs and a clean independent Git repo."""
    assert loss_timing in ("before", "after")
    repo = root / "repository"
    external = root / "external"
    observations = root / "observations"
    for directory in (repo / "src/simrecon", repo / "scripts", external, observations):
        directory.mkdir(parents=True)
    nonce = uuid.uuid4().hex
    database = external / ("native-" + nonce + ".db")
    receipt = database if destination == "collision" else external / "receipt.json"
    if destination in ("native-neighbor", "native-stale"):
        receipt = external / ("native-" + uuid.uuid4().hex + ".db")
    if destination in ("stale", "native-stale"):
        # A real, unrelated native container is a permitted replaceable output.
        from coverage import CoverageData

        stale = CoverageData(basename=str(receipt))
        stale.add_lines({"unrelated_stale.py": [17]})
        stale.set_context("unrelated-stale-run")
        stale.write()
        (observations / "stale-before.bin").write_bytes(receipt.read_bytes())
    (repo / "src/simrecon/__init__.py").write_text("VALUE = 7\n")
    (repo / "scripts/probe.py").write_text(
        "from simrecon import VALUE\n"
        "for flag in (False, True):\n"
        "    if flag:\n"
        "        assert VALUE == 7\n"
        "    else:\n"
        "        assert VALUE != 8\n"
    )
    (repo / ".gitignore").write_text(
        "artifacts/\ndist/\n__pycache__/\n" + (".venv/\n" if local_python else "")
    )
    if local_python:
        # A genuine disposable venv uses the installed locked dependencies via
        # Python's supported .pth mechanism; no install/network or shim module.
        local_venv = repo / ".venv"
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(local_venv)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        site = local_venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
        (site / "site-packages" / "locked-dependencies.pth").write_text(
            sysconfig.get_path("purelib") + "\n"
        )
        health = subprocess.run(
            [str(local_venv / "bin/python"), "-m", "coverage", "--version"],
            check=True,
            capture_output=True,
            timeout=20,
        )
        (observations / "local-python-health.txt").write_bytes(health.stdout + health.stderr)
    project = '[project]\nname = "simrecon"\nversion = "0.0.0"\n'
    configuration = (
        "[run]\nbranch = True\nrelative_files = True\n"
        "source = src/simrecon,scripts\ndata_file = " + str(database) + "\n"
        "[report]\nfail_under = 0\n"
    )
    env = os.environ.copy()
    env.pop("COVERAGE_FILE", None)
    env.pop("COVERAGE_RCFILE", None)
    env.pop("COVERAGE_PROCESS_START", None)
    env.pop("A14_CONFIG_LOSS", None)
    env.pop("A14_CONFIG_LOSS_PHASE", None)
    if selector == "pyproject":
        project += (
            "[tool.coverage.run]\nbranch = true\nrelative_files = true\n"
            'source = ["src/simrecon", "scripts"]\ndata_file = '
            + json.dumps(str(database))
            + "\n[tool.coverage.report]\nfail_under = 0\n"
        )
    elif selector == "rcfile":
        config = (external if configuration_loss else repo) / "selected-coverage.ini"
        config.write_text(configuration)
        env["COVERAGE_RCFILE"] = str(config)
    else:
        (repo / ".coveragerc").write_text(configuration)
    (repo / "pyproject.toml").write_text(project)
    if configuration_loss:
        assert selector == "rcfile"
        assert configuration_loss in ("missing", "invalid")
        env["A14_CONFIG_LOSS"] = configuration_loss
        env["A14_CONFIG_LOSS_PHASE"] = loss_phase
    driver = root / "phase-driver"
    driver.write_text("#!" + sys.executable + "\n" + DRIVER)
    driver.chmod(0o755)
    env.update(
        PYTHONDONTWRITEBYTECODE="1",
        A16_CONFIG_LOSS_TIMING=loss_timing,
        A15_OUTPUT_STREAM=output_stream,
        A13_NONCE=nonce,
        A13_OBSERVATIONS=str(observations),
        A13_DATABASE=str(database),
        PYTHONPATH=str(repo / "src") + os.pathsep + env.get("PYTHONPATH", ""),
    )
    for argv in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        [
            "git",
            "-c",
            "user.name=A13 fixture",
            "-c",
            "user.email=a13@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "disposable public fixture",
        ],
    ):
        subprocess.run(argv, cwd=repo, env=env, check=True, capture_output=True, timeout=20)
    declared = {
        "selector": selector,
        "destination": destination,
        "local_python": local_python,
        "configuration_loss": configuration_loss,
        "output_stream": output_stream,
        "loss_phase": loss_phase if configuration_loss else None,
        "loss_timing": loss_timing if configuration_loss else None,
        "nonce": nonce,
        "repository": str(repo),
        "database": str(database),
        "receipt": str(receipt),
        "driver_sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
        "input_sha256": {
            str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in repo.rglob("*")
            if path.is_file() and not {".git", ".venv"}.intersection(path.relative_to(repo).parts)
        },
        "coverage_environment": {
            name: env.get(name)
            for name in ("COVERAGE_FILE", "COVERAGE_RCFILE", "COVERAGE_PROCESS_START")
        },
    }
    (observations / "declared-case.json").write_text(json.dumps(declared, indent=2))
    return dict(
        repo=repo,
        database=database,
        receipt=receipt,
        observations=observations,
        nonce=nonce,
        driver=driver,
        env=env,
    )


def invoke(case: dict) -> subprocess.CompletedProcess[str]:
    """Execute the genuine helper, with the opaque diagnostic wrapper inherited."""
    result = subprocess.run(
        [
            sys.executable,
            str(BASE / "scripts/source_free_check.py"),
            "--timeout",
            "90",
            "python",
            str(BASE / "scripts/verify.py"),
            "--make",
            str(case["driver"]),
            "--uv",
            str(case["driver"]),
            "--receipt",
            str(case["receipt"]),
        ],
        cwd=case["repo"],
        env=case["env"],
        capture_output=True,
        text=True,
        timeout=100,
    )
    for stream in ("stdout", "stderr"):
        (case["observations"] / (stream + ".txt")).write_text(getattr(result, stream))
    (case["observations"] / "status.json").write_text(json.dumps({"returncode": result.returncode}))
    return result
