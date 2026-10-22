# Disposable repository maintenance race

**Version 1.0.** Bounded follow-up to the owner's CI repair and stack-rebase
request. The baseline is PR39 commit
`cca7314b87e3c8a9a7479f4530e26ab3eaa5a461`.

The macOS public-caller test observed `.git/objects/maintenance.lock` during
inventory and then failed when the file disappeared before `stat()`. A separate
verification-evidence test observed the same lock change in complete metadata
snapshots. Both disposable repository builders committed with automatic Git
maintenance enabled. This is a fixture/environment interaction; these failures
show no scientific product defect.

The correction sets repository-local `maintenance.auto=false` immediately after
`git init` in `VerificationFixture` and `create_repository`. The latter setting
also applies to the evidence fixture's later commit and linked worktree. Keep
all snapshot contents, assertions and public verification commands unchanged.
Do not filter transient paths, retry snapshots or change host Git configuration.

Run all public-callers verifier cases (`-k verifier`) and the complete
output-protection and evidence-output modules through the source-free project
harness. Retain exact selected-node inventories and counts. Use an isolated global Git
configuration with automatic maintenance enabled and disposable fixtures under
`/private/tmp`, outside Git ancestors, to challenge the local override. Check
the affected source formatting and retain exact command/status/environment,
lock, tree and fixture configuration evidence. No routine full local suite is
part of this follow-up; the coordinator retains the owner's task-specific
verification decision and fresh independent review requirements.

The coordinator's single canonical state and ignored evidence live under
`artifacts/stack-rebase-20261022/maintenance-race-followup/`. This pointer grants
no push, merge or release authority. The worker returns a clean passing commit
for independent review; the coordinator owns descendant replay and publication.
All previous attempts and charges remain cumulative; human numeric limits are
not set and unmeasured usage remains unknown.
