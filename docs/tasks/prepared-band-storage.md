# PB119: design releasable prepared-band storage

**Version 1.0. Git versions revisions; this record is not enforcement.**

## Contract

- Authority: original nine-issue user request at campaign attachment
  `923fd507-9da9-4f09-985c-ca6eb43c352d/Pasted text.txt`, SHA256
  `01bf84ee7afdb4e033502db4b726d62f0c83ec888cb112b0f786430c2239457e`,
  and [issue #119](https://github.com/david-hoffman/simrecon/issues/119).
  Routine roles, diagnosed corrections, checks and publication need no repeated
  document approval. Root owns scheduling/integration/publication.
- Branch: `docs/119-prepared-band-storage`; intended PR title:
  `docs(memory): design releasable prepared-band storage`. Stacked body uses
  `Refs #119`, names eventual default-branch closure and immediate parent #118;
  a PR into an intermediate branch does not complete default-branch delivery.
- Outcome: [contract R1–R9](../contracts/prepared-band-storage-design-v1.md),
  one concrete design and bounded handoff or a specific equivalence blocker.
  Authoring a recommendation activates no runtime/storage/scientific contract.
- Route: report-only scientific/design work with high-risk scientific reasoning,
  nonblind author and fresh independent scientific review, then exact full-local
  gate and fresh final readiness review. Runtime A/B/C/D are reserved for a
  separately authorized implementation; no manufactured red test is applicable.
- Architecture and public expectations: AGENTS, PROJECT, CE02–CE07, RM84 and #115;
  accepted #112 may inform precision context only. No new dtype/default/domain,
  disk API, assembly redesign or failure semantics are authorized.
- Ownership: coordinator owns this task, contract, `docs/packets/prepared-band-119/`
  and future report intake/integration metadata. Scientific author owns only
  `docs/reports/prepared-band-storage-design/design.md`, `lifetime-map.md`,
  `source-evidence-manifest.md`, `implementation-handoff.md` and, if needed after
  root permission/window, report-only evidence in that same directory. Scientific
  reviewer owns only its separately named review report; final reviewer owns only
  its separate readiness report. No role edits runtime/tests/fixtures/locks/gates/
  delivery rules/shared documentation or another worktree. Workers do not delegate.
- Coverage: inherit PROJECT's approved behavior coverage/independent risk review;
  percentages advisory, no selected percentage threshold or migration. Native
  global/package/file/never-imported/subprocess statement/branch integrity and
  current JSON/HTML reports stay required; no new runtime test obligation arises
  from this report-only diff.
- Checks: initial intake only source/document reads, writes and Git/diff checks.
  Dependent investigation and all executable checks wait for root. Final canonical
  `make verify` on exact clean Ubuntu candidate is required before any PR, draft
  included, or push to an open PR. All 13 phases and same-run M25
  (33,554,432-byte limit) remain; optional platforms do not replace Ubuntu.
- Model/effort: conservative project scientific author/reviewer selection
  `gpt-6.1-sol`, high; actual serving attribution/usage unknown unless exposed.
  Broader scientific calibration unmeasured. Escalate diagnosed reasoning or
  equivalence uncertainty; missing semantics return to intake, not a tolerance.
- Human numeric execution/review/cost limits: not set. Root's exclusive resource
  schedule is binding. Unknown measurements remain unknown; preserve all prior
  campaign attempts/charges and count only this task's events here.
- Completion: independently reviewed design/handoff or explicit blocker, exact
  accepted parent and reviewed refreshed evidence, full final Ubuntu verification,
  fresh final readiness acceptance, correctly stacked PR and observed CI. A
  blocked intake is not completed #119. Root has publication authority; no merge,
  release, manual issue closure or additional implementation authority.

| Scenario | Distinct obligation/outcome | Source | Examples to cover after dependency freeze | Evidence/review |
|---|---|---|---|---|
| S01 | Relevant peak/workload and affected refresh are accepted before reliance | #119 prerequisite; R1 | Original #116 vs post-#117/#118 observations | Manifest and independent applicability review |
| S02 | Time fragmentation opportunity and mandatory remainder for T>1 | #119 scope; R2 | Independent time owners, retained caller inputs | Analytic comparison/lifetime audit |
| S03 | T=1/multiple-direction target treated separately | #119 scope; R2 | Direction blocks vs time-only blocks | Concrete design or exact blocker |
| S04 | Every retained reference accounted for at each proposed release | #119 done; R3 | Views/bases, closures, adapters, traces | Full producer/consumer/reference map |
| S05 | Preparation/estimation/reconstruction stage order preserved | #119 scope; R4 | Later parameters still absent during preparation | Independent dependency review |
| S06 | Time-zero reuse/fresh modulation and shared acquisition state preserved | #119 scope; R4 | Multiple times, camera/anchor/drift state | Source-to-obligation design audit |
| S07 | All-direction parameter dependencies separated from local coefficient reads | #119 scope; R4 | Filter denominator versus block consumption | Consumer map/equivalence argument |
| S08 | Logical shapes/aggregate extents preserve valid positives and invalid boundaries | #119 scope; R5 | Noncontiguous inputs, accepted #115 domain | Named validation/adapters and failure matrix |
| S09 | Same-input outputs, signed values/zeros and discrete outcomes preserved | RM84; R6 | Summary and full-debug/direct-stage routes | Independent exact-equivalence obligations |
| S10 | C-order little-endian identity without a second full band array | #119 scope; R6 | Chunk boundaries, byte order, strided blocks | Ordered byte/metadata proof plan |
| S11 | Off-exposure storage/identities/consumers explicitly covered | #119 done; R3/R6 | Absent and supported present off exposures | Ownership/failure/identity matrix |
| S12 | Existing finite/failure precedence retained, including operation-time failure | #119 scope/done; R4/R5 | Invalid declarations vs later numerical/backend failure | Ordered validation/operation audit |
| S13 | Analytic opportunity and measured RSS/runtime claims distinguished | #119 done; R1/R7 | T=1 and multi-time; allocator/workspace unknowns | Evidence/units/method review |
| S14 | One concrete bounded implementation handoff or precise equivalence blocker | #119 outcome; R8 | Named private representation and public adapters | Fresh scientific verdict |
| S15 | Necessary external-storage handoff names missing lifecycle/I/O/failure contract | #119 done; R9 | Cleanup, capacity, cancellation, FFT residency | Bounded follow-up or evidenced not-needed finding |
| S16 | Defaults/debug compatibility and exclusions remain intact | #119 exclusions; contract | Direct-stage records, no disk/runtime/API edits | Diff/scope and final readiness audit |

Equivalent case counts and precise workloads remain unknown until accepted input
freeze. Scenarios map to design evidence and review, not fabricated product tests.

## Current state

- **DESIGN AND BOUNDED HANDOFF SCIENTIFICALLY ACCEPTED; final119 gates pending.** ROOT integrated the one owned intake commit onto actual accepted118 `61f3647e50e69b3f702fd0ea35fb4df9b0d8ae03`, tree `28d8214791af0fb2c75c0d7fb6ae1dfd867dac1a`, [PR125](https://github.com/david-hoffman/simrecon/pull/125). Its exact Ubuntu13 gate passed3500/47 and fresh D1 accepted; CI43903983166/job133427761353 passed3500/47/585.45s on matching integration49ea6a5d/tree28d8. Earlier grant-time pending labels remain historical. Original119 intake48339c8 is preserved externally/by ROOT reference; normative PB11980afb and intake packet bodies stay unchanged.
- Four frozen reports under [prepared-band-storage-design](../reports/prepared-band-storage-design/README.md) retain exact hashes: design7f07b194, lifetime042a8313, source manifest3159ea6d and handoff650bc78a. They bind measured75fc and actual61 used21 source/contracts byte equality. Accepted118 wholeSCI7566 supplies the finite78 refresh; actual119 SCI1 report9cead2dd/final9e90ce5a independently accepts R1–R9/S01–S16/allfive issue done criteria at DESIGN level. ROOT application8a7cb33a records acceptance; no119 runtime implementation or test checkpoint is manufactured.
- Selected future slice: compact-only independently owned time/direction q roots and shared owning table, complete logical/global validation and one canonical C-order little-endian digest, then successful source-slot release after each native-direction reader/borrow. Preserve all preparation before estimation, fresh modulation under time0 carrier reuse, camera/anchor/drift state, all-direction parameters, whole-time destination/setup/ALL-copy-before-any-filter, one global filtered finite check and separate assembly. Full/direct/default records and caller independence remain. Future implementation requires separate intake, blind A/B/restricted C/fresh D and actual ownership/equivalence/resource proof.
- Opportunity is later retained q payload `(T*D-k)*b`, `b=16*Q*Z*Y*(X//2+1)`; earlier caller/raw snapshots/all-q preparation/estimation and initial whole-time source+destination overlap remain. Hypothetical22.5146484375GiB is logical payload, not RSS/observed capacity. No general memory/speed benefit, currentlarge256 attribution/ranking/scaling/margin/headroom/16GiB or113single qualification is transferred. Currentlarge holds remain; no new256 is needed for the accepted structural design.
- R9: one conditional external-prepared-storage CONTRACT handoff specifies ownership/permissions/capacity/cleanup/cancellation/I/O/errors/identity/mappings/FFT residency. Independent SCI accepts its necessity criterion under a later explicit earlier-residency objective. Current disk necessity/fit is not established, so no follow-up filing/implementation is required or commissioned now. Three-query ROOT dedup remains finite evidence, not global completeness. #120 assembly stays separately scoped.
- Portable96-key map preserves original paths AND logical hashes,44 published ancestor Git streams,6 inherited118 same-byte records and46 finite exact local/history/SCI transports; no raw118 corpus or whole-program duplication. ROOT stage hash/length checks passed. Historical absolute paths/old Current bodies are provenance versions, not drop-in live checksum targets. Final staged/committed Git byte proof follows outside candidate bytes. No source/test/fixture/helper/dependency/gate/policy or public API changed.
- Final exact clean119 candidate/full Ubuntu13 `make verify`, native current global/package/file/subprocess coverage JSON+HTML/DB, wheels/isolated imports/audit/same-runM25, fresh independent readiness, ROOT lease-controlled PR and actual CI remain pending. Inherited118 B4 descriptor identifies unchanged test baseline, not a new119 A/B review. Prepare final pointer `/workspace/work/campaign/evidence/119/final-evidence.json` before verification; all eventual hashes/results stay external, without postgate tracked edits.
- Cumulative roles/partials/read corrections and unknown costs remain in [ROOT role ledger](../reports/prepared-band-storage-design/ROOT-role-ledger.md) and immutable histories. Fresh nonblind SCI1 metadata-only wc names/counts overread of2excluded files is disclosed; no bodies/history/verdict opened, no retroactive permission or restored blindness claim. Same-event literal49 continuation recorded. Human numeric quotas not set; serving/tokens/cache/money/unrecorded elapsed unknown; shared filesystem/prompt scopes are not engineered isolation. No merge/release/manual closure/follow-up implementation. No scratch/script/fixture/persistent workload created by119 authors/reviewer; active worktrees/environments/frozen fixtures/durable evidence kept. Next ROOT: clean candidate→fullgate→fresh readiness→publication/CI.

## PR presentation

Root will explain the selected storage ownership change and its limits in plain
English, identify immediate #118 parent and semantic #116/refresh dependencies,
and use the repository PR template. A conceptual lifetime/block figure will be
useful once an actual design exists; label it conceptual, with no invented RSS
bars. Technical appendix retains exact base/head, proposal/review identities,
full Ubuntu receipt, coverage/M25/resource limits and actual CI status. No PR is
ready at intake. Final candidate identities/results stay outside verified bytes.
