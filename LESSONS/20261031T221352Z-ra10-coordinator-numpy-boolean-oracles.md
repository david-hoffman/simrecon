# Normalize a numerical predicate before Python-bool identity checks

**Version 1.0**

- ID: 20261031T221352Z-ra10-coordinator-numpy-boolean-oracles
- Date: 2026-10-31T22:13:52.081146+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: scalar test oracle
- Status: confirmed
- Observation: The accepted RA10 test helper compared a required Python bool flag by identity with a comparison involving a NumPy integer tolerance. The expected value was numpy.bool, so seven permitted layout cases failed despite the contracted flag type. The correction normalizes only the expected predicate and preserves the actual Python-bool type check.
- Evidence: ../artifacts/ra10/packets/A-correction-2-public-findings.md; ../artifacts/ra10/roles/A1/correction-2.cHpObk/handoff.md; ../artifacts/ra10/roles/B4/final.txt. Independent review checked scalar combinations and all95 product cases.
- Suggested action: Test the flag type separately from its mathematical condition; normalize an oracle predicate to the contracted scalar type.
