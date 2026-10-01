# MRC-CONVERSION: intake decisions

**Version 1.0**. Draft. No architecture, product contract, tests, or execution allowance is approved here. The sole Current state remains in [architecture intake](architecture-intake.md#current-state).

## Accepted objective and baseline

Inspect supported legacy MRC images, resolve metadata and named axes, and write modern documented MRC output. Preserve decoded pixel values exactly; plane order and storage encoding may change. Python library and command-line interface share behavior. No image correction or reconstruction; no optical transfer function (OTF) required. The separately requested reconstruction placeholder remains separate.

Existing handed-off worktree: `/Users/davidhoffman/.codex/worktrees/540f/simrecon`; clean baseline `4fc8ea2d51d3ed58536b034954a0596a1b9d0dc2`. Intake allowance is unlimited; execution allowance is pending. New commits require author and committer `codex <codex@openai.com>`. No push, pull request, merge or release requested.

## Evidence opened September 30, 2026

- [CCP-EM MRC2014](https://www.ccpem.ac.uk/mrc-format/mrc2014/): proposed modern output authority. Modern mode 0 is signed; a three-dimensional grid alone cannot retain all SIM acquisition axes.
- [mrcfile usage](https://mrcfile.readthedocs.io/en/stable/usage_guide.html): candidate modern reader/writer and memory mapping; no owner legacy compatibility established.
- [mrc publisher documentation](https://pypi.org/project/mrc/): republishes the former UCSF Priism header table and distinguishes Priism/DV from MRC2014. This is a secondary historical copy, not an opened original UCSF specification or proof of owner-file applicability. No package implementation is adopted.

Material discrepancy: the republished table describes cell fields as pixel spacing times sampling intervals, while the repository legacy study observed code using header fields directly as micrometre spacing. Profiles must explicitly distinguish these conventions. Do not infer semantics from plausible magnitudes.

The owner supplied a processed companion and then a raw 2D single-channel acquisition. [Local observations](../architecture/owner-mrc-observations.md) establish mode 6 little-endian raw pixels and mode 2 big-endian processed pixels with the legacy identifier, identity spatial mapping and no actual extension. The raw acquisition has nine stored planes. The owner confirmed three phases per orientation and required phase/orientation counts and ordering to be supplied by configuration. The proposed sample config therefore declares three orientations and phase-fast ordering. Physical units and missing axial scale need an explicit profile/output policy. Confidence is high in these measured storage facts and limited for dialects not represented by the samples.

## Fixture route

Use independent byte fixtures alongside owner-file value-preservation checks: independently construct bytes from a reviewed offset table and explicitly declared profile. Expected pixels come from an asymmetric coordinate formula, not the new writer, a round trip, or legacy outputs. Declare byte order, counts, axes, units and extended bytes alongside each fixture. This demonstrates the declared profile only, not unseen owner datasets.

The provided raw file establishes a representative storage layout; the owner confirms 2D/no Z and one channel. Use explicit acquisition config for phase/orientation ordering, and the proposed direct-micrometre profile for owner approval before deriving logical expectations. Keep the owner files local; do not commit or upload them. No external sharing authorized.

## Proposed contract boundaries

These are recommendations, not approved behavior:

- Functional Python/NumPy, existing Python 3.13/uv scaffold, small value records and scoped file access; no scheduler or compiled core. SciPy remains available for later scientific work.
- Narrow the initial proposal to demonstrated spatial modes 6 (unsigned 16-bit) and 2 (32-bit float), including both byte orders. Other modes, complex data, sub-resolution payloads, compressed files and axis permutations remain separate coverage decisions. Each supported mode and byte order requires honest scenario accounting.
- Explicit profiles declare dialect, byte order, spatial-field convention/units, acquisition counts and fastest-to-slowest plane axes. No hidden phase/orientation defaults. Explicit overrides win and record old/new provenance. Unknown ordering blocks harmonization; explicitly opaque extended metadata may be preserved without invented meanings.
- Metadata-only inspection, selected reads into owned NumPy blocks, pure metadata/layout harmonization, and bounded-block writing. Settle exact public signatures, CLI syntax, selection semantics, errors and source-change checks before tests.
- Canonical logical axis order: time/channel/orientation/phase/z/y/x, retaining only axes actually present. For the supplied 2D single-channel raw data, propose orientation/phase/y/x after ordering confirmation; do not relabel stored sections as Z. Output is a plane stack plus one versioned documented extension preserving full axes, original header bytes, opaque extended bytes and override provenance. Settle framing, padding, size limits, header scaling and schema validation before tests. A private tag is not an officially registered extension.
- Exact decoded-value preservation; no lossy casts, guessed scale or silent metadata loss. Unknown units require an approved output policy.
- Bound pixel memory by selected plane/block size, without a whole-acquisition allocation. Separately bound metadata or specify streamed preservation; pixel streaming alone does not bound a large extension.
- Demonstrate a pinned independent modern reader. Establish a pinned ImageJ/Bio-Formats path and asymmetric fixture before viewer claims. Label flattened stacks explicitly; correct channel/time interpretation remains later integration.

## Concrete proposal for owner read-back

[Public/config/output contract proposal 1](../contracts/mrc-conversion-v1.md) supplies exact functions, returned fields, JSON config, byte framing, output header mapping, streaming bounds and errors. [MRC-CONVERSION-01](mrc-conversion.md) proposes one coherent end-to-end task, with 26 honestly listed scenario contexts, an explicit exception to the five-case default, and a 12-hour execution cap. Both require actual owner approval. It also explicitly narrows initial demonstrated reader support to mrcfile 1.5.4; ImageJ integration remains pending, with no installed Java runtime established.

## Delivery preparation

The linked proposal requests an explicit larger-slice exception for one 26-case contract. Until that exception and the identified behavior/budget are accepted, the ordinary five-case default remains in force. Cases are counted as contexts rather than assertions; no executable tests/product code are authorized by this draft. Any subdivision preserves scenario lineage, spent budget and the plan repair allowance.

Settle architecture approval, public interfaces, fixture sources, output schema, errors, scenario tables, completion and execution budget before tests or product code. Default two A/B rounds per window and one C repair after initial C apply; splitting does not multiply the plan repair allowance. Fresh root A/B/C/D sessions follow approval. Placeholder and doctor proposal remain separate.
