# DOCSTRING-LINT-01: NumPy-style docstring linting

**Version 1.0.** Git versions revisions.

## Contract

The owner requested pydocstyle linting targeting NumPy standards in worktree
`540f/simrecon` on October 2, 2026. This is an authorized lint-infrastructure
setup change against baseline `be5a5379a4232f62d0411da28a51dd1d6102984d`.

Enable Ruff's `D` rules with `convention = "numpy"` through the existing hooks
and canonical `make verify` command. Scope assumption: tests and fixtures may
omit function/method docstrings (`D102` and `D103`); existing docstrings still
receive style checks. The owner was offered stricter test coverage in the
conversation. No scientific behavior, reviewed tests, runtime code, dependency
versions, coverage requirements, or workflows change.

Expected behavior follows the [Ruff convention documentation](https://docs.astral.sh/ruff/settings/#lint_pydocstyle_convention).
The standalone [pydocstyle project](https://github.com/PyCQA/pydocstyle) is deprecated
and recommends Ruff. No additional linter dependency is needed.

| Scenario | Observable result | Verification |
|---|---|---|
| L1 | A valid NumPy docstring passes; a missing section underline fails with D407. | Disposable stdin probes through the configured Ruff command. |
| L2 | A missing public source-function docstring fails with D103. | Disposable stdin probe. |
| L3 | Missing test-function/method docstrings are allowed; malformed existing test docstrings fail. | Disposable stdin probes and the unchanged repository lint target. |

## Current state

- Approval: owner's lint setup request above; test-docstring scope was delivered
  as an explicit assumption. The owner authorized commit, push, and PR creation
  on October 3, 2026 after the passing local handoff.
- Candidate and final evidence: this conversation records the final diff identity,
  verification environment, results, and confirmation that the candidate stayed unchanged.
- Reviewed checkpoint: existing tests remain unchanged; no A/B/C/D product role is claimed.
- Setup checks: configuration probes and full `make verify`; final outcomes are recorded outside this tree.
- Blockers and next action: no known blocker. Verify the final commit, publish
  the branch, and open its PR; final results and remote links stay in the
  conversation and PR.
- Metrics: scenarios=3; A/B rounds=not applicable (configuration setup);
  C repairs=not applicable; budget=no numeric allowance specified.
