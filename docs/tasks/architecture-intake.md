# ARCHITECTURE-INTAKE: select the pristine library design

**Version 1.0** Git versions revisions. Architecture and product contracts remain unapproved.

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

- Status: conversion contract proposal 1 is ready for owner read-back. [Public/config/output contract](../contracts/mrc-conversion-v1.md) and [bounded task/scenarios](mrc-conversion.md) make the exact scope reviewable; no product/architecture approval yet.
- Approval: owner accepted starting conversion in a fresh chat, supplied local raw/processed files, confirmed raw 2D/no Z/single channel and three phases per orientation, and explicitly required acquisition information from config. Unlimited intake remains authorized. These answers do not approve the draft's format/schema/API/budget choices or the separate placeholder.
- Candidate: documentation proposal based on `4fc8ea2d51d3ed58536b034954a0596a1b9d0dc2`; final proposal commit/hash and check result will be recorded in this conversation outside the tracked tree.
- Reviewed checkpoint and role results: none; no A/B/C/D session started.
- Checks: [local read-only sample observations](../architecture/owner-mrc-observations.md) establish storage facts and exact payload lengths; inputs unchanged. Documentation receives `git diff --check`. Handed-off infrastructure verification covers only the clean baseline; no conversion implementation/compatibility or reconstruction claim.
- Blockers: actual owner approval of identified proposal, including direct-micrometre profile, labeled unknown axial scale, initial mrcfile reader boundary with ImageJ deferred, explicit 26-case exception, pinned runtime/development dependency setup and 12-hour execution cap. Separate placeholder read-back/budget remains pending.
- Next action: owner read-back; after actual approval, record the accepted revision/allowance, perform permitted dependency setup and prepare narrow fresh-root A/B packets from the public contract. Subsequent C/D use reviewed checkpoints. No implementation in this intake chat; no forked reviews; doctor proposal outside scope.
- Metrics: conversion scenarios=26 proposed / 0 approved; A/B rounds=0/2; C repairs=0/1 after initial C; intake allowance=unlimited, spending totals unavailable; execution cap=12 hours proposed / 0 used / approval pending. Placeholder scenarios=1 requested, read-back/budget pending; A/B rounds=0/2; C repairs=0/1.
