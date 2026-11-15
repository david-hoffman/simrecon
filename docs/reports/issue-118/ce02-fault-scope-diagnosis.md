# CE02 external-fault test scope diagnosis

Nonblind coordinator evidence; excluded from A/B read inputs. No independent
review verdict, product correction or new public requirement is recorded here.

At committed baseline32d9c9651f9ca884cbec31793cb80d47571e0645 (product bytes
unchanged from public64a752b4), A3's source-free owned run reported26passes/1fail,
then the targeted row observed the injected generic FFT RuntimeError rather
than its asserted SimreconError. All twelve command/status logs, two formatter
repairs and hashes are in `a3-focused-checks.md`; no process remains running.
Observed test hash before semantic correction:
5df2ac664b0550998aa88345ad156e81155ce9542eba99fa14eb8770a442b88e.
Focused report hash244238db337b102dad19ef16582eb19ee4648dee5e942909b75425344b53f7a1.

Public CE02's errors section explicitly covers backend FACTORIZATION failure,
nonfinite phase matrices/noise, overflow/nonfinite correction/sums/gains/transforms
and alpha via SimreconError, allocation as MemoryError, interruption as
interruption. It does not establish universal translation of every arbitrary
third-party FFT RuntimeError. CE04/CE06 explicitly state broader backend/allocation
translation/cause rules. PH118 S25 inherits these distinct API-specific contracts;
the common CE contract adds no universal exception-wrapper requirement.

For baseline diagnosis only, coordinator statically read
`src/simrecon/acquisition/preparation.py`: public preparation's transform calls
and finite checks are within the numerical operation region, which translates
FloatingPointError, OverflowError and NumPy LinAlgError, not generic RuntimeError.
This explains the observed injection result; it supplies no new expectation to
blind A. No product source/history is included in the sanitized correction.

Classification: test-scope/oracle overgeneralization in the newly authored S25
CE02 backend row. It is not valid approved product-red, an environment failure,
or an identified new scientific decision. Broadening CE02 to wrap arbitrary FFT
exceptions would require a separate concrete contract/ownership decision and
touches preparation.py outside PH118 C scope. No such dependency is required to
complete the existing preservation task, and no such runtime change is authorized.

Scoped correction: retain failed bytes/logs/hashes; keep CE02 allocation and
interruption controls and CE04/CE06 backend controls unchanged. Replace the
unsupported CE02 universal-FFT assertion with an independently designed witness
of the explicit factorization guarantee on valid declared supplied full-rank
phases, using only public external dependency controls and an independently
bounded finite positive if a legitimate backend avoids interception. No mandatory
binding, expectation of arbitrary-error propagation, tolerance widening or
product seam. Same blind A3 owns this test-only correction; fresh B reviews the
entire exact revised checkpoint and mapping before C. Actual interception must
not be inferred from ordinary pass counts. Selected keeper checks remain pending.
