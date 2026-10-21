# Use the scheduler's native test identities for timing data

**Version 1.0**

- ID: 20261021T230753Z-test-audit-ci-coordinator-native-scheduling-identities
- Date: 2026-10-21T23:07:53+00:00
- Task: test-audit-linux-ci
- Role: coordinator
- Topic: Standard pytest-split timing input with grouped xdist workers
- Status: confirmed
- Observation: The first derived timing map had all 8,950 original semantic test IDs and independently correct measured values. It still missed 265 scheduler lookups: xdist 3.8.0 annotates grouped worker node IDs before pytest-split 0.11.0's late collection hook looks up exact native IDs. The affected 107 reader-cache and 158 evidence-baseline cases would receive average fallback weights. A correct semantic completeness map does not establish that scheduling weights are consumed.
- Evidence: The independent R1 review is retained at artifacts/test-audit-ci/standard-ci/performance/timing-data-review/REPORT.md, SHA-256 f8fbd54d19d77b8ec0e83207f26ca40470b7a58cabbf7c8732d57cd84c6ac5bf. It reconstructed all 26,850 passed native phase reports and the exact original data SHA-256 110d49df729ba2383f32093485a3858d562ba37bb0221fe49e632ec33c517f66. Installed xdist remote.py SHA-256 86d2f8132b3ef7e190f622c2b3cfd83cde464a4dd07ccd75486b27b161336b3d and pytest-split plugin.py SHA-256 6a79343ca370b680c65776a3f7515a27cad9ceab1f2eeef4592bcbddfa665a03 supply the hook and writer behavior. Fresh clean-context Astra separately confirmed the diagnosis. No rejected data was activated.
- Suggested action: Use whole observed native report IDs as timing keys, with a separately retained observed association to semantic IDs for comparison with the complete serial reference. Check native-key uniqueness before constructing the map. Preserve transport strings; do not reconstruct resource suffixes or add aliases. Collection-only execution bypasses xdist worker setup, so qualify the actual configured complementary execution separately. This is a scheduling-data correction, not authority to change scientific tests, the scheduler or acceptance gates.
