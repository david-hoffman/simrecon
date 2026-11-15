# Issue 115 exact test preparation delta

Source-free test evidence only; no runtime source/history/coverage content.
Coordinator reconstructed the four initial test revisions from the exact final
bytes using the initial test text observed before preparation and cosmetic
changes. Each reconstructed byte sequence matches the independently recorded
initial-run SHA256 in A's report exactly; all four matches were required before
writing this evidence. No test or product execution was used. This is not a new
behavioral run or an acceptance verdict.

| Test file | Verified reconstructed initial SHA256 | Final prepared SHA256 |
|---|---|---|
| tests/test_wide_allocation_domain.py | a16ec25abc105e48a2352babb221cd3d7eb30aac62f93d4dc4cbcd7d4188a961 | 016c47bcbdff42b41c90b01a1c2f07af459c09574b0f127b1655e8c327d84360 |
| tests/wide_allocation_fixture.py | 205836da05dbc17d3e22356a6a715e30501ae0b4f955726adb7ae1db4997aaf6 | 09c7ac15b02226f986b17f12a244056654b1166b5accbd2c4407a5f7cb3e94c8 |
| tests/test_c_known_boundary.py | 9f17a12b32c70273e63dc87d0f5f28cc577dfa728e52246550a345a6a1cece50 | 1125ff758f2cade00fd007c6dbdb54b31eef4e93cf4f109a97292526e4efd6b9 |
| tests/test_c_acquisition_boundary.py | ac66e1fbba22b2b0027556de70b5f47e2512838c1263a9215ffeee38ab760f86 | 590d03ac6370b73294af1783f8e55eed1ffd932a1e50d2b80c7b8a56053b56b0 |

The adjacent behavior-to-prepared.diff is the complete unified difference from
those exact reconstructed initial bytes to final prepared bytes. Its SHA256 is
8f9f86c09ad3480a83dad6aff4637863d75bc0516e236376633ef39472dcbb39. The workflow-validation and summary
files retain identical initial/final digests as already recorded in A report.
B independently assesses the delta and retained proof applicability; the
coordinator supplies bytes/hashes, not a semantic acceptance assertion.
