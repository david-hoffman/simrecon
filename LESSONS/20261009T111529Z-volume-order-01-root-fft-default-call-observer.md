# Audit equivalent public FFT defaults

**Version 1.0**

- ID: 20261009T111529Z-volume-order-01-root-fft-default-call-observer
- Date: 2026-10-09T11:15:29.149867+00:00
- Task: [VOLUME-ORDER-01](../docs/tasks/volume-order-transfers.md)
- Role: root
- Topic: fft-default-call-observer
- Status: confirmed
- Observation: A shared test observer initially mishandled omitted axes with an explicit s argument. NumPy transforms the trailing len(s) axes in that call. The revised observer retained 80 prior supported layouts and added 8 omitted-axes layouts; fresh B4 accepted the complete 152-case checkpoint.
- Evidence: Accepted checkpoint 043af890d7c161fe69550eb0f4577a86035ab02b; tests/test_volume_order_otf.py and tests/volume_order_fixture.py. Independent full B4 verdict and retained before/after control evidence are in artifacts/axial-order-execution/, referenced by the task execution record. macOS arm64, Python3.13.12, NumPy2.5.3.
- Suggested action: For public-call observers, derive omitted defaults from the public API and independently challenge permitted equivalent call layouts before implementation.
