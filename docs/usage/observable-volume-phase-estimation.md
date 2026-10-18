# Observable-subspace local volume phase estimation

`estimate_observable_volume_phases` fits every exposure phase in a supplied,
fixed complex calibration gauge. It removes exactly structurally invisible
real specimen Fourier modes before the unregularized nuisance fit. The
[contract](../contracts/observable-volume-phase-estimation-v1.md) defines the
stored-input model, validation, errors and numerical limits.

```python
from simrecon import estimate_observable_volume_phases

estimate = estimate_observable_volume_phases(
    images,                         # real ndarray, phase/z/y/x, N >= 5
    order_otf=orders,                # already paired VolumeOrderOtf
    carrier_bins_yx=(0, 1),          # supplied integer y/x detector bins
    initial_phases_rad=commands,    # real ndarray (N,), radians
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen/calibration pairing",
)
```

All keywords are required. Signed observations, non-Hermitian zero order,
weak or zero transfer, repeated commands and finite huge angles/carriers are
permitted. The full calibration record and every input sample are validated
before any unavailable result. Arrays are independently owned, mutable,
native and C contiguous; record bindings are frozen. The existing
`estimate_volume_phases` interface retains its behavior.

Structural visibility and numerical information are different. After common
component normalization, a specimen frequency is directly visible if any
signed transfer at its carrier-shifted detector frequency has a nonzero real
or imaginary component. Modular Hermitian closure on all three axes includes
the negative-frequency partner. A pair contributes two real dimensions; a
self-conjugate frequency contributes one. `observable_fourier_mask` stores
that exact Boolean closure in centered frequency order.
`observable_dimension = r` counts its entries, and
`unobservable_dimension = M-r`, where `M = Nz*Ny*Nx`. No tolerance or initial
phase cancellation deletes a structural mode. Normalization underflow can
make a stored component zero; weak remaining nonzero components stay structural.

The fit keeps all `2*N*M` real/imaginary observation rows, including unexplained
signal, and uses a real orthonormal Fourier-orbit basis `Q`. Its nuisance
matrix is `B = A*Q`; singular value decomposition (SVD) solves the unregularized
least-squares problem. Numerical rank counts singular values strictly above
`eps * (2*N*M) * sigma_max`. Rank is required to equal `r`, not `M`.
The full residual Jacobian includes its residual-dependent term; the separately
reported projected phase information is a different matrix.

`specimen_normalized` is the full z/y/x minimum-norm observable representative,
dimensionless in normalized observation/transfer units. Excluded modes are
unavailable. Their zero target Fourier coefficients are not measured physical
zeros. A floating-point Fourier transform of the returned spatial array can
have rounding-level coefficients outside the mask. `image_scale = b` and
`transfer_scale = t` are common maximum-component scales (one for an all-zero
input); `u*b/t` changes units where representable but supplies no physical
intensity calibration. RMS means root mean square. Residual and imaginary
prediction RMS use `sqrt(N*M)`, including when `r < M`.

Inspect `termination` before interpreting phases:

- `no_observable_specimen`: `r=0`; canonical initial phases, zero specimen,
  residual equal to normalized data, empty nuisance singular values, zero phase
  information and gradient. No nuisance SVD or optimizer runs. Evaluator counts
  are actual counts, including zero when no evaluator is entered.
- `nuisance_rank_deficient`: retained modes are numerically deficient at the
  initial point; a truncated minimum-norm availability diagnostic is returned
  without optimization.
- `rank_changed`: an optimizer trial or final canonical reevaluation loses full
  retained rank; the initial candidate and its diagnostics are restored.
- `stationary`, `evaluation_limit`, `stagnated`: the returned candidate retains
  full nuisance rank. Stationary means only a small computed first derivative.

Phase rank, nuisance rank and the five-column phase-design rank have separate
meanings. All N phase coordinates, including a common offset, remain in the
fixed supplied calibration gauge. Phase zero is not anchored. Changing that
gauge requires the corresponding order-dependent complex transfer rotation.
No outcome certifies a minimum, global uniqueness, correct physical phases or
an informative separator design. `global_ambiguity` remains `unassessed`.

The retained local example producer can be run from the repository root with
the locked Python 3.13.12 environment. Choose a fresh output directory for
each attempt:

```sh
.venv/bin/python -B artifacts/phase-observable-subspace-20261018/C01/evidence/producer02/record_examples.py --output artifacts/phase-observable-subspace-20261018/C01/evidence/examples02
```

The recorder runs this actual scientific command, retaining its arguments,
working directory, times, status, logs, input hashes and before/after Git state:

```sh
.venv/bin/python -B artifacts/phase-observable-subspace-20261018/C01/evidence/producer02/produce_examples.py --output artifacts/phase-observable-subspace-20261018/C01/evidence/examples02
```

Two independently generated groups use distinct specimens, phase errors,
grids and complex kernels. One generates real-space periodic convolution;
the other evaluates an independent direct Fourier sum. Both retain invisible
axial specimen content, meaningful `0 < r < M`, and initial commands different
from hidden phases. The third example actually composes `declare_acquisition`,
`calibrate_raw_point_bead`, `adapt_empirical_volume_response`, then the new fit.
It declares counts, supplied offset 13 counts, response 1.7 counts/electron,
actual calibration phases and z/y/x spacing in micrometres. Calibration and
specimen reference origins differ; the explicit adapter shift pairs them.
Nominal acquisition commands remain metadata. Known calibration phases,
carrier, response relation and pairing are supplied, not inferred.

Reports and complete numerical arrays live in the chosen output directory.
`summary.json` and per-group reports distinguish structural visibility,
independent stored-objective/estimator error, wrapped phase error in radians,
observable specimen error and unavailable hidden specimen content. The
reviewed direct Fourier observer supplies numerical expectations; product
diagnostics never supply their own expected values. Raw-calibration reports
compare actual components and adapted transfers with independent generation
truth. Manifests and associations preserve the original generation state,
which can be dirty. A later clean candidate admission is a separate coordinator
record; it cannot rewrite generation history. This guide is frozen before
generation, so results and later admission pointers belong in separate files.

These are small, noiseless finite periodic examples with a known integer
carrier and fixed calibration. They establish neither measured instrument
accuracy nor arbitrary-start recovery. Model or calibration error can change
both phases and specimen; a low stored-model residual does not measure that
physical error. Dense execution supplies no scalable full-volume guarantee.
This operation does not complete the raw workflow or phases 7–9. Actual
examples and focused checks do not replace full verification and fresh
independent review.
