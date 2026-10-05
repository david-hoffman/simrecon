# SIMrecon project

**Version 1.0.** Git versions revisions.

## Approved architecture and boundaries

SIMrecon is a pristine functional Python/NumPy library for structured illumination microscopy (SIM). The owner approved the functional architecture and first MRC conversion contract on October 1, 2026, then two bounded amendments. [Approval and historical execution accounting](tasks/architecture-intake.md#current-state) identify the accepted revisions. Architecture approval does not approve additional scientific scenarios.

The [public conversion contract](contracts/mrc-conversion-v1.md) defines `inspect`, selected-block `read`, pure metadata/layout `harmonize`, streamed `write`, records/errors and the `simrecon` command-line interface. Explicit acquisition configuration controls interpretation. Modern MRC output preserves pixel bits, original metadata and override provenance in embedded HDF5 metadata. Conversion performs no reconstruction or scientific image correction. Initial compatibility is pinned mrcfile 1.5.4; ImageJ integration is deferred.

[Library boundaries](architecture/library-design.md) and [data flow](architecture/data-flow.md) give architecture context. The separately requested [reconstruction placeholder](tasks/reconstruction-placeholder.md) has no approved execution allowance or completed implementation. New estimators, defaults, adapters, calibration, viewer integration and performance promises need separate contracts. [Scientific context](SCIENTIFIC-CONTEXT.md) and the [migration roadmap](MIGRATION-ROADMAP.md) identify unresolved work. Citation-only paper conversions are available; full-paper extraction remains incomplete.

The owner permits studying legacy algorithms but requires independently written code. `SIMrecon_svn/` remains ignored, unshipped reference material. Do not copy, ship, link or import it. The [adoption baseline](setup/BASELINE.md) records historical compiler/test-discovery limitations, not current product verification.

## Stack and structure

- Python 3.13.12, uv 0.12.19, locked `uv.lock`, one isolated `.venv` per worktree. NumPy/SciPy form the numerical stack; h5py 3.16.0 is runtime and mrcfile 1.5.4 a development reference.
- Owned library/runtime code lives in `src/simrecon/`; owned verification tools live in `scripts/`. Native statement/branch measurement includes both, never-imported files and relevant subprocesses.
- Root [AGENTS.md](../AGENTS.md) holds shared operating rules; four `.agents/skills/` procedures hold role differences; the [delivery specification](agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md) defines policy. Root [LESSONS/](../LESSONS/README.md) remains the single append-only lesson home.
- Git and GitHub Actions provide ordinary checks. Prompted role/file restrictions are not engineered access controls. No controller, daemon or scheduled model loop is installed.

## Commands and evidence

From a worktree root, synchronize with `uv sync --locked --all-groups`. This workstation uses `/Users/davidhoffman/.local/bin/uv`; CI installs the pinned uv/Python versions. [Environment setup](operations/environment.md) separates present checks from historical incidents.

```sh
make check UV=/Users/davidhoffman/.local/bin/uv
make verify UV=/Users/davidhoffman/.local/bin/uv
```

`make check` runs locked sync, Ruff lint/format and Pyright through shared full-check targets. `make verify` remains the canonical full gate: those checks, pytest under statement/branch and subprocess coverage, all coverage reports, wheel build, isolated wheel import and locked vulnerability audit. Test policy rejects empty discovery, skips, expected failures and unexpected passes. CI repeats the full suite independently on Ubuntu 24.04 and macOS 15. Default submission mode is full-local exact-candidate verification; any known failure or incomplete coverage blocks submission. The conditional alternative in specification section 6 is not enabled. Eligibility needs separately evaluated effective native protections/trusted complete CI/head-base/artifact-version proof; high risk and changes to that proof remain excluded. A legacy protection-endpoint absence alone does not establish that native rulesets are absent.

[Verification evidence](operations/verification.md) describes ignored phase logs and receipt/input identities. Coverage JSON/HTML live in `artifacts/coverage/`, receipts/logs in `artifacts/verification/`, wheels in `dist/`. Prepare the task pointer before verification. Record the final commit/command/environment/results outside that commit's tracked tree and confirm it stays unchanged.

Coverage.py measures executable source lines and possible line-to-line branch destinations. Require 100% of native metrics globally/per owned package; report exact covered/total integers and unsupported measurements. Make, YAML, native dependency internals and model behavior have no owned-Python coverage claim. Their command paths require actual exercised evidence.

Install fast generic Ruff hooks with `uv run --locked pre-commit install --hook-type pre-commit --hook-type pre-push`. NumPy-style docstring lint applies to runtime; tests/fixtures may omit function/method docstrings. Hooks give local feedback and never replace full verification. [Lint scope](tasks/numpy-docstring-lint.md) records its setup.

## Role entry points

Coordinators select the impact/uncertainty route in the approved contract: mechanical worker; explicitly scoped bounded worker plus fresh reviewer; or blind A/B, restricted C and fresh D for high risk. Data-loss behavior, including settled overwrite/truncation repair, is high risk and excluded from bounded work. Policy adoption has a separate approved documentation scope and fresh independent policy review before activation. Use [native role launches](operations/role-launches.md), [public A/B packets](agentic-software-delivery-v1.0/templates/PUBLIC-PACKET.md), [worker/reviewer candidate packets](agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md) and [handoffs](agentic-software-delivery-v1.0/templates/HANDOFF.md). [Model selection and calibration](operations/model-selection.md) records conservative defaults, the qualified mechanical scope and unqualified lower-cost/effort candidates, with measured calibration limits. Launched roles perform their role directly without nested launches. Initial high-risk roles and required reviewers are fresh; unexposed A and C may continue their own approved corrections. Reviewers never inherit author history, and exposure cannot be cured by context reset. A/B follow an explicit public-input allowlist; they do not follow implementation-bearing task/plan/history/lesson links.

Installed doctor commands are `uv run --locked delivery doctor --check` (report only) and `uv run --locked delivery doctor` (bounded documentation patch within identified approval and fresh independent policy review before activation). [Doctor scope](tasks/setup-doctor.md) and the [procedure](agentic-software-delivery-v1.0/DOCTOR-PROMPT.md) remain binding. No merge/release follows from checks; owner action is required.

Historical deadlines, interviews, environment flags and native launch changes remain in [setup accounting](tasks/setup-plan.md), [architecture intake](tasks/architecture-intake.md) and linked evidence. Completed allowances do not renew under this cleanup. Current work uses its own approved contract and one Current state with route/gate, evidence-validity inputs, complete metrics or unknowns, and conserved allowances. Owner-authorized new rollout slices/pilots may adopt the synchronized policy after independent review; historical completed receipt work remains charged. [Repo rollout plan](plans/agentic-delivery-repo-efficiency-plan.md) and [generic policy plan](plans/agentic-delivery-spec-efficiency-plan.md) retain historical evidence and link rollout accounting. Profile local phases before any optional cache/shard/launcher change; none is a prerequisite without demonstrated need.
