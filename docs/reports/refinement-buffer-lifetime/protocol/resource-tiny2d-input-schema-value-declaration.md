# RB117 four tiny2d observations — pre-call literal declaration

FROZEN DECLARATION ONLY. No target, constructor, validator or oracle code was run
or added to make this file. This records existing public fixture/schema/value and
retention meaning before the four calls. It is no grant, physical accuracy claim,
resource acceptance or resource-saving target. ROOT selects exact actual row ids,
immutable grants, fresh admission and exclusive execution windows separately.

## Frozen subjects and sources

Parent root /workspace/work/issue-116, HEAD158776ade28079276304d49a6b973eccbf4109c9,
tree23530ae22e7e1a64f8171dbbedfea81d1b00174c. Candidate root
/workspace/work/issue-117, HEADe6945817850cfdaa3ebbfe21e7a23784964208d6,
treecd637c9b568e2cbe35119193804b36105ec54500. Same external measurement overlay:
observer eacf24b70cd67f12e403906cf92bb7cb1bb1a7632645335a8b8f3bfbc4225745;
runner 6f34617bb59c060eeceeeb6a06a6180755448f3310481202f96df5e5dd1fe14f;
child 5249e4cdadbee6523012127468fd9c3d90228df2558c81087929bc35e60e5459;
preserved qualifier 56c1dafe3c6bdab3b9e9e6fdefc1dc01d419b09e6f6f09bc8b302073474f2a21;
manifest 1854f8760dd9ede607b2611f2d9640e1e3a7056e054ae564211fdea90ef7d4ed.
Separate control driver65b is not substituted for the preserved measurement key.

Existing public sources under both selected product roots have matching hashes:
- tests/reconstruction_summary_fixture.py:
  271335a5065791a986de239cdf89e4d15eb0f2e5df80943d6cb084167516d20f.
- tests/reconstruction_memory_benchmark.py:
  929106da36b47bcd03ed785d1a7f6b941d04299403b6c0ffe7df9846f3809b8f.
- docs/contracts/reconstruction-memory-v1.md:
  3630933e71fbda5cf78ae36943cbbb9dc4fbfe1c0e3d993622dd37da4fcb196a.
- docs/contracts/c-equivalence-workflow-v1.md:
  00b80613c1ff417b4d5bdd782cf25e1aed32a9c62ccf44d68cce77c643b9adef.
- docs/contracts/c-equivalence-carrier-modulation-v1.md:
  15a467853fb4db0dda4553f94dcd1a06f0dfed431d7c67863489dc4a11ecd02c.
- docs/contracts/c-equivalence-optical-transfer-v1.md:
  3214afc2766e7bb19bdb3eaf81356dac1ef17630995bb98282fa3d46f0237529.

SOURCE2 report9fab586ead7da9a0f36956fbc784fed6d6e7f6f6245ab23db5cfa06573405805
accepts source suitability with prerequisites, not an executed or scientific pass.
Its exact four integration rows and unchanged validate_complete_record remain the
schema baseline. No implementation-dependent numerical truth is introduced.

## Literal caller case fixed before observation

Exactly fixture.scenario("2d-search"): workload((2,2,1,12,16), mode="2d",
search=True), default radial transfer. Dimensions T2,D2,P5,Z1,Y12,X16,O3,L2,A1.
Returned specimen is float32 shape(2,2,5,1,12,16); transfer.samples is complex128
shape(3,64,1). Input array identities name them "specimen" and "transfer.samples".
Declared samples are exactly complex64-representable dyadic values, held in the
contract's owned complex128 array; no new rounding or physical model is added.

For integer z,y,x in their finite ranges, the exact source expression order is
fixed by fixture2713, not algebraically rewritten for execution:
object_counts = 30 + 3*cos(2*pi*(x/16+y/12))
  + 2*sin(2*pi*(2*x/16-y/12)) + cos(2*pi*(z/1+3*x/16))
  + .75*cos(2*pi*(3*y/12+x/16)).
For t=0,1, d=0,1 and p=0..4: angle=d*pi/2,
spatial=2*pi*(x*cos(angle)+y*sin(angle))/8, phase=2*pi*p/5;
illumination=1+(.31+t/64)*cos(spatial+phase)
  +(.13+t/128)*cos(2*spatial+2*phase+.3);
raw[t,d,p]=float32(object_counts*illumination+d/4+t/8).
Transfer for m=0..2,r=0..63,a=0 is
1+m/16+r/128 + 1j*(m+r+a)/256, radial dkr=dkz=.125 cycles/um.
No scalar/vector formula is a claim of universal libm/FFT error or physical recovery.
The unchanged scenario source first constructs its default workload() before
selecting the returned 2d case; keep that existing generation behavior on both
roots. Whole-process observations include imports and input generation, not an
isolated target allocation.

Acquisition: 2d, dxy=dz=1um, norders3, background0, lateral_zoom2, axial_zoom1,
phase_policy uniform, edge_pixels0, equalizeFalse. Optics: wavelength500nm,
NA1, immersion_index1. Carrier: linespacing4um, phase_start_angle0,
search_carriersTrue, use_time0_carriersTrue. Filtering: wiener.5,
suppress_singularitiesFalse, output_taper none. Specimen id rm84-multifrequency-v1,
intensity_unit signed-counts; transfer id rm84-complex-dyadic-v1,
intensity_unit dimensionless-transfer, same optics. Unlisted optional settings
keep the already approved public defaults; no metadata/configuration is injected.

Expected branches, fixed independently of observed output:
[["searched","searched"],["time0-reused","time0-reused"]].
First time searches both directions; second time reuses time-zero carriers and
still fits that time's modulation. Every row profile is literal false and stages
must be the empty list. One public workflow call; no warmup/reference call.

## Seven common field identities and shapes

All seven are NumPy numeric arrays. JSON output_hashes uses four-element identity
lists [name, shape-list, canonical-little-endian-dtype, sha256]. Finite common
fields must be true; identity digests are 64 lowercase hexadecimal characters.

| Name | Public dtype / canonical identity dtype | Expected shape |
| --- | --- | --- |
| image | float64 / <f8 | [2,1,24,32] |
| x_um | float64 / <f8 | [32] |
| y_um | float64 / <f8 | [24] |
| z_um | float64 / <f8 | [1] |
| carriers_cyc_um | float64 / <f8 | [2,2,2] |
| modulation | complex128 / <c16 | [2,2,2] |
| raw_modulation | complex128 / <c16 | [2,2,2] |

Coordinates follow existing CE07 labels: x[j]=(j-16)/2um,
y[i]=(i-12)/2um, z[0]=0um. Summary reads parameters directly from the result;
full reads the actual nested result.parameters. This declaration does not amend
validate_complete_record: that unchanged function checks legal identity types,
finite/map/schema/status structure; responsible review additionally checks these
predeclared particular shapes/dtypes and exact branch values.

## Four rows, value comparisons and retained owners

Run repetition1 in this exact order, with ROOT's fresh per-row ids/grants:
1. parent, rb117-2d-search-summary, mode summary, case2d-search, profilefalse.
2. candidate, rb117-2d-search-summary, mode summary, case2d-search, profilefalse.
3. parent, rb117-2d-search-full, mode full, case2d-search, profilefalse.
4. candidate, rb117-2d-search-full, mode full, case2d-search, profilefalse.
All spec shapes are [2,2,1,12,16], searchtrue, repetition1.

Input_sha256 and both input-array identities must agree in all four records,
using the existing public_value_sha256/array_identity protocols. Numeric input
hash values have not been executed or invented in this declaration; immutable
fixture/helper source identities and literal recipes above fix their pre-call
meaning. Observed hashes serve exact same-input comparison, not fitted truth.
Same mode parent/candidate must have identical seven output identities,
common_output_sha256 and complete public_result_sha256. Across full/summary,
compare only the seven common fields/common_output_sha256 and expected branches;
complete record fingerprints intentionally describe different public graphs.
No tolerance is created or widened; a mismatch is preserved and diagnosed.

The child retains caller case and returned result throughout the post-call
observations. Existing retained_payload traverses public records, containers,
instance attributes and slots, counts each reachable ndarray backing once,
records array paths/shapes/dtypes/visible bytes, estimates Python metadata and
fails unsupported external backing owners. Full mode intentionally retains its
complete bands/estimator overlaps/events/per-time records/transfer graph.
Summary retains its approved final scientific arrays and compact projections,
with discarded diagnostic arrays represented by identities where contracted.
Do not claim equality of those two graph payloads, discard full records or infer
freed allocator/native pages from Python ownership. No predetermined payload
byte count, native peak improvement or performance target is imposed here.

Expected successful observations remain process0, child
finite_observation_pending_qualification, runner
complete_child_observed_pending_scientific_qualification, terminal0, no ownership/
material/postflight/cleanup gap. Snapshot self-high-waters at their actual three
pre-JSON points, sampled current RSS, terminal direct-child wait4 and call time
keep distinct meanings. Same four records supply new binding/PID/session/exec/
wait/FD/native/finite/value/retention evidence; no duplicate workflows for tables.
Failures are retained, not silently replaced. ROOT admission/representation and
physical headroom remain separate; no256 or core24/total60 release follows.
