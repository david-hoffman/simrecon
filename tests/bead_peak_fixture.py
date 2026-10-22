"""Independent selected-model acquisition and Decimal stored-input observer.

No product imports. Coordinates are generator/observer truth only. Decimal normal
-equation elimination is an observer, never the required production SVD solver.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]


@dataclass(frozen=True)
class SyntheticBead:
    """Explicit camera/model arrays and independent observer truth."""

    raw: Array
    offset: float | Array
    response: float | Array
    phases: Array
    commands: Array
    config: dict[str, Any]
    corrected: Array
    ideal_dc: Array
    truth: tuple[int, int, int]


def phase_matrix(phases: Array) -> Array:
    """Normative represented H, independent of the product solver."""
    c, s = np.cos(phases), np.sin(phases)
    return np.column_stack((np.ones(phases.size), c, s, c * c - s * s, (2 * c) * s))


def stored_dc_oracle(images: Array, phases: Array, precision: int = 90) -> Array:
    """Fit stored binary64 observations in Decimal; return rounded DC only.

    Decimal.from_float is exact for each represented matrix/sample entry.
    Partial-pivot elimination of H.T H is adequate at cond(H) < 10; tests
    independently repeat at 120 digits to check the rounded observer result.
    """
    with localcontext() as context:
        context.prec = precision
        h = [[Decimal.from_float(float(v)) for v in row] for row in phase_matrix(phases)]
        normal = [
            [sum((row[i] * row[j] for row in h), Decimal(0)) for j in range(5)] for i in range(5)
        ]
        # Solve (H.T H) w = e0, then DC = w.T H.T b.
        augmented = [row[:] + [Decimal(int(i == 0))] for i, row in enumerate(normal)]
        for col in range(5):
            pivot = max(range(col, 5), key=lambda r: abs(augmented[r][col]))
            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
            divisor = augmented[col][col]
            assert divisor != 0
            augmented[col] = [v / divisor for v in augmented[col]]
            for r in range(5):
                if r != col:
                    factor = augmented[r][col]
                    augmented[r] = [
                        v - factor * u for v, u in zip(augmented[r], augmented[col], strict=True)
                    ]
        weights = [sum(augmented[i][-1] * row[i] for i in range(5)) for row in h]
        dc = np.empty(images.shape[1:], dtype=np.float64)
        for coordinate in np.ndindex(dc.shape):
            dc[coordinate] = float(
                sum(
                    w * Decimal.from_float(float(images[(p, *coordinate)]))
                    for p, w in enumerate(weights)
                )
            )
        return dc


def synthetic_bead(
    *, asymmetric: bool, mapped_camera: bool, truth: tuple[int, int, int]
) -> SyntheticBead:
    """Noiseless periodic point bead, equal scalar fields a0=a+=a-=1.

    Grid (3,4,5); spacing (0.5,0.25,0.2) micrometres. Modes (1,0,1)
    give kappa=2/3 and |q|=1 cycles/micrometre, so 0<kappa<|q|.
    Brightness is 240 electrons. Kernel peak is uniquely at displacement 0.
    """
    shape = (3, 4, 5)
    u = np.indices(shape, dtype=np.float64)
    if asymmetric:
        # Positive, nonsymmetric family; normalization cannot change its peak.
        kernel = np.ones(shape, dtype=np.float64)
        kernel[0, 0, 0] = 40
        kernel[1, 2, 3] = 9
        kernel[2, 1, 4] = 5
    else:
        kernel = np.exp(
            sum(
                alpha * np.cos(2 * np.pi * u[axis] / shape[axis])
                for axis, alpha in enumerate((1.5, 2.0, 1.0))
            )
        )
    kernel = kernel / np.sum(kernel)
    shifted = np.roll(kernel, truth, axis=(0, 1, 2))
    ideal_dc = 240.0 * shifted
    phases = np.array([0.13, 0.91, 1.82, 2.77, 3.62, 4.58, 5.71])
    commands = phases + np.array([0.0, 0.12, -0.08, 0.21, -0.15, 0.09, -0.19])
    delta_z = (u[0] - truth[0]) / shape[0]
    axial = np.exp(2j * np.pi * delta_z)
    exposures = np.empty((phases.size, *shape), dtype=np.float64)
    for p, phase in enumerate(phases):
        theta = 2 * np.pi * truth[2] / shape[2] + phase
        field = axial + np.exp(1j * theta) + np.exp(-1j * theta)
        exposures[p] = ideal_dc * (field.real * field.real + field.imag * field.imag) / 3.0
    canonical = exposures[None, ...]  # one explicit orientation, then phase/z/y/x
    if mapped_camera:
        coordinate = np.indices(canonical.shape)
        offset: float | Array = -3.0 + coordinate[1] + 0.25 * coordinate[2] + 0.5 * coordinate[3]
        response: float | Array = 1.0 + 0.25 * coordinate[1] + 0.125 * coordinate[4]
    else:
        offset, response = 10.0, 2.0
    raw = offset + response * canonical
    corrected = np.divide(np.subtract(raw, offset), response)[0]
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "sim_beads",
        "axes": ["orientation", "phase", "z", "y", "x"],
        "sampling_um": {"z": 0.5, "y": 0.25, "x": 0.2},
        "nominal_phases_rad": [commands.tolist()],
        "intensity_unit": "counts",
    }
    return SyntheticBead(
        raw, offset, response, phases, commands, config, corrected, ideal_dc, truth
    )


def separator_dc_budget(images: Array) -> Array:
    """Inherited per-voxel budget plus a conservative rounded-observer allowance."""
    scale = np.max(np.abs(images), axis=0)
    return (8192 * images.shape[0] + 1) * 2.0**-52 * scale + 8 * float.fromhex(
        "0x0.0000000000001p-1022"
    )


def composition_evidence(fixture: SyntheticBead) -> dict[str, float]:
    """Independent error allowance and physical-model peak margin, in electrons."""
    oracle = stored_dc_oracle(fixture.corrected, fixture.phases)
    assert np.array_equal(oracle, stored_dc_oracle(fixture.corrected, fixture.phases, 120))
    condition = float(np.linalg.cond(phase_matrix(fixture.phases)))
    assert condition <= 10
    # Rounded Decimal oracle adds <=0.5 ulp; one extra epsilon*B conservatively
    # covers that observer rounding alongside the inherited 8192*N*epsilon*B.
    scale = float(np.max(np.abs(fixture.corrected)))
    assert np.all(np.abs(oracle) <= np.max(np.abs(fixture.corrected), axis=0))
    budget = float(np.max(separator_dc_budget(fixture.corrected)))
    model_error = float(np.max(np.abs(oracle - fixture.ideal_dc)))
    peak = float(fixture.ideal_dc[fixture.truth])
    other = [
        float(fixture.ideal_dc[c]) for c in np.ndindex(fixture.ideal_dc.shape) if c != fixture.truth
    ]
    margin = peak - max(other)
    allowance = model_error + budget
    assert margin > 2 * allowance
    wrong = stored_dc_oracle(fixture.corrected, fixture.commands)
    command_error = float(np.max(np.abs(wrong - oracle)))
    assert command_error > 100 * allowance
    return {
        "condition_H": condition,
        "scale_electrons": scale,
        "separator_budget_electrons": budget,
        "stored_model_error_electrons": model_error,
        "peak_margin_electrons": margin,
        "nominal_phase_dc_error_electrons": command_error,
    }
