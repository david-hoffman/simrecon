"""Independent immutable declarations and endian-normalized array identities."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import fields
from typing import Any

import numpy as np

from ..acquisition.declarations import RawAcquisition
from ..optical_transfer import OpticalTransfer, PreparedOtf
from .config import _extent, _optics, _schema
from .result import _ArrayIdentity, raise_workflow_error


def freeze_declarations(
    value: Any,
    *,
    code: str = "config",
    active: set[int] | None = None,
    path: str | None = None,
) -> Any:
    """Snapshot supported values recursively, preserving scalar types and bits."""
    if type(value) is np.ndarray:
        _extent(value.shape, value.dtype.itemsize)
        if path is not None:
            # Preserve the native sequence-extent checks of the former tolist
            # snapshot, including the point where an empty axis stops traversal.
            for dimension in value.shape:
                _extent((dimension,), 8)
                if dimension == 0:
                    break
            # Numeric/string leaves already have the supported built-in
            # tolist() types. Other dtypes still undergo the original recursive
            # metadata admissibility checks, one element at a time, without
            # constructing an array-sized Python snapshot.
            if value.dtype.kind not in "biufcSU" or (
                value.dtype.kind == "c" and value.dtype.itemsize > 16
            ):
                for child in value.flat:
                    freeze_declarations(child.tolist(), code=code, active=active)
            return array_identity(path, value)
        return freeze_declarations(value.tolist(), code=code, active=active)
    if isinstance(value, np.floating):
        # Admissibility is checked before snapshotting. Even a binary64-width
        # NumPy real can keep its scalar type after item(); terminate explicitly.
        return float(value)
    if isinstance(value, np.generic):
        return freeze_declarations(value.item(), code=code, active=active)
    if value is None or type(value) in (str, bytes, int, float, complex, bool):
        return value
    if not isinstance(value, Mapping) and type(value) not in (tuple, list):
        raise_workflow_error(code, "metadata must contain supported built-in values")
    active = set() if active is None else active
    if id(value) in active:
        raise_workflow_error(code, "metadata must be acyclic")
    active.add(id(value))
    try:
        _extent((len(value),), 8)
        if isinstance(value, Mapping):
            if any(type(key) is not str for key in value):
                raise_workflow_error(code, "metadata mapping keys must be strings")
            return tuple(
                (
                    key,
                    freeze_declarations(
                        value[key],
                        code=code,
                        active=active,
                        path=None if path is None else path + "." + key,
                    ),
                )
                for key in sorted(value)
            )
        if (
            path is not None
            and value
            and all(
                type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str for pair in value
            )
        ):
            named = []
            for pair in value:
                if id(pair) in active:
                    raise_workflow_error(code, "metadata must be acyclic")
                active.add(id(pair))
                try:
                    _extent((len(pair),), 8)
                    named.append(
                        (
                            pair[0],
                            freeze_declarations(
                                pair[1], code=code, active=active, path=path + "." + pair[0]
                            ),
                        )
                    )
                finally:
                    active.remove(id(pair))
            return tuple(named)
        return tuple(
            freeze_declarations(
                v,
                code=code,
                active=active,
                path=None if path is None else path + "." + str(i),
            )
            for i, v in enumerate(value)
        )
    finally:
        active.remove(id(value))


def validate_source_identity(
    value: Any, name: str, optics: dict[str, Any], *, direct: bool = False, transfer: bool = False
) -> dict[str, Any]:
    """Validate explicit source claims against workflow optics without file I/O.

    Defaults serve validation only; the returned shallow mapping retains the
    supplied keys. Callers freeze it when an independent declaration is needed.
    """
    required = ("id", "intensity_unit", "optics") if direct else ("id", "intensity_unit")
    defaults: dict[str, Any] = {"files": ()}
    if not direct:
        defaults["optics"] = None
    result = _schema(value, name, required, defaults)
    for key in ("id", "intensity_unit"):
        if type(result[key]) is not str or not result[key]:
            raise_workflow_error("config", f"{name}.{key} must be a nonempty string")
    if transfer and result["intensity_unit"] != "dimensionless-transfer":
        raise_workflow_error("config", "transfer identity must declare dimensionless-transfer")
    files = result["files"]
    if type(files) not in (tuple, list):
        raise_workflow_error("config", "identity.files must be a sequence")
    for file in files:
        item = _schema(file, "identity.files", ("name", "bytes", "sha256", "role"))
        if (
            type(item["name"]) is not str
            or not item["name"]
            or item["name"] in (".", "..")
            or any(c in item["name"] for c in ("/", "\\", "\x00"))
        ):
            raise_workflow_error("config", "file name requires a basename")
        if type(item["bytes"]) is not int or item["bytes"] < 0:
            raise_workflow_error("config", "file bytes must be a nonnegative integer")
        if type(item["sha256"]) is not str or re.fullmatch("[0-9a-f]{64}", item["sha256"]) is None:
            raise_workflow_error("config", "file sha256 must be lowercase hexadecimal")
        if type(item["role"]) is not str or not item["role"]:
            raise_workflow_error("config", "file role must be nonempty")
    if direct and result["optics"] is None:
        raise_workflow_error("config", "direct transfer identity requires optics")
    if result["optics"] is not None and _optics(result["optics"], name + ".optics") != optics:
        raise_workflow_error("metadata", f"{name} optics conflict with workflow optics")
    # Defaults are resolved for validation, but source claims retain supplied keys.
    return dict(value)


def array_identity(name: str, array: Any) -> _ArrayIdentity:
    # Use the ndarray descriptor directly: this is a view of the original
    # validated storage, without subclass methods or surface metadata overrides.
    """Hash validated backing storage in contiguous little-endian representation.

    Retain original shape and normalized dtype in the identity record. This is
    an array-content identity, not verification of declared source files.
    """
    backing = np.ndarray.view(array, type=np.ndarray)
    _extent(backing.shape, backing.dtype.itemsize)
    dtype = backing.dtype.newbyteorder("<")
    normalized = np.ascontiguousarray(backing, dtype=dtype)
    # A byte view exposes the normalized storage without requiring Python's
    # buffer format to express a native-only numerical dtype or copying bytes.
    byte_view = normalized.view(np.uint8)
    digest = hashlib.sha256(memoryview(byte_view)).hexdigest()
    return _ArrayIdentity(name, tuple(backing.shape), dtype.str, digest)


def collect_array_identities(name: str, value: Any, result: dict[str, _ArrayIdentity]) -> None:
    """Collect array hashes recursively through supported mappings and records."""
    if issubclass(type(value), np.ndarray):
        result[name] = array_identity(name, value)
    elif isinstance(value, Mapping):
        for key, child in value.items():
            collect_array_identities(name + "." + key, child, result)
    elif type(value) in (RawAcquisition, PreparedOtf, OpticalTransfer):
        for field in fields(value):
            collect_array_identities(name + "." + field.name, getattr(value, field.name), result)
    elif type(value) in (tuple, list):
        # Accepted record settings may themselves contain numerical declarations.
        for index, child in enumerate(value):
            collect_array_identities(name + "." + str(index), child, result)


def owned_readonly_array(value: Any) -> Any:
    """Copy checked array storage in C order and mark the result read-only."""
    _extent(value.shape, value.dtype.itemsize)
    result = np.array(value, copy=True, order="C")
    result.flags.writeable = False
    return result


def readonly_private_array(value: Any) -> Any:
    """Transfer a private C-order allocation after its last write.

    Unlike owned_readonly_array(), this must never receive caller storage or a
    full-debug field that also remains published in another returned record.
    """
    _extent(value.shape, value.dtype.itemsize)
    value.flags.writeable = False
    return value
