# Full verification and receipts

Prepare the single task pointer/intended docs before the final candidate commit. Run the canonical full gate for that clean exact candidate; retain failures and give D applicable evidence. `make check` provides fast feedback only.

```sh
make check UV=/Users/davidhoffman/.local/bin/uv
make verify UV=/Users/davidhoffman/.local/bin/uv \
  VERIFY_ARGS='--contract TASK-ID --reviewed-tests TEST-REVISION --base BASE-REVISION'
```

The [public receipt contract](../contracts/verification-receipt-v1.md) defines required phases, statuses and JSON fields. The helper writes ignored `artifacts/verification/receipt.json` and phase logs. Coverage/build evidence comes from that same run; CI retains it on success/failure. It grants no approval, retries no role/check and mutates no Git state.

Optional `--input NAME=PATH` fingerprints an approved regular file's public alias, size and SHA-256 without copying its private path/contents into the receipt. Keep owner data and revealing raw logs local. HEAD/clean Git alone do not identify external/ignored inputs. Do not fingerprint ignored study archives implicitly.

Passing requires every full phase, a clean tracked start, unchanged candidate/input identities, complete owned-file native coverage JSON/HTML and one valid wheel. Failed/partial runs cannot pass through stale artifacts. Omitted context labels stay null, never guessed approval/checkpoint/base. Phase logs retain output actually emitted by the check commands. Some existing tests capture measurements internally; those measurements do not automatically appear in the logs or receipt. Same-run export requires a separately authorized A/B-reviewed test change. This infrastructure task neither needs nor authorizes that change; report and defer missing export rather than rerun tests solely to retrieve numbers.

D may inspect applicable successful evidence without automatically rerunning it. Changed candidate/tests/fixtures/dependencies/checks/environment/base/relevant inputs invalidate affected reuse. The current submission rule still requires full verification of a changed exact submission candidate. Present package version is static 0.1.0; future Git-derived versions would additionally require commit/tag/dirty build identity. Receipts are ordinary evidence, not certificates/controllers.

Before opening/reopening a PR or pushing to an open one, confirm the exact candidate and passing full local gate. Any known failure/incomplete supported metric blocks submission. Supported-platform CI still repeats the complete gate. Owner action is required to merge/release.
