# Ubuntu-only required verification

**Version 1.0.** Owner-requested platform-policy and named infrastructure migration.

On 2026-11-14 the owner stated: **“We don’t need macOS verification. How do I get
rid of that?”** This authorizes removing mandatory macOS qualification, including
the macOS CI job and corresponding required-check setting. It does not authorize
removing Ubuntu verification, changing scientific behavior, lowering other gates,
altering bypass/approval/merge rules, or publishing an RM84 branch/PR.

## Policy and scope

Ubuntu 24.04 becomes the sole required platform for ongoing and future work,
including RM84 and the continuing CE roadmap. Other-platform qualification is
optional. Missing macOS reports alone cease to block acceptance, submission or
dependent slices. Known failures still require diagnosis under the existing rules.

The current PROJECT platform policy supersedes older platform-specific clauses
in inherited contracts/tasks/plans/packets. Scientific expectations, supported
input domains, portability code and platform-specific unit cases remain intact.
Historical receipts, verdicts, lessons and setup snapshots retain their original
meaning and charges. In particular, RM84 D1 remains evidence-incomplete under the
policy it reviewed; it is not rewritten into an acceptance.

Preserve all 13 `make verify` phases, two-worker strict test outcomes, complete
native statement/branch/file/package/global JSON/HTML evidence on Ubuntu, wheel
isolation, dependency audit and same-run M25 <=33,554,432 bytes. Percentages stay
advisory. Full-local exact-candidate submission and independent review remain.

## Ownership and review

The coordinator owns the policy documentation and this named bounded
infrastructure change: `.github/workflows/verify.yml` loses only `macos-15` from
its matrix. Keep the singleton matrix so `Verify (ubuntu-24.04)` and the Ubuntu
artifact name remain stable. The comment in `tests/test_imagej_export.py` may
name Linux/Darwin without calling both required; its executable AST is unchanged.
No executable test, fixture, runtime, lock, Make target, verifier or generic role rule changes.

A fresh independent policy reviewer assesses the concrete proposal before
activation. After adoption, a fresh reviewer checks the named infrastructure
diff and exact passing candidate; RM84 additionally needs a fresh D readiness
disposition. Existing scientific checkpoint/resource evidence may be reused only
for demonstrated unchanged material inputs with reviewer agreement. New full
receipts must identify the changed candidate; old receipts are not relabeled.

GitHub reconciliation is limited to removing `Verify (macos-15)` from each
effective required-check rule while preserving every other field. Inspect live
settings and prepare the exact diff before an authorized update; verify readback.
If administration access is unavailable, record the unapplied change and exact
owner steps. Do not replay historical protection-request JSON, invent successful
remote enforcement or alter unrelated protections to obtain access.

## Evidence and continuity

The sole Current state remains `artifacts/rm84/current-state.md`. It records the
policy review, exact candidate, checks, remote observations/outcome and fresh
readiness verdict, while retaining all previous RM84 attempts and measurements.
The owner set no new numeric limit. Serving attribution/tokens/cost remain unknown
where not supplied. This migration creates no PR, merge, release or external message.
