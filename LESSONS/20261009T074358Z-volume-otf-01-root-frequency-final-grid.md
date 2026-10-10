# Classify the required final frequency grid

**Version 1.0**

- ID: 20261009T074358Z-volume-otf-01-root-frequency-final-grid
- Date: 2026-10-09T07:43:58Z
- Task: VOLUME-OTF-01, [task pointer](../docs/tasks/volume-otf-preparation.md)
- Role: coordinator
- Topic: independent numerical test oracle
- Status: confirmed
- Observation: Three frequency rejection examples used d=2^-1024 um on a (2,3,4) grid, although every required final coordinate k/(N*d) is representable. The largest magnitudes are 2^1023 and 2^1024/3 cycles/um, below binary64 maximum. The intermediate reciprocal 1/d overflows; this does not imply final-grid failure. Fresh blind B diagnosed the classification defect, and the unexposed author independently confirmed it with exact rational arithmetic before moving those examples to success assertions. All three d=2^-1074 rejection examples remain invalid by exact endpoint comparison. No product-red evidence was inferred from absent API setup.
- Evidence: [approved formula and U23/U24](../docs/contracts/volume-otf-preparation-v1.md); test-only checkpoint a61456e19f1e8c8b4428f19e6ea6d1e327a545c1, test SHA256 c775cff6edb92d12fcd8a423522917c5fd6d6dab452926976c4652cfedd145de; ignored b3-final.txt and a-b3-correction-diagnosis.log referenced by the task evidence pointer. The author used Python3.13.12 and exact Fraction arithmetic; local NumPy2.5.3. Fresh checkpoint acceptance remains independently recorded outside tracked bytes.
- Suggested action: Classify extreme numerical examples against the final contract quantity with an independently representable oracle. Test permitted positives alongside genuine final-range failures. Do not turn an avoidable intermediate overflow into an extra rejection rule.
