"""Complementary public proofs for exact Fourier-block phase execution."""

from typing import Any

import numpy as np
import pytest
import scipy.linalg
from numpy.testing import assert_allclose, assert_array_equal

from fourier_block_phase_estimation_fixture import (
    EPS,
    PHASES,
    Case,
    canonical,
    coupled_case,
    dft,
    independent_fit,
    model,
    partition,
    profile,
    realify,
)
from simrecon import SimreconError, select_volume_phase_carrier


def assert_profile(row: Any, case: Case) -> Any:
    """Check full observations, lifted nuisance and global information independently."""
    point = profile(case, row.phases_rad)
    msize, nphase = case.images[0].size, len(case.initial)
    assert_array_equal(
        row.observable_fourier_mask,
        np.fft.fftshift(point.mask.reshape(case.images.shape[1:])),
    )
    assert row.observable_dimension == int(np.count_nonzero(point.mask))
    assert row.unobservable_dimension == msize - row.observable_dimension
    assert row.nuisance_rank == point.rank
    # For these bounded matrices M<=32, ||B||<12 and cond(B)<10 in the
    # full-rank coupled cases. 2e-11 permits >1000 eps per direct-sum term,
    # while resolving order signs, sqrt(2) pair factors and discarded rows.
    assert_allclose(row.specimen_normalized, point.specimen, atol=2e-11, rtol=2e-11)
    assert_allclose(row.nuisance_singular_values, point.singular, atol=2e-11, rtol=2e-11)
    assert_allclose(row.phase_singular_values, point.phase_singular, atol=2e-11, rtol=2e-10)
    assert_allclose(
        row.normalized_residual_rms,
        np.linalg.norm(point.residual) / np.sqrt(nphase * msize),
        atol=2e-11,
        rtol=2e-10,
    )
    assert_allclose(
        row.relative_residual,
        np.linalg.norm(point.residual) / np.linalg.norm(point.data),
        atol=2e-11,
        rtol=2e-10,
    )
    assert_allclose(
        row.normalized_imaginary_rms,
        np.linalg.norm(point.prediction.imag) / np.sqrt(nphase * msize),
        atol=2e-11,
        rtol=2e-10,
    )
    assert_allclose(
        row.gradient_inf_norm,
        np.linalg.norm(point.jacobian.T @ point.residual, ord=np.inf),
        atol=2e-11,
        rtol=2e-10,
    )
    if point.phase_singular[0] > 1e-8:
        cutoff = EPS * 2 * nphase * msize * point.phase_singular[0]
        # Rank is asserted only with a broad margin around the operational cutoff.
        assert np.all((point.phase_singular < cutoff / 8) | (point.phase_singular > 8 * cutoff))
        assert row.phase_rank == int(np.count_nonzero(point.phase_singular > cutoff))
    assert row.image_scale == point.image_scale
    assert row.transfer_scale == point.transfer_scale
    assert row.global_ambiguity == "unassessed"
    return point


@pytest.mark.parametrize("dark", [False, True])
def test_small_block_factors_equal_direct_spatial_model_and_public_fit(dark: bool) -> None:
    case = coupled_case(dark)
    point = profile(case, canonical(case.initial))
    shape = case.images.shape[1:]
    transform = dft(shape)
    q = transform.conj().T @ point.basis
    assert_allclose(q.imag, 0, atol=8e-16)
    assert_allclose(q.real.T @ q.real, np.eye(q.shape[1]), atol=3e-15)
    g, _, _ = model(case.values / point.transfer_scale, case.carrier, canonical(case.initial))
    a = realify(g @ transform)
    assert_allclose(a @ q.real, point.design, atol=4e-15)
    # Separate full spatial SVD supplies an equivalence check without sharing
    # the block SVD factors or using any estimator output as an expectation.
    spatial, _, _, _ = np.linalg.lstsq(a, point.data, rcond=EPS * len(point.data))
    assert_allclose(spatial.reshape(shape), point.specimen, atol=3e-14)
    assert_allclose(
        np.sort(np.linalg.svd(a @ q.real, compute_uv=False))[::-1],
        point.singular,
        atol=8e-15,
    )
    assert len(point.block_rows) > 3
    assert point.singular[0] / point.singular[-1] < 10
    assert point.singular[-1] > 1 / 16
    if dark:
        assert any(len(s) == 0 for s in point.block_singular)
        dark_rows = point.block_rows[[len(s) for s in point.block_singular].index(0)]
        assert np.linalg.norm(point.data[dark_rows]) > 0.01
        assert_array_equal(point.residual[dark_rows], point.data[dark_rows])
        assert_array_equal(point.jacobian[dark_rows], 0)
        assert np.count_nonzero(point.mask) < case.images[0].size
    result = case.estimate()
    assert result.termination == "evaluation_limit"
    assert_allclose(result.phases_rad, canonical(case.initial), atol=5e-16, rtol=0)
    assert_profile(result, case)


@pytest.mark.parametrize(
    "shape,carrier",
    [
        ((3, 2, 4), (1, -2)),
        ((2, 3, 4), (10**80 + 1, -(10**90) + 2)),
        ((1, 1, 6), (0, -2)),
        ((3, 4, 1), (-2, 0)),
        ((2, 2, 4), (0, 0)),
    ],
)
def test_sparse_geometry_pairs_nyquist_singletons_and_exact_carrier_aliases(
    shape: tuple[int, ...], carrier: tuple[int, int]
) -> None:
    msize = int(np.prod(shape))
    values = np.zeros((3, *shape), dtype=np.complex128)
    values.reshape(3, -1)[0, 0] = 1
    values.reshape(3, -1)[1, -1] = 0.31 - 0.17j
    values.reshape(3, -1)[2, msize // 2] = -0.24 + 0.09j
    images = (0.4 + np.sin(0.37 * np.arange(6 * msize))).reshape((6, *shape))
    case = Case(images, values, carrier, PHASES.copy())
    point = profile(case, canonical(case.initial))
    basis = point.basis
    assert basis.shape[1] == int(np.count_nonzero(point.mask))
    assert_allclose((basis.conj().T @ basis).real, np.eye(basis.shape[1]), atol=3e-16)
    blocks = partition(shape, carrier)
    assert sorted(k for block in blocks for k in block) == list(range(msize))
    # An independent dense Fourier design has exactly zero cross-block coupling.
    g, _, _ = model(values, carrier, canonical(case.initial))
    for block in blocks:
        outside = sorted(set(range(msize)) - set(block))
        rows = [p * msize + k for p in range(6) for k in block]
        assert_array_equal(g[np.ix_(rows, outside)], 0)
    row = case.estimate()
    assert row.carrier_bins_yx == carrier
    assert_profile(row, case)
    alias = Case(images, values, (carrier[0] % shape[1], carrier[1] % shape[2]), PHASES.copy())
    other = alias.estimate()
    assert_allclose(row.specimen_normalized, other.specimen_normalized, atol=2e-12, rtol=0)
    assert_allclose(row.nuisance_singular_values, other.nuisance_singular_values, atol=2e-12)


def test_global_cutoff_discards_entire_weak_pair_but_retains_structural_support() -> None:
    shape = (2, 2, 4)
    values = np.zeros((3, *shape), dtype=np.complex128)
    length = 2 * len(PHASES) * int(np.prod(shape))
    weak = 0.25 * EPS * length
    values[0, 0, 0, 0] = 1
    values[0, 1, 1, 2] = 0.27
    values[0, 0, 0, 1] = weak
    values[0, 0, 0, 3] = weak
    x = np.arange(4)
    # Nonzero data on the discarded pair and on structurally unsupported modes.
    images = np.tile((1 + 0.4 * np.cos(2 * np.pi * x / 4))[None, None, :], (6, 2, 2, 1))
    images[:, 1, 0] += 0.23 * np.array([1, -1, 1, -1])
    case = Case(images, values, (0, 0), PHASES.copy())
    point = profile(case, canonical(case.initial))
    expected = np.sqrt(6) * np.array([1, 0.27, weak, weak])
    assert_allclose(point.singular, expected, atol=0, rtol=5e-16)
    assert point.rank == 2 and sum(point.local_ranks) == 4
    assert np.linalg.norm(point.residual) > 0.3
    row = case.estimate()
    assert row.termination == "nuisance_rank_deficient"
    assert row.observable_dimension == 4 and row.nuisance_rank == 2
    assert_profile(row, case)
    # The weak block lies outside the well-conditioned accuracy envelope.
    # Its structural dimension and the strict computed global cutoff still bind;
    # do not impose an invented relative digit guarantee on tiny singular values.
    assert_allclose(row.nuisance_singular_values[:2], expected[:2], atol=2e-14)
    assert row.nuisance_singular_values.shape == (4,)
    cutoff = EPS * length * row.nuisance_singular_values[0]
    assert np.count_nonzero(row.nuisance_singular_values > cutoff) == 2
    assert_allclose(row.phases_rad, canonical(case.initial), atol=5e-16, rtol=0)
    assert np.linalg.norm(row.specimen_normalized) < 5


def test_full_off_model_derivative_and_global_coupled_step() -> None:
    case = coupled_case(dark=True)
    initial = canonical(case.initial)
    point = profile(case, initial)
    assert np.linalg.norm(point.jacobian + point.information) > 1e-3
    h = 2e-5
    columns = []
    for direction in np.eye(len(initial)):
        plus = profile(case, initial + h * direction).residual
        minus = profile(case, initial - h * direction).residual
        columns.append((plus - minus) / (2 * h))
    # O(h^2)+O(eps/h), with bounded trigonometric derivatives and cond<10.
    assert_allclose(point.jacobian, np.column_stack(columns), atol=2e-8, rtol=2e-7)
    gram = point.information.T @ point.information
    assert np.max(np.abs(gram - np.diag(np.diag(gram)))) > 1e-3
    local_information_singular = [
        np.linalg.svd(point.information[rows], compute_uv=False) for rows in point.block_rows
    ]
    assert np.linalg.norm(sum(local_information_singular) - point.phase_singular) > 0.01
    full = independent_fit(case, 2)
    wrong = independent_fit(case, 2, projected_only=True)
    # This measures the fixture's discrimination before comparing product output.
    assert np.max(np.abs(full.x - wrong.x)) > 1e-5
    row = case.estimate(2)
    assert row.termination == "evaluation_limit"
    assert_allclose(row.phases_rad, canonical(full.x), atol=3e-9, rtol=0)
    assert_profile(row, case)


def test_complete_selection_keeps_independent_multiblock_starts_and_alias_rows() -> None:
    case = coupled_case(dark=True)
    candidates = [(0, 0), case.carrier, (0, 6), case.carrier]
    kwargs = case.kwargs(2)
    del kwargs["carrier_bins_yx"]
    result = select_volume_phase_carrier(
        case.images,
        **kwargs,
        candidate_carriers_yx=candidates,
        max_relative_residual=1.0,
        min_phase_rank=0,
    )
    assert len(result.candidates) == len(candidates)
    assert result.eligible_indices == ()
    assert result.failure_code == "no_acceptable_volume_phase_carrier"
    for row, carrier in zip(result.candidates, candidates, strict=True):
        independent = Case(case.images, case.values, carrier, case.initial.copy())
        expected = independent_fit(independent, 2)
        assert row.carrier_bins_yx == carrier
        assert_allclose(row.phases_rad, canonical(expected.x), atol=3e-9, rtol=0)
        assert_profile(row, independent)
        assert row.termination == "evaluation_limit"
        assert row.nfev >= 2 and row.njev >= 1
    assert np.max(np.abs(result.candidates[0].phase_deviations_rad)) > 1e-3
    assert result.candidates[1] is not result.candidates[3]
    assert not np.shares_memory(
        result.candidates[1].specimen_normalized, result.candidates[3].specimen_normalized
    )


def test_observed_real_svd_calls_do_not_factor_a_global_dense_nuisance_design(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = coupled_case()
    msize = case.images[0].size
    length = 2 * len(case.initial) * msize
    cmax = max(map(len, partition(case.images.shape[1:], case.carrier)))
    assert cmax < msize and len(case.initial) < msize
    observed: list[tuple[int, ...]] = []

    def observer(original: Any) -> Any:
        def forwarding(*args: Any, **kwargs: Any) -> Any:
            matrix = args[0] if args else kwargs.get("a")
            # Inspect genuine already-materialized operands only. Do not
            # coerce a valid LinearOperator/lazy/lower-memory alternative.
            if isinstance(matrix, np.ndarray):
                observed.append(matrix.shape)
            return original(*args, **kwargs)

        return forwarding

    monkeypatch.setattr(np.linalg, "svd", observer(np.linalg.svd))
    monkeypatch.setattr(scipy.linalg, "svd", observer(scipy.linalg.svd))
    row = case.estimate()
    assert row.observable_dimension == msize
    # The contract forbids these materialized global nuisance factors. No
    # particular calls, basis ordering, block sizes or backend are required.
    # This is partial evidence: non-SVD allocations and bound aliases need D.
    for forbidden in ((length, msize), (msize, length), (msize, msize)):
        assert forbidden not in observed, (
            f"forbidden global dense nuisance SVD operand {forbidden}; "
            f"observed genuine operands {observed}, cmax={cmax}"
        )


@pytest.mark.parametrize("boundary", ["ifftn", "ifft", "irfftn"])
@pytest.mark.parametrize("failure", [FloatingPointError, OverflowError, RuntimeError, MemoryError])
def test_inverse_transform_failures_if_used_keep_the_inherited_boundary(
    monkeypatch: pytest.MonkeyPatch, boundary: str, failure: type[Exception]
) -> None:
    case = coupled_case()
    calls = []
    marker = failure("public inverse transform failure")

    def failing(*args: Any, **kwargs: Any) -> Any:
        calls.append(True)
        raise marker

    monkeypatch.setattr(np.fft, boundary, failing)
    try:
        row = case.estimate()
    except SimreconError as error:
        assert calls and failure in (FloatingPointError, OverflowError)
        assert error.code == "volume_phase_estimation_transform_failure"
    except (RuntimeError, MemoryError) as error:
        assert calls and error is marker
        assert failure in (RuntimeError, MemoryError)
    else:
        # A direct real lift or another valid transform needs no inverse call.
        # Do not require a backend merely to make injected failure observable.
        assert not calls
        assert_profile(row, case)
