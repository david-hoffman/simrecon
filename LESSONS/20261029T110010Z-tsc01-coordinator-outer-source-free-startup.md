# Protect the outer diagnostic interpreter before it starts

**Version 1.0**

- ID: 20261029T110010Z-tsc01-coordinator-outer-source-free-startup
- Date: 2026-10-29T11:00:10Z
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: blind-role diagnostic boundary
- Status: confirmed
- Observation: The existing source-free wrapper protected its child, but an interrupted outer wrapper printed its own source lines when the outer interpreter had started without the source-free startup environment. The affected blind author stopped. A separate synthetic outer KeyboardInterrupt probe exited with its expected failure status while retaining category and location without source lines after the outer PYTHONPATH was set before startup. This qualifies that tested launch path; it does not make arbitrary launchers source-free.
- Evidence: Preserved R5 protocol A2 continuation STOP-HANDOFF and original streams; A3 preparation and root outer-interruption qualification; accepted A3/B launch environment and explicit pytest-mode receipts. Exact paths, hashes, candidate identities and all failed attempts are bound in artifacts/test-consolidation/current-state.json and its retained role manifests. Python 3.13.12 on the recorded macOS host. No wrapper implementation change was made.
- Suggested action: Qualify the outer process as well as children before blind checks. Install the existing source-free startup path before starting outer Python, use explicit pytest mode for pytest, and capture original streams from startup. Stop blind work after an exposure; clearing context does not restore blindness. This lesson adds no edit or launch authority.
