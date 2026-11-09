# An algebraic cancellation is not a finite branch proof

**Version 1.0**

- ID: 20261104T045108Z-ce06-coordinator-exact-cancellation-oracle
- Date: 2026-11-04T04:51:08.666539+00:00
- Task: CE06 acquisition modes
- Role: coordinator
- Topic: Numerical oracle and operation-domain test
- Status: confirmed
- Observation: Four old repeated off-side cases demanded a zero-noise rejection because nonidentical prepared inputs were proportional in real arithmetic. Independent binary64 direct sums left positive selected noise after scaling, Fourier transforms and weighted subtraction, even with a positive initial signal margin. This disproved the unconditional test expectation. The separate identical-input case still gives exact cancellation with equal half weights.
- Evidence: [Acquisition contract, off/on Fourier combination](../docs/contracts/c-equivalence-acquisition-modes-v1.md), sections 4 and 16; source-free pure arithmetic counterexample and revised preparation cases in the CE06 checkpoint evidence. The probe made no product call. Its small positive residuals are examples, not acceptance bounds.
- Suggested action: For a selected zero-divisor rejection, establish an operation-level exactness argument or use an independently conditioned alternate case. Keep a separate exact-zero witness and paired positive case. Do not add a numerical floor to satisfy an algebraic test expectation.
