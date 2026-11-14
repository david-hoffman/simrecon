"""SP112 diagnosed observer corrections. Immutable originals remain unchanged.
Execute only after coordinator grants Ubuntu numerical window.
"""
import argparse
import json
import math
from pathlib import Path
import resource
import sys
import time
import traceback

import numpy as np
import simrecon as s

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import supplement as prior
import study as ref
from preflight import environment
CASES=['scalar-recombination','camera','off-combination','cubic','ties-reciprocal','workflow-full','workflow-summary']


def declarations():
    raw=np.empty((2,1,3,2,2,4),np.float64)
    for t,d,p,z in np.ndindex(raw.shape[:4]):raw[t,d,p,z]=8+t+p+z
    raw[0,0,0,0,-1,-1]=-1
    off=np.empty((*raw.shape[:4],1,2,4))
    for t,d,p,z in np.ndindex(raw.shape[:4]):off[t,d,p,z,0]=10+t+p+z
    bg=np.ones((2,4));bg[-1,-1]=5;slope=np.ones((2,4));slope[-1,-1]=-2
    combo=(11+(3*np.indices((2,2,3,2,4,6))[0]+5*np.indices((2,2,3,2,4,6))[1]+7*np.indices((2,2,3,2,4,6))[2]+np.indices((2,2,3,2,4,6))[3]+2*np.indices((2,2,3,2,4,6))[4]+np.indices((2,2,3,2,4,6))[5]**2)%17).astype(np.float64)
    cubic=np.zeros((1,4,3,2,10,64),np.float64)
    for d,p,z in np.ndindex(4,3,2):cubic[0,d,p,z,5,5+d**3]=64
    clock=np.r_[np.array([10+d+(p-3)/10 for d in range(4) for p in range(6)]),np.arange(24,dtype=float)+100]
    phases=np.arange(48,dtype=float)/3
    return dict(camera_raw=raw,camera_off=off,camera_background=bg,camera_slope=slope,combo_raw=combo,combo_off=(combo+3)[...,None,:,:].copy(),cubic_raw=cubic,cubic_off=cubic[...,None,:,:].copy(),cubic_clock=clock,cubic_phases=phases)


def ties_input(profile):
    shape=(1,1,5,2,1,4) if profile=='height-one' else (1,1,5,2,4,2)
    raw=np.ones(shape,np.float64)
    b=s.prepare_bands(raw,dxy_um=1.,dz_um=1.,norders=3,background=0,lateral_zoom=1,axial_zoom=1,edge_pixels=0,equalize=False)
    b.quadratures.fill(0)
    if profile=='height-one':
        b.quadratures[0,0,0,0,0,:]=[2,0,1];b.quadratures[0,0,1,0,0,0]=5/32
        b.quadratures[0,0,3,0,0,1]=.5;b.quadratures[0,0,4,0,0,1]=.5j
        initial=np.array([[-.05,0.]])
    else:
        b.quadratures[0,0,0,0,0,:]=[1,-1];b.quadratures[0,0,1,0,0,0]=.25;b.quadratures[0,0,3,0,1,0]=1
        initial=np.zeros((1,2))
    b.quadratures[:,:,0]*=math.ldexp(1.,330);b.quadratures[:,:,1:]*=math.ldexp(1.,-330)
    transfer=s.declare_otf(np.ones((3,2,1)),layout='radial',dkr_cyc_um=1.,dkz_cyc_um=1.)
    return b,transfer,initial


def manifest():
    data=declarations()
    ties=[]
    for profile in ['height-one','coarse-tie']:
        b,tr,k=ties_input(profile)
        ties.append(dict(profile=profile,band_hash=ref.digest(b.quadratures),shape=b.input_shape,initial=prior.clean(k),expected_coarse_power=[[0,64,0,0]] if profile=='height-one' else [[0,0],[0,0],[0,0],[64,64]],expected_first_peak=[1,0] if profile=='height-one' else [0,3],expected_final_carrier=[0,0],expected_all_objectives=0,expected_first_order_modulation='2^-660/16' if profile=='height-one' else '2^-660/8',single_input_conversion='large coefficients overflow, tiny coefficients underflow; unqualified'))
    return dict(revision='sp112-corrections-v1',script_sha256=ref.sha(__file__),prior_script_sha256=ref.sha(HERE/'supplement.py'),prior_manifest_sha256=ref.sha(HERE/'supplement-manifest.json'),identities=ref.identities(),cases=CASES,repetitions=3,input_hashes={k:dict(shape=v.shape,dtype=str(v.dtype),sha256=ref.digest(v)) for k,v in data.items()},ties=ties,
                corrections=dict(camera='int selectors zero; sentinel camera separated from combination to avoid uniform zero-noise witness',off_combination='integer selectors [1,1], nonuniform spatial observations, explicit optics',cubic='complete header phases alongside clock',workflow='transfer_identity optics equal optics; intensity_unit dimensionless-transfer',ties='separate valid reciprocal-scaled declared fixture; prior tie input stays actual zero-coarse rejection'))


def camera(data):
    b=s.prepare_acquisition_bands(data['camera_raw'],**prior.opts(background=data['camera_background'],flatfield_slope=data['camera_slope'],off_exposures=data['camera_off'],equalize=True,equalize_time=True,equalize_z=True,combine_off_orders=np.array([0,0],dtype=np.int64)))
    exact=np.empty((2,1,3,2));g=np.empty_like(exact)
    for t,d,p,z in np.ndindex(exact.shape):exact[t,d,p,z]=(7+t+p+z)/2;g[t,d,p,z]=7/(7+t+p+z)
    return dict(sentinels=b.sentinel_frames,frame_sums=prior.clean(b.frame_sums),exact_frame_sums=prior.clean(exact),max_frame_sum_error=float(np.max(abs(b.frame_sums-exact))),max_gain_error=float(np.max(abs(b.equalization_gains-g))),N1_off_gain_unique=np.unique(b.off_equalization_gains).tolist(),background_corner=float(b.background_after[-1,-1]),slope_corner=float(b.slope_after[-1,-1]),noise_shape=b.noise_variance_factors.shape,qualification='double public camera and equalization with exact rational pre-FFT oracle, no c64 CE06')


def recombination():
    from fractions import Fraction as F
    rows=prior.scalar_filter()
    configs={c['name']:c for c in ref.declarations()}
    for r in rows:
        c=configs[r['case']];t,d,m,y=(r[k] for k in ['t','d','m','y'])
        z=complex(*r['scale']);v=ref.modes(c,t,d,m)[y]
        p=np.complex64(ref.ascomplex(v))*np.complex64(z)
        n=np.conj(np.complex64(ref.ascomplex(ref.modes(c,t,d,m)[-y]))*np.complex64(z)) if m else p
        e=(p+n)*np.complex64(.5);o=(p-n)*np.complex64(-.5j)
        exactp=ref.mul(v,ref.factor(c,t,d,m,y))
        exactn=ref.conj(ref.mul(ref.modes(c,t,d,m)[-y],ref.factor(c,t,d,m,-y))) if m else exactp
        ee=ref.scale(ref.add(exactp,exactn),F(1,2));eo=ref.mul(ref.add(exactp,ref.scale(exactn,-1)),ref.pair(0,-F(1,2)))
        error=max(abs(F.from_float(float(g))-v) for got,wanted in [(e,ee),(o,eo)] for g,v in zip([got.real,got.imag],wanted))
        terms=sum(abs(v) for v in exactp)+sum(abs(v) for v in exactn)
        r.update(recombination_all_component_error=float(error),exact_e=list(map(str,ee)),exact_o=list(map(str,eo)),candidate_e=prior.clean(e),candidate_o=prior.clean(o),sum_abs_exact_pn_components=float(terms),normal_arithmetic='explicit scalar64 calculation in supplement.scalar_filter, c64 p and opposite p each formed from actual input and rounded scalar; rational expected p/n only in observer')
    return rows


def combination(data):
    kw=prior.opts(off_exposures=data['combo_off'],combine_off_orders=np.array([1,1],np.int64),wavelength_nm=520,numerical_aperture=.25,immersion_index=1.)
    b=s.prepare_acquisition_bands(data['combo_raw'],**kw)
    events=[dict(e.details) for e in b.trace if e.kind=='off-combination']
    return dict(events=prior.clean(events),noise=prior.clean(b.noise_variance_factors),bands_hash=ref.digest(b.quadratures),qualification='finite double on/off diagnostic only; no independent combined image oracle/no c64 workflow')


def cubic(data):
    b=s.prepare_acquisition_bands(data['cubic_raw'],**prior.opts(off_exposures=data['cubic_off'],drift_within=True,adjust_phases=True,header_timestamps=data['cubic_clock'],header_phases_rad=data['cubic_phases'],linespacing_um=100.,phase_start_angle_rad=.37,negative_angle_step=True,**ref.OPTICS))
    fits=[dict(e.details) for e in b.trace if e.kind=='cubic-fit']
    return dict(fits=prior.clean(fits),exact_coefficients=[[0,0],[0,0],[1,0]],coefficient_errors=[float(np.max(abs(np.array(e['coefficients'])-np.array([[0,0],[0,0],[1,0]])))) for e in fits],qualification='actual D4 double public cubic drift versus independent polynomial coefficients; no c64 drift')


def ties():
    rows=[]
    for profile in ['height-one','coarse-tie']:
        b,tr,k=ties_input(profile)
        result=s.estimate_parameters(b,tr,initial_carriers_cyc_um=k,**ref.OPTICS)
        coarse=next(dict(e.details) for e in result.trace if e.kind=='coarse')
        expected=np.array([[0,64,0,0]]) if profile=='height-one' else np.array([[0,0],[0,0],[0,0],[64,64]])
        with np.errstate(all='ignore'):rounded=b.quadratures.astype(np.complex64)
        rows.append(dict(profile=profile,coarse=prior.clean(coarse),coarse_power_error_from_exact=float(np.max(abs(coarse['correlation_power']-expected))),carrier=prior.clean(result.carriers_cyc_um),raw_modulation_scaled_2p660=prior.clean(result.raw_modulation*math.ldexp(1.,660)),brackets=prior.clean([dict(e.details) for e in result.trace if e.kind=='bracket']),parabolas=prior.clean([dict(e.details) for e in result.trace if e.kind=='parabola']),objectives=[dict(e.details)['objective'] for e in result.trace if e.kind=='evaluation'],rounded_input_nonfinite=int(np.count_nonzero(~np.isfinite(rounded))),rounded_input_nonzero=int(np.count_nonzero(rounded)),qualification='valid double tie/zero-curvature, single conversion rejects overflow before arithmetic; no c64 search'))
    return rows


def workflow(case):
    raw=np.empty((1,1,3,2,4,4),np.float64)
    for p,v in enumerate([4,6,2]):raw[:,:,p]=v
    otf=s.declare_otf(np.ones((2,8,8)),layout='radial',dkr_cyc_um=.25,dkz_cyc_um=1.)
    acq=prior.opts();acq['phase_policy']='uniform'
    kw=dict(acquisition=acq,optics=ref.OPTICS,carrier=dict(linespacing_um=10.,phase_start_angle_rad=0.,search_carriers=False),filtering=dict(wiener=.5,suppress_singularities=False,output_taper='none'),specimen_identity=dict(id='SP112-explicit-phase-observations',intensity_unit='detector-counts'),transfer=otf,transfer_identity=dict(id='SP112-unit-H',intensity_unit='dimensionless-transfer',optics=ref.OPTICS))
    result=(s.reconstruct_workflow if case=='workflow-full' else s.reconstruct_summary)(raw,**kw)
    return dict(image_sha256=ref.digest(result.image),image_dtype=str(result.image.dtype),signed_extrema=[float(result.image.min()),float(result.image.max())],carriers_sha256=ref.digest(result.carriers_cyc_um),modulation_sha256=ref.digest(result.modulation),retained_array_payload=ref.payload(result),input_payload=ref.payload(raw,otf),qualification='unchanged double full-summary compatibility, no single runtime/no physical recovery oracle')


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('--case');p.add_argument('--repeat',type=int,default=1);a=p.parse_args()
    if a.mode=='freeze':
        m=manifest();(HERE/'corrections-manifest.json').write_text(json.dumps(m,indent=2)+'\n');return dict(status='frozen',manifest_sha256=ref.sha(HERE/'corrections-manifest.json'),fresh_runs=21)
    frozen=json.loads((HERE/'corrections-manifest.json').read_text());assert frozen['script_sha256']==ref.sha(__file__) and frozen['identities']==ref.identities()
    base=dict(case=a.case,repeat=a.repeat,argv=sys.argv,environment=environment(),script_sha256=ref.sha(__file__),manifest_sha256=ref.sha(HERE/'corrections-manifest.json'))
    base['precall_ru_maxrss_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;start=time.monotonic()
    try:
        data=declarations()
        assert all(ref.digest(v)==frozen['input_hashes'][k]['sha256'] for k,v in data.items())
        if a.case=='scalar-recombination':answer=recombination()
        elif a.case=='camera':answer=camera(data)
        elif a.case=='off-combination':answer=combination(data)
        elif a.case=='cubic':answer=cubic(data)
        elif a.case=='ties-reciprocal':answer=ties()
        elif a.case.startswith('workflow-'):answer=workflow(a.case)
        else:raise ValueError(a.case)
        base.update(status='completed',result=answer)
    except Exception as e:base.update(status='failed',exception=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    base.update(seconds=time.monotonic()-start,whole_process_ru_maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    base['whole_process_peak_bytes']=base['whole_process_ru_maxrss_KiB']*1024
    return prior.clean(base)

if __name__=='__main__':print(json.dumps(main(),indent=2,allow_nan=True))
