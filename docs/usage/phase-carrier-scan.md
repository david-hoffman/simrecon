# Unknown-phase integer-carrier scanning

`scan_volume_phase_carriers` returns an independent local phase fit for every
caller-listed integer carrier. Each row uses the same observations, fixed complex
calibration and nominal starting commands. It preserves order, duplicates, huge
integer provenance and ordinary unavailable outcomes. It selects no winner.
The [scan contract](../contracts/phase-carrier-scan-v1.md) and its normative
[observable estimator](../contracts/observable-volume-phase-estimation-v1.md)
define the numerical model and error boundaries.

```python
from simrecon import scan_volume_phase_carriers

rows = scan_volume_phase_carriers(
    images,                              # real ndarray, phase/z/y/x, N >= 5
    order_otf=orders,                     # paired VolumeOrderOtf
    candidate_carriers_yx=[(0, 0), (1, -1), (4, 3)],
    initial_phases_rad=nominal_commands,  # real ndarray (N,), radians
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared calibration / caller candidate policy",
)
```

All keywords are required. Carriers are integer y/x detector bins. The table
must be a nonempty exact built-in tuple/list of exact two-element tuple/list
rows containing nonboolean Python/NumPy integers, or a plain integer ndarray of
shape `(C,2)`. Floating, Boolean, object, masked and subclass arrays reject.
Signed/unsigned integers, strided/endian/read-only arrays and arbitrarily large
Python integers are accepted. Only indexing reduces carriers modulo detector
size; result provenance retains the original values. The complete table and
all shared inputs are validated and snapshotted before any numerical row.

Each row is a fresh `ObservableVolumePhaseEstimate` with independently owned
mutable arrays and frozen bindings. Repeated candidates actually run separate
fits. `max_nfev` applies separately to each local solve; `nfev` and `njev` count
actual residual/Jacobian evaluations, including inherited reevaluations. There
is no hidden aggregate budget or warm start. Calibration already contains its
origin, relative complex gains and reference gauge. The fit uses those once,
retains all five signed orders and estimates every exposure phase. No new gain,
drift, specimen positivity or carrier refinement is fitted.

Inspect every row's `termination`, ranks and singular values. `stationary`
means a small computed gradient. `evaluation_limit` and `stagnated` retain the
returned local point. `nuisance_rank_deficient`, `rank_changed` and
`no_observable_specimen` are unavailable outcomes; their rows remain present
and later candidates still run. A genuine inherited numerical error aborts
the whole call. Allocation failures and unrelated exceptions propagate; no
partial tuple is returned. Malformed candidate tables use
`invalid_volume_phase_carrier_candidates`; other error codes are inherited.

The specimen is the dimensionless minimum-norm observable representative.
Unobservable modes are missing physical information. Image and transfer scales
remain common across rows. Residual root mean square (RMS) uses the full
`sqrt(N*Nz*Ny*Nx)` normalization, independent of observable dimension. Phase,
nuisance and phase-design rank describe different information. Numerical
availability is not physical identifiability; `global_ambiguity` is `unassessed`.

The retained example recorder runs from the repository root in the locked
environment. Use a fresh output directory for each attempt:

```sh
.venv/bin/python -B artifacts/phase-carrier-scan-20261018/C01/evidence/producer01/record_examples.py --output artifacts/phase-carrier-scan-20261018/C01/evidence/examples02
```

It invokes the actual new scientific producer:

```sh
.venv/bin/python -B artifacts/phase-carrier-scan-20261018/C01/evidence/producer01/produce_examples.py --output artifacts/phase-carrier-scan-20261018/C01/evidence/examples02
```

One group uses direct finite Fourier sums. The second uses explicit spatial
circular convolution and actually composes raw acquisition declarations,
camera correction, raw point-bead calibration and empirical transfer adaptation.
Camera offset and response are supplied; calibration phases, spacing, reference
shift and carrier are declared. Specimen phases have hidden unequal deviations
from independently recorded nominal commands. Each candidate policy includes
a deliberately truth-listed carrier and a detector-period alias. That is
candidate coverage, not an inferred search. An additional zero-transfer control
demonstrates ordinary unavailability. All groups use the fixed calibration
gauge/origin and all five signed orders where transfer is available.

The producer stores scan inputs separately from evaluator-only specimen,
actual phases and carrier truth. A separately constructed spatial operator
evaluates the stored returned-point objective, minimum-norm nuisance and
diagnostics. Signed numerical differences and wrapped phase errors in radians
are reported separately. Product-to-product agreement supplies no numerical
oracle. The recorder retains argv, status, bounded timeout, times, original
dirty Git state, complete before/after source/input/environment fingerprints,
closed manifests and associations. Endpoint equality does not establish
continuous custody; macOS shared-cache library bytes have an explicit census
limit. Later clean-candidate admission is separate and cannot rewrite original
generation records. This guide is frozen before final example generation;
measured results belong in the retained reports and coordinator comparison.

A low residual, full rank or apparently promising single row proves neither
the physical carrier nor global phase recovery. Detector-period aliases can
fit identically. Sparse specimens, symmetries, differing observable dimensions,
calibration error and off-model physics can confound comparisons. These small
finite periodic examples establish no arbitrary-start recovery, measured
instrument accuracy, dense scalability or complete raw workflow. Existing
public behavior remains unchanged; focused checks and examples do not replace
the canonical full gate or fresh independent review.
