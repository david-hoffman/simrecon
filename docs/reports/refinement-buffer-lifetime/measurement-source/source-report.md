# RB117 fixed external method7 source delta

This is an author source report, dated 2026-11-16. It supplies no suitability,
qualification, resource, scientific, or execution acceptance. Only the fixed
external source/data binding was authored. A fresh independent SOURCE reviewer
decides the delta's suitability and any control-evidence applicability.

## Authority, inputs, and write boundary

The assigned packet is
`/workspace/work/campaign/evidence/117/resource-method-source-author-packet.md`,
SHA256 `694b225a64e6d77f11d4f52148ad6e13b7d7102ed87bb2ff2d83467666833a25`.
Its named original files were read under
`/workspace/work/issue-117/docs/reports/reconstruction-working-set/`:

| Original input | Verified SHA256 |
| --- | --- |
| observer.py | `384b4f1a95ad135136c60b9bb750437fe72e5bbb1a94fc21bd7cc1ae14ff6c9e` |
| run_attempt.py | `2c2358bbcb801a970de6b1d3c786cf510394887ef397b1e14d7ad4a843efea1e` |
| workload_child.py | `5249e4cdadbee6523012127468fd9c3d90228df2558c81087929bc35e60e5459` |
| manifest.json | `bd633265f3ac1967420b2032401b4f52c2a525271da510ed16dfb3506ef05234` |
| method_qualification.py | `56c1dafe3c6bdab3b9e9e6fdefc1dc01d419b09e6f6f09bc8b302073474f2a21` |

Both named proposal inputs also matched:
`resource-conditions-parent1587-PROPOSED.tsv` SHA256
`e9ae81c06a862414cfb830f7ae4e339ddba631aa01b6e06d1d6092d485bcad73` and
`resource-protocol-parent1587-PROPOSED.md` SHA256
`742106e826c1387c3819306b7c1c447ec74743991e5dcba88286df998fe17980`.
Their directory is `/workspace/work/campaign/evidence/117/`.

Only the required instruction context was additionally read:
`/workspace/work/issue-117/AGENTS.md` SHA256
`56ea4b592323779ac86cacede6dc15eff3d80098e25805cb606e6166010d5ecd`,
`docs/PROJECT.md` SHA256
`530e72dbc3b9e73756687c3893bef2803cb775080a12539681020916c59b9fee`, and
`.agents/skills/implement-work/SKILL.md` SHA256
`3dd402828a1de66bed570de455daf1492ce3120f7174b2386eef330f4e02c23c`
within that worktree. No linked history, raw controls, reports, product bodies,
test bodies, active-process data, or grants were consulted.

All writes are the nine packet-permitted files in
`/workspace/work/campaign/evidence/117/resource-method-source/`.
No tracked or original116 file was edited. No control worktree, raw directory,
grant, inventory, fixture, reference data, scratch script, or new helper was
created. No delegation occurred.

## Frozen source/data and complete delta

| External file | SHA256 | Treatment |
| --- | --- | --- |
| observer.py | `eacf24b70cd67f12e403906cf92bb7cb1bb1a7632645335a8b8f3bfbc4225745` | material/root binding only |
| run_attempt.py | `6f34617bb59c060eeceeeb6a06a6180755448f3310481202f96df5e5dd1fe14f` | fixed root, declaration, output binding and direct callers |
| workload_child.py | `5249e4cdadbee6523012127468fd9c3d90228df2558c81087929bc35e60e5459` | byte-identical copy; cmp succeeded |
| method_qualification.py | `56c1dafe3c6bdab3b9e9e6fdefc1dc01d419b09e6f6f09bc8b302073474f2a21` | byte-identical preserved control source; cmp succeeded |
| manifest.json | `1854f8760dd9ede607b2611f2d9640e1e3a7056e054ae564211fdea90ef7d4ed` | fixed task declaration with ROOT-confirmed revision binding |
| source-delta.patch | `1d53ddc1b74ce69947e9beff634dee07d4b4e88afc831deae636abd2f31c0ae1` | complete unified diff against the named originals |

`source-manifest.sha256` freezes these files, both reports, and every named
original/proposal/instruction input. It excludes its own bytes to avoid circular
self-identification. The separate handoff carries the routing limitations.
The complete patch contains only observer.py, run_attempt.py, and manifest.json;
there are no omitted executable-source differences in the two identical copies.

ROOT commissioned one same-author manifest-only continuation before fresh SOURCE
review, then clarified authority for the corresponding parent-status correction.
The original nine-file freeze was already archived by ROOT at
`/workspace/work/campaign/evidence/117/resource-method-source-before-candidate-e694/`
and ROOT reported its hash verification; this author neither created nor read
that archive. Preserve its original identities: manifest
`4f167721476f946bd58970d8096690a3f2537ba93b3427ecff0a9136c32f4858`,
delta `69cd092cc4e552b63ba3597dca0549f21de3cc7e0f89ad3b2f2301272d6b7edc`,
report `21d796feb93a6b95f179c72de0b4d3579ef7d9d25bb7add51c88e7044eb135a0`,
handoff `58d51153fb748774a62c59fa0157d83c1b56ab8277fa42517d04a2b96af6ca2c`,
and ledger `84eeb16541734e2bc2d07219b52fee2cfac6d374ae6b55d5169e4d79cc6e14dd`.
All four executable-source identities above are unchanged in this continuation.
The only program/data change after that freeze is revision-mapping candidate
identity/status and parent status in manifest.json; the other changes are
corresponding factual report/handoff, complete delta, and hash-ledger updates.

## Exact bindings and changed callers

| Changed scope | Signature/callers | Necessary binding |
| --- | --- | --- |
| observer.py::material_hashes | `material_hashes(root)` unchanged; runner `admit`, runner `main` at pre-admission/before/after/final, unchanged child `execute` before/after | Accept only exact resolved `/workspace/work/issue-116` or `/workspace/work/issue-117`; hash actual product, fixture, benchmark, and lock under their existing root-relative keys; hash the active fixed external method files under explicit absolute `external_method:` keys. |
| run_attempt.py module constants | `ROOT` replaced by literal `ROOTS` and fixed `OUTPUTS` | Exactly `parent` and `candidate`; separate `raw-parent` and `raw-candidate` output roots; no arbitrary product/Python/module/command selector. |
| run_attempt.py::git | `git(*args)` becomes `git(root, *args)`; calls in `admit` and `candidate_identity` updated | Read Git provenance from the selected actual product root. |
| run_attempt.py::admit | `admit(grant)` becomes `admit(grant, root)`; `main` updated | Keep original candidate/material comparisons and admission machinery, binding them to selected root and active external task manifest. Growth rows must equal the manifest's literal 256 declarations; existing separate admission and smaller-evidence guards remain. Only declared condition/profile groups are eligible. |
| run_attempt.py::candidate_identity | `candidate_identity()` becomes `candidate_identity(root)`; `main` pre-admission/after/final calls updated | Preserve existing head/tree/tracked-diff identity schema using selected root. |
| run_attempt.py::main | `main()` unchanged; CLI now requires `--revision parent` or `--revision candidate` | Verify fixed external method directory and resolved selected root; use selected-root context, cwd, product PYTHONPATH, child root argv, and material checks; add truthful receipt `revision_selector`, `product_root`, and `external_method_root`. |

The external method keys are exactly
`external_method:/workspace/work/campaign/evidence/117/resource-method-source/`
followed by each of `manifest.json`, `observer.py`, `run_attempt.py`,
`workload_child.py`, and `method_qualification.py`. No external source is forced
through `relative_to(product_root)`. No original tracked116 method is silently
identified as the active external method. Both revisions use these same five
external files/hashes. The product/fixture/benchmark/lock keys still identify
actual selected-root files and may differ between revisions.

The declared parent source is `158776ade28079276304d49a6b973eccbf4109c9`, tree
`23530ae22e7e1a64f8171dbbedfea81d1b00174c`. ROOT confirmed that fixed parent
worktree clean. ROOT also froze the clean candidate at fixed root
`/workspace/work/issue-117`, source commit
`e6945817850cfdaa3ebbfe21e7a23784964208d6`, tree
`cd637c9b568e2cbe35119193804b36105ec54500`, product-source digest
`527bb3459e295a5cec0a776a464d82723e32b0b6f64e3d47f3eb514529e19b38`.
The manifest's `source` field denotes Git source commit, as for the parent; the
separate product-source digest here is ROOT-supplied evidence. These are
coordinator confirmations, not author-observed worktree/setup assertions.
Resource qualification and individual admission remain pending. No product,
fixture, lock, interpreter, environment, backend, dirty/version, import, grant,
resource-domain, or runtime identity was measured in this role.
Existing actual before/after checks remain for later root-granted execution;
the coordinator must bind any further required version/setup facts separately.
A root-path change requires source rebind and fresh review.

## Fixed manifest and finite scope

| Groups | Literal conditions | Profile | Proposed calls across both revisions |
| --- | --- | --- | --- |
| 1/2 | central64 summary/full searched, `[1,3,8,64,64]`, no case key | false | 12 |
| 3/4 | rb117-2d-search summary/full, `[2,2,1,12,16]`, `case=2d-search` | false | 12 |
| 5/6 | same central64 summary/full as groups1/2 | true | 12 |
| 7/8 | growth256 summary/full searched, `[1,3,8,256,256]`, no case key | false | 12 |
| 9/10 | same growth256 summary/full as groups7/8 | true | 12 |

The four initial conditions are only groups1-4. Three repetitions use declared
paired order parent/candidate, candidate/parent, parent/candidate. Core scope is
24 calls; total proposed scope is 60. `initial_attempt_count=24` describes that
matched core across both revisions. These are proposed scope counts, not observed
calls, automatic scheduling, budget, or an admission.

Growth256 remains outside `initial_conditions`, requires its exact row in the
grant's `declared_growth_conditions`, and retains separate-growth-admission and
smaller-measured-evidence requirements for each revision/mode/profile. No 192,
supplied, extra profile2D, or other growth route is declared in this task.
Every largest group remains pending new256 admission. Central profiles reuse
groups1/2; largest profiles reuse groups7/8. No duplicate unprofiled series was
added. Fixed bootstrap/startup bounds, four startup thread controls, generator,
constants, repetitions, 0.01-second sampling, and original method mechanics are
preserved. No old resource thresholds, numerical formulas, or fixture values
were copied into this task declaration.

## Preserved machinery and qualification routing

The complete diff leaves `SESSION_BOOTSTRAP`, `FixedSessionLaunch`, readiness/FD
machinery, `WaitOwner`, `cleanup`, `independent_monitor_stop`,
`monitor_sample_decision`, `stopped_status`, `observe_session_readiness`,
`observer_exception_status`, `observed_child_status`, `validate_complete_record`,
`child_outcome`, stage hooks, rusage snapshots, array identity, finite checks,
and the complete child byte-for-byte unchanged. Main's launch/session/wait/
monitor/termination/parser control flow is unchanged apart from the named
binding substitutions and metadata. The child still retains one caller/result,
imports from the declared product root, calls one unchanged public workflow,
and creates no numerical descendants.

The following are finite changed-path review/qualification candidates for the
coordinator and fresh reviewer to select, never executions or mandates here:

- Fixed parent/candidate selection, exact resolved roots and external directory,
  distinct output routing, actual cwd/PYTHONPATH/root argv, and provenance checks
  on each revision. Reject undeclared selectors/relocated method bindings.
- Active external material-map keys on both revisions, actual product/fixture/
  benchmark/lock keys, matching grant/spec/child maps, and changed/missing material
  detection before/after. A hash identifies bytes; it accepts no scientific result.
- Exact native64 and `2d-search` full/summary manifest/shape/search bindings,
  profile eligibility, fixed repetitions, undeclared condition/growth refusal,
  and missing separate256 admission or smaller-evidence refusal. No new numeric
  fixture or generalized generator is proposed.
- External runner integration with the unchanged fixed launch/readiness/nonce/
  session/exec and exact-PID wait/cleanup paths, record completeness and stop
  precedence. Any fresh readiness, wrong/late/missing nonce/session/exec, nonzero/
  signal/partial-record/deadline/ownership cases must use separately routed
  existing finite controls and actual material bindings.
- Only genuinely uncovered public one-call retention/finite/value/native-unit
  bindings, if identified by independent review; no reference reconstruction,
  warmup, new numerical fixture, profile executor, or broad control framework.

Unchanged control-source reuse candidates, requiring material and applicability
proof rather than a whole-control rerun solely because file hashes changed:

| Original source controls | Unchanged subject | Limits requiring a fresh decision |
| --- | --- | --- |
| `normal_case` / Q1-normal; `small_lifecycle_case` / four Q2 cases | fixed launch/readiness, WaitOwner, direct-PID signals/cleanup, native conversion | External runner main integration and selected-root/material/output binding are changed; no prior full-source pass transfers. |
| `parser_case` / Q4-parser | child_outcome, validate_complete_record, dtype/bootstrap helpers | New spec condition/profile/material-map dependencies need affected binding assessment; no parser-control rewrite here. |
| `tiny_hash_case` / Q5-tinyhash and `tiny_hash_vector` | observer array/finite and frozen fixture/benchmark value protocol | Actual selected-root fixture/benchmark/lock/import/environment must be established; numerical workflow and resource benefit remain outside this control's scope. |
| `method6_controls` / method6-rss-controls | strict RSS gap/timestamp/terminal confirmation, independent-stop precedence, late-readiness/final-status helpers | Source-only synthetic semantics; no live-exit/kernel-wait proof. Fixed external driver/source keys need separate routing. |
| `context_case` / Q0-context | existing context/backend observation code | Actual A/B environments and selected filesystem root have not been checked here. |

No historical control receipt or result was opened. Embedded source references
to prior receipts establish only what the source expects. `retained_q1`,
`retained_q2`, `retained_q4`, and `method6_prior_scope` remain unchanged source;
none was called or accepted. No mandatory blanket requalification is inferred.

## Preserved qualification driver is not executable setup

The copied `method_qualification.py` is source preservation, not an adapted
external qualification entry. Its exact unresolved binding points are:

- Lines19-21 still derive `ROOT = HERE.parents[2]` and `QUAL = HERE / "qualification"`.
  In this external location they do not name the chosen product/control layout.
  No qualification directory, inventory, or fixtures were copied or created.
- `admission` line148 calls `method.git("rev-parse", "HEAD")`. The external runner
  now requires `git(root, *args)`. The concrete caller substitution, only after a
  properly bound driver root exists, would be
  `method.git(ROOT, "rev-parse", "HEAD")`. This was not edited or run.
- `source_identities` lines82-125 and `pure_method6` lines1157-1177 still require
  worktree-relative method/inventory/fixture keys and reject outside-root source.
  They do not implement the new explicit external_method keys.
- `tiny_hash_case` lines668-680 still resolves fixture/benchmark imports through
  the old ROOT assumption; `context_case`, generic admission preflight, and main
  postflight also use that ROOT.
- `retained_q1`, `retained_q2`, `retained_q4`, and `method6_prior_scope` still use
  original QUAL receipt locations and original whole-file/root-relative mappings.
  `method6_prior_scope` also names a fixed old116 legacy runner source and parses
  named functions. No path/hash substitution or evidence relabeling was made.

Running this copied driver would not establish qualification of this external
binding. A concrete minimal future scope request is: separately own only its
fixed revision ROOT/QUAL/source-key/inventory/fixture/retained-evidence bindings
and the single `method.git(ROOT, ...)` caller; preserve every control body and
numeric fixture. Alternatively, the coordinator may route unchanged original
controls with independently accepted function/material applicability plus a
finite affected external-binding slice. Neither route was implemented here.
If broader changes are necessary, they require a new concrete ownership packet
before edits. This report requests no blanket control rewrite or new helper.

## Static activity, failures, and accounting

Administrative shell/file operations only: exact named-file `cat`/`sed`/`rg`,
`sha256sum`, `cmp`, `diff`, fixed-directory `mkdir`, exact four-file `cp`, and
text patch construction. No Python/JavaScript computation, AST, compile, import,
lint, type check, test, probe, CLI/help invocation, install, synchronization,
benchmark, measurement, process-monitoring, Git mutation, commit, push, network,
reviewer, or workload/control child occurred. Tool orchestration called file
tools only. There are no owned persistent runtime processes or launched children
to clean up; this is about this role's actions, not a global process claim.

Every named primary hash matched on first verification. Both required identical
copies matched with cmp. A full runner read was output-truncated; subsequent
focused source reads covered the relevant binding and preserved machinery.
No executable-source correction cycle or runtime failure occurred. The uncovered old
qualification `method.git` caller and ROOT/key/layout assumptions remain
explicit unresolved future routing dependencies, not hidden passes. Syntax,
format, imports, and runtime behavior were not checked and remain unknown.

One source-author pass plus one same-author manifest-only continuation and its
parent-status scope clarification; no delegation or runtime/control/scientific
attempt. One report-text patch initially failed its expected-context match and
made no changes; the exact source context was reread and the patch corrected.
The continuation used only source/file reads, text edits, diff construction and
hashing, with no executable-source edit, runtime/AST/import/test/check activity,
or additional archive. The 60-proposed/core24/256-pending scope is unchanged.
Requested model/effort/fork: Sol/high/fork-none per assignment; actual serving,
tokens, cached tokens, monetary cost, elapsed time, and runtime meters are unknown.
Optional role controls are unavailable; shared filesystem and prompt restrictions
provide no engineered isolation. No human numeric cap was supplied to this role.
Prior campaign charges/attempts/failures remain intact and were not reset or
recounted. The next action is fresh independent SOURCE review, then coordinator
routing of only accepted affected qualification/applicability paths. Remaining
setup/material confirmation, grants, admissions, and exclusive execution windows
remain with the coordinator.
