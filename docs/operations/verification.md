# Full verification and receipts

**Version 1.0** Git versions revisions.

Prepare the single task pointer/intended docs before the final candidate commit. Run the canonical full gate for that clean exact candidate; retain failures and give D applicable evidence. `make check` provides fast feedback only.

```sh
make check UV=/Users/davidhoffman/.local/bin/uv
make verify UV=/Users/davidhoffman/.local/bin/uv \
  VERIFY_ARGS='--contract TASK-ID --reviewed-tests TEST-REVISION --base BASE-REVISION'
```

The [public receipt contract](../contracts/verification-receipt-v1.md) defines required phases, statuses and JSON fields. The owner-selected [advisory coverage amendment](../contracts/verification-coverage-advisory-v1.md) replaces the original full-percentage condition with report-integrity checks; exact native counts remain required. The additive [measurement contract](../contracts/measurements-export-v1.md) defines same-run M25 evidence; this repository’s `make verify` supplies `--measurements-required`. Direct helper calls without that flag preserve the legacy receipt behavior. The helper writes ignored `artifacts/verification/receipt.json` and phase logs. Coverage/build evidence comes from that same local run. Distributed CI retains its actual per-job evidence on success/failure. It grants no approval, retries no role/check and mutates no Git state.

Optional `--input NAME=PATH` fingerprints an approved regular file's public alias, size and SHA-256 without copying its private path/contents into the receipt. Keep owner data and revealing raw logs local. HEAD/clean Git alone do not identify external/ignored inputs. Do not fingerprint ignored study archives implicitly.

Passing requires every full phase, a clean tracked start, unchanged candidate/input identities, current, internally consistent native coverage JSON/HTML for every owned file and one valid wheel. Failed/partial runs cannot pass through stale artifacts. Omitted context labels stay null, never guessed approval/checkpoint/base. Phase logs retain output actually emitted by the check commands. The existing M25 test exports baseline, peak, native units, byte increment and the unchanged 32 MiB limit after its assertions, from its single native subprocess. The verification helper supplies a fresh run ID and the ignored `artifacts/verification/measurements.json` destination. Its receipt includes the validated same-run values and exact report digest. Stale, missing or invalid mandatory measurement evidence cannot pass. A failed tests phase may retain valid current measurements as diagnostics, never as a passing result. Standalone scientific tests without the export environment retain their prior behavior. Do not run M25 a second time solely to retrieve numbers.

D may inspect applicable successful evidence without automatically rerunning it. Changed candidate/tests/fixtures/dependencies/checks/environment/base/relevant inputs invalidate affected reuse. The current submission rule still requires full verification of a changed exact submission candidate. Present package version is static 0.1.0; future Git-derived versions would additionally require commit/tag/dirty build identity. Receipts are ordinary evidence, not certificates/controllers.

Before opening/reopening a PR or pushing to an open one, confirm the exact candidate and passing full local gate. Any known check failure, missing required evidence or unmet selected coverage target blocks submission. Unselected percentages are advisory under the recorded [project policy](../PROJECT.md#coverage-policy-and-adoption-provenance); required report integrity still binds. The owner chose advisory statement/branch percentages; Coverage.py no longer enforces a percentage threshold and receipts accept valid partial or zero execution. Missing/inconsistent measurements, missing reports and unapproved owned-file exclusions still fail. The adoption task records the independently reviewed migration and its activation evidence. Following the owner's October 20, 2026 platform migration, Ubuntu 24.04 is the sole CI platform and repeats the complete gate. Owner action is required to merge/release.

## Distributed Ubuntu verification

The [standard CI contract](../contracts/test-audit-standard-ci-v1.md) preserves
all logical checks with genuine preparation, independent quality, complementary
test and finalizer commands. Each job records clean-start and unchanged
source/input identity. Quality runs locked sync, lint, format and types, retaining
its own run-id/attempt artifact without a measurement UUID or preparation dependency.
Original native coverage and reportlog inputs remain in separate downloaded
bundles; finalization combines explicit originals with `--keep`, generates current
JSON and complete HTML, and runs wheel, isolated import and locked audit. Existing
coverage-integrity, same-run measurement and wheel validators remain automatic.
Native logs and identity observations record truthful job origins; these outputs
do not claim a single-process passed v1 receipt.

A passive public pytest collection hook records original test identity for native
reportlogs. Independent qualification compares the actual full reference and
successful shard phases without reverse-parsing resource-group suffixes. The
actual passing parent/child tests retain scientific and opaque-byte proof; a
resource report alone does not supply it. Preserve the sole original M25 export,
its exclusive canonical copy and matching digest through later phases.

The project automatic coverage policy remains advisory. The test-audit task has
separate selected exact100% native targets and cannot complete without independent
local and Ubuntu proof. Its complete closed-job interval includes setup, transfers,
finalization and post-job work; local test time or green shard counts alone do not
establish the requested sub-300-second result.
