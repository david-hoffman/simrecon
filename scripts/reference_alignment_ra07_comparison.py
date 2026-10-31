"""Retain a predeclared direct-sum RA07 comparison, then observe and render it."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

import numpy as np


def _bins(shape: tuple[int, ...]) -> np.ndarray:
    return np.asarray(list(itertools.product(*(range(-(n // 2), (n + 1) // 2) for n in shape))))


def _positions(shape: tuple[int, ...]) -> np.ndarray:
    return np.asarray(list(itertools.product(*(range(n) for n in shape))))


def _matrix(shape: tuple[int, ...]) -> np.ndarray:
    return np.exp(2j * np.pi * (_positions(shape) / np.asarray(shape)) @ _bins(shape).T)


def _interpolate(values: np.ndarray, point: tuple[Fraction, ...]) -> complex | None:
    axes = []
    for n, value in zip(values.shape, point, strict=True):
        low, high = -(n // 2), (n - 1) // 2
        if value < low or value > high:
            return None
        left = value.numerator // value.denominator
        if value == left:
            axes.append([(left + n // 2, 1.0)])
        else:
            weight = float(value - left)
            axes.append([(left + n // 2, 1.0 - weight), (left + 1 + n // 2, weight)])
    total = 0j
    for stencil in itertools.product(*axes):
        index = tuple(item[0] for item in stencil)
        total += values[index] * np.prod([item[1] for item in stencil])
    return complex(total)


def _reference(inputs: dict[str, np.ndarray]) -> dict[str, np.ndarray | float]:
    images, transfer = inputs["images"], inputs["transfer"]
    shape = images.shape[-3:]
    output_shape = tuple(int(x) for x in inputs["output_shape"])
    native_bins, output_bins = _bins(shape), _bins(output_shape)
    native_synthesis, output_synthesis = _matrix(shape), _matrix(output_shape)
    positions = _positions(output_shape)
    m, p = int(np.prod(shape)), int(np.prod(output_shape))
    phases = inputs["phases"]
    cos, sin = np.cos(phases), np.sin(phases)
    design = np.stack(
        [np.ones_like(cos), 2 * cos, -2 * sin, 2 * (cos * cos - sin * sin), -2 * ((2 * cos) * sin)],
        axis=1,
    )
    # Independent tiny stored-input observer; well-conditioned normal system.
    coordinates = np.linalg.solve(design.T @ design, design.T @ images[0].reshape(len(phases), -1))
    bands = [
        coordinates[0],
        coordinates[1] + 1j * coordinates[2],
        coordinates[3] + 1j * coordinates[4],
    ]
    signed_bands = {0: bands[0], 1: bands[1], 2: bands[2], -1: bands[1].conj(), -2: bands[2].conj()}
    signed_transfers = {order: transfer[abs(order)].copy() for order in range(3)}
    for order in (1, 2):
        negative = np.empty(shape, dtype=np.complex128)
        for index, mode in zip(np.ndindex(shape), native_bins, strict=True):
            reflected = tuple(int((-int(k) + n // 2) % n) for k, n in zip(mode, shape, strict=True))
            negative[index] = transfer[order][reflected].conjugate()
        signed_transfers[-order] = negative
    carrier = [
        Fraction(int(n)) * Fraction(float(d)) * Fraction(float(k))
        for n, d, k in zip(shape[1:], inputs["spacing"][1:], inputs["carriers"][0], strict=True)
    ]
    lam, gain = float(inputs["regularization"]), float(inputs["gains"][0])
    expected = np.zeros(p, dtype=np.complex128)
    denominator_samples = []
    shifted_data, shifted_transfer = [], []
    component_spectra = []
    for order in range(-2, 3):
        data = native_synthesis.conj().T @ signed_bands[order] / m
        otf = signed_transfers[order].ravel()
        denominator = np.empty(m)
        for index, mode in enumerate(native_bins):
            object_point = (
                Fraction(int(mode[0])),
                Fraction(int(mode[1])) - order * carrier[0],
                Fraction(int(mode[2])) - order * carrier[1],
            )
            power = lam
            for other in range(-2, 3):
                query = (
                    object_point[0],
                    object_point[1] + other * carrier[0],
                    object_point[2] + other * carrier[1],
                )
                sampled = _interpolate(signed_transfers[other], query)
                if sampled is not None:
                    power += abs(gain * sampled) ** 2
            denominator[index] = power
        denominator_samples.extend(denominator.tolist())
        ramp_cycles = np.asarray(
            [
                float(
                    (
                        order
                        * (
                            carrier[0] * int(n[1]) / output_shape[1]
                            + carrier[1] * int(n[2]) / output_shape[2]
                        )
                    )
                    % 1
                )
                for n in positions
            ]
        )
        ramp = np.exp(-2j * np.pi * ramp_cycles)
        native_to_output = np.exp(
            2j * np.pi * (positions / np.asarray(output_shape)) @ native_bins.T
        )
        relocation = (output_synthesis.conj().T @ (ramp[:, None] * native_to_output)) / p
        filtered = gain * otf.conj() * data / denominator
        component = relocation @ filtered
        component_spectra.append(component)
        expected += component
        shifted_data.append(relocation @ data)
        shifted_transfer.append(relocation @ (gain * otf))
    # A different, explicitly labelled finite estimator: interpolate observations
    # and transfer arrays first, then form a scalar quotient on output bins.
    numerator = sum(t.conj() * d for t, d in zip(shifted_transfer, shifted_data, strict=True))
    power = sum(np.abs(t) ** 2 for t in shifted_transfer) + lam
    after_shift = numerator / power
    taper = inputs["taper"].ravel()
    result = expected * taper
    volume = output_synthesis @ result
    # Conservative bound fixed from input scales, conditioning and sum lengths.
    # Accounts for inherited phase allowance, products, denominator, two sums.
    eps = np.finfo(np.float64).eps
    scale = max(1.0, float(np.max(np.abs(images))))
    condition = float(np.linalg.cond(design))
    denominator_minimum = float(min(denominator_samples))
    spectrum_bound = (
        2**20 * eps * scale * condition * (len(phases) + m + p) / min(1.0, denominator_minimum) ** 2
    )
    return {
        "expected_spectrum": result.reshape(output_shape),
        "expected_volume": volume.reshape(output_shape),
        "after_shift_spectrum": (after_shift * taper).reshape(output_shape),
        "components": np.asarray(component_spectra).reshape((5, *output_shape)),
        "output_bins": output_bins,
        "carrier_bins": np.asarray([float(x) for x in carrier]),
        "spectrum_bound": spectrum_bound,
        "volume_bound": p * spectrum_bound,
        "phase_condition": condition,
        "minimum_denominator": denominator_minimum,
    }


def prepare(destination: Path) -> None:
    """Set inputs and independent expectations before any product observation."""
    destination.mkdir(parents=True, exist_ok=False)
    shape, output_shape = (1, 5, 6), (1, 11, 12)
    points = _positions(shape)
    y, x = points[:, 1] / shape[1], points[:, 2] / shape[2]
    dc = 2 + 0.2 * np.cos(2 * np.pi * (y - x))
    c1 = 0.4 * np.exp(2j * np.pi * (0.4 * y - 0.7 * x)) + 0.1j * np.exp(2j * np.pi * x)
    c2 = 0.17 * np.exp(2j * np.pi * (-0.3 * y + 0.6 * x))
    phases = np.asarray([0.0, 0.7, 1.6, 2.5, 3.4, 4.7, 5.9])
    cos, sin = np.cos(phases), np.sin(phases)
    images = (
        dc
        + 2 * cos[:, None] * c1.real
        - 2 * sin[:, None] * c1.imag
        + 2 * (cos * cos - sin * sin)[:, None] * c2.real
        - 2 * ((2 * cos) * sin)[:, None] * c2.imag
    ).reshape(1, len(phases), *shape)
    native = _bins(shape)
    transfer = np.asarray(
        [
            (
                0.45
                + 0.05 * order
                + 0.02 * native[:, 1]
                + 0.015 * native[:, 2]
                + 1j * (0.025 * native[:, 1] - 0.035 * native[:, 2] + 0.02 * order)
            ).reshape(shape)
            for order in range(3)
        ]
    )
    inputs = {
        "images": images,
        "transfer": transfer,
        "phases": phases,
        "spacing": np.asarray([0.5, 0.25, 0.25]),
        "carriers": np.asarray([[0.5, -0.5]]),
        "gains": np.asarray([1.2]),
        "regularization": np.asarray(0.05),
        "output_shape": np.asarray(output_shape),
        "taper": np.ones(output_shape),
    }
    reference = _reference(inputs)
    np.savez(destination / "inputs.npz", allow_pickle=False, **inputs)
    np.savez(destination / "expectations.npz", allow_pickle=False, **reference)
    manifest = {
        "phase": "inputs and expectations fixed before product observation",
        "model": "RA07 filter-before-shift; different after-shift estimator shown descriptively",
        "input_sha256": hashlib.sha256((destination / "inputs.npz").read_bytes()).hexdigest(),
        "expectation_sha256": hashlib.sha256(
            (destination / "expectations.npz").read_bytes()
        ).hexdigest(),
        "units": {
            "spacing": "micrometres",
            "carrier": "cycles per micrometre",
            "spectrum_volume": "input intensity",
            "transfer": "dimensionless",
        },
        "shape": shape,
        "output_shape": output_shape,
        "bound_derivation": (
            "2**20*eps*max(1,abs(images))*cond(K)*(N+M+P)/min(1,min_denominator)**2; "
            "volume=P*spectrum"
        ),
        "spectrum_bound": float(reference["spectrum_bound"]),
        "volume_bound": float(reference["volume_bound"]),
        "condition": float(reference["phase_condition"]),
        "minimum_denominator": float(reference["minimum_denominator"]),
        "limits": (
            "Finite stored-input comparison; no noise/physical-resolution/infinite-field claim. "
            "Normal equations are independent small observer only; product requires SVD phase fit."
        ),
    }
    (destination / "design.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


def observe(source: Path, destination: Path) -> None:
    """Observe the public product once against unchanged prior expectations."""
    from simrecon import VolumeOrderOtf, reconstruct_volume_fractional

    destination.mkdir(parents=True, exist_ok=False)
    with np.load(source / "inputs.npz") as archive:
        inputs = {key: archive[key] for key in archive.files}
    with np.load(source / "expectations.npz") as archive:
        expected = {key: archive[key] for key in archive.files}
    shape = inputs["images"].shape[-3:]
    axes = [
        np.asarray(
            [float(Fraction(k, n) / Fraction(float(d))) for k in range(-(n // 2), (n + 1) // 2)]
        )
        for n, d in zip(shape, inputs["spacing"], strict=True)
    ]
    otf = VolumeOrderOtf(
        values=inputs["transfer"],
        fz_per_um=axes[0],
        fy_per_um=axes[1],
        fx_per_um=axes[2],
        voxel_size_um=(
            float(inputs["spacing"][0]),
            float(inputs["spacing"][1]),
            float(inputs["spacing"][2]),
        ),
        origin_zyx=(0, 0, 0),
        source="predeclared analytic complex fixture",
    )
    result = reconstruct_volume_fractional(
        inputs["images"],
        order_otfs=[otf],
        phases_rad=inputs["phases"][None, :],
        carriers_per_um=inputs["carriers"],
        gains=inputs["gains"],
        regularization=float(inputs["regularization"]),
        output_shape_yx=tuple(int(n) for n in inputs["output_shape"][1:]),
        apodization=inputs["taper"],
    )
    np.savez(
        destination / "observed.npz",
        spectrum=result.spectrum,
        volume=result.volume,
        fz_per_um=result.fz_per_um,
        fy_per_um=result.fy_per_um,
        fx_per_um=result.fx_per_um,
    )
    spectrum_error = float(np.max(np.abs(result.spectrum - expected["expected_spectrum"])))
    volume_error = float(np.max(np.abs(result.volume - expected["expected_volume"])))
    summary = {
        "spectrum_complex_max_error": spectrum_error,
        "volume_complex_max_error": volume_error,
        "spectrum_bound": float(expected["spectrum_bound"]),
        "volume_bound": float(expected["volume_bound"]),
        "spectrum_amplitude_max_error": float(
            np.max(np.abs(np.abs(result.spectrum) - np.abs(expected["expected_spectrum"])))
        ),
        "different_after_shift_max_difference": float(
            np.max(np.abs(expected["after_shift_spectrum"] - expected["expected_spectrum"]))
        ),
        "voxel_size_um": result.voxel_size_um,
        "input_sha256": hashlib.sha256((source / "inputs.npz").read_bytes()).hexdigest(),
        "expectation_sha256": hashlib.sha256(
            (source / "expectations.npz").read_bytes()
        ).hexdigest(),
        "observed_sha256": hashlib.sha256((destination / "observed.npz").read_bytes()).hexdigest(),
        "passed": spectrum_error <= float(expected["spectrum_bound"])
        and volume_error <= float(expected["volume_bound"]),
    }
    (destination / "observation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit("Predeclared comparison failed")


def render(source: Path, observation: Path, destination: Path) -> None:
    """Render retained observations; the render environment does no science fit."""
    import matplotlib  # pyright: ignore[reportMissingImports]

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # pyright: ignore[reportMissingImports]

    destination.mkdir(parents=True, exist_ok=False)
    with np.load(source / "expectations.npz") as archive:
        expected = {key: archive[key] for key in archive.files}
    with np.load(observation / "observed.npz") as archive:
        observed = {key: archive[key] for key in archive.files}
    spectrum = observed["spectrum"][0]
    truth = expected["expected_spectrum"][0]
    alternate = expected["after_shift_spectrum"][0]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    half_x = float(observed["fx_per_um"][1] - observed["fx_per_um"][0]) / 2
    half_y = float(observed["fy_per_um"][1] - observed["fy_per_um"][0]) / 2
    extent = [
        float(observed["fx_per_um"][0]) - half_x,
        float(observed["fx_per_um"][-1]) + half_x,
        float(observed["fy_per_um"][0]) - half_y,
        float(observed["fy_per_um"][-1]) + half_y,
    ]
    image = axes[0, 0].imshow(
        np.abs(spectrum), origin="lower", extent=extent, aspect="auto", cmap="magma"
    )
    fig.colorbar(image, ax=axes[0, 0], label="Coefficient amplitude [input intensity]")
    axes[0, 0].set(
        title="Observed fractional finite-window spectrum",
        xlabel="fx [cycles/µm]",
        ylabel="fy [cycles/µm]",
    )
    row = spectrum.shape[0] // 2
    frequency = observed["fx_per_um"]
    axes[0, 1].plot(frequency, spectrum[row].real, "o", label="Observed real")
    axes[0, 1].plot(frequency, truth[row].real, "-", label="Direct-sum real")
    axes[0, 1].plot(frequency, spectrum[row].imag, "x", label="Observed imaginary")
    axes[0, 1].plot(frequency, truth[row].imag, "--", label="Direct-sum imaginary")
    axes[0, 1].set(
        title="Full complex agreement at fy=0",
        xlabel="fx [cycles/µm]",
        ylabel="Coefficient [input intensity]",
    )
    axes[0, 1].legend(fontsize=8)
    axes[1, 0].plot(frequency, np.abs(truth[row]), "o-", label="Filter before shift")
    axes[1, 0].plot(
        frequency,
        np.abs(alternate[row]),
        "s--",
        label="Shift arrays, then quotient",
    )
    axes[1, 0].set(
        title="Filter order changes this finite estimator",
        xlabel="fx [cycles/µm]",
        ylabel="Amplitude [input intensity]",
    )
    axes[1, 0].legend(fontsize=8, loc="upper left")
    component = expected["components"][3, 0]
    axes[1, 1].semilogy(frequency, np.maximum(np.sum(np.abs(component), axis=0), 1e-18), "o-")
    axes[1, 1].set(
        title="Order +1: finite phase-ramp smearing",
        xlabel="fx [cycles/µm]",
        ylabel="Sum over fy of amplitude [input intensity]",
    )
    fig.suptitle("RA07: declared periodic finite-window relocation; no continuum-resolution claim")
    fig.savefig(destination / "fractional-placement.png", dpi=160)
    fig.savefig(destination / "fractional-placement.svg")
    plt.close(fig)


def main() -> None:
    """Dispatch one explicit preparation, observation or rendering operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "observe", "render"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.destination)
    elif args.mode == "observe" and args.source is not None:
        observe(args.source, args.destination)
    elif args.mode == "render" and args.source is not None and args.observation is not None:
        render(args.source, args.observation, args.destination)
    else:
        parser.error("Required source/observation paths missing")


if __name__ == "__main__":
    main()
