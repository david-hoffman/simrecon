# Volume carrier selection: retained small comparisons

The nine retained C02 cases pass their independent diagnostic and exact policy
checks. They show that explicit limits select a sole row, reject all rows or
retain ambiguity, including duplicates. They also show why an excellent fit
cannot establish a physical carrier. These are finite algebraic examples with
known actual phases and declared calibration, not a full simulator or raw workflow.

All gains, residuals, coherence and policy limits below are dimensionless.
Specimen spacing is z/y/x in micrometres (µm); phases are in radians. The
[contract](../contracts/volume-carrier-selection-v1.md) supplies policy meaning;
the [diagnostics contract](../contracts/volume-carrier-diagnostics-v1.md) supplies
the numerical objective and allowances.

The closed evidence directory is
`artifacts/volume-carrier-selection-20261016/C02/examples/`. It retains the
generator, raw input arrays, expected and returned diagnostic arrays in JSON,
per-field errors/budgets, independent report, exact executed guide block,
commands and logs. This document was written from those retained outputs after
generation. It was not a generation input. The guide was a frozen input and
has not changed since its separate execution.

The current-input generation ran from `2026-10-17T00:06:00.966634+00:00` to
`2026-10-17T00:06:02.572424+00:00`. Its actual commit was
`a0850aae2a8e5f7f58f6e611bebcfe52ab0ca330`, tree
`76db8554f800caa224ddb892dadbd0e08cab5d37`, with clean tracked state
at both generation endpoints. This document was updated afterward from the
retained outputs. These observations describe that actual generation, not a
future final candidate. All 2,693 scientific/dependency input records have equal
before and after pins, including the complete 36-file Python source census,
current reviewed test and unchanged fixture, contracts, lock/build declaration,
guide, generators, managed environment configuration and actual executable.
The additional C02 entry-integrity record is pinned as a dependency used by the
before-generation validation. Endpoint agreement is not an atomic snapshot or
universal process/dependency custody claim.

The fixed closure envelopes are `C02/examples/manifest.json` and
`C02/examples/association.json`. Eight generator/data/report/log members plus
those two envelopes form the complete closed directory. Envelopes are not
self-hashed members or generation inputs. The separate C02 closure wrapper pins
both envelopes. Later postcommit admission and full/platform gates belong to
the coordinator.

The revised test checkpoint is explicitly **POSTIMPLEMENTATION TYPING-ONLY
SUPPLEMENTAL**, accepted by fresh B04. Only line-local accommodations for
intentional invalid argument calls changed; runtime assertions, scientific
expectations, fixture and product remain unchanged. B03's original semantic
proof remains historical; no test-first claim is restored. The changed test
bytes required a new current-input closure. C01's original observations and
all artifacts, including its failed generation, remain preserved. C01's
envelopes were outside its closed root and did not match the reviewed binder's
fixed layout; C02 supplies the required layout without changing any helper or
gate. All nine C02 observations equal the retained C01 observations exactly,
so the numerical tables below describe the actual current run as well.

The asymmetric example uses seven actual unequal phases, a 2×2×3 specimen,
spacing `(1,2,4)` µm, a 4×4×8 full complex empirical response on spacing
`(0.5,0.25,0.125)` µm, calibration carrier `(1,-2)`, coordinate offset `(2,-1)`
and phase-reference shift `0.31` rad. A single stored observation has an added
`0.01953125` intensity-unit perturbation, so the overdetermined fit is off model.
The fixed calibration gauge is identical for every candidate within each call.
Both positive orders use the same fundamental phase schedule.

Independent expectations use the frozen public fixture's 90-digit Decimal
observer, without the product separator, fast Fourier transform (FFT), sampler
or fitter: solve normal equations on the exact represented phase matrix and
stored images; evaluate finite Fourier sums with a 180-term Taylor observer;
evaluate rational-coordinate complex trilinear weights and the constant gauge;
then evaluate the full-pair complex regression. This observer is suitable for
these small well-conditioned examples; the product still uses its inherited
singular value decomposition solver. The observer and its decimal π constant
are retained and pinned as inputs. Float-rounded expected diagnostics add at
most binary64 rounding at reporting precision, far below the applied budgets.

For each geometric pair `j=p+(0,m*ky,m*kx)`, the independent calculation uses

\[
x_p=F_m(f(j))D_0(p),\qquad y_p=F_0(f(p))D_m(j),\qquad
\beta=\frac{\sum\overline{x_p}y_p}{\sum|x_p|^2}.
\]

Here `D` denotes normalized negative-exponent finite Fourier coefficients.
Residual is computed directly from normalized vectors; coherence is amplitude
correlation. Every geometric pair participates. The full JSON retains every
expected/returned value; representative rounded values are:

| Order | Carrier y/x | Pairs | Independent gain | Returned gain | Independent / returned residual |
|---|---|---:|---|---|---|
| 1 | `(0,0)` | 12 | `-0.434820913420-0.122001349868j` | `-0.434820913420-0.122001349868j` | `0.107623643602 / 0.107623643602` |
| 1 | `(0,1)` | 8 | `0.044098973944-0.017617267238j` | `0.044098973944-0.017617267238j` | `0.994471787413 / 0.994471787413` |
| 1 | `(0,-1)` | 8 | `0.037258038616+0.029560031717j` | `0.037258038616+0.029560031717j` | `0.994483214322 / 0.994483214322` |
| 2 | `(0,0)` | 12 | `-0.020404251068-0.130118738224j` | `-0.020404251068-0.130118738224j` | `0.176140604708 / 0.176140604708` |
| 2 | `(0,1)` | 4 | `0.115894903947+0.524671921076j` | `0.115894903947+0.524671921076j` | `0.007646102239 / 0.007646102239` |
| 2 | `(0,-1)` | 4 | `-0.504216586971-0.175825013927j` | `-0.504216586971-0.175825013927j` | `0.009073181346 / 0.009073181346` |

The independent observer propagates the inherited phase, Fourier, transfer and
regression allowances for each actual case. Checks use each stored budget
times `1.000001`, plus `1e-60` for Decimal/truncation margin. These are arithmetic
allowances, not selection tolerances or empirical noise thresholds. Comparing
the largest observed error with the smallest applied allowance in each group
gives a conservative sanity check:

| Cases | Gain: maximum error / minimum allowance | Residual: maximum error / minimum allowance | Coherence: maximum error / minimum allowance |
|---|---|---|---|
| Asymmetric order 1 | `5.56e-17 / 2.28e-9` | `2.23e-16 / 9.59e-9` | `2.23e-16 / 4.80e-9` |
| Asymmetric order 2 | `2.23e-15 / 2.14e-9` | `2.10e-15 / 2.15e-8` | `1.12e-16 / 1.07e-8` |
| Sparse fitted cases | `8.38e-15 / 4.68e-8` | `2.15e-16 / 1.24e-8` | `1.12e-16 / 6.24e-9` |

For the sparse landscape, a 1×1×4 spatial delta produces flat spectra, with
ideal `D1=(3+4j)*D0`. Unit transfers and a zero declared calibration gauge
therefore give `beta=3+4j`, magnitude `sqrt(9+16)=5`, for both distinct carriers
`(0,0)` and `(0,1)` despite different overlaps. Stored-input expectations account
for phase/observation rounding. The returned gains are approximately
`3.000000000000004+4.000000000000007j`; residuals are `0` and
`2.14994e-16`. This supplies the above-one acceptance and misleading equal-fit
example without asserting a hidden physical carrier.

| Retained case | Explicit policy change | Eligible indices | Result |
|---|---|---|---|
| Both asymmetric orders | Residual ≤2, overlap ≥1, gain in `[0,100]` | `(0,1,2)` | Ambiguous |
| Sparse equal fits, duplicate `(0,1)` | Residual ≤`1e-10`, gain in `[4,6]`, overlap ≥1 | `(0,1,2)` | Ambiguous; duplicate rows count separately |
| Sparse sole acceptance | Same, overlap ≥4 | `(0,)` | Sole row; the gate merely prefers the larger geometric overlap |
| Sparse no match | Overlap ≥5 | `()` | No acceptable row |
| Retained no-overlap row | Middle carrier `(0,4)` | `(0,2)` | Ambiguous, middle row retained with absent diagnostics |
| Zero predictor | Selected response row zero | `()` | `zero_predictor/no_overlap/zero_predictor`; all diagnostics absent |
| Incomplete coverage | Specimen spacing `(0.01,0.01,0.01)` µm | `()` | `incomplete_coverage/no_overlap/incomplete_coverage`; all diagnostics absent |
| Zero response | Zero-order response row zero | `(0,2)` | Numeric zero gain/residual/coherence passes the permissive policy |

Every case independently checks the exact policy relation on actual returned
diagnostics. In particular, the gain gate evaluates
`lower² <= real(beta)²+imag(beta)² <= upper²` with rational arithmetic on
represented binary64 values. This proves the selection relation separately
from numerical agreement. Unavailable outcomes and zero-response conventions
are checked against their public contract, outside the nonzero-norm observer.

The guide's exact code block ran separately with exit 0. Order one returned
`3.0000000000000013+3.999999999999999j`; order two returned
`-2.0000000000000013+1j`. Both selected index zero and retained a no-overlap
row. Its extracted block SHA-256 is
`28d18247cf8673d5f7a25a1875240978a686695de0d8c22f0d05b329cd211a40`.
These values come from the retained log, not a reporting rerun.

One failed prior generation is preserved under `C01/failed-generation01/`.
Its example mistakenly sent an unavailable order-two candidate to the
nonzero-norm independent observer, causing Decimal division by zero. Correcting
the example candidate to a covered lateral shift left product and frozen tests
unchanged. Intermediate values from the failed run were not retained and are
not claimed. The successful generation checks all three candidates in both
asymmetric orders.

Arithmetic agreement does not validate empirical calibration, actual unknown
phases, optical modeling, informative support, alias resolution or physical
identification. Different overlaps compare different data. A sole row under
one finite list and policy gives no uniqueness beyond that list and no
confidence probability. Full raw-workflow simulation, owner-data/reference
parity and separately qualified platform/full-gate evidence remain outside
these comparisons.
