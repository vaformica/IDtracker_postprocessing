"""Encode scoped review clips and package portable BA scoring rounds."""
from pathlib import Path
import json,sys,subprocess,hashlib,base64,html,csv,zipfile
from ba_large_pilot import load,save,sha,permit,probe,FF
FIELDS=['id','label','start','end','frames','fps','mode','suggestions','not_eligible_ranges','tracking_uncertain_ranges']
def public_clip(c):return {f:c[f] for f in FIELDS}
def scorer(template,clips,media,set_id,filename,instructions):
 public=[public_clip(c) for c in clips];encoded=json.dumps(public,separators=(',',':'));setting=dict(id=set_id,cohort_id='ba-large-review-20261007',public_clips_sha256=hashlib.sha256(encoded.encode()).hexdigest(),export_filename=filename,instructions=instructions)
 text=template.replace('__SET__',json.dumps(setting)).replace('__CLIPS__',encoded).replace('__MEDIA__',json.dumps(media,separators=(',',':')))
 assert '__SET__' not in text and '__MEDIA__' not in text
 return text,setting

def package(root):
 sys.path.insert(0,str(root/'vendor'));from pypdf import PdfReader,PdfWriter
 queue=load(root/'REVIEW_QUEUE.json');index=load(root/'ANALYSIS_INDEX.json');runs={r['id']:r for r in index['runs'] if r['status']=='ANALYSIS_COMPLETE_UNREVIEWED'}
 review=root/'review_v2';review.mkdir(exist_ok=True);(review/'pdfs').mkdir(exist_ok=True);(root/'clips_v2').mkdir(exist_ok=True);(root/'individual_run_zips_v2').mkdir(exist_ok=True)
 template=(root/'ba_large_review_template.html').read_text();media={};clip_receipts=[];pdfs=[];full_receipts=[]
 for rid,s in runs.items():
  run=root/'runs_v2'/rid;v=load(run/'VIDEO_RECEIPT.json');assert sha(run/'review_video.mp4')==v['sha256']
  for n,h in s['analysis_output_sha256'].items():assert sha(run/n)==h,(rid,n)
  if s['pdf_name']:
   dst=review/'pdfs'/s['pdf_name'];dst.write_bytes((run/s['pdf_name']).read_bytes());pdfs.append(dict(id=rid,path=str(dst.relative_to(review)),sha256=sha(dst)))
  pred=load(run/'predictions.json');g=pred['gate']
  with (run/'frame_data.csv').open(newline='') as f:frame_rows=list(csv.DictReader(f))
  assert len(frame_rows)==7200 and [int(f['global_frame']) for f in frame_rows]==list(range(s['start'],s['end']+1))
  assert [f['frozen_turtling_candidate']=='True' for f in frame_rows]==g['candidate_mask']
  save(run/'PILOT_CONTEXT.json',dict(pilot_version=s['pilot_version'],driver_sha256=load(root/'DRIVER_SHA256.json'),frozen_modules=load(root/'CODE_SHA256.json'),settings=dict(frame_count=7200,movement_threshold_px=30,wall_buffer_px=30,rejected_jump_threshold_px=200),episode_rules=pred['episode']['rules'],gate_parameters={k:g[k] for k in ['version','distance_px','hold_seconds','hold_frames','max_step_px','initial_camera_artifact_frames']},review_status='UNREVIEWED',confirmed_overturned_seconds=None))
  from ba_large_review_prepare import spans
  full=dict(id=rid+'_full',label=rid.upper()+' / '+Path(s['toml']).stem.split('_')[-1],start=s['start'],end=s['end'],frames=7200,fps=30,mode='guided',suggestions=spans(g['candidate_mask'],s['start']),not_eligible_ranges=spans([not x for x in g['eligible_mask']],s['start']),tracking_uncertain_ranges=spans([x in ['tracking_uncertain','camera_reference_unconfirmed'] for x in g['state']],s['start']))
  data,setting=scorer(template,[full],{full['id']:'data:video/mp4;base64,'+base64.b64encode((run/'review_video.mp4').read_bytes()).decode()},'ba-large-full-'+rid+'-20261007','BA_'+rid+'_full_scores_20261007.json','Full run: watch the complete displayed run before saving a whole-run decision. Use the short review rounds for targeted checks.')
  (run/'review_marked_v2.html').write_text(data)
  paths={n:run/n for n in [*s['analysis_output_sha256'],'manifest.json','review_video.mp4','VIDEO_RECEIPT.json','PILOT_CONTEXT.json']};paths['review.html']=run/'review_marked_v2.html';manifest={name:sha(path) for name,path in paths.items()};save(run/'BUNDLE_HASHES_v2.json',manifest)
  z=root/'individual_run_zips_v2'/(rid+'.zip')
  with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as f:
   for name,path in paths.items():f.write(path,arcname=name)
   f.write(run/'BUNDLE_HASHES_v2.json',arcname='BUNDLE_HASHES.json')
  with zipfile.ZipFile(z) as f:assert f.testzip() is None
  full_receipts.append(dict(id=rid,video_sha256=v['sha256'],video_frames=int(v['stream']['nb_read_frames']),viewer_sha256=sha(run/'review_marked_v2.html'),zip_sha256=sha(z),zip_bytes=z.stat().st_size))
 book=PdfWriter();page=1
 for entry in pdfs:
  entry['book_start_page']=page;reader=PdfReader(review/entry['path']);entry['pages']=len(reader.pages);book.append(reader,outline_item=entry['id'].upper());page+=len(reader.pages)
 with (review/'BA_Pilot_100_Reports.pdf').open('wb') as f:book.write(f)
 assert len(PdfReader(review/'BA_Pilot_100_Reports.pdf').pages)==page-1
 for c in queue['clips']:
  s=runs[c['source_id']];source=root/'runs_v2'/s['id']/'review_video.mp4';out=root/'clips_v2'/(c['id']+'.mp4');assert not out.exists(),out
  if c['start']==s['start'] and c['frames']==7200:out.write_bytes(source.read_bytes())
  else:
   offset=c['start']-s['start'];seconds=offset//30;residual=offset%30;vf=f"trim=start_frame={residual}:end_frame={residual+c['frames']},setpts=PTS-STARTPTS"
   subprocess.run([FF,'-v','error','-nostdin','-ss',str(seconds),'-i',str(source),'-vf',vf,'-frames:v',str(c['frames']),'-an','-c:v','libx264','-threads','2','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
  st=probe(out,True);assert int(st['nb_read_frames'])==c['frames'] and st['avg_frame_rate']=='30/1' and abs(float(st['duration'])-c['frames']/30)<.001
  b=out.read_bytes();digest=hashlib.sha256(b).hexdigest();media[c['id']]='data:video/mp4;base64,'+base64.b64encode(b).decode();clip_receipts.append(dict(id=c['id'],source_id=s['id'],start=c['start'],end=c['end'],frames=c['frames'],sha256=digest,source_video_sha256=load(source.with_name('VIDEO_RECEIPT.json'))['sha256'],stream=st));print('CLIP_VERIFIED',c['id'],flush=True)
 round_receipts=[]
 for i,ids in enumerate(queue['rounds'],1):
  clips=[next(c for c in queue['clips'] if c['id']==cid) for cid in ids];seconds=sum(c['frames']/30 for c in clips);name=f'ROUND_{i:02d}.html'
  text,setting=scorer(template,clips,{cid:media[cid] for cid in ids},f'ba-large-review-20261007-round-{i:02d}',f'BA_large_review_round_{i:02d}_scores_20261007.json',f'Round {i} of {len(queue["rounds"])}: {len(clips)} clips, {seconds/60:.1f} minutes of video. Download this round’s scores when finished.')
  (review/name).write_text(text);round_receipts.append(dict(round=i,path=name,clips=ids,viewing_seconds=seconds,scoring_set=setting,sha256=sha(review/name),bytes=(review/name).stat().st_size))
 create_index(review,index,round_receipts,pdfs)
 save(root/'RELEASE_RECEIPT_v2.json',dict(status='COMPLETE_UNREVIEWED',stats=queue['stats'],full_run_bundles=full_receipts,pdfs=pdfs,review_clips=clip_receipts,rounds=round_receipts,report_book_sha256=sha(review/'BA_Pilot_100_Reports.pdf'),report_book_pages=page-1,confirmed_overturned_seconds=None,detector_rules_changed=False,dyadic_tests='DEFERRED',browser_playback_tested=False))
 for p in [root,*root.rglob('*')]:permit(p)
 print('PACKAGE_COMPLETE',len(full_receipts),'full bundles',len(round_receipts),'review rounds',flush=True)
def create_index(review,index,rounds,pdfs):
 esc=html.escape;stats=index['stats']
 buttons=''.join(f'<a class="round" href="{r["path"]}">Open round {r["round"]} <small>{len(r["clips"])} clips · {r["viewing_seconds"]/60:.1f} minutes</small></a>' for r in rounds)
 rows=[]
 for s in index['runs']:
  if s['cohort']!='new_run_pilot':continue
  good=s['status']=='ANALYSIS_COMPLETE_UNREVIEWED';page=next((p['book_start_page'] for p in pdfs if p['id']==s['id']),1);pdf=f'<a href="BA_Pilot_100_Reports.pdf#page={page}">PDF</a>' if good else '—'
  if s.get('blind_full_run'):pdf='After scoring the blinded clip'
  rows.append('<tr><td>'+esc(s['id'].upper())+'</td><td>'+esc(Path(s['toml']).stem)+'</td><td>'+('Hidden for review' if s.get('blind_full_run') else (f'{s["candidate_seconds"]:.2f}' if good else '—'))+'</td><td>'+esc('Hidden for review' if s.get('blind_full_run') else ('; '.join(s.get('qc_flags',[])) or ('No threshold flags' if good else s.get('reason','Blocked'))))+'</td><td>'+pdf+'</td></tr>')
 text=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BA pilot: start review</title><style>body{{font:17px system-ui;max-width:1100px;margin:30px auto;padding:0 20px;color:#203047;background:#f3f6f8}}h1{{font-size:30px}}.round{{display:inline-block;background:#126e65;color:white;padding:16px 22px;margin:8px 12px 8px 0;border-radius:8px;text-decoration:none}}small{{display:block}}table{{border-collapse:collapse;font-size:13px;width:100%;background:white}}th,td{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}td:nth-child(2){{overflow-wrap:anywhere}}.note{{background:white;padding:16px;border-radius:8px}}input{{font:inherit;padding:10px;width:70%}}a{{color:#126e65}}</style><h1>BA pilot: marked video review</h1><p>{stats['completed_new_runs']} of 100 selected new runs analyzed across {stats['source_recordings']} recordings. {stats['new_runs_with_candidates']} have suggested turtling; {stats['new_runs_with_qc_flags']} have QC flags. These remain automatic suggestions.</p><div class="note"><b>Start with round 1.</b> Each file contains its videos. Pause, step by frame, and choose Correct, No turtling, Adjust, or Unsure. Download the scores at the end of each round and attach them in the chat. You can stop after any round.<p>Some complete runs hide predictions to check for missed events. Short scenes confirm only their displayed frames. Include quiet time on the back; flailing does not need separate scoring.</p></div><div>{buttons}</div><p>Planned video viewing: {sum(r['viewing_seconds'] for r in rounds)/60:.1f} minutes across all rounds, plus time for adjustments. You do not need to watch all 100 complete videos.</p><details><summary>Browse all 100 runs and PDFs</summary><p><b>Score the four complete clips with predictions hidden before browsing reports.</b> The PDF collection includes their predictions.</p><p>Suggested seconds are provisional; zero is not a confirmed absence of turtling. QC flags invite inspection and are not exclusion rules.</p><input id="filter" placeholder="Find a run, recording or QC flag"><table><thead><tr><th>Run</th><th>Recording / cell</th><th>Suggested seconds</th><th>QC / status</th><th>Report</th></tr></thead><tbody>{''.join(rows)}</tbody></table></details><script>document.getElementById('filter').oninput=e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}}</script></html>'''
 (review/'START_HERE.html').write_text(text)
if __name__=='__main__':package(Path(sys.argv[1]))
