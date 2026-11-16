"""UNEXECUTED ROOT preparer: one disabled full256 supplied-r1 packet, no launch.

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

B = Path('/workspace/work/campaign/evidence/116/growth256-full-supplied-first-readiness')
E = B.parent
W = Path('/workspace/work/issue-116')
AUTH_INPUT = B / 'ROOT-preparation-authorization.json'
SUSPENSION_INPUT = B / 'ROOT-scheduler-suspension-input.json'
MANIFEST = B / 'preparer-source-manifest.json'
HOST_PYTHON = '/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
CID = 'growth256-full-supplied'
STAGE = 'largest-full-supplied'
IDS = [f'ws116-gp-l256-full-supplied-r{rep}-u' for rep in (1, 2, 3)]
EVENTS = {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
OUTPUT_NAMES = (
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


def main():
    require(len(sys.argv) == 3 and Path(sys.argv[1]) == AUTH_INPUT, 'exact future ROOT input path+SHA argv required')
    require(sha(AUTH_INPUT) == sys.argv[2], 'ROOT preparation input hash')
    auth = load(AUTH_INPUT)
    require(auth['schema'] == 'ROOT-WS116-first-full-preparation-authorization-v1' and auth['authority'] == 'ROOT' and auth['authorized'] is True, 'explicit ROOT preparation authority absent')
    require(auth['stage_id'] == STAGE and auth['allowed_attempt_ids'] == IDS[:1] and auth['selected_largest_size'] == 256, 'ROOT fixed singleton stage')
    require(auth['prepare_first_row_authority'] is True and auth['scientific_execution_released'] is False and auth['window_seconds'] == 7200, 'prepare-only2h protocol reservation')
    require(auth['helper_sha256'] == sha(__file__) and auth['source_manifest'] == ref(MANIFEST), 'ROOT exact source release')
    require(auth['scheduler_suspension']['path'] == str(SUSPENSION_INPUT), 'exact future scheduler input')
    suspension = checked(auth['scheduler_suspension'])
    require(suspension['schema'] == 'ROOT-WS116-first-full-suspension-input-v1' and suspension['authority'] == 'ROOT', 'ROOT suspension input')
    require(suspension['stage_id'] == STAGE and suspension['campaign_work_suspended'] is True and suspension['known_active_campaign_runtimes'] == [] and suspension['unresolved_owners'] == [], 'known campaign runtimes unresolved')
    require(suspension['new_stage_has_no_prior_scientific_launches'] is True and suspension['current_stage_owned_processes'] == [], 'ROOT new-stage owner disposition required')
    require(suspension['remains_suspended_through_prepared_window'] is True, 'ROOT standing suspension for new window absent')
    require(suspension['outside_campaign_actors'] == 'unknown_not_scanned', 'external actor certainty invented')
    require(set(suspension['known_work_closure']) == {'113', '114', '116', '117', '118', '119', '120', 'root'} and all(isinstance(text, str) and text.strip() for text in suspension['known_work_closure'].values()), 'actual known actor disposition required')
    fresh(auth['observed_at_unix_ns'], 60)
    fresh(suspension['observed_at_unix_ns'], 60)
    require(all(not (B / name).exists() and not (B / name).is_symlink() for name in OUTPUT_NAMES), 'preparation output collision; no overwrite/retry')
    manifest = load(MANIFEST)
    c = load(B / 'config-row1-UNAUTHORIZED.json')
    original = copy.deepcopy(c)
    ad = load(B / 'stage-admission-DRAFT.json')
    authority = load(B / 'authority-DRAFT.json')
    ack = load(B / 'scheduler-ACK-DRAFT.json')
    ledger = load(B / 'currentstage-ledger-DRAFT.json')
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
    require(condition['condition'] == {'id': CID, 'shape': [1, 3, 8, 256, 256], 'mode': 'full', 'search': False}, 'fixed full source condition')
    proposal = condition['operating_proposal']
    worksheet = checked(manifest['full_worksheet'])
    require(worksheet['candidate'] == c['candidate'] and worksheet['exact_case']['mode'] == 'full' and worksheet['exact_case']['search'] is False and worksheet['exact_case']['shape_TDZYX'] == [1, 3, 8, 256, 256], 'source worksheet case')
    require(proposal == worksheet['unchanged_operating_proposal'] == ad['prospective_256']['operating_proposals'][CID], 'full caps may not change')
    require(worksheet['representation']['largest_named_single_backing_bytes'] == 63406080 and worksheet['unit_explicit_inventory']['six_overlap_records_aggregate']['NOT_one_allocation'] is True, 'full unit clarification')
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
    require(selection['next_proposed_stage'] == STAGE and selection['next_proposed_first_attempt'] == IDS[0], 'selected next source route')
    for pointer in c['prior_stage_closures']:
        closure = checked(pointer)
        require(closure['scope'] == 'WS116_ROOT_closed_prior_stage' and closure['closed'] is True and closure['historical_identity_facts_retained'] is True and closure['unresolved_owners'] == [], 'stored prior closure incomplete')
    require(c['prior_stage_closures'] == manifest['prior_stage_closures'], 'a4c2/0aff/79a immutable closures')
    require(c['matched_unprofiled'] == manifest['matched_unprofiled'], 'fixed9da/78cc/75fd anchors')
    for index, anchor in enumerate(c['matched_unprofiled'].values()):
        boundary = checked(anchor['boundary'])
        config = checked(anchor['config'])
        require(boundary['status'] == 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW' and boundary['row']['condition_id'] == 'growth256-summary-supplied' and boundary['row']['repetition'] == index + 1 and boundary['row']['profile'] is False, 'same-repetition summary anchor')
        require(boundary['candidate'] == c['candidate'] and boundary['material_hashes'] == c['material_hashes'] and boundary['config_sha256'] == anchor['config']['sha256'], 'anchor source/config')
        require(config['candidate'] == c['candidate'] and config['material_hashes'] == c['material_hashes'], 'anchor config source')
    baseline = checked(manifest['recorded_context_config'])
    for pointer in ad['prior_data_refs']:
        checked(pointer)  # Only immutable evidence, no historic PID refresh.
    fresh(suspension['observed_at_unix_ns'], 60)
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
    case = {'schema': 'ROOT-WS116-first-full256-source-and-context-preflight-v1', 'accepted_for_guarded_preparation': True, 'candidate': c['candidate'], 'material_hashes': c['material_hashes'], 'full_source_worksheet': manifest['full_worksheet'], 'ROOT_selection': manifest['ROOT_selection'], 'resource_context': pointer, 'resource_facts': facts, 'metadata': ref(B / 'root-full-preflight-metadata.json'), 'operating_proposal': proposal, 'external_ancestors': 'unknown_unobservable', 'outside_campaign_actors': 'unknown_not_scanned', 'limits': 'Current preparation checks only; full runtime/result/native cost unknown. Existing binder owns every-row fresh metadata/lastcapture and original-proof/end guards. No retry/recapture/nextstage.'}
    casepath = B / 'root-full-case-and-resource-preflight.json'
    save(casepath, case)
    now = time.time_ns()
    window = {'starts_unix_ns': now, 'ends_unix_ns': now + 7200 * 1000000000}
    ack.update(schema='ROOT-campaign-stage-suspension-ACK-v1', window=window, observed_at_unix_ns=now, campaign_work_suspended=True, known_active_numerical_processes=[], unresolved_owners=[], known_work_closure=suspension['known_work_closure'], preparation_suspension_input=auth['scheduler_suspension'], input_observed_at_unix_ns=suspension['observed_at_unix_ns'], ROOT_largest_selection=manifest['ROOT_selection'], scope='ROOT future standing suspension consumed now; no outside actor scan. ACK is not grant authority.')
    ack.pop('authorized', None)
    ackpath = B / 'root-full-scheduler-ACK-row1.json'
    save(ackpath, ack)
    ad.update(schema='ROOT-WS116-first-full256-stage-admission-v1', execution_authorized=True, selected_largest_size=256, selection_status='ROOT_SELECTED_COMPLETED_SUMMARY256_ONLY', stage_rows=rows, operating_proposals={CID: proposal}, prerequisites_accepted=True, fresh_case_preflight_accepted=True, ROOT_largest_selection=manifest['ROOT_selection'], fresh_full_case_preflight=ref(casepath))
    ad['required_prior_data'] = 'ROOT selected256 completed summary source/evidence and stored prior closures pinned; fresh full source/context checks passed for guarded packet preparation only. Final scientific report acceptance and actual full result remain pending.'
    ad['source_selection_recommendation'] = 'Actual ROOT immutable selection reference bound above; this preparer makes no selection or feasibility extrapolation.'
    adpath = B / 'root-full-stage-admission.json'
    save(adpath, ad)
    authority.update(schema='ROOT-WS116-first-full256-authority-v1', authorized=True, execution_authorized=True, selected_largest_size=256, ownership_resolved=True, preflight_accepted=True, prerequisites_accepted=True, status='PREPARED_SINGLETON_CONFIG_EXECUTION_STILL_DISABLED', window=window, ROOT_largest_selection=manifest['ROOT_selection'], root_preparation_authorization=ref(AUTH_INPUT), root_scheduler_ACK=ref(ackpath), fresh_case_preflight=ref(casepath), final_config_gate='Prepared config authorized:false. Separate coordinator file audit and ROOT final exact execution release required.')
    authority['scope'] = 'ROOT future authorized preparation of exact first-full-r1 authority only. Prepared config remains disabled; no scientific launch by this helper. Remaining2 and all other stages held.'
    authpath = B / 'root-full-authority-row1.json'
    save(authpath, authority)
    ledger.update(root_authority_sha256=sha(authpath), unresolved=[], closed_owned_processes=[], status='NEW_STAGE_ROOT_PREPARED_NO_SCIENTIFIC_LAUNCH', note='Empty new full-stage ledger is scoped to ROOT future suspension authority and no prior/new stage launch; historical prior-stage owners remain immutable, never rescanned.')
    ledgerpath = B / 'root-full-current-stage-ledger-row1.json'
    save(ledgerpath, ledger)
    c.update(authorized=False, selected_largest_size=256, root_authority=ref(authpath), authority_expected=authority, window=window, scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath), stage_admission=ref(adpath))
    c['grant_fixed'].update(numerical_release=True, campaign_ownership_resolved=True, declared_growth_conditions=[condition['condition']])
    c['grant_fixed']['exclusive_window'] = {'released': True, 'evidence': str(authpath), 'evidence_sha256': sha(authpath), 'scope': 'WS116 exact frozen growth/profile stage release'}
    c['conditional_rationale'] = 'ROOT prepares selected256 full supplied r1 only after actual source/worksheet/schedule/metadata/domain checks. Config remains authorized:false until coordinator audit and separate ROOT exact release. Remaining2/fullsearched/profiles held; no cap relaxation, recapture/retry or automatic nextstage. External actors/ancestors unknown.'
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
        failure = {'status': 'REFUSED_PREPARATION_NO_SCIENTIFIC_LAUNCH', 'error_type': type(error).__name__, 'reason': str(error), 'observed_at_unix_ns': time.time_ns(), 'automatic_retry_or_recapture': False}
        path = B / 'root-full-preparation-status.json'
        if not path.exists() and not path.is_symlink():
            save(path, failure)
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        raise
