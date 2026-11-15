# Issue 115 sanitized prior evidence and integrated checkpoint mapping

This file contains public test/requirement/evidence identities only. It conveys
no prior reviewer's substantive oracle conclusion. Historical test checkpoint:
9a423fd608ecf6cdb203283674522b8b88b9e080 on actual A/B base
b344e41a8b52de76d7cbbf8450319893904c3b8f. Current integrated test candidate:
290a4e6a834a3de56f7f49b40939e20be159c7cd, tree
9aa7945f5915ce81896ee001352d6eea761b3535, on frozen parent
d9a0ba924817772fdb5550c7d055bf31bcf70388/tree
836abd6603e28ea69c611429443c0684ba2f8441. Root performed integration; branch
feat/115-wide-allocation-domain. Prior original ancestry remains preserved.

All 99 entries in historical tests-checkpoint.sha256 still match current bytes.
Integrated tests-integrated-checkpoint.sha256 adds only inherited
 tests/test_dev_environment.py (SHA256
9900cff002ca5f17a8aec06a4c793e5086b7ddf59b35112b04dee79993e91f2e),
for 100 files. Root/coordinator report inherited scientific src, scientific test
fixtures, AGENTS/PROJECT/Makefile/lock/dependencies unchanged. Parent introduces
setup/recovery script/test/docs and precision proposal docs, with no active
precision API/default change. Assess the added setup test and unchanged scientific
inputs independently through permitted text; do not inspect implementation.
The integration is not a new behavioral run or a scientific gate result.

Exact six authored test digests are unchanged:

| File | Final SHA256 |
|---|---|
| tests/test_wide_allocation_domain.py | 016c47bcbdff42b41c90b01a1c2f07af459c09574b0f127b1655e8c327d84360 |
| tests/wide_allocation_fixture.py | 09c7ac15b02226f986b17f12a244056654b1166b5accbd2c4407a5f7cb3e94c8 |
| tests/test_c_known_boundary.py | 1125ff758f2cade00fd007c6dbdb54b31eef4e93cf4f109a97292526e4efd6b9 |
| tests/test_c_acquisition_boundary.py | 590d03ac6370b73294af1783f8e55eed1ffd932a1e50d2b80c7b8a56053b56b0 |
| tests/test_c_workflow_validation.py | 0ae4005badef392502e310df1cd8bd8b7f47aa06cd9550d1a8b1194969e50052 |
| tests/test_reconstruction_summary.py | aa9d4d23fd3a5efa421d682366bde8c97a971e823dad696f411d81dbd67a00c8 |

Historical source-free focused pytest used the first four pre-format digests
recorded in behavior-retention-evidence.md plus identical workflow/summary bytes.
It ran the five test modules above (fixture omitted), collected 1118, exited 1:
1099 passed / 19 failed / 16 warnings in 128.26 s. The 19 observed failures were obsolete
output/lookup byte rejections: output-byte neighbors 5, lookup crossings 2,
admitted signed-volume endpoint 1, target metadata 1, wide direct routes 4,
acquisition pitch complement 1, inherited known 2, acquisition witness 1,
workflow witness 1, summary delegate 1. These are reported historical outcomes;
B must independently assess valid oracles and product-red classification.

Subsequent cosmetic preparation changed I to SIGNED_MAX (binding value remains
2**31-1), import ordering and decorator/signature whitespace. Complete exact
old→prepared diff and reconstruction/hash evidence are separately allowlisted.
Coordinator reconstructed the initial text matching all pre-existing recorded
SHA256 values; it is not an originally archived file or invented timestamp.
No assertion/formula/parameter/tolerance/call/observer/discovery change is claimed;
B must decide from the complete delta. No final-file behavioral rerun occurred.
Final exact-six-file Ruff/format/canonical uv-run source-free Pyright each exited0.
Initial quality failures and two cosmetic rounds remain historical charges.

The focused command used the pinned Ubuntu container prefix with worktree cwd,
then .venv/bin/python scripts/source_free_check.py --timeout 300 pytest and the
five named modules. Narrow final quality commands used uv run --locked ruff
check/ruff format --check on the six files, and uv run --locked python
scripts/source_free_check.py --timeout 300 python -m pyright on the six files.
The first raw-Python Pyright invocation could not resolve environment imports;
correct project uv-run selection resolved it without package/config edits.

Warnings retained source-free category/message/location. Four identical fixed
native lines appeared after pytest:

```text
 ** On entry to DLASCL parameter number  4 had an illegal value
```

A conservatively stopped, then root explicitly permitted this exact fixed
source-free diagnostic only (no source snippets/locals observed), preserving
all four lines and the stop. Its originating test/calculation is unproven.
No blanket native renderer/harness waiver; assess oracle relevance independently.
No target volume allocation or reconstruction resource benchmark was run.

Public obligation preservation to audit: known L6000/L8192 obsolete rejection
rows replaced by wide arithmetic plus safe invalid-Wiener public cases;
acquisition complex-workspace rejection replaced by metadata admission plus
invalid pitch, while signed-count rows remain; workflow unsigned witness now
metadata admission plus config rejection and summary delegate follows it.
Fractional/nonexact zoom, real signed native/padded/half/output/frame/phase/order
limits, actual unsafe stencils and independent small positives remain required.
Integer-only validators complement public ordering/route cases; they do not
prove real production use, which C/D must inspect. New tests cannot request a
huge successful numerical operation or deliberately OOM.

Cumulative prior charges: intake 1, A1 plus continuation 1, completed prior B1
review 1, C 0 / D 0. Semantic test corrections 0, cosmetic rounds 2, environment/tool
invocation diagnosis 1, conservative diagnostic stop 1, missing-evidence request 1
resolved without test change, source exposure 0. A 10 check commands, five nonzero
statuses including intended product-red. B2 is a new fresh session/review, not
reuse of a sibling verdict. Actual human numeric limits not set; missing served
model/tokens/costs/overall elapsed unknown. Do not relabel historical results as
an integrated full gate. Parent CI status/PR publication proves no #115 result.
