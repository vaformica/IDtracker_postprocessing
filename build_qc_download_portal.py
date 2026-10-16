"""Bind verified Dropbox upload receipts to the warning-guided download index."""
import json,html
from pathlib import Path
from build_review_qc_packages import portal, csvwrite, dump, write, sha

def build(root):
 root=Path(root); rows=json.loads((root/'QC_RUN_INDEX.json').read_text())
 uploads=json.loads((root/'QC_UPLOAD_RESULTS.json').read_text())
 by_run={x['run']:x for x in uploads}
 assert len(by_run)==len(uploads)==len(rows)==51
 for row in rows:
  uploaded=by_run[row['run']]
  assert not uploaded.get('error'), uploaded
  assert uploaded['file']['file']['size']==row['zip_bytes'], row['run']
  assert uploaded['link']['allow_download'] and uploaded['link']['access_level']=='view'
  assert uploaded['link']['audience']=='no_one'
  row['download_url']=uploaded['link']['url']
 out=root/'dropbox_portal';out.mkdir(exist_ok=True)
 csvwrite(out/'QC_RUN_INDEX.csv',rows)
 dump(out/'QC_SHARING_MANIFEST.json',dict(status='COMPLETE_UNREVIEWED',run_count=len(rows),science_version='PSC 1.6.0 / processor 0.8.2-group',qc_version='review-qc-v1',uploads=uploads,packages=rows))
 index_html=portal(rows,remote=True)
 csv_link_file=root/'QC_CSV_LINK.json'
 if csv_link_file.exists():
  csv_url=json.loads(csv_link_file.read_text())['url']
  index_html=index_html.replace('href="QC_RUN_INDEX.csv"','href="'+html.escape(csv_url,quote=True)+'"')
 write(out/'START_HERE.html',index_html)
 write(out/'QC_READ_ME_FIRST.txt','Download START_HERE.html and open it in your browser. Select a case ZIP, unzip it, and open the START_HERE.html inside that case folder. Warning frame links open the review at the flagged global frame. All outputs remain UNREVIEWED. QCwarnings_v1 packages contain the current warning guidance; earlier ZIPs and START_HERE_before_QCwarnings_20261005.html are retained as history. Scientific files are unchanged.\n')
 dump(out/'PORTAL_CHECKSUMS.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='PORTAL_CHECKSUMS.json'})
 return out

if __name__=='__main__':
 import sys
 print(build(sys.argv[1]))
