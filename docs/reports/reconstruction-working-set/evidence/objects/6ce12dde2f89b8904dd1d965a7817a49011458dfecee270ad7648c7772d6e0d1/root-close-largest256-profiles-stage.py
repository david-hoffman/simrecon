"""UNEXECUTED fixed largest256 profile six-row closure audit; ROOT release only.

Three fixed read-only git calls and ONE fixed exact12-owner Ubuntu metadata call.
No resource capture, workload, global scan, signal/wait controller, retry or stats.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import time

B = Path('/workspace/work/campaign/evidence/116/largest256-profiles-first-readiness')
W = Path('/workspace/work/issue-116')
S = Path('/workspace/work/campaign/evidence/116/largest256-profiles-stage-closure-source')
OUTPUT = B / 'root-largest256-profiles-stage-closed.json'
AUDIT = S / 'execution-a1'
AUDIT_CREATED = False
HOST_PYTHON = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
OUTER_ALIAS = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python')
EVENTS = {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
RELEASE = S / 'ROOT-execution-release.json'
ATTESTATION = S / 'ROOT-final-controller-ended.json'
FIRST_CONFIG = (B / 'config-row1-AUTHORIZED.json', '446fc4718d6c0075d01a7c69c0deaaeb7e986ef42a92edba81ba1337905a79c6')
IDS = [f'ws116-gp-l256-{mode}-searched-r{rep}-p' for mode in ('summary', 'full') for rep in (1, 2, 3)]


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
        require(item['disks'][name]['free_bytes'] >= 5915017216 and item['disks'][name]['free_inodes'] > 0, 'recorded disk headroom')
    absent_items(item, request['owned_processes'], True)
    return item


def resource_proofs(directory, config, end, mode):
    stop, reserve, ancestor, host_minimum = {
        'summary': (6442450944, 3221225472, 15032385536, 9663676416),
        'full': (8589934592, 4294967296, 16106127360, 12884901888),
    }[mode]
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
            require(events == mapping['events_exact'] == EVENTS, 'exact50340 event counters changed')
            require(int(files['/sys/fs/cgroup/memory.swap.current']) == 0, 'swap nonzero')
            current = int(files['/sys/fs/cgroup/memory.current'])
            maximum = int(files['/sys/fs/cgroup/memory.max'])
            require(maximum == 17179869184 and current + stop + reserve <= ancestor < maximum, 'finite16GiB/mode-specific ancestor headroom')
            mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
            require(mem['MemAvailable'].strip().endswith('kB'), 'host memory units')
            require(int(mem['MemAvailable'].split()[0]) * 1024 > host_minimum, 'host headroom')
            facts[label] = {'current_bytes': current, 'events': events, 'swap_bytes': 0}
        proofs.append({'phase': phase, 'proof': pointer, 'started_ns': proof['started_at_unix_ns'],
                       'finished_ns': proof['finished_at_unix_ns'], 'facts': facts})
    require(0 <= end['runner_invocation_unix_ns'] - proofs[0]['started_ns'] <= 5000000000, 'initial proof age')
    require(0 <= proofs[1]['finished_ns'] - proofs[0]['started_ns'] <= 7320 * 1000000000, 'original proof horizon')
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
    mode = 'summary' if index < 3 else 'full'
    condition = f'growth256-{mode}-searched'
    expected_row = {'serial_index': index + 1, 'stage_id': 'largest-profiles',
                    'condition_id': condition,
                    'repetition': index % 3 + 1, 'profile': True, 'attempt_id': aid, 'launch_nonce': aid}
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
        require(type(entry['logical_bytes']) is int and 0 <= entry['logical_bytes'] <= 5915017216, 'raw logical extent')
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
    require(grant['launch_nonce'] == grant['attempt_id'] == aid and grant['profile'] is True, 'grant attempt')
    require(child['protocol'] == config['child_protocol'] and child['status'] == 'finite_observation_pending_qualification', 'child protocol/status')
    require(child['finite_common_fields'] is True and child['material_identity_matches'] is True, 'finite/material child')
    search = True
    branches = [['searched' if search else 'known'] * 3]
    require(child['branches'] == branches and isinstance(child['stages'], list) and len(child['stages']) == 10, 'actual branch/profile')
    require(boundary['fingerprints'] == {key: child[key] for key in ('input_sha256', 'common_output_sha256', 'public_result_sha256', 'branches')}, 'actual child/boundary fingerprints')
    anchor = config['matched_unprofiled'][aid]
    control, control_config = checked(anchor['boundary']), checked(anchor['config'])
    require(control['row']['condition_id'] == condition and control['row']['repetition'] == index % 3 + 1 and control['row']['profile'] is False, 'same-mode/same-rep control')
    require(control['candidate'] == config['candidate'] and control['material_hashes'] == config['material_hashes'] and control['config_sha256'] == anchor['config']['sha256'] and control_config['environment_expected'] == config['environment_expected'], 'control software/context bindings')
    require(control['fingerprints'] == boundary['fingerprints'], 'all4 same-mode input/common/public/branches profile control fingerprints')
    spec = child['spec']
    require(spec['shape'] == [1, 3, 8, 256, 256] and spec['mode'] == mode, 'workload shape/mode')
    require(spec['search'] is search and spec['repetition'] == index % 3 + 1 and spec['profile'] is True, 'workload case')
    require(spec['launch']['nonce'] == receipt['launch']['nonce'] == aid, 'launch nonce')
    require(spec.get('case') is None, 'unexpected fixture case')
    require(receipt['interpreter']['resolved'] == config['python_resolved'] and receipt['session_ready']['pid'] == receipt['workload_pid'], 'interpreter/session')
    for key, value in config['expected_core'][condition].items():
        require(child['output_hashes'][key][:3] == [key, value['shape'], value['dtype']], 'actual core shape/dtype')
    snapshots = child['snapshots']
    require(snapshots['pre_call']['monotonic_ns'] <= child['call_start_monotonic_ns'] <= child['call_end_monotonic_ns'], 'call start ordering')
    require(child['call_end_monotonic_ns'] <= snapshots['call_end']['monotonic_ns'] <= snapshots['post_observation']['monotonic_ns'] <= terminal['reaped_monotonic_ns'], 'last snapshot ordering')
    require(child['elapsed_call_seconds'] == (child['call_end_monotonic_ns'] - child['call_start_monotonic_ns']) / 1e9, 'recorded call duration')
    events = child['stages']
    expected_events = [(stage, time_index, edge) for stage, time_index in (('declaration', None), ('preparation', None), ('estimation', None), ('reconstruction', 0), ('result', None)) for edge in ('enter', 'exit')]
    require([(item['stage'], item['time_index'], item['edge']) for item in events] == expected_events, 'fixed10 scalar stage-event sequence')
    require(all(set(item) == {'stage', 'time_index', 'edge', 'monotonic_ns', 'ru_maxrss_native_KiB'} and type(item['monotonic_ns']) is int and type(item['ru_maxrss_native_KiB']) is int for item in events), 'scalar stage-event fields')
    require([item['monotonic_ns'] for item in events] == sorted(item['monotonic_ns'] for item in events) and [item['ru_maxrss_native_KiB'] for item in events] == sorted(item['ru_maxrss_native_KiB'] for item in events), 'ordered cumulative stage observations')
    require(child['call_start_monotonic_ns'] <= events[0]['monotonic_ns'] <= events[-1]['monotonic_ns'] <= child['call_end_monotonic_ns'] and 0 <= events[0]['ru_maxrss_native_KiB'] <= events[-1]['ru_maxrss_native_KiB'] <= terminal['rusage_native']['ru_maxrss'], 'stage observation bounds')
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
    proofs = resource_proofs(directory, config, end, mode)
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
        'branches': branches, 'mode': mode, 'profile_events': events, 'matched_unprofiled_control': anchor, 'fingerprints': boundary['fingerprints'], 'proofs': proofs,
        'terminal_native': terminal, 'terminal_direct_child_high_water_bytes': terminal['kernel_reported_direct_child_high_water_bytes'],
        'workflow_call_seconds': child['elapsed_call_seconds'], 'visible_terminal_gap': gap,
        'metadata_scope': {'external_ancestors': post['external_ancestors'], 'outside_campaign_processes': post['outside_campaign_processes']},
    }, expected, post, pre


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def tool_sha(path):
    # Only the known recorded tool6 outer-python alias may resolve.
    # All data, other tools and the resolved target retain strict regular checks.
    path = Path(path)
    if path == OUTER_ALIAS:
        require(path.is_symlink() and path.resolve() == HOST_PYTHON, 'recorded outer alias target changed')
        return sha(HOST_PYTHON)
    return sha(path)


def fresh_owner_absence(config, owners):
    """One exact12 query after final controller/root guards and stored closure."""
    require(len(owners) == len({identity_key(item) for item in owners}) == 12, 'exact12 unique request identities')
    request_path = AUDIT / 'fresh-owner-metadata-request.json'
    save(request_path, {'disk_paths': [str(W), str(AUDIT)], 'owned_processes': owners})
    argv = [config['docker'], 'exec', '--user', '1000:1000', '-w', str(W)]
    for name, value in config['environment_expected']['thread_controls'].items():
        argv += ['-e', name + '=' + value]
    argv += [config['container'], config['inner_python'], config['metadata_source']['path'], str(request_path)]
    started = time.time_ns()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=60)
    except subprocess.TimeoutExpired as error:
        def text(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value
        save(AUDIT / 'fresh-owner-metadata-command.json', {'argv': argv, 'returncode': None, 'status': 'TIMEOUT_HOLD_INNER_DISPOSITION_UNKNOWN', 'stdout': text(error.stdout), 'stderr': text(error.stderr), 'started_at_unix_ns': started, 'finished_at_unix_ns': time.time_ns(), 'retry': False})
        raise ValueError('fixed metadata timed out; no closure/retry, ROOT must resolve inner disposition') from error
    save(AUDIT / 'fresh-owner-metadata-command.json', {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr, 'started_at_unix_ns': started, 'finished_at_unix_ns': time.time_ns(), 'timeout_seconds': 60})
    require(result.returncode == 0 and len(result.stdout.encode('utf-8')) <= 16777216, 'fixed metadata failed or oversized')
    fresh_path = AUDIT / 'fresh-owner-metadata.json'
    save(fresh_path, json.loads(result.stdout))
    context = copy.deepcopy(config)
    disks = config['metadata_expected']['disk_identity']
    context['metadata_expected']['disk_identity'] = {str(W): disks[str(W)], str(AUDIT): disks[config['external_batch_directory']]}
    observed = metadata(fresh_path, context)
    require(started <= observed['observed_at_unix_ns'] <= time.time_ns(), 'fresh metadata chronology')
    absent_items(observed, owners, True)
    return {'metadata': ref(fresh_path), 'request': ref(request_path), 'command': ref(AUDIT / 'fresh-owner-metadata-command.json'), 'scope': 'One fixed exact12 birth/FD absence query after actual final controller reaped/pipes closed and all6/stored12 validated. Not measurement/native peak/global outside-actor or external-ancestor proof.'}


def main():
    global AUDIT_CREATED
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == RELEASE, 'exact ROOT release path and hash argv required')
    require(sha(RELEASE) == sys.argv[2], 'ROOT release hash')
    release = load(RELEASE)
    require(release['schema'] == 'ROOT-WS116-close-largest256-profiles-release-v1' and release['authorized'] is True, 'ROOT explicit authorization')
    require(release['stage_id'] == 'largest-profiles' and release['output'] == str(OUTPUT), 'release fixed stage/output')
    require(not OUTPUT.exists() and not OUTPUT.is_symlink(), 'closure output already exists')
    require(release['helper_sha256'] == sha(__file__), 'released helper source')
    require(release['one_fixed_exact12_metadata_authorized'] is True and release['audit_output_directory'] == str(AUDIT), 'explicit one-metadata effect/output authorization')
    require(release['controller_attestation']['path'] == str(ATTESTATION), 'exact attestation path')
    attestation = checked(release['controller_attestation'])
    require(attestation['schema'] == 'ROOT-WS116-controller-terminal-attestation-v1', 'attestation schema')
    session = release['final_controller_session']
    require(type(session) is int and session > 0 and session != 29012 and attestation['controller_session'] == session and attestation['actual_terminal_observed'] is True, 'actual future final-controller terminal; first29012 is not final')
    require(release['actual_final_controller_reaped'] is True and release['actual_final_controller_pipes_closed'] is True and release['all_six_rows_complete'] is True, 'ROOT actual final reap/pipes/all6 facts required')
    require(attestation['exit_code'] == 0 and attestation['no_pending_proxy'] is True, 'controller/proxy still unresolved')
    require(attestation['authority'] == 'ROOT' and attestation['basis'] == 'actual_tool_terminal_receipt', 'ROOT terminal provenance')
    tool_receipt = checked(attestation['tool_receipt'])
    require(tool_receipt == attestation['tool_receipt_expected'], 'ROOT-bound actual tool receipt content')
    manifest = load(S / 'source-manifest.json')
    require(release['source_manifest'] == ref(S / 'source-manifest.json'), 'released manifest identity')
    for pointer in manifest['fixed_source_bindings']:
        require(sha(pointer['path']) == pointer['sha256'], 'fixed source binding changed')
    require(not AUDIT.exists() and not AUDIT.is_symlink(), 'exclusive source-owned audit output exists')
    remaining_pointer = release['remaining_config']
    remaining_path = Path(remaining_pointer['path'])
    require(remaining_path.is_absolute() and remaining_path.resolve().is_relative_to(B.resolve()) and remaining_path != FIRST_CONFIG[0], 'remaining config must be exact own-stage file')
    first = checked({'path': str(FIRST_CONFIG[0]), 'sha256': FIRST_CONFIG[1]})
    rest = checked(remaining_pointer)
    require(rest == release['remaining_config_expected'], 'ROOT-bound exact actual remaining config JSON')
    configs = [first, rest]
    config_bindings = [FIRST_CONFIG, (remaining_path, remaining_pointer['sha256'])]
    AUDIT.mkdir()
    AUDIT_CREATED = True
    for path, name in ((RELEASE, 'release.input.json'), (ATTESTATION, 'controller-attestation.input.json')):
        with (AUDIT / name).open('xb') as stream:
            stream.write(path.read_bytes())
    save(AUDIT / 'audit-inputs.json', {'first_config': ref(FIRST_CONFIG[0]), 'remaining_config': remaining_pointer, 'source_manifest': ref(S / 'source-manifest.json'), 'terminal_attestation': release['controller_attestation'], 'final_controller_session': session})
    require(first['allowed_attempt_ids'] == IDS[:1] and rest['allowed_attempt_ids'] == IDS[1:], 'fixed six profile attempts')
    require(first['external_batch_directory'] == str(B / 'batch-row1-ea9117d-a1') and rest['external_batch_directory'] == str(B / 'batch-remaining5-ea9117d-a1'), 'fixed batch directories')
    require(first['selected_largest_size'] == rest['selected_largest_size'] == 256 and first['grant_fixed']['declared_growth_conditions'] == rest['grant_fixed']['declared_growth_conditions'] == manifest['declared_growth_conditions'], 'largest256/two exact growth conditions')
    require(first['prior_eligible'] == [] and first['continuation_authorized'] is False and rest['continuation_authorized'] is True, 'prefix continuation')
    require(rest['prior_eligible'] == manifest['retained_row1_boundary'], 'recorded row1 prefix')
    require(first['stage_admission'] == manifest['stage_admission'] and first['prior_stage_closures'] == manifest['prior_stage_closures'], 'same850/prior6closedstages')
    old_row1 = checked(manifest['retained_row1_eligibility'])
    require(old_row1['schema'] == 'ROOT-WS116-largest256-profile-r1-eligibility-v1' and old_row1['stage_id'] == 'largest-profiles' and old_row1['selected_largest_size'] == 256 and old_row1['controller_session'] == 29012 and old_row1['eligible_for_same_stage_continuation'] is True and old_row1['actual_controller_exit'] == 0 and old_row1['no_pending_proxy'] is True, 'recorded502 R1 eligibility only')
    require(sha(config_bindings[0][0]) == config_bindings[0][1] and old_row1['boundary'] == rest['prior_eligible'][0], 'recorded502 prefix/config')
    early_window = checked(manifest['retained_row1_window_closure'])
    require(early_window['closed_first_profile_window'] is True and early_window['controller29012_actual_terminal_exit0_no_proxy'] is True and early_window['eligibility'] == manifest['retained_row1_eligibility'] and early_window['no_active_stage_controller'] is True, 'recorded first window closure')
    for key in ('root', 'git', 'docker', 'outer_python', 'capture_helper', 'table_path', 'container', 'inner_python', 'python_resolved', 'stage_id', 'selected_largest_size', 'candidate', 'material_hashes', 'stage_admission', 'prior_stage_closures', 'binder_sha256', 'expected_core', 'accepted_method7', 'method7_expected', 'environment', 'environment_expected', 'tool_hashes', 'matched_unprofiled', 'metadata_source', 'metadata_max_age_seconds', 'receipt_protocol', 'child_protocol', 'expected_exposed', 'docker_inspect_stdout'):
        require(first[key] == rest[key], f'same stage basis: {key}')
    require(len(first) == len(rest) == 44 and first['authorized'] is True and rest['authorized'] is True and first['stage_id'] == 'largest-profiles', 'actual44-key authorized stage configs')
    require({key: value for key, value in first['grant_fixed'].items() if key != 'exclusive_window'} == {key: value for key, value in rest['grant_fixed'].items() if key != 'exclusive_window'}, 'same fixed grant fields except new authority window')
    admission = checked(first['stage_admission'])
    require(admission['selected_largest_size'] == 256 and admission['operating_proposals'] == manifest['profile_operating_proposals'] and [item['attempt_id'] for item in admission['stage_rows']] == IDS, 'same exact profile recipes/caps7200/7320/disk5915017216')
    require(len(first['material_hashes']) == 35 and first['material_hashes'] == manifest['material35'] and first['candidate'] == manifest['candidate'], 'EA35 candidate')
    require(checked(first['accepted_method7']) == first['method7_expected'], 'actual method acceptance')
    require(checked(first['environment']) == first['environment_expected'], 'actual environment binding')
    require(str((W / first['inner_python']).resolve()) == first['python_resolved'], 'actual inner interpreter path')
    require(first['tool_hashes'] == manifest['tool6'], 'unchanged original tool6 map')
    for path, digest in first['tool_hashes'].items():
        require(tool_sha(path) == digest, 'actual tool6 bytes; resolved outer alias only')
    for path, digest in first['material_hashes'].items():
        require(sha(W / path) == digest, 'actual35 source bytes')
    for key, arg in (('head', 'HEAD'), ('tree', 'HEAD^{tree}')):
        require(subprocess.check_output([first['git'], 'rev-parse', arg], cwd=W, text=True).strip() == first['candidate'][key], 'actual git candidate')
    require(subprocess.check_output([first['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b'', 'tracked working bytes changed')
    rows, owners = [], []
    for index in range(6):
        config_index = 0 if index == 0 else 1
        result, expected, post, pre = row(index, configs[config_index], config_bindings[config_index][0])
        absent_items(pre, owners, False)
        require(not ({identity_key(item) for item in owners} & {identity_key(item) for item in expected}), 'repeated owned birth identity')
        owners.extend(expected)
        absent_items(post, owners, False)
        rows.append(result)
    require(len(owners) == 12, 'all12 identities')
    absent_items(post, owners, True)
    require(rows[0]['boundary'] == rest['prior_eligible'][0], 'actual retained first boundary')
    require(rows[0]['post_metadata'] == old_row1['final_post_metadata'], 'recorded502 first-row metadata linkage')
    require(owners[:2] == old_row1['exact_owned_processes'] and rows[0]['receipt'] == old_row1['receipt'], 'recorded R1 exact2 birthFD/receipt linkage')
    for group in (rows[:3], rows[3:]):
        require(all(item['fingerprints'] == group[0]['fingerprints'] for item in group), 'within-condition repeat fingerprints')
    fresh_absence = fresh_owner_absence(rest, owners)  # Sole new effect, after all6/stored12 and ROOT final reap/pipes facts.
    closure = {
        'scope': 'WS116_ROOT_closed_prior_stage', 'stage_id': 'largest-profiles',
        'closed': True, 'historical_identity_facts_retained': True, 'unresolved_owners': [],
        'all12_currentstage_exact_identities_and_expected_FD_paths_absent': True,
        'exact_owned_identities': owners, 'candidate': first['candidate'], 'material_hashes': first['material_hashes'],
        'source_unchanged': True, 'raw_files_all_hash_verified': True,
        'repeat_fingerprints_match_within_condition': True, 'three_repeat_groups_complete': 2,
        'all_in_trial_event_counters_unchanged': True, 'oom_fields_and_swap_zero': True,
        'actual_event_baseline_max': int(first['mapping']['inner']['events_exact']['max']),
        'same_stage_admission': first['stage_admission'], 'prior_stage_closures': first['prior_stage_closures'],
        'first_config': ref(config_bindings[0][0]), 'last_config': ref(config_bindings[1][0]),
        'earlier_row1_window_closure': manifest['retained_row1_window_closure'],
        'retained_row1_eligibility': manifest['retained_row1_eligibility'],
        'last_post_metadata': rows[-1]['post_metadata'], 'rows': rows,
        'terminal_receipts': [item['receipt'] for item in rows],
        'eligible_boundaries': [item['boundary'] for item in rows],
        'final_controller_session': session, 'final_controller_exit_code': 0,
        'controller_terminal_attestation': release['controller_attestation'], 'ROOT_execution_release': ref(RELEASE),
        'no_scientific_report_acceptance': True, 'metering': 'unknown',
        'measurement_scope': 'Kernel-reported direct-child high-water through final exit; inherited/pre-exec/exec-transition retention unknown. Profile events are cumulative/time observations including perturbation, not incremental allocation or isolated cost. No subtraction, aggregate, decomposition, ranking or benefit.',
        'fresh_post_controller_owner_absence': fresh_absence,
        'context_scope': 'Recorded per-row proofs/metadata plus one exact12-target fixed metadata query; external ancestors unknown_unobservable, outside actors unknown_not_scanned. No new resource capture, global scan or native/peak measurement.',
        'required_ROOT_post_success': 'ROOT must recheck35/HEADtree/tracked/FULLexpectedrawinventory/helper-manifest and explicitly end whole window before any next admission; helper does not implement that later postcheck.',
        'next': 'No automatic next stage/release; final report acceptance pending.',
        'closed_at_unix_ns': time.time_ns(),
    }
    with OUTPUT.open('x') as stream:
        json.dump(closure, stream, indent=2, sort_keys=True)
        stream.write('\n')
    save(AUDIT / 'status.json', {'status': 'CLOSED_ROWS_AND_FRESH_EXACT12_ABSENCE_ROOT_POSTCHECK_WINDOW_END_PENDING', 'closure': ref(OUTPUT), 'fresh_owner_absence': fresh_absence, 'scientific_acceptance': False})
    print(json.dumps({'closure': ref(OUTPUT), 'audit_status': ref(AUDIT / 'status.json')}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = {'status': 'CLOSURE_AUDIT_FAILED_HOLD_NO_RETRY', 'error_type': type(error).__name__, 'reason': str(error), 'input_argv': sys.argv, 'observed_at_unix_ns': time.time_ns(), 'automatic_retry': False}
        if AUDIT_CREATED and not (AUDIT / 'status.json').exists() and not (AUDIT / 'status.json').is_symlink():
            save(AUDIT / 'status.json', failure)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        raise
