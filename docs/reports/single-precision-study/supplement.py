"""SP112 separately frozen scalar, public-interface and CE06 characterization.
No product helpers provide expected scalar filtering, camera sums or cubic fit.
Search trace captures are diagnostics, never independent f32 search oracles.
"""
from fractions import Fraction as F
import argparse
import dataclasses
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
from scipy import fft
import simrecon as s

sys.path.insert(0,str(Path(__file__).resolve().parent))
import study as ref
from preflight import environment
HERE=Path(__file__).resolve().parent
CASES=['scalar-filter','fft-interfaces','phase-designs','search-seed0','search-seed3','search-tie','transfer','camera-off','cubic','native2d-layouts','workflow-full','workflow-summary']


def clean(obj):
    if isinstance(obj,np.ndarray):return clean(obj.tolist())
    if isinstance(obj,np.generic):return clean(obj.item())
    if isinstance(obj,complex):return [obj.real,obj.imag]
    if isinstance(obj,dict):return {str(k):clean(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)):return [clean(v) for v in obj]
    return obj


def opts(**kw):
    return dict(acquisition_mode='3d',dxy_um=1.,dz_um=1.,norders=2,background=0.,lateral_zoom=1,axial_zoom=1,edge_pixels=0,equalize=False)|kw


def search_input(seed=0,tie=False):
    shape=(1,1,5,2,1,4) if tie else (1,1,5,3,3,4)
    raw=np.ones(shape,np.float64)
    b=s.prepare_bands(raw,dxy_um=1.,dz_um=1.,norders=3,background=0,lateral_zoom=1,axial_zoom=1,edge_pixels=0,equalize=False)
    if tie:
        b.quadratures.fill(0);b.quadratures[0,0,0,0,0,:]=1;b.quadratures[0,0,1,0,0,0]=.25;b.quadratures[0,0,3,0,0,1]=-.5j
        tab=np.ones((3,2,1));initial=np.array([[.11,0.]])
        transfer=s.declare_otf(tab,layout='radial',dkr_cyc_um=1.,dkz_cyc_um=1.)
    else:
        rng=np.random.default_rng(seed)
        b.quadratures[:]=(rng.integers(-8,9,b.quadratures.shape)+1j*rng.integers(-8,9,b.quadratures.shape))/16
        b.quadratures[:,:,0]*=3
        tab=np.empty((3,12,8),np.complex128)
        for idx in np.ndindex(tab.shape):
            m,r,z=idx;tab[idx]=(8+m+r+z)/16+1j*(1+2*m+r+2*z)/32
        initial=np.array([[.06,-.035]])
        transfer=s.declare_otf(tab,layout='radial',dkr_cyc_um=.25,dkz_cyc_um=1.)
    return b,transfer,initial


def inputs_manifest():
    rows=[]
    for seed,tie in [(0,False),(3,False),(0,True)]:
        b,tr,k=search_input(seed,tie)
        rows.append(dict(seed=seed,tie=tie,shape=b.input_shape,bands_hash=ref.digest(b.quadratures),rounded_bands_hash=ref.digest(b.quadratures.astype(np.complex64)),transfer_hash=ref.digest(tr.samples),initial=clean(k),expected='complete public double search; no predetermined numeric success/tolerance; inspect frozen overlap and stale bracket state; c64 capture rounding probe only'))
    sources=['src/simrecon/acquisition/modes.py','src/simrecon/acquisition/layout.py','src/simrecon/acquisition/drift.py','src/simrecon/workflow/reconstruct.py','src/simrecon/workflow/config.py','src/simrecon/workflow/summary.py']
    return dict(revision='sp112-supplement-v1',identities=ref.identities(),additional_source_hashes={p:ref.sha(ref.ROOT/p) for p in sources},script_sha256=ref.sha(__file__),cases=CASES,repetitions=3,search=rows,
                scalar='independently evaluated binary64 CE04 denominators against exact rational factor reference; c64 rounded +/- coefficients then recombination',
                camera=dict(shape=[2,1,3,2,2,4],raw='8+t+p+z constant each plane; first on corner sentinel -1',background='1 except corner 5',slope='1 except corner -2',alpha='1/16',expected_frame_sum='(7+t+p+z)/2',equalize_anchor='t0,d0,p0,z0',off='one raw+2 exposure; no sentinel on off; N1 gain one'),
                cubic=dict(shape=[1,4,3,2,10,64],displacements=[0,1,8,27],impulse='64 at (5,5+d^3)',off='one identical exposure',timestamps='prefix 10+d+(p-3)/10 for d0..3,p0..5 then 24 values arange+100; actual sample prefix no off stride',expected_coefficients=[[0,0],[0,0],[1,0]]),
                workflow=dict(raw_shape=[1,1,3,2,4,4],raw_phase_values=[4,6,2],transfer='unit radial 2x8x8',carrier='linespacing10 angle0 searchFalse',expected='exact same-environment full-summary image/parameter identity, no physical oracle'),
                pi='No certified transcendental search oracle provided; captures diagnostic-only')


def scalar_filter():
    rows=[]
    for c in ref.declarations():
        if c['name'].startswith(('M19','M20')):continue
        for t in range(c['T']):
            for d in range(c['D']):
                for m in range(c['O']):
                    for y,v in ref.modes(c,t,d,m).items():
                        # Candidate code independently evaluates binary64 products, weights and ordered sum.
                        a=complex(ref.ascomplex(ref.modulation(c,t,d,m)))
                        weight=1./(1+d+t)
                        den=(a.real*a.real+a.imag*a.imag)*weight
                        k=c.get('carrier',0)/c['X'];ky=y/c['Y']
                        included=1
                        for e in range(c['D']):
                            for n in range(-(c['O']-1),c['O']):
                                if (e,n)==(d,m):continue
                                qx=(m-n)*k
                                if qx*qx+ky*ky<.25:
                                    aa=complex(ref.ascomplex(ref.modulation(c,t,e,abs(n))))
                                    den+=(aa.real*aa.real+aa.imag*aa.imag)/(1+e+t);included+=1
                        den+=.5*.5
                        z=weight*a.conjugate()/den
                        oracle=ref.factor(c,t,d,m,y)
                        err=max(abs(F.from_float(z.real)-oracle[0]),abs(F.from_float(z.imag)-oracle[1]))
                        # Full +/- independently evaluated candidate products, then prescribed recombination.
                        p=np.complex64(ref.ascomplex(v))*np.complex64(z)
                        # opposite y has same scale here (carrier is x only), input coefficients equal.
                        n=np.conj(np.complex64(ref.ascomplex(ref.modes(c,t,d,m)[-y]))*np.complex64(z)) if m else p
                        even=(p+n)*np.complex64(.5);odd=(p-n)*np.complex64(-.5j)
                        exactp=ref.mul(v,oracle)
                        exactn=ref.conj(ref.mul(ref.modes(c,t,d,m)[-y],oracle)) if m else exactp
                        exacte=ref.scale(ref.add(exactp,exactn),F(1,2))
                        exacto=ref.mul(ref.add(exactp,ref.scale(exactn,-1)),ref.pair(0,-F(1,2)))
                        recomb_error=max(abs(F.from_float(float(got.real))-wanted[0]) for got,wanted in [(even,exacte),(odd,exacto)])
                        # Bound only scalar finite-normal arithmetic, not FFT. Conservative op-count for
                        # each positive power/weight/add/div and complex numerator components.
                        u=F(1,2**53);gamma=F(32*included)*u/(1-F(32*included)*u)
                        scalar_bound=float(gamma*(abs(oracle[0])+abs(oracle[1])+1))
                        rows.append(dict(case=c['name'],t=t,d=d,m=m,y=y,included=included,denominator_f64=den,scale=clean(z),exact_scale=list(map(str,oracle)),scale_component_error=float(err),finite_normal_scalar_envelope=scalar_bound,envelope_assumptions='32 operations per eligible positive term; normal arithmetic, no FFT; conservative first-order sum/div bound with gamma<1/2',within_scalar_envelope=float(err)<=scalar_bound,recombination_real_component_error=float(recomb_error),recombined_dtypes=[str(even.dtype),str(odd.dtype)]))
    return rows


def fft_interfaces():
    x=(np.arange(32).reshape(2,4,4)%7-3).astype(np.float32)
    rows=[]
    for api,lib in [('numpy',np.fft),('scipy',fft)]:
        r=lib.rfft2(x,axes=(-2,-1),norm='backward');z=lib.fft(r,axis=-3,norm='backward')
        rows.extend([dict(api=api,operation='rfft2',shape=x.shape,axes=[-2,-1],norm='backward',input=str(x.dtype),output=str(r.dtype)),dict(api=api,operation='fft',shape=r.shape,axis=-3,norm='backward',input=str(r.dtype),output=str(z.dtype))])
        for name,arg,kw in [('ifftn',z,dict(axes=(-3,-2,-1),norm='forward')),('fft2',z[0],dict(axes=(-2,-1),norm='backward')),('irfft',r[0,0],dict(n=4,norm='backward')),('irfftn',r,dict(s=x.shape,axes=(-3,-2,-1),norm='backward'))]:
            out=getattr(lib,name)(arg,**kw);rows.append(dict(api=api,operation=name,input=str(arg.dtype),output=str(out.dtype),parameters=kw,input_hash=ref.digest(arg),output_shape=out.shape))
    return dict(rows=rows,internal_accumulation_workspace='unknown; interface dtype only')


def phase_designs():
    rows=[]
    designs=[('uniform',[2*math.pi*j/5 for j in range(5)]),('nonuniform',[0.,.7,2.1,3.5,5.2])]
    designs += [('near-'+str(p),[j*2.**-p for j in range(5)]) for p in [4,12,20]]
    wanted=np.array([1.,-1.,.5,.25,-.125])
    for name,angles in designs:
        matrix=np.array([[1.,math.cos(a),math.sin(a),math.cos(2*a),math.sin(2*a)] for a in angles])
        # Exact rational b for the *represented* matrix and dyadic known solution.
        exactb=[sum(F.from_float(float(v))*F.from_float(float(w)) for v,w in zip(row,wanted)) for row in matrix]
        b=np.array([float(v) for v in exactb])
        rounding=max(abs(F.from_float(float(v))-r) for v,r in zip(b,exactb))
        for dtype in [np.float64,np.float32]:
            aa=matrix.astype(dtype).astype(np.float64);bb=b.astype(dtype).astype(np.float64)
            try:
                x=np.linalg.solve(aa,bb)
                residual=float(np.linalg.norm(aa@x-bb)/(np.linalg.norm(aa)*np.linalg.norm(x)+np.linalg.norm(bb)))
                rows.append(dict(name=name,angles_rad=angles,storage=str(np.dtype(dtype)),matrix_sha256=ref.digest(aa),b_sha256=ref.digest(bb),condition_estimate=float(np.linalg.cond(aa)),normalized_residual=residual,forward_error_from_known_solution=float(np.max(abs(x-wanted))),source_b_quantization_error=float(rounding),source='true phase->f64 trig error not enclosed; exact rational represented-matrix oracle separates b rounding',status='solved'))
            except np.linalg.LinAlgError as e:rows.append(dict(name=name,storage=str(np.dtype(dtype)),status='singular represented design',message=str(e)))
    return rows


def search(case):
    seed=3 if case.endswith('3') else 0;tie=case=='search-tie'
    b,tr,k=search_input(seed,tie)
    result=s.estimate_parameters(b,tr,initial_carriers_cyc_um=k,**ref.OPTICS)
    events=[dict(kind=e.kind,**dict(e.details)) for e in result.trace]
    brackets=[e for e in events if e['kind']=='bracket']
    coarse=next(e for e in events if e['kind']=='coarse')
    angle_stop=next(e for e in brackets if e['stage']=='angle' and e['branch']=='stop')
    mag_start=next(e for e in brackets if e['stage']=='magnitude' and e['branch']=='initial')
    sensitivity=[]
    for e in events:
        if e['kind']!='evaluation':continue
        o=result.overlaps[e['overlap_index']]
        spatial=o.spatial.astype(np.complex64)
        x=spatial[0];y=spatial[1]
        nz,ny,nx=x.shape;yy,xx=np.indices((ny,nx));kv=e['carrier_cyc_um']
        theta=2*np.pi*o.orders[1]*((xx-nx//2)*kv[0]+(yy-ny//2)*kv[1])
        ramp=np.exp(1j*theta).astype(np.complex64)
        product=y*ramp[None,:,:]
        xp=x.astype(np.complex128);yp=product.astype(np.complex128)
        sx=np.sum(xp.real*xp.real+xp.imag*xp.imag,dtype=np.float64);cross=np.sum(np.conj(xp)*yp,dtype=np.complex128)
        fwd=cross/sx
        sensitivity.append(dict(stage=e['stage'],overlap=e['overlap_index'],candidate_forward=clean(fwd),baseline_forward=clean(e['forward']),component_change=float(max(abs((fwd-e['forward']).real),abs((fwd-e['forward']).imag))),candidate_amplitude=float(abs(fwd)),baseline_amplitude=float(abs(e['forward'])),phase_change_rad=float(np.angle(fwd/e['forward'])) if fwd and e['forward'] else None,objective=float(abs(fwd)**2),baseline_objective=e['objective'],input='rounded PUBLIC double overlap captures; no independent overlap oracle/no full single search'))
    powers=np.sort(coarse['correlation_power'].ravel());margin=float(powers[-1]-powers[-2])
    return dict(input_hash=ref.digest(b.quadratures),input_rounding_component_error=float(np.max(abs(b.quadratures-b.quadratures.astype(np.complex64).astype(np.complex128)))),carrier_cyc_um=clean(result.carriers_cyc_um),modulation=clean(result.modulation),branches=result.branches,coarse=clean(coarse),coarse_baseline_top_margin=margin,margin_status='observed binary64 diagnostic, uncertified at single precision',brackets=clean(brackets),frozen_overlap_indices=[e['overlap_index'] for e in events if e['kind']=='evaluation' and e['stage'] in ['angle','magnitude','final']],stale_bracket_preserved=angle_stop['x1']==mag_start['x1'] and angle_stop['amp1']==mag_start['amp1'],sensitivity=sensitivity,limitations='actual public double search; rounded-capture probe is not end-to-end c64 search; no certified transcendental/margin enclosure')


def transfer_probe():
    rows=[]
    # Radial complex affine table: H(r,z)=(1+r/4+z/8)+i*(r/8-z/16).
    tab=np.empty((2,4,4),np.complex128)
    for m,r,z in np.ndindex(tab.shape):tab[m,r,z]=1+r/4+z/8+1j*(r/8-z/16)
    tr=s.declare_otf(tab,layout='radial',dkr_cyc_um=1.,dkz_cyc_um=1.)
    for r,z in [(F(1,2),0),(F(1),1),(F(3),0)]:
        try:
            out=s.sample_otf(tr,float(r),0,z,dkz_cyc_um=1.)
            want=complex(float(1+r/4+F(z,8)),float(r/8-F(z,16)))
            rows.append(dict(layout='radial',query=[str(r),z],observed=clean(out),exact=clean(want),component_error=float(abs(out-want)),decision='valid'))
        except Exception as e:rows.append(dict(layout='radial',query=[str(r),z],decision='unsafe stencil reject including zero-weight next vertex',exception=type(e).__name__,message=str(e)))
    tab=np.empty((2,4,4,4),np.complex128)
    for m,z,y,x in np.ndindex(tab.shape):tab[m,z,y,x]=1+x/4+y/8+z/16+1j*(x/8-y/16+z/32)
    tr=s.declare_otf(tab,layout='full',dkr_cyc_um=1.,dkz_cyc_um=1.)
    for x,y,z in [(F(1,2),F(1,2),0),(F(1),F(1),1),(F(3),F(0),0)]:
        try:
            out=s.sample_otf(tr,float(x),float(y),z,dkz_cyc_um=1.)
            want=complex(float(1+x/4+y/8+F(z,16)),float(x/8-y/16+F(z,32)))
            rows.append(dict(layout='full',query=[str(x),str(y),z],observed=clean(out),exact=clean(want),component_error=float(abs(out-want)),decision='valid'))
        except Exception as e:rows.append(dict(layout='full',query=[str(x),str(y),z],decision='unsafe actual stencil',exception=type(e).__name__,message=str(e)))
    return rows


def camera():
    raw=np.empty((2,1,3,2,2,4),np.float64)
    for t,d,p,z in np.ndindex(raw.shape[:4]):raw[t,d,p,z]=8+t+p+z
    raw[0,0,0,0,-1,-1]=-1
    bg=np.ones((2,4));bg[-1,-1]=5;slope=np.ones((2,4));slope[-1,-1]=-2
    # First off is ordinary; on sentinel then persists into all later planes.
    off=np.empty((*raw.shape[:4],1,2,4))
    for t,d,p,z in np.ndindex(raw.shape[:4]):off[t,d,p,z,0]=10+t+p+z
    b=s.prepare_acquisition_bands(raw,**opts(background=bg,flatfield_slope=slope,off_exposures=off,equalize=True,equalize_time=True,equalize_z=True,combine_off_orders=np.array([False,True])))
    exact=np.empty(raw.shape[:4]);gain=np.empty_like(exact)
    for t,d,p,z in np.ndindex(exact.shape):exact[t,d,p,z]=(7+t+p+z)/2;gain[t,d,p,z]=7/(7+t+p+z)
    return dict(input_hash=ref.digest(raw),sentinels=b.sentinel_frames,frame_sums=clean(b.frame_sums),exact_frame_sums=clean(exact),frame_sum_max_error=float(np.max(abs(b.frame_sums-exact))),equalization_gain_max_error=float(np.max(abs(b.equalization_gains-gain))),off_gain_unique=np.unique(b.off_equalization_gains).tolist(),N1_off_gain_expected=1,background_corner=float(b.background_after[-1,-1]),slope_corner=float(b.slope_after[-1,-1]),noise_dtype=str(b.noise_variance_factors.dtype),quadrature_dtype=str(b.quadratures.dtype),off_combination_events=clean([dict(e.details) for e in b.trace if e.kind=='off-combination']),qualification='double CE06 control with exact pre-FFT camera sums/gains; no c64 workflow')


def cubic():
    raw=np.zeros((1,4,3,2,10,64),np.float64)
    for d,p,z in np.ndindex(4,3,2):raw[0,d,p,z,5,5+d**3]=64
    off=raw[...,None,:,:].copy()
    prefix=np.array([10+d+(p-3)/10 for d in range(4) for p in range(6)])
    clock=np.r_[prefix,np.arange(24,dtype=float)+100]
    b=s.prepare_acquisition_bands(raw,**opts(off_exposures=off,drift_within=True,adjust_phases=True,header_timestamps=clock,linespacing_um=100.,phase_start_angle_rad=.37,negative_angle_step=True,**ref.OPTICS))
    fits=[dict(e.details) for e in b.trace if e.kind=='cubic-fit']
    return dict(input_hash=ref.digest(raw),fits=clean(fits),exact_coefficients=[[0,0],[0,0],[1,0]],coefficient_max_errors=[float(np.max(abs(np.array(e['coefficients'])-np.array([[0,0],[0,0],[1,0]])))) for e in fits],qualification='public double cubic/control; single camera/FFT/drift state unqualified')


def native2d():
    raw=(np.arange(1*2*3*2*8*8).reshape(1,2,3,2,8,8)%17+1).astype(np.float32)
    rows=[]
    for storage in ['direction-major','z-major']:
        r=s.reinterpret_2d_planes(raw,storage_order=storage)
        b=s.prepare_acquisition_bands(r.images,**opts(acquisition_mode='2d',dz_um=0.))
        rows.append(dict(storage_order=storage,source_mapping=clean(r.source_direction_z),output_shape=r.images.shape,input_hash=ref.digest(raw),rearranged_hash=ref.digest(r.images),bands_shape=b.quadratures.shape,band_dtype=str(b.quadratures.dtype),noise_shape=b.noise_variance_factors.shape,qualification='actual CE06 double layout/preparation; #113 excludes 2D'))
    return rows


def workflow(mode):
    raw=np.empty((1,1,3,2,4,4),np.float64)
    for p,v in enumerate([4,6,2]):raw[:,:,p]=v
    otf=s.declare_otf(np.ones((2,8,8)),layout='radial',dkr_cyc_um=.25,dkz_cyc_um=1.)
    acq=opts();acq['phase_policy']='uniform'
    kwargs=dict(acquisition=acq,optics=ref.OPTICS,carrier=dict(linespacing_um=10.,phase_start_angle_rad=0.,search_carriers=False),filtering=dict(wiener=.5,suppress_singularities=False,output_taper='none'),specimen_identity=dict(id='SP112-explicit-phase-observations',intensity_unit='detector-counts'),transfer=otf,transfer_identity=dict(id='SP112-unit-H',intensity_unit='transfer'))
    result=(s.reconstruct_workflow if mode=='workflow-full' else s.reconstruct_summary)(raw,**kwargs)
    return dict(image_sha256=ref.digest(result.image),image_dtype=str(result.image.dtype),signed_extrema=[float(result.image.min()),float(result.image.max())],carriers_sha256=ref.digest(result.carriers_cyc_um),modulation_sha256=ref.digest(result.modulation),retained_array_payload=ref.payload(result),input_payload=ref.payload(raw,otf),qualification='unchanged double exact full/summary compatibility only; no independent image oracle/no single runtime')


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('--case');p.add_argument('--repeat',type=int,default=1);a=p.parse_args()
    if a.mode=='freeze':
        manifest=inputs_manifest();(HERE/'supplement-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return dict(status='frozen',sha256=ref.sha(HERE/'supplement-manifest.json'),cases=len(CASES),fresh_runs=3*len(CASES))
    frozen=json.loads((HERE/'supplement-manifest.json').read_text())
    assert frozen['script_sha256']==ref.sha(__file__) and frozen['identities']==ref.identities()
    start=time.monotonic();base=dict(case=a.case,repeat=a.repeat,argv=sys.argv,environment=environment(),script_sha256=ref.sha(__file__),manifest_sha256=ref.sha(HERE/'supplement-manifest.json'))
    base['precall_ru_maxrss_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start=time.monotonic()
    try:
        if a.case=='scalar-filter':answer=scalar_filter()
        elif a.case=='fft-interfaces':answer=fft_interfaces()
        elif a.case=='phase-designs':answer=phase_designs()
        elif a.case.startswith('search'):answer=search(a.case)
        elif a.case=='transfer':answer=transfer_probe()
        elif a.case=='camera-off':answer=camera()
        elif a.case=='cubic':answer=cubic()
        elif a.case=='native2d-layouts':answer=native2d()
        elif a.case.startswith('workflow-'):answer=workflow(a.case)
        else:raise ValueError(a.case)
        base.update(status='completed',result=answer)
    except Exception as e:base.update(status='failed',exception=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    base.update(seconds=time.monotonic()-start,whole_process_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    base['whole_process_peak_bytes']=base['whole_process_ru_maxrss_KiB']*1024
    return clean(base)

if __name__=='__main__':print(json.dumps(main(),indent=2,allow_nan=True))
