"""Explicit public-stage composition of the accepted native reconstruction."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..acquisition.layout import reinterpret_2d_planes
from ..acquisition.modes import prepare_acquisition_bands
from ..reconstruction.known_parameters import reconstruct_known
from ..reconstruction.parameter_estimation import estimate_parameters
from .adapters import select_specimen_channel, select_time_bands, snapshot_raw_metadata
from .config import (
    _enum,
    _scalar,
    resolve_workflow_settings,
    validate_workflow_arrays_and_routes,
    validate_workflow_geometry,
)
from .identity import (
    array_identity,
    collect_array_identities,
    freeze_declarations,
    owned_readonly_array,
    validate_source_identity,
)
from .result import WorkflowReconstruction, _WorkflowEvent, raise_workflow_error, workflow_stage
from .transfer import resolve_optical_transfer, validate_transfer_inputs


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

    Notes
    -----
    This operation composes already decoded arrays and explicit declarations;
    source file claims are validated as metadata, not opened or authenticated.
    Geometry, backing storage and route prerequisites are checked before
    array-sized snapshots. Input hashes precede numerical conversion, and
    stage inputs receive independent copies after validation. Retained band
    buffers keep their stage-defined mutability; final image, coordinates and
    declaration snapshots have separate ownership.

    Acquisition preparation and estimation run across the effective time
    sequence. Known reconstruction then consumes one-time band views in order,
    with the corresponding parameters and effective Wiener value. Stage
    failures retain their cause and available time/direction context.
    """
    acquisition_settings, optics_settings, carrier_settings, filtering_settings = (
        resolve_workflow_settings(acquisition, optics, carrier, filtering)
    )
    plane_policy = _enum(plane_policy, "plane_policy", ("native", "literal-2d-stack"))
    if (transfer is None) == (calibration is None):
        raise_workflow_error("selection", "select exactly one of transfer and calibration")
    if (calibration is not None and transfer_identity is not None) or (
        transfer is not None and transfer_identity is None
    ):
        raise_workflow_error(
            "selection", "transfer identity presence disagrees with calibration selection"
        )
    specimen_claim = validate_source_identity(
        specimen_identity, "specimen_identity", optics_settings
    )
    raw, selected_channel, raw_metadata = select_specimen_channel(
        specimen, channel_index, acquisition_settings, specimen_claim
    )
    original = tuple(raw.shape)
    effective = validate_workflow_geometry(
        original, acquisition_settings, carrier_settings, plane_policy
    )
    validate_workflow_arrays_and_routes(
        raw,
        acquisition_settings,
        carrier_settings,
        original,
        effective,
        off_exposures,
        exposure_background,
        header_timestamps,
        header_timestamp_unit,
        header_phases_rad,
    )
    transfer_inputs = validate_transfer_inputs(
        transfer,
        calibration,
        transfer_identity,
        optics_settings,
        acquisition_settings["acquisition_mode"],
        acquisition_settings["norders"],
    )
    raw_metadata = snapshot_raw_metadata(raw_metadata)
    times, directions, phases = effective[:3]
    with (
        workflow_stage("declaration"),
        np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"),
    ):
        delta = (-1 if carrier_settings["negative_angle_step"] else 1) * math.pi / directions
        linked_angles = [
            carrier_settings["phase_start_angle_rad"] + d * delta for d in range(directions)
        ]
        angles = (
            linked_angles
            if carrier_settings["angles_rad"] is None
            else carrier_settings["angles_rad"]
        )
        norders_in = phases // 2 + 1
        magnitude = 1 / (
            carrier_settings["linespacing_um"]
            * (1 if acquisition_settings["acquisition_mode"] == "2d" else norders_in - 1)
        )
        initial = np.array(
            [(magnitude * math.cos(v), magnitude * math.sin(v)) for v in angles], dtype=np.float64
        )
        linkage = np.array(
            [
                (
                    math.cos(v) / carrier_settings["linespacing_um"],
                    math.sin(v) / carrier_settings["linespacing_um"],
                )
                for v in linked_angles
            ],
            dtype=np.float64,
        )
        schedule = np.array(
            [
                filtering_settings["wiener"]
                + (t + 1) * filtering_settings["wiener_increment"] / times
                for t in range(times)
            ],
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
        collect_array_identities(name, value, identities)
    identities["selected_specimen"] = array_identity("selected_specimen", raw)
    if off_exposures is not None:
        identities["selected_off_exposures"] = array_identity(
            "selected_off_exposures", off_exposures
        )
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
    acquisition_settings: dict[str, Any] = {
        key: np.array(value, copy=True) if type(value) is np.ndarray else value
        for key, value in acquisition_settings.items()
    }
    carrier_settings: dict[str, Any] = {
        key: np.array(value, copy=True) if type(value) is np.ndarray else value
        for key, value in carrier_settings.items()
    }
    trace = []

    def event(kind: str, time: int | None = None, **details: Any) -> None:
        trace.append(
            _WorkflowEvent(
                kind,
                kind,
                time,
                tuple((key, freeze_declarations(value)) for key, value in details.items()),
            )
        )

    event("declaration", selected_channel=selected_channel, original_shape=original)
    layout = None
    if plane_policy == "literal-2d-stack":
        with workflow_stage("layout"):
            layout = reinterpret_2d_planes(
                raw,
                storage_order=acquisition_settings["storage_order"],
                off_exposures=off_exposures,
                exposure_background=exposure_background,
            )
        raw, off_exposures, exposure_background = (
            layout.images,
            layout.off_exposures,
            layout.exposure_background,
        )
    event("layout", plane_policy=plane_policy, effective_shape=effective)
    table, prepared = resolve_optical_transfer(transfer_inputs)
    selection = transfer_inputs.selection
    identities["consumed_transfer"] = array_identity("consumed_transfer", table.samples)
    event(
        "transfer",
        selection=selection,
        consumed_transfer_sha256=identities["consumed_transfer"].sha256,
    )
    prep_options = {
        key: value for key, value in acquisition_settings.items() if key != "phase_policy"
    }
    with workflow_stage("preparation"):
        bands = prepare_acquisition_bands(
            raw,
            **prep_options,
            **optics_settings,
            off_exposures=off_exposures,
            exposure_background=exposure_background,
            header_timestamps=header_timestamps,
            header_phases_rad=header_phases_rad,
            linespacing_um=carrier_settings["linespacing_um"],
            phase_start_angle_rad=carrier_settings["phase_start_angle_rad"],
            negative_angle_step=carrier_settings["negative_angle_step"],
        )
    identities["prepared_quadratures"] = array_identity("prepared_quadratures", bands.quadratures)
    event(
        "preparation",
        input_scale=bands.input_scale,
        phase_policy=acquisition_settings["phase_policy"],
    )
    with workflow_stage("estimation"):
        parameters = estimate_parameters(
            bands,
            table,
            initial_carriers_cyc_um=initial,
            **optics_settings,
            search_carriers=carrier_settings["search_carriers"],
            use_time0_carriers=carrier_settings["use_time0_carriers"],
            amplitude_floors=carrier_settings["amplitude_floors"],
            fit_all_phases=carrier_settings["fit_all_phases"],
            omit_kz0=filtering_settings["omit_kz0"],
        )
    event("estimation", branches=parameters.branches)
    reconstructions = []
    filter_options = {
        key: value
        for key, value in filtering_settings.items()
        if key not in ("wiener", "wiener_increment")
    }
    for time in range(times):
        with workflow_stage("reconstruction", time_index=time):
            known = reconstruct_known(
                select_time_bands(bands, time),
                table,
                carriers_cyc_um=parameters.carriers_cyc_um[time],
                modulation=parameters.modulation[time],
                **optics_settings,
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
    with workflow_stage("result"):
        image = owned_readonly_array(np.concatenate([r.image for r in reconstructions], axis=0))
        coordinates = tuple(
            owned_readonly_array(getattr(reconstructions[0], key))
            for key in ("x_um", "y_um", "z_um")
        )
        initial, linkage, schedule = (owned_readonly_array(v) for v in (initial, linkage, schedule))
        sources = tuple(
            dict(
                specimen_identity=freeze_declarations(specimen_claim),
                transfer_identity=transfer_inputs.transfer_identity,
                calibration_identity=transfer_inputs.calibration_identity,
                selected_channel=selected_channel,
                raw_acquisition_metadata=raw_metadata,
                decoded_transfer_binding=transfer_inputs.binding,
            ).items()
        )
        settings = tuple(
            dict(
                acquisition=tuple(
                    (key, freeze_declarations(value)) for key, value in acquisition_settings.items()
                ),
                optics=tuple(optics_settings.items()),
                carrier=tuple(
                    (key, freeze_declarations(value)) for key, value in carrier_settings.items()
                ),
                filtering=tuple(filtering_settings.items()),
                plane_policy=plane_policy,
                original_shape=original,
                effective_shape=effective,
                norders_in=norders_in,
                phase_policy=acquisition_settings["phase_policy"],
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
        if acquisition_settings["acquisition_mode"] == "2d":
            if acquisition_settings["axial_zoom"] > 1:
                limits.append("true2d-extra-axial-planes-zero")
            if acquisition_settings["dz_um"] == 0:
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
