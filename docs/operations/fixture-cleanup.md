# Completion cleanup of task scratch and worktrees

**Version 1.0.** Coordinator housekeeping under [delivery specification section 9.1](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#91-automatic-cleanup-at-task-completion).

Deleting an explicit list of confirmed disposable task fixtures, scratch directories or worktrees with existing filesystem and Git commands is housekeeping. It requires no custom helper, test suite, independent review or full product verification solely for the deletion.

1. **Identify exact targets.** Use task creation records or explicit owner instructions. Age, a familiar name, ignored status or a closed chat alone does not establish disposability. Preserve the current checkout, tracked source/fixtures, durable evidence, active or unrelated work, shared caches/environments and known retained dependencies unless the owner explicitly authorizes discarding the named material. Keep uncertain targets and continue with clear ones; do not start a global reference scan or preservation-proof project.
2. **Close owned processes and check worktrees.** Stop this task's writers before removing their scratch. Check worktrees for uncommitted work and ensure needed commits remain accessible outside the removed checkout. Use `git worktree remove` for registered worktrees. A dirty-worktree refusal requires preservation or explicit owner authorization to discard that work; do not force past it automatically.
3. **Delete the listed targets.** Use existing filesystem/Git commands on exact paths. Do not follow symlink targets, expand to neighboring material, create cleanup software or launch a development pipeline. If a command fails, stop that target and report the actual result.
4. **Confirm and report.** Check command status and that removed paths are absent. Briefly record removed paths, kept paths/reasons and errors in the existing Current state. Size measurements are optional. Kept or failed targets remain explicit; they do not block clear targets or completion of the underlying task.

Keep durable evidence and required inputs outside disposable scratch from the start. If existing evidence depends on a temporary path, preserve that target unless the owner authorizes its disposal. Report any resulting evidence limitation; deletion cannot turn a failed or incomplete check into a passing one.

Creating or changing custom deletion logic, reusable cleanup tools or automatic target selection is separate high-risk software development requiring its own authorized scope. This workflow authorizes none of those additions. It supersedes older cleanup-only role, test, review, hash-manifest, dependency-graph and mandatory byte-accounting requirements. Historical incidents and accounting remain facts.
