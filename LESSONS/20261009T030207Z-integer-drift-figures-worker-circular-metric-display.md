# Preserve circular-metric precision when plotting saved comparisons

**Version 1.0**

- ID: 20261009T030207Z-integer-drift-figures-worker-circular-metric-display
- Date: 2026-10-09T03:02:07.574603+00:00
- Task: [Integer drift figure follow-up](../docs/tasks/integer-drift-correction.md)
- Role: mechanical documentation worker
- Topic: scientific figure presentation
- Status: confirmed
- Observation: The accepted circular phase metric is a dimensionless represented-input phasor distance. Its 90-digit observer maxima must be taken from the measurement record; distances recomputed from rounded complex snapshots can differ. Reconstruction image panels show real parts, while the recorded error uses absolute complex differences. Common image/error scales make the wrong-phase control comparable without magnifying the corrected residual.
- Evidence: [Figure data and source hashes](../docs/references/scientific/integer-drift-figures.json), [captions and figures](../docs/reports/integer-drift-correction-comparison.md), accepted fixture SHA256 `1f0642051492dff8aef8e342acecff2ff82749c9d180d9eddd34ffcae1b56a8f`; exact saved-array/metric checks passed under the project NumPy 2.5.3 environment. Matplotlib 3.11.2 rendered saved values without product calls in a separate cached plotting environment; visual inspection caught and corrected one annotation overlap.
- Suggested action: Preserve the original metric, units, display transforms and source identity when adding figures to an already reviewed numerical comparison.
