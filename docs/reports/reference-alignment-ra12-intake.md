# RA12 intake: a predictive estimate and an identified operator are different claims

**Version 1.0. Historical scientific intake evidence.** This report does not complete
RA12, adopt an operational interface, establish an accepted test checkpoint or
claim an observation-only calibration result. The [task pointer](../tasks/reference-alignment-ra12.md)
identifies the sole mutable Current state and original evidence/accounting.

The [RA12 roadmap](../plans/reference-alignment-roadmap.md#ra12--establish-the-images-only-calibration-handoff)
requires an observation-only calibration handoff and says that calibration-equivalent
settings that change specimen predictions prevent an identified-calibration claim.
It also requires independent predictive evidence. It does not explicitly choose
whether completion may make a narrower, finite-case predictive claim while global
operator identification remains unestablished. The owner subsequently chose that
narrower claim by instructing **“Do it”** after Astra's option-2 recommendation.
The [operational contract](../contracts/reference-alignment-ra12-v1.md) records
the selected interface, finite audit, limits and required independent evidence.

An exhaustive per-input certificate is one sufficient approach. It is not an
additional requirement adopted by this report. A documented finite ambiguity
search is a different approach: its explored alternatives and independent
predictions can be measured, but finite search agreement alone excludes no
unsearched alternative. Neither missing implementation nor difficult mathematics
is, by itself, missing owner authority or proof that another sensor is necessary.

## Completed prerequisites

The managed worktree began clean at the exact completed RA11 commit
`e5f918bc54d1622f92009bce143cffd4ac4a7477` and tree
`b4ae241aaa3975fbf31dd7c303fbe3d4543eb4ce`. Preflight passed with a separate
worktree environment, Python 3.13.12, uv 0.12.19, the locked imports, isolated
build dependency check and explicitly selected Java 21.0.7 reader preparation.
The original cache-access and default-Java failures remain recorded.

The four required existing calibration suites passed **780 tests** in 57.73 s,
with no skips reported. They exercised unchanged RA11 runtime and tests; they are
baseline regression evidence, not acceptance of a new RA12 operation. Full local
verification, fresh native A/B/C/D, final platform qualification and a pull
request have not been completed for RA12. No RA13 successor has been created.

## Exact finite-model expectations

The [public mathematical expectation seed](../contracts/reference-alignment-ra12-expectations-v1.md)
retains the complete finite sphere, pupil and pixel equations. Two results matter:

1. With a shared normalized central expectation, nine distinct structured mean
   columns spanning all four harmonic image components determine their phase
   curve up to one common rotation or reflection. The proof uses the degree-four
   quadratic identities of the trigonometric moment curve. It identifies neither
   the finite source profile nor carrier or beam powers by itself. Distinct noisy
   frames and numerical local rank do not establish its exact hypotheses.
2. A legal single-focus acquisition can admit an exact, specimen-changing beam
   alternative. Finite spheres symmetric about that focus cancel the odd axial
   interference term. Exchanging unequal side beams preserves every calibration
   expectation while changing an axial specimen prediction. This is a genuine
   unavailable class, not a counterexample for every multi-focus acquisition.

These arguments received independent report-only mathematical checks. They still
require the formal role-specific test/oracle review before numerical adoption.

## Executed known-input ambiguity control

The following is an explicitly **known-input diagnostic**, not a calibration fit.
All settings and the displayed catalogue center were fixed before execution.
There was no source, phase, seed, slice or scale selection after observing output.

Calibration contains three finite radius-0.050 µm spheres centered axially at
0.0625 µm in a single-focus `(1,32,32)` detector volume. Detector spacing is
`(0.125,0.080,0.080)` µm and source refinement is `(8,8,8)`. The two models use
the same source, signed carriers, nine actual phases, clear finite pupil order
128 and pixel midpoint samples `(2,2)`. Their beam amplitudes are `(4,2,1)` and
`(4,1,2)`. The specimen is a separately predeclared three-object control on
`(8,32,32)`, not the original 27-object benchmark. Its first-five phases reuse
the calibration phases after exactly one known origin transfer.

| Measurement | Calibration, all 27 exposures | Specimen, all 15 exposures |
|---|---:|---:|
| Compared detector values | 27,648 | 122,880 |
| Maximum absolute difference | 1.7763568394002505e-14 electrons | 40.45531442489495 electrons |
| Difference Euclidean norm | 5.289621440122431e-14 electrons | 698.5837026077676 electrons |
| First-model reference norm | 2814.677102254029 electrons | 3540.168331414852 electrons |
| Relative difference norm | 1.879299560111686e-17 | 0.19733064566694597 |
| Reported arithmetic comparison scale, `2e-5*T_observed` | 0.0024518237433488006 electrons | 0.0026108768654656144 electrons |

The specimen ratio is `698.5837026077676 / 3540.168331414852 = 0.19733064566694597`.
It is a **19.733% difference between two model predictions**, not reconstruction
error, resolution gain or a measured accuracy score. The calibration equality
has an independent analytic explanation: its paired source sites have opposite
axial displacement and equal detection response. The specimen difference is
well above the reported optical arithmetic comparison scale. A strict upper
bound from an observed unilluminated peak uses
`T_exact <= T_observed/(1-1e-5)`; that small correction does not change this
separation. The original producer values remain retained unchanged.

The first model is the predeclared comparison denominator, not a claimed
experimental ground truth. Both arrays were evaluated with the same existing
optical implementation. The analytic symmetry is independent of that evaluation;
these are not two independent numerical implementations. No noisy acquisition,
camera estimate, reconstruction or observation-only inference was performed.
Nothing here establishes ambiguity for the retained eight-focus calibration
benchmark.

Retained local evidence is under `artifacts/ra12/known-input-control/`:

- `predeclared-manifest-1.json` fixes all known inputs and the catalogue-center rule.
- `generate.py`, `execution-1.json`, `execution-1.log`, `measurement-1.json` and
  `known-input-arrays-1.npz` retain the actual source, command, environment, arrays,
  hashes and numerical/resource observations.
- `render-provenance-2.json` binds the final PNG/SVG figures, source inputs, plot
  environment, font and exact scales. The original rendering and diagnosed
  presentation/environment corrections remain separately retained.

The [public figure set and numerical metadata](../studies/reference-alignment-ra12/known-input-control/README.md)
export the retained figures without changing their bytes. The final figures are `calibration-ambiguity-2.png`,
`specimen-ambiguity-2.png` and `fixed-center-profiles-2.png`. They retain XY/XZ
maximum projections, XY/XZ catalogue-center sections, equal physical aspect,
micrometre axes, common quantitative signal scales and symmetric signed
differences. Profiles separately show quantitative signal and own-peak-normalized
shape. Displayed images use fixed orientation 0 and exposure 0; table metrics use
every exposure. Differences of projections are not projections of signed volume
differences. No inference was rerun to render them.

## Representation and uncertainty limits

The existing [physical specimen fit](../contracts/image-only-specimen-fit-v1.md)
can consume a shared image-derived camera record, fitted signed carriers, beam
amplitudes and phases already transferred to its origin. Its source basis has
half-cell locations and two source samples per lateral detector dimension. It
normalizes raw counts itself; feeding it already corrected data would normalize
twice.

RA05's periodic point/discrete-profile transfer, RA09's conditional overlap
comparison and RA10's fixed-kernel same-grid phase model do not automatically
convert this physical finite sphere model. Any required conversion needs its own
explicit coordinate, source basis, pixel-area and normalization meaning.

Finite pupil orders 128, 256 and 512 are different finite models. Their observed
differences are sensitivity, not a certified continuum error bound. Optical
arithmetic, source discretization, finite source-basis changes, inverse numerical
error, camera uncertainty and statistical noise remain distinct. No new confidence
guarantee follows from recording noisy diagnostics. A confidence-level choice is
needed only if a statistical guarantee is actually selected; it is not an
automatic prerequisite to develop or assess a finite-model estimator.

The resolved completion choice is the narrower predictively validated estimate
with a finite ambiguity audit and explicit identification limits. It creates no
global-uniqueness or statistical-confidence claim. Routine inference-model
settings, independently derived arithmetic tolerances, controls and role
transitions continue under the existing authorization.
