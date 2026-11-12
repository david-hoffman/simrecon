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

For external protocol observations, the coordinator/operator must prepare the
shared reader-reservation parent from the intended worktree root before any
reservation-using focused tests or full verification:

```sh
export SIMRECON_PROTOCOLS_EVIDENCE=/tmp/simrecon-protocol-observations
mkdir -p artifacts/baseline-compatibility-20261013/A09 &&
  make preflight UV=uv &&
  make verify UV=uv \
    VERIFY_ARGS='--contract TASK-ID --reviewed-tests TEST-REVISION --base BASE-REVISION'
```

Choose an owned absolute observation directory outside the checkout; the `/tmp`
path above is an example. The export carries the same override into preflight,
full verification and any focused checks run in that shell. In the A09 public
caller fixture, `SIMRECON_PROTOCOLS_EVIDENCE` relocates only `RUN` to
`<external-directory>/authored-runs/<RUN_ID>`. The shared lock stays at
`artifacts/baseline-compatibility-20261013/A09/reader-reservation.lock`, and the
reader cache stays at `artifacts/imagej-reader`. With external `RUN`, creating
the observation directory does not create the fixed lock parent. An absent
parent causes `FileNotFoundError` (errno 2) before cache movement. The `mkdir -p`
command prepares only the parent and is safe to repeat when it already exists;
automatic fixture preparation is deferred.

If parent preparation or another prerequisite fails, retain its output/status
and stop dependent checks. An existing `reader-reservation.lock` remains an
exclusive-reservation blocker; preserve it and the cache for diagnosis. Parent
preparation does not authorize removing a lock, recovering a cache or retrying a
failed check. Ordinary locked setup, Python/uv/JDK identity and
[reader prerequisites](imagej-reader-environment.md) still apply. External
observations leave canonical receipts, phase logs and coverage in their
[documented checkout locations](verification.md). A synthetic parent/lifecycle
demonstration or focused pass does not establish full environment qualification
or replace the passing full exact-candidate gate.

Retain failed output/status and classify before repair, independently of task risk. Data-loss behavior (including settled overwrite/truncation repair) remains high risk, even when a failure first appears environmental or conventional. Stop dependent phases on prerequisite failure; retain unaffected results and diagnose before an authorized retry. Diagnose import, cache or network failures in the actual environment; do not adjust tests, dependencies or gates to hide them. Resolve required cache/network access once through authorized setup. No silent retries, unconditional elevation or offline success claims. Rerun affected checks after environment repair; unchanged reviewed tests keep their checkpoint.

Historical macOS hidden editable-install flags and duplicate environments are linked from [setup accounting](../tasks/setup-plan.md) and [environment evidence](../setup/evidence/environment/hidden-pth.json). Their responsible process was not established. Check present identity first; history does not justify rebuilding every worktree.

Use supported bounded waits/deadlines under [role launches](role-launches.md). Timeout is incomplete evidence, not success or automatic retry. Host/wait fallback setup is separately authorized. Full verification remains default local gating; optimizations need measured local need and explicit scope.

Related references: [full verification and receipts](verification.md) and [native role launches](role-launches.md).

The locked development group installs the local editable `simrecon-devtools`
distribution from `devtools/`. It supplies `delivery` and the explicitly loaded
`simrecon_devtools.pytest_policy` plugin, including for temporary caller
directories. Both project manifests and `uv.lock` are installation inputs.
A product-only installation supplies `simrecon`, with no doctor or pytest policy.
