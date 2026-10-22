# Include public construction contracts in blind composition packets

**Version 1.0**

- ID: 20261018T020456Z-phase-observable-subspace-coordinator-public-construction-context
- Date: 2026-10-18T02:04:56.307035+00:00
- Task: [Observable-subspace phase estimation](../docs/tasks/observable-volume-phase-estimation.md)
- Role: coordinator
- Topic: blind public context
- Status: confirmed
- Observation: The initial allowlist omitted the raw-acquisition declaration and empirical-volume-response construction contracts needed by the approved O15 composition. The author’s guessed constructor field failed before the new scientific operation. That was a test/context defect, not product-red evidence. The invalid draft was removed; the coordinator supplied the two existing public contracts without adding scientific meaning.
- Evidence: `artifacts/phase-observable-subspace-20261018/A01/packet.txt`; `A01/invocations/resume02/final.txt`; `A01/public-context-supplement01.json` under the same proof root, SHA256 `adec506f6f19115fe593c2583e81814243cfcf69c4677ecc53d056ef82ea5ee7`; the two approved contracts under `docs/contracts/`. These are local evidence pointers, not a claim of a passing implementation.
- Suggested action: Inventory the public construction signatures required by each composition before blind authorship. Resolve an omitted existing contract through narrow public context instead of inferred constructor fields. Keep setup/test defects separate from product failures.
