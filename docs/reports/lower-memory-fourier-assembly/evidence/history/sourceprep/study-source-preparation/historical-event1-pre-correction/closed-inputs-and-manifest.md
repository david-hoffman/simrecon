# FA120 closed-input proposal and draft manifest

Source preparation only, dated 2026-11-16 by supplied task date. No runtime
identity or observation is bound by this document. The unconditional module
hold precedes all imports. Removing it needs a later independently reviewed
ROOT-bound revision; there is no executable grant checker or bypass.

## Bound reference inputs

- Authoritative request: `/workspace/work/campaign/issue-120.md`, SHA256
  `d3b70bb7c96efb7b733b7133134fc45779013ad5ee23c384d49781743f59d756`.
- Own contract: `docs/contracts/lower-memory-fourier-assembly-study-v1.md`,
  SHA256 `7e0ee0e576237883c8ba9c7c99e244df1e1fd962fef830b57937bd3b09cdab1c`.
- External integration/evidence plan: `../integration-evidence-plan.md`, SHA256
  `2805798e5afda2cb1f208ab41b55f2fd5877a41c2d1980feb56687e3e9076490`.
- Accepted116 method/source commit `158776ade28079276304d49a6b973eccbf4109c9`.
  Assembly module SHA256
  `edb87b64e1691b7f437194aabc0df8d4ab22e3e67b6b05639dbd3bad26e2c645`.
  Own unchanged120 commit `c962ccfff03ca78de31e6a0af746ec091e822989`
  supplies identical assembly module bytes. These are source references only.
- Fixture source `tests/reconstruction_summary_fixture.py`; use its `workload`
  and `identity` definitions. Actual-parent fixture bytes must be rebound.
  Current read-input hashes appear in `read-input-sha256.txt`.

## Closed primary rows

| Condition | Native (T,D,Z,Y,X) | Mode | P/O/L/A | Per-time output |
| --- | --- | --- | --- | --- |
| Ksmall | (1,3,8,32,32) | 3d | 5/3/2/1 | (8,64,64) |
| Kmedium | (1,3,8,64,64) | 3d | 5/3/2/1 | (8,128,128) |
| K2D | (2,2,1,12,16) | 2d | 5/3/2/2 | (2,24,32) |

Each uses the approved multifrequency `workload(shape,search=False,mode=mode,
layout="radial")` with only the declared A2 change for K2D. Uniform P5 phases,
background0, edge0, equalization off, dxy=dz=1um, unit optics (500nm, NA1,
immersion1), Wiener0.5, no suppression, no taper. Direct preparation omits only
the workflow-adapter `phase_policy="uniform"` key; absence of `phases_rad`
selects CE06 uniform phases. No phase-policy domain change is proposed.

Explicit supplied parameters are closed before any trial: for direction d,
theta=d*pi/D, carrier=(cos(theta),sin(theta))/8 cycles/um; modulation entries
are `(1+d/16)*(1/2+i/4)` and `(1+d/16)*(1/4-i/8)`. They are allowed supplied
values, not a fit or an assertion that they recover physical truth. All
conditions use omit=False and explode=1 in the measured loop. W3 separately
describes finite omit/explode arithmetic witnesses; it creates no measured
matrix expansion. No estimator source or pending estimator evidence was read.

Every child independently creates the same caller/transfer/bands and calls
public `reconstruct_known` for its filtered coefficients/resolved parameters
and coordinate vectors. It drops that setup result/image before the timed
complete T/D/order assembly loop, retaining caller inputs and filtered arrays.
This is a known-stage kernel fixture binding, not the workflow fitted-parameter
benchmark. Public setup's earlier baseline assembly can mask the subsequent
kernel peak; report that limit. No alternative filter or preparation is authored.
**Blocking method/scientific review obligation:** because every variant first
runs baseline public assembly, equal terminal high-water values cannot support
a lower-peak no-go when pre-call setup dominates. The whole-process effect is
then inconclusive. Sampled current RSS retains its interval/transient limits.
Do not expand the harness/framework to repair this source proposal now.

Variants are baseline actual `kp.assemble_signed_image`, one disposable-padding
candidate, and retained-control. The candidate requests overwrite on the same
SciPy `ifftn`, default axes and forward norm; the2D branch aliases the initialized
private volume and transforms/assigns only plane0. The control uses the unchanged
non-destructive inverse and keeps one padding owner across all harmonics,
directions and times, clearing the WHOLE buffer before each embedding. Neither
control nor phase rewrites can become another recommendation.

| Repetition | Within each condition, proposed fresh-child order |
| --- | --- |
| 1 | baseline, candidate, retained-control |
| 2 | candidate, retained-control, baseline |
| 3 | retained-control, baseline, candidate |

Condition order Ksmall, Kmedium, K2D. Exactly 27 proposed primary children.
No automatic retry, growth, 256, extra condition, workflow phase or allocation
exhaustion. Counts are protocol choices, not an inherited budget/admission.

The exact proposed IDs below all have state PENDING, actual command/output/
environment/grant UNBOUND. These are names, not execution authorizations:

| Condition | Repetition | Ordered IDs |
| --- | --- | --- |
| Ksmall | 1 | Ksmall-r1-baseline; Ksmall-r1-candidate; Ksmall-r1-retained-control |
| Ksmall | 2 | Ksmall-r2-candidate; Ksmall-r2-retained-control; Ksmall-r2-baseline |
| Ksmall | 3 | Ksmall-r3-retained-control; Ksmall-r3-baseline; Ksmall-r3-candidate |
| Kmedium | 1 | Kmedium-r1-baseline; Kmedium-r1-candidate; Kmedium-r1-retained-control |
| Kmedium | 2 | Kmedium-r2-candidate; Kmedium-r2-retained-control; Kmedium-r2-baseline |
| Kmedium | 3 | Kmedium-r3-retained-control; Kmedium-r3-baseline; Kmedium-r3-candidate |
| K2D | 1 | K2D-r1-baseline; K2D-r1-candidate; K2D-r1-retained-control |
| K2D | 2 | K2D-r2-candidate; K2D-r2-retained-control; K2D-r2-baseline |
| K2D | 3 | K2D-r3-retained-control; K2D-r3-baseline; K2D-r3-candidate |

## Draft identity slots requiring ROOT binding

| Identity or prerequisite | Value |
| --- | --- |
| actual119 parent SHA/tree | UNBOUND |
| post118 affected116 refresh and independent scientific acceptance | UNBOUND |
| actual relevant peak/rank/current-largest/scaling/16GiB premises and SCI disposition | UNBOUND; ROOT d1/b5 says unavailable |
| actual120 integrated candidate SHA/tree, clean material state | UNBOUND |
| actual assembly, fixture, contracts, adapters, lock, measurement method hashes | UNBOUND |
| held experimental module/delta revision | local proposal hashes in source handoff only; actual runtime binding UNBOUND |
| Python/NumPy/SciPy executable/version/build, FFT backend/threads/workers | UNBOUND |
| supported overwrite semantics, ownership/copy/workspace evidence | UNBOUND |
| Ubuntu/kernel/host/cgroup/current RSS/headroom/resource bounds | UNBOUND |
| exclusive interval, exact-PID owner/observer, stop/deadline/grant | UNBOUND |
| each row argv/source/environment/grant/nonces/output paths | UNBOUND |
| generated input/filtered/coordinate/output arrays and hashes | UNBOUND |
| native child terminal usage/current RSS samples/timing/exit statuses | UNBOUND |
| qualification, recommendation, scientific review, public binding evidence | PENDING |

No actual117/118/119 material or old116 grant supplies these slots. #113 is
absent; storage remains float64/complex128. Historical EA observations in the
external plan establish no actual-parent peak or saving. Fresh post118 scientific
review must dispose actual design premises before dependent reliance.

## Proposed observation boundary

`child(condition,variant,repetition)` is an inert source entry, not a launcher.
There is no `__main__`, argv parser, admission framework, runtime grant validator,
child creation, reaper or monitor. Its shape/variant membership check merely
closes inputs. ROOT later rebinds its existing apparatus; this module has no
authority to do so. It imports the existing fixture module through the future
reviewed module search path; that path is UNBOUND.

Timer starts immediately before assembly under the original operation wrapper
and ends on return. Hashing, exclusive-create full little-endian image-byte
archival and JSON observation follow timing. Native Linux self high-water
snapshots are cumulative and reported in KiB with multiplier1024; they cannot
be subtracted into a kernel allocation or peak. Existing external apparatus
must supply timestamped sampled current RSS and exact-PID terminal wait4,
failed/incomplete rows, sampling interval and terminal status. The source does
not recreate or certify that apparatus. Setup, import, hashing, archival and
teardown can dominate whole-child high-water. Output identity does not replace
a complete byte comparison of archived same-shape/dtype results, including
signed-zero bits. Input identity before/after checks are supplemental ownership
evidence, not a demonstration of private allocation or internal precision.
