# Masked-array preservation requires two independent observations

**Version 1.0**

- ID: 20261012T030103Z-empirical-transfer-coordinator-masked-array-payload-preservation
- Date: 2026-10-12T03:01:03.610675+00:00
- Task: [Empirical transfer consumption](../docs/tasks/empirical-transfer-consumption.md)
- Role: coordinator
- Topic: test oracle and delivery preservation
- Status: confirmed
- Observation: Raw correction fresh B02 independently confirmed that the original tree equality helper could miss changes to a mask or the underlying payload at masked positions. Explicit snapshots and comparisons of both arrays, with unchanged/mask/visible-payload/hidden-payload controls, now guard the rejected-call preservation promise.
- Evidence: [Contract](../docs/contracts/raw-calibration-validation-proofs-v1.md), [test](../tests/test_raw_point_bead_calibration.py), and local raw-calibration-correction/B02/final.txt and A01/mask-correction-handoff.md under artifacts/empirical-calibration-consumption-20261011. Independent source-free pytest run: 247 passed on Python 3.13.12, macOS arm64.
- Suggested action: When the public contract preserves a masked array, observe both its mask and all underlying payload values; comparing only visible values does not establish that promise.
