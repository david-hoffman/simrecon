# Name each diagnostic helper identity

**Version 1.0**

- ID: 20261009T123901Z-volume-recombine-01-root-named-diagnostic-identities
- Date: 2026-10-09T12:39:01.614143+00:00
- Task: [VOLUME-RECOMBINE-01](../docs/tasks/volume-recombination.md)
- Role: root coordinator
- Topic: blind diagnostic evidence
- Status: confirmed
- Observation: the communicated core diagnostic SHA-256 was initially labeled as the runner hash. An independent runner rehash differed, while the retained passing proof correctly named both unchanged files. The mismatch was a communication defect, not a post-proof mutation. No blind role launched before that distinction was resolved.
- Evidence: ignored `artifacts/volume-recombination-execution/support-diagnostics-proof-round-02.json` authenticates fourteen controls on locked Python 3.13.12/pytest 9.1.1 and separate core/runner/startup identities; `a-launch-01.json` binds the corrected public packet to the fresh native A thread. These controls prove their named diagnostic channels, not product behavior or full verification.
- Suggested action: name every helper path beside its digest; verify packet identities against the proof before blind probes. Retain negative-control status and unsupported-channel limits. This changes no gate or role scope.
