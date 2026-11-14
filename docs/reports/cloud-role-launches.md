# Cloud role-launch investigation

**Version 1.0.** CLOUD107, November 14, 2026. [Task and authority](../tasks/cloud-role-launches.md).

The managed-cloud host's fresh tool sessions completed a documentation author
task and an independent review. Native CLI launching still failed: the outer
sandbox prevented app-server initialization, and an approved retry retaining a
read-only child sandbox reached authentication but received HTTP 401. MCP also
reported HTTP 451. No causal relationship between those service errors was
established, and no credential repair was attempted.

The proposed [launch guidance](../operations/role-launches.md) uses the host's
supported fresh-session API as an alternative transport. Independent policy
acceptance is required before activation. This is a session-selection amendment,
not new executable tooling or broader filesystem/network permissions. Scientific
roles retain their separate contracts, oracle review, ownership and gates.

## Observed evidence

The executor was running/connected with enforced configured network policy.
Local host: Debian 13.6, Linux 6.18.57, x86_64. The probes used baseline
`4dcc50dd70da2f93b4a3360e0a4160144656b35a`; final documentation/checks integrate
main `a66e343857ef64cf6f2207c9a2d53461b4caac1c`. No changed scientific source was
an input to the capability probes or pilot.

`/opt/codex/bin/codex --version` and `exec --help` exited 0 with version
`0.167.0-alpha.4`. Both emitted a PATH-alias read-only-filesystem warning.
`codex login status` reported `Logged in using ChatGPT`. No auth/config file,
credential value or raw transport header was inspected. These observations
establish parser and stored-status access only.

| Observation | Result | Interpretation |
| --- | --- | --- |
| [Native probe 1](cloud-role-launches/native-probe-01.json), 18:10:58 UTC | Exit 1; `failed to initialize in-process app-server client`, `Read-only file system`; no response marker | Local initialization failure in default outer sandbox. |
| [Native probe 2](cloud-role-launches/native-probe-02.json), 18:11:23–18:11:25 UTC | Exit 1 after approved outer escalation; HTTP 401, `Could not parse your authentication token`, refresh failure; no response marker | Authentication/request failure after the initialization barrier was removed. Inner sandbox remained read-only. |
| MCP during probe 2 | HTTP 451, `no_biscuit_no_service` | Separate integration/service failure. Co-occurrence does not prove it caused HTTP 401. |
| Fresh tool author `/root/pilot_author` | Completed one exact Markdown artifact | Actual task completion through the host tool API, not a native CLI result. |
| Fresh tool reviewer `/root/pilot_reviewer` | Independent ACCEPT of that exact artifact | Documentation pilot acceptance only. |

Each native invocation used `exec --ignore-user-config --disable memories
--disable multi_agent --ephemeral --sandbox read-only --model gpt-6.1-sol
-c 'model_reasoning_effort="high"' --json -C <checkout> -`. Its supplied prompt
forbade tools, reads, writes and delegation and requested one fixed marker,
explicitly identifying a capability probe rather than a review. Both ended
before a response, within a 45-second operational timeout. The second probe's
outer permission change used the normal approval tool; no sandbox-bypass flag,
auth substitution or environment-variable repurposing was used.

The receipts retain match results for named safe diagnostic strings and native
statuses, not raw stdout/stderr. Actual served model/effort, request identity,
token use and complete cost are unknown. No native author or reviewer result
exists. The runtime's internal retry behavior was not changed; the coordinator
made only the two diagnosed attempts. Existing issue #107/RM84 attempts remain
historical charges, not additional newly run probes.

## Fresh author and reviewer demonstration

The host tool contract exposes `collaboration.spawn_agent` with
`fork_turns="none"`, documented to omit surrounding conversation, plus explicit
model/effort settings and distinct session/task identities. The coordinator
supplied separate public packets, requested `gpt-6.1-sol`/`high` for each, and
instructed each role to work directly without delegation. The reviewer received
the same public requirements and artifact, not author conversation or the
investigator's recommendations. Both sessions reported no probes, delegation
or out-of-scope edits. No separately exposed optional-memory disable control
or per-agent filesystem sandbox was available; no such isolation is claimed.

The exact [pilot artifact](cloud-role-launches/pilot-levels.md) has SHA-256
`d2b544d18247fa45fcb21074a4fb9ecdaf6f594b1037caafc09893c68c6cdbd3`.
The author wrote it outside the repository, and the coordinator copied those
unchanged bytes here. The reviewer verified the digest and independently
assessed all six evidence levels, their positive/failure boundaries and limits,
returning **ACCEPT with no findings**. One author and one review round; no pilot
correction. Full prompt history is not committed; this summary and exact
artifact are the sanitized durable evidence. Host session handles are observed
identities, not remotely replayable or cryptographic certificates.

This establishes working author/reviewer transport for a small documentation
task on this host. It establishes neither scientific reasoning quality nor
enforced file blindness. The repository already treats role/file restrictions
as prompts; the proposed tool route must retain explicit public-input packets,
source-free diagnostics, no author-history inheritance, separate ownership and
fresh B/D verdicts. A task requiring an unavailable hard isolation or model/tool
capability remains blocked. No generic substitute can manufacture that evidence.

## Scenario evidence and handling

| Contract scenario | Evidence / handling and qualification limit |
| --- | --- |
| S01 executor | Current shell/status succeeded. Historical outage remains in #105; no new outage was induced. Stop dependent steps if executor is unavailable. |
| S02 CLI/parser | Current version/help exited 0. Missing executable/option handling is documented, not fault-injected. |
| S03 initialization | Probe 1 reproduced app-server errno 30; distinguished from the harmless version/help warning. |
| S04 auth levels | Stored status positive, actual native request failed. Completed interactive sign-in was not attempted or claimed. |
| S05 HTTP 401/refresh | Probe 2 reproduced failure; no unchanged-credential retry or assertion that the owner logged out. |
| S06 MCP | Probe 2 separately recorded HTTP 451; causal link unverified. Required missing tools block their task; no blanket ignore rule. |
| S07 author | Fresh tool author completed the identified permitted artifact. |
| S08 reviewer | Different fresh tool reviewer verified exact bytes and returned substantive ACCEPT. |
| S09 controls | Fresh no-history API and explicit requested model/effort available; actual serving attribution and separate memory/sandbox controls unavailable. Mandatory missing controls block affected use. |
| S10 resume | Documented revalidation of runtime/tool/packet/checkpoint identities and fresh review, preserving missing receipts and charges. Expiry/resume reliability not experimentally established. |
| S11 partial/failure | Both native attempts ended exit 1. Timeout/disconnect handling documented but not induced. No failed output becomes an accepted verdict. |
| S12 sanitation | Only fixed safe diagnostic matches/statuses retained; no secrets/source snippets/raw logs. Future blind probes still require their approved source-free harness before imports/tests. |
| S13 gates/policy | Proposed route changes only prompted launch selection; independent policy review, exact full-local check and required Ubuntu CI remain. Pilot does not replace them. |

Expiry, missing-tool and resume instructions describe safe operational handling,
not tested reliability promises. Do not log out, replace real credentials or
interrupt the shared executor to manufacture those cases. Revalidate capability
when material runtime/credential/host/packet conditions change. A native failure
may leave an independently authorized supported tool route usable; name the
selected route and its evidence before use, never silently claim native success.

## Scope and disposition

The two native failure layers are reproducible here, and the MCP failure is
separately observed. Their underlying provider/credential mechanisms remain
unresolved. No claim of native repair, general uptime or scientific qualification
is made. A supported host-tool route is demonstrated; the policy proposal makes
that explicit for future eligible launches after independent acceptance. It
does not retroactively accept older checkpoints or migrate active work silently.

PR #106 was independently re-read during execution and remains draft/unmerged
at `9ef76ae4b961e7679bc88d7bad99cee25b80cbb6`; none of its files was copied.
The integrated main separately changed required platforms to Ubuntu only.
This task reuses installed pinned setup and does not duplicate the #105/#106
bootstrap/recovery implementation.

Pinned preflight initially failed on sandbox-to-proxy access; the approved
retry passed. A further preflight checks integrated main. Full verification,
fresh policy/report verdict, exact candidate and publication results are
recorded outside tracked bytes in the task's receipt and PR technical appendix.
They must not be inferred from this report. All attempts, including failures,
remain charged. No human numeric limits were set; unavailable model/cost/token/
elapsed metrics remain unknown.
