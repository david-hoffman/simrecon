# PB119: releasable prepared-band storage design

**Version 1.0. Authorized design intake; no runtime or API activation.**

## Authority and one-task outcome

The user's nine-issue campaign instruction and
[#119](https://github.com/david-hoffman/simrecon/issues/119) authorize one
concrete prepared-band storage/ownership design and a bounded implementation
handoff, or an evidenced equivalence blocker. The task is
[prepared-band-storage task](../tasks/prepared-band-storage.md), whose
Current state is the sole execution authority record. A report does not commission
the proposed implementation.

The issue observes that compact reconstruction retains one complete prepared-band
allocation; views of completed time/direction regions cannot release its backing
allocation. This is the issue's motivation, not a newly measured finding here.
There is no selected numerical tolerance, memory ceiling or latency ratio.
16 GiB workstation feasibility is an objective requiring caller/OS headroom, not
a promise. Representation validity and available RAM remain separate questions.

## Dependency and baseline boundary

Scientific work waits for accepted #116 and a root-frozen accepted #118 lineage
containing #117. Before downstream reliance, affected #116 measurements must be
refreshed after #117/#118 and independently reviewed. The original report/runs
retain their actual identities; neither ancestry nor an old receipt supplies that
refresh. The campaign's applied order is
main → #112 → #115 → #116 → #117 → #118 → #119 → #120 → #113 → #114.
#119's immediate publication parent is #118. #112 may supply accepted precision
findings; #113's later implementation is not an available prerequisite.

The current checkout at public accepted #115 is an intake staging baseline only.
It supplies no #116 acceptance, final parent, live-set measurement, selected
representation or release-point conclusion. Intake may record obligations and
future roles now; dependent source/lifetime analysis and experimental work wait.
Root supplies exact accepted parent commit/tree, refresh manifest/review identities
and material-input applicability before author launch.

## Requirements

- R1 — Use #116's accepted relevant workload and reviewed affected refresh to
  identify the target peak/live set. Name measured, analytically bounded and
  unknown quantities separately, including mandatory retained storage, input/output
  ownership, backend workspace, caller retention and OS headroom.
- R2 — Compare independently owned time blocks with direction blocks. Report
  T>1 and T=1/multiple-direction implications separately. Time-only fragmentation
  cannot solve the latter's essential working set. Select one concrete design
  justified by the actual target, or document an exact equivalence blocker.
- R3 — Supply a stage/block dependency and lifetime map on the actual accepted
  parent. List producer, owner, every reader/retaining reference, last consumer,
  release condition, mandatory remainder and uncertainty. Include base arrays,
  views, adapters, containers, closures, trace/debug records, identity readers,
  validation temporaries and off-exposure storage. Distinguish logical last use,
  unreachable storage and observed process residency.
- R4 — Preserve preparation-before-estimation-before-reconstruction. Preserve
  time-zero carrier reuse with fresh modulation, camera/anchor/drift state and
  current finite/failure priorities. Do not interleave preparation/estimation,
  replay raw inputs, change arithmetic/iteration order or silently fuse filtering
  with assembly. Parameter-wide filter denominators may require all directions'
  parameters even when coefficient reads are direction-local.
- R5 — Name logical shape and aggregate extent validation boundaries, constructors,
  ownership transfer, public/private adapters and consumer interfaces. Preserve
  accepted #115 signed index/native extent rules, invalid-input categories,
  failure order and direct-stage/full-debug compatibility. Define valid positive
  cases alongside rejection obligations; do not invent new validation meaning.
- R6 — Preserve same-input/output values and compact identities, including the
  existing C-order little-endian byte identity, without concatenating a second
  full band array. Specify streaming/chunk order, metadata and validation needs
  for contiguous and noncontiguous representations and off exposures. Prove byte
  equivalence from the actual identity contract; agreement with product output
  alone is no scientific oracle.
- R7 — Distinguish a payload/liveness opportunity from proved RSS savings. Any
  experiment must be bounded, reproducible, root-scheduled and tied to its actual
  candidate, inputs, backend/thread/environment and process protocol. Analytic
  bounds may support a design without inventing RSS or timing measurements.
- R8 — Hand off one separately intakeable implementation slice with named
  representation boundaries, allowed edits, compatibility/failure/identity
  validation, scientific oracles, ownership proof and resource acceptance plan.
  It gets fresh high-risk blind A/B, restricted C and fresh D if later authorized;
  this issue supplies neither tests nor implementation approval for that slice.
- R9 — If in-memory fragmentation cannot address the target peak, identify exactly
  what remains mandatory and why. Hand off one separately bounded disk-storage
  contract defining ownership, scratch location/permissions, cleanup on success
  and failure, cancellation, I/O ordering/errors, capacity, retained mappings and
  FFT residency questions. Do not introduce memmap or assume mapping eliminates
  resident/workspace memory. State unresolved questions as blockers, not decisions.

## Compatibility and exclusions

Inherit the approved CE02–CE07 contracts, the
[RM84 summary/full-debug boundary](reconstruction-memory-v1.md) and
[accepted allocation-domain contract](wide-allocation-domain-v1.md). Defaults and
supported float64/complex128 behavior stay unchanged. Same-environment retention
changes must preserve exact values, signed zeros, discrete decisions, identities,
state and failures; no blanket tolerance is selected. The scientific reviewer
must assess whether the proposed slice can actually satisfy those obligations.

No runtime/API/test/fixture/dependency/check-policy edits, disk API, scratch
implementation, precision activation, domain expansion, output writer, general
backend migration, raw replay, filter/assembly fusion or Fourier assembly redesign
belongs here. A necessary new semantic decision returns to intake/root; scope
cannot be expanded through a report recommendation. #120 owns its own assembly
design. No private RM84 ancestry or ignored legacy source is permitted.

## Required deliverables and acceptance

The author will create a concrete design report, stage/block lifetime and retained
reference map, alternative comparison and implementation handoff under
`docs/reports/prepared-band-storage-design/`. Every issue checkbox and task
scenario must map to evidence or an exact blocker. The source/evidence manifest
must bind actual revisions and material inputs; no report conclusion is authored
at initial intake.

A fresh independent nonblind scientific reviewer assesses the exact proposal,
equivalence, failure priorities, ownership and bounded handoff. This is report-only
high-risk scientific reasoning, not mechanical prose and not runtime A/B/C work.
Do not manufacture product-red tests. Scientific acceptance is distinct from the
final exact-candidate gate/readiness review. Root then integrates on actual #118,
freezes a clean candidate and runs full local Ubuntu `make verify` (all 13 phases,
current native coverage integrity/reports and same-run M25). Fresh independent
final readiness acceptance and all required resource evidence precede publication.
Any changed parent/conflict/candidate/material input renews affected review,
measurement and checks. Final hashes/results are recorded outside tracked bytes.

PROJECT's behavior coverage with independent risk review applies; percentages
are advisory and no numerical target is added. Installed gates remain binding.
Ubuntu is the required platform. There is no CI-authoritative or macOS gate.
Root alone pushes, creates/updates the stacked PR and observes actual CI. No merge,
release, manual issue closure or follow-up implementation is authorized here.
