# Keep mixed data and solver uncertainty in cubic bounds

**Version 1.0**

- ID: 20261106T133205Z-ce07-coordinator-joint-cubic-uncertainty
- Date: 2026-11-06T13:32:05.272084+00:00
- Task: [CE07 public workflow](../docs/tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: conditional numerical-oracle error propagation
- Status: confirmed
- Observation: An independently replayed counterexample under the stated cubic-interpolation perturbation model exposed a missing mixed data/design term, even for an exact cubic underlying curve. The corrected joint square/rectangular enclosure preserved every original raw control and separated pre-subtraction fitted-motion uncertainty from applied-motion uncertainty. This is a finding about the conditional algebraic model, not a certificate for every numerical backend or a historical executable observation.
- Evidence: [public mathematical contract](../docs/contracts/c-equivalence-workflow-v1.md) and [corrected independent oracle](../tests/c_workflow_oracle.py). The task evidence root retains `oracle-advisor-3/report.md`, the sanitized `public/cubic-joint-perturbation-math-findings-3.md`, correction3 joint-model validation, and fresh B4 acceptance of the complete corrected oracle at checkpoint `5461a70c5ed0382702b4678f4badf79ff1aeaa6e5da11d5782e5246dde9fab0b`. B4 independently checked the joint derivations and their explicit solver/Fourier/elementary/equality premises before implementation acceptance work.
- Suggested action: Propagate data and design/solver perturbations jointly through evaluation and state backend premises explicitly. A small observed residual or an exact underlying polynomial does not remove the mixed term. No new backend-certification gate or editing authority follows.
