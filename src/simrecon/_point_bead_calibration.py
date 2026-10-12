"""Compose declared correction and known-phase point-bead response preparation."""

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._acquisition import RawAcquisition
from ._empirical_response import EmpiricalVolumeResponse, prepare_empirical_volume_response
from ._linear_response import correct_linear_response
from ._model import SimreconError
from ._volume_phase import VolumePhaseComponents, separate_volume_phases


@dataclass(frozen=True)
class PointBeadCalibration:
    """Observed components, relative responses and independent declarations.

    Attributes
    ----------
    components : VolumePhaseComponents
        Owned observed dc and positive first/second harmonics, in output units.
    response : EmpiricalVolumeResponse
        Owned dimensionless full signed Cartesian responses for orders 0,+1,+2.
    provenance : dict
        Explicit group, complete source metadata, supplied/applied correction,
        actual phases and sampling, selected model and retained response gauge.

    Notes
    -----
    Bindings are frozen; arrays remain mutable and metadata is read-only by
    convention. Direct construction adds no validation or persistence promise.
    """

    components: VolumePhaseComponents
    response: EmpiricalVolumeResponse
    provenance: dict[str, Any]


def calibrate_raw_point_bead(
    acquisition: RawAcquisition,
    *,
    group: dict[str, int],
    offset: int | float | npt.NDArray[Any],
    response: int | float | npt.NDArray[Any],
    output_unit: str,
    phases_rad: npt.NDArray[Any],
    voxel_size_um: object,
) -> PointBeadCalibration:
    """Calibrate one explicitly selected known-phase raw point-bead group.

    Parameters
    ----------
    acquisition : RawAcquisition
        Valid sim_beads declaration with explicit orientation, phase, z, y, x.
        Optional time/channel dimensions retain their declared meanings.
    group : dict
        Plain dict naming every present time/channel/orientation axis, each
        with a plain nonboolean int index in its nonnegative declared range.
    offset, response : int, float or numpy.ndarray
        Supplied linear correction coefficients, either plain scalars or maps
        matching the entire canonical acquisition shape. Response is positive.
    output_unit : str
        Required nonempty converted intensity label; source label is retained.
    phases_rad : numpy.ndarray
        Actual fundamental phases in exposure order, in radians, with the
        known-phase separator's real numeric representation and rank domain.
    voxel_size_um : tuple, list or numpy.ndarray
        Explicit authoritative z/y/x spacing in micrometres, with the empirical
        response primitive's finite-positive scalar and frequency domain.

    Returns
    -------
    PointBeadCalibration
        Observed separated components, commonly normalized signed response and
        independent supplied/applied snapshots. No caller storage is aliased.

    Raises
    ------
    SimreconError
        Invalid acquisition, kind, absent z or group yields a stable
        invalid_point_bead_* code. Existing stage errors propagate unchanged.

    Notes
    -----
    Correct and validate the whole acquisition, extract the named group, fit
    actual known phases, then prepare the empirical response, each exactly once.
    Nominal commands are metadata only. Supplied spacing is authoritative even
    when acquisition sampling is unknown or different. Bead-size compensation
    is identity; the observed peak and supplied phase-origin gauge remain.
    Common normalization loses brightness scale and supplies no absolute
    throughput, physical validity, streaming or working-set guarantee.
    Allocation failures and unrelated exceptions propagate without masking.
    """
    if not isinstance(acquisition, RawAcquisition):
        raise SimreconError(
            "invalid_point_bead_acquisition", "acquisition must be a RawAcquisition"
        )
    if acquisition.acquisition_kind != "sim_beads":
        raise SimreconError("invalid_point_bead_kind", "acquisition kind must be sim_beads")
    if "z" not in acquisition.axes:
        raise SimreconError("invalid_point_bead_axes", "an explicit z axis is required")

    group_axes = tuple(
        axis for axis in acquisition.axes if axis in ("time", "channel", "orientation")
    )
    if type(group) is not dict or set(group) != set(group_axes):
        raise SimreconError(
            "invalid_point_bead_group", "group must name exactly the present group axes"
        )
    for axis in group_axes:
        index = group[axis]
        count = acquisition.data.shape[acquisition.axes.index(axis)]
        if type(index) is not int or not 0 <= index < count:
            raise SimreconError(
                "invalid_point_bead_group", "group indices must be plain in-range ints"
            )

    correction = correct_linear_response(
        acquisition, offset=offset, response=response, output_unit=output_unit
    )
    selection = tuple(
        group[axis] if axis in group_axes else slice(None) for axis in correction.axes
    )
    components = separate_volume_phases(correction.data[selection], phases_rad=phases_rad)
    empirical = prepare_empirical_volume_response(
        components.dc, c1=components.c1, c2=components.c2, voxel_size_um=voxel_size_um
    )

    # Successful stages established the representation/conversion domains.
    # Keep original storage types separately from native numerical declarations.
    with np.errstate(all="ignore"):
        applied_phases = phases_rad.astype(np.float64, order="C", copy=True)
    supplied_spacing = (
        voxel_size_um.copy(order="C")
        if type(voxel_size_um) is np.ndarray
        else copy.deepcopy(voxel_size_um)
    )
    provenance = {
        "model": "point_bead_identity_v1",
        "group": group.copy(),
        "source_metadata": correction.source_metadata,
        "linear_response": correction.provenance,
        "phases_rad": {
            "source": "supplied_actual",
            "supplied": phases_rad.copy(order="C"),
            "applied": applied_phases,
        },
        "voxel_size_um": {
            "source": "supplied",
            "supplied": supplied_spacing,
            "applied": empirical.voxel_size_um,
        },
        "bead_compensation": "identity",
        "response_gauge": "observed_dc_peak_with_supplied_phase_origin",
    }
    return PointBeadCalibration(components, empirical, provenance)
