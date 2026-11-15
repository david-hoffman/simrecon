# Issue 115 approved interface excerpt

**Version 1.0.** Public signatures and value fields only. Read with
[wide-allocation-domain-v1](../contracts/wide-allocation-domain-v1.md).
No implementation text or behavioral observations are part of this excerpt.

Public imports are from `simrecon`. Arrays use `(T,D,P,Z,Y,X)` for raw input,
`(T,D,Q,Z,Y,X//2+1)` for quadratures and `(T,Zo,Yo,Xo)` for images.
Physical pitches/coordinates are micrometres, carriers cycles per micrometre,
phases radians. Inherited contracts supply complete schemas/default semantics.

```python
prepare_bands(images, *, dxy_um, dz_um, norders, background, lateral_zoom,
              axial_zoom, flatfield_slope=None, exposure_background=None,
              phases_rad=None, edge_pixels=10, equalize=True,
              equalize_z=False, equalize_time=False) -> PreparedBands

prepare_acquisition_bands(images, *, acquisition_mode, dxy_um, dz_um,
    norders, background, lateral_zoom, axial_zoom, flatfield_slope=None,
    exposure_background=None, phases_rad=None, phase_steps_rad=None,
    edge_pixels=10, equalize=True, equalize_z=False, equalize_time=False,
    off_exposures=None, combine_off_orders=None, storage_order="direction-major",
    drift_between=False, drift_within=False, fit_drift=False, adjust_phases=False,
    drift_filter_fraction=0.0, wavelength_nm=None, numerical_aperture=None,
    immersion_index=None, header_timestamps=None, header_phases_rad=None,
    linespacing_um=None, phase_start_angle_rad=1.57193,
    negative_angle_step=False) -> AcquisitionBands

reconstruct_known(bands, transfer, *, carriers_cyc_um, modulation,
    wavelength_nm, numerical_aperture, immersion_index, wiener,
    suppress_singularities=True, suppression_radius_bins=10.0,
    dampen_order0=False, omit_order0=False, omit_kz0=False,
    output_taper="cosine", wiener_increment=0.0, power_taper_exponent=None,
    precise_taper=False, filter_overlaps=True, explode_factor=1.0
) -> KnownReconstruction

reconstruct_workflow(specimen, *, acquisition, optics, carrier, filtering,
    specimen_identity, transfer=None, calibration=None, transfer_identity=None,
    off_exposures=None, exposure_background=None, header_timestamps=None,
    header_timestamp_unit=None, header_phases_rad=None, channel_index=None,
    plane_policy="native") -> WorkflowReconstruction

reconstruct_summary(specimen, *, acquisition, optics, carrier, filtering,
    specimen_identity, transfer=None, calibration=None, transfer_identity=None,
    off_exposures=None, exposure_background=None, header_timestamps=None,
    header_timestamp_unit=None, header_phases_rad=None, channel_index=None,
    plane_policy="native") -> ReconstructionSummary
```

Relevant accepted value fields (not permission to forge inconsistent records):

* `PreparedBands`: `quadratures`, `noise_variance_factors`, `input_shape`,
  `input_scale`, `dxy_um`, `dz_um`, `lateral_zoom`, `axial_zoom`,
  `source_revision`, `reference_sha256`; preparation diagnostics remain governed
  by CE02. Noise shape is `(D,O)`.
* `AcquisitionBands`: the same named geometry/identity fields, noise shape
  `(T,D,O)`, plus `acquisition_mode`, `storage_order`, `resolved_settings` and
  CE06 preparation/drift diagnostics.
* `KnownReconstruction`: `image`, `filtered_quadratures`, `x_um`, `y_um`,
  `z_um`, `carriers_cyc_um`, `modulation`, `radial_cutoff_cyc_um`,
  `axial_cutoffs_bins`, `resolved_settings`, `mode_trace`, `source_revision`,
  `reference_sha256`.
* `WorkflowReconstruction`: signed `image`, coordinates, intensity labels,
  `bands`, `parameters`, `transfer`, `calibration`, `layout`,
  `reconstructions`, carrier/linkage/Wiener arrays, identities, declarations,
  resolved settings and trace as CE07 specifies.
* `ReconstructionSummary`: signed `image`, coordinates, intensity labels,
  `carriers_cyc_um`, `modulation`, `raw_modulation`, initial/linkage/Wiener
  arrays, compact preparation/estimation/filtering/transfer/calibration/layout
  records and traces, `diagnostics="summary"`, omitted-diagnostic labels,
  identities, declarations, settings, limitations and source identity as RM84
  specifies. It retains no full numerical debug histories.

Direct errors are `ReconstructionError` and `AcquisitionModeError`; inherited
preparation errors are `SimreconError` with code `preparation-domain`.
`WorkflowError(code, message, *, stage, time_index=None, direction_index=None)`
exposes those fields. Applicable error semantics are in contract W09–W12/W17–W18.

## Approved integer-only production validation interfaces

These existing production metadata interfaces are authorized for focused tests
without reading their module sources. They are not newly supported top-level
scientific APIs or a permission to print internals. Their contract is the new
allocation-byte rule plus their stage's retained constraints:

```python
simrecon.acquisition.layout.extent(shape: tuple[int, ...], itemsize: int) -> None
simrecon.acquisition.layout.output_extents(
    shape: tuple[int, ...], lateral: float, axial: int
) -> None
simrecon.reconstruction.known_parameters._extent(
    shape: tuple[int, ...], itemsize: int
) -> None
```

`extent` checks nonnegative native dimensions and the conservative native
stride/byte rule, including empty axes. CE04 `_extent` checks positive native
dimensions; use it only for positive shapes. Item sizes are positive integer
storage widths. `output_extents` receives already validated positive six-axis
geometry and zoom declarations, checks output signed counts and wide output/
lookup/native storage validity, and creates no target array. These validators
must remain on real production call paths. Testing them supplies no proof of
public call ordering; tiny public calls must supply that complementary proof.
No new helper name or test-only interface is commissioned.
