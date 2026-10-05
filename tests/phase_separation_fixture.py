"""Independent NF02 stored-value oracle and reusable analytic visual fixture.

No SIMrecon imports or recovered values belong here. Array identities hash C-order,
little-endian float64 bytes (complex128 for complex arrays), with shape and dtype.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256

import numpy as np
import numpy.typing as npt

RealArray = npt.NDArray[np.float64]
ComplexArray = npt.NDArray[np.complex128]
DecimalArray = npt.NDArray[np.object_]
ORACLE_PRECISION = 120


def _rotation(offset: float) -> tuple[Decimal, Decimal]:
    # Taylor series at the exact stored float64 angle, never a product result.
    angle = Decimal.from_float(offset)
    squared = angle * angle
    cosine = cosine_term = Decimal(1)
    sine = sine_term = angle
    for k in range(1, 100):
        cosine_term *= -squared / Decimal((2 * k - 1) * (2 * k))
        sine_term *= -squared / Decimal((2 * k) * (2 * k + 1))
        cosine += cosine_term
        sine += sine_term
    return cosine, sine


def stored_value_oracle(
    images: npt.NDArray[np.generic], offset: float
) -> tuple[DecimalArray, DecimalArray, DecimalArray]:
    """Evaluate the contract's closed form from exact stored real values.

    At 120 significant decimal digits, sqrt and trigonometric error is far below
    the 64*2**-52 relative allowance, even for near-max and subnormal data.
    Decimal exponents encompass the entire float64 range. No float intermediate
    sum, difference, intensity product or tiny tolerance is used.
    """
    shape = images.shape[1:]
    dc = np.empty(shape, dtype=object)
    real = np.empty(shape, dtype=object)
    imag = np.empty(shape, dtype=object)
    with localcontext() as context:
        context.prec = ORACLE_PRECISION
        cosine, sine = _rotation(offset)
        root_three = Decimal(3).sqrt()
        for index in np.ndindex(shape):
            first, second, third = (
                Decimal.from_float(float(images[(phase, *index)])) for phase in range(3)
            )
            # Roots of unity: r+r**2=-1 and r**2-r=-i*sqrt(3).
            unrotated_real = (2 * first - second - third) / 6
            unrotated_imag = root_three * (third - second) / 6
            dc[index] = (first + second + third) / 3
            real[index] = unrotated_real * cosine + unrotated_imag * sine
            imag[index] = unrotated_imag * cosine - unrotated_real * sine
    return dc, real, imag


def array_identity(array: npt.NDArray[np.generic]) -> str:
    canonical = np.ascontiguousarray(array, dtype=array.dtype.newbyteorder("<"))
    digest = sha256()
    digest.update(str(canonical.shape).encode("ascii"))
    digest.update(canonical.dtype.str.encode("ascii"))
    digest.update(canonical.tobytes())
    return digest.hexdigest()


@dataclass(frozen=True)
class AnalyticPhantom:
    """Frozen record of declared inputs, analytic truth and stored-value truth."""

    images: RealArray
    expected_dc: RealArray
    expected_c1: ComplexArray
    analytic_dc: RealArray
    analytic_c1: ComplexArray
    theta_rad: RealArray
    phase_offset_rad: float
    modulation: float
    carrier_cycles_per_pixel: tuple[float, float]
    carrier_origin_rad: float

    def parameters(self) -> dict[str, object]:
        return {
            "shape_yx": self.analytic_dc.shape,
            "phase_offset_rad": self.phase_offset_rad,
            "phase_spacing_rad": 2 * np.pi / 3,
            "modulation": self.modulation,
            "carrier_cycles_per_pixel_xy": self.carrier_cycles_per_pixel,
            "carrier_origin_rad": self.carrier_origin_rad,
            "intensity_units": "arbitrary units",
            "object_definition": (
                "2+x/64+2*y/40; disk (x=12,y=9,r=4) +19; "
                "disk (x=48,y=27,r=6) +11; bar 7<=x<11,19<=y<34 +14; "
                "bar 24<=x<43,5<=y<8 +9; "
                "curve |y-(25+0.022*(x-27)^2)|<=1.2,18<=x<55 +13"
            ),
            "expected_definition": "closed form for actual stored float64 observations",
            "analytic_definition": "dc=A; c1=0.8*A*exp(i*theta)/2",
            "oracle_decimal_precision": ORACLE_PRECISION,
        }

    def array_identities(self) -> dict[str, str]:
        return {
            name: array_identity(array)
            for name, array in (
                ("images", self.images),
                ("expected_dc", self.expected_dc),
                ("expected_c1", self.expected_c1),
                ("analytic_dc", self.analytic_dc),
                ("analytic_c1", self.analytic_c1),
                ("theta_rad", self.theta_rad),
            )
        }


def analytic_phantom() -> AnalyticPhantom:
    """Build an asymmetric 40 by 64 pixel signal with a diagonal carrier.

    I_p=A*(1+m*cos(theta+phi_p)). Expanding the angle sum gives
    B=m*A*cos(theta), C=-m*A*sin(theta); hence c1=(B-i*C)/2.
    The separate stored-value expectations include float64 generation rounding.
    """
    y, x = np.indices((40, 64), dtype=np.float64)
    amplitude = 2 + x / 64 + 2 * y / 40
    amplitude += 19 * ((x - 12) ** 2 + (y - 9) ** 2 <= 4**2)
    amplitude += 11 * ((x - 48) ** 2 + (y - 27) ** 2 <= 6**2)
    amplitude += 14 * ((x >= 7) & (x < 11) & (y >= 19) & (y < 34))
    amplitude += 9 * ((x >= 24) & (x < 43) & (y >= 5) & (y < 8))
    amplitude += 13 * ((np.abs(y - (25 + 0.022 * (x - 27) ** 2)) <= 1.2) & (x >= 18) & (x < 55))
    modulation = 0.8
    carrier = (0.071, -0.043)  # cycles/pixel, x then y
    origin = 0.37  # radians
    theta = 2 * np.pi * (carrier[0] * x + carrier[1] * y) + origin
    offset = float(np.pi / 6)
    phases = offset + 2 * np.pi * np.arange(3, dtype=np.float64) / 3
    images = amplitude[None, :, :] * (
        1 + modulation * np.cos(theta[None, :, :] + phases[:, None, None])
    )
    exact_dc, exact_real, exact_imag = stored_value_oracle(images, offset)
    expected_dc = exact_dc.astype(np.float64)
    expected_c1 = exact_real.astype(np.float64).astype(np.complex128)
    expected_c1.imag = exact_imag.astype(np.float64)
    analytic_c1 = modulation * amplitude * (np.cos(theta) + 1j * np.sin(theta)) / 2
    for array in (images, expected_dc, expected_c1, amplitude, analytic_c1, theta):
        array.flags.writeable = False
    return AnalyticPhantom(
        images,
        expected_dc,
        expected_c1,
        amplitude,
        analytic_c1,
        theta,
        offset,
        modulation,
        carrier,
        origin,
    )
