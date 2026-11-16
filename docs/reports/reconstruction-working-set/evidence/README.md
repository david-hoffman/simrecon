# Portable evidence and restoration

The [location map](location-map.json) binds original path spellings and SHA256
identities to supplied files. Original JSON, source versions, failed attempts,
qualification records and canonical outputs retain their original bytes. The
active report has mapped links; archival documents retain historical references.
The map records the distinction between supplied artifacts, installed-runtime
fingerprints and sample streams supplied through lossless gzip transports.

The seven canonical sets under `../analysis/` contain 48 files. Their original
identity maps hash their other members; the map's own hash is bound externally.
The [attempt ledger](../analysis/attempt-ledger.json) separates 90 eligible
observations, one failed workflow and other operational/qualification history.

## Samples

The 91 gzip files live under `samples-gzip/<attempt-id>/samples.jsonl.gz`, outside
the raw directories. Each restored raw directory has exactly its eleven original
files. The failed historical original sample remains tracked. The 90 eligible
original sample files are preserved locally as explicitly inventoried external
inputs; their transports are published. No original sample was replaced by its
compressed digest. ROOT verified each gzip by streaming decompression and checking
the original SHA256 and byte count, then checked the copied compressed bytes.

[sample-restoration.tsv](sample-restoration.tsv) lists transport, destination,
original SHA256 and original byte count, relative to this report directory. In a
fresh checkout, change to this report directory and restore missing streams with
the standard gzip utility. For example:

```sh
gzip -dc evidence/samples-gzip/ws116-gp-l256-summary-searched-r1-p/samples.jsonl.gz > raw/ws116-gp-l256-summary-searched-r1-p/samples.jsonl
```

Use the matching TSV row's SHA256 and byte count to check the restored file before
interpreting the raw set. Do not overwrite a differing existing file. The location
map contains every original/transport pair and original size. Compressed hashes
identify transport bytes; decompressed hashes identify the original observations.
Original allocated filesystem blocks are historical facts and can differ on a
clone. This integration copied verified transports; it did not repeat experiments
or claim a clean-clone scientific rerun.

## Original paths and source versions

`objects/<SHA256>/<basename>` preserves exact referenced source/support versions.
Different versions of the same historical absolute path remain distinct objects.
For a selected canonical analysis, use its exact config/command and required
path+SHA list to construct an isolated original-path view from these objects and
restored samples. The map retains each containing document, field and original
spelling. Do not overlay every historical version into one path or change embedded
JSON references to pretend that all versions were current together.

The installed interpreter, Docker, Git and two stdlib identities are environment
fingerprints, not supplied executable bytes. Environment, dependency, ABI and
native-dispatch correspondence must be established separately before execution.
The original analysis used real full stdlib statistics/random initialization;
synthetic guard fixtures are separately labelled. Historical grants, windows and
ROOT release records authorize no new run. Numerical reproduction requires fresh
resource admission and exclusive scheduling. No portable 16 GiB guarantee follows.

## Historical limits and delivery

Nine of eleven earlier authoring-ledger pins have supplied exact Git-blob or
planning-file bytes. Two early intake task/review drafts remain unavailable within
the examined campaign-owned ancestry and named snapshots. Their original hashes,
lookup scope and unavailable status remain in the map; no global absence or
reconstructed content is claimed. They are historical drafts, separate from the
supplied current scientific/method prerequisites. Original RM84 run receipts that
were unavailable remain unavailable.

The [material transition](material-transition.json) keeps the measured EA revision
separate from publication documentation. The sole task Current state is
`../../../tasks/reconstruction-working-set.md`. Exact final candidate, full Ubuntu
gate, independent post-gate acceptance and actual CI belong to the campaign index
and PR evidence outside candidate bytes. Earlier #112/#115 gates do not qualify
this candidate. This evidence directory is not another Current state.
