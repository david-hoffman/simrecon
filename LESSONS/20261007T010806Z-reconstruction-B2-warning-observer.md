# Warning observers need both return paths and permitted categories

**Version 1.0**

- ID: 20261007T010806Z-reconstruction-B2-warning-observer
- Date: 2026-10-07T01:08:06.140606+00:00
- Task: [Known-parameter reconstruction](../docs/tasks/known-parameter-reconstruction.md)
- Role: coordinator recording B2's public observer findings
- Topic: test diagnostics
- Status: confirmed observer defects; no reconstruction product behavior established
- Observation: B2 independently demonstrated that a normal-return control dropped an arithmetic RuntimeWarning, while an exception-return control rejected a permitted UserWarning. A blanket empty-warning assertion both missed a prohibited diagnostic and rejected a legitimate alternative.
- Evidence: Local retained `artifacts/reconstruction-execution/B2-final.txt`, SHA256 `027bf266c1edf31ea3e6d84a205af487e9b2ee4c6648b153f1bf8d0ac195addc`, and its source-free public-boundary probe evidence. B2-reviewed controls SHA256 `ef1b1558d942eb11264ed93b7914d73e6392addd86aebc8a01509bb98789db98`. [R28–R29 contract](../docs/contracts/known-parameter-reconstruction-v1.md#range-errors-and-accuracy). Native environment Python3.13.12,NumPy2.5.3,SciPy1.18.1,macOS27arm64.
- Suggested action: Preserve category/message/location on normal and exceptional observer paths. Check only the warnings prohibited by the public contract and retain permitted categories as diagnostic evidence. Validate both observed cases. This lesson grants no new scope, policy or execution budget.
