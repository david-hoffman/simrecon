# Request the Pyotf focal plane explicitly

**Version 1.0**

- ID: 20261006T160343Z-calibration-intake-explicit-pyotf-focus
- Date: 2026-10-06T16:03:43Z
- Task: [CALIBRATION-FOUNDATIONS](../docs/tasks/otf-calibration-foundations.md)
- Role: intake coordinator, with independent read-only source adviser
- Topic: optical fixture provenance
- Status: confirmed
- Observation: Pyotf source revision d641ff6cde1fac6e77ff2d47629d981831a75912 constructs its default one-plane z range at -zres. An explicit zrange=[0.0] produces the intended focal-plane example. The illustration actually ran with Python 3.13.12 and this source revision; that single recipe does not qualify the package or physical convergence generally.
- Evidence: [source/recipe notes](../docs/references/scientific/otf-calibration-pyotf-notes.md) and [observed source/environment manifest](../docs/references/scientific/otf-calibration-intake-manifest.json); isolated generator imported HanserPSF and observed a (257,257) focal image.
- Suggested action: record explicit axial coordinates and exact model/source identities for future optical fixtures; do not infer focus from a one-plane stack or reuse a simulated response as its own correctness oracle.
