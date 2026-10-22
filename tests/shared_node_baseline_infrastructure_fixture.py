"""Owned disposable CLI fixtures; no production source is inspected.

Native reports and built wheel below describe this tiny fixture only. They do
not establish production coverage, scientific results, or canonical verification.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
HARNESS = ROOT / "scripts/source_free_check.py"
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
PINNED = {
    "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9": 70_000_000,
    "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20": 10_000_000,
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: float = 58,
) -> subprocess.CompletedProcess[str]:
    """Keep child diagnostics inherited and bound time/output sent to assertions."""
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    assert len(result.stdout) + len(result.stderr) < 100_000, "unbounded fixture output"
    return result


def python(
    args: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return run(
        [str(PYTHON), str(HARNESS), "--timeout", "50", "python", *args],
        cwd=cwd,
        env=env,
    )


def probe(tmp_path: Path, code: str) -> Path:
    path = tmp_path / "owned_probe.py"
    path.write_text(textwrap.dedent(code), encoding="utf-8")
    return path


def authenticated_jars() -> dict[str, Path]:
    found = {digest(path): path for path in (ROOT / "artifacts/imagej-reader").glob("*.jar")}
    assert PINNED.keys() <= found.keys(), "incomplete real pinned-cache capability"
    for identity, maximum in PINNED.items():
        assert found[identity].stat().st_size <= maximum
    return {identity: found[identity] for identity in PINNED}


def reader_layout(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    # Opaque copies are execution inputs, never an expectation source.
    shutil.copyfile(ROOT / "scripts/prepare_imagej_reader.py", scripts / "prepare_imagej_reader.py")
    cache = tmp_path / "artifacts/imagej-reader"
    cache.mkdir(parents=True)
    jars = {}
    for identity, original in authenticated_jars().items():
        target = cache / original.name
        shutil.copyfile(original, target)
        assert digest(target) == identity
        jars[identity] = target
    return cache, jars


def java_environment(*, path_selection: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    selected = env.get("SIMRECON_JAVA")
    assert selected and Path(selected).is_file(), "incomplete real Java capability"
    if path_selection:
        env.pop("SIMRECON_JAVA")
        env["PATH"] = str(Path(selected).parent) + os.pathsep + env.get("PATH", "")
    return env


# This is an owned command program, not a private verifier worker interface.
# Every evidence file is emitted by this invocation's real commands.
FIXTURE_COMMANDS = """\
import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import zipfile

phase = sys.argv[1]
root = Path.cwd()
control = json.loads((root / "control.json").read_text())
print("FIXTURE_PHASE " + phase, flush=True)
with (root / "trace.txt").open("a") as trace:
    trace.write(phase + "\\n")
out = root / "artifacts/verification"
out.mkdir(parents=True, exist_ok=True)

def command(*args):
    subprocess.run([sys.executable, *args], check=True, timeout=20)

if phase == "coverage-clean":
    command("-m", "coverage", "erase")
elif phase == "tests":
    baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    command("-m", "coverage", "run", "--branch", "fixture_tests.py")
    # Actual fixture command process readings; M25-shaped collector input ONLY.
    # This supplies no product M25 or scientific memory evidence.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.environ.get("SIMRECON_MEASUREMENTS_PATH"):
        units = "bytes" if sys.platform == "darwin" else "KiB"
        report = {
            "schema": "org.simrecon.measurements", "version": 1,
            "run_id": os.environ["SIMRECON_MEASUREMENTS_RUN_ID"],
            "measurements": {"M25": {
                "baseline": baseline, "peak": peak, "units": units,
                "increment_bytes": (peak - baseline) * (1 if units == "bytes" else 1024),
                "limit_bytes": 33554432,
            }},
        }
        Path(os.environ["SIMRECON_MEASUREMENTS_PATH"]).write_text(json.dumps(report))
elif phase == "coverage-json":
    command("-m", "coverage", "json", "-o", "artifacts/coverage/coverage.json")
    if control.get("bad_report") == "truncated":
        Path("artifacts/coverage/coverage.json").write_text("{")
    elif control.get("bad_report") == "absent":
        Path("artifacts/coverage/coverage.json").unlink()
elif phase == "coverage-html":
    command("-m", "coverage", "html", "-d", "artifacts/coverage/html")
    if control.get("bad_report") == "missing_html":
        Path("artifacts/coverage/html/index.html").unlink()
elif phase == "coverage-report":
    command("-m", "coverage", "report")
elif phase == "wheel":
    # Build a real fixture-only wheel container from the fixture source bytes.
    # RECORD hashes are defined by the public wheel schema, not verifier output.
    info = "simrecon-0.1.0.dist-info/"
    members = {
        "simrecon/__init__.py": Path("src/simrecon/__init__.py").read_bytes(),
        info + "METADATA": b"Metadata-Version: 2.1\\nName: simrecon\\nVersion: 0.1.0\\n\\n",
        info + "WHEEL": (
            b"Wheel-Version: 1.0\\nGenerator: owned-fixture\\n"
            b"Root-Is-Purelib: true\\nTag: py3-none-any\\n\\n"
        ),
    }
    rows = []
    for name, data in members.items():
        value = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        rows.append([name, "sha256=" + value, str(len(data))])
    rows.append([info + "RECORD", "", ""])
    record = io.StringIO()
    csv.writer(record, lineterminator="\\n").writerows(rows)
    members[info + "RECORD"] = record.getvalue().encode()
    Path("dist").mkdir(exist_ok=True)
    with zipfile.ZipFile("dist/simrecon-0.1.0-py3-none-any.whl", "w") as wheel:
        for name, data in members.items():
            wheel.writestr(name, data)
elif phase == "wheel-import":
    command("-c", "import sys; "
            "sys.path.insert(0, 'dist/simrecon-0.1.0-py3-none-any.whl'); "
            "import simrecon; assert simrecon.choose(True) == 1")

if phase == "audit" and control.get("receipt_alias"):
    # Bind to the file actually emitted earlier in THIS invocation.
    kind = control["receipt_alias"]
    if kind == "json":
        target = Path("artifacts/coverage/coverage.json")
    elif kind == "database":
        target = Path(".coverage")
    elif kind == "html":
        candidates = list(Path("artifacts/coverage/html").glob("*.html"))
        target = next(p for p in candidates if p.name != "index.html")
    elif kind == "wheel":
        target = next(Path("dist").glob("*.whl"))
    elif kind == "measurements":
        target = Path(os.environ["SIMRECON_MEASUREMENTS_PATH"])
    elif kind == "log":
        # Public receipt phase logs are observable emitted files; no private name.
        candidates = list(out.rglob("*.log"))
        target = next(p for p in candidates if "FIXTURE_PHASE sync" in p.read_text())
    else:
        raise ValueError("unknown owned fixture target")
    assert target.is_file()
    observed = {"path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    Path("challenged.json").write_text(json.dumps(observed))
    destination = Path(control["receipt"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.symlink_to(target.resolve())
"""


def verifier_layout(tmp_path: Path, control: dict[str, str]) -> Path:
    repo = tmp_path / "fixture_repo"
    (repo / "src/simrecon").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "src/simrecon/__init__.py").write_text(
        "def choose(value):\n    if value:\n        return 1\n    return 0\n"
    )
    (repo / "scripts/owned.py").write_text("VALUE = 17\n")
    (repo / "fixture_tests.py").write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path[:0] = [str(Path('src').resolve()), str(Path('scripts').resolve())]\n"
        "import simrecon\nimport owned\n"
        "assert simrecon.choose(True) == 1\nassert simrecon.choose(False) == 0\n"
        "assert owned.VALUE == 17\n"
    )
    (repo / ".coveragerc").write_text("[run]\nbranch = True\nsource = src/simrecon, scripts\n")
    (repo / ".gitignore").write_text(
        "artifacts/\ndist/\n.coverage*\n!/.coveragerc\n"
        "trace.txt\ncontrol.json\nchallenged.json\n__pycache__/\nsafe/\n"
    )
    (repo / "marker.txt").write_bytes(b"OWNED_TRACKED_MARKER\n")
    (repo / "fixture_commands.py").write_text(FIXTURE_COMMANDS)
    # Real Make runs every named fixture command; no successful phase is faked.
    makefile = [".PHONY: " + " ".join(PHASES)]
    for phase in PHASES:
        makefile.extend([phase + ":", f'\t@"{sys.executable}" fixture_commands.py {phase}'])
    (repo / "Makefile").write_text("\n".join(makefile) + "\n")
    for arguments in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "user.name=Owned Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "owned fixture",
        ],
    ):
        result = run(["git", *arguments], cwd=repo)
        assert result.returncode == 0, "disposable repository creation failed"
    (repo / "control.json").write_text(json.dumps(control))
    return repo


def verify(
    repo: Path, receipt: Path, *, measurements_required: bool = False
) -> subprocess.CompletedProcess[str]:
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv")
    assert Path(uv).is_file(), "incomplete selected real uv capability"
    make = shutil.which("make")
    assert make, "incomplete real Make capability"
    return python(
        [
            str(ROOT / "scripts/verify.py"),
            "--make",
            make,
            "--uv",
            uv,
            "--receipt",
            str(receipt),
            "--contract",
            "BASELINE-INFRASTRUCTURE-01-FIXTURE-ONLY",
            *(["--measurements-required"] if measurements_required else []),
        ],
        cwd=repo,
    )
