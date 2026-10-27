# PR53: observed reconstruction stages

These presentation assets show the existing fixed noisy study in PR53. The software candidate remains `0aa541d6e1483f03d6d800c6d06289fa0073327f`; these assets change no simulation, inference, tests, settings or seeds. All new images are renders of the original frozen run. The final source and prediction figures in the PR remain the original observed figures.

1. [All 15 noisy specimen exposures](01-noisy-exposures.png) ([PDF](01-noisy-exposures.pdf)). One fixed middle plane and one common linear count scale.
2. [Camera estimation and image correction](02-camera-correction.png) ([PDF](02-camera-correction.pdf)). Eight dark/blank/flat frame means and the same specimen pixels in raw counts and relative image units.
3. [Bead calibration and held-out prediction](03-bead-calibration.png) ([PDF](03-bead-calibration.pdf)). Fixed observed/predicted slices, signed residual and root mean square (RMS) residual for all 15 complete held-out volumes.
4. [Recorded specimen fit progression](04-specimen-fit-progress.png) ([PDF](04-specimen-fit-progress.pdf)). Initial score plus all 12 accepted iterations, stopping at the iteration limit. Intermediate source/prediction volumes were not stored; no intermediate image sequence is invented.

[Full captions](CAPTIONS.md), [exact input/output identities and display provenance](stage-provenance.json), and [camera/iteration data and display ranges](stage-data.json). The original [full PR description and technical appendix](delivery-evidence-before-stage-figures.md) are retained byte-for-byte, including previous local, review, CI, cleanup, historical accounting and limitation records. Its source identities refer to the unchanged software candidate, not this asset commit.

Recovery remains poor: source relative Euclidean norm error 95.3147% and signal prediction error 66.4298%. A lower training objective does not prove convergence, accuracy, uniqueness or resolution gain. This is one fixed synthetic realization under a finite scalar clear-pupil model, source/pixel/pupil discretization and an estimated camera gauge. Calibration held-out residuals are distinct from specimen training residuals.

## Reproduce the presentation

Original raw arrays stay in the retained local archive; this branch does not publish or rerun those large arrays. The archive SHA-256 is `4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0`. The published original report and its closed file inventory live at the software commit above. With that exact source checkout, access to the retained archive, and Python 3.13.12 / NumPy 2.5.1 / Matplotlib 3.11.0, run the following using new absent output directories:

```sh
python prepare_inputs.py --repo /path/to/source-checkout --archive /path/to/study-and-evidence.tar.gz --out ./verified-stage-inputs
MPLCONFIGDIR=./plot-cache python render_stages.py --inputs ./verified-stage-inputs --out ./rendered-stages
```

Preparation reads only 20 named regular members in memory, checks the authoritative whole-archive and published member hashes, and retains fixed slices plus the complete two held-out bead arrays and original manifests/estimates. It never extracts arbitrary archive paths. Rendering imports plotting libraries, not the reconstruction runtime, and never opens truth. Public preparation adds explicit path arguments to the actual initial preparation script; provenance records both hashes. PDF creation metadata may differ on a fresh render. No bitwise rerender guarantee across plotting environments is claimed.
