"""Frozen public mathematical inputs for RM84; no production helper is an oracle."""

from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Mapping
from typing import Any

import numpy as np

OPTICS = {"wavelength_nm": 500, "numerical_aperture": 1.0, "immersion_index": 1.0}
OMITTED = (
    "stage-images",
    "quadratures",
    "overlap-arrays",
    "correlation-arrays",
    "camera-maps",
    "transfer-samples",
    "calibration-arrays",
    "layout-pixels",
    "precise-query-events",
)
SUMMARY_FIELDS = (
    "image",
    "x_um",
    "y_um",
    "z_um",
    "intensity_unit",
    "intensity_semantics",
    "carriers_cyc_um",
    "modulation",
    "raw_modulation",
    "initial_carriers_cyc_um",
    "phase_linkage_carriers_cyc_um",
    "effective_wiener",
    "branches",
    "input_identities",
    "source_declarations",
    "resolved_settings",
    "preparation",
    "estimation",
    "filtering",
    "transfer",
    "calibration",
    "layout",
    "overlap_builds",
    "search_trace",
    "preparation_trace",
    "filtering_trace",
    "trace",
    "diagnostics",
    "omitted_diagnostics",
    "source_revision",
    "reference_sha256",
    "limitations",
)
SPATIAL_DETAILS = {
    "coarse": {"correlation_complex", "correlation_power"},
    "between-build": {"centers", "fourier"},
    "drift-correlation": {"cross_spectrum", "correlation", "absolute_correlation"},
    "exposure-correction": {"phase_multiplier"},
    "between-correction": {"phase_multiplier"},
    "off-combination": {"quadratures_after"},
}
RESOURCE_SHAPES = (
    (1, 3, 8, 32, 32),
    (1, 3, 8, 64, 64),
    (1, 3, 8, 128, 128),
    (1, 1, 8, 64, 64),
    (2, 3, 8, 64, 64),
    (4, 3, 8, 64, 64),
)


def identity(array: np.ndarray, name: str) -> tuple[str, tuple[int, ...], str, str]:
    """Implement CE07 byte identity independently, including endian and signed zero."""
    dtype = array.dtype.newbyteorder("<")
    value = np.ascontiguousarray(array, dtype=dtype)
    return name, array.shape, dtype.str, hashlib.sha256(value.tobytes()).hexdigest()


def identity_values(value: Any) -> tuple[Any, ...]:
    """Read only the four public identity values."""
    assert tuple(f.name for f in dataclasses.fields(value)) == ("name", "shape", "dtype", "sha256")
    return value.name, value.shape, value.dtype, value.sha256


def declared_transfer(orders: int, z: int, *, layout: str = "radial") -> Any:
    """Supply exact dyadic asymmetric complex tables with ample actual-stencil room."""
    from simrecon import declare_otf

    k = 1 if z == 1 else 16
    if layout == "radial":
        m, r, a = np.indices((orders, 64, k))
        samples = 1 + m / 16 + r / 128 + 1j * (m + r + a) / 256
    else:
        m, a, y, x = np.indices((orders, k, 64, 64))
        samples = 1 + m / 16 + x / 128 + 1j * (m + y + a) / 256
    return declare_otf(samples, layout=layout, dkr_cyc_um=0.125, dkz_cyc_um=0.125)


def analytical_case(*, complex_table: bool = False) -> dict[str, Any]:
    """CE07 section 9.1 finite control, explicitly not a physical recovery model."""
    from simrecon import declare_otf

    raw = np.broadcast_to(
        np.array([6, 3, 3], dtype=np.float32)[None, None, :, None, None, None], (1, 1, 3, 2, 2, 4)
    ).copy()
    samples = np.ones((2, 8, 2), dtype=np.complex128)
    if complex_table:
        samples[1] += 1j * np.arange(8)[:, None]
    return {
        "specimen": raw,
        "acquisition": dict(
            acquisition_mode="3d",
            dxy_um=1.0,
            dz_um=1.0,
            norders=2,
            background=0.0,
            lateral_zoom=1,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        "optics": OPTICS.copy(),
        "carrier": dict(linespacing_um=8.0, phase_start_angle_rad=0.0, search_carriers=False),
        "filtering": dict(wiener=1.0, suppress_singularities=False, output_taper="none"),
        "specimen_identity": dict(id="rm84-analytic", intensity_unit="camera counts"),
        "transfer": declare_otf(samples, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.5),
        "transfer_identity": dict(
            id="rm84-table", intensity_unit="dimensionless-transfer", optics=OPTICS.copy()
        ),
    }


def analytical_expected(complex_table: bool) -> tuple[np.ndarray, complex]:
    """Return the CE07 9.1 closed form with the fixed bound justified in the A report."""
    a0 = 1 + np.sqrt(2)
    mu = (a0 - 1j) / 4
    if complex_table:
        factor = 3 * (2 - 1j) * mu / (20 * np.sqrt(2))
        x = np.arange(4) - 2
        image = 12 / (2 + 2.5 * abs(factor) ** 2) + 6 * np.real(
            np.conj(factor) * np.exp(1j * np.pi * x / 4)
        ) / (2 + 3 * abs(factor) ** 2)
    else:
        factor = (a0 - 1j) / 16
        image = (12 + 3 / 8 * np.array([1, a0, a0, 1])) / (2 + (2 + np.sqrt(2)) / 64)
    return np.broadcast_to(image, (1, 2, 2, 4)).copy(), complex(factor)


def workload(
    shape: tuple[int, int, int, int, int] = (2, 3, 4, 16, 16),
    *,
    search: bool = False,
    mode: str = "3d",
    layout: str = "radial",
) -> dict[str, Any]:
    """Analytic multifrequency counts; formulas/constants are fixed before candidate runs.

    Object has nonzero axial and lateral harmonics. Unequal phase harmonics and
    time-varying responses prevent a time-zero-modulation replay from passing.
    Float32 rounding is an explicit detector representation, not oracle tuning.
    """
    t_count, d_count, z_count, y_count, x_count = shape
    p_count = 5
    z, y, x = np.indices((z_count, y_count, x_count), dtype=np.float64)
    object_counts = 30 + 3 * np.cos(2 * np.pi * (x / x_count + y / y_count))
    object_counts += 2 * np.sin(2 * np.pi * (2 * x / x_count - y / y_count))
    object_counts += np.cos(2 * np.pi * (z / z_count + 3 * x / x_count))
    object_counts += 0.75 * np.cos(2 * np.pi * (3 * y / y_count + x / x_count))
    raw = np.empty((t_count, d_count, p_count, z_count, y_count, x_count), dtype=np.float32)
    for t in range(t_count):
        for d in range(d_count):
            angle = d * np.pi / d_count
            spatial = 2 * np.pi * (x * np.cos(angle) + y * np.sin(angle)) / 8
            for p in range(p_count):
                phase = 2 * np.pi * p / p_count
                illumination = 1 + (0.31 + t / 64) * np.cos(spatial + phase)
                illumination += (0.13 + t / 128) * np.cos(2 * spatial + 2 * phase + 0.3)
                raw[t, d, p] = object_counts * illumination + d / 4 + t / 8
    return {
        "specimen": raw,
        "acquisition": dict(
            acquisition_mode=mode,
            dxy_um=1.0,
            dz_um=1.0,
            norders=3,
            background=0.0,
            lateral_zoom=2,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        "optics": OPTICS.copy(),
        "carrier": dict(
            linespacing_um=4.0,
            phase_start_angle_rad=0.0,
            search_carriers=search,
            use_time0_carriers=True,
        ),
        "filtering": dict(wiener=0.5, suppress_singularities=False, output_taper="none"),
        "specimen_identity": dict(id="rm84-multifrequency-v1", intensity_unit="signed-counts"),
        "transfer": declared_transfer(3, z_count, layout=layout),
        "transfer_identity": dict(
            id="rm84-complex-dyadic-v1",
            intensity_unit="dimensionless-transfer",
            optics=OPTICS.copy(),
        ),
    }


def scenario(name: str) -> dict[str, Any]:
    """Return named positive contract examples, each through a real workflow entry."""
    case = workload()
    acq, carrier, filt = case["acquisition"], case["carrier"], case["filtering"]
    if name == "signed":
        case = analytical_case(complex_table=True)
        case["specimen"] *= -1
    elif name in {"searched-reuse", "searched-independent"}:
        carrier.update(search_carriers=True, use_time0_carriers=name == "searched-reuse")
    elif name == "full-transfer":
        from c_workflow_oracle import control_cases
        from c_workflow_support import keywords

        public_case = control_cases()["full3d-asymmetric"]
        case = dict(specimen=public_case.raw, **keywords(public_case))
    elif name in {"2d", "2d-search", "fractional", "precise-inactive"}:
        case = workload((2, 2, 1, 12, 16), mode="2d", search=name == "2d-search")
        if name == "fractional":
            case["acquisition"].update(lateral_zoom=1.5, axial_zoom=3, dz_um=0.0)
        if name == "precise-inactive":
            case["filtering"]["precise_taper"] = True
    elif name in {"supplied", "steps", "reduced"}:
        phases = np.tile(np.array([0, 1.1, 2.5, 3.8, 5.2]), (3, 1))
        acq.update(phases_rad=phases, phase_policy="supplied")
        if name == "steps":
            acq.update(phase_steps_rad=np.array([1.1, 1.2, 1.3]), phase_policy="steps")
        if name == "reduced":
            acq["norders"] = 2
    elif name in {"camera", "off1", "off2", "all-skip"}:
        t, d, p, z, y, x = case["specimen"].shape
        acq.update(
            background=np.full((y, x), 0.5),
            flatfield_slope=np.full((y, x), 1.25),
            equalize=True,
            equalize_z=True,
            equalize_time=True,
        )
        case["exposure_background"] = np.full((t, d, p, z), 0.125)
        if name == "camera":
            case["specimen"][0, 0, 0, 0, -1, -1] = -1
        if name in {"off1", "off2"}:
            n = int(name[-1])
            acq["dxy_um"] = 0.1  # nonempty cells outside integer optical cutoff C=4
            case["off_exposures"] = np.repeat(case["specimen"][..., None, :, :] / 8, n, axis=4)
            acq["combine_off_orders"] = np.array([1, 1, 1])
        if name == "all-skip":
            acq["combine_off_orders"] = np.array([0, -1, 0])
    elif name in {"literal-direction", "literal-z"}:
        case = workload((1, 2, 2, 12, 16))
        case["acquisition"].update(
            acquisition_mode="2d",
            storage_order=("direction-major" if name == "literal-direction" else "z-major"),
        )
        case["transfer"] = declared_transfer(3, 1)
        case["plane_policy"] = "literal-2d-stack"
    elif name in {"between", "within", "fast"}:
        case = workload((2, 4 if name == "within" else 1 if name == "fast" else 3, 4, 12, 12))
        acq = case["acquisition"]
        acq["drift_between"] = True
        if name == "fast":
            acq["storage_order"] = "z-major"
        if name == "within":
            acq.update(drift_within=True, adjust_phases=True, phase_policy="drift")
            size = int(np.prod(case["specimen"].shape[:4]))
            case["header_timestamps"] = np.arange(size, dtype=np.float64)
            case["header_timestamp_unit"] = " ms "
            case["header_phases_rad"] = np.tile(2 * np.pi * np.arange(5) / 5, size // 5)
    elif name == "filtering":
        filt.update(
            wiener_increment=-0.125,
            suppress_singularities=True,
            suppression_radius_bins=-1.0,
            omit_order0=True,
            omit_kz0=True,
            filter_overlaps=False,
            explode_factor=-1.25,
            output_taper="power",
            power_taper_exponent=0.0,
        )
    elif name == "cosine":
        filt["output_taper"] = "cosine"
    elif name == "known":
        pass
    else:
        raise ValueError(f"unknown scenario {name}")
    return case


def walk_arrays(value: Any) -> list[np.ndarray]:
    """Traverse public record/container values, with cycle and shared-object handling."""
    arrays: list[np.ndarray] = []
    seen: set[int] = set()

    def visit(item: Any) -> None:
        if id(item) in seen:
            return
        seen.add(id(item))
        if isinstance(item, np.ndarray):
            arrays.append(item)
        elif dataclasses.is_dataclass(item) and not isinstance(item, type):
            for field in dataclasses.fields(item):
                visit(getattr(item, field.name))
        elif isinstance(item, Mapping):
            for key, child in item.items():
                visit(key)
                visit(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                visit(child)

    visit(value)
    return arrays


SCENARIOS = (
    "known",
    "signed",
    "searched-reuse",
    "searched-independent",
    "full-transfer",
    "2d",
    "2d-search",
    "fractional",
    "precise-inactive",
    "supplied",
    "steps",
    "reduced",
    "camera",
    "off1",
    "off2",
    "all-skip",
    "literal-direction",
    "literal-z",
    "between",
    "within",
    "fast",
    "filtering",
    "cosine",
)


def qualify() -> None:
    """Print source-free public-result branch and fixture qualification evidence."""
    import json

    from simrecon import reconstruct_workflow

    for name in SCENARIOS:
        case = scenario(name)
        try:
            result = reconstruct_workflow(**case)
            print(
                json.dumps(
                    dict(
                        name=name,
                        status="pass",
                        branches=result.parameters.branches,
                        specimen=identity(case["specimen"], "specimen"),
                        image=identity(result.image, "image"),
                        preparation_kinds=sorted({e.kind for e in result.bands.trace}),
                        search_kinds=sorted({e.kind for e in result.parameters.trace}),
                    )
                ),
                flush=True,
            )
        except Exception as exc:
            print(
                json.dumps(
                    dict(
                        name=name,
                        status="failure",
                        type=type(exc).__name__,
                        code=getattr(exc, "code", None),
                        message=str(exc),
                    )
                ),
                flush=True,
            )


if __name__ == "__main__":
    qualify()
