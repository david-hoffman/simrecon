"""Independent finite-sum reconstruction fixtures; no production numerical helper.

Decimal arithmetic at 85 digits resolves stored float64 least-squares truth.
Normal equations are used only in this small, well-conditioned *oracle*.
They are not an approved production solver. Fourier roots use a Taylor series.
"""

from __future__ import annotations

import importlib
import math
import sys
import warnings
from dataclasses import dataclass
from decimal import Decimal, localcontext
from functools import cache
from typing import Any


def source_free_diagnostics() -> None:
    """Render locations and messages without source lines or local variables."""

    def warning(
        message: Any, category: Any, filename: str, lineno: int, file: Any = None, line: Any = None
    ) -> None:
        stream = file or sys.stderr
        stream.write(f"{filename}:{lineno}: {category.__name__}: {message}\n")

    def exception(kind: Any, value: Any, traceback: Any) -> None:
        while traceback is not None:
            frame = traceback.tb_frame
            sys.stderr.write(f"{frame.f_code.co_filename}:{traceback.tb_lineno}\n")
            traceback = traceback.tb_next
        sys.stderr.write(f"{kind.__name__}: {value}\n")

    warnings.showwarning = warning
    sys.excepthook = exception


source_free_diagnostics()
import numpy as np  # noqa: E402

PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406286"
    "2089986280348253421170679"
)


def dec(value: Any) -> Decimal:
    """Interpret a represented float64 coordinate as an exact real number."""
    return Decimal.from_float(float(value))


@dataclass(frozen=True)
class Z:
    """A minimal high-precision complex scalar for the independent oracle."""

    re: Decimal = Decimal(0)
    im: Decimal = Decimal(0)

    def __add__(self, other: Z) -> Z:
        """Add independently represented complex coordinates."""
        return Z(self.re + other.re, self.im + other.im)

    def __mul__(self, other: Z) -> Z:
        """Multiply without converting to float64 complex arithmetic."""
        return Z(self.re * other.re - self.im * other.im, self.re * other.im + self.im * other.re)

    def scale(self, value: Decimal) -> Z:
        return Z(self.re * value, self.im * value)

    def conj(self) -> Z:
        return Z(self.re, -self.im)

    def power(self) -> Decimal:
        return self.re * self.re + self.im * self.im

    def rounded(self) -> complex:
        return complex(float(self.re), float(self.im))

    @classmethod
    def stored(cls, value: Any) -> Z:
        return cls(dec(complex(value).real), dec(complex(value).imag))


@cache
def root(turns: Decimal) -> Z:
    """Compute exp(2*pi*i*turns) with a convergent independent root series."""
    with localcontext() as ctx:
        ctx.prec = 85
        turns = turns % 1
        if turns > Decimal("0.5"):
            turns -= 1
        angle = 2 * PI * turns
        cosine, sine = Decimal(1), angle
        ct, st = cosine, sine
        for n in range(1, 180):
            ct *= -angle * angle / ((2 * n - 1) * (2 * n))
            st *= -angle * angle / ((2 * n) * (2 * n + 1))
            cosine += ct
            sine += st
            if abs(ct) + abs(st) < Decimal("1e-90"):
                break
        return Z(+cosine, +sine)


def modes(size: int) -> list[int]:
    """Return the contract's centered signed integer bins."""
    return list(range(-(size // 2), (size + 1) // 2))


def solve3(matrix: list[list[Decimal]], rhs: list[Decimal]) -> list[Decimal]:
    """Solve the oracle's three-coordinate system by pivoted elimination."""
    rows = [list(row) + [value] for row, value in zip(matrix, rhs, strict=True)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(rows[row][col]))
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        assert scale != 0, "Oracle fixture must have a full-rank phase matrix"
        rows[col] = [value / scale for value in rows[col]]
        for row in range(3):
            if row != col:
                scale = rows[row][col]
                rows[row] = [a - scale * b for a, b in zip(rows[row], rows[col], strict=True)]
    return [rows[row][3] for row in range(3)]


def finite_transform(plane: list[list[Z]]) -> list[list[Z]]:
    """Evaluate Fourier-series amplitudes by negative-exponential finite sums."""
    ny, nx = len(plane), len(plane[0])
    result = []
    for j in modes(ny):
        row = []
        for k in modes(nx):
            total = Z()
            for y in range(ny):
                for x in range(nx):
                    total += plane[y][x] * root(-Decimal(j * y) / ny - Decimal(k * x) / nx)
            row.append(total.scale(Decimal(1) / (ny * nx)))
        result.append(row)
    return result


def interpolate(plane: list[list[Z]], y: float, x: float) -> Z:
    """Direct scalar bilinear reference with closed edges and exact outside zero."""
    ny, nx = len(plane), len(plane[0])
    ys, xs = modes(ny), modes(nx)
    if not (ys[0] <= y <= ys[-1] and xs[0] <= x <= xs[-1]):
        return Z()
    yl, xl = math.floor(y), math.floor(x)
    yh, xh = min(yl + 1, ys[-1]), min(xl + 1, xs[-1])
    wy, wx = dec(y) - yl, dec(x) - xl
    value = Z()
    for yy, weight_y in ((yl, 1 - wy), (yh, wy)):
        for xx, weight_x in ((xl, 1 - wx), (xh, wx)):
            value += plane[yy - ys[0]][xx - xs[0]].scale(weight_y * weight_x)
    return value


def synthesize(spectrum: list[list[Z]]) -> np.ndarray:
    """Use the unnormalized positive-exponential synthesis, independent of FFTs."""
    ny, nx = len(spectrum), len(spectrum[0])
    output = np.empty((ny, nx), dtype=np.complex128)
    for y in range(ny):
        for x in range(nx):
            total = Z()
            for iy, j in enumerate(modes(ny)):
                for ix, k in enumerate(modes(nx)):
                    total += spectrum[iy][ix] * root(Decimal(j * y) / ny + Decimal(k * x) / nx)
            output[y, x] = total.rounded()
    return output


def estimator(arguments: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Derive the selected estimator from stored arrays, without calling product."""
    images = np.asarray(arguments["images"], dtype=np.float64)
    phases = np.asarray(arguments["phases_rad"], dtype=np.float64)
    transfer = arguments["otf"].values
    rcount, count, ny, nx = images.shape
    with localcontext() as ctx:
        ctx.prec = 85
        bands = []
        for r in range(rcount):
            design = [[Decimal(1), dec(np.cos(phi)), dec(np.sin(phi))] for phi in phases[r]]
            gram = [
                [sum((row[i] * row[j] for row in design), Decimal(0)) for j in range(3)]
                for i in range(3)
            ]
            dc = [[Z() for _ in range(nx)] for _ in range(ny)]
            plus = [[Z() for _ in range(nx)] for _ in range(ny)]
            for y in range(ny):
                for x in range(nx):
                    b = [dec(images[r, p, y, x]) for p in range(count)]
                    rhs = [
                        sum((row[i] * v for row, v in zip(design, b, strict=True)), Decimal(0))
                        for i in range(3)
                    ]
                    a, c, s = solve3(gram, rhs)
                    dc[y][x], plus[y][x] = Z(a), Z(c / 2, -s / 2)
            minus = [[value.conj() for value in row] for row in plus]
            bands.append((finite_transform(dc), finite_transform(plus), finite_transform(minus)))
        h = [[Z.stored(value) for value in row] for row in transfer]
        output = []
        dy, dx = arguments["otf"].pixel_size_um
        for iy, j in enumerate(modes(2 * ny)):
            row = []
            for ix, k in enumerate(modes(2 * nx)):
                numerator, denominator = Z(), Decimal(0)
                for r in range(rcount):
                    sy = float(arguments["wavevectors_per_um"][r, 0]) * ny * float(dy)
                    sx = float(arguments["wavevectors_per_um"][r, 1]) * nx * float(dx)
                    a = dec(arguments["brightness"][r])
                    m = dec(arguments["modulation"][r])
                    for band, shift, gain in zip(
                        bands[r], (0, 1, -1), (a, a * m / 2, a * m / 2), strict=True
                    ):
                        yy, xx = float(j + shift * sy), float(k + shift * sx)
                        d = interpolate(band, yy, xx)
                        t = interpolate(h, yy, xx).scale(gain)
                        numerator += t.conj() * d
                        denominator += t.power()
                denominator += dec(arguments["regularization"])
                value = numerator.scale(1 / denominator) if denominator > 0 else Z()
                row.append(value.scale(dec(arguments["apodization"][iy, ix])))
            output.append(row)
        spectrum = np.array([[value.rounded() for value in row] for row in output])
        return spectrum, synthesize(output)


def public() -> Any:
    """Import only the public package after installing source-free diagnostics."""
    return importlib.import_module("simrecon")


def record(
    values: np.ndarray,
    spacing: Any = (0.5, 0.25),
    origin: Any = (0, 0),
    source: Any = "  independent analytic calibration  ",
) -> Any:
    """Directly construct the public record; never treat construction as validation."""
    ny, nx = values.shape
    with np.errstate(all="ignore"):
        fy = np.array([float(Decimal(j) / ny / dec(spacing[0])) for j in modes(ny)])
        fx = np.array([float(Decimal(j) / nx / dec(spacing[1])) for j in modes(nx)])
    return public().Otf2D(
        values=values,
        fy_per_um=fy,
        fx_per_um=fx,
        pixel_size_um=spacing,
        origin_yx=origin,
        source=source,
    )


def basic(shape: tuple[int, int] = (3, 4), orientations: int = 1) -> dict[str, Any]:
    """Create a signed constant, unequal seven-phase, zero-wave reference case."""
    ny, nx = shape
    phases = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
    return dict(
        images=np.full((orientations, 7, ny, nx), -2.5),
        otf=record(np.ones(shape, dtype=np.complex128)),
        phases_rad=np.tile(phases, (orientations, 1)),
        wavevectors_per_um=np.zeros((orientations, 2)),
        modulation=np.full(orientations, 0.5),
        brightness=np.ones(orientations),
        regularization=0.0,
        apodization=np.ones((2 * ny, 2 * nx)),
    )


def phantom(fractional: bool = False) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Create asymmetric Fourier object and acquisitions by circular finite sums.

    The nonnegative PSF is a product of two low-order cosine polynomials.
    The analytic OTF has |jy|<=1, |jx|<=2 support and a one-pixel displacement.
    Object modes (0,3) and (2,1) have zero DC transfer but illuminated recovery.
    All products remain inside the 7x9 detector's signed mode rectangle.
    """
    ny, nx = 7, 9
    phases = np.array(
        [[-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81], [-1.11, 0.05, 0.89, 2.10, 3.59, 4.21, 6.77]]
    )
    shifts = [(0.0, 1.0), (1.0, 0.0)] if not fractional else [(0.5, 0.5), (-0.5, 0.5)]
    brightness, modulation = np.array([0.75, 1.5]), np.array([0.625, 0.875])
    with localcontext() as ctx:
        ctx.prec = 85
        coeff = {
            (0, 0): Z(Decimal(4)),
            (1, 0): Z(Decimal("0.25"), Decimal("0.4")),
            (0, 3): Z(Decimal("-0.35"), Decimal("0.2")),
            (2, 1): Z(Decimal("0.15"), Decimal("-0.3")),
        }
        for (j, k), value in list(coeff.items()):
            if (j, k) != (0, 0):
                coeff[-j, -k] = value.conj()

        def object_value(y: int, x: int, yn: int, xn: int) -> Z:
            result = Z()
            for (j, k), value in coeff.items():
                result += value * root(Decimal(j * y) / yn + Decimal(k * x) / xn)
            return result

        kernel = []
        for y in range(ny):
            row = []
            for x in range(nx):
                vy = 1 + Decimal("0.8") * root(Decimal(y - 1) / ny).re
                vx = (
                    1
                    + Decimal("0.6") * root(Decimal(x - 1) / nx).re
                    + Decimal("0.2") * root(Decimal(2 * (x - 1)) / nx).re
                )
                row.append(vy * vx / (ny * nx))
            kernel.append(row)
        values = np.zeros((ny, nx), dtype=np.complex128)
        for iy, j in enumerate(modes(ny)):
            for ix, k in enumerate(modes(nx)):
                gy = {0: Decimal(1), -1: Decimal("0.4"), 1: Decimal("0.4")}.get(j, Decimal(0))
                gx = {
                    0: Decimal(1),
                    -1: Decimal("0.3"),
                    1: Decimal("0.3"),
                    -2: Decimal("0.1"),
                    2: Decimal("0.1"),
                }.get(k, Decimal(0))
                values[iy, ix] = root(-Decimal(j) / ny - Decimal(k) / nx).scale(gy * gx).rounded()
        images = np.empty((2, 7, ny, nx))
        obj = [[object_value(y, x, ny, nx).re for x in range(nx)] for y in range(ny)]
        for r, (sy, sx) in enumerate(shifts):
            for p, phi in enumerate(phases[r]):
                cosine, sine = dec(np.cos(phi)), dec(np.sin(phi))
                for y in range(ny):
                    for x in range(nx):
                        total = Decimal(0)
                        for hy in range(ny):
                            for hx in range(nx):
                                yy, xx = (y - hy) % ny, (x - hx) % nx
                                wave = root(dec(sy) * yy / ny + dec(sx) * xx / nx)
                                illumination = dec(brightness[r]) * (
                                    1 + dec(modulation[r]) * (wave.re * cosine - wave.im * sine)
                                )
                                total += kernel[hy][hx] * obj[yy][xx] * illumination
                        images[r, p, y, x] = float(total)
        truth_spectrum = np.zeros((2 * ny, 2 * nx), dtype=np.complex128)
        for (j, k), value in coeff.items():
            truth_spectrum[j + ny, k + nx] = value.rounded()
        truth = np.array(
            [
                [object_value(y, x, 2 * ny, 2 * nx).rounded() for x in range(2 * nx)]
                for y in range(2 * ny)
            ]
        )
        arguments = basic((ny, nx), 2)
        arguments.update(
            images=images,
            otf=record(values),
            phases_rad=phases,
            brightness=brightness,
            modulation=modulation,
            wavevectors_per_um=np.array([[sy / (ny * 0.5), sx / (nx * 0.25)] for sy, sx in shifts]),
        )
        return arguments, truth_spectrum, truth


def accuracy_budget(arguments: dict[str, Any]) -> Decimal:
    """Evaluate the contract's informative absolute budget without overflow."""
    r, n, ny, nx = arguments["images"].shape
    with localcontext() as ctx:
        ctx.prec = 85
        b = dec(np.max(np.abs(arguments["images"].astype(np.float64)))) / dec(
            min(arguments["brightness"])
        )
        eps, small = Decimal(2) ** -52, Decimal(2) ** -1074
        return +(8192 * r * n * (4 * ny * nx) * eps * b + 8 * (4 * ny * nx) * small)


def effective_denominators(arguments: dict[str, Any]) -> np.ndarray:
    """Measure oracle eligibility using scalar high-precision effective transfers."""
    rcount, _, ny, nx = arguments["images"].shape
    dy, dx = arguments["otf"].pixel_size_um
    h = [[Z.stored(value) for value in row] for row in arguments["otf"].values]
    denominator = np.zeros((2 * ny, 2 * nx))
    with localcontext() as ctx:
        ctx.prec = 85
        for iy, j in enumerate(modes(2 * ny)):
            for ix, k in enumerate(modes(2 * nx)):
                value = Decimal(0)
                for r in range(rcount):
                    sy = float(arguments["wavevectors_per_um"][r, 0]) * ny * float(dy)
                    sx = float(arguments["wavevectors_per_um"][r, 1]) * nx * float(dx)
                    a, m = dec(arguments["brightness"][r]), dec(arguments["modulation"][r])
                    for shift, gain in zip((0, 1, -1), (a, a * m / 2, a * m / 2), strict=True):
                        value += (
                            interpolate(h, float(j + shift * sy), float(k + shift * sx))
                            .scale(gain)
                            .power()
                        )
                denominator[iy, ix] = float(value)
    return denominator


def assert_coordinates(
    actual: Any, stored_reference: Any, budget: Decimal, *, analytic: Any = None
) -> None:
    """Check the approved coordinate envelope, optionally rebased to analytic truth.

    A rounded reference contributes half an ulp of observer uncertainty. The
    85-digit finite-sum observer additionally receives 1e-40 of the budget;
    this exceeds its arithmetic error for the checked informative fixtures.
    Analytic comparisons add the independently measured stored/analytic bias.
    Neither comparison imposes a second, tighter production accuracy bound.
    """
    observed, stored = np.broadcast_arrays(np.asarray(actual), np.asarray(stored_reference))
    assert np.all(np.isfinite(observed)), "Nonfinite output coordinate"
    assert np.all(np.isfinite(stored)), "Nonfinite observer reference"
    target = stored if analytic is None else np.broadcast_to(np.asarray(analytic), stored.shape)
    assert np.all(np.isfinite(target)), "Nonfinite analytic reference"
    with localcontext() as ctx:
        ctx.prec = 85
        for value, reference, truth in zip(observed.flat, stored.flat, target.flat, strict=True):
            for got, wanted, exact_stored in (
                (complex(value).real, complex(truth).real, complex(reference).real),
                (complex(value).imag, complex(truth).imag, complex(reference).imag),
            ):
                bias = abs(dec(wanted) - dec(exact_stored)) if analytic is not None else Decimal(0)
                rounding = dec(math.ulp(exact_stored)) / 2
                # Rebasing to an independently rounded analytic array needs its
                # own final-coordinate quantization allowance as well.
                if analytic is not None:
                    rounding += dec(math.ulp(wanted)) / 2
                allowed = budget + bias + rounding + abs(budget) * Decimal("1e-40")
                error = abs(dec(got) - dec(wanted))
                assert error <= allowed, f"Coordinate error {error} exceeds envelope {allowed}"


def assert_frequency_coordinates(actual: Any, size: int, spacing: float) -> None:
    """Check physical signed bins against the approved frequency accuracy scale."""
    with localcontext() as ctx:
        ctx.prec = 85
        eps, small = Decimal(2) ** -52, Decimal(2) ** -1074
        for stored, mode in zip(actual, modes(2 * size), strict=True):
            exact = Decimal(mode) / size / dec(spacing)
            if mode == 0:
                assert stored == 0
            else:
                assert np.isfinite(stored) and stored != 0
                allowed = 8 * eps * abs(exact) + small
                assert abs(dec(stored) - exact) <= allowed * (1 + Decimal("1e-65"))


def phase_forward_envelope(phases: Any, observations: Any) -> tuple[list[Decimal], Decimal]:
    """Derive a conservative necessary forward consequence of phase backward error.

    Frobenius norms give a>=||K||2 and s<=sigma_min(K) via s=1/||K+||F.
    Using these bounds in the approved finite forward-error formula widens it.
    This smoke observer does not replace the prerequisite backward-error suite.
    """
    with localcontext() as ctx:
        ctx.prec = 85
        design = [
            [Decimal(1), 2 * dec(np.cos(phi)), -2 * dec(np.sin(phi))]
            for phi in np.asarray(phases, dtype=np.float64)
        ]
        gram = [
            [sum((row[i] * row[j] for row in design), Decimal(0)) for j in range(3)]
            for i in range(3)
        ]
        b = [dec(value) for value in np.asarray(observations, dtype=np.float64)]
        rhs = [
            sum((row[i] * value for row, value in zip(design, b, strict=True)), Decimal(0))
            for i in range(3)
        ]
        truth = solve3(gram, rhs)
        columns = [solve3(gram, [Decimal(int(i == j)) for i in range(3)]) for j in range(3)]
        inverse = [[columns[j][i] for j in range(3)] for i in range(3)]
        pinv = [
            [sum((inverse[i][j] * row[j] for j in range(3)), Decimal(0)) for row in design]
            for i in range(3)
        ]
        a = sum((value * value for row in design for value in row), Decimal(0)).sqrt()
        s = 1 / sum((value * value for row in pinv for value in row), Decimal(0)).sqrt()
        eta = 128 * max(len(design), 3) * Decimal(2) ** -52
        alpha = eta * a
        assert alpha < s, "Phase smoke fixture lacks an informative forward consequence"
        beta = eta * sum((value * value for value in b), Decimal(0)).sqrt()
        znorm = sum((value * value for value in truth), Decimal(0)).sqrt()
        residual = [
            value - sum((row[j] * truth[j] for j in range(3)), Decimal(0))
            for row, value in zip(design, b, strict=True)
        ]
        rnorm = sum((value * value for value in residual), Decimal(0)).sqrt()
        bound = (
            (beta + alpha * znorm) / (s - alpha)
            + alpha * rnorm / (s - alpha) ** 2
            + Decimal(3).sqrt() * Decimal(2) ** -1075
        )
        return truth, +bound
