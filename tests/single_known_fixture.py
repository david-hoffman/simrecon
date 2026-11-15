"""Independent SP113 declarations and rational rounding, authored before trials.

No preparation result, candidate output or production numerical helper is an
oracle. The only product calls here are the documented public constructors.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass, replace
from fractions import Fraction
from math import isqrt
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
IntervalQ = tuple[Fraction, Fraction]
PI64 = Fraction(884279719003555, 281474976710656)

BAND_FIELDS = (
    "quadratures",
    "noise_variance_factors",
    "input_shape",
    "input_scale",
    "dxy_um",
    "dz_um",
    "lateral_zoom",
    "axial_zoom",
    "mapping_revision",
    "precision_profile",
    "provenance",
)
RESULT_FIELDS = (
    "image",
    "filtered_quadratures",
    "x_um",
    "y_um",
    "z_um",
    "carriers_cyc_um",
    "modulation",
    "radial_cutoff_cyc_um",
    "axial_cutoffs_bins",
    "resolved_settings",
    "mode_trace",
    "source_revision",
    "reference_sha256",
    "precision_profile",
    "precision_provenance",
)
SETTING_KEYS = (
    "wavelength_nm",
    "numerical_aperture",
    "immersion_index",
    "wiener",
    "suppress_singularities",
    "suppression_radius_bins",
    "dampen_order0",
    "omit_order0",
    "omit_kz0",
    "output_taper",
    "dxy_um",
    "dz_um",
    "lateral_zoom",
    "axial_zoom",
    "input_scale",
)
PRECISION_VALUES = (
    ("requested_profile", PROFILE),
    ("resolved_profile", PROFILE),
    ("mapping_revision", REVISION),
    ("band_storage_dtype", "complex64"),
    ("noise_dtype", "float64"),
    ("parameter_dtypes", "float64/complex128"),
    ("transfer_source_dtype", "complex128"),
    ("transfer_query_dtype", "float64/int64"),
    ("transfer_interpolation_dtype", "complex128"),
    ("scalar_filter_dtypes", "float64/complex128"),
    ("consumed_scale_dtype", "complex64"),
    ("local_bulk_dtype", "complex64"),
    ("fft_input_dtype", "complex64"),
    ("fft_output_dtype", "complex64"),
    ("fft_interface", "scipy.fft.ifftn"),
    ("fft_axes", "0,1,2"),
    ("fft_norm", "forward"),
    ("fft_workers", "1"),
    ("fft_backend", None),
    ("fft_backend_version", None),
    ("scipy_version", None),
    ("numpy_version", None),
    ("fft_internal_precision", None),
    ("fft_workspace", None),
    ("phase_query_dtype", "float64"),
    ("consumed_phase_dtype", "complex64"),
    ("accumulation_dtype", "float64"),
    ("image_dtype", "float32"),
    ("transfer_rounding", "sample-c128;scalar-c128/f64;scale-once-c64"),
    ("input_identity_encoding", "sp113-framed-v1"),
    ("bands_sha256", None),
    ("transfer_sha256", None),
    ("parameters_sha256", None),
)
CE04_SOURCES = (
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)


def arrays(
    *,
    t: int = 1,
    d: int = 1,
    o: int = 2,
    z: int = 2,
    y: int = 2,
    x: int = 4,
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
        "dxy_um": 1.0,
        "dz_um": 1.0,
        "lateral_zoom": 1,
        "axial_zoom": 1,
        "provenance": (("formula", "explicit half-spectrum; CE alpha units"),),
    }
    options.update(changes)
    constructor = sr.declare_prepared_bands32
    return constructor(q, v, **options)


def transfer(
    *,
    orders: int = 2,
    value: complex = 1 + 0j,
    layout: str = "radial",
    radial: int = 8,
    axial: int = 8,
    empirical_delta: float = 0.0,
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
        "wavelength_nm": 500,
        "numerical_aperture": 1.0,
        "immersion_index": 1.0,
        "wiener": 0.5,
        "suppress_singularities": False,
        "output_taper": "none",
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


def framed_identity(
    domain: str, metadata: Any, entries: list[tuple[str, NDArray[Any], str]]
) -> str:
    """Independent public framed-v1 serializer; these fixtures are tiny."""
    digest = hashlib.sha256()

    def frame(payload: bytes) -> None:
        digest.update(len(payload).to_bytes(8, "little"))
        digest.update(payload)

    def canonical(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
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
        for name in (
            "layout",
            "dkr_cyc_um",
            "dkz_cyc_um",
            "norders",
            "source_revision",
            "reference_sha256",
        )
    }
    return {
        "bands_sha256": framed_identity(
            "bands",
            band_metadata,
            [
                ("quadratures", bands.quadratures, "<c8"),
                ("noise_variance_factors", bands.noise_variance_factors, "<f8"),
            ],
        ),
        "transfer_sha256": framed_identity(
            "transfer",
            transfer_metadata,
            [
                ("samples", otf.samples, "<c16"),
            ],
        ),
        "parameters_sha256": framed_identity(
            "parameters",
            {
                "resolved_settings": result.resolved_settings,
                "precision": PROFILE,
            },
            [
                ("carriers_cyc_um", result.carriers_cyc_um, "<f8"),
                ("modulation", result.modulation, "<c16"),
            ],
        ),
    }


def legacy_raw(*, two_dimensional: bool = False) -> NDArray[np.float32]:
    """Compatibility only: literal CE07 recipe, never single scientific data."""
    raw = np.empty((1, 1, 3, 1 if two_dimensional else 2, 2, 4), dtype=np.float32)
    for phase, amplitude in enumerate((6, 3, 3)):
        raw[:, :, phase] = amplitude
    return raw


def legacy_acquisition(raw: NDArray[np.float32], *, two_dimensional: bool = False) -> Any:
    return sr.prepare_acquisition_bands(
        raw,
        acquisition_mode="2d" if two_dimensional else "3d",
        dxy_um=1.0,
        dz_um=0.0 if two_dimensional else 1.0,
        norders=2,
        background=0.0,
        lateral_zoom=1,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )


def legacy_transfer(*, two_dimensional: bool = False) -> Any:
    samples = np.ones((2, 8, 1 if two_dimensional else 2), dtype=np.complex128)
    return sr.declare_otf(samples, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.5)


def legacy_known_options() -> dict[str, Any]:
    return {
        "carriers_cyc_um": np.zeros((1, 2), dtype=np.float64),
        "modulation": np.ones((1, 1), dtype=np.complex128),
        "wavelength_nm": 500,
        "numerical_aperture": 1.0,
        "immersion_index": 1.0,
        "wiener": 1.0,
        "suppress_singularities": False,
        "output_taper": "none",
    }


def legacy_workflow_options(otf: Any) -> dict[str, Any]:
    optics = {"wavelength_nm": 500, "numerical_aperture": 1.0, "immersion_index": 1.0}
    return {
        "acquisition": {
            "acquisition_mode": "3d",
            "dxy_um": 1.0,
            "dz_um": 1.0,
            "norders": 2,
            "background": 0.0,
            "lateral_zoom": 1,
            "axial_zoom": 1,
            "phase_policy": "uniform",
            "edge_pixels": 0,
            "equalize": False,
        },
        "optics": optics,
        "carrier": {"linespacing_um": 8.0, "phase_start_angle_rad": 0.0, "search_carriers": False},
        "filtering": {"wiener": 1.0, "suppress_singularities": False, "output_taper": "none"},
        "specimen_identity": {"id": "sp113-legacy-control", "intensity_unit": "camera counts"},
        "transfer": otf,
        "transfer_identity": {
            "id": "sp113-unit-transfer",
            "intensity_unit": "dimensionless-transfer",
            "optics": optics.copy(),
        },
    }


def assert_public_equal(left: Any, right: Any) -> None:
    """Exact compatibility comparison of public values, not a numerical oracle."""
    assert type(left) is type(right)
    if isinstance(left, np.ndarray):
        assert left.dtype == right.dtype and left.shape == right.shape
        assert left.tobytes(order="C") == right.tobytes(order="C")
    elif is_dataclass(left) and not isinstance(left, type):
        assert tuple(field.name for field in fields(left)) == tuple(
            field.name for field in fields(right)
        )
        for field in fields(left):
            assert_public_equal(getattr(left, field.name), getattr(right, field.name))
    elif isinstance(left, tuple | list):
        assert len(left) == len(right)
        for item, other in zip(left, right, strict=True):
            assert_public_equal(item, other)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key, item in left.items():
            assert_public_equal(item, right[key])
    else:
        assert left == right


def public_values(value: Any) -> list[Any]:
    """Visit public dataclass/container payloads for retention checks only."""
    result = [value]
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            result.extend(public_values(getattr(value, field.name)))
    elif isinstance(value, tuple | list):
        for item in value:
            result.extend(public_values(item))
    elif isinstance(value, dict):
        for item in value.values():
            result.extend(public_values(item))
    return result


def sqrt_small_interval(value: Fraction) -> IntervalQ:
    """Outward2^-160 integer-root enclosure for these small witness values."""
    assert 0 <= value <= 4
    numerator = value.numerator << 320
    root = isqrt(numerator // value.denominator)
    lower = Fraction(root, 2**160)
    if lower * lower == value:
        return lower, lower
    return lower, Fraction(root + 1, 2**160)


def rounded_interval(value: IntervalQ, *, bits: int = 53) -> IntervalQ:
    rounding = rn64 if bits == 53 else rn32
    return rounding(value[0]), rounding(value[1])


def rounding_margin32(value: IntervalQ, represented: Fraction) -> Fraction:
    """Exact distance to a binary32 rounding-cell edge for these finite points."""
    if not represented:
        lower, upper = -HALF_SUB32, HALF_SUB32
    else:
        magnitude = abs(represented)
        assert Fraction(1, 2**126) <= magnitude < 2**128
        exponent = magnitude.numerator.bit_length() - magnitude.denominator.bit_length()
        if magnitude < Fraction(2) ** exponent:
            exponent -= 1
        spacing = Fraction(2) ** (exponent - 23)
        below = spacing / 2 if magnitude == Fraction(2) ** exponent else spacing
        if represented > 0:
            lower, upper = represented - below / 2, represented + spacing / 2
        else:
            lower, upper = represented - spacing / 2, represented + below / 2
    margin = min(value[0] - lower, upper - value[1])
    assert margin > 0, "independent interval touches a rounding-cell edge"
    return margin


def interval_product64(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    endpoints = [x * y for x in a for y in b]
    return rounded_interval((min(endpoints), max(endpoints)))


def interval_sum64(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    return rounded_interval((a[0] + b[0], a[1] + b[1]))


def interval_quotient64(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    assert b[0] > 0
    endpoints = [x / y for x in a for y in b]
    return rounded_interval((min(endpoints), max(endpoints)))


def cos_point_reference(multiplier: Fraction) -> IntervalQ:
    """Only cos(0), cos(PI64/4), cos(PI64/2); certified analytic tail.

    This encloses the exact mathematical cosine at the exact binary64 query.
    It does not certify an actual libm's returned binary64 primitive.
    """
    assert multiplier in (Fraction(0), Fraction(1, 4), Fraction(1, 2))
    argument = PI64 * multiplier
    total = term = Fraction(1)
    for n in range(1, 33):
        term *= -(argument * argument) / ((2 * n - 1) * (2 * n))
        total += term
    # Terms from n>=1 decrease since argument²<5 and successive divisors>=12.
    # n32 is positive; the next term is negative and bounds the entire tail.
    next_term = -term * argument * argument / (65 * 66)
    return total + next_term, total


def binary64_rational(bits: int) -> Fraction:
    """Decode the public method's literal IEEE bits, never a runtime result."""
    sign = -1 if bits >> 63 else 1
    exponent = (bits >> 52) & 0x7FF
    fraction = bits & (2**52 - 1)
    assert exponent < 0x7FF
    if exponent == 0:
        return sign * fraction * Fraction(2) ** -1074
    return sign * (2**52 + fraction) * Fraction(2) ** (exponent - 1075)


def box64(value: IntervalQ) -> IntervalQ:
    """R64 hull covers separate rounding and omitted FMA-node rounding."""
    rounded = rounded_interval(value)
    return min(value[0], rounded[0]), max(value[1], rounded[1])


def box_add(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    return box64((a[0] + b[0], a[1] + b[1]))


def box_subtract(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    return box64((a[0] - b[1], a[1] - b[0]))


def box_multiply(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    corners = [x * y for x in a for y in b]
    return box64((min(corners), max(corners)))


def box_divide(a: IntervalQ, b: IntervalQ) -> IntervalQ:
    assert b[0] > 0
    corners = [x / y for x in a for y in b]
    return box64((min(corners), max(corners)))


def box_sqrt_small(value: IntervalQ) -> IntervalQ:
    assert value[0] > 0
    lower, upper = sqrt_small_interval(value[0])[0], sqrt_small_interval(value[1])[1]
    return box64((lower, upper))


def hypot_transfer_program(delta: Fraction) -> IntervalQ:
    """Enclose the selected moderate glibc program union for the frozen H point.

    delta0 is only the independently specified early-table-rounding alternative;
    actual test sources use delta2^-30. Source/binary/sqrt/RNE remains a G3 hold.
    """
    assert delta in (Fraction(0), Fraction(1, 2**30))
    a, b = 1 + delta, Fraction(1, 2)
    aa, bb = (a, a), (b, b)
    twice_b = box_add(bb, bb)
    difference = box_subtract(aa, bb)
    if delta:
        assert twice_b[1] < a
        fused = box_sqrt_small(box_add(box_multiply(aa, aa), box_multiply(bb, bb)))
    else:
        # Exact equality selects the other moderate expression, not an epsilon.
        assert twice_b == aa
        fused = box_sqrt_small(
            box_add(box_multiply(twice_b, aa), box_multiply(difference, difference))
        )
    h0 = box_sqrt_small(box_add(box_multiply(aa, aa), box_multiply(bb, bb)))
    assert h0[0] > 2 * b
    residual = box_subtract(h0, aa)
    a_minus_2b = box_subtract(aa, twice_b)
    t1 = box_multiply(box_multiply((Fraction(2), Fraction(2)), residual), a_minus_2b)
    t2 = box_add(
        box_multiply(box_subtract(box_multiply((Fraction(4), Fraction(4)), residual), bb), bb),
        box_multiply(residual, residual),
    )
    correction = box_divide(box_add(t1, t2), box_multiply((Fraction(2), Fraction(2)), h0))
    nonfused = box_subtract(h0, correction)
    program = min(fused[0], nonfused[0]), max(fused[1], nonfused[1])
    reference = sqrt_small_interval(a * a + b * b)
    # A loose auxiliary certificate derived from these source boxes, not an
    # actual primitive's guessed error promise and not a candidate trial.
    assert max(abs(program[0] - reference[1]), abs(program[1] - reference[0])) < Fraction(1, 2**40)
    return program


def empirical_quotients_from_program(
    delta: Fraction, modulation_real: Fraction
) -> tuple[IntervalQ, IntervalQ]:
    """Strict RN64 center scales before the one consumed RN32 conversion."""
    h = hypot_transfer_program(delta)
    power = interval_product64(h, h)
    a2 = rn64(modulation_real * modulation_real)
    side_power = interval_product64(power, (a2, a2))
    denominator = interval_sum64(interval_sum64(power, side_power), side_power)
    denominator = interval_sum64(denominator, (Fraction(1, 4), Fraction(1, 4)))
    return (
        interval_quotient64((1 + delta, 1 + delta), denominator),
        interval_quotient64((Fraction(-1, 2), Fraction(-1, 2)), denominator),
    )


def empirical_scale_from_program(
    delta: Fraction, modulation_real: Fraction = Fraction(1)
) -> ComplexQ:
    """Center consumed scale; local strict RN64 order follows the contract."""
    result: list[Fraction] = []
    for quotient in empirical_quotients_from_program(delta, modulation_real):
        consumed = rounded_interval(quotient, bits=24)
        assert consumed[0] == consumed[1], "source-program consumed-scale interval is unresolved"
        rounding_margin32(quotient, consumed[0])
        result.append(consumed[0])
    return result[0], result[1]


def sin_point_reference(multiplier: Fraction) -> IntervalQ:
    assert multiplier in (
        Fraction(-1, 2),
        Fraction(-1, 4),
        Fraction(0),
        Fraction(1, 4),
        Fraction(1, 2),
    )
    argument = PI64 * abs(multiplier)
    total = term = argument
    for n in range(1, 33):
        term *= -(argument * argument) / ((2 * n) * (2 * n + 1))
        total += term
    next_term = -term * argument * argument / (66 * 67)
    positive = total + next_term, total
    return (-positive[1], -positive[0]) if multiplier < 0 else positive


def sincos_point_program(multiplier: Fraction) -> tuple[IntervalQ, IntervalQ]:
    """Enclose selected glibc0/P4/P2 programs without a generic trig/ULP hypothesis."""
    assert multiplier in (
        Fraction(-1, 2),
        Fraction(-1, 4),
        Fraction(0),
        Fraction(1, 4),
        Fraction(1, 2),
    )
    if not multiplier:
        return (Fraction(1), Fraction(1)), (Fraction(0), Fraction(0))
    if abs(multiplier) == Fraction(1, 2):
        hp1 = binary64_rational(0x3C91A62633145C07)
        assert Fraction(1, 2**54) < hp1 < Fraction(1, 2**53)
        big = Fraction(3 * 2**44)
        assert hp1 < Fraction(1, 2**8) and rn64(big + hp1) == big
        # Cosine/sincos reduce to y0,a=hp1,da0. Standalone sine instead
        # calls do_cos(0,hp1); combined sine calls do_cos(hp1,0). Both
        # do_cos arguments select knot0 and reduced r=hp1 exactly. Their
        # source sequences differ, while this selected polynomial agrees.
        # Tiny corrections are below the lower half-spacings of hp1 and1.
        assert hp1**3 < Fraction(1, 2**107)
        assert hp1**2 < Fraction(1, 2**54)
        sine = Fraction(-1) if multiplier < 0 else Fraction(1)
        return (hp1, hp1), (sine, sine)
    x = PI64 / 4
    big, knot = Fraction(3 * 2**44), Fraction(101, 128)
    assert Fraction(201, 256) < x < Fraction(203, 256)
    assert rn64(big + x) - big == knot
    t = x - knot
    assert Fraction(-1, 256) < t < Fraction(1, 256)
    assert rn64(t) == t
    tt = (t, t)
    sn = binary64_rational(0x3FE6B5CE50B7821A)
    ssn = binary64_rational(0xBC65D5158F702E0F)
    cs = binary64_rational(0x3FE68B5A92EB6253)
    ccs = binary64_rational(0xBC89A91AD985F89C)
    decimals = (
        "-1.66666666666664880952546298448555e-1",
        "8.33333214285722277379541354343671e-3",
        "4.99999999999999999999950396842453e-1",
        "-4.16666666666664434524222570944589e-2",
        "1.38888874007937613028114285595617e-3",
    )
    sn3, sn5, cs2, cs4, cs6 = (box64((Fraction(value), Fraction(value))) for value in decimals)
    xx = box_multiply(tt, tt)
    sine_polynomial = box_add(
        tt, box_multiply(box_multiply(tt, xx), box_add(sn3, box_multiply(xx, sn5)))
    )
    cosine_correction = box_multiply(
        xx, box_add(cs2, box_multiply(xx, box_add(cs4, box_multiply(xx, cs6))))
    )
    cosine_inner = box_subtract(
        box_subtract((ccs, ccs), box_multiply(sine_polynomial, (ssn, ssn))),
        box_multiply((cs, cs), cosine_correction),
    )
    cosine = box_add((cs, cs), box_subtract(cosine_inner, box_multiply((sn, sn), sine_polynomial)))
    sine_inner = box_subtract(
        box_add((ssn, ssn), box_multiply(sine_polynomial, (ccs, ccs))),
        box_multiply((sn, sn), cosine_correction),
    )
    sine = box_add((sn, sn), box_add(sine_inner, box_multiply((cs, cs), sine_polynomial)))
    return cosine, (-sine[1], -sine[0]) if multiplier < 0 else sine


def cosine_scale_from_program(base: ComplexQ, multiplier: Fraction) -> ComplexQ:
    cosine, _ = sincos_point_program(multiplier)
    result: list[Fraction] = []
    for component in base:
        scalar = interval_product64((component, component), cosine)
        consumed = rounded_interval(scalar, bits=24)
        assert consumed[0] == consumed[1], "source-program cosine scale interval is unresolved"
        rounding_margin32(scalar, consumed[0])
        result.append(consumed[0])
    return result[0], result[1]


def pi_machin_interval() -> IntervalQ:
    """Independent rational pi enclosure; no decimal/library pi oracle."""

    def arctan(unit: int) -> IntervalQ:
        argument = Fraction(1, unit)
        total = sum(
            ((-1) ** n * argument ** (2 * n + 1) / (2 * n + 1) for n in range(65)), Fraction(0)
        )
        next_term = -(argument**131) / 131
        return total + next_term, total

    fifth, other = arctan(5), arctan(239)
    return 16 * fifth[0] - 4 * other[1], 16 * fifth[1] - 4 * other[0]


def quarter_dft_reference(
    shape: tuple[int, int, int],
    entries: dict[tuple[int, int, int], ComplexQ],
) -> dict[tuple[int, int, int], ComplexQ]:
    """Sparse exact positive DFT, no candidate values or rounded oracle output."""
    assert all(n in (1, 2, 4) for n in shape)
    roots: tuple[ComplexQ, ...] = (
        (Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(1)),
        (Fraction(-1), Fraction(0)),
        (Fraction(0), Fraction(-1)),
    )
    result: dict[tuple[int, int, int], ComplexQ] = {}
    for h in range(shape[0]):
        for y in range(shape[1]):
            for x in range(shape[2]):
                real = imaginary = Fraction(0)
                for (kz, ky, kx), value in entries.items():
                    quarter = 4 * (
                        Fraction(kz * h, shape[0])
                        + Fraction(ky * y, shape[1])
                        + Fraction(kx * x, shape[2])
                    )
                    assert quarter.denominator == 1
                    root = roots[quarter.numerator % 4]
                    real += value[0] * root[0] - value[1] * root[1]
                    imaginary += value[0] * root[1] + value[1] * root[0]
                result[h, y, x] = real, imaginary
    return result


def cardinal_fft_envelope(shape: tuple[int, int, int], sbar: Fraction) -> Fraction:
    """Conditional source-based d-level method, never a universal multiplier."""
    assert all(n in (1, 2, 4) for n in shape) and sbar > 0
    levels = sum(n.bit_length() - 1 for n in shape)
    count = shape[0] * shape[1] * shape[2]
    denominator = 1 - levels * U32
    assert denominator > 0 and sbar < 64
    return (levels * U32 * sbar + (count - 1) * HALF_SUB32) / denominator


def bounded_declaration_child(case: str) -> None:
    """Linux-only experiment guard; never a product allocation/domain ceiling."""
    import os
    import resource
    from pathlib import Path

    import scipy.fft as fft

    if not __debug__:
        raise RuntimeError("bounded declaration experiment requires active assertions")
    assert callable(fft.ifftn)  # Ordinary FFT dependency is loaded before VmSize.

    page = int(os.sysconf("SC_PAGE_SIZE"))
    assert page > 0

    def vm_bytes() -> int:
        status = Path("/proc/self/status").read_text(encoding="ascii")
        lines = [line.split() for line in status.splitlines() if line.startswith("VmSize:")]
        if len(lines) != 1 or len(lines[0]) != 3 or lines[0][2] != "kB":
            raise RuntimeError(
                "bounded declaration experiment: unavailable Linux VmSize/KiB metadata"
            )
        result = int(lines[0][1]) * 1024
        if result <= 0:
            raise RuntimeError("bounded declaration experiment: invalid VmSize metadata")
        return result

    baseline = vm_bytes()
    reserve, minimum, ceiling = 64 * 1024**2, 32 * 1024**2, 1024**3
    rounded_baseline = ((baseline + page - 1) // page) * page
    rounded_reserve = ((reserve + page - 1) // page) * page
    minimum = ((minimum + page - 1) // page) * page
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    candidates = [rounded_baseline + rounded_reserve, ceiling]
    if soft != resource.RLIM_INFINITY:
        candidates.append(soft)
    if hard != resource.RLIM_INFINITY:
        candidates.append(hard)
    cap = min(candidates) // page * page
    if baseline <= 0 or cap - rounded_baseline < minimum:
        raise RuntimeError(
            "bounded declaration experiment: unusable existing address-space limit/baseline"
        )
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
    if resource.getrlimit(resource.RLIMIT_AS) != (cap, cap):
        raise RuntimeError("bounded declaration experiment: RLIMIT_AS installation failed")
    guarded_vm = vm_bytes()
    if cap - guarded_vm < minimum:
        raise RuntimeError(
            "bounded declaration experiment: post-limit address-space headroom unusable"
        )
    if case not in ("wide", "phase"):
        raise RuntimeError("unknown bounded declaration case")
    # Both the tiny positive and hazardous declarations start after the cap.
    q, v = arrays(y=1, x=2)
    ordinary = call(declare(q, v), modulation=np.zeros((1, 1)))
    assert ordinary.image.shape == (1, 2, 1, 2) and np.all(ordinary.image == 0)
    if case == "wide":
        bands = declare(q, v, lateral_zoom=2**14)
        assert bands.input_shape == (1, 1, 3, 2, 1, 2)
        assert bands.lateral_zoom == 2**14 and bands.axial_zoom == 1
        output_shape = (
            bands.input_shape[3] * bands.axial_zoom,
            bands.input_shape[4] * bands.lateral_zoom,
            bands.input_shape[5] * bands.lateral_zoom,
        )
        assert output_shape == (2, 16384, 32768)
        plane = output_shape[1] * output_shape[2]
        volume = output_shape[0] * plane
        assert plane == 2**29 and volume == 2**30
        assert 8 * volume == 2**33 and 4 * volume == 2**32 and 4 * plane == 2**31
        assert bands.input_scale == 2**-30
        expected_terms = ("wiener",)
        expected_error = "reconstruction-domain/wiener"
        assertion_names = (
            "tiny-positive;wide-geometry;wiener-domain;no-memory-cause;inputs-unchanged"
        )
    else:
        q, v = arrays(z=4)
        phases = I32 // 3
        assert 3 * phases == I32 - 1 and phases * 4 > I32
        bands = declare(q, v, input_shape=(1, 1, phases, 4, 2, 4))
        assert bands.input_shape[2] == phases and bands.input_scale == 1 / 32
        assert np.all(call(bands).image == 0)
        expected_terms = ("input_shape", "phase", "quadrature", "q*p", "representation", "count")
        expected_error = "reconstruction-domain/Q*P"
        assertion_names = (
            "tiny-positive;phase-count-positive;no-preparation-frame-cap;"
            "QP-rejection;no-memory-cause;inputs-unchanged"
        )
    before = snapshot(q, v, bands.quadratures, bands.noise_variance_factors)
    try:
        if case == "wide":
            call(bands, wiener=0.0)
        else:
            declare(q, v, input_shape=(1, 1, I32 // 3 + 1, 4, 2, 4))
    except sr.ReconstructionError as error:
        assert error.code == "reconstruction-domain"
        assert any(term in str(error).lower() for term in expected_terms)
        pending: list[BaseException] = [error]
        visited: set[int] = set()
        while pending:
            cause = pending.pop()
            if id(cause) in visited:
                continue
            visited.add(id(cause))
            assert not isinstance(cause, MemoryError), (
                "allocation failure is not the expected declaration rejection"
            )
            if cause.__cause__ is not None:
                pending.append(cause.__cause__)
            if cause.__context__ is not None:
                pending.append(cause.__context__)
    else:
        raise AssertionError("bounded declaration experiment: required rejection was absent")
    assert snapshot(q, v, bands.quadratures, bands.noise_variance_factors) == before
    print(
        "\nSP113_DECLARATION_RESULT "
        + json.dumps(
            {
                "case": case,
                "status": "passed",
                "baseline_vm_bytes": baseline,
                "cap_bytes": cap,
                "reserve_bytes": rounded_reserve,
                "guard_vm_bytes": guarded_vm,
                "minimum_reserve_bytes": minimum,
                "page_bytes": page,
                "ceiling_bytes": ceiling,
                "previous_soft_bytes": "unlimited" if soft == resource.RLIM_INFINITY else soft,
                "previous_hard_bytes": "unlimited" if hard == resource.RLIM_INFINITY else hard,
                "expected_error": expected_error,
                "assertions": assertion_names,
            },
            sort_keys=True,
        )
    )


def run_bounded_declaration_experiment(case: str) -> tuple[dict[str, Any], str]:
    """One named child, capped output/deadline and owned process-group cleanup.

    The source-free wrapper and inherited descendants' diagnostic/process-group
    behavior require explicit root qualification before this protocol executes.
    """
    import os
    import selectors
    import signal
    import subprocess
    import sys
    import time
    from contextlib import suppress
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if case not in ("wide", "phase"):
        raise RuntimeError("unknown bounded declaration case")
    command = [
        sys.executable,
        str(root / "scripts/source_free_check.py"),
        "python",
        str(Path(__file__).resolve()),
        "bounded-declarations",
        case,
    ]
    budget, timeout = 16 * 1024, 30.0
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    if not __debug__:
        raise RuntimeError("bounded declaration experiment requires active assertions")
    process = subprocess.Popen(
        command,
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    status: int | None = None
    stopped = False

    def stop() -> None:
        nonlocal stopped
        if stopped:
            return
        stopped = True
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)

    selector = selectors.DefaultSelector()
    try:
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stop()
                raise AssertionError(
                    "bounded declaration experiment timed out; no product assertion accepted"
                )
            for key, _ in selector.select(min(remaining, 0.2)):
                chunk = os.read(key.fd, 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                channel = str(key.data)
                if len(buffers[channel]) + len(chunk) > budget:
                    stop()
                    raise AssertionError(
                        "bounded declaration experiment diagnostic budget exceeded; "
                        "no assertion accepted"
                    )
                buffers[channel].extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            stop()
            raise AssertionError("bounded declaration experiment exit timed out")
        try:
            status = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            stop()
            raise AssertionError("bounded declaration experiment exit timed out") from None
    finally:
        selector.close()
        try:
            if process.poll() is None:
                stop()
        finally:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
    stdout = bytes(buffers["stdout"]).decode("utf-8")
    stderr = bytes(buffers["stderr"]).decode("utf-8")
    assert status == 0, f"bounded wide child status={status}: {stdout}{stderr}"
    lines = stdout.splitlines()
    frames = [line for line in lines if line.startswith("SP113_DECLARATION_RESULT ")]
    assert len(frames) == 1 and [line for line in lines if line][-1] == frames[0]
    report: dict[str, Any] = json.loads(frames[0].removeprefix("SP113_DECLARATION_RESULT "))
    assert type(report) is dict
    assert set(report) == {
        "case",
        "status",
        "baseline_vm_bytes",
        "guard_vm_bytes",
        "cap_bytes",
        "reserve_bytes",
        "minimum_reserve_bytes",
        "page_bytes",
        "ceiling_bytes",
        "previous_soft_bytes",
        "previous_hard_bytes",
        "expected_error",
        "assertions",
    }
    assert report["case"] == case and report["status"] == "passed"
    if case == "wide":
        assert report["expected_error"] == "reconstruction-domain/wiener"
        assert (
            report["assertions"]
            == "tiny-positive;wide-geometry;wiener-domain;no-memory-cause;inputs-unchanged"
        )
    else:
        assert report["expected_error"] == "reconstruction-domain/Q*P"
        assert (
            report["assertions"] == "tiny-positive;phase-count-positive;no-preparation-frame-cap;"
            "QP-rejection;no-memory-cause;inputs-unchanged"
        )
    for name in (
        "baseline_vm_bytes",
        "guard_vm_bytes",
        "cap_bytes",
        "reserve_bytes",
        "minimum_reserve_bytes",
        "page_bytes",
        "ceiling_bytes",
    ):
        assert type(report[name]) is int and report[name] > 0
    assert report["reserve_bytes"] >= 64 * 1024**2
    assert report["cap_bytes"] <= report["ceiling_bytes"] == 1024**3
    assert report["cap_bytes"] - report["baseline_vm_bytes"] >= report["minimum_reserve_bytes"]
    assert report["cap_bytes"] - report["guard_vm_bytes"] >= report["minimum_reserve_bytes"]
    assert (
        report["cap_bytes"] - report["baseline_vm_bytes"]
        <= report["reserve_bytes"] + report["page_bytes"]
    )
    for name in ("previous_soft_bytes", "previous_hard_bytes"):
        limit = report[name]
        assert limit == "unlimited" or (type(limit) is int and limit >= report["cap_bytes"])
    diagnostics = json.dumps(
        {"stdout": "\n".join(line for line in lines if line != frames[0]), "stderr": stderr},
        sort_keys=True,
    )
    return report, diagnostics


if __name__ == "__main__":
    import sys

    if (
        len(sys.argv) != 3
        or sys.argv[1] != "bounded-declarations"
        or sys.argv[2] not in ("wide", "phase")
    ):
        raise SystemExit("unknown owned fixture invocation")
    bounded_declaration_child(sys.argv[2])
