# WS116 source-only method refinement

Resume the same investigator in `/workspace/work/issue-116` on source-preparation
commit `701b56d349adaf5e719510a158b51402876f9c30`; do not rebase. Existing contract,
investigator packet and named report-directory ownership still apply. Do not
delegate, commit, push or change product/tests/fixtures/gates/policy.

Root reports #112 independently accepted and published as PR121 at frozen head
`d9a0ba9`; its local and CI checks passed. #115 is integrated onto that parent,
focused 1118 checks passed, and candidate `ace06c8` is undergoing canonical full
Ubuntu verification; its independent D review is pending. These are contextual
root reports, not an accepted #115 baseline or new experiment evidence. Root owns
integration and will supply the final accepted dependency identities later.

Root's #115 gate has the exclusive resource window. This stage permits only
source/document/harness edits and read-only shell inspection. No Python, probes,
lint, types, tests, installs, numerical work, benchmarks or new-tool execution.
Do not install or run GNU time, or probe wait4 now. Actual environment/tool proof
must be captured at actual execution, without relabelling post-run observations.

Refine the method before any measurement freeze:

1. Replace the ambiguous child `whole_process_peak_bytes` name with explicit
   pre-call, call-end and post-observation native high-water snapshots. Keep
   monotonic timestamps and scope for each. Distinguish these cumulative samples
   from complete-child peak through exit, including JSON/teardown.
2. Assess stdlib `os.wait4` as the Linux complete-child outcome route (or an
   explicitly justified supported alternative). Use a single wait owner; do not
   let `Popen.poll`/`wait` reap the child before terminal rusage is collected.
   Preserve exit/signal status, stopped outcomes, timeout/TERM/KILL and exception
   cleanup, without double waits or implicit retries. State max-process versus
   concurrent aggregate scope, exclusions, no numerical grandchildren and
   inherited/pre-exec high-water limitations. This remains unvalidated source.
3. Avoid whole-array copies during input/output hashes: frozen fixture.identity
   uses `tobytes`, so use bounded streaming value hashing or explicit bounded
   array identity preserving shape/dtype/endian/content. Retain caller and one
   result only; no baseline/candidate/reference workflows coexist in a trial.
   Hashing/provenance and finite checks still have declared observation costs;
   avoid presenting their memory as numerical-only allocation.
4. Make receipt statuses and boundaries concrete: admission refusal, spawn or
   observation failure, child exit/nonfinite/scientific failure, signal/timeout,
   missing/malformed child record, successful complete-child observation pending
   independent scientific qualification. Every attempt survives; distinguish
   raw exit status from actual scientific success. Capture identities before and
   after relevant work, actual-time observer/tool/backend/thread/resource facts,
   terminal rusage and disk accounting limits without circular self-hashing.
5. Keep unprofiled matched fresh-process trials separate from stage attribution
   and observer-perturbation controls. Preserve the finite manifest, original
   drafts/corrections/accounting, immutable material identities and later
   #117/#118 affected-workload refresh requirements.

Write a narrow source-only method-review input under the report directory naming
exact files/claimed invariants, unresolved runtime validation and concrete
questions for a fresh independent static reviewer. It must not claim report
acceptance, scientific quality, executed probes or gate readiness.

Return useful revised sources/docs plus exact shell-check statuses, output
digests, remaining method/runtime gaps and scratch/process facts; no waiting for
accepted parent. Coordinator may then launch one fresh static method reviewer
sequentially and return WAITING again. Requested model/effort remains Sol/high;
actual served attribution/tokens/cost are unknown. Preserve prior attempts.
