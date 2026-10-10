# A bounded partial-branch counter can still contradict native evidence

**Version 1.0**

- ID: 20261007T061928Z-asd-coverage-coordinator-partial-counter-integrity
- Date: 2026-10-07T06:19:28Z
- Task: [ASD-COVERAGE-01](../docs/tasks/asd-coverage-policy.md)
- Role: coordinator
- Topic: native coverage report integrity
- Status: confirmed
- Observation: fresh bounded review reproduced two public verifier successes with contradictory partial-branch counters despite matching file/global sums. An upper bound against missing branches allowed both an overstated zero-execution counter and an understated partial-execution counter. These are report-integrity defects even when percentages are advisory.
- Evidence: bounded review round 1 of candidate b64c13cc9e2cfc310b3a61b24a4d3355f944d78d; [public regression cases](../tests/test_verification_receipt.py) named test_partial_counter_matches_native_missing_arc_sources both failed before the correction under Python 3.13.12. Coverage.py 7.16.2 [official Analysis.__post_init__](https://raw.githubusercontent.com/nedbat/coveragepy/7.16.2/coverage/results.py) derives the partial counter from missing arcs whose source is absent from missing_lines. The coordinator opened that source; final candidate/check identities remain in the task's external evidence pointer.
- Suggested action: validate this counter against native missing arcs and missing lines; retain positive partial/zero cases and obtain fresh independent review after the correction. This observation grants no additional scope.
