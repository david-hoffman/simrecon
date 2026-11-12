# Recover a task from a saved checkpoint

**Version 1.0.** Use the existing
[HANDOFF](../agentic-software-delivery-v1.0/templates/HANDOFF.md) and
[CANDIDATE-PACKET](../agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md)
templates. Keep the task's one Current state pointer. A recovery manifest is an
inventory of evidence and gaps, not another execution state or an acceptance
verdict. This procedure adds no upload, credential, deletion or role authority.

## Before retiring a workspace

Record repository remote/identity, branch, exact integration/base and candidate
commits/tree, and `git status --short`. Record contract/packet/test/fixture hashes,
accepted test checkpoint or **none**, named ownership, pending role, required
gates, model/effort and actual supported launch controls. A moving branch name is
not a checkpoint. Do not assign a commit identity to unsaved bytes.

Preserve authorized uncommitted work before retirement. For example, write
`git diff --binary HEAD` to a selected private file and copy specifically named
untracked task files separately; retain file hashes and the original base commit.
A patch alone does not preserve untracked files. A local commit is another option
only within existing authority. Inspect the saved inventory and prove its files
are readable before retiring anything. Never reset/clean a worktree to make its
record look clean. Uncertain files and original history remain preserved.

For every required evidence item, fill these fields in the existing handoff:

| Field | Required content |
| --- | --- |
| Identity | Commit/tree, blob, file hash/size, run/receipt/report identity as applicable |
| Origin | Exact command, exit status, timestamp and originating role/platform |
| Scope | Obligations/checks actually demonstrated, excluded/unsupported evidence |
| Inputs | Candidate, tests/fixtures, locks/checks, interpreter/tools/build/external inputs |
| Storage | Actual destination, access/retention limits, and verified availability |
| Recovery status | **recovered**, **newly reproduced**, **historical-record-only**, or **unavailable** |
| Applicability | Inputs still matching, changed material inputs and required new checks |

An ignored local path is not a durable copy. Select an authorized durable
destination for sanitized summaries and reusable packets, using actual existing
write/publication authority. A Git-tracked file becomes durable elsewhere only
when its commit actually reaches an authorized retained repository. An expired
artifact/link is unavailable. If no authorized destination exists, keep the safe
local record and explicitly record the durability gap; do not upload automatically.
Keep raw sensitive logs, native transcripts, private acquisitions, credentials,
tokens and device codes local/private. Select public metadata rather than dumping
the environment. A source-free traceback aid does not redact secrets. For a
confidentiality check, use harmless synthetic markers, never real secret values.

Carry cumulative attempts forward by source/role, including failed launches,
diagnoses, repairs, reviews and publication/sign-in attempts. Keep known counts
and unknown native metering/tokens/cost/time explicit. Repeated cumulative summaries
do not create additional attempts. Unknown or missing evidence means unknown,
not zero. Store packets/finals/detailed reports at distinct destinations.

## Restore records, then re-establish readiness

1. Obtain the original commits through existing Git tooling and retrieve named
   evidence through already-authorized file tools. Verify each commit/tree and
   artifact hash against the saved manifest. A newly written equivalent document
   is not recovery of the original Git object. Failed retrieval stays failed.
2. Restore a separate checkout with the original history. Recover unsaved work
   from its saved base/patch/named files and retain its dirty identity honestly.
   Do not copy an old `.venv`, ignored tool cache or missing evidence into a
   demonstration intended to prove fresh setup.
3. Follow [bootstrap](bootstrap.md) with fresh task-owned tool/cache directories
   for a fresh exercise. Select exact `UV`/`SIMRECON_JAVA`; run local readiness
   and unchanged preflight. Record actual executable/platform/import/input
   identities and status. A matching HEAD alone cannot preserve old evidence
   after a material environment/input change.
4. Reconcile recovered evidence with required gates. Reuse only evidence with
   matching material inputs and no challenging failure. Mark records that cannot
   support current acceptance historical-only. Missing required evidence blocks
   the dependent stage; stop and record the focused next diagnostic.
5. Resume only the named next role once its prerequisites hold, using
   [role launches](role-launches.md#recoverable-launch-instructions). Recovering
   an exposed conversation cannot create a fresh scientific role. A/B receive
   only their public allowlist and sanitized authorized evidence, never a
   nonblind recovery report, raw logs or implementation-bearing Current state.

Full-local exact-candidate verification and all scientific/platform gates remain
binding. Local readiness and preflight supply neither scientific acceptance nor
current native authentication. A fresh required review keeps its fresh-session
and blindness requirements.

## Concrete #84 record-recovery exercise

Use the original saved checkpoint
`f8042042ff2b6865ecf501e38f11232de5d36fc9` on
`docs/84-reconstruction-memory-intake`. In a newly selected disposable directory:

```sh
set -eu
RECOVERY_ROOT=/absolute/fresh-recovery-checkout
SAVED_COMMIT=f8042042ff2b6865ecf501e38f11232de5d36fc9
git clone --no-checkout --branch docs/84-reconstruction-memory-intake \
  https://github.com/david-hoffman/simrecon.git "$RECOVERY_ROOT"
git -C "$RECOVERY_ROOT" cat-file -e "$SAVED_COMMIT^{commit}"
git -C "$RECOVERY_ROOT" checkout --detach "$SAVED_COMMIT"
git -C "$RECOVERY_ROOT" rev-parse HEAD 'HEAD^{tree}'
git -C "$RECOVERY_ROOT" status --short
git -C "$RECOVERY_ROOT" merge-base --is-ancestor \
  e2dd30b71c883010eb706001a55d709b7459b9d0 "$SAVED_COMMIT"
git -C "$RECOVERY_ROOT" merge-base --is-ancestor \
  2777b84eb378f8102c0a7d694227c03899b433e4 "$SAVED_COMMIT"
git -C "$RECOVERY_ROOT" merge-base --is-ancestor \
  9f572e92a24de738932ecdf2bafa84418df5abf7 "$SAVED_COMMIT"
```

Stop if the branch/object/ancestor cannot be obtained or does not match. Verify
tree `f230eb3cee1ccf26332050261e0ab1fe0c01a078` and compare the recovered
task, contract and public/candidate packets with the saved identities. Use the
[pinned saved task](https://github.com/david-hoffman/simrecon/blob/f8042042ff2b6865ecf501e38f11232de5d36fc9/docs/tasks/reconstruction-memory-intake.md)
and the separately dated
[later diagnostic comment](https://github.com/david-hoffman/simrecon/issues/105#issuecomment-6828272895)
as distinct sources. [DEV105 evidence](../reports/setup-recovery.md) records the
exercise's recovered hashes, unavailable artifacts and attribution limits; it
does not replace #84's Current state. Recreate its environment with this guide's
pinned tools and the saved checkout's unchanged preflight, recording that
checkout's actual locked inputs. This older checkpoint need not contain DEV105's
readiness script; do not edit it to manufacture a current candidate.

Retain the two failed native A launches, zero accepted scientific checkpoints,
advisor/recovery work, author corrections, publication rejections,
preflight/type-check and sign-in attempts. The later comment's additional
resume-preflight pair and device authorization have separate attribution;
successful device sign-in was not observed. Do not double-count repeated totals
or infer missing aggregate metering. Missing
`artifacts/reconstruction-memory/execution-receipt.json`, `roles/a01-*`,
`roles/a02-*`, or resume logs remain **unavailable historical evidence**.
Do not recreate favorable verdicts or change #84's state during the exercise.

The next scientific stage is fresh blind A after current setup and required
native capability are established under #84's authorization, then fresh B,
restricted C and fresh D. Showing that next stage requires no scientific launch.
Current authentication, full verification and Ubuntu/macOS qualification remain
separate evidence requirements.
