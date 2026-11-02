"""Spatial image conversion through explicit, value-oriented interfaces."""

from ._acquisition import RawAcquisition, declare_acquisition
from ._imagej import ImagejSeries, ImagejWriteReport, export_imagej
from ._legacy import inspect
from ._metadata import harmonize
from ._model import DataBlock, DatasetInfo, SimreconError, WriteReport
from ._modern import write
from ._pixels import read

__all__ = [
    "DataBlock",
    "DatasetInfo",
    "ImagejSeries",
    "ImagejWriteReport",
    "RawAcquisition",
    "SimreconError",
    "WriteReport",
    "declare_acquisition",
    "export_imagej",
    "harmonize",
    "inspect",
    "read",
    "write",
]
