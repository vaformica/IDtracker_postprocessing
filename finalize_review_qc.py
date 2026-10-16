from pathlib import Path
import sys,json,zipfile,os
from build_review_qc_packages import sha,dump,write,csvwrite,portal
INJECTION='''<script>/* Review-only frame deep links; scientific arrays unchanged. */
(function(){function openQCFrame(){const m=location.hash.match(/^#frame=(\\d+)$/);if(m){const f=Number(m[1]);if(f>=D.start&&f<=D.end)seek(f)}}if(v.readyState>=1)openQCFrame();else v.addEventListener('loadedmetadata',openQCFrame,{once:true});window.addEventListener('hashchange',openQCFrame)})();</script>'''
root=Path(sys.argv[1]);rows=json.loads((root/'QC_RUN_INDEX.json').read_text())
for r in rows:
 case=root/'runs'/r['run'];v=next((case/'review').glob('*__interaction_review.html'))
 if 'Review-only frame deep links' not in v.read_text():write(v,v.read_text()+INJECTION)
 p=case/'QC_PROVENANCE.json';d=json.loads(p.read_text());d['qc_review_html_sha256']=sha(v);dump(p,d)
 p=case/'QC_FILE_CHECKSUMS.json';d=json.loads(p.read_text());d[str(v.relative_to(case))]=sha(v);d['QC_PROVENANCE.json']=sha(case/'QC_PROVENANCE.json');dump(p,d)
 zpath=root/'individual_run_zips'/r['filename'];tmp=zpath.with_suffix('.tmp')
 with zipfile.ZipFile(tmp,'w') as z:
  for p in case.rglob('*'):
   if p.is_file():z.write(p,str(p.relative_to(case.parent)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
 os.replace(tmp,zpath);r['zip_sha256']=sha(zpath);r['zip_bytes']=zpath.stat().st_size
 print(r['run'],flush=True)
dump(root/'QC_RUN_INDEX.json',rows);csvwrite(root/'QC_RUN_INDEX.csv',rows);write(root/'START_HERE.html',portal(rows));p=root/'QC_RELEASE_RECEIPT.json';d=json.loads(p.read_text());d['script_sha256']=sha(Path(__file__).with_name('build_review_qc_packages.py'));d['frame_link_repair_sha256']=sha(__file__);dump(p,d)
