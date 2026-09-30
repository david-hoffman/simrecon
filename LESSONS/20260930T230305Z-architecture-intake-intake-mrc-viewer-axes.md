# Preserving extended metadata does not establish viewer axis support

**Version 1.0**

- ID: 20260930T230305Z-architecture-intake-intake-mrc-viewer-axes
- Date: 2026-09-30T23:03:05Z
- Task: [ARCHITECTURE-INTAKE](../docs/tasks/architecture-intake.md)
- Role: intake
- Topic: viewer interoperability
- Status: confirmed
- Observation: The Bio-Formats `develop` MRC reader inspected on September 30, 2026 sets ordinary non-RGB data to one channel and one time point, and skips the extended header. Saving logical axes in a project-specific extended schema therefore does not by itself establish correct five-dimensional ImageJ interpretation. This is source evidence, not a test of an installed viewer/version.
- Evidence: [Reader source](https://github.com/ome/bioformats/blob/develop/components/formats-gpl/src/loci/formats/in/MRCReader.java), `initFile` channel/time assignment and extended-header handling; [published format support](https://bio-formats.readthedocs.io/en/stable/formats/mrc.html); [project interpretation and staged requirement](../docs/architecture/library-design.md).
- Suggested action: Distinguish library/file metadata preservation from actual viewer support. Pin a reader/version in the relevant contract and verify pixel orientation, spatial scale, and logical dimensions with asymmetric reference fixtures. Evaluate a later format adapter or reader integration for full X/Y/Z/channel/time support; do not silently relabel flattened sections as physical Z.
