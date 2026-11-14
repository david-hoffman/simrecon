# Reconstruction walkthrough math rendering

## Current state

- Request: fix the GitHub math-rendering error shown in the reconstruction
  walkthrough screenshot. Route: mechanical, presentation-only documentation.
- Scope: `docs/architecture/reconstruction-walkthrough.md` and this task record.
  Replace escaped punctuation delimiters with equivalent named TeX delimiters
  in both assembly equations, the bead-frequency norm and the radial limit.
  Mathematical expressions and product behavior remain unchanged.
- Evidence: local Markdown processing consumed the original brace escapes;
  MathJax 3.2.2 then reproduced both reported `\\left` delimiter errors.
  After correction, all 31 display equations passed Markdown-to-MathJax
  rendering. All four edited equations produced identical direct-TeX SVG
  before and after. This is local renderer evidence, not a live GitHub preview.
- Checks: focused rendering, diff review and whitespace checks passed.
  No product tests added for this formatting edit. The owner subsequently
  requested a PR with auto-merge enabled. Next: integrate current main, commit
  the candidate, pass canonical `make verify`, then push, open the PR and enable
  auto-merge. Final candidate identity, checks and submission results belong
  outside verified tracked bytes in the PR and handoff.
- Accounting: one mechanical worker and one read-only diagnostic advisor;
  one correction pass, no required independent review. One restricted-network
  package install stopped, then succeeded with network access. One Node child
  process check failed with `EPERM`; rerun using a shell-exported baseline passed.
  A second read-only advisor checks verification prerequisites for submission.
  Human limits not set; model metering, cost and total elapsed time unknown.
- Cleanup: temporary renderer dependencies and baseline under
  `/tmp/simrecon-walkthrough-math-check` removed after checks; current checkout,
  environment and unrelated files retained. No cleanup errors or active writers.
