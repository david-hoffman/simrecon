# Reconstruct an image with compact diagnostics

`reconstruct_summary` accepts the same explicit specimen, acquisition, optics,
carrier, filtering and calibration inputs as
[`reconstruct_workflow`](c-workflow.md). It returns the signed image and physical
coordinates, fitted carriers and modulation, settings, provenance and compact
diagnostics. The [RM84 contract](../contracts/reconstruction-memory-v1.md) defines
the exact boundary; the [task record](../tasks/reconstruction-memory.md) locates
verification and measured resource evidence. Documentation is not acceptance
evidence.

Use the declarations from your existing workflow call. For example, assuming
`specimen_counts` and `settings` are valid inputs as described in the workflow
guide:

```python
from simrecon import reconstruct_summary

summary = reconstruct_summary(specimen_counts, **settings)
image = summary.image
x_um, y_um, z_um = summary.x_um, summary.y_um, summary.z_um
carriers = summary.carriers_cyc_um
modulation = summary.modulation
raw_modulation = summary.raw_modulation
```

The image axes are `(time, z, y, x)`. Coordinates use micrometres and fundamental
carriers use cycles per micrometre. The image keeps signed values and the declared
count-unit label. No positivity correction, gain fit, mass calibration, physical
recovery or resolution claim is added. The arrays are independent read-only
results; changing an input after return does not change the result.

## Choosing the result

| Need | Entry point |
| --- | --- |
| Image, coordinates, fitted parameters and compact scientific decisions | `reconstruct_summary` |
| Complete preparation, overlap, correlation, filtered-band and per-time image records for debugging | `reconstruct_workflow` |

The existing workflow and direct stage APIs retain their signatures, defaults,
record schemas and ownership guarantees. No `diagnostics=` selector is added.
To inspect full debugging data, explicitly run the existing workflow with the
same inputs. Doing so computes another result and can require substantially more
memory; a summary does not contain a hidden full result that can be expanded.
Keeping both results live also retains both images.

## Reading compact diagnostics

Top-level parameter arrays contain the actual fitted, supplied or reused carriers
and raw/final modulation. `branches` distinguishes the parameter-estimation route;
`effective_wiener` contains the actual per-time filtering schedule. Initial
carrier guesses and phase-linkage carrier guesses remain separate fields.

`diagnostics` is `"summary"`, and `omitted_diagnostics` names the excluded capture
categories. There are no `bands`, `parameters` or `reconstructions` stage records
on a summary. Preparation, estimation, filtering, transfer, calibration and layout
metadata are immutable ordered `(name, value)` tuples. Convert one level with
`dict` for convenient access:

```python
transfer_fields = dict(summary.transfer)
samples_identity = transfer_fields["samples"]
print(samples_identity.shape, samples_identity.dtype, samples_identity.sha256)
```

An ArrayIdentity records a field path, shape, normalized dtype and SHA-256 hash of
contiguous little-endian array bytes. It identifies values without retaining the
numeric array. The same convention applies to array-valued settings and projected
stage metadata, including camera maps. It is not an array, a data archive or proof
that an external file matches a source declaration. Preserve source inputs for
reproduction; use the full workflow when numeric intermediate arrays are needed.

`overlap_builds` keeps every build descriptor in order. A search event's
`overlap_index` refers to that tuple, including repeated equal-valued builds.
`search_trace` retains scalar search evaluations, bracket/parabola decisions,
neighbor samples and modulation adjustments. It omits full correlation images.
`preparation_trace` retains phase, drift-fit and off-exposure decisions while
omitting spatial snapshots. `filtering_trace` retains filtering decisions and
counts consecutive precise-query events; it does not retain every query record.
The workflow `trace` describes the completed logical stages.

## Memory and failures

Summary execution avoids retaining full diagnostic histories during the call.
It still needs numerical workspaces, the output image, caller-owned inputs and
metadata. Search traces grow with actual decisions; caller metadata can also be
large. There is no fixed memory ceiling, latency guarantee, disk-backed mode or
automatic output writer. Published measurements apply only to their identified
workloads, host, versions and thread settings.

Omitting a capture does not omit its required numerical or finite checks. Invalid
inputs, unsafe representations/stencils, singular fits and nonfinite operations
retain their existing errors. An error at a later time point yields no partial
result. Allocation failure and interruption propagate. The arithmetic remains
float64/complex128, with the existing scientific order and full-debug behavior.

The motivating input `(1,3,5,32,2048,2048)` with lateral zoom 2 and axial zoom 1
is outside the unchanged source representation domain: its output workspace
expression equals `2**32` bytes, greater than the unsigned-32 maximum. Saving
diagnostic memory does not make that shape supported. Smaller-volume measurements
must not be extrapolated into a promise that this case runs on a 16 GiB machine.
