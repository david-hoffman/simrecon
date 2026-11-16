"""FA120 PUBLIC FIXTURE WRITER SOURCE PROPOSAL, qualification process only.

No syntax/import/runtime/numerical qualification is established. Only a later
independently reviewed ROOT-bound revision may remove this unconditional hold.
No argument, environment variable or grant can enable this source revision.
"""

raise SystemExit("FA120 UNCONDITIONAL EXECUTION HOLD: PUBLIC FIXTURE SOURCE ONLY")

import hashlib
import json
from pathlib import Path

import numpy as np

from simrecon import prepare_acquisition_bands, reconstruct_known
from reconstruction_summary_fixture import identity, workload


ACTUAL_119_PARENT = "UNBOUND"
ACTUAL_CANDIDATE = "UNBOUND"
ACTUAL_MATERIAL = "UNBOUND"
ACTUAL_ENVIRONMENT = "UNBOUND"
ACTUAL_GRANT = "UNBOUND"
PUBLIC_NUMERICAL_QUALIFICATION = "UNBOUND"
FIXTURE_ROOT = "UNBOUND"
REFERENCE_ROOT = "UNBOUND"
CONDITIONS = {
    "Ksmall": ((1, 3, 8, 32, 32), "3d", 1),
    "Kmedium": ((1, 3, 8, 64, 64), "3d", 1),
    "K2D": ((2, 2, 1, 12, 16), "2d", 2),
}


def qualify_condition(condition):
    """One fixed public-derived fixture, in a separate future ROOT-owned process.

    No driver/parser/launcher/admission logic. Roots/source/material/authority
    must be independently rebound before future execution. Exclusive-create
    failures or partial artifacts propagate as failed evidence, without cleanup.
    """
    if condition not in CONDITIONS:
        raise ValueError("outside closed FA120 public fixture condition inventory")
    shape, mode, axial = CONDITIONS[condition]
    # EXACT event1 generation/settings. No private validation/filter setup.
    case = workload(shape, search=False, mode=mode, layout="radial")
    case["acquisition"]["axial_zoom"] = axial
    before_preparation = {
        "specimen": identity(case["specimen"], "specimen"),
        "transfer": identity(case["transfer"].samples, "transfer.samples"),
    }
    acquisition = dict(case["acquisition"])
    del acquisition["phase_policy"]
    bands = prepare_acquisition_bands(case["specimen"], **acquisition)
    after_preparation = {
        "specimen": identity(case["specimen"], "specimen"),
        "transfer": identity(case["transfer"].samples, "transfer.samples"),
    }
    if before_preparation != after_preparation:
        raise RuntimeError("FA120 public preparation changed a caller identity")
    directions = shape[1]
    angles = np.arange(directions, dtype=np.float64) * np.pi / directions
    carriers = np.column_stack((np.cos(angles), np.sin(angles))) / 8
    modulation = np.empty((directions, 2), dtype=np.complex128)
    for d in range(directions):
        modulation[d] = np.array([0.5 + 0.25j, 0.25 - 0.125j]) * (1 + d / 16)
    before_known = {
        **after_preparation,
        "bands": identity(bands.quadratures, "bands.quadratures"),
        "noise": identity(bands.noise_variance_factors, "bands.noise_variance_factors"),
        "carriers": identity(carriers, "supplied.carriers"),
        "modulation": identity(modulation, "supplied.modulation"),
    }
    known = reconstruct_known(
        bands,
        case["transfer"],
        carriers_cyc_um=carriers,
        modulation=modulation,
        **case["optics"],
        **case["filtering"],
    )
    after_known = {
        "specimen": identity(case["specimen"], "specimen"),
        "transfer": identity(case["transfer"].samples, "transfer.samples"),
        "bands": identity(bands.quadratures, "bands.quadratures"),
        "noise": identity(bands.noise_variance_factors, "bands.noise_variance_factors"),
        "carriers": identity(carriers, "supplied.carriers"),
        "modulation": identity(modulation, "supplied.modulation"),
    }
    if before_known != after_known:
        raise RuntimeError("FA120 public known reconstruction changed a caller identity")

    # CE06 public AcquisitionBands.input_scale is the exposed alpha scalar,
    # NOT a resolved-settings guess or the private _UsedBands.scale alias.
    # The other fields below are actual exposed acquisition declarations.
    metadata = {
        "grid_shape": bands.input_shape,
        "orders": acquisition["norders"],
        "lateral_zoom": bands.lateral_zoom,
        "axial_zoom": bands.axial_zoom,
        "dxy_um": bands.dxy_um,
        "dz_um": bands.dz_um,
        "input_scale": bands.input_scale,
        "acquisition_mode": bands.acquisition_mode,
        "omit_order0": False,
        "explode_factor": 1.0,
    }
    fixture_directory = Path(FIXTURE_ROOT) / condition
    reference_directory = Path(REFERENCE_ROOT) / condition
    # ROOT binds distinct fresh roots. Neither directory may already exist.
    # Any later failure leaves all completed/partial files as failed evidence.
    fixture_directory.mkdir(parents=True, exist_ok=False)
    reference_directory.mkdir(parents=True, exist_ok=False)
    file_identities = {}
    for basename, name, array in (
        ("filtered.npy", "filtered", known.filtered_quadratures),
        ("carriers.npy", "carriers", known.carriers_cyc_um),
        ("x_um.npy", "x_um", known.x_um),
        ("y_um.npy", "y_um", known.y_um),
    ):
        path = fixture_directory / basename
        with path.open("xb") as output:
            np.save(output, array, allow_pickle=False)
        loaded = np.load(path, allow_pickle=False)
        # Qualification observations only, not a general artifact validator.
        # Complete bytes are compared; canonical hashes alone are not equality.
        if (
            loaded.shape != array.shape
            or loaded.dtype != array.dtype
            or loaded.tobytes(order="C") != array.tobytes(order="C")
        ):
            raise RuntimeError("FA120 public fixture NPY reload mismatch")
        file_identities[basename] = {
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "public_array_identity": identity(array, name),
            "reloaded_array_identity": identity(loaded, name),
            "public_strides": array.strides,
            "public_c_contiguous": bool(array.flags.c_contiguous),
            "public_owns_data": bool(array.flags.owndata),
            "public_writeable": bool(array.flags.writeable),
            "reload_strides": loaded.strides,
            "reload_c_contiguous": bool(loaded.flags.c_contiguous),
            "reload_owns_data": bool(loaded.flags.owndata),
            "reload_writeable": bool(loaded.flags.writeable),
            "complete_reload_byte_equality": True,
        }
        del loaded
    grid_path = fixture_directory / "grid.json"
    with grid_path.open("x", encoding="utf-8") as output:
        json.dump(metadata, output, sort_keys=True, separators=(",", ":"), allow_nan=False)
        output.write("\n")
    with grid_path.open(encoding="utf-8") as source:
        reloaded_metadata = json.load(source)
    # JSON's six-int shape list is the child protocol; all scalars are public.
    expected_metadata = dict(metadata)
    expected_metadata["grid_shape"] = list(bands.input_shape)
    if reloaded_metadata != expected_metadata:
        raise RuntimeError("FA120 public grid JSON reload mismatch")
    file_identities["grid.json"] = {
        "file_sha256": hashlib.sha256(grid_path.read_bytes()).hexdigest(),
        "input_scale_provenance": "public AcquisitionBands.input_scale",
        "metadata": reloaded_metadata,
        "exact_fixed_metadata_reload_equality": True,
    }

    # COMPLETE public image is stored ONLY under the distinct reference root.
    # The measured child loads none of these reference/qualification records.
    image_path = reference_directory / "public_image.npy"
    with image_path.open("xb") as output:
        np.save(output, known.image, allow_pickle=False)
    loaded_image = np.load(image_path, allow_pickle=False)
    if (
        loaded_image.shape != known.image.shape
        or loaded_image.dtype != known.image.dtype
        or loaded_image.tobytes(order="C") != known.image.tobytes(order="C")
    ):
        raise RuntimeError("FA120 complete public image NPY reload mismatch")
    reference_image_identity = identity(known.image, "image")
    reloaded_image_identity = identity(loaded_image, "image")
    del loaded_image
    provenance = {
        "status": "OBSERVATION_ONLY_NOT_ACCEPTANCE",
        "condition": condition,
        "actual119_parent": ACTUAL_119_PARENT,
        "candidate": ACTUAL_CANDIDATE,
        "material": ACTUAL_MATERIAL,
        "environment": ACTUAL_ENVIRONMENT,
        "grant": ACTUAL_GRANT,
        "public_numerical_qualification": PUBLIC_NUMERICAL_QUALIFICATION,
        "fixture_directory": str(fixture_directory),
        "reference_directory": str(reference_directory),
        "before_preparation": before_preparation,
        "after_preparation": after_preparation,
        "before_known": before_known,
        "after_known": after_known,
        "acquisition_settings": acquisition,
        "optics": case["optics"],
        "filtering": case["filtering"],
        "measured_input_files": file_identities,
        "public_image_file": str(image_path),
        "public_image_file_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "public_image_identity": reference_image_identity,
        "reloaded_image_identity": reloaded_image_identity,
        "public_image_strides": known.image.strides,
        "public_image_owns_data": bool(known.image.flags.owndata),
        "public_image_writeable": bool(known.image.flags.writeable),
        "public_image_complete_reload_byte_equality": True,
        "public_z_identity": identity(known.z_um, "z_um"),
        "public_modulation_identity": identity(known.modulation, "modulation"),
        "public_source_revision": known.source_revision,
        "public_reference_sha256": known.reference_sha256,
        "baseline_kernel_public_image_comparison": "PENDING_SEPARATE_ROOT_REVIEWED_COMPARISON",
        "independent_equations": "UNCHANGED_W1_W4_NOT_SUPPLIED_BY_PUBLIC_SELF_AGREEMENT",
        "scope": "separate fixture qualification; all memory/time includes generation/public reconstruction/archive; no measured kernel claim",
    }
    provenance_path = reference_directory / "provenance.json"
    with provenance_path.open("x", encoding="utf-8") as output:
        json.dump(provenance, output, sort_keys=True, separators=(",", ":"), allow_nan=False)
        output.write("\n")
    print(json.dumps({
        "condition": condition,
        "status": "OBSERVATION_ONLY_NOT_ACCEPTANCE",
        "provenance_path": str(provenance_path),
        "provenance_file_sha256": hashlib.sha256(provenance_path.read_bytes()).hexdigest(),
    }, sort_keys=True), flush=True)
    return None


# No __main__, three-condition driver, parser, launcher or executable authority.
# PENDING existing ROOT apparatus target: qualify_condition(ONE_FIXED_CONDITION).
