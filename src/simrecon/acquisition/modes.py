"""Integrated native 2D/3D acquisition preparation in the selected source order."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .drift import between, correlation, cubic, frequencies, ramp
from .layout import (
    REFERENCE,
    AcquisitionModeError,
    Array,
    ModeEvent,
    append,
    array_metadata,
    event,
    extent,
    finite,
    integer,
    layout,
    literal,
    operation,
    output_extents,
    owned,
    raw_images,
    raw_off,
    real_array,
    scalar,
    signed,
    zoom,
)
from .preparation import _edge, _phase_matrices


@dataclass(frozen=True)
class AcquisitionBands:
    """Owned native bands and immutable acquisition-stage diagnostics.

    Quadratures and scalar noise factors own writable storage. Other arrays
    are independent read-only snapshots. Displacements use detector pixels
    and native axial sections; sampling pitches are in micrometres.
    """

    quadratures: Array
    noise_variance_factors: Array
    separation_matrices: Array
    phase_angles_rad: Array
    phase_policies: tuple[tuple[tuple[str, ...], ...], ...]
    frame_sums: Array
    equalization_gains: Array
    off_frame_sums: Array | None
    off_equalization_gains: Array | None
    off_quadratures: Array | None
    background_after: Array
    slope_after: Array
    sentinel_frames: tuple[tuple[int, int, int, int, int], ...]
    between_displacements_pixels: Array
    exposure_displacements_pixels: Array
    header_timestamps_after: Array | None
    trace: tuple[ModeEvent, ...]
    input_shape: tuple[int, ...]
    input_scale: float
    acquisition_mode: str
    storage_order: str
    dxy_um: float
    dz_um: float
    lateral_zoom: float
    axial_zoom: int
    resolved_settings: tuple[tuple[str, Any], ...]
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = REFERENCE


@dataclass(frozen=True)
class _UsedBands:
    shape: tuple[int, ...]
    orders: int
    lateral: float
    axial: int
    dxy: float
    dz: float
    scale: float
    mode: str
    reference: tuple[tuple[str, str], ...]
    quadratures: Array
    noise: Array


def validate_used(bands: AcquisitionBands) -> _UsedBands:
    """Validate only the acquisition fields consumed by downstream science."""
    input_shape = bands.input_shape
    if not issubclass(type(input_shape), tuple) or len(input_shape) != 6:
        raise AcquisitionModeError("bands input_shape requires a tuple of six dimensions")
    shape = tuple(integer(n, "bands dimension") for n in input_shape)
    t, d, p, z, y, x = shape
    mode = literal(bands.acquisition_mode, "bands acquisition_mode", ("2d", "3d"))
    if (mode == "2d" and z != 1) or (mode == "3d" and z < 2) or x < 2 or x % 2:
        raise AcquisitionModeError("bands dimensions disagree with acquisition_mode/even X")
    data = bands.quadratures
    if not issubclass(type(data), np.ndarray):
        raise AcquisitionModeError("bands quadratures require a six-axis complex128 NumPy array")
    data = np.asarray(data)
    if data.dtype != np.complex128 or data.ndim != 6:
        raise AcquisitionModeError("bands quadratures require a six-axis complex128 NumPy array")
    q = data.shape[2]
    orders = (q + 1) // 2
    if orders < 2 or q % 2 != 1 or q > p or data.shape != (t, d, q, z, y, x // 2 + 1):
        raise AcquisitionModeError("bands quadratures require odd Q<=P, O>=2 and matching shape")
    noise = bands.noise_variance_factors
    if not issubclass(type(noise), np.ndarray):
        raise AcquisitionModeError("bands noise variance factors must be a NumPy array")
    noise = np.asarray(noise)
    if noise.dtype != np.float64 or noise.shape != (t, d, orders):
        raise AcquisitionModeError("bands noise_variance_factors require float64 (T,D,O)")
    lateral = zoom(bands.lateral_zoom, y, x)
    axial = integer(bands.axial_zoom, "axial_zoom")
    dxy, dz = scalar(bands.dxy_um, "dxy_um", positive=True), scalar(bands.dz_um, "dz_um")
    if dz < 0 or (mode == "3d" and dz == 0):
        raise AcquisitionModeError("bands dz_um must be positive in 3d or nonnegative in 2d")
    scale = scalar(bands.input_scale, "input_scale", positive=True)
    if scale != 1 / (x * y * z * lateral**2 * axial * d):
        raise AcquisitionModeError("bands input_scale disagrees with acquisition normalization")
    revision, reference = bands.source_revision, bands.reference_sha256
    if type(revision) is not str or revision != "SVN307":
        raise AcquisitionModeError("bands source_revision must be the Python string SVN307")
    if (
        type(reference) is not tuple
        or len(reference) != len(REFERENCE)
        or any(
            type(pair) is not tuple
            or len(pair) != 2
            or any(type(value) is not str for value in pair)
            for pair in reference
        )
        or reference != REFERENCE
    ):
        raise AcquisitionModeError(
            "bands reference_sha256 must be the approved ordered tuple of Python string pairs"
        )
    for name, count in (
        ("native volume", x * y * z),
        ("padded volume", (x + 2) * y * z),
        ("half volume", (x // 2 + 1) * y * z),
        ("direction/z/phase count", d * z * p),
        ("declared on-frame count (T*D*Z*P)", t * d * z * p),
        ("quadrature/phase count", q * p),
        ("direction/order count", d * orders),
    ):
        signed(count, name)
    output_extents(shape, lateral, axial)
    extent(data.shape, 16)
    extent(noise.shape, 8)
    finite(data, "bands quadratures")
    finite(noise, "bands noise_variance_factors")
    if (noise <= 0).any():
        raise AcquisitionModeError("bands noise_variance_factors must be positive")
    return _UsedBands(shape, orders, lateral, axial, dxy, dz, scale, mode, reference, data, noise)


def _optics(
    wavelength: Any, na: Any, immersion: Any, required: bool
) -> tuple[int | None, float | None, float | None]:
    values = (wavelength, na, immersion)
    if required and any(v is None for v in values):
        raise AcquisitionModeError(
            "selected drift/off combination requires wavelength_nm, numerical_aperture "
            "and immersion_index"
        )
    wave = None if wavelength is None else integer(wavelength, "wavelength_nm")
    aperture = None if na is None else scalar(na, "numerical_aperture", positive=True)
    index = None if immersion is None else scalar(immersion, "immersion_index", positive=True)
    if wave is not None and wave > 32767:
        raise AcquisitionModeError("wavelength_nm exceeds signed short range")
    if index is not None and not 1 <= index <= 2:
        raise AcquisitionModeError("immersion_index must lie in [1,2]")
    if aperture is not None and aperture > min(2, 2 if index is None else index):
        raise AcquisitionModeError("numerical_aperture exceeds physical domain")
    return wave, aperture, index


def _combine(
    on: Array,
    off: Array,
    selectors: tuple[int, ...],
    *,
    cutoff: int,
    dxy: float,
    x: int,
    trace: list[ModeEvent],
    t: int,
    d: int,
    z: int,
) -> None:
    y = on.shape[-2]
    c2 = signed(cutoff * cutoff, "off cutoff square")
    xs = [signed(math.trunc(i / (x * dxy)), "off integer kx") for i in range(x // 2 + 1)]
    ys = [signed(math.trunc(float(i) / (y * dxy)), "off integer ky") for i in frequencies(y)]
    inside = np.empty((y, x // 2 + 1), dtype=np.bool_)
    for i, ky in enumerate(ys):
        for j, kx in enumerate(xs):
            r2 = signed(
                signed(kx * kx, "off kx square") + signed(ky * ky, "off ky square"),
                "off integer frequency square",
            )
            inside[i, j] = r2 <= c2
    nin, nout = int(inside.sum()), int((~inside).sum())
    if nin == 0 or nout == 0:
        raise AcquisitionModeError("off combination requires nonempty inside and outside cell sets")
    for m, selected in enumerate(selectors):
        if selected <= 0:
            continue
        slots = slice(0, 1) if m == 0 else slice(2 * m - 1, 2 * m + 1)
        b, f = on[slots, 0], off[slots, 0]
        bp, fp = np.sum(np.abs(b) ** 2, axis=0), np.sum(np.abs(f) ** 2, axis=0)
        bn, fn = float(bp[~inside].sum() / nout), float(fp[~inside].sum() / nout)
        bs, fs = float(bp[inside].sum() / nin - bn), float(fp[inside].sum() / nin - fn)
        finite((bn, fn, bs, fs), "off noise/signal statistics")
        if bn <= 0 or fn <= 0:
            raise AcquisitionModeError("off combination zero/nonpositive noise divisor")
        bclip, fclip = max(bs, 0.0), max(fs, 0.0)
        replaced = bclip == 0 and fclip == 0
        if replaced:
            bclip = fclip = 1.0
        u, v = math.sqrt(bclip) / bn, math.sqrt(fclip) / fn
        denominator = u + v
        finite((u, v, denominator), "off weight denominator")
        if denominator <= 0:
            raise AcquisitionModeError("off combination requires positive weight denominator")
        a, bweight = u / denominator, v / denominator
        on[slots, 0] = a * b + (1 if m == 0 else -1) * bweight * f
        finite(on[slots, 0], "off weighted result")
        event(
            trace,
            "off-combination",
            t,
            d,
            z,
            call_z=z,
            affected_z=0,
            order=m,
            cutoff_integer=cutoff,
            inside_count=nin,
            outside_count=nout,
            on_noise=bn,
            off_noise=fn,
            on_signal2_before_clip=bs,
            off_signal2_before_clip=fs,
            both_zero_replaced=replaced,
            on_scale=u,
            off_scale=v,
            denominator=denominator,
            on_fraction=a,
            off_fraction=bweight,
            quadratures_after=on[slots, 0],
        )


class _Camera:
    """Persistent camera maps, last on offset and actual load-order sentinel log."""

    def __init__(self, background: Array, slope: Array, alpha: float):
        self.background, self.slope, self.alpha = background, slope, alpha
        self.extra = 0.0
        self.sentinels: list[tuple[int, int, int, int, int]] = []

    def load(self, raw: Array, indices: tuple[int, int, int, int, int]) -> Array:
        frame = np.array(raw, dtype=np.float64, copy=True)
        if frame[-1, -1] == -1:
            frame[-1, -1] = frame[-1, -2]
            self.background[-1, -1] = self.background[-1, -2]
            self.slope[-1, -1] = 1
            append(self.sentinels, indices)
        frame = self.alpha * self.slope * (frame - self.background - self.extra)
        finite(frame, "camera correction")
        return frame


def _equalize(
    frames: Array,
    sums: Array,
    gains: Array,
    *,
    t: int,
    d: int,
    z: int,
    enabled: bool,
    share_z: bool,
    share_time: bool,
) -> None:
    values = frames.sum(axis=(-2, -1))
    finite(values, "frame sums")
    sums[t, d, :, z] = values
    if enabled:
        if (values == 0).any():
            raise AcquisitionModeError("equalization frame sums contain zero divisor")
        anchor = sums[0 if share_time else t, 0, 0, 0 if share_z else z]
        gains[t, d, :, z] = anchor / values
        frames *= gains[t, d, :, z, None, None]
        finite(frames, "equalization result")


def prepare_acquisition_bands(
    images: Any,
    *,
    acquisition_mode: str,
    dxy_um: Any,
    dz_um: Any,
    norders: Any,
    background: Any,
    lateral_zoom: Any,
    axial_zoom: Any,
    flatfield_slope: Any = None,
    exposure_background: Any = None,
    phases_rad: Any = None,
    phase_steps_rad: Any = None,
    edge_pixels: Any = 10,
    equalize: bool = True,
    equalize_z: bool = False,
    equalize_time: bool = False,
    off_exposures: Any = None,
    combine_off_orders: Any = None,
    storage_order: str = "direction-major",
    drift_between: bool = False,
    drift_within: bool = False,
    fit_drift: bool = False,
    adjust_phases: bool = False,
    drift_filter_fraction: Any = 0.0,
    wavelength_nm: Any = None,
    numerical_aperture: Any = None,
    immersion_index: Any = None,
    header_timestamps: Any = None,
    header_phases_rad: Any = None,
    linespacing_um: Any = None,
    phase_start_angle_rad: Any = 1.57193,
    negative_angle_step: bool = False,
) -> AcquisitionBands:
    """Prepare on/off acquisitions through camera, drift and phase separation.

    Parameters
    ----------
    images : numpy.ndarray
        Exact finite float32 samples, axes (T,D,P,Z,Y,X).
    acquisition_mode : {'2d', '3d'}
        Explicit dimensionality: native Z=1 for 2d, Z>=2 for 3d.
    dxy_um, dz_um : real scalar
        Detector pitches in micrometres; 2d permits dz=0 except in the prepass.
    norders : int
        Orders including zero, with 2*norders-1<=P.
    background : real scalar or numpy.ndarray
        Counts, scalar or (Y,X) map.
    lateral_zoom, axial_zoom : real scalar, int
        Safe enlargement with integral output extents; positive axial factor.
    flatfield_slope, exposure_background : numpy.ndarray or None, optional
        Multiplicative (Y,X) map and (T,D,P,Z) on offsets in counts.
    phases_rad, phase_steps_rad : numpy.ndarray or None, optional
        Declared (D,P) phases or higher-priority (D,) steps, in radians.
    edge_pixels : int, optional
        Additive edge width, -1 sine window, or below -1 bypass.
    equalize, equalize_z, equalize_time : bool, optional
        On sum equalization and independent z/time anchor sharing.
    off_exposures : numpy.ndarray or None, optional
        Raw (T,D,P,Z,N,Y,X) off frames, summed before edge treatment.
    combine_off_orders : numpy.ndarray or None, optional
        Signed32 (O,) selectors; positive selects literal plane-zero combination.
    storage_order : {'direction-major', 'z-major'}, optional
        Physical stream declaration controlling source drift routing.
    drift_between, drift_within, fit_drift, adjust_phases : bool, optional
        Select the source drift estimator, cubic fit and linked phase operations.
    drift_filter_fraction : real scalar, optional
        Positive values select the squared Gaussian high-pass factor.
    wavelength_nm, numerical_aperture, immersion_index : scalar or None, optional
        Explicit optics, required for selected estimation/statistics branches.
    header_timestamps, header_phases_rad : numpy.ndarray or None, optional
        Complete physical exposure stream, in one time unit and radians.
    linespacing_um, phase_start_angle_rad : real scalar or None, optional
        Linked-phase reciprocal spacing and first direction angle.
    negative_angle_step : bool, optional
        Use negative rather than positive pi/D linked-phase direction steps.

    Returns
    -------
    AcquisitionBands
        Native bands, per-time noise and owned stage diagnostics.

    Raises
    ------
    AcquisitionModeError
        Invalid declaration, unsafe source branch or failed numerical operation.
    """
    with operation():
        images, shape = raw_images(images)
        times, directions, phases, nz, ny, nx = shape
        acquisition_mode = literal(acquisition_mode, "acquisition_mode", ("2d", "3d"))
        two_d = acquisition_mode == "2d"
        if (two_d and nz != 1) or (not two_d and nz < 2):
            raise AcquisitionModeError("acquisition_mode requires native Z1 in 2d or Z>=2 in 3d")
        order = layout(storage_order)
        orders = integer(norders, "norders")
        slots = signed(2 * orders - 1, "quadrature count")
        if slots > phases:
            raise AcquisitionModeError("norders requires 2*norders-1<=P")
        signed(slots * phases, "quadrature/phase count")
        signed(directions * orders, "direction/order count")
        lateral, axial = zoom(lateral_zoom, ny, nx), integer(axial_zoom, "axial_zoom")
        output_extents(shape, lateral, axial)
        width = integer(edge_pixels, "edge_pixels", minimum=-(2**31))
        if width > min(nx, ny):
            raise AcquisitionModeError("edge_pixels exceeds lateral dimensions")
        dxy, dz = scalar(dxy_um, "dxy_um", positive=True), scalar(dz_um, "dz_um")
        if dz < 0 or (not two_d and dz == 0):
            raise AcquisitionModeError("dz_um requires positive 3d or nonnegative 2d pitch")
        for name, flag in (
            ("equalize", equalize),
            ("equalize_z", equalize_z),
            ("equalize_time", equalize_time),
            ("drift_between", drift_between),
            ("drift_within", drift_within),
            ("fit_drift", fit_drift),
            ("adjust_phases", adjust_phases),
            ("negative_angle_step", negative_angle_step),
        ):
            if not issubclass(type(flag), (bool, np.bool_)):
                raise AcquisitionModeError(f"{name} must be a boolean")
        hpf = scalar(drift_filter_fraction, "drift_filter_fraction")
        start_angle = scalar(phase_start_angle_rad, "phase_start_angle_rad")
        spacing = (
            None
            if linespacing_um is None
            else scalar(linespacing_um, "linespacing_um", positive=True)
        )
        off_exposures, n = raw_off(off_exposures, shape)
        selectors = (0,) * orders
        if combine_off_orders is not None:
            if orders > 25:
                raise AcquisitionModeError("combine_off_orders fixed allocation requires O<=25")
            stored = (
                np.asarray(combine_off_orders)
                if issubclass(type(combine_off_orders), np.ndarray)
                else None
            )
            if stored is None or stored.shape != (orders,) or stored.dtype.kind not in "iu":
                raise AcquisitionModeError(
                    "combine_off_orders requires an integer NumPy (O,) array"
                )
            selectors = tuple(integer(v, "combine_off_orders", minimum=-(2**31)) for v in stored)
        combine = any(v > 0 for v in selectors)
        if combine and n == 0:
            raise AcquisitionModeError("positive combine_off_orders requires off exposures")
        active_drift = drift_between or drift_within
        prepass = active_drift and order == "direction-major"
        if active_drift and order == "z-major" and directions > 1:
            raise AcquisitionModeError("fast/z-major drift with D>1 reads uninitialized vectors")
        if drift_within and not two_d and order == "z-major":
            raise AcquisitionModeError(
                "fast/z-major within-3d reads uninitialized driftlist, including D1"
            )
        if prepass and (nx < 10 or ny < 10):
            raise AcquisitionModeError("drift prepass fixed10 edges require X,Y>=10")
        if prepass and dz <= 0:
            raise AcquisitionModeError("drift prepass requires positive dz axial pitch")
        if prepass and n > ny + 1:
            raise AcquisitionModeError("drift prepass off loop is nonterminating for N>Y+1")
        if drift_within and two_d and n == 0:
            raise AcquisitionModeError(
                "within-2d default reference is uninitialized without off exposures (N>0)"
            )
        fitting = drift_within and (not two_d or fit_drift)
        linked = drift_within and adjust_phases
        if fitting and not adjust_phases:
            raise AcquisitionModeError(
                "fitted within drift requires phase flag for timestamp allocation"
            )
        if fitting and (phases if two_d else directions) < 4:
            raise AcquisitionModeError("cubic fit requires four allocated points and metadata")
        if fitting and (header_timestamps is None or header_phases_rad is None):
            raise AcquisitionModeError("fitted drift requires timestamp and phase metadata")
        if linked and (header_phases_rad is None or spacing is None):
            raise AcquisitionModeError(
                "adjusted phases require header_phases_rad and linespacing_um"
            )
        wave, na, immersion = _optics(
            wavelength_nm,
            numerical_aperture,
            immersion_index,
            prepass or (drift_within and two_d) or combine,
        )
        # Check every actual owned diagnostic extent before reading raw pixels.
        qshape = (times, directions, slots, nz, ny, nx // 2 + 1)
        for sh, size in (
            (qshape, 16),
            ((times, directions, nz, slots, phases), 8),
            ((times, directions, nz, phases), 8),
            ((times, directions, orders), 8),
            (shape[:4], 8),
            ((times, directions, 3), 8),
            ((times, directions, nz, phases, 2), 8),
        ):
            extent(sh, size)
        fcount = signed(times * directions * nz * phases * (n + 1), "metadata exposure count")
        array_metadata(images, "images", shape, raw=True)
        if off_exposures is not None:
            array_metadata(off_exposures, "off_exposures", off_exposures.shape, raw=True)
        background_setting: str | float
        if issubclass(type(background), np.ndarray):
            bmap = real_array(background, "background", (ny, nx))
            background_setting = "map"
        else:
            background_setting = scalar(background, "background")
            bmap = np.full((ny, nx), background_setting)
        smap = (
            np.ones((ny, nx))
            if flatfield_slope is None
            else real_array(flatfield_slope, "flatfield_slope", (ny, nx))
        )
        extras = (
            None
            if exposure_background is None
            else real_array(exposure_background, "exposure_background", shape[:4])
        )
        supplied = (
            None
            if phases_rad is None
            else real_array(phases_rad, "phases_rad", (directions, phases))
        )
        steps = (
            None
            if phase_steps_rad is None
            else real_array(phase_steps_rad, "phase_steps_rad", (directions,))
        )
        if steps is not None and directions > 3:
            raise AcquisitionModeError("phase_steps_rad uses a fixed three-float allocation; D<=3")
        clock = (
            None
            if header_timestamps is None
            else real_array(header_timestamps, "header_timestamps", (fcount,))
        )
        header_phase = (
            None
            if header_phases_rad is None
            else real_array(header_phases_rad, "header_phases_rad", (fcount,))
        )
        policy = "steps" if steps is not None else "supplied" if supplied is not None else "uniform"
        angles = (
            np.tile(2 * np.pi * np.arange(phases) / phases, (directions, 1))
            if supplied is None
            else supplied.copy()
        )
        if steps is not None:
            angles = steps[:, None] * np.arange(phases)[None, :]
        finite(angles, "declared phases")
        alpha = 1 / (nx * ny * nz * lateral**2 * axial * directions)
        if not math.isfinite(alpha) or alpha <= 0:
            raise AcquisitionModeError("input scale alpha is zero or nonfinite")
        camera = _Camera(bmap, smap, alpha)
        quadratures = np.empty(qshape, dtype=np.complex128)
        off_q = None if not n else np.empty(qshape, dtype=np.complex128)
        sums, gains = np.empty(shape[:4]), np.ones(shape[:4])
        off_sums, off_gains = (None, None) if not n else (np.empty(shape[:4]), np.ones(shape[:4]))
        matrices = np.empty((times, directions, nz, slots, phases))
        phase_angles = np.empty((times, directions, nz, phases))
        noise = np.empty((times, directions, orders))
        displacements = np.zeros((times, directions, 3))
        exposure_displacements = np.zeros((times, directions, nz, phases, 2))
        trace: list[ModeEvent] = []
        policies: list[tuple[tuple[str, ...], ...]] = []
        cutoff = 0
        if combine:
            assert wave is not None and na is not None
            cutoff = signed(math.trunc(2 * na / (wave / 1000)), "off optical cutoff")
        for t in range(times):
            if prepass:
                assert wave is not None and na is not None and immersion is not None
                displacements[t] = between(
                    images,
                    off_exposures,
                    bmap,
                    t=t,
                    dxy=dxy,
                    dz=dz,
                    wavelength=wave,
                    na=na,
                    immersion=immersion,
                    hpf=hpf,
                    trace=trace,
                )
            if drift_within and not two_d:
                assert clock is not None
                samples = np.array(
                    [clock[d * nz * phases + (nz * phases) // 2] for d in range(directions)]
                )
                evaluated = cubic(
                    samples,
                    clock[: directions * nz * phases],
                    displacements[t, :, :2],
                    scope="between",
                    trace=trace,
                    t=t,
                    d=0,
                )
                exposure_displacements[t] = evaluated.reshape(directions, nz, phases, 2)
                for d in range(1, directions):
                    exposure_displacements[t, d] -= displacements[t, d, :2]
            time_policies = []
            for d in range(directions):
                direction_policies = []
                for z in range(nz):
                    on = np.empty((phases, ny, nx))
                    off = None if not n else np.zeros((phases, ny, nx))
                    for p in range(phases):
                        if off is not None:
                            assert off_exposures is not None
                            for e in range(n):
                                off[p] += camera.load(off_exposures[t, d, p, z, e], (t, d, z, p, e))
                            _edge(off[p], width)
                        camera.extra = 0.0 if extras is None else float(extras[t, d, p, z])
                        on[p] = camera.load(images[t, d, p, z], (t, d, z, p, n))
                        _edge(on[p], width)
                    _equalize(
                        on,
                        sums,
                        gains,
                        t=t,
                        d=d,
                        z=z,
                        enabled=equalize,
                        share_z=equalize_z,
                        share_time=equalize_time,
                    )
                    if off is not None:
                        assert off_sums is not None and off_gains is not None
                        _equalize(
                            off,
                            off_sums,
                            off_gains,
                            t=t,
                            d=d,
                            z=z,
                            enabled=equalize and n > 1,
                            share_z=equalize_z,
                            share_time=equalize_time,
                        )
                    on_fft = np.fft.rfft2(on, axes=(-2, -1))
                    off_fft = None if off is None else np.fft.rfft2(off, axes=(-2, -1))
                    finite(on_fft, "on lateral transform")
                    if off_fft is not None:
                        finite(off_fft, "off lateral transform")
                    if drift_within and two_d:
                        assert off_fft is not None and na is not None and wave is not None
                        ref = (on_fft[0] + off_fft[0])[None]
                        for p in range(phases):
                            shift = correlation(
                                ref,
                                (on_fft[p] + off_fft[p])[None],
                                x=nx,
                                dxy=dxy,
                                radius=2 * na / (wave / 1000),
                                hpf=hpf,
                                exponent=0.5,
                                trace=trace,
                                t=t,
                                d=d,
                                scope="within",
                                moving_index=p,
                                z_index=z,
                            )
                            exposure_displacements[t, d, z, p] = shift[:2]
                        if fit_drift:
                            assert clock is not None
                            samples = np.array(
                                [
                                    clock[d * phases * (n + 1) + p * (n + 1) + n]
                                    for p in range(phases)
                                ]
                            )
                            exposure_displacements[t, d, z] = cubic(
                                samples,
                                samples,
                                exposure_displacements[t, d, z],
                                scope="within",
                                trace=trace,
                                t=t,
                                d=d,
                            )
                    if drift_within:
                        for p in range(phases):
                            shift = exposure_displacements[t, d, z, p]
                            multiplier = ramp(shift, 1, ny, nx)[0]
                            on_fft[p] *= multiplier
                            if off_fft is not None:
                                off_fft[p] *= multiplier
                            event(
                                trace,
                                "exposure-correction",
                                t,
                                d,
                                z,
                                p,
                                displacement_xy=shift,
                                phase_multiplier=multiplier,
                            )
                    selected_angles = angles[d].copy()
                    selected_policy = policy
                    if linked:
                        assert spacing is not None and header_phase is not None
                        theta = (
                            start_angle
                            + d * (-1 if negative_angle_step else 1) * np.pi / directions
                        )
                        phase_vector = np.array([math.cos(theta), math.sin(theta)]) / spacing
                        base = (
                            np.array(
                                [
                                    header_phase[d * phases * (n + 1) + p * (n + 1)]
                                    for p in range(phases)
                                ]
                            )
                            if two_d
                            else 2 * np.pi * np.arange(phases) / phases
                        )
                        selected_angles = base + 2 * np.pi * dxy * (
                            exposure_displacements[t, d, z] @ phase_vector
                        )
                        selected_policy = "drift"
                    rows, variance = _phase_matrices(
                        selected_angles[None], orders, selected_policy != "uniform"
                    )
                    row, variance_row = rows[0], variance[0]
                    matrices[t, d, z], phase_angles[t, d, z], noise[t, d] = (
                        row,
                        selected_angles,
                        variance_row,
                    )
                    direction_policies.append(selected_policy)
                    event(
                        trace,
                        "phase-design",
                        t,
                        d,
                        z,
                        policy=selected_policy,
                        phases_rad=selected_angles,
                        separation_matrix=row,
                        noise_variance_factors=variance_row,
                    )
                    quadratures[t, d, :, z, :, :-1] = np.einsum(
                        "qp,pyx->qyx", row, on_fft[..., :-1]
                    )
                    quadratures[t, d, :, z, :, -1] = on_fft[:slots, :, -1]
                    if off_q is not None and off_fft is not None:
                        off_q[t, d, :, z, :, :-1] = np.einsum("qp,pyx->qyx", row, off_fft[..., :-1])
                        off_q[t, d, :, z, :, -1] = off_fft[:slots, :, -1]
                        if combine:
                            _combine(
                                quadratures[t, d],
                                off_q[t, d],
                                selectors,
                                cutoff=cutoff,
                                dxy=dxy,
                                x=nx,
                                trace=trace,
                                t=t,
                                d=d,
                                z=z,
                            )
                if not two_d:
                    quadratures[t, d] = np.fft.fft(quadratures[t, d], axis=1)
                if drift_between and d > 0:
                    multiplier = ramp(displacements[t, d], nz, ny, nx)
                    quadratures[t, d] *= multiplier[None]
                    event(
                        trace,
                        "between-correction",
                        t,
                        d,
                        displacement_xyz=displacements[t, d],
                        phase_multiplier=multiplier,
                    )
                time_policies.append(tuple(direction_policies))
            policies.append(tuple(time_policies))
        resolved = dict(
            acquisition_mode=acquisition_mode,
            dxy_um=dxy,
            dz_um=dz,
            norders=orders,
            background=background_setting,
            lateral_zoom=lateral,
            axial_zoom=axial,
            phases_rad=None
            if supplied is None
            else tuple(tuple(float(v) for v in row) for row in supplied),
            phase_steps_rad=None if steps is None else tuple(float(v) for v in steps),
            edge_pixels=width,
            equalize=bool(equalize),
            equalize_z=bool(equalize_z),
            equalize_time=bool(equalize_time),
            combine_off_orders=None if combine_off_orders is None else selectors,
            storage_order=order,
            drift_between=bool(drift_between),
            drift_within=bool(drift_within),
            fit_drift=bool(fit_drift),
            adjust_phases=bool(adjust_phases),
            drift_filter_fraction=hpf,
            wavelength_nm=wave,
            numerical_aperture=na,
            immersion_index=immersion,
            linespacing_um=spacing,
            phase_start_angle_rad=start_angle,
            negative_angle_step=bool(negative_angle_step),
            n_off_exposures=n,
        )
        return AcquisitionBands(
            owned(quadratures, writable=True),
            owned(noise, writable=True),
            owned(matrices),
            owned(phase_angles),
            tuple(policies),
            owned(sums),
            owned(gains),
            None if off_sums is None else owned(off_sums),
            None if off_gains is None else owned(off_gains),
            None if off_q is None else owned(off_q),
            owned(bmap),
            owned(smap),
            tuple(camera.sentinels),
            owned(displacements),
            owned(exposure_displacements),
            None if clock is None else owned(clock),
            tuple(trace),
            shape,
            alpha,
            acquisition_mode,
            order,
            dxy,
            dz,
            lateral,
            axial,
            tuple(resolved.items()),
        )
