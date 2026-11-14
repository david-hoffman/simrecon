# Section-only permissions can fail at whole-file reads

**Version 1.0**

- ID: 20261114T230813Z-ph118-coordinator-whole-file-public-packets
- Date: 2026-11-14T23:08:13Z
- Task: [PH118](../tasks/preparation-harmonic-lifetimes.md)
- Role: coordinator
- Topic: blind-role packet boundaries
- Status: confirmed
- Observation: Two fresh static A launches stopped before test authoring because
  whole-file reads exceeded section-only permissions. A1 read nonblind procedure
  sections of a mixed-mode audit skill; A2 read additional procedural/setup and
  history-pointer text in PROJECT. Neither reported reading actual product source,
  history, task state, coverage maps or lesson records, and neither executed tests.
  The recurrence identifies a packet-versus-whole-file-read mismatch, not a
  scientific product defect or demonstrated source exposure.
- Evidence: [A1 report](../reports/issue-118/a1-stopped.md), SHA256
  bfa3cd3f3344f3521e7400742b3171ef4760c41d7f2dab96e1d86effd059c5f7,
  retained in cebb5a753352e24ca96f76a96b7279eb32ecd881; [A2 report](../reports/issue-118/a2.md),
  SHA256 644e774f25fe8ac96cb449a1bde4e003b3bcf991b7d38509b683c0bc40b659e5,
  retained in cf2bb06b23671d5fb7cf7cfd079843aec862ae68. Both tool sessions were
  fresh Sol/high requests under the execution hold; actual serving, tokens,
  cost and elapsed time remain unknown. [Launch accounting](../reports/issue-118/role-launches.md)
  preserves both attempts. The corrected [public packet](../packets/issue-118-a.md)
  at cf2bb06 entirely excludes PROJECT and the mixed-mode skill, embeds the
  approved public facts/questions, and permits whole explicitly named public
  files without unlisted link traversal. Fresh A3 has begun; completion is pending.
- Suggested action: Use self-contained approved public context and explicit
  whole-file allowlists where a role might otherwise read a mixed-context file.
  Preserve stopped attempts and route fresh roles without claiming restored
  blindness. This is in-scope packet correction, not new policy or authority;
  shared filesystem prompt restrictions supply no engineered isolation guarantee.
