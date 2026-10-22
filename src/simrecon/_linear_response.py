"""Invert an explicitly supplied samplewise linear response in binary64."""

import copy
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._acquisition import RawAcquisition
from ._model import SimreconError

_SOURCE_FIELDS = (
    "axes",
    "source_axes",
    "source_shape",
    "acquisition_kind",
    "sampling_um",
    "wavelengths_nm",
    "nominal_phases_rad",
    "nominal_phase_axes",
    "intensity_unit",
    "acquisition_id",
    "calibration_id",
    "original_config",
    "original_metadata",
    "provenance",
)


@dataclass(frozen=True)
class LinearResponseCorrection:
    """Owned corrected samples and independent declaration/model snapshots.

    Bindings are frozen; buffers remain mutable and metadata is read-only by
    convention. Source metadata includes every public acquisition field except
    raw samples. Provenance distinguishes supplied and normalized coefficients.
    """

    data: npt.NDArray[np.float64]
    axes: tuple[str, ...]
    input_unit: str
    output_unit: str
    source_metadata: dict[str, Any]
    provenance: dict[str, Any]


def _normalized_array(array: npt.NDArray[Any], *, code: str) -> npt.NDArray[np.float64]:
    """Copy finite source values once to finite native binary64."""
    with np.errstate(all="ignore"):
        if not np.isfinite(array).all():
            raise SimreconError(code, "source values must be finite")
        try:
            result = array.astype(np.float64, order="C", copy=True)
        except (TypeError, ValueError, OverflowError) as error:
            raise SimreconError(code, "values cannot be converted to binary64") from error
        if not np.isfinite(result).all():
            raise SimreconError(code, "converted values must be finite")
    return result


def _coefficient(value: Any, *, name: str, shape: tuple[int, ...]) -> dict[str, Any]:
    """Retain the supplied value separately from its normalized coefficient."""
    code = f"invalid_linear_response_{name}"
    if type(value) in (int, float):
        try:
            applied = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise SimreconError(code, "coefficient cannot be converted to binary64") from error
        if not math.isfinite(applied) or (name == "response" and applied <= 0):
            raise SimreconError(code, "coefficient must be finite; response must be positive")
        supplied = value
    elif type(value) is np.ndarray and value.dtype.kind in "iuf":
        if value.shape != shape:
            raise SimreconError(
                "invalid_linear_response_shape", "coefficient map must match canonical sample shape"
            )
        applied = _normalized_array(value, code=code)
        if name == "response" and not (applied > 0).all():
            raise SimreconError(code, "response must be strictly positive after normalization")
        supplied = value.copy(order="C")
    else:
        raise SimreconError(code, "coefficient must be a plain int/float or real numeric ndarray")
    return {"source": "supplied", "supplied": supplied, "applied": applied}


def correct_linear_response(
    acquisition: RawAcquisition,
    *,
    offset: int | float | npt.NDArray[Any],
    response: int | float | npt.NDArray[Any],
    output_unit: str,
) -> LinearResponseCorrection:
    """Invert the caller-declared relation raw = offset + response * signal.

    Parameters
    ----------
    acquisition : RawAcquisition
        Valid public acquisition record with finite samples convertible to
        finite binary64 and a nonempty declared input intensity unit.
    offset : int, float or numpy.ndarray
        Explicit finite offset in input units. A plain scalar is shared across
        samples; a plain real numeric map must match the canonical sample shape.
    response : int, float or numpy.ndarray
        Explicit response in input units per output unit. Same forms/alignment
        as offset, strictly positive after binary64 conversion, even if subnormal.
    output_unit : str
        Nonempty opaque output intensity label, retained exactly.

    Returns
    -------
    LinearResponseCorrection
        Owned native C-contiguous float64 samples with the input shape/axes,
        source metadata without raw pixels, and supplied/applied model provenance.

    Raises
    ------
    SimreconError
        Stable invalid_linear_response_* code for invalid inputs, or
        linear_response_range for a nonfinite numerator or quotient.

    Notes
    -----
    Normalize inputs once, materialize raw minus offset, then divide by response.
    Subtraction overflow rejects even if an exact-real quotient would fit.
    Signed results, subnormals and signed underflow to zero are permitted.
    Caller storage and NumPy error modes are preserved; allocation failures and
    unrelated exceptions/warnings propagate. Units and nominal phase commands
    are not interpreted. No calibration, clipping or defective-pixel repair is
    inferred. The supplied relation must apply physically to the measurements.
    """
    if not isinstance(acquisition, RawAcquisition):
        raise SimreconError(
            "invalid_linear_response_acquisition", "acquisition must be a RawAcquisition"
        )
    input_unit = acquisition.intensity_unit
    if (
        type(input_unit) is not str
        or not input_unit
        or type(output_unit) is not str
        or not output_unit
    ):
        raise SimreconError(
            "invalid_linear_response_unit", "input and output units must be nonempty strings"
        )

    raw = _normalized_array(acquisition.data, code="invalid_linear_response_data")
    offset_entry = _coefficient(offset, name="offset", shape=raw.shape)
    response_entry = _coefficient(response, name="response", shape=raw.shape)
    with np.errstate(all="ignore"):
        numerator = np.subtract(raw, offset_entry["applied"])
        if not np.isfinite(numerator).all():
            raise SimreconError("linear_response_range", "subtraction numerator is nonfinite")
        data = np.divide(numerator, response_entry["applied"])
        if not np.isfinite(data).all():
            raise SimreconError("linear_response_range", "corrected samples are nonfinite")

    source_metadata = {name: copy.deepcopy(getattr(acquisition, name)) for name in _SOURCE_FIELDS}
    provenance = {
        "model": "linear_response_v1",
        "equation": "raw=offset+response*signal",
        "input_unit": input_unit,
        "output_unit": output_unit,
        "offset": offset_entry,
        "response": response_entry,
    }
    return LinearResponseCorrection(
        data=data,
        axes=acquisition.axes,
        input_unit=input_unit,
        output_unit=output_unit,
        source_metadata=source_metadata,
        provenance=provenance,
    )
