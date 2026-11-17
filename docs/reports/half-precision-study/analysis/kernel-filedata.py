"""One-off exact K5 retained-data inspection; no workload or general parser."""
import hashlib
import json
import math
import re
import struct
from fractions import Fraction as F
from pathlib import Path

ROOT = Path('/workspace/work/campaign/evidence/114')
OWN = ROOT / 'report-preparation-and-completion-1/author/kernel-slice-1'
LEDGER = ROOT / 'report-preparation-and-completion-1/kernel-slice-intake-1/actual-kernel5-inputs.sha256'
SOURCE = '246829749f356344fcd8e363e359039984da1911ee20b74a45637a6ff3226635'
IDS = ['N2-K01-KERNEL-r1-attempt1', 'N2-K02-KERNEL-r1-attempt1',
       'N2-K03-KERNEL-r1-attempt1', 'N2-K04-KERNEL-r1-attempt1', 'N2-K01-CPU-r1-attempt1']

def unique(pairs):
    out = {}
    for key, value in pairs:
        assert key not in out, key
        out[key] = value
    return out

def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

def scalar(value):
    if isinstance(value, dict) and set(value) == {'float64_bits_be'}:
        return struct.unpack('>d', bytes.fromhex(value['float64_bits_be']))[0]
    return value

def halfword(value):
    """Integer nearest-even binary16 expectation for these finite retained inputs."""
    sign = 0x8000 if math.copysign(1.0, value) < 0 else 0
    q = F(abs(value))
    if q >= 65520:
        return sign | 0x7c00
    if not q:
        return sign
    exponent = -14
    while q >= F(2) ** (exponent + 1):
        exponent += 1
    step = F(2) ** (max(exponent, -14) - 10)
    scaled = q / step
    rounded, rem = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * rem
    rounded += twice > scaled.denominator or (twice == scaled.denominator and rounded % 2)
    if q < F(2) ** -14:
        return sign | rounded
    if rounded == 2048:
        rounded = 1024
        exponent += 1
    return sign | ((exponent + 15) << 10) | (rounded - 1024)

ledger = {}
for line in LEDGER.read_text().splitlines():
    digest, path = line.split('  ', 1)
    assert path not in ledger
    ledger[path] = digest
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert len(ledger) == 219
result = {'scope': 'PARTIAL STUDY AUTHORING ONLY; retained K5, no workload execution',
          'ledger_files_verified': len(ledger), 'runs': {}, 'arrays': {}, 'checks': {}}
arrays = {}
runs = {}
for run_id, expected_count in zip(IDS, [6, 9, 64, 35, 0]):
    base = ROOT / 'current-runs-2' / run_id
    capture = ROOT / 'current-kernel-captures-2' / run_id
    record = read_json(base / 'run.json')
    runs[run_id] = record
    assert record['run_id'] == run_id and record['status'] == 'completed'
    assert record['identities']['harness'] == SOURCE
    assert record['materials_before'] == record['materials_after']
    assert len(record['array_index']) == expected_count
    array_map = {}
    for logical, info in record['array_index'].items():
        assert re.fullmatch(r'arrays/[0-9]{5}\.npy', info['path'])
        path = base / info['path']
        raw = path.read_bytes()
        assert str(path) in ledger and hashlib.sha256(raw).hexdigest() == info['sha256']
        assert len(raw) == info['nbytes']
        assert raw[:8] == b'\x93NUMPY\x01\x00'
        header_size = int.from_bytes(raw[8:10], 'little')
        header = raw[10:10 + header_size].decode('ascii')
        match = re.fullmatch(r"\{'descr': '(<(?:f2|f8|c16))', 'fortran_order': False, 'shape': \(([0-9, ]*)\), \} *\n", header)
        assert match, (path, header)
        dtype = match[1]
        shape = tuple(int(x.strip()) for x in match[2].split(',') if x.strip())
        assert shape in ((16,), (16, 2), (8,), (4096,), (4096, 2), (3,), (4,), (4, 2), (3, 3))
        payload = raw[10 + header_size:]
        width = {'<f2': 2, '<f8': 8, '<c16': 16}[dtype]
        assert len(payload) == math.prod(shape) * width
        component_width = 2 if dtype == '<f2' else 8
        fmt = '<e' if dtype == '<f2' else '<d'
        values = [p[0] for p in struct.iter_unpack(fmt, payload)]
        array_map[logical] = (dtype, shape, values, payload)
        finite = [x for x in values if math.isfinite(x)]
        result['arrays'][run_id + '/' + logical] = dict(
            original_path=str(path), file_sha256=info['sha256'], file_bytes=len(raw),
            original_header=header, dtype=dtype, shape=shape, component_count=len(values),
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            nonfinite=sum(not math.isfinite(x) for x in values),
            subnormal_binary16_range=sum(0 < abs(x) < 2**-14 for x in finite),
            zeros=sum(x == 0 for x in values),
            negative_zeros=sum(x == 0 and math.copysign(1, x) < 0 for x in values),
            finite_minimum=min(finite) if finite else None,
            finite_maximum=max(finite) if finite else None,
            small_component_words=[payload[i:i+component_width].hex()
                                   for i in range(0, len(payload), component_width)] if len(values) <= 32 else None)
    arrays[run_id] = array_map
    usage = read_json(capture / 'terminal-native-usage.txt')
    assert set(usage) == {'native_ru_maxrss','native_units','exit_code','elapsed_seconds','user_seconds','system_seconds'}
    assert usage['exit_code'] == 0 and usage['native_units'] == 'Linux KiB'
    assert type(usage['native_ru_maxrss']) is int and usage['native_ru_maxrss'] > 0
    assert all(math.isfinite(usage[k]) and usage[k] >= 0 for k in ('elapsed_seconds','user_seconds','system_seconds'))
    endpoint = [record[k] for k in ('pre_call_high_water_rss_kib','native_peak_rss_kib_before_export','native_peak_rss_kib_after_export')]
    assert usage['native_ru_maxrss'] >= max(endpoint)
    for phase in ('before','after'):
        assert record[f'native_peak_rss_bytes_{phase}_export'] == record[f'native_peak_rss_kib_{phase}_export'] * 1024
    clocks = [record[k] for k in ('local_cold_start_ns','numerical_import_start_ns','numerical_import_end_ns','operation_start_ns','operation_end_ns')]
    assert all(type(x) is int for x in clocks) and clocks == sorted(clocks)
    assert (clocks[2]-clocks[1])/1e9 == record['numerical_import_seconds']
    assert (clocks[4]-clocks[3])/1e9 == record['operation_seconds']
    assert (clocks[4]-clocks[0])/1e9 == record['local_cold_to_operation_end_seconds']
    launch = read_json(capture / 'launch.json')
    identity = read_json(capture / 'process-identities.json')
    closure = read_json(capture / 'postclose.stdout')
    target = read_json(capture / 'ROOT-target-terminal.json')
    observer = read_json(capture / 'ROOT-identity-observer-terminal.json')
    assert identity['complete'] and target['returncode'] == observer['returncode'] == 0
    subject, timer = identity['found']['python'], identity['found']['time']
    assert subject['ppid'] == timer['pid'] and subject['argv'] == launch['inner_argv']
    assert launch['usage_file_absent'] and launch['source_output_absent'] and launch['runtime_released']
    for name, entry in (('python', subject), ('time', timer)):
        assert closure[name]['pid'] == entry['pid'] and closure[name]['old_start'] == entry['start_ticks']
        assert closure[name]['original_identity_absent'] is True
    assert record['environment']['threads'] == {k:'1' for k in record['environment']['threads']}
    result['runs'][run_id] = dict(run_sha256=ledger[str(base/'run.json')],
        source=SOURCE, array_count=expected_count, status=record['status'],
        materials_before_after_equal=True, warnings=record['warnings'],
        source_endpoint_KiB=endpoint, native=usage, native_bytes=usage['native_ru_maxrss']*1024,
        numerical_import_seconds=record['numerical_import_seconds'], operation_seconds=record['operation_seconds'],
        local_cold_to_operation_end_seconds=record['local_cold_to_operation_end_seconds'],
        including_export_seconds=record['including_export_seconds'],
        subject_identity=subject, timer_identity=timer, closure=closure,
        required_fft_after_call=record['required_fft_after_call'])

# Exact K01 half words and promoted component bits, including original complex zero signs.
a = arrays[IDS[0]]
prescribed = [0.0,-0.0,2**-25,-2**-25,2**-24,-2**-24,2**-14,-2**-14,
              1.0,-1.0,65504.0,-65504.0,65520.0,-65520.0,70000.0,-70000.0]
assert a['00004-record.result.values'][3] == b''.join(struct.pack('<d',x) for x in prescribed)
for prefix, original in [('K01.real','00004-record.result.values'), ('K01.complex','00005-record.result.complex_values')]:
    values = a[original][2]
    words = [halfword(x) for x in values]
    assert a[prefix+'.packed'][3] == b''.join(struct.pack('<H', w) for w in words)
    assert a[prefix+'.promoted'][3] == b''.join(struct.pack('<d', struct.unpack('<e', struct.pack('<H', w))[0]) for w in words)
    converted = a[prefix+'.promoted'][2]
    result['checks'][prefix] = dict(all_component_words_match=True,
        source_nonzero_to_zero=sum(x != 0 and y == 0 for x,y in zip(values,converted)),
        nonfinite_components=sum(not math.isfinite(y) for y in converted))

# Exact K02 input and quantization error arithmetic from retained tiny vectors.
result['checks']['K02'] = []
for i, (label, denom) in enumerate([('W02',12288),('W05',49152),('metadata-only',100663296)]):
    r = runs[IDS[1]]['result'][i]
    a = arrays[IDS[1]]
    original = a[r['values']['array']][2]
    assert r['alpha'] == 1 / denom
    factors = [0.0,-0.0,-128.0,-1.0,-2**-12,2**-12,1.0,128.0]
    assert b''.join(struct.pack('<d',x) for x in original) == b''.join(struct.pack('<d',r['alpha']*x) for x in factors)
    words = [halfword(x) for x in original]
    assert a['K02.'+label+'.packed'][3] == b''.join(struct.pack('<H',w) for w in words)
    converted = a['K02.'+label+'.promoted'][2]
    assert b''.join(struct.pack('<d',x) for x in converted) == b''.join(struct.pack('<d',struct.unpack('<e',struct.pack('<H',w))[0]) for w in words)
    squared = sum((F(x)-F(y))**2 for x,y in zip(original,converted))
    energy = sum(F(x)**2 for x in original)
    result['checks']['K02'].append(dict(label=label,alpha_denominator=denom,
        squared_error=str(squared), reference_energy=str(energy),
        independently_derived_max_absolute=float(max(abs(F(x)-F(y)) for x,y in zip(original,converted))),
        independently_derived_rms=math.sqrt(float(squared/8)),
        independently_derived_relative_l2=math.sqrt(float(squared/energy)), source_error=r['error'],
        nonzero_to_zero=sum(x != 0 and y == 0 for x,y in zip(original,converted))))

# K03 all retained dyadic operands and exact wide scalar results; no reduction backend call.
result['checks']['K03'] = []
for r in runs[IDS[2]]['result']:
    n, magnitude, pattern = r['n'], r['magnitude'], r['pattern']
    q = F(magnitude)
    sx = n*q*q*F(65,64)
    real = n*q*q*F(95,128) if pattern == 'constant' else F(0)
    imag = -n*q*q*F(5,32) if pattern == 'constant' else F(0)
    for field in ('exact_sx','original_sx','quantized_operands_wide_sx'):
        assert F(scalar(r[field])) == sx
    for field in ('exact_cross','original_cross','quantized_operands_wide_cross'):
        assert F(scalar(r[field]['real'])) == real and F(scalar(r[field]['imag'])) == imag
    for operand, components in [('lower',(magnitude,magnitude/8)), ('higher',(3*magnitude/4,-magnitude/16))]:
        key = f'K03.{n}.{magnitude}.{pattern}.{operand}'
        vals = arrays[IDS[2]][key+'.promoted'][2]
        expected = [v * (-1 if operand == 'higher' and pattern == 'alternating' and j % 2 else 1)
                    for j in range(n) for v in components]
        assert vals == expected
        assert arrays[IDS[2]][key+'.packed'][3] == b''.join(struct.pack('<H',halfword(v)) for v in expected)
    expected_half_energy = n*2**-24 if magnitude == 2**-12 else float(sx) if magnitude == 1 else math.inf
    expected_half_cross = (n*2**-24 if magnitude == 2**-12 else float(real) if magnitude == 1 else math.inf) if pattern == 'constant' else (math.nan if magnitude == 1024 else 0.0)
    assert scalar(r['explicit_half_energy']) == expected_half_energy
    actual_cross = scalar(r['explicit_half_real_cross'])
    assert math.isnan(actual_cross) if math.isnan(expected_half_cross) else actual_cross == expected_half_cross
    result['checks']['K03'].append(dict(n=n,magnitude=magnitude,pattern=pattern,
        exact_sx=str(sx),exact_cross_real=str(real),exact_cross_imag=str(imag),
        explicit_half_energy=r['explicit_half_energy'],explicit_half_real_cross=r['explicit_half_real_cross'],
        half_product_stats=r['explicit_half_real_product_stats']))

# K04 constant transform and fixed scalar fit/tie/regression witnesses.
r = runs[IDS[3]]['result']; a = arrays[IDS[3]]
assert a[r['inverse_growth']['spectrum']['array']][2] == [1024.0,-256.0]*16
assert a[r['inverse_growth']['inverse']['array']][2] == [16384.0,-4096.0] + [0.0,0.0]*15
assert [scalar(x) for x in r['equal_power_fits'][0]['wider']] == [0.25,'fitted']
assert [(x['wider'][1],x['quantized_wider'][1]) for x in r['equal_power_fits']] == [('fitted','fitted'),('zero-curvature','zero-curvature'),('outside-range','zero-curvature'),('fitted','zero-curvature')]
assert a[r['ordered_objectives']['wider']['array']][2] == [1.0,1.0+2**-12,1.0]
assert a[r['ordered_objectives']['quantized']['array']][2] == [1.0]*3
assert r['ordered_objectives']['wider_first_max'] == 1 and r['ordered_objectives']['quantized_first_max'] == 0
assert r['ordered_objectives']['wider_strict'] is True and r['ordered_objectives']['quantized_strict'] is False
assert F(r['regression_pairs'][1]['wider_sy']) == 4*F(1+2**-12)**2
assert r['regression_pairs'][1]['quantized_sy'] == 4
assert [(scalar(x['result'][0]),x['result'][1]) for x in r['general_fits']] == [(1.25,'fitted'),(0.0,'duplicate-coordinate'),(0.0,'zero-curvature')]
phase = []
for i, label in enumerate(('uniform','singular','near-conditioned')):
    entry = r['phase_designs'][i]
    original = a[entry['design']['array']][2]
    packed = a['K04.design.'+label+'.packed'][3]
    assert packed == b''.join(struct.pack('<H',halfword(x)) for x in original)
    for arm, values in [('wider',original),('quantized',a['K04.design.'+label+'.promoted'][2])]:
        m = [F(x) for x in values]
        det = m[0]*(m[4]*m[8]-m[5]*m[7])-m[1]*(m[3]*m[8]-m[5]*m[6])+m[2]*(m[3]*m[7]-m[4]*m[6])
        data = dict(label=label,arm=arm,exact_retained_design_determinant=str(det))
        if not det:
            assert entry[arm]['exception'] == 'StopIteration'
        else:
            cof = [m[4]*m[8]-m[5]*m[7],m[5]*m[6]-m[3]*m[8],m[3]*m[7]-m[4]*m[6],
                   m[2]*m[7]-m[1]*m[8],m[0]*m[8]-m[2]*m[6],m[1]*m[6]-m[0]*m[7],
                   m[1]*m[5]-m[2]*m[4],m[2]*m[3]-m[0]*m[5],m[0]*m[4]-m[1]*m[3]]
            exact = [cof[j*3+i]/det for i in range(3) for j in range(3)]
            retained_inverse = a[entry[arm]['inverse']['array']][2]
            assert retained_inverse == [float(x) for x in exact]
            data['retained_inverse_matches_rounded_exact_adjugate'] = True
            data['source_observed_residual_max_absolute'] = max(abs(x) for x in a[entry[arm]['residual']['array']][2])
        phase.append(data)
result['checks']['K04'] = dict(equal_power_fits=r['equal_power_fits'], general_fits=r['general_fits'],
    regression_pairs=r['regression_pairs'],ordered_decisions={k:r['ordered_objectives'][k] for k in ('wider_first_max','quantized_first_max','wider_strict','quantized_strict')},
    phase=phase,phase_condition_source_observed=[{'label':x['label'],'condition':x['condition']} for x in r['phase_designs']])

# CPU only stored summaries; no output array regeneration or accuracy audit.
r = runs[IDS[4]]['result']
input_hash = hashlib.sha256(b''.join(struct.pack('<H',halfword(float(i-7))) for i in range(16))).hexdigest()
for backend in ('numpy.fft','scipy.fft'):
    assert r[backend]['input']['sha256'] == input_hash
    assert r[backend]['input']['dtype'] == '<f2'
    assert r[backend]['forward']['real']['dtype'] == r[backend]['forward']['imag']['dtype'] == '<f4'
    assert r[backend]['inverse']['dtype'] == '<f4'
    assert r[backend]['unsupported_norm']['exception'] == 'ValueError'
assert r['complex32_dtype']['exception'] == 'TypeError'
result['checks']['CPU_source_observed_only'] = r
result['indexed_NPY_files'] = sum(len(x) for x in arrays.values())
assert result['indexed_NPY_files'] == 114
(OWN/'file-arithmetic-results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':'retained-file checks consistent in stated finite scopes',
    'ledger_files':219,'indexed_NPY':114,'warning_counts':{k:len(v['warnings']) for k,v in runs.items()},
    'result_sha256':hashlib.sha256((OWN/'file-arithmetic-results.json').read_bytes()).hexdigest()}))
