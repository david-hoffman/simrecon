"""Closed EE113 evidence driver. SOURCE READY UNVERIFIED / execution HOLD.

Canonical entries: --child --spec SPEC.json; --assemble INDEX.json.
No launcher, subprocess, monitor, native-state setter or test-module execution.
All mathematical boxes below are independently evaluated BEFORE reconstruction.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import resource
import sys
import time
from fractions import Fraction as Q
from math import isqrt

ROOT = Path('/workspace/work/issue-113')
BASE = Path('/workspace/work/campaign/evidence/113')
SUPPORT = BASE / 'execution-protocol-source'
TRIALS = BASE / 'execution-trials'
OWN = ROOT / 'docs/reports/single-known-reconstruction'
THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'BLIS_NUM_THREADS', 'NUMEXPR_NUM_THREADS')
CASES = ('EE01', 'EE02', 'EE03', 'EE04')
FORMAL = tuple(f'{case}-{mode}-r{rep}' for case in CASES for rep in (1, 2, 3)
               for mode in (('single', 'double') if rep == 2 else ('double', 'single')))
CONTROLS = {
    'F01': ('Q-fixture-inputs', 'EE01', None, False, 0),
    'F02': ('Q-fixture-inputs', 'EE02', None, False, 0),
    'F03': ('Q-fixture-inputs', 'EE03', None, False, 0),
    'F04': ('Q-fixture-inputs', 'EE04', None, False, 0),
    'E01': ('Q-fenv-read', None, None, False, 0),
    'O01': ('Q-observer-noninterference', 'EE04', 'double', False, 1),
    'O02': ('Q-observer-noninterference', 'EE04', 'double', True, 1),
    'O03': ('Q-observer-noninterference', 'EE04', 'single', False, 1),
    'O04': ('Q-observer-noninterference', 'EE04', 'single', True, 1),
    **{f'L{n:02}': ('Q-launcher-lifecycle', None, None, False, 0) for n in range(1, 8)},
}
BRANCHES = ('fixture', 'fenv', 'interfaces', 'result', 'retention', 'lifecycle', 'synthetic_vectors')
FIXTURE_CHECKS = ('raw_C_f32_all2','raw_exact_shape','q32_q64_literal_components',
    'unspecified_positive_zero_bits','unit_noise_f64','old_metadata_alpha',
    'old_noise_DO_new_noise_TDO','new_spacing_zoom_mapping_provenance',
    'carriers_modulation_dtype_values','original_transfer_metadata','original_owned_readonly_layout',
    'both_records_common_roots_live','normalized_backing_alias_graph','tiny_arrays_lossless',
    'independent_reference_declarations','case_specific_reference_facts')
SETUP = ['imports', 'raw2f32', 'prepare_bands', 'q64', 'q32', 'noise64',
         'carriers_input', 'modulation_input', 'overwrite_old_template',
         'declare_prepared_bands32', 'transfer_input', 'declare_otf',
         'original_transfer_samples', 'transfer_record']
RETAIN = ['raw2f32', 'q64', 'q32', 'noise64', 'transfer_input', 'seed_otf',
          'original_transfer_samples', 'transfer_record', 'carriers_input',
          'modulation_input', 'old_template', 'single_bands']
OPTIONS = dict(wavelength_nm=500, numerical_aperture=1.0, immersion_index=1.0,
               wiener=0.5, suppress_singularities=False, suppression_radius_bins=10.0,
               dampen_order0=False, omit_order0=False, omit_kz0=False,
               output_taper='none', wiener_increment=0.0, power_taper_exponent=None,
               precise_taper=False, filter_overlaps=True, explode_factor=1.0)
NP_NAMES = ('array', 'empty', 'zeros', 'ones', 'full', 'copy', 'empty_like',
            'zeros_like', 'ones_like', 'full_like', 'add', 'subtract', 'multiply', 'exp', 'nditer')
ARTIFACTS = ('admission.json', 'spec.json', 'material.json', 'input-reference.json',
             'owned-child.json', 'session-ready.json', 'bootstrap-error.json', 'samples.jsonl',
             'stdout.json', 'stderr.log', 'launcher-receipt.json', 'outer-events.jsonl',
             'root-closure.json', 'controller-receipt.json')
PROTOCOLS = ('execution-evidence-owner-plan-2.md', 'execution-evidence-fixed-adapter-contract-1.md',
             'execution-evidence-qualification-route-addendum-1.md', 'execution-evidence-qualification-vectors-1.md')
PREREQUISITES = ('scalar_support','fenv_read_route','observer_noninterference',
                 'selected_hypot','selected_phase','cardinal_c64')
U32, U64, H32 = Q(1, 2**24), Q(1, 2**53), Q(1, 2**150)
PI64 = Q(884279719003555, 281474976710656)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def caught_diagnostic(error):
    """Bound caught-path messages/causal frames without consulting source or locals."""
    parts=[]
    used=0
    detail_full=True

    def text(value):
        try:
            value=str(value)
        except BaseException as rendering_error:
            return ('[text unavailable: str raised '+canonical(type(rendering_error).__name__[:512]).decode('ascii')+
                    '; rendering-error category retained first 512 of '+str(len(type(rendering_error).__name__))+
                    ' characters at most; rendering-error message not inspected]')
        prefix=canonical(value[:512]).decode('ascii')
        return prefix+(' [retained first 512 of '+str(len(value))+
                       ' characters; suffix unrecorded: text bound]' if len(value)>512 else '')

    def add(scope,value):
        nonlocal used,detail_full
        line=scope+'='+value
        if used+len(line)+1>7168:
            detail_full=False
            parts.append('diagnostic_suffix_unrecorded_from='+scope+
                         '; reason=7168-ASCII-character detail bound; remaining text/frames/chain not inspected')
            return False
        parts.append(line)
        used+=len(line)+1
        return True

    current=error
    seen=set()
    add('outer_field_scope','category/cause retain first 512 characters; actual category characters='+
        str(len(type(error).__name__))+'; actual immediate-cause category characters='+
        (str(len(type(error.__cause__).__name__)) if error.__cause__ is not None else 'null'))
    for index in range(4):
        if id(current) in seen:
            add('chain_suffix_unrecorded','cycle at exception '+str(index)+'; repeated exception not rendered again')
            break
        seen.add(id(current))
        scope='exception['+str(index)+']'
        # SyntaxError.msg excludes its source-text attribute, matching the
        # existing source-free convention. Never read text, args or locals.
        message=current.msg if isinstance(current,SyntaxError) else current
        if not add(scope+'.category',text(type(current).__name__)) or not add(scope+'.message',text(message)):
            break
        if isinstance(current,SyntaxError):
            if not add(scope+'.syntax_location',text(current.filename)+':'+text(current.lineno)):
                break
        tb=current.__traceback__
        for frame_index in range(8):
            if tb is None:
                break
            code=tb.tb_frame.f_code
            if not add(scope+'.frame['+str(frame_index)+']',
                       text(code.co_filename)+':'+str(tb.tb_lineno)+':'+text(code.co_name)):
                break
            tb=tb.tb_next
        else:
            if tb is not None and not add(scope+'.frame_suffix_unrecorded',
                    'first 8 frames retained; remaining count unobserved: frame bound'):
                break
        if not detail_full:
            break
        # Notes/group members are outside this small causal-frame renderer;
        # say so rather than imply a complete default traceback rendering.
        if not add(scope+'.other_diagnostic_scope',
                   'exception notes/group members unrecorded: caught-path category/message/causal-frame scope'):
            break
        following=current.__cause__
        relation='cause'
        if following is None and not current.__suppress_context__:
            following=current.__context__
            relation='context'
        if following is None:
            add(scope+'.chain_end','no selected cause or unsuppressed context')
            break
        if not add(scope+'.next',relation):
            break
        current=following
    else:
        add('chain_suffix_unrecorded','first 4 exceptions retained; remaining count unobserved: chain bound')
    return {'category':type(error).__name__[:512], 'message':'\n'.join(parts),
            'cause':type(error.__cause__).__name__[:512] if error.__cause__ is not None else None}


def ordinary(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve(strict=True) == path,
            'ordinary absolute path without symlink/escape required')
    require(path.is_file(), 'ordinary file required')
    return path


def read_bytes(path, limit):
    path = ordinary(path)
    require(type(limit) is int and limit > 0 and path.stat().st_size <= limit, 'file byte bound')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'file grew beyond byte bound')
    return raw


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def load_json(path, limit=2097152):
    raw = read_bytes(path, limit)
    return decode(raw), raw


def rational_json(value):
    if isinstance(value, Q):
        return str(value)
    if type(value) is dict:
        return {str(key): rational_json(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [rational_json(item) for item in value]
    return value


def material_core_sha(material):
    """Bind actual material facts without a receipt-containing self-hash cycle."""
    return digest(canonical({key:value for key,value in material.items() if key!='qualification'}))


def qualification_binding(material,key):
    require(key in PREREQUISITES,'closed material prerequisite')
    receipt=material.get('qualification',{}).get(key)
    return (type(receipt) is dict and set(receipt)=={'accepted','material_core_sha256',
                'material_files_sha256','fenv_route_sha256','evidence_sha256'} and receipt['accepted'] is True and
            receipt['material_core_sha256']==material_core_sha(material) and
            receipt['material_files_sha256']==digest(canonical(material['files'])) and
            receipt['fenv_route_sha256']==digest(canonical(material['fenv_route'])) and
            type(receipt['evidence_sha256']) is str and re.fullmatch('[0-9a-f]{64}',receipt['evidence_sha256']) is not None)


def rn(value, bits=53, emin=-1022):
    """Integer nearest-even IEEE rounding, independent of NumPy/libm."""
    value = Q(value)
    if not value:
        return Q(0)
    sign, a = (-1 if value < 0 else 1), abs(value)
    exponent = a.numerator.bit_length() - a.denominator.bit_length()
    if a < Q(2)**exponent:
        exponent -= 1
    step = Q(2)**(max(exponent, emin) - bits + 1)
    units = a / step
    whole, rest = divmod(units.numerator, units.denominator)
    if 2 * rest > units.denominator or (2 * rest == units.denominator and whole % 2):
        whole += 1
    return sign * whole * step


def rn32(value):
    return rn(value, 24, -126)


def sqrt_interval(value):
    require(value >= 0, 'nonnegative independent sqrt')
    k = isqrt((value.numerator << 320) // value.denominator)
    lo = Q(k, 2**160)
    hi = lo if lo * lo == value else Q(k + 1, 2**160)
    require(lo * lo <= value <= hi * hi, 'sqrt square certificate')
    return lo, hi


def box(value):
    return min(value[0], rn(value[0])), max(value[1], rn(value[1]))


def ba(a, b):
    return box((a[0] + b[0], a[1] + b[1]))


def bs(a, b):
    return box((a[0] - b[1], a[1] - b[0]))


def bm(a, b):
    terms = [x * y for x in a for y in b]
    return box((min(terms), max(terms)))


def bd(a, b):
    require(b[0] > 0, 'positive interval divisor')
    terms = [x / y for x in a for y in b]
    return box((min(terms), max(terms)))


def br(a):
    return box((sqrt_interval(a[0])[0], sqrt_interval(a[1])[1]))


def point(value):
    return Q(value), Q(value)


def rounded(a, bits=53):
    function = rn32 if bits == 24 else rn
    return function(a[0]), function(a[1])


def ip(a, b):
    terms = [x * y for x in a for y in b]
    return rounded((min(terms), max(terms)))


def ia(a, b):
    return rounded((a[0] + b[0], a[1] + b[1]))


def iq(a, b):
    require(b[0] > 0, 'positive scalar quotient divisor')
    terms = [x / y for x in a for y in b]
    return rounded((min(terms), max(terms)))


def cell_margin(a, represented):
    if not represented:
        lo, hi = -H32, H32
    else:
        m = abs(represented)
        e = m.numerator.bit_length() - m.denominator.bit_length()
        if m < Q(2)**e:
            e -= 1
        spacing = Q(2)**(max(e, -126) - 23)
        below = spacing / 2 if m == Q(2)**e and e > -126 else spacing
        lo, hi = ((represented - below/2, represented + spacing/2) if represented > 0
                  else (represented - spacing/2, represented + below/2))
    margin = min(a[0] - lo, hi - a[1])
    require(margin > 0, 'independent RN32 cell unresolved')
    return margin


def hypot_transfer_program():
    """Selected glibc moderate union; point-libm-method, never observed abs(H)."""
    a, b = point(1 + Q(1, 2**30)), point(Q(1, 2))
    twice = ba(b, b)
    require(twice[1] < a[0], 'hypot moderate FMA branch')
    fused = br(ba(bm(a, a), bm(b, b)))
    h0 = br(ba(bm(a, a), bm(b, b)))
    require(h0[0] > 2 * b[1], 'hypot non-FMA branch')
    delta = bs(h0, a)
    t1 = bm(bm(point(2), delta), bs(a, twice))
    t2 = ba(bm(bs(bm(point(4), delta), b), b), bm(delta, delta))
    other = bs(h0, bd(ba(t1, t2), bm(point(2), h0)))
    return min(fused[0], other[0]), max(fused[1], other[1])


def empirical_quotients_from_program(a):
    h = hypot_transfer_program()
    power = ip(h, h)
    side = ip(power, point(rn(a*a)))
    denominator = ia(ia(ia(power, side), side), point(Q(1, 4)))
    return iq(point(1 + Q(1, 2**30)), denominator), iq(point(Q(-1, 2)), denominator)


def ieee64(bits):
    sign = -1 if bits >> 63 else 1
    e, f = (bits >> 52) & 2047, bits & (2**52 - 1)
    require(e != 2047, 'finite literal IEEE bits')
    return sign * f * Q(2)**-1074 if not e else sign * (2**52 + f) * Q(2)**(e - 1075)


def sincos_point_program(m):
    require(m in (Q(-1,2), Q(-1,4), Q(0), Q(1,4), Q(1,2)), 'closed phase point')
    if not m:
        return point(1), point(0)
    if abs(m) == Q(1,2):
        h = ieee64(0x3C91A62633145C07)
        require(h**3 < Q(1,2**107) and h**2 < Q(1,2**54), 'tiny correction cells')
        require(rn(Q(3*2**44) + h) == Q(3*2**44), 'standalone/combined knot zero')
        return point(h), point(-1 if m < 0 else 1)
    x, big, knot = PI64/4, Q(3*2**44), Q(101,128)
    require(Q(201,256) < x < Q(203,256) and rn(big+x)-big == knot, 'quarter knot margin')
    t = point(x-knot)
    require(Q(-1,256) < t[0] < Q(1,256), 'quarter residual range')
    sn, ssn, cs, ccs = map(ieee64, (0x3FE6B5CE50B7821A, 0xBC65D5158F702E0F,
                                     0x3FE68B5A92EB6253, 0xBC89A91AD985F89C))
    constants = ('-1.66666666666664880952546298448555e-1', '8.33333214285722277379541354343671e-3',
                 '4.99999999999999999999950396842453e-1', '-4.16666666666664434524222570944589e-2',
                 '1.38888874007937613028114285595617e-3')
    sn3, sn5, cs2, cs4, cs6 = (box(point(Q(v))) for v in constants)
    xx = bm(t,t)
    s = ba(t,bm(bm(t,xx),ba(sn3,bm(xx,sn5))))
    c = bm(xx,ba(cs2,bm(xx,ba(cs4,bm(xx,cs6)))))
    cosine = ba(point(cs),bs(bs(bs(point(ccs),bm(s,point(ssn))),bm(point(cs),c)),bm(point(sn),s)))
    sine = ba(point(sn),ba(bs(ba(point(ssn),bm(s,point(ccs))),bm(point(sn),c)),bm(point(cs),s)))
    return cosine, (-sine[1],-sine[0]) if m < 0 else sine


def taylor(m, sine=False):
    x = PI64 * abs(m)
    term = total = x if sine else Q(1)
    for n in range(1, 33):
        term *= -x*x / ((2*n)*(2*n+1) if sine else (2*n-1)*(2*n))
        total += term
    following = -term*x*x / (66*67 if sine else 65*66)
    result = total+following, total
    return (-result[1],-result[0]) if sine and m < 0 else result


def pi_machin_interval():
    def atan(k):
        x = Q(1,k)
        total = sum(((-1)**n*x**(2*n+1)/(2*n+1) for n in range(65)),Q(0))
        return total-x**131/131, total
    a,b = atan(5),atan(239)
    return 16*a[0]-4*b[1],16*a[1]-4*b[0]


def rotate(a):
    return -a[1], a[0]


def conj(a):
    return a[0],-a[1]


def cadd(a,b):
    return rn32(a[0]+b[0]),rn32(a[1]+b[1])


def cmul(a,b):
    return rn32(rn32(a[0]*b[0])-rn32(a[1]*b[1])),rn32(rn32(a[0]*b[1])+rn32(a[1]*b[0]))


def quarter_dft(shape, entries):
    roots = ((Q(1),Q(0)),(Q(0),Q(1)),(Q(-1),Q(0)),(Q(0),Q(-1)))
    output = []
    for z in range(shape[0]):
        for y in range(shape[1]):
            for x in range(shape[2]):
                re = im = Q(0)
                for (k,j,i),a in entries.items():
                    n = 4*(Q(k*z,shape[0])+Q(j*y,shape[1])+Q(i*x,shape[2]))
                    require(n.denominator == 1,'cardinal root')
                    b = roots[n.numerator%4]
                    re += a[0]*b[0]-a[1]*b[1]
                    im += a[0]*b[1]+a[1]*b[0]
                output.append((re,im))
    return output


def cardinal_fft_envelope(shape,sbar):
    d = sum(n.bit_length()-1 for n in shape)
    n = math.prod(shape)
    require(all(v in (1,2,4) for v in shape) and d*U32 < 1 and sbar < 64,'finite cardinal range')
    return (d*U32*sbar+(n-1)*H32)/(1-d*U32)


def closed_decisions(case):
    """Selected support/ceil/stencil margins, independent of product results."""
    z=4 if case=='EE02' else 2
    hp1=sincos_point_program(Q(1,2))[0]
    numerator=rounded((1-hp1[1],1-hp1[0]))
    cutoff=iq(iq(numerator,point(Q(1,2))),point(Q(1,z)))
    ceiling=lambda value: -((-value.numerator)//value.denominator)
    c0=ceiling(cutoff[0])
    require(c0==ceiling(cutoff[1]),'strict selected ceil bin')
    highest=rn(Q(1.3)*c0)
    clipped=max(z//2-1,0)
    require(c0>=z//2 and highest>=z//2,'selected independent cutoff clipping')
    support=[]
    for x,y in ((Q(0),Q(0)),(Q(1,4),Q(0)),(Q(1,2),Q(0)),
                (Q(0),Q(1,2)),(Q(1,4),Q(1,2)),(Q(1,2),Q(1,2))):
        norm=sqrt_interval(x*x+y*y)
        relation='equal' if norm[0]==norm[1]==Q(1,2) else 'inside' if norm[1]<Q(1,2) else 'outside'
        margin=Q(0) if relation=='equal' else Q(1,2)-norm[1] if relation=='inside' else norm[0]-Q(1,2)
        require(margin>=0,'selected support interval separation')
        support.append({'x':x,'y':y,'norm_reference':norm,'relation_to_R':relation,'margin':margin})
    return {'radial_cutoff':Q(1,2),'self_equality':'included','other_equality':'excluded',
            'support_reference_cases':support,'support_program_applicability':'conditional actual scalar_support qualification; references do not identify native dispatch',
            'ceil_input':cutoff,'ceil_result':c0,'ceil_lower_margin':cutoff[0]-(c0-1),
            'ceil_upper_margin':c0-cutoff[1],'highest_preclip':highest,
            'axial_cutoffs':[clipped,clipped],
            'stencil':'all four radial vertices even at zero weights; nonzero EE03 self row0/1 at1/4, other rows0/1 at0 and1/8, K8'}


def modulation_a():
    return rn(1+Q(1,5*2**23))-Q(1,2**38)


def recipe(case):
    """Frozen literal inputs; rational strings preserve exact declarations."""
    require(case in CASES,'closed case')
    shape = [1,1,3,4,1,4] if case == 'EE02' else [1,1,3,2,2,4]
    entries = ([[0,0,0,0,0,0,'1','0']] if case == 'EE01' else
               [[0,0,0,1,0,1,str(1+Q(1,2**23)),str(2-Q(1,2**22))],
                [0,0,0,3,0,1,str(Q(-13,4)+Q(1,2**22)),str(4+Q(1,2**21))],
                [0,0,1,1,0,1,str(1+Q(1,2**23)),'-3/4'],
                [0,0,2,1,0,1,'-1/2','1/33554432']] if case == 'EE02' else
               [[0,0,1,0,0,1,'1/2','0'],[0,0,2,0,0,1,'0','-1/2']])
    return dict(case_id=case, input_shape=shape, raw={'dtype':'<f4','order':'C','all':'2'},
                quadratures={'q64':'<c16','q32':'<c8','entries':entries,'unspecified_components':'+0'},
                noise={'dtype':'<f8','shape':[1,1,2],'all':'1'},
                carriers={'dtype':'<f8','values':[['-1/8','0']] if case in ('EE03','EE04') else [['0','0']]},
                modulation={'dtype':'<f8' if case == 'EE01' else '<c16',
                            'real':str(modulation_a()) if case == 'EE01' else '1','imag':'0'},
                transfer={'layout':'radial','shape':[2,257,257] if case == 'EE04' else [2,8,8],
                          'dtype':'<c16','input_order':'C','original_order':'F' if case in ('EE03','EE04') else 'C',
                          'formula':'(row+1)*(3+4i)' if case in ('EE03','EE04') else
                                    '(1+2^-30)+i/2' if case == 'EE01' else '1',
                          'seed_formula':'1+i/2' if case == 'EE01' else 'same as original',
                          'dkr':'1','dkz':'1'},
                spacings_zooms=[1,1,1,1],mapping_revision='ce04-svn307-v1',
                provenance=[['formula','explicit half-spectrum; CE alpha units']],options=OPTIONS)


def reference(case):
    """Independent finite witnesses from the frozen named rational sources.

    Terms are conditional source mathematics, never a computed qualification.
    No complex128 FFT certificate is inferred from the c64 cardinal method.
    """
    r = {'case_id':case,'input_representation_error':Q(0),'physical_recovery':'unknown',
         'double_certificate':'unqualified: c128 FFT/scalar program requires separate justification',
         'source_methods':['point-libm-method','point-source-clarification','tiny-default-fft-method'],
         'reference_intervals':[], 'single_program_image':[], 'terms':{}, 'margins':{}}
    if case == 'EE04':
        r['scope'] = 'STORAGE/DTYPE ONLY; no extended accuracy certificate'
        return r
    if case == 'EE01':
        a,delta = modulation_a(),Q(1,2**30)
        h = hypot_transfer_program()
        quotients = empirical_quotients_from_program(a)
        consumed = [rounded(v,24) for v in quotients]
        require(all(lo == hi for lo,hi in consumed),'consumed empirical scale cells')
        r['margins']['consumed_RN32'] = [cell_margin(v,c[0]) for v,c in zip(quotients,consumed,strict=True)]
        exact = (1+delta)/(((1+delta)**2+Q(1,4))*(1+2*a*a)+Q(1,4))
        lib = [(1+delta)/(v*v*(1+2*a*a)+Q(1,4)) for v in h]
        library = max(abs(v-exact) for v in lib)
        scalar = max(abs(quotients[0][0]-max(lib)),abs(quotients[0][1]-min(lib)))
        conversion = max(abs(consumed[0][0]-v) for v in quotients[0])
        r.update(reference_intervals=[point(exact)]*16,single_program_image=[consumed[0][0]]*16,
                 signal_scale=Q(1),cancellation_condition=Q(1),
                 equations={'H':(1+delta,Q(1,2)),'modulation':a,'hypot_program':h,
                            'quotients':quotients,'denominator':'|H|^2*(1+2*a^2)+1/4'})
        ideal_hypot=sqrt_interval((1+delta)**2+Q(1,4))
        r['equations']['hypot_reference']=ideal_hypot
        r['equations']['hypot_library_error_interval']=(h[0]-ideal_hypot[1],h[1]-ideal_hypot[0])
        r['terms'] = dict(library=library,scalar=scalar,scale_conversion=conversion,
                          local=Q(0),phase=Q(0),fft=Q(0),f64_accumulation=Q(0),final_f32=Q(0))
    elif case == 'EE02':
        a=(1+Q(1,2**23),2-Q(1,2**22)); b=(Q(-13,4)+Q(1,2**22),4+Q(1,2**21))
        e=(1+Q(1,2**23),Q(-3,4)); o=(Q(-1,2),Q(1,2**25))
        center={(1,0,1):a,(3,0,1):b,(3,0,3):conj(a),(1,0,3):conj(b)}
        side={(1,0,1):(e[0]-o[1],e[1]+o[0]),(3,0,3):(e[0]+o[1],-e[1]+o[0])}
        represented={(1,0,1):cadd(e,rotate(o)),(3,0,3):cadd(conj(e),rotate(conj(o)))}
        require(sum((abs(v[0])+abs(v[1]) for v in center.values()),Q(0))<21 and
                sum((abs(v[0])+abs(v[1]) for v in represented.values()),Q(0))<4,
                'independent center Sbar21 and side Sbar4 range certificates')
        local=sum((abs(v[0]-represented[k][0])+abs(v[1]-represented[k][1]) for k,v in side.items()),Q(0))
        require(local == Q(1,2**24),'EE02 coefficient algebra')
        c,s = quarter_dft((4,1,4),center),quarter_dft((4,1,4),side)
        cf,sf = cardinal_fft_envelope((4,1,4),Q(21)),cardinal_fft_envelope((4,1,4),Q(4))
        magnitude = 21+cf+2*(4+sf)
        accumulation = 2*U64/(1-2*U64)*magnitude+2*Q(1,2**1075)
        final = U32*(magnitude+accumulation)+H32
        values=[a[0]+2*b[0] for a,b in zip(c,s,strict=True)]
        conditions=[(abs(a[0])+2*abs(b[0]))/abs(v) for a,b,v in zip(c,s,values,strict=True) if v]
        r.update(reference_intervals=[point(v) for v in values],signal_scale=Q(29),
                 cancellation_condition='infinite' if any(not v for v in values) else max(conditions),
                 equations={'center_Sbar':21,'side_Sbar':4,'N':16,'d':4,'Y1_filter_visits':0})
        r['terms']=dict(library=Q(0),scalar=Q(0),scale_conversion=Q(0),local=2*local,
                        phase=Q(0),fft_center=cf,fft_side=2*sf,
                        f64_accumulation=accumulation,final_f32=final)
    else:
        denominator=Q(625,16)+25+Q(2025,64)+Q(1,4)
        require(denominator==Q(6141,64),'EE03 ordered self/negative/center/Wiener powers')
        p=(Q(240,6141),Q(-320,6141)); p64=tuple(rn(v) for v in p); p32=tuple(rn32(v) for v in p64)
        require(p==(Q(15,4)/denominator,Q(-5)/denominator),'independent native scale quotient')
        pi = pi_machin_interval(); pi_error=max(abs(PI64-v) for v in pi)
        eighth=tuple(v/2 for v in sqrt_interval(Q(2)))
        refs=[]; expected=[]; per_pixel=[]; margins=[]
        for x,m in enumerate((Q(1,2),Q(1,4),Q(0),Q(-1,4))):
            u,ideal=p32,p
            for _ in range(x):
                u,ideal=rotate(u),rotate(ideal)
            cs,ss=sincos_point_program(m)
            cr,sr=rounded(cs,24),rounded(ss,24)
            require(cr[0]==cr[1] and sr[0]==sr[1],'phase consumed cells')
            c,s=cr[0],sr[0]; margins.extend((cell_margin(cs,c),cell_margin(ss,s)))
            product=cmul(u,(c,s))
            ic,isin=(point(0),point(1)) if m == Q(1,2) else (point(1),point(0)) if not m else (eighth,eighth if m>0 else (-eighth[1],-eighth[0]))
            rc=[ideal[0]*v for v in ic]; rs=[ideal[1]*v for v in isin]
            refs.append((2*(min(rc)-max(rs)),2*(max(rc)-min(rs))))
            expected.append(2*product[0])
            cm,sm=taylor(m),taylor(m,True)
            terms=dict(scalar=2*sum((abs(a-b) for a,b in zip(p64,p,strict=True)),Q(0)),
                       scale_conversion=2*sum((abs(a-b) for a,b in zip(p32,p64,strict=True)),Q(0)),
                       library=2*(abs(u[0])*max(abs(cs[0]-cm[1]),abs(cs[1]-cm[0]))+abs(u[1])*max(abs(ss[0]-sm[1]),abs(ss[1]-sm[0]))),
                       ramp_conversion=2*(abs(u[0])*max(abs(c-v) for v in cs)+abs(u[1])*max(abs(s-v) for v in ss)),
                       phase=2*(abs(u[0])+abs(u[1]))*abs(m)*pi_error,
                       local=2*abs(product[0]-(u[0]*c-u[1]*s)),fft=Q(0),f64_accumulation=Q(0),final_f32=Q(0))
            per_pixel.append(terms)
        r.update(reference_intervals=refs*4,single_program_image=expected*4,signal_scale=Q(1),
                 cancellation_condition=Q(7),equations={'denominator':Q(6141,64),'exact_scale':p,
                 'N':16,'d':4,'fft_zero_basis':'single nonzero coefficient; exact quarter rotations',
                 'interpolation_error':'0: dyadic affine weights','per_x_terms':per_pixel})
        r['terms']={k:max(v[k] for v in per_pixel) for k in per_pixel[0]}
        r['margins']['consumed_phase_RN32']=min(margins)
        r['margins']['quarter_knot']=min(PI64/4-Q(201,256),Q(203,256)-PI64/4)
    r['conditional_bound']=sum(r['terms'].values(),Q(0))
    r['reference_width']=max(hi-lo for lo,hi in r['reference_intervals'])
    # Closed recipes: R=1/2; relevant x frequencies0,1/4,1/2; strict overlap
    # comparisons at equality exclude. Clipped cuts0 for Z2; Y1 skips filtering.
    r['decisions']=closed_decisions(case)
    return r


def validate_spec(spec,path):
    require(type(spec) is dict and spec['purpose'] in ('formal','qualification'),'closed purpose')
    require(type(spec['driver_sha256']) is str and re.fullmatch('[0-9a-f]{64}',spec['driver_sha256']),
            'explicit actual driver identity pin required; no inferred/default digest')
    require(type(spec['attempt']) is int and spec['attempt'] > 0,'positive attempt')
    require(type(spec['nonce']) is str and re.fullmatch('[A-Za-z0-9_-]{1,64}',spec['nonce']),'nonce')
    require(spec['stage'] in ('phasep-provisional','final-integrated'),'stage')
    require(spec['candidate']['full_status']=='','clean candidate identity')
    require(type(spec['profiled']) is bool,'profile boolean')
    require(type(spec['expected_reconstruction_calls']) is int and spec['expected_reconstruction_calls'] in (0,1),
            'exact integer zero/one reconstruction declaration')
    require(spec['setup_order']==SETUP and spec['retained_root_order']==RETAIN,'literal setup/retention order')
    require(spec['context']=={'fft_workers':1,'backend':'default','numerical_threads':1},'context')
    if spec['purpose']=='formal':
        require(spec['schema']=='EE113-direct-known-v1','formal schema')
        require(type(spec['repetition']) is int and spec['repetition'] in (1,2,3),'formal repetition')
        identifier=f"{spec['case_id']}-{spec['mode']}-r{spec['repetition']}"
        require(spec['trial_id']==identifier and identifier in FORMAL and spec['profiled'],'formal table')
        require(spec['expected_reconstruction_calls']==1 and 'qid' not in spec and 'control_id' not in spec,'formal distinctions')
        directory=TRIALS/identifier/('attempt-'+str(spec['attempt']))
    else:
        control=spec['control_id']
        require(control in CONTROLS and control[0] in ('F','O'),'only F/O numerical driver controls')
        require((spec['qid'],spec['case_id'],spec['mode'],spec['profiled'],spec['expected_reconstruction_calls'])==CONTROLS[control],
                'exact qualification vector')
        require(spec['schema']=='EE113-qualification-v1' and 'repetition' not in spec and 'trial_id' not in spec,'qualification distinctions')
        directory=TRIALS/'qualification'/spec['qid']/('attempt-'+str(spec['attempt']))
    require(path==directory/'spec.json','fixed spec path')
    require(spec['case_id'] in CASES and spec['recipe']=='plan2/'+spec['case_id'],'closed recipe')
    declaration=recipe(spec['case_id'])
    require(canonical(spec['input_declarations'])==canonical(declaration) and spec['recipe_sha256']==digest(canonical(declaration)),
            'pre-frozen literal recipe/bit declarations')
    require(spec['limits']['max_child_record_bytes']==1048576 and spec['limits']['max_interface_events']==512,'fixed output/event bounds')
    return directory


def process_identity():
    tail=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()
    return dict(pid=os.getpid(),start_ticks=int(tail[19]),session_id=os.getsid(0),
                pid_namespace=os.readlink('/proc/self/ns/pid'))


def snapshot_usage():
    sample=resource.getrusage(resource.RUSAGE_SELF)
    return {'monotonic_ns':time.monotonic_ns(),'ru_maxrss_native':int(sample.ru_maxrss),
            'ru_maxrss_native_units':'Linux KiB','cumulative_high_water_bytes':int(sample.ru_maxrss)*1024,
            'rusage_native':{name:getattr(sample,name) for name in dir(sample) if name.startswith('ru_')},
            'scope':'self cumulative snapshot; not terminal wait4, call-only peak or baseline-subtracted peak'}


def import_support(spec):
    path=SUPPORT/'ee113-observation-support-1.py'
    raw=read_bytes(path,1048576)
    require(digest(raw)==spec['support_hashes'][path.name],'fixed observation support pin')
    module_spec=importlib.util.spec_from_file_location('ee113_fixed_observation_support',path)
    require(module_spec is not None and module_spec.loader is not None,'fixed support loader')
    module=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def array_blocks(np,array):
    """Bounded logical-C bytes, including F originals; never a promoted table."""
    dtype=array.dtype.newbyteorder('<')
    with np.nditer(array,flags=['external_loop','buffered','zerosize_ok'],
                   op_flags=['readonly'],op_dtypes=[dtype],order='C',buffersize=4096) as iterator:
        for block in iterator:
            yield block.tobytes(order='C')


def array_digest(np,array):
    result=hashlib.sha256()
    for raw in array_blocks(np,array):
        result.update(raw)
    return result.hexdigest()


def lossless(np,array):
    require(array.dtype.str in ('<f4','<f8','<c8','<c16','<i8') and array.nbytes<=65536,
            'fixed tiny canonical array extent/dtype')
    raw=b''.join(array_blocks(np,array))
    require(len(raw)==array.nbytes,'logical-C byte count')
    return dict(dtype=array.dtype.str,shape=list(array.shape),byte_count=len(raw),
                sha256=digest(raw),base64=base64.b64encode(raw).decode('ascii'))


def array_paths(np,roots):
    """Traverse only the fixed live public dataclass/container roots."""
    found=[]
    def walk(value,path,ancestors):
        if isinstance(value,np.ndarray):
            found.append((path,value)); return
        if id(value) in ancestors:
            return
        ancestors=ancestors|{id(value)}
        if dataclasses.is_dataclass(value) and not isinstance(value,type):
            for field in dataclasses.fields(value):
                walk(getattr(value,field.name),path+'.'+field.name,ancestors)
        elif type(value) in (list,tuple):
            for index,item in enumerate(value):
                walk(item,path+'['+str(index)+']',ancestors)
        elif type(value) is dict:
            for key,item in value.items():
                walk(item,path+'.'+key,ancestors)
    for name,value in roots:
        walk(value,name,set())
    return found


def retention(np,roots):
    paths=array_paths(np,roots)
    tokens={}
    arrays=[]; owners={}
    def token(value):
        if id(value) not in tokens:
            tokens[id(value)]='a'+str(len(tokens)+1)
        return tokens[id(value)]
    for path,array in paths:
        owner=array; seen=set()
        while isinstance(owner.base,np.ndarray) and id(owner) not in seen:
            seen.add(id(owner)); owner=owner.base
        name,owner_name=token(array),token(owner)
        known=owner.base is None and bool(owner.flags.owndata)
        if owner_name not in owners:
            owners[owner_name]={'owner':owner_name,'known':known,
                                'owned_backing_bytes':int(owner.nbytes) if known else None,
                                'unknown_nonarray_base':None if owner.base is None else type(owner.base).__name__}
        arrays.append(dict(path=path,array=name,owner=owner_name,dtype=array.dtype.str,
                           shape=list(array.shape),strides=list(array.strides),elements=int(array.size),
                           logical_bytes=int(array.nbytes),owned_backing_bytes=int(owner.nbytes) if known else None,
                           offset_from_owner_bytes=int(array.__array_interface__['data'][0]-owner.__array_interface__['data'][0]),
                           owns_data=bool(array.flags.owndata),writeable=bool(array.flags.writeable),
                           C=bool(array.flags.c_contiguous),F=bool(array.flags.f_contiguous)))
    return dict(normalized=True,unknown_nonarray_owners_explicit=True,root_order=[name for name,_ in roots],
                arrays=arrays,owners=list(owners.values()),
                unique_known_backing_bytes=sum(v['owned_backing_bytes'] for v in owners.values() if v['known']),
                gaps=['Python record/scalar/container overhead is not array payload',
                      'nonarray bases unknown where reported; internal FFT/iterator/native workspace unobserved',
                      'ephemeral call lifetimes require source audit and weak interface ledger; this is live retained roots only'])


def immutable_state(np,roots):
    return {name:{'dtype':a.dtype.str,'shape':list(a.shape),'strides':list(a.strides),
                  'writeable':bool(a.flags.writeable),'sha256':array_digest(np,a)}
            for name,a in array_paths(np,roots)}


def setup(np,sr,case,counts):
    declaration=recipe(case)
    shape=tuple(declaration['input_shape'])
    raw=np.full(shape,2.0,dtype=np.float32,order='C')
    counts['prepare_bands']+=1
    old=sr.prepare_bands(raw,dxy_um=1.0,dz_um=1.0,norders=2,background=0.0,
                         lateral_zoom=1,axial_zoom=1,flatfield_slope=None,
                         exposure_background=None,phases_rad=None,edge_pixels=0,
                         equalize=False,equalize_z=False,equalize_time=False)
    qshape=(*shape[:3],*shape[3:5],shape[5]//2+1)
    q64=np.zeros(qshape,dtype=np.complex128,order='C')
    for entry in declaration['quadratures']['entries']:
        index=tuple(entry[:6]); re,im=Q(entry[6]),Q(entry[7])
        q64.real[index]=float(re); q64.imag[index]=float(im)
    q32=np.zeros(qshape,dtype=np.complex64,order='C')
    for entry in declaration['quadratures']['entries']:
        # Independent literal declaration, with no q64/preparation conversion truth.
        index=tuple(entry[:6]); re,im=Q(entry[6]),Q(entry[7])
        q32.real[index]=float(re); q32.imag[index]=float(im)
    noise=np.ones((1,1,2),dtype=np.float64)
    carriers=np.array([[-0.125,0.0]] if case in ('EE03','EE04') else [[0.0,0.0]],dtype=np.float64)
    modulation=np.array([[float(modulation_a())]],dtype=np.float64) if case=='EE01' else np.ones((1,1),dtype=np.complex128)
    old.quadratures[...] = q64
    old.noise_variance_factors[...] = noise[0]
    counts['declare_prepared_bands32']+=1
    single=sr.declare_prepared_bands32(q32,noise,input_shape=shape,dxy_um=1.0,dz_um=1.0,
        lateral_zoom=1,axial_zoom=1,mapping_revision='ce04-svn307-v1',
        provenance=(('formula','explicit half-spectrum; CE alpha units'),))
    tshape=tuple(declaration['transfer']['shape'])
    source=np.empty(tshape,dtype=np.complex128,order='C')
    if case in ('EE03','EE04'):
        for row in range(tshape[1]):
            source[:,row,:]=(row+1)*(3+4j)
    else:
        source.fill(1+0.5j if case=='EE01' else 1+0j)
    counts['declare_otf']+=1
    seed=sr.declare_otf(source,layout='radial',dkr_cyc_um=1.0,dkz_cyc_um=1.0)
    if case=='EE02':
        original=seed.samples
    else:
        original=np.array(seed.samples,dtype=np.complex128,copy=True,
                          order='F' if case in ('EE03','EE04') else 'C')
        if case=='EE01':
            original.real[...] = 1+2**-30
        original.flags.writeable=False
    transfer=dataclasses.replace(seed,samples=original)
    roots=list(zip(RETAIN,(raw,q64,q32,noise,source,seed,original,transfer,
                          carriers,modulation,old,single),strict=True))
    return roots


def fixture_observation(np,roots,case,ref,expected_document):
    values=dict(roots); raw=values['raw2f32']; old=values['old_template']; single=values['single_bands']
    original=values['original_transfer_samples']; seed=values['seed_otf']; table=values['transfer_record']
    q64,q32=values['q64'],values['q32']; declaration=recipe(case)
    def literal_components():
        entries={tuple(e[:6]):(Q(e[6]),Q(e[7])) for e in declaration['quadratures']['entries']}
        exact=True; zeros=True
        for index in np.ndindex(q64.shape):
            real,imag=entries.get(index,(Q(0),Q(0)))
            for array in (q64,q32):
                value=array[index]
                exact=exact and Q(float(value.real))==real and Q(float(value.imag))==imag
                zeros=zeros and (real!=0 or not bool(np.signbit(value.real))) and (imag!=0 or not bool(np.signbit(value.imag)))
        return exact,zeros
    components,zeros=literal_components()
    graph=retention(np,roots)
    original_fact=next(row for row in graph['arrays'] if row['path']=='original_transfer_samples')
    reference_facts={'center_Sbar':21,'side_Sbar':4} if case=='EE02' else {
        'denominator':'6141/64','per_order_elements':66049 if case=='EE04' else 64} if case in ('EE03','EE04') else {
        'original_real':'1+2^-30','original_imag':'1/2','modulation':str(modulation_a()),
        'consumed_RN32_margins':rational_json(ref['margins'])}
    transfer_ok=table.layout=='radial' and table.dkr_cyc_um==table.dkz_cyc_um==1.0 and table.norders==2
    transfer_ok=transfer_ok and table.source_revision==seed.source_revision and table.reference_sha256==seed.reference_sha256
    if case in ('EE03','EE04'):
        transfer_values=all(bool(np.all(original[:,row,:]==(row+1)*(3+4j))) for row in range(original.shape[1]))
    else:
        transfer_values=bool(np.all(original==(1+2**-30+0.5j if case=='EE01' else 1+0j)))
    checks=dict(raw_C_f32_all2=raw.dtype==np.float32 and bool(raw.flags.c_contiguous) and bool(np.all(raw==2)),
        raw_exact_shape=list(raw.shape)==declaration['input_shape'],q32_q64_literal_components=components,
        unspecified_positive_zero_bits=zeros,unit_noise_f64=values['noise64'].dtype==np.float64 and bool(np.all(values['noise64']==1)),
        old_metadata_alpha=isinstance(old.input_shape,tuple) and old.input_shape==tuple(raw.shape) and old.input_scale==1/math.prod(raw.shape[3:])
            and old.source_revision=='SVN307' and bool(old.reference_sha256),
        old_noise_DO_new_noise_TDO=old.noise_variance_factors.shape==(1,2) and single.noise_variance_factors.shape==(1,1,2)
            and bool(np.all(old.noise_variance_factors==1)) and bool(np.all(single.noise_variance_factors==1)),
        new_spacing_zoom_mapping_provenance=single.dxy_um==single.dz_um==1.0 and single.lateral_zoom==single.axial_zoom==1
            and single.mapping_revision=='ce04-svn307-v1' and single.provenance==(('formula','explicit half-spectrum; CE alpha units'),),
        carriers_modulation_dtype_values=values['carriers_input'].dtype==np.float64 and
            Q(float(values['carriers_input'][0,0]))==(Q(-1,8) if case in ('EE03','EE04') else 0) and
            values['modulation_input'].dtype==(np.float64 if case=='EE01' else np.complex128) and
            Q(float(values['modulation_input'][0,0].real))==(modulation_a() if case=='EE01' else 1),
        original_transfer_metadata=transfer_ok,original_owned_readonly_layout=bool(original.flags.owndata) and
            not bool(original.flags.writeable) and bool(original.flags.f_contiguous if case in ('EE03','EE04') else original.flags.c_contiguous),
        both_records_common_roots_live=len(roots)==12 and type(old).__name__=='PreparedBands' and type(single).__name__=='PreparedBands32'
            and old.quadratures.dtype==np.complex128 and single.quadratures.dtype==np.complex64 and
            array_digest(np,old.quadratures)==array_digest(np,q64) and array_digest(np,single.quadratures)==array_digest(np,q32),
        normalized_backing_alias_graph=graph['normalized'],tiny_arrays_lossless=True,
        independent_reference_declarations=expected_document['declarations']==declaration and expected_document['reference']==rational_json(ref),
        case_specific_reference_facts=transfer_values)
    arrays={name:lossless(np,values[name]) for name in ('raw2f32','q64','q32','noise64','carriers_input','modulation_input')}
    return {'case_id':case,'checks':checks,'reference_facts':reference_facts,'arrays':arrays,
            'original_transfer':{**original_fact,'sha256_logical_C':array_digest(np,original),'recipe':declaration['transfer']},
            'old_metadata':{field.name:getattr(old,field.name) for field in dataclasses.fields(old)
                            if not isinstance(getattr(old,field.name),np.ndarray)},
            'single_metadata':{field.name:getattr(single,field.name) for field in dataclasses.fields(single)
                               if not isinstance(getattr(single,field.name),np.ndarray)},
            'old_double_reshape_copy':'F-order per-order reshape(-1) may materialize c128 copy; source-only fact, not executed by fixture control'}


def accuracy(np,image,ref,mode,fenv,material,case):
    reasons=[]
    if case=='EE04':
        return {'qualified':False,'unqualified_reasons':['EE04 STORAGE/DTYPE ONLY'],'metrics':None,'reference':rational_json(ref)}
    require(image.size==16,'fixed output observations')
    actual=[Q(float(v)) for v in image.reshape(-1)]
    require(bool(np.isfinite(image).all()),'nonfinite image')
    pairs=ref['reference_intervals']
    distances=[max(lo-v,v-hi,Q(0)) for v,(lo,hi) in zip(actual,pairs,strict=True)]
    far=[max(abs(v-lo),abs(v-hi)) for v,(lo,hi) in zip(actual,pairs,strict=True)]
    rms_lo=sqrt_interval(sum((v*v for v in distances),Q(0))/16)[0]
    rms_hi=sqrt_interval(sum((v*v for v in far),Q(0))/16)[1]
    if mode=='double':
        reasons.append(ref['double_certificate'])
    required=['scalar_support','fenv_read_route','observer_noninterference']
    required+=['selected_hypot'] if case=='EE01' else ['cardinal_c64'] if case=='EE02' else ['selected_phase','cardinal_c64']
    for key in required:
        if not qualification_binding(material,key):
            reasons.append('current material qualification missing: '+key)
    if not fenv['qualified_material'] or not fenv['controls_unchanged'] or not all(
        fenv[edge]['usable_read'] and fenv[edge]['suitable_controls'] for edge in ('pre','post')):
        reasons.append('actual same-child fenv/material unsuitable or unqualified')
    within=max(far)<=ref['conditional_bound']+ref['reference_width']
    return {'qualified':not reasons,'unqualified_reasons':reasons,
            'conditional_envelope_contains_observation':within if mode=='single' else None,
            'metrics':rational_json(dict(reference_width=ref['reference_width'],interval_distance=max(distances),
                far_endpoint_upper_bound=max(far),max_absolute_error_lower=max(distances),max_absolute_error_upper=max(far),
                rms_lower=rms_lo,rms_upper=rms_hi,signed_minimum=min(actual),signed_maximum=max(actual),
                signal_scale=ref['signal_scale'],error_over_signal_scale=max(far)/ref['signal_scale'],
                cancellation_condition=ref['cancellation_condition'],phase_at_zero_amplitude='undefined')),
            'reference':rational_json(ref),'scope':'independent reference per mode; qualification is conditional and distinct from envelope agreement'}


def result_observation(np,result,options,before,after):
    names=('image','filtered_quadratures','x_um','y_um','z_um','carriers_cyc_um','modulation','axial_cutoffs_bins')
    arrays={name:lossless(np,getattr(result,name)) for name in names}
    require(all(bool(np.isfinite(getattr(result,name)).all()) for name in names),'nonfinite result array')
    metadata={field.name:getattr(result,field.name) for field in dataclasses.fields(result)
              if not isinstance(getattr(result,field.name),np.ndarray)}
    return dict(arrays=arrays,metadata=metadata,field_order=[field.name for field in dataclasses.fields(result)],supplied_options=options,
                input_immutability={'before':before,'after':after,'unchanged':before==after})


def event_mapping(ledger,mode):
    """Map actual caller observations to narrow source claims, without inference."""
    sources={
        '_filter':('single_known.py:_filter','copied/filtered/full side c64 storage'),
        '_assemble':('single_known.py:_assemble','c64 padded/inverse; f64 accumulator; final f32'),
        '_ramp':('single_known.py:_ramp','one f64 phase and one c128 ramp per purpose; <=65536 ELEMENTS'),
        '_bulk_product32':('single_known.py:_bulk_product32','separate f32 component products/sums; c64 product'),
        '_blocks':('single_known.py:_blocks','nditer requested buffersize65536; native internal workspace unknown'),
        'assemble_signed_image':('known_parameters.py:assemble_signed_image','double c128 FFT I/O; supplied omissions retained'),
        'filter_native_quadratures':('known_parameters.py:filter_native_quadratures','double c128 diagnostics'),
    }
    rows=[]
    for event in ledger['events']:
        source,claim=sources.get(event['caller']['function'],('unmapped caller','event retained; no automatic arithmetic claim'))
        rows.append({'event_index':event['index'],'source':source,'claim':claim,'mode':mode,
                     'status':'reached interface observation; independent source/lifetime audit required'})
    return {'events':rows,'derived_scratch_bound':65536,'bound_units':'ELEMENTS per purpose',
            'original_source_exempt':True,'internal_fft_precision':'unknown','internal_fft_workspace':'unknown',
            'gaps':['ndarray methods, scalar operators, existing aliases and native paths are not universally wrapped',
                    'requested nditer buffersize does not expose internal buffer ownership or precision',
                    'event shapes alone do not certify per-purpose concurrent lifetimes or every promotion']}


def child(path):
    spec,raw_spec=load_json(path)
    directory=validate_spec(spec,path)
    counts={name:0 for name in ('prepare_bands','declare_otf','declare_prepared_bands32','reconstruct_known')}
    record={'schema':spec['schema'],'purpose':spec['purpose'],'attempt':spec['attempt'],'nonce':spec['nonce'],
            'case_id':spec['case_id'],'mode':spec['mode'],'profiled':spec['profiled'],'phase':'complete',
            'spec_sha256':digest(raw_spec),'material_sha256':spec['material_sha256'],
            'input_reference_sha256':spec['input_reference_sha256'],'process':process_identity(),
            'setup_calls':counts,'reconstruction_calls':0,'observations':{name:None for name in BRANCHES},
            'status':'setup_failed','error':None}
    qualification=spec['purpose']=='qualification'
    if qualification:
        record.update(qid=spec['qid'],control_id=spec['control_id'])
    else:
        record.update(trial_id=spec['trial_id'],repetition=spec['repetition'],stage=spec['stage'],
                      candidate=spec['candidate'])
    roots=[]; result=None; ledger=None; snapshots={}; timing={}; phase='setup'
    try:
        require(sys.platform=='linux' and sys.byteorder=='little','required native Linux little endian')
        require({key:os.environ.get(key) for key in THREADS}=={key:'1' for key in THREADS},'thread controls before numerical imports')
        require(digest(read_bytes(OWN/'execution-driver.py',2097152))==spec['driver_sha256'],'actual driver bytes')
        for name,expected in spec['scientific_source_hashes'].items():
            require(name in ('src/simrecon/reconstruction/single_known.py','src/simrecon/reconstruction/known_parameters.py',
                             'src/simrecon/__init__.py','src/simrecon/reconstruction/__init__.py'),'closed scientific source map')
            require(digest(read_bytes(ROOT/name,2097152))==expected,'scientific source identity')
        require(len(spec['scientific_source_hashes'])==4,'all four scientific source pins')
        material,raw_material=load_json(directory/'material.json')
        require(digest(raw_material)==spec['material_sha256'],'actual material identity')
        ref=reference(spec['case_id'])  # BEFORE imports, setup and the candidate R.
        declaration=recipe(spec['case_id'])
        expected={'schema':'EE113-input-reference-v1','case_id':spec['case_id'],
                  'recipe_sha256':digest(canonical(declaration)),
                  'declarations':declaration,'reference':rational_json(ref)}
        input_reference,raw_reference=load_json(directory/'input-reference.json')
        require(digest(raw_reference)==spec['input_reference_sha256'] and canonical(input_reference)==canonical(expected),
                'frozen independent input/reference document')
        observation=import_support(spec)
        import numpy as np
        import scipy
        import scipy.fft as fft
        import simrecon as sr
        import simrecon.reconstruction.known_parameters as known
        import simrecon.reconstruction.single_known as single_module
        require(Path(sr.__file__).resolve()==ROOT/'src/simrecon/__init__.py' and
                Path(known.__file__).resolve()==ROOT/'src/simrecon/reconstruction/known_parameters.py' and
                Path(single_module.__file__).resolve()==ROOT/'src/simrecon/reconstruction/single_known.py',
                'actual current worktree imports')
        outer_worker_before=fft.get_workers()
        with fft.set_workers(1):
            require(fft.get_workers()==1,'actual worker context')
            context_worker=fft.get_workers()
            roots=setup(np,sr,spec['case_id'],counts)
            values=dict(roots)
            baseline=immutable_state(np,roots)
            if spec['expected_reconstruction_calls']==0:
                record['observations']['fixture']=fixture_observation(np,roots,spec['case_id'],ref,input_reference)
                record['observations']['retention']=retention(np,roots)
            else:
                bindings={'simrecon.reconstruction.known_parameters.ifftn':known.ifftn,'scipy.fft.ifftn':fft.ifftn}
                bindings.update({'numpy.'+name:getattr(np,name) for name in NP_NAMES})
                disabled={'profiled':False,'events':[],'coverage_gaps':['profile off: no wrappers installed'],
                          'restoration':{},'workers':{'before':fft.get_workers(),'context':fft.get_workers()},
                          'overflow':False}
                manager=observation.observe_interfaces(spec['mode'],bindings) if spec['profiled'] else contextlib.nullcontext(disabled)
                with manager as ledger:
                    snapshots['pre_call']=snapshot_usage()
                    pre=observation.read_fenv()
                    route=material['fenv_route']
                    require(set(route)=={'selected_library','resolved_library','library_sha256',
                            'system','machine','byteorder','pointer_bytes','buffer_bytes','x87_offset','mxcsr_offset'},
                            'exact pre-frozen fenv route fields')
                    pre_corresponds=all(pre['abi'].get(key)==value for key,value in route.items())
                    require(pre['usable_read'] and pre['suitable_controls'] and pre_corresponds,
                            'BLOCKED: actual pre-call fenv/ABI/material unsuitable')
                    phase='call'
                    counts['reconstruct_known']+=1
                    record['reconstruction_calls']+=1
                    start=time.monotonic_ns()
                    try:
                        result=sr.reconstruct_known(values['old_template'] if spec['mode']=='double' else values['single_bands'],
                            values['transfer_record'],carriers_cyc_um=values['carriers_input'],
                            modulation=values['modulation_input'],**OPTIONS,
                            precision='double' if spec['mode']=='double' else 'single-mixed-v1')
                    finally:
                        end=time.monotonic_ns()
                        # This getter is immediate: no result/finite/hash/retention NumPy work first.
                        post=observation.read_fenv()
                        snapshots['call_end']=snapshot_usage()
                        timing={'call_start_monotonic_ns':start,'call_end_monotonic_ns':end,
                                'elapsed_call_seconds':(end-start)/1e9}
                        record['observations']['fenv']={'pre':pre,'post':post,
                            'controls_unchanged':pre['controls'] is not None and pre['controls']==post['controls'],
                            'qualified_material':pre_corresponds and all(post['abi'].get(key)==value for key,value in route.items())
                                and qualification_binding(material,'fenv_read_route'),
                            'exception_status_bits':'raw bits retained; excluded from controls comparison',
                            'snapshots':snapshots,'timing':timing}
                phase='observation'
                require(result is not None,'one result required')
                roots.append(('result',result))
                after=immutable_state(np,roots[:-1])
                record['observations']['result']=result_observation(np,result,
                    {**OPTIONS,'precision':'double' if spec['mode']=='double' else 'single-mixed-v1'},baseline,after)
                record['observations']['retention']=retention(np,roots)
                if not spec['profiled']:
                    ledger['workers']['after']=fft.get_workers()
                record['observations']['interfaces']=ledger
                record['observations']['interfaces']['source_audit_mapping']=event_mapping(ledger,spec['mode'])
                numerical_accuracy=accuracy(np,result.image,ref,spec['mode'],record['observations']['fenv'],material,spec['case_id'])
                if qualification:
                    record['observations']['fenv']['accuracy']=numerical_accuracy
                else:
                    record.update(record_schemas={'old':type(values['old_template']).__name__,
                        'single':type(values['single_bands']).__name__,'selected':'PreparedBands' if spec['mode']=='double' else 'PreparedBands32'},
                        timing=timing,snapshots=snapshots,accuracy=numerical_accuracy,
                        context={'threads':{key:os.environ.get(key) for key in THREADS},
                                 'numpy_version':np.__version__,'scipy_version':scipy.__version__,
                                 'workers_context':fft.get_workers(),'backend':'default; internal attribution unknown'})
        outer_worker_after=fft.get_workers()
        require(outer_worker_before==outer_worker_after,'SciPy worker context restoration')
        if not qualification:
            record.setdefault('context',{}).update(workers_before=outer_worker_before,workers_after=outer_worker_after)
        elif record['observations']['fenv'] is not None:
            record['observations']['fenv']['outer_workers']={'before':outer_worker_before,
                'context':context_worker,'after':outer_worker_after,'restored':outer_worker_before==outer_worker_after}
        elif record['observations']['fixture'] is not None:
            record['observations']['fixture']['workers']={'before':outer_worker_before,
                'context':context_worker,'after':outer_worker_after,'restored':outer_worker_before==outer_worker_after}
        if 'call_end' in snapshots:
            snapshots['post_observation']=snapshot_usage()
        record['status']='complete'
    except Exception as error:
        record['status']={'setup':'setup_failed','call':'call_failed','observation':'observation_failed'}[phase]
        record['error']=caught_diagnostic(error)
        if ledger is not None:
            record['observations']['interfaces']=ledger
        if not qualification:
            record['snapshots']=snapshots; record['timing']=timing
    # Locals roots/result intentionally remain live through serialization/emission.
    try:
        raw=canonical(record)+b'\n'
    except (ValueError,TypeError,OverflowError) as error:
        # Impossible encoding is distinct from a serializable byte overflow.
        # Keep every individually serializable actual branch/field; unavailable
        # state is explicit, not a fabricated byte encoding or success.
        missing=[]
        for name,value in record['observations'].items():
            try:
                canonical(value)
            except (ValueError,TypeError,OverflowError):
                record['observations'][name]=None
                missing.append('observations.'+name)
        for name in tuple(record):
            if name in ('observations','error'):
                continue
            try:
                canonical(record[name])
            except (ValueError,TypeError,OverflowError):
                record[name]=None
                missing.append(name)
        record['status']='observation_failed'
        record['error']={'category':'SerializationImpossible','message':
            'actual fields unrecorded because JSON encoding failed: '+','.join(missing),
            'cause':type(error).__name__}
        raw=canonical(record)+b'\n'
    if len(raw)>1048576:
        original_size=len(raw)
        record['status']='observation_failed'
        previous_error=record['error']
        message=('child stdout byte bound exceeded; original_record_bytes='+str(original_size)+
            '; limit_bytes=1048576; attempted_failure_bytes={size:020d}; '
            'actual emitted length belongs to parent stream receipt; monitor/write interruption '
            'may leave partial JSON/unavailable suffix; complete overflow transport is not guaranteed')
        if previous_error is not None:
            message+='; prior failure='+canonical(previous_error).decode('ascii').replace('{','{{').replace('}','}}')
        record['error']={'category':'SerializationBound','message':message.format(size=0),
                         'cause':previous_error['category'] if previous_error else None}
        # ROOT narrow overflow decision: preserve COMPLETE serializable observed
        # state in the SAME stdout artifact; unchanged budget overshoot is failure.
        # Fixed-width attempted length avoids a recursive JSON size dependency.
        raw=canonical(record)+b'\n'
        failure_size=len(raw)
        record['error']['message']=message.format(size=failure_size)
        raw=canonical(record)+b'\n'
        require(len(raw)==failure_size,'fixed-width failure size accounting')
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return 0 if record['status']=='complete' else 1


# Closed source/archive names. Paths here are future assembly inputs, not a
# SOURCE-author permission to read additional files. ROOT freezes every entry.
SOURCE_NAMES = (
    'AGENTS.md','.agents/skills/implement-work/SKILL.md',
    'docs/agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md',
    'docs/contracts/single-known-reconstruction-v1.md','docs/contracts/wide-allocation-domain-v1.md',
    'docs/contracts/c-equivalence-known-parameters-v1.md','docs/contracts/c-equivalence-optical-transfer-v1.md',
    'docs/contracts/c-equivalence-preprocessing-v1.md',
    'src/simrecon/reconstruction/single_known.py','src/simrecon/reconstruction/known_parameters.py',
    'src/simrecon/__init__.py','src/simrecon/reconstruction/__init__.py',
    'src/simrecon/acquisition/preparation.py','src/simrecon/optical_transfer.py',
    'scripts/check_installed_wheels.py','uv.lock','pyproject.toml',
    'tests/single_known_fixture.py','tests/test_single_known_boundary.py','tests/test_single_known_filter.py',
    'tests/test_single_known_assembly.py','tests/test_single_known_precision.py','tests/test_single_known_typing.py',
    'tests/test_module_migration.py','tests/test_installed_wheels.py',
    'docs/reports/single-known-reconstruction/execution-driver.py',
    *('docs/packets/precision-113/'+name for name in (
        'public-context.md','legacy-compatibility-public.md','tiny-default-fft-method.md','point-libm-method.md',
        'point-source-clarification.md','a1-wide-test-safety-addendum.md','finite-dependency-public-facts-1.md',
        'acceptance-stage-routing-v1.md','finite-qualification-public-facts-2.md','finite-scalar-native-public-facts-3.md',
        'init-tool-public-facts-4.md','guard-metadata-public-facts-5.md')),
)
SUPPORT_NAMES=('ee113-launcher-1.py','ee113-observation-support-1.py','ee113-init-controller-1.py')
MANIFESTS=('ee-driver-source-1-inputs.sha256','b6-accepted-inputs.sha256','a7-import-checkpoint-1/test-inputs.sha256')
ARCHIVE_MAX={'index_bytes':8388608,'per_file_bytes':16777216,'aggregate_bytes':268435456,'artifact_count':100000}


def archive_source_paths():
    result={str(ROOT/name):('source','sources/worktree/'+name) for name in SOURCE_NAMES}
    result.update({str(SUPPORT/name):('source','sources/ROOT/'+name) for name in SUPPORT_NAMES})
    result.update({str(BASE/name):('protocol','protocol/'+name) for name in PROTOCOLS})
    result.update({str(BASE/name):('input_manifest','inputs/'+name) for name in MANIFESTS})
    return result


def attempt_directory(identifier,attempt,qualification):
    require(type(attempt) is int and attempt>0,'positive archive attempt')
    return TRIALS/'qualification'/identifier/('attempt-'+str(attempt)) if qualification else TRIALS/identifier/('attempt-'+str(attempt))


def tiny_archive_array(value):
    require(type(value) is dict and set(value)=={'dtype','shape','byte_count','sha256','base64'},'lossless array fields')
    require(value['dtype'] in ('<f4','<f8','<c8','<c16','<i8'),'lossless dtype')
    require(type(value['shape']) is list and len(value['shape'])<=6 and
            all(type(n) is int and 0<=n<=65536 for n in value['shape']),'tiny shape')
    raw=base64.b64decode(value['base64'],validate=True)
    expected=int(value['dtype'][2:])*math.prod(value['shape'])
    require(expected==value['byte_count']==len(raw) and expected<=65536 and digest(raw)==value['sha256'],
            'lossless byte count/digest')
    if value['dtype']!='<i8':
        width=4 if value['dtype'] in ('<f4','<c8') else 8
        fraction_bits,exponent_mask=(23,255) if width==4 else (52,2047)
        require(all((int.from_bytes(raw[start:start+width],'little')>>fraction_bits)&exponent_mask != exponent_mask
                    for start in range(0,len(raw),width)),'finite IEEE array components')


def archived_child(record,spec,spec_sha):
    """Validate direct-known identity/representation; raw failures stay failures."""
    require(type(record) is dict,'child record object')
    for key in ('schema','purpose','attempt','nonce','case_id','mode','profiled'):
        require(record[key]==spec[key] and type(record[key]) is type(spec[key]),'child/spec identity '+key)
    require(record['spec_sha256']==spec_sha and record['material_sha256']==spec['material_sha256'] and
            record['input_reference_sha256']==spec['input_reference_sha256'],'child input/material identity')
    require(record['status'] in ('complete','setup_failed','call_failed','observation_failed'),'child status')
    require(set(record['observations'])==set(BRANCHES),'observation inventory')
    counts=record['setup_calls']
    require(set(counts)=={'prepare_bands','declare_otf','declare_prepared_bands32','reconstruct_known'} and
            all(type(v) is int and v>=0 for v in counts.values()),'setup counts')
    require(type(record['reconstruction_calls']) is int and record['reconstruction_calls'] in (0,1) and
            counts['reconstruct_known']==record['reconstruction_calls'],'actual reconstruction count')
    require(set(record['process'])=={'pid','start_ticks','session_id','pid_namespace'} and
            record['process']['pid']==record['process']['session_id'] and
            type(record['process']['start_ticks']) is int and record['process']['start_ticks']>0,'owned child facts')
    if spec['purpose']=='qualification':
        require(set(record)=={'schema','purpose','qid','control_id','attempt','nonce','case_id','mode',
            'profiled','phase','spec_sha256','material_sha256','input_reference_sha256','process',
            'setup_calls','reconstruction_calls','observations','status','error'},'exact qualification child fields')
        require(record['qid']==spec['qid'] and record['control_id']==spec['control_id'],'qualification identity')
    else:
        require(record['trial_id']==spec['trial_id'] and record['repetition']==spec['repetition'] and
                record['stage']==spec['stage'] and record['candidate']==spec['candidate'],'formal identity')
    if record['status']!='complete':
        require(type(record['error']) is dict and set(record['error'])=={'category','message','cause'},'structured failure')
        return
    expected_phase='alive_before_stop' if spec.get('control_id') in ('L04','L05','L06') else 'complete'
    require(record['error'] is None and record['phase']==expected_phase and
            record['reconstruction_calls']==spec['expected_reconstruction_calls'],'completed count/phase')
    control=spec.get('control_id')
    applicable=({'fixture','retention'} if control and control.startswith('F') else
                {'fenv','synthetic_vectors'} if control=='E01' else
                {'lifecycle','synthetic_vectors'} if control=='L07' else
                {'lifecycle'} if control and control.startswith('L') else
                {'interfaces','result','retention','fenv'})
    require(all((record['observations'][name] is not None)==(name in applicable) for name in BRANCHES),
            'applicable branches versus explicit null')
    if spec['case_id'] is not None:
        require(all(counts[key]==1 for key in ('prepare_bands','declare_otf','declare_prepared_bands32')),'common setup counts')
    if not spec['expected_reconstruction_calls']:
        if control and control.startswith('F'):
            fixture=record['observations']['fixture']
            require(set(fixture['checks'])==set(FIXTURE_CHECKS) and all(type(v) is bool for v in fixture['checks'].values()),'closed fixture checks')
            require(fixture['case_id']==spec['case_id'],'fixture identity')
            for value in fixture['arrays'].values():
                tiny_archive_array(value)
        elif control=='E01':
            require([v['id'] for v in record['observations']['synthetic_vectors']]==
                    ['E01a','E01b','E01c','E01d','E01e','E01f'],'six fenv vectors')
        elif control=='L07':
            require([v['id'] for v in record['observations']['synthetic_vectors']]==
                    ['P1','P2','P3','R1','R2','R3','R4','R5'],'eight lifecycle vectors')
        return
    result=record['observations']['result']
    require(set(result['arrays'])=={'image','filtered_quadratures','x_um','y_um','z_um','carriers_cyc_um','modulation','axial_cutoffs_bins'},'result array inventory')
    for value in result['arrays'].values():
        tiny_archive_array(value)
    require(result['supplied_options']=={**OPTIONS,'precision':'double' if spec['mode']=='double' else 'single-mixed-v1'},'explicit options')
    require(result['input_immutability']['unchanged'] is True and
            result['input_immutability']['before']==result['input_immutability']['after'],'input immutability')
    graph=record['observations']['retention']
    require(graph['normalized'] is True and graph['unknown_nonarray_owners_explicit'] is True and
            graph['root_order']==[*RETAIN,'result'],'common live-root retention')
    ledger=record['observations']['interfaces']
    require(ledger['profiled'] is spec['profiled'] and ledger['workers']['context']==1 and len(ledger['events'])<=512,'interface context')
    if not spec['profiled']:
        require(ledger['events']==[] and ledger['restoration']=={},'profile off')
    else:
        require(ledger['overflow'] is False and len(ledger['restoration'])==17 and all(
            row['exact_original_restored'] is True and row['wrapper_unchanged_before_restore'] is True
            for row in ledger['restoration'].values()),'actual restoration')
        events=[row for row in ledger['events'] if any(name in ('simrecon.reconstruction.known_parameters.ifftn','scipy.fft.ifftn') for name in row['aliases'])]
        require(len(events)==2,'two FFT events')
        dtype='<c16' if spec['mode']=='double' else '<c8'
        shape=[4,1,4] if spec['case_id']=='EE02' else [2,2,4]
        for row in events:
            require(row['args'][0]['dtype']==row['result']['dtype']==dtype and
                    row['args'][0]['shape']==row['result']['shape']==shape,'actual FFT I/O')
            require(row['resolved']['axes']==[0,1,2] and row['resolved']['workers']==1 and
                    row['resolved']['overwrite_x'] is False and row['resolved']['norm']=='forward','FFT controls')
    if spec['purpose']=='formal':
        snapshots=record['snapshots']; fenv=record['observations']['fenv']; timing=record['timing']
        require(set(snapshots)=={'pre_call','call_end','post_observation'},'native snapshot scopes')
        require(snapshots['pre_call']['monotonic_ns']<=fenv['pre']['read_start_monotonic_ns']<=timing['call_start_monotonic_ns']
                <=timing['call_end_monotonic_ns']<=fenv['post']['read_start_monotonic_ns']
                <=snapshots['call_end']['monotonic_ns']<=snapshots['post_observation']['monotonic_ns'],'call/fenv order')
        require(timing['elapsed_call_seconds']==(timing['call_end_monotonic_ns']-timing['call_start_monotonic_ns'])/1e9,'actual call timing')
        for row in snapshots.values():
            require(type(row['ru_maxrss_native']) is int and row['ru_maxrss_native']>=0 and
                    row['ru_maxrss_native_units']=='Linux KiB' and row['cumulative_high_water_bytes']==row['ru_maxrss_native']*1024,'native usage units')


def assemble(index_path):
    require(index_path==TRIALS/'index.json','fixed ROOT INDEX path')
    index,raw_index=load_json(index_path,ARCHIVE_MAX['index_bytes'])
    require(set(index)=={'schema','root_released','bounds','artifacts','formal','qualification','prerequisite_evidence'} and
            index['schema']=='EE113-index-v1' and index['root_released'] is True,'exact ROOT assembly INDEX')
    bounds=index['bounds']
    require(set(bounds)==set(ARCHIVE_MAX) and all(type(bounds[k]) is int and 0<bounds[k]<=v for k,v in ARCHIVE_MAX.items()),'finite ROOT archive operating bounds')
    require(len(raw_index)<=bounds['index_bytes'] and type(index['artifacts']) is list and len(index['artifacts'])<=bounds['artifact_count'],'index/count bound')
    prerequisites=index['prerequisite_evidence']
    require(type(prerequisites) is dict and set(prerequisites)==set(PREREQUISITES),
            'exact six inline prerequisite evidence keys')
    prerequisite_count=0
    for key in PREREQUISITES:
        require(type(prerequisites[key]) is list,'ordered prerequisite evidence versions')
        for version in prerequisites[key]:
            require(type(version) is dict and set(version)=={'evidence_sha256','artifacts'} and
                    type(version['evidence_sha256']) is str and re.fullmatch('[0-9a-f]{64}',version['evidence_sha256']) and
                    type(version['artifacts']) is list,'closed prerequisite evidence version')
            prerequisite_count+=len(version['artifacts'])
            require(len(index['artifacts'])+prerequisite_count<=bounds['artifact_count'],
                    'combined file/inline prerequisite artifact-count bound')
    require([row['trial_id'] for row in index['formal']]==list(FORMAL),'exact ordered formal24 inventory')
    require([row['control_id'] for row in index['qualification']]==list(CONTROLS),'exact closed16 qualification inventory')
    allowed=archive_source_paths()
    attempt_rows=[]; global_attempts=set()
    for qualification,rows in ((False,index['formal']),(True,index['qualification'])):
        for row in rows:
            keys={'control_id','qid','attempts','not_run_reason'} if qualification else {'trial_id','attempts','not_run_reason'}
            require(set(row)==keys and type(row['attempts']) is list,'exact inventory row')
            identifier=row['qid'] if qualification else row['trial_id']
            if qualification:
                require(row['qid']==CONTROLS[row['control_id']][0],'qualification QID/control linkage')
            require((row['not_run_reason'] is None)==bool(row['attempts']) and
                    (bool(row['attempts']) or (type(row['not_run_reason']) is str and bool(row['not_run_reason'])),'NOT_RUN explicit reason')
            numbers=[]
            for attempt in row['attempts']:
                require(set(attempt)=={'attempt','superseded','superseded_reason','disposition','reason','artifacts'},'attempt fields')
                number=attempt['attempt']; directory=attempt_directory(identifier,number,qualification)
                key=(identifier,number)
                require(key not in global_attempts,'unique QID/trial attempt; no control collision')
                global_attempts.add(key); numbers.append(number)
                require(type(attempt['superseded']) is bool and
                        ((attempt['superseded_reason'] is None) if not attempt['superseded'] else
                         type(attempt['superseded_reason']) is str and bool(attempt['superseded_reason'])),'superseded reason')
                require(attempt['disposition'] in ('completed','failed','aborted','material_invalidated') and
                        type(attempt['reason']) is str and bool(attempt['reason']),'raw attempt disposition/reason')
                required=[]
                for name in ARTIFACTS:
                    restore=str((directory/name).relative_to(BASE))
                    allowed[str(directory/name)]=('attempt',restore)
                    required.append(restore)
                activation=directory/'activation.json' if qualification else TRIALS/'activations'/(identifier+'-attempt-'+str(number)+'.json')
                restore=str(activation.relative_to(BASE)); allowed[str(activation)]=('activation',restore); required.append(restore)
                require(type(attempt['artifacts']) is list and sorted(attempt['artifacts'])==sorted(required),'all fixed artifacts present OR missing')
                attempt_rows.append((qualification,row,attempt,directory))
            require(numbers==sorted(numbers) and len(set(numbers))==len(numbers),'ordered unique explicit attempt numbers')
    blobs={}; restore_map={}; by_path={}; source_versions={}; source_missing={}; total=len(raw_index)
    source_paths=archive_source_paths()
    for entry in index['artifacts']:
        fields={'kind','path','restore_path','present','sha256','byte_count','missing_reason'}
        is_source=entry.get('kind') in ('source','protocol','input_manifest') if type(entry) is dict else False
        if is_source:
            fields|={'locator','inline_base64'}
        require(type(entry) is dict and set(entry)==fields,'artifact fields')
        path=entry['path']; restore=entry['restore_path']
        inline=is_source and entry['locator']=='inline'
        version=None
        require(path in allowed and entry['kind']==allowed[path][0],'closed artifact category/logical path')
        if inline:
            require(path in source_paths,'only exact closed sources allow historical inline bytes')
            prefix='sources/versions/'
            require(restore.startswith(prefix),'versioned source restore path')
            rest=restore[len(prefix):]
            version,separator,suffix=rest.partition('/')
            require(re.fullmatch('[0-9a-f]{64}',version) is not None and separator=='/' and
                    suffix==source_paths[path][1],'exact historical digest/source restore linkage')
        else:
            require((entry['kind'],restore)==allowed[path],'fixed file restore spelling')
            if is_source:
                require(entry['locator']=='file' and entry['inline_base64'] is None,'mutually exclusive source file locator')
        relative=PurePosixPath(restore)
        require(not relative.is_absolute() and '..' not in relative.parts and str(relative)==restore,'portable relative restore path')
        require((inline or path not in by_path) and restore not in restore_map,'unique artifact/restore mapping')
        require(type(entry['present']) is bool,'presence boolean')
        if entry['present']:
            require(entry['missing_reason'] is None and type(entry['byte_count']) is int and entry['byte_count']>=0 and
                    re.fullmatch('[0-9a-f]{64}',entry['sha256'] or ''),'present byte identity')
            require(entry['byte_count']<=bounds['per_file_bytes'],'declared per-file bound')
            if inline:
                require(entry['sha256']==version and type(entry['inline_base64']) is str and
                        len(entry['inline_base64'])<=4*((bounds['per_file_bytes']+2)//3),'finite inline source encoding')
                data=base64.b64decode(entry['inline_base64'],validate=True)
            else:
                data=read_bytes(Path(path),bounds['per_file_bytes'])
            require(len(data)==entry['byte_count'] and digest(data)==entry['sha256'],'artifact actual byte count/hash')
            total+=len(data); require(total<=bounds['aggregate_bytes'],'aggregate bound; no dropped raw evidence')
            blobs.setdefault(entry['sha256'],dict(sha256=entry['sha256'],byte_count=len(data),base64=base64.b64encode(data).decode('ascii')))
            restore_map[restore]={'sha256':entry['sha256'],'byte_count':len(data),'missing_reason':None,'local_provenance':path}
            if is_source:
                key=(path,entry['sha256'])
                require(key not in source_versions and key not in source_missing,'unique logical source/version')
                source_versions[key]=data
            if not inline:
                by_path[path]=data
        else:
            require(entry['sha256'] is None and entry['byte_count'] is None and
                    type(entry['missing_reason']) is str and bool(entry['missing_reason']),'missing bytes remain null with reason')
            if inline:
                require(entry['inline_base64'] is None,'unavailable historical bytes are not encoded')
                key=(path,version)
                require(key not in source_missing and key not in source_versions,'unique missing historical source/version')
                source_missing[key]=entry['missing_reason']
            else:
                require(not Path(path).exists() and not Path(path).is_symlink(),'listed missing artifact actually absent')
                require(Path(path).parent.resolve(strict=True)==Path(path).parent,'missing artifact parent has no symlink/escape')
            restore_map[restore]={'sha256':None,'byte_count':None,'missing_reason':entry['missing_reason'],'local_provenance':path}
            if not inline:
                by_path[path]=None
    required_attempt_paths={str(directory/name) for _,_,_,directory in attempt_rows for name in ARTIFACTS}
    require(required_attempt_paths<=set(by_path),'attempt file omissions forbidden')
    for source_path in archive_source_paths():
        require(source_path in by_path and by_path[source_path] is not None,
                'all closed source/protocol/input artifacts must be portable')
    for _,_,attempt,_ in attempt_rows:
        require(set(attempt['artifacts'])<=set(restore_map),'activation/artifact entries all listed')
    # Native-renewal evidence is DATA under these six fixed keys only. No path,
    # command, parser/plugin, new scientific control or qualification flag is
    # selected here. Supporting raw/source/closure/material facts must have
    # actual portable bytes; a path/hash without those bytes is an explicit gap.
    prerequisite_versions={}; prerequisite_manifest={key:[] for key in PREREQUISITES}
    roles={'evidence','raw','source','closure','material'}
    for key in PREREQUISITES:
        for version in prerequisites[key]:
            evidence_sha=version['evidence_sha256']
            identity=(key,evidence_sha)
            require(identity not in prerequisite_versions,'unique prerequisite key/evidence version')
            seen_roles=[]; missing=[]; restored=[]
            for position,entry in enumerate(version['artifacts']):
                require(type(entry) is dict and set(entry)=={'role','restore_path','present','sha256','byte_count','base64','missing_reason'},
                        'inline-only prerequisite artifact fields')
                role=entry['role']
                require(role in roles and type(entry['present']) is bool,'closed prerequisite role/presence')
                restore=f'prerequisite-evidence/{key}/{evidence_sha}/{role}/{position}'
                require(entry['restore_path']==restore and restore not in restore_map,
                        'unique derived versioned prerequisite restore key')
                seen_roles.append(role); restored.append(restore)
                if entry['present']:
                    require(entry['missing_reason'] is None and type(entry['byte_count']) is int and
                            0<=entry['byte_count']<=bounds['per_file_bytes'] and
                            type(entry['sha256']) is str and re.fullmatch('[0-9a-f]{64}',entry['sha256']) and
                            type(entry['base64']) is str and len(entry['base64'])<=4*((bounds['per_file_bytes']+2)//3),
                            'finite inline prerequisite byte declaration')
                    data=base64.b64decode(entry['base64'],validate=True)
                    require(len(data)==entry['byte_count'] and digest(data)==entry['sha256'] and
                            base64.b64encode(data).decode('ascii')==entry['base64'],
                            'strict canonical prerequisite base64/count/SHA256')
                    require(role!='evidence' or entry['sha256']==evidence_sha,'same-key evidence/version digest')
                    total+=len(data)
                    require(total<=bounds['aggregate_bytes'],'combined aggregate prerequisite byte bound')
                    blobs.setdefault(entry['sha256'],dict(sha256=entry['sha256'],byte_count=len(data),base64=entry['base64']))
                    restore_map[restore]={'sha256':entry['sha256'],'byte_count':len(data),'missing_reason':None,'local_provenance':None}
                else:
                    require(entry['sha256'] is None and entry['byte_count'] is None and entry['base64'] is None and
                            type(entry['missing_reason']) is str and bool(entry['missing_reason']),
                            'unavailable prerequisite bytes remain null with explicit reason')
                    missing.append({'restore_path':restore,'reason':entry['missing_reason']})
                    restore_map[restore]={'sha256':None,'byte_count':None,'missing_reason':entry['missing_reason'],'local_provenance':None}
            require(seen_roles.count('evidence')==1 and set(seen_roles)==roles,
                    'one evidence artifact and explicit raw/source/closure/material supporting facts')
            manifest={'evidence_sha256':evidence_sha,'artifacts':restored,'missing_artifacts':missing}
            prerequisite_versions[identity]=manifest
            prerequisite_manifest[key].append(manifest)
    def source_version(path,expected_hash):
        raw=source_versions.get((path,expected_hash))
        reason=source_missing.get((path,expected_hash),'historical source version not supplied in closed INDEX')
        require(raw is not None,'source version unavailable: '+path+' @ '+expected_hash+'; '+reason)
        require(digest(raw)==expected_hash,'resolved source version identity')
        return raw
    # INDEX raw bytes are embedded without inventing a self hash field in INDEX.
    index_sha=digest(raw_index)
    blobs.setdefault(index_sha,dict(sha256=index_sha,byte_count=len(raw_index),base64=base64.b64encode(raw_index).decode('ascii')))
    restore_map['execution-trials/index.json']={'sha256':index_sha,'byte_count':len(raw_index),'missing_reason':None,'local_provenance':str(index_path)}
    observations=[]; qualified_controls=set(); qualified_bindings={}
    for qualification,row,attempt,directory in attempt_rows:
        raw_spec=by_path[str(directory/'spec.json')]
        raw_stdout=by_path[str(directory/'stdout.json')]
        receipt_raw=by_path[str(directory/'controller-receipt.json')]
        observation={'purpose':'qualification' if qualification else 'formal','id':row.get('control_id',row.get('trial_id')),
                     'attempt':attempt['attempt'],'superseded':attempt['superseded'],
                     'superseded_reason':attempt['superseded_reason'],'disposition':attempt['disposition'],
                     'reason':attempt['reason'],'parse_category':'missing','record':None,'controller':None,'runtime_eligible':False}
        try:
            require(raw_spec is not None,'missing spec')
            spec=decode(raw_spec)
            if qualification:
                require(spec['purpose']=='qualification' and spec['schema']=='EE113-qualification-v1' and
                        spec['control_id']==row['control_id'] and spec['qid']==row['qid'] and
                        (spec['qid'],spec['case_id'],spec['mode'],spec['profiled'],spec['expected_reconstruction_calls'])==CONTROLS[row['control_id']],
                        'qualification closed spec identity')
            else:
                require(spec['purpose']=='formal' and spec['schema']=='EE113-direct-known-v1' and
                        spec['trial_id']==row['trial_id'],'formal closed spec identity')
            require(spec['attempt']==attempt['attempt'],'attempt/spec identity')
            require(type(spec['driver_sha256']) is str and re.fullmatch('[0-9a-f]{64}',spec['driver_sha256']),
                    'all formal/control specs require explicit actual driver identity pin')
            for name,key in (('material.json','material_sha256'),('input-reference.json','input_reference_sha256')):
                data=by_path[str(directory/name)]
                require((data is None and spec[key] is None) or (data is not None and digest(data)==spec[key]),'attempt input identity')
            material_raw=by_path[str(directory/'material.json')]
            require(material_raw is not None,'required actual material document')
            material=decode(material_raw)
            binding_fields={name:spec[name] for name in (
                'candidate','stage','scientific_source_hashes','support_hashes',
                'driver_sha256','primary_protocol_hashes')}
            binding_fields['material_core_sha256']=material_core_sha(material)
            binding=digest(canonical(binding_fields))
            observation['qualification_binding_sha256']=binding
            require(type(material['files']) is dict and bool(material['files']),'material explicit file map')
            for source_path,expected_hash in material['files'].items():
                require(source_path in source_paths,'material logical source outside exact allowlist')
                source_version(source_path,expected_hash)
            current_matches=all(by_path.get(source_path) is not None and digest(by_path[source_path])==expected_hash
                                for source_path,expected_hash in material['files'].items())
            source_version(str(OWN/'execution-driver.py'),spec['driver_sha256'])
            current_matches=current_matches and digest(by_path[str(OWN/'execution-driver.py')])==spec['driver_sha256']
            require(set(spec['support_hashes'])==set(SUPPORT_NAMES) and
                    set(spec['primary_protocol_hashes'])==set(PROTOCOLS),'closed support/protocol source maps')
            for name,expected_hash in spec['support_hashes'].items():
                source_version(str(SUPPORT/name),expected_hash)
                current_matches=current_matches and digest(by_path[str(SUPPORT/name)])==expected_hash
            for name,expected_hash in spec['primary_protocol_hashes'].items():
                source_version(str(BASE/name),expected_hash)
                current_matches=current_matches and digest(by_path[str(BASE/name)])==expected_hash
            for name,expected_hash in spec['scientific_source_hashes'].items():
                require(str(ROOT/name) in source_paths,'closed scientific logical source')
                source_version(str(ROOT/name),expected_hash)
                current_matches=current_matches and digest(by_path[str(ROOT/name)])==expected_hash
            observation['current_source_matches']=current_matches
            for prerequisite,claim in material.get('qualification',{}).items():
                require(prerequisite in PREREQUISITES,'closed material prerequisite evidence key')
                if type(claim) is dict and claim.get('accepted') is True:
                    evidence_sha=claim.get('evidence_sha256')
                    portable=prerequisite_versions.get((prerequisite,evidence_sha))
                    require(portable is not None,'accepted prerequisite evidence version unavailable: '+prerequisite)
                    require(not portable['missing_artifacts'] and evidence_sha in blobs,
                            'accepted prerequisite evidence/support bytes unavailable: '+prerequisite)
            if spec['case_id'] is not None:
                expected_recipe=recipe(spec['case_id'])
                require(spec['recipe']=='plan2/'+spec['case_id'] and canonical(spec['input_declarations'])==canonical(expected_recipe) and
                        spec['recipe_sha256']==digest(canonical(expected_recipe)),'closed archived recipe')
                expected_reference={'schema':'EE113-input-reference-v1','case_id':spec['case_id'],
                    'recipe_sha256':spec['recipe_sha256'],'declarations':expected_recipe,
                    'reference':rational_json(reference(spec['case_id']))}
                require(canonical(decode(by_path[str(directory/'input-reference.json')]))==canonical(expected_reference),
                        'archived independent reference document')
            require(raw_stdout is not None,'missing child stdout')
            if qualification and row['control_id']=='L03':
                require(raw_stdout==b'{','exact expected malformed L03 bytes')
                observation['parse_category']='expected_malformed_child_record'
            else:
                record=decode(raw_stdout)
                archived_child(record,spec,digest(raw_spec))
                observation['record']=record; observation['parse_category']=record['status']
            require(receipt_raw is not None,'missing controller receipt')
            controller=decode(receipt_raw); observation['controller']=controller
            require(controller['spec_sha256']==digest(raw_spec) and controller['attempt']==attempt['attempt'],'controller attempt identity')
            identifier=spec['qid'] if qualification else spec['trial_id']
            require(controller['schema']=='EE113-controller-receipt-v1' and
                    controller['released_id']==identifier,'controller release identity')
            closure=by_path[str(directory/'root-closure.json')]
            inner=by_path[str(directory/'launcher-receipt.json')]
            require(closure is not None and inner is not None and digest(closure)==controller['root_closure_sha256'] and
                    digest(inner)==controller['inner_receipt_sha256'],'raw closure/inner receipt identities')
            closure_record=decode(closure)
            require(closure_record['schema']=='EE113-root-closure-v1' and
                    closure_record['spec_sha256']==digest(raw_spec) and
                    closure_record['attempt']==attempt['attempt'] and
                    closure_record['released_id']==identifier and
                    closure_record['actual_pid1_terminal_and_reaped'] is True and
                    closure_record['actual_old_host_pid_absent'] is True and
                    closure_record['engine_running'] is False and closure_record['engine_pid']==0,
                    'actual separate ROOT namespace closure')
            require(controller['proxy_reaped'] is True and controller['pipes_closed'] is True and
                    controller['inner_raw_receipt_immutable'] is True and controller['hold_reasons']==[], 'actual controller closure facts')
            inner_record=decode(inner)
            require(inner_record['schema']=='EE113-launcher-receipt-v1' and
                    inner_record['spec_sha256']==digest(raw_spec) and inner_record['root_closure']=='pending' and
                    by_path[str(directory/'admission.json')] is not None and
                    inner_record['admission_sha256']==digest(by_path[str(directory/'admission.json')]),'immutable inner/admission receipt')
            terminal=inner_record.get('terminal')
            require(terminal is not None and terminal['pid']==inner_record['workload_pid'] and
                    not inner_record['wait_ownership_lost'] and not inner_record.get('cleanup_gap'),'sole child terminal usage')
            if observation['record'] is not None:
                require(terminal['pid']==observation['record']['process']['pid'],'exact record/terminal PID')
            if qualification:
                require(controller['qualification_verdict']=='matched' and
                        inner_record['qid']==spec['qid'] and inner_record['control_id']==spec['control_id'] and
                        inner_record['attempt']==spec['attempt'] and inner_record['expected']==spec['expected_outcome'] and
                        inner_record['expected_outcome_matched_before_closure'] is True and
                        all(check['passed'] is True for check in inner_record['checks'].values()),'qualification not matched')
                if current_matches and attempt['disposition']=='completed':
                    qualified_controls.add(row['control_id'])
                    qualified_bindings.setdefault(binding,set()).add(row['control_id'])
            else:
                require(observation['parse_category']=='complete' and spec['stage']=='final-integrated' and
                        inner_record['status']=='complete_child_observed_pending_scientific_qualification' and
                        not inner_record.get('stop_reason') and terminal['returncode']==0,'formal runtime eligibility')
                observation['runtime_eligible']=attempt['disposition']=='completed' and current_matches
                observation['terminal']=terminal
        except (ValueError,KeyError,TypeError,UnicodeError) as error:
            observation['validation_failure']={'category':type(error).__name__,'message':str(error)[:256]}
            if observation['parse_category']=='missing' and raw_stdout is not None:
                observation['parse_category']='malformed_or_unvalidated_raw_child_record'
        observations.append(observation)
    for observation in observations:
        if observation['purpose']=='formal' and observation['runtime_eligible']:
            binding=observation['qualification_binding_sha256']
            observation['qualification_chain_matches']=qualified_bindings.get(binding,set())==set(CONTROLS)
            observation['runtime_eligible']=observation['qualification_chain_matches']
    summaries=[]
    for case in CASES:
        for mode in ('double','single'):
            selected=[row for row in observations if row['purpose']=='formal' and row['runtime_eligible'] and
                      row['record']['case_id']==case and row['record']['mode']==mode]
            # Superseded flag never drops scientific data. Multiple eligible
            # attempts for one repetition remain ambiguous; no best-of selection.
            reps=[row['record']['repetition'] for row in selected]
            bindings={row['qualification_binding_sha256'] for row in selected}
            complete=sorted(reps)==[1,2,3] and len(selected)==3 and len(bindings)==1
            summary={'case_id':case,'mode':mode,'status':'matched_three_runtime_observations' if complete else 'INCOMPLETE',
                     'eligible_attempt_count':len(selected),'repetitions':reps,
                     'reason':None if complete else 'requires matched closed16 controls and exactly one eligible actual attempt for each r1,r2,r3',
                     'call_seconds':None,'terminal_high_water_bytes':None,'retained_backing_bytes':None,
                     'accuracy_qualified_count':sum(row['record']['accuracy']['qualified'] for row in selected)}
            if complete:
                for key,values in (
                    ('call_seconds',[row['record']['timing']['elapsed_call_seconds'] for row in selected]),
                    ('terminal_high_water_bytes',[row['terminal']['kernel_reported_direct_child_high_water_bytes'] for row in selected]),
                    ('retained_backing_bytes',[row['record']['observations']['retention']['unique_known_backing_bytes'] for row in selected])):
                    values=sorted(values); summary[key]={'raw':values,'median':values[1],'minimum':values[0],'maximum':values[-1]}
            summaries.append(summary)
    output={'schema':'EE113-execution-archive-v1','status':'ASSEMBLED_RAW_UNVERIFIED','index_sha256':index_sha,
            'formal_inventory':index['formal'],'qualification_inventory':index['qualification'],
            'prerequisite_evidence':prerequisite_manifest,
            'blob_table':blobs,'restore_map':restore_map,'observations':observations,'summaries':summaries,
            'counts':{'attempts':len(observations),'failed':sum(row['disposition']=='failed' for row in observations),
                      'aborted':sum(row['disposition']=='aborted' for row in observations),
                      'material_invalidated':sum(row['disposition']=='material_invalidated' for row in observations),
                      'superseded':sum(row['superseded'] for row in observations),'matched_controls':len(qualified_controls)},
            'limits':['raw failures/superseded attempts remain portable; no best-of selection',
                      'runtime summaries are not accuracy, physical recovery, installed/fullgate or fresh-D acceptance',
                      'self snapshots, terminal wait4, sampled RSS, retained payload and call time remain distinct',
                      'no baseline subtraction; FFT internal precision/workspace unknown; profiling costs included']}
    report=render_report(output)
    # Only these two fixed tracked destinations are writable. No restore helper,
    # attempt creation, recursive discovery, commands or product imports.
    require(OWN.resolve(strict=True)==OWN,'fixed ordinary output directory')
    for name in ('execution-runs.json','execution-report.md'):
        target=OWN/name
        require(not target.is_symlink() and (not target.exists() or
                target.is_file() and target.resolve(strict=True)==target),'fixed ordinary output destination')
    (OWN/'execution-runs.json').write_bytes(canonical(output)+b'\n')
    (OWN/'execution-report.md').write_text(report,encoding='utf-8')
    return 0


def render_report(output):
    lines=['# EE113 execution evidence','',
           'ASSEMBLED RAW / UNVERIFIED. Independent scientific, code/protocol and final gate review remain required.','',
           '| Case | Mode | Runtime observations | Eligible attempts | Call median seconds | Terminal median KiB / bytes | Retained median bytes |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for row in output['summaries']:
        call=row['call_seconds']; peak=row['terminal_high_water_bytes']; payload=row['retained_backing_bytes']
        peak_text=str(peak['median']//1024)+' / '+str(peak['median']) if peak else 'unavailable'
        lines.append(f"| {row['case_id']} | {row['mode']} | {row['status']} | {row['eligible_attempt_count']} | {call['median'] if call else 'unavailable'} | {peak_text} | {payload['median'] if payload else 'unavailable'} |")
    lines.extend(['','| Purpose / ID | Attempt | Disposition | Raw child classification | Runtime eligible |',
                  '| --- | --- | --- | --- | --- |'])
    for row in output['observations']:
        lines.append(f"| {row['purpose']} / {row['id']} | {row['attempt']} | {row['disposition']} | {row['parse_category']} | {row['runtime_eligible']} |")
    lines.extend(['','| Formal ID / attempt | Accuracy qualified | Reference width | Absolute error upper | RMS enclosure | Signed extrema |',
                  '| --- | --- | --- | --- | --- | --- |'])
    for row in output['observations']:
        record=row['record']
        if row['purpose']!='formal' or record is None or 'accuracy' not in record:
            continue
        accuracy_record=record['accuracy']; metrics=accuracy_record.get('metrics')
        if metrics is None:
            lines.append(f"| {row['id']} / {row['attempt']} | False | storage only or unavailable | unavailable | unavailable | unavailable |")
            continue
        lines.append(f"| {row['id']} / {row['attempt']} | {accuracy_record['qualified']} | {metrics['reference_width']} | {metrics['max_absolute_error_upper']} | [{metrics['rms_lower']}, {metrics['rms_upper']}] | [{metrics['signed_minimum']}, {metrics['signed_maximum']}] |")
        if accuracy_record['unqualified_reasons']:
            lines.extend(['','Unqualified '+row['id']+' attempt '+str(row['attempt'])+': '+
                          '; '.join(accuracy_record['unqualified_reasons'])+'.',''])
    lines.extend(['','All actual attempts, raw failures, aborted/material-invalidated/superseded records and explicit missing reasons are in the portable blob table and restore map. Local absolute paths are provenance only.','',
                  'EE04 is storage/dtype only. Each double mode retains its separate unsupported c128 FFT/scalar certificate. Single envelopes remain conditional on actual material and same-child fenv. No universal benefit, physical accuracy, internal FFT precision, pristine cache or isolated algorithm peak is claimed.','',
                  'Common setup retains raw, both q64/q32 declarations, noise, transfer input/seed/original/record, carriers/modulation, legitimate old template and independent new32 record in both modes; result is appended. Original F-order tables can cause legitimate old-double per-order reshape copies. Profiling costs remain in runtime/RSS.','',
                  'Call timing, self cumulative snapshots, sole direct-child terminal wait4, sampled RSS/HWM, retained owner payload and ROOT whole-private-init closure are separate observations. No baseline subtraction supplies an algorithm peak.',''])
    lines.extend(['Complete stage terms, interval-distance/far bounds, signal scale, cancellation conditions, pre/call-end/post snapshots, effective context/material/source identities and all raw arrays/streams are retained per attempt in execution-runs.json.','',
                  'An over-budget child emits a complete observation_failed record on the same stdout where possible; parent interruption may leave partial JSON/unavailable suffix. Complete overflow transport is not promised, and overflow never qualifies.',''])
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--child',action='store_true')
    group.add_argument('--assemble',type=Path)
    parser.add_argument('--spec',type=Path)
    args=parser.parse_args()
    if args.child:
        require(args.spec is not None,'canonical --child --spec required')
        return child(args.spec)
    require(args.spec is None,'assembly accepts only INDEX')
    return assemble(args.assemble)


if __name__=='__main__':
    try:
        exit_status=main()
    except Exception as error:
        # Invalid/unreadable pre-record input cannot supply a valid child
        # identity. Preserve bounded source-free detail in existing stderr;
        # parent retains missing/malformed stdout as failure, never completion.
        diagnostic=caught_diagnostic(error)
        sys.stderr.buffer.write(canonical({'schema':'EE113-pre-record-failure-v1',
            'status':'failed','category':diagnostic['category'],
            'message':diagnostic['message']})+b'\n')
        sys.stderr.buffer.flush()
        exit_status=1
    raise SystemExit(exit_status)
