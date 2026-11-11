# Standalone review packets need an absolute evidence root

**Version 1.0**

- ID: 20261103T014832Z-ce03-coordinator-absolute-paths-for-native-packets
- Date: 2026-11-03T01:48:32.639822+00:00
- Task: CE03, [task pointer](../tasks/c-equivalence-optical-transfer.md)
- Role: coordinator
- Topic: role packet
- Status: confirmed
- Observation: B3 could not locate the permitted public attachments because the coordinator packet named evidence-relative paths without an absolute evidence root. It asked for the path and produced no verdict. The coordinator stopped that owned process, retained its incomplete launch/unknown partial usage and launched fresh B4 with explicit path resolution. No test, contract or runtime bytes changed; B4 completed acceptance.
- Evidence: B3/events.jsonl, coordinator-stop.json and completion.json; public/B3-packet.md versus public/B4-packet.md; B4/final.md in the CE03 evidence root. Evidence root: `/private/tmp/simrecon-ce03-evidence-20261102/`; archived by the sole Current state at completion.
- Suggested action: Put absolute worktree/evidence roots and relative-path resolution at the start of standalone packets, then cheaply verify the named input files exist before launching. This is a packet-preparation lesson, not new role authority or a gate waiver. This entry grants no edit, publication or policy authority.
