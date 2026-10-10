# Translation comparison on stored inputs

The actual public operation was compared with the B-accepted independent
finite-sum oracle on eight stored input pairs. Every full surface and candidate
set passed. The largest observed absolute score error was
`1.1102230246251565e-16`. This supplemental comparison supports the
[approved finite objective](../contracts/translation-estimation-v1.md);
independent candidate review and canonical exact-candidate verification remain
separate obligations.

Run from the repository root with the existing worktree environment:

```sh
.venv/bin/python artifacts/translation-execution/C-comparison.py
```

The script writes and reloads
[`translation-comparison-inputs.npz`](../../artifacts/translation-execution/translation-comparison-inputs.npz)
before calculating either expected or actual values. The
[complete JSON](../../artifacts/translation-execution/translation-comparison.json)
retains every surface, canonical coordinate, minimum, candidate set, tolerance,
error, input dtype/shape/byte hash, archive hash and source/environment identity.
Scores are dimensionless root mean square (RMS) mismatches.
These task-local artifacts are ignored evidence; retain them with the handoff.

Expected values **reuse** `tests/translation_fixture.py` from B-accepted
checkpoint `9c5fe7eb5156b1f1ef5c8938a52c8c6babe608f1`. This is independent of
the product implementation, not a newly authored oracle or another independent
role review. Fixture SHA256:
`2466e242090c55c370d28046de5fc4335bffa6321fb44f33e98a92a7725013df`.
Known motion uses the fixture's explicit modular-index generator. The oracle
represents converted float64 pixels exactly as rational numbers, sums squared
differences divided by the common scale exactly, and takes a 100-digit Decimal
square root before final float64 rounding. Product output never supplies truth.

All cases use ambiguity tolerance `0.001`. Candidate membership was independently
checked with the fixture's distinguishing-margin requirement. Here `P` is the
number of pixels, and the absolute per-score budget is `4096 P 2^-52`.

| Stored case | Shape `(Ny,Nx)` | Actual minimum RMS | Maximum absolute surface error | Actual and expected candidates, pixels `(y,x)` |
|---|---|---:|---:|---|
| Asymmetric known motion `(1,-2)` | `(3,5)` | 0 | 1.11e-16 | `((1,-2),)` |
| Constructed even half-period `(2,3)` | `(4,6)` | 0 | 1.11e-16 | `((-2,-3),)` |
| Negative motion `(-2,-3)` | `(5,7)` | 0 | 1.11e-16 | `((-2,-3),)` |
| Both zero | `(2,3)` | 0 | 0 | `((-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(0,1))` |
| Repeated pattern | `(1,4)` | 0 | 0 | `((0,-1),(0,1))` |
| Known shift plus offset 7 intensity units | `(3,5)` | 0.2692307692307692 | 1.11e-16 | `((1,-2),)` |
| Near-perfect, one perturbed pixel | `(2,3)` | 3.041686791657381e-9 | 0 | `((-1,1),)` |
| Different raw SIM phases, no specimen motion | `(2,5)` | 0.15723781297232028 | 5.55e-17 | `((0,0),)` |

The three exact known motions align with zero maximum absolute pixel error
after the negative displacement roll. Their score budgets range from
`1.3642420526593924e-11` to `3.183231456205249e-11`. Even half-period output
uses the canonical negative representative. Zero and repeated inputs return
ambiguity with no selected displacement.

The offset case has common scale `B=26`. At the known shift all residuals are
`7/26`, so its analytic normalized RMS is `7/26 = 0.2692307692307692`.
The output remains unique, yet alignment leaves an intensity error of 7.
Uniqueness is not model acceptance. For the near-perfect case, `B=1`, `P=6`
and the stored perturbation is exactly `2^-27`. Thus the analytic minimum is
`2^-27 / sqrt(6) = 3.041686791657381e-9`, about 557 times its
`5.4569682106375694e-12` budget. Direct residual evaluation retains this
nonzero mismatch rather than losing it in an energy-minus-correlation subtraction.

The raw-phase illustration stores these two intensity arrays, generated without
moving the specimen:

```text
object = [[1,2,4,3,7], [5,1,6,2,8]]
reference[y,x] = object[y,x] * (1 + 0.6*cos(2*pi*x/5))
moving[y,x]    = object[y,x] * (1 + 0.6*cos(2*pi*x/5 + pi/2))
```

This is an illustrative ideal intensity model, not a microscope calibration or
optical simulation. The illumination phase changes pixel intensities on a fixed
nonconstant object. None of the integer periodic translations matches the
reference: the independent full-surface minimum is about `0.15724`, and even
the returned `(0,0)` candidate leaves a maximum pixel difference about `3.08179`.
The operation has no phase-separation, brightness fitting or physical reliability
test. Applying it directly to different raw SIM phase frames requires additional
evidence that the equal-intensity translation model actually holds.

Observed environment: Python 3.13.12, NumPy 2.5.3, SciPy 1.18.1, h5py 3.16.0,
macOS 27.0 ARM64. Local `longdouble` has the same range and 52 explicit mantissa
bits as float64; this run cannot establish wider-source conversion behavior on
other platforms. `uv.lock` SHA256 is
`e6ff14aa7d6c2108292aaef624d150f48876954ff3989e1bc3955ef2aa1ddb2b`.
The JSON fingerprints the exact product files and comparison script used.

Only modest arrays were exercised (4 to 35 pixels per pair, plus the 6-pixel
zero case). The method evaluates every shift directly: `P` candidates times
`P` pixels gives `O(P squared)` work. These results make no large-frame speed
claim and establish no fractional/nonperiodic motion, changing-intensity model,
calibrated ambiguity tolerance, noise robustness or physical identification.
Native coverage/report integrity and the full configured platform checks belong
to canonical verification, not this comparison.
