"""Export the already asserted M25 result to the approved ignored artifact."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

MEASUREMENTS_PATH = Path("artifacts/verification/measurements.json")
LIMIT_BYTES = 32 * 1024 * 1024


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"measurement export Git check failed: {result.stderr.strip()}")
    return result.stdout.strip()


def export_measurement(measurement: dict[str, Any]) -> None:
    """Write same-call native evidence only when verification supplied both values."""
    supplied_path = os.environ.get("SIMRECON_MEASUREMENTS_PATH")
    run_id = os.environ.get("SIMRECON_MEASUREMENTS_RUN_ID")
    if supplied_path is None and run_id is None:
        return
    if not supplied_path or not run_id:
        raise ValueError("measurement export requires both path and run ID")
    root = Path.cwd().resolve()
    destination = root / supplied_path
    if destination.absolute() != root / MEASUREMENTS_PATH:
        raise ValueError("measurement export destination is not the approved artifact path")
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", str(MEASUREMENTS_PATH)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode:
        raise ValueError("measurement export destination must be ignored by Git")
    tracked = git_output(root, "ls-files", "-z").split("\x00")
    resolved = destination.resolve()
    if any(resolved == (root / name).resolve() for name in tracked if name):
        raise ValueError("measurement export would overwrite tracked content")
    for option in ("--absolute-git-dir", "--git-common-dir"):
        metadata = (root / git_output(root, "rev-parse", option)).resolve()
        if resolved.is_relative_to(metadata):
            raise ValueError("measurement export would overwrite Git metadata")
    record = {**measurement, "limit_bytes": LIMIT_BYTES}
    report = {
        "schema": "org.simrecon.measurements",
        "version": 1,
        "run_id": run_id,
        "measurements": {"M25": record},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report) + "\n", encoding="utf-8")
