# Fixed invocation and field templates — NOT EXECUTED / NOT RELEASED

Every command and direct call below is documentation only. No grant, case record,
output directory, or invocation was created/executed. ROOT must select the exact
finite invocation, supply its actual grant/setup, and obtain affected review.
The separately versioned driver SHA256 is
`65b41d34c5a740548a2156ff5bafb20230aab78418eb556d23ab04df24b58cae`.

Fixed driver:
`/workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py`.
Fixed active method imports:
`/workspace/work/campaign/evidence/117/resource-method-source`.
ROOT's authorized metadata input is
`ROOT-actual-two-root-material-import-preflight-1.json`, SHA256
`b630eaceb7efc504a4d1a0f61a08d7c85ca42806c4bc03ae3d788dc31d48f2fd`.
It supplies the interpreter/helper/lock/import premises below; this author did not
repeat its imports, material collection, or environment observations. Its resource
values are not reused as an admission or thresholds.

## Nonexecuted Q0 command templates

Parent working directory: `/workspace/work/issue-116`.
Parent expected HEAD: `158776ade28079276304d49a6b973eccbf4109c9`.
Candidate working directory: `/workspace/work/issue-117`.
Candidate expected HEAD: `e6945817850cfdaa3ebbfe21e7a23784964208d6`.
The caller must use the declared working directory; the driver does not silently
change cwd. Each new stdlib target inherits that caller cwd.

```sh
/usr/bin/env -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS PYTHONPATH=/workspace/work/issue-116/src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 /workspace/work/issue-116/.venv/bin/python -B /workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py --revision parent --case Q0-context --attempt-id rb117-parent-q0-a1-PENDING --grant /PENDING_ROOT_GRANTED/rb117-parent-q0-a1.json

/usr/bin/env -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS PYTHONPATH=/workspace/work/issue-117/src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 /workspace/work/issue-117/.venv/bin/python -B /workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py --revision candidate --case Q0-context --attempt-id rb117-candidate-q0-a1-PENDING --grant /PENDING_ROOT_GRANTED/rb117-candidate-q0-a1.json
```

These exact attempt ids are placeholders containing PENDING, not releases.
The output templates are respectively
`/workspace/work/campaign/evidence/117/resource-method-qualification-source/qualification-parent/rb117-parent-q0-a1-PENDING`
and
`/workspace/work/campaign/evidence/117/resource-method-qualification-source/qualification-candidate/rb117-candidate-q0-a1-PENDING`.
Neither directory exists as a result of this authoring. Safe-id validation and
`mkdir(exist_ok=False)` remain in the driver; output ownership/canonical resolution
and absence of aliases are ROOT setup premises, not an engineered sandbox.

Q1 is a separate future invocation using the same revision/interpreter/environment
and all15 source-map entries, changing only `--case Q1-normal`, a separately
released fresh attempt id and exact grant. It requires one actual passed Q0
receipt for that same revision, same source map and exposed domain. Its
`prerequisites` key must be exactly `Q0-context` and identify that receipt's
actual path/hash. No existing historical Q0 is claimed to satisfy this.

## Exact source-map template

For both revisions the following full15-key `source_sha256` map can be supplied
to Q0 and retained unchanged for Q1. These hashes identify source bytes, not a
qualification verdict. The three root-relative keys resolve only through the
selected literal ROOT. The other twelve keys resolve through their literal
fixed paths. Old report-relative method aliases are not accepted grant keys.

```json
{
  "uv.lock": "222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b",
  "tests/reconstruction_summary_fixture.py": "271335a5065791a986de239cdf89e4d15eb0f2e5df80943d6cb084167516d20f",
  "tests/reconstruction_memory_benchmark.py": "929106da36b47bcd03ed785d1a7f6b941d04299403b6c0ffe7df9846f3809b8f",
  "external_method:/workspace/work/campaign/evidence/117/resource-method-source/observer.py": "eacf24b70cd67f12e403906cf92bb7cb1bb1a7632645335a8b8f3bfbc4225745",
  "external_method:/workspace/work/campaign/evidence/117/resource-method-source/run_attempt.py": "6f34617bb59c060eeceeeb6a06a6180755448f3310481202f96df5e5dd1fe14f",
  "external_method:/workspace/work/campaign/evidence/117/resource-method-source/workload_child.py": "5249e4cdadbee6523012127468fd9c3d90228df2558c81087929bc35e60e5459",
  "external_method:/workspace/work/campaign/evidence/117/resource-method-source/manifest.json": "1854f8760dd9ede607b2611f2d9640e1e3a7056e054ae564211fdea90ef7d4ed",
  "external_method:/workspace/work/campaign/evidence/117/resource-method-source/method_qualification.py": "56c1dafe3c6bdab3b9e9e6fdefc1dc01d419b09e6f6f09bc8b302073474f2a21",
  "external_qualifier:/workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py": "65b41d34c5a740548a2156ff5bafb20230aab78418eb556d23ab04df24b58cae",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/inventory.json": "a9991bb1468e9ea45164e6a263068cf3ac7c4a0af3267bddd5b860ed81e2106e",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/fixtures/stdlib-child.txt": "35024379416bb5e509568dad073feaab8ac6b58caaf968dc52e96162e8e3df5d",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt": "d9262207e14a7bee185a0c6accb641f8ebb0e4f3ceb257bddcdc0d52d9d6b32b",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/fixtures/parser-vectors-v1.json": "f2f14d334965e7c68baa913e30f5ce032740b87d6bffa5ddaf04c60a3e4197ed",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/fixtures/tiny-hash-vectors-v1.json": "38f32d39f93e15ecdcbb8528914e9190c3af626390b661e2962d0e4b9ee58750",
  "readonly_control:/workspace/work/issue-117/docs/reports/reconstruction-working-set/qualification/fixtures/method6-rss-controls-v1.json": "b588cb166337507737dd2b6ed147eb4f43ec865201409604616199af32a435c0"
}
```

This is a control-driver source map, not the runner's science material map.
The unchanged active observer/runner additionally hash all selected-root product
Python sources for actual workload attempts. No product-source body is imported
or newly enumerated by this qualifier binding. ROOT's actual preflight metadata
records both workload material maps, commits, trees, import origins and versions.

Q0/Q1 grant field template: existing `approved=true`, exact
`scope="WS116-Q0-Q1-method5-v1"`, `case`, `attempt_id`, selected `candidate_head`,
`python_resolved="/workspace/.simrecon-tools/python/cpython-3.13.12-linux-x86_64-gnu/bin/python3.13"`,
and the source map above. Q0 `prerequisites={}`; Q1 has the one actual matching Q0
receipt. Preserve all existing required `campaign_ownership_resolved`, `bounds`,
thread/signal/bootstrap, exposed-domain/time/correspondence/headroom/ancestor
fields and failure checks. ROOT must establish actual adequacy of those fixed
control bounds; no inventory value or historical receipt supplies a new admission.
The before/after `source_identities` maps must equal this actual frozen map;
preserve all failures. No complete grant is fabricated here.

## Held existing cases and pure restriction template

Q2 four lifecycle cases, Q4-parser and Q5-tinyhash remain held in generic dispatch:
they call `retained_q1`, which still requires original whole observer/runner/
manifest/source identities to equal truthful current identities. Those identities
changed. Q1 primary receipt/payload bodies are not supplied for this author route.
Q4/Q5 also retain the original strict Q2/Q4 equality dependencies. Do not invoke
these cases expecting an old whole-source pass, rewrite old hashes, or suppress
these requirements.

Pure `method6-rss-controls` likewise retains `method6_prior_scope`: exact named
four runner-function equality and historical unchanged-input equality remain
required. The latter includes old observer/manifest inputs that differ from
current active bytes. Missing authorized Q1 primary bodies are an additional
hold. The68 already retained synthetic outcomes are not scheduled to rerun.
If independently routed later, its command restriction is exactly:

```sh
/workspace/work/issue-116/.venv/bin/python -I -S -B /workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py --revision parent --case method6-rss-controls --attempt-id rb117-parent-m6-a1-HELD --grant /PENDING_ROOT_GRANTED/rb117-parent-m6-a1.json

/workspace/work/issue-117/.venv/bin/python -I -S -B /workspace/work/campaign/evidence/117/resource-method-qualification-source/method_qualification.py --revision candidate --case method6-rss-controls --attempt-id rb117-candidate-m6-a1-HELD --grant /PENDING_ROOT_GRANTED/rb117-candidate-m6-a1.json
```

Those are HELD templates, not a presently satisfiable release. Original pure
effect-denial, isolated/no-site/no-bytecode, no scientific imports, exact input
cardinality and before/after identities remain. Cardinality is now15 because
the active preserved qualifier and this own separately versioned driver are both
distinct required inputs. If ever routed, `legacy_runner_source` must name only
`/workspace/work/campaign/evidence/116/source-method5-review5/docs/reports/reconstruction-working-set/run_attempt.py`
with SHA256 `1e554fdadffdfc54cbc14758e072224db5cd278f1e7b7e91b813c11c65b5fd61`.
No permission to change an unchanged-function or retained-source predicate follows.

## Minimum bounded guard invocation requests — no new case bodies

Static exact enforcement and existing literal binding may discharge these
obligations. ROOT should select only genuinely necessary invocations and freeze
their finite argument/data variations before release. These are requests to call
existing interfaces, not new implemented test cases/frameworks or source patches.

| Existing interface | Exact bounded request / expected enforcement |
| --- | --- |
| This driver CLI | Omit `--revision`, then use `--revision invalid`: argparse refusal before output/import/target dispatch. Use `--revision parent --case Q0-context --attempt-id bad/id` with a PENDING grant path: safe-id refusal before output. Candidate equivalent uses the same unchanged validation. |
| This driver fixed outputs | The same safe attempt id maps to separate parent/candidate roots. Existing-directory retry must fail `exist_ok=False`; only use an actual previously ROOT-released output for a future duplicate refusal, never create historical input or mutate a frozen source to manufacture it. |
| Active observer `material_hashes` | Direct existing calls with literal `Path("/workspace/work/issue-116")` and `Path("/workspace/work/issue-117")` must identify the same5 external keys and the corresponding actual product/helper/lock keys. `Path("/workspace")` is refused by the existing fixed-root predicate. Actual positive maps/imports are already in ROOT metadata b630…f2fd; do not repeat without changed material. |
| Active runner `admit(grant, root)` | Fixed-root direct calls only. With an exact ROOT-authored finite grant variation, wrong candidate/material map is refused before launch; no call to `main` or workflow follows. Matching map acceptance still requires every existing actual safety setting and is not established by this template. |
| Active runner `admit(grant, root)` declaration guards | Literal four initial rows/ten groups/reps and separate256 map are already statically inspectable. If ROOT needs direct refusal observations, select only necessary exact variations: profile2D, non-bool profile, repetition outside1/2/3, supplied/old2d id, altered/192 growth row, absent separate256 admission, absent smaller evidence. Existing ValueError/undeclared-condition refusal is expected. No256 allocation or new fixture/recipe is authorized. |
| Active parser/completeness | Existing matching-map checks and the separately retained helper outcomes remain source proof. Any genuinely uncovered changed-map direct call needs a precisely frozen existing finite record/argument declaration first; no new caller body or oracle was added to this clone. |

Relocated method and noncanonical source/root path predicates are present in the
frozen source. Do not relocate files or alter roots to produce a negative runtime
case. If a finite direct invocation cannot be expressed with the existing
interfaces and immutable inputs, return its exact missing caller/data scope to
ROOT before writing a new guard body. No ad hoc ROOT monkeypatch is proposed.

Actual integration remains exactly four later ROOT-granted one-call observations
through the active `run_attempt.py`: parent/candidate × rb117-2d-search-full and
rb117-2d-search-summary, profile false. They provide the actual PID/exec/wait/FD/
cleanup, retention/finite/value/schema/native-unit records together. They are
outside this qualifier, not a new workflow here. Preserve actual row identities
for any later compatible reuse, with no duplicate workflows merely for tables.
Core24/total60 remain proposed scope, native256 separate new admission remains
pending, and full gate/D/scientific/resource acceptance remain separate.
