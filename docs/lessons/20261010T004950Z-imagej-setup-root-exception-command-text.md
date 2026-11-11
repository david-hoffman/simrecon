# Frame suppression does not sanitize exception command text

**Version 1.0**

- ID: 20261010T004950Z-imagej-setup-root-exception-command-text
- Date: 2026-10-10T00:49:50.468692+00:00
- Task: IMAGEJ-SETUP-01 / IMAGEJ-EXPORT-01
- Role: coordinator
- Topic: blind-role diagnostic preparation
- Status: confirmed
- Observation: Fresh independent setup review02 reproduced inline Python command text in standard nested subprocess TimeoutExpired and CalledProcessError messages even when traceback source lines were suppressed. The exact d75ae candidate passed 4015 tests; those tests did not exercise this route. Passing frame-renderer tests therefore does not establish subprocess-message suppression.
- Evidence: baseline d75ae046ffecf7213a785c44d1aa721331abd1bc; artifacts/imagej-adapter-intake/setup-review-02-final.txt (SHA256 1f423343aae8a0c6acfe3738503c4928e471a0816fc532f3536697e8c5326c77), independent direct/standard-formatting probes on CPython3.13.12; exact passing full03 receipt SHA256 34dc598dd9a0e70f04295161d9efd03ed422ebbcdd14cc242b03d4540a714fbb.
- Suggested action: Diagnose and test standard subprocess-message paths as well as frame rendering before depending on a source-free aid. Retain exception category, safe executable, duration/status and locations. Explicit source printing, replaced diagnostics and source-bearing custom messages still need separate handling; this observation supplies no engineered access-control claim or new edit authority.
