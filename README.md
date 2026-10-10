# SIMrecon

**A Python library for structured illumination microscopy (SIM) reconstruction.**

SIMrecon is being built to turn microscope images acquired at different
illumination orientations and phases into a reconstructed 2D image or 3D volume.
It uses NumPy arrays and explicit acquisition parameters, with independently
written numerical code and documented, testable interfaces.

The goal is one complete workflow:

```text
Raw specimen images + raw bead calibration images + acquisition metadata
    → instrument calibration
    → illumination and motion estimation
    → reconstruction
    → output with settings, diagnostics and provenance
```

**Status: the component library works; the complete raw-input workflow is still
under development.** The first component stack is merged. Today, reconstruction
examples require supplied calibration and known parameters. There is no single
command that takes an experimental acquisition through the entire diagram above.

## What you can use today

| Capability | Available now | Main limitation |
|---|---|---|
| Acquisition files | Inspect supported Priism-style MRC acquisitions, read selected blocks, resolve acquisition layout and convert to modern MRC while preserving pixels and metadata. | Layout and interpretation need explicit configuration. Conversion performs no reconstruction or modern-MRC input decoding. |
| Fiji viewing | Export a supported Priism acquisition as an OME-BigTIFF copy with every orientation/phase setting retained. OME means Open Microscopy Environment. | A viewing copy of the acquisition; reconstruction-array export is separate work. Keep the original for opaque metadata recovery. |
| Phase separation | Separate known-phase 2D images and five-order 3D volumes. | Phases must be supplied; this does not estimate an acquisition's unknown phases. |
| Optical calibration components | Prepare an optical transfer function (OTF) from a supplied 2D or 3D intensity point spread function (PSF); prepare volume order transfers from supplied axial profiles. | A prepared PSF/profile is required. Empirical calibration from raw phase-resolved SIM bead images remains unfinished. |
| Parameter and drift components | Fit 2D phase/modulation for known integer carriers, scan a finite caller-supplied carrier list, select a sole passing candidate, estimate periodic integer translation from comparable reference images, and correct known integer specimen drift. Fit relative complex volume-order gains for a known carrier. | These are narrow operations with explicit inputs and assumptions, rather than complete automatic 3D parameter or motion estimation. |
| Reconstruction | Reconstruct known-parameter 2D images and recombine five-order 3D data using full complex transfers. | Finite periodic models. 2D fractional shifts use approximate spectral interpolation; 3D placement currently requires integer lateral carriers and matching calibration grids. |

These components have executed examples and independent comparison reports.
Their contracts describe numerical accuracy and rejection rules. Component
agreement with a finite model does not establish accuracy on an experimental
specimen or parity with the legacy reconstruction program.
Some detailed guides retain historical stack status; use this README and the
[migration roadmap](docs/MIGRATION-ROADMAP.md) for current integration status.

## Get started

The project targets **Python 3.13**. Its reproducible development environment
uses **Python 3.13.12** and **uv 0.12.19**, with dependencies pinned by `uv.lock`.
With Git and uv installed:

```sh
git clone https://github.com/david-hoffman/simrecon.git
cd simrecon
uv sync --locked --all-groups
uv run --locked simrecon --help
```

The Python array interface is the entry point for numerical reconstruction.
The command-line interface currently provides file inspection, conversion and
Fiji export. The [environment guide](docs/operations/environment.md) covers
development setup and prerequisite checks.

### Try phase separation without a dataset

Save this as `example.py`, then run `uv run --locked python example.py`:

```python
import numpy as np
from simrecon import separate_phases

# Seven known illumination phases, in radians; one pixel per image.
phases = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
images = (10 + 4 * np.cos(phases) + 2 * np.sin(phases))[:, None, None]
components = separate_phases(images, phases_rad=phases)

print(np.round(components.dc, 6))  # [[10.]]
print(np.round(components.c1, 6))  # [[2.-1.j]]
```

Here `dc` is the constant component and `c1` is the complex first harmonic.
This small demonstration separates supplied phases; it is not a reconstructed
microscopy image. The [phase-separation guide](docs/usage/phase-separation.md)
explains the model and array conventions.

### Choose a next example

- **Use an existing acquisition:** read the
  [conversion contract and configuration examples](docs/contracts/mrc-conversion-v1.md),
  then the [Fiji export guide](docs/usage/imagej-export.md). Do not infer phase,
  orientation or Z ordering from a flattened stack.
- **Explore 2D reconstruction:** start with
  [PSF-to-OTF preparation](docs/usage/otf-calibration.md) and
  [known-parameter reconstruction](docs/usage/reconstruction.md).
- **Explore 3D reconstruction:** use the standalone
  [volume recombination example](docs/usage/volume-recombination.md), then
  [relative order-gain fitting](docs/usage/volume-order-gain.md).

Spatial array axes are `(y, x)` for images and `(z, y, x)` for volumes.
Acquisition arrays add phase and orientation axes as specified by each API.
The examples state sampling in micrometres (µm) and phases in radians.

## Roadmap: what remains before a complete workflow

**We have the numerical foundations, but substantial calibration, estimation
and integration work remains.** The merged components above are prerequisites,
not completion of the following phases. A completion percentage would be
misleading: the unresolved scientific decisions and experimental validation
have no measured effort estimate yet.

| Phase | Unfinished work | Completion evidence |
|---|---|---|
| **1 — Next** | Reconcile the merged baseline, identify the target acquisition and reference settings, and prepare concrete execution contracts. | Recorded input/settings requirements, decisions and dependency packets. |
| 2 | Define raw specimen and bead intake, axes, units, camera/background corrections and provenance. | Both acquisitions are interpreted consistently, with explicit correction ownership. |
| 3 | Calibrate effective 3D SIM order transfers from raw phase-resolved bead exposures. | Independently validated empirical calibration, rather than supplied PSFs or axial profiles. |
| 4 | Support independently sampled calibration grids and complex OTF interpolation. | Calibration can be consumed on the specimen's grid under a documented interpolation contract. |
| 5 | Complete specimen illumination-parameter estimation, drift handling and required corrections. | The selected acquisition mode no longer needs hidden true parameters supplied by the caller. |
| 6 | Complete reference-compatible 3D reconstruction, sampling, normalization and output representation. | Supported mode and output conventions have independent numerical evidence. |
| 7 | Compose one public workflow from both raw acquisitions, and demonstrate small complete cases. | Raw arrays enter the same calibration/estimation/reconstruction route, with diagnostics and provenance. |
| **8 — Penultimate** | Run an independent full 3D simulation, approximately **512 × 512 × 64 voxels (x/y/z)**, producing both raw specimen and raw bead acquisitions. | The public workflow processes both acquisitions without precomputed OTFs or hidden simulator truth; scientific error, runtime and peak memory are reported. |
| **9 — Final** | Run owner-supplied experimental acquisitions and compare with corresponding owner-provided legacy outputs. | Agreed cases satisfy an evidence-driven comparison contract under matching recorded settings. |

Phases 2–9 remain pending. Phase 1 starts after this roadmap amendment is complete.
Later dependent work waits for its completed prerequisites.
Comparison tolerances, intensity scaling, registration, optical defaults and
supported legacy modes will be resolved from evidence; this README sets none.

The [full migration roadmap](docs/MIGRATION-ROADMAP.md) gives dependencies,
deliverables and exit criteria. It distinguishes supplied-parameter components
from empirical calibration and a complete acquisition workflow. It also explains
why the full simulation precedes the final experimental comparison.

## Development and verification

From the repository root:

```sh
make preflight  # Locked setup, interpreter/import and build-tool health
make check      # Locked setup, lint, formatting and type checks
make verify     # Full tests, coverage reports, wheel/import checks and audit
```

The full check includes Fiji reader interoperability tests. They require a
Java Development Kit (JDK) **21.0.7** with source-file launching;
`SIMRECON_JAVA` can select the Java executable. Setup authenticates and caches
pinned ImageJ/Bio-Formats jars. See the
[reader environment guide](docs/operations/imagej-reader-environment.md).
The numerical library and Fiji export itself do not require Java.

Continuous integration repeats the full verification on Ubuntu 24.04 and
macOS 15. Native statement and branch coverage are measured for the library and
verification tools; percentages are advisory under the current project policy.
See the [verification guide](docs/operations/verification.md) for receipts,
reports and exact-candidate checks, and [AGENTS.md](AGENTS.md) for contributor
instructions.

## Project context

- [Project architecture and public boundaries](docs/PROJECT.md)
- [Scientific context and references](docs/SCIENTIFIC-CONTEXT.md)
- [Library design](docs/architecture/library-design.md) and
  [data flow](docs/architecture/data-flow.md)
- [Detailed migration roadmap](docs/MIGRATION-ROADMAP.md)

The Python implementation is written independently. Local legacy source under
`SIMrecon_svn/` is ignored study material and is not included in the package.
The roadmap permits source study and comparison with owner-provided outputs;
it prohibits building or running the reference programs or bundled executables.
