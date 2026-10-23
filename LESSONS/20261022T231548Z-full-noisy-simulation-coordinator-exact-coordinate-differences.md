# Rational conversion cannot recover an already rounded coordinate difference

**Version 1.0**

- ID: 20261022T231548Z-full-noisy-simulation-coordinator-exact-coordinate-differences
- Date: 2026-10-22T23:15:48.513457+00:00
- Task: [Full noisy simulation](../docs/tasks/full-noisy-simulation.md)
- Role: coordinator
- Topic: exact lattice geometry
- Status: confirmed
- Observation: A valid public optical call with source refinement 79980 and 79979 pixel subdivisions returned 65321337831247.18 electrons. Fresh blind review independently enclosed the complete finite target between 65322115055640.60 and 65322119442312.04 electrons, proving an error above the unchanged 10⁻⁵ times common reference-scale allowance. The nearest exact source/pixel displacement is 1/12793440840 µm. Both direct and convolution coordinate construction rounded large labels before subtracting them, changing this displacement by about 1.16×10⁻⁶ relatively. Subsequent conversion to Fraction preserved the rounded label rather than recovering the exact difference. The implementation role reproduced that arithmetic cause separately. Existing 100% focused line/branch measurement had not established this behavior.
- Evidence: [Independent B5 certificate and verdict](../artifacts/full-noisy-simulation-20261022/role-evidence/optics/coordinate-validation/B5-final.md), [blind A complete finite reference](../artifacts/full-noisy-simulation-20261022/role-evidence/optics/coordinate-validation/A/report.md), and [retained original public probe](../artifacts/full-noisy-simulation-20261022/coordinate-discovery/README.md). The new public regression and mathematical helper are tracked in tests/test_simulation_optics_coordinates.py and tests/simulation_optics_coordinate_fixture.py. Reference bounds include all finite distant contributions and permitted accurate alternatives; ordinary SciPy discovery is not the oracle.
- Suggested action: Combine integer indices and rational refinement/subdivision offsets before converting the physical displacement to float64. Review both explicit summation and convolution geometry. Retain independent permitted-positive and exact-target checks; percentages alone do not prove numerical accuracy. This lesson creates no new scientific rule, rejection cap or edit authority.
