"""Selected-coordinate raw adaptation and CE06 one-time band values."""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import numpy as np

from ..acquisition.declarations import RawAcquisition
from ..acquisition.modes import AcquisitionBands
from ..models import DatasetInfo
from .config import _extent, _integer, _scalar
from .identity import freeze_declarations
from .result import raise_workflow_error

_AXES = ("time", "channel", "orientation", "phase", "z", "y", "x")


def _file_input(value: Any) -> bool:
    """Recognize file-like inputs excluded from this pure-array workflow."""
    return isinstance(value, (str, Path, DatasetInfo))


def select_specimen_channel(
    specimen: Any, channel: Any, a: dict[str, Any], identity: dict[str, Any]
) -> tuple[Any, int | None, Any]:
    """Validate raw provenance and select canonical (T,D,P,Z,Y,X) values.

    Selection and transposition may return views. Array-valued metadata is only
    collected here; snapshotting waits for the workflow's geometry/backing checks.
    Explicit pitch and identity declarations must agree with known raw metadata.
    """
    if _file_input(specimen):
        raise_workflow_error("unsupported", "pure-array workflow has no file decoder")
    if type(specimen) is np.ndarray:
        if channel is not None:
            raise_workflow_error("input", "ndarray specimen requires channel_index=None")
        return specimen, None, None
    if type(specimen) is not RawAcquisition:
        raise_workflow_error("input", "specimen requires a plain ndarray or RawAcquisition")
    axes = specimen.axes
    data = specimen.data
    if (
        type(data) is not np.ndarray
        or type(axes) is not tuple
        or len(axes) != data.ndim
        or any(type(v) is not str for v in axes)
        or axes != tuple(v for v in _AXES if v in axes)
        or not {"orientation", "phase", "y", "x"} <= set(axes)
        or any(n < 1 for n in data.shape)
        or specimen.acquisition_kind != "specimen_sim"
    ):
        raise_workflow_error("input", "invalid specimen_sim data/axes/kind")
    source_axes, source_shape = specimen.source_axes, specimen.source_shape
    if (
        type(source_axes) is not tuple
        or len(source_axes) != len(axes)
        or set(source_axes) != set(axes)
        or source_axes[-2:] != ("y", "x")
        or type(source_shape) is not tuple
        or source_shape != tuple(data.shape[axes.index(v)] for v in source_axes)
    ):
        raise_workflow_error("input", "invalid source axes/shape provenance")
    if type(specimen.sampling_um) is not dict or set(specimen.sampling_um) != {"x", "y", "z"}:
        raise_workflow_error("input", "invalid raw sampling declarations")
    for axis, pitch in specimen.sampling_um.items():
        if pitch is not None:
            number = _scalar(pitch, "raw sampling", positive=True, code="input")
            if axis == "z" and "z" not in axes:
                raise_workflow_error("input", "raw z sampling requires z axis")
            expected = a["dz_um"] if axis == "z" else a["dxy_um"]
            if number != expected:
                raise_workflow_error("metadata", "known raw sampling conflicts with explicit pitch")
    for name in ("intensity_unit", "acquisition_id", "calibration_id"):
        value = getattr(specimen, name)
        if value is not None and (type(value) is not str or not value):
            raise_workflow_error("input", "invalid raw identity label")
    if (
        specimen.intensity_unit is not None
        and specimen.intensity_unit != identity["intensity_unit"]
    ):
        raise_workflow_error(
            "metadata", "known raw count-unit label conflicts with specimen identity"
        )
    if (
        type(specimen.original_config) is not dict
        or type(specimen.original_metadata) is not dict
        or type(specimen.provenance) is not tuple
    ):
        raise_workflow_error("input", "invalid raw metadata/provenance")
    for event in specimen.provenance:
        if (
            type(event) is not dict
            or set(event) != {"field", "old", "new", "source"}
            or type(event["field"]) is not str
            or event["source"] not in ("config", "override")
        ):
            raise_workflow_error("input", "invalid raw provenance event")
    if not specimen.provenance:
        raise_workflow_error("input", "missing raw declaration provenance")
    channels = data.shape[axes.index("channel")] if "channel" in axes else 1
    if type(specimen.wavelengths_nm) is not dict:
        raise_workflow_error("input", "invalid generic raw wavelengths")
    for key, value in specimen.wavelengths_nm.items():
        if (
            type(key) is not str
            or not key.isdecimal()
            or str(int(key)) != key
            or int(key) >= channels
        ):
            raise_workflow_error("input", "invalid generic wavelength channel")
        # Generic wavelengths are neutral metadata, not source optical inputs.
        if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
            raise_workflow_error("input", "invalid generic raw wavelength")
    nominal = specimen.nominal_phases_rad
    phase_axes = tuple(v for v in axes if v in _AXES[:4])
    if nominal is None:
        if specimen.nominal_phase_axes != ():
            raise_workflow_error("input", "invalid absent nominal phase axes")
    elif (
        type(nominal) is not np.ndarray
        or nominal.dtype != np.float64
        or specimen.nominal_phase_axes != phase_axes
        or nominal.shape != tuple(data.shape[axes.index(v)] for v in phase_axes)
    ):
        raise_workflow_error("input", "invalid nominal command metadata")
    _extent(data.shape, max(8, data.dtype.itemsize))
    # Defer array-valued metadata materialization until the selected source
    # geometry, raw backings and native extents have passed workflow validation.
    metadata = {f.name: getattr(specimen, f.name) for f in fields(specimen) if f.name != "data"}
    selected_channel = None
    if "channel" in axes:
        selected_channel = _integer(channel, "channel_index", 0, code="input")
        if selected_channel >= channels:
            raise_workflow_error("input", "channel_index is outside the original channel axis")
        selection: list[Any] = [slice(None)] * data.ndim
        selection[axes.index("channel")] = selected_channel
        data = data[tuple(selection)]
        axes = tuple(v for v in axes if v != "channel")
    elif channel is not None:
        raise_workflow_error("input", "absent channel axis requires channel_index=None")
    if "z" not in axes and a["acquisition_mode"] != "2d":
        raise_workflow_error("input", "absent z is permitted only for declared true2d")
    for axis in ("time", "z"):
        if axis not in axes:
            data = np.expand_dims(data, 0)
            axes = (axis, *axes)
    target = ("time", "orientation", "phase", "z", "y", "x")
    return data.transpose(tuple(axes.index(v) for v in target)), selected_channel, metadata


def snapshot_raw_metadata(metadata: Any) -> Any:
    """Check nominal command values and freeze the previously selected metadata.

    The workflow calls this after source geometry and backing-array checks;
    freezing recursively snapshots declarations rather than executing a stage.
    """
    if metadata is None:
        return None
    nominal = metadata["nominal_phases_rad"]
    if nominal is not None:
        _extent(nominal.shape, nominal.dtype.itemsize)
        if not np.isfinite(nominal).all():
            raise_workflow_error("input", "invalid nominal command metadata")
    return freeze_declarations(metadata, code="input")


def select_time_bands(bands: AcquisitionBands, time: int) -> AcquisitionBands:
    """Select a one-time AcquisitionBands record without replaying preparation.

    Array slices retain stage buffers as views. Time-indexed diagnostics are
    selected and their time indices rebased to zero for reconstruct_known;
    scientific recurrences have already run across the original acquisition.
    """
    names = (
        "quadratures",
        "noise_variance_factors",
        "separation_matrices",
        "phase_angles_rad",
        "frame_sums",
        "equalization_gains",
        "off_frame_sums",
        "off_equalization_gains",
        "off_quadratures",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
    )
    values = {
        name: None if getattr(bands, name) is None else getattr(bands, name)[time : time + 1]
        for name in names
    }
    header = bands.header_timestamps_after
    if header is not None:
        header = header[: header.size // bands.input_shape[0]]
    return replace(
        bands,
        **values,
        phase_policies=bands.phase_policies[time : time + 1],
        input_shape=(1, *bands.input_shape[1:]),
        header_timestamps_after=header,
        sentinel_frames=tuple((0, *item[1:]) for item in bands.sentinel_frames if item[0] == time),
        trace=tuple(
            replace(event, time_index=0) for event in bands.trace if event.time_index == time
        ),
    )
