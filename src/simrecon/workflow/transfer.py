"""Empirical selection, accepted-record snapshots and decoded-section binding."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from ..optical_transfer import (
    OpticalTransfer,
    OtfError,
    PreparedOtf,
    _values,
    declare_otf,
    prepare_bead_otf,
    validate_optical_transfer,
)
from .adapters import _file_input
from .config import (
    _array,
    _enum,
    _extent,
    _flags,
    _integer,
    _optics,
    _scalar,
    _schema,
    _signed,
)
from .identity import freeze_declarations, owned_readonly_array, validate_source_identity
from .result import WorkflowError, raise_workflow_error, workflow_stage

_CAL_REQUIRED = (
    "dxy_um",
    "dz_um",
    "linespacing_um",
    "wavelength_nm",
    "numerical_aperture",
    "immersion_index",
)
_CAL_DEFAULTS = dict(
    bead_diameter_um=0.12,
    carrier_angle_rad=0.0,
    background_counts=None,
    background_map=None,
    slope_map=None,
    exposure_background_counts=None,
    compensate_bead=True,
    fix_axial_axis=True,
    fix_radial_from=0,
    cleanup_axial_bins=(0, 0, 0),
    origin_fit_bins=None,
    rescale_each=False,
    forced_pi_shift=False,
    conjugate=False,
)
_CAL_FLAGS = ("compensate_bead", "fix_axial_axis", "rescale_each", "forced_pi_shift", "conjugate")
_CAL_ARRAYS = (
    "center_pixels_xyz",
    "background_counts",
    "phase_angles_rad",
    "quadratures",
    "normalization_factors",
    "quadrature_angles_rad",
)


@dataclass(frozen=True)
class _TransferInputs:
    """Validated backing values; no scientific preparation or table copies."""

    selection: str
    value: Any
    settings: dict[str, Any]
    calibration_identity: Any = None
    transfer_identity: Any = None
    binding: Any = None


def _bins(value: Any, name: str, length: int) -> tuple[int, ...]:
    """Require a fixed-length sequence of nonnegative signed32 bin indices."""
    if type(value) not in (tuple, list) or len(value) != length:
        raise_workflow_error("config", f"{name} requires {length} integer entries")
    return tuple(_integer(v, name, 0) for v in value)


def _calibration_settings(
    value: Any, shape: tuple[int, ...], optics: dict[str, Any]
) -> dict[str, Any]:
    """Validate empirical bead settings and matching optics before preparation."""
    settings = _schema(value, "calibration.settings", _CAL_REQUIRED, _CAL_DEFAULTS)
    declared = _optics({k: settings[k] for k in optics}, "calibration.settings.optics")
    settings.update(declared)
    if declared != optics:
        raise_workflow_error("metadata", "calibration optics conflict with specimen optics")
    p, z, y, x = shape
    for name in ("dxy_um", "dz_um", "linespacing_um", "bead_diameter_um", "carrier_angle_rad"):
        settings[name] = _scalar(
            settings[name], name, positive=name in ("dxy_um", "dz_um", "linespacing_um")
        )
    if settings["bead_diameter_um"] < 0:
        raise_workflow_error("config", "bead diameter must be nonnegative")
    _flags(settings, _CAL_FLAGS)
    if settings["compensate_bead"] and (settings["bead_diameter_um"] == 0 or p == 1):
        raise_workflow_error(
            "config", "compensation requires positive diameter and multiple phases"
        )
    if settings["background_counts"] is not None:
        background = _scalar(settings["background_counts"], "background_counts")
        if background < 0:
            raise_workflow_error("config", "calibration background must be nonnegative")
        settings["background_counts"] = background
    for name, sh in (
        ("background_map", (y, x)),
        ("slope_map", (y, x)),
        ("exposure_background_counts", (z, p)),
    ):
        if settings[name] is not None:
            _array(settings[name], "calibration.settings." + name, sh)
    if (settings["background_map"] is None) != (settings["slope_map"] is None):
        raise_workflow_error("config", "calibration camera maps must be paired")
    settings["fix_radial_from"] = _integer(settings["fix_radial_from"], "fix_radial_from", 0)
    settings["cleanup_axial_bins"] = _bins(settings["cleanup_axial_bins"], "cleanup_axial_bins", 3)
    if settings["origin_fit_bins"] is not None:
        bins = _bins(settings["origin_fit_bins"], "origin_fit_bins", 2)
        if not 1 <= bins[0] < bins[1] <= x // 2:
            raise_workflow_error("config", "origin fit requires 1<=a<b<=X/2")
        settings["origin_fit_bins"] = bins
    return settings


def _validate_transfer(value: OpticalTransfer) -> OpticalTransfer:
    """Validate actual transfer backing storage and translate transfer errors."""
    try:
        checked = validate_optical_transfer(value, require_actual=True)
    except OtfError as error:
        code = "workflow_representation" if "representation" in str(error) else "workflow_input"
        raise WorkflowError(code, str(error), stage="transfer") from error
    # The validator returns the actual ndarray it inspected, without narrowing.
    return replace(value, samples=checked.samples)


def _validate_prepared(value: PreparedOtf, optics: dict[str, Any]) -> PreparedOtf:
    """Check prepared radial diagnostics/settings against the selected optics."""
    transfer = _validate_transfer(value.transfer)
    if transfer.layout != "radial":
        raise_workflow_error(
            "input", "PreparedOtf requires radial transfer diagnostics", "transfer"
        )
    o, r, k = transfer.samples.shape
    p = 2 * o - 1
    shapes = ((3,), (k, p), (p,), (p, r, k), (p,), (o - 1,))
    for name, shape in zip(_CAL_ARRAYS, shapes, strict=True):
        array = getattr(value, name)
        _extent(shape, 16 if name == "quadratures" else 8, "transfer")
        dtype = np.dtype("complex128" if name == "quadratures" else "float64")
        if (
            type(array) is not np.ndarray
            or array.shape != shape
            or array.dtype != dtype
            or not array.flags.owndata
            or array.flags.writeable
            or not np.isfinite(array).all()
        ):
            raise_workflow_error("input", f"invalid PreparedOtf.{name}", "transfer")
    if type(value.resolved_settings) is not tuple or any(
        type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str
        for pair in value.resolved_settings
    ):
        raise_workflow_error("input", "invalid PreparedOtf resolved settings", "transfer")
    settings = dict(value.resolved_settings)
    expected = (set(_CAL_REQUIRED) | set(_CAL_DEFAULTS) | {"background_policy"}) - {
        "background_map",
        "slope_map",
        "exposure_background_counts",
    }
    if len(settings) != len(value.resolved_settings) or set(settings) != expected:
        raise_workflow_error("input", "invalid PreparedOtf resolved setting schema", "transfer")
    try:
        declared = _optics({key: settings[key] for key in optics})
        for name in ("dxy_um", "dz_um", "linespacing_um", "bead_diameter_um", "carrier_angle_rad"):
            _scalar(settings[name], name, positive=name in ("dxy_um", "dz_um", "linespacing_um"))
        _flags(settings, _CAL_FLAGS)
        _integer(settings["fix_radial_from"], "fix_radial_from", 0)
        _bins(settings["cleanup_axial_bins"], "cleanup_axial_bins", 3)
        if settings["origin_fit_bins"] is not None:
            _bins(settings["origin_fit_bins"], "origin_fit_bins", 2)
        if (
            settings["background_counts"] is not None
            and _scalar(settings["background_counts"], "background_counts") < 0
        ):
            raise_workflow_error("input", "invalid prepared background")
        if settings["bead_diameter_um"] < 0 or settings["background_policy"] not in (
            "exposure",
            "maps",
            "scalar",
            "auto",
        ):
            raise_workflow_error("input", "invalid prepared setting domain")
    except WorkflowError as error:
        raise WorkflowError("workflow_input", str(error), stage="transfer") from error
    if declared != optics:
        raise_workflow_error(
            "metadata", "embedded PreparedOtf optics conflict with workflow optics", "transfer"
        )
    return replace(value, transfer=transfer)


def _decoded_inputs(value: Any, mode: str, orders: int) -> _TransferInputs:
    """Validate decoded section storage and declare the source-to-order binding.

    No file decoder runs here. Counts/target extents precede array-sized checks,
    and unused sections remain explicit in the returned binding declaration.
    """
    declaration = _schema(
        value,
        "transfer",
        ("kind", "layout", "samples", "dkr_cyc_um", "dkz_cyc_um", "order_encoding"),
    )
    _enum(declaration["kind"], "transfer.kind", ("decoded-sections",))
    _enum(declaration["order_encoding"], "order_encoding", ("combined-orders",))
    layout = _enum(declaration["layout"], "transfer.layout", ("radial", "full"))
    dkr = _scalar(declaration["dkr_cyc_um"], "dkr_cyc_um", positive=True)
    dkz = _scalar(declaration["dkz_cyc_um"], "dkz_cyc_um", positive=True)
    array = declaration["samples"]
    if type(array) is not np.ndarray or array.ndim != 3 or any(n < 1 for n in array.shape):
        raise_workflow_error("input", "decoded samples require nonempty (S,V,U)", "transfer")
    s, v, u = array.shape
    for count in (s, v, u, v * u):
        _signed(count, "decoded section extent")
    _extent(array.shape, 16, "transfer")
    if mode == "2d" and dkz != 1:
        raise_workflow_error("config", "decoded 2d requires dkz exactly 1", "transfer")
    if mode == "2d" and layout == "radial" and v != 1:
        raise_workflow_error(
            "representation", "radial2d decoded plane exceeds loader allocation", "transfer"
        )
    if mode == "3d" and layout == "full":
        k = s // orders
        if k == 0:
            raise_workflow_error(
                "representation", "full3d decoded quotient K0 has no axial sample", "transfer"
            )
        _signed(k * v * u, "full per-order cells")
        _extent((orders, k, v, u), 16, "transfer")
        _extent((orders, k), 8, "transfer")
        section_map: Any = tuple(tuple(range(m * k, (m + 1) * k)) for m in range(orders))
        unused = tuple(range(orders * k, s))
    else:
        section_map = tuple(m if m < s else 0 for m in range(orders))
        unused = tuple(range(orders, s))
        target = (
            (orders, u, 1)
            if mode == "2d" and layout == "radial"
            else (orders, 1, v, u)
            if mode == "2d"
            else (orders, v, u)
        )
        _extent(target, 16, "transfer")
    # Source counts, original storage and mapped targets precede all array-sized
    # validation scratch, exact-representation conversion, indexing and hashing.
    _array(array, "transfer.samples", array.shape, code="input", complex_ok=True)
    try:
        _values(array, "transfer.samples", exact=True, complex_ok=True, wide_bound=True)
    except OtfError as error:
        raise WorkflowError("workflow_input", str(error), stage="transfer") from error
    binding = tuple(
        dict(
            original_shape=array.shape,
            layout=layout,
            effective_mode=mode,
            section_map=section_map,
            unused_sections=unused,
            dkr_cyc_um=dkr,
            dkz_cyc_um=dkz,
        ).items()
    )
    return _TransferInputs(
        "decoded-sections",
        array,
        dict(layout=layout, dkr_cyc_um=dkr, dkz_cyc_um=dkz),
        binding=binding,
    )


def validate_transfer_inputs(
    transfer: Any,
    calibration: Any,
    transfer_identity: Any,
    optics: dict[str, Any],
    mode: str,
    orders: int,
) -> _TransferInputs:
    """Validate the selected transfer alternative before copies, hashes or stages.

    Return checked backings and declarations for raw beads, decoded sections or
    accepted records. Scientific materialization is deferred to resolution.
    """
    if calibration is not None:
        cal = _schema(calibration, "calibration", ("raw", "settings", "identity"))
        raw = cal["raw"]
        if _file_input(raw):
            raise_workflow_error(
                "unsupported", "calibration.raw requires explicitly decoded values", "calibration"
            )
        if type(raw) is not np.ndarray or raw.ndim != 4:
            raise_workflow_error("input", "calibration.raw requires (P,Z,Y,X)", "calibration")
        p, z, y, x = raw.shape
        if p not in (1, 3, 5, 7, 9) or z < 1 or x < 8 or x % 2 or y < 10 or y > x + 2:
            raise_workflow_error(
                "input", "calibration raw geometry violates empirical envelope", "calibration"
            )
        for count in (*raw.shape, (x + 2) * y * z, z * p, (x // 2 + 1) * z):
            _signed(count, "bead extent")
        _extent((p, z, y, x // 2 + 1), 16, "calibration")
        _extent((p, x // 2 + 1, z), 16, "calibration")
        _array(raw, "calibration.raw", raw.shape, raw=True, code="input")
        if (p + 1) // 2 < orders:
            raise_workflow_error("selection", "insufficient empirical orders", "calibration")
        if mode == "2d" and z != 1:
            raise_workflow_error(
                "selection", "declared true2d requires transfer K=1", "calibration"
            )
        settings = _calibration_settings(cal["settings"], raw.shape, optics)
        claim = validate_source_identity(cal["identity"], "calibration.identity", optics)
        return _TransferInputs(
            "raw-beads", raw, settings, calibration_identity=freeze_declarations(claim)
        )
    else:
        if _file_input(transfer):
            raise_workflow_error(
                "unsupported",
                "transfer file decoding is outside the pure-array workflow",
                "transfer",
            )
        if type(transfer) is PreparedOtf:
            table_identity = validate_source_identity(
                transfer_identity, "transfer_identity", optics, transfer=True
            )
            prepared = _validate_prepared(transfer, optics)
            result, selection = prepared.transfer, "prepared-otf"
            value = prepared
        elif type(transfer) is OpticalTransfer:
            table_identity = validate_source_identity(
                transfer_identity, "transfer_identity", optics, direct=True, transfer=True
            )
            result, selection = _validate_transfer(transfer), "accepted-transfer"
            value = result
        elif isinstance(transfer, Mapping):
            table_identity = validate_source_identity(
                transfer_identity, "transfer_identity", optics, transfer=True
            )
            return replace(
                _decoded_inputs(transfer, mode, orders),
                transfer_identity=freeze_declarations(table_identity),
            )
        else:
            raise_workflow_error("input", "invalid transfer value record", "transfer")
    if result.norders < orders:
        raise_workflow_error("selection", "insufficient complete transfer orders", "transfer")
    k = result.samples.shape[-1] if result.layout == "radial" else result.samples.shape[1]
    if mode == "2d" and k != 1:
        raise_workflow_error("selection", "declared true2d requires transfer K=1", "transfer")
    return _TransferInputs(
        selection, value, {}, transfer_identity=freeze_declarations(table_identity)
    )


def resolve_optical_transfer(inputs: _TransferInputs) -> tuple[OpticalTransfer, PreparedOtf | None]:
    """Materialize checked transfer backings and run the selected public stage once.

    Raw beads use prepare_bead_otf; decoded sections use their validated binding
    and declare_otf. Accepted transfer/prepared records receive independent
    read-only array snapshots without repeating scientific preparation.
    """
    prepared = None
    value = inputs.value
    if inputs.selection == "raw-beads":
        raw = np.array(value, copy=True)
        settings: dict[str, Any] = {
            key: np.array(v, copy=True) if type(v) is np.ndarray else v
            for key, v in inputs.settings.items()
        }
        with workflow_stage("calibration"):
            prepared = prepare_bead_otf(raw, **settings)
        result = prepared.transfer
    elif inputs.selection == "decoded-sections":
        binding = dict(inputs.binding)
        section_map = binding["section_map"]
        mode, layout = binding["effective_mode"], binding["layout"]
        if mode == "3d" and layout == "full":
            orders, k = len(section_map), len(section_map[0])
            samples = value[: orders * k].reshape(orders, k, *value.shape[1:])
        else:
            samples = value[list(section_map)]
            if mode == "2d":
                samples = samples[:, 0, :, None] if layout == "radial" else samples[:, None]
        with workflow_stage("transfer"):
            result = declare_otf(samples, **inputs.settings)
    elif inputs.selection == "prepared-otf":
        result = replace(value.transfer, samples=owned_readonly_array(value.transfer.samples))
        prepared = replace(
            value,
            transfer=result,
            **{name: owned_readonly_array(getattr(value, name)) for name in _CAL_ARRAYS},
            resolved_settings=freeze_declarations(value.resolved_settings, code="input"),
        )
    else:
        result = replace(value, samples=owned_readonly_array(value.samples))
    return result, prepared
