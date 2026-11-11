# Reuse certified queries with complete uncertainty inputs

**Version 1.0**

- ID: 20261109T081336Z-test-apparatus-coordinator-certified-query-keys
- Date: 2026-11-09T08:13:36.514312+00:00
- Task: [test-apparatus-optimization](../tasks/test-apparatus-optimization.md)
- Role: coordinator
- Topic: independent numerical test apparatus
- Status: confirmed within the reviewed fixture scope
- Observation: A pure numerical-observer query can depend on both its nominal coordinate and separate observer/backend uncertainty columns. Reuse keyed only by the center would merge different certificates. Invocation-local keys retain dtype, shape and exact bytes for all three columns, plus fixed table/axial/order dependencies; radial reuse factors through the identical certified radial intermediate.
- Evidence: [resumed evidence](../reports/test-apparatus-audit/resume), blind A exact before/after probes and fresh B reviews, including signed zero, changed radius columns, nonzero table errors, valid flat aliases, unsafe stencils and caller nonmutation. The original on-demand observer remains callable.
- Suggested action: Establish purity, complete inputs, lifetime and nonmutation before local reuse; compare numerical/certificate bytes and independently review permitted positives as well as errors. Do not infer a global cache architecture or elapsed-time guarantee.
