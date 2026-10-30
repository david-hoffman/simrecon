"""Retain fixed-design RA06 observations and render their scientific figures.

This report driver is outside the product API and test oracles. The design stage
uses only independently assembled finite sums. The observation stage consumes
those saved arrays and the additive public estimator, without retuning anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    """Return the SHA-256 of retained bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid(shape):
    """Enumerate voxel indices in row-major order."""
    return np.stack(np.meshgrid(*(np.arange(n) for n in shape), indexing="ij"), -1).reshape(-1, 3)


def modes(shape):
    """Enumerate centered integer Fourier modes."""
    return np.stack(
        np.meshgrid(*(np.arange(-(n // 2), (n + 1) // 2) for n in shape), indexing="ij"),
        -1,
    ).reshape(-1, 3)


def fourier(shape):
    """Construct the unnormalized finite analysis matrix."""
    return np.exp(-2j * np.pi * (modes(shape) / np.array(shape)) @ grid(shape).T)


def decimal_solve(matrix, rhs):
    """Independent pivoted elimination on the exact stored real normal system."""
    with localcontext() as ctx:
        ctx.prec = 70
        n = len(rhs)
        aug = [
            [Decimal.from_float(float(v)) for v in matrix[i]] + [Decimal.from_float(float(rhs[i]))]
            for i in range(n)
        ]
        for j in range(n):
            k = max(range(j, n), key=lambda i: abs(aug[i][j]))
            aug[j], aug[k] = aug[k], aug[j]
            divisor = aug[j][j]
            for k in range(j, n + 1):
                aug[j][k] /= divisor
            for i in range(n):
                if i == j:
                    continue
                factor = aug[i][j]
                for k in range(j, n + 1):
                    aug[i][k] -= factor * aug[j][k]
        return np.array([float(row[-1]) for row in aug])


def design(destination):
    """Save inputs, truth and all model choices before product observations."""
    destination.mkdir(exist_ok=False, parents=True)
    settings_path = ROOT / "docs/reports/reference-alignment-ra06-design.json"
    settings = json.loads(settings_path.read_text())
    ds = tuple(settings["detector_shape"])
    out = tuple(settings["output_shape"])
    m = int(np.prod(ds))
    p = int(np.prod(out))
    phi = np.array(settings["phases_rad"])
    carriers = np.array(settings["carriers_bins"], dtype=np.int64)
    gains = np.array(settings["gains"])
    c, s = np.cos(phi), np.sin(phi)
    k = np.stack((np.ones_like(c), 2 * c, -2 * s, 2 * (c * c - s * s), -2 * ((2 * c) * s)), -1)
    std = np.array(settings["noise_std_by_exposure"])
    rho = settings["correlation_common_fraction"]
    sigma = np.array([(1 - rho) * np.diag(v * v) + rho * np.outer(v, v) for v in std])
    fd, fo = fourier(ds), fourier(out)
    dj, oq = modes(ds), modes(out)
    output_index = {tuple(q): i for i, q in enumerate(oq)}
    # Per-site effective kernel: one point plus finite nearest-neighbor blur.
    kernel = np.zeros(ds)
    kernel[0, 0, 0] = 0.72
    kernel[0, 1, 0] = kernel[0, -1, 0] = 0.06
    kernel[0, 0, 1] = kernel[0, 0, -1] = 0.08
    h = fd @ kernel.ravel()
    values = np.array(
        [
            np.stack((h, (0.52 + 0.13j) * h, (0.23 - 0.09j) * h)),
            np.stack((h, (0.43 - 0.18j) * h, (0.29 + 0.07j) * h)),
        ]
    ).reshape(2, 3, *ds)
    # Assemble one real observation column for each real output voxel.
    maps = []
    for r in range(2):
        bands = []
        for order in range(3):
            q = dj - np.array([0, *(order * carriers[r])])
            qi = np.array([output_index[tuple(v)] for v in q])
            bands.append(
                fd.conj().T @ ((gains[r] * values[r, order].ravel())[:, None] * fo[qi]) / p
            )
        coords = np.stack(
            (bands[0].real, bands[1].real, bands[1].imag, bands[2].real, bands[2].imag)
        )
        maps.append(np.einsum("nf,fmp->nmp", k[r], coords).reshape(-1, p))
    a = np.concatenate(maps)
    z, y, x = grid(out).T
    truth = 2 + 0.45 * np.cos(2 * np.pi * (x / out[2] + y / out[1]))
    truth += 0.3 * np.sin(4 * np.pi * x / out[2]) + 0.14 * np.cos(8 * np.pi * x / out[2])
    clean = (a @ truth).reshape(2, len(phi[0]), *ds)
    rng = np.random.default_rng(settings["noise_seed"])
    noise = np.array(
        [np.linalg.cholesky(sigma[r]) @ rng.standard_normal((len(phi[0]), m)) for r in range(2)]
    )
    noise = noise.reshape(clean.shape)
    images = clean + noise
    taper = np.ones(out)
    # Separate asymmetric post-inverse control; it never enters the objective.
    taper[..., 0] = 0.2
    np.savez(
        destination / "inputs.npz",
        phases=phi,
        carriers=carriers,
        gains=gains,
        covariance=sigma,
        values=values,
        forward=a,
        phase_design=k,
        truth=truth.reshape(out),
        clean=clean,
        noise=noise,
        images=images,
        detector_fourier=fd,
        output_fourier=fo,
        taper=taper,
    )
    record = {
        "stage": "fixed design before product",
        "settings": settings,
        "settings_sha256": digest(settings_path),
        "arrays_sha256": digest(destination / "inputs.npz"),
        "driver_sha256": digest(__file__),
        "argv": sys.argv,
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "premise": (
            "Known finite periodic model and declared stationary exposure "
            "covariance; no truth or noise supplied for parameter selection"
        ),
    }
    (destination / "design.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"design": str(destination), "arrays_sha256": record["arrays_sha256"]}))


def observe(source, destination):
    """Measure the product against a retained independently assembled real map."""
    from simrecon import VolumeOrderOtf, reconstruct_volume_weighted

    destination.mkdir(exist_ok=False, parents=True)
    design_record = json.loads((source / "design.json").read_text())
    assert digest(source / "inputs.npz") == design_record["arrays_sha256"]
    s = design_record["settings"]
    v = dict(np.load(source / "inputs.npz"))
    ds, out = tuple(s["detector_shape"]), tuple(s["output_shape"])
    m, p = int(np.prod(ds)), int(np.prod(out))
    rcount, n = v["images"].shape[:2]
    a = v["forward"]
    alpha = s["alpha"]
    blocks = []
    psi = []
    separated = []
    for r in range(rcount):
        sinv = np.linalg.solve(v["covariance"][r], np.eye(n))
        blocks.append(np.kron(sinv, np.eye(m)))
        inf = v["phase_design"][r].T @ sinv @ v["phase_design"][r]
        ps = np.linalg.solve(inf, np.eye(5))
        psi.append(ps)
        separated.append(ps @ v["phase_design"][r].T @ sinv @ v["images"][r].reshape(n, m))
    w = np.zeros((rcount * n * m, rcount * n * m))
    width = n * m
    for r, block in enumerate(blocks):
        w[r * width : (r + 1) * width, r * width : (r + 1) * width] = block
    normal = a.T @ w @ a / m + alpha * np.eye(p) / p
    rhs = a.T @ w @ v["images"].ravel() / m
    ref = decimal_solve(normal, rhs)
    linear = np.linalg.solve(normal, a.T @ w / m)
    clean_ref = linear @ v["clean"].ravel()
    cond = float(np.linalg.cond(normal))
    eps = np.finfo(float).eps
    # Fixed before any product calls; conservative sum/solve comparison budget.
    # The fixed input bound is from the public moderate regime, not this noise
    # draw or its fitted source. The linear operator depends only on declarations.
    fixed_image_bound = 16.0
    assert np.max(np.abs(v["images"])) <= fixed_image_bound
    scale_bound = max(1.0, float(np.linalg.norm(linear, ord=np.inf)) * fixed_image_bound)
    budget = 4096 * eps * max(a.shape) * max(1, cond) * scale_bound
    coords = [
        np.arange(-(d // 2), (d + 1) // 2) / (d * spacing)
        for d, spacing in zip(ds, s["voxel_size_um"], strict=True)
    ]
    records = [
        VolumeOrderOtf(
            values=v["values"][r].copy(),
            fz_per_um=coords[0].copy(),
            fy_per_um=coords[1].copy(),
            fx_per_um=coords[2].copy(),
            voxel_size_um=tuple(s["voxel_size_um"]),
            origin_zyx=(0, 0, 0),
            source=f"RA06 independently finite-summed kernel orientation {r}",
        )
        for r in range(rcount)
    ]
    kwargs = dict(
        order_otfs=records,
        phases_rad=v["phases"],
        carriers_bins=v["carriers"],
        gains=v["gains"],
        exposure_covariance=v["covariance"],
        regularization=alpha,
        output_shape_yx=out[1:],
        apodization=np.ones(out),
    )
    source_hashes = {
        str(f.relative_to(ROOT)): digest(f) for f in sorted((ROOT / "src/simrecon").glob("*.py"))
    }
    start = {
        "argv": sys.argv,
        "source": str(source),
        "driver_sha256": digest(__file__),
        "input_arrays_sha256": digest(source / "inputs.npz"),
        "lock_sha256": digest(ROOT / "uv.lock"),
        "source_hashes": source_hashes,
        "python": sys.version,
        "executable": sys.executable,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "alpha": alpha,
        "precall_absolute_budget": budget,
    }
    (destination / "observation-start.json").write_text(json.dumps(start, indent=2) + "\n")

    def measured_call(label, images):
        result = reconstruct_volume_weighted(images, **kwargs)
        names = (
            "volume",
            "spectrum",
            "untapered_volume",
            "untapered_spectrum",
            "separated_coordinates",
            "separated_covariance",
            "predicted_images",
            "residual_images",
            "data_objective",
            "penalty_objective",
            "information_rank",
            "unknown_count",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
        )
        # Retain this completed fit before another call or acceptance assertion.
        np.savez(
            destination / f"call-{label}.npz", **{name: getattr(result, name) for name in names}
        )
        return result

    result = measured_call("noisy", v["images"])
    fitted_clean = measured_call("clean", v["clean"])
    kwargs["apodization"] = v["taper"]
    tapered = measured_call("tapered", v["images"])
    x = result.untapered_volume.ravel()
    residual = v["images"].ravel() - a @ x
    normal_residual = normal @ x - rhs
    error = float(np.max(np.abs(x - ref)))
    comparison_pass = bool(error <= budget)
    taper_difference = float(np.max(np.abs(tapered.untapered_volume - result.untapered_volume)))
    taper_pass = bool(taper_difference <= budget)
    actual_noise_spectrum = (v["detector_fourier"] @ v["noise"].reshape(-1, m).T / m).T
    residual_spectrum = (v["detector_fourier"] @ result.residual_images.reshape(-1, m).T / m).T
    # Expected risk uses the declared Gaussian demonstration law and fixed inverse.
    covraw = np.zeros_like(w)
    for r in range(rcount):
        covraw[r * width : (r + 1) * width, r * width : (r + 1) * width] = np.kron(
            v["covariance"][r], np.eye(m)
        )
    covariance_x = linear @ covraw @ linear.T
    bias = clean_ref - v["truth"].ravel()
    expected_mse = float((bias @ bias + np.trace(covariance_x)) / p)
    rng = np.random.default_rng(s["risk_seed"])
    draws = []
    noise_draws = []
    for _ in range(s["risk_replicates"]):
        noise = np.concatenate(
            [
                (np.linalg.cholesky(v["covariance"][r]) @ rng.standard_normal((n, m))).ravel()
                for r in range(rcount)
            ]
        )
        draws.append(clean_ref + linear @ noise)
        noise_draws.append(noise)
    draws = np.array(draws)
    noise_draws = np.array(noise_draws)
    mse = np.mean((draws - v["truth"].ravel()) ** 2, axis=1)
    beta = alpha * float(np.mean(np.diagonal(v["covariance"], axis1=1, axis2=2)))
    unweighted = np.linalg.solve(a.T @ a / m + beta * np.eye(p) / p, a.T @ v["images"].ravel() / m)
    fields = {
        name: getattr(result, name)
        for name in (
            "volume",
            "spectrum",
            "untapered_volume",
            "untapered_spectrum",
            "separated_coordinates",
            "separated_covariance",
            "predicted_images",
            "residual_images",
        )
    }
    np.savez(
        destination / "observations.npz",
        **fields,
        independent_solution=ref.reshape(out),
        independent_separated=np.array(separated).reshape(rcount, 5, *ds),
        independent_covariance=np.array(psi),
        independent_normal=normal,
        independent_rhs=rhs,
        independent_residual=residual.reshape(v["images"].shape),
        normal_residual=normal_residual,
        actual_noise_spectrum=actual_noise_spectrum.reshape(v["images"].shape),
        actual_residual_spectrum=residual_spectrum.reshape(v["images"].shape),
        fitted_clean=fitted_clean.untapered_volume,
        tapered_volume=tapered.volume,
        tapered_spectrum=tapered.spectrum,
        linear_estimator=linear,
        reconstruction_covariance=covariance_x,
        bias=bias.reshape(out),
        monte_carlo_estimates=draws,
        monte_carlo_noise=noise_draws,
        monte_carlo_mse=mse,
        unweighted_comparison=unweighted.reshape(out),
    )
    record = {
        "stage": "observed product and independent stored-input inverse",
        "argv": sys.argv,
        "design": str(source),
        "design_json_sha256": digest(source / "design.json"),
        "input_arrays_sha256": digest(source / "inputs.npz"),
        "arrays_sha256": digest(destination / "observations.npz"),
        "driver_sha256": digest(__file__),
        "alpha": alpha,
        "unweighted_beta": beta,
        "independent_normal_condition": cond,
        "precall_absolute_budget": budget,
        "fixed_image_bound": fixed_image_bound,
        "matrix_only_solution_bound": scale_bound,
        "maximum_inverse_difference": error,
        "normal_residual_linf": float(np.max(np.abs(normal_residual))),
        "estimator_comparison_pass": comparison_pass,
        "taper_invariance_pass": taper_pass,
        "taper_untapered_difference_linf": taper_difference,
        "separated_difference_linf": float(
            np.max(
                np.abs(result.separated_coordinates - np.array(separated).reshape(rcount, 5, *ds))
            )
        ),
        "covariance_difference_linf": float(
            np.max(np.abs(result.separated_covariance - np.array(psi)))
        ),
        "data_objective": result.data_objective,
        "penalty_objective": result.penalty_objective,
        "independent_data_objective": float(residual @ w @ residual / m),
        "independent_penalty_objective": float(alpha * (x @ x) / p),
        "information_rank": result.information_rank,
        "unknown_count": result.unknown_count,
        "conditional_expected_mse_intensity_squared": expected_mse,
        "observed_mse_intensity_squared": float(np.mean((x - v["truth"].ravel()) ** 2)),
        "monte_carlo_mean_mse_intensity_squared": float(np.mean(mse)),
        "risk_acceptance": (
            "None: sampling outcomes are descriptive, never deterministic accuracy thresholds"
        ),
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "source_hashes": source_hashes,
        "lock_sha256": start["lock_sha256"],
        "per_call_arrays": {f.name: digest(f) for f in destination.glob("call-*.npz")},
        "limits": s["claim_limits"],
    }
    (destination / "observation.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: record[k]
                for k in (
                    "maximum_inverse_difference",
                    "precall_absolute_budget",
                    "normal_residual_linf",
                    "information_rank",
                    "unknown_count",
                    "conditional_expected_mse_intensity_squared",
                    "monte_carlo_mean_mse_intensity_squared",
                )
            }
        )
    )
    assert comparison_pass
    assert taper_pass


def render(source, observed, destination):
    """Plot retained original observations without running or fitting a model."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destination.mkdir(exist_ok=False, parents=True)
    v = dict(np.load(source / "inputs.npz"))
    o = dict(np.load(observed / "observations.npz"))
    settings = json.loads((source / "design.json").read_text())["settings"]
    record = json.loads((observed / "observation.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    color_limit = float(np.max(np.abs(o["separated_covariance"][0])))
    q = axes[0, 0].imshow(
        o["separated_covariance"][0], cmap="coolwarm", vmin=-color_limit, vmax=color_limit
    )
    labels = ["dc", "Re c₁", "Im c₁", "Re c₂", "Im c₂"]
    axes[0, 0].set_xticks(range(5), labels, rotation=30)
    axes[0, 0].set_yticks(range(5), labels)
    axes[0, 0].set(title="Propagated covariance, orientation 0")
    fig.colorbar(q, ax=axes[0, 0], label="intensity²")
    output_dx = v["images"].shape[-1] * settings["voxel_size_um"][2] / v["truth"].shape[-1]
    xx = np.arange(v["truth"].shape[-1]) * output_dx
    axes[0, 1].plot(xx, v["truth"][0, 0], "k-", label="Evaluator source")
    axes[0, 1].plot(xx, o["untapered_volume"][0, 0], "o-", label="Weighted inverse")
    axes[0, 1].plot(xx, o["independent_solution"][0, 0], "+", label="Independent real normal solve")
    axes[0, 1].set(
        title=f"One source row; fixed α = {record['alpha']:g} intensity⁻²",
        xlabel="x position (µm), y=z=0",
        ylabel="Intensity",
    )
    axes[0, 1].legend(fontsize=8)
    native_shape = v["images"].shape[-3:]
    center_z = native_shape[0] // 2
    power_n = np.mean(
        np.mean(np.abs(o["actual_noise_spectrum"]) ** 2, axis=(0, 1))[center_z], axis=0
    )
    power_r = np.mean(
        np.mean(np.abs(o["actual_residual_spectrum"]) ** 2, axis=(0, 1))[center_z], axis=0
    )
    kx = (np.arange(native_shape[2]) - native_shape[2] // 2) / (
        native_shape[2] * settings["voxel_size_um"][2]
    )
    expected = np.mean(np.diagonal(v["covariance"], axis1=1, axis2=2)) / int(np.prod(native_shape))
    axes[1, 0].plot(kx, power_n, "o-", label="Actual injected noise")
    axes[1, 0].plot(kx, power_r, "s-", label="Actual untapered fit residual")
    axes[1, 0].axhline(expected, color="k", linestyle="--", label="Declared mean raw noise power")
    axes[1, 0].set(
        title="kz=0; mean over ky, exposures and orientations",
        xlabel="Lateral frequency kx (cycles/µm)",
        ylabel="Power per coefficient (intensity²)",
    )
    axes[1, 0].set_ylim(bottom=0)
    axes[1, 0].legend(fontsize=8, loc="lower left")
    axes[1, 1].hist(o["monte_carlo_mse"], bins=24, color="#5999bd", alpha=0.85)
    axes[1, 1].axvline(
        record["conditional_expected_mse_intensity_squared"],
        color="k",
        label="Analytic conditional expected risk",
    )
    axes[1, 1].axvline(
        record["observed_mse_intensity_squared"],
        color="#c45b39",
        linestyle="--",
        label="Single observed product error",
    )
    axes[1, 1].set(
        title=f"Independent inverse: {settings['risk_replicates']} fixed-seed draws",
        xlabel="Mean squared source error (intensity²)",
        ylabel="Draw count",
    )
    axes[1, 1].legend(fontsize=8)
    fig.suptitle("RA06: covariance weighting, reconstruction and risk")
    for suffix in ("png", "svg"):
        fig.savefig(destination / f"weighted-inverse.{suffix}", dpi=170)
    plt.close(fig)
    report = {
        "argv": sys.argv,
        "python": sys.version,
        "executable": sys.executable,
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "MPLCONFIGDIR": os.environ.get("MPLCONFIGDIR"),
        "source_arrays_sha256": digest(source / "inputs.npz"),
        "observations_sha256": digest(observed / "observations.npz"),
        "spectral_display": {
            "kz_per_um": 0,
            "averaged_axes": ["orientation", "exposure", "ky"],
            "kx_per_um": kx.tolist(),
            "noise_power": power_n.tolist(),
            "residual_power": power_r.tolist(),
            "power_unit": "intensity_squared",
            "scale": "linear",
        },
        "covariance_display": {
            "scale": "linear, symmetric about zero",
            "limits": [-color_limit, color_limit],
        },
        "driver_sha256": digest(__file__),
        "outputs": {p.name: digest(p) for p in destination.glob("weighted-inverse.*")},
    }
    (destination / "render.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["outputs"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("design", "observe", "render"))
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--observed", type=Path)
    args = parser.parse_args()
    if args.stage == "design":
        design(args.destination)
    elif args.stage == "observe":
        observe(args.source, args.destination)
    else:
        render(args.source, args.observed, args.destination)
