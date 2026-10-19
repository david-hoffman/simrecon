# Public dependency packet: raw references and 3D motion

**Version 1.0.** Sanitized decision/dependency material from the [report-only intake](../reports/raw-phase-motion-intake.md). This is not a blind A/B packet, approved numerical contract, test oracle or implementation authorization. No scientific child is ready until its material choices and expectations are settled. Future blind roles receive only their concrete approved contract, allowed interfaces and independently justified expectations, not discovery reports, source notes, coordinator state, coverage maps, history or lessons.

## Settled public boundaries

| Public dependency | Settled input/output meaning | Remaining premise |
|---|---|---|
| [Raw declaration](../contracts/raw-acquisition-declarations-v1.md) | Canonical arrays and explicit metadata; phases are nominal commands | Actual phase, timing, intensity and physical motion provenance |
| [Supplied linear-response correction](../contracts/linear-response-correction-v1.md) | Explicit `raw=offset+response*signal` relation and units | Unknown exposure/fading/background are not inferred |
| [Known-phase volume separation](../contracts/volume-phase-separation-v1.md) | Projection of common observed component arrays onto a supplied identifiable actual-phase matrix | Motion during the cycle can invalidate common components |
| [Unknown-phase estimation](../contracts/phase-step-estimation-v1.md) | Fixed supplied carrier/transfers/gains and declared stationary finite periodic objective | Does not jointly infer motion, calibration or exposure scale |
| [Volume order transfers](../contracts/volume-order-transfers-v1.md) | Supplied axial displacement profiles in fixed effective kernels | Profiles must follow the declared scan frame; empirical zero order need not equal detection-only response |
| [Comparable-volume displacement](../contracts/volume-translation-estimation-v1.md) | Complete integer periodic score surface, common scaling and caller ambiguity tolerance | References must already be comparable and equal intensity; result names no mechanism |
| [Known 2D specimen correction](../contracts/integer-drift-correction-v1.md) | Negative alignment and positive carrier-projected phase correction for its fixed model | Does not select a 3D camera/focus/specimen model |

## Open decision before a motion child

Choose which physical mechanism the first 3D case must represent: specimen relative to fixed illumination/detection, post-formation image translation, or focal-plane/scan motion. Actual acquisition evidence may settle this; no inspected source default does. The coordinator has asked this smallest material question. No answer is inferred from silence. The report and its verification can close while the decision remains open; dependent numerical work cannot.

For the selected case, a later intake must specify:

- Coordinates, signs, voxel/µm units, rigid versus changing motion, and whether one displacement applies per exposure, cycle, orientation, scan or time point.
- Every affected argument of detection and axial illumination, actual versus commanded phase, calibration reuse and the permissible observation/reference boundary.
- Exposure/dose/background/camera relation, boundary model, representation and interpolation meaning. No unapproved normalization or crop/mask is implicit.
- Gauge choices, aliases, repeated-pattern/zero-information cases and explicit ambiguity outcomes. A unique numerical score is not a physical confidence statement.
- Independent expected results, legitimate positive alternatives, truth hidden from the estimator and a meaningful observable obligation inventory before tests.

One conditional route worth assessing is zero-order references from complete cycles with a common state within each cycle and justified actual phase cancellation, then between-cycle displacement. It gives no per-exposure motion and makes no motion-mechanism selection. If actual phases/calibration are unknown, their acquisition or contracted inference is an explicit prerequisite, not evaluator truth passed to the program.

## Dependency and gate map

```text
actual raw-layout/intensity/phase facts + selected motion mechanism
        -> concrete common-state/reference contract
        -> fresh native blind A / fresh blind B
        -> restricted C / fresh native D
        -> exact full local verification + separate required platforms
        -> own stacked delivery

continuous-carrier representation / joint-gauge questions
        -> separate report-only intake or settled numerical contracts

complete phases 2–6 -> phase7 raw workflow without supplied estimates
                  -> phase8 independent realistic hidden-truth simulation
                  -> phase9 owner-data/reference parity
```

The report adds no public API, test, fixture, runtime, gate or policy. Numerical children inherit the existing exact-candidate full-local and separately qualified Ubuntu 24.04/macOS 15 gates, task-selected 100% native executable-line/branch-destination coverage globally/per-package/per-owned-file, zero exclusions/skips, and fresh required roles. They may not execute/build reference C or copy/import/link/ship ignored source. No merge/release or older-PR edit is authorized. Full-size simulation and owner parity remain dependent exits. Human numeric limits are not set; missing resource/metering facts are unknown.

If motion remains unresolved after this report, an independent useful successor is report-only continuous-carrier representation/objective intake. It may compare finite sampled modulation, declared boundaries and Fourier interpolation, without selecting behavior, implementing an estimator or presuming a motion answer. That report must first check whether new owner input changes the dependency-ready choice. Exactly one successor follows verified delivery; this packet launches none.
