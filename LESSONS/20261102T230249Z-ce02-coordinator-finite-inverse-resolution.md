# A finite phase inverse can still be unusable

**Version 1.0**

- ID: 20261102T230249Z-ce02-coordinator-finite-inverse-resolution
- Date: 2026-11-02T23:02:49.558055+00:00
- Task: [CE02](../docs/tasks/c-equivalence-preprocessing.md)
- Role: coordinator
- Topic: numerical resolution
- Status: confirmed observations; no universal accuracy claim
- Observation: The original supplied P4/Q3 clustered design at a=1e-4 rad returned finite B/E coefficients with wrong signs. Independent D found a large left-inverse residual after the full local and platform suites had passed; the new public regression reproduces the failure.
- Evidence: [Accepted mathematical contract](../docs/contracts/c-equivalence-preprocessing-v1.md), [supplemental public regression](../tests/test_c_preparation.py); original candidate 3c68fca859e639a7c8c0570304a4d3be47291fb3. Durable D1/final.md SHA-256 51dda1d9b5e29180f4cce9753d0bf22e6bbeebe7bd4e65c83e0b2e9072aea4ca; B6-accepted checkpoint 3e5e77a2fcf33e12324df3b357603fe7549ed7ca0d4c72bdaff43aa82e0758be. C correction source commit 5317337fe130cd9761dde4ce8813f285b7185e9a has 232 focused passes; renewed full/platform/D evidence remains a separate requirement.
- Suggested action: When a contract includes square/overdetermined and resolved/clustered cases, assess the meaningful combination rather than relying on separate examples or finite coefficients. Preserve the same unweighted mathematics and resolved positive inputs; no new condition cutoff follows.
