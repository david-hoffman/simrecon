"""ROOT's frozen original DIRECT ordinals13–54; no retry, growth or arbitrary target."""

from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

B=Path('/workspace/work/campaign/evidence/118')
METHOD=B/'resource-method-final-source-preparation/source/direct'
rp=B/'ROOT-direct42-limited-release-1.json'
assert rp.exists(), 'HOLD: no exact direct release applied'
release=json.loads(rp.read_text());assert release['approved_for_exact_direct42'] is True
rows=json.loads((B/'ROOT-global78-schedule-before-observation-1.json').read_text())['rows'][12:54]
assert len(rows)==42 and all(r['route']=='direct' and not r['profile'] for r in rows)
assert [r['ordinal'] for r in rows]==list(range(13,55))
DEST=B/'ROOT-direct42-actual-1';DEST.mkdir(exist_ok=False)
CID='11bb9a3651cd9de282de77fd1ede1a807bcff83aa4e6d6322aac8a1d5da1cd7b'
manifest=json.loads((METHOD/'manifest.json').read_text())
assert manifest['approved'] is True and manifest['execution_status']=='released_exact_case'
expectations=json.loads(Path(release['direct_expectations']['path']).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


assert sha(release['direct_expectations']['path'])==release['direct_expectations']['sha256']


def owned_call(argv,envelope,path):
    p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    started=time.monotonic();intent={'argv':argv,'owner_pid':os.getpid(),'owned_outer_pid':p.pid,
        'outer_envelope_seconds':envelope,'automatic_kill':False,'started_monotonic':started}
    path.with_suffix('.intent.json').write_text(json.dumps(intent,indent=2)+'\n')
    try:stdout,stderr=p.communicate(timeout=envelope)
    except subprocess.TimeoutExpired as error:
        intent.update(status='UNKNOWN_HOLD_OUTER_EXPIRED',partial_stdout=(error.stdout or b'').decode(errors='replace'),partial_stderr=(error.stderr or b'').decode(errors='replace'),next_member='PROHIBITED')
        path.with_suffix('.HOLD.json').write_text(json.dumps(intent,indent=2)+'\n')
        print(json.dumps({'HOLD':str(path.with_suffix('.HOLD.json')),'outer_pid':p.pid}),flush=True)
        stdout,stderr=p.communicate()  # Preserve owner until exact wrapper is reaped; ROOT diagnoses, no next.
        intent.update(eventual_returncode=p.returncode,eventual_stdout=stdout.decode(errors='replace'),eventual_stderr=stderr.decode(errors='replace'))
        path.with_suffix('.HOLD-closed.json').write_text(json.dumps(intent,indent=2)+'\n')
        raise RuntimeError('Outer expiry remains HOLD; no automatic continuation')
    result={**intent,'returncode':p.returncode,'stdout':stdout.decode(),'stderr':stderr.decode(),
            'outer_reaped':True,'elapsed_seconds':time.monotonic()-started}
    path.write_text(json.dumps(result,indent=2)+'\n')
    assert p.returncode==0,str(path)
    return result


META=r'''from pathlib import Path
import sys,json,os,time,subprocess,hashlib
root=Path(sys.argv[1]);method=Path(sys.argv[2])
assert __debug__ and sys.flags.optimize==0
for name,expected in [('observer.py',sys.argv[3]),('direct_binding.py',sys.argv[4])]:assert hashlib.sha256((method/name).read_bytes()).hexdigest()==expected
sys.path.insert(0,str(method));import observer,direct_binding
assert Path(observer.__file__).resolve()==method/'observer.py' and Path(direct_binding.__file__).resolve()==method/'direct_binding.py'
parent=method/'raw';parent=parent if parent.exists() else method
assert parent.resolve()==parent and parent.stat().st_uid==os.getuid() and os.access(parent,os.W_OK)
print(json.dumps({'observed_at_unix_ns':time.time_ns(),'context':observer.context(root),'material_hashes':direct_binding.material_hashes(root),'candidate':{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root,text=True).strip(),'tracked_diff_sha256':hashlib.sha256(subprocess.check_output(['git','diff','--binary','HEAD'],cwd=root)).hexdigest()},'FULL_status':subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all'],cwd=root,text=True).strip(),'python_resolved':str(Path(sys.executable).resolve()),'debug':__debug__,'optimize':sys.flags.optimize,'uid':os.getuid(),'output_parent_canonical_writable_owned':True,'scope':'Actual ROOT per-direct-member metadata only, zero public scientific calls'}))
'''

observer_sha=sha(METHOD/'observer.py');binding_sha=sha(METHOD/'direct_binding.py')
assert observer_sha==release['direct_observer_sha256'] and binding_sha==release['direct_binding_sha256']
results=[];references={};parent_qualified={};pids=set()
for row in rows:
    role=row['role'];case=row['condition_id'];rep=row['repetition'];attempt=row['attempt_id']
    frozen=manifest['subjects'][role];root=frozen['root'];out=METHOD/'raw'/attempt
    assert not out.exists()
    if role=='candidate':assert case in parent_qualified, 'P4 actual first parent case must qualify before candidate'
    prefix=['/usr/local/bin/docker','exec','--user','1000:1000','-w',root,CID,'/usr/bin/env',
            'PYTHONPATH='+root+'/scripts/source_free_sitecustomize','PYTEST_PLUGINS=pytest_plugin',
            'PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1',
            'MKL_NUM_THREADS=1','NUMEXPR_NUM_THREADS=1',root+'/.venv/bin/python']
    cp=DEST/(attempt+'-context.json')
    meta=owned_call(prefix+['-c',META,root,str(METHOD),observer_sha,binding_sha],60,cp)
    actual=json.loads(meta['stdout']);assert actual['candidate']==frozen['identity']
    expected_status={'?? docs/packets/issue-118-direct-resource-protocol.md','?? tests/preparation_harmonic_memory_benchmark.py'} if role=='parent' else set()
    assert set(actual['FULL_status'].splitlines())==expected_status
    large=case.endswith('128')
    stop=(1024 if large else 512)*1024**2;reserve=stop;minimum=(2 if large else 1)*1024**3
    prediction=(512 if large else 256)*1024**2;native=(256 if large else 128)*1024**2
    cg=actual['context']['cgroup'];assert 'error' not in cg
    thresholds={r['path']:int(r['memory.max'])-1024**3 for r in cg['visible_ancestors']}
    assert thresholds and all(int(r['memory.current'])+stop+reserve<thresholds[r['path']]<int(r['memory.max']) for r in cg['visible_ancestors'])
    available=int(next(line.split()[1] for line in actual['context']['meminfo'].splitlines() if line.startswith('MemAvailable:')))*1024
    assert available>minimum and actual['context']['disk_available_bytes']>8*1024**3
    exposed={k:cg[k] for k in ['membership','mount_root','mount','namespace']}
    exposed['visible_memory_max']={r['path']:r['memory.max'] for r in cg['visible_ancestors']}
    domain={'scope':'WS116-exposed-domain-conditional-v1','external_ancestors':'unknown_unobservable',
        'conditional_rationale':'ROOT exact original PH118 DIRECT member, not new scale/retry. Same accepted source/scientific finite scope and P2 retained core/P3actual startup precede call; actual role workflow backend context and fully fixed direct provenance/environment frozen BEFORE first direct. First parent for each exactcase supplies limited P4 new direct parser/argv/FD/PID/retention/native correspondence; candidate awaits that actual passing parent. Source retained raw/settings/off/maps/known setup/transfer/parameters/result, generators/hash/JSON/allocator/native/bootstrap/observer/disk all remain in total accounting.64/tiny/context proposed256MiB+128MiB native allowance below512MiB stop;128 proposed512MiB+256MiB below1GiB stop. Reserve equals stop, hostminimum1/2GiB, everyactualvisibleancestor stop maxminus1GiB, current+stop+reserve belowthreshold. These are conservative unqualified operating allowances, not measured predictions/fit/product/human caps.1200s childwatch and1320s ownedouter forALL7bothroles, source-admitted512MiB/1GiB controlsidenticalpercase. Diskfree8GiB covers conservative sampler/JSON/log workingallowance, not numericalarray export; no disk arrays. No competing controlled numerics/tests/install/benchmark. Hidden ancestors/actors, startup beforehooks, spawn-before-marker and abruptGit/outerloss remain conditional/HOLD. No automatic retry/growth.',
        'correspondence_evidence':{'path':str(cp),'sha256':sha(cp),'observed_at_unix_ns':actual['observed_at_unix_ns'],'maximum_age_seconds':300},
        'expected_exposed':exposed,'predicted_child_peak_bytes':prediction,'native_allocator_allowance_bytes':native,'reserve_bytes':reserve}
    proofs=dict(release['proofs'])
    if role=='candidate':proofs['parent_case_qualification']=parent_qualified[case]
    subject={'role':role,'worktree':root,'python':root+'/.venv/bin/python','module_root':root+'/src/simrecon',
        'revision':frozen['identity']['head'],'tree':frozen['identity']['tree'],'dirty':False,
        'hashes':manifest['adapter_hashes'],'diagnostic_environment':{'inherited_pythonpath':None,'inherited_pytest_plugins':None,'PYTHONPATH':root+'/scripts/source_free_sitecustomize','PYTEST_PLUGINS':'pytest_plugin'},
        'expected_provenance':expectations['roles'][role]['provenance'],'expected_environment':expectations['roles'][role]['environment']}
    grant={'protocol':'PH118-direct-grant-v1','approved':True,'numerical_release':True,'accepted_112_then_115':True,
        'subject':subject,'proofs':proofs,'representation_preflight':{'accepted':True,'evidence':release['representation_evidence']},
        'headroom_evidence':{'path':str(cp),'sha256':sha(cp)},'deadline_seconds':1200,'process_stop_bytes':stop,
        'host_min_available_bytes':minimum,'terminate_grace_seconds':1.0,'kill_reap_seconds':5.0,'max_child_record_bytes':33554432,
        'sample_interval_seconds':0.01,'python_resolved':actual['python_resolved'],'candidate':actual['candidate'],
        'material_hashes':actual['material_hashes'],'startup_timeout_seconds':5.0,'startup_pipe_bytes':1024,
        'launch_nonce':attempt,'condition_id':case,'repetition':rep,'profile':False,'ancestor_stop_bytes':thresholds,'resource_domain':domain}
    gp=DEST/(attempt+'-grant.json');gp.write_text(json.dumps(grant,indent=2)+'\n')
    tool=owned_call(prefix+[str(METHOD/'run_direct_attempt.py'),'--subject-root',root,'--attempt-id',attempt,'--grant',str(gp)],1320,DEST/(attempt+'-tool.json'))
    receipt=json.loads((out/'receipt.json').read_text());child=json.loads((out/'stdout.json').read_text());spec=json.loads((out/'spec.json').read_text())
    assert receipt['status']=='complete_child_observed_pending_scientific_qualification'
    assert receipt['material_identity_matches'] and receipt['startup_parent_fds_closed']
    assert not receipt.get('wait_ownership_lost') and not receipt.get('signals')
    assert all(k not in receipt for k in ['cleanup_gap','postflight_gap','stop_reason'])
    assert receipt['terminal']['returncode']==0 and receipt['terminal']['exit_code']==0
    pid=receipt['terminal']['pid'];assert pid not in pids and pid!=receipt['observer_pid'];pids.add(pid)
    assert receipt['terminal']['ru_maxrss_native_units']=='Linux KiB' and receipt['terminal']['ru_maxrss_multiplier_to_bytes']==1024
    assert child['status']=='pass' and child['case']==case and child['role']==role and child['repetition']==rep
    assert child['provenance']==subject['expected_provenance']
    assert {k:child[k] for k in ['versions','backend','scipy_fft_default_workers']}==subject['expected_environment']
    assert spec['launch']['target_argv'][1]==root+'/tests/preparation_harmonic_memory_benchmark.py'
    assert child['public_fingerprints']['inputs']==child['public_fingerprints']['inputs_after']
    ref=references.setdefault(case,child)
    assert child['public_fingerprints']==ref['public_fingerprints'], 'Exact predeclared case input/result fingerprints differ; HOLD no next'
    assert child['witness']==ref['witness']
    result={'ordinal':row['ordinal'],'role':role,'condition_id':case,'repetition':rep,'attempt_id':attempt,'output':str(out),
        'target_pid':pid,'observer_pid':receipt['observer_pid'],'receipt_sha256':sha(out/'receipt.json'),
        'child_sha256':sha(out/'stdout.json'),'grant_sha256':sha(gp),'terminal0_closed':True,
        'elapsed_target_seconds':child['elapsed_target_seconds'],'terminal_native_KiB':receipt['terminal']['rusage_native']['ru_maxrss'],
        'public_fingerprints':child['public_fingerprints'],'counted_as_original_scheduled_member':True}
    results.append(result)
    if role=='parent' and case not in parent_qualified:
        qp=DEST/('ROOT-first-parent-'+case+'-actual-case-correspondence.json')
        qp.write_text(json.dumps({'scope':'P4 limited actual full DIRECT interface correspondence on first required parent case; no result science/peak acceptance, no duplicated trial','result':result,'provenance_matches_complete_frozen_expectation':True,'backend_matches_pre_direct_frozen_actual_workflow_context':True,'same_owned_target_argv_exclusive_stdout_preexec_readiness_and_terminal':True,'native_KiB_conversion_and_cumulative_snapshots_structural_checks':True,'normal_metadata_Git_returned':'same unchanged successful provenance helper path, normal subprocess.run waits; abruptloss remainsHOLD','direct_record_has_no_self_PID_nonce_timestamps':'external trusted argv/FD/terminal/provenance linkage only; no invented selfattestation','ownership':'terminal0/singleexactwait4/startupFDclosed/no lostwait/no cleanupgap/outerreaped','actual_scientific_result':'pending later independent SCI'},indent=2)+'\n')
        parent_qualified[case]={'path':str(qp),'sha256':sha(qp)}
    (DEST/'ROOT-progress.json').write_text(json.dumps({'scope':'Non-authoritative live progress; immutable per-rowraw/grant/tool remainprimary','completed':len(results),'results':results,'parent_case_qualification':parent_qualified},indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['ordinal','role','condition_id','repetition','target_pid','elapsed_target_seconds','terminal_native_KiB','receipt_sha256']}),flush=True)

assert len(results)==42 and len(parent_qualified)==7 and len(pids)==42
summary={'scope':'Exactly originalDIRECT42 ordinals13–54, all3matchedpairspercase, no retry/additionalcase; independent scientific qualification pending','results':results,'all42_complete':True,'percase_canonical_input_after_and_result_fingerprints_equal':True,'literal_full_output_byte_comparison':False,'all7_first_parent_actual_P4_correspondence':parent_qualified,'distinct_owned_numerical_PIDs':42,'ownership':'all terminal0/startupFDsclosed/exactwait4reaped/outerreaped/no cleanupgap','next_release':'HOLDcollectROOT before remaining24 centralworkflow/profile members'}
p=DEST/'ROOT-result-index.json';p.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'complete':True,'index':str(p),'sha256':sha(p)}),flush=True)
