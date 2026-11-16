# WS116 independent affected scientific-method review 6

**Verdict: NOT SUITABLE for a separately admitted real retry on these exact bytes.** Two concrete affected-method findings require author correction. The existing 45/45 pure-control pass is valid within its stated helper/parser scope; it does not cover either main-wiring defect below. This is neither a full scientific report review nor product/gate acceptance.

## Exact identity and review conditions

Reviewed `/workspace/work/issue-116` against packet SHA256 `a8a661902752d73eee6f4cf496aca7d29ff1d055e0569bb12a0ce919f8ecc00e`. The ten-target manifest SHA256 is `22ebb141345a467ba3155a8afdaa407b4021ae81a723bb4f5089ddcee9ba38b1`; all ten current targets and corresponding `source-method6-pure-frozen/` files independently matched it. In particular:

- Runner: `d530ff54b8f0695c32854a8fbc40ac868f91fc92c3a827feb2299a85b50f0f25`.
- Qualifier: `d88a72600774dd57c819bf5eeeed4d87126e4e3095ca731ddcc0baf94eb6bf22`.
- 45-vector fixture: `56226bf97df96cfd2321c4ea96832733f229769150d9d1aaa8e23841bef52ba5`.

I read AGENTS, relevant PROJECT instructions, review-work, model-selection and role-launch guidance in the commissioned narrow scientific-method mode. This fresh session received the packet, not author conversation history; no delegation occurred. Requested configuration is gpt-6.1-sol/high. Actual served model, tokens and monetary cost are unknown. Optional memory-disable and per-role filesystem sandbox controls are unavailable; shared filesystem and prompt restrictions establish no engineered isolation or scientific calibration.

Work consisted only of source/text reads, hashes, JSON comparisons and AST source-segment comparisons. No target imports, semantic controls, tests, numerical/product execution, installations, native probes or repairs were performed. Historical HEAD is not treated as the identity of this dirty source target.

## Findings requiring affected correction

### F1 — High: the confirmation interval starts after the first actual RSS observation

Source: `run_attempt.py:360–368` and `1010–1027`; relevant unchanged dependency `observer.py:383–405`. The packet and qualification-plan require the fixed 50 ms interval to begin with the first actual unusable required RSS observation. `process_sample` already records `sample["monotonic_ns"]` after reading/parsing the child status and before host observation. Main then performs host/cgroup/ancestor reads, JSON serialization, write/flush and another parent-cgroup read before calling `monitor_sample_decision`. That helper ignores the sample timestamp and sets both start and deadline from its later `clock()` call.

Consequently, delay before helper entry extends the acceptance interval. A source-derived counterexample is an invalid sample timestamp at t=0 ms, helper entry at t=60 ms after those operations/scheduling, and sole-owner terminal collection at t=70 ms. With otherwise healthy guards and sufficient overall/startup deadlines, the code confirms against [60,110] ms although collection is outside the required [0,50] ms interval. This is an acceptance-bound error, distinct from an allowed late decision or scheduling overshoot. It was not executed here and is not asserted to explain the original trial.

The controls cannot detect this: their injected `before` clock is the gap origin, while the frozen base sample's `monotonic_ns` remains the unrelated literal 1. They exercise collection/decision separation after helper entry, not sample-to-helper delay.

Required remedy: bind the immutable gap origin to the actual first unusable observation timestamp and retain helper/decision times separately. Delayed logging/guard work must not move the terminal acceptance endpoint. Preserve inclusive collection at origin+50 ms, cached owner timestamp authority, and strict late collection. Review the affected timing/control expectations rather than treating the present 45/45 pass as proof of this wiring.

### F2 — Medium: late readiness overwrites the earliest independent stop

Source: `run_attempt.py:960–967`, with the new latching in `monitor_sample_decision:377–379,424–426` and main `1030–1035`. If an iteration before session readiness observes an independent host/ancestor/RSS/cgroup stop, it latches that reason and can send TERM. On the next iteration, buffered readiness may become available after the startup deadline, including after terminal collection. The direct assignment at line 966 replaces the earlier `stop_reason` with `startup_readiness_timeout` before raising.

This violates the specified earliest-observed-stop precedence. It changes primary failure classification to `startup_timeout_stopped`; it does not create normal success, and any earlier gap diagnostic may still retain the original independent stop. This assignment predates method6, but remains a reachable dependency of the newly claimed latching policy and main integration.

The fake controls call the decision/status/parser helpers; they do not run `launch.drain()` or this main readiness branch. `independent-stop-remains-latched` therefore does not cover the overwrite.

Required remedy: preserve an existing stop reason when late readiness is observed, while retaining explicit late-readiness failure evidence and a failed final status. Diagnose/verify this bounded precedence path through the authorized affected correction route; no blanket lifecycle rerun follows solely from this finding.

## What the inspected evidence does establish

Actual receipt SHA256 `5d7f96701e749126d0dbc5df2eb380f36c210a4147aceb183ac268c53dc5870d` and results SHA256 `c58ecc47cc5bcef9f19a7ca8dbf62be44313a6b2446c050ecec7f37e353dabed` matched the packet. I independently compared all 45 unique IDs in fixture order, every literal expected object and every recorded observed object: all match. All 14 source bindings still match. The 90 artifact entries all matched their recorded hashes; index SHA256 is `005026a2ee0cc104649f9bf0422c2bece18bae197c8782ced7a116da459b9bda`. Coordinator supplement SHA256 is `94459905b3d10f086a88fcc211b8f3231fabe33b29da3122d4acafe84e7adba9`; it records driver exit 0 and exact driver PID/FD absence, which I did not newly probe.

The actual controls support the helper's within-bound/exact-bound/late owner collection, strict expiry despite returning RSS, zero as a valid measured RSS, expected wait-loss/interrupt propagation, independent guard precedence and finite/negative child parsing/status results. The cached 40 ms terminal with 60 ms decision vector correctly separates owner collection time from later decision time. Main's cached-terminal path retains child fields and separately labels refreshed host/ancestor facts. Terminal-top overall timeout uses `setdefault`. Malformed guard numeric reads raise into failed observation handling rather than being converted into success. The extracted final-status order matches the old inline order: bootstrap, monitor stop, signal, parse refusal, material, nonfinite, workflow, observation, nonzero, then complete pending qualification. Neither bootstrap precedence nor a confirmed gap removes a recorded stop to produce success.

Source inspection confirms pure entry returns before generic admission/Git/preflight/context/local_safety and generic finally. Exact -I/-S/-B, fourteen-input identities, finite bounds, fake owner/clock/sample and actual decision/status/parser calls are used. Effect denials and the audit hook leave blocked attempts fatal even when an expected negative vector catches RuntimeError; the recorded blocked list is empty. These are in-process tripwires, not an OS sandbox. Valid negative protocol outcomes differ from qualification expectation failures; the latter remain failed qualification.

I independently matched the four exact AST source segments against preserved old runner `1e554fdadffdfc54cbc14758e072224db5cd278f1e7b7e91b813c11c65b5fd61`: WaitOwner `882bfb1514954876f2304cb8e16b6d8fa867fdfba252a7f721973a36c08b388e`, cleanup `14727eb898f6d0629cd2ed029c50a91cc9c4c3334c1587752d6a5feda410a92d`, child_outcome `3cf8d8bd0229b9fb53f3239acd94365fdaaa89bc0d3ae715a2630ad541bebbb5`, validate_complete_record `89ba1a7f3b59e09498d1da0795688842f0608ab5133c1430e72b93f4ce193077`. All seven recorded historical receipt hashes/statuses and their enumerated unchanged current-input subsets matched. Applicability remains Q1/Q2 unchanged WaitOwner/cleanup/fixed launch only; Q4 unchanged parser/bootstrap/dtype only; Q5 unchanged observer array/finite/frozen public-value protocol only. No whole old runner/module, monitor, main or new final-status qualification is reused.

## Preserved failure and remaining limits

I read the preserved first-trial receipt and finite child: hashes remain `ea1132b9b6d5705768c3efaecb5e02d4d332de9e3186317d1809fb8558f1fee5` and `c95aa88eba27d90374ecde2d284183c8752814cfd60c8440f3cea600c1a91dd7`; preservation manifest is `1d50d08b9ea1bbf2610badca3fd9d81f91705ec98e68277de3d16dc4e72522a8`. It remains **monitor_stopped / required_process_RSS_observation_lost**, despite later sole wait4 exit 0 and finite child output. Old source already polled after sample writing and again before signal delivery. Exact negative-poll instants and cause remain unknown. Its 78,820 Linux KiB / 80,711,680 B native high-water is failed-trial context, not an accepted corpus statistic.

The pure pass supplies no live exit-race, OS wait/signal, readiness/close/cleanup, resource-admission or numerical proof. Terminal wait4 means kernel-reported direct-child usage through exit; inherited/pre-exec/exec-transition high-water retention remains UNKNOWN. Same PID is no preservation guarantee. No isolated-workflow, aggregate/subtraction or peak-benefit claim follows. Sampling gaps limit association without establishing their cause. Q3 abrupt loss/startup variants retain their explicit gaps; no orphan or new cleanup topology is authorized.

All five prior reviews, launches, source-preparation/control corrections, check failures and charges remain preserved; this is review launch 6. Supplied historical preparation14/execution9/total23 is a handoff-time count, not revised metering of this review or the later actual control invocation. Missing model/usage/cost remains unknown. Both findings must be resolved before affected-source suitability can be granted. Even a later suitable verdict would require a new clean numerical basis, exclusive root window and exact per-case release before a real retry; workflows/retries/profiles/growth remain HELD. No full scientific report or full-local gate acceptance is given.
