# Native and pytest unraisable events need separate public-path evidence

**Version 1.0**

- ID: 20261112T033927Z-lessons-unraisable-coordinator-native-and-pytest-paths
- Date: 2026-11-12T03:39:27Z
- Task: [LESSONS-UNRAISABLE-01](../tasks/lessons-unraisable-diagnostics.md)
- Role: coordinator
- Topic: diagnostic-channel qualification
- Status: confirmed
- Observation: At execution baseline `8ee8776352422e629b7701d7660006573ae298e6`,
  explicit destructor exceptions leaked synthetic source through the launcher,
  while the corresponding measured shutdown cases already omitted source.
  Pytest's singular warning-as-error path also needed separate original-location
  checks. Its grouped-finalizer reports already passed through the existing
  source-free traceback path. Native zero exit status and marker absence alone
  therefore provide inadequate qualification.
- Evidence: [correction report](../reports/lessons-unraisable-diagnostics.md),
  its requirement/test mapping and retained ignored baseline/native-reference logs;
  project Python 3.13.12 and locked pytest 9.1.1 on Linux. No production-source
  exposure or other-platform result is claimed.
- Suggested action: Exercise real explicit finalization, shutdown and relevant
  pytest interception paths independently, assert retained category/message/location
  and native status, and preserve already-correct group rendering rather than
  adding an unneeded broad report rewrite.
