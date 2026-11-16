# chore(reconstruction): Qualify a lower-memory Fourier assembly design

https://github.com/david-hoffman/simrecon/issues/120

Follow-up to #84 and merged #108. This is a separate backlog task for its own intake; filing it does not activate a new runtime or scientific contract. Preserve the completed summary/full-debug compatibility work. No fixed process-memory ceiling, latency ratio or numerical tolerance has been selected. A 16 GiB workstation remains a feasibility objective, with caller/OS headroom to be measured.

Current assembly uses a complete padded complex volume, an inverse result, phase-expression temporaries and the signed output image. Reusing a buffer can extend its lifetime and increase the peak, while spatial tiling or a different transform decomposition can alter the computation.

**One-task outcome:** qualify one concrete memory-saving assembly strategy, with evidence and a single implementation handoff, or a justified no-go. This is a finite assembly-kernel investigation, not an end-to-end disk/FFT platform project.

**Prerequisite:** #116 identifies the relevant peak. #113 provides an additional precision-specific baseline when available; it is not necessary to begin the existing double-precision assessment.

**Scope**
- Account for padding, inverse, phase/product/real temporaries and signed accumulation at actual live intervals on the pinned backend.
- Examine input-destruction/output-buffer capabilities, last-use boundaries and narrowly scoped phase-expression temporaries. Treat overwrite hints as capabilities to verify, not guarantees of zero-copy execution.
- Preserve full-grid transform meaning, positive-Nyquist embedding, native-2D plane behavior, normalization, signed output, direction/order accumulation and finite/failure ordering.
- Distinguish storage dtype, backend internal precision and workspace. A pure lifetime change must preserve the existing exact results; a changed algorithm/backend or numerical ordering requires its own explicitly approved scientific contract; the precision contract authorizes only changes named in it.
- If the measured floor requires an out-of-core transform, identify one exact algorithm and its storage/residency/I/O/cleanup requirements for a separate contract. Independent spatial tiles and memmap alone are not an equivalence or memory-bound proof.

**Done when**
- [ ] Reproducible small/medium public-compatible witnesses establish arithmetic/ownership behavior and expose backend allocations or their measurement limits.
- [ ] Matched fresh-process results report peak memory, repeat variation and latency; retaining reusable padding is not assumed to improve peak.
- [ ] The recommendation names one bounded implementation, preserved invariants, required independent oracles and any dependency/API change.
- [ ] Independent scientific review assesses the equivalence and measured claim; negative findings and unmeasured full-volume feasibility remain explicit.

**Out of scope:** implementing a new FFT backend, GPU stack, full disk lifecycle, preparation storage, precision mode or widened geometry domain in this issue.

Source: [current Fourier assembly](https://github.com/david-hoffman/simrecon/blob/836ec790aac55fb7fcdff8d51da1547091952b6e/src/simrecon/reconstruction/known_parameters.py#L835-L890).

