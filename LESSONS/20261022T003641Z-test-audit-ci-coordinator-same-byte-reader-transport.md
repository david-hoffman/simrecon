# Verify a transport alternative against the existing byte pin

**Version 1.0**

- ID: 20261022T003641Z-test-audit-ci-coordinator-same-byte-reader-transport
- Date: 2026-10-22T00:36:41.728035+00:00
- Task: [test audit and Ubuntu CI](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: dependency transport diagnosis
- Status: confirmed observation; Ubuntu repair effectiveness remains unmeasured
- Observation: Two actual Ubuntu attempts of run39699741369 failed before tests on the same pinned Bio-Formats TLS handshake timeout in both independent root jobs. One isolated local acquisition from the official v8.5.0 GitHub release delivered 53,843,906 bytes with the exact existing SHA-256 c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9, HTTP200, one redirect, TLS verification result0 and 2.209353 seconds. This establishes a same-byte alternative from that environment, without establishing the original routing cause or Ubuntu availability.
- Evidence: Original run39699741369 attempt1/attempt2 native metadata and failed logs under artifacts/test-audit-ci/standard-ci/performance/failed-run-39699741369-a1/ and -a2/; isolated probe summary/inventory under performance/reader-mirror-probe/; official [release asset listing](https://github.com/ome/bioformats/releases/expanded_assets/v8.5.0). Probe used stock curl8.7.1 with HTTPS-only redirects, unchanged SHA/size, no retry, 15-second connection and 180-second total bounds. Original JAR/tool identities remained unchanged.
- Suggested action: Keep scientific bytes, reader pins and existing validation fixed while reviewing a bounded workflow-only acquisition step. Require actual complete Ubuntu execution and timing afterward. A local transfer or fast failed run supplies no full-suite performance proof.
