# Independent OTF calibration examples

**Version 1.0.** October 6, 2026. These are public intake examples for the [calibration contract](../../contracts/otf-calibration-v1.md), not executable tests or an A/B-reviewed checkpoint.

## Exact expectation sources

Every mathematical case follows the normalized negative-exponential discrete Fourier sum for the **converted** float64 samples and explicit origin. The [JSON file](otf-calibration-fixtures-v1.json) records input integers, origin, binary-exact spacings `(0.125,0.25)` µm, signed mode lists, rounded frequency vectors and rounded complex expected values. The formula is authoritative; future tests must independently derive a sufficiently accurate oracle, not compare tightly against rounded JSON or another FFT call.

| Case | Input / origin | Exact transfer in declared shifted order |
|---|---|---|
| `delta-odd` | `(3,5)`, mass 7 at `(1,2)`; origin `(1,2)` | All bins one, independent of input gain |
| `uniform-even` | `(4,6)`, every sample 5; explicit origin `(1,2)` | DC at `(2,3)` is one; all other bins zero by root-sum orthogonality |
| `asymmetric-even` | `(4,6)`, masses 3 at `(1,2)`, 1 at `(2,2)`, 4 at `(1,3)`; origin `(1,2)` | `3/8 + exp(-2*pi*i*ky/4)/8 + exp(-2*pi*i*kx/6)/2` |
| `asymmetric-translated` | Same masses after circular shift `(-1,+2)`; origin `(0,4)` | Same complete transfer as the preceding case |
| `separable-mixed` | `(3,4)`, outer product `[1,2,1]` and `[1,0,1,0]`; origin `(1,0)` | Outer product of `(1/4,1,1/4)` and `(1,0,1,0)` |
| `singleton` | `(1,1)`, mass 7 at `(0,0)` | Transfer one; both frequency vectors contain only zero |

The separable example has total mass 8. In y, origin subtraction gives displacements `(-1,0,+1)` with weights `(1,2,1)/4`; hence `(2 + 2*cos(2*pi*ky/3))/4` is `(1/4,1,1/4)`. In x, displacements `(0,2)` each have weight `1/2`; `(1 + exp(-pi*i*kx))/2` is `(1,0,1,0)` for `kx=(-2,-1,0,1)`. Multiplying independently normalized factors gives the full array without an FFT oracle.

The asymmetric example's total mass is also 8. At `ky=0,kx=1`, the y terms sum to `1/2`, while the x term is `(1/2)*(1/2 - i*sqrt(3)/2)`. Therefore `H=3/4-i*sqrt(3)/4`. At `ky=1,kx=0`, `H=7/8-i/8`. At both negative Nyquist modes, `H=3/8-1/8-1/2=-1/4`. These values distinguish axis swaps, conjugation, discarded phase, peak normalization and an extra transform scale.

For the `(4,6)` examples, spacing gives `dfy=1/(4*0.125)=2 cycles/µm` and `dfx=1/(6*0.25)=2/3 cycles/µm`. The y bins are `(-4,-2,0,2)` and x bins `(-2,-4/3,-2/3,0,2/3,4/3)` cycles/µm. The unequal spacings and unequal dimensions provide an axis sanity check.

## Range and rejection examples for independent A/B

These further examples define existing contract scenarios, not a second hidden operation:

- `(1,2)` with `[max,max]`: both samples convert to maximum finite float64. Exact normalized masses are `(1/2,1/2)` despite an overflowing raw float64 sum. Shifted transfer is `(0,1)`.
- `(1,2)` with `[q,3q]`, `q=2^-1074`: normalized masses `(1/4,3/4)` give shifted transfer `(-1/2,1)`. Underflow of an unscaled intermediate must not lose the useful result.
- `[max,q]` and `(1,4)` `[1,q,0,0]`: independently derive exact converted-value ratios. The absolute transfer error budget permits a tiny coordinate to vanish; no relative/subnormal-retention guarantee is implied.
- Positive gains preserve H only when the resulting converted arrays remain exactly proportional. Rounding/underflow can change ratios, so compare each call with its own converted-value oracle.
- Change origin while holding a displaced delta fixed: its exact phase is the negative exponential of displacement. Translate both samples and origin to preserve H. Include wraparound displacements without allowing an out-of-bounds origin argument.
- `(1,1)` spacing `(q,max)` must succeed with zero frequency axes. A nonsingleton axis with spacing `q` may fail because its nonzero frequencies overflow. A small nonsingleton axis with spacing `max` must succeed when its distinct nonzero subnormal bins are representable; do not overflow `N*d` unnecessarily.
- Pair rejected negative samples with permitted negative zero/nonnegative data. Validate wider source values before conversion where the platform truly supports them; do not pretend float64-equivalent longdouble provides wider-range evidence.

Future A maps all K01–K29 to public-entry checks, independently derives accuracy/rounding budgets and supplies paired positive examples. B must assess this complete shared expectation set. Neither stored JSON, an initially passing reference FFT nor the optical illustration is product-red evidence.

## Observed intake consistency and display

The local preparation cross-checks exact delta/uniform/separable identities and algebraic asymmetric roots against a separate NumPy FFT used only for consistency and display. Recorded residuals and environment/artifact identities are in the [manifest](otf-calibration-intake-manifest.json). These observations verify the example package, not a product implementation. The exact formulas retain authority over rounded display tables.

The [preview](../../figures/otf-calibration-intake-preview.png) uses equal signed `[-1,1]` limits for independent analytic real/imaginary components. Rows increase upward in physical displays. The bottom row is a separately simulated Pyotf optical example; its PSF panel crops only the display to 31×31 samples, while its transform uses the full 257×257 kernel. No numerical crop or support threshold is applied to its OTF. No recovered/actual SIMrecon panel exists.
