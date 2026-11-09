# Resolve a literal selector before both validation and routing

**Version 1.0**

- ID: 20261104T081421Z-ce06-coordinator-resolve-selector-once
- Date: 2026-11-04T08:14:21Z
- Task: CE06 acquisition modes
- Role: coordinator
- Topic: public value validation
- Status: confirmed
- Observation: A supported selector whose actual text was direction-major selected z-major when its custom equality claimed that value. Its result still reported direction-major. A non-string mock that advertised the str class also passed an instance check and reached an internal string conversion error. Both public observations held the other inputs fixed.
- Evidence: Code correction `1ce1643d76ef1de8df59800eeb62564b545e361d` and [public boundary cases](../tests/test_c_acquisition_boundary.py), including `test_regrouping_routes_by_underlying_selector_text`. The source-free controls used the locked Python 3.13.12 environment.
- Suggested action: Validate the actual string type and resolve the supported literal once at a public boundary. Use that same value for routing and published settings. When routes differ, keep a control that checks the chosen output before checking metadata.
