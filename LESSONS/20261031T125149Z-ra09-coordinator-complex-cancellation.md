# Preserve cancellation controls across complex arithmetic implementations

**Version 1.0**

- ID: 20261031T125149Z-ra09-coordinator-complex-cancellation
- Date: 2026-10-31T12:51:49.877018+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator, verified restricted C observation
- Topic: numerical cancellation
- Status: confirmed observations in the recorded NumPy2.5.3/macOS-arm64 environment; underlying implementation cause not independently established
- Observation: A two-element normalized complex dot returned real residue -2.2371143170757382e-17 while separately materialized opposite products summed to exact zero. A complex self-product returned imaginary residue 2.23711432e-17 while explicit real/imaginary component products cancelled exactly. C's first two focused runs each failed one zero-correlation control; componentwise products and accurate sums passed all617 focused cases without an energy/correlation threshold. This does not establish identical behavior on every backend or justify replacing complex arithmetic generally.
- Evidence: artifacts/ra09/roles/C1/05-correlation-diagnosis.log; 11-complex-product-diagnosis.log; original01/07-focused.log; final20-focused-final.log; implementation-initial.py and implementation-correction1.py. Final module SHA256976a2fa2063ddf6fe961dec705d527d6062adba0fe8939add50007a7d4c249f1.
- Suggested action: Retain independently derived cancellation and finite-range controls when changing reduction/product primitives. Diagnose represented residuals before adding a small-signal cutoff; the RA09 contract selects no such threshold.
