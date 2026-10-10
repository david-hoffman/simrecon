# Known integer specimen-drift preparation

**Version 1.0. October 7, 2026.** The owner authorized the next coherent unmet roadmap implementation above verified PR #14, including required independent roles, checks, stacked publication and successor creation. This contract selects known integer specimen-drift preparation. Astra/ultra supplied report-only scientific advice; it replaces no acceptance role.

## Public operation

```python
from simrecon import DriftCorrection, correct_integer_drift
prepared = correct_integer_drift(images, phases_rad=phases,
    carrier_bins_yx=carrier, displacements_pixels_yx=displacements)
```

Only images is positional; all three keywords are required. Ordinary binding TypeError remains. One call handles one illumination orientation. This pure array operation prepares existing separation/reconstruction inputs; it estimates nothing and invokes neither reconstruction nor calibration. No dependency, file I/O, CLI or existing API change.

images is a plain NumPy ndarray of shape (N,Ny,Nx), all dimensions >=1. phases_rad is a plain ndarray of shape (N,). Both accept every signed/unsigned integer or real floating dtype (kinds i/u/f), either endian, strided/Fortran/read-only arrays and signed values. Reject bool, complex, object/string/structured/datetime arrays, subclasses/masked arrays, lists and nonarrays. Source and converted float64 values must be finite. Convert to independent float64 snapshots before numerical processing. Ordinary rounding and finite conversion underflow are permitted; converted values define the operation. Finite wider values overflowing float64 are invalid. No artificial image-size or intensity cap, no phase principal-interval input restriction and no N>=3 or phase-rank requirement. Repeated phases and degenerate corrected phase sets are valid preparation inputs.

carrier_bins_yx is a plain signed/unsigned integer ndarray of shape (2,). displacements_pixels_yx is a plain signed/unsigned integer ndarray of shape (N,2). Reject all other dtype kinds (including integer-valued floats/bools), subclasses, containers and malformed shapes. All values of permitted integer dtypes are valid, including int64/uint64 extrema; interpret each exactly as a Python integer before arithmetic. No canonical range restriction. Periodic aliases are valid. Snapshot both integer arrays before processing; never pass them through float64 or overflowing fixed-width products.

| Invalid obligation | SimreconError code |
|---|---|
| images type/dtype/shape/source or converted finiteness | invalid_drift_images |
| phases type/dtype/count/source or converted finiteness | invalid_drift_phases |
| carrier type/dtype/shape | invalid_drift_carrier |
| displacements type/dtype/shape/count | invalid_drift_displacements |

Precedence for simultaneous invalid inputs and message prose are unspecified. Catch only expected conversion TypeError/ValueError/OverflowError as validation errors. MemoryError and unrelated exceptions propagate unchanged, with no partial result. Preserve all caller storage on success/failure. No guarantee covers concurrent external mutation.

## Scientific model and sign

d_p=(d_py,d_px) is specimen content translation relative to stationary illumination and a fixed periodic shift-invariant imaging system. k=(ky,kx) is the integer detector-bin illumination carrier. The finite periodic acquisition model is

```text
L_p(y,x) = a*[1+m*cos(2*pi*(ky*y/Ny+kx*x/Nx)+phi_p)]
I_p = h circular-convolved with [s(y-d_py,x-d_px)*L_p(y,x)]
J_p(y,x) = I_p((y+d_py) mod Ny,(x+d_px) mod Nx)
phi'_p = phi_p + 2*pi*(ky*d_py/Ny+kx*d_px/Nx) modulo 2*pi
J_p = h circular-convolved with
      [s(y,x)*a*(1+m*cos(2*pi*(ky*y/Ny+kx*x/Nx)+phi'_p))]
```

The last equality follows by changing the periodic convolution coordinate: translating the observation translates both factors inside the convolution; the specimen returns to reference coordinates and the stationary illumination gains the positive phase increment. Integer carriers make illumination periodic across wrapped borders. h may be asymmetric; no OTF input is needed for this identity. Pixel alignment rolls by **negative d**; phase correction has **positive k dot d**. Do not derive specimen drift by rolling a complete stationary acquisition: that also moves illumination and models a different system.

This identity concerns the specified finite model. Camera/image motion, jointly translated illumination, changing specimens, nonperiodic borders, noninteger carriers, fractional shifts, spatially varying motion and unknown independent phase errors are outside this contract. Existing estimate_translation requires comparable equal-intensity references and cannot automatically infer d from different raw SIM phases. Supplied shifts carry no accuracy/confidence claim.

## Exact pixel operation and circular phase arithmetic

For converted snapshots M and phi, returned images obey the exact indexed permutation J above, with no interpolation, scaling, background subtraction or clipping. For each frame compute using exact integers:

```text
P = Ny*Nx
r_p = (ky*d_py*Nx + kx*d_px*Ny) modulo P, in [0,P)
q_p = correctly rounded float64 of the exact rational r_p/P
alpha_p = float64((2*np.pi)*q_p)
z_p = (cos(phi_p)+i*sin(phi_p)) * (cos(alpha_p)+i*sin(alpha_p))
```

The sine/cosine values in z are the supported NumPy float64 results, treated as exact real numbers in this target. The complex product and its normalization z/abs(z) define a real-arithmetic target, not a requirement to use a particular backend or product implementation. Returned phases are finite native float64 principal angles in [-np.pi,np.pi]. Require

```text
abs((cos(returned_phi_p)+i*sin(returned_phi_p)) - z_p/abs(z_p))
    <= 512*2^-52
```

The output sine/cosine here are likewise represented NumPy values. This conservative circular acceptance budget is a project choice, not a backend theorem. Near the branch cut either endpoint representation is legitimate; compare phasors, not ordinary angle subtraction. Do not add alpha directly to a huge phi or reduce the supplied phase by rounded 2*pi before evaluating its trig values. Large finite phases use their directly represented sin/cos meaning inherited from separation. If q rounds to 1.0 for an enormous period, it remains valid. Independent analytic rational-cycle checks supplement the represented-input oracle.

All handled conversion/arithmetic emits no RuntimeWarning and preserves the caller's NumPy error mode. Do not suppress unrelated warning categories or catch unrelated numerical/programming exceptions. No backend-specific injected solver failure or private internal hook is required. Ordinary allocation MemoryError remains unchanged.

## Result and composition

Return frozen-binding DriftCorrection with exactly the public fields images and phases_rad. Each is an independently owned mutable native float64 C-contiguous ndarray, respectively (N,Ny,Nx) and (N,). They alias no caller storage, each other or another call's arrays. No direct-construction validation is required.

Use prepared.images/prepared.phases_rad directly with separate_phases when N>=3 and its numerical rank requirement holds. For reconstruct, assemble prepared arrays for each orientation into its (R,N,Ny,Nx)/(R,N) inputs, and supply all existing required calibration/wavevector/gain/ridge/mask arguments. For spacing (dy_um,dx_um), integer carrier maps to cycles/um (ky/(Ny*dy_um),kx/(Nx*dx_um)). Preparation imposes no phase-rank check: downstream separation may reject a corrected set even when the original angles were identifiable. No reconstruction success, physical recovery, OTF support, noise, fit acceptance or automatic correction policy is added.

## Scenario inventory and evidence

| ID | Observable obligation and concrete risk |
|---|---|
| D01 | Exports, required binding, frozen record and native result representation |
| D02 | Permitted image storage/dtype/conversion and invalid image rejection |
| D03 | Permitted phase storage/range/conversion/count and invalid phase rejection |
| D04 | Exact integer carrier domain, periodic aliases/extrema and invalid carrier rejection |
| D05 | Exact integer displacement domain/count/extrema and invalid displacement rejection |
| D06 | Exact all-pixel periodic indexing, content/correction signs, odd/even/singleton axes |
| D07 | Positive rational phase increment, robust huge-phase handling, circular budget/branch cut |
| D08 | N=1/repeated or corrected-degenerate phases accepted without hidden rank/fit rules |
| D09 | Snapshots/ownership/preservation, warning/error modes, unchanged MemoryError/unrelated exceptions |
| D10 | Independent specimen-before-illumination finite-convolution identity with asymmetric kernel |
| D11 | Real downstream separation/reconstruction composition under existing contracts, executed usage and actual measured comparison |
| D12 | Existing interfaces/dependencies/gates and stated model limitations preserved |

Each distinct guarantee/rejection/outcome receives blind A mapping; rows are inventory headings, not a scenario cap. A owns independent analytic/indexed/finite-sum fixtures. B independently challenges units/signs, legitimate positive inputs, extrema, oracle validity, margins and omissions before C. Prefer real public composition; no product solver or repeated modular algorithm as the sole scientific oracle. C supplies executed usage and a measured report with independent stored inputs, actual corrected outputs/phase phasors and downstream results, plus a deliberately wrong pixel-only correction comparison. Distinguish stored/trigonometric roundoff from model mismatch. No image screenshot oracle or extra scientific accuracy promise.

High-risk numerical/custom-oracle route: fresh native blind A/B, restricted fresh C and fresh D after exact clean canonical make verify. Inherit PROJECT's approved behavior/risk coverage and complete native report-integrity policy; percentages advisory, no selected threshold or exclusions. All configured push/PR Ubuntu24.04/macOS15 jobs remain binding. No numeric review/scenario/repair/time/execution limits were set. The single task pointer carries evidence/accounting outside tracked candidate bytes; prior chain accounting remains linked intact.

Opened primary API references: [NumPy periodic roll](https://numpy.org/doc/stable/reference/generated/numpy.roll.html), [phase angle representation](https://numpy.org/doc/stable/reference/generated/numpy.angle.html), [radian sine](https://numpy.org/doc/stable/reference/generated/numpy.sin.html). The acquisition identity and all API/error/accuracy choices above are this task's contract, not claims supplied by those references.
