# RA12 — finite-model mathematical expectations

**Version 1.0. Intake expectation seed.** This document fixes mathematical
obligations drawn from the approved finite optical model. It defines no new
runtime interface, statistical confidence guarantee or accepted test checkpoint.
The [operational handoff contract](reference-alignment-ra12-v1.md) records the
owner's subsequent choice: a predictively validated estimate with a finite
ambiguity audit, global operator identification explicitly unestablished.
Identified-operator results below remain conditional mathematics. They do not
create an exhaustive per-input certificate prerequisite. Fresh native A/B/C/D
remain required.

## Model and information boundary

Use the [finite optical expectation](simulation-optics-v1.md), including its
complete midpoint source and pixel sums, exterior-zero boundary, clear finite
pupil, source-minus-focus axial sign and one common intensity normalization.
Distances are micrometres (µm), lateral carriers are cycles/µm, and phases are
radians. The [finite bead fit](image-only-bead-calibration-v1.md) supplies an
observation-derived candidate, not identification of its physical parameters.
Its finite polling and rescores do not supply global uniqueness or uncertainty.

The selected synthetic acquisition uses a common source dose and camera gauge.
Central-only illumination is normalized to one. This is the acquisition model's
unilluminated reference, rather than an inference that switching off physical
side beams preserves total instrument power. A different relative central versus
structured dose requires actual information; a common camera correction cannot
repair it.

Raw calibration images, declared geometry and image-derived camera estimates are
allowed. Generator bead positions, phases, beam powers, camera coefficients,
optical transfer arrays, noiseless means and evaluator selections cannot enter
the observation-only inference path. Independently generated means may define
an explicitly labeled noiseless mathematical control; they are not acquired noisy
images. A known-input diagnostic remains separate.

## Squared-field expansion

Let `d = source_z - focus_z`, `alpha = 2*pi*kappa*d`,
`theta = 2*pi*q dot source_yx + phi`, and
`S = a0**2 + a_plus**2 + a_minus**2 > 0`. For the approved nonnegative real beams,

```text
I = 1 + U*cos(alpha)*cos(theta)
      + V*sin(alpha)*sin(theta) + W*cos(2*theta)
U = 2*a0*(a_plus+a_minus)/S
V = 2*a0*(a_plus-a_minus)/S
W = 2*a_plus*a_minus/S
```

The phase-independent component is exactly one. Therefore the complete
central-only expected image is the structured model's phase-independent image
when source, dose, geometry and camera relation are shared. This is not an
average of nine possibly irregular exposures. A common affine camera correction
preserves the equality of expectations conditional on that independently
estimated correction; it does not establish an unbiased electron scale.

## Exact nine-exposure phase-curve result

Flatten one orientation's expected images into columns. Let `y0` be its shared
central-only expected image, and define

```text
X[:,p] = y_p - y0
v(phi) = (cos(phi), sin(phi), cos(2*phi), sin(2*phi))
X = F * [v(phi_1), ..., v(phi_9)]
```

The finite source, pupil and pixel sums are linear, so this factorization retains
their complete contributions. Suppose `rank(X)=4` and all nine columns of `X`
are distinct. Every equally fitting physical alternative then has
`v(phi'_p)=T*v(phi_p)` for an invertible real four-by-four matrix `T`.

The identities

```text
x1**2 + x2**2 = 1
x3 = x1**2 - x2**2
x4 = 2*x1*x2
```

after substitution of `T*v(phi)`, are trigonometric polynomials of degree at
most four. Distinct image columns imply nine distinct phases modulo `2*pi`.
Nine distinct zeros force each such polynomial to vanish identically. Thus `T`
maps the whole trigonometric moment curve into itself.

Its first complex coordinate is a Laurent polynomial with exponents among
`{-2,-1,1,2}` and constant modulus one on the unit circle. It must be a monomial:
otherwise the coefficient at the largest-minus-smallest exponent in its modulus
squared is nonzero. Compatibility with the second harmonic restricts its
exponent to `+1` or `-1`. Consequently every alternative phase vector has

```text
phi'_p = phi_p + delta, or phi'_p = -phi_p + delta, modulo 2*pi
```

with one common sign and offset. Additional physical constraints may eliminate
some offsets or reflections; the theorem does not assert that all are physical.
It identifies no carrier, finite bead profile or beam ratio by itself.

This is an exact expectation theorem. Distinct noisy raw images do not establish
distinct physical phases. A numerical rank threshold, a small residual or a local
Jacobian rank does not prove its hypotheses or give a global numerical stability
bound. Subtracting a shared noisy central image also creates correlated errors
between the nine differences. Noise, optical arithmetic allowance, conditioning
and source/pupil/pixel discretization require separate reporting.

## Finite-sphere ambiguity that changes specimen predictions

Take a legal single-focus calibration volume: `Nz=1`, `Dz=0.125` µm, with three
complete nonoverlapping radius-`0.050` µm spheres centered axially at `0.0625` µm.
Use the prescribed source refinement `(8,8,8)` and any legal lateral field large
enough to contain them. Their occupied source sites pair exactly at axial
displacements `d` and `-d` about that focus. Paired sites have equal weights,
identical lateral coordinates and equal finite clear-pupil detection response,
because `h_Q(r,d)=h_Q(r,-d)`.

Compare beam amplitudes `(4,2,1)` and `(4,1,2)`, with identical nonzero carriers,
actual phase arrays, camera relation and source profiles. `U` and `W` agree;
`V` changes sign. The odd axial term cancels for every paired calibration site.
Every central, nine-exposure training and repeated first-five calibration
expectation is therefore identical. Independent camera repeats have the same
observation distribution under the shared camera law.

For an unchanged specimen source away from a focus, the illumination difference
is instead

```text
I_(4,2,1) - I_(4,1,2)
    = (16/21)*sin(2*pi*kappa*d)*sin(theta).
```

It is nonzero for permitted source/focus/phase choices. This is a material
specimen-changing alternative, even when the actual first-five physical phases
are reused. An identified handoff must be unavailable without actual independent
information that distinguishes these alternatives. Both can remain as diagnostic
predictions; retaining them does not make a single operator identified. This
example does not prove ambiguity for the retained eight-focus calibration
acquisition.

## Harmless and material alternatives must remain distinct

For the full physical field, the simultaneous transformation

```text
q -> -q, phi -> -phi, (a_plus,a_minus) -> (a_minus,a_plus)
```

preserves illumination everywhere. With a shared beam triple, apply its label
exchange consistently across orientations. Occupancy-equivalent bead centers
and bead permutation can also leave the finite prediction unchanged. Neither
uniqueness of those labels nor an absolute beam-amplitude scale is required.
Setting the first fitted exposure phase to zero without transforming responses
is not the prescribed calibration gauge.

At zero carrier, different beam/phase tuples can agree on calibration exposures
and disagree at genuinely new phase settings. In the selected stationary mode,
however, the specimen reuses the actual first-five calibration phases and zero
carrier makes coordinate transfer zero. Such a construction alone does not prove
a material specimen ambiguity for that selected mode.

For origin labels `Ocal` and `Ospec`, transfer once using

```text
phi_spec = wrap_physical(phi_cal + 2*pi*q dot (Ospec-Ocal)_yx)
```

with the common sign/side gauge. The existing specimen fit already accepts
phases anchored at the specimen origin and performs no transfer itself. Its
half-cell source coordinates belong to that physical model; they must not be
silently replaced by another model's index-zero coordinates or counted twice.

## Remaining operational obligation

A positive identified handoff needs an independently justified distinction
between material alternatives and harmless parameter labels over its declared
supported information class. Phase-curve uniqueness is only one component.
Neither finite local optimization nor conditional RA09/RA10 diagnostics supply
a global finite bead-profile/carrier identification result automatically.

An exhaustive certificate is a sufficient technique, not an adopted additional
universal guarantee. The operational contract must state the actual availability
claim, numerical model, uncertainty, limitations and independently testable
positive and unavailable outcomes before formal test design. No hypothetical
phase sensor, known source support or true calibration array may be inserted
to force success. Noise diagnostics need not promise statistical confidence.
