"""Measure RA05 from retained independent data without changing original inputs.

Run this report example with the locked worktree interpreter. The output directory
must be new. This is report code, not shipped runtime or a verification gate.
"""

import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from fractions import Fraction
from itertools import product
from pathlib import Path

import numpy as np

import simrecon as sc

ROOT = Path(__file__).resolve().parents[2]
RETAINED_ORIGINAL = ROOT / "artifacts/ra05/A/independent_fixture_data_v2.npz"
PUBLISHED_INPUT = ROOT / "docs/reports/data/reference-alignment-ra05-independent-v2.npz"
ORIGINAL = RETAINED_ORIGINAL if RETAINED_ORIGINAL.exists() else PUBLISHED_INPUT
ORIGINAL_SHA = "f9b108ce86f834cb4ebf613a601559d73bf863ef7ab8a8eb78b69d9da2a5a3d2"


def digest(path):
    """Return the complete regular-file SHA256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_observer():
    """Load the reviewed independent scientific fixture by explicit path."""
    path = ROOT / "tests/reference_alignment_ra05_fixture.py"
    spec = importlib.util.spec_from_file_location("ra05_reviewed_observer", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def census():
    """Fingerprint material scientific sources, lock and interpreter inputs."""
    paths = sorted((ROOT / "src/simrecon").rglob("*.py"))
    paths += [
        ROOT / "tests/reference_alignment_ra05_fixture.py",
        ROOT / "tests/test_reference_alignment_ra05.py",
        ROOT / "docs/contracts/reference-alignment-ra05-v1.md",
        ROOT / "uv.lock",
        ROOT / "pyproject.toml",
        Path(__file__).resolve(),
        ORIGINAL,
        PUBLISHED_INPUT,
    ]
    result = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    for name in ("numpy", "scipy", "h5py", "tifffile", "simrecon"):
        distribution = importlib.metadata.distribution(name)
        for member in distribution.files or ():
            if str(member).endswith(".pyc"):
                continue
            path = distribution.locate_file(member)
            alias = "installed/" + name + "/" + str(member)
            if path.is_symlink():
                resolved = path.resolve()
                result[alias] = {
                    "link_text": str(path.readlink()),
                    "resolved_sha256": digest(resolved) if resolved.is_file() else None,
                }
            elif path.is_file():
                result[alias] = digest(path)
            else:
                result[alias] = {"status": "not_a_present_regular_file"}
    return result


def declared_pair(exposures, destination, label):
    """Create and retain actual nonidentity camera inputs in one common gauge."""
    signal = np.array(exposures[None], dtype=np.float64, order="C")
    indices = np.indices(signal.shape)
    offset = 7.0 + indices[-1] / 8
    response = 2.0 + indices[-2] / 8
    exposure = 0.5 + indices[1] / 8
    raw = offset + response * exposure * signal
    expected = ((raw - offset) / response) / exposure
    np.savez_compressed(
        destination / (label + "-bead-inputs.npz"),
        raw=raw,
        offset=offset,
        response=response,
        exposure_factor=exposure,
        expected_corrected=expected,
        original_exposures=exposures,
    )
    bead = sc.declare_acquisition(
        raw,
        config={
            "version": 1,
            "axes": ["orientation", "phase", "z", "y", "x"],
            "acquisition_kind": "sim_beads",
            "intensity_unit": "bead_counts",
            "calibration_id": "declared-bead-identity",
            "sampling_um": {"z": 9.0, "y": 8.0, "x": 7.0},
            "nominal_phases_rad": np.zeros((1, len(exposures))).tolist(),
        },
        original_metadata={"cohort": "RA05 retained independent bead control: " + label},
    )
    specimen_signal = 1 + np.arange(1 * 5 * 5 * 8 * 10).reshape(1, 5, 5, 8, 10) % 13 / 32
    specimen_raw = 9 + 3 * 0.75 * specimen_signal
    np.savez_compressed(
        destination / (label + "-specimen-inputs.npz"),
        raw=specimen_raw,
        offset=np.array(9.0),
        response=np.array(3.0),
        exposure_factor=np.array(0.75),
        expected_corrected=((specimen_raw - 9) / 3) / 0.75,
    )
    specimen = sc.declare_acquisition(
        specimen_raw,
        config={
            "version": 1,
            "axes": ["orientation", "phase", "z", "y", "x"],
            "acquisition_kind": "specimen_sim",
            "intensity_unit": "specimen_counts",
            "calibration_id": "different-opaque-specimen-identity",
            "sampling_um": {"z": 0.4, "y": 0.125, "x": 0.125},
        },
    )
    pair = sc.correct_alignment_pair(
        specimen,
        bead=bead,
        mode="declared",
        output_unit="reference_signal",
        gauge_source="RA05 explicit matched reference signal gauge",
        specimen_exposure_factor=0.75,
        bead_exposure_factor=exposure,
        reference_sum_equalization="disabled",
        specimen_offset=9.0,
        specimen_response=3.0,
        bead_offset=offset,
        bead_response=response,
    )
    save_record(destination, label + "-camera-pair", pair)
    np.testing.assert_array_equal(pair.bead.data, expected)
    return pair, {
        "bead_raw": raw,
        "bead_offset": offset,
        "bead_response": response,
        "bead_exposure": exposure,
        "expected_corrected_bead": expected,
        "specimen_raw": specimen_raw,
        "expected_corrected_specimen": ((specimen_raw - 9) / 3) / 0.75,
    }


def calibrate(pair, original, *, bead_mode="discrete_profile", minimum=0.15):
    """Call the real corrected-array adapter with fixed declared settings."""
    return sc.calibrate_alignment_bead(
        pair,
        group={"orientation": 0},
        phases_rad=original["phases_rad"],
        voxel_size_um=tuple(original["voxel_size_um"]),
        calibration_carrier_bins=tuple(int(x) for x in original["calibration_carrier_bins"]),
        bead_mode=bead_mode,
        bead_profile=original["profile"] if bead_mode == "discrete_profile" else None,
        min_profile_transfer=minimum,
        source="RA05 independent unequal-beam " + bead_mode + " calibration",
    )


def predict_exposures(calibration, original, profile, expected, components, budget, observer):
    """Propagate the measured transfer back to the declared bead exposure model."""
    shape = original["profile"].shape
    mass_record = calibration.provenance["dc_mass"]
    exact_mass = Fraction(mass_record["numerator"], mass_record["denominator"])
    mass = float(exact_mass)
    reference_mass = np.sum(components[0].real, dtype=np.longdouble)
    mass_difference = float(abs(exact_mass - Fraction(float(reference_mass))))
    origin = calibration.response.origin_zyx
    carrier = (0, *(int(x) for x in original["calibration_carrier_bins"]))
    centered_modes = list(product(*observer.modes(shape)))
    predicted_components = np.empty_like(calibration.response.values)
    allowances = []
    profile_maximum = float(np.max(np.abs(profile)))
    for order in range(3):
        spectrum = np.empty(shape, dtype=np.complex128)
        for index, mode in zip(np.ndindex(shape), centered_modes, strict=True):
            shifted = tuple(
                (k - order * c + n // 2) % n for k, c, n in zip(mode, carrier, shape, strict=True)
            )
            cycles = sum(
                (Fraction(k * b, n) for k, b, n in zip(mode, origin, shape, strict=True)),
                Fraction(),
            )
            spectrum[index] = (
                calibration.response.values[(order, *index)]
                * observer.phasor(-cycles)
                * profile[shifted]
                * mass
            )
        predicted_components[order] = observer.direct_inverse(spectrum)
        reference_maximum = float(np.max(np.abs(expected[order])))
        inverse_allowance = (
            256
            * original["profile"].size
            * observer.EPS
            * max(1.0, mass)
            * max(1.0, reference_maximum)
        )
        allowances.append(
            mass * float(budget[order]) * profile_maximum
            + mass_difference * reference_maximum * profile_maximum
            + inverse_allowance
        )
    basis = observer.phase_basis(original["phases_rad"])

    def assemble(values):
        """Evaluate the represented five-column exposure model."""
        return (
            values[0].real[None]
            + 2 * basis[:, 1, None, None, None] * values[1].real
            - 2 * basis[:, 2, None, None, None] * values[1].imag
            + 2 * basis[:, 3, None, None, None] * values[2].real
            - 2 * basis[:, 4, None, None, None] * values[2].imag
        )

    prediction = assemble(predicted_components)
    independent_fit = assemble(components)
    phase_allowance = (
        64
        * observer.EPS
        * float(
            np.max(
                np.abs(predicted_components[0])
                + 2 * np.abs(predicted_components[1])
                + 2 * np.abs(predicted_components[2])
            )
        )
    )
    allowance = allowances[0] + 2 * allowances[1] + 2 * allowances[2] + phase_allowance
    error = float(np.max(np.abs(prediction - independent_fit)))
    if error > allowance:
        raise ValueError("propagated exposure-prediction allowance exceeded")
    return (
        prediction,
        independent_fit,
        {
            "max_error_to_independent_represented_fit": error,
            "allowance_to_independent_represented_fit": allowance,
            "component_allowance": allowances,
            "interpretation": (
                "Native E is uncentered, multiplied by independent P(k-m*kc) and original S, "
                "then inverse finite-summed and evaluated with the represented phase basis. "
                "This is a prediction relation; transfer accuracy is checked separately "
                "against independent represented-fit/profile finite sums."
            ),
            "bound": (
                "Each inverse finite sum has convex 1/M weights: "
                "S*Delta_E*max|P| + |S-S_reference|*max|E_reference|*max|P|. "
                "Add 256*M*eps*max(1,S)*max(1,max|E_reference|) observer allowance per order, "
                "then weights 1,2,2 and a 64*eps represented-phase assembly allowance."
            ),
        },
    )


def json_value(value, arrays=None, key="root"):
    """Describe metadata recursively while retaining arrays in separate NPZ files."""
    if isinstance(value, np.ndarray):
        data = np.ascontiguousarray(value)
        if arrays is not None:
            arrays[key] = data.copy()
        return {
            "archive_key": key if arrays is not None else None,
            "dtype": str(value.dtype),
            "shape": list(value.shape),
            "sha256_contiguous_numeric_bytes": hashlib.sha256(data.tobytes()).hexdigest(),
        }
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: json_value(getattr(value, name), arrays, key + "." + name)
            for name in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {
            name: json_value(item, arrays, key + "." + str(name)) for name, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [json_value(item, arrays, key + "." + str(i)) for i, item in enumerate(value)]
    if isinstance(value, np.generic):
        return value.item()
    return value


def point_limit_observation(destination, original, observer, finite_response, finite_budget):
    """Measure point and declared origin-point controls from the reviewed generator."""
    point = observer.make_case(
        shape=tuple(original["profile"].shape),
        kind="point",
        anchor=tuple(int(x) for x in original["anchor_zyx"]),
        carrier=tuple(int(x) for x in original["calibration_carrier_bins"]),
        brightness=float(original["brightness"]),
        alpha=float(original["calibration_phase_rad"]),
    )
    np.testing.assert_allclose(
        point.kernels,
        original["kernels"],
        rtol=0,
        atol=128 * observer.EPS * max(1, float(np.max(np.abs(original["kernels"])))),
    )
    np.testing.assert_array_equal(point.phases, original["phases_rad"])
    point_original = dict(original)
    point_original["profile"] = point.profile
    point_original["exposures"] = point.exposures
    np.savez_compressed(
        destination / "point-source-inputs.npz",
        exposures=point.exposures,
        profile=point.profile,
        h=point.h,
        kernels=point.kernels,
        phases_rad=point.phases,
        anchor_zyx=np.array(point.anchor),
        carrier_bins=np.array(point.carrier),
        brightness=np.array(point.brightness),
        calibration_phase_rad=np.array(point.alpha),
    )
    pair, inputs = declared_pair(point.exposures, destination, "point")
    ordinary = calibrate(pair, point_original, bead_mode="point", minimum=None)
    identity = calibrate(pair, point_original, bead_mode="discrete_profile", minimum=1.0)
    save_record(destination, "point-calibration", ordinary)
    save_record(destination, "origin-point-profile-calibration", identity)
    components = observer.fit_components(inputs["expected_corrected_bead"][0], point.phases)
    expected, _, _ = observer.expected_response(
        components, point.profile, point.carrier, point.anchor
    )
    allowance = observer.response_budget(
        inputs["expected_corrected_bead"][0], components, point.profile, 0.15
    )
    point_error = np.max(np.abs(ordinary.response.values - expected), axis=(1, 2, 3))
    identity_error = np.max(np.abs(identity.response.values - expected), axis=(1, 2, 3))
    limit_error = np.max(
        np.abs(identity.response.values - ordinary.response.values), axis=(1, 2, 3)
    )
    profile_error = np.max(np.abs(ordinary.response.values - finite_response), axis=(1, 2, 3))
    if not (
        np.all(point_error <= allowance)
        and np.all(identity_error <= allowance)
        and np.all(limit_error <= 2 * allowance)
        and np.all(profile_error <= allowance + finite_budget)
    ):
        raise ValueError("point/profile limit allowance exceeded")
    np.savez_compressed(
        destination / "point-comparison.npz",
        expected_response=expected,
        point_response=ordinary.response.values,
        origin_point_response=identity.response.values,
        response_budget=allowance,
    )
    return {
        "point_response_max_complex_error": [float(x) for x in point_error],
        "origin_point_profile_max_complex_error": [float(x) for x in identity_error],
        "point_profile_limit_max_complex_difference": [float(x) for x in limit_error],
        "point_profile_limit_allowance": [float(x) for x in 2 * allowance],
        "finite_compensated_to_point_max_complex_difference": [float(x) for x in profile_error],
        "finite_compensated_to_point_allowance": [float(x) for x in allowance + finite_budget],
        "independent_response_allowance": [float(x) for x in allowance],
        "point_origin_zyx": ordinary.response.origin_zyx,
        "origin_point_profile_origin_zyx": identity.response.origin_zyx,
        "source": "Same reviewed generator/fields/h/carrier/phase/anchor, declared point profile.",
        "limits": (
            "Known finite per-site model only; origin-point threshold1 "
            "has exact identity certificate."
        ),
    }


def save_record(destination, label, record):
    """Retain every actual record before comparison decisions can fail."""
    arrays = {}
    metadata = json_value(record, arrays, label)
    np.savez_compressed(destination / (label + "-record-arrays.npz"), **arrays)
    (destination / (label + "-record.json")).write_text(json.dumps(metadata, indent=2) + "\n")


def measure(destination):
    """Retain one actual observation cohort and independent comparison."""
    destination.mkdir(parents=True, exist_ok=False)
    started = time.time()
    before = census()
    (destination / "generation-start.json").write_text(
        json.dumps({"started_unix_s": started, "argv": sys.argv, "source_inputs": before}, indent=2)
        + "\n"
    )
    if digest(ORIGINAL) != ORIGINAL_SHA:
        raise ValueError("retained original independent archive changed")
    observer = load_observer()
    with np.load(ORIGINAL) as archive:
        original = {key: archive[key].copy() for key in archive.files}
    pair, inputs = declared_pair(original["exposures"], destination, "main")
    calibration = calibrate(pair, original)
    save_record(destination, "main-calibration", calibration)
    spacing = tuple(float(x) for x in original["voxel_size_um"])
    carrier = tuple(int(x) for x in original["calibration_carrier_bins"])
    anchor = tuple(int(x) for x in original["anchor_zyx"])
    if calibration.response.origin_zyx != anchor:
        raise ValueError("stable independent anchor not recovered")
    images = inputs["expected_corrected_bead"][0]
    expected_components = observer.fit_components(images, original["phases_rad"])
    expected, profile, localization = observer.expected_response(
        expected_components, original["profile"], carrier, anchor
    )
    budget = observer.response_budget(images, expected_components, original["profile"], 0.15)
    actual = calibration.response.values.copy()
    errors = np.max(np.abs(actual - expected), axis=(1, 2, 3))
    if not np.all(errors <= budget):
        raise ValueError("independent calibrated response allowance exceeded")
    offset, delta = (2, -3), -0.31
    orders = (-2, -1, 0, 1, 2)
    specimen_shape = (5, 8, 10)
    specimen_spacing = (0.4, 0.125, 0.125)
    specimen_carrier = (1, -2)
    q = np.array([0.0, specimen_carrier[0] / (8 * 0.125), specimen_carrier[1] / (10 * 0.125)])
    source_q = np.array([0.0, carrier[0] / (4 * spacing[1]), carrier[1] / (5 * spacing[2])])
    np.testing.assert_array_equal(q, source_q)
    nodes = np.column_stack((np.zeros(7), np.zeros(7), np.arange(-3, 4) / (10 * 0.125)))
    dense = np.column_stack(
        (np.zeros(121), np.zeros(121), np.linspace(nodes[0, 2], nodes[-1, 2], 121))
    )
    queries, objects, returned, targets, dense_targets, sample_budgets = [], [], [], [], [], []
    original_query_returned, original_query_targets = [], []
    record_arrays, sample_records = {}, []
    for order in orders:
        object_points = nodes - order * q
        points = np.asarray(object_points + order * q, dtype=np.float64)
        samples = sc.sample_alignment_order_transfer(
            calibration,
            order=order,
            frequencies_zyx_per_um=points,
            coordinate_offset_yx=offset,
            phase_reference_shift_rad=delta,
            source="RA05 explicit f+m*q on a distinct specimen grid",
        )
        save_record(destination, "sample_" + str(order), samples)
        sample_records.append(json_value(samples, record_arrays, "sample_" + str(order)))
        np.testing.assert_array_equal(samples.frequencies_zyx_per_um, points)
        target = observer.expected_samples(
            expected, spacing, anchor, carrier, offset, delta, order, points
        )
        allowance = float(budget[abs(order)]) + 1024 * observer.EPS * float(
            np.max(np.abs(expected[abs(order)].real) + np.abs(expected[abs(order)].imag))
        )
        if np.max(np.abs(samples.values - target)) > allowance:
            raise ValueError("independent signed sampling allowance exceeded")
        old_points = original["query_points_zyx_per_um"]
        old = sc.sample_alignment_order_transfer(
            calibration,
            order=order,
            frequencies_zyx_per_um=old_points,
            coordinate_offset_yx=offset,
            phase_reference_shift_rad=delta,
            source="RA05 retained non-Cartesian all-axis controls",
        )
        save_record(destination, "original-query_" + str(order), old)
        old_target = observer.expected_samples(
            expected, spacing, anchor, carrier, offset, delta, order, old_points
        )
        if np.max(np.abs(old.values - old_target)) > allowance:
            raise ValueError("non-Cartesian sampling allowance exceeded")
        queries.append(points)
        objects.append(object_points)
        returned.append(samples.values)
        targets.append(target)
        dense_targets.append(
            observer.expected_samples(
                expected, spacing, anchor, carrier, offset, delta, order, dense
            )
        )
        sample_budgets.append(allowance)
        original_query_returned.append(old.values)
        original_query_targets.append(old_target)
    scaled_pair, scaled_inputs = declared_pair(original["exposures"] * 3, destination, "scale3")
    scaled = calibrate(scaled_pair, original)
    save_record(destination, "scale3-calibration", scaled)
    scaled_components = observer.fit_components(
        scaled_inputs["expected_corrected_bead"][0], original["phases_rad"]
    )
    scaled_budget = observer.response_budget(
        scaled_inputs["expected_corrected_bead"][0], scaled_components, original["profile"], 0.15
    )
    scale_error = np.max(np.abs(scaled.response.values - actual), axis=(1, 2, 3))
    if not np.all(scale_error <= budget + scaled_budget):
        raise ValueError("common amplitude scaling response allowance exceeded")
    endpoints = {}
    for order in (1, -1):
        try:
            result = sc.sample_alignment_order_transfer(
                calibration,
                order=order,
                frequencies_zyx_per_um=np.array([[0.0, 2.0, 0.0]]),
                coordinate_offset_yx=offset,
                phase_reference_shift_rad=delta,
                source="RA05 physical even-axis endpoint control",
            )
            save_record(destination, "endpoint_" + str(order), result)
            endpoints[str(order)] = {
                "status": "returned",
                "result": json_value(result, record_arrays, "endpoint_" + str(order)),
            }
        except sc.SimreconError as error:
            endpoints[str(order)] = {"status": "error", "code": error.code}
    if endpoints["1"] != {"status": "error", "code": "incomplete_empirical_transfer_coverage"}:
        raise ValueError("positive missing physical endpoint did not reject")
    if endpoints["-1"]["status"] != "returned":
        raise ValueError("negative reflected physical endpoint did not return")
    mass_record = calibration.provenance["dc_mass"]
    mass = float(Fraction(mass_record["numerator"], mass_record["denominator"]))
    scaled_record = scaled.provenance["dc_mass"]
    scaled_mass = float(Fraction(scaled_record["numerator"], scaled_record["denominator"]))
    prediction, independent_fit, prediction_record = predict_exposures(
        calibration, original, profile, expected, expected_components, budget, observer
    )
    prediction_record["independent_fit_residual_to_corrected_observations"] = float(
        np.max(np.abs(independent_fit - images))
    )
    prediction_record["max_error_to_corrected_observations"] = float(
        np.max(np.abs(prediction - images))
    )
    point_record = point_limit_observation(destination, original, observer, actual, budget)
    arrays = {
        **inputs,
        **{"scaled__" + key: value for key, value in scaled_inputs.items()},
        "predicted_exposures": prediction,
        "independent_fitted_exposures": independent_fit,
        "original_exposures": original["exposures"],
        "phases_rad": original["phases_rad"],
        "expected_components": expected_components,
        "returned_components": np.stack(
            (calibration.components.dc, calibration.components.c1, calibration.components.c2)
        ),
        "expected_response": expected,
        "returned_response": actual,
        "profile_transfer_expected": profile,
        "profile_transfer_returned": calibration.provenance["profile_transfer"],
        "compensated_dc_expected": localization,
        "compensated_dc_returned": calibration.provenance["compensated_dc"],
        "h_at_anchor": np.roll(original["h"], anchor, axis=(0, 1, 2)),
        "response_budget": budget,
        "fz_per_um": calibration.response.fz_per_um,
        "fy_per_um": calibration.response.fy_per_um,
        "fx_per_um": calibration.response.fx_per_um,
        "orders": np.array(orders),
        "query_points": np.array(queries),
        "object_points": np.array(objects),
        "sample_returned": np.array(returned),
        "sample_expected": np.array(targets),
        "sample_budget": np.array(sample_budgets),
        "dense_query_points": dense,
        "dense_sample_expected": np.array(dense_targets),
        "original_query_points": original["query_points_zyx_per_um"],
        "original_query_returned": np.array(original_query_returned),
        "original_query_expected": np.array(original_query_targets),
        "scaled_returned_response": scaled.response.values,
        "scaled_returned_components": np.stack(
            (scaled.components.dc, scaled.components.c1, scaled.components.c2)
        ),
        "scaled_expected_corrected_bead": scaled_inputs["expected_corrected_bead"],
    }
    np.savez_compressed(destination / "observations.npz", **arrays)
    metadata = {
        "started_unix_s": started,
        "completed_unix_s": time.time(),
        "argv": sys.argv,
        "cwd": str(ROOT),
        "python": sys.executable,
        "base_python": sys._base_executable,
        "resolved_python_sha256": digest(Path(sys.executable).resolve()),
        "runtime_environment_inventory_sha256": digest(
            ROOT / "artifacts/ra05/checks/runtime-environment.json"
        ),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "longdouble_epsilon": str(np.finfo(np.longdouble).eps),
        "git_at_generation": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip(),
        "source_inputs_before": before,
        "source_inputs_after": census(),
        "input_archive": str(ORIGINAL.relative_to(ROOT)),
        "input_archive_sha256": ORIGINAL_SHA,
        "output_archive_sha256": digest(destination / "observations.npz"),
        "origin_zyx": anchor,
        "raw_dc_peak_zyx": tuple(
            int(x)
            for x in np.unravel_index(
                np.argmax(calibration.components.dc), calibration.components.dc.shape
            )
        ),
        "response_max_complex_error": [float(x) for x in errors],
        "response_allowance": [float(x) for x in budget],
        "sample_max_complex_error": [
            float(x) for x in np.max(np.abs(np.array(returned) - np.array(targets)), axis=1)
        ],
        "sample_allowance": sample_budgets,
        "exposure_prediction": prediction_record,
        "point_limit": point_record,
        "declared_environment": {
            key: os.environ.get(key)
            for key in (
                "TMPDIR",
                "UV_CACHE_DIR",
                "SIMRECON_JAVA",
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "MKL_NUM_THREADS",
            )
        },
        "dc_mass": copy.deepcopy(mass_record),
        "scaled_dc_mass": copy.deepcopy(scaled_record),
        "observed_mass_scale_ratio": scaled_mass / mass,
        "common_scale_response_max_error": [float(x) for x in scale_error],
        "common_scale_response_allowance": [float(x) for x in budget + scaled_budget],
        "calibration_record": json_value(calibration, record_arrays, "calibration"),
        "scaled_calibration_record": json_value(scaled, record_arrays, "scaled_calibration"),
        "sample_records": sample_records,
        "sampling": {
            "specimen_shape_zyx": specimen_shape,
            "specimen_spacing_um": specimen_spacing,
            "specimen_carrier_bins": specimen_carrier,
            "physical_carrier_zyx_per_um": q.tolist(),
            "coordinate_offset_yx_calibration_samples": offset,
            "specimen_minus_calibration_phase_rad": delta,
            "physical_endpoints": endpoints,
        },
        "units": {
            "corrected_samples_components_mass": "reference_signal",
            "response_profile_samples": "dimensionless",
            "frequency": "cycles/um",
            "phase": "rad",
            "localization": "normalized per-site weight",
        },
        "limits": [
            "Known phase/carrier/profile and finite per-site model; no instrument authentication.",
            "Accuracy uses independent represented-fit/native finite sums as truth.",
            "Cartesian interpolation is selected; continuous-optics/model error is separate.",
            "Distinct-grid detector queries do not establish a new reconstruction estimator.",
            "Common normalization removes bead brightness; original components/mass are retained.",
            "Metadata/units/IDs declare pairing; they do not authenticate physical compatibility.",
            "Installed runtime files are fingerprinted; generated pyc caches are excluded.",
            "Base/system dynamic-library graph is not a complete authenticated build inventory.",
        ],
    }
    np.savez_compressed(destination / "record-arrays.npz", **record_arrays)
    metadata["record_arrays_sha256"] = digest(destination / "record-arrays.npz")
    if metadata["source_inputs_before"] != metadata["source_inputs_after"]:
        raise ValueError("material source/input changed during generation")
    metadata["completed_unix_s"] = time.time()
    (destination / "observation.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: metadata[key]
                for key in (
                    "response_max_complex_error",
                    "response_allowance",
                    "sample_max_complex_error",
                    "sample_allowance",
                    "origin_zyx",
                    "raw_dc_peak_zyx",
                    "observed_mass_scale_ratio",
                )
            },
            indent=2,
        )
    )


def main():
    """Select a new local report-output directory and measure once."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    measure(arguments.destination.resolve())


if __name__ == "__main__":
    main()
