# Bead grid-peak localization v1

**Version 1.0.** Authorized October 10, 2026 under the owner's continuing-roadmap instruction and explicit selection of a documented synthetic 3D calibration model. This partial C1 foundation follows completed raw declarations and declared linear-response correction. [Synthetic model](../models/synthetic-3d-acquisition-v1.md) selects the C0 meaning for independent development; actual instrument settings remain unknown. [Task](../tasks/bead-peak-localization.md).

## Public boundary and estimator

Export from simrecon:

```python
locate_bead_peak(volume) -> BeadPeak
```

Volume is an observed/derived real zero-order intensity volume, with axes z/y/x. The caller explicitly selects a single orientation/channel/time group, applies its declared correction and separates with legitimate known phases before passing the observed dc array. No bead position, detection kernel, true origin, sampling, phase command, phase estimate or acquisition record is accepted by this operation. There is no implicit composition or grouping.

Let a be an independent native float64 snapshot of the supplied volume. Define P=max over all a[z,y,x]. If P<=0, reject with no_positive_bead_peak. If more than one coordinate equals the positive P exactly, reject with ambiguous_bead_peak. Otherwise return its sole index and value. Comparison uses exact equality of represented binary64 samples, without tolerance, epsilon floor, margin, signal-to-noise or prominence threshold. The value is exactly the selected converted sample, not a fitted or normalized amplitude. A second unequal local maximum is permitted. A tie among lower samples does not reject.

This estimator finds a grid maximum. It does not certify a single isolated bead, infer its continuous center, fit neighboring samples, estimate a background, unwrap coordinates or assess model validity. A unique largest sample in an off-model or multiple-bead image is accepted. Exact equal positive maxima are ambiguous for this defined estimator; unequal nearly tied samples have a defined maximum but no stability/confidence guarantee. Ties can arise or disappear through prior correction/separation/float64 conversion. A positive subnormal peak is valid; converted all-zero/subnormal-underflow volumes have no positive peak. Signed finite samples and signed zero are allowed.

Under the selected synthetic on-grid point-bead mode, the detection kernel's unique maximum is explicitly at zero displacement, so the observed zero-order peak gives the bead index. This is a chosen center gauge, not an independently inferred experimental point-spread-function (PSF) center. For an asymmetric/off-grid/noisy physical response the grid peak need not equal the emitter position. No physical accuracy or subvoxel error bound is selected. The next empirical-response slice may use this observed integer origin only within its separately contracted gauge.

## Representation, ownership and failures

Volume must be a plain NumPy ndarray, shape (Nz,Ny,Nx), every dimension positive, dtype kind i/u/f of any available width/byte order. Nonarrays, ndarray subclasses/masked arrays and bool/complex/object/string/structured/datetime are rejected. Read-only, strided/reversed, Fortran storage, nonsquare volumes and singleton axes are valid. All source samples and their native float64 conversions must be finite. Validate source finiteness even when conversion would alter values. Converted samples define the problem: integer/wider-float rounding, finite underflow and resulting ties are permitted, without raw-bit fidelity.

Snapshot before maximum selection; preserve caller storage on success/rejection. No promise covers concurrent external mutation. No caller storage is retained in the result. Return frozen-binding BeadPeak with exactly two public fields:

- index_zyx: tuple of three built-in Python integers in corresponding axis bounds.
- value: built-in Python float, strictly positive, finite, exactly the chosen converted value, in the supplied intensity unit.

Direct record construction requires no validation. Units and physical coordinates are not inferred or included. The caller may compute r_min + index_zyx * spacing_zyx for its declared sample-center coordinates; the locator neither validates nor applies this relation. Distinct calls need no shared mutable output. The operation owns one full converted volume plus ordinary scratch; no streaming or working-set limit is selected. It does no I/O, normalization, roll, Fourier transform, correction, phase separation or transfer preparation.

Use existing SimreconError with stable code. Message prose and precedence for simultaneous violations are unspecified. Ordinary Python argument-binding TypeError remains for omitted/extra arguments or unknown keywords; volume may be supplied positionally or by name.

| Rejected obligation | Code |
|---|---|
| Input is not a plain ndarray | invalid_bead_peak_volume |
| Dtype kind outside i/u/f | invalid_bead_peak_dtype |
| Shape outside three positive dimensions | invalid_bead_peak_shape |
| Source or converted samples nonfinite; expected conversion TypeError/ValueError/OverflowError | nonfinite_bead_peak_volume |
| Converted maximum <=0 | no_positive_bead_peak |
| Multiple exact equal positive maxima | ambiguous_bead_peak |

Handled conversion/range/underflow emits no arithmetic RuntimeWarning or FloatingPointError under caller NumPy modes, and restores those modes. Suppress no unrelated warning categories. Allocation MemoryError and unrelated exceptions propagate unchanged; expected conversion translation is confined to conversion. No successful partial result or fallback. There is no sum, norm or interpolation whose overflow can reject safely finite samples; finite binary64 extrema and one positive minimum subnormal remain valid. Source wider finite values outside binary64 range reject; native wider-float availability is platform-dependent and reported honestly.

## Independent evidence and scenarios

[NumPy maximum semantics](https://numpy.org/doc/stable/reference/generated/numpy.max.html) and [array representation](https://numpy.org/doc/stable/reference/generated/numpy.array.html) describe relevant primitives. The exact domain, tie/error/result rules and scientific interpretation above are this task's choices. Independent expected indices come from named coordinates and represented-value comparisons, never product output or private internals. Small synthetic public compositions derive raw exposures independently from the selected model and compare observed peaks to independently chosen bead indices. Derive composition tolerances from the inherited known-phase separator's budget and a peak margin; peak selection/value has no additional approximation tolerance.

| ID | Distinct obligation and concrete risk | Equivalent examples / expectation |
|---|---|---|
| P01 | Public exports, ordinary binding, exact frozen two-field scalar record | Positional/keyword volume; omitted/extra/unknown keyword |
| P02 | Global unique positive maximum returns z/y/x coordinate and exact converted value | Independently labeled asymmetric odd/even/nonsquare arrays |
| P03 | Signed finite values/negative background, tied lower values and unequal multiple local maxima accepted | Unique positive maximum independently identified |
| P04 | Singleton axes and edge/corner peaks accepted; no wrapping/cropping | Every legal coordinate with periodic translations where appropriate |
| P05 | Every plain real width/byte order/storage accepted | Integer/wider conversion, read-only/strided/reversed/Fortran storage |
| P06 | Float64 converted-value interpretation includes conversion-created ties/underflow | Adjacent large integers round equal; wider native cases if supported |
| P07 | Nonarray/subclass rejection | Lists, scalar, masked/subclass vs plain ndarray |
| P08 | Unsupported dtype rejection | Bool/complex/object/string/structured/datetime vs real kinds |
| P09 | Wrong rank/nonpositive dimensions rejection | Scalar/2D/4D/empty vs valid three-dimensional singleton |
| P10 | Nonfinite source or converted samples reject whole call | NaN/infinity anywhere; wider finite overflow if supported |
| P11 | No positive converted sample rejects | Negative maximum, all zeros including signed zeros/underflow |
| P12 | Exact tied positive global maxima reject | Adjacent/separated ties/plateau/constant positive vs unequal near tie |
| P13 | Finite extrema/subnormal maxima accepted without internal sum/epsilon floor | One positive q=2^-1074, max float64, mixed negative extrema |
| P14 | Input snapshot/preservation and scalar result ownership | Caller unchanged; later mutation cannot change result |
| P15 | NumPy modes/warnings preserved; allocation/unrelated failures propagate | Public safe boundary evidence where available; disclose unportable injection gaps |
| P16 | Actual corrected known-phase synthetic bead composition and documented estimator limits | Explicit commands distinct from truth; correction→separation.dc→peak; independent index and margin |
| P17 | Existing APIs/dependencies/gates unchanged; executed usage comparison | Model/coordinate/unit/finite-grid and partial C1 status explicit |

There is no scenario/review/repair/execution limit set. A maps every obligation and relevant permitted-positive case. B independently reviews oracle, omissions, ambiguity and valid alternatives before C. No percentage-driven tests or invented physical rejection rules. Source-free public probes may report unsupported portable failure injection or storage instead of forcing impossible internal state.

A owns tests/test_bead_peak_localization.py and optional tests/bead_peak_fixture.py only. C owns src/simrecon/_bead_peak.py, additive src/simrecon/__init__.py exports and docs/usage/bead-peak-localization.md only. C produces two actual usage examples: a labeled signed asymmetric volume, and a corrected phase-resolved synthetic point-bead acquisition through public R1/R2/separation/locator with differing nominal commands and explicitly supplied true phases. Retain input/expected/output identities, selected index/value, intensity units and peak-margin/separation-error evidence in ignored artifacts. The true bead index is used only for independent comparison, never passed to locator. Coordinator owns this contract, synthetic model, task/project pointers and one useful evidence-linked unique root lesson.

Fresh native Sol/high A/B/C/D with optional memory/delegation disabled. B-accepted tests/fixtures freeze before C. D forms independent assessment after exact clean canonical make verify and before current-task implementation lessons. Inherit the owner-selected advisory coverage percentages and complete native global/per-package/owned-file JSON/HTML integrity, never-imported owned runtime and relevant subprocesses. Ubuntu24.04/macOS15 CI run the full configured suite separately. No workflow, dependency, discovery, coverage, skill/policy or unrelated interface edits. Full-local gate precedes opening/pushing the stacked PR. No Superpowers, legacy execution, private upload, merge or release.
