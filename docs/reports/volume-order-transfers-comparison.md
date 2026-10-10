# Signed finite-grid volume-order comparison

The actual product agrees with independent stored-input direct sums for **13 returned datasets / 810 complex samples**. Every sample meets its absolute output budget and every observed normalized FFT meets delta. A separate genuine computed-range case rejects with `unrepresentable_volume_order_otf`. The actual existing volume separator agrees with an independent represented-matrix least-squares solution. These are local finite-grid measurements, not instrument calibration or backend error theorems.

Inputs, expected/output arrays, exact gains, all normalized FFT arrays, frequencies, numerical errors and budgets are stored in [the numerical JSON](../references/scientific/volume-order-transfers-comparison.json). The generator used the locked product process: Python 3.13.12 / NumPy 2.5.3 on macOS 27 arm64. Native wider longdouble is unavailable. All numbers below are dimensionless except sampling (micrometres), frequencies (cycles/micrometre) and composition intensities (arbitrary specimen units).

## Independent calculation and stored inputs

The observer is separately written and imports no frozen fixture/test helper or legacy code. It computes 750-digit Decimal direct sums on exact float64/complex128 snapshots. Pi comes from converged Machin arctangent series; sine/cosine come from converged Taylor series with exact quarter-turn roots. The observer uses no FFT or product output as an expectation. Decimal exponent range retains q and F without native overflow/underflow. Residual observer rounding near mathematical zero is reported below as <1e-740, rather than an assertion of exact floating equality. This precision is ample for these grids and their budgets; it is not a general arbitrary-size theorem.

For every centered integer frequency triple k, the observer sums

```text
p = stored_PSF / sum(stored_PSF)
E_m(k) = sum_r p[r] * g_m[z] * exp(-2*pi*i*sum_j k_j*(r_j-o_j)/N_j)
g0 = 1; order layout = 0,+1,+2
G_m = max_z(max(abs(real(g_m)),abs(imag(g_m)))) or 1
```

The asymmetric PSF is `(3,2,4)`, nonseparable and unequal odd/even on z/y/x; spacing is `(0.45,0.16,0.11)` µm and origin `(2,1,3)`. Its centered axes are z modes `[-1,0,1]`, y `[-1,0]`, x `[-2,-1,0,1]`; physical grids are stored with independent precise expectations. Positive and negative signed real/imaginary samples remain. Constant complex gain, zero side DC with nonzero side transfer, and zero side rows are separate datasets. A `(4,2,3)` exact-quarter axial phasor/cosine demonstrates shifts. Joint periodic rolling of PSF/profiles and origin leaves the mathematical transfer unchanged.

Range datasets include all-maximum/all-q detection mass, mixed maximum/q mass, stored 0.7F component gains in the safe interior, an origin delta with F+iF, large gain on zero-weight axial samples, exact q/2 final rounding and mixed-quantum cancellation. The native range rejection uses an `(8,1,1)` displacement delta at z=1, origin zero and F+iF: one axial root rotates it to approximately sqrt(2)*F in one component. The rejection dataset includes its independent full expected array; no partial output exists.

## Measured errors and allowances

Let eps=2^-52, q=2^-1074 and F=max float64. With M spatial samples, the absolute complex error allowances are `128*M*eps+4*M*q` for order 0 and `256*M*eps*G_m+8*M*q` for orders 1/2. The normalized FFT allowance is `delta=128*M*eps+4*M*q`. These are project budgets, evaluated with Decimal arithmetic. No relative or subnormal-retention promise applies.

At M=24, delta is approximately 6.8212102633e-13. At M=2 and G=q, the side budget is approximately 16q=7.9050503335e-323. Losing q/2=2.4703282292e-324 therefore uses about 0.03125 of that budget. Expected q/2 is retained in the JSON and plotted as 0.5 after exact division by q. The ordinary native output may be zero. Success conditions use component inequalities, never complex magnitude: the safe-interior and zero-weight-large-gain datasets independently satisfy `abs(E_component)+G*delta <= F`. The origin delta F+iF is a measured valid boundary success without a promise for other boundary roundoff.

| Dataset | Order | G | Max complex error | Absolute budget | Error / budget |
|---|---:|---:|---:|---:|---:|
| asymmetric | 0 | 1.0000E+0 | 5.3556E-17 | 6.8212E-13 | 7.8514E-5 |
| asymmetric | 1 | 3.0000E+0 | 1.9821E-16 | 4.0927E-12 | 4.8430E-5 |
| asymmetric | 2 | 4.0000E+0 | 2.2997E-16 | 5.4570E-12 | 4.2143E-5 |
| constant_gain_zero_DC | 0 | 1.0000E+0 | <1e-740 | 6.8212E-13 | 2.4629E-737 |
| constant_gain_zero_DC | 1 | 3.0000E+0 | <1e-740 | 4.0927E-12 | 1.4055E-737 |
| constant_gain_zero_DC | 2 | 1.0000E+0 | <1e-740 | 1.3642E-12 | 7.3301E-738 |
| zero_side_rows | 0 | 1.0000E+0 | 5.3556E-17 | 6.8212E-13 | 7.8514E-5 |
| zero_side_rows | 1 | 1.0000E+0 | 0 | 1.3642E-12 | 0 |
| zero_side_rows | 2 | 1.0000E+0 | 0 | 1.3642E-12 | 0 |
| phasor_cosine | 0 | 1.0000E+0 | 1.1102E-16 | 6.8212E-13 | 1.6276E-4 |
| phasor_cosine | 1 | 2.0000E+0 | 2.4825E-16 | 2.7285E-12 | 9.0986E-5 |
| phasor_cosine | 2 | 1.0000E+0 | 3.9475E-17 | 1.3642E-12 | 2.8935E-5 |
| translated | 0 | 1.0000E+0 | 5.3556E-17 | 6.8212E-13 | 7.8514E-5 |
| translated | 1 | 3.0000E+0 | 1.9821E-16 | 4.0927E-12 | 4.8430E-5 |
| translated | 2 | 4.0000E+0 | 2.2997E-16 | 5.4570E-12 | 4.2143E-5 |
| maximum_detection_mass | 0 | 1.0000E+0 | <1e-740 | 6.8212E-13 | 3.0936E-737 |
| maximum_detection_mass | 1 | 3.0000E+0 | 1.8957E-16 | 4.0927E-12 | 4.6320E-5 |
| maximum_detection_mass | 2 | 4.0000E+0 | 3.5248E-16 | 5.4570E-12 | 6.4593E-5 |
| subnormal_detection_mass | 0 | 1.0000E+0 | <1e-740 | 6.8212E-13 | 2.4777E-737 |
| subnormal_detection_mass | 1 | 3.0000E+0 | 1.8957E-16 | 4.0927E-12 | 4.6320E-5 |
| subnormal_detection_mass | 2 | 4.0000E+0 | 3.5248E-16 | 5.4570E-12 | 6.4593E-5 |
| safe_interior | 0 | 1.0000E+0 | 5.3556E-17 | 6.8212E-13 | 7.8514E-5 |
| safe_interior | 1 | 1.2584E+308 | 1.0903E+292 | 1.7167E+296 | 6.3509E-5 |
| safe_interior | 2 | 1.2584E+308 | 1.0903E+292 | 1.7167E+296 | 6.3509E-5 |
| finite_F_plus_iF_delta | 0 | 1.0000E+0 | 0 | 6.8212E-13 | 0 |
| finite_F_plus_iF_delta | 1 | 1.7977E+308 | 0 | 2.4525E+296 | 0 |
| finite_F_plus_iF_delta | 2 | 1.7977E+308 | 0 | 2.4525E+296 | 0 |
| subnormal_q_over_2 | 0 | 1.0000E+0 | 0 | 5.6843E-14 | 0 |
| subnormal_q_over_2 | 1 | 4.9407E-324 | 2.4703E-324 | 7.9051E-323 | 3.1250E-2 |
| subnormal_q_over_2 | 2 | 4.9407E-324 | <1e-740 | 7.9051E-323 | <1e-740 |
| cancellation_mixed_quantum | 0 | 1.0000E+0 | 4.9407E-324 | 1.1369E-13 | 4.3458E-311 |
| cancellation_mixed_quantum | 1 | 1.0000E+0 | 6.9871E-324 | 2.2737E-13 | 3.0730E-311 |
| cancellation_mixed_quantum | 2 | 1.0000E+0 | 6.9871E-324 | 2.2737E-13 | 3.0730E-311 |
| mixed_detection_range | 0 | 1.0000E+0 | 5.0175E-17 | 6.8212E-13 | 7.3558E-5 |
| mixed_detection_range | 1 | 3.0000E+0 | 3.9665E-16 | 4.0927E-12 | 9.6917E-5 |
| mixed_detection_range | 2 | 4.0000E+0 | 8.4552E-17 | 5.4570E-12 | 1.5494E-5 |
| large_gain_zero_weight | 0 | 1.0000E+0 | 2.5088E-17 | 6.8212E-13 | 3.6779E-5 |
| large_gain_zero_weight | 1 | 1.7977E+308 | 0 | 2.4525E+296 | 0 |
| large_gain_zero_weight | 2 | 1.7977E+308 | 0 | 2.4525E+296 | 0 |

All per-order normalized errors and deltas are in the JSON. The largest normalized complex discrepancy is approximately 1.3866E-16; all are below their finite-grid allowances. Frequency errors obey `8*eps*abs(k/(N*d))+q`; frequencies are finite, increasing and noncollapsed. The maximum observed frequency coordinate error across these datasets is 4.2666E-16 cycles/µm.

## Actual separator composition

Independent Decimal circular displacement sums form `c_m=K_m*u_m`, with a caller-supplied real specimen and lateral fields `u_m=specimen*exp(2*pi*i*m*x/Nx)`. Independently summed forward and inverse roots then use the actual returned transfer to predict the same fields. All three predicted volumes are stored alongside the independent circular sums. Maximum complex convolution error is 1.4199E-16, below the explicit finite-grid allowance 1.3097E-10 (`4096*M*eps*max_component_gain*max_specimen`). For M=24, the independent discrete transform has `sum(abs(U))/M <= sqrt(M)*max(abs(u))` by Cauchy–Schwarz and Parseval. Thus the side transfer allowance propagates at most `256*M*eps*G*sqrt(M)*max(abs(u)) + 8*M*q*sqrt(M)*max(abs(u))`, well inside the stated ordinary-scale comparison allowance. The measured direct-sum observer uses 750 digits; this allowance is conservative, not fitted to the observed error.

Seven supplied fundamental phases generate real observations from these circular fields. The stored represented matrix uses `c=cos(phi)`, `s=sin(phi)`, `c2=c*c-s*s`, `s2=(2*c)*s`, then coordinate columns `[1,2c,-2s,2c2,-2s2]`. It never evaluates doubled angles. Matrix entries and rounded real observations define the independent exact-real fit. A separate 750-digit Decimal normal-equation elimination supplies this observer; the actual public separator still uses its existing singular value decomposition (SVD) solver. Its H condition number is approximately 1.4142E+0.

Maximum actual separator coordinate error is 2.3953E-16, using at most 1.0415E-5 of the inherited `8192*N*eps*B+8*q` allowance at its voxel. The difference between the represented/rounded fit and ideal circular coordinates is at most 1.0464E-16. The JSON separately preserves both expectations; product outputs are not fitted back into the oracle. Composition SHA-256 is `67ead64642e8279903b70243732b6905b9267a2330f13836b104ab4e2adf3c57` (canonical contents before adding that hash).

## Signed figure and exact identities

[PNG](../figures/volume-order-transfers-comparison.png) and [SVG](../figures/volume-order-transfers-comparison.svg) show every returned order and sample. Columns are signed real and imaginary components. Each row shares limits across both components and all three orders. Lines are independent expectations; crosses are product values. The x index flattens centered z/y/x with x fastest; it is not a physical one-dimensional frequency coordinate. The JSON retains the full physical axes.

Display divisors for `(order0,order1,order2)` are `(1,1,1)` ordinarily; `(1,stored 0.7F,stored 0.7F)` for safe interior; `(1,F,F)` for F+iF delta and zero-weight-large-gain; `(1,q,q)` for q/2. Every divisor is recorded precisely in the JSON and printed on its panels. Expected components are divided in 800-digit Decimal **before** float conversion. This preserves the q/2 witness. Divisors only affect rendering. The rejected range case has no product array and is described numerically above. A visual is not oracle proof.

The base plotting process was Python 3.13.12 / Matplotlib 3.11.0 / Pillow 12.3.0. It read only the saved JSON, imported no product and changed no locked dependency. The task-local Matplotlib configuration lives under ignored C artifacts. The durable PNG is 1890×4590 pixels. One presentation correction moved the legend away from the title and backed scale annotations with white; numerical inputs were unchanged.

| Artifact | SHA-256 |
|---|---|
| Numerical JSON | `00af6fe195f69cb1e4205437406933a637c4306abed0203ab49260d3afcdbd98` |
| SVG | `31248381dc15b5c6c3d1795ee0565f5a6e99e3196f872755f7974c60fb19e973` |
| PNG | `0a5fe27e4a944f9b3d665f5f74a30dcce105ac36df64eda0d933d3b48467e3fc` |
| Independent generator (current portable source) | `93d1d5bf57d72d6c568030d406a955d08eed82deabe17869aa9e821e6a499417` |
| Plot generator (original render source) | `45b42d1575b744fb1dfba63d03a4b706969f5bf8eb939e6c692ed367db002a7d` |
| Plot generator (current portable source) | `8c5f41eff285e5e0f95d18f187a260e70af39fb4d5b9862d3bf0e2a7aed2b9f4` |

Per-dataset hashes use UTF-8 JSON with sorted keys, separators `(',',':')`, no NaN and no trailing newline. Expected arrays use precise decimal component strings in order/z/y/x C order. Native arrays use dtype/shape plus hexadecimal component strings and a separate SHA-256 of contiguous native bytes. `float.fromhex` reconstructs them exactly. These hashes identify the represented problem; they do not prove scientific accuracy.

| Dataset | Input JSON SHA-256 | Expected JSON SHA-256 | Output JSON SHA-256 |
|---|---|---|---|
| asymmetric | `7fac8871c62d9b3fb48f9636468b2ee749d5d0115fafd47d555040129da01878` | `88b627a76b6df66514e1843cb5a38283538c6933a010b52f27d03ef2b33ae2a8` | `c09d1be00b09d8a399dbd5814a9f20e3e7b7cca6161d7fed885d3a3ec067d4d4` |
| constant_gain_zero_DC | `ffdfe8c9e3ad1e9a6ec5c8e8d9f82749fd0a4af5b2fe81a8cebdf390588b1fe7` | `9a736b2fc730779b58661e40091c1a55a52b3d42a5af1f99393200bc1c6bd1ca` | `713d9bc77e34d9f3b56095aa27c40ad3edd0279ff7a2da1b1a8d072f3a76fe7e` |
| zero_side_rows | `8ef526e3e265a2a08ac16504499b7633f63135e1a35af8d6b30a6a1ea9b113ea` | `a70cf3a3db3bd3ef33b581c16bc9ae962dd8b22fcdcf13142ce7a4c33d5d8e8c` | `2912742c636677c08728124cdb3f137e6ea5d547c6bd5154cc01edf35ed1f309` |
| phasor_cosine | `a42b01311e486229134f78b9147c48bdcea7f51b9c5f607ffe7bd485a2131122` | `eaf9cedc86524816ef22e4dbe6269764b8fe181376bd16062c80a5a718e0fc05` | `9b9e6915a25d3951fa9f63571dd9c716289307bd30eaed63602c548bdba4f0b0` |
| translated | `e89a467bc95b4596001f118cca31b5690d2758307db88e056d61756c3f781b10` | `7c1f70efd2ede5a075da353ad3e288ff2cc3afacec120b4eb10908f5c0bd7ad4` | `c09d1be00b09d8a399dbd5814a9f20e3e7b7cca6161d7fed885d3a3ec067d4d4` |
| maximum_detection_mass | `6511ed3a331e6a269a39f7877f940225bb58bfe1de2a38b7e97abd8b6ce348bc` | `19445296070390ef24388b2813feb247847020e289b2c19103feb4ed62458c22` | `e248459bebb21376a95dc1dfa97ff3acaa986f3c7de56a33aeb42792e546f8f3` |
| subnormal_detection_mass | `4b81bf4fc3a027765f2315e8686777922ec3fe26112eb2658cf555b287886c22` | `7c843e81c06a7b7c5663ae1a7c14be5facdf21540942cee4049275eba9742989` | `e248459bebb21376a95dc1dfa97ff3acaa986f3c7de56a33aeb42792e546f8f3` |
| safe_interior | `7ffff8f0b4dda7284fe9eb3ad29263eda8ef39e9729805c923949943de088844` | `8b48735bff3fd482ebeed44757bf9d7cfa5d3071ef0f08ab26c2b0e789d9c348` | `2be8b90ebad1453e292e9bf178901f22fcf0151142a03662f67fd2d2f619cf50` |
| finite_F_plus_iF_delta | `74388a9e27822c94c64a4667ffc2a0f1f40c0b86e27a31fdefd49c6f8f85c196` | `8fd5210f7b78c9e19c9812e69b9f509910576e0f1c2497d0bc5bd7791d129eed` | `46dbcf1ef70c60023fe5437ffe45fc94731dbad29132f2718f0e26f9054002a8` |
| subnormal_q_over_2 | `06f5567355b717f1a30065eabe689a1bd0e49464414df991cd4c283e80598353` | `d85f92ec5e781207b392fa2825970c4eb8e609f26b2da907f2e9443dfd6f2808` | `3601c8f57b6d2dc5ef4b2d0fa789251ef72b9c911347c9adf9197358c62f6750` |
| cancellation_mixed_quantum | `95170d059f299a239feaa2709db462fce024c17eaa5a160b117396b3bde6688e` | `7d8a8ab0a29a599cd1fb89be051456fa2f409c6bfa46a9975ea894ce7813e584` | `e2bdc98cb497d2fba95374e137774064544b8819f9c5875d1cac257e7748f29f` |
| mixed_detection_range | `19fcdcee028fe6fc519d69568d527741be44c09cd9e0ea9197090c9048e965d2` | `3314a0d420688c61b529523ac880b005194eb7ec4b39216d4e1f3a186cfc8c89` | `106c432e6291ab042b6f8cc5a14975c5fc2afde8199568f45ccab90a6e7a1080` |
| large_gain_zero_weight | `a2afdd7ae749ae4ccbafb9cc67bb98e897f9949bee11fe72fa4aa833559ccb49` | `c5cf451e98bd9243cfac906012e66eda28ff7e5c5f9220c7fd0d4294d81d9e2c` | `f736a32c271631002c4e836b0b1c574471815097d6dc4891f121dbf84213649c` |

Reproduction in this worktree uses retained independent generators. Set `PLOT_PYTHON` to a separately supplied plotting interpreter with the recorded Python/Matplotlib/Pillow versions. Its actual executable identity stays in ignored local evidence; the locked product interpreter is referenced as `.venv/bin/python`. No plotting dependency is added to the locked product environment:

The reported comparison generator hash identifies the current source with portable public provenance. The original numerical run used the earlier source retained in ignored local evidence; this metadata correction did not rerun that calculation. Existing figure bytes were retained because all rendered numerical datasets and plot divisors are unchanged. The ignored plot identity preserves the original render-input hash and maps it to the updated JSON hash.

```sh
.venv/bin/python artifacts/axial-order-execution/c-author-comparison.py
MPLCONFIGDIR=artifacts/axial-order-execution/c-author-mpl "$PLOT_PYTHON" artifacts/axial-order-execution/c-author-plot.py
```

The product-process source/lock/contract hashes are stored in the numerical JSON; plotting interpreter, input, script and output identities are recorded in `artifacts/axial-order-execution/c-author-plot-identity.json`. The executed standalone example is in [usage](../usage/volume-order-transfers.md). Focused passes establish no exact-candidate full verification or independent D acceptance.

## Physical limits and sources

This is an algebraic preparation of finite periodic kernels with g0=1. Absolute detection throughput is discarded. Arbitrary coefficients are permitted; they are not evidence of nonnegative illumination, realizable optics or measured calibration. An effective-kernel interpretation requires the axial illumination profile fixed relative to the objective focal plane during scanning. A specimen-fixed axial field requires a different forward model. No infinite-field/continuous-optics convergence, support recovery, interpolation, lateral relocation or three-dimensional reconstruction is asserted.

[The project contract](../contracts/volume-order-transfers-v1.md) supplies API and budgets. [NumPy fftn](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html) documents the production transform boundary and axes; [NumPy FFT convention](https://numpy.org/doc/stable/reference/routines.fft.html) supplies transform context. [Gustafsson et al., equations 5–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) motivates the displacement-dependent illumination kernel. These primary links were opened during C. No measured-instrument or optical simulator calibration claim is made.
