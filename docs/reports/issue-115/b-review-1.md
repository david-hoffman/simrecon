# Issue 115 blind B review 1

**Verdict: accept the prepared A test checkpoint for W01–W18.** No actionable
test defect or unresolved contract meaning was found in the affected scope.
Retain the initial 1099 passing / 19 intended byte-admission failing results as
applicable behavioral evidence after cosmetic preparation. This accepts tests
for C; it does not accept the failing product, establish a passing full gate,
qualify a historical executable, or establish large-array feasibility.

The coordinator supplied candidate commit
`9a423fd608ecf6cdb203283674522b8b88b9e080`, branch
`feat/115-wide-allocation-domain`, and public-main base
`b344e41a8b52de76d7cbbf8450319893904c3b8f`. I did not inspect Git, history,
product source or implementation-bearing state to establish those supplied
identities. All inspected final file hashes match the launch and manifest.

## Exact checkpoint and review boundary

| Prepared file | Accepted SHA256 |
| --- | --- |
| `tests/test_wide_allocation_domain.py` | `016c47bcbdff42b41c90b01a1c2f07af459c09574b0f127b1655e8c327d84360` |
| `tests/wide_allocation_fixture.py` | `09c7ac15b02226f986b17f12a244056654b1166b5accbd2c4407a5f7cb3e94c8` |
| `tests/test_c_known_boundary.py` | `1125ff758f2cade00fd007c6dbdb54b31eef4e93cf4f109a97292526e4efd6b9` |
| `tests/test_c_acquisition_boundary.py` | `590d03ac6370b73294af1783f8e55eed1ffd932a1e50d2b80c7b8a56053b56b0` |
| `tests/test_c_workflow_validation.py` | `0ae4005badef392502e310df1cd8bd8b7f47aa06cd9550d1a8b1194969e50052` |
| `tests/test_reconstruction_summary.py` | `aa9d4d23fd3a5efa421d682366bde8c97a971e823dad696f411d81dbd67a00c8` |

The complete 99-file freeze identity is
`docs/reports/issue-115/tests-checkpoint.sha256`, SHA256
`9fcd3732d4adf47624b13f8aaac1883e30d99ece4cbbaece9cc696d29ff25076`.
Its identities do not expand this blind review into an audit of unlisted files.
The affected semantic review covers the new tests/geometry fixture, corrected
inherited byte expectations, workflow/summary delegation, and the named
retained obligations and permitted fixture definitions used below. It does not
requalify every unrelated inherited numerical observer or all 99 files.

Named unchanged fixture identities were independently hashed and agree with
the manifest:

| Fixture | SHA256 |
| --- | --- |
| `tests/c_known_fixture.py` | `5e80aafb44b59ae9d45592181b72d62ce03dd7f49f146313294a16c73a2d89a6` |
| `tests/c_acquisition_fixture.py` | `a64a93dae93864d5b76a2fb54b794a876b76f76527e7018966a681870ee82bf9` |
| `tests/c_preparation_fixture.py` | `eeff7dd5ce4cbd7a32a346eabd0521afdfd930ba582b1e20ac441da4c4d8e80c` |
| `tests/c_workflow_support.py` | `10265f0a62703ee30f136e00559cbbc8fbda470cf01213c7487bb39ff7705902` |
| `tests/c_workflow_oracle.py` | `96c8a74df6bf0906ed878414516caefa6cde165afd768050608bb02308b66c49` |
| `tests/reconstruction_summary_fixture.py` | `271335a5065791a986de239cdf89e4d15eb0f2e5df80943d6cb084167516d20f` |

Verified scientific/routing inputs were the B launch packet
`4974405c8a9cee75c4192e046e5b04d73d2f1c9a06f9479df389f6adeaa8bdb5`,
public packet
`8d81e5ada12f199f047e84f6c8faa32616f8b199867ed391443f38bcd8f940d5`,
W01–W18 contract
`d42cf0838e73fcaba1aa78c025c96582d246ea6bfef4323ab742323dfd169acb`,
interfaces
`0939e8956573eb5b7832f2bf80ddee8866c8c6a5a9db6eb1d48e9acfd1cbd180`,
A report
`90440d8743220b609787a7c999e9d71beeeebb889d34781daccf19f7ee8a21c0`,
and preparation addendum
`acf18993dee44db786f3ec4456b39408f29e5bf09348d9d7779b8d63b16f7fcd`.
I used review-work in B mode and only public test-audit criteria, applicable
role/model guidance, permitted PROJECT context and public contracts. No linked
runtime/history/lesson/nonblind report was followed.

## Independent arithmetic and numerical audit

Let I=2147483647, U=4294967295 and M=9223372036854775807. The fixture uses
Python integer multiplication, `Fraction(lateral)` for output resolution and
`s*product(max(d,1))` for native storage. It neither obtains expected integers
from product validators nor creates arrays from large geometry.

* Native bounds: M is divisible by 7; `7*(M//7)=M`. `8*2**60=M+1` and
  `2**32*2**32=2**64` distinguish exact arithmetic from float rounding or
  fixed-width wrap. At width s=8/16, the fitting byte count is M-(s-1),
  followed by M+1. A per-time extent with count `2**58` fits at each width,
  whereas four times do not. Empty acquisition diagnostics retain the
  conservative stride calculation; CE04's positive-only validator receives
  positive shapes.
* Historical cutoffs: U and I are odd, so byte equality at widths 4/8 is
  impossible. Nearest attainable bytes are cap-(s-1) and cap+1. The scalar
  neighbor examples are arithmetic, not a claim that odd-byte arrays exist.
* For `(1,1,3,2,2,4)`, L=1 and axial A, output volume is 16A, complex
  bytes 128A and real bytes 64A. The A neighbors of `2**25` and `2**26`
  cross the respective U ceilings while all listed signed/native quantities
  fit. L=6000 gives output volume 576000000 and complex bytes 4608000000;
  L=8192 gives volume 1073741824 and complex bytes 8589934592. Both inherited
  known witnesses are therefore byte-only admission cases under this contract.
* For `(1,1,3,1,2,4)`, plane is `8L**2` and lookup bytes `32L**2`.
  L=8191/8192/8193 crosses I in bytes at 8192 while plane counts fit.
  L=32768 gives plane `2**33` and still rejects as an element count.
* With native X=Y=2 and Z around `2**27`, volume is 4Z, padded count 8Z,
  complex-native bytes 32Z. The native byte crossing is genuine and the
  phase/frame products also fit I. Generic `_extent` validates actual width
  16; this is not proof that every CE04 caller uses that validator.
* Even X=2 makes the signed-volume endpoint I unattainable: A=I//2 gives
  I-1, and the next A gives I+1. The test does not invent exact equality.
  For orders, Q=2O-1, Q<=P and QP<=I imply Q squared<=I. Q=46339 fits,
  Q=46341 does not; O<=23170 and order bytes<=185360. An isolated old order
  byte overflow is impossible within those retained constraints.
* The acquisition witness has `(Zo,Yo,Xo)=(2,16384,16384)`, volume `2**29`,
  complex bytes `2**32`, real bytes `2**31` and lookup bytes `2**30`.
  The workflow witness A=`2**25` has the same volume/complex/real bytes,
  lookup bytes 32 and alpha=`2**-29`. Its output padded count 805306368
  and half count 402653184 fit I. In contrast the retained workflow
  `source-byte-limit` shape has padded native count `2**31+8` and output
  volume `2**31`; removing that rejection would lose a real signed guard.
* The motivating target independently gives native volume 134217728,
  padded count 134348800, half volume 67174400, output plane 16777216,
  output volume 536870912, source byte expressions
  `(1073741824,4294967296,2147483648,24,67108864)`, image bytes 4294967296
  and raw bytes 16106127360. Illustrative aggregate complex arrays also fit
  M. This remains metadata classification, without a RAM/backend/stencil
  feasibility claim or a target numerical call.

For small scientific positives I checked the analytical fixture against CE07
9.1, rather than treating full/summary agreement as independent numerical truth.
Raw phases (6,3,3), alpha=1/16 and the finite transforms yield B0=12, E1=3,
O1=0. With a0=1+sqrt(2), mu=(a0-i)/4 and fitted a=mu/4,
`abs(a)**2=(2+sqrt(2))/128`; hence h=`2+(2+sqrt(2))/64` and the fixture's
image numerator `12+(3/8)*[1,a0,a0,1]` follows from centered side assembly.
The complex-table variant uses `a=3*(2-i)*mu/(20*sqrt(2))`, separate
`h0=2+2.5*abs(a)**2` and `h1=2+3*abs(a)**2`, exactly as the public contract
requires. It discriminates raw-factor, magnitude-only and common-denominator
substitutions. Fixed absolute image/factor tolerances `2**-38`/`2**-42`
remain the existing small bounded-reduction allowances; none was fitted to a
product result. Zero raw with equalization disabled independently yields zero
quadratures/image, with finite positive noise and a defined Wiener denominator.

## W01–W18 and preservation audit

Names abbreviated below are in `test_wide_allocation_domain.py` unless a file
is named. These are behavioral obligations; parameter replications are examples.

| ID | Independent disposition and proof boundary |
| --- | --- |
| W01 | Accept native inclusive/exact/wrap and actual-itemsize tests through both approved metadata validators. Native dimensions and bytes are separate; positive allocation requirements are not relaxed by supported empty diagnostics. |
| W02 | Accept five-expression fixture arithmetic, attainable historical crossings, native crossing, output/lookup crossings, order dominance and corrected known public witnesses. Integer-only native/order proof does not establish every real caller's absence of a stale guard; C/D must inspect that relationship. |
| W03 | Accept `output_extents` crossings and corrected acquisition/workflow/summary complements. The retained invalid signed plane and volume cases prevent treating byte widening as element widening. |
| W04 | Accept nearest attainable signed-volume endpoint and retained known scalar/record, acquisition invalid-declaration and workflow/summary mapped-domain tests. Bool, nonintegral and nonpositive declarations remain invalid. |
| W05 | Accept separately calculated source/padded/half/output/frame/phase/order inventory and retained source-product/frame-count tests. Several invalid examples violate multiple retained guards, so they are not isolated proof for every signed expression. No aggregate signed32 bound is invented. |
| W06 | Accept retained known derived-operation/cutoff/sampling cases, acquisition precise/fixed10/prepass cases, signed plane rejection and actual stencil controls. No invented FFT maximum or widened lookup index follows. |
| W07 | Accept widths 1/8/16, multi-axis native overflow, aggregate crossing and supported empty stride positives/errors. Illustrative target-array inventory is necessary arithmetic, not an exhaustive observer of all owned traces/identities. |
| W08 | Accept retained known L65536/L16777217/A=`2**31` rejections, fractional workflow/summary rejection, and inherited permitted integral fractional enlargement. Float32 zoom exactness and integral enlarged extents remain separate from bytes. |
| W09 | Accept invalid signed geometry before observed raw copies/scans/FFT/allocation in both workflow entries, complemented by direct source-shape rejections and ordinary small successful calls. Observers cover named NumPy/FFT operations and do not prove every alternative import or external backend path; source ordering remains for D. |
| W10 | Accept ordinary-versus-wide invalid Wiener, invalid acquisition pitch and workflow/summary invalid mapped-pitch categories. Each wide declaration is otherwise representation-valid; no simultaneous-invalid precedence is imposed. |
| W11 | Accept genuine tiny PreparedBands and AcquisitionBands preparations, matching alpha and route-specific record shapes, then common known-stage invalid-Wiener rejection. Forged-field tests remain errors; no inconsistent record is used as the new admission positive. |
| W12 | Accept paired workflow/summary config/representation tests, linked corrected witness and retained independent closed forms plus exact projection checks. Relative full/summary comparison proves projection agreement, with separate analytical truth for numerical accuracy. |
| W13 | Accept exact target integer table and honest unmeasured-resource limit. No target array is created. |
| W14 | Accept new zero-input small positives, inherited CE07 unit/complex closed forms, signed negative outputs, zero/signed carriers/modulation and permitted dtype/scalar endpoints. No precision mode, fitted gain, minimum signal or changed science is asserted. |
| W15 | Accept unchanged signature/export, full-debug/projection, writable direct-stage, read-only/strided input and post-return isolation tests. No public resource/dtype argument or result field is added by these tests. |
| W16 | Accept safe/unsafe actual stencil pairs, including data/modulation/transfer/damping zero weights, opposite signed overlaps, safe cross-axis flat vertices and short-circuited queries. Zero numerical weights do not waive actual unsafe vertices; unused outside-support queries are not over-restricted. |
| W17 | Accept controlled small allocation/backend tests through real public routes plus retained summary external-failure tests. Intercepted paths require error category, cause identity and no result; legitimate alternate imports/backends may instead take a checked positive fallback. A pass therefore does not establish interception for every parameter row. C/D must retain actual operation-failure handling and available context. |
| W18 | Accept exact injected interruption identity and unchanged input snapshots, retained summary interruption, real late-time failure and discarded-correlation finite failures. Whole-call errors remain required; a success/partial-result substitution would fail those assertions. |

The inherited ledger has no unkept approved obligation in the affected changes:

* A115-K1 removes only L6000/L8192 obsolete known-stage rejection rows. New
  byte arithmetic/public invalid-Wiener keepers replace them; L65536 signed
  overflow, L16777217 float32 nonexactness and A=`2**31` remain rejected.
* A115-A1 retains both acquisition output-count rejection rows: each exceeds
  I independently of bytes. A115-A2 replaces only the obsolete isolated complex
  byte rejection and its obsolete rejection-cause loop with integer admission
  and safe public invalid-pitch evidence. W09/W17 retain early/failure semantics.
* A115-W1/W2 change the workflow wide witness to admission/config rejection and
  separate output-plane count from lookup bytes. A115-S1 updates the exact
  summary parameter delegate together; monkeypatching inherited `entry` still
  selects summary when the corrected helper ultimately calls `assert_error`.
* A115-R1 retains the source-byte-named signed overflow through both entries;
  A115-R2 retains fractional extent, unsafe stencil and small positive controls.
  No shared schema, numerical tolerance, accepted-record rule or executable
  pre-existing fixture was changed by these corrections.

The new large integers reach only metadata validators. Public wide declarations
use tiny real backing and an independently invalid field; genuine preparation
creates native-sized bands, not enlarged images. Existing invalid huge views
retain independently binding signed guards. None of these tests requests a
successful huge numerical operation, deliberate OOM or timed-out allocation.

## Retained execution evidence and native diagnostics

I initially identified that A's old hashes plus its cosmetic-change assertion
were insufficient by themselves to decide retention. The coordinator then
explicitly permitted two additional source-free test-only evidence files:

* `behavior-retention-evidence.md`, SHA256
  `75ca73a3048a485c6ffc4001a1da5338900ea7b8ec337eb2b80717c52ae07701`;
* `behavior-to-prepared.diff`, SHA256
  `8f9f86c09ad3480a83dad6aff4637863d75bc0516e236376633ef39472dcbb39`.

I verified these hashes and inspected the complete supplied old-to-final delta.
Coordinator reconstruction matched all four independently recorded initial-run
SHA256 values before this diff was produced. The delta changes only the constant
binding/import/references/comments from I to SIGNED_MAX and whitespace in a
decorator/signature. The value remains `2**31-1`; test names, discovery,
parameter values/order, formulas, assertions, fixtures, observer logic, call
arguments, tolerances and expected outcomes do not change. Workflow and summary
have identical old/final hashes. This supplied exact delta, together with final
file inspection and identities, independently supports semantic retention; I did
not rely solely on the author's conclusion or open history.

Accordingly the reported initial source-free focused pytest remains applicable:
1118 collected, 1099 passed, 19 failed, 16 warnings, 128.26 seconds, exit 1.
The 19 rows are five output-byte admission neighbors, two lookup crossings,
the admitted signed-volume endpoint, target metadata classification, four
wide direct-route cases, one acquisition pitch complement, two inherited known
witnesses, acquisition complex witness, workflow witness and its summary
delegate. Their independently valid admission oracles agree with the contract;
the sanitized evidence reports obsolete output/lookup byte ceilings as the
failure. Classify these as intended baseline **product red**, not test defects.
No final-file behavioral rerun was performed or claimed. Initial passing small
controls and retained rejection cases remain valid evidence within their actual
scope; conditional fault rows still do not reveal whether interception occurred.

Four identical native lines were reported:

```text
 ** On entry to DLASCL parameter number  4 had an illegal value
```

This fixed routine/parameter/message text contains no implementation snippet or
locals. The addendum permits precisely this source-free channel; it does not
authorize arbitrary native renderers. A's conservative stop and later narrow
resumption are preserved. The line alone identifies neither a test nor whether
the originating calculation was an expected singular/nonfinite rejection; its
origin is not established by the supplied evidence. It supplies no numerical
oracle, no success proof, and no independently actionable product/test defect.
Retained singular/undefined-operation and discarded-finite-check tests require
errors; independent zero/CE07 positive assertions must still succeed. There is
no reported unexpected failure or changed oracle that challenges retention.
Thus these messages do not invalidate this test checkpoint or the reported
observable outcomes, but no claim of clean native internals or exact message
attribution follows. Warnings remain recorded rather than suppressed.

Final exact-six-file Ruff lint/format and canonical uv-run source-free Pyright
are reported exit 0. Initial lint/format defects, raw-interpreter unresolved
imports and later import-order lint failure remain in A's accounting: ten check
commands, five nonzero statuses, two cosmetic repair rounds, zero semantic
corrections. The first Pyright invocation is environment/tool invocation failure;
style failures were author preparation defects subsequently corrected. They do
not establish a changed behavioral oracle. I ran no import, probe, test, lint,
type check, installation, benchmark or measurement while #112 held resources.

## Risk and completion limits

The independent risk audit found no additional concrete missing test requiring
author correction. Exact/wide arithmetic, signed-index separation, native
aggregate/empty storage, early work, real-record route differences, categories,
permitted zero/signed/strided classes, stencils, external causes, interruption,
finite checks and original numerical/ownership behavior have the keepers and
limits above. Generic validators must remain real production-call validators;
blind tests cannot prove that relationship. C/D must inspect actual five-byte
guard changes, all owned aggregate extents and public ordering/error propagation.
The conditional failure fallback is explicitly limited proof, not a waiver of
the corresponding product contract.

Required exact-candidate Ubuntu full verification, native statement/branch
covered/total reports globally/per package/per owned file (including relevant
subprocesses and never-imported files), resource evidence and fresh D remain
later obligations. Percentages are advisory. This review changes no gate,
platform policy, runtime seam or test scope. It makes no new backend-size,
32-bit, memory-fit, precision or historical-executable claim.

This was one direct fresh B session and one completed full affected B review;
no delegation, repair, commit, external write or further launch occurred.
Requested route/model/effort was fresh `fork_turns="none"`, gpt-6.1-sol/high;
actual served attribution, tokens, money and complete elapsed time are unknown.
The supplied cumulative intake1/A1 plus continuation1/B1/C0/D0, earlier B/D0,
semantic A corrections0, cosmetic rounds2, diagnostic stop1 and source exposure0
are preserved. Actual human numeric limits are not set. Optional separate
memory/delegation/read-only controls were unavailable; shared filesystem/prompt
controls are not engineered isolation. No forbidden source/locals exposure was
observed in this session. I created only this report, created no scratch file,
and own no active process. Coordinator owns freezing and subsequent transitions.
