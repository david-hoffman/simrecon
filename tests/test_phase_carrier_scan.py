"""Blind public-contract tests for independent unknown-phase carrier hypotheses."""

from __future__ import annotations

import warnings
from dataclasses import FrozenInstanceError
from inspect import Parameter, signature
from typing import Any

import numpy as np
import pytest

from phase_carrier_scan_fixture import (
    direct_group,
    local_reference,
    oracle,
    raw_group,
    record,
)
from simrecon import (
    ObservableVolumePhaseEstimate,
    SimreconError,
    VolumeOrderOtf,
    estimate_observable_volume_phases,
    scan_volume_phase_carriers,
)

ARRAY_FIELDS = (
    "phases_rad",
    "phasors",
    "phase_deviations_rad",
    "specimen_normalized",
    "nuisance_singular_values",
    "phase_singular_values",
    "observable_fourier_mask",
)
SOURCE = "  fixed calibration / caller candidate policy  "
USE_GROUP_CANDIDATES = object()


def scan(group: dict, candidates: Any = USE_GROUP_CANDIDATES, **changes: Any):
    """Call the public scan with all controls explicitly supplied."""
    arguments = {
        "order_otf": group["orders"],
        "candidate_carriers_yx": (
            group["candidates"] if candidates is USE_GROUP_CANDIDATES else candidates
        ),
        "initial_phases_rad": group["commands"],
        "max_nfev": 200,
        "gradient_tolerance": 1e-9,
        "step_tolerance": 1e-10,
        "source": SOURCE,
    }
    images = changes.pop("images", group["images"])
    arguments.update(changes)
    return scan_volume_phase_carriers(images, **arguments)


def canonical(phases):
    result = np.arctan2(np.sin(phases), np.cos(phases))
    return np.where(result == np.pi, -np.pi, result)


def assert_profile(row, group, *, tight: float = 2e-11):
    """Compare diagnostics to an independently built all-row real nuisance fit."""
    target = oracle(group["images"], group["orders"], row.phases_rad, row.carrier_bins_yx)
    assert target["condition"] <= 10
    assert target["minimum_singular"] >= 1 / 16
    assert target["allowance"] <= 1 / 1024
    # Tight well-separated fixtures also discriminate errors hidden by the broad E allowance.
    np.testing.assert_allclose(row.specimen_normalized, target["specimen"], atol=tight, rtol=0)
    np.testing.assert_allclose(
        row.nuisance_singular_values, target["nuisance_singular"], atol=tight, rtol=0
    )
    np.testing.assert_allclose(
        row.phase_singular_values, target["phase_singular"], atol=tight, rtol=0
    )
    for name in (
        "relative_residual",
        "normalized_residual_rms",
        "normalized_imaginary_rms",
        "calibration_reality_defect",
        "gradient_inf_norm",
    ):
        assert abs(getattr(row, name) - target[name]) <= tight
    assert row.nuisance_rank == target["nuisance_rank"]
    # Avoid asserting a backend rank at an exact mathematical zero-information boundary.
    if target["phase_singular"][-1] > 1e-8:
        assert row.phase_rank == target["phase_rank"]
    assert row.phase_design_rank == target["phase_design_rank"]
    np.testing.assert_array_equal(row.observable_fourier_mask, target["mask"])
    assert row.observable_dimension == int(np.count_nonzero(target["mask"]))
    assert row.unobservable_dimension == group["images"][0].size - row.observable_dimension
    assert row.source == SOURCE
    assert row.global_ambiguity == "unassessed"
    assert type(row.nfev) is int and row.nfev > 0
    assert type(row.njev) is int and row.njev >= 0
    assert type(row.image_scale) is float
    assert type(row.transfer_scale) is float
    assert row.image_scale == float(np.max(np.abs(group["images"])))
    assert row.transfer_scale == max(
        np.max(np.abs(group["orders"].values.real)), np.max(np.abs(group["orders"].values.imag))
    )
    np.testing.assert_allclose(
        row.phasors, np.cos(row.phases_rad) + 1j * np.sin(row.phases_rad), atol=2e-15, rtol=0
    )
    np.testing.assert_allclose(
        row.phase_deviations_rad,
        canonical(row.phases_rad - canonical(group["commands"])),
        atol=2e-14,
        rtol=0,
    )
    assert np.all(row.phases_rad >= -np.pi) and np.all(row.phases_rad < np.pi)
    return target


@pytest.mark.parametrize(
    "factory", [direct_group, raw_group], ids=["finite-fourier", "raw-spatial"]
)
def test_independent_hidden_phases_five_orders_and_alias_control(factory):
    group = factory()
    rows = scan(group)
    assert type(rows) is tuple and len(rows) == 3
    assert all(type(row) is ObservableVolumePhaseEstimate for row in rows)
    assert [row.carrier_bins_yx for row in rows] == group["candidates"]
    targets = [assert_profile(row, group) for row in rows]
    for carrier, target in zip(group["candidates"], targets, strict=True):
        reference = local_reference(group, carrier)
        # Allow equivalent finite solver organization; phases/trajectories have no
        # cross-platform bit-pattern or universal physical-recovery guarantee.
        assert abs(target["objective"] - reference["objective"]) < target["allowance"]
    # The truth-listed hypothesis is a deliberately included coverage case, not inferred search.
    # Hidden-phase error is measured separately in evaluator evidence, without imposing
    # an unsupported universal phase tolerance or using truth as a solver input.
    for row in rows:
        assert row.termination in {"stationary", "evaluation_limit", "stagnated"}
        assert (row.gradient_inf_norm <= 1e-9) == (row.termination == "stationary")
    np.testing.assert_allclose(rows[1].phases_rad, rows[2].phases_rad, atol=2e-10, rtol=0)
    assert rows[1].carrier_bins_yx != rows[2].carrier_bins_yx


def test_each_row_uses_same_start_and_independent_budget_after_previous_row_moves():
    group = direct_group()
    rows = scan(group, [(0, 0), (1, -1), (1, -1)], max_nfev=3)
    assert len(rows) == 3
    for row in rows:
        isolated = scan(group, [row.carrier_bins_yx], max_nfev=3)[0]
        target = assert_profile(row, group)
        reference = local_reference(group, row.carrier_bins_yx, max_nfev=3)
        assert abs(target["objective"] - reference["objective"]) < target["allowance"]
        np.testing.assert_allclose(row.phases_rad, isolated.phases_rad, atol=2e-10, rtol=0)
        # Each nonstationary budget-three solve needs three actual optimizer residuals.
        # Initial/final evaluator organization may add work; no exact total is assumed.
        assert type(row.nfev) is int and row.nfev >= 3
        assert type(row.njev) is int and row.njev >= 1
        assert row.termination == "evaluation_limit"
    assert np.max(np.abs(rows[0].phase_deviations_rad)) > 1e-3
    # Fresh records are observable. Direct proof against truthful-looking cached counters
    # needs additional public observation support; it is an explicit reviewer limitation.
    assert rows[1] is not rows[2]


def test_scan_matches_single_candidate_public_estimator_without_using_it_as_oracle():
    group = direct_group()
    rows = scan(group, max_nfev=1)
    for row in rows:
        single = estimate_observable_volume_phases(
            group["images"],
            order_otf=group["orders"],
            carrier_bins_yx=row.carrier_bins_yx,
            initial_phases_rad=group["commands"],
            max_nfev=1,
            gradient_tolerance=1e-9,
            step_tolerance=1e-10,
            source=SOURCE,
        )
        for name in ARRAY_FIELDS:
            np.testing.assert_allclose(
                getattr(row, name), getattr(single, name), atol=2e-12, rtol=0
            )
        for name in (
            "termination",
            "nuisance_rank",
            "phase_rank",
            "observable_dimension",
        ):
            assert getattr(row, name) == getattr(single, name)


def test_initial_deficient_row_does_not_stop_later_informative_candidate():
    values = np.ones((3, 1, 1, 3), complex)
    values[1] = -0.5
    values[1, 0, 0, 1] = 0
    values[2] = 0
    group = {
        "images": np.ones((5, 1, 1, 3)),
        "commands": np.zeros(5),
        "orders": record(values),
        "candidates": [(0, 0), (0, 1), (0, 0)],
    }
    rows = scan(group, max_nfev=1)
    assert [row.termination for row in rows] == [
        "nuisance_rank_deficient",
        "stationary",
        "nuisance_rank_deficient",
    ]
    assert [row.nuisance_rank for row in rows] == [1, 3, 1]
    for row in rows:
        assert row.observable_dimension == 3
        np.testing.assert_array_equal(row.phases_rad, np.zeros(5))
        target = oracle(group["images"], group["orders"], row.phases_rad, row.carrier_bins_yx)
        np.testing.assert_allclose(row.specimen_normalized, target["specimen"], atol=2e-12, rtol=0)
        assert abs(row.normalized_residual_rms - target["normalized_residual_rms"]) < 2e-12


@pytest.mark.parametrize("signal", [0.0, -3.0])
def test_all_unobservable_rows_are_retained_with_ordinary_diagnostics(signal):
    group = {
        "images": np.full((5, 1, 2, 3), signal),
        "commands": np.array([1e100, 1.0, 1.0, np.pi, -2.0]),
        "orders": record(np.zeros((3, 1, 2, 3), complex)),
        "candidates": [(0, 0), (10**100, -1), (0, 0)],
    }

    rows = scan(group, max_nfev=10**90)
    assert type(rows) is tuple and len(rows) == 3
    for row in rows:
        assert row.termination == "no_observable_specimen"
        assert row.observable_dimension == row.nuisance_rank == row.phase_rank == 0
        assert row.unobservable_dimension == 6
        assert row.nuisance_singular_values.shape == (0,)
        np.testing.assert_array_equal(row.phase_singular_values, np.zeros(5))
        np.testing.assert_array_equal(row.specimen_normalized, np.zeros((1, 2, 3)))
        np.testing.assert_array_equal(row.observable_fourier_mask, np.zeros((1, 2, 3), bool))
        np.testing.assert_array_equal(row.phases_rad, canonical(group["commands"]))
        assert row.gradient_inf_norm == row.normalized_imaginary_rms == 0.0
        assert row.normalized_residual_rms == (1.0 if signal else 0.0)
        assert row.relative_residual == (1.0 if signal else 0.0)
        assert row.image_scale == (3.0 if signal else 1.0)
        assert row.transfer_scale == 1.0
        assert row.global_ambiguity == "unassessed"


class ListSubclass(list):
    """An unsupported container subtype."""


class TupleSubclass(tuple):
    """An unsupported row subtype."""


class ArraySubclass(np.ndarray):
    """An unsupported array subtype."""


INVALID_CANDIDATES = [
    ("no-table", None),
    ("empty-list", []),
    ("empty-tuple", ()),
    ("scalar-pair", (0, 1)),
    ("scalar", 1),
    ("generator", iter([(0, 1)])),
    ("set", {(0, 1)}),
    ("outer-subclass", ListSubclass([(0, 1)])),
    ("row-subclass", [TupleSubclass((0, 1))]),
    ("row-array", [np.array([0, 1])]),
    ("ragged", [(0, 1), (1,)]),
    ("long-row", [(0, 1, 2)]),
    ("bool", [(False, 1)]),
    ("numpy-bool", [(np.bool_(True), 1)]),
    ("float", [(1.0, 0)]),
    ("numpy-float", [(0, np.float64(1))]),
    ("complex", [(1j, 0)]),
    ("string", [("1", 0)]),
    ("none", [(0, None)]),
    ("object", [(object(), 0)]),
    ("array-subclass", np.array([[0, 1]]).view(ArraySubclass)),
    ("masked", np.ma.array([[0, 1]])),
    ("array-bool", np.array([[False, True]])),
    ("array-float", np.array([[0.0, 1.0]])),
    ("array-object", np.array([[0, 1]], object)),
    ("array-empty", np.empty((0, 2), int)),
    ("array-flat", np.array([0, 1])),
    ("array-extra-axis", np.zeros((1, 1, 2), int)),
    ("array-wrong-columns", np.zeros((2, 3), int)),
    ("invalid-later-row", [(0, 0), (0, 0), (0, 1.0)]),
]


@pytest.mark.parametrize(
    "candidates",
    [value for _, value in INVALID_CANDIDATES],
    ids=[name for name, _ in INVALID_CANDIDATES],
)
def test_candidate_grammar_validates_complete_table_before_numerical_work(candidates, monkeypatch):
    group = direct_group()
    calls = []
    native = np.fft.fftn

    def observe(*args, **kwargs):
        calls.append(True)
        return native(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", observe)
    with pytest.raises(SimreconError) as caught:
        scan(group, candidates)
    assert caught.value.code == "invalid_volume_phase_carrier_candidates"
    assert not calls
    # The same malformed table must not disappear behind the r=0 early return.
    group["orders"] = record(np.zeros_like(group["orders"].values))
    with pytest.raises(SimreconError) as caught:
        scan(group, candidates)
    assert caught.value.code == "invalid_volume_phase_carrier_candidates"


@pytest.mark.parametrize(
    "representation", ["mixed", "tuple", "unsigned", "endian", "fortran", "strided", "readonly"]
)
def test_candidate_positives_preserve_exact_original_integers_order_and_aliases(representation):
    group = direct_group()
    huge = 10**100 + 1
    if representation == "mixed":
        candidates = [
            [huge, -(10**101)],
            (np.int64(-3), np.uint64(2**64 - 1)),
            [0, 0],
            [huge, -(10**101)],
        ]
    elif representation == "tuple":
        candidates = ((0, 0), [np.int8(1), np.uint8(2)], (1, 2))
    else:
        candidates = np.array(
            [[0, 0], [1, 2], [1, 2]], dtype=np.uint64 if representation == "unsigned" else np.int64
        )
        if representation == "unsigned":
            candidates[1, 0] = np.uint64(2**64 - 1)
        if representation == "endian":
            candidates = candidates.astype(">i8")
        if representation == "fortran":
            candidates = np.asfortranarray(candidates)
        if representation == "strided":
            candidates = np.repeat(candidates, 2, axis=1)[:, ::2]
        if representation == "readonly":
            candidates.setflags(write=False)
    expected = [(int(row[0]), int(row[1])) for row in candidates]
    rows = scan(group, candidates, max_nfev=1)
    assert [row.carrier_bins_yx for row in rows] == expected
    for row in rows:
        assert type(row.carrier_bins_yx) is tuple
        assert all(type(value) is int for value in row.carrier_bins_yx)
        assert_profile(row, group)


def test_result_arrays_are_owned_mutable_and_independent_across_fields_rows_and_calls():
    group = direct_group()
    candidates = [[1, -1], [1, -1], [3, 2]]
    inputs = [
        group["images"],
        group["commands"],
        group["orders"].values,
        group["orders"].fz_per_um,
        group["orders"].fy_per_um,
        group["orders"].fx_per_um,
    ]
    snapshots = [array.copy() for array in inputs]
    layout = [(array.strides, array.flags.writeable) for array in inputs]
    rows = scan(group, candidates, max_nfev=1)
    more = scan(group, candidates, max_nfev=1)
    arrays = [getattr(row, name) for row in (*rows, *more) for name in ARRAY_FIELDS]
    dtypes = {
        "phasors": np.dtype(complex),
        "observable_fourier_mask": np.dtype(bool),
    }
    for row in (*rows, *more):
        for name in ARRAY_FIELDS:
            assert getattr(row, name).dtype == dtypes.get(name, np.dtype(float))
    for index, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.flags.c_contiguous and array.flags.writeable
        assert array.dtype.isnative
        for other in inputs + arrays[:index]:
            assert not np.shares_memory(array, other)
    for name in ARRAY_FIELDS:
        array = getattr(rows[0], name)
        before = [getattr(row, name).copy() for row in (*rows[1:], *more)]
        array[...] = False if array.dtype.kind == "b" else 17
        for row, snapshot in zip((*rows[1:], *more), before, strict=True):
            np.testing.assert_array_equal(getattr(row, name), snapshot)
    for row in rows:
        with pytest.raises((AttributeError, FrozenInstanceError)):
            row.source = "changed"
        with pytest.raises((AttributeError, FrozenInstanceError)):
            del row.phases_rad
    candidates[0][0] = 77
    assert rows[0].carrier_bins_yx == (1, -1)
    for array, snapshot, state in zip(inputs, snapshots, layout, strict=True):
        np.testing.assert_array_equal(array, snapshot)
        assert (array.strides, array.flags.writeable) == state


def change_orders(orders, **changes):
    fields = {
        name: getattr(orders, name)
        for name in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }
    fields.update(changes)
    return VolumeOrderOtf(**fields)


SHARED_INVALID = [
    (
        "images-list",
        "images",
        lambda g: g["images"].tolist(),
        "invalid_volume_phase_estimation_images",
    ),
    (
        "images-kind",
        "images",
        lambda g: g["images"].astype(complex),
        "invalid_volume_phase_estimation_images",
    ),
    (
        "images-subclass",
        "images",
        lambda g: g["images"].view(ArraySubclass),
        "invalid_volume_phase_estimation_images",
    ),
    ("images-count", "images", lambda g: g["images"][:4], "invalid_volume_phase_estimation_images"),
    (
        "images-nan",
        "images",
        lambda g: np.full_like(g["images"], np.nan),
        "nonfinite_volume_phase_estimation_images",
    ),
    (
        "phases-list",
        "initial_phases_rad",
        lambda g: g["commands"].tolist(),
        "invalid_volume_phase_estimation_initial_phases",
    ),
    (
        "phases-count",
        "initial_phases_rad",
        lambda g: g["commands"][:-1],
        "invalid_volume_phase_estimation_initial_phases",
    ),
    (
        "phases-bool",
        "initial_phases_rad",
        lambda g: np.zeros(7, bool),
        "invalid_volume_phase_estimation_initial_phases",
    ),
    (
        "phases-inf",
        "initial_phases_rad",
        lambda g: np.full(7, np.inf),
        "nonfinite_volume_phase_estimation_initial_phases",
    ),
    ("otf-record", "order_otf", lambda g: None, "invalid_volume_phase_estimation_otf"),
    (
        "otf-unused-nan",
        "order_otf",
        lambda g: change_orders(
            g["orders"],
            values=np.concatenate(
                (g["orders"].values[:2], np.full_like(g["orders"].values[2:], np.nan))
            ),
        ),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-width",
        "order_otf",
        lambda g: change_orders(g["orders"], values=g["orders"].values.astype(np.complex64)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-fz",
        "order_otf",
        lambda g: change_orders(g["orders"], fz_per_um=np.ones(2)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-fy",
        "order_otf",
        lambda g: change_orders(g["orders"], fy_per_um=np.ones(2)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-fx",
        "order_otf",
        lambda g: change_orders(g["orders"], fx_per_um=np.ones(3)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-spacing",
        "order_otf",
        lambda g: change_orders(g["orders"], voxel_size_um=(1.0, 0.0, 1.0)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-origin",
        "order_otf",
        lambda g: change_orders(g["orders"], origin_zyx=(2, 0, 0)),
        "invalid_volume_phase_estimation_otf",
    ),
    (
        "otf-source",
        "order_otf",
        lambda g: change_orders(g["orders"], source=" "),
        "invalid_volume_phase_estimation_otf",
    ),
    ("budget-bool", "max_nfev", lambda g: True, "invalid_volume_phase_estimation_controls"),
    ("budget-zero", "max_nfev", lambda g: 0, "invalid_volume_phase_estimation_controls"),
    ("budget-float", "max_nfev", lambda g: 2.0, "invalid_volume_phase_estimation_controls"),
    (
        "gradient-low",
        "gradient_tolerance",
        lambda g: np.finfo(float).eps,
        "invalid_volume_phase_estimation_controls",
    ),
    (
        "gradient-high",
        "gradient_tolerance",
        lambda g: 1.0,
        "invalid_volume_phase_estimation_controls",
    ),
    (
        "gradient-bool",
        "gradient_tolerance",
        lambda g: False,
        "invalid_volume_phase_estimation_controls",
    ),
    ("step-nan", "step_tolerance", lambda g: np.nan, "invalid_volume_phase_estimation_controls"),
    ("step-low", "step_tolerance", lambda g: 0, "invalid_volume_phase_estimation_controls"),
    ("step-bool", "step_tolerance", lambda g: True, "invalid_volume_phase_estimation_controls"),
    ("source", "source", lambda g: " \t ", "invalid_otf_source"),
]


@pytest.mark.parametrize(
    "field,factory,code",
    [(field, factory, code) for _, field, factory, code in SHARED_INVALID],
    ids=[name for name, _, _, _ in SHARED_INVALID],
)
def test_shared_validation_cannot_be_skipped_by_all_unobservable_rows(field, factory, code):
    group = direct_group()
    group["orders"] = record(np.zeros_like(group["orders"].values))
    change = factory(group)
    before = group["images"].copy()
    mode = np.geterr()
    filters = list(warnings.filters)
    with np.errstate(all="raise"), pytest.raises(SimreconError) as caught:
        scan(group, [(0, 0), (10**90, -3)], **{field: change})
    assert caught.value.code == code
    np.testing.assert_array_equal(group["images"], before)
    assert np.geterr() == mode
    assert warnings.filters == filters


class OrdersSubclass(VolumeOrderOtf):
    """Ordinary public record subclasses are legitimate inputs."""


def test_shared_permitted_layout_endian_readonly_subclass_and_signed_observations():
    group = direct_group()
    group["images"] = np.asfortranarray(group["images"].astype(">f8"))
    group["commands"] = np.repeat(group["commands"].astype(">f8"), 2)[::2]
    old = group["orders"]
    fields = {
        name: getattr(old, name)
        for name in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }
    fields["values"] = np.asfortranarray(old.values.astype(">c16"))
    for name in ("fz_per_um", "fy_per_um", "fx_per_um"):
        fields[name] = fields[name].astype(">f8")
    group["orders"] = OrdersSubclass(**fields)
    inputs = [
        group["images"],
        group["commands"],
        fields["values"],
        fields["fz_per_um"],
        fields["fy_per_um"],
        fields["fx_per_um"],
    ]
    for array in inputs:
        array.setflags(write=False)
    snapshots = [(array.tobytes(), array.strides) for array in inputs]
    mode = np.geterr()
    filters = list(warnings.filters)
    with np.errstate(all="raise"):
        rows = scan(
            group,
            max_nfev=np.int64(1),
            gradient_tolerance=np.float32(1e-8),
            step_tolerance=np.float64(1e-10),
        )
    for row in rows:
        assert_profile(row, group)
    for array, (contents, strides) in zip(inputs, snapshots, strict=True):
        assert array.tobytes() == contents and array.strides == strides
        assert not array.flags.writeable
    assert np.geterr() == mode and warnings.filters == filters


def test_sparse_complex_transfers_have_carrier_specific_structural_dimensions():
    group = direct_group()
    values = np.zeros_like(group["orders"].values)
    values[0, 1, 1, 1] = 1 + 0.2j  # Retain non-Hermitian zero-order mismatch.
    values[1, 0, 1, 2] = 0.7 - 0.1j
    values[2, 1, 0, 1] = -0.5 + 0.3j
    group["orders"] = record(values, origin=(1, 1, 2))
    rows = scan(group, [(0, 0), (1, -1), (0, 1)], max_nfev=1)
    dimensions = []
    for row in rows:
        target = oracle(group["images"], group["orders"], row.phases_rad, row.carrier_bins_yx)
        np.testing.assert_array_equal(row.observable_fourier_mask, target["mask"])
        dimensions.append(int(np.count_nonzero(target["mask"])))
        assert row.observable_dimension == dimensions[-1]
        assert row.unobservable_dimension == 12 - dimensions[-1]
        assert row.nuisance_singular_values.shape == (dimensions[-1],)
        np.testing.assert_allclose(row.specimen_normalized, target["specimen"], atol=2e-11, rtol=0)
        assert abs(row.normalized_residual_rms - target["normalized_residual_rms"]) < 2e-11
        assert abs(row.normalized_imaginary_rms - target["normalized_imaginary_rms"]) < 2e-11
        assert abs(row.calibration_reality_defect - target["calibration_reality_defect"]) < 2e-11
    assert len(set(dimensions)) > 1


@pytest.mark.parametrize(
    "exception,code",
    [
        (
            FloatingPointError("A01 transform arithmetic"),
            "volume_phase_estimation_transform_failure",
        ),
        (OverflowError("A01 transform range"), "volume_phase_estimation_transform_failure"),
        (MemoryError("A01 actual allocation exception"), None),
        (RuntimeError("A01 unrelated transform exception"), None),
        (TypeError("A01 unrelated transform type exception"), None),
    ],
)
def test_actual_transform_entry_failure_aborts_whole_call_and_preserves_inputs(
    monkeypatch, exception, code
):
    group = direct_group()
    before = group["images"].copy()
    entered = []

    def failing_transform(*args, **kwargs):
        entered.append(True)
        raise exception

    monkeypatch.setattr(np.fft, "fftn", failing_transform)
    with pytest.raises(SimreconError if code else type(exception)) as caught:
        scan(group)
    assert entered
    if code:
        assert caught.value.code == code
    else:
        assert caught.value is exception
    np.testing.assert_array_equal(group["images"], before)


def test_all_keywords_are_required_and_only_images_is_positional():
    group = direct_group()
    arguments = {
        "order_otf": group["orders"],
        "candidate_carriers_yx": [(0, 0)],
        "initial_phases_rad": group["commands"],
        "max_nfev": 1,
        "gradient_tolerance": 1e-9,
        "step_tolerance": 1e-10,
        "source": SOURCE,
    }
    public_signature = signature(scan_volume_phase_carriers)
    public_signature.bind(group["images"], **arguments)
    for key in arguments:
        parameter = public_signature.parameters[key]
        assert parameter.kind is Parameter.KEYWORD_ONLY
        assert parameter.default is Parameter.empty
        missing = dict(arguments)
        del missing[key]
        with pytest.raises(TypeError):
            scan_volume_phase_carriers(group["images"], **missing)
    remaining = dict(arguments)
    positional_order_otf = remaining.pop("order_otf")
    with pytest.raises(TypeError):
        scan_volume_phase_carriers(group["images"], positional_order_otf, **remaining)


@pytest.mark.parametrize(
    "failure", [TypeError, ValueError, OverflowError, MemoryError, RuntimeError]
)
def test_candidate_extraction_exceptions_are_confined_to_the_named_boundary(failure):
    seen = []

    class ExtractingInteger(int):
        def __int__(self):
            seen.append(True)
            raise failure("A01 candidate integer conversion")

    group = direct_group()
    candidate = ExtractingInteger(1)
    try:
        rows = scan(group, [(candidate, -1)], max_nfev=1)
    except (SimreconError, MemoryError, RuntimeError) as error:
        assert seen
        if failure in (TypeError, ValueError, OverflowError):
            assert isinstance(error, SimreconError)
            assert error.code == "invalid_volume_phase_carrier_candidates"
        else:
            assert type(error) is failure
    else:
        # A valid exact extraction may bypass an int subtype's overridable __int__.
        # The contract does not prescribe that Python protocol as the only algorithm.
        assert not seen
        assert rows[0].carrier_bins_yx == (1, -1)


def test_arithmetic_dependency_warning_translates_and_unrelated_warning_remains_visible(
    monkeypatch,
):
    group = direct_group()
    native = np.fft.fftn
    mode, filters = np.geterr(), list(warnings.filters)

    def numerical_warning(*args, **kwargs):
        warnings.warn("overflow encountered in multiply", RuntimeWarning, stacklevel=1)
        return native(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", numerical_warning)
    with pytest.raises(SimreconError) as caught:
        scan(group)
    assert caught.value.code == "volume_phase_estimation_transform_failure"
    assert np.geterr() == mode and warnings.filters == filters

    def ordinary_warning(*args, **kwargs):
        warnings.warn("A01 unrelated public warning", UserWarning, stacklevel=1)
        return native(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", ordinary_warning)
    with pytest.warns(UserWarning, match="A01 unrelated public warning"):
        rows = scan(group, max_nfev=1)
    assert len(rows) == len(group["candidates"])
    assert np.geterr() == mode and warnings.filters == filters
