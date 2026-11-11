# Inspecting a dependency signature must not replay its defaults

**Version 1.0**

- ID: 20261017T181948Z-phase-step-estimation-coordinator-scipy-observer-forwarding
- Date: 2026-10-17T18:19:48.580236+00:00
- Task: docs/tasks/phase-step-estimation.md
- Role: coordinator
- Topic: public dependency observation
- Status: confirmed
- Observation: With the locked Python3.13.12/SciPy1.18.1 environment, a genuine selected least_squares call succeeds. An observer using inspect.signature.bind, apply_defaults and replay through bound.args/bound.kwargs turns all21parameters into positional arguments. SciPy's decorated callable also supplies workers by keyword, so the replay fails with a duplicate-workers TypeError before the intended callbacks. Inspecting a valid call and replaying synthesized defaults are observably different operations in this environment. This was a test-observer defect, not scientific product-red.
- Evidence: C01/examples/observer-reproduction01.py/log and public-observer-finding01.json (SHA25694288c6153b75b09652767e77096ebae0f1d66a737916bf2c64a3ab7e5053d7a); A05/report.json; committed tests/test_volume_phase_estimation.py::test_scipy_observer_preserves_genuine_call_form_and_controls and tests/volume_phase_estimation_fixture.py::forward_observed_callbacks at6d938c0d4216fa69378f77002a69da1f0eb752dd; fresh B04/final.txt. New evidence remains postimplementation/supplemental; the B03 accepted preimplementation baseline is retained.
- Suggested action: Inspect signature bindings separately from execution. Forward the originally supplied args and kwargs, replacing only justified callback slots. Exercise each custom observer with genuine dependency execution and permitted call forms; a generic bootstrap check alone does not exercise every specialized observer.
