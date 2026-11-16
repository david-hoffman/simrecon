# Bound phase and assembly expression lifetimes

Rank 1 / medium. Report-only handoff; no product repair commissioned. Measured revision EA `ea9117d3efe2d8de273402d643e732140138e496`, tree `e8fe2b1b01d9e7abf476a71a2241309255bb0587`; source material35 basis `bcfbb0352618325a4363952ed2f58bd2fe0660d730b0d6138093bdbc8a22303c`. Exact evidence identities are indexed in [input-references](../input-references.json) and [attempt ledger](../analysis/attempt-ledger.json). Confidence in a source lifetime does not establish confidence in resident-memory benefit.

## Evidence and proposed mechanism

The exact workload `ws116-gp-l256-summary-searched-r1-p` is T1/D3/P5/Z8/Y256/X256, O3/L2/A1/search=true. Canonical largest summary9533 records estimation exit232312 KiB, reconstruction exit326288 KiB, result exit326288 KiB. Its full counterpart `ws116-gp-l256-full-searched-r1-p` records558684/678956/678956 KiB. All repeats and same-mode controls remain separate in the canonical largest output; these endpoints associate high-water with reconstruction but identify no individual expression. The unprofiled256 summary/full searched triples and central profiles supply the matched context.

Narrow scope: `src/simrecon/reconstruction/known_parameters.py::assemble_signed_image`, source hash `edb87b64e1691b7f437194aabc0df8d4ab22e3e67b6b05639dbd3bad26e2c645`. Inspect explicit scope/release of phase and expression temporaries while retaining operation order. Padded and inverse complex output volumes coexist through FFT; padded is already explicitly deleted before phase. Spatial is explicitly deleted after image addition. A float64 Yo×Xo phase local survives into the next iteration; the next allocation evaluates before the old local is replaced. The exponential is complex YX broadcast, not a full-volume exponential. Spatial×ramp creates a complex Vo product; its real view shares backing and scalar-times-real creates float64 Vo.

At256, copied source literals give one padded OR inverse complex volume33,554,432B and image16,777,216B. Those are individual payloads, not measured resident saving. The likely bounded opportunity is shortening a named phase lifetime and avoiding an unnecessary concurrently materialized product where identical arithmetic can be retained. A benefit ceiling for any proposed rewrite must be limited to its actual removed co-live backing(s); no saving is promised for required inverse/FFT workspace. Exact ufunc temporary release, native FFT workspace and allocator retention are unknown. Do not add unrelated estimation/retained-result payloads.

## Invariants, risks and exclusions

Preserve signed native/Nyquist placement, every-axis conjugate reflection, even/odd quadrature signs, positive centered continuous carrier ramp, order/direction/time addition order, `norm="forward"` unnormalized inverse, modulation and explode semantics, native2D plane-zero behavior with axial enlargement, omit/kz0 cases, coordinate calibration and float64/complex128 policy. An in-place or fused expression can change rounding, aliasing or finite-error location; a new mathematical rearrangement is outside this narrow lifetime proposal. Preserve readonly independent published arrays and caller immutability. Never overwrite a filtered/source volume still required by later orders.

Valid odd/even/unit extents and representation/error checks need affected public tests; do not assume primary even square geometry covers them. Failure traceback retention is a separate error-path issue. No FFT replacement, precision change, diagnostic deletion or new dependency is proposed.

## Dependencies and ranking

Rank1 because it targets the observed later high-water interval and a bounded local mechanism across full/summary, without first renegotiating result ownership. It interacts with harmonic scratch and future output preallocation: accept one isolated mechanism before attributing a combined result. Source lifetime confidence is medium; numerical-equivalence and resident-saving confidence remain unmeasured.

## Acceptance and reuse boundary

This is a recommendation, not implementation authority. Preserve the public mathematical contract and inherited scientific expectations; no tolerance, dtype, transfer-domain or size-check relaxation is proposed. First bind the later accepted source revision and recalculate affected live intervals. Functional verification must exercise the public workflow/summary entries on the frozen supplied/searched anchors, native2D, off1/off2 and between/within witnesses, time-zero carrier reuse with current-time modulation, and valid/error boundaries affected by the change. Compare same-mode public values and ownership/mutability/alias behavior; compare full/summary only on common scientific values. Include rejection/finite/representation failures rather than just successful primary shapes.

Resource acceptance requires matched fresh-process old/new triples on identical declared materials and source-specific environment/resource grants, caller retained, plus affected central/largest profile controls and raw terminal/self/sample/time scope preservation. Do not subtract a pre-call baseline, infer a saving from array arithmetic or select only favorable repetitions. Report all outcomes/ranges/medians, native unknowns and observer perturbation; a zero terminal-RSS improvement is a legitimate result. No threshold or expected percentage is invented here. Exact final gates/reviews remain required.

Later #117/#118 changes require revision-specific affected liveness, measurement and observer refresh and fresh review before #119/#120 reliance. Original #116 measurements remain EA evidence, not a certificate obtained by restacking a newer base. Dependencies below are mechanism interactions, not permission to combine unreviewed numerical changes.

