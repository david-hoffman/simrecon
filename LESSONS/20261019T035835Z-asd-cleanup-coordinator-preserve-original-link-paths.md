# Cleanup must preserve original evidence link paths

**Version 1.0**

- ID: 20261019T035835Z-asd-cleanup-coordinator-preserve-original-link-paths
- Date: 2026-10-19T03:58:35.686331+00:00
- Task: [ASD automatic cleanup](../docs/tasks/asd-automatic-cleanup.md)
- Role: coordinator
- Topic: evidence retention during task completion
- Status: confirmed
- Observation: A retained evidence tree can depend on a symlink referent inside a large disposable fixture tree. Matching regular-file hashes at another location does not preserve that original relationship. Cleanup needs the original link text, resolved referent, dependencies and ancestor paths, and may trim only proven disjoint disposable siblings.
- Evidence: The independently accepted ten-file policy review is retained at artifacts/roadmap-successor-20261018/Q01/acceptance.json, with activation receipt activation01/policy-activation.json. The [cleanup procedure](../docs/operations/fixture-cleanup.md) records the concrete retention requirements and the observed predecessor cleanup evidence. The review checked all ten candidate hashes and 36 local links/anchors; this is documentation evidence, not a qualification of a destructive program.
- Suggested action: At completion, inventory exact owned scratch and retained original relationships before selecting removals. Preserve uncertain scope and record blocked or unchecked areas. Keep the existing risk, ownership, review and verification requirements for each actual operation.
