# Pinned validator behavior differs from its prose dimensions rule

**Version 1.0**

- ID: 20261001T050213Z-mrc-conversion-intake-validator-doc-discrepancy
- Date: 2026-10-01T05:02:13Z
- Task: [MRC conversion intake](../docs/tasks/mrc-conversion.md)
- Role: intake
- Topic: independent-reader applicability
- Status: confirmed
- Observation: mrcfile 1.5.4 prose describes positive cell dimensions, while its published validator source checks for negative dimensions and therefore allows zero. The initial proposed nonphysical axial placeholder was based on the stricter prose description; the revised proposal keeps unknown axial scale zero.
- Evidence: [Pinned public-wheel source inspection](../docs/architecture/mrc-output-compatibility.md), with advertised wheel SHA-256 verified; package source read in memory without installation/execution. This corrects the initial documentation-based claim in the intake conversation and superseded owner-observation draft, not an executed reader result.
- Suggested action: check the pinned reader's actual rule before choosing output conventions; establish live output validation in fresh contract tests. Never describe a source inspection as a passing product check. This grants no implementation authority.
