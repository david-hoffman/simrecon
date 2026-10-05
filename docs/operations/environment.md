# Worktree environment

Use one task per worktree. Check `git status --short` and `git rev-parse HEAD` against the approved baseline. Resolve the actual uv/native executable before expensive roles or checks. Do not share another worktree's `.venv`.

```sh
/Users/davidhoffman/.local/bin/uv --version
/Users/davidhoffman/.local/bin/uv sync --locked --all-groups
.venv/bin/python --version
.venv/bin/python -c "import simrecon; print(simrecon.__file__)"
```

Pinned setup is uv 0.12.19 and CPython 3.13.12. CI installs them from `.github/workflows/verify.yml` and `.python-version`. The delivery-efficiency preparation observed Codex 0.160.0 at `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. Record current executable/version for future launches; an observation is not a permanent capability claim.

Retain failed output/status and classify before repair. Diagnose import, cache or network failures in the actual environment; do not adjust tests, dependencies or gates to hide them. Resolve required cache/network access once through authorized setup. No silent retries, unconditional elevation or offline success claims. Rerun affected checks after environment repair; unchanged reviewed tests keep their checkpoint.

Historical macOS hidden editable-install flags and duplicate environments are linked from [setup accounting](../tasks/setup-plan.md) and [environment evidence](../setup/evidence/environment/hidden-pth.json). Their responsible process was not established. Check present identity first; history does not justify rebuilding every worktree.
