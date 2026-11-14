"""Immutable compact result and immediate, path-aware diagnostic projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Any

import numpy as np

from ..acquisition.layout import REFERENCE
from .identity import array_identity
from .result import _ArrayIdentity, _WorkflowEvent

OMITTED_DIAGNOSTICS = (
    "stage-images",
    "quadratures",
    "overlap-arrays",
    "correlation-arrays",
    "camera-maps",
    "transfer-samples",
    "calibration-arrays",
    "layout-pixels",
    "precise-query-events",
)


@dataclass(frozen=True)
class ReconstructionSummary:
    """Signed reconstruction with compact immutable scientific provenance."""

    image: Any
    x_um: Any
    y_um: Any
    z_um: Any
    intensity_unit: str
    intensity_semantics: str
    carriers_cyc_um: Any
    modulation: Any
    raw_modulation: Any
    initial_carriers_cyc_um: Any
    phase_linkage_carriers_cyc_um: Any
    effective_wiener: Any
    branches: tuple[tuple[str, ...], ...]
    input_identities: tuple[_ArrayIdentity, ...]
    source_declarations: tuple[tuple[str, Any], ...]
    resolved_settings: tuple[tuple[str, Any], ...]
    preparation: tuple[tuple[str, Any], ...]
    estimation: tuple[tuple[str, Any], ...]
    filtering: tuple[tuple[tuple[str, Any], ...], ...]
    transfer: tuple[tuple[str, Any], ...]
    calibration: tuple[tuple[str, Any], ...] | None
    layout: tuple[tuple[str, Any], ...] | None
    overlap_builds: tuple[Any, ...]
    search_trace: tuple[Any, ...]
    preparation_trace: tuple[Any, ...]
    filtering_trace: tuple[tuple[Any, ...], ...]
    trace: tuple[_WorkflowEvent, ...]
    diagnostics: str = "summary"
    omitted_diagnostics: tuple[str, ...] = OMITTED_DIAGNOSTICS
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = REFERENCE
    limitations: tuple[str, ...] = ()


def project(value: Any, path: str, *, exclude: tuple[str, ...] = ()) -> Any:
    """Project validated public fields before arrays become Python sequences.

    Record declaration order and named-pair order are preserved. Mapping order
    follows CE07 metadata sorting. This function never stores a source object.
    """
    if isinstance(value, np.ndarray):
        return array_identity(path, value)
    if isinstance(value, _ArrayIdentity):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (field.name, project(getattr(value, field.name), f"{path}.{field.name}"))
            for field in fields(value)
            if field.name not in exclude
        )
    if isinstance(value, Mapping):
        return tuple((key, project(value[key], f"{path}.{key}")) for key in sorted(value))
    if isinstance(value, (tuple, list)):
        named = bool(value) and all(
            type(item) is tuple and len(item) == 2 and type(item[0]) is str for item in value
        )
        if named:
            return tuple((key, project(child, f"{path}.{key}")) for key, child in value)
        return tuple(project(child, f"{path}.{i}") for i, child in enumerate(value))
    if isinstance(value, np.generic):
        return value.item()
    return value
