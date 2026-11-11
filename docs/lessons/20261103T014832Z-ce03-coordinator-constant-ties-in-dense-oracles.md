# Dense equivalent formulas can change exact finite decisions

**Version 1.0**

- ID: 20261103T014832Z-ce03-coordinator-constant-ties-in-dense-oracles
- Date: 2026-11-03T01:48:32.639822+00:00
- Task: CE03, [task pointer](../tasks/c-equivalence-optical-transfer.md)
- Role: coordinator
- Topic: numerical oracle
- Status: confirmed
- Observation: The original dense edge observer changed a constant2-count plane by up to4.440892098500626e-16counts, changing its refined center from(0,0,0) to(19.875,1.125,0)pixels. A second negative-map plateau had the same cause. The literal endpoint differences are exactlyzero. Blind A repaired the observer without changing tolerances; fresh B4 independently recalculated all41affected cases and accepted the revised complete checkpoint.
- Evidence: C1/public-findings.md; A3-correction-3/design.md and report.md; B4/final.md in the CE03 evidence root. Source-free arithmetic and focused pytest used Python3.13.12/NumPy2.5.3; checkpoint3eb95d7dc9f6a42448fd0a1f6b687bd049eba3aeb950d44213f4fae45fda96be. Evidence root: `/private/tmp/simrecon-ce03-evidence-20261102/`; archived by the sole Current state at completion.
- Suggested action: For an oracle that feeds a discrete maximum or branch, verify exact nulls/ties independently and review every shared dependent after an arithmetic change. A small continuous error bound alone does not justify a changed finite decision. This entry grants no edit, publication or policy authority.
