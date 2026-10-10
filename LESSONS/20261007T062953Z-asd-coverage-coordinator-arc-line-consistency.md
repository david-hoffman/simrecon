# Complete-execution gates can mask native report contradictions

**Version 1.0**

- ID: 20261007T062953Z-asd-coverage-coordinator-arc-line-consistency
- Date: 2026-10-07T06:29:53Z
- Task: [ASD-COVERAGE-01](../docs/tasks/asd-coverage-policy.md)
- Role: coordinator
- Topic: native coverage evidence migration
- Status: confirmed
- Observation: fresh bounded review round 2 demonstrated a passed public verification receipt with no executed sample statements but both sample branches reported executed, including a source marked missing. Individually consistent list lengths/counters do not establish consistency between statement and branch evidence. The previous complete-statement requirement rejected this input and masked the missing invariant.
- Evidence: candidate 4c089d8bba604278db4e0d29286056aec2855beb; independent public probe and receipt are retained through the task's external evidence pointer. Root confirmed its passed status/no problems. Locked Coverage.py 7.16.2 CoverageData.lines() derives positive executed lines from both arc endpoints; its [official analysis](https://raw.githubusercontent.com/nedbat/coveragepy/7.16.2/coverage/results.py) filters executed lines to statements and derives missing statements. The root opened that analysis and read the installed producer. Four independent native-positive helper probes passed, including zero/partial/negative-exit cases.
- Suggested action: reject executed positive arc endpoints present in measured missing lines; preserve negative exits and legitimate nonstatement endpoints. Audit native evidence invariants separately from percentage acceptance during a gate migration. This observation supplements the partial-counter lesson and grants no new scope.
