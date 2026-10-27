# Per-process file limits also constrain coverage databases

**Version 1.0**

- ID: 20261027T000006Z-pr53-coordinator-file-limit-caps-coverage
- Date: 2026-10-27T00:00:06.532415+00:00
- Task: [PR53](https://github.com/david-hoffman/simrecon/pull/53)
- Role: coordinator
- Topic: test instrumentation and operating-system resource limits
- Status: confirmed
- Observation: An existing partial-I/O test imposed a 128-byte file limit on its real CLI child. The test passed, while the inherited subprocess coverage writer produced a 128-byte malformed SQLite database and the native combination phase failed. The isolated reproduction retained all three input databases before combination; their sizes were 122,880, 128 and 167,936 bytes.
- Evidence: [Public reproduction record](../docs/operations/evidence/pr53-H2-reproduction.json), source commit 9fe16e5f00591d5f0556a584fc6b9bcc2e73c5f9 and accepted test checkpoint 0fe9133d…; Python 3.13.12/Coverage 7.16.2 on Darwin arm64. The single instrumented test returned 0 and the unchanged native combination phase returned 2. Raw original receipts and inputs remain retained locally.
- Suggested action: Qualify the intended partial-write failure together with actual subprocess instrumentation. Choose a valid fixture and resource limit that permit the observer to persist its data, and run native combination with warnings treated as errors in the combination process.
