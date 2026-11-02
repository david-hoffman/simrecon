# RA14 source-identified one-off recipes

These coordinator recipes record the fixed experiment. They are not an installed command-line interface or a new maintained file format. The actual closed manifests identify the executed bytes, inputs, commands and outcomes. No reference executable is used.

The original retained archive has SHA-256 `4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0` and size 1,706,228,839 bytes. Restore only the 46 generation members listed in the original public full-case inventory, under `artifacts/ra14/original/generation/`; verify each member against that inventory. The archive itself and complete native arrays remain locally retained inputs; this document does not supply a downloadable raw-data bundle.

Place the exact recipes below under `artifacts/ra14/study/` in a locked checkout. Preserve separate generation/reference, prepared observation-only and frozen result directories. Directory creation is exclusive; do not overwrite a prior attempt. Generation and the three arms have separate input/hash/native-resource records. Run full heavy phases serially. Actual unchanged inputs and clean producer identity are evidence, not an assumption supplied by these snippets.

```sh
.venv/bin/python artifacts/ra14/study/generate_matched.py
.venv/bin/python artifacts/ra14/study/prepare_observations.py
.venv/bin/python artifacts/ra14/study/run_fixed_arms.py
.venv/bin/python artifacts/ra14/study/evaluate.py
uv run --no-project --offline --with matplotlib==3.10.7 --with numpy==2.5.3 python artifacts/ra14/study/render.py
```

The recorded execution additionally uses `/usr/bin/time -l`, fixed prospective protocol/figure-plan JSON, input pinning and host observations. Do not confuse a command example with proof it passed. No automatic retry or outcome-based retuning is specified.

## generate_matched.py

SHA-256: `8f343cc60ca45e25f124c733dc3f0e1ff7f4ebee0f3be6f051171539f3b429af`.

```python
"""Coordinator's fixed RA14 matched-observation recipe; never an inference API."""
from pathlib import Path
import sys,json,hashlib,time,resource,subprocess,dataclasses
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from simrecon import estimate_scalar_camera
from scripts.simulation_camera import sample_camera
from scripts.simulation_optics import expected_images

OUT=ROOT/'artifacts/ra14/matched';ORIGINAL=ROOT/'artifacts/ra14/original/generation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 return {'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),'tracked_status':subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True),'describe':subprocess.run(['git','describe','--always','--dirty'],cwd=ROOT,capture_output=True,text=True).stdout.strip()}
def peak():return {'native_ru_maxrss':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'unit':'bytes' if sys.platform=='darwin' else 'KiB','scope':'whole producer process high-water; not isolated stage allocation'}
def main():
 start=time.monotonic();before=snapshot();OUT.mkdir(exist_ok=False);obs=OUT/'observations';ref=OUT/'reference';obs.mkdir();ref.mkdir();plan=json.loads((ORIGINAL/'private_truth/plan.json').read_text());truth=json.loads((ORIGINAL/'private_truth/generation_summary.json').read_text());g=plan['geometry'];cam=plan['camera'];ill=plan['illumination'];files={};stages=[]
 def save(path,array):
  assert not path.exists();np.save(path,array,allow_pickle=False);files[str(path.relative_to(OUT))]={'shape':list(array.shape),'dtype':array.dtype.str,'size_bytes':path.stat().st_size,'sha256':sha(path)}
 def stage(name,t0):stages.append({'name':name,'elapsed_seconds':time.monotonic()-t0,'memory':peak()})
 kw={'read_noise_e':0.0,'gain_counts_per_e':cam['gain_counts_per_e'],'offset_counts':cam['offset_counts'],'shot_noise':False}
 t=time.monotonic();groups={}
 for label,signal,background in [('dark',0.,0.),('blank',0.,cam['background_e']),('flat',cam['flat_signal_e'],cam['background_e'])]:
  base=np.full(tuple(g['camera_shape_yx']),signal,dtype=np.float64);groups[label]=np.stack([sample_camera(base,background_e=background,seed=seed,**kw) for seed in plan['seeds']['camera_'+label]]);save(obs/('camera_'+label+'.npy'),groups[label])
 camera=estimate_scalar_camera(groups['dark'],blank_counts=groups['blank'],flat_counts=groups['flat'],source='RA14 deterministic generation-only camera gauge');d=float(camera.contrast_counts);gain=cam['gain_counts_per_e'];assert d>0;stage('deterministic_camera',t)
 t=time.monotonic();fine=np.load(ORIGINAL/'private_truth/specimen_source_e.npy',mmap_mode='r');paired=np.asarray(fine[0::2]+fine[1::2],dtype=np.float64);x64=(gain/d)*paired;x32=x64.astype(np.float32);source=(d/gain)*x32.astype(np.float64);save(ref/'paired_electron_source.npy',paired);save(ref/'pre_round_relative_source.npy',x64);save(ref/'represented_relative_source.npy',x32);save(ref/'generator_electron_source.npy',source);del fine,paired,x64;stage('pair_and_once_round_source',t)
 q=np.array(ill['carriers_yx_per_um'],dtype=np.float64);phases=np.array(ill['phases_at_calibration_origin_rad'],dtype=np.float64);spec_phases=np.array(truth['specimen_phases_at_specimen_origin_rad'],dtype=np.float64);beams=tuple(ill['beam_amplitudes']);optics={'excitation_um':0.488,'emission_um':0.525,'refractive_index':1.515,'detection_na':1.4,'pupil_order':128,'pixel_subsamples_yx':(2,2)}
 t=time.monotonic();bead=np.load(ORIGINAL/'private_truth/bead_source_e.npy');central=expected_images(bead,detector_spacing_um_zyx=tuple(g['calibration_spacing_um_zyx']),source_refinement_zyx=(8,8,8),carriers_yx_per_um=np.zeros((1,2)),phases_rad=np.zeros((1,1)),beam_amplitudes=(1.,0.,0.),**optics)[0,0];training=expected_images(bead,detector_spacing_um_zyx=tuple(g['calibration_spacing_um_zyx']),source_refinement_zyx=(8,8,8),carriers_yx_per_um=q,phases_rad=phases,beam_amplitudes=beams,**optics);del bead
 save(ref/'calibration_central_expected_signal_e.npy',central);save(ref/'calibration_training_expected_signal_e.npy',training);heldout=np.ascontiguousarray(training[:,:5]);save(ref/'calibration_heldout_expected_signal_e.npy',heldout)
 save(obs/'calibration_central.npy',sample_camera(central,background_e=cam['background_e'],seed=plan['seeds']['calibration_central'],**kw))
 for name,means,seeds in [('training',training,plan['seeds']['calibration_training']),('heldout',heldout,plan['seeds']['calibration_heldout'])]:
  counts=np.stack([np.stack([sample_camera(means[o,p],background_e=cam['background_e'],seed=seeds[o][p],**kw) for p in range(means.shape[1])]) for o in range(3)]);save(obs/('calibration_'+name+'.npy'),counts)
 stage('Q128_original_finite_sphere_calibration',t)
 del central,training,heldout,counts
 for o in range(3):
  t=time.monotonic();means=expected_images(source,detector_spacing_um_zyx=tuple(g['specimen_spacing_um_zyx']),source_refinement_zyx=(1,2,2),carriers_yx_per_um=q[o:o+1],phases_rad=spec_phases[o:o+1],beam_amplitudes=beams,**optics)[0]
  for p in range(5):
   save(ref/f'specimen_o{o}_p{p}_expected_signal_e.npy',means[p]);save(obs/f'specimen_o{o}_p{p}.npy',sample_camera(means[p],background_e=cam['background_e'],seed=plan['seeds']['specimen'][o][p],**kw))
  del means;stage(f'Q128_matched_specimen_orientation_{o}',t)
 settings={'calibration_id':'RA14 full original geometry paired acquisition','specimen_calibration_id':'RA14 full original geometry paired acquisition','calibration_origin_um_zyx':g['calibration_origin_um_zyx'],'specimen_detector_spacing_um_zyx':g['specimen_spacing_um_zyx'],'specimen_origin_um_zyx':g['specimen_origin_um_zyx'],'sweep_scales':[1.0],'max_refinement_evaluations':40,'training_rms_limit':0.05,'calibration_atol':1e-8,'operator_atol':1e-6,'regularization':0.001,'max_iterations':12,'max_backtracking_trials':8,'source':'RA14 fixed full-scene observation-only controls'}
 (obs/'controls.json').write_text(json.dumps(settings,indent=2)+'\n');files['observations/controls.json']={'size_bytes':(obs/'controls.json').stat().st_size,'sha256':sha(obs/'controls.json')}
 known={'carriers_yx_per_um':q.tolist(),'phases_at_specimen_origin_rad':spec_phases.tolist(),'beam_amplitudes':list(beams),'illumination_source':'RA14 explicitly supplied original true illumination; known-input control only','detector_spacing_um_zyx':g['specimen_spacing_um_zyx'],'specimen_origin_um_zyx':g['specimen_origin_um_zyx'],'pupil_order':128,'regularization':0.001,'max_iterations':12,'max_backtracking_trials':8}
 (ref/'known-controls.json').write_text(json.dumps(known,indent=2)+'\n');files['reference/known-controls.json']={'size_bytes':(ref/'known-controls.json').stat().st_size,'sha256':sha(ref/'known-controls.json')}
 after=snapshot();material=['scripts/simulation_camera.py','scripts/simulation_optics.py','scripts/simulation_sources.py','src/simrecon/_scalar_camera_calibration.py','uv.lock','pyproject.toml'];result={'status':'generated','before':before,'after':after,'producer_sha256':sha(Path(__file__)),'original_generation_seal_sha256':sha(ORIGINAL/'generation.complete.json'),'plan_sha256':sha(ORIGINAL/'private_truth/plan.json'),'generation_summary_sha256':sha(ORIGINAL/'private_truth/generation_summary.json'),'material_source_sha256':{n:sha(ROOT/n) for n in material},'camera_means_counts':camera.means_counts.tolist(),'camera_contrast_counts':d,'physical_gain_estimate':camera.gain_counts_per_e,'camera_gauge_factor_gain_over_contrast':gain/d,'source_pairing':'sum adjacent fine axial masses; shift +/-0.03125um to coarse center; relative conversion then single float32 rounding; backconvert identical represented values to electrons for generator','stages':stages,'elapsed_seconds':time.monotonic()-start,'peak_memory':peak(),'files':files,'limits':['Q128 paired noiseless distinct from original Q256 fine noisy; comparison does not isolate noise','heldout noiseless repeats supply no independent noise information','known source/illumination/true camera remain outside observation-only inputs','no full-grid independent numeric bound or source recovery/resolution criterion']};(OUT/'complete.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('files','material_source_sha256')},indent=2))
if __name__=='__main__':main()
```

## prepare_observations.py

SHA-256: `ef26e3958bc8fb8792825acae984f8a7adac384bc9e63337cae201afc4337ee3`.

```python
from pathlib import Path
import json,hashlib,shutil,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 parent=ROOT/'artifacts/ra14/prepared';parent.mkdir(exist_ok=False);settings=(ROOT/'artifacts/ra14/matched/observations/controls.json').read_bytes();manifests={}
 for label,source in [('noiseless',ROOT/'artifacts/ra14/matched/observations'),('noisy',ROOT/'artifacts/ra14/original/generation/observations')]:
  out=parent/label;out.mkdir();names=['camera_dark.npy','camera_blank.npy','camera_flat.npy','calibration_central.npy','calibration_training.npy','calibration_heldout.npy']+[f'specimen_o{o}_p{p}.npy' for o in range(3) for p in range(5)];copies={}
  for name in names:
   shutil.copyfile(source/name,out/name);assert digest(out/name)==digest(source/name);copies[name]={'source_sha256':digest(source/name),'copy_sha256':digest(out/name)}
  raw=np.stack([np.stack([np.load(out/f'specimen_o{o}_p{p}.npy',allow_pickle=False) for p in range(5)]) for o in range(3)]);assert raw.shape==(3,5,32,256,256) and raw.dtype==np.float64;np.save(out/'specimen-counts.npy',raw,allow_pickle=False);del raw;(out/'controls.json').write_bytes(settings)
  files={p.name:{'sha256':digest(p),'size_bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()};seal={'format_version':'RA14_internal_observation_recipe_v1','status':'complete_raw_inputs','arm':label,'files':files,'preparation_source_sha256':digest(Path(__file__)),'limits':'Only raw arrays/declared controls; no source/illumination/true-camera/reference/seed payload. Copy and stack preserve original counts; not a product file format or authenticity certificate.'};(out/'complete.json').write_text(json.dumps(seal,indent=2)+'\n');manifests[label]={'path':str(out),'seal_sha256':digest(out/'complete.json'),'copied_frames':copies,'file_count':len(files),'bytes':sum(x['size_bytes'] for x in files.values())}
 (parent/'preparation.json').write_text(json.dumps(manifests,indent=2)+'\n');print(json.dumps({k:{x:y for x,y in v.items() if x!='copied_frames'} for k,v in manifests.items()},indent=2))
if __name__=='__main__':main()
```

## support.py

SHA-256: `032e7ed00ca1bd5b4cb431ffd7c09182714384c5bbf010ff352d5127dd08e59f`.

```python
"""Coordinator-owned immutable result persistence for the fixed RA14 experiment."""
from pathlib import Path
import dataclasses,hashlib,json,time,resource,sys,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def freeze(out,name,value):
 folder=out/(name+'-arrays');folder.mkdir(exist_ok=False);index=0
 def encode(v):
  nonlocal index
  if isinstance(v,np.ndarray):
   path=folder/f'{index:04d}.npy';index+=1;np.save(path,v,allow_pickle=False);return {'array_file':str(path.relative_to(out)),'shape':list(v.shape),'dtype':v.dtype.str,'sha256':digest(path),'size_bytes':path.stat().st_size}
  if dataclasses.is_dataclass(v):return {f.name:encode(getattr(v,f.name)) for f in dataclasses.fields(v)}
  if isinstance(v,dict):return {str(k):encode(x) for k,x in v.items()}
  if isinstance(v,(list,tuple)):return [encode(x) for x in v]
  if isinstance(v,np.generic):return encode(v.item())
  if v is None or type(v) in (str,int,float,bool):return v
  raise TypeError('unsupported returned record type '+type(v).__name__)
 encoded=encode(value);dump(out/(name+'.json'),encoded);return encoded

def snapshot():return {'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),'tracked_status':subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True),'describe':subprocess.run(['git','describe','--always','--dirty'],cwd=ROOT,capture_output=True,text=True).stdout.strip()}
def peak():return {'native_ru_maxrss':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'units':'bytes' if sys.platform=='darwin' else 'KiB','scope':'whole process high-water, not isolated stage allocation'}
class StageObserver:
 """Read-only public-function timing/high-water observation in standalone producers."""
 def __init__(self,targets):
  self.targets={fn.__code__:name for name,fn in targets.items()};self.records=[];self.entered={};self.previous=None
 def _observe(self,frame,event,arg):
  if event not in ('call','return') or frame.f_code not in self.targets:return
  code=frame.f_code
  if event=='call':self.entered.setdefault(code,[]).append((time.monotonic(),peak()))
  elif self.entered.get(code):
   started,baseline=self.entered[code].pop();self.records.append({'stage':self.targets[code],'elapsed_seconds':time.monotonic()-started,'entry_process_high_water':baseline,'exit_process_high_water':peak(),'exit_return_type':type(arg).__name__,'limits':'Public call/return observation only; None return event can reflect an exception. Native returned outcome remains authoritative. Process high-water readings overlap earlier history, not isolated stage allocations or additive peaks; profiler overhead included.'})
 def __enter__(self):
  self.previous=sys.getprofile()
  if self.previous is not None:raise RuntimeError('RA14 measurement requires an unprofiled standalone producer')
  sys.setprofile(self._observe);return self
 def __exit__(self,*exc):sys.setprofile(self.previous)

def finish(out,*,status,stage,fit,before,started,input_seal,elapsed_call,stage_observations):
 summary={'status':status,'stage':stage,'fit_status':fit.status if fit is not None else None,'fit_stop_reason':fit.stop_reason if fit is not None else None,'has_source':fit is not None and fit.source_relative is not None,'candidate_id':fit.best_score.candidate_id if fit is not None and fit.best_score is not None else None,'call_elapsed_seconds':elapsed_call,'total_elapsed_seconds':time.monotonic()-started,'peak_memory':peak(),'before':before,'after':snapshot(),'input_seal_sha256':input_seal}
 if fit is not None and fit.source_relative is not None:
  from scripts.reference_alignment_ra14_comparison import replay_source
  assert fit.best_score is not None and fit.source_spacing_um_zyx is not None
  p=out/'source_relative.npy';np.save(p,fit.source_relative,allow_pickle=False);source_before=digest(p);t=time.monotonic();prediction=replay_source(fit.source_relative,source_spacing_um_zyx=fit.source_spacing_um_zyx,carriers_yx_per_um=fit.carriers_yx_per_um,phases_at_specimen_origin_rad=fit.phases_at_specimen_origin_rad,beam_amplitudes=fit.beam_amplitudes,pupil_order=fit.pupil_order);np.save(out/'predictions_relative.npy',prediction,allow_pickle=False);assert digest(p)==source_before and np.array_equal(np.load(p,mmap_mode='r'),fit.source_relative);summary.update({'replay_seconds':time.monotonic()-t,'prediction_shape':list(prediction.shape),'source_sha256':source_before,'prediction_sha256':digest(out/'predictions_relative.npy'),'replay_limit':'production-operator replay; no independent optical reference; original fit status preserved'});del prediction
 summary['stage_observations']=list(stage_observations);summary['total_elapsed_seconds']=time.monotonic()-started;summary['peak_memory']=peak();summary['after']=snapshot();dump(out/'summary.json',summary);files={str(p.relative_to(out)):{'size_bytes':p.stat().st_size,'sha256':digest(p)} for p in out.rglob('*') if p.is_file()};dump(out/'complete.json',{'status':'frozen_real_result','summary':summary,'files':files,'limits':'No truth evaluation in this process; unavailable/partial component status preserved; timeout/exceptions cannot produce this seal.'});print(json.dumps(summary,indent=2))
```

## run_known_control.py

SHA-256: `d7ca55f0988e256afa98389896f7c7f5d9d0b3f8105c7af065f9b4594435148c`.

```python
"""Explicitly supplied nuisance truth; this is not observation-only inference."""
from pathlib import Path
import sys,json,time
import numpy as np
from support import ROOT,digest,freeze,finish,snapshot,StageObserver
sys.path.insert(0,str(ROOT))
from simrecon import estimate_scalar_camera
from scripts.image_only_specimen_fit import fit_specimen
from scripts.reference_alignment_ra14_comparison import replay_source

def main():
 obs=Path(sys.argv[1]).resolve();known=Path(sys.argv[2]).resolve();out=Path(sys.argv[3]).resolve();out.mkdir(exist_ok=False);started=time.monotonic();before=snapshot();seal=json.loads((obs/'complete.json').read_text())
 for name,d in seal['files'].items():assert digest(obs/name)==d['sha256'] and (obs/name).stat().st_size==d['size_bytes']
 kw=json.loads(known.read_text())
 for n in ('carriers_yx_per_um','phases_at_specimen_origin_rad','beam_amplitudes'):kw[n]=np.array(kw[n],dtype=np.float64)
 for n in ('detector_spacing_um_zyx','specimen_origin_um_zyx'):kw[n]=tuple(kw[n])
 with StageObserver({'camera_estimation':estimate_scalar_camera,'specimen_fit':fit_specimen,'prediction_replay':replay_source}) as observation:
  camera=estimate_scalar_camera(np.load(obs/'camera_dark.npy'),blank_counts=np.load(obs/'camera_blank.npy'),flat_counts=np.load(obs/'camera_flat.npy'),source='RA14 known-illumination control camera from deterministic raw groups');raw=np.load(obs/'specimen-counts.npy');t=time.monotonic();fit=fit_specimen(raw,camera_estimate=camera,**kw);elapsed=time.monotonic()-t;result={'arm':'known/noiseless supplied-illumination control','camera_estimate':camera,'specimen_fit':fit,'known_controls_sha256':digest(known)};freeze(out,'result',result)
  finish(out,status=fit.status,stage=fit.stage,fit=fit,before=before,started=started,input_seal=digest(obs/'complete.json'),elapsed_call=elapsed,stage_observations=observation.records)
if __name__=='__main__':main()
```

## run_observation_only.py

SHA-256: `43d0b79a71d57476725b2f1e9ea460443a17525779e7c9b3d5f4361d9a4bdbd5`.

```python
"""Only prepared raw arrays and declared metadata/controls enter this process."""
from pathlib import Path
import sys,json,time
import numpy as np
from support import ROOT,digest,freeze,finish,snapshot,StageObserver
sys.path.insert(0,str(ROOT))
from simrecon import estimate_scalar_camera
from scripts.raw_sim_workflow import reconstruct_raw_sim
from scripts.image_only_calibration_handoff import infer_calibration_handoff
from scripts.image_only_specimen_fit import fit_specimen
from scripts.reference_alignment_ra14_comparison import replay_source

def main():
 obs=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False);started=time.monotonic();before=snapshot();seal=json.loads((obs/'complete.json').read_text())
 for name,d in seal['files'].items():assert digest(obs/name)==d['sha256'] and (obs/name).stat().st_size==d['size_bytes']
 controls=json.loads((obs/'controls.json').read_text())
 for key in ('calibration_origin_um_zyx','specimen_detector_spacing_um_zyx','specimen_origin_um_zyx','sweep_scales'):controls[key]=tuple(controls[key])
 arrays={name:np.load(obs/(file+'.npy'),allow_pickle=False) for name,file in [('dark_counts','camera_dark'),('blank_counts','camera_blank'),('flat_counts','camera_flat'),('central_counts','calibration_central'),('structured_counts','calibration_training'),('heldout_counts','calibration_heldout')]};raw=np.load(obs/'specimen-counts.npy',allow_pickle=False)
 with StageObserver({'camera_estimation':estimate_scalar_camera,'predictive_handoff':infer_calibration_handoff,'specimen_fit':fit_specimen,'prediction_replay':replay_source}) as observation:
  t=time.monotonic();result=reconstruct_raw_sim(raw,**arrays,**controls);elapsed=time.monotonic()-t;freeze(out,'result',result);fit=result.specimen_fit
  finish(out,status=result.status,stage=result.stage,fit=fit,before=before,started=started,input_seal=digest(obs/'complete.json'),elapsed_call=elapsed,stage_observations=observation.records)
if __name__=='__main__':main()
```

## run_fixed_arms.py

SHA-256: `122900c12ae480c4ba449ff7dfbc8ea2bd2e79d139b85c5d44aa084798e96f15`.

```python
"""One frozen three-arm RA14 execution; no retry, tuning or fallback."""
from pathlib import Path
import sys,os,signal,subprocess,json,time,datetime,hashlib,shutil
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'artifacts/ra14/study';RECORD=STUDY/'arms-run-1';RECORD.mkdir(exist_ok=False);RUNS=ROOT/'artifacts/ra14/runs';RUNS.mkdir(exist_ok=False)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def dump(path,data):
 with path.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def host():
 cmds=[['/usr/sbin/sysctl','-n','hw.memsize'],['/usr/sbin/sysctl','vm.swapusage'],['/usr/bin/vm_stat']];out={}
 for cmd in cmds:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);out[' '.join(cmd)]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr};assert p.returncode==0
 out['disk_free_bytes']=shutil.disk_usage(ROOT).free;return out
tracked=subprocess.check_output(['git','ls-files','src','scripts'],cwd=ROOT,text=True).splitlines();paths={n:ROOT/n for n in tracked if (ROOT/n).is_file()};paths.update({str(p.relative_to(ROOT)):p for folder in (ROOT/'artifacts/ra14/original/generation',ROOT/'artifacts/ra14/matched',ROOT/'artifacts/ra14/prepared') for p in folder.rglob('*') if p.is_file()});paths.update({str(p.relative_to(ROOT)):p for p in STUDY.glob('*.py')});paths.update({n:ROOT/n for n in ('uv.lock','pyproject.toml','.python-version','.venv/pyvenv.cfg','docs/contracts/reference-alignment-ra14-v1.md','tests/test_reference_alignment_ra14_comparison.py','tests/reference_alignment_ra14_fixture.py','artifacts/ra14/study/protocol.json','artifacts/ra14/study/figure-plan.json','artifacts/ra14/B3/final.md','artifacts/ra14/C1/report.md')});paths['resolved-python-executable']=(ROOT/'.venv/bin/python').resolve()
def pin():return {name:{'size_bytes':p.stat().st_size,'sha256':digest(p)} for name,p in paths.items()}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip();assert subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)=='';before=pin();dump(RECORD/'inputs-before.json',before);began=time.monotonic();records=[];python=str(ROOT/'.venv/bin/python')
probe=subprocess.run([python,'-c','import sys,json,numpy,scipy,simrecon;from importlib.metadata import version;import scripts.raw_sim_workflow as w;import scripts.reference_alignment_ra14_comparison as e;print(json.dumps({"python":sys.version,"executable":sys.executable,"numpy":[numpy.__version__,numpy.__file__],"scipy":[scipy.__version__,scipy.__file__],"simrecon":[version("simrecon"),simrecon.__file__],"workflow":w.__file__,"comparison":e.__file__}))'],cwd=ROOT,capture_output=True,text=True,timeout=30);assert probe.returncode==0;dump(RECORD/'environment.json',json.loads(probe.stdout))
noiseless=ROOT/'artifacts/ra14/prepared/noiseless';noisy=ROOT/'artifacts/ra14/prepared/noisy';known=ROOT/'artifacts/ra14/matched/reference/known-controls.json'
commands=[('known-noiseless',[python,str(STUDY/'run_known_control.py'),str(noiseless),str(known),str(RUNS/'known-noiseless')]),('estimated-noiseless',[python,str(STUDY/'run_observation_only.py'),str(noiseless),str(RUNS/'estimated-noiseless')]),('estimated-noisy',[python,str(STUDY/'run_observation_only.py'),str(noisy),str(RUNS/'estimated-noisy')])]
for name,call in commands:
 out=RECORD/name;out.mkdir();t=time.monotonic();meta={'arm':name,'command':['/usr/bin/time','-l']+call,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'tree':tree,'host_before':host(),'operational_timeout_seconds':7200,'human_numeric_limits':'not set'};dump(out/'launch.json',meta)
 with (out/'stdout.log').open('w') as so,(out/'stderr-native-time.log').open('w') as se:
  p=subprocess.Popen(meta['command'],cwd=ROOT,stdout=so,stderr=se,start_new_session=True)
  try:rc=p.wait(timeout=7200);timed_out=False
  except subprocess.TimeoutExpired:
   timed_out=True
   try:os.killpg(p.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:rc=p.wait(timeout=30)
   except subprocess.TimeoutExpired:
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    rc=p.wait(timeout=30)
 current=pin();unchanged=current==before and subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head and subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)=='';seal=RUNS/name/'complete.json';record={'arm':name,'returncode':rc,'timed_out':timed_out,'elapsed_seconds':time.monotonic()-t,'host_after':host(),'all_material_inputs_unchanged':unchanged,'process_group_closed_by_native_completion_or_timeout_handling':True,'result_seal_present':seal.is_file(),'result_seal_sha256':digest(seal) if seal.is_file() else None,'classification':'real_frozen_return' if rc==0 and not timed_out and unchanged and seal.is_file() else 'incomplete_requires_diagnosis'}
 if record['classification']=='real_frozen_return':record['actual_result_summary']=json.loads(seal.read_text())['summary']
 records.append(record);dump(out/'completion.json',record);print(json.dumps({'arm':name,'returncode':rc,'timed_out':timed_out,'elapsed_seconds':record['elapsed_seconds'],'all_material_inputs_unchanged':unchanged,'actual_status':record.get('actual_result_summary',{}).get('status'),'has_source':record.get('actual_result_summary',{}).get('has_source')},indent=2),flush=True)
 if record['classification']!='real_frozen_return':dump(RECORD/'incomplete.json',{'records':records,'status':'incomplete_no_retry','inputs_changed':[n for n in before if current[n]!=before[n]]});raise SystemExit(1)
after=pin();dump(RECORD/'inputs-after.json',after);assert before==after;dump(RECORD/'complete.json',{'status':'three_real_arms_frozen','head':head,'tree':tree,'elapsed_seconds':time.monotonic()-began,'pinned_files':len(paths),'inputs_unchanged':True,'records':records,'limits':'No source/illumination/camera truth enters either observation-only process. Known input is explicitly separate. High-water/process/host observations are not isolated allocations or portable bounds; profiling overhead included. Unavailable/partial native return is not a positive scientific success. No retry/downsize/tuning or reference execution.'});print('Three fixed arms complete; every declared material input unchanged.',flush=True)
```

## evaluate.py

SHA-256: `f8b49eeb5fb0d18c2ad6230bc5dcc7678425d32d73d011dce4c56d096e8088cd`.

```python
"""Post-freeze RA14 descriptive evaluation. Truth is never an inference argument."""
from pathlib import Path
import sys,json,dataclasses,time,math
import numpy as np
from support import ROOT,digest,dump,peak
sys.path.insert(0,str(ROOT))
from scripts.reference_alignment_ra14_comparison import compare_arrays,replay_source

def metric(a,b):return dataclasses.asdict(compare_arrays(np.asarray(a),np.asarray(b)))
def check_seal(folder):
 seal=json.loads((folder/'complete.json').read_text())
 for n,d in seal['files'].items():assert digest(folder/n)==d['sha256'] and (folder/n).stat().st_size==d['size_bytes']
 return seal

def power_axes(array,spacing):
 f=np.fft.fftn(np.asarray(array,dtype=np.float64),norm='ortho');power=f.real*f.real+f.imag*f.imag
 return {'frequency_cycles_per_um':[np.fft.fftfreq(n,d=d).tolist() for n,d in zip(array.shape,spacing)],'axis_power_sums':[np.sum(power,axis=tuple(j for j in range(3) if j!=i)).tolist() for i in range(3)],'spatial_squared_norm':float(np.sum(np.asarray(array,dtype=np.float64)**2)),'spectral_squared_norm':float(np.sum(power)),'definition':'full-frame untapered unitary DFT; sum |F|^2 on other axes; descriptive image/residual power, not an OTF or resolution measure'}

def profiles(source,reference,spacing,catalogue):
 axes=[(np.arange(n)+.5)*d for n,d in zip(source.shape,spacing)];result=[]
 for row,object_row in enumerate(catalogue):
  centre=object_row[:3];indices=[int(np.argmin(np.abs(v-c))) for v,c in zip(axes,centre)];lines=[]
  for axis in range(3):
   selector=list(indices);selector[axis]=slice(None);key=tuple(selector);lines.append({'axis_zyx':axis,'coordinate_um':axes[axis].tolist(),'reference':np.asarray(reference[key],dtype=np.float64).tolist(),'estimate':np.asarray(source[key],dtype=np.float64).tolist()})
  result.append({'catalogue_index':row,'requested_centre_um_zyx':centre,'actual_indices_zyx':indices,'actual_centre_um_zyx':[float(v[i]) for v,i in zip(axes,indices)],'selection':'nearest represented grid centre, first index on represented tie; no fit/interpolation','lines':lines})
 return result

def main():
 start=time.monotonic();runs=ROOT/'artifacts/ra14/runs';out=ROOT/'artifacts/ra14/evaluation-1';out.mkdir(exist_ok=False)
 # Verify every inference payload before opening any evaluator-only reference.
 frozen={name:check_seal(runs/name) for name in ('known-noiseless','estimated-noiseless','estimated-noisy')}
 original=ROOT/'artifacts/ra14/original/generation';matched=ROOT/'artifacts/ra14/matched';generated=json.loads((matched/'complete.json').read_text())
 for n,d in generated['files'].items():assert digest(matched/n)==d['sha256']
 plan=json.loads((original/'private_truth/plan.json').read_text());cam=plan['camera'];gain=cam['gain_counts_per_e'];spacing=tuple(plan['geometry']['specimen_spacing_um_zyx']);source_spacing=(spacing[0],spacing[1]/2,spacing[2]/2);known=json.loads((matched/'reference/known-controls.json').read_text());x32=np.asarray(np.load(matched/'reference/represented_relative_source.npy',mmap_mode='r'));paired=np.asarray(np.load(matched/'reference/paired_electron_source.npy',mmap_mode='r'));pre_round=np.asarray(np.load(matched/'reference/pre_round_relative_source.npy',mmap_mode='r'));electron_matched=np.asarray(np.load(matched/'reference/generator_electron_source.npy',mmap_mode='r'))
 output={'status':'evaluated_frozen_results','producer_sha256':digest(Path(__file__)),'protocol_sha256':digest(ROOT/'artifacts/ra14/study/protocol.json'),'figure_plan_sha256':digest(ROOT/'artifacts/ra14/study/figure-plan.json'),'inference_seal_sha256':{n:digest(runs/n/'complete.json') for n in frozen},'original_generation_seal_sha256':digest(original/'generation.complete.json'),'matched_generation_seal_sha256':digest(matched/'complete.json'),'source_rounding':{'pre_round_to_float32':metric(x32,pre_round),'backconversion':metric((gain/generated['camera_contrast_counts'])*electron_matched,x32),'signed_mass_change_relative':math.fsum((x32.astype(np.float64)-pre_round).ravel()),'nonzero_coefficients_lost':int(np.count_nonzero((pre_round!=0)&(x32==0))),'axial_site_displacement_um':0.03125},'arms':{},'limits':['No source recovery/uncertainty/resolvability acceptance threshold adopted','Full-grid numerical budget not independently qualified; measured agreement descriptive','Known/noiseless and estimated/noiseless use pairedQ128; original noisy uses fineQ256; difference does not isolate noise','No matched conventional/photon-budget resolution control','Noisy fits diagnostic; finite iteration stops not convergence; procedural truth separation only']}
 for name,seal in frozen.items():
  folder=runs/name;native=json.loads((folder/'result.json').read_text());summary=seal['summary'];fit=native.get('specimen_fit');camera=native.get('camera_estimate');arm={'summary':summary,'result_json_sha256':digest(folder/'result.json'),'training_rms':native.get('handoff',{}).get('training_rms') if native.get('handoff') else None,'reason_code':native.get('reason_code'),'failure_code':native.get('failure_code',fit.get('failure_code') if fit else None),'message':native.get('message',fit.get('message') if fit else None),'fit_diagnostics':{k:fit.get(k) for k in ('status','stage','stop_reason','message','failure_code','failure_component')} if fit else None,'fit_metrics':None}
  if camera is not None:
   means=np.load(folder/camera['means_counts']['array_file'],allow_pickle=False);expected_means=np.array([cam['offset_counts'],cam['offset_counts']+gain*cam['background_e'],cam['offset_counts']+gain*(cam['background_e']+cam['flat_signal_e'])],dtype=np.float64);cg=camera['gain_counts_per_e'];arm['camera_summary']={'means_counts':means.tolist(),'contrast_counts':camera['contrast_counts'],'physical_gain_counts_per_e':cg,'means_error_counts':(means-expected_means).tolist(),'contrast_error_counts':camera['contrast_counts']-gain*cam['flat_signal_e'],'physical_gain_error_counts_per_e':cg-gain if cg is not None else None,'gain_unavailable_reason':'estimate_unavailable' if cg is None else None,'limit':'Descriptive comparison after freeze; no noise-confidence/instrument-accuracy criterion; physical gain not required for positivecontrast normalization.'}
  else:arm['camera_summary']=None
  if not summary['has_source']:
   assert not (folder/'source_relative.npy').exists() and not (folder/'predictions_relative.npy').exists();arm['unavailable_metrics']='no scored source/predictions in genuine frozen outcome';output['arms'][name]=arm;continue
  assert fit is not None and fit['source_relative'] is not None and fit['best_score'] is not None
  pred=np.asarray(np.load(folder/'predictions_relative.npy',mmap_mode='r'));source=np.asarray(np.load(folder/'source_relative.npy',mmap_mode='r'));b=fit['blank_counts'];d=fit['contrast_counts'];is_noisy=name=='estimated-noisy';refs=original/'private_truth' if is_noisy else matched/'reference';prepared=ROOT/'artifacts/ra14/prepared'/('noisy' if is_noisy else 'noiseless');raw=np.asarray(np.load(prepared/'specimen-counts.npy',mmap_mode='r'));means=np.stack([np.stack([np.load(refs/f'specimen_o{o}_p{p}_expected_signal_e.npy') for p in range(5)]) for o in range(3)]);signal=(gain/d)*means;corrected=(cam['offset_counts']+gain*(means+cam['background_e'])-b)/d;observed=(raw-b)/d;xref=(gain/d)*paired if is_noisy else x32
  if not is_noisy:assert d==generated['camera_contrast_counts']
  m={'source':metric(source,xref),'signal_predictions':metric(pred,signal),'corrected_mean_predictions':metric(pred,corrected),'observed_predictions':metric(pred,observed),'per_frame':[],'original_best_score':fit['best_score'],'original_initial_score':fit['initial_score'],'stopping_status':fit['status'],'stop_reason':fit['stop_reason'],'candidate_id':fit['best_score']['candidate_id'],'counts':fit['counts'],'attempt_trace':fit['attempt_trace'],'last_complete_gradient':fit['last_complete_gradient'],'source_reference':'original fine axial mass pair times actualgauge' if is_noisy else 'identical once-rounded float32 matched coefficient reference'};spectra=[]
  for o in range(3):
   for p in range(5):
    residual=pred[o,p]-observed[o,p];m['per_frame'].append({'orientation':o,'phase':p,'signal':metric(pred[o,p],signal[o,p]),'corrected_mean':metric(pred[o,p],corrected[o,p]),'observed':metric(pred[o,p],observed[o,p])});spectra.append({'orientation':o,'phase':p,'prediction':power_axes(pred[o,p],spacing),'signal_reference':power_axes(signal[o,p],spacing),'corrected_mean_reference':power_axes(corrected[o,p],spacing),'observed':power_axes(observed[o,p],spacing),'signed_observed_residual':power_axes(residual,spacing)})
  m['replay_data_objective']=.5*m['observed_predictions']['error_rms']**2;m['replay_penalty_objective']=.5*fit['regularization']*float(np.mean(source.astype(np.float64)**2));m['replay_total_objective']=m['replay_data_objective']+m['replay_penalty_objective'];m['camera_blank_counts']=b;m['camera_contrast_counts']=d
  dump(out/(name+'-profiles.json'),profiles(source,xref,source_spacing,plan['specimen_catalogue']));dump(out/(name+'-image-spectra.json'),spectra);dump(out/(name+'-source-spectra.json'),{'estimate':power_axes(source,source_spacing),'reference':power_axes(xref,source_spacing),'difference':power_axes(source.astype(np.float64)-xref,source_spacing)});arm['fit_metrics']=m;output['arms'][name]=arm
  del means,signal,corrected,observed,raw,pred,source,xref
 # Supplied-known forward diagnostic after every inference result was closed.
 reference_prediction=replay_source(x32,source_spacing_um_zyx=source_spacing,carriers_yx_per_um=np.array(known['carriers_yx_per_um'],dtype=np.float64),phases_at_specimen_origin_rad=np.array(known['phases_at_specimen_origin_rad'],dtype=np.float64),beam_amplitudes=np.array(known['beam_amplitudes'],dtype=np.float64),pupil_order=128);np.save(out/'known-source-forward-relative.npy',reference_prediction,allow_pickle=False)
 means=np.stack([np.stack([np.load(matched/'reference'/f'specimen_o{o}_p{p}_expected_signal_e.npy') for p in range(5)]) for o in range(3)]);d=generated['camera_contrast_counts'];b=generated['camera_means_counts'][1];signal=(gain/d)*means;raw=np.asarray(np.load(ROOT/'artifacts/ra14/prepared/noiseless/specimen-counts.npy',mmap_mode='r'));normalized=(raw-b)/d;output['matched_forward_diagnostic']={'metrics':metric(reference_prediction,signal),'per_frame':[{'orientation':o,'phase':p,'metrics':metric(reference_prediction[o,p],signal[o,p])} for o in range(3) for p in range(5)],'camera_sequential_roundoff':metric(normalized,signal),'limit':'Known supplied-source component comparison; not an observation-only arm, no independently qualified full-grid numerical bound'}
 from scripts.simulation_inverse_operator import build_kernel_cache
 cache=build_kernel_cache(source_shape_zyx=tuple(x32.shape),source_spacing_um_zyx=source_spacing,emission_um=.525,refractive_index=1.515,detection_na=1.4,pupil_order=128);lags=[0,16,31];selected=np.array(cache.lateral_spectra[lags],copy=True);np.save(out/'declared-cache-selected-lags.npy',selected,allow_pickle=False);dump(out/'declared-cache-representation.json',{'source_shape_zyx':list(x32.shape),'source_spacing_um_zyx':list(source_spacing),'selected_absolute_axial_lags':lags,'axial_lag_um':[i*source_spacing[0] for i in lags],'ky_cycles_per_um':np.fft.fftfreq(2*x32.shape[1],d=source_spacing[1]).tolist(),'kx_cycles_per_um':np.fft.rfftfreq(2*x32.shape[2],d=source_spacing[2]).tolist(),'dtype':selected.dtype.str,'units':'um^-2; unnormalized lateral DFT of finite computational embedding, no pixel-area factor','limits':'Actual signed native cache half-spectrum, not a continuous/global3D optical transfer function, recovered bandwidth or information analysis. Unused embedding values may affect this representation without changing retained finite interactions.'});del cache,selected
 baseline=ROOT/'docs/studies/full-noisy-study-2026-10-26/evidence/post-correction-full-evaluation.json';old=json.loads(baseline.read_text());output['historical_PR53_baseline']={'source_file':str(baseline.relative_to(ROOT)),'sha256':digest(baseline),'metrics':{k:old[k] for k in ('status','inference_status','source_metrics','signal_prediction_metrics','corrected_mean_prediction_metrics')},'limit':'Historical inference settings/model differ; retained baseline, not a fresh run or noise-only comparator'}
 output.update({'elapsed_seconds':time.monotonic()-start,'memory':peak(),'scientific_alignment':'not established','resolution_improvement':'not established','experiment_delivery':'all3frozenrealoutcomes evaluated; software checks/review remain separate'});dump(out/'evaluation.json',output);files={str(p.relative_to(out)):{'size_bytes':p.stat().st_size,'sha256':digest(p)} for p in out.rglob('*') if p.is_file()};dump(out/'complete.json',{'status':'closed_postfreeze_evaluation','files':files,'inference_seal_sha256':output['inference_seal_sha256']});print(json.dumps({'status':output['status'],'elapsed_seconds':output['elapsed_seconds'],'arms':{k:{'status':v['summary']['status'],'has_source':v['summary']['has_source'],'source_relative_l2':v['fit_metrics']['source']['relative_l2'] if v['fit_metrics'] else None} for k,v in output['arms'].items()},'matched_forward':output['matched_forward_diagnostic']['metrics']},indent=2))
if __name__=='__main__':main()
```

## render.py

SHA-256: `dc80e034ba8cb96fafb2b974f20c101baa1a8a5a616bf5755d8b56875eea24cc`.

```python
"""Physical-axis rendering of closed RA14 arrays; no inference or fitted scaling."""
from pathlib import Path
import json,hashlib,time,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];EVAL=ROOT/'artifacts/ra14/evaluation-1';OUT=ROOT/'artifacts/ra14/render-1';OUT.mkdir(exist_ok=False)
plt.rcParams.update({'font.size':10,'axes.titlesize':11,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report=json.loads((EVAL/'evaluation.json').read_text());plan=json.loads((ROOT/'docs/studies/full-noisy-study-2026-10-26/full-plan.json').read_text());g=plan['geometry'];spacing=np.array(g['specimen_spacing_um_zyx'],dtype=float);ss=spacing/np.array([1,2,2]);lengths=np.array(g['specimen_shape_zyx'])*spacing;catalogue=plan['specimen_catalogue'];records={};started=time.monotonic()
def save(fig,name,caption):
 path=OUT/(name+'.png');fig.savefig(path,dpi=150);plt.close(fig);records[name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'size_bytes':path.stat().st_size,'caption':caption}
def panels(reference,estimate,*,step,name,title,unit,caption):
 reference=np.asarray(reference,dtype=np.float64);estimate=np.asarray(estimate,dtype=np.float64);coords=[(np.arange(n)+.5)*d for n,d in zip(reference.shape,step)];centre=catalogue[0][:3];iz,iy,ix=[int(np.argmin(abs(v-c))) for v,c in zip(coords,centre)];get=[lambda a:np.max(a,axis=0),lambda a:np.max(a,axis=1),lambda a:a[iz],lambda a:a[:,iy,:]];rowlabels=['XY maximum over z','XZ maximum over y',f'XY section z={coords[0][iz]:.4f} µm',f'XZ section y={coords[1][iy]:.4f} µm'];extents=[(0,lengths[2],0,lengths[1]),(0,lengths[2],0,lengths[0])]*2;vmin=min(0.,float(np.min(reference)),float(np.min(estimate)));vmax=max(float(np.max(reference)),float(np.max(estimate)));vmax=vmax if vmax>0 else 1.;differences=[f(estimate)-f(reference) for f in get];dv=max(float(np.max(np.abs(a))) for a in differences);dv=dv if dv>0 else 1.;fig,axes=plt.subplots(4,3,figsize=(13,12),gridspec_kw={'height_ratios':[5,1,5,1]},layout='constrained')
 for row,f in enumerate(get):
  for col,a in enumerate((f(reference),f(estimate),differences[row])):
   ax=axes[row,col];im=ax.imshow(a,interpolation='nearest',origin='lower',extent=extents[row],aspect='equal',cmap='RdBu_r' if col==2 else 'viridis',vmin=-dv if col==2 else vmin,vmax=dv if col==2 else vmax);ax.set_xlabel('x (µm)');ax.set_ylabel(('y' if row%2==0 else 'z')+' (µm)');ax.set_title(rowlabels[row]+'\n'+('Reference','Finite fit','Fit − reference')[col])
 fig.colorbar(axes[0,0].images[0],ax=axes[:,:2].ravel().tolist(),shrink=.85,label=unit);fig.colorbar(axes[0,2].images[0],ax=axes[:,2].ravel().tolist(),shrink=.85,label=unit);fig.suptitle(title);save(fig,name,caption+f' First catalogue centre requested z/y/x={centre} µm. Actual fixed source/detector sections z={coords[0][iz]:.4f}, y={coords[1][iy]:.4f} µm; nearest native grid, no interpolation/registration. Shared linear amplitude scale{vmin:.8g}..{vmax:.8g}; signed differences ±{dv:.8g}. Projected differences subtract displayed projections. Equal physical aspect.')

# Stage/status evidence is separate from any source image or scientific success claim.
fig,ax=plt.subplots(figsize=(12,3.6),layout='constrained');ax.axis('off');rows=[]
for name,arm in report['arms'].items():
 s=arm['summary'];rows.append([name,s['status'],s['stage'],s['fit_stop_reason'] or 'not produced',f"{100*arm['fit_metrics']['source']['relative_l2']:.3f}%" if arm['fit_metrics'] and arm['fit_metrics']['source']['relative_l2'] is not None else 'unavailable'])
table=ax.table(cellText=rows,colLabels=['Arm','Native outcome','Stage','Finite fit stop','Relative source error'],loc='center',cellLoc='left',colLoc='left');table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,2.5);ax.set_title('Actual frozen outcomes; finite procedure completion is not scientific alignment');save(fig,'workflow-outcomes','Actual closed result labels. Known/noiseless supplies true illumination to the existing fitter; estimated arms call RA13 using only raw arrays/declared controls. Unavailable has no source/predictions. No convergence, recovery or resolution verdict follows from a finite stop.')

for name,arm in report['arms'].items():
 if not arm['summary']['has_source']:continue
 folder=ROOT/'artifacts/ra14/runs'/name;source=np.asarray(np.load(folder/'source_relative.npy',mmap_mode='r'));prediction=np.asarray(np.load(folder/'predictions_relative.npy',mmap_mode='r'));m=arm['fit_metrics'];d=m['camera_contrast_counts'];is_noisy=name=='estimated-noisy';paired=np.asarray(np.load(ROOT/'artifacts/ra14/matched/reference/paired_electron_source.npy',mmap_mode='r'));reference=(plan['camera']['gain_counts_per_e']/d)*paired if is_noisy else np.asarray(np.load(ROOT/'artifacts/ra14/matched/reference/represented_relative_source.npy',mmap_mode='r'));err=m['source']['relative_l2'];title=f'{name}: source, relative L2 error {100*err:.3f}% — {m["stop_reason"]}'
 panels(reference,source,step=ss,name=name+'-source-comparison',title=title,unit='Integrated relative weight',caption='Observed finite source estimate versus the declared paired-basis reference. Axial mass pairing shifts original fine sites by ±0.03125 µm; this is not the original continuous scene or an electron-density image.')
 refroot=ROOT/'artifacts/ra14/original/generation/private_truth' if is_noisy else ROOT/'artifacts/ra14/matched/reference';mu=np.load(refroot/'specimen_o0_p0_expected_signal_e.npy');signal=(plan['camera']['gain_counts_per_e']/d)*mu;panels(signal,prediction[0,0],step=spacing,name=name+'-prediction-comparison',title=name+': predeclared orientation0 / phase0 prediction',unit='Reference-flat-relative image',caption='Fixed exposure0/0, selected before inference. Prediction versus noiseless signal in the actual camera gauge; this is not an observed-noise residual. All15 observed/expected residual metrics and spectra are retained separately.')
 trace=m['attempt_trace'];scored=[x for x in trace if x['score'] is not None];fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
 for key,label in [('total_objective','Total'),('data_objective','Data'),('penalty_objective','Penalty')]:
  values=np.array([x['score'][key] for x in scored]);axes[0].plot([x['candidate_id'] for x in scored],np.where(values>0,values,np.nan),marker='.',label=label)
 accepted=[x for x in scored if x['outcome'] in ('initial_scored','accepted')];axes[0].scatter([x['candidate_id'] for x in accepted],[x['score']['total_objective'] for x in accepted],facecolors='none',edgecolors='black',label='Initial / accepted score')
 gradients=[x['gradient'] for x in trace if x['gradient_state']=='complete'];projected=[x for x in trace if x['projected_gradient_max_abs'] is not None]
 if gradients:axes[1].plot([x['candidate_id'] for x in gradients],np.where(np.array([x['max_abs'] for x in gradients])>0,[x['max_abs'] for x in gradients],np.nan),marker='.',label='Completed approximate gradient max')
 if projected:axes[1].plot([x['candidate_id'] for x in projected],np.where(np.array([x['projected_gradient_max_abs'] for x in projected])>0,[x['projected_gradient_max_abs'] for x in projected],np.nan),marker='.',label='Trial projected-gradient diagnostic')
 for ax in axes:ax.axvline(m['candidate_id'],color='.5',ls=':',label='Returned best candidate');ax.set(xlabel='Actual entered candidate ID',yscale='log');ax.legend(fontsize=8)
 axes[0].set_ylabel('Declared normalized objective');axes[1].set_ylabel('Stored finite gradient diagnostic');fig.suptitle(name+': '+str(m['stop_reason'])+'; finite trial history, convergence unestablished');save(fig,name+'-finite-trial-history','All completely scored candidates retain actual data/penalty/total values, including rejected trials. Rings mark the initial and accepted scores. Gradient points belong only to their own completed candidate; missing terminal gradients are not filled. Zero values are omitted only on log axes. Original trial/step/call/partial/stopping records remain in the native freeze. A hard stop or decreasing objective is not convergence or source recovery.')
 profiles=json.loads((EVAL/(name+'-profiles.json')).read_text());fig,axes=plt.subplots(4,3,figsize=(14,10),layout='constrained')
 for j,index in enumerate((0,10)):
  item=profiles[index]
  for axis,line in enumerate(item['lines']):
   x=np.array(line['coordinate_um']);ref=np.array(line['reference']);est=np.array(line['estimate']);upper=axes[2*j,axis];lower=axes[2*j+1,axis]
   upper.plot(x,ref,label='Reference',lw=1.5);upper.plot(x,est,label='Finite fit',lw=1.5);upper.axvline(item['requested_centre_um_zyx'][axis],color='.5',lw=.8,ls=':');upper.set(xlabel='zyx'[axis]+' (µm)',ylabel='Integrated relative weight',title=f'Catalogue object{index}, quantitative full line')
   for values,label in ((ref,'Reference / own full-line peak'),(est,'Fit / own full-line peak')):
    peak=float(np.max(np.abs(values)))
    if peak>0:lower.plot(x,values/peak,label=label,lw=1.5)
    else:lower.text(.02,.9,label+': unavailable (zero line)',transform=lower.transAxes,fontsize=8)
   centre=item['requested_centre_um_zyx'][axis];lower.set(xlim=(max(0,centre-.6),min(lengths[axis],centre+.6)),xlabel='zyx'[axis]+' (µm)',ylabel='Own-peak shape only',title='Fixed ±0.6 µm display window');lower.axvline(centre,color='.5',lw=.8,ls=':')
 axes[0,0].legend(fontsize=8);axes[1,0].legend(fontsize=8);fig.suptitle(name+': fixed catalogue-centre profiles; shape normalization is not amplitude recovery');save(fig,name+'-fixed-profiles','Predeclared catalogue indices0 and10. Quantitative top rows retain full native lines and actual integrated weights. Shape rows divide each complete line by its own absolute peak, with a fixed ±0.6 µm display window; zero lines have no normalized curve. Nearest fixed grid planes, no fitted peak, interpolation or registration. All27 native profile triples and exact selected plane coordinates are retained in the closed JSON.')
 per=m['per_frame'];mean=np.array([x['observed']['error_mean'] for x in per]).reshape(3,5);rms=np.array([x['observed']['error_rms'] for x in per]).reshape(3,5);fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained');v=float(np.max(np.abs(mean)));v=v if v else 1.
 for ax,data,label in zip(axes,(mean,rms),('Signed mean observed residual','Observed residual RMS')):
  im=ax.imshow(data,interpolation='nearest',origin='lower',aspect='auto',cmap='RdBu_r' if data is mean else 'viridis',vmin=-v if data is mean else 0,vmax=v if data is mean else None);ax.set(xlabel='Phase index',ylabel='Orientation index',title=label);ax.set_xticks(range(5));ax.set_yticks(range(3));fig.colorbar(im,ax=ax,label='Relative image units')
 fig.suptitle(name+': all15 complete-frame training residuals');save(fig,name+'-all15-residuals','Each cell uses all32×256×256 voxels of its exposure, prediction minus signed camera-normalized observed counts. These are training residuals, not held-out validation or a source-recovery criterion.')
 spectra=json.loads((EVAL/(name+'-image-spectra.json')).read_text());fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
 for axis,ax in enumerate(axes):
  for key,label in [('signal_reference','Noiseless signal'),('prediction','Prediction'),('signed_observed_residual','Observed residual')]:
   power=sum((np.array(v[key]['axis_power_sums'][axis]) for v in spectra));frequency=np.array(spectra[0][key]['frequency_cycles_per_um'][axis]);ix=np.argsort(frequency);ax.plot(frequency[ix],np.where(power[ix]>0,power[ix],np.nan),label=label)
  ax.set(xlabel='zyx'[axis]+' frequency (cycles/µm)',ylabel='Sum of unitary Fourier power',yscale='log',title='All15 exposures, full-frame power')
 axes[0].legend(fontsize=8);fig.suptitle(name+': descriptive image/residual spectra; no recovered-bandwidth or resolution claim');save(fig,name+'-image-spectra','Untapered full3D DFT with norm=ortho, summed over the other two frequency axes and all15 exposures. Power retains relative-image squared units. Zero power is not drawn on the log axis. No fitted scaling, source-spectrum division, optical transfer or observable-mode inference.')
 source_spectra=json.loads((EVAL/(name+'-source-spectra.json')).read_text());fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
 for axis,ax in enumerate(axes):
  for key,label in [('reference','Paired-basis reference'),('estimate','Finite source'),('difference','Source difference')]:
   record=source_spectra[key];frequency=np.array(record['frequency_cycles_per_um'][axis]);power=np.array(record['axis_power_sums'][axis]);ix=np.argsort(frequency);ax.plot(frequency[ix],np.where(power[ix]>0,power[ix],np.nan),label=label)
  ax.set(xlabel='zyx'[axis]+' frequency (cycles/µm)',ylabel='Sum of unitary coefficient power',yscale='log',title='Complete paired source basis')
 axes[0].legend(fontsize=8);fig.suptitle(name+': descriptive source-basis Fourier power; observable modes unestablished');save(fig,name+'-source-spectra','Untapered unitary full3D source-coefficient DFT, other-axis power sums. Integrated-relative-weight squared units, native paired basis. Difference power is the DFT of the signed coefficient difference. Zero power is not drawn on the log axis. These are not optical transfer, observable-subspace recovery, resolvability or a physical-resolution criterion.')
 del source,prediction,reference,paired

cache=np.load(EVAL/'declared-cache-selected-lags.npy');meta=json.loads((EVAL/'declared-cache-representation.json').read_text());fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
for values,lag in zip(cache,meta['axial_lag_um']):ax.plot(meta['kx_cycles_per_um'],values[0],label=f'|axial lag|={lag:g} µm')
ax.set(xlabel='Computational x frequency (cycles/µm), ky=0',ylabel='Signed cache coefficient (µm⁻²)',title='Declared Q128 finite cache representation — not an optical transfer function');ax.legend();save(fig,'declared-cache-representation',meta['limits']+' '+meta['units']+'. Fixed absolute lag indices0,16,31 and native ky=0. These computational-embedding coefficients are not measured/recovered bandwidth or a scalar global3D OTF.')
manifest={'status':'rendered_closed_evidence','producer_sha256':sha(Path(__file__)),'evaluation_seal_sha256':sha(EVAL/'complete.json'),'figure_plan_sha256':sha(ROOT/'artifacts/ra14/study/figure-plan.json'),'numpy':np.__version__,'matplotlib':matplotlib.__version__,'elapsed_seconds':time.monotonic()-started,'figures':records,'limits':'Rendering only; no inference/evaluation output mutation or recovery/resolution certification. All per-arm arrays remain native grids; no image registration or brightness fit.'};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'figure_count':len(records),'elapsed_seconds':manifest['elapsed_seconds'],'names':list(records)},indent=2))
```

## Corrected timing environment and actual post-freeze recipes

The original evaluator and its output remain at their original paths. Its timing wrapper returned 1 after a denied system query. The successful second evaluation changes only its exclusive output directory to `evaluation-2`; the actual renderer reads that closed output. Numerical settings/equations and all three frozen inference results are unchanged. Actual commands use `evaluate_second.py` and `render_second.py` in place of the first versions above.

### evaluate_second.py

SHA-256: `243975fd3ff3ab48702805df529661644bddf3718ecb4c9964ead4913743ac06`.

```python
"""Post-freeze RA14 descriptive evaluation. Truth is never an inference argument."""
from pathlib import Path
import sys,json,dataclasses,time,math
import numpy as np
from support import ROOT,digest,dump,peak
sys.path.insert(0,str(ROOT))
from scripts.reference_alignment_ra14_comparison import compare_arrays,replay_source

def metric(a,b):return dataclasses.asdict(compare_arrays(np.asarray(a),np.asarray(b)))
def check_seal(folder):
 seal=json.loads((folder/'complete.json').read_text())
 for n,d in seal['files'].items():assert digest(folder/n)==d['sha256'] and (folder/n).stat().st_size==d['size_bytes']
 return seal

def power_axes(array,spacing):
 f=np.fft.fftn(np.asarray(array,dtype=np.float64),norm='ortho');power=f.real*f.real+f.imag*f.imag
 return {'frequency_cycles_per_um':[np.fft.fftfreq(n,d=d).tolist() for n,d in zip(array.shape,spacing)],'axis_power_sums':[np.sum(power,axis=tuple(j for j in range(3) if j!=i)).tolist() for i in range(3)],'spatial_squared_norm':float(np.sum(np.asarray(array,dtype=np.float64)**2)),'spectral_squared_norm':float(np.sum(power)),'definition':'full-frame untapered unitary DFT; sum |F|^2 on other axes; descriptive image/residual power, not an OTF or resolution measure'}

def profiles(source,reference,spacing,catalogue):
 axes=[(np.arange(n)+.5)*d for n,d in zip(source.shape,spacing)];result=[]
 for row,object_row in enumerate(catalogue):
  centre=object_row[:3];indices=[int(np.argmin(np.abs(v-c))) for v,c in zip(axes,centre)];lines=[]
  for axis in range(3):
   selector=list(indices);selector[axis]=slice(None);key=tuple(selector);lines.append({'axis_zyx':axis,'coordinate_um':axes[axis].tolist(),'reference':np.asarray(reference[key],dtype=np.float64).tolist(),'estimate':np.asarray(source[key],dtype=np.float64).tolist()})
  result.append({'catalogue_index':row,'requested_centre_um_zyx':centre,'actual_indices_zyx':indices,'actual_centre_um_zyx':[float(v[i]) for v,i in zip(axes,indices)],'selection':'nearest represented grid centre, first index on represented tie; no fit/interpolation','lines':lines})
 return result

def main():
 start=time.monotonic();runs=ROOT/'artifacts/ra14/runs';out=ROOT/'artifacts/ra14/evaluation-2';out.mkdir(exist_ok=False)
 # Verify every inference payload before opening any evaluator-only reference.
 frozen={name:check_seal(runs/name) for name in ('known-noiseless','estimated-noiseless','estimated-noisy')}
 original=ROOT/'artifacts/ra14/original/generation';matched=ROOT/'artifacts/ra14/matched';generated=json.loads((matched/'complete.json').read_text())
 for n,d in generated['files'].items():assert digest(matched/n)==d['sha256']
 plan=json.loads((original/'private_truth/plan.json').read_text());cam=plan['camera'];gain=cam['gain_counts_per_e'];spacing=tuple(plan['geometry']['specimen_spacing_um_zyx']);source_spacing=(spacing[0],spacing[1]/2,spacing[2]/2);known=json.loads((matched/'reference/known-controls.json').read_text());x32=np.asarray(np.load(matched/'reference/represented_relative_source.npy',mmap_mode='r'));paired=np.asarray(np.load(matched/'reference/paired_electron_source.npy',mmap_mode='r'));pre_round=np.asarray(np.load(matched/'reference/pre_round_relative_source.npy',mmap_mode='r'));electron_matched=np.asarray(np.load(matched/'reference/generator_electron_source.npy',mmap_mode='r'))
 output={'status':'evaluated_frozen_results','producer_sha256':digest(Path(__file__)),'protocol_sha256':digest(ROOT/'artifacts/ra14/study/protocol.json'),'figure_plan_sha256':digest(ROOT/'artifacts/ra14/study/figure-plan.json'),'inference_seal_sha256':{n:digest(runs/n/'complete.json') for n in frozen},'original_generation_seal_sha256':digest(original/'generation.complete.json'),'matched_generation_seal_sha256':digest(matched/'complete.json'),'source_rounding':{'pre_round_to_float32':metric(x32,pre_round),'backconversion':metric((gain/generated['camera_contrast_counts'])*electron_matched,x32),'signed_mass_change_relative':math.fsum((x32.astype(np.float64)-pre_round).ravel()),'nonzero_coefficients_lost':int(np.count_nonzero((pre_round!=0)&(x32==0))),'axial_site_displacement_um':0.03125},'arms':{},'limits':['No source recovery/uncertainty/resolvability acceptance threshold adopted','Full-grid numerical budget not independently qualified; measured agreement descriptive','Known/noiseless and estimated/noiseless use pairedQ128; original noisy uses fineQ256; difference does not isolate noise','No matched conventional/photon-budget resolution control','Noisy fits diagnostic; finite iteration stops not convergence; procedural truth separation only']}
 for name,seal in frozen.items():
  folder=runs/name;native=json.loads((folder/'result.json').read_text());summary=seal['summary'];fit=native.get('specimen_fit');camera=native.get('camera_estimate');arm={'summary':summary,'result_json_sha256':digest(folder/'result.json'),'training_rms':native.get('handoff',{}).get('training_rms') if native.get('handoff') else None,'reason_code':native.get('reason_code'),'failure_code':native.get('failure_code',fit.get('failure_code') if fit else None),'message':native.get('message',fit.get('message') if fit else None),'fit_diagnostics':{k:fit.get(k) for k in ('status','stage','stop_reason','message','failure_code','failure_component')} if fit else None,'fit_metrics':None}
  if camera is not None:
   means=np.load(folder/camera['means_counts']['array_file'],allow_pickle=False);expected_means=np.array([cam['offset_counts'],cam['offset_counts']+gain*cam['background_e'],cam['offset_counts']+gain*(cam['background_e']+cam['flat_signal_e'])],dtype=np.float64);cg=camera['gain_counts_per_e'];arm['camera_summary']={'means_counts':means.tolist(),'contrast_counts':camera['contrast_counts'],'physical_gain_counts_per_e':cg,'means_error_counts':(means-expected_means).tolist(),'contrast_error_counts':camera['contrast_counts']-gain*cam['flat_signal_e'],'physical_gain_error_counts_per_e':cg-gain if cg is not None else None,'gain_unavailable_reason':'estimate_unavailable' if cg is None else None,'limit':'Descriptive comparison after freeze; no noise-confidence/instrument-accuracy criterion; physical gain not required for positivecontrast normalization.'}
  else:arm['camera_summary']=None
  if not summary['has_source']:
   assert not (folder/'source_relative.npy').exists() and not (folder/'predictions_relative.npy').exists();arm['unavailable_metrics']='no scored source/predictions in genuine frozen outcome';output['arms'][name]=arm;continue
  assert fit is not None and fit['source_relative'] is not None and fit['best_score'] is not None
  pred=np.asarray(np.load(folder/'predictions_relative.npy',mmap_mode='r'));source=np.asarray(np.load(folder/'source_relative.npy',mmap_mode='r'));b=fit['blank_counts'];d=fit['contrast_counts'];is_noisy=name=='estimated-noisy';refs=original/'private_truth' if is_noisy else matched/'reference';prepared=ROOT/'artifacts/ra14/prepared'/('noisy' if is_noisy else 'noiseless');raw=np.asarray(np.load(prepared/'specimen-counts.npy',mmap_mode='r'));means=np.stack([np.stack([np.load(refs/f'specimen_o{o}_p{p}_expected_signal_e.npy') for p in range(5)]) for o in range(3)]);signal=(gain/d)*means;corrected=(cam['offset_counts']+gain*(means+cam['background_e'])-b)/d;observed=(raw-b)/d;xref=(gain/d)*paired if is_noisy else x32
  if not is_noisy:assert d==generated['camera_contrast_counts']
  m={'source':metric(source,xref),'signal_predictions':metric(pred,signal),'corrected_mean_predictions':metric(pred,corrected),'observed_predictions':metric(pred,observed),'per_frame':[],'original_best_score':fit['best_score'],'original_initial_score':fit['initial_score'],'stopping_status':fit['status'],'stop_reason':fit['stop_reason'],'candidate_id':fit['best_score']['candidate_id'],'counts':fit['counts'],'attempt_trace':fit['attempt_trace'],'last_complete_gradient':fit['last_complete_gradient'],'source_reference':'original fine axial mass pair times actualgauge' if is_noisy else 'identical once-rounded float32 matched coefficient reference'};spectra=[]
  for o in range(3):
   for p in range(5):
    residual=pred[o,p]-observed[o,p];m['per_frame'].append({'orientation':o,'phase':p,'signal':metric(pred[o,p],signal[o,p]),'corrected_mean':metric(pred[o,p],corrected[o,p]),'observed':metric(pred[o,p],observed[o,p])});spectra.append({'orientation':o,'phase':p,'prediction':power_axes(pred[o,p],spacing),'signal_reference':power_axes(signal[o,p],spacing),'corrected_mean_reference':power_axes(corrected[o,p],spacing),'observed':power_axes(observed[o,p],spacing),'signed_observed_residual':power_axes(residual,spacing)})
  m['replay_data_objective']=.5*m['observed_predictions']['error_rms']**2;m['replay_penalty_objective']=.5*fit['regularization']*float(np.mean(source.astype(np.float64)**2));m['replay_total_objective']=m['replay_data_objective']+m['replay_penalty_objective'];m['camera_blank_counts']=b;m['camera_contrast_counts']=d
  dump(out/(name+'-profiles.json'),profiles(source,xref,source_spacing,plan['specimen_catalogue']));dump(out/(name+'-image-spectra.json'),spectra);dump(out/(name+'-source-spectra.json'),{'estimate':power_axes(source,source_spacing),'reference':power_axes(xref,source_spacing),'difference':power_axes(source.astype(np.float64)-xref,source_spacing)});arm['fit_metrics']=m;output['arms'][name]=arm
  del means,signal,corrected,observed,raw,pred,source,xref
 # Supplied-known forward diagnostic after every inference result was closed.
 reference_prediction=replay_source(x32,source_spacing_um_zyx=source_spacing,carriers_yx_per_um=np.array(known['carriers_yx_per_um'],dtype=np.float64),phases_at_specimen_origin_rad=np.array(known['phases_at_specimen_origin_rad'],dtype=np.float64),beam_amplitudes=np.array(known['beam_amplitudes'],dtype=np.float64),pupil_order=128);np.save(out/'known-source-forward-relative.npy',reference_prediction,allow_pickle=False)
 means=np.stack([np.stack([np.load(matched/'reference'/f'specimen_o{o}_p{p}_expected_signal_e.npy') for p in range(5)]) for o in range(3)]);d=generated['camera_contrast_counts'];b=generated['camera_means_counts'][1];signal=(gain/d)*means;raw=np.asarray(np.load(ROOT/'artifacts/ra14/prepared/noiseless/specimen-counts.npy',mmap_mode='r'));normalized=(raw-b)/d;output['matched_forward_diagnostic']={'metrics':metric(reference_prediction,signal),'per_frame':[{'orientation':o,'phase':p,'metrics':metric(reference_prediction[o,p],signal[o,p])} for o in range(3) for p in range(5)],'camera_sequential_roundoff':metric(normalized,signal),'limit':'Known supplied-source component comparison; not an observation-only arm, no independently qualified full-grid numerical bound'}
 from scripts.simulation_inverse_operator import build_kernel_cache
 cache=build_kernel_cache(source_shape_zyx=tuple(x32.shape),source_spacing_um_zyx=source_spacing,emission_um=.525,refractive_index=1.515,detection_na=1.4,pupil_order=128);lags=[0,16,31];selected=np.array(cache.lateral_spectra[lags],copy=True);np.save(out/'declared-cache-selected-lags.npy',selected,allow_pickle=False);dump(out/'declared-cache-representation.json',{'source_shape_zyx':list(x32.shape),'source_spacing_um_zyx':list(source_spacing),'selected_absolute_axial_lags':lags,'axial_lag_um':[i*source_spacing[0] for i in lags],'ky_cycles_per_um':np.fft.fftfreq(2*x32.shape[1],d=source_spacing[1]).tolist(),'kx_cycles_per_um':np.fft.rfftfreq(2*x32.shape[2],d=source_spacing[2]).tolist(),'dtype':selected.dtype.str,'units':'um^-2; unnormalized lateral DFT of finite computational embedding, no pixel-area factor','limits':'Actual signed native cache half-spectrum, not a continuous/global3D optical transfer function, recovered bandwidth or information analysis. Unused embedding values may affect this representation without changing retained finite interactions.'});del cache,selected
 baseline=ROOT/'docs/studies/full-noisy-study-2026-10-26/evidence/post-correction-full-evaluation.json';old=json.loads(baseline.read_text());output['historical_PR53_baseline']={'source_file':str(baseline.relative_to(ROOT)),'sha256':digest(baseline),'metrics':{k:old[k] for k in ('status','inference_status','source_metrics','signal_prediction_metrics','corrected_mean_prediction_metrics')},'limit':'Historical inference settings/model differ; retained baseline, not a fresh run or noise-only comparator'}
 output.update({'elapsed_seconds':time.monotonic()-start,'memory':peak(),'scientific_alignment':'not established','resolution_improvement':'not established','experiment_delivery':'all3frozenrealoutcomes evaluated; software checks/review remain separate'});dump(out/'evaluation.json',output);files={str(p.relative_to(out)):{'size_bytes':p.stat().st_size,'sha256':digest(p)} for p in out.rglob('*') if p.is_file()};dump(out/'complete.json',{'status':'closed_postfreeze_evaluation','files':files,'inference_seal_sha256':output['inference_seal_sha256']});print(json.dumps({'status':output['status'],'elapsed_seconds':output['elapsed_seconds'],'arms':{k:{'status':v['summary']['status'],'has_source':v['summary']['has_source'],'source_relative_l2':v['fit_metrics']['source']['relative_l2'] if v['fit_metrics'] else None} for k,v in output['arms'].items()},'matched_forward':output['matched_forward_diagnostic']['metrics']},indent=2))
if __name__=='__main__':main()
```

### render_second.py

SHA-256: `20b9fe2245859d80b823971b4edaabd7de30c3b129f0f11d833a8e77f872af08`.

```python
"""Physical-axis rendering of closed RA14 arrays; no inference or fitted scaling."""
from pathlib import Path
import json,hashlib,time,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];EVAL=ROOT/'artifacts/ra14/evaluation-2';OUT=ROOT/'artifacts/ra14/render-1';OUT.mkdir(exist_ok=False)
plt.rcParams.update({'font.size':10,'axes.titlesize':11,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report=json.loads((EVAL/'evaluation.json').read_text());plan=json.loads((ROOT/'docs/studies/full-noisy-study-2026-10-26/full-plan.json').read_text());g=plan['geometry'];spacing=np.array(g['specimen_spacing_um_zyx'],dtype=float);ss=spacing/np.array([1,2,2]);lengths=np.array(g['specimen_shape_zyx'])*spacing;catalogue=plan['specimen_catalogue'];records={};started=time.monotonic()
def save(fig,name,caption):
 path=OUT/(name+'.png');fig.savefig(path,dpi=150);plt.close(fig);records[name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'size_bytes':path.stat().st_size,'caption':caption}
def panels(reference,estimate,*,step,name,title,unit,caption):
 reference=np.asarray(reference,dtype=np.float64);estimate=np.asarray(estimate,dtype=np.float64);coords=[(np.arange(n)+.5)*d for n,d in zip(reference.shape,step)];centre=catalogue[0][:3];iz,iy,ix=[int(np.argmin(abs(v-c))) for v,c in zip(coords,centre)];get=[lambda a:np.max(a,axis=0),lambda a:np.max(a,axis=1),lambda a:a[iz],lambda a:a[:,iy,:]];rowlabels=['XY maximum over z','XZ maximum over y',f'XY section z={coords[0][iz]:.4f} µm',f'XZ section y={coords[1][iy]:.4f} µm'];extents=[(0,lengths[2],0,lengths[1]),(0,lengths[2],0,lengths[0])]*2;vmin=min(0.,float(np.min(reference)),float(np.min(estimate)));vmax=max(float(np.max(reference)),float(np.max(estimate)));vmax=vmax if vmax>0 else 1.;differences=[f(estimate)-f(reference) for f in get];dv=max(float(np.max(np.abs(a))) for a in differences);dv=dv if dv>0 else 1.;fig,axes=plt.subplots(4,3,figsize=(13,12),gridspec_kw={'height_ratios':[5,1,5,1]},layout='constrained')
 for row,f in enumerate(get):
  for col,a in enumerate((f(reference),f(estimate),differences[row])):
   ax=axes[row,col];im=ax.imshow(a,interpolation='nearest',origin='lower',extent=extents[row],aspect='equal',cmap='RdBu_r' if col==2 else 'viridis',vmin=-dv if col==2 else vmin,vmax=dv if col==2 else vmax);ax.set_xlabel('x (µm)');ax.set_ylabel(('y' if row%2==0 else 'z')+' (µm)');ax.set_title(rowlabels[row]+'\n'+('Reference','Finite fit','Fit − reference')[col])
 fig.colorbar(axes[0,0].images[0],ax=axes[:,:2].ravel().tolist(),shrink=.85,label=unit);fig.colorbar(axes[0,2].images[0],ax=axes[:,2].ravel().tolist(),shrink=.85,label=unit);fig.suptitle(title);save(fig,name,caption+f' First catalogue centre requested z/y/x={centre} µm. Actual fixed source/detector sections z={coords[0][iz]:.4f}, y={coords[1][iy]:.4f} µm; nearest native grid, no interpolation/registration. Shared linear amplitude scale{vmin:.8g}..{vmax:.8g}; signed differences ±{dv:.8g}. Projected differences subtract displayed projections. Equal physical aspect.')

# Stage/status evidence is separate from any source image or scientific success claim.
fig,ax=plt.subplots(figsize=(12,3.6),layout='constrained');ax.axis('off');rows=[]
for name,arm in report['arms'].items():
 s=arm['summary'];rows.append([name,s['status'],s['stage'],s['fit_stop_reason'] or 'not produced',f"{100*arm['fit_metrics']['source']['relative_l2']:.3f}%" if arm['fit_metrics'] and arm['fit_metrics']['source']['relative_l2'] is not None else 'unavailable'])
table=ax.table(cellText=rows,colLabels=['Arm','Native outcome','Stage','Finite fit stop','Relative source error'],loc='center',cellLoc='left',colLoc='left');table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,2.5);ax.set_title('Actual frozen outcomes; finite procedure completion is not scientific alignment');save(fig,'workflow-outcomes','Actual closed result labels. Known/noiseless supplies true illumination to the existing fitter; estimated arms call RA13 using only raw arrays/declared controls. Unavailable has no source/predictions. No convergence, recovery or resolution verdict follows from a finite stop.')

for name,arm in report['arms'].items():
 if not arm['summary']['has_source']:continue
 folder=ROOT/'artifacts/ra14/runs'/name;source=np.asarray(np.load(folder/'source_relative.npy',mmap_mode='r'));prediction=np.asarray(np.load(folder/'predictions_relative.npy',mmap_mode='r'));m=arm['fit_metrics'];d=m['camera_contrast_counts'];is_noisy=name=='estimated-noisy';paired=np.asarray(np.load(ROOT/'artifacts/ra14/matched/reference/paired_electron_source.npy',mmap_mode='r'));reference=(plan['camera']['gain_counts_per_e']/d)*paired if is_noisy else np.asarray(np.load(ROOT/'artifacts/ra14/matched/reference/represented_relative_source.npy',mmap_mode='r'));err=m['source']['relative_l2'];title=f'{name}: source, relative L2 error {100*err:.3f}% — {m["stop_reason"]}'
 panels(reference,source,step=ss,name=name+'-source-comparison',title=title,unit='Integrated relative weight',caption='Observed finite source estimate versus the declared paired-basis reference. Axial mass pairing shifts original fine sites by ±0.03125 µm; this is not the original continuous scene or an electron-density image.')
 refroot=ROOT/'artifacts/ra14/original/generation/private_truth' if is_noisy else ROOT/'artifacts/ra14/matched/reference';mu=np.load(refroot/'specimen_o0_p0_expected_signal_e.npy');signal=(plan['camera']['gain_counts_per_e']/d)*mu;panels(signal,prediction[0,0],step=spacing,name=name+'-prediction-comparison',title=name+': predeclared orientation0 / phase0 prediction',unit='Reference-flat-relative image',caption='Fixed exposure0/0, selected before inference. Prediction versus noiseless signal in the actual camera gauge; this is not an observed-noise residual. All15 observed/expected residual metrics and spectra are retained separately.')
 trace=m['attempt_trace'];scored=[x for x in trace if x['score'] is not None];fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
 for key,label in [('total_objective','Total'),('data_objective','Data'),('penalty_objective','Penalty')]:
  values=np.array([x['score'][key] for x in scored]);axes[0].plot([x['candidate_id'] for x in scored],np.where(values>0,values,np.nan),marker='.',label=label)
 accepted=[x for x in scored if x['outcome'] in ('initial_scored','accepted')];axes[0].scatter([x['candidate_id'] for x in accepted],[x['score']['total_objective'] for x in accepted],facecolors='none',edgecolors='black',label='Initial / accepted score')
 gradients=[x['gradient'] for x in trace if x['gradient_state']=='complete'];projected=[x for x in trace if x['projected_gradient_max_abs'] is not None]
 if gradients:axes[1].plot([x['candidate_id'] for x in gradients],np.where(np.array([x['max_abs'] for x in gradients])>0,[x['max_abs'] for x in gradients],np.nan),marker='.',label='Completed approximate gradient max')
 if projected:axes[1].plot([x['candidate_id'] for x in projected],np.where(np.array([x['projected_gradient_max_abs'] for x in projected])>0,[x['projected_gradient_max_abs'] for x in projected],np.nan),marker='.',label='Trial projected-gradient diagnostic')
 for ax in axes:ax.axvline(m['candidate_id'],color='.5',ls=':',label='Returned best candidate');ax.set(xlabel='Actual entered candidate ID',yscale='log');ax.legend(fontsize=8)
 axes[0].set_ylabel('Declared normalized objective');axes[1].set_ylabel('Stored finite gradient diagnostic');fig.suptitle(name+': '+str(m['stop_reason'])+'; finite trial history, convergence unestablished');save(fig,name+'-finite-trial-history','All completely scored candidates retain actual data/penalty/total values, including rejected trials. Rings mark the initial and accepted scores. Gradient points belong only to their own completed candidate; missing terminal gradients are not filled. Zero values are omitted only on log axes. Original trial/step/call/partial/stopping records remain in the native freeze. A hard stop or decreasing objective is not convergence or source recovery.')
 profiles=json.loads((EVAL/(name+'-profiles.json')).read_text());fig,axes=plt.subplots(4,3,figsize=(14,10),layout='constrained')
 for j,index in enumerate((0,10)):
  item=profiles[index]
  for axis,line in enumerate(item['lines']):
   x=np.array(line['coordinate_um']);ref=np.array(line['reference']);est=np.array(line['estimate']);upper=axes[2*j,axis];lower=axes[2*j+1,axis]
   upper.plot(x,ref,label='Reference',lw=1.5);upper.plot(x,est,label='Finite fit',lw=1.5);upper.axvline(item['requested_centre_um_zyx'][axis],color='.5',lw=.8,ls=':');upper.set(xlabel='zyx'[axis]+' (µm)',ylabel='Integrated relative weight',title=f'Catalogue object{index}, quantitative full line')
   for values,label in ((ref,'Reference / own full-line peak'),(est,'Fit / own full-line peak')):
    peak=float(np.max(np.abs(values)))
    if peak>0:lower.plot(x,values/peak,label=label,lw=1.5)
    else:lower.text(.02,.9,label+': unavailable (zero line)',transform=lower.transAxes,fontsize=8)
   centre=item['requested_centre_um_zyx'][axis];lower.set(xlim=(max(0,centre-.6),min(lengths[axis],centre+.6)),xlabel='zyx'[axis]+' (µm)',ylabel='Own-peak shape only',title='Fixed ±0.6 µm display window');lower.axvline(centre,color='.5',lw=.8,ls=':')
 axes[0,0].legend(fontsize=8);axes[1,0].legend(fontsize=8);fig.suptitle(name+': fixed catalogue-centre profiles; shape normalization is not amplitude recovery');save(fig,name+'-fixed-profiles','Predeclared catalogue indices0 and10. Quantitative top rows retain full native lines and actual integrated weights. Shape rows divide each complete line by its own absolute peak, with a fixed ±0.6 µm display window; zero lines have no normalized curve. Nearest fixed grid planes, no fitted peak, interpolation or registration. All27 native profile triples and exact selected plane coordinates are retained in the closed JSON.')
 per=m['per_frame'];mean=np.array([x['observed']['error_mean'] for x in per]).reshape(3,5);rms=np.array([x['observed']['error_rms'] for x in per]).reshape(3,5);fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained');v=float(np.max(np.abs(mean)));v=v if v else 1.
 for ax,data,label in zip(axes,(mean,rms),('Signed mean observed residual','Observed residual RMS')):
  im=ax.imshow(data,interpolation='nearest',origin='lower',aspect='auto',cmap='RdBu_r' if data is mean else 'viridis',vmin=-v if data is mean else 0,vmax=v if data is mean else None);ax.set(xlabel='Phase index',ylabel='Orientation index',title=label);ax.set_xticks(range(5));ax.set_yticks(range(3));fig.colorbar(im,ax=ax,label='Relative image units')
 fig.suptitle(name+': all15 complete-frame training residuals');save(fig,name+'-all15-residuals','Each cell uses all32×256×256 voxels of its exposure, prediction minus signed camera-normalized observed counts. These are training residuals, not held-out validation or a source-recovery criterion.')
 spectra=json.loads((EVAL/(name+'-image-spectra.json')).read_text());fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
 for axis,ax in enumerate(axes):
  for key,label in [('signal_reference','Noiseless signal'),('prediction','Prediction'),('signed_observed_residual','Observed residual')]:
   power=sum((np.array(v[key]['axis_power_sums'][axis]) for v in spectra));frequency=np.array(spectra[0][key]['frequency_cycles_per_um'][axis]);ix=np.argsort(frequency);ax.plot(frequency[ix],np.where(power[ix]>0,power[ix],np.nan),label=label)
  ax.set(xlabel='zyx'[axis]+' frequency (cycles/µm)',ylabel='Sum of unitary Fourier power',yscale='log',title='All15 exposures, full-frame power')
 axes[0].legend(fontsize=8);fig.suptitle(name+': descriptive image/residual spectra; no recovered-bandwidth or resolution claim');save(fig,name+'-image-spectra','Untapered full3D DFT with norm=ortho, summed over the other two frequency axes and all15 exposures. Power retains relative-image squared units. Zero power is not drawn on the log axis. No fitted scaling, source-spectrum division, optical transfer or observable-mode inference.')
 source_spectra=json.loads((EVAL/(name+'-source-spectra.json')).read_text());fig,axes=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
 for axis,ax in enumerate(axes):
  for key,label in [('reference','Paired-basis reference'),('estimate','Finite source'),('difference','Source difference')]:
   record=source_spectra[key];frequency=np.array(record['frequency_cycles_per_um'][axis]);power=np.array(record['axis_power_sums'][axis]);ix=np.argsort(frequency);ax.plot(frequency[ix],np.where(power[ix]>0,power[ix],np.nan),label=label)
  ax.set(xlabel='zyx'[axis]+' frequency (cycles/µm)',ylabel='Sum of unitary coefficient power',yscale='log',title='Complete paired source basis')
 axes[0].legend(fontsize=8);fig.suptitle(name+': descriptive source-basis Fourier power; observable modes unestablished');save(fig,name+'-source-spectra','Untapered unitary full3D source-coefficient DFT, other-axis power sums. Integrated-relative-weight squared units, native paired basis. Difference power is the DFT of the signed coefficient difference. Zero power is not drawn on the log axis. These are not optical transfer, observable-subspace recovery, resolvability or a physical-resolution criterion.')
 del source,prediction,reference,paired

cache=np.load(EVAL/'declared-cache-selected-lags.npy');meta=json.loads((EVAL/'declared-cache-representation.json').read_text());fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
for values,lag in zip(cache,meta['axial_lag_um']):ax.plot(meta['kx_cycles_per_um'],values[0],label=f'|axial lag|={lag:g} µm')
ax.set(xlabel='Computational x frequency (cycles/µm), ky=0',ylabel='Signed cache coefficient (µm⁻²)',title='Declared Q128 finite cache representation — not an optical transfer function');ax.legend();save(fig,'declared-cache-representation',meta['limits']+' '+meta['units']+'. Fixed absolute lag indices0,16,31 and native ky=0. These computational-embedding coefficients are not measured/recovered bandwidth or a scalar global3D OTF.')
manifest={'status':'rendered_closed_evidence','producer_sha256':sha(Path(__file__)),'evaluation_seal_sha256':sha(EVAL/'complete.json'),'figure_plan_sha256':sha(ROOT/'artifacts/ra14/study/figure-plan.json'),'numpy':np.__version__,'matplotlib':matplotlib.__version__,'elapsed_seconds':time.monotonic()-started,'figures':records,'limits':'Rendering only; no inference/evaluation output mutation or recovery/resolution certification. All per-arm arrays remain native grids; no image registration or brightness fit.'};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'figure_count':len(records),'elapsed_seconds':manifest['elapsed_seconds'],'names':list(records)},indent=2))
```

## Independent post-freeze observer

This supplemental direct-array observer imports no project numerical implementation and performs no fitting, optics or FFT. It checks arithmetic consistency and cannot provide a full-grid optical oracle or recovery criterion. Run serially after the four seals close: `.venv/bin/python artifacts/ra14/advice/independent_reductions.py --run --evaluation evaluation-2`.

```python
"""Read-only, post-freeze descriptive reductions. Run only when explicitly authorized.

No project/evaluator/metric/optics/fitter imports. This is advice, not a product
test or formal scientific verdict. The input seals must all exist before work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ARMS = ("known-noiseless", "estimated-noiseless", "estimated-noisy")
CHUNK = 262144
EPS = float(np.finfo(np.float64).eps)
TINY = float(np.nextafter(np.float64(0), np.float64(1)))


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return np.load(path, mmap_mode="r", allow_pickle=False)


def envelope(scale, count):
    """Conservative arithmetic comparison envelope, not a recovery criterion.

    gamma_(n+32) bounds a serial floating reduction; 64 covers subtraction,
    squaring, division/sqrt and comparing two reduction paths. This intentionally
    uses float64 epsilon even if longdouble supplies wider observer arithmetic.
    An explicit subnormal term replaces an arbitrary absolute-error floor.
    """
    k = int(count) + 32
    u = k * EPS
    return 64 * (u / (1 - u)) * abs(float(scale)) + 64 * k * TINY


def numeric(actual, expected, scale=None, count=1):
    if actual is None or expected is None:
        return {"reported": actual, "independent": expected,
                "same_availability": actual is None and expected is None}
    actual, expected = float(actual), float(expected)
    scale = max(abs(actual), abs(expected)) if scale is None else float(scale)
    delta = actual - expected
    allowance = envelope(scale, count)
    return {"reported": actual, "independent": expected, "difference": delta,
            "arithmetic_envelope": allowance,
            "within_arithmetic_envelope": abs(delta) <= allowance}


def chunks(*arrays):
    views = [np.asarray(a).reshape(-1) for a in arrays]
    if not all(v.size == views[0].size for v in views):
        raise ValueError("independent arrays have different element counts")
    for start in range(0, views[0].size, CHUNK):
        yield tuple(v[start:start + CHUNK] for v in views)


def norm_block(x):
    x = np.asarray(x, dtype=np.longdouble)
    maximum = np.max(np.abs(x), initial=np.longdouble(0))
    if maximum == 0:
        return 0.0
    return float(maximum * np.sqrt(np.sum((x / maximum) ** 2, dtype=np.longdouble)))


def reduce_pairs(blocks):
    count = 0
    errors, refs, sums, abs_sums = [], [], [], []
    maximum = 0.0
    for a, b in blocks:
        a, b = np.asarray(a, dtype=np.longdouble), np.asarray(b, dtype=np.longdouble)
        error = a - b
        count += a.size
        errors.append(norm_block(error))
        refs.append(norm_block(b))
        sums.append(float(np.sum(error, dtype=np.longdouble)))
        abs_sums.append(float(np.sum(np.abs(error), dtype=np.longdouble)))
        maximum = max(maximum, float(np.max(np.abs(error), initial=np.longdouble(0))))
    error_l2, reference_l2 = math.hypot(*errors), math.hypot(*refs)
    return {"count": count, "reference_l2": reference_l2, "error_l2": error_l2,
            "relative_l2": error_l2 / reference_l2 if reference_l2 else None,
            "error_rms": error_l2 / math.sqrt(count), "error_max_abs": maximum,
            "error_mean": math.fsum(sums) / count,
            "error_abs_sum": math.fsum(abs_sums)}


def metric(a, b):
    if np.shape(a) != np.shape(b):
        raise ValueError("independent metric shape mismatch")
    return reduce_pairs(chunks(a, b))


def combine(rows):
    n = sum(r["count"] for r in rows)
    error = math.hypot(*(r["error_l2"] for r in rows))
    reference = math.hypot(*(r["reference_l2"] for r in rows))
    return {"count": n, "reference_l2": reference, "error_l2": error,
            "relative_l2": error / reference if reference else None,
            "error_rms": error / math.sqrt(n),
            "error_max_abs": max(r["error_max_abs"] for r in rows),
            "error_mean": math.fsum(r["error_mean"] * r["count"] for r in rows) / n,
            "error_abs_sum": math.fsum(r["error_abs_sum"] for r in rows)}


def compare_metric(reported, independent):
    n = independent["count"]
    scale = independent["reference_l2"] + independent["error_l2"]
    answer = {"count_reported": reported["count"], "count_independent": n,
              "same_count": reported["count"] == n}
    for key in ("reference_l2", "error_l2", "relative_l2", "error_rms",
                "error_max_abs", "error_mean"):
        local = scale
        if key in ("error_rms", "error_mean"):
            local /= math.sqrt(n)
        elif key == "relative_l2":
            local = scale / independent["reference_l2"] if independent["reference_l2"] else 0
        answer[key] = numeric(reported[key], independent[key], local, n)
    return answer


def energy(array):
    norms = [norm_block(block[0]) for block in chunks(array)]
    return math.fsum(n * n for n in norms)


def check_spectrum(record, array, spacing):
    squared = energy(array)
    shape = array.shape
    axes = []
    for axis, (n, step) in enumerate(zip(shape, spacing)):
        # Integer signed-index construction, independently of numpy.fftfreq.
        expected = np.array([(k if k <= (n - 1) // 2 else k - n) / (n * step)
                             for k in range(n)], dtype=np.float64)
        given = np.asarray(record["frequency_cycles_per_um"][axis])
        axes.append({"axis": axis, "frequency_length": len(given),
                     "frequency_error": metric(given, expected),
                     "power_sum": numeric(math.fsum(record["axis_power_sums"][axis]),
                                          squared, squared, array.size)})
    return {"spatial_energy": numeric(record["spatial_squared_norm"], squared, squared, array.size),
            "spectral_energy": numeric(record["spectral_squared_norm"], squared, squared, array.size),
            "axes": axes}


def verify_seal(folder):
    path = folder / "complete.json"
    seal = read(path)
    mismatches = []
    for relative, expected in seal["files"].items():
        candidate = folder / relative
        if not candidate.is_file():
            mismatches.append({"path": relative, "reason": "missing"})
        elif (candidate.stat().st_size != expected["size_bytes"]
              or digest(candidate) != expected["sha256"]):
            mismatches.append({"path": relative, "reason": "size_or_digest"})
    if mismatches:
        raise ValueError(f"Seal mismatch in {folder}: {mismatches}")
    return seal, {"path": str(path), "sha256": digest(path), "verified_payloads": len(seal["files"])}


def source_rounding(root, generated, reported):
    ref = root / "matched/reference"
    fine = load(root / "original/generation/private_truth/specimen_source_e.npy")
    paired = load(ref / "paired_electron_source.npy")
    pre = load(ref / "pre_round_relative_source.npy")
    x32 = load(ref / "represented_relative_source.npy")
    electron = load(ref / "generator_electron_source.npy")
    g = read(root / "original/generation/private_truth/plan.json")["camera"]["gain_counts_per_e"]
    d = generated["camera_contrast_counts"]
    equations = {"axial_pair": 0, "pre_round_gauge": 0, "float32_rounding": 0, "backconversion": 0}
    for z in range(paired.shape[0]):
        expected_pair = np.add(fine[2*z], fine[2*z+1], dtype=np.float64)
        equations["axial_pair"] += int(np.count_nonzero(paired[z] != expected_pair))
        expected_pre = np.multiply(g / d, paired[z], dtype=np.float64)
        equations["pre_round_gauge"] += int(np.count_nonzero(pre[z] != expected_pre))
        equations["float32_rounding"] += int(np.count_nonzero(x32[z] != expected_pre.astype(np.float32)))
        expected_e = np.multiply(d / g, np.asarray(x32[z], dtype=np.float64), dtype=np.float64)
        equations["backconversion"] += int(np.count_nonzero(electron[z] != expected_e))
    independent = metric(x32, pre)
    lost = sum(int(np.count_nonzero((b != 0) & (a == 0))) for a, b in chunks(x32, pre))
    back = reduce_pairs(((g/d) * np.asarray(e, dtype=np.float64), x) for e, x in chunks(electron, x32))
    return {"prescribed_equation_mismatch_counts": equations,
            "rounding_metrics": compare_metric(reported["pre_round_to_float32"], independent),
            "backconversion_metrics": compare_metric(reported["backconversion"], back),
            "mass_change": numeric(reported["signed_mass_change_relative"],
                                   independent["error_mean"] * independent["count"],
                                   independent["error_abs_sum"], independent["count"]),
            "lost_reported": reported["nonzero_coefficients_lost"], "lost_independent": lost,
            "axial_site_displacement_um": 0.125 / 4}


def profile_check(records, source, reference, spacing, origin, catalogue, figure_plan):
    findings = []
    coordinates = [origin[i] + (np.arange(n) + 0.5) * spacing[i] for i, n in enumerate(source.shape)]
    for row, obj in enumerate(catalogue):
        record = records[row]
        indices = [min(range(len(c)), key=lambda j: (abs(float(c[j]) - obj[i]), j))
                   for i, c in enumerate(coordinates)]
        lines = []
        for axis in range(3):
            selector = list(indices)
            selector[axis] = slice(None)
            key = tuple(selector)
            line = record["lines"][axis]
            estimate, truth = np.asarray(source[key]), np.asarray(reference[key])
            lines.append({"axis": axis,
                          "coordinate_error": metric(np.array(line["coordinate_um"]), coordinates[axis]),
                          "estimate_error": metric(np.array(line["estimate"]), estimate),
                          "reference_error": metric(np.array(line["reference"]), truth),
                          "estimate_full_line_peak": float(np.max(estimate)),
                          "reference_full_line_peak": float(np.max(truth)),
                          "shape_window_um": [obj[axis] - figure_plan["profile_shape_display_window_half_width_um"],
                                              obj[axis] + figure_plan["profile_shape_display_window_half_width_um"]]})
        findings.append({"catalogue_index": row, "reported_indices": record["actual_indices_zyx"],
                         "independent_indices": indices,
                         "independent_centres": [float(c[j]) for c, j in zip(coordinates, indices)],
                         "lines": lines})
    return {"expected_catalogue_count": len(catalogue), "reported_count": len(records), "rows": findings,
            "rendering_limit": "Checks saved quantitative profile values and intended normalization denominators. PNG colors, displayed windows and projection-difference rendering require a later visual/data check; no render inspected here."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Explicitly start authorized post-freeze reductions")
    parser.add_argument("--evaluation", default="evaluation-1")
    parser.add_argument("--output", default="independent-reductions-1.json")
    args = parser.parse_args()
    if not args.run:
        parser.error("No work performed: --run requires coordinator authorization")
    root = ROOT / "artifacts/ra14"
    evaluation_dir = root / args.evaluation
    folders = [root / "runs" / name for name in ARMS] + [evaluation_dir]
    missing = [str(f / "complete.json") for f in folders if not (f / "complete.json").is_file()]
    if missing:
        raise SystemExit("No reductions started; missing required seals: " + repr(missing))
    output = Path(__file__).parent / args.output
    if output.exists():
        raise SystemExit("Refusing to overwrite existing advisory report")
    started = time.monotonic()
    seals, identities = {}, []
    for name, folder in zip((*ARMS, "evaluation"), folders):
        seals[name], identity = verify_seal(folder)
        identities.append(identity)
    generated, identity = verify_seal(root / "matched")
    identities.append(identity)
    # Bind original read inputs to the published full-case per-file inventory.
    inventory = read(ROOT / "docs/studies/full-noisy-study-2026-10-26/evidence/closed-protocol-file-inventory.json")
    original_verified = 0
    for key, item in inventory["cases"]["full"]["files"].items():
        if key.startswith("generation/"):
            path = root / "original" / key
            if path.stat().st_size != item["size_bytes"] or digest(path) != item["sha256"]:
                raise ValueError("Original public inventory mismatch: " + key)
            original_verified += 1
    evaluation = read(evaluation_dir / "evaluation.json")
    plan = read(root / "original/generation/private_truth/plan.json")
    protocol = read(root / "study/protocol.json")
    figure_plan = read(root / "study/figure-plan.json")
    spacing = tuple(plan["geometry"]["specimen_spacing_um_zyx"])
    ss = (spacing[0], spacing[1]/2, spacing[2]/2)
    cam = plan["camera"]
    gain, background, offset = cam["gain_counts_per_e"], cam["background_e"], cam["offset_counts"]
    paired = load(root / "matched/reference/paired_electron_source.npy")
    x32 = load(root / "matched/reference/represented_relative_source.npy")
    report = {"purpose": "Independent descriptive post-freeze reductions; no formal acceptance verdict",
              "checker_sha256": digest(__file__), "seals": identities,
              "original_generation_files_verified": original_verified,
              "protocol_sha256": digest(root / "study/protocol.json"),
              "figure_plan_sha256": digest(root / "study/figure-plan.json"),
              "observer": {"python": sys.version, "numpy": np.__version__, "chunk_elements": CHUNK,
                           "float64_epsilon": EPS, "longdouble_epsilon": float(np.finfo(np.longdouble).eps),
                           "method": "longdouble block subtraction/scaled norms; math.hypot combination; math.fsum signed totals; no production numerical imports",
                           "envelope": "64*gamma_(n+32)(float64_epsilon)*arithmetic_scale + 64*(n+32)*smallest_float64_subnormal; conservative comparison-path allowance, not a recovery target"},
              "source_pairing_and_rounding": source_rounding(root, generated, evaluation["source_rounding"]),
              "arms": {}, "limits": ["No fitter/optics replay or Fourier recomputation", "No full-grid optical oracle or source-recovery criterion", "No statistical confidence or resolution verdict", "Rendered image review remains separate"]}
    for name in ARMS:
        folder = root / "runs" / name
        native = read(folder / "result.json")
        frozen = seals[name]["summary"]
        supplied = evaluation["arms"][name]
        fit, camera = native.get("specimen_fit"), native.get("camera_estimate")
        arm = {"frozen_status": frozen["status"], "evaluation_status": supplied["summary"]["status"],
               "same_status": supplied["summary"]["status"] == frozen["status"],
               "has_source": frozen["has_source"], "frozen_candidate_id": frozen.get("candidate_id")}
        if not frozen["has_source"]:
            arm["unavailability"] = {"source_file_absent": not (folder / "source_relative.npy").exists(),
                                     "prediction_file_absent": not (folder / "predictions_relative.npy").exists(),
                                     "fit_metrics_absent": supplied["fit_metrics"] is None,
                                     "spectra_file_absent": not (evaluation_dir / (name + "-image-spectra.json")).exists(),
                                     "reason_code_native": native.get("reason_code"),
                                     "reason_code_reported": supplied.get("reason_code")}
            report["arms"][name] = arm
            continue
        source = load(folder / "source_relative.npy")
        prediction = load(folder / "predictions_relative.npy")
        noisy = name == "estimated-noisy"
        prepared = root / "prepared" / ("noisy" if noisy else "noiseless")
        raw = load(prepared / "specimen-counts.npy")
        means_root = root / "original/generation/private_truth" if noisy else root / "matched/reference"
        b, d = fit["blank_counts"], fit["contrast_counts"]
        reference = (gain/d) * np.asarray(paired) if noisy else x32
        stored = supplied["fit_metrics"]
        camera_means = load(folder / camera["means_counts"]["array_file"])
        arm["gauge"] = {"fit_blank_vs_camera": numeric(b, camera_means[1]),
                        "fit_contrast_vs_camera": numeric(d, camera["contrast_counts"]),
                        "positive_contrast": d > 0, "physical_gain": camera["gain_counts_per_e"],
                        "source_reference": "actual noisy gauge times original paired electron mass" if noisy else "once-rounded matched relative coefficients",
                        "matched_generation_contrast_difference": d - generated["camera_contrast_counts"] if not noisy else None}
        arm["source_metric"] = compare_metric(stored["source"], metric(source, reference))
        rows = {"signal": [], "corrected_mean": [], "observed": []}
        frame_checks, spectra_checks = [], []
        spectra = read(evaluation_dir / (name + "-image-spectra.json"))
        seen = [(r["orientation"], r["phase"]) for r in stored["per_frame"]]
        arm["frame_inventory"] = {"reported_pairs": seen,
                                  "exact_orientation_major_15": seen == [(o,p) for o in range(3) for p in range(5)],
                                  "spectra_pairs": [(r["orientation"], r["phase"]) for r in spectra],
                                  "spectra_exact_orientation_major_15": [(r["orientation"], r["phase"]) for r in spectra] == [(o,p) for o in range(3) for p in range(5)],
                                  "prediction_shape": list(prediction.shape), "raw_shape": list(raw.shape)}
        for o in range(3):
            for p in range(5):
                index = 5*o+p
                mu = load(means_root / f"specimen_o{o}_p{p}_expected_signal_e.npy")
                signal = (gain/d) * mu
                corrected = (offset + gain * (mu + background) - b) / d
                observed = (raw[o,p] - b) / d
                residual = prediction[o,p] - observed
                items = {"signal": signal, "corrected_mean": corrected, "observed": observed}
                check = {"orientation": o, "phase": p}
                for key, values in items.items():
                    independent = metric(prediction[o,p], values)
                    rows[key].append(independent)
                    check[key] = compare_metric(stored["per_frame"][index][key], independent)
                constant = (offset + gain * background - b) / d
                shift = corrected - signal
                check["corrected_minus_signal_constant"] = {
                    "independent_algebraic_constant": constant,
                    "min": float(np.min(shift)), "max": float(np.max(shift)),
                    "maximum_deviation": float(np.max(np.abs(shift-constant))),
                    "arithmetic_envelope": envelope(float(np.max(np.abs(corrected))) + float(np.max(np.abs(signal))) + abs(constant), 32)}
                frame_checks.append(check)
                spectra_checks.append({"orientation": o, "phase": p,
                    **{label: check_spectrum(spectra[index][label], array, spacing)
                       for label, array in {"prediction": prediction[o,p], "signal_reference": signal,
                                            "corrected_mean_reference": corrected, "observed": observed,
                                            "signed_observed_residual": residual}.items()}})
        arm["per_frame_metrics"] = frame_checks
        arm["spectral_energy_and_frequency"] = spectra_checks
        aggregates = {key: combine(values) for key, values in rows.items()}
        arm["aggregate_metrics"] = {key: compare_metric(stored[key+"_predictions"], result)
                                     for key, result in aggregates.items()}
        data_objective = aggregates["observed"]["error_l2"]**2 / (2*aggregates["observed"]["count"])
        penalty = fit["regularization"] * energy(source) / (2*source.size)
        objective = data_objective + penalty
        arm["objectives"] = {"M": aggregates["observed"]["count"], "N": int(source.size),
                             "expected_full_counts": aggregates["observed"]["count"] == 31457280 and source.size == 8388608,
                             "data": numeric(stored["replay_data_objective"], data_objective, data_objective, raw.size),
                             "penalty": numeric(stored["replay_penalty_objective"], penalty, penalty, source.size),
                             "total": numeric(stored["replay_total_objective"], objective, objective, raw.size+source.size),
                             "frozen_best_score": fit["best_score"],
                             "reported_candidate_id": stored["candidate_id"],
                             "candidate_id_matches": stored["candidate_id"] == frozen.get("candidate_id"),
                             "independent_total": objective}
        score = fit["best_score"]
        arm["objectives"]["frozen_data_comparison"] = numeric(score["data_objective"], data_objective, data_objective, raw.size)
        arm["objectives"]["frozen_penalty_comparison"] = numeric(score["penalty_objective"], penalty, penalty, source.size)
        arm["objectives"]["frozen_total_comparison"] = numeric(score["total_objective"], objective, objective, raw.size+source.size)
        arm["profiles"] = profile_check(read(evaluation_dir / (name+"-profiles.json")), source, reference,
                                          ss, plan["geometry"]["specimen_origin_um_zyx"], plan["specimen_catalogue"], figure_plan)
        source_spectra = read(evaluation_dir / (name+"-source-spectra.json"))
        arm["source_spectral_energy"] = {label: check_spectrum(source_spectra[label], array, ss)
                                           for label, array in {"estimate": source, "reference": reference,
                                                                "difference": source.astype(np.float64)-reference}.items()}
        report["arms"][name] = arm
        print(f"Independent array reductions complete: {name}", flush=True)
    # Reduce the existing sealed known-source forward diagnostic, never replay it.
    matched_prediction = load(evaluation_dir / "known-source-forward-relative.npy")
    matched_raw = load(root / "prepared/noiseless/specimen-counts.npy")
    matched_metrics, camera_metrics, forward_rows = [], [], []
    forward_record = evaluation["matched_forward_diagnostic"]
    d, b = generated["camera_contrast_counts"], generated["camera_means_counts"][1]
    for o in range(3):
        for p in range(5):
            mu = load(root / "matched/reference" / f"specimen_o{o}_p{p}_expected_signal_e.npy")
            signal = (gain/d) * mu
            observed = (matched_raw[o,p] - b) / d
            computed = metric(matched_prediction[o,p], signal)
            matched_metrics.append(computed)
            camera_metrics.append(metric(observed, signal))
            forward_rows.append({"orientation": o, "phase": p,
                                 "metrics": compare_metric(forward_record["per_frame"][5*o+p]["metrics"], computed)})
    report["matched_forward_record_reduction"] = {
        "aggregate": compare_metric(forward_record["metrics"], combine(matched_metrics)),
        "per_frame": forward_rows,
        "camera_roundoff": compare_metric(forward_record["camera_sequential_roundoff"], combine(camera_metrics)),
        "limit": "Only sealed arrays reduced; no independent full-grid optical accuracy claim"}
    # Ensure the required seal identities were not replaced during the observer.
    for identity in identities:
        if digest(identity["path"]) != identity["sha256"]:
            raise ValueError("Seal changed during observer: " + identity["path"])
    report["elapsed_seconds"] = time.monotonic() - started
    report["criteria"] = protocol["criteria"]
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(str(output), flush=True)


if __name__ == "__main__":
    main()
```
