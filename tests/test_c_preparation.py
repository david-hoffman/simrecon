"""Blind public-entry CE02 contract tests. Scientific truth is fixture-local."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import simrecon
from c_preparation_fixture import (
    CLUSTERED_TOL,
    REFERENCE,
    close,
    composition,
    direct_volume,
    edge_plane,
    expected,
    options,
    repeated_rows,
    square_rows,
    uniform_rows,
)


@pytest.fixture
def prepare() -> Any:
    # Runtime lookup preserves collection and independent oracle outcomes when absent.
    entry = getattr(simrecon, "prepare_bands", None)
    if entry is None:
        pytest.fail("CE02 feature absence: simrecon.prepare_bands is not installed")
    return entry


def test_public_entry_and_record_exist() -> None:
    assert callable(getattr(simrecon, "prepare_bands", None)), "CE02 feature absence"
    assert getattr(simrecon, "PreparedBands", None) is not None, "CE02 record absence"


def test_independent_edge_radical_and_sine_controls() -> None:
    c = 1 - math.sqrt(0.5)
    close(
        edge_plane(np.arange(0, 16, 2, dtype=float).reshape(2, 4), 1),
        [[7 * c, 2 + 4 * c, 4 + 4 * c, 6 + c], [8 - c, 10 - 4 * c, 12 - 4 * c, 14 - 7 * c]],
    )
    close(edge_plane(np.ones((2, 2)), -1), np.full((2, 2), 0.5))


def test_independent_phase_rows_solve_analytic_synthesis() -> None:
    phases, rows = square_rows()
    coefficients = np.array([7, -3, 2, 5, -4.0])
    for d in range(3):
        phi = phases[d]
        samples = (
            coefficients[0]
            + 2 * coefficients[1] * np.cos(phi)
            + 2 * coefficients[2] * np.sin(phi)
            + 2 * coefficients[3] * np.cos(2 * phi)
            + 2 * coefficients[4] * np.sin(2 * phi)
        ) / 5
        close(rows[d] @ samples, coefficients)
    close(np.sum(rows[:, 0] ** 2, axis=1) / 5, [1.25] * 3)
    close(np.sum(rows[:, 1:3] ** 2, axis=(1, 2)) / 5, [1.25] * 3)
    close(np.sum(rows[:, 3:5] ** 2, axis=(1, 2)) / 5, [2.5] * 3)


def test_independent_finite_sum_matches_displaced_root() -> None:
    volume = np.zeros((3, 2, 4))
    volume[1, 1, 1] = 1
    transformed = direct_volume(volume)
    close(transformed[1, 0, 1], -math.sqrt(3) / 2 + 0.5j)
    close(transformed[1, 0, 2], 0.5 + math.sqrt(3) / 2 * 1j)
    close(transformed[2, 1, 1], -math.sqrt(3) / 2 - 0.5j)


def test_composed_camera_edges_equalization_irregular_phase_profile(prepare: Any) -> None:
    images, kw, rows = composition()
    snapshots = {"images": images.copy()}
    snapshots.update({k: v.copy() for k, v in kw.items() if isinstance(v, np.ndarray)})
    truth = expected(images, rows, **kw)
    result = prepare(images, **kw)
    for field, value in truth.items():
        if field == "sentinel_frames":
            assert result.sentinel_frames == value
        else:
            close(getattr(result, field), value)
    close(result.separation_matrices, rows)
    close(result.noise_variance_factors, np.tile([1.25, 1.25, 2.5], (3, 1)))
    np.testing.assert_array_equal(images, snapshots.pop("images"))
    for key, value in snapshots.items():
        np.testing.assert_array_equal(kw[key], value)
    assert result.sentinel_frames == ((0, 0, 0, 3), (0, 0, 1, 1), (0, 2, 2, 4), (1, 1, 0, 0))


def test_exact_metadata_and_independent_writable_storage(prepare: Any) -> None:
    images, kw, _ = composition()
    result = prepare(images, **kw)
    record = getattr(simrecon, "PreparedBands", None)
    assert record is not None
    assert isinstance(result, record)
    assert result.input_shape == images.shape
    assert result.source_revision == "SVN307"
    assert result.reference_sha256 == REFERENCE
    assert result.phase_policy == "supplied"
    for key in (
        "dxy_um",
        "dz_um",
        "lateral_zoom",
        "axial_zoom",
        "edge_pixels",
        "equalize",
        "equalize_z",
        "equalize_time",
    ):
        assert getattr(result, key) == kw[key]
    fields = {
        "quadratures": ((2, 3, 5, 3, 3, 3), np.dtype("complex128")),
        "noise_variance_factors": ((3, 3), np.dtype("float64")),
        "separation_matrices": ((3, 5, 5), np.dtype("float64")),
        "phase_angles_rad": ((3, 5), np.dtype("float64")),
        "frame_sums": ((2, 3, 5, 3), np.dtype("float64")),
        "equalization_gains": ((2, 3, 5, 3), np.dtype("float64")),
        "background_after": ((3, 4), np.dtype("float64")),
        "slope_after": ((3, 4), np.dtype("float64")),
    }
    arrays = [getattr(result, name) for name in fields]
    inputs = [images] + [v for v in kw.values() if isinstance(v, np.ndarray)]
    for name, (shape, dtype) in fields.items():
        array = getattr(result, name)
        assert array.shape == shape
        assert array.dtype == dtype
        assert array.flags.owndata and array.flags.writeable
        for source in inputs:
            assert not np.shares_memory(array, source)
    for i, array in enumerate(arrays):
        for other in arrays[i + 1 :]:
            assert not np.shares_memory(array, other)
    np.testing.assert_array_equal(result.phase_angles_rad, kw["phases_rad"])
    # Caller mutation of one result must not change a second call's maps.
    result.background_after[:] = -999
    again = prepare(images, **kw)
    assert again.background_after[0, 0] == 2


@pytest.mark.parametrize("impulse", [False, True], ids=["constant", "displaced-unit"])
def test_analytic_alpha_and_forward_roots(prepare: Any, impulse: bool) -> None:
    images = np.full((1, 3, 5, 3, 2, 4), 5 if impulse else 20, dtype=np.int16)
    if impulse:
        images[:, :, :, 1, 1, 1] += 144
    result = prepare(
        images,
        **options(
            background=3,
            flatfield_slope=np.full((2, 4), 4.0),
            exposure_background=np.full((1, 3, 5, 3), 2.0),
            lateral_zoom=2,
            axial_zoom=2,
        ),
    )
    close(result.input_scale, 1 / 576)
    assert result.quadratures.shape == (1, 3, 5, 3, 2, 3)
    if impulse:
        close(result.quadratures[0, :, 0, 1, 0, 1], -5 * math.sqrt(3) / 2 + 2.5j)
        close(result.quadratures[0, :, :, 1, 0, 2], 0.5 + math.sqrt(3) / 2 * 1j)
    else:
        close(result.frame_sums, np.full((1, 3, 5, 3), 5 / 6))
        close(result.quadratures[0, :, 0, 0, 0, 0], [12.5] * 3)
        close(result.quadratures[:, :, 1:, :, :, :-1], 0)


def test_sentinel_camera_state_analytic_and_cross_call_reset(prepare: Any) -> None:
    images = np.full((2, 3, 3, 2, 1, 2), [12, 20], dtype=np.int16)
    images[0, 0, 0, 0, 0] = [10, -1]
    extra = np.full((2, 3, 3, 2), 2.0)
    extra[0, 0, 0, 0] = 1
    kw = options(
        norders=2,
        background=np.array([[3, 7.0]]),
        flatfield_slope=np.array([[2, 4.0]]),
        exposure_background=extra,
    )
    result = prepare(images, **kw)
    close(result.frame_sums[0, 0, 0, 0], 1.5)
    close(result.frame_sums[1, 2, 2, 1], 29 / 12)
    np.testing.assert_array_equal(result.background_after, [[3, 3]])
    np.testing.assert_array_equal(result.slope_after, [[2, 1]])
    assert result.sentinel_frames == ((0, 0, 0, 0),)
    images[0, 0, 0, 0, 0] = [12, 20]
    clean = prepare(images, **kw)
    close(clean.frame_sums[1, 2, 2, 1], 29 / 6)
    assert clean.sentinel_frames == ()


@pytest.mark.parametrize("background", [3.0, np.full((2, 4), 3.0)], ids=["scalar", "map"])
def test_signed_zero_camera_slopes_and_negative_counts(prepare: Any, background: Any) -> None:
    images = np.arange(-12, 36, dtype=np.int16).reshape(1, 1, 3, 2, 2, 4)
    images[images == -1] = -2  # only ordinary negative data in this control
    slope = np.array([[0, -2, 0.5, 1], [3, -1, 2, 0.25]])
    kw = options(
        norders=2,
        background=background,
        flatfield_slope=slope,
        exposure_background=np.full((1, 1, 3, 2), 1.25),
    )
    _, rows = uniform_rows(1, 3, 2)
    result = prepare(images, **kw)
    truth = expected(images, rows, **kw)
    close(result.quadratures, truth["quadratures"])
    close(result.frame_sums, truth["frame_sums"])


@pytest.mark.parametrize("width", [0, 1, 2, 3, -1, -2, -17])
def test_edge_modes_overlap_odd_height_and_selector(prepare: Any, width: int) -> None:
    images = (np.arange(72).reshape(1, 1, 3, 2, 3, 4) + 2).astype(np.int16)
    kw = options(norders=2, edge_pixels=width, background=0.5)
    _, rows = uniform_rows(1, 3, 2)
    truth = expected(images, rows, **kw)
    result = prepare(images, **kw)
    close(result.quadratures, truth["quadratures"])
    close(result.frame_sums, truth["frame_sums"])
    assert result.edge_pixels == width


def test_edge_radical_and_half_sample_window_at_public_entry(prepare: Any) -> None:
    images = np.tile(np.arange(0, 16, 2).reshape(1, 1, 1, 1, 2, 4), (1, 1, 1, 2, 1, 1))
    c = 1 - math.sqrt(0.5)
    plane = (
        np.array(
            [[7 * c, 2 + 4 * c, 4 + 4 * c, 6 + c], [8 - c, 10 - 4 * c, 12 - 4 * c, 14 - 7 * c]]
        )
        / 16
    )
    result = prepare(images, **options(norders=1, edge_pixels=1))
    close(result.quadratures, direct_volume(np.tile(plane, (2, 1, 1)))[None, None, None])
    close(result.frame_sums, 3.5)
    sine = prepare(np.ones((1, 1, 1, 2, 2, 2)), **options(norders=1, edge_pixels=-1))
    close(sine.frame_sums, 0.25)
    close(sine.quadratures[0, 0, 0, 0, 0, 0], 0.5)


@pytest.mark.parametrize(
    "ez,et,ref,gain",
    [
        (False, False, 15, 0.5),
        (True, False, 9, 0.3),
        (False, True, 10, 1 / 3),
        (True, True, 6, 0.2),
    ],
)
def test_all_four_z_time_anchor_decisions(
    prepare: Any, ez: bool, et: bool, ref: int, gain: float
) -> None:
    sums = np.array(
        [[[[6, 10], [18, 30]], [[12, 20], [24, 40]]], [[[9, 15], [18, 30]], [[27, 45], [36, 60]]]],
        dtype=float,
    )
    # X*Y*Z*D=8, four pixels? each plane has 2 pixels: raw=4*S.
    images = np.repeat((4 * sums)[..., None, None], 2, axis=-1)
    kw = options(norders=1, equalize=True, equalize_z=ez, equalize_time=et)
    _, rows = uniform_rows(2, 2, 1)
    result = prepare(images, **kw)
    close(result.frame_sums, sums)
    close(result.equalization_gains[1, 0, 1, 1], gain)
    close(result.frame_sums[1, :, :, 1] * result.equalization_gains[1, :, :, 1], ref)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])


@pytest.mark.parametrize("ez,et", [(False, False), (True, False), (False, True), (True, True)])
def test_disabled_equalization_accepts_zero_and_records_flags(
    prepare: Any, ez: bool, et: bool
) -> None:
    result = prepare(
        np.zeros((1, 1, 1, 2, 1, 2)), **options(norders=1, equalize_z=ez, equalize_time=et)
    )
    np.testing.assert_array_equal(result.quadratures, 0)
    np.testing.assert_array_equal(result.equalization_gains, 1)
    assert result.equalize is False
    assert result.equalize_z == ez and result.equalize_time == et


@pytest.mark.parametrize("zero_kind", ["anchor", "later", "cancellation"])
def test_equalization_rejects_zero_divisors_without_mutation(prepare: Any, zero_kind: str) -> None:
    images = np.full((1, 1, 3, 2, 1, 2), 8.0)
    target = (0, 0, 0 if zero_kind == "anchor" else 2, 0, 0)
    images[target] = [2, -2] if zero_kind == "cancellation" else [0, 0]
    original = images.copy()
    with pytest.raises(simrecon.SimreconError, match=r"(?i)sum|equaliz|zero|divis"):
        prepare(images, **options(norders=2, equalize=True))
    np.testing.assert_array_equal(images, original)


def test_negative_nonzero_sums_equalize_without_clipping(prepare: Any) -> None:
    images = np.full((1, 1, 3, 2, 1, 2), -8.0)
    images[:, :, 1] = 4
    images[:, :, 2] = -2
    kw = options(norders=2, equalize=True)
    _, rows = uniform_rows(1, 3, 2)
    result = prepare(images, **kw)
    close(result.equalization_gains[0, 0, :, 0], [1, -2, 4])
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])


def test_uniform_harmonic_sign_slot_scale_and_complex_partners(prepare: Any) -> None:
    # P=4 gives exact float32 samples for a signed first harmonic.
    # f(x)=sin(2*pi*x/4), spatial imaginary Fourier coefficient fixes odd sign.
    phase_sign = np.array([0, 1, 0, -1])
    spatial = np.array([0, 1, 0, -1])
    images = np.tile(
        (8 + 4 * phase_sign[:, None] * spatial)[None, None, :, None, None, :], (1, 1, 1, 2, 1, 1)
    )
    result = prepare(images, **options(norders=2))
    close(result.quadratures[0, 0, :, 0, 0, 1], [0, 0, -4j])
    e, o = result.quadratures[0, 0, 1:3, 0, 0, 1]
    close(e + 1j * o, 4)
    close(e - 1j * o, -4)
    assert not np.isclose(e - 1j * o, np.conj(e + 1j * o))
    phi, rows = uniform_rows(1, 4, 2)
    close(result.separation_matrices, rows)
    close(result.phase_angles_rad, phi)
    np.testing.assert_array_equal(result.noise_variance_factors, 1)
    assert result.phase_policy == "uniform"


@pytest.mark.parametrize("orders", [1, 2, 3])
def test_uniform_five_phase_all_harmonic_rows_and_noise(prepare: Any, orders: int) -> None:
    images = (np.arange(3 * 5 * 3 * 3 * 4).reshape(1, 3, 5, 3, 3, 4) % 29).astype(np.int16)
    phi, rows = uniform_rows(3, 5, orders)
    kw = options(norders=orders)
    result = prepare(images, **kw)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])
    close(result.separation_matrices, rows)
    close(result.phase_angles_rad, phi)
    np.testing.assert_array_equal(result.noise_variance_factors, np.ones((3, orders)))


def test_supplied_uniform_list_selects_inverse_not_uniform_policy(prepare: Any) -> None:
    images = np.arange(48, dtype=np.int16).reshape(1, 1, 3, 2, 2, 4)
    phi, rows = uniform_rows(1, 3, 2)
    result = prepare(images, **options(norders=2, phases_rad=phi))
    close(result.separation_matrices, rows)
    close(result.noise_variance_factors, [[1, 1]])
    assert result.phase_policy == "supplied"
    # P=5 reduced order also selects supplied policy, even when rows coincide.
    phi5, rows5 = uniform_rows(1, 5, 2)
    result5 = prepare(np.ones((1, 1, 5, 2, 1, 2)), **options(norders=2, phases_rad=phi5))
    close(result5.separation_matrices, rows5)
    close(result5.noise_variance_factors, [[1, 1]])
    assert result5.phase_policy == "supplied"


def test_repeated_phases_unweighted_residual_projection(prepare: Any) -> None:
    phi, rows = repeated_rows()
    images = np.array([4, 12, 8, 16], dtype=np.int16)[None, None, :, None, None, None] * np.ones(
        (1, 1, 4, 2, 1, 2), dtype=np.int16
    )
    kw = options(norders=2, phases_rad=phi)
    result = prepare(images, **kw)
    close(result.separation_matrices, rows)
    close(result.noise_variance_factors, [[1.5, 1.75]])
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])
    changed = images.copy()
    changed[:, :, 2] += 3
    changed[:, :, 3] -= 3
    other = prepare(changed, **kw)
    close(other.quadratures[..., :-1], result.quadratures[..., :-1])
    # q=2 retains phase 2 at the endpoint. Its DC here is zero, so use a pattern.
    changed[:, :, 2, :, :, 0] += 4
    changed[:, :, 3, :, :, 0] -= 4
    third = prepare(changed, **kw)
    close(third.quadratures[..., :-1], result.quadratures[..., :-1])
    assert abs(third.quadratures[0, 0, 2, 0, 0, -1]) > 1


@pytest.mark.parametrize("phases", [np.zeros((1, 3)), np.array([[0, 0, np.pi]])])
def test_rank_deficient_phase_design_rejects(prepare: Any, phases: Any) -> None:
    with pytest.raises(simrecon.SimreconError, match=r"(?i)phase|rank|singular|design"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(norders=2, phases_rad=phases))


def test_clustered_but_resolved_full_rank_has_no_coarse_cutoff(prepare: Any) -> None:
    a = 0.01
    phi = np.array([[a, 0, -a]])
    e = 3 / (4 * (math.cos(a) - 1))
    o = 3 / (4 * math.sin(a))
    rows = np.array([[[-2 * e, 3 + 4 * e, -2 * e], [e, -2 * e, e], [o, 0, -o]]])
    images = np.array([3, 5, 8], dtype=np.int16)[None, None, :, None, None, None] * np.ones(
        (1, 1, 3, 2, 1, 2), dtype=np.int16
    )
    kw = options(norders=2, phases_rad=phi)
    result = prepare(images, **kw)
    close(result.separation_matrices, rows, CLUSTERED_TOL)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"], CLUSTERED_TOL)


@pytest.mark.parametrize("orders,phases", [(1, 2), (2, 4), (3, 5)])
def test_nyquist_retains_both_components_raw_phase_identity_and_axial_sum(
    prepare: Any, orders: int, phases: int
) -> None:
    images = np.zeros((1, 1, phases, 3, 3, 4), dtype=np.int16)
    # Different p,z amplitudes; y=1 gives nonzero imaginary endpoint at ky=1.
    for p in range(phases):
        for z in range(3):
            images[0, 0, p, z, 1, 1] = 4 * (p + 1) * (z + 2)
    kw = options(norders=orders)
    result = prepare(images, **kw)
    _, rows = uniform_rows(1, phases, orders)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])
    # At kz=1, sum_z(z+2)*exp(-2pi*i*z/3)=-3/2+i*sqrt(3)/2.
    # x=1 endpoint contributes -1; y=1 contributes exp(-2pi*i/3).
    root = complex(-0.5, -math.sqrt(3) / 2)
    for q in range(2 * orders - 1):
        value = -(q + 1) / 9 * root * complex(-1.5, math.sqrt(3) / 2)
        close(result.quadratures[0, 0, q, 1, 1, -1], value)
        assert abs(value.real) > 0 and abs(value.imag) > 0


@pytest.mark.parametrize(
    "dtype",
    [
        np.uint8,
        np.int8,
        np.uint16,
        np.int16,
        np.uint32,
        np.int32,
        np.uint64,
        np.int64,
        np.float16,
        np.float32,
        np.float64,
    ],
)
def test_exact_float32_subset_input_dtypes(prepare: Any, dtype: Any) -> None:
    images = np.arange(24).reshape(1, 1, 3, 2, 1, 4).astype(dtype)
    result = prepare(images, **options(norders=2))
    _, rows = uniform_rows(1, 3, 2)
    close(result.quadratures, expected(images, rows, **options(norders=2))["quadratures"])


def test_strided_negative_stride_readonly_arrays_all_arguments(prepare: Any) -> None:
    images, kw, rows = composition()
    images = images[..., ::-1]
    # Keep sentinels ordinary after reversal; new right edge has no sentinel.
    for key in ("background", "flatfield_slope"):
        kw[key] = kw[key][:, ::-1]
    kw["phases_rad"] = kw["phases_rad"][:, ::-1]
    rows = rows[:, :, ::-1]
    kw["exposure_background"] = kw["exposure_background"][:, :, ::-1, :]
    inputs = [images] + [v for v in kw.values() if isinstance(v, np.ndarray)]
    snapshots = [a.copy() for a in inputs]
    for a in inputs:
        a.flags.writeable = False
    truth = expected(images, rows, **kw)
    result = prepare(images, **kw)
    close(result.quadratures, truth["quadratures"])
    for a, old in zip(inputs, snapshots, strict=True):
        np.testing.assert_array_equal(a, old)
        assert not a.flags.writeable


def invalid_arrays() -> list[Any]:
    base = np.ones((1, 1, 3, 2, 1, 2))
    return [
        pytest.param(base.tolist(), id="nonarray"),
        pytest.param(base.astype(complex), id="complex"),
        pytest.param(base.astype(object), id="object"),
        pytest.param(base.astype(str), id="string"),
        pytest.param(base.astype(bool), id="bool"),
        pytest.param(np.full_like(base, np.nan), id="nan"),
        pytest.param(np.full_like(base, np.inf), id="infinity"),
        pytest.param(base.reshape(1, 3, 2, 1, 2), id="missing-axis"),
        pytest.param(np.ones((1, 1, 3, 2, 1, 2, 1)), id="extra-axis"),
        pytest.param(np.ones((1, 1, 3, 1, 1, 2)), id="Z-one"),
        pytest.param(np.ones((1, 1, 3, 2, 1, 3)), id="odd-X"),
        pytest.param(np.ones((1, 1, 3, 2, 1, 1)), id="X-one"),
        *[
            pytest.param(
                np.empty(tuple(0 if i == axis else n for i, n in enumerate(base.shape))),
                id=f"empty-axis-{axis}",
            )
            for axis in range(6)
        ],
    ]


@pytest.mark.parametrize("images", invalid_arrays())
def test_image_type_shape_finite_domain_errors(prepare: Any, images: Any) -> None:
    with pytest.raises(
        simrecon.SimreconError,
        match=r"(?i)image|shape|dimension|axis|dtype|finite|sample|real|array|empty|even|[xz]",
    ):
        prepare(images, **options(norders=2))


@pytest.mark.parametrize(
    "name,valid_shape",
    [
        ("background", (1, 2)),
        ("flatfield_slope", (1, 2)),
        ("exposure_background", (1, 1, 3, 2)),
        ("phases_rad", (1, 3)),
    ],
)
@pytest.mark.parametrize(
    "kind", ["list", "shape", "complex", "object", "string", "bool", "nan", "inf"]
)
def test_map_exposure_phase_errors_separate_type_shape_finiteness(
    prepare: Any, name: str, valid_shape: tuple[int, ...], kind: str
) -> None:
    value: Any = np.ones(valid_shape)
    if kind == "list":
        value = value.tolist()
    elif kind == "shape":
        value = np.ones((1,))
    elif kind in ("complex", "object", "string", "bool"):
        value = value.astype(
            {"complex": complex, "object": object, "string": str, "bool": bool}[kind]
        )
    else:
        value[:] = np.nan if kind == "nan" else np.inf
    kw = options(**({"norders": 2} | {name: value}))
    with pytest.raises(
        simrecon.SimreconError, match=r"(?i)background|slope|flatfield|exposure|phase"
    ):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **kw)


@pytest.mark.parametrize("name", ["dxy_um", "dz_um"])
@pytest.mark.parametrize("value", [0, -1, True, np.nan, np.inf, 1j, "1", [1], np.array([1.0])])
def test_sampling_errors(prepare: Any, name: str, value: Any) -> None:
    with pytest.raises(simrecon.SimreconError, match=r"(?i)dxy|dz|sampl|pitch"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(**({"norders": 2} | {name: value})))


@pytest.mark.parametrize("value", [True, complex(1), "1", np.nan, np.inf])
def test_scalar_background_errors(prepare: Any, value: Any) -> None:
    with pytest.raises(simrecon.SimreconError, match=r"(?i)background"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(norders=2, background=value))


@pytest.mark.parametrize("name", ["norders", "lateral_zoom", "axial_zoom", "edge_pixels"])
@pytest.mark.parametrize("value", [True, 1.5, 1.0, "1", np.nan, np.inf, 1j])
def test_integer_parameter_types(prepare: Any, name: str, value: Any) -> None:
    with pytest.raises(simrecon.SimreconError, match=r"(?i)order|zoom|edge|integer"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(**({"norders": 2} | {name: value})))


@pytest.mark.parametrize(
    "name,value",
    [
        ("norders", 0),
        ("norders", -1),
        ("norders", 3),
        ("lateral_zoom", 0),
        ("lateral_zoom", -1),
        ("axial_zoom", 0),
        ("axial_zoom", -1),
        ("edge_pixels", 2),
        ("norders", 2**31),
        ("lateral_zoom", 2**31),
        ("axial_zoom", 2**31),
        ("edge_pixels", -(2**31) - 1),
        ("lateral_zoom", 2**24 + 1),
    ],
)
def test_count_zoom_edge_and_source_integer_domain(prepare: Any, name: str, value: int) -> None:
    with pytest.raises(
        simrecon.SimreconError, match=r"(?i)order|zoom|edge|index|32|represent|range"
    ):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(**({"norders": 2} | {name: value})))


@pytest.mark.parametrize("name", ["equalize", "equalize_z", "equalize_time"])
@pytest.mark.parametrize("value", [0, 1, "true", None, np.array([True])])
def test_flags_require_booleans(prepare: Any, name: str, value: Any) -> None:
    with pytest.raises(simrecon.SimreconError, match=r"(?i)equaliz|bool"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(**({"norders": 2} | {name: value})))


def test_public_defaults_are_applied_without_clamping(prepare: Any) -> None:
    images = np.ones((1, 1, 3, 2, 10, 10))
    kw = options(norders=np.int64(2), lateral_zoom=np.int32(1), axial_zoom=np.int64(1))
    del kw["edge_pixels"]
    del kw["equalize"]
    result = prepare(images, **kw)
    assert result.edge_pixels == 10 and result.equalize is True
    assert result.equalize_z is False and result.equalize_time is False
    assert result.phase_policy == "uniform"
    close(result.quadratures[0, 0, 0, 0, 0, 0], 3)
    np.testing.assert_array_equal(result.background_after, 0)
    np.testing.assert_array_equal(result.slope_after, 1)
    with pytest.raises(simrecon.SimreconError, match=r"(?i)edge|dimension|width"):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **kw)


@pytest.mark.parametrize("value", [-1 + 1e-10, 0.1, float(2**24 + 1), float(2**128)])
def test_inexact_or_overflowed_raw_float32_rejects(prepare: Any, value: float) -> None:
    images = np.ones((1, 1, 3, 2, 1, 2))
    images[0, 0, 0, 0, 0, 1] = value
    before = images.copy()
    with pytest.raises(simrecon.SimreconError, match=r"(?i)image|sample|float32|represent"):
        prepare(images, **options(norders=2))
    np.testing.assert_array_equal(images, before)


@pytest.mark.parametrize(
    "dtype,value",
    [
        (np.int64, 2**24 + 1),
        (np.uint64, 2**63 + 1),
        (np.longdouble, 1),
    ],
)
def test_raw_inexactness_and_actual_longdouble_representation(
    prepare: Any, dtype: Any, value: int
) -> None:
    images = np.full((1, 1, 3, 2, 1, 2), value, dtype=dtype)
    kw = options(norders=2)
    if images.dtype == np.dtype(np.float64):
        # longdouble can name ordinary float64; these exact raw ones are valid.
        _, rows = uniform_rows(1, 3, 2)
        result = prepare(images, **kw)
        truth = expected(images, rows, **kw)
        close(result.quadratures, truth["quadratures"])
        close(result.frame_sums, truth["frame_sums"])
    else:
        with pytest.raises(simrecon.SimreconError, match=r"(?i)image|sample|float|dtype|represent"):
            prepare(images, **kw)


@pytest.mark.parametrize(
    "shape,orders",
    [
        ((1, 1, 1, 2**30, 1, 2), 1),
        ((1, 1, 1, 2**29, 1, 2), 1),
        ((1, 65536, 32768, 2, 1, 2), 1),
        ((1, 1, 65537, 2, 1, 2), 32769),
        ((1, 1, 1, 2, 1, 2**31), 1),
    ],
)
def test_unsafe_source_products_reject_metadata_only_views(
    prepare: Any, shape: tuple[int, ...], orders: int
) -> None:
    # broadcast_to allocates only metadata; no dangerous strided backing buffer.
    images = np.broadcast_to(np.array(0, dtype=np.float32), shape)
    with pytest.raises(
        simrecon.SimreconError, match=r"(?i)index|size|dimension|32|range|overflow|product"
    ):
        prepare(images, **options(norders=orders))


@pytest.mark.parametrize("kind", ["correction", "sum", "gain", "transform"])
def test_natural_numerical_operation_failures_are_explicit(prepare: Any, kind: str) -> None:
    images = np.zeros((1, 1, 3, 2, 1, 2))
    kw = options(norders=2, background=-1e308)
    if kind == "correction":
        kw["flatfield_slope"] = np.full((1, 2), 1e308)
    elif kind == "sum":
        kw["flatfield_slope"] = np.full((1, 2), 6.0)
    elif kind == "gain":
        kw["background"] = 0
        kw["exposure_background"] = np.array([[[[-1e308, -1e308], [-1e-308, -1e-308], [-1, -1]]]])
        kw["equalize"] = True
    else:
        # Each frame sum=5e307 finite, but order-zero 3*2 frames overflows.
        pass
    before = images.copy()
    with pytest.raises(
        simrecon.SimreconError, match=r"(?i)finite|overflow|numeric|correction|sum|gain|transform"
    ):
        prepare(images, **kw)
    np.testing.assert_array_equal(images, before)


@pytest.mark.parametrize(
    "unknown",
    [
        "channel",
        "off_exposures",
        "phase_step",
        "drift",
        "axial_padding",
        "transfer",
        "wiener",
        "bessel",
    ],
)
def test_unsupported_modes_are_signature_errors(prepare: Any, unknown: str) -> None:
    with pytest.raises(TypeError):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(norders=2, **{unknown: True}))


def test_required_arguments_and_extra_positionals_are_signature_errors(prepare: Any) -> None:
    with pytest.raises(TypeError):
        prepare(np.ones((1, 1, 3, 2, 1, 2)))
    with pytest.raises(TypeError):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), 0.1, **options(norders=2))


def test_second_harmonic_analytic_sign_and_slot(prepare: Any) -> None:
    phase = np.array([0, 1, 0, -1, 0, 1, 0, -1])
    spatial = np.array([0, 1, 0, -1])
    images = np.tile(
        (12 + 4 * phase[:, None] * spatial)[None, None, :, None, None, :], (1, 1, 1, 2, 1, 1)
    )
    result = prepare(images, **options(norders=3))
    close(result.quadratures[0, 0, :, 0, 0, 1], [0, 0, 0, 0, -8j])
    np.testing.assert_array_equal(result.noise_variance_factors, [[1, 1, 1]])


def test_signed_wrapped_yz_and_all_axis_conjugate_boundary(prepare: Any) -> None:
    images = np.zeros((1, 1, 3, 3, 5, 4), dtype=np.int16)
    images[:, :, :, 1, 1, 1] = 60  # alpha=1/60, unit impulse in each phase
    result = prepare(images, **options(norders=2, dxy_um=0.2, dz_um=0.6))
    # ky=4 is -1/(5*0.2), kz=2 is -1/(3*0.6), with first-sample origin.
    phase = 2 * math.pi * (1 / 3 + 1 / 5 - 1 / 4)
    close(result.quadratures[0, 0, 0, 2, 4, 1], 3 * complex(math.cos(phase), math.sin(phase)))
    for kx in (0, 2):
        for kz, ky in np.ndindex((3, 5)):
            close(
                result.quadratures[0, 0, :, kz, ky, kx],
                np.conj(result.quadratures[0, 0, :, (-kz) % 3, (-ky) % 5, kx]),
            )


def test_supplied_unwrapped_angles_are_preserved(prepare: Any) -> None:
    phases, rows = square_rows()
    phases = phases + np.array([4 * np.pi, -2 * np.pi, 6 * np.pi])[:, None]
    images = np.arange(360, dtype=np.int16).reshape(1, 3, 5, 3, 2, 4)
    kw = options(phases_rad=phases)
    result = prepare(images, **kw)
    np.testing.assert_array_equal(result.phase_angles_rad, phases)
    close(result.separation_matrices, rows)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])


def test_unrepresentable_phase_inverse_fails_explicitly(prepare: Any) -> None:
    # Distinct mathematical points, but required inverse coefficients ~1/a**2
    # exceed float64. No successful finite matrix can satisfy this design.
    phases = np.array([[1e-200, 0, -1e-200]])
    with pytest.raises(
        simrecon.SimreconError, match=r"(?i)phase|matrix|rank|finite|factor|singular|numeric"
    ):
        prepare(np.ones((1, 1, 3, 2, 1, 2)), **options(norders=2, phases_rad=phases))


def test_validation_precedes_sentinel_correction_and_overflow(prepare: Any) -> None:
    images = np.ones((1, 1, 3, 2, 1, 2))
    images[0, 0, 0, 0, 0, 1] = -1
    background = np.full((1, 2), -1e308)
    slope = np.full((1, 2), 1e308)
    snapshots = [a.copy() for a in (images, background, slope)]
    with pytest.raises(simrecon.SimreconError, match=r"(?i)phase"):
        prepare(
            images,
            **options(
                norders=2,
                background=background,
                flatfield_slope=slope,
                phases_rad=np.full((1, 3), np.nan),
            ),
        )
    for array, old in zip((images, background, slope), snapshots, strict=True):
        np.testing.assert_array_equal(array, old)


def test_binary64_camera_and_exposure_values_are_not_raw_quantized(prepare: Any) -> None:
    images = np.full((1, 1, 3, 2, 1, 2), 2.0)
    kw = options(
        norders=2,
        background=np.full((1, 2), 0.1),
        flatfield_slope=np.full((1, 2), 0.3),
        exposure_background=np.full((1, 1, 3, 2), 0.2),
    )
    result = prepare(images, **kw)
    close(result.frame_sums, 0.255)
    close(result.quadratures[0, 0, 0, 0, 0, 0], 1.53)


@pytest.mark.parametrize(
    "name,shape",
    [
        ("background", (1, 2)),
        ("flatfield_slope", (1, 2)),
        ("exposure_background", (1, 1, 3, 2)),
        ("phases_rad", (1, 3)),
    ],
)
def test_array_arguments_follow_actual_longdouble_representation(
    prepare: Any, name: str, shape: tuple[int, ...]
) -> None:
    phases, rows = uniform_rows(1, 3, 2)
    value = (
        phases.astype(np.longdouble)
        if name == "phases_rad"
        else np.ones(shape, dtype=np.longdouble)
    )
    images = np.full((1, 1, 3, 2, 1, 2), 8.0)
    kw = options(norders=2, **{name: value})
    if value.dtype == np.dtype(np.float64):
        # Use a full-rank supplied list, so alias acceptance cannot hit a rank guard.
        truth = expected(images, rows, **kw)
        result = prepare(images, **kw)
        close(result.quadratures, truth["quadratures"])
        close(result.frame_sums, truth["frame_sums"])
    else:
        with pytest.raises(
            simrecon.SimreconError,
            match=r"(?i)background|slope|flatfield|exposure|phase|dtype|precision",
        ):
            prepare(images, **kw)


def test_independent_repeated_phase_rows_residual_and_noise() -> None:
    _, rows = repeated_rows()
    g = np.array([4, 12, 8, 16.0])
    # h=12 -> (B,E,O)=(32,-8,8), independent scalar equations.
    close(rows[0] @ g, [32, -8, 8])
    close(rows[0] @ (g + [0, 0, 7, -7]), [32, -8, 8])
    close(np.sum(rows[0, 0] ** 2) / 4, 1.5)
    close(np.sum(rows[0, 1:] ** 2) / 4, 1.75)


def test_independent_composed_observer_constant_control() -> None:
    _, rows = uniform_rows(3, 5, 3)
    images = np.full((1, 3, 5, 3, 2, 4), 20.0)
    kw = options(
        background=3,
        flatfield_slope=np.full((2, 4), 4.0),
        exposure_background=np.full((1, 3, 5, 3), 2.0),
        lateral_zoom=2,
        axial_zoom=2,
    )
    truth = expected(images, rows, **kw)
    close(truth["frame_sums"], 5 / 6)
    close(truth["quadratures"][0, :, 0, 0, 0, 0], 12.5)
    close(truth["quadratures"][:, :, 1:, :, :, :-1], 0)


def test_existing_error_remains_value_error() -> None:
    assert issubclass(simrecon.SimreconError, ValueError)


def test_large_but_safe_source_zoom_and_exact_raw_boundary(prepare: Any) -> None:
    images = np.full((1, 1, 1, 2, 1, 2), 2**24, dtype=np.int64)
    kw = options(norders=1, lateral_zoom=np.int64(2**24), axial_zoom=np.int64(2**31 - 1))
    result = prepare(images, **kw)
    # Valid source integers can make small positive outputs. No size cap or
    # downstream resampling allocation applies to this native-grid stage.
    alpha = 1 / (4 * (2**24) ** 2 * (2**31 - 1))
    assert math.isfinite(result.input_scale) and result.input_scale > 0
    close(result.input_scale / alpha, 1)
    close(result.quadratures[0, 0, 0, 0, 0, 0] / (4 * 2**24 * alpha), 1)
    assert result.quadratures.shape == (1, 1, 1, 2, 1, 2)


@pytest.mark.parametrize(
    "dtype,value",
    [
        (np.uint64, 2**63),
        (np.int64, -(2**60)),
        (np.float64, 1.5),
        (np.float32, np.finfo(np.float32).max),
    ],
)
def test_large_signed_dyadic_and_float32_endpoint_raw_values_are_valid(
    prepare: Any, dtype: Any, value: Any
) -> None:
    images = np.full((1, 1, 1, 2, 1, 2), value, dtype=dtype)
    result = prepare(images, **options(norders=1))
    close(result.quadratures[0, 0, 0, 0, 0, 0], float(value))
    close(result.frame_sums, float(value) / 2)


def test_supplied_noise_uses_each_directions_distinct_design(prepare: Any) -> None:
    uniform_phases, uniform = uniform_rows(1, 5, 3)
    irregular_phases, irregular = square_rows()
    phases = np.concatenate((uniform_phases, irregular_phases[:1]))
    rows = np.concatenate((uniform, irregular[:1]))
    images = (np.arange(80).reshape(1, 2, 5, 2, 1, 4) % 17 + 3).astype(np.int16)
    kw = options(phases_rad=phases)
    result = prepare(images, **kw)
    # Independent norms: fifth-root orthogonality versus cardinal/diagonal inverse.
    close(result.noise_variance_factors, [[1, 1, 1], [5 / 4, 5 / 4, 5 / 2]])
    close(result.separation_matrices, rows)
    close(result.quadratures, expected(images, rows, **kw)["quadratures"])


def test_sine_window_precedes_equalization_sums_gains_and_final_quadratures(prepare: Any) -> None:
    images = np.zeros((1, 1, 3, 2, 1, 4), dtype=np.int16)
    for p in range(3):
        images[0, 0, p, :, 0, p] = 8
    s = math.sqrt(2 - math.sqrt(2)) / 2
    c = math.sqrt(2 + math.sqrt(2)) / 2
    sums = np.repeat(np.array([s, c, c])[None, None, :, None], 2, axis=-1)
    gains = np.repeat(
        np.array([1, math.sqrt(2) - 1, math.sqrt(2) - 1])[None, None, :, None], 2, axis=-1
    )
    # Closed-form Fourier roots, phase rows and axial factor2; no shared observer.
    quadratures = np.zeros((1, 1, 3, 2, 1, 3), dtype=np.complex128)
    quadratures[0, 0, :, 0, 0, :] = s * np.array(
        [[6, -2j, 2], [0, 3 + 1j, -2], [0, math.sqrt(3) * (1 - 1j), 2]]
    )
    result = prepare(images, **options(norders=2, edge_pixels=-1, equalize=True))
    close(result.frame_sums, sums)
    close(result.equalization_gains, gains)
    close(result.quadratures, quadratures)


def test_unrepresentable_noise_factor_rejects_even_for_zero_data(prepare: Any) -> None:
    images = np.zeros((1, 1, 3, 2, 1, 2), dtype=np.float64)
    phases = np.array([[0, np.pi, 1e-160]], dtype=np.float64)
    original_images = images.copy()
    original_phases = phases.copy()
    # Finite odd-row coefficients ~1.5e160 require a noise factor ~1.5e320.
    # A backend's explicit inability to resolve the design is also legitimate.
    with pytest.raises(
        simrecon.SimreconError,
        match=r"(?i)noise|variance|finite|overflow|numeric|phase|matrix|factor|rank|singular",
    ):
        prepare(images, **options(norders=2, phases_rad=phases))
    np.testing.assert_array_equal(images, original_images)
    np.testing.assert_array_equal(phases, original_phases)
