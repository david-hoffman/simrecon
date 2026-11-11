# Range tests must isolate each required materialized stage

**Version 1.0**

- ID: 20261009T145219Z-volume-recombine-01-root-range-stage-inventory
- Date: 2026-10-09T14:52:19.289224+00:00
- Task: VOLUME-RECOMBINE-01
- Role: root coordinator
- Topic: scientific test adequacy
- Status: confirmed
- Observation: Fresh B3 found that existing individual-product and squared-transfer overflow tests did not cover numerator accumulation or denominator-plus-regularization overflow. Both are approved rejection outcomes even when the exact mathematical quotient is finite. B3 also demonstrated that zero-count assertions alone accept empty output arrays. These observations establish test gaps, not product defects; the public reconstruction API remained absent.
- Evidence: Local ignored `artifacts/volume-recombination-execution/b-final-03.txt` and `support-b3-completion-audit-01.json`, reviewed checkpoint `6892f1f1214927f957e99ca249addd2c4fc02758`; contract W08/W20/W23. A correction 3 independently demonstrated finite preceding stages with the existing public separator on Python 3.13.12 / NumPy 2.5.3 in `a-correction-03-prerequisite.stdout.json`. Its revised checkpoint still requires fresh B acceptance.
- Suggested action: Inventory required materialized arithmetic stages separately, isolate each failing stage with otherwise valid inputs, and pair exact-zero checks with the public shape/storage guarantees. Corrections follow the existing test-owner and fresh-review route.
