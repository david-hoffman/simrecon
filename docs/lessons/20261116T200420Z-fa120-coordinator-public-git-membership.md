# Filesystem identity does not establish public Git membership

**Version 1.0**

- ID: 20261116T200420Z-fa120-coordinator-public-git-membership
- Date: 2026-11-16T20:04:20.556857+00:00
- Task: [#120](https://github.com/david-hoffman/simrecon/issues/120)
- Role: campaign coordinator
- Topic: scientific evidence portability
- Status: confirmed
- Observation: Nine ignored environment files were incorrectly listed among494 public ancestor references. Matching their current filesystem hashes and lengths did not show that their bytes existed in Git. ROOT found the metadata error before tracked report integration. Scientific source, observations and conclusion were unchanged.
- Evidence: [ROOT exact Git/copy proof](../reports/lower-memory-fourier-assembly/evidence/review/ROOT-corrected-portable-Git-blob-proof-1.json), SHA8ad71ced219b0fe52612ecc52cd506f1403b8613d75f6071e3c51a6dba1a4f70; [fresh affected SCI4](../reports/lower-memory-fourier-assembly/evidence/review/portability-scientific-review4/report.md), SHA457b5c07d259814a4004dc10da24dbc563dbcfa7ffb5220ed1c5b36b3dea6285. Exact REV:path Git blob OID/SHA256/uncompressed length checks independently cover485 references, with332 exact copies and3 unbundled native identities.
- Suggested action: Check claimed public references against their exact Git revisions and paths; distinguish copied evidence from native identity metadata. This observation authorizes no new framework or policy change.
