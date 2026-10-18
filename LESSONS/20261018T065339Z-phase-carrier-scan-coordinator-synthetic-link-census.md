# Synthetic probe links need an explicit closed-evidence representation

**Version 1.0**

- ID: 20261018T065339Z-phase-carrier-scan-coordinator-synthetic-link-census
- Date: 2026-10-18T06:53:39.527326+00:00
- Task: [unknown-phase finite carrier scan](../docs/tasks/phase-carrier-scan.md)
- Role: coordinator
- Topic: evidence closure
- Status: confirmed
- Observation: The accepted source-free synthetic controls left one lookup symlink in each setup author/reviewer scratch root. The role binder rejects live authoritative symlinks. Passing helper controls alone therefore did not make those scratch roots acceptable closed role inputs. This was a preparatory metadata issue; no scientific gate had run.
- Evidence: The original S01/H01 closure-final01.json records under artifacts/phase-carrier-scan-20261018 retain the exact link targets. Their synthetic-link-normalization01.json records and readback-verified synthetic-links01.tar archives preserve those links recoverably. Only the synthetic link entries were unlinked; target files, accepted helper bytes and original reports stayed unchanged. Superseding closure-final02.json records contain no live links. The binder rule is documented in the exact accepted support-setup/README.md and H01/acceptance.json.
- Suggested action: Check synthetic scratch links before freezing the role census. Preserve exact originals and normalization evidence; do not silently follow a live link or erase prior closure/accounting records. This finding changes no helper, gate or role authority.
