# Native role launches

This is coordinator guidance. The launched role performs its packet directly; it does not launch another role. Use a new native `codex exec` process for each A/B/C/D role. Do not resume/fork implementation history into review. Use supported memory/delegation controls, one packet/worktree/report destination and no automatic retry.

Record applicable `command -v codex`, `codex --version` and `codex exec --help` evidence when missing/stale. The observed parser accepts:

```sh
codex exec --ignore-user-config --disable memories --disable multi_agent \
  --sandbox read-only --model <packet-model> --json \
  -C /absolute/path/to/worktree -o /absolute/path/to/report.txt \
  - < /absolute/path/to/packet.txt
```

Select `workspace-write` for authorized A/C authoring. `--approve-for-me` already selects workspace-write; do not combine it with explicit `--sandbox`. Set reasoning only with supported native configuration. Record actual executable/version, header/model/effort, command, packet revision, worktree, timestamps/status/report; unavailable settings/counters stay unknown. Controlled launcher tests do not establish live role/model behavior.

Use [PUBLIC-PACKET.md](../agentic-software-delivery-v1.0/templates/PUBLIC-PACKET.md) for A/B. B additionally gets A's exact tests/fixtures and sanitized public evidence. Exclude plans, coordinator history, implementation-bearing Current state, coverage maps and LESSONS entries. Use [CANDIDATE-PACKET.md](../agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md) for C/D; C gets frozen checkpoint/file identities. B/D assess and hand off; they do not repair review targets.

Before blind probes, arrange source-free warning/traceback rendering for Python, pytest and relevant subprocess channels. Retain types/categories, messages, locations and status; suppress source snippets/locals, not diagnostics. Disclose unsupported channels or exposure and stop blind work for coordinator routing. Packets identify the permitted harness/checks.

Use supported bounded waits rather than repeated unchanged status reads. Timeout leaves evidence incomplete and consumes the existing allowance. Do not create a reviewer merely as a connectivity probe. A helper, fallback route or host change needs its own scope. Prompt restrictions are not filesystem isolation. The existing [doctor scope](../tasks/setup-doctor.md) is not a general role coordinator.
