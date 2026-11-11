# NumPy integer dimensions need exact observer arithmetic

**Version 1.0**

- ID: 20261009T161749Z-volume-recombine-01-root-exact-observer-dimensions
- Date: 2026-10-09T16:17:49.553429+00:00
- Task: VOLUME-RECOMBINE-01
- Role: root coordinator
- Topic: scientific observer representation
- Status: confirmed
- Observation: The accepted fixture's canonical-bin helper produced an empty range for permitted `numpy.uint64(1025)`, while Python `1025` produced -512 through 512. Unsigned negation wrapped before range construction. Blind A's correction audit also found signed int8 endpoint overflow and related dimension products/conversions. This is an observer defect, not a product defect; new observations after implementation remain supplemental.
- Evidence: Prior accepted checkpoint `48424efe7a0b0ad139361a79e24d86840577aa44`; source-free `root-w17-public-mode-probe-02.stdout.txt` and stderr under local ignored `artifacts/volume-recombination-execution`; Python 3.13.12 / NumPy 2.5.3. `a-correction-05-report.md` and own-source dependency audit document four fixture-function integer-handling corrections, with the public test arguments unchanged. Fresh B6 acceptance remains required.
- Suggested action: Convert internal dimension arithmetic to exact Python integers before negation, endpoint arithmetic, products and Decimal/index operations. Keep the original permitted NumPy integer arguments passed to the public API and review every shared expectation dependency. A failed diagnostic indexing attempt is retained separately; it supplies no product evidence.
