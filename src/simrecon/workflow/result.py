"""Workflow value records and contextual failure translation."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, NoReturn

from ..acquisition.layout import REFERENCE, TwoDPlaneInputs
from ..acquisition.modes import AcquisitionBands
from ..models import SimreconError
from ..optical_transfer import OpticalTransfer, PreparedOtf
from ..reconstruction.known_parameters import KnownReconstruction
from ..reconstruction.parameter_estimation import EstimatedParameters


class WorkflowError(SimreconError):
    """Rejected workflow declaration or failed scientific operation."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        stage: str,
        time_index: int | None = None,
        direction_index: int | None = None,
    ):
        super().__init__(code, message)
        self.stage = stage
        self.time_index = time_index
        self.direction_index = direction_index


@dataclass(frozen=True)
class _ArrayIdentity:
    name: str
    shape: tuple[int, ...]
    dtype: str
    sha256: str


@dataclass(frozen=True)
class _WorkflowEvent:
    kind: str
    stage: str
    time_index: int | None
    details: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class WorkflowReconstruction:
    """Actual composed stages and independent signed image/coordinate storage."""

    image: Any
    x_um: Any
    y_um: Any
    z_um: Any
    intensity_unit: str
    intensity_semantics: str
    bands: AcquisitionBands
    parameters: EstimatedParameters
    transfer: OpticalTransfer
    calibration: PreparedOtf | None
    layout: TwoDPlaneInputs | None
    reconstructions: tuple[KnownReconstruction, ...]
    initial_carriers_cyc_um: Any
    phase_linkage_carriers_cyc_um: Any
    effective_wiener: Any
    input_identities: tuple[_ArrayIdentity, ...]
    source_declarations: tuple[tuple[str, Any], ...]
    resolved_settings: tuple[tuple[str, Any], ...]
    trace: tuple[_WorkflowEvent, ...]
    limitations: tuple[str, ...]
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = REFERENCE


def _fail(code: str, message: str, stage: str = "declaration") -> NoReturn:
    raise WorkflowError("workflow_" + code, message, stage=stage)


def _context(error: BaseException) -> tuple[int | None, int | None]:
    """Read actual active stage indices, without replaying a failed operation."""
    time = direction = None
    tb = error.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        module = frame.f_globals.get("__name__", "")
        if module in ("simrecon.acquisition.modes", "simrecon.reconstruction.parameter_estimation"):
            local = frame.f_locals
            instance = local.get("self")
            for name in ("t", "d"):
                value = local.get(name, getattr(instance, name, None))
                if type(value) is int and value >= 0:
                    if name == "t":
                        time = value
                    else:
                        direction = value
        tb = tb.tb_next
    return time, direction


@contextmanager
def _stage(stage: str, *, time_index: int | None = None) -> Iterator[None]:
    """Wrap stage failures with their cause, preserving allocation/interruption."""
    try:
        yield
    except WorkflowError:
        raise
    except MemoryError:
        raise
    except Exception as error:
        cause: BaseException | None = error
        while cause is not None:
            if isinstance(cause, MemoryError):
                raise MemoryError(f"{stage}: allocation failed") from error
            cause = cause.__cause__
        time, direction = _context(error)
        text = str(error)
        representation = any(
            part in text
            for part in (
                "representation",
                "out of allocation",
                "outside allocation",
                "out-of-allocation",
                "leaves the order allocation",
            )
        )
        raise WorkflowError(
            "workflow_representation" if representation else "workflow_operation",
            text or type(error).__name__,
            stage=stage,
            time_index=time if time_index is None else time_index,
            direction_index=direction,
        ) from error
