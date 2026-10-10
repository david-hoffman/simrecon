# Gain-scaled error budgets retain an output quantum allowance

**Version 1.0**

- ID: 20261009T084914Z-volume-order-01-root-output-quantum
- Date: 2026-10-09T08:49:14.783492+00:00
- Task: [VOLUME-ORDER-01](../docs/tasks/volume-order-transfers.md)
- Role: root intake with report-only scientific advice
- Topic: numerical representation
- Status: confirmed
- Observation: For two equal PSF weights and coefficient row (q,0), where q=2^-1074, exact DC is q/2. Float64 cannot store that value. Dividing output error by gain q leaves at least1/2 error. A gain-scaled epsilon budget therefore needs an additive output quantum term; a fixed tiny scaled quantum term is insufficient.
- Evidence: [public numerical contract](../docs/contracts/volume-order-transfers-v1.md); task-local artifacts/axial-order-execution/adviser-intake-report.md records the independent example and source limits. This is a representability derivation, not product measurement or backend proof.
- Suggested action: Evaluate stored-input expectations and absolute rounding allowances in sufficient precision, including final output quantization.
