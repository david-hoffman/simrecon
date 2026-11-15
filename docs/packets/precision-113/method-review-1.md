# SP113 — fresh independent report-only scientific-method reviewer1

You are already this fresh independent reviewer; perform directly, no delegation.
This is an early frozen-method challenge for intake, NOT blind A/B, implementation,
D/product readiness or a passing candidate. A1 continues authoring independently.
No author history is inherited. Do not repair either method or author tests.

## Binding, scope and independent question

Worktree `/workspace/work/issue-113`, branch feat/113-single-known-reconstruction.
Frozen method source at current tracked HEAD
`df77054284c87098b5eddebf17863238126cef69`, tree
`ea170056430afada58d26deb0db51d144494871d`:

- `docs/packets/precision-113/tiny-default-fft-method.md`, SHA256
  3688bd74526f3435e3dce0e3dad832a8f7e3af132c7fd78f9ad210a70f3377ac.
- `docs/packets/precision-113/point-libm-method.md`, SHA256
  6b8cde309a853bd3bb3fd1ac7233282303e5b814a046f20eb0e3688d95102695.

Those exact whole public methods and their primary external dependency/source/
correspondence assumptions are the review target. The new opt-in profile uses
c64 filtering/FFT bulk, f64 scalar/coordinates/image accumulation and f32 result,
fixed positive unnormalized inverse axes0,1,2/norm forward/workers1/no overwrite;
old calls remain double. No universal FFT/libm guarantee, physical-accuracy
threshold, memory ceiling or16GiB promise is selected. A frozen justified
fixture-specific enclosure is required for each accuracy-qualified witness;
unresolved intended coverage stays blocking. Observed R/dtype alone cannot
supply a multiplier. The method documents themselves prove no runtime outcome.

Independently challenge:

1. Cardinal1/2/4 codelet/source applicability, per-component operation/depth and
   normalization/axis-order facts, gamma/Sbar propagation, absolute underflow
   term/node count, input uncertainty and range/overflow conditions; any hidden
   universal extension, wrong accumulator/precision assumption or source/binary
   correspondence gap.
2. Selected hypot moderate/FMA/non-FMA expressions and source branches; exact
   point/reference/R64/sqrt interval validity, dependencies/correlations,
   fused-operation containment and missing input/constant/denominator conditions.
3. Selected sin/cos/cexp points, table index/bit constants/source grouping,
   rounding-cell/bin/pole/domain margins, signs/signed zero and tiny-tail exact
   claims. Check both independent mathematical reference and finite-program
   enclosure, pi representation and consumed conversion separation. A generic
   approximate ULP comment is not a certificate.
4. Actual source/binary/RNE/gradual-underflow or normal-only assumptions,
   CPython/NumPy/GLIBC dispatch/source-version applicability, what static symbol
   imports prove, and precisely what later qualification is necessary. Do not
   infer runtime provenance or acceptance from source text/outputdtype.

Return concrete findings with primary mathematical/source evidence, affected
statement/conditions and severity; independently recalculate rather than merely
endorse a derivation. Distinguish defect, missing proof/material condition,
legitimate conditional claim and unreviewed scope. Do not invent a general
framework, new accuracy/algorithm/owner meaning or a universal-backend obligation.
No product/test acceptance is requested or available.

## Exact allowed inputs; excluded history/source

Whole files allowed:
- this actual packet;
- `AGENTS.md` and `.agents/skills/review-work/SKILL.md` (report-only scientific
  method assessment; no D acceptance or repair mode);
- the two exact frozen public method docs above.

Do not expand repository links. Do NOT read SIMrecon src/product implementation,
Git history/diffs, task/Current state/intake/method-investigation/role-ledger,
A reports/tests/fixtures, coverage, lessons,112 prototypes/raw reports or any
coordinator/sibling/advisor conclusion. Git identity/status and hashes of allowed
files are permitted, no source-history inspection. A has dirty owned files;
preserve them and do not inspect them. Whole PROJECT/mixed test-audit are not
needed/permitted: capability/model/gate facts are copied in this packet.

Primary external numeric-library sources MAY be read only at the pinned tags
below, using existing read-only tools. This is external numerical algorithm
analysis, never permission for SIMrecon product source or a broad source archive:

- scipy/scipy v1.18.1: scipy/fft/_backend.py,_basic_backend.py,
  _duccfft/basic.py,helper.py,pyduccfft.cxx;
  subprojects/duccfft/ducc0/fft/fft.h,fft1d_impl.h,fftnd_impl.h;
  subprojects/duccfft/ducc0/math/cmplx.h and directly needed numeric/SIMD type
  definitions under that vendored ducc0 directory.
- bminor/glibc glibc-2.39: sysdeps/ieee754/dbl-64/e_hypot.c,s_sin.c,
  s_sincos.c,usncs.h,sincostab.c; math/w_hypot_compat.c,s_cexp_template.c;
  directly needed x86_64 sin/cos/hypot dispatch/FMA wrappers and macro definitions
  for these functions only. Narrow directory/file discovery for those dependencies
  is allowed, no issues/reviews/whole archives.
- python/cpython v3.13.12: Objects/complexobject.c and directly relevant
  mathmodule/hypot/float primitive definitions/documentation.
- numpy/numpy v2.5.3: numpy/_core/src/umath/funcs.inc.src,
  numpy/_core/src/npymath/npy_math_complex.c.src and directly needed configured
  complex-exp/primitive binding definitions only.

Installed dependency metadata/source correspondence may be inspected read-only
at the matching task .venv's SciPy fft/version and NumPy numeric binding files,
package metadata and compiled-module/interpreter ELF symbols/hashes. No import
or execution of NumPy/SciPy/libm/candidate functions to obtain actual outputs,
no tool/source mutation/install. Static import symbols alone are no active-route
proof; report unavailable actual correspondence honestly. Do not read credentials
or unrelated environment/cache/history. Primary references in frozen methods
are factual starting points, not trusted reviewer conclusions.

## Tools, permitted exact arithmetic and report ownership

Ordinary read-only static assessment is preferred. Root explicitly permits tiny
exact STANDARD-LIBRARY Fraction/interval arithmetic if needed and recorded,
in the pinned Ubuntu environment below. This is not a dependency/candidate trial.
Use math.isqrt/struct/decimal only for exact/reference arithmetic with rigorous
remainders; no sampling libm sin/cos/hypot or FFT, no NumPy/SciPy imports, array
allocations, benchmark, installs/sync, resource experiment or product test.
No arbitrary big search/retry loop. Preserve every failed command and limitation.

Selected execution prefix for any permitted tiny exact process:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-113 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  -e BLIS_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 \
  simrecon-campaign-ubuntu \
  uv run --locked --no-sync python -B scripts/source_free_check.py --timeout 300 \
  python -B -c '<fixed tiny exact stdlib proof arithmetic>'
```

The existing renderer/support are execution-only, no source read needed. Record
exact payload/command/hash/status and arithmetic claims actually checked in the
report. No new helper/environment/gate. Do not run code merely as connectivity
probe. If root/coordinator announces an exclusive116 window, suspend arithmetic
and acknowledge before further execution; missing window/conditions are not
permission. Timeout is incomplete, never a pass. All other execution is forbidden.

Write ONLY `/workspace/work/campaign/evidence/113/method-review-1.md`, the
explicitly authorized outside-candidate detailed report. No tracked edits,
repair, commit/push or other file. Include frozen target hashes, actual read
inventory/primary identities, assumptions/independent derivations/findings,
commands/status/unknowns, no-product-acceptance scope and own process/scratch
facts. Final collaboration message is separate; summarize findings and exact
report identity. Reviewer conclusions remain coordinator-only; do not message A
or future B, and do not delegate.

## Freshness, gates and cumulative accounting

Root authorizes this one parallel fresh report-only method challenge. It does
not replace fresh B's complete tests/oracles/material review or C/full exact
Ubuntu/D, and grants no actual dependency/product acceptance/performance/116 data.
A1 continues valid static work. Coordinator may correct normative proof facts
only from independently checked primary math/source and send sanitized deltas;
raw reviewer conclusions/verdict are not A/B inputs. No acceptance shortcut.

Launch fork_turns=none, requested gpt-6.1-sol/high per conservative PROJECT role
guidance. Served model/effort/meters unknown unless exposed. Supported fresh tool
route after accepted CLOUD107 policy; optional separate memory/read-only/delegation
controls unavailable, shared filesystem/permissions and prompt allowlists are
not engineered isolation. No native CLI/auth probe is required. Actual packet
hash/session/launch details supplied/recorded by coordinator after packet freeze.
Human numeric caps not set; bounded timeout is not a new quota. Retain all
review/read/failed arithmetic/diagnosis costs; tokens/cached/output/verified
money/total durations unknown, never zero. One method review, not an A/B round,
no context/charge reset and no policy/permission/workflow/gate change.
