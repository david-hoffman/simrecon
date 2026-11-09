"""Check the cell-detail study after both normal reconstructions have closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from zipfile import BadZipFile

import numpy as np

SPECIMEN = "specimen.npy"
CALIBRATION = "calibration.npy"
SETTINGS = "settings.json"
MANIFEST = "manifest.json"
TRUTH = "truth.npy"
CONVENTIONAL = "conventional.npy"
RUNTIME = "runtime.json"
PROGRESS = "progress.jsonl"
IMAGE = "w-0.020.npz"
OBSERVATION_NAME = re.compile(r"w-[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\.npz")
PUBLIC_INPUTS = {"specimen": SPECIMEN, "calibration": CALIBRATION, "settings": SETTINGS}
MANIFEST_FIELDS = {
    SPECIMEN: ("raw-specimen", "ADU"),
    CALIBRATION: ("raw-bead", "ADU"),
    TRUTH: ("continuous-source-reference", "SU"),
    CONVENTIONAL: ("same-exposure-conventional", "SU"),
    SETTINGS: ("public-settings", None),
}
IMAGE_SEMANTICS = "C-scaled-camera-corrected-equalized-phase-reconstruction"

SHAPE = (32, 256, 256)
CAMERA_SHAPE = (32, 128, 128)
WIENER = 0.02
SU_PER_COUNT = 0.000020
BIAS_ADU = 512
ADU_PER_SU = 4 * 30_000
PITCH_NM = 40
MIDPOINT_NM = 560
MIDPOINT_INDEX = SHAPE[-1] // 2 + MIDPOINT_NM // PITCH_NM
TARGETS_NM = (-80, 80)
PAIR_WINDOW_NM = 200
CONTROL_WINDOW_NM = 160
Y_INDEX = 127
Z_INDEX = 20
EPS = float(np.finfo(np.float64).eps)


def require(condition: bool, message: str) -> None:
    """Reject an artifact that violates the study contract."""
    if not condition:
        raise ValueError(message)


def json_object(path: Path) -> dict[str, Any]:
    """Read a receipt or settings file as a JSON object."""
    result = json.loads(path.read_bytes())
    require(isinstance(result, dict), f"{path}: expected a JSON object")
    return result


def file_identity(path: Path) -> dict[str, Any]:
    """Identify a file by its name, byte count, and SHA-256 digest."""
    with path.open("rb") as stream:
        size = path.stat().st_size
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"name": path.name, "bytes": size, "sha256": digest}


def check_array(
    array: np.ndarray, shape: tuple[int, ...], dtype: type | np.dtype, label: str
) -> np.ndarray:
    """Require the expected array representation and finite samples."""
    require(isinstance(array, np.ndarray), f"{label}: expected a NumPy ndarray")
    require(array.shape == shape, f"{label}: expected shape {shape}, got {array.shape}")
    dtype_matches = (
        array.dtype == dtype if isinstance(dtype, np.dtype) else array.dtype.type == dtype
    )
    require(dtype_matches, f"{label}: expected {np.dtype(dtype)}, got {array.dtype}")
    require(bool(np.isfinite(array).all()), f"{label}: nonfinite samples")
    return array


def load_npy(
    directory: Path, name: str, shape: tuple[int, ...], dtype: type | np.dtype
) -> np.ndarray:
    """Open and validate a generated array through a read-only memory map."""
    path = directory / name
    return check_array(np.load(path, mmap_mode="r", allow_pickle=False), shape, dtype, str(path))


def native_axes() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the centered native x, y, and z axes in micrometres."""
    lateral_um = (np.arange(256) - 128) * 0.040
    axial_um = (np.arange(32) - 16) * 0.125
    return lateral_um, lateral_um, axial_um


def read_signed(directory: Path, name: str = IMAGE) -> tuple[np.ndarray, list[float]]:
    """Validate the signed archive and return its native count line and y/z coordinates."""
    path = directory / name
    reference_axes = native_axes()
    with np.load(path, allow_pickle=False) as observation:
        image = check_array(observation["image"], SHAPE, np.float64, f"{path}: image")
        x, y, z = (
            check_array(
                observation[f"{axis}_um"],
                reference.shape,
                np.float64,
                f"{path}: {axis}_um",
            )
            for axis, reference in zip("xyz", reference_axes, strict=True)
        )
    for axis, actual, reference in zip("xyz", (x, y, z), reference_axes, strict=True):
        tolerance_um = 8 * EPS * max(1.0, float(np.max(np.abs(reference))))
        require(
            bool(np.all(np.abs(actual - reference) <= tolerance_um)),
            f"{path}: {axis}_um differs from the centered native grid",
        )
    return image[Z_INDEX, Y_INDEX].copy(), [float(y[Y_INDEX]), float(z[Z_INDEX])]


def truth_difference(
    detail: np.ndarray,
    base: np.ndarray,
    axes: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> dict[str, Any]:
    """Compare both truth volumes against the analytic Gaussian replacement."""
    x, y, z = axes
    dx, dy, dz = x[None, None, :], y[None, :, None] + 0.04, z[:, None, None]
    lateral_y = (dy / 0.0275) ** 2
    axial = ((dz - 0.50) / 0.065) ** 2
    pair = sum(
        16.8 * np.exp(-0.5 * (((dx - center) / 0.0275) ** 2 + lateral_y + axial))
        for center in (0.48, 0.64)
    )
    cos_angle, sin_angle = math.cos(0.31), math.sin(0.31)
    old_x = cos_angle * (dx - 0.55) + sin_angle * dy
    old_y = -sin_angle * (dx - 0.55) + cos_angle * dy
    removed = 1.23 * np.exp(
        -0.5 * ((old_x / 0.078) ** 2 + (old_y / 0.091) ** 2 + ((dz - 0.53) / 0.091) ** 2)
    )
    error = np.abs((detail - base) - (pair - removed))
    # Scale with both source sums and changed terms. The 1 SU floor covers
    # absolute roundoff in the independently evaluated Gaussian tails.
    tolerance = 64 * EPS * np.maximum(1.0, np.abs(detail) + np.abs(base) + pair + removed)
    return {
        "passed": bool(np.all(error <= tolerance)),
        "max_abs_error_su": float(np.max(error)),
        "max_error_over_tolerance": float(np.max(error / tolerance)),
    }


def camera_average(specimen: np.ndarray) -> np.ndarray:
    """Average the bias-corrected detector exposures in simulation source units."""
    return (np.sum(specimen[0], axis=(0, 1), dtype=np.float64) - 15 * BIAS_ADU) / (15 * ADU_PER_SU)


def interpolation_weights(output_index: np.ndarray) -> np.ndarray:
    """Evaluate real periodic cardinal weights on the doubled detector grid."""
    size = CAMERA_SHAPE[-1]
    distance = output_index[..., None] / 2 - np.arange(size)
    phase = (2 * np.pi / size) * distance
    harmonics = np.arange(1, size // 2)
    return (
        1 + 2 * np.cos(phase[..., None] * harmonics).sum(axis=-1) + np.cos(np.pi * distance)
    ) / size


def check_conventional(
    conventional: np.ndarray, specimen: np.ndarray, *, score_row: bool
) -> dict[str, Any]:
    """Check the exposure average on detector nodes and, when scored, the native row."""
    camera = camera_average(specimen)
    tolerance = 32 * EPS * max(1.0, float(np.max(np.abs(camera))))
    error = float(np.max(np.abs(conventional[:, ::2, ::2] - camera)))
    result = {"passed": error <= tolerance, "detector_max_abs_error_su": error}
    if score_row:
        # The score row lies halfway between native detector rows.
        y_weights = interpolation_weights(np.array(Y_INDEX))
        row = y_weights @ camera[Z_INDEX]
        radius = PAIR_WINDOW_NM // PITCH_NM + 1
        x_indices = np.arange(MIDPOINT_INDEX - radius, MIDPOINT_INDEX + radius + 1)
        expected = interpolation_weights(x_indices) @ row
        row_error = float(np.max(np.abs(conventional[Z_INDEX, Y_INDEX, x_indices] - expected)))
        row_tolerance = 128 * EPS * max(1.0, float(np.max(np.abs(camera[Z_INDEX]))))
        result["score_row_max_abs_error_su"] = row_error
        result["passed"] = bool(result["passed"] and row_error <= row_tolerance)
    return result


def score(line: np.ndarray, *, pair: bool, signed_counts: bool = False) -> dict[str, Any]:
    """Score in the line's native intensity units and report samples in source units."""
    offsets_nm = (np.arange(line.size) - MIDPOINT_INDEX) * PITCH_NM
    window_nm = PAIR_WINDOW_NM if pair else CONTROL_WINDOW_NM
    # The fixed positive conversion preserves ordering and dip fractions.
    # 250 counts is the native equivalent of the 0.005 SU peak threshold.
    threshold = 250.0 if signed_counts else 0.005
    su_scale = SU_PER_COUNT if signed_counts else 1.0
    eligible = (
        np.flatnonzero(
            (line[1:-1] > line[:-2])
            & (line[1:-1] >= line[2:])
            & (line[1:-1] >= threshold)
            & (np.abs(offsets_nm[1:-1]) <= window_nm)
        )
        + 1
    )
    ranked = sorted(eligible, key=lambda index: (-line[index], index))

    def sample(index: int | np.integer) -> dict[str, Any]:
        return {
            "x_index": int(index),
            "x_offset_um": int(offsets_nm[index]) / 1000,
            "value_su": float(line[index]) * su_scale,
        }

    peaks = sorted(ranked[:2])
    result: dict[str, Any] = {
        "eligible_peak_count": len(eligible),
        "eligibility_half_width_um": window_nm / 1000,
        "midpoint_value_su": float(line[MIDPOINT_INDEX]) * su_scale,
        "peaks": [sample(index) for index in peaks],
        "spacing_um": None,
        "valley": None,
        "dip_fraction": None,
        "passes_rule": False,
    }
    if len(peaks) == 2:
        left, right = peaks
        valley = left + 1 + int(np.argmin(line[left + 1 : right]))
        spacing_nm = (right - left) * PITCH_NM
        weaker = float(min(line[left], line[right]))
        valley_value = float(line[valley])
        dip = 1.0 - valley_value / weaker
        at_targets = (
            offsets_nm[left] < 0 < offsets_nm[right]
            and abs(offsets_nm[left] - TARGETS_NM[0]) <= 45
            and abs(offsets_nm[right] - TARGETS_NM[1]) <= 45
        )
        result.update(
            spacing_um=int(spacing_nm) / 1000,
            valley=sample(valley),
            dip_fraction=dip,
            passes_rule=bool(
                spacing_nm >= 100 and valley_value <= 0.85 * weaker and (at_targets or not pair)
            ),
        )
    return result


def read_manifest(directory: Path, case: str) -> dict[str, dict[str, Any]]:
    """Verify generated file identities, roles, and units against the manifest."""
    manifest = json_object(directory / MANIFEST)
    require(manifest["case"] == case, f"{directory / MANIFEST}: wrong case")
    entries = {entry["name"]: entry for entry in manifest["files"]}
    require(
        len(entries) == len(manifest["files"]) and entries.keys() == MANIFEST_FIELDS.keys(),
        f"{directory / MANIFEST}: expected one entry for each generated file",
    )
    for name, entry in entries.items():
        actual = file_identity(directory / name)
        require(
            all(entry[key] == value for key, value in actual.items()),
            f"{directory / name}: byte count or SHA-256 differs from manifest",
        )
        require(
            (entry["role"], entry["unit"]) == MANIFEST_FIELDS[name],
            f"{directory / MANIFEST}: unexpected role or unit for {name}",
        )
    return entries


def read_settings(directory: Path, case: str, entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Verify acquisition settings and bind specimen and calibration identities."""
    settings = json_object(directory / SETTINGS)
    for name, label, expected_id in (
        (SPECIMEN, settings["specimen_identity"], f"{case}-noisy-specimen"),
        (CALIBRATION, settings["calibration"]["identity"], "full-noisy-bead"),
    ):
        entry = entries[name]
        expected_file = {key: entry[key] for key in ("name", "bytes", "role", "sha256")}
        require(
            label["id"] == expected_id
            and label["intensity_unit"] == "ADU"
            and label["files"] == [expected_file],
            f"{directory / SETTINGS}: wrong identity binding for {name}",
        )
    acquisition = settings["acquisition"]
    expected = {
        "background": BIAS_ADU,
        "dxy_um": 0.080,
        "dz_um": 0.125,
        "lateral_zoom": 2,
        "axial_zoom": 1,
        "norders": 3,
        "storage_order": "direction-major",
    }
    require(
        all(acquisition[key] == value for key, value in expected.items()),
        f"{directory / SETTINGS}: unexpected acquisition geometry or camera bias",
    )
    filtering = settings["filtering"]
    require(
        filtering["wiener"] == WIENER and filtering["wiener_increment"] == 0,
        f"{directory / SETTINGS}: expected Wiener 0.020 and zero increment",
    )
    return settings


def check_closed(directory: Path, case: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Require completed public reconstruction before opening any study arrays."""
    progress = directory / PROGRESS
    records = [json.loads(line) for line in progress.read_text().splitlines()]
    require(
        bool(records)
        and all(isinstance(record, dict) for record in records)
        and records[-1].get("event") == "complete"
        and records[-1]["case"] == case
        and any(
            record.get("event") == "public-complete" and record.get("case") == case
            for record in records[:-1]
        ),
        f"{progress}: run is incomplete",
    )
    final = records[-1]
    completed = final["observations"]
    require(
        isinstance(completed, list) and WIENER in completed,
        f"{progress}: no completed Wiener 0.020 observation",
    )
    if case == "cell-detail":
        require(
            completed == [WIENER] and final["scored"] == [],
            f"{progress}: cell-detail requires a normal run",
        )
    return file_identity(progress), final


def matches_completed_sweep(completed: list[float], observations: dict[str, Any]) -> bool:
    """Match distinct completed Wiener settings to the runtime sweep metadata."""
    if len(completed) != len(observations) or len(completed) < 2:
        return False
    resolved = [entry["resolved_settings"]["wiener"] for entry in observations.values()]
    if not all(
        type(value) is int or (type(value) is float and math.isfinite(value))
        for value in (*completed, *resolved)
    ):
        return False
    values = set(completed)
    return len(values) == len(completed) and values == set(resolved)


def _bound_observation(path: Path, observation: dict[str, Any]) -> dict[str, Any]:
    identity = file_identity(path)
    require(
        observation["sha256"] == identity["sha256"],
        f"{path}: SHA-256 differs from runtime receipt",
    )
    return identity


def _legacy_sweep_identity(
    directory: Path, completion: dict[str, Any], observations: dict[str, Any]
) -> dict[str, Any]:
    scored = completion.get("scored")
    completed = set(completion["observations"])
    require(
        isinstance(scored, list)
        and all(type(value) in (int, float) and value in completed for value in scored)
        and len(set(scored)) == len(scored),
        f"{directory / PROGRESS}: scored settings must be a unique subset of completed settings",
    )
    directory = directory.resolve()
    identities = {}
    file_keys: set[tuple[int, int]] = set()
    for name, observation in observations.items():
        require(
            OBSERVATION_NAME.fullmatch(name) is not None,
            f"{directory / RUNTIME}: invalid observation archive name {name!r}",
        )
        path = directory / name
        require(
            path.resolve().parent == directory,
            f"{path}: observation archive escapes the case directory",
        )
        require(not path.is_symlink(), f"{path}: observation archive must not be a symlink")
        require(path.is_file(), f"{path}: observation archive is missing or not a regular file")
        metadata = path.stat()
        file_key = (metadata.st_dev, metadata.st_ino)
        require(file_key not in file_keys, f"{path}: observation archives must be distinct files")
        file_keys.add(file_key)
        require("sha256" in observation, f"{path}: missing runtime SHA-256")
        identities[name] = _bound_observation(path, observation)
        if name != IMAGE:
            read_signed(directory, name)
    return identities[IMAGE]


def read_runtime(
    directory: Path, case: str, entries: dict[str, dict[str, Any]], completion: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Bind the public input roles and the signed Wiener 0.020 archive."""
    path = directory / RUNTIME
    runtime = json_object(path)
    require(runtime["case"] == case, f"{path}: wrong case")
    require(
        runtime["image_axes"] == "zyx"
        and runtime["image_unit"] == "ADU"
        and runtime["coordinate_unit"] == "um"
        and runtime["image_semantics"] == IMAGE_SEMANTICS,
        f"{path}: expected a signed ZYX image in ADU with coordinates in um",
    )
    require(
        runtime["public_files"]
        == {role: entries[name]["sha256"] for role, name in PUBLIC_INPUTS.items()},
        f"{path}: public input SHA-256 identities differ from generated case",
    )
    observations = runtime["observations"]
    if case == "cell-detail":
        require(
            isinstance(observations, dict) and observations.keys() == {IMAGE},
            f"{path}: cell-detail requires exactly one runtime observation, {IMAGE}",
        )
    observation = observations[IMAGE]
    resolved = observation["resolved_settings"]
    require(
        resolved["wiener"] == WIENER and resolved["effective_wiener"] == [WIENER],
        f"{path}: expected effective and resolved Wiener 0.020",
    )
    if "workflow_effective_wiener" in runtime:
        image_identity = _bound_observation(directory / IMAGE, observation)
        require(
            runtime["workflow_effective_wiener"] == [WIENER],
            f"{path}: workflow_effective_wiener must be [0.02]",
        )
    else:
        require(
            case == "cell" and matches_completed_sweep(completion["observations"], observations),
            f"{path}: missing workflow_effective_wiener outside a completed cell sweep",
        )
        image_identity = _legacy_sweep_identity(directory, completion, observations)
    return {
        "runtime": file_identity(path),
        "image": image_identity,
    }


def read_camera(directory: Path) -> np.ndarray:
    """Validate the raw camera files and return the specimen exposures."""
    dtype = np.dtype("<f4")
    specimen = load_npy(directory, SPECIMEN, (1, 3, 5, *CAMERA_SHAPE), dtype)
    calibration = load_npy(directory, CALIBRATION, (5, *CAMERA_SHAPE), dtype)
    for name, counts in ((SPECIMEN, specimen), (CALIBRATION, calibration)):
        require(
            bool(np.all(counts == np.trunc(counts))),
            f"{directory / name}: fractional ADU",
        )
    return specimen


def study_receipt(
    detail_input: Path, detail_output: Path, base_input: Path, base_output: Path
) -> dict[str, Any]:
    """Return the same verified receipt as the command, including adverse verdicts."""
    detail_progress, detail_completion = check_closed(detail_output, "cell-detail")
    base_progress, base_completion = check_closed(base_output, "cell")
    detail_entries = read_manifest(detail_input, "cell-detail")
    base_entries = read_manifest(base_input, "cell")
    detail_run = read_runtime(detail_output, "cell-detail", detail_entries, detail_completion)
    base_run = read_runtime(base_output, "cell", base_entries, base_completion)

    require(
        detail_entries[CALIBRATION]["sha256"] == base_entries[CALIBRATION]["sha256"],
        "cell-detail and cell calibration SHA-256 identities differ",
    )
    detail_settings = read_settings(detail_input, "cell-detail", detail_entries)
    base_settings = read_settings(base_input, "cell", base_entries)
    for key in (
        "acquisition",
        "optics",
        "carrier",
        "calibration",
        "filtering",
        "plane_policy",
    ):
        require(
            detail_settings[key] == base_settings[key],
            f"cell-detail and cell {key} differ",
        )
    detail_truth = load_npy(detail_input, TRUTH, SHAPE, np.float64)
    base_truth = load_npy(base_input, TRUTH, SHAPE, np.float64)
    detail_conventional = load_npy(detail_input, CONVENTIONAL, SHAPE, np.float64)
    base_conventional = load_npy(base_input, CONVENTIONAL, SHAPE, np.float64)
    detail_line, detail_yz = read_signed(detail_output)
    base_line, base_yz = read_signed(base_output)
    checks = {
        "truth_difference": truth_difference(detail_truth, base_truth, native_axes()),
        "detail_same_exposure": check_conventional(
            detail_conventional, read_camera(detail_input), score_row=True
        ),
        "base_same_exposure": check_conventional(
            base_conventional, read_camera(base_input), score_row=False
        ),
    }
    chains = {
        case: {
            "manifest": file_identity(directory / MANIFEST),
            "public_inputs": {name: entries[name]["sha256"] for name in PUBLIC_INPUTS.values()},
            "runtime": run["runtime"],
            "progress": progress,
        }
        for case, directory, entries, run, progress in (
            ("cell-detail", detail_input, detail_entries, detail_run, detail_progress),
            ("cell", base_input, base_entries, base_run, base_progress),
        )
    }

    row = (Z_INDEX, Y_INDEX)
    arms = {}
    for name, line, via, identity in (
        ("truth", detail_truth[row], "manifest", detail_entries[TRUTH]),
        ("same_exposure", detail_conventional[row], "manifest", detail_entries[CONVENTIONAL]),
        ("detail_sim", detail_line, "runtime", detail_run["image"]),
        ("base_sim", base_line, "runtime", base_run["image"]),
    ):
        pair = name != "base_sim"
        expected = name in ("truth", "detail_sim")
        metrics = score(line, pair=pair, signed_counts=via == "runtime")
        arms[name] = {
            "passed": metrics["passes_rule"] == expected,
            "expected_passes_rule": expected,
            "rule": "pair_resolution" if pair else "false_split",
            "identity": {"case": "cell-detail" if pair else "cell", "via": via, **identity},
            **metrics,
        }
    passed = all(check["passed"] for check in checks.values()) and all(
        arm["passed"] for arm in arms.values()
    )
    return {
        "status": "pass" if passed else "fail",
        "native_line": {
            "axis": "x",
            "shape_zyx": SHAPE,
            "x_midpoint_um": MIDPOINT_NM / 1000,
            "x_pitch_um": PITCH_NM / 1000,
            "y_index": Y_INDEX,
            "z_index": Z_INDEX,
            "detail_yz_um": detail_yz,
            "base_yz_um": base_yz,
            "value_unit": "SU",
            "su_per_signed_count": SU_PER_COUNT,
        },
        "checks": checks,
        "cases": chains,
        "arms": arms,
    }


def main() -> int:
    """Print one JSON receipt and distinguish adverse science from invalid artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("DETAIL_INPUT", "DETAIL_OUTPUT", "BASE_INPUT", "BASE_OUTPUT"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        receipt = study_receipt(
            args.DETAIL_INPUT, args.DETAIL_OUTPUT, args.BASE_INPUT, args.BASE_OUTPUT
        )
        print(json.dumps(receipt, separators=(",", ":"), allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError, BadZipFile, EOFError) as error:
        print(
            json.dumps(
                {
                    "status": "invalid_artifacts",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
        )
        return 2
    return int(receipt["status"] != "pass")


if __name__ == "__main__":
    sys.exit(main())
