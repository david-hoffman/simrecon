# Check the complete evidence grammar before an expensive gate

**Version 1.0**

- ID: 20261017T005317Z-volume-carrier-selection-coordinator-full-evidence-grammar
- Date: 2026-10-17T00:53:17.433737+00:00
- Task: VOLUME-CARRIER-SELECTION / docs/tasks/volume-carrier-selection.md
- Role: coordinator
- Topic: closed example provenance
- Status: confirmed
- Observation: Full local01 passed all 13 canonical phases and 7,572 tests, but unchanged qualification rejected its closed-example provenance. The association named an outer driver absent from the closed generator list. Its timestamps also bracketed the observer instead of the actual child generation, violating before/start/end/after ordering. The initial cheap binder checked source/member fingerprints and schemas but missed these downstream obligations. The coordinator diagnosed both before routing one producer-only C03 correction. C03 generated the same nine cases through an actually invoked closed cohort member, with actual child timestamps inside source observations. Current code/tests remained frozen. The original passing gate, failed qualification and earlier examples remain historical; renewed exact-candidate verification is required.
- Evidence: artifacts/volume-carrier-selection-20261016/qualification-diagnosis01.json SHA256 ee11562aa57e7ba611345f6bc210a7f737f7e08e50d2eb39bf80419092a22ad1; support-qualification/qualification-full-local01-01.json SHA256 b621cce7125d5b054ef4a512ba1517f5453344964338ab229138bcdec0b6a166; C03/closed-grammar-check01.json SHA256 b1bc31fb8b6450ac6ccc300acc8924133a3e0dacc28a9e1314c5e9b718fe9407. C03 generation check is not final admission, full qualification or independent D review.
- Suggested action: exercise the complete existing structural grammar on actual closed generation records before expensive dependent verification, including invoked-member identity and honest temporal bracketing. Label pre-gate structural checks separately from actual gate/qualification evidence. This observation grants no gate relaxation or new authority.
