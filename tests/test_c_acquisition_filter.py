"""Known filtering variants, literal zoom, inverse dimensionality and signed views."""

from itertools import product
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    close,
    events,
    known_options,
    options,
    prepare_expected,
    raw_pattern,
    reconstruct_expected,
    transfer,
)
from c_acquisition_fixture import (
    numerical_case as numerical_case,
)


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)])
@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("zoom,axial", [(1.0, 1), (1.5, 2), (2.0, 2)])
def test_raw_known_image_fractional_embedding_dimensional_inverse(
    mode: str, z: int, layout: str, zoom: float, axial: int
) -> None:
    raw = raw_pattern(d=3, p=5, z=z, y=4, x=6)
    prep = options(acquisition_mode=mode, norders=3, lateral_zoom=zoom, axial_zoom=axial)
    bands = api("prepare_acquisition_bands")(raw, **prep)
    independent = prepare_expected(raw, prep)
    close(bands.quadratures, independent["quadratures"])
    table = transfer(3, layout=layout, k=z, complex_values=True)
    carriers = np.array([[0.09, 0.03], [-0.04, 0.08], [0.01, -0.07]])
    modulation = np.array([[0.7 + 0.2j, 0.2 - 0.1j], [0.8 - 0.2j, -0.3j], [0.3 + 0.4j, 0.6]])
    expected = reconstruct_expected(bands, table, carriers, modulation, **known_options())
    actual = api("reconstruct_known")(
        bands, table, carriers_cyc_um=carriers, modulation=modulation, **known_options()
    )
    for name in ["image", "filtered_quadratures", "x_um", "y_um", "z_um"]:
        close(getattr(actual, name), expected[name])
    cutoffs = actual.axial_cutoffs_bins
    assert isinstance(cutoffs, np.ndarray) and cutoffs.dtype.kind in "iu"
    assert cutoffs.shape == expected["axial_cutoffs_bins"].shape
    np.testing.assert_array_equal(cutoffs, expected["axial_cutoffs_bins"])
    assert not actual.image.flags.writeable and actual.image.dtype == np.float64
    if z == 1 and axial > 1:
        np.testing.assert_array_equal(actual.image[:, 1:], 0)
    assert actual.image.shape == (1, z * axial, int(4 * zoom), int(6 * zoom))
    assert dict(actual.resolved_settings)["acquisition_mode"] == mode


@pytest.mark.parametrize(
    "overlap,suppress,omit,explode",
    [
        (False, False, False, 0.0),
        (False, True, False, -0.5),
        (True, True, True, 1.25),
        (True, False, False, 1.0),
        (True, True, False, -1.0),
    ],
)
@pytest.mark.parametrize("radius", [-1.0, 0.0, 10.0])
def test_overlap_suppression_omit_and_explode_public_image(
    overlap: bool, suppress: bool, omit: bool, explode: float, radius: float
) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(d=2, y=4, x=6), **options())
    table = transfer(complex_values=True)
    carriers = np.array([[0.11, 0.03], [-0.04, 0.08]])
    modulation = np.array([[0.7 + 0.2j], [-0.4j]])
    settings = known_options(
        filter_overlaps=overlap,
        suppress_singularities=suppress,
        suppression_radius_bins=radius,
        omit_order0=omit,
        explode_factor=explode,
    )
    expected = reconstruct_expected(bands, table, carriers, modulation, **settings)
    actual = api("reconstruct_known")(
        bands, table, carriers_cyc_um=carriers, modulation=modulation, **settings
    )
    close(actual.image, expected["image"])
    close(actual.filtered_quadratures, expected["filtered_quadratures"])
    # Explode changes only the output ramp, never filtering.
    ordinary = api("reconstruct_known")(
        bands,
        table,
        carriers_cyc_um=carriers,
        modulation=modulation,
        **(settings | {"explode_factor": 1.0}),
    )
    np.testing.assert_array_equal(ordinary.filtered_quadratures, actual.filtered_quadratures)
    if explode != 1:
        assert np.max(abs(actual.image - ordinary.image)) > 1e-5


@pytest.mark.parametrize("d", [1, 2, 3])
def test_no_overlap_still_counts_other_center_orders_and_self(d: int) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(d=d, y=2, x=4), **options())
    bands.quadratures[:] = 0
    bands.quadratures[:, :, 0, 0, 0, 0] = 1
    bands.quadratures[:, :, 1, 0, 0, 0] = 1
    actual = api("reconstruct_known")(
        bands,
        transfer(),
        carriers_cyc_um=np.zeros((d, 2)),
        modulation=np.ones((d, 1)),
        **known_options(filter_overlaps=False),
    )
    close(
        actual.filtered_quadratures[:, :, 0, 0, 0, 0],
        1 / (d + 0.25),
        proof=actual.filtered_quadratures,
    )
    close(actual.filtered_quadratures[:, :, 1, 0, 0, 0], 0.8, proof=actual.filtered_quadratures)
    close(actual.image, d * (1 / (d + 0.25) + 1.6))


@pytest.mark.parametrize("increment", [0.0, 0.2, -0.1])
def test_wiener_schedule_preincrement_each_time_and_trace(increment: float) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(t=2, y=2, x=4), **options())
    bands.quadratures[:] = 0
    bands.quadratures[:, :, 0, 0, 0, 0] = 1
    settings = known_options(wiener=0.2, wiener_increment=increment, filter_overlaps=False)
    actual = api("reconstruct_known")(
        bands, transfer(), carriers_cyc_um=np.zeros((1, 2)), modulation=np.zeros((1, 1)), **settings
    )
    values = tuple(0.2 + (t + 1) * increment / 2 for t in range(2))
    close(actual.image[:, 0, 0, 0], [1 / (1 + w * w) for w in values], proof=actual.image)
    close(dict(actual.resolved_settings)["effective_wiener"], values)
    steps = events(actual, "wiener-step")
    assert len(steps) == 2
    for t, e in enumerate(steps):
        assert tuple(e) == ("previous", "increment", "effective")
        close(e["previous"], 0.2 + t * increment / 2)
        close(e["increment"], increment / 2)
        close(e["effective"], values[t])


@pytest.mark.parametrize(
    "taper,gamma",
    [
        ("none", -1.0),
        ("cosine", None),
        ("power", 0.0),
        ("power", 0.5),
        ("power", 2.0),
        ("power", -1.0),
    ],
)
def test_native_taper_power_signed_finite_branch(taper: str, gamma: Any) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=4, x=6), **options())
    # The non-axis carrier is parallel to no boundary native bin. Triangle
    # inequality is strict at every visited side sample, so base stays positive
    # and the negative exponent exercises a finite numerical branch.
    settings = known_options(output_taper=taper, power_taper_exponent=gamma)
    carriers, modulation = np.array([[0.11, 0.02]]), np.array([[0.5 + 0.2j]])
    expected = reconstruct_expected(bands, transfer(), carriers, modulation, **settings)
    actual = api("reconstruct_known")(
        bands, transfer(), carriers_cyc_um=carriers, modulation=modulation, **settings
    )
    close(actual.image, expected["image"])
    if taper == "power" and gamma == 0:
        no_taper = api("reconstruct_known")(
            bands, transfer(), carriers_cyc_um=carriers, modulation=modulation, **known_options()
        )
        np.testing.assert_array_equal(actual.image, no_taper.image)


@pytest.mark.parametrize("dampen,omit,kz", list(product([False, True], repeat=3)))
def test_zero_axial_cutoff_damping_rejected_only_when_visited(
    dampen: bool, omit: bool, kz: bool
) -> None:
    settings = known_options(dampen_order0=dampen, omit_order0=omit, omit_kz0=kz)
    for y in [1, 2]:
        bands = api("prepare_acquisition_bands")(raw_pattern(y=y, x=4), **options())
        args = dict(carriers_cyc_um=np.zeros((1, 2)), modulation=np.zeros((1, 1)))
        if dampen and y == 2:
            with pytest.raises(api("ReconstructionError"), match="(?i)damp|cutoff|zero|divis"):
                api("reconstruct_known")(bands, transfer(), **args, **settings)
        else:
            actual = api("reconstruct_known")(bands, transfer(), **args, **settings)
            assert np.isfinite(actual.image).all()


def test_fractional_power_at_visited_zero_base_and_original_record_options() -> None:
    from c_acquisition_fixture import as_disc, certified_close

    raw = raw_pattern(z=2, y=2, x=4)
    prep = options(acquisition_mode="3d")
    old = dict(prep)
    del old["acquisition_mode"]
    old["lateral_zoom"] = 1
    original = api("prepare_bands")(raw, **old)
    acquisition = api("prepare_acquisition_bands")(raw, **prep)
    carrier = np.zeros((1, 2))
    factors = np.ones((1, 1), dtype=complex)
    settings = known_options(
        output_taper="power",
        power_taper_exponent=0.5,
        filter_overlaps=False,
        explode_factor=-0.5,
        wiener_increment=0.1,
        precise_taper=False,
    )
    # At positive native x Nyquist rho=(.5)/(.5)=1: positive fractional
    # power is exactly zero, unlike exponent0 and singular negative exponent.
    for bands in [original, acquisition]:
        result = api("reconstruct_known")(
            bands, transfer(k=2), carriers_cyc_um=carrier, modulation=factors, **settings
        )
        assert result.filtered_quadratures[0, 0, 0, 0, 0, 2] == 0
        independent = prepare_expected(raw, prep)
        model = type(
            "PublicInputs",
            (),
            dict(
                quadratures=independent["quadratures"],
                noise_variance_factors=independent["noise_variance_factors"],
                input_shape=raw.shape,
                acquisition_mode="3d",
                dxy_um=1.0,
                dz_um=0.5,
                lateral_zoom=1.0,
                axial_zoom=1,
            ),
        )()
        truth = reconstruct_expected(
            model, transfer(k=2), as_disc(carrier), as_disc(factors), **settings
        )
        certified_close(result.image, truth["image"])


def test_precise_positive_options_on_original_prepared_bands() -> None:
    from types import SimpleNamespace

    from c_acquisition_fixture import as_disc, certified_close

    raw = raw_pattern(t=2, z=8, y=2, x=4)
    prep = options(acquisition_mode="3d", dz_um=2.0)
    old = prep.copy()
    del old["acquisition_mode"]
    old["lateral_zoom"] = 1
    bands = api("prepare_bands")(raw, **old)
    source = prepare_expected(raw, prep)
    independent = SimpleNamespace(
        **source,
        input_shape=raw.shape,
        acquisition_mode="3d",
        dxy_um=1.0,
        dz_um=2.0,
        lateral_zoom=1.0,
        axial_zoom=1,
    )
    carriers = as_disc(np.array([[0.1, 0.02]]))
    modulation = as_disc(np.array([[0.4 + 0.1j]]))
    table = transfer(k=8, complex_values=True)
    settings = known_options(
        numerical_aperture=1.0,
        precise_taper=True,
        output_taper="cosine",
        filter_overlaps=False,
        explode_factor=1.25,
        wiener_increment=0.2,
    )
    expected = reconstruct_expected(independent, table, carriers, modulation, **settings)
    actual = api("reconstruct_known")(
        bands,
        table,
        carriers_cyc_um=np.asarray(carriers),
        modulation=np.asarray(modulation),
        **settings,
    )
    certified_close(actual.image, expected["image"])
    assert len(events(actual, "sector-boundaries")) == 2
    assert not events(actual, "precise-query")
