# Qualify blind diagnostics on an actual failing native probe

**Version 1.0**

- ID: 20261030T232729Z-ra06-coordinator-native-failing-diagnostics
- Date: 2026-10-30T23:27:29.914633+00:00
- Task: [RA06](../docs/tasks/reference-alignment-ra06.md)
- Role: coordinator
- Topic: source-free native diagnostics
- Status: confirmed observed failures and qualified repair; original foreign-module origin remains unverified
- Observation: B2's default file-descriptor capture needed an unavailable temporary directory, then the native Python exception hook printed source despite a StackSummary formatter. A later controlled preflight passed, but native B3's failing test found the imported `sitecustomize` lacked the guard callback. The exact guard file contained it; the original module's origin was not established. The repair loads that file under a unique module name, binds the callback directly and preserves ambient startup modules/PYTHONPATH. V6 exercised a foreign cached module plus successful checks, actual failed tests, collection/startup errors and warnings under denied regular-file writes. Fresh B4 then observed source-free failing-test diagnostics in its native read-only session. No SIMrecon implementation source appeared in B2/B3's reported exposures; both sessions stopped without acceptance.
- Evidence: `artifacts/ra06/roles/B2/final.txt`, `artifacts/ra06/roles/B3/final.txt`, `artifacts/ra06/harness-preflight-v6/result.json`, `artifacts/ra06/public_runner.py`, `artifacts/ra06/public_harness/sitecustomize.py` and `artifacts/ra06/roles/B4/final.txt`. Qualified Python3.13.12/pytest9.1.1; B4 independently checked exact guard hashes and retained category, message, location and failure status. Earlier failed preflights/role charges remain in the sole evidence ledger.
- Suggested action: Qualify intentional failure as well as success in the actual role environment. Bind the intended diagnostic module explicitly rather than assuming a generic startup-module name resolves to it. Recheck relevant startup/cache/capture differences. Keep these diagnostic settings separate from the unchanged canonical full gate. This is an observed workflow lesson, not an engineered blindness guarantee, permission change or general pytest compatibility claim.
