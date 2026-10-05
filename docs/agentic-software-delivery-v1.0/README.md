# Agentic Software Delivery System

**Version 1.0** This specifies a delivery process; it does not install tooling, configure GitHub or certify readiness.

> One monorepo, four skills, ordinary continuous integration (CI), and a learning log. Select sessions by risk; preserve independent judgment and full checks.

First inventory existing failures, exact coverage, environment problems and unresolved behavior. Separate tooling setup from product remediation/cost. Reuse approved architecture or resolve affected decisions. Installation alone makes no failing or under-covered product ready.

Intake records observable contracts, edit ownership, route, checks/model/effort, gate mode and budget. Large requests may approve a slice plan and all contracts together. Five distinct decisions/outcomes per slice is the default; equivalent values are coverage examples. A complete explicit mechanical/bounded request may authorize execution without a second yes. High risk and policy need approval of an identified proposal; changed scope/permissions/budget still needs approval.

| Route | Work | Acceptance |
|---|---|---|
| Mechanical | Non-normative/deterministic edits, one worker | Diff/relevant checks and owner acceptance; independent review if contract requires |
| Bounded | Settled conventional behavior or explicit dependency/platform/check maintenance, with no data-loss behavior; worker with named test/infrastructure ownership | One fresh independent reviewer challenges oracle, product/check behavior, preserved gates and exact passing candidate |
| High risk | Science/numerics, binary/custom oracle, data-loss behavior, permission/security, substantial interface or uncertain impact | Fresh blind A tests, fresh blind B review, restricted C implementation, fresh D final review |
| Policy documentation | Explicit approved amendment/adoption scope | Fresh independent policy review before activation |

A three-line endian or settled overwrite/truncation repair is high risk; data-loss behavior never qualifies as bounded merely because it is conventional. Mixed work takes highest tier unless independent contracts justify a split. Bounded construction loses blindness; settled expectations and independent oracle review make that tradeoff explicit. It never grants restricted C test/workflow edits. Policy adoption cannot approve itself as mechanical.

Default delivery:

```text
Authorized contract/route
  → named worker or high-risk A/B checkpoint then C
  → canonical full local verification on exact unchanged candidate
  → open/update PR; full required platform CI
  → fresh required final reviewer acceptance
  → owner merge action; release remains separate
```

Mechanical tasks use their required acceptance; policy docs use independent policy review. Full local verification gates PR opening/reopening (drafts too) and updates. Known failures/coverage gaps block. Pre-PR backups may be incomplete when labeled; moving/closing a PR bypasses nothing. A conditional CI-authoritative trial is only eligible after separate approval and verified native protections/trusted complete check/head-base/artifact-version proof under [specification section 6](DELIVERY-SYSTEM-SPEC.md#6-ordinary-github-ci). High risk, uncertain proof and own-gate edits keep local gating. No green PR alone proves enforcement.

Use meaningful real-entry tests; expectations derive from approved behavior/applicable sources/invariants. Existing behavior may pass initially; no manufactured red or mandatory mutation platform. Require 100% native measured owned-runtime statements/branches globally/per package, including never-imported code/subprocesses. Report unsupported metrics/exclusions/missing evidence.

Classify environment/tooling, test defect, product defect and unresolved meaning before repair. Risk and failure category differ. High-risk corrections use sanitized public findings, A's changed tests/test-requirement dependents and fresh B; shared fixtures/oracles expand scope, retained evidence needs reviewer confirmation. A/C may continue their own authorized work while scope/blindness hold; reviewers stay fresh. Exposure requires replacement, not context clearing.

Use one Current state and concise packets/handoffs. Record complete metrics or unknowns; no double-counted cumulative tokens or overlapping elapsed times. Default two B reviews/window and one C/bounded corrective cycle; diagnosis after two nonacceptances. Fresh sessions/splits/migration/model swaps reset no charges. Cheap prerequisites and supported bounded waits reduce wasted work; timeout is incomplete. Calibrate capability/effort by hardest judgment before adopting cheaper candidates. Profile local hotspots before optional cache/shard/helper work.

You supply intent, consequential answers, scope/budget approvals and final merge/release action. Prompted role/file restrictions are not technical barriers or a bug-free guarantee. CI executes repository-controlled checks.

Root LESSONS holds one new timestamped evidence-linked file per useful lesson; corrections add superseding entries, no shared index. Doctor proposes an evidenced patch to existing rules, within approved docs scope, with independent policy review before activation. In-flight migration requires explicit authority and preserves historical spending.

| Entry | Purpose |
|---|---|
| [Specification](DELIVERY-SYSTEM-SPEC.md) | Canonical policy/rationale |
| [Setup](SETUP-PROMPT.md) | Install using approved architecture/tooling scope |
| [Intake](INTAKE-PROMPT.md) | Define risk/contract/ownership/authorization |
| [Doctor](DOCTOR-PROMPT.md) | Improve evidenced instruction gaps |
| [GitHub setup](GITHUB-SETUP.md) | Native CI/protection configuration and limits |
| [Examples](WORKFLOW-EXAMPLES.md) | Risk, corrections, evidence and model choices |
| [Templates](templates/TASK.md) | Task plus public/candidate/handoff/project starters |

Four `.agents/skills/` procedures implement role modes; repository AGENTS is the single shared operational home. Preserve product README and source/test structure. [References](REFERENCES.md) are background, not fresh authority. No controller, external repository, tracing service or daemon.
