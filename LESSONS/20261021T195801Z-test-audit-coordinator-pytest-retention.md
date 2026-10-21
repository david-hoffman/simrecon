# Keep passing test scratch inside the pytest lifetime

**Version 1.0**

- ID: 20261021T195801Z-test-audit-coordinator-pytest-retention
- Date: 2026-10-21T19:58:01.075381+00:00
- Task: [Test audit and Ubuntu CI](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: fixture disk lifecycle
- Status: confirmed for the locked pytest9.1.1 and observed cases
- Observation: Default `all` retention kept passing function scratch. The reviewed
  `failed` policy releases eligible function scratch and removes a successful
  default numbered session after factory consumers finish. A custom explicit
  base does not receive whole-session cleanup. A shipped test helper must also
  put its generated children under its outer pytest fixture; a permanent audit
  directory would create a new accumulation path. Keep required native/log/report
  evidence external and preserve the canonical coverage destination.
- Evidence: [Public contract](../docs/contracts/test-fixture-disk-lifecycle-v1.md),
  frozen tests c7f232d5c4a9dcaae9989b2b7839f085d0d044e0384794330dd099c4278539e6
  and helper6f994f04e16d15466adb0f07f1273aa5f10a81b08e732b22d3e3f042f4b0caa2;
  configuration4575c19b17c0b723778e6e1bcb4cda5ac8e40e4cfbba4473a787e1d24e290c86.
  Fresh blind B accepted the pair; C observed12passing focused cases. Two genuine
  four-worker runs of M25, the sparse-extension limit, bounded TIFF/opaque hashing
  and authentic Java reader cases each passed6items. Their owned namespaces each
  retained0logical fixture bytes and0native allocated entry bytes after process
  closure, with an empty uv lock and parent directory remaining. Each retained
  10original native databases (1,024,000bytes) plus4reports outside scratch.
  Receipts: artifacts/test-audit-ci/disk-lifecycle/qualification/
  a1c45e260a59457887f37a45ed7e1550-summary.json and its two named original runs.
  Those are supplemental staged-source measurements, not full-suite/native100%
  qualification or CI timing evidence.
- Suggested action: Use owned default-numbered namespaces for future diagnostics;
  keep permanent evidence outside them. Do not resume the old unmanaged profiling
  launcher. Separate final retained bytes from live traversal sums: non-atomic
  scans may understate or overstate simultaneous allocation. Failed calls retain
  scratch within the count3 policy; setup and later teardown errors do not
  guarantee retention. Require the unchanged exact-candidate full gate and fresh
  review before submission. This observation authorizes no generic pruner or
  historical deletion.
