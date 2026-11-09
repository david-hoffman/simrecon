"""Write one frozen synthetic input case to a new directory."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from optics import BASE, Pupil, camera, conventional
from render import render
from scenes import cell_truth, sphere_truth, structured_truth

# Case values bind each public specimen identity and camera draw.
CASES = {
    "clean": ("full-noiseless-specimen", None),
    "noisy": ("full-noisy-specimen", 21103431),
    "beads": ("beads-noisy-specimen", 83071341),
    "cell": ("cell-noisy-specimen", 83071342),
    "cell-detail": ("cell-detail-noisy-specimen", 83071342),
}
FILES = {
    "specimen.npy": ("raw-specimen", "ADU"),
    "calibration.npy": ("raw-bead", "ADU"),
    "settings.json": ("public-settings", None),
    "truth.npy": ("continuous-source-reference", "SU"),
    "conventional.npy": ("same-exposure-conventional", "SU"),
}


def _entry(path, role):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": digest, "role": role}


def _write_array(path, array):
    with path.open("xb") as stream:
        np.save(stream, array, allow_pickle=False)


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _settings(output, specimen_id, calibration_id):
    template = Path(__file__).with_name("settings-template.json")
    settings = json.loads(template.read_text(encoding="utf-8"))
    settings["specimen_identity"] = {
        "id": specimen_id,
        "intensity_unit": "ADU",
        "files": [_entry(output / "specimen.npy", "raw-specimen")],
    }
    settings["calibration"]["identity"] = {
        "id": calibration_id,
        "intensity_unit": "ADU",
        "files": [_entry(output / "calibration.npy", "raw-bead")],
    }
    return settings


def _truth(case):
    if case == "beads":
        return sphere_truth(96)
    if case in ("cell", "cell-detail"):
        return cell_truth(detail=case == "cell-detail")
    return structured_truth()


def _generate(case, output):
    specimen_id, seed = CASES[case]
    calibration_id = "full-noiseless-bead" if seed is None else "full-noisy-bead"
    stage = "create output directory"
    try:
        output.mkdir()
        stage = "pupil"
        pupil = Pupil(*BASE[1:4])
        stage = "specimen"
        raw = camera(render(case, pupil), seed)
        # Preserve the public specimen time axis and native D, P, Z, Y, X order.
        _write_array(output / "specimen.npy", raw[None])
        stage = "same-exposure conventional"
        _write_array(output / "conventional.npy", conventional(raw))
        del raw
        stage = "raw calibration"
        calibration_seed = None if seed is None else 49019457
        bead = camera(render("calibration", pupil), calibration_seed)
        # Calibration has one direction. Its public array starts at phase.
        _write_array(output / "calibration.npy", bead[0])
        stage = "truth"
        _write_array(output / "truth.npy", _truth(case))
        stage = "settings"
        _write_json(output / "settings.json", _settings(output, specimen_id, calibration_id))
        stage = "write identities"
        _write_json(
            output / "manifest.json",
            {
                "case": case,
                "files": [
                    {**_entry(output / name, role), "unit": unit}
                    for name, (role, unit) in FILES.items()
                ],
            },
        )
    except Exception as error:
        print(f"{case} failed at {stage}: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


def main():
    """Parse the case and fresh output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("output", type=Path, metavar="NEW_OUTPUT_DIR")
    args = parser.parse_args()
    return _generate(args.case, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
