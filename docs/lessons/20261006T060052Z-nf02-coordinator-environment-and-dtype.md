# Actual dtype identity and stationary check context

**Version 1.0**

- ID: 20261006T060052Z-nf02-coordinator-environment-and-dtype
- Date: 2026-10-06T06:00:52.610624+00:00
- Task: NF02 v2
- Role: coordinator recording verified C evidence
- Topic: NumPy conversion and check invocation
- Status: confirmed for the recorded local environment
- Observation: C observed that NumPy2.5.3 Darwin/arm64 `np.array(longdouble_input, dtype=np.float64, copy=True)` retained the distinct longdouble dtype despite float64-width storage; NumPy linalg rejected it. Ordinary `astype(np.float64)` established the intended solver dtype and all 139 unchanged phase cases passed. A separate full-suite invocation selected venv Python without its CLI directory on PATH, causing 14 command-not-found failures; overlapping rendering invalidated one stationary-candidate assertion.
- Evidence: local ignored `artifacts/nf02-revision/role-C/C-report.md`, `C-focused-pytest-initial.log`, `C-focused-pytest.log`, `C-full-pytest.log`; final phase source SHA256 92ff9728f0362cd37cadd130da0ebd02325d10cf2ff365095a1e6e2a86f539a4. The source diff changes conversion to `astype(np.float64)` and preserves frozen test/fixture hashes.
- Suggested action: verify actual dtype identity rather than displayed name/width; use installed command context and finish candidate writes before checks comparing Git state. Keep full canonical verification separate from focused passes.
