# Comparable raw references require a motion definition

**Version 1.0.** Report-only Phase 5 intake. Structured illumination microscopy (SIM) changes image contrast deliberately between phase exposures. A displacement score between those exposures therefore cannot, by itself, identify motion. The delivered [volume translation operation](../contracts/volume-translation-estimation-v1.md#objective-coordinates-and-numerical-meaning) measures periodic integer displacement between **supplied comparable equal-intensity volumes**. It constructs no raw reference and identifies no physical mechanism.

The evidence supports conditional reference constructions, not a general raw-phase drift estimator. Complete stationary phase cycles can yield a comparable zero-order image. A single changed-phase exposure generally cannot. Actual acquisition provenance does not settle whether the first 3D case should represent specimen, camera/image or focal-plane motion. That one choice remains for the owner; no mechanism, new threshold or numerical behavior is selected here.

## Evidence and its authority

| Evidence class | Opened source and locator | What it establishes |
|---|---|---|
| Approved public boundary | [2D specimen correction](../contracts/integer-drift-correction-v1.md#scientific-model-and-sign), [volume displacement](../contracts/volume-translation-estimation-v1.md), [order transfers](../contracts/volume-order-transfers-v1.md#operation-and-scientific-meaning) | Existing narrow operations and exclusions; no new scientific authorization |
| Selected development model | [Synthetic 3D model, illumination/scan and camera relation](../models/synthetic-3d-acquisition-v1.md#illumination-and-axial-scan) | Finite periodic, linear, noiseless five-order model; axial profile follows the focal plane; drift/fading excluded |
| Primary theory | [Gustafsson et al. (2008), pp.4958–4959, equations 1–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) | Linear emission/detection; focal-plane-relative axial structure belongs in each effective detection kernel; known phase diversity separates mixed orders |
| Observed source possibilities | [Phase-1 matrix](../plans/scientific-phase1-acquisition.md#target-matrix); selected H/S/D text below | Possible settings and reference paths; no owner configuration or independent oracle |
| Owner facts | [O1–O5 and S10/S11 register](../plans/scientific-phase1-decisions.md) | Relevant acquisition timing, effective flags, intensity corrections and motion meaning remain unknown |
| Derived implications | Algebra and counterexamples below; independent discovery lanes M01/S01 retained locally | Conditional statements about declared models, not measured performance or approved algorithms |

The opened paper has DOI `10.1529/biophysj.107.120345`. The locally retained PDF is 1,699,729 bytes, SHA-256 `b91f2697d05bb8c77ab88179034548003da919cf287856278af379e7104baf09`. Original text identities and read limits are in `artifacts/raw-phase-motion-intake-20261018/paper-identity01.json` and `S01/report.md`. No paper body or ignored reference source is shipped. A web screenshot failed; the primary equations were read as parsed text, with the original PDF retained for inspection. No reference C program was built, invoked or executed.

## Three distinct motion models

Use the selected finite grid with index `n=(nz,ny,nx)` and spacing `Delta=(dz,dy,dx)` in micrometres (µm). Define content translation `T_d f[n]=f[n-d]`, circularly, for integer voxel displacement `d`. Physical displacement is `d*Delta`, component by component. Let lateral carrier `q` have units cycles/µm and `Q(j)=2*pi*q·(jy*dy,jx*dx)` radians. For signed orders `m=-2,...,2`, write the stationary observation as

```text
A_phi s[n] = sum_m exp(i*m*phi) sum_j K_m[n-j] s[j] exp(i*m*Q(j))
K_m[u] = h[u] g_m(uz*dz)
beta(d) = 2*pi*q·(dy_index*dy, dx_index*dx).
```

Here the `dy_index`/`dx_index` components belong to displacement `d`; `dy`/`dx` denote physical sample spacing. Signed conjugate orders make the observation real. This notation expresses the selected model's algebra, with no new numerical implementation or rounding contract.

| Mechanism | Declared observation | After aligning by `T_-d` | Consequence for references |
|---|---|---|---|
| Specimen translates relative to stationary lateral illumination and fixed detection/axial kernels | `A_phi(T_d s)` | `A_(phi+beta(d)) s` | Alignment changes effective illumination phase. A full raw-image roll alone generally fails. Pure axial specimen translation has `beta=0` only under these displacement-frame kernels and lateral-only carrier. |
| Image/detector coordinates translate after formation | `T_d(A_phi s)` | `A_phi s` | Alignment restores the same phase; adding a specimen phase correction would change the model. This is a declared image-coordinate transformation, not proof that a real camera produces only that effect. |
| Focus/scan origin moves by axial offset `a` while detection and axial illumination move together | `sum_m,j h[n+a*ez-j]g_m((nz+a-jz)*dz)s[j]exp(i*m*(Q(j)+phi))` | Stored volume is `T_(-a*ez)A_phi s` | Indistinguishable here from specimen displacement `-a*ez`. If only detection moves or the axial illumination changes independently, the kernel changes and this identity need not hold. |

These are alternatives, not exhaustive models of a microscope. Changing aberration, deformation, scan-step spacing, rolling exposure, illumination motion or a mixture needs another declared forward relation. “Axial drift” alone does not specify which argument of `h` or `g_m` changed.

For specimen translation, substitute `j=l+d`:

```text
A_phi(T_d s)[n]
 = sum_m,l K_m[n-d-l]s[l]exp(i*m*(Q(l)+phi+beta(d)))
 = T_d(A_(phi+beta(d))s)[n].
```

Thus the negative voxel alignment and positive phase increment agree with the existing 2D specimen contract. A shift by one illumination period parallel to `q` gives `beta=2*pi`; a perpendicular shift gives zero. Units cancel: cycles/µm × µm × radians/cycle = radians. Axial motion shifts both `h` and the displacement-frame `g_m` together in this derivation; it does not leave a profile fixed at its old array locations.

For contrast, an axial illumination factor fixed in specimen/laboratory coordinate, `g_m(jz*dz)`, becomes `g_m((lz+dz_index)*dz)` after substitution. It cannot generally be absorbed into a translated unchanged kernel. Translating only `h` while retaining the old `g_m` likewise changes their product. This is why the selected [order-transfer interpretation](../contracts/volume-order-transfers-v1.md) cannot silently be reused for every axial motion mechanism.

## Which observations can form comparable references?

For one stationary cycle write `D_p=c0+sum_(m!=0) c_m exp(i*m*phi_p)`. Real weights `w_p` extract `c0` exactly in this algebra if

```text
sum_p w_p = 1
sum_p w_p exp(i*m*phi_p) = 0,  m=1,2
```

and the same `c_m` apply throughout. Equal weights on five evenly spaced **actual** phases satisfy both harmonic sums by the finite geometric series. Three balanced actual phases also cancel orders 1 and 2 and can extract zero order alone, although they cannot identify all five real component coordinates. This does not relax the existing separator's five-phase/full-rank input requirement. Their common phase origin is immaterial. Unequal phases can use justified full-rank separation weights; nominal commands alone do not establish them. Algebraic exactness is not a new floating-point accuracy or noisy-estimation promise. The existing [known-phase separator](../contracts/volume-phase-separation-v1.md) retains its own represented-matrix contract.

| Candidate construction | Sufficient premises | Missing information or failure |
|---|---|---|
| Whole differently phased raw exposures | Same underlying image after only the declared displacement | Phase contrast usually changes even with zero motion. No general comparability. |
| Mean of a complete cycle | Common specimen state, common kernels/intensity scale; actual harmonic sums vanish | Within-cycle motion, phase error, fading or exposure-dependent gains break cancellation. A complete cycle is not sufficient by its count alone. |
| Known-phase separated zero order | Common component arrays and identifiable actual phase matrix; legitimate supplied phases | Unknown phase truth cannot be borrowed from the evaluator. Motion within the cycle invalidates the common-component premise. |
| Separated side-order magnitude | Stable cycles and valid separation, fixed order response and equal scale; `abs(c_m)` removes the scalar motion/phase gauge | Magnitude can discard position information. Constant/zero magnitudes remain ambiguous. A new combined-order objective needs its own contract. |
| Demodulated complex order | Common complex phase gauge; remove the known lateral modulation after valid separation | Algebraically translates with the specimen, but complex arrays are outside the current real-volume translation interface. |
| Repeated same-phase exposures | Fixed imaging relation/scale and the matching physical motion model | For specimen translation, equal commanded phase still requires `beta(d)=0 mod 2*pi`, or a justified matched effective phase. Using unknown displacement to construct that match is circular. |
| Dedicated unmodulated or switch-off/combined exposure | Acquisition physics proves a common contrast image; timing/dose/background relation recorded | Extra exposures are not present by declaration alone. Nonlinear switch-off data do not inherit the selected linear five-order relation. |
| Joint raw-data motion/phase/gain fit | Explicit selected forward model, gauges, objective, information outcomes and independent expectations | A future research contract, not a consequence of low residual or existing separate estimators. |

Separate cycles with one fixed displacement per cycle can have zero-order references related by `T_d`, because the side orders cancel within each cycle. For specimen motion their shared phase offset `beta(d)` does not affect those harmonic sums. This supports a possible **between-cycle** reference construction. It supplies no per-exposure displacement, and between-orientation use additionally requires the same zero-order transfer/brightness and a valid reuse rule. Empirical zero-order responses need not share the synthetic model's `g0=1`.

## Counterexamples and identifiability

1. **Apparent motion without specimen motion.** With identity detection and a uniform specimen, a legitimate nonconstant periodic illumination `I_phi(x)=1+b*cos(Q(x)+phi)`, `0<b<=1`, changes with phase. If the sampled phase increment equals a spatial illumination shift, two raw frames are exact translates despite zero specimen motion. Identical raw evidence can arise from a camera shift with unchanged phase. The displacement objective cannot identify which mechanism generated it. This illustrative one-harmonic subcase demonstrates failure; it selects no modulation bound for a new API.
2. **Averaging a moving cycle does not restore a stationary image.** Even with constant illumination, averaging `T_0 s` and `T_d s` gives two displaced copies for a localized `s`, not generally one translated `s`. With patterned illumination, the phase sums also weight different translated component arrays. Perfect nominal phase spacing does not cancel those array-valued differences.
3. **Unknown exposure scale survives phase cancellation.** If `D_p=a_p[c0+sum c_m exp(i*m*phi_p)]+b_p`, then weighted averaging contains `sum w_p*a_p exp(i*m*phi_p)` and `sum w_p*b_p`. The ordinary harmonic constraints no longer remove the side terms. Independently normalizing references changes the delivered displacement objective and needs its own contract. Equal total image sums can occur accidentally under changed structure and establish no comparability.
4. **Even perfect alignment can remove phase diversity.** On a five-sample x period with carrier index 1, actual phases `phi_p=2*pi*p/5` and specimen displacements `dx_p=-p`, perfect alignment gives effective phases `phi_p+beta(d_p)=0`. The corrected phase design has rank one. Averaging does not recover general zero order. This defeats cancellation/separation, not every more constrained calibrated inverse. Using hidden displacements to avoid the problem would violate the input boundary.
5. **Unknown origin, phase and gain have gauges.** Relative motion cannot establish an absolute specimen origin. With free order gains, `phi_p -> phi_p+alpha` and `gain_m -> gain_m*exp(-i*m*alpha)` leave the observations unchanged. Translation and the carrier-projected phase are coupled by the identity above. Fixed, independently justified calibration can remove some freedoms, but a small residual cannot certify physical recovery. See [phase identifiability](../contracts/phase-step-estimation-v1.md#identifiability-and-assessment).
6. **Periodic and optical information limits remain.** `d` and `d+(Nz,0,0)` describe the same periodic array displacement; repeated patterns admit additional ties. Constant or transfer-annihilated contrast supplies no spatial motion information. A singleton axis can have a sole numerical candidate with no physical resolving power. Nonwrapping crop/occlusion, fractional sampling and transfer nulls are separate limits; uniqueness on the finite score grid is not accuracy or confidence.
7. **Focus versus axial specimen motion can be indistinguishable.** When the declared focus offset translates detection and every axial factor together, its volume equals the opposite axial specimen shift in this model. Additional scan/instrument provenance is required to name the physical cause. If profiles do not follow together, even that equivalence fails.

A useful permitted alternative limits the intensity warning: if one complete reference is exactly a positive global gain times a translated other reference, its ideal periodic least-squares displacement minimizers stay the same. Expanding the squared mismatch leaves two shift-independent energy terms minus a positive multiple of cross-correlation. The full scores and residual do change; this does not authorize gain fitting, prove equal intensity or repair exposure-dependent phase mixing.

## Input and truth-access ledger

| Quantity | Legitimate current access | Evaluator-only or absent | Identifiability implication |
|---|---|---|---|
| Raw specimen/bead exposures, axis mapping and group identity | Caller-provided observations and explicit [raw declarations](../contracts/raw-acquisition-declarations-v1.md) | No owner dataset supplied here | Layout preservation supplies no scientific phase/motion truth |
| Nominal phases | Declared commands/metadata | Actual phases require separate evidence or contracted estimation | Commands cannot be treated as known actual phases |
| Camera offset/response and exposure scale | Explicit supplied correction coefficients with declared units/provenance | Unknown maps, bleaching, background and dose remain unknown | No automatic intensity equalization or fading law |
| Detection/effective transfers, carrier and order-gain gauge | Supplied calibrated inputs under existing contracts, with reuse conditions | Simulator's exact kernel/true carrier/gain is comparison truth unless independently available | Conditioning on truth can validate a conditional operation, not hidden-truth inference |
| Reference volume | Legitimate observed comparable reference for the existing displacement operation | True specimen/unshifted simulator volume cannot secretly replace a raw-derived reference | Reference construction needs its own access rule |
| Displacement, scan/focus offset, physical mechanism | Independently recorded motion/scan metadata if actually supplied | Synthetic displacement and mechanism label belong only to evaluation | Raw displacement score cannot authenticate its causal label |
| Boundaries, voxel spacing and timing | Explicit declarations/records | Actual O1/O3/O4 facts absent | Index voxels are not µm; periodic aliases are not unbounded motion estimates |
| Independent acceptance truth | Hidden evaluator specimen, motion, phases and optics under a later contract | Must not reach estimator, candidate selection or reference construction | A truth-hidden workflow remains an unmet Phase 7/8 dependency |

## Selected reference-source observations

Only selected settings and directly located drift/reference definitions/call sites were read. Complete file hashes identify the text, not any owner build. H=`helpers.c`: `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206`; S=`sirecon.c`: `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567`; D=`drift_n_phasestep.c`: `13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2`. Original ignored files remain at their existing main-checkout paths; no source bytes are copied into this report.

| Exact text locator | Observed possibility | What does not follow |
|---|---|---|
| H:525–563; S:651–655 | Fading rescale defaults on; drift/phase-step flags default off. Conditional rescale call handles phase data and a separate off-image branch. | Actual owner flags, rescale law or physical intensity comparability; rescale body was not inspected. |
| D:10–211, `determinedrift_bt_dirs`; S:511–563 | Middle-slab phase-averaged center-band proxy; weighted correlation and wrapped peak refinement; acquisition-mode-dependent dispatch. | General phase-independent contrast, motion during averaging, fractional physical accuracy or complete fast-mode support. |
| D:432–470, `calcRefImage`; S:672–708 | Planar type 0 uses first exposure plus its off image and fails without off images; type 1 sums such pairs; types 2/3 provide no construction. | A universal no-off fallback or permission to treat arbitrary raw phases as comparable. No product-bug verdict is made. |
| D:472–582, `determinedrift_2D`; D:260–371, `fitXYdrift` | Per-phase correlation and optional temporal x/y polynomial model. | Independent per-exposure axial motion or an observed timing law. |
| D:213–257,374–430,584–622; S:730–736,783–785 | Stored-band Fourier alignment and separate lateral carrier-projected phase addition; caller flags control application. | A correct mechanism for the owner's data or a general axial-profile correction. |

The planar addition is dimensionally `2*pi*(pixel displacement)*(µm/pixel)*(cycles/µm)` radians. This supports checking a declared sign/model; it supplies no independent numerical oracle. Source shortcuts, peak weighting and interpolation are not adopted. Actual revision/build, effective configuration, acquisition timing and off-image/intensity provenance remain absent.

## Recommendation and public dependencies

Finish this evidence objective and retain the [sanitized dependency packet](../plans/raw-phase-motion-public-dependencies.md). Before any motion implementation, resolve only: **which physical mechanism must the first supported 3D case represent?** If no actual acquisition fact settles it, the owner must choose; a synthetic development choice must be labeled as such. Do not use the architecture, ignored-source defaults or this recommendation to answer for them.

After that choice, intake must settle timing granularity, legitimate reference/phase/calibration access, intensity/boundary assumptions, gauges and ambiguity outcomes. A promising limited case is a comparable zero-order reference from complete cycles stationary within each cycle, with between-cycle rigid motion. It is a conditional candidate, not an approved motion model or per-exposure correction. A future contract must explicitly address repeated patterns, zero information, positive alternate models and any information lost in the transfer.

Existing dependencies are raw declaration → explicitly supplied camera correction → justified actual-phase/common-state premise → zero-order reference construction → supplied-reference displacement scoring. Unknown-phase fitting can help only under its own fixed-calibration, stationary-model assumptions; [its contract](../contracts/phase-step-estimation-v1.md) does not establish these premises for moving data. A new physical correction then requires the chosen motion identity. Fractional/nonperiodic estimation, continuous-carrier refinement and joint gain/phase/motion inference remain separate contracts.

Phase 7 still needs integrated nuisance estimation without manually supplied estimates. Phase 8 still needs an independently contracted realistic `(64,512,512)` z/y/x raw bead/specimen simulation with hidden truth. Phase 9 still needs owner data/settings/output provenance and parity criteria. This report establishes none of those exits.

**Confidence:** high in the conditional algebra and in the absence of settled owner motion provenance among the inspected records; medium that stationary complete-cycle references are the best first numerical candidate. An actual acquisition record, changed optical/scan model or a concrete owner motion choice could change that recommendation. No experiment, runtime performance, physical recovery or full-size feasibility was measured.
