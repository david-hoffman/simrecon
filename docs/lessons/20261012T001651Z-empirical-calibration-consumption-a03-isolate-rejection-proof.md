# Isolate rejection proof from shared error-code failures

**Version 1.0**

- ID: 20261012T001651Z-empirical-calibration-consumption-a03-isolate-rejection-proof
- Date: 2026-10-12T00:16:51Z
- Task: empirical-calibration-consumption supplemental A03
- Role: A03
- Topic: oracle isolation
- Status: confirmed
- Observation: A spacing-grammar rejection test also had a canonical-frequency mismatch with the same public error code. It could pass without proving the intended container/scalar rule. Matching-grid positives and singleton domain controls removed that overlap; 397 focused tests passed after correction.
- Evidence: artifacts/empirical-calibration-consumption-20261011/A03/report.md, correction.patch and candidate-focused-tests.log; baseline 2080b9cb82de2a8df543a5d70eba1e2631f3f236; source-free focused pytest on Python 3.13.12/NumPy 2.5.3/macOS arm64.
- Suggested action: For a shared-code rejection assertion, pair the intended negative with an otherwise-identical valid control and remove unrelated invalid fields before claiming decision-specific proof.
