"""Read frozen run members and derive orthogonal displays; no inference or refitting."""
import argparse
from pathlib import Path
import hashlib
import io
import json
import tarfile
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
study = args.repo / 'docs/studies/full-noisy-study-2026-10-26'
plan = json.loads((study / 'full-plan.json').read_text())
parameters = json.loads((study / 'evidence/full-parameter-estimates.json').read_text())
inventory = json.loads((study / 'evidence/closed-protocol-file-inventory.json').read_text())['cases']['full']['files']
expected_archive = '4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0'
h = hashlib.sha256()
with args.archive.open('rb') as source:
    for chunk in iter(lambda: source.read(16 * 1024 * 1024), b''):
        h.update(chunk)
assert h.hexdigest() == expected_archive
print('Original archive hash matched', flush=True)

def coordinate_choice(shape, spacing, center):
    indices = [int(np.argmin(np.abs((np.arange(n) + .5) * d - c))) for n, d, c in zip(shape, spacing, center)]
    actual = [(i + .5) * d for i, d in zip(indices, spacing)]
    return {'nominal_bead_center_local_um_zyx': list(center), 'indices_zyx': indices, 'actual_plane_centers_local_um_zyx': actual, 'shape_zyx': list(shape), 'spacing_um_zyx': list(spacing), 'selection': 'first catalogue row; nearest voxel center, first index on an exact tie; no fitted-peak recentering'}

def crop_bounds(shape, spacing, center, halfwidth):
    return [[max(0, int(np.floor((c - w) / d))), min(n, int(np.ceil((c + w) / d)))] for n, d, c, w in zip(shape, spacing, center, halfwidth)]

arrays = {}
choices = {}
def views(name, a, spacing, center, crop=None):
    choice = coordinate_choice(a.shape, spacing, center)
    iz, iy, ix = choice['indices_zyx']
    arrays[name + '_xy_mip'] = np.max(a, axis=0)
    arrays[name + '_xz_mip'] = np.max(a, axis=1)
    bounds = crop_bounds(a.shape, spacing, center, crop) if crop else [[0, n] for n in a.shape]
    (z0,z1),(y0,y1),(x0,x1) = bounds
    arrays[name + '_xy_slice'] = a[iz, y0:y1, x0:x1].copy()
    arrays[name + '_xz_slice'] = a[z0:z1, iy, x0:x1].copy()
    choice['crop_index_bounds_zyx_exclusive'] = bounds
    choice['xy_slice_extent_um'] = [x0*spacing[2], x1*spacing[2], y0*spacing[1], y1*spacing[1]]
    choice['xz_slice_extent_um'] = [x0*spacing[2], x1*spacing[2], z0*spacing[0], z1*spacing[0]]
    choices[name] = choice

spacing_raw = (.125,.08,.08)
spacing_source = (.125,.04,.04)
spec_center = plan['specimen_catalogue'][0][:3]
bead_center = plan['bead_catalogue'][0][:3]
names = [f'generation/observations/specimen_o{o}_p{p}.npy' for o in range(3) for p in range(5)]
names += ['generation/observations/calibration_heldout.npy', 'inference/bead_heldout_prediction.npy', 'generation/private_truth/specimen_source_e.npy', 'inference/specimen_source_relative.npy', 'inference/prediction_o0_p0.npy', 'generation/private_truth/specimen_o0_p0_expected_signal_e.npy', 'generation/observations/complete.json', 'inference/freeze.json']
prefix = 'pr53-full-study/artifacts/pr53-full-study/'
wanted = {prefix + n.replace('generation/', 'full-noisy-trial1/', 1).replace('inference/', 'full-noisy-inference1/', 1): n for n in names}
found = {}
held = {}
whole_ranges = {}
for_tar = {}
with tarfile.open(args.archive, 'r|gz') as archive:
    for member in archive:
        if member.name not in wanted:
            continue
        name = wanted[member.name]
        assert member.isfile() and name not in found
        data = archive.extractfile(member).read()
        identity = {'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}
        assert identity == inventory[name], name
        found[name] = identity
        for_tar[name] = member.name
        if name.endswith('.json'):
            (args.out / Path(name).name).write_bytes(data)
        else:
            a = np.load(io.BytesIO(data), allow_pickle=False)
            assert np.isfinite(a).all()
            stem = Path(name).stem
            if '/observations/specimen_' in name:
                assert a.shape == (32,256,256)
                views(stem, a, spacing_raw, spec_center, (.65,1.,1.))
                whole_ranges[stem] = [float(a.min()), float(a.max())]
                if stem == 'specimen_o0_p0':
                    held['raw'] = a
            elif stem in ['calibration_heldout','bead_heldout_prediction']:
                assert a.shape == (3,5,8,32,32)
                held[stem] = a
            elif stem == 'specimen_source_e':
                assert a.shape == (64,512,512)
                factor = plan['camera']['gain_counts_per_e'] / parameters['camera_estimate']['contrast_counts']
                held['reference'] = factor * (a[::2] + a[1::2])
            elif stem == 'specimen_source_relative':
                assert a.shape == (32,512,512)
                held['estimate'] = a
            elif stem == 'prediction_o0_p0':
                assert a.shape == (32,256,256)
                held['prediction'] = a
            elif stem == 'specimen_o0_p0_expected_signal_e':
                held['expected_e'] = a
            else:
                raise AssertionError(name)
        if len(found) == len(names):
            break
assert set(found) == set(names)
blank = parameters['camera_estimate']['means_counts'][1]
contrast = parameters['camera_estimate']['contrast_counts']
observed_bead = (held['calibration_heldout'] - blank) / contrast
bead_pred = held['bead_heldout_prediction']
for key, a in [('bead_observed', observed_bead[0,0]), ('bead_prediction',bead_pred[0,0])]:
    views(key, a, spacing_raw, bead_center)
    whole_ranges[key] = [float(a.min()),float(a.max())]
rms = np.sqrt(np.mean((bead_pred - observed_bead)**2, axis=(2,3,4)))
assert np.array_equal(rms, np.array(parameters['bead_calibration']['heldout_residual_rms']))
arrays['bead_all_volume_RMS'] = rms
corrected = (held['raw'] - blank) / contrast
for key,a in [('corrected',corrected),('prediction',held['prediction'])]:
    views(key, a, spacing_raw, spec_center, (.65,1.,1.))
    whole_ranges[key] = [float(a.min()),float(a.max())]
for key,a in [('source_reference',held['reference']),('source_estimate',held['estimate'])]:
    views(key, a, spacing_source, spec_center, (.65,1.,1.))
    whole_ranges[key] = [float(a.min()),float(a.max())]
    np.save(args.out / (key + '.npy'), a, allow_pickle=False)

# Post-freeze descriptive evaluation, never a new source or altered official metric.
ref = held['reference']
est = held['estimate'].astype(np.float64)
support = ref > 0
ref2 = float(np.sum(ref*ref))
est2 = float(np.sum(est*est))
dot = float(np.sum(ref*est))
err = est-ref
source_stats = {'count':ref.size, 'truth_nonzero_voxels':int(support.sum()), 'truth_support_fraction':float(np.mean(support)),
    'reference_norm':float(np.sqrt(ref2)), 'estimate_norm':float(np.sqrt(est2)), 'error_norm':float(np.linalg.norm(err.ravel())),
    'relative_error':float(np.linalg.norm(err.ravel())/np.sqrt(ref2)), 'reference_max':float(ref.max()), 'estimate_max':float(est.max()),
    'reference_sum':float(ref.sum()),'estimate_sum':float(est.sum()),'dot_estimate_reference':dot,
    'cosine_similarity':float(dot/np.sqrt(ref2*est2)), 'estimate_energy_in_true_support_fraction':float(np.sum(est[support]**2)/est2),
    'squared_error_in_true_support_fraction':float(np.sum(err[support]**2)/np.sum(err**2)),
    'hypothetical_truth_chosen_scalar_only_diagnostic':{'scale':dot/est2,'remaining_relative_error':float(np.sqrt(max(0,1-dot*dot/(ref2*est2)))),'changes_frozen_fit_or_official_metric':False}}
for key,a in [('example_corrected_observation',corrected),('example_prediction',held['prediction']),('example_expected_signal_relative',plan['camera']['gain_counts_per_e']*held['expected_e']/contrast)]:
    np.save(args.out/(key+'.npy'),a,allow_pickle=False)
np.savez_compressed(args.out/'orthogonal-views.npz',**arrays)
metadata = {'schema':'simrecon.pr53.orthogonal-inputs.v1','archive_sha256':expected_archive,'input_files':found,'archive_members':for_tar,
    'source_commit':'0aa541d6e1483f03d6d800c6d06289fa0073327f','choices':choices,'whole_volume_ranges':whole_ranges,'camera_blank':blank,'camera_contrast':contrast,
    'calibration_origin_local_label_um_zyx':plan['geometry']['calibration_origin_um_zyx'],'specimen_first_catalogue_bead':plan['specimen_catalogue'][0],
    'calibration_first_catalogue_bead':plan['bead_catalogue'][0],'source_stats':source_stats,
    'projection_definition':{'XY':'maximum over all z samples; rows y, columns x','XZ':'maximum over all y samples; rows z, columns x','difference':'displayed estimate projection minus displayed reference projection; not maximum of signed residual'},
    'truth_use':'Only post-freeze source evaluation and predeclared first-catalogue visualization plane selection. No inference run or changed fit.',
    'physical_aspect':'Equal physical units on x/y/z display axes; do not stretch XZ into a square',
    'no_alignment_interpolation_or_peak_selection':True,'prepare_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(args.out/'orthogonal-input-provenance.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps({'selected_files':len(found),'selected_bytes':sum(x['size_bytes'] for x in found.values()),'source_stats':source_stats,'source_bead_choice':choices['source_reference'],'calibration_bead_choice':choices['bead_observed']}),flush=True)
