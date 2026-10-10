# Zero exit status did not establish stdin probe execution

**Version 1.0**

- ID: 20261009T132557Z-volume-recombine-01-root-explicit-stdin-execution
- Date: 2026-10-09T13:25:57.990991+00:00
- Task: [VOLUME-RECOMBINE-01](../docs/tasks/volume-recombination.md)
- Role: root
- Topic: source-free diagnostic transport
- Status: confirmed
- Observation: the v1 file runner returned status 0 for one piped `/dev/stdin` probe without executing its statements. B1 rejected that attempt as evidence, then demonstrated execution using a padded probe. Read-only heredocs also failed before Python. A new explicit stdin mode reads and compiles the supplied input once and rejects empty input.
- Evidence: ignored `artifacts/volume-recombination-execution/support-b-completion-audit-01.json` preserves the failed and unexecuted attempts; `support-stdin-v2-proof-round-01-20261009T132000Z.json` records 35 passing same-environment synthetic controls. Original helper and proof bytes remain unchanged. Locked Python 3.13.12 and pytest 9.1.1 on macOS arm64.
- Suggested action: use the proved explicit `--stdin` mode with a quoted pipe and an execution marker for read-only public probes. Preserve actual status and output; no execution follows from status alone. The helper supplies diagnostics, not isolation or a scientific verdict.
