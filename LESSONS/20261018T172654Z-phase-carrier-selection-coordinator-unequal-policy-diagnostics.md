# Equal eligible diagnostics cannot distinguish ranking

**Version 1.0**

- ID: 20261018T172654Z-phase-carrier-selection-coordinator-unequal-policy-diagnostics
- Date: 2026-10-18T17:26:54.103866+00:00
- Task: PHASE-CARRIER-SELECTION
- Role: coordinator observing blind B01
- Topic: public policy test discrimination
- Status: confirmed
- Observation: B01 found that duplicate/aliased eligible rows with equal residuals could not distinguish complete policy filtering from retaining only minimum-residual ties. The existing distinct row was nonstationary. B's real public probes produced stationary rows with unequal residuals, and a second transfer/input group produced unequal phase ranks. Both must remain eligible under the same loose caller limits. B also found that nonnegative-only work checks allowed every informative counter to be zero. These are test omissions, not demonstrated product defects.
- Evidence: proposed checkpoint f4d8c9ce7f4a68bf349d079f1142bfe19a0e7a97; artifacts/phase-carrier-selection-20261018/B01/review.md and original native initial01 lifecycle; sanitized public findings at A03/public-findings-correction01.md. Current locked Python3.13.12/NumPy2.5.3/SciPy1.18.1.
- Suggested action: For a no-ranking policy, include real eligible rows whose ranking diagnostics differ. For work-report preservation, require meaningful observed work without inventing a universal backend count. Route scientific tests through their blind author and fresh independent reviewer; this lesson supplies no edit or acceptance authority.
