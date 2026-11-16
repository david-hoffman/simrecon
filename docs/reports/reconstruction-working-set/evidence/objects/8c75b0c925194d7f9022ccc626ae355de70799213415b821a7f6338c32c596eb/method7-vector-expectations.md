# Method7 F1/F2 finite control expectations — unexecuted source

Exactly68 finite vectors:45 prior examples re-authored with coherent explicit sample and owner nanosecond timestamps plus23 affected regressions (15 timestamp/origin,8 readiness). Original45 fixture56226bf9/results/pass remain unchanged in preserved evidence; this new fixtureb588cb16/protocol is not a relabelled execution. All times use a +1second abstract baseline; sample0ms means1000000000ns, never an invented real zero timestamp.

The actual corrected monitor helper supplies origin/deadline/outcome/stop. Actual readiness helper raises StartupError with distinct late evidence; actual main exception-status helper supplies its classification. Normal terminal cases still call the actual existing child/bootstrap parsers and final-status helper. No copied implementation determines observed values. Every expected object below is literal fixture source; any mismatch is failed qualification.

| Vector | Origin ns | End ns | Gap outcome | Latched stop | Exception | Terminal | Final helper status | Late readiness primary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valid-RSS-nonterminal | none | none | none | none | none | false | not called | none |
| measured-zero-terminal | none | none | none | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| immediate-terminal | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| delayed-terminal | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| terminal-exact-bound | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| terminal-after-bound | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| null-RSS-expires | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| missing-RSS-expires | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| negative-RSS-expires | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| boolean-RSS-expires | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| text-RSS-expires | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| RSS-returns-no-terminal | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| RSS-returns-terminal-within-bound | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| wait-ownership-loss | 1000000000 | 1050000000 | ownership_lost_or_collection_interrupted | none | RuntimeError | false | not called | none |
| immediate-wait-ownership-loss | 1000000000 | 1050000000 | ownership_lost_or_collection_interrupted | none | RuntimeError | false | not called | none |
| nonterminal-notifications-not-success | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| supported-interrupt-propagates | 1000000000 | 1050000000 | ownership_lost_or_collection_interrupted | none | KeyboardInterrupt | false | not called | none |
| deadline-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | timeout | none | true | timeout_stopped | none |
| startup-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | startup_readiness_timeout | none | true | startup_timeout_stopped | none |
| host-low-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped | none |
| host-unknown-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped | none |
| ancestor-high-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | cgroup_current_threshold_or_unknown | none | true | monitor_stopped | none |
| ancestor-unknown-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | cgroup_current_threshold_or_unknown | none | true | monitor_stopped | none |
| cgroup-moved-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | child_cgroup_missing_or_moved | none | true | monitor_stopped | none |
| cgroup-missing-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | child_cgroup_missing_or_moved | none | true | monitor_stopped | none |
| RSS-threshold-on-return-precedence | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | process_current_RSS_threshold | none | true | monitor_stopped | none |
| independent-stop-remains-latched | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped | none |
| deadline-crossed-during-collect | 1000000000 | 1050000000 | strict_required_RSS_failure | timeout | none | true | timeout_stopped | none |
| confirmation-bound-crossed-during-collect | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| confirmed-terminal-later-host-stop | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped | none |
| expired-RSS-never-reclassified | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| status-normal-finite | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| status-nonzero-finite | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_nonzero_exit | none |
| status-signal-finite | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_signaled | none |
| status-malformed-child | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | malformed_child_record | none |
| status-missing-child | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | missing_child_record | none |
| status-oversized-child | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_record_exceeds_admitted_parse_bound | none |
| status-nonfinite-child | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | nonfinite_scientific_failure | none |
| status-material-child | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | material_identity_failure | none |
| status-workflow-exception | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | workflow_exception_unclassified | none |
| status-observation-failure | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_observation_failure | none |
| status-identity-mismatch | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | material_identity_failure | none |
| status-bootstrap-exec-error | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | bootstrap_exec_failure | none |
| status-bootstrap-setsid-error | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | bootstrap_setsid_failure | none |
| terminal-collected-before-bound-late-guard-refresh | 1000000000 | 1050000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| sample0-entry60-collection70-refused | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample0-entry60-nonterminal-refused | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called | none |
| sample10-entry20-collection60-endpoint | 1010000000 | 1060000000 | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification | none |
| sample10-entry20-collection61-refused | 1010000000 | 1060000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-missing-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-null-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-zero-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-negative-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-boolean-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-fractional-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-text-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-future-refused | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| sample-timestamp-regression-refused | 1000000000 | 1050000000 | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| invalid-origin-never-repaired | none | none | invalid_sample_timestamp | required_process_RSS_observation_lost | none | true | monitor_stopped | none |
| invalid-origin-host-stop-precedence | none | none | invalid_sample_timestamp | host_headroom_missing_or_deteriorated | none | true | monitor_stopped | none |
| readiness-on-time-no-stop | none | none | none | none | none | false | not called | none |
| readiness-at-startup-deadline | none | none | none | startup_readiness_timeout | StartupError | false | startup_timeout_stopped | startup_readiness_timeout |
| late-readiness-no-prior-stop | none | none | none | startup_readiness_timeout | StartupError | false | startup_timeout_stopped | startup_readiness_timeout |
| late-readiness-preserves-host-after-terminal | none | none | none | host_headroom_missing_or_deteriorated | StartupError | true | monitor_stopped | host_headroom_missing_or_deteriorated |
| late-readiness-preserves-ancestor | none | none | none | cgroup_current_threshold_or_unknown | StartupError | false | monitor_stopped | cgroup_current_threshold_or_unknown |
| late-readiness-preserves-cgroup | none | none | none | child_cgroup_missing_or_moved | StartupError | false | monitor_stopped | child_cgroup_missing_or_moved |
| late-readiness-preserves-expired-RSS-after-terminal | 1000000000 | 1050000000 | strict_required_RSS_failure | required_process_RSS_observation_lost | StartupError | true | monitor_stopped | required_process_RSS_observation_lost |
| late-readiness-preserves-overall-deadline | none | none | none | timeout | StartupError | false | timeout_stopped | timeout |

The JSON fixture also requires exact full late-readiness evidence (observed/deadline/prior/primary/ready values), wait-ownership-loss flags and nonterminal notification counts. Native waits, signals, physical resource probes and workload children are absent; all owner/sample events are explicitly fake. This does not reproduce live races/readiness pipes/cleanup or qualify a real corpus row. Proposed unique attempt method7-rss-readiness-controls-a1, pure -I-S-B command and approved=false template require coordinator inspection/freeze/release before execution; fresh affected review7 and a new clean basis/root window/per-case grant remain required for any workflow retry.
