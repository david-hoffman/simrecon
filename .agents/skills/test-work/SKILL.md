---
name: test-work
description: Author blind role A contract tests for an approved SIMrecon slice through public interfaces.
---

# Test work: role A

**Version 1.0.** Follow root `AGENTS.md`. You are already the fresh root for role A with the approved A packet. Perform the work here; do not launch another reviewer or CLI role. The coordinator owns role launches. Work only in authorized test and fixture scope. Do not read implementation source, its history/conversations, implementation-bearing task status, or existing `LESSONS/` entries. Public-interface records and the lesson format guide are permitted.

Before importing or probing the product, arrange source-free rendering for tracebacks **and warnings**. Retain exception type, message, stack locations, and failure status. If a tool exposes source anyway, disclose the exposure and stop blind work until the coordinator resolves it. Do not use exploratory inspection that prints implementation internals.

Map every approved scenario to a public entry point and observable assertion. Prefer end-to-end or public API tests. Use smaller interfaces only for a real gap through a boundary production or real callers also need. For numerical cases, state units, conventions, estimator assumptions, oracle derivation, and tolerance rationale. Choose inputs distinguishing correct results from plausible wrong values. For parsers, test approved syntax and material rejection boundaries. Do not derive expected values from product output or legacy implementation.

Existing code may pass initially. Report that honestly; do not force red or mutate the product. Run relevant checks with source-free diagnostics, classify any failure as environment/tooling, test defect, product defect, or unresolved requirement, and report evidence without leaving scope. Return a concise handoff for B: verdict/findings, scope, scenario mapping, oracle sources, tolerance rationale, commands/results, and any source exposure or unresolved issue. Link unchanged mappings and evidence rather than repeat them. Tests are not a reviewed checkpoint until B accepts them.
