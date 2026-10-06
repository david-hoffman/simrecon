# Read-only reviewers need temp-free probe transport

**Version 1.0**

- ID: 20261006T042237Z-nf02-coordinator-readonly-probe-transport
- Date: 2026-10-06T04:22:37.478189+00:00
- Task: [NF02](../docs/tasks/known-phase-separation.md)
- Role: coordinator
- Topic: reviewer tooling
- Status: confirmed
- Observation: Native strict read-only B1 pytest stopped before collection because default file-descriptor capture needed a temporary file. B2 reached all focused tests with in-memory capture, then its zsh here-document failed before Python ran for the same write restriction. Neither failure established a product defect. Both completed reviews remained charged; no accepted checkpoint resulted.
- Evidence: Corrected public test checkpoint 717416955799667a150967a4e96a0195070da39d; ignored artifacts/nf02-revision/execution-record.json reviewer_environment_diagnosis and B2_command_diagnosis, retained role-B1/role-B2 verdicts. Native :read-only pytest with --capture=sys -p no:cacheprovider executed139cases (124 missing-API failures/15passes). Native Python -c probe exited0, reproduced eight fixture hashes and certified nine public NumPy/SciPy SVD results in0.277s. This was command capability evidence, not blind acceptance.
- Suggested action: For an authorized strict read-only review, validate temp-free capture and inline argument transport before dependent probes. Pass Python source through -c; avoid shell here-documents. Keep assertions/canonical checks unchanged and retain failed attempts. A tooling resolution grants no review-budget extension by itself.
