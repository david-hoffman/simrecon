"""Verify ten saved observations against witness receipts and collect their scores."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from run_study import digest, observation_name, write_json
from sweep_response import WIENERS
from sweep_witness import BASE_WIENER, require_complete


def require(condition: bool, message: str) -> None:
    """Fail at the named receipt mismatch."""
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> Any:
    """Read a JSON receipt."""
    return json.loads(path.read_text(encoding="utf-8"))


def identity(array: np.ndarray) -> list[Any]:
    """Check the witness wire identity without altering the saved observation."""
    data = np.ascontiguousarray(array, dtype=array.dtype.newbyteorder("<"))
    return [
        list(data.shape),
        data.dtype.str,
        hashlib.sha256(memoryview(data).cast("B")).hexdigest(),
    ]


def collect_case(case: str, directory: Path) -> tuple[list[dict], dict]:
    """Verify one completed case's row, observation and typed factor receipts."""
    progress = [
        json.loads(line)
        for line in (directory / "progress.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    require(
        progress[-1]["event"] == "complete" and progress[-1]["scored"] == list(WIENERS),
        f"{case}: observer did not finish",
    )
    rows = [
        json.loads(line)
        for line in (directory / "rows.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    metadata = read_json(directory / "case.json")
    runtime = read_json(directory / "runtime.json")
    require(runtime["case"] == case and all(row["case"] == case for row in rows), case)
    require(
        runtime["fixed_factors"] == metadata["fixed_factors"]
        and runtime["default_replay"] == metadata["default_replay"],
        f"{case}: runtime and witness provenance differ",
    )
    with np.load(directory / "fixed-factors.npz", allow_pickle=False) as archive:
        require(
            {key: identity(archive[key]) for key in archive.files}
            == metadata["fixed_factors"]["array_identities"],
            f"{case}: fixed factor array identity mismatch",
        )
    primary = runtime["observations"][observation_name(BASE_WIENER)]
    replay = runtime["default_replay_returned"]
    schedule = runtime["workflow_effective_wiener"]
    require(
        all(replay[key] == value for key, value in primary.items() if key != "sha256")
        and schedule == [BASE_WIENER]
        and type(schedule[0]) is float
        and type(replay["resolved_settings"]["wiener"]) is float
        and type(replay["resolved_settings"]["effective_wiener"][0]) is float
        and type(replay["resolved_settings"]["wiener_increment"]) is float,
        f"{case}: missing exact returned default replay settings or effective Wiener",
    )
    for row in rows:
        value = row["wiener"]
        name = observation_name(value)
        path = directory / name
        entry = runtime["observations"][name]
        require(digest(path) == entry["sha256"], f"{case}/{name}: archive digest mismatch")
        require(
            type(row["effective_wiener"]) is float
            and type(entry["resolved_settings"]["wiener"]) is float
            and entry["resolved_settings"]["effective_wiener"] == [value]
            and type(entry["resolved_settings"]["effective_wiener"][0]) is float
            and type(entry["resolved_settings"]["wiener_increment"]) is float
            and entry["resolved_settings"]["wiener"] == row["effective_wiener"] == value
            and entry["resolved_settings"]["wiener_increment"] == 0,
            f"{case}/{name}: Wiener schedule mismatch",
        )
        with np.load(path, allow_pickle=False) as archive:
            require(
                set(archive.files) == {"image", "x_um", "y_um", "z_um"},
                f"{case}/{name}: observation members differ",
            )
            require(
                identity(archive["image"]) == row["signed_image_counts_identity"]
                and all(
                    identity(archive[key]) == metadata["default_replay"][key]
                    for key in ("x_um", "y_um", "z_um")
                ),
                f"{case}/{name}: signed image or physical axis identity mismatch",
            )
    if case == "beads":
        score = read_json(directory / "bead-default-score.json")
        require(
            score["status"] == 0
            and score["receipt_sha256"]
            == runtime["observations"][observation_name(BASE_WIENER)]["sha256"],
            "beads: default figure score is not bound to the measured observation",
        )
    return rows, metadata


def main() -> None:
    """Collect the two completed cases into the measured plotter's schema."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("beads", type=Path)
    parser.add_argument("cell", type=Path)
    parser.add_argument("output", type=Path, help="new aggregate JSON file")
    args = parser.parse_args()
    rows: list[dict] = []
    cases: dict[str, dict] = {}
    for case in ("beads", "cell"):
        observed, cases[case] = collect_case(case, getattr(args, case))
        rows.extend(observed)
    require_complete(rows)
    write_json(args.output, {"rows": rows, "cases": cases})
    print(f"{len(rows)} unique witnessed observations")


if __name__ == "__main__":
    main()
