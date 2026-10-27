# Observed reconstruction stages

## 01-noisy-exposures

All 15 recorded noisy full-case specimen exposures, fixed z index 16 (local z 2.0625 µm), full 20.48 × 20.48 µm field, nearest-neighbor display. Rows identify orientations; columns identify commanded exposures, not estimated true phases. One shared linear detector-count scale across all panels; no clipping or best-exposure selection.

## 02-camera-correction

Left: all eight frame means in each dark/blank/flat group; dots are frame means and short bars group means. Vertical scale is logarithmic detector counts. Right: the same fixed orientation-1/exposure-1/z-16 pixels before and after (counts − estimated blank mean)/estimated flat-minus-blank contrast. Color scales are corresponding affine transforms, so appearance is intentionally unchanged. This changes units, not spatial resolution or deblurring.

## 03-bead-calibration

Corrected observed held-out bead image and frozen prediction at fixed orientation-1/exposure-1/local z-index-4 (0.5625 µm); full 2.56 × 2.56 µm field, nearest-neighbor display, one shared linear relative-image scale. Signed residual is prediction minus corrected observation on a symmetric scale. Heatmap: root mean square (RMS) residual over each whole held-out 8 × 32 × 32 volume, all 15 volumes, in relative image units. No truth-aligned fit or selection is performed; finite calibration does not establish optical-model validity or uniqueness.

## 04-specimen-fit-progress

The initial source and all 12 accepted iteration scores from the recorded attempt trace. The plotted total dimensionless objective uses all M specimen image values and N source coefficients with regularization 0.001. The solver stopped at its declared iteration limit. A decreasing training objective does not establish convergence, accurate reconstruction or resolution gain. Intermediate source/prediction volumes were not serialized and are not illustrated.
