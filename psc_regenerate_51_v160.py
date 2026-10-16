#!/usr/bin/env python3
"""Reproducible, manifest-driven PSC 1.6.0 dyadic and six-beetle regeneration (UNREVIEWED)."""
from __future__ import annotations
import argparse,collections,csv,datetime,hashlib,html,json,os,random,shutil,subprocess,sys,zipfile
from pathlib import Path

MODEL='1.6.0'; VIEWER='raw-psc-compare-v4'; PROCESSOR='0.8.2-group'; COUNT=51; SEED=20260930
OLD=Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/dyadic_fight_7200_frames_psc_v1_5_1_processor_0_8_1_20260928')
FFMPEG='/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'
FFPROBE=str(Path(FFMPEG).with_name('ffprobe'))
CODE=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);temp=p.with_name(p.name+'.partial');temp.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');temp.replace(p)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def rows_csv(p,rows):
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def select(previous):
 import re
 base=Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs')
 dyad=base/'dyadic_25_run_development_psc_v1_5_2_viewer_v4_20260930'
 six=base/'grouptrial_2024_9000_frames_OFFICIAL_26_psc_v1_5_1_processor_0_8_1_20260928'
 tasks=[]
 for old in read(dyad/'plan.json')['tasks']:
  r=dict(old,animals=2,frames=7200,collection='dyadic',
         previous_manifest=str(dyad/'runs'/old['stem']/'analysis/manifest.json'))
  tasks.append(r)
 with (six/'RUN_MANIFEST.csv').open() as f:
  rows=list(csv.DictReader(f))
 for row in rows:
  old=six/'runs'/row['label'];m=read(old/'analysis/manifest.json')
  review=read(old/'review_compare_v3/source_manifest.json')
  stem=Path(row['source_toml']).stem
  cell=re.search(r'_(Box\d+)(?:_(?:OLD|MIX|YOUNG))?$',stem,re.I).group(1).upper()
  tasks.append(dict(stem=stem,id=stem,cell=cell,animals=6,frames=9000,collection='six_beetle',
   source_path=row['source_toml'],source_sha256=row['source_toml_sha256'],
   submitted_toml=row['submitted_toml'],submitted_sha256=row['submitted_toml_sha256'],
   trajectory=m['trajectory_file'],trajectory_sha256=sha(m['trajectory_file']),
   session=m['session_folder'],blob_evidence=m['blob_evidence_file'],
   previous_manifest=str(old/'analysis/manifest.json'),source_video=review['video_source'],
   fps=review['fps'],first_global_frame=int(row['first_global_frame']),
   last_global_frame_inclusive=int(row['last_global_frame_inclusive']),
   selection_reason='REGENERATE_ALL_26_PREVIOUS_SIX_BEETLE_RUNS',source_name_warning=''))
 assert len(tasks)==51 and len({r['stem'] for r in tasks})==51
 return dict(schema='shared-psc-regeneration-v1',created_utc=utc(),run_count=51,
  dyadic_runs=25,six_beetle_runs=26,review_status='UNREVIEWED',psc_model_version=MODEL,
  processor_version=PROCESSOR,review_view_version=VIEWER,
  scope='Same 25 dyadic pilot and all 26 six-beetle runs; no new sample selection.',tasks=tasks)
def preflight(root):
 plan=read(root/'plan.json');records=[]
 for r in plan['tasks']:
  for key,expected in [('source_path',r['source_sha256']),('trajectory',r['trajectory_sha256'])]:
   if sha(r[key])!=expected:raise ValueError(f'Changed input: {r[key]}')
  old=read(r['previous_manifest']);blob=Path(r['blob_evidence']);evidence=read(blob)
  if sha(blob)!=old['blob_evidence_sha256'] or evidence['schema']!='idtracker-blob-evidence-v1':raise ValueError('Changed detection export')
  if sha(evidence['source'])!=evidence['source_sha256']:raise ValueError('Changed IDtracker detection source')
  if not Path(r['source_video']).is_file() or not Path(r['session']).is_dir():raise FileNotFoundError(r['stem'])
  import tomllib
  toml=tomllib.loads(Path(r['source_path']).read_text())
  if int(toml['number_of_animals'])!=r['animals'] or int(toml['tracking_intervals'][0][0])!=r['first_global_frame']:raise ValueError('TOML mismatch')
  if r['last_global_frame_inclusive']-r['first_global_frame']+1!=r['frames']:raise ValueError('Frame count')
  records.append(dict(id=r['id'],stem=r['stem'],source_toml_sha256=r['source_sha256'],trajectory_sha256=r['trajectory_sha256'],blob_evidence_sha256=sha(blob),blob_source_sha256=evidence['source_sha256']))
 write(root/'PREFLIGHT.json',dict(status='PASS',utc=utc(),records=records,plan_sha256=sha(root/'plan.json')))
 print('PREFLIGHT PASS',len(records),flush=True)
def probe(video):
 return json.loads(subprocess.check_output([FFPROBE,'-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_frames,nb_read_frames,r_frame_rate,width,height','-of','json',str(video)],text=True))['streams'][0]
def run(root,index):
 from psc_release_validation import validate_bundle
 from run_six_beetle_pipeline import load_rois,probe_video,arena_crop
 from review_geometry import plan_review_geometry,review_filter
 from build_canonical_review import build
 from render_psc_outlined_pdf import render
 from output_manifest import write_output_manifest
 r=read(root/'plan.json')['tasks'][index];folder=root/'runs'/r['stem'];folder.mkdir(parents=True,exist_ok=False)
 status=folder/'status.json'
 def phase(name,**kw):write(status,dict(stage=name,utc=utc(),id=r['id'],stem=r['stem'],**kw))
 try:
  if read(root/'PREFLIGHT.json')['plan_sha256']!=sha(root/'plan.json'):raise ValueError('Plan changed')
  snapshot=read(root/'CODE_SNAPSHOT.json')
  for name,digest in snapshot['sha256'].items():
   if sha(CODE/name)!=digest:raise ValueError(f'Code changed: {name}')
  input_before={p:sha(p) for p in (r['source_path'],r['trajectory'],r['blob_evidence'])}
  video_stat=Path(r['source_video']).stat();phase('ANALYSIS')
  (folder/'input').mkdir();shutil.copy2(r['source_path'],folder/'input'/Path(r['source_path']).name)
  write(folder/'selection.json',r)
  analysis=folder/'analysis';review=folder/'review';outline=folder/'outlined_pdf'
  cmd=[sys.executable,str(CODE/'six_beetle_processor.py'),'--trajectory',r['trajectory'],'--session',r['session'],'--blob-evidence',r['blob_evidence'],'--output',str(analysis),'--start',str(r['first_global_frame']),'--window',str(r['frames']-1),'--video',Path(r['source_video']).name,'--cell-label',r['stem'],'--pdf-name',r['stem']+'.pdf','--fps',str(r['fps']),'--social-distance-threshold-px','60']
  subprocess.run(cmd,check=True)
  valid=validate_bundle(analysis,MODEL,PROCESSOR)
  if valid['frames']!=r['frames'] or valid['animals']!=r['animals']:raise ValueError('Wrong canonical window')
  phase('VIDEO',validation=valid)
  rois=load_rois(Path(r['session']));width,height=probe_video(Path(r['source_video']),FFPROBE);crop=arena_crop(rois,width,height);geometry=plan_review_geometry(rois,crop);vf=review_filter(r['first_global_frame'],r['last_global_frame_inclusive'],geometry)
  video=folder/(r['stem']+'__encoding.mp4')
  video_cmd=[FFMPEG,'-hide_banner','-loglevel','error','-threads','2','-i',r['source_video'],'-filter_threads','2','-vf',vf,'-an','-c:v','libx264','-threads','4','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
  subprocess.run(video_cmd,check=True)
  page=build(analysis,video,review,crop,r['fps'],label=r['stem'],source_toml=r['source_path'],source_video=r['source_video'],video_geometry=geometry,video_filter=vf)
  # Builder hardlinks/copies its verified derivative; remove only this temporary encoding.
  video.unlink()
  phase('PDF_AND_VERIFICATION',validation=valid)
  pdf=render(analysis,outline)
  review_meta=read(review/'source_manifest.json');meta=read(analysis/'manifest.json')
  if review_meta['review_view_version']!=VIEWER or review_meta['cell_id']!=r['cell']:raise ValueError('Viewer/cell mismatch')
  if review_meta['html']!=r['stem']+'__interaction_review.html' or review_meta['video']!=r['stem']+'__review_video.mp4':raise ValueError('Artifact identity mismatch')
  stream=probe(review/review_meta['video'])
  if int(stream['nb_frames'])!=r['frames'] or int(stream['nb_read_frames'])!=r['frames']:raise ValueError('Encoded frame count mismatch')
  if abs(float(__import__('fractions').Fraction(stream['r_frame_rate']))-r['fps'])>1e-5:raise ValueError('Video frame rate mismatch')
  for name,digest in meta['output_sha256'].items():
   if sha(analysis/name)!=digest:raise ValueError(f'Output hash mismatch {name}')
  with (analysis/'frame_data.csv').open() as f:frame_rows=list(csv.DictReader(f))
  expected=set(range(r['first_global_frame'],r['last_global_frame_inclusive']+1))
  if len(frame_rows)!=r['frames']*r['animals']:raise ValueError('Frame CSV row count')
  for animal in map(str,range(r['animals'])):
   if {int(x['global_frame']) for x in frame_rows if x['animal_id']==animal}!=expected:raise ValueError('Frame CSV window')
  for p in [analysis/r['stem'].__add__('.pdf'),pdf]:
   content=subprocess.check_output(['pdftotext',str(p),'-'],text=True)
   if MODEL not in content or PROCESSOR not in content or r['cell'].lower() not in content.lower():raise ValueError(f'PDF label/version missing {p}')
  for p,digest in input_before.items():
   if sha(p)!=digest:raise ValueError(f'Input changed during processing {p}')
  after=Path(r['source_video']).stat()
  if (after.st_size,after.st_mtime_ns)!=(video_stat.st_size,video_stat.st_mtime_ns):raise ValueError('Source video changed')
  receipt=dict(status='COMPLETE_UNREVIEWED',utc=utc(),id=r['id'],stem=r['stem'],source_toml=r['source_path'],source_video=r['source_video'],source_video_sha256=review_meta['video_sha256'],input_sha256=input_before,plan_sha256=sha(root/'plan.json'),code_snapshot_sha256=sha(root/'CODE_SNAPSHOT.json'),analysis_command=cmd,video_command=video_cmd,validation=valid,video_probe=stream,review_html=str(page),outlined_pdf=str(pdf),review_manifest_sha256=sha(review/'source_manifest.json'),analysis_manifest_sha256=sha(analysis/'manifest.json'))
  write(folder/'pipeline_receipt.json',receipt)
  write_output_manifest(analysis,review,receipt=folder/'pipeline_receipt.json',source_toml=Path(r['source_path']))
  phase('COMPLETE_UNREVIEWED',validation=valid)
 except Exception as e:
  phase('FAILED',error=f'{type(e).__name__}: {e}');raise

def package(root):
 plan=read(root/'plan.json');checks={};index=[]
 zip_dir=root/'individual_run_zips';zip_dir.mkdir(exist_ok=False)
 for r in plan['tasks']:
  folder=root/'runs'/r['stem']
  if read(folder/'status.json')['stage']!='COMPLETE_UNREVIEWED':raise ValueError('Incomplete '+r['stem'])
  meta=read(folder/'review/source_manifest.json');outline=read(folder/'outlined_pdf/render_manifest.json')
  csv_links=''.join('<li><a href="'+html.escape(p.name,quote=True)+'">'+html.escape(p.name)+'</a></li>' for p in sorted((folder/'analysis').glob('*.csv')))
  (folder/'analysis/CSV_INDEX.html').write_text('<!doctype html><meta charset="utf-8"><title>'+html.escape(r['stem'])+' CSV files</title><h1>'+html.escape(r['stem'])+'</h1><p>PSC 1.6.0 — UNREVIEWED. Raw and model-derived columns remain separate.</p><ul>'+csv_links+'</ul>')
  files=sorted(p for p in folder.rglob('*') if p.is_file())
  for p in files:checks[str(p.relative_to(root))]=sha(p)
  archive=zip_dir/(r['stem']+'__PSC1.6.0.zip')
  with zipfile.ZipFile(archive,'w') as z:
   for p in files:z.write(p,str(p.relative_to(folder.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
  with zipfile.ZipFile(archive) as z:
   if z.testzip():raise ValueError('Bad individual ZIP')
  index.append(dict(run=r['stem'],collection=r['collection'],cell=r['cell'],
   first_global_frame=r['first_global_frame'],last_global_frame_inclusive=r['last_global_frame_inclusive'],frames=r['frames'],
   review_status='UNREVIEWED',html=str((folder/'review'/meta['html']).relative_to(root)),
   video=str((folder/'review'/meta['video']).relative_to(root)),
   csv=str((folder/'analysis/CSV_INDEX.html').relative_to(root)),
   pdf=str((folder/'analysis'/(r['stem']+'.pdf')).relative_to(root)),
   outlined_pdf=str((folder/'outlined_pdf'/outline['pdf_filename']).relative_to(root)),
   zip=str(archive.relative_to(root)),zip_sha256=sha(archive),zip_bytes=archive.stat().st_size))
 rows_csv(root/'RUN_INDEX.csv',index)
 rows_csv(root/'REVIEW_WORKSHEET.csv',[dict(run=r['run'],reviewer='',global_frame='',issue='',decision='',review_status='UNREVIEWED') for r in index])
 title='25 dyadic + 26 six-beetle reviews — PSC 1.6.0 / processor 0.8.2-group — UNREVIEWED'
 entries=[]
 for r in index:
  links=' · '.join('<a href="'+html.escape(r[k],quote=True)+'">'+label+'</a>' for k,label in [('html','Open review'),('video','Video'),('pdf','PDF'),('outlined_pdf','Outlined PDF'),('csv','CSV files')])
  entries.append('<tr><td>'+html.escape(r['collection'])+'</td><td>'+html.escape(r['run'])+'</td><td>'+str(r['frames'])+'</td><td>'+links+'</td></tr>')
 (root/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>'+title+'</title><style>body{font:15px system-ui;margin:24px}td,th{border:1px solid #aaa;padding:8px}table{border-collapse:collapse}td{overflow-wrap:anywhere}a{white-space:nowrap}</style><h1>'+title+'</h1><p>Available IDtracker IDs keep their exact coordinates. Two assigned centroids within 60 pixels are in proximity. PSC inference applies only to missing IDs. Missing-ID inference and upstream identity swaps still require human review.</p><p>The dyadic sample is unchanged (25 runs across 12 recordings, 7,200 frames each); all 26 six-beetle trials contain 9,000 frames each. Windows begin at their source TOML start. Report global frame numbers and full video/cell names.</p><p><a href="RUN_INDEX.csv">Run index</a> · <a href="REVIEW_WORKSHEET.csv">Review worksheet</a></p><table><tr><th>Collection</th><th>Video and cell</th><th>Frames</th><th>Review files</th></tr>'+''.join(entries)+'</table>')
 write(root/'FILE_CHECKSUMS.json',checks)
 (root/'README.txt').write_text(title+'\nOpen START_HERE.html. Keep each HTML beside its MP4. Automatic results remain UNREVIEWED. Source data are unchanged.\n')
 archives=[]
 for collection in ['dyadic','six_beetle']:
  selected={r['stem'] for r in plan['tasks'] if r['collection']==collection}
  archive=root/(collection+'__PSC1.6.0_processor0.8.2__review_bundle.zip')
  with zipfile.ZipFile(archive,'w') as z:
   for p in sorted(root.rglob('*')):
    if not p.is_file() or p.suffix=='.zip' or any(x in p.parts for x in ['logs','__pycache__','individual_run_zips']):continue
    rel=p.relative_to(root)
    if rel.parts[0]=='runs' and rel.parts[1] not in selected:continue
    # Each collection includes a filtered index with resolving links.
    if p.name in ['START_HERE.html','RUN_INDEX.csv','FILE_CHECKSUMS.json','REVIEW_WORKSHEET.csv']:continue
    z.write(p,str(rel),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
   filtered=[r for r in index if r['collection']==collection]
   text=(root/'START_HERE.html').read_text()
   for r,entry in zip(index,entries):
    if r['collection']!=collection:text=text.replace(entry,'')
   z.writestr('START_HERE.html',text)
   z.writestr('FILE_CHECKSUMS.json',json.dumps({k:v for k,v in checks.items() if k.split('/')[1] in selected},indent=2))
   import io
   for name,rows in [('RUN_INDEX.csv',filtered),('REVIEW_WORKSHEET.csv',[dict(run=r['run'],reviewer='',global_frame='',issue='',decision='',review_status='UNREVIEWED') for r in filtered])]:
    buf=io.StringIO();w=csv.DictWriter(buf,list(rows[0]));w.writeheader();w.writerows(rows);z.writestr(name,buf.getvalue())
  with zipfile.ZipFile(archive) as z:
   if z.testzip():raise ValueError('Bad collection ZIP')
  archives.append(dict(collection=collection,path=str(archive),sha256=sha(archive),bytes=archive.stat().st_size))
 receipt=dict(status='COMPLETE_UNREVIEWED',created_utc=utc(),run_count=51,dyadic_runs=25,six_beetle_runs=26,
  psc_model_version=MODEL,processor_version=PROCESSOR,review_view_version=VIEWER,
  all_encoded_frame_counts_verified=True,all_pdf_versions_verified=True,all_raw_psc_csvs_verified=True,
  source_inputs_unchanged=True,zip_integrity_passed=True,plan_sha256=sha(root/'plan.json'),
  code_snapshot_sha256=sha(root/'CODE_SNAPSHOT.json'),file_checksums_sha256=sha(root/'FILE_CHECKSUMS.json'),archives=archives)
 write(root/'RELEASE_RECEIPT.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['select','preflight','run','package']);p.add_argument('root',type=Path);p.add_argument('--previous',type=Path);p.add_argument('--index',type=int);a=p.parse_args()
 if a.action=='select':
  a.root.mkdir(parents=True,exist_ok=True)
  if (a.root/'plan.json').exists():raise FileExistsError(a.root/'plan.json')
  plan=select(None);write(a.root/'plan.json',plan);print(json.dumps(collections.Counter(Path(r['source_video']).name for r in plan['tasks']),indent=2))
 elif a.action=='preflight':preflight(a.root)
 elif a.action=='run':run(a.root,a.index)
 else:package(a.root)
if __name__=='__main__':main()
