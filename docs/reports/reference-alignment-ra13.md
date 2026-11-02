# RA13 — integrating raw-array scientific stages

The [public contract](../contracts/reference-alignment-ra13-v1.md) composes camera
estimation, the accepted predictive calibration handoff and the selected physical
specimen fit. It preserves raw count correction and calibration-to-specimen phase
transfer at their owning stages, with explicit unavailable and partial outcomes.
No new estimator, recovery criterion, convergence guarantee or optical premise is
introduced. The original noisy RA12 case remains separate and unavailable.

## Fixed finite controls

The [public observation bundles](../studies/reference-alignment-ra13/README.md)
were generated before running the new workflow. The noiseless arm uses a deliberately
degenerate central-only illumination and permissive training/operator controls to
exercise finite composition. The noisy arm adds a fixed 0.001-count normal
perturbation (seed 20261102) and uses a predeclared zero training limit. No outcome
was used to retune settings. These are procedure and diagnostic examples, not a
calibrated structured illumination microscopy (SIM) resolution demonstration.

The estimator consumes only seven observed arrays and declared metadata/controls.
A separate source/illumination reference is retained for evaluation after inference
freezes. The [usage example](../usage/reference-alignment-ra13.md) loads only
observations and parameters. The workflow receives no private truth, supplied true
camera, illumination or output rescale.

## Execution and evidence

Actual workflow execution, measured summaries and figures are pending the accepted
blind test checkpoint and restricted implementation. This draft makes no passing
or scientific improvement claim. The sole task state and final identities are
outside tracked bytes at `artifacts/ra13/current-state.json`.

Noiseless finite controls validate only their named arithmetic, wiring, gauge,
prediction and finite optimization obligations. Noisy outcomes are diagnostic.
Iteration limits remain limits; finite material-alternative checks are not global
identification. The model's source-grid/continuum, optical and inverse errors remain
separate from optimizer and noise effects. There is no statistical confidence,
instrument accuracy, universal source recovery or resolution guarantee.
