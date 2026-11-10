# Read-only audit evidence

This is an **incomplete discovery handoff**, not passing test or optimization
evidence. The sole [Current state](../../tasks/test-apparatus-optimization.md)
contains the authorized scope, exact baseline, blocker, accounting and next steps.
These are **nonblind coordinator inputs**; do not send them to scientific A/B.

- `declaration-index.tsv`: all 723 declarations, assigned once, with proposed
  dispositions and baseline source locations.
- `*-discovery.md`: owner-lane findings, obligations and conditional keeper plans.
- `inventory-accounting.md`: counts, support ownership and historical charges.
- `*.json.gz`: complete original ledgers/inventory, compressed without changing
  their contents. `gzip -dc FILE.json.gz` reads one. They include baseline source
  excerpts, parameter tables and history; references retain original local paths.
- `archive-manifest.json`: compressed/uncompressed sizes and SHA-256 digests.
- `ledger-reconciliation.json`: exact syntax-tree/ledger declaration comparison.
- `pr83-history.json`: closed wrong-baseline attempt, retained as history only.
- `preflight.log`: this attempt's failed pinned-reader prerequisite.
- `profile-plan.txt`, `profile-uv.py.txt`: proposed instrumentation. Recheck all
  paths/tools in the next container; the wrapper was not used for a suite run.
- `intake.txt`: the original coordinator discovery packet, before any edit.

No performance result, acceptance review, measured native coverage, same-run M25
measurement or full verification is available for this attempt. All savings are
unmeasured hypotheses or static counts of repeated operations. Retained baseline
tests are initially unexecuted here, not assumed passing. Review cost and all
missing historical measurements remain unknown.
