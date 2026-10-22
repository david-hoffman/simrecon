"""Independent small finite-sum observations and profiled scan expectations.

Only public calibration/declaration APIs are used. No product Fourier/model helpers
supply an expectation. Frequencies here use unshifted modular coordinates internally.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import scipy.optimize
from numpy.typing import NDArray

from simrecon import (
    VolumeOrderOtf,
    adapt_empirical_volume_response,
    calibrate_raw_point_bead,
    correct_linear_response,
    declare_acquisition,
)

Array = NDArray[Any]


def fourier_matrix(shape: tuple[int, int, int]) -> Array:
    """Return the negative-exponent unitary DFT by explicit finite sums."""
    coordinates = np.array(list(np.ndindex(shape)), dtype=np.float64)
    phase = (coordinates / np.array(shape)) @ coordinates.T
    return np.exp(-2j * np.pi * phase) / np.sqrt(np.prod(shape))


def record(values: Array, *, origin: tuple[int, int, int] = (0, 0, 0)) -> VolumeOrderOtf:
    """Declare stored centered transfers with exactly representable canonical bins."""
    shape = values.shape[1:]
    spacing = tuple(1.0 / size for size in shape)
    frequencies = [np.arange(-(size // 2), (size + 1) // 2, dtype=float) for size in shape]
    return VolumeOrderOtf(
        values=values,
        fz_per_um=frequencies[0],
        fy_per_um=frequencies[1],
        fx_per_um=frequencies[2],
        voxel_size_um=spacing,
        origin_zyx=origin,
        source="independent finite-sum calibration",
    )


def signed_transfers(values: Array) -> dict[int, Array]:
    """Build modular conjugate reflection on every axis, including even Nyquist."""
    positive = np.fft.ifftshift(values, axes=(1, 2, 3))
    negative_indices = [(-np.arange(size)) % size for size in values.shape[1:]]
    result = {m: positive[m] for m in range(3)}
    for m in (1, 2):
        result[-m] = np.conj(positive[m][np.ix_(*negative_indices)])
    return result


def model(values: Array, phases: Array, carrier: tuple[int, int]) -> tuple[Array, Array]:
    """Construct realified all-five-order A and its per-exposure derivatives."""
    shape = values.shape[1:]
    size = int(np.prod(shape))
    transform = fourier_matrix(shape)
    signed = signed_transfers(values)
    coordinates = np.array(list(np.ndindex(shape)), dtype=int)
    ell = np.array((0, carrier[0] % shape[1], carrier[1] % shape[2]), dtype=int)
    z = np.cos(phases) + 1j * np.sin(phases)
    z2 = (np.cos(phases) ** 2 - np.sin(phases) ** 2) + 1j * ((2 * np.cos(phases)) * np.sin(phases))
    powers = {-2: z2.conj(), -1: z.conj(), 0: np.ones_like(z), 1: z, 2: z2}
    operator = np.zeros((len(phases), size, size), dtype=complex)
    derivative = np.zeros_like(operator)
    for m in range(-2, 3):
        source = (coordinates - m * ell) % np.array(shape)
        indices = np.ravel_multi_index(source.T, shape)
        term = signed[m].reshape(-1, 1) * transform[indices]
        operator += powers[m][:, None, None] * term
        derivative += (1j * m * powers[m])[:, None, None] * term
    realified = np.concatenate(
        (np.real(operator).reshape(-1, size), np.imag(operator).reshape(-1, size))
    )
    return realified, derivative


def observations(values: Array, specimen: Array, phases: Array, carrier: tuple[int, int]) -> Array:
    """Synthesize real spatial observations from independently summed Fourier rows."""
    operator, _ = model(values, phases, carrier)
    size = specimen.size
    prediction = operator @ specimen.reshape(-1)
    spectrum = prediction[: len(phases) * size] + 1j * prediction[len(phases) * size :]
    spatial = spectrum.reshape(len(phases), size) @ fourier_matrix(specimen.shape).conj()
    assert np.max(np.abs(spatial.imag)) < 2e-13
    return spatial.real.reshape((len(phases), *specimen.shape))


def support(values: Array, carrier: tuple[int, int]) -> Array:
    """Compute exact stored-component visibility by explicit specimen-bin enumeration."""
    shape = values.shape[1:]
    signed = signed_transfers(values)
    visible = np.zeros(shape, dtype=bool)
    ell = (0, carrier[0] % shape[1], carrier[1] % shape[2])
    for j in np.ndindex(shape):
        for m in range(-2, 3):
            destination = tuple((j[a] + m * ell[a]) % shape[a] for a in range(3))
            value = signed[m][destination]
            visible[j] |= np.real(value) != 0 or np.imag(value) != 0
    mask = visible.copy()
    for j in np.ndindex(shape):
        opposite = tuple(-j[a] % shape[a] for a in range(3))
        mask[j] |= visible[opposite]
    return np.fft.fftshift(mask)


def oracle(images: Array, orders: VolumeOrderOtf, phases: Array, carrier: tuple[int, int]) -> dict:
    """Profile the full real nuisance model and independently derive diagnostics.

    The full-space truncated pseudoinverse gives the observable minimum-norm lift;
    structural zeros are omitted only when reporting reduced singular values.
    """
    b = float(np.max(np.abs(images))) or 1.0
    t = float(max(np.max(np.abs(orders.values.real)), np.max(np.abs(orders.values.imag)))) or 1.0
    values = orders.values.real / t + 1j * (orders.values.imag / t)
    a, derivative = model(values, phases, carrier)
    spectrum = (images / b).reshape(len(phases), -1) @ fourier_matrix(images.shape[1:]).T
    y = np.concatenate((spectrum.real.reshape(-1), spectrum.imag.reshape(-1)))
    left, singular, right = np.linalg.svd(a, full_matrices=False)
    cutoff = np.finfo(float).eps * len(y) * singular[0]
    keep = singular > cutoff
    inverse = (right[keep].T / singular[keep]) @ left[:, keep].T
    specimen = inverse @ y
    residual = y - a @ specimen
    prediction = a @ specimen
    d = np.zeros((len(y), len(phases)))
    ap: list[Array] = []
    size = specimen.size
    for p in range(len(phases)):
        block = np.zeros_like(a)
        block[p * size : (p + 1) * size] = derivative[p].real
        start = (len(phases) + p) * size
        block[start : start + size] = derivative[p].imag
        ap.append(block)
        d[:, p] = block @ specimen
    kphi = d - a @ (inverse @ d)
    jacobian = -kphi - np.column_stack([inverse.T @ block.T @ residual for block in ap])
    phase_singular = np.linalg.svd(kphi, compute_uv=False)
    phase_cutoff = np.finfo(float).eps * max(len(y), len(phases)) * phase_singular[0]
    mask = support(values, carrier)
    dimension = int(np.count_nonzero(mask))
    c, s = np.cos(phases), np.sin(phases)
    design = np.column_stack((np.ones_like(c), c, s, c * c - s * s, (2 * c) * s))
    design_singular = np.linalg.svd(design, compute_uv=False)
    design_rank = int(
        np.count_nonzero(
            design_singular > np.finfo(float).eps * max(design.shape) * design_singular[0]
        )
    )
    f0 = signed_transfers(values)[0]
    negative = np.ix_(*[(-np.arange(n)) % n for n in f0.shape])
    allowance = (
        2**20
        * len(y)
        * (size + len(phases) + 1)
        * np.finfo(float).eps
        * (1 + np.linalg.norm(y) + np.linalg.norm(specimen) + np.linalg.norm(d)) ** 2
    )
    return {
        "specimen": specimen.reshape(images.shape[1:]),
        "nuisance_singular": singular[:dimension],
        "nuisance_rank": int(np.count_nonzero(keep)),
        "phase_singular": phase_singular,
        "phase_rank": int(np.count_nonzero(phase_singular > phase_cutoff)),
        "phase_design_rank": design_rank,
        "relative_residual": float(np.linalg.norm(residual) / np.linalg.norm(y))
        if np.any(y)
        else 0.0,
        "normalized_residual_rms": float(np.linalg.norm(residual) / np.sqrt(images.size)),
        "normalized_imaginary_rms": float(
            np.linalg.norm(prediction[len(y) // 2 :]) / np.sqrt(images.size)
        ),
        "calibration_reality_defect": float(
            np.linalg.norm(f0 - f0[negative].conj()) / np.sqrt(size)
        ),
        "gradient_inf_norm": float(np.max(np.abs(jacobian.T @ residual))),
        "mask": mask,
        "allowance": float(allowance),
        "condition": (
            float(singular[0] / singular[dimension - 1])
            if dimension and singular[dimension - 1] > 0
            else None
        ),
        "minimum_singular": float(singular[dimension - 1]) if dimension else 0.0,
        "objective": float(0.5 * residual @ residual),
        "residual": residual,
        "jacobian": jacobian,
    }


def local_reference(group: dict, carrier: tuple[int, int], *, max_nfev: int = 200) -> dict:
    """Run the prescribed solver on the independent finite-sum residual/Jacobian."""
    initial = np.arctan2(np.sin(group["commands"]), np.cos(group["commands"]))
    initial[initial == np.pi] = -np.pi

    def evaluate(phases):
        return oracle(group["images"], group["orders"], phases, carrier)

    # The installed SciPy annotations omit supported callable-jac/None-ftol forms.
    # Keep the actual prescribed public invocation; this cast changes no execution.
    solver = cast(Any, scipy.optimize.least_squares)
    solved = solver(
        lambda phases: evaluate(phases)["residual"],
        initial,
        jac=lambda phases: evaluate(phases)["jacobian"],
        method="trf",
        bounds=(-np.inf, np.inf),
        loss="linear",
        x_scale=1,
        tr_solver="exact",
        ftol=None,
        gtol=1e-9,
        xtol=1e-10,
        max_nfev=max_nfev,
    )
    phases = np.arctan2(np.sin(solved.x), np.cos(solved.x))
    phases[phases == np.pi] = -np.pi
    return evaluate(phases)


def direct_group() -> dict:
    """Generate asymmetric odd/even 3D transfers and unknown unequal deviations."""
    shape = (2, 2, 3)
    coordinate = np.arange(np.prod(shape)).reshape(shape)
    values = np.empty((3, *shape), complex)
    # T0 is Hermitian; side rows deliberately are neither Hermitian nor constant.
    values[0] = 1.0
    values[1] = (0.13 + 0.008 * coordinate) * np.exp(1j * (0.3 + 0.17 * coordinate))
    values[2] = (0.06 + 0.003 * coordinate) * np.exp(-1j * (0.2 + 0.23 * coordinate))
    commands = np.array([-2.7, -1.8, -0.9, 0.0, 0.9, 1.8, 2.7])
    truth = commands + np.array([0.11, -0.07, 0.09, 0.06, -0.10, 0.08, -0.04])
    specimen = (-0.4 + 0.11 * coordinate + 0.3 * np.cos(0.9 * coordinate)).astype(float)
    orders = record(values, origin=(1, 1, 2))
    return {
        "images": observations(values, specimen, truth, (1, -1)),
        "orders": orders,
        "commands": commands,
        "truth": truth,
        "specimen": specimen,
        "carrier": (1, -1),
        "candidates": [(0, 0), (1, -1), (3, 2)],
    }


def raw_group() -> dict:
    """Compose raw declarations/correction/point-bead calibration/adapter.

    A finite spatial circular convolution generates both bead and specimen data.
    True bead position and kernels never enter the calibration call. Nominal
    commands and candidate policy are fixed independently of hidden deviations.
    """
    shape = (1, 3, 3)
    kernel = np.array([[[0.60, 0.04, 0.03], [0.02, 0.08, 0.05], [0.07, 0.06, 0.05]]])
    gains = np.array([1, 0.16 + 0.09j, -0.07 + 0.04j])
    commands = np.array([-2.8, -1.9, -1.0, -0.1, 0.8, 1.7, 2.6])
    truth = commands + np.array([-0.09, 0.08, -0.06, 0.10, 0.04, -0.07, 0.06])
    calibration_phases = np.array([-2.9, -2.0, -1.1, -0.2, 0.7, 1.6, 2.5])
    carrier = (1, -1)
    alpha_calibration, alpha_specimen = 0.21, -0.17
    bead_index = (0, 1, 2)
    coordinates = np.array(list(np.ndindex(shape)))

    def spatial_producer(specimen: Array, phases: Array) -> Array:
        result = np.zeros((len(phases), *shape))
        for p, phase in enumerate(phases):
            for x in np.ndindex(shape):
                for j in np.ndindex(shape):
                    displacement = tuple((x[a] - j[a]) % shape[a] for a in range(3))
                    theta = phase + 2 * np.pi * (carrier[0] * j[1] / 3 + carrier[1] * j[2] / 3)
                    illumination = 1 + 2 * np.real(
                        gains[1] * np.exp(1j * theta) + gains[2] * np.exp(2j * theta)
                    )
                    result[(p, *x)] += kernel[displacement] * specimen[j] * illumination
        return result

    bead = np.zeros(shape)
    bead[bead_index] = 4.0
    bead_images = spatial_producer(bead, calibration_phases)
    specimen = (
        0.4 + 0.09 * coordinates[:, 1] - 0.12 * coordinates[:, 2] + 0.2 * np.sin(np.arange(9))
    ).reshape(shape)
    specimen_images = spatial_producer(specimen, truth)

    def declaration(images: Array, kind: str):
        return declare_acquisition(
            (7.0 + 2.0 * images)[None],
            config={
                "version": 1,
                "acquisition_kind": kind,
                "axes": ["orientation", "phase", "z", "y", "x"],
                "intensity_unit": "count",
                "nominal_phases_rad": [commands.tolist()],
            },
        )

    calibrated = calibrate_raw_point_bead(
        declaration(bead_images, "sim_beads"),
        group={"orientation": 0},
        offset=7.0,
        response=2.0,
        output_unit="signal",
        phases_rad=calibration_phases + alpha_calibration,
        voxel_size_um=(1.0, 1 / 3, 1 / 3),
    )
    orders = adapt_empirical_volume_response(
        calibrated.response,
        carrier_bins=carrier,
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=alpha_specimen - alpha_calibration,
        source="raw bead/specimen fixed response pairing",
    )
    corrected = correct_linear_response(
        declaration(specimen_images, "specimen_sim"), offset=7.0, response=2.0, output_unit="signal"
    )
    expected = np.empty((3, *shape), complex)
    transform = fourier_matrix(shape) * np.sqrt(np.prod(shape))
    for m in range(3):
        expected[m] = np.fft.fftshift(
            (transform @ (kernel * gains[m]).reshape(-1)).reshape(shape)
        ) * np.exp(-1j * m * alpha_specimen)
    np.testing.assert_allclose(orders.values, expected, rtol=0, atol=2e-12)
    return {
        "images": corrected.data[0],
        "orders": orders,
        "commands": commands + alpha_specimen,
        "truth": truth + alpha_specimen,
        "specimen": specimen,
        "carrier": carrier,
        "candidates": [(0, 0), (1, -1), (4, 2)],
        "expected_transfers": expected,
    }
