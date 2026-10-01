# MRC-CONVERSION-01 coverage amendment — proposal 2

**Version 1.0**. Approval pending. Approval and accounting remain solely in [architecture intake Current state](architecture-intake.md#current-state).

## Owner read-back and unchanged contract

Approve an explicit **44-scenario exception** for the same end-to-end task: keep approved M01–M26 unchanged and add the 18 separately counted contexts M27–M44 below. These provide evidence for the existing [public contract](../contracts/mrc-conversion-v1.md), not new scientific behavior.

Authorize **one new bounded fresh-root A/B review window of at most two rounds** for these evidenced coverage/test corrections. The original window remains recorded as 2/2 used and accepted at `0db9ef102f7c3328b7b4aba871e4ddbf3e9cc8e9`; it is not erased or replenished. Changed tests/fixtures get a revised checkpoint. Both new roles remain blind to implementation, history/conversations, implementation-bearing status, coverage/source mappings and existing lesson entries. Their packets contain only accepted public contracts/scenarios, permitted project context and A's tests/evidence for B.

Retain the original **12 elapsed working-hour execution cap**, including all prior spending, setup, roles, checks and local conservation. Pause only for owner-response waiting. Retain **one C repair across the whole task after initial C**; none has been used. Use that existing repair for contract-preserving simplification of host-dependent encoding and any evidenced product defects from accepted tests. No new C repair or time allowance is requested. Scope, worktree, dependencies, scientific exclusions and no push/PR/merge/release terms remain binding.

All settled requirements remain binding: acquisition config supplies counts/order; user overrides and provenance; exact pixel words; bounded block/opaque-copy memory; fresh output files; independently authored code; owner data local and outside Git/CI; functional Python/NumPy; direct-micrometre profile; unknown flattened standard-header axial scale; genuine embedded HDF5 metadata; initial pinned mrcfile compatibility and ImageJ deferred.

## Additional public scenarios

Each row is one distinct input context. Multiple assertions through the Python/CLI boundary within a row do not create additional scenarios. Do not hide extra distinct inputs in parameter matrices. These are public specifications; blind packets must not contain the coordinator's implementation/coverage mapping.

| ID | Input/context and observable outcome | Expectation source |
|---|---|---|
| M27 | CLI conversion omits required `--config`. Exit 2 with error JSON, code `config_invalid`, no successful stdout or source-bearing traceback. This specifies the existing-vocabulary usage error for this context; exact prose remains noncontractual. | Explicit config and CLI usage/domain-error boundary |
| M28 | CLI config uses the nonstandard JSON token `NaN`. Reject `config_invalid`, no successful output/traceback. | Finite acyclic JSON config boundary |
| M29 | CLI config is finite JSON array `[]`, rather than an object. Reject `config_invalid`, no successful output. | Config mapping/object boundary |
| M30 | Otherwise valid configuration has one unknown top-level field `extra`. Harmonization rejects `config_invalid`, without input/config mutation. | Unknown fields are errors |
| M31 | Otherwise valid configuration supplies `plane_axes` as scalar string `phase`. Reject `config_invalid`, without mutation. | Explicit axis-list/shape contract |
| M32 | Zero actual extension with an unknown extension-policy string. Reject `config_invalid`. | Policy vocabulary none/opaque |
| M33 | Zero actual extension with explicit opaque policy. Reject `config_invalid`; absence requires none. | Actual extension length governs policy |
| M34 | Otherwise valid configuration has one unknown field inside overrides. Reject `config_invalid`. | Override vocabulary sampling_um/wavelengths_nm |
| M35 | Sampling overrides contain unknown axis key q. Reject `config_invalid`. | Sampling axes x/y/z |
| M36 | Wavelength overrides are an array, rather than a channel-index mapping. Reject `config_invalid`. | Sparse channel-index mapping |
| M37 | Explicit X sampling override is zero. Reject `config_invalid`; do not fall back to the file value. | Finite positive explicit sampling and override priority |
| M38 | Wavelength override key is nonnumeric string channelA, with an ordinary positive value. Reject `config_invalid`. No new leading-zero or Unicode-digit restriction is introduced. | Channel-index key contract |
| M39 | Unknown spatial-field convention plus complete positive canonical X/Y overrides for a 2D source. Harmonization/conversion succeed with those overrides, exact pixels, original bytes, precise metadata and provenance; no guessed file units. | Explicit canonical override resolution for unknown profiles |
| M40 | Positive finite X override 1e-60 micrometres with NX=5. Required cell length 5e-56 angstroms rounds to zero in float32. Write rejects `header_unrepresentable`, with no successful report. | Positive finite float32 header representability |
| M41 | Valid one-pixel mode-6 source with 2,147,483,647 opaque-extension bytes, exact total source length and opaque policy. Self-contained HDF5 plus padding exceeds signed-32-bit NSYMBT. Write rejects `header_unrepresentable`, no successful report. Build a genuine sparse source with bounded fixture memory; no fabricated descriptor/private helper. | Signed-32-bit NSYMBT and three HDF5 dataset contents |
| M42 | Real source payload shortens while selected read is active, after initial identity validation. Reject `source_changed`; no DataBlock. | Existing source-consistency requirement; separately counted M21 timing refinement |
| M43 | Real opaque source extension shortens during conversion's copy, after initial identity validation. Reject `source_changed`; no WriteReport. A partial new output may remain. | Existing source-consistency/bounded-copy requirement; M21 timing refinement |
| M44 | Real source identity changes after the last pixel read and before write completion returns. Reject `source_changed`; no WriteReport. | Explicit completion-time source consistency; M21 timing refinement |

M42–M44 use ordinary Path/integer/dictionary public arguments. Test-side coordination may observe filesystem operations and modify a real synthetic source. Do not replace private product functions, pass arbitrary caller object protocols or use sleeps to win a race. Preserve diagnostic types/messages/frame locations/status without implementation source for blind probes.

M41 is separate from the unchanged M25 memory context. It may need approximately 2 GiB temporary metadata disk space while the sparse input itself uses bounded physical storage. Available storage is an environment prerequisite, not permission to skip or weaken the test. Native resident-memory acceptance and platform units remain governed by unchanged M25.

## Host encoding and verification

Both source byte orders are approved and already have portable tests. Linux/macOS are the configured platform scope. No native big-endian-host run has been established. Diagnose the uncovered host-specific output-encoding path through the allocated C repair: prefer simple explicit word encoding that preserves exact bits on configured platforms and removes unnecessary host-dependent control flow. Do not fake NumPy host constants, add private-helper tests or exclude owned code to manufacture coverage. No new native-host support claim is made.

A's test expectations derive solely from approved public requirements, independent byte fixtures and coordinate/IEEE-word/storage invariants. New tests may pass initially; no fabricated product-red evidence or mutation testing. Actual failure classifications and native counts stay in coordinator/C evidence, outside blind inputs.

Completion retains the original gate: fresh B accepts the revised checkpoint; allocated fresh-root C repair passes exact-candidate `make verify UV=/Users/davidhoffman/.local/bin/uv`, 100% native statements and branches globally/per package including subprocess/unimported owned files; repeat owner raw/processed conservation for changed runtime; independent memory/reader evidence; fresh D accepts behavior/evidence/simplicity. Record final candidate hash/results outside its tracked tree. No dependency/check/workflow/delivery-rule weakening or remote submission.
