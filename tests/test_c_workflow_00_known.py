"""WF097: independent known controls precede any nuisance-search observation."""

from __future__ import annotations

import numpy as np
import pytest

from c_workflow_oracle import (
    OPTICS,
    Case,
    constant_case,
    control_cases,
    empirical,
    filter_and_assemble,
    gamma,
    initial_vectors,
    observe,
    prepare,
)
from c_workflow_support import close, public


@pytest.mark.parametrize("complex_table", [False, True])
def test_known_parameter_raw_to_native_image(complex_table: bool) -> None:
    """Raw -> actual preparation -> actual native filter; protects absolute scale.

    Wrong alpha, conjugation, normalized inverse, side factor or centered ramp
    changes this result. No estimator is involved in this first control.
    """
    case = constant_case(complex_table=complex_table)
    a, _, f = case.resolved()
    expected_bands = prepare(case)
    carrier, _ = initial_vectors(case)
    modulation = np.array([[0.25 + 0.125j]])
    expected = filter_and_assemble(
        case, expected_bands, dict(carriers_cyc_um=carrier[None], modulation=modulation[None])
    )
    kwargs = {key: value for key, value in a.items() if key != "phase_policy"}
    bands = public().prepare_acquisition_bands(case.raw, **kwargs)
    table = public().declare_otf(
        case.table.samples,
        layout=case.table.layout,
        dkr_cyc_um=case.table.dkr,
        dkz_cyc_um=case.table.dkz,
    )
    actual = public().reconstruct_known(
        bands, table, carriers_cyc_um=carrier, modulation=modulation, **OPTICS, **f
    )
    # n=16,P=3, bounded |H|<=sqrt(50), w²=1. Dense observer and
    # backend <=gamma_4096 L1; two quotients and assembly <=gamma_65536*64.
    bound = gamma(65536) * 64
    close(
        bands.quadratures,
        expected_bands["quadratures"],
        gamma(4096) * 18,
        label="known input bands",
    )
    close(
        actual.filtered_quadratures,
        expected["filtered_quadratures"],
        bound / 16,
        label="known native coefficients",
    )
    close(actual.image, expected["image"], bound, label="known absolute image")


@pytest.mark.parametrize(
    "name", ["ordinary-camera-phase", "true2d-full-floors-products", "empirical-z1"]
)
def test_general_known_controls_from_independent_raw_sums(name: str) -> None:
    case: Case = control_cases()[name]
    expected = observe(case)
    a, _, f = case.resolved()
    prep_kwargs = {key: value for key, value in a.items() if key != "phase_policy"}
    prep_kwargs.update(
        {
            key: value
            for key, value in case.extras.items()
            if key not in ("header_timestamp_unit", "plane_policy")
        }
    )
    bands = public().prepare_acquisition_bands(case.raw, **prep_kwargs)
    if case.bead is None:
        transfer = public().declare_otf(
            case.table.samples,
            layout=case.table.layout,
            dkr_cyc_um=case.table.dkr,
            dkz_cyc_um=case.table.dkz,
        )
    else:
        calibration = public().prepare_bead_otf(case.bead[0], **case.bead[1])
        transfer = calibration.transfer
        truth = empirical(*case.bead)
        case.table = truth["table"]
        # <=32*32*3 terms, four-ulp sin/cos/exp premise, 17 radial
        # reductions and nonzero normalization max>1. Per-value bound.
        bead_bound = gamma(64 * 32 * 32) * 16
        close(
            transfer.samples, truth["table"].samples, bead_bound, label="empirical raw finite sums"
        )
        assert np.any(
            transfer.samples != transfer.samples.astype(np.complex64).astype(np.complex128)
        )
    carrier, _ = initial_vectors(case)
    t, d = case.raw.shape[:2]
    o = a["norders"]
    gains = np.empty((t, d, o - 1), dtype=complex)
    gains[:] = np.array([0.2 + 0.1j * m for m in range(1, o)])
    expected_known = filter_and_assemble(
        case,
        expected["preparation"],
        dict(carriers_cyc_um=np.broadcast_to(carrier, (t, d, 2)), modulation=gains),
    )
    # Use the actual lower public boundary with T all at once and the same
    # known factors at each time. This control proves its own arbitrary gains.
    actual = public().reconstruct_known(
        bands, transfer, carriers_cyc_um=carrier, modulation=gains[0], **OPTICS, **f
    )
    from c_workflow_oracle import error_budget

    budget = error_budget(case, expected)
    from c_workflow_oracle import native_errors

    propagated = native_errors(
        case,
        expected["preparation"],
        dict(carriers_cyc_um=np.broadcast_to(carrier, (t, d, 2)), modulation=gains),
        expected_known,
        budget["preparation_bounds"]["quadratures"],
        budget["preparation_bounds"]["noise_variance_factors"],
        np.zeros_like(gains, dtype=float),
        np.zeros((t, d)),
        (
            np.zeros_like(case.table.samples, dtype=float)
            if case.bead is None
            else budget["calibration_bounds"]["samples"]
        ),
    )
    close(
        actual.filtered_quadratures,
        expected_known["filtered_quadratures"],
        propagated["filtered"],
        label="known coefficients with linked variance uncertainty",
    )
    close(actual.image, expected_known["image"], propagated["image"], label="general known image")
