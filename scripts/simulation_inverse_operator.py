"""Finite, exterior-zero scalar imaging and its real coordinate adjoint.

The cache stores lateral transforms of even axial lags. Applications transform
one source plane at a time and do the axial convolution in frequency blocks;
neither a three-dimensional kernel nor a dense optical matrix is constructed.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from decimal import Decimal, getcontext, localcontext
from fractions import Fraction
from typing import Any, NoReturn

import numpy as np
from numpy.typing import NDArray
from scipy import fft as scipy_fft
from scipy import special

from simrecon import SimreconError

Array = NDArray[Any]
Shape = tuple[int, int, int]
Spacing = tuple[float, float, float]
# SciPy's dispatch decorators currently expose the dispatch argument tuple as
# the static return type; the public transform functions return ndarrays.
fft: Any = scipy_fft


@dataclass(frozen=True)
class InverseKernelCache:
    """Bind seven cache fields without validating or authenticating their values."""

    lateral_spectra: Array
    source_shape_zyx: Shape
    source_spacing_um_zyx: Spacing
    emission_um: float
    refractive_index: float
    detection_na: float
    pupil_order: int


def _invalid(field: str) -> NoReturn:
    raise SimreconError("invalid_simulation_inverse_operator", f"Invalid {field}.")


def _range(field: str) -> NoReturn:
    raise SimreconError(
        "simulation_inverse_operator_range", f"Unrepresentable inverse operator {field}."
    )


def _scalar(value: Any, field: str, *, zero: bool = False) -> float:
    if type(value) not in (int, float):
        _invalid(field)
    try:
        result = float(value)
    except OverflowError:
        _invalid(field)
    if not math.isfinite(result) or (result < 0 if zero else result <= 0):
        _invalid(field)
    return result


def _triple(value: Any, field: str, *, zero: bool = False) -> Spacing:
    if type(value) is not tuple or len(value) != 3:
        _invalid(field)
    return tuple(_scalar(v, field, zero=zero) for v in value)  # type: ignore[return-value]


def _metadata(
    shape: Any, spacing: Any, emission: Any, index: Any, na: Any, order: Any
) -> tuple[Shape, Spacing, float, float, float, int]:
    if (
        type(shape) is not tuple
        or len(shape) != 3
        or any(type(n) is not int or n < 1 for n in shape)
        or shape[1] % 2
        or shape[2] % 2
    ):
        _invalid("source_shape_zyx")
    steps = _triple(spacing, "source_spacing_um_zyx")
    wavelength = _scalar(emission, "emission_um")
    medium = _scalar(index, "refractive_index")
    aperture = _scalar(na, "detection_na")
    if aperture > medium:
        _invalid("detection_na / refractive_index")
    if type(order) is not int or order < 1:
        _invalid("pupil_order")
    return shape, steps, wavelength, medium, aperture, order


def _address(shape: tuple[int, ...], width: int, field: str) -> None:
    # Check the arrays actually needed at this stage, not a fictitious full F
    # volume, an optional unused quadrature, or a discretionary work limit.
    if any(n > sys.maxsize for n in shape) or math.prod(shape) > sys.maxsize // width:
        _range(f"{field} address space")


def _float32_array(value: Any, shape: tuple[int, ...], field: str) -> None:
    if (
        type(value) is not np.ndarray
        or value.dtype.kind != "f"
        or value.dtype.itemsize != 4
        or value.shape != shape
        or not np.all(np.isfinite(value))
    ):
        _invalid(field)


def _settings_array(value: Any, field: str, *, carrier: bool = False) -> Array:
    if (
        type(value) is not np.ndarray
        or value.dtype.kind not in "iuf"
        or value.ndim != 1
        or (value.shape != (2,) if carrier else value.size == 0)
    ):
        _invalid(field)
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = value.astype(np.float64)
    if not np.all(np.isfinite(result)):
        _invalid(field)
    return result


def _cis_turns(turns: Fraction | Decimal) -> complex:
    # Reduce BEFORE conversion to radians: multiplying a huge turn count by a
    # rounded 2*pi would change the specified carrier/axial phase.
    remainder = float(turns % 1)
    angle = math.tau * remainder
    return complex(math.cos(angle), math.sin(angle))


def _phasors(
    shape: Shape, spacing: Spacing, q: Array, index: float, excitation: float
) -> tuple[Array, Array]:
    qy, qx = (Fraction(float(v)) for v in q)
    k0 = Fraction(index) / Fraction(excitation)
    q2 = qy * qy + qx * qx
    if q2 > k0 * k0:
        _invalid("carrier_yx_per_um propagating domain")
    dy, dx = Fraction(spacing[1]), Fraction(spacing[2])
    ey = np.array([_cis_turns(qy * dy * Fraction(2 * j + 1, 2)) for j in range(shape[1])])
    ex = np.array([_cis_turns(qx * dx * Fraction(2 * j + 1, 2)) for j in range(shape[2])])
    # Products of tiny phasor components may underflow even though the unit
    # phasor remains accurate. Handle only that owned arithmetic locally.
    with np.errstate(under="ignore"):
        lateral = ey[:, None] * ex[None, :]
    with localcontext() as ctx:
        # Products of finite binary64 ratios, spacings and addressable indices
        # span fewer than 1000 decimal orders here. Rationalization avoids
        # cancellation when a tiny carrier accompanies a huge wave number.
        ctx.prec = 2200
        wave = Decimal(index) / Decimal(excitation)
        squared = Decimal(q2.numerator) / Decimal(q2.denominator)
        remaining = k0 * k0 - q2
        root = (Decimal(remaining.numerator) / Decimal(remaining.denominator)).sqrt()
        kappa = squared / (wave + root) if squared else Decimal(0)
        step = kappa * Decimal(spacing[0])
        axial = np.array([_cis_turns(step * (Decimal(j) + Decimal(0.5))) for j in range(shape[0])])
    return lateral, axial


def _validate(
    data: Any,
    cache: Any,
    carrier: Any,
    phases: Any,
    amplitudes: Any,
    excitation: Any,
    operation: str,
) -> tuple[Shape, Spacing, Array, tuple[float, float, float], Array, Array]:
    if not isinstance(cache, InverseKernelCache):
        _invalid("kernel_cache")
    shape, spacing, _, index, _, _ = _metadata(
        cache.source_shape_zyx,
        cache.source_spacing_um_zyx,
        cache.emission_um,
        cache.refractive_index,
        cache.detection_na,
        cache.pupil_order,
    )
    nz, ny, nx = shape
    _float32_array(cache.lateral_spectra, (nz, 2 * ny, nx + 1), "lateral_spectra")
    for j in range(1, ny):
        if not np.array_equal(cache.lateral_spectra[:, j], cache.lateral_spectra[:, -j]):
            _invalid("lateral_spectra stored y symmetry")
    q = _settings_array(carrier, "carrier_yx_per_um", carrier=True)
    phi = _settings_array(phases, "phases_rad")
    beams = _triple(amplitudes, "beam_amplitudes", zero=True)
    maximum = max(beams)
    if not maximum:
        _invalid("beam_amplitudes")
    a, b, c = (v / maximum for v in beams)
    total = math.fsum((a * a, b * b, c * c))
    coefficients = a * b / total, a * c / total, b * c / total
    wavelength = _scalar(excitation, "excitation_um")
    target = shape if operation == "forward" else (len(phi), nz, ny // 2, nx // 2)
    _float32_array(data, target, "source_e" if operation == "forward" else "detector_values")
    _address(target, 8, f"{operation} output")
    lateral, axial = _phasors(shape, spacing, q, index, wavelength)
    return shape, spacing, phi, coefficients, lateral, axial


def _sum_four(terms: list[Array]) -> Array:
    """Sum four dyadic terms while retaining cancellation residuals.

    Error-free TwoSum expansions prevent an unused-lag component from obscuring
    a small, independently represented finite kernel. Each input is float32
    promoted to float64; neither sums nor their roundoff can overflow float64.
    """
    expansion = [terms[0]]
    for term in terms[1:]:
        tail = []
        for component in expansion:
            combined = term + component
            recovered = combined - term
            tail.append((term - (combined - recovered)) + (component - recovered))
            term = combined
        expansion = [*tail, term]
    result = expansion[0]
    for component in expansion[1:]:
        result = result + component
    return result


def _finite_spectra(cache: InverseKernelCache) -> tuple[Array, float]:
    """Remove only unused lag lines, then normalize the actual finite kernel."""
    nz, ny, nx = cache.source_shape_zyx
    _address((nz, 2 * ny, nx + 1), 8, "lateral_spectra workspace")
    _address((2 * ny, 2 * nx), 16, "lateral transform")
    result = np.empty((nz, 2 * ny, nx + 1), dtype=np.float64)
    parity_y = np.where(np.arange(2 * ny) % 2, -1.0, 1.0)[:, None]
    parity_x = np.where(np.arange(nx + 1) % 2, -1.0, 1.0)[None, :]
    maximum = 0.0
    for d in range(nz):
        original = cache.lateral_spectra[d].astype(np.float64)
        # Subtracted spectra invert to x=Nx or y=Ny only. None of those lags
        # occurs in the finite operator. Exact zero here proves G_C=0, including
        # nonzero payloads supported entirely on these unused lag lines.
        projected = _sum_four(
            [
                original,
                -original[:, :1] * parity_x,
                -original[:1, :] * parity_y,
                original[0, 0] * parity_y * parity_x,
            ]
        )
        plane = fft.irfft2(projected, s=(2 * ny, 2 * nx))
        plane[ny, :] = 0
        plane[:, nx] = 0
        maximum = max(maximum, float(np.max(np.abs(plane))))
        result[d] = fft.rfft2(plane).real
    if maximum:
        result /= maximum
    return result, maximum


def _convolve(spectra: Array, shape: Shape, planes: Callable[[int], Array]) -> Iterator[Array]:
    """Apply normalized finite H, retaining only the physical source-sized crop."""
    nz, ny, nx = shape
    work = np.empty(spectra.shape, dtype=np.complex64)
    for z in range(nz):
        work[z] = fft.rfft2(planes(z), s=(2 * ny, 2 * nx))
    flat, kernels = work.reshape(nz, -1), spectra.reshape(nz, -1)
    block_size = min(4096, sys.maxsize // (2 * nz * 16))
    for start in range(0, flat.shape[1], block_size):
        stop = min(start + block_size, flat.shape[1])
        kernel = np.zeros((2 * nz, stop - start), dtype=np.float64)
        kernel[:nz] = kernels[:, start:stop]
        kernel[nz + 1 :] = kernels[1:, start:stop][::-1]
        transformed = fft.fft(flat[:, start:stop].astype(np.complex128), n=2 * nz, axis=0)
        transformed *= fft.fft(kernel, axis=0).real
        flat[:, start:stop] = fft.ifft(transformed, axis=0)[:nz]
    for z in range(nz):
        yield fft.irfft2(work[z], s=(2 * ny, 2 * nx))[:ny, :nx].astype(np.float64)


def _pixel(plane: Array) -> Array:
    ny, nx = plane.shape
    return plane.reshape(ny // 2, 2, nx // 2, 2).sum(axis=(1, 3))


def _box_sums(plane: Array, ny: int, nx: int) -> Array:
    """Sum every finite lateral source window of a nonnegative even plane."""
    shifted = np.roll(plane, (ny - 1, nx - 1), axis=(0, 1))
    prefix = np.pad(shifted, ((1, 0), (1, 0))).cumsum(axis=0).cumsum(axis=1)
    return (
        prefix[ny : 2 * ny, nx : 2 * nx]
        - prefix[:ny, nx : 2 * nx]
        - prefix[ny : 2 * ny, :nx]
        + prefix[:ny, :nx]
    )


def _norms(spectra: Array, shape: Shape) -> tuple[float, float]:
    """Evaluate finite G row/column norms without area, for precision diagnosis."""
    nz, ny, nx = shape
    row = column = 0.0
    # Rare subnormal-output diagnosis: keep only two lateral planes. The sum
    # over a rectangle of source sites is evaluated by integral images.
    for z in range(nz):
        sums = np.zeros((ny, nx), dtype=np.float64)
        for j in range(nz):
            h = np.abs(fft.irfft2(spectra[abs(z - j)], s=(2 * ny, 2 * nx)))
            sums += _box_sums(h, ny, nx)
        row = max(row, float(np.max(_pixel(sums))))
        column = max(column, float(np.max(sums)))
    return row, column


def _restore(
    output: Array,
    factors: tuple[float, ...],
    spectra: Array,
    shape: Shape,
    light: float,
    phase_count: int,
    operation: str,
) -> Array:
    mantissa, exponent = 1.0, 0
    for factor in factors:
        part, power = math.frexp(factor)
        mantissa *= part
        exponent += power
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = np.ldexp(output * mantissa, exponent)
    if not np.all(np.isfinite(result)):
        _range(f"{operation} output")
    # Only subnormal rounding can be large compared with the selected normwise
    # target. Compare in normalized coordinates so neither area nor the target
    # is rounded to zero before the decision.
    if exponent < -1000 and np.any(output):
        row, column = _norms(spectra, shape)
        scale = light * (row if operation == "forward" else phase_count * column)
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            restored = np.ldexp(result, -exponent) / mantissa
        if np.max(np.abs(restored - output)) > 1e-4 * scale:
            _range(f"{operation} output precision")
    return result


def _pupil_nodes(order: int, roots: Array) -> list[Decimal]:
    """Refine the canonical Legendre nodes at the active decimal precision.

    A binary64 node is insufficient when a long defocus distance magnifies its
    error into an appreciable phase. Newton refinement uses the defining
    polynomial, independently of the eventual trigonometric argument reduction.
    """
    tolerance = Decimal(1).scaleb(-getcontext().prec + 10)
    result = []
    for root in roots:
        x = Decimal(float(root))
        while True:
            previous, value = Decimal(0), Decimal(1)
            for k in range(1, order + 1):
                previous, value = value, ((2 * k - 1) * x * value - (k - 1) * previous) / k
            derivative = order * (x * value - previous) / (x * x - 1)
            correction = value / derivative
            x -= correction
            if abs(correction) <= tolerance:
                break
        result.append((x + 1) / 2)
    return result


def _decimal_pi() -> Decimal:
    """Evaluate pi at the active precision for large Bessel arguments."""
    a, b, t, power = Decimal(1), Decimal(0.5).sqrt(), Decimal(0.25), 1
    tolerance = Decimal(1).scaleb(-getcontext().prec + 10)
    while abs(a - b) > tolerance:
        mean = (a + b) / 2
        b = (a * b).sqrt()
        t -= power * (a - mean) ** 2
        a = mean
        power *= 2
    return (a + b) ** 2 / (4 * t)


def _large_j0(argument: Decimal, pi: Decimal) -> float:
    """Evaluate J0 beyond 1e6 using its oscillatory asymptotic expansion.

    Through inverse-cubic order the omitted relative envelope term is below
    2e-24 at the transition and decreases thereafter. Reducing the unrounded
    argument preserves its phase even beyond the binary64 exponent range.
    Coefficients and real-argument remainder: https://dlmf.nist.gov/10.17.
    """
    phase = float((argument - pi / 4) % (2 * pi))
    inverse = float(1 / argument)
    p = 1 - 9 / 128 * inverse**2
    q = -inverse / 8 + 225 / 3072 * inverse**3
    envelope = float((2 / (pi * argument)).sqrt())
    return envelope * (math.cos(phase) * p - math.sin(phase) * q)


def build_kernel_cache(
    *,
    source_shape_zyx: Any,
    source_spacing_um_zyx: Any,
    emission_um: Any,
    refractive_index: Any,
    detection_na: Any,
    pupil_order: Any,
) -> InverseKernelCache:
    """Build the complete finite-Q scalar pupil cache, without pixel integration."""
    shape, spacing, emission, index, na, order = _metadata(
        source_shape_zyx,
        source_spacing_um_zyx,
        emission_um,
        refractive_index,
        detection_na,
        pupil_order,
    )
    nz, ny, nx = shape
    _address((nz, 2 * ny, nx + 1), 4, "source_shape_zyx cache")
    _address((2 * ny, 2 * nx), 16, "source_shape_zyx lateral transform")
    _address((order,), 8, "pupil_order")
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        radius = na / emission
        peak = math.pi * radius * radius
        if not math.isfinite(peak) or peak == 0:
            _range("lateral_spectra pupil peak")
        roots, weights = special.roots_legendre(order)
        weights = weights / 2
        result = np.empty((nz, 2 * ny, nx + 1), dtype=np.float32)
        yy = np.minimum(np.arange(2 * ny), 2 * ny - np.arange(2 * ny))
        xx = np.minimum(np.arange(2 * nx), 2 * nx - np.arange(2 * nx))
        with localcontext() as ctx:
            ctx.prec = 80
            r = Decimal(na) / Decimal(emission)
            beta = Decimal(na) / Decimal(index)
            extent = max(
                Decimal(nz) * Decimal(spacing[0]) * r * beta,
                Decimal(ny) * Decimal(spacing[1]) * r,
                Decimal(nx) * Decimal(spacing[2]) * r,
            )
            ctx.prec = max(80, extent.adjusted() + 80)
            r = Decimal(na) / Decimal(emission)
            beta = Decimal(na) / Decimal(index)
            nodes = _pupil_nodes(order, roots)
            pi = _decimal_pi()
            root0 = (1 - beta * beta * nodes[0]).sqrt()

            def physical(d: int) -> Array:
                amplitude = np.zeros((ny, nx), dtype=np.complex128)
                for u, w in zip(nodes, weights, strict=True):
                    # Remove a common pupil phase, which cannot affect |A|^2.
                    # Rationalize the difference of square roots before any
                    # products, including when n/lambda itself would overflow.
                    root = (1 - beta * beta * u).sqrt()
                    turns = (
                        Decimal(d)
                        * Decimal(spacing[0])
                        * r
                        * beta
                        * (u - nodes[0])
                        / (root + root0)
                    )
                    factor = 2 * pi * r * u.sqrt()
                    sy, sx = factor * Decimal(spacing[1]), factor * Decimal(spacing[2])
                    y = np.array([float(sy * j) for j in range(ny)])
                    x = np.array([float(sx * j) for j in range(nx)])
                    arguments = np.hypot(y[:, None], x[None, :])
                    bessel = special.j0(np.minimum(arguments, 1e6))
                    for iy, ix in zip(*np.nonzero(arguments > 1e6), strict=True):
                        argument = ((sy * int(iy)) ** 2 + (sx * int(ix)) ** 2).sqrt()
                        bessel[iy, ix] = _large_j0(argument, pi)
                    amplitude += float(w) * bessel * _cis_turns(turns)
                quadrant = peak * np.abs(amplitude) ** 2
                plane = quadrant[np.minimum(yy, ny - 1)[:, None], np.minimum(xx, nx - 1)[None, :]]
                plane[ny, :] = 0
                plane[:, nx] = 0
                return plane

            # Upper bound on either error norm and an average physical norm
            # give a cheap sufficient certificate. Failure of this conservative
            # bound triggers actual finite norms, not an input rejection.
            error_mass, physical_average = 0.0, 0.0
            lateral_overlap = (1 - yy / ny)[:, None] * (1 - xx / nx)[None, :]
            for d in range(nz):
                plane = physical(d)
                # These two lag lines are never queried by the finite map.
                # Continuing its mean across them avoids artificial jumps that
                # waste float32 precision when the physical plane is nearly constant.
                background = float(np.sum(plane)) / ((2 * ny - 1) * (2 * nx - 1))
                plane[ny, :] = background
                plane[:, nx] = background
                transformed = fft.rfft2(plane).real
                if np.max(np.abs(transformed)) > np.finfo(np.float32).max:
                    # A constant extension concentrates the background in DC.
                    # Instead extend that component separably by -(N-1) at
                    # each unused lag N. Its 1D transform has magnitude N at
                    # every frequency: DC=N, others=-N*(-1)**k. The resulting
                    # background coefficients have magnitude ny*nx*background,
                    # rather than 4*ny*nx*background, with every required lag
                    # unchanged. The nonconstant residual stays zero-padded.
                    plane[ny, :] = -(ny - 1) * background
                    plane[:, nx] = -(nx - 1) * background
                    plane[ny, nx] = (ny - 1) * (nx - 1) * background
                    transformed = fft.rfft2(plane).real
                for j in range(1, ny):
                    transformed[-j] = transformed[j]
                result[d] = transformed
                if not np.all(np.isfinite(result[d])):
                    _range("lateral_spectra float32 pupil representation")
                represented = fft.irfft2(result[d].astype(np.float64), s=(2 * ny, 2 * nx))
                error = np.abs(represented - plane)
                error[ny, :] = 0
                error[:, nx] = 0
                multiplicity = 1 if d == 0 else 2
                error_mass += multiplicity * float(np.sum(error))
                physical_average += (
                    multiplicity * (1 - d / nz) * float(np.sum(plane * lateral_overlap))
                )
            if error_mass > 1e-4 * physical_average:
                reference_sums = np.zeros(shape, dtype=np.float64)
                error_sums = np.zeros(shape, dtype=np.float64)
                for d in range(nz):
                    plane = physical(d)
                    represented = fft.irfft2(result[d].astype(np.float64), s=(2 * ny, 2 * nx))
                    for sums, values in (
                        (reference_sums, plane),
                        (error_sums, np.abs(represented - plane)),
                    ):
                        boxes = _box_sums(values, ny, nx)
                        sums[d:] += boxes
                        if d:
                            sums[: nz - d] += boxes
                reference_rows = reference_sums.reshape(nz, ny // 2, 2, nx // 2, 2).sum(axis=(2, 4))
                error_rows = error_sums.reshape(nz, ny // 2, 2, nx // 2, 2).sum(axis=(2, 4))
                if np.max(error_rows) > 1e-4 * np.max(reference_rows) or np.max(
                    error_sums
                ) > 1e-4 * np.max(reference_sums):
                    _range("lateral_spectra pupil precision")
    return InverseKernelCache(result, shape, spacing, emission, index, na, order)


def _apply(
    data: Any,
    cache: Any,
    carrier: Any,
    phases: Any,
    amplitudes: Any,
    excitation: Any,
    operation: str,
) -> Array:
    shape, spacing, phi, coefficients, lateral, axial = _validate(
        data, cache, carrier, phases, amplitudes, excitation, operation
    )
    nz, ny, nx = shape
    target = (len(phi), nz, ny // 2, nx // 2) if operation == "forward" else shape
    result = np.zeros(target, dtype=np.float64)
    input_scale = float(np.max(np.abs(data)))
    if not input_scale:
        return result
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        spectra, kernel_scale = _finite_spectra(cache)
        if not kernel_scale:
            return result
        phase = np.array([complex(math.cos(float(p)), math.sin(float(p))) for p in phi])
        if operation == "forward":
            for z, plane in enumerate(
                _convolve(spectra, shape, lambda j: data[j].astype(np.float64) / input_scale)
            ):
                result[:, z] = _pixel(plane)
            for coefficient, lateral_order, axial_sign in zip(
                coefficients, (1, 1, 2), (1, -1, 0), strict=True
            ):
                if not coefficient:
                    continue
                lateral_factor = lateral**lateral_order
                focus = (
                    axial if axial_sign == 1 else axial.conj() if axial_sign == -1 else np.ones(nz)
                )
                for imaginary in (False, True):

                    def source(
                        j: int,
                        lateral_factor: Array = lateral_factor,
                        focus: Array = focus,
                        imaginary: bool = imaginary,
                    ) -> Array:
                        modulation = lateral_factor * focus[j].conjugate()
                        return (
                            data[j].astype(np.float64)
                            / input_scale
                            * (modulation.imag if imaginary else modulation.real)
                        )

                    for z, plane in enumerate(_convolve(spectra, shape, source)):
                        multiplier = phase**lateral_order * focus[z]
                        weight = -multiplier.imag if imaginary else multiplier.real
                        result[:, z] += (2 * coefficient * weight)[:, None, None] * _pixel(plane)
        else:

            def deposit(j: int, weights: Array) -> Array:
                summed = np.sum(
                    data[:, j].astype(np.float64) / input_scale * weights[:, None, None], axis=0
                )
                return summed.repeat(2, axis=0).repeat(2, axis=1)

            for z, plane in enumerate(
                _convolve(spectra, shape, lambda j: deposit(j, np.ones(len(phi))))
            ):
                result[z] = plane
            for coefficient, lateral_order, axial_sign in zip(
                coefficients, (1, 1, 2), (1, -1, 0), strict=True
            ):
                if not coefficient:
                    continue
                lateral_factor = lateral**lateral_order
                focus = (
                    axial if axial_sign == 1 else axial.conj() if axial_sign == -1 else np.ones(nz)
                )
                for imaginary in (False, True):

                    def residual(
                        j: int,
                        lateral_order: int = lateral_order,
                        focus: Array = focus,
                        imaginary: bool = imaginary,
                    ) -> Array:
                        multiplier = (phase**lateral_order * focus[j]).conj()
                        return deposit(j, multiplier.imag if imaginary else multiplier.real)

                    for z, plane in enumerate(_convolve(spectra, shape, residual)):
                        multiplier = (lateral_factor * focus[z].conjugate()).conj()
                        weight = -multiplier.imag if imaginary else multiplier.real
                        result[z] += 2 * coefficient * weight * plane
        light = 1 + 2 * math.fsum(coefficients)
        return _restore(
            result,
            (input_scale, kernel_scale, spacing[1], spacing[2]),
            spectra,
            shape,
            light,
            len(phi),
            operation,
        )


def forward(
    source_e: Any,
    *,
    kernel_cache: Any,
    carrier_yx_per_um: Any,
    phases_rad: Any,
    beam_amplitudes: Any,
    excitation_um: Any,
) -> Array:
    """Map signed float32 source coefficients to float64 detector electrons."""
    return _apply(
        source_e,
        kernel_cache,
        carrier_yx_per_um,
        phases_rad,
        beam_amplitudes,
        excitation_um,
        "forward",
    )


def adjoint(
    detector_values: Any,
    *,
    kernel_cache: Any,
    carrier_yx_per_um: Any,
    phases_rad: Any,
    beam_amplitudes: Any,
    excitation_um: Any,
) -> Array:
    """Apply the real Euclidean transpose, including weighted pixel deposit."""
    return _apply(
        detector_values,
        kernel_cache,
        carrier_yx_per_um,
        phases_rad,
        beam_amplitudes,
        excitation_um,
        "adjoint",
    )
