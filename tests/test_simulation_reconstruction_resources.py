"""M01–M06: small public composition and independent resource-witness checks."""

from fractions import Fraction as F
from itertools import product
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from simulation_reconstruction_resource import (
    SIZES,
    ZERO,
    add,
    budgets,
    compare_outputs,
    conj,
    inverse,
    make_case,
    mul,
    reference_tile,
    represented_matrix,
    run_witness,
    signal_cell,
    sparse_bands,
    sparse_estimator,
    transfer,
)


def test_small_correction_to_reconstruction_witness() -> None:
    evidence = run_witness()
    assert evidence["shape"] == [4, 16, 16]
    assert evidence["inputs_preserved"]


def test_rational_reference_and_full_size_bound_without_full_allocation() -> None:
    h = represented_matrix()
    inv = inverse(h)
    for i, j in product(range(5), repeat=2):
        assert sum(h[i][k] * inv[k][j] for k in range(5)) == int(i == j)
    bands, condition = sparse_bands()
    assert condition < 10
    # Raw cells vary in z and contain nonzero first and second fitted harmonics.
    assert not np.array_equal(signal_cell()[:, :, 0], signal_cell()[:, :, 1])
    for band in bands:
        assert any(v[1] != ZERO for v in band.values())
        assert any(v[2] != ZERO for v in band.values())
        # DC signal includes the x even-Nyquist endpoint, not a duplicate +Nyquist.
        assert band[(0, 0, -2)][0] != ZERO
        assert (0, 0, 2) not in band
    # Independent analytic DC and cosine Fourier samples from the dyadic cell.
    # Its phase-0 z-cosine amplitude is (r+1)*4/32, hence half in k_z=+/-1.
    for r in range(3):
        for k, expected in (((0, 0, 0), F(r + 1, 2)), ((1, 0, 0), F(r + 1, 16))):
            dc, c1, c2 = bands[r][k]
            negative = bands[r][(-k[0], -k[1], -k[2])]
            coefficients = [dc]
            for cm, cn in zip((c1, c2), negative[1:], strict=True):
                reflected = conj(cn)
                coefficients.append(add(cm, reflected))
                difference = add(cm, (-reflected[0], -reflected[1]))
                coefficients.append(mul((F(0), F(1)), difference))
            restored = ZERO
            for value, coefficient in zip(h[0], coefficients, strict=True):
                restored = add(restored, mul((value, F(0)), coefficient))
            assert restored == (expected, F(0))
    small, facts = sparse_estimator(SIZES["small"])
    full, full_facts = sparse_estimator(SIZES["full"])
    assert facts == full_facts
    normalized_small = {
        tuple(F(v, n) for v, n in zip(q, SIZES["small"], strict=True)): t for q, t in small.items()
    }
    normalized_full = {
        tuple(F(v, n) for v, n in zip(q, SIZES["full"], strict=True)): t for q, t in full.items()
    }
    assert normalized_small == normalized_full
    limits = budgets(SIZES["full"], full, full_facts)
    assert limits["old_regime_left"] > limits["old_regime_right"]
    tile = reference_tile(full, SIZES["full"])
    assert limits["volume"] < float(np.max(np.abs(tile.imag))) / 1000
    # Asymmetric transfers distinguish modular reflection from centered reversal.
    assert transfer(1, 2, (-2, -4, -4), SIZES["small"]) != transfer(1, 2, (1, 3, 3), SIZES["small"])


def test_output_observer_legal_perturbation_and_wrong_answers() -> None:
    shape = SIZES["small"]
    case, _ = make_case(shape)
    spectrum, facts = sparse_estimator(shape)
    tile = reference_tile(spectrum, shape)
    limits = budgets(shape, spectrum, facts)
    expected_s = np.zeros((4, 16, 16), dtype=np.complex128)
    for q, (a, b) in spectrum.items():
        expected_s[q[0] + 2, q[1] + 8, q[2] + 8] = complex(float(a), float(b))

    def result(s: Any, v: Any) -> Any:
        return SimpleNamespace(
            spectrum=s.copy(),
            volume=v.copy(),
            fz_per_um=np.arange(-2, 2, dtype=float) / 4 / 0.5,
            fy_per_um=np.arange(-8, 8, dtype=float) / 8 / 0.25,
            fx_per_um=np.arange(-8, 8, dtype=float) / 8 / 0.125,
            voxel_size_um=(0.5, 0.125, 0.0625),
        )

    compare_outputs(result(expected_s, tile), case, spectrum, tile, limits)
    compare_outputs(
        result(expected_s + limits["spectrum"] / 4, tile + limits["volume"] / 4),
        case,
        spectrum,
        tile,
        limits,
    )
    # The public frequency budget permits rounding away from the exact grid.
    # For fx[0], exact=-8 cycles/um and allowance=2^-46 + 2^-1074.
    coordinate_budget = F(1, 2**46) + F(1, 2**1074)
    permitted = result(expected_s, tile)
    permitted.fx_per_um[0] = np.nextafter(-8.0, -np.inf)
    assert 0 < abs(F(float(permitted.fx_per_um[0])) + 8) <= coordinate_budget
    compare_outputs(permitted, case, spectrum, tile, limits)
    outside = result(expected_s, tile)
    outside.fx_per_um[0] = -8.0 - 2.0**-45
    assert abs(F(float(outside.fx_per_um[0])) + 8) > coordinate_budget
    with pytest.raises(AssertionError):
        compare_outputs(outside, case, spectrum, tile, limits)
    # An additive q allowance must not admit a nonzero centered DC coordinate.
    for variant in ("nonzero_center", "nonfinite", "unordered"):
        invalid = result(expected_s, tile)
        if variant == "nonzero_center":
            invalid.fx_per_um[8] = np.nextafter(0.0, 1.0)
        elif variant == "nonfinite":
            invalid.fy_per_um[0] = np.inf
        else:
            invalid.fz_per_um[0] = invalid.fz_per_um[1]
        with pytest.raises(AssertionError):
            compare_outputs(invalid, case, spectrum, tile, limits)
    # Probe only our observer, never replace reconstruct_volume.
    for s, v in (
        (-expected_s, -tile),
        (2 * expected_s, 2 * tile),
        (expected_s.conj(), tile.conj()),
        (expected_s, tile.real.astype(complex)),
        (np.roll(expected_s, 1, axis=2), tile),
        (expected_s, tile / 1024),
    ):
        with pytest.raises(AssertionError):
            compare_outputs(result(s, v), case, spectrum, tile, limits)
    bad = result(expected_s, tile)
    bad.volume[3, 15, 15] = complex(0, np.nan)
    with pytest.raises(AssertionError):
        compare_outputs(bad, case, spectrum, tile, limits)
