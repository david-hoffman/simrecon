# A broken fixture repository can discover an enclosing real repository

**Version 1.0**

- ID: 20261031T092521Z-ra08-coordinator-fixture-git-ceiling
- Date: 2026-10-31T09:25:21.923476+00:00
- Task: [RA08 finite-field objective](../docs/tasks/reference-alignment-ra08.md)
- Role: coordinator
- Topic: Git fixture environment
- Status: confirmed
- Observation: Two existing invalid-Git tests failed when their fixture HEAD was removed under a temporary directory nested in a real worktree. Git then discovered the enclosing real repository. A read-only comparison without and with a directory-discovery ceiling distinguished that environment effect; both unchanged focused tests passed with the ceiling. The separate full passing run used an isolated source checkout, explicit temporary directory and matching ceiling. No product or test code changed.
- Evidence: [Git discovery diagnosis](../artifacts/ra08/checks/git-discovery-diagnosis-1/), [isolated full-run environment](../artifacts/ra08/environment-full-aux-3.json), [full passing command](../artifacts/ra08/checks/full-verify-3/command.json). The original failed full run and its environment remain retained.
- Suggested action: When a public test intentionally invalidates Git metadata, qualify discovery in the actual temporary-directory layout. Confine discovery to that fixture area when required by its existing expectation, and preserve the failed environment evidence. Do not turn this observation into a hidden product fallback.
