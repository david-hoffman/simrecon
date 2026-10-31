# Outer verifier Python differs from the scientific test interpreter

**Version 1.0**

- ID: 20261031T141049Z-ra09-coordinator-verifier-test-interpreters
- Date: 2026-10-31T14:10:49.218866+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator
- Topic: CI environment provenance
- Status: confirmed in both original hosted runs
- Observation: The successful Ubuntu 24.04 and macOS 15 receipts described outer verifier Python 3.12.3 and 3.15.2. Original locked-sync and pytest headers independently showed CPython 3.13.12 for both scientific test suites. These values describe different processes; the outer receipt field alone cannot identify the product-test interpreter.
- Evidence: artifacts/ra09/ci/qualification-support-1/interpreter-association-1.json; ci/provider-originals-1/{run,ubuntu-job,macos-job,ubuntu-job-log,macos-job-log}.stdout; original provider ZIP digests in each download receipt. Run 41205922086, attempt 1.
- Suggested action: Associate interpreter identity with each actual command and process. Preserve the original headers and distinguish verifier, scientific tests and isolated wheel import.
