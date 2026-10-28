# Separate illumination error from source recovery with a frozen-source control

**Version 1.0**

- ID: 20261028T143227Z-pr53-recovery-coordinator-illumination-control
- Date: 2026-10-28T14:32:27.273363+00:00
- Task: [PR53 recovery investigation](../docs/tasks/pr53-recovery-investigation.md)
- Role: coordinator
- Topic: scientific diagnosis
- Status: confirmed for one recorded exposure
- Observation: With the same paired reference source and forward operator, orientation 0 phase 0 image error was 1.70% using true illumination and 45.64% using frozen estimated illumination. The original reconstructed-source prediction error on that exposure was 66.31%. This makes illumination mismatch a concrete concern without changing the specimen or claiming additive causal shares.
- Evidence: [Controlled measurement](../docs/reports/pr53-recovery-investigation.md#first-controlled-measurement) and its linked exact input/output hashes; unchanged merged runtime tree 73c1ffb702c04dc68cb4d53f01b3a937d0860ec1, Python 3.13.12, NumPy 2.5.3. Outer resource wrapper failed after sealed numerical outputs; resource limits remain explicit.
- Suggested action: Extend the control across exposures, then separate convergence and calibration effects under matched assumptions. Do not replace a sparse sample solely to improve the headline source error.
