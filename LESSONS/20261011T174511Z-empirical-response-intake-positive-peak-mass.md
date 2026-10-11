# Positive observed peak does not imply positive normalization mass

**Version 1.0**

- ID: 20261011T174511Z-empirical-response-intake-positive-peak-mass
- Date: 2026-10-11T17:45:11.166257+00:00
- Task: [Empirical response foundation](../docs/tasks/empirical-volume-response.md)
- Role: intake coordinator
- Topic: signed empirical normalization
- Status: confirmed
- Observation: The locator accepts a unique positive maximum in signed dc. That does not establish positive total mass. The two-sample dc [2,-3] has maximum2 and exact sum-1; [2,-1] has sum1 and a two-point normalized transfer [1,3]. Thus positive mass is a separate response-domain rule, and a transfer-magnitude bound of one cannot be inherited from nonnegative PSF preparation. These are exact algebraic examples, not measured instrument facts or numerical implementation results.
- Evidence: [Empirical response contract](../docs/contracts/empirical-volume-response-v1.md), signed domain and common-mass equations; pretest report-only scientific-advisory.md in the task's ignored evidence directory. No product experiment or formal acceptance is claimed.
- Suggested action: Independently audit signed mass and cancellation cases in A/B and preserve the entire measured zero-order shape. Do not silently impose a nonnegative-PSF magnitude bound or use peak positivity as a mass check.
