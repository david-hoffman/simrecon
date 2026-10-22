# Phase cancellation needs a common acquisition state

**Version 1.0**

- ID: 20261019T063259Z-raw-phase-motion-coordinator-reference-premise
- Date: 2026-10-19T06:32:59.180771+00:00
- Task: RAW-PHASE-MOTION-INTAKE
- Role: coordinator
- Topic: scientific reference construction
- Status: confirmed
- Observation: In the declared finite fixed-kernel model, aligned specimen motion adds a carrier-projected phase. Balanced commanded phases alone do not establish a comparable zero-order reference when the specimen moves within a cycle; even perfect alignment can collapse effective phase diversity. These are conditional algebraic findings, not experimental validation.
- Evidence: docs/reports/raw-phase-motion-intake.md, counterexamples 2 and 4; independent artifacts/raw-phase-motion-intake-20261018/M01/report.md; existing docs/models/synthetic-3d-acquisition-v1.md. No numerical experiment or reference program was run.
- Suggested action: Before a later raw-motion contract, declare the physical frame and legitimate phase/reference access, and check cancellation on actual effective phases. This lesson approves no new behavior.
