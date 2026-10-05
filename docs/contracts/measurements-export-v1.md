# MEASUREMENTS-EXPORT-01: same-run native memory evidence

**Version 1.0.** Owner authorization: “Do the WHOLE plan soup to nuts” adopts the remaining repository/specification efficiency rollout, including the original same-run measurement export obligation. This public additive contract preserves every existing MRC conversion expectation and verification-receipt V1–V5 obligation. It approves no scientific algorithm or altered memory limit.

## Public behavior

The existing M25 public conversion test already launches one synthetic native-memory subprocess. Its baseline, peak, native units and byte increment must be exported from that same invocation after its existing assertions succeed. Do not run it again solely to retrieve numbers. Keep all assertions, inputs, product interfaces and the 32 MiB increment limit unchanged.

`python3 scripts/verify.py --measurements-required` opts into mandatory same-run evidence; `make verify` opts in for this repository. Without that flag the additive collector is disabled, preserving existing disposable receipt callers. The helper sets `SIMRECON_MEASUREMENTS_PATH` and `SIMRECON_MEASUREMENTS_RUN_ID` only for its phase subprocesses. The path is the repository-relative `artifacts/verification/measurements.json`; the ID is a fresh UUID string for each invocation. The tests phase must write a report with this invocation's ID; stale reports never satisfy the requirement. Standalone scientific pytest without both environment variables retains its existing behavior and writes no report. A partial pair is an export error, not silent success.

Report JSON: `schema = org.simrecon.measurements`, `version = 1`, `run_id`, and `measurements` containing exactly the required `M25` record. Record fields: `baseline`, `peak`, `units` (`bytes` on macOS, `KiB` on Linux), `increment_bytes`, `limit_bytes = 33554432`. Baseline and peak are nonnegative integers (Booleans are not integers here); peak is at least baseline. Byte increment is `(peak-baseline) * (1 if units == bytes else 1024)`, is nonnegative, and does not exceed the unchanged limit. JSON must be an object; duplicate keys and unexpected measurement IDs fail validation. No owner data, private paths or source content is included.

Receipt gets additive `measurements`: null when not requested or unavailable; otherwise the same validated report fields plus repository-relative `path` and SHA-256. Reconcile exactly with emitted file bytes. A passed opted-in run requires a current valid M25 report produced by its successful tests phase. If tests fail, retain current valid partial measurements as diagnostics but the receipt still fails. On failure before tests, measurements remain null and old data cannot be reported as current. Missing, malformed, mismatched-ID, invalid-unit/arithmetic/limit or unavailable report fails opted-in verification. Keep every old required phase, exit status, check, coverage obligation and before/after identity rule.

The measurements destination and existing leaf symlinks receive the same resolved tracked-file/Git-metadata protection as all other output before execution; reject unsafe paths before writing protected bytes. The writer must create only the approved artifact path supplied by verification and must not overwrite tracked/Git content. Source-free diagnostic rendering remains required for A/B, including warnings and subprocesses.

## Scenarios

| ID | Approved observable decision | Expectation source |
|---|---|---|
| E1 | Opted-in full verification captures the existing single M25 invocation's exact baseline/peak/native units/byte increment/unchanged limit and run identity in the report and receipt; standalone tests and legacy callers retain their prior behavior. | Whole-plan approval; original repo plan §3; unchanged M25 contract |
| E2 | Missing/stale/malformed/invalid or unsafe measurement evidence cannot pass; preserve protected bytes, genuine phase status and applicable current diagnostics. | Existing exact-candidate, output-protection and honest-evidence requirements |
| E3 | Linux KiB and macOS bytes normalize correctly, including legitimate zero/equal-limit cases; invalid type/order/arithmetic/unit/limit and changed report identity are rejected without changing scientific assertions. | Declared arithmetic and existing 32 MiB limit |

Three behavioral scenarios; multiple equivalent values are coverage examples. High-risk route: blind A authors additive public helper cases and narrowly edits the existing M25 export/fixture without reading product implementation; fresh blind B reviews changed tests plus shared dependencies, freezes checkpoint; C owns only `scripts/verify.py`; D independently reviews the exact passing full candidate. Coordinator may add Make's opt-in flag and synchronize public receipt documentation before tests freeze. Existing 73 receipt cases and all scientific assertions remain required. Later tests are supplemental, not recreated test-first evidence for unchanged code.
