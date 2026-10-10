# Setup prompt

**Version 1.0** Supply the whole package to a fresh coding-harness session at the target monorepo, then use this prompt. Nothing here claims that a `delivery` command is already installed.

```text
Set up the Agentic Software Delivery System described in DELIVERY-SYSTEM-SPEC.md.
Read that file once. It supersedes the earlier conversation drafts.

Use ONE monorepo, existing coding-harness sessions, four skills, ordinary GitHub
Actions, and Git. Do not build a custom controller, separate control repository,
GitHub App, immutable test store, permission enforcement, or agent swarm.
Restrictions on editing reviewed tests/workflows and append-only lessons are prompts.

Start read-only. Inventory existing failures, exact measured statement/branch coverage,
environment/tooling problems, and unresolved behavior before proposing remediation.
Identify the revision, environment, and commands; label stale evidence and blocked
measurement. Use existing checks in an isolated usable environment without changing
product/tooling files or running setup scripts for discovery. Preserve sound tooling.
Find usable approved architecture; otherwise route to architecture intake. An empty
repo needs a concrete minimal project record and resolved material stack choices before dependent work. Existing
code is evidence, not automatically the intended behavior. Repeated setup must not
overwrite working choices. Do not implement product features during setup.

Show the concrete setup plan and proceed within the human-requested scope; the record needs no extra document approval. Resolve only missing material decisions, unclear/outside-request objectives or human-required external authority. Separate delivery-tooling installation
from existing-product remediation, with effort, measurement gaps, and owner decisions.
A setup request does not itself request product repairs or resolve missing behavior.
Expose legacy baseline dependencies that make small slices unable to pass the full
gate, including any selected global numerical coverage target. Let the owner choose adoption scope case by case,
including an explicitly larger slice where needed; do not weaken readiness criteria.
Adapt paths and instructions without creating two live specs or overwriting the
product README. Create root LESSONS/ with a README.md format guide for one timestamped
Markdown file per lesson, following specification section 7. Install the four skills in the
selected harness's supported location, with
one canonical copy of each. Generate or reconcile AGENTS.md as the single operational
home for shared instructions; skills contain role-specific differences. Add a thin
native bridge only when required. Record actual launch/check/wait commands, model/effort choices and calibration status. Candidate cheaper/medium settings are not demonstrated defaults. Check actual interpreter/platform/lock/install/import health before expensive dependent phases; probe reviewer capability only when review is required and valid evidence is missing/stale. Stop dependent work on failed prerequisites; diagnose before authorized retry.

Infer languages/frameworks. Research suitable native formatting/lint/type/test tools.
Create or adapt ordinary CI and minimal test infrastructure as authorized setup work.
Prefer real end-to-end/public-entry-point tests, smaller tests only for useful gaps.
Before formal test design, obtain or inherit the owner's coverage policy under spec
section 5.1. Explain behavior coverage with independent risk review and optional line,
statement, branch or combined measured targets. Behavior coverage is recommended for
ordinary application work; it is not an assumed choice, and 100% is a valid explicit
target. Lines and statements are distinct metrics. Record the choice/reason/actual
authorization in PROJECT, plus each selected metric's tool/command, exact threshold,
runtime/package/platform scope, aggregation, exclusions and reporting limits. Tasks
inherit settled choices without another interview and identify relevant high-risk paths.
Unless explicitly approved otherwise, selected measurement includes instrumentable
owned runtime globally/per package on each required platform, never-imported files and
relevant subprocess/server/browser code. Inspect exact values and all required reports;
never union platforms to hide gaps. Missing/unsupported required measurement or an unmet
selected target blocks acceptance; unselected metrics are advisory. Preserve installed
gates until independently reviewed, owner-authorized policy migration and authorized
infrastructure changes reconcile them. This setup prompt silently changes no gate.

A maps approved requirements/risks to tests; B independently audits plausible high-impact
omissions and distinguishing assertions before accepting the checkpoint. Bounded review
performs the same audit; D checks actual implementation for concrete missed behavior/risk.
Record short mappings/risk dispositions through existing roles. Under spec section 5.2,
classify coverage findings before correction: approved behavior/test gaps go to the test
owner through source-free public reproductions, needless implementation to its author,
new semantics to intake and measurement/configuration defects to authorized infrastructure.
A bare uncovered branch is no new public requirement. An irreducible selected-target
conflict needs an explicit owner policy decision or remains blocked. Do not add speculative
guards, force impossible internal states or duplicate tests solely for a percentage;
preserve required validation, real invariants, ownership, blindness and all prior accounting.
Use GITHUB-SETUP.md; apply settings only with permission or give exact owner actions.

Implement delivery doctor as a thin invocation of review-work in doctor mode using
DOCTOR-PROMPT.md. No daemon or scheduled LLM loop. Default behavior writes an evidenced spec/instruction patch on a docs branch. Policy activation requires human-requested scope and fresh independent policy review; --check only reports. Keep every delivery document at version 1.0. Git versions edits.

Use spec sections 3–4 for risk routing and named ownership: mechanical one worker;
bounded worker may own authorized product/tests/infrastructure and needs one fresh
reviewer; high risk fresh blind A/B, restricted C and fresh D. Data-loss behavior, including settled overwrite/truncation repairs, is high risk and cannot use bounded ownership. Policy adoption has a
separate human-requested independently reviewed docs path. Mixed highest tier unless independent
contracts justify a split. Never grant high-risk C maintenance edits by renaming its mode.
A direct human request authorizes its intended scope for every route; record the concrete
contract and proceed without another document approval. Routine named transitions/checks,
diagnosed in-scope corrections and fresh required reviews need no repeated permission.
There is no default scenario cap; equivalent values are coverage examples. Resolve missing
or outside-request meaning through intake; shared-oracle/fixture corrections expand review and preserve valid retained
evidence. Author continuation is allowed within scope/blindness; reviewers stay fresh.
Record one Current state with complete metrics/unknowns and link detail. Preserve every
review/repair/diagnosis/failed attempt/expenditure through splits, fresh context or accepted
policy migration. There are no default review/repair/execution quotas or new-window approval
stops. Explicit human-set limits still bind; do not infer caps from defaults or historical
records. Diagnose recurring failures and each correction before proceeding within scope.
No silent model fallback or uncontrolled automatic repair loop.
Independent tasks use worktrees; dependent slices wait for integrated prerequisites.
Use bounded terminal waits/timeouts; incomplete waits are no passing review. Profile this
project before cache/shard/launcher changes; those are conditional authorized tasks.

Demonstrate valid baseline evidence and a reviewed test checkpoint, fresh C,
full local verification passing on the exact candidate, fresh D, and a normal PR.
Apply section 4's gate before opening/reopening a PR (drafts included) or pushing an
update to an open PR. Pre-PR pushes may back up failing checkpoints. Use fast generic
hooks and the full command at submission, not a custom controller or backup branch.
Known failures, including unmet selected coverage targets or missing required measurement, block submission. A conditional CI-authoritative evaluation must be part of the human request and proved native protections/trusted complete CI/head-base/artifact-version prerequisites under section 6; high risk/unknown proof/own-gate changes remain local. Do not configure or infer eligibility silently.
CI repeats verification on its configured platforms. Inspect native protections and
reuse existing failure-blocking evidence; do not submit a known failure to create it.
Add one honest lesson and demonstrate doctor editing the spec with independent policy review. Pilot mechanical docs, conventional bounded repair, authorized infrastructure and a high-risk public/synthetic case under recorded quality criteria; keep route/model/gate/hotspot changes distinguishable. Record complete cost/critical-path time, defects and unknowns; small pilots prove no general defect rate.
Label setup evidence honestly; do not fabricate independent sessions
or active protections. Preserve required source references once; do not make routine
agents reread the archive. Honor actual human-set limits and report remaining gaps. Record absent limits as not set and missing measurements as unknown. No merge/release or external messaging authority follows from setup.
```
