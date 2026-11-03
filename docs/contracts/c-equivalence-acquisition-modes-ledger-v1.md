# CE06: complete acquisition source-mode ledger

**Version 1.0. Source-mode definitions, safety boundaries and proof limits.**

This ledger defines source capability and safety boundaries for the
[proposed acquisition contract](c-equivalence-acquisition-modes-v1.md).
It covers the ordinary non-TIFF sirecon caller, its linked drift/math/helpers,
and the selected ordinary radialft bead caller. It distinguishes a called
capability from a mathematical helper and from an alternative executable.

## Authority, evidence and status keys

CE06 covers the remaining defined supported acquisition branches in one
integrated candidate and stacked pull request on completed CE05 head
a87f3ffc8c95877e8fbb159a44b6ab7527a879b3, tree
1375fb4ee38004cfdd9dcfd2889a7491ec406c80. Capability/proof status below inherits
the completed-baseline declaration and accepted public contracts. The source
ledger supplies no new runtime, test or binary qualification.

- **P**: implemented/proved on that declared accepted baseline, within the
  cited CE02–CE05 contract only. This is not a new independent implementation verdict.
- **D**: source-defined finite subdomain, not yet implemented/proved under an
  accepted public contract. “Selected” assigns remaining CE06 work; “outside”
  identifies an alternative tool or later file/workflow scope.
- **U**: undefined, unsafe, aborting or without a finite terminating reference
  on the named subdomain. No numerical expectation may be fabricated there.
  A mode can have both D and U subdomains.

References use SIMrecon_svn/-relative filenames and inclusive source line
ranges. The external source-binding manifest is source-manifest.json;
its SHA-256 is
0a78491837d4409df60a16d6290bde5ceed8bd7f274aa1f788492a001a91b043.
Its ten source files and the two extra identities below bind the reference.
SVN307 is a label; actual bytes, not the label, define the source target.

## Content identities and build/caller routing

| Retained file | Bytes | SHA-256 |
| --- | ---: | --- |
| mainfile.c | 49548 | b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8 |
| small_math_funcs.c | 25520 | a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e |
| helpers.c | 29024 | b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206 |
| sirecon.c | 107235 | 3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567 |
| sirecon.h | 13139 | f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629 |
| Makefile | 1920 | 1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4 |
| usr_local/include/sfftw.h | 12408 | 72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138 |
| usr_local/include/srfftw.h | 3771 | d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a |
| usr_local/include/fftw3.h | 17900 | 8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d |
| drift_n_phasestep.c | 22186 | 13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2 |
| radialft2d_Hesper.c — extra, statically inspected | 10542 | 57fb0be2b39efd556cd0e014d7144d1d525d7f6718bd46551eae48f4e70900a9 |
| wiener2d.c — extra, hashed only | 15662 | 1b041298f0c3f677880ca2ccf1c0cbf10bacc0b8727892493d4273deaf0e660a |

Makefile:55–69 links sirecon from sirecon.o, drift_n_phasestep.o,
small_math_funcs.o and helpers.o, using FFTW3 single precision and external
image/LAPACK libraries. radialft is mainfile.o with FFTW2. otf2d is a different
target, radialft2d_Hesper.o plus tiffhandle.o; wiener2d is another target.
Neither otf2d nor wiener2d is linked into sirecon. The pinned retained root
lacks tiffhandle.c/.h; effective historical external include/library resolution
remains unknown. These findings
are static routing, not proof that any historical binary built or ran.

Ordinary sirecon does not define __SIRECON_USE_TIFF__; its image read route is
the non-TIFF branch (sirecon.c:122–205; helpers.c:747–814). The alternate TIFF
conditional is not qualified: header variables/routing in main remain mixed,
and helper code at helpers.c:690–744 contains unresolved alternate calls.
No alternative estimator is selected by merely finding it in an archive.

## Preparation, dimensions and transfer capability

| ID | Branch and exact source | Baseline / remaining disposition |
| --- | --- | --- |
| M01 | Ordinary on-exposure 3D; sirecon.c:574–666,740–755; helpers.c:658–687 | **P**, CE02 C01–C22: camera sentinel/state, slope/background/extra offset, alpha, all safe edges, sums, lateral transform, native Nyquist exception, axial transform. Useful D=3/P=5/O=3 stays required. |
| M02 | Uniform versus supplied full-rank phase list; sirecon.c:581–595,1155–1274 | **P**, CE02 C12–C16, including square inverse, unweighted left inverse, scalar noise, reduced order/even P when Q<=P. A uniform-valued supplied list remains the supplied policy. |
| M03 | Per-direction step shorthand; helpers.c:180–195; sirecon.c:581–590 | **D selected**: phases p*step[d], supplied-matrix policy. Steps take precedence over a list. **U** CLI step table beyond D=3: allocation/read is exactly three floats. D<=3 is a defined caller subdomain; arbitrary-D explicit lists remain permitted. |
| M04 | Equalization off/on and all four z/time reference-sharing policies; sirecon.c:651–655,1104–1139 | **P**, CE02 C07–C11. Anchor is pre-equalization direction0/phase0, selected t/z; negative nonzero sums permitted. **U** selected zero divisors. Off-image special case is M20. |
| M05 | True 2D specimen, nz=1; sirecon.c:207–215,369–395,753–755,1308–1316,1616–1624,1699–1709,852–854,930–933 | **D selected** end to end, not supplied by a length-one OTF table. No axial forward FFT; initial carrier is 1/line spacing, not divided by nordersIn-1; searched pair (0,1), factor1 threshold, adjacent later searched pairs; known path still (0,b), then cumulative product in both paths. |
| M06 | A stack declared -2D; sirecon.c:207–215,599–603 | **D selected**, literal section regrouping into Zstack effective times, without data permutation. Nominal per-plane composition requires a z-major physical stream (or D=1/Zstack=1 degeneracy). An ordinary direction-major stream groups original (d,z) differently; preserve that regrouping with the contract layout helper, not a silent transpose. Flags, phases, time0 reuse and equalize-time apply to NEW effective time/direction labels. External IMAlZWT/IMPosnZWT binding stays CE07. |
| M07 | Odd Y including Y=1; sirecon.c:2103–2124,2294–2319 | **P** CE04 K16 for 3D: omitted row and partial reflected zero writes; Y1 loops empty. **D selected** same literal 2D behavior. Odd X conflicts with nx+2 real-transform storage; **U**. |
| M08 | Radial 3D table, full nonradial 3D table; helpers.c:767–809; sampler small_math_funcs.c:396–483 | **P** CE03 O24–O30 and CE04/05 composition. Complex radial imaginary-odd values, full all-axis reflection and actual zero-weight vertices remain binding. |
| M09 | Radial 2D table K=1; full 2D table K=1, Ytable>=1; helpers.c:757–765,801–805 | **P** declaration/sampler primitive, **D selected** specimen composition. Source FILE loader sets dkzotf=1, radial nx=R/ny ignored or full x-half/ny=Ytable. Actual prepared value records retain original positive dkz and complex128 samples and are directly consumed; no forced dkz1/redeclaration. A K1 primitive is not M05 proof. |
| M10 | Too few radial/2D file orders; helpers.c:799–805 | **D outside CE06 runtime**, CE07 resolved file adapter: available sections used in order, every absent later order duplicates order0. CE03 complete declared tables never silently duplicate. Full 3D instead divides total sections by O and reads complete stacks. Malformed/incomplete files have no invented values. |
| M11 | Fast versus ordinary exposure order; sirecon.c:599–603; drift main:515–517,528–563,675–708 | **D**, pure decoded-array equivalence selected with file routing CE07. Without drift they differ only in section lookup. **U** fast drift with D>1: skipped estimator leaves drift_bt_dirs[1..D-1] unreadied yet read/printed. Fast D1 BETWEEN-ONLY is a defined zero-displacement bypass. **U** fast WITHIN-3D for every D, including1: allocated driftlist is never filled by the empty fast branch, then consumed by fixdrift_2D. Fast within-2D D1 instead runs its own estimator; it is qualified only by that actual path and M15/M17/M18, never by the between-only bypass. |
| M12 | Multichannel wave loop; sirecon.c:488–492,508,758–759,778–811 | **D outside selected single-channel CE06**: source global Wiener increments once per wave/time, carrier time0 state is not independently stored per wave, automatic branch uses wave[0]. No promise of independent per-channel behavior. CE07 must bind explicitly or compose separate declared calls without claiming literal shared-state parity. |

## Drift and linked phase modes: actual caller, not an unused primitive

| ID | Branch and exact source | Baseline / remaining disposition |
| --- | --- | --- |
| M13 | Between-direction estimator; sirecon.c:511–525 calls drift_n_phasestep.c:10–209 | **D selected**, ordinary source active estimator. Uses middle max(floor(Z/2),1) raw sections, phase average divided by X*Y*Z, background only, fixed10 edges, unnormalized real FFT, conj(reference)*moving, magnitude power1/4, optional squared Gaussian high-pass, strict optical-radius mask (not Nyquist clamp), real inverse, absolute peak and periodic parabola. Axial optical cutoff is calculated but UNUSED. **U** unsafe fixed10 addresses: X<10 or Y<10 reaches negative/out-of-allocation offsets even with zero edge differences (call:109; sirecon.c:1056–1069). X=Y=10 is address-safe with overlapping strips; no 20-pixel minimum. No-drift Y1 remains M07; the fast D1 skipped prepass does not evaluate these accesses. |
| M14 | Between-direction Fourier correction; sirecon.c:783–785; drift_n_phasestep.c:213–255 | **D selected** after separation/axial FFT, before parameter fitting. All retained quadratures multiply exp(+2*pi*i*(dx*kx/X+dy*ky/Y+dz*kz/Z)), displacement in detector pixels/sections, positive native Nyquist labels. Direction0 zero. No generic shift alone discharges M13. |
| M15 | Within-exposure 2D drift; sirecon.c:672–708; drift_n_phasestep.c:432–582 | **D selected** with actual default reference type0 AND off-images: phase0 on+off reference in Fourier space; power1/2 cross spectrum, same high-pass/absolute-peak procedure. **U** type0 without off-images: calcRefImage returns0 without writing malloc reference, ignored by main. **U** type1: += into uninitialized reference (also null off-image dereference without off); types2/3 write nothing. Those types are not parser-selectable (helpers defaults:553). |
| M16 | Within-direction 3D lateral curve; sirecon.c:534–563; drift_n_phasestep.c:260–326 | **D selected** ordinary order, D>=4, usable timestamp metadata and full-rank cubic-with-fixed-intercept fit. Fitted x/y evaluated for each exposure, subtract measured direction drift for d>0. **U** D<=3: nPoints-1 rows/leading dimension/RHS storage cannot hold 3 unknown coefficients per RHS; D=3 LDB=2<3 and evaluation reads coefficients out of allocated RHS. Not a quadratic fit. **U** no timestamp allocation when bFixPhaseStep false; no safe automatic timestamps source there. |
| M17 | Optional fit of measured 2D exposure drift; sirecon.c:224–270,684–697; drift_n_phasestep.c:275–326 | **D selected** P>=4, full-rank cubic, bFixPhaseStep enabled and usable timestamp/phase metadata. **U** fit enabled with phase flag disabled: timestamps is never allocated, then read at sirecon.c:687–689 before fitting. The unfit branch with phase correction disabled requires NO timestamps and permits smaller P, subject to the actual reference/estimator prerequisites. In fit, timestamp input/evaluation alias and in-place mutation matter. Only x/y are assigned/consumed; no defined fitted z is invented. Ignored source failure status is not numeric success. |
| M18 | Exposure translation and linked phase; sirecon.c:705–737; drift_n_phasestep.c:374–428,584–619 | **D selected** positive exp(+2*pi*i*k dot displacement), before separation, and phases base+2*pi*dxy*drift dot kguess. kguess HERE is (cos(angle0+d*delta),sin(...))/linespacing; it ignores supplied k0angles and 3D carrier division. 2D base is recorded absolute phase of FIRST off exposure (or on if none); 3D base is p*2*pi/P. **U** absent phaseAbs even in 3D: unconditional printf at 615–616 dereferences it. Metadata fallback at sirecon.c:232–242 allocates timestamps alone, so cannot qualify linked phases. |
| M19 | Flag combinations; sirecon.c:511–572,672–737,783–785 | **D selected** between-only, within-only, both, raw/fitted 2D drift, linked phases on/off WHERE defined. “Fix phase” without within correction does no phase adjustment. Ordinary 3D within and fitted 2D within require the phase flag for timestamp allocation; unfit 2D without linked phases needs no clock. Fast D1 between-only is a zero bypass, fast within-3D is unsafe even D1, and fast within-2D D1 must qualify its own active estimator. No-off 2D within is unsafe. Metadata accesses use the first exposure block across later times, not a t advance. |

## Off exposures, filtering, zoom and special paths

| ID | Branch and exact source | Baseline / remaining disposition |
| --- | --- | --- |
| M20 | Optional N off-images before each on-image; sirecon.c:605–655,661–662,742–746 | **D selected** load/correct/sum, never average; edge AFTER sum; equalize off only N>1; sentinel state shared; extra background for off is carried from preceding on exposure, initial0. With N=1 off equalization is skipped even when on equalization is enabled. |
| M21 | Off input in between-dir drift; drift_n_phasestep.c:83–106 | **D selected** 1<=N<=Y+1: reused loop variable i means only FIRST off image is read once; then zsec advances N and reads on. **U** N>Y+1: inner y loop leaves i=Y, outer increment sets Y+1 repeatedly, so outer loop cannot terminate. Do not repair by accumulating all off-images in this estimator. Ordinary preparation still sums all N. |
| M22 | Selected off/on Fourier combination; sirecon.c:743–746 calls small_math_funcs.c:115–229 | **D selected** finite nonempty statistics/positive noise. Cutoff is converted to int; kx,ky are integers truncated after frequency scaling. Side quadratures subtract off; zero order adds it; estimated signal clamps negatives to0, both-zero becomes1; weights are signal/noise normalized by their SUM. Noise factors remain unchanged (updates commented). Source passes base pointer on every z iteration: first plane is repeatedly combined; current later planes only supply separation before later axial transform. No z offset is passed. Unused real-space combine_exp_off at 233–276 is **D outside**, not called. |
| M23 | Integer zoom L,A; sirecon.c:432,917–957,2334–2491 | **P**, CE02 scale and CE04 assembly with positive native Nyquist lift. **D selected** 2D: when Z=1 source creates a 2D backward plan even with A>1; only first output plane is transformed, remaining zero planes stay zero. A full 3D inverse that repeats the plane changes the source. |
| M24 | Fractional lateral zoom; helpers.c:219–224; sirecon.c:919–936,2342–2401,2427–2458 | **D selected** source-float L>=1 with LX and LY exactly integral and representable; no alias/race in embedding. **U** nonintegral lateral extents: lookup fill uses floor extents but final loops use i<L*Y,j<L*X (ceiling count), causing uninitialized lookup/access mismatch. Shrinking grids have colliding parallel writes or invalid lifts, not a qualified deterministic decimator. No arbitrary “integer only” rejection of safe L=3/2 on even compatible dimensions. |
| M25 | Normal suppression, order0 damping/omission/kz0, cosine/no taper | **P**, CE04 K03–K19; **D selected** dimensional composition. Singular evaluated c0=0 damping remains **U**; Y1 empty traversal can remain valid. Suppression radius is an outer selection bound; helper radius itself unused (small_math_funcs.c:381–392). |
| M26 | Power taper; sirecon.c:2194–2224; helpers.c:305–311 | **D selected** same rho/clip as cosine, T=(1-rho)^gamma, gamma explicitly finite. Zero base with gamma>0 gives0; gamma0 gives1; negative gamma at zero base is singular and **U** on that operation. No hidden positive-gamma-only rule for finite paths. |
| M27 | Precise angular boundary; sirecon.c:938–941,2209–2213; small_math_funcs.c:612–730 | **D selected** literal finite sector/intersection subdomain, including inactive 3D elliptical/no-taper cases. **U** no matched sector leaves intersection uninitialized; negative discriminant, zero returned limit, nonfinite tan or zero-carrier boundary polar conversion. Active DC queries atan2(0,0): no portable real-arithmetic reference under accepted CE05 convention. Reject there; no radial fallback, arbitrary DC angle or corrected geometry. See proposed contract for complete procedure and the explicit reference decision if active precise-2D at DC is required. |
| M28 | Overlap filter disabled / exploded view; sirecon.c:2157–2160,2349–2350,2389 | **D selected** debug capability: skip other terms unless self order0 AND other signed order0; self term always retained. Explode factor scales only assembly phase, not filtering/support/taper. No reconstruction-quality or increased-resolution claim. |
| M29 | Explicit positive Wiener; helpers.c:364–378; sirecon.c:508,2016 | **P** fixed positive CE04 w; **D selected** time schedule: increment BEFORE first time, w_t=w_initial+(t+1)*increment/T for one wave, all used w_t>0. Source variable updates persist. No endpoint interpolation from w_initial at t=0. |
| M30 | Automatic Wiener; small_math_funcs.c:580–609; sirecon.c:758–759,886–888 | **U excluded**: k loop is c<=k<Z-c, but midfrequency condition needs k<c OR k>Z-c; countMidFrequencies always0 (including empty loop), division0/0 in return. The older estimate_Wiener helper is commented out at sirecon.c:667–670, not a replacement caller estimator. |
| M31 | Axial input padding; sirecon.c:217–220,354,480–483,919–957 | **U excluded** for nz0>nz: bigbuffer allocated using original nz, but plan/move use nz0; padded savedband sections never initialized by a padding fill either. nz0<nz can write beyond savedbands or use negative zoffset. Explicit nz0=nz is a defined no-op; no “safe useful padding” is invented. |
| M32 | Bessel; sirecon.c:833–849,867–878,1426–1439,2046–2053,2069–2077 | **U excluded for O>=2**: highest-order zdistcutoff[O-1] is never initialized, then read in clipping/filtering; acos can fail independently. **D outside selected support**: O1 with search off, fit-all-phases on, safe initial-guess conversion and otherwise defined settings skips all positive-order fits; cutoff entry0 IS assigned and taper selects c[0]. It has no c[1] access in this special filter branch. This narrow no-search O1 path does not qualify the requested multi-order Bessel acquisition, and no Bessel feature is selected. |
| M33 | Two-objective reconstruction; sirecon.c:833–849,867–878,1441–1443,2055–2079 | **U** whenever the parameter workflow reaches makeoverlaps: explicit abort. **D outside selected support**: known-carrier O1, search off, fit-all-phases on and otherwise defined settings skips that loop/call; special cutoff entry0 is initialized (last assignment wins) and taper uses c[0], not c[1]. Safe initial-guess conversion still matters (3D P1 divides by nordersIn-1 at sirecon.c:395). No O1/two-objective feature is selected; the finite narrow path is not mislabeled as an overlap abort. |
| M34 | Model/debug replacement; sirecon.c:762–764,1750–1838 | **U excluded as ordinary main**: k0[direction] passed before initialization at 778–779. This is not an independent acquisition oracle. Save-separated/aligned/overlap flags at 767–771,891–911 are **D outside CE06**, early-exit file diagnostics, CE07 disposition; never a successful final reconstruction. |

## Empirical transfer caller and alternative tools

| ID | Branch and exact source | Baseline / remaining disposition |
| --- | --- | --- |
| M35 | Ordinary square 3D radialft bead route; mainfile.c:76–340 | **P**, CE03 O01–O41: uniform odd phases, all declared backgrounds, fixed10 edge, center, sphere division, radial average, repairs, cleanup, common/per-slot scale, combination/sign and conjugation. |
| M36 | Rectangular bead arrays in same caller; mainfile.c:150–151,603–627,705–866 | **D selected**, preserve horizontal subtraction at y*(X+2)+Y-1-k, not X-1-k; raw FFT uses actual X/Y, but compensation BOTH lateral increments and returned radial increment are 1/(Y*dxy). Radial bin uses unscaled index radius with limit X/2+1. **U** actual out-of-allocation addresses, including last-row high offset if Y>X+2. In-allocation padding/cross-row effects are literal, not automatically errors. |
| M37 | nz=1 in same radialft caller; mainfile.c:142–151,262–265,805–866,1057–1073 | **D selected** finite array preparation; axial transform length1, radial table K1. ifixr can reach outside final radial row; reject actual unsafe requests, no clamp. This tool output header uses nx=K,ny=R (mainfile.c:1007–1037), while sirecon 2D loader expects nx=R: unchanged file chaining is NOT qualified. Value composition directly consumes PreparedOtf.transfer (O,R,1), original positive dkz and all complex128 values, including those not exactly complex64-representable; no quantization/redeclaration/rebinding. |
| M38 | Even bead phases / P1 compensation / unsafe diagnostic | **U**, mainfile.c:346–387 leaves an even-P row uninitialized; 732–733 divides by O-1 for P1 compensation; 521–527 can evaluate zero denominator yc=20 or invalid floor(zc) accesses. Existing CE03 safe domains preserved. |
| M39 | I2M, two-objective bead paths; mainfile.c:226–233,529–571,937–968,332–336 | **D outside selected ordinary single-objective CE06**, not uniformly undefined: finite subdomains exist. I2M includes separate center and unconditional origin fit (default bins0,0 singular). Two-lens cleanup has its own arcs and acos/asin limits. Does not cure M33. No new two-objective reference is commissioned. |
| M40 | Five-quadrature / order0 file output, alternate ACCURATE_PEAK; mainfile.c:259–260,318–330,459–508,1007–1037 | **D outside selected combined-transfer value boundary**: file layouts/diagnostics are CE07 or an explicitly named alternate tool. ACCURATE_PEAK is not enabled by selected Makefile; alternate unwrapped sample accesses can be unsafe. Supplying five quadratures as three orders remains invalid. |
| M41 | Separate otf2d target; radialft2d_Hesper.c:204–350 | **D outside selected empirical caller**: single PSF plane, no phase separation/bead compensation, different background, DC normalization, diametric half-plane radial weighting and origin fit. **U** peak-row20 division at 117–124; invalid fit bins at128–149; radial cutoff above allocated R at341–343; missing TIFF settings; absent tiffhandle source prevents complete alternate build provenance. Not silently substituted for radialft or proof of 2D specimen support. |
| M42 | Separate wiener2d target; Makefile:68–69 | **D outside selected sirecon acquisition/reconstruction**. File hashed to record exposure only; algorithm not used or qualified. No new standalone deconvolution feature follows from this ledger. |

## Axial sampling fallback

| ID | Branch and exact source | Baseline / remaining disposition |
| --- | --- | --- |
| M43 | Nonpositive-dz overlap/filter fallback; sirecon.c:1410–1414,2021–2026; contrast drift_n_phasestep.c:28–34 | **D selected** in 2D at dz=0: use table dkz directly, so kzscale=1; positive dz uses 1/(Z*dz). Source also defines this overlap/filter branch for dz<0, but negative pitch remains **D outside selected physical public support**, not automatically unsafe arithmetic and not an authorized new domain. Existing positive-dz 3D is **P**; neither original 3D nor empirical preparation gains a nonpositive pitch domain. The actual between-direction prepass has NO fallback and dz=0 is undefined there. Fast D1 between-only can skip that prepass; it does not implement a fallback estimator. |

## Compatibility, remaining work and claim limits

All P rows retain their accepted defaults, public signatures/records/errors and
test obligations. A proposed new entry/domain cannot invalidate their inputs,
delete their tests, or lower verification. The remaining selected D rows are
assigned logical obligation groups in ONE integrated acquisition contract,
candidate, review chain and stacked PR; none is treated as already proved.
CE07 keeps file/CLI orchestration, channels and debug output;
CE08 keeps recovery/resolution. U rows require informative rejection, never
numeric comparison with uninitialized data, an infinite loop or a repaired
reference.

Prepared empirical transfer values and declared-table samples keep their
different accepted CE03 domains. Direct PreparedOtf.transfer consumption does
not weaken declare_otf's exact-complex64-representable input requirement.
EstimatedParameters source_revision/reference_sha256 stay the exact CE05
SVN307/six-file estimator identity for both input types. Only AcquisitionBands
results append the exact acquisition_mode and acquisition_reference_sha256
pairs to resolved_settings; the latter preserves the input ten-file tuple
losslessly. The contract fixes all names, value kinds and ordering. Original
PreparedBands result metadata receives no added keys.

There is no blanket C-equivalence, binary agreement or resolution claim.
The active precise-2D origin is the one specifically identified reference
decision: if that optional capability is essential, coordinator intake must
name a portable zero-angle convention or a corrected composite reference and
obtain the required independent review. No correction is implicit in the selected reference.
All remaining selected defined branches stay in the single CE06 aggregate.

Coverage is approved behavior plus independent risk review; percentages advisory.
Exact-candidate full local make verify and original Ubuntu24.04/macOS15 gates,
all reports, strict outcomes, wheel/import/audit and same-run M25 conversion
increment <=33,554,432 bytes remain unchanged. Source review precedes blind A/B;
no source-discovery report carries implementation-edit or test-deletion authority.
