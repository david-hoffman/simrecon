# CE02–CE08: rebuild the C procedure and prove the whole reconstruction

**Version 1.0. Ordered scientific stage contracts.**

Every section inherits the [common contract](c-equivalence-common-v1.md), source pin, owner requirement, input/error/domain inventory and fresh native A/B/C/D route. These contracts fix the scientific target. Before a stage starts, intake expands the exact selected branches, full equations and public signature/error table into a reviewable public packet; no implementation may fill a scientific gap by choosing a convenient estimator. Stage interfaces are pure arrays/value records until CE07 binds existing file adapters. Units, selected options, source identity and stage diagnostics travel in those records.

## CE02: preprocessing and separation

Input: explicitly ordered real specimen exposures, detector dimensions/sampling, resolved camera/background/flat-field parameters, phase policy, edge/equalization flags, output zoom and direction count. Output: the C-normalized native phase bands, noise factors and exact resolved preprocessing metadata. Unsupported combinations reject before numerical work. Do not use a camera moment estimator or a flat-relative intensity gauge as a substitute for declared C inputs.

The ordinary loading operation is `I'=alpha*s*(I-b-b_exposure)`, with multiplicative slope `s` when selected, and `alpha=1/(Nx*Ny*Nz0*zoom²*zzoom*ndirs)`. Preserve correction, lateral edge handling, selected sum equalization, lateral forward Fourier transform, phase separation, then axial transform. Sum equalization is data-dependent and uses direction-zero/phase-zero at the selected z/time reference. Its exact divisions, reference updates and zero-sum domain are part of the packet.

For uniform phases at samples actually separated: `B0=sum G`, `E_m=sum G*cos(m*phi)`, `O_m=sum G*sin(m*phi)`, `Bplus_m=E_m+i*O_m`; no `1/P` in specimen separation. For supplied phases use the inverse or unweighted left inverse of the C forward matrix with columns `1/P`, `2*cos(m*phi)/P`, `2*sin(m*phi)/P`. Preserve one scalar noise factor per direction/order derived from the separation-row squared norms, combining side quadratures. No full covariance estimator.

Preserve the unseparated stored lateral Nyquist pair and the exact harmonic/phase conventions. Source: `helpers.c:658–705`, `sirecon.c:432,632–742,1051–1274`, `small_math_funcs.c:85–109`. The packet must specify the edge equations and all equalization cases rather than cite these ranges as a replacement for them.

Acceptance: independently calculated constants, signed complex harmonics, irregular full-rank phases, unequal frame sums and flat slopes, degenerate rejection, positive/negative frequency endpoints, Nyquist reached by optical support, normalization and every selected branch. Use finite Fourier sums. Demonstrate actual public preprocessing-to-bands composition. No PSF fitting or reconstruction exists yet.

## CE03: optical transfer preparation and sampling

Input: selected raw bead planes and explicit optical/bead/acquisition settings, or a declared C transfer-table layout with complete samples and sampling metadata. Output: empirical optical transfer function (OTF) tables and their complex sampling operation. Point spread function (PSF) means the spatial response; an arbitrary normalized PSF transform is not a substitute for the empirical preparation path.

Preserve bead pixel correction, background selection, edge operation, peak/parabola centering, Fourier transform and centering phase, finite-bead division, radial averaging, axis repair, optional support cleanup, normalization and quadrature combination in the actual C order. Bead separation includes `1/P`, unlike specimen separation. Do not infer unknown parameters through the removed three-bead physical optimizer.

For bead radius `R`, use `S_R(rho)=3*(sin u-u*cos u)/u³`, `u=2*pi*R*rho`, with limit 1 at zero. Divide both quadratures at the exact order-shifted frequency selected by C, `rho=|(kx,ky,kz)+m/(M*linespacing)*(cos theta,sin theta,0)|`, where `M=norders-1` is the highest retained order. Define directions and source units from the selected C configuration in the public packet. Handle transform zeros as a declared unsupported domain; do not add a regularizer.

Radial bins use C's rounded index-radius operation. Preserve `H(r,-kz)=conj(H(r,kz))`, which permits imaginary odd values and does not imply all-real transfer. Default 3D normalization is one inverse maximum modulus of order zero, not separate per-order or plane normalization. Quadrature combination is `C*cos(varphi)-S*sin(varphi)` with the source's magnitude-sum/sign rule for `varphi`, not `C+i*S`.

Radial sampling is complex bilinear interpolation in radius/axial frequency; full tables use the selected trilinear interpolation and negative-x all-coordinate reflection plus conjugation. Preserve source wrapping, endpoints and actual accessed stencil, including the extra lateral sample even at zero fractional weight. Source: `mainfile.c:192–411,651–866,1041–1140`; `small_math_funcs.c:396–483`; `helpers.c` transfer reading. The exact centering, binning, axis-repair and quadrature-angle equations must be expanded before A; no omission becomes an implementation choice.

Acceptance: asymmetric complex transfers, radial imaginary-odd structure, unequal order amplitude, common normalization, displaced bead, continuum-sphere versus discrete-sphere discriminator, each selected layout and stencil boundary, and public bead-to-transfer-to-sample composition. No direct pupil/finite integrated-source simulation is installed as the oracle.

## CE04: known-parameter filter and assembly

Input: accepted bands, accepted transfer tables, supplied carriers/complex modulation and explicit supported filtering/output configuration. Output: the same real sampled reconstructed image as fixed-parameter C, with declared output coordinates and optional stage diagnostics. This is the first complete known-parameter reconstruction; there is no iterative specimen source solver or positivity projection.

At native sample `k` of direction/order `(d,m)`, object frequency is `K=k+m*k0_d`. With `a_d0=1`, the filtered coefficient has numerator

`T(K)*g_dm(k)*conj(H_m(k))*conj(a_dm)*B_dm(k)`

and denominator `w²` plus the exact eligible signed transfer-power terms. `g` includes the selected suppression/damping and scalar inverse order-noise factor. Preserve self/other differences: self radial `<=` cutoff versus other radial `<`; the other-term loop does not impose each other order's axial cutoff. Preserve order-dependent integer axial cutoffs, order-zero special rules, all signed bands/directions and selected overlaps. No idealized common denominator or full covariance inverse is substituted.

Default suppression is `1/(1+1000/(r²+0.2))` at the source-defined radius; its nominal radius parameter is unused. The default output taper uses C's cosine of clipped elliptical shifted frequency. Expand these radii, cutoff equations and every selected mask into the public packet before tests. No arbitrary caller mask substitutes for C taper semantics.

Recover the negative filtered partner by conjugate reflection; reconstruct the quadratures; embed native coefficients in the larger zero-filled Fourier array; perform the unnormalized inverse transform; then assemble

`f(r)=sum_d [Re(u_d0(r))+2*sum_(m>0) Re(u_dm(r)*exp(2*pi*i*m*k0_d dot r))]`.

Use centered output coordinates, the upstream C scale and positive signed Nyquist placement without splitting. Native filtering precedes noninteger carrier relocation. Never interpolate unfiltered data/transfer and then form a quotient. Source: `sirecon.c:2005–2493`; `small_math_funcs.c:381–394`.

Acceptance includes constant and displaced-point amplitude, independently synthesized small modes, anisotropic z versus lateral sampling, noninteger carrier, signed negative output, complex conjugation, Nyquist placement, support boundary inequalities and taper order. Sanity checks: unit transfer/data with `w=0.5` gives `0.8` for a single unit-weight term; suppression `s=0.1,w=1` gives `1/11`, not `0.05`. These local checks supplement, never replace, an independent full band-to-image expectation. Numerically show image and spectrum differences from the retired interpolation-first procedure.

## CE05: carrier and modulation estimation

Input: accepted separated specimen bands, transfers and the C initial guesses/options. Output: the C finite-search carrier and complex modulation factors, branch/status diagnostics and exact finite trace on independent small tests. Do not replace the procedure by a converged optimizer, normalized residual fit or a nominally equivalent objective with different evaluation order.

Construct each selected overlap by multiplying one band by the other band's complex transfer and dividing by `sqrt(|Ha|²+|Hb|²)`. Preserve selected masks, threshold `0.006`, the ordinary-3D factor 5, inverse-transform conventions and displacement `(b-a)*k0`. No magnitude or conjugate substitute.

Coarse search maximizes the squared modulus of the lateral transform of the z-summed `Oa*conj(Ob)`, using first-strict-maximum ties and periodic-neighbor parabola refinement. Preserve the literal alias test containing `old_k0*dk` and its units as implemented, labeling the quirk. For refinement, `Y=Ob*exp(2*pi*i*(b-a)*k0 dot centered_r)` and `a_forward=sum(conj(Oa)*Y)/sum(|Oa|²)`. Maximize `|a_forward|²` using angle step `0.001 rad`, parabola, then magnitude step `0.1/(max(Nx,Ny)*dxy) cycles/um`, parabola.

Trace main's forced `recalcarrays=1`: remake overlaps once at refinement entry, then freeze during that pair's search. Preserve strict-improvement branches, tie/bracket state, zero-curvature behavior, later order fits, amplitude floors and selected higher-order phase replacement. A shared maximizer alone does not prove the same finite result. Source: `sirecon.c:803–898,1323–1999`; `small_math_funcs.c:285–333`.

Acceptance: independently calculated overlap values and finite search traces, known signed carriers/gains, ties and symmetry, weak/absent overlap, zero-curvature and input-range boundaries; successful composition into CE04. Require evidence that the workflow uses these outputs, not a different hidden bead/calibration path.

## CE06: defined acquisition modes

Produce the complete source-mode ledger required by the common contract. For every mode required by the supported public scope, expand and prove its actual C branch before adding it: 2D preparation/reconstruction; radial/full transfer layouts; supplied phase lists/steps; time/z sharing in equalization; optional drift estimation/correction; zoom/taper/suppression variants. These remain C parity work, not enhancements. Stage may be divided into coherent dependent PRs if necessary; no new mode may evade contracts/reviews by being called a default.

For selected drift, preserve actual estimation and coordinate origin plus Fourier correction `exp(+2*pi*i*k dot displacement)` and the associated phase linkage `+2*pi*dxy*drift dot kguess`; porting only a generic shift identity is insufficient. Source: `drift_n_phasestep.c:229,595` and its callers. Do not fit independent free exposure phases through the retired source-nuisance estimator.

Defined modes not yet ported are explicit unsupported capabilities. Unsafe/undefined C branches remain explicitly excluded with source evidence. The ordinary initial 3D profile must work throughout. No blanket C-equivalence claim covers the unsupported ledger. If a required application needs an excluded branch, return that concrete reference decision to the owner rather than inventing intended behavior.

## CE07: public workflow

One reconstruction entry point consumes explicitly declared specimen images, calibration observations or accepted transfer tables, and resolved C configuration. It invokes only CE02–CE06 stages in the actual C order. It returns the real reconstruction, physical coordinates/intensity units, resolved settings, source identity and stage diagnostics. Calibration selection, phase/carrier policy, output scaling and unavailable outcomes are visible. No automatic fallback to any retired solver, oracle-only true parameters or unrequested optimizer.

Existing neutral I/O may adapt values without changing pixel meaning. Missing C-required metadata/optics/phase policy is a meaningful input error, not an invitation to estimate a different physical model. Freeze the public signature and complete array/error/representation contract before A. Source-derived end-to-end expectations independently start at corrected raw input and traverse preparation, fitting, filtering and assembly. Tests must observe the actual public output, including a case that the historical fit path would fail.

## CE08: independent reconstruction acceptance

First prove the fixed-parameter mapping and finite nuisance search on small independent controls. Then use a preregistered matched acquisition with spatial information outside the conventional passband but inside the declared combined support. Derive expected C regularization/taper bias before calling the product; exact recovery of arbitrary noisy objects is not the contract. A larger useful reconstruction case follows only after these proofs, with explicit field, sampling, parameters, input provenance and recovery criteria frozen in advance.

Show signed ground truth, conventional comparison, reference-mathematical expectation, reconstructed image, residual and frequency/mode recovery on common scales. Report numerical equivalence separately from recovery and conditioning. A resolution claim needs a declared physically meaningful comparison and resolvability criterion, not denser output voxels. Noise/dose comparisons match acquisitions and report known limits. No truth-conditioned fitting, seed selection, residual-threshold relaxation or per-result rescale/registration.

If supplied matching owner C outputs become available, compare under exactly recorded settings and coordinate/unit maps; until then label binary-output agreement untested. Current no-C-execution and stop-before-old-RA15 constraints remain. An unsuccessful recovery case stays in the evidence and blocks any claim that the reconstruction goal passed; it does not authorize a different estimator. Only a separately requested post-baseline improvement may change the mathematics.
