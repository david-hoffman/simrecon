# Suppress source lines in unraisable exception diagnostics

Finding: **LESSONS-DOCTOR-01-F001**. Priority: first, because this affects the diagnostic boundary used by blind roles. Classification: confirmed infrastructure diagnostic defect; no claim of actual product-source exposure in a blind session.

At baseline `b05fc782522a81ebd92c10726dac731a26e5a026`, a synthetic exception raised by `__del__` through the public source-free launcher prints the original `raise` line and its comment. This bypasses the intended source-free traceback rendering. Python still exits 0, as it normally does for this unraisable exception; that status does not prove no source was rendered.

Reproduction: save this synthetic program as `probe.py`, then run `.venv/bin/python scripts/source_free_check.py --timeout 15 python probe.py`:

```python
class Broken:
    def __del__(self):
        raise RuntimeError("SYNTHETIC_UNRAISABLE_MESSAGE")  # SYNTHETIC_SOURCE_ONLY_UNRAISABLE

value = Broken()
del value
```

Observed on Linux with project Python 3.13.12 and separately Python 3.12.14: stderr contains `SYNTHETIC_SOURCE_ONLY_UNRAISABLE`. The RuntimeError type, message, filename and line are retained. A paired direct ResourceWarning probe retained its category/location without exposing its source marker. These are isolated diagnoses, not full verification or proof about every diagnostic channel.

Expected behavior: `docs/operations/role-launches.md` requires source-free warning/traceback rendering while retaining type/category, message, location and status. Handle this channel through the normal source-free launcher and its inherited child environment, without suppressing the diagnostic or turning it into a fictitious process failure. The current installation in `scripts/source_free_sitecustomize/sitecustomize.py` does not replace `sys.unraisablehook`; this is the leading implementation diagnosis, not a prescribed patch.

Lesson evidence: [unraisable diagnostic escape](https://github.com/david-hoffman/simrecon/blob/b05fc782522a81ebd92c10726dac731a26e5a026/docs/lessons/20261007T213220Z-illumination-coordinator-blind-diagnostic-format-correction.md), [related startup diagnostics](https://github.com/david-hoffman/simrecon/blob/b05fc782522a81ebd92c10726dac731a26e5a026/docs/lessons/20261007T213156Z-illumination-coordinator-blind-startup-diagnostics.md). Local first-pass evidence: `docs/reports/lessons-doctor-2026-11-11/cohort-1-probe.json` contains exact helper hashes, both interpreter results and the safe synthetic inputs.

Completion conditions:

- Exercise the public launcher with an unraisable synthetic exception; omit source snippets/comments/locals while retaining useful category, message, location and native process status.
- Qualify inherited Python-child behavior and relevant warning/error interactions on the supported project interpreter. Keep the paired working warning case and existing diagnostic channels intact.
- Independently review meaningful tests and the exact passing correction under the normal delivery route; full local verification remains required before submission.
- Record a scoped disposition with evidence. An issue link or closure alone does not resolve other source-free diagnostic claims.

This issue commissions no automatic implementation from the doctor pass. Intake is recorded in `docs/tasks/lessons-unraisable-diagnostics.md`; its execution state is authoritative once correction is commissioned.
