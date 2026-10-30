# Matched complex order calibration

Use the [RA05 adapter](../contracts/reference-alignment-ra05-v1.md) after `correct_alignment_pair` has put specimen and bead data in one declared output unit and gauge. The adapter consumes the corrected bead samples directly. Known actual phases, a known calibration carrier and a declared point or discrete emission profile remain caller inputs.

```python
from simrecon import calibrate_alignment_bead, sample_alignment_order_transfer

calibration = calibrate_alignment_bead(
    pair,
    group={"orientation": 0},
    phases_rad=actual_bead_phases,
    voxel_size_um=(dz_cal, dy_cal, dx_cal),
    calibration_carrier_bins=(ky_cal, kx_cal),
    bead_mode="discrete_profile",
    bead_profile=relative_site_weights,
    min_profile_transfer=0.15,
    source="declared bead, camera and optical pairing",
)
sampled = sample_alignment_order_transfer(
    calibration,
    order=-1,
    frequencies_zyx_per_um=detector_points,
    coordinate_offset_yx=(0, 0),
    phase_reference_shift_rad=specimen_phase_reference - bead_phase_reference,
    source="explicit specimen detector frequencies",
)
```

For a point bead, explicitly select `bead_mode="point"`, `bead_profile=None` and `min_profile_transfer=None`. Present time/channel/orientation axes require their own group index, including singleton axes. Calibration spacing is z/y/x in micrometres (µm). Supplied actual phases are in radians and remain distinct from nominal phase commands. An unavailable camera pair gives an information failure.

A discrete profile contains nonnegative relative weights at calibration grid sites. Its declared anchor is at index zero. Native Fourier division uses the different factors P(k-m*kc) for orders zero, one and two. Compensation precedes anchor localization and interpolation. The explicit transfer minimum applies to every native profile node. Weak, zero or uncertifiable profile transfer rejects the calibration; there is no epsilon-filled result. No continuous sphere, extra pixel integration, radial averaging or support cleanup is inferred.

All orders share the original exact positive dc mass and one observed anchor. The transfer is dimensionless and preserves relative complex amplitude and phase. Original separated components retain the corrected unit. `calibration.provenance["dc_mass"]` retains the reduced exact numerator/denominator and that unit. This shared normalization removes bead brightness from the transfer; it does not determine photons or absolute instrument throughput. Keep the calibration object and correction provenance with sampled results.

`detector_points` is a plain float64 array with shape (P,3), in z/y/x cycles/µm. For object frequency f and signed order m, supply detector frequency f+m*q_specimen, with zero axial carrier. Specimen and calibration grids may differ. Calibration carrier bins remove the bead gauge; specimen carrier bins on a different grid need not be numerically equal. Coordinate offsets use calibration samples. The supplied phase shift is specimen reference minus calibration reference. The adapter estimates none of these quantities.

Negative orders reflect all three physical frequency coordinates before conjugation. Exact ideal source nodes define the closed measured hull. Rounded frequency metadata does not enlarge it. Even-grid negative Nyquist and positive Nyquist endpoints have different coverage. Missing coverage rejects the whole query, including queries whose response would be zero. The existing integer-grid reconstruction has its own modular negative-order convention; this sampler adds no new reconstruction estimator.

The [measured comparison](../reports/reference-alignment-ra05.md) retains independent finite-sum inputs, calibrated outputs, complex order planes and distinct-grid sampling. Known profile, phase and finite-grid premises constrain its claims. Declared matching labels establish provenance, not measured instrument compatibility.

The standalone report commands use the published synthetic archive and reviewed independent observer; each execution requires a new output directory and retains actual corrected/calibrated/sampled records before numerical comparison. Plotting reads those retained arrays separately. See the report for the executed environment, exact comparison limits and original annotation qualification.
