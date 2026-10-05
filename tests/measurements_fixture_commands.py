"""Synthetic same-run measurement phase commands; reuse approved receipt evidence."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from verification_fixture_tools import PHASES
from verification_fixture_tools import main as receipt_main


def main() -> int:
    root = Path.cwd()
    args = sys.argv[1:]
    path_value = os.environ.get("SIMRECON_MEASUREMENTS_PATH")
    run_id = os.environ.get("SIMRECON_MEASUREMENTS_RUN_ID")
    observation = {"args": args, "path": path_value, "run_id": run_id}
    with (root / "measurement-calls.jsonl").open("a") as stream:
        stream.write(json.dumps(observation) + "\n")
    phase = next((arg for arg in args if arg in PHASES), None)
    status = receipt_main()
    mode = os.environ.get("EXPORT_FIXTURE_MODE", "valid")
    if phase == "tests" and mode == "tests-no-report":
        print("controlled tests failure without measurements", file=sys.stderr)
        return 37
    emit_phase = "audit" if mode == "late-report" else "tests"
    if phase == emit_phase and mode != "missing" and path_value is not None:
        report = json.loads(os.environ["EXPORT_FIXTURE_REPORT"])
        if isinstance(report, dict) and report.get("run_id") == "CURRENT":
            report["run_id"] = run_id
        payload = json.dumps(report)
        if mode == "duplicate-top":
            payload = payload[:-1] + ', "version": 1}'
        elif mode == "duplicate-record":
            payload = payload.replace('"peak":', '"baseline": 100, "peak":', 1)
        elif mode == "duplicate-id":
            payload = payload.replace('"M25":', '"M25": {}, "M25":', 1)
        elif mode == "malformed":
            payload = "{"
        elif mode == "invalid-utf8":
            payload = ""
        destination = root / path_value
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"\xff" if mode == "invalid-utf8" else payload.encode("utf-8"))
        if mode in {"changed-report-same-id", "reformatted-report-same-id"}:
            destination.with_name("tests-phase-measurements.json").write_bytes(
                destination.read_bytes()
            )
        if mode == "tests-failure":
            print("controlled tests failure after measurements", file=sys.stderr)
            return 37
    if phase == "audit" and mode == "changed-id" and path_value is not None:
        destination = root / path_value
        report = json.loads(destination.read_text())
        report["run_id"] = "11111111-1111-4111-8111-111111111111"
        destination.write_text(json.dumps(report))
    if (
        phase == "audit"
        and mode in {"changed-report-same-id", "reformatted-report-same-id"}
        and path_value is not None
    ):
        destination = root / path_value
        report = json.loads(destination.read_bytes())
        if mode == "changed-report-same-id":
            report["measurements"]["M25"].update(baseline=200, peak=211, increment_bytes=11264)
        replacement = destination.with_suffix(".replacement")
        replacement.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
        replacement.replace(destination)
    if phase == "audit" and mode == "unavailable" and path_value is not None:
        destination = root / path_value
        destination.unlink()
        destination.mkdir()
    return status


if __name__ == "__main__":
    sys.exit(main())
