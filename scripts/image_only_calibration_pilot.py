"""Finite image-only, fixed-clear-pupil calibration trial.

The source weights are electrons; fitted brightness is reference-flat-relative.
Fit-local detection kernels factor the complete finite optical sum, without a
spatial cutoff. No acquisition, random stream, persistence or recovery promise
is supplied here.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, NoReturn, cast

import numpy as np
import scipy
from numpy.typing import NDArray
from scipy import ndimage, optimize, special
from scripts import simulation_optics as optics
from scripts.simulation_sources import make_sources

from simrecon import ScalarCameraEstimate, SimreconError

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
_D = (0.125, 0.080, 0.080)
_F = (8, 8, 8)
_A = 0.050
_K0 = Fraction(1.515) / Fraction(0.488)
_EPS = np.finfo(np.float64).eps
_RANGE = "image_only_calibration_pilot_range"
_KNOWN = {_RANGE, "simulation_source_range", "simulation_optics_range"}


@dataclass(frozen=True)
class PilotCandidate:
    """Independent physical parameters and represented one-electron masses."""

    centers_um_zyx: Real
    brightness_relative: Real
    carriers_yx_per_um: Real
    phases_rad: Real
    beam_amplitudes: Real
    occupied_counts: tuple[int, ...]
    stored_unit_masses_e: Real


@dataclass(frozen=True)
class PilotScore:
    """One actual successful, infeasible or failed training attempt."""

    stage: str
    pupil_order: int
    candidate: PilotCandidate | None
    objective: float | None
    outcome: str


@dataclass(frozen=True)
class PilotCenterAttempt:
    """One ordered center poll, including attempts without optical work."""

    bead_index: int
    axis_index: int
    sign: int
    outcome: str


@dataclass(frozen=True)
class CalibrationPilotResult:
    """Finite search evidence, frozen parameters and independent held-out checks."""

    status: str
    stage: str
    message: str
    failure_code: str | None
    detector_shape_zyx: tuple[int, ...]
    origin_um_zyx: tuple[float, ...]
    camera_source: str
    blank_counts: float
    contrast_counts: float
    initial_candidate: PilotCandidate | None
    frozen_candidate: PilotCandidate | None
    objective_trace: tuple[PilotScore, ...]
    optimizer_status: int | None
    optimizer_message: str | None
    optimizer_nfev: int | None
    optimizer_nit: int | None
    center_attempts: tuple[PilotCenterAttempt, ...]
    training_objectives_q128_q256_q512: tuple[float | None, ...]
    heldout_prediction: Real | None
    heldout_residual_mean: Real | None
    heldout_residual_rms: Real | None


def _invalid(message: str) -> NoReturn:
    raise SimreconError("invalid_image_only_calibration_pilot", message)


def _range(message: str) -> NoReturn:
    raise SimreconError(_RANGE, message)


def _copy(value: Any) -> Real:
    return np.array(value, dtype=np.float64, order="C", copy=True)


def _snapshot(candidate: PilotCandidate) -> PilotCandidate:
    return PilotCandidate(
        _copy(candidate.centers_um_zyx),
        _copy(candidate.brightness_relative),
        _copy(candidate.carriers_yx_per_um),
        _copy(candidate.phases_rad),
        _copy(candidate.beam_amplitudes),
        candidate.occupied_counts,
        _copy(candidate.stored_unit_masses_e),
    )


def _array(value: Any, name: str) -> Real:
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        _invalid(f"{name} must be a plain real numeric ndarray")
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = _copy(value)
    if not np.isfinite(result).all():
        _invalid(f"{name} must be finite before and after float64 conversion")
    return result


def _number(value: Any, name: str) -> float:
    if type(value) not in (int, float):
        _invalid(f"{name} must be a plain built-in real number")
    try:
        result = float(value)
    except OverflowError:
        _invalid(f"{name} cannot normalize to float64")
    if not math.isfinite(result):
        _invalid(f"{name} must be finite")
    return result


def _finite(value: Real, operation: str) -> Real:
    if not np.isfinite(value).all():
        _range(f"nonfinite {operation}")
    return value


def _correct(raw: Real, blank: float, contrast: float) -> Real:
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        return _finite((raw - blank) / contrast, "camera correction")


def _upper(n: int, spacing: float) -> float:
    exact = n * Fraction(spacing) - Fraction(_A)
    value = float(exact)
    return math.nextafter(value, -math.inf) if Fraction(value) > exact else value


def _feasible(centers: Real, shape: tuple[int, ...]) -> bool:
    for center in centers:
        for c, n, d in zip(center, shape, _D, strict=True):
            if Fraction(float(c)) < Fraction(_A) or Fraction(float(c)) + Fraction(
                _A
            ) > n * Fraction(d):
                return False
    return all(
        sum((Fraction(float(x)) - Fraction(float(y))) ** 2 for x, y in zip(a, b, strict=True))
        >= (2 * Fraction(_A)) ** 2
        for a, b in itertools.combinations(centers, 2)
    )


def _initialize(y: Real) -> tuple[Real, Real, str] | None:
    smooth = ndimage.gaussian_filter(
        y, sigma=(1, 1, 1), order=0, radius=4, mode="constant", cval=0.0, output=np.float64
    )
    _finite(smooth, "Gaussian initialization")
    available = np.ones(y.shape, dtype=bool)
    centers, maxima, windows = [], [], []
    clipped, clamped = 0, 0
    for _ in range(3):
        eligible = np.where(available, smooth, -np.inf)
        peak = np.unravel_index(int(np.argmax(eligible)), y.shape)
        if eligible[peak] <= 0:
            return None
        # Exact normalized geometry decides closed suppression, including ties.
        # A small integer offset stencil suffices; it is not an image mask.
        for delta in itertools.product(
            *(range(-math.ceil(0.5 / d), math.ceil(0.5 / d) + 1) for d in _D)
        ):
            if sum((i * Fraction(d)) ** 2 for i, d in zip(delta, _D, strict=True)) <= Fraction(
                1, 4
            ):
                site = tuple(int(p) + i for p, i in zip(peak, delta, strict=True))
                if all(0 <= i < n for i, n in zip(site, y.shape, strict=True)):
                    available[site] = False
        window = tuple(
            slice(max(0, int(p) - r), min(n, int(p) + r + 1))
            for p, r, n in zip(peak, (2, 3, 3), y.shape, strict=True)
        )
        clipped += int(
            any(
                int(p) - r < 0 or int(p) + r >= n
                for p, r, n in zip(peak, (2, 3, 3), y.shape, strict=True)
            )
        )
        windows.append(window)
        weights = np.maximum(y[window], 0)
        maximum = float(np.max(weights))
        if maximum == 0:
            return None
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            # Scaling cancels in the centroid quotient. At least one weight is
            # exactly one; at most 245 weights and native-index coordinates keep
            # both mass and physical moments finite, even for extreme counts.
            weights /= maximum
            mass = float(np.sum(weights, dtype=np.float64))
            center = []
            for axis, d in enumerate(_D):
                coordinate = np.arange(window[axis].start, window[axis].stop)
                view = [1, 1, 1]
                view[axis] = len(coordinate)
                raw = float(np.sum(weights * ((coordinate + 0.5) * d).reshape(view)) / mass)
                bounded = min(max(raw, _A), _upper(y.shape[axis], d))
                clamped += int(bounded != raw)
                center.append(bounded)
        centers.append(center)
        maxima.append(maximum)
    c = _copy(centers)
    if not _feasible(c, y.shape):
        return None
    overlap = sum(
        all(max(a.start, b.start) < min(a.stop, b.stop) for a, b in zip(left, right, strict=True))
        for left, right in itertools.combinations(windows, 2)
    )
    return (
        c,
        _copy(maxima),
        f"SciPy {scipy.__version__}; clipped windows={clipped}, "
        f"overlapping windows={overlap}, clamped centroid coordinates={clamped}",
    )


@dataclass
class _Harmonics:
    carrier: tuple[float, float]
    dc: Real
    first: Complex
    axial_first: Complex
    c2: Real
    s2: Real
    phase_error: float


class _Profile:
    def __init__(self, center: Real, shape: tuple[int, ...]) -> None:
        catalogue = np.array([[*center, _A, 1.0]])
        source = make_sources(
            catalogue,
            detector_shape_zyx=shape,
            detector_spacing_um_zyx=_D,
            source_refinement_zyx=_F,
        )
        self.sites = np.argwhere(source != 0)
        self.count = len(self.sites)
        self.weight = float(source[tuple(self.sites[0])])
        self.mass = float(Fraction(self.weight) * self.count)
        # Retain sparse represented weights, not the much larger source grid.
        self.kernels: dict[int, tuple[Real, float]] = {}
        self.harmonics: dict[tuple[int, int], _Harmonics] = {}


class _Pupil:
    """Shared detection geometry for one Q, independent of the fitted illumination.

    The dependency's density evaluator and error bound are used unchanged.
    Identical represented radii share evaluations; no geometric quantization is
    introduced. Each source/pixel pair still contributes to the complete sum.
    """

    def __init__(self, shape: tuple[int, ...], order: int) -> None:
        self.shape = shape
        source_shape = tuple(n * f for n, f in zip(shape, _F, strict=True))
        nodes, weights = special.roots_legendre(order)
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            nodes, weights = (nodes + 1) / 2, weights / 2
            frequency = 1.4 / 0.525
            beta = 1.4 / 1.515
            radial = 2 * math.pi * frequency * np.sqrt(nodes)
            axial = (
                -2
                * math.pi
                * (1.515 / 0.525)
                * beta**2
                * nodes
                / (np.sqrt(1 - beta**2 * nodes) + 1)
            )
            axial -= axial[0]
        self.model = optics._Optics(
            _D,
            _F,
            (2, 2),
            shape,
            np.array([1.0, 0.0, 0.0]),
            [],
            [],
            [],
            np.ones((1, 1), dtype=np.complex128),
            radial,
            axial,
            weights,
        )
        radii = []
        for ly, lx in itertools.product(range(2), repeat=2):
            y = optics._displacements(
                range(-(source_shape[1] - 1), source_shape[1]),
                _D[1],
                8,
                Fraction(8 * (2 * ly + 1) - 2, 4),
            )
            x = optics._displacements(
                range(-(source_shape[2] - 1), source_shape[2]),
                _D[2],
                8,
                Fraction(8 * (2 * lx + 1) - 2, 4),
            )
            radii.append(np.hypot(y[:, None], x[None, :]))
        self.radii, inverse = np.unique(np.stack(radii), return_inverse=True)
        self.indices = inverse.reshape((4, *radii[0].shape))
        self.zero = (source_shape[1] - 1, source_shape[2] - 1)
        self.density: dict[Fraction, tuple[Real, float]] = {}

    def kernel(self, profile: _Profile) -> tuple[Real, float]:
        nz, ny, nx = self.shape
        result = np.zeros((nz, profile.count, ny, nx))
        error = 0.0
        iy, ix = 8 * np.arange(ny), 8 * np.arange(nx)
        for j, (jz, jy, jx) in enumerate(profile.sites):
            yy = iy - jy + self.zero[0]
            xx = ix - jx + self.zero[1]
            lookup = self.indices[:, yy[:, None], xx[None, :]]
            for k in range(nz):
                exact_d = abs(Fraction(_D[0]) * (2 * int(jz) + 1 - 8 * (2 * k + 1)) / 16)
                if exact_d not in self.density:
                    # density updates its certification state; retain the bound
                    # with the cached values, never a reset or weakened bound.
                    with np.errstate(
                        over="ignore", under="ignore", invalid="ignore", divide="ignore"
                    ):
                        values = self.model.density(self.radii, float(exact_d))
                    self.density[exact_d] = values, self.model.error
                values, bound = self.density[exact_d]
                result[k, j] = np.mean(values[lookup], axis=0)
                error = max(error, bound)
        return result, error


class _Prediction:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape
        self.profiles: dict[tuple[float, ...], _Profile] = {}
        self.pupils: dict[int, _Pupil] = {}

    def profile(self, center: Real) -> _Profile:
        key = tuple(float(v) for v in center)
        if key not in self.profiles:
            self.profiles[key] = _Profile(center, self.shape)
        return self.profiles[key]

    def retain(self, candidate: PilotCandidate) -> None:
        # Neither rejected polls nor old quadrature rules need retained storage.
        keys = {tuple(float(v) for v in c) for c in candidate.centers_um_zyx}
        self.profiles = {k: p for k, p in self.profiles.items() if k in keys}

    def candidate(
        self, centers: Real, brightness: Real, carriers: Real, phases: Real, beams: Real
    ) -> PilotCandidate:
        profiles = [self.profile(c) for c in centers]
        return PilotCandidate(
            _copy(centers),
            _copy(brightness),
            _copy(carriers),
            _copy(phases),
            _copy(beams),
            tuple(p.count for p in profiles),
            _copy([p.mass for p in profiles]),
        )

    def unit(
        self, profile: _Profile, q: Real, phases: Real, beams: Real, order: int, slot: int = -1
    ) -> Real:
        if order not in self.pupils:
            self.pupils.clear()
            for p in self.profiles.values():
                p.kernels.clear()
                p.harmonics.clear()
            self.pupils[order] = _Pupil(self.shape, order)
        pupil = self.pupils[order]
        if order not in profile.kernels:
            profile.kernels[order] = pupil.kernel(profile)
        kernel, density_error = profile.kernels[order]
        key = (order, slot)
        carrier = (float(q[0]), float(q[1]))
        if key not in profile.harmonics or profile.harmonics[key].carrier != carrier:
            squares = [sum((Fraction(float(v)) ** 2 for v in q), Fraction(0))]
            kappa, kappa_error = optics._axial_frequencies(_K0, squares)
            model = replace(pupil.model, kappa=kappa, kappa_error=kappa_error, phase_error=0.0)
            y = optics._wave(optics._turns(float(q[0]), _D[1], 8, self.shape[1] * 8))
            x = optics._wave(optics._turns(float(q[1]), _D[2], 8, self.shape[2] * 8))
            lateral = y[profile.sites[:, 1]] * x[profile.sites[:, 2]]
            axial = np.array(
                [
                    [
                        model.axial_wave(
                            Fraction(_D[0]) * (2 * int(jz) + 1 - 8 * (2 * k + 1)) / 16, 0
                        )
                        for jz in profile.sites[:, 0]
                    ]
                    for k in range(self.shape[0])
                ],
                dtype=np.complex128,
            )
            with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
                dc = np.sum(kernel, axis=1)
                c1 = np.einsum("kj,kjyx->kyx", axial.real * lateral.real, kernel)
                s1 = np.einsum("kj,kjyx->kyx", axial.real * lateral.imag, kernel)
                # sin(theta-alpha) gives the unequal-side, source-minus-focus term.
                ac = np.einsum("kj,kjyx->kyx", axial.imag * lateral.real, kernel)
                ass = np.einsum("kj,kjyx->kyx", axial.imag * lateral.imag, kernel)
                second = lateral**2
                c2 = np.einsum("j,kjyx->kyx", second.real, kernel)
                s2 = np.einsum("j,kjyx->kyx", second.imag, kernel)
            # Complex pairs retain cosine and sine responses. The cache is
            # candidate-derived, bounded to the current carrier per orientation.
            profile.harmonics[key] = _Harmonics(
                carrier, dc, c1 + 1j * s1, ac + 1j * ass, c2, s2, model.phase_error
            )
        harmonics = profile.harmonics[key]
        dc, first, axial_first = harmonics.dc, harmonics.first, harmonics.axial_first
        c2, s2, phase_error = harmonics.c2, harmonics.s2, harmonics.phase_error
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            normalized = beams / float(np.max(beams))
            normalized /= np.linalg.norm(normalized)
            a0, plus, minus = normalized
            phase = np.cos(phases) + 1j * np.sin(phases)
            phase = phase[:, None, None, None]
            result = np.broadcast_to(dc, (len(phases), *self.shape)).copy()
            result += 2 * a0 * (plus + minus) * (phase.real * first.real - phase.imag * first.imag)
            result += (
                2
                * a0
                * (plus - minus)
                * (phase.real * axial_first.imag + phase.imag * axial_first.real)
            )
            result += 2 * plus * minus * ((phase**2).real * c2 - (phase**2).imag * s2)
            peak = float(np.max(dc))
            operations = profile.count * math.prod(self.shape) * 4
            error = (
                3 * density_error * profile.count
                + phase_error * peak
                + 512 * _EPS * (1 + math.log2(max(2, operations))) * profile.count
            )
            return optics._scale_output(
                result,
                peak,
                (profile.weight, _D[1], _D[2], math.pi, 1.4 / 0.525, 1.4 / 0.525),
                error,
            )

    def predict(self, candidate: PilotCandidate, order: int, count: int = 9) -> tuple[Real, Real]:
        central = np.zeros(self.shape)
        structured = np.zeros((3, count, *self.shape))
        for center, brightness in zip(
            candidate.centers_um_zyx, candidate.brightness_relative, strict=True
        ):
            profile = self.profile(center)
            unit = self.unit(profile, np.zeros(2), np.zeros(1), np.array([1.0, 0.0, 0.0]), order)[0]
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                central += brightness * unit
            for o in range(3):
                unit = self.unit(
                    profile,
                    candidate.carriers_yx_per_um[o],
                    candidate.phases_rad[o, :count],
                    candidate.beam_amplitudes,
                    order,
                    o,
                )
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    structured[o] += brightness * unit
        return _finite(central, "central prediction"), _finite(structured, "structured prediction")


def _decode(x: Real, initial: PilotCandidate, prediction: _Prediction) -> PilotCandidate | None:
    gamma, eta = x[3:5] * (math.pi / 2)
    sine = 0.0 if x[3] == 0 else math.sin(gamma)
    beams = np.array(
        [
            0.0 if x[3] == 1 else math.cos(gamma),
            0.0 if x[4] == 1 else sine * math.cos(eta),
            0.0 if x[4] == 0 else sine * math.sin(eta),
        ]
    )
    q = np.array(
        [
            [
                x[5 + 2 * o] * (1.515 / 0.488) * math.sin(x[6 + 2 * o] * math.pi),
                x[5 + 2 * o] * (1.515 / 0.488) * math.cos(x[6 + 2 * o] * math.pi),
            ]
            for o in range(3)
        ]
    )
    if any(sum(Fraction(float(v)) ** 2 for v in row) > _K0**2 for row in q):
        return None
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        brightness = _finite(x[:3] * initial.brightness_relative, "candidate brightness")
    return prediction.candidate(
        initial.centers_um_zyx, brightness, q, x[11:].reshape(3, 9) * (2 * math.pi), beams
    )


def fit_small_pilot(
    central_counts: Any,
    *,
    structured_counts: Any,
    heldout_counts: Any,
    camera_estimate: Any,
    origin_um_zyx: Any,
) -> CalibrationPilotResult:
    """Fit the adopted finite procedure from primary-camera images only.

    Parameters
    ----------
    central_counts : numpy.ndarray
        Plain finite real central-only raw image, shaped (z,y,x).
    structured_counts : numpy.ndarray
        Raw training images, shaped (3,9,z,y,x).
    heldout_counts : numpy.ndarray
        Independent raw check images, shaped (3,5,z,y,x).
    camera_estimate : ScalarCameraEstimate
        Estimated blank, contrast and opaque source identity.
    origin_um_zyx : tuple of float
        Known finite box corner in micrometres; fitted coordinates are local.

    Returns
    -------
    CalibrationPilotResult
        Independent frozen records of actual work and available outputs.

    Raises
    ------
    SimreconError
        Invalid public inputs; unrelated dependency errors propagate unchanged.
    MemoryError
        Actual allocation failure, without translation to a numerical result.
    """
    central = _array(central_counts, "central_counts")
    structured = _array(structured_counts, "structured_counts")
    heldout = _array(heldout_counts, "heldout_counts")
    shape = central.shape
    if central.ndim != 3 or any(
        n == 0 or n * Fraction(d) < Fraction(0.100) for n, d in zip(shape, _D, strict=False)
    ):
        _invalid("central image must have three nonempty axes at least 0.100 micrometres long")
    if structured.shape != (3, 9, *shape) or heldout.shape != (3, 5, *shape):
        _invalid("structured and heldout shapes must be (3,9,*N) and (3,5,*N)")
    if not isinstance(camera_estimate, ScalarCameraEstimate):
        _invalid("camera_estimate must be a ScalarCameraEstimate")
    means = camera_estimate.means_counts
    if (
        type(means) is not np.ndarray
        or means.dtype != np.dtype(np.float64)
        or not means.dtype.isnative
        or means.shape != (3,)
        or not np.isfinite(means).all()
    ):
        _invalid("camera means must be a plain finite native float64 array of shape (3,)")
    blank = float(_copy(means)[1])
    contrast = _number(camera_estimate.contrast_counts, "contrast_counts")
    source = camera_estimate.source
    if not isinstance(source, str) or not source.strip():
        _invalid("camera source must be a nonblank string")
    if not isinstance(origin_um_zyx, tuple) or len(origin_um_zyx) != 3:
        _invalid("origin must be a length-three tuple")
    origin = tuple(_number(v, "origin") for v in origin_um_zyx)
    result = CalibrationPilotResult(
        "normalization_unavailable",
        "normalization",
        "nonpositive estimated contrast",
        None,
        shape,
        origin,
        source,
        blank,
        contrast,
        None,
        None,
        (),
        None,
        None,
        None,
        None,
        (),
        (None, None, None),
        None,
        None,
        None,
    )
    if contrast <= 0:
        return result
    trace: list[PilotScore] = []
    attempts: list[PilotCenterAttempt] = []
    objectives: list[float | None] = [None, None, None]
    stage = "normalization"
    best: PilotCandidate | None = None
    best_cost = math.inf
    prediction = _Prediction(shape)
    init_message = ""

    def score(
        build: Callable[[], PilotCandidate | None], score_stage: str, order: int
    ) -> tuple[PilotCandidate | None, float]:
        # Construction and scoring share one failure boundary: a callback or
        # poll produces one trace record even when its profile/decoding fails.
        try:
            candidate = build()
            if candidate is None:
                trace.append(PilotScore(score_stage, order, None, None, "infeasible"))
                return None, math.inf
            cp, sp = prediction.predict(candidate, order)
            with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
                residual_c, residual_s = y - cp, training - sp
                loss = float(
                    (
                        np.sum(residual_c**2, dtype=np.float64)
                        + np.sum(residual_s**2, dtype=np.float64)
                    )
                    / (2 * 28 * y.size)
                )
            if not math.isfinite(loss) or loss < 0:
                _range("nonfinite or negative training loss")
        except SimreconError as error:
            if error.code in _KNOWN:
                trace.append(PilotScore(score_stage, order, None, None, "numerical_incomplete"))
            raise
        trace.append(PilotScore(score_stage, order, _snapshot(candidate), loss, "scored"))
        return candidate, loss

    try:
        y, training = _correct(central, blank, contrast), _correct(structured, blank, contrast)
        stage = "initialization"
        initialized = _initialize(y)
        if initialized is None:
            return replace(
                result,
                status="initialization_failed",
                stage=stage,
                message="initialization: unavailable positive separated centroids",
            )
        centers, maxima, init_message = initialized
        units = [
            prediction.unit(
                prediction.profile(c), np.zeros(2), np.zeros(1), np.array([1.0, 0.0, 0.0]), 128
            )[0]
            for c in centers
        ]
        peaks = np.array([float(np.max(unit)) for unit in units])
        # Initialization proves maxima>0. A successful central _scale_output
        # certifies finite peaks>0: all-zero storage would violate its relative
        # unilluminated allowance. Here U <= D_y*D_x*pi*(NA/emission)^2 times
        # stored unit mass and (1+1e-5), <0.144. Division therefore cannot produce
        # zero brightness, including subnormal maxima; overflow still can occur.
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            brightness = _finite(maxima / peaks, "initial brightness")
        commands = np.array(
            [
                *(2 * math.pi * j / 5 for j in range(5)),
                math.pi / 5,
                3 * math.pi / 5,
                7 * math.pi / 5,
                9 * math.pi / 5,
            ]
        )
        q = (1.2 / 0.488) * np.array(
            [[math.sin(w), math.cos(w)] for w in (0, math.pi / 3, 2 * math.pi / 3)]
        )
        initial = prediction.candidate(
            centers, brightness, q, np.tile(commands, (3, 1)), np.ones(3) / math.sqrt(3)
        )
        result = replace(result, initial_candidate=_snapshot(initial))
        stage = "initial"
        _, best_cost = score(lambda: initial, stage, 128)
        best = initial
        stage = "optimizer"

        def objective(x: Real) -> float:
            nonlocal best, best_cost
            # Each callback appends exactly one record, independently of nfev.
            candidate, loss = score(lambda: _decode(x, initial, prediction), "optimizer", 128)
            if loss < best_cost:
                best, best_cost = candidate, loss
            return loss

        x0 = np.array(
            [
                1,
                1,
                1,
                math.acos(1 / math.sqrt(3)) / (math.pi / 2),
                0.5,
                1.2 / 1.515,
                0,
                1.2 / 1.515,
                1 / 3,
                1.2 / 1.515,
                2 / 3,
                *np.tile(commands / (2 * math.pi), 3),
            ]
        )
        answer = optimize.minimize(
            objective,
            x0,
            method="Powell",
            bounds=[(0, 100)] * 3 + [(0, 1)] * 2 + [(0, 1), (-1, 1)] * 3 + [(-1, 1)] * 27,
            options={"maxfev": 100, "maxiter": 4, "xtol": 1e-3, "ftol": 1e-3},
        )
        result = replace(
            result,
            optimizer_status=int(answer.status),
            optimizer_message=str(answer.message),
            optimizer_nfev=int(answer.nfev),
            optimizer_nit=int(answer.nit),
        )
        if not answer.success and answer.status not in (1, 2):
            return replace(
                result,
                status="numerical_incomplete",
                stage=stage,
                message=f"optimizer: {answer.message}",
                failure_code="image_only_calibration_pilot_optimizer",
                objective_trace=tuple(trace),
                training_objectives_q128_q256_q512=tuple(objectives),
            )
        stage = "center"
        for bead, axis in itertools.product(range(3), range(3)):
            incumbent = cast(PilotCandidate, best)
            trials: list[tuple[PilotCandidate, float]] = []
            for sign in (-1, 1):
                moved = _copy(incumbent.centers_um_zyx)
                moved[bead, axis] += sign * _D[axis] / 8
                try:
                    candidate, loss = score(
                        lambda moved=moved, incumbent=incumbent: (
                            prediction.candidate(
                                moved,
                                incumbent.brightness_relative,
                                incumbent.carriers_yx_per_um,
                                incumbent.phases_rad,
                                incumbent.beam_amplitudes,
                            )
                            if _feasible(moved, shape)
                            else None
                        ),
                        "center",
                        128,
                    )
                except SimreconError as error:
                    if error.code in _KNOWN:
                        attempts.append(
                            PilotCenterAttempt(bead, axis, sign, "numerical_incomplete")
                        )
                    raise
                attempts.append(
                    PilotCenterAttempt(
                        bead, axis, sign, "infeasible" if candidate is None else "scored"
                    )
                )
                if candidate is not None:
                    trials.append((candidate, loss))
            # Decide only after BOTH signs, retaining the first best strict tie.
            for candidate, loss in trials:
                if loss < best_cost:
                    best, best_cost = candidate, loss
            prediction.retain(cast(PilotCandidate, best))
        frozen = cast(PilotCandidate, best)
        result = replace(result, frozen_candidate=_snapshot(frozen))
        objectives[0] = best_cost
        for i, order in enumerate((256, 512), start=1):
            stage = f"refinement_q{order}"
            _, objectives[i] = score(lambda: frozen, "refinement", order)
        stage = "heldout"
        _, heldout_prediction = prediction.predict(frozen, 512, 5)
        result = replace(result, heldout_prediction=_copy(heldout_prediction))
        heldout_y = _correct(heldout, blank, contrast)
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            residual = _finite(heldout_y - heldout_prediction, "heldout residual")
            mean = np.mean(residual, axis=(-3, -2, -1))
            rms = np.sqrt(np.mean(residual**2, axis=(-3, -2, -1)))
        _finite(mean, "heldout mean")
        _finite(rms, "heldout RMS")
        return replace(
            result,
            status="completed_local" if answer.success else "completed_budget_limited",
            stage="complete",
            message=f"complete: {answer.message}; {init_message}",
            objective_trace=tuple(trace),
            center_attempts=tuple(attempts),
            training_objectives_q128_q256_q512=tuple(objectives),
            heldout_prediction=_copy(heldout_prediction),
            heldout_residual_mean=_copy(mean),
            heldout_residual_rms=_copy(rms),
        )
    except SimreconError as error:
        if error.code not in _KNOWN:
            raise
        return replace(
            result,
            status="numerical_incomplete",
            stage=stage,
            message=f"{stage}: {error}",
            failure_code=error.code,
            objective_trace=tuple(trace),
            center_attempts=tuple(attempts),
            training_objectives_q128_q256_q512=tuple(objectives),
        )
