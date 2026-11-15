"""Public schema/signatures and an exercised literal typed-caller proof.

New API imports occur inside their own tests or in the typed caller, so missing
pre-C entries fail those obligations without preventing legacy test collection.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from textwrap import dedent

import simrecon as sr
from simrecon.reconstruction.known_parameters import (
    KnownReconstruction,
    ReconstructionError,
    reconstruct_known,
)

from .single_known_fixture import BAND_FIELDS, RESULT_FIELDS, call, declare

ROOT = Path(__file__).resolve().parents[1]

# This is a real public caller, not a stub, Any cast, reveal_type parser or
# production annotation inspection. It becomes an ordinary pytest tmp fixture
# only under a future explicit source-free execution grant.
PUBLIC_CALLER = dedent(
    """\
    from typing import Literal, assert_type

    import numpy as np
    from numpy.typing import NDArray

    import simrecon as sr
    from simrecon.reconstruction.known_parameters import KnownReconstruction
    from simrecon.reconstruction.single_known import KnownReconstruction32, PreparedBands32


    def public_return_types(
        old: sr.PreparedBands,
        acquisition: sr.AcquisitionBands,
        single: PreparedBands32,
        optical_transfer: sr.OpticalTransfer,
        selected: str,
    ) -> None:
        carriers: NDArray[np.float64] = np.zeros((1, 2), dtype=np.float64)
        modulation: NDArray[np.complex128] = np.ones((1, 1), dtype=np.complex128)
        double_literal: Literal["double"] = "double"
        single_literal: Literal["single-mixed-v1"] = "single-mixed-v1"
        omitted = sr.reconstruct_known(
            old, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5,
        )
        explicit = sr.reconstruct_known(
            old, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=double_literal,
        )
        acquired = sr.reconstruct_known(
            acquisition, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision="double",
        )
        mixed = sr.reconstruct_known(
            single, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=single_literal,
        )
        runtime = sr.reconstruct_known(
            single, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=selected,
        )
        assert_type(omitted, KnownReconstruction)
        assert_type(explicit, KnownReconstruction)
        assert_type(acquired, KnownReconstruction)
        assert_type(mixed, KnownReconstruction32)
        assert_type(runtime, KnownReconstruction | KnownReconstruction32)
        assert_type(single.quadratures, NDArray[np.complex64])
        assert_type(single.noise_variance_factors, NDArray[np.float64])
        assert_type(single.input_shape, tuple[int, int, int, int, int, int])
        assert_type(single.input_scale, float)
        assert_type(single.dxy_um, float)
        assert_type(single.dz_um, float)
        assert_type(single.lateral_zoom, int)
        assert_type(single.axial_zoom, int)
        assert_type(mixed.image, NDArray[np.float32])
        assert_type(mixed.filtered_quadratures, NDArray[np.complex64])
        assert_type(mixed.carriers_cyc_um, NDArray[np.float64])
        assert_type(mixed.modulation, NDArray[np.complex128])
        assert_type(mixed.axial_cutoffs_bins, NDArray[np.int64])
    """
)


def test_facade_defining_module_identity_and_exact_record_fields() -> None:
    # Existing module-migration owns the stronger exact41 inventory assertion.
    single = importlib.import_module("simrecon.reconstruction.single_known")
    prepared_type = single.PreparedBands32
    result_type = single.KnownReconstruction32
    assert sr.PreparedBands32 is prepared_type
    assert sr.KnownReconstruction32 is result_type
    assert sr.declare_prepared_bands32 is single.declare_prepared_bands32
    assert sr.reconstruct_known is reconstruct_known
    assert sr.ReconstructionError is ReconstructionError
    assert tuple(field.name for field in fields(prepared_type)) == BAND_FIELDS
    assert tuple(field.name for field in fields(result_type)) == RESULT_FIELDS
    assert not issubclass(result_type, KnownReconstruction)
    assert type(declare()) is prepared_type
    assert type(call()) is result_type
    retired = ("reconstruct", "reconstruct_volume", "prepare_otf")
    assert all(not hasattr(sr, name) for name in retired)


def test_exact_keyword_only_public_signatures_and_defaults() -> None:
    reconstruction = inspect.signature(reconstruct_known)
    assert tuple(reconstruction.parameters) == (
        "bands",
        "transfer",
        "carriers_cyc_um",
        "modulation",
        "wavelength_nm",
        "numerical_aperture",
        "immersion_index",
        "wiener",
        "suppress_singularities",
        "suppression_radius_bins",
        "dampen_order0",
        "omit_order0",
        "omit_kz0",
        "output_taper",
        "wiener_increment",
        "power_taper_exponent",
        "precise_taper",
        "filter_overlaps",
        "explode_factor",
        "precision",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in list(reconstruction.parameters.values())[2:]
    )
    assert reconstruction.parameters["precision"].default == "double"
    declaration = inspect.signature(sr.declare_prepared_bands32)
    assert tuple(declaration.parameters) == (
        "quadratures",
        "noise_variance_factors",
        "input_shape",
        "dxy_um",
        "dz_um",
        "lateral_zoom",
        "axial_zoom",
        "mapping_revision",
        "provenance",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in list(declaration.parameters.values())[2:]
    )
    assert declaration.parameters["mapping_revision"].default == "ce04-svn307-v1"
    assert declaration.parameters["provenance"].default == ()


def test_retired_scientific_module_paths_remain_absent() -> None:
    for name in ("simrecon._otf", "simrecon._reconstruction"):
        assert importlib.util.find_spec(name) is None


def test_literal_public_caller_typechecks_with_actual_candidate(tmp_path: Path) -> None:
    caller = tmp_path / "single_known_public_caller.py"
    caller.write_text(PUBLIC_CALLER, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/source_free_check.py"),
            "python",
            "-m",
            "pyright",
            "--outputjson",
            "--pythonpath",
            sys.executable,
            str(caller),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["summary"]["filesAnalyzed"] >= 1
    assert report["summary"]["errorCount"] == 0
