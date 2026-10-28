# Synthetic scalar optical expectation v1

**Version 1.0, revision 2.** NS02 of the owner's October 22, 2026 full noisy simulation request. This pure deterministic in-repository operator generates expected detector signal. It is independent of camera sampling and supplies no calibration/inverse estimator. All optical choices below are explicit synthetic assumptions, not measured instrument facts.

## Public boundary

The module `scripts/simulation_optics.py` exposes:

```python
expected_images(
    source_e,
    *,
    detector_spacing_um_zyx,
    source_refinement_zyx,
    carriers_yx_per_um,
    phases_rad,
    beam_amplitudes,
    excitation_um,
    emission_um,
    refractive_index,
    detection_na,
    pupil_order,
    pixel_subsamples_yx,
) -> numpy.ndarray
```

All arguments are explicit and required. Source weights are integrated electrons per source cell per exposure, before structured illumination. They are not density samples: do not multiply them by source voxel volume again. Phantom construction/refinement computes those weights separately.

A shared finite box has corner `(z,y,x)=(0,0,0)` µm. Detector shape N is source_e.shape divided componentwise by the positive integer source refinements f. With detector spacing D, source-cell centers are r_j=(j+1/2)*D/f. Detector focus centers are z_k=(k+1/2)*D_z. Lateral detector pixel centers are ((i_y+1/2)*D_y,(i_x+1/2)*D_x). Source exterior is zero; boundaries never wrap. Source cells act at their midpoints in this finite quadrature model.

For positive pixel counts p_y,p_x, the equal-weight tensor midpoint samples in pixel (i_y,i_x) are ((i_y+(l_y+1/2)/p_y)*D_y,(i_x+(l_x+1/2)/p_x)*D_x). Their mean is multiplied by pixel area D_y*D_x. Source and pixel refinements are independently declared; they need not equal each other.

Output shape is `(orientation,phase,z,y,x)`, with orientation count O from the carriers and phase count P from phases_rad. Every focus/phase is a separate exposure. There is no output-focus-spacing factor.

## Illumination and detection equations

All distances/wavelengths below use µm; carriers are cycles/µm and phases radians. For source j and focus k, define **d=r_j,z-z_k**, source minus focus. Let q_o be the signed continuous carrier vector in y,x order, k0=n/lambda_ex and kappa_o=k0-sqrt(k0**2-|q_o|**2). No integer-bin rounding is permitted. Define theta_opj=2*pi*q_o dot r_j,yx+phi_op. For real nonnegative amplitudes a0,a+,a- with S=a0**2+a+**2+a-**2>0,

I_op(j,d)=abs(a0*exp(i*2*pi*kappa_o*d)+a+*exp(i*theta_opj)+a-*exp(-i*theta_opj))**2/S.

The central/plus/minus amplitude ordering and source-minus-focus sign are normative. Unequal sides are supported; no symmetry shortcut may change their complex interference. Actual phases/carriers here are generator inputs only. This contract gives the inverse no access to them.

The detection approximation is a homogeneous matched-index, uniform clear circular scalar pupil. It includes no vectorial polarization, aberration or scattering. Set R=NA_det/lambda_em, nu=n/lambda_em, beta=NA_det/n. Let u_a,w_a be the canonical pupil_order-point Gauss-Legendre nodes and weights transformed to [0,1], with sum(w)=1. With J0 the order-zero Bessel function,

A_Q(r,d)=sum_a w_a*J0(2*pi*R*sqrt(u_a)*r)*exp(i*2*pi*nu*d*(sqrt(1-beta**2*u_a)-1)),
h_Q(r,d)=pi*R**2*abs(A_Q(r,d))**2.

h_Q has units µm^-2. It has one common scale derived from the continuum uniform pupil. Do not renormalize defocus planes, crops, individual orders or the finite 3D array. The finite radial rule is the numerical model; it is not a continuum-accuracy claim.

For detector pixel n at focus k, let t_nl be its lateral midpoint quadrature sites. The exact finite expectation target is

mu_opkn = (D_y*D_x)/(p_y*p_x) * sum_j source_e[j]*I_op(j,d_jk)*sum_l h_Q(norm_2(t_nl-r_j,yx),d_jk).

Here norm_2 is Euclidean lateral distance, not componentwise absolute value. The sum includes every declared source cell, even at field boundaries. No arbitrary spatial cutoff, periodic source image, per-plane intensity normalization or noise/background enters this equation. Factoring it into harmonics is permitted only when it preserves this target.

The focal-plane-relative illumination follows the physical separation in [Gustafsson et al. 2008, equation 5](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf), opened October 22, 2026. The finite uniform scalar-pupil and quadrature conventions above are the selected synthetic mathematical model, not a claim that the experiment satisfies every assumption in that paper.

## Arithmetic accuracy, ownership and errors

Return a complete, independently owned, writable, C-contiguous native float64 plain ndarray of finite nonnegative means in electrons. No input is mutated on success or rejection. The operator is deterministic for normalized inputs and recorded numerical dependencies. No bitwise cross-version or implementation equality is selected.

Arithmetic error is bounded separately from discretization. Normalized inputs are interpreted as exact real values in the stated finite mathematical quadrature; rounded intermediate phases do not redefine that target. Mathematically equivalent phase reduction or higher precision evaluation is permitted. Define U by the exact same finite source/pupil/pixel equation with illumination identically one, and T=max(U) over detector z,y,x. Each returned entry must differ from its exact finite mu by at most **1e-5*T** electrons. If T=0, output must be exactly zero. A zero source returns exact zero. This unilluminated scale also governs dark exposures; do not divide by a nearly zero illuminated image. The allowance is 0.01 electron when T=1000 electrons. It is a selected numerical target, not an observed error or proof that any mixed-precision algorithm attains it. No relative L2-only substitution or hidden arbitrary denominator floor is allowed. Numerical removal of negative roundoff is permissible only within that same error bound.

Input arrays source_e, carriers_yx_per_um and phases_rad are plain NumPy ndarrays of dtype kind i/u/f; original values and normalized float64 values must be finite. Source is rank3, every axis nonempty, nonnegative after normalization, and each shape axis divisible by its refinement. Carriers have shape(O,2), phases shape(O,P), O,P>=1; signed carrier components and any finite phases, including duplicates, are allowed. Layout/endian/read-only variants are allowed. Numeric conversion may round. Boolean/complex/object/non-numeric arrays and ndarray subclasses are outside the boundary.

The spacing tuple contains three plain built-in positive int/float values; beam_amplitudes contains three plain built-in nonnegative int/float values with at least one positive. Wavelengths, index and aperture are plain built-in positive int/float; NA_det<=n. Each must normalize to finite float64; bool/numeric subclasses/NumPy scalar coefficients are excluded. Carrier norms must satisfy |q_o|<=n/lambda_ex. Zero carrier and zero individual amplitudes are valid. Refinements and pixel counts are tuples of respectively three and two plain built-in positive ints; pupil_order is a plain built-in positive int; bool is excluded. No arbitrary maximum is selected.

Use public SimreconError code invalid_simulation_optics for invalid domains/shapes; simulation_optics_range for nonfinite derived geometry, frequency/phase/pupil arithmetic or expected output. Domain-valid astronomical values are not promised stable representability of every model intermediate. Finite subnormal/underflow-to-zero outcomes are permitted only when successful output still satisfies the unchanged 1e-5*T allowance. simulation_optics_range also covers a concrete inability to represent or evaluate the target within that allowance even when intermediates remain finite. For example, a one-cell source of the smallest float64 value delta=2**-1074 with unit area/refinements/pupil order, R=1 and central-only illumination has mu=T=pi*delta; the nearest float64 value 3*delta has about4.51% relative error, so that call must report range failure. This creates no absolute-error floor or arbitrary magnitude cap. Magnitude alone does not prove failure: large integer-turn carrier geometry can still have an exactly reducible phase and remain a valid positive. A range refusal needs an identifiable numerical precision/representation obstruction; ordinary unimplemented work, unavailable time or a hidden shape/carrier cap is not that obstruction. Ordinary Python argument binding remains TypeError; invalid-input precedence and diagnostic prose are unspecified. Preserve NumPy caller error settings; expected arithmetic overflow/underflow emits no arithmetic RuntimeWarning/FloatingPointError. MemoryError and unrelated failures propagate; suppress no unrelated warning category. No successful partial output is returned.

There is no persistence interface, overwrite authority or file retention model here. Normal temporary numerical allocation is permitted; no process-wide memory policy or hidden scientific truncation follows. The full trial is detector(64,512,512), source refinement(2,2,2), pixel counts(2,2), O=3,P=5. Its execution must be staged and measured on the 16GiB workstation before accepting full-size feasibility; no current measured resource guarantee is asserted. Other legal shapes/refinements retain the same mathematical target but no fixed memory/time bound. Resource failure is incomplete execution, never a passing simulation.

## Scenarios and independent evidence

| ID | Observable obligation / credible wrong outcome |
|---|---|
| O01 | Zero source and single-source pupil-peak scale; no source-volume or focus-spacing multiplier |
| O02 | Independent source superposition with unequal nonnegative weights and ownership |
| O03 | Direct squared-field illumination, relative phases and central/side normalization |
| O04 | Unequal-side source-minus-focus axial sign; balanced symmetry cannot supply this proof |
| O05 | Continuous signed two-dimensional carriers, phase-coordinate anchor and no bin rounding |
| O06 | Finite exterior-zero boundaries, off-center/edge sources and no periodic contamination |
| O07 | Pixel area and midpoint integration distinct from evaluating only at the pixel center |
| O08 | Source/focus half-cell coordinates, odd/even shapes and independent source/pixel refinements |
| O09 | Finite radial pupil quadrature, defocus and one shared normalization across planes |
| O10 | Uniform finite-equation arithmetic allowance, including cancellation/dark exposure, no output negativity |
| O11 | Valid layouts/dtypes/rounding, all-zero/one-beam/zero-carrier/duplicate-phase positive cases |
| O12 | Invalid array/coefficient/refinement/shape/aperture/carrier domains; ordinary binding errors |
| O13 | Nonfinite derived/output range, input preservation and caller arithmetic settings |
| O14 | Real generator use with multiple orientations/phases and deterministic expected-electron output |
| O15 | Finite numerical representation/precision obstruction reports range instead of violating the accuracy bound; stable large integer-turn phase positives remain supported |

A independently derives tiny explicit finite sums, analytic on-axis/one-node pupil cases and direct squared-field values. Do not duplicate the runtime algorithm or use output as expected truth. For example amplitudes(4,2,1), source at the lateral phase origin, phi=pi/2 and kappa*d=+/-1/4 give illumination25/21 versus9/21; symmetric h alone cannot reveal that sign. Recalculate any fixture rather than copying this value without its conditions. One-node radial rules and h_Q(0,0)=pi*R**2 provide independent controls. Equivalent values under an obligation are examples, not new scenarios.

After implementation, independent executed evidence must distinguish arithmetic/storage error from radial, pixel and source discretization and finite-field effects. Refine radial and pixel quadrature through at least three resolutions while holding other inputs fixed; report relative L2, maximum difference normalized by independent unilluminated peak, and total-signal change over a declared displacement domain. Use separately evaluated references/analytic controls, not only repeated calls to the same algorithm. Source/bead geometry refinement and full phantom sensitivity belong to the subsequent generation composition; 2x sampling alone proves no 100nm sphere accuracy. No continuum accuracy threshold is silently inferred; actual limits remain explicit before the full scientific report.
