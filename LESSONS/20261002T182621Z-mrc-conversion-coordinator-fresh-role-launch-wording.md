# Describe a launched role as the current root

**Version 1.0**

- ID: 20261002T182621Z-mrc-conversion-coordinator-fresh-role-launch-wording
- Date: 2026-10-02T18:26:21Z
- Task: MRC-CONVERSION-01
- Role: coordinator
- Topic: native role launch packet
- Status: confirmed
- Observation: A D2 packet combined a no-delegation rule with an imperative to launch a new native root. The already launched role started another reviewer process. The coordinator terminated both task-owned processes, retained the attempt and spending, and relaunched a direct fresh root with explicit instructions to review within its current invocation. No product or test bytes changed; direct D2 accepted the verified candidate.
- Evidence: [interrupted launch classification](../artifacts/mrc-conversion/roles/d-keys-launch-attempt1-tooling.json), retained ignored attempt events/stderr, [direct D2 acceptance](../artifacts/mrc-conversion/roles/d-keys-report.txt), candidate `06eef6a837837e2d0ed7eacdc6cce19dfaba30b2`; native codex0.159.2 with memory/multi_agent disabled.
- Suggested action: Put launch commands in coordinator instructions. Tell a launched role that it is already the fresh root and must perform its review there, with no nested CLI/reviewer process. Disabled optional agent tools are not an engineered barrier to external CLI launches. This is a packet correction under existing rules, not a delivery-policy change or allowance reset.
