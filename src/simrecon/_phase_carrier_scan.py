"""Evaluate independent observable-phase fits for an ordered carrier table."""

from typing import Any

import numpy as np
import numpy.typing as npt

from ._array_validation import conversion_errors
from ._model import SimreconError
from ._observable_volume_phase_estimation import (
    ObservableVolumePhaseEstimate,
    estimate_observable_volume_phases,
)
from ._volume_order_otf import VolumeOrderOtf
from .volume_reconstruction import _calibration, _container, _integer, _real_array, _real_scalar


def _candidates(value: Any) -> tuple[tuple[int, int], ...]:
    """Snapshot the complete table without rounding or periodic reduction."""
    code = "invalid_volume_phase_carrier_candidates"
    with conversion_errors(code, "candidate extraction failed"):
        if type(value) is np.ndarray:
            if value.dtype.kind not in "iu" or value.ndim != 2 or value.shape[1] != 2:
                raise SimreconError(code, "expected an integer (C,2) table")
            rows = value.tolist()
        else:
            rows = _container(value, len(value) if type(value) in (tuple, list) else 0, code)
        if not rows:
            raise SimreconError(code, "expected at least one candidate")
        result = []
        for row in rows:
            ky, kx = (_integer(v, code) for v in _container(row, 2, code))
            result.append((ky, kx))
        return tuple(result)


def scan_volume_phase_carriers(
    images: npt.NDArray[np.generic],
    *,
    order_otf: VolumeOrderOtf,
    candidate_carriers_yx: object,
    initial_phases_rad: npt.NDArray[np.generic],
    max_nfev: int,
    gradient_tolerance: float,
    step_tolerance: float,
    source: str,
) -> tuple[ObservableVolumePhaseEstimate, ...]:
    """Fit all exposure phases independently for every declared integer carrier.

    Parameters
    ----------
    images : numpy.ndarray
        Finite real observations with phase/z/y/x axes and at least five phases.
    order_otf : VolumeOrderOtf
        Fixed complex calibration, already paired to the specimen gauge/grid.
    candidate_carriers_yx : tuple, list or numpy.ndarray
        Nonempty exact tuple/list of exact two-integer tuple/list rows, or a
        plain integer ndarray of shape (C,2). Original values/order are retained.
    initial_phases_rad : numpy.ndarray
        Shared initial exposure commands in radians; not measured actual phases.
    max_nfev : int
        Positive residual evaluation limit applied separately to each solve.
    gradient_tolerance, step_tolerance : float
        Per-row binary64 tolerances strictly between machine epsilon and one.
    source : str
        Nonblank caller label, retained unchanged.

    Returns
    -------
    tuple of ObservableVolumePhaseEstimate
        Fresh independent records in caller order, including unavailable rows,
        duplicates and detector-period aliases. No winner is selected.

    Raises
    ------
    SimreconError
        For malformed candidates or inherited shared-input/numerical failures.
        Allocation failures and unrelated exceptions propagate.

    Notes
    -----
    Every row starts from the same commands using the existing all-five-order
    periodic observable-subspace objective. Calibration is fixed; gains are not
    fitted. A local fit supplies no global or physical uniqueness guarantee.
    """
    with np.errstate(all="ignore"):
        candidates = _candidates(candidate_carriers_yx)
        image_code = "invalid_volume_phase_estimation_images"
        if (
            type(images) is not np.ndarray
            or images.ndim != 4
            or images.shape[0] < 5
            or 0 in images.shape[1:]
        ):
            raise SimreconError(image_code, "images must have shape (N>=5,z>0,y>0,x>0)")
        values = _real_array(
            images, images.shape, image_code, "nonfinite_volume_phase_estimation_images"
        )
        angles = _real_array(
            initial_phases_rad,
            (values.shape[0],),
            "invalid_volume_phase_estimation_initial_phases",
            "nonfinite_volume_phase_estimation_initial_phases",
        )
        try:
            transfers, spacing = _calibration(order_otf, values.shape[1:])
            oz, oy, ox = order_otf.origin_zyx
            with conversion_errors(
                "invalid_volume_phase_estimation_otf", "origin conversion failed"
            ):
                origin = (int(oz), int(oy), int(ox))
            orders = VolumeOrderOtf(
                values=transfers,
                fz_per_um=order_otf.fz_per_um.copy(),
                fy_per_um=order_otf.fy_per_um.copy(),
                fx_per_um=order_otf.fx_per_um.copy(),
                voxel_size_um=spacing,
                origin_zyx=origin,
                source=order_otf.source,
            )
        except (SimreconError, AttributeError) as error:
            raise SimreconError(
                "invalid_volume_phase_estimation_otf", "invalid calibration"
            ) from error
        controls = "invalid_volume_phase_estimation_controls"
        limit = _integer(max_nfev, controls)
        gtol, xtol = (_real_scalar(v, controls) for v in (gradient_tolerance, step_tolerance))
        if limit < 1 or not (np.finfo(float).eps < gtol < 1 and np.finfo(float).eps < xtol < 1):
            raise SimreconError(controls, "invalid evaluation limit or tolerance")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")
        # No row cache, warm start or exception handler: even duplicate carriers
        # execute a fresh estimator, and a failure in any later row aborts.
        return tuple(
            estimate_observable_volume_phases(
                values,
                order_otf=orders,
                carrier_bins_yx=carrier,
                initial_phases_rad=angles,
                max_nfev=limit,
                gradient_tolerance=gtol,
                step_tolerance=xtol,
                source=source,
            )
            for carrier in candidates
        )
