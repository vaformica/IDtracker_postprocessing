"""Prepare an immutable 60-run sweep from the three recorded source sessions."""
import hashlib,itertools,json
from pathlib import Path

LABELS=['Box01_OLD','Box01_OLD_TEst','Box02_MIX']
BASE='/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024'

def toml_value(v):
    if v is True:return 'true'
    if v is False:return 'false'
    if isinstance(v,float) and v==float('inf'):return 'inf'
    if isinstance(v,list):return '['+', '.join(map(toml_value,v))+']'
    return json.dumps(v)

def main():
    root=Path('results/firebird_grid_v1');root.mkdir(exist_ok=False)
    configs=root/'configs';configs.mkdir();tasks=[]
    for label in LABELS:
        source=Path('results/firebird_inputs')/label/'session.json'
        d=json.loads(source.read_text())
        params={k:d[k] for k in ['intensity_ths','area_ths','number_of_animals','use_bkg','roi_list','background_subtraction_stat','resolution_reduction','number_of_frames_for_background']}
        params.update(video_paths=[BASE+'/groupagetrial01_062024.mp4'],tracking_intervals=[[422,16998]],check_segmentation=False,track_wo_identities=False)
        cases=[('paired_control',bg,d['intensity_ths'],d['area_ths'][0]) for bg in [False,True]]
        cases += [('shared_grid',bg,[t,255] if bg else [0,t],area)
                  for bg in [False,True] for t in ([30,50,70] if bg else [123,143,163]) for area in [250,400,550]]
        for kind,bg,threshold,area in cases:
            index=len(tasks);name=f'{index:03d}_{label}_{kind}_bg{int(bg)}_i{threshold[0]}-{threshold[1]}_a{area:g}'
            config=dict(params,name=name,use_bkg=bg,intensity_ths=threshold,area_ths=[area,float('inf')])
            path=configs/(name+'.toml');path.write_text(''.join(k+' = '+toml_value(v)+'\n' for k,v in config.items()))
            tasks.append(dict(index=index,name=name,label=label,kind=kind,use_bkg=bg,intensity_low=threshold[0],intensity_high=threshold[1],min_area=area,config='configs/'+path.name,config_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_session_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    assert len(tasks)==60
    (root/'tasks.json').write_text(json.dumps(tasks,indent=2)+'\n')
    (root/'design.json').write_text(json.dumps(dict(tracking_interval=[422,16998],analysis_inclusive=[422,7622],fps=30,area_minima=[250,400,550],background_on_lower=[30,50,70],background_off_upper=[123,143,163],notes='54 shared-grid runs plus 6 paired controls. Controls preserve source intensity and area while toggling background. All runs standardize tracking start to422 for comparable training coverage. OLD and OLD_TEst are two parameterizations of the same group, not independent biological replicates. No automatic QC approval or claim of optimality from missingness alone.'),indent=2)+'\n')
    print(root,len(tasks))
if __name__=='__main__':main()
