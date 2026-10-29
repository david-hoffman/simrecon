"""Owned public-command fixtures; never inspect runtime implementation bytes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/source_free_check.py"
PYTHON = Path(sys.executable)
JAVA = os.environ.get("SIMRECON_JAVA", "java")
EVIDENCE = Path(
    os.environ.get(
        "SIMRECON_PROTOCOLS_EVIDENCE",
        str(ROOT / "artifacts/infrastructure-supplement-A07/evidence"),
    )
)
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
PINS = {
    "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9": 70_000_000,
    "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20": 10_000_000,
}


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run_public(
    cwd: Path, *args: str, timeout: float = 60, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """All product invocations retain the inherited source-free diagnostic aid."""
    result = subprocess.run(
        [str(PYTHON), str(HARNESS), "--timeout", str(timeout), "python", *args],
        cwd=cwd,
        env=os.environ.copy() | (env or {}),
        text=True,
        capture_output=True,
        timeout=timeout + 10,
        check=False,
    )
    invocation = EVIDENCE / ("public-" + str(uuid.uuid4()))
    invocation.mkdir(parents=True)
    (invocation / "stdout.txt").write_text(result.stdout)
    (invocation / "stderr.txt").write_text(result.stderr)
    (invocation / "command.json").write_text(
        json.dumps({"command": result.args, "returncode": result.returncode, "cwd": str(cwd)})
    )
    for relative in (
        "artifacts/verification",
        "artifacts/coverage",
        "artifacts/trace.jsonl",
        "ordinary-receipt.json",
        "ordinary-failed-receipt.json",
        "artifacts/imagej-reader/inputs.json",
        "artifacts/audit-events.json",
        ".coverage",
    ):
        source = cwd / relative
        destination = invocation / relative
        if source.is_dir():
            shutil.copytree(
                source, destination, symlinks=True, ignore=shutil.ignore_patterns("harmless-fifo")
            )
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return result


def write_program(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def executable(path: Path, body: str) -> None:
    write_program(path, f"#!{PYTHON}\n" + textwrap.dedent(body).lstrip())
    path.chmod(0o755)


def verifier_repo(path: Path, *, change: str = "", fail: str = "") -> Path:
    """Real Git/coverage/wheel evidence, with caller-owned Make command fixture.

    The phase fixture is not a full project check and makes no readiness claim.
    Native data/JSON/HTML are emitted by Coverage.py on two owned tiny modules.
    All mutations happen to public native report fields after authentic emission.
    """
    path.mkdir(parents=True)
    for folder in ("src/simrecon", "scripts", "artifacts", "dist"):
        (path / folder).mkdir(parents=True)
    (path / ".gitignore").write_text("artifacts/\ndist/\n.coverage*\n__pycache__/\n")
    (path / "src/simrecon/__init__.py").write_text("ANSWER = 42\n")
    (path / "scripts/owned.py").write_text("ANSWER = 42\n")
    (path / "marker.txt").write_bytes(b"A07 tracked preservation marker\n")
    (path / ".coveragerc").write_text("[run]\nbranch = True\nsource = src/simrecon, scripts\n")
    make = path / "phase-command"
    executable(
        make,
        """
        import base64
        import csv
        import hashlib
        import io
        import json
        import os
        from pathlib import Path
        import runpy
        import subprocess
        import sys
        import zipfile
        import coverage

        if "--version" in sys.argv:
            print("A07 disposable Make caller 1")
            raise SystemExit(0)
        phase = next(item for item in sys.argv[1:]
                     if not item.startswith(("-", "UV=")))
        with Path("artifacts/trace.jsonl").open("a") as output:
            output.write(json.dumps(sys.argv[1:]) + "\\n")
        print("authentic A07 phase output: " + phase, flush=True)
        change = os.environ.get("A07_CHANGE", "")
        failure = os.environ.get("A07_FAIL", "")
        if phase == failure:
            raise SystemExit(23)
        if phase == "coverage-clean":
            coverage.Coverage().erase()
        elif phase == "tests":
            cov = coverage.Coverage()
            cov.start()
            runpy.run_path("src/simrecon/__init__.py")
            runpy.run_path("scripts/owned.py")
            cov.stop()
            cov.save()
        elif phase == "coverage-json":
            cov = coverage.Coverage()
            cov.load()
            Path("artifacts/coverage").mkdir(exist_ok=True)
            cov.json_report(outfile="artifacts/coverage/coverage.json")
            report_path = Path("artifacts/coverage/coverage.json")
            report = json.loads(report_path.read_text())
            native = report["files"]["scripts/owned.py"]
            if change == "missing-destinations":
                native["executed_branches"] = {}
            elif change == "bad-destination":
                native["executed_branches"] = [[1, "destination"]]
            elif change == "exclusion-counter":
                native["summary"]["excluded_lines"] = 1
            elif change == "excluded-list":
                native["excluded_lines"] = [1]
            elif change == "global-exclusion-counter":
                report["totals"]["excluded_lines"] = 1
            report_path.write_text(json.dumps(report))
        elif phase == "coverage-html":
            cov = coverage.Coverage()
            cov.load()
            cov.html_report(directory="artifacts/coverage/html")
            html = Path("artifacts/coverage/html")
            if change == "directory-alias":
                (html / "harmless-alias").symlink_to(html.resolve(), target_is_directory=True)
            elif change == "directory-cycle":
                (html / "harmless-cycle").symlink_to(".", target_is_directory=True)
            elif change == "fifo-neighbor":
                os.mkfifo(html / "harmless-fifo")
        elif phase == "coverage-report":
            cov = coverage.Coverage()
            cov.load()
            cov.report()
        elif phase == "wheel":
            files = {
                "simrecon/__init__.py": b"ANSWER = 42\\n",
                "simrecon-1.0.dist-info/METADATA":
                    b"Metadata-Version: 2.1\\nName: simrecon\\nVersion: 1.0\\n",
                "simrecon-1.0.dist-info/WHEEL":
                    (b"Wheel-Version: 1.0\\nGenerator: A07\\n"
                     b"Root-Is-Purelib: true\\nTag: py3-none-any\\n"),
            }
            record = io.StringIO(newline="")
            writer = csv.writer(record)
            for name, content in files.items():
                digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
                writer.writerow((name, "sha256=" + digest.decode(), len(content)))
            writer.writerow(("simrecon-1.0.dist-info/RECORD", "", ""))
            files["simrecon-1.0.dist-info/RECORD"] = record.getvalue().encode()
            with zipfile.ZipFile("dist/simrecon-1.0-py3-none-any.whl", "w") as wheel:
                for name, content in files.items():
                    wheel.writestr(name, content)
        elif phase == "wheel-import":
            result = subprocess.run(
                [sys.executable, "-c",
                 "import sys; sys.path.insert(0, 'dist/simrecon-1.0-py3-none-any.whl'); "
                 "import simrecon; assert simrecon.ANSWER == 42"],
                timeout=15,
            )
            raise SystemExit(result.returncode)
        """,
    )
    for args in (
        ("init", "-q"),
        # Quiesce fixture setup before byte snapshots: commit can otherwise
        # launch detached maintenance that removes its lock during verification.
        # Repository-local only; https://git-scm.com/docs/git-config#maintenanceauto
        ("config", "--local", "maintenance.auto", "false"),
        ("add", "."),
        (
            "-c",
            "user.name=A07 Fixture",
            "-c",
            "user.email=a07@example.invalid",
            "commit",
            "-qm",
            "public fixture",
        ),
    ):
        # Keep fixture setup from leaving detached maintenance in the byte snapshot.
        subprocess.run(
            ["git", "-c", "maintenance.auto=false", *args],
            cwd=path,
            check=True,
            capture_output=True,
            timeout=15,
        )
    # Parameters are passed through the fixture's explicit environment in verify().
    assert change in {
        "",
        "missing-destinations",
        "bad-destination",
        "exclusion-counter",
        "excluded-list",
        "global-exclusion-counter",
        "directory-alias",
        "directory-cycle",
        "fifo-neighbor",
    }
    assert fail == "" or fail in PHASES
    return make


def verify(
    path: Path,
    make: Path,
    *,
    receipt: str = "artifacts/verification/receipt.json",
    change: str = "",
    fail: str = "",
) -> subprocess.CompletedProcess[str]:
    return run_public(
        path,
        str(ROOT / "scripts/verify.py"),
        "--make",
        str(make),
        "--uv",
        str(PYTHON),
        "--receipt",
        receipt,
        "--contract",
        "BASELINE-INFRASTRUCTURE-SUPPLEMENT-01",
        "--reviewed-tests",
        "A07-authored-not-yet-reviewed",
        "--base",
        "fixture",
        timeout=90,
        env={"A07_CHANGE": change, "A07_FAIL": fail},
    )


def protected_bytes(path: Path) -> dict[str, bytes]:
    """Owned fixture marker and actual Git metadata; no project source reads."""
    return {
        "marker.txt": (path / "marker.txt").read_bytes(),
        ".git/HEAD": (path / ".git/HEAD").read_bytes(),
        ".git/index": (path / ".git/index").read_bytes(),
    }


def receipt_at(path: Path, relative: str = "artifacts/verification/receipt.json") -> dict:
    return json.loads((path / relative).read_text())


def trace_at(path: Path) -> list[list[str]]:
    return [json.loads(line) for line in (path / "artifacts/trace.jsonl").read_text().splitlines()]


def attempted_phases(path: Path) -> list[str]:
    return [next(item for item in entry if item in PHASES) for entry in trace_at(path)]
