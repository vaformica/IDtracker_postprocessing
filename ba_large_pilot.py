#!/usr/bin/env python3
"""Versioned BA development pilot; immutable tracking and frozen detector modules."""
from pathlib import Path
import argparse,csv,hashlib,json,os,grp,subprocess,sys,traceback
from datetime import datetime,timezone
VERSION='ba-large-pilot-0.1.1'
FF='/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'
PROBE='/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,d):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');permit(p)
def permit(p):
 gid=grp.getgrnam('vformic1-swat-lab').gr_gid;os.chown(p,-1,gid);Path(p).chmod(0o2770 if Path(p).is_dir() else 0o660)
def probe(p,count=False):
 cmd=[PROBE,'-v','error']+(['-count_frames'] if count else [])+['-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,start_time,codec_name,nb_frames,nb_read_frames,duration','-of','json',str(p)]
 return json.loads(subprocess.check_output(cmd))['streams'][0]
def preflight(root,idx):
 plan=load(root/'PLAN.json');video=Path(plan['videos'][idx]);before=video.stat();s=probe(video);digest=sha(video);after=video.stat()
 assert s['avg_frame_rate']=='30/1' and float(s.get('start_time',0))==0
 assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
 save(root/'source_videos'/f'video_{idx:02d}.json',dict(video=str(video),sha256=digest,bytes=after.st_size,mtime_ns=after.st_mtime_ns,stream=s))
 print('SOURCE_VERIFIED',idx,flush=True)
def analyze(root,idx):
 sys.path.insert(0,str(root/'vendor'));sys.path.insert(0,str(root/'code'));import numpy as np
 import processor,ba_qc,ba_turtling
 from run_ba_pipeline import source_config,frame_rows,write_csv
 from ba_turtling_episode_experiment import experiment
 from ba_turtling_recovery_gate import gate_candidates
 plan=load(root/'PLAN.json');row=plan['sources'][idx];rid=row['id'];out=root/'runs_v2'/rid
 try:
  assert not out.exists(),f'Refusing existing run {out}'
  for n,h in load(root/'CODE_SHA256.json').items():assert sha(root/'code'/n)==h,n
  ss=row['sessions'][0];session=Path(ss['session']);toml=Path(row['toml']);trajectory=Path(ss['trajectory'])
  assert sha(toml)==row['toml_sha256'] and sha(session/'session.json')==ss['session_sha256']
  config,start,end,arena=source_config(toml,session,7200);processor.validate_trajectory_source(trajectory)
  arr=processor.load_trajectories(trajectory);assert arr.ndim==3 and arr.shape[1:]==(1,2) and end<len(arr)
  xy=arr[start:end+1,0];assert len(xy)==7200
  vi=plan['videos'].index(row['video']);vm=load(root/'source_videos'/f'video_{vi:02d}.json');video=Path(row['video']);st=video.stat();assert st.st_size==vm['bytes'] and st.st_mtime_ns==vm['mtime_ns']
  source_hashes=dict(toml=sha(toml),session=sha(session/'session.json'),trajectory=sha(trajectory),video=vm['sha256'])
  summary=processor.analyze(trajectory,session,start,end-start,30.,wall_buffer_px=30.,analysis_type='BA',one_frame_jump_threshold_px=200.,analysis_start_source='SOURCE_TOML_TRACKING_START')
  frames=list(frame_rows(xy,arena,start,200.,30.));base=np.array([f['turtling_candidate'] for f in frames]);exp=experiment(xy,base,start)
  known=[f for f in plan['camera_artifact_ledger'].get(row['video'],[]) if start<=f<=end];gate=gate_candidates(exp['episode_mask'],xy,start,initial_camera_artifact_frames=known)
  account=ba_turtling.summarize(gate['candidate_mask'],np.isfinite(xy).all(1).tolist(),start,30)
  qc=ba_qc.summarize(frames,summary[0]);qc['frozen_gate_status']=gate['status']
  if gate['status']!='RECOVERY_CONFIRMED_EXPERIMENTALLY':qc['flags'].append('TURTLING_RECOVERY_NOT_CONFIRMED')
  if known:qc['flags'].append('KNOWN_CAMERA_BUMP_RECORDING')
  for f,b,e,g,state in zip(frames,base,exp['episode_mask'],gate['candidate_mask'],gate['state']):
   f.update(baseline_turtling_candidate=bool(b),episode_turtling_candidate=bool(e),frozen_turtling_candidate=bool(g),turtling_eligibility_state=state)
  x,y=np.floor(arena.min(0)-12).astype(int);x=max(0,int(x)//2*2);y=max(0,int(y)//2*2);vs=vm['stream']
  w=min(int(np.ceil((arena[:,0].max()+12-x)/2)*2),vs['width']-x)//2*2;h=min(int(np.ceil((arena[:,1].max()+12-y)/2)*2),vs['height']-y)//2*2;assert w>0 and h>0
  out.mkdir(parents=True);write_csv(out/'summary.csv',summary,processor.OUTPUT_COLUMNS);write_csv(out/'frame_data.csv',frames)
  (out/'source.toml').write_bytes(toml.read_bytes());save(out/'predictions.json',dict(episode=exp,gate=gate,account=account));save(out/'qc.json',qc)
  pdf_name=toml.stem+'.pdf'
  if row['cohort']=='new_run_pilot':
   baseline_report=ba_turtling.summarize(base.tolist(),np.isfinite(xy).all(1).tolist(),start,30)
   processor.write_plot_pdf(out/'prototype_pages.pdf',trajectory,session,summary,'BA',video.name,toml.stem,'UNREVIEWED')
   make_pdf(out,pdf_name,toml.stem,start,end,base,exp,gate,account,qc)
  for n,p in [('toml',toml),('session',session/'session.json'),('trajectory',trajectory)]:assert sha(p)==source_hashes[n]
  result=dict(id=rid,status='ANALYSIS_COMPLETE_UNREVIEWED',cohort=row['cohort'],blind_full_run=row['blind_full_run'],toml=str(toml),session=str(session),trajectory=str(trajectory),video=str(video),source_hashes=source_hashes,start=start,end=end,frames=7200,fps=30,crop=[x,y,w,h],pdf_name=pdf_name if row['cohort']=='new_run_pilot' else None,pilot_version=VERSION,processor_version=processor.SCRIPT_VERSION,episode_version=exp['version'],gate_version=gate['version'],candidate_seconds=account['candidate_seconds'],bout_count=account['bout_count'],longest_bout_seconds=account['longest_bout_seconds'],recovery_status=gate['status'],qc_flags=qc['flags'],qc_metrics=qc['metrics'],camera_artifact_frames=known,pdf_style='prototype-0.8.1-with-frozen-pilot-cover',confirmed_overturned_seconds=None,code_sha256=load(root/'CODE_SHA256.json'))
  result['analysis_output_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file()};save(out/'manifest.json',result)
  for p in [out,*out.iterdir()]:permit(p)
  save(root/'results'/f'{rid}.json',result);print('ANALYZED',rid,account['candidate_seconds'],qc['flags'],flush=True)
 except Exception as e:
  save(root/'results'/f'{rid}.json',dict(id=rid,status='BLOCKED_RETAINED',toml=row['toml'],cohort=row['cohort'],reason=str(e),traceback=traceback.format_exc()));print('BLOCKED',rid,str(e),flush=True)
def make_pdf(out,name,label,start,end,base,exp,gate,account,qc):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.backends.backend_pdf import PdfPages
 from pypdf import PdfReader,PdfWriter
 from ba_turtling_episode_experiment import segments
 import textwrap
 with PdfPages(out/'frozen_detector_pages.pdf') as pdf:
  bouts=account['bouts'];pages=max(1,(len(bouts)+19)//20)
  for page in range(pages):
   fig=plt.figure(figsize=(8.5,11));fig.text(.07,.95,'BA frozen turtling pilot | UNREVIEWED',fontsize=16,va='top')
   fig.text(.07,.91,'\n'.join(textwrap.wrap(label,85)),fontsize=8,va='top')
   lines=[f"Original global frames {start}-{end} inclusive | 7,200 frames at 30 fps",f"Episode {exp['version']} | recovery gate {gate['version']}",f"Suggested turtling: {account['candidate_seconds']:.3f} seconds | {account['bout_count']} bouts",f"Tracking missing: {account['unknown_seconds']:.3f} seconds",'Confirmed time on back: NOT ASSESSED',f"Recovery status: {gate['status']}",'QC: '+(', '.join(qc['flags']) or 'No threshold flags'),'', 'Centroid-based hypotheses; quiet posture and camera motion require review.', 'No candidate does not establish upright posture or successful recovery.', 'Later prototype pages retain baseline metrics for comparison.']
   fig.text(.07,.855,'\n'.join('\n'.join(textwrap.wrap(x,92)) for x in lines),fontsize=9,va='top',linespacing=1.5)
   ax=fig.add_axes([.13,.48,.8,.12])
   for row,(name0,mask,color) in enumerate([('Baseline',base,'#777777'),('Episode',exp['episode_mask'],'#4d87ad'),('Gated',gate['candidate_mask'],'#bd6d12')]):
    ax.broken_barh([(start+int(a),int(b-a)) for a,b in segments(mask)],(row-.3,.6),facecolors=color)
   ax.set(xlim=(start,end+1),yticks=[0,1,2],yticklabels=['Baseline','Episode','Gated'],xlabel='Original global frame');ax.tick_params(labelsize=8)
   table=['GATED CANDIDATE INTERVALS (inclusive)', 'Start frame      End frame      Seconds      Boundary uncertain']
   for b in bouts[page*20:(page+1)*20]:table.append(f"{b['start_global_frame']:10d} {b['end_global_frame_inclusive']:14d} {b['seconds']:12.3f}    {'yes' if b['left_censored'] or b['right_censored'] else 'no'}")
   if not bouts:table.append('No gated candidate intervals. Review eligibility and tracking QC above.')
   fig.text(.07,.41,'\n'.join(table),fontsize=8,family='monospace',va='top',linespacing=1.5)
   fig.text(.07,.04,f'Frozen BA review pilot | provisional candidates | page {page+1}/{pages}',fontsize=8);pdf.savefig(fig);plt.close(fig)
 writer=PdfWriter()
 for path in [out/'frozen_detector_pages.pdf',out/'prototype_pages.pdf']:writer.append(PdfReader(path))
 with (out/name).open('wb') as f:writer.write(f)
 reader=PdfReader(out/name);assert len(reader.pages)>=2 and 'UNREVIEWED' in reader.pages[0].extract_text()
def encode(root,idx):
 plan=load(root/'PLAN.json');video=plan['videos'][idx];sources=[]
 for row in plan['sources']:
  if row['video']==video:
   r=load(root/'results'/f"{row['id']}.json")
   if r['status']=='ANALYSIS_COMPLETE_UNREVIEWED':sources.append(r)
 if not sources:save(root/'encoded'/f'video_{idx:02d}.json',dict(status='NO_USABLE_RUNS',video=video,runs=[]));return
 seek=min(s['start'] for s in sources)//30;n=len(sources);filters=[]
 if n>1:filters.append('[0:v]split='+str(n)+''.join(f'[v{i}]' for i in range(n)))
 for i,s in enumerate(sources):
  x,y,w,h=s['crop'];lo=s['start']-seek*30;inp=f'[v{i}]' if n>1 else '[0:v]';filters.append(f'{inp}trim=start_frame={lo}:end_frame={lo+7200},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y}[o{i}]')
 cmd=[FF,'-v','error','-nostdin','-threads','4','-ss',str(seek),'-i',video,'-filter_complex_threads','2','-filter_complex',';'.join(filters)]
 for i,s in enumerate(sources):
  out=root/'runs_v2'/s['id']/'review_video.mp4';assert not out.exists(),out
  cmd+=['-map',f'[o{i}]','-frames:v','7200','-an','-c:v','libx264','-threads','1','-crf','20','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
 subprocess.run(cmd,check=True)
 records=[]
 for s in sources:
  out=root/'runs_v2'/s['id']/'review_video.mp4';st=probe(out,True);assert int(st['nb_read_frames'])==7200 and st['avg_frame_rate']=='30/1' and abs(float(st['duration'])-240)<.001 and [st['width'],st['height']]==s['crop'][2:]
  record=dict(id=s['id'],status='VIDEO_COMPLETE_UNREVIEWED',sha256=sha(out),stream=st);save(out.with_name('VIDEO_RECEIPT.json'),record);permit(out);records.append(record)
 vm=load(root/'source_videos'/f'video_{idx:02d}.json');assert sha(video)==vm['sha256']
 save(root/'encoded'/f'video_{idx:02d}.json',dict(status='VERIFIED',video=video,runs=records));print('VIDEO_GROUP_VERIFIED',idx,len(records),flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','analyze','encode']);p.add_argument('root',type=Path);p.add_argument('index',type=int);a=p.parse_args();
 if a.mode=='preflight':
  try:preflight(a.root.resolve(),a.index)
  except Exception as e:save(a.root/'source_videos'/f'video_{a.index:02d}.json',dict(status='BLOCKED_RETAINED',reason=str(e),traceback=traceback.format_exc()))
 else:globals()[a.mode](a.root.resolve(),a.index)
if __name__=='__main__':main()
