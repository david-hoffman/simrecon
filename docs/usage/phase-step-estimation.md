# Local volume phase estimation

`estimate_volume_phases` estimates every exposure phase from corrected images,
known integer carrier bins and fixed complex calibration transfers. It fits one
shared real signed specimen. Nominal commands supply the local starting point;
they are not measured phases or a penalty on the result.

Prepare the `VolumeOrderOtf` through the existing calibration and transfer
adapters. Its complex gains, phase reference and origin already define the
calibration gauge. Keep those declarations consistent with the specimen images.
Do not supply the hidden specimen, actual specimen phases, kernels or true bead
location to the estimator.

```python
from simrecon import estimate_volume_phases

fit = estimate_volume_phases(
    corrected_images,                   # phase/z/y/x; at least five exposures
    order_otf=calibrated_orders,         # one prepared VolumeOrderOtf
    carrier_bins_yx=(0, 1),              # declared integer detector bins
    initial_phases_rad=nominal_commands, # one real angle per exposure, radians
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen/calibration pairing",
)
print(fit.termination, fit.gradient_inf_norm, fit.relative_residual)
```

Every keyword is required. Images and initial phases must be plain finite real
NumPy arrays. Signed images, repeated commands and read-only or strided arrays
are permitted. Tolerances must each be strictly between binary64 machine epsilon
and one; the positive integer evaluation limit has no arbitrary upper cap.
Inputs are snapshotted without changing caller storage or numerical warning
policy. The source label is retained verbatim and does not authenticate provenance.

The finite periodic model uses all five signed orders, a unitary negative discrete
Fourier transform (DFT), and all-axis modular negative-order conjugation, including
even Nyquist bins. The supplied origin is applied only through the stored
transfers. The local solve uses an unregularized real nuisance singular value
decomposition (SVD) and the full analytic profile residual Jacobian, including its
residual-dependent term for off-model data. Transfers are never symmetrized,
registered, independently normalized or refitted.

Inspect termination before using the phases:

- `stationary`: the computed gradient meets the supplied tolerance. This proves
  neither a minimum nor phase accuracy or uniqueness.
- `evaluation_limit`: the solver exhausted its supplied residual evaluation limit
  before the final gradient met tolerance.
- `stagnated`: a positive solver termination did not meet the final gradient
  criterion.
- `nuisance_rank_deficient`: the initial nuisance matrix has unobserved numerical
  directions. No optimizer ran. The returned initial phases and minimum-norm
  specimen are availability diagnostics.
- `rank_changed`: a trial or final canonical reevaluation lost full nuisance rank.
  The returned phases and diagnostics belong to the initial candidate.

`nfev` and `njev` count observed residual and analytic Jacobian evaluator calls,
including the initial and final evaluations that use them. They can exceed the
solver's internal counters. A numerical dependency failure or a nonfinite computed
result raises `SimreconError`; unrelated exceptions and allocation failures
propagate. Error codes and exact input rules are in the
[approved contract](../contracts/phase-step-estimation-v1.md).

Returned angles lie in `[-pi, pi)` radians. Phasors and wrapped deviations are
computed from those returned angles; huge initial commands use native sine/cosine
canonicalization. Array bindings are frozen, while each returned array is an
independent mutable C-contiguous copy.

`specimen_normalized` is dimensionless and may be negative. One observation scale
and one common transfer component scale preserve relative complex gains. Where
representable, `specimen_normalized * image_scale / transfer_scale` restores the
original signal scaling; it does not calibrate physical specimen brightness.
Residual root mean square (RMS), imaginary prediction RMS and calibration reality
defect use normalized inputs. The imaginary contribution of non-real calibration
remains in the objective.

Nuisance rank, projected phase-information rank and the five-column phase-design
rank answer different questions. Information singular values describe normalized
signal strength per radian; they are not confidence intervals. A stationary
full-forward fit may have phases that the existing known-phase separator cannot
use. Check `phase_design_rank` before composing with that separator or volume
reconstruction. Downstream reconstruction regularization adds its own bias and
must be assessed separately from stored-input estimator arithmetic and synthetic
physical phase error.

All results retain `global_ambiguity="unassessed"`. Fixed calibration removes the
free phase/gain gauge, but it does not establish global recovery. Weak side orders,
permanently invisible nuisance modes, symmetries, even-only illumination and
calibration mismatch can leave inaccurate or ambiguous phases. Dense matrix
storage and factorization make this a small-volume development implementation;
large-volume feasibility and physical instrument accuracy remain unassessed.
