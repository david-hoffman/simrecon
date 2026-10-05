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
repo needs an owner-approved minimal project record before choosing a stack. Existing
code is evidence, not automatically the intended behavior. Repeated setup must not
overwrite working choices. Do not implement product features during setup.

Show the small setup plan and obtain approval of the identified scope; an existing explicit approval of that proposal needs no duplicate yes. Separate delivery-tooling installation
from existing-product remediation, with effort, measurement gaps, and owner decisions.
Installation approval does not authorize product repairs or resolve missing behavior.
Expose legacy baseline dependencies that make small slices unable to pass the full
gate, including global 100% coverage. Let the owner choose adoption scope case by case,
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
Retain 100% measured statement/branch coverage and report unsupported measurement.
Use GITHUB-SETUP.md; apply settings only with permission or give exact owner actions.

Implement delivery doctor as a thin invocation of review-work in doctor mode using
DOCTOR-PROMPT.md. No daemon or scheduled LLM loop. Default behavior writes an evidenced spec/instruction patch on a docs branch. Policy activation requires approval of the identified scope (reuse existing authorization) and fresh independent policy review; --check only reports. Keep every delivery document at version 1.0. Git versions edits.

Use spec sections 3–4 for risk routing and named ownership: mechanical one worker;
bounded worker may own authorized product/tests/infrastructure and needs one fresh
reviewer; high risk fresh blind A/B, restricted C and fresh D. Data-loss behavior, including settled overwrite/truncation repairs, is high risk and cannot use bounded ownership. Policy adoption has a
separate approved independently reviewed docs path. Mixed highest tier unless independent
contracts justify a split. Never grant high-risk C maintenance edits by renaming its mode.
A complete explicit lower-route instruction may authorize scope; high risk/policy retain
approval of identified proposals. Routine authorized transitions need no repeat permission.
Default five behavioral scenarios; equivalent values are coverage examples. New meaning
needs approval; shared-oracle/fixture corrections expand review and preserve valid retained
evidence. Author continuation is allowed within scope/blindness; reviewers stay fresh.
Record one Current state with complete metrics/unknowns and link detail. Preserve every
attempt/window/repair/budget through splits, fresh context or migration. Default two B
reviews/window and one C/bounded corrective cycle; no automatic fallback/retry.
Independent tasks use worktrees; dependent slices wait for integrated prerequisites.
Use bounded terminal waits/timeouts; incomplete waits are no passing review. Profile this
project before cache/shard/launcher changes; those are conditional authorized tasks.

Demonstrate valid baseline evidence and a reviewed test checkpoint, fresh C,
full local verification passing on the exact candidate, fresh D, and a normal PR.
Apply section 4's gate before opening/reopening a PR (drafts included) or pushing an
update to an open PR. Pre-PR pushes may back up failing checkpoints. Use fast generic
hooks and the full command at submission, not a custom controller or backup branch.
Known failures, including incomplete coverage, block submission. A conditional CI-authoritative trial requires separate scope/budget and proved native protections/trusted complete CI/head-base/artifact-version prerequisites under section 6; high risk/unknown proof/own-gate changes remain local. Do not configure or infer eligibility silently.
CI repeats verification on its configured platforms. Inspect native protections and
reuse existing failure-blocking evidence; do not submit a known failure to create it.
Add one honest lesson and demonstrate doctor editing the spec with independent policy review. Pilot mechanical docs, conventional bounded repair, authorized infrastructure and a high-risk public/synthetic case under recorded quality criteria; keep route/model/gate/hotspot changes distinguishable. Record complete cost/critical-path time, defects and unknowns; small pilots prove no general defect rate.
Label setup evidence honestly; do not fabricate independent sessions
or active protections. Preserve required source references once; do not make routine
agents reread the archive. Stop at the approved budget and report remaining gaps.
```
