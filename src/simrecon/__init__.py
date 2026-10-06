"""Spatial image conversion through explicit, value-oriented interfaces."""

from ._legacy import inspect
from ._metadata import harmonize
from ._model import DataBlock, DatasetInfo, SimreconError, WriteReport
from ._modern import write
from ._otf import Otf2D, prepare_otf
from ._phase import PhaseComponents, separate_phases
from ._pixels import read

__all__ = [
    "DataBlock",
    "DatasetInfo",
    "Otf2D",
    "PhaseComponents",
    "SimreconError",
    "WriteReport",
    "harmonize",
    "inspect",
    "prepare_otf",
    "read",
    "separate_phases",
    "write",
]
