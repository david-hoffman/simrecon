# Comparable-reference periodic volume translation

**Version 1.0.** The new `estimate_volume_translation` operation measures integer content displacement between supplied comparable 3D volumes. It returns the complete periodic mismatch surface and every candidate admitted by the caller's ambiguity tolerance. Displacements use z/y/x voxel units. The volumes must share the stated intensity model; a sole candidate supplies no physical-motion or fit-acceptance guarantee.

The [contract](../contracts/volume-translation-estimation-v1.md) defines the scientific meaning. The [executed usage](../usage/volume-translation-estimation.md) shows caller composition and negative-roll alignment. This report records small synthetic observations. Final candidate, full-check, independent review and native platform evidence remain at the [task's sole Current-state pointer](../tasks/volume-translation-estimation.md#current-state-pointer), outside these tracked report bytes.

## Independent comparison

The actual producer used exact rational representations of converted binary64 inputs. For every canonical displacement, it summed indexed squared raw differences and divided by P B², where P is voxel count and B is the maximum absolute intensity across both volumes. A 160-digit Decimal square root supplied the expected dimensionless root mean square (RMS) score. It used neither product output nor the reviewed test oracle as truth. Known shifts were evaluator-only inputs; the estimator received moving, reference and tolerance.

All 11 complete surfaces agreed within the contract allowance. Four known comparable-reference shifts matched their canonical truth. The largest observed absolute score error was 1.1102230246251565 × 10⁻¹⁶. For the largest observed P=60, the allowance is 4096 × 60 × 2⁻⁵² = 5.4569682106375694 × 10⁻¹¹. The smallest independent winner margin was 0.15335095364797155, comfortably larger than that numerical allowance. This score comparison is separate from displacement truth and physical accuracy.

| Observation | Shape z/y/x | Returned displacement, voxels z/y/x | Minimum RMS | Candidates | Maximum absolute score error |
|---|---|---|---:|---:|---:|
| motion_positive | 3 × 4 × 5 | (1, -1, 2) | 0 | 1 | 2.78e-17 |
| motion_negative | 3 × 4 × 5 | (-1, 1, -2) | 0 | 1 | 2.78e-17 |
| motion_half_period | 2 × 4 × 6 | (-1, -2, -3) | 0 | 1 | 2.78e-17 |
| motion_singleton_axis | 1 × 3 × 5 | (0, -1, 2) | 0 | 1 | 5.55e-17 |
| gain_changed | 3 × 4 × 5 | (1, -1, 2) | 0.08145186488 | 1 | 2.78e-17 |
| background_changed | 3 × 4 × 5 | (1, -1, 2) | 0.08095238095 | 1 | 5.55e-17 |
| structure_changed | 3 × 4 × 5 | (1, -1, 2) | 0.0835520678 | 1 | 5.55e-17 |
| repeated_axial | 4 × 2 × 3 | ambiguous | 0 | 4 | 5.55e-17 |
| all_zero | 2 × 3 × 4 | ambiguous | 0 | 24 | 0 |
| constant_mismatch | 2 × 3 × 4 | ambiguous | 0.6 | 24 | 1.11e-16 |
| singleton_poor_fit | 1 × 1 × 1 | (0, 0, 0) | 2 | 1 | 0 |

The first four cases belong to the nonnegative asymmetric comparable-reference group. The remaining seven are ambiguity and off-model controls. Changes in gain, background and structure remain visible as nonzero residuals. Repeated axial content retains four candidates. Zero and mismatched constant volumes retain every candidate. For the constant control, |5−2|/5 = 0.6 at every shift. The singleton poor-fit control has |5−(−5)|/5 = 2 and still has one candidate. These analytic checks show why uniqueness alone cannot accept a fit.

The literal Python block from the final guide was extracted, compiled and executed. Actual output was:

```text
(1, -1, 2)
0.0
None
True
```

The last value checks exact alignment of the stored example arrays after rolling by the negative returned displacement.

## Execution and provenance

The current observation run is `artifacts/roadmap-successor-20261018/C01/examples03`. Its 19 retained output files include actual inputs, full returned and expected surfaces, exact rational squared-score expectations, candidate lists, aligned arrays, literal usage input/output and process logs. Two actual producer sources are separately inventoried. The v2 manifest and actual-child association are under `C01/invocations/resume01/examples03-{manifest,association}.json`; before/after inputs and original dirty Git identity remain unchanged. The child exited 0 without timeout. Later clean admission is a separate record.

The generation census contains 14,147 stable input records, including all 43 recursive runtime Python files, frozen new and relevant 2D tests/fixtures, both contracts, lock/project files, final usage guide, producer sources, current managed environment configuration/regular files and resolved interpreter. These are enumerated endpoint observations. They do not establish universal operating-system, native-loader, standard-library, transient-cache or process custody. Local execution used CPython 3.13.12 and NumPy 2.5.3 on macOS 27.0.1 arm64.

Original observation runs remain historical evidence. The first producer packaging attempt used relative managed dependency names; a distinct second run corrected admission naming. A later runtime correction shared the settled tolerance validator between the 2D and 3D operations and required this fresh third run. No original observation or generation identity was overwritten. Initial lint/format failures and all correction costs remain recorded. Frozen reviewed tests/fixtures are unchanged.

The final focused public check passed 366 cases without skips, including existing scalar-conversion and exception-preservation compatibility cases. Both changed runtime modules measured complete native Coverage.py executable statements and branch destinations in that focused run: 2D 64/64 and 18/18; 3D 48/48 and 12/12, zero exclusions. This is limited focused evidence. Exact clean canonical verification of all 13 phases and separate required native-platform evidence remain delivery requirements; these percentages do not prove complete behavior.

## Limits

These are modest periodic synthetic volumes. No physical motion, fractional displacement, nonperiodic correction, raw-illumination-phase drift inference, comparable-reference construction, confidence/noise threshold or full-size feasibility was established. Direct evaluation costs O(P²) work and O(P) working storage, so use modest volumes or regions of interest. Existing 2D public behavior remains separate. Continuous nuisance inference, the complete raw workflow, realistic truth-hidden simulation and owner-reference parity remain unfinished roadmap exits.
