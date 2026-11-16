"""Exact workflow schemas and preallocation declaration checks."""

from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Integral, Real
from typing import Any

import numpy as np

from ..acquisition.layout import AcquisitionModeError, extent, output_extents
from ..acquisition.preparation import _raw_samples
from ..models import SimreconError
from .result import WorkflowError, raise_workflow_error

_F32_MAX = float(np.finfo(np.float32).max)
_ACQUISITION_REQUIRED = (
    "acquisition_mode",
    "dxy_um",
    "dz_um",
    "norders",
    "background",
    "lateral_zoom",
    "axial_zoom",
    "phase_policy",
)
_ACQUISITION_DEFAULTS = dict(
    flatfield_slope=None,
    phases_rad=None,
    phase_steps_rad=None,
    edge_pixels=10,
    equalize=True,
    equalize_z=False,
    equalize_time=False,
    storage_order="direction-major",
    combine_off_orders=None,
    drift_between=False,
    drift_within=False,
    fit_drift=False,
    adjust_phases=False,
    drift_filter_fraction=0.0,
)
_OPTICS_KEYS = ("wavelength_nm", "numerical_aperture", "immersion_index")
_CARRIER_DEFAULTS = dict(
    phase_start_angle_rad=1.57193,
    negative_angle_step=False,
    angles_rad=None,
    search_carriers=True,
    use_time0_carriers=True,
    amplitude_floors=None,
    fit_all_phases=True,
)
_FILTER_DEFAULTS = dict(
    wiener_increment=0.0,
    suppress_singularities=True,
    suppression_radius_bins=10.0,
    dampen_order0=False,
    omit_order0=False,
    omit_kz0=False,
    output_taper="cosine",
    power_taper_exponent=None,
    precise_taper=False,
    filter_overlaps=True,
    explode_factor=1.0,
)


def _schema(
    value: Any, name: str, required: tuple[str, ...], defaults: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Resolve exactly the required/default keys of a workflow mapping."""
    if not isinstance(value, Mapping):
        raise_workflow_error("config", f"{name} requires a mapping")
    defaults = {} if defaults is None else defaults
    if (
        any(type(k) is not str for k in value)
        or not set(required) <= value.keys()
        or not value.keys() <= set(required) | defaults.keys()
    ):
        raise_workflow_error("config", f"{name} has missing or unlisted keys")
    return {k: value[k] for k in required} | {k: value.get(k, v) for k, v in defaults.items()}


def _extent(shape: tuple[int, ...], size: int, stage: str = "declaration") -> None:
    """Translate native allocation-extent failures to the workflow stage."""
    try:
        extent(shape, size)
    except AcquisitionModeError as error:
        raise WorkflowError("workflow_representation", str(error), stage=stage) from error


def _signed(value: int, name: str) -> int:
    """Require the source signed32 integer representation without narrowing."""
    if not -(2**31) <= value <= 2**31 - 1:
        raise_workflow_error("representation", f"{name} exceeds signed32 representation")
    return value


def _integer(value: Any, name: str, minimum: int = 1, *, code: str = "config") -> int:
    """Require a nonboolean integer meeting its minimum and signed32 bound."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise_workflow_error(code, f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise_workflow_error(code, f"{name} must be at least {minimum}")
    return _signed(result, name)


def _scalar(value: Any, name: str, *, positive: bool = False, code: str = "config") -> float:
    """Require a standard finite real scalar within source float magnitude."""
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Real)
        or (isinstance(value, np.generic) and value.dtype.kind == "f" and value.dtype.itemsize > 8)
    ):
        raise_workflow_error(code, f"{name} must be a standard finite real scalar")
    native: Any = value.item() if isinstance(value, np.generic) else value
    if abs(native) > _F32_MAX:
        raise_workflow_error(code, f"{name} exceeds source float magnitude")
    result = float(native)
    if not math.isfinite(result) or (positive and result <= 0):
        raise_workflow_error(code, f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _enum(value: Any, name: str, choices: tuple[str, ...]) -> str:
    """Require an exact string from the declared workflow choices."""
    if type(value) is not str or value not in choices:
        raise_workflow_error("config", f"{name} must be one of {choices}")
    return value


def _flags(mapping: dict[str, Any], names: tuple[str, ...]) -> None:
    """Require Python bool values for each listed configuration switch."""
    for name in names:
        if type(mapping[name]) is not bool:
            raise_workflow_error("config", f"{name} must be a Python bool")


def _array(
    value: Any,
    name: str,
    shape: tuple[int, ...],
    *,
    raw: bool = False,
    code: str = "config",
    complex_ok: bool = False,
) -> Any:
    """Validate exact shape, supported storage and finite source-range values.

    Raw samples additionally use the acquisition stage's exact-representation
    checks. The original array is returned without copying or conversion.
    """
    _extent(shape, 16 if complex_ok else 8)
    if type(value) is not np.ndarray or value.shape != shape:
        raise_workflow_error(code, f"{name} requires a plain array of shape {shape}")
    dtype = value.dtype
    if not (
        (dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        or (dtype.kind == "f" and dtype.itemsize in (2, 4, 8))
        or (complex_ok and dtype.kind == "c" and dtype.itemsize in (8, 16))
    ):
        raise_workflow_error(code, f"{name} has an unsupported sample kind")
    if not np.isfinite(value).all():
        raise_workflow_error(code, f"{name} must be finite")
    if raw:
        try:
            _raw_samples(value, name)
        except SimreconError as error:
            raise WorkflowError("workflow_" + code, str(error), stage="declaration") from error
    else:
        for component in (np.real(value), np.imag(value)) if dtype.kind == "c" else (value,):
            if (component > np.float64(_F32_MAX)).any() or (
                component < np.float64(-_F32_MAX)
            ).any():
                raise_workflow_error(code, f"{name} exceeds source float magnitude")
    return value


def _optics(value: Any, name: str = "optics") -> dict[str, Any]:
    """Resolve the exact wavelength, aperture and immersion-index schema."""
    result = _schema(value, name, _OPTICS_KEYS)
    result["wavelength_nm"] = _integer(result["wavelength_nm"], name + ".wavelength_nm")
    if result["wavelength_nm"] > 32767:
        raise_workflow_error("config", f"{name}.wavelength_nm exceeds signed short domain")
    for key in _OPTICS_KEYS[1:]:
        result[key] = _scalar(result[key], name + "." + key, positive=True)
    if not 1 <= result["immersion_index"] <= 2 or result["numerical_aperture"] > min(
        2, result["immersion_index"]
    ):
        raise_workflow_error("config", f"{name} is outside the optical domain")
    return result


def resolve_workflow_settings(
    acquisition: Any, optics: Any, carrier: Any, filtering: Any
) -> tuple[dict[str, Any], ...]:
    """Resolve acquisition, optics, carrier and filtering declarations in order.

    Defaults and scalar domains are checked here. Geometry, array backings and
    route-specific prerequisites are checked separately before stage execution.
    """
    a = _schema(acquisition, "acquisition", _ACQUISITION_REQUIRED, _ACQUISITION_DEFAULTS)
    o = _optics(optics)
    c = _schema(carrier, "carrier", ("linespacing_um",), _CARRIER_DEFAULTS)
    f = _schema(filtering, "filtering", ("wiener",), _FILTER_DEFAULTS)
    a["acquisition_mode"] = _enum(a["acquisition_mode"], "acquisition_mode", ("3d", "2d"))
    a["storage_order"] = _enum(a["storage_order"], "storage_order", ("direction-major", "z-major"))
    a["phase_policy"] = _enum(
        a["phase_policy"], "phase_policy", ("uniform", "supplied", "steps", "drift")
    )
    for key in ("dxy_um", "dz_um", "lateral_zoom", "drift_filter_fraction"):
        a[key] = _scalar(a[key], key, positive=key in ("dxy_um", "lateral_zoom"))
    if a["dz_um"] < 0 or (a["acquisition_mode"] == "3d" and a["dz_um"] == 0):
        raise_workflow_error("config", "dz_um requires positive 3d or nonnegative 2d pitch")
    a["norders"] = _integer(a["norders"], "norders", 2)
    a["axial_zoom"] = _integer(a["axial_zoom"], "axial_zoom")
    a["edge_pixels"] = _integer(a["edge_pixels"], "edge_pixels", -(2**31))
    _flags(
        a,
        (
            "equalize",
            "equalize_z",
            "equalize_time",
            "drift_between",
            "drift_within",
            "fit_drift",
            "adjust_phases",
        ),
    )
    for key in ("linespacing_um", "phase_start_angle_rad"):
        c[key] = _scalar(c[key], key, positive=key == "linespacing_um")
    _flags(c, ("negative_angle_step", "search_carriers", "use_time0_carriers", "fit_all_phases"))
    for key in ("wiener", "wiener_increment", "suppression_radius_bins", "explode_factor"):
        f[key] = _scalar(f[key], key, positive=key == "wiener")
    if f["power_taper_exponent"] is not None:
        f["power_taper_exponent"] = _scalar(f["power_taper_exponent"], "power_taper_exponent")
    f["output_taper"] = _enum(f["output_taper"], "output_taper", ("cosine", "none", "power"))
    if f["output_taper"] == "power" and f["power_taper_exponent"] is None:
        raise_workflow_error("config", "power taper requires its exponent")
    _flags(
        f,
        (
            "suppress_singularities",
            "dampen_order0",
            "omit_order0",
            "omit_kz0",
            "precise_taper",
            "filter_overlaps",
        ),
    )
    return a, o, c, f


def validate_workflow_geometry(
    shape: tuple[int, ...], a: dict[str, Any], c: dict[str, Any], plane_policy: str
) -> tuple[int, ...]:
    """Validate source/native extents and return the effective six-axis shape.

    The literal-2d policy regroups physical planes into time without numerical
    processing. Output/scratch extents are checked before array-sized work.
    """
    if len(shape) != 6 or any(n < 1 for n in shape) or shape[-1] < 2 or shape[-1] % 2:
        raise_workflow_error("input", "specimen requires positive (T,D,P,Z,Y,X) with even X>=2")
    t, d, p, z, y, x = shape
    if plane_policy == "literal-2d-stack":
        if a["acquisition_mode"] != "2d":
            raise_workflow_error("config", "literal-2d-stack requires declared 2d")
        effective = (t * z, d, p, 1, y, x)
    else:
        if (a["acquisition_mode"] == "2d" and z != 1) or (a["acquisition_mode"] == "3d" and z < 2):
            raise_workflow_error("input", "specimen Z disagrees with declared mode")
        effective = shape
    orders = a["norders"]
    q = 2 * orders - 1
    if q > p or (a["acquisition_mode"] == "3d" and c["search_carriers"] and orders < 3):
        raise_workflow_error("config", "orders require Q<=P and searching 3d requires O>=3")
    for n in (
        *shape,
        *effective,
        q,
        (x + 2) * y * z,
        (x // 2 + 1) * y * z,
        x * y * z,
        d * z * p,
        t * d * z * p,
        q * p,
        d * orders,
    ):
        _signed(n, "source dimension/product")
    lateral = a["lateral_zoom"]
    if lateral < 1 or float(np.float32(lateral)) != lateral:
        raise_workflow_error("representation", "lateral zoom requires exact source-float L>=1")
    for n in (x, y):
        target = lateral * n
        if not math.isfinite(target) or not target.is_integer():
            raise_workflow_error("representation", "lateral zoom requires integral extents")
        _signed(int(target), "output extent")
    try:
        output_extents(effective, lateral, a["axial_zoom"])
    except AcquisitionModeError as error:
        raise WorkflowError("workflow_representation", str(error), stage="declaration") from error
    te, _, _, ze, _, _ = effective
    oz, oy, ox = ze * a["axial_zoom"], int(y * lateral), int(x * lateral)
    for sh, size in (
        (shape, 8),
        ((te, d, q, ze, y, x // 2 + 1), 16),
        ((te, d, ze, q, p), 8),
        ((te, d, ze, p), 8),
        ((te, d, orders), 8),
        ((te, d, ze, p, 2), 8),
        ((te, d, 3), 8),
        ((te, d, q, oz, oy, ox // 2 + 1), 16),
        ((ox + 2, oy, oz), 16),
        ((t * z, d, 2), 8),
    ):
        _extent(sh, size)
    if a["edge_pixels"] > min(x, y):
        raise_workflow_error("config", "edge_pixels exceeds lateral dimensions")
    return effective


def validate_workflow_arrays_and_routes(
    raw: Any,
    a: dict[str, Any],
    c: dict[str, Any],
    original: tuple[int, ...],
    effective: tuple[int, ...],
    off: Any,
    extra: Any,
    clock: Any,
    clock_unit: Any,
    header_phases: Any,
) -> int:
    """Validate raw backings and selected phase/drift prerequisites before copies.

    Input axes remain (T,D,P,Z,Y,X), with aligned off-exposure and header streams.
    Return the off-exposure count after rejecting unsupported source routes.
    """
    t, d, p, z, y, x = original
    orders = a["norders"]
    n = 0
    if off is not None:
        if (
            type(off) is not np.ndarray
            or off.ndim != 7
            or off.shape[:4] != original[:4]
            or off.shape[-2:] != (y, x)
            or off.shape[4] < 1
        ):
            raise_workflow_error("input", "off_exposures require aligned (T,D,P,Z,N,Y,X)")
        n = _integer(off.shape[4], "off exposure count", code="input")
        _extent(off.shape, 8)
    for value in (n + 1, d * p * (n + 1), t * d * z * p * (n + 1)):
        _signed(value, "exposure stream count")
    # Counts and all target sizes have passed before examining/copying pixels.
    _array(raw, "specimen", original, raw=True, code="input")
    if off is not None:
        _array(off, "off_exposures", off.shape, raw=True, code="input")
    if extra is not None:
        _array(extra, "exposure_background", original[:4], code="input")
    if type(a["background"]) is np.ndarray:
        _array(a["background"], "acquisition.background", (y, x))
    else:
        a["background"] = _scalar(a["background"], "background")
    for name, shape in (
        ("flatfield_slope", (y, x)),
        ("phases_rad", (d, p)),
        ("phase_steps_rad", (d,)),
    ):
        if a[name] is not None:
            _array(a[name], "acquisition." + name, shape)
    if c["angles_rad"] is not None:
        _array(c["angles_rad"], "carrier.angles_rad", (d,))
    if c["amplitude_floors"] is not None:
        values = _array(c["amplitude_floors"], "carrier.amplitude_floors", (orders - 1,))
        if (values <= 0).any():
            raise_workflow_error("config", "amplitude floors must be positive")
        if orders > 25:
            raise_workflow_error("unsupported", "amplitude floors use fixed O<=25 allocation")
    if a["combine_off_orders"] is not None:
        values = a["combine_off_orders"]
        if (
            type(values) is not np.ndarray
            or values.shape != (orders,)
            or values.dtype.kind not in "iu"
        ):
            raise_workflow_error("config", "combine_off_orders requires integer (O,) array")
        for value in values:
            _integer(value, "combine_off_orders", -(2**31))
        if orders > 25:
            raise_workflow_error("unsupported", "off selectors use fixed O<=25 allocation")
        if n == 0 and (values > 0).any():
            raise_workflow_error("config", "positive off selector requires off exposures")
    base = (
        "steps"
        if a["phase_steps_rad"] is not None
        else "supplied"
        if a["phases_rad"] is not None
        else "uniform"
    )
    actual = "drift" if a["drift_within"] and a["adjust_phases"] else base
    if a["phase_policy"] != actual:
        raise_workflow_error("config", "phase_policy does not assert the actual matrix route")
    if a["phase_steps_rad"] is not None and d > 3:
        raise_workflow_error("unsupported", "phase steps use a fixed three-float allocation")
    count = t * d * z * p * (n + 1)
    for name, value in (("header_timestamps", clock), ("header_phases_rad", header_phases)):
        if value is not None:
            _array(value, name, (count,), code="metadata")
    if (clock is None and clock_unit is not None) or (
        clock is not None and (type(clock_unit) is not str or not clock_unit.strip())
    ):
        raise_workflow_error(
            "metadata", "timestamp data requires an explicit nonblank clock unit and vice versa"
        )
    two_d = a["acquisition_mode"] == "2d"
    active = a["drift_between"] or a["drift_within"]
    fast = a["storage_order"] == "z-major"
    if active and fast and d > 1:
        raise_workflow_error("unsupported", "fast drift reads uninitialized vectors for D>1")
    if a["drift_within"] and not two_d and fast:
        raise_workflow_error("unsupported", "fast within-3d reads uninitialized driftlist")
    if active and not fast:
        if x < 10 or y < 10 or a["dz_um"] <= 0:
            raise_workflow_error(
                "config", "drift prepass requires fixed10 edges and positive axial pitch"
            )
        if n > y + 1:
            raise_workflow_error("unsupported", "prepass off loop is nonterminating for N>Y+1")
    if a["drift_within"] and two_d and n == 0:
        raise_workflow_error(
            "unsupported", "within2d reference is uninitialized without off exposures"
        )
    fitting = a["drift_within"] and (not two_d or a["fit_drift"])
    if fitting and not a["adjust_phases"]:
        raise_workflow_error("unsupported", "fitted drift timestamp allocation requires phase flag")
    if fitting and (p if two_d else d) < 4:
        raise_workflow_error("unsupported", "cubic fit requires four allocated points")
    if fitting and (clock is None or header_phases is None):
        raise_workflow_error("metadata", "fitted drift requires clock and phase data")
    if a["drift_within"] and a["adjust_phases"] and header_phases is None:
        raise_workflow_error("metadata", "linked phases require header phase data")
    return n
