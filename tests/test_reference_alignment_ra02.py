"""Tiny public-boundary numerical controls for RA02; see A/REPORT.md mapping."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from reference_alignment_ra02_fixture import (
    EPS,
    asymmetric_volume_control,
    bands,
    call_volume,
    convolution_matrix,
    coordinates,
    decimal_solve,
    finite_sum,
    frequency,
    fusion_budget,
    least_squares,
    matched_control,
    modes,
    observe_volume,
    oracle_2d,
    otf_record,
    phase_matrix,
    real_basis,
)
from simrecon import (
    SimreconError,
    prepare_volume_order_otfs,
    reconstruct,
    separate_phases,
    separate_volume_phases,
)


def close(actual: Any, expected: Any, bound: float) -> None:
    assert 0 < bound < np.inf
    error = float(np.max(np.abs(np.asarray(actual) - expected)))
    assert error <= bound, f"absolute error {error:.17g} exceeds prederived bound {bound:.17g}"


def assert_observation(o: dict[str, Any]) -> None:
    b = o["budget"]
    close(
        o["actual_spectrum"], o["expected_spectrum"], b["spectrum_bound"] + b["observer_spectrum"]
    )
    close(o["actual_spatial"], o["expected_spatial"], b["spatial_bound"] + b["observer_spatial"])


def test_2d_signed_unequal_phase_projection_and_backward_certificate() -> None:
    phi = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
    k = phase_matrix(phi, 1)
    known = np.array([[[1.0, -2.0, 0.5]], [[0.25, -0.5, 0.0]], [[-0.75, 0.125, 0.5]]])
    model = np.einsum("pk,kyx->pyx", k, known)
    for data in (model, model + 0.1 * np.arange(phi.size)[:, None, None] ** 2):
        expected = least_squares(k, data)
        s = np.linalg.svd(k, compute_uv=False)
        eta, a, minimum = 128 * phi.size * EPS, s[0], s[-1]
        alpha = eta * a
        assert alpha < minimum and np.linalg.cond(k) < 10
        bnorm = np.linalg.norm(data, axis=0)
        znorm = np.linalg.norm(expected, axis=0)
        residual = data - np.einsum("pk,kyx->pyx", k, expected)
        forward = (eta * bnorm + alpha * znorm) / (minimum - alpha) + alpha * np.linalg.norm(
            residual, axis=0
        ) / (minimum - alpha) ** 2
        observer = 8 * EPS * np.maximum(1, znorm)
        result = coordinates(separate_phases(data, phases_rad=phi), 1)
        assert np.all(np.linalg.norm(result - expected, axis=0) <= forward + observer)
        # E=0, f=K(z_hat-z_star_exact). Rounded observer adds the stated
        # upper bound; unchanged K is full rank. This is sufficient, not a
        # necessary characterization of all possible backward certificates.
        f_upper = (
            np.linalg.norm(np.einsum("pk,kyx->pyx", k, result - expected), axis=0) + a * observer
        )
        assert np.all(f_upper < eta * bnorm)
        fitted = np.einsum("pk,kyx->pyx", k, result)
        if data is model:
            close(result, known, float(np.max(forward + observer)))
            close(fitted, data, float(a * np.max(forward + observer)))
        else:
            assert np.linalg.norm(fitted - data) > 0.1
            assert np.max(np.abs(result[0] - np.mean(data, axis=0))) > 0.05


def test_volume_signed_two_harmonics_projection_and_joint_permutation() -> None:
    phi = np.array([-0.4, 0.3, 1.4, 2.3, 3.5, 4.8, 5.9])
    k = phase_matrix(phi, 2)
    assert np.linalg.cond(k) < 10
    z = np.array([2.0, 0.5, -0.75, -0.25, 1.0])[:, None, None, None] * np.array(
        [[[[1.0, -0.5, 0.25]]]]
    )
    model = np.einsum("pk,kzyx->pzyx", k, z)
    permutation = np.array([5, 0, 3, 6, 2, 1, 4])
    for data in (model, model + 0.02 * np.arange(phi.size)[:, None, None, None] ** 3):
        expected = least_squares(k, data)
        bound = 8192 * phi.size * EPS * float(np.max(np.abs(data)))
        observer = 16 * EPS * max(1.0, float(np.max(np.abs(expected))))
        actual = coordinates(separate_volume_phases(data, phases_rad=phi), 2)
        reordered = coordinates(
            separate_volume_phases(data[permutation], phases_rad=phi[permutation]), 2
        )
        close(actual, expected, bound + observer)
        close(reordered, expected, bound + observer)
        fitted = np.einsum("pk,kzyx->pzyx", k, actual)
        if data is model:
            close(actual, z, bound + observer)
            close(fitted, data, 9 * (bound + observer))
        else:
            assert np.linalg.norm(data - fitted) > 0.1
            assert abs(float(actual[0, 0, 0, 0] - np.mean(data[:, 0, 0, 0]))) > 0.05


def test_five_order_complex_fusion_asymmetric_axes_origin_ridge_and_mask() -> None:
    c = asymmetric_volume_control()
    observed = observe_volume(c)
    assert_observation(observed)
    expected = observed["expected_spectrum"]
    assert np.max(np.abs(expected.imag)) > 0.01
    assert np.min(observed["expected_spatial"].real) < 0
    assert observed["actual_spectrum"][0, 1, 2] == 0
    # Frequency origin is centered; spatial origin is zero, axial size fixed.
    for actual_axis, nout, ndet, d in zip(
        observed["axes"], c["mask"].shape, c["images"].shape[2:], c["spacing"], strict=True
    ):
        target = frequency(nout, ndet * d / nout)
        close(actual_axis, target, 16 * EPS * max(1.0, float(np.max(np.abs(target)))))
    # Same valid input with no amplitude mask and no ridge. These are separate
    # choices in the public estimator, not inferred support or power weights.
    c["mask"] = np.ones_like(c["mask"])
    unmasked = observe_volume(c)
    assert_observation(unmasked)
    # Recreate the declared mask: c was deliberately reused for the next call.
    mask = asymmetric_volume_control()["mask"]
    close(
        observed["actual_spectrum"],
        mask * unmasked["actual_spectrum"],
        2 * observed["budget"]["spectrum_bound"],
    )
    c["penalty"] = 0.0
    no_ridge = observe_volume(c)
    assert_observation(no_ridge)
    assert np.max(np.abs(no_ridge["expected_spectrum"] - unmasked["expected_spectrum"])) > 0.01


@pytest.mark.parametrize("kind", ["constant", "point", "zero"])
def test_zero_side_zero_carrier_normalization_and_unequal_gains(kind: str) -> None:
    shape = (3, 2, 5)
    source = np.full(shape, -0.75) if kind == "constant" else np.zeros(shape)
    if kind == "point":
        source[2, 1, 3] = 1.25
    phi = np.array([-0.3, 0.8, 2.0, 3.4, 5.0])
    gains = np.array([0.5, 2.0])
    transfers = np.zeros((3, *shape), dtype=np.complex128)
    transfers[0] = 1
    c = dict(
        images=np.array([np.broadcast_to(g * source, (phi.size, *shape)).copy() for g in gains]),
        phases=np.array([phi, phi]),
        transfers=[transfers, transfers.copy()],
        carriers=np.zeros((2, 2), dtype=np.int64),
        gains=gains,
        penalty=0.0,
        mask=np.ones(shape),
        spacing=(0.7, 0.4, 0.25),
    )
    if kind == "zero":
        actual = call_volume(c)
        assert np.array_equal(actual.spectrum, np.zeros(shape))
        assert np.array_equal(actual.volume, np.zeros(shape))
    else:
        observed = observe_volume(c)
        assert_observation(observed)
        close(observed["actual_spectrum"], finite_sum(source), observed["budget"]["spectrum_bound"])
        close(observed["actual_spatial"], source, observed["budget"]["spatial_bound"])
        if kind == "point":
            assert np.unravel_index(np.argmax(observed["actual_spatial"].real), shape) == (2, 1, 3)
            assert np.max(np.abs(observed["actual_spectrum"].imag)) > 0.02


def test_order_preparation_origin_phase_is_used_once_in_fusion() -> None:
    shape, origin = (3, 2, 5), (1, 1, 2)
    spacing = (0.7, 0.4, 0.25)
    psf = np.zeros(shape)
    psf[origin], psf[2, 0, 3], psf[0, 1, 0] = 4, 2, 1
    coefficients = np.array(
        [[0.5 + 0.125j, -0.25 + 0.25j, 0.75 - 0.125j], [-0.25j, 0.375 + 0.25j, 0.25 - 0.375j]],
        dtype=np.complex128,
    )
    prep_bound = 256 * np.prod(shape) * EPS
    assert np.max(np.abs(coefficients.real)) <= 1
    assert np.max(np.abs(coefficients.imag)) <= 1
    order = prepare_volume_order_otfs(
        psf,
        axial_coefficients=coefficients,
        voxel_size_um=spacing,
        origin_zyx=origin,
        source="RA02 finite kernel",
    )
    independent = []
    for row in (np.ones(shape[0]), *coefficients):
        kernel = psf * row[:, None, None] / np.sum(psf)
        rolled = np.roll(kernel, tuple(-i for i in origin), axis=(0, 1, 2))
        independent.append(finite_sum(rolled) * np.prod(shape))
    close(order.values, np.array(independent), prep_bound)
    c = asymmetric_volume_control()
    c["transfers"] = [order.values, order.values]
    observed = observe_volume(c)
    assert_observation(observed)


def test_even_nyquist_single_selected_complex_lift_and_no_real_projection() -> None:
    phi = np.array([-0.3, 0.8, 2.0, 3.4, 5.0])
    shape, outshape = (2, 1, 4), (2, 1, 8)
    source = np.broadcast_to(np.array([1.0, -1.0, 1.0, -1.0]), shape).copy()
    transfers = np.zeros((3, *shape), dtype=np.complex128)
    transfers[0] = 1
    c = dict(
        images=np.broadcast_to(source, (1, phi.size, *shape)).copy(),
        phases=phi[None],
        transfers=[transfers],
        carriers=np.zeros((1, 2), dtype=np.int64),
        gains=np.ones(1),
        penalty=0.0,
        mask=np.ones(outshape),
        spacing=(0.7, 0.4, 0.25),
    )
    observed = observe_volume(c)
    assert_observation(observed)
    exact = np.zeros(outshape, dtype=np.complex128)
    exact[1, 0, 2] = 1  # qz=0, qx=-2 only; never a duplicated +2 endpoint.
    close(observed["actual_spectrum"], exact, observed["budget"]["spectrum_bound"])
    selected = finite_sum(exact, synthesis=True)
    close(observed["actual_spatial"], selected, observed["budget"]["spatial_bound"])
    assert abs(selected[0, 0, 1].imag + 1) < 16 * EPS
    assert np.max(np.abs(selected.imag)) > 0.9
    # A real cosine interpolation would split the two endpoints and differs.
    real_interpolation = np.cos(2 * np.pi * 2 * np.arange(8) / 8)
    assert np.max(np.abs(selected[0, 0] - real_interpolation)) > 0.9


@pytest.mark.parametrize("penalty", [0.0, 0.5])
def test_rank_deficient_observations_zero_unsupported_modes_and_ridge(penalty: float) -> None:
    shape = (3, 1, 5)
    phi = np.array([-0.3, 0.8, 2.0, 3.4, 5.0])
    source = real_basis(shape, [(0, 0, 1), (1, 0, 0)]) @ np.array([1.0, -0.4, 0.3, 0.5, -0.2])
    source = source.reshape(shape)
    spectrum = finite_sum(source)
    transfer = np.zeros((3, *shape), dtype=np.complex128)
    transfer[0, 1, 0, 2] = 0.75  # DC only: full phase rank, deficient spatial map.
    measured = finite_sum(transfer[0] * spectrum, synthesis=True).real
    c = dict(
        images=np.broadcast_to(measured, (1, phi.size, *shape)).copy(),
        phases=phi[None],
        transfers=[transfer],
        carriers=np.zeros((1, 2), dtype=np.int64),
        gains=np.ones(1),
        penalty=penalty,
        mask=np.ones(shape),
        spacing=(0.7, 0.4, 0.25),
    )
    observed = observe_volume(c)
    assert_observation(observed)
    expected = np.zeros(shape, dtype=np.complex128)
    expected[1, 0, 2] = 0.75**2 / (0.75**2 + penalty)
    close(observed["actual_spectrum"], expected, observed["budget"]["spectrum_bound"])
    unsupported = transfer[0] == 0
    assert np.array_equal(
        observed["actual_spectrum"][unsupported], np.zeros(np.count_nonzero(unsupported))
    )
    assert np.linalg.norm(source - finite_sum(expected, synthesis=True).real) > 0.5


@pytest.mark.parametrize("volume", [False, True], ids=["2d", "five_order_volume"])
def test_matched_real_inverse_forward_adjoint_metric_penalty_and_normal_equations(
    volume: bool,
) -> None:
    c = matched_control(volume=volume)
    a, metric, gram = c["a"], c["metric"], c["gram"]
    theta = c["solution"]
    tol = c["tolerance"]
    if volume:
        public = dict(
            images=c["images"][None],
            phases=c["phases"][None],
            transfers=[c["transfer"]],
            carriers=np.array([[0, 1]]),
            gains=np.array([c["gain"]]),
            penalty=c["penalty"],
            mask=np.ones(c["outshape"]),
            spacing=(0.7, 0.4, 0.25),
        )
        observation = observe_volume(public)
        assert_observation(observation)
        actual, spectrum = observation["actual_spatial"], observation["actual_spectrum"]
    else:
        images, phases = c["images"][None], c["phases"][None]
        h, mask = c["transfer"], np.ones(c["outshape"])
        shifts, gains = np.array([[0, 1]]), np.array([c["gain"]])
        modulation = np.array([0.75])
        expected, expected_image, v = oracle_2d(
            images, phases, h, shifts, modulation, gains, c["penalty"], mask
        )
        budget = fusion_budget(
            images,
            phases,
            v + c["penalty"],
            mask.shape,
            volume=False,
            gains=gains,
            penalty=c["penalty"],
        )
        # Exact integer shift: dx=1/4, Nx=7 -> wave=4/7 cycles/um.
        result = reconstruct(
            images,
            otf=otf_record(h, (0.4, 0.25)),
            phases_rad=phases,
            wavevectors_per_um=np.array([[0.0, 4 / 7]]),
            modulation=modulation,
            brightness=gains,
            regularization=c["penalty"],
            apodization=mask,
        )
        close(result.spectrum, expected, budget["spectrum_bound"] + budget["observer_spectrum"])
        close(result.image, expected_image, budget["spatial_bound"] + budget["observer_spatial"])
        actual, spectrum = result.image, result.spectrum
    basis = c["basis"]
    recovered = decimal_solve(basis.T @ basis, basis.T @ actual.real.ravel())
    close(recovered, theta, tol)
    close(actual.imag, np.zeros_like(actual.imag), tol)
    close(actual.real.ravel(), basis @ theta, tol)
    # Source basis norm is NOT identity: cos/sin contribute 1/2 each.
    close(gram, np.diag([1.0] + [0.5] * (gram.shape[0] - 1)), tol)
    wrong_penalty = decimal_solve(
        a.T @ metric @ a + c["penalty"] * np.eye(gram.shape[0]), a.T @ metric @ c["images"].ravel()
    )
    assert np.linalg.norm(theta - wrong_penalty) > 100 * tol
    residual = a @ recovered - c["images"].ravel()
    normal_residual = a.T @ metric @ residual + c["penalty"] * gram @ recovered
    close(
        normal_residual,
        np.zeros_like(normal_residual),
        tol * max(1.0, float(np.linalg.norm(c["normal"]))),
    )
    probe = np.arange(a.shape[1], dtype=np.float64) / (a.shape[1] + 1)
    data_probe = np.linspace(-0.5, 0.75, a.shape[0])
    lhs = (a @ probe) @ metric @ data_probe
    rhs = probe @ (a.T @ metric @ data_probe)
    close(lhs, rhs, tol)
    # Independently form the adjoint in Fourier band coordinates. It must
    # match the spatial raw-map transpose under the declared phase metric.
    probe_coordinates = least_squares(
        phase_matrix(c["phases"], 2 if volume else 1),
        data_probe.reshape(c["images"].shape),
    )
    probe_transforms = [finite_sum(b) for b in bands(probe_coordinates)]
    spectral_adjoint = np.zeros(a.shape[1])
    for column in range(a.shape[1]):
        source_coefficients = finite_sum(basis[:, column].reshape(c["outshape"]))
        source_lookup = dict(zip(modes(c["outshape"]), source_coefficients.ravel(), strict=True))
        for m, data_band in enumerate(probe_transforms):
            for index, j in zip(np.ndindex(c["shape"]), modes(c["shape"]), strict=True):
                q = tuple(jj - m * cc for jj, cc in zip(j, c["carrier"], strict=True))
                transfer = (
                    c["transfer"][m][index]
                    if volume
                    else c["transfer"][index] * (1 if m == 0 else 0.375)
                )
                predicted = c["gain"] * transfer * source_lookup.get(q, 0)
                spectral_adjoint[column] += (1 if m == 0 else 2) * float(
                    (np.conj(predicted) * data_band[index]).real
                )
    close(spectral_adjoint, a.T @ metric @ data_probe, tol)
    # The independent spatial convolution map also matches the declared
    # Fourier band forward map. Signed-band Parseval and raw phase metric
    # then compare the objectives including actual multiplicities.
    source_spectrum = finite_sum((basis @ probe).reshape(c["outshape"]))
    source_by_mode = dict(zip(modes(c["outshape"]), source_spectrum.ravel(), strict=True))
    band_forward = c["band_map"] @ probe
    for m, band in enumerate(bands(band_forward.reshape((-1, *c["shape"])))):
        measured = finite_sum(band)
        for index, j in zip(np.ndindex(c["shape"]), modes(c["shape"]), strict=True):
            q = tuple(jj - m * cc for jj, cc in zip(j, c["carrier"], strict=True))
            transfer = (
                c["transfer"][m][index]
                if volume
                else c["transfer"][index] * (1 if m == 0 else 0.375)
            )
            expected_band = c["gain"] * transfer * source_by_mode.get(q, 0)
            close(measured[index], expected_band, tol)
    raw_objective = residual @ metric @ residual + c["penalty"] * (recovered @ gram @ recovered)
    raw_residual = residual.reshape(c["images"].shape)
    separated_residual = least_squares(phase_matrix(c["phases"], 2 if volume else 1), raw_residual)
    transforms = [finite_sum(b) for b in bands(separated_residual)]
    transformed_objective = (
        np.sum(np.abs(transforms[0]) ** 2)
        + 2 * sum(float(np.sum(np.abs(d) ** 2)) for d in transforms[1:])
        + c["penalty"] * float(np.sum(np.abs(spectrum) ** 2))
    )
    close(raw_objective, transformed_objective, tol * max(1.0, float(raw_objective)))
    close(
        c["images"].ravel() @ metric @ c["images"].ravel(),
        np.sum(least_squares(phase_matrix(c["phases"], 2 if volume else 1), c["images"])[0] ** 2)
        / np.prod(c["shape"])
        + 2
        * sum(
            float(np.sum(np.abs(b) ** 2)) / np.prod(c["shape"])
            for b in bands(
                least_squares(phase_matrix(c["phases"], 2 if volume else 1), c["images"])
            )[1:]
        ),
        tol,
    )


def test_unequal_phase_white_metric_is_not_diagonal_band_metric() -> None:
    phi = np.array([-0.3, 0.8, 2.0, 3.4, 5.0])
    k = phase_matrix(phi, 2)
    white_gram = k.T @ k / phi.size
    off_diagonal = white_gram - np.diag(np.diag(white_gram))
    assert np.max(np.abs(off_diagonal)) > 0.1
    z = np.array([1.0, 1.0, 0.0, 0.0, 0.0])
    raw = float(np.sum((k @ z) ** 2) / phi.size)
    diagonal = float(z @ np.diag([1.0, 2.0, 2.0, 2.0, 2.0]) @ z)
    assert abs(raw - diagonal) > 0.1
    # Also bound, rather than assert exact identity for, represented regular
    # phases. 64 epsilon per Gram entry covers 5-term products and trig
    # representation at these small angles; this is not a noise model.
    regular = phase_matrix(np.asarray(np.arange(5) * (2 * np.pi / 5), dtype=np.float64), 2)
    close(regular.T @ regular / 5, np.diag([1.0, 2.0, 2.0, 2.0, 2.0]), 64 * EPS)


def test_valid_complex_transfer_can_have_nonreal_dc_raw_map() -> None:
    c = asymmetric_volume_control()
    c["images"] = np.ones_like(c["images"])
    c["transfers"] = [np.zeros_like(e) for e in c["transfers"]]
    for e in c["transfers"]:
        e[0] = 0.5j
    c["carriers"][:] = 0
    c["mask"] = np.ones(c["images"].shape[2:])
    observed = observe_volume(c)
    assert_observation(observed)
    assert np.max(np.abs(observed["actual_spatial"].imag)) > 0.5
    # E0=i/2 sends a real constant to an imaginary constant. Such a supplied
    # algebraic record is valid fusion data, but no real raw forward map.
    assert (0.5j * 1).imag == 0.5


def test_alias_collision_distinguishes_extended_lifts_from_native_real_inverse() -> None:
    native = (1, 5)
    extended = (2, 10)
    detector_x = np.arange(5)
    # q=1 and q=-4 are indistinguishable on native detector samples.
    a = np.exp(2j * np.pi * detector_x / 5)
    b = np.exp(-2j * np.pi * 4 * detector_x / 5)
    close(a, b, 128 * EPS)
    lift = np.zeros(extended, dtype=np.complex128)
    lift[1, 6], lift[1, 1] = 1, -1  # qx=+1 and -4; qy=0.
    extended_signal = finite_sum(lift, synthesis=True)
    assert np.max(np.abs(extended_signal)) > 1.9
    close(extended_signal[0, ::2], np.zeros(native[1]), 128 * EPS)
    # This linear dependence rules out a unique unmatched real inverse. The
    # public selected-lift behavior is separately exercised in the Nyquist test.


def test_positivity_inactive_and_active_tiny_constrained_comparisons() -> None:
    # Independent mathematical comparison only: no new product positivity API.
    a = np.array([[1.0, 0.25], [0.0, 0.75], [0.5, 0.5]])
    normal = a.T @ a + 0.25 * np.eye(2)
    assert np.min(np.linalg.eigvalsh(normal)) > 0.25
    for target, active in ((np.array([1.0, 0.5]), False), (np.array([1.0, -0.75]), True)):
        b = a @ target
        rhs = a.T @ b
        unconstrained = decimal_solve(normal, rhs)
        # Enumerate all four faces of a two-coordinate nonnegative orthant.
        candidates = [np.zeros(2)]
        if np.all(unconstrained >= 0):
            candidates.append(unconstrained)
        for j in range(2):
            value = np.zeros(2)
            value[j] = max(0.0, rhs[j] / normal[j, j])
            candidates.append(value)

        def objective(x: Any, data: Any = b) -> float:
            return float(np.sum((a @ x - data) ** 2) + 0.25 * np.sum(x * x))

        constrained = min(candidates, key=objective)
        gradient = normal @ constrained - rhs
        assert np.all(gradient[constrained == 0] >= -128 * EPS)
        close(gradient[constrained > 0], np.zeros(np.count_nonzero(constrained > 0)), 128 * EPS)
        if active:
            assert np.min(unconstrained) < -0.1
            assert np.linalg.norm(constrained - unconstrained) > 0.1
            assert objective(constrained) > objective(unconstrained) + 0.01
        else:
            close(constrained, unconstrained, 128 * EPS)


def test_deficient_phase_and_insufficient_window_even_with_zero_sides_and_mask() -> None:
    with pytest.raises(SimreconError) as two:
        separate_phases(np.ones((3, 1, 1)), phases_rad=np.zeros(3))
    assert two.value.code == "rank_deficient_phases"
    with pytest.raises(SimreconError) as five:
        separate_volume_phases(np.ones((5, 1, 1, 1)), phases_rad=np.zeros(5))
    assert five.value.code == "rank_deficient_volume_phases"
    c = asymmetric_volume_control()
    c["images"][:] = 0
    c["transfers"] = [np.zeros_like(e) for e in c["transfers"]]
    c["mask"] = np.zeros((3, 5, 9))  # Ny=2 and |cy|=1 requires Ly>=6.
    with pytest.raises(SimreconError) as window:
        call_volume(c)
    assert window.value.code == "invalid_volume_reconstruction_output_shape"


def test_2d_own_estimator_complex_hermitian_otf_integer_signed_carriers_and_extended_window() -> (
    None
):
    shape, outshape = (3, 5), (6, 10)
    spacing = (0.5, 0.25)
    # Positive finite PSF, declared offset: Hermitian full complex OTF.
    kernel = np.zeros(shape)
    kernel[0, 0], kernel[1, 2], kernel[2, 1] = 0.5, 0.25, 0.25
    h = finite_sum(kernel) * np.prod(shape)
    assert abs(h[1, 2] - 1) < 16 * EPS
    phases = np.array([[-0.4, 0.2, 1.4, 2.9, 4.8], [0.1, 1.0, 2.3, 3.5, 5.6]])
    shifts = np.array([[0, 1], [-1, 0]])
    brightness, modulation = np.array([0.75, 1.5]), np.array([0.5, 0.875])
    reps = [(0, 1), (1, 0), (1, -1)]
    source = real_basis(shape, reps) @ np.array([1.0, -0.4, 0.3, -0.2, 0.1, 0.15, -0.25])
    raw = []
    for phi, carrier, gain, mod in zip(phases, shifts, brightness, modulation, strict=True):
        # Direct circular convolution of illuminated real source, evaluated
        # at the detector. No separation/reconstruction output defines truth.
        matrix, _ = convolution_matrix(
            shape, phi, [h, h * mod / 2], tuple(int(v) for v in carrier), float(gain), reps
        )
        raw.append(
            (matrix @ np.array([1.0, -0.4, 0.3, -0.2, 0.1, 0.15, -0.25])).reshape(
                (phi.size, *shape)
            )
        )
    assert np.min(source) > 0
    images = np.array(raw)
    mask = np.ones(outshape)
    mask[1, 2] = 0.25
    penalty = 0.5
    expected, image, v = oracle_2d(images, phases, h, shifts, modulation, brightness, penalty, mask)
    budget = fusion_budget(
        images, phases, v + penalty, outshape, volume=False, gains=brightness, penalty=penalty
    )
    waves = np.array([[0.0, 0.8], [-2 / 3, 0.0]])
    actual = reconstruct(
        images,
        otf=otf_record(h, spacing),
        phases_rad=phases,
        wavevectors_per_um=waves,
        modulation=modulation,
        brightness=brightness,
        regularization=penalty,
        apodization=mask,
    )
    close(actual.spectrum, expected, budget["spectrum_bound"] + budget["observer_spectrum"])
    close(actual.image, image, budget["spatial_bound"] + budget["observer_spatial"])
    assert actual.image.shape == outshape
    assert actual.pixel_size_um == (0.25, 0.125)
    # Accepted finite periodic acquisition may alias on the extended window;
    # this control compares its own estimator, not unrounded specimen truth.
    assert np.max(np.abs(expected[-1])) > 0.001
