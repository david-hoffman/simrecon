# Finite integer-carrier scan

**Version 1.0. October 7, 2026.** The owner's instruction to implement the next roadmap slice stacked on PR #11 authorizes this diagnostic step toward carrier estimation. It exposes the candidate landscape rather than claiming an identifiable carrier from a low overlap residual. Report-only Astra/ultra advice informed scope; it is not formal test or candidate acceptance.

## Public boundary

```python
from simrecon import CarrierCandidate, scan_carriers

candidates = scan_carriers(
    images, otf=calibration, phase_steps_rad=steps,
    candidate_carriers_bins_yx=[(0, 2), (1, 2), (-1, -2)],
)
```

Only images is positional. Every keyword is required. Ordinary binding TypeError remains. Inputs images, otf and phase_steps_rad have exactly the representation, conversion, validation, phase separation, precision, copying, warning/error-mode and stable-error semantics of [known-carrier illumination estimation](illumination-estimation-v1.md). All those existing permitted positive classes remain permitted. No file I/O, new dependency, reconstruction change or legacy code use.

candidate_carriers_bins_yx is a nonempty tuple/list of carrier pairs, or a plain ndarray with shape `(M,2)`, M>=1. Each row follows the existing known-carrier representation: tuple/list/plain one-dimensional length-two ndarray of nonboolean Python/NumPy integers in signed y/x detector-bin units. Either endian, strided/read-only integer arrays and object arrays whose entries are actual nonboolean integers are permitted. Lists/tuples can represent arbitrarily large integers. Reject generators, sets, ndarray subclasses, ragged/malformed outer shapes, malformed rows and noninteger/bool entries with SimreconError code invalid_carrier_candidates. Do not round or wrap. Validate the entire candidate representation before numerical candidate execution; no valid prefix can hide a later invalid row. Source arrays and candidate storage remain unchanged on success and rejection. There is no candidate-count cap.

Copy each candidate into a tuple of Python integers. Preserve caller order, duplicates, signed carriers and zero. Fixed supplied phase-step signs distinguish k and -k; do not identify these candidates or deduplicate them. This operation does no continuous or fractional search, automatic grid construction, orientation equivalence or refinement.

## Per-candidate operation and result

Return a nonempty Python tuple with one frozen-binding CarrierCandidate per supplied row, in exactly the supplied order. Fields:

- carrier_bins_yx: independently represented tuple of two Python ints;
- estimate: a successful IlluminationEstimate, otherwise None;
- failure_code: None on success; otherwise exactly no_illumination_overlap or unidentifiable_illumination.

No direct-construction validation is required. Each successful estimate obeys the complete existing known-carrier contract, including geometric closed-grid overlap, full complex OTF, unconstrained modulation, corrected represented-trigonometric phases, independent mutable float64 phases storage, precision/range policy and unchanged source. Its arrays alias neither caller inputs nor another candidate's output, including duplicate candidates. Frozen bindings do not make contained arrays immutable.

For each candidate k, evaluate the existing estimator's equations on that k:

```text
Q_k = {q: q and q+k are inside the closed signed detector grid}
x_k(q) = H(q+k)*D0(q)
y_k(q) = H(q)*Dplus(q+k)
z_k = sum(conjugate(x_k)*y_k) / sum(abs(x_k)**2)
modulation_k = 2*abs(z_k)
phase_offset_k = arg(z_k)
relative_residual_k = norm(y_k-z_k*x_k) / norm(y_k)
```

The known-carrier contract supplies stable arithmetic and informative accuracy obligations. Independent expectations must use analytic/finite-sum or independently justified stored-value calculations, never production output as truth. Single-candidate scans have the same observable successful estimate or candidate-local failure as the existing operation. No bitwise equality across separately executed numerical calls is promised.

A geometric no_illumination_overlap or computed unidentifiable_illumination becomes that candidate's failure_code and scanning continues. All-candidate failure is a valid complete tuple of failure records. Do not invent a whole-call failure or fallback carrier for it. Common input validation still applies when every candidate has no overlap or zero information. Any other SimreconError, inherited separation failure, illumination_solver_failure, unrepresentable_illumination, allocation MemoryError or unrelated exception aborts the whole call and propagates unchanged; return no partial tuple. Catch only the two named candidate-local information failures. Error message prose and simultaneous-error precedence are unspecified.

## Interpretation and limitations

No winner, ranking, confidence, uniqueness, tie breaking, overlap support threshold or physical-modulation filter is returned. A successful candidate can have modulation above one. A lower normalized residual on a different overlap is not a guarantee of the true carrier. In particular, one informative complex pair admits an exact scalar fit for any nonzero x,y; geometric overlap_count also counts zero-transfer pairs. Neither low residual nor a larger geometric count proves identifiability of the physical carrier. Caller candidates change the compared data, not just a fixed objective parameter. Weak support, noise, aliases, periodic/sparse specimens and model mismatch can defeat recovery. These are documented limits, not extra rejection rules.

The diagnostic lets a caller inspect fits and failures before making a separate, explicit scientific selection. Robust carrier selection, continuous search, independent phase-step estimation, drift, brightness estimation, 3D and adapters remain later contracts. This slice claims completion only of finite integer-carrier diagnostics, not of all parameter estimation or owner integration.

## Behavioral inventory and evidence

Every distinct positive guarantee and stable rejection/propagation outcome is mapped independently by A. Group IDs below are headings, not a cap.

| ID | Observable obligation / high-risk path |
|---|---|
| C01 | Public exports, required keyword-only binding, tuple/result record structure |
| C02 | Nonempty finite candidate collection, full prevalidation, invalid_carrier_candidates; legitimate representations and huge integers |
| C03 | Order, duplicates, signed/zero values, Python integer conversion and no wrapping/deduplication |
| C04 | Per-candidate independent full complex fit, phase/modulation signs/scaling and residual on distinct overlaps |
| C05 | Candidate-local no overlap and unidentifiable outcomes, mixed success, all-failed tuple and continued scan |
| C06 | Common input validation and inherited phase/OTF/grid errors even with no successful candidates |
| C07 | Solver/range/MemoryError/unrelated propagation, no partial result, caller warning/error mode |
| C08 | Existing positive representation/precision/range/large-step guarantees; single-candidate compatibility |
| C09 | Frozen bindings, independent mutable successful estimate arrays, preservation of all caller storage on success/failure |
| C10 | No ranking/filtering/selection; m>1, one-pair and ambiguous landscapes honestly exposed |
| C11 | Existing APIs/commands/dependencies intact; no I/O or legacy use |
| C12 | Executed usage and measured independent multi-candidate comparison showing true candidate, distractors, local failures and ambiguous limitations |

A authors real public-entry tests and independent fixtures. B independently audits equations, legitimate alternatives, positive classes, mapping, precision justification and omissions before accepting exact tests. C implements only named runtime/docs and supplies an actual comparison JSON/PNG/report with candidate order, per-candidate estimates/failure codes, independently known truth, scalar diagnostics and environment/fixture provenance. D inspects actual behavior, pixels and exact passing candidate. Native coverage percentages are advisory; behavior/risk audit and complete valid native measurement remain required. No fabricated product-red or percentage-driven internal-state tests.

[NumPy's opened Fourier reference](https://numpy.org/doc/stable/reference/routines.fft.html) supports the inherited negative-sign transform convention and centered frequency ordering. Candidate/error/ownership/selection boundaries here are explicit project choices.
