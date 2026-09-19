"""Run one isolated IDtracker sweep task and retain explicit success evidence."""
import datetime,hashlib,json,os,subprocess,sys,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
TRACK='/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/idtrackerai'
POST='/home/vformic1-swat/miniconda3/envs/idtracker_reprocess_v1/bin/python'

def state(folder,stage,**kwargs):
    d=dict(stage=stage,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),job=os.environ.get('SLURM_JOB_ID'),**kwargs)
    temp=folder/'status.partial.json';temp.write_text(json.dumps(d,indent=2)+'\n');temp.replace(folder/'status.json')

def main():
    task=json.loads((ROOT/'tasks.json').read_text())[int(os.environ['SLURM_ARRAY_TASK_ID'])]
    folder=ROOT/'runs'/task['name'];folder.mkdir(parents=True,exist_ok=False)
    try:
        config=ROOT/task['config'];assert hashlib.sha256(config.read_bytes()).hexdigest()==task['config_sha256']
        output=folder/'tracking';output.mkdir()
        state(folder,'TRACKING',task=task)
        with (folder/'tracking.log').open('x') as log:
            process=subprocess.run([TRACK,'--track','--load',str(config),'--output_dir',str(output),'--number_of_parallel_workers',os.environ.get('SLURM_CPUS_PER_TASK','8'),'--device','cuda','--data_policy','all'],cwd=folder,stdout=log,stderr=subprocess.STDOUT)
        sessions=list(output.glob('*/session.json'))
        if len(sessions)!=1:raise RuntimeError(f'Expected exactly one session; CLI exit {process.returncode}')
        session=sessions[0].parent;metadata=json.loads(sessions[0].read_text())
        finished=metadata.get('timers',{}).get('Tracking session',{}).get('finish_time')
        trajectory=session/'trajectories/trajectories.npy'
        # Version6.0.10 returns1 on successful runs here. Require independent completion evidence.
        logtext=(folder/'tracking.log').read_text(errors='replace')
        if not finished or not trajectory.is_file() or 'FINISH Tracking session' not in logtext or 'Success' not in logtext:
            raise RuntimeError(f'Incomplete tracking; CLI exit {process.returncode}')
        data=np.load(trajectory,allow_pickle=True).item();xy=data['trajectories'];assert xy.ndim==3 and xy.shape[1:]==(6,2)
        sample=xy[422:7623];assert len(sample)==7201
        present=np.isfinite(sample).all(axis=2);steps=np.linalg.norm(np.diff(sample,axis=0),axis=2)
        validsteps=np.isfinite(steps)
        stats=metadata.get('individual_fragments_stats',{})
        metrics=dict(**task,tracking_exit_code=process.returncode,tracking_finished=finished,
            missing_percent=float(100*(~present).mean()),per_animal_missing_percent=(100*(~present).mean(axis=0)).tolist(),
            all_six_present_percent=float(100*present.all(axis=1).mean()),
            rejected_jump_percent=float(100*(steps[validsteps]>200).mean()) if validsteps.any() else None,
            estimated_accuracy=metadata.get('estimated_accuracy'),silhouette_score=metadata.get('silhouette_score'),
            fragment_connectivity=metadata.get('fragment_connectivity'),
            detected_blobs=stats.get('blobs'),crossing_blobs=stats.get('crossing_blobs'),
            number_of_error_frames=metadata.get('number_of_error_frames'),
            trajectory_sha256=hashlib.sha256(trajectory.read_bytes()).hexdigest(),session=str(session))
        (folder/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
        state(folder,'POSTPROCESSING',task=task,session=str(session))
        report=session/'six_beetle_postprocessing_v042'
        with (folder/'postprocessing.log').open('x') as log:
            subprocess.run([POST,str(ROOT/'six_beetle_processor.py'),'--trajectory',str(trajectory),'--session',str(session),
                '--output',str(report),'--start','422','--window','7200','--video','groupagetrial01_062024.mp4',
                '--cell-label',task['label'],'--pdf-name',task['name']+'.pdf'],stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest=json.loads((report/'manifest.json').read_text())
        for name,digest in manifest['output_sha256'].items():assert hashlib.sha256((report/name).read_bytes()).hexdigest()==digest
        state(folder,'COMPLETE_UNREVIEWED',task=task,session=str(session),output=str(report),metrics=str(folder/'metrics.json'))
    except BaseException as exc:
        state(folder,'FAILED',task=task,error=repr(exc));traceback.print_exc();raise
if __name__=='__main__':main()
