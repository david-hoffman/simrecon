# Finite-search oracles must bind probes to bracket candidates

**Version 1.0**

- ID: 20261106T223133Z-ce08-coordinator-probe-coordinate-link
- Date: 2026-11-06T22:31:33.748382+00:00
- Task: [CE08 independent acceptance](../docs/tasks/c-equivalence-independent-acceptance.md)
- Role: coordinator, recording fresh blind B1 evidence
- Topic: finite numerical procedure oracle
- Status: confirmed
- Observation: B1 demonstrated that a checker could validate regression at a reported candidate and separately validate bracket updates while never requiring that candidate to equal the bracket probe. A synthetic magnitude probe displaced by 0.00001 cycles/um passed the original checker and broad final-parameter bounds. This was a test-oracle defect; no product call occurred. A acknowledged the finding and correction remains under independent review.
- Evidence: CE08 B1-F01, durable B1-report.md via the task evidence pointer; report SHA-256 2a65afef7f97d73fc9e145db2cd1782959893e772b49e1cbfb3795a85b7e5c53. The report preserves the source-free synthetic reproduction and unchanged authored checkpoint.
- Suggested action: Derive each prescribed probe from the preceding finite search state, bind its objective to that candidate, and review those links independently. Endpoint proximity alone does not establish an ordered finite decision procedure.
