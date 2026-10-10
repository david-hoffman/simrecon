# Valid phase-output quantization can break illumination accuracy

**Version 1.0**

- ID: 20261008T023531Z-carrier-scan-intake-scale-free-precision
- Date: 2026-10-08T02:35:31.085950+00:00
- Task: CARRIER-SCAN-01; [execution pointer](../docs/tasks/carrier-scan.md)
- Role: intake coordinator; independently reproduced by blind B1
- Topic: numerical composition and scaling
- Status: confirmed
- Observation: On stored two-pixel subnormal observations with positive quanta [23,22,13,9,19], the baseline known-carrier API returned gain 0.1875+0.0625i. Independent stored-input fits gave 0.2114244582986091+0.09357666907420538i. Error 0.0392191 exceeds the informative budget 1.81899e-11. Individually valid quantized intensity coefficients can lose necessary accuracy when used inside a dimensionless ratio. This observation does not establish a standalone phase-solver defect.
- Evidence: Baseline PR #11 head 4b47d8c0917d6e2ac0dfa7052ea4b980b69dd855; test_subnormal_stored_input_fit_is_scaled_before_precision_is_lost in the task's proposed tests; source-free A/B1 reports in ignored execution evidence; [existing illumination arithmetic contract](../docs/contracts/illumination-estimation-v1.md).
- Suggested action: Preserve original-scale phase validation/rank/range errors while retaining enough intermediate precision for the admitted stored-input illumination fit. Do not add a subnormal exception or change standalone phase-output semantics.
