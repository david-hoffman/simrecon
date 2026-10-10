"""Independent Priism bytes and pinned, external reader observations for IMAGEJ-EXPORT-01.

No SIMrecon implementation or writer supplies this fixture's coordinates/pixels.
"""

from __future__ import annotations

import base64
import hashlib
import itertools
import json
import math
import os
import struct
import subprocess
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import tifffile

CANONICAL = ("time", "channel", "orientation", "phase", "z")
NS = "http://www.openmicroscopy.org/Schemas/OME/2016-06"
JAR_HASHES = {
    "bioformats_package.jar": "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9",
    "ij-1.54p.jar": "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20",
}
FLOAT_SPECIAL = (
    0,
    0x80000000,
    0x7F800000,
    0xFF800000,
    0x7FC12345,
    0x7FA23456,
    0xFFC56789,
    1,
    0x007FFFFF,
    0x3F800001,
)
RUN_ID = os.environ.get("SIMRECON_MEASUREMENTS_RUN_ID", str(uuid.uuid4()))
ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def finite_json(value: Any) -> Any:
    """Encode public value records independently, preserving source-word objects."""
    if isinstance(value, Mapping):
        return {str(key): finite_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(item) for item in value]
    if isinstance(value, float):
        assert math.isfinite(value), "public nonfinite fields need IEEE-word representation"
    return value


def reject_json_constant(token: str) -> None:
    raise AssertionError(f"nonfinite JSON token: {token}")


def json_with_exact_numbers(text: str, **kwargs: Any) -> Any:
    """Preserve integer/fraction/exponent values and -0 before domain checks."""
    return json.loads(
        text, parse_int=Decimal, parse_float=Decimal, parse_constant=reject_json_constant, **kwargs
    )


def exact_json_dumps(value: Any, *, ensure_ascii: bool = False) -> str:
    """Serialize an observation without rounding exact decoded number values.

    Raw CLI text is captured separately; Decimal spelling here preserves value
    and zero sign, but is not claimed to preserve the original numeral spelling.
    Native public/API floats use ordinary finite round-trip JSON encoding.
    """
    if isinstance(value, Decimal):
        assert value.is_finite(), "nonfinite exact observation"
        return str(value)
    if isinstance(value, Mapping):
        assert all(isinstance(key, str) for key in value)
        return (
            "{"
            + ", ".join(
                json.dumps(key, ensure_ascii=ensure_ascii)
                + ": "
                + exact_json_dumps(value[key], ensure_ascii=ensure_ascii)
                for key in sorted(value)
            )
            + "}"
        )
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(exact_json_dumps(v, ensure_ascii=ensure_ascii) for v in value) + "]"
    return json.dumps(value, ensure_ascii=ensure_ascii, allow_nan=False)


def cli_json_basename(text: str) -> str:
    """Retain original stdout bytes/text except top-level destination path tokens."""
    decoder = json.JSONDecoder(
        parse_int=Decimal, parse_float=Decimal, parse_constant=reject_json_constant
    )

    def skip_space(position: int) -> int:
        while position < len(text) and text[position] in " \t\r\n":
            position += 1
        return position

    position = skip_space(0)
    assert text[position] == "{"
    position = skip_space(position + 1)
    replacements = []
    while text[position] != "}":
        key, position = decoder.raw_decode(text, position)
        position = skip_space(position)
        assert text[position] == ":"
        start = skip_space(position + 1)
        value, position = decoder.raw_decode(text, start)
        if key == "destination":
            assert isinstance(value, str)
            replacements.append((start, position, json.dumps(Path(value).name, ensure_ascii=False)))
        position = skip_space(position)
        if text[position] == "}":
            break
        assert text[position] == ","
        position = skip_space(position + 1)
    assert replacements
    for start, end, replacement in reversed(replacements):
        text = text[:start] + replacement + text[end:]
    return text


def values_equal(actual: Any, expected: Any) -> bool:
    """Compare exact integer domains or approved finite binary64 round trips.

    Expected public int/float values select the domain, not observed spelling.
    Boolean kind stays distinct. Exact copied float zero requires zero magnitude
    and sign; integer/count values select no zero sign. Arrays remain ordered.
    Decimal expectations are used only for lossless evidence self-checks.
    """
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(actual) is bool and type(expected) is bool and actual is expected
    if expected is None or actual is None:
        return actual is expected
    if isinstance(expected, (int, float, Decimal)) or isinstance(actual, (int, float, Decimal)):
        if not isinstance(actual, (int, float, Decimal)) or not isinstance(
            expected, (int, float, Decimal)
        ):
            return False
        if any(
            isinstance(value, float) and not math.isfinite(value) for value in (actual, expected)
        ):
            return False
        if any(
            isinstance(value, Decimal) and not value.is_finite() for value in (actual, expected)
        ):
            return False
        if isinstance(expected, float):
            # Decimal-to-double conversion belongs only at this float-domain
            # boundary. Exact integers never pass through binary64.
            observed_float = float(actual)
            if not math.isfinite(observed_float) or observed_float != expected:
                return False
            if expected == 0:
                return actual == 0 and math.copysign(1.0, observed_float) == math.copysign(
                    1.0, expected
                )
            return True
        if isinstance(expected, Decimal) and expected == 0 and isinstance(actual, Decimal):
            return actual == expected and actual.is_signed() == expected.is_signed()
        return actual == expected
    if isinstance(expected, Mapping):
        return (
            isinstance(actual, Mapping)
            and actual.keys() == expected.keys()
            and all(values_equal(actual[key], value) for key, value in expected.items())
        )
    if isinstance(expected, (list, tuple)):
        return (
            isinstance(actual, (list, tuple))
            and len(actual) == len(expected)
            and all(values_equal(a, e) for a, e in zip(actual, expected, strict=True))
        )
    return type(actual) is type(expected) and actual == expected


def assert_values(actual: Any, expected: Any) -> None:
    assert values_equal(actual, expected), "public value/kind/float-sign preservation mismatch"


@dataclass(frozen=True)
class Acquisition:
    """Explicit rectangular acquisition; bytes use the public Priism offsets."""

    plane_axes: tuple[str, ...] = ("phase", "z", "time", "orientation", "channel")
    plane_shape: tuple[int, ...] = (3, 3, 2, 2, 2)
    x: int = 5
    y: int = 3
    mode: int = 6
    byte_order: str = "little"
    extension: bytes = b"\x00opaque\xff\x80\x00settings\x01"
    sampling: tuple[float, float, float] = (0.0975, 0.173, 0.625)
    overrides: Mapping[str, Any] = field(default_factory=dict)
    spatial_words: tuple[int, int, int] | None = None
    map_axes: tuple[int, int, int] = (1, 2, 3)

    @property
    def counts(self) -> dict[str, int]:
        return dict(zip(self.plane_axes, self.plane_shape, strict=True))

    def count(self, axis: str) -> int:
        return self.counts.get(axis, 1)

    @property
    def sections(self) -> int:
        return math.prod(self.plane_shape)

    @property
    def itemsize(self) -> int:
        return 2 if self.mode == 6 else 4 if self.mode == 2 else 1

    @property
    def series_count(self) -> int:
        return self.count("orientation") * self.count("phase")

    @property
    def series_shape(self) -> tuple[int, ...]:
        return (self.count("time"), self.count("channel"), self.count("z"), self.y, self.x)

    def name(self, o: int, p: int) -> str:
        orientation = str(o) if "orientation" in self.plane_axes else "absent"
        phase = str(p) if "phase" in self.plane_axes else "absent"
        return f"orientation={orientation}; phase={phase}"

    def config(self) -> dict[str, Any]:
        return {
            "version": 1,
            "data_kind": "spatial_image",
            "plane_axes": list(self.plane_axes),
            "plane_shape": list(self.plane_shape),
            "spatial_fields": "direct_um",
            "extended_header": "opaque" if self.extension else "none",
            "overrides": finite_json(self.overrides),
        }

    def header(self) -> bytes:
        header = bytearray((i * 37 + 11) % 256 for i in range(1024))
        endian = "<" if self.byte_order == "little" else ">"

        def put(offset: int, fmt: str, *values: int | float) -> None:
            struct.pack_into(endian + fmt, header, offset, *values)

        put(0, "4i", self.x, self.y, self.sections, self.mode)
        put(28, "3i", 17, 19, 23)
        if self.spatial_words is None:
            put(40, "3f", *self.sampling)
        else:
            put(40, "3I", *self.spatial_words)
        put(64, "3i", *self.map_axes)
        put(92, "i", len(self.extension))
        put(96, "h", -16224)
        put(128, "2h", 7, 9)
        put(180, "2h", 5, 4)
        put(196, "6h", 4, 488, 561, 640, 405, 730)
        return bytes(header)

    def resolved_sampling(self) -> dict[str, float | None]:
        """Derive scale from source float32 words and explicit binary64 overrides."""
        order = "<" if self.byte_order == "little" else ">"
        words = struct.unpack_from(order + "3f", self.header(), 40)
        explicit = self.overrides.get("sampling_um", {})
        result: dict[str, float | None] = {}
        for axis, word in zip("xyz", words, strict=True):
            if axis == "z" and "z" not in self.plane_axes:
                result[axis] = None
            else:
                value = explicit.get(axis, word)
                assert isinstance(value, (int, float)) and math.isfinite(value) and value > 0
                result[axis] = float(value)
        return result

    def word(self, coordinates: Mapping[str, int], y: int, x: int) -> int:
        canonical_plane = 0
        for axis in CANONICAL:
            canonical_plane = canonical_plane * self.count(axis) + coordinates.get(axis, 0)
        ordinal = (canonical_plane * self.y + y) * self.x + x
        if self.mode == 6:
            return (0, 65535, 32768)[ordinal] if ordinal < 3 else (40000 + ordinal) % 65536
        if ordinal < len(FLOAT_SPECIAL):
            return FLOAT_SPECIAL[ordinal]
        return struct.unpack("<I", struct.pack("<f", ordinal / 4 - 173))[0]

    def plane_bytes(self, *, o: int, p: int, t: int, c: int, z: int) -> bytes:
        coords = {"orientation": o, "phase": p, "time": t, "channel": c, "z": z}
        fmt = "<H" if self.mode == 6 else "<I"
        return b"".join(
            struct.pack(fmt, self.word(coords, y, x)) for y in range(self.y) for x in range(self.x)
        )

    def write(self, path: Path, *, sparse: bool = False) -> None:
        with path.open("xb") as stream:
            stream.write(self.header())
            stream.write(self.extension)
            if sparse:
                stream.truncate(
                    1024 + len(self.extension) + self.sections * self.x * self.y * self.itemsize
                )
                return
            fmt = ("<" if self.byte_order == "little" else ">") + (
                "H" if self.mode == 6 else "I" if self.mode == 2 else "B"
            )
            for position in itertools.product(*(range(n) for n in self.plane_shape)):
                coords = dict(zip(self.plane_axes, position, strict=True))
                for y in range(self.y):
                    for x in range(self.x):
                        word = self.word(coords, y, x) if self.mode in (2, 6) else 0
                        stream.write(struct.pack(fmt, word))


def scale_close(actual: float, expected: float) -> None:
    # Round-trip binary64 decimal parsing: <= 0.5 ulp. Same-unit conversion has
    # factor 1; reserve a further rounding in each reader/JSON transfer, 4 ulps.
    # This rejects float32 rounding (normally ~2**29 binary64 ulps).
    assert isinstance(actual, (int, float)) and not isinstance(actual, bool)
    assert isinstance(expected, (int, float)) and not isinstance(expected, bool)
    assert math.isfinite(actual) and actual > 0
    assert abs(actual - expected) <= 4 * math.ulp(expected), "binary64 scale not preserved"


def sparse_extension_source(path: Path, spec: Acquisition, length: int) -> bytes:
    """Write declared zero opaque bytes and zero pixels as sparse public file bytes."""
    assert not spec.extension and length >= 0
    header = bytearray(spec.header())
    struct.pack_into("<i" if spec.byte_order == "little" else ">i", header, 92, length)
    with path.open("xb") as stream:
        stream.write(header)
        stream.truncate(1024 + length + spec.sections * spec.x * spec.y * spec.itemsize)
    digest = hashlib.sha256()
    zero_chunk = bytes(1 << 20)
    remaining = length
    while remaining:
        size = min(remaining, len(zero_chunk))
        digest.update(zero_chunk[:size])
        remaining -= size
    return digest.digest()


def reader_inputs() -> dict[str, Any]:
    inputs = json.loads((ROOT / "artifacts/imagej-reader/inputs.json").read_text())
    for name, expected_hash in JAR_HASHES.items():
        entry = inputs["jars"][name]
        path = Path(entry["path"])
        assert entry["sha256"] == expected_hash
        assert path.stat().st_size == entry["size_bytes"]
        assert sha256(path) == expected_hash
    assert inputs["java"]["version"] == "21.0.7"
    return inputs


def observe(path: Path | None, scratch: Path) -> dict[str, Any]:
    inputs = reader_inputs()
    scratch = scratch / ("launch-" + str(uuid.uuid4()))
    scratch.mkdir(parents=True, exist_ok=True)
    prefs = scratch / "preferences"
    prefs.mkdir(exist_ok=True)
    result_file = scratch / "observer.json"
    cp = os.pathsep.join(
        inputs["jars"][name]["path"] for name in ("ij-1.54p.jar", "bioformats_package.jar")
    )
    args = [
        inputs["java"]["executable"],
        "-Djava.awt.headless=true",
        f"-Duser.home={prefs}",
        f"-Djava.util.prefs.userRoot={prefs / 'user'}",
        f"-Djava.util.prefs.systemRoot={prefs / 'system'}",
        "--class-path",
        cp,
        str(ROOT / "tests/imagej_export_reader.java"),
        "--startup" if path is None else str(path),
        str(result_file),
    ]
    if path is not None:
        with tifffile.TiffFile(path) as carrier:
            first_page = carrier.pages[0]
            assert isinstance(first_page, tifffile.TiffPage)
            carrier_xml = first_page.description
        xml_path = scratch / "carrier.xml"
        xml_path.write_text(carrier_xml, encoding="utf-8")
        args.append(str(xml_path))
    result = subprocess.run(args, capture_output=True, text=True, timeout=180)
    (scratch / "observer.stdout.log").write_text(result.stdout)
    (scratch / "observer.stderr.log").write_text(result.stderr)
    assert result.returncode == 0, (
        f"owned Java observer failed ({result.returncode}): {result.stderr}"
    )
    record = json.loads(result_file.read_text())
    assert record["java_version"] == "21.0.7"
    assert record["java_vendor"] == inputs["java"]["vendor"]
    assert record["java_platform"] == inputs["java"]["platform"]
    assert record["imagej_version"] == "1.54p"
    assert record["bioformats_version"] == "8.5.0"
    record["reader_inputs"] = {
        "manifest_sha256": sha256(ROOT / "artifacts/imagej-reader/inputs.json"),
        "jars": {
            name: {"sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
            for name, entry in inputs["jars"].items()
        },
        "java": {key: inputs["java"][key] for key in ("version", "vendor", "platform")},
        "java_executable_sha256": sha256(Path(inputs["java"]["executable"])),
    }
    record["preferences"] = "isolated owned scratch/user+system preferences; user.home isolated"
    return record


def persist_observation(
    record: dict[str, Any], source: Path, output: Path, config: Mapping[str, Any], label: str
) -> Path:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10
        )
        return result.stdout.strip()

    record.update(
        {
            "schema": "org.simrecon.imagej-interop-observation",
            "version": 1,
            "run_id": RUN_ID,
            "fixture_label": label,
            "product_observation": True,
            "candidate": {
                "head": git("rev-parse", "HEAD"),
                "tree": git("rev-parse", "HEAD^{tree}"),
                "tracked_state": git("status", "--porcelain=v1", "--untracked-files=no"),
            },
            "owned_inputs": {
                name: sha256(ROOT / name)
                for name in (
                    "tests/test_imagej_export.py",
                    "tests/imagej_export_fixture.py",
                    "tests/imagej_export_reader.java",
                )
            },
            "source": {
                "name": source.name,
                "sha256": sha256(source),
                "size_bytes": source.stat().st_size,
            },
            "output": {
                "name": output.name,
                "sha256": sha256(output),
                "size_bytes": output.stat().st_size,
            },
            "config": finite_json(config),
            "config_sha256": hashlib.sha256(
                json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest(),
            "checked_pixels": (
                "every raw byte and every ImagePlus primitive word/coordinate; JVM NaNs classified"
            ),
            "assertions_passed": True,
        }
    )
    target = ROOT / "artifacts/verification/imagej-interop" / RUN_ID
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{label}-{uuid.uuid4()}.json"
    # Exclusive create prevents replacement of any other run's observation.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, allow_nan=False, sort_keys=True)
    return path


def report_observation(
    report: Any,
    source: Path,
    output: Path,
    config: Mapping[str, Any],
    spec: Acquisition,
    info: Any,
    label: str,
    *,
    cli_report: Mapping[str, Any] | None = None,
    cli_stdout: str | None = None,
) -> dict[str, Any]:
    """Capture observations, never decide the truth of unrestricted English.

    The API tuple is encoded as a JSON array with its observed Python type.
    Only destination paths are reduced to basenames; all disclosure text and
    other public report values remain exact. Tests compare destinations locally.
    Independent D must assess these texts AND the actual emitting paths.
    """

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=10
        )
        return result.stdout.strip()

    api_report = {
        "destination": report.destination.name,
        "series": [
            {
                "index": series.index,
                "name": series.name,
                "orientation_index": series.orientation_index,
                "phase_index": series.phase_index,
                "shape": finite_json(series.shape),
            }
            for series in report.series
        ],
        "series_count": report.series_count,
        "planes_written": report.planes_written,
        "provenance": finite_json(report.provenance),
        "limitations": list(report.limitations),
    }
    captured_cli = None
    captured_cli_stdout = None
    cli_stdout_sha256 = None
    cli_output = None
    if cli_report is not None:
        assert cli_stdout is not None
        assert_values(json_with_exact_numbers(cli_stdout), cli_report)
        captured_cli_stdout = cli_json_basename(cli_stdout)
        cli_stdout_sha256 = hashlib.sha256(cli_stdout.encode("utf-8")).hexdigest()
        captured_cli = finite_json(cli_report)
        captured_cli["destination"] = Path(cli_report["destination"]).name
        cli_path = Path(cli_report["destination"])
        cli_output = {
            "name": cli_path.name,
            "sha256": sha256(cli_path),
            "size_bytes": cli_path.stat().st_size,
        }
    inputs = reader_inputs()
    return {
        "schema": "org.simrecon.imagej-report-observation",
        "version": 1,
        "run_id": RUN_ID,
        "fixture_label": label,
        "candidate": {
            "head": git("rev-parse", "HEAD"),
            "tree": git("rev-parse", "HEAD^{tree}"),
            "tracked_state": git("status", "--porcelain=v1", "--untracked-files=no"),
        },
        "owned_inputs": {
            name: sha256(ROOT / name)
            for name in (
                "tests/test_imagej_export.py",
                "tests/imagej_export_fixture.py",
                "tests/imagej_export_reader.java",
            )
        },
        "contract_sha256": sha256(ROOT / "docs/contracts/imagej-export-v1.md"),
        "source": {
            "name": source.name,
            "sha256": sha256(source),
            "size_bytes": source.stat().st_size,
            "mtime_ns": source.stat().st_mtime_ns,
            "header_sha256": info.header_sha256,
        },
        "output": {
            "name": output.name,
            "sha256": sha256(output),
            "size_bytes": output.stat().st_size,
        },
        "config": finite_json(config),
        "config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest(),
        "input_class": {
            "pixel_mode": spec.mode,
            "byte_order": spec.byte_order,
            "plane_axes": list(spec.plane_axes),
            "plane_shape": list(spec.plane_shape),
            "logical_axes": list(info.axes),
            "logical_shape": list(info.shape),
            "axis_presence": {axis: axis in spec.plane_axes for axis in CANONICAL},
            "opaque_extension_bytes": info.extended_header_bytes,
            "sampling_um": finite_json(info.sampling_um),
            "float_special_words_in_fixture": spec.mode == 2,
        },
        "api_report": api_report,
        "api_limitations_python_type": type(report.limitations).__name__,
        "cli_report": captured_cli,
        "cli_stdout": captured_cli_stdout,
        "cli_stdout_sha256": cli_stdout_sha256,
        "cli_output": cli_output,
        "destination_path_recording": "basename only; exact path checked locally",
        "semantic_review": {
            "status": "pending independent D assessment of actual text and emitting paths",
            "automated_truth_verdict": False,
            "matrix": "IMAGEJ-EXPORT-01-A-04 report-01.md disclosure matrix",
        },
        "reader_inputs": {
            "manifest_sha256": sha256(ROOT / "artifacts/imagej-reader/inputs.json"),
            "jars": {
                name: {"sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
                for name, entry in inputs["jars"].items()
            },
            "java": {key: inputs["java"][key] for key in ("version", "vendor", "platform")},
            "java_executable_sha256": sha256(Path(inputs["java"]["executable"])),
        },
    }


def persist_report_observation(
    report: Any,
    source: Path,
    output: Path,
    config: Mapping[str, Any],
    spec: Acquisition,
    info: Any,
    label: str,
    *,
    cli_report: Mapping[str, Any] | None = None,
    cli_stdout: str | None = None,
) -> Path:
    record = report_observation(
        report,
        source,
        output,
        config,
        spec,
        info,
        label,
        cli_report=cli_report,
        cli_stdout=cli_stdout,
    )
    # An actual successful export report earns report evidence only. This does
    # not claim a Java observation, pixel-check success or semantic acceptance.
    record.update(product_observation=True, observation_kind="successful-export-report")
    target = ROOT / "artifacts/verification/imagej-interop" / RUN_ID
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"report-{label}-{uuid.uuid4()}.json"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(exact_json_dumps(record))
    return path


def decode_raw(plane: Mapping[str, Any]) -> bytes:
    return base64.b64decode(plane["bytes_base64"], validate=True)
