# Direct-model agreement and phase truth need separate columns

**Version 1.0**

- ID: 20261018T220128Z-fourier-block-phase-coordinator-oracle-versus-truth
- Date: 2026-10-18T22:01:28.456369+00:00
- Task: FOURIER-BLOCK-PHASE
- Role: coordinator
- Topic: scientific evidence presentation
- Status: confirmed
- Observation: Original C01 recorded an off-model stationary result with normalized specimen-minus-target difference 2.2204460492503131e-16 and maximum wrapped phase-minus-truth discrepancy 0.0048280360068910788 rad. Agreement with the independent direct-model target did not establish phase-truth accuracy. The target was the least-squares result at returned phases, not hidden specimen truth.
- Evidence: [C01 report](../artifacts/fourier-block-phase-20261018/C01/report.md), actual status-0 examples01 generation in arm64 macOS 27.0.1; [coordinator comparison](../docs/reports/fourier-block-phase-estimation-comparison.md). These are postimplementation observations; regeneration and independent acceptance remain separate.
- Suggested action: Name arithmetic comparisons, hidden-truth discrepancies, model controls and termination outcomes separately in scientific reports.
