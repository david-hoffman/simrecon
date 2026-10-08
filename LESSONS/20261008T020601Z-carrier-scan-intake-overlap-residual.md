# A perfect single-pair overlap fit does not identify a carrier

**Version 1.0**

- ID: 20261008T020601Z-carrier-scan-intake-overlap-residual
- Date: 2026-10-08T02:06:01.706144+00:00
- Task: CARRIER-SCAN-01; [contract](../docs/contracts/carrier-scan-v1.md)
- Role: intake coordinator with report-only Astra/ultra advice
- Topic: carrier identifiability
- Status: confirmed
- Observation: One nonzero complex overlap pair admits z=y/x and zero fit residual. Different carrier hypotheses can use different overlap pairs. Geometric pair count includes zero-transfer pairs. These diagnostics alone do not establish a unique physical carrier.
- Evidence: The contract's inherited complex scalar least-squares equations and Interpretation and limitations; scoped advisor report retained in the task's ignored execution evidence. This is an algebraic limitation, not an implementation or physical recovery result.
- Suggested action: Expose candidate diagnostics with explicit limitations; a future selection contract must supply its own assumptions and ambiguity behavior.
