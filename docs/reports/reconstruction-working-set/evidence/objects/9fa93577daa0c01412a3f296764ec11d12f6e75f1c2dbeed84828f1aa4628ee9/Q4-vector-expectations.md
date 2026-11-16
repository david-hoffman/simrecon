# Q4 finite vector expectations — unexecuted source

The frozen JSON fixture provides each input, mutation and literal expected result. The accepted interfaces supply observed outcomes during a later released invocation. These are synthetic scalar records; no native/scientific measurements are represented.

| Vector | Accepted interface | Expected outcome | Direct completeness |
| --- | --- | --- | --- |
| unprofiled-max-null-big-endian | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T1-no-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T1-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T2-no-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T2-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T4-no-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| profile-T4-layout | child_outcome | "finite_observation_pending_qualification" | accepted |
| status-material_identity_failure | child_outcome | "material_identity_failure" | not invoked |
| status-nonfinite_scientific_failure | child_outcome | "nonfinite_scientific_failure" | not invoked |
| status-workflow_exception | child_outcome | "workflow_exception" | not invoked |
| status-observation_failure | child_outcome | "observation_failure" | not invoked |
| file-missing | child_outcome | "missing_child_record" | not invoked |
| file-empty | child_outcome | "missing_child_record" | not invoked |
| file-truncated | child_outcome | "malformed_child_record" | not invoked |
| file-invalid-utf8 | child_outcome | "malformed_child_record" | not invoked |
| file-array-not-object | child_outcome | "malformed_child_record" | not invoked |
| file-oversized | child_outcome | "child_record_exceeds_admitted_parse_bound" | not invoked |
| snapshot-map-null | child_outcome | "malformed_child_record" | refused |
| snapshot-map-missing | child_outcome | "malformed_child_record" | refused |
| snapshot-pre-null | child_outcome | "malformed_child_record" | refused |
| snapshot-post-missing | child_outcome | "malformed_child_record" | refused |
| snapshot-scope | child_outcome | "malformed_child_record" | refused |
| snapshot-native-null | child_outcome | "malformed_child_record" | refused |
| snapshot-native-bool | child_outcome | "malformed_child_record" | refused |
| snapshot-native-negative | child_outcome | "malformed_child_record" | refused |
| snapshot-native-units | child_outcome | "malformed_child_record" | refused |
| snapshot-byte-conversion | child_outcome | "malformed_child_record" | refused |
| snapshot-time-zero | child_outcome | "malformed_child_record" | refused |
| snapshot-time-misaligned | child_outcome | "malformed_child_record" | refused |
| snapshot-counter-negative | child_outcome | "malformed_child_record" | refused |
| snapshot-cpu-null | child_outcome | "malformed_child_record" | refused |
| snapshot-cumulative-decrease | child_outcome | "malformed_child_record" | refused |
| elapsed-duration | child_outcome | "malformed_child_record" | refused |
| finite-boolean | child_outcome | "malformed_child_record" | refused |
| material-boolean | child_outcome | "malformed_child_record" | refused |
| material-map-before | child_outcome | "malformed_child_record" | refused |
| material-map-after | child_outcome | "malformed_child_record" | refused |
| fingerprint-malformed | child_outcome | "malformed_child_record" | refused |
| array-identity-name | child_outcome | "malformed_child_record" | refused |
| array-identity-illegal-f1 | child_outcome | "malformed_child_record" | refused |
| array-identity-illegal-b16 | child_outcome | "malformed_child_record" | refused |
| array-identity-big-endian | child_outcome | "malformed_child_record" | refused |
| array-identity-shape-negative | child_outcome | "malformed_child_record" | refused |
| branch-time-count | child_outcome | "malformed_child_record" | refused |
| branch-label | child_outcome | "malformed_child_record" | refused |
| backend-empty | child_outcome | "malformed_child_record" | refused |
| fft-workers-zero | child_outcome | "malformed_child_record" | refused |
| context-pid | child_outcome | "malformed_child_record" | refused |
| context-thread | child_outcome | "malformed_child_record" | refused |
| context-rlimit | child_outcome | "malformed_child_record" | refused |
| ancestor-current-null | child_outcome | "malformed_child_record" | refused |
| ancestor-current-negative | child_outcome | "malformed_child_record" | refused |
| ancestor-limit-unusable | child_outcome | "malformed_child_record" | refused |
| ancestor-domain-namespace | child_outcome | "malformed_child_record" | refused |
| optional-ancestor-missing | child_outcome | "malformed_child_record" | refused |
| retention-illegal-dtype | child_outcome | "malformed_child_record" | refused |
| retention-missing-arrays | child_outcome | "malformed_child_record" | refused |
| unprofiled-events | child_outcome | "malformed_child_record" | refused |
| profile-lone-enter | child_outcome | "malformed_child_record" | refused |
| profile-timestamp-zero | child_outcome | "malformed_child_record" | refused |
| profile-unpaired | child_outcome | "malformed_child_record" | refused |
| profile-reordered | child_outcome | "malformed_child_record" | refused |
| profile-time-misaligned | child_outcome | "malformed_child_record" | refused |
| profile-timestamps-decrease | child_outcome | "malformed_child_record" | refused |
| profile-wrong-time-index | child_outcome | "malformed_child_record" | refused |
| profile-missing-time-index | child_outcome | "malformed_child_record" | refused |
| profile-unknown-stage | child_outcome | "malformed_child_record" | refused |
| profile-highwater-decrease | child_outcome | "malformed_child_record" | refused |
| profile-highwater-exceeds-call-end | child_outcome | "malformed_child_record" | refused |
| outer-pid | child_outcome | "malformed_child_record" | not invoked |
| outer-spec | child_outcome | "malformed_child_record" | not invoked |
| outer-protocol | child_outcome | "malformed_child_record" | not invoked |
| status-unknown | child_outcome | "malformed_child_record" | not invoked |
| status-missing | child_outcome | "malformed_child_record" | not invoked |
| bootstrap-arguments | bootstrap_failure | "arguments" | not invoked |
| bootstrap-setsid | bootstrap_failure | "setsid" | not invoked |
| bootstrap-readiness | bootstrap_failure | "readiness" | not invoked |
| bootstrap-exec | bootstrap_failure | "exec" | not invoked |
| bootstrap-unknown-stage | bootstrap_failure | null | not invoked |
| bootstrap-malformed | bootstrap_failure | null | not invoked |
| bootstrap-not-object | bootstrap_failure | null | not invoked |
| bootstrap-no-prefix | bootstrap_failure | null | not invoked |
| bootstrap-second-line | bootstrap_failure | null | not invoked |
| bootstrap-bounded-prefix | bootstrap_failure | null | not invoked |
| dtype-legal-0 | legal_numeric_dtype | true | not invoked |
| dtype-legal-1 | legal_numeric_dtype | true | not invoked |
| dtype-legal-2 | legal_numeric_dtype | true | not invoked |
| dtype-legal-3 | legal_numeric_dtype | true | not invoked |
| dtype-legal-4 | legal_numeric_dtype | true | not invoked |
| dtype-legal-5 | legal_numeric_dtype | true | not invoked |
| dtype-legal-6 | legal_numeric_dtype | true | not invoked |
| dtype-legal-7 | legal_numeric_dtype | true | not invoked |
| dtype-legal-8 | legal_numeric_dtype | true | not invoked |
| dtype-legal-9 | legal_numeric_dtype | true | not invoked |
| dtype-legal-10 | legal_numeric_dtype | true | not invoked |
| dtype-legal-11 | legal_numeric_dtype | true | not invoked |
| dtype-legal-12 | legal_numeric_dtype | true | not invoked |
| dtype-legal-13 | legal_numeric_dtype | true | not invoked |
| dtype-legal-14 | legal_numeric_dtype | true | not invoked |
| dtype-legal-15 | legal_numeric_dtype | true | not invoked |
| dtype-legal-16 | legal_numeric_dtype | true | not invoked |
| dtype-legal-17 | legal_numeric_dtype | true | not invoked |
| dtype-legal-18 | legal_numeric_dtype | true | not invoked |
| dtype-legal-19 | legal_numeric_dtype | true | not invoked |
| dtype-legal-20 | legal_numeric_dtype | true | not invoked |
| dtype-legal-21 | legal_numeric_dtype | true | not invoked |
| dtype-legal-22 | legal_numeric_dtype | true | not invoked |
| dtype-legal-23 | legal_numeric_dtype | true | not invoked |
| dtype-legal-24 | legal_numeric_dtype | true | not invoked |
| dtype-legal-25 | legal_numeric_dtype | true | not invoked |
| dtype-legal-26 | legal_numeric_dtype | true | not invoked |
| dtype-legal-27 | legal_numeric_dtype | true | not invoked |
| dtype-legal-28 | legal_numeric_dtype | true | not invoked |
| dtype-legal-29 | legal_numeric_dtype | true | not invoked |
| dtype-endian-30 | legal_numeric_dtype | false | not invoked |
| dtype-endian-31 | legal_numeric_dtype | true | not invoked |
| dtype-endian-32 | legal_numeric_dtype | false | not invoked |
| dtype-endian-33 | legal_numeric_dtype | true | not invoked |
| dtype-endian-34 | legal_numeric_dtype | false | not invoked |
| dtype-endian-35 | legal_numeric_dtype | true | not invoked |
| dtype-endian-36 | legal_numeric_dtype | false | not invoked |
| dtype-endian-37 | legal_numeric_dtype | true | not invoked |
| dtype-endian-38 | legal_numeric_dtype | false | not invoked |
| dtype-endian-39 | legal_numeric_dtype | true | not invoked |
| dtype-endian-40 | legal_numeric_dtype | false | not invoked |
| dtype-endian-41 | legal_numeric_dtype | true | not invoked |
| dtype-endian-42 | legal_numeric_dtype | false | not invoked |
| dtype-endian-43 | legal_numeric_dtype | true | not invoked |
| dtype-endian-44 | legal_numeric_dtype | false | not invoked |
| dtype-endian-45 | legal_numeric_dtype | true | not invoked |
| dtype-endian-46 | legal_numeric_dtype | false | not invoked |
| dtype-endian-47 | legal_numeric_dtype | true | not invoked |
| dtype-endian-48 | legal_numeric_dtype | false | not invoked |
| dtype-endian-49 | legal_numeric_dtype | true | not invoked |
| dtype-endian-50 | legal_numeric_dtype | false | not invoked |
| dtype-endian-51 | legal_numeric_dtype | true | not invoked |
| dtype-endian-52 | legal_numeric_dtype | false | not invoked |
| dtype-endian-53 | legal_numeric_dtype | true | not invoked |
| dtype-illegal-54 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-55 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-56 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-57 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-58 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-59 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-60 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-61 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-62 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-63 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-64 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-65 | legal_numeric_dtype | false | not invoked |
| dtype-illegal-66 | legal_numeric_dtype | false | not invoked |
