# DEV105 setup and recovery evidence

This is the sanitized evidence summary for
[the task](../tasks/setup-recovery.md), whose Current state owns execution status.
The owner approved implementation after `/intake 105`. Evidence below does not
establish scientific acceptance or authorize publication. Final candidate/gate/
review results belong outside verified tracked bytes, in the conversation and
the local `artifacts/setup-recovery/` evidence. That ignored directory is a local
working copy, not a durable external backup. This tracked summary can travel with
the Git history only when publication is authorized.

## Baseline and protected inputs

Implementation baseline: `fdcb0fa76c35a522035b532435f1bc2593eb579f`, tree
`c8f8d2fdf45007db0912d7dd3619a0010de986d4`. Product/runtime baseline remains
`4dcc50dd70da2f93b4a3360e0a4160144656b35a`; the intervening commit records intake.
No changes to scientific code, dependencies, reader preparation, Makefile,
workflows, coverage/discovery settings, or delivery policy are assigned.

| Input | Baseline SHA-256 |
|---|---|
| `uv.lock` | `222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b` |
| `.python-version` | `40411dc2c2726b4c7024d38318dd8df45c528b49491efb45939dd4a829847d94` |
| `pyproject.toml` | `96a30134cc00103853913cfccaf673373b97760549467035082e71532c245abb` |
| `devtools/pyproject.toml` | `6c0f12a59c2434909270c7edf88930e7cade0a513ef987f29cf722d24d67c93b` |
| `Makefile` | `d747ad6e5f5c0b83d13e1867864ac28c06c465fdfa22ee679ee0c302e8ca7bea` |
| `.github/workflows/verify.yml` | `e376459ac25b0b8476d2bbb6d0404e7aacce7bf7f227d5d255391fccae1e068a` |

## Recovered checkpoint and unavailable evidence

A new Git clone obtained the original #84 branch and checked out
`f8042042ff2b6865ecf501e38f11232de5d36fc9`, tree
`f230eb3cee1ccf26332050261e0ab1fe0c01a078`, with clean tracked state. Git ancestry
checks confirmed original predecessors `e2dd30b71c883010eb706001a55d709b7459b9d0`,
`2777b84eb378f8102c0a7d694227c03899b433e4` and original scientific/resource base
`9f572e92a24de738932ecdf2bafa84418df5abf7`. This restored original Git objects,
not re-authored replacements. The first clone attempt failed to connect to the
sandbox proxy; the same clone succeeded after approved escalation. Recovery
used no old `.venv`, ignored artifacts or host tool cache as cloned input.

The local `recovery-manifest.json` records exact paths, Git blobs, SHA-256 hashes,
ancestry and missing evidence. The recovered six-file inventory is:

| Document under `docs/` | SHA-256 of recovered bytes |
|---|---|
| `tasks/reconstruction-memory-intake.md` | `d37af26b506174203cee0172d7e4debef41872190daa19403922ec6bbc6c6839` |
| `contracts/reconstruction-memory-v1.md` | `73aca03885c2244222774b0237e7b7fe64574269c9d807bf1c3059f849484a9b` |
| `packets/reconstruction-memory-public.md` | `fec241a5225e312fdea02706f046747b85fe606de1f6dbe8616cdb019caf90fe` |
| `packets/reconstruction-memory-candidate.md` | `d391aeeac7439bcc9dbd20bf582bd3550f45cb60cf908ec23e9a7af5f46417d8` |
| `lessons/20261112T053549Z-reconstruction-memory-intake-workspace-bound.md` | `03011e1991d87a528c08053a78be2f694e2df424479c781b8c28ccb4c7febf0f` |
| `lessons/dispositions/20261112T053549Z-reconstruction-memory-intake-workspace-bound-deferred.md` | `98f10f248e6f5ca8e58aab2fb3e74f446ceeec84b4609d1bd0686f0c57e03c8c` |

These expected historical artifacts were unavailable in the fresh clone:
`artifacts/reconstruction-memory/execution-receipt.json`, `roles/a01-*`,
`roles/a02-*`, `baseline-types-02.log` and `resume-20261112/` under that artifact
root. No missing artifact was regenerated and attributed to an old attempt.
Historical green results below are historical-record-only, not reproduced proof.
The saved task contains no accepted scientific test checkpoint or review verdict.

The recovery exercise leaves #84's Current state untouched. Its next scientific
stage remains fresh blind A after the coordinator verifies setup/native capability
under that task's authorization, followed by fresh B, restricted C and fresh D.
No #84 scientific role or sign-in was launched for this infrastructure exercise.
An exposed coordinator handoff cannot be substituted for A/B's public packet.

## Historical accounting carried forward

Sources are the
[original saved task](https://github.com/david-hoffman/simrecon/blob/f8042042ff2b6865ecf501e38f11232de5d36fc9/docs/tasks/reconstruction-memory-intake.md)
and the separately dated
[November 12 diagnostic comment](https://github.com/david-hoffman/simrecon/issues/105#issuecomment-6828272895).
Counts are attributed to those records, not added again when a later summary
repeats them. Missing complete metering/timing remains unknown.

| Origin | Retained charges and limits |
|---|---|
| Saved #84 task | Two failed native A launches: read-only initialization, then HTTP401 after successful initialization. No authored tests or verdict. A/B/C/D reviews=0; runtime repairs=0. |
| Saved #84 task | One intake advisor with two assignments, one environment advisor with two assignments, three author correction passes, two recovery documentation workers with one hash-helper follow-up. |
| Saved #84 task | Two publication auto-review rejections; one device-sign-in attempt failed before code issuance. These historical rejections do not describe any #105 publication attempt. |
| Saved #84 task | Preflight attempt 1 failed on sandbox proxy access; attempt 2 passed. Type check initially reported 497 errors under sandbox subprocess denial; unchanged check then passed outside that sandbox. Recorded 376 workflow baseline tests passed, not full verification or scientific acceptance. |
| Saved #84 task | Two failed GitHub CLI reads, two incorrect module-path lookups and one incorrect packet lookup; subsequent retrieval succeeded. |
| Later comment | Resumed-session preflight attempt 1 failed, attempt 2 passed (reported 2.083 s). Attributed separately from the saved task's earlier pair; original logs are unavailable and no aggregate elapsed total is inferred. |
| Later comment | Another device authorization issued and awaited completion; successful sign-in was not observed. No new scientific role launched. Later executor running/offline observations and failed shell start have unknown cause. Diagnostic history was unavailable. |
| Both | 23 scientific scenario groups/four resource workloads belong to #84, not #105. Human limits not set; served-model attribution, full response/token/cost/elapsed totals unknown. Prior base/naming charges remain in their own records. |

## Current-host prerequisite evidence

Current host is Debian 13.6, Linux 6.18.57 x86_64. Existing pinned tools selected
uv 0.12.19, Python 3.13.12 and Temurin 21.0.7+6 using an existing local activation
file; this is current-host health, not the fresh-bootstrap proof. First
`make preflight` failed during hatchling resolution because sandbox proxy access
returned `Operation not permitted`. After approved escalation the same command
passed, including locked all-groups sync, reader authentication, worktree-local
Python/simrecon imports and isolated hatchling 1.32.4. Logs are
`preflight-01.log` and `preflight-02.log` in local task evidence.

Managed status was connected/current with enforced network policy. Local Docker
socket access failed under the sandbox and succeeded after approved escalation
(server 29.9.2). No credentials/sign-in were checked. Debian observations do not
establish Ubuntu/macOS acceptance; exact supported-platform setup evidence and
remaining limits are recorded separately before the candidate gate.

## Implementation and focused proof

The bounded worker added the standard-library local readiness command and 21
public-command cases, the pinned bootstrap and recovery procedures, and additive
environment/role-launch guidance. The existing 11 preflight tests are unchanged.
No new installer, launcher, uploader or gate configuration was added.

| Scenarios | Evidence and limits |
|---|---|
| S01–S02 | Official pinned command blocks and separate fresh/repeated Ubuntu exercise; macOS evidence remains missing. |
| S03–S07 | Actual readiness CLI exercised for missing tools, version/prefix/import/dependency failures, explicit path overrides, paths with spaces/Unicode, permission/nonzero/timeout failures, positive readiness, deferred limits and no setup side effects. Real current-worktree command also passed. |
| S08 | All 11 unchanged preflight tests passed, retaining failure ordering and isolation behavior. |
| S09–S11 | Evidence-based diagnosis table separates tool, connectivity, stored login, observed sign-in, native capability and offline executor. Current sandbox-denied preflight provides an actual classified example; no live authentication or outage was manufactured. |
| S12–S13 | Original checkpoint/ancestors/six-file identities recovered; missing ignored evidence declared, and original historical accounting retained above. |
| S14–S15 | Readiness reports actual material identities; recovery/launch guidance binds checkpoint, packet, ownership, supported controls and separate outputs, preserving fresh scientific roles and blindness. |
| S16 | Harmless synthetic markers in unrelated JVM properties and failing child output are omitted; selected metadata is retained. Durable-write authority and unavailable-destination handling are explicit. No secret material was inspected or published. |
| S17 | Protected-input hashes and scoped diff preserve all gates; focused proof supplies no scientific or full-verification verdict. |

Two focused pytest runs passed all 32 cases (9.65 s, then 9.05 s after final
resolved-path metadata). Ruff lint/format passed; focused Pyright passed outside
the sandbox. Three earlier type attempts could not resolve pytest despite a
successful direct import; explicit Python still failed inside the sandbox, while
the unchanged command passed outside it. This diagnoses interpreter-discovery
environment failure without dependency/config changes. Two escalated type runs
passed, the second after final metadata changes.

One initial lint run found three long diagnostic strings; splitting them fixed
formatting without changing behavior. One coordinator finding narrowed initial
overbroad Java/failure output to selected metadata/status and prompted synthetic
marker assertions before the first focused test run. The worker also recorded
two harmless incorrect-path lookups. There was no asserted product-red baseline,
test removal, scientific correction or policy change.

Detailed commands/mapping/hashes are in local `worker-report.md` and
`worker-*.log`. Worker launches=1; coordinator-assigned operational helper
launches=1; delegated scientific launches=0. Requested worker/helper model is
`gpt-6.1-sol`, high. Actual served attribution, full token/cost/elapsed totals are
unknown. Parent historical attempts above are not added as new #105 attempts.
Human limits were not set. Final gate/review attempts and verdicts use the
outside-candidate evidence pointer, preserving these charges.

## Fresh Ubuntu setup, repeat and recovered environment

The operational exercise used official Ubuntu 24.04, observed release 24.04.5
LTS x86_64/glibc 2.39, container-shared host kernel 6.18.57. Image digest:
`ubuntu@sha256:2198e4c65076e9cb0b3d695219df667c0e3b0072da64ca3c2648aca17dcecaf5`.
Git 2.43.0 and GNU Make 4.3 were installed as seed tools. Project/Git/tool setup
ran as an ordinary container user; only container seed packages used container
root. The system CA bundle was mounted read-only, with inherited proxy and TLS
verification retained. No privileged container, host networking or daemon changes.

Initial container had no uv/Python/Java, old `.venv`, readers or uv cache. Only
Git bundles and an explicit nonignored worktree snapshot were transferred.
The versioned uv and Temurin archives passed upstream SHA-256 checks:

| Artifact | SHA-256 |
|---|---|
| uv 0.12.19 Linux x86_64 archive | `23bf5552d220e0842b65c862097b2ebaeba0064b74eda5e565e77fd25969d8c8` |
| Temurin 21.0.7+6 Linux x64 archive | `974d3acef0b7193f541acb61b76e81670890551366625d4f6ca01b91ac152ce0` |

Pinned uv installed managed CPython 3.13.12. The documented bootstrap blocks
ran twice with only owned-path substitutions; both current-snapshot preflights
passed, as did the separate original #84 checkpoint preflight. Recovery used a
fresh `.venv`, reader downloads and separate initially absent dependency cache,
reusing only tools newly installed during this exercise. All three preflights
proved actual worktree import identity, authenticated readers/source launcher and
isolated hatchling 1.32.4. All three current readiness commands passed.

The initial current snapshot was baseline `fdcb0fa` plus explicitly recorded
unsaved task/implementation bytes, preserved in the local snapshot archive. It
is not relabeled as a final-candidate commit. After repeat, the final readiness
script `7aa7d0c3eafee1e145e5424fabb0dcde62ae1ca462e5642843178ef2c7ba1302`
was layered explicitly and passed local readiness. Protected setup inputs were
unchanged; that final-script check is not another full-candidate preflight or
full verification. The exact final candidate still needs its canonical gate.

Repeat comparisons preserved both manifests, Python pin, lock, Makefile, reader
script, selected uv/Java/Python executable bytes, both reader jars, Git HEAD/tree
and two harmless caller-data sentinels. Recovered #84 tracked state remained
clean. No corrupt-cache repair, native authentication or scientific role ran.

Helper accounting: one container/image pull and seed install; two tool/Python
setup sequences; five locked sync/reader preparations (two explicit plus three
inside preflight); three readiness and three preflight successes. One additional
sandbox Docker denial was followed by successful escalation. Two checkout
preparation attempts failed because task input permissions prevented the container
user reading the bundles; correcting only those task-owned permissions resolved
it. These are preparation failures, not product defects. Complete details and
safe logs/scripts/reader identities are in local `ubuntu/REPORT.txt` and adjacent
evidence. Avoid adding these contained commands again as separate parent totals.

**Remaining platform limit:** no macOS 15 executor was available. macOS fresh/repeat
setup is unproven. This Ubuntu container exercise is bootstrap/preflight evidence,
not full Ubuntu/macOS CI or scientific acceptance. Missing required platform
evidence blocks final acceptance/submission; no requirement was waived.
