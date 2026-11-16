"""ROOT's final original24 centralworkflow/profile members, ordinals55–78; no retry or growth."""

from pathlib import Path
import hashlib
import json
import subprocess
import time

B = Path('/workspace/work/campaign/evidence/118')
METHOD = B / 'resource-method-final-source-preparation/source/workflow'
RELEASE_PATH = B / 'ROOT-final24-workflow-limited-release-1.json'
assert RELEASE_PATH.exists(), 'HOLD: scientific scope/current limited release not yet applied'
release = json.loads(RELEASE_PATH.read_text())
assert release['approved_for_exact_final24_scheduled_members'] is True
schedule = json.loads((B / 'ROOT-global78-schedule-before-observation-1.json').read_text())
rows = schedule['rows'][54:78]
assert len(rows)==24 and [r['ordinal'] for r in rows]==list(range(55,79))
assert all(r['route']=='workflow' and r['profile']==(r['group'] in (5,6)) for r in rows)
DEST = B / 'ROOT-final24-workflow-actual-1'
DEST.mkdir(exist_ok=False)
CID = '11bb9a3651cd9de282de77fd1ede1a807bcff83aa4e6d6322aac8a1d5da1cd7b'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def owned_call(argv, envelope, path):
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    started = time.monotonic()
    intent = {'argv':argv,'owned_outer_pid':p.pid,'owner_pid':__import__('os').getpid(),
              'outer_envelope_seconds':envelope,'started_monotonic':started,'automatic_kill':False}
    path.with_suffix('.intent.json').write_text(json.dumps(intent,indent=2)+'\n')
    try:
        stdout,stderr = p.communicate(timeout=envelope)
    except subprocess.TimeoutExpired as error:
        intent.update(status='UNKNOWN_HOLD_OUTER_EXPIRED',partial_stdout=(error.stdout or b'').decode(errors='replace'),
                      partial_stderr=(error.stderr or b'').decode(errors='replace'),next_member='PROHIBITED')
        path.with_suffix('.HOLD.json').write_text(json.dumps(intent,indent=2)+'\n')
        print(json.dumps({'HOLD':str(path.with_suffix('.HOLD.json')),'outer_pid':p.pid}),flush=True)
        stdout,stderr = p.communicate()  # Keep exact wrapper wait ownership alive for diagnosis.
        intent.update(eventual_returncode=p.returncode,eventual_stdout=stdout.decode(errors='replace'),
                      eventual_stderr=stderr.decode(errors='replace'))
        path.with_suffix('.HOLD-closed.json').write_text(json.dumps(intent,indent=2)+'\n')
        raise RuntimeError('Outer expiry remains HOLD; no automatic continuation')
    result={**intent,'returncode':p.returncode,'stdout':stdout.decode(),'stderr':stderr.decode(),
            'outer_reaped':True,'elapsed_seconds':time.monotonic()-started}
    path.write_text(json.dumps(result,indent=2)+'\n')
    assert p.returncode==0,str(path)
    return result


META = r'''from pathlib import Path
import sys,json,os,time,subprocess,hashlib
root=Path(sys.argv[1]);method=Path(sys.argv[2]);expected=sys.argv[3]
assert __debug__ and sys.flags.optimize==0
assert Path(sys.executable).resolve().as_posix()=='/workspace/.simrecon-tools/python/cpython-3.13.12-linux-x86_64-gnu/bin/python3.13'
assert hashlib.sha256((method/'observer.py').read_bytes()).hexdigest()==expected
sys.path.insert(0,str(method));import observer
assert Path(observer.__file__).resolve()==method/'observer.py'
parent=method/('raw-'+sys.argv[4]);parent=parent if parent.exists() else method
assert parent.resolve()==parent and parent.stat().st_uid==os.getuid() and os.access(parent,os.W_OK)
print(json.dumps({'observed_at_unix_ns':time.time_ns(),'context':observer.context(root),'material_hashes':observer.material_hashes(root),'candidate':{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root,text=True).strip(),'tracked_diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=root)).hexdigest()},'FULL_status':subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=root,text=True).strip(),'python_resolved':str(Path(sys.executable).resolve()),'debug':__debug__,'optimize':sys.flags.optimize,'uid':os.getuid(),'output_parent_canonical_writable_owned':True,'scope':'Actual per-case ROOT context/material metadata only; zero workflow calls'}))
'''

manifest = json.loads((METHOD/'manifest.json').read_text())
assert manifest['approved'] is True and manifest['execution_status']=='released_exact_case'
observer_sha = sha(METHOD/'observer.py')
assert observer_sha==release['workflow_observer_sha256']
children=[]
results=[]
reference=None
mode_references={}
unprofiled={}
for row in rows:
    role=row['role'];subject=manifest['subjects'][role];root=subject['root'];attempt=row['attempt_id']
    out=METHOD/('raw-'+role)/attempt
    assert not out.exists()
    prefix=['/usr/local/bin/docker','exec','--user','1000:1000','-w',root,CID,'/usr/bin/env',
            'PYTHONPATH='+root+'/scripts/source_free_sitecustomize','PYTEST_PLUGINS=pytest_plugin',
            'PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1',
            'MKL_NUM_THREADS=1','NUMEXPR_NUM_THREADS=1',root+'/.venv/bin/python']
    context_path=DEST/(attempt+'-context.json')
    meta=owned_call(prefix+['-c',META,root,str(METHOD),observer_sha,role],60,context_path)
    actual=json.loads(meta['stdout']);assert actual['candidate']==subject['identity']
    expected_status={'?? docs/packets/issue-118-direct-resource-protocol.md','?? tests/preparation_harmonic_memory_benchmark.py'} if role=='parent' else set()
    assert set(actual['FULL_status'].splitlines())==expected_status
    cg=actual['context']['cgroup'];assert 'error' not in cg
    stop=512*1024**2;reserve=512*1024**2;minimum=1024**3
    thresholds={r['path']:int(r['memory.max'])-1024**3 for r in cg['visible_ancestors']}
    assert thresholds and all(int(r['memory.current'])+stop+reserve<thresholds[r['path']]<int(r['memory.max']) for r in cg['visible_ancestors'])
    available=int(next(line.split()[1] for line in actual['context']['meminfo'].splitlines() if line.startswith('MemAvailable:')))*1024
    assert available>minimum and actual['context']['disk_available_bytes']>2*1024**3
    exposed={k:cg[k] for k in ['membership','mount_root','mount','namespace']}
    exposed['visible_memory_max']={r['path']:r['memory.max'] for r in cg['visible_ancestors']}
    domain={'scope':'WS116-exposed-domain-conditional-v1','external_ancestors':'unknown_unobservable',
            'conditional_rationale':'ROOT exact original central64 searched workflow/profile member. Retained finite core, independent source/scientific scope acceptance, P3startup and actual first scheduled pair P4 role correspondence precede this call. This is not final scientific qualification. Frozen T1/D3/Z8/Y64/X64/P5/O3/L2/A1 caller/output and full/summary retention are source-admitted; profile observation adds metadata/time/memory perturbation and requires same-role/repetition unprofiled controls; proposed256MiB child plus128MiB native/allocator allowance fit512MiB process stop, with512MiB reserve, host1GiB minimum, actual visible ancestor stops1GiB below max and2GiB free disk. Allowances are conservative operating decisions, not RSS predictions established by data or guarantees. No competing controlled test/install/benchmark; hidden ancestors/actors and early startup/abrupt-loss windows remain conditional/HOLD. No retry/growth.',
            'correspondence_evidence':{'path':str(context_path),'sha256':sha(context_path),'observed_at_unix_ns':actual['observed_at_unix_ns'],'maximum_age_seconds':300},
            'expected_exposed':exposed,'predicted_child_peak_bytes':256*1024**2,
            'native_allocator_allowance_bytes':128*1024**2,'reserve_bytes':reserve}
    grant={'protocol':'PH118-workflow-grant-v1','approved':True,'numerical_release':True,'accepted_112_then_115':True,
           'subject':{'role':role,'worktree':root,'python':root+'/.venv/bin/python','diagnostic_environment':{'inherited_pythonpath':None,'inherited_pytest_plugins':None,'PYTHONPATH':root+'/scripts/source_free_sitecustomize','PYTEST_PLUGINS':'pytest_plugin'}},
           'proofs':release['proofs'],'representation_preflight':{'accepted':True,'evidence':release['representation_evidence']},
           'headroom_evidence':{'path':str(context_path),'sha256':sha(context_path)},
           'deadline_seconds':240,'process_stop_bytes':stop,'host_min_available_bytes':minimum,
           'terminate_grace_seconds':1.0,'kill_reap_seconds':5.0,'max_child_record_bytes':33554432,
           'sample_interval_seconds':0.01,'python_resolved':actual['python_resolved'],'candidate':actual['candidate'],
           'material_hashes':actual['material_hashes'],'startup_timeout_seconds':5.0,'startup_pipe_bytes':1024,
           'launch_nonce':attempt,'condition_id':row['condition_id'],'repetition':row['repetition'],'profile':row['profile'],
           'ancestor_stop_bytes':thresholds,'resource_domain':domain}
    gp=DEST/(attempt+'-grant.json');gp.write_text(json.dumps(grant,indent=2)+'\n')
    tool=owned_call(prefix+[str(METHOD/'run_attempt.py'),'--revision',role,'--attempt-id',attempt,'--grant',str(gp)],300,DEST/(attempt+'-tool.json'))
    receipt=json.loads((out/'receipt.json').read_text());child=json.loads((out/'stdout.json').read_text())
    assert receipt['status']=='complete_child_observed_pending_scientific_qualification'
    assert receipt['material_identity_matches'] and receipt['startup_parent_fds_closed']
    assert not receipt.get('wait_ownership_lost') and not receipt.get('signals')
    assert all(k not in receipt for k in ['cleanup_gap','postflight_gap','stop_reason'])
    assert receipt['terminal']['returncode']==0 and receipt['terminal']['pid']==child['pid']
    assert receipt['observer_pid']!=child['pid']
    assert receipt['terminal']['ru_maxrss_native_units']=='Linux KiB'
    assert receipt['terminal']['ru_maxrss_multiplier_to_bytes']==1024
    assert child['status']=='finite_observation_pending_qualification' and child['finite_common_fields']
    assert child['numpy']=='2.5.3' and child['scipy']=='1.18.1' and child['scipy_fft_default_workers']==1
    assert child['product_module']=='src/simrecon/__init__.py'
    assert bool(child['stages']) is row['profile']
    if reference is None:reference=child
    assert child['input_sha256']==reference['input_sha256'] and child['input_arrays']==reference['input_arrays']
    assert child['common_output_sha256']==reference['common_output_sha256'] and child['output_hashes']==reference['output_hashes']
    assert child['numpy_backend']==reference['numpy_backend']
    previous=mode_references.setdefault(row['condition_id'],child)
    assert child['public_result_sha256']==previous['public_result_sha256']
    key=(role,row['condition_id'],row['repetition'])
    control=None
    if row['profile']:
        assert key in unprofiled
        control=unprofiled[key]
        assert child['input_sha256']==control['child']['input_sha256'] and child['output_hashes']==control['child']['output_hashes']
        assert child['public_result_sha256']==control['child']['public_result_sha256']
    else:unprofiled[key]={'child':child,'output':str(out),'receipt_sha256':sha(out/'receipt.json'),'child_sha256':sha(out/'stdout.json')}
    results.append({'ordinal':row['ordinal'],'role':role,'attempt_id':attempt,'output':str(out),
                    'receipt_sha256':sha(out/'receipt.json'),'child_sha256':sha(out/'stdout.json'),
                    'grant_sha256':sha(gp),'terminal0_closed':True,'counted_as_original_scheduled_member':True})
    results[-1]['profile']=row['profile']
    results[-1]['unprofiled_control_same_subject_mode_repetition']=None if control is None else {k:v for k,v in control.items() if k!='child'}
    children.append(child)
    (DEST/(attempt+'-actual-observation.json')).write_text(json.dumps({'scope':'P4 exact scheduled first workflow main/exec/PID/map/native-unit/closed ownership correspondence only, no scientific/resource conclusion','result':results[-1],'numpy_backend':child['numpy_backend'],'numpy':child['numpy'],'scipy':child['scipy'],'scipy_fft_default_workers':child['scipy_fft_default_workers']},indent=2)+'\n')
    print(json.dumps(results[-1]),flush=True)

assert len(children)==24 and len(unprofiled)==12
summary={'scope':'Exactly ordinals55–78 of original78,12unprofiled+12profiled; actual observations pending scientific qualification','results':results,'all24_complete':True,'prior_original_slots_required':54,'all_original_slots_total_after_success':78,'all_input_common_and_within_mode_public_fingerprints_equal':True,'literal_full_output_byte_comparison':False,'both_actual_backend_contexts_collected':True,'ownership':'all terminal0, startupFDsclosed, exact child reaped, outerreaped; no cleanupgap','next_release':'WINDOW CLOSED after24; ROOT all78collection/scientific review, no additional observations'}
p=DEST/'ROOT-result-index.json';p.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'complete':True,'index':str(p),'sha256':sha(p)}),flush=True)
