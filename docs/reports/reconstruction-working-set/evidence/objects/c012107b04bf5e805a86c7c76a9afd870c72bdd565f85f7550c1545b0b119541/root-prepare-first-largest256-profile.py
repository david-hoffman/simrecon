"""UNEXECUTED ROOT largest256 summary-profile R1 preparer; no scientific launch.

Minimal e4a2 first-profile port; NEW ROOT profile decision and closed central6,
one fixed empty-owner metadata and one existing resource-domain capture.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import time

B = Path('/workspace/work/campaign/evidence/116/largest256-profiles-first-readiness')
P = Path('/workspace/work/campaign/evidence/116/largest256-profiles-first-source')
S = Path('/workspace/work/campaign/evidence/116/largest256-profiles-preparer-source')
W = Path('/workspace/work/issue-116')
OUTPUT_CREATED = False
AUTH_INPUT = S / 'ROOT-preparation-authorization.json'
SUSPENSION_INPUT = S / 'ROOT-scheduler-suspension-input.json'
PREREQUISITES_INPUT = S / 'ROOT-central-completion-and-largest-decision.json'
MANIFEST = S / 'source-manifest.json'
HOST_PYTHON = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
STAGE = 'largest-profiles'
CID = 'growth256-summary-searched'
IDS = [f'ws116-gp-l256-{mode}-searched-r{rep}-p' for mode in ('summary', 'full') for rep in (1, 2, 3)]
EVENTS = {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
OUTPUT_NAMES = (
    'ROOT-preparation-authorization.input.json', 'ROOT-scheduler-suspension.input.json', 'ROOT-prerequisites.input.json',
    'metadata-request.json', 'metadata-command.json', 'metadata.json', 'context-command.json',
    'case-preflight.json', 'stage-admission.json', 'scheduler-ACK.json', 'ROOT-authority.json',
    'current-stage-ledger.json', 'config-row1-PREPARED.json', 'preparation-status.json',
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


def central_prerequisites(pr, c, manifest):
    """Existing closure protocol plus explicit ROOT-bound unknown artifacts."""
    require(pr['schema'] == 'ROOT-WS116-largest256-profile-first-prerequisites-v1' and pr['authority'] == 'ROOT', 'ROOT prerequisite attestation')
    require(pr['stage_id'] == STAGE and pr['selected_largest_size'] == 256 and pr['allowed_attempt_ids'] == IDS[:1], 'NEW ROOT largest256 first-profile decision')
    require(pr['largest_profile_stage_admission_authorized'] is True and pr['old_central_profile_window_closed'] is True, 'NEW largest-profile decision/old central window not ROOT accepted')
    require(pr['actual_88772_terminal_exit0_no_proxy'] is True and pr['central_six_profile_rows_eligible'] is True, 'actual central controller/six-profile prerequisite')
    require(pr['canonical940_primary_six_rows_two_complete_groups_auditvalid'] is True and pr['independent_sixteen_triplets_match_primary'] is True and pr['ROOT_analysis_acceptance'] is True, 'ROOT actual primary/independent acceptance missing')
    for name in ('ROOT_largest_profile_stage_decision', 'old_central_window_evidence', 'primary_analysis_config',
                 'primary_analysis_result', 'primary_summary', 'independent_sixteen_triplets', 'coordinator_output_review', 'ROOT_post_source_audit', 'ROOT_acceptance_evidence'):
        if name in manifest['known_prerequisite_pins']:
            require(pr[name] == manifest['known_prerequisite_pins'][name], 'known closed prerequisite pin')
        actual = checked(pr[name])
        require(isinstance(actual, dict) and actual == pr[name + '_expected'], 'ROOT-bound actual JSON differs: ' + name)
    window_end = checked(pr['old_central_window_evidence'])
    require(window_end['schema'] == 'ROOT-WS116-central6-window-ended-v1' and window_end['authority'] == 'ROOT' and window_end['stage_id'] == 'central64-profiles' and window_end['closed_central_profile_window'] is True and window_end['controller88772_actual_terminal_exit0_no_proxy'] is True and window_end['all12_stored_birth_FD_facts_closed'] is True and window_end['no_active_stage_controller'] is True, 'actual closed central window')
    program = pr['canonical_primary_program']
    require(program == manifest['canonical_primary_program'], 'canonical source path and digest')
    require(program['sha256'] == '940f6e62cbf3bf817e7173bfa896f329658f1d4b5bb9ccca7228a51051b45f97' and sha(program['path']) == program['sha256'], 'actual canonical940 source identity')
    primary_config = checked(pr['primary_analysis_config'])
    require(primary_config['protocol'] == 'WS116-fixed-stage-report-v1' and primary_config['analysis_scope'] == 'one_fixed_stage' and primary_config['root_analysis_approved'] is True and primary_config['data_window_closed'] is True and primary_config['allow_partial_selection'] is False and primary_config['stage_id'] == 'central64-profiles' and primary_config['selected_largest_size'] is None, 'actual authorized closed central profile analysis configuration')
    summary = checked(pr['primary_summary'])
    require(summary['fixed_stage_descriptive_complete'] is True and summary['referenced_evidence_audit_valid'] is True and summary['analysis_success'] is True and summary['final_scientific_acceptance'] is False, 'actual940 completeness/reference audit/success scope')
    closure_pointer = pr['central_profile_stage_closure']
    require(closure_pointer == manifest['known_prerequisite_pins']['central_profile_stage_closure'] and window_end['closure'] == closure_pointer, 'exact central closure/window linkage')
    require(summary['stage_id'] == 'central64-profiles' and summary['selected_largest_size'] is None and [group['condition_id'] for group in summary['groups']] == ['central64-summary-searched', 'central64-full-searched'] and all(group['status'] == 'three_repeat_descriptive_only' and group['eligible_repetitions'] == [1, 2, 3] for group in summary['groups']), 'two exact descriptive groups')
    closure = checked(closure_pointer)
    require(closure == pr['central_profile_stage_closure_expected'], 'ROOT-bound actual central closure JSON')
    require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['stage_id'] == 'central64-profiles' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'actual whole central stage not closed')
    require(closure['candidate'] == c['candidate'] and closure['material_hashes'] == c['material_hashes'] and closure['source_unchanged'] is True and closure['raw_files_all_hash_verified'] is True, 'closed central source/raw audit')
    require(closure['all12_currentstage_exact_identities_and_expected_FD_paths_absent'] is True and closure['three_repeat_groups_complete'] == 2 and closure['repeat_fingerprints_match_within_condition'] is True, 'closed six-row/twelve-owner/two-group scope')
    require(closure['prior_stage_closures'] == c['prior_stage_closures'][:5] and closure['final_controller_session'] == 88772 and closure['final_controller_exit_code'] == 0, 'closed actual controller/prior stages')
    release = checked(closure['ROOT_execution_release'])
    closing_source = pr['central_closure_source']
    require(closing_source == manifest['central_closure_source'] and sha(closing_source['path']) == closing_source['sha256'] and release == pr['central_closure_release_expected'] and release['authorized'] is True and release['helper_sha256'] == closing_source['sha256'], 'ROOT actual406 central closure source/release binding')
    terminal = checked(closure['controller_terminal_attestation'])
    require(terminal['schema'] == 'ROOT-WS116-controller-terminal-attestation-v1' and terminal['authority'] == 'ROOT' and terminal['basis'] == 'actual_tool_terminal_receipt' and terminal['controller_session'] == 88772 and terminal['actual_terminal_observed'] is True and terminal['exit_code'] == 0 and terminal['no_pending_proxy'] is True, 'actual88772 tool-terminal attestation')
    require(terminal['tool_receipt'] == manifest['known_prerequisite_pins']['central_controller_tool_terminal'] and checked(terminal['tool_receipt']) == terminal['tool_receipt_expected'], 'actual tool-terminal JSON changed')
    rows = closure['rows']
    require(len(rows) == len(closure['terminal_receipts']) == len(closure['eligible_boundaries']) == 6, 'exact completed central six')
    selected = primary_config['stage_selection']
    require(len(selected) == 6 and [item['attempt_id'] for item in selected] == [item['attempt_id'] for item in rows] and all(item['phase'] == 'stage' for item in selected), 'primary selected exact six central profiles')
    require([item['boundary'] for item in selected] == closure['eligible_boundaries'], 'primary/closure boundary linkage')
    owners = closure['exact_owned_identities']
    require(len(owners) == 12, 'exact12 stored owner identities')
    keys = {(item['pid'], item['start_ticks'], item['boot_id']) for item in owners}
    require(len(keys) == 12, 'duplicate central owner birth identity')
    for index, item in enumerate(rows):
        mode, repetition = ('summary' if index < 3 else 'full'), index % 3 + 1
        aid, cid = f'ws116-gp-c64-{mode}-searched-r{repetition}-p', f'central64-{mode}-searched'
        require(item['attempt_id'] == aid and item['condition_id'] == cid and item['repetition'] == repetition, 'closure rows not exact central six profiles')
        require(item['boundary'] == closure['eligible_boundaries'][index] and item['receipt'] == closure['terminal_receipts'][index], 'closure row reference linkage')
        boundary, receipt = checked(item['boundary']), checked(item['receipt'])
        expected_row = {'serial_index': index + 1, 'stage_id': 'central64-profiles', 'condition_id': cid, 'repetition': repetition, 'profile': True, 'attempt_id': aid, 'launch_nonce': aid}
        require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['row'] == expected_row and boundary['stage_admission'] == closure['same_stage_admission'], 'actual8190 eligible central profile row/admission')
        require(boundary['candidate'] == c['candidate'] and boundary['material_hashes'] == c['material_hashes'] and boundary['source_sha256'] == c['binder_sha256'] and boundary['method7'] == c['accepted_method7'] and boundary['table_sha256'] == manifest['table']['sha256'], 'eligible central source basis')
        require(len(boundary['raw_files']) == 11 and boundary['raw_files']['receipt.json']['sha256'] == item['receipt']['sha256'], 'closed raw reference linkage')
        require(item['receipt']['path'] == boundary['raw_path'] + '/receipt.json', 'canonical receipt/raw reference')
        require(receipt['status'] == 'complete_child_observed_pending_scientific_qualification' and receipt['wait_ownership_lost'] is False and receipt['terminal']['returncode'] == 0 and receipt['terminal']['exited'] is True and receipt['terminal']['signaled'] is False and receipt['launch']['nonce'] == aid, 'complete central terminal ownership')
        require([owner['pid'] for owner in owners[2 * index:2 * index + 2]] == [receipt['observer_pid'], receipt['workload_pid']], 'closed identity/receipt PIDs')
    post = checked(closure['last_post_metadata'])
    require(post['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and post['source_sha256'] == c['metadata_source']['sha256'] and len(post['owned_processes']) == 12, 'actual final twelve-owner metadata')
    observed = {(item['expected']['pid'], item['expected']['start_ticks'], item['expected']['boot_id']): item for item in post['owned_processes']}
    require(set(observed) == keys and len(observed) == 12, 'final metadata exact12 coverage')
    for owner in owners:
        require(type(owner['pid']) is int and owner['pid'] > 1 and type(owner['start_ticks']) is int and owner['start_ticks'] > 0 and owner['boot_id'] == post['boot_id'] and isinstance(owner['fds'], list) and all(type(fd) is int and fd >= 0 for fd in owner['fds']), 'stored owner birth/FD identity')
        item = observed[(owner['pid'], owner['start_ticks'], owner['boot_id'])]
        require(item['expected'] == owner and item['identity_state'] == 'absent' and set(item['fds']) == {str(fd) for fd in owner['fds']} and all(value['state'] == 'absent' for value in item['fds'].values()), 'stored owner/FD closure ambiguity')
    require(c['prior_stage_closures'] == manifest['known_prior_closures'] + [None], 'only lastnull may be filled')
    c['prior_stage_closures'][-1] = closure_pointer
    refs = [pr[name] for name in ('central_profile_stage_closure', 'ROOT_largest_profile_stage_decision', 'primary_analysis_config', 'primary_analysis_result', 'primary_summary', 'independent_sixteen_triplets', 'ROOT_acceptance_evidence', 'old_central_window_evidence', 'coordinator_output_review', 'ROOT_post_source_audit')]
    return closure_pointer, refs


def main():
    global OUTPUT_CREATED
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == AUTH_INPUT and sha(AUTH_INPUT) == sys.argv[2], 'exact ROOT input path/hash')
    auth = load(AUTH_INPUT)
    require(auth['schema'] == 'ROOT-WS116-first-largest256-profile-preparation-authorization-v1' and auth['authority'] == 'ROOT' and auth['authorized'] is True, 'explicit ROOT preparation authority')
    require(auth['stage_id'] == STAGE and auth['selected_largest_size'] == 256 and auth['allowed_attempt_ids'] == IDS[:1], 'NEW ROOT largest256 singleton scope')
    require(auth['prepare_first_row_authority'] is True and auth['scientific_execution_released'] is False and auth['window_seconds'] == 14400, 'prepare-only4h operational reservation')
    require(auth['helper_sha256'] == sha(__file__) and auth['source_manifest'] == ref(MANIFEST), 'ROOT exact source release')
    require(auth['scheduler_suspension']['path'] == str(SUSPENSION_INPUT) and auth['central_completion_and_largest_decision']['path'] == str(PREREQUISITES_INPUT), 'exact future ROOT input paths')
    suspension = checked(auth['scheduler_suspension'])
    require(suspension['schema'] == 'ROOT-WS116-first-largest256-profile-suspension-input-v1' and suspension['authority'] == 'ROOT' and suspension['stage_id'] == STAGE, 'ROOT suspension scope')
    require(suspension['campaign_work_suspended'] is True and suspension['known_active_campaign_runtimes'] == [] and suspension['unresolved_owners'] == [] and suspension['new_stage_has_no_prior_scientific_launches'] is True and suspension['current_stage_owned_processes'] == [] and suspension['remains_suspended_through_prepared_window'] is True, 'actual ROOT no-prior-largest-profile-launch/owners and standing suspension')
    require(suspension['outside_campaign_actors'] == 'unknown_not_scanned', 'outside actor scope')
    require(set(suspension['known_work_closure']) == {'113', '114', '116', '117', '118', '119', '120', 'root'} and all(isinstance(text, str) and text.strip() for text in suspension['known_work_closure'].values()), 'actual known actor disposition')
    fresh(auth['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not B.exists() and not B.is_symlink(), 'new readiness directory must be absent')
    manifest = load(MANIFEST)
    c = load(P / 'config-row1-UNAUTHORIZED.json')
    original = copy.deepcopy(c)
    ad = load(P / 'stage-admission-DRAFT.json')
    authority = load(P / 'authority-DRAFT.json')
    ack = load(P / 'scheduler-ACK-DRAFT.json')
    ledger = load(P / 'currentstage-ledger-DRAFT.json')
    source_checks(c, manifest)
    require(c['stage_id'] == STAGE and c['selected_largest_size'] is None and c['allowed_attempt_ids'] == IDS[:1] and c['prior_eligible'] == [] and c['continuation_authorized'] is False and c['grant_fixed']['declared_growth_conditions'] == manifest['declared_growth_conditions'], 'unchanged disabled-null largest256 singleton source')
    batch = B / 'batch-row1-ea9117d-a1'
    raw = W / 'docs/reports/reconstruction-working-set/raw' / IDS[0]
    require(c['external_batch_directory'] == str(batch) and not batch.exists() and not batch.is_symlink() and not raw.exists() and not raw.is_symlink(), 'batch/attempt collision')
    table = checked(manifest['table'])
    conditions = dict(table['conditions'])
    conditions.update({entry['condition']['id']: entry for entry in table['growth_proposals']})
    worksheet = checked(manifest['worksheet'])
    require(worksheet['candidate'] == c['candidate'] and worksheet['stage']['id'] == STAGE and worksheet['stage']['source_recipe_size'] == 256 and worksheet['exact_fixture']['shape_TDZYX'] == [1, 3, 8, 256, 256] and worksheet['exact_fixture']['search_carriers'] is True, 'reviewed largest256 worksheet scope')
    rows, proposals = [], {}
    for mode in ('summary', 'full'):
        cid = f'growth256-{mode}-searched'
        condition = conditions[cid]
        require(condition['condition'] == {'id': cid, 'shape': [1, 3, 8, 256, 256], 'mode': mode, 'search': True}, 'fixed growth256 condition')
        proposal = copy.deepcopy(condition['operating_proposal'])
        # Exact frozen8190 profile transformation; no math/worker/cap change.
        proposal['deadline_seconds'] *= 2
        proposal['correspondence_maximum_age_seconds'] = proposal['deadline_seconds'] + 120
        proposal['disk_proposal_bytes'] = max(67108864, proposal['deadline_seconds'] * 100 * 8192 + 16777216)
        proposals[cid] = proposal
        for rep in (1, 2, 3):
            aid = f'ws116-gp-l256-{mode}-searched-r{rep}-p'
            rows.append({'serial_index': len(rows) + 1, 'stage_id': STAGE, 'condition_id': cid, 'repetition': rep, 'profile': True, 'attempt_id': aid, 'launch_nonce': aid})
    require(rows == ad['prospective_256']['stage_rows'] and proposals == ad['prospective_256']['operating_proposals'] == worksheet['profile_operating_proposals_literal'], 'exact8190 six profile recipes/proposals')
    require(ad['selected_largest_size'] is None and authority['selected_largest_size'] is None and ad['stage_rows'] is None and ad['operating_proposals'] is None, 'disabled runtime recipe remains null until NEW ROOT decision')
    require(c['grant_fixed']['declared_growth_conditions'] == ad['prospective_256']['declared_growth_conditions'] == manifest['declared_growth_conditions'], 'exact two declared growth256 conditions')
    proposal = proposals[CID]  # ONLY summary profile R1 operational preflight.
    core = {}
    for name, item in conditions.items():
        expected = item['expected_output']
        core[name] = {key: {'shape': expected[key]['shape'], 'dtype': '<f8'} for key in ('image', 'x_um', 'y_um', 'z_um', 'carriers_cyc_um')}
        for key in ('modulation', 'raw_modulation'):
            core[name][key] = {'shape': expected['modulation_and_raw']['shape'], 'dtype': '<c16'}
    require(core == c['expected_core'], 'unchanged table core28')
    prerequisites = checked(auth['central_completion_and_largest_decision'])
    closure_pointer, prior_data = central_prerequisites(prerequisites, c, manifest)
    c['selected_largest_size'] = 256  # Only after NEW ROOT stage decision/central completion.
    for value in (ad, authority, ack):
        value['prior_stage_closures'] = copy.deepcopy(c['prior_stage_closures'])
    ad['prior_data_refs'] = prior_data + [pair['boundary'] for pair in c['matched_unprofiled'].values()]
    for pointer in c['prior_stage_closures']:
        closure = checked(pointer)
        require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'stored prior-stage closure')
    require(c['prior_stage_closures'][:5] == manifest['known_prior_closures'] and c['prior_stage_closures'][5] == closure_pointer, 'only final central closure slot filled')
    require(c['matched_unprofiled'] == manifest['matched_unprofiled'] and set(c['matched_unprofiled']) == set(IDS), 'all six exact mode-specific controls')
    for row in rows:
        anchor = c['matched_unprofiled'][row['attempt_id']]
        boundary, config = checked(anchor['boundary']), checked(anchor['config'])
        require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['row']['condition_id'] == row['condition_id'] and boundary['row']['repetition'] == row['repetition'] and boundary['row']['profile'] is False, 'same-mode/same-rep unprofiled control')
        require(boundary['candidate'] == c['candidate'] and boundary['material_hashes'] == c['material_hashes'] and boundary['config_sha256'] == anchor['config']['sha256'] and boundary['source_sha256'] == config['binder_sha256'], 'control source/config binding')
        require(config['candidate'] == c['candidate'] and config['material_hashes'] == c['material_hashes'] and config['environment_expected'] == c['environment_expected'], 'same control software basis')
        require(set(boundary['fingerprints']) == {'input_sha256', 'common_output_sha256', 'public_result_sha256', 'branches'}, 'preserve public and common fingerprints; runtime8190 compares ALL same-mode profile fingerprints')
    baseline = checked(manifest['recorded_context_config'])
    for pointer in ad['prior_data_refs']:
        checked(pointer)
    fresh(suspension['observed_at_unix_ns'], 60)
    B.mkdir()
    OUTPUT_CREATED = True
    for path, name, digest in ((AUTH_INPUT, 'ROOT-preparation-authorization.input.json', sys.argv[2]), (SUSPENSION_INPUT, 'ROOT-scheduler-suspension.input.json', auth['scheduler_suspension']['sha256']), (PREREQUISITES_INPUT, 'ROOT-prerequisites.input.json', auth['central_completion_and_largest_decision']['sha256'])):
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == digest, 'ROOT input changed')
        with (B / name).open('xb') as stream:
            stream.write(data)
    request_path = B / 'metadata-request.json'
    save(request_path, {'disk_paths': [str(W), str(B)], 'owned_processes': []})
    argv = [c['docker'], 'exec', '--user', '1000:1000', '-w', str(W)]
    for name in THREADS:
        argv += ['-e', name + '=1']
    argv += [c['container'], c['inner_python'], c['metadata_source']['path'], str(request_path)]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    save(B / 'metadata-command.json', {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'fixed metadata command failed')
    m = json.loads(result.stdout)
    save(B / 'metadata.json', m)
    require(m['protocol'] == 'WS116-fixed-ubuntu-metadata-v1' and m['source_sha256'] == c['metadata_source']['sha256'] and m['request_sha256'] == sha(request_path), 'metadata source/request')
    for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits'):
        require(m[key] == baseline['metadata_expected'][key], 'actual fixed metadata: ' + key)
    require(len(m['rlimits']) == 9 and m['uid'] == m['gid'] == 1000 and m['owned_processes'] == [] and m['environment'] == {name: '1' for name in THREADS}, 'new-stage metadata identity/Root-attested empty request')
    require(m['external_ancestors'] == 'unknown_unobservable' and m['outside_campaign_processes'] == 'unknown_not_scanned' and set(m['disks']) == {str(W), str(B)}, 'metadata unknown scope/twoFS')
    for name in (str(W), str(B)):
        disk = m['disks'][name]
        expected_name = str(W) if name == str(W) else baseline['external_batch_directory']
        require({key: disk[key] for key in ('device', 'fsid', 'fragment_size')} == baseline['metadata_expected']['disk_identity'][expected_name], 'actual filesystem identity')
        require(disk['free_bytes'] >= proposal['disk_proposal_bytes'] and disk['free_inodes'] > 0, 'actual profile disk reserve')
    c['metadata_expected'] = {key: copy.deepcopy(m[key]) for key in ('uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits')}
    c['metadata_expected']['disk_identity'] = {str(W): {key: m['disks'][str(W)][key] for key in ('device', 'fsid', 'fragment_size')}, str(batch): {key: m['disks'][str(B)][key] for key in ('device', 'fsid', 'fragment_size')}}
    result = subprocess.run([HOST_PYTHON, c['capture_helper']], capture_output=True, text=True, check=False)
    save(B / 'context-command.json', {'argv': [HOST_PYTHON, c['capture_helper']], 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, 'existing capture failed; no recapture')
    pointer = json.loads(result.stdout)
    pointer = {key: pointer[key] for key in ('path', 'sha256')}
    proof = checked(pointer)
    require(proof['schema'] == 'campaign-resource-domain-correspondence-v1' and proof['capture_source_sha256'] == c['tool_hashes'][c['capture_helper']] and proof['external_ancestors'] == 'unknown_unobservable', 'capture protocol/source/scope')
    require(proof['docker_inspect']['returncode'] == proof['inner']['returncode'] == 0 and proof['docker_inspect']['stdout'] == baseline['docker_inspect_stdout'], 'actual container/image/init context')
    inner = json.loads(proof['inner']['stdout'])
    require(proof['outer']['file_identities'] == inner['file_identities'], 'outer/inner correspondence')
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
        require(events == EVENTS and swap == 0 and maximum == 17179869184, 'actual50340/OOM0/swap0/finite16GiB')
        require(current + proposal['process_stop_bytes'] + proposal['reserve_bytes'] <= proposal['proposed_each_visible_ancestor_stop_bytes'] < maximum and available > max(proposal['host_min_available_bytes'], proposal['process_stop_bytes'] + proposal['reserve_bytes']), 'first-summary256 stop6+reserve3<=ancestor14GiB/host>9GiB margin')
        mapping['events_exact'], mapping['swap_current_bytes'] = events, swap
        facts[label] = {'current_bytes': current, 'maximum_bytes': maximum, 'events': events, 'swap_bytes': swap, 'host_available_bytes': available}
        fresh(view['observed_at_unix_ns'], 5)
    source_checks(original, manifest)
    fresh(proof['started_at_unix_ns'], 5)
    fresh(m['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(not batch.exists() and not raw.exists(), 'batch/attempt appeared')
    c['expected_exposed'] = copy.deepcopy(baseline['expected_exposed'])
    c['docker_inspect_stdout'] = proof['docker_inspect']['stdout']
    case = {'schema': 'ROOT-WS116-largest256-profile-first-source-context-v1', 'accepted_for_guarded_preparation': True, 'selected_largest_size': 256, 'candidate': c['candidate'], 'material_hashes': c['material_hashes'], 'profile_source_worksheet': manifest['worksheet'], 'ROOT_central_completion_and_largest_decision': auth['central_completion_and_largest_decision'], 'resource_context': pointer, 'resource_facts': facts, 'metadata': ref(B / 'metadata.json'), 'operating_proposals': proposals, 'preflight_condition_id': CID, 'external_ancestors': 'unknown_unobservable', 'outside_campaign_actors': 'unknown_not_scanned', 'limits': 'Preparation only; no profile metrics/cost/isolated allocation or causal benefit; existing binder owns every-row guard.'}
    casepath = B / 'case-preflight.json'
    save(casepath, case)
    now = time.time_ns()
    window = {'starts_unix_ns': now, 'ends_unix_ns': now + auth['window_seconds'] * 1000000000}
    ack.update(schema='ROOT-campaign-stage-suspension-ACK-v1', window=window, observed_at_unix_ns=now, campaign_work_suspended=True, known_active_numerical_processes=[], unresolved_owners=[], known_work_closure=suspension['known_work_closure'], preparation_suspension_input=auth['scheduler_suspension'], input_observed_at_unix_ns=suspension['observed_at_unix_ns'], scope='ROOT standing suspension consumed now; outside actors unknown; ACK not grant authority')
    ack.pop('authorized', None)
    ackpath = B / 'scheduler-ACK.json'
    save(ackpath, ack)
    ad.update(schema='ROOT-WS116-largest256-profile-first-stage-admission-v1', execution_authorized=True, selected_largest_size=256, stage_rows=rows, operating_proposals=proposals, prerequisites_accepted=True, fresh_case_preflight_accepted=True, ROOT_largest_profiles_stage_decision=prerequisites['ROOT_largest_profile_stage_decision'], central_profiles_whole_stage_closure=closure_pointer, central_profiles_primary940_JSON=prerequisites['primary_summary'], central_profiles_independent16_JSON=prerequisites['independent_sixteen_triplets'], ROOT_central_profile_descriptive_acceptance=prerequisites['ROOT_acceptance_evidence'], fresh_case_preflight=ref(casepath))
    ad['required_prior_data'] = 'ROOT actual central6/12storedowners/controller88772/window closure, canonical940primary/independent16/descriptive acceptance and NEW ROOT largest-profile decision selecting256. Six same-mode256 controls retained; size provenance alone is not authority.'
    ad['selection_status'] = 'ROOT_SELECTED256_PROFILE_STAGE_PREPARED_CONFIG_DISABLED'
    ad.pop('prospective_256', None)  # Its exact rows/proposals are now the actual ROOT-selected bindings.
    adpath = B / 'stage-admission.json'
    save(adpath, ad)
    authority.update(schema='ROOT-WS116-largest256-profile-first-authority-v1', authorized=True, execution_authorized=True, selected_largest_size=256, ownership_resolved=True, preflight_accepted=True, prerequisites_accepted=True, status='PREPARED_SINGLETON_CONFIG_DISABLED', window=window, ROOT_largest_profiles_stage_decision=prerequisites['ROOT_largest_profile_stage_decision'], central_profiles_whole_stage_closure=closure_pointer, central_profiles_primary940_JSON=prerequisites['primary_summary'], central_profiles_independent16_JSON=prerequisites['independent_sixteen_triplets'], ROOT_central_profile_descriptive_acceptance=prerequisites['ROOT_acceptance_evidence'], root_preparation_authorization=ref(AUTH_INPUT), root_scheduler_ACK=ref(ackpath), fresh_case_preflight=ref(casepath), final_config_gate='Config authorized:false; coordinator/ROOT actual packet audit and separate exact scientific release still required.')
    authpath = B / 'ROOT-authority.json'
    save(authpath, authority)
    ledger.update(root_authority_sha256=sha(authpath), unresolved=[], closed_owned_processes=[], status='NEW_STAGE_ROOT_PREPARED_NO_PROFILE_LAUNCH', note='Empty new largest-profile ledger only from actual ROOT fresh no-prior-largest-profile-launch/owner attestation. Historical twelve central owners remain stored, never rescanned.')
    ledgerpath = B / 'current-stage-ledger.json'
    save(ledgerpath, ledger)
    c.update(authorized=False, selected_largest_size=256, root_authority=ref(authpath), authority_expected=authority, window=window, scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath), stage_admission=ref(adpath))
    c['grant_fixed'].update(numerical_release=True, campaign_ownership_resolved=True, declared_growth_conditions=manifest['declared_growth_conditions'])
    c['grant_fixed']['exclusive_window'] = {'released': True, 'evidence': str(authpath), 'evidence_sha256': sha(authpath), 'scope': 'WS116 exact frozen growth/profile stage release'}
    c['conditional_rationale'] = 'ROOT prepares largest256 summary searched PROFILE R1 ONLY after central6 whole closure/12storedowners/controller88772/window closure, canonical940primary/independent16/descriptive acceptance, NEW ROOT profile-stage decision selecting256 and fresh source/schedule/newstage-owner/context checks. Six same-mode controls/public+common equality retained; exact7200/7320/disk5915017216/mode256 caps unchanged. First-summary guard only; full caps retained but no full or remaining5 release. Configfalse until coordinator/ROOT actual audit and separate exact scientific release. No retry/recapture/cap relax, known profile cost or16GiB fit claim.'
    require(len(c) == 44 and c['selected_largest_size'] == 256 and c['grant_fixed']['declared_growth_conditions'] == manifest['declared_growth_conditions'] and c['tool_hashes'] == original['tool_hashes'] and c['outer_python'] == original['outer_python'], 'unchanged44/selected256/twoexactgrowth/tool6')
    cfgpath = B / 'config-row1-PREPARED.json'
    save(cfgpath, c)
    status = {'status': 'PREPARED_LARGEST256_PROFILE_CONFIG_DISABLED', 'prepared_config': ref(cfgpath), 'case_preflight': ref(casepath), 'stage_admission': ref(adpath), 'authority': ref(authpath), 'ACK': ref(ackpath), 'ledger': ref(ledgerpath), 'window': window, 'execution_released': False}
    save(B / 'preparation-status.json', status)
    print(json.dumps(status, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = {'status': 'REFUSED_PREPARATION_NO_PROFILE_LAUNCH', 'error_type': type(error).__name__, 'reason': str(error), 'input_argv': sys.argv, 'observed_at_unix_ns': time.time_ns(), 'automatic_retry_or_recapture': False}
        path = B / 'preparation-status.json'
        if OUTPUT_CREATED and not path.exists() and not path.is_symlink():
            save(path, failure)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        raise
