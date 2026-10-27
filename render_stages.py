"""Render observed PR53 stages from verified retained inputs. No fitting or simulation."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(exist_ok=False, parents=True)
data = np.load(args.inputs / 'fixed-display-inputs.npz', allow_pickle=False)
public = json.loads((args.inputs / 'full-parameter-estimates.json').read_text())
details = json.loads((args.inputs / 'estimates.json').read_text())
provenance = json.loads((args.inputs / 'input-provenance.json').read_text())
camera = public['camera_estimate']
blank = camera['means_counts'][1]
contrast = camera['contrast_counts']
raw = np.stack([[data[f'specimen_o{o}_p{p}'] for p in range(5)] for o in range(3)])
observed = (data['calibration_heldout'] - blank) / contrast
predicted = data['bead_heldout_prediction']
residual = predicted - observed
rms = np.sqrt(np.mean(residual * residual, axis=(2, 3, 4)))
recorded_rms = np.array(public['bead_calibration']['heldout_residual_rms'])
trace = details['specimen_fit']['attempt_trace']
assert [row['iteration'] for row in trace] == list(range(13))
assert trace[0]['outcome'] == 'initial_scored'
assert all(row['outcome'] == 'accepted' for row in trace[1:])
assert trace[0]['score'] == public['specimen_fit']['initial_score']
assert trace[-1]['score'] == public['specimen_fit']['best_score']

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
    'axes.titlesize': 11, 'axes.labelsize': 10, 'figure.facecolor': 'white',
    'savefig.facecolor': 'white', 'axes.spines.top': False, 'axes.spines.right': False,
    'pdf.fonttype': 42, 'svg.fonttype': 'none'})
outputs = {}
def save(fig, name):
    for extension in ['png', 'pdf']:
        target = args.out / f'{name}.{extension}'
        fig.savefig(target, dpi=150, bbox_inches='tight', metadata={'Title': name})
        outputs[target.name] = {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'size_bytes': target.stat().st_size}
    plt.close(fig)

def image(ax, a, title, extent, limits, units, cmap='cividis'):
    shown = ax.imshow(a, origin='lower', extent=extent, vmin=limits[0], vmax=limits[1], cmap=cmap, interpolation='nearest')
    ax.set(title=title, xlabel='Local x (µm)', ylabel='Local y (µm)')
    ax.figure.colorbar(shown, ax=ax, shrink=.79, label=units, pad=.025)
    return shown

# 1: No selection of a best exposure or automatic per-image contrast.
raw_limits = [float(raw.min()), float(raw.max())]
fig, axs = plt.subplots(3, 5, figsize=(13.4, 8.3), layout='constrained')
for o in range(3):
    for p in range(5):
        ax = axs[o, p]
        im = ax.imshow(raw[o, p], origin='lower', extent=(0, 20.48, 0, 20.48),
            vmin=raw_limits[0], vmax=raw_limits[1], cmap='cividis', interpolation='nearest')
        if o == 0:
            ax.set_title(f'Exposure {p + 1}')
        if p == 0:
            ax.set_ylabel(f'Orientation {o + 1}\nLocal y (µm)')
        else:
            ax.tick_params(labelleft=False)
        if o == 2:
            ax.set_xlabel('Local x (µm)')
        else:
            ax.tick_params(labelbottom=False)
        ax.set_xticks([0, 10, 20])
        ax.set_yticks([0, 10, 20])
fig.colorbar(im, ax=axs, shrink=.86, pad=.02, label='Raw detector counts · one shared linear scale')
fig.suptitle('1  Recorded noisy specimen images: all 15 exposures\nFixed middle plane z = 2.0625 µm · 20.48 × 20.48 µm field · exposure indices are not fitted phases', fontsize=13)
save(fig, '01-noisy-exposures')

# 2: Camera normalization changes units, not spatial image structure.
fig, axs = plt.subplots(1, 3, figsize=(13.8, 4.4), layout='constrained', gridspec_kw={'width_ratios': [.9, 1.1, 1.1]})
ax = axs[0]
frame_means = np.array(camera['frame_means_counts'])
for k, label in enumerate(['Dark', 'Blank', 'Flat']):
    ax.scatter(k + np.linspace(-.12, .12, 8), frame_means[k], s=22, color='#245f90', zorder=3)
    ax.plot([k - .2, k + .2], [camera['means_counts'][k]] * 2, color='#c65432', lw=2)
ax.set_xticks(range(3), ['Dark', 'Blank', 'Flat'])
ax.set_yscale('log')
ax.set_ylim(5, 3500)
ax.set_ylabel('Frame mean (detector counts; log scale)')
ax.set_title('Eight recorded frames per group')
ax.grid(axis='y', alpha=.2)
example = raw[0, 0]
one_limits = [float(example.min()), float(example.max())]
corrected = (example - blank) / contrast
corr_limits = [(x - blank) / contrast for x in one_limits]
image(axs[1], example, 'Example raw image: orientation 1, exposure 1', (0, 20.48, 0, 20.48), one_limits, 'Detector counts')
image(axs[2], corrected, 'Same pixels after camera correction', (0, 20.48, 0, 20.48), corr_limits, 'Reference-flat-relative image units')
fig.suptitle(f'2  Estimate the camera scale from images, then normalize\ncorrected = (counts − {blank:.5f}) / {contrast:.5f} · same affine display mapping; no spatial deblurring', fontsize=13)
save(fig, '02-camera-correction')

# 3: Fixed held-out image, never selected after comparing predictions.
fig, axs = plt.subplots(2, 2, figsize=(10.8, 9.3), layout='constrained')
a, b, e = observed[0, 0, 4], predicted[0, 0, 4], residual[0, 0, 4]
bead_limits = [float(min(a.min(), b.min())), float(max(a.max(), b.max()))]
diff_limit = float(np.max(np.abs(e)))
image(axs[0, 0], a, 'Corrected held-out observation', (0, 2.56, 0, 2.56), bead_limits, 'Relative image units')
image(axs[0, 1], b, 'Frozen bead-model prediction', (0, 2.56, 0, 2.56), bead_limits, 'Relative image units')
image(axs[1, 0], e, 'Prediction − corrected observation', (0, 2.56, 0, 2.56), [-diff_limit, diff_limit], 'Signed relative image units', 'RdBu_r')
ax = axs[1, 1]
im = ax.imshow(rms, cmap='magma', vmin=0, vmax=float(rms.max()), aspect='auto', interpolation='nearest')
ax.set_xticks(range(5), range(1, 6))
ax.set_yticks(range(3), range(1, 4))
ax.set(xlabel='Held-out exposure index', ylabel='Orientation index', title='Residual RMS over each complete 8 × 32 × 32 volume')
for o in range(3):
    for p in range(5):
        ax.text(p, o, f'{rms[o,p]:.3f}', ha='center', va='center', color='black' if rms[o,p] > .085 else 'white', fontsize=10)
fig.colorbar(im, ax=ax, shrink=.79, pad=.025, label='Relative image units · RMS')
fig.suptitle('3  Image-only bead / illumination calibration, then held-out prediction\nFixed orientation 1, exposure 1, local z = 0.5625 µm · 2.56 × 2.56 µm field · ten sweeps, 940 finite polls', fontsize=13)
save(fig, '03-bead-calibration')

# 4: Only recorded scores exist; do not invent intermediate source volumes.
iterations = [row['iteration'] for row in trace]
objectives = [row['score']['total_objective'] for row in trace]
fig, ax = plt.subplots(figsize=(9.7, 4.8), layout='constrained')
ax.plot(iterations, objectives, 'o-', color='#245f90', lw=2, ms=5)
ax.set(xlabel='Accepted specimen iteration (0 = initial source)', ylabel='Recorded total objective (dimensionless)',
    xticks=iterations, ylim=(0, max(objectives) * 1.22), xlim=(-.3, 12.9))
ax.yaxis.set_major_formatter(ScalarFormatter())
ax.grid(alpha=.2)
ax.annotate(f'Initial: {objectives[0]:.6f}', (0, objectives[0]), xytext=(1.2, objectives[0] * 1.08), arrowprops={'arrowstyle': '-', 'color': '#666666'})
ax.annotate(f'Final: {objectives[-1]:.6f}\n12-iteration limit reached', (12, objectives[-1]), xytext=(7.1, .0165), arrowprops={'arrowstyle': '->', 'color': '#c65432'}, color='#9d3e25')
ax.text(.02, .08, 'Lower training objective does not establish accurate recovery or convergence.\nIntermediate reconstruction images were not stored.', transform=ax.transAxes, fontsize=10,
    bbox={'boxstyle': 'round,pad=.5', 'facecolor': '#fff7e9', 'edgecolor': '#dfb971'})
fig.suptitle('4  Projected nonnegative specimen fit with frozen calibration\nObserved objective = residual sum of squares / (2M) + 0.001 × source sum of squares / (2N)', fontsize=12)
save(fig, '04-specimen-fit-progress')

captions = {
 '01-noisy-exposures': 'All 15 recorded noisy full-case specimen exposures, fixed z index 16 (local z 2.0625 µm), full 20.48 × 20.48 µm field, nearest-neighbor display. Rows identify orientations; columns identify commanded exposures, not estimated true phases. One shared linear detector-count scale across all panels; no clipping or best-exposure selection.',
 '02-camera-correction': 'Left: all eight frame means in each dark/blank/flat group; dots are frame means and short bars group means. Vertical scale is logarithmic detector counts. Right: the same fixed orientation-1/exposure-1/z-16 pixels before and after (counts − estimated blank mean)/estimated flat-minus-blank contrast. Color scales are corresponding affine transforms, so appearance is intentionally unchanged. This changes units, not spatial resolution or deblurring.',
 '03-bead-calibration': 'Corrected observed held-out bead image and frozen prediction at fixed orientation-1/exposure-1/local z-index-4 (0.5625 µm); full 2.56 × 2.56 µm field, nearest-neighbor display, one shared linear relative-image scale. Signed residual is prediction minus corrected observation on a symmetric scale. Heatmap: root mean square (RMS) residual over each whole held-out 8 × 32 × 32 volume, all 15 volumes, in relative image units. No truth-aligned fit or selection is performed; finite calibration does not establish optical-model validity or uniqueness.',
 '04-specimen-fit-progress': 'The initial source and all 12 accepted iteration scores from the recorded attempt trace. The plotted total dimensionless objective uses all M specimen image values and N source coefficients with regularization 0.001. The solver stopped at its declared iteration limit. A decreasing training objective does not establish convergence, accurate reconstruction or resolution gain. Intermediate source/prediction volumes were not serialized and are not illustrated.'}

compact = {
 'camera_estimate': camera,
 'specimen_attempt_trace': [{k: row[k] for k in ['iteration', 'trial', 'candidate_id', 'outcome', 'score']} for row in trace],
 'raw_slice_linear_range_counts': raw_limits,
 'camera_example_range_counts': one_limits,
 'corrected_example_range_relative': corr_limits,
 'bead_shared_linear_range_relative': bead_limits,
 'bead_signed_residual_range_relative': [-diff_limit, diff_limit],
 'heldout_residual_rms': rms.tolist(),
 'maximum_absolute_difference_from_recorded_RMS': float(np.max(np.abs(rms - recorded_rms))),
 'raw_fixed_slice_sha256': {k: hashlib.sha256(np.ascontiguousarray(data[k]).tobytes()).hexdigest() for k in data.files if k.startswith('specimen_')},
 'all15_raw_slices_used': True,
 'selection': {'specimen_z_index': 16, 'example_orientation_index': 0, 'example_exposure_index': 0, 'bead_z_index': 4},
 'no_refit_no_seed_change_no_truth_inputs': True,
}
target = args.out / 'stage-data.json'
target.write_text(json.dumps(compact, indent=2, sort_keys=True) + '\n')
outputs[target.name] = {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'size_bytes': target.stat().st_size}
provenance.update({'schema': 'simrecon.pr53.stage-figures.v1', 'kind': 'observed frozen data, presentation only',
    'source_delivery_commit': '0aa541d6e1483f03d6d800c6d06289fa0073327f',
    'relative_image_units': '(counts − estimated blank mean)/(estimated flat mean − estimated blank mean)',
    'selected_whole_input_files': len(provenance['source_files']),
    'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'matplotlib': matplotlib.__version__, 'backend': 'Agg', 'font_family': 'DejaVu Sans'},
    'render_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'outputs': outputs, 'captions': captions,
    'original_images_and_fits_unchanged': True, 'no_intermediate_iterate_images_available': True,
    'limits': ['one fixed synthetic run, no independent statistical repeats', 'finite clear-pupil model and finite source/pixel/pupil sampling', 'camera contrast is an estimated relative gauge', 'bead held-out prediction is distinct from specimen training objective', 'no recovery, convergence or resolution-gain certification', 'final source and prediction comparison figures remain the original observed renderings']})
(args.out / 'stage-provenance.json').write_text(json.dumps(provenance, indent=2, sort_keys=True) + '\n')
(args.out / 'CAPTIONS.md').write_text('# Observed reconstruction stages\n\n' + '\n\n'.join('## ' + name + '\n\n' + caption for name, caption in captions.items()) + '\n')
print(json.dumps({'outputs': outputs, 'RMS_last_bit_difference': compact['maximum_absolute_difference_from_recorded_RMS']}), flush=True)
