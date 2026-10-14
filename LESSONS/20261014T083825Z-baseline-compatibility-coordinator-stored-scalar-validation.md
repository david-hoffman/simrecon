# Validate stored scalar values before ordinary conversion

**Version 1.0**

- ID: 20261014T083825Z-baseline-compatibility-coordinator-stored-scalar-validation
- Date: 2026-10-14T08:38:25.215263+00:00
- Task: [BASELINE-COMPATIBILITY-01](../docs/tasks/shared-node-baseline-compatibility.md)
- Role: coordinator, observing fresh blind B08 review
- Topic: scalar validation and caller exceptions
- Status: confirmed
- Observation: An ordinary float subclass can store NaN or positive infinity while its conversion returns finite 0.125. The reviewed public tests establish two source-finiteness failures despite finite conversion. The independent reviewer also accepted preserving an unrelated caller-owned domain exception by object identity and code when its ordinary conversion callback actually raises, while admitting a qualified lawful protocol bypass.
- Evidence: Exact accepted six-file checkpoint and B08/final.txt in ignored artifacts/baseline-compatibility-20261013; public-failure test SHA256 377af6d65033a072d40ddc0e14517e37f2fe38936c8901a0d26ed47924f94abf. Authenticated 28-example run: 26 passes and the two stored-source failures; no skips. B08 independently accepted these supplemental product-red cases.
- Suggested action: Preserve distinct stored-source and converted-value obligations during validation consolidation. Error inheritance alone does not establish that an unrelated caller error may be replaced. This evidence grants no additional editing or gate authority.
