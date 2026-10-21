# Identifiability for a quarter-period two-site calibration profile

**Result.** In the selected finite model, a known two-site emission profile can determine unknown exposure phases, relative field powers, brightness and the shared detection kernel even when the two side fields have equal power. The sufficient conditions are a fixed known axial mode and origin, real positive fields, at least five distinct actual phases, and kernel support spanning at least three distinct known axial cosine values. The proof below compares every admissible equal-data alternative in that same information set. It establishes exact uniqueness, including the common-normalized responses; it supplies no estimator or stability guarantee.

The two sites have unequal positive weights and differ in lateral illumination phase by pi/2. That known spatial asymmetry supplies information absent from a single point. This is conditional mathematics within the [selected periodic scalar model](../models/synthetic-3d-acquisition-v1.md), not evidence that an instrument supplies the profile or field constraints. The [preceding information report](relative-phase-invariants.md) treats the point and common-character profile cases. The [task contract](../tasks/two-site-phase-information.md) records documentary scope and verification duties. No numerical experiment was run.

## Information and target

| Quantity or information | Status in this theorem | Consequence or limit |
|---|---|---|
| Anchored profile p=a delta_0+b delta_ex, a>b>0, a+b=1 | Known exactly, including weights and anchor | Arbitrary unknown beads are outside the claim |
| Signed integer lateral carrier | Supplied, with phase increment pi/2 at ex | Its physical unaliasing is not inferred |
| Native integer axial mode, plane coordinates and origin | Supplied and fixed for all compared alternatives | Unknown-mode/origin alternatives are unclassified |
| Real positive balanced fields | Declared restricted field family; power gamma is unknown | Unknown relative field phases are outside the claim |
| Actual exposure phases | Unknown, at least five distinct modulo 2 pi | Nominal phase commands are not used as actual phases |
| Brightness B and kernel h | Unknown; B>0, h>=0, unit mass, sole maximum at zero | The peak condition fixes the kernel origin; no kernel truth is supplied |
| At least three occupied axial cosine values | Explicit sufficient condition on h and the supplied mode | Not a necessity claim or an operational support test |
| Compensated responses | K0=h, K1=2 sqrt(gamma tau) C h, K2=gamma h | One common brightness normalization; relative order gains retained |

All arrays and all labeled exposures are observed without noise in the mathematical claim. The target equality is literal in this anchored, signed, fixed-field-phase convention. A larger common phase/reflection quotient would weaken the target; independent unknown order gains are not admitted. Absolute optical throughput and physical field amplitudes remain outside normalized illumination.

## Model and claim

Use the finite periodic model and exact raw equation in [the analytical dependency](../plans/relative-phase-public-dependencies.md#concrete-successor-recommendation). The known anchored profile is p=a delta_0+b delta_ex, with a>b>0 and a+b=1. The supplied integer lateral carrier has phase increment pi/2 at ex, so its lateral cycle has length divisible by four. Write T h[z,y,x]=h[z,y,x-1], with circular indices. All native samples and labeled exposures are present. The axial and lateral sample counts are Nz and Nx; ex is one x grid step.

The shared kernel h is nonnegative, has unit total mass, and has a unique global largest sample at zero. Brightness B is positive. The balanced side-field power is gamma in (0,1/2), tau=1-2 gamma, and q=sqrt(gamma tau)>0. Fields are real positive in the fixed declared gauge. The actual exposure phases eta_p are unknown, with at least five distinct values modulo 2 pi. Thus the sampled columns 1, cos eta, sin eta, cos 2 eta, sin 2 eta have rank five: a vanishing nonzero degree-two trigonometric polynomial, multiplied by exp(2 i eta), would be a polynomial of degree at most four with five distinct unit-circle roots. Nominal phase commands supply no extra information.

Fix the actual known native axial mode ell and origin, with relative field phase xi=0. Write omega=2 pi ell/Nz, C(z)=cos(omega z), J=C h, and H_z=sum_xy h[z,y,x]. The physical axial frequency is ell/(Nz dz) cycles/µm when dz is the supplied axial spacing in µm. Assume

    number of distinct C(z) with H_z>0 >= 3.                 (I)

Here gamma is each side field's power divided by total field power; tau is the corresponding central fraction. B and D have expected-electron units. h, a, b, gamma, tau, q and the intensity factors are dimensionless; angles use radians. No absolute field-amplitude scale is recoverable from normalized illumination.

The raw model is

    D_p/B = a h (1+2 gamma cos 2 eta_p)
          + b T h (1-2 gamma cos 2 eta_p)
          + 4 q [a cos eta_p J - b sin eta_p T J].         (1)

At the two emitting sites the local phases are eta and eta+pi/2. The latter changes cos(2 eta) to -cos(2 eta) and cos eta to -sin eta, which checks both shift coefficients in (1). For example, a=2/3, b=1/3, gamma=tau=1/3 and eta=0 give intensity factors 3 and 1/3 at z=0, matching direct squared fields. This is a symbolic sanity check, not a generated-data experiment.

Claim: any second admissible tuple in this same information set giving every raw sample in (1) has gamma'=gamma, eta'_p=eta_p modulo 2 pi, B'=B, and h'=h. In particular the compensated common-normalization response arrays K_0=h, K_1=2 q J, K_2=gamma h and their signed partners agree exactly. No independent order gains or enlarged response quotient are needed. Direct expansion gives c0=B(aI+bT)h, c1=2Bq(aI+i bT)J and c2=B gamma(aI-bT)h. The latter two profile operators are also invertible because a>b. Known-profile compensation and one common division by B give the stated K arrays.

## 1. Axial totals leave a single positive scale

Put d=a-b>0 and define exposure vectors

    F_p = 1+2 d gamma cos 2 eta_p,
    G_p = 4 q (a cos eta_p-b sin eta_p).

The rank-five phase design makes F and G linearly independent. Lateral summation of (1) gives

    S_p(z)=B H_z [F_p+C(z) G_p].                           (2)

Equal-data alternatives have positive H'_z at every occupied plane: the nonzero observed vector S(z) cannot be produced by H'_z=0. At those planes,

    F'+C(z)G' = s_z [F+C(z)G],  s_z=B H_z/(B'H'_z)>0.     (3)

Two distinct C values give two independent observed directions and identify the same two-dimensional span for F,G and F',G'. On this span the transformation in (3) has eigenvector directions (1,C). Three distinct C values force it to be scalar: a nonscalar linear map in two dimensions has at most two distinct eigenvector directions. Therefore

    F'=k F,  G'=k G,  k>0.                                (4)

No phase average, known zero-order image, or full continuous phase curve was used.

## 2. The anchored peak plane fixes its spatial shape

Let v=h[0,:,:]. At z=0, C=1, and

    D_p[0,:,:]=B [a A_p v+b L_p T v],
    A_p=1+2 gamma cos 2 eta_p+4 q cos eta_p,
    L_p=1-2 gamma cos 2 eta_p-4 q sin eta_p.               (5)

A,L are independent by the rank-five design. Also v,Tv,T^2v are independent. Otherwise a nonzero real polynomial of degree at most two annihilates v under the finite periodic shift. Since v is nonnegative with positive sum, its shift spectrum includes the eigenvalue 1. Any other supported root of that polynomial must be real: a nonreal root would require its conjugate as well as 1. The only real roots of unity are 1 and -1. The periodic shift is diagonalizable, so T^2v=v. That repeats the maximum two lateral samples away. The cycle has at least four sites, contradicting the unique maximum at zero.

The rank-two raw slice in (5) consequently identifies span(v,Tv). The alternative also has this span, so v'=r v+s Tv and Tv' lies in span(v,Tv). Independence of v,Tv,T^2v forces s=0, hence v'=r v. Nonnegativity and nonzero mass give r>0. Coefficient comparison in (5) yields

    A'=lambda A,  L'=lambda L,  lambda=B/(B'r)>0.         (6)

Since F+G=a A+b L on this plane, (4) and (6) imply lambda=k.

## 3. The finite phase circle removes that scale

Write c_p=cos eta_p, s_p=sin eta_p, u_p=cos 2 eta_p. Equation (4) gives

    gamma' u'_p=k gamma u_p+(k-1)/(2d).                   (7)

Combining (7) with A'=k A and L'=k L gives

    q' c'_p=k q c_p-b(k-1)/(2d),
    q' s'_p=k q s_p-a(k-1)/(2d).                         (8)

Taking squared norms and using c_p^2+s_p^2=1,

    q'^2 = k^2 q^2 - k q (k-1)(b c_p+a s_p)/d
           + (k-1)^2 (a^2+b^2)/(4d^2).                 (9)

If k differs from one, every actual phase has the same value of b cos eta+a sin eta. A line meets the unit circle in at most two points, contradicting the five distinct actual phases. Thus k=1. Equations (8)-(9), with q,q'>0, give q'=q and each phase agrees modulo 2 pi.

Equation (7) then gives (gamma'-gamma) cos 2 eta_p=0 for every exposure. Five distinct phases cannot all lie at the four zeros of cos 2 eta modulo 2 pi. Hence gamma'=gamma.

## 4. Brightness and the complete kernel follow

With the actual phases now equal, rank-five coefficient comparison in (1) uniquely identifies the constant coefficient:

    B (a I+b T)h = B' (a I+b T)h'.                        (10)

The operator a I+b T is invertible because a>b>0 and T has unit-modulus eigenvalues. It follows that B h=B' h'. Unit mass then gives B=B' and h=h'. All declared compensated responses agree exactly.

As a consistency check, every scale was positive; gamma stays in the declared interior; the proof used only finitely many supplied exposure phases; and the shift and axial multiplication constraints were retained together. Inverting the ordinary profile operator alone did not reduce the problem to the earlier point-bead theorem.

## Boundaries and next contract

| Changed condition | What this result establishes |
|---|---|
| Strictly positive h, native cosine cycle with at least three values | The support premise holds; a native axial cycle length at least four suffices |
| Some zero kernel planes, at least three occupied cosine values | The theorem still applies; one shared lateral Fourier mode across those planes is unnecessary |
| Fewer than three occupied cosine values, short axial cycle, fewer distinct phases | This proof does not classify uniqueness or ambiguity; failure of a sufficient condition proves neither |
| Missing samples or exposures, changed/unknown native mode or origin | Unclassified by this theorem |
| Unknown relative field phases, unequal side fields, unanchored profile or nonunique kernel peak | Different information sets; no transfer of this conclusion is asserted |
| Finite precision, noise, nearly degenerate profile/phase/support | No conditioning bound, rank tolerance, accuracy promise or numerical method is established |

The shifted-plane independence argument uses nonnegativity, a positive plane at the anchored zero peak, and a lateral cycle of at least four. The quarter-period carrier guarantees that cycle length is divisible by four. The axial support condition excludes a one-value or two-value cosine cycle, but does not demand complete positive axial support.

The concrete dependency conclusion is that this two-site family has a proved informative conditional branch. Failure of the earlier point ambiguities alone was insufficient; the equal-data proof resolves the stated family. No generic successor report is needed. Before a numerical self-calibration contract, the owner or an independent information source must settle the actual calibration support/profile, applicable field constraints, supplied or inferred native mode/origin, desired response quotient, and weak-information/finite-precision outcomes. Unknown mode/origin and reduced-support questions remain optional separate analytical scopes, not silently adopted premises. Existing known-phase calibration interfaces retain their supplied inputs.

Independent future expectations can use direct squared-field expansion at the two sites, exact finite convolution sums and independent phase-polynomial/projective derivations. True tuples may define analytical examples, but may not provide a proposed raw estimator's initialization, search interval, support, rank threshold or tolerance. Numerical behavior would require a concrete contract and fresh blind A/B, restricted C and fresh D under [repository instructions](../../AGENTS.md).

Full raw calibration/reconstruction, realistic 512×512×64 hidden-truth simulation and owner-data/reference parity remain unfinished. Continuous observation and physical motion remain separate unresolved choices. This report changes no runtime, tests, fixtures, dependencies or delivery gates.
