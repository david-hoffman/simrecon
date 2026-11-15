"""PH118 public lifetime witnesses; static authorship is not passing evidence.

Independent science comes from CE02 finite sums and the retained CE04 observer.
Exact snapshots below include float bits, so signed zero cannot disappear from
an earlier public result when a later harmonic/call reuses private storage.
"""

from __future__ import annotations

import dataclasses
import struct
from collections.abc import Mapping
from contextlib import nullcontext
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

import c_acquisition_fixture as acquisition_observer
from c_known_fixture import (
    blank,
    compare,
    known,
    public,
    raw_quadratures,
    table,
)
from c_preparation_fixture import expected as preparation_expected
from c_workflow_oracle import OPTICS, control_cases


def _snapshot(value: Any) -> Any:
    """Snapshot public values, preserving order, dtype and every numeric bit."""
    if isinstance(value, np.ndarray):
        return ("array", value.dtype.str, value.shape, value.tobytes(order="C"))
    if isinstance(value, np.generic):
        return ("scalar", value.dtype.str, value.tobytes())
    if type(value) is float:
        return ("float", struct.pack("!d", value))
    if type(value) is complex:
        return ("complex", struct.pack("!dd", value.real, value.imag))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (field.name, _snapshot(getattr(value, field.name)))
            for field in dataclasses.fields(value)
        )
    if isinstance(value, Mapping):
        return tuple((_snapshot(key), _snapshot(child)) for key, child in value.items())
    if isinstance(value, (tuple, list)):
        return tuple(_snapshot(child) for child in value)
    assert value is None or type(value) in (str, bytes, bool, int)
    return (type(value).__name__, value)


def _arrays(value: Any) -> list[np.ndarray]:
    """Walk declared public fields once; no product object internals are read."""
    arrays: list[np.ndarray] = []
    seen: set[int] = set()

    def visit(item: Any) -> None:
        if id(item) in seen:
            return
        seen.add(id(item))
        if isinstance(item, np.ndarray):
            arrays.append(item)
        elif dataclasses.is_dataclass(item) and not isinstance(item, type):
            for field in dataclasses.fields(item):
                visit(getattr(item, field.name))
        elif isinstance(item, Mapping):
            for key, child in item.items():
                visit(key)
                visit(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                visit(child)

    visit(value)
    return arrays


def _array_occurrences(value: Any) -> list[tuple[str, np.ndarray]]:
    """Keep repeated public field occurrences; reject cycles on the active path."""
    result: list[tuple[str, np.ndarray]] = []
    active: set[int] = set()

    def visit(item: Any, path: str) -> None:
        if isinstance(item, np.ndarray):
            result.append((path, item))
            return
        if dataclasses.is_dataclass(item) and not isinstance(item, type):
            children = [
                (field.name, getattr(item, field.name)) for field in dataclasses.fields(item)
            ]
        elif isinstance(item, Mapping):
            children = [(str(key), child) for key, child in item.items()]
        elif isinstance(item, (tuple, list)):
            children = [(str(index), child) for index, child in enumerate(item)]
        else:
            return
        assert id(item) not in active, f"cycle in declared public fields: {path}"
        active.add(id(item))
        try:
            for label, child in children:
                visit(child, f"{path}.{label}")
        finally:
            active.remove(id(item))

    visit(value, "result")
    return result


def _enclosed_capture(actual: Any, expected: Any) -> None:
    """Use the frozen observer/backend enclosure; no fitted numeric tolerance."""
    bound = float(np.max(expected.error))
    assert np.isfinite(bound) and bound >= 0
    assert_allclose(actual, np.asarray(expected), rtol=0, atol=bound)


def test_t2_current_camera_first_off_debug_values_and_field_occurrence_lifetimes() -> None:
    """RC1/S09/S19: independent ordered full-debug truth, then lifetime isolation."""
    case = control_cases()["between-first-off-and-persistent-sentinel"]
    raw = case.raw
    off = case.extras["off_exposures"]
    initial_background = case.acquisition["background"].copy()
    current_background = initial_background.copy()
    current_background[-1, -1] = initial_background[-1, -2]
    # The sole normal-camera sentinel is t0/d0/z0/p0. Off frames are positive
    # or -.25/-.5, so none is exactly -1. Prepass repair never updates maps.
    assert np.count_nonzero(raw[..., -1, -1] == -1) == 1
    assert not np.any(off[..., -1, -1] == -1)
    expected = []
    for time, background in enumerate((initial_background, current_background)):
        expected.append(
            acquisition_observer.between_expected(
                acquisition_observer.as_disc(raw[time]),
                background=acquisition_observer.as_disc(background),
                off=acquisition_observer.as_disc(off[time]),
                dz=1.0,
                pitch=1.0,
                highpass=0.2,
                **OPTICS,
            )
        )
    # Freeze distinguishing margins BEFORE the public call. The stale-camera
    # error is the fixed10 image of a +3/(Z*Y*X) bottom-right impulse.
    impulse = acquisition_observer.disc_zeros((10, 12))
    impulse[-1, -1] = acquisition_observer.as_disc(3.0) / (2 * 10 * 12)
    camera_difference = acquisition_observer.edge(impulse, 10)
    center_error = [float(np.max(item["centers"].error)) for item in expected]
    assert np.max(abs(np.asarray(camera_difference))) > 2 * sum(center_error)
    assert np.max(abs(np.asarray(expected[1]["centers"] - expected[0]["centers"]))) > (
        2 * sum(center_error)
    )
    for time, item in enumerate(expected):
        assert np.max(abs(np.asarray(item["centers"]))) > 2 * center_error[time]
        # Summing the second off exposure would add this independent field.
        extra = acquisition_observer.as_disc(off[time, :, :, 0, 1]).sum(axis=1) / (5 * 12 * 10 * 2)
        extra = np.stack([acquisition_observer.edge(plane, 10) for plane in extra])
        assert np.max(abs(np.asarray(extra))) > 2 * center_error[time]
        for correlation in item["correlations"]:
            values = np.sort(np.asarray(correlation["absolute_correlation"]).ravel())
            error = float(np.max(correlation["absolute_correlation"].error))
            assert values[-1] > 2 * error
            assert values[-1] - values[-2] > 2 * error
    settings = dict(case.acquisition)
    del settings["phase_policy"]
    settings.update(case.extras)
    settings.update(OPTICS)
    caller_before = _snapshot((raw, settings))
    first = public("prepare_acquisition_bands")(raw, **settings)
    assert _snapshot((raw, settings)) == caller_before
    captures = [
        event
        for event in first.trace
        if event.kind == "between-build"
        or (event.kind == "drift-correlation" and dict(event.details)["scope"] == "between")
    ]
    assert [(event.kind, event.time_index, event.direction_index) for event in captures] == [
        (kind, time, direction)
        for time in range(2)
        for kind, direction in (
            ("between-build", 0),
            ("drift-correlation", 1),
            ("drift-correlation", 2),
        )
    ]
    for time, item in enumerate(expected):
        build = dict(captures[3 * time].details)
        assert build["subz"] == 1 and build["first_z"] == 0
        for field in ("centers", "fourier"):
            _enclosed_capture(build[field], item[field])
        for direction, correlation in enumerate(item["correlations"], 1):
            actual = dict(captures[3 * time + direction].details)
            assert actual["scope"] == "between" and actual["moving_index"] == direction
            assert actual["exponent"] == 0.25
            for field in (
                "cross_spectrum",
                "correlation",
                "absolute_correlation",
                "neighbors_xyz",
                "offsets_xyz",
                "wrapped_displacement_xyz",
            ):
                _enclosed_capture(actual[field], correlation[field])
            assert actual["integer_peak_xyz"] == correlation["integer_peak_xyz"]
            assert actual["offset_status_xyz"] == correlation["offset_status_xyz"]
    occurrences = _array_occurrences(first)
    for index, (path, array) in enumerate(occurrences):
        assert array.flags.owndata, path
        assert np.isfinite(array).all(), path
        if path in {"result.quadratures", "result.noise_variance_factors"}:
            assert array.flags.writeable, path
        else:
            assert not array.flags.writeable, path
        for other_path, other in occurrences[index + 1 :]:
            assert not np.shares_memory(array, other), (path, other_path)
        for _, caller in _array_occurrences((raw, settings)):
            assert not np.shares_memory(array, caller), path
    before = _snapshot(first)
    later_case = control_cases()["between-first-off-and-persistent-sentinel"]
    later_settings = dict(later_case.acquisition)
    del later_settings["phase_policy"]
    later_settings.update(later_case.extras)
    later_settings.update(OPTICS)
    later_case.raw[:] += 16
    later_case.extras["off_exposures"][:] += 4
    later = public("prepare_acquisition_bands")(later_case.raw, **later_settings)
    later.quadratures[:] = 0
    later.noise_variance_factors[:] = 7
    raw[:] = 0
    off[:] = 0
    case.acquisition["background"][:] = 999
    case.acquisition["flatfield_slope"][:] = 0
    assert _snapshot(first) == before
    trace_before = _snapshot(first.trace)
    first.quadratures[:] = 0
    first.noise_variance_factors[:] = 9
    assert _snapshot(first.trace) == trace_before


def _raw(z: int, y: int = 3) -> np.ndarray:
    """Dyadic integer multifrequency frames with phase-dependent Nyquist."""
    t, d, p, h, i, j = np.indices((2, 2, 5, z, y, 4))
    return (
        20
        + (3 * t + 5 * d + 7 * p + h + i * j + j * j) % 17
        + (p + 1) * np.where(j % 2 == 0, 1, -1)
    ).astype(np.float64)


@pytest.mark.parametrize("z", [2, 3])
@pytest.mark.parametrize("extended", [False, True])
def test_completed_sections_preserve_full_z_and_earlier_preparation(z: int, extended: bool) -> None:
    """S01/S02/S19/S21: later section/call storage cannot replace old output."""
    backing = _raw(z)[..., ::-1].copy()
    raw = backing[..., ::-1]
    raw.flags.writeable = False
    original = _snapshot(raw)
    settings: dict[str, Any] = dict(
        dxy_um=0.5,
        dz_um=0.3,
        norders=3,
        background=0,
        lateral_zoom=2,
        axial_zoom=2,
        edge_pixels=0,
        equalize=False,
    )
    name = "prepare_acquisition_bands" if extended else "prepare_bands"
    if extended:
        settings["acquisition_mode"] = "3d"
    # CE02 steps5--7: direct negative finite sums, raw phase slots at X/2.
    expected = raw_quadratures(raw, 3, 1 / (4 * 3 * z * 4 * 2 * 2))
    first = public(name)(raw, **settings)
    assert_allclose(first.quadratures, expected, rtol=2e-10, atol=2e-10)
    assert np.max(abs(expected[..., -1])) > 0
    assert not np.array_equal(expected[:, :, 0, :, :, -1], expected[:, :, 1, :, :, -1])
    assert first.quadratures.dtype == np.complex128
    assert first.quadratures.flags.owndata and first.quadratures.flags.writeable
    for output in _arrays(first):
        assert not np.shares_memory(output, raw)
    before = _snapshot(first)
    later_raw = -2 * _raw(z)
    later = public(name)(later_raw, **settings)
    assert_allclose(later.quadratures, -2 * expected, rtol=2e-10, atol=4e-10)
    later.quadratures[:] = 123 - 17j
    later.noise_variance_factors[:] = 7
    assert _snapshot(raw) == original
    backing[:] = 0
    assert _snapshot(first) == before
    # Mutation above was by the owner of the backing, after both public calls.
    assert original != _snapshot(raw)


@pytest.mark.parametrize("ny", [1, 3, 4, 5])
@pytest.mark.parametrize("layout", ["radial", "full"])
def test_sparse_harmonics_zero_successors_and_published_results_are_independent(
    ny: int, layout: str
) -> None:
    """S14--S17/S19/S21: zero later harmonics cannot inherit earlier scratch."""
    bands = blank(3, shape=(2, 2, 5, 6, ny, 4), lateral_zoom=2, axial_zoom=2)
    # All unassigned samples are actual exact caller-specified zeros. Distinct
    # predecessor locations/signs distinguish harmonic/direction/time leakage.
    q = np.zeros_like(bands.quadratures)
    q[0, 0, 1, 1, 0, 1] = 0.5 + 0.25j
    q[0, 0, 2, 1, 0, 1] = 0.25 - 0.5j
    q[0, 1, 3, 0, ny - 1, 2] = -0.75 + 0.125j
    q[0, 1, 4, 0, ny - 1, 2] = -0.125 - 0.75j
    # Keep a signed zero in an untouched public operand; its exact output bits
    # are compared in snapshots, while the scientific observer uses values.
    q[1, 0, 0, 0, 0, 0] = complex(-0.0, -0.0)
    bands.quadratures[:] = q
    bands.noise_variance_factors[:] = [[1, 2, 4], [2, 1, 3]]
    carriers = np.array([[0.125, -0.0625], [-0.1875, 0.125]])
    modulation = np.array([[0.5 + 0.25j, -0.5j], [-0.75, 0.25j]])
    transfer = table(3, layout)
    input_before = _snapshot((bands, transfer, carriers, modulation))
    first = compare(bands, transfer, carriers_cyc_um=carriers, modulation=modulation)
    assert _snapshot((bands, transfer, carriers, modulation)) == input_before
    assert_array_equal(first.filtered_quadratures[0, 0, 3:5], 0)
    assert_array_equal(first.filtered_quadratures[0, 1, 1:3], 0)
    assert_array_equal(first.filtered_quadratures[1], 0)
    assert_array_equal(first.image[1], 0)
    assert np.max(abs(first.image[0])) > 0
    if ny == 1:
        # CE04's empty filter traversal retains every supplied bit.
        assert _snapshot(first.filtered_quadratures) == _snapshot(q)
    before = _snapshot(first)
    # A real caller may modify both documented writable stage operands.
    bands.quadratures[:] = -q
    bands.noise_variance_factors[:] = [[3, 4, 2], [1, 3, 2]]
    carriers[:] *= -1
    modulation[:] *= 0.5j
    compare(bands, transfer, carriers_cyc_um=carriers, modulation=modulation)
    assert _snapshot(first) == before
    for output in _arrays(first):
        assert output.flags.owndata and not output.flags.writeable
        for caller in (
            bands.quadratures,
            bands.noise_variance_factors,
            carriers,
            modulation,
            transfer.samples,
        ):
            assert not np.shares_memory(output, caller)


def test_phase_design_snapshots_survive_caller_and_later_call_mutations() -> None:
    """S19: full per-section debug arrays cannot publish reused phase storage."""
    raw = _raw(3)
    phases = np.array(
        [
            [0, np.pi / 2, np.pi, 3 * np.pi / 2, np.pi / 4],
            [np.pi / 4, 3 * np.pi / 2, np.pi, np.pi / 2, 0],
        ]
    )
    settings = dict(
        acquisition_mode="3d",
        dxy_um=0.5,
        dz_um=0.3,
        norders=3,
        background=0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
        phases_rad=phases,
    )
    first = public("prepare_acquisition_bands")(raw, **settings)
    designs = [event for event in first.trace if event.kind == "phase-design"]
    assert len(designs) == 2 * 2 * 3
    arrays = _arrays(tuple(designs))
    for index, array in enumerate(arrays):
        assert array.flags.owndata and not array.flags.writeable
        assert not any(np.shares_memory(array, other) for other in arrays[index + 1 :])
        assert not np.shares_memory(array, first.quadratures)
        assert not np.shares_memory(array, first.noise_variance_factors)
    before = _snapshot(tuple(designs))
    first.quadratures[:] = 0
    first.noise_variance_factors[:] = 9
    phases[:] += 0.125
    raw[:] *= -1
    public("prepare_acquisition_bands")(raw, **settings)
    assert _snapshot(tuple(designs)) == before


def test_fractional_2d_zero_planes_nyquist_and_wiener_preincrement_closed_values() -> None:
    """S17/S18/S21: real caller-edited bands isolate geometry and schedule."""
    raw = np.zeros((2, 2, 3, 1, 10, 10), dtype=np.float32)
    settings = dict(
        acquisition_mode="2d",
        dxy_um=1.0,
        dz_um=0.0,
        norders=2,
        background=0,
        lateral_zoom=1.5,
        axial_zoom=3,
        edge_pixels=0,
        equalize=False,
    )
    bands = public("prepare_acquisition_bands")(raw, **settings)
    bands.quadratures[:] = 0
    bands.noise_variance_factors[:] = 1
    bands.quadratures[:, :, 0, 0, 0, 0] = [[1, 2], [3, -1]]
    bands.quadratures[:, 0, 0, 0, 0, 5] = [1, -2]
    transfer = public("declare_otf")(
        np.ones((2, 8, 1), dtype=np.complex64),
        layout="radial",
        dkr_cyc_um=0.25,
        dkz_cyc_um=0.7,
    )
    before = _snapshot(bands)
    result = known(
        bands,
        transfer,
        carriers_cyc_um=np.zeros((2, 2)),
        modulation=np.zeros((2, 1)),
        wavelength_nm=500,
        numerical_aperture=1,
        immersion_index=1,
        wiener=0.2,
        wiener_increment=0.2,
        filter_overlaps=False,
        output_taper="power",
        power_taper_exponent=0.0,
    )
    # Other direction's center power remains at DC even with overlaps off.
    # At native positive Nyquist, strict other support excludes it: self only.
    # Gamma0 makes taper1 at the boundary. A>1 transforms plane0 only.
    expected = np.zeros((2, 3, 15, 15))
    mode = np.cos(2 * np.pi * 5 * np.arange(15) / 15)
    for t, (dc, endpoint, w) in enumerate(((3, 1, 0.3), (2, -2, 0.4))):
        expected[t, 0] = dc / (2 + w * w) + endpoint * mode / (1 + w * w)
    assert_allclose(result.image, expected, rtol=2e-12, atol=2e-12)
    assert_array_equal(result.image[:, 1:], 0)
    assert_array_equal(result.z_um, 0)
    assert_allclose(result.x_um, (np.arange(15) - 7) / 1.5, rtol=2e-12, atol=2e-12)
    assert_allclose(
        dict(result.resolved_settings)["effective_wiener"], [0.3, 0.4], rtol=2e-12, atol=2e-12
    )
    assert _snapshot(bands) == before
    with pytest.raises(public("AcquisitionModeError"), match="(?i)zoom|integral|integer|extent"):
        public("prepare_acquisition_bands")(raw, **(settings | {"lateral_zoom": 1.25}))


def _workflow_case(*, multifrequency: bool) -> dict[str, Any]:
    """Freeze explicit public declarations, independent of any returned record."""
    optics = dict(wavelength_nm=500, numerical_aperture=1.0, immersion_index=1.0)
    if multifrequency:
        shape = (2, 2, 5, 4, 12, 16)
        t, d, p, z, y, x = np.indices(shape, dtype=np.float64)
        obj = 30 + 3 * np.cos(2 * np.pi * (x / 16 + y / 12))
        obj += 2 * np.sin(2 * np.pi * (2 * x / 16 - y / 12))
        obj += np.cos(2 * np.pi * (z / 4 + 3 * x / 16))
        spatial = 2 * np.pi * (x * np.cos(d * np.pi / 2) + y * np.sin(d * np.pi / 2)) / 8
        phase = 2 * np.pi * p / 5
        raw = (
            obj
            * (
                1
                + (0.31 + t / 64) * np.cos(spatial + phase)
                + (0.13 + t / 128) * np.cos(2 * spatial + 2 * phase + 0.3)
            )
            + d / 4
            + t / 8
        ).astype(np.float32)
        m, r, a = np.indices((3, 64, 16))
        samples = 1 + m / 16 + r / 128 + 1j * (m + r + a) / 256
        orders, spacing, lateral, step_r, step_z = 3, 4.0, 2, 0.125, 0.125
    else:
        # CE07 9.1 complex-table control: actual known-vector modulation fit.
        raw = np.broadcast_to(
            np.array([6, 3, 3], dtype=np.float32)[None, None, :, None, None, None],
            (1, 1, 3, 2, 2, 4),
        ).copy()
        samples = np.ones((2, 8, 2), dtype=np.complex128)
        samples[1] += 1j * np.arange(8)[:, None]
        orders, spacing, lateral, step_r, step_z = 2, 8.0, 1, 0.25, 0.5
    return dict(
        specimen=raw,
        acquisition=dict(
            acquisition_mode="3d",
            dxy_um=1.0,
            dz_um=1.0,
            norders=orders,
            background=0.0,
            lateral_zoom=lateral,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        optics=optics,
        carrier=dict(
            linespacing_um=spacing,
            phase_start_angle_rad=0.0,
            search_carriers=False,
            use_time0_carriers=True,
            fit_all_phases=True,
        ),
        filtering=dict(
            wiener=1.0 if not multifrequency else 0.5,
            suppress_singularities=False,
            output_taper="none",
        ),
        specimen_identity=dict(id="ph118-raw-v1", intensity_unit="camera counts"),
        transfer=public("declare_otf")(
            samples,
            layout="radial",
            dkr_cyc_um=step_r,
            dkz_cyc_um=step_z,
        ),
        transfer_identity=dict(
            id="ph118-table-v1",
            intensity_unit="dimensionless-transfer",
            optics=optics.copy(),
        ),
    )


@pytest.mark.parametrize("multifrequency", [False, True])
def test_workflow_summary_exact_values_and_full_history_survive_later_calls(
    multifrequency: bool,
) -> None:
    """S19/S20: full records survive summary/later full calls and caller writes."""
    case = _workflow_case(multifrequency=multifrequency)
    caller_before = _snapshot(case)
    full = public("reconstruct_workflow")(**case)
    if not multifrequency:
        # CE07 9.1: fit from the complex table, not the raw contrast 1/4.
        root2 = np.sqrt(2.0)
        mu = (1 + root2 - 1j) / 4
        factor = 3 * (2 - 1j) * mu / (20 * root2)
        x = np.arange(4) - 2
        image = 12 / (2 + 2.5 * abs(factor) ** 2) + 6 * np.real(
            np.conj(factor) * np.exp(1j * np.pi * x / 4)
        ) / (2 + 3 * abs(factor) ** 2)
        assert_allclose(full.parameters.modulation, factor, rtol=2e-10, atol=2e-10)
        # Reuse the retained finite-assembly observer's bounds. Its absolute
        # coefficient budget here is <=6+3*abs(factor)<8, since both h>=2.
        assert_allclose(
            full.image, np.broadcast_to(image, (1, 2, 2, 4)), rtol=3e-10, atol=3e-10 * 8
        )
    before = _snapshot(full)
    summary = public("reconstruct_summary")(**case)
    assert _snapshot(case) == caller_before
    for name in (
        "image",
        "x_um",
        "y_um",
        "z_um",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
        "effective_wiener",
        "input_identities",
        "trace",
        "source_revision",
        "reference_sha256",
        "limitations",
    ):
        assert _snapshot(getattr(summary, name)) == _snapshot(getattr(full, name))
    for name in ("carriers_cyc_um", "modulation", "raw_modulation", "branches"):
        assert _snapshot(getattr(summary, name)) == _snapshot(getattr(full.parameters, name))
    assert summary.diagnostics == "summary"
    assert summary.omitted_diagnostics == (
        "stage-images",
        "quadratures",
        "overlap-arrays",
        "correlation-arrays",
        "camera-maps",
        "transfer-samples",
        "calibration-arrays",
        "layout-pixels",
        "precise-query-events",
    )
    assert "quadratures" not in dict(summary.preparation)
    assert "off_quadratures" not in dict(summary.preparation)
    assert "overlaps" not in dict(summary.estimation)
    assert "samples" in dict(summary.transfer)
    assert not isinstance(dict(summary.transfer)["samples"], np.ndarray)
    arrays = _arrays(summary)
    for index, array in enumerate(arrays):
        assert array.flags.owndata and not array.flags.writeable
        assert not any(np.shares_memory(array, other) for other in arrays[index + 1 :])
    assert not np.shares_memory(full.image, full.reconstructions[0].image)
    summary_before = _snapshot(summary)
    case["specimen"][:] *= -1
    public("reconstruct_workflow")(**case)
    assert _snapshot(full) == before
    full.bands.quadratures[:] = 0
    full.bands.noise_variance_factors[:] = 7
    # Writable bands are intentionally excluded after this caller mutation.
    assert _snapshot(summary) == summary_before
    assert _snapshot(full.reconstructions) == dict(before)["reconstructions"]
    assert _snapshot(full.parameters) == dict(before)["parameters"]


def test_superseded_phase_validation_and_full_rank_positive_are_distinct() -> None:
    """S22/S23: validate unused declarations; solve only the selected design."""
    raw = _raw(2, y=2)
    settings = dict(
        acquisition_mode="3d",
        dxy_um=0.5,
        dz_um=0.3,
        norders=3,
        background=0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
        phase_steps_rad=np.array([0.8, 0.9]),
    )
    invalid = np.full((2, 5), np.nan)
    before = _snapshot(raw)
    with pytest.raises(public("AcquisitionModeError"), match="(?i)phase|finite"):
        public("prepare_acquisition_bands")(raw, phases_rad=invalid, **settings)
    assert _snapshot(raw) == before
    # The unused finite singular list is legal; the used steps have five
    # distinct phase points and hence a full-rank five-column design.
    actual = public("prepare_acquisition_bands")(raw, phases_rad=np.zeros((2, 5)), **settings)
    for direction, step in enumerate((0.8, 0.9)):
        assert_allclose(
            actual.phase_angles_rad[:, direction],
            np.broadcast_to(np.arange(5) * step, (2, 2, 5)),
            rtol=0,
            atol=0,
        )
    with pytest.raises(public("AcquisitionModeError"), match="(?i)rank|singular|matrix|design"):
        public("prepare_acquisition_bands")(
            raw, phases_rad=np.zeros((2, 5)), **(settings | {"phase_steps_rad": None})
        )


def test_zero_weight_actual_stencil_rejects_but_empty_traversal_is_valid() -> None:
    """S24: zero signal/modulation cannot remove a reached vertex check."""
    transfer = public("declare_otf")(
        np.zeros((2, 1, 1), dtype=np.complex64),
        layout="radial",
        dkr_cyc_um=1,
        dkz_cyc_um=1,
    )
    visited = blank(shape=(1, 1, 3, 6, 2, 4))
    before = _snapshot(visited)
    with pytest.raises(
        public("ReconstructionError"), match="(?i)stencil|vertex|sample|index|bound|transfer"
    ):
        known(visited, transfer, modulation=np.zeros((1, 1)))
    assert _snapshot(visited) == before
    # CE04 Y1 visits no filter/recombination coordinates: this same declaration
    # remains a valid zero result, without a speculative global stencil scan.
    unvisited = blank(shape=(1, 1, 3, 6, 1, 4))
    result = known(unvisited, transfer, modulation=np.zeros((1, 1)))
    assert_array_equal(result.image, 0)
    assert_array_equal(result.filtered_quadratures, 0)


def _direct_fault_case(
    name: str, *, factorization: bool = False
) -> tuple[tuple[Any, ...], dict[str, Any], np.ndarray]:
    """Make small valid caller inputs before intercepting an external dependency."""
    settings: dict[str, Any]
    if name == "reconstruct_known":
        bands = blank()
        bands.quadratures[:] = 0
        bands.quadratures[0, 0, 0, 0, 0, 0] = 1
        settings = dict(
            carriers_cyc_um=np.zeros((1, 2)),
            modulation=np.zeros((1, 1)),
            wavelength_nm=520,
            numerical_aperture=0.8,
            immersion_index=1.33,
            wiener=0.5,
            suppress_singularities=False,
            output_taper="none",
        )
        # Unit self term, no other nonzero power: image=1/(1+.5^2)=.8.
        return (bands, table(constant=True)), settings, np.full((1, 6, 4, 4), 0.8)
    raw = _raw(2)
    settings = dict(
        dxy_um=0.5,
        dz_um=0.3,
        norders=3,
        background=0,
        lateral_zoom=2,
        axial_zoom=2,
        edge_pixels=0,
        equalize=False,
    )
    if name == "prepare_acquisition_bands":
        settings["acquisition_mode"] = "3d"
    if factorization:
        # CE02's valid overdetermined cardinal design. L is the independent
        # exact left inverse; duplicate pi phases are permitted, not singular.
        raw = raw[:, :, :4]
        settings["norders"] = 2
        settings["phases_rad"] = np.tile([0, np.pi / 2, np.pi, np.pi], (2, 1))
        rows = np.tile([[[2, 0, 1, 1], [1, 0, -0.5, -0.5], [-1, 2, -0.5, -0.5]]], (2, 1, 1))
        expected = preparation_expected(raw, rows, **settings)["quadratures"]
        return (raw,), settings, expected
    expected = raw_quadratures(raw, 3, 1 / (4 * 3 * 2 * 4 * 2 * 2))
    return (raw,), settings, expected


def _has_cause(error: BaseException, target: BaseException) -> bool:
    """Check the promised original cause without prescribing wrapper depth."""
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        if current is target:
            return True
        seen.add(id(current))
        current = current.__cause__
    return False


@pytest.mark.parametrize(
    "fault,name",
    [
        ("allocation", "prepare_bands"),
        ("allocation", "prepare_acquisition_bands"),
        ("allocation", "reconstruct_known"),
        ("interruption", "prepare_bands"),
        ("interruption", "prepare_acquisition_bands"),
        ("interruption", "reconstruct_known"),
        ("factorization", "prepare_bands"),
        ("backend", "prepare_acquisition_bands"),
        ("backend", "reconstruct_known"),
    ],
)
def test_direct_entry_external_failure_semantics(name: str, fault: str, monkeypatch: Any) -> None:
    """S25: preserve direct-API distinctions without requiring a backend binding.

    A public NumPy/SciPy dependency is unavailable; no product hook or scientific
    decision is replaced. If a legitimate import/backend avoids interception,
    assert the independent finite positive and claim no fault-path evidence.
    """
    import scipy.fft
    import scipy.linalg

    function = public(name)
    args, settings, expected = _direct_fault_case(name, factorization=fault == "factorization")
    before = _snapshot((args, settings))
    kind = (
        MemoryError
        if fault == "allocation"
        else KeyboardInterrupt
        if fault == "interruption"
        else np.linalg.LinAlgError
        if fault == "factorization"
        else RuntimeError
    )
    sentinel = kind("PH118 unavailable external array/transform dependency")
    calls: list[str] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        calls.append("external-operation")
        raise sentinel

    class FailingBackend:
        """Use SciPy's public FFT backend protocol, including bound dispatchers."""

        __ua_domain__ = "numpy.scipy.fft"

        @staticmethod
        def __ua_function__(method: Any, args: Any, kwargs: Any) -> Any:
            return fail()

    outcome: Any = None
    caught: BaseException | None = None
    backend_context = (
        scipy.fft.set_backend(FailingBackend(), only=True) if fault == "backend" else nullcontext()
    )
    with monkeypatch.context() as patch, backend_context:
        if fault == "factorization":
            # Public dependency operations only. Any legitimate provider or
            # previously bound alternative may avoid interception and succeed.
            for module in (np.linalg, scipy.linalg):
                for method in ("inv", "solve", "lstsq", "pinv", "svd", "qr", "cholesky"):
                    patch.setattr(module, method, fail)
            for method in ("lu_factor", "lu_solve", "cho_factor", "cho_solve"):
                patch.setattr(scipy.linalg, method, fail)
        elif fault == "backend":
            for module in (np.fft, scipy.fft):
                for method in (
                    "fft",
                    "ifft",
                    "fftn",
                    "ifftn",
                    "fft2",
                    "ifft2",
                    "rfft",
                    "irfft",
                    "rfftn",
                    "irfftn",
                    "rfft2",
                    "irfft2",
                ):
                    patch.setattr(module, method, fail)
        else:
            for method in (
                "array",
                "empty",
                "zeros",
                "ones",
                "full",
                "empty_like",
                "zeros_like",
                "ones_like",
                "copy",
                "stack",
                "concatenate",
            ):
                patch.setattr(np, method, fail)
        try:
            outcome = function(*args, **settings)
        except BaseException as error:
            caught = error
    assert _snapshot((args, settings)) == before
    print(
        f"PH118 public dependency control: {name}/{fault}: "
        f"{'intercepted' if calls else 'valid-alternative'}; calls={len(calls)}"
    )
    if calls:
        assert outcome is None and caught is not None
        if fault == "interruption":
            assert isinstance(caught, KeyboardInterrupt)
        elif fault == "allocation" and name == "prepare_bands":
            assert isinstance(caught, MemoryError)
        else:
            error_name = {
                "prepare_bands": "SimreconError",
                "prepare_acquisition_bands": "AcquisitionModeError",
                "reconstruct_known": "ReconstructionError",
            }[name]
            assert isinstance(caught, public(error_name)), (
                f"{name} {fault}: expected {error_name}; observed {type(caught).__name__}: {caught}"
            )
            assert str(caught).strip()
            if name != "prepare_bands":
                assert _has_cause(caught, sentinel)
    else:
        assert caught is None and outcome is not None
        if name == "reconstruct_known":
            assert_allclose(outcome.image, expected, rtol=2e-12, atol=2e-12)
        else:
            assert_allclose(outcome.quadratures, expected, rtol=2e-10, atol=2e-10)
