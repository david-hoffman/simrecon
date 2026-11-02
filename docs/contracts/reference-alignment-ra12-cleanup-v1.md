# RA12 housekeeping — superseded one-shot contract

**Version 1.1.** The owner explicitly replaced the former cleanup software
contract with the simplified policy in [PR #68](https://github.com/david-hoffman/simrecon/pull/68)
and requested its application to this continuation. The former one-shot helper,
cleanup tests, manifests and cleanup review pipeline are retired. Their historical
attempts and costs remain recorded; they are not outstanding completion gates.
Git retains the previous contract for historical interpretation.

The coordinator follows [routine housekeeping](../operations/fixture-cleanup.md):
identify exact task-created disposable paths, close owned processes, check
worktrees, remove clear targets with existing commands, and briefly report the
result in the existing Current state. Preserve durable evidence, active work,
shared environments/caches and known required inputs. Keep uncertain targets
and report why. No cleanup tools, cleanup tests or cleanup reviews are authorized.

The scientific verification and independent review requirements are unchanged.
Owner-directed disposal of old artifacts remains an explicit evidence limitation;
it cannot turn historical or missing evidence into a fresh passing result.
