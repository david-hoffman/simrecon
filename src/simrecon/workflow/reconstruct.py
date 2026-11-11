"""Explicit public-stage composition of the accepted native reconstruction."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..acquisition.layout import reinterpret_2d_planes
from ..acquisition.modes import prepare_acquisition_bands
from ..reconstruction.known_parameters import reconstruct_known
from ..reconstruction.parameter_estimation import estimate_parameters
from .adapters import _selected, _snapshot_raw_metadata, _time_bands
from .config import (
    _arrays_and_routes,
    _configs,
    _enum,
    _geometry,
    _scalar,
)
from .identity import _collect, _digest, _freeze, _identity, _owned
from .result import WorkflowReconstruction, _fail, _stage, _WorkflowEvent
from .transfer import _resolve_transfer, _transfer_inputs


def reconstruct_workflow(
    specimen: Any,
    *,
    acquisition: Any,
    optics: Any,
    carrier: Any,
    filtering: Any,
    specimen_identity: Any,
    transfer: Any = None,
    calibration: Any = None,
    transfer_identity: Any = None,
    off_exposures: Any = None,
    exposure_background: Any = None,
    header_timestamps: Any = None,
    header_timestamp_unit: Any = None,
    header_phases_rad: Any = None,
    channel_index: Any = None,
    plane_policy: str = "native",
) -> WorkflowReconstruction:
    """Prepare, fit and reconstruct one explicitly declared specimen channel.

    Parameters
    ----------
    specimen : numpy.ndarray or RawAcquisition
        Raw specimen observations, with explicit channel selection for records.
    acquisition, optics, carrier, filtering : Mapping
        Exact workflow schemas for acquisition, detection optics, initial
        carriers and filtering. Sampling uses micrometres and carriers cycles/um.
    specimen_identity : Mapping
        Explicit source id, count-unit label and optional content declarations.
    transfer : OpticalTransfer, PreparedOtf or Mapping, optional
        Accepted value record or explicitly decoded combined-order sections.
    calibration : Mapping, optional
        Selected raw beads, settings and identity; exclusive with transfer.
    transfer_identity : Mapping or None, optional
        Required for supplied transfer values, absent for raw calibration.
    off_exposures, exposure_background : numpy.ndarray or None, optional
        Aligned raw off frames and per-on-frame detector-count offsets.
    header_timestamps, header_phases_rad : numpy.ndarray or None, optional
        Complete decoded physical exposure streams, clocks and radians.
    header_timestamp_unit : str or None, optional
        Nonblank opaque unit label required with clocks; changes no values.
    channel_index : int or None, optional
        Original named channel selection; required even for a singleton channel.
    plane_policy : {'native', 'literal-2d-stack'}, optional
        Native dimensionality or the literal CE06 physical-stream regrouping.

    Returns
    -------
    WorkflowReconstruction
        Actual complete stages, signed image, coordinates and immutable
        declarations. Band/noise buffers retain their accepted mutability.

    Raises
    ------
    WorkflowError
        Invalid declarations, unsafe representations or failed operations.
    MemoryError
        Allocation failed; interruption also propagates without a result.
    """
    a, o, c, f = _configs(acquisition, optics, carrier, filtering)
    plane_policy = _enum(plane_policy, "plane_policy", ("native", "literal-2d-stack"))
    if (transfer is None) == (calibration is None):
        _fail("selection", "select exactly one of transfer and calibration")
    if (calibration is not None and transfer_identity is not None) or (
        transfer is not None and transfer_identity is None
    ):
        _fail("selection", "transfer identity presence disagrees with calibration selection")
    specimen_claim = _identity(specimen_identity, "specimen_identity", o)
    raw, selected_channel, raw_metadata = _selected(specimen, channel_index, a, specimen_claim)
    original = tuple(raw.shape)
    effective = _geometry(original, a, c, plane_policy)
    _arrays_and_routes(
        raw,
        a,
        c,
        original,
        effective,
        off_exposures,
        exposure_background,
        header_timestamps,
        header_timestamp_unit,
        header_phases_rad,
    )
    transfer_inputs = _transfer_inputs(
        transfer, calibration, transfer_identity, o, a["acquisition_mode"], a["norders"]
    )
    raw_metadata = _snapshot_raw_metadata(raw_metadata)
    times, directions, phases = effective[:3]
    with (
        _stage("declaration"),
        np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"),
    ):
        delta = (-1 if c["negative_angle_step"] else 1) * math.pi / directions
        linked_angles = [c["phase_start_angle_rad"] + d * delta for d in range(directions)]
        angles = linked_angles if c["angles_rad"] is None else c["angles_rad"]
        norders_in = phases // 2 + 1
        magnitude = 1 / (
            c["linespacing_um"] * (1 if a["acquisition_mode"] == "2d" else norders_in - 1)
        )
        initial = np.array(
            [(magnitude * math.cos(v), magnitude * math.sin(v)) for v in angles], dtype=np.float64
        )
        linkage = np.array(
            [
                (math.cos(v) / c["linespacing_um"], math.sin(v) / c["linespacing_um"])
                for v in linked_angles
            ],
            dtype=np.float64,
        )
        schedule = np.array(
            [f["wiener"] + (t + 1) * f["wiener_increment"] / times for t in range(times)],
            dtype=np.float64,
        )
    for row in (*initial, *linkage):
        for component in row:
            _scalar(component, "derived carrier component")
    for value in schedule:
        _scalar(value, "effective Wiener", positive=True)
    # Hash original representations before any numerical conversion. All raw and
    # aggregate extents have already passed the source/native checks.
    identities = {}
    for name, value in dict(
        specimen=specimen,
        acquisition=acquisition,
        optics=optics,
        carrier=carrier,
        filtering=filtering,
        transfer=transfer,
        calibration=calibration,
        off_exposures=off_exposures,
        exposure_background=exposure_background,
        header_timestamps=header_timestamps,
        header_phases_rad=header_phases_rad,
    ).items():
        _collect(name, value, identities)
    identities["selected_specimen"] = _digest("selected_specimen", raw)
    if off_exposures is not None:
        identities["selected_off_exposures"] = _digest("selected_off_exposures", off_exposures)
    # Independent snapshots retain every checked backing dtype until the stage
    # itself performs its accepted conversion, including wide integer rejection.
    raw = np.array(raw, copy=True)
    off_exposures = None if off_exposures is None else np.array(off_exposures, copy=True)
    exposure_background = (
        None if exposure_background is None else np.array(exposure_background, copy=True)
    )
    header_timestamps = (
        None if header_timestamps is None else np.array(header_timestamps, copy=True)
    )
    header_phases_rad = (
        None if header_phases_rad is None else np.array(header_phases_rad, copy=True)
    )
    a: dict[str, Any] = {
        key: np.array(value, copy=True) if type(value) is np.ndarray else value
        for key, value in a.items()
    }
    c: dict[str, Any] = {
        key: np.array(value, copy=True) if type(value) is np.ndarray else value
        for key, value in c.items()
    }
    trace = []

    def event(kind: str, time: int | None = None, **details: Any) -> None:
        trace.append(
            _WorkflowEvent(
                kind, kind, time, tuple((key, _freeze(value)) for key, value in details.items())
            )
        )

    event("declaration", selected_channel=selected_channel, original_shape=original)
    layout = None
    if plane_policy == "literal-2d-stack":
        with _stage("layout"):
            layout = reinterpret_2d_planes(
                raw,
                storage_order=a["storage_order"],
                off_exposures=off_exposures,
                exposure_background=exposure_background,
            )
        raw, off_exposures, exposure_background = (
            layout.images,
            layout.off_exposures,
            layout.exposure_background,
        )
    event("layout", plane_policy=plane_policy, effective_shape=effective)
    table, prepared = _resolve_transfer(transfer_inputs)
    selection = transfer_inputs.selection
    identities["consumed_transfer"] = _digest("consumed_transfer", table.samples)
    event(
        "transfer",
        selection=selection,
        consumed_transfer_sha256=identities["consumed_transfer"].sha256,
    )
    prep_options = {key: value for key, value in a.items() if key != "phase_policy"}
    with _stage("preparation"):
        bands = prepare_acquisition_bands(
            raw,
            **prep_options,
            **o,
            off_exposures=off_exposures,
            exposure_background=exposure_background,
            header_timestamps=header_timestamps,
            header_phases_rad=header_phases_rad,
            linespacing_um=c["linespacing_um"],
            phase_start_angle_rad=c["phase_start_angle_rad"],
            negative_angle_step=c["negative_angle_step"],
        )
    identities["prepared_quadratures"] = _digest("prepared_quadratures", bands.quadratures)
    event("preparation", input_scale=bands.input_scale, phase_policy=a["phase_policy"])
    with _stage("estimation"):
        parameters = estimate_parameters(
            bands,
            table,
            initial_carriers_cyc_um=initial,
            **o,
            search_carriers=c["search_carriers"],
            use_time0_carriers=c["use_time0_carriers"],
            amplitude_floors=c["amplitude_floors"],
            fit_all_phases=c["fit_all_phases"],
            omit_kz0=f["omit_kz0"],
        )
    event("estimation", branches=parameters.branches)
    reconstructions = []
    filter_options = {
        key: value for key, value in f.items() if key not in ("wiener", "wiener_increment")
    }
    for time in range(times):
        with _stage("reconstruction", time_index=time):
            known = reconstruct_known(
                _time_bands(bands, time),
                table,
                carriers_cyc_um=parameters.carriers_cyc_um[time],
                modulation=parameters.modulation[time],
                **o,
                **filter_options,
                wiener=float(schedule[time]),
                wiener_increment=0.0,
            )
        reconstructions.append(known)
        event(
            "reconstruction",
            time,
            effective_wiener=float(schedule[time]),
            parameter_time_index=time,
        )
    with _stage("result"):
        image = _owned(np.concatenate([r.image for r in reconstructions], axis=0))
        coordinates = tuple(
            _owned(getattr(reconstructions[0], key)) for key in ("x_um", "y_um", "z_um")
        )
        initial, linkage, schedule = (_owned(v) for v in (initial, linkage, schedule))
        sources = tuple(
            dict(
                specimen_identity=_freeze(specimen_claim),
                transfer_identity=transfer_inputs.transfer_identity,
                calibration_identity=transfer_inputs.calibration_identity,
                selected_channel=selected_channel,
                raw_acquisition_metadata=raw_metadata,
                decoded_transfer_binding=transfer_inputs.binding,
            ).items()
        )
        settings = tuple(
            dict(
                acquisition=tuple((key, _freeze(value)) for key, value in a.items()),
                optics=tuple(o.items()),
                carrier=tuple((key, _freeze(value)) for key, value in c.items()),
                filtering=tuple(f.items()),
                plane_policy=plane_policy,
                original_shape=original,
                effective_shape=effective,
                norders_in=norders_in,
                phase_policy=a["phase_policy"],
                calibration_selection=selection,
                header_timestamp_unit=header_timestamp_unit,
            ).items()
        )
        limits = [
            "mathematical-source-target-only",
            "historical-binary-agreement-unqualified",
            "recovery-and-resolution-unqualified",
            "selected-channel-independent-state",
            "external-IVE-file-binding-unqualified",
            "input-unit-label-not-specimen-mass",
        ]
        if plane_policy == "literal-2d-stack":
            limits.append("literal-2d-stream-regrouping")
        if a["acquisition_mode"] == "2d":
            if a["axial_zoom"] > 1:
                limits.append("true2d-extra-axial-planes-zero")
            if a["dz_um"] == 0:
                limits.append("true2d-axial-pitch-undeclared")
        event("result", output_shape=image.shape)
        return WorkflowReconstruction(
            image=image,
            x_um=coordinates[0],
            y_um=coordinates[1],
            z_um=coordinates[2],
            intensity_unit=specimen_claim["intensity_unit"],
            intensity_semantics="C-scaled-camera-corrected-equalized-phase-reconstruction",
            bands=bands,
            parameters=parameters,
            transfer=table,
            calibration=prepared,
            layout=layout,
            reconstructions=tuple(reconstructions),
            initial_carriers_cyc_um=initial,
            phase_linkage_carriers_cyc_um=linkage,
            effective_wiener=schedule,
            input_identities=tuple(identities[key] for key in sorted(identities)),
            source_declarations=sources,
            resolved_settings=settings,
            trace=tuple(trace),
            limitations=tuple(limits),
        )
