"""Pure finite-box scalar optical expectations (contract revision 2).

Source entries are integrated electron weights. Neither the direct sum nor the
linear convolution uses reconstruction, a periodic specimen, or a PSF cutoff.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from typing import Any, NoReturn, cast

import numpy as np
from numpy.typing import NDArray
from scipy import fft, special

from simrecon import SimreconError

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
_EPS = np.finfo(np.float64).eps


def _invalid(message: str) -> NoReturn:
    raise SimreconError("invalid_simulation_optics", message)


def _range(message: str) -> NoReturn:
    raise SimreconError("simulation_optics_range", message)


def _array(value: Any, name: str) -> Real:
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        _invalid(f"{name} must be a plain real numeric ndarray")
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = np.asarray(value, dtype=np.float64)
    # Supported real casts preserve nonfinite values. This single check also
    # rejects finite wider inputs that overflow during float64 normalization.
    if not np.isfinite(result).all():
        _invalid(f"{name} cannot normalize to finite float64")
    return result


def _coefficient(value: Any, name: str, *, zero: bool = False) -> float:
    if type(value) not in (int, float):
        _invalid(f"{name} must be a built-in int or float")
    try:
        result = float(value)
    except OverflowError:
        _invalid(f"{name} cannot normalize to float64")
    if not math.isfinite(result) or result < 0 or (not zero and result == 0):
        _invalid(f"{name} is outside its finite domain")
    return result


def _counts(value: Any, length: int, name: str) -> tuple[int, ...]:
    if (
        type(value) is not tuple
        or len(value) != length
        or any(type(v) is not int or v <= 0 for v in value)
    ):
        _invalid(f"{name} must contain {length} positive built-in integers")
    return value


def _coefficients(value: Any, name: str, *, zero: bool = False) -> tuple[float, ...]:
    if type(value) is not tuple or len(value) != 3:
        _invalid(f"{name} must be a three-element tuple")
    return tuple(_coefficient(v, name, zero=zero) for v in value)


def _turns(q: float, spacing: float, refinement: int, size: int) -> Real:
    """Reduce exact rational carrier coordinates BEFORE multiplying by 2*pi."""
    step = Fraction(q) * Fraction(spacing) / (2 * refinement)
    return np.array([float((step * (2 * j + 1)) % 1) for j in range(size)])


def _wave(cycles: Real) -> Complex:
    return np.cos(2 * np.pi * cycles) + 1j * np.sin(2 * np.pi * cycles)


def _axial_frequencies(
    k0: Fraction, squares: list[Fraction]
) -> tuple[list[Fraction], list[Fraction]]:
    frequencies, errors = [], []
    for q2 in squares:
        remaining = k0**2 - q2
        numerator, denominator = math.isqrt(remaining.numerator), math.isqrt(remaining.denominator)
        if numerator**2 == remaining.numerator and denominator**2 == remaining.denominator:
            frequencies.append(k0 - Fraction(numerator, denominator))
            errors.append(Fraction(0))
        else:
            # Stable evaluation avoids subtraction of nearly equal k0/root.
            # Decimal also avoids underflow BEFORE sqrt at the closed boundary.
            with localcontext(Context(prec=80)):
                k = Decimal(k0.numerator) / Decimal(k0.denominator)
                q = Decimal(q2.numerator) / Decimal(q2.denominator)
                r = Decimal(remaining.numerator) / Decimal(remaining.denominator)
                value = Fraction(q / (k + r.sqrt()))
            frequencies.append(value)
            errors.append(abs(value) / 10**75)
    return frequencies, errors


def _displacements(
    indices: range, spacing: float, refinement: int, offset: Fraction = Fraction(0)
) -> Real:
    # Integer displacements and rational half-cell/pixel offsets are combined
    # BEFORE float conversion, preserving close differences on unequal grids.
    step = Fraction(spacing) / refinement
    try:
        return np.array([float((i + offset) * step) for i in indices])
    except OverflowError:
        _range("displacement exceeds float64 geometry representation")


@dataclass
class _Optics:
    spacing: tuple[float, ...]
    refinement: tuple[int, ...]
    pixels: tuple[int, ...]
    shape: tuple[int, ...]
    beams: Real
    kappa: list[Fraction]
    kappa_error: list[Fraction]
    lateral: list[Complex]
    phases: Complex
    radial: Real
    axial: Real
    weights: Real
    # Absolute density error estimate in units of the common pi*R**2 factor.
    error: float = 0.0
    phase_error: float = 0.0
    last_error_sum: float = 0.0
    convolution_error: float = 0.0

    def density(
        self, radius: Real, d: float, multiplicities: NDArray[np.intp] | None = None
    ) -> Real:
        field = np.zeros(radius.shape, dtype=np.complex128)
        field_error = np.zeros(radius.shape)
        for radial, axial, weight in zip(self.radial, self.axial, self.weights, strict=True):
            argument = radial * radius
            angle = axial * d
            if not np.isfinite(argument).all() or not math.isfinite(angle):
                _range("nonfinite pupil argument")
            bessel = special.j0(argument)
            argument_error = 32 * _EPS * len(self.weights) * np.abs(argument) + abs(radial) * (
                4 * math.ulp(0.0)
            )
            # |J0'|=|J1| and |J1'|<=1 bound the effect of argument rounding.
            # Use the evaluated derivative plus its argument-neighbourhood,
            # instead of charging the largest argument at every dark pixel.
            field_error += weight * (
                argument_error * (np.abs(special.j1(argument)) + argument_error)
                + (
                    32 * _EPS * len(self.weights) * (1 + abs(angle))
                    + abs(axial) * (2 * math.ulp(0.0))
                )
                * np.abs(bessel)
            )
            field += weight * bessel * complex(math.cos(angle), math.sin(angle))
        # Operation/argument roundoff is absolute, not relative to a dark field.
        # Track it against the eventual unilluminated peak, including all sources.
        density = field.real**2 + field.imag**2
        density_error = 2 * np.abs(field) * field_error + field_error**2 + 8 * _EPS * density
        self.error = max(self.error, float(density_error.max()))
        if multiplicities is None:
            self.last_error_sum = float(density_error.sum())
        else:
            # Each unique radius stands for this many sites in the FULL plane.
            # fsum avoids accumulating error proportional to the site count;
            # padding covers count conversion, multiplication and final rounding.
            try:
                weighted = math.fsum(
                    float(error) * int(count)
                    for error, count in zip(density_error, multiplicities, strict=True)
                )
            except OverflowError:
                _range("density error sum exceeds arithmetic range")
            self.last_error_sum = (
                math.nextafter(weighted * (1 + 4 * _EPS), math.inf) if weighted else 0.0
            )
        return density

    def axial_wave(self, d: Fraction, orientation: int) -> complex:
        turns = self.kappa[orientation] * d
        angle = 2 * math.pi * float(turns % 1)
        try:
            uncertainty = 128 * _EPS + 16 * float(abs(d) * self.kappa_error[orientation])
        except OverflowError:
            _range("axial illumination phase precision is exhausted")
        self.phase_error = max(self.phase_error, uncertainty)
        return complex(math.cos(angle), math.sin(angle))


def _direct(source: Real, model: _Optics) -> tuple[Real, float]:
    """Explicit finite sums, with lateral arrays bounded to one detector plane."""
    orientations, phases = model.phases.shape
    nz, ny, nx = model.shape
    fz, fy, fx = model.refinement
    dz, dy, dx = model.spacing
    py, px = model.pixels
    result = np.zeros((orientations, phases, nz, ny, nx))
    unilluminated = np.zeros((nz, ny, nx))
    a0, plus, minus = model.beams
    sole = np.count_nonzero(model.beams) == 1
    for jz, jy, jx in np.argwhere(source != 0):
        weight = source[jz, jy, jx]
        ds = _displacements(range(int(jz), int(jz) - fz * nz, -fz), dz, fz, Fraction(1 - fz, 2))
        for k, d in enumerate(ds):
            kernel = np.zeros((ny, nx))
            for ly in range(py):
                y = _displacements(
                    range(-int(jy), ny * fy - int(jy), fy),
                    dy,
                    fy,
                    Fraction(fy * (2 * ly + 1) - py, 2 * py),
                )
                for lx in range(px):
                    x = _displacements(
                        range(-int(jx), nx * fx - int(jx), fx),
                        dx,
                        fx,
                        Fraction(fx * (2 * lx + 1) - px, 2 * px),
                    )
                    kernel += model.density(np.hypot(y[:, None], x[None, :]), float(d)) / (py * px)
            contribution = weight * kernel
            unilluminated[k] += contribution
            for o in range(orientations):
                if sole:
                    illumination = np.ones(phases)
                else:
                    theta = model.lateral[o][jy, jx] * model.phases[o]
                    exact_d = Fraction(dz) * (2 * int(jz) + 1 - fz * (2 * k + 1)) / (2 * fz)
                    axial = model.axial_wave(exact_d, o) if a0 != 0 else 1.0
                    field = a0 * axial + plus * theta + minus * theta.conjugate()
                    illumination = field.real**2 + field.imag**2
                result[o, :, k] += illumination[:, None, None] * contribution
    return result, float(unilluminated.max())


def _kernel_cache(
    model: _Optics, source_shape: tuple[int, ...], offset: tuple[Fraction, Fraction]
) -> tuple[Real | Complex, Real, tuple[int, int]]:
    """Embed displacement kernels on the FINAL zero-padded lateral grid."""
    mz, my, mx = source_shape
    fz, fy, fx = model.refinement
    dz, dy, dx = model.spacing
    pad = (cast(int, fft.next_fast_len(2 * my - 1)), cast(int, fft.next_fast_len(2 * mx - 1)))
    ds = _displacements(range(mz - 1, mz - 1 - (2 * mz - fz), -1), dz, fz, Fraction(1 - fz, 2))
    count = (len(ds) + 1) // 2
    even = offset == (0, 0)
    cache = np.empty((count, pad[0], pad[1] // 2 + 1), dtype=np.float64 if even else np.complex128)
    iy, ix = np.arange(-(my - 1), my), np.arange(-(mx - 1), mx)
    y = _displacements(range(-(my - 1), my), dy, fy, offset[0])
    x = _displacements(range(-(mx - 1), mx), dx, fx, offset[1])
    radius = np.hypot(y[:, None], x[None, :])
    # Only bit-identical computed radii are shared. No distance quantization,
    # pupil approximation or missing displacement follows from this factoring.
    unique_radius, inverse, multiplicities = np.unique(
        radius, return_inverse=True, return_counts=True
    )
    del radius
    kernel_error = 0.0
    for a in range(count):
        embedded = np.zeros(pad)
        values = model.density(unique_radius, float(ds[a]), multiplicities)
        embedded[np.ix_(iy % pad[0], ix % pad[1])] = values[inverse].reshape(len(iy), len(ix))
        kernel_error += model.last_error_sum * (1 if a == len(ds) - 1 - a else 2)
        transformed = cast(Complex, fft.rfft2(embedded))
        cache[a] = transformed.real if even else transformed
    # Every normalized source cell is <=1. Summing the nonnegative error
    # kernel over ALL displacements bounds each finite, exterior-zero sum.
    model.convolution_error += kernel_error
    return cast(Real | Complex, cache), ds, pad


def _source_spectra(
    source: Real,
    maximum: float,
    lateral: Complex | None,
    harmonic: int,
    sine: bool,
    pad: tuple[int, int],
) -> Complex:
    spectra = np.empty((source.shape[0], pad[0], pad[1] // 2 + 1), dtype=np.complex128)
    factor: Real | float = 1.0
    if lateral is not None:
        wave = lateral if harmonic == 1 else lateral**2
        factor = wave.imag if sine else wave.real
    for j, plane in enumerate(source):
        spectra[j] = cast(Complex, fft.rfft2((plane / maximum) * factor, s=pad))
    return spectra


def _convolve(
    spectra: Complex,
    cache: Real | Complex,
    factors: Real,
    model: _Optics,
    pad: tuple[int, int],
    aligned: bool,
) -> Real:
    """Linear axial convolution in bounded lateral-frequency blocks.

    Each input is the lateral half-spectrum of a REAL field/kernel. Axial FFTs
    are complex FFTs; inverse real lateral transforms occur only after summing
    the real-kernel convolution, never on an arbitrary complex optical field.
    """
    mz, nyf, nxf = spectra.shape
    nz, ny, nx = model.shape
    fz, fy, fx = model.refinement
    length = len(factors)
    axial_pad = fft.next_fast_len(mz + length - 1)
    mirror = np.minimum(np.arange(length), length - 1 - np.arange(length))
    output = np.empty((nz, nyf, nxf), dtype=np.complex128)
    flat_source = spectra.reshape(mz, -1)
    flat_cache = cache.reshape(len(cache), -1)
    flat_output = output.reshape(nz, -1)
    selected = fz * np.arange(nz) + mz - 1
    for start in range(0, nyf * nxf, 2048):
        end = min(start + 2048, nyf * nxf)
        left = cast(Complex, fft.fft(flat_source[:, start:end], n=axial_pad, axis=0))
        right = cast(
            Complex, fft.fft(flat_cache[mirror, start:end] * factors[:, None], n=axial_pad, axis=0)
        )
        left *= right
        del right
        values = cast(Complex, fft.ifft(left, axis=0, overwrite_x=True))
        flat_output[:, start:end] = values[selected]
    result = np.empty((nz, ny, nx))
    for k in range(nz):
        plane = cast(Real, fft.irfft2(output[k], s=pad))
        if aligned:
            result[k] = plane[: ny * fy, : nx * fx].reshape(ny, fy, nx, fx).mean(axis=(1, 3))
        else:
            result[k] = plane[: ny * fy : fy, : nx * fx : fx]
    return result


def _dense(source: Real, maximum: float, model: _Optics) -> tuple[Real, float]:
    """Harmonic factorization of the SAME finite source/pupil/pixel sum."""
    orientations, phases = model.phases.shape
    result = np.zeros((orientations, phases, *model.shape))
    unilluminated = np.zeros(model.shape)
    _, fy, fx = model.refinement
    py, px = model.pixels
    aligned = (fy, fx) == (py, px)
    offsets = (
        [(Fraction(0), Fraction(0))]
        if aligned
        else [
            (Fraction(fy * (2 * ly + 1) - py, 2 * py), Fraction(fx * (2 * lx + 1) - px, 2 * px))
            for ly in range(py)
            for lx in range(px)
        ]
    )
    a0, plus, minus = model.beams
    c = a0 * (plus + minus)
    b = a0 * (minus - plus)
    g2 = plus * minus
    for offset in offsets:
        cache, ds, pad = _kernel_cache(model, source.shape, offset)
        spectra = _source_spectra(source, maximum, None, 0, False, pad)
        dc = _convolve(spectra, cache, np.ones(len(ds)), model, pad, aligned) / len(offsets)
        del spectra
        unilluminated += dc
        result += dc
        for o in range(orientations):
            fz = model.refinement[0]
            axial: Complex = (
                np.array(
                    [
                        model.axial_wave(
                            Fraction(model.spacing[0])
                            * (-2 * (a - (source.shape[0] - 1)) - (fz - 1))
                            / (2 * fz),
                            o,
                        )
                        for a in range(len(ds))
                    ]
                )
                if c != 0 or b != 0
                else np.ones(len(ds), dtype=np.complex128)
            )
            phase = model.phases[o]
            for harmonic, gain in ((1, c), (2, g2)):
                if gain == 0 and (harmonic == 2 or b == 0):
                    continue
                for sine in (False, True):
                    spectra = _source_spectra(
                        source, maximum, model.lateral[o], harmonic, sine, pad
                    )
                    factors = axial.real if harmonic == 1 else np.ones(len(ds))
                    component = _convolve(spectra, cache, factors, model, pad, aligned)
                    coefficient = -(phase**harmonic).imag if sine else (phase**harmonic).real
                    result[o] += (
                        (2 * gain / len(offsets)) * coefficient[:, None, None, None] * component
                    )
                    if harmonic == 1 and b != 0:
                        component = _convolve(spectra, cache, axial.imag, model, pad, aligned)
                        coefficient = phase.real if sine else phase.imag
                        result[o] -= (
                            (2 * b / len(offsets)) * coefficient[:, None, None, None] * component
                        )
                    del spectra
    model.convolution_error /= len(offsets)
    return result, float(unilluminated.max())


def _scale_output(result: Real, peak: float, factors: tuple[float, ...], error: float) -> Real:
    """Apply dimensional scale without intermediate overflow or tiny-weight loss."""
    if not math.isfinite(peak) or peak <= 0 or not np.isfinite(result).all():
        _range("finite-equation accumulation lost representability")
    allowance = 1e-5 * peak - error
    if allowance < 0 or not math.isfinite(error):
        _range("pupil/phase evaluation cannot resolve the unilluminated absolute allowance")
    if float(result.min()) < -allowance:
        _range("convolution cancellation exceeds the absolute allowance")
    np.maximum(result, 0, out=result)
    mantissa, exponent = 1.0, 0
    for factor in factors:
        m, e = math.frexp(factor)
        mantissa *= m
        exponent += e
    m, e = math.frexp(mantissa)
    exponent += e
    # Each scratch owns its storage. Reuse it between arithmetic stages without
    # changing their order or overwriting the reference used for comparison.
    scaled = result * m
    np.ldexp(scaled, exponent, out=scaled)
    if not np.isfinite(scaled).all():
        _range("expected output exceeds float64 range")
    # Undo scaling BEFORE comparing the actual storage error. This catches
    # impossible subnormal quantization without an arbitrary magnitude floor.
    restored = np.ldexp(scaled, -exponent)
    restored /= m
    if not np.isfinite(restored).all():
        _range("float64 output quantization exceeds the absolute allowance")
    restored -= result
    np.abs(restored, out=restored)
    if float(np.max(restored)) > allowance:
        _range("float64 output quantization exceeds the absolute allowance")
    return np.ascontiguousarray(scaled)


def expected_images(
    source_e: Any,
    *,
    detector_spacing_um_zyx: Any,
    source_refinement_zyx: Any,
    carriers_yx_per_um: Any,
    phases_rad: Any,
    beam_amplitudes: Any,
    excitation_um: Any,
    emission_um: Any,
    refractive_index: Any,
    detection_na: Any,
    pupil_order: Any,
    pixel_subsamples_yx: Any,
) -> Real:
    """Return owned native-float64 (orientation, phase, z, y, x) electrons.

    All sites, source weights, clear-pupil rule and arithmetic/range semantics
    are specified in ``docs/contracts/simulation-optics-v1.md``. No camera,
    noise, calibration, reconstruction or persistence is performed.
    """
    source = _array(source_e, "source_e")
    carriers = _array(carriers_yx_per_um, "carriers_yx_per_um")
    phases = _array(phases_rad, "phases_rad")
    refinement = _counts(source_refinement_zyx, 3, "source_refinement_zyx")
    pixels = _counts(pixel_subsamples_yx, 2, "pixel_subsamples_yx")
    spacing = _coefficients(detector_spacing_um_zyx, "detector_spacing_um_zyx")
    beams = _coefficients(beam_amplitudes, "beam_amplitudes", zero=True)
    excitation = _coefficient(excitation_um, "excitation_um")
    emission = _coefficient(emission_um, "emission_um")
    index = _coefficient(refractive_index, "refractive_index")
    aperture = _coefficient(detection_na, "detection_na")
    if type(pupil_order) is not int or pupil_order <= 0:
        _invalid("pupil_order must be a positive built-in integer")
    if source.ndim != 3 or 0 in source.shape or np.any(source < 0):
        _invalid("source_e must be nonempty, nonnegative and rank three")
    if any(n % f for n, f in zip(source.shape, refinement, strict=True)):
        _invalid("source shape must be divisible by its refinements")
    if carriers.ndim != 2 or carriers.shape[1] != 2 or not len(carriers):
        _invalid("carriers must have shape (O,2), O>=1")
    if phases.ndim != 2 or phases.shape[0] != len(carriers) or phases.shape[1] == 0:
        _invalid("phases must have shape (O,P), P>=1")
    if aperture > index or not any(beams):
        _invalid("aperture exceeds index, or all beam amplitudes are zero")
    # Exact rational comparison prevents squared-norm overflow and preserves the
    # closed carrier boundary after native-float64 normalization.
    k0 = Fraction(index) / Fraction(excitation)
    squares = [Fraction(float(qy)) ** 2 + Fraction(float(qx)) ** 2 for qy, qx in carriers]
    if any(q2 > k0**2 for q2 in squares):
        _invalid("carrier lies outside the excitation sphere")
    shape = tuple(n // f for n, f in zip(source.shape, refinement, strict=True))
    maximum = float(source.max())
    if maximum == 0:
        return np.zeros((*phases.shape, *shape))
    # Only arithmetic operations belonging to this evaluator are scoped. No
    # warning filters, exception blanket, or process-wide NumPy settings change.
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        normalized_beams = np.array(beams) / max(beams)
        normalized_beams /= np.linalg.norm(normalized_beams)
        frequency = aperture / emission
        nu = index / emission
        beta = aperture / index
        if not math.isfinite(frequency) or not math.isfinite(nu):
            _range("nonfinite pupil frequency")
        nodes, weights = special.roots_legendre(pupil_order)
        nodes, weights = (nodes + 1) / 2, weights / 2
        radial = 2 * math.pi * frequency * np.sqrt(nodes)
        # Remove a common axial phase: it cancels exactly from |A|**2. Q=1
        # therefore requires no axial evaluation, however large the defocus.
        root = np.sqrt(1 - beta**2 * nodes)
        axial = -2 * math.pi * nu * (beta**2 * nodes) / (root + 1)
        axial -= axial[0]
        kappas, kappa_errors = _axial_frequencies(k0, squares)
        lateral = [
            _wave(_turns(float(qy), spacing[1], refinement[1], source.shape[1]))[:, None]
            * _wave(_turns(float(qx), spacing[2], refinement[2], source.shape[2]))[None, :]
            for qy, qx in carriers
        ]
        model = _Optics(
            spacing,
            refinement,
            pixels,
            shape,
            normalized_beams,
            kappas,
            kappa_errors,
            lateral,
            np.cos(phases) + 1j * np.sin(phases),
            radial,
            axial,
            weights,
        )
        operations = int(np.count_nonzero(source)) * math.prod(shape) * math.prod(pixels)
        total = math.fsum(float(np.sum(plane / maximum)) for plane in source)
        if operations <= 1_000_000:
            result, peak = _direct(source / maximum, model)
            numerical_error = model.error * total
        else:
            result, peak = _dense(source, maximum, model)
            numerical_error = model.convolution_error
        error = (
            3 * numerical_error
            + model.phase_error * peak
            + 512 * _EPS * (1 + math.log2(max(2, operations))) * total
        )
        return _scale_output(
            result, peak, (maximum, spacing[1], spacing[2], math.pi, frequency, frequency), error
        )
