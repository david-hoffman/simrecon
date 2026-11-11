# Optional conversion hooks are not extraction requirements

**Version 1.0**

- ID: 20261018T180751Z-phase-carrier-selection-coordinator-optional-conversion-oracles
- Date: 2026-10-18T18:07:51.678177+00:00
- Task: PHASE-CARRIER-SELECTION
- Role: coordinator
- Topic: public scalar conversion oracles
- Status: confirmed
- Observation: Fresh blind B03 showed an accepted residual-conversion test rejected legitimate base-float extraction in all five public controls because it required an optional subtype hook to run. The contract specified converted values and exceptions actually encountered. A03 corrected the test to observe hook encounter and permit exact bypass, with independently distinguishing residual limits0.5/1/2 on a rank-zero residual-one control. No product defect or new conversion-call requirement followed.
- Evidence: `artifacts/phase-carrier-selection-20261018/B03/review.md`; sanitized `A03/public-findings-correction03.md`, `A03/report-correction03.md` and public protocol probe records. Revised170case checkpoint2711d1f8fe1de616933540a2bd5a2910867e3f7e awaits fresh B04 acceptance.
- Suggested action: Review failure-boundary tests against legitimate public conversion alternatives. Assert error handling when a hook is actually encountered and exact policy behavior when it is bypassed; do not require an implementation's conversion organization without contractual authority.
