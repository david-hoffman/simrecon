# VERIFICATION-RECEIPT-01: ordinary full-check evidence

**Version 1.0.** This public infrastructure contract implements section 3 of the owner-approved [repository efficiency plan](../plans/agentic-delivery-repo-efficiency-plan.md). It approves no scientific behavior, lighter delivery route, alternate submission gate, or orchestration helper. Approval and allowances live in [the task record](../tasks/delivery-efficiency.md#current-state); A/B receive this contract without that implementation-bearing record or the plan.

## Public entry points

`make check UV=/absolute/path/to/uv` synchronizes the locked environment, then runs exactly the Ruff lint, Ruff formatting and Pyright commands used by full verification. It does not replace `make verify`.

`make verify UV=/absolute/path/to/uv` retains the full current gate. A standard-library helper is callable as:

```text
python3 scripts/verify.py [--uv UV] [--make MAKE] [--receipt PATH]
    [--contract ID] [--reviewed-tests REVISION] [--base REVISION]
    [--input NAME=PATH ...]
```

Defaults are `uv`, `make`, and `artifacts/verification/receipt.json`. The caller's working directory is the repository root. The helper launches one Make target per phase, in this order: `sync`, `coverage-clean`, `lint`, `format`, `types`, `tests`, `coverage-combine`, `coverage-json`, `coverage-html`, `coverage-report`, `wheel`, `wheel-import`, `audit`. It passes the selected uv executable through `UV=...`. The targets retain these commands: locked all-group synchronization; coverage erase/removal of old reports and wheels; Ruff lint and format checks of src/tests/scripts; Pyright; coverage-run pytest; subprocess coverage combine; JSON, HTML and terminal coverage reports; uv wheel build; isolated wheel import; locked audit. No retry, remote role launch, Git mutation, publication, or skipped check is permitted.

Expected command failures stop later phases. The helper preserves output in per-phase ignored logs, forwards it to the caller, and writes an ordinary UTF-8 JSON receipt. A successful helper exits 0. A command failure preserves its nonzero status; missing command exits 127. Evidence validation failures exit 1. Invalid arguments use the ordinary argparse usage error status 2. No failure may yield `result: passed`. Receipts are evidence, not approval certificates. Artifact/receipt output must be outside tracked candidate files and Git metadata, including when a tracked file is missing or identity cannot be fully collected. Protection cannot depend on successfully reading every tracked file.

## Receipt schema and identity

Top-level fields: `schema` = `org.simrecon.verification`, `version` = 1, `result` = `passed` or `failed`, `started_at`, `finished_at`, `context`, `environment`, `before`, `after`, `phases`, `inputs`, `coverage`, `artifact`, `problems`.

Exact nested field names:

- `context`: `contract`, `reviewed_tests`, `integration_base`.
- `environment`: `platform`; `python`, `make`, `uv`, `git` each with `executable` and `version`; `tools` mapping check-tool names to available version strings or null. Python uses the actually running interpreter. Tool names are `ruff`, `pyright`, `coverage`, `pytest`. Resolved executable paths may be absolute; approved input private paths may not appear.
- `before` and `after`: `commit`, `tree`, `dirty` (tracked Boolean), `untracked` (relative-name list), `manifest` (relative tracked-name to SHA-256 mapping). An unavailable identity is null and cannot pass.
- Each `phases` list entry: `name`, `command` (argument list), `returncode`, `started_at`, `finished_at`, `log` (relative path). The target argument identifies the phase, and selected uv is passed as `UV=...`.
- `inputs`: public alias to `before` and `after`, each holding `size_bytes` and `sha256`, or null when unavailable. No `path` field is permitted here.
- `coverage`: `reports` with `json` and `html` relative paths; `files` mapping owned relative filenames to metrics; `global` metrics; `packages` mapping `simrecon` and `scripts` to metrics. Every metrics object has `statements` and `branches`, each with integer `covered` and `total`. Aggregates equal their owned-file sums. Unavailable coverage is null on failure.
- `artifact`: `path` (relative wheel filename), `size_bytes`, `sha256`, `version`; null when unavailable/invalid.
- `problems`: list of diagnostic strings. It is empty only on a passed run. Extra informational fields are allowed; none may weaken validation or disclose private input data.

- Timestamps use UTC ISO 8601. Context contains `contract`, `reviewed_tests`, `integration_base`; omitted labels are null, never guessed approval. A phase has `name`, argument-list `command`, `returncode`, start/end timestamps and a relative log path. An unrun phase is absent; the failed receipt explains incompleteness. All phases must succeed before passing.
- Environment records platform, actual Python executable/version, resolved Make and uv executable paths/versions, Git version, and installed check-tool versions available after synchronization. Unavailable metadata is explicit; it is not invented. No native agent is launched by verification; agent model/effort belongs in its role report.
- Before/after identities contain commit, committed tree, tracked dirty flag, untracked file names and an SHA-256 content manifest of all tracked files. Manifests use repository-relative names, including source, tests/fixtures, lock and check configuration. Passing requires a clean tracked start and equal commit/tree/manifests after all phases. Relevant untracked local inputs must be named explicitly through `--input`; unrelated untracked files are recorded without claiming their contents were tested.
- Approved extra inputs are regular files. Each NAME is a unique nonempty public alias. Record its alias, byte size and SHA-256 before/after without its private path or contents. Invalid inputs or changed fingerprints fail. No ignored study archive or owner data is read implicitly. A receipt is reusable only for the recorded identities/context/environment; this helper neither authorizes reuse nor decides task routing.
- Coverage reads `artifacts/coverage/coverage.json` from this run and requires the HTML report `artifacts/coverage/html/index.html`. Report paths, each owned Python file under `src/simrecon/` and `scripts/`, global and per-package exact covered/total statements and covered/total branches are recorded. Every owned file, including never-imported files, must appear. No missing, excluded or partial item and no incomplete native numerator may pass. Zero branch denominator is reported as 0/0, not fabricated. This measures Coverage.py's native lines/destinations; Make/YAML and dependency internals have no Python coverage claim.
- Artifact contains the sole built wheel's relative name, byte size, SHA-256 and resolved distribution version from its metadata. Ordinary wheel evidence follows the [Python Packaging Authority binary distribution format](https://packaging.python.org/en/latest/specifications/binary-distribution-format/): consistent distribution/version metadata, WHEEL format/tags and a complete RECORD with correct secure member hashes (SHA-256 or stronger) and an unhashed self-entry. This is evidence collection for the current build gate, not a general installer. Missing, ambiguous or invalid wheel evidence fails. This project has a static version; commit/tree and dependency/check manifests remain recorded build inputs.
- `problems` identifies missing/incomplete/changed evidence. Failed runs retain collected identities, logs and any available metrics or valid artifact evidence, including valid partial native counts emitted by a failing coverage JSON phase before HTML runs, and valid same-run wheel evidence emitted by a failing build phase; they cannot reuse stale reports to pass. Phase logs retain only output actually emitted by the check commands. Measurements captured internally by existing tests are not automatically exported into the logs or receipt. Same-run export requires a separately authorized A/B-reviewed test change; this infrastructure task neither needs nor authorizes that existing-test change. Report and defer missing export rather than rerun scientific tests solely to retrieve numbers.

## Contract

| Scenario | Public input/context and observable outcome | Expectation source |
|---|---|---|
| V1 | A clean disposable Git repository, unchanged approved extra input, all required successful phase commands, complete owned-file statement/branch reports and one valid wheel yield exit 0 and a complete passed receipt with exact identities, phase order, metrics and artifact version/digest. `make check` shares only sync/lint/format/type commands. | Approved plan section 3 and existing full gate |
| V2 | A phase command fails, or its executable is unavailable: retain its output/status and failed receipt, stop later phases, and do not retry or mutate Git. | Full gate's existing stop-on-failure behavior |
| V3 | Required coverage JSON/HTML, an owned file, full native measurement, or valid sole wheel is absent/incomplete: full command execution cannot produce a passed receipt. Equivalent malformed report values exercise this evidence obligation. | Full coverage/build gate and plan's missing-report rule |
| V4 | The tracked candidate is dirty before verification or commit/tree/tracked content changes during it: receipt identifies the states and fails despite successful check commands. | Exact-candidate/tree-unchanged requirement |
| V5 | Explicit context labels and approved extra inputs are faithfully recorded; invalid duplicate/unnamed/nonfile inputs or changed file fingerprints fail without copying private paths/data into the receipt. Omitted context stays null. | Plan's input identity/privacy and honest-evidence requirements |

Scenario count is five. No numerical or binary product scenario is added. New helper code is owned runtime, with independently authored public CLI tests, B-reviewed checkpoint before C, and 100% measured supported statements/branches globally and per package. Make command paths receive exercised-command evidence.
