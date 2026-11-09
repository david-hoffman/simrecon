"""CE01 neutral preservation from BASELINE-COMPATIBILITY-01.

Run through scripts/source_free_check.py. Retained expectations use the public
conversion, acquisition and ImageJ contracts and independently encoded bytes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest
import tifffile

import simrecon as sr
from shared_node_baseline_fixture import priism_file

ROOT = Path(__file__).resolve().parents[1]


def error(code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(sr.SimreconError) as caught:
        operation()
    assert caught.value.code == code, f"expected={code}; actual={caught.value.code}"


def owned(array: np.ndarray[Any, Any], dtype: str, *inputs: np.ndarray[Any, Any]) -> None:
    assert type(array) is np.ndarray
    assert array.dtype == np.dtype(dtype)
    assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
    for source in inputs:
        assert not np.shares_memory(array, source)


def test_raw_named_axes_preserve_nan_payloads_and_metadata() -> None:
    words = np.array(
        [0x80000000, 0x7F800000, 0xFF800000, 0x7FC12345, 0x3F800000, 0x00000000], dtype=">u4"
    )
    data = words.view(">f4").reshape(2, 1, 1, 3)
    data.flags.writeable = False
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "detection_psf",
        "axes": ["z", "channel", "y", "x"],
        "sampling_um": {"x": 0.25, "y": 0.5},
        "intensity_unit": "  ",
    }
    metadata: dict[str, Any] = {"opaque": [b"\x00\xff", (float("inf"), "label")], "unknown": None}
    result = sr.declare_acquisition(data, config=config, original_metadata=metadata)
    assert result.axes == ("channel", "z", "y", "x")
    assert result.source_axes == ("z", "channel", "y", "x")
    assert result.data.dtype.str == ">f4"
    assert result.data.tobytes() == data.transpose(1, 0, 2, 3).tobytes()
    assert result.sampling_um == {"x": 0.25, "y": 0.5, "z": None}
    assert result.intensity_unit == "  " and result.nominal_phases_rad is None
    owned(result.data, ">f4", data)
    metadata["opaque"].append("later")
    config["sampling_um"]["x"] = 9
    assert len(result.original_metadata["opaque"]) == 2
    assert result.original_config["sampling_um"]["x"] == 0.25
    assert not data.flags.writeable and data.tobytes() == words.tobytes()


def test_raw_wider_padding_bytes_survive_coordinate_reorder() -> None:
    data = np.arange(12, dtype=np.longdouble).reshape(2, 2, 1, 3)[:, ::-1]
    result = sr.declare_acquisition(
        data,
        config={
            "version": 1,
            "acquisition_kind": "detection_psf",
            "axes": ["z", "channel", "y", "x"],
        },
    )
    assert result.data.dtype == data.dtype
    for channel in range(2):
        for z in range(2):
            assert result.data[channel, z].tobytes() == data[z, channel].tobytes()


def test_raw_overrides_group_commands_and_schema() -> None:
    data = np.arange(12, dtype=np.int16).reshape(3, 2, 1, 2)
    commands = [[float(10 * p + o) for o in range(2)] for p in range(3)]
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "specimen_sim",
        "axes": ["phase", "orientation", "y", "x"],
        "sampling_um": {"x": -1},
        "nominal_phases_rad": commands,
        "intensity_unit": "counts",
        "overrides": {
            "sampling_um": {"x": 0.25},
            "intensity_unit": "counts",
            "calibration_id": None,
        },
    }
    result = sr.declare_acquisition(data, config=config)
    assert result.axes == ("orientation", "phase", "y", "x")
    np.testing.assert_array_equal(result.data, data.transpose(1, 0, 2, 3))
    np.testing.assert_array_equal(result.nominal_phases_rad, np.array(commands).T)
    assert result.nominal_phase_axes == ("orientation", "phase")
    assert result.sampling_um == {"x": 0.25, "y": None, "z": None}
    initial = sorted(key for key in config if key not in ("version", "overrides"))
    overridden = sorted(config["overrides"])
    assert [p["field"] for p in result.provenance] == initial + overridden
    assert [p["source"] for p in result.provenance] == ["config"] * len(initial) + [
        "override"
    ] * len(overridden)
    for change, code in (
        ({"version": True}, "invalid_acquisition_config"),
        ({"extra": 1}, "invalid_acquisition_config"),
        ({"axes": ["phase", "phase", "y", "x"]}, "invalid_acquisition_axes"),
        ({"acquisition_kind": "detection_psf"}, "invalid_acquisition_kind"),
        ({"nominal_phases_rad": [0, 1, 2]}, "invalid_acquisition_phase_commands"),
        ({"wavelengths_nm": {"00": 488}}, "invalid_acquisition_wavelengths"),
        ({"overrides": {"axes": ["y", "x"]}}, "invalid_acquisition_config"),
    ):
        error(
            code,
            lambda change=change: sr.declare_acquisition(data, config=config | cast(Any, change)),
        )
    for bad in ({"value": np.array([1])}, {"value": object()}):
        error(
            "invalid_acquisition_metadata",
            lambda bad=bad: sr.declare_acquisition(
                data, config=config, original_metadata=cast(Any, bad)
            ),
        )
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic
    error(
        "invalid_acquisition_metadata",
        lambda: sr.declare_acquisition(data, config=config, original_metadata=cyclic),
    )


def file_config(
    *, axes: list[str] | None = None, shape: list[int] | None = None, extension: bool = False
) -> dict[str, Any]:
    return {
        "version": 1,
        "data_kind": "spatial_image",
        "plane_axes": [] if axes is None else axes,
        "plane_shape": [] if shape is None else shape,
        "spatial_fields": "direct_um",
        "extended_header": "opaque" if extension else "none",
        "overrides": {},
    }


@pytest.mark.parametrize("dtype", ["<u2", ">u2", "<f4", ">f4"])
def test_real_file_bigtiff_scalar_bits_and_setting_mapping(tmp_path: Path, dtype: str) -> None:
    import base64
    import hashlib
    import xml.etree.ElementTree as ET

    source = tmp_path / "source.dv"
    if np.dtype(dtype).kind == "u":
        pixels = (np.arange(12, dtype=np.uint16) + 40000).astype(dtype).reshape(2, 2, 3)
    else:
        endian = dtype[0]
        words = np.array(
            [
                0x80000000,
                0x7F800000,
                0xFF800000,
                0x7FC12345,
                0,
                0x3F800000,
                0x7FA12345,
                0xFFC54321,
                0x40000000,
                0x40400000,
                0x40800000,
                0x40A00000,
            ],
            dtype=endian + "u4",
        )
        pixels = words.view(dtype).reshape(2, 2, 3)
    extension = b"opaque\x00\xff" * 7
    original = priism_file(source, pixels, extension=extension)
    config = file_config(axes=["phase", "orientation"], shape=[2, 1], extension=True)
    info = sr.harmonize(sr.inspect(source), config=config)
    destination = tmp_path / "copy.ome.tif"
    report = sr.export_imagej(destination, info, block_planes=1)
    assert destination.read_bytes()[:8] == b"II+\x00\x08\x00\x00\x00"
    assert report.series_count == 2 and report.planes_written == 2
    assert [item.name for item in report.series] == [
        "orientation=0; phase=0",
        "orientation=0; phase=1",
    ]
    assert [item.shape for item in report.series] == [(1, 1, 1, 2, 3)] * 2
    assert all(item.orientation_index == 0 for item in report.series)
    namespace = {"o": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
    with tifffile.TiffFile(destination) as reader:
        assert reader.is_bigtiff and reader.byteorder == "<" and len(reader.pages) == 2
        for page, expected in zip(reader.pages, pixels, strict=True):
            assert int(page.compression) == 1
            kind = "u4" if expected.dtype.kind == "f" else "u2"
            words = expected.view(expected.dtype.byteorder + kind)
            native_words = words.astype(kind)
            assert page.asarray().tobytes() == native_words.tobytes()
        xml = ET.fromstring(cast(Any, reader.pages[0]).description)
        images = xml.findall("o:Image", namespace)
        assert len(images) == 2
        for index, image in enumerate(images):
            assert image.attrib["Name"] == report.series[index].name
            node = image.find("o:Pixels", namespace)
            assert node is not None
            assert node.attrib["DimensionOrder"] == "XYCZT"
            assert [node.attrib["Size" + axis] for axis in "XYZCT"] == ["3", "2", "1", "1", "1"]
            assert (
                float(node.attrib["PhysicalSizeX"]) == 0.25
                and float(node.attrib["PhysicalSizeY"]) == 0.5
            )
            assert "PhysicalSizeZ" not in node.attrib
            mappings = node.findall("o:TiffData", namespace)
            assert len(mappings) == 1 and int(mappings[0].attrib["IFD"]) == index
        values = xml.findall(".//o:MapAnnotation/o:Value/o:M", namespace)
        metadata = [
            json.loads(item.text or "")
            for item in values
            if item.attrib.get("K") == "metadata_json"
        ]
        assert metadata and all(item == metadata[0] for item in metadata)
        document = metadata[0]
        assert document["schema"] == "org.simrecon.imagej-copy"
        assert document["logical_axes"] == ["orientation", "phase", "y", "x"]
        assert document["logical_shape"] == [1, 2, 2, 3]
        assert document["source_identity"]["source_name"] == source.name
        assert str(tmp_path) not in json.dumps(document)
        assert base64.b64decode(document["original_header_base64"]) == original[:1024]
        assert document["original_extension"] == {
            "schema": "opaque",
            "bytes": len(extension),
            "sha256": hashlib.sha256(extension).hexdigest(),
            "content_retained": False,
        }
        assert document["series_layout"]["orientation_present"] is True
        assert document["series_layout"]["z_present"] is False
    assert source.read_bytes() == original


def test_file_precreation_rejections_and_genuine_os_failures(tmp_path: Path) -> None:
    source = tmp_path / "input.dv"
    original = priism_file(source, np.array([[[50000, 3]]], dtype=">u2"))
    inspected = sr.inspect(source)
    info = sr.harmonize(inspected, config=file_config())
    destination = tmp_path / "new.tif"
    error("config_required", lambda: sr.export_imagej(destination, inspected))
    assert not destination.exists()
    for block in (0, -1, True, 1.5):
        error(
            "invalid_block_size",
            lambda block=block: sr.export_imagej(destination, info, block_planes=cast(Any, block)),
        )
        assert not destination.exists()
    for sampling in (1.0e-100, 1.0e100):
        changed = sr.harmonize(
            inspected, config=file_config() | {"overrides": {"sampling_um": {"x": sampling}}}
        )
        error(
            "imagej_unrepresentable",
            lambda changed=changed: sr.export_imagej(destination, cast(Any, changed)),
        )
        assert not destination.exists()
    destination.write_bytes(b"existing marker")
    with pytest.raises(FileExistsError):
        sr.export_imagej(destination, info)
    assert destination.read_bytes() == b"existing marker"
    with pytest.raises(FileExistsError):
        sr.export_imagej(source, info)
    assert source.read_bytes() == original
    with pytest.raises(FileNotFoundError):
        sr.export_imagej(tmp_path / "missing-parent" / "new.tif", info)
    assert source.read_bytes() == original
    alias = tmp_path / "source-alias.tif"
    alias.symlink_to(source)
    with pytest.raises(FileExistsError):
        sr.export_imagej(alias, info)
    assert source.read_bytes() == original
    # A genuine header edit after inspection must reject without creating output.
    altered = bytearray(original)
    altered[300] ^= 1
    source.write_bytes(altered)
    error("source_changed", lambda: sr.export_imagej(tmp_path / "changed.tif", info))
    assert not (tmp_path / "changed.tif").exists() and source.read_bytes() == altered


def test_later_payload_io_failure_preserves_owned_source(tmp_path: Path) -> None:
    import contextlib
    import os
    import signal

    if os.name != "posix":
        pytest.fail("incomplete_io_fixture: POSIX child containment unavailable")
    source = tmp_path / "input.dv"
    original = priism_file(source, np.arange(2 * 256 * 256, dtype=np.uint16).reshape(2, 256, 256))
    destination = tmp_path / "partial.tif"
    probe = tmp_path / "owned_io_probe.py"
    probe.write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, sys.argv[3])\n"
        "from shared_node_baseline_fixture import imagej_write_failure\n"
        "imagej_write_failure(Path(sys.argv[1]), Path(sys.argv[2]), json.loads(sys.argv[4]))\n",
        encoding="utf-8",
    )
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                str(probe),
                str(source),
                str(destination),
                str(ROOT / "tests"),
                json.dumps(file_config(axes=["z"], shape=[2])),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as failure:
        pytest.fail("incomplete_io_fixture: child launch failed: " + type(failure).__name__)
    try:
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                pytest.fail("incomplete_io_fixture: timed-out child cleanup incomplete")
            pytest.fail("incomplete_io_fixture: intervention child timed out")
    finally:
        # Contain the child and workers inheriting its new process group even
        # when the child exits early. No persistent export process is requested.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pytest.fail("incomplete_io_fixture: owned child could not be reaped")
    if process.returncode != 0:
        pytest.fail(f"incomplete_io_fixture: child status={process.returncode}; {stderr}")
    try:
        evidence = json.loads(stdout)
    except json.JSONDecodeError:
        pytest.fail("incomplete_io_fixture: child did not emit a complete evidence document")
    if evidence["classification"] == "incomplete_fixture":
        pytest.fail("incomplete_io_fixture: " + evidence["incomplete_reason"])
    assert evidence["classification"] == "witnessed_expected_failure", (
        "witnessed operation-time outcome failure: " + stdout
    )
    assert evidence["unrestricted_planes"] == 2
    assert evidence["unrestricted_bytes"] > evidence["limit_bytes"] == 65536
    assert evidence["limit_verified"] is True and evidence["sigxfsz_count"] > 0
    assert evidence["export_succeeded"] is False
    assert evidence["failure_is_os_error"] is True and evidence["errno_is_efbig"] is True
    assert evidence["signal_handler_restored"] is True
    assert evidence["limits_restored"] is True and evidence["source_preserved"] is True
    assert source.read_bytes() == original


def child(args: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    """Inherit the source-free Python-child environment; never replace it."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60, check=False)


@pytest.mark.parametrize(
    "body,category",
    [
        ("raise ValueError('ordinary failure')", "ValueError"),
        (
            (
                "try:\n    raise KeyError('first failure')\nexcept KeyError as "
                "cause:\n    raise RuntimeError('second failure') from cause"
            ),
            "RuntimeError",
        ),
        (
            "raise ExceptionGroup('group failure', [ValueError('one'), TypeError('two')])",
            "ExceptionGroup",
        ),
        (
            (
                "raise SyntaxError('invalid syntax', ('owned_syntax.py', 3, 2"
                ", 'HIDDEN_SOURCE_MARKER\\n'))"
            ),
            "SyntaxError",
        ),
        (
            (
                "import subprocess\nraise subprocess.TimeoutExpired(['owned-ex"
                "ecutable', '-c', 'HIDDEN_SOURCE_MARKER'], 0.25)"
            ),
            "TimeoutExpired",
        ),
        (
            (
                "import subprocess\nraise subprocess.CalledProcessError(7, ['o"
                "wned-executable', '-c', 'HIDDEN_SOURCE_MARKER'])"
            ),
            "CalledProcessError",
        ),
        (
            "import subprocess\nraise subprocess.CalledProcessError(7, 'HIDDEN_SOURCE_MARKER')",
            "CalledProcessError",
        ),
    ],
)
def test_source_free_standard_exception_channels(tmp_path: Path, body: str, category: str) -> None:
    probe = tmp_path / "owned_probe.py"
    probe.write_text("hidden_local = 'HIDDEN_SOURCE_MARKER'\n" + body + "\n", encoding="utf-8")
    result = child(
        [sys.executable, str(ROOT / "scripts/source_free_check.py"), "python", str(probe)]
    )
    rendered = result.stdout + result.stderr
    assert result.returncode != 0 and category in rendered
    assert "HIDDEN_SOURCE_MARKER" not in rendered and "hidden_local" not in rendered
    if category in ("CalledProcessError", "TimeoutExpired"):
        assert "owned-executable" in rendered or "not recorded" in rendered.lower(), rendered
    else:
        assert "owned_probe.py" in rendered or "owned_syntax.py" in rendered


def test_source_free_warning_child_and_literal_program_arguments(tmp_path: Path) -> None:
    probe = tmp_path / "warning_probe.py"
    probe.write_text(
        (
            "import warnings, sys\nwarnings.warn('observable warning', Use"
            "rWarning) # HIDDEN_SOURCE_MARKER\nassert sys.argv[1:] == ['-S"
            "', '-I', '-E']\n"
        ),
        encoding="utf-8",
    )
    harness = str(ROOT / "scripts/source_free_check.py")
    result = child([sys.executable, harness, "python", str(probe), "-S", "-I", "-E"])
    assert result.returncode == 0
    assert "observable warning" in result.stderr and "UserWarning" in result.stderr
    assert "warning_probe.py" in result.stderr and "HIDDEN_SOURCE_MARKER" not in result.stderr
    nested = tmp_path / "nested_probe.py"
    nested.write_text(
        (
            "import subprocess, sys\nsubprocess.run([sys.executable, '-c',"
            " \"raise ValueError('child failure') # HIDDEN_SOURCE_MARKER\"]"
            ", check=True)\n"
        ),
        encoding="utf-8",
    )
    outcome = child([sys.executable, harness, "python", str(nested)])
    assert outcome.returncode != 0
    assert "ValueError" in outcome.stderr and "CalledProcessError" in outcome.stderr
    assert "HIDDEN_SOURCE_MARKER" not in outcome.stderr
    for option in ("-I", "-S", "-E", "-IS", "-ES"):
        rejected = child([sys.executable, harness, "python", option, str(probe)])
        assert rejected.returncode != 0
    for duration in ("0", "-1", "nan"):
        rejected = child([sys.executable, harness, "--timeout", duration, "python", str(probe)])
        assert rejected.returncode != 0


def disposable_verifier(
    tmp_path: Path, phase_failure: int = 9, temporal_alias: bool = False
) -> tuple[Path, Path]:
    """Copy runtime opaquely; commands/evidence are independently authored."""
    repo = tmp_path / "repository"
    (repo / "scripts").mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/verify.py", repo / "scripts/verify.py")
    (repo / ".gitignore").write_text("artifacts/\n", encoding="utf-8")
    (repo / "marker.txt").write_bytes(b"unchanged tracked marker\n")
    runner = repo / "owned_make.py"
    runner.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, sys\n"
        "if '--version' in sys.argv:\n    print('GNU Make owned fixture'); sys.exit(0)\n"
        + (
            "phases = ['sync', 'coverage-clean', 'lint', 'format', 'types"
            "', 'tests', 'coverage-combine', 'coverage-json', 'coverage-h"
            "tml', 'coverage-report', 'wheel', 'wheel-import', 'audit']\n"
        )
        + (
            "phase = next(a for a in sys.argv[1:] if a in phases)\nprint('"
            "attempted phase=' + phase, flush=True)\n"
        )
        + (
            (
                "if phase == 'coverage-clean':\n    p=pathlib.Path('artifacts/"
                "verification/custom.json')\n    p.parent.mkdir(parents=True, "
                "exist_ok=True)\n    p.symlink_to(pathlib.Path('marker.txt').r"
                "esolve())\n"
            )
            if temporal_alias
            else ""
        )
        + f"sys.exit({phase_failure} if phase == 'coverage-clean' else 0)\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    for command in (
        ["git", "init", "-q"],
        ["git", "add", "."],
        [
            "git",
            "-c",
            "user.name=Owned Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "owned fixture",
        ],
    ):
        result = child(list(command), cwd=repo)
        assert result.returncode == 0
    return repo, runner


def test_verifier_genuine_failed_phase_status_order_and_safe_receipt(tmp_path: Path) -> None:
    repo, runner = disposable_verifier(tmp_path)
    result = child(
        [
            sys.executable,
            "scripts/verify.py",
            "--make",
            str(runner),
            "--uv",
            str(Path(sys.executable)),
            "--receipt",
            "artifacts/verification/custom.json",
            "--contract",
            "BASELINE-COMPATIBILITY-01",
        ],
        cwd=repo,
    )
    assert result.returncode == 9, f"status={result.returncode}; {result.stdout}; {result.stderr}"
    receipt = json.loads((repo / "artifacts/verification/custom.json").read_text())
    assert receipt["result"] == "failed" and receipt["schema"] == "org.simrecon.verification"
    assert [phase["name"] for phase in receipt["phases"]] == ["sync", "coverage-clean"]
    assert [phase["returncode"] for phase in receipt["phases"]] == [0, 9]
    for phase in receipt["phases"]:
        assert phase["command"][0] == str(runner)
        assert phase["name"] in phase["command"] and f"UV={sys.executable}" in phase["command"]
        assert (repo / phase["log"]).read_text() == "attempted phase=" + phase["name"] + "\n"
    assert receipt["context"]["contract"] == "BASELINE-COMPATIBILITY-01"
    assert receipt["context"]["reviewed_tests"] is None
    assert receipt["problems"] and receipt["before"]["commit"] == receipt["after"]["commit"]
    assert (repo / "marker.txt").read_bytes() == b"unchanged tracked marker\n"


def test_verifier_phase_introduced_receipt_alias_on_failed_run(tmp_path: Path) -> None:
    repo, runner = disposable_verifier(tmp_path, temporal_alias=True)
    marker = repo / "marker.txt"
    result = child(
        [
            sys.executable,
            "scripts/verify.py",
            "--make",
            str(runner),
            "--receipt",
            "artifacts/verification/custom.json",
        ],
        cwd=repo,
    )
    assert result.returncode != 0
    assert marker.read_bytes() == b"unchanged tracked marker\n"
    assert "attempted phase=coverage-clean" in result.stdout, (
        f"status={result.returncode}; {result.stdout}; {result.stderr}"
    )


@pytest.mark.parametrize("name", ["declare_acquisition"])
def test_required_keyword_binding_remains_python_typeerror(name: str) -> None:
    operation = getattr(sr, name)
    with pytest.raises(TypeError):
        operation(np.ones((1, 1, 1)))
    with pytest.raises(TypeError):
        operation(np.ones((1, 1, 1)), unexpected_keyword=0)


def test_imagej_cli_domain_and_io_statuses_preserve_source(tmp_path: Path) -> None:
    source = tmp_path / "input.dv"
    original = priism_file(source, np.ones((1, 2, 3), dtype="<u2"))
    config = tmp_path / "config.json"
    config.write_text(json.dumps(file_config()), encoding="utf-8")
    command = [
        str(ROOT / ".venv/bin/simrecon"),
        "export-imagej",
        str(source),
        str(tmp_path / "absent" / "output.tif"),
        "--config",
        str(config),
    ]
    io_failure = child(command)
    assert io_failure.returncode == 1
    assert json.loads(io_failure.stderr)["code"] == "io_error"
    domain_failure = child(command + ["--block-planes", "0"])
    assert domain_failure.returncode == 2
    assert json.loads(domain_failure.stderr)["code"] == "invalid_block_size"
    assert source.read_bytes() == original


def test_imagej_complete_xyzct_and_setting_plane_permutation(tmp_path: Path) -> None:
    source = tmp_path / "all_axes.dv"
    pixels = (np.arange(72 * 2 * 3, dtype=np.uint16) + 40000).reshape(72, 2, 3)
    original = priism_file(source, pixels)
    config = file_config(
        axes=["phase", "z", "time", "channel", "orientation"], shape=[3, 3, 2, 2, 2]
    )
    info = sr.harmonize(sr.inspect(source), config=config)
    destination = tmp_path / "all_axes.tif"
    report = sr.export_imagej(destination, info, block_planes=3)
    assert report.series_count == 6 and report.planes_written == 72
    assert all(series.shape == (2, 2, 3, 2, 3) for series in report.series)
    with tifffile.TiffFile(destination) as reader:
        assert len(reader.pages) == 72
        for orientation in range(2):
            for phase in range(3):
                series = orientation * 3 + phase
                assert report.series[series].name == f"orientation={orientation}; phase={phase}"
                for time in range(2):
                    for z in range(3):
                        for channel in range(2):
                            ordinal = channel + 2 * (z + 3 * time)
                            source_plane = (
                                ((phase * 3 + z) * 2 + time) * 2 + channel
                            ) * 2 + orientation
                            decoded = reader.pages[series * 12 + ordinal].asarray()
                            assert decoded.tobytes() == pixels[source_plane].tobytes()
    assert source.read_bytes() == original
