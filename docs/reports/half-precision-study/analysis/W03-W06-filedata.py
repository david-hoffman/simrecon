"""One-off retained-data aggregation for exactly the closed W03/W04/W05/W06 84 cases."""
import hashlib
import json
import math
import re
import statistics
import struct
from fractions import Fraction as F
from pathlib import Path

ROOT = Path('/workspace/work/campaign/evidence/114')
OWN = ROOT/'report-preparation-and-completion-1/author/closed-W03-W06-slice-1'
LEDGER = ROOT/'report-preparation-and-completion-1/closed-W03-W06-row-intake-1/actual-closed-W03-W06-inputs.sha256'
MODES = ['WIDER','H1','H1_PROMOTED','H2_CORRECTED','H2_PREPARED','H2_FILTERED','H2_EMBEDDED']
IDS = [f'N2-{row}-{mode}-r{rep}-attempt1' for row in ('W03','W04','W05','W06') for mode in MODES for rep in (1,2,3)]
SOURCE = '246829749f356344fcd8e363e359039984da1911ee20b74a45637a6ff3226635'

def unique(pairs):
    out = {}
    for k,v in pairs:
        assert k not in out, k
        out[k] = v
    return out

def read_json(p):
    return json.loads(p.read_text(),object_pairs_hook=unique,
        parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

def scalar(x):
    return struct.unpack('>d',bytes.fromhex(x['float64_bits_be']))[0] if isinstance(x,dict) and set(x)=={'float64_bits_be'} else x

def clean(x):
    if isinstance(x,float) and (not math.isfinite(x) or x==0):
        return {'float64_bits_be':struct.pack('>d',x).hex()}
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    return x

def compstats(v):
    finite = [x for x in v if math.isfinite(x)]
    return dict(components=len(v),minimum=min(finite) if finite else None,maximum=max(finite) if finite else None,
        nonfinite=sum(not math.isfinite(x) for x in v),negative=sum(x<0 for x in v),
        zeros=sum(x==0 for x in v),negative_zeros=sum(x==0 and math.copysign(1,x)<0 for x in v),
        binary16_subnormal_range=sum(0<abs(x)<2**-14 for x in v))

def hword(v):
    sign = 0x8000 if math.copysign(1,v)<0 else 0
    if not math.isfinite(v): return sign | (0x7e00 if math.isnan(v) else 0x7c00)
    q = F(abs(v))
    if q>=65520: return sign|0x7c00
    if not q: return sign
    e=-14
    while q>=F(2)**(e+1): e+=1
    step=F(2)**(max(e,-14)-10); scaled=q/step
    n,r=divmod(scaled.numerator,scaled.denominator)
    n+=2*r>scaled.denominator or (2*r==scaled.denominator and n%2)
    if q<F(2)**-14: return sign|n
    if n==2048: n=1024; e+=1
    return sign|((e+15)<<10)|(n-1024)

ledger={}
for line in LEDGER.read_text().splitlines():
    digest,path=line.split('  ',1)
    assert path not in ledger
    assert any(str(ROOT/family/run_id)+'/' in path for family in ('current-runs-2','current-numerical-captures-2') for run_id in IDS),path
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
    ledger[path]=digest
assert len(ledger)==27252
decoded={}; paircache={}; indexed={}; cases={}

def pairmetrics(a,b):
    key=(a['payload_hash'],b['payload_hash'],a['dtype'],b['dtype'],a['shape'],b['shape'])
    if key in paircache: return paircache[key]
    assert a['shape']==b['shape']
    complex_pair=a['dtype'][1]=='c' or b['dtype'][1]=='c'
    av=a['values']; bv=b['values']
    if complex_pair:
        if a['dtype'][1]!='c': av=[z for v in av for z in (v,0.0)]
        if b['dtype'][1]!='c': bv=[z for v in bv for z in (v,0.0)]
    assert len(av)==len(bv)
    losses={}; signchanges={}
    for part,offset in [('real',0),('imag',1)] if complex_pair else [('real',0)]:
        step=2 if complex_pair else 1
        losses[part]=sum(x!=0 and y==0 for x,y in zip(av[offset::step],bv[offset::step]))
        signchanges[part]=sum(x!=0 and y!=0 and math.copysign(1,x)!=math.copysign(1,y) for x,y in zip(av[offset::step],bv[offset::step]))
    out=dict(reference_payload_hash=a['payload_hash'],candidate_payload_hash=b['payload_hash'],
        nonzero_to_zero=losses,sign_changes_nonzero=signchanges,
        component_values_equal=av==bv,exact_payload_equal=a['dtype']==b['dtype'] and a['payload']==b['payload'])
    if not all(math.isfinite(x) and math.isfinite(y) for x,y in zip(av,bv)):
        out['status']='nonfinite'; paircache[key]=out; return out
    d=[F(y)-F(x) for x,y in zip(av,bv)]
    sq=sum(x*x for x in d); energy=sum(F(x)**2 for x in av)
    mags=[d[i]**2+d[i+1]**2 for i in range(0,len(d),2)] if complex_pair else [x*x for x in d]
    n=math.prod(a['shape'])
    out.update(status='finite',count=n,exact_squared_error=str(sq),exact_reference_energy=str(energy),
        max_absolute=math.sqrt(float(max(mags,default=F(0)))),
        rms=math.sqrt(float(sq/n)) if n else 0.0,
        relative_l2=math.sqrt(float(sq/energy)) if energy else (0.0 if not sq else None),
        zero_reference_rule='both zero ->0; nonzero error with zero reference ->undefined/null')
    paircache[key]=out; return out

for run_id in IDS:
    base=ROOT/'current-runs-2'/run_id; cap=ROOT/'current-numerical-captures-2'/run_id
    r=read_json(base/'run.json'); arrays={}
    assert r['run_id']==run_id and r['status']=='completed' and r['result']['status']=='completed'
    assert r['identities']['harness']==SOURCE and r['materials_before']==r['materials_after']
    for logical,info in r['array_index'].items():
        assert re.fullmatch(r'arrays/[0-9]{5}\.npy',info['path'])
        p=base/info['path']; raw=p.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
        assert sha==info['sha256']==ledger[str(p)] and len(raw)==info['nbytes']
        if sha not in decoded:
            assert raw[:8]==b'\x93NUMPY\x01\x00'
            n=int.from_bytes(raw[8:10],'little'); header=raw[10:10+n].decode('ascii')
            m=re.fullmatch(r"\{'descr': '([<>|](?:f2|f4|f8|c8|c16|i4|i8|b1))', 'fortran_order': False, 'shape': \(([0-9, ]*)\), \} *\n",header)
            assert m,(p,header)
            dtype=m[1]; shape=tuple(int(x.strip()) for x in m[2].split(',') if x.strip())
            assert len(shape)<=8 and all(x>=0 for x in shape)
            payload=raw[10+n:]; width=int(dtype[2:]); assert len(payload)==math.prod(shape)*width
            component_width=width//2 if dtype[1]=='c' else width
            fmt={'f2':'e','f4':'f','f8':'d','c8':'f','c16':'d','i4':'i','i8':'q','b1':'?'}[dtype[1:]]
            values=[x[0] for x in struct.iter_unpack(('>' if dtype[0]=='>' else '<')+fmt,payload)]
            canonical=payload if dtype[0]!='>' else b''.join(payload[i:i+component_width][::-1] for i in range(0,len(payload),component_width))
            stats={'real':compstats(values[::2]),'imag':compstats(values[1::2])} if dtype[1]=='c' else compstats(values)
            decoded[sha]=dict(dtype=dtype,shape=shape,payload=payload,values=values,header=header,
                payload_hash=hashlib.sha256(canonical).hexdigest(),statistics=stats)
        arr=decoded[sha]; arrays[logical]=arr
        indexed[run_id+'/'+logical]=dict(original_path=str(p),file_sha256=sha,file_bytes=len(raw),
            dtype=arr['dtype'],shape=arr['shape'],original_header=arr['header'],
            canonical_payload_sha256=arr['payload_hash'],component_statistics=arr['statistics'])
    def desc(x):
        assert set(x)=={'array','shape','dtype'}
        a=arrays[x['array']]; assert a['dtype']==x['dtype'] and list(a['shape'])==x['shape']; return a
    def descriptors(x):
        if isinstance(x,dict):
            if 'array' in x: desc(x)
            else:
                for v in x.values(): descriptors(v)
        elif isinstance(x,list):
            for v in x: descriptors(v)
    descriptors(r['result'])
    res=r['result']; b=res['baseline']; c=res['candidate']; bp=b['parameters']; cp=c['parameters']
    comparisons={}
    for name,x,y in [('image_error_count_units',b['image'],c['image']),
        ('prepared_error',b['bands']['quadratures'],c['bands']['quadratures']),
        ('noise_error',b['bands']['noise_variance_factors'],c['bands']['noise_variance_factors']),
        ('frame_sum_error',b['bands']['frame_sums'],c['bands']['frame_sums']),
        ('gain_error',b['bands']['equalization_gains'],c['bands']['equalization_gains']),
        ('phase_matrix_error',b['bands']['separation_matrices'],c['bands']['separation_matrices']),
        ('carrier_cyc_um',bp['carriers_cyc_um'],cp['carriers_cyc_um']),
        ('modulation',bp['modulation'],cp['modulation']),('raw_modulation',bp['raw_modulation'],cp['raw_modulation'])]:
        comparisons[name]=pairmetrics(desc(x),desc(y))
    quantization={}
    for key in arrays:
        if not key.endswith('.packed'): continue
        prefix=key[:-7]; promoted=arrays[prefix+'.promoted']; packed=arrays[key]
        if prefix+'.source' in arrays: original=arrays[prefix+'.source']
        elif prefix=='H1.raw': original=arrays['generator.raw32']
        elif prefix=='prepared': original=desc(b['bands']['quadratures'])
        elif prefix.startswith('filtered.'):
            original=desc(b['reconstructions'][int(prefix.split('.')[1])]['filtered_quadratures'])
        else: raise ValueError(('unmapped exact packing site',prefix))
        words=[hword(v) for v in original['values']]
        assert packed['payload']==b''.join(struct.pack('<H',w) for w in words)
        assert promoted['payload']==b''.join(struct.pack('<d',struct.unpack('<e',struct.pack('<H',w))[0]) for w in words)
        quantization[prefix]=dict(original_dtype=original['dtype'],shape=original['shape'],
            packed_dtype=packed['dtype'],packed_shape=packed['shape'],promoted_dtype=promoted['dtype'],
            all_half_words_match_integer_nearest_even=True,metrics=pairmetrics(original,promoted),
            source_stats=original['statistics'],packed_stats=packed['statistics'],promoted_stats=promoted['statistics'])
    par=res['parameters']; reference_decisions=par['decisions_reference']; candidate_decisions=par['decisions_candidate']
    decision_equal=reference_decisions==candidate_decisions
    assert decision_equal==par['decisions_equal']
    parameter_arrays={k:dict(dtype=desc(par[k])['dtype'],shape=desc(par[k])['shape'],
        stats=desc(par[k])['statistics'],values=desc(par[k])['values']) for k in
        ('carrier_bin_components','amplitude_error','wrapped_phase_error_rad','phase_defined')}
    def stats_desc(x):
        a=desc(x);return dict(dtype=a['dtype'],shape=a['shape'],canonical_payload_sha256=a['payload_hash'],statistics=a['statistics'])
    usage=read_json(cap/'terminal-native-usage.txt'); launch=read_json(cap/'launch.json')
    identities=read_json(cap/'process-identities.json'); post=read_json(cap/'postclose.stdout')
    target=read_json(cap/'ROOT-target-terminal.json'); observer=read_json(cap/'ROOT-identity-observer-terminal.json')
    assert set(usage)=={'native_ru_maxrss','native_units','exit_code','elapsed_seconds','user_seconds','system_seconds'}
    assert usage['native_units']=='Linux KiB' and usage['exit_code']==target['returncode']==observer['returncode']==0
    assert type(usage['native_ru_maxrss']) is int and usage['native_ru_maxrss']>0
    endpoint={k:r[k] for k in ('pre_call_high_water_rss_kib','native_peak_rss_kib_before_export','native_peak_rss_kib_after_export')}
    assert usage['native_ru_maxrss']>=max(endpoint.values())
    for phase in ('before','after'):
        assert r[f'native_peak_rss_bytes_{phase}_export']==r[f'native_peak_rss_kib_{phase}_export']*1024
    py=identities['found']['python']; tm=identities['found']['time']
    assert identities['complete'] and py['ppid']==tm['pid'] and py['argv']==launch['inner_argv']
    assert launch['usage_file_absent'] and launch['source_output_absent'] and launch['runtime_released']
    for name,identity in [('python',py),('time',tm)]:
        assert post[name]['pid']==identity['pid'] and post[name]['old_start']==identity['start_ticks']
        assert post[name]['original_identity_absent'] is True
    clocks=res['local_clocks']
    assert clocks['setup_start_ns']<=clocks['setup_end_ns']<=clocks['baseline_start_ns']<=clocks['baseline_end_ns']
    assert clocks['setup_seconds']==(clocks['setup_end_ns']-clocks['setup_start_ns'])/1e9
    assert clocks['setup_to_candidate_end_seconds']==(clocks['candidate_end_ns']-clocks['setup_start_ns'])/1e9
    assert res['conversion_and_candidate_seconds']==(clocks['candidate_end_ns']-clocks['candidate_start_ns'])/1e9
    for t in r['timings']: assert t['start_ns']<=t['end_ns'] and t['seconds']==(t['end_ns']-t['start_ns'])/1e9
    assert r['operation_seconds']==(r['operation_end_ns']-r['operation_start_ns'])/1e9
    assert r['numerical_import_seconds']==(r['numerical_import_end_ns']-r['numerical_import_start_ns'])/1e9
    lifecycle={k:r[k] for k in ('numerical_import_seconds','cold_to_operation_start_seconds','operation_seconds',
        'local_cold_to_operation_end_seconds','whole_run_before_export_seconds','including_export_seconds')}
    lifecycle.update(setup_seconds=clocks['setup_seconds'],conversion_and_candidate_seconds=res['conversion_and_candidate_seconds'],
        setup_to_candidate_end_seconds=clocks['setup_to_candidate_end_seconds'],
        baseline_call_seconds=(clocks['baseline_end_ns']-clocks['baseline_start_ns'])/1e9,
        terminal_native_Linux_KiB=usage['native_ru_maxrss'],terminal_native_bytes=usage['native_ru_maxrss']*1024,
        GNU_broad_elapsed_seconds=usage['elapsed_seconds'],GNU_user_seconds=usage['user_seconds'],GNU_system_seconds=usage['system_seconds'],
        retained_reachable_array_payload_bytes=r['retained_payload']['reachable_array_payload_bytes'],
        **endpoint)
    lifecycle.update({'timed.'+t['operation']+'.seconds':t['seconds'] for t in r['timings']})
    case=dict(row=r['row'],mode=r['strategy'],repetition=r['repetition'],run_sha256=ledger[str(base/'run.json')],
        source=SOURCE,status=r['status'],scope=res['scope'],array_count=len(arrays),warnings=r['warnings'],
        source_error_observers={k:v for k,v in res.items() if k not in ('baseline','candidate','local_clocks','scope','status','conversion_and_candidate_seconds')},
        independent_actual_array_comparisons=comparisons,quantization=quantization,
        image_reference=stats_desc(b['image']),image_candidate=stats_desc(c['image']),
        decisions_equal=decision_equal,decisions_reference=reference_decisions,decisions_candidate=candidate_decisions,
        parameter_arrays=parameter_arrays,lifecycle=lifecycle,source_local_clocks=clocks,source_timed_intervals=r['timings'],
        source_retained_payload=r['retained_payload'],native_usage=usage,
        capture_identities={k:ledger[str(cap/k)] for k in ('binding.json','context.json','grant.json','launch.json',
            'terminal-native-usage.txt','process-identities.json','postclose.stdout','ROOT-target-terminal.json','ROOT-identity-observer-terminal.json')},
        original_subject=py,original_timer=tm,postclose=post,
        scientific_disposition='UNRESOLVED_NOACTIVATION; descriptive relative to current wider only')
    cases[run_id]=case

groups={}
for row in ('W03','W04','W05','W06'):
    for mode in MODES:
        three=[cases[f'N2-{row}-{mode}-r{rep}-attempt1'] for rep in (1,2,3)]
        summary={}
        for k in sorted(set().union(*(c['lifecycle'] for c in three))):
            vals=[c['lifecycle'].get(k) for c in three]
            summary[k]=dict(raw=vals,median=statistics.median(vals),minimum=min(vals),maximum=max(vals)) if all(type(v) in (int,float) and math.isfinite(v) for v in vals) else dict(raw=vals,median=None,reason='missing/nonfinite; no invented value')
        error={}
        for name in three[0]['independent_actual_array_comparisons']:
            error[name]={}
            for metric in ('max_absolute','rms','relative_l2'):
                source_name=three[0]['source_error_observers'].get(name) if name.endswith('error') or name=='image_error_count_units' else three[0]['source_error_observers']['parameters'].get(name)
                source_values=[]
                for c in three:
                    source_metric=c['source_error_observers'].get(name) if name in c['source_error_observers'] else c['source_error_observers']['parameters'].get(name)
                    source_values.append(scalar(source_metric.get(metric)) if source_metric is not None else None)
                vals=[c['independent_actual_array_comparisons'][name].get(metric) for c in three]
                error[name][metric]=dict(source_raw=source_values,independent_raw=vals,
                    source_median=statistics.median(source_values) if all(type(x) in (int,float) and math.isfinite(x) for x in source_values) else None,
                    source_minimum=min(source_values) if all(type(x) in (int,float) and math.isfinite(x) for x in source_values) else None,
                    source_maximum=max(source_values) if all(type(x) in (int,float) and math.isfinite(x) for x in source_values) else None)
        groups[row+'/'+mode]=dict(run_ids=[f'N2-{row}-{mode}-r{rep}-attempt1' for rep in (1,2,3)],
            scope=three[0]['scope'],collected_completed_repetitions=3,
            source_error_summary=error,lifecycle_summary=summary,
            decision_equal_each=[c['decisions_equal'] for c in three],
            warnings_each=[c['warnings'] for c in three],
            image_candidate_each=[c['image_candidate'] for c in three],
            quantization_each=[c['quantization'] for c in three])

payload=dict(scope='PARTIAL STUDY AUTHORING ONLY; exact closed W03/W04/W05/W06 retained data',
    supplied_input_files=len(ledger),cases=cases,groups=groups,indexed_array_files=indexed,
    indexed_NPY_count=len(indexed),distinct_decoded_NPY_hashes=len(decoded),
    science='UNRESOLVED_NOACTIVATION',matched_resource='NOT_ASSESSED; diagnostics unmatched')
assert len(cases)==84 and len(indexed)==25488
(OWN/'closed-row-results.json').write_text(json.dumps(clean(payload),indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status='bounded retained-row aggregation complete',cases=84,NPY_files=len(indexed),
    unique_NPY_hashes=len(decoded),warnings=sum(len(c['warnings']) for c in cases.values()),
    source=SOURCE,result_sha256=hashlib.sha256((OWN/'closed-row-results.json').read_bytes()).hexdigest())))
