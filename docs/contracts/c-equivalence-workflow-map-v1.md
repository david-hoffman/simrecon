# CE07: pinned caller map and complete workflow scenario inventory

**Version 1.0. Proposed source-derived map. No execution or acceptance claim.**

This is the normative companion to the [workflow contract](c-equivalence-workflow-v1.md).
Public expectations are source-derived mathematics and explicit decoded-value
declarations. Existing CE02–CE06 accepted equations are incorporated by exact
section references; NEW composition choices are expanded here and in that
contract. A fresh independent complete source-contract review must assess both
documents before blind A. Earlier proposed labels in accepted stage documents
do not undo the completed CE06 baseline.

## 1. Baseline, content pins and static inspection limits

Input baseline: commit `00ac7697231cee022dc40a1ecf2301bbb92a6490`, tree
`f687f0589ab7ce41f5cf3ec51196845cc5f75ebf`, branch
`codex/c-equivalence-workflow`. The author observed a clean tracked checkout
before authoring. No Git mutation, product/test read, retained executable output,
old lesson/history read, role launch or delegation supplies this map.

All paths in the next table are relative to the retained SIMrecon_svn root.
SHA-256 and byte counts were independently recomputed with standard-library
byte reads, without importing/building/executing retained scientific material.
The known CE06 source-manifest.json SHA-256 was verified as
`0a78491837d4409df60a16d6290bde5ceed8bd7f274aa1f788492a001a91b043`.
All ten files matched that manifest exactly. `SVN307` is a label, not a content
identity or proof of the external binary's build inputs.

| Alias | Retained source | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| B | mainfile.c | 49548 | b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8 |
| S | small_math_funcs.c | 25520 | a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e |
| H | helpers.c | 29024 | b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206 |
| R | sirecon.c | 107235 | 3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567 |
| RH | sirecon.h | 13139 | f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629 |
| M | Makefile | 1920 | 1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4 |
| F2 | usr_local/include/sfftw.h | 12408 | 72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138 |
| RF2 | usr_local/include/srfftw.h | 3771 | d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a |
| F3 | usr_local/include/fftw3.h | 17900 | 8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d |
| D | drift_n_phasestep.c | 22186 | 13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2 |
| IH | IVE/win64/INCLUDE/IMInclude.h | 320 | 3deb02c4b654b47efca25106ae94edea573a95ff3af409cf8e163ed3eafd56fd |
| IP | IVE/win64/INCLUDE/IM.h | 6162 | 585e1a46478bac6ec2af8c21d05bc293ed7e8b18e931983899e882dd14ecc65f |
| IC | IVE/win64/INCLUDE/IWApiConstants.h | 9863 | 3c0d20eb9510a74b5e6dde29e6ee237d8be1a1b72311c340f7c2b8a2b13355bb |
| II | IVE/win64/INCLUDE/kernel/IKInterleave.h | 1270 | 23add743544935c939c8169487d0a9d6e4cff14a72d068c18279e59c9af615ba |

IH/IP/IC/II are the ONLY extra source files read beyond the ten-file manifest.
They were read to resolve the missing header/API/sequence declarations, not to
assert that a Windows include tree was the effective historical macOS/Linux
include tree. Other retained filenames were listed without reading their
contents. CE06's separately pinned alternate tools are described ONLY through
its accepted public ledger, not re-executed or promoted to this reference.
Hashing all bytes is not a claim that every helper branch was newly audited;
the incorporated accepted stage maps retain their own proof limits.

M:55–69 links sirecon from R,D,S,H with FFTW3 single precision and external
IVE/LAPACK; radialft links B with FFTW2. M:1–54 resolves IVE include/lib paths
from the environment and platform. It does not select the alternative TIFF
macro. F3:376–377 fixes forward -1/backward +1; F2:58 and RF2:37–38 bind the
radialft transform direction. R and B include IH's public IM API route; exact
external library resolution remains unknown. IC:63–72 declares float2,
complex4 and unsigned16 mode6, IC:129–160 the native header struct,
IC:277–279 sequence codes. IP:79,93–95,120,133 exposes header rewrite,
extended-header query, positioning and section-read prototypes. II:15–44
specifies conversion input domains/status, not its conversion implementation.
These facts qualify explicit declarations, not a complete historical binary
decoder, native ABI, file-library implementation or runtime result.

## 2. Exact incorporated equations and preserved domains

The following public sections are part of the CE07 mathematical packet, without
reprinting their complete accepted equations or reopening their baselines:

| Equation group | Exact normative section and CE07 obligation |
| --- | --- |
| Camera/maps/sentinel/alpha/edges/sums/FFTs/separation/noise | [CE02 Complete selected operation order](c-equivalence-preprocessing-v1.md#complete-selected-operation-order) and [Selected phase matrices and scalar noise](c-equivalence-preprocessing-v1.md#selected-phase-matrices-and-scalar-noise); CE06 supersedes only its explicitly extended modes |
| Empirical bead correction/center/sphere/radial repairs/scale/combination | [CE03 Preparation operation map](c-equivalence-optical-transfer-v1.md#preparation-operation-map), modified ONLY by [CE06 section8](c-equivalence-acquisition-modes-v1.md#8-safe-rectangular-and-z1-empirical-radialft-preparation) |
| Transfer sampling/actual stencils/reflection/wrap | [CE03 Sampling operation map and actual stencils](c-equivalence-optical-transfer-v1.md#sampling-operation-map-and-actual-stencils) |
| Native weights/cutoffs/masks/taper | [CE04 Support, weights and taper](c-equivalence-known-parameters-v1.md#support-weights-and-taper), [Literal native traversal](c-equivalence-known-parameters-v1.md#literal-native-traversal-conjugate-partners-and-odd-height-quirk), plus [CE06 section9](c-equivalence-acquisition-modes-v1.md#9-known-reconstruction-dimensions-filter-variants-zoom-and-taper) |
| Embedding/normalization/phase/sign/output | [CE04 Zero padding, inverse scale and real assembly](c-equivalence-known-parameters-v1.md#zero-padding-inverse-scale-and-real-assembly), CE06 sections9.1/9.2 for precise geometry and dimensional/fractional zoom |
| Overlap/regression/coarse/refinement/time/floors/phases | [CE05 Exact overlaps](c-equivalence-carrier-modulation-v1.md#exact-overlaps-and-sampling-short-circuit), [Regression](c-equivalence-carrier-modulation-v1.md#regression-objective-and-defined-helper-domain), [Coarse search](c-equivalence-carrier-modulation-v1.md#coarse-carrier-search), [Literal refinement](c-equivalence-carrier-modulation-v1.md#literal-angle-then-magnitude-refinement), [Time policy](c-equivalence-carrier-modulation-v1.md#time-policy-known-carriers-and-caller-modulation-adjustments) |
| Off/drift/phase/clocks/true2D/provenance | [CE06 sections3–7](c-equivalence-acquisition-modes-v1.md#3-exact-preparation-and-off-exposure-sequence), including literal plane0, true cubic, alias mutation and thirteen-plus-two settings; active estimator is D, not retired _drift |
| Numerical domains/failures/representation | Each prior public error section and [CE06 section10](c-equivalence-acquisition-modes-v1.md#10-validation-representation-and-operation-time-failures); no new stage validation/dtype relaxation |
| Finite precision and independent observer | [CE06 section12](c-equivalence-acquisition-modes-v1.md#12-independent-numerical-obligations-and-bounds-before-implementation), plus CE07 section9 conditional composition bounds |

All current accepted CE06 ledger mode dispositions M01–M43 remain binding.
Each selected finite CE06 mode is routable through CE07's option whitelist.
Historical original-square/standalone CE02–05 domains do not receive implicit
new dtype repairs or new source tuples. Computed empirical complex128 and raw
declared complex64-exact samples remain distinct domains. Ten-file acquisition
provenance is not six-file estimator provenance.

## 3. Equation and caller map

Source ranges are inclusive and refer to the exact hash aliases in section1.
Every row lists the public operation, input/output, signs/units/origins/scales,
support/Nyquist/finite rules and an independent proof obligation. CE07-W numbers
are operation-map IDs, not additional tests or a scenario quota.

| Map ID / exact caller source | Mapping and public operation | Independent proof / discriminating wrong result |
| --- | --- | --- |
| W01; R:122–205; H:658–687; IP:120–133; IC:129–160 | Neutral source -> explicitly decoded specimen. R uses header.ylen/zlen as dxy/dz, not a modern cell-length conversion; wave slots supply caller wavelength only after a declared role. CE07 requires explicit equal x/y pitch and optics. Camera pixels are float-decoded; no inferred phases/channel roles. Public read/declare_acquisition -> reconstruct_workflow. | Independently label nonsquare per-coordinate pixels in source bytes; actual public read/declaration preserves every selected value and unsigned >32767. Missing declarations error. Arbitrary opaque extension bytes supply no scientific metadata. |
| W02; R:207–215,599–603; IP:79; IC:277–279 | Literal b2D multiplies T by Zstack, sets Z1, calls IMAlZWT with ZTW. No data permutation appears. CE07 literal2D calls accepted reinterpret helper; explicit physical stream map from section5, new direction/time labels. External rewrite/seek remains unqualified. | For D2,Zstack2, phase groups (d0z0,d0z1,d1z0,d1z1), new q0 contains first TWO groups; z-major q0 instead d0z0,d1z0. Distinct labels through FINAL image, off alignment and T_eff schedules; no nominal-plane transpose. |
| W03; R:278–307; H:747–785,799–814 | Transfer dimensions depend on effective Z and radial flag. 3D radial columns K,rows R; 2D radial columns R,row1; full3D K=floor(S/O) axial blocks, consume O*K sections and report the trailing remainder. decoded-section value binding section3.3; complete accepted values bypass this file representation conversion. Units cycles/um, no normalization. | Hand-enumerate unequal complex cells and section maps; exact order availability and K. A K1 transfer with Z>=2 specimen remains 3D. Full3D S7/O3 consumes ((0,1),(2,3),(4,5)), unused(6,); divisible S6/O3 has no remainder. K0 rejects because no axial sample/stencil can exist, not because of divisibility. |
| W04; H:791–814 | For radial OR Z1 loader, order m reads section m if S>m, otherwise copies order0. Full3D reads floor(S/O) sections per order, no order duplication; its trailing S-O*K sections remain unread and are reported. O3/S2 -> (0,1,0). Public decoded adapter only. | Available order1 differs from order0 and missing order2 duplicates0; distinguish repeating last available and all-order0. Complete O2 table for required O3 rejects instead of duplicating; empirical insufficient orders likewise. |
| W05; B:140–151,192–340,1007–1037; R:285–307 | Separate radialft preparation -> combined transfer, then sirecon consumes table. CE07 raw calibration calls prepare_bead_otf once; exact B order and CE03/06 equations. P_b normalization differs from specimen; dkr=1/(Y_b*dxy_b), dkz=1/(Z_b*dz_b). Direct consumed values retain complex128 and metadata, including Z_b1. | Independently sum bead correction/edge/center/DFT/sphere/radial/repair/scale/angle to table and FINAL specimen image; non-complex64-exact coefficient survives. No arbitrary normalized PSF or old physical optimizer produces the expectation. |
| W06; B:603–627,705–866; R:1051–1096; D:109 | Empirical X_b8/Y_b10 padding writes are finite; B horizontal subtraction uses Y_b-1-k, not X_b-1-k. Specimen/prepass fixed10 remains X,Y>=10. Accepted prepare_bead_otf vs prepare_acquisition_bands keep distinct geometry. | X8/Y10 positive and X8/Y8, X6/Y10, X8/Y11 distinct address rejections; rectangular finite mode through consumed transfer. Do not replace one bound with the other's. |
| W07; R:316–327; H:822–854 | Camera file meaning: first background then slope, matching X/Y. CE07 accepts decoded background/slope with no new camera estimator or file parser. No correction -> scalar background, slope1. | Independent signed/zero slope counts and sentinel, same correction into real image. Dividing by slope instead of multiplying differs. Extra file metadata never selects a calibration. |
| W08 NEW; R:278–283,388–417 | norders_in=P//2+1; resolved output O separate. Guess b=1/Ls for Z1 else1/(Ls*(norders_in-1)); theta supplied angles or start+d*(+/-pi/D). Public workflow passes this fundamental vector to actual estimate_parameters. | P5/O2 searchFalse uses divisor2; P7/O3 divisor3; true2D divisor1. Separate math from O-1 and uniform direction-angle assumptions, compare recorded guesses AND final known-fit image. |
| W09; R:581–595,730–742; D:584–619 | Steps beat supplied list; drift-linked design overrides both when within+adjust. Link kguess=(cos(start+d*delta),sin(...))/Ls, without supplied k0angles or 3D divisor; positive 2*pi*dxy*drift dot kguess. CE07 explicit actual phase_policy, all arrays validated, used rank checked. | Unequal angle declarations distinguish initialization from linked phases. Irregular full-rank and uniform-valued supplied lists yield accepted distinct noise/scale. Steps D>3 is a source allocation limit, arbitrary-D lists remain positive. |
| W10; R:224–270,534–563,684–737; RH:97–99; D:260–326,584–619 | Explicit clocks/phases bind decoded exposure stream. CE07 requires header_timestamp_unit with supplied clocks, preserves its exact text in the final workflow resolved_settings key, and performs no numeric conversion; None clocks require None label. Source supplies no timestamp unit. Cubic row j units are detector-pixels/(declared-clock-unit**j), fixed B0 pixels. No CE06 stage/source schema changes. Source phase header converts degrees to radians; CE07 accepts radians only. Actual fixed-intercept cubic, timestamp alias/global-prefix mutation, first metadata block across times. No dose/acquisition drift fit. | Independent polynomial coefficients/evaluations and linked phases through raw-to-image; unfit/no-adjust2D no clock positive. Fitted-with-phase-flag-off, missing phaseAbs and rank/underallocation reject distinctly. Supplied/missing/invalid/blank/without-data unit-label controls follow section5/10; relabeling numeric clocks leaves values/fits unchanged while returned label changes. |
| W11; R:488–508 NEW time binding | Single selected-channel w_t=w_initial+(t+1)*incr/T_eff before first time. Full historical C loops t then wave and mutates global w each wave; CE07 expressly one-channel independent state. | T_eff2 (0.2,0.2 increment)->(0.3,0.4); literal stack effective T used. No endpoint linspace or one-time double increment. Explicit selection from multi-channel values matches standalone selected data, no shared-wave parity claim. |
| W12; R:511–572; D:10–209 | Active between prepass before ordinary camera loading/fitting. Background-only, middle subz=max(floor(Z/2),1), phase average/X/Y/Z, fixed10, cross conj(ref)*moving, power1/4, squared highpass, strict UNCLAMPED optical radius, unused axial cutoff still calculated, abs real peak/periodic parabola. Fast drift exclusions from ledger. | Independent shifted raw samples, first-off bug, fixed10 vs requested edge0, absolute negative peak and first-strict ties. actual finite corrections affect later fit/image; generic ramp-only test insufficient. |
| W13; R:599–666; H:658–687; R:1051–1157 | Camera sentinel at exact corner -1, persistent maps; off e ascending then on, alpha=1/(XYZ_eff L²AD); carried previous ON extra offset for off; sum not average, edge on SUM, off equalization only N>1; lateral forward - exponent first-sample origin. | Independent raw corrected frames with unequal sums/sentinel and two times; first off carries0 then preceding on offset. Slope sign and sum anchors expose wrong order. No wrapper second preparation changes outputs. |
| W14; R:672–746; D:374–582; S:85–229 | Within2D reference on0+off0, power1/2 correlation; actual optional cubic; identical positive ramp on on/off before separation. Phase separation leaves x Nyquist raw slot. Fourier combine plus0/minus side, integer cutoff, repeatedly plane0, no noise update. | Raw on/off asymmetry, per-phase drift, selected source statistics/weights, multiple z with plane0 changed twice. Compare bands, last-z noise and final actual fit/image, not only identities. |
| W15; R:753–755,778–785; D:213–255 | Axial negative forward sum only if Z>1, then between correction on on quadratures d>0 only when requested, positive k dot displacement at first-sample origin. Off bands do not receive axial FFT/correction. | Independent finite z transforms and positive ramp including positive Nyquist; within-only differs from both-flags; full prepared bands consumed by estimator without replay. |
| W16; R:787–858,1286–1747,1839–1999; S:285–375 | Actual CE05 finite estimator: 3D pair02/higher threshold5, 2D pair01/threshold1; strict masks/thresholds; inverse overlap + sign, coarse - sign; refinement remakes at entry then freezes; literal alias old_k0*dk and stale angle bracket. Outputs actual carriers/modulation, never reverse/combined as filter gain. | Finite-sum ordered trace and known-parameter controls before search. Initial/subsequent ties, finite search outcomes and permitted weak unequal-energy inputs. Image alone with broad tolerance cannot excuse a different search path. |
| W17; R:778–781,803–849 NEW consumption | SearchFalse uses source guesses and actually fits all (0,b); reused t>0 uses retained time0 carrier and FRESH (0,b) fits at current bands, no search. Unreachable nested fallback in search block is not an alternative fit route. | Same time0 carrier and changed current modulation, with current final image discriminating time0 gain replay; search-all starts at declared guesses. No supplied true-modulation seam in workflow. |
| W18; R:852–882 | Both 2D paths multiply factor[b] by UPDATED factor[b-1] ascending before floors then phase replacement. 3D no products. Last-z scalar variance per t,d retained. | Independently chosen direct known factors2,3,5 ->2,6,30 before floors; contrast 3D/adjacent-fit errors. Bound product error before native filter. |
| W19 NEW; R:915–967; CE05 public composition and CE06 section7 | Slice actual AcquisitionBands to T1 preserving alpha independent of T, used arrays/time labels/metadata. Pass actual estimate[t] and same transfer to reconstruct_known with precomputed w_t/increment0. No fit or preprocess replay. Batch stage calls preserve dependency recurrences; no filtering feedback into preparation/estimation. | Independently compute two different times through full workflow; inspect actual complete stage records and output, not call counts alone. One-time known controls are supplemental cross-check, not sole oracle. |
| W20; R:938–967,2005–2322; S:381–483,612–730 | Native filter includes self r<=R, other r<R without other axial cutoff; g inverse variance and ordered suppression/damping/omit, conj(H),conj(a),w², taper after quotient; literal odd-Y/Nyquist. CE06 no-overlap/power/precise flags consumed with their finite domains. | Independent weighted powers and finite bands, support equality/noninteger carrier, asymmetric complex table, native-before-relocation counterexample. Unit term w0.5->0.8 and g0.1,w1->1/11 supplement whole image. |
| W21; R:919–936,2334–2491 | L>=1 safe integral LX/LY, source alpha L², positive signed Nyquist lift, full zero padding; unnormalized + inverse, real center plus2*Re(side exp(+2*pi*i*explode*m*k dot centered_r)). Z1 uses only 2D inverse plane0 even A>1. | Independent full finite sums and centered physical labels. Fractional L1.5 and anisotropic dxy/dz, negative image samples, A2 true2D zero later planes. No gain fit, interpolation-first quotient or plane replication. |
| W22 NEW; R:310–327,970–998 | Pure result preserves accepted image scale and source identities. Output x/y pitch dxy/L, z dz/A, centered labels but inverse unshifted; header x/y/z lengths are not a reason for fftshift. C float output precision is not a bitwise target. No file header min/max or command title is a scientific normalizer. | Constant/displaced raw controls and signed Fourier coefficients/coordinates. No final normalization, registration, positivity, header-stat correction or direction/phase extra division. |
| W23 NEW; R:891–913; ledger M30–M34,M39–M42 | Source debug output may exit with status0 before final image; not workflow success. All selected stages must return finite complete result. Unsafe Wiener/padding/model/Bessel/two-objective paths rejected with ledger reason; narrow otherwise-defined excluded cases not falsely called undefined. | All unlisted debug/file/source-flag mapping keys give workflow_config; missing top-level required arguments give TypeError. Only recognized public unavailable/unsafe input/option combinations give workflow_unsupported with exact reason. No zero image/partial time. Existing neutral APIs stay usable; retirement still holds; binary/recovery claim limits distinct from numeric failure. |

## 4. Complete scenario inventory

Each ID below denotes one distinct decision/outcome/guarantee/boundary.
Multiple numerical values in a row are coverage examples, not extra scenarios.
The inherited stage inventories C01–C22, O01–O41 as modified by CE06,
K01–K29, E01–E29 and A01–A54 remain independent obligations; CE07 requires
the corresponding exposed options actually compose, not every primitive
assertion duplicated in a wrapper test. A maps every ID to an observable
public keeper/proof, credible failure, independent expectation, tolerance and
paired positive as relevant. B audits omissions/oracles/legitimate alternatives.
No scenario count limits authoring or expands the authorized feature scope.

| ID | Distinct operation/outcome; required observation or paired control |
| --- | --- |
| WF001 | Public entry/type/result/errors exported under new names; actual signed image returned |
| WF002 | General ordinary D3/P5/O3 raw -> preparation -> finite estimation -> native filter/assembly, with independent whole-image expectation |
| WF003 | General declared true2D Z1 workflow; a K1 transfer alone does not choose it |
| WF004 | Exactly one calibration alternative; neither rejects |
| WF005 | Both calibration alternatives reject without selecting one or doing scientific work |
| WF006 | Raw empirical calibration selected once and its actual transfer/diagnostics consumed in final reconstruction |
| WF007 | Accepted OpticalTransfer selected directly without normalization, fit or symmetry projection |
| WF008 | Precomputed PreparedOtf unwraps directly, retains diagnostics and computed value domain |
| WF009 | Computed non-complex64-exact coefficient and original dkz survive all consumers; direct empirical vs declared-table representability remain different |
| WF010 | Calibration default common scale retains unequal order amplitudes; optional rescale_each/forced pi/conjugate bind exactly once |
| WF011 | Calibration background priority and validation of superseded inputs; no specimen alpha or supplied bead-phase policy |
| WF012 | Tight empirical rectangular/Z1 positive X8/Y10 versus each distinct address failure, original square qualifications retained |
| WF013 | Calibration independent pitches/shape/phase count accepted; table sampler handles frequency conversion without resampling/rebinding |
| WF014 | Calibration known optics must match declared specimen detection optics; incompatible physical declarations reject without refitting |
| WF015 | Complete value transfer requires >=O orders, extras unused; insufficient values reject without missing-order duplication |
| WF016 | Explicit decoded3D radial section order map, missing later order copies0, S>O unused reported |
| WF017 | Explicit decoded2D radial section columns-as-radius and one row; V>1 allocation discrepancy rejects |
| WF018 | Explicit decoded2D full half-x/row-y sections, missing orders duplicate0 |
| WF019 | Explicit decoded3D full K=floor(S/O)>=1, consumes O*K sections with no duplication and reports unused remainder; S7/O3 maps ((0,1),(2,3),(4,5)), unused(6,), S6/O3 unused() |
| WF020 | Explicit decoded2D dkz1 profile versus computed/accepted K1 original positive dkz, neither silently coerced |
| WF021 | Combined-order declaration required; five quadratures/magnitude-phase/invalid encoding cannot masquerade as orders |
| WF022 | Radialft Z1 historical header(K,R) does not silently chain into loader(R,1); actual prepared value chain succeeds |
| WF023 | Complete asymmetric complex radial/full values and all actual zero-weight stencil vertices used; unsafe vertex rejects whole workflow |
| WF024 | Plain canonical ndarray accepted without named-axis inference, general T,D,P,Z,Y,X shapes and unchanged raw representation |
| WF025 | RawAcquisition named-coordinate adaptation preserves exact pixel meaning; source layouts can differ |
| WF026 | Absent time inserts1; true2D absent z inserts1; declared singleton z distinction retained |
| WF027 | Explicit channel selection required for present C, including singleton; exact selected channel, no implicit mix |
| WF028 | Absent-channel/ndarray requires channel_index None; invalid kind/range/bool rejected |
| WF029 | Selected-channel scientific state independent; historical shared multichannel recurrence explicitly unsupported, separate calls not labeled equivalent |
| WF030 | Known neutral x/y sampling must match explicit common dxy; unequal/conflicting pitches reject |
| WF031 | Known z/intensity conflicts reject; absent/unknown neutral metadata does not create guessed values |
| WF032 | Generic wavelengths/nominal commands/ids/opaque extension remain provenance, never scientific calibration or phase selection |
| WF033 | Missing/malformed required optics/count-unit/source-id/phase-policy mapping fields are workflow_config; missing required top-level Python argument is ordinary TypeError, not missing metadata |
| WF034 | Every unlisted mapping key, including nested identity and debug/filename/source-flag spellings, is workflow_config; no reserved vocabulary; every accepted default resolved visibly |
| WF035 | Uniform policy explicitly chosen, no 1/P specimen division; supplied uniform-valued lists remain supplied route |
| WF036 | Step precedence over list with explicit actual-policy assertion, used rank and all supplied-array shape validation |
| WF037 | Steps D<=3 source limit versus arbitrary-D explicit full-rank list positive; no artificial D3 cap |
| WF038 | Within+adjust chooses drift phase design over base; inert adjust without within preserved, phase_policy mismatch rejects |
| WF039 | Actual initial source magnitude uses P//2, not O-1, for reduced-order 3D; true2D no division |
| WF040 | Initial angles override default start+signed pi/D; positive/negative direction step preserved |
| WF041 | Phase-link guess ignores initial angles/3D divisor, with positive dxy*drift linkage; both vectors observable |
| WF042 | SearchFalse still fits modulation from actual bands; no top-level supplied true gains/carriers bypass |
| WF043 | Finite source search consumes actual corrected bands, exact pair/threshold/alias/tie/frozen-overlap procedure |
| WF044 | Reuse time0 carrier refits later modulation from current data; final image exposes incorrect gain replay |
| WF045 | Search-all starts each time at source initial guesses, no preceding-time warm start |
| WF046 | 2D adjacent searched fits vs known/reused (0,b), cumulative products in both before floors/phase; 3D no products |
| WF047 | Floors and fit_all_phases obey accepted zero/equality/positive domains; no new phase guess on zero |
| WF048 | ONE omit_kz0 policy consumed in both estimator/filter; 2D empty overlap fails at actual operation, not silently ignored |
| WF049 | On correction/edges/equalization before transforms, signed nonzero sums/slopes valid; selected zero divisor rejects |
| WF050 | All time/z equalization sharing policies use actual effective labels; unselected flags inert/recorded |
| WF051 | Camera sentinel persistent across t/d/z/p and off/on loads, caller input unchanged; no second prep reset |
| WF052 | Off exposures sum, prior ON offset carry, edge on SUM, N1 no off equalization; all actual data consumed |
| WF053 | Selected off Fourier combination affects literal plane0 repeatedly with accepted integer statistic/sign/noise behavior; skipped selector inert |
| WF054 | Active between prepass from raw/current background, fixed10 and actual fitted displacements, then correct after axial transform |
| WF055 | True2D within raw estimator/on0+off0 reference and optional actual cubic fit before separation, no generic-shift replacement |
| WF056 | 3D actual cubic clocks/intercept and measured between subtraction compose into final image; D<=3 underallocation rejects |
| WF057 | Exact first-block timestamp/phase indexes and alias/mutation across later times; explicit workflow clock-unit label, unchanged numeric clocks, no metadata inference/conversion or t advancement |
| WF058 | Missing/invalid clock/phase DATA/unit is workflow_metadata; recognized null-reference/fitted-phase-flag unsafe routing is workflow_unsupported; unfitted2D no-adjust no-clock positive |
| WF059 | Fast/z-major drift unsafe combinations rejected with exact reason; fastD1 between bypass/qualified within2D positives preserved |
| WF060 | Between prepass N>Y+1 nontermination rejects; first-off-only prepass vs ordinary summed-off finite positive |
| WF061 | No-drift safe small/odd Y and bypass edges remain allowed; specimen/prepass fixed10 X/Y>=10 bound not inherited from bead |
| WF062 | Native plane policy validates mode/Z without flattening or inferring true2D |
| WF063 | Literal2D z-major maps nominal planes with exact on/off/offset/source-direction mapping |
| WF064 | Literal2D direction-major maps contiguous stream groups, discriminating D2/Z2 counterexample through final result |
| WF065 | Literal2D effective T controls time0 reuse/equalize_time/Wiener and Z_eff1 controls alpha; no inherited 3D normalization |
| WF066 | Literal2D metadata stays in physical stream order, phases/directions use new labels; no implicit nominal-angle remap |
| WF067 | One-time known reconstruction slices every used time field/trace consistently, preserves alpha, no raw reprepare/refit |
| WF068 | Actual per-time fitted carriers and final modulation used in native filter, all directions present together |
| WF069 | Wiener preincrements t0, uses T_eff and positive effective sequence; negative increment allowed where all values positive |
| WF070 | No double increment in T1 calls; fixed increment0 accepted original mapping |
| WF071 | Declared Wiener0 or effective w_t<=0 is workflow_config; overflow in deriving otherwise valid values is workflow_operation; no automatic selector/fallback/estimated-noise replacement |
| WF072 | Native self/other cutoff inequalities, scalar noise, complex conjugation and w² distinguish final image from wrong quotient |
| WF073 | Suppression radius/weight, dampen/omit precedence and no-overlap flags preserved at actual native operation |
| WF074 | Cosine/none/power/precise options actually consumed; signed finite exponents and inactive-precise positives vs selected singularities |
| WF075 | Explode only final phase, including zero/negative values; no changed optical support/filter/taper |
| WF076 | Native-filter-before-noninteger-relocation public counterexample, asymmetric complex transfers and signed independent Fourier expectation |
| WF077 | Exact safe fractional L alpha/output spacing/extents, nonintegral/shrinking representation rejects |
| WF078 | Positive Nyquist no split, unseparated raw endpoint and literal odd-Y partial writes retained through image |
| WF079 | Unnormalized backward scale and side factor2, centered phase labels but unshifted array; no extra P/D division or fitted gain |
| WF080 | True2D A>1 only plane0 inverse, later planes zero; true2D dz0 coordinate/axial limits explicit |
| WF081 | Signed output/read-only top arrays, physical um labels/count-unit semantics; no mass/positivity/resolution promise |
| WF082 | Full bands/estimator/calibration/known/layout diagnostics and public WorkflowEvents expose actual consumed state and ordering |
| WF083 | Six-file estimator identity/thirteen-plus-two settings distinct from ten-file bands/workflow; separate CE03 transfer provenance unchanged |
| WF084 | Exact source declarations/decoded section binding, including unused full3D remainder, settings/defaults/limits and final header_timestamp_unit key; no private paths/pointers or added inherited stage fields/provenance keys |
| WF085 | Numerical ArrayIdentity hashes endian-normalized bits plus original shape/dtype, distinguish signed zero/channel/source selection and no quantization |
| WF086 | Input/config/RawAcquisition/strided/read-only arrays preserved; returned top arrays independent, stage writable ownership retained |
| WF087 | Invalid sample kinds/nonfinite/exact-float32 representability/record provenance/source domain reject; neutral bit-preserving reader still accepts its larger domain |
| WF088 | Source signed32/unsigned32/intp array/trace/metadata extents checked without artificial allocation cap; actual allocation failure honest |
| WF089 | Complete section10 single-invalid schema/category audit binds even without precedence for simultaneous errors; numerical solve/correction/transform/calibration/regression/search/filter/backend failures are workflow_operation with context/cause and no partial result |
| WF090 | Later-time/order failure rejects whole workflow, no fallback/zero image/truncated time/result trace |
| WF091 | Actual file read -> declaration -> workflow keeps canonical coordinate identity and explicit source provenance; no default automatic full read |
| WF092 | Missing/unresolved source config, source_changed/I/O failure remain neutral adapter failures before workflow; no guessed header/schema |
| WF093 | Complex OTF/modern input/unqualified original IVE/header routing unsupported with exact reason; explicit decoded supported alternative |
| WF094 | Debug early-exit results never successful final reconstruction; all absent debug/padding/automatic/Bessel/two-objective/model request keys are workflow_config; recognized existing unsafe option combinations retain exact workflow_unsupported reasons, with no new scientific selector |
| WF095 | Old public APIs/modules/solver/optimizer stay retired and ImageJ/neutral source-only output contracts unchanged |
| WF096 | Historical hidden-fit-path public counterexample proves empirical response/current fit/native filter consumed without old executable or truth fitting |
| WF097 | Known controls precede nuisance search, independent algebra/finite sums and conditional tolerances frozen before discrepancies; self-replay alone insufficient |
| WF098 | All scientific finite diagnostics/decision margins observed; missing source/binary/recovery evidence labeled unqualified rather than inferred |
| WF099 | Documentation covers exact entry/types/options/file-value remainder mapping, clock-unit keyword/ordered settings/coefficient units, consistent errors/positive controls, calibration/phase/carrier/scale/limits and general supported examples |
| WF100 | Source review before A, complete A/B checkpoint, exact clean full local/platform evidence and fresh D before stacked-PR readiness; no gate/policy relaxation |
| WF101 | Supplied header_timestamps with explicit nonblank header_timestamp_unit accepted, arbitrary common-unit label domain rather than closed conversion registry |
| WF102 | Supplied timestamps with missing/None unit label gives workflow_metadata even when clocks unused; valid label positive |
| WF103 | Supplied timestamps with nonstring label gives workflow_metadata; string label positive |
| WF104 | Supplied timestamps with empty/whitespace-only label gives workflow_metadata; exact surrounding whitespace around nonblank text preserved |
| WF105 | Label without timestamp data gives workflow_metadata, independently of whether drift needs clocks |
| WF106 | No timestamps and unit None permitted when clocks unselected; no arbitrary clock requirement on unfit/no-adjust2D or no-drift paths |
| WF107 | Selected clock-dependent fit with absent timestamp data gives workflow_metadata; label/opaque metadata cannot supply data; present valid clock+label positive |
| WF108 | No automatic conversion: identical numeric arrays labeled seconds, milliseconds or custom ticks yield identical numerical results/array hashes and different exact returned labels |
| WF109 | Fixed B0 detector pixels and cubic c_j detector-pixels/(declared-clock-unit**j), powers1/2/3 in existing matrix, sample/evaluation/after clocks share label; CE06 tuple/fields/math unchanged |
| WF110 | Full3D decoded S<O yields K0 workflow_representation: zero axial order storage cannot supply finite stencil; adjacent S=O gives K1, and positive remainder case WF019 remains supported |
| WF111 | Exact signature binding: missing required top-level optics or unknown top-level keyword is TypeError, versus optics={} and unknown nested/mapped keys workflow_config; no reserved-name exception |

WF001–WF111 are 111 explicitly enumerated CE07 composition scenarios, not a cap
or test-count requirement. The C/O/K/E/A inventories remain inherited, not
silently counted as examples of WF100. Logical independent proof groups are
selection/adaptation (WF004–WF034), phase/carrier/preparation (WF035–WF061),
layout/time/filter/output (WF062–WF086), and error/compatibility/evidence
(WF087–WF100), with explicit clock/error/remainder-boundary obligations
WF101–WF111. WF001–WF003 establish the public operation. Groups are not separate
tasks/baselines or permission to defer part of CE07.

## 5. Independent proof construction and numerical limits

An independent finite observer begins at declared raw on/off pixels and explicit
camera/clock/phase/calibration declarations. It computes corrected frames,
edges/equalization, explicit finite Fourier sums and separation; calibration
uses its own raw-bead arithmetic and radial cells. Independently enumerate
overlap masks/complex transfer samples/regression and ordered finite decisions.
Then form native weighted coefficients, reflected partners and the full
unnormalized output finite sum with the stated centered assembly phase. Known
controls isolate the filter before nuisance search. Whole-workflow comparisons
observe actual output, not a spy's function-call count or runtime helper replay.

Small controls can use analytic Fourier modes and exact inverse/left-inverse
designs, displaced impulses, distinct off/statistic cells and cubic timestamp
polynomials. Include more than one nontrivial mode/response so a single fitted
gain could not conceal the wrong algorithm. Calibration-derived table controls
include a coefficient not exactly binary32, general rectangular geometry,
nontrivial native support and selected actual parameter fits. Do not select a
favorable exactly representable transfer to avoid direct complex128 consumption.
The accepted CE06 algebraic nonbinary32 H0[1,0]=(17+3*cos(pi/8))/20 is one
coefficient discriminator, not the sole empirical/workflow oracle.

For each fixture/conditional branch, derive representation error and observer
error separately before seeing product discrepancies. A direct n-term sum can
use gamma_n times its absolute term sum plus input/multiplication errors;
FFT backend error needs its own stated bound rather than a copied direct-sum
operation count. Propagate phase/design/cubic conditioning, actual statistic
and fit divisors, taper behavior, w_t² lower bounds where weights nonnegative,
then the full native/output accumulation. Require gaps larger than propagated
error to assert a strict peak/threshold/search decision, or exact constructed
symmetry/tie proofs. Near-boundary sensitivity is a claim limit, not a relaxed
finite procedure. Separate final absolute and relative bounds. No blanket task
epsilon or fixed condition-number/noise floor supplies a new scientific rule.

Sanity checks, in addition to full proofs: P5/O2 3D initialization magnitude
1/(2*linespacing); O3/S2 radial section map(0,1,0); full3D S7/O3 floor blocks((0,1),(2,3),(4,5)) with unused(6,); one-channel T2 schedule
(0.3,0.4) for initial/increment(0.2,0.2); unit native self term w0.5 gives0.8;
g0.1,w1 gives1/11; L1.5,X=Y10 gives15-by15 with pitch dxy/1.5; true2D A2
later output planes zero; cumulative direct2D factors2,3,5 give2,6,30 before
floors. These are algebraic controls, not observed retained-C outputs.

No recovery/resolution, matching historical executable output, realistic noise/
dose claim or physical calibration authenticity is established by a source map
or these controls. CE08 remains separate. Failure evidence is retained and
classified; no seed selection, tolerance tuning, per-result scale/registration,
different objective or dependency/gate/policy change repairs equivalence.

## 6. Source-author handoff and unresolved items

The source-derived decisions in the owned contract are PROPOSED until fresh
complete independent source-contract review. That review must challenge actual
caller order, decoded declarations, inherited domains, legitimate positives,
oracle independence and every inventory row. This author supplies no review
verdict. No essential owner meaning was found missing within this explicit
decoded, selected-channel workflow boundary. A request for historical external
IVE binary file binding, shared multiwave state or active precise2D DC requires
separately resolved meaning/evidence; it is not silently implemented here.

Mandatory runtime evidence remains exact clean local
`make verify PYTHON=.venv/bin/python`, all13 phases, two workers, strict outcomes,
complete statement/branch JSON/HTML/global/package/file/subprocess reports,
pinned reader, wheel/source/RECORD/isolated imports/audit, same-run M25 conversion
increment<=33,554,432 bytes, original Ubuntu24.04/macOS15 qualification, and fresh
D. Percentages remain advisory under approved behavior coverage plus independent
risk review. Nothing in this document supplies that evidence or permission to
skip it. CE07's stacked PR and eventual CE08 handoff stay coordinator-owned.

Requested model/effort gpt-6.1-sol/high; actual serving/billing/effort/tokens/cost
unknown. Human numeric limits not set. This author launched no child roles or
scientific processes and left no background process. Commands were read-only
Git identity/status queries, rg/cat/sed static reads, a standard-library source
hash report, owned document writes and static document checks. Command failures
are reported outside tracked bytes; there is no runtime success inference.
Role-created external evidence directories are source-author-1 and
source-author-1-correction-1 under the coordinator-provided CE07 evidence root;
their source-pin/static/correction reports are durable handoff evidence, kept. No disposable fixture/worktree was created or removed.
The launcher owns final.md and its packet/event/process/completion paths; this
role does not write them. Output hashes belong in the external handoff, not
self-referential tracked documents.
