# HP114 frozen study manifest — preparation v1

This is a source-prepared experimental protocol, not numerical evidence. All
scientific cases below are frozen before candidate trials. The standalone
[study.py](study.py) is an experiment, outside runtime/test roots. The task is the
sole execution state; this manifest records reproducibility inputs, not competing
Current state. Artifact SHA256 values and final identities belong in the root's
external receipt, avoiding self-referential hashes in tracked bytes.

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
design. For supplied source noise, squared row sums/P define the planned observer;
independent noise-observer implementation remains deferred to the execution-phase
source review. Raw noise values and wider/candidate deviations are already retained.
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

The preparation grant permits only compiling source bytes and Ruff on this owned
harness, in pinned Ubuntu. Scientific imports/trials, tests, benchmarks and product
execution still await root. Root prepares external destination and grants runs
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
A matched standalone resource protocol, with only one workload in each fresh
process and comparison against saved qualification outside that process, remains
deferred. It must be frozen/reviewed before any memory/speed recommendation.
This is a known incomplete preparation detail, not completed contract evidence.

16 GiB=17,179,869,184 bytes is an objective, not a measured limit or guarantee.
K02 large metadata alpha is not a crop/full-volume measurement. No full-volume
allocation, OOM test, source-limit expansion, GPU install or adapter is authorized.
Optional cuFFT Xt assessment remains documentary and pending: exact vendor
version/URL/access date, architecture, transform layout/size/stride and half
restrictions, workspace/GPU memory, driver/toolkit, license/redistribution and
portability are required before any conditional feasibility recommendation.
GPU timing/memory and actual native-half execution are unmeasured.

## Evidence index and remaining preparation limits

- Source-read identities: tables above; root owns exact candidate/role ledger.
- Preparation syntax/Ruff commands and outcomes: [study report](study.md).
- Numerical environment qualification: pending numerical grant; root preflight
  is separately identified, not reused as an investigator result.
- W01–W06 qualifications, all W comparisons/repetitions, K01–K04 and H3 CPU:
  pending; no raw run, timing/RSS/error number or successful branch is claimed.
- Harness syntax checks cannot establish runtime imports, public record validity,
  fixture fitness, numerical observer correctness or report completeness.
- Full input capture makes trace/disk and retained memory conservative; artifact
  export duplication is explicit and cannot be sold as storage savings.
- Independent scientific report review, any diagnosed corrections, final exact
  gate and post-gate D review remain coordinator steps.
