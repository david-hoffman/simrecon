# Phase separation: source notes and independent expectations

**Version 1.0.** This supports the owner-approved [first numerical contract](../../contracts/known-phase-separation-v1.md). Execution and approvals belong to the [single milestone Current state](../../tasks/numerical-foundations-plan.md#current-state).

The [Gustafsson 2000 article](https://onlinelibrary.wiley.com/doi/10.1046/j.1365-2818.2000.00710.x) motivates separating three contributions using known illumination phases. Its acquisition section uses three exposures separated by 120 degrees for each orientation. Its processing section separates components before spatial Fourier transforms and subsequent reconstruction. These locators support the operation's physical motivation. They do not specify this project's API, output ownership, precision bound or complex-sign convention.

The approved operation uses phase indices `p=0,1,2`, `phi_p=phi_0+2*pi*p/3`, and coefficients `dc=sum(I_p)/3` and `c1=sum(I_p*exp(-i*phi_p))/3`. These are project-selected conventions. Expanding `cos(phi)` and `sin(phi)` into exponentials, and summing the three complex roots of unity, gives `dc=A` and `c1=(B-i*C)/2` for `I_p=A+B*cos(phi_p)+C*sin(phi_p)`. The inverse is `I_p=dc+2*Re(c1*exp(i*phi_p))`. No legacy output supplies these expectations.

Sanity check: `A=10`, `B=4`, `C=2`, `phi_0=0` gives inputs `14`, `8+sqrt(3)`, `8-sqrt(3)`, hence `dc=10` and `c1=2-i`. Constant input has `c1=0`. The contract gives an independent closed expression and the accuracy/validation requirements; blind A/B will assess executable expectations before implementation.

The [analytic preview](../../figures/phase-separation-analytic-preview.png) shows simulated inputs and expected components only. Its diagonal stripes and asymmetric landmarks expose phase, sign and axis mistakes. NF02 adds recovered components, absolute errors and all three resynthesis residuals from the actual candidate.

## Extraction evidence and limits

[The extraction record](gustafsson-2000/full-text-extraction.json) identifies the actual local Docling run. Its input is the publisher's full HTML body serialized from the normal browser after expanding References, not the earlier generated citation projection. It includes all article sections, four captions, inline mathematical notation and 17 references. All 30 source paragraphs and four captions were retained under the disclosed punctuation/whitespace normalization; all 17 references were retained. The HTML converter reported success and zero conversion errors. Four figure-viewer/download hyperlink collisions were reported and are retained as diagnostics.

The source HTML and full Markdown/JSON outputs remain local under ignored `artifacts/numerical-foundations/reference-extraction/`. Docling retains four picture records and captions but does not embed figure pixels. A separate Figure 1 image was saved locally; Figures 2–4 were not saved or visually checked. This is a completed full-body text/caption conversion with incomplete figure extraction, not a completed extraction of the entire paper. Direct PDF downloads were blocked; no local PDF conversion is claimed. The 2008 paper remains citation-only. Full-text redistribution permission remains unverified; no paper body or source figure is committed.
