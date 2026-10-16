# Scale weighted contributions before binary64 summation

**Version 1.0**

- ID: 20261016T033855Z-empirical-trilinear-coordinator-weighted-scaling
- Date: 2026-10-16T03:38:55.769180+00:00
- Task: [Empirical trilinear transfer](../docs/tasks/empirical-trilinear-transfer.md)
- Role: coordinator observing restricted C checks
- Topic: numerical range
- Status: confirmed
- Observation: The first implementation passed264 cases but lost meaningful contributions in two extreme-weight cases. Selecting a common scale from the largest unweighted source component still let those weighted contributions underflow. Multiplying exact weights by represented components before conversion and selecting the scale from weighted components corrected both failures.
- Evidence: Frozen checkpoint `52de983c34f40e25b1cfc8a28f70847b794bf5cb`, tests `test_extreme_weighted_contribution_survives_standalone_weight_underflow` and `test_tensor_weight_product_underflow_keeps_representable_contribution` in [the public test module](../tests/test_empirical_trilinear_transfer.py). Final focused C02 run passed266 cases; [runtime](../src/simrecon/_empirical_trilinear.py) SHA256 `1909fbec7b866d1d65bd70a710f58723d62efe4986804eb52f0b356b181d9030`. C01/C02 command/log pointers live in the task's retained local Current state. This is focused evidence, not a full-project acceptance claim.
- Suggested action: Choose scales from weighted components, or demonstrate that an alternative preserves the contracted contributions. Distinguish standalone-weight underflow from tensor-product underflow and check both through the public numerical boundary.
