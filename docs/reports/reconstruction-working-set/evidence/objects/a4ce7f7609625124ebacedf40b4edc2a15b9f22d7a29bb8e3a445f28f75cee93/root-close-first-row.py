"""ROOT file/scalar/ownership audit of completed first256; no workload or PID scan."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

B = Path('/workspace/work/campaign/evidence/116/growth256-first-readiness')
W = Path('/workspace/work/issue-116')
AID = 'ws116-gp-g256-summary-supplied-r1-u'
D = B / 'batch-row1-ea9117d-a2' / AID
R = W / 'docs/reports/reconstruction-working-set/raw' / AID

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

config = B / 'config-row1-AUTHORIZED-v2.json'
assert sha(config) == '66a9c74c206ead2ea307eddd87e914ca114660fb3032d13dd0e0b66aa40335c3'
c = load(config)
b = load(D / 'eligible-boundary.json')
r = load(R / 'receipt.json')
child = load(R / 'stdout.json')
post = load(D / 'post-metadata.json')
end = load(D / 'observer-exit.json')
assert b['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and b['config_sha256'] == sha(config)
assert b['source_sha256'] == c['binder_sha256'] and b['stage_id'] == c['stage_id']
assert b['stage_admission'] == c['stage_admission'] and b['prior_stage_closures'] == c['prior_stage_closures']
assert b['candidate'] == c['candidate'] and b['material_hashes'] == c['material_hashes']
assert {p.name for p in R.iterdir()} == set(b['raw_files'])
for name, entry in b['raw_files'].items():
    path = R / name
    assert path.is_file() and not path.is_symlink()
    assert path.stat().st_size == entry['logical_bytes'] and sha(path) == entry['sha256'], name
assert r['protocol'] == c['receipt_protocol'] and r['status'] == 'complete_child_observed_pending_scientific_qualification'
assert r['signals'] == [] and r['wait_ownership_lost'] is False and r['nonterminal_wait_events'] == []
assert r['startup_parent_fds_closed'] is True and type(r['startup_eof_observed']) is bool
assert not any(k in r for k in ['stop_reason', 'cleanup_gap', 'postflight_gap', 'error_type'])
t = r['terminal']
assert t['pid'] == r['workload_pid'] == child['pid'] and t['returncode'] == t['exit_code'] == 0
assert t['exited'] is True and t['signaled'] is False and t['wait_status_raw'] == 0
assert t['ru_maxrss_native_units'] == 'Linux KiB' and t['ru_maxrss_multiplier_to_bytes'] == 1024
assert t['kernel_reported_direct_child_high_water_bytes'] == t['rusage_native']['ru_maxrss'] * 1024
for key in ['candidate_before', 'candidate_after', 'candidate_final']:
    assert r[key] == c['candidate']
for key in ['material_hashes_before', 'material_hashes_after', 'material_hashes_final']:
    assert r[key] == c['material_hashes']
assert r['child_record_sha256'] == sha(R / 'stdout.json') and r['grant_sha256'] == sha(D / 'grant.json')
assert child['protocol'] == c['child_protocol'] and child['status'] == 'finite_observation_pending_qualification'
assert child['finite_common_fields'] is True and child['material_identity_matches'] is True
assert child['branches'] == [['known', 'known', 'known']] and child['stages'] == []
assert child['spec']['shape'] == [1, 3, 8, 256, 256] and child['spec']['mode'] == 'summary'
assert child['spec']['search'] is False and child['spec']['repetition'] == 1 and child['spec']['profile'] is False
assert child['spec']['launch']['nonce'] == r['launch']['nonce'] == AID
for key, value in c['expected_core']['growth256-summary-supplied'].items():
    assert child['output_hashes'][key][:3] == [key, value['shape'], value['dtype']]
snapshots = child['snapshots']
assert snapshots['pre_call']['monotonic_ns'] <= child['call_start_monotonic_ns'] <= child['call_end_monotonic_ns']
assert child['call_end_monotonic_ns'] <= snapshots['call_end']['monotonic_ns'] <= snapshots['post_observation']['monotonic_ns'] <= t['reaped_monotonic_ns']
assert child['elapsed_call_seconds'] == (child['call_end_monotonic_ns'] - child['call_start_monotonic_ns']) / 1e9
assert end['returncode'] == 0 and end['overdue'] is False and end['wait_gaps'] == []

markers = [load(R / 'spawn-intent.json')['observer_identity'], load(R / 'owned-child.json')['child_identity']]
fds = sorted(set(r['startup_fd_plan'].values()))
expected = [{'pid': x['pid'], 'start_ticks': x['start_ticks'], 'boot_id': x['boot_id'], 'fds': fds} for x in markers]
assert [x['pid'] for x in expected] == [r['observer_pid'], r['workload_pid']]
assert len(post['owned_processes']) == 2 and [x['expected'] for x in post['owned_processes']] == expected
for item in post['owned_processes']:
    assert item['identity_state'] == 'absent' and set(item['fds']) == {str(fd) for fd in fds}
    assert all(x['state'] == 'absent' for x in item['fds'].values())

proofs = []
for phase in ['pre', 'post']:
    command = load(D / (phase + '-capture-command.json'))
    assert command['returncode'] == 0
    pointer = json.loads(command['stdout'])
    assert sha(pointer['path']) == pointer['sha256']
    proof = load(pointer['path'])
    assert proof['schema'] == 'campaign-resource-domain-correspondence-v1'
    assert proof['capture_source_sha256'] == c['tool_hashes'][c['capture_helper']]
    assert proof['docker_inspect']['stdout'] == c['docker_inspect_stdout']
    assert proof['inner']['returncode'] == proof['docker_inspect']['returncode'] == 0
    inner = json.loads(proof['inner']['stdout'])
    facts = {}
    for label, view in [('outer', proof['outer']), ('inner', inner)]:
        mapping = c['mapping'][label]
        assert view['file_identities'] == mapping['file_identities'] and view['cgroup_namespace'] == mapping['cgroup_namespace']
        for path, text in mapping['fixed_files'].items():
            assert view['files'][path] == text
        files = view['files']
        events = dict(line.split() for line in files['/sys/fs/cgroup/memory.events'].splitlines())
        assert events == mapping['events_exact'] and int(files['/sys/fs/cgroup/memory.swap.current']) == 0
        current, maximum = int(files['/sys/fs/cgroup/memory.current']), int(files['/sys/fs/cgroup/memory.max'])
        assert current + 6442450944 + 3221225472 <= 15032385536 < maximum
        mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
        assert int(mem['MemAvailable'].split()[0]) * 1024 > 9663676416
        facts[label] = {'current_bytes': current, 'events': events, 'swap_bytes': 0}
    proofs.append({'phase': phase, 'proof': {'path': pointer['path'], 'sha256': pointer['sha256']},
                   'started_ns': proof['started_at_unix_ns'], 'finished_ns': proof['finished_at_unix_ns'], 'facts': facts})
assert 0 <= end['runner_invocation_unix_ns'] - proofs[0]['started_ns'] <= 5000000000
assert 0 <= proofs[1]['finished_ns'] - proofs[0]['started_ns'] <= 3720 * 1000000000
gap = r.get('rss_terminal_confirmation')
gap_ns = None
if gap is not None:
    assert gap['bound_seconds'] == 0.05 and gap['outcome'] == 'terminal_confirmed_with_visible_sampling_gap'
    assert gap['first_sample']['VmRSS_bytes'] is None
    assert gap['first_sample']['monotonic_ns'] == gap['origin_monotonic_ns']
    gap_ns = gap['terminal_collected_monotonic_ns'] - gap['origin_monotonic_ns']
    assert 0 <= gap_ns <= 50000000
for name, digest in c['material_hashes'].items():
    assert sha(W / name) == digest
for key, arg in [('head', 'HEAD'), ('tree', 'HEAD^{tree}')]:
    assert subprocess.check_output([c['git'], 'rev-parse', arg], cwd=W, text=True).strip() == c['candidate'][key]
assert subprocess.check_output([c['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b''

eligibility = {'schema': 'ROOT-WS116-growth256-row1-data-eligibility-v1', 'status': 'ROW1_ELIGIBLE_ALL_CURRENT_OWNERS_CLOSED',
               'actual_config': ref(config), 'boundary': ref(D / 'eligible-boundary.json'), 'receipt': ref(R / 'receipt.json'),
               'child': ref(R / 'stdout.json'), 'post_metadata': ref(D / 'post-metadata.json'),
               'candidate': c['candidate'], 'material_hashes': c['material_hashes'],
               'all_raw_hashes_match': True, 'raw_file_count': len(b['raw_files']), 'proofs': proofs,
               'exact2_birth_identities_and_all_FDs_absent': expected,
               'native_direct_child_high_water_bytes': t['kernel_reported_direct_child_high_water_bytes'],
               'native_direct_child_high_water_MiB': t['kernel_reported_direct_child_high_water_bytes'] / 1048576,
               'workflow_call_seconds': child['elapsed_call_seconds'], 'fingerprints': b['fingerprints'],
               'visible_terminal_gap_ns': gap_ns, 'gap_cause': 'UNKNOWN, not RSS=0 or proof of exit',
               'proxy_session_19686_actual_exit0': True, 'not_final_scientific_acceptance': True,
               'remaining5_unreleased': True, 'actual_cost_tokens_serving': 'UNKNOWN', 'observed_at_unix_ns': time.time_ns()}
eligibility_path = B / 'root-row1-data-eligibility.json'
save(eligibility_path, eligibility)
closure = {'schema': 'ROOT-WS116-row1-exclusive-reservation-ended-v1', 'window_closed_early': True,
           'original_authority': c['root_authority'], 'original_window': c['window'],
           'eligible_row1': ref(eligibility_path), 'active_observer_or_proxy': False,
           'all_known_current_stage_owners_closed': True, 'remaining5_not_authorized': True,
           'reason': 'ROOT explicitly pauses after first256 to run prepared113C4 checks/G1 renewal and116finiteguards/fileanalysis; allcurrent2owners/FDs closed. No concurrent scientific work.',
           'next_window': 'Renew actual scheduler/source/material/resource/event/swap/metadata and explicit finite remaining5 authority before continuation; same stageadmission/priorclosures/prefix remain pinned.',
           'closed_at_unix_ns': time.time_ns()}
save(B / 'root-row1-window-closed-for-checks.json', closure)
(B / 'root-live-progress.json').write_text(json.dumps({'status': 'GROWTH256_FIRST_ROW_CLOSED_REMAINING5_UNRELEASED',
    'eligibility': ref(eligibility_path), 'window_closure': ref(B / 'root-row1-window-closed-for-checks.json')}, indent=2, sort_keys=True) + '\n')
print(json.dumps({'eligibility': ref(eligibility_path), 'closure': ref(B / 'root-row1-window-closed-for-checks.json'),
                  'native_bytes': eligibility['native_direct_child_high_water_bytes'], 'call_seconds': child['elapsed_call_seconds'],
                  'visible_gap_ns': gap_ns, 'raw_count': len(b['raw_files']), 'all2owners_and_FDs_absent': True}))
