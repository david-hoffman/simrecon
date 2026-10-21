# Patched development-environment dependency

**Version 1.0.** This bounded dependency-maintenance correction resolves a
necessary blocker in the owner's authorized test/CI work. The full lifecycle
candidate passed8789tests; its final dependency audit failed on virtualenv21.14.1.
Fresh clean Astra classified this settled vendor-patch update as bounded: the
package remains a development dependency through pre-commit, Python remains
explicitly3.13.12, local hooks retain system language, and this project adds no
activation code, execution permission, runtime dependency or policy exemption.

The worker owns only `uv.lock` and its ignored evidence under
artifacts/test-audit-ci/disk-lifecycle/virtualenv-refresh/. Select published
`virtualenv==21.14.11`, which supports Python3.13. It is the selected patched
release, not a claim of newest availability. Preserve all other packages,
versions, dependency relationships and settings; stop and diagnose unrelated
resolver changes. No production/test/fixture/workflow/gate/coverage edit.

Primary upstream expectations:

- [zsh prompt issue](https://github.com/pypa/virtualenv/security/advisories/GHSA-5vjq-rrrf-7h2q): fixed21.14.4.
- [fish quoting issue](https://github.com/pypa/virtualenv/security/advisories/GHSA-c947-3pg5-gm8q): fixed21.14.2.
- [placeholder replacement issue](https://github.com/pypa/virtualenv/security/advisories/GHSA-8rjx-v5ww-45pp): fixed21.14.2.
- [bash prompt issue](https://github.com/pypa/virtualenv/security/advisories/GHSA-vxj4-q4g9-crj7): fixed21.14.7.
- [compatibility-mode prompt issue](https://github.com/pypa/virtualenv/security/advisories/GHSA-6w3r-xr62-4xcp): fixed21.14.9; do not select21.14.7 merely because the earlier audit lists four findings.
- [Published selected release](https://pypi.org/project/virtualenv/21.14.11/).

Use the targeted uv lock upgrade, inspect the complete parsed/text diff, locked
lock check/sync and focused audit, retaining exact commands/status and installed
version. Existing public tests/gates are the meaningful integration proof; no
project tests duplicating upstream shell-escaping internals are required. A
fresh independent bounded reviewer (virtualenv_lock_reviewer, launched by the
coordinator without worker history) must assess the exact candidate, dependency
and preserved-gate scope, oracle/evidence and passing full local result.

Coordinator owns this contract/task documentation and preserving old evidence.
Round5 originals are verified in full-gate-round5-audit-failed/ before any erase.
After focused dependency checks, create a clean exact candidate and repeat the
complete `make verify`, selected100% native executable-line/branch-destination
qualification and fresh lifecycle D. A passing standalone audit does not repair
the failed exact full gate. Retain earlier staged-source disk runs as supplemental;
repeat both heavy diagnostics after the final clean full run closes to bind their
Git-derived report identities to that same candidate. Do not rerun concurrently
against the shared reader cache. Human total execution/review/spending limits are
not set; all failed checks/launches/corrections remain charged, unknown metering
remains unknown. No push while required evidence fails, and no merge/release or
external messaging authority follows.
