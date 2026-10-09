# PR16 volume phase figures

Static figures for [SIMrecon PR #16](https://github.com/david-hoffman/simrecon/pull/16), code candidate `cdf4a0745d6b9681e371b006db60239f3f5af0f9`.

This asset-only branch stores non-normative views of the independently reviewed synthetic comparison data. The code candidate, scientific contract, tests, dependencies and verification policy are unchanged. These are phase harmonics of observed volumes, with voxel indices and unspecified intensity units. They do not show physical 3D specimen reconstruction or axial calibration.

- `volume-components.png`: signed DC and first/second complex-harmonic coordinates at both acquired z indices. Color limits are shared within each component column across z.
- `volume-local-error.png`: all 80 voxels, with the largest of five coordinate errors divided by that voxel's own budget. Decimal subtraction/division/logarithms preserve the subnormal case. Exact zero is explicitly marked rather than logged.
- `volume-off-model-projection.png`: stored observations, returned fit, independent fit and residuals at two voxels. Lines join saved exposure samples. Projection mismatch is distinct from numerical fit error.

`data/volume-comparison-inputs.npz` and `data/volume-comparison-outputs.npz` are byte-for-byte copies of the reviewed archives. `data/comparison-data.json` retains the original array descriptors, coordinate order and Decimal numerical data, with local environment paths omitted. It records the original JSON digest. `figure-metrics.json` records every plotted voxel error, budget and ratio. `figure-manifest.json` records data/renderer/output identities and plotting versions.

Reproduce from this branch's root with Python, NumPy and Matplotlib:

```sh
MPLCONFIGDIR=/tmp/pr16-figures-mpl python render_figures.py
```

The renderer checks all 44 archived arrays and verifies that its Decimal-derived case maxima exactly equal the reviewed metrics. It never imports or executes the product or refits a model. Visual layout may vary with plotting-library/font versions; the published PNGs are immutable at their asset commit URLs.
