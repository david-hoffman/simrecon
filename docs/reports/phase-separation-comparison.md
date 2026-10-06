# Actual seven-phase separation comparison

![All seven inputs and fitted-input residuals, independent expected and actual signed coefficients, and absolute errors](../figures/phase-separation-comparison.png)

The figure shows actual public `simrecon.separate_phases` outputs from the unchanged
[frozen `analytic_fixture()`](../../tests/phase_separation_fixture.py), using its
default **9 × 14 pixel** spatial shape and **seven unequal phases**. Intensities
use arbitrary common units (a.u.). x increases rightward and y downward.
The arrays were neither resized, resampled nor altered. Nearest-neighbor display
shows their original pixel grid. The analytic example has no added noise or
optical blur; it is phase separation at acquired sampling, with no high-resolution
reconstruction or golden screenshot claim.

The [approved contract](../contracts/known-phase-separation-v2.md) and
[usage guide](../usage/phase-separation.md) define the numerical meaning.
The input images, phases and stored matrix `H` are float64. Ordinary conversion
therefore preserves these fixture values. The fixture generates signed asymmetric
fields on x,y coordinates spanning [-1,1]:

```text
A = 1.2 + 0.4*x - 0.7*y + 1.8*exp(-((x-0.31)^2/0.09 + (y+0.22)^2/0.21))
R = -0.9 + 0.65*x + 0.31*sin(2.1*y+0.3)
J = 0.6 - 0.47*y + 0.8*exp(-((x+0.42)^2/0.16 + (y-0.37)^2/0.07))
generating dc = A; generating c1 = R+i*J
stored I[p] = A + 2*R*H[p,1] - 2*J*H[p,2]
H[p,:] = [1, np.cos(phases_rad[p]), np.sin(phases_rad[p])]
K = H @ diag(1,2,-2)
```

The represented phases and H entries used in both generation and fitted-value
evaluation are listed below; values are printed with 17 significant digits.

| Input | Phase (rad) | H constant | H cosine | H sine |
|---|---:|---:|---:|---:|
| I0 | -0.42999999999999999 | 1 | 0.90896574967488508 | -0.41687080242921076 |
| I1 | 0.20999999999999999 | 1 | 0.97803091472414827 | 0.20845989984609956 |
| I2 | 1.3400000000000001 | 1 | 0.22875280780845939 | 0.97348454169531939 |
| I3 | 2.5699999999999998 | 1 | -0.84104046084620143 | 0.54097222037698856 |
| I4 | 3.1800000000000002 | 1 | -0.99926252853272091 | -0.038397904505235378 |
| I5 | 4.7300000000000004 | 1 | 0.01761010929230725 | -0.99984493000200436 |
| I6 | 5.8099999999999996 | 1 | 0.89012118569526522 | -0.4557239019148055 |

Independent expected arrays use exact rational least-squares algebra on the
actual stored float64 observations and represented K entries, rounded once
to float64 for display. Product outputs supply no expected values. Generating
fields are distinct from that stored-value truth. Their maximum differences
from rounded stored expectations are 2.2204460492503131e-16 a.u. for each of
dc, Re(c1) and Im(c1). The frozen public tests independently certify the
actual outputs for all 126 fixture pixels under the approved backward-error
policy; the display differences below are against rounded expectations.

## Shared scales and measured differences

Every raw image appears, and all seven raw panels share a zero-centered signed
scale [-5.2832256111555917, 5.2832256111555917] a.u.
Actual raw range is [-2.6840562539851507, 5.2832256111555917] a.u.
Each expected/actual coefficient pair shares its own zero-centered signed scale;
blue is negative and red positive. All three absolute-error maps share
[0, 1.3322676295501878e-15] a.u. No data are clipped.

| Component | Expected/actual signed scale (a.u.) | Maximum absolute difference (a.u.) | Root mean square difference (a.u.) |
|---|---:|---:|---:|
| dc | [-3.2136351524823894, 3.2136351524823894] | 8.8817841970012523e-16 | 2.7625303311322876e-16 |
| Re(c1) | [-1.8518927655722408, 1.8518927655722408] | 6.6613381477509392e-16 | 3.241700595263682e-16 |
| Im(c1) | [-1.1286760553580608, 1.1286760553580608] | 1.3322676295501878e-15 | 7.8470737137831559e-16 |

The represented H singular values are 2.7374648326916931, 2.0428936462632206, 1.5273741649751715.
Its spectral condition number is 1.792268649991335. The project
backward-error budget is `eta=128*7*2^-52=1.9895196601282805e-13`.
That dimensionless budget constrains matrix/right-hand-side perturbations;
it is not an absolute intensity tolerance or a universal useful-digit guarantee.
Near-cutoff and off-model behavior is exercised numerically in the frozen tests.

## All fitted-input residuals

Every residual panel uses the actual returned values and the stored H:

```text
fitted[p] = dc + 2*c1.real*H[p,1] - 2*c1.imag*H[p,2]
residual[p] = fitted[p] - stored I[p]
```

No exponential reimplementation supplies the fitted values. All seven residual
maps share the signed scale
[-3.3306690738754696e-15, 3.3306690738754696e-15] a.u.

| Input | Maximum absolute actual fitted-input residual (a.u.) |
|---|---:|
| I0 | 1.3322676295501878e-15 |
| I1 | 2.4424906541753444e-15 |
| I2 | 3.3306690738754696e-15 |
| I3 | 1.3322676295501878e-15 |
| I4 | 1.7763568394002505e-15 |
| I5 | 2.6645352591003757e-15 |
| I6 | 8.8817841970012523e-16 |

The actual residual root mean square across all 882 observations is 1.0509078343108564e-15 a.u.
The independent exact stored-value minimizer has maximum absolute residual
5.3516910836475646e-16 a.u. (rounded for this summary). That small
nonzero residual arises from forward-generation rounding. Actual residuals also
include solver error and float64 fitted-value evaluation rounding; they are not
themselves coefficient-error estimates. Arbitrary off-model observations can
have much larger legitimate least-squares residuals. This noiseless figure
does not represent that case; frozen numerical tests cover it.

## Reproduction and identities

Actual local renderer command (from the worktree root):

```sh
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/simrecon-nf02-v2-20261005/matplotlib-config /private/tmp/simrecon-nf02-20261005/plot-venv/bin/python /private/tmp/simrecon-nf02-v2-20261005/C-render-comparison.py
```

The renderer imports this worktree src and the frozen test fixture. It appends
the already installed worktree Python site-packages for the unchanged MRC
public import dependency h5py. The external plotting environment supplies
Python 3.13.12, NumPy 2.5.3, Matplotlib 3.11.0 and Pillow 12.3.0;
worktree h5py is 3.16.0. Observed platform is Darwin arm64, backend Agg.
No installation, project dependency or lock change was made. All actual
module paths and environment inputs are recorded locally.

| File | SHA256 |
|---|---|
| Frozen fixture | `519a41115bb05ba17f369ebe77466b567c08a9417db70be17043e9128b25485b` |
| Frozen tests | `becb7c1d737e1fb4ea69dc9a2db11e606c78b178c74f5692543f4d04a4a09f99` |
| Approved contract | `af8b0bc503a2c6d73ed54d0cd21083ded11e26007a32b1fd320d11254018562d` |
| Candidate _phase.py | `92ff9728f0362cd37cadd130da0ebd02325d10cf2ff365095a1e6e2a86f539a4` |
| Local renderer C-render-comparison.py | `0804275f30ca48b8631bf3d329f192449f8ba7942619b0452565feaeef473b9a` |
| PNG | `464247a7de1211ac17ceee85517dcea8971bff4fbc067359434eaf542373fba1` |
| Local array archive C-comparison-arrays.npz | `7bd0536bfa208fc66dce728f39f64e47475f5562e5282556c61cca40192ea18e` |

Array SHA256 identities hash compact sorted JSON containing `shape` and
`dtype`, then a newline byte, then C-contiguous little-endian array bytes.
Strided real/imaginary views are copied only for hashing and display.
All original fixture arrays remain unchanged.

| Array | Shape | Dtype | SHA256 |
|---|---|---|---|
| `phases_rad` | `[7]` | `<f8` | `50c83a199d2db7aee5e0599f007716d992252527ca926bfcf8dea185f6e9e6fd` |
| `h` | `[7, 3]` | `<f8` | `fdc2913b759002f31224dd07004480e7f26d49fd414f6a728be6ebb300eab6a5` |
| `images` | `[7, 9, 14]` | `<f8` | `5de11eb69c71a7a78c1eaf2d85c81d16139cf7251547158e1ed65d88e662fbd4` |
| `generating_dc` | `[9, 14]` | `<f8` | `dd554cf4d63b8eb54a4849e6f4388cfd6830e641cc41136ec24d634a6dae4bc3` |
| `generating_c1` | `[9, 14]` | `<c16` | `e627dd70d2f18326cbe3cfd0830619214f6f6a7ac55afe2ae9f446fb886123da` |
| `expected_dc` | `[9, 14]` | `<f8` | `d98caa8b9e60a8f66f1f614e98823e063e8521f15ca19f66393202b355b0dbc8` |
| `expected_c1` | `[9, 14]` | `<c16` | `b0bae7448a86a0936533c3f7ff432cc85763163b1c586a8bd413508a5feb8f61` |
| `expected_residuals` | `[7, 9, 14]` | `<f8` | `8a102758129f0d30cb4e462de6109ce7636ab65b8ded59d607f6d2c7930848a2` |
| `actual_dc` | `[9, 14]` | `<f8` | `f4d4bc44c412b680d4d1a9ea3ffbbc3fbb62f6ce8039a66bb43598c662554025` |
| `actual_c1` | `[9, 14]` | `<c16` | `d0b247a37961c36489458557085a7910b2805662a4f18f028314b34dc9ebd0bc` |
| `fitted` | `[7, 9, 14]` | `<f8` | `de474cbb23a30c311160cd1217f1997f9798bf1f1f159cc1854aff90f0a812ad` |
| `actual_residuals` | `[7, 9, 14]` | `<f8` | `104660e4a8d5d97aaa6fe127c591db8ff37b9c8d8d0c3321b760797fdcbb1f55` |
| `absolute_error_dc` | `[9, 14]` | `<f8` | `8a041744b488e9f9ddc2c2708ea0e0f8f425cafef76ec7faf3f5139172fa5e2b` |
| `absolute_error_Re(c1)` | `[9, 14]` | `<f8` | `833c196155cfd455eb0edf139e89e32e88906bdcf57efd4c35186013e03f82db` |
| `absolute_error_Im(c1)` | `[9, 14]` | `<f8` | `014276c1bbdf7aeb9f7a0e1794328f5c0a26accfef7eb73452075061b39bc72d` |

The local renderer, `C-comparison-arrays.npz` and
`C-comparison-provenance.json` live under `/private/tmp/simrecon-nf02-v2-20261005`.
They are evidence, not shipped runtime or a plotting dependency, and may be
absent in a clean clone. The frozen fixture, stored equations, API and recorded
renderer identify the comparison. C viewed the real PNG and checked all panels,
labels, sign conventions and shared scales. Independent D correspondence
review remains pending.

Final candidate commit, exact canonical `make verify` results, fresh D verdict
and configured continuous integration (CI) results belong outside these tracked
bytes. The coordinator will fill the local sidecar or external handoff after
committing and verification. Focused C checks do not establish the full gate.
