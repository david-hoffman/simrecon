# Large input declarations can exhaust Make's child argument envelope

**Version 1.0**

- ID: 20261016T212410Z-volume-carrier-diagnostics-coordinator-make-input-transport
- Date: 2026-10-16T21:24:10.140537+00:00
- Task: [Volume carrier diagnostics](../docs/tasks/volume-carrier-diagnostics.md)
- Role: coordinator
- Topic: verification evidence transport
- Status: confirmed for the observed local Make/platform; universal duplication mechanism remains an inference
- Observation: A harmless ignored Makefile invoking only `/usr/bin/true` with the actual 2,552 example-input declarations failed with `Argument list too long`. The argument payload was 365,424 bytes and the reported operating-system argument limit was 1,048,576 bytes. The outer invocation was below that limit; Make's forwarding/export behavior can consume a larger child envelope. This is an evidence-transport failure, not a product or scientific-test failure.
- Evidence: `artifacts/volume-carrier-diagnostics-20261016/support-qualification/argument-envelope-probe01.json`, the retained probe Makefile, and `argument-envelope-diagnosis01.md`. The probe ran on the actual local macOS environment and invoked no installed verification gate or product code.
- Suggested action: Measure the complete child envelope before expensive execution. For this demonstrated helper scope, use a pinned complete per-file manifest and independent before/after/current file hashing while keeping the canonical gate and selected coverage obligations unchanged. A manifest pointer alone does not establish member custody or authorize omission.
