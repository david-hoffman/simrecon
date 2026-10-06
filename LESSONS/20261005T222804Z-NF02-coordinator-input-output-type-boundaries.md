# Input and output type restrictions are separate obligations

**Version 1.0**

- ID: 20261005T222804Z-NF02-coordinator-input-output-type-boundaries
- Date: 2026-10-05T22:28:04.643228+00:00
- Task: NF02, known-phase separation
- Role: coordinator
- Topic: test oracle scope
- Status: confirmed
- Observation: The approved contract requires plain ndarray inputs but does not require exact ndarray output types. B1 demonstrated that the original shared observer rejected an owned ndarray-subclass result satisfying output shape, dtype, layout, ownership and numerical requirements. A changed only the two output type assertions; fresh B2 accepted the revised checkpoint after checking every success dependent.
- Evidence: [Public contract](../docs/contracts/known-phase-separation-v1.md#output-ownership-and-numerical-limits); accepted test SHA-256 67e1c2aa7c1f05dda4c8bf920ed1a2c5fc3bee2e080c8cc1fa3f48c91098a546 and unchanged fixture SHA-256 8ec63bbfb716adb13ca59c98dec1cd8e8471dabc998e09e1c72d8c4498489c9c. Independent source-free observer probes on Python 3.13.12/NumPy 2.5.3 accepted valid subclasses and rejected representation, ownership and numerical defects; final role evidence is recorded externally in the NF02 PR/conversation.
- Suggested action: Compare input and output obligations separately before adding exact-type assertions to shared public-interface observers.
