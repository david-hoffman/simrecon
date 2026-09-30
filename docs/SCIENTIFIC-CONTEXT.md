# Scientific context for the new SIM library

**Version 1.0**. Recorded September 30, 2026. This document connects scientific sources to algorithm responsibilities. It is background for task intake, not an approved numerical specification or a claim that the new library exists.

The owner permits studying `SIMrecon_svn/` to understand algorithms and requires all new library code to be written from scratch. Source code and historical output can inform investigation; neither independently establishes correct behavior. The owner approved the Python NumPy/SciPy architecture and an initial eight-hour delivery installation pass on September 30, 2026. Scientific behavior and implementation remain subject to separate approved task contracts; see [project](PROJECT.md).

## Primary references

- **SCI-2000-2D:** M. G. L. Gustafsson. *Surpassing the lateral resolution limit by a factor of two using structured illumination microscopy*. Journal of Microscopy **198**, 82–87 (2000). [PubMed](https://pubmed.ncbi.nlm.nih.gov/10810003/), [publisher article](https://onlinelibrary.wiley.com/doi/10.1046/j.1365-2818.2000.00710.x). Cite the 2000 journal issue; the publisher page separately displays a 2001 online publication date.
- **SCI-2008-3D:** M. G. L. Gustafsson, L. Shao, P. M. Carlton, C. J. R. Wang, I. N. Golubovskaya, W. Z. Cande, D. A. Agard, and J. W. Sedat. *Three-dimensional resolution doubling in wide-field fluorescence microscopy by structured illumination*. Biophysical Journal **94**, 4957–4970 (2008). [PubMed](https://pubmed.ncbi.nlm.nih.gov/18326650/), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2397368/), [published-paper reading copy](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf).

SIM means structured illumination microscopy. An optical transfer function (OTF) describes frequency-dependent imaging response; a point spread function (PSF) describes the image of a point source. The archive [inventory and conversion limits](references/scientific/README.md) distinguish citation extracts from paper text.

## Algorithms supported by the papers

These are concise reading notes. Section, equation, and figure identifiers refer to the published papers, not to legacy source line numbers.

| Algorithm responsibility | Scientific support | Relevant locator |
|---|---|---|
| Separate 2D phase components | A sinusoidal pattern produces a central component and two sidebands. Phase-varied exposures allow their separation. | SCI-2000-2D, Concept; Extended resolving ability; Fig. 1 |
| Assemble a 2D reconstruction | The reported experiment uses three phases at each of three orientations. Processing estimates pattern parameters from overlapping bands, relocates the bands, weights them by the OTF, apodizes, and transforms back. | SCI-2000-2D, Acquisition; Processing; Fig. 2 |
| Separate 3D illumination orders | Three-beam illumination has seven spatial-frequency components but five lateral orders. The reported acquisition uses five phase steps per orientation. | SCI-2008-3D, Theory, Eqs. 8–10 and Fig. 1; Data acquisition, p. 4963 |
| Calibrate and estimate parameters | Methods describe bead-derived order-specific OTFs, rotational averaging/support treatment, drift estimation, and fitting pattern parameters from overlap. | SCI-2008-3D, Transfer functions and Parameter fitting, pp. 4963–4964 |
| Combine 3D bands | Generalized Wiener recombination includes apodization. The implementation discussion filters before noninteger frequency shifts to avoid amplifying interpolation artifacts. | SCI-2008-3D, Reconstruction, Eq. 11, p. 4964 |

## Candidate mathematical oracle

The following is an independently stated discrete Fourier transform (DFT) convention for a possible first phase-separation task. It is **proposed**, not owner-approved, and does not reproduce a complete reconstruction algorithm.

At each pixel, let three real measurements correspond to phases
`phi_p = phi_0 + 2*pi*p/3`, for `p = 0, 1, 2`. Define

```text
dc = (I_0 + I_1 + I_2) / 3
c1 = sum_p(I_p * exp(-i * phi_p)) / 3
I_p = dc + 2 * Re(c1 * exp(i * phi_p))
```

Here `i*i = -1`; phases are in radians. The three equally spaced complex roots sum to zero. Applying that identity to `I_p = A + B*cos(phi_p) + C*sin(phi_p)` gives `dc = A` and `c1 = (B - i*C)/2`. For `A = 10`, `B = 4`, and `C = 2`, the expected coefficient is `2 - i`. A constant input gives zero first-order coefficient. These distinguish sign and factor-of-two mistakes without consulting implementation output.

The [FFTW definition](https://www.fftw.org/fftw3_doc/The-1d-Discrete-Fourier-Transform-_0028DFT_0029.html) supplies an additional convention reference: its forward transform uses the negative exponential sign and is unnormalized. The division by three above is an explicit proposed library choice; it must not be attributed to FFTW or inferred from a legacy scaling constant. This reference does not select FFTW as a dependency.

## Decisions required before scientific tests

Task intake must settle the relevant subset of these choices before A/B derive expectations:

- Supported operation and acquisition model: 2D or 3D, known or estimated phases, phase spacing, illumination orders, and input ordering.
- Array axes, real/complex representation, arithmetic precision, spatial and frequency units, Fourier sign, band ordering, and normalization.
- Calibration provenance, OTF representation, modulation convention, noise model, Wiener parameter, apodization, and support boundaries.
- Output sampling, cropping/padding, brightness interpretation, metadata, and behavior on malformed or nonfinite input.
- Independent synthetic/experimental reference data, conditioning assumptions, and justified absolute/relative tolerances.

This list does not approve a particular estimator, default parameter, interface, performance target, or tolerance. Papers motivate algorithms; approved contracts select the behavior to implement.

## Proposed work dependencies

An initial phase-separation public API can have a small analytic oracle. Reconstruction with known parameters then adds calibrated band positioning and combination; parameter estimation and 3D support require further contracts. File adapters can be considered independently after array and metadata conventions are approved. This is a dependency sketch, not an approved slice plan or permission to implement features during setup.

Count contract scenarios honestly. For example, three valid cases plus invalid shape, invalid phase pattern, and nonfinite input are **six** scenarios. Those three errors cannot be grouped into one row to claim the five-scenario default was met.

## Reading and verification limits

The 2000 publisher article was read through the web tool; a direct automated retrieval returned HTTP 403. For the 2008 paper, the cited theory/methods were read from the published PDF, and printed pages 4959 and 4964 were rendered for visual checking. The original PMC article URL presented a browser challenge; official front-matter metadata was successfully retrieved through PMC's documented API. No challenge was bypassed.

Full papers, figures, and abstracts are not reproduced here. Neither article had a verified full-text redistribution license in the retrieved records. The repository contains factual citation metadata, actual Docling conversions of generated citation-only HTML, and these original notes. Full-paper Docling conversion remains incomplete. These documents are not independent A/B/C/D evidence, a passing product baseline, or a completed delivery-system demonstration.
