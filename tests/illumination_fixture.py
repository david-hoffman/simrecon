"""Independent finite-sum illumination fixtures; no simrecon imports.

The Decimal normal-equation solve is an *oracle*, not a proposed runtime
algorithm. Its 90-digit arithmetic treats stored float64 trig/data entries as
exact. Only well-conditioned phase matrices use this oracle. Fourier sums use
extended precision and explicit signed modes, without an FFT or product helper.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def modes(n: int) -> NDArray[np.int64]:
    return np.arange(-(n // 2), n - n // 2, dtype=np.int64)


def roots(n: int, sign: int = -1) -> NDArray[np.clongdouble]:
    """Explicit Fourier matrix, with exact quadrant roots when available."""
    indices = modes(n)[:, None] * np.arange(n)[None, :]
    angle = sign * 2 * np.arccos(np.longdouble(-1)) * indices / n
    result = np.cos(angle).astype(np.clongdouble) + 1j * np.sin(angle)
    for row in range(n):
        for col in range(n):
            numerator = sign * 4 * int(indices[row, col])
            if numerator % n == 0:
                result[row, col] = (1, 1j, -1, -1j)[(numerator // n) % 4]
    return result


def finite_dft(values: NDArray, *, normalized: bool = True) -> NDArray:
    ny, nx = values.shape
    result = roots(ny) @ values.astype(np.clongdouble) @ roots(nx).T
    return result / (ny * nx) if normalized else result


def phase_coefficients(
    images: NDArray, steps: NDArray, *, precision: int = 90
) -> tuple[NDArray, NDArray]:
    """90-digit minimizer for actual converted observations, scaled by B."""
    converted = images.astype(np.float64)
    angles = steps.astype(np.float64)
    peak = float(np.max(np.abs(converted)))
    if peak == 0:
        return np.zeros(images.shape[1:]), np.zeros(images.shape[1:], complex)
    with localcontext() as context:
        context.prec = precision
        matrix = [
            [Decimal(1), Decimal(float(c)), Decimal(float(s))]
            for c, s in zip(np.cos(angles), np.sin(angles), strict=True)
        ]
        gram: list[list[Decimal]] = [
            [sum((row[j] * row[k] for row in matrix), Decimal(0)) for k in range(3)]
            for j in range(3)
        ]
        # Invert the tiny exact represented Gram matrix by pivoted elimination.
        augmented = [
            row.copy() + [Decimal(int(j == k)) for k in range(3)] for j, row in enumerate(gram)
        ]
        for j in range(3):
            pivot = max(range(j, 3), key=lambda k: abs(augmented[k][j]))
            augmented[j], augmented[pivot] = augmented[pivot], augmented[j]
            divisor = augmented[j][j]
            augmented[j] = [value / divisor for value in augmented[j]]
            for k in range(3):
                if k != j:
                    factor = augmented[k][j]
                    augmented[k] = [
                        a - factor * b for a, b in zip(augmented[k], augmented[j], strict=True)
                    ]
        inverse = [row[3:] for row in augmented]
        certificate_floor = Decimal("1e-75")
        inverse_defect = max(
            abs(
                sum((gram[j][k] * inverse[k][column] for k in range(3)), Decimal(0))
                - int(j == column)
            )
            for j in range(3)
            for column in range(3)
        )
        assert inverse_defect < certificate_floor
        # The independently computed inverse defect also certifies full rank:
        # ||I-G*inverse||_2 <= 3*max_entry_defect < 1. Decimal arithmetic error
        # is far smaller than 1e-75 for these bounded, well-conditioned matrices.
        dc = np.empty(images.shape[1:], np.longdouble)
        c1 = np.empty(images.shape[1:], np.clongdouble)
        for index in np.ndindex(images.shape[1:]):
            data = [
                Decimal(float(converted[(p, *index)])) / Decimal(peak) for p in range(len(angles))
            ]
            rhs = [
                sum(row[j] * value for row, value in zip(matrix, data, strict=True))
                for j in range(3)
            ]
            coefficients = [sum(a * b for a, b in zip(row, rhs, strict=True)) for row in inverse]
            normal_defect = max(
                abs(sum((gram[j][k] * coefficients[k] for k in range(3)), Decimal(0)) - rhs[j])
                for j in range(3)
            )
            assert normal_defect < certificate_floor * (1 + max(abs(value) for value in rhs))
            dc[index] = np.longdouble(str(coefficients[0]))
            c1[index] = np.longdouble(str(coefficients[1] / 2)) - 1j * np.longdouble(
                str(coefficients[2] / 2)
            )
        return dc, c1


@dataclass(frozen=True)
class FitTruth:
    """Store independent regression and informative-regime diagnostics."""

    gain: complex
    residual: float
    overlap: int
    condition: float
    x_norm_over_b: float
    y_norm_over_b: float
    correlation: float

    @property
    def informative(self) -> bool:
        return (
            self.condition <= 10
            and self.x_norm_over_b >= 0.125
            and self.y_norm_over_b >= 0.125
            and self.correlation >= 0.25
            and 1e-4 <= abs(self.gain) <= 10
        )


def stored_fit(
    images: NDArray, steps: NDArray, transfer: NDArray, carrier: tuple[int, int]
) -> FitTruth:
    """Cross-weighted regression for stored observations, with closed overlap."""
    dc, c1 = phase_coefficients(images, steps)
    d0, dp = finite_dft(dc), finite_dft(c1)
    ny, nx = transfer.shape
    ky, kx = carrier
    x, y = [], []
    for j, qy in enumerate(modes(ny)):
        for column, qx in enumerate(modes(nx)):
            jy, lx = int(qy + ky + ny // 2), int(qx + kx + nx // 2)
            if 0 <= jy < ny and 0 <= lx < nx:
                x.append(np.clongdouble(transfer[jy, lx]) * d0[j, column])
                y.append(np.clongdouble(transfer[j, column]) * dp[jy, lx])
    xx, yy = np.asarray(x, np.clongdouble), np.asarray(y, np.clongdouble)
    xn = np.sqrt(np.sum(np.abs(xx) ** 2))
    yn = np.sqrt(np.sum(np.abs(yy) ** 2))
    u, v = xx / xn, yy / yn
    correlation = np.sum(u.conj() * v)
    gain = (yn / xn) * correlation
    residual = np.sqrt(np.sum(np.abs(v - correlation * u) ** 2))
    matrix = np.column_stack((np.ones(len(steps)), np.cos(steps), np.sin(steps)))
    return FitTruth(
        complex(gain),
        float(residual),
        len(x),
        float(np.linalg.cond(matrix)),
        float(xn),
        float(yn),
        float(abs(correlation)),
    )


@dataclass(frozen=True)
class Acquisition:
    """Store public inputs and separately known finite-model parameters."""

    images: NDArray
    steps: Array
    transfer: ComplexArray
    carrier: tuple[int, int]
    specimen: Array
    brightness: float
    modulation: float
    theta: float
    pixel_size: tuple[float, float] = (0.2, 0.35)
    origin: tuple[int, int] = (0, 0)
    source: str = " independent signed complex finite kernel "


def acquisition(
    shape: tuple[int, int] = (5, 7),
    *,
    carrier: tuple[int, int] = (1, -1),
    brightness: float = 1.0,
    modulation: float = 0.9,
    theta: float = 0.7,
    steps: NDArray | None = None,
    off_model: bool = False,
    specimen: NDArray | None = None,
) -> Acquisition:
    """Finite circular forward model, explicit represented step rotations.

    Object support is {(0,0),(0,+/-1),(+/-1,0),(+/-1,+/-1)}. On the default
    odd grid its carrier-shifted modes remain within the detector: no alias.
    The kernel has masses 3/8 at zero, 1/8 at +y, 1/2 at +x.
    """
    ny, nx = shape
    if steps is None:
        steps = np.array([-2.4, -0.8, 0.25, 1.1, 2.5, 3.7])
    steps = steps.astype(np.float64)
    yy, xx = np.indices(shape)
    a, b = 2 * np.pi * yy / ny, 2 * np.pi * xx / nx
    if specimen is None:
        specimen = 3 + 0.35 * np.cos(b) + 0.2 * np.sin(a) + 0.17 * np.cos(a + b)
    carrier_angle = 2 * np.pi * (carrier[0] * yy / ny + carrier[1] * xx / nx)
    spatial_c = np.cos(carrier_angle) * np.cos(theta) - np.sin(carrier_angle) * np.sin(theta)
    spatial_s = np.sin(carrier_angle) * np.cos(theta) + np.cos(carrier_angle) * np.sin(theta)
    images = []
    for c, s in zip(np.cos(steps), np.sin(steps), strict=True):
        illuminated = brightness * specimen * (1 + modulation * (spatial_c * c - spatial_s * s))
        images.append(
            3 * illuminated / 8
            + np.roll(illuminated, 1, axis=0) / 8
            + np.roll(illuminated, 1, axis=1) / 2
        )
    data = np.array(images)
    if off_model:
        data += 0.16 * np.arange(1, len(steps) + 1)[:, None, None] * np.cos(a - 2 * b)[None]
    kernel = np.zeros(shape)
    kernel[0, 0] += 3 / 8
    kernel[1 % ny, 0] += 1 / 8
    kernel[0, 1 % nx] += 1 / 2
    transfer = finite_dft(kernel, normalized=False).astype(np.complex128)
    return Acquisition(data, steps, transfer, carrier, specimen, brightness, modulation, theta)


def grid(shape: tuple[int, int], spacing: tuple[float, float]) -> tuple[Array, Array]:
    return tuple(
        (modes(n).astype(np.longdouble) / n / np.longdouble(d)).astype(np.float64)
        for n, d in zip(shape, spacing, strict=True)
    )  # type: ignore[return-value]


def rotated_phases(steps: NDArray, theta: float) -> Array:
    c, s = np.cos(steps.astype(np.float64)), np.sin(steps.astype(np.float64))
    ct, st = np.cos(theta), np.sin(theta)
    return np.arctan2(s * ct + c * st, c * ct - s * st)


def circular_error(actual: NDArray | float, expected: NDArray | float) -> NDArray:
    difference = np.asarray(actual) - expected
    return np.arctan2(np.sin(difference), np.cos(difference))


def continuous_specimen(shape: tuple[int, int]) -> Array:
    """Sample the same analytic object on a doubled grid (same field)."""
    ny, nx = shape
    yy, xx = np.indices((2 * ny, 2 * nx))
    a, b = 2 * np.pi * yy / (2 * ny), 2 * np.pi * xx / (2 * nx)
    return 3 + 0.35 * np.cos(b) + 0.2 * np.sin(a) + 0.17 * np.cos(a + b)


# Child bootstrap is installed before loading this fixture or scientific imports.
# Parent captures every byte; only one validated JSON record may reach assertions.
FAULT_CHILD_BOOTSTRAP = r"""
import sys
sys.dont_write_bytecode = True
diagnostics = []
state = {"stage": "startup", "injections": [], "dormant_calls": 0}
def describe(error):
    locations = []
    tb = error.__traceback__
    while tb is not None:
        locations.append({"file": tb.tb_frame.f_code.co_filename, "line": tb.tb_lineno})
        tb = tb.tb_next
    code = getattr(error, "code", None)
    return {"type": type(error).__name__, "code": code if isinstance(code, str) else None,
            "message": str(error), "locations": locations}
def unraisable(event):
    diagnostics.append({"kind": "unraisable", **describe(event.exc_value)})
sys.unraisablehook = unraisable
sys.excepthook = lambda kind, error, tb: diagnostics.append(describe(error))
original_stdout = sys.stdout
try:
    import contextlib
    import gc
    import io
    import json
    import warnings
    def warning(message, category, filename, lineno, file=None, line=None):
        diagnostics.append({"kind": "warning", "type": category.__name__, "code": None,
                            "message": str(message),
                            "locations": [{"file": filename, "line": lineno}]})
    warnings.showwarning = warning
    warnings.simplefilter("error")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            state["stage"] = "fixture_import"
            sys.path.insert(0, sys.argv[1])
            from illumination_fixture import numerical_fault_child
            result = numerical_fault_child(sys.argv[2], sys.argv[3], sys.argv[4], state)
        except BaseException as error:
            result = {"status": "setup_exception", "exception": describe(error)}
        finally:
            gc.collect()
    result.update({"protocol": 1, "stage": state["stage"],
                   "injections": state["injections"],
                   "dormant_calls": state["dormant_calls"], "diagnostics": diagnostics,
                   "suppressed_stdout_chars": len(out.getvalue()),
                   "suppressed_stderr_chars": len(err.getvalue())})
    if diagnostics or out.getvalue() or err.getvalue():
        result["prior_status"] = result["status"]
        result["status"] = "diagnostic_failure"
    original_stdout.write("ILLUMINATION_FAULT_JSON " + json.dumps(result) + "\n")
    sys.exit(3 if result["status"] in ("setup_exception", "diagnostic_failure") else 0)
except SystemExit:
    raise
except BaseException:
    original_stdout.write('ILLUMINATION_FAULT_JSON {"protocol":1, "status":'
                          '"bootstrap_failure", "stage":"startup", "exception":'
                          '{"type":"BootstrapDiagnosticFailure", "code":null,'
                          '"message":"Structured startup diagnostics unavailable",'
                          '"locations":[]}, "injections":[]}\n')
    sys.exit(3)
"""


def exception_summary(error: BaseException) -> dict[str, Any]:
    """Record exception identity and locations, never traceback source or locals."""
    locations = []
    tb = error.__traceback__
    while tb is not None:
        locations.append({"file": tb.tb_frame.f_code.co_filename, "line": tb.tb_lineno})
        tb = tb.tb_next
    code = getattr(error, "code", None)
    return {
        "type": type(error).__name__,
        "code": code if isinstance(code, str) else None,
        "message": str(error),
        "locations": locations,
        "domain_message": getattr(error, "message", None),
    }


def numerical_fault_child(
    family: str, action: str, mode: str, state: dict[str, Any]
) -> dict[str, Any]:
    """Install dormant public wrappers before product import; arm only for call."""
    import sys

    import scipy.fft
    import scipy.fftpack
    import scipy.linalg

    if "simrecon" in sys.modules:
        return {"status": "preimport_defect", "message": "Public package imported before observer"}
    state["stage"] = "observer_install"
    armed = False
    owners = (
        [
            (np.fft, ("fft", "fft2", "fftn")),
            (scipy.fft, ("fft", "fft2", "fftn")),
            (scipy.fftpack, ("fft", "fft2", "fftn")),
        ]
        if family == "transform"
        else [(np.linalg, ("svd", "lstsq")), (scipy.linalg, ("svd", "lstsq"))]
    )
    for owner, names in owners:
        for name in names:
            original = getattr(owner, name)

            def boundary(
                *args: Any,
                _original: Any = original,
                _name: str = f"{owner.__name__}.{name}",
                **kwargs: Any,
            ) -> Any:
                if not armed:
                    state["dormant_calls"] += 1
                    return _original(*args, **kwargs)
                state["injections"].append({"boundary": _name, "action": action})
                if action == "nonfinite":
                    result = _original(*args, **kwargs)

                    def contaminate(value: Any) -> Any:
                        if isinstance(value, np.ndarray) and value.dtype.kind in "fc":
                            return np.full_like(value, np.nan)
                        return value

                    return (
                        tuple(contaminate(v) for v in result)
                        if isinstance(result, tuple)
                        else contaminate(result)
                    )
                errors: dict[str, type[Exception]] = {
                    "value": ValueError,
                    "floating": FloatingPointError,
                    "overflow": OverflowError,
                    "linalg": np.linalg.LinAlgError,
                    "memory": MemoryError,
                    "unrelated": RuntimeError,
                }
                raise errors[action]("controlled public numerical boundary failure")

            setattr(owner, name, boundary)
    if mode == "alias_probe":
        state["stage"] = "alias_import"
        if family == "transform":
            from numpy.fft import fft2 as alias
        else:
            from scipy.linalg import svd as alias
        data = np.ones((3, 3))
        # This public-library demo also proves preparation runs while dormant.
        alias(data)

        def call_alias() -> Any:
            return alias(data)

        function = call_alias
        snapshots: list[tuple[NDArray, NDArray]] = [(data, data.copy())]
        domain_error: Any = ()
    else:
        state["stage"] = "product_import"
        import simrecon

        state["stage"] = "preparation"
        fixture = acquisition()
        fy, fx = grid(fixture.transfer.shape, fixture.pixel_size)
        record = simrecon.Otf2D(
            values=fixture.transfer.copy(),
            fy_per_um=fy,
            fx_per_um=fx,
            pixel_size_um=fixture.pixel_size,
            origin_yx=fixture.origin,
            source=fixture.source,
        )
        operation = getattr(simrecon, "estimate_illumination", None)
        if operation is None:
            return {
                "status": "missing_export",
                "exception": {
                    "type": "MissingPublicExport",
                    "code": None,
                    "message": "Missing public simrecon export: estimate_illumination",
                    "locations": [],
                },
            }

        def call_product() -> Any:
            return operation(
                fixture.images,
                otf=record,
                phase_steps_rad=fixture.steps,
                carrier_bins_yx=fixture.carrier,
            )

        function = call_product
        snapshots = [
            (array, array.copy())
            for array in (
                fixture.images,
                fixture.steps,
                record.values,
                record.fy_per_um,
                record.fx_per_um,
            )
        ]
        domain_error = simrecon.SimreconError
    state["stage"] = "call"
    armed = True
    result: dict[str, Any]
    try:
        returned = function()
    except BaseException as error:
        result = {
            "status": "call_exception",
            "exception": exception_summary(error),
            "is_domain_error": isinstance(error, domain_error),
        }
    else:
        result = {
            "status": "call_returned",
            "exception": None,
            "is_domain_error": False,
            "returned_type": type(returned).__name__,
        }
        if mode == "alias_probe":
            result["returned_nonfinite"] = isinstance(returned, np.ndarray) and not bool(
                np.all(np.isfinite(returned))
            )
    finally:
        armed = False
    result["inputs_preserved"] = all(np.array_equal(a, b) for a, b in snapshots)
    if not state["injections"]:
        result["status"] = "harness_reachability_defect"
    return result


def fault_subprocess_report(family: str, action: str, *, mode: str = "product") -> dict[str, Any]:
    """Capture child output and accept only a single structured diagnostic record."""
    import json
    import subprocess
    import sys
    from pathlib import Path

    try:
        child = subprocess.run(
            [
                sys.executable,
                "-W",
                "error",
                "-c",
                FAULT_CHILD_BOOTSTRAP,
                str(Path(__file__).resolve().parent),
                family,
                action,
                mode,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "child_startup_failure",
            "injections": [],
            "returncode": None,
            "exception": {
                "type": "TimeoutExpired",
                "code": None,
                "message": "Protected numerical child exceeded 30 s wait",
                "locations": [],
            },
        }
    except OSError as error:
        return {
            "status": "child_startup_failure",
            "exception": exception_summary(error),
            "injections": [],
            "returncode": None,
        }
    prefix = "ILLUMINATION_FAULT_JSON "
    lines = child.stdout.splitlines()
    if len(lines) != 1 or not lines[0].startswith(prefix) or child.stderr:
        return {
            "status": "child_protocol_defect",
            "returncode": child.returncode,
            "exception": {
                "type": "ChildProtocolDefect",
                "code": None,
                "message": "Unrecognized child output withheld",
                "locations": [],
            },
            "injections": [],
            "stdout_chars": len(child.stdout),
            "stderr_chars": len(child.stderr),
        }
    try:
        report = json.loads(lines[0][len(prefix) :])
    except (ValueError, TypeError):
        return {
            "status": "child_protocol_defect",
            "returncode": child.returncode,
            "injections": [],
            "message": "Invalid child JSON withheld",
        }
    if not isinstance(report, dict) or report.get("protocol") != 1:
        return {
            "status": "child_protocol_defect",
            "returncode": child.returncode,
            "injections": [],
            "message": "Invalid child protocol withheld",
        }
    report["returncode"] = child.returncode
    return report
