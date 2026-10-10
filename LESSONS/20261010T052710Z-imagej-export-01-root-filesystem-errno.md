# Bounded TIFF writes preserved the filesystem error number

**Version 1.0**

- ID: 20261010T052710Z-imagej-export-01-root-filesystem-errno
- Date: 2026-10-10T05:27:10.600420+00:00
- Task: [IMAGEJ-EXPORT-01](../docs/tasks/imagej-adapter-intake.md)
- Role: coordinating observer
- Topic: operation-time file errors
- Status: confirmed for the tested environment
- Observation: The first exporter run passed 63 of 64 accepted cases. Under the real file-size limit, its array-backed TIFF write path raised OSError with errno=None. After C supplied bounded per-plane bytes to the writer, the same unchanged public test observed errno=27 (EFBIG), and all 64 cases passed. This is an observation on Python 3.13.12, NumPy and tifffile 2026.9.20 on the recorded macOS environment; it is not a guarantee for other write paths or platforms.
- Evidence: [Accepted operation-time public test](../tests/test_imagej_export.py); ignored artifacts/imagej-adapter-intake/C-01/pytest-01.log and pytest-02.log retain the two runs. Command: .venv/bin/python -m pytest -q tests/test_imagej_export.py with the authenticated development Java input and distinct ImageJ evidence run identity. [Adapter code](../src/simrecon/_imagej.py) contains the resulting bounded byte write path. The task pointer retains final exact-candidate and platform evidence separately.
- Suggested action: When an adapter promises ordinary filesystem exceptions, exercise a real operating-system write refusal and check the error number. Bounded byte writes are the tested alternative for this adapter. A different implementation needs its own evidence; this lesson grants no new scope.
