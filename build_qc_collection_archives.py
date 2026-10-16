from pathlib import Path
import json,sys,zipfile,io,csv
from build_review_qc_packages import portal,sha,dump
root=Path(sys.argv[1]);rows=json.loads((root/'QC_RUN_INDEX.json').read_text());archives=[]
for collection in ['dyadic','six_beetle']:
 selected=[r for r in rows if r['collection']==collection];p=root/(collection+'__PSC1.6.0_QCwarnings_v1__review_bundle.zip')
 with zipfile.ZipFile(p,'w') as z:
  for r in selected:
   for f in (root/'runs'/r['run']).rglob('*'):
    if f.is_file():z.write(f,str(f.relative_to(root)),compress_type=zipfile.ZIP_STORED if f.suffix in ['.mp4','.pdf','.npz'] else zipfile.ZIP_DEFLATED)
  z.writestr('START_HERE.html',portal(selected));buf=io.StringIO();w=csv.DictWriter(buf,list(selected[0]));w.writeheader();w.writerows(selected);z.writestr('QC_RUN_INDEX.csv',buf.getvalue())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
 archives.append(dict(collection=collection,filename=p.name,sha256=sha(p),bytes=p.stat().st_size));print(archives[-1],flush=True)
dump(root/'QC_COLLECTION_ARCHIVES.json',archives)
