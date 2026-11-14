"""Allocation-byte admission, retained integer guards and tiny public complements.

No newly admitted large declaration is sent down a successful numerical path.
"""

from __future__ import annotations

import importlib
from math import prod
from typing import Any

import numpy as np
import pytest

import simrecon
from c_acquisition_fixture import options
from c_known_fixture import blank, known, table
from reconstruction_summary_fixture import analytical_case, analytical_expected, walk_arrays
from wide_allocation_fixture import SIGNED_MAX, M, U, geometry, stride_bytes


def extent_validator(route: str) -> tuple[Any, type[ValueError]]:
    if route == "acquisition":
        module = importlib.import_module("simrecon.acquisition.layout")
        return module.extent, simrecon.AcquisitionModeError
    module = importlib.import_module("simrecon.reconstruction.known_parameters")
    return module._extent, simrecon.ReconstructionError


def output_extents(shape: tuple[int, ...], lateral: float, axial: int) -> None:
    module = importlib.import_module("simrecon.acquisition.layout")
    module.output_extents(shape, lateral, axial)


@pytest.mark.parametrize("route", ["acquisition", "known"])
def test_native_byte_bound_is_inclusive_exact_and_does_not_wrap(route: str) -> None:
    validate, error = extent_validator(route)
    assert int(np.iinfo(np.intp).max) == M
    for count in (M - 1, M):
        assert validate((count,), 1) is None
    with pytest.raises(error):
        validate((M + 1,), 1)
    # All individual dimensions fit; these products distinguish exact integer
    # arithmetic from float rounding at M and fixed-width multiplication wrap.
    assert 7 * (M // 7) == M
    assert validate((7, M // 7), 1) is None
    for shape in ((8, 2**60), (2**32, 2**32)):
        assert all(d <= M for d in shape)
        assert stride_bytes(shape, 1) > M
        with pytest.raises(error):
            validate(shape, 1)


@pytest.mark.parametrize("route", ["acquisition", "known"])
@pytest.mark.parametrize("itemsize", [8, 16])
def test_actual_itemsize_and_aggregate_native_extents(route: str, itemsize: int) -> None:
    validate, error = extent_validator(route)
    last = M // itemsize
    assert itemsize * last == M - (itemsize - 1)
    assert itemsize * (last + 1) == M + 1
    assert validate((last,), itemsize) is None
    with pytest.raises(error):
        validate((last + 1,), itemsize)
    per_time = 2**58
    assert stride_bytes((per_time,), itemsize) <= M
    assert stride_bytes((4, per_time), itemsize) > M
    with pytest.raises(error):
        validate((4, per_time), itemsize)


def test_supported_empty_diagnostic_shape_still_needs_native_strides() -> None:
    validate, error = extent_validator("acquisition")
    assert validate((0, 0), 16) is None
    assert validate((0, M), 1) is None
    assert validate((0, M // 8), 8) is None
    for shape, itemsize in (((0, M // 8 + 1), 8), ((0, M + 1), 1), ((-1, 1), 1)):
        with pytest.raises(error):
            validate(shape, itemsize)
    # This exercises a metadata validator for supported empty diagnostics,
    # never a new successful empty scientific input.


@pytest.mark.parametrize("route", ["acquisition", "known"])
@pytest.mark.parametrize(
    "itemsize,old_cap",
    [
        (8, U),
        (4, U),
        (4, SIGNED_MAX),
    ],
)
def test_historical_byte_crossings_use_native_storage_rule(
    route: str, itemsize: int, old_cap: int
) -> None:
    validate, _ = extent_validator(route)
    # The historical scalar neighbors are arithmetic examples. Attainable
    # byte values are multiples of itemsize, so equality to an odd cap is
    # impossible; these are the nearest attainable counts on either side.
    assert old_cap - 1 < old_cap < old_cap + 1
    below, above = old_cap // itemsize, old_cap // itemsize + 1
    assert itemsize * below <= old_cap < itemsize * above
    assert itemsize * below == old_cap - (itemsize - 1)
    assert itemsize * above == old_cap + 1
    for count in (below - 1, below, above, above + 1):
        assert 0 < count <= SIGNED_MAX
        assert 0 < itemsize * count <= M
        assert validate((count,), itemsize) is None


@pytest.mark.parametrize("axial", [2**25 - 1, 2**25, 2**25 + 1, 2**26 - 1, 2**26, 2**26 + 1])
def test_output_byte_crossings_with_valid_signed_counts(axial: int) -> None:
    shape = (1, 1, 3, 2, 2, 4)
    counts = geometry(shape, 2, 1, axial)
    assert counts["signed"]["output_volume"] == 16 * axial <= SIGNED_MAX
    assert all(0 < count <= SIGNED_MAX for count in counts["signed"].values())
    assert all(0 < count <= M for count in counts["native_bytes"].values())
    assert counts["bytes"]["complex_output"] == 128 * axial
    assert counts["bytes"]["real_output"] == 64 * axial
    assert output_extents(shape, 1.0, axial) is None


@pytest.mark.parametrize("lateral", [8191, 8192, 8193])
def test_lookup_byte_crossing_does_not_widen_plane_indices(lateral: int) -> None:
    shape = (1, 1, 3, 1, 2, 4)
    counts = geometry(shape, 2, lateral, 1)
    assert counts["signed"]["output_plane"] == 8 * lateral**2 <= SIGNED_MAX
    assert counts["bytes"]["lookup"] == 32 * lateral**2
    assert (counts["bytes"]["lookup"] > SIGNED_MAX) == (lateral >= 8192)
    assert output_extents(shape, float(lateral), 1) is None
    with pytest.raises(simrecon.AcquisitionModeError):
        output_extents(shape, 32768.0, 1)


def test_signed_output_count_endpoint_is_separate_from_wide_bytes() -> None:
    # X>=2 even makes volume even; SIGNED_MAX itself is unattainable here. The last
    # admissible volume is SIGNED_MAX-1 and the next attainable one is SIGNED_MAX+1.
    shape = (1, 1, 3, 1, 1, 2)
    last = SIGNED_MAX // 2
    assert 2 * last == SIGNED_MAX - 1
    assert output_extents(shape, 1.0, last) is None
    assert 2 * (last + 1) == SIGNED_MAX + 1
    with pytest.raises(simrecon.AcquisitionModeError):
        output_extents(shape, 1.0, last + 1)


def test_order_byte_ceiling_is_dominated_by_retained_phase_matrix_count() -> None:
    # Q<=P and Q=2*O-1 imply Q*P>=Q**2. The largest O permitted
    # by this necessary signed count is 23170, far below the old byte cap.
    largest = 23170
    assert (2 * largest - 1) ** 2 <= SIGNED_MAX < (2 * (largest + 1) - 1) ** 2
    assert 8 * largest < U < 8 * (U // 8 + 1)
    assert (2 * (U // 8 + 1) - 1) ** 2 > SIGNED_MAX


@pytest.mark.parametrize("z", [2**27 - 1, 2**27, 2**27 + 1])
def test_native_complex_byte_crossing_keeps_native_element_counts(z: int) -> None:
    # These are integer declarations, not virtual/real target arrays. X=Y=2
    # separates the old native byte ceiling from all listed source counts.
    counts = geometry((1, 1, 3, z, 2, 2), 2, 1, 1)
    assert counts["signed"]["native_volume"] == 4 * z
    assert counts["signed"]["padded_real"] == 8 * z
    assert counts["bytes"]["complex_native"] == 32 * z
    assert (counts["bytes"]["complex_native"] > U) == (z >= 2**27)
    assert all(0 < count <= SIGNED_MAX for count in counts["signed"].values())
    validate, _ = extent_validator("known")
    assert validate((z, 2, 2), 16) is None


def test_motivating_geometry_classification_is_integer_only() -> None:
    shape = (1, 3, 5, 32, 2048, 2048)
    counts = geometry(shape, 3, 2, 1)
    assert counts["output_shape"] == (32, 4096, 4096)
    signed = counts["signed"]
    assert (signed["native_volume"], signed["padded_real"], signed["half_volume"]) == (
        134217728,
        134348800,
        67174400,
    )
    assert (signed["output_plane"], signed["output_volume"]) == (16777216, 536870912)
    assert counts["bytes"] == dict(
        complex_native=1073741824,
        complex_output=4294967296,
        real_output=2147483648,
        orders=24,
        lookup=67108864,
    )
    assert counts["native_bytes"]["image"] == 4294967296
    assert counts["native_bytes"]["raw"] == 16106127360
    assert all(0 < count <= SIGNED_MAX for count in signed.values())
    assert all(0 < count <= M for count in counts["native_bytes"].values())
    assert output_extents(shape, 2.0, 1) is None
    for route in ("acquisition", "known"):
        validate, _ = extent_validator(route)
        for array_shape, itemsize in counts["arrays"].values():
            assert validate(array_shape, itemsize) is None
    # No raw, target, Fourier or diagnostic array is constructed here. This
    # proves representation only; RAM fit and backend execution are unmeasured.


@pytest.mark.parametrize("lateral", [1, 6000, 8192])
@pytest.mark.parametrize("route", ["prepared", "acquisition"])
def test_direct_routes_keep_invalid_field_after_wide_byte_admission(
    lateral: int, route: str
) -> None:
    raw = np.zeros((1, 1, 3, 2, 2, 4), dtype=np.float32)
    if route == "prepared":
        bands = blank(shape=raw.shape, lateral_zoom=lateral)
    else:
        bands = simrecon.prepare_acquisition_bands(
            raw, **options(acquisition_mode="3d", lateral_zoom=float(lateral))
        )
    before = bands.quadratures.copy()
    # Genuine tiny native preparations retain the declared zoom and alpha;
    # wiener=0 is independently invalid. No huge reconstruction can succeed.
    assert bands.input_scale == 1 / (16 * lateral**2)
    with pytest.raises(simrecon.ReconstructionError, match="(?i)wiener"):
        known(bands, table(), wiener=0, modulation=np.ones((1, 1)))
    np.testing.assert_array_equal(bands.quadratures, before)


@pytest.mark.parametrize("lateral,axial", [(1, 1), (4096, 2)])
def test_acquisition_invalid_pitch_category_after_complex_byte_admission(
    lateral: int, axial: int
) -> None:
    raw = np.ones((1, 1, 3, 1, 4, 4), dtype=np.float64)
    before = raw.copy()
    with pytest.raises(simrecon.AcquisitionModeError, match="(?i)dxy|pitch"):
        simrecon.prepare_acquisition_bands(
            raw, **options(lateral_zoom=float(lateral), axial_zoom=axial, dxy_um=0)
        )
    np.testing.assert_array_equal(raw, before)


@pytest.mark.parametrize("entry_name", ["reconstruct_workflow", "reconstruct_summary"])
@pytest.mark.parametrize("axial", [1, 2**25])
def test_workflow_invalid_config_category_after_wide_byte_admission(
    entry_name: str, axial: int
) -> None:
    case = analytical_case()
    case["acquisition"].update(axial_zoom=axial, dxy_um=0.0)
    before = case["specimen"].copy()
    with pytest.raises(simrecon.WorkflowError) as caught:
        getattr(simrecon, entry_name)(**case)
    assert caught.value.code == "workflow_config"
    assert caught.value.stage == "declaration"
    np.testing.assert_array_equal(case["specimen"], before)


@pytest.mark.parametrize("entry_name", ["reconstruct_workflow", "reconstruct_summary"])
def test_invalid_output_geometry_precedes_copy_scan_and_backend(
    entry_name: str, monkeypatch: Any
) -> None:
    import scipy.fft

    case = analytical_case()
    case["acquisition"]["axial_zoom"] = 2**31
    raw = case["specimen"]
    before = raw.copy()
    touched: list[str] = []

    def observe(name: str, original: Any) -> Any:
        def call(value: Any, *args: Any, **kwargs: Any) -> Any:
            if isinstance(value, np.ndarray) and np.shares_memory(value, raw):
                touched.append(name)
            return original(value, *args, **kwargs)

        return call

    def allocate(original: Any) -> Any:
        def call(shape: Any, *args: Any, **kwargs: Any) -> Any:
            dims = (shape,) if isinstance(shape, int) else tuple(shape)
            assert prod(dims) <= 2**20, "invalid geometry reached target allocation"
            return original(shape, *args, **kwargs)

        return call

    def backend(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("invalid geometry reached numerical backend")

    with monkeypatch.context() as patch:
        for name in ("array", "copy", "ascontiguousarray", "isfinite"):
            patch.setattr(np, name, observe(name, getattr(np, name)))
        for name in ("empty", "zeros", "ones", "full"):
            patch.setattr(np, name, allocate(getattr(np, name)))
        for module in (np.fft, scipy.fft):
            for name in ("fftn", "ifftn", "rfftn", "irfftn", "fft2", "ifft2"):
                patch.setattr(module, name, backend)
        with pytest.raises(simrecon.WorkflowError) as caught:
            getattr(simrecon, entry_name)(**case)
    assert caught.value.code == "workflow_representation"
    assert caught.value.stage == "declaration"
    assert not touched, f"declaration reached array-sized work: {touched}"
    np.testing.assert_array_equal(raw, before)


@pytest.mark.parametrize(
    "route", ["known-prepared", "known-acquisition", "preparation", "workflow"]
)
@pytest.mark.parametrize("fault", ["allocation", "backend", "interruption"])
def test_small_operation_failures_keep_causes_interruptions_and_inputs(
    route: str, fault: str, monkeypatch: Any
) -> None:
    import scipy.fft

    function: Any
    inputs: dict[str, Any]
    if route == "workflow":
        inputs = analytical_case()
        args: tuple[Any, ...] = ()
        function = simrecon.reconstruct_workflow
        expected, _ = analytical_expected(False)
        direct_error: Any = None
    else:
        raw = np.zeros((1, 1, 3, 2, 2, 4), dtype=np.float32)
        inputs = options(acquisition_mode="3d")
        if route == "preparation":
            args = (raw,)
            function = simrecon.prepare_acquisition_bands
            direct_error = simrecon.AcquisitionModeError
        else:
            bands = (
                blank(shape=raw.shape)
                if route == "known-prepared"
                else simrecon.prepare_acquisition_bands(raw, **inputs)
            )
            args = (bands, table())
            function = simrecon.reconstruct_known
            inputs = dict(
                carriers_cyc_um=np.zeros((1, 2)),
                modulation=np.ones((1, 1)),
                wavelength_nm=520,
                numerical_aperture=0.8,
                immersion_index=1.33,
                wiener=0.5,
                suppress_singularities=False,
                output_taper="none",
            )
            direct_error = simrecon.ReconstructionError
        expected = np.zeros((1, 2, 2, 4))

    def check_positive(result: Any) -> None:
        if route == "preparation":
            np.testing.assert_array_equal(result.quadratures, 0)
            assert np.isfinite(result.noise_variance_factors).all()
            assert (result.noise_variance_factors > 0).all()
        else:
            np.testing.assert_allclose(result.image, expected, rtol=0, atol=2**-38)

    # The normal operation is an independently specified positive control.
    check_positive(function(*args, **inputs))
    arrays = walk_arrays((args, inputs))
    snapshots = [array.copy() for array in arrays]
    kind = (
        MemoryError
        if fault == "allocation"
        else KeyboardInterrupt
        if fault == "interruption"
        else RuntimeError
    )
    sentinel = kind("issue115 controlled external dependency failure")
    calls: list[bool] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        calls.append(True)
        raise sentinel

    outcome: Any = None
    caught: BaseException | None = None
    with monkeypatch.context() as patch:
        if fault == "backend":
            for module in (np.fft, scipy.fft):
                for name in (
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
                    patch.setattr(module, name, fail)
        else:
            for name in (
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
                patch.setattr(np, name, fail)
        try:
            outcome = function(*args, **inputs)
        except BaseException as error:
            caught = error
    if calls:
        assert outcome is None and caught is not None
        if fault == "interruption":
            assert caught is sentinel
        elif route == "workflow":
            if fault == "allocation":
                assert isinstance(caught, MemoryError)
            else:
                assert isinstance(caught, simrecon.WorkflowError)
                assert caught.code == "workflow_operation"
        else:
            assert isinstance(caught, direct_error)
        chain: list[BaseException] = []
        while caught is not None and all(caught is not item for item in chain):
            chain.append(caught)
            caught = caught.__cause__
        assert any(error is sentinel for error in chain)
    else:
        # A legitimate alternate backend/import is allowed. This branch is
        # only the independent positive control, never claimed fault coverage.
        assert caught is None
        check_positive(outcome)
    for actual, before in zip(arrays, snapshots, strict=True):
        np.testing.assert_array_equal(actual, before)
