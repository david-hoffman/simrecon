# Wide allocation-byte domain v1 (issue 115)

**Version 1.0.** Authorized extension of representation validity on the supported
64-bit Ubuntu 24.04 platform. This contract changes allocation-byte arithmetic;
it preserves the original-domain scientific mapping. It does not qualify a
historical C executable, a 32-bit platform, available RAM or an FFT of any
particular large size.

## Authority and precedence

The owner commissioned issue [115](https://github.com/david-hoffman/simrecon/issues/115),
“Replace legacy workspace-byte limits safely.” This is one coherent CE04/CE06/
CE07/summary representation change, independent of precision and storage work.
The approved [PROJECT](../PROJECT.md) architecture and coverage policy apply.

This contract supersedes only the allocation-byte limits and corresponding target
classification in CE04's representation section, CE06 section 10, CE07 section 10
and RM84 sections 3/5. Their signed element/index, scalar, scientific, ownership,
stencil and failure requirements remain in force. Historical evidence keeps its
original domain; it is not retroactively requalified. Corresponding usage guides
must explain the extension without implying RAM admission.

## Checked arithmetic and bound inventory

Let `I = 2**31 - 1` and `M = np.iinfo(np.intp).max`, which is `2**63 - 1` on
the supported platform. All products and comparisons are exact integer
arithmetic before narrowing or allocating. In particular, do not multiply in
fixed-width NumPy integer arithmetic or route byte counts through floating point.
For a required positive allocation byte count `B`, representation requires
`0 < B <= M`. No unsigned32 or signed32 **byte-only** admission limit remains
for the expressions below. Actual target arrays must independently satisfy the
native extent rule with their actual element sizes, not the historical sizes.

Write native dimensions as `X,Y,Z`, directions `D`, orders including zero `O`,
phases `P`, quadratures `Q=2*O-1`, times `T`; output dimensions are
`Xo=L*X`, `Yo=L*Y`, `Zo=A*Z`, all resolved exactly under the inherited zoom rules.

| Byte-only expression | Affected boundary | Old cap replaced | Safety argument for the replacement |
| --- | --- | --- | --- |
| `8*X*Y*Z` complex native workspace | CE04 | unsigned32 | Byte extent is not a signed element index. Exact wide multiplication plus actual complex128 workspace extent retains addressability; signed native volume/offset checks remain. |
| `8*Xo*Yo*Zo` complex output workspace | CE04, CE06, CE07, summary | unsigned32 | Same separation for output count versus bytes; actual complex128 workspace and aggregate extents remain checked. |
| `4*Xo*Yo*Zo` real output | CE04, CE06, CE07, summary | unsigned32 | Byte count may exceed the former cast while signed output count fits. Actual binary64 image extent and aggregate time axes still bind. |
| `8*O` order allocation | CE04 | unsigned32 | This is solely a storage-size expression. Order counts, direction/order products and actual coefficient/table indices retain signed constraints; actual order storage must fit native addressing. It receives the same wide rule even where another retained count already makes the old cap redundant. |
| `4*Xo*Yo` lookup allocation | CE04, CE06, CE07, summary | signed32 bytes | Multiplication by item size is not an element/index constraint. Retain signed output plane and actual lookup index arithmetic; require wide byte extent and actual lookup/native array extents. Do not keep a signed byte cast solely because the historical allocation narrowed it. |

These are five distinct byte expressions and eight affected direct-stage guard
obligations (five CE04, three CE06 shared by workflow/summary). No other
byte-only source cast ceiling is implicitly preserved or expanded. Native size_t
addressability remains necessary and is covered conservatively by signed native
intp byte representation for owned arrays.

For any owned/copied/used array or diagnostic with shape `d` and item size `s`,
retain `0 <= d_i <= M` and `s*product(max(d_i,1)) <= M`, including empty shapes
where supported. This checks contiguous stride and byte representation as well
as dimensions. Bound all aggregate time/direction/order/trace/identity arrays;
per-order source allocation does not authorize ignoring aggregate native storage.
Respect each stage's existing nonempty-shape requirements. Do not introduce a
new successful empty scientific input.

## Bounds that remain and their purposes

* Signed32 dimensions, counts, resolved output dimensions and loop variables
  remain. They represent the selected finite algorithm, not its allocation size.
* Signed32 products remain where they count elements or form source indices:
  `X*Y*Z`, `(X+2)*Y*Z`, `(X//2+1)*Y*Z` as applicable to a stage, output plane
  and volume, `D*Z*P`, `T*D*Z*P`, `D*P*(N+1)`, `Q*P`, `D*O`, exposure/metadata
  counts, selected fit/matrix dimensions and actual flattened offsets. Do not
  add a signed32 aggregate bound when source arrays are separately indexed.
* Signed lifts, wrap/reflection sums, cutoff integers, squared-radius/index
  arithmetic, finite ceil/floor/pow conversions and actual lookup/stencil
  addresses remain checked before use. Removing the lookup **byte** ceiling
  does not widen lookup **indices**.
* Native array shape, contiguous stride, byte extent, aggregate storage and
  backend addressability constraints remain. Do not invent an unverified backend
  maximum; preserve actual backend failures and any independently established
  required backend index constraint. Representation-valid is not a promise that
  a backend will execute or allocate successfully.
* Exact float32 lateral-zoom declarations and integral enlarged extents, finite
  physical values, standard raw types/exact sample representation, accepted
  record identity and all original scientific-domain restrictions remain.

## Declaration, errors and compatibility

Reject known invalid/unaddressable geometry from integer metadata before
array-sized copying, hashing, finite scans, broadcasting, numerical preparation,
FFT/backend calls or target allocation. Public APIs gain no new argument, result
field or resource-admission mode. CE04 PreparedBands and AcquisitionBands routes,
CE06 preparation, CE07 full workflow and summary use the same applicable byte
rule; their stage-specific signed/count constraints continue to apply.

Representation rejection remains `ReconstructionError` for direct known-stage
calls, `AcquisitionModeError` for acquisition-mode calls, and
`WorkflowError(code="workflow_representation", stage="declaration")` for
declaration-time workflow/summary failures. A byte count above an obsolete cap,
with every remaining constraint satisfied, is not a representation error.
Independently invalid public fields keep their prescribed category. No new
ordering of simultaneous errors is specified. Tiny public inputs may pair a
newly permitted byte declaration with an independently invalid declaration to
observe the latter rejection safely; do not run its large numerical path.

Allocation failures inside the representable domain remain operation failures,
with causes retained by direct-stage wrappers; workflow and summary preserve
`MemoryError`, including allocation causes wrapped by a stage. Backend failures
remain stage operation errors with causes and available context. Interruption
propagates. No partial result, input mutation, disabled finite check or changed
debug/summary retention is authorized.

Original-domain small numerical cases retain the same binary64/complex128
calculation, units, signed outputs, parameter values, transforms, normalization,
ownership, full-debug records and summary projection. Existing initially passing
tests remain valid. A revised inherited assertion may no longer demand rejection
solely for an obsolete byte cap; it must preserve every independently justified
signed count/index/native/stencil rejection.

## Motivating target: integer classification only

For `(T,D,P,Z,Y,X)=(1,3,5,32,2048,2048)`, `O=3`, `L=2`, `A=1`:

| Quantity | Exact value |
| --- | --- |
| Output per time `(Zo,Yo,Xo)` | `(32,4096,4096)` |
| Native volume / padded real count / half-volume | `134217728` / `134348800` / `67174400` |
| Output plane / volume | `16777216` / `536870912` |
| Historical complex-native / complex-output bytes | `1073741824` / `4294967296` |
| Historical real-output / lookup / order bytes | `2147483648` / `67108864` / `24` |
| Binary64 image bytes, before other storage | `4294967296` (4 GiB) |
| Binary64 raw array bytes, if owned | `16106127360` (15 GiB) |

The listed signed count products and applicable aggregate native byte extents
fit their retained limits. Thus this geometry is representation-valid under the
extended allocation-byte rule on the supported 64-bit platform. Other public
declarations, actual stencils/cutoffs, numerical data and selected branches must
still be valid. No target array is created to establish this classification.
Caller inputs alone can approach a 16 GiB workstation's capacity; the image,
quadratures, diagnostics and backend workspaces add storage. Actual full-volume
allocation, time and feasibility are unmeasured and outside this task. Neither
summary retention nor choosing a smaller dtype establishes a 16 GiB fit.

## Scenario obligations and evidence

Each row is a distinct decision/outcome. Equivalent values and entry-point
replications do not add meaning. There are 18 scenarios; no scenario cap applies.

| ID | Required outcome | Paired positive/error examples and evidence |
| --- | --- | --- |
| W01 | Exact wide byte arithmetic has inclusive native bound and no wrap | Integer-only `M-1`, `M`, `M+1`; zero/negative only where allocation is required positive; check multiplication without float/fixed-width wrap. |
| W02 | All five CE04 byte-only ceilings are replaced | Historical-limit neighbors and reachable byte crossings; native/order/lookup math distinguished from element counts; never allocate a large success. |
| W03 | CE06/CE07/summary output and lookup byte ceilings are replaced | Integer-only output/lookup declarations across former byte limits, with valid signed counts; pair signed/native-invalid declarations. |
| W04 | Signed dimension/count limits remain | Below/at/above `I` where structurally possible, bool/noninteger rejection, ordinary valid count. |
| W05 | Signed element/product limits remain separately from bytes | Native/padded/half/output/metadata/order/phase products; valid wide bytes versus count overflow. |
| W06 | Required index/cutoff/backend-address constraints remain | Valid neighboring index and actual unsafe offset/cutoff; no blanket widening from the byte change. |
| W07 | Actual native extents remain required, including aggregate/empty stride cases | Integer-only native bound and aggregate crossing, item sizes 1/8/16, supported empty diagnostics; no successful empty scientific input invented. |
| W08 | Exact zoom and integral extent rules remain | Valid enlargement versus fractional/shrinking/nonexact/nonintegral or signed-overflow output. |
| W09 | Known declaration failures reject before array-sized/numerical work | Tiny backing with invalid signed/native geometry and safe declaration observers; pair ordinary tiny successful call. |
| W10 | Other public invalid declarations retain categories after wide-byte admission | Tiny backing, newly admitted byte declaration, independently invalid field; compare same field under ordinary geometry; no large numerical call. |
| W11 | Direct-stage applicable byte rules agree across accepted band-record routes | PreparedBands and AcquisitionBands metadata/extent proof plus tiny genuine preparations; preserve their existing dimensional differences. |
| W12 | Full workflow and summary agree on representation/error categories | Same safe integer/public cases through both entries, including declaration stage; successful small signed image/parameter agreement. |
| W13 | Motivating geometry is honestly classified without allocation or fit claim | Exact target arithmetic above and all retained constraints; documentation says resource/backend trial unmeasured. |
| W14 | Original-domain scientific computation remains unchanged | Independently justified small numerical controls and existing accepted CE02–07/RM84 tests, including signed/zero values permitted by selected operations. |
| W15 | Public signatures, record ownership and debug/summary compatibility remain | Small full/summary/direct records; original mutation/retention guarantees; no dtype/precision/resource parameter. |
| W16 | Actual transfer and buffer stencil rejection remains | Safe actual stencil versus unsafe vertex, including zero weights, under original public contracts. |
| W17 | Allocation and backend errors preserve type/category, causes and no partial result | Controlled small operation failures through existing real interfaces; ordinary successful operation control. |
| W18 | Interruption propagates and inputs remain unchanged on failure | Controlled small interruption/late failure and normal call; no partial result or mutation. |

Integer-only tests may use the specifically documented production metadata
validators in the interface excerpt. They must be used by real production
callers; a test-only seam is prohibited. Combine these proofs with tiny public
calls and original numerical controls. Where a byte-only branch is redundant
under another retained bound, demonstrate that implication rather than inventing
an impossible isolated public case. Do not invoke a huge successful allocation.

## Required delivery and verification

High-risk representation route: fresh blind A, fresh blind B, frozen accepted
tests/fixtures, restricted C, full exact-candidate Ubuntu 24.04 verification,
fresh independent D. Numeric limits on scenarios/reviews/resources are not set.
Coverage policy is approved behavior plus independent risk review, percentages
advisory. Required native statement/branch reports remain exact covered/total
globally, per owned package and per owned file, including never-imported files
and relevant subprocesses; unsupported metrics/exclusions/skips/missing reports
must be disclosed. No handwritten runtime exclusion or threshold change follows.
Focused checks and the full `make verify` gate are specified in the role packets.
This contract alone records no test, implementation, allocation or acceptance
result.
