# A unit Nyquist expectation needs an explicit unit gain

**Version 1.0**

- ID: 20261031T023130Z-ra07-coordinator-nyquist-gain-expectation
- Date: 2026-10-31T02:31:30.499280+00:00
- Task: [RA07](../docs/tasks/reference-alignment-ra07.md)
- Role: coordinator
- Topic: independent numerical fixture qualification
- Status: confirmed
- Observation: Fresh B2 found a local analytic test retained gain0.75 while expecting unit amplitude with transfer1 and penalty0. The approved quotient is0.75/(0.75**2)=4/3. This was a test defect; no implementation had been authored or observed.
- Evidence: artifacts/ra07/roles/B2/final.txt; exact prior sources in artifacts/ra07/checkpoint-A1-v2 and authored-checkpoint-v2.json.
- Suggested action: Derive special-case amplitudes from the actual declared gain, transfer and penalty, or set the intended unit parameters explicitly before observing product output.
