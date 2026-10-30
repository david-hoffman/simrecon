"""Blind public RA06 contract tests; expectations precede product observations."""

import warnings
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, localcontext
from itertools import combinations
from typing import Any

import numpy as np
import pytest

from reference_alignment_ra06_fixture import (
    EPS,
    Case,
    bins,
    case,
    dec,
    design,
    fourier,
    matched_case,
    matrix,
    observe,
    real_map,
    solve,
    synthesize,
)


def api() -> Any:
    # Missing additive API is setup/absence, never classified as product-red.
    import simrecon

    assert hasattr(simrecon, "reconstruct_volume_weighted"), "SETUP_ABSENCE: weighted API"
    assert hasattr(simrecon, "WeightedReconstruction3D"), "SETUP_ABSENCE: weighted record"
    return simrecon


def run(c: Case, **changes: Any) -> Any:
    arguments = c.arguments()
    arguments.update(changes)
    return api().reconstruct_volume_weighted(c.images, **arguments)


def close(actual: Any, expected: Any, allowance: float) -> None:
    assert np.all(np.isfinite(actual))
    error = np.max(np.abs(np.asarray(actual) - np.asarray(expected)), initial=0)
    assert error <= allowance, f"absolute error {error} exceeds prior budget {allowance}"


def agrees(c: Case) -> tuple[Any, Any]:
    truth = observe(c)
    result = run(c)
    tolerance = truth.tolerance
    close(result.untapered_volume, truth.x, tolerance)
    close(result.untapered_spectrum, truth.spectrum, tolerance)
    close(result.spectrum, truth.spectrum * c.taper, tolerance)
    close(result.volume, synthesize(truth.spectrum * c.taper), tolerance * np.prod(c.output))
    close(result.separated_coordinates, truth.coordinates, tolerance)
    close(result.separated_covariance, truth.covariance, tolerance)
    close(
        result.predicted_images,
        truth.predicted,
        tolerance * max(1, np.linalg.norm(truth.a, np.inf)),
    )
    close(
        result.residual_images, truth.residual, tolerance * max(1, np.linalg.norm(truth.a, np.inf))
    )
    close(result.data_objective, truth.data_objective, truth.objective_tolerance)
    close(result.penalty_objective, truth.penalty_objective, truth.objective_tolerance)
    assert result.information_rank == truth.rank
    assert result.unknown_count == int(np.prod(c.output))
    normal_residual = truth.normal @ result.untapered_volume.ravel() - truth.rhs
    close(normal_residual, 0, tolerance * max(1, np.linalg.norm(truth.normal, np.inf)))
    return result, truth


def rejects(c: Case, code: str, **changes: Any) -> None:
    library = api()
    with pytest.raises(library.SimreconError) as caught:
        run(c, **changes)
    assert caught.value.code == code


def test_independent_observer_real_forward_adjoint_and_source_gram() -> None:
    c = case(detector=(1, 1, 3), n=5)
    c.transfers[:] = 0
    c.transfers[:, 0] = 0.75 + 0.4j
    c.gains[:] = 1
    with localcontext() as context:
        context.prec = 70
        h, a = real_map(c)
        # Real E0=0.75 is an identity convolution on the native grid;
        # its imaginary DC prediction is intentionally unobserved.
        expected = np.tile(0.75 * np.eye(3), (5, 1))
        close(np.asarray(a, float), expected, 1e-60)
        x, dual = matrix([0.2, -0.7, 1.1]), matrix(np.arange(15) / 11)
        assert abs(np.sum((a @ x) * dual) - np.sum(x * (a.T @ dual))) < Decimal("1e-60")
        fr, fi = fourier(c.output)
        basis = np.stack((np.ones(3), np.asarray(fr[2], float), np.asarray(fi[2], float)), axis=1)
        close(basis.T @ basis / 3, np.diag([1, 0.5, 0.5]), 16 * EPS)
        assert np.max(np.abs(np.asarray(h[0, 0], float) - 0.75 * np.eye(3))) < 1e-60
    truth = observe(c)
    assert abs(truth.constant) < 1e-50
    assert abs(truth.data_objective - truth.separated_objective - truth.constant) < 128 * EPS


@pytest.mark.parametrize(
    ("detector", "carriers", "n"),
    [
        ((1, 1, 3), ((0, 0),), 7),
        ((2, 2, 2), ((0, 1),), 5),
        ((3, 1, 2), ((1, -1),), 5),
        ((1, 2, 3), ((0, 1), (0, -1)), 5),
        ((1, 1, 3), ((0, 0), (0, 0)), 7),
    ],
)
def test_full_real_inverse_odd_even_signed_placement_and_correlated_gls(
    detector: tuple[int, int, int],
    carriers: tuple[tuple[int, int], ...],
    n: int,
) -> None:
    c = case(detector, carriers, n)
    _, truth = agrees(c)
    assert truth.constant > 1e-3 if n > 5 else abs(truth.constant) < 1e-50
    assert np.max(np.abs(truth.covariance - np.diag(np.diag(truth.covariance[0])))) > 1e-3


def test_gls_off_model_constant_covariance_and_joint_permutation() -> None:
    c = case(n=7)
    truth = observe(c)
    ordinary = np.linalg.lstsq(design(c.phases)[0], c.images[0].reshape(7, -1), rcond=None)[0]
    assert np.max(np.abs(truth.coordinates[0].reshape(5, -1) - ordinary)) > 0.01
    assert truth.constant > 0.05
    first, _ = agrees(c)
    permutation = np.array([6, 2, 0, 5, 1, 4, 3])
    permuted = replace(
        c,
        images=c.images[:, permutation],
        phases=c.phases[:, permutation],
        covariance=c.covariance[:, permutation][:, :, permutation],
    )
    second, expected = agrees(permuted)
    close(second.untapered_volume, first.untapered_volume, truth.tolerance + expected.tolerance)
    close(
        second.separated_covariance,
        first.separated_covariance,
        truth.tolerance + expected.tolerance,
    )
    close(
        second.data_objective,
        first.data_objective,
        truth.objective_tolerance + expected.objective_tolerance,
    )


def test_five_exposures_coordinates_ignore_covariance_but_inverse_does_not() -> None:
    c = case(n=5)
    first, truth = agrees(c)
    changed = replace(c, covariance=np.array([np.diag([4.0, 1.0, 0.4, 2.0, 0.7])]))
    second, other = agrees(changed)
    close(
        first.separated_coordinates, second.separated_coordinates, truth.tolerance + other.tolerance
    )
    assert np.max(np.abs(truth.covariance - other.covariance)) > 0.01
    assert np.max(np.abs(truth.x - other.x)) > 0.01


def test_huge_finite_phases_and_valid_repeated_rows_use_represented_square() -> None:
    c = case(n=7)
    c.phases = np.array([[1e308, -1e308, 0.12, 0.91, 2.07, 3.16, 4.51]])
    assert np.linalg.cond(design(c.phases)[0]) < 10
    agrees(c)
    c.phases[:] = 0
    rejects(c, "rank_deficient_volume_phases")


def test_matched_ra02_diagonal_wiener_and_penalty_units() -> None:
    variance = 0.6
    c = matched_case(variance)
    truth = observe(c)
    # This is a declared represented metric. It is not inferred white raw noise.
    expected_psi = np.diag([variance, variance / 2, variance / 2, variance / 2, variance / 2])
    close(truth.covariance[0], expected_psi, 128 * EPS)
    z = truth.coordinates[0].reshape(5, -1)
    fr, fi = fourier(c.detector)
    fourier_matrix = np.asarray(fr, float) - 1j * np.asarray(fi, float)
    bands = [z[0], z[1] + 1j * z[2], z[3] + 1j * z[4]]
    numerator = np.zeros(3, dtype=complex)
    denominator = np.zeros(3)
    for order, band in enumerate(bands):
        coefficient = fourier_matrix @ band / 3
        transfer = c.gains[0] * c.transfers[0, order].ravel()
        numerator += np.conj(transfer) * coefficient / variance
        denominator += np.abs(transfer) ** 2 / variance
        if order:
            # Complete conjugation, not a second independent noisy observation.
            negative = fourier_matrix @ np.conj(band) / 3
            numerator += np.conj(transfer) * negative / variance
            denominator += np.abs(transfer) ** 2 / variance
    expected = numerator / (denominator + c.alpha)
    close(truth.spectrum.ravel(), expected, 4096 * EPS)
    close(expected, numerator * variance / (denominator * variance + c.alpha * variance), 128 * EPS)
    result, _ = agrees(c)
    library = api()
    legacy_arguments = c.arguments()
    legacy_arguments.pop("exposure_covariance")
    # v_ref*alpha is the squared-transfer penalty of the original estimator.
    legacy_arguments["regularization"] = c.alpha * variance
    original = library.reconstruct_volume(c.images, **legacy_arguments)
    close(original.spectrum, result.untapered_spectrum, truth.tolerance)
    close(original.volume, result.untapered_volume, truth.tolerance * 3)


def test_physical_white_phase_metric_has_bounded_represented_gram_error() -> None:
    c = matched_case()
    c.phases = (np.arange(5) * (2 * np.pi / 5))[None]
    variance_raw = 0.8
    c.covariance = np.eye(5)[None] * variance_raw
    k = design(c.phases)[0]
    ideal_gram = np.diag([5, 10, 10, 10, 10])
    perturbation = np.linalg.norm(k.T @ k - ideal_gram, 2)
    assert 0 < perturbation < 128 * EPS
    # Inverse perturbation bound, with the measured represented-input Gram only.
    bound = variance_raw * perturbation / (5 * (5 - perturbation)) + 128 * EPS
    truth = observe(c)
    close(truth.covariance[0], np.diag([0.16, 0.08, 0.08, 0.08, 0.08]), bound)
    agrees(c)


def _observable_dc_amplitude(c: Case, weight: float) -> float:
    """Derive the scalar answer from the stored DC transfer, gain and data."""
    dc_index = (0, 0, *(n // 2 for n in c.detector))
    effective_transfer = float(c.gains[0]) * float(np.real(c.transfers[dc_index]))
    level = float(c.images.flat[0])
    information = effective_transfer**2 * weight
    return level * effective_transfer * weight / (information + c.alpha)


@pytest.mark.parametrize("alpha", [0.0, 0.2])
def test_observable_dc_nullspace_minimum_norm_and_rank_zero(alpha: float) -> None:
    c = case(n=5, alpha=alpha)
    c.transfers[:] = 0
    c.transfers[0, 0, 0, 0, 1] = 0.75
    c.images[:] = 1.4
    # Exactly one source direction. Raw y is constant across phase and voxel.
    k = design(c.phases)[0]
    precision = np.linalg.solve(c.covariance[0], np.ones(5))
    expected = _observable_dc_amplitude(c, float(np.sum(precision)))
    tolerance = 8192 * EPS * 15 * max(1.0, abs(expected))
    result = run(c)
    close(result.untapered_volume, expected, tolerance)
    assert result.information_rank == 1
    assert result.unknown_count == 3
    # The two cosine/sine source directions are null and must stay zero.
    close(result.untapered_spectrum.ravel()[[0, 2]], 0, tolerance)
    assert np.linalg.matrix_rank(k) == 5
    c.transfers[:] = 0
    result = run(c)
    for name in (
        "untapered_volume",
        "untapered_spectrum",
        "volume",
        "spectrum",
        "predicted_images",
    ):
        assert np.count_nonzero(getattr(result, name)) == 0
    close(result.residual_images, c.images, 0)
    close(result.data_objective, 1.4**2 * np.sum(precision), tolerance * 64)
    assert result.penalty_objective == 0
    assert result.information_rank == 0


def test_ridge_retains_below_rank_cutoff_and_zero_alpha_discards_it() -> None:
    c = case(detector=(1, 1, 2), n=5, alpha=0)
    n = 128
    c.phases = np.linspace(0.1, 6.1, n)[None]
    c.covariance = np.eye(n)[None]
    c.images = np.tile(np.array([1.0, -1.0]), (1, n, 1)).reshape(1, n, 1, 1, 2)
    c.gains[:] = 1
    c.transfers[:] = 0
    weak = 2e-14
    c.transfers[0, 0, 0, 0] = [weak, 0.7]
    # Exactly orthogonal DC and canonical real Nyquist; their singular values
    # are sqrt(N)*0.7 and sqrt(N)*weak. The weak value is below tau by a factor >1.9.
    assert weak < EPS * (n * 2) * 0.7 / 1.9
    zero = run(c)
    assert zero.information_rank == 1
    close(zero.untapered_volume, 0, 8192 * EPS * (n * 2))
    positive = replace(c, alpha=n * weak)
    ridge = run(positive)
    expected = (n * weak / (n * weak * weak + positive.alpha)) * np.array([1.0, -1.0])
    # Outside mandatory accuracy. Allow weak-mode uncertainty from a 32-epsilon
    # strong-mode backward perturbation, before observing the candidate.
    allowance = 32 * EPS * 0.7 / weak + 8192 * EPS * (n * 2)
    assert allowance < 0.3
    close(ridge.untapered_volume.ravel(), expected, allowance)
    assert ridge.information_rank == 1


@pytest.mark.parametrize("scaling", ["covariance", "gain", "intensity", "joint"])
def test_declared_scaling_laws(scaling: str) -> None:
    c = case(n=5)
    truth = observe(c)
    a = 2.0
    factor = 1.0
    if scaling == "covariance":
        changed = replace(c, covariance=c.covariance * a, alpha=c.alpha / a)
    elif scaling == "gain":
        changed = replace(c, gains=c.gains * a, alpha=c.alpha * a * a)
        factor = 1 / a
    elif scaling == "intensity":
        changed = replace(
            c, images=c.images * a, covariance=c.covariance * a * a, alpha=c.alpha / (a * a)
        )
        factor = a
    else:
        changed = replace(
            c, images=c.images * a, gains=c.gains * a, covariance=c.covariance * a * a
        )
    first, _ = agrees(c)
    second, other = agrees(changed)
    close(
        second.untapered_volume,
        factor * first.untapered_volume,
        truth.tolerance * factor + other.tolerance,
    )


def test_asymmetric_and_zero_taper_follow_inverse_and_leave_diagnostics() -> None:
    c = case(detector=(2, 1, 2), carriers=((0, 1),), n=5)
    first, truth = agrees(c)
    taper = np.linspace(0.1, 0.9, np.prod(c.output)).reshape(c.output)
    masked = replace(c, taper=taper)
    second, _ = agrees(masked)
    assert np.max(np.abs(np.imag(synthesize(truth.spectrum * taper)))) > 1e-3
    zero, _ = agrees(replace(c, taper=np.zeros(c.output)))
    for name in (
        "untapered_volume",
        "untapered_spectrum",
        "predicted_images",
        "residual_images",
        "separated_coordinates",
        "separated_covariance",
        "data_objective",
        "penalty_objective",
    ):
        close(getattr(second, name), getattr(first, name), truth.objective_tolerance)
        close(getattr(zero, name), getattr(first, name), truth.objective_tolerance)
    assert second.information_rank == first.information_rank == zero.information_rank
    assert np.count_nonzero(zero.volume) == np.count_nonzero(zero.spectrum) == 0


def test_public_record_binding_array_ownership_and_coordinates() -> None:
    c = case(detector=(2, 1, 2), carriers=((0, 1),), n=5)
    arguments = c.arguments()
    result = api().reconstruct_volume_weighted(c.images, **arguments)
    assert isinstance(result, api().WeightedReconstruction3D)
    expected_fields = {
        "volume",
        "spectrum",
        "untapered_volume",
        "untapered_spectrum",
        "separated_coordinates",
        "separated_covariance",
        "predicted_images",
        "residual_images",
        "data_objective",
        "penalty_objective",
        "information_rank",
        "unknown_count",
        "fz_per_um",
        "fy_per_um",
        "fx_per_um",
        "voxel_size_um",
    }
    public_fields = {
        name
        for name in dir(result)
        if not name.startswith("_") and not callable(getattr(result, name))
    }
    assert public_fields == expected_fields
    second = run(c)
    arrays = [
        getattr(result, name)
        for name in expected_fields
        if isinstance(getattr(result, name), np.ndarray)
    ]
    inputs = [c.images, c.phases, c.carriers, c.gains, c.covariance, c.taper]
    for record in arguments["order_otfs"]:
        inputs.extend([record.values, record.fz_per_um, record.fy_per_um, record.fx_per_um])
    for value in arrays:
        assert value.flags.owndata and value.flags.c_contiguous and value.flags.writeable
        assert value.dtype.isnative
        for caller in inputs:
            assert not np.shares_memory(value, caller)
        for name in expected_fields:
            other = getattr(second, name)
            if isinstance(other, np.ndarray):
                assert not np.shares_memory(value, other)
    for left, right in combinations(arrays, 2):
        assert not np.shares_memory(left, right)
    for name in ("volume", "spectrum", "untapered_spectrum"):
        assert getattr(result, name).dtype == np.dtype("complex128")
        assert getattr(result, name).shape == c.output
    for name in (
        "untapered_volume",
        "separated_coordinates",
        "separated_covariance",
        "predicted_images",
        "residual_images",
    ):
        assert getattr(result, name).dtype == np.dtype("float64")
    for name in ("information_rank", "unknown_count"):
        assert type(getattr(result, name)) is int
    for name in ("data_objective", "penalty_objective"):
        assert type(getattr(result, name)) is float
        assert np.isfinite(getattr(result, name)) and getattr(result, name) >= 0
    spacing = (
        c.spacing[0],
        c.detector[1] * c.spacing[1] / c.out[0],
        c.detector[2] * c.spacing[2] / c.out[1],
    )
    assert result.voxel_size_um == spacing
    assert type(result.voxel_size_um) is tuple
    assert all(type(v) is float for v in result.voxel_size_um)
    assert result.untapered_volume.shape == c.output
    assert result.separated_coordinates.shape == (len(c.gains), 5, *c.detector)
    assert result.separated_covariance.shape == (len(c.gains), 5, 5)
    assert result.predicted_images.shape == result.residual_images.shape == c.images.shape
    for n, d, output_n, name in zip(
        c.detector, c.spacing, c.output, ("fz_per_um", "fy_per_um", "fx_per_um"), strict=True
    ):
        frequency = np.array([q[0] / (n * d) for q in bins((output_n,))])
        assert getattr(result, name).shape == (output_n,)
        close(getattr(result, name), frequency, 8 * EPS * max(1, np.max(np.abs(frequency))))
        assert getattr(result, name).dtype == np.dtype("float64")
    for name in expected_fields:
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(result, name, None)
        with pytest.raises((FrozenInstanceError, AttributeError)):
            delattr(result, name)
    for value in arrays:
        value.flat[0] = 9
        assert value.flat[0] == 9
    # Every keyword is required; images alone is positional.
    for omitted in arguments:
        missing = dict(arguments)
        missing.pop(omitted)
        with pytest.raises(TypeError):
            api().reconstruct_volume_weighted(c.images, **missing)
    with pytest.raises(TypeError):
        api().reconstruct_volume_weighted(c.images, *arguments.values())


class ArraySubclass(np.ndarray):
    """A genuine ndarray subclass must remain distinguishable from a plain array."""


def nonplain(value: np.ndarray, form: str) -> Any:
    if form == "list":
        return value.tolist()
    if form == "subclass":
        return value.view(ArraySubclass)
    return np.ma.array(value)


def representation(value: np.ndarray, style: str) -> np.ndarray:
    if style == "endian":
        return value.astype(value.dtype.newbyteorder(">"))
    if style == "fortran":
        return np.asfortranarray(value)
    if style == "strided":
        expanded = np.repeat(value, 2, axis=-1)
        return expanded[..., ::2]
    answer = value.copy()
    answer.setflags(write=False)
    return answer


@pytest.mark.parametrize(
    "dtype",
    [
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "float16",
        "float32",
        "float64",
        "longdouble",
    ],
)
def test_all_real_widths_and_signed_unsigned_input_classes(dtype: str) -> None:
    c = case(detector=(1, 1, 1), n=5)
    c.images = np.abs(c.images * 7).astype(dtype)
    c.phases = np.arange(5, dtype=dtype)[None]
    c.gains = np.ones(1, dtype=dtype)
    c.covariance = (np.eye(5) * 2).astype(dtype)[None]
    c.taper = np.ones(c.output, dtype=dtype)
    c.carriers = c.carriers.astype("uint64" if dtype.startswith("uint") else "int32")
    agrees(c)


@pytest.mark.parametrize("style", ["endian", "fortran", "strided", "readonly"])
def test_all_array_storage_classes_include_calibration_fields(style: str) -> None:
    c = case(n=5)
    for name in ("images", "phases", "carriers", "gains", "covariance", "taper", "transfers"):
        setattr(c, name, representation(getattr(c, name), style))
    truth = observe(c)
    args = c.arguments()
    records = []
    for record in args["order_otfs"]:
        records.append(
            replace(
                record,
                **{
                    name: representation(getattr(record, name), style)
                    for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
                },
            )
        )
    args["order_otfs"] = records
    args["output_shape_yx"] = [np.int32(c.out[0]), np.uint64(c.out[1])]
    args["regularization"] = np.float32(c.alpha)
    # The converted float32 penalty defines a different represented problem.
    truth = observe(replace(c, alpha=float(np.float32(c.alpha))))
    result = api().reconstruct_volume_weighted(c.images, **args)
    close(result.untapered_volume, truth.x, truth.tolerance)


@pytest.mark.parametrize(
    "field,code",
    [
        ("images", "invalid_volume_reconstruction_images"),
        ("phases_rad", "invalid_volume_reconstruction_phases"),
        ("carriers_bins", "invalid_volume_reconstruction_carriers"),
        ("gains", "invalid_volume_reconstruction_gains"),
        ("apodization", "invalid_volume_reconstruction_apodization"),
        ("exposure_covariance", "invalid_weighted_volume_covariance"),
    ],
)
@pytest.mark.parametrize("form", ["list", "subclass", "masked"])
def test_plain_array_boundary(field: str, code: str, form: str) -> None:
    c = case(n=5)
    args = c.arguments()
    if field == "images":
        library = api()
        with pytest.raises(library.SimreconError) as caught:
            library.reconstruct_volume_weighted(nonplain(c.images, form), **args)
        assert caught.value.code == code
    else:
        rejects(c, code, **{field: nonplain(args[field], form)})


@pytest.mark.parametrize("dtype", ["bool", "complex128", "object", "U3", "datetime64[D]", "V8"])
@pytest.mark.parametrize(
    "field,code",
    [
        ("images", "invalid_volume_reconstruction_dtype"),
        ("phases_rad", "invalid_volume_reconstruction_phases"),
        ("gains", "invalid_volume_reconstruction_gains"),
        ("apodization", "invalid_volume_reconstruction_apodization"),
        ("exposure_covariance", "invalid_weighted_volume_covariance"),
    ],
)
def test_rejected_real_dtype_kinds(field: str, code: str, dtype: str) -> None:
    c = case(n=5)
    args = c.arguments()
    value = c.images if field == "images" else args[field]
    wrong = np.zeros(value.shape, dtype=dtype)
    if field == "images":
        c.images = wrong
        rejects(c, code)
    else:
        rejects(c, code, **{field: wrong})


@pytest.mark.parametrize(
    "field,kind,code",
    [
        ("images", "empty_orientation", "invalid_volume_reconstruction_shape"),
        ("images", "few_phases", "invalid_volume_reconstruction_shape"),
        ("images", "empty_space", "invalid_volume_reconstruction_shape"),
        ("images", "dimension", "invalid_volume_reconstruction_shape"),
        ("phases_rad", "shape", "invalid_volume_reconstruction_phases"),
        ("gains", "shape", "invalid_volume_reconstruction_gains"),
        ("carriers_bins", "shape", "invalid_volume_reconstruction_carriers"),
        ("apodization", "shape", "invalid_volume_reconstruction_apodization"),
        ("exposure_covariance", "shape", "invalid_weighted_volume_covariance"),
    ],
)
def test_distinct_input_shape_decisions(field: str, kind: str, code: str) -> None:
    c = case(n=5)
    args = c.arguments()
    if field == "images":
        c.images = {
            "empty_orientation": c.images[:0],
            "few_phases": c.images[:, :4],
            "empty_space": c.images[..., :0],
            "dimension": c.images[0],
        }[kind]
        rejects(c, code)
    else:
        rejects(c, code, **{field: args[field][0]})


@pytest.mark.parametrize(
    "field,code",
    [
        ("images", "nonfinite_volume_reconstruction_images"),
        ("phases_rad", "nonfinite_volume_reconstruction_phases"),
        ("gains", "invalid_volume_reconstruction_gain_values"),
        ("apodization", "invalid_volume_reconstruction_apodization_values"),
        ("exposure_covariance", "invalid_weighted_volume_covariance"),
    ],
)
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_source_nonfinite_inputs_not_waived_by_zero_taper(
    field: str, code: str, value: float
) -> None:
    c = case(n=5)
    c.taper[:] = 0
    args = c.arguments()
    wrong = (c.images if field == "images" else args[field]).copy()
    wrong.flat[0] = value
    if field == "images":
        c.images = wrong
        rejects(c, code)
    else:
        rejects(c, code, **{field: wrong})


@pytest.mark.parametrize(
    "field,code",
    [
        ("images", "nonfinite_volume_reconstruction_images"),
        ("phases_rad", "nonfinite_volume_reconstruction_phases"),
        ("gains", "invalid_volume_reconstruction_gain_values"),
        ("apodization", "invalid_volume_reconstruction_apodization_values"),
        ("exposure_covariance", "invalid_weighted_volume_covariance"),
    ],
)
def test_converted_nonfinite_and_finite_underflow_classes(field: str, code: str) -> None:
    c = case(n=5)
    value = c.images if field == "images" else c.arguments()[field]
    # longdouble may equal float64 on some platforms. Do not invent an overflow there.
    if np.finfo(np.longdouble).max > np.finfo(float).max:
        wrong = value.astype(np.longdouble)
        wrong.flat[0] = np.longdouble(np.finfo(float).max) * np.longdouble(2)
        if field == "images":
            bad = replace(c, images=wrong)
            rejects(bad, code)
        else:
            rejects(c, code, **{field: wrong})
    # Conversion underflow defines a new stored value, including zero covariance
    # eigenvalues and zero gains. These have their own rejection decisions.
    tiny = np.nextafter(np.longdouble(0), np.longdouble(1))
    converted_zero = float(tiny) == 0
    small = value.astype(np.longdouble)
    small.flat[0] = tiny
    if field == "images":
        result = run(replace(c, images=small))
        assert np.all(np.isfinite(result.untapered_volume))
    elif field == "gains" and converted_zero:
        rejects(c, "invalid_volume_reconstruction_gain_values", gains=small)
    elif field == "exposure_covariance" and converted_zero:
        small = np.eye(5, dtype=np.longdouble)[None]
        small[0, 0, 0] = tiny
        rejects(c, "singular_weighted_volume_covariance", exposure_covariance=small)
    elif field in {"phases_rad", "apodization"}:
        result = run(c, **{field: small})
        assert np.all(np.isfinite(result.untapered_volume))
    else:
        # This platform has no wider-range conversion-underflow example.
        result = run(c)
        assert np.all(np.isfinite(result.untapered_volume))


@pytest.mark.parametrize(
    "wrong",
    [
        np.array([[0.0, 0.0]]),
        np.array([[False, False]]),
        np.zeros((1, 3), dtype=int),
    ],
)
def test_exact_carrier_type_and_shape(wrong: np.ndarray) -> None:
    rejects(case(n=5), "invalid_volume_reconstruction_carriers", carriers_bins=wrong)


@pytest.mark.parametrize("wrong", [0, -1, np.nan, np.inf])
def test_gain_positive_converted_value(wrong: float) -> None:
    rejects(
        case(n=5), "invalid_volume_reconstruction_gain_values", gains=np.array([wrong], dtype=float)
    )


@pytest.mark.parametrize("wrong", [True, 1j, [0.2], np.array(0.2), -0.1, np.nan, np.inf])
def test_regularization_scalar_finite_nonnegative_boundary(wrong: Any) -> None:
    rejects(case(n=5), "invalid_volume_reconstruction_regularization", regularization=wrong)


@pytest.mark.parametrize(
    "wrong",
    [
        (True, 3),
        (1.0, 3),
        (0, 3),
        (-1, 3),
        (1, 3, 4),
        np.array([1, 3]),
        (1, int(np.iinfo(np.intp).max) + 1),
    ],
)
def test_output_shape_container_integer_index_boundary(wrong: Any) -> None:
    rejects(case(n=5), "invalid_volume_reconstruction_output_shape", output_shape_yx=wrong)


def test_insufficient_signed_window_even_with_zero_transfer_and_taper() -> None:
    c = case(carriers=((0, -1),), n=5)
    c.transfers[:] = 0
    c.taper = np.zeros((1, 1, 6))
    rejects(c, "invalid_volume_reconstruction_output_shape", output_shape_yx=(1, 6))
    c = case(n=5)
    huge = np.array([[0, np.iinfo(np.uint64).max]], dtype=np.uint64)
    rejects(c, "invalid_volume_reconstruction_output_shape", carriers_bins=huge)


@pytest.mark.parametrize("wrong", [-0.01, 1.01])
def test_taper_closed_amplitude_interval(wrong: float) -> None:
    c = case(n=5)
    taper = c.taper.copy()
    taper.flat[0] = wrong
    rejects(c, "invalid_volume_reconstruction_apodization_values", apodization=taper)


@pytest.mark.parametrize(
    "mode", ["asymmetric", "zero", "negative", "singular", "equal_cutoff", "below_cutoff"]
)
def test_covariance_strict_numerical_positive_spectrum_boundary(mode: str) -> None:
    c = case(n=5)
    covariance = np.eye(5)
    if mode == "asymmetric":
        covariance[0, 1] = np.nextafter(0.0, 1.0)
    elif mode == "zero":
        covariance[:] = 0
    elif mode == "negative":
        covariance[0, 0] = -1
    elif mode == "singular":
        covariance[0, 0] = 0
    else:
        covariance[0, 0] = 5 * EPS * (1 if mode == "equal_cutoff" else 0.5)
    rejects(c, "singular_weighted_volume_covariance", exposure_covariance=covariance[None])
    # Above the boundary is valid; no arbitrary variance floor may reject it.
    covariance = np.eye(5)
    covariance[0, 0] = 10 * EPS
    positive = run(c, exposure_covariance=covariance[None])
    assert np.all(np.isfinite(positive.untapered_volume))


@pytest.mark.parametrize("factor", [2.0**-500, 2.0**500])
def test_covariance_scale_has_no_absolute_floor_or_ceiling(factor: float) -> None:
    c = case(n=5)
    changed = replace(c, covariance=c.covariance * factor, alpha=c.alpha / factor)
    first = run(c)
    second = run(changed)
    budget = observe(c).tolerance * 4
    close(second.untapered_volume, first.untapered_volume, budget)


@pytest.mark.parametrize(
    "field,mode",
    [
        ("values", "dtype"),
        ("values", "shape"),
        ("values", "nonfinite"),
        ("values", "subclass"),
        ("fz_per_um", "dtype"),
        ("fx_per_um", "nonfinite"),
        ("fx_per_um", "bins"),
        ("fx_per_um", "shape"),
    ],
)
def test_direct_calibration_array_validation(field: str, mode: str) -> None:
    c = case(n=5)
    c.taper[:] = 0
    args = c.arguments()
    record = args["order_otfs"][0]
    value = getattr(record, field).copy()
    if mode == "dtype":
        value = value.astype(np.complex64 if field == "values" else np.float32)
    elif mode == "shape":
        value = value[..., :0]
    elif mode == "nonfinite":
        value.flat[0] = np.nan
    elif mode == "subclass":
        value = value.view(ArraySubclass)
    else:
        value.flat[0] += 0.01
    rejects(
        c, "invalid_volume_reconstruction_otfs", order_otfs=(replace(record, **{field: value}),)
    )


@pytest.mark.parametrize(
    "mode", ["container", "count", "type", "spacing", "origin", "source", "spacing_disagreement"]
)
def test_calibration_record_metadata_and_container_validation(mode: str) -> None:
    c = case(carriers=((0, 0), (0, 0)), n=5)
    args = c.arguments()
    records = list(args["order_otfs"])
    first = records[0]
    if mode == "container":
        wrong: Any = iter(records)
    elif mode == "count":
        wrong = records[:1]
    elif mode == "type":
        wrong = [object(), records[1]]
    else:
        # Rebuild through the complete public positional record boundary.
        spacing: Any = c.spacing
        origin: Any = (0, 0, 0)
        source: Any = "valid metadata"
        if mode == "spacing":
            spacing = (True, 0.4, 0.25)
        elif mode == "origin":
            origin = (0, 0, c.detector[2])
        elif mode == "source":
            source = "   "
        else:
            spacing = tuple(d * 2 for d in c.spacing)
        frequencies = [first.fz_per_um.copy(), first.fy_per_um.copy(), first.fx_per_um.copy()]
        if mode == "spacing_disagreement":
            frequencies = [f / 2 for f in frequencies]
        records[0] = type(first)(first.values, *frequencies, spacing, origin, source)
        wrong = records
    rejects(c, "invalid_volume_reconstruction_otfs", order_otfs=wrong)


def test_grid_underflow_is_distinct_from_valid_extreme_spacing() -> None:
    c = case(detector=(1, 1, 1), carriers=((0, 1),), n=5)
    c.spacing = (1.0, 1.0, np.nextafter(0.0, 1.0))
    rejects(c, "unrepresentable_volume_reconstruction_grid")
    c = case(detector=(1, 1, 3), n=5)
    c.spacing = (1.0, 1.0, 1e308)
    result = run(c)
    # Field length overflows float64, but nonzero subnormal frequencies exist.
    assert result.fx_per_um[0] < 0 < result.fx_per_um[2]
    assert result.fx_per_um[1] == 0
    c.spacing = (1.0, 1.0, np.nextafter(0.0, 1.0))
    # The native calibration grid is already nonfinite: reject its OTF record.
    # The fixture deliberately constructs the invalid infinity without warnings.
    args = c.arguments()
    rejects(c, "invalid_volume_reconstruction_otfs", order_otfs=args["order_otfs"])


def input_arrays(c: Case, args: dict[str, Any]) -> list[np.ndarray]:
    result = [c.images, c.phases, c.carriers, c.gains, c.covariance, c.taper]
    for record in args["order_otfs"]:
        result.extend([record.values, record.fz_per_um, record.fy_per_um, record.fx_per_um])
    return result


@pytest.mark.parametrize("invalid", [False, True])
def test_caller_contents_layout_error_mode_and_warning_filters_preserved(invalid: bool) -> None:
    c = case(n=5)
    c.images = representation(c.images, "strided")
    c.phases.setflags(write=False)
    args = c.arguments()
    if invalid:
        args["exposure_covariance"] = np.zeros_like(c.covariance)
    originals = [(a, a.tobytes(), a.strides, a.flags.writeable) for a in input_arrays(c, args)]
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        modes, filters = np.geterr().copy(), list(warnings.filters)
        if invalid:
            with pytest.raises(api().SimreconError) as error:
                api().reconstruct_volume_weighted(c.images, **args)
            assert error.value.code == "singular_weighted_volume_covariance"
        else:
            api().reconstruct_volume_weighted(c.images, **args)
        assert np.geterr() == modes
        assert warnings.filters == filters
        assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
    for a, contents, strides, writable in originals:
        assert a.tobytes() == contents
        assert a.strides == strides and a.flags.writeable == writable


def test_snapshots_precede_phase_processing_when_public_cosine_is_used(monkeypatch: Any) -> None:
    c = case(n=5)
    truth = observe(c)
    args = c.arguments()
    caller_arrays = input_arrays(c, args)
    original = np.cos
    calls = []

    def mutate_after_snapshot(value: Any, *positional: Any, **keywords: Any) -> Any:
        result = original(value, *positional, **keywords)
        if not calls:
            calls.append(True)
            for a in caller_arrays:
                a.flat[0] = 0
        return result

    monkeypatch.setattr(np, "cos", mutate_after_snapshot)
    result = api().reconstruct_volume_weighted(c.images, **args)
    close(result.untapered_volume, truth.x, truth.tolerance)
    # No fixed binding/call-count claim: a valid direct import may bypass this probe.


@pytest.mark.parametrize(
    "failure",
    [
        "arithmetic_warning",
        "floating",
        "overflow",
        "nonfinite",
        "memory",
        "unrelated",
        "user_warning",
    ],
)
def test_public_transform_failures_if_fft_backend_used(monkeypatch: Any, failure: str) -> None:
    c = case(n=5)
    truth = observe(c)
    args = c.arguments()
    calls = []
    originals = {name: getattr(np.fft, name) for name in ("fftn", "ifftn")}

    def wrapped(name: str) -> Any:
        def transform(*values: Any, **keywords: Any) -> Any:
            calls.append(name)
            if failure == "arithmetic_warning":
                warnings.warn("RA06 controlled arithmetic", RuntimeWarning, stacklevel=2)
            elif failure == "floating":
                raise FloatingPointError("RA06 controlled transform")
            elif failure == "overflow":
                raise OverflowError("RA06 controlled transform")
            elif failure == "memory":
                raise MemoryError("RA06 controlled allocation")
            elif failure == "unrelated":
                raise RuntimeError("RA06 controlled unrelated transform")
            elif failure == "user_warning":
                warnings.warn("RA06 unrelated category", UserWarning, stacklevel=2)
            result = originals[name](*values, **keywords)
            if failure == "nonfinite":
                result = np.full_like(result, np.nan)
            return result

        return transform

    for name in originals:
        monkeypatch.setattr(np.fft, name, wrapped(name))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if failure == "arithmetic_warning":
            warnings.simplefilter("ignore", RuntimeWarning)
        modes, filters = np.geterr().copy(), list(warnings.filters)
        try:
            result = api().reconstruct_volume_weighted(c.images, **args)
        except (MemoryError, RuntimeError) as error:
            assert calls and failure in {"memory", "unrelated"}
            assert type(error) is (MemoryError if failure == "memory" else RuntimeError)
        except api().SimreconError as error:
            assert calls and failure in {"arithmetic_warning", "floating", "overflow", "nonfinite"}
            assert error.code == "volume_reconstruction_transform_failure"
        else:
            # Equivalent finite direct sums are an explicitly legitimate backend.
            assert not calls or failure == "user_warning"
            close(result.untapered_volume, truth.x, truth.tolerance)
        assert np.geterr() == modes and warnings.filters == filters
        assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
        if calls and failure == "user_warning":
            assert any(w.category is UserWarning for w in caught)


@pytest.mark.parametrize("failure", ["linalg", "memory", "unrelated", "nonfinite"])
def test_numerical_factor_failures_if_public_numpy_backend_used(
    monkeypatch: Any, failure: str
) -> None:
    c = case(n=5)
    truth = observe(c)
    args = c.arguments()
    calls = []
    names = ("svd", "eigh", "eigvalsh", "cholesky", "solve", "lstsq")

    def wrapped(name: str, original: Any) -> Any:
        def factor(*values: Any, **keywords: Any) -> Any:
            calls.append(name)
            if failure == "linalg":
                raise np.linalg.LinAlgError("RA06 controlled factor")
            if failure == "memory":
                raise MemoryError("RA06 controlled allocation")
            if failure == "unrelated":
                raise RuntimeError("RA06 controlled unrelated factor")
            output = original(*values, **keywords)
            if isinstance(output, tuple):
                return tuple(
                    np.full_like(v, np.nan) if isinstance(v, np.ndarray) else v for v in output
                )
            return np.full_like(output, np.nan)

        return factor

    for name in names:
        monkeypatch.setattr(np.linalg, name, wrapped(name, getattr(np.linalg, name)))
    try:
        result = api().reconstruct_volume_weighted(c.images, **args)
    except (MemoryError, RuntimeError) as error:
        assert calls and failure in {"memory", "unrelated"}
        assert type(error) is (MemoryError if failure == "memory" else RuntimeError)
    except api().SimreconError as error:
        assert calls and failure in {"linalg", "nonfinite"}
        # Covariance eigenspectrum is a specified validation stage; unusable
        # covariance eigenvalues reject as singular. Phase solver errors inherit.
        permitted = {"weighted_volume_solver_failure", "volume_phase_solver_failure"}
        if failure == "nonfinite":
            permitted.add("singular_weighted_volume_covariance")
        assert error.code in permitted
    else:
        assert not calls
        close(result.untapered_volume, truth.x, truth.tolerance)


def test_nonfinite_required_diagnostics_not_rescued_by_zero_taper() -> None:
    c = case(detector=(1, 1, 1), n=5)
    c.images[:] = np.finfo(float).max
    c.transfers[:] = 0
    c.taper[:] = 0
    # Raw residual-square diagnostic is unrepresentable even though x is zero.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rejects(c, "unrepresentable_weighted_volume_reconstruction")
        assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]


def test_moderate_mandatory_success_zero_signed_data_and_safe_large_transform() -> None:
    c = case(detector=(1, 1, 3), n=5)
    prior = observe(c)
    assert np.linalg.cond(design(c.phases)[0] / np.array([1, 2, -2, 2, -2])) <= 10
    assert np.linalg.cond(c.covariance[0]) <= 100
    assert max(c.images.size, np.prod(c.output)) <= 256
    assert np.all((prior.singular > 1 / 16) & (prior.singular < 16))
    agrees(c)
    c.images[:] = 0
    result = run(c)
    for name in (
        "volume",
        "spectrum",
        "untapered_volume",
        "untapered_spectrum",
        "predicted_images",
        "residual_images",
        "separated_coordinates",
    ):
        assert np.count_nonzero(getattr(result, name)) == 0
    assert result.data_objective == result.penalty_objective == 0
    # Raw transform sums can overflow; normalized constant answer and residuals
    # are representable after whitening by a large covariance.
    c = case(detector=(1, 1, 3), n=5, alpha=0)
    c.transfers[:] = 0
    c.transfers[:, 0] = 1
    c.gains[:] = 1
    c.images[:] = np.finfo(float).max / 2
    c.covariance = np.eye(5)[None] * (np.finfo(float).max / 2)
    # This lies outside mandatory accuracy. Check a finite, correctly scaled answer.
    result = run(c)
    close(result.untapered_volume / c.images.flat[0], 1, 8192 * EPS * 15)


def test_reproducible_finite_noise_ensemble_covariance_and_residual_spectra() -> None:
    c = case(detector=(1, 1, 3), n=5)
    c.images[:] = 0
    prior = observe(c)
    m, n, p = 3, 5, 3
    # A finite symmetric ensemble exactly reproduces the declared covariance.
    # It proves linear propagation for these samples, not an instrument noise model.
    raw_covariance = np.kron(c.covariance[0], np.eye(m))
    root = np.linalg.cholesky(raw_covariance)
    ensemble = np.concatenate((root, -root), axis=1).T * np.sqrt(n * m)
    inverse = np.linalg.solve(prior.normal, prior.a.T @ np.linalg.inv(raw_covariance) / m)
    expected_x_covariance = inverse @ raw_covariance @ inverse.T
    residual_map = np.eye(n * m) - prior.a @ inverse
    expected_residual_covariance = residual_map @ raw_covariance @ residual_map.T
    fr, fi = fourier(c.output)
    transform = (np.asarray(fr, float) - 1j * np.asarray(fi, float)) / p
    expected_noise_power = np.real(np.diag(transform @ expected_x_covariance @ transform.conj().T))
    detector_fr, detector_fi = fourier(c.detector)
    detector_transform = (np.asarray(detector_fr, float) - 1j * np.asarray(detector_fi, float)) / m
    expected_residual_power = np.zeros(m)
    for exposure in range(n):
        block = expected_residual_covariance[
            exposure * m : (exposure + 1) * m, exposure * m : (exposure + 1) * m
        ]
        expected_residual_power += (
            np.real(np.diag(detector_transform @ block @ detector_transform.conj().T)) / n
        )
    outputs, residual_power, separated_noise = [], [], []
    allowance = prior.tolerance * 4096
    for sample in ensemble:
        result = run(replace(c, images=sample.reshape(c.images.shape)))
        outputs.append(result.untapered_volume.ravel())
        separated_noise.append(
            (result.separated_coordinates[0].reshape(5, m) @ detector_transform.T).ravel()
        )
        transformed = result.residual_images.reshape(n, m) @ detector_transform.T
        residual_power.append(np.mean(np.abs(transformed) ** 2, axis=0))
    outputs_array = np.asarray(outputs)
    measured_covariance = outputs_array.T @ outputs_array / len(ensemble)
    measured_spectra = np.mean(np.abs(outputs_array @ transform.T) ** 2, axis=0)
    close(measured_covariance, expected_x_covariance, allowance)
    close(measured_spectra, expected_noise_power, allowance)
    close(np.mean(residual_power, axis=0), expected_residual_power, allowance)
    separated = np.asarray(separated_noise)
    expected_hermitian = np.kron(prior.covariance[0], np.eye(m) / m)
    reflection = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]])
    expected_pseudo = np.kron(prior.covariance[0], reflection / m)
    close(separated.T @ separated.conj() / len(ensemble), expected_hermitian, allowance)
    close(separated.T @ separated / len(ensemble), expected_pseudo, allowance)
    # A real noise field couples opposite Fourier coefficients deterministically.
    fourier_samples = outputs_array @ transform.T
    close(fourier_samples[:, 0], np.conj(fourier_samples[:, 2]), allowance)


@pytest.mark.parametrize(
    ("detector", "carriers", "n"),
    [
        ((1, 1, 3), ((0, 0),), 7),
        ((2, 2, 2), ((0, 1),), 5),
        ((3, 1, 2), ((1, -1),), 5),
        ((1, 2, 3), ((0, 1), (0, -1)), 5),
        ((1, 1, 3), ((0, 0), (0, 0)), 7),
    ],
)
def test_independent_oracle_catalog_before_additive_api(
    detector: tuple[int, int, int],
    carriers: tuple[tuple[int, int], ...],
    n: int,
) -> None:
    c = case(detector, carriers, n)
    truth = observe(c)
    assert np.array_equal(c.covariance, np.swapaxes(c.covariance, -1, -2))
    assert np.linalg.cond(design(c.phases)[0]) < 10
    assert np.linalg.cond(c.covariance[0]) < 100
    assert np.all(np.linalg.eigvalsh(truth.normal) > 0)
    close(truth.normal @ truth.x.ravel(), truth.rhs, 128 * EPS * max(c.output))
    assert abs(truth.data_objective - truth.separated_objective - truth.constant) < 128 * EPS
    assert truth.constant > 0.01 if n > 5 else abs(truth.constant) < 1e-50
    assert 0 < truth.tolerance < 1e-5
    # All nonzero singular values are far from the numerical rank threshold.
    tau = EPS * max(c.images.size, np.prod(c.output)) * truth.singular[0]
    positive = truth.singular[truth.singular > tau]
    assert np.min(positive) > 1000 * tau
    discarded = truth.singular[truth.singular <= tau]
    assert np.all(discarded < tau / 1000)


def test_independent_huge_phase_and_matched_metric_controls_before_api() -> None:
    c = case(n=7)
    c.phases = np.array([[1e308, -1e308, 0.12, 0.91, 2.07, 3.16, 4.51]])
    assert np.linalg.cond(design(c.phases)[0]) < 10
    observe(c)
    c = matched_case(0.6)
    truth = observe(c)
    close(truth.covariance[0], np.diag([0.6, 0.3, 0.3, 0.3, 0.3]), 128 * EPS)
    # The matched white diagonal metric has the correct real-coordinate Gram.
    # This proof uses the observer's map and an independently known convolution.
    source_information = (c.gains[0] ** 2) * (0.7**2 + 2 * 0.4**2 + 2 * 0.3**2) / 0.6
    expected = (source_information + c.alpha) / 3 * np.eye(3)
    close(truth.normal, expected, 1024 * EPS)


def test_original_complex_nyquist_convention_is_preserved() -> None:
    import simrecon

    c = case(detector=(1, 1, 4), n=5, alpha=0)
    c.images[:] = [1.0, -1.0, 1.0, -1.0]
    c.gains[:] = 1
    c.transfers[:] = 0
    c.transfers[0, 0, 0, 0, 0] = 1
    c.out = (1, 8)
    c.taper = np.ones(c.output)
    args = c.arguments()
    args.pop("exposure_covariance")
    result = simrecon.reconstruct_volume(c.images, **args)
    expected = np.zeros(c.output, dtype=complex)
    expected[0, 0, 2] = 1  # Canonical output mode -2, with no positive copy.
    close(result.spectrum, expected, 8192 * EPS * 20)
    close(result.volume, synthesize(expected), 8192 * EPS * 160)
    assert np.max(np.abs(result.volume.imag)) > 0.9


def test_weighted_real_even_lift_has_real_minimum_norm_multiplicity() -> None:
    c = case(detector=(1, 1, 4), n=5, alpha=0)
    c.images[:] = [1.0, -1.0, 1.0, -1.0]
    c.gains[:] = 1
    c.covariance = np.eye(5)[None]
    c.transfers[:] = 0
    c.transfers[0, 0, 0, 0, 0] = 1
    c.out = (1, 8)
    c.taper = np.ones(c.output)
    expected_spectrum = np.zeros(c.output, dtype=complex)
    expected_spectrum[0, 0, 2] = expected_spectrum[0, 0, 6] = 1
    expected = synthesize(expected_spectrum)
    result = run(c)
    close(result.untapered_volume, np.real(expected), 8192 * EPS * 20)
    close(result.untapered_spectrum, expected_spectrum, 8192 * EPS * 20)
    close(result.predicted_images, c.images, 8192 * EPS * 20)
    assert result.information_rank == 1
    assert result.unknown_count == 8


def test_pure_imaginary_dc_prediction_is_valid_but_unobserved() -> None:
    c = case(detector=(1, 1, 1), n=5, alpha=0)
    c.transfers[:] = 0
    c.transfers[:, 0] = 0.75j
    result = run(c)
    assert result.information_rank == 0
    assert np.count_nonzero(result.untapered_volume) == 0
    assert np.count_nonzero(result.predicted_images) == 0
    close(result.residual_images, c.images, 0)
    assert result.data_objective > 0


@pytest.mark.parametrize("alpha", [0.0, 1.0])
def test_full_rank_unregularized_and_positive_ridge_limits(alpha: float) -> None:
    c = case(n=7, alpha=alpha)
    result, truth = agrees(c)
    assert result.information_rank == result.unknown_count == 3
    if alpha == 0:
        assert result.penalty_objective == 0
    else:
        close(result.penalty_objective, np.sum(truth.x**2) / 3, truth.objective_tolerance)


def test_accepted_metadata_alternatives_do_not_apply_origin_twice() -> None:
    c = case(carriers=((0, 0), (0, 0)), n=5)
    truth = observe(c)
    args = c.arguments()
    records = []
    for r, record in enumerate(args["order_otfs"]):
        spacing = [np.float64(v) for v in c.spacing]
        origin = [np.int32(0), np.uint16(0), np.int64(r)]
        records.append(
            type(record)(
                record.values,
                record.fz_per_um,
                record.fy_per_um,
                record.fx_per_um,
                spacing,
                origin,
                f" opaque unrelated metadata {r} ",
            )
        )
    result = api().reconstruct_volume_weighted(c.images, **(args | {"order_otfs": records}))
    close(result.untapered_volume, truth.x, truth.tolerance)


def test_white_raw_ridge_beta_and_denominator_penalty_conversion() -> None:
    c = matched_case()
    c.phases = (np.arange(5) * (2 * np.pi / 5))[None]
    sigma_squared = 0.8
    c.covariance = np.eye(5)[None] * sigma_squared
    truth = observe(c)
    raw = replace(c, covariance=np.eye(5)[None], alpha=c.alpha * sigma_squared)
    raw_truth = observe(raw)
    close(truth.x, raw_truth.x, 1024 * EPS)
    # beta=alpha*sigma_squared, lambda_den=beta/N. Stored phase perturbations
    # make the diagonal formula approximate here; derive an inverse perturbation
    # allowance before either public output, rather than assert exact orthogonality.
    k = design(c.phases)[0]
    gram_error = np.linalg.norm(k.T @ k - np.diag([5, 10, 10, 10, 10]), 2)
    allowance = truth.tolerance + 128 * gram_error * max(1.0, np.linalg.norm(truth.x))
    result = run(c)
    close(result.untapered_volume, truth.x, truth.tolerance)
    args = c.arguments()
    args.pop("exposure_covariance")
    args["regularization"] = c.alpha * sigma_squared / 5
    original = api().reconstruct_volume(c.images, **args)
    close(result.untapered_spectrum, original.spectrum, allowance)


def test_valid_weak_phase_design_has_no_extra_conditioning_cap() -> None:
    c = case(detector=(1, 1, 1), n=5)
    c.phases = np.array([[0.0, 0.01, 0.02, 0.03, 0.04]])
    c.images[:] = 0
    h = design(c.phases)[0] / np.array([1, 2, -2, 2, -2])
    singular = np.linalg.svd(h, compute_uv=False)
    assert singular[0] / singular[-1] > 1e6
    assert singular[-1] > 1000 * EPS * 5 * singular[0]
    result = run(c)
    assert np.count_nonzero(result.untapered_volume) == 0
    assert np.all(np.isfinite(result.separated_covariance))
    assert np.max(np.abs(result.separated_covariance)) > 1e10


def test_covariance_symmetry_is_on_converted_not_source_values() -> None:
    c = case(n=5)
    covariance = np.eye(5, dtype=np.longdouble)[None]
    covariance[0, 0, 1] = covariance[0, 1, 0] = np.longdouble(0.125)
    if np.finfo(np.longdouble).eps < EPS:
        covariance[0, 0, 1] = np.nextafter(covariance[0, 0, 1], np.longdouble(1))
        assert covariance[0, 0, 1] != covariance[0, 1, 0]
    converted = np.asarray(covariance, dtype=float)
    assert np.array_equal(converted, converted.swapaxes(-1, -2))
    truth = observe(replace(c, covariance=converted))
    result = run(c, exposure_covariance=covariance)
    close(result.untapered_volume, truth.x, truth.tolerance)


@pytest.mark.parametrize("alpha", [0.0, 0.2])
def test_dc_scalar_gain_oracle_matches_independent_real_map_before_api(alpha: float) -> None:
    c = case(n=5, alpha=alpha)
    c.transfers[:] = 0
    c.transfers[0, 0, 0, 0, 1] = 0.75
    c.images[:] = 1.4
    assert c.gains[0] != 1  # Keep the nonunit-gain validation gap observable.
    with localcontext() as context:
        context.prec = 80
        _, a = real_map(c)
        n, m, p = c.phases.shape[1], int(np.prod(c.detector)), int(np.prod(c.output))
        # Project the full independently assembled map onto a constant real source.
        source = matrix(np.ones(p))
        prediction = (a @ source).reshape(n, m)
        y = matrix(c.images[0].reshape(n, m))
        sigma = matrix(c.covariance[0])
        weighted_prediction = solve(sigma, prediction)
        curvature = np.sum(prediction * weighted_prediction) / Decimal(m)
        slope = np.sum(y * weighted_prediction) / Decimal(m)
        source_gram = np.sum(source * source) / Decimal(p)
        independent = slope / (curvature + dec(alpha) * source_gram)
        # Pixel-difference directions are null; the constant representative has
        # the least Euclidean norm for this one-dimensional observation map.
        null = matrix([1, -1, 0])
        assert np.max(np.abs(a @ null)) < Decimal("1e-70")
        assert source_gram == 1
    # Observer and scalar-helper roundoff, fixed before either estimate is compared.
    budget = 512 * EPS * n * np.linalg.cond(c.covariance[0]) * max(1, abs(float(independent)))
    weight = float(np.sum(np.linalg.solve(c.covariance[0], np.ones(n))))
    close(_observable_dc_amplitude(c, weight), float(independent), budget)
