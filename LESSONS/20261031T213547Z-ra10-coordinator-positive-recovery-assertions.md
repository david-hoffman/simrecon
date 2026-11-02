# Require a positive inference outcome directly

**Version 1.0**

- ID: 20261031T213547Z-ra10-coordinator-positive-recovery-assertions
- Date: 2026-10-31T21:35:47.820426+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: test-oracle value
- Status: confirmed
- Observation: B1 found that the original RA10 recovery test checked source accuracy only if phase recovery had already happened. A seed-only result could avoid that assertion. The corrected author checkpoint declares a fixed command-derived candidate and unconditional phase/prediction targets before product observations.
- Evidence: ../artifacts/ra10/packets/B1-public-findings.md; ../artifacts/ra10/roles/A1/correction-1/derivation.md. These are test/oracle findings; product inference had not run.
- Suggested action: Separate stored-point diagnostic agreement from a declared successful-inference outcome; test both when the contract requires both.
