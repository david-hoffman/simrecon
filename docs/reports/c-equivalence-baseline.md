# Where the C-equivalence baseline was lost

**Version 1.0 — static audit, 2 November 2026.**

No inspected PR establishes a complete mathematically C-equivalent reconstruction. The last pre-reconstruction foundation is [PR #7](https://github.com/david-hoffman/simrecon/pull/7), merged commit `1fd3c7e7b76cfd303f7850c8542e2d70da88f58a`, tree `5bc2acd5f6787039ec89c0a8c69a2cadf38e5b91`. Calling it the last correct **complete port** would be false.

The earliest unambiguous reconstruction difference is [PR #8](https://github.com/david-hoffman/simrecon/pull/8), merged commit `5e231d3d27dfd843de776de5ac80d3d46c0c5727`. Its [original contract](../contracts/known-parameter-reconstruction-v1.md) bilinearly interpolates unfiltered bands and transfers, then forms a reconstruction quotient. C `sirecon.c:2093–2310,2334–2493` filters native band coefficients and then relocates them through Fourier embedding, inverse transforms and centered spatial phase ramps. Those operations do not commute in general.

A one-dimensional counterexample exposes the ordering difference without executing either implementation. For two native samples `B=(1,1)`, `H=(1,2)` and squared regularizer `w²=1`, native filtering gives `(1/2,2/5)`, whose midpoint is `9/20=0.45`. Interpolate first: `B=1,H=3/2`, giving `(3/2)/(9/4+1)=6/13≈0.461538`. This is an ordering discriminator, not a full simulation of C's phase-ramp relocation. It proves that moving an interpolation through this quotient is not an identity.

PR #7's normalized discrete Fourier transform and the phase least-squares primitive remain useful mathematical facts. For the corresponding full-rank phase designs, Python `dc,c_m` and C coordinates satisfy `B0=P*dc`, `Bplus_m=P*conj(c_m)`. That conditional mapping does not establish identical phase construction, numerical rank/rejection rules, stored Nyquist handling, radial OTF preparation or a complete reconstruction. Accordingly the removal contract does not preserve those old APIs merely because their names look appropriate.

The RA chain did not repair this at its integration boundary:

| Checkpoint | Actual evidence and limitation |
|---|---|
| PR #55 / RA01 | Freezes comparison inputs and claims; adds no equivalent solver. |
| PR #57 / RA02 | Tests existing finite periodic formulas and equality under a specially matched metric/source subspace. That is not universal C equivalence. |
| PR #58 / RA03 | Adds valuable fixed-source mismatch diagnostics, but retains the earlier divergent tree. |
| RA04–RA10 | Add camera, calibration, covariance, finite-boundary, carrier and phase operations with independently selected scientific semantics. Closer individual Fourier identities do not prove the C algorithm. |
| PR #67–69 / RA12–13 | Contracts explicitly choose the inherited physical specimen fitter. RA13 forbids substituting the newer stage models. |
| PR #70 / RA14 | Executes that path and reports poor recovery; does not establish reference alignment. |

The owner's requirement was mathematical identity. Later contracts selecting other estimators did not waive it. The failure was in preserving that requirement through decomposition, tests, review and integration; it was not caused by a requirement for bitwise identity or by Python itself.

The actual removal PR targets merged PR #54, `8f6b35ceda362944f00de44acbf7098989f157e4`, tree `0c806071b04528b67044d90e6131ff1b1dccc9b7`. It explicitly deletes current scientific alternatives while preserving neutral infrastructure and historical evidence. A branch from PR #7 opened against current main would otherwise omit the intended deletions from its merge-base diff. Open RA branches are preserved but do not become dependencies of the replacement stack.

Source inspection used retained SVN revision 307, with file hashes recorded in the task evidence. `Makefile:55` identifies `sirecon` as reconstruction and `radialft` (`mainfile.c`) as the 3D OTF producer; they are distinct programs. No C binary, build, link, import, scientific rerun or owner-output comparison was used. Exact old C invocation/settings/outputs remain unavailable. The static conclusion that the algorithms differ is high confidence; PR #7 as the economical historical restart boundary is a reasoned choice, not a newly issued correctness certificate.

Primary materials opened in this audit: GitHub PR metadata for #7, #8, #54, #55, #57, #58 and #70; original PR #8 contract via `git show`; retained C source; immutable RA14 contracts and the earlier source-comparison evidence. The [common target contract](../contracts/c-equivalence-common-v1.md) defines how these limits constrain the rebuild.
