# DEV105: reproducible development setup and task recovery

**Version 1.0.** Git versions revisions. Intake contract for
[issue #105](https://github.com/david-hoffman/simrecon/issues/105), requested by
`/intake 105` on November 12, 2026. This defines future infrastructure work;
it is not an implemented bootstrap or an acceptance result.

## Purpose and boundaries

Make setup reproducible from repository instructions and recover a task from a
saved checkpoint without assuming a particular workstation, tool cache or ignored
artifact survives. Reuse [environment setup](../operations/environment.md),
[reader preparation](../operations/imagej-reader-environment.md),
[role launches](../operations/role-launches.md) and the existing
[handoff template](../agentic-software-delivery-v1.0/templates/HANDOFF.md).

This is **bounded development-infrastructure maintenance** with a fresh independent
reviewer. It does not change scientific interfaces, dependency pins, supported
verification platforms, permissions, delivery policy or evidence-acceptance rules.
No automatic privilege escalation, sign-in, role launcher, secret manager,
general redaction service, cache repair/deletion tool or platform-recovery service
is commissioned. New permissions/security or data-loss semantics require intake
and the applicable higher-risk route; a delivery-policy proposal requires fresh
independent policy review before activation.

## Requirements

### R1 — reproducible bootstrap using existing mechanisms

Provide repository-owned instructions for Ubuntu 24.04 and macOS 15, the current
verification matrix. Name ordinary prerequisites (working executor, shell, Git,
Make, install/download capability and required network access), supported host
architecture for each selected tool artifact and installation destinations.
Unsupported combinations get an explicit limitation, not an inferred pass.

Select uv **0.12.19**, CPython **3.13.12**, and Temurin **21.0.7+6**, matching
the current CI setup. Use pinned official installation/download sources and
their applicable integrity checks, with explicit commands for each supported
platform. A pre-existing compatible installation can be selected by path.
Do not depend on `/workspace/.simrecon-tools/activate.sh`, a developer's home
directory, shell profile or shared `.venv` existing. Such paths may be examples
or reusable inputs, not prerequisites. Do not overwrite a global tool selection.

Use existing uv Python installation, `make sync` / `make preflight` and locked
all-groups synchronization rather than a second resolver or reader downloader.
Each checkout has its own `.venv`. Preserve both manifests, `.python-version`,
`uv.lock`, upstream reader URLs/hashes and all check settings. Document explicit
`UV` and `SIMRECON_JAVA` selection and carry it into later commands. Repeating
setup with the same inputs must safely converge on those identities without
upgrading dependencies, deleting user data, replacing corrupt reader inputs or
resetting task history. Follow the existing reader failure semantics.

The minimum deliverable is an executable sequence of documented commands plus
the readiness check below; a new installer or reusable bootstrap shell script
is unnecessary. Installation is an explicit operator action, never a readiness
check side effect. Explain the initial installation path when Python/uv/Java is
absent, before commands that require it.

### R2 — local readiness distinct from setup

Provide `scripts/check_dev_environment.py`, a development-only local check,
invoked with a documented available Python interpreter. It accepts explicit
uv/Java executable selections, otherwise using `UV`/`SIMRECON_JAVA` and PATH
defaults consistent with the existing commands. It reports resolved tool
identity, expected versus observed versions, host OS/architecture, checkout
identity and per-worktree Python/import readiness. Check Git and Make presence,
uv 0.12.19, worktree Python 3.13.12, worktree-local prefix and simrecon import
location. Report Java version/vendor/build and require version 21.0.7 for local
readiness; R1 selects the CI Temurin build. Mark source-launcher and reader-input
proof as deferred to the unchanged preflight in R3, not checked by readiness.
Local-ready can succeed with those explicit pending checks. Preserve preflight's
working source-launcher requirement; do not tighten it to a vendor rule.

Use bounded local subprocess checks and report missing executable, wrong version,
wrong worktree/import, uninitialized dependencies, nonzero command, permission
failure and timeout distinctly with the next applicable setup command. Readiness
does not install, sync, download, edit shell profiles, repair caches, contact
authentication services or launch an agent. Prevent probe-created bytecode in
the checkout; no report/cache files are written by the check itself.
An unhealthy required local prerequisite returns nonzero; local-ready returns
zero with explicit limits. Connectivity and native authentication remain
**not checked**, not implicitly healthy. The standard library check must be
usable before project dependencies exist; document its seed-interpreter needs.
It is not an engineered security or filesystem isolation boundary.

### R3 — classified preflight, connectivity and native capability evidence

After explicit setup, run the unchanged `make preflight` with selected tools.
Preserve locked sync, reader authentication/source-launcher proof, current-worktree
interpreter/import checks and isolated hatchling 1.32.4 check, their ordering,
failure status and stop-on-failure behavior. Local readiness cannot substitute
for preflight; preflight cannot substitute for full verification.

Document a decision procedure using actual command/status evidence:

- Missing/mismatched executable, import or environment: setup/tooling failure.
- Proxy/socket/DNS/TLS/HTTP access failure: connectivity evidence for that
  endpoint/command; distinguish sandbox denial from a remote response. An HTTP
  403 alone does not establish bad credentials. Keep TLS verification and the
  supplied proxy configuration; permission changes use existing authorization.
- Native stored-login status: evidence of a stored login only. Completed device
  sign-in: separate observed outcome. Working native role capability: an actual
  authorized launch or the smallest permitted capability probe when required
  and stale/missing, never a fabricated review. Reuse valid launch evidence.
- A 401 from the native service may establish an authentication failure for that
  attempt, not a repository defect or permission to erase/replace credentials.
- Unreachable executor: platform blocker. A script cannot start or repair it;
  running desired/observed state alone does not establish connectivity or cause.

Retain nonzero status and stop dependent stages. Mixed/unknown cause remains
unknown with a focused next diagnostic, not a guessed category or retry loop.
Do not add a mandatory login to local setup or make network/sign-in checks run
implicitly. Native CLI versions are recorded observations, not newly pinned
dependencies; confirm required supported controls when capability is needed.

### R4 — durable handoff and reusable role instructions

Document an operational use of the existing handoff/packet templates, keeping
one task Current state. A saved handoff identifies repository, branch and exact
base/candidate commits and tree, tracked/dirty state, contract/packet identities,
accepted test/fixture checkpoint (or **none**), ownership, pending role, gates,
environment/tool/input identities, cumulative attempts and known blockers.
Record known counts per role and unknown metering explicitly. Distinguish a
checkpoint from a moving branch name and preserve uncommitted work before a
workspace is retired; do not manufacture a commit identity for unsaved bytes.

For every required evidence item record its identity, originating command/status,
scope, material inputs and storage location, plus whether it is recovered,
newly reproduced, historical-record-only or unavailable. Include retention/access
limits when known. A local ignored path or expired external artifact is not a
durable copy. Keep sanitized summaries and reusable packets in a selected durable
destination under actual write/publication authority. Keep raw sensitive evidence
local/private; record the gap if no authorized durable destination is available.
No automatic upload follows from this contract.

Recovery obtains original commits and named artifacts through existing Git/file
tools, verifies identities, recreates the environment from R1, rechecks material
inputs and resumes only the allowed next stage. Do not copy an old `.venv` or
resume an exposed scientific conversation to simulate a fresh role. Saved launch
instructions bind current worktree, exact packet/checkpoint, model/effort,
supported memory/delegation controls, distinct final/report destinations and
bounded waits using the existing role-launch procedure. Blind A/B get only the
public packet, never this nonblind recovery report or raw logs. No exception to
#84's fresh native A/B/C/D workflow is introduced.

### R5 — recovery exercise and evidence limits

Exercise recovery in a disposable fresh checkout/environment without importing
the original tool cache, `.venv` or ignored evidence. Recover the saved #84
checkpoint `f8042042ff2b6865ecf501e38f11232de5d36fc9` from branch
`docs/84-reconstruction-memory-intake`, retaining its original history. Verify
its task/contract/packets and recorded predecessor identities. Use
[the saved task](https://github.com/david-hoffman/simrecon/blob/f8042042ff2b6865ecf501e38f11232de5d36fc9/docs/tasks/reconstruction-memory-intake.md)
and [the later diagnostic record](https://github.com/david-hoffman/simrecon/issues/105#issuecomment-6828272895)
as distinct dated sources, not competing Current states.

Carry forward all recorded charges, including the two failed native A launches,
zero accepted scientific review checkpoints, prior advisor/recovery work,
publication rejections, preflight/type-check attempts and sign-in attempts.
Do not add repeated cumulative summaries twice. The later comment reports another
resume preflight pair and a device authorization with no observed completion;
retain that attribution and unknown totals where attempts cannot be reconciled.
Missing `artifacts/reconstruction-memory/execution-receipt.json`, `roles/a01-*`,
`roles/a02-*` or resume evidence are **unavailable historical evidence**, never
newly passed tests, zero attempts or grounds to recreate a favorable verdict.

Show the exact next role and prerequisites without launching scientific work.
Recovering records does not establish current authentication, scientific
acceptance, full verification or required platform evidence. If the original
Git objects cannot be obtained, report the failed recovery and missing identity;
do not substitute a reconstructed document and call it the original checkpoint.
Do not amend or create a competing #84 execution state during this exercise.

### R6 — publication and acceptance preservation

Use selected safe metadata and reviewed summaries. Never commit/publish credentials,
tokens, device codes, private acquisitions, full environment dumps, sensitive
logs or native conversation transcripts. Source-free diagnostics are not general
secret redaction. Use harmless synthetic markers for confidentiality checks;
do not inspect secrets to test filtering. Publication needs its existing actual
authorization; #84's prior six-document backup approval is not a blanket grant.

Inherit [PROJECT coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance):
behavior coverage and independent risk review; percentages advisory. Preserve
exact native statement/branch reporting globally, per package/file and platform,
never-imported/subprocess scope, current JSON/HTML and integrity checks. Preserve
all 13 `make verify` phases, both wheels, audit, same-run M25 and its
33,554,432-byte limit. Full-local exact-candidate gating remains; CI still repeats
Ubuntu 24.04/macOS 15. Debian setup observations are not that platform evidence.

## Scenario inventory

Equivalent versions/paths under one decision are examples, not additional meaning.
The worker maps all rows to meaningful public-command proof or an observed
procedure exercise; the fresh reviewer challenges omissions and permitted cases.

| ID | Distinct outcome | Source / representative examples |
|---|---|---|
| S01 | Fresh supported setup reaches pinned preflight without old caches | R1/R3; Ubuntu 24.04 and macOS 15 separately |
| S02 | Repeat setup preserves pins, caller data and checkpoint/history | R1; already-correct tools and caches |
| S03 | Missing seed/tools yields explicit installation prerequisites | R1/R2; no uv, Python, Java, Git or Make |
| S04 | Wrong PATH tool is diagnosed; explicit compatible tool succeeds | R1/R2; uv mismatch, Java mismatch, path with spaces |
| S05 | Missing/wrong-worktree environment/import is diagnosed | R2; absent `.venv`, another checkout's Python/import |
| S06 | Local-ready succeeds without installing or implying remote readiness | R2; pinned environment, connectivity/auth not checked |
| S07 | Permission/nonzero/timeout probe failures remain failures | R2/R3; executable cannot run, bounded stalled probe |
| S08 | Preflight setup/reader/build failure stops dependent stages | R3; dependency fetch failure, corrupt reader cache |
| S09 | Connectivity diagnosis preserves actual cause limits | R3; sandbox socket denial versus remote 403 |
| S10 | Stored login, completed sign-in and valid launch stay distinct | R3; stored login followed by failed launch, no completion observed |
| S11 | Offline executor remains a platform blocker of unknown cause | R3; cannot start command despite reported running state |
| S12 | Exact saved checkpoint and available evidence recover in fresh workspace | R4/R5; original #84 history, packet identities and accounting |
| S13 | Missing evidence or inaccessible commit stays explicitly unavailable | R4/R5; absent ignored logs, no accepted checkpoint invented |
| S14 | Changed environment/input invalidates reuse where material | R4; same HEAD with different executable/import identity |
| S15 | Reusable launch packet preserves fresh roles, blindness and ownership | R4; A/B public allowlist, separate final/report destinations |
| S16 | Durable evidence uses authorized destination and safe selected content | R4/R6; synthetic sensitive markers, no authorized destination |
| S17 | Setup/recovery checks preserve full scientific and platform gates | R6; local readiness/preflight are not acceptance |

No human scenario, review, repair, time or spending limits were set. No new
numerical/scientific semantics or coverage targets are selected.
