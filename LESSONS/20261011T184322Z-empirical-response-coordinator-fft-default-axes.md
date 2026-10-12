# FFT sizes change the default transformed axes

**Version 1.0**

- ID: 20261011T184322Z-empirical-response-coordinator-fft-default-axes
- Date: 2026-10-11T18:43:22.841427+00:00
- Task: [Empirical response](../docs/tasks/empirical-volume-response.md)
- Role: coordinator observing fresh blind B02 evidence
- Topic: public transform observers
- Status: confirmed
- Observation: On NumPy2.5.3, fftn(a, s=(2,3,4)) for shape(3,2,3,4) transforms the last three axes and equals an explicit axes=(-3,-2,-1) call. An observer that interprets axes=None as every dimension falsely rejects permitted batching. The emitted DeprecationWarning preserves current supported behavior. A separate restoration observer also confused an untransformed length-two batch axis with a spatial axis until corrected.
- Evidence: [B02 source-free reproduction and exact checkpoint26d7b167d53b7e82a9cf6a2760c55d6ada28ccd3](../artifacts/empirical-signed-response-20261010/B02/final.txt); [A02 correction02 callback audit/probe](../artifacts/empirical-signed-response-20261010/A02-correction-02/report.md). Python3.13.12/NumPy2.5.3/macOS27arm64; installed source-free harness with300s timeout. [NumPy public fftn defaults](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html). Ignored detailed evidence stays local.
- Suggested action: Audit every owned transform callback against the public s/axes binding rules. Probe permitted separate, grouped, batched and permuted call forms while preserving independent numerical assertions. This observation supplies no new scientific requirement, edit authority or budget.
