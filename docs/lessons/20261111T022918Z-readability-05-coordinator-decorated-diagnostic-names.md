# Decorated operation names are diagnostic inputs

**Version 1.0**

- ID: 20261111T022918Z-readability-05-coordinator-decorated-diagnostic-names
- Date: 2026-11-11T02:29:18Z
- Task: [Task 05 optical-transfer readability](../tasks/readability-stack.md#task-05-contract-and-evidence-pointer)
- Role: coordinator
- Topic: helper-name preservation
- Status: confirmed
- Observation: The optical-transfer `_operation` decorator constructs translated failure text from `function.__name__`. Renaming its decorated `_sample_transfer` helper would change diagnostics even if the numerical body stayed identical. Task 05 leaves that helper identity intact while clarifying its purpose in documentation and naming other operations.
- Evidence: Baseline `c7bea91a4c07068e7662be1f5ca5aed24e369f18`, `src/simrecon/optical_transfer.py` definitions `_operation` and `_sample_transfer`; Task 05 restricted C packet/report and preservation evidence under local ignored `artifacts/readability-05/`. This is source inspection, not a newly exercised backend-failure claim.
- Suggested action: Include decorator-generated names and string consumers in rename inventories; preserve required diagnostic identity when changing a helper's displayed name would alter the authorized behavior.
