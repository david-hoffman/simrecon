# Method6 deterministic control expectations — source only

Current command enters only pure_method6 under -I -S -B and a specific approved
pure-stdlib grant after coordinator freeze. It skips generic Git/admission/
preflight/context/local_safety and denies spawn/signal/wait/resource/scientific
effects. Root permits these controls before review; workflow retry still requires
fresh affected review, new clean basis and exclusive per-case release. Nothing
semantic has executed in this source preparation; fixture45 is unchanged.

Exactly45 finite fake-owner/clock/sample vectors, no semantic execution yet. Source fixture provides all scalar inputs and literal expectations. Actual corrected monitor_sample_decision latches stops; actual observed_child_status and child_outcome/bootstrap_failure supply statuses. No copied classifier determines observed outcomes. Synthetic reaped timestamps are declared fake-owner collection points, not native measurements. Signals/native waits/workload children are0 by construction, not live kernel qualification.

| Vector | Gap outcome | Latched stop | Exception | Terminal | Final actual-helper status |
| --- | --- | --- | --- | --- | --- |
| valid-RSS-nonterminal | none | none | none | false | not called without terminal |
| measured-zero-terminal | none | none | none | true | complete_child_observed_pending_scientific_qualification |
| immediate-terminal | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |
| delayed-terminal | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |
| terminal-exact-bound | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |
| terminal-after-bound | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped |
| null-RSS-expires | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| missing-RSS-expires | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| negative-RSS-expires | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| boolean-RSS-expires | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| text-RSS-expires | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| RSS-returns-no-terminal | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| RSS-returns-terminal-within-bound | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |
| wait-ownership-loss | ownership_lost_or_collection_interrupted | none | RuntimeError | false | not called without terminal |
| immediate-wait-ownership-loss | ownership_lost_or_collection_interrupted | none | RuntimeError | false | not called without terminal |
| nonterminal-notifications-not-success | strict_required_RSS_failure | required_process_RSS_observation_lost | none | false | not called without terminal |
| supported-interrupt-propagates | ownership_lost_or_collection_interrupted | none | KeyboardInterrupt | false | not called without terminal |
| deadline-precedence | terminal_confirmed_with_visible_sampling_gap | timeout | none | true | timeout_stopped |
| startup-precedence | terminal_confirmed_with_visible_sampling_gap | startup_readiness_timeout | none | true | startup_timeout_stopped |
| host-low-precedence | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped |
| host-unknown-precedence | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped |
| ancestor-high-precedence | terminal_confirmed_with_visible_sampling_gap | cgroup_current_threshold_or_unknown | none | true | monitor_stopped |
| ancestor-unknown-precedence | terminal_confirmed_with_visible_sampling_gap | cgroup_current_threshold_or_unknown | none | true | monitor_stopped |
| cgroup-moved-precedence | terminal_confirmed_with_visible_sampling_gap | child_cgroup_missing_or_moved | none | true | monitor_stopped |
| cgroup-missing-precedence | terminal_confirmed_with_visible_sampling_gap | child_cgroup_missing_or_moved | none | true | monitor_stopped |
| RSS-threshold-on-return-precedence | terminal_confirmed_with_visible_sampling_gap | process_current_RSS_threshold | none | true | monitor_stopped |
| independent-stop-remains-latched | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped |
| deadline-crossed-during-collect | strict_required_RSS_failure | timeout | none | true | timeout_stopped |
| confirmation-bound-crossed-during-collect | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped |
| confirmed-terminal-later-host-stop | terminal_confirmed_with_visible_sampling_gap | host_headroom_missing_or_deteriorated | none | true | monitor_stopped |
| expired-RSS-never-reclassified | strict_required_RSS_failure | required_process_RSS_observation_lost | none | true | monitor_stopped |
| status-normal-finite | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |
| status-nonzero-finite | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_nonzero_exit |
| status-signal-finite | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_signaled |
| status-malformed-child | terminal_confirmed_with_visible_sampling_gap | none | none | true | malformed_child_record |
| status-missing-child | terminal_confirmed_with_visible_sampling_gap | none | none | true | missing_child_record |
| status-oversized-child | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_record_exceeds_admitted_parse_bound |
| status-nonfinite-child | terminal_confirmed_with_visible_sampling_gap | none | none | true | nonfinite_scientific_failure |
| status-material-child | terminal_confirmed_with_visible_sampling_gap | none | none | true | material_identity_failure |
| status-workflow-exception | terminal_confirmed_with_visible_sampling_gap | none | none | true | workflow_exception_unclassified |
| status-observation-failure | terminal_confirmed_with_visible_sampling_gap | none | none | true | child_observation_failure |
| status-identity-mismatch | terminal_confirmed_with_visible_sampling_gap | none | none | true | material_identity_failure |
| status-bootstrap-exec-error | terminal_confirmed_with_visible_sampling_gap | none | none | true | bootstrap_exec_failure |
| status-bootstrap-setsid-error | terminal_confirmed_with_visible_sampling_gap | none | none | true | bootstrap_setsid_failure |
| terminal-collected-before-bound-late-guard-refresh | terminal_confirmed_with_visible_sampling_gap | none | none | true | complete_child_observed_pending_scientific_qualification |

The nonterminal-notifications vector must retain2 fake nonterminal events; wait-loss vectors must set wait_ownership_lost=true. Every other vector expects0 notifications and false wait-loss. Interrupt is an expected propagated KeyboardInterrupt; real main cancellation/cleanup classification is reviewed source, not falsely claimed executed by this fake helper control. Collection at the50ms endpoint is inclusive; unresolved/nonterminal at that endpoint fails strictly. The late-guard-refresh vector confirms a cached sole-owner terminal collected at40ms even though guard decision occurs at60ms; independent deadline/host/ancestor/cgroup guards still use actual decision time/sample and retain stop precedence. Returning RSS cannot clear an expired gap or its latched stop.
