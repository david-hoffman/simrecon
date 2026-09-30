# An editable install disappeared when its path file became hidden

**Version 1.0**

- ID: 20260930T191720Z-setup-coordinator-hidden-editable-install
- Date: 2026-09-30T19:17:20.392735+00:00
- Task: SETUP-TEST-RUN in [setup plan](../docs/tasks/setup-plan.md)
- Role: setup coordinator, after A's environment-failure report
- Topic: environment reproducibility
- Status: confirmed
- Observation: The five tests passed initially, then package imports failed without a source/test change. Both generated editable-install `.pth` files had macOS `UF_HIDDEN`. Installed Python 3.13.12 `site.py` explicitly skips such files. Clearing the bit restored imports briefly, but the flag reappeared during the next run. The flag-setting process is unknown. A rebuilt locked environment outside Documents, reached through the same `.venv` symlink, then passed the unchanged tests.
- Evidence: [flag receipt](../docs/setup/evidence/environment/hidden-pth.json). Native A session `01a0f3ba-35d4-7bf3-94f6-46d4b25f715c`; command `.venv/bin/python -m pytest tests/test_test_run.py --tb=line --show-capture=no` with the source-free diagnostic environment. After repair: 5 passed in 0.91 seconds. Classification: environment/tooling, not product defect or C repair.
- Suggested action: Keep generated environments outside a location that repeatedly changes their flags. Identify the setter before attributing a root cause to a particular sync or security service. A passing rerun alone would not have diagnosed this failure. Preserve test checkpoints across environment-only repair and rerun on the repaired environment.
