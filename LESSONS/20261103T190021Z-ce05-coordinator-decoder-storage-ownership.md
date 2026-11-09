# A read-only decoded view can still violate owned-storage input rules

**Version 1.0**

- ID: 20261103T190021Z-ce05-coordinator-decoder-storage-ownership
- Date: 2026-11-03T19:00:21.931808+00:00
- Task: [CE05 carrier/modulation](../docs/tasks/c-equivalence-carrier-modulation.md)
- Role: coordinator and artifact preparation support
- Topic: Typed numerical artifact transport
- Status: confirmed
- Observation: A typed decoder allocated an array and then reshaped it, returning a non-owning view. Setting that view read-only preserved its values but did not satisfy the existing OpticalTransfer requirement for owned, read-only complex128 samples. The first figure call was correctly rejected before fitting. A final explicit copy after reshape, followed by the required read-only flag, restored the declared input storage without changing any frozen numerical value, dtype or shape.
- Evidence: Task-local `figure/observer-1.log` retains the rejection. `figure/transport-validation-20261103T184704418107Z.json` reproduces it through existing public CE03 sampling, verifies the repaired storage and all53 frozen arrays, and records unchanged input/expectation/trace/axis hashes. `figure/harness-repair-provenance-20261103T184802130686Z.json` preserves original tools. Subsequent public observations and `figure/observation-repeat-equivalence.json` retain the successful output. The task pointer locates the durable evidence; this was an artifact defect, not a product or reviewed-test defect.
- Suggested action: Validate decoded record storage properties through the existing upstream public boundary before a dependent observation. Where the record requires ownership, copy after the last reshape and then set the declared flags. Preserve the failed attempt and frozen numeric payloads when repairing transport; this grants no new numerical meaning or editing authority.
