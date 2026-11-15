# HP114 frozen study manifest — source-method preparation v2

This is a source-prepared experimental protocol, not numerical evidence. All
scientific cases below are frozen before candidate trials. The standalone
[study.py](study.py) is an experiment, outside runtime/test roots. The task is the
sole execution state; this manifest records reproducibility inputs, not competing
Current state. Artifact SHA256 values and final identities belong in the root's
external receipt, avoiding self-referential hashes in tracked bytes.

This continuation follows `source-method-continuation.md`, SHA256
`558a02160711c50d309d32c3df2d99677b2b5ec9694d8ca24d6cebc9950661f6`.
Admission was clean `f2d15d38026da4a8b58bd8eca94b798660618608`;
original source preparation remains at `e42f978b10396fc1f015880c0fe82db786a76011`.
Coordinator task/ledger commit `135c8403260cd407b59d8f4247fc0ebf1242fa1c`
changed no scientific source or initial artifact. Original formulas, ten W/K
rows and repetitions remain. These additions correct method gaps before any
candidate trial. The source-only continuation initially allowed no Python/checks.
A later narrow packet, `preparation-checks-launch-hold.md`, SHA256
`69f7c25e754135f510866f4d5e716462041681a0786bdfc3278b94de8f00c00a`,
permits only owned-file AST/compile-without-import and pinned Ruff/format via
Ubuntu `uv run --locked --no-sync`. Those preparation checks now pass after
preserved style corrections; they execute/import none of this harness or product.
All report/control/scientific/lifecycle execution remains held. **Resource parent
and child routes are unconditionally quarantined, not ready for runtime release.**
Root's actual #116 Q1 challenge established that this interpreter rejects
`posix_spawn(..., setsid=True)` before returning a child PID. Preparation passes
do not repair or qualify that capability. No retry/fallback was performed here.

## Scope and identities

Public source baseline/initial HEAD: `b344e41a8b52de76d7cbbf8450319893904c3b8f`.
Branch/worktree: `chore/114-half-precision-study`, `/workspace/work/issue-114`.
No accepted #112 witness/result has been supplied to this role or reused.
No private ancestry, retained C implementation, retired API or product change.

| Material input | SHA256 at source preparation |
| --- | --- |
| Contract | `bb5963ce268e81dabf8773f8bce5f1b37e8153e2d18886ddef1e5766bd384284` |
| Investigator packet | `712f72dec72690ed87a2a8228884e8fcecbf4185665676a93e62ee66528d1afd` |
| Initial task input, before coordinator state refresh | `4bbd498cb84a4d00e76e20bcb0cbfa15a2043765f6e3bdd17ec235932c87af40` |
| `acquisition/preparation.py` | `2c5bb8eb536f8b1edd0c4d155da603bb66c838ce2298a899cdd6f23a3eedd0da` |
| `acquisition/modes.py` | `4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1` |
| `reconstruction/parameter_estimation.py` | `f9a924d277518cdb0717c7fe82961f3d36a480109bcbef9f8d19b42fdae7d7e8` |
| `reconstruction/known_parameters.py` | `34fbc93aa5ac9a1f4eb24b1f39ce576a1bb7770238c62cab72412de120722295` |
| `workflow/reconstruct.py` | `50a4ce199f0cceca6ba9147a1ee218441b1b5588c03beabecef95828802e28fa` |
| `workflow/summary.py` | `f0ccb2f0c566ba255eb02b0047c7000c3fe6530a0a7c797224e185d3f31ebb2e` |
| `uv.lock` | `222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b` |

Product paths above are under `src/simrecon/`. The harness checks those material
hashes before numerical imports and records the current mutable task hash at run
time. Root must reconcile actual candidate/base/tree and supporting source identity
before granting a run; the fixed BASE string is a declared baseline, not a Git
measurement. Coordinator-only task/ledger refresh does not change science inputs.

Root reports preflight attempt 1 passed in Ubuntu 24.04.5,
`simrecon-campaign-ubuntu`, per-worktree `.venv`: Python 3.13.12, NumPy 2.5.3,
SciPy 1.18.1, `/workspace/work/campaign/preflight-114-attempt1.log`. This is
root-owned evidence, not an investigator run or full gate. Versions, interpreter,
loaded source, CPU/affinity, OS, thread state, allocator variables and transform
source hashes will be recorded after numerical authorization.

Read-only installed-source inspection found:

| Source under `.venv/lib/python3.13/site-packages/` | SHA256 / observed source fact |
| --- | --- |
| `numpy/fft/_pocketfft.py` | `c809e89c05cf7b97d75abd73fdda8454403fe67772d4e435aa35bc4ce723eeb6`; output dtype selection uses `result_type` |
| `scipy/fft/_duccfft/helper.py` | `0d9c409a6dcf9cdb85cbc67aa203f7b80907036b23735f1fdceb7af1268ee9c5`; `_asfarray` explicitly converts float16 to float32 |
| `scipy/fft/_duccfft/__init__.py` | `2a6f2d9ae3ba21b77fd3d63c45931f6fc6a012858263af9c4f914a452e6ff30b`; declares pyduccfft backend |

`scipy/fft/_basic_backend.py` imports `_duccfft`. Inherited pocketfft names do
not identify this installed SciPy route. Source facts alone establish no observed
output dtype, native arithmetic precision, timing or runtime availability.

## Frozen generator and physical declarations

No random generator or seed. Shapes use `(T,D,P,Z,Y,X)`; detector pitch is
`dxy=0.1 um`, `dz=0.2 um` in 3D, `dz=0` in true 2D. Orders include zero:
W01 O2, all others O3. Lateral zoom L2, axial zoom A1. Pixel indices are first
sample origins for Fourier sums; final coordinate labels are centered.

For the ordinary specimen define

`S(z,y,x) = 3 + sum a(k)*cos(2*pi*(kx*x/X + ky*y/Y + kz*z/Z) + beta(k))`,

where `kz=0..min(Z,2)-1`, `ky=-3..3`, `kx=0..3`, excluding `(0,0,0)`,
`a(k)=32/(1+kx^2+ky^2+kz^2)` detector counts and
`beta(k)=(kx+2*ky+3*kz)*pi/7`. This finite Fourier series is a signed analytic
witness, not a biological or physically certified specimen. Coincident conjugate
terms sum literally; no fitted coefficient, gain or clipping is applied.

Direction angles `theta_d=d*pi/D`; nominal fundamental vectors
`k_d=1.25*(cos(theta_d),sin(theta_d)) cycles/um`. Uniform phase angles
`phi_p=2*pi*p/P`. W06 adds exactly `[0,1/32,-1/64,1/128,-1/32] radians`.

`R(t,d,p,z,y,x)=B + S(z,y,x)*I(t,d,p,y,x)`;
`q=2*pi*(kx_d*x*0.1+ky_d*y*0.1)+phi_dp`;
`I=1+a1(t)*cos(q+delta(t))+a2(t)*cos(2*q+0.3+2*delta(t))`.
W01 omits the second harmonic. At t0 `(a1,a2,delta)=(0.55,0.23,0)`;
at t1 `(0.37,0.16,0.41)`; no other times exist. Background B=256 counts,
except W06 B=128 counts. Public input is explicitly `float32(R)`;
`R` remains separate float64 reference. Casting is required by the existing
exact-float32 raw boundary and its discrepancy is recorded independently.
H1 compares `float16(float32(R))` with both the unquantized public baseline and
the exact same half values promoted to float64. Dtype-route equality and total
quantization error are separate questions.

For W06 replace S, with `a=2*pi*(x/X+y/Y)`, by

`8*cos(a)+(-8+2^-9)*cos(a+2^-10)+2*cos(2*pi*y/Y)+sin(2*pi*x/X)+0.25*cos(2*pi*z/Z)`.

The first pair nearly cancels; background subtraction produces signed samples.
No assertion that a half cast preserves the residual is made before measurement.

Optics: wavelength 520 nm; numerical aperture 1.2; immersion index 1.33.
Transfer is a complete radial `(O,64,64)` complex64-exact table, constant per
order: `H_m=1-m/8+i*m/32`; increments `dkr=dkz=0.25 cycles/um`.
It is artificial, nonzero and complex; no physical calibration claim. Retain
caller complex64 samples plus `declare_otf`'s complex128 record. No fitted OTF.
No edge treatment (`edge_pixels=0`), equalization, off exposure, drift, omission,
singularity suppression or output taper. Wiener=0.125, increment=0;
`filter_overlaps=True`, explode=1. All unspecified public defaults stay recorded
in full result declarations. No change to source error precedence or criteria.

Known rows set `search_carriers=False`. Workflow line spacing is 0.8 um in W01,
0.4 um in O3 rows, yielding nominal magnitude 1.25 cycles/um. Initial angle=0;
directions use positive pi/D steps. W03/W04 enable search and time-zero reuse.
W03 additionally sets amplitude floors `[0.75,0.5]` and `fit_all_phases=False`,
so raw fits, floor-applied flags and higher-phase replacement are distinguishable.
No floor is a fitted numerical-acceptance cutoff. W04 has no floors/replacement.
Wider qualification must establish the actually reached branches before comparison.

## Ten rows and finite case inventory

| Row | Shape or exact finite variants | Intended qualification / experiment |
| --- | --- | --- |
| W01 | `(1,1,3,1,16,16)` | True 2D/O2, known carriers, signed output; contiguous read-only and finite strided read-only same-value public inputs; half workflow/acquisition acceptance; nonfinite/shape failures |
| W02 | `(1,3,5,4,16,16)` | Known carriers/O3, 3D; also chosen half `prepare_bands` acceptance |
| W03 | W02 | Search each direction, ordered maxima/alias/bracket/parabola; floor and phase-replacement decisions |
| W04 | `(2,3,5,4,16,16)` | t0 searched, t1 time0-reused; new time-specific modulation despite changed illumination |
| W05 | `(1,3,5,4,32,32)` | Same physical equations/settings as W02, Y/X resource step only |
| W06 | W02 | Nonuniform full-rank phase design, near cancellation, signed background subtraction |
| K01 | 16 real values `0,-0, +/-2^-25,+/-2^-24,+/-2^-14,+/-1,+/-65504,+/-65520,+/-70000`; paired complex vector uses reversed imaginary values | Range, half rounding/subnormal/zero/signed-zero/overflow; explicit little-endian component storage |
| K02 | Eight values `[0,-0,-128,-1,-2^-12,2^-12,1,128]` scaled by each of three alphas | Alpha from W02/W05 and `(D,Z,Y,X,L,A)=(3,32,512,512,2,1)` metadata only; no volume allocation |
| K03 | 2 lengths (16,4096) x 4 magnitudes (`2^-12,1,256,1024`) x 2 patterns | 16 cases: lower=`a+i*a/8`, higher=`sign*(3*a/4-i*a/16)`; all-one or alternating signs; exact dyadic energies/cross sums, half component products/reduction versus quantized operands/wider reduction |
| K04 | Finite subcases below | Formula witnesses, explicitly limited scope, not private helper calls or new public coverage |

K04 frozen subcases:

- Unnormalized inverse: 16 coefficients all `1024-256i`; exact origin sum
  `16384-4096i`; forward-normalized inverse convention.
- Equal-spacing powers: `[1,4,3]` fitted; `[1,2,3]` zero curvature;
  `[1,2,3+2^-12]` outside 1.5 bins; `[1,1+2^-12,1]` near tie.
  Slope `(plus-minus)/2`, curvature `plus+minus-2*center`, offset `-slope/curvature`;
  exact zero curvature and outside-range fallbacks remain literal.
- General three-point coordinates/powers: `[(0,1),(1,4),(2,3)]` fitted,
  `[(0,1),(0,4),(2,3)]` duplicate coordinate,
  `[(0,1),(1,2),(2,3)]` zero curvature. Difference slopes at interval midpoints
  determine the parabola vertex; no guard/tolerance is added.
- Ordered objectives `[1,1+2^-12,1]`: first maximum and strict `>` before/after
  half storage. Exact equality retains earlier index.
- Regression lower `[1,-1,1,-1]`, higher gain 1 (intentional equal-energy
  singularity) or `1+2^-12` (paired wider nonsingular, potentially half equal).
  Preserve SX=SY domain failure; do not silently compute just the forward ratio.
- Phase designs: 3 phases `[0,2*pi/3,4*pi/3]`, `[0,0,0]` intentionally singular,
  `[0,2^-8,2^-7]` near conditioned. Design columns `1/3,2*cos(phi)/3,2*sin(phi)/3`.
  Quantize design operands only, then use exact rational inversion of binary64
  values as observer. This does not authorize half source phase generation/solve.

Bounded H3 CPU case is attached to K01, not an eleventh workload: 16 half values
`arange(16)-7`, NumPy and SciPy rfft/irfft round trip, complex32 dtype diagnostic,
unsupported `norm` diagnostic. No product backend argument exists and none is
invented. Internal multiplier/accumulator/workspace precision remains unknown
unless documented; promoted output alone is no native-half proof.

## Strategy/site boundaries

Every W row has a wider full workflow baseline and six comparison modes:
H1, H1_PROMOTED (dtype isolation), H2_CORRECTED, H2_PREPARED, H2_FILTERED,
H2_EMBEDDED. `WIDER` is a separately repeated diagnostic baseline. `QUALIFY`
runs once before comparisons, including full/summary compatibility and oracles.
Three fresh processes per successful W row/mode, no automatic batch/retry.
Kernel rows run once numerically; no kernel speed claim from sub-resolution work.

All complex packing allocates `<f2` shape `(...,2)`, real then imaginary; explicit
little-endian IEEE binary16, 4 bytes/complex value. Unpack allocates complex128
and assigns promoted real/imag components. Real packing uses `<f2`, unpack float64.
Original, packed, promoted and caller/result objects are deliberately retained.
No view alias saving, hidden scaling, native complex32 dtype or native-half
computation is assumed. Signed component zeros are observed separately.

| H2 site | Continuation / permitted claim |
| --- | --- |
| Corrected frames | Independent source-identified `alpha*(raw-background)` camera and phase/FFT formula replay, then public band record + estimator/reconstructor; wider-compute emulation, not public end-to-end precision mode |
| Prepared quadratures | Replace only public AcquisitionBands quadratures with packed/unpacked complex128; keep record metadata/noise/phase/fits/reductions wider; public estimator/reconstructor revalidate |
| Filtered quadratures | Capture public KnownReconstruction filtered result, pack/unpack, isolate assembly replay with fixed wider parameters/filtering |
| Embedded Fourier coefficients | Independently form source-defined signed embedding from filtered public record, pack/unpack each padded buffer before wider inverse/phase/signed accumulation; isolated formula replay |

Corrected replay supports exactly these no-drift/no-edge/no-equalization fixtures,
including source x-Nyquist raw-phase identity and axial FFT. It is not a general
replacement preparation implementation. Assembly replay preserves positive native
Nyquist placement, conjugate negative-x reflection, unnormalized inverse,
centered positive carrier ramps and signed accumulation. Full/summary record
compatibility is checked on unmodified wider public workflow for each W row;
H1 summary acceptance beyond the selected W01 full-path witness is unmeasured.
No half-phase/half-fit/half-final-accumulation strategy is activated.

## Independent observers and metrics

Separate analytic generator error, wider mapping deviation and physical usefulness.
For selected prepared coefficients `(0,0,0)`, `(0,1,1)`,
`(Z-1,Y-1,X/2)`, slots 0/1/2, each direction at t0, evaluate direct
negative-exponential finite sums with `math.fsum` real/imag compensation, including
source Nyquist raw-phase bypass. Record absolute term sums and signed coordinates.
This is independent of FFT code, but reuses declared binary64 separator values;
phase inverse is checked separately. For each embedded buffer compare positive
inverse finite sums at output `(0,0,0)` and `(0,1,2)` with actual wider inverse.
At origin the independent expectation is simply the sum of coefficients.

Build scaled phase design with scalar `math.cos/sin`; exactly invert its finite
binary64 values using Fraction Gauss-Jordan arithmetic, compare source left
inverse, and record finite-sum residual/condition without a new admission cutoff.
Uniform and supplied rows both resolve identity against the scaled forward
design. For supplied source noise, squared row sums/P define the observer;
v2 independently computes these from the exact finite-design inverse with scalar
compensated sums, and records source-noise deviation. Uniform noise is one by
contract. Source row energy is recorded separately, avoiding confusion between
legacy uniform declarations and recomputed trigonometric sums.
The existing binary64 achieved-residual criterion remains unchanged.
K03 energies use exact Fraction dyadic arithmetic; cross sums have finite closed
forms. K04 expectations follow the frozen finite formulas above. Formula replay
agreement is corroboration, not independently certified physical recovery.

Array errors: max absolute in declared units, RMS=`sqrt(sum|delta|^2/N)`,
relative L2=`sqrt(sum|delta|^2/sum|reference|^2)`. Both zero gives 0; nonzero error
against zero reference is undefined (`null` with rule). Nonfinite pairs retain
counts/ranges and do not acquire a fictitious finite error. Report minima,
negative counts, zero signs, nonzero-to-zero, nonzero sign changes and dtype,
shape, stride/alignment/writeability/ownership. The `binary16_subnormal_range` observer
counts nonzero components with magnitude below `2^-14` (the binary16 threshold),
even on promoted arrays; it is not the host dtype's subnormal classification.
Representability anchors: max finite 65504, normal `2^-14`, subnormal `2^-24`,
unit roundoff `2^-11`; actual rounding/flush/signed-zero behavior awaits K01.
All warnings, including intended overflow, are retained without clipping/repair.

Parameter errors: carrier components cycles/um and `delta_k*(X*dxy,Y*dxy)` bins;
complex/amplitude modulation errors; wrapped phase `arg(candidate*conj(reference))`
in radians, undefined if either zero. Preserve raw and final factors, frame
sums/gains/noise/separators and full traces. Exact discrete projection compares
branch, ordered event kinds, coarse first maximum, alias flags, fit statuses,
strict improvements, floor/reuse/phase replacement and finite/failure states.
Continuous objective/energy/cross/phase details remain in full raw trace.
Missing metrics remain unknown. No acceptance tolerance is selected here.

## Run authorization, environment and resource protocol

Original-source checks remain historical. The later preparation-checks packet
permits only AST/compile and existing Ruff on this owned harness, not its import
or execution. Resource launch is now quarantined after the known #116 Q1 failure;
no numerical/control/lifecycle run or independent capability probe is released.
Root prepares the destination and grants any later runs
only after pinning candidate/source/harness/manifest and scheduling resources.
The harness's local JSON grant is an audit receipt, not permission isolation.
Root can write one receipt containing explicit run triples, then extend it after
baseline qualification; it does not require another human approval ceremony.
Example receipt fields (placeholders are not valid evidence):

```json
{
  "authorization": "HP114_NUMERICAL_WINDOW",
  "environment": "simrecon-campaign-ubuntu",
  "baseline": "b344e41a8b52de76d7cbbf8450319893904c3b8f",
  "candidate": {
    "commit": "ROOT-PINNED-ACTUAL-HEAD",
    "tree": "ROOT-PINNED-ACTUAL-TREE",
    "tracked_status": "ROOT-RECORDED",
    "tracked_diff_sha256": "ROOT-PINNED-GIT-DIFF-BINARY-HEAD",
    "integration_base": "ROOT-PINNED-ACTUAL-BASE",
    "parent": "ROOT-PINNED-ACTUAL-PARENT"
  },
  "harness_sha256": "ROOT-PINNED",
  "manifest_sha256": "ROOT-PINNED",
  "runs": [["W01", "QUALIFY", 1]],
  "qualification_sha256": {}
}
```

A qualification run records `branch-qualified-oracle-review-required`, not scientific
acceptance. Root examines independent residuals and intended branches, records
any fixture failure, and names the qualification JSON hash in its comparison grant.
A failed intended wider fixture must be retained and routed to the author; no
comparison, tuning or favorable substitution. This freezes cases, not conclusions.
Changed formula/constants need diagnosed correction and new frozen identities.
The grant must include actual candidate commit/tree/tracked status, integration
base and parent, with root's applicability reconciliation after #113 integration.
The raw run retains this complete grant; BASE alone is not actual Git/version
identity. Reconcile EXPECTED and this manifest before execution if material
integration inputs change. The harness does not independently verify root's Git
attestation, and source hashes alone are not Git-derived version provenance.

After grant run via pinned container, with every listed thread variable =1 before
interpreter startup; SciPy context also sets workers=1:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-114 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  -e BLIS_NUM_THREADS=1 -e VECLIB_MAXIMUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 \
  simrecon-campaign-ubuntu .venv/bin/python \
  docs/reports/half-precision-study/study.py \
  --grant /workspace/work/campaign/evidence/114/study/ROOT-GRANT.json \
  --row W01 --strategy QUALIFY --repetition 1 --run-id W01-qualify-attempt1
```

This is a future command, not an executed command. Root supplies actual filenames.
For comparisons add `--qualification .../W01-qualify-attempt1/run.json`, select
one mode and repetition. Never overwrite a run ID. Raw JSON contains exact grant,
source hashes, environment, all warnings/failures, stage timings, records and array
index. NPY arrays preserve dtype/shape/signed/nonfinite values; file SHA256 and
byte count accompany each. JSON nonfinite scalars have explicit tagged encoding.
No raw output exists or is claimed during preparation.

Before fixture allocation record `/proc/meminfo`, memory pressure, self cgroup,
cgroup memory/swap current/max/events and conservative ledger. Ledger names
retained analytic/raw/half/promoted/hash copies; corrected/lateral work;
bands/filtered copies; full overlap snapshots for baseline/candidate/summary;
retained embedded source/packed/promoted; inverse/phase/signed outputs; transfer
callers; finite-sum/statistics buffers. Each coefficient is explicit in
`resource_plan`; shape arithmetic cannot activate larger domains. Compare modeled
simultaneous payload with actual MemAvailable and finite cgroup headroom; stop if
it cannot fit. The ledger is conservative array accounting, not an upper bound on
native/Python/workspace overhead. Search trace length, backend workspaces,
allocator metadata, callers outside the process, background load, parent cgroup
limits and OS reserves remain uncertainties requiring live review. The automated
fit check alone is no safety proof. Unknown workspace bars any large-case claim;
these fixed small rows are the entire experiment. There is no fixed reserve
percentage, invented process ceiling or root-required numeric reserve.

Record pre-call high-water and native peak before/after array export. Linux
`ru_maxrss` is KiB; multiply by 1024 for bytes. Whole-process peak includes
baseline retained beside candidate and conversions, so it is deliberately not
an isolated optimized pipeline peak. Baseline subtraction is no allocation peak.
Reachable backing payload is deduplicated by ndarray base allocation; external
non-ndarray extents/metadata are explicitly unknown. Timing uses monotonic_ns:
startup/import/setup in whole-run time, public call-only/stage/conversion times
separate, candidate plus conversion inclusive time separate. Hash/export time
is excluded from call-only and included in whole/export time. Replay timing
includes finite-sum observers; do not use it as a product performance prediction.
W repetitions yield raw values, median/range; aggregation/report review is pending.
Current comparison runs retain a full baseline before a candidate, while WIDER
retains only its baseline. Their RSS and warmed candidate times are systematically
unmatched. They measure diagnostic comparison-harness lifecycle, not actual
whole-pipeline storage benefit or speed ratio. **Actual benefit is UNMEASURED.**
The distinct v2 standalone method below removes reference/result coexistence.
It is now source-prepared, but neither statically accepted nor runtime-qualified.
It supplies no completed resource evidence or memory/speed recommendation.

16 GiB=17,179,869,184 bytes is an objective, not a measured limit or guarantee.
K02 large metadata alpha is not a crop/full-volume measurement. No full-volume
allocation, OOM test, source-limit expansion, GPU install or adapter is authorized.
Optional cuFFT Xt assessment remains documentary and pending: exact vendor
version/URL/access date, architecture, transform layout/size/stride and half
restrictions, workspace/GPU memory, driver/toolkit, license/redistribution and
portability are required before any conditional feasibility recommendation.
GPU timing/memory and actual native-half execution are unmeasured.

## Standalone matched resource method v2 — unexecuted

**Inactive launch draft.** `resource_parent` and internal `resource_child` both
call an unconditional refusal before any raw writes, authorization work or spawn.
Even a valid-looking grant cannot enable these routes. Root reports #116 Q1 in
the same Ubuntu CPython 3.13.12 raised `NotImplementedError: posix_spawn: setsid
unavailable on this platform` before any child PID. This is external environment/
tooling capability context, not HP114 scientific/numerical data. Root cites Q1
receipt `f1aa18a0…70a`; only that abbreviated identity was supplied here, and this
role did not rerun or independently inspect it. The exact pre-check four artifacts
and continuation scratch are preserved at
`/workspace/work/campaign/evidence/114/source-method-v2-before-checks/`.
The specification below describes the retained unexecuted method, not a launch
readiness claim. No new launcher, Popen reaping, interpreter, install or fallback.

The default `--route diagnostic` preserves baseline/candidate comparison and raw
scientific arrays. Its warmed timings and coexistent peaks remain diagnostic.
`--route resource` is a stdlib-only parent which spawns exactly one fresh copy of
this file with internal `--route resource-child`. The child imports the pinned
numerical stack only after the exact root grant is checked. It generates one
caller, runs one declared operation, retains one result and caller through exit,
and never invokes or loads a reference workflow, qualification record, analytic
truth volume or alternative candidate. Parent qualification is a root-reviewed
SHA256 attestation; reference comparison/aggregation runs in a separate diagnostic
process against saved output identities. A resource child does not load those
reference arrays or JSON. No generic profiling/parser framework or product hook
is introduced. All routes remain unexecuted under the current hold.

| Resource strategy | Caller at declared start | Exact operation and retained output | Resource scope |
| --- | --- | --- | --- |
| WIDER | One float32 raw array | `reconstruct_workflow`, full result | Full public workflow, including actual setup/observation/serialization high-water |
| H1 | One float16 raw array | Same workflow/settings/full result | Same retention; no needless full promoted duplicate held by harness |
| H1_PROMOTED | One float64 array containing exactly the half values | Same workflow/settings/full result | Isolates input dtype route with a single declared caller |
| PREPARED_WIDER | Complex128 quadratures plus required unchanged band metadata | Public `estimate_parameters`, per-time `reconstruct_known`, concatenated image and full parameter/known records | Prepared-band-to-image stage only; public acquisition setup also remains in cumulative/terminal high-water |
| PREPARED_HALF | Explicit `(...,2)` little-endian real/imag float16 caller plus same metadata | Unpack complex128, then same public stages/output policy | Same stage interval; packed caller plus required unpacked working bands coexist |

These are representations/sites within original W01–W06, not new workload rows
or a Cartesian extension. Three fresh successful repetitions retain the original
design. Corrected-frame, filtered and embedded replay have no standalone resource
claim; they stay diagnostic/isolated. PREPARED_* is rejected on the diagnostic
route rather than silently becoming a wider baseline. No native half arithmetic
is inferred from caller packing.

`resource_caller` evaluates the frozen field one x-row at a time and casts through
float32 admission, then half if selected. H1 retains half only; H1_PROMOTED stores
that row's half values directly into its sole float64 caller. There is no full
analytic or alternative-representation volume in the child. X-row coordinate,
specimen, angle, illumination and cast temporaries coexist during setup; their
cost remains in cumulative/terminal native high-water. Exact equivalence to the
original generator is an explicit pre-trial control for every W row, not assumed
from matching formulas. A mismatch is a generator-method defect to diagnose and
refreeze, never permission to tune scientific constants to outcomes.

PREPARED_* setup generates one float32 raw acquisition and calls public preparation
once. It does not estimate/reconstruct a baseline. Raw setup is released. Metadata
storage temporarily carries `quadratures=None` as an internal storage holder;
that holder is never passed to a public numerical entry. The wider caller retains
the prepared quadratures; the half caller retains only packed components after
source quadratures are released. Metadata/noise/phases remain wider. Unpacking
constructs a valid public band record before downstream validation. Initial
carriers derive directly from the frozen magnitude/direction declaration, with no
baseline result supplying seeds. Public preparation and source+packed coexistence
during setup can dominate native peak; no peak reset/subtraction hides this.
Runtime acceptance of these public records and identical seeded branches is pending.

`standalone_plan` describes one caller/result lifecycle, including released setup
costs, public camera/band/filter work, retained overlap snapshots, inverse/phase/
signed outputs, transfer callers and observation buffers. These are conservative
array estimates, not a proof of native allocation/workspace maxima. Unknown
Python/allocator/backend workspace, external callers, actual cgroup ancestor
correspondence and OS/background reserve remain explicit. The small source guard
reads host MemAvailable and exposed `/sys/fs/cgroup` root limits/current, and checks
whether modeled payload already exhausts known headroom. That exposed root is not
proof of the process's complete effective ancestor chain. Root's current admission
must reconcile actual ancestor/host bounds and unknown reserves before any run.
No hidden ancestor is called absent/unlimited; no hard numeric memory reserve or
human tolerance is invented. Parent repeats this necessary, insufficient headroom
check while waiting. Live changes can refuse/stop an attempt; no allocation growth
or deliberate OOM follows. No 16 GiB or full-volume inference is authorized.

### Grant, provenance and observations

Each standalone grant names one `run_id` and exactly one `[row,strategy,repetition]`.
It includes the existing identities/template fields plus `route: "resource"`,
actual `candidate.tracked_diff_sha256`, and:

```json
{
  "run_id": "ROOT-UNIQUE-ATTEMPT",
  "route": "resource",
  "resource_admission": {
    "accepted": true,
    "rationale": "ROOT-CURRENT-HEADROOM-WORKSPACE-RESERVE-AND-SCHEDULING-REVIEW",
    "evidence_sha256": "ROOT-PINNED-ADMISSION-EVIDENCE"
  },
  "deadline_seconds": "ROOT-POSITIVE-FINITE-NUMBER",
  "term_grace_seconds": "ROOT-POSITIVE-FINITE-NUMBER",
  "kill_reap_seconds": "ROOT-POSITIVE-FINITE-NUMBER"
}
```

Placeholders are invalid runtime values. Lifecycle bounds are root's operational
parameters for one attempt, not newly selected human resource/scientific limits.
Normal workloads require the root-reviewed qualification SHA for that row;
the child never opens it. Resource parent captures actual Git HEAD/tree/first
parent/tracked status and SHA256 of raw `git diff --binary HEAD` before spawn and
after the wait/cleanup outcome, comparing to the grant. Integration-base identity
is root-attested; Git data and named material hashes are distinct. Reconcile all
scientific/import-bearing inputs after final #113; no unrecorded ignored/untracked
import input can be silently assumed covered by commit or the named hash set.
Named material/manifest/harness and grant hashes are checked before/after.
Untracked raw files are outside the tracked-diff fingerprint. The original grant
is copied in bounded blocks to each unique attempt before spawning, and that
captured copy is passed to the child. No attempt overwrite or automatic retry.

Future command: use the same pinned docker/interpreter/thread prefix above, add
`--route resource`, select one resource strategy and use its one-attempt grant.
`--qualification` is not passed to a child. Full WIDER/H1/H1_PROMOTED compare only
with the same full-result retention policy. PREPARED_* compare only with each
other, separately from full workflow resource results. The child exports bounded
common-output identities/statistics and branches; it retains the full result but
does not serialize/reload a full reference. Diagnostic runs retain full NPY arrays
for scientific comparisons. Root pins external final receipt hashes; no receipt
hashes itself or mutates an earlier attempt.

Child snapshots are exact named cumulative `RUSAGE_SELF.ru_maxrss` observations,
each with monotonic timestamp, native Linux KiB, multiplier 1024 and raw bytes:

1. `pre_call`: after setup/caller identity, before conversion-inclusive/call clocks.
2. `call_end`: immediately after the operation clock, before output observers.
3. `post_observation`: after output hashes/finite/range/retention and final material
   observations, before JSON serialization and teardown.

These are cumulative samples, never stage increments or complete-child peak.
Call-only time excludes input setup, caller hashes, unpacking, output observers and
serialization. Conversion-inclusive time includes PREPARED_HALF unpacking plus
the same downstream call; setup packing remains separately scoped setup cost.
Full workflow modes have identical clock boundaries and no separate promoted
caller copy. Whole-child time/high-water includes setup and observations.
Array payload, native RSS and Python/allocator metadata remain separate.

The quarantined stdlib parent draft uses `os.posix_spawn(..., setsid=True)` and one cached
`os.wait4(exact_pid, WNOHANG)` owner. There is no workload Popen/poll/wait or
`RUSAGE_CHILDREN` aggregate. Git subprocesses occur only as separate provenance
work; they are not workload waiters. Terminal rusage covers the direct child's
process maximum through exit, JSON and teardown; it excludes parent/observer
memory and is not concurrent process-tree aggregate memory or numerical-only
allocation. No numerical grandchildren/accelerator are commissioned. Parent
pre-spawn self high-water is disclosed; inherited/pre-exec contribution is not
isolated or subtracted. API availability and these Linux semantics are source
candidates requiring actual runtime qualification, never proven by this draft.

No process-RSS sampling is commissioned, so sampled maxima cannot replace native
terminal usage. The parent records nominal 50 ms wait sleeps, wait-poll count and
largest observed polling gap. Scheduling/observer work can extend that gap;
spawn-to-terminal-observed elapsed is not exact child death time. Native terminal
peak remains distinct from those observation times.

### Outcomes and identity-checked recovery

Every attempt directory preserves original grant, spawn-intent marker, available
owned-child marker, stdout/stderr, child JSON and terminal attempt JSON. Files are
created exclusively. Missing/unparseable grant is an admission refusal; oversized
grant remains at its original root evidence path and is not read without bound.
Spawn failures retain phase and marker facts. JSON input size is capped at 4 MiB
before parsing, with raw oversized output preserved. This is a finite protocol
parameter, not a scientific resource limit or general parser framework.

Terminal observation retains raw wait status, exit code/signal, native usage and
reap timestamp independently of child/parse status. Missing native usage is null,
never zero. Outcomes distinguish admission refusal, spawn failure, child nonzero
exit/operation or nonfinite conversion/result, signal, timeout, malformed/incomplete
record, missing/oversized record, observer/cancellation failure, changed identities
and complete observation **pending independent scientific qualification**.
Record validation binds exact PID/row/strategy/repetition, marker birth identity,
material/grant identity, required snapshot values/units/order, caller/output
shapes/dtypes, declared entry, branches and environment. Terminal high-water cannot
be below the child's final cumulative sample. A missing/null/structurally invalid
field cannot become success merely because process exit was zero. Validation
checks this method's known record, not authenticity against malicious code.

One-shot parent SIGINT is the supported cancellation path, entering bounded cleanup.
TERM grace then KILL/reap grace use the same wait owner and exact unreaped child
session; terminal collection is cached before another signal. Repeated interrupts,
parent SIGTERM/SIGKILL, exceptions during persistence, kernel-unreapable child or
external reap can still lose terminal evidence/ownership. Source code does not
claim an infallible cleanup handler. No successful observation follows such a gap.

Before spawn a durable intent records parent boot/PID/start/group, argv and grant
hash; immediately after returned PID another record captures child boot ID,
`/proc/PID/stat` start ticks, process group/session and capture timestamp. Spawn to
marker and abrupt-death/disk-durability gaps remain explicit; intent alone proves
no child PID. Observer disappearance is never proof of child exit. If terminal
usage is lost, or spawn returned no safely recorded identity, coordinator must
inspect retained intent/marker and actual process membership, confirm boot and
start identity before signaling any PID/group, recover/stop only the matching
owned work and verify termination before another attempt. A stale PID, absent
marker or different boot/start identity is not signal authority. Unknown ownership
requires coordinator process/resource investigation; no blind PID kill, new run
or fabricated recovered terminal peak. Reaping after the sole observer died cannot
retroactively supply its lost wait4 usage. Final JSON/marker write failures may
require this same external recovery; no engineered isolation is claimed.

## Finite method controls — frozen, not run

`--route controls --row K01 --strategy KERNEL --repetition 1` requires a separate
root `route: "controls", control_release: true` grant with exact materials. It
runs in its own diagnostic process, never inside a resource child. Its controls
are bounded examples attached to existing W/K meaning, not new matrix rows or
product-red tests. They record expected and observed values without introducing
scientific tolerances or declaring report acceptance:

The controls use the conservative original W05 diagnostic payload envelope for
admission rather than only a K01 vector ledger, because generation equivalence
retains the finite W truth/caller arrays in this separate process. This remains
array accounting with unknown overhead/workspace, requiring root's live admission.

- K01's original binary16 finite/zero/normal/subnormal/underflow/overflow values,
  original K03's 16 exact-dyadic product/cross/energy variants, plus explicit
  left-associated half additions of `[2048,1,-2048]`: exact/wider-quantized sum 1,
  round-to-nearest half first addition loses the unit, final 0. NumPy reduction
  policy is not silently equated with explicit half left association.
- Separate analytic R, admitted float32 R, half R and same half promoted R;
  all six W generators compare canonical identities of each standalone caller
  against those independently retained diagnostic representations. No favorable
  replacement if the arithmetic order changes a rounded input bit.
- Canonical C-order little-endian hash of `[+0,-0,1,-2]` equals a stdlib `struct`
  byte/hash expectation across contiguous, strided and big-endian storage;
  reshaping changes recorded shape while preserving ordered bytes. Empty `(0,2)`
  hashes the empty byte stream but preserves shape/dtype; scalar `-0` has its own
  zero-sign bytes/shape. Canonicalization does not normalize signed zeros or NaNs.
- Python binary64 scalar/complex components `+0,-0,1.25,+inf,-inf,nan` and
  `complex(-0,+inf)` roundtrip JSON via explicit IEEE component bit tags when
  needed. Tiny NPY roundtrips retain finite/nonfinite/complex values, shape, actual
  dtype/endian and canonical content identity; `allow_pickle=False`. These tiny
  serialization examples are not full-volume export-memory measurements.
- Error observer `[1,-2,0]` to `[1.5,-1,0]` has max absolute 1, RMS `sqrt(5/12)`
  and relative L2 0.5, with explicit empty and all-zero-reference controls.
- Incomplete started record and a purported complete record with null pre-call
  snapshot must never yield complete-observation status. Raw failure/incomplete
  records and exceptions are retained, not overwritten as successful retries.
- K01 bounded public NumPy/SciPy `rfft/irfft` explicitly use `norm="backward"`,
  SciPy workers=1; record actual input/output dtype, unsupported complex32/norm
  diagnostics, route/source/binary-module paths and hashes. Installed SciPy is
  `_duccfft`, not pocketfft. Internal multiplier/accumulator/workspace precision
  stays unknown without specific evidence; CPU promotion is not genuine half.
  GPU/vendor feasibility stays documentary/unexecuted and no adapter is installed.

Array hash/stat/finite/error observers use 65,536-byte **per numeric buffer**
parameters. Iteration is C-order, buffered where necessary, sliced before byte
conversion even when an external-loop view is larger than the iterator buffer.
Input iterator buffers, canonical conversions, `.tobytes`, masks, selected finite
values, delta/absolute/squared operations and source arrays can coexist. Each
declared numeric/byte buffer is bounded, but 64 KiB is not total scratch. Scalar
hash state, Python metadata, iterator/native workspace and small per-chunk scalar
accumulators also cost memory. File hashing uses separate 1 MiB blocks. All
observations remain outside call-only clocks and inside child terminal high-water.
Diagnostic serialization still exports full arrays; resource children serialize
scalar observations only. Bounds and equivalence require future runtime controls.

Resource-parent lifecycle controls use the fixed `method_control` names
`missing-record`, `malformed-record`, `oversized-record`, `child-error`, `self-term`,
`timeout`, `timeout-ignore-term`, with `control_release: true`. They run no numeric
imports/workflow, require root resource admission but no prior scientific
qualification, and remain explicitly labeled method controls. Expectations are
respectively missing record, parser refusal, size refusal, retained child failure,
signal status, timeout with TERM, and timeout with KILL/reap. Timeout controls also
have a finite child fallback sleep derived from granted lifecycle bounds, so an
observer disappearance does not create an intentional infinite sleeper. The source
has no automatic retry. Normal accepted observation must later be qualified on
an actual admitted W row; synthetic controls cannot supply it. Admission refusal,
spawn/observer failure, SIGINT cleanup, repeated/abrupt interruption, marker gaps,
lost ownership, changed identities and null/omitted snapshot/identity fields need
explicit runtime fault controls under a later grant, without modifying product
science or treating a missing measurement as zero.

Resource-parent lifecycle controls are also quarantined. The source refusal is
unconditional; `control_release` cannot bypass it. No control, refusal path or
launcher was exercised by AST/Ruff preparation checks.

## Narrow launch reconciliation boundary — blocked pending root evidence

Root must first supply the diagnosed working #116 route and accepted affected-scope
evidence, exact source/check/environment identities and applicability to HP114.
An unaccepted draft or AST/Ruff pass is insufficient. Only a separately scoped
author correction may then reconcile the launch layer; no replacement is authored
here. Fresh affected static review must assess launch/readiness/exec errors and
returned-PID semantics; the sole exact-PID wait4 owner without Popen/fallback
reaping; terminal-usage/status preservation; PID/boot/start/group/session identity;
signal-race ownership, marker gaps and bounded cleanup/recovery. No scientific
constant, oracle, caller/result lifetime or matrix change follows automatically.

Root's PID1-sleep/no-init observation is planning context, not HP114 measurement.
Do not assume reparenting supplies reliable reaping, observer disappearance proves
child exit, or lost terminal usage can be reconstructed. No abrupt-loss experiment,
deliberately unreaped orphan or new-helper probe is authorized. Root must establish
a safe ownership/recovery plan before any such qualification. Existing source
markers disclose gaps; they do not solve an absent-init/reaper environment.

## Fresh static method reviewer questions

Review only the unexecuted method and preserved original diagnostic scope. This
is neither scientific report acceptance nor D readiness. Root supplies exact
candidate/diff/artifact hashes and a fresh independent reviewer; reviewer repairs
are outside that role. Concrete challenges:

1. Does any standalone child retain a needless analytic/wider/reference caller or
   run more than its one declared workflow/stage operation? Are H1/H1_PROMOTED
   and PREPARED_* boundaries, seeds, output policies and setup high-water honest?
2. Is there exactly one workload wait owner, including signal races, exceptions,
   nonterminal notifications and cancellation? Can another waiter or cleanup path
   erase terminal usage, or can a stale PID/group be signaled after ownership loss?
3. Can zero exit, null/missing snapshot, malformed/oversized output, changed
   identities, nonfinite conversion/result or cleanup gap masquerade as complete
   observation? Is every raw terminal/parse/status fact retained independently?
4. Do before/call-end/post-observation and terminal native scopes remain distinct,
   including final hashing/JSON/teardown, pre-exec limits and observer exclusion?
   Is polling delay represented without an unjustified maximum-gap guarantee?
5. Do canonical hashes preserve dtype/shape/byte order and signed-zero/nonfinite
   content with bounded conversions across contiguous/strided/endian/empty/scalar
   examples? Are separate buffer coexistence, error-observer costs and serialization
   limits stated without claiming a total 64 KiB ceiling?
6. Are finite phase/noise, dyadic cancellation, range, wire/NPY and FFT controls
   independent enough to detect plausible observer defects? Which gap is source
   defect versus runtime qualification, without adding a scientific cutoff?
7. Are root admission/ancestor uncertainty, actual Git/base/integration input
   reconciliation, observer disappearance/marker gaps and recovery obligations
   sufficient to block reuse or another attempt when evidence is lost?

AST/compile, lint and format preparation checks now pass for the corrected owned
source, using only pinned Ubuntu `uv run --locked --no-sync`. Ruff check 1 found
46 findings; import correction fixed one, formatting resolved layout findings,
and three remaining long strings were wrapped without changing content. Exact
attempts/statuses remain in the report and scratch. No report/product source or
control was imported/executed. Launcher capability is blocked by the actual
root-reported failure; other API/control/serialization/buffer/thread/backend/
headroom qualification and all science remain unexecuted. Preserve all original
S1 failed checks/repairs, prior static findings and unavailable meters.

## Evidence index and remaining preparation limits

- Source-read identities: tables above; root owns exact candidate/role ledger.
- Historical original-source and current narrow v2 preparation outcomes:
  [study report](study.md). Current passes execute/import none of the owned source.
- Resource parent/child launch: unconditionally quarantined after root's actual
  #116 Q1 capability failure. No HP114 attempt or independent retry occurred.
- Numerical environment qualification: pending numerical grant; root preflight
  is separately identified, not reused as an investigator result.
- W01–W06 qualifications, all W comparisons/repetitions, K01–K04 and H3 CPU:
  pending; no raw run, timing/RSS/error number or successful branch is claimed.
- Harness syntax checks cannot establish runtime imports, public record validity,
  fixture fitness, numerical observer correctness or report completeness.
- Full input capture in diagnostic mode makes trace/disk and retained memory
  conservative; resource children instead retain one result and export scalar
  observations. Neither unexecuted method is evidence of storage savings.
- Independent scientific report review, any diagnosed corrections, final exact
  gate and post-gate D review remain coordinator steps.
