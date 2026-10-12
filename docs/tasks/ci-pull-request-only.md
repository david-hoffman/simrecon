# Pull request only CI verification

The owner requested: “Remove running ci on push, it should only run on pr”.

This bounded infrastructure task removes the push event from `.github/workflows/verify.yml`. The pull request event retains the complete verification jobs on Ubuntu 24.04 and macOS 15. Local `make verify`, workflow jobs, actions, permissions, dependencies, test discovery and coverage controls remain unchanged.

The baseline is the completed raw point-bead calibration prerequisite. The worker owns only the workflow and this task pointer. The coordinator obtains fresh independent bounded review before publication; this task authorizes no merge or release.

One Current state and cumulative task accounting live in ignored `artifacts/ci-pr-only-20261011/`. Exact candidate, input identities, focused workflow evidence, full local receipt and review verdict stay outside tracked candidate bytes. Prior roadmap accounting remains linked without reset or double counting. No numeric scenario, review, correction or execution limit was set by the owner. Model, token, cost and unavailable timing measurements remain unknown when not observed.
