# B4 factual S26 wording clarification

The resource-adapter description in report.md incorrectly said that its known setup uses “nonzero dyadic caller-edited quadratures, carriers/modulation”. This conflated the owned preservation tests' deliberate caller edits with the resource adapter. It was a factual wording error in the report, not a description of the frozen adapter's actual code.

I reread the whole already permitted `tests/preparation_harmonic_memory_benchmark.py` as text only. Its SHA256 remains `ece8f0c660be2dc1713d6eae1c1e73843912ad4621fe0fb147c099c64a0eea59`. In `_case`, known-64/known-128 obtain genuine `prepare_acquisition_bands(raw, **settings)` output. The adapter retains those bands, does not edit their quadratures or noise, separately declares its transfer, carriers and modulation, and passes the bands to `reconstruct_known`. The dyadic descriptor applies to its explicit carriers/modulation and transfer formula, not the prepared quadratures. The owned sparse-harmonic and fractional-2D preservation tests separately do edit caller-owned stage quadratures/noise; those report descriptions remain correct.

Before correction I preserved the exact current reports:

- `report-before-s26-clarification.md`: SHA256 `155101b8723105b229793c54add8e3201cef3d1248c4dc7366bf1b82bf97c72e`.
- `final-before-s26-clarification.md`: SHA256 `88659a651a49887d7c567afe2e6ddd2e06ea58d90f3ada3e4dc41047e0cc9e78`.

The only report.md change replaces the mistaken clause with: “and retains those prepared quadratures unchanged; it supplies nonzero dyadic carriers/modulation and ample radial stencils.” final.md is unchanged. The acceptance, scientific oracle assessment, scenarios, budgets, resource protocol, implementation/test files and all original before/after hash logs are unchanged. The original logs remain historical evidence for the exact2043 review-time checkpoint; this clarification does not assert any later candidate identity or status.

This is a same-event report-only correction. It introduces no new verdict, material, science, review launch or charge reset. All previous events/charges remain preserved; no oracle/verdict change requiring fresh routing was found. No execution, import, calculator, AST, numerical operation, source investigation, ordinary check or resource work was performed or authorized. This clarification read only the already permitted adapter, not new source or ROOT evidence. The original static-only acceptance and unexecuted ordinary/resource/full-gate/D limits remain.
