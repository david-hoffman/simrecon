"""True 2D estimation, cumulative factors, public result provenance and controls."""

from copy import copy
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    ESTIMATE_KEYS,
    SOURCE6,
    SOURCE10,
    api,
    close,
    events,
    optics,
    options,
    overlaps,
    raw_pattern,
    regression,
    transfer,
)


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("dz", [0.0, 0.5])
@pytest.mark.parametrize("carrier", [(0.0, 0.0), (0.13, -0.07)])
def test_actual_raw_bands_known_fit_complex_overlap(
    layout: str, dz: float, carrier: tuple[float, float]
) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=4, x=6), **options(dz_um=dz))
    table = transfer(layout=layout, complex_values=True)
    vector = np.array([carrier])
    expected_overlap = overlaps(bands, table, vector[0], (0, 1), **optics())
    expected_fit = regression(expected_overlap["spatial"], vector[0], (0, 1), bands.dxy_um)
    actual = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=vector, search_carriers=False, **optics()
    )
    assert actual.branches == (("known",),)
    assert actual.axial_cutoff_bins == 0
    assert len(actual.overlaps) == 1 and actual.overlaps[0].orders == (0, 1)
    for name, value in expected_overlap.items():
        observed = getattr(actual.overlaps[0], name)
        if name == "written":
            np.testing.assert_array_equal(observed, value)
        else:
            close(
                observed, value, work=24, scale=float(np.sum(abs(bands.quadratures))), condition=32
            )
    evaluation = events(actual, "evaluation")[0]
    for name, value in expected_fit.items():
        close(
            evaluation[name],
            value,
            work=24,
            scale=max(abs(expected_fit["SX"]), abs(expected_fit["SY"])),
            condition=32,
        )
    assert evaluation["objective"] is None
    assert evaluation["angle_rad"] is None and evaluation["magnitude_cyc_um"] is None
    close(actual.raw_modulation, [[[expected_fit["forward"]]]], work=24, scale=1, condition=32)
    close(actual.modulation, actual.raw_modulation, work=24, scale=1)


@pytest.mark.parametrize("fit_phases", [False, True])
@pytest.mark.parametrize("floor", [None, (1.0, 6.0, 31.0), (2.0, 5.0, 20.0)])
def test_known_direct_factors_products_before_floors_and_phase(
    fit_phases: bool, floor: Any
) -> None:
    raw = raw_pattern(p=7, y=2, x=4)
    bands = api("prepare_acquisition_bands")(raw, **options(norders=4))
    bands.quadratures[:] = 0
    bands.quadratures[0, 0, 0] = 1
    direct = np.array([2j, 3.0, 5j])
    for m, value in enumerate(direct, 1):
        bands.quadratures[0, 0, 2 * m - 1] = value
    table = transfer(orders=4)
    supplied = None if floor is None else np.array(floor)
    actual = api("estimate_parameters")(
        bands,
        table,
        initial_carriers_cyc_um=np.zeros((1, 2)),
        search_carriers=False,
        fit_all_phases=fit_phases,
        amplitude_floors=supplied,
        **optics(),
    )
    cumulative = np.array([2j, 6j, -30.0], dtype=complex)
    final = cumulative.copy()
    if supplied is not None:
        final *= np.maximum(1, supplied / abs(final))
    if not fit_phases:
        final[1:] = abs(final[1:]) * np.exp(1j * np.arange(2, 4) * np.angle(final[0]))
    close(actual.raw_modulation[0, 0], direct, work=8, scale=5)
    close(actual.modulation[0, 0], final, work=8, scale=31)
    products = events(actual, "cumulative-product")
    assert len(products) == 2
    for m, e in enumerate(products, 2):
        assert tuple(e) == ("order", "direct_forward", "previous_cumulative", "product")
        assert e["order"] == m
        close(e["direct_forward"], direct[m - 1], work=8, scale=5)
        close(e["previous_cumulative"], cumulative[m - 2], work=8, scale=30)
        close(e["product"], cumulative[m - 1], work=8, scale=30)
    adjustments = events(actual, "adjustment")
    for m, e in enumerate(adjustments):
        close(e["raw_forward"], cumulative[m], work=8, scale=30)
    kinds = [e.kind for e in actual.trace]
    assert max(i for i, k in enumerate(kinds) if k == "cumulative-product") < min(
        i for i, k in enumerate(kinds) if k == "adjustment"
    )


@pytest.mark.parametrize("mode,z,o", [("2d", 1, 2), ("3d", 3, 3)])
def test_estimator_exact_result_identity_settings_and_original_prefix(
    mode: str, z: int, o: int
) -> None:
    raw = raw_pattern(d=3, p=5, z=z, y=4, x=6)
    bands = api("prepare_acquisition_bands")(
        raw, **options(acquisition_mode=mode, norders=o, lateral_zoom=1.5)
    )
    initial = np.array([[0.07, 0.02], [-0.03, 0.08], [0.04, -0.06]])
    actual = api("estimate_parameters")(
        bands, transfer(o, k=z), initial_carriers_cyc_um=initial, search_carriers=False, **optics()
    )
    assert actual.source_revision == "SVN307" and type(actual.source_revision) is str
    assert actual.reference_sha256 == SOURCE6 and len(actual.reference_sha256) == 6
    settings = actual.resolved_settings
    assert tuple(k for k, _ in settings) == (
        *ESTIMATE_KEYS,
        "acquisition_mode",
        "acquisition_reference_sha256",
    )
    assert len(settings) == 15
    expected = (
        520,
        0.25,
        1.0,
        False,
        True,
        None,
        True,
        False,
        1.0,
        0.5,
        1.5,
        1,
        bands.input_scale,
        mode,
        SOURCE10,
    )
    assert tuple(v for _, v in settings) == expected
    for (_, value), want in zip(settings, expected, strict=True):
        assert type(value) is type(want)
    assert all(
        type(k) is str and type(v) is str for k, v in dict(settings)["acquisition_reference_sha256"]
    )
    assert actual.modulation.flags.owndata and not actual.modulation.flags.writeable
    np.testing.assert_array_equal(actual.initial_carriers_cyc_um, initial)
    if mode == "3d":
        legacy_settings = options(norders=o)
        del legacy_settings["acquisition_mode"]
        legacy_settings["lateral_zoom"] = 1
        original = api("prepare_bands")(raw, **legacy_settings)
        old = api("estimate_parameters")(
            original,
            transfer(o, k=z),
            initial_carriers_cyc_um=initial,
            search_carriers=False,
            **optics(),
        )
        assert tuple(k for k, _ in old.resolved_settings) == ESTIMATE_KEYS
        assert old.reference_sha256 == SOURCE6
        assert not events(actual, "cumulative-product")


@pytest.mark.parametrize(
    "field,bad",
    [
        ("reference_sha256", SOURCE6),
        ("reference_sha256", tuple(reversed(SOURCE10))),
        ("reference_sha256", (("mainfile.c", "0" * 64), *SOURCE10[1:])),
        ("reference_sha256", list(SOURCE10)),
        ("acquisition_mode", "inferred"),
    ],
)
def test_input_ten_file_identity_is_validated_separately(field: str, bad: Any) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    forged = copy(bands)
    object.__setattr__(forged, field, bad)
    with pytest.raises(
        api("ParameterEstimationError"), match="(?i)source|reference|mode|provenance"
    ):
        api("estimate_parameters")(
            forged,
            transfer(),
            initial_carriers_cyc_um=np.zeros((1, 2)),
            search_carriers=False,
            **optics(),
        )


@pytest.mark.parametrize("search", [False, True])
def test_true_2d_omit_kz0_fails_at_reached_operation(search: bool) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    with pytest.raises(
        api("ParameterEstimationError"), match="(?i)energy|coarse|polar|zero|overlap"
    ):
        api("estimate_parameters")(
            bands,
            transfer(),
            initial_carriers_cyc_um=np.array([[0.1, 0]]),
            search_carriers=search,
            omit_kz0=True,
            **optics(),
        )


@pytest.mark.parametrize("amplitude", [2.0**-100, 2.0])
def test_weak_unequal_energy_and_zero_known_vector_are_permitted(amplitude: float) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    bands.quadratures[:] = 0
    bands.quadratures[0, 0, 0] = amplitude
    bands.quadratures[0, 0, 1] = 3 * amplitude
    actual = api("estimate_parameters")(
        bands,
        transfer(),
        initial_carriers_cyc_um=np.zeros((1, 2)),
        search_carriers=False,
        **optics(),
    )
    close(actual.modulation, 3, work=8, scale=3)


@pytest.mark.parametrize("reuse", [False, True])
@pytest.mark.parametrize("layout", ["radial", "full"])
def test_finite_2d_search_pair_trace_adjacent_fits_and_time_reuse(reuse: bool, layout: str) -> None:
    from c_acquisition_fixture import finite_search, known_options, one_time, reconstruct_expected

    raw = raw_pattern(t=2, p=5, y=4, x=6)
    bands = api("prepare_acquisition_bands")(raw, **options(norders=3))
    table = transfer(3, layout=layout)
    initial = np.array([[0.15, 0.05]])
    expected = finite_search(bands, table, initial[0], **optics())
    # Known-parameter control precedes actual finite-search composition.
    known = api("reconstruct_known")(
        one_time(bands, 0),
        table,
        carriers_cyc_um=initial,
        modulation=np.array([[0.4, 0.2]]),
        **known_options(),
    )
    known_truth = reconstruct_expected(
        one_time(bands, 0), table, initial, np.array([[0.4, 0.2]]), **known_options()
    )
    close(
        known.image,
        known_truth["image"],
        work=24,
        scale=float(np.sum(abs(bands.quadratures))),
        condition=128,
    )
    actual = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=initial, use_time0_carriers=reuse, **optics()
    )
    close(actual.carriers_cyc_um[0, 0], expected["carrier"], work=24, scale=1, condition=256)
    close(actual.raw_modulation[0, 0], expected["raw"], work=24, scale=1, condition=256)
    close(actual.modulation[0, 0], expected["modulation"], work=24, scale=1, condition=256)
    first = [e for e in actual.trace if e.time_index == 0]
    trace = [
        (e.kind, dict(e.details))
        for e in first
        if e.kind in {"evaluation", "bracket", "parabola"}
        and dict(e.details).get("stage") != "later-order"
    ]
    assert len(trace) == len(expected["trace"])
    for (kind, e), want in zip(trace, expected["trace"], strict=True):
        assert kind == want["kind"] and e["stage"] == want["stage"]
        if kind == "evaluation":
            for key in [
                "carrier_cyc_um",
                "SX",
                "SY",
                "cross",
                "forward",
                "reverse",
                "combined",
                "correlation",
                "objective",
            ]:
                close(
                    e[key],
                    want[key],
                    work=24,
                    scale=max(abs(want["SX"]), abs(want["SY"]), 1),
                    condition=256,
                )
            assert e["orders"] == (0, 1)
        elif kind == "bracket":
            assert e["branch"] == want["branch"]
            close(
                [e[k] for k in ["x1", "amp1", "x2", "amp2", "x3", "amp3"]],
                want["values"],
                work=24,
                scale=4,
                condition=256,
            )
            assert e["strict_improvement"] is (e["amp3"] > e["amp2"])
        else:
            close(e["result"], want["result"], work=24, scale=4, condition=256)
    builds = [b for b in actual.overlaps if b.time_index == 0]
    assert [b.orders for b in builds] == [(0, 1), (0, 1), (1, 2)]
    assert [b.purpose for b in builds] == ["coarse", "refinement", "later-order"]
    for build, want in zip(builds, expected["builds"], strict=True):
        np.testing.assert_array_equal(build.written, want["written"])
        close(
            build.fourier,
            want["fourier"],
            work=24,
            scale=float(np.sum(abs(bands.quadratures))),
            condition=32,
        )
    coarse_event = events(actual, "coarse")[0]
    close(
        coarse_event["carrier_cyc_um"], expected["coarse_carrier"], work=24, scale=1, condition=128
    )
    if reuse:
        assert actual.branches == (("searched",), ("time0-reused",))
        assert [b.orders for b in actual.overlaps if b.time_index == 1] == [(0, 1), (0, 2)]
        known_factors = []
        for b in [1, 2]:
            overlap = overlaps(bands, table, expected["carrier"], (0, b), t=1, **optics())
            known_factors.append(
                regression(overlap["spatial"], expected["carrier"], (0, b), 1.0)["forward"]
            )
        close(actual.raw_modulation[1, 0], known_factors, work=24, scale=4, condition=256)
        close(actual.modulation[1, 0], np.cumprod(known_factors), work=24, scale=4, condition=256)
        assert not np.allclose(actual.modulation[1], actual.modulation[0], rtol=0, atol=1e-5)
    else:
        expected1 = finite_search(bands, table, initial[0], t=1, **optics())
        close(actual.carriers_cyc_um[1, 0], expected1["carrier"], work=24, scale=1, condition=256)
        assert actual.branches == (("searched",), ("searched",))
    composed = api("reconstruct_known")(
        one_time(bands, 0),
        table,
        carriers_cyc_um=actual.carriers_cyc_um[0],
        modulation=actual.modulation[0],
        **known_options(),
    )
    truth = reconstruct_expected(
        one_time(bands, 0),
        table,
        expected["carrier"][None],
        expected["modulation"][None],
        **known_options(),
    )
    close(
        composed.image,
        truth["image"],
        work=24,
        scale=float(np.sum(abs(bands.quadratures))),
        condition=512,
    )


def test_algebraic_initial_search_ties_duplicate_angle_and_stale_magnitude_state() -> None:
    # X4/Y1, unit complex transfers. Initial carrier=-1/4 gives coarse power
    # (4,16,4,16): first strict peak1, zero periodic offset, coarse k=+1/4.
    # Frozen lower spatial overlap is a delta at centered x=0, magnitude4/sqrt2;
    # higher overlap is constant1/sqrt2. Every probe then has SX8,SY2,C2,
    # forward1/4 and objective1/16, independently of angle or magnitude.
    bands = api("prepare_acquisition_bands")(raw_pattern(y=1, x=4), **options())
    bands.quadratures[:] = 0
    bands.quadratures[0, 0, 0, 0, 0] = [1, -1, 1]
    bands.quadratures[0, 0, 1, 0, 0] = [1, 0, 1]
    actual = api("estimate_parameters")(
        bands, transfer(), initial_carriers_cyc_um=np.array([[-0.25, 0.0]]), **optics()
    )
    coarse = events(actual, "coarse")[0]
    assert coarse["integer_peak_xy"] == (1, 0)
    close(coarse["correlation_power"], [[4, 16, 4, 16]], work=4, scale=16)
    close(coarse["carrier_cyc_um"], [0.25, 0.0], work=4, scale=1)
    bracket = events(actual, "bracket")
    assert [(e["stage"], e["branch"]) for e in bracket] == [
        ("angle", "initial"),
        ("angle", "negative-swap"),
        ("angle", "stop"),
        ("magnitude", "initial"),
        ("magnitude", "negative-swap"),
        ("magnitude", "stop"),
    ]
    assert all(not e["strict_improvement"] for e in bracket)
    assert all(e["x1"] == e["amp1"] == 0 for e in bracket)
    parabolas = events(actual, "parabola")
    assert parabolas[0]["status"] == "duplicate-coordinate" and parabolas[0]["result"] == 0
    close(parabolas[1]["result"], 0.2625, work=4, scale=1)
    assert len(events(actual, "evaluation")) == 5
    for e in events(actual, "evaluation"):
        close(e["SX"], 8, work=4, scale=8)
        close(e["SY"], 2, work=4, scale=2)
        close(e["forward"], 0.25, work=4, scale=1)
        close(e["objective"], 1 / 16, work=4, scale=1)
    close(actual.carriers_cyc_um, [[[0.2625, 0]]], work=4, scale=1)
    close(actual.modulation, 0.25, work=4, scale=1)


@pytest.mark.parametrize(
    "selector",
    ["zero-permitted", "floor-zero", "phase-zero", "equal-energy", "lower-zero", "higher-zero"],
)
def test_zero_factor_domain_and_actual_regression_failures(selector: str) -> None:
    bands = api("prepare_acquisition_bands")(raw_pattern(y=2, x=4), **options())
    bands.quadratures[:] = 0
    bands.quadratures[0, 0, 0, 0, 0, 0] = 1
    bands.quadratures[0, 0, 1, 0, 0, -1] = 2
    settings: dict[str, Any] = dict(search_carriers=False)
    if selector == "floor-zero":
        settings["amplitude_floors"] = np.array([0.1])
    elif selector == "phase-zero":
        settings["fit_all_phases"] = False
    elif selector == "equal-energy":
        bands.quadratures[0, 0, 1] = bands.quadratures[0, 0, 0]
    elif selector == "lower-zero":
        bands.quadratures[0, 0, 0] = 0
    elif selector == "higher-zero":
        bands.quadratures[0, 0, 1] = 0
    if selector == "zero-permitted":
        result = api("estimate_parameters")(
            bands, transfer(), initial_carriers_cyc_um=np.zeros((1, 2)), **settings, **optics()
        )
        close(result.modulation, 0, work=8, scale=1)
        assert events(result, "evaluation")[0]["objective"] is None
    else:
        with pytest.raises(
            api("ParameterEstimationError"), match="(?i)energy|phase|floor|zero|equal|modulation"
        ):
            api("estimate_parameters")(
                bands, transfer(), initial_carriers_cyc_um=np.zeros((1, 2)), **settings, **optics()
            )


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 2)])
def test_threshold_multiplier_strict_equality_and_complex_cross_transfer(mode: str, z: int) -> None:
    bands = api("prepare_acquisition_bands")(
        raw_pattern(z=z, y=2, x=4), **options(acquisition_mode=mode)
    )
    # Both raw samples are exactly representable. Sampling at q=.25 produces
    # u=.006 through declared dkr=.25/.006, so equality is a sampled value.
    samples = np.ones((2, 4, 1), dtype=complex)
    samples[0] *= 1 + 1j
    samples[1, :, 0] = np.arange(4) * (1 + 0j)
    table = api("declare_otf")(samples, layout="radial", dkr_cyc_um=0.25 / 0.006, dkz_cyc_um=2.0)
    actual = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=np.zeros((1, 2)), search_carriers=False, **optics()
    )
    expected = overlaps(bands, table, np.zeros(2), (0, 1), **optics())
    np.testing.assert_array_equal(actual.overlaps[0].written, expected["written"])
    close(
        actual.overlaps[0].fourier,
        expected["fourier"],
        work=8 * z,
        scale=float(np.sum(abs(bands.quadratures))),
        condition=32,
    )
    h = api("sample_otf")(table, 0.25, 0, 0, dkz_cyc_um=2.0, order=1)
    assert h == 0.006
    assert bool(actual.overlaps[0].written[1, 0, 0, 1]) is (z > 1)
