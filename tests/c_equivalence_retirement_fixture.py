"""CE01 public oracle and isolated public caller; no implementation inspection."""

from __future__ import annotations

import importlib
import importlib.machinery
import json
import re
import struct
import sys
import sysconfig
from pathlib import Path, PurePosixPath
from typing import Any

RETAINED_NAMES = (
    "DataBlock",
    "DatasetInfo",
    "ImagejSeries",
    "ImagejWriteReport",
    "RawAcquisition",
    "SimreconError",
    "WriteReport",
    "declare_acquisition",
    "export_imagej",
    "harmonize",
    "inspect",
    "read",
    "write",
)

RETIRED_NAMES = (
    "BeadPeak",
    "CarrierCandidate",
    "CarrierSelection",
    "DriftCorrection",
    "EmpiricalFrequencySamples",
    "EmpiricalVolumeResponse",
    "FiniteBeadCalibration",
    "IlluminationEstimate",
    "LinearResponseCorrection",
    "ObservableVolumePhaseEstimate",
    "Otf2D",
    "Otf3D",
    "PhaseComponents",
    "PointBeadCalibration",
    "Reconstruction2D",
    "Reconstruction3D",
    "ScalarCameraEstimate",
    "SharedNodeVolumeTransfer",
    "TranslationEstimate",
    "TrilinearVolumeTransfer",
    "VolumeCarrierCandidate",
    "VolumeCarrierSelection",
    "VolumeOrderGainEstimate",
    "VolumeOrderOtf",
    "VolumePhaseCarrierSelection",
    "VolumePhaseComponents",
    "VolumePhaseEstimate",
    "VolumeTranslationEstimate",
    "adapt_empirical_volume_response",
    "adapt_empirical_volume_response_shared_nodes",
    "adapt_empirical_volume_response_trilinear",
    "calibrate_raw_finite_bead",
    "calibrate_raw_point_bead",
    "correct_integer_drift",
    "correct_linear_response",
    "estimate_illumination",
    "estimate_observable_volume_phases",
    "estimate_scalar_camera",
    "estimate_translation",
    "estimate_volume_order_gain",
    "estimate_volume_phases",
    "estimate_volume_translation",
    "locate_bead_peak",
    "prepare_empirical_volume_response",
    "prepare_otf",
    "prepare_volume_order_otfs",
    "prepare_volume_otf",
    "reconstruct",
    "reconstruct_volume",
    "sample_empirical_volume_transfer",
    "scan_carriers",
    "scan_volume_carriers",
    "scan_volume_phase_carriers",
    "select_carrier",
    "select_volume_carrier",
    "select_volume_phase_carrier",
    "separate_phases",
    "separate_volume_phases",
)

RETIRED_MODULES = (
    "simrecon._array_validation",
    "simrecon._bead_peak",
    "simrecon._carrier",
    "simrecon._carrier_selection",
    "simrecon._drift",
    "simrecon._empirical_frequency",
    "simrecon._empirical_response",
    "simrecon._empirical_shared_nodes",
    "simrecon._empirical_transfer",
    "simrecon._empirical_trilinear",
    "simrecon._finite_bead_calibration",
    "simrecon._fourier_block_phase",
    "simrecon._illumination",
    "simrecon._linear_response",
    "simrecon._observable_volume_phase_estimation",
    "simrecon._otf",
    "simrecon._phase",
    "simrecon._phase_carrier_scan",
    "simrecon._phase_carrier_selection",
    "simrecon._point_bead_calibration",
    "simrecon._reconstruction",
    "simrecon._scalar_camera_calibration",
    "simrecon._translation",
    "simrecon._volume_carrier_diagnostics",
    "simrecon._volume_order_otf",
    "simrecon._volume_otf",
    "simrecon._volume_phase",
    "simrecon._volume_phase_estimation",
    "simrecon._volume_translation_estimation",
    "simrecon.volume_carrier_selection",
    "simrecon.volume_order_gain",
    "simrecon.volume_reconstruction",
)

RETIRED_SCRIPTS = (
    "scripts/full_noisy_study.py",
    "scripts/generate_reference_fixtures.py",
    "scripts/image_only_bead_calibration.py",
    "scripts/image_only_calibration_pilot.py",
    "scripts/image_only_specimen_fit.py",
    "scripts/simulation_camera.py",
    "scripts/simulation_inverse_operator.py",
    "scripts/simulation_optics.py",
    "scripts/simulation_sources.py",
)


def observe_boundary() -> dict[str, Any]:
    """Import actual public targets; a broken dependency is never absence proof."""
    sr = importlib.import_module("simrecon")
    assert sr.__file__ is not None
    missing = [name for name in RETAINED_NAMES if not hasattr(sr, name)]
    present = [name for name in RETIRED_NAMES if hasattr(sr, name)]
    importable = []
    for name in RETIRED_MODULES:
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as failure:
            if failure.name != name:
                raise
        else:
            importable.append(name)
    return {
        "origin": str(Path(sr.__file__).resolve()),
        "missing_neutral": missing,
        "retired_attributes": present,
        "importable_retired_modules": importable,
    }


def neutral_io(directory: Path) -> dict[str, Any]:
    """One real file composition; expected values are independent byte labels."""
    import numpy as np
    import tifffile

    import simrecon as sr

    directory.mkdir()
    source = directory / "input.priism"
    pixels = np.array([[[0, 32768, 65535], [7, 23, 60000]]], dtype="<u2")
    header = bytearray(1024)
    for offset, value in (
        (0, 3),
        (4, 2),
        (8, 1),
        (12, 6),
        (28, 3),
        (32, 2),
        (36, 1),
        (64, 1),
        (68, 2),
        (72, 3),
        (92, 0),
    ):
        struct.pack_into("<i", header, offset, value)
    for offset, value in ((40, 0.25), (44, 0.5), (48, 1.0)):
        struct.pack_into("<f", header, offset, value)
    for offset, value in ((96, -16224), (180, 1), (182, 0), (196, 1)):
        struct.pack_into("<h", header, offset, value)
    original = bytes(header) + pixels.tobytes()
    source.write_bytes(original)
    config = {
        "version": 1,
        "data_kind": "spatial_image",
        "plane_axes": [],
        "plane_shape": [],
        "spatial_fields": "direct_um",
        "extended_header": "none",
    }
    info = sr.harmonize(sr.inspect(source), config=config)
    assert isinstance(info, sr.DatasetInfo)
    block = sr.read(info, plane_start=0, plane_stop=1)
    assert isinstance(block, sr.DataBlock)
    assert block.data.tobytes() == pixels.tobytes()
    converted = sr.write(directory / "converted.mrc", info)
    assert isinstance(converted, sr.WriteReport) and converted.planes_written == 1
    converted_bytes = converted.destination.read_bytes()
    payload_start = 1024 + struct.unpack_from("<i", converted_bytes, 92)[0]
    assert converted_bytes[payload_start:] == pixels.tobytes()
    raw = sr.declare_acquisition(
        block.data[0],
        config={"version": 1, "acquisition_kind": "detection_psf", "axes": ["y", "x"]},
    )
    assert isinstance(raw, sr.RawAcquisition)
    assert raw.data.tobytes() == pixels.tobytes()
    assert raw.data.flags.owndata and not np.shares_memory(raw.data, block.data)
    report = sr.export_imagej(directory / "copy.ome.tif", info)
    assert isinstance(report, sr.ImagejWriteReport)
    assert report.series_count == report.planes_written == 1
    assert isinstance(report.series[0], sr.ImagejSeries)
    assert report.series[0].shape == (1, 1, 1, 2, 3)
    with tifffile.TiffFile(report.destination) as reader:
        assert reader.pages[0].asarray().tobytes() == pixels.tobytes()
    assert source.read_bytes() == original
    (directory / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return {"source": str(source), "planes": 1, "samples": 6}


def retired_members(members: list[str]) -> list[str]:
    """Recognize retired code at wheel import/script roots, preserving evidence."""
    modules = {tuple(name.split(".")) for name in RETIRED_MODULES}
    scripts = {PurePosixPath(name).stem for name in RETIRED_SCRIPTS}
    suffixes = (
        *importlib.machinery.SOURCE_SUFFIXES,
        *importlib.machinery.BYTECODE_SUFFIXES,
        *importlib.machinery.EXTENSION_SUFFIXES,
        ".pyd",
    )

    def code_file(filename: str, leaf: str) -> bool:
        # Public loaders define native names; retain other required platforms'
        # extension tags too. An extra text suffix does not become code.
        return (
            any(filename == leaf + suffix for suffix in suffixes)
            or re.fullmatch(
                re.escape(leaf) + r"\.(?:cpython-[^.]+|cp[0-9]+-[^.]+|abi3)\.(?:so|pyd)",
                filename,
            )
            is not None
        )

    found = []
    for name in members:
        parts = PurePosixPath(name).parts
        if not parts or parts[0].endswith(".dist-info"):
            continue
        script_root = False
        if parts[0].endswith(".data"):
            if len(parts) < 3 or parts[1] not in {"purelib", "platlib", "scripts"}:
                continue
            script_root = parts[1] == "scripts"
            parts = parts[2:]
        if not parts:
            continue
        filename = parts[-1]
        if script_root:
            if any(filename == leaf or code_file(filename, leaf) for leaf in scripts):
                found.append(name)
            continue
        module_member = any(
            (parts[: len(module)] == module and (len(parts) > len(module) or name.endswith("/")))
            or (parts[:-1] == module[:-1] and code_file(filename, module[-1]))
            or (
                parts[:-2] == module[:-1]
                and len(parts) >= 2
                and parts[-2] == "__pycache__"
                and filename.startswith(module[-1] + ".")
                and filename.endswith(".pyc")
            )
            for module in modules
        )
        script_member = (len(parts) == 1 or parts[:-1] == ("scripts",)) and any(
            code_file(filename, leaf) for leaf in scripts
        )
        if module_member or script_member:
            found.append(name)
    return sorted(found)


if __name__ == "__main__":
    # The copied probe lives outside the checkout. Restrict package resolution to
    # this wheel installation plus the interpreter's standard/dependency paths.
    installed = Path(sys.argv[1]).resolve()
    checkout = Path(sys.argv[2]).resolve()
    sys.path[:] = [
        str(installed),
        sysconfig.get_path("purelib"),
        *[
            entry
            for entry in sys.path
            if entry and not Path(entry).resolve().is_relative_to(checkout)
        ],
    ]
    importlib.invalidate_caches()
    if sys.argv[3] == "--cli":
        from importlib.metadata import distribution

        entries = [
            entry
            for entry in distribution("simrecon").entry_points
            if entry.group == "console_scripts" and entry.name == "simrecon"
        ]
        assert len(entries) == 1
        sys.argv = ["simrecon", *sys.argv[4:]]
        raise SystemExit(entries[0].load()())
    observed = observe_boundary()
    assert Path(observed["origin"]).is_relative_to(installed), observed["origin"]
    observed["neutral_io"] = neutral_io(Path(sys.argv[3]))
    print(json.dumps(observed, sort_keys=True))
