# RA06: covariance-weighted known-parameter volume inverse

Version 1.0. 30 October 2026. The owner authorized RA06 above accepted RA05
`20355688312b791f72093d6764b5918b41e94ec6`, including independent high-risk
roles, exact local and hosted proof, measured figures, regular stacked PR and
preservation-aware cleanup. This contract selects the estimator before tests.
The roadmap alone supplies no additional scientific behavior.

## Public boundary and declared noise

```python
from simrecon import WeightedReconstruction3D, reconstruct_volume_weighted

result = reconstruct_volume_weighted(
    images, order_otfs=calibrations, phases_rad=phases,
    carriers_bins=carriers, gains=gains,
    exposure_covariance=covariance, regularization=alpha,
    output_shape_yx=(Ly, Lx), apodization=taper,
)
```

Only images is positional. All keywords are required. This is an additive pure
known-parameter operation. Preserve `reconstruct_volume` and its selected complex
Nyquist convention exactly. No parameter/noise estimation, automatic Wiener
rule, truth-selected penalty, Poisson likelihood, positivity, legacy C execution,
import, linking or copying, file operation, new dependency or performance
guarantee is selected. Empirical C settings are compatibility metadata only.

Images `(R,N,Nz,Ny,Nx)`, phases `(R,N)`, integer carriers `(R,2)`, gains `(R,)`,
order OTF records, complete nonwrapping output window `(Nz,Ly,Lx)` and taper
inherit the complete input grammar, snapshots, units, output-grid validation and
corresponding stable input/grid errors of
[volume recombination](volume-recombination-v1.md). R>=1, N>=5; signed images,
unequal/repeated valid phases, all permitted widths/endian/layouts and arbitrary
finite complex calibrated transfers remain valid. Origins are already encoded
in transfers. Gains multiply transfers once. No new physical admissibility
rejection is inferred from a complex transfer. All accepted fields are validated
even for zero data/transfer/taper. Phases use exactly the prerequisite represented
phasor-squared basis and its rank-five SVD cutoff, not doubled angles or period
reduction. The prerequisite phase-rank code remains applicable.

Exposure covariance is a plain real i/u/f ndarray `(R,N,N)`, copied to native
float64, finite before/after conversion. Layout/endian/read-only alternatives
are accepted; bool, complex, subclasses, masked/nonarrays and wrong shape reject
with `invalid_weighted_volume_covariance`. Converted symmetry must be exact.
Each symmetric matrix must be numerically positive definite: after division by
its largest absolute entry, all computed eigenvalues must be finite and
`eig_min > eps*N*eig_max > 0`, eps=2^-52. Nonsymmetry, zero, indefinite or
numerically singular covariance uses `singular_weighted_volume_covariance`.
Equality fails. This is an explicit numerical boundary, not an uncertainty
estimate or an arbitrary variance floor. Backend rounding can change a case
at that boundary. No pseudoinverse of covariance or silent diagonal replacement.

The caller declares this covariance in squared input-intensity units, constant
over detector voxels. Different voxels and orientations have zero covariance;
within an exposure vector full correlation is allowed. This is a declared
second-moment model. It need not describe any particular instrument. Correlated
voxels, cross-orientation noise, signal-dependent photon variance, calibration
uncertainty and covariance estimated from the same realization are outside its
statistical claims. The deterministic estimator is still defined for supplied
finite data regardless of whether that stochastic premise is physically true.

## Real forward map, normalization and separation

Let M=Nz*Ny*Nx and P=Nz*Ly*Lx. Finite Fourier coefficients use negative exponent
and divide by sample count; positive-exponent synthesis has no divisor. Detector
and output bins are centered canonical signed bins. This operation estimates
P real spatial values x, in input-intensity units, on the declared output grid.
It defines the following real observation map A, including at even Nyquist:

1. S(q)=DFT_output(x)/P. For each r and m=0,1,2, set
   D_rm(j)=gains[r]*E_rm(j)*S(jz,jy-m*cy,jx-m*cx). Every j is a canonical
   detector bin, with exact integer nonwrapping placement. The complete output
   window already contains these q. There is no detector wrapping of q.
2. d_rm is positive-exponent synthesis of D_rm on the native detector grid.
   Define h_r=(Re d_r0, Re d_r1, Im d_r1, Re d_r2, Im d_r2).
3. With represented c=cos(phi), s=sin(phi), c2=c*c-s*s, s2=(2*c)*s, set
   K_r=[1,2*c,-2*s,2*c2,-2*s2] and A_r x=K_r h_r at each voxel.

The real DC convention in step 2 is explicit. An arbitrary complex E0 can have
an unobserved imaginary DC prediction. Such a record is accepted but has no
implied physical real-DC model. On a matched Hermitian, conjugate-closed,
alias-free real source subspace this reduces to the RA02 physical real matrix.
Outside that setting the stated real map is normative, including even endpoints,
overlaps and rank deficiencies. It need not equal the original complex fusion
estimator. Negative bands are the conjugates of d_r1/d_r2, never additional
independent observations. All-axis detector-frequency reflection follows this
real-space conjugation, with the single canonical even endpoint retained.

For Sigma_r=exposure_covariance[r], define generalized least-squares (GLS)
separation:

```
L_r = (K_r.T Sigma_r^-1 K_r)^-1 K_r.T Sigma_r^-1
z_r = L_r images_r
Psi_r = L_r Sigma_r L_r.T = (K_r.T Sigma_r^-1 K_r)^-1
```

Here z has five real coordinates in the order used by h, and Psi has squared
intensity units. Implement using whitened SVD/solves, not explicit normal-matrix
inversion. The equations define exact-real expectations on represented inputs.
For N=5 full rank, L=K^-1, independent of Sigma. For N>5 ordinary unweighted
separation followed by covariance weighting is generally a different estimator
and can discard information; use GLS. In particular unequal phases generally
give correlated separated coordinates even for independent equal-variance raw
noise. Full covariance is retained.

The full raw objective decomposes into the z-h objective with metric Psi^-1 and
an x-independent GLS phase residual. Retain that residual in the reported raw
objective. Fourier transformation does not make real coordinates or signed
bands independent: for coefficient noise eta(j),
E[eta(j) eta(k).H]=Psi/M when j=k modulo the detector grid and zero otherwise;
E[eta(j) eta(k).T]=Psi/M when j=-k modulo the grid and zero otherwise.
Self-conjugate bins and relocated negative-band dependencies must be counted
through the real map, not doubled as new data.

## Weighted inverse, rank and zero regularization

The unmasked inverse minimizes

```
J(x) = (1/M) sum_r sum_detector_voxels
       (images_r-A_r x).T Sigma_r^-1 (images_r-A_r x)
       + alpha * sum_output_voxels x**2/P
```

Regularization alpha has inverse squared intensity units in this whitened raw
objective. It inherits the nonboolean real scalar, finite converted alpha>=0
grammar and `invalid_volume_reconstruction_regularization` error. It is a
declared penalty, never selected from truth or the observed residual.

For an unambiguous numerical rank convention define u=x/sqrt(P), b as raw data
whitened by a square root of Sigma^-1 and divided by sqrt(M), and B as the same
whitened A times sqrt(P/M). The square root can be any mathematically equivalent
factor. Use SVD of B, with tau=eps*max(R*N*M,P)*s_max and rank equal to the
number of singular values strictly greater than tau. Zero B has rank zero.
Return this rank as a diagnostic; rank deficiency is a successful information
outcome, not evidence of recovered missing modes.

For alpha=0 return the Moore-Penrose minimum-Euclidean-norm solution with exactly
that numerical cutoff (discard values <=tau). For alpha>0 use the unique ridge
solution with factors s/(s*s+alpha), including values below tau; exact null
directions remain zero. No positive transfer threshold, fabricated noise floor
or singular-information exception. An all-zero forward map returns zero x for
every alpha, while preserving the nonzero data residual if present. Use SVD or
equivalent stable factorizations, not a product normal-equation inverse.

Snapshot output x before taper. Untapered spectrum is its normalized centered
DFT. Apply the supplied amplitude taper only afterward and synthesize complex
volume on the output grid. Taper is excluded from J, rank and normal-equation
comparisons; an asymmetric taper may give a complex returned volume. Zero taper
does not waive invalid inputs or failed/nonfinite inverse arithmetic. There is
no positivity, intensity renormalization, hidden real projection of the tapered
volume, or normalization by the number of bands.

## Generalized Wiener units and scaling

On a matched real, alias-free, conjugate-closed supported subspace where
Psi=diag(v0,v1/2,v1/2,v2/2,v2/2), the equivalent diagonal signed-band objective
uses weights 1/v_m for each available signed band, with negative data/transfer
derived by complete conjugation/reflection. With t=g*E and no taper,

```
Q(q) = sum_(r,m) conj(t_rm)*D_rm/v_rm
       / (sum_(r,m) abs(t_rm)**2/v_rm + alpha).
```

This scalar formula applies only where the real map actually decouples into
those modes. Correlated coordinates, real/negative dependencies, aliasing and
unmatched even lifts require the full real system. Zero denominator at alpha=0
uses zero on the unobservable mode. With reference variance v_ref and normalized
weights w_rm=v_ref/v_rm, the squared-transfer denominator penalty is
lambda_den=alpha*v_ref. A plain numeric C setting cannot determine alpha
without its normalization, variance and intensity convention.

For ideal exactly orthogonal phases K.T K=N*diag(1,2,2,2,2) and Sigma=sigma² I,
all v_m=sigma²/N. An unweighted raw objective with ridge beta has
beta=alpha*sigma² and lambda_den=beta/N=alpha*sigma²/N. Stored float64 phases
are not exactly orthogonal: bound their represented Gram perturbation rather
than asserting exact identity. The RA02 declared matched metric supplies an
exact represented diagonal fixture separately from a physical-white premise.

Scaling checks follow directly from J: Sigma->c*Sigma and alpha->alpha/c leave
x unchanged for c>0. gains->a*gains and alpha->a²*alpha give x->x/a for a>0,
with fixed images/covariance. images->a*images, Sigma->a²*Sigma and
alpha->alpha/a² give x->a*x. Joint images/gains->a*(images,gains),
Sigma->a²*Sigma with fixed alpha leaves x unchanged. These statements describe
the mathematical stored-input problem, subject to represented rank/range and
rounding; they do not assert invariant diagnostics in changed units.

## Result, arithmetic and failures

Return frozen-binding `WeightedReconstruction3D` with exactly these fields:
`volume`, `spectrum`, `untapered_volume`, `untapered_spectrum`,
`separated_coordinates`, `separated_covariance`, `predicted_images`,
`residual_images`, `data_objective`, `penalty_objective`, `information_rank`,
`unknown_count`, `fz_per_um`, `fy_per_um`, `fx_per_um`, `voxel_size_um`.
Volume/spectrum/untapered_spectrum are native complex128 output-grid arrays;
untapered_volume is native float64 output-grid x. Separated coordinates are
native float64 `(R,5,Nz,Ny,Nx)` and covariance `(R,5,5)`. Predictions and residuals
are native float64 image-shaped arrays for the untapered x. Data objective is
the raw first term of J, penalty objective its second term, Python finite
nonnegative floats. Rank and unknown_count=P are Python ints. Frequency vectors
and spacing inherit recombination units/grid behavior. Every array is mutable,
independently owned, native C-contiguous and aliases no caller/output/other call.
Direct construction need not validate. Rebinding/deletion fails.

Use float64/complex128. Conversion rounding and finite underflow define the
problem. Preserve caller contents, strides, write flags, NumPy error modes and
warning filters on success/failure. Avoid avoidable raw transform-sum overflow
by finite component scaling. Required forward/synthesis transforms may use
public numpy.fft.fftn/ifftn or equivalent direct finite sums; no fixed call count
or test-only seam. Finite conversion is not a universal success promise when
the operational inverse/factors/intermediate or required diagnostics cannot be
represented. Translate nonfinite arithmetic/output/restoration to
`unrepresentable_weighted_volume_reconstruction`; numerical LinAlgError or
unusable factors to `weighted_volume_solver_failure`; arithmetic transform
warnings/FloatingPointError/OverflowError/nonfinite transform results to
`volume_reconstruction_transform_failure`. Catch these only in their numerical
stages. Expected conversion exceptions inherit the corresponding input code.
MemoryError and unrelated exceptions propagate. Handled arithmetic emits no
RuntimeWarning; unrelated warning categories remain visible. Simultaneous-error
precedence and message prose are unspecified.

Mandatory moderate-regime success: valid inputs with phase condition <=10,
normalized covariance condition <=100, dimensions R*N*M and P <=256,
gains in [1/2,2], transfer component magnitudes <=1, images abs<=16,
alpha in [0,1], retained nonzero singular values of B in [1/16,16],
and finite representable required output/diagnostics must succeed absent genuine
resource/dependency failure. This is not an input cap. Independent tests derive
stored-input error allowances before observations from epsilon, scales,
dimensions, singular gaps/conditioning and reference precision, including
ridge/cutoff margins. No universal accuracy digits are promised outside this
regime. A realization cannot set its own acceptance threshold. Stored-input
estimator agreement and expected reconstruction risk are separate claims.

## Scenario inventory and delivery

| ID | Distinct observable obligation or risk |
|---|---|
| W01 | Additive required public bindings/record; original estimator compatibility |
| W02 | Complete inherited image/phase/carrier/gain/OTF/window/taper grammar, paired positives and grid errors |
| W03 | Covariance shape/type/finite/symmetry and strict positive numerical spectrum boundary |
| W04 | Represented phase signs/factors, huge finite angles, valid rank and deficient rejection |
| W05 | GLS coordinates and exact covariance propagation; N=5 inverse and N>5 off-model projection |
| W06 | Unequal phases, unequal variances and correlated separated coordinates; joint exposure/covariance permutation |
| W07 | Independently assembled real forward/adjoint/normal system and raw versus separated objective constant |
| W08 | Nonwrapping signed placement, all-axis negative dependence, complex transfers, gain once, DC-real convention |
| W09 | Correct Fourier/real-coordinate multiplicities, odd/even endpoints and source penalty Gram |
| W10 | Unweighted matched RA02 real-system and exact represented-metric diagonal limits |
| W11 | Analytic generalized Wiener diagonal formula and alpha/v_ref/raw-ridge penalty conversion |
| W12 | Rank-deficient observable/null subspace; zero alpha minimum norm, positive ridge, rank zero |
| W13 | Declared data/gain/covariance/regularization scaling and units |
| W14 | Separate post-inverse taper; untapered predictions/residuals/objectives/rank unaffected |
| W15 | Native owned mutable array outputs, frozen bindings, complete diagnostics and independent calls |
| W16 | Caller snapshots/state preservation, unrelated/MemoryError propagation, numerical failures/range |
| W17 | Moderate mandatory success/independent precision budgets, exact zero data and finite operational limits |
| W18 | Measured residual/noise spectra, reproducible observations, stochastic versus stored-input claim limits |

A expands distinct inherited boundary decisions in its mapping without duplicating
their whole existing test matrix. A owns only
`tests/test_reference_alignment_ra06.py` and
`tests/reference_alignment_ra06_fixture.py`, independent real normal-system and
covariance fixtures, with test-audit authoring questions. No product helper or
legacy oracle. B independently challenges oracles, tolerances, omissions,
legitimate alternatives and exact frozen checkpoint. A/B read this contract,
RA02 public contract, volume recombination/phase contracts and narrow permitted
PROJECT text only; no implementation/history/state/coverage/old lessons.

C owns only `src/simrecon/weighted_volume_reconstruction.py` and additive exports
in `src/simrecon/__init__.py`. No frozen test/fixture/snapshot, gate, dependency,
workflow/discovery/coverage, policy/skill or unrelated-interface edits. Coordinator
owns contract/task/PROJECT, usage/report/figure generator and measured evidence,
packets, accounting and new unique lessons. Fresh native A/B/C/D use Sol/high,
memory/delegation disabled; coordinator launches, never roles. D assesses the
exact passing candidate and measured arrays/figures before current-task lessons.

Coverage inherits PROJECT approved behavior plus independent risk review;
percentages advisory, no selected target. Complete native global/package/file
statement/branch JSON/HTML reports, never-imported/relevant-subprocess scope and
both configured platforms remain binding. Focused checks are
`uv run --locked pytest tests/test_volume_reconstruction.py tests/test_reference_alignment_ra02.py tests/test_reference_alignment_ra06.py`
and the A checkpoint alone. Exact clean committed full `make verify`, fresh D,
then regular stacked PR against `codex/reference-alignment-ra05-transfers`.
Both hosted full proofs and preservation-aware cleanup precede review-readiness
and the requested new RA07 chat. No merge/release or unrelated external messages.

Retain original arrays, seeds, fits, settings, argv/environment, raw measurements
and rendered scientific figures; plot observed data. Derive comparison
conventions independently before using any supplied legacy numeric metadata.
No legacy archive/source inspection or execution. Retain all predecessor charges
by reference and every new failure/review/repair/exposure; numeric limits are not
set, unknown metering/served attribution/cost remain unknown. Sole Current state:
ignored `artifacts/ra06/current-state.json`. Blind roles never receive it.

Coordinator inventories only positively task-created scratch/processes, closes
owned writers, verifies retained files/original link texts/resolutions/dependencies
and preserves caches/environments/Python pins/incoming referents and ancestors at
original paths. Original evidence remains. Verified zero removal is allowed;
actual destructive scope requires its own applicable high-risk roles/checks.
No predecessor cleanup, reusable destructive tool or policy/gate exemption.
