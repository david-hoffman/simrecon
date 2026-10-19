# Fractional carrier modulation needs a finite observation meaning

**Version 1.0**

- ID: 20261019T091322Z-continuous-carrier-intake-coordinator-finite-modulation
- Date: 2026-10-19T09:13:22.652268+00:00
- Task: [CONTINUOUS-CARRIER-INTAKE](../docs/tasks/continuous-carrier-intake.md)
- Role: coordinator, report-only intake
- Topic: finite representations
- Status: confirmed algebraic distinction
- Observation: The finite DFT of native samples multiplied by a noninteger phase ramp has a geometric-sum mixing kernel. Integer carrier relocation is its special case. Continuous optical filtering and arbitrary Fourier interpolation need additional conventions and need not give the same objective.
- Evidence: [Exact finite-sum derivation and counterexample](../docs/reports/continuous-carrier-intake.md#exact-finite-sum-derivation-and-a-small-counterexample), baseline PR46 head9740a1234480ef2085b18615f6b40fb5e761624e. Analytic derivation only; no generated-data experiment.
- Suggested action: Settle the finite/exterior/continuous model, origin, signed domains and endpoint conventions in a concrete future contract before blind tests or implementation. This lesson approves no behavior.
