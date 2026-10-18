# Caller-policy selection of unknown-phase carriers

`select_volume_phase_carrier` runs the complete independent phase-fit scan, then
applies your explicit residual and local phase-rank limits to stationary rows.
It selects a row only when exactly one passes. It retains every row, including
unavailable fits, duplicates and detector-period aliases. The
[selection contract](../contracts/phase-carrier-selection-v1.md),
[scan contract](../contracts/phase-carrier-scan-v1.md) and normative
[observable estimator](../contracts/observable-volume-phase-estimation-v1.md)
define the public and numerical boundaries.

```python
from simrecon import select_volume_phase_carrier

selection = select_volume_phase_carrier(
    images,                              # real ndarray, phase/z/y/x, N >= 5
    order_otf=orders,                     # fixed paired complex VolumeOrderOtf
    candidate_carriers_yx=[(0, 0), (1, -1), (4, 3)],
    initial_phases_rad=nominal_commands,  # real ndarray (N,), radians
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen / calibration pairing",
    max_relative_residual=0.02,           # caller choice, dimensionless
    min_phase_rank=1,                     # caller choice, exact integer
)
if selection.selected_index is not None:
    row = selection.candidates[selection.selected_index]
else:
    print(selection.failure_code, selection.eligible_indices)
```

All nine keywords are required. Images, calibration, integer y/x detector-bin
candidates and solve controls inherit the scan's validation and error rules.
Each candidate starts independently from the same nominal commands; these are
starting values, not measurements of actual phases. Fixed calibration already
contains relative complex gains, origin and reference gauge. All five signed
orders enter the inherited periodic model. The fit estimates every exposure
phase without fitting a new gain or drift.

`max_relative_residual` accepts nonboolean Python or NumPy integer/floating
scalars. The source value and converted binary64 value must both be finite;
the converted value must be >=0. Both signed zeros are valid. Finite values that
underflow to signed zero use that converted zero, including a negative source
value that converts to negative zero. There is no upper bound beyond conversion
finiteness. Complex values, strings, arrays (including zero-dimensional arrays),
`Fraction`, `Decimal` and unrepresentably large integers reject.

`min_phase_rank` accepts a nonboolean Python or NumPy integer >=0. Extraction
preserves its exact Python integer value; there is no exposure-count or machine
integer cap. Zero permits rank-zero stationary rows, even for zero observations.
An arbitrarily large threshold is valid and can simply exclude every row.
Floats and arrays reject. Invalid policy raises `SimreconError` with code
`invalid_volume_phase_carrier_selection_policy` before numerical scanning.
Only expected type/value/overflow errors at policy extraction boundaries
translate; allocation failures and unrelated exceptions propagate.

Eligibility uses the returned fields exactly and inclusively:

```text
row.termination == "stationary"
AND row.relative_residual <= converted residual limit
AND row.phase_rank >= exact rank limit
```

No tolerance, residual minimization, rank preference, hidden information cutoff
or deduplication changes this relation. `evaluation_limit`, `stagnated`,
`nuisance_rank_deficient`, `rank_changed` and `no_observable_specimen` never pass.
The complete scan finishes before selection. An early eligible row cannot hide
a later fit, unavailable row or operation-time failure. Inherited errors abort
the call with their original codes and no partial result.

The four result bindings are frozen. `candidates` is the complete ordered tuple
of existing `ObservableVolumePhaseEstimate` records. Its arrays remain mutable
and independently owned across fields, rows and calls. `eligible_indices` is an
increasing tuple of zero-based Python integers. `selected_index` is its sole
index for one eligible row; otherwise it is `None`. `failure_code` is `None`
for one, `no_acceptable_volume_phase_carrier` for none and
`ambiguous_volume_phase_carrier` for multiple. These failure codes are values,
not raised errors. There is no extra winner copy. Duplicate or aliased passing
rows count separately and therefore remain ambiguous.

The retained example recorder runs from the repository root using the current
locked environment and the declared Java context. Use a fresh output directory
for every attempt:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3.13 -B artifacts/phase-carrier-selection-20261018/C01/evidence/producer01/record_examples.py --output artifacts/phase-carrier-selection-20261018/C01/evidence/examples01
```

The recorder actually invokes this scientific producer:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3.13 -B artifacts/phase-carrier-selection-20261018/C01/evidence/producer01/produce_examples.py --output artifacts/phase-carrier-selection-20261018/C01/evidence/examples01
```

One observation group uses explicit finite Fourier sums with asymmetric complex
side transfers. The second uses direct spatial circular convolution and actually
composes raw declarations, camera correction, point-bead calibration and transfer
adaptation. The raw example supplies a camera offset of 13 counts and response
of 2.1 counts per signal unit. Calibration phases, carrier, voxel spacing and
reference shift are declared inputs. Both groups have seven exposures with
hidden unequal phase deviations and use all five signed orders. The producer
records nominal commands, candidate tables and residual/rank policies before
fitting, separately from evaluator-only specimen, actual phases and carrier.
The deliberately included physical carrier is candidate coverage, not an
inferred search result.

Each group exercises sole acceptance, no acceptance with a huge rank threshold,
alias/duplicate ambiguity, a loose policy, a one-evaluation control and a
zero-transfer unavailable control. An independent spatial operator checks
returned-point objectives, nuisance vectors and diagnostic fields. Signed
numerical differences, wrapped phase errors in radians, actual residual and
Jacobian evaluation counts (`nfev`, `njev`) and signed policy margins are stored
per row and decision. Policy comparisons use returned diagnostics as observations;
those comparisons alone establish no diagnostic accuracy. Measured results live
in ignored reports and the coordinator's comparison; this guide settles before
the final scientific execution.

The recorder retains actual arguments, working directory, executable, timeout,
start/end times and return status. It fingerprints original scientific sources,
frozen tests/fixtures/contracts, guides, locks, build/check inputs and dependency
and executable bytes independently before and after execution. Closed manifests
and associations pin the actual producer and output roots, including evaluator
inputs and all reports. Endpoint equality cannot prove continuous custody or
absence of transient changes. macOS shared-cache system libraries have no
regular original files to hash; platform/build and that census limit are
recorded. Original dirty generation records stay original. Clean-candidate
admission and the canonical full verification gate remain coordinator work.

Stationarity does not prove a minimum. A small residual, full phase rank or sole
eligible row does not identify the physical carrier, prove global uniqueness,
verify calibration applicability or provide uncertainty bounds. Aliases,
specimen symmetry, sparse support and differing observable dimensions can
confound policy decisions. These small noiseless periodic examples establish no
measured instrument accuracy, arbitrary-start recovery, dense scalability or
complete raw workflow. Continuous carrier, drift and gain inference remain
outside this interface.
