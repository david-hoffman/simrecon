# SP113 — proposed bounded source-free checks, no grant

This coordinator proposal is not an execution authorization. Root must grant the
specific shared-resource window after A1 continuation returns exact file/method/
fixture hashes; freeze those inputs in outside evidence before running. Any later
change renews affected evidence. No install/sync, full gate, memory benchmark,
large success, installed-wheel/build/checker execution or116 trial is proposed.

## Selected existing environment and commands

Use only root's prepared Ubuntu24.04.5 container/per-worktree .venv, locked
Python3.13.12/uv0.12.19/NumPy2.5.3/SciPy1.18.1, with applicable existing preflight
inputs checked. Prefix every command with:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-113 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  -e BLIS_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 \
  simrecon-campaign-ubuntu
```

F is the explicit eight-file Python scope below; actual executed argv expands
all eight names, never a directory/glob or shell variable supplied by a role:

```text
tests/single_known_fixture.py
tests/test_single_known_boundary.py
tests/test_single_known_filter.py
tests/test_single_known_assembly.py
tests/test_single_known_precision.py
tests/test_single_known_typing.py
tests/test_module_migration.py
tests/test_installed_wheels.py
```

Sequential phases, no overlap with root exclusive studies:

1. Source-free syntax via standard-library ast.parse over F, named filenames;
   no import or execution of test/product code. Use locked uv-run --no-sync and
   `python scripts/source_free_check.py --timeout 300 python -c` with a frozen
   one-off payload reading only F and printing parse count/status. No compileall
   output channel or general source scan.
2. `uv run --locked --no-sync python scripts/source_free_check.py --timeout 300 python -m ruff check --output-format concise F`.
3. Same prefix/renderer, `python -m ruff format --check F`. If purely author
   formatting fails, A may format only F under the actual grant, then rerun
   changed owned checks; preserve failed attempt and exact cosmetic diff for B.
4. Same prefix/renderer, `python -m pyright --outputjson F`. Public type/caller
   proof remains; no stubs, ignored API errors, gate edits or weak typing to hide
   unimplemented features. Diagnose author harness versus feature absence.
5. Same prefix/renderer pytest, `-q` on the five new test files plus
   tests/test_module_migration.py only, with strict default outcomes retained.
   Collection must not be stopped by avoidable harness import/typing design.
   Classify genuine feature absence separately from a valid scientific red;
   no C implementation exists yet. Freeze exact selectors/file hashes after
   continuation rather than silently treating changed inputs as the same run.

Do NOT include tests/test_installed_wheels.py in runtime pytest selection:
its read/quality ownership does not grant build/install/isolated subprocess
execution. No broader original suite or installed type/wheel test. Owned literal
public typed-caller fixtures may run only through the separately specified
source-free pytest path once included by root; never source introspection.

Source-free renderer must retain diagnostics/status, suppress snippets/locals,
inherit warning/subprocess controls and remain unmodified. Ruff concise and
Pyright JSON avoid code frames. Stop if unsupported channels expose source or
material environment failures arise; no silent fallback/retry. Timeout300 is
a bounded command failure status, not human budget or success. No default
scenario/review/repair cap. Root may narrow/sequence this proposal using actual
shared-workload availability.

## Separate tiny dependency qualification request (nonblind coordinator)

Only after the finite cardinal method and exact observer payload/input hash are
frozen, propose one fresh source-free process for the actual default SciPy
cardinal call, not a SIMrecon single-runtime result. No process-memory/timing
claim or observed-error-derived tolerance. It is explicit dependency qualification,
not covered automatically by an ordinary quality-check grant.

Frozen mathematical input proposal: shape(2,4,4), ordinary c64 zeros except
z[0,0,0]=1 and z[1,2,1]=-1/2+i/4; exact Sbar=7/4, N32,d5.
Exact positive direct DFT uses quarter roots; its reference width is0. The
prefrozen per-component bound is gamma(5,2^-24)*(7/4) plus
31*2^-150/(1-5*2^-24). Source method, applicability/range proof and independently
computed direct DFT precede observing the actual call. Do not replace the bound
with measured R or enlarge it after a failure without diagnosis/fresh review.

The one-off payload, reviewed/frozen before execution, may import existing
NumPy/SciPy plus standard library and the exact frozen A quarter-DFT reference
if independently checked. Select existing default with scipy.fft.set_backend
("scipy", only=True), call ifftn c64/axes(0,1,2)/norm forward/workers1/no overwrite,
and report exact reference/error/bound/dtype/status. Nonblind coordinator may
record actual package/git/wheel/compiled-module identities and selected fenv/RNE
facts, printing only sanitized provenance/numbers, no dependency or product
source/introspection/code. A receives only sanitized facts, never raw source.

A normal/zero intermediate proof avoids assuming unsupported gradual underflow
for this finite witness; any broader use of the absolute subnormal term needs
actual material conditions. Verify source/binary correspondence with the pinned
public DUCC source and actual selected numerical environment. A dtype observation
alone establishes none of that. Missing assumptions remain explicit blockers.
This finite2/4 default qualification does not qualify lengths6/8/20/32/64, custom
backends, libm ramps/taper or a universal FFT error theorem. Fresh B independently
challenges the method and actual applicability; D checks implementation/evidence.
