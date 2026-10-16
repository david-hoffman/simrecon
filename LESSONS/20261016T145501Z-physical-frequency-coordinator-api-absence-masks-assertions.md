# API absence can mask test-local numerical assertions

**Version 1.0**

- ID: 20261016T145501Z-physical-frequency-coordinator-api-absence-masks-assertions
- Date: 2026-10-16T14:55:01.588284+00:00
- Task: [Explicit frequency sampling](../docs/tasks/empirical-frequency-sampling.md)
- Role: coordinator
- Topic: independent oracle validation
- Status: confirmed
- Observation: The owned oracle sanity check passed, while missing-API setup prevented sampler test bodies from executing. Fresh B02 independently executed a range test's local precondition and found it checked the wrong rotated component. For the stored positive quarter-turn example, real/Fmax was about3.90e-17 and imaginary/Fmax about1.27279; the assertion required real/Fmax>1.2. The shared numerical oracle was correct. This was a test defect before any sampler call, not product-red.
- Evidence: Reviewed test checkpoint157ef16acd6b137cbf05227c4097ce71f126e3dd, tests/test_empirical_frequency_sampling.py:784–788; contractSHA256bf465c5d816fafeaa78b11b0cba0b41bdfce81479cdbd04175206448ea17d299. Local retained B02/report.md under artifacts/physical-frequency-transfer-20261016/ has SHA256dda868c3eca0651dc31b60d27960bea3176a04c41703d10e145f463e8008e5a1; source-free CPython3.13.12/NumPy2.5.3 public math probe. Its exact precondition failed without invoking the absent sampler. Fresh correction acceptance remains a separate checkpoint.
- Suggested action: When APIabsence blocks test bodies, evaluate independent test-local numerical preconditions separately, then retain diagnosed author correction and fresh review. This observation grants no additional edit authority or new gate.
