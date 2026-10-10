# Phase 1: baseline manifest and dependency closure

**Version 1.0.** Observed October 10, 2026. [Task/authority](../tasks/scientific-phase1-intake.md), [acquisition/settings](scientific-phase1-acquisition.md), [decision register](scientific-phase1-decisions.md), [ordered intake packets](scientific-phase1-packets.md).

Reconciliation is complete as a documentation deliverable. Full phase-1 exit is not: later slices still lack integrated scientific prerequisites and selected target contracts/settings. This baseline contains conversion and known-phase 2D separation, with calibration contracts/fixtures; it has no OTF preparation, empirical bead calibration or reconstruction runtime.

## Exact execution baseline

| Identity | Observed value |
|---|---|
| Parent/new-stack PR | [#22, roadmap amendment](https://github.com/david-hoffman/simrecon/pull/22), open/unmerged |
| Parent branch/head | `codex/scientific-migration-roadmap` / `9022cfd617f289bc66eeeb9357a23af0926c4309` |
| Parent tree | `bb5db01319255ca526d7523b87d821a444282f09` |
| Parent base / integrated main | `a44e9d0c67403d5a001340b65ba04ea2f559256a` |
| Phase-1 branch / intended PR base | `codex/phase1-scientific-intake` / `codex/scientific-migration-roadmap` |
| Initial worktree | Clean detached checkout at exact parent commit; then dedicated branch created. One task per worktree. |
| Reference evidence | Ignored source text; exact hashes/locators in acquisition matrix. No reference execution. |
| Final phase-1 candidate/evidence | Outside tracked bytes at the task's single Current state; fresh exact-candidate gate required. |

The parent differs from main only in the roadmap/task/lesson documentation. Public runtime and installed checks are main's integrated ones. Git tree/export inspection distinguishes three usable foundations:

- [MRC conversion](../contracts/mrc-conversion-v1.md), merged [#2](https://github.com/david-hoffman/simrecon/pull/2): `inspect`, `read`, `harmonize`, `write`, metadata/layout records and command-line entry. MRC is the microscopy volume format. Explicit acquisition configuration preserves pixels/metadata; it supplies no scientific correction or reconstruction.
- [Explicit-phase 2D separation](../contracts/known-phase-separation-v2.md), merged [#5](https://github.com/david-hoffman/simrecon/pull/5): `separate_phases`, `PhaseComponents`, first-harmonic `dc`/`c1` fit from supplied actual phases. It estimates no unknown phases/carriers and provides no five-order volume separation.
- [2D intensity-PSF/OTF contract](../contracts/otf-calibration-v1.md), merged [#6](https://github.com/david-hoffman/simrecon/pull/6): six [mathematical intake examples](../references/scientific/otf-calibration-fixture-notes.md) and [JSON](../references/scientific/otf-calibration-fixtures-v1.json), plus optical illustration. PSF means point spread function; OTF means optical transfer function. `prepare_otf`/`Otf2D` are absent from this runtime. Intake examples are not an A/B-reviewed executable checkpoint.

The asymmetric fixture is mathematically consistent: masses at `(oy,ox)`, `(oy+1,ox)`, `(oy,ox+1)` match the negative-exponential formula. “Above” follows the integrated notes' upward-display convention. Open #7 clarifies the coordinates; that prose is not integrated. Carry explicit coordinates into later independent expectations (I4), without inventing a defect or changing fixtures.

## Installed verification policy

[AGENTS](../../AGENTS.md), [PROJECT](../PROJECT.md), `Makefile`, `pyproject.toml`, `scripts/verify.py` and `.github/workflows/verify.yml` were inspected in this baseline. The default submission gate is full local verification of the exact clean candidate. `make verify` runs all thirteen phases: locked sync; coverage cleanup; lint; format; types; tests; coverage combine/JSON/HTML/report; wheel; isolated wheel import; locked vulnerability audit. It requires same-run measurement export. Empty test discovery, skips and expected/unexpected passes are rejected by installed test policy.

Coverage.py's native statement and branch metrics require 100% globally/per owned package, including `src/simrecon`, `scripts`, never-imported owned files and relevant subprocesses. Make/YAML, external dependency internals, ignored reference code and model behavior have no owned-Python metric claim. Configured continuous integration (CI) repeats the complete gate on Ubuntu 24.04 and macOS 15. Conditional CI-authoritative mode is not enabled. Existing numeric test contracts, including M25's memory limit, stay unchanged; human task/review/scenario caps are not set.

Open #9's advisory coverage proposal is absent here. The owner's maintenance-only resolution of old-stack installed gates does not adopt that policy on this new stack. Any later baseline change needs applicable evidence under the policy actually governing that authorized work; no policy transplant or weaker gate is authorized here.

## Live old stack: read-only manifest

Fresh GitHub reads verified these exact heads/base refs against main and #22. All fourteen remain open/unmerged. An archived bundle was read in a separate local evidence object store; no old candidate was imported into this execution baseline. Branch ancestry and scientific dependency are different: integrating a tip as-is would also bring intervening policy and unrelated components.

| PR | Exact head | Observed base branch / exact base commit |
|---|---|---|
| [#7](https://github.com/david-hoffman/simrecon/pull/7) | `aa39de2daec1871adcfe945cd0e6b87ffe5d5745` | `main` / `a44e9d0c67403d5a001340b65ba04ea2f559256a` |
| [#8](https://github.com/david-hoffman/simrecon/pull/8) | `2da42d1234b200730d7e77970ad8f929592499ab` | `codex/otf-calibration` / `aa39de2daec1871adcfe945cd0e6b87ffe5d5745` |
| [#9](https://github.com/david-hoffman/simrecon/pull/9) | `c47788f43261dc6bc8086b3f32a6065407a9fcc0` | `codex/known-parameter-reconstruction` / `2da42d1234b200730d7e77970ad8f929592499ab` |
| [#11](https://github.com/david-hoffman/simrecon/pull/11) | `fa6efc4f448401ab72fc55e23067c21c184a01a0` | `codex/asd-coverage-policy` / `c47788f43261dc6bc8086b3f32a6065407a9fcc0` |
| [#12](https://github.com/david-hoffman/simrecon/pull/12) | `5a9098c094e398ec6dcbca645b0b195ae86304b2` | `codex/illumination-estimation` / `fa6efc4f448401ab72fc55e23067c21c184a01a0` |
| [#13](https://github.com/david-hoffman/simrecon/pull/13) | `9c39cdb5c6fe658110469bd2099cb4d274501e3d` | `codex/carrier-search` / `5a9098c094e398ec6dcbca645b0b195ae86304b2` |
| [#14](https://github.com/david-hoffman/simrecon/pull/14) | `e249f738343590a287e9c4ef384acb13b7116667` | `codex/carrier-selection` / `9c39cdb5c6fe658110469bd2099cb4d274501e3d` |
| [#15](https://github.com/david-hoffman/simrecon/pull/15) | `5b33c3329f23a85afcc66b5a6a12b36b7737f049` | `codex/translation-diagnostics` / `e249f738343590a287e9c4ef384acb13b7116667` |
| [#16](https://github.com/david-hoffman/simrecon/pull/16) | `ab2b3fbd91cee76b524e3d5321da9670e1156e4c` | `codex/known-drift-preparation` / `5b33c3329f23a85afcc66b5a6a12b36b7737f049` |
| [#17](https://github.com/david-hoffman/simrecon/pull/17) | `5ab7f75410292cfcee9ad75ced13eaa6489ab376` | `codex/volume-phase-separation` / `ab2b3fbd91cee76b524e3d5321da9670e1156e4c` |
| [#18](https://github.com/david-hoffman/simrecon/pull/18) | `76c7400d994e3e03ba23fa1815849474ad6f54a3` | `codex/volume-otf-preparation` / `5ab7f75410292cfcee9ad75ced13eaa6489ab376` |
| [#19](https://github.com/david-hoffman/simrecon/pull/19) | `e58ddd7656acc4dbe3da50c88419c4d1d40bb6a4` | `codex/volume-order-transfers` / `76c7400d994e3e03ba23fa1815849474ad6f54a3` |
| [#20](https://github.com/david-hoffman/simrecon/pull/20) | `db3c5a77bbb87d0566e6cfbc57e1602a095090ac` | `codex/volume-recombination` / `e58ddd7656acc4dbe3da50c88419c4d1d40bb6a4` |
| [#21](https://github.com/david-hoffman/simrecon/pull/21) | `d3ba7639ebec99dd67026332771fad99cf452d51` | `codex/volume-order-gain` / `db3c5a77bbb87d0566e6cfbc57e1602a095090ac` |

## Capability and genuine-gap matrix

Candidate contracts were read at exact old-stack tip `d3ba7639ebec99dd67026332771fad99cf452d51`, tree `88e46436701c5b634ec2fb9aa49a3596a2e0a934`; fingerprints remain in local evidence. Paths below are within that candidate's `docs/contracts/`, not files installed here.

| Capability / public expectation source | Execution baseline contains it? | Candidate contribution / remaining boundary |
|---|---|---|
| Conversion and explicit first-harmonic 2D separation | Yes, runtime and contracts. | Usable narrow foundations; no raw camera interpretation, calibration or parameter inference. |
| Detection-PSF 2D OTF, `otf-calibration-v1.md` | Contract/intake fixtures only. | #7 runtime; corrected supplied nonnegative PSF and supplied origin. No empirical SIM bead calibration. |
| Known-parameter 2D reconstruction, `known-parameter-reconstruction-v1.md` | No. | #8 includes fractional carriers with bilinear spectral interpolation; detector-matched calibration; documented approximation. Not a 3D interpolation contract. |
| Known-carrier phase/modulation and candidate scan/selection, `illumination-estimation-v1.md`, `carrier-scan-v1.md`, `carrier-selection-v1.md` | No. | #11–13 first-harmonic integer 2D model, supplied relative phase steps and caller limits. Continuous 3D carrier/unknown-step estimation is a gap. |
| Reference translation and known drift, `translation-estimation-v1.md`, `integer-drift-correction-v1.md` | No. | #14–15 periodic equal-intensity reference and supplied integer specimen drift/phase correction. Differing raw phases and fractional/axial motion are gaps. |
| Five-order volume separation, `volume-phase-separation-v1.md` | No. | #16 known phases, zero plus ±1/±2 complex orders. Empirical calibration preprocessing/order gauge remains separate. |
| Supplied 3D intensity-PSF OTF, `volume-otf-preparation-v1.md` | No. | #17 corrected supplied PSF/origin; not raw phase-resolved SIM calibration. |
| Effective transfers from axial profiles, `volume-order-transfers-v1.md` | No. | #18 supplied detection PSF/profiles, with `g0=1`; cannot recover empirical unknown axial order response. |
| Known volume reconstruction/gain, `volume-recombination-v1.md`, `volume-order-gain-v1.md` | No. | #19–20 finite periodic model, integer lateral carriers, native axial sampling, detector-matched grids; relative complex gain fit for order 1/2. |
| Viewing export, `imagej-export-v1.md` | No. | #21 acquisition viewing/preserved illumination settings; not reconstruction-result persistence. |
| Raw layout/correction provenance and empirical 3D bead calibration | No complete contract or runtime. | Phases 2–3, packets R1/R2/C0–C5 are genuine gaps. |
| Independent complex OTF grids, full 3D estimation/motion, selected-mode output and composition | No complete contract or runtime. | Phases 4–7 are gaps, even if the whole old scientific stack were integrated. |
| Full raw specimen+bead simulation, owner-data parity | No. | Phases 8–9 require their own independent acceptance/settings/provenance; small fixtures cannot substitute. |

## Concrete dependency closure before execution

| Upcoming slice | Reusable foundations / proposed scientific closure | Present here / blocked decisions |
|---|---|---|
| Phase 2 R1 explicit raw layout | Integrated conversion plus selected target layout/units contract. | Conversion present; O1/O2, S1/S2 pending. No old numerical PR is inherently required to draft it. |
| Phase 2 R2 corrections | Completed integrated R1 and selected camera/background/correction contract. | R1/correction behavior absent; O3/O4, S4 pending. |
| Phase 3 C0–C5 empirical bead route | Completed R1/R2; selected phase/order separator and independently reviewed bead method. #16 is a candidate separator; #7/#17 serve distinct detection-PSF operations only where needed. | Only 2D foundation contract/fixtures present; I1–I3 and S2–S8/O2–O5 pending. #18 supplied profiles do not close the empirical gap. |
| Phase 4 G1 independent grids | Integrated empirical transfer contract/runtime plus selected reconstruction consumer; #19/#20 are limited candidate consumers. | All absent; S9 and target grid facts pending. Their detector-matched restriction needs explicit new meaning before use. |
| Phase 5 estimation/drift | Integrated R1/R2, empirical responses and G1 plus chosen reconstruction/estimation foundations. #11–15/#20 can supply their narrow diagnostics, if separately reusable. | All open foundations absent; S10/S11 and nuisance/correction provenance pending. Old 2D helpers are not automatically valid 3D estimators. |
| Phase 6 reconstruction/output | Integrated phases 3–5, selected-mode reconstruction contract and needed adapters. Candidate #16–20 form a known-parameter volume path; #21 optional for acquisition viewing only. | None integrated; S12/S13/O6 and I5 pending. No automatic inclusion of #9 or all ancestry. |
| Phase 7 public raw workflow | Completed integrated phases 2–6, independent complete small cases and diagnostics/provenance. | Absent; S14 and component entry decisions pending. |
| Phase 8 full simulation | Phase-7 public workflow plus separately contracted independent forward generator/acceptance; both raw acquisitions and hidden truth. | Absent; S14, convergence/physical sampling/resource plan pending. Trial optics are not instrument facts. |
| Phase 9 owner-reference comparison | Successful phase 8, owner raw pairs/configurations/outputs, comparison contract. | Absent; O7 and S15 pending. No reference program execution. |

For owner integration consideration, first name the scientific subset and exact commits/tests/fixtures it needs; separate unavoidable Git ancestry from actual API dependencies, inspect original accepted evidence and changed-base effects, and demonstrate compatibility with the governing gate. Possible later choices are owner-authorized integration of an accepted closure or a separately authorized independent port/reimplementation; neither is authorized by this task. Leaving candidates open and continuing source/contract planning is useful now. Do not silently merge/cherry-pick or adopt a policy to make reuse easier.

## What evidence was actually inspected

| Evidence class | Inspected facts | Limit / reuse consequence |
|---|---|---|
| Fresh baseline/live stack | Git commit/tree/clean status, exports, contract/fixture paths, live PR heads/base refs and merged #2/#5/#6; exact public candidate contracts from archived Git objects. | Open functionality remains unintegrated; source/contract reading is not acceptance. |
| Predecessor roadmap | Exact accepted documentation review and full receipt: thirteen successful phases, `9022cfd…`/tree `bb5db…`, 697/697 statements and 246/246 branches. Receipt SHA-256 `2aa76ce29b76f487f1afcaad29a75f330533de01f212257dc682491f4c750494`. | Review/receipt inspected, not every predecessor artifact independently re-audited. Changed phase-1 candidate needs fresh full verification/review. |
| Old maintenance | Canonical state, exact final-local-evidence manifest and applicable retained receipt/review records inspected narrowly; #21 bounded correction acceptance is scoped to its diagnostic test. | Old scientific A/B/C/D verdicts and complete original platform/build evidence were not all re-audited. I3 remains pending; no blanket scientific acceptance inferred. |
| Old gate mismatch | Retained #21 report: 2304/2353 statements, 724/762 branches; manifests for #12–21 also show incomplete native coverage under their installed advisory policy. | Those reported full-gate passes do not establish this baseline's required 100%. Reading old contracts that reference advisory coverage adopts no policy. |
| New phase-1 checks | Pointer prepared in task record; exact candidate receipts, independent review and publication readback recorded outside tracked bytes. | Local evidence is separate from configured platform CI; no new scientific correctness or parity result. |

Historical attempt/spending records remain in their original task/evidence files. New accounting never resets them or counts their cumulative children again. Confidence is high in integrated-versus-open boundaries and the empirical/grid gaps. Target behavior and reuse applicability remain uncertain until the listed provenance, scientific decisions and integration evidence close.
