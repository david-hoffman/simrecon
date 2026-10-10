"""Own raw sample storage and explicit acquisition declarations in memory."""

import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError

_AXES = ("time", "channel", "orientation", "phase", "z", "y", "x")
_OPTIONAL = {
    "sampling_um",
    "wavelengths_nm",
    "nominal_phases_rad",
    "intensity_unit",
    "acquisition_id",
    "calibration_id",
}
_REQUIRED = {"version", "acquisition_kind", "axes"}


@dataclass(frozen=True)
class RawAcquisition:
    """Owned samples, resolved declarations and independent raw snapshots.

    Record bindings are frozen. Buffers remain mutable, and metadata is
    read-only by convention. Declarations establish no experimental validity.
    """

    data: npt.NDArray[Any]
    axes: tuple[str, ...]
    source_axes: tuple[str, ...]
    source_shape: tuple[int, ...]
    acquisition_kind: str
    sampling_um: dict[str, float | None]
    wavelengths_nm: dict[str, float]
    nominal_phases_rad: npt.NDArray[np.float64] | None
    nominal_phase_axes: tuple[str, ...]
    intensity_unit: str | None
    acquisition_id: str | None
    calibration_id: str | None
    original_config: dict[str, Any]
    original_metadata: dict[str, Any]
    provenance: tuple[dict[str, Any], ...]


def _snapshot(value: Any, *, code: str, allow_bytes: bool, active: set[int]) -> Any:
    """Copy supported built-in values without interpreting opaque leaves."""
    if type(value) in (str, bool, int, float, type(None)) or (allow_bytes and type(value) is bytes):
        return value
    if type(value) not in (dict, list, tuple):
        raise SimreconError(code, "snapshot values must be supported built-in types")
    if id(value) in active:
        raise SimreconError(code, "snapshot values must be acyclic")
    active.add(id(value))
    try:
        if type(value) is dict:
            return _mapping_snapshot(value, code=code, allow_bytes=allow_bytes, active=active)
        copied = [
            _snapshot(item, code=code, allow_bytes=allow_bytes, active=active) for item in value
        ]
        return tuple(copied) if type(value) is tuple else copied
    finally:
        active.remove(id(value))


def _mapping_snapshot(
    value: Mapping[str, object], *, code: str, allow_bytes: bool, active: set[int]
) -> dict[str, Any]:
    """Snapshot a mapping root; only built-in containers are allowed beneath it."""
    result = {}
    for key, item in value.items():
        if type(key) is not str:
            raise SimreconError(code, "snapshot mapping keys must be strings")
        result[key] = _snapshot(item, code=code, allow_bytes=allow_bytes, active=active)
    return result


def _root_snapshot(value: object, *, code: str, allow_bytes: bool = False) -> dict[str, Any]:
    """Accept a Mapping root without adopting custom nested object protocols."""
    if not isinstance(value, Mapping):
        raise SimreconError(code, "expected a mapping")
    return _mapping_snapshot(value, code=code, allow_bytes=allow_bytes, active={id(value)})


def _number(value: object, *, code: str, positive: bool) -> float:
    """Convert a plain number once, rejecting unrepresentable binary64 values."""
    if type(value) is not int and type(value) is not float:
        raise SimreconError(code, "expected a plain integer or float")
    try:
        represented = float(value)
    except OverflowError as error:
        raise SimreconError(code, "number is outside binary64 range") from error
    if not math.isfinite(represented) or (positive and represented <= 0):
        raise SimreconError(code, "number must be finite and positive" if positive else "finite")
    return represented


def _sampling(value: Any, axes: tuple[str, ...]) -> dict[str, float | None]:
    """Resolve sparse explicit micrometre declarations, leaving unknowns None."""
    code = "invalid_acquisition_sampling"
    result: dict[str, float | None] = dict.fromkeys(("x", "y", "z"))
    if value is None:
        return result
    if type(value) is not dict or not value.keys() <= result.keys():
        raise SimreconError(code, "sampling must map only x/y/z")
    for axis, number in value.items():
        if number is not None:
            if axis == "z" and "z" not in axes:
                raise SimreconError(code, "z sampling requires a declared z axis")
            result[axis] = _number(number, code=code, positive=True)
    return result


def _wavelengths(value: Any, channel_count: int) -> dict[str, float]:
    """Resolve sparse generic wavelengths without assigning optical roles."""
    code = "invalid_acquisition_wavelengths"
    if value is None:
        return {}
    if type(value) is not dict:
        raise SimreconError(code, "wavelengths must be a mapping")
    result = {}
    upper = str(channel_count)
    for key, number in value.items():
        # Compare decimal strings before parsing: arbitrarily long invalid keys
        # cannot hit Python's unrelated integer-string conversion limit.
        if (
            not key
            or any(char not in "0123456789" for char in key)
            or (len(key) > 1 and key[0] == "0")
            or len(key) > len(upper)
            or (len(key) == len(upper) and key >= upper)
        ):
            raise SimreconError(code, "wavelength key must name an existing channel")
        result[key] = _number(number, code=code, positive=True)
    return result


def _command_leaves(value: Any, shape: tuple[int, ...]) -> Iterator[float]:
    """Validate every required group dimension and convert finite command leaves."""
    code = "invalid_acquisition_phase_commands"
    if not shape:
        yield _number(value, code=code, positive=False)
        return
    if type(value) not in (list, tuple) or len(value) != shape[0]:
        raise SimreconError(code, "commands must match every declared group dimension")
    for item in value:
        yield from _command_leaves(item, shape[1:])


def _commands(
    value: Any, kind: str, source_axes: tuple[str, ...], source_shape: tuple[int, ...]
) -> tuple[npt.NDArray[np.float64] | None, tuple[str, ...]]:
    """Own the complete command tensor in canonical declared group-axis order."""
    if value is None:
        return None, ()
    if kind == "detection_psf":
        raise SimreconError("invalid_acquisition_phase_commands", "PSF commands must be absent")
    groups = tuple(axis for axis in source_axes if axis not in ("z", "y", "x"))
    shape = tuple(source_shape[source_axes.index(axis)] for axis in groups)
    canonical = tuple(axis for axis in _AXES[:4] if axis in groups)
    source = np.array(list(_command_leaves(value, shape)), dtype=np.float64).reshape(shape)
    permutation = tuple(groups.index(axis) for axis in canonical)
    return np.array(source.transpose(permutation), order="C", copy=True), canonical


def _optional_string(value: Any) -> str | None:
    """Preserve opaque nonempty string declarations, including whitespace."""
    if value is not None and (type(value) is not str or not value):
        raise SimreconError(
            "invalid_acquisition_config", "optional labels must be nonempty strings"
        )
    return value


def _sample_copy(data: npt.NDArray[Any], permutation: tuple[int, ...]) -> npt.NDArray[Any]:
    """Copy complete element storage as opaque bytes, including float padding."""
    result = np.empty(
        tuple(data.shape[index] for index in permutation), dtype=data.dtype, order="C"
    )
    storage = np.dtype(f"V{data.dtype.itemsize}")
    # Equal-size void views preserve arbitrary source strides and byte order.
    # Assignment copies storage instead of evaluating floating-point samples.
    np.copyto(result.view(storage), data.view(storage).transpose(permutation))
    return result


def declare_acquisition(
    data: npt.NDArray[Any],
    *,
    config: Mapping[str, object],
    original_metadata: Mapping[str, object] | None = None,
) -> RawAcquisition:
    """Own samples and explicit declarations without scientific interpretation.

    Parameters
    ----------
    data : numpy.ndarray
        Plain integer or floating samples, any width/byte order/strides, with
        positive dimensions. All floating storage patterns are accepted.
    config : Mapping[str, object]
        Version 1 declarations with acquisition_kind and source axes. Axes
        end in y,x; preceding names are time/channel/orientation/phase/z.
        SIM kinds require orientation and phase; detection_psf forbids them.
        Optional metadata and whole-field overrides use built-in values.
    original_metadata : Mapping[str, object] or None, optional
        Opaque built-in values, including bytes/nonfinite floats, independently
        snapshotted without supplying implicit declarations. Defaults to {}.

    Returns
    -------
    RawAcquisition
        Mutable owned C-contiguous samples with identical element storage in
        canonical declared axis order, resolved metadata, optional owned
        float64 nominal commands and independent raw snapshots/provenance.

    Raises
    ------
    SimreconError
        Stable invalid_acquisition_* code for the rejected declaration field.
        Allocation and unrelated exceptions propagate unchanged.

    Notes
    -----
    No file I/O, solver, calibration, correction, resampling or intensity
    arithmetic occurs. Sampling is explicitly in micrometres; wavelengths
    remain generic nanometres; nominal phase commands are not measured truth.
    No absent axis or scientific setting is inferred. Inputs, NumPy error
    modes and unrelated warning channels are preserved. One full owned sample
    copy plus metadata/scratch is required; no streaming memory bound applies.
    """
    if type(data) is not np.ndarray:
        raise SimreconError("invalid_acquisition_data", "data must be a plain ndarray")
    if data.dtype.kind not in "iuf":
        raise SimreconError("invalid_acquisition_dtype", "samples must have dtype kind i/u/f")
    original_config = _root_snapshot(config, code="invalid_acquisition_config")
    if (
        not original_config.keys() >= _REQUIRED
        or not original_config.keys() <= _REQUIRED | _OPTIONAL | {"overrides"}
        or type(original_config["version"]) is not int
        or original_config["version"] != 1
    ):
        raise SimreconError("invalid_acquisition_config", "invalid version or config schema")
    overrides = original_config.get("overrides", {})
    if type(overrides) is not dict or not overrides.keys() <= _OPTIONAL:
        raise SimreconError("invalid_acquisition_config", "invalid override schema")
    declared_axes = original_config["axes"]
    if (
        type(declared_axes) is not list
        or any(type(axis) is not str or axis not in _AXES for axis in declared_axes)
        or declared_axes[-2:] != ["y", "x"]
        or len(set(declared_axes)) != len(declared_axes)
    ):
        raise SimreconError("invalid_acquisition_axes", "axes must be unique and end in y,x")
    source_axes = tuple(declared_axes)
    if len(source_axes) != data.ndim or any(count <= 0 for count in data.shape):
        raise SimreconError(
            "invalid_acquisition_shape", "axes must match positive sample dimensions"
        )
    kind = original_config["acquisition_kind"]
    if (
        kind not in ("specimen_sim", "sim_beads", "detection_psf")
        or (
            kind == "detection_psf"
            and any(axis in source_axes for axis in ("orientation", "phase"))
        )
        or (kind != "detection_psf" and not {"orientation", "phase"} <= set(source_axes))
    ):
        raise SimreconError("invalid_acquisition_kind", "unsupported kind or kind-axis profile")
    effective = {**original_config, **overrides}
    sampling = _sampling(effective.get("sampling_um"), source_axes)
    channels = data.shape[source_axes.index("channel")] if "channel" in source_axes else 1
    wavelengths = _wavelengths(effective.get("wavelengths_nm"), channels)
    commands, command_axes = _commands(
        effective.get("nominal_phases_rad"), kind, source_axes, data.shape
    )
    intensity_unit = _optional_string(effective.get("intensity_unit"))
    acquisition_id = _optional_string(effective.get("acquisition_id"))
    calibration_id = _optional_string(effective.get("calibration_id"))
    metadata = _root_snapshot(
        {} if original_metadata is None else original_metadata,
        code="invalid_acquisition_metadata",
        allow_bytes=True,
    )
    provenance = tuple(
        {
            "field": name,
            "old": None,
            "new": _snapshot(
                original_config[name],
                code="invalid_acquisition_config",
                allow_bytes=False,
                active=set(),
            ),
            "source": "config",
        }
        for name in sorted(original_config.keys() - {"version", "overrides"})
    ) + tuple(
        {
            "field": name,
            "old": _snapshot(
                original_config.get(name),
                code="invalid_acquisition_config",
                allow_bytes=False,
                active=set(),
            ),
            "new": _snapshot(
                overrides[name], code="invalid_acquisition_config", allow_bytes=False, active=set()
            ),
            "source": "override",
        }
        for name in sorted(overrides)
    )
    axes = tuple(axis for axis in _AXES if axis in source_axes)
    samples = _sample_copy(data, tuple(source_axes.index(axis) for axis in axes))
    return RawAcquisition(
        data=samples,
        axes=axes,
        source_axes=source_axes,
        source_shape=data.shape,
        acquisition_kind=kind,
        sampling_um=sampling,
        wavelengths_nm=wavelengths,
        nominal_phases_rad=commands,
        nominal_phase_axes=command_axes,
        intensity_unit=intensity_unit,
        acquisition_id=acquisition_id,
        calibration_id=calibration_id,
        original_config=original_config,
        original_metadata=metadata,
        provenance=provenance,
    )
