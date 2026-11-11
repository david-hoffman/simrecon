# Verification prerequisites and execution cost: tracked

**Version 1.0**

- Record kind: disposition
- ID: 20261111T182059Z-lessons-doctor-01-coordinator-b10-tracked
- Date: 2026-11-11T18:20:59.467994+00:00
- Task / deciding role: [LESSONS-DOCTOR-01](../../tasks/lessons-doctor-first-pass.md), coordinator after independent policy acceptance.
- Lesson IDs: the exact IDs in the per-lesson decisions below; each appears once in this record.
- Finding IDs / scope: per-lesson mapping below. Grouping is a semantic view, not proof of a common defect or blanket resolution.
- State: tracked
- Completion conditions: per-lesson conditions below; tracked does not mean resolved.
- Basis / evidence: baseline b05fc782522a81ebd92c10726dac731a26e5a026; current repository inspection and the explicitly named retained checks/isolated probes. No full product verification was run for this report. Missing historical/private artifacts and platform limits remain explicit.
- Work links: per-lesson links below, or none because no current correction is commissioned for that scope.
- Relationships: no earlier disposition exists at this cutoff; these records supersede none. Related observations and narrow observation corrections remain intact. No automatic duplicate resolution is inferred.
- Revisit: per-lesson triggers/owner below. New conflicting evidence requires a new explicitly scoped disposition.

## 20261103T020523Z-ce03-coordinator-external-protocol-lock-parent

- Lesson: [original observation](../20261103T020523Z-ce03-coordinator-external-protocol-lock-parent.md)
- Finding IDs / scope: LESSONS-DOCTOR-01-F002; Current fixture/environment preparation with external evidence root; preserve lock/cache lifecycle.
- Basis / evidence: Current constructor creates overridden RUN but not fixed EVIDENCE; entry creates only the child lock. Root isolated current-class probe reproduces missing-parent FileNotFoundError, succeeds with parent prepared, and preserves preexisting-lock rejection. Missing documented preparation is a concrete fixture/environment gap, not scientific product-red.
- Evidence pointers: `docs/lessons/20261103T020523Z-ce03-coordinator-external-protocol-lock-parent.md`; `tests/shared_node_baseline_public_callers_fixture.py:26`; `tests/shared_node_baseline_public_callers_fixture.py:332`; `tests/shared_node_baseline_public_callers_fixture.py:361`; `tests/test_shared_node_baseline_public_callers.py:52`; `tests/test_shared_node_baseline_public_callers.py:878`; `docs/reports/lessons-doctor-2026-11-11/reader-lock-probe.json`; `docs/contracts/shared-node-baseline-compatibility-v1.md:69`
- Completion conditions: Meet the precise contract and completion conditions in docs/tasks/lessons-reader-reservation-parent.md, then record independently reviewed scoped evidence; intake/publication is not resolution.
- Work links: docs/tasks/lessons-reader-reservation-parent.md
- Revisit: After documentation-prerequisite versus fixture-lifecycle route is settled and independently reviewed, verify absent-parent, prepared-parent, and preexisting-lock controls. Owner: Coordinator of the next applicable authorized task.

## 20261109T061440Z-test-apparatus-coordinator-empty-affinity

- Lesson: [original observation](../20261109T061440Z-test-apparatus-coordinator-empty-affinity.md)
- Finding IDs / scope: LESSONS-DOCTOR-01-F003; Existing test-apparatus optimization task and selected measured canonical target.
- Basis / evidence: The original empty map is no longer current: measured whole-file groups are installed and task retains exact 598.57s full-gate evidence. Remaining measured optimization is already owned by the test-apparatus task: coordinator root serializes heavy runs, named bounded infrastructure worker owns groups, current next action is clean two-worker canonical attempt for selected 300s goal. Reuse that task; do not create duplicate optimization work.
- Evidence pointers: `docs/lessons/20261109T061440Z-test-apparatus-coordinator-empty-affinity.md`; `devtools/src/simrecon_devtools/pytest_policy.py:9`; `docs/tasks/test-apparatus-optimization.md:12`; `docs/tasks/test-apparatus-optimization.md:26`; `docs/tasks/test-apparatus-optimization.md:117`
- Completion conditions: Existing apparatus task must complete the selected exact-candidate 300-second canonical goal with required gates/reviews.
- Work links: docs/tasks/test-apparatus-optimization.md
- Revisit: Existing apparatus task freezes its next exact candidate and completes canonical two-worker run plus required fresh reviews for selected 300-second target. Owner: Coordinator of the next applicable authorized task.
