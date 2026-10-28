# Stored bead brightness does not establish geometric convergence

**Version 1.0**

- ID: 20261022T230603Z-full-noisy-simulation-coordinator-bead-grid-moments
- Date: 2026-10-22T23:06:03.847537+00:00
- Task: [Full noisy simulation](../docs/tasks/full-noisy-simulation.md)
- Role: coordinator
- Topic: finite source discretization
- Status: confirmed
- Observation: Six public source-generator calls used 100 nm diameter spheres with 1 electron integrated brightness on a fixed 8³ detector crop, spacing (z,y,x)=(0.125,0.080,0.080) µm. At source refinement 2, the two declared alignments occupied 5 and 8 sites. Their occupied-volume biases were −4.507% and +52.789%; their axial central-moment biases were −100% and +95.313%. Yet exact stored brightness differed from 1 electron by at most 2⁻⁵⁴ electrons. Refinement 8 used 336 sites for both alignments, with volume bias +0.268% and axis central-moment biases (+2.888%,−1.667%,−1.667%). These sampled moments do not establish continuous image accuracy or an acceptance threshold.
- Evidence: [Retained findings](../artifacts/full-noisy-simulation-20261022/source-geometry-convergence/findings.md), [exact rational metrics](../artifacts/full-noisy-simulation-20261022/source-geometry-convergence/metrics.json) and [copy/hash manifest](../artifacts/full-noisy-simulation-20261022/source-geometry-convergence/retention-manifest.json). The retained source-free command, six complete inputs/outputs, source and contract identities, environment and settings checks reproduce the observation. Own Python 3.13.12, NumPy 2.5.3, macOS ARM64; no warnings or input/state changes.
- Suggested action: Report stored mass, grid alignment, centroid and second moments separately. Use small fixed physical crops for source refinement before a full allocation. Select any image or continuum accuracy requirement explicitly; normalization alone supplies none. This observation grants no new implementation, test, policy or disposal authority.
