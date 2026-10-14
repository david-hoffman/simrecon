"""Generate the two documentary reference families on stdout, on demand."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


def asymmetric_display(ky: int, kx: int) -> complex:
    """Evaluate the declared weighted fourth/sixth roots in binary64."""
    fourth = {0: 1, 1: -1j, 2: -1, 3: 1j}[ky % 4]
    mode = kx % 6
    cosine = {0: 1, 1: 0.5, 2: -0.5, 3: -1, 4: -0.5, 5: 0.5}[mode]
    # The historical display rounds this root scalar before applying its weight.
    sine = math.sqrt(3) / 2
    imaginary = -sine if mode in (1, 2) else sine if mode in (4, 5) else 0.0
    return 3 / 8 + fourth / 8 + complex(cosine, imaginary) / 2


def otf_document() -> dict[str, Any]:
    """Build the historical display from analytic cases and algebraic roots."""
    otf = importlib.import_module("otf_calibration_fixture")

    fixtures = []
    for case_id, samples, origin in otf.analytic_cases():
        ny, nx = samples.shape
        ys, xs = list(otf.modes(ny)), list(otf.modes(nx))
        real, imag = [], []
        if case_id in ("delta-odd", "singleton"):
            formula = "H(ky,kx)=1"
        elif case_id == "uniform-even":
            formula = "H(0,0)=1; all other bins zero"
        elif case_id == "separable-mixed":
            formula = "H=outer([1/4,1,1/4],[1,0,1,0]) in declared shifted mode order"
        else:
            formula = "H(ky,kx)=3/8+exp(-2*pi*i*ky/4)/8+exp(-2*pi*i*kx/6)/2"
        for ky in ys:
            real_row, imag_row = [], []
            for kx in xs:
                if case_id in ("delta-odd", "singleton"):
                    re, im = 1.0, 0.0
                elif case_id == "uniform-even":
                    re, im = float(ky == 0 and kx == 0), 0.0
                elif case_id == "separable-mixed":
                    re = (1.0 if ky == 0 else 0.25) * float(kx % 2 == 0)
                    im = 0.0
                else:
                    value = asymmetric_display(ky, kx)
                    re, im = value.real, value.imag
                real_row.append(re)
                imag_row.append(im)
            real.append(real_row)
            imag.append(imag_row)
        fixtures.append(
            {
                "id": case_id,
                "shape_yx": [ny, nx],
                "origin_yx": list(origin),
                "pixel_size_um": [0.125, 0.25],
                "source": "analytic:" + case_id,
                # Historical documentary label; do not change the helper array.
                "input_dtype": "uint8",
                "psf_samples": samples.tolist(),
                "mode_y": ys,
                "mode_x": xs,
                "frequency_y_per_um": [float(v) for v in otf.exact_frequency(ny, 0.125)],
                "frequency_x_per_um": [float(v) for v in otf.exact_frequency(nx, 0.25)],
                "expected_formula": formula,
                "expected_otf_real": real,
                "expected_otf_imag": imag,
                "oracle": (
                    "Exact delta/root-of-unity identities; separable factors are exact rationals; "
                    "asymmetric roots use binary64 sqrt(3) display values."
                ),
                # Original intake observations, never a rerun FFT measurement.
                "example_fft_cross_check_max_abs": (
                    1.1102230246251565e-16 if case_id.startswith("asymmetric-") else 0.0
                ),
            }
        )
    return {
        "version": "1.0",
        "status": (
            "Intake reference examples; not blind-A tests or a reviewed executable checkpoint."
        ),
        "expected_value_policy": (
            "The exact formula is authoritative. JSON complex entries are rounded display values, "
            "not a tight-error oracle."
        ),
        "frequency_policy": "f=k/(N*d) cycles/um; ordered signed mode lists are explicit.",
        "fixtures": fixtures,
    }


def auxiliary_planes() -> tuple[list[list[float]], list[list[float]]]:
    """Generate rounded PSF/object scalars, then the binary64 finite convolution."""
    reconstruction = importlib.import_module("reconstruction_fixture")
    Z, root = reconstruction.Z, reconstruction.root

    with localcontext() as context:
        context.prec = 85
        coefficients = {
            (0, 0): Z(Decimal(4)),
            (1, 0): Z(Decimal("0.25"), Decimal("0.4")),
            (0, 3): Z(Decimal("-0.35"), Decimal("0.2")),
            (2, 1): Z(Decimal("0.15"), Decimal("-0.3")),
        }
        for (j, k), value in list(coefficients.items()):
            if (j, k) != (0, 0):
                coefficients[-j, -k] = value.conj()
        kernel, obj = [], []
        for y in range(7):
            kernel_row, object_row = [], []
            for x in range(9):
                vy = 1 + Decimal("0.8") * root(Decimal(y - 1) / 7).re
                vx = (
                    1
                    + Decimal("0.6") * root(Decimal(x - 1) / 9).re
                    + Decimal("0.2") * root(Decimal(2 * (x - 1)) / 9).re
                )
                kernel_row.append(float(vy * vx / 63))
                scalar = Z()
                for (j, k), value in coefficients.items():
                    scalar += value * root(Decimal(j * y) / 7 + Decimal(k * x) / 9)
                object_row.append(float(scalar.re))
            kernel.append(kernel_row)
            obj.append(object_row)
    conventional = []
    for y in range(7):
        row = []
        for x in range(9):
            total = 0.0
            for hy in range(7):
                for hx in range(9):
                    product = kernel[hy][hx] * obj[(y - hy) % 7][(x - hx) % 9]
                    total = total + product
            row.append(total)
        conventional.append(row)
    return kernel, conventional


def complex_planes(values: Any) -> dict[str, Any]:
    """Retain the historical real-then-imaginary complex layout."""
    return {"real": values.real.tolist(), "imag": values.imag.tolist()}


def reconstruction_document() -> dict[str, Any]:
    """Adapt the frozen independent finite-sum helper, without product solvers."""
    import numpy as np

    reconstruction = importlib.import_module("reconstruction_fixture")

    psf, conventional = auxiliary_planes()
    entries = []
    for fractional, name in ((False, "commensurate-recovery"), (True, "fractional-estimator")):
        arguments, truth_spectrum, truth = reconstruction.phantom(fractional)
        spectrum, image = reconstruction.estimator(arguments)
        denominators = reconstruction.effective_denominators(arguments)
        record = arguments["otf"]
        images = np.asarray(arguments["images"], dtype="<f8")
        entries.append(
            {
                "name": name,
                "shape_detector": list(images.shape[-2:]),
                "images": images.tolist(),
                "images_sha256": hashlib.sha256(images.tobytes(order="C")).hexdigest(),
                "images_dtype": "<f8",
                "images_layout": "C",
                "phases_rad": arguments["phases_rad"].tolist(),
                "wavevectors_per_um": arguments["wavevectors_per_um"].tolist(),
                "modulation": arguments["modulation"].tolist(),
                "brightness": arguments["brightness"].tolist(),
                "regularization": arguments["regularization"],
                "apodization": arguments["apodization"].tolist(),
                "otf": complex_planes(record.values),
                "pixel_size_um_detector": list(record.pixel_size_um),
                "origin_yx_psf": list(record.origin_yx),
                "source_label": record.source,
                "independent_psf": psf,
                "object_truth": complex_planes(truth),
                "object_truth_spectrum": complex_planes(truth_spectrum),
                "rounded_data_estimator_spectrum": complex_planes(spectrum),
                "rounded_data_estimator_image": complex_planes(image),
                "conventional_unilluminated_observation": conventional,
                "informative_budget_coordinate": float(reconstruction.accuracy_budget(arguments)),
                "min_positive_V": float(denominators[denominators > 0].min()),
                "max_V": float(denominators.max()),
                "physical_limitation": (
                    "Fractional circular illumination is not exactly inverted by bilinear "
                    "spectral interpolation."
                    if fractional
                    else "Exact physical recovery requires the selected commensurate, alias-free "
                    "support; rounded observations differ from analytic truth."
                ),
            }
        )
    return {
        "version": 1,
        "role": "fresh blind A; not yet B accepted",
        "product_outputs": False,
        "oracle_precision_decimal_digits": 85,
        "oracle_methods": [
            "Taylor root series",
            "explicit periodic spatial convolution",
            "pivoted 3x3 Decimal normal equations for well-conditioned represented "
            "trigonometric entries",
            "negative-exponential finite sums divided by detector sample count",
            "scalar closed-edge bilinear interpolation",
            "positive-exponential unnormalized synthesis",
        ],
        "units": {
            "spatial": "micrometres",
            "wavevectors": "cycles/micrometre",
            "phases": "radians",
            "otf": "dimensionless",
            "intensity": "arbitrary signed intensity units",
        },
        "object_coefficients": {
            "0,0": [4, 0],
            "1,0": [0.25, 0.4],
            "0,3": [-0.35, 0.2],
            "2,1": [0.15, -0.3],
            "negative_modes": "complex conjugates",
        },
        "psf_formula": (
            "(1+0.8*cos(2*pi*(y-1)/7))*(1+0.6*cos(2*pi*(x-1)/9)+0.2*cos(4*pi*(x-1)/9))/63"
        ),
        "psf_preprocessing": (
            "Analytic nonnegative unit discrete mass. No background correction, recentering, "
            "pixel area factor or measured optical claim."
        ),
        # Immutable observations of the original A checkpoint, not current hashes.
        "independent_input_hashes": {
            "tests/test_reconstruction.py": (
                "442f8a0f867370f06b9255178fec5568aa672779614bce5b374457666138d69b"
            ),
            "tests/reconstruction_fixture.py": (
                "12af3e75c815e38edbd2e1d8de0c3ddf64911117a074e0bd783ac518e02a01cd"
            ),
            "tests/reconstruction_failure_controls.py": (
                "3f2d0ff833e4e96a2b27ddfd29db816a8f18818f735e6fb3a0ee997daffbbe93"
            ),
            "docs/contracts/known-parameter-reconstruction-v1.md": (
                "e110fab1ef807a4ba2cdada351d8b0eba6e78a3c2cb14031c271b7615a359813"
            ),
            "docs/contracts/known-phase-separation-v2.md": (
                "af8b0bc503a2c6d73ed54d0cd21083ded11e26007a32b1fd320d11254018562d"
            ),
            "docs/contracts/otf-calibration-v1.md": (
                "15ba13ab604ab123799596392fbdeee632021f53ec552709db18a61aa4a00d75"
            ),
            "uv.lock": "e6ff14aa7d6c2108292aaef624d150f48876954ff3989e1bc3955ef2aa1ddb2b",
            "pyproject.toml": "c61e10e718872016e3e6e9bf633fcf9b1907a6e1ebfe1d603bfef193e14c9043",
        },
        "primary_references": [
            "https://numpy.org/doc/stable/reference/routines.fft.html",
            "https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RegularGridInterpolator.html",
        ],
        "entries": entries,
    }


def main() -> None:
    """Compute and serialize completely before writing; failures propagate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selector", choices=("otf", "reconstruction"))
    selector = parser.parse_args().selector
    # Import the frozen helpers without creating bytecode beside their sources.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    document = otf_document() if selector == "otf" else reconstruction_document()
    payload = json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    sys.stdout.write(payload)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
