# Actual raw retention and publication candidate

The final owned publication candidate is
`publishable-artifacts-v2/docs/reports/half-precision-study/`. It contains18
conventional tar/gzip raw-evidence parts, global/per-part original member SHA256
manifests, a TSV original-name/length/hash/archive map and final-publication-index.json.
The files are staged and byte-verified; ROOT has not yet integrated or published them.

| Final retained scope | Actual value |
| --- | ---: |
| Original logical entries | 37,074 |
| Original logical bytes | 589,675,161 |
| Compressed raw archive bytes, all18 parts | 56,125,830 |
| Largest archive | 7,836,377 bytes |
| Base current/history/source entries | 37,047 |
| Completed resource-review supplement | 26 files, including output ledger |
| Completed ROOT resource application supplement | 1 file |

The input scope is ROOT's immutable480c2a36… finite37047-entry snapshot: all149
primary raw/capture records, all original NPYs/array_index filenames, earlier
controls/startup/wrapper/oldQ failures/partials, source/protocol/environment and
completed prior method/common-projection/counterpart reviews,143 measured material
bodies and unchanged available startup text. Exact input inventory was frozen
before packing. Completed resource review540094b9…/finale55aff98…/output ledger
b849e50e… was frozen as26 extra files; completed application2c14c3c9… is a separate
one-file append. No active peer/coordinator or self-referential final-author tree
was included in raw membership.

All original logical names and bytes are retained, including deliberately malformed
and oversized failure records. Raw source/NPY JSON files were not normalized,
reserialized or regenerated. Runtime Python/native/time software binaries are not
redistributed; exact versions/paths/hashes/provisioning are preserved. CPU FFT
outputs were not retained, and standalone resource arrays/full metadata/trace/
working unpack are deliberately unexported: recorded identities/statistics plus
original diagnostic counterpart NPYs remain. These limitations are explicit, not
invented raw files or a whole environment/reproduction-complete claim.

## Standard hardlinks and independent byte validation

Within each finite part, duplicate SHA256+byte-count originals use standard tar
hardlink entries targeting an EARLIER REGULAR member of the SAME part with the
same bytes. All names/targets are relative without `..`; only regular/hardlink
members are allowed. No symlink/device or cross-part link is present. Restored
data files may share inodes; original filesystem/inode/metadata/live-heap
independence is not claimed. Copy data before modifying it. Archived grants are
historical evidence, not authority to execute a new study.

The second packaging pass independently read every logical member via standard
`tar.extractfile`, checking full restored length/SHA256 and exact name. The gzip
stream was then verified to decode byte-for-byte to that validated ordinary tar.
Its37,073 entries contain5,727 regular files and31,346 same-part hardlinks. The
application-only eighteenth part independently compares its exact original bytes.
All compressed parts are below100,000,000 bytes. Archive files/manifests are readonly.
No generic restorer or numerical/capture/oracle framework was added.

The first verified ordinary-tar packaging attempt (16 parts,280,375,718 compressed
bytes) remains immutable externally in publishable-artifacts/ as historical
packaging evidence. It is not the final publication set. The final17-part hardlink
base and its raw-archive-index.json remain unchanged; the application-only part
and NEW final-publication-index.json append without rewriting frozen parts.
These are packaging attempts, not numerical trials or changed data/caps.

## Extraction and original-byte checks

From `docs/reports/half-precision-study/evidence/`, with standard gzip/tar and
sha256sum installed, use a NEW EMPTY destination:

```sh
sha256sum -c final-archives.sha256
mkdir restored
for archive in *.tar.gz; do
    tar -xzf "$archive" -C restored
done
cd restored
sha256sum -c ../final-originals.sha256
```

`raw-originals.tsv` maps every base/review original path to its archive; the
application append is explicit in final-publication-index.json and its own member
manifest. Original relative run.json/array_index/NPY names restore unchanged. Local
absolute paths embedded in original records remain provenance, not portable shell
operands or current grants. This conventional byte extraction/check does not
execute product, scientific, source or archived helper code.

The old EE113 blob-table8MiB/16MiB/256MiB/count limits were not raised or used for
this standard tar set. The aggregate limit counts every logical duplicate and
would not fit the full study; ordinary finite tar partitions avoid introducing
new restoration software. Exact archive hashes/member manifests and final index
are part of the completed author's output ledger. Final SCI and ROOT's reporting
candidate/gate/D/integration/publication remain separate.
