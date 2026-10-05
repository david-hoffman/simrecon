# Worktree environment

Use one task per worktree. Check `git status --short` and `git rev-parse HEAD` against the approved baseline. Resolve the actual uv/native executable, interpreter/platform and dependency-lock identity before expensive dependent roles/checks. Record applicable installation/import health and isolated/nested environment creation where required. A known environment path is not perpetual evidence; reuse only for unchanged inputs and present health. Reviewer authentication/connectivity is probed only when independent review is required and valid capability evidence is missing/stale; reuse an observed valid launch or the smallest necessary probe, not a redundant review session. Charge preflight/failures to the approved budget; probes are no verdict. Do not share another worktree's `.venv`.

```sh
/Users/davidhoffman/.local/bin/uv --version
/Users/davidhoffman/.local/bin/uv sync --locked --all-groups
.venv/bin/python --version
.venv/bin/python -c "import simrecon; print(simrecon.__file__)"
```

Pinned setup is uv 0.12.19 and CPython 3.13.12. CI installs them from `.github/workflows/verify.yml` and `.python-version`. The delivery-efficiency preparation observed Codex 0.160.0 at `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. Record current executable/version for future launches; an observation is not a permanent capability claim.

Run the cheap prerequisites before dependent checks:

```sh
make preflight UV=/Users/davidhoffman/.local/bin/uv
```

Preflight runs the existing locked all-groups sync first. It reports the uv executable/version, actual Python executable/version/platform and environment prefix, and installed versions/distribution roots/import paths for simrecon, NumPy and h5py. It requires Python 3.13.12, this worktree's `.venv` and simrecon imported from this worktree's `src/simrecon`. The health command uses `--no-sync` to avoid repeating the sync. Finally, the existing uv `run --no-project --with` form imports hatchling 1.32.4 and reports its interpreter, environment and import identity outside the worktree `.venv`. A failed sync, health check or isolated build-dependency check retains diagnostics and stops later commands without retrying. Preflight is a prerequisite check; `make check`, `make verify` and all full verification phases remain unchanged.

Retain failed output/status and classify before repair, independently of task risk. Data-loss behavior (including settled overwrite/truncation repair) remains high risk, even when a failure first appears environmental or conventional. Stop dependent phases on prerequisite failure; retain unaffected results and diagnose before an authorized retry. Diagnose import, cache or network failures in the actual environment; do not adjust tests, dependencies or gates to hide them. Resolve required cache/network access once through authorized setup. No silent retries, unconditional elevation or offline success claims. Rerun affected checks after environment repair; unchanged reviewed tests keep their checkpoint.

Historical macOS hidden editable-install flags and duplicate environments are linked from [setup accounting](../tasks/setup-plan.md) and [environment evidence](../setup/evidence/environment/hidden-pth.json). Their responsible process was not established. Check present identity first; history does not justify rebuilding every worktree.

Use supported bounded waits/deadlines under [role launches](role-launches.md). Timeout is incomplete evidence, not success or automatic retry. Host/wait fallback setup is separately authorized. Full verification remains default local gating; optimizations need measured local need and explicit scope.

Related references: [full verification and receipts](verification.md) and [native role launches](role-launches.md).
