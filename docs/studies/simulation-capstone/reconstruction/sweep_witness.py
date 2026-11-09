"""Bind the exact capstone inputs and independently check and score sweep observations."""

import hashlib
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import sweep_response as response
import sweep_scoring as scoring
from reference_table import calibration_table

SPECIMEN_SHAPE = (1, 3, 5, 32, 128, 128)
CALIBRATION_SHAPE = (5, 32, 128, 128)
BANDS_SHAPE = (1, 3, 5, 32, 128, 65)
TRANSFER_SHAPE = (3, 65, 32)
BASE_WIENER = 0.020
PANEL_WIENERS = (0.002, 0.020, 0.200)
AXES = (scoring.GXY, scoring.GXY, scoring.GZ)
D_RADIAL = 1 / (128 * 0.09)
D_AXIAL = 0.25
ALPHA = 1 / (32 * 256 * 256 * 3)
ACQUISITION_DEFAULTS = {
    "flatfield_slope": None,
    "phases_rad": None,
    "phase_steps_rad": None,
    "edge_pixels": 10,
    "equalize": True,
    "equalize_z": False,
    "equalize_time": False,
    "storage_order": "direction-major",
    "combine_off_orders": None,
    "drift_between": False,
    "drift_within": False,
    "fit_drift": False,
    "adjust_phases": False,
    "drift_filter_fraction": 0.0,
}
CARRIER_DEFAULTS = {
    "phase_start_angle_rad": 1.57193,
    "negative_angle_step": False,
    "angles_rad": None,
    "search_carriers": True,
    "use_time0_carriers": True,
    "amplitude_floors": None,
    "fit_all_phases": True,
}
FILTER_DEFAULTS = {
    "wiener_increment": 0.0,
    "suppress_singularities": True,
    "suppression_radius_bins": 10.0,
    "dampen_order0": False,
    "omit_order0": False,
    "omit_kz0": False,
    "output_taper": "cosine",
    "power_taper_exponent": None,
    "precise_taper": False,
    "filter_overlaps": True,
    "explode_factor": 1.0,
}
PINS = json.loads(Path(__file__).with_name("sweep_pins.json").read_text())


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _binary64(value, label):
    # NumPy scalar equality may narrow the Python operand. Validate before converting.
    _require(type(value) in (float, np.float64), f"{label} must be a binary64 scalar")
    result = float(value)
    _require(math.isfinite(result), f"{label} must be finite")
    return result


def _registered_wiener(value):
    wiener = _binary64(value, "Wiener value")
    _require(wiener in response.WIENERS, "unregistered Wiener value")
    return wiener


def _require_wiener(value, expected, label):
    result = _binary64(value, label)
    _require(result == expected, f"{label} differs from the exact Wiener setting")
    return result


def _check_filter_wiener(settings, wiener, label):
    _require_wiener(settings.get("wiener"), wiener, f"{label} wiener")
    _require_wiener(settings.get("wiener_increment"), 0.0, f"{label} wiener_increment")


def _check_known_wiener(settings, wiener, label):
    _check_filter_wiener(settings, wiener, label)
    effective = settings.get("effective_wiener")
    _require(isinstance(effective, tuple) and len(effective) == 1, f"unexpected {label} sequence")
    return _require_wiener(effective[0], wiener, f"{label} effective_wiener")


def _array_identity(array):
    data = np.ascontiguousarray(array, dtype=array.dtype.newbyteorder("<"))
    return (data.shape, data.dtype.str, hashlib.sha256(memoryview(data).cast("B")).hexdigest())


def _array(array, shape, kind, label):
    _require(
        isinstance(array, np.ndarray)
        and array.shape == shape
        and array.dtype.newbyteorder("<") == np.dtype(kind)
        and np.isfinite(array).all(),
        f"{label} must be a finite {kind} array of shape {shape}",
    )
    return array


def _fixed_axes(record):
    for field, expected in zip(("x_um", "y_um", "z_um"), AXES, strict=True):
        value = _array(getattr(record, field), expected.shape, "<f8", field)
        _require(np.array_equal(value, expected), f"unexpected signed coordinate vector {field}")


def _check_workflow_wiener(filtering, effective):
    _check_filter_wiener(filtering, BASE_WIENER, "workflow filtering")
    sequence = _array(effective, (1,), "<f8", "workflow effective_wiener")
    _require_wiener(sequence[0], BASE_WIENER, "workflow effective_wiener")


def _settings(value):
    if isinstance(value, dict):
        return tuple((k, _settings(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(map(_settings, value))
    return value


def _output_axes():
    return {
        "order": "zyx",
        "shape": scoring.OUTPUT_SHAPE,
        "origin_um": [float(v[0]) for v in AXES[::-1]],
        "pitch_um": [scoring.DZ, scoring.PITCH, scoring.PITCH],
    }


def _check_prior_fields(prior, expected, label):
    _require(prior.keys() == expected.keys(), f"unexpected fields in prior {label}")
    for field, value in expected.items():
        # JSON normalizes tuples to lists and still distinguishes signed zero and booleans.
        old = json.dumps(prior[field], sort_keys=True, allow_nan=False)
        new = json.dumps(value, sort_keys=True, allow_nan=False)
        _require(old == new, f"prior {label} {field} differs")


def _check_reuse_wieners(value, prior):
    wiener = _registered_wiener(value)
    _require(wiener in PANEL_WIENERS, "Wiener value is ineligible for carry-forward")
    _require_wiener(prior.get("wiener"), wiener, "prior row wiener")
    effective = _require_wiener(prior.get("effective_wiener"), wiener, "prior row effective_wiener")
    return wiener, effective


PUBLIC_ROLES = frozenset(("specimen", "calibration", "settings"))
EVALUATOR_ROLES = frozenset(("truth", "conventional"))


def _valid_evaluator_roles(case, roles):
    return roles == EVALUATOR_ROLES or (
        case == "cell" and roles == EVALUATOR_ROLES | {"reference_table"}
    )


def _read_settings(case, path):
    payload = Path(path).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    variants = PINS[case]["settings"]
    for variant in variants.values():
        if variant["sha256"] == digest:
            break
    else:
        raise ValueError(f"{case} settings do not match an independent variant pin")

    settings = json.loads(payload)
    # Undo only the two serialized name bindings before checking every archived byte.
    archived = variants["archived"]
    for role, identity in (
        ("specimen", settings["specimen_identity"]),
        ("calibration", settings["calibration"]["identity"]),
    ):
        name = variant[role]
        _require(identity["files"][0]["name"] == name, f"incorrect {case} {role} file name")
        payload = payload.replace(
            f'"name": "{name}"'.encode("ascii"),
            f'"name": "{archived[role]}"'.encode("ascii"),
            1,
        )
    _require(
        hashlib.sha256(payload).hexdigest() == archived["sha256"],
        f"{case} settings differ from the archive beyond the two file names",
    )
    return settings, digest


def _load_pinned(case, files, role, shape, kind):
    path = Path(files[role])
    with path.open("rb") as stream:
        _require(
            hashlib.file_digest(stream, "sha256").hexdigest() == PINS[case][role],
            f"{case} {role} does not match its independent file pin",
        )
    source = np.load(path, allow_pickle=False, mmap_mode="r")
    return _array(np.asarray(source), shape, kind, role)


@dataclass(frozen=True)
class PublicInputs:
    """Read-only specimen and raw calibration with exact public call settings."""

    case: str
    settings: dict[str, Any]
    settings_sha256: str
    specimen: np.ndarray
    calibration: np.ndarray

    @classmethod
    def bind(cls, case, files):
        """Bind public material without opening any evaluator files."""
        _require(case in PINS and set(files) == PUBLIC_ROLES, "incorrect public sweep input roles")
        settings, digest = _read_settings(case, files["settings"])
        specimen = _load_pinned(case, files, "specimen", SPECIMEN_SHAPE, "<f4")
        calibration = _load_pinned(case, files, "calibration", CALIBRATION_SHAPE, "<f4")
        return cls(case, settings, digest, specimen, calibration)

    def workflow_kwargs(self):
        """Return fresh public settings and calibration, with no evaluator inputs."""
        args = json.loads(json.dumps(self.settings))
        args["calibration"]["raw"] = self.calibration
        return args


@dataclass(frozen=True)
class Inputs(PublicInputs):
    """Public inputs and the independent evaluator arrays used only for scoring."""

    truth: np.ndarray
    conventional: np.ndarray
    mask: np.ndarray | None

    @classmethod
    def bind(cls, case, files):
        """Bind all study inputs for independent qualification without runtime calls."""
        evaluator_roles = files.keys() - PUBLIC_ROLES
        _require(
            case in PINS
            and files.keys() >= PUBLIC_ROLES
            and _valid_evaluator_roles(case, evaluator_roles),
            "incorrect sweep input roles",
        )
        public = PublicInputs.bind(case, {role: files[role] for role in PUBLIC_ROLES})
        return cls.bind_evaluator(public, {role: files[role] for role in evaluator_roles})

    @classmethod
    def bind_evaluator(cls, public, files):
        """Bind truth and comparator and establish the independent mask for scoring."""
        _require(
            public.case in PINS and _valid_evaluator_roles(public.case, set(files)),
            "incorrect sweep evaluator roles",
        )
        truth = _load_pinned(public.case, files, "truth", scoring.OUTPUT_SHAPE, "<f8")
        conventional = _load_pinned(public.case, files, "conventional", scoring.OUTPUT_SHAPE, "<f8")
        mask = None
        if public.case == "cell":
            if "reference_table" in files:
                table = _load_pinned(public.case, files, "reference_table", TRANSFER_SHAPE, "<c16")
            else:
                table = _array(
                    calibration_table(public.calibration), TRANSFER_SHAPE, "<c16", "reference_table"
                )
                with io.BytesIO() as stream:
                    np.save(stream, table, allow_pickle=False)
                    digest = hashlib.sha256(stream.getbuffer()).hexdigest()
                _require(
                    digest == PINS["cell"]["reference_table"],
                    f"regenerated cell reference_table does not match its independent file pin "
                    f"(SHA-256 {digest})",
                )
            mask = scoring.conditioned_low_mask(table)
            reference = scoring.cell_scores(truth, truth, mask)
            low = reference["low_band"]
            _require(
                low["truth_rms_su"] >= 0.001
                and np.count_nonzero(mask[1:]) >= 4
                and min(reference["contrast_su"].values()) > 0.025,
                "independent cell truth does not satisfy the frozen score conditioning",
            )
            mask.setflags(write=False)
        return cls(
            public.case,
            public.settings,
            public.settings_sha256,
            public.specimen,
            public.calibration,
            truth,
            conventional,
            mask,
        )

    def reference_metrics(self):
        """Provide common comparator and truth metrics and fixed display scales."""
        ranges = scoring.display_ranges(self.truth, self.conventional)
        truth = scoring.measure(self.case, self.truth, self.truth, self.mask)
        conventional = scoring.measure(self.case, self.conventional, self.truth, self.mask)
        if self.case == "beads":
            for metrics in (truth, conventional):
                beads = metrics["beads"]
                _require(
                    beads["P45"]["status"] == "resolved"
                    and not any(
                        features[axis]["status"] == "false-split"
                        for label, features in beads.items()
                        if label.startswith("I")
                        for axis in ("lateral_false_split", "transverse_false_split")
                    ),
                    "independent bead reference fails the accepted wide-pair/isolated controls",
                )
        return {
            "file_sha256": PINS[self.case] | {"settings": self.settings_sha256},
            "output_axes": _output_axes(),
            "reconstruction_gain_su_per_count": scoring.SCORE_GAIN_SU_PER_COUNT,
            "conventional_gain_su_per_adu": 1 / 120_000,
            "display_ranges": ranges,
            "panel_wieners": PANEL_WIENERS,
            "truth": truth,
            "same_exposure": conventional,
        }


def _check_workflow(inputs, workflow):
    expected = inputs.settings
    actual = dict(workflow.resolved_settings)
    for key, defaults in (
        ("acquisition", ACQUISITION_DEFAULTS),
        ("carrier", CARRIER_DEFAULTS),
        ("filtering", FILTER_DEFAULTS),
        ("optics", {}),
    ):
        expected_options = {k: _settings(v) for k, v in (defaults | expected[key]).items()}
        actual_options = dict(actual[key])
        if key == "filtering":
            _check_workflow_wiener(actual_options, workflow.effective_wiener)
        _require(actual_options == expected_options, f"unexpected workflow {key} settings")
    _require(
        actual["original_shape"] == actual["effective_shape"] == SPECIMEN_SHAPE
        and actual["phase_policy"] == "uniform"
        and actual["plane_policy"] == "native"
        and actual["norders_in"] == 3
        and actual["calibration_selection"] == "raw-beads"
        and actual["header_timestamp_unit"] is None
        and workflow.layout is None
        and workflow.intensity_unit == "ADU",
        "unexpected workflow layout, calibration route or intensity unit",
    )
    declared = dict(workflow.source_declarations)
    for label, source in (
        ("specimen_identity", expected["specimen_identity"]),
        ("calibration_identity", expected["calibration"]["identity"]),
    ):
        identity = dict(declared[label])
        _require(
            identity.pop("optics", None) is None
            and identity == {k: _settings(v) for k, v in source.items()},
            f"unexpected workflow {label}",
        )
    calibration = workflow.calibration
    transfer = workflow.transfer
    _require(calibration is not None, "workflow did not expose its raw-bead preparation")
    prepared = calibration.transfer
    _require(
        (prepared.layout, prepared.dkr_cyc_um, prepared.dkz_cyc_um, prepared.norders)
        == (transfer.layout, transfer.dkr_cyc_um, transfer.dkz_cyc_um, transfer.norders)
        and _array_identity(prepared.samples) == _array_identity(transfer.samples),
        "workflow did not consume the raw-bead transfer value",
    )
    calibrated = dict(calibration.resolved_settings)
    for key, value in expected["calibration"]["settings"].items():
        _require(
            key in calibrated and calibrated[key] == _settings(value),
            f"unexpected raw-bead setting {key}",
        )

    _fixed_axes(workflow)
    _array(workflow.image, (1, *scoring.OUTPUT_SHAPE), "<f8", "workflow image")
    _require(len(workflow.reconstructions) == 1, "expected one workflow reconstruction")
    band_identity = _array_identity(workflow.bands.quadratures)
    specimen_identity = _array_identity(inputs.specimen)
    identities = {
        item.name: (item.shape, item.dtype, item.sha256) for item in workflow.input_identities
    }
    _require(
        identities
        == {
            "specimen": specimen_identity,
            "selected_specimen": specimen_identity,
            "calibration.raw": _array_identity(inputs.calibration),
            "prepared_quadratures": band_identity,
            "consumed_transfer": _array_identity(workflow.transfer.samples),
        },
        "workflow input or stage bytes differ from the actual frozen material",
    )


@dataclass(frozen=True)
class StageWitness:
    """Actual fixed stage arguments and a separate independent signed prediction."""

    case: str
    settings_sha256: str
    bands: Any
    transfer: Any
    carriers: np.ndarray
    modulation: np.ndarray[Any, np.dtype[np.complex128]]
    fixed_arrays: dict[str, tuple]
    options: tuple[tuple[str, Any], ...]
    predictions: np.ndarray
    minimum_separation: float

    @classmethod
    def start(cls, inputs, workflow):
        """Bind fixed stage arguments and calculate all five independent predictions."""
        _check_workflow(inputs, workflow)
        bands, transfer = workflow.bands, workflow.transfer
        _require(
            bands.input_shape == SPECIMEN_SHAPE
            and bands.input_scale == ALPHA
            and bands.acquisition_mode == "3d"
            and bands.storage_order == "direction-major"
            and (bands.dxy_um, bands.dz_um, bands.lateral_zoom, bands.axial_zoom)
            == (0.08, 0.125, 2, 1),
            "unexpected preparation dimensions, pitches, zoom or normalization",
        )
        _require(
            transfer.layout == "radial"
            and transfer.norders == 3
            and (transfer.dkr_cyc_um, transfer.dkz_cyc_um) == (D_RADIAL, D_AXIAL),
            "unexpected transfer layout or radial/axial calibration increments",
        )
        _array(bands.quadratures, BANDS_SHAPE, "<c16", "prepared quadratures")
        variances = _array(bands.noise_variance_factors, (1, 3, 3), "<f8", "variance factors")
        _require(np.all(variances == 1), "uniform specimen variance factors must all be one")
        _require(
            np.all(bands.equalization_gains == 1)
            and np.all(bands.background_after == 512)
            and np.all(bands.slope_after == 1)
            and not bands.sentinel_frames
            and bands.off_quadratures is None
            and not np.any(bands.between_displacements_pixels)
            and not np.any(bands.exposure_displacements_pixels),
            "unexpected preparation gain, camera, sentinel, off frame or drift",
        )
        table = _array(transfer.samples, TRANSFER_SHAPE, "<c16", "actual radial transfer")
        carriers = _array(workflow.parameters.carriers_cyc_um, (1, 3, 2), "<f8", "carriers")[0]
        _require(
            workflow.parameters.branches == (("searched",) * 3,),
            "unexpected carrier estimator branch",
        )
        modulation = _array(workflow.parameters.modulation, (1, 3, 2), "<c16", "modulation")[0]
        resolved = dict(workflow.resolved_settings)
        options = dict(resolved["optics"]) | dict(resolved["filtering"])
        del options["wiener"]
        prediction = response.predicted(
            inputs.specimen[0],
            table,
            D_RADIAL,
            carriers,
            modulation,
            variances[0],
            response.POINTS_YX[inputs.case],
            response.AXIAL_BINS,
        )
        prediction.setflags(write=False)
        return cls(
            inputs.case,
            inputs.settings_sha256,
            bands,
            transfer,
            carriers,
            modulation,
            _stage_identities(bands, transfer, carriers, modulation),
            tuple(options.items()),
            prediction,
            response.prediction_margin(prediction),
        )

    def _check_fixed(self):
        _require(
            self.fixed_arrays
            == _stage_identities(self.bands, self.transfer, self.carriers, self.modulation),
            "a fixed preparation, transfer or fitted parameter array changed",
        )

    def fixed_metadata(self):
        """Report actual factor values and fingerprints shared by the five rows."""
        self._check_fixed()
        return {
            "native_input_scale": self.bands.input_scale,
            "settings_except_wiener": dict(self.options),
            "array_identities": self.fixed_arrays.copy(),
            "carriers_cyc_um": self.carriers.tolist(),
            "modulation_re_im": np.stack(
                [self.modulation.real, self.modulation.imag], axis=-1
            ).tolist(),
            "variance_factors": self.bands.noise_variance_factors[0].tolist(),
            "transfer_layout": self.transfer.layout,
            "transfer_pitch_radial_axial_cyc_um": [
                self.transfer.dkr_cyc_um,
                self.transfer.dkz_cyc_um,
            ],
        }

    def stage_arguments(self, wiener):
        """Return the actual one-time bands, transfer and unchanged filter options."""
        wiener = _registered_wiener(wiener)
        self._check_fixed()
        kwargs = dict(self.options) | {
            "carriers_cyc_um": self.carriers,
            "modulation": self.modulation,
            "wiener": wiener,
        }
        return (self.bands, self.transfer), kwargs

    def _check_inputs(self, inputs):
        _require(
            (inputs.case, inputs.settings_sha256) == (self.case, self.settings_sha256),
            "observation belongs to a different sweep specimen or settings variant",
        )
        self._check_fixed()

    def _checked_counts(self, inputs, wiener, record):
        wiener = _registered_wiener(wiener)
        self._check_inputs(inputs)
        _fixed_axes(record)
        actual = dict(record.resolved_settings)
        effective = _check_known_wiener(actual, wiener, "known reconstruction")
        expected = dict(self.options) | {
            "wiener": wiener,
            "effective_wiener": (wiener,),
            "acquisition_mode": "3d",
            "dxy_um": 0.08,
            "dz_um": 0.125,
            "lateral_zoom": 2,
            "axial_zoom": 1,
            "input_scale": ALPHA,
        }
        _require(actual == expected, "known reconstruction changed fixed settings or Wiener")
        _require(
            record.radial_cutoff_cyc_um == response.RADIUS_CYC_UM
            and np.array_equal(record.axial_cutoffs_bins, [8, 15, 10]),
            "known reconstruction changed optical support",
        )
        _require(
            _array_identity(record.carriers_cyc_um) == self.fixed_arrays["carriers_cyc_um"]
            and _array_identity(record.modulation) == self.fixed_arrays["modulation"],
            "known reconstruction changed supplied carriers or complex modulation",
        )
        counts = _array(record.image, (1, *scoring.OUTPUT_SHAPE), "<f8", "signed image")[0]
        return counts, wiener, effective

    def check_row(self, inputs, wiener, record):
        """Check and score the actual stage output; also return fixed signed panel arrays."""
        counts, wiener, effective = self._checked_counts(inputs, wiener, record)
        return self._score_row(inputs, wiener, counts, effective)

    def check_prior_case(self, inputs, workflow, prior):
        """Compare a sealed prior case receipt with the fresh default and fixed factors."""
        self._checked_counts(inputs, BASE_WIENER, workflow.reconstructions[0])
        expected = {
            "case": inputs.case,
            "file_sha256": PINS[inputs.case] | {"settings": inputs.settings_sha256},
            "output_axes": _output_axes(),
            "fixed_metadata": self.fixed_metadata(),
            "default_replay": _default_identities(workflow),
        }
        _check_prior_fields(prior, expected, "case")

    def check_reused_row(self, inputs, wiener, counts, prior):
        """After prior case validation, recheck a saved signed image and its prior scores."""
        wiener, effective = _check_reuse_wieners(wiener, prior)
        self._check_inputs(inputs)
        counts = _array(counts, scoring.OUTPUT_SHAPE, "<f8", "saved signed image")
        identity = {
            "case": self.case,
            "wiener": wiener,
            "effective_wiener": wiener,
            "signed_image_counts_identity": _array_identity(counts),
        }
        _check_prior_fields(
            {key: prior[key] for key in identity if key in prior}, identity, "row identity"
        )
        row, panels = self._score_row(inputs, wiener, counts, effective)
        _check_prior_fields(
            prior,
            identity | {key: row[key] for key in ("metrics", "panel_clipping_counts")},
            "row",
        )
        return row, panels

    def _score_row(self, inputs, wiener, counts, effective):
        coeff = response.observed(counts, response.POINTS_YX[self.case], response.AXIAL_BINS)
        target = self.predictions[response.WIENERS.index(wiener)]
        error = response.check_projection(coeff, target)
        image = counts * scoring.SCORE_GAIN_SU_PER_COUNT
        metrics = scoring.measure(self.case, image, inputs.truth, inputs.mask)
        row: dict[str, Any] = {
            "case": self.case,
            "wiener": wiener,
            "effective_wiener": effective,
            "signed_image_counts_identity": _array_identity(counts),
            "projection": {
                "axial_bins": response.AXIAL_BINS,
                "points_yx": response.POINTS_YX[self.case],
                "expected_su_re_im": np.stack([target.real, target.imag], axis=-1).tolist(),
                "observed_su_re_im": np.stack([coeff.real, coeff.imag], axis=-1).tolist(),
                "max_abs_error_su": error,
                "atol_su": response.PROJECTION_ATOL_SU,
                "rtol": response.PROJECTION_RTOL,
                "minimum_pair_separation_in_combined_allowances": self.minimum_separation,
            },
            "metrics": metrics,
        }
        if wiener in PANEL_WIENERS:
            ranges = scoring.display_ranges(inputs.truth, inputs.conventional)
            image_planes, residuals, clipping = scoring.display_planes(
                self.case,
                image,
                inputs.truth,
                ranges,
            )
            row["panel_clipping_counts"] = clipping
            # Copy views of the measured planes so retaining panels need not pin a volume.
            panels = {f"image_su/{key}": value.copy() for key, value in image_planes.items()}
            panels.update({f"residual_su/{key}": value for key, value in residuals.items()})
        else:
            panels = {}
        return row, panels


def _stage_identities(bands, transfer, carriers, modulation):
    return {
        "quadratures": _array_identity(bands.quadratures),
        "noise_variance_factors": _array_identity(bands.noise_variance_factors),
        "separation_matrices": _array_identity(bands.separation_matrices),
        "phase_angles_rad": _array_identity(bands.phase_angles_rad),
        "transfer_samples": _array_identity(transfer.samples),
        "carriers_cyc_um": _array_identity(carriers),
        "modulation": _array_identity(modulation),
    }


def _default_identities(workflow):
    primary = workflow.reconstructions[0]
    _require(
        _array_identity(workflow.image) == _array_identity(primary.image),
        "workflow image differs from its actual one-time known result",
    )
    fields = (
        "image",
        "filtered_quadratures",
        "x_um",
        "y_um",
        "z_um",
        "carriers_cyc_um",
        "modulation",
        "axial_cutoffs_bins",
    )
    return {name: _array_identity(getattr(primary, name)) for name in fields}


def _check_replay_settings(primary, replay):
    _check_known_wiener(dict(primary), BASE_WIENER, "default workflow primary")
    _check_known_wiener(dict(replay), BASE_WIENER, "default staged replay")
    _require(primary == replay, "public stage replay differs from actual workflow at Wiener 0.020")


def check_default_replay(workflow, replay):
    """Compare actual workflow and stage outputs byte for byte at 0.020."""
    primary = workflow.reconstructions[0]
    _check_replay_settings(primary.resolved_settings, replay.resolved_settings)
    checked = _default_identities(workflow)
    _require(
        checked == {name: _array_identity(getattr(replay, name)) for name in checked}
        and primary.radial_cutoff_cyc_um == replay.radial_cutoff_cyc_um,
        "public stage replay differs from actual workflow at Wiener 0.020",
    )
    return checked


def require_complete(rows):
    """Require exactly one validated result for every case and registered Wiener."""
    found = [(row["case"], _registered_wiener(row["wiener"])) for row in rows]
    expected = [(case, w) for case in PINS for w in response.WIENERS]
    _require(sorted(found) == sorted(expected), "missing, duplicate or unregistered sweep outcome")
