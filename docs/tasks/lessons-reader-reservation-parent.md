# LESSONS-READER-PARENT-01: define the external-evidence reservation prerequisite

**Version 1.0** Git versions revisions.

## Contract

- Origin: owner-authorized LESSONS-DOCTOR-01 prioritized intake; stable finding LESSONS-DOCTOR-01-F002. [Issue draft](../reports/lessons-doctor-2026-11-11/F002-issue.md), [current isolated diagnosis](../reports/lessons-doctor-2026-11-11/reader-lock-probe.json), and the CE03 source lesson identify the same prerequisite gap.
- Objective: document and qualify the existing preparation of the empty fixed reservation parent when verification evidence is external. Evidence location and lock location remain distinct. Preserve existing lock rejection, reader cache contents/inode and exact verification gates.
- Baseline: `b05fc782522a81ebd92c10726dac731a26e5a026`, project Python 3.13.12. Current class fails at lock mkdir when fixed parent is absent; isolated parent-prepared positive and existing-lock rejection cases preserve synthetic cache. This is an environment/fixture diagnosis, not product-red or a complete suite run.
- Route: policy/documentation amendment for an existing explicit prerequisite, with fresh independent policy review. Proposed documentation ownership: `docs/operations/imagej-reader-environment.md` and directly affected PROJECT verification guidance only. Demonstrate with disposable synthetic directories; never experiment on a live shared reservation or replace the installed reader cache for this documentation task.
- Proposed command: from repository root, `mkdir -p artifacts/baseline-compatibility-20261013/A09` prepares only the parent. A preexisting `reader-reservation.lock` remains a blocker; neither this task nor the command authorizes removing it. Validate path/ownership assumptions in the actual supported environment before prescribing a broader automation change.
- Scenarios/completion: external evidence + absent parent is diagnosed; documented parent preparation permits the existing reservation; existing lock is rejected; cache content/inode restored; checks/evidence clearly distinguish the synthetic diagnosis from full reader qualification. Record a scoped resolution only after the documentation is independently accepted and the supported procedure is demonstrated.
- Executable alternative: any request to change the reservation implementation is separate named test/infrastructure ownership. Cache rename/restoration/deletion behavior remains high risk where affected; never call a lifecycle change mechanical or bypass full verification/review. Missing meaning returns to intake.
- Gate: no runtime/test/config edits under this initial route. Relevant documentation/procedure checks and fresh policy review; full `make verify` before any later PR submission. Existing product gates and historical attempts remain unchanged.
- Authority/accounting: intake only in this pass; correction not launched. No human-set numeric limits; proposed policy author/reviewer `gpt-6.1-sol`, high; missing actual attribution/tokens/cost unknown. Parent diagnosis charges retained.

## Current state

- Status: recorded; intake complete, documentation correction not started. Priority: second actionable finding.
- Next action: commission named documentation author and fresh policy review, qualifying the prerequisite without touching a live lock/cache. Automatic fixture preparation remains a separate decision, not silently selected here.
- Issue link: [#100](https://github.com/david-hoffman/simrecon/issues/100), published and read back open with the exact reviewed body. This section is the sole correction execution state.
