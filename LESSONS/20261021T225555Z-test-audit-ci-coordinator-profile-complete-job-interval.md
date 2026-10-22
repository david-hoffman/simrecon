# Profile the complete required-job interval

**Version 1.0**

- ID: 20261021T225555Z-test-audit-ci-coordinator-profile-complete-job-interval
- Date: 2026-10-21T22:55:55.308035+00:00
- Task: test-audit-linux-ci
- Role: coordinator
- Topic: CI timing
- Status: confirmed
- Observation: The first standard twelve-shard Ubuntu run passed every job but took 355 seconds from the first required job start to the last required job completion. Its critical path was 96 seconds of preparation, a 2-second wait, a 182-second slowest shard, another 2-second wait, and 73 seconds of finalization. Preparation included 47 seconds of type checking. Shard test steps ranged from 62 to 142 seconds under the initial count-based timing input. More jobs alone did not meet the owner's strict 300-second target.
- Evidence: [Run39688634685, attempt1](https://github.com/david-hoffman/simrecon/actions/runs/39688634685), candidate bffeb97c067b7d5de9a434de5ba7521b64e9525c; retained native jobs at artifacts/test-audit-ci/standard-ci/ubuntu-run/metadata/jobs.json. The calculation is 96 + 2 + 182 + 2 + 73 = 355 seconds. Initial queue time is separate; uploads and post-job completion remain included.
- Suggested action: Use original stage timings to select ordinary scheduling changes. Concurrent quality checks and measured immutable pytest-split inputs are the next candidate. Re-measure its complete interval; summed test durations do not prove elapsed-time savings or final readiness. This lesson authorizes no gate, test or policy change.
