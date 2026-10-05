# HTML picture records do not establish pixel capture

**Version 1.0**

- ID: 20261005T213507Z-NF01-intake-html-picture-records
- Date: 2026-10-05T21:35:07Z
- Task: [NF01](../docs/tasks/numerical-conventions.md)
- Role: intake
- Topic: reference-conversion evidence
- Status: confirmed
- Observation: The local Docling HTML conversion succeeded with zero errors and retained all four captions, but its four picture records contained zero embedded images. Direct publisher PDF and Figures 2–4 requests returned HTTP 403. A separate browser Figure 1 export took about 29 minutes; its stall cause is unknown. Conversion success alone therefore did not establish source-pixel capture.
- Evidence: [Conversion counts, artifact hashes and access attempts](../docs/references/scientific/gustafsson-2000/full-text-extraction.json); recorded HTML conversion command, Docling Slim 2.131.0, Python 3.12.14, macOS arm64. [PR #4](https://github.com/david-hoffman/simrecon/pull/4) records the owner-approved removal of source-figure capture from scope.
- Suggested action: Define and compare the required text/notation/caption content explicitly. Keep converter status, embedded-pixel counts and separate download attempts distinct. Apply NF01's approved scope removal; this lesson authorizes no further figure-capture work.
