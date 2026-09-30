# A Git revision did not identify the ignored legacy input

**Version 1.0**

- ID: 20260930T184757Z-setup-coordinator-ignored-input-identity
- Date: 2026-09-30T18:47:57.706047+00:00
- Task: [SETUP](../docs/tasks/setup-plan.md)
- Role: setup coordinator
- Topic: baseline identity
- Status: confirmed
- Observation: The Git baseline was clean, but the source studied for adoption was ignored. HEAD alone could not identify the measured input. Discovery therefore recorded a separate content manifest and checked that the snapshot was unchanged afterward.
- Evidence: [Baseline](../docs/setup/BASELINE.md), [manifest](../docs/setup/evidence/legacy/snapshot-sha256.json), and [after-check](../docs/setup/evidence/legacy/final-baseline-state.json). macOS 27 Apple Silicon; original Make commands ran against an unchanged isolated copy. The manifest SHA-256 is `201d46d1646552c69c453b02e17dfa8d307b895d095904ffcdaec6b3b0244e8d`.
- Suggested action: Doctor should check whether baseline instructions explicitly cover ignored or untracked inputs. If that is an instruction gap, propose a small evidenced clarification. This lesson does not determine doctor's verdict, authorize a commit, or make the unbuilt legacy source a valid scientific oracle.
