# RA12 verification isolation and housekeeping

**Version 1.1.** This supplement preserves the scientific verification isolation
requirement and applies the owner-selected [simplified housekeeping policy](../operations/fixture-cleanup.md).
The superseded one-shot cleanup protocol, helper, tests and cleanup reviews are
not requirements of this continuation.

The first historical verification attempt placed generated test repositories
below a real working tree. Deliberately unavailable fixture Git identities could
then discover the parent repository. The first receipt and test output were
subsequently lost; they remain unavailable, never reconstructed as passing proof.

Run the complete unchanged canonical gate on the exact committed candidate.
Create its temporary fixture root outside every Git working tree. Give the
verification worktree its own locked environment and check interpreter, platform,
lock, installation/import and selected Java before dependent work. Record the
actual commit/tree, environment and required input identities. A failed or partial
run supplies no passing evidence; tree equality alone is not commit identity.

The previous auxiliary verification checkout and some original inputs were
removed under explicit owner direction. Historical results and review records
remain historical; do not claim that every former referent survives. The current
continuation renews exact-candidate verification and required independent review.
Retain its new material evidence and required inputs. Use existing commands for
confirmed disposable scratch after owned processes close, and record any kept
paths or errors in the sole Current state. No additional cleanup pipeline follows.
