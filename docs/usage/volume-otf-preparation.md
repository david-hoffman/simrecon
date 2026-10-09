# Prepare a sampled volume OTF

`prepare_volume_otf` prepares the optical transfer function (OTF) of a supplied
three-dimensional intensity point spread function (PSF). Supply the z/y/x sample
spacing in micrometres (µm), the zero-displacement sample index and an opaque source
label. All three keywords are required. The [contract](../contracts/volume-otf-preparation-v1.md)
defines accepted representations, errors and numerical budgets.

This standalone example was executed with the worktree's pinned `.venv/bin/python`:

```python
import numpy as np
from simrecon import prepare_volume_otf

psf = np.zeros((3, 4, 2), dtype=np.float64)
for position, mass in [
    ((0, 0, 0), 3), ((1, 0, 0), 1), ((0, 1, 0), 4),
    ((0, 0, 1), 2), ((2, 3, 1), 5),
]:
    psf[position] = mass
calibration = prepare_volume_otf(
    psf,
    voxel_size_um=(0.7, 1.25, 2.5),
    origin_zyx=(2, 1, 1),
    source="example:finite intensity samples v1",
)
print("shape z/y/x:", calibration.values.shape)
print("DC:", calibration.values[1, 2, 1])
print("H at modes (1, 1, -1):", calibration.values[2, 3, 0])
print("fz in cycles/um:", calibration.fz_per_um)
print("fy in cycles/um:", calibration.fy_per_um)
print("fx in cycles/um:", calibration.fx_per_um)
```

Observed output:

```text
shape z/y/x: (3, 4, 2)
DC: (1+0j)
H at modes (1, 1, -1): (-0.19999999999999998+0.2976067743425169j)
fz in cycles/um: [-0.47619048  0.          0.47619048]
fy in cycles/um: [-0.4 -0.2  0.   0.2]
fx in cycles/um: [-0.2  0. ]
```

The zero-frequency (DC) index is `(Nz//2, Ny//2, Nx//2)`. Each axis is centered
and increasing; an even axis includes the negative Nyquist endpoint. The
[NumPy multidimensional transform](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html)
and [centered ordering](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftshift.html)
describe the underlying operations.

For converted float64 samples `a`, normalize sample mass with `p=a/sum(a)` and
calculate `H=sum(p*exp(-2*pi*i*sum(k*(position-origin)/N)))`. No `1/M` factor
follows the sum, where `M=Nz*Ny*Nx`. Here the raw discrete mass is
`3+1+4+2+5=15`; normalized mass is one, so DC is one. Uniform voxel volume
cancels. Transfer values are dimensionless, and signed real and imaginary parts
both matter. The frequency at mode `k` is `k/(N*d)` cycles/µm. For example,
`fz(1)=1/(3*0.7)=0.476190476…` cycles/µm. Moving both the samples and the declared
origin by the same periodic integer translation preserves the transfer.

The returned frozen `Otf3D` has exactly `values`, `fz_per_um`, `fy_per_um`,
`fx_per_um`, `voxel_size_um`, `origin_zyx` and `source`. Its bindings are frozen;
its four separately owned arrays remain writable. `values` is native complex128,
frequency arrays are native float64, and all arrays are C-contiguous. Preparation
copies inputs and leaves their bytes, layout and write permissions unchanged.
Direct construction of `Otf3D` does not validate arguments.

Source samples must be finite and nonnegative before conversion. Integer rounding
and floating conversion underflow define the stored float64 problem. Converted
mass must remain positive. Maximum and all-positive-subnormal float64 samples are
supported without summing the raw samples. Singleton axes accept every finite
positive converted spacing. Nonfinite, collapsed or unordered final frequency
grids reject with `unrepresentable_otf_frequencies`.

Handled numerical transform failures reject with `otf_transform_failure`:
`FloatingPointError`, `OverflowError`, arithmetic `RuntimeWarning` and nonfinite
transfer results. Memory errors and unrelated exceptions propagate. Scoped
arithmetic preserves the caller's NumPy error policy and warning filters.
The function reads no files and does not authenticate or persist `source`.

This is a finite sampled periodic kernel. It discards absolute throughput and
supplies no continuous-optics or infinite-field convergence guarantee. It does
not estimate background, origin, sampling, optical support or instrument
parameters. Record input identity, preprocessing, origin, sampling and resolved
software separately; the label alone proves none of them.

Physical three-dimensional structured illumination microscopy (SIM) needs
order-dependent effective transfers and relative gains. Axial illumination
profiles modify the conventional OTF in the model of
[Gustafsson et al., equations 5–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf).
This operation supplies no such factors or reconstruction. See the
[measured independent comparison](../reports/volume-otf-preparation-comparison.md)
for full-array accuracy evidence and the signed figure.

Local execution evidence is retained under `artifacts/volume-otf-execution/`:
`c-usage-v1.py` and `c-usage-01.log`. These ignored artifacts are not shipped.
