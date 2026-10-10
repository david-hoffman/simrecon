# VOLUME-OTF-01: sampled 3D intensity PSF preparation

**Version 1.0.** Git versions revisions.

The owner requested the next coherent unmet implementation slice stacked above verified PR #16, plus publication, all configured push/PR checks and a fresh successor when more implementation remains. The [concrete contract](../contracts/volume-otf-preparation-v1.md) defines `prepare_volume_otf` / `Otf3D`. This is normalized finite-volume intensity-PSF preparation, with explicit sampling/origin and full complex transfer. It does not supply order-specific physical 3D SIM calibration.

Baseline: PR #16, `codex/volume-phase-separation`, head `cdf4a0745d6b9681e371b006db60239f3f5af0f9`, tree `2864cf6dea57bc91c7fa15c6051ff0c801d860f3`, live verified October 8, 2026. Dedicated managed worktree and branch: `codex/volume-otf-preparation`. This is authorized stacked delivery, not owner integration.

Route: high-risk scientific/numerical/custom-oracle. Fresh native blind A owns `tests/test_volume_otf.py` and any explicitly named new volume-OTF fixture; fresh native blind B reviews exact tests and independently challenges oracles/omissions. Restricted fresh C owns the new volume-OTF runtime module, public exports and named usage/comparison documents. Fresh native D reviews the exact passing candidate. Existing tests/fixtures, workflows, dependencies, discovery, coverage and delivery policy are outside C's ownership. Default model/effort for A/B/C/D is `gpt-6.1-sol` high; scoped sticky-judgment advisors use requested `gpt-6-astra` ultra and replace no required role.

Checks: cheap locked per-worktree preflight; narrow test static checks and source-free public-entry probes; focused accepted tests; canonical exact-candidate `make verify`; fresh D; all configured Ubuntu 24.04/macOS 15 push and pull_request matrix legs. Inherit PROJECT's behavior/risk review plus complete native JSON/HTML report integrity, advisory percentages, no selected numeric target and no exclusions. U01–U29 inventory normal operation, invalid input, representation range, failure, compatibility and docs; A maps distinct scenarios and equivalent examples for B's audit.

No numeric scenario/review/repair/time/execution limits were set. Merge, release and unrelated external messages are not authorized. Missing metering is unknown.

## Current state

One task-local coordinator record, `artifacts/volume-otf-execution/execution-record.json`, holds current status, exact candidate/checkpoint/input identities, role/check verdicts, classified corrections/blockers, cumulative attempts and measured metrics. Final candidate hashes and check results remain outside tracked bytes. That record links the prior PR #16 execution record and its earlier chain without resetting or recounting prior attempts/spending. Raw role packets/events/reports and numerical/local/CI evidence remain beside it. Blind roles receive only narrow public packets, never the coordinator record or implementation-bearing task history.
