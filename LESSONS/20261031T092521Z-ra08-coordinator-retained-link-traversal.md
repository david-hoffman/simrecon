# Retained-link proof must challenge traversal before dot-dot

**Version 1.0**

- ID: 20261031T092521Z-ra08-coordinator-retained-link-traversal
- Date: 2026-10-31T09:25:21.923476+00:00
- Task: [RA08 finite-field objective](../docs/tasks/reference-alignment-ra08.md)
- Role: coordinator
- Topic: cleanup oracle review
- Status: hypothesis
- Observation: Fresh blind review found that the independent preservation observer derived retained requirements from link names, the final endpoint and their ancestors. It inferred an omitted boundary: a link may traverse an existing directory before a dot-dot component, so preserving only its final endpoint may permit a plan that breaks original resolution. The reviewer used source inspection and symbolic path reasoning; no executor existed and no physical failure or product-red was observed. The scoped author correction and fresh negative/positive calibration remain pending.
- Evidence: [Fresh B3 review](../artifacts/ra08/roles/cleanup-B3/review.md), [sanitized correction](../artifacts/ra08/roles/cleanup-A2-correction-2/public/findings.md), [frozen prior observer](../artifacts/ra08/roles/cleanup-A2-correction-2/previous-current-sources/preservation_observer.py). B3 reviewed observer SHA2560450d7dc77f0d571c58bcbe9d2793da3d117375dae816944bb20090e778b55fe and checkpoint602ee5dae767268feb1e9e7f1259de20abc62c022c1911051e73417389ae7e60.
- Suggested action: Test necessary traversal components through fresh finite controls, including a legitimate positive that retains those directories while trimming disjoint children. Do not blanket reject relative links or dot-dot. Obtain fresh independent review of the shared observer and dependent evidence before any executor or actual cleanup.
