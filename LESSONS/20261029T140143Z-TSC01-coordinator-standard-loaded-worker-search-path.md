# Qualify the actual worker loading mode

**Version 1.0**

- ID: 20261029T140143Z-TSC01-coordinator-standard-loaded-worker-search-path
- Date: 2026-10-29T14:01:43.208842Z
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator, recording verified author/reviewer observations
- Topic: public CLI fixture loading
- Status: confirmed
- Observation: The first validation-worker control started as a script without the repository root on its module search path. The real scripts package was unavailable, so its supposed blocking control never reached the FIFO read. Standard -c/runpy loading then passed success, rejection and actually reached blocking-read controls.
- Evidence: R6 study A cmd-027 failed; cmd-029 passed and retained native request, timeout and process-closure records. The accepted checkpoint map binds the author and fresh B reports. Local checkpoint pointer: `artifacts/test-consolidation/R6-accepted-checkpoints.json`; exact source evidence is indexed locally in `artifacts/test-consolidation/R6-lessons-evidence.json`.
- Suggested action: Qualify the exact public-command loading mode before reusing a child. A failed import is not evidence that a blocking read timed out. This lesson grants no additional edit, gate or execution authority.
