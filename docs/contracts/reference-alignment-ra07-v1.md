# RA07 — fractional finite-window volume band relocation

Version 1.0, 30 October 2026. Owner-authorized RA07 of the RA01–RA15
chain, above completed RA06 commit 106fd79527dbea5853b1223092dfacae0fcdf8d3.
This contract selects the finite estimator before tests or product observations.

## Public boundary and inherited validation

```python
from simrecon import reconstruct_volume_fractional

result = reconstruct_volume_fractional(
    images, order_otfs=calibrations, phases_rad=phases,
    carriers_per_um=carriers, gains=gains, regularization=penalty,
    output_shape_yx=(Ly, Lx), apodization=taper,
)
```

Only images is positional; every keyword is required. Return the existing
six-field `Reconstruction3D`. Preserve every existing operation, including
`reconstruct_volume` and `reconstruct_volume_weighted`.

Images, phases, gains, regularization, order_otfs, output shape, taper,
snapshots, output ownership, phase separation, output physical grids and
corresponding errors inherit the complete public
[integer volume contract](volume-recombination-v1.md), with the sole carrier
and output-support changes below. All fields are validated even for zero
images/transfers/taper. Arbitrary finite complex transfer rows remain valid.
Origins are already encoded in transfers and are not applied a second time.

`carriers_per_um` is a plain ndarray `(R,2)`, real i/u/f kind, all available
widths/endian/layouts accepted; bool/complex/subclasses/masked/nonarrays reject.
Source and native float64 copied values must be finite. Values are y/x
frequencies in cycles per micrometre, with zero axial carrier. Positive,
negative, zero, repeated and integer-equivalent physical carriers are valid.
Invalid representation/shape/conversion/finiteness uses
`invalid_fractional_volume_carriers`. No carrier estimation, modulo reduction,
frequency snapping or automatic calibration/specimen matching occurs.

Let detector sizes be `(Nz,Ny,Nx)`, converted common spacings `(dz,dy,dx)` in
micrometres, and `c_r=(Ny*dy*k_ry,Nx*dx*k_rx)` in detector-bin units. Geometry
uses exact rational products of converted binary64 values, not rounded
intermediate field lengths or a tolerance-based integer decision. Integer
limit means these exact products are integers. Require
`Ly >= Ny + ceil(4*max_r(abs(c_ry)))` and likewise x, and require every native
endpoint relocated by every m=-2..2 to lie within the canonical output-bin
closed interval. Reject insufficient/native-index/unrepresentable dimensions
with `invalid_volume_reconstruction_output_shape`, even for zero data or taper.
No practical-size cap. Output retains field of view and origin index zero.

## Selected estimator: filter before finite phase-ramp relocation

This is an explicit finite estimator, not an asserted reproduction of unexecuted
legacy code. It extends the accepted complex integer fusion, not RA06's real
covariance inverse. The latter solves a different objective in general.

Use the integer contract's represented known-phase least-squares separation,
native centered canonical bins j, normalized negative-exponent DFT coefficients
`D_rm(j)` and signed transfers `E_rm(j)`. In particular negative bands are
conjugate spatial positive bands and negative transfers are all-axis modular
reflection/conjugation of positive native rows. The single canonical even
Nyquist endpoint is retained without splitting. These dependent negative bands
are not new independent observations.

Define `I_rm(v)` by Cartesian complex linear interpolation of the *signed
native transfer array E_rm* on its exact ideal physical nodes. In bin coordinates
its domain is the closed native canonical node hull on each axis; a singleton
axis covers only zero. Exact nodes select that stored component; other points
use the two bracketing nodes and identical real/imaginary weights. Outside this
domain a band is unavailable in the following denominator. This is declared
finite transfer availability, not zero physical transfer or extrapolation.
No physical-support inference, magnitude/phase interpolation, radial averaging,
gauge rotation or normalization is added. Signed rows are formed before
interpolation: at even Nyquist this explicitly retains the integer operation's
modular convention. This interpolant must not be silently replaced by the
RA05 physical-reflection sampler, whose even-endpoint domains differ.

For each r,m and native j, set object coordinate
`a=(jz,jy-m*c_ry,jx-m*c_rx)` in bins, physical frequency
`f_a=(a_z/(Nz*dz),a_y/(Ny*dy),a_x/(Nx*dx))` cycles/µm. For every orientation s
and signed order ell, query `I_s,ell(a+(0,ell*c_sy,ell*c_sx))` when in its
closed native hull. Let

```
H(a) = sum_(s,ell available) abs(gains[s]*I_s,ell(a+ell*c_s))**2
F_rm(j) = conj(gains[r]*E_rm(j))*D_rm(j)/(H(a)+lambda)
```

Use zero for F when its denominator is zero. Its own native row is always
available, but all-zero transfers can give a zero denominator when lambda=0.
Gain enters once in each transfer and squared in H; lambda has squared-transfer
units. No side factor, band-count division, brightness renormalization, hidden
real projection or data-dependent regularization.

Let P=Nz*Ly*Lx. Embed each native filtered coefficient F_rm(j) at its *unshifted*
canonical integer j in a zero-filled output spectrum. Define output samples
`n=(nz,ny,nx)`, 0<=nz<Nz, 0<=ny<Ly, 0<=nx<Lx, and

```
b_rm(n) = sum_native_j F_rm(j) * exp(2*pi*i*(
    jz*nz/Nz + jy*ny/Ly + jx*nx/Lx))
u(n) = sum_(r,m) b_rm(n) * exp(-2*pi*i*m*(
    c_ry*ny/Ly + c_rx*nx/Lx))
Q(q) = sum_output_n u(n)*exp(-2*pi*i*q.n/(Nz,Ly,Lx))/P
T(q) = apodization(q)*Q(q)
volume(n) = sum_output_q T(q)*exp(2*pi*i*q.n/(Nz,Ly,Lx))
```

Return centered T as spectrum and full complex volume. Phase ramps use the
index-zero origin and bounded-angle evaluation of exact rational cycles. Native
embedding introduces no voxel-volume or P/M factor. The native observation
interpolation implicit in these equations is a finite Dirichlet kernel on the
*output* torus, distinct from the transfer interpolant I. Filter-after-shift
generally differs: interpolating native filtered coefficients is not the same
as interpolating observations then applying a continuously sampled quotient.

For noninteger shifts Q generally has tails on every output bin. Those tails
are the selected finite periodic representation, including its seam, not
discarded/cropped signal. The endpoint guard retains all translated native
anchors; it does not make Dirichlet tails compact or eliminate a seam. This
model extends the finite output samples periodically. It assumes no finite
zero exterior and promises no continuum bandwidth/resolution or unique
specimen recovery. At exact integer c every ramp permutes bins; the endpoint
guard prevents wrap loss, I selects native nodes, and the sum recovers the
accepted integer estimator under identical support, lambda and taper.

For fixed inputs other than images this is a real-linear map from raw real
exposures to complex volume. Its complex extension at the signed-band boundary
is a sum of matrices `L_rm diag(w_rm)`, where
`w_rm(j)=conj(g*E_rm(j))/(H(j-m*c)+lambda)` and L is precisely embedding,
positive synthesis, unit-modulus phase ramp and normalized output DFT above.
Under ordinary complex Euclidean coefficient inner products its adjoint is
`diag(conj(w_rm))*L_rm.H`; L.H conjugates the ramp and restricts back to native
bins. Taper is real diagonal and self-adjoint. Verify this finite adjoint
independently. No public adjoint API or new production seam is required.

## Arithmetic, errors, success and boundaries

Use float64/complex128. Inherit integer input errors, separator failures,
caller-buffer/state preservation, unrelated exceptions/warnings, MemoryError,
safe component-scaled Fourier sums and transform/range error codes. Equivalent
direct finite sums or public NumPy Fourier transforms are allowed; no fixed
call count. Each required arithmetic stage (gain transfer, square, accumulated
H, denominator, native quotient, synthesized/ramped bands, band accumulation,
output DFT, taper and volume) must be finite. Zero taper does not rescue an
unrepresentable earlier stage. Translate handled arithmetic to
`unrepresentable_volume_reconstruction`; numerical transform failures to
`volume_reconstruction_transform_failure`. Expected conversion failures stay
at their input boundary. Do not catch unrelated exceptions across the whole
operation. Handled failures emit no arithmetic RuntimeWarning and restore
caller floating/warning policy. Underflow is permitted.

Mandatory moderate success: valid inputs with phase condition<=10, gains in
[1/2,2], transfer real/imaginary magnitudes<=1, images abs<=16, lambda in [0,1],
R*N*Nz*Ny*Nx<=512, P<=512, and every positive denominator>=1/16 must succeed
absent genuine resource/dependency failure when required outputs are finite.
These are sufficient success conditions, never input caps. All-zero images in
this regime produce exact zero arrays. General finite inputs are attempted
with the operational range rule; no universal digit promise.

A derives independent stored-input allowances before observing output from
epsilon, dimensions, phase conditioning, denominator lower bound, interpolation
weights and finite synthesis sums. Expectations include represented input
phase/geometry values, not ideal unrounded ones. Use independent direct sums,
analytic off-bin waves and tiny dense L/adjoint matrices. Separate arithmetic
error, transfer interpolation/model error, finite-window leakage and physical
mismatch. No output-selected input, tolerance, lambda, crop or phase adjustment.

| ID | Distinct obligation / credible wrong outcome |
|---|---|
| F01 | Additive public required bindings, inherited record, integer/weighted compatibility |
| F02 | Inherited image/phase/gain/transfer/taper/output grammar and paired valid alternatives |
| F03 | Physical carrier grammar, exact converted geometry, no snapping/modulo/integer reinterpretation |
| F04 | Complete anchor window and closed endpoint/singleton availability, zero-data guard |
| F05 | Represented phase separation, N>5 projection, negative-band dependence/signs |
| F06 | Full complex signed transfer interpolation, anisotropic physical queries and even modular convention |
| F07 | Cross-orientation/order denominator query a+ell*c, gain and lambda units, zero denominator |
| F08 | Filter-before-shift finite synthesis and distinguishing after-shift comparison |
| F09 | Negative/fractional/order-two placement, odd/even/Nyquist, no hidden tail cropping or negative duplication |
| F10 | Exact integer limit under identical support/normalization, complex canonical Nyquist lift |
| F11 | Index-zero phase origin, field of view, native z, physical-coordinate usage |
| F12 | Independent dense finite L and adjoint, full complex and amplitude agreement |
| F13 | Post-combination taper, zero/nonunit cases and unmasked operational range |
| F14 | Snapshot/caller state, owned mutable outputs/frozen bindings, repeat calls |
| F15 | Moderate success, exact zero and safe transforms versus representability/dependency failure |
| F16 | Executed measured placement/smearing comparison, predeclared independent inputs/bounds and limits |

## Ownership and gate

High-risk scientific/custom-oracle route. Fresh native Sol/high A, fresh blind
B, separate restricted C, fresh D; optional memory/delegation disabled. A owns
only `tests/test_reference_alignment_ra07.py` and
`tests/reference_alignment_ra07_fixture.py`, plus its ignored evidence. A/B
read AGENTS, this contract, integer volume and phase public contracts, and only
PROJECT's architecture/stack/commands/coverage-policy text. No implementation,
history, conversations, Current state, coverage maps or existing lessons.
B additionally reads exact A files and sanitized evidence. Use verified own
source-free diagnostics before imports/probes, including pytest startup.
Apply test-audit authoring questions; A maps distinct inherited decisions and
B independently recalculates/audits omissions and legitimate alternatives.

C owns only `src/simrecon/fractional_volume_reconstruction.py` and additive
exports in `src/simrecon/__init__.py`. No reviewed test/fixture/snapshot,
dependency, gate, workflow/discovery/coverage, skill/policy or unrelated edits.
Coordinator owns contract/task/PROJECT, usage/report/figure driver, packets,
accounting/evidence and useful unique lessons. No legacy/study archive source
inspection/execution/import/link/build/copy. No Superpowers.

Coverage inherits approved behavior plus independent risk review; percentages
advisory, no target/exclusion change. Complete native SQLite/JSON/HTML/file and
global/package scope proof includes every owned src/scripts file, never-imported
files and relevant subprocesses, separately local/Ubuntu24.04/macOS15. Preserve
all installed gates, same-run M25, wheel/source/version/lock/check/base and
environment/ignored-input identities. Focused checks include RA07 tests,
`tests/test_volume_reconstruction.py` and `tests/test_empirical_frequency_sampling.py`.
Exact clean committed full 13-phase `make verify` passes before fresh D and
PR/push. Both hosted platforms and independently qualified original integration,
ordered parents/tree/source/wheel/reader/native artifacts plus completion cleanup
precede review-readiness and exactly one RA08 successor chat. Never start RA16.
No merge/release or unrelated external messages. Human numeric limits not set;
missing actual serving/provider/coordinator meter/money remain unknown.

Retain all prior charges by reference to RA06's sole Current state/ledger, and
all new launch/check failures, reviews, corrections, exposures and measured use.
RA07 sole Current state is ignored `artifacts/ra07/current-state.json`.
Completion cleanup is coordinator-owned: positively identify task-created
disposables, close writers, preserve original evidence/links/referents/ancestors,
cache/environment/Python pins and predecessor containers at original paths.
Any actual destructive operation needs its own applicable A/B/C/D ownership,
checks and review. Verified zero-removal is permitted; no reusable destructive
tool, age-based pruning or predecessor cleanup follows from this contract.
