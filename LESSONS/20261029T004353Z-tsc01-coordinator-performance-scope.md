# Match reduction scope to the measured performance objective

**Version 1.0**

- ID: 20261029T004353Z-tsc01-coordinator-performance-scope
- Date: 2026-10-29T00:43:53.136706+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: test reduction and measurement
- Status: confirmed
- Observation: The original covered diagnostic attributed611.535s of2875.235s summed test-case time to the whole declarations containing the first20 reduction groups (21.269%). That is an affected envelope, not measured savings. The owner subsequently set a600s test-time objective. The separate canonical baseline took2888.877726s, including2842.468892s in its test phase. The target therefore requires a much broader reduction than the first group list alone establishes. Shared-helper effects outside the mapped declarations need their own evidence; elapsed values from different runs are not additive.
- Evidence: The retained original audit timing-analysis.json/profile receipt, canonical baseline commit6e150c594d814000ab9a70701b1ebe757650a4c2 and full-verification-2.json SHA256f3ce7dfc2d7d9550c4e04b3f8f50a77c5425f0b516ef49cd1b81ceaa07d8f535; local artifacts/test-consolidation/canonical-baseline.json binds its exact source and phase timings. Original covered diagnostic and standard make verify are separate runs. Final candidate savings remain unmeasured at this observation.
- Suggested action: Inventory the remaining cost by owning boundary, retire redundant proof layers and equivalent examples, and reduce fixtures where independent mathematical or byte-level truth remains informative. Use the final canonical full-check run for the performance claim; retain test-phase and other-phase times separately. A performance target is not a total work, review or token budget. This lesson grants no scope, oracle, gate or review waiver.
