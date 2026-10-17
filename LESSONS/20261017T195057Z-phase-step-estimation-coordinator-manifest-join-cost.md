# Exact-input manifest preparation can have quadratic lookup cost

**Version 1.0**

- ID: 20261017T195057Z-phase-step-estimation-coordinator-manifest-join-cost
- Date: 2026-10-17T19:50:57.754442+00:00
- Task: phase-step-estimation
- Role: coordinator
- Topic: verification preparation cost
- Status: confirmed
- Observation: The frozen run_local.py generation-alias comprehension repeatedly scans the full input mapping and constructs the same path inside each comparison. For 16200 logical inputs and15175 generation inputs, the actual insertion order implies130484579 prefix comparisons. A bounded20000-comparison sample took0.053366958993137814s, implying348.17825883649255s for that predicate alone under the sample conditions. This is a cost estimate from a representative path, not a profile or ETA for the running verification. Warm preflight ended at2026-10-17T19:23:45.096648+00:00; actual make began at19:29:18.423334+00:00. No helper was changed and no passing gate result follows from this observation.
- Evidence: Preserved predecessor worktree58fe, artifacts/phase-step-estimation-20261016/preparation-cost-diagnosis01.json; support-qualification/run_local.py generation_aliases comprehension; full-local01/preflight.json and launch.json. Locked CPython3.13.12 on local macOS27.0.1 arm64. The original helper remains frozen at SHA256e5faed95d9394124ee3579b54a55f0a6b94880cb373955448a7e2d2dc43cf705.
- Suggested action: During a separately authorized bounded setup, consider building one exact path-to-alias mapping before the generation-input join. Independently verify unchanged positive/rejection behavior, complete pin identity and failure handling before use. This observation grants no helper-edit, gate-weakening or new budget authority. This entry was handed off after the current candidate froze; record it in the successor's unique root LESSONS file before that successor freezes its candidate.
