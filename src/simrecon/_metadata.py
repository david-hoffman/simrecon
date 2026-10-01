"""Pure configuration validation and logical-layout resolution."""

import copy
import math
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, NoReturn, cast

from ._model import DatasetInfo, SimreconError

ORDER = ("time", "channel", "orientation", "phase", "z")


def supported(info: DatasetInfo) -> None:
    if info.stored_dtype is None:
        raise SimreconError(
            "unsupported_mode", "Only uint16 mode 6 and float32 mode 2 are supported"
        )
    if info.file_metadata["map_axes"] != (1, 2, 3):
        raise SimreconError("unsupported_axes", "Only identity spatial mapping is supported")


def resolved(info: DatasetInfo) -> None:
    supported(info)
    if info.config is None:
        raise SimreconError("config_required", "Explicit acquisition configuration is required")


def invalid(message: str) -> NoReturn:
    raise SimreconError("config_invalid", message)


def positive(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (isinstance(value, int) or math.isfinite(value))
        and value > 0
    )


def harmonize(info: DatasetInfo, *, config: Mapping[str, object]) -> DatasetInfo:
    supported(info)
    if not config:
        raise SimreconError("config_required", "Explicit acquisition configuration is required")
    cfg: dict[str, Any] = copy.deepcopy(dict(config))
    allowed = {
        "version",
        "data_kind",
        "plane_axes",
        "plane_shape",
        "spatial_fields",
        "extended_header",
        "overrides",
    }
    if (
        cfg.keys() - allowed
        or type(cfg.get("version")) is not int
        or cfg.get("version") != 1
        or cfg.get("data_kind") != "spatial_image"
        or not isinstance(cfg.get("spatial_fields"), str)
    ):
        invalid("Unknown configuration fields, version, or data kind")
    axes, shape = cfg.get("plane_axes"), cfg.get("plane_shape")
    if not isinstance(axes, (list, tuple)) or not isinstance(shape, (list, tuple)):
        invalid("Plane axes and shape must be sequences")
    if (
        len(axes) != len(shape)
        or any(a not in ORDER for a in axes)
        or len(set(axes)) != len(axes)
        or any(type(n) is not int or n <= 0 for n in shape)
    ):
        invalid("Plane axes must be unique allowed names with positive integer counts")
    if math.prod(shape) != info.stored_shape[0]:
        raise SimreconError(
            "layout_mismatch", "Configured plane count disagrees with stored sections"
        )
    policy = cfg.get("extended_header")
    if info.extended_header_bytes and policy != "opaque":
        raise SimreconError("schema_required", "Nonempty extension requires explicit opaque policy")
    if policy not in (None, "none", "opaque"):
        invalid("Unknown extended-header policy")
    if not info.extended_header_bytes and policy == "opaque":
        invalid("An absent extension requires none policy")
    overrides = cfg.get("overrides", {})
    if not isinstance(overrides, Mapping) or overrides.keys() - {"sampling_um", "wavelengths_nm"}:
        invalid("Unknown override fields")
    sampling_overrides = overrides.get("sampling_um", {})
    wavelength_overrides = overrides.get("wavelengths_nm", {})
    if not isinstance(sampling_overrides, Mapping) or sampling_overrides.keys() - {"x", "y", "z"}:
        invalid("Sampling overrides require x, y, or z")
    if not isinstance(wavelength_overrides, Mapping):
        invalid("Wavelength overrides require a channel-index mapping")
    if any(not positive(v) for v in sampling_overrides.values()):
        invalid("Sampling overrides must be finite and positive")
    if any(
        not isinstance(k, str)
        or not k.isascii()
        or not k.isdecimal()
        or (k != "0" and k.startswith("0"))
        or not positive(v)
        for k, v in wavelength_overrides.items()
    ):
        invalid(
            "Wavelength overrides need canonical nonnegative indices and positive finite values"
        )
    sampling = {
        axis: value if isinstance(value, float) else None
        for axis, value in zip(("x", "y", "z"), info.file_metadata["spatial_fields"], strict=True)
    }
    required = ("x", "y", "z") if "z" in axes else ("x", "y")
    if cfg.get("spatial_fields") != "direct_um":
        sampling = dict.fromkeys(("x", "y", "z"))
    provenance: list[dict[str, Any]] = [
        {
            "field": "plane_axes",
            "unresolved": "acquisition_order",
            "new": copy.deepcopy(axes),
            "source": "config",
        },
        {
            "field": "plane_shape",
            "unresolved": "acquisition_counts",
            "new": copy.deepcopy(shape),
            "source": "config",
        },
    ]
    sizes = dict(zip(axes, shape, strict=True))
    for axis in ("time", "channel"):
        if axis in sizes:
            provenance.append(
                {
                    "field": f"file_metadata.{axis}_count",
                    "old": info.file_metadata[f"{axis}_count"],
                    "new": sizes[axis],
                    "source": "config",
                }
            )
    for axis, value in sampling_overrides.items():
        i = ("x", "y", "z").index(axis)
        old = info.file_metadata["spatial_fields"][i]
        provenance.append(
            {"field": f"sampling_um.{axis}", "old": old, "new": value, "source": "override"}
        )
        sampling[axis] = value
    if any(not positive(sampling[a]) for a in required):
        raise SimreconError(
            "sampling_required", "Required spatial sampling must be finite and positive"
        )
    slots = info.file_metadata["wavelength_slots"]
    wavelengths = {str(i): value for i, value in enumerate(slots) if value > 0}
    original_wavelengths = {str(i): value for i, value in enumerate(slots)}
    for channel, value in wavelength_overrides.items():
        provenance.append(
            {
                "field": f"wavelengths_nm.{channel}",
                "old": original_wavelengths.get(channel),
                "new": value,
                "source": "override",
            }
        )
        wavelengths[channel] = value
    if "z" not in axes:
        sampling["z"] = None
    canonical = tuple(a for a in ORDER if a in sizes)
    return replace(
        info,
        data_kind="spatial_image",
        unresolved=(),
        axes=(*canonical, "y", "x"),
        shape=(*(sizes[a] for a in canonical), *info.stored_shape[1:]),
        config=cfg,
        sampling_um=sampling,
        wavelengths_nm=wavelengths,
        provenance=tuple(provenance),
    )


def coordinate(info: DatasetInfo, index: int) -> dict[str, int]:
    result = {}
    for axis, size in reversed(tuple(zip(info.axes[:-2], info.shape[:-2], strict=True))):
        index, result[axis] = divmod(index, size)
    return result


def source_index(info: DatasetInfo, coord: dict[str, int]) -> int:
    index = 0
    for axis, size in zip(
        cast(dict[str, Any], info.config)["plane_axes"],
        cast(dict[str, Any], info.config)["plane_shape"],
        strict=True,
    ):
        index = index * size + coord[axis]
    return index
