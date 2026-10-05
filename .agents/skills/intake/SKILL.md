---
name: intake
description: Define an approved SIMrecon project or bounded task contract before tests or implementation.
---

# Intake

**Version 1.0.** Follow root `AGENTS.md` for shared rules. Perform intake in this session. This role owns architecture and task definition, not executable tests or product code. Use `docs/agentic-software-delivery-v1.0/templates/PROJECT.md` and `templates/TASK.md`; `docs/agentic-software-delivery-v1.0/INTAKE-PROMPT.md` gives the interview boundary.

Inspect existing records first. Reuse approved architecture, even under another filename. If absent, unapproved, or materially inconsistent, resolve project outcome, constraints, stack, public interfaces, verification, and operation before task work. The approved Python NumPy/SciPy architecture constrains this project. `SIMrecon_svn` is study material only; derive new behavior from approved contracts and applicable primary references, never copied legacy source or assumed product features.

Ask only material unresolved questions, usually at most three per turn. Use contrasting examples. Distinguish observed, proposed, and approved behavior. For numerical outputs, settle units, conventions, estimator choices, tolerances, and boundary cases before tests rely on them. For bugs, separate reproduction evidence, expected behavior, and unverified cause. Unknown cause may warrant a bounded report-only investigation.

Create one small task contract or a large-request plan with all slice contracts. Each ordinary slice defaults to at most five distinct scenario cases, counted in the Contract table. Define observable inputs, outputs, errors, non-goals, dependencies, checks, budget, and completion. Expected results must derive from approved behavior, an applicable primary reference, or a mathematical invariant. Plan slices against the full verification and global coverage gate; expose baseline dependencies before adoption decisions. Redistribute unchanged approved scenarios without expanding total budget or C repair allowance.

Read back the identified task, or the entire slice plan and contracts together. Record the owner's actual approval and document revision; silence is not approval. Architecture approval alone does not approve a task. Stop when a material answer or approval is missing or preparation budget is spent. After approval, prepare narrow A/B packets containing only approved scenario IDs, public interfaces, expected-result sources, requested output, completion condition, relevant revision, budget, and remaining allowances. Exclude implementation, its history/conversations, implementation-bearing task status, and existing lesson entries. Use [PUBLIC-PACKET.md](../../../docs/agentic-software-delivery-v1.0/templates/PUBLIC-PACKET.md) for A/B inputs and sanitize correction findings to the same boundary. Hand approved packets to the coordinator, which owns the fresh native launch commands documented in `docs/PROJECT.md`. Each launched role is already its fresh root; it performs the work there without launching another reviewer or CLI role.
