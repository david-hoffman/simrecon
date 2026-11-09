# Test apparatus optimization — incomplete handoff

## Current state

**Incomplete; discovery only. No optimization, full baseline, acceptance review,
or final verification has completed. No PR is ready.** The user explicitly
authorized pushing this handoff branch to continue in a new cloud container.
This is the pre-PR incomplete-backup exception in `AGENTS.md`, not a waiver of
the full-local submission gate.

The requested goal is aggressive removal of equivalent test/fixture work while
preserving current C-equivalent scientific contracts and numerical behavior.
The user added a target of **total test time below 10 minutes**; the coordinator
adopted the stricter target of canonical `make verify` below **600 seconds**, with
pytest time reported separately. No total task, review, scenario, token or money
budget was set. Do not invoke Superpowers. Do not merge.

The sole execution blocker is the active cloud instance's network policy. Pinned
reader preparation failed with proxy `403 Forbidden`. These hosts are required:

- `downloads.openmicroscopy.org`: pinned Bio-Formats jar.
- `sites.imagej.net`: pinned ImageJ jar.
- `api.osv.dev`: mandatory vulnerability audit.

The user reported publishing the environment configuration. Fresh status still
showed running revision `1`, enforced policy, and no added hosts; fresh HTTP
connections were still denied. Available tools exposed status/diagnostics but
no environment restart or policy mutation. A new instance must actually apply
the published settings. Do not bypass the proxy, weaken reader authentication,
omit the audit, or treat publication as proof of connectivity.

## Exact starting point and authority

Repository: `https://github.com/david-hoffman/simrecon`.

- Required and observed starting HEAD:
  `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`.
- Observed tree: `0fa2edf2df263fa08110daa26ceb22c847b2900b`.
- Origin was fetched before creating `codex/test-apparatus-edcf53b` directly from
  that commit. Branch, HEAD, tree and clean staged/unstaged tracked state were
  verified and reported before dependency setup or expensive work.
- `origin/main` equaled that exact commit at intake. Recheck it before eventual
  publication and disclose divergence; never silently substitute another base.
- This handoff adds documentation and discovery evidence only. All runtime,
  tests, fixtures, workflows, configuration, dependencies and contracts remain
  byte-identical to the required baseline. The final handoff commit identity is
  recorded outside these tracked bytes, in the conversation.

The original instruction authorizes autonomous discovery, appropriate role-owned
implementation, focused and exact-candidate canonical verification, independent
reviews/final preservation sweep, confirmed task scratch cleanup, branch push
and a **new PR after all required local checks/reviews pass**. The latest user
instruction additionally authorizes this incomplete backup push and a pickup
prompt. It does not authorize opening an incomplete PR.

Use the explicitly requested [OpenClaw test-audit skill](https://github.com/openclaw/openclaw/blob/main/.agents/skills/test-audit/SKILL.md)
together with `.agents/skills/test-audit/SKILL.md`, root `AGENTS.md`, applicable
role skills, and relevant `docs/PROJECT.md`. The external skill's campaign,
candidate-evidence workflow and boundary guide were consulted; SIMrecon's
full-local gate, roles and blindness remain binding. Learn selectively from
[PR56](https://github.com/david-hoffman/simrecon/pull/56). Existing two-worker
flags and prior shell-dispatch delivery consolidation are already present.

## Completed read-only discovery

Four fresh, nonblind, nondelegating agents used requested `gpt-6.1-sol` / high
settings under project model-selection guidance. They are inventory/accounting,
scientific oracle discovery, infrastructure discovery, and neutral API discovery.
They are not A/B/D or final acceptance reviewers. Actual served-model attribution,
tokens, monetary cost and exact role elapsed times are unknown.

The [evidence directory](../reports/test-apparatus-audit/) contains all reports,
723 declaration records, full preservation ledgers, inventory, historical PR83
accounting, environment failure evidence and the profiling plan. Every declared
test was independently reconciled against the syntax-tree inventory: **52 files,
723 declarations; no missing, extra or duplicate assignment**. This is a source
inventory, not proof that tests pass or that every oracle is valid.

| Lane | Files | Declarations | Disposition |
| --- | ---: | ---: | --- |
| Scientific | 28 | 413 | 407 retain; 6 conditional consolidation proposals |
| Neutral API | 5 | 113 | Retain all |
| Infrastructure | 19 | 197 | Retain all |

Conditional proposals are not approved edits. Each must be checked against
measured cost and routed before implementation. Current collected case count is
unknown: static accounting establishes 3027 examples plus one generated family,
estimated at 68. Reconcile the resulting estimate of 3095 against actual native
collection/JUnit. Inventory includes 22 fixtures, 45032 test/support Python lines
and 9091 owned runtime Python lines; physical lines are not coverage statements.

High-value leads, all with **unmeasured runtime savings**:

1. `_pytest_policy.PARALLEL_GROUPS` is empty. Existing `-n 2 --dist=loadgroup`
   assigns all tests to one `serial-rest` group. Qualify useful whole-file
   groups with measured balance; preserve reader-cache affinity and serial
   fallback. Do not present two-worker flags as a new improvement.
2. CE06 test-support `Disc` operations repeat identical local propagation and
   allocate unused default arrays. Scientific oracle ownership/review is required
   even for apparently equivalent arithmetic changes.
3. Six CE07 consolidation proposals have exact keeper/assertion mappings in the
   scientific report. Source-level estimates remove 30 repeated workflow calls,
   27 complete observers and 25 budgets without dropping logical examples.
   Repeated complete fixture-catalog construction is a separate profiling lead.
4. ImageJ tests launch 20 genuine reader JVM observations. Compiling the unchanged
   Java observer once per qualified session/worker may avoid repeated source-file
   compilation while preserving every fresh JVM observation and assertion.
5. M41 stages roughly 2 GiB before a signed-size rejection. This is a reported
   product-boundary lead, not authorization for a bounded binary/data-loss edit.
   Profile before deciding whether it belongs in this task's implementation.

CE08's three distinct acceptance tests, on-demand independent expectations,
compensated direct transforms, physical/quantization checks, shapes and hashes
remain intact. `examples/reconstruct_simulated.py` is a real caller of CE08 test
support. Do not restore retired science or substitute precomputed old snapshots.

## Resume sequence and role ownership

1. Read this coordinator handoff on `codex/test-apparatus-edcf53b`. Confirm the
   branch descends from the required commit and contains only handoff evidence.
   Fetch origin and record the remote base. Preserve this committed branch.
2. For the **fresh exact baseline measurement**, switch the same task checkout
   temporarily to detached `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`. Verify/report
   HEAD, tree and clean tracked state before setup. The handoff evidence remains
   available through the committed branch; copy its needed profiling inputs into
   ignored `artifacts/test-apparatus-audit/` first. Switch back to the handoff
   branch only after baseline evidence is safely retained. No alternate baseline.
3. Refresh cloud status and probe the actual required destinations. Recheck tools,
   environment/import identity and locked setup with `make preflight`. The prior
   instance used `/workspace/.simrecon-tools/activate.sh`, uv 0.12.19, CPython
   3.13.12 and Temurin 21.0.7+6. Do not assume these paths exist in the new instance.
   Use one worktree-local `.venv`; preserve required shared dependency inputs.
4. Complete the first actual canonical baseline `make verify`, retaining failures
   honestly. Profile setup/call/teardown, subprocess launches, reference work,
   coverage and all phase/outer times. The retained profile plan selects top-level
   pytest durations/JUnit through an exact-argv uv wrapper; nested commands are
   forwarded unchanged. `strace --seccomp-bpf` execve collection was cheaply
   qualified here. Recheck tool capability and paths. Use identical instrumentation
   on baseline/candidate; disclose overhead, cache/load differences and uncertainty.
5. Review measured costs against the read-only ledgers. Name bounded infrastructure
   ownership and a fresh independent reviewer for conventional harness changes.
   Scientific test/fixture/oracle changes require fresh blind A and fresh blind B
   with sanitized public packets and complete dependent-test mapping. Never feed
   these nonblind reports/ledgers, implementation history or coverage maps to A/B.
   C remains restricted to named product ownership and frozen reviewed tests;
   if no product change is needed, record that rather than inventing one. Use fresh
   D for high-risk preservation and an independent bounded reviewer for that slice.
6. Preserve all approved positive, negative, representation, compatibility and
   operation-time failure obligations; tolerances; omission guards; exactly two
   workers/no restart; native per-file/package/global coverage JSON/HTML and child
   shards; all 13 verification phases; and same-run M25 evidence with the unchanged
   33554432-byte limit. Percentages are advisory; report integrity is mandatory.
7. Run focused checks, commit the exact final candidate and run canonical
   `make verify` from a clean tracked start. Obtain the required fresh independent
   reviews and final preservation sweep of that exact passing scope. Preserve
   final hashes/results outside tracked candidate bytes. Report runtime, concrete
   work reductions, obligations, net production/test/support growth and limits.
8. Follow repository completion housekeeping; recheck origin/base; push the final
   passing branch and open a new PR. Do not reopen PR83, cherry-pick it or merge.

## Evidence, accounting and cleanup

Current attempt: one preflight run failed during authenticated reader setup;
separate interpreter/import and isolated hatchling 1.32.4 health checks passed.
Seven explicit HTTP probes across three user/status transitions were denied;
the preflight reader request was an additional failure. No actual test suite,
full baseline, benchmark, candidate gate, implementation correction, A/B/C/D
review or final preservation sweep has run in this attempt. Timing and memory/
coverage results for this baseline/candidate are **unknown**, not zero.

Four discovery launches completed. Inventory's optional repeated syntax-tree
query was stopped after approximately 33 seconds and replaced with a per-file
query; retain that diagnostic charge. No owner-wait time or overlapping role
durations have been added into a fabricated elapsed total. Routine diagnostic
reads of absent optional paths are not test results. Detailed unmetered effort
remains unknown. Preserve all future rounds, failed runs and repairs cumulatively.

[PR83 history](../reports/test-apparatus-audit/pr83-history.json) is retained only
as prior-attempt accounting: wrong baseline `8f6b35c`, historical full gate
3666.65 s / 1229.67 s, historical pytest 3392.25 s / 1185.32 s, abandoned low-value
cache and reported reviews/corrections. Its local detailed artifacts are unavailable;
exact historical role rounds/costs are unknown. Those results establish nothing
about the required baseline or this task's performance. No PR83 changes were used.

Durable discovery evidence is retained in this commit and in the ignored original
artifact directory in the current instance. Compressed ledgers preserve the original
bytes, with hashes in `archive-manifest.json`; they are nonblind evidence only.
No runtime/test changes are included. Repository diff/archival integrity checks
apply to this documentation backup only, not product readiness.

Task-owned disposable scratch cleanup completed: the inventory agent's
`/workspace/work/test-apparatus-inventory/` and coordinator's
`/workspace/simrecon/work/test-apparatus-audit/` were removed with ordinary `rm -r`
after durable copies were preserved; absence was confirmed and no error occurred.
No owned writer remains. Kept the current checkout/branch,
`artifacts/test-apparatus-audit/`, shared `.simrecon-tools`, `.venv`, original data,
tracked fixtures, native reference inputs and all unrelated artifacts. No worktree
was created. The evidence and required environments remain available locally.
