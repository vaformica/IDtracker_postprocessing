"""Add review-only QC guidance to frozen PSC 1.6.0 results; no science recomputation."""
from pathlib import Path
import argparse,csv,hashlib,html,json,math,os,shutil,zipfile
import numpy as np
VERSION='review-qc-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,s):
 p=Path(p)
 if p.exists():p.unlink() # detach any hardlinked source before editing
 p.write_text(s)
def dump(p,x):write(p,json.dumps(x,indent=2)+'\n')
def bouts(mask):
 edges=np.diff(np.r_[False,mask,False].astype(int));return list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)-1))
def calculate(n,start,fps):
 raw=n['raw'];present=np.isfinite(raw).all(axis=2);events=[];nframes,animals=present.shape;exact_jumps=[]
 def event(kind,a,lo,hi,detail,dist=None,prev=None):
  events.append(dict(kind=kind,animal_id=a,first_global_frame=int(start+lo),last_global_frame_inclusive=int(start+hi),frames=int(hi-lo+1),distance_px='' if dist is None else round(float(dist),3),previous_global_frame='' if prev is None else int(start+prev),detail=detail))
 for a in range(animals):
  seen=np.flatnonzero(present[:,a])
  for prev,t in zip(seen[:-1],seen[1:]):
   d=np.linalg.norm(raw[t,a]-raw[prev,a])
   if t-prev==1 and d>100:exact_jumps.append(float(d))
   if d>100:event('RAW_JUMP' if t-prev==1 else 'DISTANT_RETURN',a,t,t,'Adjacent-frame displacement' if t-prev==1 else f'Return after {t-prev-1} missing frames; not a one-frame speed',d,prev)
  for kind,mask in [('LONG_MISSING_ID',~present[:,a]),('LONG_PSC',n['inferred'][:,a]),('AMBIGUOUS',n['ambiguous'][:,a]),('IDENTITY_CONFLICT',n['identity_conflict'][:,a])]:
   for lo,hi in bouts(mask):
    if kind.startswith('LONG') and hi-lo+1<math.ceil(fps):continue
    event(kind,a,lo,hi,{'LONG_MISSING_ID':'Raw ID absent for at least 1 second; may be an ordinary occlusion','LONG_PSC':'Inferred position for at least 1 second; check partner and entry/exit','AMBIGUOUS':'Processor flagged ambiguity; not proof of a swap','IDENTITY_CONFLICT':'Processor flagged an identity conflict'}[kind])
 events.sort(key=lambda e:(e['first_global_frame'],e['animal_id'],e['kind']))
 counts={k:sum(e['kind']==k for e in events) for k in ['RAW_JUMP','DISTANT_RETURN','LONG_MISSING_ID','LONG_PSC','AMBIGUOUS','IDENTITY_CONFLICT']}
 jumps=[e for e in events if e['kind']=='RAW_JUMP']
 summary=dict(raw_jumps_over_100=counts['RAW_JUMP'],raw_jumps_over_200=sum(e['distance_px']>200 for e in jumps),max_raw_jump_px=max([e['distance_px'] for e in jumps],default=0),distant_returns_over_100=counts['DISTANT_RETURN'],long_missing_bouts=counts['LONG_MISSING_ID'],long_psc_bouts=counts['LONG_PSC'],ambiguous_bouts=counts['AMBIGUOUS'],identity_conflict_bouts=counts['IDENTITY_CONFLICT'],raw_missing_percent=round(float((~present).mean()*100),2),inferred_percent=round(float(n['inferred'].mean()*100),2),unresolved_percent=round(float((~np.isfinite(n['xy']).all(axis=2)).mean()*100),2))
 summary['raw_jumps_over_200']=sum(d>200 for d in exact_jumps)
 return summary,events
STYLE='<style>body{font:16px system-ui;margin:24px;color:#172a38;line-height:1.5;background:#f8fafb}h1{font-size:26px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #ccd5dc;padding:9px;text-align:left}th{background:#e6edf2;position:sticky;top:0}td.name{max-width:390px;overflow-wrap:anywhere}.flag{font-weight:700;color:#a32219}.note{background:#fff0d0;padding:14px;border-radius:8px}input,select{font:inherit;padding:8px;margin:6px}a{color:#125795}summary{cursor:pointer}small{color:#4e606c}</style>'
GUIDE='''<div class="note"><b>Human review required · all results UNREVIEWED.</b> Counts prioritize inspection; they do not prove tracking errors. No flags does not establish correct IDs. Jumps use raw centroids in original-video pixels, before PSC. <b>&gt;100 px</b> means one adjacent-frame step; <b>&gt;200 px</b> is a subset. A distant return is measured across missing frames and is not a speed violation. Missing/PSC bouts below are at least one second. PSC and missingness can be expected during real contact. Counts are per beetle/episode, so overlapping warnings must not be added as independent errors. Raw missing, inferred and unresolved percentages use animal-frames; inferred/unresolved are subsets of raw missing.</div>'''
def page(title,body):return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title>'+STYLE+'<h1>'+html.escape(title)+'</h1>'+body+'</html>'
def csvwrite(p,rows):
 with open(p,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def portal(rows,remote=False):
 entries=[]
 for r in sorted(rows,key=lambda r:(r['collection']!='six_beetle',-r['raw_jumps_over_100'],-r['raw_missing_percent'],r['run'])):
  link=r.get('download_url','individual_run_zips/'+r['filename']) if remote else 'runs/'+r['run']+'/START_HERE.html'
  entries.append('<tr data-collection="'+r['collection']+'"><td>'+r['collection']+'</td><td class="name">'+html.escape(r['run'])+'</td><td class="'+('flag' if r['raw_jumps_over_100'] else '')+'">'+str(r['raw_jumps_over_100'])+' / '+str(r['raw_jumps_over_200'])+'</td><td>'+str(r['distant_returns_over_100'])+'</td><td>'+str(r['raw_missing_percent'])+'% / '+str(r['long_missing_bouts'])+'</td><td>'+str(r['long_psc_bouts'])+'</td><td>'+str(r['ambiguous_bouts'])+' / '+str(r['identity_conflict_bouts'])+'</td><td><a href="'+html.escape(link,quote=True)+'">'+('Download ZIP' if remote else 'Warnings &amp; files')+'</a></td></tr>')
 body=GUIDE+'<p>PSC 1.6.0 / processor 0.8.2-group · '+VERSION+' · '+str(len(rows))+' cases. Six-beetle trials first, then descending jump count. Source video/TOML cell names are preserved.</p><p>Download and unzip a case, then open its START_HERE.html. Its warning table opens the review video at the flagged global frame. Existing PDFs and scientific CSVs are unchanged; QC summaries are separate.</p><p><a href="QC_RUN_INDEX.csv">Warning summary CSV</a></p><input id="search" placeholder="Search video or cell" aria-label="Search cases"><select id="collection" aria-label="Collection"><option value="">All collections</option><option>six_beetle</option><option>dyadic</option></select><table><thead><tr><th>Collection</th><th>Video / cell</th><th>Jumps &gt;100 / &gt;200</th><th>Distant returns</th><th>Raw missing % / long bouts</th><th>Long PSC bouts</th><th>Ambiguous / conflict bouts</th><th>Open</th></tr></thead><tbody>'+''.join(entries)+'</tbody></table><script>function filter(){for(const r of document.querySelectorAll("tbody tr"))r.hidden=!r.textContent.toLowerCase().includes(document.getElementById("search").value.toLowerCase())||!!document.getElementById("collection").value&&r.dataset.collection!==document.getElementById("collection").value}document.getElementById("search").oninput=filter;document.getElementById("collection").onchange=filter;</script>'
 return page('Beetle reviews — warning-guided downloads',body)
def build(source,out):
 source,out=Path(source),Path(out);out.mkdir(exist_ok=False,parents=True);(out/'runs').mkdir();(out/'individual_run_zips').mkdir();index=list(csv.DictReader((source/'RUN_INDEX.csv').open()));results=[]
 for r in index:
  name=r['run'];src=source/'runs'/name;dst=out/'runs'/name;shutil.copytree(src,dst,copy_function=os.link)
  meta=json.loads((src/'analysis/manifest.json').read_text());rm=json.loads((src/'review/source_manifest.json').read_text());canonical=src/'analysis/canonical_states.npz'
  assert sha(canonical)==rm['canonical_sha256'];assert sha(src/'analysis/manifest.json')==rm['analysis_manifest_sha256']
  with np.load(canonical) as n:summary,events=calculate(n,int(r['first_global_frame']),rm['fps'])
  summary.update(run=name,collection=r['collection'],frames=int(r['frames']),first_global_frame=int(r['first_global_frame']),last_global_frame_inclusive=int(r['last_global_frame_inclusive']),qc_version=VERSION,review_status='UNREVIEWED')
  dump(dst/'QC_SUMMARY.json',summary);dump(dst/'QC_EVENTS.json',events)
  if events:csvwrite(dst/'QC_EVENTS.csv',events)
  else:write(dst/'QC_EVENTS.csv','kind,animal_id,first_global_frame,last_global_frame_inclusive,frames,distance_px,previous_global_frame,detail\n')
  viewer=dst/'review'/rm['html'];original_hash=sha(viewer)
  injection='''<script>/* Review-only frame deep links; scientific arrays unchanged. */
(function(){function openQCFrame(){const m=location.hash.match(/^#frame=(\\d+)$/);if(m){const f=Number(m[1]);if(f>=D.start&&f<=D.end)seek(f)}}if(v.readyState>=1)openQCFrame();else v.addEventListener('loadedmetadata',openQCFrame,{once:true});window.addEventListener('hashchange',openQCFrame)})();</script>'''
  write(viewer,viewer.read_text()+injection)
  links=' · '.join('<a href="'+html.escape(str(Path(r[k]).relative_to(Path('runs')/name)),quote=True)+'">'+label+'</a>' for k,label in [('html','Open review'),('video','Video'),('pdf','PDF'),('outlined_pdf','Outlined PDF'),('csv','Scientific CSVs')])
  rows=[]
  for e in events:
   href='review/'+rm['html']+'#frame='+str(e['first_global_frame']);rows.append('<tr><td>'+e['kind']+'</td><td>'+str(e['animal_id'])+'</td><td><a href="'+href+'">'+str(e['first_global_frame'])+'–'+str(e['last_global_frame_inclusive'])+'</a></td><td>'+str(e['distance_px'])+'</td><td>'+html.escape(e['detail'])+'</td></tr>')
  body=GUIDE+'<p>'+links+'</p><p><b>'+str(summary['raw_jumps_over_100'])+' raw jumps &gt;100 px ('+str(summary['raw_jumps_over_200'])+' &gt;200 px)</b> · '+str(summary['distant_returns_over_100'])+' distant returns · '+str(summary['raw_missing_percent'])+'% raw missing · '+str(summary['inferred_percent'])+'% inferred · '+str(summary['unresolved_percent'])+'% unresolved.</p><p><a href="QC_EVENTS.csv">Warning events CSV</a> · <a href="QC_SUMMARY.json">QC summary</a></p><p>Click a frame range to inspect its beginning. Check the frames before and after it as well. IDs are zero-based as in the review viewer.</p><table><tr><th>Warning</th><th>ID</th><th>Global frames</th><th>Distance px</th><th>Why inspect</th></tr>'+''.join(rows)+'</table>'
  write(dst/'START_HERE.html',page(name+' — review warnings',body))
  dump(dst/'QC_PROVENANCE.json',dict(qc_version=VERSION,canonical_sha256=sha(canonical),source_manifest_sha256=sha(src/'analysis/manifest.json'),original_review_html_sha256=original_hash,qc_review_html_sha256=sha(viewer),science_unchanged=True,change='Added QC sidecars/index and frame deep links only; source_manifest describes original viewer generation.'))
  checks={str(p.relative_to(dst)):sha(p) for p in dst.rglob('*') if p.is_file()};dump(dst/'QC_FILE_CHECKSUMS.json',checks)
  filename=name+'__PSC1.6.0_QCwarnings_v1.zip';zpath=out/'individual_run_zips'/filename
  with zipfile.ZipFile(zpath,'w') as z:
   for p in dst.rglob('*'):
    if p.is_file():z.write(p,str(p.relative_to(dst.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
  with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
  summary.update(filename=filename,zip_sha256=sha(zpath),zip_bytes=zpath.stat().st_size);results.append(summary);print(name,summary['raw_jumps_over_100'],flush=True)
 dump(out/'QC_RUN_INDEX.json',results);csvwrite(out/'QC_RUN_INDEX.csv',results);write(out/'START_HERE.html',portal(results));dump(out/'QC_RELEASE_RECEIPT.json',dict(status='COMPLETE_UNREVIEWED',qc_version=VERSION,run_count=len(results),source=str(source.resolve()),script_sha256=sha(__file__),all_canonical_hashes_verified=True,all_zip_integrity_passed=True,science_recomputed=False))
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('output');a=p.parse_args();build(a.source,a.output)
