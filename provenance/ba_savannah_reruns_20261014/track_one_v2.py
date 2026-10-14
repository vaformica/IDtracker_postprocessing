from pathlib import Path
import sys,os,json,hashlib,subprocess,datetime
import numpy as np
R=Path(__file__).resolve().parent
p=json.loads((R/'TRACKING_PLAN.json').read_text())['runs'][int(sys.argv[1])]
out=R/'tracking_v2'/p['id'];out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def status(stage,**kw):
 d=dict(stage=stage,id=p['id'],job=os.environ.get('SLURM_JOB_ID'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw)
 (out/'status.json').write_text(json.dumps(d,indent=2));print(d,flush=True)
try:
 (out/'idtracker_output').mkdir(exist_ok=False)
 assert sha(p['source_toml'])==p['toml_sha256']
 assert sha(p['submission_toml'])==p['submission_sha256']
 assert sha(p['savannah_source_path'])==p['savannah_source_sha256']
 cmd=[str(Path(sys.executable).with_name('idtrackerai')),'--track','--load',p['submission_toml'],'--output_dir',str(out/'idtracker_output'),'--number_of_parallel_workers','16','--device','cuda','--data_policy','all']
 status('TRACKING',command=cmd)
 with (out/'idtracker.log').open('x') as log:ret=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT)
 sessions=list((out/'idtracker_output').rglob('session.json'));assert len(sessions)==1
 session=sessions[0].parent;meta=json.loads(sessions[0].read_text());assert meta['tracking_intervals']==p['tracking_intervals']
 trajectory=session/'trajectories/trajectories.npy';a=np.load(trajectory,allow_pickle=True).item()['trajectories'];assert a.ndim==3 and a.shape[1:]==(1,2) and len(a)>p['end']
 assert (session/'preprocessing/list_of_blobs.pickle').is_file()
 xy=a[p['start']:p['end']+1,0];assert xy.shape==(7200,2) and np.isfinite(xy).any()
 if p['excluded_frames']:assert np.isnan(a[p['excluded_frames']]).all()
 log=(out/'idtracker.log').read_text();assert ret.returncode==0 or (ret.returncode==1 and 'Success' in log),'Unresolved tracking failure'
 assert sha(p['source_toml'])==p['toml_sha256'] and sha(p['submission_toml'])==p['submission_sha256']
 status('COMPLETE_UNREVIEWED',session=str(session),trajectory=str(trajectory),trajectory_sha256=sha(trajectory),session_sha256=sha(sessions[0]),exit_code=ret.returncode,exit_warning=ret.returncode!=0,unexpected_missing_frames=int((~np.isfinite(xy).all(1)).sum())-len(p['excluded_frames']),frame_count=len(a),excluded_frames=p['excluded_frames'])
except BaseException as e:status('FAILED',error=repr(e));raise
