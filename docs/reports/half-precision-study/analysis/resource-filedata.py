"""One-off retained-file aggregation for exactly the twelve closed prepared resources."""
import hashlib
import json
import math
import re
import statistics
import struct
from pathlib import Path
R=Path('/workspace/work/campaign/evidence/114')
O=R/'report-preparation-and-completion-1/author/final-completion-1'
L=R/'actual-bound-method-review-preparation-1/actual-resource12-followup-1/actual-resource12-inputs.sha256'
M=R/'actual-bound-method-review-preparation-1/reviewer1/prepared-counterpart-assessment-1/actual-twelve-counterpart-map.json'
ORDER=[f'R2-{row}-PREPARED_{arm}-r{rep}-attempt1' for row in ('W02','W05') for rep in (1,2,3) for arm in (('HALF','WIDER') if rep==2 else ('WIDER','HALF'))]
def unique(pairs):
    d={}
    for k,v in pairs:
        assert k not in d,k
        d[k]=v
    return d
def load(p):return json.loads(p.read_text(),object_pairs_hook=unique,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def num(x):return struct.unpack('>d',bytes.fromhex(x['float64_bits_be']))[0] if isinstance(x,dict) and set(x)=={'float64_bits_be'} else x
def canonical_stats(s):
    parts=[s['real'],s['imag']] if 'real' in s else [s]
    return dict(components=sum(math.prod(p['shape']) for p in parts),
        nonfinite=sum(p['nonfinite'] for p in parts),negative=sum(p['negative'] for p in parts),
        zeros=sum(p['zeros'] for p in parts),negative_zeros=sum(p['negative_zeros'] for p in parts),
        half_subnormal_component_range=sum(p['binary16_subnormal_range'] for p in parts),
        minimum_component=min(num(p['minimum']) for p in parts),maximum_component=max(num(p['maximum']) for p in parts))
ledger={}
for line in L.read_text().splitlines():
    h,p=line.split('  ',1);assert p not in ledger
    assert any(str(R/family/runid)+'/' in p for family in ('current-runs-2','current-resource-captures-2') for runid in ORDER)
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    ledger[p]=h
assert len(ledger)==264
mapping=load(M);counter={(m['row'],m['resource_arm'],m['repetition']):m for m in mapping}
rows={};counterfiles={}
for rid in ORDER:
    d=R/'current-runs-2'/rid;c=R/'current-resource-captures-2'/rid
    a=load(d/'attempt.json');ch=load(d/'child.json');launch=load(c/'launch.json');post=load(c/'postclose.stdout')
    assert ch['row']==a['row'] and ch['strategy']==a['strategy'] and ch['repetition']==a['repetition']
    expected=counter[(ch['row'],ch['strategy'],ch['repetition'])]
    assert ch['caller']==expected['expected_resource_caller']['identity']
    assert ch['branches']==expected['expected_branches'] and ch['finite_outputs'] is True
    assert set(ch['outputs'])==set(expected['expected_seven_outputs']) and len(ch['outputs'])==7
    assert ch['materials_before']==ch['materials_after']==a['materials_before']==a['materials_after']
    assert ch['reference_workflow_loaded'] is False and ch['qualification_receipt_loaded'] is False
    def npy_stats(info):
        p=Path(info['path']);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==info['file_sha256']
        assert raw[:8]==b'\x93NUMPY\x01\x00';n=int.from_bytes(raw[8:10],'little');head=raw[10:10+n].decode('ascii')
        m=re.fullmatch(r"\{'descr': '(<(?:f2|f8|c16))', 'fortran_order': False, 'shape': \(([0-9, ]*)\), \} *\n",head)
        assert m,(p,head)
        shape=tuple(int(x.strip()) for x in m[2].split(',') if x.strip());dtype=m[1];payload=raw[10+n:]
        assert list(shape)==info['shape'] and dtype==info['canonical_dtype']
        assert len(payload)==info['payload_bytes'] and len(payload)==math.prod(shape)*int(dtype[2:])
        assert hashlib.sha256(payload).hexdigest()==info['content_sha256']
        vals=[x[0] for x in struct.iter_unpack('<e' if dtype=='<f2' else '<d',payload)]
        assert all(math.isfinite(x) for x in vals)
        s=dict(components=len(vals),nonfinite=0,negative=sum(x<0 for x in vals),zeros=sum(x==0 for x in vals),
            negative_zeros=sum(x==0 and math.copysign(1,x)<0 for x in vals),
            half_subnormal_component_range=sum(0<abs(x)<2**-14 for x in vals),
            minimum_component=min(vals),maximum_component=max(vals))
        counterfiles[str(p)]=dict(sha256=info['file_sha256'],bytes=len(raw),header=head)
        return s
    assert canonical_stats(ch['caller_stats'])==npy_stats(expected['expected_resource_caller']['original_NPY'])
    for name,item in expected['expected_seven_outputs'].items():
        assert ch['outputs'][name]['identity']==item['identity']
        assert canonical_stats(ch['outputs'][name]['statistics'])==npy_stats(item['NPY'])
    assert a['child_record_sha256']==hashlib.sha256((d/'child.json').read_bytes()).hexdigest()
    assert (d/'grant.original.json').read_bytes()==(c/'grant.json').read_bytes()
    assert a['grant_sha256']==ch['grant_sha256_after']==hashlib.sha256((c/'grant.json').read_bytes()).hexdigest()
    term=a['terminal'];assert term['exit_code']==0 and term['signal'] is None and term['raw_wait_status']==0
    assert term['native_units']=='Linux KiB' and term['multiplier_to_bytes']==1024
    assert term['terminal_child_peak_bytes']==term['native_ru_maxrss']*1024
    assert not a['wait_ownership_lost'] and not a['coordinator_recovery_required']
    assert term['pid']==ch['pid']==ch['identity']['pid']==a['readiness']['pid']==a['owned_child']['pid']
    assert a['readiness']['session']==a['readiness']['process_group']==ch['pid']
    assert ch['identity']['start_ticks']==a['owned_child']['start_ticks']
    assert load(d/'startup-readiness.bin')==a['readiness']
    assert a['launch']['target_argv']==launch['target_argv']
    assert hashlib.sha256(a['launch']['bootstrap_argv'][2].encode()).hexdigest()==a['launch']['bootstrap_sha256']
    assert launch['runtime_released'] and launch['source_output_absent']
    assert load(c/'ROOT-target-terminal.json')['returncode']==0
    for name,identity in [('child',ch['identity']),('parent',a['parent_identity'])]:
        assert post[name]['pid']==identity['pid'] and post[name]['old_start']==identity['start_ticks']
        assert post[name]['original_identity_absent'] is True
    t=[ch[k] for k in ('numerical_import_end_ns','setup_start_ns','setup_end_ns','conversion_start_ns','call_start_ns','call_end_ns')]
    assert all(type(x) is int for x in t) and t==sorted(t)
    for key,x,y in [('numerical_import_seconds','numerical_import_start_ns','numerical_import_end_ns'),
        ('setup_seconds','setup_start_ns','setup_end_ns'),('call_only_seconds','call_start_ns','call_end_ns'),
        ('conversion_and_call_seconds','conversion_start_ns','call_end_ns'),('setup_to_call_seconds','setup_start_ns','call_end_ns')]:
        assert ch[key]==(ch[y]-ch[x])/1e9
    if ch['strategy']=='PREPARED_HALF':
        assert ch['setup_start_ns']<=ch['setup_pack_start_ns']<=ch['setup_pack_end_ns']<=ch['setup_end_ns']
        assert ch['setup_pack_seconds']==(ch['setup_pack_end_ns']-ch['setup_pack_start_ns'])/1e9
    else:assert ch['setup_pack_seconds'] is None and ch['setup_pack_start_ns'] is None and ch['setup_pack_end_ns'] is None
    for snap in ch['snapshots'].values():
        assert snap['native_units']=='Linux KiB' and snap['bytes']==snap['native_ru_maxrss']*1024
        assert snap['native_ru_maxrss']<=term['native_ru_maxrss']
    metrics={k:ch[k] for k in ('numerical_import_seconds','setup_seconds','setup_pack_seconds','call_only_seconds',
        'conversion_and_call_seconds','setup_to_call_seconds','cold_to_setup_start_seconds','local_cold_to_call_end_seconds','whole_child_until_json_seconds')}
    metrics.update(terminal_native_Linux_KiB=term['native_ru_maxrss'],terminal_native_bytes=term['terminal_child_peak_bytes'],
        retained_reachable_payload_bytes=ch['retained_payload']['reachable_array_payload_bytes'],
        spawn_to_terminal_observed_seconds=a['spawn_to_terminal_observed_seconds'])
    rows[rid]=dict(row=ch['row'],arm=ch['strategy'],repetition=ch['repetition'],
        child_sha256=ledger[str(d/'child.json')],attempt_sha256=ledger[str(d/'attempt.json')],
        release_time_unix_ns=launch['time_unix_ns'],metrics=metrics,
        caller=ch['caller'],caller_stats=ch['caller_stats'],outputs=ch['outputs'],branches=ch['branches'],warnings=ch['warnings'],
        source_snapshots=ch['snapshots'],local_clock_endpoints={k:v for k,v in ch.items() if k.endswith('_ns')},
        native_terminal=term,readiness=a['readiness'],owned_child_pre_setsid=a['owned_child'],postclose=post,
        counterpart_diagnostic_run=expected['diagnostic_run_id'],counterpart_all_identities_and_recorded_stats_match=True,
        limits='Record identity/statistics correspondence under stated method; no independently retained child output arrays/full standalone metadata/trace/live heap or upstream science theorem.')
assert sorted(ORDER,key=lambda rid:rows[rid]['release_time_unix_ns'])==ORDER
groups={}
for row in ('W02','W05'):
    for arm in ('PREPARED_WIDER','PREPARED_HALF'):
        triple=[rows[f'R2-{row}-{arm}-r{n}-attempt1'] for n in (1,2,3)]
        groups[row+'/'+arm]={}
        for key in triple[0]['metrics']:
            vals=[x['metrics'][key] for x in triple]
            finite=all(type(x) in (int,float) and math.isfinite(x) for x in vals)
            groups[row+'/'+arm][key]=dict(raw=vals,median=statistics.median(vals) if finite else None,
                minimum=min(vals) if finite else None,maximum=max(vals) if finite else None,
                missing_reason=None if finite else 'No separate packing operation in wider; null is not measured zero')
out=dict(scope='actual selected12 retained-file aggregation; independent completed peer disposition remains separate',
    resource_ledger_files=264,order=ORDER,cases=rows,groups=groups,counterpart_NPY_inputs=counterfiles)
(O/'resource-results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
lines=['# Selected12 resource observations\n','All values retain distinct lifecycle scopes. Three fresh successful observations per row/arm; exact predefined alternating order. No subtraction of peaks, process-tree sum or native precision theorem.\n',
    '| Row/arm | Quantity | r1,r2,r3 | Median [minimum,maximum] |','| --- | --- | --- | --- |']
for g,fields in groups.items():
    for k,s in fields.items():lines.append('| '+g+' | '+k+' | '+', '.join(str(x) for x in s['raw'])+' | '+str(s['median'])+' ['+str(s['minimum'])+','+str(s['maximum'])+'] |')
(O/'resource-tables.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'resource_files_verified':264,'counterpart_NPY_paths_checked':len(counterfiles),'cases':12,
    'warnings':sum(len(x['warnings']) for x in rows.values()),'result_sha256':hashlib.sha256((O/'resource-results.json').read_bytes()).hexdigest()}))
