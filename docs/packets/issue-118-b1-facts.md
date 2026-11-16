# PH118 B1 — factual command evidence

This contains identities and observed diagnostics only, not an author/coordinator
test-adequacy verdict. B independently derives approved meaning and oracles.

Scientific runtime/public baseline was64a752b4642709c539df2079cc3c906acf4cc7b8;
the local documentation/test checkpoint was32d9c9651f9ca884cbec31793cb80d47571e0645,
treeee654eec7598c3d3fe8702aca73cd6ecffa467a1, with the owned test uncommitted
during the commands below. The launch message supplies the later frozen commit/
tree. Runtime/dependency/shared-fixture bytes were unchanged by this task.
Actual final integration-parent qualification is pending; no later profile or
shared-helper branch is assumed qualified by this provisional public baseline.

Final test SHA256:
`ce63d3b83ba5257d821cf71076a42a745fc636ae8b40450c26527f15a61ac3ca`.
PH118 contract SHA256:
`d217c186ae2e736fb6fbfe29a432b84d5e34e6490679a422835253742bbcf3e5`.
Whole approved input identities are in `issue-118-b1-inputs.sha256`.

All commands used this exact prefix, the existing issue118 .venv and no install:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-118 -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin simrecon-campaign-ubuntu
```

After that prefix, final owned-byte commands were:

- `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py`: exit0.
- `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py`: exit0.
- `uv run --locked --no-sync pyright tests/test_preparation_harmonic_lifetimes.py`: exit0,0errors/0warnings.
- `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_preparation_harmonic_lifetimes.py`: exit0,27passed in11.72s.
- Same source-free targeted corrected factorization row: exit0,1passed in.49s
  (a repeated member of the27, not an additional distinct case).

Observed environment in pytest: Linux/Python3.13.12, pytest9.1.1, pluggy1.6.0,
platformdirs4.12.2 and xdist3.8.0 installed plugin; no worker option selected.
Runtime backend-site/allocator/profile/resource qualification was not inferred.

Same `uv run --locked --no-sync python scripts/source_free_check.py pytest` command
also ran these selected keeper groups, all exit0:

| Group | Exact test arguments | Observed result |
| --- | --- | --- |
| A | `tests/test_c_workflow_numerical.py::test_complete_actual_workflow_against_raw_finite_observer[between-first-off-and-persistent-sentinel]` |1passed,2.18s |
| B | acquisition boundary structural-unsafe, fixed10-small, prepass-off-limit and exact-Y-plus-one positive nodes; workflow recognized-unsafe and representation-small-backing nodes, exact command in log22 |21passed,1.13s |
| C | `tests/test_c_acquisition_filter.py` |49passed,38.60s |
| D | summary full-scientific/projection-matrix, external-failure, discarded-regression-finite and inherited-unsafe nodes, exact command in log24 |34passed,101.01s |

The test-owned diagnostic labels in the final27-case log identify actual
interception with calls1 in all9 direct controls: CE02 allocation/interruption/
factorization; CE06 and CE04 allocation/interruption/FFT. They do not locate an
internal operation or prove all provider bindings. The test's legitimate
no-interception positive branch was not taken by those9 rows in this run.
Inherited summary fault rows did not print their conditional branch, so their
pass count alone does not identify which hooks intercepted.

Earlier exact inputs/statuses are preserved separately. Two initial long-line
findings and formatting failures were repaired; later diagnostic/fixed-matrix
format failures were repaired. An earlier owned run reported26pass/1fail and
the targeted row observed injected generic FFT RuntimeError for CE02 where that
old test asserted SimreconError. The current row selects factorization instead.
Public CE02 names factorization/nonfinite-operation errors, MemoryError and
interruption; CE04/CE06 state their own broader backend/allocation rules. Review
these primary contracts independently. The earlier failed test bytes are an
explicit allowed test artifact; no runtime implementation or diagnosis is supplied.
No tolerance was changed between the supplied revisions. No source exposure or
unsupported diagnostic channel was reported; all24 logs/failed input remain
retained outside the narrowed B input set. Check times are not speed claims.

Cumulative attempts supplied for accounting: intake1; A launches3 (A1/A2 stopped
on procedural/pointer overreads before authoring, with no actual product/source/
history/task-state/coverage/lesson record exposure reported); same A3 static and
focused continuations plus one CE02 test correction. B1 is the first independent
test review; prior accepted checkpoint NONE. All unknown tokens/cache/serving/
money/total durations remain unknown. No numeric human cap is set. No resource
benchmark, full verification, implementation or final review is claimed here.
