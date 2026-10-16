# Error-code tests need isolated invalid preconditions

**Version 1.0**

- ID: 20261016T031139Z-empirical-trilinear-coordinator-isolate-error-preconditions
- Date: 2026-10-16T03:11:39.566052+00:00
- Task: [Empirical trilinear transfer](../docs/tasks/empirical-trilinear-transfer.md)
- Role: coordinator observing blind A/B review
- Topic: error oracle validity
- Status: confirmed
- Observation: The initial target-frequency-range test also violated source coverage. Its single expected error code therefore imposed a validation precedence the contract leaves unspecified. An exact same-geometry source with tolerance-admitted finite metadata isolates target rounding overflow; doubling target spacing supplies a valid finite companion.
- Evidence: Accepted test checkpoint `52de983c34f40e25b1cfc8a28f70847b794bf5cb`, `test_target_unrepresentable_frequency_error`, `test_tolerance_admitted_extreme_source_with_finite_target` and their independent self-check in [the public test module](../tests/test_empirical_trilinear_transfer.py). [The contract](../docs/contracts/empirical-trilinear-transfer-v1.md) leaves simultaneous-invalid precedence unspecified. Fresh B02 accepted exact test SHA256 `e54f420ccc09cabb9345751fb17f8aa13c7ef819cdda399f7c4bbfd9b55aeff3`; review/evidence pointer is in the task's local Current state. Source-free CPython3.13.12 tests executed the precondition self-check; the adapter was absent, so this is no product-red claim.
- Suggested action: When asserting a particular boundary error, independently verify the other preconditions or allow every outcome the contract permits. Retain a valid companion that challenges accidental extra restrictions.
