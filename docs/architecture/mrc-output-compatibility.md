# Modern MRC output compatibility evidence

**Version 1.0**. Intake source inspection on September 30, 2026 (America/Los_Angeles). No product fixture/writer/test was authored or executed. Architecture/task approval remains pending; current state is elsewhere.

## Pinned validator, not a guessed promise

Read the public `mrcfile==1.5.4` wheel through the [published release metadata](https://pypi.org/pypi/mrcfile/1.5.4/json), verified its advertised SHA-256 `195370a13db5ce19600499f9bdf90fd9888979bf39de19a17c19024436c6f4c2`, and inspected `mrcfile/mrcobject.py` in memory with the Python standard library. It was not installed, imported or executed. No legacy source or owner data was uploaded/copied into that request. Initial restricted-network lookup failed; the authorized read-only package request then succeeded.

`MrcObject.validate` accepts only CCP4/MRCO/SERI/AGAR/FEI1/FEI2/HDF5 for a nonempty extension. An unregistered SRM1 tag would fail that check. Therefore the proposal uses a real HDF5 container with the agreed HDF5 type, not a fake known tag or suppressed failure. [CCP-EM MRC2014](https://www.ccpem.ac.uk/mrc-format/mrc2014/) lists HDF5 as an agreed extension type. Our dataset/schema definitions remain project-specific.

The same pinned source rejects negative cell dimensions, not zero ones. This differs from the [prose documentation](https://mrcfile.readthedocs.io/en/stable/source/mrcfile.html), which describes them as positive. The proposal preserves unknown axial scale as zero, labels it as unknown, and keeps actual acquisition axes/physical sampling in metadata. Positive measured lateral sampling is still required. Source inspection is not a successful live reader check; fresh A/B/C/D must establish actual output compatibility.

## Container dependency

The proposed runtime pin is [h5py 3.16.0](https://pypi.org/project/h5py/3.16.0/), with published CPython 3.13 wheels for macOS arm64 and Linux. Its [file API](https://docs.h5py.org/en/stable/high/file.html) supports disk-backed temporary files and its [dataset API](https://docs.h5py.org/en/stable/high/dataset.html) supports bounded slice/chunk access. Metadata staging uses temporary disk space proportional to the source extension, while pixel memory remains block-bounded. Resolver/build/audit and measured working-memory evidence remain required after approval; publication alone does not prove installation or speed in this environment.

The native dependency is not a copied legacy codec or an owned native kernel. Measure all new Python adapters/wrappers; do not claim Python coverage measures HDF5 C internals. The full output remains one MRC file, with the standalone HDF5 image embedded only in its extended header.
