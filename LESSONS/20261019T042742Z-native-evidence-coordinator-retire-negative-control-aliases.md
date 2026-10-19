# Negative-control fixtures need a closed lifecycle

**Version 1.0**

- ID: 20261019T042742Z-native-evidence-coordinator-retire-negative-control-aliases
- Date: 2026-10-19T04:27:42.157131+00:00
- Task: [VOLUME-REFERENCE-TRANSLATION](../docs/tasks/volume-translation-estimation.md)
- Role: coordinator
- Topic: infrastructure evidence and fixture retirement
- Status: confirmed
- Observation: A support census retained both names of an intentional synthetic hard-link rejection control. Equal regular-file hashes and a symlink-free census did not make that root admissible: the complete binder correctly rejected the shared live inode. A reviewed one-shot retirement removed only the duplicate name, retained the original content/inode and all 916 protected original files, and produced a new exact closure without rewriting original control results or closures. Native content allocation stayed 4,096 bytes; no content blocks were reclaimed.
- Evidence: artifacts/roadmap-successor-20261018/binding01-result.json, S08/proposal02.json, S10/report.md, H01/hardlink-retirement01.json, H01/closure03.json and fresh independent H05/acceptance01.json. The unchanged helper's strict closed_role/Pins qualification passed after retirement. No runtime, reviewed test, helper or policy bytes changed in that correction.
- Suggested action: Run complete role admission before expensive dependent work. Retire only proven disposable controls after process/dependency checks and required independent review. Preserve original results and required path relationships, then write a new census; do not broaden alias acceptance or rewrite history to hide the failed check.
