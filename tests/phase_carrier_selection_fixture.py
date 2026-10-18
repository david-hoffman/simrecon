"""Independent small finite models for the public carrier-selection contract.

All Fourier matrices below are explicit finite sums, independent of product FFTs.
Hidden truth is used only by generation/evaluation, never as selection arguments.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from simrecon import (
    VolumeOrderOtf,
    adapt_empirical_volume_response,
    calibrate_raw_point_bead,
    declare_acquisition,
)

RealArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass
class Observation:
    """Evaluator-owned truth and separately declared public inputs."""

    images: RealArray
    orders: VolumeOrderOtf
    commands: RealArray
    truth: RealArray
    specimen: RealArray
    carrier: tuple[int, int]
    label: str

    def arguments(self, **changes: Any) -> dict[str, Any]:
        """Return explicit nominal-command inputs, without hidden truth."""
        result = dict(
            order_otf=self.orders,
            candidate_carriers_yx=[self.carrier, (1, 0), (0, 4)],
            initial_phases_rad=self.commands,
            max_nfev=120,
            gradient_tolerance=1e-10,
            step_tolerance=1e-11,
            source=self.label,
        )
        result.update(changes)
        return result


def fourier_matrix(shape: tuple[int, ...]) -> ComplexArray:
    """Unitary negative-exponent DFT on uncentered modular integer indices."""
    coordinates = np.array(list(np.ndindex(shape)), dtype=np.float64)
    cycles = (coordinates / np.array(shape)) @ coordinates.T
    return np.asarray(np.exp(-2j * np.pi * cycles) / np.sqrt(len(coordinates)))


def signed_transfers(values: ComplexArray) -> dict[int, ComplexArray]:
    """Expand centered positive orders by explicit all-axis modular reflection."""
    shape = values.shape[1:]
    indices = list(np.ndindex(shape))
    positive = {
        m: np.array(
            [
                values[(m, *(int((k + n // 2) % n) for k, n in zip(j, shape, strict=True)))]
                for j in indices
            ]
        )
        for m in range(3)
    }
    reflected = [
        indices.index(tuple((-k) % n for k, n in zip(j, shape, strict=True))) for j in indices
    ]
    return {**positive, -1: positive[1][reflected].conj(), -2: positive[2][reflected].conj()}


def operator(
    values: ComplexArray,
    phases: RealArray,
    carrier: tuple[int, int],
    *,
    derivative: bool = False,
) -> ComplexArray:
    """Complex Fourier observation matrix, N*M by M, for a real specimen."""
    shape = values.shape[1:]
    indices = list(np.ndindex(shape))
    transform = fourier_matrix(shape)
    transfers = signed_transfers(values)
    blocks = []
    for phase in phases:
        z = complex(np.cos(phase), np.sin(phase))
        z2 = complex(np.cos(phase) ** 2 - np.sin(phase) ** 2, (2 * np.cos(phase)) * np.sin(phase))
        powers = {0: 1, 1: z, 2: z2, -1: z.conjugate(), -2: z2.conjugate()}
        block = np.zeros_like(transform)
        for m in (-2, -1, 0, 1, 2):
            shifted = [
                indices.index(
                    tuple(
                        (k - m * ell) % n for k, ell, n in zip(j, (0, *carrier), shape, strict=True)
                    )
                )
                for j in indices
            ]
            coefficient = (1j * m if derivative else 1) * powers[m]
            block += coefficient * transfers[m][:, None] * transform[shifted]
        blocks.append(block)
    return np.concatenate(blocks)


def observe(
    specimen: RealArray, values: ComplexArray, phases: RealArray, carrier: tuple[int, int]
) -> RealArray:
    """Independent real-space observations from the finite five-order sum."""
    shape = specimen.shape
    spectra = (operator(values, phases, carrier) @ specimen.ravel()).reshape(len(phases), -1)
    spatial = spectra @ fourier_matrix(shape).conj()
    assert np.max(np.abs(spatial.imag)) < 2e-13
    return spatial.real.reshape((len(phases), *shape)).copy()


def orders_from_kernels(
    kernels: ComplexArray, source: str = "independent kernels"
) -> VolumeOrderOtf:
    """Build an admissible direct transfer using ordinary finite Fourier sums."""
    shape = kernels.shape[1:]
    transform = fourier_matrix(shape) * np.sqrt(np.prod(shape))
    uncentered = (kernels.reshape(3, -1) @ transform.T).reshape(kernels.shape)
    values = np.roll(uncentered, tuple(n // 2 for n in shape), axis=(1, 2, 3))
    frequencies = [np.arange(-(n // 2), n - n // 2, dtype=np.float64) / n for n in shape]
    return VolumeOrderOtf(
        values=values,
        fz_per_um=frequencies[0],
        fy_per_um=frequencies[1],
        fx_per_um=frequencies[2],
        voxel_size_um=(1.0, 1.0, 1.0),
        origin_zyx=(0, 0, 0),
        source=source,
    )


def direct_observation() -> Observation:
    """Asymmetric signed specimen; nonproportional complex side kernels."""
    kernels = np.array(
        [
            [[[1.0, 0.09, 0.02], [0.04, 0.01, 0.03]]],
            [[[0.18 + 0.07j, 0.03 - 0.02j, -0.01j], [0.02j, 0.015, -0.01 + 0.02j]]],
            [[[0.08 - 0.04j, -0.02 + 0.01j, 0.015j], [0.01, -0.015j, 0.005]]],
        ],
        dtype=np.complex128,
    )
    orders = orders_from_kernels(kernels)
    commands = np.arange(7, dtype=np.float64) * (2 * np.pi / 7)
    truth = commands + np.array([0.04, -0.03, 0.02, -0.05, 0.01, 0.03, -0.02])
    specimen = np.array([[[1.0, -0.4, 0.7], [0.2, 0.9, -0.3]]])
    images = observe(specimen, orders.values, truth, (0, 1))
    return Observation(images, orders, commands, truth, specimen, (0, 1), "direct independent")


def raw_observation() -> Observation:
    """Spatial circular convolution, raw correction and public bead adaptation.

    The point bead sits at zero. Its DC kernel has a unique positive maximum and
    exact dyadic mass one. Calibration and specimen phase gauges agree explicitly.
    """
    shape = (1, 2, 3)
    kernels = np.array(
        [
            [[[0.75, 0.0625, 0.03125], [0.0625, 0.0625, 0.03125]]],
            [[[0.12 + 0.03j, 0.02j, 0.01], [-0.01j, 0.015, 0.005j]]],
            [[[0.05 - 0.02j, 0.01, 0.008j], [0.004j, -0.006, 0.003]]],
        ],
        dtype=np.complex128,
    )
    commands = np.arange(8, dtype=np.float64) * (2 * np.pi / 8)
    calibration_phases = np.arange(9, dtype=np.float64) * (2 * np.pi / 9) + 0.11
    calibration_signal = np.array(
        [
            kernels[0].real
            + 2 * (np.exp(1j * p) * kernels[1]).real
            + 2 * (np.exp(2j * p) * kernels[2]).real
            for p in calibration_phases
        ]
    )
    raw = 8.0 + 2.0 * calibration_signal[None]
    acquisition = declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "count",
            "nominal_phases_rad": [(np.arange(9) * (2 * np.pi / 9)).tolist()],
        },
    )
    calibration = calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=8.0,
        response=2.0,
        output_unit="electron",
        phases_rad=calibration_phases,
        voxel_size_um=(1, 1, 1),
    )
    orders = adapt_empirical_volume_response(
        calibration.response,
        carrier_bins=(0, 1),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source="declared common bead/specimen gauge",
    )
    specimen = np.array([[[0.8, -0.2, 0.5], [0.1, 0.6, -0.1]]])
    truth = commands + np.array([-0.025, 0.035, -0.015, 0.045, -0.03, 0.02, -0.04, 0.01])
    # Direct spatial circular convolution: illumination multiplies the specimen;
    # each signed order has its own complex kernel. No product forward operation.
    images = np.zeros((len(truth), *shape))
    for p, phase in enumerate(truth):
        for x in np.ndindex(shape):
            value = 0j
            for u in np.ndindex(shape):
                displacement = tuple((a - b) % n for a, b, n in zip(x, u, shape, strict=True))
                angle = phase + 2 * np.pi * u[2] / shape[2]
                value += specimen[u] * (
                    kernels[(0, *displacement)]
                    + 2 * (np.exp(1j * angle) * kernels[(1, *displacement)]).real
                    + 2 * (np.exp(2j * angle) * kernels[(2, *displacement)]).real
                )
            assert abs(value.imag) < 1e-15
            images[(p, *x)] = value.real
    return Observation(images, orders, commands, truth, specimen, (0, 1), "raw spatial independent")


def phase_blind_observation(*, unavailable: bool = False, deficient: bool = False) -> Observation:
    """Exact no-phase-information positive and genuine availability controls."""
    values = np.zeros((3, 1, 1, 2), dtype=np.complex128)
    if not unavailable:
        values[0] = 1
    if deficient:
        values[0, 0, 0, 0] = 1e-30
    orders = VolumeOrderOtf(
        values=values,
        fz_per_um=np.array([0.0]),
        fy_per_um=np.array([0.0]),
        fx_per_um=np.array([-0.5, 0.0]),
        voxel_size_um=(1.0, 1.0, 1.0),
        origin_zyx=(0, 0, 0),
        source="phase blind",
    )
    commands = np.arange(6, dtype=np.float64)
    images = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0])[:, None, None, None] * np.ones(
        (1, 1, 1, 2)
    )
    return Observation(
        images, orders, commands, commands.copy(), np.zeros((1, 1, 2)), (0, 0), "phase blind"
    )


def independent_fit(case: Observation, row: Any) -> dict[str, Any]:
    """Direct real-matrix nuisance solve and diagnostic expectations at returned angles.

    This checks arithmetic/objective, not global phase recovery or physical truth.
    The full-support generated groups have a full real nuisance domain.
    """
    b = float(np.max(np.abs(case.images))) or 1.0
    t = (
        float(max(np.max(np.abs(case.orders.values.real)), np.max(np.abs(case.orders.values.imag))))
        or 1.0
    )
    design_complex = operator(case.orders.values / t, row.phases_rad, row.carrier_bins_yx)
    design = np.concatenate((design_complex.real, design_complex.imag))
    data_complex = (case.images.reshape(len(case.commands), -1) / b) @ fourier_matrix(
        case.images.shape[1:]
    ).T
    data = np.concatenate((data_complex.real.ravel(), data_complex.imag.ravel()))
    nuisance, _, rank, singular = np.linalg.lstsq(design, data, rcond=None)
    residual = data - design @ nuisance
    prediction = design_complex @ nuisance
    observation_count, m = design.shape
    # Exposure p affects only its own block: the norm of this stacked vector
    # equals the Frobenius norm of the realified phase derivative matrix D.
    derivative_vector = (
        operator(case.orders.values / t, row.phases_rad, row.carrier_bins_yx, derivative=True)
        @ nuisance
    )
    coordinate_count = m + len(case.commands) + 1
    allowance = 2**20 * observation_count * coordinate_count * np.finfo(float).eps * (
        1 + np.linalg.norm(data) + np.linalg.norm(nuisance) + np.linalg.norm(derivative_vector)
    ) ** 2 + 256 * observation_count * coordinate_count * float.fromhex("0x0.0000000000001p-1022")
    return dict(
        specimen=nuisance.reshape(case.specimen.shape),
        singular=singular,
        rank=int(rank),
        relative=float(np.linalg.norm(residual) / np.linalg.norm(data)),
        rms=float(np.linalg.norm(residual) / np.sqrt(case.images.size)),
        imaginary=float(np.linalg.norm(prediction.imag) / np.sqrt(case.images.size)),
        allowance=float(allowance),
        condition=float(singular[0] / singular[-1]),
        image_scale=b,
        transfer_scale=t,
    )
