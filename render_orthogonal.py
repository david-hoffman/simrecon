"""Observed XY/XZ maximum-intensity projections and predetermined bead-center sections."""
import argparse
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--inputs', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
meta = json.loads((args.inputs/'orthogonal-input-provenance.json').read_text())
data = np.load(args.inputs/'orthogonal-views.npz', allow_pickle=False)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,
    'figure.facecolor':'white','savefig.facecolor':'white','axes.spines.top':False,
    'axes.spines.right':False,'pdf.fonttype':42})
outputs = {}
display = {}
def save(fig, name):
    for ext in ['png','pdf']:
        p=args.out/(name+'.'+ext)
        fig.savefig(p,dpi=150,bbox_inches='tight',metadata={'Title':name})
        outputs[p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size}
    plt.close(fig)

def draw(ax,a,extent,limits,title,units,cmap='cividis',colorbar=True):
    im=ax.imshow(a,origin='lower',extent=extent,vmin=limits[0],vmax=limits[1],
        cmap=cmap,interpolation='nearest',aspect='equal')
    ax.set_title(title)
    ax.set_xlabel('Local x (µm)')
    ax.set_ylabel('Local '+('z' if 'XZ' in title else 'y')+' (µm)')
    if colorbar:
        ax.figure.colorbar(im,ax=ax,pad=.025,shrink=.82,label=units)
    return im

# Every recorded exposure is shown; all depths/rows enter their maxima.
raw_keys=[f'specimen_o{o}_p{p}' for o in range(3) for p in range(5)]
limits=[min(meta['whole_volume_ranges'][k][0] for k in raw_keys),max(meta['whole_volume_ranges'][k][1] for k in raw_keys)]
fig,axs=plt.subplots(6,5,figsize=(13.8,10.9),layout='constrained',gridspec_kw={'height_ratios':[1,.28]*3})
for o in range(3):
    for p in range(5):
        key=f'specimen_o{o}_p{p}'
        for q,plane in enumerate(['xy','xz']):
            ax=axs[2*o+q,p]
            im=ax.imshow(data[key+'_'+plane+'_mip'],origin='lower',extent=(0,20.48,0,20.48 if plane=='xy' else 4),
                vmin=limits[0],vmax=limits[1],interpolation='nearest',cmap='cividis',aspect='equal')
            ax.set_xticks([0,10,20])
            ax.set_yticks([0,10,20] if plane=='xy' else [0,2,4])
            if p==0:ax.set_ylabel(f'O{o+1} {plane.upper()}\n'+('y' if plane=='xy' else 'z')+' (µm)')
            else:ax.tick_params(labelleft=False)
            if q==0:ax.set_title(f'Exposure {p+1}');ax.tick_params(labelbottom=False)
            else:ax.set_xlabel('x (µm)')
fig.colorbar(im,ax=axs,shrink=.83,pad=.015,label='Raw detector counts · common linear scale for all 30 panels')
fig.suptitle('1  All 15 recorded exposures: XY and XZ maximum-intensity projections\nXY = max over z; XZ = max over y · physical aspect preserved · full 20.48 × 20.48 × 4 µm box',fontsize=13)
save(fig,'01-noisy-orthogonal-mips')
display['01-noisy-orthogonal-mips']={'linear_scale_counts':limits,'interpolation':'nearest','aspect':'equal physical units','all15_exposures':True}

# Corrected maxima are the same positive affine transform of the raw maxima.
raw0='specimen_o0_p0'
raw_limits=meta['whole_volume_ranges'][raw0]
corr_limits=[(x-meta['camera_blank'])/meta['camera_contrast'] for x in raw_limits]
fig,axs=plt.subplots(2,2,figsize=(11.2,8.1),layout='constrained',gridspec_kw={'height_ratios':[1,.26]})
for row,plane in enumerate(['xy','xz']):
    extent=(0,20.48,0,20.48 if plane=='xy' else 4)
    left_im=draw(axs[row,0],data[raw0+'_'+plane+'_mip'],extent,raw_limits,plane.upper()+' · raw counts','Detector counts',colorbar=False)
    right_im=draw(axs[row,1],data['corrected_'+plane+'_mip'],extent,corr_limits,plane.upper()+' · camera-corrected','Relative image units',colorbar=False)
fig.colorbar(left_im,ax=axs[:,0],pad=.025,shrink=.85,label='Detector counts')
fig.colorbar(right_im,ax=axs[:,1],pad=.025,shrink=.85,label='Relative image units')
fig.suptitle('2  Camera correction of the same frozen exposure: orthogonal MIPs\n(counts − 20.1973062) / 1700.0256947 · same affine color mapping; normalization does not deblur',fontsize=12)
save(fig,'02-camera-orthogonal-mips')
display['02-camera-orthogonal-mips']={'raw_linear_scale':raw_limits,'corrected_linear_scale':corr_limits,'same_affine_mapping':True,'example_orientation_index':0,'example_exposure_index':0}

def compare(name,left,right,title,unit,kind,profiles=False):
    choice=meta['choices'][left]
    shape=choice['shape_zyx'];spacing=choice['spacing_um_zyx']
    selected=['xy','xz']
    pair=[];extents=[]
    for plane in selected:
        pair.append((data[f'{left}_{plane}_{kind}'],data[f'{right}_{plane}_{kind}']))
        if kind=='mip':
            extents.append([0,shape[2]*spacing[2],0,shape[1 if plane=='xy' else 0]*spacing[1 if plane=='xy' else 0]])
        else:extents.append(choice[plane+'_slice_extent_um'])
    low=min(meta['whole_volume_ranges'][left][0],meta['whole_volume_ranges'][right][0])
    high=max(meta['whole_volume_ranges'][left][1],meta['whole_volume_ranges'][right][1])
    diff=max(float(np.max(np.abs(b-a))) for a,b in pair)
    ratios=[(e[3]-e[2])/(e[1]-e[0]) for e in extents]
    ratios=[x/max(ratios) for x in ratios]
    rows=3 if profiles else 2
    gs={'height_ratios':ratios+([.7] if profiles else [])}
    fig=plt.figure(figsize=(13.2,9.8 if profiles else 7.5),layout='constrained')
    grid=fig.add_gridspec(rows,3,**gs)
    image_axes=[[],[],[]]
    image_handles=[None,None,None]
    for row,plane in enumerate(selected):
        a,b=pair[row];e=extents[row]
        label=plane.upper()+' '+('MIP' if kind=='mip' else 'section')
        for col,(arr,cmap,lim,head) in enumerate([(a,'magma' if left.startswith('source') else 'cividis',[low,high],'Reference' if left.startswith('source') else 'Corrected observation'),(b,'magma' if left.startswith('source') else 'cividis',[low,high],'Frozen estimate' if left.startswith('source') else 'Frozen prediction'),(b-a,'RdBu_r',[-diff,diff],'Difference of MIPs' if kind=='mip' else 'Signed section difference')]):
            ax=fig.add_subplot(grid[row,col])
            image_axes[col].append(ax)
            image_handles[col]=draw(ax,arr,e,lim,label+' · '+head,unit if col<2 else 'Signed '+unit,cmap,colorbar=False)
            if kind=='slice' and col<2:
                center=choice['nominal_bead_center_local_um_zyx']
                ax.plot([center[2]],[center[1 if plane=='xy' else 0]],marker='+',color='#00d6dd',markersize=9,markeredgewidth=1.3)
    for col in range(3):
        short_unit='Relative source coefficients' if left.startswith('source') else 'Relative image units'
        fig.colorbar(image_handles[col],ax=image_axes[col],pad=.025,shrink=.84,label=('Signed ' if col==2 else '')+short_unit)
    profile_data={}
    if profiles:
        colors=['#333333','#ce532e']
        names=['Reference','Frozen estimate'] if left.startswith('source') else ['Corrected observation','Frozen prediction']
        ij=choice['indices_zyx'];bounds=choice['crop_index_bounds_zyx_exclusive']
        # Axis-aligned lines through the same nearest sample-center planes as the images.
        for k,plane in enumerate(['xy','xz']):
            ax=fig.add_subplot(grid[2,k]);axis=2 if plane=='xy' else 0
            coords=(np.arange(bounds[axis][0],bounds[axis][1])+.5)*spacing[axis]
            row_in_slice=ij[1]-bounds[1][0]
            x_in_slice=ij[2]-bounds[2][0]
            lines=[a[row_in_slice,:] if plane=='xy' else a[:,x_in_slice] for a in pair[k]]
            for i,arr in enumerate(lines):
                peak=float(np.max(arr));assert peak>0
                ax.plot(coords,arr/peak,'o-',ms=3,lw=1.5,color=colors[i],label=names[i])
            ax.set(xlabel='Local '+('x' if plane=='xy' else 'z')+' (µm)',ylabel='Profile / its own maximum',title=('Lateral' if plane=='xy' else 'Axial')+' shape-only line profile')
            ax.grid(alpha=.2);ax.legend(fontsize=9)
            profile_data[plane]={'sample_centers_um':coords.tolist(),'unscaled_lines':[x.tolist() for x in lines],'per_line_maxima':[float(x.max()) for x in lines]}
        ax=fig.add_subplot(grid[2,2]);ax.axis('off')
        c=choice['nominal_bead_center_local_um_zyx'];actual=choice['actual_plane_centers_local_um_zyx']
        note=f'First catalogue bead (local µm)\nz={c[0]:.4f}, y={c[1]:.4f}, x={c[2]:.4f}\n\nActual section planes\nXY: z={actual[0]:.4f} µm\nXZ: y={actual[1]:.4f} µm\n\nMain images: common quantitative scale.\nProfiles: separate peak normalization,\nshape only; no alignment or recentering.'
        if left.startswith('source'):
            note+=f"\n\nWhole-volume peaks:\nreference {meta['whole_volume_ranges'][left][1]:.6f}\nestimate {meta['whole_volume_ranges'][right][1]:.6f}"
        ax.text(.02,.98,note,va='top',fontsize=10)
    center_note='\nXY = max over z; XZ = max over y · right column = difference of projections, not max of signed error' if kind=='mip' else '\nSections through the first catalogue bead; nearest available planes, no interpolation or fitted-peak recentering'
    fig.suptitle(title+center_note,fontsize=12)
    save(fig,name)
    display[name]={'kind':kind,'left':left,'right':right,'common_linear_scale':[low,high],'signed_symmetric_scale':[-diff,diff],'extents_xy_xz_um':extents,'interpolation':'nearest','aspect':'equal physical units','profiles':profile_data,'profile_normalization':'each line divided by its own maximum, shape only' if profiles else None}

compare('03-bead-orthogonal-mips','bead_observed','bead_prediction','3a  Held-out bead observation and prediction: orthogonal MIPs','relative image units','mip')
compare('03b-bead-center-sections','bead_observed','bead_prediction','3b  Calibration-bead center: XY and XZ sections','relative image units','slice',profiles=True)
compare('05-source-orthogonal-mips','source_reference','source_estimate','5a  Frozen reconstructed source versus paired reference: orthogonal MIPs','relative source-coefficient units','mip')
compare('05b-source-bead-sections','source_reference','source_estimate','5b  Specimen-bead center: reconstructed source versus reference','relative source-coefficient units','slice',profiles=True)
compare('06-prediction-orthogonal-mips','corrected','prediction','6a  Frozen image prediction versus corrected observation: orthogonal MIPs','relative image units','mip')
compare('06b-prediction-bead-sections','corrected','prediction','6b  Specimen-bead center: prediction versus corrected observation','relative image units','slice',profiles=True)

provenance={'schema':'simrecon.pr53.orthogonal-figures.v1','source_commit':meta['source_commit'],'archive_sha256':meta['archive_sha256'],'input_files':meta['input_files'],
 'archive_members':meta['archive_members'],'plane_choices':meta['choices'],'display':display,'projection_definition':meta['projection_definition'],
 'source_stats':meta['source_stats'],'truth_use':meta['truth_use'],'outputs':outputs,
 'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__,'backend':'Agg','font_family':'DejaVu Sans'},
 'render_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'prepare_code_sha256':meta['prepare_code_sha256'],
 'limitations':['maximum projections conceal axial/lateral location and do not establish resolution; paired center sections accompany them','XZ physical aspect preserved; nearest-neighbor display','main panels retain common absolute relative-unit scales, never independently peak-normalized','only labeled profile plots divide each line by its own maximum; shape comparison only, no metric/fit change','first catalogue bead chosen before inspecting estimates/errors; selected planes are nearest stored centers, not interpolated exact geometric centers','one fixed noisy synthetic run with finite scalar optics and source/pixel/pupil discretization','paired axial reference remains the declared mass-aggregation basis, not a continuum or prediction-equivalent truth source','no inference, changed settings, alignment, new seed or refit']}
(args.out/'orthogonal-provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
print(json.dumps({'outputs':outputs,'source_center_planes':meta['choices']['source_reference'],'calibration_center_planes':meta['choices']['bead_observed']}),flush=True)
