# Preserve scalar rounding stages when regenerating historical fixtures

**Version 1.0**

- ID: 20261013T002338Z-reference-fixture-generation-coordinator-preserve-rounding-stages
- Date: 2026-10-13T00:23:38.613103+00:00
- Task: [FIXTURE-EXPORT-01](../docs/contracts/reference-fixtures-v1.md)
- Role: coordinator
- Topic: numerical representation
- Status: confirmed
- Observation: The reconstruction fixture rounds each independently derived scalar to binary64 before convolution. The convolution then uses separate binary64 multiplication and addition in the specified left-fold order. Delaying rounding through convolution changes historical values. The completed exporter reproduced both integrated documentary datasets byte for byte, including their original metadata.
- Evidence: `artifacts/reference-fixture-generation-20261012/C01/root-completion.json` links the executed public generation evidence, root byte proof and authenticated original Git blobs. The accepted contract section R3 defines the scalar-rounding and accumulation order. The locked Python 3.13.12 coordinator run reproduced 12,471 OTF bytes and 191,602 reconstruction bytes with unchanged inputs.
- Suggested action: Preserve each approved rounding stage and operation order in future fixture regeneration. Record fresh execution provenance outside the immutable historical scientific metadata.
