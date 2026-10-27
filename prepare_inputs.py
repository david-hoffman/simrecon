"""Retain exact frozen input members and fixed 2D display slices; never refit."""
from pathlib import Path
import hashlib
import io
import json
import tarfile
import numpy as np

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
ROOT = args.repo.resolve()
OUT = args.out.resolve()
OUT.mkdir(exist_ok=False, parents=True)
ARCHIVE = args.archive.resolve()
EXPECTED_ARCHIVE = '4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0'
h = hashlib.sha256()
with ARCHIVE.open('rb') as stream:
    for chunk in iter(lambda: stream.read(16 * 1024 * 1024), b''):
        h.update(chunk)
assert h.hexdigest() == EXPECTED_ARCHIVE
print('Authoritative archive hash matched', flush=True)
STUDY = ROOT / 'docs/studies/full-noisy-study-2026-10-26'
inventory = json.loads((STUDY / 'evidence/closed-protocol-file-inventory.json').read_text())['cases']['full']['files']
prefix = 'pr53-full-study/artifacts/pr53-full-study/'
names = [f'generation/observations/specimen_o{o}_p{p}.npy' for o in range(3) for p in range(5)]
names += ['generation/observations/calibration_heldout.npy', 'generation/observations/complete.json', 'inference/freeze.json', 'inference/estimates.json', 'inference/bead_heldout_prediction.npy']
wanted = {prefix + n.replace('generation/', 'full-noisy-trial1/', 1).replace('inference/', 'full-noisy-inference1/', 1): n for n in names}
inputs = {}
arrays = {}
members = {}
with tarfile.open(ARCHIVE, 'r|gz') as archive:
    for member in archive:
        if member.name not in wanted:
            continue
        name = wanted[member.name]
        assert name not in inputs and member.isfile(), member.name
        data = archive.extractfile(member).read()
        actual = {'sha256': hashlib.sha256(data).hexdigest(), 'size_bytes': len(data)}
        assert actual == inventory[name], name
        inputs[name] = actual
        members[name] = member.name
        if name.endswith('.npy'):
            a = np.load(io.BytesIO(data), allow_pickle=False)
            assert a.dtype == np.dtype('<f8') and np.isfinite(a).all(), name
            if 'specimen_o' in name:
                assert a.shape == (32, 256, 256)
                arrays[Path(name).stem] = a[16].copy()
            else:
                assert a.shape == (3, 5, 8, 32, 32)
                arrays[Path(name).stem] = a
        else:
            (OUT / Path(name).name).write_bytes(data)
        if len(inputs) == len(names):
            break
assert set(inputs) == set(names)
np.savez_compressed(OUT / 'fixed-display-inputs.npz', **arrays)
public = STUDY / 'evidence/full-parameter-estimates.json'
(OUT / 'full-parameter-estimates.json').write_bytes(public.read_bytes())
manifest = {'archive_sha256': EXPECTED_ARCHIVE, 'archive_bytes': ARCHIVE.stat().st_size, 'source_commit': '1c209a4769c0caab0fb173287efbcac952ed01b1', 'source_files': inputs, 'members': members, 'fixed_specimen_slice': 16, 'bead_arrays_retained_whole': True, 'no_runtime_import_no_refit': True, 'archive_untouched': True}
(OUT / 'input-provenance.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
est = json.loads((OUT / 'estimates.json').read_text())
print('Verified selected files:', len(inputs), 'bytes:', sum(x['size_bytes'] for x in inputs.values()), flush=True)
print('Detailed specimen keys:', list(est['specimen_fit']), flush=True)
trace = est['specimen_fit']['attempt_trace']
print('Trace length:', len(trace), 'first:', json.dumps(trace[0])[:1800], flush=True)
