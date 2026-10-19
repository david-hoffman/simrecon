# Relative phases and response invariants in the selected three-field model

**Result.** The selected finite model has both nonidentifiable and informative cases. Equal side fields admit independent exposure reflections that can leave every current calibration response unchanged. A different unknown-power/brightness family changes relative order gains while preserving raw observations. Unequal side fields, sufficient axial diversity and an identifiable phase design instead determine relative phases and the point-bead kernel, under the precise conditions below. These conditional results select no estimator or instrument premise.

This report uses the already selected [static periodic scalar model](../models/synthetic-3d-acquisition-v1.md). It does not establish an experimental acquisition model, numerical stability, continuous observation, motion, or a completed raw workflow. Its elementary proofs are analytical; no generated-data experiment was run. The optical motivation is focal-plane-relative illumination multiplying the detection kernel, as in [Gustafsson et al., equations 3–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). The finite grid, field family and normalization here are project choices.

## Information and target table

An identifiable target must agree for every admissible tuple producing the same observations, modulo its explicitly declared consumer equivalence. A phase label, a normalized response and a physical field power are different targets.

| Conditional information set | Exact conclusion | Important limit |
|---|---|---|
| Fixed equal-side fields, point bead, otherwise even known parameters | Independent exposure reflections preserve raw data and the same separated coefficient images | Actual phase labels need not be unique; this alone blocks no response-invariant workflow |
| Equal real positive side fields, unknown powers and brightness | The D,E family below preserves raw data and changes normalized side gains | It preserves h; no unknown-kernel-shape ambiguity follows |
| Point bead, unknown shared kernel/fields/brightness/position, known native axial mode, four distinct positive-weight axial directions, rank-five phase design, nonzero central field and unequal side magnitudes | Global relative phases up to common rotation/reflection; complete data also determine c0, B, b and h | Exact uniqueness supplies no noise, conditioning or binary64 guarantee; lateral carrier remains unidentified |
| Same point case, unknown axial mode, all axial planes positive and observed, native cycle length at least four | Native mode is determined modulo sign and integer-period lifts; preceding phase/kernel conclusion still holds | Physical unaliased axial frequency is not determined |
| Missing axial planes | Known mode still permits the four-direction phase theorem; unknown mode can have additional aliases | General partial-plane classification and missing kernel mass/peak are not settled |
| Known profile, one common lateral carrier character, nonzero discrete Fourier transform at every node, complete data | Exact exposure-level deconvolution reduces to the point theorem | Multiple lateral characters, missing data and numerical conditioning need separate arguments |
| General finite profiles or nonnegative specimens | Neither point factorization nor its conclusion transfers automatically | Explicit mixed-profile and phase-erasing examples appear below; no universal failure is asserted |

## Model, units and rank

Let Pfield=|a0|²+|a+|²+|a−|². Write the normalized products

```text
u=a+ conjugate(a0)/Pfield,  v=a0 conjugate(a−)/Pfield,
g=a+ conjugate(a−)/Pfield,  tau=|a0|²/Pfield.
g1(t)=u exp(−it)+v exp(it),  g2=g,  uv=tau*g.
```

For a point s=B delta_b, let beta=2*pi*q·r_b,xy, eta_p=phi_p+beta, omega=2*pi*ell/Nz and t=omega*(n_z−b_z). Then

```text
D_p[n]=B h[n−b] {1+2 Re[g1(t) exp(i eta_p)+g exp(2i eta_p)]}.  (1)
```

h is nonnegative, unit mass and has its sole largest sample at zero. B>0 is the zero-order summed brightness in expected electrons. D has expected-electron units; normalized fields, h and intensity factors are dimensionless. Angles use radians. ell is an integer axial mode; its physical frequency is ell/(Nz*dz) cycles/µm. An unknown b or field phase is not supplied truth.

The ideal phase design has columns 1, cos(phi), sin(phi), cos(2phi), sin(2phi). It has rank five exactly when there are at least five distinct phases modulo 2*pi. For sufficiency, a nonzero degree-two trigonometric polynomial cannot vanish at five distinct points: multiplication by exp(2i phi) makes a polynomial of degree at most four. Necessity follows because fewer distinct rows cannot have rank five. Extra repeated rows are allowed. This exact-real criterion is distinct from the current separator's represented matrix and numerical rank policy.

## Equal-side reflections: phases can change while responses do not

Suppose |a+|=|a−|>0 and a0!=0. Put gamma=|a+|²/Pfield=(1−tau)/2. With field arguments beta0,beta+,beta− define

```text
delta=(beta+−beta−)/2,  xi=beta0−(beta++beta−)/2,
g1(t)=2 sqrt(gamma*tau) exp(i delta) cos(t+xi),
g2=gamma exp(2i delta),  eta_p=phi_p+beta+delta.
I_p=tau+4 gamma cos²(eta_p)
          +4 sqrt(gamma*tau) cos(eta_p) cos(t+xi).             (2)
```

The identity follows by adding the two equal-magnitude first-harmonic phasors; uv=tau*g fixes the second-harmonic phase consistently. For arbitrary independent signs epsilon_p in {−1,+1}, replace eta_p by epsilon_p*eta_p while holding fields, kernel, brightness and bead fixed. Both cosines are unchanged, so every raw sample agrees. This is the exact equal-side family, including complex constant field phases.

A concrete positive example uses a0=a+=a−=1, b=0, any strictly positive selected exponential-cosine kernel, and eta_p=j*pi/7 for j=1,…,5. Reflect only the first angle. Both designs have five distinct circle points and hence rank five. Four unchanged angles rule out a common rotation or common reflection relating the two entire vectors. No |2 cos(eta_p)| equals one, so |exp(it)+2 cos(eta_p)| is strictly positive for every t; these examples need no dark exposure. The tuples are analytic examples, not estimator initialization or generated data.

Crucially, c0, c1 and c2 themselves are unchanged. With real positive fields and b=0 they are B*h, 2B*sqrt(gamma*tau)*h*cos(t), and B*gamma*h. The same arrays synthesize the observations under both rank-five designs, so uniqueness of supplied-phase separation returns those same arrays. More general field phases only add their common retained order factors. Thus mass, observed origin, common-mass normalized responses, and declared known-profile compensated responses also agree. Supplied-phase provenance differs. A timing/phase-label target can fail even when these response targets agree.

This is global ambiguity, not necessarily absent local information. With the other quantities fixed, the phase derivative of (2) is

```text
−4 sin(eta_p) [2 gamma cos(eta_p)+sqrt(gamma*tau) cos(t+xi)].   (3)
```

If two different cosine values have positive kernel weight and sin(eta_p)!=0, that derivative cannot vanish at every sample. Each exposure then has local phase sensitivity while its reflected global alternative survives. Nominal commands alone provide no branch restriction.

## A distinct ambiguity changes normalized response gains

Take real positive equal-side fields, anchor zero, x_p=cos(eta_p), and allow tau, gamma=(1−tau)/2 and B to be unknown. Equation (2) becomes

```text
D=B*tau>0,  E_p=4B sqrt(gamma*tau) x_p,
D_p[n]=h[n] {D+E_p²/(4D)+E_p cos(t)}.                        (4)
```

For any tau' in (0,1), put gamma'=(1−tau')/2, B'=D/tau', and x'_p=E_p/[4B' sqrt(gamma'*tau')]. Whenever |x'_p|<=1, choosing cos(eta'_p)=x'_p preserves (4) exactly. Both field tuples retain squared-field nonnegative intensity. The explicit pair

```text
tau=gamma=1/3;  tau'=1/5, gamma'=2/5;
B'=5B/3;  cos(eta'_p)=cos(eta_p)/sqrt(2)                     (5)
```

works for all exposures. Five distinct eta in (0,pi) map to five distinct eta' there, so both phase designs are full rank. The positive example above applies. The kernel, mode, carrier and anchor stay fixed.

The coefficient arrays scale by (5/3,sqrt(2),2) for orders (0,1,2). Dividing each tuple by its own zero-order mass gives

```text
K0=h,                   K0'=h,
K1=(2/3)h cos(t),        K1'=(2sqrt(2)/5)h cos(t),
K2=(1/3)h,               K2'=(2/5)h.                        (6)
```

The second-order zero-frequency response is 1/3 versus 2/5. Common brightness normalization, recentering and unit-modulus phase changes cannot reconcile them. Therefore the current calibrated target retaining relative complex order gains is nonidentifiable over this unknown-power/brightness class from the bead stack alone. Holding powers or brightness fixed invalidates this particular family; it is not an impossibility proof for those narrower information sets. It also proves no nonuniqueness of h, because h is identical throughout.

There is a useful narrower kernel result. If the absolute sequence x_z=cos(omega*(z−b_z)+xi) is independently fixed, the balanced stack has columns B*h[n]*F*(1,x_z), with F rows (A_p,T_p)=(tau+4gamma cos² eta_p,4sqrt(gamma*tau) cos eta_p). Rank(F)=2 and three distinct positive-weight x_z fix F up to a positive scalar: three distinct directions in the projective line force the intervening two-by-two matrix to be scalar. Thus F'=alpha*F and B*h=alpha*B'*h'; unit mass fixes h'=h and B'=B/alpha. Substitution into A_p=tau+T_p²/(4tau), at two distinct T_p² values, forces tau'=alpha*tau. Hence B'tau'=Btau and B'T'_p=BT_p: the remaining power/brightness alternatives are precisely (4), with admissible cosine branches. This lemma requires fixed axial origin/field phase; it does not recover them from hidden truth or establish general balanced unknown-kernel uniqueness.

## What the actual consumers can absorb

The [empirical response contract](../contracts/empirical-volume-response-v1.md) keeps one common normalization and relative order gains. The [adapter](../contracts/empirical-transfer-consumption-v1.md) applies only a declared common fundamental phase-reference change, multiplying order m by exp(−im*delta). It preserves order zero. [Reconstruction](../contracts/volume-recombination-v1.md) has one positive gain per orientation multiplying every order. Since K0 is unchanged and nonzero in (6), that common gain must be one to match it; it cannot also fix the different side gains. These current freedoms do not identify the two response objects.

An explicitly composed workflow can have a larger equivalence. [Relative volume-order gain fitting](../contracts/volume-order-gain-v1.md) fits a separate complex scalar for one positive order using supplied phases/carrier and informative specimen overlap. If E'_m=a_m E_m, its least-squares predictor scales by a_m and the fitted correction scales by 1/a_m, so their product is invariant wherever the fit is identifiable. In (6), a1=3sqrt(2)/5 and a2=6/5; independent order corrections could remove both differences. The operation supplies no correction when predictor information is absent, estimates no independent phase steps, and applies no automatic reconstruction. This larger workflow therefore needs its own observed inputs and composition contract. Different calibrated inputs alone do not prove every possible raw workflow or reconstruction ambiguous.

For arbitrary per-order scalar freedom, response shape rather than its scalar is the target. Family (5) preserves those shapes. It is unsuitable as an oracle claiming shape nonuniqueness. Unknown shared-kernel uniqueness must be proved separately; the unequal-side theorem next supplies one positive result.

## Unequal-side point theorem with an unknown shared kernel

Assume complete noiseless point-bead data, a0!=0, |a+|!=|a−|, a rank-five actual phase design, and a known native axial mode. Require at least four distinct sampled axial directions with positive marginal kernel weight. Brightness, bead index, kernel and constant complex fields are unknown. A single point's unknown lateral carrier contributes only a common phase offset; this theorem does not identify that carrier. For phase recovery alone, an observed subset with those four directions suffices. Complete-data consequences below require complete spatial observations.

**Factorization.** Set t_z=omega*z. Absorb unknown b_z into u_tilde=u exp(i omega*b_z), v_tilde=v exp(−i omega*b_z). Lateral sums obey

```text
Y[:,z]=w_z F v_z,  v_z=(1,cos t_z,sin t_z)^T,
w_z=B sum_xy h[(z,y,x)−b],
F=[d A C],
d_p=1+2 Re[g exp(2i eta_p)],
A_p=2 Re[(u_tilde+v_tilde) exp(i eta_p)],
C_p=2 Re[i(v_tilde−u_tilde) exp(i eta_p)].                    (7)
```

The two first-harmonic coordinates equal L*(cos eta_p,sin eta_p). Direct expansion gives

```text
det L=4(|u|²−|v|²)
     =4|a0|²(|a+|²−|a−|²)/Pfield² !=0.                     (8)
```

For real positive fields with a+>a−, A=2(u+v)cos eta and C=2(u−v)sin eta, confirming the sign. Rank-five phase design makes F rank three: A,C span the first-harmonic columns, whereas d has constant coefficient one and only second-harmonic additions.

**Four directions remove the projective ambiguity.** Any alternative producing the same Y must have F'=F Q for an invertible real three-by-three Q. At positive-weight planes, Q v_z=(w_z/w'_z)v_z. Three distinct circle directions form a basis. In that basis Q is diagonal. A fourth distinct circle direction has every coordinate nonzero, since no line intersects a circle at three distinct points. Its eigenvector equation forces all eigenvalues equal. Hence Q=c Id with c>0. F and its first-harmonic coordinates are determined up to one positive scale. An alternative equal-side or zero-central-field tuple has rank at most two and cannot reproduce this Y.

**The centered ellipse removes the unknown field map.** For f_p=(A_p,C_p), there is a positive symmetric matrix H with f_p^T H f_p=1. It is unique: a difference of two such quadratic forms restricts, after the invertible L map, to a combination of 1,cos(2eta),sin(2eta). Rank-five phase design makes those three columns independent. Whitening gives H^(1/2) f_p=O*(cos eta_p,sin eta_p), with one common orthogonal matrix O. The unknown positive scale cancels. Thus all admissible phase vectors differ by one common rotation and optional reflection. This is a global uniqueness argument. Field rephasing and side-field exchange realize those freedoms; labels or nominal commands do not choose them.

Five distinct phases are a sufficient transparent premise. More minimally, rank(F)=3 and rank of the three ellipse quadratic columns suffice, but those are separate obligations, not a new operational test here. Four visible axial directions are sufficient for this proof; necessity under every physical restriction is not asserted. Near-equal fields, nearly coincident directions and poor phase designs may be arbitrarily ill-conditioned despite exact uniqueness.

**Kernel and response consequences.** A recovered phase representative uniquely separates every observed voxel. A common rotation phi'=phi+alpha gives c'_m=exp(−im alpha)c_m. A common reflection phi'=−phi+alpha gives c'_m=exp(−im alpha)conjugate(c_m). Both leave c0 unchanged. With complete data,

```text
B=sum_n c0[n],  b=unique grid maximum of c0,
h[u]=c0[u+b]/B.                                             (9)
```

So kernel shape, model brightness and peak-origin bead index are identified. A missing plane does not supply its unobserved mass, peak or kernel values. Brightness is not calibrated photon yield and the model peak is not a certified physical emitter center.

Normalized signed side responses are determined in the same phase/conjugation quotient. In Fourier coordinates, reflection means E'_m(k)=exp(−im alpha)*conjugate(E_m(−k)), with native modular negation; it is not same-frequency conjugation. This uses the [negative-exponent discrete Fourier convention](https://numpy.org/doc/stable/reference/routines.fft.html). A signed consumer must receive a consistent phase/carrier orientation, not silently discard the reflection.

With all three fields nonzero, recovered c1/c0 and c2/c0 at positive planes determine the product magnitudes. The normalized powers follow from

```text
tau=|u||v|/|g|,  power_plus=|u|²/tau,
power_minus=|v|²/tau.                                      (10)
```

Common field scale/phase remain invisible and reflection exchanges side labels. One zero side is a legitimate exception: a0=sqrt(r),a+=sqrt(1−r),a−=0 and its r↔1−r alternative have identical u,v,g and intensities. Phases and responses can be identified while those two power assignments are not.

A strictly positive admissible example is a0=4,a+=2,a−=1, Pfield=21, any selected strictly positive unique-peak kernel, five regular phases, and native cycle length at least four. The total field magnitude is at least 4−2−1=1, so intensity is at least 1/21. Equation (8) gives 192/441>0. Kernel symmetry is harmless here; equal side magnitudes, insufficient axial diversity or missing information are the relevant deficiencies.

## Unknown axial mode and missing planes

Let r=Nz/gcd(ell,Nz) be the number of distinct axial directions. If every axial plane is observed with positive marginal weight, rank-three Y exposes exactly which labeled columns have the same projective direction. Any alternative mode has the same repeated-direction partition and hence the same r. Write ell=d*k,ell'=d*k', where d=Nz/r and k,k' are units modulo r.

For r>=5, the change-of-factor projectivity maps at least five conic points onto conic points. Pulling back the conic equation gives a degree-two trigonometric polynomial; five zeros force it to vanish identically. Thus it preserves the entire real conic and induces a circle homeomorphism. Such a map preserves or reverses cyclic order. On the complete regular r-gon the labeled permutation is j→(k'/k)j, fixing zero. Only multiplication by +1 or −1 preserves or reverses cyclic order. For r=4, the only units are already ±1. Therefore

```text
ell' = ell or −ell modulo Nz.                               (11)
```

All integer-period lifts remain aliases. Both signs are realizable by changing field labels/conjugations consistently with the axial sign. A positive kappa convention does not remove a positive representative Nz−ell. No true-frequency-centered interval or unproved sampling bound entered the proof. With r>=4, either representative yields the same phase quotient and c0/h result. Physical unaliased kappa remains unknown.

For a known mode, four positive distinct observed directions still suffice when other planes are missing. For an unknown mode, the full-polygon argument fails on a partial set. A concrete counterexample has Nz=12, visible planes S={0,2,4,6,8,10}, and ell=1 or 7. Their axial exponentials agree on S although 7 is neither ±1 modulo 12. Choose an axial kernel with weight 1/2 at zero, 1/10 at each other plane in S and zero elsewhere, times a positive normalized lateral kernel with sole peak zero. Both tuples satisfy the selected kernel gauge, arbitrary unequal fields and full-rank phases; all complete raw samples agree. This alias even preserves the response arrays and phases, so it does not itself prove a response ambiguity. With acquisition omissions instead of zero kernel planes, the observed-data alias holds for any common positive kernel.

The remaining general missing-plane problem is exact: classify labeled finite conic configurations, positive weights and physically feasible alternative coefficients for each candidate residue. No universal uniqueness is asserted. Cycles r=1,2 cannot supply rank three; with real fields, kernel support only at axial angles 0 or pi retains reflection even for unequal sides. A delta kernel is an admissible extreme example. At r=3 the four-direction proof is unavailable; additional physical constraints require a separate analysis. No blanket failure theorem is claimed there. A vanished central field removes the first harmonic; equal side magnitudes collapse (8); rank-deficient phase designs lack the stated separation guarantee.

## Finite profiles: proved extension and explicit boundaries

For p=(1−epsilon)delta_0+epsilon delta_ez, 0<epsilon<1/2,

```text
P[k]=1−epsilon+epsilon exp(−2*pi*i*k_z/Nz),
|P[k]|>=1−2epsilon>0.                                      (12)
```

Both occupied sites have the same lateral carrier phase. This genuinely nonpoint nonnegative profile preserves the equal-side reflection and D,E examples, with a strictly positive chosen h. There is no profile spectral zero. Its exact lower bound is not an executed numerical conditioning certificate under the current finite-bead API.

More generally, reflections and (4) extend when all occupied lateral carrier phases agree modulo pi. Relative to a common character, let sigma_j=±1 be their signs. Then raw data equal

```text
[D+E_p²/(4D)]*(h*p) + E_p*((h cos(t+xi))*p_sigma),
p_sigma[j]=sigma_j*p[j].                                   (13)
```

Holding D,E,h,p fixed proves the extension. Ordinary deconvolution by p is not a point-model inverse for arbitrary signed p_sigma.

A separate positive transfer of the point theorem is available. Suppose p is exactly known/anchored, complete circular data are observed, every P[k]!=0, and every occupied profile site has one identical lateral carrier character modulo 2*pi. Absorb that character into the common phase. If F_p[n]=B*h[n−b]*I_p(anchor,(n_z−b_z)dz), direct expansion gives

```text
D_p=p*F_p.                                                  (14)
```

The axial displacement shifts by the same profile index as h. Circular convolution by p is invertible, so division by P recovers each point exposure without supplied phases. The point and full-plane mode theorems therefore transfer to this precisely defined class. This is an analytical proof, not an implementation of the existing [known-phase compensation](../contracts/finite-bead-compensation-v1.md), a stability bound, or a missing-plane result. Carrier/profile knowledge and the shared-character condition must be legitimate inputs or established observations; evaluator truth cannot certify them for an estimator.

Multiple lateral phases can add information. For example, use lateral size four, mode one, p=(1−epsilon)delta_0+epsilon delta_ex, 0<epsilon<1/2, and h=delta_0. The occupied carrier phases differ by pi/2, while P is still nonzero everywhere. Equal real unit fields at the second site give B*epsilon*(1−2 sin eta)²/3; reflecting eta gives B*epsilon*(1+2 sin eta)²/3. Their difference is nonzero for sin eta!=0. The D,E pair also fails there in general: at eta=pi/2, the original second-site intensity times B is B/3, while (5) gives B*(9−4sqrt(2))/3. These examples refute an indiscriminate extension of those ambiguities; they do not prove global uniqueness of general mixed profiles.

Conversely, broad nonnegative profiles can erase phase information even with unequal fields and a strictly positive unique-peak kernel. On Nx=7 with lateral mode one, take a uniform specimen and a separable kernel whose lateral factor is [1+epsilon*cos(2*pi*3*x/7)]/7, 0<epsilon<1, with any selected positive axial factor and Ny=1. Its lateral Fourier coefficients at ±1 and ±2 vanish. Every side coefficient vanishes and every exposure is the same constant, for arbitrary full-rank phase designs. This is a valid selected forward-model specimen; its uniform profile has spectral zeros and lies outside the current all-node finite-compensation acceptance domain. It establishes no failure result for every compact invertible profile. General mixed-character invertible profiles remain a separate proof problem.

## Observed inputs, evaluator truth and next contract

| Quantity | Present status | Permitted use in a future inverse contract |
|---|---|---|
| Corrected raw exposures, grid/spacing, plane/group labels | Supplied observations/declarations; camera correction still needs its declared inputs | Actual inverse inputs with recorded units/provenance |
| Nominal commands | Metadata distinct from actual phases | Initialization/branch policy only if a new justified contract selects it |
| Actual phases, fields, h, B, bead location, true carrier | Generator/comparison truth in synthetic examples; not automatic raw metadata | Evaluate analytic counterexamples; never seed raw search, support, settings or tolerances from truth |
| Point support or a known profile/anchor and carrier character | Conditional structural information | Must be independently supplied/certified or explicitly contracted; no inference from calling an array a bead |
| Unequal sides, central field, phase/rank/diversity conditions | Theorem premises | An operational acquisition/model or observable diagnostic obligation, with legitimate failures, not silent exclusions |
| Native mode | Known-mode premise or finite residue inference under complete-plane theorem | All residues modulo Nz are the mathematical sample classes; physical lifts remain unresolved |
| Phase rotation/reflection and order-gain quotient | Choice of target and consumer | Carry consistently into signed responses, carrier orientation and any gain fitting |

Independent expectation options are exact squared-field substitution, direct finite sums with separately derived signs, the polynomial root/rank proof, projective eigenvector uniqueness, and the centered quadratic-form proof. Positive and counterexample pairs must be checked against all information premises. Existing runtime output, this nonblind discovery history or a fitted residual is not an independent oracle. Any numerical contract needs fresh blind tests and review, represented arithmetic/rank/conditioning decisions and honest no-information outcomes.

The concrete next operational contract must declare the legitimate source of phase/carrier/profile information and the response quotient the raw workflow needs. One useful candidate is unknown-phase point calibration in the unequal-side, complete-plane finite family, returning a consistently gauged response and ambiguity outcomes; it is only a candidate until its structural information and numerical meaning are authorized. The current allowed family also contains balanced unknown-power alternatives, so a universal raw self-calibration promise would be false. A balanced response-shape contract or a particular mixed-profile/partial-plane contract would need its own missing origin/field/profile premises resolved. No favorable case is adopted here and no generic report successor is justified merely by unresolved subcases.

Confidence is high in the exact conditional algebra; a valid alternative meeting every stated premise or a failed projective/ellipse step would change those conclusions. Operational relevance remains uncertain until actual information-source and acquisition choices are supplied. Continuous observation and physical motion questions remain pending. Full raw workflow, realistic512×512×64hidden-truth simulation and owner-data/reference parity are unfinished.
