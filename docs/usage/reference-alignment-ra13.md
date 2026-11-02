# Raw arrays to a finite specimen fit

The development operation `scripts.raw_sim_workflow.reconstruct_raw_sim` composes
observed camera calibration, RA12 calibration handoff and the selected physical
specimen fit. It uses detector counts throughout its input boundary. The output
source uses integrated reference-flat-relative weights. It is an in-memory
workflow; importing it does not run a generator or evaluate private truth.

The [contract](../contracts/reference-alignment-ra13-v1.md) fixes axes, pairing,
geometry, controls, validation, provenance and unavailable/partial outcomes.
`calibration_id` and `specimen_calibration_id` assert the same intended camera/bead
calibration. They must match exactly; labels cannot authenticate acquisition.
Specimen arrays must be native float64 with axes orientation/phase/z/y/x and
leading shape3/5. Camera and bead arrays retain their documented real numeric
representations. File loading, axis declarations and dtype conversion belong to
the caller before this operation.

From a locked worktree root, run this example with `.venv/bin/python`:

```python
import json
from pathlib import Path

import numpy as np

from scripts.raw_sim_workflow import reconstruct_raw_sim

root = Path("docs/studies/reference-alignment-ra13")
for case in ("noiseless", "noisy-diagnostic"):
    folder = root / case
    options = json.loads((folder / "parameters.json").read_text())
    for key in (
        "calibration_origin_um_zyx",
        "specimen_detector_spacing_um_zyx",
        "specimen_origin_um_zyx",
        "sweep_scales",
    ):
        options[key] = tuple(options[key])
    with np.load(folder / "observations.npz", allow_pickle=False) as bundle:
        arrays = {name: bundle[name] for name in bundle.files}
    result = reconstruct_raw_sim(arrays.pop("specimen_counts"), **arrays, **options)
    print(case, result.status, result.stage, result.reason_code)
    if result.specimen_fit is not None:
        fit = result.specimen_fit
        print("finite stop:", fit.stop_reason, "source shape:", fit.source_shape_zyx)
        if fit.best_score is not None:
            print("data objective:", fit.best_score.data_objective)
```

The two [small public observation bundles](../studies/reference-alignment-ra13/README.md)
are declared finite controls. The noiseless example uses central-only illumination
and deliberately permissive training/operator settings to demonstrate composition.
It does not identify a calibrated SIM operator or establish recovery/resolution.
The noisy example has its own fixed diagnostic setting; its actual unavailable or
finite output is reported without a noise-accuracy claim. Both settings were fixed
before workflow execution. No retry, threshold adjustment or best-seed selection
is part of this example.

A failed handoff leaves `specimen_fit=None`, preserving the actual camera/handoff
records and reasons. Never use a retained handoff candidate as fallback illumination.
A numerical-incomplete specimen result may retain a best scored source; it remains
partial. A completed finite fit retains its actual stopping reason. An iteration
limit does not establish convergence. Input errors raise their documented errors;
unrelated exceptions and allocation failures propagate.

Pass original raw counts to this operation. The components correct counts and
transfer calibration-to-specimen phases at their owning stages. A caller must not
pre-correct counts or add the origin shift again. No physical gain, fitted intensity
alignment, exposure equalization, periodic-model substitution or true parameter is
inserted. The result's original-byte hashes identify supplied representation,
with explicit endian/layout limits, and its component diagnostics retain their
original scientific meaning.
