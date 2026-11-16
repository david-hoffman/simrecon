# Role launches in native and managed cloud sessions

**Version 1.0** Git versions revisions.

This is coordinator guidance. Select the approved delivery route first: one
mechanical worker; bounded worker with named ownership plus a fresh reviewer;
or fresh initial A/B/C/D for high risk. Data-loss behavior, including settled
overwrite/truncation repair, stays high risk. Policy adoption needs its own fresh
independent policy reviewer. The coordinator launches each role; recipients work
directly without nested delegation. Routine transitions, needed checks and
diagnosed in-scope corrections follow the human request. No default review/repair
quota, repeated document approval, silent fallback or automatic retry loop applies.

## Adoption boundary and route requirements

The CLOUD107 fresh tool-session route is a **proposal until fresh independent
policy acceptance of the exact affected instructions is recorded in the task
evidence**. Until that verdict, high-risk native-root requirements remain in
force. After acceptance, only new sessions may use either a supported native root
or the supported fresh tool-session route below. A native process is not an
additional requirement when the selected tool route meets the packet. This
changes documentation policy, not executable, authentication or permission
mechanisms. It retroactively qualifies no earlier role and migrates no active
task wholesale. Any separately authorized named migration must preserve evidence
applicability, every prior attempt/charge and actual human-set limits.

Initial high-risk A/B/C/D and every B/D correction verdict remain fresh.
Bounded/policy reviewers remain fresh independent sessions without author history.
Never fork, resume or inherit an author/implementation conversation for review.
A/C may continue their own authorized work only under existing scope/blindness
rules. Exposure, changed scope or excessive context calls for a fresh permitted
author; clearing context restores no blindness or accounting. Tool availability
and controls must be checked in each environment. A missing required capability
blocks that route; diagnose and explicitly select another compliant supported
route within authority, or report the blocker. Do not silently fall back.

A launch record identifies the coordinator-owned packet revision/digest, role,
permitted inputs/tools and named write ownership, worktree/base/test checkpoint,
command or tool arguments, task/session ID, timestamps/status and distinct
report/final-message destinations. Record requested versus actually exposed
model/effort, context controls and metering; unavailable values are **unknown**.
Record exact completed artifact identities and the independent substantive
verdict's scope and candidate. An acknowledgement is no completion or verdict.
A documentation pilot proves launch, exact artifact completion and independent
review only for that documentation family/environment; it proves no scientific
oracle quality, calibration or blanket scientific-role qualification.

## Cheap six-level preflight

Use existing applicable evidence before probing. Advance only through applicable
levels; stop expensive dependent work when a required level fails. Native CLI or
stored native-login evidence is not required merely to use a compliant tool route.

| Level | Cheap evidence and what it proves | What it does not prove |
|---|---|---|
| 1. Available executor | Inspect current environment/tool contracts and supported fresh-session, packet, worktree, artifact and control capabilities. | A selected role actually launches or required controls exist elsewhere. |
| 2. Installed CLI/parser | For a native route, record `command -v codex`, `codex --version` and installed `codex exec --help` when missing/stale. Mark not applicable for tool-only launches. | Authentication, connectivity or a model response. |
| 3. Stored-login status | If needed for native diagnosis, use supported status without reading credentials. Mark not applicable where the tool route manages execution. | Valid request/refresh, provider access or role readiness. |
| 4. Actual authorized launch | Observe a real scoped role launch using the chosen supported route and required controls. Reuse applicable observed evidence; a probe supplies no review verdict. | Completed work, correct model attribution or accepted output. |
| 5. Completed exact artifact | Verify the required output exists, matches its revision/digest and has completion/command-status evidence. | Correctness or independent acceptance. |
| 6. Independent substantive review | A fresh reviewer receives only permitted inputs and exact artifact, then returns an evidenced acceptance or findings. | Other task families, scientific calibration or complete future reliability. |

Environment availability, setup/import success and login status are distinct from
role launch. The CLOUD107 native observations with CLI `0.167.0-alpha.4` include
one read-only filesystem initialization failure and one approved outer escalation
retaining inner read-only controls that reached native HTTP 401 token-parse/
refresh errors and MCP HTTP 451 `no_biscuit_no_service`; both exited 1 without a
model response. Keep those layers separate. These observations establish neither
causality between errors nor sign-out, and do not justify credential repair or
permission changes. A successful tool documentation pilot cannot recast them as
native success. See the task's sanitized report/evidence for exact provenance.

## Supported fresh tool-session route

Inspect the actual host tool contract before launching. The currently exposed
collaboration interface accepts `fork_turns="none"` to create a session without
conversation inheritance and permits explicit model/effort selection with that
setting. The coordinator sends only the role's permitted packet, records the
returned task/session identifier and owns all later transitions. Do not use the
default full-history fork. A reviewer must never be a continuation of its author.
For example, the supported arguments have this shape (not a new launcher):

```json
{
  "task_name": "<unique-role-name>",
  "fork_turns": "none",
  "model": "<packet-model>",
  "reasoning_effort": "<supported-packet-effort>",
  "message": "<only the role-permitted packet>"
}
```

Disable optional memory/delegation controls where exposed. The current tool
contract has no separately exposed memory-disable or per-role read-only sandbox
control; record that limit rather than inventing flags. Tool agents share the
filesystem and parent permissions. Read allowlists, reviewer report-only rules,
no nested delegation and named write scopes remain prompt restrictions, not
engineered access isolation. Fresh conversation controls do not prevent a role
from reading forbidden files: enforce the packet, disclose exposure and stop
blind work if it occurs. If a packet requires an unavailable control rather than
an optional one, this route is blocked.

## Native route

Use installed help, not remembered flags. The following example is usable only
when the actual parser confirms the flags/settings:

```sh
codex exec --ignore-user-config --disable memories --disable multi_agent \
  --sandbox read-only --model <packet-model> \
  -c 'model_reasoning_effort="high"' --json \
  -C /absolute/path/to/worktree -o /absolute/path/to/final.txt \
  - < /absolute/path/to/packet.txt
```

The `-o` destination receives the final assistant message. Keep a detailed report
at a different path so that the final message cannot overwrite it. Select
`workspace-write` only for authorized authors; reviewer work stays report-only.
High-risk C gains no bounded test/infrastructure ownership. `--approve-for-me`
already selects workspace-write; do not combine it with explicit `--sandbox`.
Set reasoning only using supported native configuration. The [official
configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents `model_reasoning_effort`; support still depends on model/client. Record
the executable/version, requested and exposed settings, packet and outputs.
Controlled parser tests establish no live role/model behavior. [Model
selection](model-selection.md) separates conservative choices from calibration.
An outer executor sandbox failure and the role's inner sandbox are different;
an approved outer retry must preserve required inner controls.

## Packets, failure and recovery

Use [PUBLIC-PACKET](../agentic-software-delivery-v1.0/templates/PUBLIC-PACKET.md)
for A/B. B additionally receives exact tests/fixtures and sanitized evidence.
Exclude implementation/history/conversations, plans, implementation-bearing
Current state, coverage maps and existing lessons. Give A/B only sanitized public
acceptance/launch fields; the coordinator retains nonblind task/report/history
links and raw evidence rather than adding them to a blind packet. Use [CANDIDATE-PACKET](../agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md)
for C/D, bounded/mechanical workers and policy reviewers. Select explicit mode and
named ownership; C gets frozen checkpoint identities. Shared oracle/fixture
changes expand fresh B review; only B decides retained evidence applicability.
Reviewers assess without repairing their review target.

Before blind imports/probes/tests, arrange source-free warnings, tracebacks and
relevant subprocess diagnostics. Retain categories/messages, locations, counts
and status; suppress source snippets/locals, not diagnostics. Pytest `--tb=no`
alone does not suppress warning source. Packets name the permitted harness/checks.
Disclose unsupported channels or exposure and stop blind work for routing. Neither
launch route waives this requirement, frozen ownership, exact-candidate full-local
verification, required platform evidence or any other delivery gate.

Use supported bounded terminal waits/notifications with timeout/failure handling
and actual human-set limits. Yield on unchanged status. Timeout, disconnection,
expired sessions and missing tools leave evidence incomplete, never accepted.
Check the recorded task/session and artifact before resuming; do not count a late
completion twice. Resume A/C only if their existing continuation rules still
hold. Reviewers need fresh verdict sessions after interruption/correction when
continuing would reuse author history or violate required freshness. An expired
or unverifiable blind session is replaced with a fresh permitted packet; this
restores no exposed role and erases no attempt. Recheck material environment,
packet/checkpoint, tool/control and artifact identities before evidence reuse.
Changed inputs or a challenging failure invalidate affected evidence.

Classify filesystem initialization, native request/authentication, MCP/provider,
missing-tool, timeout and artifact/review failures separately. Diagnose before a
scoped retry or explicit compliant route change; a failed launch counts even
without a model response. Do not create a reviewer just as a connectivity probe,
invalidate working credentials to simulate expiry, copy/extract credentials,
change sign-in, repurpose `HOME`/`CODEX_HOME`, bypass controls or install a fallback
launcher. Human/provider account actions remain documented external blockers.
If safe failure/resume/expiry cases were not exercised, label their handling
unexercised. A helper, host change or executable repair needs its own demonstrated
authorized scope; the [doctor scope](../tasks/setup-doctor.md) is no general role
coordinator. Preserve one Current state, cumulative accounting and unknown values.

## Recoverable launch instructions

Save the reusable instruction with the existing packet/handoff templates and
[recovery evidence manifest](task-recovery.md), under actual durable-write
authority. Bind an absolute current worktree, repository/base/candidate commit
and tree (or explicit unsaved-work identity), exact packet hash, accepted
test/fixture checkpoint or **none**, named role/ownership, selected model/effort
and pending gates. A branch name alone cannot bind the recovered stage.

Record command or tool arguments and the selected route's supported controls,
selected local tool/input identities, bounded wait/deadline and timeout handling,
start/status evidence, and separate absolute final-message and detailed report
destinations. For native launches record executable/version/help; mark those
fields not applicable for a tool-only launch. Follow the supported route and
adoption boundary above; retain cumulative failed launches and unknown metering
rather than resetting them on recovery.
Do not copy native conversation transcripts into shared packets. Re-establish
material environment inputs before reusing old capability/check evidence.

The coordinator still launches fresh permitted A/B/C/D sessions for high-risk
scientific work under the applicable route and adoption boundary. Restoring a
conversation or copying another `.venv` does not supply that freshness.
Blind A/B receive only their public packet/allowlist and permitted
sanitized evidence; nonblind recovery reports, raw logs, implementation history
and implementation-bearing Current state remain excluded. Fresh bounded review
is likewise independent of author history. Recovering a packet alone supplies
neither capability nor a verdict. No launch, sign-in, upload or permission change
is implicit in saving or restoring these instructions.
