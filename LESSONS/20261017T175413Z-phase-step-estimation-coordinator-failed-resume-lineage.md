# A failed resume attempt does not establish author lineage

**Version 1.0**

- ID: 20261017T175413Z-phase-step-estimation-coordinator-failed-resume-lineage
- Date: 2026-10-17T17:54:13.481922+00:00
- Task: docs/tasks/phase-step-estimation.md
- Role: coordinator
- Topic: native evidence
- Status: confirmed
- Observation: A02 used an incorrect remembered resume UUID. The CLI returned status1 after0.492700167s, with an empty journal and no final report. Those bytes establish a failed lookup attempt, not an opened author session or valid lineage. The later A03 used the actual A01 thread.started identity. A success-only lineage check initially rejected retaining the failed attempt; a scoped correction keeps failed history unqualified while preserving strict successful-owner checks.
- Evidence: artifacts/phase-step-estimation-20261016/A02/launch.json, events.jsonl, stderr.log and diagnosis.json; A01/events.jsonl; A03/launch.json; support-setup/coordinator-failed-resume-precheck01.json; H02/assessment.txt and H02/final.txt. H02 independently accepted only the bounded setup and retained unknown lineage for generic failed resumes.
- Suggested action: Read the actual observed initial thread identity before a resume. Preserve failed lookup records separately from successful formal-role evidence; never infer session creation or owner lineage from UUID syntax alone.
