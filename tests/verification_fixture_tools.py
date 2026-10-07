"""Controlled public command executables for verification receipt tests."""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import TypedDict


class CoverageSummary(TypedDict):
    """Describe native coverage counters and display fields in fixture reports."""

    covered_lines: int | str
    num_statements: int
    missing_lines: int
    excluded_lines: int
    num_branches: int
    num_partial_branches: int
    covered_branches: int
    missing_branches: int
    percent_covered: float
    percent_covered_display: str


PHASES = [
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
]

# Filename suffix and independently declared expanded WHEEL tags.
TAG_WHEELS = {
    "tag-missing-component": ("py3-none-any", ("py3-none",)),
    "tag-extra-component": ("py3-none-any", ("py3-none-any-extra",)),
    "tag-empty-python": ("py3-none-any", ("-none-any",)),
    "tag-empty-abi": ("py3-none-any", ("py3--any",)),
    "tag-empty-platform": ("py3-none-any", ("py3-none-",)),
    "tag-python-mismatch": ("py3-none-any", ("py2-none-any",)),
    "tag-abi-mismatch": ("py3-none-any", ("py3-abi3-any",)),
    "tag-platform-mismatch": ("py3-none-any", ("py3-none-linux_x86_64",)),
    "tag-incomplete-expansion": ("py2.py3-none-any", ("py3-none-any",)),
    "tag-extra-expansion": ("py3-none-any", ("py2-none-any", "py3-none-any")),
    "tag-valid-compressed": ("py2.py3-none-any", ("py2-none-any", "py3-none-any")),
    "tag-valid-build-platform": ("1-py3-none-linux_x86_64", ("py3-none-linux_x86_64",)),
}


def write_tag_evidence_wheel(path: Path, tags: tuple[str, ...]) -> None:
    """Write complete SHA-256 RECORD evidence after choosing declared tags."""
    info = "simrecon-1.2.0.dist-info"
    members = {
        f"{info}/METADATA": b"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.0\n",
        f"{info}/WHEEL": (
            "Wheel-Version: 1.0\nRoot-Is-Purelib: true\n"
            + ("Build: 1\n" if "-1-" in path.name else "")
            + "".join(f"Tag: {tag}\n" for tag in tags)
        ).encode("ascii"),
        "simrecon/__init__.py": b"__version__ = '1.2.0'\n",
    }
    records = []
    for name, data in members.items():
        value = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
        records.append(f"{name},sha256={value.decode('ascii')},{len(data)}")
    record_name = f"{info}/RECORD"
    members[record_name] = ("\n".join([*records, f"{record_name},,"]) + "\n").encode("ascii")
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)


def write_metadata_evidence_wheel(path: Path, mode: str) -> None:
    """Build independent V3 fixtures with valid evidence apart from one ambiguity."""
    info = "simrecon-1.2.0.dist-info"
    metadata = b"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.0\n"
    members = [
        (f"{info}/WHEEL", b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"),
        ("simrecon/__init__.py", b"__version__ = '1.2.0'\n"),
    ]
    if mode != "missing-metadata":
        members.append((f"{info}/METADATA", metadata))
    if mode == "multiple-metadata":
        members.append(("simrecon_extra-1.2.0.dist-info/METADATA", metadata))
    if mode == "duplicate-member":
        # Identical payloads isolate archive-name ambiguity from hash/size defects.
        members.append(("simrecon/__init__.py", b"__version__ = '1.2.0'\n"))
    records = []
    for name, data in dict(members).items():
        fingerprint = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
        records.append(f"{name},sha256={fingerprint.decode('ascii')},{len(data)}")
    record_name = f"{info}/RECORD"
    records.append(f"{record_name},,")
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members:
            archive.writestr(name, data)
        archive.writestr(record_name, "\n".join(records) + "\n")


def main():
    """Run a controlled Make or uv executable without product imports."""
    if sys.argv[1:] == ["--version"]:
        print("fixture tool 1.0")
        return 0
    root = Path.cwd()
    args = sys.argv[1:]
    with (root / "calls.jsonl").open("a") as stream:
        stream.write(json.dumps(args) + "\n")
    if Path(sys.argv[0]).name == "uv":
        print("controlled uv command")
        return 0
    phase = next((arg for arg in args if arg in PHASES), None)
    print(f"controlled phase {phase}")
    mode = os.environ.get("RECEIPT_FIXTURE_MODE", "complete")
    if phase == "lint" and mode == "command-failure":
        print("controlled failure diagnostic", file=sys.stderr)
        return 23
    if phase == "coverage-clean":
        shutil.rmtree(root / "artifacts/coverage", ignore_errors=True)
        shutil.rmtree(root / "dist", ignore_errors=True)
    if phase == "tests":
        if mode == "tracked-change":
            (root / "candidate.txt").write_bytes(b"changed\n")
        if mode == "commit-change":
            (root / "candidate.txt").write_bytes(b"new commit\n")
            subprocess.run(["git", "add", "candidate.txt"], check=True)
            subprocess.run(["git", "commit", "-qm", "controlled change"], check=True)
        if mode == "input-change":
            Path(os.environ["RECEIPT_PRIVATE_INPUT"]).write_bytes(b"changed input")
    if phase == "coverage-json" and mode != "missing-json":
        coverage_mode = {
            "partial-counter-overstatement": "zero-coverage",
            "partial-counter-understatement": "partial-coverage",
        }.get(mode, mode)
        files = {}
        for name in ("src/simrecon/sample.py", "scripts/sample.py", "scripts/branchless.py"):
            if mode == "missing-owned" and name.startswith("scripts/"):
                continue
            summary: CoverageSummary = {
                "covered_lines": 2,
                "num_statements": 2,
                "missing_lines": 0,
                "excluded_lines": 0,
                "num_branches": 2,
                "num_partial_branches": 0,
                "covered_branches": 2,
                "missing_branches": 0,
                "percent_covered": 100.0,
                "percent_covered_display": "100",
            }
            item = {
                "executed_lines": [1, 2],
                "missing_lines": [],
                "excluded_lines": [],
                "executed_branches": [[1, 2], [1, -1]],
                "missing_branches": [],
                "summary": summary,
            }
            if (
                coverage_mode in {"partial-coverage", "partial-json-failure", "partial-combined"}
                and name != "scripts/branchless.py"
            ):
                summary.update(
                    covered_branches=1,
                    missing_branches=1,
                    num_partial_branches=1,
                    percent_covered=75.0,
                    percent_covered_display="75",
                )
                item["executed_branches"] = [[1, 2]]
                item["missing_branches"] = [[1, -1]]
            if mode == "excluded-coverage":
                summary["excluded_lines"] = 1
                item["excluded_lines"] = [3]
            if mode == "malformed-coverage":
                summary["covered_lines"] = "two"
            if name == "scripts/branchless.py":
                summary.update(
                    covered_lines=1,
                    num_statements=1,
                    num_branches=0,
                    covered_branches=0,
                    missing_branches=0,
                    num_partial_branches=0,
                    excluded_lines=0,
                )
                item.update(
                    executed_lines=[1], executed_branches=[], missing_branches=[], excluded_lines=[]
                )
            if mode == "partial-statements" and name == "scripts/branchless.py":
                summary.update(
                    covered_lines=0,
                    missing_lines=1,
                    percent_covered=0.0,
                    percent_covered_display="0",
                )
                item.update(executed_lines=[], missing_lines=[1])
            if coverage_mode in {"partial-combined", "zero-coverage"}:
                covered = 0 if coverage_mode == "zero-coverage" else 1
                summary.update(
                    covered_lines=covered,
                    missing_lines=summary["num_statements"] - covered,
                )
                item["executed_lines"] = [1] if covered else []
                item["missing_lines"] = list(range(covered + 1, summary["num_statements"] + 1))
            if mode == "partial-combined" and summary["num_branches"]:
                summary.update(percent_covered=50.0, percent_covered_display="50")
                item.update(executed_branches=[[1, -1]], missing_branches=[[1, 2]])
            if coverage_mode == "zero-coverage":
                summary.update(
                    covered_branches=0,
                    missing_branches=summary["num_branches"],
                    num_partial_branches=0,
                    percent_covered=0.0,
                    percent_covered_display="0",
                )
                item["missing_branches"] = item["executed_branches"]
                item["executed_branches"] = []
            if name == "src/simrecon/sample.py":
                if mode == "partial-counter-overstatement":
                    summary["num_partial_branches"] = 1
                if mode == "partial-counter-understatement":
                    summary["num_partial_branches"] = 0
            files[name] = item
        totals: dict[str, int | float | str] = {
            key: sum(item["summary"][key] for item in files.values())
            for key in (
                "covered_lines",
                "num_statements",
                "missing_lines",
                "excluded_lines",
                "num_branches",
                "num_partial_branches",
                "covered_branches",
                "missing_branches",
            )
            if key != "covered_lines" or mode != "malformed-coverage"
        }
        totals.update(percent_covered=100.0, percent_covered_display="100")
        if coverage_mode in {"partial-coverage", "partial-json-failure"}:
            totals.update(percent_covered=700 / 9, percent_covered_display="78")
        if coverage_mode in {"partial-statements", "partial-combined", "zero-coverage"}:
            percent = {
                "partial-statements": 800 / 9,
                "partial-combined": 500 / 9,
                "zero-coverage": 0.0,
            }[coverage_mode]
            totals.update(percent_covered=percent, percent_covered_display=str(round(percent)))
        report = {
            "meta": {"version": "7.13.4", "format": 3, "branch_coverage": True},
            "files": files,
            "totals": totals,
        }
        invalid = files["src/simrecon/sample.py"]
        summary = invalid["summary"]
        if mode == "covered-statements-over-total":
            summary["covered_lines"] = 3
            invalid["executed_lines"] = [1, 2, 3]
        if mode == "covered-branches-over-total":
            summary["covered_branches"] = 3
            invalid["executed_branches"] = [[1, 2], [1, -1], [1, 3]]
        if mode in {"statement-count-mismatch", "overlapping-lines", "missing-line-length"}:
            summary.update(
                covered_lines=1, missing_lines=0 if mode == "statement-count-mismatch" else 1
            )
            invalid["executed_lines"] = [1]
            invalid["missing_lines"] = (
                [] if mode == "missing-line-length" else [1 if mode == "overlapping-lines" else 2]
            )
        if mode in {"branch-count-mismatch", "overlapping-branches", "missing-branch-length"}:
            summary.update(
                covered_branches=1,
                missing_branches=0 if mode == "branch-count-mismatch" else 1,
            )
            invalid["executed_branches"] = [[1, 2]]
            invalid["missing_branches"] = (
                []
                if mode == "missing-branch-length"
                else [[1, 2 if mode == "overlapping-branches" else -1]]
            )
        if mode == "duplicate-executed-lines":
            invalid["executed_lines"] = [1, 1]
        if mode == "duplicate-missing-lines":
            summary.update(covered_lines=0, missing_lines=2)
            invalid.update(executed_lines=[], missing_lines=[1, 1])
        if mode == "duplicate-executed-branches":
            invalid["executed_branches"] = [[1, 2], [1, 2]]
        if mode == "duplicate-missing-branches":
            summary.update(covered_branches=0, missing_branches=2)
            invalid.update(executed_branches=[], missing_branches=[[1, 2], [1, 2]])
        if mode == "malformed-line-destination":
            invalid["executed_lines"] = [True, 2]
        if mode == "malformed-branch-destination":
            invalid["executed_branches"] = [[1, "2"], [1, -1]]
        if mode == "negative-counter":
            summary["num_branches"] = -1
        if mode == "boolean-counter":
            summary["num_branches"] = True
        if mode == "inconsistent-zero-counter":
            summary["num_statements"] = 0
        if mode == "invalid-partial-counter":
            summary["num_partial_branches"] = 3
        if mode == "inconsistent-native-destinations":
            files["src/simrecon/sample.py"]["executed_branches"] = [[1, 2]]
        if mode == "missing-native-numerator":
            del files["src/simrecon/sample.py"]["summary"]["covered_branches"]
        if mode == "missing-native-destinations":
            del files["src/simrecon/sample.py"]["executed_branches"]
        if mode == "no-native-branches":
            report["meta"]["branch_coverage"] = False
        path = root / "artifacts/coverage/coverage.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report))
        if mode == "partial-json-failure":
            print("controlled partial JSON failure", file=sys.stderr)
            return 29
    if phase == "coverage-html" and mode != "missing-html":
        path = root / "artifacts/coverage/html/index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html>controlled coverage</html>")
    if phase == "wheel" and mode != "missing-wheel":
        dist = root / "dist"
        dist.mkdir(exist_ok=True)
        for index in range(2 if mode == "multiple-wheels" else 1):
            path = dist / f"simrecon-1.2.{index}-py3-none-any.whl"
            if mode in TAG_WHEELS:
                suffix, tags = TAG_WHEELS[mode]
                write_tag_evidence_wheel(dist / f"simrecon-1.2.0-{suffix}.whl", tags)
            elif mode in {"missing-metadata", "multiple-metadata", "duplicate-member"}:
                write_metadata_evidence_wheel(path, mode)
            elif mode == "invalid-wheel":
                path.write_bytes(b"not a zip")
            else:
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(
                        f"simrecon-1.2.{index}.dist-info/METADATA",
                        f"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.{index}\n"
                        if mode != "conflicting-metadata"
                        else "Metadata-Version: 2.1\nName: other\nVersion: 9.0\n",
                    )
                    archive.writestr(
                        f"simrecon-1.2.{index}.dist-info/WHEEL",
                        (
                            "Wheel-Version: invalid\n"
                            if mode == "invalid-wheel-format"
                            else "Wheel-Version: 1.0\n"
                        )
                        + "Generator: fixture\n"
                        "Root-Is-Purelib: true\nTag: py3-none-any\n",
                    )
                    archive.writestr("simrecon/__init__.py", f"__version__ = '1.2.{index}'\n")
                    records = []
                    for name in archive.namelist():
                        data = archive.read(name)
                        algorithm = (
                            "sha512"
                            if mode == "sha512-wheel"
                            else "sha1"
                            if mode == "weak-wheel-hash"
                            else "sha256"
                        )
                        fingerprint = (
                            base64.urlsafe_b64encode(hashlib.new(algorithm, data).digest())
                            .rstrip(b"=")
                            .decode("ascii")
                        )
                        size = len(data) + (1 if mode == "record-size-mismatch" else 0)
                        if mode == "record-hash-mismatch":
                            fingerprint = "A" * len(fingerprint)
                        if mode != "incomplete-record" or name != "simrecon/__init__.py":
                            records.append(f"{name},{algorithm}={fingerprint},{size}")
                    record_name = f"simrecon-1.2.{index}.dist-info/RECORD"
                    records.append(
                        f"{record_name},,"
                        if mode != "invalid-record-self"
                        else f"{record_name},sha256=AAAA,1"
                    )
                    archive.writestr(record_name, "\n".join(records) + "\n")
    if phase == "wheel" and mode == "wheel-build-failure":
        print("controlled wheel build failure", file=sys.stderr)
        return 31
    if phase == "audit" and mode == "unavailable-final-identity":
        (root / ".git/HEAD").unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
