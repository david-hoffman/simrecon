# Measured known-phase volume comparison

The executed `separate_volume_phases` candidate agrees with an independent
stored-input least-squares observer in all four cases below. Every returned real
coordinate meets its own voxel's contract budget. This is focused implementation
evidence; clean canonical verification and fresh D review remain separate gates.

Inputs come from the frozen independent
[fixture](../../tests/volume_phase_fixture.py), using distinct signed coefficients
on z/y/x and both nonzero harmonics. The observer lifts the stored float64
observations and represented basis entries exactly into 120-digit Decimal
arithmetic. Its scaled normal equations are used only for independent
expectations. The product uses float64 singular value decomposition (SVD).
The comparison never uses product output as its reference.

For coordinates `(dc, c1.real, c1.imag, c2.real, c2.imag)`, the permitted absolute
error is `8192*N*2^-52*B + 8*2^-1074`, where `B` is the maximum absolute converted
observation at that voxel. For `N=8`, the intensity-scaled term is
`1.4551915228366852e-11*B`. Errors and budgets were compared in Decimal so the
smallest positive budgets could not underflow.

| Case | Acquisition shape | Independent upper bound on cond₂(H) | Maximum error / local budget | Maximum absolute coordinate error, intensity units |
|---|---|---:|---:|---:|
| Represented on-model | `(8,2,3,4)` | 1.655065 | 0.00002227 | `7.6215e-15` |
| Off-model projection | `(8,2,3,4)` | 1.655065 | 0.00002340 | `8.4782e-15` |
| Direct huge phases | `(14,2,3,4)` | 2.806513 | 0.00004199 | `2.3245e-14` |
| Mixed voxel scales | `(8,2,2,2)` | 1.655065 | 0.027396 | `1.7777e292` |

The eight unequal phases are `[-0.2, 0.43, 1.21, 2.04, 2.9, 3.63, 4.57, 5.38]`
radians. At the first on-model voxel the returned coordinates are approximately
`(10, 2, -1, 3, 4)`, giving `dc=10`, `c1=2-1j`, `c2=3+4j`. The public
[usage example](../usage/volume-phase-separation.md) was also executed verbatim;
it printed `9.999999999999995`, `(2.0000000000000004-1.000000000000001j)`,
and `(3+4j)`.

The off-model case adds 3.25 intensity units to exposure 1 at every voxel and
subtracts 7.5 from exposure 5 at voxel `(1,2,3)`, with zero-based indices.
Its first returned coordinate row is
`(10.353535639349559, 2.327563601735023, -1.1628142414178735,
3.2112089302835702, 3.6834483134780083)`.
The independent first-voxel DC differs from the sample mean by
`-0.7371111507203732` intensity units.

| Case | Maximum independent residual | Maximum returned-fit residual | Maximum returned fit minus independent fit |
|---|---:|---:|---:|
| Represented on-model | `1.2949e-15` | `1.1396e-14` | `1.0998e-14` |
| Off-model projection | `2.9604965294436664` | `2.9604965294436610` | `1.1782e-14` |
| Direct huge phases | `1.4772e-15` | `5.6374e-14` | `5.6087e-14` |
| Mixed voxel scales | `3.9931e291` | `2.8055e292` | `2.4952e292` |

All residual quantities use maximum absolute observation-coordinate error in
input intensity units. The small on-model oracle residual comes from rounding
observations to float64. The off-model residual is projection mismatch, distinct
from numerical solver error. Predictions and residuals were evaluated in Decimal
before storage to avoid intermediate overflow.

The mixed case contains independent voxel scales `1e-200`, `1`,
`float64_max/64`, `2^-1074`, `0`, `2^-1022`, `1e100`, and `1e-100`.
Its large absolute maximum reflects its bright voxel. The budget ratio checks
every coordinate against its own local intensity and includes the subnormal
allowance; it does not normalize errors by the brightest voxel.

The huge-phase case includes finite angles near positive and negative float64
maximum. It evaluates `c=cos(phi)`, `s=sin(phi)`, then `c*c-s*s` and `(2*c)*s`
in the declared order. It never forms `2*phi` or reduces modulo rounded `2*pi`.
This checks the represented finite-angle model, with no exact-real trigonometric
or bitwise cross-platform claim.

Reproduce from the repository root with:

```sh
.venv/bin/python artifacts/roadmap-next-execution/C-comparison.py
```

The local review artifacts use these relative aliases:

- `artifacts/roadmap-next-execution/C-comparison.py`: executed generator.
- `artifacts/roadmap-next-execution/volume-comparison-inputs.npz`: actual phases and observations.
- `artifacts/roadmap-next-execution/volume-comparison-outputs.npz`: actual DC/complex harmonics, all five actual and rounded expected real coordinates, fitted observations and residual arrays.
- `artifacts/roadmap-next-execution/volume-comparison.json`: exact Decimal expectations/budgets, metrics, per-array dtype/shape/byte hashes, file hashes and environment.
- `artifacts/roadmap-next-execution/C-comparison-1.log`: successful execution output.

Both NPZ archives contain numeric arrays and were reopened with
`allow_pickle=False`. Their measured SHA256 identities are:

- Inputs: `d70143d5d7e5e901474aa5e70f2d56952d225673653bee2d8d3fe1295e1d092d`.
- Outputs: `de6f71f929bd365cc9e66b30a38ace1b7e51d5f93a123067270089729075601e`.
- JSON: `d8b6c0a074ae901b37d3e14eb7c54612d6d585611ecee6dd37e2ae7cdefbbd56`.

Execution used Python 3.13.12, NumPy 2.5.3 and SciPy 1.18.1 on macOS arm64.
All informative cases have independently bounded condition number below 10.
This supplies no uniform accuracy guarantee for weakly identified full-rank
phase sets, no physical noise guarantee and no 3D specimen reconstruction or
axial order-specific calibration claim. These are observed-volume phase
harmonics at the acquired sampling.
