# Prepare the fixed reader-reservation parent when evidence is external

Finding: **LESSONS-DOCTOR-01-F002**. Priority: second. Classification: confirmed fixture/environment prerequisite gap, not a scientific product defect.

At baseline `b05fc782522a81ebd92c10726dac731a26e5a026`, `ReaderReservation` in `tests/shared_node_baseline_public_callers_fixture.py` creates `RUN`, which follows `SIMRECON_PROTOCOLS_EVIDENCE`, but acquires its exclusive lock under the fixed `artifacts/baseline-compatibility-20261013/A09` directory. In a fresh checkout with external evidence and no fixed parent, `self.lock.mkdir()` raises `FileNotFoundError` before any reader-cache rename.

The [CE03 lesson](https://github.com/david-hoffman/simrecon/blob/b05fc782522a81ebd92c10726dac731a26e5a026/docs/lessons/20261103T020523Z-ce03-coordinator-external-protocol-lock-parent.md) records the original 15 affected failures and unchanged focused checks passing after the empty parent was prepared. A new isolated diagnosis on project Python 3.13.12 redirects the current class's RUN, EVIDENCE and CACHE to disposable synthetic directories: absent parent fails with errno 2; the same code with an empty parent succeeds and restores cache contents/inode; a preexisting lock is rejected and preserved. No real cache was accessed. Receipt: `docs/reports/lessons-doctor-2026-11-11/reader-lock-probe.json`.

Current search found no standard prerequisite that prepares this fixed parent for the external-evidence case. Evidence relocation intentionally must not relocate the shared exclusive lock. The existing disposable lifecycle fixture prepares its own parent and therefore does not demonstrate this fresh-checkout case.

Proposed first remedy for intake: document and demonstrate the existing parent-directory preparation command in the verification environment procedure. Determine whether automatic preparation is separately warranted; do not silently change cache/lock lifecycle to make the symptom disappear.

Completion conditions:

- Name the supported external-evidence invocation and fixed-parent prerequisite, including its owner and when it is prepared.
- Demonstrate absent-parent behavior and the supported prepared-parent path with the current reservation, retaining evidence outside the checkout.
- Preserve rejection of existing locks and original cache contents/inode; never create/remove a live reservation lock or bypass preservation.
- Obtain independent policy review for a documentation remedy. Any executable fixture/cache lifecycle change needs separately named ownership and the applicable risk route, tests and exact-candidate gate.
- Add an evidenced scoped disposition; do not equate issue closure with completed qualification.

Intake is recorded in `docs/tasks/lessons-reader-reservation-parent.md`. This issue and the doctor pass do not authorize changing runtime/tests, cached reader data, lock semantics or verification gates.
