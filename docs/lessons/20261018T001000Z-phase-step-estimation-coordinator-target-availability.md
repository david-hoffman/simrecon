# Link integrity and target availability are separate observations

**Version 1.0**

- ID: 20261018T001000Z-phase-step-estimation-coordinator-target-availability
- Date: 2026-10-18T00:10:00.504202+00:00
- Task: phase-step-estimation-20261016
- Role: coordinator
- Topic: evidence retention
- Status: confirmed
- Observation: All 5,464 retained regular-file pins and 20 literal link strings matched, while ten previously live external fixture targets were unavailable. Loss cause, actor and timing remain unknown. Fresh D03 mapped these targets to disposable adversarial controls or aliases with separately retained required reports; no required input or unique report keeper was missing.
- Evidence: artifacts/phase-step-estimation-20261016/retention-preservation-audit01.json; D03/final.txt SHA256 e77b627fdeebbc24009f18d45e58921f673b893fe8d6d1869c29c8bb705bbe8e; post-D03-material-recheck01.json at candidate d99996fa39abc85abad4887b8ccad06056a9c20e.
- Suggested action: Report regular-file hashes, literal link strings and current target availability separately. Map a missing target to its actual obligation and retained keeper proof before deciding evidence admissibility. Supplemental current-time copies do not restore historical custody. This lesson grants no cleanup or gate waiver.
