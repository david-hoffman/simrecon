# Pytest collection errors can embed source in exception messages

**Version 1.0**

- ID: 20261006T165011Z-otf-calibration-coordinator-collection-diagnostics
- Date: 2026-10-06T16:50:11.884139+00:00
- Task: [OTF-CALIBRATION](../docs/tasks/otf-calibration-implementation.md)
- Role: coordinator
- Topic: blind-role diagnostic qualification
- Status: confirmed
- Observation: With pytest 9.1.1, `--tb=line` still rendered source during an import collection failure. A diagnostic hook retaining traceback locations without lines still leaked the preformatted source inside pytest's `CollectError` message. Synthetic qualification passed only after retaining that wrapper's first message line together with the underlying exception chain. Resolving a virtual-environment Python symlink also selected the base interpreter and lost the installed project; preserving the executable path restored the environment.
- Evidence: Local task evidence `artifacts/otf-execution/diagnostic-qualification.txt`, `diagnostic-probe-qualification.txt` and `execution-record.json`; Python 3.13.12 / pytest 9.1.1 / macOS arm64. The one-off invocation's current SHA-256 is `e21a14ecd684ce09e26c78d545580bfa62c47562bca249ef280c425e205f5953`. Synthetic source markers were absent while warning/exception categories, locations, messages and expected failing exit statuses remained.
- Suggested action: Qualify import, syntax, warning, failure and chained-exception diagnostics before blind probes. Use the virtual-environment executable path without resolving its symlink. This lesson supplies no runtime/check/policy edit authority.
