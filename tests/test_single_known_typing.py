"""Public facade, dataclass schema, signature and static return selection."""

from __future__ import annotations

import inspect
from dataclasses import fields
from typing import TYPE_CHECKING, Literal, assert_type

import numpy as np
from numpy.typing import NDArray

import simrecon as sr
from simrecon.reconstruction.known_parameters import (
    KnownReconstruction,
    ReconstructionError,
    reconstruct_known,
)
from simrecon.reconstruction.single_known import (
    KnownReconstruction32,
    PreparedBands32,
    declare_prepared_bands32,
)

from .single_known_fixture import BAND_FIELDS, RESULT_FIELDS, call, declare


def test_facade_defining_module_identity_and_exact_record_fields() -> None:
    # Exact set/cardinality/names/callability belongs to the stronger existing
    # module-migration test. This keeper adds canonical defining-module identity.
    assert sr.PreparedBands32 is PreparedBands32
    assert sr.KnownReconstruction32 is KnownReconstruction32
    assert sr.declare_prepared_bands32 is declare_prepared_bands32
    assert sr.reconstruct_known is reconstruct_known
    assert sr.ReconstructionError is ReconstructionError
    assert tuple(field.name for field in fields(PreparedBands32)) == BAND_FIELDS
    assert tuple(field.name for field in fields(KnownReconstruction32)) == RESULT_FIELDS
    assert not issubclass(KnownReconstruction32, KnownReconstruction)
    assert type(declare()) is PreparedBands32
    assert type(call()) is KnownReconstruction32
    retired = ("reconstruct", "reconstruct_volume", "prepare_otf")
    assert all(not hasattr(sr, name) for name in retired)


def test_exact_keyword_only_public_signatures_and_defaults() -> None:
    reconstruction = inspect.signature(reconstruct_known)
    names = tuple(reconstruction.parameters)
    assert names == (
        "bands", "transfer", "carriers_cyc_um", "modulation", "wavelength_nm",
        "numerical_aperture", "immersion_index", "wiener", "suppress_singularities",
        "suppression_radius_bins", "dampen_order0", "omit_order0", "omit_kz0",
        "output_taper", "wiener_increment", "power_taper_exponent", "precise_taper",
        "filter_overlaps", "explode_factor", "precision",
    )
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in list(reconstruction.parameters.values())[2:])
    assert reconstruction.parameters["precision"].default == "double"
    declaration = inspect.signature(declare_prepared_bands32)
    assert tuple(declaration.parameters) == (
        "quadratures", "noise_variance_factors", "input_shape", "dxy_um", "dz_um",
        "lateral_zoom", "axial_zoom", "mapping_revision", "provenance",
    )
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in list(declaration.parameters.values())[2:])
    assert declaration.parameters["mapping_revision"].default == "ce04-svn307-v1"
    assert declaration.parameters["provenance"].default == ()


if TYPE_CHECKING:
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
        omitted = sr.reconstruct_known(old, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5)
        explicit = sr.reconstruct_known(old, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=double_literal)
        acquired = sr.reconstruct_known(acquisition, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision="double")
        mixed = sr.reconstruct_known(single, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=single_literal)
        runtime = sr.reconstruct_known(single, optical_transfer, carriers_cyc_um=carriers,
            modulation=modulation, wavelength_nm=500, numerical_aperture=1.0,
            immersion_index=1.0, wiener=0.5, precision=selected)
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
