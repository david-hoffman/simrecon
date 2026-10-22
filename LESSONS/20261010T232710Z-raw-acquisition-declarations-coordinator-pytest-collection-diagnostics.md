# Pytest import collection has a separate diagnostic channel

**Version 1.0**

- ID: 20261010T232710Z-raw-acquisition-declarations-coordinator-pytest-collection-diagnostics
- Date: 2026-10-10T23:27:10.960012+00:00
- Task: [Raw acquisition declarations](../docs/tasks/raw-acquisition-declarations.md)
- Role: coordinator
- Topic: blind-test diagnostics
- Status: confirmed for the observed local case
- Observation: A missing new public symbol imported during pytest collection emitted a short standard-library loader source line and the owned-test import line despite the existing source-free harness's line traceback setting. A Python-mode retry with pytest native tracebacks reproduced that collection text. No product source snippet or locals appeared in these observations. The fresh author's runtime lookup of the absent export instead produced line-formatted assertion diagnostics without snippets. This establishes the observed workaround, not suppression of every collection channel or engineered access isolation.
- Evidence: local artifacts/raw-acquisition-r1-20261010/A01/report.md and diagnostic-repair/native-collection.log retain the stopped author observation and coordinator reproduction. Python 3.13.12, pytest 9.1.1, macOS arm64; the commands used scripts/source_free_check.py before runtime imports. The runtime export lookup is retained in tests/test_raw_acquisition_declarations.py at test checkpoint fefe2db5b8b5b2d530134d5d80e3c3e06012bedb. Fresh B02 independently reproduced the missing-callable assertion with source-free pytest, capture disabled and no cache provider.
- Suggested action: when testing an absent new export blindly, import the existing public module and assert the new export at runtime through the supported line-formatted harness. Treat unexpected source-bearing collection diagnostics as an exposure requiring routing; the workaround does not establish general collection suppression.
