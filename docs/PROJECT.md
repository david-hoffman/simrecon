# SIMrecon project

**Version 1.0** Git versions revisions.

## Purpose and non-goals

Build a pristine Python library for structured illumination microscopy (SIM), using NumPy and SciPy. Scientists should eventually reconstruct images through documented array interfaces with independently justified numerical expectations. The owner approved this architecture and an initial eight-hour delivery setup pass in this conversation on September 30, 2026. Installation began at 18:29:01 UTC (11:29:01 PDT); its hard stop is October 1 at 02:29:01 UTC (September 30 at 19:29:01 PDT).

The owner explicitly permits studying legacy algorithms but requires all new code to be written independently. `SIMrecon_svn/` remains ignored historical study material. Do not copy, ship, link, or import it. This setup pass implements no scientific algorithm, legacy repair, or file-format compatibility feature.

## Constraints and structure

- One monorepo; Python 3.13.12, NumPy and SciPy; isolated `.venv`, exact dependency resolution in `uv.lock`.
- New library under `src/simrecon/`. Delivery helpers are owned runtime and must be measured along with future scientific code.
- `AGENTS.md` is the shared operational home. The four canonical repository skills live in `.agents/skills/`. Codex supports that location, so no native bridge is needed.
- The canonical specification remains `docs/agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md`. Source archives are inert reference material. Routine roles receive narrow packets, not the archive.
- Ordinary Git and GitHub Actions provide versioning and checks. No controller, daemon, scheduled LLM loop, separate control repository, custom GitHub App, or engineered role/file permissions.

## Public interfaces and scientific decisions

No scientific API is approved yet. [Scientific context](SCIENTIFIC-CONTEXT.md) maps the requested papers to algorithms and lists unresolved units, axes, Fourier conventions, scaling, calibration, estimators, tolerances, and malformed-input behavior. Those decisions must enter approved contracts before tests or implementation. Existing source and historical output do not establish intended behavior.

Citation-only Docling conversions are stored in `docs/references/scientific/`; full-paper conversion remains incomplete. This distinction must not be lost in later task packets.

## Adoption baseline and scope

See [the read-only baseline](setup/BASELINE.md). The legacy build fails before product tests at a missing compiler; no automated test target was found. Statement and branch counts and percentages are unknown, not zero or 100%. Historical binaries are stale evidence.

The owner chose a new library rather than repairing/adopting the legacy runtime. That makes legacy compiler recovery and legacy global coverage separate, unapproved work. Every new owned runtime file, including delivery helpers and never-imported files, belongs to the new measurement scope. A tiny scientific slice could not pass a global legacy gate; treating the legacy snapshot as unshipped reference is an explicit adoption-scope decision, not a coverage exclusion for shipped code.

Delivery installation uses the approved eight-hour cap. Product remediation and reconstruction implementation are outside it; their effort is not yet estimated because public behavior and independent fixtures remain unresolved. [The setup plan](tasks/setup-plan.md) records dependencies, the proposed demonstration contract, and remaining decisions.

## Verify and operate

Install the pinned uv version shown in CI, then run `uv sync --locked --all-groups` in an isolated environment. The local setup installation used `/private/tmp/simrecon-uv/bin/uv` version 0.12.19. No legacy setup script was used for discovery. During the first blind test pass, generated editable-install path files repeatedly acquired the macOS hidden flag and Python skipped them. The local environment was rebuilt at `/private/tmp/simrecon-delivery-setup/project-env`, with `.venv` as a symlink. Its interpreter remains the existing CPython 3.13.12 installation. Tests were not changed for that environment repair; the flag-setting process is unknown. CI creates a clean isolated environment on each runner.

Fast generic Git hooks use Ruff from the synchronized `.venv`. Install them with `uv run --locked pre-commit install --hook-type pre-commit --hook-type pre-push`. They provide local lint/format feedback; the full submission gate is the explicit command below. Hooks do not query GitHub or manage PR state.

The canonical full command is `make verify` from the repository root. In this workstation's setup environment use `make verify UV=/private/tmp/simrecon-uv/bin/uv`. It performs locked dependency synchronization, Ruff lint/format checks, Pyright, pytest with coverage, combined subprocess coverage and reports, a wheel build and isolated wheel import, and `uv audit --locked`. CI repeats it on Ubuntu 24.04 and macOS 15. Tooling remains incomplete until the approved helper/tests and rejection of omitted tests are installed; this is not a passing baseline claim.

Coverage reports are `artifacts/coverage/coverage.json` and `artifacts/coverage/html/`. Coverage.py's native statements are executable source lines and its branches are possible line-to-line control-flow destinations. Report those exact integer numerators and denominators. This does not measure every abstract-syntax-tree expression or condition independently. Zero executable scientific code has no meaningful scientific coverage percentage. Require 100% of the native supported statement and branch metrics for all new instrumentable owned runtime; report unsupported measurements explicitly.

An actual fresh native root-session probe succeeded with Codex 0.155.0-alpha.16.4:

```sh
codex exec --ignore-user-config --disable memories --disable multi_agent \
  --sandbox read-only --model gpt-6-sol --json -C /absolute/path/to/simrecon \
  -o /absolute/path/to/role-report.txt - < /absolute/path/to/role-packet.txt
```

Use a new invocation for each role, not `resume` or `fork`. Select `workspace-write` for authorized authoring. Probe success only demonstrates launch availability, not an independent A/B/C/D review. The proposed installed doctor invocation is `uv run --locked delivery doctor [--check]`; it is not implemented yet. Its contract is in the setup plan. Neither command creates a controller.

No merge or release without explicit owner action. Check failures are classified and routed under `AGENTS.md`; do not adjust thresholds to make a result pass. GitHub protection configuration and its verification evidence are recorded with the setup task.

## Approval and next slice

Architecture and eight-hour installation approval: owner's message, “I Approve this Python architecture and an initial eight-hour setup pass?” Repository setting authorization: subsequent message, “Can you configure the github repo correctly as well?” These approve setup and settings, not scientific behavior or an as-yet-unapproved task contract. The owner subsequently instructed completion of architecture and the initial setup pass. The unchanged demonstration cases are now two sequential default-size slices in [the plan](tasks/setup-plan.md); no larger-slice exception or scientific behavior was approved.
