# Raw calibration needs an information source for its phase and carrier labels

**Version 1.0.** A known finite bead profile does not, by itself, make an unknown calibration carrier identifiable when each order response is free. Exactly five exposures also cannot identify five unknown phases by minimizing an unrestricted five-component separation residual. Extra information can change both conclusions. The necessary distinction is which transfer, spatial, phase and acquisition constraints are independently available.

This analytical report adds an information dependency to the earlier [carrier representation](continuous-carrier-intake.md) and [motion](raw-phase-motion-intake.md) reports. It adopts no observation or motion model, estimator, threshold, API or experiment. All results below are conditional algebra; no generated data or scientific performance was measured. The current public finite-bead operation still requires supplied actual phases, integer carrier and a known native bead profile. Calling those inputs “calibration” does not infer them.

## Equations, coordinates and three different kinds of transfer knowledge

The opened [Gustafsson et al. primary paper, equations 5–9, pp.4958–4959 and transfer discussion p.4963](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) distinguishes effective order kernels during focal scanning, harmonic phase shifts and bead-based transfer measurement. Its phase separation assumes known shifts; its bead treatment uses additional optical symmetry and support assumptions. Those premises are not consequences of acquiring five images. This report derives the following conditional finite-model consequences independently. The paper does not select this project's finite observation representation.

Use real exposure arrays y_p, p=1,...,P, with spatial coordinates r_n in micrometres (µm). A lateral carrier q has units cycles/µm; phases phi_p are radians. For signed active orders m in {0,±1,±2}, a candidate sampled circular model is

```text
y_p = sum_m exp(i*m*phi_p) K_m * [s[n] exp(i*2*pi*m*q·r_n)]
Y_p(k) = sum_m exp(i*m*phi_p) H_m(k) V_m(k;q,s).
```

Here * is declared circular convolution, H_m is its discrete Fourier transform (DFT), and V_m is the DFT of the finite modulated samples. Negative orders satisfy K_-m=conj(K_m) when s is real, equivalently H_-m(k)=conj(H_m(-k mod N)); a real zero-order kernel is also required for real predictions. Individual positive-order images and spectra can be complex. Complex measurements without these reality constraints form a different problem. The opened [NumPy convention](https://numpy.org/doc/stable/reference/routines.fft.html#implementation-details) uses a negative forward exponent and inverse factor 1/M for M samples. These signs are used below.

| Transfer premise | What is independently fixed | What cannot be concluded automatically |
|---|---|---|
| Known transfer | Signed complex H_m, normalization, coordinate/phase gauge and reuse relation | Fixed transfer need not be informative; zeros, symmetries and point cases can leave ambiguities |
| Calibrated transfer | H_m estimated from separate raw observations through a stated calibration model and labels | A transfer fitted with unknown labels can retain their ambiguities; a stored array or source label does not make its gauge independent |
| Unknown independent order responses | Each complex H_m(k) can vary freely, subject only to the stated reality/normalization constraints | Spatial carrier factors and phase-origin changes can be absorbed into those responses |
| Unknown but structured transfer | A common detection kernel, axial factors, known support/symmetry or a finite optical parameterization | Neither the free-response impossibility nor a known-transfer uniqueness claim applies without checking that structure |

The existing [phase estimator](../contracts/phase-step-estimation-v1.md#stored-input-periodic-model-and-normalization) fixes full complex transfers and one integer carrier. The [finite-bead calibration](../contracts/finite-bead-compensation-v1.md#selected-model-and-observable-purpose) instead measures responses conditional on known phases, profile and carrier. These are different directions of inference. The narrow source check confirms that calibration calls known-phase separation and divides by P[k-m*kc]; it does not estimate these labels.

## Five exposures: an exact separation counterexample, with its limits

Write each real image as a row of a P-by-M matrix Y. Define

```text
X(phi)[p,:] = [1, cos(phi_p), sin(phi_p), cos(2*phi_p), sin(2*phi_p)]
Y = X(phi) C.
```

C contains five real coefficient images. In the public separator, c_m=(B_m-i*C_m)/2, so the same model is dc+2 Re(c1 exp(i phi)+c2 exp(2i phi)). For P=5, take ANY other phase vector psi for which X(psi) is invertible. Then

```text
C' = inverse(X(psi)) X(phi) C
X(psi) C' = Y.
```

Thus zero separation residual cannot choose phi from psi when these coefficient images are unrestricted. This remains a real-data example: X and C' are real. It is stronger than counting parameters and does not need noisy data, a failed solver or an experiment. Five distinct exact phases modulo 2*pi make the ideal degree-two trigonometric design invertible: multiplying a vanishing trigonometric polynomial by z^2 gives a degree-at-most-four polynomial with five distinct unit-circle roots. Numerical rank near coincident phases is a separate stored-input issue.

This is not a proof that five exposures can never identify phases. Requiring C to arise from one known bead/specimen through fixed or physically linked kernels reduces the permitted C. An alternative C' may violate those constraints. Likewise, a completely free five-by-five mixture matrix has a general change-of-basis ambiguity; harmonic phase rows lie on the much smaller curve X(phi), and arbitrary matrix transformations need not preserve it. “Five unrestricted mixtures” and “five unknown harmonic phases under a fixed spatial forward model” are different contracts.

For example, the already [selected finite scalar-field model](../models/synthetic-3d-acquisition-v1.md#illumination-and-axial-scan) has K0=h, K2=gamma*h and K1=h*(u*exp(-i*2*pi*ell_z*nz/Nz)+v*exp(i*2*pi*ell_z*nz/Nz)), where u,v,gamma arise from the same three field amplitudes. Consequently H2=gamma*H0 and H1(k)=u*H0(k+ell_z*e_z)+v*H0(k-ell_z*e_z). A general five-image mixing does not preserve those relationships or the nonnegative unit-mass h with its fixed peak. This existing development-model structure is an informative alternative to free responses; it proves no universal joint-identifiability theorem and is no new instrument assumption.

For P>5, the alternative phase set must also satisfy Y in the column space of X(psi). Redundant exposures and sufficiently independent spatial coefficient images can constrain that space. Merely adding frames proves no uniqueness: repeated labels, low spatial coefficient rank, absent harmonics or compatible alternative phase curves can still defeat it. The current separator's represented binary64 trigonometric rules and rank cutoff are numerical policies, not new information about actual exposure labels.

At five equally spaced phases phi_p=2*pi*p/5, replacing phi by psi=2*phi permutes the five harmonic characters modulo five. Relabelling freely fitted coefficient images preserves the observations. This is an unknown-design/order-label alias; a supplied known design still separates its five distinct characters. Additional genuinely distinct exposures or fixed physical order constraints may break the relabelling.

## A finite bead can fail to determine the carrier exactly

First use the current periodic integer-carrier setting, where the meaning is already explicit. Let a known normalized profile p be translated to anchor b, with brightness B>0, and let P(k) be its DFT. Known separation phases give order spectra

```text
C_m(k) = B H_m(k) exp[-i*2*pi*(k-m*kc)·b/N] P(k-m*kc).
```

For an alternative integer carrier kc', define, wherever its denominator is nonzero,

```text
H'_m(k) = H_m(k)
          * exp[i*2*pi*m*(kc-kc')·b/N]
          * P(k-m*kc) / P(k-m*kc').
```

Substitution gives the identical C_m, hence identical raw observations at every exposure. H'_0=H_0. For real p, the negative-order relation is preserved when positive/negative rows are transformed together. A normalized zero-order response and its positivity can remain unchanged. Therefore a single finite profile, even with known anchor and nonzero spectrum everywhere, cannot determine kc against unrestricted independent side-order responses. Spatial extent alone does not cure this problem. The current all-node profile-transfer certificate permits division; it supplies no independent carrier information.

Zero denominators qualify this construction. If the alternative profile factor is zero where an observed order is nonzero, that candidate is impossible under finite responses. If both vanish, that sample constrains neither its response nor a division there. Known support, bounded response, common-kernel factorization or axial-only factors can also invalidate H'. Such constraints must be declared and independently justified; the ratio may violate them. The current profile certificate is not permission to replace an unknown physical support with hidden simulator truth.

For a noninteger sampled carrier, replace the shifted P factor by the exact finite transform V_m(k;q,p_b). Where alternative V'_m is nonzero, H'_m=H_m V_m/V'_m gives the same absorption. The [earlier report](continuous-carrier-intake.md#exact-finite-sum-derivation-and-a-small-counterexample) derives why V is generally a finite-sum mixture, rather than an integer permutation. A continuous optical model must instead use its declared continuous profile and transfer queries. The algebraic argument is conditional on allowing the resulting responses; it does not choose between these models.

## Information that can legitimately break particular ambiguities

Known spatial structure can help when it is not simultaneously absorbed into a free response. For a simple informative alternative, take a known identity detection operator, one known nonzero real first-harmonic amplitude a1, known baseline a0>=2*abs(a1), known B and known profile with p[n]>0 at successive one-dimensional sites. This amplitude condition makes the illumination nonnegative. Let

```text
z_p[n] = (y_p[n]/(B*p[n]) - a0)/(2*a1)
       = cos(omega*n + phi_p),  omega=2*pi*q*Delta.
z_p[n+2] + z_p[n] = 2*cos(omega)*z_p[n+1].
```

When the denominator z_p[n+1] is nonzero, three such samples determine cos(omega). More samples can cover a zero denominator. This leaves sign and sampling aliases; an independently declared domain and further nondegenerate samples are needed to recover a representative phase. The example proves that finite extent can carry information under fixed transfer. It is not an adopted estimator, a minimum sample theorem for general optics or a promise for arbitrary beads. A fixed asymmetric complex transfer may distinguish signs that this real cosine example cannot.

Multiple known bead positions can add information even with unknown shared responses. In the integer periodic model, acquire the same profile at positions b_l with the same H_m, q and a common known phase reference. At a common nonzero frequency/order factor, with known brightnesses or independently determined relative scales,

```text
(C_l,m(k)/B_l)/(C_j,m(k)/B_j)
  * exp[i*2*pi*k·(b_l-b_j)/N]
  = exp[i*2*pi*m*kc·(b_l-b_j)/N].
```

H and P cancel. Two-dimensional carrier recovery needs informative displacement directions; a single direction constrains only a projection. Wrapped phase, order gcd and the displacement lattice leave aliases. The bead displacements, relative brightness and common phase reference must be measured/justified or separately estimated. Unknown independent phase offsets alpha_l can absorb the carrier term again. A simultaneous known arrangement can enforce common exposure phases, but overlapping images, unknown individual brightnesses and common-transfer validity need their own observation contract. One bead moved by an unmeasured stage is not a set of known positions.

A single aggregate multibead image does not automatically provide these ratios: it still gives one product H_m(k)*S(k-m*kc), which can retain carrier absorption. Separately identifiable contributions or multiple shared-response observations are needed for the cancellation above.

| Available information | Distinct information gain | Remaining failure/ambiguity |
|---|---|---|
| Independently measured actual phase labels | Makes harmonic separation a known-design problem | Phase origin/reuse, rank, measurement error and carrier still matter |
| Independently measured carrier and coordinate anchor | Removes its inference from profile division | Sampling aliases, units and physical versus modular frequency meaning remain |
| Known finite profile plus fixed informative transfer | Spatial modulation can constrain q and phases | Zeros, narrow support, sign/alias and nuisance-scale failures remain |
| Known finite profile plus free independent H_m | Profile zeros can reject some candidates | The exact ratio transformation otherwise preserves observations |
| More than five phase exposures | Adds phase-curve consistency beyond unrestricted interpolation | Low spatial rank and alternative compatible phase sets remain possible |
| Multiple known positions with shared transfer/reference | Cancels shared response and yields carrier projection phases | Lattice aliases, collinear positions, unknown brightness/reference and zeros remain |
| Known optical factorization/support/symmetry | May rule out absorbed responses or order exchanges | Must establish actual restrictions; symmetry can also create ambiguities |
| More unlabelled data with unconstrained per-acquisition responses | No guaranteed shared constraint | Each response can absorb its own nuisance changes |

## Gauges, aliases and rank failures to retain

These are observation-preserving transformations only under the stated freedoms:

| Transformation | Required freedom and exact effect |
|---|---|
| Scale | B->cB, H_m->H_m/c for c>0 leaves all predictions unchanged; a fixed H0 mass removes this particular normalization freedom, not absolute detector/emitter calibration |
| Common phase | phi_p->phi_p+alpha, H_m->H_m exp(-i*m*alpha) preserves data when responses/gains are free; fixed independent complex calibration need not permit it |
| Anchor versus response origin | b->b+t, H_m(k)->H_m(k) exp[i*2*pi*(k-m*kc)·t/N] preserves the integer bead formula when the response-origin constraint is free; a fixed unique kernel peak can forbid it |
| Coordinate origin | Moving origin O to O+a gives r'=r-a and phi'=phi+2*pi*q·a; assigning r'=r+a instead gives the opposite phase sign |
| Order/sign exchange | q->-q, phi->-phi, K'_m=K_-m preserves the signed sum if order responses may be relabelled; a fixed asymmetric transfer or measured order labels can forbid it |
| Sample alias | At anchored native sites q_a->q_a+h_a/(g*Delta_a) leaves all active modulation unchanged, h_a integer, g the greatest common divisor of nonzero active orders; an off-grid anchor adds a compensable phase. This is a sampled-kernel alias, not equality of physical optics at aliased frequencies |
| Harmonic phase alias | phi_p->phi_p+2*pi*j_p/g independently per exposure leaves active harmonics unchanged. If only even orders are active, phases are modulo pi; no fundamental activity means no fundamental-phase information |

Within the existing integer-bin domain, the alternative carrier must itself remain integer: for every active m, m*delta_kc_a=0 modulo N_a on each axis. The continuous-frequency gcd expression alone does not establish that an alternative belongs to that integer domain.

The active set must mean actually nonzero contributing order signals, not merely allocated rows. With no side signal there is no phase/carrier information in that component. A point at the coordinate origin gives V_m independent of q for fixed sampled kernels. A known nonzero point elsewhere gives only phi_p+2*pi*q·b; a carrier change can be offset in every phase. Constant specimens can be informative under appropriate fixed transfer and modulation, so “no texture means no information” is not a valid universal rule.

For any proposed differentiable model f(theta,eta), where eta contains the nuisance parameters actually fitted, a parameter perturbation dtheta is locally invisible if J_theta*dtheta lies in the range of J_eta. Equivalently, (I-J_eta*J_eta^+)J_theta has a null direction, with real coordinates for real observations. This is a local differential criterion away from rank transitions. It gives no global uniqueness, noise confidence interval or numerical cutoff. A later contract must state which nuisance directions are included; fixing a transfer fitted from the same ambiguous data can create spurious apparent information.

Preserve physical signed frequency domains. Native even-grid Nyquist identifies + and - endpoints only at native sample positions. The family cos(pi*x)+b*sin(pi*x) agrees at every integer x and differs between them. Fractional motion, continuous profile evaluation or interpolation needs an explicit extension. A harmonic is field-periodic only when each active m*kappa_axis is integer; second-order-only half-bin carriers are a legitimate periodic case. None of the alias or sign arguments authorizes filling missing physical calibration coverage with zero.

## Minimum legitimate input boundary and the next meaningful contract

There is no model-independent minimum list or universal exposure count. For one concrete **proposed conditional composition**, the existing stationary discrete periodic integer-carrier operations could accept the following information. This proposal selects no new representation or physical motion law and is not an approved public workflow:

| Quantity | Legitimate source/category | Required distinction from hidden truth |
|---|---|---|
| Raw bead and specimen arrays; grouping/layout, spacing/units, coordinate anchor and relevant acquisition order | Observations and measured/declared metadata | Do not infer absent physical meaning from array shape or simulator labels |
| Camera offset/response and output units | Independently supplied calibration or separately contracted observation-derived estimates | Generator camera coefficients cannot silently supply corrections |
| Actual calibration phase labels and integer carrier | Independently measured acquisition information, with reference/uncertainty, or separately contracted inference | Nominal commands are initialization/commands; hidden actual phases/carrier are not metadata |
| Relative native bead profile with its index-zero anchor convention | Supplied independently known profile/calibration; translated bead location remains observed/fitted | A nominal sphere diameter does not determine discrete site weights, pixel integration or subvoxel placement; no true bead-location input is required |
| Response reuse, coordinate offset and calibration/specimen phase-reference relation | Independent acquisition declarations or separately inferred quantities | A chosen gauge labels an equivalence class; it does not measure an unknown phase-reference difference |
| Specimen initial phases and carrier domain, if estimated | Commands/physical bounds fixed independently or an observation-derived procedure | No truth-centered start, candidate list, bounds or stopping policy |
| Profile-conditioning minimum, interpolation/coverage, reconstruction window/mask/ridge and numerical controls | Explicit scientific/numerical contract and legitimate settings | No tuning to hidden specimen/optics, held-out answers or returned diagnostics as truth |
| Actual specimen, phase errors, drift, optics and withheld reference output | Evaluator only | May assess results; cannot select support, interpolation, references or tolerances |

The present APIs can form a conditional calibration-to-reconstruction composition only after those declarations are supplied. It would still not satisfy the roadmap's unknown-nuisance/full raw workflow exit merely by passing generator values as “known.” For a truth-hidden simulation, any independently measured metadata must be modeled as an observation with its own declared meaning; exact simulator state cannot impersonate that observation. Zero motion may be a stated conditional scenario but cannot silently settle the pending physical-motion choice.

An absolute instrument phase is unnecessary when specimen exposure phases, including their common offset, are fitted in the declared calibration gauge. The adapter may declare a common reference (delta=0), and the fit reports phases in it. That convention does not measure independent calibration step errors or resolve unknown physical coordinate/motion differences. Likewise the profile anchor convention is distinct from the translated bead location derived from compensated dc observations.

The next meaningful numerical contract must therefore name an **information source**, before selecting an optimizer: (1) measured phase/carrier acquisition metadata plus explicit uncertainty/reuse semantics; or (2) a particular self-calibration experiment with independently justified transfer structure or shared known spatial probes. The first is simpler conditional composition. The second can reduce caller knowledge, but needs a concrete model and an identifiability assessment; five images of one bead with free responses are insufficient in the cases derived above. Neither branch is selected here. The pending observation and motion questions remain pending unless an actual human reply resolves them.

Independent expectations can use symbolic X(psi)^-1 X(phi) substitution, the response-ratio identity, direct finite real-space sums, known-kernel cosine recurrence, multiple-position cancellation and null-direction checks. Positive controls must violate the premise of an impossibility claim, rather than being rejected to make it universal. These are expectation possibilities, not authored tests or acceptance tolerances. Blind A/B receive a later concrete approved contract and permitted public context; this nonblind discovery report, source notes, history and coverage maps are excluded.

```text
independent phase/carrier information OR declared informative shared structure
 + chosen observation representation / calibration reuse / truth boundary
 -> concrete calibration and nuisance contract -> fresh blind A/B -> restricted C / fresh D
 -> exact local + separate native platform gates -> public raw composition

physical motion choice + actual acquisition/reference facts -> motion contract
completed phases2–6 -> phase7 raw workflow -> phase8 512x512x64 truth-hidden simulation
 -> phase9 owner-data/reference parity
```

Confidence is high in the exact counterexamples and conditional positive alternatives. General identifiability for an owner's actual microscope remains unresolved without its acquisition information and transfer restrictions. A measured phase/carrier source, a specified optical factorization or a concrete shared-probe acquisition could change the next contract. Without one, the actual blocker is missing scientific input meaning; another generic gauge report would not advance the roadmap.
