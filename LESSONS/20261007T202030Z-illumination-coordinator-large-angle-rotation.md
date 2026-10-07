# Rotate represented phases without adding a lost offset

**Version 1.0**

- ID: 20261007T202030Z-illumination-coordinator-large-angle-rotation
- Date: 2026-10-07T20:20:30.557352+00:00
- Task: [ILLUMINATION-01](../docs/tasks/illumination-estimation.md)
- Role: coordinator
- Topic: floating-point phase representation
- Status: confirmed
- Observation: With float64 psi=1e20 rad and theta=0.5 rad, psi+theta equals psi. Rotating the represented sine/cosine pair retains the offset, producing principal phase -0.20135215771534534 rad rather than -0.70135215771534543 rad. This is representation evidence, not product verification.
- Evidence: [Public corrected-phase contract](../docs/contracts/illumination-estimation-v1.md#corrected-phases-and-result); local numerical probe with NumPy 2.5.3/Python 3.13.12. Astra/ultra report-only scientific advice identified this boundary before blind tests.
- Suggested action: For accepted arbitrarily large supplied angles, rotate represented trigonometric entries when forming estimated corrected phases; compare phase differences circularly.
