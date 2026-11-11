# External compatibility and native capabilities: resolved

**Version 1.0**

- Record kind: disposition
- ID: 20261111T182059Z-lessons-doctor-01-coordinator-b11-resolved
- Date: 2026-11-11T18:20:59.467994+00:00
- Task / deciding role: [LESSONS-DOCTOR-01](../../tasks/lessons-doctor-first-pass.md), coordinator after independent policy acceptance.
- Lesson IDs: the exact IDs in the per-lesson decisions below; each appears once in this record.
- Finding IDs / scope: per-lesson mapping below. Grouping is a semantic view, not proof of a common defect or blanket resolution.
- State: resolved
- Completion conditions: per-lesson conditions below; tracked does not mean resolved.
- Basis / evidence: baseline b05fc782522a81ebd92c10726dac731a26e5a026; current repository inspection and the explicitly named retained checks/isolated probes. No full product verification was run for this report. Missing historical/private artifacts and platform limits remain explicit.
- Work links: per-lesson links below, or none because no current correction is commissioned for that scope.
- Relationships: no earlier disposition exists at this cutoff; these records supersede none. Related observations and narrow observation corrections remain intact. No automatic duplicate resolution is inferred.
- Revisit: per-lesson triggers/owner below. New conflicting evidence requires a new explicitly scoped disposition.

## 20260930T201435Z-setup-coordinator-native-boundary-compatibility

- Lesson: [original observation](../20260930T201435Z-setup-coordinator-native-boundary-compatibility.md)
- Finding IDs / scope: none; no actionable finding established; Historical doctor native --sandbox/--approve-for-me option-pair incompatibility only.
- Basis / evidence: The reported incompatible pair is absent in the current launcher: check mode supplies sandbox read-only; default supplies approve-for-me alone. Current public tests reject the combination. The setup record identifies the corrected candidate and exact canonical, fresh D, real default/check and CI evidence. This resolves only the historical option-pair defect, not compatibility with every future native CLI.
- Evidence pointers: `docs/lessons/20260930T201435Z-setup-coordinator-native-boundary-compatibility.md`; `devtools/src/simrecon_devtools/delivery.py:35`; `tests/test_delivery.py:160`; `docs/tasks/setup-plan.md:26`
- Completion conditions: For this exact scoped claim, the implementation/procedure and retained verification evidence cited below establish the stated result.
- Work links: none; scoped knowledge/decision only, evidence retained below
- Revisit: Recheck live parser compatibility when the selected native executable/options change. Owner: Coordinator of the next applicable authorized task.
