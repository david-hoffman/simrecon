"""Reconstruct a tiny, noiseless synthetic fixture with the public workflow.

Run with `uv run --locked python examples/reconstruct_simulated.py`.
The matched fixture contains differential detector counts and a tabulated optical
transfer. The full specimen simulations and Wiener sweep are separate opt-in runs.
"""

from pathlib import Path

import numpy as np

from simrecon import WorkflowReconstruction, declare_otf, reconstruct_workflow


def reconstruct_simulated(fixture_path: Path) -> WorkflowReconstruction:
    """Reconstruct the matched synthetic counts using their declared settings."""
    with np.load(fixture_path, allow_pickle=False) as fixture:
        # Raw axes are (time, direction, phase, z, y, x).
        raw = fixture["raw"]
        transfer = declare_otf(
            fixture["transfer"], layout="radial", dkr_cyc_um=0.125, dkz_cyc_um=0.25
        )

    optics = {"wavelength_nm": 500, "numerical_aperture": 0.125, "immersion_index": 1.33}
    return reconstruct_workflow(
        raw,
        acquisition={
            "acquisition_mode": "3d",
            "dxy_um": 1.0,
            "dz_um": 1.0,
            "lateral_zoom": 2,
            "axial_zoom": 1,
            "norders": 3,
            "background": 7.0,
            "flatfield_slope": np.full(raw.shape[-2:], 2.0),
            "phase_policy": "uniform",
            "edge_pixels": 0,
            "equalize": False,
            "equalize_z": False,
            "equalize_time": False,
            "storage_order": "direction-major",
            "drift_between": False,
            "drift_within": False,
            "fit_drift": False,
            "adjust_phases": False,
            "drift_filter_fraction": 0.0,
        },
        optics=optics,
        carrier={
            "linespacing_um": 4.0,
            "phase_start_angle_rad": 0.0,
            "negative_angle_step": False,
            "search_carriers": False,
            "use_time0_carriers": True,
            "fit_all_phases": True,
        },
        filtering={
            "wiener": 0.002,
            "wiener_increment": 0.0,
            "suppress_singularities": False,
            "suppression_radius_bins": 0.0,
            "dampen_order0": False,
            "omit_order0": False,
            "omit_kz0": False,
            "output_taper": "none",
            "precise_taper": False,
            "filter_overlaps": True,
            "explode_factor": 1.0,
        },
        transfer=transfer,
        specimen_identity={
            "id": "ce08-matched-recovery-v1",
            "intensity_unit": "calibrated-differential-detector-count",
        },
        transfer_identity={
            "id": "ce08-matched-recovery-v1-matched-transfer",
            "intensity_unit": "dimensionless-transfer",
            "optics": optics,
        },
        exposure_background=np.full(raw.shape[:4], 3.0),
        plane_policy="native",
    )


def main() -> None:
    """Print the signed reconstruction summary without writing an image file."""
    fixture_path = (
        Path(__file__).resolve().parents[1] / "tests" / "data" / "ce08-matched-recovery-v1.npz"
    )
    result = reconstruct_simulated(fixture_path)
    image = result.image
    if not np.isfinite(image).all():
        raise RuntimeError("The synthetic reconstruction contains nonfinite values.")

    dx_um = result.x_um[1] - result.x_um[0]
    dy_um = result.y_um[1] - result.y_um[0]
    dz_um = result.z_um[1] - result.z_um[0]
    print(f"Synthetic signed image shape (time, z, y, x) = {image.shape}")
    print(f"Output pitches (x, y, z) = ({dx_um:g}, {dy_um:g}, {dz_um:g}) µm")
    print(f"Intensity range = [{image.min():.6g}, {image.max():.6g}] {result.intensity_unit}")


if __name__ == "__main__":
    main()
