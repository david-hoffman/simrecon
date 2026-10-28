# Isolate platform-dependent fixture cases

**Version 1.0**

- ID: 20261022T200641Z-simulation-camera-coordinator-platform-case-identity
- Date: 2026-10-22T20:06:41.990686+00:00
- Task: [Full noisy simulation](../docs/tasks/full-noisy-simulation.md), NS01
- Role: coordinator
- Topic: portable numerical test oracles
- Status: confirmed
- Observation: On Darwin arm64 with NumPy2.5.3, longdouble aliases float64. A fixture guard based only on that dtype and equal maximum values applied a positive exception to nine unrelated invalid-array cases. The implementation correctly rejected them; the tests incorrectly expected success. The exception was intended only for the finite maximum-longdouble boundary.
- Evidence: Accepted B3 test snapshot SHA2567fdfcde14a61babad10de0da0991918942d7eaf4ce2316c44cce1d5932df466d in artifacts/full-noisy-simulation-20261022/accepted-B3/test_simulation_camera.py; [sanitized finding and NumPy-only reproduction](../artifacts/full-noisy-simulation-20261022/A-correction04-public-findings.md); C full-file pytest result146passed/9failed, Python3.13.12, NumPy2.5.3. The unchanged production candidate is SHA2562fcb365010e3118605186f8b37e4d9e6d0ee6ae008bb5f0c1d920a806618e7cd.
- Suggested action: Isolate the platform-dependent boundary as an explicitly identified case or separate test. Keep all unrelated invalid cases unconditional. Route the oracle correction through blind A and fresh B; do not accommodate an invalid success expectation in production. This lesson grants no edit authority.
