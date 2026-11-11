# Preserve empty traversals when classifying numerical singularities

**Version 1.0**

- ID: 20261103T033106Z-ce04-coordinator-empty-traversal-domain
- Date: 2026-11-03T03:31:06.644577+00:00
- Task: [CE04](../tasks/c-equivalence-known-parameters.md)
- Role: coordinator
- Topic: source-derived domain
- Status: confirmed
- Observation: Initial static review found that a blanket rejection of zero-cutoff damping excluded valid singleton-height data. The retained source visits no filtering/recombination rows at Y=1, so it never evaluates that division. The accepted contract rejects the singular expression only when visited; for Y>=2 the origin evaluates it before omission overrides.
- Evidence: [CE04 operation and domain contract](../contracts/c-equivalence-known-parameters-v1.md); source-review-2 finding2 and source-review-2-delta ACCEPT through the task's sole evidence pointer. Static source/math review, no retained C execution.
- Suggested action: Trace actual evaluation and empty-loop cases before converting a helper's singular formula into a whole-call rejection rule.
