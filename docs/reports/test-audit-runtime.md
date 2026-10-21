# Test ownership and verification runtime audit

**Version 1.0.** [Task and authority](../tasks/test-audit-linux-ci.md).

The owner requested a smaller, faster suite using the upstream
[OpenClaw test-audit procedure](https://github.com/openclaw/openclaw/blob/main/.agents/skills/test-audit/SKILL.md),
end-to-end/public-entry proof, Ubuntu-only CI, and a full-suite objective of at
most 600 seconds. The audit starts from PR50,
`8a0e488b66588d7d943dbf52fc48a276dbb14253`.

## Baseline and scope

The saved exact PR50 verification passed 9,074 cases with 29 warnings. Its pytest
phase took 2,085.65 seconds on macOS arm64; the complete 13-phase verification
took 2,121.369 seconds. These are local observations, independent of the owner's
approximately 55-minute CI observation. An intentionally interrupted diagnostic
profile retains timings for completed cases. Its incomplete result and repaired
executable-discovery failures do not establish a second passing baseline.
Final candidate identities, current
timings, exact native coverage integers and review verdicts remain outside
tracked bytes in the task's evidence and PR/conversation.

The global inventory contains 55 test files, 1,557 test declarations and 49,459
test lines. Three read-only owner lanes assessed concrete candidates and keeper
proof. Their detailed declaration ledgers distinguish inspected candidates from
untouched or partially inspected bodies. Numerical fixture derivations were
preserved; the audit does not claim a fresh derivation of every fixture.

## Retired proof and primary owners

The focused bounded batch removes 39 declarations and 305 expanded cases.
Distributed execution adds 13 net policy cases: 18 replace the previous five.
The complete candidate collects 8,782 unique cases, versus 9,074 before the
audit. Its 55 test modules contain 1,523 test declarations and 48,449 lines,
versus 1,557 declarations and 49,459 lines. These module counts exclude helper
and conftest files. Every removal has an exact source identity and keeper
mapping in the [applied deletion ledger](test-audit-deletions.md); complete
execution remains part of the final gate.

| Removed layer | Retained primary proof |
|---|---|
| Redundant reconstruction-result checker tests and 100 repeated integer-conversion observer placements | Actual `reconstruct_volume` numerical, permitted-input, conversion-failure, ownership and policy-preservation tests, plus the primary copied-exception/bypass qualification; independent Decimal expectations remain unchanged |
| NumPy/SciPy observer-bootstrap, callback and fault-targeting qualification replays without a product call | Real estimator FFT/SVD/optimizer failure controls, positive phase fits, off-model Jacobian and caller-policy checks in `test_volume_phase_estimation.py` and `test_observable_volume_phase_estimation.py` |
| Masked-array snapshot checker demonstrations | Actual raw point-bead rejection tests comparing the caller's mask and underlying data before and after calibration |
| Duplicate 2D arithmetic and conventional fabricated-result checker repetitions | Actual phase separation, OTF preparation, illumination/carrier fitting, drift and reconstruction results checked through the same unchanged independent helpers |
| Export inventories and standalone reader startup smoke | Actual file conversion/export and reader/ImagePlus cases; exact series names and shapes remain checked by `test_every_setting_file_raw_and_imageplus[all-absent]` through `assert_report` |
| Duplicate source-free formatting, cache-size rejection and verifier failure/alias tests | Stronger real traceback/exception callers, authentic cache preservation, public receipt command-order/status, exact retained-log and protected-output tests |

The preservation diagnosis retained thirteen initially proposed removals. These
include closed-form Fourier references, subnormal and comparison-budget
boundaries, permitted numerical alternatives, extreme-range and forced-accuracy
premises, copied-exception/bypass admission and legitimate LAPACK controls.
Calling the same general reference from a product test does not independently
verify that reference. The original broader deletion plan remains superseded
in the task evidence; its preparation and correction charges remain counted.

The removed controls often originated in earlier diagnoses of observer defects.
The corrected observers and real-product regression controls remain. The audit
removes redundant executions of support qualification; it supplies no authority
to weaken a numerical expectation, tolerance, representation or rejection rule.

The complete raw-data workflow remains a roadmap dependency. Existing numerical
public APIs are the useful owning boundaries for their current contracts.
Focused tests continue to cover numerical limits and failure paths that a
broader composition could hide through cancellation or an earlier rejection.

## Reuse immutable observations

In `test_verification_evidence_outputs.py`, seven fixture families repeatedly
ran the complete verifier before a test mutated a copied observation. Preserve
all 19 consuming test declarations and their 158 expanded rows. Seven private
copying wrapper fixtures preserve function isolation. Capture the 13
distinct real outcomes once in module-owned isolated repositories, then return
deep copies to each function-scoped consumer. This removes 145 redundant full
verifier invocations. Real product-case repositories retain function scope;
independent outcomes, assertions and error cases remain intact.

A further focused inspection covered 64 declarations and 332 static rows in
measurement export, receipt and output-protection tests. It found no additional
safe snapshot batch: those calls change actual inputs, protected files or
invocation provenance. Output protection already shares its discovery fixture.
Those distinct real-call obligations remain in the full suite; resemblance
between commands is insufficient reason to remove them.

## Reader deadline and platforms

The [reader deadline correction](../contracts/test-audit-reader-deadline-v1.md)
has separate blind author/reviewer ownership. It retains real transport and
child-process behavior while separating the production deadline default from a
short controlled execution. Child closure must be observed before harness
rescue cleanup. A timeout or harness kill is incomplete product evidence.

Ubuntu 24.04 is the only configured CI platform under the owner's explicit
instruction. The complete verification phases, pinned tools, retained artifacts,
local gate, native coverage/report integrity, same-run measurement, wheel import
and audit remain required. Historical platform records retain their original
meaning.

## Validation limits

The [parallel execution contract](../contracts/test-audit-parallel-execution-v1.md)
scopes conventional scheduling if needed after the reductions. Shared reader
resources and immutable fixture captures must stay together. Serial and
distributed policy/resource/coverage qualification precedes a complete run.

All 18 real CLI policy cases passed, including one controlled worker crash with
replacement disabled. The paired resource pilots each passed the same 165
cases once, in 40.36 seconds serially and 32.45 seconds with four workers.
Their normal scheduling proof predates the zero-restart option; the subsequent
policy checks exercise that failure setting. The original pilots' raw coverage
shard retention and complete outer-worker attribution are incomplete. A
separate three-case probe preserves nine native databases and independently
establishes owned body execution in two outer workers plus owned child
processes. That probe does not retroactively repair missing original shards,
and no selected-run coverage is unioned or reused as the full gate.

Use the current exact-candidate receipt and independent preservation review for
passing claims. Preserve selected 100% native executable-line and branch-
destination targets; a low percentage or elapsed-time target cannot silently
remove an obligation. Measure local suite time and complete verification time
separately. Ubuntu CI time requires its own observed run. No throughput estimate
is a measured result, and fewer test names alone do not establish faster or
equivalent proof.
