# Stationarity alone cannot certify least-squares backward accuracy

**Version 1.0**

- ID: 20261006T034103Z-nf02-intake-stationarity-limit
- Date: 2026-10-06T03:41:03.397519+00:00
- Task: [NF02 Proposal 3](../docs/tasks/known-phase-separation.md)
- Role: intake coordinator with report-only numerical adviser
- Topic: numerical acceptance oracle
- Status: confirmed mathematical limitation; proposed contract remains pending owner approval
- Observation: A scale-relative stationarity inequality can accept arbitrarily large errors along the smallest right singular vector when its tolerance times the squared condition number reaches one. For zero observations and `z_hat=t*v_min`, the exact optimality defect norm is `sigma_min(K)^2*abs(t)` while the proposed relative allowance contains `eta*||K||_2^2*abs(t)`. When the latter coefficient is at least the former, every `t` passes although the exact coefficient vector is zero. This is algebra, not a measured product failure.
- Evidence: [Proposal 3 accuracy definition and finite derivation](../docs/contracts/known-phase-separation-v2.md#independently-checkable-accuracy); [LAPACK least-squares error analysis](https://netlib.org/lapack/lug/node83.html), opened during October 5 intake. No product solver, test probe or implementation source supplied this finding.
- Suggested action: Use an independently assessed normwise backward-error oracle when promising stable least-squares accuracy; use stationarity as supplemental evidence. Approve conditioning/digit requirements explicitly rather than treating rank as accuracy. This lesson grants no scope or budget authority.
