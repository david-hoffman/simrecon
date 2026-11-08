# Reproduce the simulation reconstruction and Wiener sweep

Use the locked environment in the current checkout. The commands below run
from the repository root after installing its locked dependencies. Set
`scratch` to an existing directory outside the checkout. Each generated case
and run needs a new destination directly under that directory.

```sh
python_locked="$PWD/.venv/bin/python"
study="$PWD/docs/studies/simulation-capstone"
scratch=/path/to/existing/scratch
export VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

for case_name in beads cell; do
    "$python_locked" -B "$study/inputs/generate.py" "$case_name" "$scratch/input-$case_name" || break
    "$python_locked" -B "$study/inputs/check_inputs.py" "$case_name" "$scratch/input-$case_name" || break
done
```

Generate and check `clean` or `noisy` with the same commands for a normal
structured-specimen run. The exact check includes independent reference
files. It is a separate process from reconstruction. The following
normal command only reads `specimen.npy`, `calibration.npy` and
`settings.json` from the generated case. It uses Wiener 0.020 and increment 0.

```sh
"$python_locked" -B "$study/reconstruction/run_study.py" beads \
    "$scratch/input-beads" "$scratch/default-beads"
```

For the measured sweep, add `--sweep --observe` and run the cases serially.
The observer opens the independent files after all public calls have returned
for the case. It scores the live default workflow and other four stage
records in the same process. The `--sweep` flag on its own runs the public
sweep and exact replay without opening the evaluator inputs. The cell observer
uses the sibling `noisy-reference-table.npy`.

The five public Wiener values are 0.002, 0.006324555320336759, 0.020,
0.0632455532033676 and 0.200. Each step multiplies the public value by
√10 and the squared term in the filter denominator by 10. The two
intermediate archive labels, `w-0.006325.npz` and `w-0.063246.npz`, round
for display. Calls and numeric receipts use the full values.

To supply another copy of the
exact evaluator table, add `--reference-table PATH` to the cell command.

```sh
"$python_locked" -B "$study/reconstruction/run_study.py" beads \
    "$scratch/input-beads" "$scratch/measured-beads" --sweep --observe &&
"$python_locked" -B "$study/reconstruction/run_study.py" cell \
    "$scratch/input-cell" "$scratch/measured-cell" --sweep --observe &&
"$python_locked" -B "$study/reconstruction/collect_sweep.py" \
    "$scratch/measured-beads" "$scratch/measured-cell" "$scratch/sweep-metrics.json"
```

The measured environment was macOS arm64 with CPython 3.13.12, NumPy 2.5.3,
SciPy 1.18.1 and Apple Accelerate. The measured worker set and read back
Accelerate Basic Linear Algebra Subprograms (BLAS) threading mode 1 on the
thread making the public calls, in addition to the one-thread environment.
To reproduce that explicit macOS mode from a shell, use this wrapper in
place of the leading `"$python_locked" -B` for the reconstruction commands.

```sh
run_apple() {
    "$python_locked" -B -c '
import ctypes, runpy, sys
from pathlib import Path

blas = ctypes.CDLL("/System/Library/Frameworks/Accelerate.framework/Accelerate")
blas.BLASSetThreading.argtypes = (ctypes.c_uint,)
blas.BLASSetThreading.restype = ctypes.c_int
blas.BLASGetThreading.argtypes = ()
blas.BLASGetThreading.restype = ctypes.c_uint
if (blas.BLASSetThreading(1), blas.BLASGetThreading()) != (0, 1):
    raise RuntimeError("Apple Accelerate did not select one thread")
sys.argv = sys.argv[1:]
sys.path.insert(0, str(Path(sys.argv[0]).resolve().parent))
runpy.run_path(sys.argv[0], run_name="__main__")
' "$@"
}
```

The accepted exact input checker and signed witness determine whether a
different numerical build reproduces the study.

## Files and identities

- `w-0.020.npz` and the four other value-specific NumPy ZIP archives use
  `image`, `x_um`, `y_um`, and `z_um`. The binary64 image has shape
  `(32, 256, 256)` in z, y, x order and contains signed native reconstruction
  counts on the workflow's analog-to-digital unit (ADU) scale. The
  corresponding binary64 axes are in micrometres. The observer uses the
  frozen conversion of 0.000020 simulation source units (SU) per count
  for scoring.
- `runtime.json` records the input hashes, actual resolved workflow and
  filtering settings, fitted carriers and complex modulation, support cutoffs
  and each observation file's SHA-256. The exact default replay compares the
  original workflow image, filtered quadratures, axes, fitted factors and
  cutoffs with the known-stage result. The receipt retains its array
  identities and the actual replay's returned settings and cutoffs.
- `fixed-factors.npz` contains the exact common prepared quadratures
  `(1, 3, 5, 32, 128, 65)`, transfer samples `(3, 65, 32)`,
  noise variance factors, separation matrices, phase angles, carriers and
  complex modulation. Complex arrays retain their actual dtype and values.
  The receipt identifies each array by shape, little-endian dtype and SHA-256
  of contiguous element bytes.
- `rows.jsonl` holds each completed witness row. `case.json` contains the
  reference and fixed-factor metadata. Each row records its observation
  provenance. The collector verifies all ten signed
  observation and axis identities, then writes `{"rows": [...], "cases": {...}}`.
- `bead-default-score.json` links the exact default observation archive
  through its `receipt_sha256`. It contains the reviewed bead scores for
  `truth`, `same_dose_conventional` and `reconstruction`, with signed
  profile samples and baselines.
- `progress.jsonl` records the stage and value, each saved observation,
  completed witness rows and the terminal status. On a failed call, keep
  the partial directory and use a new destination for another run.

The case directories and full observations belong in local scratch. The
compact aggregate supplies the measured figure inputs together with the
original generated references and registered representative observations.
