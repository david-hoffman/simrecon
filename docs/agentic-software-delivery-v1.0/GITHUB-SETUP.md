# GitHub setup

**Version 1.0** One monorepo, ordinary Actions, native branch protection. No external control repository or custom GitHub App. These settings are instructions until applied and checked in the actual repository.

## Implementer

Identify the repository, default branch, existing CI, account capabilities, and the owner's available permissions. Preserve useful existing workflows. Propose the minimal settings diff before applying it. If access is missing, provide the exact remaining owner steps and say they are unapplied.

Create or adapt one ordinary required job, preferably `verify`. Run the project's canonical checks, including end-to-end tests and the approved project coverage checks/reports. Do not add a duplicate workflow just to obtain that name. Use the real existing job name when appropriate. All required targets must run; no path filter or conditional should silently omit them. Avoid error suppression and use native tool failures for empty discovery, missing required reports, and unmet selected measured targets. Advisory percentages must not become hidden gates; installed targets remain binding until owner-authorized policy and infrastructure migration.

By default, before opening or reopening a PR (including a draft), or pushing an update to an open PR, run full canonical verification against the exact candidate and record its commit, environment, command, and result. Confirm the tested tree matches the commit and remains unchanged through submission. Any known check failure, missing required evidence or unmet selected coverage target blocks submission. CI repeats verification on configured platforms; classify newly discovered failures under specification section 4 before repair.

Before a PR exists, ordinary branch pushes may back up failing checkpoints; record their incomplete status. No dedicated backup branch or controller is needed. Use fast generic hooks and run the full command at submission. Closing a PR or moving a branch never permits unverified submission; opening or reopening the PR still requires the full gate.

Pin third-party actions/dependencies, use only needed CI permissions, and keep production secrets out of tests. For fork contributions, do not run untrusted proposed code with privileged credentials. Save useful failure reports using ordinary Actions artifacts; no evidence service.

## Owner: configure the PR target branch

Use the repository's branch protection or branch ruleset settings for the approved PR target. The exact controls available depend on repository visibility, account plan, and permissions. GitHub's [protected-branch documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) describes availability and settings.

1. Require changes through pull requests and require the actual CI job(s). Run the workflow once if needed for its check name to be available. Require branches to be current with the base branch before merging.
2. Disallow ordinary force pushes, branch deletion, and bypass. Apply the rule to administrators where supported. Do not create fake human reviewer accounts or a mandatory approval count that a solo owner cannot satisfy; independent agent review is documented in the task/PR, not proven by GitHub identity.
3. Confirm the rule is active and inspect required checks and merge state on a real PR. Reuse existing failed-run/protection evidence when available. Do not submit a known failure solely to demonstrate blocking. Configuration inspection alone does not demonstrate an observed blocked merge; report missing behavioral evidence plainly.

GitHub accepts successful, skipped, or neutral required-check conclusions. The workflow should run required validation rather than skip the job. If several jobs are genuinely necessary, require all applicable checks rather than accepting an incomplete aggregate. See the same [GitHub documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

## What this does not enforce

Tests and workflows live beside product code. Agents are instructed not to weaken them, but no custom file restriction or check-source authority prevents that. Reviewer D inspects the diff; native CI checks the submitted configuration. A workflow deletion/change or an agent ignoring instructions can defeat the intended process. Do not claim otherwise.

The first tests may fail before implementation; they may be backed up before a PR exists. Tests of existing approved behavior may pass initially without mutation or artificial failure. Neither case changes the full submission gate. Initial test infrastructure and workflows are authorized setup work. Later workflow changes require named human-requested maintenance scope and fresh independent review. A bounded worker may own those named files; high-risk C cannot acquire that ownership by renaming an ordinary feature repair. Data-loss behavior, including settled overwrite/truncation repair, requires high risk and cannot qualify for bounded CI-authoritative work.

Record the effective branch rule, required check names, and evidence links in the setup task's concise Current state section. When a protection feature is unavailable, report the gap rather than building a substitute platform or saying merging is protected. Owner-driven manual review remains a weaker operating choice, not equivalent enforcement.

Preserve existing human-review settings unless the owner explicitly approves changing them. A solo owner may lack an eligible reviewer under existing approval rules; disclose that limitation rather than fabricate reviewer identities or treat an agent report as GitHub human approval. Merge and production release remain explicit owner actions.

## This installation

Repository: `david-hoffman/simrecon`; target: `main`. The owner explicitly authorized repository configuration in the setup conversation. [Setup accounting](../tasks/setup-plan.md) retains the historical applied request/evidence; it is not a perpetual claim about effective settings. The [delivery-efficiency Current state](../tasks/delivery-efficiency.md#current-state) links current read-only prerequisite assessment and its limits.

The ordinary matrix checks are `Verify (ubuntu-24.04)` and `Verify (macos-15)`, bound to native GitHub Actions app ID 15368. This is GitHub's existing check provider, not a custom app. The historical setup request applied the same legacy rule to administrators; the current effective ruleset observation below supersedes that no-bypass claim. No human approval count was previously configured; the new PR requirement uses zero required human approvals for solo-owner operation. Agent reports do not represent GitHub identity-based approvals. Repository ownership still permits an explicit settings change; this configuration is not an immutable policy boundary.

The coordinator's October 5, 2026 read-only inspection found active native `main` ruleset `24511329`, requiring pull requests, strict/current branches and both GitHub Actions-source matrix checks. It also found administrator repository-role `5` bypass with `bypass_mode=pull_request`; the current user's reported capability was `pull_requests_only`. Legacy branch-protection lookup returned 404, which does not establish absent effective rulesets. No complete expected-check-set aggregate is installed. No settings were changed during this inspection; recorded configuration alone is not an observed blocked merge.

Project gating remains full-local. The conditional CI-authoritative route in [specification section 6](DELIVERY-SYSTEM-SPEC.md#conditional-ci-authoritative-submission) is not eligible on this evidence: complete-set enforcement, effective bypass/base requirements and exact artifact/integration proof need their separately evaluated named scope. This rollout also changes its own verification proof, an initial eligibility exclusion. A passing matrix/PR is insufficient, and no native control proves role blindness. Do not configure an aggregate or alter bypass settings merely to enable the route without actual authority and measured justification.

The exact historically applied request is [protection-request.json](../setup/evidence/github/protection-request.json). A repeated setup must inspect current settings and reconcile changes before issuing a replacement PUT, because that endpoint replaces settings. Do not blindly replay this historical request over later working choices.

```sh
gh api repos/david-hoffman/simrecon/branches/main/protection
gh api repos/david-hoffman/simrecon/rulesets
gh api repos/david-hoffman/simrecon/actions/permissions/workflow
# Only after reconciling the inspected current settings and owner authorization:
gh api --method PUT repos/david-hoffman/simrecon/branches/main/protection \
  --input docs/setup/evidence/github/protection-request.json
```

GitHub's current personal-repository API rejected an explicit organization-only bypass list and rejected simultaneous legacy `contexts` and modern `checks` fields. The successful request uses `checks` and omits the unsupported bypass-list object. The historical read-back confirmed that request at the time; current evidence above governs today. Failed validation requests did not alter the repository. See the [official branch-protection API](https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection) for supported fields.
