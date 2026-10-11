# Selected synthetic 3D acquisition model v1

**Version 1.0.** The owner selected a documented synthetic 3D model on October 10, 2026. These are explicit development choices, never measured facts about the owner's instrument. This C0 definition supports the [grid-peak localization foundation](../contracts/bead-peak-localization-v1.md) and later individually contracted calibration slices. It adds no generator runtime or full raw-input workflow. Actual reference settings and real-data parity remain unresolved.

## Coordinates, detection and specimen

The model uses a finite periodic grid G=Z_Nz × Z_Ny × Z_Nx, with positive spacings (dz,dy,dx) in micrometres (µm). Index j denotes sample center r_j=(jz*dz,jy*dy,jx*dx). Coordinate zero is the synthetic specimen/detector coordinate origin; lengths are L_a=N_a*d_a. Position is defined modulo those periods, and the last sample center is (N_a-1)*d_a, distinct from L_a. Arrays use z/y/x; raw SIM declarations separately retain orientation/phase and optional channel/time.

The sampled detection intensity response h[u] is dimensionless, nonnegative, sum_G h=1 and has its sole largest sample at u=(0,0,0). This explicitly fixes the peak-origin gauge. A selected smooth synthetic family is

```text
w[u] = exp(alpha_z*cos(2*pi*uz/Nz)
         + alpha_y*cos(2*pi*uy/Ny)
         + alpha_x*cos(2*pi*ux/Nx))
h[u] = w[u]/sum_G w, with each alpha_a>0.
```

Each cosine is at most one, with equality on its discrete axis only at zero; hence the joint maximum is unique. Singleton axes have their only coordinate zero. Independently specified asymmetric nonnegative normalized kernels with the same unique-zero-peak property are also valid model instances. Symmetry is not an estimator requirement. This is a phenomenological finite detection response, not a diffraction-limited pupil/point-spread-function (PSF) calculation, optical support claim or continuous-optics convergence result. It does not settle phase8's separately required realistic optical simulation.

Specimen s[j]>=0 is a discrete brightness scale in expected electrons for the normalized phase-zero scan volume. No voxel-volume factor occurs because s is a per-grid-site weight, not a density. Calibration's selected point-bead mode is s[j]=B*1_(j=b), B>0, with an on-grid index b. B is the summed zero-order response in electrons, including the chosen exposure/brightness scale; it is not calibrated photon yield. A point bead has identity size compensation by definition. Finite diameter/emission, fractional positions and continuous sampling need later contracts. The forward definition extends to nonnegative specimen arrays, but no complete reconstruction workflow is implemented here.

## Illumination and axial scan

For one explicitly selected orientation, q=(qy,qx) in cycles/µm and kappa>0 in cycles/µm define a lateral fundamental and axial difference frequency. Choose q_a=ell_a/L_a and kappa=ell_z/L_z with integer modes for exact periodicity. Physical lateral coordinates refer to the fixed specimen. At output scan index n and emitting site j, axial displacement is delta_z=(nz-jz)*dz. The illumination's axial structure follows the objective focal plane during scanning, rather than remaining fixed to the specimen.

Choose constant complex scalar field amplitudes a0,a_plus,a_minus with P=abs(a0)^2+abs(a_plus)^2+abs(a_minus)^2>0. Define

```text
theta_pj = 2*pi*(qy*jy*dy + qx*jx*dx) + phi_p
I_p(j,delta_z) = abs(a0*exp(i*2*pi*kappa*delta_z)
                    + a_plus*exp(i*theta_pj)
                    + a_minus*exp(-i*theta_pj))^2/P
D_p[n] = sum_(j in G) s[j]*h[n-j]*I_p(j,(nz-jz)*dz)
```

All differences/convolution are circular. Integer illumination modes make the field/intensity invariant to adding a grid period. D has expected-electron units. Intensity is nonnegative by its squared-field definition. Linear fluorescence/detection and focal-plane-fixed axial illumination motivate this form: [Gustafsson et al., equations 1–10, pp.4958–4960](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). The finite response, grid, normalization and selected parameters here are project choices.

This scalar model ignores vector polarization and aberrations. If interpreting its fields as symmetric propagating plane waves in one chosen homogeneous medium, require 0<kappa<abs(q), and set nu0=(abs(q)^2+kappa^2)/(2*kappa), nu_side=nu0-kappa>0. Then nu_side^2+abs(q)^2=nu0^2; adding the removed common axial phase gives equal-magnitude wavevectors. Refractive index n_med and vacuum excitation wavelength lambda_exc must satisfy n_med/lambda_exc=nu0, with wavelength in µm. Grid-compatible illustrative values below satisfy that algebra. No actual wavelength, refractive index, numerical aperture or detection model is inferred from it.

Expand the selected field algebra:

```text
g0(delta_z) = 1
g1(delta_z) = (a_plus*conj(a0)*exp(-i*2*pi*kappa*delta_z)
              + a0*conj(a_minus)*exp(i*2*pi*kappa*delta_z))/P
g2(delta_z) = a_plus*conj(a_minus)/P
I_p = 1 + 2*Re(g1*exp(i*theta_pj) + g2*exp(2*i*theta_pj))
K_m[u] = h[u]*g_m(uz*dz)
c_m[n] = sum_j K_m[n-j]*s[j]*exp(i*2*pi*m*q·r_j,xy)
D_p[n] = c0[n] + 2*Re(c1[n]*exp(i*phi_p)+c2[n]*exp(2*i*phi_p))
```

For a0=a_plus=a_minus=1, P=3, g1=(2/3)*cos(2*pi*kappa*delta_z), g2=1/3. At delta_z=theta=0, I=1+4/3+2/3=3, matching squared field 9/3. Constant g0 and g2 are explicit features of this ideal model, consistent with the ideal three-beam lateral-order grouping in the cited paper. They are not a statement that every empirical calibration has g0=1. A nonconstant zero-order envelope requires a separately contracted model.

For a point bead,

```text
c0[n]=B*h[n-b]
c_m[n]=B*h[n-b]*g_m((nz-bz)*dz)*exp(i*2*pi*m*q·r_b,xy), m=1,2.
```

Thus its unique zero-order peak is b under the selected gauge. Neither b nor h is passed to the locator; they are independent generator/comparison truth. The observed dc array is its input. A brightest unequal multi-bead response is still a legitimate grid peak, without isolation certification.

## Phase truth, camera relation and signed response

Actual phases phi_p in radians are explicitly declared generator truth, constant across each phase volume. Nominal commands chi_p are distinct metadata and may differ independently by phase; commands do not prove truth. Known-phase separation requires an identifiable actual five-column matrix from its inherited contract. Five evenly spaced actual phases are one valid example; unequal full-rank phases are allowed by the inherited separator. No unknown-step estimator is added.

The existing separator defines represented float64 phasors and their squares. The continuous expressions above motivate the model; stored rounded exposures/angles and the separator's represented matrix define each numerical fit. Independent examples must account for their numerical budget and show a peak margin safely exceeding error. An arbitrary physical accuracy threshold or exact-real trigonometric/bitwise cross-platform promise is not introduced.

A common phase-origin shift preserves dc and rephases side orders; independent phase-step errors generally change separation. A common offset alone is therefore not an adequate wrong-phase negative control. Unknown phases, phase/origin gauges and illumination amplitude versus bead brightness cannot be disentangled from raw data here. Localization is identifiable only as the unique observed grid maximum; physical emitter center needs the selected detection gauge. Later response formation must contract removal/retention of the bead lateral factor, centering and normalization exactly once.

Raw detector samples follow explicitly supplied offset o and response r>0:

```text
raw[p,n] = o[p,n] + r[p,n]*D_p[n]
```

Raw and offset use counts; response uses counts/electron. The existing correct_linear_response computes binary64 subtraction then division with its whole-call range rule, retains signed results and records supplied/applied coefficients. Scalars or full exact-shape canonical maps are supplied explicitly; there is no default correction. The chosen model is noiseless, with no saturation, defective pixels, fading, drift or unknown background. Those experimental mechanisms remain unimplemented rather than assumed corrected. Broader R2/actual O4/S4 remain pending.

Phase harmonics retain signed complex information: spatial c_-m=conj(c_m). If later E_m(k) is a forward discrete Fourier transform with negative exponential, E_-m(k)=conj(E_m(-k)), using modular frequency negation, including even Nyquist bins. This is not pointwise same-frequency Fourier conjugation. [NumPy's DFT convention](https://numpy.org/doc/stable/reference/routines.fft.html) describes the transform convention. Current C1 performs no transform, centering, normalization, conjugation or order-transfer preparation. Signed complex harmonics cannot be silently passed as nonnegative intensity PSFs.

## Fully specified illustrative instance and limits

These parameters define one reproducible synthetic instance, not runtime defaults or instrument settings.

| Quantity | Selected example |
|---|---|
| Grid and spacing | (Nz,Ny,Nx)=(8,7,10); (dz,dy,dx)=(0.25,0.10,0.10) µm |
| Periods / sample-center maxima | (2.0,0.7,1.0) µm / (1.75,0.6,0.9) µm |
| Kernel shape parameters | (alpha_z,alpha_y,alpha_x)=(2,4,3) |
| Illumination modes | (ell_z,ell_y,ell_x)=(1,0,1): kappa=0.5, q=(0,1) cycles/µm |
| Scalar fields | a0=a_plus=a_minus=1; P=3 |
| Optional homogeneous wave interpretation | nu0=1.25, nu_side=0.75 cycles/µm; n_med=1, lambda_exc=0.800 µm (800 nm) |
| Point bead / brightness | b=(3,2,7); B=600 expected electrons in zero-order summed volume |
| Actual phases | phi_p=2*pi*p/5, p=0,…,4 |
| Nominal commands | chi_p=phi_p+(0.00,0.03,-0.02,0.05,-0.04) radians |
| Camera scalar example | o=10 counts; r=2 counts/electron; other explicitly declared full maps remain valid |
| Groups | One orientation/channel/time; no extra exposure or hidden group reuse |

Sanity checks: 0.75^2+1^2=1.25^2; lateral second-order frequency 2 cycles/µm is below the selected 5 cycles/µm lateral Nyquist value; kappa=0.5 is below 2 cycles/µm axial Nyquist. These checks do not establish alias-free continuous imaging: the sampled kernel is not band-limited. Periodic boundary wrap, finite axial response and scalar optics are defined approximation limits; no infinite-field, optical-support or physical-accuracy guarantee follows. C1 examples may use smaller independent instances or asymmetric admissible kernels rather than treat this table as an oracle.

The calibration route under development is explicit raw declaration → supplied affine correction → caller group selection → known-phase dc → observed grid peak. C2–C5 empirical signed response/scale/finite-bead composition, independent grids, unknown-phase/drift inference, full reconstruction, phase8 realistic simulation and phase9 owner-data/reference parity remain separate unfinished work. Actual instrument facts may later require another model without invalidating this narrowly labeled synthetic foundation.
