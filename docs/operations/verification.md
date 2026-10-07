# Full verification and receipts

**Version 1.0** Git versions revisions.

Prepare the single task pointer/intended docs before the final candidate commit. Run the canonical full gate for that clean exact candidate; retain failures and give D applicable evidence. `make check` provides fast feedback only.

```sh
make check UV=/Users/davidhoffman/.local/bin/uv
make verify UV=/Users/davidhoffman/.local/bin/uv \
  VERIFY_ARGS='--contract TASK-ID --reviewed-tests TEST-REVISION --base BASE-REVISION'
```

The [public receipt contract](../contracts/verification-receipt-v1.md) defines required phases, statuses and JSON fields. The additive [measurement contract](../contracts/measurements-export-v1.md) defines same-run M25 evidence; this repository’s `make verify` supplies `--measurements-required`. Direct helper calls without that flag preserve the legacy receipt behavior. The helper writes ignored `artifacts/verification/receipt.json` and phase logs. Coverage/build evidence comes from that same run; CI retains it on success/failure. It grants no approval, retries no role/check and mutates no Git state.

Optional `--input NAME=PATH` fingerprints an approved regular file's public alias, size and SHA-256 without copying its private path/contents into the receipt. Keep owner data and revealing raw logs local. HEAD/clean Git alone do not identify external/ignored inputs. Do not fingerprint ignored study archives implicitly.

Passing requires every full phase, a clean tracked start, unchanged candidate/input identities, complete owned-file native coverage JSON/HTML and one valid wheel. Failed/partial runs cannot pass through stale artifacts. Omitted context labels stay null, never guessed approval/checkpoint/base. Phase logs retain output actually emitted by the check commands. The existing M25 test exports baseline, peak, native units, byte increment and the unchanged 32 MiB limit after its assertions, from its single native subprocess. The verification helper supplies a fresh run ID and the ignored `artifacts/verification/measurements.json` destination. Its receipt includes the validated same-run values and exact report digest. Stale, missing or invalid mandatory measurement evidence cannot pass. A failed tests phase may retain valid current measurements as diagnostics, never as a passing result. Standalone scientific tests without the export environment retain their prior behavior. Do not run M25 a second time solely to retrieve numbers.

D may inspect applicable successful evidence without automatically rerunning it. Changed candidate/tests/fixtures/dependencies/checks/environment/base/relevant inputs invalidate affected reuse. The current submission rule still requires full verification of a changed exact submission candidate. Present package version is static 0.1.0; future Git-derived versions would additionally require commit/tag/dirty build identity. Receipts are ordinary evidence, not certificates/controllers.

Before opening/reopening a PR or pushing to an open one, confirm the exact candidate and passing full local gate. Any known check failure, missing required evidence or unmet selected coverage target blocks submission. Unselected percentages are advisory under the recorded [project policy](../PROJECT.md#coverage-policy-and-adoption-provenance); required report integrity still binds. Installed receipt/coverage thresholds remain binding until the adoption task records the owner choice and authorized independently reviewed infrastructure migration. Supported-platform CI still repeats the complete gate. Owner action is required to merge/release.
