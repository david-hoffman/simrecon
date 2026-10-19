# A continuous carrier needs a declared finite observation model

**Version 1.0.** A noninteger illumination carrier can be evaluated at detector sample positions. Its finite discrete Fourier transform generally mixes many frequency bins. That is different from rounding a carrier to an integer, moving one Fourier bin fractionally, or evaluating a physical continuous transfer function between samples. These alternatives can agree at selected integer cases and disagree elsewhere. A later estimator needs an explicit representation and objective before implementation or tests.

This report selects none of them. It compares their meanings, derives distinguishing cases and recommends a narrow next contract for consideration. The earlier [raw-phase motion report](raw-phase-motion-intake.md) leaves the first physical motion mechanism pending. No later human answer was found at this report's admission. Carrier representation can be investigated independently; it does not answer that motion question. No generated-data experiment or performance measurement was made.

## What is already settled

The [fixed-transfer phase estimator](../contracts/phase-step-estimation-v1.md#stored-input-periodic-model-and-normalization) uses a real signed nuisance specimen, supplied complex transfers and an integer lateral carrier on a finite periodic grid. It profiles unweighted least squares over that specimen and fits exposure phases in a fixed calibration gauge. The [observable reduction](../contracts/observable-volume-phase-estimation-v1.md) and [Fourier-block execution](../contracts/fourier-block-phase-estimation-v1.md) preserve that objective. Their carrier shifts are modular permutations. Changing the carrier to a noninteger changes the forward operator and can change structural nullspaces, blocks and numerical rank behavior.

[Volume recombination](../contracts/volume-recombination-v1.md#signed-window-and-estimator) instead places integer bands without wrapping in a declared enlarged signed output window. The older [2D fractional reconstruction](../contracts/known-parameter-reconstruction-v1.md#forward-model-and-fourier-conventions) explicitly selects complex bilinear band/transfer interpolation and zero outside closed detector coverage. Its [comparison](reconstruction-comparison.md) distinguishes estimator arithmetic from physical interpolation bias. Neither operation selects a continuous-carrier 3D estimation model.

[Physical-frequency empirical sampling](../contracts/empirical-frequency-sampling-v1.md#public-boundary-and-consumer-meaning) evaluates an already selected complex trilinear transfer interpolant at caller-supplied cycles/µm coordinates. It interpolates no detector observations and supplies no carrier estimate. A continuous transfer query alone does not define a continuous observation model.

Evidence was read through selected public contracts and the primary paper, with independent nonblind M01/S01 discovery retained locally. The original admitted paper is 1,699,729 bytes, SHA-256 `b91f2697d05bb8c77ab88179034548003da919cf287856278af379e7104baf09`, DOI `10.1529/biophysj.107.120345`; equation/page locators appear below. The opened NumPy documentation identified version 2.5; the opened SciPy page identified 1.18.0, while the lock selects NumPy 2.5.3/SciPy 1.18.1. These pages document conventions, not a claim of package-version identity. No ignored reference-source body was needed or copied. All new conclusions below are conditional mathematical analysis, not measured instrument settings.

## Coordinates and four alternatives

Let `n=(nz,ny,nx)` index an explicitly anchored array, `K=(Nz,Ny,Nx)`, and spacings `Delta=(dz,dy,dx)` be in micrometres (µm). Let `q=(qy,qx)` be lateral cycles/µm, with zero axial component. Define `kappa=(Ny*dy*qy,Nx*dx*qx)` in detector frequency bins and the phase at position `r_n` as `2*pi*q·r_n + phi_p` radians. One bin is `1/(N*Delta)` cycles/µm on an axis. For example, 0.5 cycles/µm on 100 samples at 0.1 µm spacing means 5 bins: `(cycles/µm)*(samples)*(µm/sample)=cycles` over the field. No physical calibration value is inferred from this dimensional example.

| Candidate representation | Observation meaning | Consequences requiring a later contract |
|---|---|---|
| A. Finite sampled modulation plus circular filtering | Multiply the finite specimen samples by the declared noninteger phase ramp, then apply each fixed finite convolution kernel | Exact finite operator; periodic continuation of the *sampled product* can have an illumination seam when an active harmonic fails field periodicity; integer Fourier blocks generally disappear |
| B. Continuous Fourier-basis specimen and optical filtering | Declare a continuous periodic specimen basis, multiply by a continuous illumination, apply a continuous optical kernel, then sample | Shifted continuous modes query physical transfers, including frequencies absent from detector bins; continuous extension and aliases must be explicit |
| C. Interpolate measured Fourier bands for overlap/recombination | Declare how stored complex band data and transfers are evaluated at fractional frequencies, then compare or combine them | Kernel, physical coverage, weighting, order of operations and interpolation bias define a separate estimator; not generally equivalent to A or B |
| D. Finite exterior and detector crop | Declare specimen/kernel outside the measured field, form linear imaging and then crop detector samples | Exterior support or nuisance values, crop, padding, timing and likelihood become model inputs; padding alone supplies none of them |

These are model families, not interchangeable implementations. A Fourier interpolation can implement A exactly if it uses precisely the same finite-sum kernel, origin and index representatives. A continuous basis can also be chosen to represent sampled data, but its behavior after multiplication/filtering is additional meaning. A fixed periodic *illumination function* on the same field requires `m*kappa_a` to be integer on each axis a for every active harmonic m. Integer kappa is necessary when a nonzero fundamental is present. With only orders 0 and ±2, a half-bin declared carrier has integer active shifts and can be periodic without an illumination seam. If an active harmonic fails this condition, A defines a finite sampled vector that is then periodically repeated; it does not claim that the unbroken sinusoid has that period. A noninteger base-carrier declaration alone therefore implies neither dense active coupling nor a seam.

## Exact finite-sum derivation and a small counterexample

The following is derived algebra, not an executed simulation or selected product behavior. On one axis use the negative-exponent DFT `S[l]=sum_n s[n]*exp(-2*pi*i*l*n/N)` and its inverse with factor `1/N`. These conventions match the opened [NumPy transform documentation](https://numpy.org/doc/stable/reference/routines.fft.html#implementation-details). For signed order m define `v[n]=s[n]*exp(2*pi*i*m*kappa*n/N)` on `n=0,...,N-1`. Substituting the inverse DFT gives

```text
V[k] = sum_l S[l] * D_N(l+m*kappa-k)
D_N(t) = (1/N) sum_(n=0..N-1) exp(2*pi*i*t*n/N).
```

At integer `t`, the inner geometric sum is one if `t=0 mod N`, and zero otherwise. Thus integer `m*kappa` gives the familiar modular shift. For noninteger t,

```text
D_N(t) = exp(pi*i*t*(N-1)/N) * sin(pi*t)/(N*sin(pi*t/N)),
```

with its removable limits supplied by the finite sum. It is generally nonzero for every l. In multiple axes the kernels multiply; unchanged axes retain their integer delta. This is exact for finite samples, with no claim about infinite-field optics.

For `N=2`, `s=[1,1]`, `m=1`, `kappa=1/2`, the sampled side harmonic is `[1,i]`. Its DFT is `[1+i,1-i]`. Both bins are nonzero. An integer relocation of the original `[2,0]` cannot give this result. Conjugate side harmonics can still be combined into real observations; a complex individual order is expected.

An off-grid evaluation of the finite transform `S(t)=sum_n s[n]*exp(-2*pi*i*t*n/N)` gives the same formula at `t=k-m*kappa`. Replacing unsigned sample coordinates by signed modular representatives changes wrapped samples individually and generally cannot be repaired by one global phase. Moving a physical coordinate origin instead changes every coordinate by the same offset and requires the corresponding declared phase adjustment. Agreement at stored integer bins alone is insufficient. Physical transfer interpolation and this observation interpolation concern different functions.

For A, an illustrative Fourier prediction is `sum_m exp(i*m*phi_p)*F_m[k]*V_m[k]`, where the finite modulation above defines V and F contains fixed detector-grid kernel eigenvalues. For B, a continuous specimen basis `sum_l a_l*exp(2*pi*i*f_l·r)` instead produces terms proportional to `a_l*H_m(f_l+m*q)*exp(2*pi*i*(f_l+m*q)·r_n)`. Here optical filtering occurs at the shifted continuous frequency. In A, it occurs after sampling/modulation, at detector eigenvalues. They agree only under additional compatible assumptions, not by the Fourier shift theorem alone. The primary [Gustafsson et al. paper, equations 5–9, pp.4958–4959](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) supplies the continuous effective-kernel theory; it does not select this project's finite discretization.

## Padding, endpoints and operation order

Spatial zero extension enlarges the declared exterior/period if spacing is fixed. With a new size L, the same physical q has `kappa_L=L*Delta*q`; retaining the old bin number changes q. Spectral zero insertion instead describes a chosen continuous Fourier-series extension sampled more finely over the same field of view, with its own scaling and endpoint rules. Zero padding used to calculate a declared finite linear convolution is a third use: it must cover that convolution's support before cropping. None is an automatic padding factor or evidence that unknown exterior specimen values are zero.

For an even N, native samples at Nyquist cannot distinguish `exp(+i*pi*x)` from `exp(-i*pi*x)` at integer x. The real family

```text
f_b(x) = cos(pi*x) + b*sin(pi*x),  b real,
f_b(n) = (-1)**n for every integer n.
```

gives different values at half samples for different b. A symmetric split, a one-sided complex lift, a restricted Nyquist-free subspace or an explicit continuous basis are different legitimate choices. Reality at native samples does not choose one. The opened [SciPy Fourier resampling documentation](https://docs.scipy.org/doc/scipy-1.18.0/reference/generated/scipy.signal.resample.html) describes periodic extension and special handling of unpaired even-length bins. That is useful evidence about conventions, not permission to adopt a resampler here. Candidate A needs no intersample specimen lift merely to evaluate illumination at the native sample positions; fractional spatial motion would need an additional convention.

Native modular negation also differs from physical-frequency reflection. An even source grid stores the canonical negative Nyquist endpoint. The [empirical point-sampling contract](../contracts/empirical-frequency-sampling-v1.md#query-geometry-and-physical-endpoints) evaluates negative orders by reflecting physical coordinates in all axes; its positive- and negative-order coverage hulls can differ. Missing calibration coverage is not a physical zero, periodic bridge or extrapolation license. A future consumer must settle the required endpoint representation explicitly.

Fractional relocation and nonconstant weighting need not commute. If C is a fractional mixing matrix and W is diagonal weighting, then `(W*C-C*W)[k,l]=(w_k-w_l)*C[k,l]`. Any nonzero mixed entry with unequal weights supplies a counterexample. The [paper, pp.4963–4964, reconstruction discussion](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) explicitly discusses noninteger phase-gradient shifts, sinc-like spreading and filter order. This motivates declaring the order of operations; it supplies no adopted Wiener parameter, apodization or edge treatment.

## Objective, gauges and information

One possible future extension of A would profile `J(q,phi)=0.5*min_(s real)||y-A(q,phi)s||^2` using all declared observations and fixed calibration. This is a conditional candidate, not a selected objective, optimizer, derivative, cutoff or threshold. An overlap objective in C has different observed coordinates, interpolation and potentially carrier-dependent coverage. Changing the fitted set with q can lower a raw score by discarding difficult observations. A later contract must define common comparison meaning and unavailable coverage, rather than infer that a lower number identifies the physical carrier. No likelihood/noise model follows from unweighted least squares.

Exact conditional ambiguities remain even for a perfectly implemented objective:

- On anchored native samples, changing q by integer sampling frequencies `(ay/dy,ax/dx)` leaves sampled modulation unchanged; a nonzero anchor contributes a compensable constant phase. This is a sample alias under fixed sampled kernels, not a claim that physical optics at all aliased frequencies are equal. Missing fundamental orders can create additional aliases: second-order-only modulation also repeats after a half sampling-frequency change, and its exposure phases are defined modulo pi.
- For a fixed physical point R and origin O, moving the origin to `O'=O+a` gives `r'=r-a` and requires `phi'=phi+2*pi*q·a` to preserve `2*pi*q·r+phi`. In contrast, assigning coordinates `r'=r+a` requires `phi'=phi-2*pi*q·a`. The coordinate map determines the sign. With freely fitted order gains, `phi_p -> phi_p+alpha` and `gain_m -> gain_m*exp(-i*m*alpha)` preserve predictions. Fixed calibration may remove those freedoms only when its gauge and reuse are justified.
- For a point specimen at r0 and fixed kernels, each side order depends on `phi_p+2*pi*q·r0`. Any q change can be absorbed into all phases by the opposite offset. At r0=0, the modulation does not depend on q at all. This exact counterexample applies to the stated finite model; additional independently available information can change it.
- Zero specimen or zero side transfers provides no carrier information. A narrow texture/transfer may constrain only a projection of q. Free specimen, phase, gain or motion can compensate one another. Local information rank and a small residual do not establish global uniqueness, physical accuracy or a confidence interval.
- The existing integer periodic motion/phase identity does not extend by replacing the integer carrier with a fractional value: a wrapped sample picks up an additional `exp(2*pi*i*m*kappa)` factor, generally different from the unwrapped sample. A global phase does not remove that sample-dependent seam.
- Carrier sign can be exchanged with order/phase labels when the model permits that exchange. Fixed asymmetric calibration can break the exchange, so universal sign ambiguity must not be asserted without its premise. Repeated/aliased candidate declarations remain meaningful provenance even when their predictions coincide.

The current integer structural-support reduction and orbit blocks cannot simply be carried over: dense fractional mixing can alter the observable subspace and its variation with q. New rank transitions, derivatives, minimum-norm representative and scalability need a concrete contract. This report sets no resource limit or feasibility claim for `(64,512,512)` z/y/x data.

## Input, truth and dependency ledgers

| Quantity | Legitimate estimator access | Hidden or unresolved information |
|---|---|---|
| Raw bead/specimen exposures, grouping, nominal commands | Observations plus explicit [raw declarations](../contracts/raw-acquisition-declarations-v1.md) | Commands are not actual phases; no owner acquisition supplied here |
| Pixel spacing, coordinate origin, scan/timing and boundary settings | Measured/declared metadata with units and provenance | Ground-truth simulator geometry cannot silently fill absent metadata |
| Camera maps, exposure scale, background and noise relation | Explicit supplied correction or separately contracted inference | True simulated coefficients are evaluator-only unless declared as known conditional inputs |
| Empirical complex transfers and gauge | Independently observed bead calibration through its contracted pipeline, with declared reuse | Simulator's exact optics, phase gauge, carrier and order gains are not automatic raw-workflow inputs |
| Initial carrier/search domain and nominal phases | Declared prior/acquisition information or observation-derived procedure | Hidden true carrier cannot initialize or restrict a search around truth without labeling that conditional task |
| Actual calibration phases/carrier and finite-bead profile | Current raw calibration uses these as explicitly supplied known inputs | An unknown-phase/carrier calibrator and unknown physical bead profile remain dependencies; generator truth cannot silently satisfy them |
| Specimen, actual phase errors, motion and true continuous field | Evaluator-only comparison quantities | Must not reach fitting, candidate selection, reference construction, interpolation/support choice or tolerance tuning |
| Numerical expectation | Independent analytic finite sums, exact limiting cases or independently justified reference mathematics | Existing product helpers/output and ignored reference output are insufficient as sole oracles |

| Dependency | What must be settled before a numerical child |
|---|---|
| Representation | A/B/C/D family, anchor, exterior/crop, physical units, signed domains and Nyquist convention |
| Calibration compatibility | Fixed or carrier-dependent kernels/profiles, empirical coverage and gauge, known versus inferred quantities |
| Objective and information | Observed sample set, nuisance constraints, scaling/noise/weighting, aliases/gauges, unavailable and ambiguity outcomes |
| Numerical meaning | Parameter domain, rank transitions, derivative/solver meaning, range/failure behavior and justified accuracy assessment |
| Independent expectations | Distinguishing finite sums/integer limit, endpoint/alias controls, permitted positive alternatives and truth-access separation |
| Delivery | Concrete approved contract; fresh native blind A/B, restricted C and fresh native D; inherited exact local/separate-platform gates |

These rows identify decisions, not a scenario or review cap. Future expectations can use the geometric sum above, direct finite kernel sums, declared analytic continuous modes, the even-Nyquist family and exact gauge/zero-information transformations. They must be derived independently for the selected model. No tests or new tolerances are authored here, and discovery/source reports do not enter blind packets.

## Recommendation and remaining exits

For a deliberately finite development slice, A is the narrowest candidate to consider first: it extends the current finite sample domain without secretly inventing a continuous specimen field. A prospective contract could first fix q and actual phases and establish the forward/objective meaning before unknown-carrier inference. That recommendation selects no representation or behavior and supplies no instrument-validity claim. If the intended target is a continuous optical field or owner-reference parity, B or D may be the appropriate first contract; C can remain an explicitly approximate overlap/recombination estimator if independently justified. The smallest next scientific decision is the intended finite/exterior/continuous observation meaning, with origin and endpoint conventions attached.

The [sanitized future dependency material](../plans/continuous-carrier-public-dependencies.md) records the unresolved boundary. The physical motion question stays separate. Phase 6 still needs fractional band/output/filter meaning; Phase 7 needs an integrated raw bead/specimen workflow without supplied nuisance truth; Phase 8 needs an independently contracted realistic `512×512×64` truth-hidden simulation; Phase 9 needs owner-data/settings/reference-output provenance and parity criteria. None is closed by this report.

Confidence is high in the exact finite-sum distinctions and conditional counterexamples. Confidence is moderate that A is the best first development model, because actual acquisition/exterior/optical provenance remains absent. An owner-selected target model, measured calibration reuse limits or a concrete parity requirement could change the recommendation. No physical accuracy, numerical performance or full-volume feasibility was measured.
