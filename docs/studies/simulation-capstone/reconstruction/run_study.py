"""Run the public simulation workflow and optionally witness the fixed Wiener sweep."""

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from sweep_response import WIENER_FILES, WIENERS
from sweep_scoring import SCORE_GAIN_SU_PER_COUNT, bead_scores
from sweep_witness import BASE_WIENER, Inputs, PublicInputs, StageWitness, check_default_replay

from simrecon import (
    KnownReconstruction,
    WorkflowReconstruction,
    reconstruct_known,
    reconstruct_workflow,
)

HERE = Path(__file__).resolve().parent
CASES = ("clean", "noisy", "beads", "cell")
PUBLIC_FILES = {
    "specimen": "specimen.npy",
    "calibration": "calibration.npy",
    "settings": "settings.json",
}


def digest(path: Path) -> str:
    """Return the file SHA-256."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Create a JSON receipt exclusively."""
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def normal_arguments(case: str, paths: dict[str, Path]) -> tuple[np.ndarray, dict[str, Any]]:
    """Bind only the exact three portable public inputs for a normal run."""
    provenance = HERE.parent / "inputs" / "provenance.json"
    frozen = json.loads(provenance.read_text(encoding="utf-8"))["cases"][case]["files"]
    for path in paths.values():
        if digest(path) != frozen[path.name]["sha256"]:
            raise ValueError(f"{case}: unexpected {path.name} identity")
    settings = json.loads(paths["settings"].read_text(encoding="utf-8"))
    if (settings["filtering"]["wiener"], settings["filtering"]["wiener_increment"]) != (
        BASE_WIENER,
        0.0,
    ):
        raise ValueError("expected the frozen default Wiener value and zero increment")
    settings["calibration"]["raw"] = np.load(
        paths["calibration"], mmap_mode="r", allow_pickle=False
    )
    return np.load(paths["specimen"], mmap_mode="r", allow_pickle=False), settings


def observation_name(wiener: float) -> str:
    """Return the single observation archive name for a registered value."""
    return WIENER_FILES[wiener]


def save_observation(
    output: Path, wiener: float, record: KnownReconstruction | WorkflowReconstruction
) -> str:
    """Save actual signed counts and axes without changing their element bytes."""
    path = output / observation_name(wiener)
    with path.open("xb") as stream:
        np.savez_compressed(
            stream,
            image=record.image[0],
            x_um=record.x_um,
            y_um=record.y_um,
            z_um=record.z_um,
        )
    return digest(path)


def filter_receipt(record: KnownReconstruction, sha256: str) -> dict[str, Any]:
    """Record the actual filtering settings, support and observation digest."""
    return {
        "sha256": sha256,
        "resolved_settings": dict(record.resolved_settings),
        "radial_cutoff_cyc_um": record.radial_cutoff_cyc_um,
        "axial_cutoffs_bins": record.axial_cutoffs_bins.tolist(),
    }


def save_factors(output: Path, witness: StageWitness) -> None:
    """Save the actual fixed typed factor arrays once."""
    with (output / "fixed-factors.npz").open("xb") as stream:
        np.savez_compressed(
            stream,
            quadratures=witness.bands.quadratures,
            noise_variance_factors=witness.bands.noise_variance_factors,
            separation_matrices=witness.bands.separation_matrices,
            phase_angles_rad=witness.bands.phase_angles_rad,
            transfer_samples=witness.transfer.samples,
            carriers_cyc_um=witness.carriers,
            modulation=witness.modulation,
        )


def execute(args: argparse.Namespace, before_witness: Callable[[], None] | None = None) -> int:
    """Keep actual records live across the public-to-observer phase boundary."""
    output = args.output
    try:
        output.mkdir()
    except OSError as failure:
        print(f"{args.case} destination: {type(failure).__name__}: {failure}", file=sys.stderr)
        return 1

    stage, wiener = "public-inputs", BASE_WIENER
    receipts: dict[float, dict[str, Any]] = {}
    scored: list[float] = []
    with (output / "progress.jsonl").open("x", encoding="utf-8") as progress:

        def event(kind: str, **details: Any) -> None:
            value = dict(case=args.case, event=kind, stage=stage, wiener=wiener, **details)
            print(json.dumps(value, allow_nan=False), file=progress, flush=True)

        try:
            event("start")
            paths = {role: args.input / name for role, name in PUBLIC_FILES.items()}
            public = PublicInputs.bind(args.case, paths) if args.sweep else None
            specimen, settings = (
                normal_arguments(args.case, paths)
                if public is None
                else (public.specimen, public.workflow_kwargs())
            )
            stage = "reconstruct_workflow"
            event("start")
            workflow = reconstruct_workflow(specimen, **settings)
            records = {BASE_WIENER: workflow.reconstructions[0]}
            stage = "write-observation"
            receipts[BASE_WIENER] = filter_receipt(
                records[BASE_WIENER], save_observation(output, BASE_WIENER, workflow)
            )
            event("saved", archive=observation_name(BASE_WIENER), receipt=receipts[BASE_WIENER])

            witness = None
            replay_identities = None
            replay_receipt = None
            if public is not None:
                stage = "StageWitness.start"
                event("start")
                witness = StageWitness.start(public, workflow)
                stage = "write-fixed-factors"
                event("start")
                save_factors(output, witness)
                event("saved", archive="fixed-factors.npz", receipt=witness.fixed_metadata())
                for wiener in (BASE_WIENER, *(value for value in WIENERS if value != BASE_WIENER)):
                    stage = "stage-arguments"
                    event("start")
                    positional, keywords = witness.stage_arguments(wiener)
                    stage = "reconstruct_known"
                    event("start")
                    known = reconstruct_known(*positional, **keywords)
                    stage = "fixed-factor-fingerprints"
                    witness.fixed_metadata()
                    if wiener == BASE_WIENER:
                        stage = "check_default_replay"
                        replay_identities = check_default_replay(workflow, known)
                        replay_receipt = {
                            "resolved_settings": dict(known.resolved_settings),
                            "radial_cutoff_cyc_um": known.radial_cutoff_cyc_um,
                            "axial_cutoffs_bins": known.axial_cutoffs_bins.tolist(),
                        }
                        event("passed", identities=replay_identities, receipt=replay_receipt)
                        del known
                    else:
                        records[wiener] = known
                        stage = "write-observation"
                        receipts[wiener] = filter_receipt(
                            known, save_observation(output, wiener, known)
                        )
                        event("saved", archive=observation_name(wiener), receipt=receipts[wiener])

            stage, wiener = "write-runtime-receipt", None
            primary = records[BASE_WIENER]
            fit = (
                witness.fixed_metadata()
                if witness
                else {
                    "carriers_cyc_um": primary.carriers_cyc_um.tolist(),
                    "modulation_re_im": np.stack(
                        [primary.modulation.real, primary.modulation.imag], axis=-1
                    ).tolist(),
                }
            )
            write_json(
                output / "runtime.json",
                {
                    "case": args.case,
                    "image_axes": "zyx",
                    "image_unit": workflow.intensity_unit,
                    "image_semantics": workflow.intensity_semantics,
                    "coordinate_unit": "um",
                    "public_files": {role: digest(path) for role, path in paths.items()},
                    "workflow_settings": dict(workflow.resolved_settings),
                    "source_declarations": dict(workflow.source_declarations),
                    "fit_branches": workflow.parameters.branches,
                    "fixed_factors": fit,
                    "default_replay": replay_identities,
                    "default_replay_returned": replay_receipt,
                    "workflow_effective_wiener": workflow.effective_wiener.tolist(),
                    "observations": {
                        observation_name(value): receipt
                        for value, receipt in sorted(receipts.items())
                    },
                },
            )
            event("public-complete")

            # The observer first opens its references here. All product calls are finished.
            if args.observe and public is not None and witness is not None:
                stage = "witness-admission"
                event("start")
                if before_witness is not None:
                    before_witness()
                stage = "Inputs.bind_evaluator"
                event("start")
                evaluator_paths = {
                    "truth": args.input / "truth.npy",
                    "conventional": args.input / "conventional.npy",
                }
                if args.case == "cell":
                    evaluator_paths["reference_table"] = args.reference_table
                inputs = Inputs.bind_evaluator(public, evaluator_paths)
                stage = "reference-metrics"
                case_metadata = inputs.reference_metrics()
                case_metadata["fixed_factors"] = witness.fixed_metadata()
                case_metadata["default_replay"] = replay_identities
                with (output / "rows.jsonl").open("x", encoding="utf-8") as rows:
                    for wiener in WIENERS:
                        stage = "check_row"
                        event("start")
                        row, _ = witness.check_row(inputs, wiener, records[wiener])
                        row["provenance"] = {
                            "kind": "measured",
                            "public_call": (
                                "reconstruct_workflow"
                                if wiener == BASE_WIENER
                                else "reconstruct_known"
                            ),
                        }
                        print(json.dumps(row, allow_nan=False), file=rows, flush=True)
                        scored.append(wiener)
                        event("passed")
                if args.case == "beads":
                    stage, wiener = "bead-default-score", BASE_WIENER
                    images = {
                        "truth": inputs.truth,
                        "same_dose_conventional": inputs.conventional,
                        "reconstruction": records[BASE_WIENER].image[0] * SCORE_GAIN_SU_PER_COUNT,
                    }
                    write_json(
                        output / "bead-default-score.json",
                        {
                            "receipt_sha256": receipts[BASE_WIENER]["sha256"],
                            "comparison": {
                                name: {"metrics": bead_scores(image)}
                                for name, image in images.items()
                            },
                            "status": 0,
                        },
                    )
                stage, wiener = "write-case-metadata", None
                write_json(output / "case.json", case_metadata)
            stage, wiener = "complete", None
            event("complete", observations=sorted(receipts), scored=scored)
        except Exception as failure:
            event(
                "failed",
                error_type=type(failure).__name__,
                message=str(failure),
                product_stage=getattr(failure, "stage", None),
                product_code=getattr(failure, "code", None),
                time_index=getattr(failure, "time_index", None),
                direction_index=getattr(failure, "direction_index", None),
                observations=sorted(receipts),
                scored=scored,
            )
            print(
                f"{args.case} {stage} {wiener}: {type(failure).__name__}: {failure}",
                file=sys.stderr,
            )
            return 1
    return 0


def arguments() -> argparse.Namespace:
    """Parse the closed study protocol and its separate observer switch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("input", type=Path, help="exact generated case directory")
    parser.add_argument("output", type=Path, help="new output directory with an existing parent")
    parser.add_argument("--sweep", action="store_true", help="run the five fixed Wiener values")
    parser.add_argument("--observe", action="store_true", help="score after all public calls")
    parser.add_argument("--reference-table", type=Path, help="exact evaluator-only cell table")
    args = parser.parse_args()
    if args.sweep and args.case not in ("beads", "cell"):
        parser.error("--sweep requires beads or cell")
    if args.observe and not args.sweep:
        parser.error("--observe requires --sweep")
    if args.reference_table is not None and not (args.observe and args.case == "cell"):
        parser.error("--reference-table requires the cell observer")
    if args.reference_table is None:
        args.reference_table = HERE / "noisy-reference-table.npy"
    return args


if __name__ == "__main__":
    raise SystemExit(execute(arguments()))
