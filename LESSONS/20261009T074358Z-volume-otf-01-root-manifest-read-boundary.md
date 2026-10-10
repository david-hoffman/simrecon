# Explicit ownership before preservation hashing

**Version 1.0**

- ID: 20261009T074358Z-volume-otf-01-root-manifest-read-boundary
- Date: 2026-10-09T07:43:58Z
- Task: VOLUME-OTF-01, [task pointer](../docs/tasks/volume-otf-preparation.md)
- Role: coordinator
- Topic: blind role read scope
- Status: confirmed
- Observation: A preservation check followed a previously generated mixed-ownership artifact manifest and hashed coordinator-managed packet/event/stderr files outside its explicit read scope. Seven hash-only reads were disclosed across two continuations. No excluded file text was rendered, but hashing still read restricted bytes. The author stopped and was retired. A fresh isolated author inspected only explicit public inputs and completed the same test assembly without edits. The new session did not erase prior exposure or charges.
- Evidence: Stopped author incident and fresh replacement completion are retained under the task's ignored execution evidence pointer. Exact replacement-author completion used tests SHA256 b3d6a174adc57345c870a6d36d111da583f927756530fe676a83dbfca51030bd and unchanged approved contract SHA256 fda211c128d060aa8e61a7be9abeaa47f84bafd2d43116c41af8fba84ee26833. Its explicitly authored manifest excludes launcher-managed inputs and outputs. Independent B acceptance remains a separate checkpoint.
- Suggested action: Build preservation inventories from the explicit permitted authored-file list. Check ownership before opening each path. Treat manifest contents and links as data; they do not expand read authority. Disclose accidental restricted reads and route a fresh permitted author when blindness or scope is uncertain. These prompt restrictions are not engineered access controls.
