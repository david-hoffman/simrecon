"""Read the bound observations and reference volumes for one baseline figure."""

import hashlib
import json
from pathlib import Path

import numpy as np

BASELINE_WIENER = 0.020
STUDY = Path(__file__).resolve().parents[1]


def _read_metadata(path):
    payload = path.read_bytes()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def _load_reference(path, expected, role):
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"{role} does not match the selected case")
        stream.seek(0)
        return np.load(stream, allow_pickle=False)


def read_baseline(case, truth_path, conventional_path, archive_path, runtime_path):
    """Load the verified signed arrays and the digests used in figure provenance."""
    if runtime_path is None:
        history, source_hash = _read_metadata(STUDY / "historical-results.json")
        original = history["cases"][case]
        if history["wiener"] != BASELINE_WIENER:
            raise ValueError("expected an accepted historical baseline at Wiener 0.020")
        expected_archive = original["original_receipt_sha256"]
        source = "historical-results.json"
    else:
        runtime, source_hash = _read_metadata(runtime_path)
        receipt = runtime["observations"][f"w-{BASELINE_WIENER:.3f}.npz"]
        returned = receipt["resolved_settings"]
        if (
            runtime["case"] != case
            or returned["wiener"] != BASELINE_WIENER
            or returned["effective_wiener"] != [BASELINE_WIENER]
        ):
            raise ValueError("expected a matching case and returned Wiener value of 0.020")
        expected_archive = receipt["sha256"]
        source = "runtime.json"

    provenance, _ = _read_metadata(STUDY / "inputs" / "provenance.json")
    files = provenance["cases"][case]["files"]
    truth_hash = files["truth.npy"]["sha256"]
    conventional_hash = files["conventional.npy"]["sha256"]
    truth = _load_reference(truth_path, truth_hash, "truth")
    conventional = _load_reference(conventional_path, conventional_hash, "same-exposure mean")
    with archive_path.open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
        if archive_hash != expected_archive:
            raise ValueError("observation archive does not match the selected baseline receipt")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as observed:
            axes = tuple(observed[f"{axis}_um"] for axis in ("x", "y", "z"))
            counts = observed["image"]

    return (
        axes,
        counts,
        truth,
        conventional,
        {
            "truth.npy": truth_hash,
            "conventional.npy": conventional_hash,
            "observations.npz": archive_hash,
            source: source_hash,
        },
    )
