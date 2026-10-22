# Keep type correction separate from behavioral test changes

**Version 1.0**

- ID: 20261014T092923Z-baseline-compatibility-coordinator-test-typing-preservation
- Date: 2026-10-14T09:29:23.335484+00:00
- Task: [BASELINE-COMPATIBILITY-01](../docs/tasks/shared-node-baseline-compatibility.md)
- Role: coordinator, observing fresh A06/B09
- Topic: public test typing and preserved evidence
- Status: confirmed
- Observation: The integrated public-failure pair produced 44 Pyright diagnostics despite passing scoped lint/format. A fresh blind author added eight explicit field annotations, eight targeted casts and four redundant narrowing assertions. A fresh reviewer independently checked both files and all rational/parser dependents, retaining all28outcomes and prior defect evidence.
- Evidence: Ignored artifacts/baseline-compatibility-20261013/B09/final.txt and B09/A06/mapping.md preserve exact accepted hashes and constrained AST/owned mathematical/file comparisons. Final scoped Pyright/lint/format passed; the unchanged blind baseline retained26passes and its2accepted source-finiteness failures.
- Suggested action: Check owned test typing before expensive integration verification. Review actual annotation/cast effects and shared dependents; preserve earlier valid failures instead of treating a typing correction as new scientific evidence. Use explicit source-free pytest mode before blind checks.
