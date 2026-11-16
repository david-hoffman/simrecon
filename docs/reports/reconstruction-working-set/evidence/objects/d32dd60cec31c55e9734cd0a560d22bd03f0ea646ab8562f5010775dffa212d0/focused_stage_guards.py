"""UNEXECUTED finite SYNTHETIC guards for canonical940; explicit ROOT release only."""

import argparse
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

ROOT = Path('/workspace/work/campaign/evidence/116')
HERE = ROOT / 'stage-analysis-source/focused-guards-preparation'
TARGET = ROOT / 'stage-analysis-source/aggregate_stage_observations.py'
BINDER = ROOT / 'growth-profile-binder/source-final-coordinator-frozen/stage_batch_binder.py'
PREP = ROOT / 'report-source-preparation'
INPUTS = PREP / 'inputs'
DRIVER = HERE / 'focused_stage_guards.py'
VECTORS = HERE / 'fixture-vectors.json'
LABEL = 'SYNTHETIC_guard_never_scientific_observation'
FIXED_PINS = {
    str(TARGET): '940f6e62cbf3bf817e7173bfa896f329658f1d4b5bb9ccca7228a51051b45f97',
    str(BINDER): '8190db99ef7fca49659e2979172a111f1c1f325eccef27c991caea06c1a2c4e9',
    str(PREP / 'aggregate_observations.py'): 'a0758714c64798a39ded0b1beaf76f8dbbfc24c023d83cc8244172f106235dac',
    str(ROOT / 'stage-analysis-source/config-template.json'): '6b7d7b98b115cecb98cfe5e37056ce4687307ff35a7b7e8b55c6b2bcb19bb967',
    str(INPUTS / 'admission-table.json'): '0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d',
    str(INPUTS / 'qualified-method7-source-basis.json'): 'bcfbb0352618325a4363952ed2f58bd2fe0660d730b0d6138093bdbc8a22303c',
    str(INPUTS / 'source-identities.json'): '49db118fc930f6c86c8f24201fb9de001a7d3b47aac9fdc7670143c59f922a72',
    str(PREP / 'schema-inputs/source-identities.json'): '1350a5cfacb72e4a7d18b9947b002a56a6178bef45cd6b399a87bc66a5b3395d',
    str(INPUTS / 'docs/reports/reconstruction-working-set/observer.py'): '384b4f1a95ad135136c60b9bb750437fe72e5bbb1a94fc21bd7cc1ae14ff6c9e',
    str(INPUTS / 'docs/reports/reconstruction-working-set/run_attempt.py'): '2c2358bbcb801a970de6b1d3c786cf510394887ef397b1e14d7ad4a843efea1e',
    str(INPUTS / 'docs/reports/reconstruction-working-set/workload_child.py'): '5249e4cdadbee6523012127468fd9c3d90228df2558c81087929bc35e60e5459',
}
OUT = None
RESULTS = []
BLOCKED = []
WRITTEN = set()
a = s = TABLE = BASIS = None


def require(value, message):
    if not value:
        raise AssertionError(message)


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


def bounded_bytes(path, limit=4 * 1024 * 1024):
    with Path(path).open('rb') as stream:
        result = stream.read(limit + 1)
    require(len(result) <= limit, 'tiny source/fixture bound exceeded')
    return result


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, allow_nan=False) + '\n'
    require(len(payload.encode()) <= 2 * 1024 * 1024, 'synthetic JSON bound exceeded')
    WRITTEN.add(str(path.resolve()))
    require(len(WRITTEN) <= 256, 'synthetic output-file bound exceeded')
    if path.exists() and name != 'results.json':
        require(bounded_bytes(path, 2 * 1024 * 1024) == payload.encode(), 'immutable synthetic fixture/output collision')
        return {'path': str(path), 'sha256': h(payload)}
    path.write_text(payload)
    return {'path': str(path), 'sha256': h(payload)}


class ForbiddenEffect(BaseException):
    pass


def forbidden(*args, **kwargs):
    BLOCKED.append('forbidden effect/import/time/identity call')
    raise ForbiddenEffect(BLOCKED[-1])


def install_blocks(pins):
    forbidden_imports = {'numpy', 'scipy', 'simrecon', 'resource', 'ctypes', 'psutil', 'socket'}
    require(not any(name.split('.')[0] in forbidden_imports for name in sys.modules), 'forbidden module preloaded')
    source_paths = {str(Path(path).resolve()) for path in pins}
    stdlib = Path(sys.base_prefix).resolve()

    def audit(event, args):
        if event == 'import' and args[0].split('.')[0] in forbidden_imports:
            forbidden()
        if (event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.fork', 'os.forkpty',
                      'os.kill', 'os.killpg', 'os.exec', 'os.spawn', 'os.wait', 'os.waitpid', 'os.wait4'} or
                event.startswith(('socket.', 'ctypes.'))):
            forbidden()
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(char in mode for char in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing:
                if not path.is_relative_to(OUT):
                    forbidden()
                WRITTEN.add(str(path))
                require(len(WRITTEN) <= 256, 'synthetic output-file bound exceeded')
            elif not (str(path) in source_paths or path.is_relative_to(OUT) or path.is_relative_to(stdlib)):
                forbidden()
        if event == 'os.mkdir' and not Path(os.fsdecode(args[0])).resolve().is_relative_to(OUT):
            forbidden()
        if event in {'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink', 'os.chmod', 'os.truncate'}:
            forbidden()

    sys.addaudithook(audit)
    for name in ('fork', 'forkpty', 'posix_spawn', 'posix_spawnp', 'system', 'kill', 'killpg',
                 'wait', 'waitpid', 'wait3', 'wait4', 'getpid', 'getppid', 'getpgid', 'getsid'):
        if hasattr(os, name):
            setattr(os, name, forbidden)
    for name in ('time', 'time_ns', 'monotonic', 'monotonic_ns', 'perf_counter', 'perf_counter_ns', 'sleep'):
        setattr(time, name, forbidden)
    import signal
    for name in ('signal', 'alarm', 'setitimer', 'raise_signal', 'pthread_kill'):
        if hasattr(signal, name):
            setattr(signal, name, forbidden)


def load_source(name, path):
    # Exact pinned source bytes, canonical __file__, no bytecode-cache lookup.
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(bounded_bytes(path), str(path), 'exec'), module.__dict__)
    return module


@contextlib.contextmanager
def replace(obj, **values):
    old = {key: getattr(obj, key) for key in values}
    for key, value in values.items():
        setattr(obj, key, value)
    try:
        yield
    finally:
        for key, value in old.items():
            setattr(obj, key, value)


def check(name, action, exception=None, phrase=None):
    require(len(RESULTS) < 128 and name not in {row['id'] for row in RESULTS}, 'finite case identity bound')
    observed = None
    try:
        action()
    except BaseException as error:
        observed = {'type': type(error).__name__, 'reason': str(error)}
        matched = exception is not None and type(error) is exception and phrase in str(error)
        if not matched:
            row = {'id': name, 'label': LABEL, 'matched': False, 'observed': observed}
            RESULTS.append(row)
            save('cases/' + name + '.json', row)
            save('results.json', RESULTS)
            raise
    else:
        if exception is not None:
            row = {'id': name, 'label': LABEL, 'matched': False, 'observed': None,
                   'error': 'required specific refusal absent', 'expected_type': exception.__name__,
                   'expected_phrase': phrase}
            RESULTS.append(row)
            save('cases/' + name + '.json', row)
            save('results.json', RESULTS)
            raise AssertionError(name + ': required specific refusal absent')
    require(not BLOCKED, 'blocked effect attempt invalidates case')
    row = {'id': name, 'label': LABEL, 'matched': True, 'observed': observed,
           'expected_type': exception.__name__ if exception else None, 'expected_phrase': phrase}
    RESULTS.append(row)
    save('cases/' + name + '.json', row)
    save('results.json', RESULTS)


class MemoryFiles:
    """Structural-only fake refs; real byte/JSON paths are separately exercised."""
    def __init__(self, values, real=None):
        self.values, self.real, self.audit = values, real or {}, []

    def read(self, ref, **kwargs):
        if ref['path'] in self.real:
            return self.real[ref['path']].read(ref, **kwargs)
        self.audit.append({**ref, 'logical_bytes': 1, 'allocated_bytes': 4096})
        return copy.deepcopy(self.values[ref['path']])


def core_for(conditions):
    core = {}
    for cid, plan in conditions.items():
        exp = plan['expected_output']
        core[cid] = {name: {'shape': exp[name]['shape'], 'dtype': '<f8'}
                     for name in ('image', 'x_um', 'y_um', 'z_um', 'carriers_cyc_um')}
        core[cid].update({name: {'shape': exp['modulation_and_raw']['shape'], 'dtype': '<c16'}
                          for name in ('modulation', 'raw_modulation')})
    return core


class Fixture:
    """Small actual-schema SYNTHETIC mapping; no real scientific values or arrays."""
    def __init__(self, phase='stage', profile=False, stage_id=None, selected=None):
        self.values = {}
        self.basis = {'candidate': {'head': 'SYNTHETIC', 'tree': 'SYNTHETIC', 'tracked_diff_sha256': h('')},
                      'material_hashes': {name: h('SYNTHETIC-' + name) for name in BASIS['material_hashes']},
                      'bootstrap_sha256': BASIS['bootstrap_sha256']}
        sid = stage_id or ('central64-profiles' if profile else 'growth192-summary')
        rows, conditions = s.stage_recipe(TABLE, sid, selected)
        if phase == 'initial':
            self.row = copy.deepcopy(next(row for row in TABLE['initial_rows']
                                         if row['condition_id'] == 'central64-summary-searched' and row['repetition'] == 1))
            conditions = TABLE['conditions']
            rows = [self.row]
        else:
            self.row = copy.deepcopy(rows[0])
        self.plan = copy.deepcopy(conditions[self.row['condition_id']])
        self.source = a.BINDER_SHA if phase == 'initial' else a.STAGE_SHA
        root = OUT / 'SYNTHETIC-worktree'
        directory = OUT / 'SYNTHETIC-support' / self.row['attempt_id']
        method_ref = self.ref('method', {})
        basis_ref = self.ref('basis', self.basis, a.BASIS_SHA)
        method = {'candidate': self.basis['candidate'], 'suitable': True, 'qualified': True,
                  'runner_end_domain_check': False, 'source_basis': basis_ref,
                  'review_report': self.ref('review', None)}
        self.values[method_ref['path']] = method
        software = {key: 'SYNTHETIC-' + key for key in ('python', 'executable', 'numpy', 'scipy',
                    'numpy_backend', 'scipy_fft_default_workers', 'product_module', 'effective_worker_limits')}
        software.update(numpy_backend={'SYNTHETIC': True}, scipy_fft_default_workers=1)
        environment = {'software': software, 'label': LABEL}
        authority = {'label': LABEL}
        self.stored = {'expected': {'pid': 123, 'start_ticks': 456, 'boot_id': 'SYNTHETIC-boot', 'fds': [64, 65]},
                       'identity_state': 'absent', 'fds': {'64': {'state': 'absent'}, '65': {'state': 'absent'}}}
        old_metadata = {'protocol': 'WS116-fixed-ubuntu-metadata-v1', 'owned_processes': [self.stored]}
        closure = {'scope': 'WS116_ROOT_closed_prior_stage', 'closed': True, 'unresolved_owners': [],
                   'historical_identity_facts_retained': True,
                   'terminal_receipts': [self.ref('old-receipt', {'terminal': {'pid': 123}, 'wait_ownership_lost': False})],
                   'eligible_boundaries': [self.ref('old-boundary', {'status': 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW'})],
                   'last_post_metadata': self.ref('old-metadata', old_metadata)}
        closures = [self.ref('closure', closure)]
        ack = {'stage_id': sid, 'unresolved_owners': [], 'prior_stage_closures': closures,
               'window': {'starts_unix_ns': 10**18 - 100, 'ends_unix_ns': 10**18 + 10**12},
               'campaign_work_suspended': True, 'known_active_numerical_processes': [],
               'outside_campaign_actors': 'unknown_not_scanned'}
        authority_ref = self.ref('authority', authority)
        domain = {'membership': 'SYNTHETIC', 'namespace': 'SYNTHETIC', 'mount_root': '/',
                  'mount': '/SYNTHETIC', 'visible_memory_max': {'/SYNTHETIC': '1024'}}
        fixed = {'numerical_release': True, 'accepted_112_then_115': True, 'campaign_ownership_resolved': True,
                 'exclusive_window': {'released': True, 'evidence': authority_ref['path'], 'evidence_sha256': authority_ref['sha256']},
                 'declared_growth_conditions': list({row['condition_id']: conditions[row['condition_id']]['condition']
                                                     for row in rows if row['condition_id'].startswith('growth')}.values()),
                 'no_automatic_retry_or_growth': True}
        self.cfg = {'authorized': True, 'binder_sha256': self.source, **self.basis,
                    'allowed_attempt_ids': [self.row['attempt_id']], 'root': str(root),
                    'accepted_method7': method_ref, 'method7_expected': copy.deepcopy(method),
                    'root_authority': authority_ref, 'authority_expected': authority,
                    'environment': self.ref('environment', environment), 'environment_expected': copy.deepcopy(environment),
                    'scheduler_ack': self.ref('ack', ack), 'scheduler_ack_expected': copy.deepcopy(ack),
                    'owned_ledger': self.ref('ledger', {'scope': 'WS116_current_stage_scientific_observer_workload_processes'
                        if phase == 'stage' else 'WS116_scientific_observer_workload_processes', 'stage_id': sid,
                        'unresolved': [], 'root_authority_sha256': authority_ref['sha256'], 'closed_owned_processes': []}),
                    'metadata_source': self.ref('metadata-source', None), 'stage_id': sid, 'selected_largest_size': selected,
                    'prior_stage_closures': closures, 'prior_eligible': [], 'continuation_authorized': False,
                    'expected_core': core_for(conditions), 'matched_unprofiled': {}, 'grant_fixed': fixed,
                    'expected_exposed': domain, 'receipt_protocol': 'WS116-attempt-v3', 'child_protocol': 'WS116-child-v2',
                    'external_batch_directory': str(directory.parent), 'window': ack['window'],
                    'metadata_max_age_seconds': 60, 'docker_inspect_stdout': 'SYNTHETIC-docker'}
        for row in rows:
            if row['profile'] or conditions[row['condition_id']]['condition']['mode'] == 'full':
                self.cfg['matched_unprofiled'][row['attempt_id']] = {
                    'boundary': self.ref('unused-control-boundary-' + row['attempt_id'], None),
                    'config': self.ref('unused-control-config-' + row['attempt_id'], None)}
        admission = {'stage_id': sid, 'selected_largest_size': selected, 'candidate': self.basis['candidate'],
                     'material_hashes': self.basis['material_hashes'], 'method7': method_ref, 'environment': self.cfg['environment'],
                     'prerequisites_accepted': True, 'fresh_case_preflight_accepted': True, 'prior_stage_closures': closures,
                     'stage_rows': rows, 'table_sha256': a.TABLE_SHA, 'prior_data_refs': [self.ref('prior-data', {'label': LABEL})],
                     'operating_proposals': {row['condition_id']: conditions[row['condition_id']]['operating_proposal'] for row in rows}}
        self.cfg['stage_admission'] = self.ref('admission', admission)
        self.entry = {'phase': phase, 'attempt_id': self.row['attempt_id'], 'support': {}}
        self.entry['batch_config'] = self.ref('cfg', self.cfg)
        self.boundary = {'status': 'ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW', 'row': copy.deepcopy(self.row),
                         'candidate': self.basis['candidate'], 'material_hashes': self.basis['material_hashes'],
                         'table_sha256': a.TABLE_SHA, 'method7': method_ref, 'config_sha256': self.entry['batch_config']['sha256'],
                         'source_sha256': self.source, 'raw_path': str(root / 'docs/reports/reconstruction-working-set/raw' / self.row['attempt_id']),
                         'raw_files': {}, 'end_validation_scope': 'binder original-proof hash/horizon + fresh end domain/context/margins/events; runner receipt does not perform this check',
                         'stage_id': sid, 'stage_admission': self.cfg['stage_admission'], 'prior_stage_closures': closures}
        self.entry['boundary'] = self.ref(str(directory / 'eligible-boundary.json'), self.boundary)
        self.build_record(software, domain)
        self.build_operational(directory)
        self.files = MemoryFiles(self.values)

    def ref(self, name, value, digest=None):
        path = name if name.startswith('/') else str(OUT / 'SYNTHETIC-map' / name)
        self.values[path] = value
        return {'path': path, 'sha256': digest or h('SYNTHETIC-ref-' + name)}

    def value(self, name):
        return self.values[str(OUT / 'SYNTHETIC-map' / name)]

    def build_record(self, software, domain):
        row, condition = self.row, self.plan['condition']
        raw = Path(self.boundary['raw_path'])
        refs = {name: self.ref(str(raw / name), None) for name in
                ('receipt.json', 'stdout.json', 'spec.json', 'grant.input', 'owned-child.json')}
        inventory = {name: {'sha256': ref['sha256'], 'logical_bytes': 1, 'allocated_bytes': 4096} for name, ref in refs.items()}
        self.boundary['raw_files'] = inventory
        launch = {'bootstrap_sha256': self.basis['bootstrap_sha256'], 'nonce': row['launch_nonce']}
        self.spec = {**condition, 'repetition': row['repetition'], 'profile': row['profile'],
                     'expected_material_hashes': self.basis['material_hashes'], 'expected_exposed_domain': domain, 'launch': launch}
        self.grant = {**copy.deepcopy(self.cfg['grant_fixed']), 'candidate': self.basis['candidate'],
                      'material_hashes': self.basis['material_hashes'], 'condition_id': row['condition_id'],
                      'attempt_id': row['attempt_id'], 'repetition': row['repetition'], 'profile': row['profile'],
                      'launch_nonce': row['launch_nonce'], 'resource_domain': {'expected_exposed': domain}}
        if condition['id'].startswith('growth'):
            self.grant.update(growth_separate_admission=True, smaller_measured_evidence={
                'root_stage_admission': self.cfg['stage_admission'], 'prior_stage_closures': self.cfg['prior_stage_closures']})
        snapshots = {name: {'scope': scope, 'ru_maxrss_native': native, 'ru_maxrss_native_units': 'Linux KiB',
                           'cumulative_high_water_bytes': native * 1024, 'monotonic_ns': stamp,
                           **{key: 0 for key in ('ru_minflt', 'ru_majflt', 'ru_nswap', 'ru_inblock', 'ru_oublock')},
                           'ru_utime_seconds': 0.0, 'ru_stime_seconds': 0.0}
                     for (name, scope), native, stamp in zip(a.SNAPSHOT_SCOPES.items(), (10, 30, 40), (110, 141, 150), strict=True)}
        outputs = {name: [name, item['shape'], item['dtype'], h('SYNTHETIC-array-' + name)]
                   for name, item in self.cfg['expected_core'][condition['id']].items()}
        events = [{'stage': name, 'time_index': index, 'edge': edge, 'monotonic_ns': 121 + number,
                   'ru_maxrss_native_KiB': 15} for number, (name, index, edge) in enumerate(
            (name, index, edge) for name, index in (('declaration', None), ('preparation', None),
            ('estimation', None), ('reconstruction', 0), ('result', None)) for edge in ('enter', 'exit'))] if row['profile'] else []
        payload = {'array_payload_bytes': 8, 'unique_backings': 1, 'python_metadata_estimate_bytes': 1,
                   'metadata_limit': LABEL, 'arrays': [{'path': 'SYNTHETIC', 'shape': [1], 'dtype': '<f8', 'bytes': 8}]}
        self.child = {'protocol': 'WS116-child-v2', 'status': 'finite_observation_pending_qualification',
                      'finite_common_fields': True, 'material_identity_matches': True, 'pid': 123,
                      'spec': self.spec, 'material_hashes_before': self.basis['material_hashes'],
                      'material_hashes_after': self.basis['material_hashes'], 'branches': self.plan['expected_output']['branches'],
                      'stages': events, 'output_hashes': outputs, 'input_arrays': {
                          'specimen': ['specimen', self.plan['fixture']['raw_shape_TDPZYX'], '<f4', h('SYNTHETIC-input')],
                          'transfer': ['transfer.samples', self.plan['fixture']['transfer_shape'], '<c16', h('SYNTHETIC-transfer')]},
                      'input_sha256': h('SYNTHETIC-input'), 'common_output_sha256': h('SYNTHETIC-common'),
                      'public_result_sha256': h('SYNTHETIC-public'), 'snapshots': snapshots, 'started_monotonic_ns': 100,
                      'call_start_monotonic_ns': 120, 'call_end_monotonic_ns': 140, 'elapsed_call_seconds': 20 / 1e9,
                      'snapshot_limits': LABEL,
                      'context': {'pid': 123, 'system': 'Linux', 'kernel': LABEL, 'machine': LABEL,
                          'meminfo': LABEL, 'host_id_sha256': h(LABEL), 'disk_available_bytes': 1,
                          'threads': {name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')},
                          'allocator': {'PYTHONMALLOC': None, 'MALLOC_ARENA_MAX': None},
                          'rlimits': {name: [-1, -1] for name in ('RLIMIT_AS', 'RLIMIT_DATA', 'RLIMIT_RSS', 'RLIMIT_CPU', 'RLIMIT_FSIZE', 'RLIMIT_NOFILE')},
                          'cgroup': {**{name: domain[name] for name in ('membership', 'mount_root', 'mount', 'namespace')},
                              'hidden_ancestors': 'unknown_unobservable', 'visible_ancestors': [
                                  {'path': '/SYNTHETIC', 'memory.current': '1', 'memory.max': '1024',
                                   **{name: None for name in ('memory.peak', 'memory.events', 'memory.swap.max', 'memory.swap.current')}}]}},
                      'caller_retained': copy.deepcopy(payload), 'result_retained': payload, **software}
        self.receipt = {'protocol': 'WS116-attempt-v3', 'status': 'complete_child_observed_pending_scientific_qualification',
                        'child_outcome': self.child['status'], 'signals': [], 'nonterminal_wait_events': [],
                        'startup_eof_observed': True, 'startup_parent_fds_closed': True, 'wait_ownership_lost': False,
                        'material_identity_matches': True, 'child_record_sha256': refs['stdout.json']['sha256'],
                        'grant_sha256': refs['grant.input']['sha256'], 'workload_pid': 123, 'observer_pid': 122,
                        'launch': launch, 'session_ready': {'nonce': row['launch_nonce'], 'pid': 123, 'pgid': 123, 'session_id': 123, 'ppid': 122},
                        'terminal': {'pid': 123, 'wait_status_raw': 0, 'returncode': 0, 'exited': True, 'signaled': False,
                                     'rusage_native': {'ru_maxrss': 50}, 'ru_maxrss_native_units': 'Linux KiB',
                                     'ru_maxrss_multiplier_to_bytes': 1024, 'kernel_reported_direct_child_high_water_bytes': 50 * 1024,
                                     'reaped_monotonic_ns': 200}, 'spawn_start_monotonic_ns': 90,
                        'resource_domain_admission': self.grant['resource_domain'],
                        'files_before_receipt': {name: item for name, item in inventory.items() if name != 'receipt.json'}}
        for suffix in ('before', 'after', 'final'):
            self.receipt['candidate_' + suffix] = self.basis['candidate']
            self.receipt['material_hashes_' + suffix] = self.basis['material_hashes']
        self.marker = {'attempt_id': row['attempt_id'], 'workload_pid': 123, 'observer_pid': 122,
                       'child_identity': {'pid': 123, 'boot_id': 'SYNTHETIC-boot', 'start_ticks': 456},
                       'grant_sha256': refs['grant.input']['sha256'], 'spec_sha256': refs['spec.json']['sha256']}
        for name, value in (('receipt.json', self.receipt), ('stdout.json', self.child), ('spec.json', self.spec),
                            ('grant.input', self.grant), ('owned-child.json', self.marker)):
            self.values[refs[name]['path']] = value
        self.boundary['fingerprints'] = {key: self.child[key] for key in
                                        ('input_sha256', 'common_output_sha256', 'public_result_sha256', 'branches')}

    def build_operational(self, directory):
        stamp = 10**18
        pre_ref = self.ref('pre-proof', None)
        self.grant['root_release_at_unix_ns'] = stamp
        self.grant['resource_domain']['correspondence_evidence'] = {**pre_ref, 'observed_at_unix_ns': stamp, 'maximum_age_seconds': 360}
        def support(name, value, digest=None):
            self.entry['support'][name] = self.ref(str(directory / name), value, digest)
        support('grant.json', self.grant, self.boundary['raw_files']['grant.input']['sha256'])
        support('raw-files.json', self.boundary['raw_files'])
        support('intent.json', {'row': self.row, 'config_sha256': self.entry['batch_config']['sha256'],
                               'source_sha256': self.source, 'grant_sha256': self.entry['support']['grant.json']['sha256'],
                               'time_unix_ns': stamp, 'proof': pre_ref})
        support('observer-exit.json', {'returncode': 0, 'overdue': False, 'wait_gaps': [],
                                      'runner_invocation_unix_ns': stamp + 10**9, 'proof_age_at_invocation_seconds': 1.0})
        expected = {'uid': 1000, 'gid': 1000, 'executable': '/SYNTHETIC/python', 'cwd': '/SYNTHETIC',
                    'boot_id': 'SYNTHETIC-boot', 'namespaces': {'pid': 'pid:[SYNTHETIC]', 'cgroup': 'cgroup:[SYNTHETIC]'},
                    'rlimits': {'RLIMIT_AS': [-1, -1]}}
        self.cfg['metadata_expected'] = expected
        self.cfg['mapping'] = {name: {'cgroup_namespace': name, 'file_identities': {'SYNTHETIC': 1},
                                     'fixed_files': {'SYNTHETIC-limit': '16'}} for name in ('outer', 'inner')}
        for phase in ('pre', 'post'):
            observed = stamp if phase == 'pre' else stamp + 2 * 10**9
            def view(name):
                return {'cgroup_namespace': name, 'file_identities': {'SYNTHETIC': 1},
                        'files': {'SYNTHETIC-limit': '16'}, 'observed_at_unix_ns': observed}
            proof = {'schema': 'campaign-resource-domain-correspondence-v1', 'capture_source_sha256': a.CAPTURE_SHA,
                     'external_ancestors': 'unknown_unobservable', 'docker_inspect': {'returncode': 0, 'stdout': 'SYNTHETIC-docker'},
                     'inner': {'returncode': 0, 'stdout': json.dumps(view('inner'))}, 'outer': view('outer'), 'started_at_unix_ns': observed}
            pointer = self.ref(phase + '-proof', proof)
            support(phase + '-capture-command.json', {'returncode': 0, 'stdout': json.dumps(pointer)})
            request_name = phase + '-metadata-request.json'
            support(request_name, {'owned_processes': [self.stored]})
            # Request uses expected identities, observation uses the recorded absent fact.
            self.values[self.entry['support'][request_name]['path']] = {'owned_processes': [self.stored['expected']]}
            metadata = {**expected, 'protocol': 'WS116-fixed-ubuntu-metadata-v1',
                        'source_sha256': self.cfg['metadata_source']['sha256'],
                        'request_sha256': self.entry['support'][request_name]['sha256'],
                        'owned_processes': [self.stored], 'outside_campaign_processes': 'unknown_not_scanned',
                        'observed_at_unix_ns': observed}
            support(phase + '-metadata.json', metadata)
            support(phase + '-metadata-intent.json', {'source': self.cfg['metadata_source'],
                                                    'request_sha256': self.entry['support'][request_name]['sha256']})
            support(phase + '-metadata-command.json', {'returncode': 0, 'stdout': json.dumps(metadata)})
        for alias, name in (('OP-EXIT', 'observer-exit.json'), ('OP-INTENT', 'intent.json'),
                            ('OP-PRE-CAPTURE', 'pre-capture-command.json'), ('OP-PRE-METADATA', 'pre-metadata.json')):
            self.values[str(OUT / 'SYNTHETIC-map' / alias)] = self.values[self.entry['support'][name]['path']]

    def call_boundary(self):
        return a.boundary_for(self.entry, self.files, self.basis, self.row, TABLE)

    def call_record(self):
        return a.audit_record(self.entry, self.row, self.plan, self.basis, self.files, TABLE)

    def call_operational(self):
        return a.audit_operational(self.entry, self.boundary, self.cfg, self.grant, self.files)


def mutate(fixture, vector):
    target = vector['target']
    value = fixture.value(target[4:]) if target.startswith('map:') else getattr(fixture, target)
    for key in vector['path'][:-1]:
        value = value[key]
    key = vector['path'][-1]
    if vector.get('delete'):
        del value[key]
    else:
        value[key] = copy.deepcopy(vector['value'])


def vector_checks(vectors):
    require(len(vectors) == 41, 'exact literal vector inventory differs')
    kinds = {'boundary': Fixture.call_boundary, 'record': Fixture.call_record, 'operational': Fixture.call_operational}
    exceptions = {'ValueError': ValueError, 'KeyError': KeyError, 'TypeError': TypeError}
    for vector in vectors:
        def action(vector=vector):
            fixture = Fixture()
            mutate(fixture, vector)
            kinds[vector['call']](fixture)
        check(vector['id'], action, exceptions[vector['exception']], vector['phrase'])


def recipe_checks():
    variants = [('growth192-summary', None), ('growth256-summary', None), ('central64-profiles', None)]
    variants += [(sid, size) for sid in ('largest-full-supplied', 'largest-full-searched') for size in (192, 256)]
    variants += [(sid, size) for sid in ('largest-profiles', 'central-and-largest-profiles') for size in (128, 192, 256)]
    for sid, selected in variants:
        def action(sid=sid, selected=selected):
            expected = s.stage_recipe(TABLE, sid, selected)
            require(a.stage_recipe(TABLE, sid, selected) == expected, 'fixed pure recipes differ')
            rows, _ = expected
            count = 12 if sid == 'central-and-largest-profiles' else 3 if sid.startswith('largest-full') else 6
            require(len(rows) == count and len({row['attempt_id'] for row in rows}) == count, 'recipe cardinality differs')
            require([row['repetition'] for row in rows] == [1, 2, 3] * (count // 3), 'recipe repetitions differ')
        check('G02-' + sid + '-' + str(selected), action)
    for name, sid, selected, phrase in (
        ('unknown', 'other', None, 'unknown fixed stage'),
        ('full128', 'largest-full-supplied', 128, 'selected largest full size required'),
        ('central-selected', 'central64-profiles', 192, 'central-only profiles'),
        ('string-size', 'largest-profiles', '192', 'selected largest profile size required')):
        check('G02-refuse-' + name, lambda sid=sid, selected=selected: a.stage_recipe(TABLE, sid, selected), ValueError, phrase)


def json_reference_checks():
    good = save('SYNTHETIC-evidence/prior.json', {'label': LABEL})
    prose = OUT / 'SYNTHETIC-evidence/prior.md'
    prose.write_text('# ' + LABEL + '\n')
    markdown = {'path': str(prose), 'sha256': hashlib.sha256(bounded_bytes(prose)).hexdigest()}
    real = a.Files([OUT / 'SYNTHETIC-evidence'])
    def action(kind):
        fixture = Fixture()
        admission = fixture.value('admission')
        admission['prior_data_refs'] = [markdown if kind == 'bad' else good]
        if kind == 'hash-only':
            admission['descriptive_report_applicability_reference'] = markdown
        fixture.files.real = {good['path']: real, markdown['path']: real}
        a.audit_stage_context(fixture.cfg, fixture.boundary, TABLE, fixture.files)
    check('G05-actual-JSON-prior-positive', lambda: action('good'))
    check('G05-actual-Markdown-JSON-path-refused', lambda: action('bad'), json.JSONDecodeError, 'Expecting value')
    check('G05-separate-Markdown-hash-only-positive', lambda: action('hash-only'))


def record_and_pair_checks():
    for eof in (True, False):
        def eof_case(eof=eof):
            fixture = Fixture()
            fixture.receipt['startup_eof_observed'] = eof
            result = fixture.call_record()
            require(result['startup_eof_observed'] is eof, 'EOF bool altered')
            require(result['metrics']['terminal_native_KiB'] == 50 and
                    result['metrics']['terminal_kernel_bytes'] == 50 * 1024 and
                    result['metrics']['call_seconds'] == 20 / 1e9 and
                    result['metrics']['spawn_to_terminal_collection_seconds'] == 110 / 1e9 and
                    result['metrics']['target_start_to_last_snapshot_seconds'] == 50 / 1e9 and
                    result['snapshots'] == fixture.child['snapshots'], 'scoped synthetic scalar extraction altered')
        check('G06-EOF-' + str(eof) + '-preserved', eof_case)
    def profile():
        fixture = Fixture(profile=True)
        require(fixture.call_record()['stages'] == fixture.child['stages'], 'actual event objects altered')
        require(set(fixture.child['stages'][0]) == {'stage', 'time_index', 'edge', 'monotonic_ns', 'ru_maxrss_native_KiB'},
                'fixture event fields drifted')
    check('G07-profile-events-pass-through', profile)
    def presence(profile):
        fixture = Fixture(profile=profile)
        fixture.child['stages'] = [] if profile else [{'stage': 'declaration'}]
        fixture.call_record()
    for flag in (True, False):
        check('G07-wrong-presence-' + str(flag), lambda flag=flag: presence(flag), ValueError, 'branch/profile presence mismatch')

    def pair_case(profile=True, change=None):
        primary = Fixture(profile=True) if profile else Fixture(stage_id='largest-full-supplied', selected=192)
        control = Fixture(phase='initial') if profile else Fixture()
        link = {'boundary': control.entry['boundary'], 'config': control.entry['batch_config']}
        primary.cfg['matched_unprofiled'][primary.row['attempt_id']] = link
        row, anchor = primary.call_record(), control.call_record()
        if not profile:
            row['public_result_sha256'] = h('SYNTHETIC-full-graph')
        if change:
            change(row, anchor)
        pairs, errors = a.matched_controls([row], [anchor])
        return row, anchor, pairs, errors
    check('G08-profile-f6-control-positive', lambda: require(not pair_case()[3], 'profile pair failed'))
    check('G08-full-summary8190-public-difference-positive', lambda: require(not pair_case(False)[3], 'full-summary pair failed'))
    changes = [
        ('profile-public', lambda r, c: r.update(public_result_sha256=h('different')), 'public graph'),
        ('repetition', lambda r, c: c.update(repetition=2), 'mode/geometry/case/search/repetition'),
        ('mode', lambda r, c: c['condition'].update(mode='full'), 'mode/geometry/case/search/repetition'),
        ('search', lambda r, c: c['condition'].update(search=False), 'mode/geometry/case/search/repetition'),
        ('environment', lambda r, c: c.update(environment={'different': True}), 'environment'),
        ('method-reference', lambda r, c: c['method7_reference'].update(sha256=h('wrong')), 'method7_reference'),
        ('control-reference', lambda r, c: r['matched_unprofiled']['boundary'].update(sha256=h('wrong')), None),
        ('common', lambda r, c: r.update(common_output_sha256=h('wrong')), 'common_output_sha256'),
    ]
    for name, change, phrase in changes:
        def negative(change=change, phrase=phrase):
            errors = pair_case(change=change)[3]
            require(errors and (phrase is None or any(phrase in row.get('reason', '') for row in errors)),
                    'specific paired refusal absent')
        check('G08-refuse-' + name, negative)
    def unused():
        _, anchor, _, _ = pair_case()
        _, errors = a.matched_controls([], [anchor])
        require(errors[0]['state'] == 'unused_or_mismatched_control_selection', 'unused control not reported')
    check('G08-unused-control-reported', unused)


def scalar_row(recipe, conditions):
    condition = conditions[recipe['condition_id']]['condition']
    token = json.dumps({key: condition.get(key) for key in ('shape', 'case', 'search')}, sort_keys=True)
    return {'attempt_id': recipe['attempt_id'], 'condition_id': recipe['condition_id'], 'condition': condition,
            'stage_id': recipe['stage_id'], 'profile': recipe['profile'], 'repetition': recipe['repetition'],
            'state': 'eligible_descriptive_pending_scientific_review', 'environment': {'label': LABEL},
            'input_sha256': h(token), 'input_arrays': {'label': token}, 'branches': [['SYNTHETIC']],
            'output_hashes': {'label': token}, 'common_output_sha256': h(token),
            'public_result_sha256': h(token + condition['mode']), 'matched_unprofiled': None,
            'process_identity': {'boot_id': LABEL, 'pid': 100 + recipe['serial_index'], 'start_ticks': recipe['serial_index']},
            'metrics': {key: 1 for key in a.METRICS}}


def summary_checks():
    recipes, conditions = s.stage_recipe(TABLE, 'growth192-summary', None)
    rows = [scalar_row(row, conditions) for row in recipes[:3]]
    cid = rows[0]['condition_id']
    one = {'conditions': {cid: conditions[cid]}}
    check('G09-three-repeat-positive', lambda: require(a.summarize(one, rows)[0]['metrics'] is not None, 'complete group absent'))
    cases = [('missing', rows[:2], 'missing/invalid/duplicate repetition'),
             ('duplicate', [rows[0]] * 3, 'missing/invalid/duplicate repetition')]
    for name, field in (('reused-process', 'process_identity'), ('branch', 'branches'),
                        ('input', 'input_sha256'), ('public', 'public_result_sha256')):
        changed = copy.deepcopy(rows)
        changed[1][field] = copy.deepcopy(changed[0][field]) if field == 'process_identity' else 'SYNTHETIC-mismatch'
        cases.append((name, changed, 'not three distinct' if field == 'process_identity' else 'repeat mismatch'))
    for name, changed, phrase in cases:
        def action(changed=changed, phrase=phrase):
            group = a.summarize(one, changed)[0]
            require(group['metrics'] is None and any(phrase in reason for reason in group['reasons']), 'incomplete group got statistics')
        check('G09-' + name + '-no-partial-median', action)


def main_case(name, partial=False, approved=True, bad=False, output_refusal=False, pin_refusal=False, disabled=False):
    recipes, conditions = s.stage_recipe(TABLE, 'growth192-summary', None)
    source_files = a.Files
    tiny = save('SYNTHETIC-evidence/main-tiny.json', {'label': LABEL})
    real = source_files([OUT / 'SYNTHETIC-evidence'])
    class MainFiles:
        def __init__(self, roots):
            self.roots, self.audit = tuple(Path(root).resolve() for root in roots), []
        def read(self, ref, **kwargs):
            if disabled or pin_refusal:
                forbidden()
            path = Path(ref['path'])
            if path == Path(tiny['path']):
                return real.read(ref, **kwargs)
            if path.name == 'source-identities.json':
                return {'input_sha256': {}, 'source_sha256': {}}
            if path.name == 'admission-table.json':
                return TABLE
            if path.name == 'qualified-method7-source-basis.json':
                return {'candidate': {'head': LABEL}, 'material_hashes': {'label': h(LABEL)}}
            if path.name == 'SYNTHETIC-batch-config.json':
                return {'selected_largest_size': None}
            return None  # Exact original/binder source lookups substituted, no imports/effects.
    output = OUT / ('SYNTHETIC-main-' + name)
    cfg = {'protocol': 'WS116-fixed-stage-report-v1', 'root_analysis_approved': not disabled,
           'data_window_closed': True, 'analysis_scope': 'one_fixed_stage',
           'source_manifest_sha256': a.SOURCE_MANIFEST, 'schema_manifest_sha256': a.SCHEMA_MANIFEST,
           'original_extractor_sha256': a.ORIGINAL_SHA, 'stage_binder_sha256': a.STAGE_SHA,
           'table_sha256': a.TABLE_SHA, 'basis_sha256': a.BASIS_SHA, 'stage_id': 'growth192-summary',
           'selected_largest_size': None, 'allow_partial_selection': approved if partial else False,
           'stage_selection': [{'phase': 'stage', 'attempt_id': row['attempt_id'],
                                'batch_config': {'path': str(OUT / 'SYNTHETIC-batch-config.json'), 'sha256': h('config')}}
                               for row in (recipes[:1] if partial else recipes)], 'control_selection': [],
           'excluded_records': [{'phase': 'failed', 'reason': LABEL, 'availability': 'available',
                                 'evidence': [{**tiny, 'sha256': '0' * 64}]}] if bad else [],
           'historical_rm84_inventory': [{'phase': 'historical', 'reason': LABEL, 'availability': 'unknown'}],
           'allowed_evidence_roots': [str(OUT / 'SYNTHETIC-evidence')], 'protected_output_roots': ['/SYNTHETIC-protected'],
           'output_root': str(INPUTS if output_refusal else output)}
    if pin_refusal:
        cfg['stage_binder_sha256'] = h('wrong-pin')
    ref = save('SYNTHETIC-config-' + name + '.json', cfg)
    def extract(entry, *args):
        return scalar_row(next(row for row in recipes if row['attempt_id'] == entry['attempt_id']), conditions)
    with replace(sys, argv=[str(TARGET), '--config', ref['path'], '--config-sha256', ref['sha256']]), replace(
            a, Files=MainFiles, audit_selection=forbidden if output_refusal or pin_refusal or disabled else extract):
        code = a.main()
    summary = json.loads(bounded_bytes(output / 'summary.json'))
    require(summary['fixed_stage_descriptive_complete'] is (not partial), 'actual main descriptive status differs')
    require(summary['referenced_evidence_audit_valid'] is (not bad), 'actual main bad-reference status differs')
    require(summary['analysis_success'] is (not partial and not bad) and code == (1 if partial or bad else 0), 'actual main exit mismatch')
    require(summary['historical_rm84_inventory'][0]['evidence_errors'] == [], 'historical unknown fabricated corruption')
    (output / 'SYNTHETIC-NEVER-SCIENTIFIC.txt').write_text(LABEL + '\n')


def operational_checks():
    for phase in ('initial', 'stage'):
        def action(phase=phase):
            fixture = Fixture(phase=phase)
            result = fixture.call_operational()
            require(result['exact_binder_final_horizon_check_unix_ns'] is None, 'invented end timestamp')
            require(result['source_sha256'] == fixture.source, 'wrong binder scope')
        check('G11-operational-' + phase + '-recorded-positive', action)


def run_cases(vectors):
    recipe_checks()
    check('G03-actual-shaped-stage-positive', lambda: Fixture().call_boundary())
    check('G03-actual-shaped-f6-control-positive', lambda: Fixture(phase='initial').call_boundary())
    vector_checks(vectors)
    json_reference_checks()
    record_and_pair_checks()
    summary_checks()
    operational_checks()
    check('G01-disabled-before-evidence', lambda: main_case('disabled', disabled=True), ValueError, 'ROOT post-window analysis release absent')
    check('G01-wrong-source-pin-before-evidence', lambda: main_case('wrong-pin', pin_refusal=True), ValueError, 'config source/table/basis differs')
    check('G01-output-root-before-extraction', lambda: main_case('output-refusal', output_refusal=True), ValueError, 'output would modify source/evidence/worktree')
    check('G10-actual-main-six-SYNTHETIC-complete-clean', lambda: main_case('complete'))
    check('G10-actual-main-six-complete-excluded-badhash-exit1', lambda: main_case('excluded-bad', bad=True))
    check('G12-explicit-one-SYNTHETIC-row-incomplete-exit1', lambda: main_case('partial', partial=True))
    check('G12-unapproved-partial-before-extraction', lambda: main_case('partial-unapproved', partial=True, approved=False),
          ValueError, 'partial data requires explicit ROOT analysis selection')


def main():
    global OUT, a, s, TABLE, BASIS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--release-sha256', required=True)
    args = parser.parse_args()
    require(Path(__file__).resolve() == DRIVER and sys.flags.isolated and sys.dont_write_bytecode,
            'canonical driver and pinned Python -I -B required')
    raw = bounded_bytes(args.release, 65536)
    require(hashlib.sha256(raw).hexdigest() == args.release_sha256, 'release hash differs')
    release = json.loads(raw)
    require(release['protocol'] == 'WS116-finite-stage-guard-release-v1' and release['root_approved'] is True and
            release['window_closed'] is True and release['approved_action'] == 'finite_synthetic_only' and
            release['run_id'] == 'ws116-stage-guards-a1', 'future explicit ROOT release absent')
    OUT = Path(release['output_root']).resolve()
    require(OUT == ROOT / 'focused-stage-guards-execution/SYNTHETIC-ws116-stage-guards-a1', 'unexpected unique synthetic output')
    pins = release['source_pins']
    require(set(pins) == set(FIXED_PINS) | {str(DRIVER), str(VECTORS)} and
            all(pins[path] == digest for path, digest in FIXED_PINS.items()), 'exact frozen source-pin set differs')
    def verify():
        for path, digest in pins.items():
            require(hashlib.sha256(bounded_bytes(path)).hexdigest() == digest, 'source pin changed: ' + path)
        require(hashlib.sha256(bounded_bytes(args.release, 65536)).hexdigest() == args.release_sha256,
                'ROOT release bytes changed')
    verify()
    OUT.mkdir(parents=True, exist_ok=False)
    save('SYNTHETIC-purpose.json', {'label': LABEL, 'release_sha256': args.release_sha256, 'source_pins': pins})
    install_blocks({**pins, str(args.release.resolve()): args.release_sha256})
    status = 'FAILED'
    error = None
    try:
        a = load_source('ws116_canonical940', TARGET)
        s = load_source('ws116_frozen8190_recipe_only', BINDER)
        s.subprocess = types.SimpleNamespace(run=forbidden, Popen=forbidden, check_output=forbidden)
        for name, value in list(vars(s).items()):
            if isinstance(value, types.FunctionType) and name not in {'stage_recipe', 'require'}:
                setattr(s, name, forbidden)
        TABLE = json.loads(bounded_bytes(INPUTS / 'admission-table.json'))
        BASIS = json.loads(bounded_bytes(INPUTS / 'qualified-method7-source-basis.json'))
        vectors = json.loads(bounded_bytes(VECTORS, 262144))
        require(vectors['label'] == LABEL, 'fixture label differs')
        run_cases(vectors['vectors'])
        require(len(RESULTS) == vectors['expected_cases'] == 95, 'exact finite case inventory differs')
        require(not BLOCKED, 'blocked attempt invalidates invocation')
        status = 'PASS_FINITE_SYNTHETIC_ONLY'
    except BaseException as failure:
        error = {'type': type(failure).__name__, 'reason': str(failure)}
        raise
    finally:
        try:
            verify()
        except BaseException as failure:
            status = 'FAILED_SOURCE_IDENTITY'
            error = {'type': type(failure).__name__, 'reason': str(failure)}
        files = {path: {'sha256': hashlib.sha256(bounded_bytes(path, 2 * 1024 * 1024)).hexdigest(),
                        'logical_bytes': Path(path).stat().st_size} for path in sorted(WRITTEN) if Path(path).is_file()}
        require(len(files) <= 256 and sum(item['logical_bytes'] for item in files.values()) <= 32 * 1024 * 1024,
                'synthetic cumulative disk bound exceeded')
        save('summary.json', {'label': LABEL, 'status': status, 'error': error, 'checks': len(RESULTS),
                             'matched': all(row['matched'] for row in RESULTS), 'blocked_effect_attempts': BLOCKED,
                             'source_pins': pins, 'files_before_summary': files, 'actual_scientific_data': False,
                             'actual_cost': 'UNKNOWN', 'actual_tokens': 'UNKNOWN'})
    return 0 if status == 'PASS_FINITE_SYNTHETIC_ONLY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
