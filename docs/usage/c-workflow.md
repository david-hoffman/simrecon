# Public C reconstruction workflow

This guide describes the CE07 candidate boundary in the
[public contract](../contracts/c-equivalence-workflow-v1.md). The
[task pointer](../tasks/c-equivalence-workflow.md) identifies acceptance evidence.
Documentation alone is not a runtime acceptance verdict.

`reconstruct_workflow` composes the accepted acquisition preparation, finite
carrier/modulation estimator, and native filter/assembly operations. Select one
calibration source: raw bead observations, a prepared empirical transfer, an
accepted complete transfer, or explicitly decoded historical transfer sections.
The returned image keeps its signed intensity. The result also contains the
actual intermediate records, coordinates in micrometres, settings, identities,
and diagnostics.

The example below assumes `specimen_counts` is a valid real array with axes
`(time, direction, phase, z, y, x)` and `accepted_transfer` is a valid
`OpticalTransfer` covering its actual operations. Obtain the settings from the
declared acquisition and calibration. The numbers illustrate the units and
configuration schema; they do not establish that a particular experiment has
enough overlap for estimation or reconstruction.

```python
from simrecon import reconstruct_workflow

optics = {
    "wavelength_nm": 525,
    "numerical_aperture": 1.2,
    "immersion_index": 1.33,
}

result = reconstruct_workflow(
    specimen_counts,
    acquisition={
        "acquisition_mode": "3d",
        "dxy_um": 0.1,
        "dz_um": 0.2,
        "norders": 3,
        "background": 100.0,
        "lateral_zoom": 2.0,
        "axial_zoom": 1,
        "phase_policy": "uniform",
    },
    optics=optics,
    carrier={"linespacing_um": 0.2},
    filtering={"wiener": 0.01},
    specimen_identity={"id": "specimen-01", "intensity_unit": "detector-counts"},
    transfer=accepted_transfer,
    transfer_identity={
        "id": "selected-transfer-01",
        "intensity_unit": "dimensionless-transfer",
        "optics": optics,
    },
)

image = result.image
x_um, y_um, z_um = result.x_um, result.y_um, result.z_um
```

For raw empirical calibration, supply `calibration` with the required `raw`,
`settings`, and `identity` mappings and omit `transfer` and `transfer_identity`.
`raw` has axes `(phase, z, y, x)` for the explicitly selected calibration.
Its settings supply its own pitches and line spacing plus the declared matching
optics. The six required settings keys are `dxy_um`, `dz_um`, `linespacing_um`,
`wavelength_nm`, `numerical_aperture`, and `immersion_index`, all directly inside
`settings`. The workflow prepares the transfer once and consumes that computed
complex128 value directly. Pass a precomputed `PreparedOtf` as
`transfer=prepared_otf` with `transfer_identity` and no `calibration`; it is used
without recomputing or quantizing it. Complete transfer records never acquire silently
duplicated orders. The decoded historical-section adapter has a separate,
explicit order-selection rule.

An actual `RawAcquisition` can replace the ndarray specimen. Its named axes
control the layout adapter. A present channel axis requires `channel_index`,
including a one-channel axis. A known unit or sampling declaration must agree
with the explicit workflow configuration. Generic wavelengths, nominal phase
commands, acquisition IDs, and calibration IDs remain recorded metadata; they
do not choose scientific settings or calibration automatically.

Declare true two-dimensional acquisition with `acquisition_mode="2d"`.
A length-one transfer axis alone does not establish that mode. The explicit
`plane_policy="literal-2d-stack"` alternative preserves the historical section-stream
regrouping of a declared stack; it is not an automatic transpose into nominal
planes. See the contract's exact storage-order and metadata rules before using it.

The initial carrier is resolved from line spacing, phase count and the declared
dimensional mode. Set `carrier["search_carriers"] = False` to use that nominal
carrier while retaining the source's modulation fits.
Time-zero carrier reuse also fits each later time's modulation. A Wiener increment
applies before the first effective time as well as subsequent times. The returned
initial carriers, effective Wiener sequence, parameter branches and reconstruction
records expose those choices.

The example uses the defaults: carrier search and time-zero reuse enabled,
equalization enabled, and `edge_pixels=10`. The default edge operation needs
X and Y at least 10 pixels. Set acquisition options explicitly when those choices
do not describe the declared experiment.

`phase_policy` asserts the actual separation route: `uniform`, `supplied`,
`steps`, or `drift`. A supplied list uses `acquisition["phases_rad"]`; steps use
`acquisition["phase_steps_rad"]` and take precedence over a simultaneous list.
Within-exposure drift with phase adjustment selects `drift`. An assertion that
disagrees with the selected route rejects; nominal metadata is not substituted.

When supplying `header_timestamps`, also supply `header_timestamp_unit`, such as
`"seconds"` or `"acquisition-clock-ticks"`. The workflow retains the label and
passes the numeric clocks unchanged; it infers and converts no clock unit.
Without timestamp data the unit must be `None`. Missing or invalid unit metadata
rejects. Fitted drift coefficients use detector pixels divided by the declared
clock unit raised to the corresponding polynomial power.

The image uses the source's camera correction, equalization, transform,
separation and reconstruction scale. Its count-unit label is traceable to the
input; it is not a specimen-mass calibration or a guarantee that image sums equal
raw counts. Smaller output pixels establish no resolution improvement. True2D
with extra axial zoom retains the accepted plane-zero behavior and reports its
limits explicitly.

Missing required metadata, incompatible declarations, unsupported reference
branches, or an unresolved numerical operation raise `WorkflowError` with a
category, stage and known time/direction context. The original cause is retained
where required. A failed call returns no partial reconstruction or fallback.
See the contract for exact domains and ordinary argument/allocation exceptions.

Neutral file operations can explicitly read and declare specimen pixels before
this call. They preserve pixel meaning and do not infer C metadata. The existing
ImageJ exporter accepts its documented file-source inputs; this workflow adds
no result writer, complex-transfer decoder, reconstruction CLI, or historical
IVE-library qualification. Mathematical source agreement, historical executable
agreement, physical recovery, and resolution remain separate qualifications.
