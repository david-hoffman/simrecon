# Apply optical support before sampling recovery controls

**Version 1.0**

- ID: 20261107T011216Z-ce08-coordinator-presampling-physical-modes
- Date: 2026-11-07T01:12:16.557539+00:00
- Task: [CE08 independent acceptance](../tasks/c-equivalence-independent-acceptance.md)
- Role: coordinator, observing independently reviewed A3/B3 evidence
- Topic: independent physical acquisition
- Status: confirmed
- Observation: A3 synthesized continuous source modes at 0.625 cycles/um, shifted them by illumination, applied the declared optical transfer, then sampled at 1 um detector pitch. Fresh B3 independently reproduced the raw float32 observations and confirmed conventional high-mode fractions below 2.5e-16. Rasterizing the unfiltered high-frequency source on the native detector grid first would alias the intended modes and could not establish this recovery claim. The actual focused workflow passed the frozen differential-mode recovery criteria; this supplies no resolution or experimental-calibration claim.
- Evidence: [independent acquisition and projection](../../tests/ce08_recovery_model.py), [frozen acquisition and criteria](../../tests/data/ce08-matched-recovery-v1.json), [public workflow proof](../../tests/test_c_independent_matched_recovery.py); fresh B3 report and exact checkpoint identities are retained through the task evidence pointer. Source-free focused pytest passed 1 test in 0.10 s on the declared local Python 3.13.12 environment.
- Suggested action: For above-detector-Nyquist physical recovery controls, preregister continuous frequencies, illumination shifts, optical support and detector sampling in that order; independently audit the conventional loss and dose. This lesson grants no new runtime validation rule or scientific feature.
