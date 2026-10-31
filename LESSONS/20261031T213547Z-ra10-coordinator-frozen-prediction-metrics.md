# Score the frozen product prediction for prediction claims

**Version 1.0**

- ID: 20261031T213547Z-ra10-coordinator-frozen-prediction-metrics
- Date: 2026-10-31T21:35:47.820426+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: scientific reporting
- Status: confirmed
- Observation: A static check found that the draft RA10 report driver computed held-out errors from an independent re-solve. That could mask a defective returned prediction. Before any product observation, the coordinator changed those metrics to frozen product outputs and retained independent source/forward/objective checks separately.
- Evidence: ../artifacts/ra10/checks/figure-driver-correction-1.json; ../artifacts/ra10/figure-preparation-1/driver-preparation.py; ../scripts/reference_alignment_ra10_comparison.py. The scoped static recheck found both metric and identity-check corrections addressed.
- Suggested action: Keep a reference re-solve as an agreement oracle; compute claims about returned predictions from the frozen returned arrays.
