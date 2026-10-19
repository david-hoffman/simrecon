# Cleanup proof must permit successful alternatives

**Version 1.0**

- ID: 20261019T011447Z-fourier-block-phase-coordinator-conditional-cleanup-oracles
- Date: 2026-10-19T01:14:47.960000+00:00
- Task: FOURIER-BLOCK-PHASE
- Role: coordinator
- Topic: test oracles and data preservation
- Status: confirmed
- Observation: B05 found a static false rejection in a supplemental cleanup test. It denied only literal `ps -axo`, then required both owned processes to remain. A valid query spelling or stronger cleanup could prove disappearance and correctly release the guard. No alternate candidate was executed. The corrected test permits proved cleanup and requires refusal while cleanup remains unproven. B06 independently observed both live-process refusal and conservative refusal after known processes disappeared externally; backup bytes, inode and mode remained intact. Sixteen checks passed on the accepted test checkpoint.
- Evidence: local retained records `artifacts/fourier-block-phase-20261018/B05/review.md`, `B06/review.md` and `B06/acceptance.json`; accepted checkpoint `6d921bc1296a51ab9dc6cd2de5d8c51fee58beae`; [current test boundary](../tests/test_shared_node_baseline_public_callers.py). The original macOS 15 CI process state was unavailable, so these observations do not establish its cause.
- Suggested action: Specify the conditional preservation guarantee from actual owned-process state and available cleanup proof. Permit legitimate successful strategies, preserve a real refusal witness, and record missing proof separately from a passing test.
