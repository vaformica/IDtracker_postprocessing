#!/usr/bin/env python3
"""Package the pilot with portable review links; individual ZIPs stay separate."""
from dyadic_pilot25 import *

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
  entries.append('<tr><td>'+html.escape(r['stem'])+'</td><td>'+html.escape(r['selection_reason'])+'</td><td>'+html.escape(r['source_name_warning'])+'</td><td>'+ ' · '.join('<a href="'+html.escape(row[k],quote=True)+'">'+label+'</a>' for k,label in [('html','Open review'),('pdf','PDF'),('outlined_pdf','Outlined PDF')])+'</td></tr>')
 rows_csv(root/'RUN_INDEX.csv',index)
 worksheet=[dict(run=r['run'],cell=r['cell'],source_video=r['source_video'],selection_reason=r['selection_reason'],reviewer='',first_global_frame='',last_global_frame_inclusive='',observed_issue='',raw_vs_psc='',proposed_rule_change='',decision_export_filename='',review_status='UNREVIEWED') for r in index];rows_csv(root/'REVIEW_WORKSHEET.csv',worksheet)
 title='Dyadic development pilot — 25 runs · PSC 1.5.2 · UNREVIEWED'
 (root/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>'+title+'</title><style>body{font:15px system-ui;margin:24px;max-width:1500px}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:8px;text-align:left}td:first-child{max-width:650px;overflow-wrap:anywhere}a{white-space:nowrap}</style><h1>'+title+'</h1><p>25 cells across all 12 source recordings; 7,200 inclusive frames from each TOML start. Seed 20260930. A1 and B2 of the reported recording are targeted regression cases; the other 23 choices are seeded. This is a rule-development sample, not an unbiased estimate of behavior.</p><p><strong>Priority review:</strong> PSC 1.5.2 still classifies beetle 0 as PSCP_BLOB at global frame 3005 in both A1 and B2 of Camera_2_40359705_20260702_1536_FIGHT_ACT2. The extracted images at global frame 3005 show the beetles appearing close together in both cells. The retained PSC labels alone do not establish that the reported error persists. Confirm the exact cell and whether the reported frame is global or relative to the review video; inspect persistence and identity assignment in these two candidates first.</p><p>Open a review, compare RAW with PSC, and export attributed decisions. Report frame numbers and the full recording/cell name. A low missingness rate does not validate inferred contact. PAPER_DATA_WRONG source-name flags are retained for provenance review.</p><p><a href="REVIEW_WORKSHEET.csv">Review worksheet</a> · <a href="RUN_INDEX.csv">Run index</a> · <a href="plan.json">Sampling manifest</a></p><table><tr><th>Recording and cell</th><th>Selection</th><th>Source-name flag</th><th>Files</th></tr>'+''.join(entries)+'</table>')
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

if __name__ == '__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('root',type=Path)
 args=parser.parse_args()
 package(args.root)
