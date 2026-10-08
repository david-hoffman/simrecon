"""CARRIER-SCAN-01 blind A public-contract tests (C01--C12).

Expectations use finite sums and exact represented-value least squares in the
owned fixture. All product access is through public exports.
"""

import warnings
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
import pytest
import scipy.fft

import simrecon as sr
from carrier_fixture import (
    Acquisition,
    Complex,
    Fit,
    acquisition,
    decimal_pi,
    decimal_sin_cos,
    delta,
    fit,
    image_dtype_acquisition,
    informative,
    large_step_acquisition,
    overflow_ratio_acquisition,
    stored_fits,
    synthesize,
    two_pixel,
)


class ArraySubclass(np.ndarray):
    """Explicitly forbidden ndarray subclass for public representation tests."""


def export(name: str) -> Any:
    """Resolve exports at execution time so an absent API cannot break collection."""
    return getattr(sr, name)


def scan(case: Acquisition, candidates: Any, **changes: Any) -> Any:
    kwargs = {
        "otf": case.otf(sr),
        "phase_steps_rad": case.steps,
        "candidate_carriers_bins_yx": candidates,
    }
    kwargs.update(changes)
    return export("scan_carriers")(case.images, **kwargs)


def assert_code(code: str, call: Any) -> None:
    with pytest.raises(export("SimreconError")) as raised:
        call()
    assert raised.value.code == code
    assert isinstance(raised.value.message, str)


def assert_success_record(record: Any, case: Acquisition, overlap: int) -> Any:
    assert isinstance(record, export("CarrierCandidate"))
    assert record.failure_code is None
    estimate = record.estimate
    assert isinstance(estimate, export("IlluminationEstimate"))
    for name in ("modulation", "phase_offset_rad", "relative_residual"):
        assert type(getattr(estimate, name)) is float
        assert np.isfinite(getattr(estimate, name))
    assert type(estimate.overlap_count) is int
    assert estimate.overlap_count == overlap
    assert estimate.modulation > 0
    assert estimate.relative_residual >= 0
    assert estimate.source == case.source
    assert -np.pi <= estimate.phase_offset_rad <= np.pi
    phases = estimate.phases_rad
    assert type(phases) is np.ndarray
    assert phases.dtype == np.dtype(np.float64)
    assert phases.shape == case.steps.shape
    assert phases.flags.c_contiguous and phases.flags.writeable and phases.flags.owndata
    assert np.all(np.abs(phases) <= np.pi)
    # Circular observer permits either represented sign at the branch cut.
    rotation = (np.cos(case.steps) + 1j * np.sin(case.steps)) * np.exp(
        1j * estimate.phase_offset_rad
    )
    np.testing.assert_allclose(np.exp(1j * phases), rotation, atol=3e-14, rtol=0)
    assert not np.shares_memory(phases, case.images)
    assert not np.shares_memory(phases, case.steps)
    return estimate


def assert_fit(record: Any, expected: Fit, case: Acquisition, *, accuracy: bool = True) -> None:
    estimate = assert_success_record(record, case, expected.overlap)
    if accuracy:
        # No caller may apply the digit budget outside any selected prerequisite.
        assert informative(case, expected)
        gain = 0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad)
        budget = delta(case)
        assert abs(gain - expected.gain) <= budget * max(1.0, abs(expected.gain))
        assert abs(estimate.relative_residual - expected.residual) <= budget


def assert_failure(record: Any, code: str) -> None:
    assert isinstance(record, export("CarrierCandidate"))
    assert record.estimate is None
    assert record.failure_code == code


def test_public_exports_binding_and_record() -> None:
    case = acquisition()
    function = export("scan_carriers")
    record_type = export("CarrierCandidate")
    kwargs = dict(otf=case.otf(sr), phase_steps_rad=case.steps, candidate_carriers_bins_yx=[(1, 1)])
    result = function(case.images, **kwargs)
    assert type(result) is tuple and len(result) == 1
    assert isinstance(result[0], record_type)
    for omitted in kwargs:
        with pytest.raises(TypeError):
            function(case.images, **{k: v for k, v in kwargs.items() if k != omitted})
    with pytest.raises(TypeError):
        function(case.images, kwargs["otf"], case.steps, [(1, 1)])
    with pytest.raises(TypeError):
        function(case.images, **kwargs, extra=True)
    with pytest.raises(TypeError):
        function(**kwargs)


@pytest.mark.parametrize("shape", [(5, 7), (6, 8), (5, 8), (6, 7)])
@pytest.mark.parametrize("off_model", [False, True])
def test_independent_multicandidate_landscape(shape: tuple[int, int], off_model: bool) -> None:
    case = acquisition(shape, off_model=off_model)
    carriers = [(1, 1), (0, 1), (-1, -1), (0, 0), (1, 1), (10**100, 0)]
    expected = stored_fits(case, carriers)
    result = scan(case, carriers)
    assert type(result) is tuple and len(result) == len(carriers)
    for record, carrier, reference in zip(result, carriers, expected, strict=True):
        assert record.carrier_bins_yx == carrier
        assert type(record.carrier_bins_yx) is tuple
        assert all(type(v) is int for v in record.carrier_bins_yx)
        if isinstance(reference, Fit):
            accuracy = informative(case, reference)
            if off_model:
                assert accuracy  # All four independent diagnostic fits carry accuracy obligations.
            # The analytic cross product is exactly zero. Stored rounding can
            # yield computed zero or a tiny gain; no uniform digit claim applies.
            if (
                not off_model
                and carrier == (-1, -1)
                and record.failure_code == "unidentifiable_illumination"
            ):
                assert_failure(record, "unidentifiable_illumination")
                continue
            assert_fit(record, reference, case, accuracy=accuracy)
        else:
            assert_failure(record, reference)
    if not off_model:
        true_gain = case.modulation / 2 * np.exp(1j * case.theta)
        assert isinstance(expected[0], Fit)
        assert abs(expected[0].gain - true_gain) < 2e-13
        assert result[0].estimate.relative_residual < 2e-11
    # Different overlaps give different fits. A scalar residual cannot rank truth.
    gains = [reference.gain for reference in expected[:4] if isinstance(reference, Fit)]
    assert max(abs(a - b) for a in gains for b in gains) > 0.02


@pytest.mark.parametrize(
    "representation",
    ["list", "tuple", "native", "big-endian", "strided", "readonly", "object", "mixed-rows"],
)
def test_legitimate_candidate_representations(representation: str) -> None:
    case = acquisition()
    rows = [(np.int64(1), np.uint64(1)), (np.int32(-1), np.int16(-1)), (0, 0), (1, 1)]
    candidates: Any = rows
    if representation == "tuple":
        candidates = tuple(tuple(row) for row in rows)
    elif representation in ("native", "big-endian", "strided", "readonly", "object"):
        candidates = np.array(
            rows,
            dtype=object
            if representation == "object"
            else ">i8"
            if representation == "big-endian"
            else "i8",
        )
        if representation == "strided":
            storage = np.empty((8, 4), dtype=np.int64)
            storage[::2, ::2] = candidates
            candidates = storage[::2, ::2]
        if representation == "readonly":
            candidates.flags.writeable = False
    elif representation == "mixed-rows":
        candidates = [
            list(rows[0]),
            np.array(rows[1], dtype=">i8"),
            np.array(rows[2], dtype=object),
            rows[3],
        ]
    before = np.array(candidates, dtype=object, copy=True)
    result = scan(case, candidates)
    assert [record.carrier_bins_yx for record in result] == [(1, 1), (-1, -1), (0, 0), (1, 1)]
    assert all(all(type(v) is int for v in record.carrier_bins_yx) for record in result)
    np.testing.assert_array_equal(np.array(candidates, dtype=object), before)
    if isinstance(candidates, np.ndarray):
        candidates.flags.writeable = True
        candidates[0, 0] = 99
        assert result[0].carrier_bins_yx == (1, 1)


def invalid_candidates() -> list[Any]:
    return [
        [],
        (),
        np.empty((0, 2), dtype=int),
        None,
        1,
        "1,2",
        {(1, 1)},
        iter([(1, 1)]),
        (row for row in [(1, 1)]),
        np.array([1, 1]),
        np.array(1),
        np.ones((2, 2, 1), dtype=int),
        np.ones((2, 3), dtype=int),
        np.ones((1, 2), dtype=int).view(ArraySubclass),
        [()],
        [(1,)],
        [(1, 1, 1)],
        [None],
        [1],
        ["12"],
        [iter((1, 1))],
        [{1, 2}],
        [(True, 1)],
        [(1, np.bool_(False))],
        [(1.0, 1)],
        [(1, np.float64(1))],
        [(1 + 0j, 1)],
        [("1", 1)],
        np.array([[1.0, 1.0]]),
        np.array([[True, False]]),
        np.array([[1, None]], dtype=object),
        [np.array([[1, 1]])],
        [np.array([1, 1]).view(ArraySubclass)],
        [(1, 1), (0,)],
        [np.array([1, 1]), np.array([1, 0, 1])],
    ]


@pytest.mark.parametrize("candidates", invalid_candidates())
def test_invalid_candidates(candidates: Any) -> None:
    case = acquisition()
    before = case.images.copy(), case.steps.copy(), case.transfer.copy()
    assert_code("invalid_carrier_candidates", lambda: scan(case, candidates))
    for original, snapshot in zip((case.images, case.steps, case.transfer), before, strict=True):
        np.testing.assert_array_equal(original, snapshot)


def patch_public_calls(monkeypatch: Any, targets: Any, replacement: Any) -> list[str]:
    """Instrument actual public-boundary calls, allowing earlier captured bindings."""
    hits: list[str] = []

    def instrument(original: Any, label: str) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            hits.append(label)
            return replacement(original, *args, **kwargs)

        return wrapped

    for provider, name in targets:
        monkeypatch.setattr(
            provider, name, instrument(getattr(provider, name), f"{provider.__name__}.{name}")
        )
    return hits


def patch_transforms(monkeypatch: Any, replacement: Any) -> list[str]:
    return patch_public_calls(
        monkeypatch,
        [(provider, name) for provider in (np.fft, scipy.fft) for name in ("fft", "fft2", "fftn")],
        replacement,
    )


def assert_observed_fault_or_success(
    call: Any,
    hits: list[str],
    on_success: Any,
    *,
    code: str | None = None,
    error: Exception | None = None,
) -> None:
    """Require fault semantics only after an observed injected-boundary call.

    Unreached faults require a substantive independent success observer. They do
    not verify fault handling; later C/D must cover any unreached execution path.
    """
    previous = len(hits)
    try:
        result = call()
    except Exception as caught:
        if len(hits) == previous:
            raise  # Includes absent API; never label an unobserved exception injected.
        if error is not None:
            assert caught is error
        else:
            assert code is not None
            assert isinstance(caught, export("SimreconError"))
            domain_error: Any = caught
            assert domain_error.code == code
            assert isinstance(domain_error.message, str)
    else:
        assert len(hits) == previous, "observed injected failure was swallowed"
        on_success(result)


def assert_conditional_scan_fault(
    case: Acquisition,
    carriers: Any,
    hits: list[str],
    *,
    code: str | None = None,
    error: Exception | None = None,
    otf: Any = None,
) -> None:
    expected = stored_fits(case, carriers)

    def success(result: Any) -> None:
        assert type(result) is tuple and len(result) == len(carriers)
        for record, carrier, reference in zip(result, carriers, expected, strict=True):
            assert record.carrier_bins_yx == tuple(carrier)
            if isinstance(reference, Fit):
                assert_fit(record, reference, case)  # Informative successful controls.
            else:
                assert_failure(record, reference)

    changes = {} if otf is None else {"otf": otf}
    assert_observed_fault_or_success(
        lambda: scan(case, carriers, **changes), hits, success, code=code, error=error
    )


def test_fault_observer_selfcheck_captured_and_reached_public_functions(monkeypatch: Any) -> None:
    captured = np.fft.fft
    error = RuntimeError("controlled public numeric self-check")

    def fail(original: Any, *args: Any, **kwargs: Any) -> Any:
        raise error

    hits = patch_transforms(monkeypatch, fail)

    def success(result: Any) -> None:
        np.testing.assert_array_equal(result, np.array([1.0, 1.0], dtype=complex))

    assert_observed_fault_or_success(
        lambda: captured(np.array([1.0, 0.0])), hits, success, error=error
    )
    assert hits == []
    assert_observed_fault_or_success(
        lambda: np.fft.fft(np.array([1.0, 0.0])), hits, success, error=error
    )
    assert len(hits) == 1


def test_entire_candidate_representation_rejects_later_row_without_prefix_result() -> None:
    case = acquisition()
    otf = case.otf(sr)
    reference = stored_fits(case, [(1, 1)])[0]
    assert isinstance(reference, Fit)
    assert_fit(scan(case, [(1, 1)], otf=otf)[0], reference, case)
    # All common inputs remain valid. No injected simultaneous fault chooses an
    # unspecified error precedence or assumes common preparation is a candidate.
    candidates = np.array([[1, 1], [0, False]], dtype=object)
    arrays = [case.images, case.steps, otf.values, otf.fy_per_um, otf.fx_per_um, candidates]
    before = [array.copy() for array in arrays]
    assert_code("invalid_carrier_candidates", lambda: scan(case, candidates, otf=otf))
    for array, snapshot in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, snapshot)


@pytest.mark.parametrize("representation", ["list", "tuple", "object-array"])
def test_huge_integers_no_wrap_and_no_default_count_cap(representation: str) -> None:
    case = acquisition()
    huge = 10**200
    rows = [(huge, 0), (0, -huge), (np.uint64(2**64 - 1), 0), (0, 0)]
    candidates = (
        np.array(rows, dtype=object)
        if representation == "object-array"
        else tuple(rows)
        if representation == "tuple"
        else rows
    )
    result = scan(case, candidates)
    assert [record.carrier_bins_yx for record in result] == rows
    for record in result[:3]:
        assert_failure(record, "no_illumination_overlap")
    assert result[3].estimate is not None
    # This is a finite example, not a claimed exhaustive proof of no cap.
    repeated = scan(case, [(huge, 0)] * 257)
    assert len(repeated) == 257
    assert all(record.failure_code == "no_illumination_overlap" for record in repeated)


@pytest.mark.parametrize("shape", [(1, 1), (1, 2), (2, 1), (3, 4), (4, 3)])
def test_closed_grid_endpoints_singletons_and_one_pair(shape: tuple[int, int]) -> None:
    ny, nx = shape
    base = two_pixel()
    steps = base.steps
    y, x = np.indices(shape)
    dc = 2 + 0.1 * y + 0.2 * x + 0.03 * x * y
    c1 = 0.3 + 0.05 * y + 0.07 * x + 1j * (0.2 + 0.03 * y * x)
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in steps])
    transfer = np.ones(shape, dtype=np.complex128)
    case = Acquisition(images, steps, transfer, transfer.copy(), transfer.copy())
    carriers = [(0, 0), (ny - 1, nx - 1), (-(ny - 1), -(nx - 1)), (ny, 0), (0, -nx)]
    result = scan(case, carriers)
    expected = stored_fits(case, carriers)
    assert result[0].estimate.overlap_count == ny * nx
    for record, reference in zip(result, expected, strict=True):
        if isinstance(reference, Fit):
            assert_fit(record, reference, case, accuracy=informative(case, reference))
        else:
            assert_failure(record, reference)
    for record in result[-2:]:
        assert_failure(record, "no_illumination_overlap")


def test_one_pair_ambiguity_and_above_one_fit_are_successes() -> None:
    case = two_pixel(plus=0.9 + 0.4j)
    carriers = [(0, -1), (0, -1), (0, 2)]
    result = scan(case, carriers)
    expected = stored_fits(case, carriers)
    for record, reference in zip(result[:2], expected[:2], strict=True):
        assert isinstance(reference, Fit)
        assert_fit(record, reference, case)
        assert record.estimate.overlap_count == 1
        assert record.estimate.modulation > 1
        assert record.estimate.relative_residual < 2e-11
    assert_failure(result[2], "no_illumination_overlap")


def test_distinct_one_pair_candidates_both_have_exact_fit_without_selection() -> None:
    base = two_pixel()
    dc = np.array([[0.4, 0.2, 0.4]], dtype=np.complex128)
    plus = np.array([[0.35 + 0.05j, 0, 0.3 - 0.08j]], dtype=np.complex128)
    spatial_dc, spatial_plus = synthesize(dc).real, synthesize(plus)
    images = np.array(
        [
            spatial_dc + 2 * (spatial_plus.real * np.cos(p) - spatial_plus.imag * np.sin(p))
            for p in base.steps
        ]
    )
    case = Acquisition(images, base.steps, np.ones((1, 3), dtype=np.complex128), dc, plus)
    carriers = [(0, 2), (0, -2)]
    reference = stored_fits(case, carriers)
    result = scan(case, carriers)
    assert len(result) == 2
    for record, expected in zip(result, reference, strict=True):
        assert isinstance(expected, Fit)
        assert expected.norm_x >= 1 / 8 and expected.norm_y >= 1 / 8
        assert_fit(record, expected, case)
        assert record.estimate.overlap_count == 1
        assert record.estimate.relative_residual < 2e-11
    assert abs(result[0].estimate.modulation - result[1].estimate.modulation) > 0.1


@pytest.mark.parametrize("information", ["zero-x", "zero-y", "zero-cross"])
def test_local_information_failures_all_failed_and_continued_scan(information: str) -> None:
    case = two_pixel(transfer_edge=0)
    local = (0, -1)  # x=H(-1)*D0(0)=0, y=Dplus(-1) != 0.
    if information == "zero-y":
        local = (0, 1)  # y=H(-1)*Dplus(0)=0, regardless of separation roundoff.
    elif information == "zero-cross":
        # For k=1 on [-1,0,1], a DC-only OTF makes x nonzero only at
        # q=-1 and y nonzero only at q=0. Products are EXACTLY zero.
        steps = case.steps
        dc = np.array([[1.0, -0.5, -0.5]])
        angles = 2 * np.pi * np.arange(3) / 3
        c1: Complex = np.exp(1j * angles)[None, :]
        images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in steps])
        transfer = np.array([[0, 1, 0]], dtype=np.complex128)
        case = Acquisition(images, steps, transfer, transfer.copy(), transfer.copy())
        local = (0, 1)
    rows = [local, (0, 3), (10**100, -(10**100)), local]
    result = scan(case, rows)
    assert len(result) == len(rows)
    assert_failure(result[0], "unidentifiable_illumination")
    assert_failure(result[1], "no_illumination_overlap")
    assert_failure(result[2], "no_illumination_overlap")
    assert_failure(result[3], "unidentifiable_illumination")


def test_mixed_success_local_failures_and_geometric_zero_transfer_count() -> None:
    case = two_pixel()
    case.transfer[0, 0] = 0
    # At k=-1, x=0 but y is informative: local zero-x. At k=0 DC is
    # informative, while plus DC is only roundoff; avoid assuming zero-y.
    case.images[:] = 0
    result = scan(case, [(0, -1), (0, 2)])
    assert_failure(result[0], "unidentifiable_illumination")
    assert_failure(result[1], "no_illumination_overlap")
    # Exact constant temporal/spatial signal times a known relative harmonic.
    scalar = (2 + 0.6 * np.cos(case.steps + 0.4))[:, None, None]
    case.images = np.broadcast_to(scalar, (len(case.steps), 1, 2)).copy()
    result = scan(case, [(0, 2), (0, 0), (0, -1), (0, 0)])
    assert_failure(result[0], "no_illumination_overlap")
    assert result[1].estimate.overlap_count == 2
    assert_failure(result[2], "unidentifiable_illumination")
    assert result[3].estimate is not None
    assert abs(result[1].estimate.modulation - 0.3) < 2e-11


def invalid_common_cases() -> list[tuple[str, str, Any]]:
    return [
        ("images", "invalid_phase_images", [[[1.0]]]),
        ("images", "invalid_phase_images", np.ones((5, 5, 7)).view(ArraySubclass)),
        ("images", "invalid_phase_dtype", np.ones((5, 5, 7), dtype=bool)),
        ("images", "invalid_phase_dtype", np.ones((5, 5, 7), dtype=complex)),
        ("images", "invalid_phase_dtype", np.ones((5, 5, 7), dtype=object)),
        ("images", "invalid_phase_shape", np.ones((2, 5, 7))),
        ("images", "invalid_phase_shape", np.ones((5, 0, 7))),
        ("images", "invalid_phase_shape", np.ones((5, 7))),
        ("images", "nonfinite_phase_images", np.full((5, 5, 7), np.nan)),
        ("images", "nonfinite_phase_images", np.full((5, 5, 7), np.inf)),
        ("phase_steps_rad", "invalid_phase_angles", [0, 1, 2, 3, 4]),
        ("phase_steps_rad", "invalid_phase_angles", np.arange(5.0).view(ArraySubclass)),
        ("phase_steps_rad", "invalid_phase_angles_dtype", np.ones(5, dtype=complex)),
        ("phase_steps_rad", "invalid_phase_angles_dtype", np.ones(5, dtype=bool)),
        ("phase_steps_rad", "invalid_phase_angles_shape", np.ones((5, 1))),
        ("phase_steps_rad", "invalid_phase_angles_shape", np.ones(4)),
        ("phase_steps_rad", "nonfinite_phase_angles", np.array([0, 1, 2, 3, np.inf])),
        ("phase_steps_rad", "nonfinite_phase_angles", np.array([0, 1, 2, 3, np.nan])),
        ("phase_steps_rad", "rank_deficient_phases", np.zeros(5)),
        ("phase_steps_rad", "rank_deficient_phases", np.array([0, np.pi, 2 * np.pi, 0, np.pi])),
        ("otf", "invalid_illumination_otf", None),
    ]


@pytest.mark.parametrize("candidates", [[(10**100, 0)], [(0, 0)]])
@pytest.mark.parametrize(("field", "code", "value"), invalid_common_cases())
def test_common_validation_even_without_success(
    candidates: Any, field: str, code: str, value: Any
) -> None:
    case = acquisition()
    if candidates == [(0, 0)]:
        case.images[:] = 0
    if field == "images":
        assert_code(
            code,
            lambda: export("scan_carriers")(
                value,
                otf=case.otf(sr),
                phase_steps_rad=case.steps,
                candidate_carriers_bins_yx=candidates,
            ),
        )
    else:
        assert_code(code, lambda: scan(case, candidates, **{field: value}))


def invalid_otf_fields() -> list[tuple[str, Any, str]]:
    invalid = "invalid_illumination_otf"
    grid = "incompatible_illumination_otf_grid"
    return [
        ("values", np.ones((5, 7)), invalid),
        ("values", np.ones((5, 7), dtype=np.complex64), invalid),
        ("values", np.ones((5, 7), dtype=complex).view(ArraySubclass), invalid),
        ("values", [[1j]], invalid),
        ("values", np.ones((5, 8), dtype=complex), invalid),
        ("values", np.full((5, 7), np.nan + 0j), invalid),
        ("values", np.full((5, 7), 0.8 + 0j), invalid),
        ("values", np.full((5, 7), 1.2 + 0j), invalid),
        ("fy_per_um", np.arange(5, dtype=np.float32), invalid),
        ("fy_per_um", np.zeros((5, 1)), invalid),
        ("fy_per_um", np.array([0, 1, 2, 3, np.inf]), invalid),
        ("fx_per_um", np.arange(7.0).view(ArraySubclass), invalid),
        ("fx_per_um", np.arange(7.0), grid),
        ("fx_per_um", np.arange(6.0), invalid),
        ("pixel_size_um", (0.0, 0.35), invalid),
        ("pixel_size_um", (True, 0.35), invalid),
        ("pixel_size_um", (np.inf, 0.35), invalid),
        ("pixel_size_um", (0.2,), invalid),
        ("origin_yx", (-1, 0), invalid),
        ("origin_yx", (5, 0), invalid),
        ("origin_yx", (0.0, 0), invalid),
        ("origin_yx", (True, 0), invalid),
        ("source", "  ", invalid),
        ("source", 1, invalid),
    ]


@pytest.mark.parametrize(("field", "value", "code"), invalid_otf_fields())
def test_direct_otf_validation_with_no_overlap(field: str, value: Any, code: str) -> None:
    case = acquisition()
    assert_code(code, lambda: scan(case, [(10**100, 0)], otf=case.otf(sr, **{field: value})))


@pytest.mark.parametrize("mutation", ["nonhermitian", "wrong-grid", "reversed-grid", "zero-grid"])
def test_otf_transfer_and_grid_invariants(mutation: str) -> None:
    case = acquisition()
    otf = case.otf(sr)
    code = "incompatible_illumination_otf_grid"
    if mutation == "nonhermitian":
        otf.values[1, 2] += 0.02j
        code = "invalid_illumination_otf"
    elif mutation == "wrong-grid":
        otf.fy_per_um[:] *= 1.01
    elif mutation == "reversed-grid":
        otf.fx_per_um[:] = otf.fx_per_um[::-1]
    else:
        otf.fx_per_um[:] = 0
    assert_code(code, lambda: scan(case, [(10**100, 0)], otf=otf))


@pytest.mark.parametrize(
    "dtype",
    ["i1", "u1", "i2", "u2", "i4", "u4", "i8", "u8", "f2", "f4", "f8", ">f8", ">i4", np.longdouble],
)
def test_image_dtype_conversion_uses_stored_values(dtype: Any) -> None:
    case = image_dtype_acquisition(dtype)
    reference = stored_fits(case, [(1, 1)])[0]
    assert isinstance(reference, Fit)
    assert_fit(scan(case, [(1, 1)])[0], reference, case)


@pytest.mark.parametrize("dtype", [np.int64, np.uint64])
def test_wide_integer_image_rounding_defines_the_stored_problem(dtype: Any) -> None:
    base = two_pixel()
    maximum = int(np.iinfo(dtype).max)
    values = [maximum, maximum // 2, maximum // 3, maximum // 4, maximum // 5]
    if dtype is np.int64:
        values[1] = -values[1]
    images = np.array(values, dtype=dtype)[:, None, None]
    transfer = np.ones((1, 1), dtype=np.complex128)
    case = Acquisition(images, base.steps, transfer, transfer.copy(), transfer.copy())
    reference = stored_fits(case, [(0, 0)])[0]
    assert isinstance(reference, Fit)
    assert int(images[0, 0, 0]) != int(float(images[0, 0, 0]))
    assert_fit(scan(case, [(0, 0)])[0], reference, case)


@pytest.mark.parametrize("dtype", ["i1", "u2", "i4", "u8", "f2", "f4", "f8", ">f8", np.longdouble])
def test_step_dtype_conversion(dtype: Any) -> None:
    steps = np.array([0, 1, 2, 4, 5], dtype=dtype)
    case = acquisition(steps=steps.astype(np.float64))
    reference = stored_fits(case, [(1, 1)])[0]
    assert isinstance(reference, Fit)
    assert_fit(scan(case, [(1, 1)], phase_steps_rad=steps)[0], reference, case)


def test_integer_step_rounding_precedes_represented_trigonometry() -> None:
    steps = np.array([2**53 + value for value in (1, 3, 5, 7, 9)], dtype=np.int64)
    case = acquisition(steps=steps.astype(np.float64))
    expected = stored_fits(case, [(1, 1)])[0]
    assert isinstance(expected, Fit)
    assert_fit(scan(case, [(1, 1)], phase_steps_rad=steps)[0], expected, case)


@pytest.mark.parametrize(
    "steps",
    [
        np.array([-0.7, 1.1, 3.8]),
        np.arange(4, dtype=np.float64) * (np.pi / 2),
        np.array([-1.2, -0.1, 0.7, 1.8, 2.4, 3.9, 5.6]),
    ],
)
def test_three_quadrature_and_more_unequal_phase_counts(steps: Any) -> None:
    case = acquisition(steps=steps)
    expected = stored_fits(case, [(1, 1)])[0]
    assert isinstance(expected, Fit)
    assert_fit(scan(case, [(1, 1)])[0], expected, case)
    assert abs(expected.gain - case.modulation / 2 * np.exp(1j * case.theta)) < 2e-13


def test_strided_readonly_big_endian_images_steps_and_otf() -> None:
    case = acquisition(off_model=True)
    reference = stored_fits(case, [(1, 1), (0, 1)])

    def strided(array: Any, dtype: str) -> Any:
        storage = np.empty(tuple(2 * n for n in array.shape), dtype=dtype)
        view = storage[tuple(slice(None, None, 2) for _ in array.shape)]
        view[:] = array
        view.flags.writeable = False
        return view

    case.images = strided(case.images, ">f8")
    case.steps = strided(case.steps, ">f8")
    otf = case.otf(sr)
    calibration = case.otf(
        sr,
        values=strided(otf.values, ">c16"),
        fy_per_um=strided(otf.fy_per_um, ">f8"),
        fx_per_um=strided(otf.fx_per_um, ">f8"),
        pixel_size_um=np.array(case.spacing),
        origin_yx=np.array([0, 0]),
    )
    result = scan(case, [(1, 1), (0, 1)], otf=calibration)
    for record, expected in zip(result, reference, strict=True):
        assert isinstance(expected, Fit)
        assert_fit(record, expected, case)


@pytest.mark.parametrize("scale", [2.0**-900, 1.0, 2.0**900])
@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_safe_extreme_common_gain_preserves_fit_and_numpy_policy(scale: float, mode: Any) -> None:
    case = acquisition(off_model=True)
    reference = stored_fits(case, [(1, 1), (0, 1)])
    case.images *= scale
    with np.errstate(all=mode), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        before = np.geterr().copy()
        result = scan(case, [(1, 1), (0, 1), (10**100, 0)])
        assert np.geterr() == before
    assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
    for record, expected in zip(result[:2], reference, strict=True):
        assert isinstance(expected, Fit)
        assert_fit(record, expected, case)
    assert_failure(result[2], "no_illumination_overlap")


def test_tiny_transfer_is_not_an_information_threshold() -> None:
    case = two_pixel(transfer_edge=1e-290, dc_odd=True)
    result = scan(case, [(0, 0), (0, 2)])
    # Odd images make the DC transform exactly zero; the sole informative
    # nonzero-frequency pair has both factors ~1e-290. Raw squares underflow.
    # These overlap norms are outside B/8. Demand accepted nonzero finite output
    # and geometry/ownership, without inventing a weak-overlap digit guarantee.
    assert_success_record(result[0], case, 2)
    assert_failure(result[1], "no_illumination_overlap")


def test_negative_real_transfer_is_preserved_in_complex_fit() -> None:
    case = two_pixel(transfer_edge=-0.5)
    expected = stored_fits(case, [(0, -1)])[0]
    assert isinstance(expected, Fit)
    assert abs(expected.gain - (-0.4 - 0.2j)) < 2e-13
    assert_fit(scan(case, [(0, -1)])[0], expected, case)


def test_genuine_modulation_range_failure_aborts_whole_scan() -> None:
    case = two_pixel(transfer_edge=1e-310)
    # At k=-1 on [-1,0], ONLY q=0 is used: x=1e-310*D0(0),
    # y=Dplus(-1)~0.2+0.1j. m~4.47e309 is decisively outside float64.
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        before = np.geterr().copy()
        assert_code("unrepresentable_illumination", lambda: scan(case, [(0, 2), (0, -1), (0, 0)]))
        assert np.geterr() == before
    assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]


def test_decimal_range_observer_selfcheck_roots_and_forward_sign() -> None:
    with localcontext() as context:
        context.prec = 120
        pi = decimal_pi()
        assert Decimal("3.14159") < pi < Decimal("3.14160")
        sine, cosine = decimal_sin_cos(-pi / 2)
        assert abs(sine + 1) < Decimal("1e-95")
        assert abs(cosine) < Decimal("1e-95")
        for mode in (1, 3):
            sine_sum, cosine_sum = Decimal(0), Decimal(0)
            for coordinate in range(7):
                sine, cosine = decimal_sin_cos(-2 * pi * mode * coordinate / 7)
                assert abs(sine * sine + cosine * cosine - 1) < Decimal("1e-95")
                sine_sum += sine
                cosine_sum += cosine
            assert abs(sine_sum) < Decimal("1e-95")
            assert abs(cosine_sum) < Decimal("1e-95")


def test_range_witness_selfcheck_exact_dc_and_finite_final_modulation() -> None:
    case, witness = overflow_ratio_acquisition()
    assert all(value == 1 for value in witness.exact_dc)
    assert all(value == 0 for value in witness.exact_cosine)
    maximum = Decimal.from_float(float(np.finfo(np.float64).max))
    assert witness.norm_ratio_lower > maximum
    assert Decimal("1e301") < witness.modulation < Decimal("1e303") < maximum
    assert 0 < witness.modulation_lower <= witness.modulation <= witness.modulation_upper < maximum
    assert case.dc_coefficients[0, 3] == 1
    assert np.count_nonzero(case.dc_coefficients) == 1
    assert case.plus_coefficients[0, 4] != 0
    assert np.all(np.isfinite(case.images))
    assert case.images.shape == (4, 1, 7)


def test_overflowing_intermediate_norm_ratio_has_finite_successful_modulation() -> None:
    case, witness = overflow_ratio_acquisition()
    maximum = Decimal.from_float(float(np.finfo(np.float64).max))
    assert (
        witness.norm_ratio_lower > maximum > witness.modulation_upper > witness.modulation_lower > 0
    )
    otf = case.otf(sr)
    arrays = [case.images, case.steps, otf.values, otf.fy_per_um, otf.fx_per_um]
    before = [array.copy() for array in arrays]
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        policy = np.geterr().copy()
        result = scan(case, [(0, 1)], otf=otf)
        assert np.geterr() == policy
    assert type(result) is tuple and len(result) == 1
    assert result[0].carrier_bins_yx == (0, 1)
    # Weak overlap supplies no uniform gain digits. The independently established
    # positive class must still return a finite successful estimate, not a range
    # error from a needless intermediate ratio, zero-information code or fallback.
    assert_success_record(result[0], case, 6)
    assert not [warning for warning in caught if issubclass(warning.category, RuntimeWarning)]
    for array, snapshot in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, snapshot)


def test_inherited_separation_final_range_failure_is_whole_call() -> None:
    case = acquisition(steps=np.array([0.0, 0.1, 0.2]))
    maximum = np.finfo(np.float64).max
    case.images = np.broadcast_to(
        np.array([maximum / 4, -maximum / 4, maximum / 4])[:, None, None], (3, 5, 7)
    ).copy()
    assert_code("unrepresentable_phase_components", lambda: scan(case, [(10**100, 0)]))


def test_large_steps_corrected_rotation_and_joint_permutation() -> None:
    case = large_step_acquisition()
    reference = stored_fits(case, [(1, 1), (-1, -1)])
    result = scan(
        case,
        [(1, 1), (-1, -1)],
        otf=case.otf(
            sr,
            origin_yx=[np.int64(2), np.uint32(3)],
            pixel_size_um=[np.float64(case.spacing[0]), case.spacing[1]],
        ),
    )
    for record, expected in zip(result, reference, strict=True):
        assert isinstance(expected, Fit)
        assert_fit(record, expected, case)
    order = np.array([3, 0, 7, 4, 1, 6, 2, 5])
    case.images, case.steps = case.images[order], case.steps[order]
    reordered = scan(case, [(1, 1), (-1, -1)])
    for before, after in zip(result, reordered, strict=True):
        np.testing.assert_allclose(
            after.estimate.phases_rad, before.estimate.phases_rad[order], atol=2e-11, rtol=0
        )
        assert abs(after.estimate.modulation - before.estimate.modulation) < 2e-11


def test_frozen_bindings_independent_mutable_outputs_and_source_preservation() -> None:
    case = acquisition()
    otf = case.otf(sr)
    candidates = np.array([[1, 1], [1, 1], [0, 1]])
    inputs = [case.images, case.steps, otf.values, otf.fy_per_um, otf.fx_per_um, candidates]
    snapshots = [array.copy() for array in inputs]
    result = scan(case, candidates, otf=otf)
    for record in result:
        for name, value in (
            ("carrier_bins_yx", (0, 0)),
            ("estimate", None),
            ("failure_code", "no_illumination_overlap"),
        ):
            with pytest.raises((AttributeError, TypeError)):
                setattr(record, name, value)
        for name in (
            "modulation",
            "phase_offset_rad",
            "relative_residual",
            "phases_rad",
            "overlap_count",
            "source",
        ):
            with pytest.raises((AttributeError, TypeError)):
                setattr(record.estimate, name, None)
        for array in inputs:
            assert not np.shares_memory(record.estimate.phases_rad, array)
    for i, record in enumerate(result):
        for other in result[i + 1 :]:
            assert record.estimate is not other.estimate
            assert not np.shares_memory(record.estimate.phases_rad, other.estimate.phases_rad)
    untouched = result[1].estimate.phases_rad.copy()
    result[0].estimate.phases_rad[:] = 99
    np.testing.assert_array_equal(result[1].estimate.phases_rad, untouched)
    for array, before in zip(inputs, snapshots, strict=True):
        np.testing.assert_array_equal(array, before)
    failure = scan(case, [(10**100, 0)])[0]
    with pytest.raises((AttributeError, TypeError)):
        failure.failure_code = None


@pytest.mark.parametrize(
    "failure", [ValueError, FloatingPointError, OverflowError, MemoryError, RuntimeError]
)
def test_transform_failure_translation_and_unrelated_identity(
    monkeypatch: Any, failure: Any
) -> None:
    case = acquisition(off_model=True)
    error = failure("controlled public transform execution failure")

    def fail(original: Any, *args: Any, **kwargs: Any) -> Any:
        raise error

    hits = patch_transforms(monkeypatch, fail)
    if failure in (ValueError, FloatingPointError, OverflowError):
        assert_conditional_scan_fault(
            case, [(10**100, 0), (1, 1)], hits, code="illumination_solver_failure"
        )
    else:
        assert_conditional_scan_fault(case, [(10**100, 0), (1, 1)], hits, error=error)


def test_nonfinite_public_transform_is_solver_failure(monkeypatch: Any) -> None:
    case = acquisition(off_model=True)

    def nonfinite(original: Any, array: Any, *args: Any, **kwargs: Any) -> Any:
        return np.full(np.shape(array), np.nan + 1j * np.inf, dtype=np.complex128)

    hits = patch_transforms(monkeypatch, nonfinite)
    assert_conditional_scan_fault(case, [(1, 1)], hits, code="illumination_solver_failure")


@pytest.mark.parametrize("failure", [np.linalg.LinAlgError, MemoryError, RuntimeError])
def test_inherited_phase_execution_failure_even_without_overlap(
    monkeypatch: Any, failure: Any
) -> None:
    case = acquisition(off_model=True)
    error = failure("controlled public separation execution failure")

    def fail(original: Any, *args: Any, **kwargs: Any) -> Any:
        raise error

    hits = patch_public_calls(monkeypatch, [(np.linalg, name) for name in ("svd", "lstsq")], fail)
    code = "phase_solver_failure" if failure is np.linalg.LinAlgError else None
    propagated = None if failure is np.linalg.LinAlgError else error
    assert_conditional_scan_fault(case, [(10**100, 0)], hits, code=code, error=propagated)
    if not hits:
        # A no-overlap return alone is not our alternative-binding success oracle.
        # Exercise an informative candidate too, conditional on that call's hits.
        assert_conditional_scan_fault(case, [(1, 1)], hits, code=code, error=propagated)


def test_single_candidate_existing_public_api_compatibility_is_supplemental() -> None:
    case = acquisition(off_model=True)
    for carrier in [(1, 1), (-1, -1), (0, 0)]:
        independent = stored_fits(case, [carrier])[0]
        assert isinstance(independent, Fit)
        record = scan(case, [carrier])[0]
        assert_fit(record, independent, case)
        existing = export("estimate_illumination")(
            case.images,
            otf=case.otf(sr),
            phase_steps_rad=case.steps,
            carrier_bins_yx=carrier,
        )
        for name in ("modulation", "phase_offset_rad", "relative_residual"):
            assert abs(getattr(existing, name) - getattr(record.estimate, name)) < 2e-11
        np.testing.assert_allclose(
            existing.phases_rad, record.estimate.phases_rad, atol=2e-11, rtol=0
        )
    for name in ("separate_phases", "prepare_otf", "reconstruct", "estimate_illumination"):
        assert callable(getattr(sr, name))


def test_fixture_analytic_true_gain_and_informative_accuracy_regime() -> None:
    """Self-check the independent observer, not a product-derived expectation."""
    case = acquisition()
    analytic = fit(case.dc_coefficients, case.plus_coefficients, case.transfer, (1, 1))
    stored = stored_fits(case, [(1, 1)])[0]
    assert isinstance(analytic, Fit) and isinstance(stored, Fit)
    truth = case.modulation / 2 * np.exp(1j * case.theta)
    assert abs(analytic.gain - truth) < 1e-15
    assert analytic.residual < 1e-15
    assert abs(stored.gain - truth) < 2e-13
    assert stored.residual < 2e-13
    h = np.column_stack([np.ones(len(case.steps)), np.cos(case.steps), np.sin(case.steps)])
    assert np.linalg.cond(h) <= 10
    # stored_bands normalized images by B, so the norm threshold is 1/8.
    assert stored.norm_x >= 1 / 8 and stored.norm_y >= 1 / 8
    assert stored.correlation >= 1 / 4
    assert 1e-4 <= abs(stored.gain) <= 10
    assert delta(case) == 8192 * 5 * 35 * 2.0**-52


def test_informative_observer_selfcheck_audits_accuracy_fixture_families() -> None:
    """Audit prerequisites without needing the not-yet-present scan API."""
    examples: list[tuple[Acquisition, list[tuple[int, int]]]] = []
    for shape in ((5, 7), (6, 8), (5, 8), (6, 7)):
        examples.append((acquisition(shape), [(1, 1)]))
        examples.append((acquisition(shape, off_model=True), [(1, 1), (0, 1), (-1, -1), (0, 0)]))
    for dtype in (
        "i1",
        "u1",
        "i2",
        "u2",
        "i4",
        "u4",
        "i8",
        "u8",
        "f2",
        "f4",
        "f8",
        ">f8",
        ">i4",
        np.longdouble,
    ):
        examples.append((image_dtype_acquisition(dtype), [(1, 1)]))
    for steps in (
        np.array([0, 1, 2, 4, 5], dtype=np.float64),
        np.array([2**53 + value for value in (1, 3, 5, 7, 9)], dtype=np.int64).astype(np.float64),
        np.array([-0.7, 1.1, 3.8]),
        np.arange(4, dtype=np.float64) * (np.pi / 2),
        np.array([-1.2, -0.1, 0.7, 1.8, 2.4, 3.9, 5.6]),
    ):
        examples.append((acquisition(steps=steps), [(1, 1)]))
    examples.append((large_step_acquisition(), [(1, 1), (-1, -1)]))
    for dtype in (np.int64, np.uint64):
        maximum = int(np.iinfo(dtype).max)
        values = [maximum, maximum // 2, maximum // 3, maximum // 4, maximum // 5]
        if dtype is np.int64:
            values[1] = -values[1]
        transfer = np.ones((1, 1), dtype=np.complex128)
        base = two_pixel()
        case = Acquisition(
            np.array(values, dtype=dtype)[:, None, None],
            base.steps,
            transfer,
            transfer.copy(),
            transfer.copy(),
        )
        examples.append((case, [(0, 0)]))
    examples.extend(
        [
            (two_pixel(plus=0.9 + 0.4j), [(0, -1)]),
            (two_pixel(transfer_edge=-0.5), [(0, -1)]),
            (two_pixel(dc_odd=True, plus=-0.2 + 0j), [(0, 0)]),
        ]
    )
    subnormal = two_pixel(dc_odd=True)
    subnormal.images *= 2.0**-1070
    examples.append((subnormal, [(0, 0)]))
    for case, carriers in examples:
        for reference in stored_fits(case, carriers):
            assert isinstance(reference, Fit)
            assert informative(case, reference)
    # These are observer checks rather than impossible product states or
    # additional precision requirements on product outputs.
    base = acquisition()
    reference = stored_fits(base, [(1, 1)])[0]
    assert isinstance(reference, Fit)
    for invalid in (
        Fit(reference.gain, reference.residual, reference.overlap, 0.01, reference.norm_y, 1),
        Fit(reference.gain, reference.residual, reference.overlap, reference.norm_x, 0.01, 1),
        Fit(
            reference.gain,
            reference.residual,
            reference.overlap,
            reference.norm_x,
            reference.norm_y,
            0.1,
        ),
        Fit(1e-6 + 0j, 0, 1, 1, 1, 1),
        Fit(11 + 0j, 0, 1, 1, 1, 1),
    ):
        assert not informative(base, invalid)
    clustered = acquisition(steps=np.arange(5, dtype=np.float64) * 1e-4)
    assert not informative(clustered, reference)


def test_exact_zero_acquisition_yields_only_information_and_overlap_failures() -> None:
    case = acquisition()
    case.images[:] = 0
    result = scan(case, [(1, 1), (0, 0), (-1, -1), (10**100, 0)])
    for record in result[:3]:
        assert_failure(record, "unidentifiable_illumination")
    assert_failure(result[3], "no_illumination_overlap")


def test_subnormal_stored_input_fit_is_scaled_before_precision_is_lost() -> None:
    case = two_pixel(dc_odd=True)
    case.images *= 2.0**-1070
    reference = stored_fits(case, [(0, 0)])[0]
    assert isinstance(reference, Fit)
    assert reference.norm_x >= 1 / 8 and reference.norm_y >= 1 / 8
    assert reference.correlation >= 1 / 4
    # Truth is the quantized stored observations, not the unrounded 0.2+0.1j.
    assert abs(reference.gain - (0.2 + 0.1j)) > 0.001
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        result = scan(case, [(0, 0)])
    assert not [warning for warning in caught if issubclass(warning.category, RuntimeWarning)]
    assert_fit(result[0], reference, case)


def test_branch_cut_phase_equivalence_and_signed_data() -> None:
    case = two_pixel(dc_odd=True, plus=-0.2 + 0j)
    reference = stored_fits(case, [(0, 0)])[0]
    assert isinstance(reference, Fit)
    result = scan(case, [(0, 0)])
    assert_fit(result[0], reference, case)
    assert abs(abs(result[0].estimate.phase_offset_rad) - np.pi) < 2e-11
    assert np.min(case.images) < 0


def test_identifiable_clustered_steps_have_no_extra_condition_cutoff() -> None:
    steps = np.arange(5, dtype=np.float64) * 1e-4
    case = two_pixel(dc_odd=True)
    scalar = 2 + 0.6 * np.cos(steps + 0.4)
    case.steps = steps
    case.images = scalar[:, None, None] * np.array([[[1.0, -1.0]]])
    h = np.column_stack([np.ones(5), np.cos(steps), np.sin(steps)])
    singular = np.linalg.svd(h, compute_uv=False)
    assert singular[-1] > np.finfo(float).eps * 5 * singular[0]
    assert singular[0] / singular[-1] > 10
    record = scan(case, [(0, 0)])[0]
    assert record.failure_code is None
    assert np.isfinite(record.estimate.modulation)
    assert np.all(np.isfinite(record.estimate.phases_rad))
    # No uniform coefficient-digit promise applies to this ill-conditioned case.


@pytest.mark.parametrize("field", ["images", "phase_steps_rad"])
def test_longdouble_source_conversion_matches_available_range(field: str) -> None:
    case = acquisition()
    extra_range = np.finfo(np.longdouble).max > np.longdouble(np.finfo(np.float64).max)
    original = case.images if field == "images" else case.steps
    if extra_range:
        large = np.longdouble(np.finfo(np.float64).max) * 2
        assert np.isfinite(large)
        source = np.full(original.shape, large, dtype=np.longdouble)
        expected = None
    else:
        # No finite extra-range value exists on this platform. Exercise the
        # permitted longdouble representation and its actual converted problem.
        source = original.astype(np.longdouble)
        assert source.dtype == np.dtype(np.longdouble)
        assert np.all(np.isfinite(source))
        np.testing.assert_array_equal(source.astype(np.float64), original)
        expected = stored_fits(case, [(1, 1)])[0]
        assert isinstance(expected, Fit)
    before = source.copy()
    if field == "images":
        case.images = source
        changes = {}
        code = "nonfinite_phase_images"
    else:
        changes = {"phase_steps_rad": source}
        code = "nonfinite_phase_angles"
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        error_mode = np.geterr().copy()
        if extra_range:
            assert_code(code, lambda: scan(case, [(10**100, 0)], **changes))
        else:
            assert isinstance(expected, Fit)
            assert_fit(scan(case, [(1, 1)], **changes)[0], expected, case)
        assert np.geterr() == error_mode
    assert not [warning for warning in caught if issubclass(warning.category, RuntimeWarning)]
    np.testing.assert_array_equal(source, before)


def test_direct_otf_tolerance_positive_and_full_complex_values() -> None:
    case = acquisition(off_model=True)
    ny, nx = case.transfer.shape
    tau = 128 * ny * nx * 2.0**-52
    case.transfer[ny // 2, nx // 2] = 1 + tau / 4
    reference = stored_fits(case, [(1, 1), (-1, -1)])
    assert np.max(np.abs(case.transfer.imag)) > 0.2
    result = scan(case, [(1, 1), (-1, -1)])
    for record, expected in zip(result, reference, strict=True):
        assert isinstance(expected, Fit)
        assert_fit(record, expected, case)


def test_other_simreconerror_propagates_unchanged_from_numeric_execution(monkeypatch: Any) -> None:
    case = acquisition(off_model=True)
    # Obtain a real public error without guessing its construction signature.
    with pytest.raises(export("SimreconError")) as original:
        export("separate_phases")(None, phases_rad=case.steps)

    def fail(original_function: Any, *args: Any, **kwargs: Any) -> Any:
        raise original.value

    hits = patch_transforms(monkeypatch, fail)
    assert_conditional_scan_fault(case, [(10**100, 0), (1, 1)], hits, error=original.value)


def test_inherited_nonfinite_numerical_factors_are_whole_call_failure(monkeypatch: Any) -> None:
    case = acquisition(off_model=True)

    def nonfinite(function: Any, *args: Any, **kwargs: Any) -> Any:
        result = function(*args, **kwargs)
        if isinstance(result, tuple):
            return tuple(
                np.full_like(value, np.nan) if isinstance(value, np.ndarray) else value
                for value in result
            )
        return np.full_like(result, np.nan)

    hits = patch_public_calls(
        monkeypatch, [(np.linalg, name) for name in ("svd", "lstsq")], nonfinite
    )
    assert_conditional_scan_fault(case, [(10**100, 0)], hits, code="phase_solver_failure")
    if not hits:
        assert_conditional_scan_fault(case, [(1, 1)], hits, code="phase_solver_failure")


def test_operation_time_failure_preserves_all_caller_storage(monkeypatch: Any) -> None:
    case = acquisition(off_model=True)
    otf = case.otf(sr)
    candidates = np.array([[1, 1], [-1, -1]])
    arrays = [case.images, case.steps, otf.values, otf.fy_per_um, otf.fx_per_um, candidates]
    snapshots = [array.copy() for array in arrays]
    error = MemoryError("controlled operation-time allocation failure")

    def fail(original: Any, *args: Any, **kwargs: Any) -> Any:
        raise error

    hits = patch_transforms(monkeypatch, fail)
    assert_conditional_scan_fault(case, candidates, hits, error=error, otf=otf)
    for array, snapshot in zip(arrays, snapshots, strict=True):
        np.testing.assert_array_equal(array, snapshot)


@pytest.mark.parametrize("carrier", [(10**100, 0), (0, 0)])
def test_single_candidate_local_failure_matches_existing_public_api(carrier: Any) -> None:
    case = acquisition()
    case.images[:] = 0
    code = "no_illumination_overlap" if carrier[0] else "unidentifiable_illumination"
    assert_code(
        code,
        lambda: export("estimate_illumination")(
            case.images,
            otf=case.otf(sr),
            phase_steps_rad=case.steps,
            carrier_bins_yx=carrier,
        ),
    )
    assert_failure(scan(case, [carrier])[0], code)
