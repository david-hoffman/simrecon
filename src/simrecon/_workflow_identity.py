"""Independent immutable declarations and endian-normalized array identities."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import fields
from typing import Any

import numpy as np

from ._acquisition import RawAcquisition
from ._optical_transfer import OpticalTransfer, PreparedOtf
from ._workflow_config import _extent, _optics, _schema
from ._workflow_result import _ArrayIdentity, _fail


def _freeze(value: Any, *, code: str = "config", active: set[int] | None = None) -> Any:
    """Snapshot supported values recursively, preserving scalar types and bits."""
    if type(value) is np.ndarray:
        _extent(value.shape, value.dtype.itemsize)
        return _freeze(value.tolist(), code=code, active=active)
    if isinstance(value, np.floating):
        # Admissibility is checked before snapshotting. Even a binary64-width
        # NumPy real can keep its scalar type after item(); terminate explicitly.
        return float(value)
    if isinstance(value, np.generic):
        return _freeze(value.item(), code=code, active=active)
    if value is None or type(value) in (str, bytes, int, float, complex, bool):
        return value
    if not isinstance(value, Mapping) and type(value) not in (tuple, list):
        _fail(code, "metadata must contain supported built-in values")
    active = set() if active is None else active
    if id(value) in active:
        _fail(code, "metadata must be acyclic")
    active.add(id(value))
    try:
        _extent((len(value),), 8)
        if isinstance(value, Mapping):
            if any(type(key) is not str for key in value):
                _fail(code, "metadata mapping keys must be strings")
            return tuple(
                (key, _freeze(value[key], code=code, active=active)) for key in sorted(value)
            )
        return tuple(_freeze(v, code=code, active=active) for v in value)
    finally:
        active.remove(id(value))


def _identity(
    value: Any, name: str, optics: dict[str, Any], *, direct: bool = False, transfer: bool = False
) -> dict[str, Any]:
    required = ("id", "intensity_unit", "optics") if direct else ("id", "intensity_unit")
    defaults: dict[str, Any] = {"files": ()}
    if not direct:
        defaults["optics"] = None
    result = _schema(value, name, required, defaults)
    for key in ("id", "intensity_unit"):
        if type(result[key]) is not str or not result[key]:
            _fail("config", f"{name}.{key} must be a nonempty string")
    if transfer and result["intensity_unit"] != "dimensionless-transfer":
        _fail("config", "transfer identity must declare dimensionless-transfer")
    files = result["files"]
    if type(files) not in (tuple, list):
        _fail("config", "identity.files must be a sequence")
    for file in files:
        item = _schema(file, "identity.files", ("name", "bytes", "sha256", "role"))
        if (
            type(item["name"]) is not str
            or not item["name"]
            or item["name"] in (".", "..")
            or any(c in item["name"] for c in ("/", "\\", "\x00"))
        ):
            _fail("config", "file name requires a basename")
        if type(item["bytes"]) is not int or item["bytes"] < 0:
            _fail("config", "file bytes must be a nonnegative integer")
        if type(item["sha256"]) is not str or re.fullmatch("[0-9a-f]{64}", item["sha256"]) is None:
            _fail("config", "file sha256 must be lowercase hexadecimal")
        if type(item["role"]) is not str or not item["role"]:
            _fail("config", "file role must be nonempty")
    if direct and result["optics"] is None:
        _fail("config", "direct transfer identity requires optics")
    if result["optics"] is not None and _optics(result["optics"], name + ".optics") != optics:
        _fail("metadata", f"{name} optics conflict with workflow optics")
    # Defaults are resolved for validation, but source claims retain supplied keys.
    return dict(value)


def _digest(name: str, array: Any) -> _ArrayIdentity:
    # Use the ndarray descriptor directly: this is a view of the original
    # validated storage, without subclass methods or surface metadata overrides.
    backing = np.ndarray.view(array, type=np.ndarray)
    _extent(backing.shape, backing.dtype.itemsize)
    dtype = backing.dtype.newbyteorder("<")
    normalized = np.ascontiguousarray(backing, dtype=dtype)
    # A byte view exposes the normalized storage without requiring Python's
    # buffer format to express a native-only numerical dtype or copying bytes.
    byte_view = normalized.view(np.uint8)
    digest = hashlib.sha256(memoryview(byte_view)).hexdigest()
    return _ArrayIdentity(name, tuple(backing.shape), dtype.str, digest)


def _collect(name: str, value: Any, result: dict[str, _ArrayIdentity]) -> None:
    if issubclass(type(value), np.ndarray):
        result[name] = _digest(name, value)
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _collect(name + "." + key, child, result)
    elif type(value) in (RawAcquisition, PreparedOtf, OpticalTransfer):
        for field in fields(value):
            _collect(name + "." + field.name, getattr(value, field.name), result)
    elif type(value) in (tuple, list):
        # Accepted record settings may themselves contain numerical declarations.
        for index, child in enumerate(value):
            _collect(name + "." + str(index), child, result)


def _owned(value: Any) -> Any:
    _extent(value.shape, value.dtype.itemsize)
    result = np.array(value, copy=True, order="C")
    result.flags.writeable = False
    return result
