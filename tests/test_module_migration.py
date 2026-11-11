"""Owner-approved import layout; these paths remain implementation details.

This structural migration check is separate from the retained public numerical,
file-format, CLI and installed-distribution behavior proofs.
"""

from __future__ import annotations

import importlib
import importlib.util

import pytest

MODULE_MOVES = (
    ("_model", "models"),
    ("_cli", "cli"),
    ("_legacy", "io.priism"),
    ("_pixels", "io.pixels"),
    ("_metadata", "io.metadata"),
    ("_modern", "io.mrc_writer"),
    ("_imagej", "io.imagej"),
    ("_imagej_metadata", "io.imagej_metadata"),
    ("_acquisition", "acquisition.declarations"),
    ("_preparation", "acquisition.preparation"),
    ("_acquisition_layout", "acquisition.layout"),
    ("_acquisition_drift", "acquisition.drift"),
    ("_acquisition_modes", "acquisition.modes"),
    ("_optical_transfer", "optical_transfer"),
    ("_parameter_estimation", "reconstruction.parameter_estimation"),
    ("_known_reconstruction", "reconstruction.known_parameters"),
    ("_workflow", "workflow.reconstruct"),
    ("_workflow_adapters", "workflow.adapters"),
    ("_workflow_config", "workflow.config"),
    ("_workflow_identity", "workflow.identity"),
    ("_workflow_result", "workflow.result"),
    ("_workflow_transfer", "workflow.transfer"),
)

PUBLIC_EXPORTS = frozenset(
    (
        "AcquisitionBands",
        "AcquisitionModeError",
        "ModeEvent",
        "TwoDPlaneInputs",
        "prepare_acquisition_bands",
        "reinterpret_2d_planes",
        "DataBlock",
        "DatasetInfo",
        "EstimatedParameters",
        "ImagejSeries",
        "ImagejWriteReport",
        "KnownReconstruction",
        "OpticalTransfer",
        "OtfError",
        "ParameterEstimationError",
        "PreparedBands",
        "PreparedOtf",
        "RawAcquisition",
        "ReconstructionError",
        "SimreconError",
        "WriteReport",
        "WorkflowError",
        "WorkflowReconstruction",
        "declare_acquisition",
        "declare_otf",
        "estimate_parameters",
        "export_imagej",
        "harmonize",
        "inspect",
        "prepare_bands",
        "prepare_bead_otf",
        "read",
        "reconstruct_known",
        "reconstruct_workflow",
        "sample_otf",
        "write",
    )
)


@pytest.mark.parametrize(("old", "new"), MODULE_MOVES)
def test_approved_module_move_loads_without_compatibility_alias(old: str, new: str) -> None:
    """The approved destination loads, and the removed path cannot resolve."""
    moved = importlib.import_module(f"simrecon.{new}")
    assert moved.__name__ == f"simrecon.{new}"
    assert importlib.util.find_spec(f"simrecon.{old}") is None


def test_root_facade_keeps_exact_supported_exports_and_names() -> None:
    """Module loading must not add supported exports or rename API objects."""
    public = importlib.import_module("simrecon")
    assert len(public.__all__) == len(PUBLIC_EXPORTS) == 36
    assert set(public.__all__) == PUBLIC_EXPORTS
    for name in PUBLIC_EXPORTS:
        assert getattr(public, name).__name__ == name


@pytest.mark.parametrize(
    "name",
    ("AcquisitionModeError", "ParameterEstimationError", "ReconstructionError", "WorkflowError"),
)
def test_public_exception_hierarchies_survive_module_moves(name: str) -> None:
    public = importlib.import_module("simrecon")
    assert issubclass(getattr(public, name), public.SimreconError)
    assert issubclass(public.SimreconError, ValueError)
    assert issubclass(public.OtfError, ValueError)
