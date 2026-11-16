# WS116 F01 independent affected prose-correction review

Verdict: **ACCEPT_F01_PROSE_CORRECTION**.

This accepts only the CE06 backing/publication wording correction in the exact corrected Markdown identified below. There is no concrete source/meaning mismatch in the changed passage. This is not whole-study scientific acceptance, acceptance of any cohort or new experimental evidence, final-report readiness, or a make-verify/postgate verdict.

## Independent scope and basis

I independently compared the original and preserved original with the corrected whole Markdown, inspected the complete supplied patch, and inspected the named primary source for final ownership publication and event capture. I treated the existing admission-plan statement as a claim to check against source, not as an oracle. I read the named normative context, applying W02's backing-aware, overlapping-lifetime distinction and the prohibition on self-repair. I did not consult author/coordinator/ROOT conversations, handoffs, previous review verdicts, task Current state, or unrelated cohort evidence.

The packet declares frozen EA head `ea9117d3efe2d8de273402d643e732140138e496`, tree `e8fe2b1b01d9e7abf476a71a2241309255bb0587`, and accepted parent `ace06c861b974b6251a092567c253ae4eb0f56c8`. Those are packet declarations, not independently verified Git/ancestry facts. My reviewed identity is the file content bound by the verified hashes below. No Git probe was performed.

## Source judgment

The old clause, “Full `_finish_owned` paths/trace snapshots require separate copies/backings,” conflates final publication with snapshot capture. In `src/simrecon/acquisition/layout.py:158–177`, `owned()` constructs `np.array(value, copy=True)`, whereas `_finish_owned()` checks the supplied array, sets its writable flag, and returns that same `value`. `_finish_owned` therefore creates no finishing snapshot of the payload. Its finite check is not a claim that the entire operation has no transient allocations.

The full return in `src/simrecon/acquisition/modes.py:1101–1118` publishes quadratures, noise, matrices, phase angles, sums/gains, optional off arrays, maps, displacements and clock through `_finish_owned`; it also retains `tuple(trace)`. The inspected allocations at lines 734–790 establish private map/metadata copies or newly allocated arrays, including q and optional off_q. The final calls transfer those private backings into the result rather than duplicate them again. “Transfers the same private backing without a finishing copy” accurately describes this publication path; it does not imply aliasing caller input.

Full event capture is different. In `layout.py:202–259`, each ndarray detail in the noncompact branch is passed through `owned()`, then stored in the event's detail tuple and appended to the trace. These are independent copies, retained by their events and the published trace. The inspected `modes.py` callsites include off-combination's `quadratures_after` view (lines 325–348), exposure correction (924–933), phase design (967–977), and between correction (1004–1012). A source view or workspace passed at those callsites does not become the event's backing: full capture copies it. The snapshots can therefore coexist with the working/private arrays, and changing or publishing a workspace does not replace the already captured event backing. This supports “full trace/event `owned()` captures have independent backings and their own lifetimes.”

The compact branch of `event()` instead checks arrays and omits selected spatial details or converts other arrays to scalar tuples. The compact return at `modes.py:1045–1100` publishes q/noise and projections rather than full diagnostic arrays. These branches support keeping final publication and diagnostic retention distinct; they establish no process-memory reduction measurement.

The admission-plan paragraph at line 13 independently agrees with the checked distinction: final private q is transferred without another q snapshot, full event arrays are copied, and off_q exists through preparation. I did not validate its unrelated formulas, workloads, operating envelopes or runtime claims.

“Exact transient peak remains unclosed” is appropriately limited. Source shows allocation/capture/publication relationships, not an observed instantaneous peak, allocator behavior, every expression's release timing or native workspace. Retained full traces and finite-check/other expression temporaries remain relevant. Neither final ownership transfer nor the correction proves reduced measured RSS or a validated transient peak.

## Exact extent of correction

`cmp` reported the frozen original and preserved original byte-identical. The independent whole-file `diff -u` showed one changed line: the CE06 row's final prose clause, beginning “Full `_finish_owned`”. The original prefix concerning q/off_q and compact preparation is unchanged. The supplied complete patch describes that same substitution.

Every other byte of the Markdown is unchanged by this comparison: all formulas, Bq/Bqt definitions and quantities, the CE06 payload cell, numeric examples, other rows, qualifications and surrounding text. This confirms preservation, not a fresh derivation or acceptance of those formulas and unrelated claims. No measured-RSS, new numerical-trial or broader scientific-validation claim is added.

## Verified SHA256 identities

All seven target/source digests matched the packet's expected values:

| Input | SHA256 |
| --- | --- |
| Review packet `/workspace/work/campaign/evidence/116/scientific-review-F01-correction/packet.md` | `85fa517ddca854d12d50744fbc3140fac580eb02ad3aae6c65878aa288ff3b1f` |
| Frozen original `/workspace/work/issue-116/docs/reports/reconstruction-working-set/analysis/liveness-draft.md` | `8fef6fcfd756b48f22e08cccead97387fdd41fc2ed4e10b86d54deb62eb09f07` |
| Preserved original `/workspace/work/campaign/evidence/116/report-source-preparation/inputs/docs/reports/reconstruction-working-set/analysis/liveness-draft.md` | `8fef6fcfd756b48f22e08cccead97387fdd41fc2ed4e10b86d54deb62eb09f07` |
| Corrected whole Markdown `/workspace/work/campaign/evidence/116/report-liveness-wording-correction/liveness-draft-corrected.md` | `337ae76ca2a685c9ef111cdcc1a9f96a641f6503336898d8cabb6f33f7b79b5c` |
| Complete patch `/workspace/work/campaign/evidence/116/report-liveness-wording-correction/literal-wording-delta.patch` | `bfffb26ad222bbc7e428011538d9899b3ab84383d16170fe83249d26ad21714a` |
| Primary `/workspace/work/issue-116/src/simrecon/acquisition/layout.py` | `6f9284ceba55f2747c3b238dc568bff2d4154d718b4511d943a6aab0014c320e` |
| Primary `/workspace/work/issue-116/src/simrecon/acquisition/modes.py` | `4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1` |
| Claim target `/workspace/work/campaign/evidence/116/corpus-admission-plan/admission-plan.md` | `b7148be4355f32dd4bda70c0824201fe67d89baa27d13f1ccaf3b9b29eb37430` |

Normative inputs were also hashed:

| Input under `/workspace/work/issue-116/` | SHA256 |
| --- | --- |
| `AGENTS.md` | `56ea4b592323779ac86cacede6dc15eff3d80098e25805cb606e6166010d5ecd` |
| `docs/PROJECT.md` | `530e72dbc3b9e73756687c3893bef2803cb775080a12539681020916c59b9fee` |
| `.agents/skills/review-work/SKILL.md` | `e069e1be50587974d46ffca2a8c38b865e7133881aa39aaf0bf45934c6ae0160` |
| `docs/packets/reconstruction-working-set-review.md` | `8162a83f185bdf089fca4f9b2fcd38e59da6cbb15b2b561e81570aa1874f3dc5` |
| `docs/contracts/reconstruction-working-set-v1.md` | `4b049da71379199cae229f259baa8942936cdd1a352c505b52d2f8d2fda3bc4e` |

## Actions, independence and limits

Read/check actions were bounded `cat`, `sed`, `rg`, `wc`, `sha256sum`, `cmp` and `diff` on the named inputs. Commands completed; the expected `diff` content shows the one substitution, and `cmp` emitted no difference. One combined initial normative read was output-truncated; I then reread the relevant PROJECT excerpt, the complete 46-line review skill, and the contract's W02/ownership/liveness passages in bounded output. No omitted portion was used as evidence.

Only this review artifact was written, using `apply_patch`. I did not repair or integrate any target. No source, frozen report, preserved evidence, policy, gate or experiment input was modified by me. I created no scratch files or numerical/long-running processes. No interpreters, imports, scripts, tests, lint, statistics, calculators, Git, native/Docker execution, resource/process probes, active98828 records, inventory or discovery tools were used. No cross-role cleanup or process ownership check was performed or claimed.

No unintended exposure was observed. The named sources and normative documents were the only file inputs. No delegation or collaboration tools were used. This is a fresh assigned independent review with no author conversation supplied to me. Optional memory-disable and engineered per-role read-only isolation are unavailable per the packet; restrictions are prompt-level on a shared filesystem, not proof of engineered isolation.

Requested serving configuration is `gpt-6.1-sol` / high / no history. Actual serving attribution, effort, token use, cached tokens, cost and elapsed-time metering are unknown unless separately exposed; I have no verified meter values. This is one completed F01 affected prose review in this session. Earlier attempts and charges are not inspected, reset or represented as zero. No human numeric review cap is specified.

W02 disposition is acceptance of this ownership/publication wording only. Runtime liveness, complete event inventories/byte totals, exact transients, numerical behavior, all other W01–W09 obligations, cohort validity and exact-candidate full gate remain outside this verdict. No readiness or gate waiver follows.
