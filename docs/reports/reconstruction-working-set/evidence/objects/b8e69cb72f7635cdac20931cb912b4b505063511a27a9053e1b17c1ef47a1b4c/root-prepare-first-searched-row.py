"""UNEXECUTED ROOT preparer: one disabled full256 searched-r1 packet, no launch.

Consumes explicit hashed ROOT preparation/suspension inputs; runs only existing
git, fixed metadata and capture commands. No binder/workload, retry or recapture.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import time

B = Path('/workspace/work/campaign/evidence/116/growth256-full-searched-first-readiness')
P = Path('/workspace/work/campaign/evidence/116/growth256-full-searched-first-source')
S = Path('/workspace/work/campaign/evidence/116/growth256-full-searched-preparer-source')
OUTPUT_CREATED = False
E = B.parent
W = Path('/workspace/work/issue-116')
AUTH_INPUT = S / 'ROOT-preparation-authorization.json'
SUSPENSION_INPUT = S / 'ROOT-scheduler-suspension-input.json'
PREREQUISITES_INPUT = S / 'ROOT-supplied-completion-and-searched-decision.json'
MANIFEST = S / 'source-manifest.json'
HOST_PYTHON = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
CID = 'growth256-full-searched'
STAGE = 'largest-full-searched'
IDS = [f'ws116-gp-l256-full-searched-r{rep}-u' for rep in (1, 2, 3)]
EVENTS = {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
OUTPUT_NAMES = (
    'ROOT-preparation-authorization.input.json', 'ROOT-scheduler-suspension.input.json', 'ROOT-prerequisites.input.json',
    'root-full-preflight-metadata-request.json', 'root-full-preflight-metadata-command.json',
    'root-full-preflight-metadata.json', 'root-full-preparation-context-command.json',
    'root-full-case-and-resource-preflight.json', 'root-full-stage-admission.json',
    'root-full-scheduler-ACK-row1.json', 'root-full-authority-row1.json',
    'root-full-current-stage-ledger-row1.json', 'config-row1-PREPARED.json',
    'root-full-preparation-status.json',
)


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


def supplied_prerequisites(pr, c, manifest):
    """Existing closure protocol plus explicit ROOT-bound unknown artifacts."""
    require(pr['schema'] == 'ROOT-WS116-searched-first-prerequisites-v1' and pr['authority'] == 'ROOT', 'ROOT prerequisite attestation')
    require(pr['stage_id'] == STAGE and pr['selected_largest_size'] == 256 and pr['allowed_attempt_ids'] == IDS[:1], 'new searched-stage ROOT scope')
    require(pr['searched_stage_admission_authorized'] is True and pr['old_supplied_window_closed'] is True, 'new searched decision/old window not ROOT accepted')
    require(pr['actual_60678_terminal_exit0_no_proxy'] is True and pr['supplied_triple_eligible'] is True, 'actual supplied controller/triple prerequisite')
    require(pr['canonical940_primary_three_rows_one_complete_group_auditvalid'] is True and pr['independent_eight_triplets_match_primary'] is True and pr['ROOT_analysis_acceptance'] is True, 'ROOT actual primary/independent acceptance missing')
    for name in ('ROOT_searched_stage_decision', 'old_supplied_window_evidence', 'primary_analysis_config',
                 'primary_analysis_result', 'primary_summary', 'independent_eight_triplets', 'ROOT_acceptance_evidence'):
        actual = checked(pr[name])
        require(isinstance(actual, dict) and actual == pr[name + '_expected'], 'ROOT-bound actual JSON differs: ' + name)
    program = pr['canonical_primary_program']
    require(program['sha256'] == '940f6e62cbf3bf817e7173bfa896f329658f1d4b5bb9ccca7228a51051b45f97' and sha(program['path']) == program['sha256'], 'actual canonical940 source identity')
    primary_config = checked(pr['primary_analysis_config'])
    require(primary_config['protocol'] == 'WS116-fixed-stage-report-v1' and primary_config['analysis_scope'] == 'one_fixed_stage' and primary_config['root_analysis_approved'] is True and primary_config['data_window_closed'] is True and primary_config['allow_partial_selection'] is False and primary_config['stage_id'] == 'largest-full-supplied' and primary_config['selected_largest_size'] == 256, 'actual authorized closed full-supplied analysis configuration')
    summary = checked(pr['primary_summary'])
    require(summary['fixed_stage_descriptive_complete'] is True and summary['referenced_evidence_audit_valid'] is True and summary['analysis_success'] is True and summary['final_scientific_acceptance'] is False, 'actual940 completeness/reference audit/success scope')
    closure_pointer = pr['supplied_full_stage_closure']
    expected_path = '/workspace/work/campaign/evidence/116/growth256-full-supplied-first-readiness/root-fullsupplied256-stage-closed.json'
    require(closure_pointer['path'] == expected_path, 'canonical future full-supplied closure path')
    closure = checked(closure_pointer)
    require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['stage_id'] == 'largest-full-supplied' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'actual whole supplied stage not closed')
    require(closure['candidate'] == c['candidate'] and closure['material_hashes'] == c['material_hashes'] and closure['source_unchanged'] is True and closure['raw_files_all_hash_verified'] is True, 'closed supplied source/raw audit')
    require(closure['all6_currentstage_exact_identities_and_expected_FD_paths_absent'] is True and closure['three_repeat_groups_complete'] == 1 and closure['repeat_fingerprints_match_within_condition'] is True, 'closed three-row/six-owner scope')
    require(closure['prior_stage_closures'] == c['prior_stage_closures'][:3] and closure['final_controller_session'] == 60678 and closure['final_controller_exit_code'] == 0, 'closed actual controller/prior stages')
    release = checked(closure['ROOT_execution_release'])
    require(release['schema'] == 'ROOT-WS116-close-fullsupplied256-release-v1' and release['authorized'] is True and release['helper_sha256'] == manifest['supplied_closure_source']['sha256'], 'ROOT actual canonical closure source release')
    terminal = checked(closure['controller_terminal_attestation'])
    require(terminal['schema'] == 'ROOT-WS116-controller-terminal-attestation-v1' and terminal['authority'] == 'ROOT' and terminal['basis'] == 'actual_tool_terminal_receipt' and terminal['controller_session'] == 60678 and terminal['actual_terminal_observed'] is True and terminal['exit_code'] == 0 and terminal['no_pending_proxy'] is True, 'actual60678 tool-terminal attestation')
    require(checked(terminal['tool_receipt']) == terminal['tool_receipt_expected'], 'actual tool-terminal JSON changed')
    rows = closure['rows']
    require(len(rows) == len(closure['terminal_receipts']) == len(closure['eligible_boundaries']) == 3, 'exact completed supplied triple')
    selected = primary_config['stage_selection']
    require(len(selected) == 3 and [item['attempt_id'] for item in selected] == [item['attempt_id'] for item in rows] and all(item['phase'] == 'stage' for item in selected), 'primary selected exact three supplied rows')
    require([item['boundary'] for item in selected] == closure['eligible_boundaries'], 'primary/closure boundary linkage')
    owners = closure['exact_owned_identities']
    require(len(owners) == 6, 'exact6 stored owner identities')
    keys = {(item['pid'], item['start_ticks'], item['boot_id']) for item in owners}
    require(len(keys) == 6, 'duplicate supplied owner birth identity')
    for index, item in enumerate(rows):
        aid = f'ws116-gp-l256-full-supplied-r{index + 1}-u'
        require(item['attempt_id'] == aid and item['condition_id'] == 'growth256-full-supplied' and item['repetition'] == index + 1, 'closure rows not exact supplied triple')
        require(item['boundary'] == closure['eligible_boundaries'][index] and item['receipt'] == closure['terminal_receipts'][index], 'closure row reference linkage')
        boundary, receipt = checked(item['boundary']), checked(item['receipt'])
        expected_row = {'serial_index': index + 1, 'stage_id': 'largest-full-supplied', 'condition_id': 'growth256-full-supplied', 'repetition': index + 1, 'profile': False, 'attempt_id': aid, 'launch_nonce': aid}
        require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['row'] == expected_row and boundary['stage_admission'] == closure['same_stage_admission'], 'actual8190 eligible supplied row/admission')
        require(boundary['candidate'] == c['candidate'] and boundary['material_hashes'] == c['material_hashes'] and boundary['source_sha256'] == c['binder_sha256'] and boundary['method7'] == c['accepted_method7'] and boundary['table_sha256'] == manifest['table']['sha256'], 'eligible supplied source basis')
        require(len(boundary['raw_files']) == 11 and boundary['raw_files']['receipt.json']['sha256'] == item['receipt']['sha256'], 'closed raw reference linkage')
        require(item['receipt']['path'] == boundary['raw_path'] + '/receipt.json', 'canonical receipt/raw reference')
        require(receipt['status'] == 'complete_child_observed_pending_scientific_qualification' and receipt['wait_ownership_lost'] is False and receipt['terminal']['returncode'] == 0 and receipt['terminal']['exited'] is True and receipt['terminal']['signaled'] is False and receipt['launch']['nonce'] == aid, 'complete supplied terminal ownership')
        require([owner['pid'] for owner in owners[2 * index:2 * index + 2]] == [receipt['observer_pid'], receipt['workload_pid']], 'closed identity/receipt PIDs')
    post = checked(closure['last_post_metadata'])
    require(post['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and post['source_sha256'] == c['metadata_source']['sha256'] and len(post['owned_processes']) == 6, 'actual final six-owner metadata')
    observed = {(item['expected']['pid'], item['expected']['start_ticks'], item['expected']['boot_id']): item for item in post['owned_processes']}
    require(set(observed) == keys and len(observed) == 6, 'final metadata exact6 coverage')
    for owner in owners:
        require(type(owner['pid']) is int and owner['pid'] > 1 and type(owner['start_ticks']) is int and owner['start_ticks'] > 0 and owner['boot_id'] == post['boot_id'] and isinstance(owner['fds'], list) and all(type(fd) is int and fd >= 0 for fd in owner['fds']), 'stored owner birth/FD identity')
        item = observed[(owner['pid'], owner['start_ticks'], owner['boot_id'])]
        require(item['expected'] == owner and item['identity_state'] == 'absent' and set(item['fds']) == {str(fd) for fd in owner['fds']} and all(value['state'] == 'absent' for value in item['fds'].values()), 'stored owner/FD closure ambiguity')
    require(c['prior_stage_closures'] == manifest['known_prior_closures'] + [None], 'only lastnull may be filled')
    c['prior_stage_closures'][-1] = closure_pointer
    refs = [pr[name] for name in ('supplied_full_stage_closure', 'ROOT_searched_stage_decision', 'primary_analysis_config', 'primary_analysis_result', 'primary_summary', 'independent_eight_triplets', 'ROOT_acceptance_evidence', 'old_supplied_window_evidence')]
    return closure_pointer, refs


def main():
    global OUTPUT_CREATED
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == AUTH_INPUT, 'exact future ROOT input path+SHA argv required')
    require(sha(AUTH_INPUT) == sys.argv[2], 'ROOT preparation input hash')
    auth = load(AUTH_INPUT)
    require(auth['schema'] == 'ROOT-WS116-first-searched-preparation-authorization-v1' and auth['authority'] == 'ROOT' and auth['authorized'] is True, 'explicit ROOT preparation authority absent')
    require(auth['stage_id'] == STAGE and auth['allowed_attempt_ids'] == IDS[:1] and auth['selected_largest_size'] == 256, 'ROOT fixed singleton stage')
    require(auth['prepare_first_row_authority'] is True and auth['scientific_execution_released'] is False and auth['window_seconds'] == 7200, 'prepare-only2h protocol reservation')
    require(auth['helper_sha256'] == sha(__file__) and auth['source_manifest'] == ref(MANIFEST), 'ROOT exact source release')
    require(auth['scheduler_suspension']['path'] == str(SUSPENSION_INPUT), 'exact future scheduler input')
    suspension = checked(auth['scheduler_suspension'])
    require(suspension['schema'] == 'ROOT-WS116-first-searched-suspension-input-v1' and suspension['authority'] == 'ROOT', 'ROOT suspension input')
    require(suspension['stage_id'] == STAGE and suspension['campaign_work_suspended'] is True and suspension['known_active_campaign_runtimes'] == [] and suspension['unresolved_owners'] == [], 'known campaign runtimes unresolved')
    require(suspension['new_stage_has_no_prior_scientific_launches'] is True and suspension['current_stage_owned_processes'] == [], 'ROOT new-stage owner disposition required')
    require(suspension['remains_suspended_through_prepared_window'] is True, 'ROOT standing suspension for new window absent')
    require(suspension['outside_campaign_actors'] == 'unknown_not_scanned', 'external actor certainty invented')
    require(set(suspension['known_work_closure']) == {'113', '114', '116', '117', '118', '119', '120', 'root'} and all(isinstance(text, str) and text.strip() for text in suspension['known_work_closure'].values()), 'actual known actor disposition required')
    fresh(auth['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not B.exists() and not B.is_symlink(), 'new searched preparation directory must be absent; no overwrite')
    manifest = load(MANIFEST)
    c = load(P / 'config-row1-UNAUTHORIZED.json')
    original = copy.deepcopy(c)
    ad = load(P / 'stage-admission-DRAFT.json')
    authority = load(P / 'authority-DRAFT.json')
    ack = load(P / 'scheduler-ACK-DRAFT.json')
    ledger = load(P / 'currentstage-ledger-DRAFT.json')
    source_checks(c, manifest)
    require(c['stage_id'] == STAGE and c['allowed_attempt_ids'] == IDS[:1] and c['prior_eligible'] == [] and c['continuation_authorized'] is False, 'new-stage r1 only')
    batch = B / 'batch-row1-ea9117d-a1'
    require(c['external_batch_directory'] == str(batch) and not batch.exists() and not batch.is_symlink(), 'new batch must be absent')
    raw = W / 'docs/reports/reconstruction-working-set/raw' / IDS[0]
    require(not raw.exists() and not raw.is_symlink(), 'scientific attempt already exists')
    table = checked(manifest['table'])
    conditions = dict(table['conditions'])
    conditions.update({entry['condition']['id']: entry for entry in table['growth_proposals']})
    condition = conditions[CID]
    require(condition['condition'] == {'id': CID, 'shape': [1, 3, 8, 256, 256], 'mode': 'full', 'search': True}, 'fixed full source condition')
    proposal = condition['operating_proposal']
    worksheet = checked(manifest['full_worksheet'])
    require(worksheet['candidate'] == c['candidate'] and worksheet['exact_case']['mode'] == 'full' and worksheet['exact_case']['search'] is True and worksheet['exact_case']['shape_TDZYX'] == [1, 3, 8, 256, 256], 'source worksheet case')
    require(proposal == worksheet['unchanged_operating_proposal'] == ad['prospective_256']['operating_proposals'][CID], 'full caps may not change')
    require(worksheet['representation']['largest_named_single_backing_bytes'] == 63406080 and worksheet['unit_explicit_inventory']['searched_nine_overlap_table_literal']['NOT_one_allocation'] is True and worksheet['unit_explicit_inventory']['searched_nine_overlap_table_literal']['records'] == 9, 'full unit clarification')
    core = {}
    for name, item in conditions.items():
        expected = item['expected_output']
        core[name] = {key: {'shape': expected[key]['shape'], 'dtype': '<f8'} for key in ('image', 'x_um', 'y_um', 'z_um', 'carriers_cyc_um')}
        for key in ('modulation', 'raw_modulation'):
            core[name][key] = {'shape': expected['modulation_and_raw']['shape'], 'dtype': '<c16'}
    require(core == c['expected_core'], 'exact table core28')
    rows = [{'serial_index': rep, 'stage_id': STAGE, 'condition_id': CID, 'repetition': rep, 'profile': False, 'attempt_id': IDS[rep - 1], 'launch_nonce': IDS[rep - 1]} for rep in (1, 2, 3)]
    require(rows == ad['prospective_256']['stage_rows'], 'three fixed recipes')
    selection = checked(manifest['ROOT_selection'])
    require(selection['authority'] == 'ROOT' and selection['selected_largest_size'] == 256 and selection['candidate'] == c['candidate'] and selection['material_hashes'] == c['material_hashes'], 'actual ROOT selection')
    # Original0f795 next_proposed_stage is SUPPLIED. It is a size fact only.
    require(auth['supplied_completion_and_searched_decision']['path'] == str(PREREQUISITES_INPUT), 'exact future ROOT prerequisite path')
    prerequisites = checked(auth['supplied_completion_and_searched_decision'])
    closure_pointer, prior_data = supplied_prerequisites(prerequisites, c, manifest)
    ad['prior_stage_closures'] = copy.deepcopy(c['prior_stage_closures'])
    ad['prior_data_refs'] = prior_data
    authority['prior_stage_closures'] = copy.deepcopy(c['prior_stage_closures'])
    ack['prior_stage_closures'] = copy.deepcopy(c['prior_stage_closures'])
    for pointer in c['prior_stage_closures']:
        closure = checked(pointer)
        require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'stored prior closure incomplete')
    require(c['prior_stage_closures'][:3] == manifest['known_prior_closures'] and c['prior_stage_closures'][3] == closure_pointer, 'only last supplied-full closure slot changes')
    require(c['matched_unprofiled'] == manifest['matched_unprofiled'], 'fixed9da/78cc/75fd anchors')
    for index, anchor in enumerate(c['matched_unprofiled'].values()):
        boundary = checked(anchor['boundary'])
        config = checked(anchor['config'])
        require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['row']['condition_id'] == 'growth256-summary-searched' and boundary['row']['repetition'] == index + 1 and boundary['row']['profile'] is False, 'same-repetition searched summary anchor')
        require(boundary['candidate'] == c['candidate'] and boundary['material_hashes'] == c['material_hashes'] and boundary['config_sha256'] == anchor['config']['sha256'], 'anchor source/config')
        require(config['candidate'] == c['candidate'] and config['material_hashes'] == c['material_hashes'], 'anchor config source')
    baseline = checked(manifest['recorded_context_config'])
    for pointer in ad['prior_data_refs']:
        checked(pointer)  # Existing JSON evidence only; no historic PID refresh.
    fresh(suspension['observed_at_unix_ns'], 60)
    B.mkdir()
    OUTPUT_CREATED = True
    for path, name, digest in ((AUTH_INPUT, 'ROOT-preparation-authorization.input.json', sys.argv[2]), (SUSPENSION_INPUT, 'ROOT-scheduler-suspension.input.json', auth['scheduler_suspension']['sha256']), (PREREQUISITES_INPUT, 'ROOT-prerequisites.input.json', auth['supplied_completion_and_searched_decision']['sha256'])):
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == digest, 'ROOT input changed before snapshot')
        with (B / name).open('xb') as stream:
            stream.write(data)
    request_path = B / 'root-full-preflight-metadata-request.json'
    save(request_path, {'disk_paths': [str(W), str(B)], 'owned_processes': []})
    argv = [c['docker'], 'exec', '--user', '1000:1000', '-w', str(W)]
    for name in THREADS:
        argv += ['-e', name + '=1']
    argv += [c['container'], c['inner_python'], c['metadata_source']['path'], str(request_path)]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    save(B / 'root-full-preflight-metadata-command.json', {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'fixed metadata command failed')
    m = json.loads(result.stdout)
    save(B / 'root-full-preflight-metadata.json', m)
    require(m['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and m['source_sha256'] == c['metadata_source']['sha256'] and m['request_sha256'] == sha(request_path), 'metadata source/request')
    for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits'):
        require(m[key] == baseline['metadata_expected'][key], 'actual fixed metadata: ' + key)
    require(len(m['rlimits']) == 9 and m['uid'] == m['gid'] == 1000 and m['owned_processes'] == [] and m['environment'] == {name: '1' for name in THREADS}, 'new-stage metadata identity/empty request')
    require(m['external_ancestors'] == 'unknown_unobservable' and m['outside_campaign_processes'] == 'unknown_not_scanned', 'metadata unknown scopes')
    require(set(m['disks']) == {str(W), str(B)}, 'two actual filesystems')
    for name in (str(W), str(B)):
        disk = m['disks'][name]
        expected_name = str(W) if name == str(W) else baseline['external_batch_directory']
        require({key: disk[key] for key in ('device', 'fsid', 'fragment_size')} == baseline['metadata_expected']['disk_identity'][expected_name], 'actual prospective filesystem identity')
        require(disk['free_bytes'] >= proposal['disk_proposal_bytes'] and disk['free_inodes'] > 0, 'actual disk reserve')
    c['metadata_expected'] = {key: copy.deepcopy(m[key]) for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits')}
    c['metadata_expected']['disk_identity'] = {str(W): {key: m['disks'][str(W)][key] for key in ('device', 'fsid', 'fragment_size')}, str(batch): {key: m['disks'][str(B)][key] for key in ('device', 'fsid', 'fragment_size')}}
    result = subprocess.run([HOST_PYTHON, c['capture_helper']], capture_output=True, text=True, check=False)
    save(B / 'root-full-preparation-context-command.json', {'argv': [HOST_PYTHON, c['capture_helper']], 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'existing capture helper failed; no recapture')
    pointer = json.loads(result.stdout)
    pointer = {key: pointer[key] for key in ('path', 'sha256')}
    proof = checked(pointer)
    require(proof['schema'] == 'campaign-resource-domain-correspondence-v1' and proof['capture_source_sha256'] == c['tool_hashes'][c['capture_helper']], 'capture source/protocol')
    require(proof['external_ancestors'] == 'unknown_unobservable' and proof['docker_inspect']['returncode'] == proof['inner']['returncode'] == 0, 'exposed-domain scope')
    require(proof['docker_inspect']['stdout'] == baseline['docker_inspect_stdout'], 'actual container/image/init context changed')
    inner = json.loads(proof['inner']['stdout'])
    require(proof['outer']['file_identities'] == inner['file_identities'], 'outer/inner exposed object mismatch')
    c['mapping'] = copy.deepcopy(baseline['mapping'])
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
        require(events == EVENTS and swap == 0 and maximum == 17179869184, 'actual events50340/OOM0/swap0/finite16GiB required')
        require(current + 8589934592 + 4294967296 <= 16106127360 < maximum and available > 12884901888, 'full8+4<=15GiB/host>12GiB headroom fails')
        mapping['events_exact'], mapping['swap_current_bytes'] = events, swap
        facts[label] = {'current_bytes': current, 'maximum_bytes': maximum, 'events': events, 'swap_bytes': swap, 'host_available_bytes': available}
        fresh(view['observed_at_unix_ns'], 5)
    source_checks(original, manifest)
    fresh(proof['started_at_unix_ns'], 5)
    fresh(m['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not batch.exists() and not raw.exists(), 'batch/attempt appeared during preparation')
    c['expected_exposed'] = copy.deepcopy(baseline['expected_exposed'])
    c['docker_inspect_stdout'] = proof['docker_inspect']['stdout']
    case = {'schema': 'ROOT-WS116-first-searched256-source-and-context-preflight-v1', 'accepted_for_guarded_preparation': True, 'candidate': c['candidate'], 'material_hashes': c['material_hashes'], 'full_source_worksheet': manifest['full_worksheet'], 'ROOT_summary_size_selection': manifest['ROOT_selection'], 'ROOT_supplied_completion_and_searched_decision': auth['supplied_completion_and_searched_decision'], 'resource_context': pointer, 'resource_facts': facts, 'metadata': ref(B / 'root-full-preflight-metadata.json'), 'operating_proposal': proposal, 'external_ancestors': 'unknown_unobservable', 'outside_campaign_actors': 'unknown_not_scanned', 'limits': 'Current preparation checks only; full runtime/result/native cost unknown. Existing binder owns every-row fresh metadata/lastcapture and original-proof/end guards. No retry/recapture/nextstage.'}
    casepath = B / 'root-full-case-and-resource-preflight.json'
    save(casepath, case)
    now = time.time_ns()
    window = {'starts_unix_ns': now, 'ends_unix_ns': now + 7200 * 1000000000}
    ack.update(schema='ROOT-campaign-stage-suspension-ACK-v1', window=window, observed_at_unix_ns=now, campaign_work_suspended=True, known_active_numerical_processes=[], unresolved_owners=[], known_work_closure=suspension['known_work_closure'], preparation_suspension_input=auth['scheduler_suspension'], input_observed_at_unix_ns=suspension['observed_at_unix_ns'], ROOT_largest_selection=manifest['ROOT_selection'], scope='ROOT future standing suspension consumed now; no outside actor scan. ACK is not grant authority.')
    ack.pop('authorized', None)
    ackpath = B / 'root-full-scheduler-ACK-row1.json'
    save(ackpath, ack)
    ad.update(schema='ROOT-WS116-first-searched256-stage-admission-v1', execution_authorized=True, selected_largest_size=256, selection_status='ROOT_NEW_SEARCHED_DECISION_AFTER_ACCEPTED_SUPPLIED_COMPLETION', stage_rows=rows, operating_proposals={CID: proposal}, prerequisites_accepted=True, fresh_case_preflight_accepted=True, ROOT_largest_selection=manifest['ROOT_selection'], fresh_full_case_preflight=ref(casepath))
    ad['required_prior_data'] = 'ROOT actual completed supplied-full three eligible rows/whole-stage6owner/controller/window closure and canonical940primary+independent8triplets acceptance; new explicit ROOT searched-stage decision bound. Fresh searched source/context preparation only; final scientific report acceptance remains pending.'
    ad['ROOT_searched_stage_decision'] = prerequisites['ROOT_searched_stage_decision']
    ad['completed_supplied_full_triple'] = closure_pointer
    ad['supplied_full_primary_analysis_JSON'] = prerequisites['primary_summary']
    ad['supplied_full_independent_analysis_JSON'] = prerequisites['independent_eight_triplets']
    ad['supplied_full_owner_controller_window_closure'] = closure_pointer
    ad['source_selection_recommendation'] = 'Actual ROOT immutable selection reference bound above; this preparer makes no selection or feasibility extrapolation.'
    adpath = B / 'root-full-stage-admission.json'
    save(adpath, ad)
    authority.update(schema='ROOT-WS116-first-searched256-authority-v1', authorized=True, execution_authorized=True, selected_largest_size=256, ownership_resolved=True, preflight_accepted=True, prerequisites_accepted=True, status='PREPARED_SINGLETON_CONFIG_EXECUTION_STILL_DISABLED', window=window, ROOT_largest_selection=manifest['ROOT_selection'], root_preparation_authorization=ref(AUTH_INPUT), root_scheduler_ACK=ref(ackpath), fresh_case_preflight=ref(casepath), final_config_gate='Prepared config authorized:false. Separate coordinator file audit and ROOT final exact execution release required.')
    authority['scope'] = 'ROOT future authorized preparation of exact first-searched-r1 after actual supplied completion and NEW searched decision. Prepared config remains disabled; remaining2/profile and all other stages held.'
    authority['ROOT_searched_stage_decision'] = prerequisites['ROOT_searched_stage_decision']
    authority['completed_supplied_full_triple'] = closure_pointer
    authority['supplied_full_primary_analysis_JSON'] = prerequisites['primary_summary']
    authority['supplied_full_independent_analysis_JSON'] = prerequisites['independent_eight_triplets']
    authority['supplied_full_owner_controller_window_closure'] = closure_pointer
    authpath = B / 'root-full-authority-row1.json'
    save(authpath, authority)
    ledger.update(root_authority_sha256=sha(authpath), unresolved=[], closed_owned_processes=[], status='NEW_STAGE_ROOT_PREPARED_NO_SCIENTIFIC_LAUNCH', note='Empty new full-stage ledger is scoped to ROOT future suspension authority and no prior/new stage launch; historical prior-stage owners remain immutable, never rescanned.')
    ledgerpath = B / 'root-full-current-stage-ledger-row1.json'
    save(ledgerpath, ledger)
    c.update(authorized=False, selected_largest_size=256, root_authority=ref(authpath), authority_expected=authority, window=window, scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath), stage_admission=ref(adpath))
    c['grant_fixed'].update(numerical_release=True, campaign_ownership_resolved=True, declared_growth_conditions=[condition['condition']])
    c['grant_fixed']['exclusive_window'] = {'released': True, 'evidence': str(authpath), 'evidence_sha256': sha(authpath), 'scope': 'WS116 exact frozen growth/profile stage release'}
    c['conditional_rationale'] = 'ROOT prepares full searched r1 ONLY after actual supplied three-row/6owner/controller/window closure, canonical940+independent8triplets acceptance, NEW searched decision and fresh source/worksheet/schedule/metadata/domain checks. Original0f795 is size fact only. Config authorized:false until coordinator audit and separate ROOT exact scientific release; remaining2/profile held. No cap relaxation, retry/recapture or automatic nextstage; external actors/ancestors unknown.'
    require(len(c) == 44 and c['tool_hashes'] == original['tool_hashes'] and c['outer_python'] == original['outer_python'], 'unchanged44/tool6/config interpreter paths')
    cfgpath = B / 'config-row1-PREPARED.json'
    save(cfgpath, c)
    status = {'status': 'PREPARED_CONFIG_DISABLED', 'prepared_config': ref(cfgpath), 'case_preflight': ref(casepath), 'authority': ref(authpath), 'stage_admission': ref(adpath), 'ACK': ref(ackpath), 'ledger': ref(ledgerpath), 'window': window, 'execution_released': False}
    save(B / 'root-full-preparation-status.json', status)
    print(json.dumps(status, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = {'status': 'REFUSED_PREPARATION_NO_SCIENTIFIC_LAUNCH', 'error_type': type(error).__name__, 'reason': str(error), 'input_argv': sys.argv, 'observed_at_unix_ns': time.time_ns(), 'automatic_retry_or_recapture': False}
        path = B / 'root-full-preparation-status.json'
        if OUTPUT_CREATED and not path.exists() and not path.is_symlink():
            save(path, failure)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        raise

