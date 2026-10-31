# Fixed-gauge exposure phase inference

`fit_exposure_phases` compares known phases, a common command offset and
independent per-exposure offsets under one explicitly supplied finite model.
It profiles one real source shared by all exposures. The carrier, finite
complex displacement kernels, geometry and calibration phase gauge are fixed
inputs. It does not infer them from the raw frames.

The [contract](../contracts/reference-alignment-ra10-v1.md) gives the complete
array grammar, objective, cutoff rules, records and failure behavior. Kernels
are not sampled `VolumeOrderOtf` arrays: transforming a transfer into a finite
kernel requires an independently declared convention. Existing periodic phase
estimators keep their meaning and interfaces.

Use `mode="known"` only for supplied actual phase labels, including synthetic
known-phase controls or actual monitor observations. That mode takes one empty
offset start `(1,0)`, empty bounds `(2,0)` and empty difference steps `(0,)`.
It performs no phase search. A nominal phase command alone is not a monitor
measurement.

Use `mode="common"` to infer one offset added to every command. Use
`mode="independent"` to infer N offsets for N exposures. Supply starts with
one row per desired local attempt, closed bounds and finite positive diagnostic
steps. Duplicate starts and aliases remain separate candidates. There is no
automatic physical winner. The first independent offset is reported as the
common offset; deviations subtract it, without setting the first actual phase
to zero or changing the kernels.

`exposure_covariance` weights exposure vectors in raw image space.
`fit_mask` is one detector spatial mask shared by all exposures. Fit only its
true sites, then evaluate returned predictions at false sites without refitting.
This common spatial mask keeps covariance whitening from mixing held-out pixels
into training. A wholly withheld exposure has an unconstrained independent
phase; its nominal command does not provide a prediction label.

Each candidate retains the source, full raw predictions/residuals, the complete
covariance-weighted objective, search/diagnostic counts and finite-step stopping
information. `source_rtol` selects the truncated minimum-norm source estimator.
Phase sensitivity projects away only that retained source subspace, frozen at
the candidate. Its relative rank and absolute singular values are conditional
diagnostics. Discarded nonzero source directions may absorb phase changes in
the unrestricted model. Neither `full_local_rank`, stationarity nor a smaller
training residual establishes unique or corrected physical illumination.

The independent demonstration driver separates fixed inputs, observations and
post-fit evaluation:

```sh
uv run --locked python scripts/reference_alignment_ra10_comparison.py prepare \
  --directory artifacts/ra10/example
uv run --locked python scripts/reference_alignment_ra10_comparison.py observe \
  --directory artifacts/ra10/example \
  --authorization 'RA10 coordinator authorizes these sealed observations'
uv run --no-project --python 3.13.12 \
  --with-requirements docs/reports/figures/reference-alignment-ra10/render-requirements.txt \
  python scripts/reference_alignment_ra10_comparison.py render \
  --directory artifacts/ra10/example --output artifacts/ra10/example-figures
```

Preparation requires a fresh empty directory and imports no product code.
Observation freezes all product candidates before loading evaluator truth.
The authorization string makes this deliberate operation visible; it is a
workflow convention, not an access control. Rendering uses saved outputs and
a separate environment with the recorded Matplotlib dependencies; it does not rerun the
fit. The [comparison report](../reports/reference-alignment-ra10-comparison.md)
records the actual observations and their limits.
