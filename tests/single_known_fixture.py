"""Independent SP113 declarations and rational rounding, authored before trials.

No preparation result, candidate output or production numerical helper is an
oracle. The only product calls here are the documented public constructors.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, replace
from fractions import Fraction
from typing import Any

import numpy as np
from numpy.typing import NDArray

import simrecon as sr

PROFILE = "single-mixed-v1"
REVISION = "ce04-svn307-v1"
I32 = 2**31 - 1
NATIVE_MAX = 2**63 - 1
U32 = Fraction(1, 2**24)
U64 = Fraction(1, 2**53)
HALF_SUB32 = Fraction(1, 2**150)
ComplexQ = tuple[Fraction, Fraction]

BAND_FIELDS = (
    "quadratures", "noise_variance_factors", "input_shape", "input_scale",
    "dxy_um", "dz_um", "lateral_zoom", "axial_zoom", "mapping_revision",
    "precision_profile", "provenance",
)
RESULT_FIELDS = (
    "image", "filtered_quadratures", "x_um", "y_um", "z_um",
    "carriers_cyc_um", "modulation", "radial_cutoff_cyc_um",
    "axial_cutoffs_bins", "resolved_settings", "mode_trace", "source_revision",
    "reference_sha256", "precision_profile", "precision_provenance",
)
SETTING_KEYS = (
    "wavelength_nm", "numerical_aperture", "immersion_index", "wiener",
    "suppress_singularities", "suppression_radius_bins", "dampen_order0",
    "omit_order0", "omit_kz0", "output_taper", "dxy_um", "dz_um",
    "lateral_zoom", "axial_zoom", "input_scale",
)
PRECISION_VALUES = (
    ("requested_profile", PROFILE), ("resolved_profile", PROFILE),
    ("mapping_revision", REVISION), ("band_storage_dtype", "complex64"),
    ("noise_dtype", "float64"), ("parameter_dtypes", "float64/complex128"),
    ("transfer_source_dtype", "complex128"),
    ("transfer_query_dtype", "float64/int64"),
    ("transfer_interpolation_dtype", "complex128"),
    ("scalar_filter_dtypes", "float64/complex128"),
    ("consumed_scale_dtype", "complex64"), ("local_bulk_dtype", "complex64"),
    ("fft_input_dtype", "complex64"), ("fft_output_dtype", "complex64"),
    ("fft_interface", "scipy.fft.ifftn"), ("fft_axes", "0,1,2"),
    ("fft_norm", "forward"), ("fft_workers", "1"),
    ("fft_backend", None), ("fft_backend_version", None),
    ("scipy_version", None), ("numpy_version", None),
    ("fft_internal_precision", None), ("fft_workspace", None),
    ("phase_query_dtype", "float64"), ("consumed_phase_dtype", "complex64"),
    ("accumulation_dtype", "float64"), ("image_dtype", "float32"),
    ("transfer_rounding", "sample-c128;scalar-c128/f64;scale-once-c64"),
    ("input_identity_encoding", "sp113-framed-v1"),
    ("bands_sha256", None), ("transfer_sha256", None),
    ("parameters_sha256", None),
)
CE04_SOURCES = (
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    ("usr_local/include/fftw3.h", "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d"),
)


def arrays(
    *, t: int = 1, d: int = 1, o: int = 2, z: int = 2,
    y: int = 2, x: int = 4,
) -> tuple[NDArray[np.complex64], NDArray[np.float64]]:
    """Every slot is declared: unspecified coefficients are literal +0+0j."""
    q = np.zeros((t, d, 2 * o - 1, z, y, x // 2 + 1), dtype=np.complex64)
    v = np.ones((t, d, o), dtype=np.float64)
    return q, v


def declare(q: Any = None, v: Any = None, **changes: Any) -> Any:
    if q is None:
        q, default_v = arrays()
        if v is None:
            v = default_v
    assert v is not None
    # Malformed public array kinds/arity must reach the public constructor,
    # rather than failing in this fixture's convenience metadata extraction.
    shape = q.shape if isinstance(q, np.ndarray) and q.ndim == 6 else (1, 1, 3, 2, 2, 3)
    t, d, slots, z, y, half = shape
    options: dict[str, Any] = {
        "input_shape": (t, d, slots, z, y, 2 * (half - 1)),
        "dxy_um": 1.0, "dz_um": 1.0,
        "lateral_zoom": 1, "axial_zoom": 1,
        "provenance": (("formula", "explicit half-spectrum; CE alpha units"),),
    }
    options.update(changes)
    return sr.declare_prepared_bands32(q, v, **options)


def transfer(
    *, orders: int = 2, value: complex = 1 + 0j, layout: str = "radial",
    radial: int = 8, axial: int = 8, empirical_delta: float = 0.0,
) -> Any:
    shape = (orders, radial, axial) if layout == "radial" else (orders, axial, 8, radial)
    samples = np.full(shape, value, dtype=np.complex128)
    result = sr.declare_otf(samples, layout=layout, dkr_cyc_um=1.0, dkz_cyc_um=1.0)
    if empirical_delta:
        # Valid prepared-style c128 source storage; no c64 declaration rounding.
        original = np.array(result.samples, dtype=np.complex128, copy=True)
        original.real += empirical_delta
        original.flags.writeable = False
        result = replace(result, samples=original)
    return result


def call(bands: Any = None, otf: Any = None, **changes: Any) -> Any:
    if bands is None:
        bands = declare()
    if otf is None:
        otf = transfer(orders=bands.noise_variance_factors.shape[-1])
    directions = bands.input_shape[1]
    orders = bands.noise_variance_factors.shape[-1]
    options: dict[str, Any] = {
        "carriers_cyc_um": np.zeros((directions, 2), dtype=np.float64),
        "modulation": np.ones((directions, orders - 1), dtype=np.complex128),
        "wavelength_nm": 500, "numerical_aperture": 1.0,
        "immersion_index": 1.0, "wiener": 0.5,
        "suppress_singularities": False, "output_taper": "none",
        "precision": PROFILE,
    }
    options.update(changes)
    return sr.reconstruct_known(bands, otf, **options)


def owned(value: NDArray[Any]) -> NDArray[Any]:
    result = np.array(value, copy=True, order="C", subok=False)
    result.flags.writeable = False
    return result


def snapshot(*values: NDArray[Any]) -> tuple[bytes, ...]:
    return tuple(value.tobytes(order="C") for value in values)


def assert_owned(value: NDArray[Any], dtype: Any, shape: tuple[int, ...]) -> None:
    assert type(value) is np.ndarray
    assert value.dtype == np.dtype(dtype)
    assert value.dtype.isnative
    assert value.shape == shape
    assert value.flags.owndata and value.flags.c_contiguous
    assert not value.flags.writeable


def round_binary(value: Fraction, precision: int, emin: int) -> Fraction:
    """Exact IEEE nearest-even for finite in-range values; no float oracle.

    precision=24, emin=-126 gives binary32; precision=53, emin=-1022 gives
    binary64. Callers keep overflow cases out of this reference's domain.
    """
    if not value:
        return Fraction(0)
    sign = -1 if value < 0 else 1
    magnitude = abs(value)
    exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
    power = Fraction(2) ** exponent
    if magnitude < power:
        exponent -= 1
    spacing = Fraction(2) ** (max(exponent, emin) - precision + 1)
    units = magnitude / spacing
    quotient, remainder = divmod(units.numerator, units.denominator)
    twice = 2 * remainder
    if twice > units.denominator or (twice == units.denominator and quotient % 2):
        quotient += 1
    return sign * quotient * spacing


def rn32(value: Fraction) -> Fraction:
    return round_binary(value, 24, -126)


def rn64(value: Fraction) -> Fraction:
    return round_binary(value, 53, -1022)


def cq(value: complex | int | Fraction) -> ComplexQ:
    if isinstance(value, Fraction | int):
        return Fraction(value), Fraction(0)
    return Fraction(value.real), Fraction(value.imag)


def add(a: ComplexQ, b: ComplexQ, *, bits: int = 24) -> ComplexQ:
    rounding = rn32 if bits == 24 else rn64
    return rounding(a[0] + b[0]), rounding(a[1] + b[1])


def conjugate(a: ComplexQ) -> ComplexQ:
    return a[0], -a[1]


def rotate(a: ComplexQ) -> ComplexQ:
    return -a[1], a[0]


def multiply(a: ComplexQ, b: ComplexQ, *, bits: int = 24) -> ComplexQ:
    rounding = rn32 if bits == 24 else rn64
    return (
        rounding(rounding(a[0] * b[0]) - rounding(a[1] * b[1])),
        rounding(rounding(a[0] * b[1]) + rounding(a[1] * b[0])),
    )


def to_complex(value: ComplexQ) -> complex:
    return complex(float(value[0]), float(value[1]))


def recombine(p: ComplexQ, n: ComplexQ) -> tuple[ComplexQ, ComplexQ]:
    total = add(p, n)
    difference = add(p, (-n[0], -n[1]))
    even = rn32(total[0] / 2), rn32(total[1] / 2)
    odd = rn32(difference[1] / 2), rn32(-difference[0] / 2)
    return even, odd


def unit_scale(noise: tuple[Fraction, ...], order: int, *, boundary: bool = False) -> Fraction:
    """H=a=1, w=1/2, k0=0: three signed powers for O2.

    Interior denominator has zero order once and every side order twice;
    at r=R strict other support excludes every other term.
    """
    g = tuple(rn64(1 / v) for v in noise)
    denominator = g[order]
    if not boundary:
        for signed in range(-(len(noise) - 1), len(noise)):
            if signed != order:
                denominator = rn64(denominator + g[abs(signed)])
    denominator = rn64(denominator + Fraction(1, 4))
    return rn32(rn64(g[order] / denominator))


def framed_identity(domain: str, metadata: Any, entries: list[tuple[str, NDArray[Any], str]]) -> str:
    """Independent public framed-v1 serializer; these fixtures are tiny."""
    digest = hashlib.sha256()

    def frame(payload: bytes) -> None:
        digest.update(len(payload).to_bytes(8, "little"))
        digest.update(payload)

    def canonical(value: Any) -> bytes:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")

    frame(("sp113-framed-v1/" + domain).encode("ascii"))
    frame(canonical(metadata))
    for name, array, dtype in entries:
        frame(canonical([name, dtype, list(array.shape)]))
        frame(array.astype(np.dtype(dtype), copy=False).tobytes(order="C"))
    return digest.hexdigest()


def identities(bands: Any, otf: Any, result: Any) -> dict[str, str]:
    band_metadata = {
        field.name: getattr(bands, field.name)
        for field in fields(bands)
        if field.name not in ("quadratures", "noise_variance_factors")
    }
    transfer_metadata = {
        name: getattr(otf, name)
        for name in ("layout", "dkr_cyc_um", "dkz_cyc_um", "norders", "source_revision", "reference_sha256")
    }
    return {
        "bands_sha256": framed_identity("bands", band_metadata, [
            ("quadratures", bands.quadratures, "<c8"),
            ("noise_variance_factors", bands.noise_variance_factors, "<f8"),
        ]),
        "transfer_sha256": framed_identity("transfer", transfer_metadata, [
            ("samples", otf.samples, "<c16"),
        ]),
        "parameters_sha256": framed_identity("parameters", {
            "resolved_settings": result.resolved_settings, "precision": PROFILE,
        }, [
            ("carriers_cyc_um", result.carriers_cyc_um, "<f8"),
            ("modulation", result.modulation, "<c16"),
        ]),
    }
