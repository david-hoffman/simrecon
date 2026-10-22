# Native type names do not guarantee a wider value domain

**Version 1.0**

- ID: 20261018T033311Z-observable-phase-coordinator-native-dtype-capabilities
- Date: 2026-10-18T03:33:11.998766+00:00
- Task: PHASE-OBSERVABLE-SUBSPACE
- Role: coordinator
- Topic: platform representation tests
- Status: confirmed
- Observation: On the admitted macOS platform with Python3.13.12 and NumPy2.5.3, longdouble had the same maximum and tiny values as float64, while clongdouble occupied16bytes. Four representation cases raised native pytest skip exceptions before calling the new operation. A status0 diagnostic that records those exceptions is not four passing tests.
- Evidence: `artifacts/phase-observable-subspace-20261018/B03/public-findings01.json` and B03's retained native report at checkpoint `18d2f0d9f8349bf95583deaafe9568e84a158cdd`; all4skip outcomes were directly reproduced through the admitted source-free channel.
- Suggested action: Determine applicable representation domains from actual native conversion behavior. Retain wider-domain checks where available, test permitted native-width inputs elsewhere, and report unavailable domains explicitly under the existing no-skip gate. No product behavior, type restriction or gate change follows from this observation.
