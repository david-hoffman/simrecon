# Process display is not a lifetime identity

**Version 1.0**

- ID: 20261029T103416Z-R5-protocols-a3-A-ps-display-transition
- Date: 2026-10-29T10:34:16Z
- Task: R5-protocols-a3
- Role: fresh blind A3
- Topic: test observer qualification
- Status: confirmed observation; teardown explanation is an inference
- Observation: During a genuine six-second native subprocess timeout, the observed download child retained PID, parent and second-resolution start text while ps changed its executable display to a parenthesized Python name with state S. Earlier observations had its original executable path and R/S state. The PID was strictly absent after natural application failure, before harness rescue. A separate real live/zombie/reaped control showed that a zombie must still count present. These observations do not establish a kernel birth identity or general OS timing guarantee.
- Evidence: artifacts/test-consolidation/R5/A-results/closure-01.json and original .stdout/.stderr; reader-evidence/authored-runs/standalone-bd0b551bc38343828b015941286b9479/observations/actual-reader-ff9534ae13c74ef9b174b5de7a27ab97.json; diagnoses.md; corrected reader-target-03 and closure-03 results. Host macOS 27.0.1 arm64; Python 3.13.12. Exact executable and environment identities are in environment-01.stdout.
- Suggested action: Keep original/current state and display metadata in failures. Qualify progress only while the original live identity/display is present. A changed display supplies no additional live-progress proof. Require actual PID absence separately; do not treat zombies or reused PID slots as absent. Independently qualify this observer on other supported hosts before generalizing it.
