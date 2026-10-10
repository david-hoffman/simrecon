# Global Java absence did not establish Fiji runtime absence

**Version 1.0**

- ID: 20261009T213515Z-imagej-intake-coordinator-bundled-java
- Date: 2026-10-09T21:35:15.047645+00:00
- Task: IMAGEJ-INTAKE-01 / docs/tasks/imagej-adapter-intake.md
- Role: coordinator
- Topic: reader capability inventory
- Status: confirmed
- Observation: The global Java launcher and java_home exited 1, but a discovered Fiji installation contained bundled Java 21.0.7 whose explicit executable completed -version with exit 0. The initial named application paths missed the nested Fiji.app layout. Installed reader jars and a working JVM do not establish actual file/ImageJ interoperability; the attempted JShell class-load probe timed out.
- Evidence: artifacts/imagej-adapter-intake/capability-inventory-01.json; capability-fiji-inventory-02.json; capability-reader-classload-04.json. Read-only bounded checks on macOS 27 arm64, October 9, 2026. No GUI or file import occurred.
- Suggested action: Inventory the discovered Fiji installation and bundled runtime before concluding that missing global Java blocks reader setup. Keep actual importer/pixel/dimension/scale acceptance separate.
