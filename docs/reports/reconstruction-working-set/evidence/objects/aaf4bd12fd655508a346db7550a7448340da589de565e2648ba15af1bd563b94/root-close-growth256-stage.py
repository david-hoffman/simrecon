"""UNEXECUTED fixed CLOSED256 file audit; only ROOT may release this helper.

No capture, workload, process/FD scan, signal, wait, retry, or statistical summary.
The only subprocesses, after explicit release, are three fixed read-only git calls.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

B = Path('/workspace/work/campaign/evidence/116/growth256-first-readiness')
W = Path('/workspace/work/issue-116')
S = Path('/workspace/work/campaign/evidence/116/growth256-stage-closure-source')
OUTPUT = B / 'root-growth256-stage-closed.json'
RELEASE = S / 'ROOT-execution-release.json'
ATTESTATION = S / 'ROOT-controller-94974-ended.json'
CONFIGS = [
    (B / 'config-row1-AUTHORIZED-v2.json', '66a9c74c206ead2ea307eddd87e914ca114660fb3032d13dd0e0b66aa40335c3'),
    (B / 'config-remaining5-AUTHORIZED.json', '72b3830ff1f6936b7332cb54a2b64fb6c3d86e5af532fd8999f7dfeaf8a3d197'),
]
IDS = [f'ws116-gp-g256-summary-{kind}-r{rep}-u'
       for kind in ('supplied', 'searched') for rep in (1, 2, 3)]


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f'not a regular input: {path}')
    require(path.stat().st_size <= 16777216, f'JSON input exceeds 16MiB: {path}')
    return json.loads(path.read_bytes())


def sha(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f'not a regular hash input: {path}')
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def checked(pointer):
    require(set(pointer) == {'path', 'sha256'}, 'exact file pointer required')
    require(sha(pointer['path']) == pointer['sha256'], f'file hash mismatch: {pointer["path"]}')
    return load(pointer['path'])


def identity_key(item):
    return (item['pid'], item['start_ticks'], item['boot_id'], tuple(item['fds']))


def absent_items(post, expected, exact):
    actual = post['owned_processes']
    keyed = {identity_key(item['expected']): item for item in actual}
    require(len(keyed) == len(actual), 'duplicate recorded owner identity')
    wanted = {identity_key(item) for item in expected}
    require(wanted <= set(keyed), 'current pair absent from accumulated metadata')
    if exact:
        require(set(keyed) == wanted, 'final metadata must exactly cover all12 owners')
    for key in wanted:
        item = keyed[key]
        require(item['identity_state'] == 'absent', 'recorded owner not absent')
        require(set(item['fds']) == {str(fd) for fd in key[3]}, 'recorded FD coverage mismatch')
        require(all(value['state'] == 'absent' for value in item['fds'].values()), 'recorded FD not absent')


def metadata(path, config):
    item = load(path)
    require(item['protocol'] == 'WS116-fixed-ubuntu-metadata-v1', 'metadata protocol')
    require(item['source_sha256'] == config['metadata_source']['sha256'], 'metadata source')
    phase = path.name.removesuffix('-metadata.json')
    request_path = path.parent / (phase + '-metadata-request.json')
    require(item['request_sha256'] == sha(request_path), 'metadata request bytes')
    request = load(request_path)
    require([value['expected'] for value in item['owned_processes']] == request['owned_processes'], 'metadata exact request coverage')
    for key in ('boot_id', 'cwd', 'executable', 'uid', 'gid', 'namespaces', 'rlimits'):
        require(item[key] == config['metadata_expected'][key], f'metadata identity: {key}')
    require(item['environment'] == config['environment_expected']['thread_controls'], 'thread environment')
    require(item['external_ancestors'] == 'unknown_unobservable', 'external ancestors scope')
    require(item['outside_campaign_processes'] == 'unknown_not_scanned', 'outside actor scope')
    for name, expected in config['metadata_expected']['disk_identity'].items():
        for key, value in expected.items():
            require(item['disks'][name][key] == value, f'disk identity: {name}/{key}')
        require(item['disks'][name]['free_bytes'] >= 2965897216 and item['disks'][name]['free_inodes'] > 0, 'recorded disk headroom')
    absent_items(item, request['owned_processes'], True)
    return item


def resource_proofs(directory, config, end):
    proofs = []
    for phase in ('pre', 'post'):
        command = load(directory / (phase + '-capture-command.json'))
        require(command['returncode'] == 0, 'capture command failed')
        parsed = json.loads(command['stdout'])
        pointer = {key: parsed[key] for key in ('path', 'sha256')}
        proof = checked(pointer)
        require(proof['schema'] == 'campaign-resource-domain-correspondence-v1', 'proof schema')
        require(proof['external_ancestors'] == 'unknown_unobservable', 'proof external ancestors scope')
        require(proof['capture_source_sha256'] == config['tool_hashes'][config['capture_helper']], 'capture source')
        require(proof['docker_inspect']['stdout'] == config['docker_inspect_stdout'], 'recorded container context')
        require(proof['inner']['returncode'] == proof['docker_inspect']['returncode'] == 0, 'proof command failure')
        facts = {}
        for label, view in (('outer', proof['outer']), ('inner', json.loads(proof['inner']['stdout']))):
            mapping = config['mapping'][label]
            require(view['file_identities'] == mapping['file_identities'], 'cgroup file mapping')
            require(view['cgroup_namespace'] == mapping['cgroup_namespace'], 'cgroup namespace')
            for path, text in mapping['fixed_files'].items():
                require(view['files'][path] == text, f'fixed resource mapping: {path}')
            files = view['files']
            events = dict(line.split() for line in files['/sys/fs/cgroup/memory.events'].splitlines())
            require(events == mapping['events_exact'], 'event counters changed')
            require(int(files['/sys/fs/cgroup/memory.swap.current']) == 0, 'swap nonzero')
            current = int(files['/sys/fs/cgroup/memory.current'])
            maximum = int(files['/sys/fs/cgroup/memory.max'])
            require(current + 6442450944 + 3221225472 <= 15032385536 < maximum, 'ancestor headroom')
            mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
            require(mem['MemAvailable'].strip().endswith('kB'), 'host memory units')
            require(int(mem['MemAvailable'].split()[0]) * 1024 > 9663676416, 'host headroom')
            facts[label] = {'current_bytes': current, 'events': events, 'swap_bytes': 0}
        proofs.append({'phase': phase, 'proof': pointer, 'started_ns': proof['started_at_unix_ns'],
                       'finished_ns': proof['finished_at_unix_ns'], 'facts': facts})
    require(0 <= end['runner_invocation_unix_ns'] - proofs[0]['started_ns'] <= 5000000000, 'initial proof age')
    require(0 <= proofs[1]['finished_ns'] - proofs[0]['started_ns'] <= 3720 * 1000000000, 'original proof horizon')
    return proofs


def row(index, config, config_path):
    aid = IDS[index]
    directory = Path(config['external_batch_directory']) / aid
    raw = W / 'docs/reports/reconstruction-working-set/raw' / aid
    boundary = load(directory / 'eligible-boundary.json')
    receipt = load(raw / 'receipt.json')
    child = load(raw / 'stdout.json')
    end = load(directory / 'observer-exit.json')
    require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW', 'boundary status')
    require(boundary['config_sha256'] == sha(config_path), 'boundary config identity')
    require(boundary['source_sha256'] == config['binder_sha256'], 'boundary source')
    expected_row = {'serial_index': index + 1, 'stage_id': 'growth256-summary',
                    'condition_id': 'growth256-summary-' + ('searched' if index >= 3 else 'supplied'),
                    'repetition': index % 3 + 1, 'profile': False, 'attempt_id': aid, 'launch_nonce': aid}
    require(boundary['row'] == expected_row and boundary['raw_path'] == str(raw), 'exact boundary row/raw path')
    require(boundary['table_sha256'] == '0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d', 'boundary table')
    require(boundary['method7'] == config['accepted_method7'], 'boundary method7')
    for key in ('stage_id', 'stage_admission', 'prior_stage_closures', 'candidate', 'material_hashes'):
        require(boundary[key] == config[key], f'boundary binding: {key}')
    require(len(boundary['raw_files']) == 11, 'exact11 raw files')
    require(raw.is_dir() and not raw.is_symlink(), 'raw directory aliased/missing')
    require({path.name for path in raw.iterdir()} == set(boundary['raw_files']), 'raw directory differs from boundary')
    for name, entry in boundary['raw_files'].items():
        require(Path(name).name == name, 'unsafe raw basename')
        require(type(entry['logical_bytes']) is int and 0 <= entry['logical_bytes'] <= 2965897216, 'raw logical extent')
        path = raw / name
        require(path.stat().st_size == entry['logical_bytes'] and sha(path) == entry['sha256'], f'raw bytes: {name}')
    require(receipt['protocol'] == config['receipt_protocol'], 'receipt protocol')
    require(receipt['child_outcome'] == 'finite_observation_pending_qualification' and receipt['material_identity_matches'] is True, 'receipt child/material outcome')
    require(receipt['status'] == 'complete_child_observed_pending_scientific_qualification', 'receipt status')
    require(receipt['signals'] == [] and receipt['wait_ownership_lost'] is False, 'signals/wait ownership')
    require(receipt['nonterminal_wait_events'] == [] and receipt['startup_parent_fds_closed'] is True, 'startup/wait disposition')
    require(type(receipt['startup_eof_observed']) is bool, 'startup EOF field')
    require(not any(key in receipt for key in ('stop_reason', 'cleanup_gap', 'postflight_gap', 'error_type')), 'receipt failure')
    terminal = receipt['terminal']
    require(terminal['pid'] == receipt['workload_pid'] == child['pid'], 'terminal PID')
    require(terminal['returncode'] == terminal['exit_code'] == terminal['wait_status_raw'] == 0, 'terminal exit')
    require(terminal['exited'] is True and terminal['signaled'] is False, 'terminal disposition')
    require(terminal['ru_maxrss_native_units'] == 'Linux KiB' and terminal['ru_maxrss_multiplier_to_bytes'] == 1024, 'native RSS scope')
    require(type(terminal['rusage_native']['ru_maxrss']) is int and terminal['rusage_native']['ru_maxrss'] > 0, 'usable native RSS value')
    require(terminal['kernel_reported_direct_child_high_water_bytes'] == terminal['rusage_native']['ru_maxrss'] * 1024, 'native RSS conversion')
    for key in ('candidate_before', 'candidate_after', 'candidate_final'):
        require(receipt[key] == config['candidate'], 'receipt candidate')
    for key in ('material_hashes_before', 'material_hashes_after', 'material_hashes_final'):
        require(receipt[key] == config['material_hashes'], 'receipt material')
    require(receipt['child_record_sha256'] == sha(raw / 'stdout.json'), 'child bytes')
    require(receipt['grant_sha256'] == sha(directory / 'grant.json'), 'grant bytes')
    require(boundary['raw_files']['grant.input']['sha256'] == receipt['grant_sha256'], 'raw grant input bytes')
    grant = load(directory / 'grant.json')
    for key, value in config['grant_fixed'].items():
        require(grant[key] == value, f'grant binding: {key}')
    for key in ('candidate', 'material_hashes'):
        require(grant[key] == config[key], 'grant source identity')
    require(grant['launch_nonce'] == grant['attempt_id'] == aid and grant['profile'] is False, 'grant attempt')
    require(child['protocol'] == config['child_protocol'] and child['status'] == 'finite_observation_pending_qualification', 'child protocol/status')
    require(child['finite_common_fields'] is True and child['material_identity_matches'] is True, 'finite/material child')
    search = index >= 3
    condition = 'growth256-summary-' + ('searched' if search else 'supplied')
    branches = [['searched' if search else 'known'] * 3]
    require(child['branches'] == branches and child['stages'] == [], 'actual branch/profile')
    require(boundary['fingerprints'] == {key: child[key] for key in ('input_sha256', 'common_output_sha256', 'public_result_sha256', 'branches')}, 'actual child/boundary fingerprints')
    spec = child['spec']
    require(spec['shape'] == [1, 3, 8, 256, 256] and spec['mode'] == 'summary', 'workload shape/mode')
    require(spec['search'] is search and spec['repetition'] == index % 3 + 1 and spec['profile'] is False, 'workload case')
    require(spec['launch']['nonce'] == receipt['launch']['nonce'] == aid, 'launch nonce')
    require(spec.get('case') is None, 'unexpected fixture case')
    require(receipt['interpreter']['resolved'] == config['python_resolved'] and receipt['session_ready']['pid'] == receipt['workload_pid'], 'interpreter/session')
    for key, value in config['expected_core'][condition].items():
        require(child['output_hashes'][key][:3] == [key, value['shape'], value['dtype']], 'actual core shape/dtype')
    snapshots = child['snapshots']
    require(snapshots['pre_call']['monotonic_ns'] <= child['call_start_monotonic_ns'] <= child['call_end_monotonic_ns'], 'call start ordering')
    require(child['call_end_monotonic_ns'] <= snapshots['call_end']['monotonic_ns'] <= snapshots['post_observation']['monotonic_ns'] <= terminal['reaped_monotonic_ns'], 'last snapshot ordering')
    require(child['elapsed_call_seconds'] == (child['call_end_monotonic_ns'] - child['call_start_monotonic_ns']) / 1e9, 'recorded call duration')
    require(end['returncode'] == 0 and end['overdue'] is False and end['wait_gaps'] == [], 'observer exit evidence')
    pre = metadata(directory / 'pre-metadata.json', config)
    post = metadata(directory / 'post-metadata.json', config)
    require(0 <= end['runner_invocation_unix_ns'] - pre['observed_at_unix_ns'] <= 60000000000, 'recorded pre-metadata invocation age')
    markers = [load(raw / 'spawn-intent.json')['observer_identity'], load(raw / 'owned-child.json')['child_identity']]
    fds = sorted(set(receipt['startup_fd_plan'].values()))
    expected = [{'pid': item['pid'], 'start_ticks': item['start_ticks'], 'boot_id': item['boot_id'], 'fds': fds} for item in markers]
    require([item['pid'] for item in expected] == [receipt['observer_pid'], receipt['workload_pid']], 'marker PIDs')
    require(all(type(item['pid']) is int and item['pid'] > 1 and type(item['start_ticks']) is int and item['start_ticks'] > 0 and item['boot_id'] == post['boot_id'] for item in expected), 'exact birth identities')
    absent_items(post, expected, False)
    proofs = resource_proofs(directory, config, end)
    gap = receipt.get('rss_terminal_confirmation')
    if gap is not None:
        require(gap['bound_seconds'] == 0.05 and gap['outcome'] == 'terminal_confirmed_with_visible_sampling_gap', 'gap outcome')
        require(gap['first_sample']['VmRSS_bytes'] is None and gap['first_sample']['monotonic_ns'] == gap['origin_monotonic_ns'], 'gap origin')
        require(0 <= gap['terminal_collected_monotonic_ns'] - gap['origin_monotonic_ns'] <= 50000000, 'gap bound')
    return {
        'attempt_id': aid, 'condition_id': condition, 'repetition': index % 3 + 1,
        'boundary': ref(directory / 'eligible-boundary.json'), 'receipt': ref(raw / 'receipt.json'),
        'child': ref(raw / 'stdout.json'), 'post_metadata': ref(directory / 'post-metadata.json'),
        'post_resource': proofs[1]['proof'], 'actual_config': ref(config_path),
        'branches': branches, 'fingerprints': boundary['fingerprints'], 'proofs': proofs,
        'terminal_native': terminal, 'terminal_direct_child_high_water_bytes': terminal['kernel_reported_direct_child_high_water_bytes'],
        'workflow_call_seconds': child['elapsed_call_seconds'], 'visible_terminal_gap': gap,
        'metadata_scope': {'external_ancestors': post['external_ancestors'], 'outside_campaign_processes': post['outside_campaign_processes']},
    }, expected, post, pre


def main():
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == RELEASE, 'exact ROOT release path and hash argv required')
    require(sha(RELEASE) == sys.argv[2], 'ROOT release hash')
    release = load(RELEASE)
    require(release['schema'] == 'ROOT-WS116-close-growth256-release-v1' and release['authorized'] is True, 'ROOT explicit authorization')
    require(release['stage_id'] == 'growth256-summary' and release['output'] == str(OUTPUT), 'release fixed stage/output')
    require(not OUTPUT.exists() and not OUTPUT.is_symlink(), 'closure output already exists')
    require(release['helper_sha256'] == sha(__file__), 'released helper source')
    require(release['controller_attestation']['path'] == str(ATTESTATION), 'exact attestation path')
    attestation = checked(release['controller_attestation'])
    require(attestation['schema'] == 'ROOT-WS116-controller-terminal-attestation-v1', 'attestation schema')
    require(attestation['controller_session'] == 94974 and attestation['actual_terminal_observed'] is True, 'actual94974 terminal evidence')
    require(attestation['exit_code'] == 0 and attestation['no_pending_proxy'] is True, 'controller/proxy still unresolved')
    require(attestation['authority'] == 'ROOT' and attestation['basis'] == 'actual_tool_terminal_receipt', 'ROOT terminal provenance')
    tool_receipt = checked(attestation['tool_receipt'])
    require(tool_receipt == attestation['tool_receipt_expected'], 'ROOT-bound actual tool receipt content')
    manifest = load(S / 'source-manifest.json')
    require(release['source_manifest'] == ref(S / 'source-manifest.json'), 'released manifest identity')
    for pointer in manifest['fixed_source_bindings']:
        require(sha(pointer['path']) == pointer['sha256'], 'fixed source binding changed')
    configs = []
    for path, digest in CONFIGS:
        require(sha(path) == digest, 'fixed config bytes')
        configs.append(load(path))
    first, rest = configs
    require(first['allowed_attempt_ids'] == IDS[:1] and rest['allowed_attempt_ids'] == IDS[1:], 'fixed six attempts')
    require(first['external_batch_directory'] == str(B / 'batch-row1-ea9117d-a2') and rest['external_batch_directory'] == str(B / 'batch-remaining5-ea9117d-a1'), 'fixed batch directories')
    require(first['prior_eligible'] == [] and first['continuation_authorized'] is False and rest['continuation_authorized'] is True, 'prefix continuation')
    require(rest['prior_eligible'] == manifest['retained_row1_boundary'], 'recorded row1 prefix')
    require(first['stage_admission'] == manifest['stage_admission'] and first['prior_stage_closures'] == manifest['prior_stage_closures'], 'fixed1f4/a4c2/0aff')
    old_row1 = checked(manifest['retained_row1_eligibility'])
    require(old_row1['schema'] == 'ROOT-WS116-growth256-row1-data-eligibility-v1' and old_row1['status'] == 'ROW1_ELIGIBLE_ALL_CURRENT_OWNERS_CLOSED', 'recorded107 row1 eligibility')
    require(old_row1['actual_config'] == ref(CONFIGS[0][0]) and old_row1['boundary'] == rest['prior_eligible'][0], 'recorded107 prefix/config')
    early_window = checked(manifest['retained_row1_window_closure'])
    require(early_window['window_closed_early'] is True and early_window['eligible_row1'] == manifest['retained_row1_eligibility'], 'recorded first window closure')
    for key in ('candidate', 'material_hashes', 'stage_admission', 'prior_stage_closures', 'binder_sha256', 'expected_core', 'accepted_method7', 'environment', 'tool_hashes'):
        require(first[key] == rest[key], f'same stage basis: {key}')
    require(len(first['material_hashes']) == 35 and first['material_hashes'] == manifest['material35'] and first['candidate'] == manifest['candidate'], 'EA35 candidate')
    require(checked(first['accepted_method7']) == first['method7_expected'], 'actual method acceptance')
    require(checked(first['environment']) == first['environment_expected'], 'actual environment binding')
    require(str((W / first['inner_python']).resolve()) == first['python_resolved'], 'actual inner interpreter path')
    for path, digest in first['material_hashes'].items():
        require(sha(W / path) == digest, 'actual35 source bytes')
    for key, arg in (('head', 'HEAD'), ('tree', 'HEAD^{tree}')):
        require(subprocess.check_output([first['git'], 'rev-parse', arg], cwd=W, text=True).strip() == first['candidate'][key], 'actual git candidate')
    require(subprocess.check_output([first['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b'', 'tracked working bytes changed')
    rows, owners = [], []
    for index in range(6):
        config_index = 0 if index == 0 else 1
        result, expected, post, pre = row(index, configs[config_index], CONFIGS[config_index][0])
        absent_items(pre, owners, False)
        require(not ({identity_key(item) for item in owners} & {identity_key(item) for item in expected}), 'repeated owned birth identity')
        owners.extend(expected)
        absent_items(post, owners, False)
        rows.append(result)
    require(len(owners) == 12, 'all12 identities')
    absent_items(post, owners, True)
    require(rows[0]['boundary'] == rest['prior_eligible'][0], 'actual retained first boundary')
    for key in ('receipt', 'child', 'post_metadata'):
        require(rows[0][key] == old_row1[key], 'recorded107 first-row file linkage')
    for group in (rows[:3], rows[3:]):
        require(all(item['fingerprints'] == group[0]['fingerprints'] for item in group), 'within-condition repeat fingerprints')
    closure = {
        'scope': 'WS116_ROOT_closed_prior_stage', 'stage_id': 'growth256-summary',
        'closed': True, 'historical_identity_facts_retained': True, 'unresolved_owners': [],
        'all12_currentstage_exact_identities_and_expected_FD_paths_absent': True,
        'exact_owned_identities': owners, 'candidate': first['candidate'], 'material_hashes': first['material_hashes'],
        'source_unchanged': True, 'raw_files_all_hash_verified': True,
        'repeat_fingerprints_match_within_condition': True, 'three_repeat_groups_complete': 2,
        'all_in_trial_event_counters_unchanged': True, 'oom_fields_and_swap_zero': True,
        'actual_event_baseline_max': int(first['mapping']['inner']['events_exact']['max']),
        'same_stage_admission': first['stage_admission'], 'prior_stage_closures': first['prior_stage_closures'],
        'first_config': ref(CONFIGS[0][0]), 'last_config': ref(CONFIGS[1][0]),
        'earlier_row1_window_closure': manifest['retained_row1_window_closure'],
        'retained_row1_eligibility': manifest['retained_row1_eligibility'],
        'last_post_metadata': rows[-1]['post_metadata'], 'rows': rows,
        'terminal_receipts': [item['receipt'] for item in rows],
        'eligible_boundaries': [item['boundary'] for item in rows],
        'final_controller_session': 94974, 'final_controller_exit_code': 0,
        'controller_terminal_attestation': release['controller_attestation'], 'ROOT_execution_release': ref(RELEASE),
        'no_scientific_report_acceptance': True, 'metering': 'unknown',
        'measurement_scope': 'Kernel-reported direct-child high-water through final exit; inherited/pre-exec/exec-transition retention unknown. No subtraction, aggregate, decomposition, ranking or benefit.',
        'context_scope': 'Recorded per-row proofs/metadata only; external ancestors unknown_unobservable, outside actors unknown_not_scanned; no present-day PID/FD/resource scan.',
        'next': 'No automatic full/profile/largest selection or release; ROOT owns future admission.',
        'closed_at_unix_ns': time.time_ns(),
    }
    with OUTPUT.open('x') as stream:
        json.dump(closure, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'closure': ref(OUTPUT)}, sort_keys=True))


if __name__ == '__main__':
    main()
