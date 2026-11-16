"""UNEXECUTED ROOT full256 searched rows2-3 preparer; no scientific launch.

Preserves exact stage admission and requires future ROOT-closed R1 evidence.
Only fixed git/metadata/capture commands after explicit preparation authority.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import time

S = Path('/workspace/work/campaign/evidence/116/growth256-full-searched-remaining2-source')
B = Path('/workspace/work/campaign/evidence/116/growth256-full-searched-first-readiness')
W = Path('/workspace/work/issue-116')
O = B / 'remaining2-preparation-a1'
BATCH = B / 'batch-remaining2-ea9117d-a1'
AUTH_INPUT = S / 'ROOT-preparation-authorization.json'
SUSPENSION_INPUT = S / 'ROOT-scheduler-suspension-input.json'
PREREQUISITES_INPUT = S / 'ROOT-closed-r1-prerequisites.json'
MANIFEST = S / 'source-manifest.json'
HOST_PYTHON = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
STAGE = 'largest-full-searched'
CID = 'growth256-full-searched'
IDS = [f'ws116-gp-l256-full-searched-r{rep}-u' for rep in (1, 2, 3)]
AUTHORIZED_R1_SHA = '5f1d5052d34c42bf0021987c862982b2660643f517a06b2e72a8c712edab9be3'
EVENTS = {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
OUTPUT_CREATED = False

def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 16777216, 'regular bounded JSON input required: ' + str(path))
    return json.loads(path.read_bytes())


def sha(path):
    # Original tool6 intentionally retains its recorded symlink path. Hash the
    # resolved file bytes, as the original preparers/binder do; do not edit tool6.
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def checked(pointer):
    require(sha(pointer['path']) == pointer['sha256'], 'pinned bytes changed: ' + pointer['path'])
    return load(pointer['path'])


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def fresh(timestamp, seconds):
    require(type(timestamp) is int and 0 <= time.time_ns() - timestamp <= seconds * 1000000000, 'stale/future recorded time')


def source_checks(c, manifest):
    for pointer in manifest['immutable_source_inputs']:
        require(sha(pointer['path']) == pointer['sha256'], 'immutable source/config changed: ' + pointer['path'])
    require(len(c) == 44 and c['authorized'] is False, 'exact disabled44-key config')
    require(len(c['material_hashes']) == 35 and len(c['expected_core']) == 28 and len(c['tool_hashes']) == 6, 'fixed35/core28/tool6')
    require(c['root'] == str(W) and c['container'] == 'simrecon-campaign-ubuntu' and c['inner_python'] == '.venv/bin/python', 'fixed execution context')
    require(c['candidate'] == manifest['candidate'], 'EA candidate')
    for name, digest in c['material_hashes'].items():
        require(sha(W / name) == digest, 'actual material changed: ' + name)
    for path, digest in c['tool_hashes'].items():
        require(sha(path) == digest, 'actual tool changed: ' + path)
    require(sha(HOST_PYTHON) == c['tool_hashes'][c['outer_python']], 'regular host interpreter binding')
    require(Path(HOST_PYTHON).is_file() and not Path(HOST_PYTHON).is_symlink(), 'regular host interpreter required')
    for key, arg in (('head', 'HEAD'), ('tree', 'HEAD^{tree}')):
        require(subprocess.check_output([c['git'], 'rev-parse', arg], cwd=W, text=True).strip() == c['candidate'][key], 'actual HEAD/tree changed')
    require(subprocess.check_output([c['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b'', 'tracked source changed')
    require(checked(c['accepted_method7']) == c['method7_expected'], 'method7 binding')
    require(checked(c['environment']) == c['environment_expected'], 'environment binding')
    require(str((W / c['inner_python']).resolve()) == c['python_resolved'], 'inner interpreter path')


def absent_pair(metadata, owners):
    require(len(metadata['owned_processes']) == 2, 'exact two current-stage R1 owners required')
    observed = {(item['expected']['pid'], item['expected']['start_ticks'], item['expected']['boot_id']): item
                for item in metadata['owned_processes']}
    require(len(observed) == 2, 'duplicate stored identity')
    for owner in owners:
        key = (owner['pid'], owner['start_ticks'], owner['boot_id'])
        require(key in observed and observed[key]['expected'] == owner, 'exact R1 birth/FD identity mismatch')
        item = observed[key]
        require(item['identity_state'] == 'absent' and set(item['fds']) == {str(fd) for fd in owner['fds']} and
                all(value['state'] == 'absent' for value in item['fds'].values()), 'R1 owner/FD not absent')


def closed_row1(prerequisites, base):
    require(prerequisites['schema'] == 'ROOT-WS116-searched-r1-continuation-prerequisites-v1' and prerequisites['authority'] == 'ROOT', 'ROOT prerequisite attestation')
    require(prerequisites['stage_id'] == STAGE and prerequisites['attempt_id'] == IDS[0], 'exact same-stage R1')
    require(prerequisites['controller_session'] == 17352 and prerequisites['actual_terminal_observed'] is True and prerequisites['controller_exit_code'] == 0 and prerequisites['no_pending_proxy'] is True, 'actual R1 controller not ROOT-closed')
    require(prerequisites['row1_eligible'] is True and prerequisites['old_window_closed'] is True, 'ROOT eligibility/window disposition missing')
    for name in ('ROOT_eligibility_evidence', 'ROOT_window_closure_evidence', 'ROOT_controller_terminal_evidence'):
        actual = checked(prerequisites[name])
        require(isinstance(actual, dict) and actual == prerequisites[name + '_expected'], 'ROOT-bound actual prerequisite evidence differs')
    config_pointer = prerequisites['authorized_row1_config']
    require(config_pointer['path'] == str(B / 'config-row1-AUTHORIZED.json') and config_pointer['sha256'] == AUTHORIZED_R1_SHA, 'exact canonical authorized searched R1 path/bytes')
    actual_config = checked(config_pointer)
    expected_config = copy.deepcopy(base)
    expected_config['authorized'] = True
    require(actual_config == expected_config, 'R1 authorization may differ from canonical PREPARED only by authorized flag')
    boundary_pointer = prerequisites['row1_boundary']
    first = B / 'batch-row1-ea9117d-a1' / IDS[0]
    require(boundary_pointer['path'] == str(first / 'eligible-boundary.json'), 'canonical R1 boundary path')
    boundary = checked(boundary_pointer)
    require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['config_sha256'] == AUTHORIZED_R1_SHA, 'actual eligible R1/config')
    row = {'serial_index': 1, 'stage_id': STAGE, 'condition_id': CID, 'repetition': 1, 'profile': False, 'attempt_id': IDS[0], 'launch_nonce': IDS[0]}
    require(boundary['row'] == row, 'actual8190 prefix row schema')
    for key in ('stage_id', 'stage_admission', 'prior_stage_closures', 'candidate', 'material_hashes'):
        require(boundary[key] == base[key], 'same actual stage basis: ' + key)
    require(boundary['source_sha256'] == base['binder_sha256'] and boundary['method7'] == base['accepted_method7'] and boundary['table_sha256'] == '0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d', 'prefix binder/table/method')
    raw = W / 'docs/reports/reconstruction-working-set/raw' / IDS[0]
    require(boundary['raw_path'] == str(raw), 'exact R1 raw path')
    def raw_record(name):
        entry = boundary['raw_files'][name]
        path = raw / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == entry['logical_bytes'], 'R1 required file shape')
        return checked({'path': str(path), 'sha256': entry['sha256']})
    receipt = raw_record('receipt.json')
    child = raw_record('stdout.json')
    require(receipt['protocol'] == base['receipt_protocol'] and receipt['status'] == 'complete_child_observed_pending_scientific_qualification' and receipt['child_outcome'] == 'finite_observation_pending_qualification', 'R1 receipt completeness')
    require(receipt['wait_ownership_lost'] is False and receipt['signals'] == [] and receipt['nonterminal_wait_events'] == [] and receipt['startup_parent_fds_closed'] is True, 'R1 lifecycle gap')
    require(not any(key in receipt for key in ('stop_reason', 'cleanup_gap', 'postflight_gap', 'error_type')), 'R1 receipt failure')
    terminal = receipt['terminal']
    require(terminal['pid'] == receipt['workload_pid'] == child['pid'] and terminal['exited'] is True and terminal['signaled'] is False and terminal['returncode'] == terminal['exit_code'] == terminal['wait_status_raw'] == 0, 'R1 exact terminal0')
    require(receipt['launch']['nonce'] == child['spec']['launch']['nonce'] == IDS[0], 'R1 nonce')
    require(receipt['child_record_sha256'] == boundary['raw_files']['stdout.json']['sha256'], 'R1 child bytes')
    for key in ('candidate_before', 'candidate_after', 'candidate_final'):
        require(receipt[key] == base['candidate'], 'R1 source candidate')
    for key in ('material_hashes_before', 'material_hashes_after', 'material_hashes_final'):
        require(receipt[key] == base['material_hashes'], 'R1 material basis')
    require(child['protocol'] == base['child_protocol'] and child['status'] == 'finite_observation_pending_qualification' and child['finite_common_fields'] is True and child['material_identity_matches'] is True, 'R1 finite/material record')
    require(child['spec']['shape'] == [1, 3, 8, 256, 256] and child['spec']['mode'] == 'full' and child['spec']['search'] is True and child['spec']['profile'] is False and child['spec']['repetition'] == 1 and child['branches'] == [['searched'] * 3] and child['stages'] == [], 'R1 actual case')
    require(boundary['fingerprints'] == {key: child[key] for key in ('input_sha256', 'common_output_sha256', 'public_result_sha256', 'branches')}, 'actual R1 fingerprints')
    for key, value in base['expected_core'][CID].items():
        require(child['output_hashes'][key][:3] == [key, value['shape'], value['dtype']], 'R1 actual core')
    markers = [raw_record('spawn-intent.json')['observer_identity'], raw_record('owned-child.json')['child_identity']]
    fds = sorted(set(receipt['startup_fd_plan'].values()))
    require(fds and all(type(fd) is int and fd >= 0 for fd in fds), 'literal startup FDs')
    owners = [{'pid': item['pid'], 'start_ticks': item['start_ticks'], 'boot_id': item['boot_id'], 'fds': fds} for item in markers]
    require([item['pid'] for item in owners] == [receipt['observer_pid'], receipt['workload_pid']], 'R1 marker PIDs')
    require(len({(item['pid'], item['start_ticks'], item['boot_id']) for item in owners}) == 2, 'two unique R1 birth identities')
    for owner in owners:
        require(type(owner['pid']) is int and owner['pid'] > 1 and type(owner['start_ticks']) is int and owner['start_ticks'] > 0 and owner['boot_id'] == base['metadata_expected']['boot_id'], 'complete recorded R1 birth identity')
    post_pointer = prerequisites['final_post_metadata']
    require(post_pointer['path'] == str(first / 'post-metadata.json'), 'exact R1 finalpost path')
    post = checked(post_pointer)
    require(post['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and post['source_sha256'] == base['metadata_source']['sha256'], 'actual fixed metadata schema/source')
    absent_pair(post, owners)
    receipt_pointer = {'path': str(raw / 'receipt.json'), 'sha256': boundary['raw_files']['receipt.json']['sha256']}
    return boundary_pointer, receipt_pointer, owners


def main():
    global OUTPUT_CREATED
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == AUTH_INPUT, 'exact future ROOT input path and SHA argv')
    require(sha(AUTH_INPUT) == sys.argv[2], 'ROOT preparation input hash')
    auth = load(AUTH_INPUT)
    require(auth['schema'] == 'ROOT-WS116-remaining2-searched-preparation-authorization-v1' and auth['authority'] == 'ROOT' and auth['authorized'] is True, 'ROOT explicit preparation authority')
    require(auth['stage_id'] == STAGE and auth['allowed_attempt_ids'] == IDS[1:] and auth['selected_largest_size'] == 256 and auth['prepare_continuation_authority'] is True and auth['scientific_execution_released'] is False, 'fixed prepare-only rows2-3')
    require(type(auth['window_seconds']) is int and 0 < auth['window_seconds'] <= 21600, 'ROOT finite reservation required; proposed3h, maximum6h')
    require(auth['helper_sha256'] == sha(__file__) and auth['source_manifest'] == ref(MANIFEST), 'ROOT exact source binding')
    require(auth['scheduler_suspension']['path'] == str(SUSPENSION_INPUT) and auth['closed_r1_prerequisites']['path'] == str(PREREQUISITES_INPUT), 'exact future ROOT input paths')
    suspension = checked(auth['scheduler_suspension'])
    require(suspension['schema'] == 'ROOT-WS116-remaining2-searched-suspension-input-v1' and suspension['authority'] == 'ROOT' and suspension['stage_id'] == STAGE, 'ROOT current suspension')
    require(suspension['campaign_work_suspended'] is True and suspension['known_active_campaign_runtimes'] == [] and suspension['unresolved_owners'] == [] and suspension['remains_suspended_through_prepared_window'] is True, 'known campaign work unresolved')
    require(suspension['outside_campaign_actors'] == 'unknown_not_scanned', 'outside actor scope')
    require(set(suspension['known_work_closure']) == {'113', '114', '116', '117', '118', '119', '120', 'root'} and all(isinstance(text, str) and text.strip() for text in suspension['known_work_closure'].values()), 'ROOT actual actor dispositions')
    fresh(auth['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not O.exists() and not O.is_symlink() and not BATCH.exists() and not BATCH.is_symlink(), 'new output/batch collision; no overwrite')
    for aid in IDS[1:]:
        raw = W / 'docs/reports/reconstruction-working-set/raw' / aid
        require(not raw.exists() and not raw.is_symlink(), 'continuation attempt collision')
    manifest = load(MANIFEST)
    base = checked(manifest['canonical_prepared_base'])
    source_checks(base, manifest)
    original = copy.deepcopy(base)
    require(base['stage_id'] == STAGE and base['selected_largest_size'] == 256 and base['allowed_attempt_ids'] == IDS[:1] and base['prior_eligible'] == [] and base['continuation_authorized'] is False, 'canonical singleton base')
    require(base['stage_admission'] == manifest['same_stage_admission'], 'critical unchanged d1b stage admission')
    admission = checked(base['stage_admission'])
    rows = [{'serial_index': rep, 'stage_id': STAGE, 'condition_id': CID, 'repetition': rep, 'profile': False, 'attempt_id': IDS[rep - 1], 'launch_nonce': IDS[rep - 1]} for rep in (1, 2, 3)]
    require(admission['stage_rows'] == rows and admission['selected_largest_size'] == 256 and admission['candidate'] == base['candidate'] and admission['material_hashes'] == base['material_hashes'], 'actual8190 stage schema')
    table = checked(manifest['table'])
    conditions = dict(table['conditions'])
    conditions.update({entry['condition']['id']: entry for entry in table['growth_proposals']})
    proposal = conditions[CID]['operating_proposal']
    worksheet = checked(manifest['full_worksheet'])
    require(proposal == worksheet['unchanged_operating_proposal'] == admission['operating_proposals'][CID], 'unchanged full proposal/deadline/horizon')
    core = {}
    for name, item in conditions.items():
        expected = item['expected_output']
        core[name] = {key: {'shape': expected[key]['shape'], 'dtype': '<f8'} for key in ('image', 'x_um', 'y_um', 'z_um', 'carriers_cyc_um')}
        for key in ('modulation', 'raw_modulation'):
            core[name][key] = {'shape': expected['modulation_and_raw']['shape'], 'dtype': '<c16'}
    require(core == base['expected_core'], 'exact unchanged core28')
    selection = checked(manifest['ROOT_selection'])
    require(selection['authority'] == 'ROOT' and selection['selected_largest_size'] == 256 and selection['candidate'] == base['candidate'] and selection['material_hashes'] == base['material_hashes'], 'same ROOT selection')
    require(base['prior_stage_closures'] == manifest['prior_stage_closures'] and base['matched_unprofiled'] == manifest['matched_unprofiled'], 'same prior stages/summary controls')
    for pointer in base['prior_stage_closures']:
        closure = checked(pointer)
        require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'stored prior-stage closure')
    prerequisites = checked(auth['closed_r1_prerequisites'])
    boundary_pointer, receipt_pointer, owners = closed_row1(prerequisites, base)
    fresh(suspension['observed_at_unix_ns'], 60)
    O.mkdir()
    OUTPUT_CREATED = True
    for path, name in ((AUTH_INPUT, 'ROOT-preparation-authorization.input.json'),
                       (SUSPENSION_INPUT, 'ROOT-scheduler-suspension.input.json'),
                       (PREREQUISITES_INPUT, 'ROOT-closed-r1-prerequisites.input.json')):
        with (O / name).open('xb') as stream:
            stream.write(path.read_bytes())
    c = copy.deepcopy(base)
    c.update(authorized=False, allowed_attempt_ids=IDS[1:], continuation_authorized=True, prior_eligible=[boundary_pointer], external_batch_directory=str(BATCH))
    request_path = O / 'metadata-request.json'
    save(request_path, {'disk_paths': [str(W), str(O)], 'owned_processes': owners})
    argv = [c['docker'], 'exec', '--user', '1000:1000', '-w', str(W)]
    for name in THREADS:
        argv += ['-e', name + '=1']
    argv += [c['container'], c['inner_python'], c['metadata_source']['path'], str(request_path)]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    save(O / 'metadata-command.json', {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'fixed metadata failure')
    m = json.loads(result.stdout)
    save(O / 'metadata.json', m)
    require(m['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and m['source_sha256'] == c['metadata_source']['sha256'] and m['request_sha256'] == sha(request_path), 'metadata source/request')
    for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits'):
        require(m[key] == base['metadata_expected'][key], 'fresh fixed metadata: ' + key)
    require(len(m['rlimits']) == 9 and m['uid'] == m['gid'] == 1000 and m['environment'] == {name: '1' for name in THREADS}, 'fresh Ubuntu context')
    require(m['external_ancestors'] == 'unknown_unobservable' and m['outside_campaign_processes'] == 'unknown_not_scanned', 'external unknown scopes')
    absent_pair(m, owners)
    require(set(m['disks']) == {str(W), str(O)}, 'two actual filesystems')
    for name in (str(W), str(O)):
        expected_name = str(W) if name == str(W) else base['external_batch_directory']
        disk = m['disks'][name]
        require({key: disk[key] for key in ('device', 'fsid', 'fragment_size')} == base['metadata_expected']['disk_identity'][expected_name], 'actual worktree/progress filesystem identity')
        require(disk['free_bytes'] >= proposal['disk_proposal_bytes'] and disk['free_inodes'] > 0, 'actual disk reserve')
    c['metadata_expected'] = {key: copy.deepcopy(m[key]) for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits')}
    c['metadata_expected']['disk_identity'] = {str(W): {key: m['disks'][str(W)][key] for key in ('device', 'fsid', 'fragment_size')}, str(BATCH): {key: m['disks'][str(O)][key] for key in ('device', 'fsid', 'fragment_size')}}
    result = subprocess.run([HOST_PYTHON, c['capture_helper']], capture_output=True, text=True, check=False)
    save(O / 'context-command.json', {'argv': [HOST_PYTHON, c['capture_helper']], 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'existing capture failed; no recapture')
    pointer = json.loads(result.stdout)
    pointer = {key: pointer[key] for key in ('path', 'sha256')}
    proof = checked(pointer)
    require(proof['schema'] == 'campaign-resource-domain-correspondence-v1' and proof['capture_source_sha256'] == c['tool_hashes'][c['capture_helper']] and proof['external_ancestors'] == 'unknown_unobservable', 'capture source/protocol/scope')
    require(proof['docker_inspect']['returncode'] == proof['inner']['returncode'] == 0 and proof['docker_inspect']['stdout'] == base['docker_inspect_stdout'], 'actual container/image/init context')
    inner = json.loads(proof['inner']['stdout'])
    require(proof['outer']['file_identities'] == inner['file_identities'], 'outer/inner correspondence')
    facts = {}
    for label, view in (('outer', proof['outer']), ('inner', inner)):
        mapping = c['mapping'][label]
        require(view['file_identities'] == mapping['file_identities'] and view['cgroup_namespace'] == mapping['cgroup_namespace'], 'actual exposed mapping')
        for path, value in mapping['fixed_files'].items():
            require(view['files'][path] == value, 'membership/mount/limit changed: ' + path)
        files = view['files']
        events = dict(line.split() for line in files['/sys/fs/cgroup/memory.events'].splitlines())
        current, maximum = int(files['/sys/fs/cgroup/memory.current']), int(files['/sys/fs/cgroup/memory.max'])
        swap = int(files['/sys/fs/cgroup/memory.swap.current'])
        mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
        require(mem['MemAvailable'].strip().endswith('kB'), 'host units')
        available = int(mem['MemAvailable'].split()[0]) * 1024
        require(events == EVENTS and swap == 0 and maximum == 17179869184, 'actual50340/OOM0/swap0/finite16GiB')
        require(current + 8589934592 + 4294967296 <= 16106127360 < maximum and available > 12884901888, 'full8+4<=15GiB/host>12GiB')
        mapping['events_exact'], mapping['swap_current_bytes'] = events, swap
        facts[label] = {'current_bytes': current, 'maximum_bytes': maximum, 'events': events, 'swap_bytes': swap, 'host_available_bytes': available}
        fresh(view['observed_at_unix_ns'], 5)
    source_checks(original, manifest)
    fresh(proof['started_at_unix_ns'], 5)
    fresh(m['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not BATCH.exists() and not BATCH.is_symlink(), 'batch appeared during preparation')
    preflight = {'schema': 'ROOT-WS116-remaining2-searched-context-preflight-v1', 'accepted_for_guarded_preparation': True, 'same_stage_admission': base['stage_admission'], 'prior_eligible': [boundary_pointer], 'ROOT_closed_r1_prerequisites': auth['closed_r1_prerequisites'], 'ROOT_selection': manifest['ROOT_selection'], 'full_source_worksheet': manifest['full_worksheet'], 'candidate': c['candidate'], 'material_hashes': c['material_hashes'], 'resource_context': pointer, 'resource_facts': facts, 'fresh_exact2_owner_metadata': ref(O / 'metadata.json'), 'operating_proposal': proposal, 'external_ancestors': 'unknown_unobservable', 'outside_campaign_actors': 'unknown_not_scanned', 'limits': 'Preparation only; binder retains original-stage-prefix/raw/controls and every-row context/end/ownership checks. No next stage, retry, recapture or cap relaxation.'}
    preflight_path = O / 'new-context-preflight.json'
    save(preflight_path, preflight)
    now = time.time_ns()
    window = {'starts_unix_ns': now, 'ends_unix_ns': now + auth['window_seconds'] * 1000000000}
    ack = {'schema': 'ROOT-campaign-stage-suspension-ACK-v1', 'stage_id': STAGE, 'window': window, 'observed_at_unix_ns': now, 'campaign_work_suspended': True, 'known_active_numerical_processes': [], 'unresolved_owners': [], 'outside_campaign_actors': 'unknown_not_scanned', 'prior_stage_closures': c['prior_stage_closures'], 'known_work_closure': suspension['known_work_closure'], 'preparation_suspension_input': auth['scheduler_suspension'], 'input_observed_at_unix_ns': suspension['observed_at_unix_ns'], 'scope': 'ROOT current standing suspension consumed now; outside actors unscanned; ACK is not grant authority.'}
    ackpath = O / 'scheduler-ACK.json'
    save(ackpath, ack)
    authority = {'schema': 'ROOT-WS116-remaining2-searched-authority-v1', 'authorized': True, 'execution_authorized': True, 'stage_id': STAGE, 'selected_largest_size': 256, 'allowed_attempt_ids': IDS[1:], 'window': window, 'candidate': c['candidate'], 'material_hashes': c['material_hashes'], 'same_stage_admission': base['stage_admission'], 'prior_eligible': [boundary_pointer], 'ROOT_preparation_authorization': ref(AUTH_INPUT), 'ROOT_closed_r1_prerequisites': auth['closed_r1_prerequisites'], 'new_preflight': ref(preflight_path), 'scheduler_ACK': ref(ackpath), 'final_config_gate': 'Config remains authorized:false; coordinator audit and separate ROOT exact scientific execution release still required.'}
    authpath = O / 'ROOT-authority.json'
    save(authpath, authority)
    ledger = {'scope': 'WS116_current_stage_scientific_observer_workload_processes', 'stage_id': STAGE, 'root_authority_sha256': sha(authpath), 'unresolved': [], 'closed_owned_processes': [{'attempt_id': IDS[0], 'receipt': receipt_pointer, 'identity': owner} for owner in owners], 'fresh_exact_owner_metadata': ref(O / 'metadata.json'), 'meaning': 'Only same-stage R1 exact observer/workload birth/FD identities, derived from its actual complete receipt/markers and finalpost metadata; freshly checked by fixed helper. Prior-stage identities never refreshed.'}
    ledgerpath = O / 'current-stage-ledger.json'
    save(ledgerpath, ledger)
    c.update(root_authority=ref(authpath), authority_expected=authority, scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath), window=window)
    c['grant_fixed']['exclusive_window'] = {'released': True, 'evidence': str(authpath), 'evidence_sha256': sha(authpath), 'scope': 'WS116 exact frozen growth/profile stage release'}
    c['conditional_rationale'] = 'ROOT prepares full searched remaining2 ONLY after actual R1 eligibility/controller17352/window closure and fresh source/current-owner/schedule/context checks. Exact d1b stage admission, prior4closed stages, nine-overlap source worksheet and all3searched-summary controls retained. Config authorized:false until separate coordinator/ROOT actual packet audit and exact scientific release. No repeat R1/profile/other stage, retry, recapture or cap relaxation. External actors/ancestors unknown.'
    require(len(c) == 44 and c['authorized'] is False and c['stage_admission'] == base['stage_admission'] and c['tool_hashes'] == base['tool_hashes'] and c['outer_python'] == base['outer_python'], 'unchanged44/tool6/same stage admission')
    cfgpath = O / 'config-remaining2-PREPARED.json'
    save(cfgpath, c)
    status = {'status': 'PREPARED_CONTINUATION_CONFIG_DISABLED', 'prepared_config': ref(cfgpath), 'same_stage_admission': c['stage_admission'], 'new_preflight': ref(preflight_path), 'authority': ref(authpath), 'ACK': ref(ackpath), 'ledger': ref(ledgerpath), 'window': window, 'execution_released': False}
    save(O / 'preparation-status.json', status)
    print(json.dumps(status, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = {'status': 'REFUSED_PREPARATION_NO_SCIENTIFIC_LAUNCH', 'error_type': type(error).__name__, 'reason': str(error), 'input_argv': sys.argv, 'observed_at_unix_ns': time.time_ns(), 'automatic_retry_or_recapture': False}
        if OUTPUT_CREATED and not (O / 'preparation-status.json').exists() and not (O / 'preparation-status.json').is_symlink():
            save(O / 'preparation-status.json', failure)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        raise


