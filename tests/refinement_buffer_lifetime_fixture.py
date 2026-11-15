"""Frozen public inputs and exact RB117 retention observers.

These controls assert retention and record relationships. Independent science
stays in the named unchanged estimator/acquisition keepers in the receipt.
No numerical-accuracy envelope or in-call last-use proof is supplied here.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import struct
from typing import Any

import numpy as np

import simrecon
from c_estimation_fixture import OPTICS, transfer_record


def workflow_case(
    mode: str,
    orders: int,
    *,
    times: int = 1,
    directions: int = 1,
    layout: str = "radial",
    reuse: bool = True,
    search: bool = True,
    dz: float = 1.0,
    adjustments: bool = False,
    low_bin: bool = False,
    odd_phase: bool = False,
) -> tuple[Any, dict[str, Any]]:
    """Retain previously observed passing inputs without an accuracy claim."""
    shape = (times, directions, 2 * orders - 1, 1 if mode == "2d" else 3, 3, 8 if low_bin else 4)
    raw = np.random.default_rng(7).integers(1, 17, shape).astype(np.float64)
    if low_bin:
        phases = shape[2]
        spatial = np.array([2, 1, -1, -1, 0, -1, -1, 1], dtype=np.float64)
        for t in range(times):
            for p in range(phases):
                coefficient = phases * int(p == 0) - 1
                raw[t, :, p] = 64 + (t + 1) * (p + 1) / 8 + (1 + t / 4) * coefficient * spatial
                if odd_phase:
                    sine = np.array([0, 1, 1, 1, 0, -1, -1, -1], dtype=np.float64)
                    raw[t, :, p] += 0.5 * (int(p == 1) - int(p == 0)) * sine
    samples = None if mode == "3d" else _plane_samples(orders + 1, layout)
    if low_bin:
        table_shape = (
            (orders + 1, 12, 1 if mode == "2d" else 8)
            if layout == "radial"
            else (orders + 1, 1 if mode == "2d" else 8, 12, 12)
        )
        samples = np.ones(table_shape)
    transfer = transfer_record(orders + 1, layout=layout, samples=samples)
    settings: dict[str, Any] = dict(
        acquisition=dict(
            acquisition_mode=mode,
            dxy_um=1.0,
            dz_um=dz,
            norders=orders,
            background=0.0,
            lateral_zoom=1.0,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        optics=OPTICS.copy(),
        carrier=dict(
            linespacing_um=10.0,
            angles_rad=np.linspace(-0.4, 0.2, directions),
            search_carriers=search,
            use_time0_carriers=reuse,
            amplitude_floors=np.full(orders - 1, 0.75) if adjustments else None,
            fit_all_phases=not adjustments,
        ),
        filtering=dict(wiener=0.5, suppress_singularities=False, output_taper="none"),
        specimen_identity=dict(id="rb117-specimen", intensity_unit="detector-counts"),
        transfer=transfer,
        transfer_identity=dict(
            id="rb117-transfer", intensity_unit="dimensionless-transfer", optics=OPTICS.copy()
        ),
    )
    return raw, settings


def _plane_samples(orders: int, layout: str) -> Any:
    shape = (orders, 12, 1) if layout == "radial" else (orders, 1, 12, 12)
    samples = np.empty(shape, dtype=np.complex128)
    for index in np.ndindex(shape):
        b, *coordinates = index
        samples[index] = (8 + b + sum(coordinates)) / 16 + 1j * (
            1 + 2 * b + sum((j + 1) * v for j, v in enumerate(coordinates))
        ) / 32
    return samples


def retention_case(
    group: str,
    mode: str = "3d",
    orders: int = 3,
    *,
    layout: str = "radial",
    reuse: bool = True,
    search: bool = True,
    invalid: str | None = None,
) -> tuple[Any, dict[str, Any]]:
    """One exogenous-input declaration shared by collection and public tests."""
    options: dict[str, Any] = dict(layout=layout, reuse=reuse, search=search)
    if group == "native":
        options.update(times=2, directions=3)
    elif group == "later":
        options.update(
            adjustments=orders > 2,
            dz=0.0 if mode == "2d" else 1.0,
            low_bin=mode == "3d",
        )
        # The earlier even LO3D input passed the pinned observation run. Its
        # mathematical peak tie is legitimate; no floating truth is claimed.
    elif group == "time":
        options.update(times=2, dz=0.2, low_bin=True, odd_phase=True)
    elif group in ("repeated", "late"):
        options.update(times=2, search=False)
    elif group == "invalid":
        options["search"] = False
    else:
        assert group in ("omit", "strided")
    raw, settings = workflow_case(mode, orders, **options)
    if group == "repeated":
        raw[1] = raw[0]
        backing = np.zeros((*raw.shape[:-1], raw.shape[-1] * 2), dtype=np.float64)
        backing[..., ::2] = raw
        raw = backing[..., ::2]
        raw.flags.writeable = False
    elif group == "omit":
        settings["filtering"]["omit_kz0"] = True
    elif group == "late":
        raw[1] = 0
    elif group == "invalid":
        if invalid == "raw-finite":
            raw[0, 0, 0, 0, 0, 0] = np.nan
        elif invalid == "flag":
            settings["carrier"]["search_carriers"] = 1
        else:
            assert invalid == "stencil"
            settings["transfer"] = simrecon.declare_otf(
                np.ones((4, 1, 1 if mode == "2d" else 8)),
                layout="radial",
                dkr_cyc_um=1.0,
                dkz_cyc_um=1.0,
            )
    return raw, settings


def case_declarations() -> list[dict[str, Any]]:
    """Freeze all exogenous cases without estimation/reconstruction."""
    cases: list[dict[str, Any]] = []
    for layout in ("radial", "full"):
        for reuse in (True, False):
            cases.append(dict(group="native", layout=layout, reuse=reuse))
        for mode, orders in (("3d", 5), ("2d", 4), ("2d", 2)):
            cases.append(dict(group="later", mode=mode, orders=orders, layout=layout))
    for reuse in (True, False):
        cases.append(dict(group="time", mode="2d", orders=4, reuse=reuse))
    for mode in ("2d", "3d"):
        cases.append(dict(group="repeated", mode=mode, orders=4))
        for search in (True, False):
            cases.append(dict(group="omit", mode=mode, search=search))
        cases.append(dict(group="late", mode=mode))
        cases.append(dict(group="strided", mode=mode))
        for invalid in ("raw-finite", "flag", "stencil"):
            cases.append(dict(group="invalid", mode=mode, invalid=invalid))
    return cases


def _input_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        canonical = np.ascontiguousarray(value.astype(value.dtype.newbyteorder("<"), copy=False))
        return dict(
            kind="ndarray",
            shape=list(value.shape),
            dtype=canonical.dtype.str,
            sha256=hashlib.sha256(canonical.tobytes()).hexdigest(),
            strides=list(value.strides),
            writeable=bool(value.flags.writeable),
        )
    if isinstance(value, dict):
        return {key: _input_value(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple | list):
        return dict(kind=type(value).__name__, values=[_input_value(item) for item in value])
    if isinstance(value, float):
        return dict(kind="float", hex=value.hex())
    if isinstance(value, simrecon.OpticalTransfer):
        return {
            name: _input_value(getattr(value, name))
            for name in (
                "samples",
                "layout",
                "dkr_cyc_um",
                "dkz_cyc_um",
                "norders",
                "source_revision",
                "reference_sha256",
            )
        }
    assert value is None or isinstance(value, str | int | bool)
    return value


def input_record(raw: Any, settings: dict[str, Any]) -> dict[str, Any]:
    return dict(schema_version=1, specimen=_input_value(raw), settings=_input_value(settings))


def input_record_digest(record: dict[str, Any]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def emit_input_record(raw: Any, settings: dict[str, Any]) -> None:
    """Emit declared input identities before the public workflow result calls."""
    print("RB117_INPUT " + input_record_digest(input_record(raw, settings)))


def declared_input_manifest() -> list[dict[str, Any]]:
    """Materialize fixed public input identities before result observations."""
    result = []
    for declaration in case_declarations():
        raw, settings = retention_case(**declaration)
        record = input_record(raw, settings)
        result.append(
            dict(
                declaration=declaration,
                inputs_sha256=input_record_digest(record),
                inputs=record,
            )
        )
    return result


def exact(actual: Any, expected: Any) -> None:
    """Compare same-environment types/array bits and scalar signed-zero bits."""
    assert type(actual) is type(expected)
    if isinstance(expected, np.ndarray):
        assert actual.shape == expected.shape and actual.dtype == expected.dtype
        assert actual.tobytes(order="C") == expected.tobytes(order="C")
    elif isinstance(expected, float):
        assert struct.pack("!d", actual) == struct.pack("!d", expected)
    elif isinstance(expected, complex):
        exact(actual.real, expected.real)
        exact(actual.imag, expected.imag)
    elif isinstance(expected, tuple):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected, strict=True):
            exact(a, e)
    elif dataclasses.is_dataclass(expected):
        for field in dataclasses.fields(expected):
            exact(getattr(actual, field.name), getattr(expected, field.name))
    else:
        assert actual == expected


def compact_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return compact_value(value.tolist())
    if isinstance(value, list | tuple):
        return tuple(compact_value(v) for v in value)
    return value


def assert_capture_projection(summary: Any, full: Any) -> None:
    parameters = full.parameters
    assert len(summary.overlap_builds) == len(parameters.overlaps)
    for index, (descriptor, build) in enumerate(
        zip(summary.overlap_builds, parameters.overlaps, strict=True)
    ):
        for name in ("index", "time_index", "direction_index", "purpose", "orders"):
            exact(getattr(descriptor, name), getattr(build, name))
        assert descriptor.index == index
        exact(descriptor.carrier_cyc_um, compact_value(build.carrier_cyc_um))
        assert not hasattr(descriptor, "spatial") and not hasattr(descriptor, "fourier")
    assert len(summary.search_trace) == len(parameters.trace)
    for compact, complete in zip(summary.search_trace, parameters.trace, strict=True):
        for name in ("kind", "time_index", "direction_index"):
            exact(getattr(compact, name), getattr(complete, name))
        expected = tuple(
            (key, compact_value(value))
            for key, value in complete.details
            if complete.kind != "coarse" or key not in ("correlation_complex", "correlation_power")
        )
        exact(compact.details, expected)
        for key, value in compact.details:
            if key == "overlap_index":
                assert 0 <= value < len(summary.overlap_builds)
    for name in (
        "image",
        "x_um",
        "y_um",
        "z_um",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
        "effective_wiener",
        "input_identities",
        "trace",
        "source_revision",
        "reference_sha256",
        "limitations",
        "intensity_unit",
        "intensity_semantics",
    ):
        exact(getattr(summary, name), getattr(full, name))
    for name in ("carriers_cyc_um", "raw_modulation", "modulation", "branches"):
        exact(getattr(summary, name), getattr(parameters, name))
    identity = dict(summary.transfer)["samples"]
    array = full.transfer.samples
    canonical = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
    assert identity.name == "transfer.samples"
    assert identity.shape == array.shape and identity.dtype == canonical.dtype.str
    assert identity.sha256 == hashlib.sha256(canonical.tobytes()).hexdigest()


def public_arrays(value: Any) -> list[Any]:
    """Visit declared public fields only; hidden owners remain C/D evidence."""
    if isinstance(value, np.ndarray):
        return [value]
    if isinstance(value, tuple):
        return [array for item in value for array in public_arrays(item)]
    if dataclasses.is_dataclass(value):
        return [
            array
            for field in dataclasses.fields(value)
            for array in public_arrays(getattr(value, field.name))
        ]
    return []
