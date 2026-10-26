"""Exclusive, three-process noisy study protocol.

Generation alone sees acquisition truth. Inference consumes the public bundle;
evaluation validates the frozen public result before opening private truth.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import itertools
import json
import math
import platform
import re
import struct
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from decimal import ROUND_FLOOR, Decimal, localcontext
from functools import lru_cache
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
import scipy
from scripts.image_only_bead_calibration import fit_bead_calibration
from scripts.image_only_specimen_fit import fit_specimen
from scripts.simulation_camera import sample_camera
from scripts.simulation_inverse_operator import build_kernel_cache, forward
from scripts.simulation_optics import expected_images
from scripts.simulation_sources import make_sources

from simrecon import SimreconError, estimate_scalar_camera

D = (0.125, 0.080, 0.080)
OPTICS = dict(excitation_um=0.488, emission_um=0.525, refractive_index=1.515, detection_na=1.4)
ACQUISITION = dict(
    camera_law="scalar_poisson_gaussian",
    shot_noise=True,
    stationary_camera=True,
    common_dose=True,
    known_registration=True,
    pupil="clear_scalar_matched_index",
    **OPTICS,
    pixel_subsamples_yx=[2, 2],
)
NOMINAL = [0.0, *(k * math.pi / 5 for k in (2, 4, 6, 8, 1, 3, 7, 9))]
RAW = [f"specimen_o{o}_p{p}.npy" for o in range(3) for p in range(5)]
PRED = [f"prediction_o{o}_p{p}.npy" for o in range(3) for p in range(5)]
OBS = (
    [f"camera_{s}.npy" for s in ("dark", "blank", "flat")]
    + [f"calibration_{s}.npy" for s in ("central", "training", "heldout")]
    + RAW
)
TRUTH = (
    ["plan.json", "generation_summary.json", "bead_source_e.npy", "specimen_source_e.npy"]
    + [f"calibration_{s}_expected_signal_e.npy" for s in ("central", "training", "heldout")]
    + [s.replace(".npy", "_expected_signal_e.npy") for s in RAW]
)
RANGES = {
    "simulation_source_range",
    "simulation_optics_range",
    "simulation_camera_range",
    "scalar_camera_calibration_range",
    "image_only_bead_calibration_range",
    "image_only_calibration_pilot_range",
    "image_only_specimen_fit_range",
    "simulation_inverse_operator_range",
}
LIMITATIONS = [
    "conditional_clear_pupil_model",
    "finite_source_and_pixel_quadrature",
    "paired_axial_mass_aggregation",
    "finite_search_not_convergence",
    "possible_unprobed_or_ambiguous_parameters",
    "estimated_camera_gauge",
    "training_residual_not_heldout_validation",
    "no_recovery_accuracy_threshold",
    "procedural_truth_boundary_only",
]
COMPARISONS = [
    "camera_comparison",
    "source_metrics",
    "signal_prediction_metrics",
    "corrected_mean_prediction_metrics",
    "observed_residual_mean",
    "observed_residual_rms",
    "bead_permutation_comparisons",
    "illumination_gauge_comparisons",
]


class _Fault(Exception):
    """A classified CLI/protocol failure, without a completion claim."""

    def __init__(self, code: str, message: str, exit_code: int = 4, cause: str | None = None):
        super().__init__(message)
        self.code, self.exit_code, self.cause = code, exit_code, cause


def _invalid(message: str) -> NoReturn:
    raise _Fault("full_noisy_study_input_invalid", message)


def _require(condition: Any, message: str) -> None:
    if not condition:
        _invalid(message)


def _keys(value: Any, names: str) -> None:
    _require(type(value) is dict and set(value) == set(names.split()), f"exact keys: {names}")


def _integer(value: Any, minimum: int = 0) -> int:
    _require(type(value) is int and value >= minimum, "integer domain")
    return value


def _real(value: Any, *, positive: bool = False, nonnegative: bool = False) -> float:
    _require(type(value) in (int, float), "real scalar kind")
    try:
        result = float(value)
    except OverflowError:
        _invalid("float64 normalization overflow")
    _require(math.isfinite(result), "finite float64 required")
    _require(not positive or result > 0, "positive value required")
    _require(not nonnegative or result >= 0, "nonnegative value required")
    return result


def _text_value(value: Any) -> str:
    _require(type(value) is str and bool(value.strip()), "nonblank string required")
    return value


def _array(value: Any, shape: tuple[int, ...], kind: str = "real") -> Any:
    if not shape:
        if kind == "int":
            return _integer(value, 1)
        return _real(value, positive=kind == "positive", nonnegative=kind == "nonnegative")
    _require(type(value) is list and len(value) == shape[0], f"list shape {shape}")
    return [_array(v, shape[1:], kind) for v in value]


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _sha_value(value: Any) -> None:
    _require(type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None, "SHA-256")


def _json_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    _invalid(f"non-JSON constant {value}")


@contextmanager
def _json_integers() -> Iterator[None]:
    # JSON seeds/counts have no decimal-digit cap. Restore interpreter policy
    # even when parsing or an exclusive write fails. Commands are sequential.
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(0)
        yield
    finally:
        sys.set_int_max_str_digits(previous)


def _parse_json(raw: str | bytes) -> Any:
    try:
        with _json_integers():
            text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            return json.loads(text, object_pairs_hook=_json_pairs, parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        _invalid(f"invalid JSON: {exc}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        result = _parse_json(path.read_bytes())
    except FileNotFoundError as exc:
        raise _Fault("full_noisy_study_input_incomplete", str(path)) from exc
    _require(type(result) is dict, "JSON object required")
    return result


def _write_json(path: Path, value: Any) -> dict[str, Any]:
    with _json_integers(), path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(
            value,
            stream,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        stream.write("\n")
    return _descriptor(path)


def _descriptor(path: Path, data: Any = None) -> dict[str, Any]:
    result: dict[str, Any] = dict(
        path=path.name, size_bytes=path.stat().st_size, sha256=_digest(path)
    )
    if data is not None:
        result.update(dtype=data.dtype.str, shape=list(data.shape))
    return result


def _save_array(path: Path, data: Any, dtype: str = "<f8") -> dict[str, Any]:
    stored = np.asarray(data, dtype=dtype, order="C")
    _require(np.isfinite(stored).all(), "nonfinite output payload")
    with path.open("xb") as stream:
        np.save(stream, stored, allow_pickle=False)
    return _descriptor(path, stored)


def _claim(path: Path) -> None:
    # mkdir without parents also rejects dangling symlinks and existing empty roots.
    path.mkdir()


def _geometry(value: Any) -> dict[str, Any]:
    _keys(
        value,
        (
            "camera_shape_yx calibration_shape_zyx calibration_spacing_um_zyx "
            "calibration_origin_um_zyx specimen_shape_zyx "
            "specimen_spacing_um_zyx specimen_origin_um_zyx"
        ),
    )
    result = {"camera_shape_yx": _array(value["camera_shape_yx"], (2,), "int")}
    _require(math.prod(result["camera_shape_yx"]) >= 2, "camera needs two pixels")
    for prefix in ("calibration", "specimen"):
        result[prefix + "_shape_zyx"] = _array(value[prefix + "_shape_zyx"], (3,), "int")
        result[prefix + "_spacing_um_zyx"] = _array(
            value[prefix + "_spacing_um_zyx"], (3,), "positive"
        )
        result[prefix + "_origin_um_zyx"] = _array(value[prefix + "_origin_um_zyx"], (3,))
    _require(tuple(result["calibration_spacing_um_zyx"]) == D, "calibration spacing")
    with localcontext() as ctx:
        ctx.prec = 800
        _require(
            all(
                Decimal(n) * _dec(d) >= _dec(0.100)
                for n, d in zip(result["calibration_shape_zyx"], D, strict=True)
            ),
            "calibration box size",
        )
    return result


def _carriers(value: Any) -> Any:
    result = _array(value, (3, 2))
    with localcontext() as ctx:
        ctx.prec = 800
        limit = (_dec(1.515) / _dec(0.488)) ** 2
        _require(
            all(sum((_dec(v) ** 2 for v in row), Decimal(0)) <= limit for row in result),
            "carrier domain",
        )
    return result


def _beams(value: Any) -> Any:
    result = _array(value, (3,), "nonnegative")
    _require(any(v > 0 for v in result), "nonzero beams")
    return result


def _validate_plan(value: Any) -> dict[str, Any]:
    _keys(
        value,
        (
            "format_version geometry camera illumination bead_catalogue "
            "specimen_catalogue generator_pupil_order seeds"
        ),
    )
    _require(value["format_version"] == "full_noisy_study_plan_v1", "plan version")
    value["geometry"] = _geometry(value["geometry"])
    g = value["geometry"]
    c = value["camera"]
    _keys(c, "background_e read_noise_e gain_counts_per_e offset_counts flat_signal_e")
    for key in c:
        c[key] = _real(
            c[key],
            positive=key not in ("background_e", "offset_counts"),
            nonnegative=key == "background_e",
        )
    light = value["illumination"]
    _keys(light, "carriers_yx_per_um phases_at_calibration_origin_rad beam_amplitudes")
    light["carriers_yx_per_um"] = _carriers(light["carriers_yx_per_um"])
    light["phases_at_calibration_origin_rad"] = _array(
        light["phases_at_calibration_origin_rad"], (3, 9)
    )
    light["beam_amplitudes"] = _beams(light["beam_amplitudes"])
    _integer(value["generator_pupil_order"], 1)
    with localcontext() as ctx:
        ctx.prec = 800
        for name, prefix in (("bead_catalogue", "calibration"), ("specimen_catalogue", "specimen")):
            rows = value[name]
            _require(
                type(rows) is list and (name != "bead_catalogue" or len(rows) == 3),
                "catalogue rows",
            )
            rows = _array(rows, (len(rows), 5))
            lengths = [
                Decimal(n) * _dec(d)
                for n, d in zip(
                    g[prefix + "_shape_zyx"], g[prefix + "_spacing_um_zyx"], strict=True
                )
            ]
            for row in rows:
                radius = _dec(row[3])
                _require(radius > 0 and row[4] >= 0, "radius/brightness")
                _require(
                    all(
                        radius <= _dec(x) <= length - radius
                        for x, length in zip(row[:3], lengths, strict=True)
                    ),
                    "source containment",
                )
                if name == "bead_catalogue":
                    _require(row[3] == 0.050, "bead radius")
            if name == "bead_catalogue":
                for left, right in itertools.combinations(rows, 2):
                    _require(
                        sum(
                            (_dec(a) - _dec(b)) ** 2
                            for a, b in zip(left[:3], right[:3], strict=True)
                        )
                        >= (_dec(left[3]) + _dec(right[3])) ** 2,
                        "bead overlap",
                    )
            value[name] = rows
    seeds = value["seeds"]
    _keys(
        seeds,
        (
            "camera_dark camera_blank camera_flat calibration_central "
            "calibration_training calibration_heldout specimen"
        ),
    )
    flat: list[int] = []

    def seed_list(item: Any, shape: tuple[int, ...]) -> None:
        if not shape:
            flat.append(_integer(item))
            return
        _require(type(item) is list and len(item) == shape[0], "seed dimensions")
        for sub in item:
            seed_list(sub, shape[1:])

    for name in seeds:
        shape = (
            (8,)
            if name.startswith("camera_")
            else (
                ()
                if name == "calibration_central"
                else (3, 9 if name == "calibration_training" else 5)
            )
        )
        seed_list(seeds[name], shape)
    _require(len(flat) == 82 and len(set(flat)) == 82, "distinct seeds")
    return value


def _settings(value: Any) -> dict[str, Any]:
    _keys(value, "sweep_scales regularization max_iterations max_backtracking_trials pupil_order")
    scales = value["sweep_scales"]
    _require(type(scales) is list and bool(scales), "nonempty scales")
    return dict(
        sweep_scales=[_real(v, positive=True) for v in scales],
        regularization=_real(value["regularization"], positive=True),
        **{
            key: _integer(value[key], 1)
            for key in ("max_iterations", "max_backtracking_trials", "pupil_order")
        },
    )


def _runtime() -> dict[str, Any]:
    try:
        version = importlib.metadata.version("simrecon")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return dict(
        python_version=platform.python_version(),
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
        simrecon_version=version,
        platform=platform.platform(),
        byteorder=sys.byteorder,
        driver_sha256=_digest(Path(__file__)),
    )


def _dec(value: Any) -> Decimal:
    return Decimal.from_float(float(value))


@lru_cache(maxsize=1)
def _physical_pi() -> Decimal:
    # Chudnovsky, evaluated past the precision needed for all finite binary64
    # phases and origin products. Decimal avoids the rounded-2*pi period.
    with localcontext() as ctx:
        ctx.prec = 820
        m, series_term, x, k = 1, 13591409, 1, 6
        total = Decimal(series_term)
        for n in range(1, 60):
            m = m * (k**3 - 16 * k) // n**3
            series_term += 545140134
            x *= -262537412640768000
            total += Decimal(m * series_term) / Decimal(x)
            k += 12
        return +(426880 * Decimal(10005).sqrt() / total)


def _wrap(value: Decimal) -> float:
    pi = _physical_pi()
    reduced = value - ((value + pi) / (2 * pi)).to_integral_value(rounding=ROUND_FLOOR) * (2 * pi)
    result = float(reduced)
    return -math.pi if result >= math.pi else result


def _transfer(phases: Any, q: Any, origin: Any, destination: Any) -> Any:
    with localcontext() as ctx:
        ctx.prec = 800
        shift = [_dec(destination[i]) - _dec(origin[i]) for i in (1, 2)]
        return np.array(
            [
                [
                    _wrap(
                        _dec(phases[o][p])
                        + 2
                        * _physical_pi()
                        * sum((_dec(q[o][i]) * shift[i] for i in range(2)), Decimal(0))
                    )
                    for p in range(5)
                ]
                for o in range(3)
            ],
            dtype=np.float64,
        )


def _float_or_none(value: Decimal) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _source_mass(catalogue: Any, source: Any) -> dict[str, Any]:
    with localcontext() as ctx:
        ctx.prec = 800
        target = sum((_dec(row[4]) for row in catalogue), Decimal(0))
        # Chunk scaling keeps large positive storage sums available without
        # a per-cell Decimal loop on ordinary full-size sources.
        largest = float(np.max(source, initial=0))
        total = (
            Decimal(0)
            if largest == 0
            else _dec(largest)
            * _dec(
                math.fsum(
                    float(np.sum(block / largest, dtype=np.float64)) for block in _chunks(source)
                )
            )
        )
        values = dict(
            catalogue_total_e=target,
            stored_total_e=total,
            difference_e=total - target,
            relative_difference=None if target == 0 else (total - target) / target,
        )
        result: dict[str, Any] = {
            k: None if v is None else _float_or_none(v) for k, v in values.items()
        }
        result["unavailable_fields"] = [
            dict(field=k, reason="zero_reference" if v is None else "unrepresentable")
            for k, v in values.items()
            if result[k] is None
        ]
        return result


def _chunks(data: Any):
    flat = np.asarray(data).reshape(-1)
    for start in range(0, flat.size, 65536):
        yield flat[start : start + 65536]


def _generate(plan_path: Path, out: Path) -> int:
    try:
        plan = _validate_plan(_read_json(plan_path))
    except _Fault as exc:
        raise _Fault("invalid_full_noisy_study", str(exc), 2) from exc
    input_sha = _digest(plan_path)
    _claim(out)
    obs, truth = out / "observations", out / "private_truth"
    obs.mkdir()
    truth.mkdir()
    private_files = {"plan.json": _write_json(truth / "plan.json", plan)}
    public_files: dict[str, Any] = {}
    g, c, light, seeds = (plan[k] for k in ("geometry", "camera", "illumination", "seeds"))
    camera_kw = {k: c[k] for k in ("read_noise_e", "gain_counts_per_e", "offset_counts")}

    def sample(mean: Any, seed: int, background: float | None = None) -> Any:
        return sample_camera(
            mean,
            background_e=c["background_e"] if background is None else background,
            shot_noise=True,
            seed=seed,
            **camera_kw,
        )

    optics_kw = dict(
        **OPTICS, pupil_order=plan["generator_pupil_order"], pixel_subsamples_yx=(2, 2)
    )
    bead_source = make_sources(
        np.asarray(plan["bead_catalogue"], dtype=np.float64),
        detector_shape_zyx=tuple(g["calibration_shape_zyx"]),
        detector_spacing_um_zyx=D,
        source_refinement_zyx=(8, 8, 8),
    )
    private_files["bead_source_e.npy"] = _save_array(truth / "bead_source_e.npy", bead_source)
    masses = {"bead": _source_mass(plan["bead_catalogue"], bead_source)}
    central = expected_images(
        bead_source,
        detector_spacing_um_zyx=D,
        source_refinement_zyx=(8, 8, 8),
        carriers_yx_per_um=np.zeros((1, 2)),
        phases_rad=np.zeros((1, 1)),
        beam_amplitudes=(1.0, 0.0, 0.0),
        **optics_kw,
    )[0, 0]
    private_files["calibration_central_expected_signal_e.npy"] = _save_array(
        truth / "calibration_central_expected_signal_e.npy", central
    )
    public_files["calibration_central.npy"] = _save_array(
        obs / "calibration_central.npy", sample(central, seeds["calibration_central"])
    )
    del central
    training = expected_images(
        bead_source,
        detector_spacing_um_zyx=D,
        source_refinement_zyx=(8, 8, 8),
        carriers_yx_per_um=np.asarray(light["carriers_yx_per_um"], dtype=np.float64),
        phases_rad=np.asarray(light["phases_at_calibration_origin_rad"], dtype=np.float64),
        beam_amplitudes=tuple(light["beam_amplitudes"]),
        **optics_kw,
    )
    del bead_source
    for name, mean in (("training", training), ("heldout", training[:, :5])):
        filename = f"calibration_{name}_expected_signal_e.npy"
        private_files[filename] = _save_array(truth / filename, mean)
        raw = np.empty(mean.shape, dtype=np.float64)
        for o in range(3):
            for p in range(mean.shape[1]):
                raw[o, p] = sample(mean[o, p], seeds[f"calibration_{name}"][o][p])
        filename = f"calibration_{name}.npy"
        public_files[filename] = _save_array(obs / filename, raw)
    del training, mean, raw
    specimen = make_sources(
        np.asarray(plan["specimen_catalogue"], dtype=np.float64).reshape(-1, 5),
        detector_shape_zyx=tuple(g["specimen_shape_zyx"]),
        detector_spacing_um_zyx=tuple(g["specimen_spacing_um_zyx"]),
        source_refinement_zyx=(2, 2, 2),
    )
    private_files["specimen_source_e.npy"] = _save_array(truth / "specimen_source_e.npy", specimen)
    masses["specimen"] = _source_mass(plan["specimen_catalogue"], specimen)
    psi = _transfer(
        light["phases_at_calibration_origin_rad"],
        light["carriers_yx_per_um"],
        g["calibration_origin_um_zyx"],
        g["specimen_origin_um_zyx"],
    )
    for o in range(3):
        mean = expected_images(
            specimen,
            detector_spacing_um_zyx=tuple(g["specimen_spacing_um_zyx"]),
            source_refinement_zyx=(2, 2, 2),
            carriers_yx_per_um=np.asarray(light["carriers_yx_per_um"][o : o + 1], dtype=np.float64),
            phases_rad=psi[o : o + 1],
            beam_amplitudes=tuple(light["beam_amplitudes"]),
            **optics_kw,
        )[0]
        for p in range(5):
            name = f"specimen_o{o}_p{p}.npy"
            private_name = name.replace(".npy", "_expected_signal_e.npy")
            private_files[private_name] = _save_array(truth / private_name, mean[p])
            public_files[name] = _save_array(obs / name, sample(mean[p], seeds["specimen"][o][p]))
        del mean
    del specimen
    for name in ("dark", "blank", "flat"):
        signal = np.full(
            tuple(g["camera_shape_yx"]),
            c["flat_signal_e"] if name == "flat" else 0.0,
            dtype=np.float64,
        )
        group = np.empty((8, *signal.shape), dtype=np.float64)
        for i, seed in enumerate(seeds[f"camera_{name}"]):
            group[i] = sample(signal, seed, 0.0 if name == "dark" else c["background_e"])
        filename = f"camera_{name}.npy"
        public_files[filename] = _save_array(obs / filename, group)
    summary = dict(
        format_version="full_noisy_study_truth_v1",
        runtime=_runtime(),
        plan_input_sha256=input_sha,
        specimen_phases_at_specimen_origin_rad=psi.tolist(),
        source_model="closed_midpoint_total_normalized_catalogue_order",
        source_mass=masses,
    )
    private_files["generation_summary.json"] = _write_json(
        truth / "generation_summary.json", summary
    )
    observation = _write_json(
        obs / "complete.json",
        dict(
            format_version="full_noisy_study_observations_v1",
            geometry=g,
            acquisition_model=ACQUISITION,
            nominal_phase_commands_rad=NOMINAL,
            files=[public_files[n] for n in OBS],
        ),
    )
    private = _write_json(
        truth / "complete.json",
        dict(
            format_version="full_noisy_study_truth_v1",
            observation_manifest_sha256=observation["sha256"],
            files=[private_files[n] for n in TRUTH],
        ),
    )
    _write_json(
        out / "generation.complete.json",
        dict(
            format_version="full_noisy_study_generation_v1",
            status="generated",
            observation_manifest_sha256=observation["sha256"],
            private_truth_manifest_sha256=private["sha256"],
        ),
    )
    return 0


def _payload_shape(name: str, g: dict[str, Any]) -> tuple[int, ...]:
    nc, ns = tuple(g["calibration_shape_zyx"]), tuple(g["specimen_shape_zyx"])
    if name.startswith("camera_"):
        return (8, *g["camera_shape_yx"])
    if name == "bead_source_e.npy":
        return tuple(8 * n for n in nc)
    if name == "specimen_source_e.npy":
        return tuple(2 * n for n in ns)
    if name == "specimen_source_relative.npy":
        return (ns[0], 2 * ns[1], 2 * ns[2])
    if name == "bead_heldout_prediction.npy" or name.startswith("calibration_heldout"):
        return (3, 5, *nc)
    if name.startswith("calibration_training"):
        return (3, 9, *nc)
    if name.startswith("calibration_central"):
        return nc
    return ns


def _verify_descriptor(
    root: Path,
    item: Any,
    name: str,
    shape: tuple[int, ...] | None = None,
    *,
    nonnegative: bool = False,
) -> None:
    _keys(item, "path size_bytes sha256" + (" dtype shape" if shape is not None else ""))
    _require(item["path"] == name, "fixed payload path/order")
    _integer(item["size_bytes"])
    _sha_value(item["sha256"])
    path = root / name
    try:
        size = path.stat().st_size
        if size != item["size_bytes"] or _digest(path) != item["sha256"]:
            raise _Fault("full_noisy_study_integrity", f"payload identity: {name}")
        if shape is None:
            return
        dtype = "<f4" if name == "specimen_source_relative.npy" else "<f8"
        _require(item["dtype"] == dtype, "payload dtype descriptor")
        _array(item["shape"], (len(shape),), "int")
        _require(tuple(item["shape"]) == shape, "payload shape descriptor")
        # Inspect the DECLARED header order even for degenerate arrays that
        # would be both C- and Fortran-contiguous after loading.
        with path.open("rb") as stream:
            _require(stream.read(6) == b"\x93NUMPY", "NPY magic")
            version = tuple(stream.read(2))
            _require(version in ((1, 0), (2, 0), (3, 0)), "NPY version")
            width = 2 if version == (1, 0) else 4
            raw_length = stream.read(width)
            _require(len(raw_length) == width, "NPY length")
            length = struct.unpack("<H" if width == 2 else "<I", raw_length)[0]
            _require(length <= size - stream.tell(), "NPY incomplete header")
            header = ast.literal_eval(
                stream.read(length).decode("utf-8" if version == (3, 0) else "latin1")
            )
            _keys(header, "descr fortran_order shape")
            _require(
                header["descr"] == dtype and header["fortran_order"] is False, "NPY dtype/C header"
            )
            _require(
                type(header["shape"]) is tuple
                and all(type(n) is int for n in header["shape"])
                and header["shape"] == shape,
                "NPY declared shape",
            )
            _require(
                stream.tell() + math.prod(shape) * np.dtype(dtype).itemsize == size,
                "one complete NPY payload",
            )
        data = np.load(path, mmap_mode="r", allow_pickle=False)
        for block in _chunks(data):
            _require(
                np.isfinite(block).all() and (not nonnegative or (block >= 0).all()),
                "payload finite/domain",
            )
    except FileNotFoundError as exc:
        raise _Fault("full_noisy_study_input_incomplete", f"missing {name}") from exc
    except (ValueError, SyntaxError, UnicodeError, EOFError, struct.error) as exc:
        _invalid(f"NPY format {name}: {exc}")


def _verify_files(root: Path, items: Any, names: list[str], g: Any) -> None:
    _require(type(items) is list and len(items) == len(names), "payload list length")
    for item, name in zip(items, names, strict=True):
        _verify_descriptor(
            root,
            item,
            name,
            None if name.endswith(".json") else _payload_shape(name, g),
            nonnegative=(name.endswith("_e.npy") or name == "specimen_source_relative.npy"),
        )


def _observations(root: Path) -> tuple[dict[str, Any], str]:
    manifest = _read_json(root / "complete.json")
    _keys(manifest, "format_version geometry acquisition_model nominal_phase_commands_rad files")
    _require(
        manifest["format_version"] == "full_noisy_study_observations_v1", "observation version"
    )
    g = _geometry(manifest["geometry"])
    _keys(manifest["acquisition_model"], " ".join(ACQUISITION))
    for k, expected in ACQUISITION.items():
        actual = manifest["acquisition_model"][k]
        if type(expected) is bool:
            _require(actual is expected, "acquisition boolean")
        elif type(expected) is float:
            _require(_real(actual) == expected, "fixed optics")
        elif type(expected) is list:
            _require(_array(actual, (2,), "int") == expected, "pixel samples")
        else:
            _require(type(actual) is str and actual == expected, "acquisition label")
    _require(_array(manifest["nominal_phase_commands_rad"], (9,)) == NOMINAL, "nominal commands")
    _verify_files(root, manifest["files"], OBS, g)
    return g, _digest(root / "complete.json")


# Explicit public schemas. The serializer accepts only these named records;
# arrays outside the two declared large payload fields are small metadata.
SCHEMAS = {
    "ScalarCameraEstimate": (
        "means_counts variances_counts2 frame_means_counts "
        "frame_variances_counts2 empirical_mean_se_counts contrast_counts "
        "gain_counts_per_e information_codes source"
    ),
    "PilotCandidate": (
        "centers_um_zyx brightness_relative carriers_yx_per_um phases_rad "
        "beam_amplitudes occupied_counts stored_unit_masses_e"
    ),
    "BeadCalibrationScore": (
        "stage pupil_order coordinates candidate objective outcome failure_code"
    ),
    "BeadCalibrationAttempt": (
        "sweep_index coordinate_index sign base_score_index "
        "trial_coordinates coordinate_changed parameter_changed outcome "
        "infeasibility_reason score_index selected information_codes "
        "failure_code"
    ),
    "BeadCoordinateEvidence": (
        "coordinate_index attempt_count scored_count "
        "distinct_coordinate_scored_count distinct_parameter_scored_count "
        "selected_count information_codes"
    ),
    "BeadCalibrationCounts": (
        "planned_poll_attempts attempted_polls scored_polls "
        "infeasible_polls numerical_incomplete_polls completed_pairs "
        "completed_sweeps score_attempts successful_scores"
    ),
    "BeadCalibrationResult": (
        "status stage message failure_code detector_shape_zyx "
        "origin_um_zyx scipy_version camera_source blank_counts "
        "contrast_counts sweep_scales initialization_notes "
        "initial_candidate initial_coordinates best_candidate "
        "best_coordinates best_score_index incumbent_score_index "
        "frozen_candidate frozen_coordinates objective_trace poll_attempts"
        " coordinate_evidence unprobed_coordinates counts "
        "training_objectives_q128_q256_q512 heldout_prediction "
        "heldout_residual_mean heldout_residual_rms"
    ),
    "SpecimenScore": (
        "candidate_id data_objective penalty_objective total_objective residual_mean residual_rms"
    ),
    "SpecimenGradientSummary": "candidate_id max_abs",
    "SpecimenFitAttempt": (
        "candidate_id iteration trial from_candidate_id "
        "gradient_candidate_id step projected_gradient_max_abs outcome "
        "score gradient_state gradient"
    ),
    "SpecimenFitCall": "call_index operation purpose candidate_id orientation outcome failure_code",
    "SpecimenFitCounts": (
        "cache_attempted cache_completed cache_failed forward_attempted "
        "forward_completed forward_failed adjoint_attempted "
        "adjoint_completed adjoint_failed score_attempts scores_completed "
        "gradient_attempts gradients_completed seed_attempts "
        "seeds_completed iterations_started trials_attempted "
        "trials_accepted trials_rejected trials_unrepresentable "
        "trials_stagnated best_updates"
    ),
    "SpecimenFitResult": (
        "status stage stop_reason message failure_code failure_component "
        "detector_shape_zyx source_shape_zyx detector_spacing_um_zyx "
        "source_spacing_um_zyx specimen_origin_um_zyx excitation_um "
        "emission_um refractive_index detection_na pixel_samples_yx "
        "pupil_order regularization max_iterations max_backtracking_trials"
        " camera_means_counts blank_counts contrast_counts camera_source "
        "carriers_yx_per_um phases_at_specimen_origin_rad beam_amplitudes "
        "illumination_source source_relative initial_score best_score "
        "last_complete_gradient seed_step attempt_trace call_trace counts"
    ),
}


def _serialize(value: Any) -> Any:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        _require(math.isfinite(value), "finite record scalar")
        return value
    if type(value) is np.ndarray:
        _require(np.isfinite(value).all(), "finite record array")
        return value.tolist()
    if type(value) is tuple:
        return [_serialize(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        name = type(value).__name__
        _require(
            name in SCHEMAS and {f.name for f in fields(value)} == set(SCHEMAS[name].split()),
            "public record field set",
        )
        result = {}
        for f in fields(value):
            item = getattr(value, f.name)
            if f.name in ("source_relative", "heldout_prediction"):
                result[f.name] = (
                    None
                    if item is None
                    else {
                        "file": "specimen_source_relative.npy"
                        if f.name == "source_relative"
                        else "bead_heldout_prediction.npy"
                    }
                )
            else:
                result[f.name] = _serialize(item)
        return result
    _invalid("unexpected public record value")


def _infer(obs: Path, out: Path, algorithm: dict[str, Any]) -> int:
    g, obs_sha = _observations(obs)
    _claim(out)
    camera = bead = specimen = psi = None
    status, stage, message, failure = "unavailable", "camera", "camera estimation unavailable", None
    label = f"full_noisy_study:{obs_sha}"
    try:
        camera = estimate_scalar_camera(
            np.load(obs / "camera_dark.npy", allow_pickle=False),
            blank_counts=np.load(obs / "camera_blank.npy", allow_pickle=False),
            flat_counts=np.load(obs / "camera_flat.npy", allow_pickle=False),
            source=label + ":camera",
        )
        stage = "camera_normalization"
        if camera.contrast_counts <= 0:
            message = "camera contrast is nonpositive"
        else:
            stage = "bead"
            bead = fit_bead_calibration(
                np.load(obs / "calibration_central.npy", allow_pickle=False),
                structured_counts=np.load(obs / "calibration_training.npy", allow_pickle=False),
                heldout_counts=np.load(obs / "calibration_heldout.npy", allow_pickle=False),
                camera_estimate=camera,
                origin_um_zyx=tuple(g["calibration_origin_um_zyx"]),
                sweep_scales=tuple(algorithm["sweep_scales"]),
            )
            message, failure = bead.message, bead.failure_code
            if bead.status == "completed_finite_fit":
                _require(
                    bead.camera_source == camera.source
                    and bead.blank_counts == float(camera.means_counts[1])
                    and bead.contrast_counts == camera.contrast_counts,
                    "paired bead camera gauge",
                )
                candidate = bead.frozen_candidate
                if candidate is None:
                    _invalid("completed bead candidate")
                stage = "phase_transfer"
                psi = _transfer(
                    candidate.phases_rad,
                    candidate.carriers_yx_per_um,
                    g["calibration_origin_um_zyx"],
                    g["specimen_origin_um_zyx"],
                )
                stage = "specimen"
                raw = np.empty((3, 5, *g["specimen_shape_zyx"]), dtype=np.float64)
                for o in range(3):
                    for p in range(5):
                        raw[o, p] = np.load(obs / f"specimen_o{o}_p{p}.npy", allow_pickle=False)
                specimen = fit_specimen(
                    raw,
                    camera_estimate=camera,
                    carriers_yx_per_um=candidate.carriers_yx_per_um,
                    phases_at_specimen_origin_rad=psi,
                    beam_amplitudes=candidate.beam_amplitudes,
                    illumination_source=label + ":bead_finite47",
                    detector_spacing_um_zyx=tuple(g["specimen_spacing_um_zyx"]),
                    specimen_origin_um_zyx=tuple(g["specimen_origin_um_zyx"]),
                    **{
                        k: algorithm[k]
                        for k in (
                            "regularization",
                            "max_iterations",
                            "max_backtracking_trials",
                            "pupil_order",
                        )
                    },
                )
                del raw
                message, failure = specimen.message, specimen.failure_code
                if specimen.status == "completed_finite_fit":
                    status, stage = "completed_finite_fit", "complete"
    except SimreconError as exc:
        allowed = {
            "camera": {"scalar_camera_calibration_range"},
            "bead": {
                "image_only_bead_calibration_range",
                "image_only_calibration_pilot_range",
                "simulation_source_range",
                "simulation_optics_range",
            },
            "specimen": {"image_only_specimen_fit_range", "simulation_inverse_operator_range"},
        }
        if exc.code not in allowed.get(stage, set()):
            raise
        message, failure = str(exc), exc.code
    files_by_name: dict[str, Any] = {}
    if bead is not None and bead.heldout_prediction is not None:
        files_by_name["bead_heldout_prediction.npy"] = _save_array(
            out / "bead_heldout_prediction.npy", bead.heldout_prediction
        )
    if specimen is not None and specimen.source_relative is not None:
        files_by_name["specimen_source_relative.npy"] = _save_array(
            out / "specimen_source_relative.npy", specimen.source_relative, "<f4"
        )
    estimates = dict(
        format_version="full_noisy_study_estimates_v1",
        observation_manifest_sha256=obs_sha,
        algorithm_settings=algorithm,
        runtime=_runtime(),
        fit_status=status,
        fit_stage=stage,
        message=message,
        failure_code=failure,
        camera_estimate=_serialize(camera),
        bead_calibration=_serialize(bead),
        specimen_fit=_serialize(specimen),
        transferred_phases_at_specimen_origin_rad=None if psi is None else psi.tolist(),
    )
    files_by_name["estimates.json"] = _write_json(out / "estimates.json", estimates)
    counts = dict.fromkeys(
        [
            "cache_attempted",
            "cache_completed",
            "cache_failed",
            "forward_attempted",
            "forward_completed",
            "forward_failed",
        ],
        0,
    )
    if status == "completed_finite_fit":
        if specimen is None or specimen.source_relative is None:
            _invalid("completed source")
        stage = "prediction"
        try:
            counts["cache_attempted"] += 1
            try:
                cache = build_kernel_cache(
                    source_shape_zyx=specimen.source_shape_zyx,
                    source_spacing_um_zyx=specimen.source_spacing_um_zyx,
                    emission_um=specimen.emission_um,
                    refractive_index=specimen.refractive_index,
                    detection_na=specimen.detection_na,
                    pupil_order=specimen.pupil_order,
                )
            except SimreconError as exc:
                if exc.code == "simulation_inverse_operator_range":
                    counts["cache_failed"] += 1
                raise
            counts["cache_completed"] += 1
            for o in range(3):
                counts["forward_attempted"] += 1
                try:
                    prediction = forward(
                        specimen.source_relative,
                        kernel_cache=cache,
                        carrier_yx_per_um=np.asarray(
                            specimen.carriers_yx_per_um[o], dtype=np.float64
                        ),
                        phases_rad=np.asarray(
                            specimen.phases_at_specimen_origin_rad[o], dtype=np.float64
                        ),
                        beam_amplitudes=tuple(float(v) for v in specimen.beam_amplitudes),
                        excitation_um=specimen.excitation_um,
                    )
                except SimreconError as exc:
                    if exc.code == "simulation_inverse_operator_range":
                        counts["forward_failed"] += 1
                    raise
                counts["forward_completed"] += 1
                for p in range(5):
                    name = f"prediction_o{o}_p{p}.npy"
                    files_by_name[name] = _save_array(out / name, prediction[p])
                del prediction
            stage = "complete"
        except SimreconError as exc:
            if exc.code != "simulation_inverse_operator_range":
                raise
            status, message, failure = "unavailable", str(exc), exc.code
    order = ["estimates.json", "bead_heldout_prediction.npy", "specimen_source_relative.npy", *PRED]
    _write_json(
        out / "freeze.json",
        dict(
            format_version="full_noisy_study_freeze_v1",
            status=status,
            stage=stage,
            message=message,
            failure_code=failure,
            observation_manifest_sha256=obs_sha,
            files=[files_by_name[n] for n in order if n in files_by_name],
            prediction_call_counts=counts,
        ),
    )
    return 0 if status == "completed_finite_fit" else 3


def _choice(value: Any, options: str) -> None:
    _require(type(value) is str and value in options.split(), f"literal: {options}")


def _sequence(value: Any) -> list[Any]:
    _require(type(value) is list, "list required")
    return value


def _codes(value: Any, options: str) -> None:
    _sequence(value)
    _require(len(set(_text_value(v) for v in value)) == len(value), "unique codes")
    for item in value:
        _choice(item, options)


def _nullable_real(value: Any, *, nonnegative: bool = False, positive: bool = False) -> None:
    if value is not None:
        _real(value, positive=positive, nonnegative=nonnegative)


def _nullable_index(value: Any, length: int) -> None:
    if value is not None:
        _require(_integer(value) < length, "record index")


def _range_code(value: Any) -> None:
    _require(
        value is None or (type(value) is str and value in RANGES | {"full_noisy_study_range"}),
        "known range code",
    )


def _validate_runtime(value: Any) -> None:
    _keys(
        value,
        (
            "python_version numpy_version scipy_version simrecon_version "
            "platform byteorder driver_sha256"
        ),
    )
    for key in ("python_version", "numpy_version", "scipy_version", "simrecon_version", "platform"):
        if value[key] is not None:
            _text_value(value[key])
        else:
            _require(
                key in ("numpy_version", "scipy_version", "simrecon_version"),
                "required runtime string",
            )
    _choice(value["byteorder"], "little big")
    _sha_value(value["driver_sha256"])


def _record(value: Any, name: str) -> None:
    _keys(value, SCHEMAS[name])


def _validate_camera(value: Any, obs_sha: str) -> None:
    _record(value, "ScalarCameraEstimate")
    _array(value["means_counts"], (3,))
    for name in ("variances_counts2", "empirical_mean_se_counts"):
        _array(value[name], (3,), "nonnegative")
    _array(value["frame_means_counts"], (3, 8))
    _array(value["frame_variances_counts2"], (3, 8), "nonnegative")
    _real(value["contrast_counts"])
    _nullable_real(value["gain_counts_per_e"], positive=True)
    _require(value["source"] == f"full_noisy_study:{obs_sha}:camera", "camera source label")
    _codes(
        value["information_codes"],
        (
            "nonpositive_flat_contrast nonpositive_variance_contrast "
            "unrepresentable_gain negative_background_estimate"
        ),
    )
    with localcontext() as ctx:
        ctx.prec = 800
        means, variances = value["means_counts"], value["variances_counts2"]
        dm = _float_or_none(_dec(means[2]) - _dec(means[1]))
        dv = _float_or_none(_dec(variances[2]) - _dec(variances[1]))
        db = _float_or_none(_dec(means[1]) - _dec(means[0]))
        _require(dm is not None and dv is not None and db is not None, "camera returned contrasts")
        _require(value["contrast_counts"] == dm, "camera mean-contrast relation")
        expected_codes = []
        if dm is None or dv is None or db is None:
            _invalid("camera returned contrasts")
        if dm <= 0:
            expected_codes.append("nonpositive_flat_contrast")
        if dv <= 0:
            expected_codes.append("nonpositive_variance_contrast")
        gain = None
        if dm > 0 and dv > 0:
            gain = _float_or_none(_dec(dv) / _dec(dm))
            if gain is None or gain <= 0:
                gain = None
                expected_codes.append("unrepresentable_gain")
        if db < 0:
            expected_codes.append("negative_background_estimate")
        _require(
            value["gain_counts_per_e"] == gain and value["information_codes"] == expected_codes,
            "camera returned gain/information relations",
        )


def _validate_candidate(value: Any, g: Any) -> None:
    _record(value, "PilotCandidate")
    centers = _array(value["centers_um_zyx"], (3, 3))
    _array(value["brightness_relative"], (3,), "nonnegative")
    _carriers(value["carriers_yx_per_um"])
    _array(value["phases_rad"], (3, 9))
    _beams(value["beam_amplitudes"])
    _array(value["occupied_counts"], (3,), "int")
    _array(value["stored_unit_masses_e"], (3,), "nonnegative")
    with localcontext() as ctx:
        ctx.prec = 800
        lengths = [Decimal(n) * _dec(d) for n, d in zip(g["calibration_shape_zyx"], D, strict=True)]
        r = _dec(0.050)
        for row in centers:
            _require(
                all(r <= _dec(v) <= length - r for v, length in zip(row, lengths, strict=True)),
                "candidate containment",
            )
        for a, b in itertools.combinations(centers, 2):
            _require(
                sum((_dec(x) - _dec(y)) ** 2 for x, y in zip(a, b, strict=True)) >= (2 * r) ** 2,
                "candidate nonoverlap",
            )


BEAD_CODES = (
    "unchanged_coordinate unchanged_parameter "
    "occupancy_equivalent_center zero_brightness_center "
    "zero_carrier_angle single_beam_illumination zero_total_brightness"
    " equal_computed_objective"
)


def _validate_bead(value: Any, g: Any, camera: Any, algorithm: Any) -> None:
    _record(value, "BeadCalibrationResult")
    _choice(
        value["status"],
        (
            "completed_finite_fit normalization_unavailable "
            "initialization_failed numerical_incomplete"
        ),
    )
    _choice(
        value["stage"],
        (
            "normalization initialization initial poll refinement_q256 "
            "refinement_q512 heldout_prediction heldout_residual complete"
        ),
    )
    _text_value(value["message"])
    _text_value(value["scipy_version"])
    _range_code(value["failure_code"])
    _require(
        (value["status"] == "numerical_incomplete") == (value["failure_code"] is not None),
        "bead failure status",
    )
    _require(
        _array(value["detector_shape_zyx"], (3,), "int") == g["calibration_shape_zyx"],
        "bead geometry",
    )
    _require(_array(value["origin_um_zyx"], (3,)) == g["calibration_origin_um_zyx"], "bead origin")
    _require(
        value["camera_source"] == camera["source"]
        and _real(value["blank_counts"]) == camera["means_counts"][1]
        and _real(value["contrast_counts"]) == camera["contrast_counts"],
        "paired bead gauge",
    )
    _require(_sequence(value["sweep_scales"]) == algorithm["sweep_scales"], "bead scales")
    if value["initialization_notes"] is not None:
        _text_value(value["initialization_notes"])
    for prefix in ("initial", "best", "frozen"):
        candidate, coordinates = value[prefix + "_candidate"], value[prefix + "_coordinates"]
        _require((candidate is None) == (coordinates is None), "candidate/coordinate presence")
        if candidate is not None:
            _validate_candidate(candidate, g)
            _array(coordinates, (47,))
    scores = _sequence(value["objective_trace"])
    for score in scores:
        _record(score, "BeadCalibrationScore")
        _choice(score["stage"], "initial poll refinement")
        _require(_integer(score["pupil_order"], 1) in (128, 256, 512), "bead score quadrature")
        _require(
            (score["stage"] == "refinement") == (score["pupil_order"] != 128), "score stage/order"
        )
        if score["coordinates"] is not None:
            _array(score["coordinates"], (47,))
        _choice(score["outcome"], "scored numerical_incomplete")
        _range_code(score["failure_code"])
        if score["outcome"] == "scored":
            _validate_candidate(score["candidate"], g)
            _array(score["coordinates"], (47,))
            _real(score["objective"], nonnegative=True)
            _require(score["failure_code"] is None, "successful score failure")
        else:
            _require(
                score["candidate"] is None
                and score["objective"] is None
                and score["failure_code"] is not None,
                "failed bead score",
            )
    for key in ("best_score_index", "incumbent_score_index"):
        _nullable_index(value[key], len(scores))
        if value[key] is not None:
            _require(
                scores[value[key]]["outcome"] == "scored"
                and scores[value[key]]["pupil_order"] == 128,
                "Q128 score index",
            )
    if value["best_score_index"] is not None:
        best = scores[value["best_score_index"]]
        _require(
            value["best_candidate"] == best["candidate"]
            and value["best_coordinates"] == best["coordinates"],
            "best snapshot relation",
        )
        eligible = [
            (s["objective"], i)
            for i, s in enumerate(scores)
            if s["outcome"] == "scored" and s["pupil_order"] == 128
        ]
        _require(min(eligible)[1] == value["best_score_index"], "best chronological score")
    else:
        _require(value["best_candidate"] is None, "absent best score")
    polls = _sequence(value["poll_attempts"])
    _require(len(polls) <= 94 * len(algorithm["sweep_scales"]), "poll schedule bound")
    for index, poll in enumerate(polls):
        _record(poll, "BeadCalibrationAttempt")
        for key in ("sweep_index", "coordinate_index", "base_score_index"):
            _integer(poll[key])
        _require(
            (poll["sweep_index"], poll["coordinate_index"], poll["sign"])
            == (index // 94, index // 2 % 47, -1 if index % 2 == 0 else 1)
            and type(poll["sign"]) is int,
            "ordered complete coordinate polls",
        )
        _nullable_index(poll["base_score_index"], len(scores))
        _require(scores[poll["base_score_index"]]["outcome"] == "scored", "poll base score")
        if poll["trial_coordinates"] is not None:
            _array(poll["trial_coordinates"], (47,))
        for flag in ("coordinate_changed", "parameter_changed", "selected"):
            _require(poll[flag] is None or type(poll[flag]) is bool, "poll flag")
        _choice(poll["outcome"], "scored infeasible numerical_incomplete")
        _nullable_index(poll["score_index"], len(scores))
        _range_code(poll["failure_code"])
        _codes(poll["information_codes"], BEAD_CODES)
        if poll["outcome"] == "scored":
            _require(
                poll["score_index"] is not None
                and poll["coordinate_changed"] is not None
                and poll["parameter_changed"] is not None
                and poll["failure_code"] is None
                and poll["infeasibility_reason"] is None,
                "scored poll fields",
            )
            score = scores[poll["score_index"]]
            _require(
                score["outcome"] == "scored"
                and score["stage"] == "poll"
                and score["coordinates"] == poll["trial_coordinates"],
                "poll score relation",
            )
        elif poll["outcome"] == "infeasible":
            _choice(
                poll["infeasibility_reason"], "coordinate_bounds center_geometry carrier_domain"
            )
            _require(
                poll["score_index"] is None
                and poll["parameter_changed"] is None
                and poll["failure_code"] is None
                and not poll["information_codes"],
                "infeasible poll fields",
            )
        else:
            _require(
                poll["failure_code"] is not None and poll["selected"] is None,
                "incomplete poll fields",
            )
    completed_pairs = sum(
        all(p["selected"] is not None for p in polls[i : i + 2])
        for i in range(0, len(polls) - 1, 2)
    )
    for i in range(completed_pairs):
        pair = polls[2 * i : 2 * i + 2]
        _require(
            sum(p["selected"] is True for p in pair) <= 1
            and pair[0]["base_score_index"] == pair[1]["base_score_index"],
            "paired selection",
        )
    evidence = _sequence(value["coordinate_evidence"])
    _require(len(evidence) == 47, "47 coordinate evidence rows")
    for index, e in enumerate(evidence):
        _record(e, "BeadCoordinateEvidence")
        _require(_integer(e["coordinate_index"]) == index, "evidence order")
        own = [p for p in polls if p["coordinate_index"] == index]
        expected = dict(
            attempt_count=len(own),
            scored_count=sum(p["outcome"] == "scored" for p in own),
            distinct_coordinate_scored_count=sum(
                p["outcome"] == "scored" and p["coordinate_changed"] is True for p in own
            ),
            distinct_parameter_scored_count=sum(
                p["outcome"] == "scored" and p["parameter_changed"] is True for p in own
            ),
            selected_count=sum(p["selected"] is True for p in own),
        )
        for key, count in expected.items():
            _require(_integer(e[key]) == count, "coordinate evidence count")
        _codes(e["information_codes"], BEAD_CODES)
        union = {code for p in own if p["outcome"] == "scored" for code in p["information_codes"]}
        _require(
            e["information_codes"] == [code for code in BEAD_CODES.split() if code in union],
            "coordinate code union",
        )
    unprobed = _sequence(value["unprobed_coordinates"])
    for i in unprobed:
        _integer(i)
    _require(
        unprobed
        == [e["coordinate_index"] for e in evidence if e["distinct_parameter_scored_count"] == 0],
        "unprobed coordinates",
    )
    count = value["counts"]
    _record(count, "BeadCalibrationCounts")
    expected_counts = dict(
        planned_poll_attempts=94 * len(algorithm["sweep_scales"]),
        attempted_polls=len(polls),
        scored_polls=sum(p["outcome"] == "scored" for p in polls),
        infeasible_polls=sum(p["outcome"] == "infeasible" for p in polls),
        numerical_incomplete_polls=sum(p["outcome"] == "numerical_incomplete" for p in polls),
        completed_pairs=completed_pairs,
        completed_sweeps=completed_pairs // 47,
        score_attempts=len(scores),
        successful_scores=sum(s["outcome"] == "scored" for s in scores),
    )
    for key, count_expected in expected_counts.items():
        _require(_integer(count[key]) == count_expected, "bead ledger counter")
    objectives = _sequence(value["training_objectives_q128_q256_q512"])
    _require(len(objectives) == 3, "three refinement objectives")
    for objective in objectives:
        _nullable_real(objective, nonnegative=True)
    if value["best_score_index"] is not None:
        _require(
            objectives[0] == scores[value["best_score_index"]]["objective"], "best Q128 objective"
        )
    _require(
        (value["heldout_residual_mean"] is None) == (value["heldout_residual_rms"] is None),
        "paired heldout summaries",
    )
    if value["heldout_residual_mean"] is not None:
        _array(value["heldout_residual_mean"], (3, 5))
        _array(value["heldout_residual_rms"], (3, 5), "nonnegative")
        _require(value["heldout_prediction"] is not None, "heldout summary prediction")
    _payload_reference(value["heldout_prediction"], "bead_heldout_prediction.npy")
    if value["status"] == "completed_finite_fit":
        _require(
            value["stage"] == "complete"
            and value["frozen_candidate"] is not None
            and len(polls) == count["planned_poll_attempts"]
            and completed_pairs == 47 * len(algorithm["sweep_scales"])
            and all(v is not None for v in objectives)
            and value["heldout_prediction"] is not None
            and value["heldout_residual_mean"] is not None,
            "completed bead obligations",
        )
    elif value["status"] in ("normalization_unavailable", "initialization_failed"):
        _require(
            value["stage"]
            == (
                "normalization"
                if value["status"] == "normalization_unavailable"
                else "initialization"
            )
            and not scores
            and not polls
            and value["initial_candidate"] is None
            and value["frozen_candidate"] is None,
            "unavailable bead record",
        )


def _payload_reference(value: Any, name: str) -> None:
    if value is not None:
        _keys(value, "file")
        _require(value["file"] == name, "fixed payload reference")


def _validate_score(value: Any) -> None:
    _record(value, "SpecimenScore")
    _integer(value["candidate_id"])
    for key in ("data_objective", "penalty_objective", "total_objective"):
        _real(value[key], nonnegative=True)
    _require(
        value["total_objective"] == value["data_objective"] + value["penalty_objective"],
        "total objective relation",
    )
    _array(value["residual_mean"], (3, 5))
    _array(value["residual_rms"], (3, 5), "nonnegative")


def _validate_gradient(value: Any) -> None:
    _record(value, "SpecimenGradientSummary")
    _integer(value["candidate_id"])
    _real(value["max_abs"], nonnegative=True)


def _validate_specimen(
    value: Any, g: Any, camera: Any, bead: Any, psi: Any, algorithm: Any, obs_sha: str
) -> None:
    _record(value, "SpecimenFitResult")
    _choice(value["status"], "completed_finite_fit normalization_unavailable numerical_incomplete")
    _choice(
        value["stage"],
        (
            "complete normalization geometry kernel_cache initial_score "
            "initial_gradient curvature_seed trial_score trial_gradient "
            "backtracking_step"
        ),
    )
    _text_value(value["message"])
    _range_code(value["failure_code"])
    _require(
        (value["status"] == "numerical_incomplete") == (value["failure_code"] is not None),
        "specimen failure status",
    )
    if value["failure_component"] is not None:
        _choice(
            value["failure_component"],
            (
                "source_geometry observations residual penalty_objective "
                "data_objective total_objective residual_mean residual_rms "
                "residual32 gradient seed_step step dependency"
            ),
        )
    _require(
        _array(value["detector_shape_zyx"], (3,), "int") == g["specimen_shape_zyx"],
        "specimen detector shape",
    )
    ns = g["specimen_shape_zyx"]
    _require(
        _array(value["source_shape_zyx"], (3,), "int") == [ns[0], 2 * ns[1], 2 * ns[2]],
        "specimen source shape",
    )
    _require(
        _array(value["detector_spacing_um_zyx"], (3,), "positive") == g["specimen_spacing_um_zyx"],
        "specimen spacing",
    )
    if value["source_spacing_um_zyx"] is not None:
        _require(
            _array(value["source_spacing_um_zyx"], (3,), "positive")
            == [v if i == 0 else v / 2 for i, v in enumerate(g["specimen_spacing_um_zyx"])],
            "source basis spacing",
        )
    if value["stage"] not in ("normalization", "geometry"):
        _require(value["source_spacing_um_zyx"] is not None, "derived source spacing")
    _require(
        _array(value["specimen_origin_um_zyx"], (3,)) == g["specimen_origin_um_zyx"],
        "specimen origin",
    )
    for key, fixed in OPTICS.items():
        _require(_real(value[key]) == fixed, "specimen fixed optics")
    _require(_array(value["pixel_samples_yx"], (2,), "int") == [2, 2], "specimen pixels")
    for key in ("regularization", "pupil_order", "max_iterations", "max_backtracking_trials"):
        normalized = (
            _real(value[key], positive=True) if key == "regularization" else _integer(value[key], 1)
        )
        _require(normalized == algorithm[key], "retained algorithm setting")
    _require(
        _array(value["camera_means_counts"], (3,)) == camera["means_counts"]
        and _real(value["blank_counts"]) == camera["means_counts"][1]
        and _real(value["contrast_counts"]) == camera["contrast_counts"]
        and value["camera_source"] == camera["source"],
        "paired specimen camera gauge",
    )
    candidate = bead["frozen_candidate"]
    _require(
        _carriers(value["carriers_yx_per_um"]) == candidate["carriers_yx_per_um"]
        and _beams(value["beam_amplitudes"]) == candidate["beam_amplitudes"]
        and _array(value["phases_at_specimen_origin_rad"], (3, 5)) == psi,
        "retained estimated illumination",
    )
    _require(
        value["illumination_source"] == f"full_noisy_study:{obs_sha}:bead_finite47",
        "specimen illumination label",
    )
    _payload_reference(value["source_relative"], "specimen_source_relative.npy")
    _nullable_real(value["seed_step"], positive=True)
    attempts = _sequence(value["attempt_trace"])
    for index, attempt in enumerate(attempts):
        _record(attempt, "SpecimenFitAttempt")
        _require(_integer(attempt["candidate_id"]) == index, "candidate ID order")
        _integer(attempt["iteration"])
        _integer(attempt["trial"])
        _choice(
            attempt["outcome"],
            "initial_scored accepted rejected unrepresentable stagnated score_incomplete",
        )
        _choice(attempt["gradient_state"], "complete incomplete not_needed")
        if index == 0:
            _require(
                attempt["iteration"] == attempt["trial"] == 0
                and all(
                    attempt[k] is None
                    for k in (
                        "from_candidate_id",
                        "gradient_candidate_id",
                        "step",
                        "projected_gradient_max_abs",
                    )
                ),
                "initial attempt metadata",
            )
        else:
            _require(
                _integer(attempt["iteration"], 1) <= algorithm["max_iterations"]
                and _integer(attempt["trial"], 1) <= algorithm["max_backtracking_trials"],
                "trial settings bounds",
            )
            _require(
                _integer(attempt["from_candidate_id"]) < index
                and attempt["from_candidate_id"] == attempt["gradient_candidate_id"]
                and type(attempt["gradient_candidate_id"]) is int,
                "trial incumbent IDs",
            )
            _real(attempt["step"], positive=True)
            _real(attempt["projected_gradient_max_abs"], nonnegative=True)
        scored = attempt["outcome"] in ("initial_scored", "accepted", "rejected")
        _require(scored == (attempt["score"] is not None), "attempt score presence")
        if scored:
            _validate_score(attempt["score"])
            _require(attempt["score"]["candidate_id"] == index, "attempt score identity")
        _require(
            (attempt["gradient_state"] == "complete") == (attempt["gradient"] is not None),
            "gradient completion",
        )
        if attempt["gradient"] is not None:
            _validate_gradient(attempt["gradient"])
            _require(attempt["gradient"]["candidate_id"] == index, "gradient candidate identity")
    for field in ("initial_score", "best_score"):
        score = value[field]
        if score is not None:
            _validate_score(score)
            _require(
                score["candidate_id"] < len(attempts)
                and attempts[score["candidate_id"]]["score"] == score,
                "retained score identity",
            )
            if field == "initial_score":
                _require(score["candidate_id"] == 0, "initial score ID")
    winners = [a["score"] for a in attempts if a["outcome"] in ("initial_scored", "accepted")]
    _require(value["best_score"] == (winners[-1] if winners else None), "returned best score")
    _require(
        (value["source_relative"] is None) == (value["best_score"] is None), "source/score presence"
    )
    if value["last_complete_gradient"] is not None:
        _validate_gradient(value["last_complete_gradient"])
        gradients = [a["gradient"] for a in attempts if a["gradient"] is not None]
        _require(
            bool(gradients) and value["last_complete_gradient"] == gradients[-1],
            "last complete gradient identity",
        )
    calls = _sequence(value["call_trace"])
    for index, call in enumerate(calls):
        _record(call, "SpecimenFitCall")
        _require(_integer(call["call_index"], 1) == index + 1, "call index order")
        _choice(call["operation"], "build_kernel_cache forward adjoint")
        _choice(call["purpose"], "cache score gradient curvature_seed")
        _choice(call["outcome"], "completed range_failure")
        _require(
            call["failure_code"]
            == (None if call["outcome"] == "completed" else "simulation_inverse_operator_range"),
            "call failure relation",
        )
        if call["operation"] == "build_kernel_cache":
            _require(
                call["purpose"] == "cache"
                and call["candidate_id"] is None
                and call["orientation"] is None,
                "cache call metadata",
            )
        else:
            _require(
                _integer(call["orientation"]) < 3
                and _integer(call["candidate_id"]) < len(attempts),
                "call orientation/candidate",
            )
    count = value["counts"]
    _record(count, "SpecimenFitCounts")
    for key in count:
        _integer(count[key])
    for prefix, operation in (
        ("cache", "build_kernel_cache"),
        ("forward", "forward"),
        ("adjoint", "adjoint"),
    ):
        own = [c for c in calls if c["operation"] == operation]
        _require(
            count[prefix + "_attempted"] == len(own)
            and count[prefix + "_completed"] == sum(c["outcome"] == "completed" for c in own)
            and count[prefix + "_failed"] == sum(c["outcome"] == "range_failure" for c in own),
            "specimen call counts",
        )
    expected = dict(
        score_attempts=sum(
            a["outcome"] in ("initial_scored", "accepted", "rejected", "score_incomplete")
            for a in attempts
        ),
        scores_completed=sum(a["score"] is not None for a in attempts),
        gradient_attempts=sum(a["gradient_state"] != "not_needed" for a in attempts),
        gradients_completed=sum(a["gradient_state"] == "complete" for a in attempts),
        seed_attempts=int(value["seed_step"] is not None or value["stage"] == "curvature_seed"),
        seeds_completed=int(value["seed_step"] is not None),
        iterations_started=len({a["iteration"] for a in attempts if a["candidate_id"] != 0}),
        trials_attempted=max(0, len(attempts) - 1),
        best_updates=len(winners),
    )
    for outcome in ("accepted", "rejected", "unrepresentable", "stagnated"):
        expected["trials_" + outcome] = sum(a["outcome"] == outcome for a in attempts)
    for key, n in expected.items():
        _require(count[key] == n, "specimen derived ledger counter")
    if value["status"] == "completed_finite_fit":
        _require(
            value["stage"] == "complete"
            and value["source_relative"] is not None
            and value["initial_score"] is not None
            and value["failure_component"] is None,
            "completed specimen obligations",
        )
        _choice(
            value["stop_reason"],
            "no_projected_direction float32_stagnation backtracking_limit iteration_limit",
        )
    else:
        _require(value["stop_reason"] is None, "incomplete stop reason")


def _validate_inference(root: Path, g: Any, obs_sha: str) -> tuple[Any, Any, str]:
    freeze = _read_json(root / "freeze.json")
    _keys(
        freeze,
        (
            "format_version status stage message failure_code "
            "observation_manifest_sha256 files prediction_call_counts"
        ),
    )
    _require(
        freeze["format_version"] == "full_noisy_study_freeze_v1"
        and freeze["observation_manifest_sha256"] == obs_sha,
        "freeze identity",
    )
    _choice(freeze["status"], "completed_finite_fit unavailable")
    _choice(
        freeze["stage"],
        "complete camera camera_normalization bead phase_transfer specimen prediction",
    )
    _text_value(freeze["message"])
    _range_code(freeze["failure_code"])
    items = _sequence(freeze["files"])
    _require(bool(items), "estimates descriptor required")
    _verify_descriptor(root, items[0], "estimates.json")
    estimates = _read_json(root / "estimates.json")
    _keys(
        estimates,
        (
            "format_version observation_manifest_sha256 algorithm_settings "
            "runtime fit_status fit_stage message failure_code camera_estimate"
            " bead_calibration specimen_fit "
            "transferred_phases_at_specimen_origin_rad"
        ),
    )
    _require(
        estimates["format_version"] == "full_noisy_study_estimates_v1"
        and estimates["observation_manifest_sha256"] == obs_sha,
        "estimates identity",
    )
    algorithm = _settings(estimates["algorithm_settings"])
    _validate_runtime(estimates["runtime"])
    _choice(estimates["fit_status"], "completed_finite_fit unavailable")
    _choice(
        estimates["fit_stage"], "complete camera camera_normalization bead phase_transfer specimen"
    )
    _text_value(estimates["message"])
    _range_code(estimates["failure_code"])
    camera, bead, specimen, psi = (
        estimates[k]
        for k in (
            "camera_estimate",
            "bead_calibration",
            "specimen_fit",
            "transferred_phases_at_specimen_origin_rad",
        )
    )
    if camera is not None:
        _validate_camera(camera, obs_sha)
    if bead is not None:
        _require(
            camera is not None and camera["contrast_counts"] > 0, "bead requires positive camera"
        )
        _validate_bead(bead, g, camera, algorithm)
    if psi is not None:
        if not isinstance(bead, dict):
            _invalid("transfer needs complete bead")
        _array(psi, (3, 5))
        _require(
            bead is not None and bead["status"] == "completed_finite_fit",
            "transfer needs complete bead",
        )
        frozen: Any = bead["frozen_candidate"]
        expected = _transfer(
            frozen["phases_rad"],
            frozen["carriers_yx_per_um"],
            g["calibration_origin_um_zyx"],
            g["specimen_origin_um_zyx"],
        ).tolist()
        _require(
            np.allclose(psi, expected, rtol=0, atol=128 * np.finfo(float).eps),
            "once transferred phase metadata",
        )
    if specimen is not None:
        _require(
            psi is not None and bead is not None and camera is not None, "specimen prerequisites"
        )
        _validate_specimen(specimen, g, camera, bead, psi, algorithm, obs_sha)
    if estimates["fit_status"] == "completed_finite_fit":
        _require(
            estimates["fit_stage"] == "complete"
            and estimates["failure_code"] is None
            and specimen is not None
            and specimen["status"] == "completed_finite_fit",
            "completed fit obligations",
        )
    else:
        _require(estimates["fit_stage"] != "complete", "unavailable fit stage")
    stage = estimates["fit_stage"]
    if stage in ("camera", "camera_normalization"):
        _require(bead is None and specimen is None and psi is None, "unentered fit records")
        if stage == "camera":
            _require(
                camera is None and estimates["failure_code"] == "scalar_camera_calibration_range",
                "camera failure record",
            )
        else:
            _require(
                camera is not None
                and camera["contrast_counts"] <= 0
                and estimates["failure_code"] is None,
                "unavailable camera normalization",
            )
    elif stage == "bead":
        _require(
            camera is not None and specimen is None and psi is None, "bead-stage prerequisites"
        )
        if bead is not None:
            _require(
                bead["status"] != "completed_finite_fit"
                and estimates["failure_code"] == bead["failure_code"],
                "bead unavailable status/code",
            )
        else:
            _require(estimates["failure_code"] in RANGES, "bead raised range")
    elif stage in ("phase_transfer", "specimen", "complete"):
        _require(
            bead is not None and bead["status"] == "completed_finite_fit",
            "completed bead prerequisite",
        )
        if stage == "phase_transfer":
            _require(
                specimen is None
                and psi is None
                and estimates["failure_code"] == "full_noisy_study_range",
                "phase-transfer failure",
            )
        elif stage == "specimen":
            _require(psi is not None, "specimen transfer prerequisite")
            if specimen is not None:
                _require(
                    specimen["status"] != "completed_finite_fit"
                    and estimates["failure_code"] == specimen["failure_code"],
                    "specimen unavailable status/code",
                )
            else:
                _require(estimates["failure_code"] in RANGES, "specimen raised range")
    if freeze["stage"] != "prediction":
        _require(
            freeze["status"] == estimates["fit_status"]
            and freeze["stage"] == estimates["fit_stage"]
            and freeze["failure_code"] == estimates["failure_code"],
            "fit/freeze relation",
        )
    else:
        _require(
            freeze["status"] == "unavailable"
            and estimates["fit_status"] == "completed_finite_fit"
            and freeze["failure_code"] == "simulation_inverse_operator_range",
            "prediction failure relation",
        )
    names = ["estimates.json"]
    if bead is not None and bead["heldout_prediction"] is not None:
        names.append("bead_heldout_prediction.npy")
    if specimen is not None and specimen["source_relative"] is not None:
        names.append("specimen_source_relative.npy")
    counts = freeze["prediction_call_counts"]
    _keys(
        counts,
        (
            "cache_attempted cache_completed cache_failed forward_attempted "
            "forward_completed forward_failed"
        ),
    )
    for key in counts:
        _integer(counts[key])
    _require(
        counts["cache_attempted"] == counts["cache_completed"] + counts["cache_failed"] <= 1
        and counts["forward_attempted"]
        == counts["forward_completed"] + counts["forward_failed"]
        <= 3,
        "prediction call accounting",
    )
    exported = len(items) - len(names)
    _require(
        0 <= exported <= 15 and exported <= 5 * counts["forward_completed"],
        "prediction export count",
    )
    names += PRED[:exported]
    if freeze["status"] == "completed_finite_fit":
        _require(
            freeze["stage"] == "complete" and exported == 15,
            "completed freeze",
        )
        _require(
            counts
            == dict(
                cache_attempted=1,
                cache_completed=1,
                cache_failed=0,
                forward_attempted=3,
                forward_completed=3,
                forward_failed=0,
            ),
            "completed prediction counts",
        )
    elif freeze["stage"] != "prediction":
        _require(not any(counts.values()) and exported == 0, "unentered prediction counts")
    else:
        _require(
            exported == 5 * counts["forward_completed"]
            and counts["cache_failed"] + counts["forward_failed"] == 1,
            "failed prediction counts",
        )
    _verify_files(root, items, names, g)
    return estimates, freeze, _digest(root / "freeze.json")


def _validate_unavailable(value: Any, fields_allowed: list[str], reasons: str) -> None:
    seen: set[str] = set()
    for item in _sequence(value):
        _keys(item, "field reason")
        _require(item["field"] in fields_allowed and item["field"] not in seen, "unavailable field")
        seen.add(item["field"])
        _choice(item["reason"], reasons)


def _validate_truth(root: Path, g: Any, obs_sha: str) -> tuple[Any, str]:
    manifest = _read_json(root / "complete.json")
    _keys(manifest, "format_version observation_manifest_sha256 files")
    _require(
        manifest["format_version"] == "full_noisy_study_truth_v1"
        and manifest["observation_manifest_sha256"] == obs_sha,
        "truth manifest identity",
    )
    _verify_files(root, manifest["files"], TRUTH, g)
    plan = _validate_plan(_read_json(root / "plan.json"))
    _require(plan["geometry"] == g, "private/public geometry agreement")
    summary = _read_json(root / "generation_summary.json")
    _keys(
        summary,
        (
            "format_version runtime plan_input_sha256 "
            "specimen_phases_at_specimen_origin_rad source_model source_mass"
        ),
    )
    _require(
        summary["format_version"] == "full_noisy_study_truth_v1"
        and summary["source_model"] == "closed_midpoint_total_normalized_catalogue_order",
        "truth summary literals",
    )
    _sha_value(summary["plan_input_sha256"])
    _validate_runtime(summary["runtime"])
    _array(summary["specimen_phases_at_specimen_origin_rad"], (3, 5))
    _keys(summary["source_mass"], "bead specimen")
    names = ["catalogue_total_e", "stored_total_e", "difference_e", "relative_difference"]
    for mass in summary["source_mass"].values():
        _keys(mass, " ".join(names) + " unavailable_fields")
        for field in names:
            _nullable_real(
                mass[field], nonnegative=field in ("catalogue_total_e", "stored_total_e")
            )
        _validate_unavailable(mass["unavailable_fields"], names, "zero_reference unrepresentable")
        _require(
            {i["field"] for i in mass["unavailable_fields"]}
            == {n for n in names if mass[n] is None},
            "source mass availability",
        )
    return plan, _digest(root / "complete.json")


def _decimal_parts(value: Decimal) -> tuple[float, int]:
    if value == 0:
        return 0.0, 0
    exponent = int((abs(value).adjusted() + 1) * math.log2(10))
    scaled = value / (Decimal(2) ** exponent)
    while abs(scaled) >= 1:
        scaled /= 2
        exponent += 1
    while abs(scaled) < Decimal("0.5"):
        scaled *= 2
        exponent -= 1
    return float(scaled), exponent


def _linear(terms: list[tuple[Any, Decimal]], constant: Decimal = Decimal(0)) -> tuple[Any, int]:
    """Represent a finite array times a shared power of two without overflow.

    Each coefficient multiplies its complete represented array before the
    shared scaling. This avoids overflowing g*mu or an unweighted axial sum.
    """
    prepared = []
    for values, coefficient in terms:
        data = np.asarray(values, dtype=np.float64)
        maximum = float(np.max(np.abs(data), initial=0))
        exponent = math.frexp(maximum)[1] if maximum else 0
        mantissa, power = _decimal_parts(coefficient * (Decimal(2) ** exponent))
        prepared.append((data, exponent, mantissa, power))
    cm, ce = _decimal_parts(constant)
    power = max([e for _, _, m, e in prepared if m] + ([ce] if cm else []) or [0])
    # No array multiplication involves an unrepresentable coefficient.
    with np.errstate(under="ignore"):
        result = np.full(prepared[0][0].shape, math.ldexp(cm, ce - power) if cm else 0.0)
        for data, e, m, p in prepared:
            if m:
                result += np.ldexp(data, -e) * math.ldexp(m, p - power)
    return result, power


def _squares(data: Any) -> float:
    return math.fsum(float(np.sum(block * block, dtype=np.float64)) for block in _chunks(data))


def _merge_squares(old: float, old_power: int, new: float, new_power: int) -> tuple[float, int]:
    if not old:
        return new, new_power
    if not new:
        return old, old_power
    power = max(old_power, new_power)
    a = math.ldexp(1.0, old_power - power)
    b = math.ldexp(1.0, new_power - power)
    return math.fsum((old * a * a, new * b * b)), power


class _Metrics:
    """Stream scaled statistics with separate reference and error norm scales."""

    def __init__(self) -> None:
        self.count = 0
        self.ref_power = self.error_power = 0
        self.ref_square = self.error_square = self.error_sum = self.error_max = 0.0

    def add(self, estimated: Any, reference: tuple[Any, int]) -> None:
        """Accumulate every element of one paired payload."""
        ref, ref_power = reference
        est = np.asarray(estimated, dtype=np.float64)
        _require(est.shape == ref.shape, "comparison shape")
        ref_max = float(np.max(np.abs(ref), initial=0))
        if ref_max:
            shift = math.frexp(ref_max)[1]
            with np.errstate(under="ignore"):
                ref = np.ldexp(ref, -shift)
            ref_power += shift
            square = _squares(ref)
            self.ref_square, self.ref_power = _merge_squares(
                self.ref_square, self.ref_power, square, ref_power
            )
        est_max = float(np.max(np.abs(est), initial=0))
        est_power = math.frexp(est_max)[1] if est_max else ref_power
        power = max(ref_power if ref_max else est_power, est_power)
        with np.errstate(under="ignore"):
            error = np.ldexp(est, -power) - np.ldexp(ref, ref_power - power)
        maximum = float(np.max(np.abs(error), initial=0))
        self.count += int(est.size)
        if maximum:
            shift = math.frexp(maximum)[1]
            with np.errstate(under="ignore"):
                error = np.ldexp(error, -shift)
            power += shift
            square = _squares(error)
            total = math.fsum(float(np.sum(block, dtype=np.float64)) for block in _chunks(error))
            previous_power = self.error_power
            had_error = bool(self.error_square)
            self.error_square, self.error_power = _merge_squares(
                self.error_square, self.error_power, square, power
            )
            old_scale = math.ldexp(1.0, previous_power - self.error_power) if had_error else 0.0
            new_scale = math.ldexp(1.0, power - self.error_power)
            self.error_sum = math.fsum((self.error_sum * old_scale, total * new_scale))
            self.error_max = max(
                self.error_max * old_scale, math.ldexp(maximum, -shift) * new_scale
            )

    def finish(self) -> dict[str, Any]:
        """Return each independently representable descriptive statistic."""
        n = Decimal(self.count)
        ref_scale, error_scale = Decimal(2) ** self.ref_power, Decimal(2) ** self.error_power
        rnorm = _dec(self.ref_square).sqrt() * ref_scale
        enorm = _dec(self.error_square).sqrt() * error_scale
        targets = dict(
            reference_l2=rnorm,
            error_l2=enorm,
            relative_l2=None if self.ref_square == 0 else enorm / rnorm,
            error_rms=(_dec(self.error_square) / n).sqrt() * error_scale,
            error_max_abs=_dec(self.error_max) * error_scale,
            error_mean=_dec(self.error_sum) / n * error_scale,
        )
        result: dict[str, Any] = dict(count=self.count)
        result.update({k: None if v is None else _float_or_none(v) for k, v in targets.items()})
        result["unavailable_fields"] = [
            dict(field=k, reason="zero_reference" if v is None else "unrepresentable")
            for k, v in targets.items()
            if result[k] is None
        ]
        return result


def _camera_comparison(camera: Any, truth: Any) -> dict[str, Any]:
    offset, gain, background, flat = (
        _dec(truth[k])
        for k in ("offset_counts", "gain_counts_per_e", "background_e", "flat_signal_e")
    )
    expected = (offset, offset + gain * background, offset + gain * (background + flat))
    errors = [
        _float_or_none(_dec(v) - ref)
        for v, ref in zip(camera["means_counts"], expected, strict=True)
    ]
    contrast = _float_or_none(_dec(camera["contrast_counts"]) - gain * flat)
    physical = (
        None
        if camera["gain_counts_per_e"] is None
        else _float_or_none(_dec(camera["gain_counts_per_e"]) - gain)
    )
    unavailable = [
        dict(field=f"means_error_counts[{i}]", reason="unrepresentable")
        for i, v in enumerate(errors)
        if v is None
    ]
    if contrast is None:
        unavailable.append(dict(field="contrast_error_counts", reason="unrepresentable"))
    if physical is None:
        unavailable.append(
            dict(
                field="gain_error_counts_per_e",
                reason="estimate_unavailable"
                if camera["gain_counts_per_e"] is None
                else "unrepresentable",
            )
        )
    return dict(
        means_error_counts=errors,
        contrast_error_counts=contrast,
        gain_error_counts_per_e=physical,
        unavailable_fields=unavailable,
    )


def _bead_comparisons(candidate: Any, truth: Any, gain: Decimal, contrast: Decimal) -> Any:
    result = []
    for permutation in itertools.permutations(range(3)):
        centers = [
            [
                _float_or_none(
                    _dec(candidate["centers_um_zyx"][i][j]) - _dec(truth[permutation[i]][j])
                )
                for j in range(3)
            ]
            for i in range(3)
        ]
        brightness = [
            _float_or_none(
                _dec(candidate["brightness_relative"][i])
                - gain * _dec(truth[permutation[i]][4]) / contrast
            )
            for i in range(3)
        ]
        if any(v is None for row in centers for v in row) or any(v is None for v in brightness):
            return None
        result.append(
            dict(
                permutation=list(permutation),
                center_error_um_zyx=centers,
                brightness_error_relative=brightness,
            )
        )
    return result


def _normalize_beams(values: Any) -> list[Decimal]:
    # Decimal norm retains tiny ratios and handles maximum-finite components.
    beam = [_dec(v) for v in values]
    norm = sum((v * v for v in beam), Decimal(0)).sqrt()
    return [v / norm for v in beam]


def _illumination_comparisons(candidate: Any, truth: Any) -> Any:
    result = []
    normalized_truth = _normalize_beams(truth["beam_amplitudes"])
    for gauge, sign in (("as_stored", 1), ("global_side_exchange", -1)):
        q = [
            [
                _float_or_none(
                    sign * _dec(candidate["carriers_yx_per_um"][o][i])
                    - _dec(truth["carriers_yx_per_um"][o][i])
                )
                for i in range(2)
            ]
            for o in range(3)
        ]
        differences = [
            [
                sign * _dec(candidate["phases_rad"][o][p])
                - _dec(truth["phases_at_calibration_origin_rad"][o][p])
                for p in range(9)
            ]
            for o in range(3)
        ]
        raw = [[_float_or_none(v) for v in row] for row in differences]
        if any(v is None for row in [*q, *raw] for v in row):
            return None
        fitted_beam = candidate["beam_amplitudes"]
        if sign == -1:
            fitted_beam = [fitted_beam[0], fitted_beam[2], fitted_beam[1]]
        normalized_fit = _normalize_beams(fitted_beam)
        result.append(
            dict(
                gauge=gauge,
                carrier_error_yx_per_um=q,
                phase_error_rad=raw,
                wrapped_phase_error_rad=[[_wrap(v) for v in row] for row in differences],
                normalized_beam_error=[
                    float(a - b) for a, b in zip(normalized_fit, normalized_truth, strict=True)
                ],
            )
        )
    return result


def _load_mapped(path: Path) -> Any:
    return np.asarray(np.load(path, mmap_mode="r", allow_pickle=False))


def _evaluate(obs: Path, inference: Path, truth: Path, out: Path) -> int:
    g, obs_sha = _observations(obs)
    estimates, freeze, freeze_sha = _validate_inference(inference, g, obs_sha)
    # No truth path stat/open occurs above this line.
    plan, truth_sha = _validate_truth(truth, g, obs_sha)
    _claim(out)
    report: dict[str, Any] = dict(
        format_version="full_noisy_study_evaluation_v1",
        status="reported_unavailable",
        message=freeze["message"],
        runtime=_runtime(),
        observation_manifest_sha256=obs_sha,
        inference_freeze_sha256=freeze_sha,
        private_truth_manifest_sha256=truth_sha,
        inference_status=freeze["status"],
        inference_stage=freeze["stage"],
        inference_failure_code=freeze["failure_code"],
        **dict.fromkeys(COMPARISONS),
        unavailable_comparisons=[],
        limitations=LIMITATIONS,
    )
    if freeze["status"] == "unavailable":
        report["message"] = (
            freeze["message"]
            + "; "
            + "; ".join(
                name
                + "="
                + (
                    "not_returned"
                    if estimates[name] is None
                    else "returned"
                    if name == "camera_estimate"
                    else estimates[name]["status"]
                )
                for name in ("camera_estimate", "bead_calibration", "specimen_fit")
            )
        )
        report["unavailable_comparisons"] = [
            dict(field=name, reason="inference_unavailable") for name in COMPARISONS
        ]
    else:
        with localcontext() as ctx:
            ctx.prec = 800
            camera = estimates["camera_estimate"]
            true_camera = plan["camera"]
            gain, contrast, blank = (
                _dec(true_camera["gain_counts_per_e"]),
                _dec(camera["contrast_counts"]),
                _dec(camera["means_counts"][1]),
            )
            report["camera_comparison"] = _camera_comparison(camera, true_camera)
            source = _load_mapped(truth / "specimen_source_e.npy")
            metric = _Metrics()
            metric.add(
                _load_mapped(inference / "specimen_source_relative.npy"),
                _linear([(source[::2], gain / contrast), (source[1::2], gain / contrast)]),
            )
            report["source_metrics"] = metric.finish()
            del source
            signal_metric, corrected_metric = _Metrics(), _Metrics()
            affine = (
                _dec(true_camera["offset_counts"])
                + gain * _dec(true_camera["background_e"])
                - blank
            ) / contrast
            residual_mean: list[list[Any]] = [[], [], []]
            residual_rms: list[list[Any]] = [[], [], []]
            for o in range(3):
                for p in range(5):
                    name = f"specimen_o{o}_p{p}.npy"
                    prediction = _load_mapped(inference / f"prediction_o{o}_p{p}.npy")
                    mean = _load_mapped(truth / name.replace(".npy", "_expected_signal_e.npy"))
                    signal_metric.add(prediction, _linear([(mean, gain / contrast)]))
                    corrected_metric.add(prediction, _linear([(mean, gain / contrast)], affine))
                    residual = _Metrics()
                    residual.add(
                        prediction,
                        _linear([(_load_mapped(obs / name), 1 / contrast)], -blank / contrast),
                    )
                    stats = residual.finish()
                    residual_mean[o].append(stats["error_mean"])
                    residual_rms[o].append(stats["error_rms"])
                    del mean, prediction
            report["signal_prediction_metrics"] = signal_metric.finish()
            report["corrected_mean_prediction_metrics"] = corrected_metric.finish()
            report["observed_residual_mean"] = (
                None if any(v is None for row in residual_mean for v in row) else residual_mean
            )
            report["observed_residual_rms"] = (
                None if any(v is None for row in residual_rms for v in row) else residual_rms
            )
            candidate = estimates["bead_calibration"]["frozen_candidate"]
            report["bead_permutation_comparisons"] = _bead_comparisons(
                candidate, plan["bead_catalogue"], gain, contrast
            )
            report["illumination_gauge_comparisons"] = _illumination_comparisons(
                candidate, plan["illumination"]
            )
            unavailable = []
            for field in COMPARISONS:
                value = report[field]
                reasons = (
                    ["unrepresentable"]
                    if value is None
                    else (
                        [v["reason"] for v in value["unavailable_fields"]]
                        if isinstance(value, dict) and "unavailable_fields" in value
                        else []
                    )
                )
                for reason in dict.fromkeys(reasons):
                    unavailable.append(dict(field=field, reason=reason))
            report["unavailable_comparisons"] = unavailable
            report["status"] = "evaluated_with_unavailable_metrics" if unavailable else "evaluated"
            report["message"] = "Frozen finite fit assessed in its paired estimated camera gauge"
    item = _write_json(out / "evaluation.json", report)
    _write_json(
        out / "complete.json",
        dict(
            format_version="full_noisy_study_evaluation_complete_v1",
            status=report["status"],
            observation_manifest_sha256=obs_sha,
            inference_freeze_sha256=freeze_sha,
            private_truth_manifest_sha256=truth_sha,
            files=item,
        ),
    )
    return 3 if report["status"] == "reported_unavailable" else 0


def _arguments(argv: list[str]) -> Any:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    options = {
        "generate": ("plan", "out"),
        "infer": (
            "observations",
            "out",
            "sweep-scales",
            "regularization",
            "max-iterations",
            "max-backtracking-trials",
            "pupil-order",
        ),
        "evaluate": ("observations", "inference", "private-truth", "out"),
    }
    for name, flags in options.items():
        command = commands.add_parser(name, allow_abbrev=False)
        for flag in flags:
            command.add_argument("--" + flag, required=True)
    # argparse's ordinary store action otherwise silently takes the last value.
    flags = [token.split("=", 1)[0] for token in argv if token.startswith("--")]
    if len(flags) != len(set(flags)):
        parser.error("duplicate options")
    result = parser.parse_args(argv)
    if result.command == "infer":
        try:
            result.algorithm = _settings(
                dict(
                    sweep_scales=_parse_json(result.sweep_scales),
                    regularization=_parse_json(result.regularization),
                    max_iterations=_parse_json(result.max_iterations),
                    max_backtracking_trials=_parse_json(result.max_backtracking_trials),
                    pupil_order=_parse_json(result.pupil_order),
                )
            )
        except _Fault as exc:
            parser.error(str(exc))
    return result


def main(argv: list[str] | None = None) -> int:
    """Run one exclusive study stage and report recognized protocol failures."""
    args = None
    try:
        args = _arguments(sys.argv[1:] if argv is None else argv)
        if args.command == "generate":
            return _generate(Path(args.plan), Path(args.out))
        if args.command == "infer":
            return _infer(Path(args.observations), Path(args.out), args.algorithm)
        return _evaluate(
            Path(args.observations), Path(args.inference), Path(args.private_truth), Path(args.out)
        )
    except _Fault as exc:
        failure = exc
    except FileExistsError as exc:
        failure = _Fault("full_noisy_study_output_exists", str(exc), 5)
    except OSError as exc:
        failure = _Fault("full_noisy_study_io", str(exc), 5)
    except SimreconError as exc:
        if (
            args is None
            or args.command != "generate"
            or exc.code
            not in {"simulation_source_range", "simulation_optics_range", "simulation_camera_range"}
        ):
            raise
        failure = _Fault("full_noisy_study_range", str(exc), 6, exc.code)
    diagnostic = dict(
        command=None if args is None else args.command,
        status="error",
        stage="input"
        if failure.exit_code in (2, 4)
        else "output"
        if failure.exit_code == 5
        else "generation",
        error_code=failure.code,
        cause_code=failure.cause,
        message=str(failure),
        output_dir=None if args is None else args.out,
    )
    print(
        json.dumps(
            diagnostic, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ),
        file=sys.stderr,
    )
    return failure.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
