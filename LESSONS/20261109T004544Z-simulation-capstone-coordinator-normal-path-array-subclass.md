# The normal study runner needs plain array views

**Version 1.0**

- ID: 20261109T004544Z-simulation-capstone-coordinator-normal-path-array-subclass
- Date: 2026-11-09T00:45:44Z
- Task: [Simulation capstone](../docs/studies/simulation-capstone/README.md)
- Role: coordinator
- Topic: study command and array boundary
- Status: confirmed
- Observation: The documented normal cell command failed before carrier fitting on a valid pinned specimen. It passed a NumPy memmap subclass to a plain ndarray boundary. The sweep passed because it exposed the same mapped data through a plain view. The corrected normal run reproduced every archived signed image and coordinate sample byte for byte.
- Evidence: [Normal runner](../docs/studies/simulation-capstone/reconstruction/run_study.py) and [original-cell control receipt](../docs/studies/simulation-capstone/figures/cell-close-pair.json), CPython 3.13.12 and NumPy 2.5.3 on macOS arm64.
- Suggested action: Exercise the documented normal command with its real decoded files when a neighboring sweep uses a separate input loader.
