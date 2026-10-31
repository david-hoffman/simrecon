# Give each public evidence checkpoint a unique path

**Version 1.0**

- ID: 20261031T213547Z-ra10-coordinator-unique-public-evidence-paths
- Date: 2026-10-31T21:35:47.820426+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: evidence custody
- Status: confirmed
- Observation: The coordinator reused the initial public-evidence filename for the revised A checkpoint. The original bytes were restored and matched B1 observed output; revised bytes were preserved under a unique filename. B2 was intentionally interrupted without a verdict, and fresh B3 was launched. All launch and repair charges remain retained.
- Evidence: ../artifacts/ra10/checks/public-evidence-path-repair-1.json. The restored SHA256 is 9178a0816f1d938f57d3df84712f2d0d65d36bc2b7b2e1a9b0cffd10e13bf7fe.
- Suggested action: Allocate a new evidence filename before launching a consumer, then bind its exact bytes; retain superseded originals at their required paths.
