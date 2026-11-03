# Use absolute error near a cosine zero

**Version 1.0**

- ID: 20261103T044512Z-ce04-coordinator-near-zero-oracle-budget
- Date: 2026-11-03T04:45:12.477197+00:00
- Task: [CE04](../docs/tasks/c-equivalence-known-parameters.md)
- Role: coordinator
- Topic: numerical oracle precision
- Status: confirmed
- Observation: B1 independently found that a relative-only 2e-12 comparison around a 4.9e-17 cosine residual allowed only 9.8e-29 absolute error. The contract permits binary64 rounding differences and fixes no cosine library. The preimplementation test correction uses a preregistered absolute bound plus a well-conditioned near-endpoint control; no product output selected its tolerance.
- Evidence: B1/final.md finding1 and A2-correction-1/report.md through the task evidence pointer; exact proposed test checkpoints retained.
- Suggested action: Bound argument uncertainty in absolute units near a function zero. Use a stable nonzero neighbor to discriminate behavior and retain source-operation inspection where rounded outputs cannot identify an algorithm.
