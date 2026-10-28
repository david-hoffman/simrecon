# Finite fine-grid scalar operator and real adjoint

**Version1.1, October23,2026.** NS03-L of the owner's full noisy simulation request. The owner selected images-only inference. This independent deterministic operator consumes explicitly supplied model/estimated parameters and performs no inference. All physical choices are conditional synthetic assumptions.

The slice builds a common scalar kernel cache and applies one orientation's forward map or real adjoint. It estimates no carrier, phase, pupil, specimen, brightness, rank or likelihood. It implements no solver, persistence, cleanup, general configuration framework or hidden truth channel. All scientific inputs are supplied explicitly.

## Public boundary and records

The module exposes exactly these operations and its cache record:

```python
build_kernel_cache(
    *, source_shape_zyx, source_spacing_um_zyx,
    emission_um, refractive_index, detection_na, pupil_order,
) -> InverseKernelCache

forward(
    source_e, *, kernel_cache, carrier_yx_per_um, phases_rad,
    beam_amplitudes, excitation_um,
) -> numpy.ndarray

adjoint(
    detector_values, *, kernel_cache, carrier_yx_per_um, phases_rad,
    beam_amplitudes, excitation_um,
) -> numpy.ndarray
```

Only the first array is positional in forward/adjoint; all shown settings are required. Ordinary missing/extra argument binding raises `TypeError`. There is no orientation axis or caller-selectable backend/work-buffer API.

`InverseKernelCache` has exactly seven public fields: `lateral_spectra`, `source_shape_zyx`, `source_spacing_um_zyx`, `emission_um`, `refractive_index`, `detection_na`, `pupil_order`. Bindings are frozen; array contents remain mutable. The builder returns an independent, owned, writable, C-contiguous native float32 plain ndarray for `lateral_spectra`. Metadata consists of Python-int/float tuples/scalars normalized as below. No field is an authenticated provenance or accuracy certificate.

Direct record construction performs no validation. Forward/adjoint validate every field and use its represented payload as defined below. They do not recompute or authenticate a pupil cache from its metadata. A well-formed directly constructed or modified payload defines an algebraic cache kernel, possibly signed and nonphysical; its application guarantee still applies. The physical-pupil approximation guarantee belongs to the builder. Concurrent external mutation is outside the promise. Valid native inputs may be borrowed without an unconditional snapshot; none may be mutated.

## Geometry, pixel integration and units

Let source shape `N=(Nz,Ny,Nx)`, with `Nz>=1` and even `Ny,Nx>=2`, and source steps `D=(dz,dy,dx)` in µm. Source sites are `r_j=((jz+1/2)*dz,(jy+1/2)*dy,(jx+1/2)*dx)`. Detector shape is `(Nz,Ny/2,Nx/2)`, focus sites `(k+1/2)*dz`, lateral pixel size `(2*dy,2*dx)` and pixel centers `((2*iy+1)*dy,(2*ix+1)*dx)`.

Each pixel uses exactly four equal midpoint samples coinciding with fine source-grid lateral sites `(2*iy+sy,2*ix+sx)`, `sy,sx in {0,1}`. For a fine-grid field v, define

`(P v)[k,iy,ix] = dy*dx * sum_(sy,sx) v[k,2*iy+sy,2*ix+sx]`.

Thus `P*` repeats each detector value onto those four sites and multiplies each by `dy*dx`; it is not an average. At the full trial, `N=(64,1024,1024)`, `D=(0.125,0.040,0.040)` µm, detector `(64,512,512)`, and the fine-pixel area is `0.0016 µm^2`.

Source entries are integrated electron-equivalent brightness per source coefficient, not densities. H below has units µm^-2. H followed by P returns electrons; add no source-volume or focus-spacing factor. This source basis has 64 axial sites at 125 nm, an explicit approximation to the refined generator's 128 axial source planes. A 40 nm lateral basis and four pixel samples prove no twofold recovered resolution. Source exterior is zero in every axis; no periodic physical image, missing-tail filling, arbitrary support cutoff or crop/plane normalization occurs.

## Physical builder and represented cache kernel

The builder uses the approved clear, matched-index scalar finite-Q pupil, independently specified here. With exact normalized float64 parameters, set `R=NA_det/lambda_em`, `nu=n/lambda_em`, `beta=NA_det/n`. Let `u_a,w_a` be the canonical Q-point Gauss-Legendre rule transformed to `[0,1]`, with positive weights summing to one. For the order-zero Bessel function J0,

```text
A_Q(r,d) = sum_a w_a * J0(2*pi*R*sqrt(u_a)*r)
                    * exp(i*2*pi*nu*d*(sqrt(1-beta**2*u_a)-1))
h_Q(r,d) = pi*R**2 * abs(A_Q(r,d))**2
H_Q(Delta) = h_Q(sqrt((Delta_y*dy)**2+(Delta_x*dx)**2), -Delta_z*dz)
```

The source-minus-focus sign is explicit. For this clear pupil H_Q is real, nonnegative and even separately in all displacements. Its finite radial quadrature is the selected model, not a continuum or experimental-optics claim. H_Q contains no pixel-area factor.

All required displacements are `-(N_a-1)..N_a-1`. Set `F=(2*Nz,2*Ny,2*Nx)`. One reference embedding places each nonnegative axial lag plane `d=0..Nz-1` at `Delta_y mod Fy, Delta_x mod Fx`, with unused lateral lag indices Ny/Nx set to zero. The exact two-dimensional negative-exponent, unnormalized discrete Fourier transform of that even reference plane is real. The builder stores a real x half-spectrum approximation as float32, shape

`lateral_spectra.shape == (Nz,2*Ny,Nx+1)`.

Builder eligibility is determined by the stated metadata/payload rules and both required-lag builder-fidelity bounds below. The zero-filled plane is a reference embedding, not an additional pretransform or coefficientwise accuracy obligation. A builder may choose different unused lateral lag values before transforming, or another faithful representation, provided its returned float32 payload obeys those rules and both bounds against the unchanged physical H_Q. No accuracy is required at unused lateral lags, and their choice changes no retained finite-map interaction. Coordinated coefficient choices are permitted; no particular rounding algorithm is prescribed.

The payload must be finite and exactly even in its stored y frequency: `C[d,l,k]=C[d,(-l) mod Fy,k]`. This is a representation rule, not an imaginary-residue tolerance. The builder may enforce that representation by a faithful symmetric computation; no particular transform backend is required.

For any valid payload C, complete its x spectrum by the usual real-array conjugate reflection and take the **exact normalized inverse two-dimensional DFT**. This defines a real, separately even lateral plane `h_C[d]` in µm^-2. Define the cache kernel on every required signed displacement by

`H_C(Delta) = h_C[abs(Delta_z)][Delta_y mod Fy, Delta_x mod Fx]`.

This definition, not an undocumented idealization of rounded cache values, is the target for forward/adjoint. Float32 cache quantization can make H_C signed. Unused lateral lag values, including those chosen before transformation, are never queried by the retained finite sum. Embed axial lags `+/-1..+/-(Nz-1)` evenly and lag zero once on Fz; the unused axial lag Nz is zero. In exact arithmetic, convolution on F followed by the first N sites equals the complete finite exterior-zero convolution. It is a computational embedding, not periodic exterior. Neither the cache nor this equivalence makes a floating FFT exact.

## Continuous-carrier forward map

Let q be the supplied signed continuous y/x carrier in cycles/µm, `phi_p` the supplied actual phases in radians, `k0=n/lambda_ex`, `kappa=k0-sqrt(k0**2-|q|**2)`. No bin rounding is permitted. Let nonnegative beam amplitudes be `(a0,a+,a-)`, with `S=a0**2+a+**2+a-**2>0`, and define `u=a0*a+/S`, `v=a0*a-/S`, `g=a+*a-/S`. Stable equivalent amplitude normalization is permitted.

For real x and real-kernel finite convolution H using H_C, write `theta_j=2*pi*q dot r_j,yx`, `alpha=2*pi*kappa`. For fine focus index n, whose axial coordinate is z_n,

```text
T+[n] = exp(+i*alpha*z_n) * H[x*exp(i*(theta-alpha*z_source))][n]
T-[n] = exp(-i*alpha*z_n) * H[x*exp(i*(theta+alpha*z_source))][n]
T2[n] = H[x*exp(2*i*theta)][n]
(A_C x)[p] = P[H[x] + 2*Re(exp(i*phi_p)*(u*T+ + v*T-)
                           +g*exp(2*i*phi_p)*T2)]
```

H on complex data means its separate real and imaginary applications. Equivalently the coefficient for source j and fine detector site n is `H_C(n-j)*I_p(j,z_j-z_n)`, where I is the squared three-beam field from the approved optical equation divided by S. All source sites contribute, including boundary/corner interactions. The expansion preserves unequal sides and the `phi,2*phi` relation. A later physical q fit must update kappa; this slice performs no such fit.

## Real Euclidean adjoint

Use unweighted real coordinate inner products, with no voxel-volume, phase-count, noise or extra pixel factor. For real detector y, let

```text
r0 = sum_p P* y[p]
r1 = sum_p exp(-i*phi_p) * P* y[p]
r2 = sum_p exp(-2*i*phi_p) * P* y[p]
gamma+ = exp(i*(theta-alpha*z_source))
gamma- = exp(i*(theta+alpha*z_source))
beta+ = exp(+i*alpha*z_focus)
beta- = exp(-i*alpha*z_focus)
(A_C* y) = H[r0] + 2*Re(u*conj(gamma+)*H[conj(beta+)*r1]
                        +v*conj(gamma-)*H[conj(beta-)*r1]
                        +g*exp(-2*i*theta)*H[r2])
```

H is self-adjoint here because the represented kernel is real and even and source/output fine grids have the same finite restriction. Focus phasors multiply the lifted, phase-weighted residual **before** H; source phasors multiply after it. In exact real arithmetic `<A_C x,y>=<x,A_C* y>`. Numerical calls approximate these equations as specified below. Neither the adjoint nor a small dot-product error is an inverse or evidence of physical recovery.

## Normalized inputs, outputs and failures

Source and residual inputs are plain float32-width ndarrays, all finite, of respectively shape N and `(P,Nz,Ny/2,Nx/2)`. Both may be signed. Reject float64/float16/integer/bool/complex/other array kinds, subclasses, lists and wrong/empty shapes. Endian, strided, Fortran and read-only variants are valid; native float32 values define the exact source/data problem. The numerical operator therefore makes no universal float64-subnormal input promise. Caller construction or rounding of a residual from a float64 prediction is separate and explicit; the API does not silently accept and downcast that prediction.

Carrier and phase arrays are plain ndarray kinds i/u/f, shapes `(2,)` and `(P,)`, P>=1; original and normalized float64 values must be finite. Conversion may round or underflow finitely. Signed/zero carriers and arbitrary finite phases, including duplicates or one phase, are valid; no rank/conditioning gate is imposed. Require `|q|<=n/lambda_ex` on normalized exact-real values. Huge reducible phases/turns are not excluded by a hidden cap. Rounded intermediate phases do not redefine the target.

Source shape is a built-in tuple of three plain built-in positive ints, with the even lateral restriction above; bool is excluded. Spacing and amplitudes are built-in tuples of length three of plain built-in int/float values, excluding bool/subclasses. Wavelengths, n and NA are likewise plain built-in int/float scalars, excluding bool/subclasses. Spacings, wavelengths, n and NA normalize to finite positive float64; require NA<=n. Amplitudes normalize to finite nonnegative float64 with at least one positive. Q is a plain built-in positive int. There is no arbitrary shape, Q, carrier or amplitude cap. Unrepresentable native indexing/address space is a range obstruction, not permission to choose another grid.

Cache consumers require an `InverseKernelCache` instance; subclasses are accepted under the same field rules. They validate all metadata under the builder grammar plus payload plain-array float32 width, exact shape, component finiteness and exact stored y symmetry. They do not impose physical positivity, mass, pupil-content authentication or a kernel-conditioning threshold on directly constructed payloads. All metadata is validated even for zero input or an unused beam order.

Forward returns owned, writable, C-contiguous native float64 plain ndarray `(P,Nz,Ny/2,Nx/2)`; adjoint returns the same storage kind with shape N. Results are finite, signed and independent of every input/other call. Zero source/residual and an all-zero represented kernel return exact zero after complete validation. No clipping, partial output or implicit normalization is permitted. Inputs, global random state and caller NumPy/warning policy are preserved on success/failure.

Use error codes `invalid_simulation_inverse_operator` for invalid representations/domains/cache fields, and `simulation_inverse_operator_range` for concrete address-space, derived geometry, cache representability or owned numerical precision/nonfinite failures. Diagnostics identify the operation/field; exact prose and simultaneous-invalid precedence are unspecified. A range failure cannot stand for ordinary unimplemented work, unavailable time or an arbitrary cap. A raw sum, square, norm or coordinate product overflowing alone does not establish failure when an equivalent safe evaluation meets the target. Actual `MemoryError` and unrelated exceptions/warnings propagate unchanged. Expected own arithmetic overflow/underflow/invalid handling is locally scoped, emits no arithmetic `RuntimeWarning`/`FloatingPointError` and restores caller policy; unrelated backend `RuntimeError`, `TypeError` or `ValueError` is not relabeled. No backend or private call count is selected solely to enable injected tests.

## Numerical targets, separate from optical discretization

These are selected numerical targets under the owner-authorized simulation contract. Independent A/B review must challenge oracle validity and meaningful precision risks. They are neither observed accuracy nor universal FFT error theorems. The generator's separate `1e-5*T` contract remains unchanged.

For any kernel H, define its finite unilluminated source-to-detector matrix

`B_H[n,j]=dy*dx*sum_(sy,sx) H((nz,2*ny+sy,2*nx+sx)-j)`.

It is dimensionless. Define `C_r(B)=max_n sum_j abs(B[n,j])` and `C_c(B)=max_j sum_n abs(B[n,j])`, evaluated without observer overflow/underflow. For a represented cache, also define the nonnegative matrices

```text
G_C[n,j] = dy*dx*sum_(sy,sx) abs(H_C((nz,2*ny+sy,2*nx+sx)-j))
E[n,j] = dy*dx*sum_(sy,sx) abs((H_C-H_Q)((nz,2*ny+sy,2*nx+sx)-j))
```

The absolute values precede the four-sample pixel sum. Thus cancellation within a pixel does not erase the numerical scale of a signed cache. These are reference definitions, not a requirement to allocate dense matrices.

**Builder fidelity:** for the exact physical Q model B_Q and the represented-cache error E, require

```text
max_n sum_j E[n,j] <= 1e-4*C_r(B_Q)
max_j sum_n E[n,j] <= 1e-4*C_c(B_Q)
```

This explicitly includes pupil evaluation, transform and float32 cache storage. It is a normwise finite-model approximation; it promises no accurate relative value in a dark tail.

**Application fidelity:** let `L=(a0+a++a-)**2/S`, with `1<=L<=3`. Set `F_scale=L*C_r(G_C)*max_j abs(x[j])` and `J_scale=phase_count*L*C_c(G_C)*max_(p,n) abs(y[p,n])`. Here phase_count is the number of supplied exposure phases. Both have units electrons. Require each successful forward/adjoint output to have maximum absolute error, against its exact cache-defined equations, at most `1e-4*F_scale` / `1e-4*J_scale`. Zero scale requires exact zero. There is no added absolute floor. The supplied source/residual values are float32, while the exact reference phasors and matrix equations use their real values and normalized float64 settings.

Thus builder and application errors are separate. Since H_Q is nonnegative, `abs(H_C)<=H_Q+abs(H_C-H_Q)` gives `G_C<=B_Q+E` entrywise. With `t=1e-4`, builder fidelity therefore gives `C_r(G_C)<=(1+t)*C_r(B_Q)` and the same column inequality. The physical forward scale is `L*C_r(B_Q)*max(abs(x))`; the physical adjoint scale is `P*L*C_c(B_Q)*max(abs(y))`. On either scale, application error is at most `t*(1+t)` and physical-to-cache model error at most t, so their sum is `2*t+t**2=2e-4+1e-8`. This is not a `1e-4` end-to-end physical promise. Neither bound measures axial/source/pixel discretization or conditioning. Approximately 839 float32 machine epsilons (`2**-23`) fit inside `1e-4`; that gives a plausible normwise target for staged transforms and harmonic reconstruction, **not** a proof that every shape/phase meets it. Tiny direct-sum and representative cache controls must challenge the numerical behavior independently. A concrete precision obstruction reports range instead of silently violating the target; magnitude alone is not that obstruction.

Per-call max-absolute component scaling before float32 FFT work, with restoration in float64, is a feasible way to preserve tiny/large float32 source/residual inputs. Equivalent safe scaling, including kernel scaling when needed, is allowed. The cache target remains its represented float32 values; the physical target remains the finite-Q equations. Wider internal arithmetic is permitted if behavior and measured resources remain suitable.

## Feasible finite work and required resource evidence

A feasible H application stores the Nz real lateral kernel half-spectra and the Nz complex64 lateral source-plane half-spectra. Process lateral frequency bins in finite blocks, for example 4096 bins: pad the axial source to Fz, form the real axial kernel transform from its even lags, multiply, inverse transform and retain the first Nz planes. Then invert lateral transforms plane by plane. A final shorter block is ordinary work. This work-unit size is not a human execution budget, public test seam, input cap or required backend. Equivalent faithful bounded organization is allowed; do not allocate all orientations or all harmonic work simultaneously.

At full shape, the kernel payload has 134348800 float32 entries, **537395200 B**. The source-plane half-spectra have the same entry count as complex64, **1074790400 B = 1.0009765625 GiB**. One real float32 source volume is 268435456 B; a float64 fine output is 536870912 B; five float64 detector outputs are 671088640 B. An axial block `(128,4096)` uses 4194304 B complex64, or 2097152 B real float32. Plane transforms, real/complex modulation/accumulation arrays and validation/normalization temporaries add to these counts. A roughly 3–5 GiB principal-array plan is plausible; it is not measured RSS/footprint or a 16 GiB guarantee. No full kernel files need be persisted.

One orientation uses seven real H applications: DC once, plus two each for T+, T- and T2. Three ordinary public calls use 21, likewise for three adjoints. The algebraic 19 count is possible only in a fused three-orientation composition sharing one forward DC convolution, or convolving the sum of the three adjoint DC residuals once. This draft adds no stateful reuse or extra composition API to claim that saving.

Before any inverse fit: independently evaluated tiny float64 direct pupil/convolution and adjoint controls; then a moderate H/forward/adjoint pilot; then a bounded full-size H application and one-orientation forward/adjoint resource pilot with retained real inputs and no competing heavy phase. Measure actual cache construction/application times, native RSS/footprint, transient work/ownership, available memory, swap/disk changes and complete status. No resource failure counts as a numerical success. No optimizer workload, accuracy threshold policy, iteration or recovery guarantee follows.

## Compact behavioral inventory and remaining adoption issues

Independent proof must cover: physical pupil peak and finite-Q reference; complete even cache geometry and direct-payload meaning; odd/even axial shapes and even lateral pixel grouping; point electron/pixel-area units; continuous signed q and half-cell anchors; unequal-side axial signs and harmonic factors; finite edges/corners without wrap; direct real adjoint including P* and focus/source phasor order; signed/zero/one-beam/zero-carrier/duplicate-phase positives; float32 storage/layout/ownership and float64 settings normalization; malformed cache/domain/shape/dtype inputs; safe extreme float32 scaling versus concrete representational failure; nonfinite numerical output versus unrelated dependency/allocation/warning propagation; policy/input preservation and no persistence.

Tiny independent oracles may use direct float64 sums and analytic one-node/on-axis pupil controls, asymmetric signed inputs and noninteger carriers. A cache-defined direct DFT oracle and a physical pupil oracle test different obligations. Dot products supplement direct adjoint values; agreement with another product call is insufficient. No full-size arrays are automatic routine-test inputs. Public dependency-failure probes may exercise real entry points without requiring a named backend or adding a production test seam.

This independent slice starts from stable baseline62f12e2936281f35bd78f2892c1511ee558365d4 and calls only stable NumPy/SciPy and public errors, never unfinished simulator/calibration/source/memory runtime. Float32 operands, float64 results and the separate1e-4 numerical budgets above are selected. Later actual image-only q/phase estimation, source-grid mismatch and inverse regularization remain separate dependencies. No source truth or experimental-accuracy threshold is supplied. The complete mathematical expectation is specified here; role inputs need no implementation or private advisor/history material.
