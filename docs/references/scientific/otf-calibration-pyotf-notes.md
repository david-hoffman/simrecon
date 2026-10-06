# Pyotf focal-plane calibration illustration

**Version 1.0.** Observed October 6, 2026. Pyotf is the owner's selected optical simulator. This illustration is separate from the independent mathematical [fixture oracle](otf-calibration-fixture-notes.md).

## Source and explicit recipe

The read-only upstream checkout matches commit [`d641ff6cde1fac6e77ff2d47629d981831a75912`](https://api.github.com/repos/david-hoffman/pyotf/commits/d641ff6cde1fac6e77ff2d47629d981831a75912), tree `e90f55cf46b355250a66586aa6ed3a033df4a01f`. Export that tracked revision without its untracked files. Its source identity is distinct from release `v0.0.3`; a release-only package pin would not identify this example. Exact source/archive and resolved environment identities are in the [manifest](otf-calibration-intake-manifest.json).

Use the upstream `HanserPSF` and its intensity `PSFi`, not the coherent field `PSFa`. Explicit source parameters determine this **illustrative** microscope:

```python
import numpy as np
from pyotf.otf import HanserPSF

model = HanserPSF(
    wl=520.0, na=1.2, ni=1.33, res=40.0, size=257,
    zres=40.0, zsize=1, zrange=[0.0],
    vec_corr="total", condition="sine",
)
focal = np.asarray(model.PSFi[0], dtype=np.float64)
kernel = focal / focal.sum(dtype=np.float64)
origin_yx = (128, 128)
pixel_size_um = (0.04, 0.04)
illustrative_otf = np.fft.fftshift(
    np.fft.fft2(np.roll(kernel, (-128, -128), axis=(0, 1)))
)
frequency_per_um = np.fft.fftshift(np.fft.fftfreq(257, d=0.04))
```

The upstream [model source](https://raw.githubusercontent.com/david-hoffman/pyotf/d641ff6cde1fac6e77ff2d47629d981831a75912/pyotf/otf.py) specifies `(z,y,x)` intensity data, length parameters in the wavelength's units, available vector corrections and pupil conditions. Here lengths are nanometres; numerical aperture (`na`) and refractive index (`ni`) are dimensionless. The explicit vector/pupil choices belong to this fixture, not project-wide defaults. A source-derived interpretation is that these are intensity samples rather than detector-area integrals; no detector-integration model is selected.

An explicit focal plane is necessary. With this revision, the default one-plane z range lies at `-zres`; `zrange=[0.0]` requests actual focus. Its stack plotting helpers reject one-/two-plane z grids, so the preview uses ordinary image plotting. The odd lateral grid places the declared origin at `(128,128)`. Physical sample centers span `±128*0.04=±5.12 µm`; full image edges span ±5.14 µm. A nanometre-to-micrometre conversion changes coordinates, not the array or normalization.

The source's unnormalized intensity sum is converted to unit discrete mass. This is a finite sampled PSF, not density in µm^-2, a measured optical throughput, an experimental bead calibration or an exact continuous optical response. Sine-condition apodization and vector correction are explicit; a uniform-pupil Airy function is not the exact oracle for this recipe.

## Observed environment and limits

The isolated intake environment actually imported Pyotf and generated this `(257,257)` focal PSF under Python 3.13.12, NumPy 2.5.3 and SciPy 1.18.1. Matplotlib 3.11.2 and dphtools 0.0.5 are among the resolved dependencies recorded completely in the manifest. This is one measured recipe on this workstation, not upstream Python-3.13 qualification or a dependency lock proposal for SIMrecon. No SIMrecon product dependency/lock was changed.

The source was exported with `git archive` from its exact tracked Git revision; local untracked files were excluded. Upstream `.gitattributes` sets `export-subst` on `pyotf/_version.py`, so archive creation expands its refnames/commit/date keywords. The manifest distinguishes `tracked_source_blob_sha256` from `archived_source_files_sha256` and names that sole transformation. Eight source files match their blobs; the expanded version file matches its archive member. This archived module reports version `0+unknown`; exact commit/tree/archive/generated-byte identities, rather than that version string, identify the simulator used. Local generator and full arrays remain temporary/ignored with their SHA-256 identities recorded. Reproducing a byte-identical image/archive can require the exact plotting/transform environment; numerical acceptance is defined by equations rather than PNG resemblance.

Inspect the manifest for observed PSF bounds, normalized sum, complex DC, maximum transfer magnitude, imaginary roundoff and artifact digests. Tiny imaginary residuals of the symmetric numerical illustration do not change the general complex-valued calibration contract. This example performs no SIMrecon public-API recovery and no numerical acceptance claim.

Physical convergence under larger pupil grids, larger fields of view, finer sampling, detector integration and real acquisition parameters remains unmeasured. The finite kernel's transfer is displayed without ideal-cutoff masking or thresholding. These limitations must remain visible if the example is reused for later reconstruction.
