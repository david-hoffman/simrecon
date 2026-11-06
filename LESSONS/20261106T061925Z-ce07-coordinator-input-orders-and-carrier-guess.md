# Resolve workflow carrier guesses from acquisition phase count

**Version 1.0**

- ID: 20261106T061925Z-ce07-coordinator-input-orders-and-carrier-guess
- Date: 2026-11-06T06:19:25.070939+00:00
- Task: [CE07](../docs/tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: scientific caller composition
- Status: confirmed (static source and independent source review)
- Observation: The selected C caller computes its input order count from P as
  P//2+1 before selecting a possibly reduced output order count O. Its 3D initial
  carrier magnitude uses 1/(linespacing*(P//2)); true2D uses 1/linespacing.
  Therefore P5/O2 still uses divisor2. Drift phase linkage has a separate source
  guess and must not silently reuse the fitted or angle-overridden carrier.
- Evidence: [Exact public carrier rules](../docs/contracts/c-equivalence-workflow-v1.md#23-optics-initial-carrier-and-estimator-configuration)
  and [source map W08/W09](../docs/contracts/c-equivalence-workflow-map-v1.md#3-equation-and-caller-map),
  pinned sirecon.c:278-283,388-417 and drift caller references. Fresh complete
  source-review-2 accepted the frozen contract/map; durable verdict is
  /private/tmp/simrecon-ce07-evidence-20261104/source-review-2/final.md.
  No product or retained executable was run for this observation.
- Suggested action: Resolve each caller-level quantity from its declared source
  inputs before invoking the accepted stages. Keep output-order reduction,
  initial carriers and phase-linkage carriers explicit in tests and diagnostics.
