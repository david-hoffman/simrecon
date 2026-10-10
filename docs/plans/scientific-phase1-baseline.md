# Phase 1: baseline manifest and dependency closure

**Version 1.0.** Observed October 10, 2026. [Task/authority](../tasks/scientific-phase1-intake.md), [acquisition/settings](scientific-phase1-acquisition.md), [decision register](scientific-phase1-decisions.md), [ordered intake packets](scientific-phase1-packets.md).

The owner selected PR #21 → corrected roadmap PR #22 → this phase-1 continuation. Its execution baseline contains all inherited completed component implementations, contracts, tests and fixtures, although the PRs remain unmerged into main. Their narrow scientific limits remain. Reconciliation documents do not settle the target acquisition or complete the new scientific contracts required for full phase-1 exit.

## Exact execution baseline

| Identity | Observed value |
|---|---|
| Parent/new continuation PR | [#22, roadmap amendment](https://github.com/david-hoffman/simrecon/pull/22), directly above PR #21 |
| Parent branch/head | `codex/scientific-migration-roadmap` / publication confirmation pending; prepared candidate `01db3d08a7c32b1dca5f2b8160a6e99ab24365d2` |
| Parent tree | Publication confirmation pending; exact identity will be recorded before phase-1 verification. |
| Inherited PR #21 head/tree | `d3ba7639ebec99dd67026332771fad99cf452d51` / `88e46436701c5b634ec2fb9aa49a3596a2e0a934` |
| Merged main history | `a44e9d0c67403d5a001340b65ba04ea2f559256a`; distinct from this stacked execution baseline |
| Phase-1 branch / PR base | `codex/phase1-scientific-intake` / `codex/scientific-migration-roadmap` |
| Migration | Preserve the incomplete main-based draft/evidence checkpoint, then replay only phase-1 work after corrected #22 publication confirmation. Old PR heads/bases and owner checkouts stay intact. |
| Final phase-1 candidate/evidence | Outside tracked bytes at the task's single Current state; fresh exact-candidate gate required. |

The owner's correction supersedes the initial main-based prompt and its absent-component/strict-percentage assumptions. The wrong-baseline draft and earlier measurements remain historical evidence, not the execution baseline or a reset of charges. PR #21's runtime, tests/fixtures, dependency lock and installed checks are inherited; the roadmap adds documentation only. No component transplant or owner merge is required to make those existing components present.

Merged history includes [MRC conversion #2](https://github.com/david-hoffman/simrecon/pull/2), [explicit-phase 2D separation #5](https://github.com/david-hoffman/simrecon/pull/5), and [2D PSF/OTF foundations #6](https://github.com/david-hoffman/simrecon/pull/6). MRC is the microscopy volume format; PSF means point spread function and OTF means optical transfer function. Subsequent stacked PRs add the runtime and fixtures listed below. The six original 2D mathematical intake examples remain distinct from executable A/B checkpoints and rounded JSON remains unsuitable as a tight oracle.

The inherited 2D OTF v1.1 contract explicitly places asymmetric masses at `(oy,ox)`, `(oy+1,ox)`, `(oy,ox+1)`. Its formula and fixtures agree. Main's historical “above” wording follows the upward-display convention. The clarification is already present here; no defect or additional reuse blocker is established (I4).

## Installed verification policy

The owner expressly retained PR #21's [advisory coverage policy](../contracts/verification-coverage-advisory-v1.md) for roadmap #22 and phase 1. [PROJECT](../PROJECT.md), [AGENTS](../../AGENTS.md), `Makefile`, `pyproject.toml`, `scripts/verify.py` and the workflow supply installed checks. This task edits none of them.

The default submission gate remains full local verification of the exact clean candidate. `make verify` runs thirteen phases: locked sync; coverage cleanup; lint; format; types; tests; coverage combine/JSON/HTML/report; wheel; isolated wheel import; locked vulnerability audit. Same-run measurement export is required. Empty discovery, test skips and expected/unexpected passes are rejected by installed test policy.

Native statement/branch measurement is required globally/per owned package, including `src/simrecon`, `scripts`, never-imported owned files and relevant subprocesses. Current complete JSON/HTML reports and valid, consistent exact counters are mandatory. Percentages are advisory; no threshold is selected and low percentages alone do not block or justify test additions. Behavioral coverage and independent risk review remain required. Make/YAML, external dependency internals, ignored reference source and model behavior have no owned-Python metric claim. Configured continuous integration (CI) repeats the complete gate on Ubuntu 24.04 and macOS 15; conditional CI-authoritative mode is not enabled.

Existing numeric test contracts, including M25's memory limit, stay unchanged. Human task/review/scenario caps are not set. Inherited Java reader checks use the existing Fiji Java selected through `SIMRECON_JAVA`; executable/environment identities stay in local evidence. This is independent of the forbidden reference C/binary execution.

## Inherited open stack: read-only manifest

Fresh reads initially verified all fourteen exact heads/base refs below. They remain open/unmerged; corrected #22 continues above #21 without changing them. Final live readback is recorded outside tracked bytes. The archived bundle was read in a separate evidence object store before migration; its reading alone was not integration. Presence after migration comes from the owner-selected PR #21 ancestry.

| PR | Exact head | Base branch / exact base commit |
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

The public contracts below are inherited files under `docs/contracts/` in this execution tree, read at exact PR #21 head above. Their input restrictions are scientific boundaries, not missing implementations.

| Capability / public contract | Present in execution baseline? | Limit / genuine extension needed |
|---|---|---|
| Conversion and explicit first-harmonic 2D separation | Yes, runtime/contracts/tests. | Explicit acquisition mapping and supplied phases; no raw camera correction or unknown-phase estimation. |
| Detection-PSF 2D OTF, `otf-calibration-v1.md` | Yes, #7 runtime/contracts/fixtures. | Corrected supplied nonnegative PSF and supplied origin; no empirical SIM bead calibration. |
| Known-parameter 2D reconstruction, `known-parameter-reconstruction-v1.md` | Yes, #8. | Fractional carriers with bilinear spectral interpolation on detector-matched calibration; documented approximation. Not a 3D grid-resampling contract. |
| Known-carrier phase/modulation, candidate scan/selection, `illumination-estimation-v1.md`, `carrier-scan-v1.md`, `carrier-selection-v1.md` | Yes, #11–13. | First-harmonic integer 2D model, supplied relative steps/caller limits; continuous 3D carrier and unknown-step estimation remain gaps. |
| Reference translation and known drift, `translation-estimation-v1.md`, `integer-drift-correction-v1.md` | Yes, #14–15. | Periodic equal-intensity reference and supplied integer specimen drift/phase correction; differing raw phases and fractional/axial motion remain gaps. |
| Five-order volume separation, `volume-phase-separation-v1.md` | Yes, #16. | Known phases, zero plus ±1/±2 complex orders; empirical preprocessing/order gauge is separate. |
| Supplied 3D intensity-PSF OTF, `volume-otf-preparation-v1.md` | Yes, #17. | Corrected supplied PSF/origin; not raw phase-resolved SIM calibration. |
| Effective transfers from axial profiles, `volume-order-transfers-v1.md` | Yes, #18. | Supplied detection PSF/profiles, with `g0=1`; unknown empirical axial order response is not recovered. |
| Known volume reconstruction/gain, `volume-recombination-v1.md`, `volume-order-gain-v1.md` | Yes, #19–20. | Finite periodic model, integer lateral carriers, native axial sampling, detector-matched grids; relative complex gain fit for order 1/2. Complex output and signed Nyquist placement are explicit. |
| Viewing export, `imagej-export-v1.md` | Yes, #21. | Harmonized acquisition viewing/preserved illumination settings; not arbitrary reconstruction-array persistence. |
| Raw scientific layout/correction provenance and empirical 3D bead calibration | Not yet supplied by inherited components. | Phases 2–3, R1/R2/C0–C5 are genuinely new work. Reuse conversion mappings and separators rather than replacing them. |
| Independent complex OTF grids, full 3D unknown-parameter/motion estimation, selected-mode output and composition | Not complete. | Phases 4–7 extend existing narrow primitives and require new concrete contracts. |
| Full raw specimen+bead simulation and owner-reference parity | No complete accepted route. | Phases 8–9 require independent acceptance/settings/provenance; small component fixtures do not substitute. |

## Concrete dependency closure before execution

| Upcoming slice | Present reusable foundations | Remaining prerequisite / decision |
|---|---|---|
| Phase 2 R1 explicit raw layout | Conversion and optional acquisition viewing export. | Selected target layout/units contract; O1/O2, S1/S2. No old numerical PR merge prerequisite. |
| Phase 2 R2 corrections | Existing conversion metadata/provenance boundaries. | Completed R1 plus correction contract; O3/O4, S4. Scientific correction runtime is new. |
| Phase 3 C0–C5 empirical bead route | Known-phase volume separator and supplied-PSF preparation/transfer records, with actual inherited contracts/fixtures. | Completed new R1/R2 and empirical bead method; S2–S8/O2–O5. Supplied profiles and `g0=1` do not close empirical response recovery. I3 audits only applicable reused evidence. |
| Phase 4 G1 independent grids | Known volume reconstruction/order-gain consumers and limited 2D fractional interpolation. | Empirical response meaning/runtime, S9 and target grid facts; detector-matched restriction needs a new consumption/interpolation contract. |
| Phase 5 estimation/drift | #11–15/#20 narrow estimators/diagnostics. | New R1/R2, empirical responses and G1; S10/S11 and nuisance provenance. No automatic validity of 2D helpers for 3D inference. |
| Phase 6 reconstruction/output | #16–20 known-parameter volume path and optional #21 acquisition viewer. | Completed new phases 3–5, selected-mode extensions S12/S13/O6, result adapter decision I5. Existing reconstruction is present. |
| Phase 7 public raw workflow | Existing separate component APIs. | Completed new phases 2–6, independent complete small cases and S14 diagnostics/provenance. |
| Phase 8 full simulation | Inherited independent component cases/illustrations. | Phase-7 route plus separately contracted independent generator/acceptance; both raw acquisitions, hidden truth, convergence and resource plan (S14). |
| Phase 9 reference comparison | Conversion/provenance and later completed public workflow. | Successful phase 8, supplied matched cases/settings/outputs O7 and comparison decisions S15. Never execute reference programs. |

I1/I2 are owner-resolved baseline/policy choices; they do not require another merge/integration interview. Future new numerical components must be completed and present in their dependent slice's baseline. Applicable evidence is inspected by interface and intended use, not by reopening every unchanged historical component solely because PRs are open. Material contract/test/fixture/base/environment changes renew affected evidence under the installed rules. This task remains documentation-only.

## What evidence was actually inspected

| Evidence class | Inspected facts | Limit / reuse consequence |
|---|---|---|
| Exact inherited baseline | PR #21 tree, public exports/contracts, tests/fixture identities; prepared corrected roadmap ancestry and documentation-only delta; fresh old-head/base snapshots. | Present component functionality is distinct from merged-main status and future scientific completeness. Source reading is not a new acceptance verdict. |
| Original main-based roadmap | Accepted documentation review/full receipt for superseded `9022cfd…`: thirteen phases, 697/697 statements, 246/246 branches. Receipt SHA-256 `2aa76ce29b76f487f1afcaad29a75f330533de01f212257dc682491f4c750494`. | Historical only; neither baseline authority nor verification of corrected #22 or phase 1. Archived unchanged. |
| PR #21 maintenance | Canonical state, final-local-evidence manifest, exact tip receipt/coverage/measurement/logs and fresh bounded correction verdict inspected narrowly. Tip receipt SHA-256 `835e43d93223150f98906c4fda3efcd7c62f39b648c49a562fdbbbb60d98adff`; thirteen phases/4115 tests recorded. | Maintenance acceptance covers its named diagnostic correction. Applicable original scientific role/checkpoint evidence is inventoried separately; no claim of complete historical re-audit. |
| Native measurement | Tip reports 2304/2353 statements and 724/762 branches across 28 owned files; complete reports inspected. | Valid advisory measurement, not a percentage failure or a reason to add tests. Report integrity/behavioral findings remain review obligations. |
| Scientific acceptance/provenance | Inherited task pointers, contracts and signed reports identify approved checkpoints and independent comparisons; local inventory distinguishes actual verdicts inspected from reported claims. | Missing audit records are evidence gaps, not absent runtime. Review only applicability challenged by intended reuse or changed material inputs (I3). |
| Corrected roadmap / phase-1 checks | Exact receipts, fresh documentation verdicts, source/contract fingerprints and publication readback retained in local evidence outside tracked bytes. | Each changed candidate needs its own full gate/review. Local evidence is separate from configured platform CI; no new scientific correctness or parity claim. |

Historical attempts/spending stay in original records; new accounting preserves the superseded draft/checkpoint and correction without counting cumulative children again. Confidence is high in present component boundaries and empirical/grid/estimation gaps. Target behavior and specific evidence applicability remain uncertain until provenance, scientific contracts and narrow audits close.
