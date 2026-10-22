"""Calibrate a declared discrete finite emission profile before localization."""

import copy
import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from ._acquisition import RawAcquisition
from ._bead_peak import locate_bead_peak
from ._empirical_response import EmpiricalVolumeResponse
from ._empirical_transfer import _integers, _phasor, _real
from ._linear_response import correct_linear_response
from ._model import SimreconError
from ._volume_otf import _frequencies, _spacing, _triple
from ._volume_phase import VolumePhaseComponents, separate_volume_phases


@dataclass(frozen=True)
class FiniteBeadCalibration:
    """Observed harmonics, compensated response and independent declarations.

    Attributes
    ----------
    components : VolumePhaseComponents
        Original observed dc and positive first/second harmonics in output units.
    response : EmpiricalVolumeResponse
        Commonly normalized complex responses centered at the compensated peak.
    provenance : dict
        Owned supplied/applied declarations and profile/localization diagnostics.

    Notes
    -----
    Bindings are frozen. Arrays and the plain metadata dict remain mutable.
    Direct construction supplies no validation or deep immutability.
    """

    components: VolumePhaseComponents
    response: EmpiricalVolumeResponse
    provenance: dict[str, Any]


def _fraction(value: Any) -> Fraction:
    """Interpret a represented real component exactly."""
    return Fraction.from_float(float(value))


def _finite_round(value: Fraction) -> float:
    """Round a required component, translating only actual range overflow."""
    try:
        return float(value)
    except OverflowError as error:
        raise SimreconError(
            "unrepresentable_finite_bead_response", "required component exceeds finite range"
        ) from error


def _transform(values: npt.NDArray[Any], *, inverse: bool = False) -> npt.NDArray[np.complex128]:
    """Execute a public transform with scoped arithmetic diagnostics."""
    operation = np.fft.ifftn if inverse else np.fft.fftn
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            result = operation(values, axes=(0, 1, 2), norm="backward")
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(
            "finite_bead_transform_failure", "numerical transform failure"
        ) from error
    if not np.isfinite(result).all():
        raise SimreconError("finite_bead_transform_failure", "scaled transform must be finite")
    return result


def _profile(
    supplied: object, shape: tuple[int, ...], minimum: float
) -> tuple[npt.NDArray[Any], npt.NDArray[np.float64], npt.NDArray[np.complex128]]:
    """Snapshot and normalize weights, then certify every computed native node."""
    code = "invalid_finite_bead_profile"
    if (
        type(supplied) is not np.ndarray
        or supplied.dtype.kind != "f"
        or supplied.dtype.itemsize != 8
        or supplied.ndim != 3
        or 0 in supplied.shape
        or supplied.shape != shape
    ):
        raise SimreconError(code, "profile must be a plain float64 volume of the selected shape")
    snapshot = supplied.copy(order="C")
    if not np.isfinite(snapshot).all() or np.any(snapshot < 0):
        raise SimreconError(code, "profile weights must be finite and nonnegative")
    mass = sum((_fraction(v) for v in snapshot.flat), Fraction())
    if mass <= 0:
        raise SimreconError(code, "profile must have positive exact mass")
    normalized = (
        np.array([float(_fraction(v) / mass) for v in snapshot.flat], dtype=np.float64)
        .reshape(shape)
        .copy(order="C")
    )
    identity = np.count_nonzero(snapshot) == 1 and snapshot.flat[0] > 0
    if identity:
        transfer = np.ones(shape, dtype=np.complex128)
    else:
        transfer = _transform(normalized)
        transfer[0, 0, 0] = 1 + 0j
    # Squaring exact rational coordinates avoids both hypot rounding and loss
    # of the q0 tail when adding the acceptance allowance to the minimum.
    eta = 128 * snapshot.size * Fraction(1, 2**52) + 4 * snapshot.size * Fraction(1, 2**1074)
    for index in np.ndindex(shape):
        boundary = _fraction(minimum) + (0 if identity or index == (0, 0, 0) else eta)
        value = transfer[index]
        if _fraction(value.real) ** 2 + _fraction(value.imag) ** 2 < boundary**2:
            raise SimreconError(
                "unstable_finite_bead_transfer", "a native profile node cannot certify the minimum"
            )
    return snapshot, normalized, transfer


def _normalized_spectrum(
    observed: npt.NDArray[np.float64 | np.complex128], mass: Fraction, *, zero_order: bool
) -> npt.NDArray[np.complex128]:
    """Transform uncentered samples at component scale and restore original mass."""
    gain = float(max(np.max(np.abs(observed.real)), np.max(np.abs(observed.imag)))) or 1.0
    scaled = np.empty(observed.shape, dtype=np.complex128)
    scaled.real = observed.real / gain
    scaled.imag = observed.imag / gain
    transformed = _transform(scaled)
    scale = _fraction(gain) / mass
    result = np.empty(observed.shape, dtype=np.complex128)
    for index in np.ndindex(observed.shape):
        # The whole scaled transform has already been validated. The exact dc
        # identity is assigned before any restoration/range check of that bin.
        if zero_order and index == (0, 0, 0):
            result[index] = 1 + 0j
        else:
            value = transformed[index]
            result[index] = complex(
                _finite_round(_fraction(value.real) * scale),
                _finite_round(_fraction(value.imag) * scale),
            )
    return result


def _divide(numerator: Any, divisor: Any) -> complex:
    """Divide represented components without a floating square or reciprocal."""
    ar, ai = _fraction(numerator.real), _fraction(numerator.imag)
    pr, pi = _fraction(divisor.real), _fraction(divisor.imag)
    square = pr * pr + pi * pi
    return complex(
        _finite_round((ar * pr + ai * pi) / square),
        _finite_round((ai * pr - ar * pi) / square),
    )


def _localization(q0: npt.NDArray[np.complex128]) -> npt.NDArray[np.float64]:
    """Restore only the required real part of a safely scaled inverse."""
    gain = float(max(np.max(np.abs(q0.real)), np.max(np.abs(q0.imag)))) or 1.0
    scaled = np.empty(q0.shape, dtype=np.complex128)
    scaled.real = q0.real / gain
    scaled.imag = q0.imag / gain
    transformed = _transform(scaled, inverse=True)
    return (
        np.array(
            [_finite_round(_fraction(v) * _fraction(gain)) for v in transformed.real.flat],
            dtype=np.float64,
        )
        .reshape(q0.shape)
        .copy(order="C")
    )


def _center(
    compensated: npt.NDArray[np.complex128], origin: tuple[int, int, int]
) -> npt.NDArray[np.complex128]:
    """Apply the one observed origin phase with component-safe rotation."""
    result = np.empty_like(compensated)
    shape = compensated.shape[1:]
    for index in np.ndindex(shape):
        cycles = (
            sum(
                (Fraction(k * b, n) for k, b, n in zip(index, origin, shape, strict=True)),
                Fraction(),
            )
            % 1
        )
        # The shared helper uses the negative-exponential convention.
        phase = _phasor((-cycles) % 1, 0.0)
        pr, pi = _fraction(phase.real), _fraction(phase.imag)
        for order in range(3):
            value = compensated[(order, *index)]
            ar, ai = _fraction(value.real), _fraction(value.imag)
            result[(order, *index)] = complex(
                _finite_round(ar * pr - ai * pi), _finite_round(ar * pi + ai * pr)
            )
    result[0, 0, 0, 0] = 1 + 0j
    return np.array(np.fft.fftshift(result, axes=(1, 2, 3)), order="C", copy=True)


def calibrate_raw_finite_bead(
    acquisition: RawAcquisition,
    *,
    group: dict[str, int],
    offset: int | float | npt.NDArray[Any],
    response: int | float | npt.NDArray[Any],
    output_unit: str,
    phases_rad: npt.NDArray[Any],
    voxel_size_um: object,
    bead_profile: npt.NDArray[Any],
    calibration_carrier_bins: object,
    min_profile_transfer: object,
) -> FiniteBeadCalibration:
    """Remove a supplied native profile before observing the response origin.

    Parameters
    ----------
    acquisition : RawAcquisition
        Declared sim_beads acquisition with explicit orientation/phase/z/y/x.
    group : dict
        Exactly the present time/channel/orientation names with plain int indices.
    offset, response : int, float or numpy.ndarray
        Scalar or full canonical-array camera coefficients. Correction precedes
        selection; nonselected invalid samples still reject.
    output_unit : str
        Nonempty corrected intensity unit.
    phases_rad : numpy.ndarray
        Supplied actual fundamental exposure phases in radians.
    voxel_size_um : tuple, list or numpy.ndarray
        Authoritative finite positive z/y/x spacing in micrometres.
    bead_profile : numpy.ndarray
        Plain float64 nonnegative relative site weights on the selected grid.
        The declared anchor is index zero; no symmetry or peak is required.
    calibration_carrier_bins : tuple or list
        Known nonboolean integer y/x carrier bins, retained unreduced.
    min_profile_transfer : int or float
        Explicit dimensionless minimum in (0, 1], including the exact computed
        profile-transform certificate allowance at every native node.

    Returns
    -------
    FiniteBeadCalibration
        Original observed harmonics, compensated complex responses and independent
        supplied/applied snapshots including native localization diagnostics.

    Raises
    ------
    SimreconError
        Invalid declarations, uncertifiable profile, nonpositive original mass,
        absent/ambiguous compensated peak, transform or required-stage range
        failure. Existing correction, separation and frequency errors propagate.

    Notes
    -----
    The exact original observed dc mass normalizes all orders once. Native
    division by P[k-m*kc] precedes localization; only the real compensated dc
    inverse supplies the unique positive peak. All returned spectra remain
    complex and share that origin and the supplied separation phase gauge.
    This discrete periodic estimator certifies neither physical bead geometry
    nor detection validity. It estimates no phase, carrier or continuous center.
    Caller buffers, NumPy modes and unrelated warning categories are preserved.
    Allocation failures and unrelated dependency exceptions propagate.
    """
    if not isinstance(acquisition, RawAcquisition):
        raise SimreconError("invalid_finite_bead_acquisition", "expected RawAcquisition")
    if acquisition.acquisition_kind != "sim_beads":
        raise SimreconError("invalid_finite_bead_kind", "acquisition kind must be sim_beads")
    if "z" not in acquisition.axes:
        raise SimreconError("invalid_finite_bead_axes", "an explicit z axis is required")
    group_axes = tuple(a for a in acquisition.axes if a in ("time", "channel", "orientation"))
    if type(group) is not dict or set(group) != set(group_axes):
        raise SimreconError("invalid_finite_bead_group", "group must name every present group axis")
    for axis in group_axes:
        index = group[axis]
        if (
            type(index) is not int
            or not 0 <= index < acquisition.data.shape[acquisition.axes.index(axis)]
        ):
            raise SimreconError(
                "invalid_finite_bead_group", "group index must be a plain in-range int"
            )
    selected_group = group.copy()
    carrier = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
    with np.errstate(all="ignore"):
        minimum = _real(min_profile_transfer, "invalid_finite_bead_transfer_threshold")
        if not 0 < minimum <= 1:
            raise SimreconError(
                "invalid_finite_bead_transfer_threshold", "minimum must be in (0, 1]"
            )
        supplied_phases = (
            phases_rad.copy(order="C") if type(phases_rad) is np.ndarray else phases_rad
        )
        supplied_spacing = (
            voxel_size_um.copy(order="C")
            if type(voxel_size_um) is np.ndarray
            else copy.deepcopy(voxel_size_um)
        )
        # Profile snapshot precedes the inherited numerical acquisition stages.
        # Its transform/certificate follows separation and the original mass.
        profile_snapshot = (
            bead_profile.copy(order="C") if type(bead_profile) is np.ndarray else bead_profile
        )
        correction = correct_linear_response(
            acquisition, offset=offset, response=response, output_unit=output_unit
        )
        selection = tuple(
            selected_group[a] if a in group_axes else slice(None) for a in correction.axes
        )
        components = separate_volume_phases(correction.data[selection], phases_rad=supplied_phases)
        mass = sum((_fraction(v) for v in components.dc.flat), Fraction())
        if mass <= 0:
            raise SimreconError(
                "nonpositive_empirical_response_mass", "exact dc mass must be positive"
            )
        spacing = tuple(_spacing(v) for v in _triple(supplied_spacing, "invalid_otf_voxel_size"))
        dz, dy, dx = spacing
        shape = components.dc.shape
        fz, fy, fx = (_frequencies(n, d) for n, d in zip(shape, spacing, strict=True))
        supplied_profile, normalized_profile, profile = _profile(profile_snapshot, shape, minimum)
        compensated = np.empty((3, *shape), dtype=np.complex128)
        for order, observed in enumerate((components.dc, components.c1, components.c2)):
            spectrum = _normalized_spectrum(observed, mass, zero_order=order == 0)
            for index in np.ndindex(shape):
                shifted = (
                    index[0],
                    (index[1] - order * carrier[0]) % shape[1],
                    (index[2] - order * carrier[1]) % shape[2],
                )
                compensated[(order, *index)] = _divide(spectrum[index], profile[shifted])
        localization = _localization(compensated[0])
        origin = locate_bead_peak(localization).index_zyx
        values = _center(compensated, origin)
        empirical = EmpiricalVolumeResponse(values, fz, fy, fx, (dz, dy, dx), origin)
        applied_phases = supplied_phases.astype(np.float64, order="C", copy=True)
    provenance = {
        "model": "discrete_finite_bead_v1",
        "group": selected_group,
        "source_metadata": correction.source_metadata,
        "linear_response": correction.provenance,
        "phases_rad": {
            "source": "supplied_actual",
            "supplied": supplied_phases,
            "applied": applied_phases,
        },
        "voxel_size_um": {
            "source": "supplied",
            "supplied": supplied_spacing,
            "applied": empirical.voxel_size_um,
        },
        "bead_compensation": "native_periodic_profile_division_v1",
        "response_gauge": "compensated_dc_peak_with_supplied_phase_origin",
        "bead_profile": {
            "source": "supplied_relative_site_weights",
            "supplied": supplied_profile,
            "applied": normalized_profile,
            "normalization": "exact_converted_sum",
        },
        "calibration_carrier_bins": carrier,
        "min_profile_transfer": minimum,
        "profile_transfer": np.array(np.fft.fftshift(profile), order="C", copy=True),
        "compensated_dc": localization,
    }
    return FiniteBeadCalibration(components, empirical, provenance)
