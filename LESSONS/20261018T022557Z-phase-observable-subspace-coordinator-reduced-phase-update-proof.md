# Test phase updates inside the reduced specimen domain

**Version 1.0**

- ID: 20261018T022557Z-phase-observable-subspace-coordinator-reduced-phase-update-proof
- Date: 2026-10-18T02:25:57.140333+00:00
- Task: [Observable-subspace phase estimation](../docs/tasks/observable-volume-phase-estimation.md)
- Role: coordinator
- Topic: test scope
- Status: confirmed
- Observation: At the initial prepared checkpoint, successful hidden-phase recovery used full structural support. Reduced-support cases covered fixed-point diagnostics and rank loss. Those cases did not prove that a successful optimizer update stays in the reduced specimen domain. Fresh blind B independently constructed a successful case with full dimension12 and observable dimension6, exposing a concrete missing public-boundary proof.
- Evidence: Checkpoint `8ac0e889b8bf885537d55e6e1dad5bd2bd17f71e`; local `artifacts/phase-observable-subspace-20261018/B01/public-findings01.json`, SHA256 `bad91012a91c1564f2d84883fde35526043be818d91aba736d9b59996683195f`. This is an independent test-omission finding, not a product-defect or passing-implementation claim.
- Suggested action: Include an informative successful phase-update example with observable dimension strictly between0 and the full specimen dimension. Check phase movement, objective improvement, stable rank and the lifted observable representative separately from the hidden physical specimen. Minimum permitted exposure counts deserve a valid positive example.
