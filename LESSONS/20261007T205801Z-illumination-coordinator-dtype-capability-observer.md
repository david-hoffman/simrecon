# Dtype names do not prove a wider observation range

**Version 1.0**

- ID: 20261007T205801Z-illumination-coordinator-dtype-capability-observer
- Date: 2026-10-07T20:58:01.349395+00:00
- Task: [ILLUMINATION-01](../docs/tasks/illumination-estimation.md)
- Role: coordinator
- Topic: numerical oracle and platform capability
- Status: confirmed
- Observation: On this macOS arm64 NumPy 2.5.3 environment, longdouble has the same finite maximum as float64. The blind author diagnosed an int64 conversion observer that treated it as wider. Exact Python-integer comparison observes the lost low bit of 2**63-1; conversion of both sides to this platform's longdouble cannot.
- Evidence: tests/test_illumination.py, test_e02_int64_uint64_rounding_is_converted_problem; source-free A runs and revised dependency report in local artifacts/illumination-execution/A-report.md. Coordinator worktree probe confirmed the finfo and integer comparison. No runtime source supplied the expectation.
- Suggested action: Establish observer capability before relying on a dtype name. Select actually available wider-source examples at discovery, report unavailable representations explicitly, and preserve the project's no-skips gate.
