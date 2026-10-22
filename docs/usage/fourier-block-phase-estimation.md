# Fourier-block observable phase fitting

`estimate_observable_volume_phases` fits one common vector of exposure phases and
one real nuisance specimen in the supplied calibration gauge. Its required inputs
and result fields are unchanged. Carrier-orbit blocks replace the global dense
specimen matrix. The full-space `estimate_volume_phases` retains its existing path.

The following example runs from the repository root after the recorded producer
has generated its caller-only arrays. Each exposure has phase/z/y/x axes. Phases
are radians, carriers are integer detector bins in y/x, voxel spacing is in
micrometres, and transfer frequencies are cycles per micrometre.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  artifacts/fourier-block-phase-20261018/C01/evidence/producer04/record_examples.py \
  --output artifacts/fourier-block-phase-20261018/C01/evidence/examples01
```

Use a fresh output directory for each execution. The recorder checks the actual
input grammar before dispatch. It retains generator bytes, caller and evaluator
arrays, commands, logs, timestamps, process resources and before/after input pins.
Its endpoint hashes establish neither continuous custody nor universal native
library or process-image identity. Coordinator admission and the full verification
gate are separate later operations.

```python
import numpy as np
from simrecon import VolumeOrderOtf, estimate_observable_volume_phases

path = "artifacts/fourier-block-phase-20261018/C01/evidence/examples01/caller-small.npz"
with np.load(path) as data:
    images = data["images"].copy()
    transfers = data["transfers_centered"].copy()
    nominal = data["nominal_rad"].copy()
    carrier = tuple(int(k) for k in data["carrier_yx"])
shape = images.shape[1:]
orders = VolumeOrderOtf(
    values=transfers,
    fz_per_um=(np.arange(shape[0]) - shape[0] // 2) / shape[0],
    fy_per_um=(np.arange(shape[1]) - shape[1] // 2) / shape[1],
    fx_per_um=(np.arange(shape[2]) - shape[2] // 2) / shape[2],
    voxel_size_um=(1.0, 1.0, 1.0),
    origin_zyx=(0, 0, 0),
    source="declared finite periodic calibration",
)
fit = estimate_observable_volume_phases(
    images,
    order_otf=orders,
    carrier_bins_yx=carrier,
    initial_phases_rad=nominal,
    max_nfev=150,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="Fourier-block usage",
)
print(fit.termination, fit.relative_residual, fit.phase_rank)
```

Only images is positional; every displayed keyword is required. Nominal commands
initialize the local fit. Hidden specimen and actual exposure phases stay in the
separate evaluator record and are never estimator arguments. The synthetic
calibration and declared carrier are required inputs of this finite model.

All frequencies belong to the smallest sets closed under carrier shifts and
three-axis conjugation. A conjugate pair supplies two orthonormal real coordinates;
a self-conjugate mode supplies one. Exact normalized transfer components define
structural support. Unexplained observation rows still contribute to the objective.
Unobservable specimen modes are unavailable physical information, not recovered
physical zeros. The returned specimen is a signed minimum-norm representative.

At every trial and final point, local singular value decompositions supply one
global nuisance singular-value list and one cutoff, using all real and imaginary
observation rows. One common phase optimizer receives the assembled residual and
full analytic derivative, including the residual-dependent term. Phase information
comes from the assembled global matrix. Blocks do not have independent phase fits
or numerical rank thresholds. Non-Hermitian calibration is retained as supplied.

Inspect termination before interpreting phases. `no_observable_specimen` and
`nuisance_rank_deficient` return initial availability diagnostics without an
optimizer. `rank_changed` restores the initial candidate. `evaluation_limit` and
`stagnated` do not satisfy the supplied gradient criterion. `stationary` reports a
local gradient condition; it proves no minimum, global uniqueness, physical phase
accuracy or correct carrier. Scan and selection still return all caller-ordered
rows from independent identical starts, including aliases and unavailable rows.

The recorded experiment uses independent finite real-space illumination and
circular convolution to generate observations. A separate direct-sum observer
checks the stored normalized objective, singular values, minimum-norm specimen,
full derivative and projected information. It reports signed estimator-minus-target
errors separately from wrapped phase-minus-truth errors. An algebraic off-model
control and a zero-transfer availability control are explicit. Complete scans
include duplicate/aliased hypotheses and independently initialized row comparisons.

The scaling group holds six exposures, lateral shape 8 by 16 and carrier (0, 8)
fixed while increasing axial extent from 2 to 4 to 8 planes. All five signed orders
and retained support are present. Each extent runs in a fresh process and records
actual elapsed seconds and native Darwin peak resident bytes, with pre-fit peak
reported separately. The peak is a process
high-water mark, not an allocation trace or baseline-subtracted estimator peak.
Numeric arrays are binary64 real or complex128. Block geometry is reported with
observed outputs. No byte or time acceptance cap is imposed.

Storage is block-local for nuisance bases, operators, designs and factors. For
largest frequency block size cmax, dense leading storage scales as
O(N*M*cmax + N*N*M + M + r). The residual Jacobian and phase-information matrix
still each have 2*N*M by N entries. Long coprime carrier cycles can produce large
blocks. These measurements contain no old-backend timing comparison, speedup
claim or evidence that an entire 512 by 512 by 64 workflow is feasible. Fixed
transfer/carrier assumptions, stationarity, finite periodic boundaries, local
initialization and unresolved physical calibration applicability remain limits.

See the [execution contract](../contracts/fourier-block-phase-estimation-v1.md),
[observable estimator contract](../contracts/observable-volume-phase-estimation-v1.md)
and [phase fitting guide](phase-step-estimation.md) for the preserved boundaries.
