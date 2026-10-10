# Phase 1: acquisition, mode and settings evidence

**Version 1.0.** Observed October 10, 2026. [Task/authority](../tasks/scientific-phase1-intake.md), [baseline](scientific-phase1-baseline.md), [decision register](scientific-phase1-decisions.md).

This matrix records possibilities in source text, not the owner's instrument settings or an approved Python algorithm. Structured illumination microscopy (SIM) specimen exposures, a detection-only point spread function (PSF) stack and phase-resolved SIM bead exposures are three different inputs. An optical transfer function (OTF) prepared from a corrected detection PSF does not recover unknown empirical order responses. Owner datasets were not supplied to this task; their absence leaves provenance pending and permits planning.

## Source identities and interpretation

Read-only locators below are relative to the ignored local `SIMrecon_svn/` tree. The source is not shipped, imported or executed. Local paths and full observations remain in ignored task evidence. A hash identifies the inspected text, not the reference build that generated an owner's result. Build flags and effective commands remain unknown.

| Key | File | SHA-256 |
|---|---|---|
| M | `mainfile.c` | `b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8` |
| H | `helpers.c` | `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206` |
| S | `sirecon.c` | `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567` |
| F | `small_math_funcs.c` | `a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e` |
| R | `sirecon.h` | `f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629` |

Fresh Astra/high advice independently inspected these locators and found no new ambiguity blocking the documentation task. Scientific choices and effective owner settings remain pending. Confidence is high in the textual distinctions below; a different reference revision/build or actual command could change the applicable path.

## Target matrix

| Quantity / input | Source-supported possibility and locator | Missing target fact / decision | Earliest dependency |
|---|---|---|---|
| Specimen raw order | S:596–647: orientation/z/phase normally; z/orientation/phase under `-fastSIM`. Switch-off images can precede phase exposures. H:658–682 addresses channel/time separately. | Actual section order, extra-exposure count, channel/time counts and mappings. Do not flatten them into phase or z. | Phase 2, O1/S1 |
| Specimen volume versus plane/time series | S:185–196 derives z count using sections/channels/time/phases/directions/extra images. S:207–214 can reinterpret multiple 2D planes as time. | Declare 2D versus 3D mode, raw rank and dimension meaning; preserve headers and overrides. | Phase 2, O1/S1 |
| Detection-only PSF | [Inherited 2D operation](../contracts/otf-calibration-v1.md) starts with corrected nonnegative intensity samples and an explicit integer origin; [inherited 3D preparation](../contracts/volume-otf-preparation-v1.md) provides the corresponding volume boundary. | Identify whether the owner's PSF is detection-only. Its correction/origin are not inferred by those APIs. It cannot stand in for raw SIM bead calibration. | Phases 2–3, O2/S2 |
| Phase-resolved SIM bead order | M:140–155,187–234 reads successive phases within each z plane, optionally an extra I2M image. No comparable orientation/channel/time loop is present in this calibration path. | Separate acquisitions per orientation/channel/time or a justified reuse rule; exact pairing and order. | Phase 2, O2/S1/S2 |
| Optical/acquisition mode | H:203–213,503–517 and R:23–25,53,72–77 distinguish opposing-objective, Bessel-sheet, 2D, fast acquisition and nonlinear switch-off paths. | Select the target reference mode and excluded alternatives from actual configurations. Source branches alone request no feature. | Phase 2, O3/S2 |
| Phases, orientations and signed orders | M:23,84,155,346–358: calibration defaults to five equally spaced phases and zero plus two harmonics. H:510–514 assigns reconstruction three directions/three phases. S:278–284 can override output orders. | Actual counts, commanded angles and orientation conventions; deviation handling. General unequal-phase fitting does not extend `radialft`'s equal-phase empirical method. | Phases 2–3, O1/S3 |
| Length/frequency/intensity units | S:185–196 reads wavelength and lateral/axial spacing; M:147–151 derives calibration frequency increments. | Header/config unit conversion, excitation/emission wavelengths, voxel spacing, detector counts versus photoelectrons, exposure and camera-gain meanings. Use µm, nm, radians and cycles/µm only after declared conversion. | Phase 2, O1/O4/S1 |
| Camera/background corrections | M:192–212,219–250 has a last-pixel correction and an exclusive background/header/camera-map/supplied/border-estimation branch chain. S:316–328,624–645 and H:679–682 have specimen map/constant and extra header-background terms. | Maps, offsets, exposures, units, valid combinations, correction order and absent-input outcomes. Do not assume identical calibration/specimen preprocessing. Saturation/bad-pixel/bleaching rules require separate meaning. | Phase 2, O4/S4 |
| Bead localization/origin | M:422–457,511–517 averages phases, searches a peak and fits neighbors with wrapped boundaries; M:272–275,769–800 shifts Fourier phase. `ACCURATE_PEAK` changes the axial route at M:459–509. | Selection, multi-bead behavior, subvoxel estimator, boundaries/failures and origin gauge; owner bead isolation/build settings. | Phase 3, O2/O3/S5 |
| Finite bead compensation | M:90,280–282,705–758,1041–1054 uses a solid-sphere transform at order-shifted coordinates; source diameter default 0.12 µm, disabled by `-nocompen`. | Actual diameter/emission model, illumination angle/spacing, compensation choice and near-zero behavior. Source diameter is not a measurement. | Phase 3, O2/S6 |
| Radial averaging/symmetry | M:805–866 rounds pixel-index radii into bins, averages complex samples and enforces axial conjugate symmetry. | Radial versus Cartesian representation; appropriateness of symmetry, anisotropic/nonsquare grids and bin weighting. | Phase 3, O5/S7 |
| Cleanup, phase gauge and normalization | M:309–326,654–701,1057–1073,1114–1130: origin-line modification, optional support cleanup, usually common scaling from maximum order-zero magnitude, sine/cosine combination and optional conjugation. M:878–886 uses 0.92×NA in side-order cleanup. NA means numerical aperture. | Actual `-leavekz`, `-ifixkz`, `-ifixkr`, `-fixorigin`, `-rescale`, `-PIshift`, `-conj`, `-5bands` settings; signed-order/gauge/relative-scale/zero-signal contract. No cleanup constant is adopted. | Phase 3, O3/O5/S8 |
| Axial zero-order response | [Inherited supplied-profile operation](../contracts/volume-order-transfers-v1.md) fixes axial `g0=1`; empirical response comes from raw bead exposures. | Determine the target measured zero-order axial transfer and its representation; do not force empirical data into a supplied-profile assumption. | Phase 3, S8 |
| Independent OTF grid | M:147–151,1009–1035 derives/writes calibration dimensions/increments. H:747–786 reads independent radial/Cartesian OTF dimensions; S:1408–1414 computes axial increment ratio. | Actual dimensions, radial/Cartesian layout, spacings, order/orientation mapping and `-otfRA`; target coverage. Equal voxel spacings do not imply equal frequency bins. | Phases 3–4, O5/S9 |
| Complex interpolation | F:396–480 interpolates radial/axial or Cartesian complex values, wraps axial indices and conjugates reflected negative-kx Cartesian coordinates. | Domain/endpoints, sign/gauge, physical zero support versus missing calibration coverage, rejection/extrapolation and independent interpolation accuracy. The excerpt defines no complete safe out-of-grid policy. | Phase 4, S9 |
| Estimation, fading, drift, noise | H:525–563 initializes search/time-zero reuse, fading normalization, Wiener/noise settings, edge apodization and drift switches; S:651–655 rescales. | Actual flags/overrides/noise units and unknown quantities; objective/identifiability and fractional/3D motion/correction interaction. Supplied truth is not an estimator. | Phase 2 records O3/O4; phase 5 resolves S10/S11 |
| Output geometry/intensity | S:304–312 divides spacing by zoom; H:519–521 assigns lateral zoom 4, axial zoom 1, no z padding. S:966–976 removes padded z margins; S:2365–2367,2394–2401 forms real output. | Actual sampling, origin, padding/crop, normalization, projection/negative values and preserved provenance. Source output drops extension data; Python metadata requirements remain separate. | Phase 6, O6/S12/S13 |

## Provenance traps and sampling check

Help is not a reliable substitute for effective configuration. H:73 advertises five phases but H:511 assigns three; H:103 advertises background 515 but H:558 assigns zero. M:1204,1207 differs from assignments at M:91,106–107. Retain both observations and obtain actual command/configuration/build provenance (O3). Calibration defaults to radial output, while H:545 defaults reconstruction to nonradial interpretation. H:801–805 can duplicate order zero when per-order sections are absent. Whether the owner used either interpretation/fallback is unknown, not a rule equating all orders.

For calibration lengths `Ny,Nz` and spacings `dy,dz` in µm:

```text
Δkr = 1/(Ny*dy)          cycles/µm
Δkz = 1/(Nz*dz)          cycles/µm
kz_index,OTF = kz_index,specimen * Δkz_specimen/Δkz_OTF
```

Sanity check: doubling calibration `Nz` at the same `dz` halves its frequency increment; a specimen bin then maps to twice the OTF index. This is dimensional bookkeeping, not a chosen interpolation or accuracy contract.

No available owner provenance establishes an optical model, wavelength, bead size, phase/orientation count, noise level or zoom for the target experiment. The [phase-8 trial optics](../MIGRATION-ROADMAP.md#8-penultimate--full-end-to-end-3d-simulation) remain simulation proposals. They do not fill any pending cell here. Source method notes can proceed now; actual settings and approved numerical interpretation must precede dependent scientific tests.
