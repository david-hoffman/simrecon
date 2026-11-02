# RA14 fixed full-scene experiment

The actual three-arm experiment retains poor known-input recovery and two
calibration failures. The [scientific report](../../reports/reference-alignment-ra14.md)
leads with these outcomes. This study delivers diagnostic evidence; full scientific
alignment, source recovery and resolution improvement remain unestablished.

The [prospective protocol](protocol.json) and [figure plan](figure-plan.json) were
fixed before inference. The [contract](../../contracts/reference-alignment-ra14-v1.md)
defines source units, three mandatory arms, truth separation, settings and limits.
The [source-identified recipes](reproduction.md) preserve the exact one-off numerical
construction and calls. They introduce no maintained command-line/file interface.

The original full scene uses 27 objects, detector shape 32×256×256 and source basis
32×512×512. Matched noiseless observations use Q128 and paired axial electron masses;
original noisy observations retain their Q256/finer-source generation. The comparison
does not isolate noise. Neither estimated arm passes the fixed 0.05 training-RMS gate.
The known-input source has 94.58% relative L2 error after 12 updates. A finite stop
does not establish convergence.

## Evidence inventory

- [Index and exact identities](evidence.json): public file hashes, archive identity,
  local array roots and explicit availability limits.
- [Three frozen outcomes](evidence/inference/complete.json): native command/status,
  input pinning and result-seal identities. The two input maps are the actual
  unchanged before/after maps, not reconstructed output claims.
- [Known-input native result](evidence/runs/known-noiseless/result.json),
  [estimated/noiseless native result](evidence/runs/estimated-noiseless/result.json)
  and [original estimated/noisy native result](evidence/runs/estimated-noisy/result.json):
  complete returned records, entered trials and local array shape/dtype/hash references.
- [Post-freeze evaluation](evidence/evaluation/evaluation.json): separate source,
  signal, corrected-mean and observed comparisons, all 15 residual summaries and
  original PR53 baseline.
- [All 15 image spectra](evidence/evaluation/known-noiseless-image-spectra.json),
  [source spectra](evidence/evaluation/known-noiseless-source-spectra.json) and
  [all 27 fixed-centre profiles](evidence/evaluation/known-noiseless-profiles.json).
- [Independent reduction summary](evidence/independent-reductions-summary.md),
  [detailed values](evidence/independent-reductions.json) and
  [execution receipt](evidence/independent-reductions-receipt.json): direct-array
  gauge/metric/objective/energy/profile checks; no fitting, optics, production metric
  import or new Fourier transform. This advisory observer gives no formal acceptance.
- [Calibration diagnosis](evidence/calibration-diagnosis.md): observed `ftol` stops
  and pre-audit training rejection; cause remains unresolved, with no proved defect.
- [Original timing-environment failure](evidence/evaluation-first-environment-failure.json)
  and [repeat comparison](evidence/evaluation-repeat-comparison.json): the original
  post-freeze output remains at its original path. Corrected timing access and an
  exclusive output directory changed no numerical result or inference.
- [Figure manifest](evidence/render-manifest.json) and [visual inspection](evidence/visual-qa.json):
  all nine physical-axis figures, exact color/shape display choices and limits.

The native resource records under `evidence/native/` retain real units and statuses.
Process high-water values and nested stage durations overlap; do not add them or
interpret them as isolated allocations or portable bounds. Canonical verification's
same-run reader resource measurement is separate.

## Local data and reproduction limits

The original retained archive is 1,706,228,839 bytes, SHA-256
`4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0`.
Only its 46 identified generation members were restored and matched against the
[original full-case inventory](../full-noisy-study-2026-10-26/evidence/closed-protocol-file-inventory.json).
The original public plan/seeds are unchanged.

Large raw, source, prediction and cache arrays remain locally retained under the
index's declared `artifacts/ra14/` roots. Their closed manifests retain every actual
file hash/size and native array representation. This public study does **not** supply
a complete downloadable raw-data bundle. Exact local reproduction needs those
identified inputs or separately regenerated, independently identified observations.
Original native records can name their producer checkout; those paths are provenance,
not public download links. Arrays referenced by a result record are relative to that
arm's original `artifacts/ra14/runs/<arm>/` directory.

Restore and verify the identified original generation inputs, then use the pinned
project environment and recipes to generate/seal the matched controls, prepare the
observation-only namespaces and run each fixed arm once. Never overwrite an original
attempt. Close all three inference seals before loading evaluation truth. The recorded
successful post-freeze commands use `evaluate_second.py` and `render_second.py`; their
only recipe differences from the first versions are the evaluation-directory literals.
Full-gate and final fresh-review identities belong to the sole local task state and
PR appendix outside the verified candidate bytes. Stop before RA15; no merge or
reference executable is authorized.
