# Error vocabulary is not a numerical-cause oracle

**Version 1.0**

- ID: 20261102T230249Z-ce02-coordinator-diagnostic-causality
- Date: 2026-11-02T23:02:49.558055+00:00
- Task: [CE02](../tasks/c-equivalence-preprocessing.md)
- Role: coordinator
- Topic: public error observation
- Status: confirmed observations; no universal accuracy claim
- Observation: The first supplemental exception assertion rejected legitimate inverse/solver messages. A negative grammar rewrite also rejected valid descriptions of failed numerical outputs. Removing those unaccepted restrictions preserved the numerical oracle and accepted public error alternatives.
- Evidence: [Public numerical-error contract](../contracts/c-equivalence-preprocessing-v1.md), [revised supplemental test](../../tests/test_c_preparation.py). Durable B5/final.md documents the vocabulary counterexamples; A1-correction-6/report.md records the removed classifier and probe defect/repair. B6/final.md SHA-256 6745de52b4f0c7984172781fe44bbaa21ce1d37aca559bd9fb12b10e435cbb32 accepts checkpoint 3e5e77a2fcf33e12324df3b357603fe7549ed7ca0d4c72bdaff43aa82e0758be with an explicit causality limit.
- Suggested action: Keep the test observer within the published exception contract. Class and nonempty text cannot prove the backend cause; implementation review must verify it. This observation introduces no diagnostic vocabulary, structured-error interface or new gate.
