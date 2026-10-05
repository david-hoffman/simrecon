# Calibration results

**Version 1.0. Recorded October 5, 2026.** One fresh native call per requested configuration answered the same 12 public synthetic decision groups. The coordinator scored Luna/medium at 9/12 and Sol/high at 12/12. This qualifies no general model ranking, defect rate, scientific equivalence or savings estimate. The [model selection decision](model-selection.md) limits adoption to the evidence below.

## Packet, key and scoring

The delivered UTF-8 packet has a 256-bit Secure Hash Algorithm (SHA-256) digest `02e96ce049bc2f318bbee7d15e581bf985ead30c3275a489eba21d7ffeabd715`. [Public calibration data](calibration-cases-v1.json) preserves its exact text, expected decisions and group verdicts. Its expected-decision key has SHA-256 `244efae6aa977df3885df7490a09f756c2f89855b06b2efc297564a57335d2c3` under the canonical JSON encoding declared in that file. A fresh independent designer agent delivered the closed expected key to the coordinator before either calibration call. No separate retained designer artifact exists. The coordinator performed semantic group scoring; no separate scoring delegate completed.

The packet declares its rules and data. It prohibits repository reads, tools, nested launches and questions and requests JSON for fixed IDs C01–C12. The groups challenge route selection, permitted inputs, unsigned values, byte order, not-a-number (NaN) payloads, unresolved units, container invariants, evidence reuse, blindness and allowances. Twelve groups in one probe are a calibration sample, not twelve approved product scenarios or a new task allowance.

| Group | Declared judgment | Luna/medium | Sol/high |
|---|---|---|---|
| C01 | Non-normative references paragraph is mechanical | Correct | Correct |
| C02 | Settled missing-executable proof is bounded; no initial-red requirement | Correct | Correct |
| C03 | Binary repair is high risk; C cannot edit the reviewed fixture | Correct | Correct |
| C04 | Policy requires separate owner approval, independent review and synchronized activation | Correct | Correct |
| C05 | Accept normalized key `01` as `1`; reject out-of-range `2` | Incorrect | Correct |
| C06 | Opaque source units keep old provenance unresolved | Incorrect | Correct |
| C07 | Preserve unsigned interpretation and every pixel-word bit | Incorrect | Correct |
| C08 | Container digest differs legitimately; compression violates no-filters rule | Correct | Correct |
| C09 | Shared fixture change affects T1–T3; unchanged T4 evidence may remain | Correct | Correct |
| C10 | Changed relevant evidence inputs invalidate reuse; missing report blocks acceptance | Correct | Correct |
| C11 | Exposed A loses blindness; replacement packet permits P, Q and S | Correct | Correct |
| C12 | Charge 95 min, retain 25 min, no C repair or automatic third B round | Correct | Correct |

Luna's C05 answer correctly described acceptance but also marked the rejection oracle valid. C06 falsely resolved an opaque source magnitude as an old canonical value. C07 accepted signed decoding of unsigned data and the payload-losing float result; its decision and rationale also disagreed about the expected float bytes. These are oracle defects, not cosmetic response differences. Sol's C11 wording called the replacement A a reviewer; the required decisions remained correct, but A's role is test author.

The C07 sanity check is word-wise: unsigned `80 01` is `0x8001 = 32769`, and `ff ff` is 65535. Reversing each word yields `01 80 ff ff`. The float words `80 00 00 00` and `7f c0 00 35` become `00 00 00 80` and `35 00 c0 7f`; equal numerical NaN comparisons cannot establish that bit pattern. C12 is `85 + 3 + 7 = 95 min`; `120 - 95 = 25 min`. The explicitly excluded 20 min owner wait is not charged.

## Observed native counters and timing

| Requested configuration | Correct decision groups | Input tokens | Cached input tokens | Output tokens | Reported reasoning output tokens | Approximate observed duration |
|---|---:|---:|---:|---:|---:|---:|
| `gpt-6-luna`, medium | 9/12 | 15,489 | 11,008 | 1,300 | 0 | 26.3 s |
| `gpt-6.1-sol`, high | 12/12 | 16,181 | 12,288 | 1,902 | 467 | 71.6 s |

These are requested native model/effort settings. Actual served-model attribution is unavailable. Counters come from each ignored event file's `turn.completed` usage, not private reasoning or raw item logs. Cached input is a subset of input: uncached input is `15,489 - 11,008 = 4,481` for Luna and `16,181 - 12,288 = 3,893` for Sol. Do not add cached input again or add separately reported reasoning output to an undocumented token total. Duration is the coordinator's approximate clock observation after launch, not a complete task/PR critical path. Exact start/end timestamps, complete preparation/check/owner effort and monetary cost are unknown here. These single calls do not isolate model from effort or establish a general latency advantage.

Retained local evidence: [Luna final JSON](../../artifacts/delivery-efficiency/rollout/calibration-luna-final.json), [Sol final JSON](../../artifacts/delivery-efficiency/rollout/calibration-sol-final.json). Their sibling ignored event files contain the usage records; do not read private reasoning or raw item logs. The tracked public data provides reproducible inputs/expectations without depending on local event logs. Reproduce packet identity from the repository root:

```sh
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
record = json.loads(Path('docs/operations/calibration-cases-v1.json').read_text())
packet = record['packet_utf8'].encode('utf-8')
assert hashlib.sha256(packet).hexdigest() == record['packet_sha256']
key = json.dumps(record['expected_decisions'], ensure_ascii=False,
                 sort_keys=True, separators=(',', ':')).encode('utf-8')
assert hashlib.sha256(key).hexdigest() == record['expected_decisions_sha256']
print(record['packet_sha256'])
PY
```

## DOC1 and adoption limits

The [approved DOC1 contract](../contracts/delivery-pilots-v1.md) selected a fresh `gpt-6-luna`/medium mechanical worker only after route classification. It appended the requested Related references paragraph to [environment.md](environment.md), linking the existing verification and role-launch documents. The [worker report](../../artifacts/delivery-efficiency/rollout/doc1-report.md) records both link targets present, a passing exact-file `git diff --check`, inspection of the exact diff, one initial edit and no repair cycle. DOC1’s mechanical edit is complete under the owner-approved scope; its checks do not establish the final candidate’s canonical verification.

DOC1's `turn.completed` reports 185,229 input tokens, including 152,576 cached input tokens; 1,872 output tokens; and 536 reasoning output tokens. Uncached input is `185,229 - 152,576 = 32,653`. Actual served model, full elapsed cost, owner effort and dollars are unknown. These role-specific counters do not represent the complete rollout.

Permit Luna/medium for already-classified non-normative mechanical edits with deterministic diff/link checks. This evidence does not qualify Luna/medium for risk intake, blind numerical test design, oracle review, policy review, bounded worker/reviewer responsibility or data-loss behavior. Select Sol/high provisionally for subsequent risk/oracle roles, while preserving each required independent gate. One correct synthetic response is no general guarantee. In the live MEM1 slice, Sol/high A omitted a distinguishing same-run-ID report-replacement case; the independent B review found that gap before implementation. The fixed calibration therefore does not replace independent review or complete contract inventory. Unrepresented complexity, changed settings, a missed obligation or unexpected tools/permission need would require fresh diagnosis and applicable evidence within the existing budget.
