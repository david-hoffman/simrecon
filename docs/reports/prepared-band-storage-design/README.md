# Releasable prepared-band storage design

The independently accepted design gives each compact-workflow time/direction its
own prepared-band allocation. Completed directions can then lose their source
storage after filtering. All preparation and parameter estimation still finish
first, and every direction's parameters remain available to filtering.

This is a design and separately intakeable implementation handoff. It introduces
no runtime representation or storage API. Earlier caller/raw snapshots and all
prepared bands still coexist, and the complete filtered destination is allocated
before any source release. Later payload opportunity is not a measured RSS saving
or a whole-volume/16 GiB feasibility result.

- [Design and alternatives](design.md)
- [Owners, readers, release conditions and failure order](lifetime-map.md)
- [Exact source and accepted-evidence provenance](source-evidence-manifest.md)
- [Bounded implementation and conditional storage-contract handoff](implementation-handoff.md)
- [Independent SCI1 report and literal requirement mapping](evidence/reviews/scientific-review-1/report.md)
- [Distinct SCI1 final verdict](evidence/reviews/scientific-review-1/final.md)

SCI1 accepts the exact four report hashes with bounded scientific limitations,
against accepted118 local61f3647e/tree28d82147 over1172cb. It independently checks
all21 used source/contracts and the exact49-leaf before/after closure. Executable
ownership/equivalence, RSS benefit, currentlarge attribution and disk necessity
remain unproved. Conditional R9 supplies missing lifecycle/I/O/failure/residency
questions; it does not select memmap or claim a disk implementation will fit.

The four authored reports preserve their original checkpoint wording and bytes.
Older pending-parent/review text is qualified by the exact ACTIVE ROOT grant and
completed SCI1 report, rather than rewritten after review.119's final integration,
full Ubuntu gate, fresh readiness and publication/CI remain separate ROOT gates.
Grant-time118 CI was in progress and is not relabelled passed by these artifacts.

## Portable evidence

[Versioned source map](evidence/portable-source-map-versioned.json) resolves each
literal `source_path` plus `logical_sha256`. It preserves aliases and originating
maps, actual nonnull logical/transport byte lengths and exact transport hashes.
44 streams resolve to published ancestor Git blobs; six118 records reuse existing
repository paths at61. The remaining finite author/coordinator/SCI artifacts are
exact copies. No118 raw measurement corpus or whole-program snapshot is duplicated.

The original [45-input author map](input-source.sha256), source read/accounting
records,22 literal local author inputs, original proposal/history and ACTIVE SCI49
packet remain represented. Absolute paths in frozen records are provenance keys,
not required local filesystem locations. Resolve them through the versioned map;
Git entries identify immutable revision/path bytes. The [96-entry finite inventory](evidence/source-inputs-with-SCI1.sha256)
includes actual four SCI1 outputs. [Before-SCI map](evidence/portable-source-map-before-SCI1.json)
and its92-entry inventory preserve the source-only preparation checkpoint.

Report-local Git attributes preserve exact bytes. ROOT must check the actual Git
index/blob bytes when integrating; external staging checks alone do not prove the
eventual committed candidate or its verification.

ROOT subsequently confirmed [parent PR125](https://github.com/david-hoffman/simrecon/pull/125) CI43903983166/job133427761353 passed3500tests/47warnings/585.45s on integration49ea6a5d/tree28d82147, matching accepted61. [Integration release](evidence/provenance/ROOT-accepted-parent-and-integration-release-1.json) applies that later fact without rewriting grant-time pending records. ROOT independently verified all96 portable mappings/lengths before copying. The [SCI application](evidence/provenance/ROOT-scientific-acceptance-application-1.json) applies the bounded design verdict. The final119 candidate/gate/readiness/PR/CI records are external at `/workspace/work/campaign/evidence/119/final-evidence.json`; no current119 gate completion is claimed by this snapshot.
