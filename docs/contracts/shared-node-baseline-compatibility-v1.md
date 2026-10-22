# BASELINE-COMPATIBILITY-01 — proposed public preservation contract

Status: authorized baseline-preservation contract under the owner’s get-it-done continuation. This record authorizes its stated preservation scope and required roles; it supplies no acceptance checkpoint or readiness claim.

## Objective and boundary

The human has authorized completing the isolated baseline readiness work and SharedNodeVolumeTransfer, with new tasks as needed. This proposed prerequisite preserves the already contracted baseline while allowing private compatibility-preserving validation consolidation needed to attain the current native coverage requirement. No numerical execution, review, correction, scenario or spending limit was set. Merge and release are not authorized.

Risk route: high risk. The preservation boundary includes scientific/numerical meaning, binary representation and data-loss guarantees. A small internal refactor does not lower that risk. This contract has no role verdict yet.

Public baseline operations in scope are locate_bead_peak, correct_integer_drift, prepare_empirical_volume_response, correct_linear_response, estimate_translation, prepare_volume_order_otfs, prepare_volume_otf, separate_volume_phases, reconstruct_volume, declare_acquisition, scan_carriers, estimate_illumination, estimate_volume_order_gain, export_imagej and its existing CLI, the existing development reader preparation and source-free diagnostic commands, the verifier and its existing Make entry points, and the on-demand reference-fixture exporter. Existing prerequisite semantics incorporated by these contracts remain binding; incorporation does not authorize adding a feature.

Private validation consolidation may remove duplication or demonstrably unreachable defensive code only while preserving every documented accepted representation, rejected obligation, stable error, ownership guarantee, numerical/range decision, failure propagation and public operation. This contract does not prescribe a helper, call graph, allocation strategy or line/branch count. Coverage alone is not the behavior oracle.

## Proposed ownership and checks

Blind test-author ownership is limited to these two new files:

- tests/test_shared_node_baseline_compatibility.py
- tests/shared_node_baseline_fixture.py

Existing tests, fixtures, snapshots, numerical helpers, discovery, workflows, dependencies, lock, gates, skills, delivery rules and unrelated interfaces stay outside that ownership. The support fixture may contain compact independently derived case formulas, public real-file fixture construction, disposable repository/command fixtures, observers and public expectation calculations. It may not copy retired payloads, read production implementation as an oracle, rewrite existing reviewed helpers or conceal new scientific meaning in a shared observer.

Runtime ownership is in the private implementation packet; A owns only its two new test/fixture files. No unnamed runtime edit authority is granted. The later implementation role cannot change the accepted test/fixture checkpoint.

Before blind probes or tests, use the inherited source-free harness. Proposed narrow command after the two files exist:

    .venv/bin/python scripts/source_free_check.py pytest -q tests/test_shared_node_baseline_compatibility.py

Canonical full verification of the exact clean candidate remains:

    make verify UV=/absolute/path/to/uv \
      VERIFY_ARGS='--contract BASELINE-COMPATIBILITY-01 --reviewed-tests TEST-REVISION --base BASE-REVISION'

make check provides feedback only. Preparation supports no passing claim. The current owner instruction requires 100% native measured statements and branches for all instrumentable owned runtime, globally, per package, every owned file including never-imported files and relevant subprocesses. Older advisory paragraphs in inherited documents do not override this requirement. Native metrics not supported for an input must be reported honestly; Make/YAML and external dependency internals have no Python-coverage claim. No exclusion, skipped check, missing report, lowered threshold, test-discovery change or policy amendment is authorized here.

## Requirements

R01 — Public compatibility and binding. Preserve all named public exports, argument kinds, required keywords, record fields, CLI arguments, output schema/status and documented pure-array/file boundaries. Ordinary Python binding TypeError remains where specified. There is no automatic correction, reconstruction, parameter inference, grouping, scientific selection, file adapter or new public validation rule. Exact error prose and precedence for simultaneous invalid obligations remain unspecified where inherited contracts say so.

R02 — Operation-specific accepted representations. Preserve each operation's own plain-ndarray/type/dtype/rank/shape rules, all permitted widths and byte orders, strided/reversed/Fortran/read-only storage, singleton axes and signed values. Do not broaden a scalar or container rule by convenience conversion. Integer shifts/carriers/origins must keep their specified exact integer meanings, bool exclusions and representation distinctions. Lists, tuples, zero-dimensional arrays, NumPy scalars and object arrays are accepted only at the boundaries that explicitly accept them. In particular scan candidates may contain actual nonboolean integers in an object array; gain carriers require an integer ndarray or exact built-in integer list/tuple; drift requires integer ndarrays.

R03 — Source validation and conversion. Preserve source checks before lossy conversion where specified, converted-value checks, finite conversion rounding/underflow and operation-specific positivity. Scientific operations use their required independent native float64/complex128 snapshots. Source negatives do not become valid PSF/spacing/tolerance inputs by rounding to negative zero. Each operation’s coefficient/PSF positivity is assessed at its expressly contracted source/converted stage; no extra normalization changes that decision. Raw declaration instead preserves every sample's dtype, byte order and storage bytes, including nonfinite raw pixels and wider floating padding. Do not unify that bit-preserving boundary with scientific float64 validation. A valid RawAcquisition satisfies R1 public output invariants; manually corrupted nested metadata/schema has no newly defined outcome.

R04 — Scientific meaning and precision. Preserve these separate stored-input estimators, units, signs and acceptance budgets without adding thresholds:

- Bead location is the sole exact positive maximum of the converted z/y/x volume. Its value is that sample, not a fit or normalization. Lower ties and unequal maxima remain valid.
- Drift returns the exact negative-displacement indexed permutation and the positive carrier-dot-displacement phase correction. Integer arithmetic precedes the specified rational-cycle rounding. Huge phase sine/cosine meaning and circular phasor comparison remain; no phase-rank check is added.
- Empirical response uses the observed peak as the sole origin, exact real sum of converted dc as positive mass, one shared centering and mass for all orders, exact zero-order DC one and modular negative-order identity. Signed dc, overflowing mass, zero side rows and finite component values with overflowing complex magnitude remain permitted within the specified final range/accuracy policy.
- Linear response computes sequential binary64 subtraction, materializes its numerator, then divides. It preserves signed results, negative underflow zero and the declared coefficient units/provenance. An overflowing numerator rejects even if a different fused exact-real expression would be finite.
- Translation evaluates the full canonical periodic grid with one common intensity scale, no mean subtraction or brightness fit. Its dimensionless normalized root mean square scores, inclusive same-call ambiguity rule, motion sign and singleton behavior remain.
- Detection OTF and effective order OTF retain their negative-exponent, origin-rolled, centered native-grid sums, one detection-mass normalization, full complex values and cycles per micrometre coordinates. Positive side orders retain supplied axial displacement-frame coefficients, phase and relative gain; there is no per-order DC normalization or added factor of two.
- Volume separation uses the explicitly represented [1,cos(phi),sin(phi),cos(phi)^2-sin(phi)^2,(2*cos(phi))*sin(phi)] matrix with shown binary64 operation order, unweighted SVD least squares and c_m=(B_m-i*C_m)/2. It neither doubles enormous phases nor substitutes normal equations. Its strict numerical singular-value rank rule remains.
- Recombination separates supplied phases unchanged, relocates orders -2..+2 without wrapping into the explicit signed output window, derives negative transfers by modular frequency conjugation, combines the stated weighted estimator/ridge and then applies the amplitude mask. It retains complex signed Nyquist lifting, native axial count and field of view. A zero mask cannot rescue an overflowing unmasked quotient.
- Illumination uses the inherited represented first-harmonic separation and closed signed-grid cross-weighted complex fit. It returns unconstrained modulation, including values above one, and corrected represented-trigonometric phases. No support threshold, OTF magnitude replacement or physical-identifiability claim is added.
- Carrier scan preserves the entire validated input order, duplicates, exact signed carriers, distinct positive/negative candidates and successful independent outputs. It returns candidate-local information failures only for the two named codes, with no winner or fallback.
- Volume-order gain preserves the selected fundamental-phase five-column fit, exact order/carrier placement, cross-weighted complex least-squares correction, coherence amplitude, directly evaluated residual and all four information outcomes. There is no extra factor of two, inferred phase for zero gain, order-two half-angle or automatic correction.

All source-specific informative-regime budgets, mandatory-success conditions, representability definitions and boundaries remain exactly those in S01–S13. They are acceptance budgets on represented inputs, not newly chosen physical accuracy requirements. Conditions sufficient for success are not rejection cutoffs. Outside a stated informative regime, retain the defined estimator and range/information boundary; do not invent a uniform digit guarantee. Independent observers evaluate expectations and budgets without their own overflow/underflow.

R05 — Failure taxonomy and warning preservation. Preserve validation errors, rank/information outcomes, numerical execution failures and computed-result range errors separately. Translate only the exception categories and operation-time failures explicitly named by the relevant public source, in that source's permitted scope. MemoryError and unrelated exceptions propagate unchanged; no broad conversion/programming-exception catch or successful partial/fallback output is allowed. Preserve caller NumPy error mode and warning filters; handled arithmetic emits no forbidden arithmetic RuntimeWarning/FloatingPointError, while unrelated warning categories remain observable. Do not infer one global FFT exception policy: empirical/order/detection/recombination/gain transforms intentionally differ from illumination execution and translation's unpromised backend failure translation.

R06 — Result ownership. Preserve exact frozen binding/field contracts, independently owned mutable native C-contiguous output arrays, scalar Python types, metadata snapshots, nonaliasing and source preservation as each source specifies. Frozen bindings do not imply immutable contained arrays. Direct construction needs validation only when a public consumer expressly validates the supplied record. Direct VolumeOrderOtf and Otf2D consumer validation must include all specified fields, including an unused positive row; valid arbitrary finite effective transfers, zero rows and phase gauges remain accepted. Raw and linear-response metadata retain permitted nested built-in values and opaque labels, without new interpretation or deep-immutability claims. Concurrent external mutation is outside inherited snapshot promises.

R07 — Real-file ImageJ export and data-loss boundary. Obtain descriptors only through the documented inspect/harmonize path on genuine supported Priism source files. Export scalar uncompressed little-endian single-file OME-BigTIFF with header version 43 and 64-bit offsets at every size. Keep original source unchanged. Create the destination exclusively; existing/source-equal paths cannot be modified. Domain validation before creation leaves no destination. Later source/I/O/encoding failure reports non-success; a partial newly created destination may remain. No overwrite/truncation, automatic user-file deletion, atomic-publication or concurrent atomic-snapshot promise is added. Check source size, modification time and main-header digest before payload/extension access and at success; detected mismatch retains source_changed. Opaque extension hashing remains bounded and the original file remains necessary to recover omitted bytes.

R08 — ImageJ mapping, binary fidelity and metadata. Preserve setting series order s=o*P+p, exact ordinal names, absent versus declared-singleton indices, X/Y/Z/channel/time meanings, XYCZT plane order n=c+C*(z+Z*t), exact public source-plane mapping and complete nonoverlapping IFD ranges. No setting axis becomes acquired Z/channel/time. File/raw-reader decoded bits remain exact after endian normalization, including uint16 above 32767, signed zero, infinities and float32 NaN payloads. The pinned ImageJ importer separately retains unsigned/finite values, infinity sign, signed zero and NaN classification; JVM payload limitations are disclosed. Preserve recoverable main-header bytes, finite metadata JSON, public descriptor values, complete setting declarations, source basename-only identity, source-referenced opaque extension length/hash and all required limitations. Sampling units, binary64 serialization and ImageJ unit-conversion expectations follow S14; no inferred time/angle/origin/wavelength role is added. Preserve signed32 dimensions/series/plane indexing and float32 physical-size limits, unsigned64 offset/count limits and positive nonbool block size without artificial practical caps.

R09 — Development reader preparation. Preserve locked sync followed by scripts/prepare_imagej_reader.py and the existing prerequisite relationships. Every preparation authenticates cached jar bytes. Corrupt cached bytes fail and remain for diagnosis; absent bytes download only to scoped temporary storage, reject redirects/oversize/timeout/digest mismatch and publish only matching bytes. Failure removes temporary download and stale identity manifest as documented. Preserve the pinned reader identities/byte limits, bounded deadlines, selected SIMRECON_JAVA or PATH executable, required reported Java version/source-launcher capability, inputs.json identity fields and external development-input boundary. Product export never launches Java or redistributes jars.

R10 — Source-free diagnostics. Preserve the documented python/pytest modes, subprocess status, warning category/message/location, exception category/message/chain/group/stack locations and original exception fields. Suppress standard source snippets and locals, including SyntaxError formatting. Standard timeout/child-failure diagnostics retain executable identity and duration/status without arguments/inline source; a string command reports executable identity unavailable. Preserve inherited Python-child handling, required pytest flags, 300 s default and positive explicit timeout. Reject interpreter options that disable the environment, including combined -I/-S/-E forms; program arguments after -c/-m/script remain untouched. Explicit/custom source output and changed child environments remain outside this rendering aid's guarantee; this is not engineered source access control.

R11 — Verifier behavior and honest evidence. Preserve the 13 public phases and order: sync, coverage-clean, lint, format, types, tests, coverage-combine, coverage-json, coverage-html, coverage-report, wheel, wheel-import, audit. Retain actual attempted argv with selected UV, command-failure stopping/status, missing command 127, evidence failure 1, invalid arguments 2 and success 0 only with complete valid evidence. Preserve no retries, Git mutation, publication or role launch. Record authentic phase output and honest incomplete evidence. Receipt schema/identity/environment/input privacy, current complete native reports and same-run artifact/measurement truth remain; direct non-opted-in helper callers retain the inherited legacy measurement behavior. Current mandatory measurements are taken from the single existing M25 invocation, not a second scientific run. Receipt/log writes cannot overwrite tracked candidate content or private/common Git metadata, including missing tracked files, unavailable identity, linked .git pointer files, initial/phase-introduced symbolic or hard-link aliases and output ancestors. Revalidate destinations when writing; earlier safe resolution does not authorize later redirection. Own writes cannot replace current measurements, actual current phase logs, native database or complete emitted HTML evidence while claiming success. Safe custom outputs, neighbors, safely unused stale aliases or safe replacement remain permitted; no blanket directory ban or prescribed private filename/layout is added.

R12 — Reference exporter compatibility. Preserve exactly the required otf and reconstruction selectors, complete deterministic JSON document on stdout, no scientific knobs and no created files/directories/default destination. Compute before emission; generation/output failure is non-success. Preserve scientific schemas/ordering/IDs/shapes/dtypes/C-order complex layout/axes/origins/source whitespace/units/parameters/accuracy fields and parsed binary64/integer values exactly. Preserve S17's documented frozen mathematical helpers and explicit conventional-plane left-fold recipe; production numeric output never supplies the oracle. No encoded retired payload or copied generated array replaces compact formulas/digests. Historical labels/checkpoints/digests remain historical fields, never fresh acceptance. The TemporaryDirectory lifecycle remains documented; new generation provenance is recorded separately. No retirement, historical-package rewrite or new fixture family is authorized by this baseline task.

R13 — Meaningful test design and lawful seams. Prefer public-entry end-to-end preservation tests and independently grounded positive/error/failure pairs. Public numpy.fft.fftn/ifftn dependencies may be controlled only where S03/S06/S07/S09/S13 expressly name them. Admissible tests preserve legitimate batching, axis permutations, equivalent normalizations and exact-zero bypasses; no call-count/private-organization oracle is allowed. Public documented solver failures may be assessed through legitimate public dependency calls once their exact inherited seam is supplied. File/reader/verifier tests use owned disposable files/repositories, public commands and real emitted same-invocation evidence. Do not fabricate inconsistent DatasetInfo descriptors, impossible OS/private states, malformed RawAcquisition internals, source dtype behavior through a new NumPy copy seam or artificial product-red solely to raise coverage. An initially passing meaningful preservation test remains valid. Unresolved failure causes are diagnosed as environment/tooling, test defect, product defect or unresolved requirement before repair; that label grants no new edit ownership.

R14 — Scope and gate preservation. This task cannot alter scientific formulas, tolerances, dependencies, version semantics, binary/file formats, security/permission boundaries, coverage instrumentation/exclusions, checks/discovery/workflows, delivery policy or new interfaces. Evidence reuse applies only to unchanged material candidate/checkpoint/fixture/lock/check/base/environment/external inputs with no challenging failure. Keep exact-candidate full-local gate and current 100% targets. This proposed contract is not evidence that either gate has passed.

## Coherent scenario inventory

Each row is a distinct documented decision, interpretation, output or guarantee. Equivalent widths/endianness/layout values within a row are coverage examples, not extra meaning. There is no scenario cap. The future author maps tests to every applicable row and reports any row not established; this table does not authorize private-state fabrication to fill a row.

| ID | Observable preservation scenario and genuine examples |
|---|---|
| C01 | Required public binding and exact fields/CLI schema remain; omit one keyword versus a fully valid call. |
| C02 | Reject nonplain/nonarray inputs only at boundaries that require plain ndarrays; pair lists/subclasses/masked arrays with accepted ordinary strided ndarrays. |
| C03 | Preserve each accepted and rejected dtype domain; pair signed/unsigned real arrays with bool/object/complex rejection where applicable and permitted complex side orders. |
| C04 | Preserve each rank/shape/count rule; pair malformed/empty arrays with supported singleton/nonsquare shapes and valid phase counts. |
| C05 | Source nonfinite numeric components reject in numeric kernels; converted overflow separately rejects, while finite rounding/underflow stays accepted. |
| C06 | Source sign remains binding when lossy conversion could hide negativity; pair a source-negative underflow case where a wider native type exists with valid signed zero/positive subnormal. Report unavailable wider precision. |
| C07 | Preserve exact integer carrier/displacement/origin extraction and per-API containers; pair extrema/huge integers/negative/zero with bool and fractional rejection. |
| C08 | Representation-specific scalar rules remain; pair documented zero-dimensional tolerance with disallowed coefficient NumPy scalar/list/broadcast array. |
| C09 | Successful and rejected calls preserve caller bytes/strides/flags/metadata and have no successful partial result. |
| C10 | Results preserve frozen bindings while arrays remain mutable and independently owned across inputs/fields/calls, as promised per record. |
| C11 | Bead unique positive converted peak returns its exact z/y/x index and value; unequal secondary peaks and lower-value ties remain valid. |
| C12 | Bead no-positive maximum rejects; zero/signed-zero/all-negative samples differ from a positive minimum subnormal. |
| C13 | Bead exact positive tie rejects; unequal near ties remain valid and conversion-created ties use converted equality. |
| C14 | Drift image permutation uses negative motion correction with periodic borders, arbitrary integer aliases and N=1. |
| C15 | Drift circular phase has positive carrier-dot-motion sign and exact integer rational cycle; huge finite phases/extreme integer products stay valid. |
| C16 | Drift accepts repeated/degenerate corrected phases and leaves downstream rank rejection downstream. |
| C17 | Empirical response shares observed origin and exact dc mass; [2,-1] is permitted while [2,-3] rejects nonpositive mass despite a valid peak. |
| C18 | Empirical overflowing positive mass and minimum-subnormal positive mass cannot alone reject safely representable responses. |
| C19 | Empirical zero-order DC is exactly one; all orders retain shared normalization, full complex side phase and exact zero side rows. |
| C20 | Empirical common roll and declared phase-gauge changes obey the documented identities; no true-center or supplied-PSF substitution. |
| C21 | Linear response all scalar/array coefficient combinations obey exact alignment, strict converted response positivity and declared opaque units. |
| C22 | Linear response sequential numerator overflow rejects; finite negative/subnormal results and negative underflow zero remain valid. |
| C23 | Linear-response original/applied coefficient and metadata provenance snapshots remain independent and retain supplied forms/labels. |
| C24 | Translation full-grid objective/sign/canonical even half-period agree with independent finite periodic calculation, including arbitrary off-model data. |
| C25 | Translation same-call inclusive tolerance produces sole/ambiguous results without choosing a first winner; exact ties/near ties/zero/large tolerance remain valid. |
| C26 | Translation (1,1), constant and zero images remain accepted, with no invented information rejection or intensity threshold. |
| C27 | Detection PSF finite nonnegative source and positive converted mass are separate decisions; signed zero is valid, all converted-zero mass rejects. |
| C28 | Detection OTF normalization/origin/negative sign/full complex centered grid match an independent asymmetric finite-sum kernel; all-maximum/all-subnormal kernels remain valid. |
| C29 | Frequency accuracy/zero/noncollapsed ordering and extreme singleton spacing are preserved; unrepresentable nonsingleton coordinates reject without intermediate-product shortcuts. |
| C30 | Order OTF accepts zero/signed/complex/large finite axial coefficients and retains relative side amplitude/DC/phase; no physical-realizability cutoff. |
| C31 | Axial displacement-frame mode shifts, common roll/origin identity and modular negative-order conjugation remain, including even Nyquist. |
| C32 | Detection/order/empirical public FFT controlled failures translate only the named numerical categories/nonfinite stages; unrelated RuntimeError/TypeError/ValueError and MemoryError retain identities. |
| C33 | Order/empirical final restoring-scale overflow is a distinct range failure; finite components with overflowing mass/magnitude/intermediate scale alone remain permitted where guaranteed. |
| C34 | Volume separation represented phasor-square matrix, signs and factor distinguish dc/c1/c2, huge finite phases and unequal N>5 off-model projections. |
| C35 | Volume rank five uses strict SVD threshold; full-rank repeated-phase sets remain valid and deficient phase sets reject without a condition cutoff. |
| C36 | Volume public solver LinAlgError/unusable factors differs from nonfinite final coordinates; unrelated/allocation failure propagates. The packet must supply a legitimate inherited public solver seam before controlled execution. |
| C37 | Supplied transfer consumers validate every field/unused row; valid direct finite complex zero/non-Hermitian/nonunit/gauged records remain allowed where contracted. |
| C38 | Recombination exact signed nonwrapping window retains every band and rejects insufficient output even with zero transfers/mask. |
| C39 | Recombination weighted estimator/gain/ridge and post-quotient amplitude mask match independent stored-input sums. |
| C40 | Recombination complex signed even-Nyquist lift and negative-order modular conjugation remain; no forced real interpolation or Nyquist splitting. |
| C41 | Recombination output field of view/native z/sample-center coordinates and independent complex records remain; invalid output spacing/grid rejects. |
| C42 | Recombination operational estimator/restoration range rejects separately from normalized FFT failure; zero mask cannot rescue an overflowing quotient. |
| C43 | Recombination informative-regime and all-zero-image success remains required; outside regime zero data does not waive gain/transfer range failures. |
| C44 | Raw declaration canonical named-coordinate mapping preserves exact raw bytes, wider padding, NaNs/infinities/signed zero and absent versus explicit singleton axes. |
| C45 | Raw kind/axes/config version/schema decisions remain, including SIM orientation/phase requirements and detection-PSF exclusions. |
| C46 | Raw resolved sampling/wavelength/nominal-command tensor rules preserve unknowns, channels and group ordering, without inferred units/roles/phase truth. |
| C47 | Raw whole-field overrides can replace invalid optional declarations; structural fields stay validated and equal/None overrides remain deterministic provenance. |
| C48 | Raw supported acyclic nested metadata snapshots retain opaque bytes/nonfinite floats and reject unsupported/cyclic values without new interpretation. |
| C49 | Illumination geometric overlap/no overlap differs from computed zero predictor/response/cross-product unidentifiability. |
| C50 | Illumination unweighted complex fit/sign/factor/residual and corrected represented-trig phases retain unconstrained modulation above one and huge finite steps. |
| C51 | Illumination full supplied Otf2D record/grid validation, inherited separation failures, named transform execution failures and final range remain separate. |
| C52 | Scan validates every row before execution; a valid prefix cannot hide a malformed later carrier. |
| C53 | Scan preserves order/duplicates/opposite/zero/exact huge carriers, independent successful output arrays and each named local failure; all-candidate failure remains valid. |
| C54 | Scan aborts and propagates other domain/numerical/allocation/unrelated failures without a partial tuple, winner or fallback. |
| C55 | Volume-order gain order selection, exact shifted overlap count/sign and cross weighting retain the no-extra-factor estimator. |
| C56 | Gain empty overlap and zero predictor reject; zero response instead returns zero_response with zero gain/residual/coherence. |
| C57 | Gain nonzero orthogonal response returns zero_correlation with gain zero/residual one; ordinary nonzero correlation returns fitted, including restored gain underflow to zero. |
| C58 | Gain safely representable components F+iF do not reject solely on complex magnitude; normalized FFT/range failure categories remain separate. |
| C59 | Explicit gain correction copies/calibrates only selected positive row; E0/unselected row remain and order two is not forced to square/half-angle composition. |
| C60 | Each informative-regime accuracy/mandatory-success promise is tested with independently established conditioning/margins and overflow-safe budgets; no invented physical tolerance. |
| C61 | Caller floating policy/warning filters restore on success/rejection/handled failure; unrelated warning category and exception identity remain observable. |
| C62 | Genuine supported Priism inspected/harmonized inputs export all settings; mode/axis/config/block/source-change errors retain their own meanings. |
| C63 | ImageJ absent versus declared-singleton setting/z/channel/time remains recoverable, with exact series/name/plane/pixel coordinate maps. |
| C64 | Export is uncompressed scalar single-file little-endian BigTIFF at small sizes too; independent raw decoding preserves uint16 and float32 special bit patterns. |
| C65 | Actual pinned all-series reader preserves its documented pixels/series/scales and separately discloses JVM NaN payload limits. |
| C66 | Copy annotation/header/public metadata/extension digest/provenance/limitations retain exact documented fields and finite JSON, without private absolute source paths. |
| C67 | Format/index/physical-size representability rejects real inspectable supported files/configs at accessible boundaries; no inconsistent descriptor construction or claimed infeasible huge allocation is required. |
| C68 | Existing/source-equal destination raises ordinary exclusive-creation failure with protected bytes unchanged; precreation domain failure leaves no file. |
| C69 | Source change before access/at completion and later genuine I/O/encoding failure yield non-success, preserved original bytes and honest partial-new-file limits. |
| C70 | Bounded block-plane pixels/extension hashing preserve documented resource behavior through genuine file reading; no whole-acquisition allocation or viewer-heap guarantee is inferred. |
| C71 | Reader valid cached/downloaded pinned bytes produce identity; corrupt cache fails without replacement and failed preparation removes stale identity. |
| C72 | Reader redirect/oversize/timeout/hash failure cleans scoped temporary bytes; selected Java identity/version/source launcher and external jar boundary remain. |
| C73 | Source-free direct warning/exception/chains/groups/SyntaxError and pytest/Python-child channels retain category/message/status/locations while hiding standard source/locals. |
| C74 | Source-free command timeout/CalledProcessError omits args/source but retains executable and duration/status; string-command identity unavailable stays honest. |
| C75 | Source-free disabling interpreter options reject, while literal program -S/-I/-E arguments after program boundary remain; positive timeout validation/default are preserved. |
| C76 | Verifier safe successful ordinary fixture runs all 13 phases with authentic argv/status/logs; failed/missing command stops later phases with original statuses/no retry. |
| C77 | Verifier receipt identity/context/environment/input privacy/current native-report/artifact evidence remains truthful; invalid/incomplete/stale/changed evidence cannot pass. |
| C78 | Verifier initial/temporal receipt or current/future log aliases/ancestor redirection cannot change tracked/Git bytes, including linked .git pointer/private/common locations. |
| C79 | Verifier dirty/missing tracked/unavailable final identity/failing phases never waive own-write protection or permit false success. |
| C80 | Verifier own receipt/log writes cannot replace authentic current measurements, emitted logs, native database or any current HTML report member while passing. |
| C81 | Safe custom receipt neighbors, unused/stale aliases and safe replacement retain ordinary behavior; binding observers use actual same-invocation paths and do not require cross-run recurrence. |
| C82 | Opted-in mandatory same-run measurements remain authentic from one existing invocation; direct legacy callers remain valid and failed tests may retain diagnostics without passing. |
| C83 | Reference otf/reconstruction selectors produce one deterministic complete document, no files/directories/scientific knobs; generation/output/usage failure is non-success. |
| C84 | Reference scientific parsed binary64/int fields/acquisition bytes/order/schema and compact independent formulas match public digests; whitespace-only serialization is not falsely called numerical drift. |
| C85 | Reference frozen helper meaning and conventional-plane ordered binary64 multiply/add remain, with historical fields separated from current generation evidence. |
| C86 | Documented TemporaryDirectory lifecycle and existing command/dependency/check behavior remain; no baseline readiness, role acceptance or physical validation claim is inferred from output. |

## Permitted concrete oracle examples

These are compact starting cases, not mandatory private layouts or a cap. The author derives independent results and supports all acceptance margins.

- Bead: a shape (1,1,2) volume [2,-1] has peak (0,0,0), value 2; [2,2] is an exact positive tie; [0,-1] has no positive maximum. The empirical case [2,-1] has exact mass 1 and DC one, whereas [2,-3] has mass -1 and rejects before successful response. A finite maximum float64 peak is valid without computing a norm.
- Linear response: raw=110 count, offset=10 count, response=2 count/electron yields (110-10)/2=50 electrons. Independently varying full coefficient maps distinguishes accidental broadcasting. A finite maximum positive raw minus finite maximum negative offset makes the specified numerator nonfinite and must reject even when a large response could rescue a fused quotient.
- Translation: make moving(y,x)=reference((y-dy) mod Ny,(x-dx) mod Nx) from an independently labeled asymmetric array and choose a distinguishing score margin; returned motion is d and aligning roll is -d. A (1,1) zero pair has exactly one candidate. Constant larger arrays with tolerance zero admit computed ties.
- Drift: use an asymmetric frame with an exact integer displacement and a rational quarter-cycle carrier increment; check indexed bytes/values and circular phase sign. Permit N=1/repeated phases and exact int64/uint64 endpoints; do not simulate specimen drift by rolling stationary illumination and claim the wrong physical model.
- Volume separation: the declared signal 10+4*cos(phi)+2*sin(phi)+6*cos(2*phi)-8*sin(2*phi) distinguishes dc=10, c1=2-i, c2=3+4i in the ideal model. Build observations/expectations on the required represented phasor-square matrix and assess stored-input least squares rather than asserting exact-real trigonometric truth for rounded data.
- OTF: use a genuine nonnegative asymmetric delta/small finite kernel with an explicit origin, independent negative-exponential finite sums and odd/even/singleton dimensions. Coefficient rows 0 and a finite pure phase show side-zero/DC/relative-phase preservation. A delta carrying finite coefficients F+iF exercises allowed overflowing complex magnitude at representable component range.
- Recombination: detector Nx=4, carrier zero, E0=1, side rows zero and dc=(1,-1,1,-1) lift the canonical kx=-2 coefficient onto output Nx=8 as exp(-2*pi*i*2*x/8). This must retain its complex imaginary samples. Use valid directly constructed VolumeOrderOtf records with canonical public frequencies, never fabricated internal descriptors.
- Gain: with nonempty overlap and nonzero predictor, independently supply zero selected separated response to obtain zero_response. For zero_correlation use genuinely representable orthogonal overlap vectors and a distinguishing exact cancellation fixture. A one-pair informative nonzero fit has residual near zero but provides no physical identification guarantee.
- ImageJ: construct a real small supported Priism file with independently coordinate-labeled unequal dimensions, declared/absent singleton settings and supplied resolved sampling. Obtain DatasetInfo via inspect/harmonize, export and independently decode raw TIFF/OME mapping and pinned-reader results. Use known uint16 words above 32767 and float32 signed-zero/infinity/NaN payload words. Existing destination marker bytes remain unchanged. Accessible float32 physical-size limits can be exercised through real file config; impossible memory/private-descriptor claims are excluded.
- Verifier: a disposable repository and trace-emitting genuine commands establish attempted phase order/status and safe outputs. A phase may create an alias to an owned tracked marker; assertions preserve marker bytes and bind any challenged write destination to this invocation's emitted paths. A legitimate unused alias can pass. Authentic native containers/reports used for own-write tests establish preservation only, not measured production scientific behavior or the canonical coverage gate.
- Reference exporter: call each selector under the locked interpreter through source-free subprocess handling, parse JSON independently and pack documented acquisition values as C-order little-endian binary64. The commensurate acquisition shape (2,7,7,9) is 2*7*7*9*8=7,056 bytes, a useful size sanity check. Check the exact acquisition-byte digests and independently derived fields; compare a historical dataset byte digest only when its full serialization is actually reproduced. Do not use product output as an expected array.

Documented numerical FFT seams can supply controlled FloatingPointError/OverflowError/arithmetic RuntimeWarning/nonfinite factors and propagation sentinels when the relevant source explicitly permits them. Distinguish expected values from dependency-intervention tests. No named NumPy copy seam or arbitrary backend-specific injection is supplied by this contract.

## Public expectation sources and inherited read scope

Read only the following technical/public portions. Names below are local source identities, not traversal instructions. The author packet should carry immutable selected excerpts and their hashes; do not follow embedded package/archive/history/lesson/status links. Historical authority, delivery rounds, roles, accounting and readiness narratives in the parent documents are excluded. Current owner instructions and this task's actual constraints govern routing/gates.

| Source | Document and selected public portions |
|---|---|
| S01 | bead-peak-localization-v1.md: Public boundary and estimator; Representation, ownership and failures. |
| S02 | integer-drift-correction-v1.md: Public operation; Scientific model and sign; Exact pixel operation and circular phase arithmetic; Result and composition. |
| S03 | empirical-volume-response-v1.md: Public boundary and meaning; Representation and native sampling; Numerical execution, accuracy and failure; Result and errors. |
| S04 | linear-response-correction-v1.md: Scientific meaning and public boundary; Input/coefficient alignment/units; Arithmetic representation and range; Result and provenance; Errors and compatibility. |
| S05 | translation-estimation-v1.md: Public boundary and representation; Fixed objective and conventions; Result and ambiguity. |
| S06 | volume-order-transfers-v1.md: Operation and scientific meaning; Numerical and range boundary; Record/errors/compatibility. |
| S07 | volume-otf-preparation-v1.md: Scope/public interface; Mathematical meaning; Numerical/range/failure boundaries; Result/errors/compatibility. |
| S08 | volume-phase-separation-v1.md: Public operation/scope; Input representation/errors; Represented phase model/sign; Rank/accuracy/range; result-record paragraph only. |
| S09 | volume-recombination-v1.md: Public operation; Effective transfer records; Signed window/estimator; Output coordinates/record/numerical execution; Informative accuracy/mandatory success; Errors. |
| S10 | raw-acquisition-declarations-v1.md: Public boundary; Explicit array layout/kind; Config/metadata schema; Overrides/provenance; Failures/representation. |
| S11 | carrier-scan-v1.md: Public boundary; Per-candidate operation/result; Interpretation/limitations. |
| S12 | illumination-estimation-v1.md: Public boundary; Model/estimator; Corrected phases/result; Arithmetic/errors/accuracy. |
| S13 | volume-order-gain-v1.md: Public operation/meaning; Overlap/stored-input estimator; Distinct information outcomes; Scaled numerical policy/accuracy; Record/errors/explicit caller composition. |
| S14 | imagej-export-v1.md: Outcome/source; Public interface; Axis/plane mapping; Pixels/scale/limits; Recoverable copy metadata; Public metadata/rejection details; Integrity/destinations/resources. |
| S15 | verification-output-protection-v1.md: public-entry own-write guarantees, P01–P11 observable table and technical preservation limits only; strip historical correction/authority/role/accounting paragraphs. |
| S16 | verification-receipt-v1.md: Public entry points; Receipt schema/identity/evidence; strip historical authority/ownership clauses and do not inherit obsolete advisory targets. |
| S17 | reference-fixtures-v1.md: public selector/stdout/temporary lifecycle; Observable requirements R1–R4/R6 scientific preservation only; strip historical authority/review/task accounting and do not authorize new retirement work. |
| S18 | operations/imagej-reader-environment.md: pinned identities/cache/fetch limits/Java prerequisites/manifest; documented source-free commands/rendering behavior/limits. |
| S19 | operations/verification.md: documented Make commands and current-evidence measurement behavior; strip historical adoption/role/readiness claims and advisory-target authority. |

Public preservation constants from S17: the two dataset digests identify historical serialized documents. They are not a new byte-serialization requirement for fresh output when scientific parsed values match and only whitespace differs. The acquisition digests apply to independently reconstructed C-order little-endian binary64 bytes and must still match exactly.

- OTF dataset SHA-256: ba2dcd790738cf950b184995e1c12935266ddaa1738c9f874b46a6dd442c9dcf.
- Reconstruction dataset SHA-256: 64decad0389d332100bee202a02a8bafacd1c942e324dff992babccb8ca88541.
- Commensurate acquisition SHA-256: 83281edcbaf738af9f78b025630a27ed50f8270349114fb7b7bbca427ffc97e2.
- Fractional acquisition SHA-256: bb1f007740ae091fdae2037bf83cae210147c6d5e0bf3d343fc682e14520bcc5.

Required development-reader identities from S18: Bio-Formats 8.5.0 bundle SHA-256 c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9, maximum 70,000,000 bytes; ImageJ 1.54p SHA-256 2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20, maximum 10,000,000 bytes. Fetch socket timeout 15 s, parent deadline 180 s. Reported Java version 21.0.7 and JDK source-file launching remain required. These are inherited pinned contract identities, not fresh claims about latest releases or fetched artifacts.

## Inherited supplemental public inputs and uncertainty

No new scientific choice has been identified in the named source portions. Public semantics are inherited; completeness/oracle adequacy require independent B and later D review.

The named sources incorporate public semantics not fully reproduced in the authorized read set: separate_phases v2 image/phase/rank/solver codes and exact public solver seam, Otf2D supplied-record invariants/tolerances from known-parameter reconstruction, and inspect/harmonize/read/conversion behavior underlying DatasetInfo. The packet supplies approved immutable supplements S20–S23 for these details. Do not infer them from implementation, existing tests, traversal links or a guessed dependency hook. C36/C51/C62 use the supplied inherited supplements; they create no new semantics.

The supplied S23 contains the exact same-run measurement schema. Preserve the documented existing behavior; if a new assertion needs field names/rules beyond those excerpts, the coordinator supplies the approved public measurement excerpt. Coverage/native-container or wheel observers must establish authentic public format requirements without inspecting runtime. No controlled private parser state is authorized.

Native wider-float availability, feasible representation-bound fixtures, reader connectivity/JDK availability and supported-platform evidence are environment facts to establish later, not assumptions counted as successful execution. The coordinator separately verifies the composed candidate; this contract asserts no result from that verification.

