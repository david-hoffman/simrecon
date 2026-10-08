# Measured explicit-policy carrier selection

The implemented selector returns the unique passing row for the restrictive policy,
no row for the tighter residual policy, and ambiguity for permissive or duplicated
passing rows. The sparse and one-pair fixtures also pass their explicit policies;
neither establishes a physical carrier. See the
[contract](../contracts/carrier-selection-v1.md) and
[executed usage](../usage/carrier-selection.md).

## Independent method and inputs

The accepted read-only `tests/carrier_selection_fixture.py` supplies expectations.
It solves the represented phase matrix `[1, cos(psi), sin(psi)]` with exact rational
arithmetic on stored float64 observations and trigonometric entries. Each final
coefficient converts once to float. Separate explicit finite Fourier sums use the
negative forward sign and divide by the pixel count. For each closed-grid overlap,
the oracle calculates `x=H(q+k)*D0(q)`, `y=H(q)*Dplus(q+k)`, then
`z=sum(conj(x)*y)/sum(abs(x)**2)` and `norm(y-z*x)/norm(y)`.
Production separation, Fourier transforms, calibration and scan outputs supply no
numerical truth. Modulation is `2*abs(z)` and phase offset is `arg(z)`. The policy
conjunction is checked independently from these expectations and also against the
actual returned diagnostics. Limits are far from roundoff-sized decision boundaries.

The off-model fixture is a 5 by 7 pixel periodic acquisition at (dy, dx) = (0.7, 1.3)
micrometres. Its object Fourier-series DC is 2; modes (0,1), (1,0), (1,1) are
0.3+0.1i, 0.2-0.05i, 0.12+0.07i, with their conjugates. The injected primary carrier
is (0,+1) detector bins and gain is `0.4*exp(0.63i)`. The full complex OTF is
`H(ky,kx)=0.5+0.3*exp(-2*pi*i*ky/5)+0.2*exp(-2*pi*i*kx/7)`.
Its source label is `  independent selector finite-sum fixture  `, retaining spaces.
The origin is (0,0); centered signed modes divided by the respective field of view
give axes in cycles per micrometre. Relative steps are [-0.4,0.7,1.9,3.4,5.2] rad.
Off-model additions to the plus spectrum are 0.035-0.021i at array index (1,1)
and -0.025+0.017i at (3,4). Thus the expected stored-data fit is not exactly the
injected model gain, and this landscape has no asserted single physical truth.

The sparse fixture has shape (5,1,5), unit OTF, DC 2, and
`c1=2.4*exp(0.4i+2*pi*i*x/5)`. The factor of two in acquisition synthesis makes
its regression gain `1.2*exp(0.4i)` and modulation 2.4. Only one mode is informative,
despite four geometric pairs for carrier (0,1). Its steps are [0,0.8,2.2,3.7,5.5] rad.

The one-pair fixture uses those same steps and unit OTF, with
`dc=3+0.3*cos(-4*pi*x/5+0.2)` and `c1=0.1*exp(4*pi*i*x/5+0.7i)`.
At carrier (0,4), only q=-2 and q+k=+2 overlap:
`x=0.15*exp(0.2i)`, `y=0.1*exp(0.7i)`, so
`z=(2/3)*exp(0.5i)` and modulation is 4/3. This illustrates an exact scalar fit
on one complex pair, without a physical-carrier interpretation. Both small fixtures
retain spacing (0.7,1.3) micrometres, origin (0,0) and the fixture source label.
The all-local-failure fixture copies the off-model calibration/steps but replaces
all observations with zero. Zero information and empty geometric overlaps supply
analytic failure expectations without dividing zero energy in the oracle.

## Actual fits and independent deviations

The table shows the off-model rows in supplied order. Row 3 is the late candidate
(100,0), which remains in every full landscape with `no_illumination_overlap`.

| Row | Carrier (y,x), bins | Actual gain, real + imaginary | Actual modulation | Actual phase, rad | Actual residual | Pairs |
|---|---|---|---|---|---|---|
| 0 | (0,0) | 0.103591610088 +0.0322129463071i | 0.216969081579 | 0.301482138060 | 0.951427955055 | 35 |
| 1 | (0,1) | 0.322227463274 +0.235458874108i | 0.798176470423 | 0.631048957454 | 0.0442239700679 | 30 |
| 2 | (0,2) | 0.0790935559354 +0.113526445065i | 0.276724009219 | 0.962290450628 | 0.951294340197 | 25 |
| 3 | (100,0) | — | — | — | — | 0 |

| Row | Independent gain, real + imaginary | Independent residual | Gain deviation | Residual deviation |
|---|---|---|---|---|
| 0 | 0.103591610088 +0.0322129463071i | 0.951427955055 | 1.010e-16 | 2.220e-16 |
| 1 | 0.322227463274 +0.235458874108i | 0.0442239700679 | 1.241e-16 | 6.245e-17 |
| 2 | 0.0790935559354 +0.113526445065i | 0.951294340197 | 1.963e-17 | 1.110e-16 |

All three off-model rows satisfy the inherited informative regime: matrix condition
1.6216, both overlap norms above image peak/8 = 0.681159, correlation above 0.25,
and gain magnitude between 1e-4 and 10. The inherited absolute budget is
`8192*5*35*2^-52 = 3.1832314562e-10` for gain (times max(1,abs(z))) and residual.
This is a project numerical acceptance budget, not a physical accuracy promise.
Across all ten cases, the largest actual-versus-independent gain deviation is
4.335559509131367e-16 and residual deviation is 2.220446049250313e-16.

| Landscape | Actual gain, real + imaginary | Actual modulation | Actual residual | Independent residual | Geometric pairs |
|---|---|---|---|---|---|
| Sparse (0,1) | 1.10527319280 +0.467302010770i | 2.4000000000000004 | 2.93029623625e-16 | 2.87357224745e-16 | 4 |
| One-pair (0,4) | 0.585055041260 +0.319617025736i | 1.3333333333333328 | 0 | 1.38777878078e-16 | 1 |

Both also agree with their analytic gains within 2e-10. The one-pair fixture is
outside the general informative regime because its overlap norms are small relative
to image peak. Its small observed error is fixture evidence, not a uniform digit
promise. Computed zero residual and independent roundoff-sized residual agree
within the explicit comparison tolerance; neither is rounded into a decision.

## Policy outcomes

Each comparison asserts the independently expected eligible indices, selected
index and failure code. It also checks every actual diagnostic against the exact
inclusive predicate. Every row and local failure remains available.

| Case | Residual maximum | Minimum geometric count | Modulation bounds | Eligible indices | Selected index | Failure code |
|---|---|---|---|---|---|---|
| Unique | 0.05 | 12 | [0.6,1] | (1,) | 1 | None |
| None | 0.001 | 12 | [0.6,1] | () | None | no_acceptable_carrier |
| Ambiguity | 1 | 1 | [0,20] | (0,1,2) | None | ambiguous_carrier |
| Duplicate | 0.05 | 12 | [0.6,1] | (1,3) | None | ambiguous_carrier |
| Sparse above one | 1e-8 | 1 | [2.3,2.5] | (0,) | 0 | None |
| Sparse physical bounds | 1e-8 | 1 | [0,1] | () | None | no_acceptable_carrier |
| One pair | 1e-8 | 1 | [1.2,1.4] | (0,) | 0 | None |
| One-pair count rejection | 1e-8 | 2 | [1.2,1.4] | () | None | no_acceptable_carrier |
| One-pair duplicate | 1e-8 | 1 | [1.2,1.4] | (0,1) | None | ambiguous_carrier |
| All local failures | 0.05 | 12 | [0.6,1] | () | None | no_acceptable_carrier |

Unique, none and ambiguity use [(0,0),(0,1),(0,2),(100,0)]. Duplicate uses
[(100,0),(0,1),(0,2),(0,1)]. Sparse cases use [(0,1)]; one-pair cases use [(0,4)]
or two copies of it. All local failures uses [(0,1),(100,0),(0,0)], retaining
`unidentifiable_illumination`, `no_illumination_overlap`, `unidentifiable_illumination`.
Ambiguity persists despite the very different residuals and counts. Repeated rows
are separate policy outcomes, even when the represented carrier is identical.

## Reproduction and provenance

The ignored executable generator is
`artifacts/carrier-selection-execution/C-comparison.py`. Run it from the repository
root with `.venv/bin/python artifacts/carrier-selection-execution/C-comparison.py`.
Its [actual JSON output](../../artifacts/carrier-selection-execution/carrier-selection-comparison.json)
retains all stored images, phase steps, full signed complex OTF values, axes,
metadata, candidate order, unrounded actual and independent diagnostics, corrected
phases, eligible indices and outcomes. It records source/check/lock hashes and
fixture array byte hashes, shapes and dtypes. No plot is needed for this scalar
policy comparison. The generator is task evidence, not a shipped interface.

The frozen fixture SHA-256 is
`e422c78d3fa81b9386ef4d734e09b49d44327b9424048d849b490b67557fd1ba`;
accepted tests are
`f1a09f12a2a04043e02d0d018135ba13ff2ad519a97370fed70c3175c697fddb`;
selection contract is
`5403893fb186145a7cfcee6189e8fdbee12817ffa47e807d6f9605066d183598`.
The lock SHA-256 is
`e6ff14aa7d6c2108292aaef624d150f48876954ff3989e1bc3955ef2aa1ddb2b`.
Source/contract/fixture identities describe the measured inputs; final candidate
identity and canonical verification belong in the external handoff, outside these
tracked report bytes.

Observed environment: macOS 27.0 arm64; current-worktree `.venv/bin/python`,
CPython 3.13.12 packaged by Anaconda; NumPy 2.5.3, SciPy 1.18.1, h5py 3.16.0,
pytest 9.1.1, Ruff 0.16.9, Pyright 1.1.414 and Coverage.py 7.16.2. Imports resolve
to this worktree's `src/simrecon`. Here longdouble has 52 mantissa bits and maximum
exponent 1024, providing no wider range/precision than float64. Inputs use native
float64 observations and complex128 transfer. No external dataset, optical simulator,
legacy implementation or product-output truth is used.

Focused execution passed all 586 selector, scan and illumination tests. Narrow
Ruff lint, format and Pyright passed. The complete usage example ran and its output
matched the documented output. Comparison assertions passed all ten cases. Logs
and command statuses remain in `artifacts/carrier-selection-execution/C-checks.jsonl`.
One initial JSON export failed because an oracle comparison yielded NumPy bool_
rather than a Python bool; converting that evidence predicate to bool repaired
serialization without changing product code, fixtures or numerical expectations.

`make check UV=/Users/davidhoffman/.local/bin/uv` stopped at locked synchronization
with status 2: the sandbox denied access to the default uv cache. No quality phase
ran under that command. Direct narrow checks above used the existing environment.
The coordinator must resolve that environment boundary and perform the exact full
local gate and required fresh review. This report supplies no wheel, vulnerability,
full-suite, coverage-measurement or configured Linux/macOS CI claim.

## Interpretation limits

Selection is solely uniqueness among caller-supplied policy-passing rows. The
comparison demonstrates deterministic policy outcomes on these stored inputs,
not physical-carrier identification, noise robustness, recovery accuracy or
confidence. Residuals on different overlaps measure different data, and geometric
counts include zero-transfer pairs. Sparse or one-pair data can fit exactly; omitted
carriers cannot be recovered. Even above-one modulation is a valid diagnostic when
the caller accepts it. Reconstruction separately enforces its physical modulation
range and explicit inputs. No ranking, hidden limits, fallback, automatic
reconstruction or new scientific estimator is introduced.
