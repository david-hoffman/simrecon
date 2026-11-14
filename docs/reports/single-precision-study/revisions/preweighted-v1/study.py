"""SP112 report-only finite kernels; never a product single reconstruction entry.

Oracle uses rational CE04 scalar filtering and sparse finite inverse sums.
Only roots 1,i,-1,-i and eighth roots are needed. sqrt(2) is enclosed by
rational endpoints checked by squaring. No FFT or product helper is an oracle.
"""
from __future__ import annotations
import argparse
import dataclasses
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
from scipy import fft
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from preflight import environment

SQLO = F(1414213562373095048801688724209698078569,10**39)
SQHI = SQLO + F(1,10**39)
assert SQLO*SQLO < 2 < SQHI*SQHI
OPTICS = dict(wavelength_nm=500,numerical_aperture=1.,immersion_index=1.)


def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identities():
    files = ['docs/reports/single-precision-study/study.py',
             'docs/reports/single-precision-study/preflight.py','uv.lock',
             'src/simrecon/reconstruction/known_parameters.py',
             'src/simrecon/reconstruction/parameter_estimation.py',
             'src/simrecon/acquisition/preparation.py','src/simrecon/optical_transfer.py',
             'docs/contracts/c-equivalence-known-parameters-v1.md',
             'docs/contracts/c-equivalence-carrier-modulation-v1.md']
    return {p:sha(ROOT/p) for p in files}


def pair(a,b=0): return (F(a),F(b))
def add(a,b): return (a[0]+b[0],a[1]+b[1])
def mul(a,b): return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def conj(a): return (a[0],-a[1])
def norm(a): return a[0]*a[0]+a[1]*a[1]
def scale(a,s): return (a[0]*s,a[1]*s)
def ascomplex(a): return complex(float(a[0]),float(a[1]))


def declarations():
    rows=[]
    def row(name,T=1,D=1,O=2,Z=2,Y=4,X=4,L=1,**kw):
        rows.append(dict(name=name,T=T,D=D,O=O,Z=Z,Y=Y,X=X,L=L,A=1,**kw))
    row('M02-signed')
    row('M03-zero-mod',zero_mod=True)
    row('M03-carrier-positive',carrier=1)
    row('M03-carrier-negative',carrier=-1)
    row('M04-directions',D=3,O=3,Z=4,Y=8,X=8)
    for p in [-100,0,100]: row('M05-power'+str(p),power=p)
    row('M06-near-cancel',cancel='near')
    row('M06-exact-cancel',cancel='exact')
    row('M16-times',T=2,D=3,O=3,Z=4,Y=8,X=8)
    row('M19-spatial32',D=3,O=3,Z=4,Y=32,X=32,L=2)
    row('M19-spatial64',D=3,O=3,Z=4,Y=64,X=64,L=2)
    row('M20-direction1',D=1,O=3,Z=4,Y=32,X=32,L=2)
    row('M20-times2',T=2,D=3,O=3,Z=4,Y=32,X=32,L=2)
    row('M20-native2d',D=3,O=3,Z=1,Y=32,X=32,L=2)
    return rows


def modes(c,t,d,m):
    """Complete sparse coefficient declaration, all omitted bins exactly zero."""
    amp = F(2)**c.get('power',0)
    sign = (-1)**d
    if c.get('cancel'):
        if m==0: return {0:pair(1)}
        b = -F(1,2) if c['cancel']=='exact' else -(1-F(1,2**20))/2
        return {0:pair(b)} # a=1, side contribution 2*b
    if m==0:
        return {0:pair(-amp/4),c['Y']//4:pair(amp/2),-c['Y']//4:pair(amp/2)}
    # E and O are Hermitian sparse spectra: B=E+iO. Time and direction differ.
    return {0:pair(sign*amp*m*(t+1)/8,-amp*m/16),
            c['Y']//4:pair(sign*amp/(8*m),-amp/(16*m)),
            -c['Y']//4:pair(sign*amp/(8*m),-amp/(16*m))}


def modulation(c,t,d,m):
    if not m: return pair(1)
    if c.get('zero_mod'): return pair(0)
    if c.get('cancel'): return pair(1)
    return pair(F((-1)**d*(m+t),2),F(1,4))


def noise(c,t,d,m): return F(1+d+t,1) # independent, positive and time-specific


def factor(c,t,d,m,y):
    # dxy=dz=1, unit H, R=1/2, w=1/2, no suppression/taper.
    kx=F(c.get('carrier',0),c['X'])
    ky=F(y,c['Y'])
    den=norm(modulation(c,t,d,m))/noise(c,t,d,m)
    for e in range(c['D']):
        for n in range(-(c['O']-1),c['O']):
            if (e,n)==(d,m): continue
            qx=(m-n)*kx
            if qx*qx+ky*ky < F(1,4):
                den += norm(modulation(c,t,e,abs(n)))/noise(c,t,e,abs(n))
    den+=F(1,4)
    return scale(conj(modulation(c,t,d,m)),1/(noise(c,t,d,m)*den))


def fixture(c,dtype):
    shape=(c['T'],c['D'],2*c['O']-1,c['Z'],c['Y'],c['X']//2+1)
    q=np.zeros(shape,dtype=dtype)
    for t in range(c['T']):
        for d in range(c['D']):
            for m in range(c['O']):
                for y,v in modes(c,t,d,m).items():
                    if m:
                        q[t,d,2*m-1,0,y%c['Y'],0]=float(v[0])
                        q[t,d,2*m,0,y%c['Y'],0]=float(v[1])
                    else: q[t,d,0,0,y%c['Y'],0]=ascomplex(v)
    return q


def root_interval(turn):
    k=(turn*8)%8
    assert k.denominator==1, 'oracle only frozen eighth roots'
    k=int(k)
    z=(F(0),F(0)); one=(F(1),F(1)); neg=(-F(1),-F(1))
    s=(SQLO/2,SQHI/2); ns=(-SQHI/2,-SQLO/2)
    return [(one,z),(s,s),(z,one),(ns,s),(neg,z),(ns,ns),(z,neg),(s,ns)][k]


def interval_product(a,b):
    v=[x*y for x in a for y in b]
    return (min(v),max(v))


def oracle(c,t,y,x):
    lo=F(0); hi=F(0); total=F(0)
    for d in range(c['D']):
        for m in range(c['O']):
            for fy,v in modes(c,t,d,m).items():
                v=mul(v,factor(c,t,d,m,fy))
                turn=F(fy*y,c['L']*c['Y']) + F(m*c.get('carrier',0)*(x-c['L']*c['X']//2),c['L']*c['X'])
                rr,ri=root_interval(turn)
                a=interval_product((v[0],v[0]),rr)
                b=interval_product((-v[1],-v[1]),ri)
                mult=2 if m else 1
                lo+=mult*(a[0]+b[0]); hi+=mult*(a[1]+b[1])
                total+=mult*(abs(v[0])+abs(v[1]))
    return lo,hi,total


def exact_metrics(image,c):
    lower=F(0); upper=F(0); width=F(0); scale0=F(0); sumabs=F(0)
    rms_terms=[]; worstcondition=F(0); infinite=False
    period_y=4*c['L']; period_x=c['L']*c['X'] if c.get('carrier') else 1
    for t in range(c['T']):
        for y in range(period_y):
            for x in range(period_x):
                lo,hi,total=oracle(c,t,y,x)
                width=max(width,hi-lo); scale0=max(scale0,abs(lo),abs(hi)); sumabs=max(sumabs,total)
                near=min(abs(lo),abs(hi)) if lo*hi>0 else 0
                if near: worstcondition=max(worstcondition,total/near)
                else: infinite=True
                block=image[t,:,y::period_y,x::period_x]
                for value in np.unique(block):
                    v=F.from_float(float(value))
                    lower=max(lower,lo-v,v-hi,0); upper=max(upper,abs(v-lo),abs(v-hi))
                rms_terms.append(float(np.mean((block.astype(np.float64)-float((lo+hi)/2))**2)))
    return dict(max_abs_distance_lower=float(lower),max_abs_error_upper=float(upper),
                reference_interval_width_max=float(width),rms_midpoint=math.sqrt(sum(rms_terms)/len(rms_terms)),
                signal_scale=float(scale0),max_error_over_signal_scale=float(upper/scale0) if scale0 else None,
                signed_min=float(image.min()),signed_max=float(image.max()),
                max_sum_abs_terms=float(sumabs),condition_upper=None if infinite else float(worstcondition),
                zero_or_interval_crossing_reference=infinite,
                condition_scaled_absolute_error=float(upper/sumabs) if sumabs else 0,
                input_quantization_error='exactly zero: all frozen band components are binary32 dyadics',
                scalar_reference='exact rational with checked sqrt2 interval; no double-as-truth')


def payload(*objects):
    seen=set(); total=0
    def walk(obj):
        nonlocal total
        if id(obj) in seen:return
        seen.add(id(obj))
        if isinstance(obj,np.ndarray):
            base=obj
            while isinstance(base.base,np.ndarray):base=base.base
            if id(base) not in seen or base is obj:
                seen.add(id(base));total+=base.nbytes
        elif dataclasses.is_dataclass(obj):
            for f in dataclasses.fields(obj):walk(getattr(obj,f.name))
        elif isinstance(obj,dict):
            for v in obj.values():walk(v)
        elif isinstance(obj,(list,tuple)):
            for v in obj:walk(v)
    for obj in objects:walk(obj)
    return total


def kernel(c,q,profile):
    cd=np.complex64 if profile=='mixed' else np.complex128
    outshape=(c['Z'],c['L']*c['Y'],c['L']*c['X'])
    acc=np.zeros((c['T'],*outshape),np.float64)
    filtered=np.zeros_like(q)
    stages=[]
    for t in range(c['T']):
        for d in range(c['D']):
            for m in range(c['O']):
                spec=np.zeros(outshape,cd)
                for y in modes(c,t,d,m):
                    val=q[t,d,2*m-1,0,y%c['Y'],0]+cd(1j)*q[t,d,2*m,0,y%c['Y'],0] if m else q[t,d,0,0,y%c['Y'],0]
                    scalar=ascomplex(factor(c,t,d,m,y)) # f64 scalar policy, explicitly bounded cast
                    coef=val*cd(scalar)
                    spec[0,y%outshape[1],0]=coef
                    if m:
                        n=conj(mul(modes(c,t,d,m)[-y],factor(c,t,d,m,-y)))
                        # Snapshot recombination follows rounded p,n, not rational expected output.
                        nv=cd(ascomplex(n))
                        filtered[t,d,2*m-1,0,y%c['Y'],0]=(coef+nv)*cd(.5)
                        filtered[t,d,2*m,0,y%c['Y'],0]=(coef-nv)*cd(-.5j)
                    else:filtered[t,d,0,0,y%c['Y'],0]=coef
                spatial=fft.ifftn(spec,norm='forward',workers=1)
                # One bounded x ramp is rounded before bulk product. No c128 spatial temporary.
                theta=2*np.pi*m*c.get('carrier',0)*(np.arange(outshape[2],dtype=np.float64)-outshape[2]//2)/(c['L']*c['X'])
                ramp=np.exp(1j*theta).astype(cd)
                product=spatial*ramp[None,None,:]
                acc[t]+=(2 if m else 1)*product.real
                if len(stages)<c['O']:
                    stages.append(dict(input=str(q.dtype),scalar='complex128->'+str(np.dtype(cd)),spectrum=str(spec.dtype),ifft=str(spatial.dtype),ramp=str(ramp.dtype),product=str(product.dtype),accumulator=str(acc.dtype)))
    result=acc.astype(np.float32) if profile=='mixed' else acc.copy()
    return dict(image=result,filtered_quadratures=filtered),dict(stages=stages,
        accumulator_final_coexist_bytes=acc.nbytes+result.nbytes,
        last_workspace_logical_bytes=spec.nbytes+spatial.nbytes+product.nbytes+ramp.nbytes,
        copies='owned input supplied; filtered owned; each spectrum zero-filled; ramp cast copied; final image copy; FFT internal copies unknown')


def public_bands(c,q):
    import simrecon as s
    # Valid public CE02 history from constant frames, then independently declared caller-writable used bands.
    raw=np.ones((c['T'],c['D'],2*c['O']-1,c['Z'],c['Y'],c['X']),np.float64)
    b=s.prepare_bands(raw,dxy_um=1.,dz_um=1.,norders=c['O'],background=0,lateral_zoom=c['L'],axial_zoom=1,edge_pixels=0,equalize=False)
    b.quadratures[:]=q
    for d in range(c['D']):
        for m in range(c['O']):b.noise_variance_factors[d,m]=float(noise(c,0,d,m))
    return b,raw


def public_known(c,q):
    import simrecon as s
    b,raw=public_bands(c,q)
    otf=s.declare_otf(np.ones((c['O'],8,8)),layout='radial',dkr_cyc_um=.25,dkz_cyc_um=1.)
    carriers=np.zeros((c['D'],2));carriers[:,0]=c.get('carrier',0)/c['X']
    mod=np.array([[ascomplex(modulation(c,0,d,m)) for m in range(1,c['O'])] for d in range(c['D'])])
    result=s.reconstruct_known(b,otf,carriers_cyc_um=carriers,modulation=mod,**OPTICS,wiener=.5,suppress_singularities=False,output_taper='none')
    return result,dict(public='reconstruct_known double compatibility/oracle control',caller_payload=payload(b,raw,otf,carriers,mod),retained_payload=payload(result),dtypes={f.name:str(getattr(result,f.name).dtype) for f in dataclasses.fields(result) if isinstance(getattr(result,f.name),np.ndarray)})


def small_probe(case):
    if case=='M01':
        rows=[]
        for n in [4,8]:
            x=np.array([(-1)**j*(j+1)/8 for j in range(n)],np.float32)
            # Forward DFT exact eighth-root enclosure, real and imag components.
            for api in ['numpy','scipy']:
                for kind in ['fft','rfft','ifft']:
                    xx=x.astype(np.complex64) if kind!='rfft' else x
                    f=getattr(np.fft if api=='numpy' else fft,kind)
                    out=f(xx,norm='backward')
                    lower=F(0);upper=F(0);width=F(0)
                    for k,val in enumerate(out):
                        rlo=rhi=ilo=ihi=F(0)
                        for j,v in enumerate(x):
                            rr,ri=root_interval(F((1 if kind=='ifft' else -1)*j*k,n))
                            p=interval_product((F.from_float(float(v)),)*2,rr)
                            q=interval_product((F.from_float(float(v)),)*2,ri)
                            div=n if kind=='ifft' else 1
                            rlo+=p[0]/div;rhi+=p[1]/div;ilo+=q[0]/div;ihi+=q[1]/div
                        for v,lo,hi in [(val.real,rlo,rhi),(val.imag,ilo,ihi)]:
                            exact=F.from_float(float(v));lower=max(lower,lo-exact,exact-hi,0);upper=max(upper,abs(exact-lo),abs(exact-hi));width=max(width,hi-lo)
                    rows.append(dict(n=n,api=api,operation=kind,axes='last axis',norm='backward',input=str(xx.dtype),output=str(out.dtype),input_hash=digest(xx),max_abs_distance_lower=float(lower),max_abs_error_upper=float(upper),reference_width=float(width)))
        phase=np.arange(4,dtype=np.float64)/7
        c=np.ones(4,np.complex64)
        rows.append(dict(promotion_probe=dict(c64_times_f64_phase=str((c*np.exp(1j*phase)).dtype),bounded_rounded_ramp=str((c*np.exp(1j*phase).astype(np.complex64)).dtype))))
        return rows
    if case=='M08-M09':
        cases=[('nonzero',[1,2j],[F(1,2)+1j,1-F(1,2)*1j]),('orthogonal',[1,1],[2,-2]),('equal',[1,0],[0,1]),('zero',[0,0],[1,0])]
        rows=[]
        for name,x,y in cases:
            x=np.array(x,np.complex64);y=np.array(y,np.complex64)
            ex=sum(F.from_float(float(v.real))**2+F.from_float(float(v.imag))**2 for v in x)
            ey=sum(F.from_float(float(v.real))**2+F.from_float(float(v.imag))**2 for v in y)
            ec=pair(0)
            for a,b in zip(x,y):ec=add(ec,mul(conj(pair(float(a.real),float(a.imag))),pair(float(b.real),float(b.imag))))
            xp=x.astype(np.complex128);yp=y.astype(np.complex128)
            sx=float(np.sum(xp.real*xp.real+xp.imag*xp.imag,dtype=np.float64));sy=float(np.sum(yp.real*yp.real+yp.imag*yp.imag,dtype=np.float64));cross=np.sum(np.conj(xp)*yp,dtype=np.complex128)
            valid=ex>0 and ey>0 and ex!=ey
            rows.append(dict(name=name,SX=sx,SY=sy,cross=[float(cross.real),float(cross.imag)],exact=[str(ex),str(ey),list(map(str,ec))],decision='valid' if valid else 'undefined-energy-reject',forward=[float((cross/sx).real),float((cross/sx).imag)] if valid else None,phase='undefined at zero amplitude' if cross==0 else float(np.angle(cross)),input_hashes=[digest(x),digest(y)]))
        with np.errstate(all='ignore'):
            a=np.array([2.**-100,2.**100],np.float32)
            rows.append(dict(product_risk=dict(input=a.tolist(),square_before_promoted_sum=(a*a).tolist(),promote_before_square=(a.astype(np.float64)**2).tolist(),f32_product_absolute_subnormal_round_bound=2.**-150)))
        return rows
    if case=='M07':
        rows=[]
        for separation in [2.**-4,2.**-12,2.**-20]:
            # Explicit 2-column phase design subproblem [[1,1],[1,cos(delta)]];
            # exact analytic solution x=[1,-1], b=[0,1-cos(delta)].
            # Transcendental construction is f64 source-only, NOT exact oracle.
            a=np.array([[1.,1.],[1.,math.cos(separation)]],np.float64);wanted=np.array([1.,-1.]);b=a@wanted
            for dtype in [np.float64,np.float32]:
                aa=a.astype(dtype).astype(np.float64);bb=b.astype(dtype).astype(np.float64)
                try:
                    sol=np.linalg.solve(aa,bb);res=np.linalg.norm(aa@sol-bb)/(np.linalg.norm(aa)*np.linalg.norm(sol)+np.linalg.norm(bb))
                    rows.append(dict(delta_rad=separation,source='f64 cos, represented design only',storage=str(np.dtype(dtype)),condition=float(np.linalg.cond(aa)),residual=float(res),forward_error_represented=float(np.max(abs(sol-wanted))),status='solved'))
                except np.linalg.LinAlgError as e:rows.append(dict(delta_rad=separation,storage=str(np.dtype(dtype)),status='singular represented matrix',error=str(e)))
        # Exact rational solve to separate oracle from previous conditioning illustration.
        for power in [4,12,20]:
            eps=F(1,2**power);a=np.array([[1,1],[1,float(1-eps)]],np.float64);b=np.array([0,float(eps)])
            x=np.linalg.solve(a,b)
            rows.append(dict(exact_rational_eps=str(eps),independent_solution=[1,-1],observed=x.tolist(),condition=float(np.linalg.cond(a)),residual=float(np.linalg.norm(a@x-b))))
        return rows
    if case=='M14-M18':
        rows=[]
        with np.errstate(all='ignore'):
            for v in [1+2**-30,1.,2.**-149,2.**-150,2.**128]:
                a=np.float32(v)
                rows.append(dict(source_hex=float(v).hex(),consumed=float(a),rounding_error=float(a)-v,source_schema='empirical c128 permits non-c64-exact; declared OTF does not',finite=bool(np.isfinite(a))))
        # scalar exact tie and representable near-tie decision margins, not a search witness.
        for delta in [F(0),F(1,2**20),-F(1,2**20),F(1,2**30)]:
            values=np.array([1,float(1+delta)],np.float32)
            rows.append(dict(maximum_exact_margin=str(delta),consumed_values=values.tolist(),first_row_major_index=int(np.argmax(values)),representation_changed_order=bool(delta>0 and values[1]==values[0]),oracle='exact rational comparison, no epsilon tie rule'))
        return rows
    raise ValueError(case)


def freeze():
    rows=[]
    for c in declarations():
        q64=fixture(c,np.complex128);q32=fixture(c,np.complex64)
        assert np.array_equal(q64,q32.astype(np.complex128))
        vox=c['T']*c['Z']*(c['L']*c['Y'])*(c['L']*c['X'])
        native=c['Z']*(c['L']*c['Y'])*(c['L']*c['X'])
        rows.append(dict(**c,input_c128_sha256=digest(q64),input_c64_sha256=digest(q32),shape=list(q32.shape),oracle_samples=[dict(t=t,lo=str(oracle(c,t,0,0)[0]),hi=str(oracle(c,t,0,0)[1])) for t in range(c['T'])],
                         planned_payload=dict(caller_c64=q32.nbytes,filtered_c64=q32.nbytes,accumulator_f64=8*vox,final_f32=4*vox,three_complex64_workspaces=3*8*native,ramp_c64=8*c['L']*c['X']),
                         profiles=['mixed','prototype-double']+(['public-double'] if c['name'].startswith(('M02','M03','M06')) else [])))
    result=dict(revision='sp112-finite-v1',identities=identities(),kernel_rows=rows,small_rows=['M01','M07','M08-M09','M14-M18'],repetitions=3,formula='CE04 sparse z0,x0 with coefficients modes(); all omitted bins zero; unit H; w=1/2; dxy=dz=1; R=1/2; no taper/suppression; noise=1+d+t; alpha metadata=1/(X*Y*Z*L^2*D), already consumed in supplied band units',sqrt2_enclosure=[str(SQLO),str(SQHI)],not_cartesian=True,random_seed=None,search_ce06='separate source/rounded-input probes, not c64 runtime')
    (HERE/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return dict(status='frozen',manifest_sha256=sha(HERE/'manifest.json'),kernel_rows=len(rows),kernel_fresh_runs=3*sum(len(r['profiles']) for r in rows),small_fresh_runs=12)


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('--case');p.add_argument('--profile',default='mixed');p.add_argument('--repeat',type=int,default=1);a=p.parse_args()
    if a.mode=='freeze':return freeze()
    manifest=json.loads((HERE/'manifest.json').read_text());assert manifest['identities']==identities(),'material script/source drift after freeze'
    base=dict(case=a.case,profile=a.profile,repeat=a.repeat,argv=sys.argv,environment=environment(),manifest_sha256=sha(HERE/'manifest.json'),identities=identities(),generator_revision='sp112-finite-v1')
    try:
        if a.case in manifest['small_rows']:
            before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;start=time.monotonic();answer=small_probe(a.case);elapsed=time.monotonic()-start
            base.update(result=answer,seconds=elapsed,precall_ru_maxrss_KiB=before)
        else:
            c=next(c for c in manifest['kernel_rows'] if c['name']==a.case)
            assert a.profile in c['profiles']
            q=fixture(c,np.complex64 if a.profile=='mixed' else np.complex128)
            assert digest(q)==c['input_c64_sha256' if a.profile=='mixed' else 'input_c128_sha256']
            before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            start=time.monotonic()
            result,detail=public_known(c,q) if a.profile=='public-double' else kernel(c,q,a.profile)
            elapsed=time.monotonic()-start
            # Freeze call peak before allocating oracle/observer temporaries, retain whole-process peak too.
            callpeak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            image=result.image if dataclasses.is_dataclass(result) else result['image']
            metrics=exact_metrics(image,c)
            base.update(seconds=elapsed,precall_ru_maxrss_KiB=before,call_end_ru_maxrss_KiB=callpeak,
                        input_dtype=str(q.dtype),input_sha256=digest(q),input_payload=q.nbytes,result_payload=payload(result),caller_plus_result_payload=payload(q,result),result_image_dtype=str(image.dtype),result_image_hash=digest(image),metrics=metrics,detail=detail)
        base.update(status='completed',whole_process_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except Exception as e:
        base.update(status='failed',exception_type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),whole_process_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    base['whole_process_peak_bytes']=base['whole_process_ru_maxrss_KiB']*1024
    return base

if __name__=='__main__':
    print(json.dumps(main(),indent=2,allow_nan=True))
