# CE08: independent reconstruction acceptance

**Version 1.0. Authorized staged scientific acceptance, not a new estimator.**

The owner explicitly authorized this continuation in the isolated CE08 worktree
from CE07 commit `73fc1b734e3187aee6cdb788aa700e81e298d61a`, tree
`a5b1236fd0dbfbac847c81f8099ac6301dfe1a14`. CE07 PR #77 stays open and
unmerged. The governing behavior is [CE08](c-equivalence-rebuild-v1.md#ce08-independent-reconstruction-acceptance)
and the [common contract](c-equivalence-common-v1.md). This record makes that
request executable; it grants no additional scientific behavior.

## Boundary and sequence

Use the accepted public CE02 preparation, CE03 declared complex optical transfer,
CE04 known-parameter reconstruction, CE05 finite nuisance procedure, CE06 ordinary
stationary acquisition and CE07 explicit workflow. Their public contracts are
the complete equation, signature, input/error, coordinate and source-hash map:

- [CE02](c-equivalence-preprocessing-v1.md).
- [CE03](c-equivalence-optical-transfer-v1.md), declaration/sampling only.
- [CE04](c-equivalence-known-parameters-v1.md).
- [CE05](c-equivalence-carrier-modulation-v1.md).
- [CE06](c-equivalence-acquisition-modes-v1.md), stationary 3D preparation,
  filtering and composition, plus its [ledger](c-equivalence-acquisition-modes-ledger-v1.md).
- [CE07](c-equivalence-workflow-v1.md), including its public
  [map](c-equivalence-workflow-map-v1.md).

No retained source archive or executable is needed to derive these controls.
No historical C output has been supplied. Binary-output agreement stays untested.

The following dependent phases are mandatory. Later-phase product calls wait
for the preceding proof; failed recovery remains an explicit failed result.

1. Blind A independently preregisters small finite controls and derives
   expectations/tolerances without product calls. Fresh blind B audits the
   complete checkpoint. Execute fixed-parameter controls first, then finite
   nuisance controls. Both must prove the selected mathematical mapping before
   the matched recovery acquisition is preregistered.
2. Blind A preregisters one matched acquisition containing declared source modes
   outside the conventional passband and inside declared combined support.
   Freeze physical model, field, sampling, transfer tables, illumination,
   phase/origin maps, counts, source amplitudes, all processing settings,
   independent mathematical image and mode biases, conditioning and recovery
   criteria before product calls. Fresh B accepts the new checkpoint first.
3. Only after the small matched proof, preregister and independently review a
   larger useful reconstruction with explicit physical dimensions and criteria.
   It must exercise the actual workflow, not an unused equivalent primitive.

A may select finite control values and independently justify tolerances from
precision, finite operation counts, conditioning and observer error. Those are
test-design choices within the approved mathematics, not new product semantics.
Preregistration is immutable once a corresponding product call occurs; record
corrections as new revisions with diagnosis, dependency mapping and fresh B.
Never select parameters, seeds, gain, registration or criteria from results.

## Required observables and independent expectations

For each acquired raw sample, define a finite illumination/object/transfer model
in the accepted acquisition coordinates. Derive its raw observations independently
using explicit Fourier modes or finite sums, never a production forward helper.
Declare detector counts separately from source density and source mass. Quantize
raw observations to the declared float32-representable input boundary explicitly;
include the quantization effect in the independent expectation/error budget.

Source regularization is the approved native quotient with denominator
`w^2 + sum eligible g*|a*H|^2`; taper multiplies the numerator after that quotient
at shifted object frequency. Compute the expected mode response and attenuation
before calling the product. A familiar `power/(power+w^2)` factor is valid only
where the actual signed eligibility, noise weights, phase/origin and source
traversal justify it. Use the literal accepted boundary rules elsewhere.

The independent nuisance oracle must implement the declared finite decision
procedure, including coarse ordering, strict finite bracketing/stops, parabolas,
overlap rebuilds and final modulation fitting. An asymptotic optimum or shared
product helper is insufficient. Distinguish intrinsic source decisions and
conditioning from product numerical discrepancies. The small controls must be
well conditioned away from unintended singularities and unclaimed decision
boundaries; deliberate unsupported controls retain their explicit error outcomes.

Every study reports signed ground truth, conventional comparison, independent
mathematical expectation, actual reconstruction, signed residual and frequency
or mode recovery. Use common physical coordinates, intensity units and image/
residual scales fixed in advance. Show negative values. Never fit output gain,
rescale or register a result. Conventional comparison uses the same acquisition
and total dose; phase/direction sums must be normalized from their declared
exposure model rather than given a favorable photon budget. Noise comparisons,
if made, use one preregistered acquisition/noise realization with matched dose;
no stochastic performance claim is required or implied by a noiseless proof.

Report these separately: numerical equivalence to the source mathematics;
physical mode recovery; conditioning; and resolution. A resolution claim
requires a preregistered physically meaningful comparison and resolvability
criterion. Denser output sampling alone supports no such claim. A failed
recovery blocks a passed recovery goal and authorizes no replacement solver.

## Scenario and boundary inventory

| ID | Distinct obligation | Expected proof |
| --- | --- | --- |
| I01 | Small fixed-parameter raw-to-image mapping, including signed/complex phase and amplitude | Independent finite observations, bands, native filtering and image; CE02/03/04 |
| I02 | Small finite nuisance search and actual final fitted modulation | Independent complete finite procedure and trace/decision discriminators; CE05 |
| I03 | Physical acquisition/origin/unit map and raw representation | Explicit forward modes, input quantization, invertible labels and count convention |
| I04 | Above-conventional modes inside combined support | Preregistered mode inventory, conventional loss and recoverable combined response |
| I05 | Wiener/taper bias and conditioning before calls | Independent mathematical expectation and predicted mode amplitudes |
| I06 | Actual full workflow on the matched acquisition | Public workflow output and stage/mode agreement with independent expectation |
| I07 | Larger useful reconstruction after the prerequisite proofs | Frozen larger acquisition/provenance/criteria and full workflow result |
| I08 | Signed common-scale image, residual and mode evidence | Ground truth, conventional, expectation, product and frequency comparison |
| I09 | Honest distinct claims, including failed recovery | Equivalence/recovery/conditioning/resolution/binary statuses stated separately |
| I10 | Supported-domain, error and compatibility limits | Reuse accepted CE02–07 boundaries; no invented rejection or retired API |

Equivalent numeric values are coverage examples. A maps distinct assertions,
credible wrong outcomes, strongest public proof and remaining risks. B audits
omissions and legitimate alternatives. Existing test suites remain binding;
this acceptance study does not need duplicate validation or allocation tests
already proved by the unchanged public boundary.

## Route, ownership and gates

High risk: scientific recovery and independent custom oracles. Fresh native A,
fresh blind B, restricted native C and fresh native D are mandatory. No
Superpowers is invoked. Requested conservative settings are `gpt-6.1-sol`, high,
per project guidance; actual serving and absent metering remain unknown.
Human numeric limits are **not set**. Preserve every attempt/correction and
diagnose each failure before repair. New estimator meaning returns to the owner.

A owns only new `tests/ce08_*` helpers, `tests/test_c_independent_*` tests and
`tests/data/ce08-*` preregistrations/fixtures. B is report-only. Neither reads
production/history, current-state/coverage maps, existing oracle implementations,
source archives or earlier lessons. Use the existing source-free diagnostic
harness before every Python/pytest product probe.

C owns only diagnosed mathematical corrections, if needed, in the existing
CE02–CE07 runtime modules named in its candidate packet. A passing baseline
needs no manufactured product-red and no unnecessary product diff. C may not
edit tests/fixtures, dependencies, gates, policy or unrelated interfaces.
The coordinator owns this contract, task pointer, evidence, figures and report.
D assesses the exact passing candidate independently before implementation lessons.

Coverage policy is approved behavior plus independent risk review; percentages
are advisory. Preserve native/JSON/HTML coverage globally, per package and per
owned file on each required platform, including never-imported owned modules
and relevant subprocesses. No threshold or exclusion changes are authorized.

Before PR readiness: clean exact `make verify PYTHON=.venv/bin/python` with all
13 phases, exactly two workers, strict outcomes, current reader, wheel/source/
RECORD/isolated import/audit and same-run M25 conversion memory increase
<=33,554,432 bytes. No second M25 solely for measurements. Qualify original
Ubuntu24.04 and macOS15 artifacts independently, then obtain fresh D acceptance.
No merge/release or external messages. Stop at CE08 acceptance or an actual
material blocker; do not create, dispatch or message a successor.

All predecessor constraints and accounting are inherited **once by reference**
to the verified immutable CE07 completion manifest recorded in the task pointer.
Keep one Current state in the durable CE08 evidence root. At completion remove
only confirmed task-owned disposable scratch/processes under the existing
housekeeping workflow; preserve this checkout, tracked fixtures, durable evidence,
predecessor/shared environments and uncertain paths.
