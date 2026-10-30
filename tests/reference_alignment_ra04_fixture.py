"""Independent small RA04 controls. No product-derived truth or predecessor arrays."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np

from simrecon import declare_acquisition


@dataclass(frozen=True)
class PairExample:
    """Keep caller inputs, declared arguments and independent reference signals."""

    specimen: Any
    bead: Any
    arguments: dict[str, Any]
    specimen_signal: np.ndarray
    bead_signal: np.ndarray


def acquisition(
    data: np.ndarray,
    kind: str = "specimen_sim",
    *,
    unit: str | None = "detector count",
    calibration_id: str | None = "paired calibration",
    axes: tuple[str, ...] = ("orientation", "phase", "y", "x"),
    sampling_um: tuple[float, float] = (0.5, 0.25),
) -> Any:
    """Declare real raw input, including opaque and commanded metadata."""
    config: dict[str, Any] = {
        "version": 1,
        "axes": list(axes),
        "acquisition_kind": kind,
        "intensity_unit": unit,
        "calibration_id": calibration_id,
        "acquisition_id": "opaque acquisition",
        "sampling_um": {"y": sampling_um[0], "x": sampling_um[1]},
        "wavelengths_nm": {"0": 510.0},
    }
    if kind != "detection_psf":
        group_shape = tuple(
            data.shape[i] for i, name in enumerate(axes) if name not in ("z", "y", "x")
        )
        config["nominal_phases_rad"] = np.zeros(group_shape).tolist()
    return declare_acquisition(
        data,
        config=config,
        original_metadata={"opaque": [b"raw header", {"flags": (False, -3)}]},
    )


def declared_example(*, maps: bool = False) -> PairExample:
    """Distinct shapes and dyadic coefficients make every arithmetic step exact."""
    s = (np.arange(36, dtype=np.float64).reshape(2, 3, 2, 3) - 18) / 4
    b = (np.arange(8, dtype=np.float64).reshape(1, 4, 1, 2) - 3) / 2
    so: Any = -3
    sr: Any = 2.0
    bo: Any = 7.0
    br: Any = 0.5
    se: Any = 2
    be: Any = 0.5
    if maps:
        so = np.arange(s.size, dtype=np.int16).reshape(s.shape) - 11
        sr = np.where(np.indices(s.shape).sum(axis=0) % 2, 2.0, 0.5)
        bo = np.arange(b.size, dtype=np.float64).reshape(b.shape) - 5
        br = np.where(np.indices(b.shape).sum(axis=0) % 2, 4.0, 1.0)
        se = np.where(np.indices(s.shape)[1] % 2, 0.5, 2.0)
        be = np.where(np.indices(b.shape)[1] % 2, 4.0, 0.25)
    return PairExample(
        acquisition(so + sr * se * s),
        acquisition(bo + br * be * b, "sim_beads"),
        {
            "mode": "declared",
            "output_unit": " shared signal ",
            "gauge_source": " independent declared gauge ",
            "reference_sum_equalization": "disabled",
            "specimen_offset": so,
            "specimen_response": sr,
            "bead_offset": bo,
            "bead_response": br,
            "specimen_exposure_factor": se,
            "bead_exposure_factor": be,
        },
        s,
        b,
    )


def estimated_example(
    *, flat_mean: int = 20, flat_spread: float = 2.0, dark_mean: int = 4
) -> tuple[PairExample, tuple[np.ndarray, ...], dict[str, Any]]:
    """Finite calibration moments: means 4,12,F; variances 5/3,20/3,20*f²/3.

    Each group's frame means differ by -2,0,2. Standard error is sqrt(4/3).
    These are algebraic finite controls, not a sampled physical-camera claim.
    """
    pattern = np.array([-3.0, -1.0, 1.0, 3.0])[None, None, :]
    shifts = np.array([-2.0, 0.0, 2.0])[:, None, None]
    groups = tuple(
        center + shifts + spread * pattern
        for center, spread in ((dark_mean, 0.5), (12, 1.0), (flat_mean, flat_spread))
    )
    s = np.array([-1.0, 0.0, 0.5, 2.0]).reshape(1, 1, 1, 4)
    b = np.array([0.25, 1.0]).reshape(1, 1, 1, 2)
    pair = PairExample(
        acquisition(12 + 8 * s),
        acquisition(12 + 8 * b, "sim_beads"),
        {
            "mode": "estimated",
            "output_unit": "reference_flat_relative",
            "gauge_source": " finite ensemble gauge ",
            "reference_sum_equalization": "disabled",
            "specimen_exposure_factor": 1,
            "bead_exposure_factor": np.ones(b.shape),
        },
        s,
        b,
    )
    variances = (
        Fraction(5, 3),
        Fraction(20, 3),
        Fraction(20, 3) * Fraction(flat_spread) ** 2,
    )
    truth = {
        "means": np.array([float(dark_mean), 12.0, float(flat_mean)]),
        "variances": np.array([float(v) for v in variances]),
        "frame_means": tuple(np.array([c - 2.0, c, c + 2.0]) for c in (dark_mean, 12, flat_mean)),
        "frame_variances": tuple(np.full(3, float(v)) for v in variances),
        "se": np.full(3, np.sqrt(4.0 / 3.0)),
        "contrast": float(flat_mean - 12),
        "variance_contrast": float(variances[2] - variances[1]),
    }
    return pair, groups, truth


def carrier_point(*, scale: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A=2 point at (1,2) on fixed 3 by 5 pixels; no sum equalization law."""
    phases = np.array([[0.0, np.pi / 2, np.pi, 3 * np.pi / 2]])
    signal = np.zeros((3, 5))
    signal[1, 2] = 2 * scale
    x = np.arange(5)[None, :]
    illumination = 1 + 0.5 * np.cos(2 * np.pi * x / 5 + phases[..., None, None])
    images = signal * illumination
    totals = 2 * scale * (1 + 0.5 * np.cos(4 * np.pi / 5 + phases))
    return images, phases, totals


def reconstruction_control(
    *, point: bool, scale: float = 1.0
) -> tuple[PairExample, dict[str, Any], np.ndarray, np.ndarray]:
    """Fix lambda=1/8, identity transfer, V=9/8, shrinkage=9/10.

    Point control keeps only qx=-1,0,1, qy=0; its coefficient/integral has
    independent truth despite discarded high modes. It is not peak recovery.
    """
    from simrecon import prepare_otf

    if point:
        images, phases, _ = carrier_point(scale=scale)
        ny, nx = 3, 5
        waves = np.array([[0.0, 1.0 / 5]])
        mask = np.zeros((2 * ny, 2 * nx))
        mask[ny, nx - 1 : nx + 2] = 1
        spectrum = np.zeros(mask.shape, dtype=np.complex128)
        for q in (-1, 0, 1):
            spectrum[ny, nx + q] = (2 * scale / 15) * 0.9 * np.exp(-2j * np.pi * q * 2 / 5)
        x = np.arange(2 * nx)[None, :]
        image = np.zeros(mask.shape, dtype=np.complex128)
        for q in (-1, 0, 1):
            image += spectrum[ny, nx + q] * np.exp(2j * np.pi * q * x / (2 * nx))
    else:
        ny, nx = 1, 1
        phases = np.array([[0.0, np.pi / 2, np.pi, 3 * np.pi / 2]])
        images = -2 * scale * (1 + 0.5 * np.cos(phases[..., None, None]))
        waves = np.zeros((1, 2))
        mask = np.ones((2, 2))
        spectrum = np.zeros((2, 2), dtype=np.complex128)
        spectrum[1, 1] = -2 * scale * 0.9
        image = np.full((2, 2), -2 * scale * 0.9, dtype=np.complex128)
    kernel = np.zeros((ny, nx))
    kernel[0, 0] = 1
    args = {
        "otf": prepare_otf(
            kernel, pixel_size_um=(1.0, 1.0), origin_yx=(0, 0), source="fixed delta"
        ),
        "phases_rad": phases,
        "wavevectors_per_um": waves,
        "modulation": np.array([0.5]),
        "brightness": np.array([1.0]),
        "regularization": 0.125,
        "apodization": mask,
    }
    pair = PairExample(
        acquisition(7 + 4 * images, sampling_um=(1.0, 1.0)),
        acquisition(np.array([[[[9.0, 11.0]]]]), "sim_beads"),
        {
            "mode": "declared",
            "output_unit": "fixed signal",
            "gauge_source": "fixed gauge",
            "specimen_offset": 7,
            "specimen_response": 2,
            "bead_offset": 1,
            "bead_response": 2,
            "specimen_exposure_factor": 2,
            "bead_exposure_factor": 1,
            "reference_sum_equalization": "disabled",
        },
        images,
        np.array([[[[4.0, 5.0]]]]),
    )
    return pair, args, spectrum, image
