# FULL-NOISY-SIMULATION: independent raw acquisitions and full workflow assessment

**Version 1.0.** On October 22, 2026 the owner requested “Let’s do the simulation!” after distinguishing the completed small noisy study from the roadmap's full raw-bead/raw-specimen simulation. This authorizes the simulation and its necessary numerical prerequisites. No numerical time, cost, scenario or review limits were set.

## Objective and dependency order

Deliver an independently generated approximately 512 × 512 × 64 voxel specimen acquisition and a separate finite-bead calibration acquisition; include photon/background/read noise; process legitimate raw observations through the public calibration/reconstruction route with evaluator truth hidden. Report scientific errors, failure/ambiguity outcomes, runtime, memory, seeds, array digests and model limits. Large arrays alone do not complete the objective.

The execution baseline is fetched main at 62f12e2936281f35bd78f2892c1511ee558365d4. Existing PR52 CI work is preserved on its own branch; this task does not merge it, alter gates or claim it is integrated into main.

The [roadmap](../MIGRATION-ROADMAP.md#8-penultimate--full-end-to-end-3d-simulation) supplies the objective. Proposed optical/geometry/noise values are adopted as explicit synthetic trial assumptions, never instrument facts: detector (z,y,x)=(64,512,512), spacing (0.125,0.080,0.080) µm, wavelengths 488/525 nm, matched index 1.515, detection numerical aperture 1.40, three nominal orientations and five phase commands; finite 100 nm uniformly emitting beads. Physical generator intake must state pupil/polarization approximation, focal-plane-relative illumination, boundaries/padding, pixel integration and independent convergence checks before its own tests.

| Slice | Concrete result and dependency | State |
|---|---|---|
| NS01 | Pure Poisson/background/Gaussian camera sampling under the [public camera contract](../contracts/simulation-camera-v1.md). Independent of the calibration-information choice. | Implemented; camera-only verification retained, final combined/platform acceptance pending |
| NS02 | Independent expected-image optical operator, then phantom and raw bead/specimen generation, with analytic/convergence proofs and a measured memory plan. The pure optical operator is independent of NS01; noisy composition uses completed NS01. Requires its concrete public numerical contract. | Optical/source prerequisites implemented; exact combined verification and independent acceptance pending |
| NS03 | Missing raw calibration and parameter operations, continuous carrier/grid consumption and scalable execution. Uses a concrete image-only or independently measured information channel. | Material acquisition choice pending |
| NS04 | Public raw workflow, small complete noisy cases, full-size sequential generation/calibration/estimation/reconstruction and independent error/resource assessment. | Dependent on completed NS02/NS03 |

The independent pure source-catalogue prerequisite is contracted in [simulation-sources-v1](../contracts/simulation-sources-v1.md), with [named role ownership](simulation-sources.md). It selects a disclosed total-normalized midpoint sphere model. Exact sphere-cell integration and continuum accuracy are not inferred. Source refinement and grid-offset sensitivity remain measured scientific evidence. This pure geometry slice does not depend on the optical/camera implementations or supply an inverse information channel.

The owner has been asked whether phase/carrier information must be inferred from noisy images or may use independently simulated measurement channels. No answer is inferred from silence. No phase monitor or extra metrology is silently added. No true phases/carriers/optical responses/offsets/gains/drift may enter the inverse as unmeasured “metadata.” Current point/two-site information theorems are not general finite-sphere noisy calibration algorithms. Existing integer-carrier APIs may not silently round the proposed continuous optical carriers.

On the inspected workstation, memory is 16 GiB. Existing full-volume phase-estimation allocations are not feasible merely by scaling the small example. Measure staged execution; no uncontrolled full-size launch or truth-selected short-cycle/support workaround. Resource staging is implementation discipline, not a new owner-set quota.

## NS01 contract, route and ownership

High risk: stochastic numerical meaning, statistical oracle and representation/failure rules. Fresh native blind A, fresh native blind B, restricted C and fresh native D. Use gpt-6.1-sol/high provisionally under existing model guidance; record actual attribution/counters or unknown. No source/history/current-task lesson exposure for A/B.

- A owns only tests/test_simulation_camera.py and optional tests/simulation_camera_fixture.py.
- C owns only scripts/simulation_camera.py. This is an in-repository simulator tool module, not a new top-level shipped reconstruction API. No test/fixture/check/discovery/coverage/lock/policy changes.
- B and D assess only and do not repair targets.
- Coordinator owns this task, the numerical contract, packets, evidence, subsequent slice intake, scientific report/presentation and completion housekeeping.
- All later scientific slices retain the same high-risk role separation; dependent work starts from completed prerequisite baselines. This plan grants no unfinished contract numerical meaning.

Retain complete native Coverage.py executable-line/branch-destination measurement globally and per owned package/file for src/simrecon and scripts, never-imported files and relevant subprocesses; no exclusions/skips/platform union. Preserve the continuing numerical chain's binding 100% native targets and current configured platform gates. This does not change PROJECT's advisory default for unrelated work or promise complete behavior from percentages. Source-free diagnostics precede blind imports/probes. A/B independently map behavior/risk obligations; D checks concrete omissions.

Use focused locked lint/format/type/public-entry checks during work. Exact final candidate make verify UV=/Users/davidhoffman/.local/bin/uv remains required before any own push or PR; full independent configured-platform evidence and fresh D remain completion duties where applicable. No PR, push, merge, release or external message follows from this record. No existing tests or gates may be weakened to obtain a run.

## Boundary and evidence inventory

NS01 enumerates input domain, deterministic/noisy modes, independent noise sources, units, seeded repeatability, ownership, conversion/range, operation-time failure and compatibility in its contract. It performs no persistence. Later generation must contract no-overwrite/output failure behavior before code; no reusable destructive cleanup tool is authorized.

One sole live state is artifacts/full-noisy-simulation-20261022/Current-state.md. It links cumulative predecessor cleanup/accounting, actual role launches/checkpoints, command/status/environment inputs, classified failures, review/correction rounds and outstanding scientific decisions. Final candidate hashes/results belong outside tracked bytes. Missing tokens/cost/elapsed measurements are unknown, never zero.

Completion cleanup is coordinator-owned under AGENTS and the completion workflow: inventory only this task's positively identified fixture/scratch units, close its writers, retain original evidence, raw-array digests/seeds, actual required raw/evaluation artifacts and all still referenced files/links/ancestors/environment/Python/Java pins. Verify regular hashes and link text/resolution/dependencies before/after, trim safe disjoint siblings and report blocked exceptions. Actual destructive behavior retains its applicable route/review; no age/name-only deletion, daemon or new reusable cleanup helper.

## Presentation

The final report must lead with what the noisy acquisition and reconstruction did, which unknowns were inferred, scientific errors and limits. Use observed signed slices/profiles with units and shared scales when useful; place technical identities, coverage, resources and provenance in a collapsible appendix if publication is authorized. A full-size known-input diagnostic is labeled conditional and cannot stand in for NS04.
