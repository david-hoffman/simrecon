"""FIXTURE-EXPORT-01 blind A02: public command and corrected R3 preservation.

S01--S11 use the real command. S12 retirement/link/history scope and S13 full
candidate/config/gates require coordinator/D review; frozen hashes are checked
here. No Git-history access or permanent JSON payload is needed by these tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any

import numpy as np
import pytest

import otf_calibration_fixture as otf
import reconstruction_fixture as reconstruction
from reference_fixture_export_oracle import (
    assert_exact,
    auxiliary_planes,
    complex_layout,
    digest,
    historical_display,
)

ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts/generate_reference_fixtures.py"
DOCUMENTS = {
    "otf": (
        "otf-calibration-fixtures-v1.json",
        "ba2dcd790738cf950b184995e1c12935266ddaa1738c9f874b46a6dd442c9dcf",
        "0cf7ec8dd42396576914a421dc8a4bb67bfb0b586ceeb2046e5d467a19ec7d41",
    ),
    "reconstruction": (
        "reconstruction-fixtures-v1.json",
        "64decad0389d332100bee202a02a8bafacd1c942e324dff992babccb8ca88541",
        "1b2d562540e2cd9f6d8b63746d3c61317e9eadc0499fbed85cac907b9411fbce",
    ),
}
ACQUISITION_HASHES = (
    "83281edcbaf738af9f78b025630a27ed50f8270349114fb7b7bbca427ffc97e2",
    "bb1f007740ae091fdae2037bf83cae210147c6d5e0bf3d343fc682e14520bcc5",
)
# Public dataset schemas identify data-bearing output, not diagnostic keywords.
# These compact field names contain neither retired payload nor generated arrays.
DATASET_SCHEMAS: tuple[tuple[str, frozenset[str], frozenset[str]], ...] = (
    (
        "fixtures",
        frozenset(("version", "status", "expected_value_policy", "frequency_policy", "fixtures")),
        frozenset(
            (
                "id",
                "shape_yx",
                "origin_yx",
                "pixel_size_um",
                "source",
                "input_dtype",
                "psf_samples",
                "mode_y",
                "mode_x",
                "frequency_y_per_um",
                "frequency_x_per_um",
                "expected_formula",
                "expected_otf_real",
                "expected_otf_imag",
                "oracle",
                "example_fft_cross_check_max_abs",
            )
        ),
    ),
    (
        "entries",
        frozenset(
            (
                "version",
                "role",
                "product_outputs",
                "oracle_precision_decimal_digits",
                "oracle_methods",
                "units",
                "object_coefficients",
                "psf_formula",
                "psf_preprocessing",
                "independent_input_hashes",
                "primary_references",
                "entries",
            )
        ),
        frozenset(
            (
                "name",
                "shape_detector",
                "images",
                "images_sha256",
                "images_dtype",
                "images_layout",
                "phases_rad",
                "wavevectors_per_um",
                "modulation",
                "brightness",
                "regularization",
                "apodization",
                "otf",
                "pixel_size_um_detector",
                "origin_yx_psf",
                "source_label",
                "independent_psf",
                "object_truth",
                "object_truth_spectrum",
                "rounded_data_estimator_spectrum",
                "rounded_data_estimator_image",
                "conventional_unilluminated_observation",
                "informative_budget_coordinate",
                "min_positive_V",
                "max_V",
                "physical_limitation",
            )
        ),
    ),
)
REAL_DATA_FIELDS = {
    "fixtures": ("psf_samples", "expected_otf_real", "expected_otf_imag"),
    "entries": ("images", "independent_psf", "conventional_unilluminated_observation"),
}
COMPLEX_DATA_FIELDS = (
    "otf",
    "object_truth",
    "object_truth_spectrum",
    "rounded_data_estimator_spectrum",
    "rounded_data_estimator_image",
)


def diagnostic_environment(child_temporary: Path) -> dict[str, str]:
    """Install child diagnostics independently of the parent's module registry."""
    result = os.environ.copy()
    site = str(ROOT / "scripts/source_free_sitecustomize")
    previous = result.get("PYTHONPATH", "")
    result["PYTHONPATH"] = site + (os.pathsep + previous if previous else "")
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    result["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + result.get("PATH", "")
    for variable in ("TMPDIR", "TEMP", "TMP"):
        result[variable] = str(child_temporary)
    return result


def assert_no_child_residue(
    directory: Path, child_temporary: Path, caller_entries: set[Path], returncode: int
) -> None:
    """Observe cwd and the child's dedicated tempfile root before cleanup."""
    label = f"child exit status {returncode}"
    assert set(directory.iterdir()) == caller_entries | {child_temporary}, (
        f"child changed caller directory entries; {label}"
    )
    assert child_temporary.is_dir() and not child_temporary.is_symlink(), (
        f"child changed its temporary root; {label}"
    )
    assert not list(child_temporary.iterdir()), f"child left temporary residue; {label}"


def assert_capture_unchanged(capture: Path, payload: bytes) -> None:
    assert capture.is_file() and capture.read_bytes() == payload, (
        "repeated invocation changed caller-owned capture"
    )


def run(arguments: list[str], directory: Path, *, stdout: Any = subprocess.PIPE) -> Any:
    caller_entries = set(directory.iterdir())
    with TemporaryDirectory(prefix="child-temp-", dir=directory) as temporary:
        child_temporary = Path(temporary)
        result = subprocess.run(
            [sys.executable, str(EXPORTER), *arguments],
            cwd=directory,
            env=diagnostic_environment(child_temporary),
            stdout=stdout,
            stderr=subprocess.PIPE,
            timeout=240,
            check=False,
        )
        assert_no_child_residue(directory, child_temporary, caller_entries, result.returncode)
    assert set(directory.iterdir()) == caller_entries, "invocation temporary root did not clean up"
    return result


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        assert key not in result, "duplicate JSON field"
        result[key] = value
    return result


def reject_nonfinite(value: str) -> Any:
    raise AssertionError(f"nonfinite JSON token: {value}")


def parse(payload: bytes) -> Any:
    return json.loads(payload, object_pairs_hook=unique_object, parse_constant=reject_nonfinite)


def scalar_tensor(shape: tuple[int, ...]) -> Any:
    """Generate shape controls from one scalar; no historical samples are stored."""
    if not shape:
        return 0.0
    return [scalar_tensor(shape[1:]) for _ in range(shape[0])]


def dataset_representation(container: str) -> dict[str, Any]:
    """Public complete-document structures, independent of scientific values.

    These scalar-generated controls describe every field, fixed extent and case
    identity. They are neither numerical expectations nor valid fixture data.
    Rejection recognition does not test accuracy, ordering or exact leaf values.
    """
    _, root_fields, record_fields = next(s for s in DATASET_SCHEMAS if s[0] == container)
    root: dict[str, Any] = dict.fromkeys(sorted(root_fields), "")
    records = []
    if container == "fixtures":
        cases = (
            ("delta-odd", (3, 5)),
            ("uniform-even", (4, 6)),
            ("asymmetric-even", (4, 6)),
            ("asymmetric-translated", (4, 6)),
            ("separable-mixed", (3, 4)),
            ("singleton", (1, 1)),
        )
        for name, shape in cases:
            record: dict[str, Any] = dict.fromkeys(sorted(record_fields), "")
            record.update(
                id=name,
                shape_yx=list(shape),
                origin_yx=[0, 0],
                pixel_size_um=scalar_tensor((2,)),
                mode_y=scalar_tensor((shape[0],)),
                mode_x=scalar_tensor((shape[1],)),
                frequency_y_per_um=scalar_tensor((shape[0],)),
                frequency_x_per_um=scalar_tensor((shape[1],)),
                example_fft_cross_check_max_abs=0.0,
            )
            for field in REAL_DATA_FIELDS[container]:
                record[field] = scalar_tensor(shape)
            records.append(record)
    else:
        root.update(
            version=0,
            product_outputs=False,
            oracle_precision_decimal_digits=0,
            oracle_methods=[""] * 6,
            units=dict.fromkeys(("spatial", "wavevectors", "phases", "otf", "intensity"), ""),
            object_coefficients={
                **{mode: scalar_tensor((2,)) for mode in ("0,0", "1,0", "0,3", "2,1")},
                "negative_modes": "",
            },
            independent_input_hashes=dict.fromkeys(
                (
                    "tests/test_reconstruction.py",
                    "tests/reconstruction_fixture.py",
                    "tests/reconstruction_failure_controls.py",
                    "docs/contracts/known-parameter-reconstruction-v1.md",
                    "docs/contracts/known-phase-separation-v2.md",
                    "docs/contracts/otf-calibration-v1.md",
                    "uv.lock",
                    "pyproject.toml",
                ),
                "",
            ),
            primary_references=[""] * 2,
        )
        for name in ("commensurate-recovery", "fractional-estimator"):
            record = dict.fromkeys(sorted(record_fields), "")
            record.update(
                name=name,
                shape_detector=[7, 9],
                images=scalar_tensor((2, 7, 7, 9)),
                phases_rad=scalar_tensor((2, 7)),
                wavevectors_per_um=scalar_tensor((2, 2)),
                modulation=scalar_tensor((2,)),
                brightness=scalar_tensor((2,)),
                regularization=0.0,
                apodization=scalar_tensor((14, 18)),
                pixel_size_um_detector=scalar_tensor((2,)),
                origin_yx_psf=[0, 0],
                independent_psf=scalar_tensor((7, 9)),
                conventional_unilluminated_observation=scalar_tensor((7, 9)),
                informative_budget_coordinate=0.0,
                min_positive_V=0.0,
                max_V=0.0,
            )
            for field in COMPLEX_DATA_FIELDS:
                shape = (7, 9) if field == "otf" else (14, 18)
                record[field] = {part: scalar_tensor(shape) for part in ("real", "imag")}
            records.append(record)
    root[container] = records
    return root


def complete_representation(value: Any, template: Any) -> bool:
    """Recognize structure and leaf kinds; never impose scientific tolerances."""
    if isinstance(template, dict):
        return isinstance(value, dict) and all(
            key in value and complete_representation(value[key], item)
            for key, item in template.items()
        )
    if isinstance(template, list):
        return (
            isinstance(value, list)
            and len(value) == len(template)
            and all(complete_representation(v, t) for v, t in zip(value, template, strict=True))
        )
    if type(template) in (int, float):
        return type(value) in (int, float)
    return type(value) is type(template)


def assert_no_success_document(payload: bytes) -> None:
    """Recognize a complete family, independently of exact success equality.

    All public cases and their entire representations must be present. Numeric
    fragments, incomplete case collections and unavailable metadata are legal
    diagnostics. Extra claims/nonrecords cannot mask a retained complete family.
    Malformed framing and arbitrary text are not scanned for embedded data.
    """
    try:
        document = json.loads(payload)
    except (ValueError, UnicodeError):
        return
    if not isinstance(document, dict):
        return
    for container, _, _ in DATASET_SCHEMAS:
        template = dataset_representation(container)
        expected_records = template.pop(container)
        if not complete_representation(document, template):
            continue
        records = document.get(container)
        identity = "id" if container == "fixtures" else "name"
        assert not (
            isinstance(records, list)
            and all(
                any(
                    isinstance(record, dict)
                    and record.get(identity) == expected[identity]
                    and complete_representation(record, expected)
                    for record in records
                )
                for expected in expected_records
            )
        ), "rejection emitted a dataset document"


@pytest.fixture(scope="module", params=("otf", "reconstruction"))
def exported(request: Any) -> Iterator[tuple[str, Any]]:
    """Two real commands and caller capture/consume/cleanup lifecycle (S07/S10)."""
    selector: str = request.param
    with TemporaryDirectory(prefix="reference-export-") as temporary:
        directory = Path(temporary)
        capture = directory / "reference.json"
        with capture.open("wb") as stream:
            first = run([selector], directory, stdout=stream)
        assert first.returncode == 0, first.stderr.decode(errors="replace")
        payload = capture.read_bytes()
        document = parse(payload)
        assert sorted(path.name for path in directory.iterdir()) == [capture.name], (
            "exporter created entries alongside caller-owned capture"
        )
        second = run([selector], directory)
        assert second.returncode == 0, second.stderr.decode(errors="replace")
        assert second.stdout == payload, "unchanged-input generation is not byte deterministic"
        assert_capture_unchanged(capture, payload)
        assert sorted(path.name for path in directory.iterdir()) == [capture.name]
        yield selector, document
    assert not directory.exists(), "caller TemporaryDirectory did not clean up"


def test_complete_historical_representation(exported: tuple[str, Any]) -> None:
    """All fields/types/order/strings/float bits, including historic provenance."""
    selector, document = exported
    filename, byte_hash, representation_hash = DOCUMENTS[selector]
    assert digest(document) == representation_hash, "complete historical representation mismatch"
    assert_dataset_rejection_controls(document)
    historical = ROOT / "docs/references/scientific" / filename
    if historical.exists():
        payload = historical.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == byte_hash, "historical input changed"
        assert_exact(document, parse(payload), "all historical fields before retirement")


def assert_otf_document(document: Any) -> None:
    cases = list(otf.analytic_cases())
    assert [entry["id"] for entry in document["fixtures"]] == [case[0] for case in cases]
    for entry, (case_id, samples, origin) in zip(document["fixtures"], cases, strict=True):
        ny, nx = samples.shape
        assert_exact(entry["shape_yx"], [ny, nx], "OTF shape")
        assert_exact(entry["origin_yx"], list(origin), "OTF origin")
        assert_exact(entry["psf_samples"], samples.tolist(), "converted sample integers")
        assert entry["input_dtype"] == "uint8"  # Historical label, including separable-mixed.
        assert entry["source"] == "analytic:" + case_id
        assert_exact(entry["pixel_size_um"], [0.125, 0.25], "OTF spacing")
        ys, xs = list(otf.modes(ny)), list(otf.modes(nx))
        assert_exact(entry["mode_y"], ys, "signed y modes")
        assert_exact(entry["mode_x"], xs, "signed x modes")
        for axis, size, spacing in (("y", ny, 0.125), ("x", nx, 0.25)):
            expected = [float(value) for value in otf.exact_frequency(size, spacing)]
            assert_exact(entry[f"frequency_{axis}_per_um"], expected, "signed physical frequency")
        re, im = historical_display(case_id, ys, xs)
        assert_exact(entry["expected_otf_real"], re, "binary64 algebraic display real")
        assert_exact(entry["expected_otf_imag"], im, "binary64 algebraic display imaginary")
        # Independent high-precision mathematical check; this is supplementary,
        # never a substitute for the exact historical representation above.
        high_precision = otf.reference_transfer(samples, origin)
        for iy, row in enumerate(high_precision):
            for ix, (real, imaginary) in enumerate(row):
                assert abs(Fraction.from_float(re[iy][ix]) - real) <= Fraction(1, 2**51)
                assert abs(Fraction.from_float(im[iy][ix]) - imaginary) <= Fraction(1, 2**51)


@pytest.mark.parametrize("exported", ["otf"], indirect=True)
def test_otf_formula_and_display_rounding(exported: tuple[str, Any]) -> None:
    selector, document = exported
    assert selector == "otf"
    assert_otf_document(document)


def assert_reconstruction_entry(entry: Any, fractional: bool, image_hash: str) -> None:
    """Frozen public independent formulas plus exact arrays, never product math."""
    arguments, truth_spectrum, truth = reconstruction.phantom(fractional)
    images = np.asarray(entry["images"], dtype="<f8")
    assert images.shape == (2, 7, 7, 9)
    assert images.nbytes == 7056
    assert hashlib.sha256(images.tobytes(order="C")).hexdigest() == image_hash
    assert entry["images_sha256"] == image_hash
    assert entry["images_dtype"] == "<f8" and entry["images_layout"] == "C"
    assert_exact(entry["images"], arguments["images"].tolist(), "finite acquisition/order")
    assert_exact(entry["shape_detector"], [7, 9], "detector shape")
    for field in ("phases_rad", "wavevectors_per_um", "modulation", "brightness", "apodization"):
        assert_exact(entry[field], arguments[field].tolist(), field)
    assert_exact(entry["regularization"], arguments["regularization"], "ridge parameter")
    record = arguments["otf"]  # Only frozen-helper public Otf2D construction.
    assert_exact(entry["otf"], complex_layout(record.values), "full complex analytic OTF")
    assert_exact(entry["pixel_size_um_detector"], list(record.pixel_size_um), "spacing")
    assert_exact(entry["origin_yx_psf"], list(record.origin_yx), "PSF declared origin")
    assert entry["source_label"] == record.source == "  independent analytic calibration  "
    assert_exact(entry["object_truth"], complex_layout(truth), "object truth")
    assert_exact(entry["object_truth_spectrum"], complex_layout(truth_spectrum), "truth spectrum")
    spectrum, image = reconstruction.estimator(arguments)
    assert_exact(
        entry["rounded_data_estimator_spectrum"], complex_layout(spectrum), "estimator spectrum"
    )
    assert_exact(entry["rounded_data_estimator_image"], complex_layout(image), "estimator image")
    assert_exact(
        entry["informative_budget_coordinate"],
        float(reconstruction.accuracy_budget(arguments)),
        "historical informative budget",
    )
    denominators = reconstruction.effective_denominators(arguments)
    assert_exact(entry["min_positive_V"], float(denominators[denominators > 0].min()), "min V")
    assert_exact(entry["max_V"], float(denominators.max()), "max V")
    psf, conventional, ideal = auxiliary_planes()
    assert_exact(entry["independent_psf"], psf, "85-digit PSF with final rounding")
    assert_exact(
        entry["conventional_unilluminated_observation"],
        conventional,
        "rounded scalars, hy/hx binary64 multiply/add left fold",
    )
    # Supplementary mathematical anchor only: with u=2^-53, two input
    # roundings, one multiply and <=62 effective additions give gamma_65.
    # gamma_65 < 128*u. Nonnegative unit-mass PSF and |object|<7 give
    # sum |h*object|<7 intensity units. 85-digit arithmetic is far tighter.
    with localcontext() as context:
        context.prec = 85
        bound = 128 * Decimal(2) ** -53 * 7
        for row, ideal_row in zip(conventional, ideal, strict=True):
            for value, anchor in zip(row, ideal_row, strict=True):
                assert abs(Decimal.from_float(value) - anchor) <= bound
    # A phase average has brightness and nonzero uneven-phase illumination bias.
    for orientation in arguments["images"]:
        assert not np.array_equal(np.asarray(conventional), orientation.mean(axis=0))
    assert entry["physical_limitation"]
    if fractional:
        assert digest(entry["object_truth_spectrum"]) != digest(
            entry["rounded_data_estimator_spectrum"]
        )


@pytest.mark.parametrize("exported", ["reconstruction"], indirect=True)
def test_reconstruction_formulas_and_representations(exported: tuple[str, Any]) -> None:
    selector, document = exported
    assert selector == "reconstruction"
    assert [entry["name"] for entry in document["entries"]] == [
        "commensurate-recovery",
        "fractional-estimator",
    ]
    for entry, fractional, image_hash in zip(
        document["entries"], (False, True), ACQUISITION_HASHES, strict=True
    ):
        assert_reconstruction_entry(entry, fractional, image_hash)


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["unknown"],
        ["OTF"],
        ["otf", "reconstruction"],
        ["otf", "--output", "output.json"],
        ["otf", "--settings", "{}"],
        ["otf", "--arrays", "[]"],
        ["reconstruction", "--tolerance", "1"],
    ],
)
def test_selector_rejections(exported: tuple[str, Any], arguments: list[str]) -> None:
    # Successful real public invocations are the paired positive precondition.
    assert exported[0] in DOCUMENTS
    with TemporaryDirectory(prefix="reference-rejection-") as temporary:
        directory = Path(temporary)
        result = run(arguments, directory)
        assert result.returncode != 0, "unsupported command binding succeeded"
        assert_no_success_document(result.stdout)
        assert not list(directory.iterdir()), "rejection created files"


def test_closed_stdout_reports_failure(exported: tuple[str, Any]) -> None:
    """Reachable output failure at the real public command, no product patching."""
    selector, _ = exported
    with TemporaryDirectory(prefix="reference-output-failure-") as temporary:
        directory = Path(temporary)
        reader, writer = os.pipe()
        os.close(reader)
        try:
            result = run([selector], directory, stdout=writer)
        finally:
            os.close(writer)
        assert result.returncode != 0, "closed output stream reported success"
        assert not list(directory.iterdir()), "output failure created files"


def test_frozen_helper_hash_guards() -> None:
    for filename, expected in (
        (
            "otf_calibration_fixture.py",
            "ec4edf3874ed2ebf91afae4e6f8ea2d0469381fc35382725150c10ceda010f27",
        ),
        (
            "reconstruction_fixture.py",
            "12af3e75c815e38edbd2e1d8de0c3ddf64911117a074e0bd783ac518e02a01cd",
        ),
    ):
        assert hashlib.sha256((ROOT / "tests" / filename).read_bytes()).hexdigest() == expected


def test_available_historical_oracle_evidence() -> None:
    """Independently validate retained digests/formulas while public inputs exist.

    Retirement removes this optional historical cross-check, not any exporter
    obligation: complete digest and formula tests above remain unconditional.
    """
    for selector, (filename, byte_hash, representation_hash) in DOCUMENTS.items():
        historical = ROOT / "docs/references/scientific" / filename
        if not historical.exists():
            continue
        payload = historical.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == byte_hash, "historical input changed"
        document = parse(payload)
        assert digest(document) == representation_hash, "historical digest derivation changed"
        if selector == "otf":
            assert_otf_document(document)
        else:
            for entry, fractional, image_hash in zip(
                document["entries"], (False, True), ACQUISITION_HASHES, strict=True
            ):
                assert_reconstruction_entry(entry, fractional, image_hash)


def test_observer_distinguishes_preserved_representations() -> None:
    """Challenge the shared observer's type, bit, framing, text and order risks."""
    for left, right in (
        (True, 1),
        (1, 1.0),
        (0.0, -0.0),
        (1.0, float(np.nextafter(1.0, 2.0))),
        (" calibration ", "calibration"),
        ({"real": [1.0], "imag": [0.0]}, {"imag": [0.0], "real": [1.0]}),
        ([[1, 2]], [[1], [2]]),
        (["ab", "c"], ["a", "bc"]),
    ):
        with pytest.raises(AssertionError, match="exact representation mismatch"):
            assert_exact(left, right, "observer boundary")
    assert_exact(parse(b'{"v":1.0}'), parse(b' { "v" : 1e0 }\n'), "JSON whitespace")
    with pytest.raises(AssertionError, match="duplicate JSON field"):
        parse(b'{"v":1,"v":1}')
    with pytest.raises(AssertionError, match="nonfinite"):
        parse(b'{"v":NaN}')
    for value in (float("inf"), float("nan")):
        with pytest.raises(AssertionError, match="nonfinite"):
            digest(value)
    for payload in (
        b"",
        b"selector error\n",
        b'{"error":"selector"}',
        b'{"error":"unsupported selector","entries":[]}',
        b'{"error":"unsupported selector","fixtures":[]}',
        b'{"error":"unsupported selector","entries":[],"fixtures":[]}',
        b'{"entries":[]}',
        b'{"fixtures":[]}',
    ):
        assert_no_success_document(payload)
    for container, root_fields, record_fields in DATASET_SCHEMAS:
        # A diagnostic may report every root metadata key with an empty body,
        # or a partial error record. No arbitrary root/record key is reserved.
        diagnostic: dict[str, Any] = dict.fromkeys(sorted(root_fields))
        diagnostic["error"] = "unsupported selector"
        fields = sorted(record_fields)
        for records in (
            [],
            [{"error": "unsupported selector"}],
            [None],
            [None, {"error": "unsupported selector"}, None],
            [dict.fromkeys(fields[:-1]), dict.fromkeys(fields[1:])],
        ):
            diagnostic[container] = records
            assert_no_success_document(json.dumps(diagnostic).encode())
        # Full absence/error templates are legal; keys and scalar metadata do
        # not establish scientific output, irrespective of diagnostic vocabulary.
        for placeholder in (
            None,
            {"error": "unsupported selector"},
            {"code": 17, "message": "unavailable"},
            "unavailable",
            17,
            False,
            [],
            [[None]],
            [[False]],
            [["unavailable"]],
            [[{"code": 17, "message": "unavailable"}]],
            {"real": [[None]], "imag": [[None]]},
        ):
            record = dict.fromkeys(sorted(record_fields), placeholder)
            record["error"] = "unsupported selector"
            diagnostic[container] = [None, record, {"message": "unavailable"}]
            assert_no_success_document(json.dumps(diagnostic).encode())
        mixed_record: dict[str, Any] = {
            field: None if index % 2 else {"message": "unavailable"}
            for index, field in enumerate(sorted(record_fields))
        }
        mixed_record["shape_yx" if container == "fixtures" else "shape_detector"] = [7, 9]
        mixed_record["id" if container == "fixtures" else "name"] = "diagnostic context"
        diagnostic[container] = [mixed_record]
        assert_no_success_document(json.dumps(diagnostic).encode())

        # Numeric context fragments remain incomplete, even at a payload's rank.
        # Full field names do not supply absent identities, parameters or planes.
        document: dict[str, Any] = dict.fromkeys(sorted(root_fields))
        for field in REAL_DATA_FIELDS[container]:
            for scalar in (7, 0.0, -0.0, -17.5, 1e200):
                sample: Any = scalar
                for _ in range(4 if field == "images" else 2):
                    sample = [sample]
                record = dict.fromkeys(sorted(record_fields))
                record[field] = sample
                document[container] = [record]
                assert_no_success_document(json.dumps(document).encode())
        if container == "entries":
            for field in COMPLEX_DATA_FIELDS:
                record = dict.fromkeys(sorted(record_fields))
                record[field] = {"real": [[0.0]], "imag": [[0.0]]}
                document[container] = [record]
                assert_no_success_document(json.dumps(document).encode())


@pytest.mark.parametrize("container", ("fixtures", "entries"))
def test_no_success_observer_complete_representation_controls(container: str) -> None:
    """Pair entire scalar-generated representations with incomplete diagnostics."""
    complete = dataset_representation(container)
    assert_dataset_rejection_controls(complete)
    # Values need not be historically correct to constitute complete output.
    # Recognition must not inherit the strict success digest or error vocabulary.
    assert_dataset_rejection_controls({**complete, container: list(reversed(complete[container]))})
    for index in range(len(complete[container])):
        partial = deepcopy(complete)
        del partial[container][index]
        assert_no_success_document(json.dumps(partial).encode())
    for field in complete:
        if field == container:
            continue
        for missing in (False, True):
            partial = deepcopy(complete)
            if missing:
                del partial[field]
            else:
                partial[field] = {"message": "unavailable"}
            assert_no_success_document(json.dumps(partial).encode())
        if isinstance(complete[field], dict):
            for part in complete[field]:
                partial = deepcopy(complete)
                partial[field][part] = None
                assert_no_success_document(json.dumps(partial).encode())
        elif isinstance(complete[field], list):
            partial = deepcopy(complete)
            partial[field] = partial[field][:-1]
            assert_no_success_document(json.dumps(partial).encode())
    for field, value in complete[container][0].items():
        # Hold all other data intact. An absent field, wrong leaf kind, or
        # truncated extent cannot silently become a complete record witness.
        alternatives: list[Any] = [None, {"message": "unavailable"}, False]
        if isinstance(value, list):
            alternatives.append(value[:-1])
        if isinstance(value, dict):
            alternatives.extend({**value, part: None} for part in value)
        for alternative in alternatives:
            partial = deepcopy(complete)
            partial[container][0][field] = alternative
            assert_no_success_document(json.dumps(partial).encode())
        partial = deepcopy(complete)
        del partial[container][0][field]
        assert_no_success_document(json.dumps(partial).encode())
    identity = "id" if container == "fixtures" else "name"
    partial = deepcopy(complete)
    partial[container][0][identity] = "diagnostic context"
    assert_no_success_document(json.dumps(partial).encode())

    # Numeric samples inside otherwise complete arrays are still incomplete
    # when one coordinate or one complex plane is unavailable/non-numeric.
    fields = (*REAL_DATA_FIELDS[container],)
    if container == "entries":
        fields += COMPLEX_DATA_FIELDS
    for field in fields:
        partial = deepcopy(complete)
        value = partial[container][0][field]
        if isinstance(value, dict):
            value = value["real"]
        while isinstance(value[0], list):
            value = value[0]
        value[0] = False
        assert_no_success_document(json.dumps(partial).encode())


def assert_dataset_rejection_controls(document: dict[str, Any]) -> None:
    """Whole-data variants must remain identifiable on rejected invocations."""
    reordered_records = {
        key: [dict(reversed(list(record.items()))) for record in value]
        if key in ("fixtures", "entries")
        else value
        for key, value in document.items()
    }
    for variant in (
        document,
        dict(reversed(list(document.items()))),
        {**document, "success": True},
        {**document, "error": "unsupported selector"},
        reordered_records,
    ):
        with pytest.raises(AssertionError, match="dataset document"):
            assert_no_success_document(json.dumps(variant, separators=(",", ":")).encode())
    for container in ("fixtures", "entries"):
        if container not in document:
            continue
        records = document[container]
        for extra in ({"error": "unsupported selector"}, None):
            # Preserve every complete record. A nonmatching element at either
            # end cannot mask retained scientific output or the added claim.
            for augmented in ([extra, *records], [*records, extra]):
                variant = {**document, container: augmented, "success": True}
                with pytest.raises(AssertionError, match="dataset document"):
                    assert_no_success_document(json.dumps(variant).encode())


@pytest.mark.parametrize("parent_mode", ("unregistered", "unrelated"))
def test_child_diagnostics_without_parent_precondition(
    parent_mode: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Supplemental harness control; installed parent hooks remain active.

    Changing only registry/env metadata models the faulty precondition safely.
    It does not reproduce the ordinary full canonical gate, which root owns.
    """
    with TemporaryDirectory(prefix="observer-diagnostics-") as temporary:
        directory = Path(temporary)
        script = directory / "diagnostic_control.py"
        script.write_text(
            "import warnings\n"
            "warnings.warn('child warning control', UserWarning)  # source-marker\n"
            "raise RuntimeError('child failure control')  # source-marker\n",
            encoding="utf-8",
        )
        with TemporaryDirectory(prefix="child-temp-", dir=directory) as child:
            child_temporary = Path(child)
            with monkeypatch.context() as parent:
                if parent_mode == "unregistered":
                    parent.delitem(sys.modules, "sitecustomize", raising=False)
                    parent.delenv("PYTHONPATH", raising=False)
                    inherited = ""
                else:
                    parent.setitem(sys.modules, "sitecustomize", ModuleType("sitecustomize"))
                    inherited = str(directory / "caller-imports")
                    parent.setenv("PYTHONPATH", inherited)
                environment = diagnostic_environment(child_temporary)
            site = str(ROOT / "scripts/source_free_sitecustomize")
            assert environment["PYTHONPATH"] == site + (os.pathsep + inherited if inherited else "")
            assert environment["PATH"].split(os.pathsep)[0] == str(ROOT / ".venv/bin")
            assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
            assert all(environment[key] == child for key in ("TMPDIR", "TEMP", "TMP"))
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=directory,
                env=environment,
                capture_output=True,
                timeout=30,
                check=False,
            )
            assert result.returncode == 1, "diagnostic control lost failure status"
            assert not result.stdout, "diagnostic control wrote unexpected stdout"
            diagnostics = result.stderr.decode(errors="replace")
            assert "UserWarning: child warning control" in diagnostics
            assert "RuntimeError: child failure control" in diagnostics
            assert str(script) in diagnostics, "diagnostic control lost its location"
            for line in (2, 3):
                assert f":{line}:" in diagnostics or f"line {line}" in diagnostics
            assert "source-marker" not in diagnostics, "child diagnostics exposed source lines"
            assert_no_child_residue(directory, child_temporary, {script}, result.returncode)
        assert set(directory.iterdir()) == {script}
    assert not directory.exists()


@pytest.mark.parametrize("returncode", (0, 1, 2))
@pytest.mark.parametrize("residue", ("none", "file", "directory"))
def test_child_temp_observer_controls(residue: str, returncode: int) -> None:
    """Standard-library controls exercise tempfile routing, not exporter behavior."""
    with TemporaryDirectory(prefix="observer-control-") as temporary:
        directory = Path(temporary)
        capture = directory / "capture.txt"
        payload = b"caller-owned capture\n"
        capture.write_bytes(payload)
        with TemporaryDirectory(prefix="child-temp-", dir=directory) as child:
            child_temporary = Path(child)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import os, sys, tempfile; "
                    "assert 'sitecustomize' in sys.modules; "
                    "assert tempfile.gettempdir() == sys.argv[1]; "
                    "assert all(os.environ[k] == sys.argv[1] for k in ('TMPDIR','TMP','TEMP')); "
                    "\nwith tempfile.NamedTemporaryFile(): pass"
                    "\nwith tempfile.TemporaryDirectory(): pass"
                    "\nif sys.argv[2] == 'file':"
                    "\n    descriptor, _ = tempfile.mkstemp(); os.close(descriptor)"
                    "\nelif sys.argv[2] == 'directory': tempfile.mkdtemp()"
                    "\nsys.exit(int(sys.argv[3]))",
                    child,
                    residue,
                    str(returncode),
                ],
                cwd=directory,
                env=diagnostic_environment(child_temporary),
                capture_output=True,
                timeout=30,
                check=False,
            )
            assert result.returncode == returncode, result.stderr.decode(errors="replace")
            assert not result.stderr, "observer control failed unexpectedly"
            if residue == "none":
                assert_no_child_residue(directory, child_temporary, {capture}, result.returncode)
            else:
                with pytest.raises(AssertionError, match="child left temporary residue"):
                    assert_no_child_residue(
                        directory, child_temporary, {capture}, result.returncode
                    )
            assert_capture_unchanged(capture, payload)
        assert set(directory.iterdir()) == {capture}
    assert not directory.exists()


def test_repeated_capture_observer_controls() -> None:
    """Exercise real caller redirection twice, then distinguish capture changes."""
    with TemporaryDirectory(prefix="observer-capture-") as temporary:
        directory = Path(temporary)
        capture = directory / "capture.txt"
        payload = b"observer-only stdout\n"
        child_roots: list[Path] = []
        for first in (True, False):
            with TemporaryDirectory(prefix="child-temp-", dir=directory) as child:
                child_temporary = Path(child)
                child_roots.append(child_temporary)
                with capture.open("wb") if first else capture.open("rb") as stream:
                    result = subprocess.run(
                        [sys.executable, "-c", "print('observer-only stdout')"],
                        cwd=directory,
                        env=diagnostic_environment(child_temporary),
                        stdout=stream if first else subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=30,
                        check=False,
                    )
                assert result.returncode == 0, result.stderr.decode(errors="replace")
                assert_no_child_residue(directory, child_temporary, {capture}, result.returncode)
                assert_capture_unchanged(capture, payload)
                if not first:
                    assert result.stdout == payload
            assert set(directory.iterdir()) == {capture}
        assert child_roots[0] != child_roots[1]
        capture.write_bytes(b"changed capture\n")
        with pytest.raises(AssertionError, match="changed caller-owned capture"):
            assert_capture_unchanged(capture, payload)
    assert not directory.exists()


def test_no_success_observer_historical_controls() -> None:
    """Reject the actual public historical documents where still available."""
    for filename, byte_hash, _ in DOCUMENTS.values():
        historical = ROOT / "docs/references/scientific" / filename
        if not historical.exists():
            continue
        payload = historical.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == byte_hash, "historical input changed"
        with pytest.raises(AssertionError, match="dataset document"):
            assert_no_success_document(payload)
        document = parse(payload)
        # Confirm these compact signatures against the exact public inputs.
        container, root_fields, record_fields = next(
            schema for schema in DATASET_SCHEMAS if schema[0] in document
        )
        assert set(document) == root_fields
        assert all(set(record) == record_fields for record in document[container])
        # Full shapes/leaf kinds, not merely rank, come from these public inputs.
        template = dataset_representation(container)
        expected_records = template.pop(container)
        assert complete_representation(document, template)
        assert len(document[container]) == len(expected_records)
        assert all(
            complete_representation(record, expected)
            for record, expected in zip(document[container], expected_records, strict=True)
        )
        assert_dataset_rejection_controls(document)
