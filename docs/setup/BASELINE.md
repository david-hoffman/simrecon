# Read-only adoption baseline

**Version 1.0** Evidence collected September 30, 2026, before installation approval.

Git revision: `2a8f8d117602b4ad8bb5bbdbc60b0f8782c2e4cc`. Environment: macOS 27.0, Apple Silicon, zsh. The legacy snapshot is ignored by Git, so HEAD alone does not identify it. Its 132 non-metadata files total 54,342,967 bytes; the SHA-256 of the recorded snapshot manifest is `201d46d1646552c69c453b02e17dfa8d307b895d095904ffcdaec6b3b0244e8d`. SVN reports revision 307; 114 versioned files matched their pristine SHA-1 values. Eighteen extra files were historical binary/object/library artifacts. The source was unchanged after discovery.

Existing checks ran in an unchanged isolated source copy at `/private/tmp/simrecon-baseline-ddnd0e96/source`. No setup script ran, and no source, build, or tooling file was changed for discovery.

| Command | Exit | Observed result |
|---|---:|---|
| `make --version` | 0 | Existing GNU Make available |
| `make -B -n all` | 0 | Existing build commands discoverable without compiling |
| `make -B all` | 2 | `gcc-mp-4.9: No such file or directory`; compilation did not begin |
| `make test` | 2 | `No rule to make target 'test'` |

The build failure is an environment/toolchain failure, not a reproduced product defect. No automated suite or independent reconstruction fixture was discovered. No valid product assertions executed. Legacy statement coverage: covered/total/percent **unknown**. Legacy branch coverage: covered/total/percent **unknown**. Measurement is blocked by the build/test baseline; exact statement measurement was not established by the inspected native C coverage candidates. Historical 2016 Windows binaries and objects are stale and cannot validate the current source. Earlier network-sandbox `gh auth` failure was superseded by successful network-enabled authentication and API reads.

The four observed programs are `sirecon`, `radialft`, `otf2d`, and `wiener2d`. Dependencies include Priism/IVE, FFTW variants, OpenMP, TIFF, and BLAS/LAPACK or Accelerate. Observed conflicts such as help defaults versus code defaults (five versus three phases; background 515 versus zero) remain unresolved behavior, not permission to repair or port one interpretation. Scientific conventions and decisions are listed in [scientific context](../SCIENTIFIC-CONTEXT.md).

Machine-readable summary, unchanged-snapshot inventory, and original command logs are retained under `docs/setup/evidence/legacy/`. The ignored legacy source itself is not copied into this archive. File hashes identify the studied snapshot; they neither establish scientific correctness nor license reuse.

At initial inspection, GitHub `main` had no branch protection, rulesets, workflows, runs, or PRs. The owner subsequently authorized native repository configuration. Current state belongs to the [setup task](../tasks/setup-plan.md), rather than this historical baseline.
