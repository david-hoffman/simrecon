# Check test harness integration in the canonical parent environment

**Version 1.0**

- ID: 20261026T201943Z-pr53-coordinator-match-gate-environment-before-long-run
- Date: 2026-10-26T20:19:43.095111+00:00
- Task: [FULL-NOISY-SIMULATION](../docs/tasks/full-noisy-simulation.md)
- Role: coordinator
- Topic: test integration
- Status: confirmed
- Observation: A focused driver suite passed under the source-free diagnostic wrapper, but canonical verification launched ordinary coverage pytest. The shared CLI helper required diagnostic entries in its parent environment. Verification spent 2966.37 seconds in tests and reported 175 failures and 163 setup errors at those preconditions, alongside 10961 passes. These were harness failures before driver execution, not product-red evidence. The blind author's narrow correction established the existing diagnostics in each child and subsequently reported 390 passes in each parent context; independent review and canonical verification remained required.
- Evidence: Local candidate `dcecb4fa07e4ee6c0ad3ae5349a729d2a04b5378`, `make verify UV=<pinned executable>`; retained local bundles `artifacts/pr53-full-study/fullgate2/` and `artifacts/pr53-full-study/roles/A1-correction5/`. All 717 tracked files remained unchanged during the failed gate. Its original receipt, logs and partial coverage files were retained with hashes. The author's ordinary and source-free focused runs overlapped, so their reported 306.21-second durations are not additive wall time.
- Suggested action: Before an expensive canonical gate, exercise a cheap public-entry representative in the same parent environment. Keep diagnostic rendering separate from scientific behavior, make child diagnostics self-contained, and preserve coverage and unrelated inherited instrumentation. Route harness corrections through the existing test owner and fresh review; do not repair this mismatch only by changing the local shell environment while leaving CI unchanged.
