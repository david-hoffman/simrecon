"""Run the ordinary full gate and record exact candidate evidence."""

from __future__ import annotations

import argparse
import base64
import csv
import glob
import hashlib
import io
import json
import os
import platform
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import zipfile
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from email.parser import Parser
from itertools import product
from pathlib import Path
from typing import Any
from uuid import uuid4

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
MEASUREMENTS_PATH = Path("artifacts/verification/measurements.json")


def now() -> str:
    """Return a UTC timestamp."""
    return datetime.now(timezone(timedelta(0))).isoformat()


def fingerprint(path: Path) -> dict[str, Any]:
    """Fingerprint regular file bytes."""
    data = path.read_bytes()
    return {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def capture(command: list[str], environment: dict[str, str] | None = None) -> tuple[int, str]:
    """Confine measurement export to an explicitly supplied phase environment."""
    if environment is None:
        environment = os.environ.copy()
        environment.pop("SIMRECON_MEASUREMENTS_PATH", None)
        environment.pop("SIMRECON_MEASUREMENTS_RUN_ID", None)
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            env=environment,
        )
        return result.returncode, result.stdout
    except OSError:
        return 127, "Command unavailable\n"


def identity() -> dict[str, Any]:
    """Collect tracked Git identity and byte manifest."""

    def git(*args: str) -> str:
        status, output = capture(["git", "--no-optional-locks", *args])
        if status:
            raise ValueError("Git identity unavailable")
        return output.rstrip("\n")

    names = git("ls-files", "-z").split("\0")[:-1]
    return {
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
        "untracked": git("ls-files", "--others", "--exclude-standard", "-z").split("\0")[:-1],
        "manifest": {name: fingerprint(Path(name))["sha256"] for name in names},
    }


def safe_output(path: Path, protected: list[Path]) -> bool:
    """Protect retained and currently resolved candidate and Git locations."""
    targets = (path.absolute(), path.resolve())
    locations = {location for item in protected for location in (item, item.resolve())}
    return not any(
        target == item or item in target.parents or target in item.parents
        for target in targets
        for item in locations
    )


def persist_output(path: Path, text: str, protected: list[Path]) -> None:
    """Revalidate each write and replace leaves without truncating hard-link targets."""
    if not safe_output(path, protected):
        raise ValueError("Unsafe output destination")
    path.parent.mkdir(parents=True, exist_ok=True)
    permissions = stat.S_IMODE(path.stat().st_mode) if path.is_file() else None
    candidate = path.parent / ("." + uuid4().hex + ".tmp")
    if not safe_output(candidate, protected):
        raise ValueError("Unsafe output destination")
    temporary = None
    try:
        with candidate.open("x", encoding="utf-8") as stream:
            temporary = candidate
            if permissions is not None:
                os.fchmod(stream.fileno(), permissions)
            stream.write(text)
        if not safe_output(path, protected):
            raise ValueError("Unsafe output destination")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def protect_evidence(paths: list[Path], protected: list[Path]) -> None:
    """Retain actual evidence locations for subsequent verifier-owned writes."""
    for path in paths:
        if path.is_file():
            protected.extend((path.absolute(), path.resolve()))


def protect_test_databases(paths: list[Path], protected: list[Path]) -> None:
    """Associate test-emitted native databases with the current complete report."""
    try:
        report = json.loads(Path("artifacts/coverage/coverage.json").read_text())
        reported = {Path(name).resolve() for name in report["files"]}
    except (OSError, ValueError, KeyError, TypeError):
        # The ordinary report collector diagnoses invalid/unavailable reports.
        return
    for path in paths:
        try:
            with path.open("rb") as stream:
                if stream.read(16) != b"SQLite format 3\x00":
                    continue
            connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            try:
                measured = {
                    Path(name).resolve() for (name,) in connection.execute("SELECT path FROM file")
                }
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            continue
        if measured & reported:
            protect_evidence([path], protected)


def coverage_data_path() -> Path:
    """Resolve storage through the installed Coverage.py public configuration API."""
    interpreter = Path(".venv/bin/python")
    if not interpreter.is_file():
        interpreter = Path(__file__).resolve().parents[1] / ".venv/bin/python"
    result = subprocess.run(
        [
            str(interpreter),
            "-c",
            "import json; from coverage import Coverage; "
            "print(json.dumps(Coverage().get_option('run:data_file')))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ValueError("Coverage data-file configuration unavailable")
    return Path(json.loads(result.stdout)).expanduser().absolute()


def coverage_data_files() -> list[Path]:
    """Observe the selected database and parallel shards without directory traversal."""
    native = coverage_data_path()
    return [native, *native.parent.glob(glob.escape(native.name) + ".*")]


def evidence_files(root: Path) -> dict[Path, tuple[int, int, int, int, int]]:
    """Observe file writes without reading payloads or assuming native output names."""
    files = {}
    visited = set()

    def observe(path: Path) -> None:
        with suppress(FileNotFoundError):
            metadata = path.stat()
            if stat.S_ISREG(metadata.st_mode):
                # Compare the same destination even when reached through a
                # different directory alias before and after the phase.
                files[path.resolve()] = (
                    metadata.st_dev,
                    metadata.st_ino,
                    metadata.st_size,
                    metadata.st_mtime_ns,
                    metadata.st_ctime_ns,
                )

    for directory, directories, names in os.walk(root, followlinks=True):
        directory_metadata = Path(directory).stat()
        directory_identity = (directory_metadata.st_dev, directory_metadata.st_ino)
        if directory_identity in visited:
            directories[:] = []
            continue
        visited.add(directory_identity)
        for name in names:
            observe(Path(directory) / name)
    if root == Path("."):
        for path in coverage_data_files():
            observe(path)
    return files


def collect_final_identity(receipt: dict[str, Any], inputs: dict[str, Path]) -> None:
    """Record actual candidate/input identities independently of output availability."""
    problems = []
    receipt["after"] = None
    try:
        receipt["after"] = identity()
        if (
            receipt["before"] is None
            or any(
                receipt["before"][key] != receipt["after"][key]
                for key in ("commit", "tree", "manifest")
            )
            or receipt["after"]["dirty"]
        ):
            problems.append("Tracked candidate changed or unavailable")
    except (OSError, ValueError):
        problems.append("Final identity unavailable")
    for name, path in inputs.items():
        entry = receipt["inputs"].setdefault(name, {"before": None, "after": None})
        entry["after"] = None
        with suppress(OSError):
            entry["after"] = fingerprint(path) if path.is_file() else None
        if entry["before"] is None or entry["before"] != entry["after"]:
            problems.append("Input changed or unavailable: " + name)
    receipt["problems"].extend(item for item in problems if item not in receipt["problems"])


def clear_measurements(protected: list[Path]) -> None:
    """Remove prior evidence only after protecting the resolved destination."""
    if not safe_output(MEASUREMENTS_PATH, protected):
        raise ValueError("Unsafe measurement destination")
    MEASUREMENTS_PATH.unlink(missing_ok=True)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys at every object level."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate measurement JSON key")
        result[key] = value
    return result


def measurements(run_id: str) -> dict[str, Any]:
    """Validate current M25 evidence and fingerprint the exact parsed bytes."""
    data = MEASUREMENTS_PATH.read_bytes()
    report = json.loads(data, object_pairs_hook=unique_object)
    if (
        not isinstance(report, dict)
        or report.get("schema") != "org.simrecon.measurements"
        or type(report.get("version")) is not int
        or report["version"] != 1
        or report.get("run_id") != run_id
    ):
        raise ValueError("Invalid measurement report identity")
    records = report.get("measurements")
    if not isinstance(records, dict) or set(records) != {"M25"}:
        raise ValueError("Expected exactly the M25 measurement")
    record = records["M25"]
    if not isinstance(record, dict):
        raise ValueError("Invalid M25 measurement record")
    fields = ("baseline", "peak", "increment_bytes", "limit_bytes")
    if any(type(record.get(key)) is not int or record[key] < 0 for key in fields):
        raise ValueError("Invalid measurement integer")
    units = record.get("units")
    if units not in ("bytes", "KiB"):
        raise ValueError("Invalid measurement units")
    increment = (record["peak"] - record["baseline"]) * (1 if units == "bytes" else 1024)
    if (
        record["peak"] < record["baseline"]
        or record["increment_bytes"] != increment
        or record["limit_bytes"] != 33554432
        or increment > record["limit_bytes"]
    ):
        raise ValueError("Invalid measurement arithmetic or limit")
    return {
        "schema": report["schema"],
        "version": report["version"],
        "run_id": run_id,
        "measurements": {"M25": {**{key: record[key] for key in fields}, "units": units}},
        "path": MEASUREMENTS_PATH.as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def native_destinations(values: Any, branches: bool) -> set[int | tuple[int, int]]:
    """Validate unique native lines or branch arcs, including negative exit destinations."""
    if not isinstance(values, list):
        raise ValueError("Invalid native coverage destinations")
    destinations: set[int | tuple[int, int]] = set()
    for value in values:
        if branches:
            if (
                not isinstance(value, list)
                or len(value) != 2
                or any(type(line) is not int for line in value)
                or value[0] <= 0
                or value[1] == 0
            ):
                raise ValueError("Invalid native coverage destinations")
            destinations.add((value[0], value[1]))
        else:
            if type(value) is not int or value <= 0:
                raise ValueError("Invalid native coverage destinations")
            destinations.add(value)
    if len(destinations) != len(values):
        raise ValueError("Duplicate native coverage destinations")
    return destinations


def metrics(problems: list[str]) -> dict[str, Any]:
    """Validate and aggregate native owned-file coverage evidence."""
    reports = {
        "json": "artifacts/coverage/coverage.json",
        "html": "artifacts/coverage/html/index.html",
    }
    if not Path(reports["html"]).is_file():
        problems.append("Missing coverage HTML")
    report = json.loads(Path(reports["json"]).read_text())
    if report["meta"]["branch_coverage"] is not True:
        raise ValueError("Native branch measurement unavailable")
    # Native totals include all reported files, not nested function/class regions.
    keys = (
        "covered_lines",
        "num_statements",
        "covered_branches",
        "num_branches",
        "missing_lines",
        "excluded_lines",
        "missing_branches",
        "num_partial_branches",
    )
    totals = dict.fromkeys(keys, 0)
    for item in report["files"].values():
        summary = item["summary"]
        if any(type(summary[key]) is not int or summary[key] < 0 for key in keys):
            raise ValueError("Invalid native coverage counters")
        for key in keys:
            totals[key] += summary[key]
    if any(type(report["totals"][key]) is not int or report["totals"][key] < 0 for key in keys):
        raise ValueError("Invalid native coverage counters")
    if any(report["totals"][key] != totals[key] for key in keys):
        raise ValueError("Invalid native coverage totals")
    files = {}
    packages = {
        name: {kind: {"covered": 0, "total": 0} for kind in ("statements", "branches")}
        for name in ("simrecon", "scripts")
    }
    for directory, package in (("src/simrecon", "simrecon"), ("scripts", "scripts")):
        for path in sorted(Path(directory).rglob("*.py")):
            item = report["files"][path.as_posix()]
            summary = item["summary"]
            excluded = native_destinations(item["excluded_lines"], False)
            if len(excluded) != summary["excluded_lines"]:
                raise ValueError("Invalid native coverage counters")
            if excluded:
                problems.append("Excluded owned coverage: " + path.as_posix())
            current = {}
            for kind, numerator, denominator, native, missing in (
                (
                    "statements",
                    "covered_lines",
                    "num_statements",
                    "executed_lines",
                    "missing_lines",
                ),
                (
                    "branches",
                    "covered_branches",
                    "num_branches",
                    "executed_branches",
                    "missing_branches",
                ),
            ):
                covered, total = summary[numerator], summary[denominator]
                executed = native_destinations(item[native], kind == "branches")
                unexecuted = native_destinations(item[missing], kind == "branches")
                if (
                    covered + summary[missing] != total
                    or len(executed) != covered
                    or len(unexecuted) != summary[missing]
                    or executed & unexecuted
                ):
                    raise ValueError("Invalid native coverage destinations")
                current[kind] = {"covered": covered, "total": total}
                for counter in ("covered", "total"):
                    packages[package][kind][counter] += current[kind][counter]
            missing_lines = set(item["missing_lines"])
            if any(
                endpoint in missing_lines for arc in item["executed_branches"] for endpoint in arc
            ):
                raise ValueError("Executed branch endpoint is a missing statement")
            partial = sum(arc[0] not in missing_lines for arc in item["missing_branches"])
            if summary["num_partial_branches"] != partial:
                raise ValueError("Invalid native partial branch counter")
            files[path.as_posix()] = current
    aggregate = {
        kind: {
            counter: sum(package[kind][counter] for package in packages.values())
            for counter in ("covered", "total")
        }
        for kind in ("statements", "branches")
    }
    return {"reports": reports, "files": files, "global": aggregate, "packages": packages}


def artifact() -> dict[str, Any]:
    """Validate the sole wheel and its recorded member fingerprints."""
    wheels = list(Path("dist").glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected one wheel")
    path = wheels[0]
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata_names) != 1 or len(names) != len(set(names)):
            raise ValueError("Invalid wheel metadata")
        metadata_name = metadata_names[0]
        metadata = Parser().parsestr(archive.read(metadata_name).decode())
        version = metadata["Version"]
        prefix = f"simrecon-{version}"
        if (
            metadata["Name"] != "simrecon"
            or not version
            or metadata_name != prefix + ".dist-info/METADATA"
            or not path.name.startswith(prefix + "-")
        ):
            raise ValueError("Wheel identity mismatch")
        info = prefix + ".dist-info/"
        wheel = Parser().parsestr(archive.read(info + "WHEEL").decode())
        tags = wheel.get_all("Tag")
        if wheel["Wheel-Version"] != "1.0" or not tags:
            raise ValueError("Invalid wheel format")
        filename_tags = {
            "-".join(parts)
            for parts in product(*(part.split(".") for part in path.stem.split("-")[-3:]))
        }
        if any(
            re.fullmatch(r"[A-Za-z0-9_]+-[A-Za-z0-9_]+-[A-Za-z0-9_]+", tag) is None for tag in tags
        ):
            raise ValueError("Invalid expanded wheel tag")
        if set(tags) != filename_tags:
            raise ValueError("Wheel tags disagree with filename")
        record = info + "RECORD"
        rows = list(csv.reader(io.StringIO(archive.read(record).decode())))
        if {row[0] for row in rows} != set(names) or len(rows) != len(names):
            raise ValueError("Incomplete wheel RECORD")
        for name, digest, size in rows:
            if name == record:
                if digest or size:
                    raise ValueError("Invalid RECORD self entry")
            else:
                data = archive.read(name)
                algorithm, encoded = digest.split("=", 1)
                member_hash = hashlib.new(algorithm, data)
                # Resolve aliases before recognizing conventional secure fixed-length
                # SHA-2/SHA-3 and default BLAKE2 algorithms. Digest length alone
                # does not establish security for an arbitrary backend algorithm.
                if member_hash.name not in {
                    "sha256",
                    "sha384",
                    "sha512",
                    "sha512_256",
                    "sha3_256",
                    "sha3_384",
                    "sha3_512",
                    "blake2b",
                    "blake2s",
                }:
                    raise ValueError("Insecure wheel member hash")
                expected = base64.urlsafe_b64encode(member_hash.digest()).rstrip(b"=").decode()
                if encoded != expected or size != str(len(data)):
                    raise ValueError("Wheel member fingerprint mismatch")
    return {"path": path.as_posix(), **fingerprint(path), "version": version}


def main() -> int:
    """Execute required phases and write an honest receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in (
        ("uv", "uv"),
        ("make", "make"),
        ("receipt", "artifacts/verification/receipt.json"),
    ):
        parser.add_argument("--" + name, default=default)
    for name in ("contract", "reviewed-tests", "base"):
        parser.add_argument("--" + name)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--measurements-required", action="store_true")
    args = parser.parse_args()
    run_id = str(uuid4())
    phase_environment = None
    if args.measurements_required:
        phase_environment = {
            **os.environ,
            "SIMRECON_MEASUREMENTS_PATH": MEASUREMENTS_PATH.as_posix(),
            "SIMRECON_MEASUREMENTS_RUN_ID": run_id,
        }
    inputs = {}
    for value in args.input:
        if "=" not in value:
            parser.error("Inputs require NAME=PATH")
        name, value = value.split("=", 1)
        if not name or name in inputs:
            parser.error("Input aliases must be nonempty and unique")
        inputs[name] = Path(value)
    receipt: dict[str, Any] = {
        "schema": "org.simrecon.verification",
        "version": 1,
        "result": "failed",
        "started_at": now(),
        "finished_at": None,
        "context": {
            "contract": args.contract,
            "reviewed_tests": args.reviewed_tests,
            "integration_base": args.base,
        },
        "environment": {
            "platform": platform.platform(),
            "python": {"executable": sys.executable, "version": platform.python_version()},
            "tools": dict.fromkeys(("ruff", "pyright", "coverage", "pytest")),
        },
        "before": None,
        "after": None,
        "phases": [],
        "inputs": {},
        "coverage": None,
        "artifact": None,
        "measurements": None,
        "problems": [],
    }
    for name, executable in (("make", args.make), ("uv", args.uv), ("git", "git")):
        status, output = capture([executable, "--version"])
        receipt["environment"][name] = {
            "executable": shutil.which(executable),
            "version": output.strip() if status == 0 else None,
        }
    destination = Path(args.receipt)
    exitcode = 1
    evidence_protected: list[Path] = []
    native_protected: list[Path] = []
    test_emitted: list[Path] = []
    try:
        protected = [Path(".git").absolute(), Path(".git").resolve()]
        for arguments in (
            ["ls-files", "-z"],
            ["rev-parse", "--absolute-git-dir"],
            ["rev-parse", "--git-common-dir"],
        ):
            status, output = capture(["git", "--no-optional-locks", *arguments])
            if status:
                raise ValueError(
                    "Measurement output protection unavailable"
                    if args.measurements_required
                    else "Output protection unavailable"
                )
            for name in output.rstrip("\n\0").split("\0"):
                protected.extend((Path(name).absolute(), Path(name).resolve()))
        if args.measurements_required and not safe_output(MEASUREMENTS_PATH, protected):
            raise ValueError("Unsafe measurement destination")
        logs = Path("artifacts/verification/logs")
        if not safe_output(destination, protected) or not safe_output(logs, protected):
            raise ValueError("Unsafe receipt/log destination")
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    try:
        if any(not safe_output(logs / (phase + ".log"), protected) for phase in PHASES):
            raise ValueError("Unsafe phase-log destination")
        if args.measurements_required:
            clear_measurements(protected)
        receipt["before"] = identity()
        for name, path in inputs.items():
            receipt["inputs"][name] = {"before": None, "after": None}
            if not path.is_file():
                raise ValueError("Input is not a regular file: " + name)
            receipt["inputs"][name]["before"] = fingerprint(path)
        if receipt["before"]["dirty"]:
            raise ValueError("Tracked candidate is dirty at start")
        for phase in PHASES:
            if args.measurements_required and phase == "tests":
                clear_measurements([*protected, *evidence_protected])
            command = [args.make, "--no-print-directory", phase, "UV=" + args.uv]
            started = now()
            evidence_root = {
                "tests": Path("."),
                "coverage-combine": Path("."),
                "coverage-html": Path("artifacts/coverage/html"),
            }.get(phase)
            emitted_before = evidence_files(evidence_root) if evidence_root is not None else {}
            status, output = capture(command, phase_environment)
            if status:
                exitcode = status
            log = Path("artifacts/verification/logs") / (phase + ".log")
            receipt["phases"].append(
                {
                    "name": phase,
                    "command": command,
                    "returncode": status,
                    "started_at": started,
                    "finished_at": now(),
                    "log": log.as_posix(),
                }
            )
            if evidence_root is not None:
                emitted = [
                    path
                    for path, metadata in evidence_files(evidence_root).items()
                    if emitted_before.get(path) != metadata
                ]
                if phase == "tests":
                    test_emitted = emitted
                    native = coverage_data_path().resolve()
                    protect_evidence(
                        [path for path in emitted if path == native],
                        native_protected,
                    )
                else:
                    protect_evidence(emitted, evidence_protected)
            if phase == "coverage-json":
                protect_test_databases(test_emitted, evidence_protected)
            report = {
                "coverage-json": Path("artifacts/coverage/coverage.json"),
                "coverage-html": Path("artifacts/coverage/html/index.html"),
            }.get(phase)
            if report is not None:
                protect_evidence([report], evidence_protected)
            if phase == "wheel":
                protect_evidence(list(Path("dist").glob("*.whl")), evidence_protected)
            if args.measurements_required and phase == "tests":
                protect_evidence([MEASUREMENTS_PATH], evidence_protected)
                try:
                    receipt["measurements"] = measurements(run_id)
                except (OSError, ValueError) as error:
                    receipt["problems"].append(
                        "Measurement evidence invalid or unavailable: " + str(error)
                    )
            print(output, end="", flush=True)
            persist_output(log, output, [*protected, *evidence_protected, *native_protected])
            protect_evidence([log], evidence_protected)
            if status:
                raise ValueError("Phase failed: " + phase)
            if phase == "sync":
                for tool in receipt["environment"]["tools"]:
                    tool_status, version = capture([args.uv, "run", "--locked", tool, "--version"])
                    receipt["environment"]["tools"][tool] = (
                        version.strip() if tool_status == 0 else None
                    )
        exitcode = 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        receipt["problems"].append(
            str(error) if not isinstance(error, OSError) else "Evidence file unavailable"
        )
    attempted = {phase["name"] for phase in receipt["phases"]}
    for field, required, collect in (
        ("coverage", {"coverage-json"}, lambda: metrics(receipt["problems"])),
        ("artifact", {"wheel"}, artifact),
    ):
        if required <= attempted:
            try:
                receipt[field] = collect()
            except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
                receipt["problems"].append(
                    str(error) if not isinstance(error, OSError) else "Evidence file unavailable"
                )
    collect_final_identity(receipt, inputs)
    if receipt["measurements"] is not None:
        try:
            if (
                not safe_output(MEASUREMENTS_PATH, protected)
                or fingerprint(MEASUREMENTS_PATH)["sha256"] != receipt["measurements"]["sha256"]
            ):
                raise ValueError("Measurement evidence changed after tests")
        except (OSError, ValueError) as error:
            receipt["measurements"] = None
            receipt["problems"].append("Measurement evidence invalid or unavailable: " + str(error))
    if receipt["problems"]:
        exitcode = exitcode or 1
    else:
        receipt["result"] = "passed"
    receipt["finished_at"] = now()
    # Approved inputs cannot be overwritten by the evidence that describes them.
    receipt_protected = [
        *protected,
        *evidence_protected,
        *native_protected,
        *(Path(phase["log"]).absolute() for phase in receipt["phases"]),
        *(path.absolute() for path in inputs.values() if not path.is_dir()),
    ]
    try:
        persist_output(destination, json.dumps(receipt, indent=2) + "\n", receipt_protected)
        recorded = json.dumps((receipt["after"], receipt["inputs"], receipt["problems"]))
        collect_final_identity(receipt, inputs)
        if recorded != json.dumps((receipt["after"], receipt["inputs"], receipt["problems"])):
            if receipt["problems"]:
                receipt["result"] = "failed"
                exitcode = exitcode or 1
            receipt["finished_at"] = now()
            persist_output(destination, json.dumps(receipt, indent=2) + "\n", receipt_protected)
    except (OSError, ValueError):
        print("Receipt output unsafe or unavailable", file=sys.stderr)
        return exitcode or 1
    return exitcode


sys.exit(main())
