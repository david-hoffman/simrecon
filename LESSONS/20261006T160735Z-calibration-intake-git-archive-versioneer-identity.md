# Distinguish Git blobs from exported version bytes

**Version 1.0**

- ID: 20261006T160735Z-calibration-intake-git-archive-versioneer-identity
- Date: 2026-10-06T16:07:35Z
- Task: [CALIBRATION-FOUNDATIONS](../docs/tasks/otf-calibration-foundations.md)
- Role: intake coordinator, finding supplied by fresh independent intake reviewer
- Topic: source and generated-version provenance
- Status: confirmed
- Observation: Pyotf revision d641ff6cde1fac6e77ff2d47629d981831a75912 declares export-subst for pyotf/_version.py. git archive expands its Git keywords, giving bytes different from git-show's tracked blob. The archived module reports 0+unknown. Exact commit identity alone must not be presented as byte identity or a meaningful resolved package-version string for that transformed file.
- Evidence: [corrected manifest](../docs/references/scientific/otf-calibration-intake-manifest.json) separates tracked-source and archived-source hashes and records the transformation; git check-attr export-subst, git show, tar member SHA-256 and module version inspection established the cause. [Recipe/source notes](../docs/references/scientific/otf-calibration-pyotf-notes.md) preserve its limits.
- Suggested action: record source blob and exported/generated-byte identities separately when Git archive or a versioning tool transforms inputs; pin the actual simulator source/environment rather than trust an unknown version string.
