"""ROOT prepares a disabled finite continuation; no scientific launch."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import time

B = Path('/workspace/work/campaign/evidence/116/growth256-first-readiness')
P = B / 'coordinator-remaining5-readiness'
W = Path('/workspace/work/issue-116')

def load(path):
    return json.loads(Path(path).read_bytes())

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def ref(path):
    return {'path': str(path), 'sha256': sha(path)}

def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

assert sha(P / 'config-remaining5-UNAUTHORIZED.json') == 'b8dee8ccbe90517aa8b110ca6454bf8c37af75e4383638b915f019197ce0b046'
c = load(P / 'config-remaining5-UNAUTHORIZED.json')
old = load(B / 'config-row1-AUTHORIZED-v2.json')
ad = load(old['stage_admission']['path'])
assert c['authorized'] is False and c['continuation_authorized'] is True and len(c) == 44
for key in ['candidate', 'material_hashes', 'expected_core', 'tool_hashes', 'accepted_method7',
            'method7_expected', 'environment', 'environment_expected', 'stage_admission', 'prior_stage_closures']:
    assert c[key] == old[key], key
assert c['allowed_attempt_ids'] == [row['attempt_id'] for row in ad['stage_rows'][1:]]
assert [x['sha256'] for x in c['prior_eligible']] == ['9da7715f05d723386764c538a6de90009be8edf5977db5e4a660d7ebf125da86']
assert len(c['material_hashes']) == 35 and len(c['expected_core']) == 28 and len(c['tool_hashes']) == 6
for path, digest in c['material_hashes'].items():
    assert sha(W / path) == digest, path
for path, digest in c['tool_hashes'].items():
    assert sha(path) == digest, path
for key, arg in [('head', 'HEAD'), ('tree', 'HEAD^{tree}')]:
    assert subprocess.check_output([c['git'], 'rev-parse', arg], cwd=W, text=True).strip() == c['candidate'][key]
assert subprocess.check_output([c['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b''
assert not Path(c['external_batch_directory']).exists()
ledger = load(P / 'currentstage-ledger-DRAFT.json')
owned = [entry['identity'] for entry in ledger['closed_owned_processes']]
assert len(owned) == 2
request = B / 'root-remaining5-preflight-metadata-request.json'
save(request, {'disk_paths': [str(W), str(B)], 'owned_processes': owned})
argv = [c['docker'], 'exec', '--user', '1000:1000', '-w', str(W)]
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    argv += ['-e', name + '=1']
argv += [c['container'], c['inner_python'], c['metadata_source']['path'], str(request)]
x = subprocess.run(argv, capture_output=True, text=True)
save(B / 'root-remaining5-preflight-metadata-command.json', {'argv': argv, 'returncode': x.returncode, 'stdout': x.stdout, 'stderr': x.stderr})
assert x.returncode == 0
m = json.loads(x.stdout)
save(B / 'root-remaining5-preflight-metadata.json', m)
for key in ['uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits']:
    assert m[key] == old['metadata_expected'][key], key
assert [v['expected'] for v in m['owned_processes']] == owned
for item in m['owned_processes']:
    assert item['identity_state'] == 'absent'
    assert set(item['fds']) == {str(fd) for fd in item['expected']['fds']}
    assert all(v['state'] == 'absent' for v in item['fds'].values())
for disk in m['disks'].values():
    assert disk['free_bytes'] >= 2965897216 and disk['free_inodes'] > 0
c['metadata_expected'] = copy.deepcopy(old['metadata_expected'])
c['metadata_expected']['disk_identity'] = {
    str(W): {k: m['disks'][str(W)][k] for k in ['device', 'fsid', 'fragment_size']},
    c['external_batch_directory']: {k: m['disks'][str(B)][k] for k in ['device', 'fsid', 'fragment_size']}}

x = subprocess.run([c['outer_python'], c['capture_helper']], capture_output=True, text=True)
save(B / 'root-remaining5-preparation-context-command.json', {'returncode': x.returncode, 'stdout': x.stdout, 'stderr': x.stderr})
assert x.returncode == 0
pointer = json.loads(x.stdout)
assert sha(pointer['path']) == pointer['sha256']
proof = load(pointer['path'])
assert proof['docker_inspect']['returncode'] == proof['inner']['returncode'] == 0
assert proof['docker_inspect']['stdout'] == old['docker_inspect_stdout']
inner = json.loads(proof['inner']['stdout'])
assert proof['outer']['file_identities'] == inner['file_identities']
c['mapping'] = copy.deepcopy(old['mapping'])
facts = {}
for label, view in [('outer', proof['outer']), ('inner', inner)]:
    mapping = c['mapping'][label]
    assert view['file_identities'] == mapping['file_identities'] and view['cgroup_namespace'] == mapping['cgroup_namespace']
    for path, text in mapping['fixed_files'].items():
        assert view['files'][path] == text, (label, path)
    files = view['files']
    events = dict(line.split() for line in files['/sys/fs/cgroup/memory.events'].splitlines())
    assert events == {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
    current, maximum = int(files['/sys/fs/cgroup/memory.current']), int(files['/sys/fs/cgroup/memory.max'])
    swap = int(files['/sys/fs/cgroup/memory.swap.current'])
    mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
    available = int(mem['MemAvailable'].split()[0]) * 1024
    assert current + 6442450944 + 3221225472 <= 15032385536 < maximum
    assert swap == 0 and available > 9663676416
    mapping['events_exact'] = events
    mapping['swap_current_bytes'] = swap
    facts[label] = {'current_bytes': current, 'maximum_bytes': maximum, 'events': events,
                    'swap_bytes': swap, 'host_available_bytes': available,
                    'current_plus_process_stop_plus_reserve_bytes': current + 6442450944 + 3221225472}
c['expected_exposed'] = copy.deepcopy(old['expected_exposed'])
c['docker_inspect_stdout'] = proof['docker_inspect']['stdout']
admission = {'schema': 'ROOT-WS116-growth256-remaining5-new-context-admission-v1', 'accepted': True,
             'candidate': c['candidate'], 'all35materials28cores6tools_match': True,
             'same_geometry_and_source_operating_proposals': True,
             'same_stage_admission': c['stage_admission'], 'prior_eligible': c['prior_eligible'],
             'root_row1_eligibility': ref(B / 'root-row1-data-eligibility.json'),
             'coordinator_row1_review': ref(B / 'coordinator-row1-closed-file-review.json'),
             'prior_window_closed': ref(B / 'root-row1-window-closed-for-checks.json'),
             'new_context': {'path': pointer['path'], 'sha256': pointer['sha256']}, 'facts': facts,
             'fresh_exact2owner_metadata': ref(B / 'root-remaining5-preflight-metadata.json'),
             'limits': 'Recorded current preparation only; actual every-row metadata/lastcapture<=5s/newnative/endproof guards remain. Single r1 outcome is not a prediction or complete3repstat. No nextstage/full/profile or automaticretry.',
             'external_ancestors': 'unknown_unobservable', 'outside_actors': 'unknown_not_scanned'}
adpath = B / 'root-remaining5-new-context-admission.json'
save(adpath, admission)
now = time.time_ns()
window = {'starts_unix_ns': now, 'ends_unix_ns': now + 21600 * 1000000000}
ack = load(P / 'scheduler-ACK-DRAFT.json')
ack.update(schema='ROOT-campaign-stage-suspension-ACK-v1', window=window, observed_at_unix_ns=now,
           campaign_work_suspended=True, known_active_numerical_processes=[], unresolved_owners=[])
ack['known_work_closure'] = {'113': 'C4threecheap/G1normal/Pyright runtimes and privateinit/proxies/pipes closed. C1author SOURCE-only correction; no runtime/import/tests/lint/types/build/install.',
                             '116': 'First256r1 bothowners/FDs closed; a3guard+192actualanalysis ended0; metadata/capture just returned. EAunchanged.',
                             '114_117_118': 'Only source plans completed; no runtime/owners.',
                             '119_120': 'Intake-only waiting; no runtime.',
                             'root': 'Only finite packet/file/operationalmetadata work; all unrelated numerical/gate/build/install/test work suspended.'}
ack['scope'] = 'Known campaign schedule only; outsideactors notscanned; ACK is not grantauthority. Source-only authoring permitted.'
ackpath = B / 'root-scheduler-ACK-remaining5.json'
save(ackpath, ack)
authority = load(P / 'authority-DRAFT.json')
authority.update(schema='ROOT-WS116-growth256-remaining5-authority-v1', authorized=True, execution_authorized=True,
                 window=window, campaign_ownership_resolved=True, fresh_preflight_accepted=True)
authority['fresh_preflight'] = ref(adpath)
authority['scheduler_ACK'] = ref(ackpath)
authority['final_config_gate'] = 'Config remains authorizedfalse until coordinator file audit and separate ROOT explicit execution release.'
authpath = B / 'root-authority-remaining5.json'
save(authpath, authority)
ledger.update(root_authority_sha256=sha(authpath), unresolved=[])
ledger['fresh_exact_owner_metadata'] = ref(B / 'root-remaining5-preflight-metadata.json')
ledger['meaning'] = 'Recorded row1 receipt identities, independently verified absent with all expectedFDs in newactualmetadata. Existing binder freshly rechecks exact currentstage owners, no globalabsence claim.'
ledgerpath = B / 'root-current-stage-ledger-remaining5.json'
save(ledgerpath, ledger)
c.update(root_authority=ref(authpath), authority_expected=authority, window=window,
         scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath))
c['grant_fixed'].update(numerical_release=True, campaign_ownership_resolved=True)
c['grant_fixed']['exclusive_window'] = {'released': True, 'evidence': str(authpath), 'evidence_sha256': sha(authpath),
                                      'scope': 'WS116 exact frozen growth/profile stage release'}
c['conditional_rationale'] = 'ROOT prospective finite remaining256 rows2-6 only; exacteligibleclosedr1 prefix/same1f4stageadmission retained, no r1rerun. Freshsource/case/resource/context/owner/schedule preflight, new6hwindow notruntimeprediction. Configdisabled until audit+ROOTfinalrelease. Existing every-rowfresh/endguards; anyfailure HOLD, no automaticretry/recapture/growth/full/profile. Outsideactors/ancestors unknown.'
out = B / 'config-remaining5-PREPARED.json'
save(out, c)
print(json.dumps({'prepared_config': ref(out), 'authority': ref(authpath), 'ACK': ref(ackpath),
                  'ledger': ref(ledgerpath), 'new_admission': ref(adpath), 'window': window, 'facts': facts,
                  'allowed': c['allowed_attempt_ids'], 'execution_released': False}))
