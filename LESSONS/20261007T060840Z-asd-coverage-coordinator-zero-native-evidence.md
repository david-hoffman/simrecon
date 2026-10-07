# Zero percent still needs native measurement evidence

**Version 1.0**

- ID: 20261007T060840Z-asd-coverage-coordinator-zero-native-evidence
- Date: 2026-10-07T06:08:40.532143+00:00
- Task: [ASD-COVERAGE-01](../docs/tasks/asd-coverage-policy.md)
- Role: coordinator
- Topic: coverage report fixture
- Status: confirmed
- Observation: With Coverage.py 7.16.2, executing only an unowned launcher in the real-command regression produced no native branch evidence. Executing an empty owned script instead produced valid branch-capable measurement while nonempty owned files remained unexecuted. A zero percentage and unavailable instrumentation are distinct outcomes.
- Evidence: The diagnosed second scoped suite had 1 failure/95 passes; the corrected suite passed 96 cases. The two real-command cases also passed under subprocess instrumentation. [Public regression](../tests/test_verification_receipt.py), `test_project_coverage_commands_allow_advisory_percentages`, in commit `3976aa5`; Python 3.13.12, Coverage.py 7.16.2. Final candidate results remain in PR #9 and the task evidence pointer.
- Suggested action: For advisory-percentage tests, retain required native metadata and reports. Use a legitimate instrumented zero-execution fixture rather than treating missing measurement as zero coverage.
