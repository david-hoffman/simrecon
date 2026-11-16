"""ROOT's concrete first256 packet assembly; no workload invocation."""
from pathlib import Path
import hashlib
import json
import subprocess
import time

B = Path('/workspace/work/campaign/evidence/116/growth256-first-readiness')
E = B.parent
W = Path('/workspace/work/issue-116')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def ref(path):
    return {'path': str(path), 'sha256': sha(path)}

def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')

c = json.loads((B / 'config-row1-UNAUTHORIZED.json').read_bytes())
a = json.loads((B / 'stage-admission-DRAFT.json').read_bytes())
assert len(c) == 44 and c['authorized'] is False
assert len(c['material_hashes']) == 35 and len(c['expected_core']) == 28 and len(c['tool_hashes']) == 6
for name, digest in c['material_hashes'].items():
    assert sha(W / name) == digest, name
for path, digest in c['tool_hashes'].items():
    assert sha(path) == digest, path
for key, arg in [('head', 'HEAD'), ('tree', 'HEAD^{tree}')]:
    assert subprocess.check_output([c['git'], 'rev-parse', arg], cwd=W, text=True).strip() == c['candidate'][key]
assert subprocess.check_output([c['git'], 'diff', '--binary', 'HEAD'], cwd=W) == b''
table = json.loads(Path(c['table_path']).read_bytes())
assert sha(c['table_path']) == a['table_sha256'] == '0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d'
conditions = dict(table['conditions'])
conditions.update({entry['condition']['id']: entry for entry in table['growth_proposals']})
core = {}
for name, condition in conditions.items():
    expected = condition['expected_output']
    core[name] = {key: {'shape': expected[key]['shape'], 'dtype': '<f8'}
                  for key in ('image', 'x_um', 'y_um', 'z_um', 'carriers_cyc_um')}
    for key in ('modulation', 'raw_modulation'):
        core[name][key] = {'shape': expected['modulation_and_raw']['shape'], 'dtype': '<c16'}
assert core == c['expected_core'] == json.loads((B / 'expected-core28.json').read_bytes())
assert a['operating_proposals'] == {row['condition_id']: conditions[row['condition_id']]['operating_proposal'] for row in a['stage_rows']}
assert len(a['stage_rows']) == 6 and c['allowed_attempt_ids'] == [a['stage_rows'][0]['attempt_id']]

prior192 = ref(E / 'growth192-first-readiness/root-growth192-stage-closed.json')
assert prior192['sha256'] == '0affac7112b093baa1759080fa864241f9d95d80cbf685aeca1c935909c252b1'
closures = [c['prior_stage_closures'][0], prior192]
for item in closures:
    assert sha(item['path']) == item['sha256']
    closed = json.loads(Path(item['path']).read_bytes())
    assert closed['closed'] is True and closed['unresolved_owners'] == [] and closed['scope'] == 'WS116_ROOT_closed_prior_stage'
accepted192 = [ref(E / 'growth192-first-readiness/root-growth192-independent-scalar.json'),
               ref(E / 'growth192-first-readiness/coordinator-growth192-closed-file-scalar-review.json'), prior192]
assert [x['sha256'] for x in accepted192[:2]] == [
    '2cc066edb5ebeeb52d8d2a0e41d8d3435e5628d60113a72d2b85bf19e0b2c240',
    '311eabff259e07e35f1b3890d9ffdb7603d526cfc9ecbdd0584fe22eaa64a6ab']

capture = subprocess.run([c['outer_python'], c['capture_helper']], capture_output=True, text=True)
save(B / 'root-preparation-context-command.json', {'returncode': capture.returncode, 'stdout': capture.stdout, 'stderr': capture.stderr})
assert capture.returncode == 0
pointer = json.loads(capture.stdout)
assert sha(pointer['path']) == pointer['sha256']
proof = json.loads(Path(pointer['path']).read_bytes())
inner = json.loads(proof['inner']['stdout'])
assert proof['docker_inspect']['returncode'] == proof['inner']['returncode'] == 0
assert proof['outer']['file_identities'] == inner['file_identities']
facts = {}
for label, view in [('outer', proof['outer']), ('inner', inner)]:
    old = c['mapping'][label]
    assert view['cgroup_namespace'] == old['cgroup_namespace'] and view['file_identities'] == old['file_identities']
    for path, value in old['fixed_files'].items():
        assert view['files'][path] == value, (label, path)
    files = view['files']
    events = dict(line.split() for line in files['/sys/fs/cgroup/memory.events'].splitlines())
    assert events == {'low': '0', 'high': '0', 'max': '50340', 'oom': '0', 'oom_kill': '0', 'oom_group_kill': '0'}
    current = int(files['/sys/fs/cgroup/memory.current'])
    maximum = int(files['/sys/fs/cgroup/memory.max'])
    swap = int(files['/sys/fs/cgroup/memory.swap.current'])
    mem = dict(line.split(':', 1) for line in files['/proc/meminfo'].splitlines())
    available = int(mem['MemAvailable'].split()[0]) * 1024
    assert current + 6442450944 + 3221225472 <= 15032385536 < maximum
    assert available > 9663676416 and swap == 0
    old['events_exact'] = events
    old['swap_current_bytes'] = swap
    facts[label] = {'current_bytes': current, 'maximum_bytes': maximum, 'swap_bytes': swap,
                    'host_available_bytes': available, 'events': events,
                    'current_plus_stop_plus_reserve_bytes': current + 6442450944 + 3221225472}
c['docker_inspect_stdout'] = proof['docker_inspect']['stdout']
m = json.loads((B / 'root-preflight-metadata.json').read_bytes())
for key in ['uid', 'gid', 'executable', 'cwd', 'boot_id', 'namespaces', 'rlimits']:
    assert m[key] == c['metadata_expected'][key], key
assert m['owned_processes'] == []
for disk in m['disks'].values():
    assert disk['free_bytes'] >= 2965897216 and disk['free_inodes'] > 0
actual_disk = {k: m['disks'][str(B)][k] for k in ['device', 'fsid', 'fragment_size']}
assert actual_disk == c['metadata_expected']['disk_identity'][c['external_batch_directory']]
assert not Path(c['external_batch_directory']).exists()

case = {'schema': 'ROOT-WS116-growth256-source-and-physical-preflight-v1',
        'accepted_for_guarded_first_trial': True, 'candidate': c['candidate'],
        'material_hashes': c['material_hashes'], 'table_sha256': a['table_sha256'],
        'source_basis_counts': {'T': 1, 'D': 3, 'P': 5, 'Z': 8, 'Y': 256, 'X': 256,
                               'native_volume': 8*256*256, 'native_half_volume': 8*256*129,
                               'caller_elements': 1*3*5*8*256*256, 'aggregate_q_elements': 3*5*8*256*129,
                               'output_volume': 8*512*512, 'largest_listed_allocation_bytes': 63406080},
        'signed32_and_actual_width_intp_valid': True,
        'stencil_source_enclosure': {'u_max': 4, 'axial_abs_table_max': 3, 'K': 16,
                                     'maximum_flat_vertex': 95, 'order_flat_count': 1024,
                                     'basis': 'unchanged support-before-sampling enclosure; source bound, not actual query trace'},
        'partial_named_subset_bytes': 265273344, 'partial_subset_is_neither_RSS_nor_total_bound': True,
        'resource_context': {'path': pointer['path'], 'sha256': pointer['sha256']},
        'resource_facts': facts, 'metadata': ref(B / 'root-preflight-metadata.json'),
        'accepted192_JSON_data': accepted192,
        'accepted192_review_markdown': ref(E / 'growth192-first-readiness/coordinator-growth192-review.md'),
        'scope': 'First256supplied summary trial only. Actual192 three-repeat raw/scalar eligibility accepted as prerequisite; final scientific report acceptance pending. No runtime/peak prediction from192.',
        'remaining_unknown': ['actual input/output/finite scientific result', 'native workspace/allocator/RSS/cost',
                              'external physical host actors and unexposed ancestors', 'actual per-row context until fresh binder checks'],
        'dynamic_guards': 'Fresh metadata and capture per row; capture<=5s to existing runner invocation, original proof hash/horizon3720s plus fresh end-domain/events/swap/owners. Any failure HOLD; no automatic retry, recapture, skip, growth, full or profile.'}
casepath = B / 'root-case-and-resource-preflight.json'
save(casepath, case)

now = time.time_ns()
window = {'starts_unix_ns': now, 'ends_unix_ns': now + 7200*10**9}
ack = {'schema': 'ROOT-campaign-stage-suspension-ACK-v1', 'stage_id': c['stage_id'],
       'window': window, 'campaign_work_suspended': True, 'known_active_numerical_processes': [],
       'outside_campaign_actors': 'unknown_not_scanned', 'unresolved_owners': [],
       'prior_stage_closures': closures, 'observed_at_unix_ns': now,
       'known_work_closure': {'113': 'C3 AST/Ruff/format direct targets and whole namespaces/controllers/proxies ended. All future tool/native/test/type/build work suspended; source-only C4 correction and plans allowed.',
                             '116': '192six science rows and12owners closed; a2 finite synthetic attempt ended. No science/analysis/guards active; EA unchanged.',
                             'other_campaign': '114/117/118 closed SAFE HOLD;119/120 intake-only; no authorized runtime.',
                             'root': 'Only current source/file/operational metadata preparation; no unrelated test/import/install/benchmark.'},
       'limits': 'Known campaign schedule only; external actors unknown, not scanned. This packet assembly does not start a workload.'}
ackpath = B / 'root-scheduler-ACK-row1.json'
save(ackpath, ack)
a.update(schema='ROOT-WS116-growth256-stage-admission-v1', execution_authorized=True,
         prerequisites_accepted=True, fresh_case_preflight_accepted=True,
         prior_stage_closures=closures, prior_data_refs=accepted192)
a['required_prior_data'] = 'Actual complete192six raw/scalar eligibility and closed12owners accepted by ROOT; final scientific report review remains pending.'
a['case_preflight'] = ref(casepath)
a['markdown_review_hash_only'] = case['accepted192_review_markdown']
adpath = B / 'root-stage-admission.json'
save(adpath, a)
authority = json.loads((B / 'root-authority-DRAFT.json').read_bytes())
authority.update(schema='ROOT-WS116-growth256-first-row-authority-v1', authorized=True,
                 execution_authorized=True, prior_stage_closures=closures, accepted192_data=accepted192,
                 root192_closure=prior192, window=window, root_fresh_context_and_case_preflight=ref(casepath),
                 root_scheduler_ack=ref(ackpath))
authority['release_disposition'] = 'ROOT-approved exact first-row packet; final config remains disabled until coordinator file audit and ROOT explicit execution release.'
authpath = B / 'root-authority-row1.json'
save(authpath, authority)
ledger = {'scope': 'WS116_current_stage_scientific_observer_workload_processes', 'stage_id': c['stage_id'],
          'root_authority_sha256': sha(authpath), 'unresolved': [], 'closed_owned_processes': [],
          'meaning': 'New256stage has no commissioned observer/workload; prior192 owners remain in immutable prior-stage closure, never fresh-scanned.'}
ledgerpath = B / 'root-current-stage-ledger-row1.json'
save(ledgerpath, ledger)
c.update(authority_expected=authority, root_authority=ref(authpath), window=window,
         scheduler_ack=ref(ackpath), scheduler_ack_expected=ack, owned_ledger=ref(ledgerpath),
         stage_admission=ref(adpath), prior_stage_closures=closures)
c['grant_fixed'].update(numerical_release=True, campaign_ownership_resolved=True)
c['grant_fixed']['exclusive_window'].update(released=True, evidence=str(ackpath), evidence_sha256=sha(ackpath))
c['conditional_rationale'] = 'ROOT first256 summary supplied r1 only; accepted closed192six prerequisites, actual new source/case/resource preflight and new schedule. Exact config still disabled pending coordinator file audit and ROOT final explicit release. Existing binder rechecks per-row context; no automatic growth/retry/full/profile.'
save(B / 'config-row1-PREPARED.json', c)
print(json.dumps({'prepared_config': ref(B / 'config-row1-PREPARED.json'), 'case_preflight': ref(casepath),
                  'stage_admission': ref(adpath), 'authority': ref(authpath), 'ACK': ref(ackpath),
                  'window': window, 'facts': facts, 'execution_released': False}))
