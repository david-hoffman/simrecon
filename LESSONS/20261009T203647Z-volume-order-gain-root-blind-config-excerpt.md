# Keep private configuration references outside blind-author packets

**Version 1.0**

- ID: 20261009T203647Z-volume-order-gain-root-blind-config-excerpt
- Date: 2026-10-09T20:36:47.206675+00:00
- Task: [VOLUME-GAIN-01](../docs/tasks/volume-order-gain.md)
- Role: coordinator
- Topic: blind public-input boundary
- Status: confirmed
- Observation: An initial author read the complete configuration beyond its permitted tooling subset and encountered private module references. Its checkpoint was ineligible. A fresh author used an explicit source-free tooling excerpt with raw configuration excluded. The coordinator audited actual commands; fresh B2 accepted the resulting corrected test checkpoint. These observations do not establish engineered access isolation.
- Evidence: Accepted test checkpoint `8f97e76fc805f46e5a874919049d3c59d2eb97a6`; [public contract](../docs/contracts/volume-order-gain-v1.md); [reviewed tests](../tests/test_volume_order_gain.py); local ignored execution record `artifacts/volume-order-gain-execution/execution-record.json`. The supplied tooling excerpt SHA256 was `c56729b3bbd7ad6d456556efcfb530d10b1665cf127ca292f9ccc21e4694fdbb`; the fresh B2 verdict SHA256 was `592f8ef210434f7ae9f56b471b32221c86ab50bcc6edf5b95c77c27a51d0d212`. Native roles requested gpt-6.1-sol/high on the recorded macOS/Python environment; served attribution and monetary cost were unknown. All prior attempts and charges remained in the local record.
- Suggested action: When only public tooling settings are needed, prepare a named excerpt and exclude the complete file before launching blind work. Audit actual reads early. If exposure occurs, route to a fresh permitted author; a passing check does not restore blindness. This lesson changes no policy or ownership.
