"""Real neutral file/declaration composition, unchanged retirement and docs."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect as signature_inspection
import re
import struct
from pathlib import Path

import numpy as np
import pytest

from c_workflow_oracle import array_digest, constant_case, coordinate_case, observe
from c_workflow_support import assert_scientific, entry, keywords, public
from test_c_workflow_validation import assert_error


def legacy_bytes(raw: np.ndarray, byte_order: str = "<") -> bytes:
    """Independent 1024-byte public format fixture, source planes phase,z."""
    _, _, p, z, y, x = raw.shape
    header = bytearray(1024)
    for offset, values in ((0, (x, y, p * z, 6)), (28, (x, y, z)), (64, (1, 2, 3)), (92, (0,))):
        struct.pack_into(byte_order + "i" * len(values), header, offset, *values)
    struct.pack_into(byte_order + "fff", header, 40, 1.0, 1.0, 1.0)
    struct.pack_into(byte_order + "h", header, 96, -16224)
    for offset, value in ((180, 1), (182, 0), (196, 1), (198, 777)):
        struct.pack_into(byte_order + "h", header, offset, value)
    return bytes(header) + raw[0, 0].astype(np.dtype(byte_order + "u2")).tobytes()


@pytest.mark.parametrize("byte_order", ["<", ">"])
def test_actual_file_read_declaration_and_workflow_keep_unsigned_pixels(
    tmp_path: Path, byte_order: str
) -> None:
    case = coordinate_case()
    payload = legacy_bytes(case.raw, byte_order)
    source = tmp_path / "explicit-raw.mrc"
    source.write_bytes(payload)
    info = public().inspect(source)
    config = dict(
        version=1,
        data_kind="spatial_image",
        plane_axes=["phase", "orientation", "z"],
        plane_shape=[3, 1, 2],
        spatial_fields="direct_um",
        extended_header="none",
        overrides={},
    )
    resolved = public().harmonize(info, config=config)
    with pytest.raises(TypeError):
        public().read(resolved)
    block = public().read(resolved, plane_start=0, plane_stop=6)
    assert block.data.dtype == np.dtype("uint16")
    np.testing.assert_array_equal(block.data.reshape(3, 2, 2, 4), case.raw[0, 0])
    record = public().declare_acquisition(
        block.data.reshape(resolved.shape),
        config=dict(
            version=1,
            acquisition_kind="specimen_sim",
            axes=list(resolved.axes),
            sampling_um=dict(x=1.0, y=1.0, z=1.0),
            intensity_unit="detector-counts",
        ),
        original_metadata=dict(
            header=resolved.original_header,
            source_layout=config,
            provenance=[dict(item) for item in resolved.provenance],
        ),
    )
    kwargs = keywords(case)
    kwargs["specimen_identity"]["files"] = [
        dict(
            name=source.name,
            bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            role="specimen",
        )
    ]
    assert record.axes == ("orientation", "phase", "z", "y", "x")
    np.testing.assert_array_equal(record.data, case.raw[0])
    result = entry()(record, **kwargs)
    assert_scientific(case, result, observe(case))
    selected_identity = next(
        item for item in result.input_identities if item.name == "selected_specimen"
    )
    assert (
        selected_identity.shape,
        selected_identity.dtype,
        selected_identity.sha256,
    ) == array_digest(case.raw)
    declarations = repr(result.source_declarations)
    assert str(tmp_path) not in declarations
    assert hashlib.sha256(payload).hexdigest() in declarations
    assert result.intensity_unit == "detector-counts"
    assert_error("workflow_unsupported", resolved, kwargs)


def test_neutral_unresolved_and_changed_source_fail_before_workflow(tmp_path: Path) -> None:
    # Neutral failure is not reclassified as a workflow/scientific failure.
    case = constant_case()
    source = tmp_path / "changed-raw.mrc"
    source.write_bytes(legacy_bytes(case.raw))
    info = public().inspect(source)
    with pytest.raises(public().SimreconError):
        public().read(info, plane_start=0, plane_stop=1)
    resolved = public().harmonize(
        info,
        config=dict(
            version=1,
            data_kind="spatial_image",
            plane_axes=["phase", "z"],
            plane_shape=[3, 2],
            spatial_fields="direct_um",
            extended_header="none",
        ),
    )
    source.write_bytes(source.read_bytes()[:-2])
    with pytest.raises(public().SimreconError) as caught:
        public().read(resolved, plane_start=0, plane_stop=1)
    assert caught.value.code == "source_changed"


def test_exact_workflow_signature_and_new_public_types() -> None:
    function = entry()
    expected = (
        "specimen",
        "acquisition",
        "optics",
        "carrier",
        "filtering",
        "specimen_identity",
        "transfer",
        "calibration",
        "transfer_identity",
        "off_exposures",
        "exposure_background",
        "header_timestamps",
        "header_timestamp_unit",
        "header_phases_rad",
        "channel_index",
        "plane_policy",
    )
    signature = signature_inspection.signature(function)
    assert tuple(signature.parameters) == expected
    for i, parameter in enumerate(signature.parameters.values()):
        assert parameter.kind == (
            parameter.POSITIONAL_OR_KEYWORD if i == 0 else parameter.KEYWORD_ONLY
        )
    assert signature.parameters["plane_policy"].default == "native"
    for name in ("WorkflowReconstruction", "WorkflowError"):
        assert isinstance(getattr(public(), name, None), type)
    assert issubclass(public().WorkflowError, public().SimreconError)
    assert issubclass(public().WorkflowError, ValueError)


def test_retired_science_does_not_return_and_neutral_boundaries_remain() -> None:
    module = public()
    for name in ("reconstruct", "reconstruct_volume", "prepare_otf"):
        assert not hasattr(module, name)
    for name in ("simrecon._otf", "simrecon._reconstruction", "simrecon._drift"):
        assert importlib.util.find_spec(name) is None
    for name in ("inspect", "harmonize", "read", "write", "declare_acquisition", "export_imagej"):
        assert callable(getattr(module, name, None))
    # Compatibility smoke only. Existing accepted CE01/file/export tests own
    # the complete neutral/installed-wheel/module retirement proof.


def test_approved_usage_keeps_explicit_workflow_and_claim_limits() -> None:
    text = Path("docs/usage/c-workflow.md").read_text()
    for word in (
        "reconstruct_workflow",
        "specimen_identity",
        "transfer_identity",
        "phase_policy",
        "channel_index",
        "header_timestamp_unit",
        "literal-2d-stack",
        "PreparedOtf",
        "dimensionless-transfer",
        "edge_pixels=10",
        "resolution",
        "historical executable",
    ):
        assert word in text
    examples = re.findall(r"```python\n(.*?)```", text, flags=re.S)
    assert examples
    for example in examples:
        tree = ast.parse(example)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "reconstruct_workflow"
        ]
        assert calls
        for call in calls:
            keys = {keyword.arg for keyword in call.keywords}
            assert {"acquisition", "optics", "carrier", "filtering", "specimen_identity"} <= keys
    contract = Path("docs/contracts/c-equivalence-workflow-v1.md").read_text()
    assert (
        "header_timestamp_unit" in contract
        and "detector-pixels/(declared-clock-unit**j)" in contract
    )
    assert "unused_sections=(6,)" in contract
