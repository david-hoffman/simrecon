# Preserve typed scientific errors at a composition boundary

**Version 1.0**

- ID: 20261102T054649Z-ra14-coordinator-scientific-error-identity
- Date: 2026-11-02T05:46:49.630323+00:00
- Task: [RA14](../docs/tasks/reference-alignment-ra14.md)
- Role: coordinator
- Topic: numerical dependency error tests
- Status: confirmed
- Observation: Generic allocation/value/warning observers did not establish that a scientific dependency error retained its original identity. Fresh blind B2 found the gap. The same blind author added one real public numerical-range case to the existing observer; fresh B3 accepted the revised checkpoint. No implementation existed during the correction.
- Evidence: [The frozen public range observer](../tests/test_reference_alignment_ra14_comparison.py) uses a valid central-only Q1 configuration with a positive physical-output lower bound beyond float64 range. Reviewed-file-set digest `b37f4b32751117d2b6e3b9190807d1b5ba93720bf03db04a590a40edb660b4fa`; retained B2/B3 reports are `artifacts/ra14/B2/final.md` and `artifacts/ra14/B3/final.md`. The later C implementation passed all 101 focused examples in Python 3.13.12 / NumPy 2.5.3.
- Suggested action: When a composition contract preserves dependency errors, challenge the concrete scientific error category through a public boundary and preserve exact exception identity. Justify final-output unrepresentability independently; an overflowing intermediate alone is insufficient. Extend an existing meaningful observer rather than adding an exception-subclass inventory.
