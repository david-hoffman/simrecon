# Physical coverage arcs and logical branch destinations are different evidence

**Version 1.0**

- ID: 20261021T021518Z-relative-phase-invariants-coordinator-native-coverage-arcs
- Date: 2026-10-21T02:15:18.148555+00:00
- Task: RELATIVE-PHASE-INVARIANTS / PR49
- Role: coordinator
- Topic: native coverage qualification
- Status: confirmed
- Observation: Coverage.py7.16.2 reported the same4,282/4,282 executable lines and1,302/1,302 logical branch destinations on the accepted candidate, while original physical arc totals were8,667 on Ubuntu and8,659 on macOS. Directly equating physical arc counts or positive endpoints with native logical report sets produced an incorrect qualification result. Native source translation and branch filtering are part of the measurement semantics.
- Evidence: Candidate1009f651b4aec345996cdbd77f525d7ec9ad8d09; [PR49](https://github.com/david-hoffman/simrecon/pull/49); [native CI run39523739279/attempt1](https://github.com/david-hoffman/simrecon/actions/runs/39523739279). Retained local qualification05 SHA2569102089c028bf40be1f8941a5567ec7a6258b242f6b212e4ecd27d1cc2a2ae10 and independent native reviewR05 SHA2561128a34a35f8a8dd26b140a4c0b2e3d28bcdf76c3d9fa07808cbd5be6f74fb67. Canonical makeverify; Python3.13.12/Coverage7.16.2. The unchanged64735B native-analysis support helper SHA2564bf7cad4f595e08cdbdcaa0564433c91cfe8779f206c514c6ba8c28021cdadfd and83dependency pins were checked before/after the actual comparisons. These are exact observed scopes, not complete behavior coverage.
- Suggested action: Qualify each original platform's physical arcs with the same native Coverage version/configuration and frozen source; compare translated executed/missing lines and possible/executed/missing branch pairs to its original logical report. Retain physical and logical totals separately. Diagnose a faulty proof reader before requesting product/test repairs. This lesson changes no selected target or editing authority.
