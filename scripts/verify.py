"""Run the ordinary full gate and record exact candidate evidence."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
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
    """Protect resolved candidate and Git paths from artifact writes."""
    target = path.resolve()
    return not any(
        target == item or item in target.parents or target in item.parents for item in protected
    )


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
    files = {}
    packages = {
        name: {kind: {"covered": 0, "total": 0} for kind in ("statements", "branches")}
        for name in ("simrecon", "scripts")
    }
    for directory, package in (("src/simrecon", "simrecon"), ("scripts", "scripts")):
        for path in sorted(Path(directory).rglob("*.py")):
            item = report["files"][path.as_posix()]
            summary = item["summary"]
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
            if any(type(summary[key]) is not int or summary[key] < 0 for key in keys):
                raise ValueError("Invalid native coverage counters")
            if (
                summary["missing_lines"]
                or summary["excluded_lines"]
                or summary["missing_branches"]
                or summary["num_partial_branches"]
                or item["missing_lines"]
                or item["excluded_lines"]
                or item["missing_branches"]
            ):
                problems.append("Incomplete or excluded owned coverage: " + path.as_posix())
            current = {}
            for kind, numerator, denominator, native in (
                ("statements", "covered_lines", "num_statements", "executed_lines"),
                ("branches", "covered_branches", "num_branches", "executed_branches"),
            ):
                covered, total = summary[numerator], summary[denominator]
                if len(item[native]) != covered:
                    raise ValueError("Invalid native coverage destinations")
                if covered != total:
                    problems.append("Incomplete native coverage: " + path.as_posix())
                current[kind] = {"covered": covered, "total": total}
                for counter in ("covered", "total"):
                    packages[package][kind][counter] += current[kind][counter]
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
                if algorithm not in {"sha256", "sha384", "sha512"}:
                    raise ValueError("Insecure wheel member hash")
                expected = (
                    base64.urlsafe_b64encode(hashlib.new(algorithm, data).digest())
                    .rstrip(b"=")
                    .decode()
                )
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
    try:
        protected = [Path(".git").resolve()]
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
            protected.extend(Path(name).resolve() for name in output.rstrip("\n\0").split("\0"))
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
                clear_measurements(protected)
            command = [args.make, "--no-print-directory", phase, "UV=" + args.uv]
            started = now()
            status, output = capture(command, phase_environment)
            print(output, end="", flush=True)
            log = Path("artifacts/verification/logs") / (phase + ".log")
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(output, encoding="utf-8")
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
            if args.measurements_required and phase == "tests":
                try:
                    receipt["measurements"] = measurements(run_id)
                except (OSError, ValueError) as error:
                    receipt["problems"].append(
                        "Measurement evidence invalid or unavailable: " + str(error)
                    )
            if status:
                exitcode = status
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
            receipt["problems"].append("Tracked candidate changed or unavailable")
        for name, path in inputs.items():
            entry = receipt["inputs"].setdefault(name, {"before": None, "after": None})
            entry["after"] = fingerprint(path) if path.is_file() else None
            if entry["before"] is None or entry["before"] != entry["after"]:
                receipt["problems"].append("Input changed or unavailable: " + name)
    except (OSError, ValueError):
        receipt["problems"].append("Final identity unavailable")
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return exitcode


sys.exit(main())
