"""Check generated files against frozen byte identities and the native-dose rule."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def _check(case, output, expected):
    actual = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if actual["case"] != case:
        raise ValueError(f"manifest case is {actual['case']!r}, expected {case!r}")
    entries = {entry["name"]: entry for entry in actual["files"]}
    if entries.keys() != expected.keys() or len(actual["files"]) != len(expected):
        raise ValueError("unexpected file identities")
    for name, frozen in expected.items():
        path = output / name
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        size = path.stat().st_size
        if (size, digest) != (frozen["bytes"], frozen["sha256"]):
            raise ValueError(f"{name}: expected {frozen['sha256']}, got {digest} ({size} bytes)")
        if (entries[name]["bytes"], entries[name]["sha256"]) != (size, digest):
            raise ValueError(f"{name}: recorded identity does not describe the file")

    expected_layout = {
        "specimen.npy": ((1, 3, 5, 32, 128, 128), "<f4", "ADU", "raw-specimen"),
        "calibration.npy": ((5, 32, 128, 128), "<f4", "ADU", "raw-bead"),
        "truth.npy": ((32, 256, 256), "<f8", "SU", "continuous-source-reference"),
        "conventional.npy": ((32, 256, 256), "<f8", "SU", "same-exposure-conventional"),
    }
    arrays = {}
    for name, (shape, dtype, unit, role) in expected_layout.items():
        array = np.load(output / name, mmap_mode="r", allow_pickle=False)
        if (array.shape, array.dtype.str) != (shape, dtype):
            raise ValueError(f"{name}: expected {shape} with dtype {dtype}")
        if (entries[name]["unit"], entries[name]["role"]) != (unit, role):
            raise ValueError(f"{name}: expected {unit} and role {role}")
        arrays[name] = array
    if (entries["settings.json"]["unit"], entries["settings.json"]["role"]) != (
        None,
        "public-settings",
    ):
        raise ValueError("unexpected settings units or role")

    # The conventional image must reproduce the same 15 background-corrected
    # exposures at the detector-grid nodes, using the fixed 120,000 ADU/SU scale.
    raw = arrays["specimen.npy"][0]
    native_control = (raw.astype(np.float64) - 512).mean(axis=(0, 1)) / 120_000
    native_error = float(np.max(np.abs(arrays["conventional.npy"][:, ::2, ::2] - native_control)))
    if native_error >= 1e-12:
        raise ValueError(f"same-exposure detector-grid error {native_error:.6g} SU")
    return native_error


def main():
    """Check one directory and report the first failed obligation."""
    manifest = Path(__file__).with_name("provenance.json")
    cases = json.loads(manifest.read_text(encoding="utf-8"))["cases"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=cases)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        error = _check(args.case, args.output, cases[args.case]["files"])
    except (OSError, ValueError, KeyError) as failure:
        print(f"{args.case}: {type(failure).__name__}: {failure}", file=sys.stderr)
        return 1
    print(f"{args.case}: five exact files and identities; detector-grid error {error:.6g} SU")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
