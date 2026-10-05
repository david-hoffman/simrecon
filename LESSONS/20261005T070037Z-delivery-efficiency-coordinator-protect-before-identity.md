# Protect output even when candidate identity is unavailable

**Version 1.0**

- ID: 20261005T070037Z-delivery-efficiency-coordinator-protect-before-identity
- Date: 2026-10-05T07:00:37Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: verification output safety
- Status: confirmed
- Observation: Output protection was bypassed when another tracked file was missing: the initial candidate wrote its receipt over tracked candidate/config files. The independently reviewed public tests reproduced this in disposable repositories.
- Evidence: `1a021f485c387b57a0ab8bb895fc1982d6856cc9`, [verify.py](../scripts/verify.py); [test_verification_receipt.py](../tests/test_verification_receipt.py), `test_v4_output_protection_with_missing_tracked_file`; B4 accepted the oracle and reproduced product-red evidence.
- Suggested action: Validate output destinations using independent tracked-name/Git metadata discovery before content fingerprinting. Fail closed when the protection inputs are unavailable.
