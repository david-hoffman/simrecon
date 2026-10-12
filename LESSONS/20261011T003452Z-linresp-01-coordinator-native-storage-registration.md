# Register storage-specific examples by observed native capability

**Version 1.0**

- ID: 20261011T003452Z-linresp-01-coordinator-native-storage-registration
- Date: 2026-10-11T00:34:52.441802+00:00
- Task: LINRESP-01; [task pointer](../docs/tasks/linear-response-correction.md)
- Role: coordinator
- Topic: portable native numerical examples
- Status: confirmed
- Observation: The blind author initially registered five wider-floating-storage examples as skips on Darwin binary64 longdouble. The installed gate rejects skips. The same unexposed author corrected registration using observed native dtype capabilities; assertions remained intact. The final local checkpoint collected 241 cases with zero skips; five unsupported wider examples were absent rather than reported as passing.
- Evidence: Test checkpoint 9f68b1c73d0bd26adacf3dd8c98b0b0b5efb9bea; corrected test SHA256 4ef6c4f20869d3d23997dfe91bf092c42ae45bdab8a5c773e4147feb533e1bb8. Ignored local A01-cont1/report.md and B01/final.txt are linked by the task pointer. B01 independently accepted capability predicates and retained oracles. Environment: Python 3.13.12, NumPy 2.5.3, Darwin arm64; longdouble significand/exponent range matched binary64.
- Suggested action: Keep applicable native examples and supported base examples. Record unsupported representation evidence explicitly; do not treat absent collection as a pass or infer capability from an operating-system label.
