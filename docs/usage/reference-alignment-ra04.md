# Paired camera and intensity correction

`correct_alignment_pair` prepares a specimen and a bead acquisition in one declared signal gauge. It composes existing acquisition declarations and linear-response correction with an explicit exposure division. The [contract](../contracts/reference-alignment-ra04-v1.md) defines the supported inputs and all unavailable/error outcomes.

## Unit chain

| Quantity | Declared mode | Estimated mode |
|---|---|---|
| Raw C | Detector counts | Detector counts in the calibration's count unit |
| Subtraction baseline O | Applicable sensor-plus-optical mean, counts | Observed blank mean M_B, counts |
| Response r | Counts per declared reference-exposure signal unit | Observed excess flat mean dM=M_F−M_B, counts per flat-relative unit |
| Exposure factor t | Explicit positive dimensionless factor relative to declared reference | Explicit one; changed conditions unavailable |
| First subtraction | C−O, counts | C−M_B, counts |
| Response division | (C−O)/r, signal units at acquired exposure | (C−M_B)/dM, reference-flat-relative units |
| Exposure division | ((C−O)/r)/t, reference-exposure signal units | Identity division recorded once |
| Retained camera variances | No inferred noise model | Original detector-count² statistics |
| Retained empirical mean standard errors | No inferred uncertainty | Original detector-count statistics of frame-mean repeatability |

The supplied baseline may already include optical background: O=o+r*t*B. Subtract it once. Do not then subtract a dark or blank mean again. Separate specimen/bead coefficients may describe the same signal gauge despite different shapes, raw-unit labels or exposures. Each supplied response converts its member's raw unit into the declared common output unit. Calibration IDs are opaque provenance in both modes; equal, different or missing IDs do not authenticate pairing. Estimated mode requires identical declared raw-unit labels for its one shared affine calibration. Even matching text does not verify physical applicability.

## Supplied coefficients

Declare the raw axes and kinds with the existing `declare_acquisition` interface. Supply every exposure factor and the sum-equalization choice explicitly:

```python
import numpy as np
from simrecon import correct_alignment_pair, declare_acquisition

axes = ["orientation", "phase", "y", "x"]
specimen_acquisition = declare_acquisition(
    np.array([[[[22.0]]]]),
    config={"version": 1, "axes": axes, "acquisition_kind": "specimen_sim",
            "intensity_unit": "specimen count", "calibration_id": "supplied specimen"},
)
bead_acquisition = declare_acquisition(
    np.array([[[[18.0]]]]),
    config={"version": 1, "axes": axes, "acquisition_kind": "sim_beads",
            "intensity_unit": "bead count", "calibration_id": "supplied bead"},
)
pair = correct_alignment_pair(
    specimen_acquisition,
    bead=bead_acquisition,
    mode="declared",
    output_unit="synthetic_reference_signal",
    gauge_source="supplied paired synthetic controls",
    specimen_offset=10.0,
    specimen_response=2.0,
    bead_offset=12.0,
    bead_response=4.0,
    specimen_exposure_factor=2.0,
    bead_exposure_factor=0.5,
    reference_sum_equalization="disabled",
)
assert pair.status == "corrected"
assert pair.specimen is not None and pair.bead is not None
print(pair.specimen.data.item(), pair.bead.data.item())  # 3.0 3.0
```

For a specimen raw sample of 22 counts, the sequence gives `(22−10)/2/2=3` signal units. A bead raw sample of 18 counts gives `(18−12)/4/0.5=3` in the same declared unit. Substitution gives `10+2*2*3=22` and `12+4*0.5*3=18` counts. Coefficient and exposure maps must match the complete canonical data shape; no implicit broadcasting aligns phases, orientations or z planes.

Operations use sequential binary64 subtraction, response division and exposure division. Combining response and exposure into one product can change rounding or overflow. Signed corrected samples and finite underflow remain valid. This is not a universal exact-intensity recovery promise at representation limits.

## Estimated coefficients

Use one `estimate_scalar_camera` record from matched stationary dark, blank and flat ensembles for both acquisitions. Choose `mode="estimated"`, pass `camera_estimate=estimate`, omit the four declared coefficients, use `output_unit="reference_flat_relative"` and explicit exposure factors of one. Optional physical gain availability does not control the relative gauge. Nonpositive flat contrast returns `status="unavailable"` with neither corrected member.

Changed estimated-mode exposure is deliberately unsupported here. Under an additional known exposure/background law, a dark-based mean decomposition can be valid, but the scalar estimate alone does not assert that new acquisition law. Do not divide a blank-subtracted image by a new exposure factor and silently treat the result as calibrated.

The result keeps an independent copy of the full camera estimate. Subtracting the mean blank does not remove its photon noise. The original within-frame variance and empirical mean standard-error statistics retain their original units and interpretation. A variance difference used for a gain statistic is not the uncertainty of subtracting independent measurements. Unknown physical gain never turns flat-relative units into electrons or photons. Synthetic moments do not calibrate a real instrument.

## Reconstruction boundary

Pass the corrected member's `data` to a compatible existing reconstruction operation with its explicit phases, transfers and unit conventions. Reconstruction preserves the applicable linear signal scale when its other settings are fixed. Point comparisons require a fixed field, sampling and transfer normalization; a blurred or interpolated peak pixel need not be invariant.

The existing image-only bead and specimen fitters perform their own blank/flat normalization. Their current raw-count interfaces remain unchanged. Passing corrected arrays through those raw-count paths would correct twice. This adapter adds an explicit public composition boundary; it does not migrate those fitter interfaces.

`reference_sum_equalization="disabled"` preserves legitimate frame variation. Requesting `"per_frame_sum"` returns unavailable. For a point under structured illumination, phase can change the total fluorescent signal. Matching each frame's sum would remove part of the measured modulation, and a signed nonzero frame can even have zero sum. This operation applies no camera-specific pixel heuristic, clipping, saturation repair, bleaching model or noise removal.

The [numerical report](../reports/reference-alignment-ra04.md) records the actual evaluated controls and limits.
