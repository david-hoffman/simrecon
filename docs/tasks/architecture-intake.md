# ARCHITECTURE-INTAKE: select the pristine library design

**Version 1.0** Git versions revisions. Approval and execution accounting live in the single Current state below; the preceding interview/proposal records are historical.

## Intake scope

- Baseline: documentation commit `0e04094d3eaf9da05a9b792f12136e71dc9474ae` on `codex/architecture-intake`, based on main `28da51d8617b9c454a1580df80759bf3cdcd3ff6`.
- Inputs: [project](../PROJECT.md), [scientific context](../SCIENTIFIC-CONTEXT.md), [roadmap](../MIGRATION-ROADMAP.md), narrow read-only legacy study, applicable primary documentation, and the owner's architecture interview.
- Outcome: compare two or three practical designs; propose data/public-interface boundaries, stack, components, operation, and verification; obtain actual owner approval before implementation.
- Permitted work: interview, investigation, architecture records, and correction of stale architecture-approval claims. No scientific runtime, executable scientific tests, legacy execution, or doctor-proposal adoption.
- Budget: owner answered "unlimited" for this intake on September 30, 2026. No time ceiling. Scientific implementation and slice execution need separate approval and allowance. Historical setup spending and repairs remain separate.
- Commit identity: new commits must use `codex` for author and committer. No change to authenticated GitHub identity is implied.
- No product scenarios are approved by this document. It does not constitute the first MRC task contract or an A/B packet.
- Subsequent exception: the owner explicitly requests the reconstruction stage in code as a placeholder during review. [RECONSTRUCTION-PLACEHOLDER](reconstruction-placeholder.md) records that narrow requested scaffold and the read-back behavior; its execution budget is pending. It is not the MRC task or scientific implementation approval.

## Owner requirements from the interview

1. CPU-first; small public API; image, metadata, and algorithm-parameter intake.
2. Functions with explicit inputs/outputs; minimize statefulness. Input/output adapters harmonize sources into a shared internal representation.
3. First requested slice reads, inspects, harmonizes, and writes legacy MRC image data. Reconstruction receives separate approval.
4. Python library and command-line interface both ship in that first slice.
5. Explicit user metadata automatically overrides file values, with a record of the change.
6. New output uses modern documented MRC, in one self-contained file with a documented extended header.
7. Study legacy algorithms, write new code independently, and preserve the distinction between citation-only conversions and full-paper extraction.
8. Example scale is `2048 × 2048 × 40 × 3 × 5 × 5 × 100`, with ImageJ as a downstream viewer and RAM unspecified. Interpret the counts provisionally as X/Y/Z/orientation/phase/channel/time, without hard dimension limits.
9. Retain OTF calibration as a first-class category in the intake plan. Calibration file intake/output and generating or estimating calibration are distinct scopes.
10. Inspection can show unknown fields; harmonization requires an explicit acquisition profile/override when ordering or extended-header schema is unknown.
11. Fallback 3D processing unit: one channel at one time point, its complete Z acquisition across required orientations/phases. Intake/output may use smaller blocks.
12. ImageJ should ultimately interpret five-dimensional X/Y/Z/channel/time data correctly. The owner accepts current reader support in the first MRC slice, with limitations stated and full metadata preserved, followed by a better adapter/integration later.

These are owner-supplied requirements, not acceptance of a concrete architecture. Numerical conventions, format coverage, error behavior, and test scenarios still need approved contracts.

## Design comparison

| Practical design | Useful properties | Costs and limits | Assessment for this request |
|---|---|---|---|
| Functional Python + NumPy/SciPy + explicit metadata records + selected block I/O | Direct array interoperability; few dependencies; pure operation boundaries; straightforward CLI reuse; file access can be bounded without a scheduler. | We must specify axis/unit validation and ownership. Block I/O does not remove whole-volume Fourier memory needs. Performance is unmeasured. | Recommended starting architecture. Size is handled at the file boundary and by explicit processing units, with scientific memory contracts later. |
| xarray data model, with Dask for lazy/scheduled execution | Named dimensions/coordinates are built in; lazy arrays can describe data larger than memory. | Adds data-model and scheduler behavior to the core. Automatic coordinate alignment must be controlled in scientific arithmetic. Global transforms still need suitable chunk/algorithm choices. | Practical alternative if labeled manipulation and distributed workflows become primary requirements; an optional bridge can be added after core contracts. |
| Independently written compiled core, with a functional Python binding | Direct control of native kernels, buffer ownership, and threading; same external functional API is possible. | Adds extension builds and platform-specific measurement/packaging. Speed advantage has not been demonstrated; file/metadata semantics still need exactly the same resolution. | Defer unless profiling or a defined latency/memory target justifies it. Do not adopt the legacy runtime. |

The recommendation is engineering judgment, not a performance benchmark. [NumPy array representation](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html), [xarray dimensions/coordinates](https://docs.xarray.dev/en/stable/user-guide/data-structures.html), [xarray alignment semantics](https://docs.xarray.dev/en/stable/user-guide/computation.html#automatic-alignment), [xarray/Dask execution](https://docs.xarray.dev/en/stable/user-guide/dask.html), and [native Python extension builds](https://pybind11.readthedocs.io/en/stable/compiling.html) establish the capabilities being compared. The [concrete proposal in PROJECT.md](../PROJECT.md#proposed-library-architecture--approval-pending) is the architecture record for owner review.

## Proposed delivery boundaries

After architecture approval, define public format/model contracts first, then approve bounded end-to-end intake/output slices, each with at most five honestly counted scenarios unless the owner approves an exception. Keep image files and OTF calibration semantics distinct; include Python/CLI parity, independent expected metadata/pixels, selected reads, and modern single-file output in the relevant contracts. This record does not approve a combined oversized slice. Scientific reconstruction, OTF generation/preparation, and estimator algorithms remain later contracts. Full-paper extraction stays unfinished.

Fixtures must establish the supported legacy dialect independently of a successful new-reader round trip. No owner legacy example was found in the checked source tree. Representative image and OTF files with known acquisition interpretation, or documented independently constructed format fixtures, are prerequisites for claiming that compatibility. The exact fixture route is a task-intake decision, not permission to bypass it or treat old outputs as scientific truth.

## Evidence

[Legacy MRC observations](../architecture/legacy-mrc-observations.md) identify image header metadata, separate parameter inputs, acquisition layout choices, competing extended-header meanings, and distinct frequency-domain calibration semantics. No sample image or verified legacy codec was established. Installed dependencies are evidence of scaffolding, not architecture selection.

## Current state

- Status: owner approved complete MRC-CONVERSION-01 Proposal 1; execution started October 1, 2026 at 14:48:49 UTC (07:48:49 PDT). Coordinator performs authorized dependency setup before fresh-root A/B/C/D.
- Approval: actual owner response, “Approved!”, in the fresh coordinator chat on October 1, 2026, accepts proposal revision `a3808d545659556a024b70dca2dae1dc6238a32b`: functional Python/NumPy and exact public/config/output contract; direct-micrometre profile and unknown standard-header axial scale; genuine embedded HDF5 metadata; initial independent mrcfile compatibility with ImageJ deferred; 26-scenario exception; runtime h5py==3.16.0 / development mrcfile==1.5.4 setup; 12-hour execution cap, two A/B rounds and one C repair after initial C. Settled explicit acquisition config, override provenance, exact pixels, bounded memory, no overwrite, independent code and local owner data remain binding. Separate reconstruction placeholder, deferred features, push/PR/merge/release remain outside this approval. Unlimited intake remains authorized.
- Candidate: accepted test/fixture checkpoint `0db9ef102f7c3328b7b4aba871e4ddbf3e9cc8e9`, atop verified dependency baseline `f1668cfb6bd7e19103cb138d674ae278bbc28f37`; coordinator records B acceptance before fresh initial C. All new commits use codex <codex@openai.com> as author and committer.
- Reviewed checkpoint and role results: B round 2 accepted all 26 public cases at `0db9ef1`; [B acceptance](../../artifacts/mrc-conversion/roles/b-round2-report.txt). Round 1's four test defects were corrected by fresh A; [round-2 evidence](../../artifacts/mrc-conversion/roles/a-round2-evidence.md). Initial A/B window is closed (2/2). No blind-role source exposure. Each A/B used a new Codex 0.159.2 / gpt-6.1-sol root session with memories/delegation disabled. Fresh initial C is next; D unstarted.
- Checks: setup baseline passes canonical verification (macOS arm64 / CPython 3.13.12 / uv 0.12.19; 10 infrastructure tests, 30/30 statements, 4/4 branches, lint/format/type/wheel/audit). Revised A files pass Ruff/Pyright/fixture smoke; focused run has 26 expected missing-public-export errors. B verified independent coordinate/scaling/header/container/provenance/CLI oracles. Converter runtime coverage, behavior, memory and interoperability are still unexecuted/unknown.
- Blockers: none for initial C. Separate placeholder read-back/budget remains pending and outside this task.
- Next action: fresh-root C independently implements only approved product scope against the accepted tests and passes exact-candidate canonical verification. Coordinator then collects local owner-file conservation/native-memory evidence; fresh D reviews passing behavior/evidence/simplicity. Changed tests require an evidenced authorized reopening and fresh A/B; C cannot modify them.
- Metrics: conversion scenarios=26 approved; A/B rounds=2/2, accepted and window closed (first nonaccepted, second accepted); C repairs=0/1 after initial C; intake allowance=unlimited, prior spending totals unavailable; execution cap=12 elapsed working hours, start=2026-10-01T14:48:49Z, spent=3138 s, remaining=40062 s at this checkpoint, no owner-wait pause; complete token/dollar totals unavailable (partial native role counters in ignored event evidence). Placeholder scenarios=1 requested, read-back/budget pending; A/B rounds=0/2; C repairs=0/1.
