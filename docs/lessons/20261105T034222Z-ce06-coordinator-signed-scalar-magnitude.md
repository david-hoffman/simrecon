# Widen signed NumPy values before taking their magnitude

**Version 1.0**

- **ID** `20261105T034222Z-ce06-coordinator-signed-scalar-magnitude`
- **Date** 2026-11-05T03:42:22Z
- **Task** CE06
- **Role** Coordinator
- **Topic** Numerical input validation
- **Status** Confirmed
- **Observation** Taking the absolute value of a NumPy signed minimum can overflow in its original type. For an eight-bit signed integer, the mathematical magnitude of −128 is 128 and the largest positive value is 127. The bead preparation check rejected this valid angle before the optical calculation.
- **Evidence** The [public regression cases](../../tests/test_c_acquisition_boundary.py) compare three NumPy signed minima with equal Python integers through `prepare_bead_otf`. The source-free scoped checks used Python 3.13.12 and NumPy 2.5.3. Runtime and test commit `eb407695f0c3679638309378b67d05b041f9c1b0` binds the correction.
- **Suggested action** Widen a fixed-width signed scalar to an exact integer before computing its magnitude. Where the contract bounds the supplied value and its converted representation, check both before the calculation.
