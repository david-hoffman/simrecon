# Public dependencies: raw calibration labels and information

**Version 1.0.** This is decision material for the [raw calibration intake](../tasks/raw-calibration-intake.md), not an approved numerical contract, blind packet or test oracle. Its [nonblind report](../reports/raw-calibration-identifiability.md) contains conditional derivations and source investigation. Do not pass that discovery report, source notes, history, Current state, coverage maps or lessons to blind A/B.

## Preserved boundaries

| Public operation | Required information today | Missing full-workflow dependency |
|---|---|---|
| [Known-phase volume separation](../contracts/volume-phase-separation-v1.md) | Actual exposure phases | Nominal commands cannot silently become measured actual labels |
| [Raw point-bead calibration](../contracts/raw-point-bead-calibration-v1.md) | Camera declarations, actual phases, spacing, group | No automatic calibration phase inference; point-model limitations remain |
| [Raw finite-bead calibration](../contracts/finite-bead-compensation-v1.md) | The above plus known native profile, integer carrier and explicit conditioning minimum | No unknown profile/carrier recovery or continuous bead model |
| [Empirical response consumption](../contracts/empirical-transfer-consumption-v1.md) | Carrier, coordinate offset and calibration/specimen phase-reference relation | Gauge selection does not measure missing reference differences |
| [Fixed-transfer phase inference](../contracts/phase-step-estimation-v1.md) | Already fixed signed complex transfer/gauge, carrier, initial commands and controls | Cannot provide an independent raw calibration by assuming the output it needs |

The next numerical contract must state the independent information source: measured calibration phase/carrier metadata with uncertainty/reference semantics, or one concrete informative shared optical/probe acquisition model. More data need shared constraints. A known finite profile alone supplies no general carrier identity with unrestricted order responses. Five unrestricted coefficient images and harmonic-constrained shared spatial responses must not be conflated. These are questions to resolve under a specific approved model, not default rejection rules.

## Minimum contract decisions

1. Name the raw bead/specimen observation model, axes, units, sampling, boundaries, signed frequency/Nyquist meaning and relevant timing/stationarity conditions. The earlier [observation](continuous-carrier-public-dependencies.md) and [motion](raw-phase-motion-public-dependencies.md) questions remain separate and pending.
2. Inventory what is measured, supplied independently, fitted and a chosen gauge. Name the phase/carrier information source, finite profile representation, camera correction, transfer structure, shared acquisitions and calibration reuse. Include uncertainty and absent/inconsistent information outcomes before tests.
3. Define the estimator/objective only after that information is fixed: nuisance freedoms, parameter domain/aliases, initialization, unavailable/ambiguous outcomes, numerical conditioning/failure and independent accuracy assessment. Do not hide a new assumption in a threshold or a caller label.
4. Keep hidden evaluator truth out of initialization, candidate domains, masks/support/interpolation, references, solver choices and tolerances. Model any measured acquisition channel as an observation; an exact simulator value is not a measurement merely because it is in metadata.
5. Derive independent expectations and permitted positive alternatives for the selected contract. Use a concrete public packet, fresh native blind A/fresh B, restricted C/fresh D and exact gates before numerical publication.

A conditional composition of existing stationary periodic integer-carrier primitives may be proposed when actual calibration labels/profile and reuse facts are independently supplied. It does not automatically satisfy the full raw-workflow exit, unknown-nuisance simulation or physical motion requirement. No new API, numerical model, profile, estimator, tolerance, test, fixture, dependency, gate or policy is selected here.

```text
independent label observations OR informative shared structure
 + observation/calibration/parameter contract
 -> independent numerical expectations and fresh A/B/C/D
 -> exact full-local and independent required-platform gates
 -> raw composition -> full truth-hidden simulation -> owner-reference parity
```

Numerical children inherit full-local exact-candidate 13-phase `make verify`, separately qualified Ubuntu24.04/macOS15 proof and task-selected100% native executable-line/branch-destination coverage globally/per-package/per-owned-file, including never-imported owned files/relevant subprocesses, zero exclusions/skips and no platform union. Coverage establishes no complete behavior. Human numeric limits are not set; unavailable measurements stay unknown. When the material information source/model remains missing, report that blocker rather than launch another generic intake loop.
