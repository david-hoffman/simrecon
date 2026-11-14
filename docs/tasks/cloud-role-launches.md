# CLOUD107: reliable role launches in managed cloud sessions

**Version 1.0.** Intake for [issue #107](https://github.com/david-hoffman/simrecon/issues/107).
This defines an investigation and its acceptance conditions; it does not certify
a working launch route or activate a repository-wide fallback.

## Contract

The human instruction is `/intake 107` on November 14, 2026. This session owns
the concrete intake and narrow execution/review packets. No product code,
executable tests, launcher implementation or authentication repair is part of
this intake. Reuse [PROJECT](../PROJECT.md), the [intake skill](../../.agents/skills/intake/SKILL.md)
and [role-launch guidance](../operations/role-launches.md). No further approval
of this record is needed. Execution of the described investigation is the next
task phase, not an already completed outcome.

Baseline is clean commit `4dcc50dd70da2f93b4a3360e0a4160144656b35a`, tree
`7f8963b067708db5d49da8c98ea71a90bd352435`. The existing checkout is dedicated to
`chore/107-cloud-role-launch-intake`; no additional worktree is needed for intake.
Proposed eventual PR title: `chore(delivery): Qualify cloud role launches`.
Use `Refs #107` until all investigation criteria are actually met; intake alone
does not resolve the issue. No push, PR, issue comment, merge or release is
requested by this command. The follow-up below supplies execution/publication authority.

### Authorized execution and integrated baseline

The follow-up instruction is **“Ok let’s a get a pr up and finish the task”**.
It authorizes the investigation, fresh documentation pilot and review, necessary
scoped policy proposal, required checks, commit/push and PR publication. It does
not authorize merge/release or credential/permission changes. The intake-only
restrictions above describe the completed first phase, not an execution blocker.

Execution integrates current main `a66e343857ef64cf6f2207c9a2d53461b4caac1c`,
tree `57703e0b8fac884ae4366e1aefae76a9ed85a8ec`, before the final check. That
baseline includes RM84 and its independently reviewed [Ubuntu-only platform
migration](ubuntu-verification-policy.md). Ubuntu 24.04 is now the sole required
platform; historical macOS requirements/results below keep their original meaning.
No platform policy or executable code is changed by CLOUD107.

Reproduction identified a supported host tool-session route while native CLI
authentication remained unavailable. The necessary policy proposal permits fresh
managed-cloud tool sessions as an alternative launch transport, with no new
filesystem/network/credential grants. Named policy ownership is now
`AGENTS.md`, `docs/PROJECT.md` (role-entry guidance only),
`docs/operations/role-launches.md`, `.agents/skills/intake/SKILL.md`,
`.agents/skills/review-work/SKILL.md`, the delivery specification's role-session
paragraph, and its `AGENTS`, `PUBLIC-PACKET`, `CANDIDATE-PACKET` templates.
Fresh independent policy acceptance precedes activation. Only future launches
under the adopted guidance are eligible; no past verdict is requalified and
no in-flight task is silently migrated. All scientific and verification gates
remain. This changes prompted session selection, not executable security controls.

The [investigation report](../reports/cloud-role-launches.md) and its sanitized
probe/pilot artifacts are durable candidate evidence. The coordinator owns these
files plus a new scoped lesson/disposition; original RM84 records stay immutable.

### Observations, dependencies and uncertainty

1. Issue #107 reports two native attempts with Codex CLI 0.167.0-alpha.4:
   initialization failed with read-only filesystem errno 30; an approved outer
   sandbox retry initialized but failed with HTTP 401/token parsing and refresh
   messages. Neither authored code/tests. The retry retained the role's
   workspace-write sandbox. This is historical reported evidence, not a fresh
   reproduction here.
2. That attempt also reported MCP transport HTTP 451 `no_biscuit_no_service`.
   Its relationship to the HTTP 401 is unverified. A stored-login status was
   positive; it did not establish usable authentication. The messages do not
   establish that the owner logged out. Expiry, forwarding, nested CLI support
   and client/runtime integration remain hypotheses.
3. [Issue #105's diagnostic comment](https://github.com/david-hoffman/simrecon/issues/105#issuecomment-6828272895)
   records earlier missing evidence, a device-auth proxy failure, an incomplete
   later sign-in and a separate unreachable executor. Its two native A failures
   may overlap #107's report: retain source references rather than sum them as
   four attempts without distinct identities. No original private logs were
   opened for this intake. Setup success is not authentication evidence.
4. On this intake's remote reads, #105 was closed as completed, while
   [PR #106](https://github.com/david-hoffman/simrecon/pull/106) remained open,
   draft and unmerged at `9ef76ae4b961e7679bc88d7bad99cee25b80cbb6`. Its body
   records missing macOS 15 fresh/repeated setup evidence. Its bootstrap,
   recovery and readiness files are absent from this local baseline. Issue
   closure is not proof of integration or qualification. Recheck actual remote
   and baseline identities before execution; do not silently import that work
   or duplicate its bootstrap/readiness implementation. Report-only launch
   diagnosis can proceed on an identified existing environment without waiting
   for #106; any dependent documentation integration waits for its actual base.
5. Current intake observations: the selected executor became ready; shell
   commands worked. `command -v codex` returned `/opt/codex/bin/codex`;
   `codex --version` returned `codex-cli 0.167.0-alpha.4`, status 0, together
   with a read-only-filesystem warning about creating PATH aliases.
   `codex exec --help` also exited 0 with that warning. Its parser lists
   `--ignore-user-config`, `--disable`, `--sandbox`, `--ephemeral`, `--json`
   and `--output-last-message`. Help says ignoring user config still uses
   `CODEX_HOME` for auth. These observations prove installation/parser access,
   not app-server initialization, authentication or a working native role.
   No `codex exec` role, login or MCP reproduction was attempted here.
6. Issue #107 explicitly limits the #84 tool-agent exception to #84. The
   separate [readability-stack exception](readability-stack.md#authorization-and-execution-model)
   is also task-scoped. Neither authorizes a new general scientific A/B/C/D
   fallback. Existing policy already permits fresh independent policy review
   without an extra native launcher; using that provision for intake review is
   not evidence that native or scientific role launching works.

### Requirements and scenario inventory

The investigation should identify a supported route, or report a precise
remaining capability blocker. A blocked report is useful evidence but does not
satisfy #107's successful author/reviewer demonstration criterion. Separate
reported facts, observed reproductions, hypotheses and proposed policy.

| ID | Distinct required outcome | Expectation and evidence |
| --- | --- | --- |
| S01 | Unavailable executor stops dependent commands; its state is distinct from CLI/auth failures. | #105 comment, #107; status and actual command availability with timestamp. No startup-script repair claim. |
| S02 | Missing executable or unsupported option is an installation/parser result, not a failed scientific role. | Current help and role guidance; path, version, help/status and required-option mapping. |
| S03 | Filesystem initialization failure is classified separately from network/authentication. | #107; sanitized category/message/errno, stage and outer/inner sandbox identities. A version-command warning alone cannot reproduce app-server failure. |
| S04 | Stored login, completed sign-in and a real authenticated request remain different evidence levels. | #107 and #105 comment; sanitized status, then actual authorized request outcome. No credential contents. |
| S05 | HTTP 401 or refresh/expiry failure stops dependent roles and preserves the failed attempt. | #107; stage, HTTP/native status and safe message. Do not infer owner logout or repeatedly retry unchanged credentials. |
| S06 | MCP HTTP 451 is recorded independently; required unavailable tools block their dependent task. | #107; endpoint class/tool requirement and safe status. A nonessential integration failure need not invalidate an otherwise evidenced task, but no causality or blanket ignore rule is inferred. |
| S07 | A fresh author produces the exact small permitted artifact with observable completion. | Existing ownership/launch policy; narrow pilot below, packet/artifact digests, session and outcome. A spawn acknowledgement is insufficient. |
| S08 | A distinct fresh reviewer independently assesses that artifact against its contract. | Existing independence policy; no author history, separate session, exact artifact identity and substantive verdict. Review findings remain findings. |
| S09 | Missing freshness, required tool, or model/effort control is disclosed rather than silently substituted. | AGENTS and model guidance; capability record distinguishes requested/exposed/unknown. Unsupported mandatory controls block the affected role. |
| S10 | Resume or changed runtime invalidates stale capability assumptions; lost receipts stay unavailable. | #105 recovery boundary; recheck material identities, preserve checkpoint/attempts, launch fresh reviewers. Never resume author history into review. |
| S11 | Timeout, disconnect or partial output is incomplete evidence; diagnosed retries retain all charges. | Role guidance; bounded terminal waits, owned-process outcome and separate attempt IDs. No automatic retry loop. |
| S12 | Sanitized evidence retains useful categories/messages/locations/status without source snippets or secrets. | AGENTS source-free rules, #107; inspect evidence before retention; unsupported channels/exposure stop affected blind work. |
| S13 | Route qualification and any policy adoption remain separate from scientific acceptance and full verification. | #107, AGENTS, PROJECT; scope-limited recommendation, fresh policy verdict before activation, unchanged gates/platform obligations. |

Thirteen scenarios are decisions/outcomes, not test cases or a numeric cap.
Equivalent versions, error wording and repeated permitted launches are examples;
their actual count is recorded during execution. Normal/positive operation is
S07–S08; invalid inputs/capabilities are S02/S09; representation limits include
unavailable attribution/receipts in S09–S10; operation-time failures are S01 and
S03–S06/S11; compatibility and documentation are S10/S12–S13. No scientific
units, tolerance, API or numerical acceptance meaning changes.

### Investigation design and cheap capability preflight

Use existing tools manually. Record environment/OS, worktree/commit/tree/dirty
state, executable/version, supported flags, packet digest, requested and exposed
model/effort, context controls, sandbox, timestamps, native status, safe evidence
destination and task completion. Avoid dumping environment/config/auth files or
raw transport headers. Preserve only reviewed sanitized evidence; no tokens,
device codes, sensitive logs or private input paths in Git/issues.

Proceed in order: executor available; CLI/parser present; safe stored-login
status if native execution is being investigated; one scoped actual launch;
completed artifact; fresh substantive review. Stop dependent steps at failure.
`make preflight` checks the pinned product environment, not these launch levels.
CLI installation and login status never suffice as actual-role evidence. A
connectivity probe is explicitly a probe, never a reviewer or an accepted review.
Use evidence of an already completed applicable launch instead of repeating it.

For S07–S08, use a small **non-normative documentation pilot**, outside product
source/tests: a fresh author writes a short Markdown table explaining the six
preflight levels above and their evidence limits, using only the supplied public
contract. A fresh reviewer checks every row, the exact artifact digest, honest
failure claims and scope, returning ACCEPT or concrete findings. The coordinator
launches each independently; neither role delegates. No numerical task, custom
oracle, policy activation or high-risk acceptance role is used as a probe.
The pilot may demonstrate the existing native route or an already permitted
fresh independent tool-agent documentation route, explicitly recording which.
Its success supports only that task family, environment and controls; it does
not qualify scientific A/B/C/D or generalize #84's exception.

Use the actual installed help to select native flags; preserve the role sandbox
and normal approval mechanisms. An outer sandbox failure warrants diagnosis,
not automatic unsandboxed execution. Do not copy/extract credentials, repurpose
`HOME`/`CODEX_HOME`, change sign-in, grant new execution authority, or install a
fallback launcher. Any required account action belongs to the human/provider
and is a documented blocker. Investigate supported mechanisms from available
official guidance and current tool contracts; distinguish documented support
from one observed successful launch. Unsupported nested CLI use remains an
explicit limitation, not a presumed supported configuration.

For resume/expiry/missing-tool cases that cannot safely be exercised, provide
documented handling with a clear unexercised label. Do not invalidate real
credentials or disrupt the shared executor to manufacture failures. Reproducing
all historical failures may be impossible; report current success/non-reproduction
with the historical evidence intact. No broad reliability claim follows.

### Route, ownership and dependencies

This intake is documentation preparation with fresh independent intake review.
The execution design separates report-only diagnosis/pilot from a later
**policy-documentation** proposal. This is not a bounded permission change.
New executable authentication, launcher or security behavior would require a
concrete separately scoped high-risk contract and fresh native A/B/C/D under
the then-effective policy; do not bootstrap an exception by implementing it.

- Coordinator owns this task and [execution packets](../packets/cloud-role-launches.md),
  route selection, launches, sanitized evidence, accounting and cleanup.
- Investigation author owns a future `docs/reports/cloud-role-launches.md`
  report and task-owned pilot/evidence files only. No runtime, tests, fixtures,
  scripts, lock, workflows, configuration or credential edits.
- Fresh pilot reviewer reads the public pilot contract and exact artifact,
  never the author's conversation. Fresh investigation reviewer checks the
  complete report/scenario evidence and unresolved limitations, without repairs.
- A later policy author may propose changes to `AGENTS.md`,
  `docs/operations/role-launches.md`, relevant environment guidance and packet
  templates only after diagnosis names the exact affected rules/files. Resolve
  consistency with PROJECT/specification/skills before any activation. The
  current intake writes none of those files; no general fallback is selected.
  Fresh independent policy acceptance is required before adoption, with named
  migration scope and preserved prior charges. Executable security changes do
  not become policy-only work by being described in docs.

No A/B public packet is needed for this intake or documentation pilot. If a
high-risk implementation becomes necessary, prepare separate sanitized public
packets; this nonblind diagnostic task/history is not an A/B input.

Inherit [PROJECT coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance):
behavior coverage with independent risk review, no selected percentage target.
Native statement/branch reports, exact integers, package/platform scope,
never-imported/subprocess measurement and report integrity remain required when
the full gate applies. No artificial product-red or executable test suite is
needed for this intake. Required checks: source/evidence cross-check, relative
links, whitespace, owned-file diff and fresh independent intake review. Later
execution adds the scenario evidence and fresh review. Before any authorized PR
submission, run cheap pinned-environment preflight followed by clean exact-candidate
`make verify`; preserve all 13 phases and the integrated PROJECT platform requirements
(Ubuntu 24.04; historical macOS clauses are superseded by its recorded migration). No CI-authoritative exception is selected.

Select `gpt-6.1-sol`/high provisionally for uncertain infrastructure and policy
judgment under [model guidance](../operations/model-selection.md). The mechanical
pilot may use that conservative configuration; no broader calibration claim
follows. Requested settings and actual attribution are distinct. Escalate only
diagnosed capability/reasoning limitations; missing material authority or
semantics return to intake. Human numeric limits: **not set**. Missing per-role
tokens, cost, elapsed and owner-wait measurements: **unknown**, never zero.

Intake completion means a reviewable contract, scenario inventory and narrow
packets with independent intake acceptance. Investigation completion additionally
requires classified evidence, the author/reviewer pilot and reviewed failure/
recovery guidance. A necessary policy proposal needs its own accepted exact
scope before activation. Publication, issue closure and product acceptance are
distinct; none follows from this intake.

## Current state

- **Scope/status:** investigation and policy candidate prepared for independent
  review and full verification. Exact final review/check/publication outcomes
  are retained outside tracked bytes in the receipt below. Native CLI auth is
  unrepaired; the fresh host-tool documentation route is demonstrated.
- **Authorization/base:** `/intake 107` plus “Ok let’s a get a pr up and finish
  the task”; execution base `a66e343857ef64cf6f2207c9a2d53461b4caac1c`.
  Documentation/policy route, default full-local submission gate, required
  Ubuntu CI. No accepted scientific test checkpoint is claimed.
- **Evidence:** [report](../reports/cloud-role-launches.md), tracked sanitized
  probes and pilot; `/workspace/cloud107-evidence/intake-record.json` preserves
  the intake review; `/workspace/cloud107-evidence/execution-record.json`
  holds final candidate hashes, review/check/PR outcomes and cumulative detail.
  Local full-check receipt/logs live under `artifacts/verification/`.
- **Accounting:** intake: one adviser and one independent ACCEPT, zero native
  probes. Execution: one environment adviser, two failed native capability
  probes, one fresh tool pilot author and one fresh pilot reviewer (ACCEPT),
  one policy author; final policy/investigation review recorded in the receipt.
  Historical RM84/#107 native attempts remain two, with #105 overlap not summed.
  Preflight attempt 1 failed at sandbox proxy access; approved attempt 2 passed;
  attempt 3 rechecks integrated main. A concurrent PROJECT edit blocked the
  initial fast-forward; its exact patch was preserved, main fast-forwarded and
  the patch reapplied without loss. Lookup/proxy failures and all later review/
  correction/gate attempts remain charged in the receipt. Actual serving
  attribution, complete per-role tokens/cost/time and owner wait are unknown.
  Requested policy/pilot model is Sol/high. Human numeric limits: not set.
- **Remaining limits/action:** final review/gate/PR outcomes are in the receipt;
  perform diagnosed corrections through existing ownership. Native authentication
  needs provider/account investigation if native execution is required; tool
  session success does not prove native repair or scientific correctness.
  New policy use waits for independent acceptance. No merge/release authority.
- **Housekeeping:** keep current checkout, tracked evidence, shared environment
  and `/workspace/cloud107-evidence`. No extra worktree/disposable fixture or
  long-lived task process was created; native probes exited. Removed paths:
  none; cleanup errors: none. Report any later exception in the receipt.

## PR presentation

For the authorized PR, lead with the observed launch barrier and the demonstrated
route and limits. A figure is unnecessary for this short ordered preflight.
Place exact environment/packet/candidate identities, pilot verdicts, failure
classifications, checks/platform gaps and cumulative accounting in the technical
appendix. Do not claim broad authentication reliability or issue resolution from
a single pilot. Keep this presentation context out of future blind A/B packets.
