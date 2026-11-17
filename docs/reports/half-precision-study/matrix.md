# Complete HP114 finite disposition matrix

These are scoped report dispositions from149 collected observations, not product
activation or final SCI acceptance. Numerical reference/physical-use uncertainty
remains explicit. Completed common-value compatibility is separate from science.

| Finite row | Actual question/outcome | Precision/science disposition |
| --- | --- | --- |
| W01 | Native2D/O2 known;21 diagnostic successes; complete Q2 projection | H1/H2 finite signed deviations measured; independent full-grid/upstream science UNRESOLVED/noactivation |
| W02 | Known3D;21 successes, complete Q2 projection and six matched prepared observations | Same scientific limit; no terminal peak reduction in selected protocol |
| W03 | Search/floor/phase replacement;21 successes and complete Q2 projection | Actual discrete projection stable, continuous fit errors measured; independent search/full-grid interpretation UNRESOLVED/noactivation |
| W04 | t0 search/time0 carrier reuse/later factors;21 successes and complete Q2 projection | Actual reuse/factor deviations measured; complete science UNRESOLVED/noactivation |
| W05 | Only spatial step from W02;21 successes, complete Q2 projection and six matched prepared observations | Same scientific limit; no terminal peak reduction in selected protocol, no large-volume extrapolation |
| W06 | Nonuniform phases/signed cancellation;21 successes and complete Q2 projection | H1 relativeL2 .019978077714797954 observed; no phase-solve/noise/physical qualification inferred |
| K01 |16 real/32 paired boundary components; nearest-even/signed zero/subnormal/overflow checked | Binary16 unsuitable for finite preservation of named ±65520/70000 inputs without changed representation; no global algorithmic negative |
| K02 | Three normalized eight-value vectors;2/2/4 nonzero losses | Tiny-vector/metadata-only evidence, not full-volume or waveform physical acceptance |
| K03 | All16 dyadic product/energy/cancellation cases | Wider reductions on these half-representable operands retain formulas; explicit-half underflow/overflow/NaN effects demonstrate named limitations |
| K04 | Frozen inverse/fit/tie/regression/phase matrix witnesses | LIMITED scalar effects only; no public combined-fit branch reach/new conditioning cutoff |

| Strategy/site/backend | Demonstrated/available scope | Resource disposition | Scientific/activation disposition |
| --- | --- | --- | --- |
| H1 real half caller | All six W public full-workflow observations, with wider promotion and actual quantization errors | Standalone optimized benefit UNMEASURED under§8A; diagnostic lifecycle only | UNRESOLVED/noactivation; accepting dtype is not half computation |
| H1_PROMOTED | Same quantized values as wider caller; candidate image hashes match H1 in all18 row/repetition pairs | Standalone benefit UNMEASURED | Finite dtype control, not universal route equivalence |
| H2 corrected | Frozen corrected-camera/separation wider-compute replay plus public downstream | Standalone benefit UNMEASURED | Isolated finite mapping; no general preparation/product half mode |
| H2 prepared | Explicit paired binary16 storage/unpack, wider metadata and public downstream; all18 repetitions | W02/W05 selected protocol measured: half terminal peak/payload higher; other-row benefit UNMEASURED | Technical storage demonstrated, independent science unresolved; noactivation |
| H2 filtered | Captured wider filtering/parameters, quantized filtered coefficients and assembly replay | Standalone benefit UNMEASURED | Frozen parameter fields are not refits; no full-pipeline precision mode |
| H2 embedded | Explicit paired embedded coefficients, wider inverse/phase/signed replay | Standalone benefit UNMEASURED | Isolated finite replay; no native-half/full-pipeline claim |
| H3 NumPy/SciPy CPU | Named public FFT route promotes input/output storage; complex32 dtype technically unavailable in pinned API | CPU single tiny pass is diagnostic, not benchmark; native/workspace precision unknown | Native-half compute not demonstrated; output FFT arrays not retained, no independent accuracy bound |
| H3 cuFFT Xt | Vendor documents restricted GPU half route at exact archived/live versions | GPU runtime/host-device peak UNMEASURED; actual GPU/driver/ABI/plan UNOBSERVED | Documentary conditional feasibility only; not adopted, not a global H1/H2 negative |

All seven W modes and three fresh successful repetitions are retained. Failed/
partial/refused/unsafe historical/method attempts remain extra evidence. No
UNMEASURED cell implies no benefit or waives numerical/compatibility/native/
lifecycle obligations. No fixed numerical tolerance, latency ratio, RAM cap or
native precision/workstation/physical-recovery theorem is supplied. Recommendation:
no product precision/backend activation, with the bounded acceptance proposal
and remaining scientific premises in acceptance-proposal.md/next-slice.md.
