#!/usr/bin/env python3
"""Reproducible, manifest-driven PSC 1.5.2 dyadic development pilot (UNREVIEWED)."""
from __future__ import annotations
import argparse,collections,csv,datetime,hashlib,html,json,os,random,shutil,subprocess,sys,zipfile
from pathlib import Path

MODEL='1.5.2'; VIEWER='raw-psc-compare-v4'; PROCESSOR='0.8.1-group'; COUNT=25; SEED=20260930
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
 groups=collections.defaultdict(list)
 for row in previous['tasks']:
  if not row['excluded']:groups[row['source_video']].append(row)
 if len(groups)!=12 or sum(map(len,groups.values()))!=99:raise ValueError('Expected original 99-run, 12-recording population')
 rng=random.Random(SEED);chosen=[];remaining=[]
 for video,group in sorted(groups.items()):
  group=sorted(group,key=lambda r:r['source_path']);rng.shuffle(group)
  if Path(video).stem=='Camera_2_40359705_20260702_1536_FIGHT_ACT2':
   picks=[r for r in group if Path(r['source_path']).stem.endswith(('_A1','_B2'))]
   if len(picks)!=2:raise ValueError('Both reported-episode candidate cells required')
   reason='TARGETED_FRAME_3005_A1_OR_B2'
  else:picks=group[:2];reason='STRATIFIED_RANDOM_TWO_PER_RECORDING'
  for r in picks:chosen.append(dict(r,selection_reason=reason))
  remaining.extend(r for r in group if r not in picks)
 extra=rng.choice(sorted(remaining,key=lambda r:r['source_path']))
 chosen.append(dict(extra,selection_reason='SEEDED_RANDOM_EXTRA'))
 chosen.sort(key=lambda r:r['source_path'])
 for i,r in enumerate(chosen):
  r.update(pilot_index=i,stem=Path(r['source_path']).stem,cell=Path(r['source_path']).stem.rsplit('_',1)[1],
           blob_evidence=str(OLD/'tasks'/r['id']/'analysis_v151r081.blob_evidence.json'),
           previous_manifest=str(OLD/'tasks'/r['id']/'analysis_v151r081'/'manifest.json'),
           source_name_warning='PAPER_DATA_WRONG' if 'PAPER_DATA_WRONG' in r['source_path'] else '')
 assert len(chosen)==COUNT and len({r['id'] for r in chosen})==COUNT
 return dict(schema='dyadic-development-pilot-v1',created_utc=utc(),seed=SEED,run_count=COUNT,
  eligible_population=99,source_recordings=12,frames_per_run=7200,review_status='UNREVIEWED',
  psc_model_version=MODEL,processor_version=PROCESSOR,review_view_version=VIEWER,
  sampling='Two cells per source recording, with A1/B2 in the reported recording selected deliberately; remaining within-recording choices and one extra cell use the fixed seed. Development sample, not a prevalence estimate.',tasks=chosen)
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
  if int(toml['number_of_animals'])!=2 or int(toml['tracking_intervals'][0][0])!=r['first_global_frame']:raise ValueError('TOML mismatch')
  if r['last_global_frame_inclusive']-r['first_global_frame']+1!=7200:raise ValueError('Frame count')
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
  cmd=[sys.executable,str(CODE/'six_beetle_processor.py'),'--trajectory',r['trajectory'],'--session',r['session'],'--blob-evidence',r['blob_evidence'],'--output',str(analysis),'--start',str(r['first_global_frame']),'--window','7199','--video',Path(r['source_video']).name,'--cell-label',r['stem'],'--pdf-name',r['stem']+'.pdf','--fps',str(r['fps']),'--social-distance-threshold-px','60']
  subprocess.run(cmd,check=True)
  valid=validate_bundle(analysis,MODEL,PROCESSOR)
  if valid['frames']!=7200 or valid['animals']!=2:raise ValueError('Wrong canonical window')
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
  if int(stream['nb_frames'])!=7200 or int(stream['nb_read_frames'])!=7200:raise ValueError('Encoded frame count mismatch')
  if abs(float(__import__('fractions').Fraction(stream['r_frame_rate']))-r['fps'])>1e-5:raise ValueError('Video frame rate mismatch')
  for name,digest in meta['output_sha256'].items():
   if sha(analysis/name)!=digest:raise ValueError(f'Output hash mismatch {name}')
  with (analysis/'frame_data.csv').open() as f:frame_rows=list(csv.DictReader(f))
  expected=set(range(r['first_global_frame'],r['last_global_frame_inclusive']+1))
  if len(frame_rows)!=14400:raise ValueError('Frame CSV row count')
  for animal in ['0','1']:
   if {int(x['global_frame']) for x in frame_rows if x['animal_id']==animal}!=expected:raise ValueError('Frame CSV window')
  for p in [analysis/r['stem'].__add__('.pdf'),pdf]:
   content=subprocess.check_output(['pdftotext',str(p),'-'],text=True)
   if MODEL not in content or PROCESSOR not in content or r['cell'] not in content:raise ValueError(f'PDF label/version missing {p}')
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
 plan=read(root/'plan.json');index=[];entries=[];checks={};zip_dir=root/'individual_run_zips';zip_dir.mkdir(exist_ok=True)
 for r in plan['tasks']:
  folder=root/'runs'/r['stem'];status=read(folder/'status.json')
  if status['stage']!='COMPLETE_UNREVIEWED':raise ValueError('Incomplete '+r['stem'])
  meta=read(folder/'review/source_manifest.json');receipt=read(folder/'pipeline_receipt.json');outline=read(folder/'outlined_pdf/render_manifest.json')
  files=sorted(p for p in folder.rglob('*') if p.is_file())
  for p in files:checks[str(p.relative_to(root))]=sha(p)
  out=zip_dir/(r['stem']+'__PSC1.5.2_test.zip')
  if out.exists():raise FileExistsError(out)
  with zipfile.ZipFile(out,'w') as z:
   for p in files:z.write(p,str(p.relative_to(folder.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
  with zipfile.ZipFile(out) as z:
   if z.testzip():raise ValueError('Bad ZIP')
  row=dict(run=r['stem'],cell=r['cell'],source_video=Path(r['source_video']).name,selection_reason=r['selection_reason'],source_name_warning=r['source_name_warning'],first_global_frame=r['first_global_frame'],last_global_frame_inclusive=r['last_global_frame_inclusive'],frames=7200,review_status='UNREVIEWED',html=str((folder/'review'/meta['html']).relative_to(root)),video=str((folder/'review'/meta['video']).relative_to(root)),pdf=str((folder/'analysis'/(r['stem']+'.pdf')).relative_to(root)),outlined_pdf=str((folder/'outlined_pdf'/outline['pdf_filename']).relative_to(root)),zip=str(out.relative_to(root)),zip_sha256=sha(out),zip_bytes=out.stat().st_size)
  index.append(row)
  entries.append('<tr><td>'+html.escape(r['stem'])+'</td><td>'+html.escape(r['selection_reason'])+'</td><td>'+html.escape(r['source_name_warning'])+'</td><td>'+ ' · '.join('<a href="'+html.escape(row[k],quote=True)+'">'+label+'</a>' for k,label in [('html','Open review'),('pdf','PDF'),('outlined_pdf','Outlined PDF'),('zip','ZIP')])+'</td></tr>')
 rows_csv(root/'RUN_INDEX.csv',index)
 worksheet=[dict(run=r['run'],cell=r['cell'],source_video=r['source_video'],selection_reason=r['selection_reason'],reviewer='',first_global_frame='',last_global_frame_inclusive='',observed_issue='',raw_vs_psc='',proposed_rule_change='',decision_export_filename='',review_status='UNREVIEWED') for r in index];rows_csv(root/'REVIEW_WORKSHEET.csv',worksheet)
 title='Dyadic development pilot — 25 runs · PSC 1.5.2 · UNREVIEWED'
 (root/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>'+title+'</title><style>body{font:15px system-ui;margin:24px;max-width:1500px}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:8px;text-align:left}td:first-child{max-width:650px;overflow-wrap:anywhere}a{white-space:nowrap}</style><h1>'+title+'</h1><p>25 cells across all 12 source recordings; 7,200 inclusive frames from each TOML start. Seed 20260930. A1 and B2 of the reported recording are targeted regression cases; the other 23 choices are seeded. This is a rule-development sample, not an unbiased estimate of behavior.</p><p>Open a review, compare RAW with PSC, and export attributed decisions. Report frame numbers and the full recording/cell name. A low missingness rate does not validate inferred contact. PAPER_DATA_WRONG source-name flags are retained for provenance review.</p><p><a href="REVIEW_WORKSHEET.csv">Review worksheet</a> · <a href="RUN_INDEX.csv">Run index</a> · <a href="plan.json">Sampling manifest</a></p><table><tr><th>Recording and cell</th><th>Selection</th><th>Source-name flag</th><th>Files</th></tr>'+''.join(entries)+'</table>')
 write(root/'FILE_CHECKSUMS.json',checks)
 (root/'README.txt').write_text(title+'\nOpen START_HERE.html after extraction. Keep every HTML beside its referenced MP4. Source videos, TOMLs and IDtracker tracking are unchanged. All results are provisional for Vince’s review.\n')
 archive=root/'Dyadic_25_run_development_test_PSC1.5.2_viewer4.zip'
 if archive.exists():raise FileExistsError(archive)
 with zipfile.ZipFile(archive,'w') as z:
  for p in sorted(root.rglob('*')):
   if not p.is_file() or p==archive or any(x in p.parts for x in ['individual_run_zips','logs','__pycache__']):continue
   z.write(p,str(p.relative_to(root)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise ValueError('Bad full ZIP')
 receipt=dict(status='COMPLETE_UNREVIEWED',created_utc=utc(),run_count=25,source_recordings=12,frames_per_run=7200,psc_model_version=MODEL,processor_version=PROCESSOR,review_view_version=VIEWER,source_inputs_unchanged=True,all_encoded_frame_counts_verified=True,all_pdf_versions_verified=True,all_raw_psc_csvs_verified=True,zip_integrity_passed=True,plan_sha256=sha(root/'plan.json'),file_checksums_sha256=sha(root/'FILE_CHECKSUMS.json'),archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,total_run_bytes=sum(p.stat().st_size for p in (root/'runs').rglob('*') if p.is_file()))
 write(root/'RELEASE_RECEIPT.json',receipt);print(json.dumps(receipt,indent=2),flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['select','preflight','run','package']);p.add_argument('root',type=Path);p.add_argument('--previous',type=Path);p.add_argument('--index',type=int);a=p.parse_args()
 if a.action=='select':
  a.root.mkdir(parents=True,exist_ok=True)
  if (a.root/'plan.json').exists():raise FileExistsError(a.root/'plan.json')
  plan=select(read(a.previous));plan['previous_plan_sha256']=sha(a.previous);write(a.root/'plan.json',plan);print(json.dumps(collections.Counter(Path(r['source_video']).name for r in plan['tasks']),indent=2))
 elif a.action=='preflight':preflight(a.root)
 elif a.action=='run':run(a.root,a.index)
 else:package(a.root)
if __name__=='__main__':main()
