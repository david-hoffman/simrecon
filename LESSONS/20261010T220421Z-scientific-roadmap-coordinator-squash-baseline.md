# Use the merged baseline after squash integration

**Version 1.0**

- ID: 20261010T220421Z-scientific-roadmap-coordinator-squash-baseline
- Date: 2026-10-10T22:04:21.999437+00:00
- Task: SCIENTIFIC-ROADMAP-20261010, owner-merge continuation.
- Role: coordinator/intake author.
- Topic: squash ancestry and candidate identity.
- Status: confirmed.
- Observation: owner-merged `main` at `8f7148d` and PR #21 at `d3ba763` have the same tree `88e4643`, but squash ancestry leaves merge-base `a44e9d0`. Keeping the roadmap above the old PR #21 chain would produce a 224-file three-dot PR diff despite only four directly different documentation files.
- Evidence: git merge-base, git diff --stat and tree identities in `artifacts/roadmap-amendment-20261010/stack-correction/`; live owner-completed merge snapshot and prior exact-candidate receipts remain preserved.
- Suggested action: preserve the old candidate, replay only the roadmap commit onto merged main, update active baseline/target statements, run fresh exact-candidate verification and independent documentation review, then migrate the existing successor’s own work. Equal file trees narrow the migration; they do not certify a new commit. Preserve earlier lesson bytes and cumulative accounting.
