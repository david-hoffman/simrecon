"""Blind carrier-scan tests with an explicit caller source label.

EmpiricalVolumeResponse keeps its six-field public schema. The ninth required
scan keyword supplies result labels independently of all calibration fields.
"""

from __future__ import annotations

import dataclasses
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from simrecon import (
    EmpiricalVolumeResponse,
    SimreconError,
    VolumeCarrierCandidate,
    calibrate_raw_point_bead,
    correct_linear_response,
    declare_acquisition,
    scan_volume_carriers,
    separate_volume_phases,
)
from volume_carrier_diagnostics_fixture import (
    EPS,
    FMAX,
    PRECISION,
    Q0,
    bands,
    bins,
    dec,
    expected,
    finite_dft,
    frequency,
    observations,
    phase_condition_upper_bound,
    phase_matrix,
    root,
    solve_exact,
    z,
)

SOURCE = " declared calibration / opaque provenance "
PHASES = np.array([0.0, 0.37, 1.2, 2.4, 3.6, 4.7, 5.9])
Array = np.ndarray[Any, Any]


def response_from_values(
    values: Array, spacing: Any = (1.0, 1.0, 1.0), origin: Any = (0, 0, 0)
) -> EmpiricalVolumeResponse:
    axes = [
        np.array([float(Fraction(k, n) / Fraction(float(d))) for k in bins(n)])
        for n, d in zip(values.shape[1:], spacing, strict=True)
    ]
    return EmpiricalVolumeResponse(
        values=values,
        fz_per_um=axes[0],
        fy_per_um=axes[1],
        fx_per_um=axes[2],
        voxel_size_um=spacing,
        origin_zyx=origin,
    )


def response(
    shape: tuple[int, int, int] = (3, 5, 7), spacing: Any = (0.25, 0.125, 0.125)
) -> EmpiricalVolumeResponse:
    # Arbitrary non-Hermitian, nonseparable complex calibration; not an ideal OTF.
    a, b, c = np.indices(shape, dtype=np.float64)
    values = np.stack(
        [
            (1 + m / 3 + a / 17 - b / 29 + c / 23 + a * b * c / 301)
            + 1j * (0.2 - m / 5 + a * b / 37 - b * c / 53 + a * c / 47)
            for m in range(3)
        ]
    )
    return response_from_values(values, spacing, tuple(n // 2 for n in shape))


def inputs(shape: tuple[int, int, int] = (2, 3, 4)) -> dict[str, Any]:
    return dict(
        images=observations(shape, PHASES),
        response=response(),
        voxel_size_um=(1.0, 1.0, 1.0),
        phase_steps_rad=PHASES.copy(),
        candidate_carriers_yx=[(0, 0)],
        order=1,
        calibration_carrier_bins=(0, 0),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source=SOURCE,
    )


def scan(case: dict[str, Any]) -> Any:
    args = dict(case)
    images = args.pop("images")
    return scan_volume_carriers(images, **args)


def assert_code(case: dict[str, Any], code: str) -> None:
    with pytest.raises(SimreconError) as caught:
        scan(case)
    assert caught.value.code == code


def assert_fit(case: dict[str, Any], row: Any, carrier: tuple[int, int]) -> Any:
    truth = expected(
        case["images"],
        case["phase_steps_rad"],
        case["response"],
        case["voxel_size_um"],
        carrier,
        int(case["order"]),
        case["calibration_carrier_bins"],
        case["coordinate_offset_yx"],
        case["phase_reference_shift_rad"],
    )
    assert truth is not None
    assert truth.informative and truth.success_margin, truth
    assert row.status == "fitted"
    assert row.overlap_count == truth.count
    assert row.source == case["source"]
    with localcontext() as ctx:
        ctx.prec = PRECISION
        assert (z(row.gain) - truth.gain).norm() <= truth.gain_bound
        assert abs(dec(row.relative_residual) - truth.residual) <= truth.residual_bound
        assert abs(dec(row.coherence) - truth.coherence) <= truth.coherence_bound
    return truth


def test_required_bindings_and_exact_frozen_record() -> None:
    case = inputs()
    for name in case:
        if name == "images":
            continue
        args = dict(case)
        del args[name]
        with pytest.raises(TypeError):
            scan(args)
    with pytest.raises(TypeError):
        # Deliberate signature violation: keep the real runtime binding call.
        scan_volume_carriers(*case.values())  # pyright: ignore[reportCallIssue]
    with pytest.raises(TypeError):
        scan_volume_carriers(
            **case,
            undeclared_option=True,  # pyright: ignore[reportCallIssue]
        )
    without_images = dict(case)
    del without_images["images"]
    with pytest.raises(TypeError):
        scan_volume_carriers(**without_images)
    case["candidate_carriers_yx"] = [(0, 0), (2**1000, -(2**1000)), (0, 0)]
    rows = scan(case)
    assert type(rows) is tuple and len(rows) == 3
    assert [r.carrier_bins_yx for r in rows] == case["candidate_carriers_yx"]
    assert rows[0] == rows[2] and rows[0] is not rows[2]
    names = (
        "gain",
        "relative_residual",
        "coherence",
        "overlap_count",
        "status",
        "order",
        "carrier_bins_yx",
        "source",
    )
    for row in rows:
        assert isinstance(row, VolumeCarrierCandidate)
        public_fields = {
            name
            for name in dir(row)
            if not name.startswith("_") and not callable(getattr(row, name))
        }
        assert public_fields == set(names)
        assert type(row.overlap_count) is int and type(row.order) is int
        assert type(row.carrier_bins_yx) is tuple
        assert all(type(k) is int for k in row.carrier_bins_yx)
        assert row.source == SOURCE
        for name in names:
            with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
                setattr(row, name, getattr(row, name))
            with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
                delattr(row, name)
    assert type(rows[0].gain) is complex
    assert type(rows[0].relative_residual) is float and type(rows[0].coherence) is float
    assert rows[1].status == "no_overlap"
    assert rows[1].gain is rows[1].relative_residual is rows[1].coherence is None
    # Direct construction has frozen bindings, but no validation requirement.
    direct = VolumeCarrierCandidate(
        gain=None,
        relative_residual=None,
        coherence=None,
        overlap_count=-1,
        status="caller record",
        order=9,
        carrier_bins_yx=(3, 4),
        source="",
    )
    assert direct.overlap_count == -1


@pytest.mark.parametrize("bad", [None, "", " \t\n", 17, b"label", np.array("label")])
def test_explicit_source_label_rejections_are_global(bad: Any) -> None:
    case = inputs()
    case.update(source=bad, candidate_carriers_yx=[(2**1000, 0)])
    assert_code(case, "invalid_otf_source")


class OpaqueSourceLabel(str):
    """A string subclass within the nonblank string label contract."""


@pytest.mark.parametrize("label", [" pairing kept ", "\tα pairing\n", OpaqueSourceLabel("opaque")])
def test_explicit_source_label_is_retained_for_every_row(label: str) -> None:
    case = inputs()
    case.update(source=label, candidate_carriers_yx=[(0, 0), (2**1000, 0), (0, 0)])
    assert type(case["response"]) is EmpiricalVolumeResponse
    rows = scan(case)
    assert [row.status for row in rows] == ["fitted", "no_overlap", "fitted"]
    assert all(row.source == label for row in rows)
    assert_fit(case, rows[0], (0, 0))


@pytest.mark.parametrize("order", [1, 2])
@pytest.mark.parametrize("carrier", [(0, 0), (1, -1), (-1, 1)])
def test_full_complex_anisotropic_nonwrapping_projection(
    order: int, carrier: tuple[int, int]
) -> None:
    case = inputs((2, 5, 6))
    case.update(
        order=order,
        candidate_carriers_yx=[carrier],
        calibration_carrier_bins=(2, -3),
        coordinate_offset_yx=(1, -2),
        phase_reference_shift_rad=0.41,
    )
    row = scan(case)[0]
    truth = assert_fit(case, row, carrier)
    # The official allowance is conservative; these well-conditioned small
    # arrays also distinguish conjugation, side factors, order and bin errors.
    assert abs(complex(row.gain) - complex(float(truth.gain.re), float(truth.gain.im))) < 2e-10
    assert abs(row.coherence - float(truth.coherence)) < 2e-10
    assert abs(row.relative_residual - float(truth.residual)) < 2e-10


@pytest.mark.parametrize("order", [1, 2])
def test_single_voxel_analytic_sign_factor_order_and_fixed_gauge(order: int) -> None:
    case = inputs((1, 1, 1))
    coefficients = np.array([10.0, 4.0, 2.0, 6.0, -8.0])
    case["images"] = (phase_matrix(PHASES) @ coefficients).reshape(-1, 1, 1, 1)
    case["response"] = response_from_values(np.array([2 + 1j, 3 - 2j, -1 + 4j]).reshape(3, 1, 1, 1))
    case.update(order=order, phase_reference_shift_rad=0.37)
    truth = assert_fit(case, scan(case)[0], (0, 0))
    harmonic = (2 - 1j) if order == 1 else (3 + 4j)
    transfer = (3 - 2j) if order == 1 else (-1 + 4j)
    analytic = (2 + 1j) * harmonic / (10 * transfer * np.exp(-1j * order * 0.37))
    assert abs(complex(float(truth.gain.re), float(truth.gain.im)) - analytic) < 2e-14


@pytest.mark.parametrize(
    "shape,carrier,order",
    [
        ((1, 1, 1), (0, 0), 2),
        ((2, 4, 5), (-1, 2), 1),
        ((3, 5, 4), (2, -1), 2),
        ((1, 3, 6), (0, -2), 2),
        ((1, 2, 3), (2, 0), 1),
        ((1, 2, 3), (0, -3), 1),
    ],
)
def test_exact_overlap_geometry(
    shape: tuple[int, int, int], carrier: tuple[int, int], order: int
) -> None:
    case = inputs(shape)
    case.update(order=order, candidate_carriers_yx=[carrier])
    row = scan(case)[0]
    count = (
        shape[0]
        * max(shape[1] - abs(order * carrier[0]), 0)
        * max(shape[2] - abs(order * carrier[1]), 0)
    )
    assert row.overlap_count == count
    if count:
        assert_fit(case, row, carrier)
    else:
        assert row.status == "no_overlap" and row.gain is None


@pytest.mark.parametrize(
    "candidates",
    [
        [[0, 0], [-(2**1000), 2**1001], [0, 0]],
        ((np.int8(0), np.uint64(2**64 - 1)),),
        np.array([[0, 0], [1, 0]], dtype=">i8"),
        np.array([[0, 0], [2**64 - 1, 0]], dtype=np.uint64),
    ],
)
def test_exact_candidate_integer_representations(candidates: Any) -> None:
    case = inputs()
    if isinstance(candidates, np.ndarray):
        candidates = np.asfortranarray(candidates)
        candidates.flags.writeable = False
    case["candidate_carriers_yx"] = candidates
    rows = scan(case)
    assert [r.carrier_bins_yx for r in rows] == [tuple(int(k) for k in pair) for pair in candidates]
    for row in rows:
        ky, kx = row.carrier_bins_yx
        assert row.overlap_count == 2 * max(3 - abs(ky), 0) * max(4 - abs(kx), 0)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        (),
        (0, 0),
        [[0]],
        [[0, 0, 0]],
        [[0.0, 0]],
        [[True, 0]],
        np.array([[False, False]]),
        np.array([[0.0, 0.0]]),
        np.zeros((0, 2), dtype=int),
        np.zeros((2,), dtype=int),
        np.zeros((1, 1, 2), dtype=int),
        {0: (0, 0)},
        iter([(0, 0)]),
    ],
)
def test_candidate_grammar_rejections(bad: Any) -> None:
    case = inputs()
    case["candidate_carriers_yx"] = bad
    assert_code(case, "invalid_volume_carrier_candidates")


class CandidateListSubclass(list):
    """A container outside the contract's exact built-in grammar."""


class CandidateArraySubclass(np.ndarray):
    """An ndarray subclass outside the plain candidate-table grammar."""


@pytest.mark.parametrize("kind", ["table_subclass", "row_subclass", "array_subclass", "ragged"])
def test_candidate_container_boundaries(kind: str) -> None:
    case = inputs()
    if kind == "table_subclass":
        bad = CandidateListSubclass([(0, 0)])
    elif kind == "row_subclass":
        bad = [CandidateListSubclass([0, 0])]
    elif kind == "array_subclass":
        bad = np.zeros((1, 2), dtype=int).view(CandidateArraySubclass)
    else:
        bad = [(0, 0), (1,)]
    case["candidate_carriers_yx"] = bad
    assert_code(case, "invalid_volume_carrier_candidates")


@pytest.mark.parametrize(
    "bad", [True, np.bool_(False), 1.0, np.float64(2), 0, -1, 3, "1", None, [1]]
)
def test_order_rejections(bad: Any) -> None:
    case = inputs()
    case["order"] = bad
    assert_code(case, "invalid_volume_carrier_order")


@pytest.mark.parametrize(
    "bad",
    [
        (1.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
        np.ones(3),
        (True, 1.0, 1.0),
        (1 + 0j, 1.0, 1.0),
        ("1", 1.0, 1.0),
        (0.0, 1.0, 1.0),
        (-1.0, 1.0, 1.0),
        (np.inf, 1.0, 1.0),
        (np.nan, 1.0, 1.0),
        (2**2000, 1.0, 1.0),
    ],
)
def test_spacing_rejections_even_with_no_overlap(bad: Any) -> None:
    case = inputs()
    case.update(voxel_size_um=bad, candidate_carriers_yx=[(2**1000, 0)])
    assert_code(case, "invalid_volume_carrier_voxel_size")


@pytest.mark.parametrize(
    "spacing",
    [
        (float.fromhex("0x0.0000000000001p-1022"), 1.0, 1.0),
        (1.0, 1.0, float.fromhex("0x0.0000000000001p-1022")),
    ],
)
def test_full_frequency_axis_range_is_global_before_no_overlap(spacing: Any) -> None:
    case = inputs((2, 3, 4))
    case.update(voxel_size_um=spacing, candidate_carriers_yx=[(2**1000, 0)])
    assert_code(case, "unrepresentable_otf_frequencies")


def test_period_overflow_and_singleton_spacing_are_permitted() -> None:
    case = inputs((1, 1, 4))
    case["voxel_size_um"] = [np.nextafter(0.0, 1.0), np.finfo(float).max, np.finfo(float).max]
    row = scan(case)[0]
    assert_fit(case, row, (0, 0))


@pytest.mark.parametrize("values_zero", [False, True])
def test_rounded_matching_endpoint_is_uncovered_without_snapping(values_zero: bool) -> None:
    case = inputs((1, 1, 5))
    values = np.full((3, 1, 1, 5), 0j if values_zero else 1 + 0j)
    case["response"] = response_from_values(values)
    # RN64(2/5) > exact 2/5. Matching metadata/grids do not grant coverage.
    assert frequency(2, 5, 1.0) > Fraction(2, 5)
    row = scan(case)[0]
    assert row.status == "incomplete_coverage" and row.overlap_count == 5
    assert row.source == case["source"]
    assert row.gain is row.coherence is row.relative_residual is None


@pytest.mark.parametrize("perturb_metadata", [False, True])
def test_each_shifted_query_is_rounded_separately(perturb_metadata: bool) -> None:
    case = inputs((1, 1, 8))
    case.update(
        voxel_size_um=(1.0, 1.0, 0.75),
        candidate_carriers_yx=[(0, 7)],
        response=response_from_values(np.full((3, 1, 1, 4), 1 + 0.2j), (1.0, 1.0, 0.5)),
    )
    if perturb_metadata:
        # Tolerated metadata does not move the exact closed source hull.
        case["response"].fx_per_um[-1] = np.nextafter(0.5, 0.0)
    # Single pair: p=-4, j=3. f(j)=1/2 is covered, whereas adding two
    # independently rounded f(-4)+f(7) gives the next float above the hull.
    assert frequency(3, 8, 0.75) == Fraction(1, 2)
    assert frequency(-4, 8, 0.75) + frequency(7, 8, 0.75) > Fraction(1, 2)
    row = scan(case)[0]
    truth = assert_fit(case, row, (0, 7))
    assert truth.count == 1 and abs(row.coherence - 1.0) < 1e-12


@pytest.mark.parametrize(
    "kind", ["zero_predictor", "zero_response", "zero_correlation", "extra_response"]
)
def test_full_pair_information_outcomes_and_zero_predictor_pairs(kind: str) -> None:
    case = inputs((1, 1, 4))
    values = np.zeros((3, 1, 1, 4), dtype=np.complex128)
    values[1, 0, 0, 2] = 1
    values[0, 0, 0, 3] = 1  # x=0, y!=0 must remain in the response norm.
    if kind == "zero_predictor":
        values[1] = 0
    elif kind == "zero_response":
        values[0] = 0
    elif kind == "extra_response":
        values[0, 0, 0, 2] = 1
    case["response"] = response_from_values(values)
    row = scan(case)[0]
    assert row.overlap_count == 4
    assert row.source == case["source"]
    if kind == "extra_response":
        truth = assert_fit(case, row, (0, 0))
        assert truth.residual > Decimal(".01")
        assert truth.coherence < Decimal(".999")
    else:
        assert row.status == kind
        if kind == "zero_predictor":
            assert row.gain is row.relative_residual is row.coherence is None
        else:
            assert type(row.gain) is complex and row.gain == 0j
            assert type(row.relative_residual) is float
            assert row.relative_residual == (1.0 if kind == "zero_correlation" else 0.0)
            assert type(row.coherence) is float and row.coherence == 0.0


@pytest.mark.parametrize("order", [1, 2])
def test_zero_observed_bands_with_nonzero_response(order: int) -> None:
    case = inputs((1, 1, 1))
    case.update(
        images=np.zeros((5, 1, 1, 1)),
        phase_steps_rad=np.arange(5) * (2 * np.pi / 5),
        response=response_from_values(np.ones((3, 1, 1, 1), dtype=complex)),
        candidate_carriers_yx=[(0, 0), (2**1000, 0), (0, 0)],
        order=order,
    )
    with localcontext() as ctx:
        ctx.prec = PRECISION
        assert phase_condition_upper_bound(case["phase_steps_rad"]) < 10
        dc, cm = bands(case["images"], case["phase_steps_rad"], order)
        assert all(value.re == 0 and value.im == 0 for value in (*dc, *cm))
    # All observed bands vanish. No transform call or zero-band organization is
    # selected: an exact-zero band may bypass the public transform entirely.
    rows = scan(case)
    assert [row.status for row in rows] == ["zero_predictor", "no_overlap", "zero_predictor"]
    assert [row.overlap_count for row in rows] == [1, 0, 1]
    assert [row.carrier_bins_yx for row in rows] == case["candidate_carriers_yx"]
    for row in rows:
        assert row.gain is row.relative_residual is row.coherence is None
        assert row.order == order and row.source == case["source"]


@pytest.mark.parametrize("image_power,transfer_power", [(900, 900), (-900, -900), (0, -700)])
def test_informative_scaled_products_without_raw_product_range(
    image_power: int, transfer_power: int
) -> None:
    case = inputs((1, 2, 3))
    case["images"] *= 2.0**image_power
    base = case["response"]
    case["response"] = dataclasses.replace(base, values=base.values * 2.0**transfer_power)
    assert_fit(case, scan(case)[0], (0, 0))


def test_nonzero_correlation_with_underflowed_gain_stays_fitted() -> None:
    case = inputs((1, 1, 1))
    case["response"] = response_from_values(
        np.array([2.0**-900, 2.0**900, 1.0], dtype=np.complex128).reshape(3, 1, 1, 1)
    )
    row = scan(case)[0]
    assert_fit(case, row, (0, 0))
    assert row.status == "fitted" and row.gain == 0j
    assert row.coherence > 0.99


def test_safe_gain_components_with_overflowing_complex_magnitude() -> None:
    case = inputs((1, 1, 1))
    case["images"] = (phase_matrix(PHASES) @ np.array([1.0, 2.0, -2.0, 0.25, 0.1])).reshape(
        -1, 1, 1, 1
    )
    case["response"] = response_from_values(
        np.array([0.75 * float(FMAX), 1.0, 1.0], dtype=np.complex128).reshape(3, 1, 1, 1)
    )
    truth = assert_fit(case, scan(case)[0], (0, 0))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        assert truth.gain.norm() > FMAX
        assert max(abs(truth.gain.re), abs(truth.gain.im)) + truth.gain_bound < FMAX


def test_fft_normalization_precedes_near_maximum_band_restoration() -> None:
    case = inputs((1, 1, 4))
    exposure = (phase_matrix(PHASES) @ np.array([5.0, 2.0, -1.0, 0.5, 0.25])) * (float(FMAX) / 16)
    case["images"] = np.broadcast_to(exposure[:, None, None, None], (7, 1, 1, 4)).copy()
    case["response"] = response_from_values(np.ones((3, 1, 1, 4), dtype=complex))
    # The raw constant-band sum is 4*(5*Fmax/16)>Fmax; the normalized
    # band, its phase coordinates and final gain have ample finite margins.
    assert_fit(case, scan(case)[0], (0, 0))


def test_tiny_stencil_weights_retain_finite_contributions() -> None:
    case = inputs((1, 1, 3))
    huge = float(FMAX) / 16
    values = np.array([[[huge, 0.0, huge]]] * 3, dtype=np.complex128).reshape(3, 1, 1, 3)
    case.update(
        response=response_from_values(values, (1.0, 1.0, 2.0**-1020)),
        voxel_size_um=(1.0, 1.0, 2.0**1020),
    )
    assert_fit(case, scan(case)[0], (0, 0))


def test_stencil_cancellation_uses_absolute_source_envelope() -> None:
    case = inputs((1, 1, 3))
    values = np.tile(
        np.array([-1e6 + 0.001, 2e6 + 0.001, 0.0, 2e6 + 0.001, -1e6 + 0.001]), (3, 1, 1, 1)
    ).astype(np.complex128)
    case["response"] = response_from_values(values)
    truth = assert_fit(case, scan(case)[0], (0, 0))
    assert truth.stencil_ratio > Decimal("1e-5")
    assert truth.h < Decimal(1) / 64


def test_nearly_collinear_response_has_a_direct_nonzero_residual() -> None:
    case = inputs((1, 1, 4))
    dc = np.array([1.0, 2.0, 3.0, 4.0])
    cm = (0.4 + 0.3j) * dc + 1e-7 * np.array([1.0, -1.0, -1.0, 1.0])
    coefficients = np.stack((dc, 2 * cm.real, -2 * cm.imag, dc / 7, dc / 11))
    case["images"] = (phase_matrix(PHASES) @ coefficients).reshape(7, 1, 1, 4)
    case["response"] = response_from_values(np.ones((3, 1, 1, 4), dtype=complex))
    row = scan(case)[0]
    truth = assert_fit(case, row, (0, 0))
    assert Decimal("1e-9") < truth.residual < Decimal("1e-6")
    assert abs(dec(row.relative_residual) - truth.residual) < Decimal("2e-12")


def test_small_nonzero_correlation_has_no_information_cutoff() -> None:
    case = inputs((1, 1, 4))
    values = np.zeros((3, 1, 1, 4), dtype=complex)
    values[1, 0, 0, 2] = 1
    values[0, 0, 0, 2] = 2.0**-40
    values[0, 0, 0, 3] = 1
    case["response"] = response_from_values(values)
    row = scan(case)[0]
    truth = assert_fit(case, row, (0, 0))
    assert 0 < truth.coherence < Decimal("1e-9")
    assert row.gain != 0j and row.coherence > 0


@pytest.mark.parametrize("order", [np.int8(1), np.uint64(2)])
def test_huge_exact_gauge_and_huge_finite_phase(order: Any) -> None:
    case = inputs((1, 2, 3))
    case.update(
        order=order,
        calibration_carrier_bins=(2**2000 + 3, -(2**1700) + 7),
        coordinate_offset_yx=(-(2**1400) + 1, 2**1900 + 2),
        phase_reference_shift_rad=float(FMAX),
    )
    assert_fit(case, scan(case)[0], (0, 0))


@pytest.mark.parametrize("phase_kind", ["unequal", "huge", "permuted"])
def test_actual_represented_phases_and_joint_permutation(phase_kind: str) -> None:
    case = inputs((1, 2, 3))
    if phase_kind == "huge":
        phases = np.concatenate(
            ([float(FMAX), -float(FMAX), 1e300, -1e299, 1e250, 1e200, 1e100], PHASES)
        )
        assert np.linalg.cond(phase_matrix(phases)) < 10
        case.update(phase_steps_rad=phases, images=observations((1, 2, 3), phases), order=2)
    elif phase_kind == "permuted":
        permutation = np.array([5, 2, 0, 6, 3, 1, 4])
        before = scan(case)[0]
        case.update(
            images=case["images"][permutation], phase_steps_rad=case["phase_steps_rad"][permutation]
        )
        after = scan(case)[0]
        assert abs(after.gain - before.gain) < 2e-11
        assert abs(after.relative_residual - before.relative_residual) < 2e-11
    assert_fit(case, scan(case)[0], (0, 0))


@pytest.mark.parametrize("layout", ["big_endian", "strided", "fortran_readonly", "integer"])
def test_permitted_input_storage_and_preservation(layout: str) -> None:
    case = inputs((2, 3, 4))
    if layout == "big_endian":
        case["images"] = case["images"].astype(">f8")
        case["phase_steps_rad"] = PHASES.astype(">f8")
        base = case["response"]
        case["response"] = dataclasses.replace(
            base,
            values=base.values.astype(">c16"),
            fz_per_um=base.fz_per_um.astype(">f8"),
            fy_per_um=base.fy_per_um.astype(">f8"),
            fx_per_um=base.fx_per_um.astype(">f8"),
        )
    elif layout == "strided":
        case["images"] = case["images"][:, ::-1, ::-1, ::-1]
        holder = np.empty(PHASES.size * 2)
        holder[::2] = PHASES
        case["phase_steps_rad"] = holder[::2]
        base = case["response"]
        storage = np.empty((*base.values.shape[:-1], base.values.shape[-1] * 2), dtype=complex)
        storage[..., ::2] = base.values
        case["response"] = dataclasses.replace(base, values=storage[..., ::2])
    elif layout == "integer":
        case["images"] = np.rint(case["images"] * 32).astype(np.int16)
    else:
        case["images"] = np.asfortranarray(case["images"])
        case["images"].flags.writeable = False
        case["phase_steps_rad"].flags.writeable = False
        case["response"].values.flags.writeable = False
    arrays = [
        case["images"],
        case["phase_steps_rad"],
        case["response"].values,
        case["response"].fz_per_um,
        case["response"].fy_per_um,
        case["response"].fx_per_um,
    ]
    saved = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    assert_fit(case, scan(case)[0], (0, 0))
    case["candidate_carriers_yx"] = [[True, 0]]
    assert_code(case, "invalid_volume_carrier_candidates")
    for array, (copy, strides, writable) in zip(arrays, saved, strict=True):
        np.testing.assert_array_equal(array, copy)
        assert array.strides == strides and array.flags.writeable == writable


@pytest.mark.parametrize(
    "field,bad",
    [
        ("values", np.zeros((2, 1, 1, 1), dtype=complex)),
        ("values", np.zeros((3, 1, 1, 1), dtype=float)),
        ("values", np.full((3, 1, 1, 1), complex(np.nan, 0))),
        ("fz_per_um", np.array([1.0, 2.0, 3.0])),
        ("fy_per_um", np.array([0.0])),
        ("voxel_size_um", np.ones(3)),
        ("origin_zyx", (99, 0, 0)),
    ],
)
def test_all_response_fields_validated_even_if_no_overlap(field: str, bad: Any) -> None:
    case = inputs()
    case["response"] = dataclasses.replace(case["response"], **{field: bad})
    case["candidate_carriers_yx"] = [(2**2000, -(2**2000))]
    assert_code(case, "invalid_empirical_transfer_response")


@pytest.mark.parametrize("carrier", [(0, 0), (10, 0)])
def test_supplemental_non_response_object_is_globally_rejected(carrier: tuple[int, int]) -> None:
    """Post-implementation supplemental proof of the response instance boundary."""
    case = inputs((1, 1, 1))
    case.update(
        images=np.zeros((5, 1, 1, 1)),
        phase_steps_rad=np.arange(5) * (2 * np.pi / 5),
        response=object(),
        candidate_carriers_yx=[carrier],
    )
    assert_code(case, "invalid_empirical_transfer_response")


@pytest.mark.parametrize("carrier", [(0, 0), (10, 0)])
def test_supplemental_response_spacing_must_be_positive(carrier: tuple[int, int]) -> None:
    """Post-implementation supplemental spacing validation, with a valid control."""
    case = inputs((1, 1, 1))
    valid_response = response_from_values(np.ones((3, 1, 1, 1), dtype=complex))
    case.update(
        images=np.zeros((5, 1, 1, 1)),
        phase_steps_rad=np.arange(5) * (2 * np.pi / 5),
        response=valid_response,
        candidate_carriers_yx=[carrier],
    )
    row = scan(case)[0]
    assert row.status == ("zero_predictor" if carrier == (0, 0) else "no_overlap")
    assert row.overlap_count == (1 if carrier == (0, 0) else 0)
    assert row.gain is row.relative_residual is row.coherence is None
    assert row.source == case["source"]
    # Keep all six source fields and the singleton zero frequency vectors.
    # Only source spacing is invalid; specimen spacing and phases remain valid.
    case["response"] = dataclasses.replace(valid_response, voxel_size_um=(0.0, 1.0, 1.0))
    assert_code(case, "invalid_empirical_transfer_response")


def test_unused_response_row_and_unqueried_sample_are_validated() -> None:
    case = inputs((1, 1, 1))
    case["response"].values[2, 0, 0, 0] = complex(1, np.inf)
    assert_code(case, "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "field,code,bad",
    [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier", np.array([0, 0])),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset", (False, 0)),
        ("phase_reference_shift_rad", "invalid_empirical_transfer_phase_shift", np.inf),
    ],
)
def test_sampler_scalar_errors_remain_global(field: str, code: str, bad: Any) -> None:
    case = inputs()
    case.update(candidate_carriers_yx=[(2**1000, 0)])
    case[field] = bad
    assert_code(case, code)


@pytest.mark.parametrize(
    "field,bad,code",
    [
        ("images", np.zeros((7, 1, 1)), "invalid_volume_phase_shape"),
        ("images", np.full((7, 1, 1, 1), np.inf), "nonfinite_volume_phase_images"),
        ("phase_steps_rad", np.zeros(7), "rank_deficient_volume_phases"),
        ("phase_steps_rad", np.full(7, np.nan), "nonfinite_volume_phase_angles"),
    ],
)
def test_inherited_phase_errors_are_not_local_rows(field: str, bad: Any, code: str) -> None:
    case = inputs((1, 1, 1))
    case.update(candidate_carriers_yx=[(2**1000, 0)])
    case[field] = bad
    assert_code(case, code)


@pytest.mark.parametrize("order", [1, 2])
@pytest.mark.parametrize("candidates", [[(0, 0)], [(2**1000, 0)], [(2**1000, 0), (0, 0)]])
def test_inherited_phase_component_range_failure_is_global(order: int, candidates: Any) -> None:
    case = inputs((1, 1, 1))
    case.update(
        images=(np.array([1.0, -1.0, 1.0, -1.0, 1.0]) * (float(FMAX) / 16)).reshape(5, 1, 1, 1),
        phase_steps_rad=0.5 * np.arange(5),
        response=response_from_values(np.ones((3, 1, 1, 1), dtype=complex)),
        candidate_carriers_yx=candidates,
        order=order,
    )
    assert np.isfinite(case["images"]).all()
    singular = np.linalg.svd(phase_matrix(case["phase_steps_rad"]), compute_uv=False)
    tau = np.finfo(float).eps * 5 * singular[0]
    assert singular[-1] > 10**8 * tau
    with localcontext() as ctx:
        ctx.prec = PRECISION
        solution = solve_exact(case["images"], case["phase_steps_rad"])
        assert dec(solution[0][0]) > 3 * FMAX
    # The exact represented-input dc is far outside range. Observe the real
    # prerequisite's operational error as well; neither rank failure nor a
    # nonfinite input explains it. Even all-no-overlap must propagate that error.
    with pytest.raises(SimreconError) as caught:
        separate_volume_phases(case["images"], phases_rad=case["phase_steps_rad"])
    assert caught.value.code == "unrepresentable_volume_phase_components"
    assert_code(case, "unrepresentable_volume_phase_components")


class GetterFailure(RuntimeError):
    """An unrelated public response property failure."""


class SourceGetterTrapResponse(EmpiricalVolumeResponse):
    """A six-field record subclass detecting a forbidden source getter read."""

    @property
    def source(self) -> str:
        """Fail if scan incorrectly consults a response source attribute."""
        raise GetterFailure("response.source must not be read")


def test_response_source_getter_is_never_read() -> None:
    case = inputs()
    base = case["response"]
    fields = {field.name: getattr(base, field.name) for field in dataclasses.fields(base)}
    case["response"] = SourceGetterTrapResponse(**fields)
    case["source"] = "explicit label independent of response"
    row = scan(case)[0]
    assert_fit(case, row, (0, 0))


class UnreadableResponse(EmpiricalVolumeResponse):
    """A permitted record subclass with an unrelated failing getter."""

    def __getattribute__(self, name: str) -> Any:
        """Raise outside the handled missing-attribute category."""
        if name == "values":
            raise GetterFailure("unrelated response getter")
        return super().__getattribute__(name)


class MissingValuesResponse(EmpiricalVolumeResponse):
    """A record subclass whose required values attribute is missing."""

    def __getattribute__(self, name: str) -> Any:
        """Expose the specified missing-required-field boundary."""
        if name == "values":
            raise AttributeError("missing required response field")
        return super().__getattribute__(name)


def test_response_getter_failure_ownership() -> None:
    case = inputs()
    base = response()
    fields = {field.name: getattr(base, field.name) for field in dataclasses.fields(base)}
    case["response"] = UnreadableResponse(**fields)
    with pytest.raises(GetterFailure, match="unrelated response getter"):
        scan(case)
    case["response"] = MissingValuesResponse(**fields)
    assert_code(case, "invalid_empirical_transfer_response")


@pytest.mark.parametrize("failure", ["floating", "overflow", "warning", "nonfinite"])
def test_fft_arithmetic_failures_are_global_even_under_ignore(
    monkeypatch: Any, failure: str
) -> None:
    case = inputs()
    case["candidate_carriers_yx"] = [(2**1000, 0), (0, 0)]

    def broken(a: Any, *args: Any, **kwargs: Any) -> Any:
        if failure == "floating":
            raise FloatingPointError("injected FFT arithmetic")
        if failure == "overflow":
            raise OverflowError("injected FFT arithmetic")
        if failure == "warning":
            warnings.warn("injected FFT arithmetic", RuntimeWarning, stacklevel=2)
            return np.zeros(np.asarray(a).shape, dtype=complex)
        return np.full(np.asarray(a).shape, complex(np.inf, 0))

    monkeypatch.setattr(np.fft, "fftn", broken)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        saved_filters = list(warnings.filters)
        with np.errstate(all="raise"):
            modes = np.geterr().copy()
            assert_code(case, "volume_carrier_transform_failure")
            assert np.geterr() == modes and warnings.filters == saved_filters


@pytest.mark.parametrize("error_type", [RuntimeError, TypeError, ValueError, MemoryError])
def test_unrelated_fft_exceptions_propagate(monkeypatch: Any, error_type: Any) -> None:
    case = inputs()
    error = error_type("unrelated FFT failure")

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(np.fft, "fftn", broken)
    with pytest.raises(error_type) as caught:
        scan(case)
    assert caught.value is error


def test_fft_input_is_scaled_before_the_public_transform(monkeypatch: Any) -> None:
    case = inputs()
    case["images"] *= 2.0**900
    real_fft = np.fft.fftn
    calls = []

    def checked(a: Any, *args: Any, **kwargs: Any) -> Any:
        array = np.asarray(a)
        assert max(np.max(np.abs(array.real)), np.max(np.abs(array.imag))) <= 1.0
        # No private count or axis/batching organization is required.
        calls.append(array.shape)
        return real_fft(a, *args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", checked)
    assert_fit(case, scan(case)[0], (0, 0))
    assert calls


def test_snapshot_before_fft_and_interpolation(monkeypatch: Any) -> None:
    case = inputs((1, 2, 3))
    case.update(
        candidate_carriers_yx=[[0, 0], [2**1000, 0]],
        voxel_size_um=[1.0, 1.0, 1.0],
        calibration_carrier_bins=[0, 0],
        coordinate_offset_yx=[0, 0],
    )
    truth = expected(
        case["images"], case["phase_steps_rad"], case["response"], case["voxel_size_um"], (0, 0), 1
    )
    assert truth is not None and truth.informative and truth.success_margin
    real_fft = np.fft.fftn
    touched = []

    def mutate_then_fft(*args: Any, **kwargs: Any) -> Any:
        if not touched:
            touched.append(True)
            case["images"][...] = np.nan
            case["phase_steps_rad"][...] = np.nan
            case["response"].values[...] = np.nan
            case["response"].fx_per_um[...] = np.nan
            case["candidate_carriers_yx"][0][0] = 2**1000
            case["voxel_size_um"][0] = -1
            case["calibration_carrier_bins"][0] = 8
            case["coordinate_offset_yx"][0] = 9
            case["source"] = "caller changed its declaration"
        return real_fft(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", mutate_then_fft)
    rows = scan(case)
    assert touched and rows[0].carrier_bins_yx == (0, 0)
    assert rows[1].status == "no_overlap"
    assert all(row.source == SOURCE for row in rows)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        assert (z(rows[0].gain) - truth.gain).norm() <= truth.gain_bound


def test_unrelated_warning_and_success_policy_preservation(monkeypatch: Any) -> None:
    case = inputs()
    real_fft = np.fft.fftn

    def warned(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("visible unrelated FFT warning", UserWarning, stacklevel=2)
        return real_fft(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warned)
    with warnings.catch_warnings():
        warnings.simplefilter("always", UserWarning)
        before = list(warnings.filters)
        with np.errstate(all="raise"):
            modes = np.geterr().copy()
            with pytest.warns(UserWarning, match="visible unrelated FFT warning"):
                row = scan(case)[0]
            assert np.geterr() == modes and warnings.filters == before
    assert_fit(case, row, (0, 0))


def test_interpolation_range_failure_is_global_not_a_coverage_row() -> None:
    case = inputs((1, 1, 1))
    huge = 0.9 * float(FMAX)
    values = np.array([1 + 0j, complex(huge, huge), 1 + 0j]).reshape(3, 1, 1, 1)
    case.update(
        response=response_from_values(values),
        phase_reference_shift_rad=np.pi / 4,
        candidate_carriers_yx=[(2**1000, 0), (0, 0)],
    )
    assert_code(case, "unrepresentable_empirical_interpolation")


def test_gain_restoration_range_failure_is_global() -> None:
    case = inputs((1, 1, 1))
    case["response"] = response_from_values(
        np.array([2.0**900, 2.0**-900, 1.0], dtype=complex).reshape(3, 1, 1, 1)
    )
    case["candidate_carriers_yx"] = [(2**1000, 0), (0, 0)]
    assert_code(case, "unrepresentable_volume_carrier_fit")


def test_single_pair_does_not_establish_a_unique_physical_carrier() -> None:
    case = inputs((1, 1, 3))
    case["candidate_carriers_yx"] = [(0, -2), (0, 2), (0, -2)]
    rows = scan(case)
    for row, carrier in zip(rows, case["candidate_carriers_yx"], strict=True):
        assert_fit(case, row, carrier)
        assert row.overlap_count == 1
        assert abs(row.coherence - 1.0) < 1e-12 and row.relative_residual < 1e-12
    assert rows[0] == rows[2] and rows[0] is not rows[2]
    # Both opposite candidates fit perfectly. No winner or physical truth is inferred.


@pytest.mark.parametrize("order,size,carrier,alias", [(1, 5, 1, 6), (2, 6, 1, 4)])
def test_sampled_carrier_aliases_are_not_resolved_by_the_window(
    order: int, size: int, carrier: int, alias: int
) -> None:
    case = inputs((1, 1, size))
    dc = 1 + np.arange(size) / 7
    with localcontext() as ctx:
        ctx.prec = PRECISION
        wave = [root(Fraction(-order * carrier * r, size)) for r in range(size)]
        aliased_wave = [root(Fraction(-order * alias * r, size)) for r in range(size)]
    assert wave == aliased_wave
    cm = (0.3 + 0.2j) * dc * np.array([complex(float(v.re), float(v.im)) for v in wave])
    coefficients = np.zeros((5, size))
    coefficients[0] = dc
    coefficients[2 * order - 1] = 2 * cm.real
    coefficients[2 * order] = -2 * cm.imag
    case.update(
        images=(phase_matrix(PHASES) @ coefficients).reshape(7, 1, 1, size),
        response=response_from_values(np.ones((3, 3, 5, 7), dtype=complex), (0.25, 0.125, 0.125)),
        order=order,
        candidate_carriers_yx=[(0, carrier), (0, alias)],
    )
    fitted, absent = scan(case)
    assert_fit(case, fitted, (0, carrier))
    assert abs(fitted.gain - (0.3 + 0.2j)) < 2e-12
    assert fitted.relative_residual < 2e-12
    assert absent.status == "no_overlap" and absent.overlap_count == 0
    # The same sampled illumination has two physical declarations. The absent
    # row describes this nonwrapping window, not exclusion of the physical alias.


def test_raw_bead_correction_calibration_to_specimen_scan() -> None:
    # A finite synthetic point response; actual phases differ from nominal commands.
    shape = (1, 3, 3)
    grid = np.arange(9, dtype=float).reshape(shape)
    dc = 1 + grid / 32
    dc[0, 1, 2] = 4
    coefficients = np.stack(
        (dc, 0.2 + grid / 53, -0.3 + grid / 71, 0.1 + grid / 83, 0.15 - grid / 97)
    )
    signal = (phase_matrix(PHASES) @ coefficients.reshape(5, -1)).reshape(7, *shape)
    raw = (8.0 + 2.0 * signal)[None]
    acquisition = declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "count",
            "nominal_phases_rad": [[0.0] * 7],
            "sampling_um": {"z": 2.0, "y": 2.0, "x": 2.0},
        },
    )
    bead = calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=8.0,
        response=2.0,
        output_unit="electron",
        phases_rad=PHASES,
        voxel_size_um=(1.0, 1.0, 1.0),
    )
    # Use the unwrapped six-field calibration record. Its independently
    # specified origin/mass/finite DFT are checked below, not trusted.
    measured = bead.response
    with localcontext() as ctx:
        ctx.prec = PRECISION
        corrected = (raw[0] - 8.0) / 2.0
        dc_exact, cm1 = bands(corrected, PHASES, 1)
        _, cm2 = bands(corrected, PHASES, 2)
        peak = max(range(9), key=lambda i: dc_exact[i].re)
        assert tuple(np.unravel_index(peak, shape)) == measured.origin_zyx
        mass = sum((v.re for v in dc_exact), Decimal(0))
        origin = tuple(int(v) for v in np.unravel_index(peak, shape))
        rolled = []
        for band in (dc_exact, cm1, cm2):
            rolled.append(
                [
                    band[
                        np.ravel_multi_index(
                            tuple((r + b) % n for r, b, n in zip(site, origin, shape, strict=True)),
                            shape,
                        )
                    ]
                    for site in np.ndindex(shape)
                ]
            )
        reference_values = np.empty((3, *shape), dtype=complex)
        # Common mass and peak are separated from a physically exact scene.
        # Separator uncertainty: alpha per real coordinate, 2*alpha for a side.
        alpha = 8192 * len(PHASES) * EPS * max(abs(dec(v)) for v in corrected.flat) + 8 * Q0
        assert mass > 9 * alpha
        assert (
            dc_exact[peak].re - max(v.re for i, v in enumerate(dc_exact) if i != peak) > 2 * alpha
        )
        source_error = Decimal(0)
        for order in range(3):
            coordinate_error = alpha if order == 0 else 2 * alpha
            l1 = sum((abs(v.re) + abs(v.im) for v in rolled[order]), Decimal(0))
            for index in np.ndindex(shape):
                mode = tuple(i - n // 2 for i, n in zip(index, shape, strict=True))
                reference = finite_dft(rolled[order], mode, shape).scale(Decimal(9) / mass)
                propagated = (9 * coordinate_error + reference.norm() * 9 * alpha) / (
                    mass - 9 * alpha
                )
                # Bound the empirical transform's Lambda on all permitted
                # separated outputs, without using their observed values.
                empirical = (
                    512 * 9 * EPS * (l1 + 18 * coordinate_error) / (mass - 9 * alpha) + 16 * 9 * Q0
                )
                bound = propagated + empirical
                assert (z(measured.values[(order, *index)]) - reference).norm() <= bound
                reference_values[(order, *index)] = complex(
                    float(reference.re), float(reference.im)
                )
                rounding = (z(reference_values[(order, *index)]) - reference).norm()
                source_error = max(source_error, bound + rounding)
    specimen_signal = observations((1, 2, 2), PHASES)
    specimen_raw = 12.0 + 4.0 * specimen_signal
    specimen = declare_acquisition(
        specimen_raw[None],
        config={
            "version": 1,
            "acquisition_kind": "specimen_sim",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "count",
        },
    )
    corrected_specimen = correct_linear_response(
        specimen, offset=12.0, response=4.0, output_unit="electron"
    )
    independently_corrected = (specimen_raw - 12.0) / 4.0
    np.testing.assert_array_equal(corrected_specimen.data[0], independently_corrected)
    case = inputs((1, 2, 2))
    case.update(
        images=corrected_specimen.data[0],
        response=measured,
        voxel_size_um=(1.0, 2.0, 2.0),
        calibration_carrier_bins=(2, -1),
        coordinate_offset_yx=(1, -1),
        phase_reference_shift_rad=0.23,
        candidate_carriers_yx=[(0, 0), (0, 1)],
    )
    independent_response = response_from_values(reference_values, (1.0, 1.0, 1.0), origin)
    for row, carrier in zip(scan(case), case["candidate_carriers_yx"], strict=True):
        # Expectation uses independently derived source samples. Upstream
        # calibration uncertainty is separate from scan arithmetic/model error.
        truth = expected(
            independently_corrected,
            PHASES,
            independent_response,
            case["voxel_size_um"],
            carrier,
            1,
            (2, -1),
            (1, -1),
            0.23,
            source_error=source_error,
        )
        assert truth is not None and truth.informative and truth.success_margin
        assert row.status == "fitted" and row.overlap_count == truth.count
        assert row.source == case["source"]
        with localcontext() as ctx:
            ctx.prec = PRECISION
            assert (z(row.gain) - truth.gain).norm() <= truth.gain_bound
            assert abs(dec(row.coherence) - truth.coherence) <= truth.coherence_bound
            assert abs(dec(row.relative_residual) - truth.residual) <= truth.residual_bound
