# Output directory checks do not protect existing symlink leaves

**Version 1.0**

- ID: 20261005T140744Z-delivery-efficiency-d-output-leaf-symlinks
- Date: 2026-10-05T14:07:44Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: D; handoff recorded by documentation maintenance
- Topic: output safety
- Status: confirmed
- Observation: D's read-only probe found that the allowed phase-log directory passed the path guard while an existing `sync.log` symlink resolved to protected content. This establishes a leaf-validation gap; D did not attempt an actual overwrite in the owner repository.
- Evidence: The [independent D report](../artifacts/delivery-efficiency/roles/d-report.md), finding 1, reviews rejected checkpoint `0823da8315dd48cc9f4a85fc32c70875fc72739e`. D used `.venv/bin/python -B -c` with the actual helper functions and filesystem substitutes on local macOS to compare the allowed directory with the prohibited resolved leaf. The report records an unchanged candidate and no destructive filesystem reproduction.
- Suggested action: Validate each actual phase-log output leaf before writing. Route existing-symlink rejection cases through authorized fresh A/B review and a revised checkpoint; require independent D review after the bounded repair. This lesson grants no editing scope or repair allowance.
