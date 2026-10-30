# Repeatability targets use returned moments

**Version 1.0**

- ID: 20261030T042724Z-ra04-coordinator-returned-moment-repeatability
- Date: 2026-10-30T04:27:24.394844+00:00
- Task: RA04, docs/tasks/reference-alignment-ra04.md
- Role: coordinator, observing preimplementation contract/test review
- Topic: numerical test oracle
- Status: confirmed within the cited public contracts and controls
- Observation: B1 showed that an assertion using exact fixture frame means can reject a scalar-camera result allowed by the public contract. B2 independently accepted a ninety-digit target computed from genuinely returned frame/group means, while preserving separate source-moment accuracy checks.
- Evidence: docs/contracts/scalar-camera-calibration-v1.md; docs/reports/evidence/ra04/B2-review.md; docs/reports/evidence/ra04/test-checkpoint.json. The public counterexample differs from the returned-point target by0.89999928 allowances and from source truth by1.47734955 allowances.
- Suggested action: For this contracted statistic, compute the expected relation from returned moment values in adequate precision and keep independent checks of those moments. This does not authorize another estimator or tolerance change.
