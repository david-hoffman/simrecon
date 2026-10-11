# Prepared detection PSFs do not complete empirical SIM calibration

**Version 1.0**

- ID: 20261010T211858Z-scientific-roadmap-intake-empirical-calibration-gap
- Date: 2026-10-10T21:18:58Z
- Task: [SCIENTIFIC-ROADMAP-20261010](../docs/tasks/scientific-migration-roadmap.md)
- Role: intake coordinator, with read-only advisor/source assessment
- Topic: scientific scope and prerequisite interpretation
- Status: confirmed
- Observation: The open volume-order preparation contract consumes a corrected detection PSF and caller-supplied axial profiles. It does not measure those profiles from raw phase-resolved SIM bead acquisitions. The reference calibration source assumes equally spaced phases and performs a substantive raw-bead calibration chain. Current volume recombination also requires specimen-matched OTF grids, while reference source reads independent OTF grids and interpolates them. Reviewed component delivery therefore does not establish a complete raw-input pipeline.
- Evidence: [Roadmap source/contract locators](../docs/MIGRATION-ROADMAP.md#integrated-work-open-stack-and-genuine-gaps); input hashes and exact live stack identities in local ignored `artifacts/roadmap-amendment-20261010/input-identities.json` and `github-stack.json`. Stack contract baseline `d3ba7639ebec99dd67026332771fad99cf452d51`; read-only text inspection on October 10, 2026. No reference program was built or executed.
- Suggested action: Define raw empirical calibration and independent-grid consumption as explicit scientific contracts before full end-to-end simulation. Preserve existing narrow contracts; resolve normalization, phase, support and interpolation choices from independent evidence and target settings.
