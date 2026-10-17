# Select a volume carrier with explicit caller policy

`select_volume_carrier` retains the complete `scan_volume_carriers` result and
selects a row only when exactly one passes all three caller limits. Supply
known actual fundamental phases in radians, one positive order, specimen spacing
z/y/x in micrometres (µm), and a compatible fixed empirical response/gauge.
The required `source` is an opaque label, not authenticated provenance.

Run this complete algebraic example in the managed repository environment:

```python
import numpy as np
from simrecon import EmpiricalVolumeResponse, select_volume_carrier

phases = np.array([0.0, 0.43, 1.31, 2.29, 3.4, 4.51, 5.72])
c, s = np.cos(phases), np.sin(phases)
h = np.column_stack((np.ones(7), c, s, c*c-s*s, (2*c)*s))
images = (h @ np.array([1.0, 6.0, -8.0, -4.0, -2.0]))[:, None, None, None]
response = EmpiricalVolumeResponse(
    np.ones((3, 1, 1, 1), dtype=complex),
    np.array([0.0]), np.array([0.0]), np.array([0.0]),
    (1.0, 1.0, 1.0), (0, 0, 0),
)
for order, bounds in [(1, (4.0, 6.0)), (2, (2.0, 3.0))]:
    result = select_volume_carrier(
        images, response=response, voxel_size_um=(1.0, 1.0, 1.0),
        phase_steps_rad=phases, candidate_carriers_yx=[(0, 0), (0, 1)],
        order=order, calibration_carrier_bins=(0, 0),
        coordinate_offset_yx=(0, 0), phase_reference_shift_rad=0.0,
        source="declared algebraic pairing", max_relative_residual=1e-10,
        min_overlap_count=1, gain_magnitude_bounds=bounds,
    )
    assert result.selected_index == 0 and result.failure_code is None
    assert result.candidates[1].status == "no_overlap"
    row = result.candidates[result.selected_index]
    print(order, result.eligible_indices, row.gain, row.relative_residual)
```

Here the analytic ideal gains are `3+4j` and `-2+1j`; their magnitudes are 5
and √5, dimensionless. Stored rounded observations receive the inherited
least-squares fit. This one-pair example proves policy usage, not physical
carrier recovery. The [measured comparison](../reports/volume-carrier-selection-comparison.md)
also checks asymmetric complex transfers and a misleading equal-fit landscape.

Every keyword is required. The residual limit accepts finite nonboolean
Python/NumPy integer or floating scalars converting to finite nonnegative
binary64. The overlap minimum is an exact positive integer with no size cap.
Gain bounds are an exact built-in tuple/list or plain one-dimensional length-two
array of permitted real scalars. Their converted values must satisfy
`0 <= lower <= upper`. Equal, zero and above-one bounds are valid. There is no
modulation interpretation or gain cap. Arrays, strings, Decimal, Fraction and
complex values are not scalar limits. See the [contract](../contracts/volume-carrier-selection-v1.md)
for the full representation and conversion rules.

A row passes exactly when its gain exists, its residual is at most the limit,
its full geometric overlap is at least the minimum, and its represented complex
gain magnitude lies inclusively between the bounds. The last comparison uses
exact squared represented components; overflowing squares, underflow and a
rounded square root do not alter the decision. No tolerance is added.

`zero_response` and `zero_correlation` have real zero-valued diagnostics and can
pass. `no_overlap`, `incomplete_coverage` and `zero_predictor` have absent gains
and cannot pass. All rows remain in caller order. Duplicates passing the policy
produce `ambiguous_volume_carrier`; none produce `no_acceptable_volume_carrier`.
These codes are result values. Invalid policy raises `SimreconError` with code
`invalid_volume_carrier_selection_policy` before scanning. All inherited global
failures abort the entire call unchanged, including after an earlier passing row.

The result has four frozen bindings: `candidates`, `eligible_indices`,
`selected_index`, `failure_code`. Use `candidates[selected_index]` after checking
the index. There is no ranking, deduplication, search-range inference or early
return. The scanner preserves input snapshots and floating/warning policy.

Residuals from different overlaps describe different data. Geometric overlap
includes zero-transfer pairs and measures no informative support. Sparse or
aliased data can fit several candidates equally well; sole acceptance says
nothing about candidates outside the list. Caller thresholds give no noise
calibration, confidence probability, physical uniqueness or robustness. Actual
phases and calibration/specimen compatibility are supplied, not inferred.
This slice adds no complete raw workflow, reconstruction or experimental parity.
