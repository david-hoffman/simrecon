# Derive finite-sum oracles from actual supplied operands

**Version 1.0**

- ID: 20261103T051249Z-ce04-coordinator-actual-finite-operands
- Date: 2026-11-03T05:12:49+00:00
- Task: [CE04](../tasks/c-equivalence-known-parameters.md)
- Role: coordinator
- Topic: ideal arithmetic versus finite public inputs
- Status: confirmed
- Observation: A singleton-height control preserved every prepared coefficient, as required, but its image test demanded exact ideal intensity 3. The actual public bands contained center DC 3 and side-even DC -2^-52. The declared zero-carrier real finite sum is 3-2^-51, one binary64 unit in the last place below 3. Independent source review confirmed that supplied finite coefficients remain authoritative and clarified the ideal example without adding a tolerance or residual-removal rule. The invalid exact comparison was not product-red evidence.
- Evidence: [CE04 finite-input and empty-traversal contract](../contracts/c-equivalence-known-parameters-v1.md); public/y1-finite-operands-finding.md and source-review-2-roundoff/final.md through the task's sole evidence pointer. The independent rational calculation used no product source or historical executable.
- Suggested action: Distinguish ideal raw-input anchors from downstream operations on actual finite intermediates. Preserve independently justified precision and closed amplitude controls; never round the product or remove residual coefficients to force an ideal constant.
