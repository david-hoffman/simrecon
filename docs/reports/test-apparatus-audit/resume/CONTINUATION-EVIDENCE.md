# Retained continuation evidence

This evidence directory is a nonblind archival packet. Do not send its raw
measurement summaries, coverage reports, nonblind discovery material or combined
index to blind scientific roles. Their authorized sanitized packets remain
separate. The sole task state is the coordinator's task record; this file records
retained evidence and its limits, not a competing readiness state.

Original discovery, earlier resumed archives and all ignored raw artifacts remain
untouched. Newly selected reports/numeric summaries use deterministic gzip with
mtime 0. `continuation-files.json` identifies exact selected source bytes and
portable archive hashes. It is a selection journal. After the coordinator froze the completed selection,
the README and manifest were refreshed to include it. The coordinator's refreshed
`preservation-inputs.json` and `change-accounting.json` are retained without
alteration and included in the final manifest.

## Observed full runs

| Run | Exact commit | Outer wall, seconds | Pytest wall, seconds | Native cases | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Baseline | edcf53b5d5c0f494c388944d3cfda5c04b9fda97 | 2287.89 | 2243.177 | 3087 | 13 phases passed |
| Candidate 1 | a41b378b10681c83029dd6f27fe3df65d66b22f2 | 829.59 | 783.316 | 3066 | 13 phases passed; 600-second goal unmet |
| Candidate 2 | 8b9c39f7ea458a21c5feed39775005dc8cf487bd | 611.04 | 564.184 | 3066 | 13 phases passed; goal missed by 11.04 seconds |

Candidate 1 is historical evidence for that commit, not verification of later
A3/A4/A5 inputs. Its pre-existing compressed console, JUnit, time, receipt, M25
and coverage JSON were decompressed and compared byte-for-byte to the preserved
same-run raw inputs. Its compact identity, 3066 passing/no-error/no-skip cases,
M25 and global coverage were checked against the same-run receipt. Existing
compressed bytes were not rewritten. The new compact profile summary retains
resource totals, successful-exec counts and top printed durations without
copying its 20 MB raw execve trace or full catalogs again.

Candidate 1 retains 4783/4919 statements and 1845/1952 branch destinations,
with no exclusions; same-run M25 is baseline=peak=101792 KiB, increment 0 bytes,
limit 33554432 bytes. Zero high-water increment does not prove no allocation.
Its 15326 successful execve events include 76 launches of the exact pinned JDK
executable. Broader Java basename counts also contain synthetic fixture Java
executables and are not genuine-reader counts. All three claims remain tied to
candidate 1's preserved receipt, coverage and trace summary.

## Later attempts retained

- A3's initially rejected fixture and B3 correction report remain charged.
  B3 independently found two admitted-representation apparatus defects: plain
  noise metadata and plain-quadrature rounding dispatch. These are not product-red
  evidence. A rejected 14-suite proof was interrupted with status 2 after
  593 passes, 18 warnings and 228.71 seconds; it is incomplete diagnostic evidence.
  The rejected manifest and exact reproduction outcomes are retained.
- A3 corrected admission, preserved the scalar fallback, and completed 1062
  focused cases in 346.53 seconds with 18 warnings. Its corrected manifest,
  equivalence summaries, JUnit catalog, correction report and B4 acceptance/hash
  manifest are retained. B4 accepts that exact apparatus checkpoint, not a full
  canonical runtime outcome. The focus used an explicitly recorded measurement
  plugin and is not the ordinary canonical command.
- A4 reused same-invocation workflow facts and three already-owned budgets.
  Its affected six-suite proof passed 465 cases in 63.43 seconds. B5 accepted
  the exact workflow slice after a measurement-evidence correction, with no
  scientific source fix requested. A4/B5 reports, hashes, JUnit and concise
  equivalence/final-probe summaries are retained. The optional nominal-memo
  experiment was rejected and removed; its numeric outcome remains historical.
- The Pyright two-thread experiment is rejected. The successful-path observation
  was 29.5842 seconds serial versus 19.1585 seconds threaded, but malformed
  configuration hung the threaded process until an owned worker was terminated.
  Its eventual status 3 after 96.6409 seconds is rescued failure behavior, not
  equivalent native behavior. All six observed command durations total
  147.1016 seconds, including that hung control. Qualification, exact input hashes,
  command outcomes and cleanup evidence are retained. Canonical serial types and
  all 13 phase requirements were not changed by this rejected experiment.
- The public-only advisor's report is retained as advice, with no acceptance or
  execution authority. Its suggested helper speedups were not measured by that
  advisor. It made no edit or probe and left no owned process.
- A5's frozen report/hash ledger and completed separately matched overlap/native
  helper-probe summaries are retained. Its completed eight-suite acquisition proof
  passed 597 cases with 18 warnings in 282.58 seconds (461.713 seconds summed
  JUnit durations). The status-0 ledger, complete XML, log and renewed small-check
  outcomes are archived; XML count/no-failure/no-skip, native summary and source
  pins agree. Both critical rows retain 32/32 eligible native component admissions.
  This focus used the recorded measurement plugin. The author's final report is
  retained separately from its pre-proof version. Fresh B6 accepted the exact
  acquisition checkpoint, with zero candidate findings. It independently checked
  57 exact lane nodes, 17 complete overlaps, 10 complete native controls and two
  closed truths. The final report, accepted hashes and concise probe summary are
  archived. One scratch syntax failure, one probe-input correction and one early
  missing-summary read remain charged. During report writing the author finalized
  its report and appended admission metadata to the proof summary; B6 reread and
  reconfirmed those final bytes and refreshed their hashes without source changes.
  Earlier evidence-only snapshot hashes and bytes are retained separately. No
  final canonical run, integrated D verdict or completion claim follows.
- The final root `make check` passed Ruff, formatting of all 116 configured files
  and full Pyright with zero errors, warnings or informations. Its completed log
  is archived, with exit status 0 supplied by the coordinator. This quality check
  does not replace final canonical verification.

## Withdrawal of pre-purity-guard workflow timing provenance

The former `workflow-facts-probe` final-checkpoint timing attribution is explicitly
withdrawn. That probe replaced `Table.sample`, disabling the later frozen pure
method guard; its low slope counts describe the preserved PRE-GUARD diagnostic
checkpoint, not final guarded A4/B5 source. The archive name includes
`PRE-GUARD`, and the raw evidence remains unchanged. This is a provenance defect,
not a reason to weaken the purity guard or alter scientific assertions.

The replacement `workflow-final-probe` leaves `Table.sample` unchanged and wraps
only `_sample_error` and `_table_slopes` while forwarding their arguments, results
and exceptions. A4's corrected report and B5's independent review identify and
accept that measurement correction. Its representative heavy budget retains
87556 nominal sample-error queries while slope computations fall to 2, with
wall observation 2.5937 to 1.2695 seconds. These are uncovered helper-call
observations, not full-suite savings or a 600-second completion guarantee.


## Candidate 2 reconciliation and later completed attempts

Candidate 2's exact tree is `0b0e02c817ae186b6655525090867ac2e6a2e5e5`.
Its native receipt, M25, coverage, JUnit, console, time and complete parsed summary
are retained under unique candidate-2 names. The compact reconciliation and cost
exports remain separate from the full raw trace. All 13 phases and 3066 cases
passed, but the strict under-600-second goal did not. Pytest's console summary
is 564.25 seconds and the receipt tests phase is 565.953532 seconds; the table's
564.184 seconds is JUnit suite wall time. These boundaries are not interchanged.

Exact baseline-to-candidate node identity reconciliation removes only each
final observed `@xdist-group` suffix using rsplit; spaces/internal @ remain.
It finds precisely 20 old clock parameter rows and six drift-only rows removed,
five clock keepers added, and all other 3061 identities unchanged, without
normalized duplicates. All eight native integer counters match baseline in
all 30 files. Package/global counters agree with the same-run receipt; all 30
HTML pages/status counters and a read-only SQLite integrity/file-catalog check
pass. Candidate's before/after tracked manifests and all three external input
fingerprints match. This verifies recorded identity/report consistency, not
behavioral completeness or final integrated review.

Same-run candidate-2 M25 is baseline=peak=101828 KiB, increment 0 bytes, limit
33554432 bytes, with report/receipt run ID/hash/values matching. Only its exact
run-ID child observations are used: 20 real reader records with true assertion
status, and 27 distinct API/report records whose schema has no such field.
Other copied run-ID directories are ignored. Canonical combine has no --keep;
293 combined plus 1274 duplicate-skipped inputs retain child data in the native
database, not raw consumed shards after combine. The earlier real bounded
child-data/arc-union qualification remains the relevant preservation proof;
no post-combine raw-shard survival is claimed or required. A final bounded
review still independently assesses the gate and evidence.

The public scientific cost summary contains file totals and top 40 normalized
test-node setup/call/teardown sums, with no product implementation, raw product
profile, coverage, manifest or subprocess data. The full local export contains
2117 scientific node totals; original portable console/JUnit retain all rows.
Only root-selected sanitized costs may go to blind scientific roles.

A6 regression factoring was measured and withdrawn. Matched two real public
search rows passed before in 38.79 seconds and experimentally in 36.14 seconds
(about 2.13 seconds printed call-sum difference). Normal helper outputs/traces,
1046 2D and 2060 wider-3D certificate counts, warnings and input bits matched,
but wider alias/failure-domain qualification was not completed after the cost
rejection. All six prior B5/B6 hashes were restored before A7. No A6 candidate
change, broad proof, new acceptance or canonical result is retained. Reports,
restoration log, helper summaries and both actual row logs/XML are archived;
multi-megabyte full comparison arrays remain untouched locally with hashes.

The worker's source-based archive-cost diagnosis rejected repacking: nested
fixture suites use their own synthetic repositories, so root documentation is
not repeatedly copied/hashed per row. It ran no timing probe or edit. The
worker report is retained instead of duplicating the root's earlier hypothesis
record. No claimed archive saving follows from a file count or outside-phase
subtraction.

The JVM C1 startup experiment is also rejected. Four genuine reader runs
(two default/tier-1 input pairs) returned zero and their actual Java JSON bytes
match within each pair and the recorded hashes. The mean 0.228156-second wall
observation extrapolates to only 4.563125 seconds over 20 calls; the separate
25.9-second CPU extrapolation is not elapsed savings. That limited potential
did not justify new VM capability/vendor fallback logic. The initial absent
system GNU time failure and resumed existing-tool launch, all four records and
paired outputs, input identities, qualification/rejection and cleanup are
retained. No source change or 117-case reader proof was performed. Shared
inputs remain; only confirmed owned experiment work was removed by its owner.
The public-only advisor continued in the same launch with no probe or edit.

A7's only final source delta from B6 is the edge helper at fixture SHA-256
`ea32ed4fb891b18af81dcc557ef0ad1fa6ac958068406a8b20032b7acdfac7dc`.
It preserves scalar updates, alias/error ownership and diagnostics while
skipping qualified unused width-zero deltas and reusing exact local factors.
The 270 warn/raise comparison records all match; the compact qualifier source
is archived. The eight-suite proof passes 597 cases/18 warnings in 246.24
seconds, with 379.665 seconds summed JUnit durations. All 13 pinned scientific/
test hashes match afterward. Full root make check passes all 116 lint/format
files and Pyright with zero diagnostics. Its complete log is retained.

Final-hash preparation wall is 0.823750 seconds versus accepted 1.530678;
final-hash bead wall is 8.412408 versus 9.171537 seconds, with complete output/
certificate/warning/input parity. Earlier preformat timings (including bead
7.1002 seconds) are retained under PRE-FORMAT names and never substituted for
final ea32 evidence. Variation in non-edge bead time remains explicit; these
component runs and the focused proof do not establish canonical goal success.

Fresh B7 accepted the exact A7 checkpoint after independent 10 closed/ownership,
74 exact prior/current and two factor count/immutability controls. It independently
parsed the complete proof and pinned final author report, summary and evidence.
Its final report/manifest, completed/static summaries and compact independent
probe sources/log are archived. Three missing-path attempts remain charged;
there were no candidate correction requests or probe failures. The next exact
canonical run and fresh integrated D/bounded review remain separate gates.

Coordinator `change-accounting.json` records physical net lines against the
required baseline: scientific product 0, runtime harness +38, tests/support
+1238. A7's final formatted addition is +34 net lines; earlier intermediate
estimates are superseded. These are physical diff counts, not behavioral or
coverage statement counts. The coordinator's preservation/LOC JSON bytes were
read for identity and included in the manifest without exporter alteration.

## Cumulative accounting and limits

The coordinator records 13 known role launches before fresh B6, 14 including
B6, and 15 including fresh B7. The same continuing author A session covers
A1–A7; rounds and advisor/worker continuations are not new launches. B1/B2 accepted, B3 rejected with two related defects,
B4 accepted the correction, and B5 accepted the separate workflow slice after
one measurement-provenance correction. B6 accepted the exact acquisition checkpoint after reconfirming final evidence;
B7 accepted the later edge checkpoint. Seven fresh B reviews are completed,
including B3 nonacceptance. Fresh final D/bounded roles are not included in 15.
Prior discovery, exporter, infrastructure, advisor, reviewer input corrections,
failed qualifications, interrupted work and author fixes remain charged. No
counter is reset by this archive. Actual served models, token counts and monetary
cost are unknown. Requested role/model settings do not prove actual serving.

No human total-task, review-round, scenario, token or monetary cap was supplied.
The explicit full canonical runtime goal remains below 600 seconds. Overlapping
role/check durations are not added into a fabricated total elapsed time. All
figures are individual observed runs; instrumentation, warm caches, host load
and source differences limit direct comparison. Full exact-candidate same-run
verification/native coverage/M25, required independent review, final preservation
sweep and configured platform checks remain coordinator obligations.

## Exporter process and cleanup status

This exporter read reports and ran small parsing/hash/compression checks only.
No repository test suite, coverage command, scientific probe, heavy profile,
source/policy/test edit, delegation or Superpowers ran. No persistent process, server or
scratch worktree was launched; all exporter command processes exited. There is no exporter-owned active process to stop
and no disposable scratch directory was created. Intended portable report/archive
files and ignored raw evidence remain; no cleanup deletion was performed.
