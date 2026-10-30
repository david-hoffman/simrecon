# Exact per-call mass does not imply exact cross-call scaling

**Version 1.0**

- ID: 20261030T073110Z-ra05-coordinator-cross-call-mass-roundoff
- Date: 2026-10-30T07:31:10Z
- Task: [RA05](../docs/tasks/reference-alignment-ra05.md)
- Role: coordinator
- Topic: Numerical test oracle
- Status: confirmed
- Observation: A fresh public-array SVD calculation satisfied the separator's real-coordinate allowances but had a nonzero exact mass-scaling residual (2.22e-14 signal units for an eightfold input scale). The old cross-call exact equality rejected it. The corrected relation uses the sum of the two separator error budgets; each call still reports the exact Fraction sum of its own returned dc samples.
- Evidence: [Separator contract](../docs/contracts/volume-phase-separation-v1.md) and [corrected public test](../tests/test_reference_alignment_ra05.py). Retained local B2 review: artifacts/ra05/B2/final.txt, SHA256 d300bf0f5a20cc067a2f967e40a0a71f4ee2437340679e8f21c197027ffab024; A3 qualification uses the locked Python3.13.12/NumPy2.5.3 environment.
- Suggested action: Use exact equality for the per-call metadata relation. Derive cross-call scientific comparisons from the operation's stated error allowances. A power-of-two input scale alone adds no bitwise-output promise. This lesson supplies no new authority or gate change.
