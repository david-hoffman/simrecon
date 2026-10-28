# Finite pupil-rule accuracy does not establish continuum convergence

**Version 1.0**

- ID: 20261022T215001Z-full-noisy-simulation-coordinator-pupil-convergence
- Date: 2026-10-22T21:50:01.807363+00:00
- Task: [full noisy simulation](../docs/tasks/full-noisy-simulation.md)
- Role: coordinator
- Topic: optical model convergence and execution cost
- Status: confirmed within the sampled displacement domain
- Observation: For the declared matched-index scalar pupil at emission0.525µm, index1.515 and numerical aperture1.40, a tiny public point-source probe at radius0 and defocus6µm returned normalized density0.1798523445 with8radial nodes versus0.0006514216 with2048nodes. The finite8-node equation remains a valid mathematical target; it is a poor continuum approximation at that point. Across the sampled domain(radius0–58µm, absolute defocus0–8µm),256nodes was the first tested order with strong consecutive-rule convergence; unsampled points remain unproved.
- Evidence: Original public probe source, command, complete captured output, environment, sampling grid and limits are retained locally under artifacts/full-noisy-simulation-20261022/pupil-discovery/. SHA256SUMS.json:3652dc608c7c5fa734eac6f756c1630fd9c8291ab8dadc39a4a89fdee91cfdc5. Runtime SHA2564a0e9f5b2eb2fc7c93d11a251f61b31c2802da052b94edd1f89e5893d5c3f15f;Python3.13.12/NumPy2.5.3/SciPy1.18.1. Focal probes also used an independent analytic Airy/J1 comparison. Per-point arrays and separate streams were unavailable; original combined captures are retained.
- Suggested action: Evaluate pupil and pixel convergence separately from finite-equation arithmetic tests, then profile the selected higher-order calculation before a full physical trial. This observation selects no universal tolerance, gate, instrument assumption or new implementation authority.
