# Known-phase raw point-bead calibration

`calibrate_raw_point_bead` composes full-array declared linear correction,
explicit group selection, actual known-phase volume separation and empirical
response preparation. Each stage runs once. The [contract](../contracts/raw-point-bead-calibration-v1.md)
defines the boundary; the [selected synthetic model](../models/synthetic-3d-acquisition-v1.md)
defines the point-bead interpretation.

Supply a `RawAcquisition` declared as `sim_beads` with explicit orientation,
phase, z, y and x axes. An explicit singleton z is valid. Every other argument
is required and keyword-only. `group` must be a plain dict naming exactly the
present time/channel/orientation axes. Each index must be a plain nonboolean
Python int in range, including zero for a present singleton. Optional axes
retain their meaning; no group is selected or averaged automatically.

This runnable example uses seven unequal actual phases, two orientations,
two times and two channels on a `(2,3,4)` z/y/x grid. Its asymmetric,
nonseparable detection kernel and squared complex field follow the selected
finite periodic model. Kernel, emitter position, brightness and illumination
parameters are generation truth only. Calibration receives the declared raw
array, correction, explicit selector, actual phases and spacing.

```python
import numpy as np
from simrecon import calibrate_raw_point_bead, declare_acquisition

actual = np.array([0.13, 0.82, 1.91, 2.76, 3.64, 4.73, 5.81])  # radians
spacing = (0.31, 0.17, 0.09)  # dz, dy, dx in micrometres
axes = ("time", "channel", "orientation", "phase", "z", "y", "x")
group = {"time": 1, "channel": 1, "orientation": 1}
shape = (2, 3, 4)
z, y, x = np.indices(shape)
h = (1 + (11*z + 7*y + 3*x + 5*y*x) % 13).astype(float)
h[0, 0, 0] = 61
h /= h.sum()
a0, plus, minus = 1 + 0.2j, 0.47 - 0.31j, -0.26 + 0.39j
power = abs(a0)**2 + abs(plus)**2 + abs(minus)**2

def make_signals(bead=(1, 2, 3)):
    shifted_h = np.roll(h, bead, axis=(0, 1, 2))
    axial = 2*np.pi*(z - bead[0])/shape[0]
    data = np.empty((2, 2, 2, len(actual), *shape))
    for time in range(2):
        for channel in range(2):
            brightness = 128 + 16*time + 8*channel  # zero-order electron mass
            for orientation in range(2):
                lateral = 2*np.pi*((orientation + 1)*bead[1]/shape[1]
                                   + bead[2]/shape[2])
                for phase_index, phase in enumerate(actual):
                    theta = lateral + phase
                    field = (a0*np.exp(1j*axial) + plus*np.exp(1j*theta)
                             + minus*np.exp(-1j*theta))
                    data[time, channel, orientation, phase_index] = (
                        brightness*shifted_h*np.abs(field)**2/power
                    )
    return data

signals = make_signals()  # expected electrons; noiseless synthetic exposures
index = np.arange(signals.size).reshape(signals.shape)
offset_map = (7 + (index % 11)/8).astype(">f8")  # counts, canonical shape
response_map = (1.5 + (index % 7)/4).astype(">f8")  # counts/electron
commands = np.broadcast_to(
    actual + np.array([0.00, 0.03, -0.02, 0.05, -0.04, 0.08, -0.06]),
    signals.shape[:4],
).copy()  # nominal command metadata, independently different from actual
config = {
    "version": 1, "acquisition_kind": "sim_beads", "axes": list(axes),
    "intensity_unit": "count", "nominal_phases_rad": commands.tolist(),
    "sampling_um": {"z": 9, "y": 8, "x": 7},  # distinct declaration retained
    "acquisition_id": "synthetic-point-bead", "calibration_id": "example-only",
}
results = {}
acquisitions = {}
for name, offset, response in (
    ("scalar", 10, 2),
    ("maps", offset_map, response_map),
):
    raw = offset + response*signals  # counts
    acquisition = declare_acquisition(
        raw, config=config, original_metadata={"purpose": "synthetic example"}
    )
    acquisitions[name] = acquisition
    results[name] = calibrate_raw_point_bead(
        acquisition, group=group, offset=offset, response=response,
        output_unit="electron", phases_rad=actual, voxel_size_um=spacing,
    )
    result = results[name]
    print(name, result.components.dc.shape, result.response.values.shape,
          result.response.origin_zyx)
```

Both calls print component shape `(2,3,4)`, response shape `(3,2,3,4)`
and observed origin `(1,2,3)`. Correction uses sequential binary64 subtraction
then division: `(raw-offset)/response`. Raw and offset are in counts;
response is in counts/electron; separated components are in electrons.
These labels and coefficients are caller declarations, not estimated camera
calibration. Scalar and map forward generation can round differently, so
the stored corrected exposures define each fit.

Full correction maps match `acquisition.data.shape` in canonical named-axis
order. They cannot be selected-group maps or maps in a different source layout.
Correction validates every supplied sample and map value, including nonselected
groups. Any invalid value or arithmetic range failure rejects the whole call.
To correct only one group, first declare an acquisition containing that group,
retaining required singleton group axes and selecting them explicitly.

`phases_rad` is a plain real numeric ndarray `(N,)` of actual known fundamental
phases, in exposure order, with at least five exposures and the separator's
rank requirement. Nominal commands remain metadata and are never substituted.
`voxel_size_um` is the explicit authoritative `(dz,dy,dx)` calibration sampling,
even when the acquisition sampling differs as above or is unknown. Tuple, list
and supported plain one-dimensional ndarray forms are accepted. Both supplied
and applied declarations are retained; no physical consistency is inferred.

`result.components` contains the observed `dc`, `c1` and `c2`, where the phase
model is `dc + 2*Re(c1*exp(i*phi) + c2*exp(2*i*phi))`. For the represented
five-column fit, `dc` need not equal the exposure mean. The operation then finds
the sole positive observed dc maximum and uses it as a common grid origin.
Every response order uses the same exact converted-dc mass `S`:

```text
E_m[k] = sum_n (c_m[n]/S) * exp(-2*pi*i*sum_a k_a*(n_a-origin_a)/N_a)
S = exact sum of converted dc samples; c_0 = dc; m = 0,1,2
```

`result.response.values` stores full signed complex orders `0,+1,+2` and all
centered Cartesian z/y/x bins. Frequency axes are in cycles/micrometre;
`k/(N*d)` uses converted supplied spacing. Even axes retain the negative
Nyquist bin. Zero-order DC is exactly `1+0j`; other zero-order bins retain the
observed shape. No per-order normalization, magnitude projection, conjugation,
support cleaning or additional bead division occurs. Point-bead size
compensation is identity. Negative orders, if needed by another consumer,
follow `E_-m(k)=conj(E_m(-k))` with modular negation on every spatial axis.

The retained gauge is `observed_dc_peak_with_supplied_phase_origin`. Jointly
rolling every exposure volume shifts the observed origin but preserves its
centered response. Physically moving the model bead laterally also changes its
illumination phase, rephasing order `m` by `exp(i*m*delta_theta)`. Changing
supplied actual phases to `phi+alpha` for unchanged observations rephases
orders by `exp(-i*m*alpha)`, up to the inherited represented-phase numerical
budgets. Neither bead nor phase gauge is silently removed.

`result.provenance` retains exactly model, group, complete source metadata,
linear-response declarations, supplied/applied actual phases, supplied/applied
spacing, bead compensation and response gauge. The source snapshot includes
original config, metadata, overrides, nominal commands, declared sampling,
units and IDs, but no raw pixel archive. Origin is in
`result.response.origin_zyx`. Records have frozen bindings, independently owned
mutable arrays and independent caller snapshots. Metadata is read-only by
convention; there is no deep-immutability or direct-construction validation
promise. The library performs no file I/O, hashing or persistence.

The executed local comparison retains complete stored raw/corrected/model
reference/independent expected/output arrays and provenance in ignored
`artifacts/raw-point-bead-calibration-20261011/C02/`. Its `example.py` executes
this exact code block and compares all fitted coordinates and signed bins to
the reviewed independent 110-digit stored-input least-squares/direct-sum
observer. It also checks scalar/map variants and all three gauge relations.
`example-summary.json`, `example-inputs.json`, per-case arrays and
`artifact-hashes.json` preserve numerical budgets, identities and limitations.
Those are local caller-side evidence, not installed package resources or a
runtime persistence API.

The sole grid peak does not certify bead isolation or a physical emitter
center. A positive peak still needs positive exact dc mass for normalization;
signed samples are allowed. Common normalization discards brightness scale
and identifies no absolute detection throughput. This noiseless model is
finite, periodic, sampled and on-grid, with a phenomenological kernel. It
does not establish measured instrument settings, continuous optical accuracy,
finite-bead compensation, unknown phases, drift/noise correction or real-data
parity. Empirical responses retain their observation gauge and are not
automatically interchangeable with supplied-profile optical transfer functions
(OTFs), nor do they guarantee reconstruction. No streaming, whole-volume
memory bound or performance guarantee is selected. The inherited public
errors and numerical budgets remain binding; focused examples do not replace
the full verification gate and independent review.
