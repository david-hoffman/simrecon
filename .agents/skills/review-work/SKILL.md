---
name: review-work
description: Review blind A tests as B, review passing code as D, or run bounded documentation-only doctor.
---

# Review work

**Version 1.0.** Follow root `AGENTS.md`. Select the role named in the narrow packet. For B or D, you are already the fresh root for that role; perform the work here and do not launch another reviewer or CLI role. The coordinator owns separate fresh native launches for B and D, never reused or forked from the work under review. Review is assessment and handoff, not permission to repair another role's files.

## B: test review

Receive only approved public-contract inputs and A's tests/evidence. Do not read implementation, its history/conversations, implementation-bearing task state, or existing `LESSONS/` entries. Before probes, use source-free traceback **and warning** rendering while retaining diagnostic value and failure status; disclose accidental exposure. Check every scenario has a meaningful public-boundary assertion. Independently recalculate numerical oracles from approved sources/invariants. Check units, conventions, estimators, and tolerances against legitimate variation and plausible wrong outputs; check parser acceptance/rejection. Background references do not silently choose unspecified behavior.

Accept, request bounded A correction, or classify a blocker as environment/tooling, test defect, product defect, or unresolved requirement. Product-red evidence needs a valid test failing at intended behavior; initially passing tests are valid. After two nonacceptances in the current window, diagnose the blocker before another A rewrite. Preserve attempts/budget; restart only after documented resolution or authorized extension. On acceptance, identify the exact reviewed test/fixture checkpoint. Reopen review of changed tests/fixtures only through an evidenced, authorized correction with prior rounds recorded. Return concise verdict/findings, scope, commands/results, evidence pointers, and remaining allowances; link unchanged mappings rather than repeat them.

## D: candidate review

Review only a candidate with passing canonical verification. Inspect behavior against contract, tests, coverage evidence, interfaces, and simplicity. Flag missing scenarios, wrong numerical expectations, hidden exclusions, unsupported metrics, unmeasured owned files, and unverified environment changes. Classify failures before routing. Do not edit product, tests, or rules, or approve your own repair. Return concise acceptance or actionable findings, scope, commands/results, evidence pointers, and remaining allowances; link unchanged mappings and environment records. Product findings route to C within its allowance; test/contract issues return through A/B or intake. Submission still requires passing full verification of the exact candidate.

## Doctor: documentation review

Use `docs/agentic-software-delivery-v1.0/DOCTOR-PROMPT.md` in a fresh session. Check the working tree; avoid overwriting unrelated or active work. Read relevant instructions, recent lessons, and concrete repository/CI evidence narrowly. Separate an evidenced instruction gap from execution error under an existing rule. `--check` reports only and writes nothing. For a confirmed gap, make a small docs-branch patch to the existing delivery spec and directly affected instructions. Keep shared rules in `AGENTS.md`, role differences in skills, and generation templates synchronized. Do not edit runtime, tests, workflows, thresholds, or repository settings. Present exact diff and evidence; wait for explicit owner approval before commit, push, or merge. No daemon, autonomous loop, or speculative threshold change.
