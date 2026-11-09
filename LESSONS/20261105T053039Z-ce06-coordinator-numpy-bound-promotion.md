# Range comparisons must represent the bound

**Version 1.0**

- **ID** `20261105T053039Z-ce06-coordinator-numpy-bound-promotion`
- **Date** 2026-11-05T05:30:39Z
- **Task** CE06
- **Role** Coordinator
- **Topic** Numerical input validation
- **Status** Confirmed
- **Observation** Under NumPy 2.5.3, comparing a binary16 array with a Python scalar holding the binary32 maximum can overflow while casting the bound. The array can contain only 1.0. Binary16 has maximum finite magnitude 65,504, so its finite values fit the permitted binary32 magnitude.
- **Evidence** The [public binary16 cases](../tests/test_c_acquisition_boundary.py) compare accepted equal-valued representations through five public entries. The locked source-free checks used Python 3.13.12 and NumPy 2.5.3. Runtime and test commit `028ea776410aede0dd05a148b94decf378146fcb` binds the correction.
- **Suggested action** Choose a comparison representation that can hold the bound. Retain the exact supplied-value and converted-value limits, finite checks and original raw representability rules when adjusting promotion.
