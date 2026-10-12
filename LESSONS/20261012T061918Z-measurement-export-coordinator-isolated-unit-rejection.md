# Unit rejection can be masked by arithmetic rejection

**Version 1.0**

- ID: 20261012T061918Z-measurement-export-coordinator-isolated-unit-rejection
- Date: 2026-10-12T06:19:18.627098+00:00
- Task: [Empirical transfer consumption](../docs/tasks/empirical-transfer-consumption.md)
- Role: coordinator
- Topic: public-contract test oracle
- Status: confirmed
- Observation: Fresh B02 constructed a static counterexample that rejected the reviewed invalid-unit examples through inconsistent arithmetic while accepting an otherwise valid zero-increment record with prohibited units `KB`. This demonstrates an oracle gap in those examples; it establishes no runtime defect or native memory result. With zero baseline, peak and increment, arithmetic remains valid and the unit field alone requires rejection.
- Evidence: Native B02 final SHA256 `0664c2887b9335d28f6bae7609bc919929513c0ccfe31067f2c36c419ff813ba`, reviewed checkpoint `76341ce771f6d7840ec8a79bb12065f394bb365f`; public [unit contract](../docs/contracts/measurements-export-v1.md) and [measurement export tests](../tests/test_measurements_export.py). The static counterexample used `scale = 1024 if units == "KiB" else 1`: the prior examples yield `7 B != 7168 B`, while zero yields `0 B == 0 B`. Original review/check evidence and environment limitations remain in the task accounting chain. No product execution was inferred from the read-only review.
- Suggested action: Within an authorized representation-test correction, keep every unrelated field valid, isolate the rejected field and retain permitted positive siblings. Obtain fresh review of affected shared helpers and dependents; this lesson grants no additional edit scope.
