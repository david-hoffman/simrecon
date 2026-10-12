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
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
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


def diagnostic_environment() -> dict[str, str]:
    """Inherit diagnostics and ensure all child interpreters install the harness."""
    assert "sitecustomize" in sys.modules, "run via scripts/source_free_check.py"
    result = os.environ.copy()
    site = str(ROOT / "scripts/source_free_sitecustomize")
    previous = result.get("PYTHONPATH", "")
    result["PYTHONPATH"] = site + (os.pathsep + previous if previous else "")
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    result["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + result.get("PATH", "")
    return result


def run(arguments: list[str], directory: Path, *, stdout: Any = subprocess.PIPE) -> Any:
    return subprocess.run(
        [sys.executable, str(EXPORTER), *arguments],
        cwd=directory,
        env=diagnostic_environment(),
        stdout=stdout,
        stderr=subprocess.PIPE,
        timeout=240,
        check=False,
    )


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


def assert_no_success_document(payload: bytes) -> None:
    """Error diagnostic prose/streams are unspecified; a dataset is not success."""
    try:
        document = json.loads(payload)
    except (ValueError, UnicodeError):
        return
    assert not (isinstance(document, dict) and {"fixtures", "entries"}.intersection(document)), (
        "rejection emitted a dataset document"
    )


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
        assert sorted(path.name for path in directory.iterdir()) == [capture.name]
        yield selector, document
    assert not directory.exists(), "caller TemporaryDirectory did not clean up"


def test_complete_historical_representation(exported: tuple[str, Any]) -> None:
    """All fields/types/order/strings/float bits, including historic provenance."""
    selector, document = exported
    filename, byte_hash, representation_hash = DOCUMENTS[selector]
    assert digest(document) == representation_hash, "complete historical representation mismatch"
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
    for payload in (b"", b"selector error\n", b'{"error":"selector"}'):
        assert_no_success_document(payload)
    for payload in (b'{"fixtures":[]}', b'{"entries":[]}'):
        with pytest.raises(AssertionError, match="dataset document"):
            assert_no_success_document(payload)
