"""CE04 raw composition, literal rows, finite inverse and output ownership."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from c_known_fixture import (
    SETTINGS,
    SOURCE,
    assemble,
    bands_from,
    blank,
    compare,
    expectation,
    known,
    public,
    raw_quadratures,
    table,
)


def test_normal_three_direction_five_phase_raw_to_image() -> None:
    raw = (2 + np.arange(2 * 3 * 5 * 6 * 4 * 4).reshape(2, 3, 5, 6, 4, 4) % 29).astype(np.float32)
    b = bands_from(raw, 3, lateral_zoom=2, axial_zoom=2)
    independent = raw_quadratures(raw, 3, 1 / (4 * 4 * 6 * 4 * 2 * 3))
    assert_allclose(b.quadratures, independent, rtol=2e-10, atol=2e-10)
    carrier = np.array([[0.125, -0.125], [-0.1875, 0.0625], [0, 0.25]])
    options = dict(
        carriers_cyc_um=carrier,
        modulation=np.array([[0.5 + 0.25j, -0.5], [0.75, 0.5j], [-0.5j, 0.25]]),
        suppress_singularities=True,
        output_taper="cosine",
    )
    transfer = table(3, "full")
    fq, image, budget = expectation(b, transfer, original=independent, **options)
    result = known(b, transfer, **options)
    assert_allclose(result.filtered_quadratures, fq, rtol=2e-10, atol=2e-10)
    assert_allclose(result.image, image, rtol=3e-10, atol=3e-10 * max(1, budget))
    assert result.image.shape == (2, 12, 8, 8)


@pytest.mark.parametrize("phases,orders", [(4, 2), (6, 3)])
def test_reduced_order_even_phase_raw_composition_is_permitted(phases: int, orders: int) -> None:
    raw = (2 + np.arange(2 * phases * 4 * 2 * 4).reshape(1, 2, phases, 4, 2, 4) % 17).astype(
        np.float32
    )
    b = bands_from(raw, orders)
    independent = raw_quadratures(raw, orders, 1 / (4 * 2 * 4 * 2))
    assert_allclose(b.quadratures, independent, rtol=2e-10, atol=2e-10)
    transfer = table(orders)
    options = dict(
        carriers_cyc_um=np.array([[0.125, -0.0625], [-0.1875, 0.125]]),
        modulation=np.full((2, orders - 1), 0.5 + 0.25j),
    )
    fq, image, budget = expectation(b, transfer, original=independent, **options)
    r = known(b, transfer, **options)
    assert_allclose(r.filtered_quadratures, fq, rtol=2e-10, atol=2e-10)
    assert_allclose(r.image, image, rtol=3e-10, atol=3e-10 * max(1, budget))


@pytest.mark.parametrize("lateral,axial", [(1, 1), (2, 3), (3, 2)])
def test_raw_constant_preserves_declared_scale_and_unnormalized_inverse(
    lateral: int, axial: int
) -> None:
    raw = np.full((2, 3, 5, 6, 4, 4), 8, np.float32)
    b = bands_from(raw, 3, lateral_zoom=lateral, axial_zoom=axial)
    result = known(b, table(3, constant=True), modulation=np.zeros((3, 2)))
    # Each center DC=5*8/(L²*A*3); all three center powers contribute.
    expected = 40 / (lateral**2 * axial * (3 + 0.25))
    assert_allclose(result.image, expected, rtol=2e-12, atol=2e-12)


def test_displaced_raw_impulse_amplitude_and_unseparated_nyquist() -> None:
    raw = np.zeros((1, 1, 3, 4, 2, 4), np.float32)
    raw[:, :, :, 1, 1, 1] = 32
    b = bands_from(raw, 2, lateral_zoom=2, axial_zoom=2)
    iq = raw_quadratures(raw, 2, 1 / (4 * 2 * 4 * 4 * 2))
    assert_allclose(iq[0, 0, :, 0, 0, 0], [3 / 8, 0, 0], atol=2e-12)
    assert_allclose(iq[0, 0, :, 0, 0, 2], [-1 / 8] * 3, atol=2e-12)
    transfer = table(constant=True)
    fq, image, budget = expectation(b, transfer, original=iq, modulation=np.zeros((1, 1)))
    result = known(b, transfer, modulation=np.zeros((1, 1)))
    assert_allclose(result.filtered_quadratures, fq, rtol=2e-10, atol=2e-10)
    assert_allclose(result.image, image, rtol=3e-10, atol=3e-10 * max(1, budget))


def test_raw_bead_prepared_transfer_to_raw_specimen_image() -> None:
    # Interior delta is untouched by the fixed width10 bead edge operation.
    raw_bead = np.zeros((3, 6, 24, 24), np.float32)
    raw_bead[:, 2, 12, 12] = [12, 4, 4]
    prepared = public("prepare_bead_otf")(
        raw_bead,
        dxy_um=0.25,
        dz_um=0.3,
        linespacing_um=1,
        wavelength_nm=520,
        background_counts=0,
        compensate_bead=False,
        fix_axial_axis=False,
        fix_radial_from=0,
        cleanup_axial_bins=(0, 0, 0),
    )
    assert_allclose(prepared.transfer.samples[0], 1, rtol=2e-10, atol=2e-10)
    assert_allclose(prepared.transfer.samples[1], 0.4, rtol=2e-10, atol=2e-10)
    raw = np.full((1, 1, 3, 6, 4, 4), 8, np.float32)
    result = known(bands_from(raw), prepared.transfer)
    # H0=1 and two side powers .4²; raw B0=24.
    assert_allclose(result.image, 24 / (1 + 2 * 0.4**2 + 0.25), rtol=2e-10, atol=2e-10)


@pytest.mark.parametrize("ny,na", [(1, 0.8), (3, 0.8), (5, 0.8), (3, 0.2), (5, 0.2)])
def test_odd_y_omitted_row_keeps_values_except_reflected_partial_zeros(ny: int, na: float) -> None:
    b = blank(shape=(1, 1, 3, 6, ny, 4), lateral_zoom=2, axial_zoom=2)
    indices = np.indices(b.quadratures.shape)
    b.quadratures[:] = 1 + indices[3] / 4 + indices[4] / 8 + 1j * (indices[5] + 1)
    before = b.quadratures.copy()
    result = compare(
        b, table(), carriers_cyc_um=np.array([[0.1875, -0.125]]), numerical_aperture=na
    )
    omitted = (-(ny // 2)) % ny
    assert_array_equal(
        result.filtered_quadratures[0, 0, 0, :, omitted], before[0, 0, 0, :, omitted]
    )
    if ny == 1:
        assert_array_equal(result.filtered_quadratures, before)
    else:
        # Reflected x=-1 visit writes into the omitted row, but x=0 is
        # never addressed there. Its side slots remain exactly unchanged.
        assert_array_equal(
            result.filtered_quadratures[0, 0, 1:, :, omitted, 0], before[0, 0, 1:, :, omitted, 0]
        )
        assert_array_equal(result.filtered_quadratures[0, 0, 1:, 2:5, omitted, 1], 0)
        if na == 0.2:
            assert_array_equal(result.filtered_quadratures[0, 0, 1:, :, omitted, 1], 0)
        assert_array_equal(
            result.filtered_quadratures[0, 0, 1:, :, omitted, 2], before[0, 0, 1:, :, omitted, 2]
        )


def test_y1_empty_traversal_permits_requested_zero_cutoff_damping() -> None:
    b = bands_from(np.ones((1, 1, 3, 2, 1, 2), np.float32))
    before = b.quadratures.copy()
    # Consume actual finite CE02 operands, including any phase-row residuals.
    finite_image, _ = assemble(before, b, np.zeros((1, 2)))
    assert_allclose(finite_image, 3, rtol=2e-12, atol=2e-12)
    # This valid all-zero table has no safe radial query at all. No query occurs.
    transfer = public("declare_otf")(
        np.zeros((2, 1, 1), np.complex64), layout="radial", dkr_cyc_um=1, dkz_cyc_um=1
    )
    result = known(b, transfer, modulation=np.zeros((1, 1)), dampen_order0=True)
    assert_array_equal(result.axial_cutoffs_bins, [0, 0])
    assert_array_equal(result.filtered_quadratures, before)
    assert_array_equal(b.quadratures, before)
    assert_allclose(result.image, finite_image, rtol=2e-12, atol=2e-12)


def test_all_axis_reflection_and_positive_nyquist_embedding_have_closed_modes() -> None:
    b = blank(shape=(1, 1, 3, 2, 1, 4), lateral_zoom=2, axial_zoom=2)
    # Y1 leaves every diagnostic unchanged; this isolates assembly reflection.
    b.quadratures[0, 0, 0, 1, 0, 1] = 1 + 2j
    b.quadratures[0, 0, 0, 0, 0, 2] = 3 + 1j
    r = known(b, table(constant=True), modulation=np.zeros((1, 1)))
    z, _, x = np.indices((4, 2, 8))
    # Negative x coefficient reflects z too. Native positive z Nyquist
    # stays at positive output z for both stored/native reflected reads.
    expected = (
        (2 * np.cos(2 * np.pi * x / 8) - 4 * np.sin(2 * np.pi * x / 8))
        * (np.cos(2 * np.pi * z / 4))
        + 3 * np.cos(2 * np.pi * 2 * x / 8)
        - np.sin(2 * np.pi * 2 * x / 8)
    )
    assert_allclose(r.image[0], expected, rtol=2e-12, atol=2e-12)


def test_noninteger_centered_carrier_closed_mode_with_anisotropic_spacing() -> None:
    b = blank(shape=(1, 1, 3, 4, 1, 4), lateral_zoom=3, axial_zoom=2, dz_um=0.7)
    b.quadratures[0, 0, 1, 1, 0, 1] = 0.5 + 0.25j
    b.quadratures[0, 0, 2, 1, 0, 1] = 0.25 - 0.5j
    carrier = np.array([[0.1875, -0.0625]])
    r = known(b, table(), carriers_cyc_um=carrier)
    z, y, x = np.indices((8, 3, 12))
    centered_x = (x - 6) / 6
    centered_y = (y - 1) / 6
    phase = 2 * np.pi * (z / 8 + x / 12 + 0.1875 * centered_x - 0.0625 * centered_y)
    assert_allclose(r.image[0], 2 * (np.cos(phase) - 0.5 * np.sin(phase)), atol=2e-12, rtol=2e-12)
    assert np.min(r.image) < -1


def test_nonendpoint_axial_and_y_reflection_closed_omitted_row_mode() -> None:
    b = blank(shape=(1, 1, 3, 4, 3, 4), lateral_zoom=2, axial_zoom=2)
    # Center order's omitted row y=-1 stays unchanged. The negative-x
    # read must reflect z and y as well, giving the opposite full mode.
    b.quadratures[0, 0, 0, 1, 2, 1] = 1 + 2j
    r = known(b, table(constant=True), modulation=np.zeros((1, 1)))
    z, y, x = np.indices((8, 6, 8))
    phase = 2 * np.pi * (z / 8 - y / 6 + x / 8)
    assert_allclose(r.image[0], 2 * np.cos(phase) - 4 * np.sin(phase), rtol=2e-12, atol=2e-12)
    assert r.filtered_quadratures[0, 0, 0, 1, 2, 1] == 1 + 2j


def test_supplied_phase_raw_delta_composes_unequal_noise_to_known_image() -> None:
    raw = np.zeros((1, 1, 5, 6, 4, 4), np.float32)
    amplitudes = np.array([8, 16, 4, 12, 20])
    raw[0, 0, :, 1, 1, 1] = amplitudes
    phases = np.array([[0, np.pi / 2, np.pi, 3 * np.pi / 2, np.pi / 4]])
    b = bands_from(raw, 3, phases_rad=phases)
    z, y, x = np.indices((6, 4, 3))
    kernel = np.exp(-2j * np.pi * (z / 6 + y / 4 + x / 4)) / 96
    separated = np.array([50, 5, 5, -10, 25 - 5 * np.sqrt(2)])
    independent = separated[None, None, :, None, None, None] * kernel
    independent[0, 0, :, :, :, 2] = amplitudes[:, None, None] * kernel[:, :, 2]
    assert_allclose(b.quadratures, independent, rtol=2e-10, atol=2e-10)
    assert_allclose(b.noise_variance_factors, [[1.25, 1.25, 2.5]], rtol=2e-12, atol=2e-12)
    transfer = table(3)
    options = dict(
        carriers_cyc_um=np.array([[0.1875, -0.125]]), modulation=np.array([[0.5 + 0.25j, -0.5j]])
    )
    # Use independently specified variance, not product-returned noise, as
    # the expectation's input. Only the documented writable field changes.
    expected_bands = bands_from(np.zeros_like(raw), 3)
    expected_bands.noise_variance_factors[:] = [[1.25, 1.25, 2.5]]
    fq, image, budget = expectation(expected_bands, transfer, original=independent, **options)
    r = known(b, transfer, **options)
    assert_allclose(r.filtered_quadratures, fq, rtol=2e-10, atol=2e-10)
    assert_allclose(r.image, image, rtol=3e-10, atol=3e-10 * max(1, budget))


def test_metadata_source_coordinates_frozen_owned_readonly_and_input_immutability() -> None:
    b = blank(3, shape=(2, 2, 5, 6, 3, 4), lateral_zoom=2, axial_zoom=3)
    b.quadratures[:] = 0.25 + 0.5j
    q, v = b.quadratures.copy(), b.noise_variance_factors.copy()
    transfer = table(4)
    ts = transfer.samples.copy()
    carriers = np.array([[0.125, -0.25], [0.25, 0.0625]], dtype=np.float32)
    mods = np.array([[0.5j, 0], [-1, 0.75]], dtype=np.complex64)
    c0, a0 = carriers.copy(), mods.copy()
    r = compare(
        b,
        transfer,
        carriers_cyc_um=carriers,
        modulation=mods,
        suppress_singularities=True,
        output_taper="cosine",
    )
    assert isinstance(r, public("KnownReconstruction"))
    assert r.source_revision == "SVN307"
    assert r.reference_sha256 == SOURCE
    expected_settings = SETTINGS | {"suppress_singularities": True, "output_taper": "cosine"}
    expected_settings.update(
        dxy_um=0.5, dz_um=0.3, lateral_zoom=2, axial_zoom=3, input_scale=1 / (4 * 3 * 6 * 4 * 3 * 2)
    )
    assert r.resolved_settings == tuple(expected_settings.items())
    assert r.radial_cutoff_cyc_um == 1
    arrays = [
        r.image,
        r.filtered_quadratures,
        r.x_um,
        r.y_um,
        r.z_um,
        r.carriers_cyc_um,
        r.modulation,
        r.axial_cutoffs_bins,
    ]
    for output in arrays:
        assert output.flags.owndata
        assert not output.flags.writeable
        for original in (b.quadratures, b.noise_variance_factors, transfer.samples, carriers, mods):
            assert not np.shares_memory(output, original)
        with pytest.raises(ValueError):
            output.flat[0] = 0
    assert r.image.dtype == np.float64
    assert r.filtered_quadratures.dtype == np.complex128
    assert r.carriers_cyc_um.dtype == np.float64
    assert r.modulation.dtype == np.complex128
    assert np.issubdtype(r.axial_cutoffs_bins.dtype, np.integer)
    for vector, n, pitch in [(r.x_um, 8, 0.25), (r.y_um, 6, 0.25), (r.z_um, 18, 0.1)]:
        assert vector.dtype == np.float64
        assert_allclose(vector, (np.arange(n) - n // 2) * pitch, rtol=2e-12, atol=2e-12)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        r.image = np.zeros_like(r.image)
    assert_array_equal(b.quadratures, q)
    assert_array_equal(b.noise_variance_factors, v)
    assert_array_equal(transfer.samples, ts)
    assert_array_equal(carriers, c0)
    assert_array_equal(mods, a0)
    b.quadratures[:] = 0
    carriers[:] = 0
    mods[:] = 0
    assert_array_equal(r.carriers_cyc_um, c0)
    assert_array_equal(r.modulation, a0)


def test_independent_finite_sum_oracle_closed_constant_and_displaced_modes() -> None:
    # Oracle-only anchors do not depend on new or existing product code.
    raw = np.full((1, 1, 3, 2, 1, 4), 8, dtype=np.float32)
    q = raw_quadratures(raw, 2, 1 / 8)
    assert_allclose(q[0, 0, :, 0, 0, 0], [24, 0, 0], atol=2e-12)
    sampling = SimpleNamespace(lateral_zoom=2, axial_zoom=2, dxy_um=0.5)
    c = np.zeros_like(q)
    c[0, 0, 0, 0, 0, 0] = 0.8
    image, _ = assemble(c, sampling, np.zeros((1, 2)))
    assert_array_equal(image, 0.8)
    raw[:] = 0
    raw[:, :, :, 1, 0, 1] = 8
    q = raw_quadratures(raw, 2, 1 / 8)
    assert_allclose(q[0, 0, 0, 1, 0, 1], 3j, atol=2e-12)
    assert_allclose(q[0, 0, :, 0, 0, 2], [-1, -1, -1], atol=2e-12)
