# A private extension tag can fail a modern MRC validator

**Version 1.0**

- ID: 20261001T045851Z-mrc-conversion-intake-extension-validation
- Date: 2026-10-01T04:58:51Z
- Task: [MRC conversion intake](../docs/tasks/mrc-conversion.md)
- Role: intake
- Topic: format interoperability
- Status: confirmed
- Observation: published mrcfile 1.5.4 validation accepts a fixed list of extended-header tags and would reject the proposed private SRM1 tag for a nonempty extension. Registration and a documented project schema are distinct concerns.
- Evidence: [Pinned validator inspection](../docs/architecture/mrc-output-compatibility.md); verified public wheel SHA-256 and read mrcobject.py without installing or executing it. No product runtime/test was written.
- Suggested action: propose an actual agreed container such as HDF5 with a documented project schema, then prove output compatibility through an independent reader. Do not borrow an agreed tag for incompatible bytes or suppress the validator failure. This lesson grants no new execution authority.
