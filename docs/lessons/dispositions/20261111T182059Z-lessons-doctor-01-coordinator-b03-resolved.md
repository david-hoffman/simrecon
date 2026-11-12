# Discriminating contract-based test oracles: resolved

**Version 1.0**

- Record kind: disposition
- ID: 20261111T182059Z-lessons-doctor-01-coordinator-b03-resolved
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

## 20261002T175150Z-mrc-conversion-coordinator-positive-key-contract-gap

- Lesson: [original observation](../20261002T175150Z-mrc-conversion-coordinator-positive-key-contract-gap.md)
- Finding IDs / scope: none; no actionable finding established; Historical rejection of the sole approved M45/M46 wavelength override keys00 and U+0660.
- Basis / evidence: Current harmonization accepts decimal strings and normalizes effective channel indices via int while retaining raw config. M45/M46 exercise ASCII00 and Arabic-Indic0 through Python/CLI with independent output/provenance checks. Architecture intake records the C2 correction,58-case canonical pass and fresh D2 acceptance. This resolves the named historical rejection, not all possible alias policies or all positive inputs.
- Evidence pointers: `docs/lessons/20261002T175150Z-mrc-conversion-coordinator-positive-key-contract-gap.md`; `src/simrecon/io/metadata.py:135`; `src/simrecon/io/metadata.py:188`; `tests/test_mrc_conversion_keys.py:277`; `docs/tasks/architecture-intake.md:57`; `docs/tasks/architecture-intake.md:58`
- Completion conditions: For this exact scoped claim, the implementation/procedure and retained verification evidence cited below establish the stated result.
- Work links: none; scoped knowledge/decision only, evidence retained below
- Revisit: Revisit if channel-key grammar, alias-collision policy or metadata normalization changes. Owner: Coordinator of the next applicable authorized task.
