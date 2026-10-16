"""Read-only review of attributed CSV comments; no trajectory corrections."""
import csv, hashlib, json, os, re, shutil, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent
SOURCE=Path('/Users/New/Downloads/Manual_Review_IDtracker_20261014(20261014_dyad).csv')
OUT=ROOT/'outputs/dyadic_comment_review_20261014'
INPUT=ROOT/'outputs/psc_review_qc_20261005/runs'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def categories(s):
 s=s.lower();tags=[]
 for label,pattern in [('Centroid drift / placement',r'centroid|dot|lag|drift'),('Identity swap / duplicate',r'swap|both 0 and 1|both.*on beetle 0'),('Missing / returning ID',r'loses|lost|missing|re-assign'),('PSC timing',r'before.*contact|after.*contact|contact ends|psc ends|delay|frames.*contact ends'),('Contact / PSC definition',r'pscp|psc|social contact|proximity'),('Fungus location',r'fungus|plaster'),('Recording start',r'start time|video starts|redo toml'),('Paint / identity visibility',r'paint color')]:
  if re.search(pattern,s):tags.append(label)
 return tags or ['General review']
def parse_frames(value):
 if not value.strip():return [(None,None)]
 result=[]
 for part in value.split(';'):
  m=re.fullmatch(r'\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*',part)
  if not m:raise ValueError(value)
  a=int(m[1]);b=int(m[2] or a)
  if b<a:raise ValueError(value)
  result.append((a,b))
 return result
def main():
 OUT.mkdir(exist_ok=True,parents=True)
 for d in ['media','snapshots','sources']: (OUT/d).mkdir(exist_ok=True)
 shutil.copy2(SOURCE,OUT/'sources'/SOURCE.name)
 rows=list(csv.DictReader(SOURCE.open(newline='',encoding='utf-8-sig')))
 videos={};cases=[]
 for i,r in enumerate(rows,2):
  name=re.sub(r'(__PSC1\.6\.0|\.toml)$','',r['Video'].strip())
  if name not in videos:
   p=INPUT/name/'review';m=json.loads((p/'source_manifest.json').read_text())
   d=json.JSONDecoder().raw_decode((p/m['html']).read_text().split('const D=',1)[1])[0]
   src=p/m['video'];dest=OUT/'media'/m['video']
   if not dest.exists():os.link(src,dest)
   assert sha(src)==m['copied_video_sha256']
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate,width,height','-of','json',str(dest)]))['streams'][0]
   assert int(probe['nb_frames'])==d['end']-d['start']+1
   videos[name]=dict(data={k:d[k] for k in ['start','end','fps','raw','held','accepted','inferred','fungus','rawFungus','pairStates','rawPairStates','rois','videoGeometry']},media='media/'+m['video'],sha256=m['copied_video_sha256'],snapshot_frames=[],probe=probe)
   shutil.copy2(p/'source_manifest.json',OUT/'sources'/(name+'__source_manifest.json'))
  v=videos[name];d=v['data']
  for j,(a,b) in enumerate(parse_frames(r['Frame #']),1):
   special=a==0 and a<d['start'];target=d['start'] if a is None or special else a;end=target if special or b is None else b
   assert d['start']<=target<=end<=d['end'],(name,a,b)
   frames=sorted(set([max(d['start'],target-5),target,min(d['end'],target+5)]+([end] if end>target else [])))
   v['snapshot_frames']+=frames
   cases.append(dict(id=f'row{i:03d}_{j}',csv_row=i,run=name,original_video=r['Video'],issue=r['Issue'],original_frame=r['Frame #'],reported_frame=a,reported_end=b,target=target,end=end,initial=max(d['start'],target-5),frame_note='No frame supplied: video overview, not a located error' if a is None else 'Reported 0 means start-of-video comment; first available global frame is '+str(target) if special else 'Global frame shown in the original review HTML',reviewer=r['Reviewed/Notes by'].strip(),beetle0=r['Beetle 0'],beetle1=r['Beetle 1'],categories=categories(r['Issue']),snapshots=[dict(frame=f,path=f'snapshots/{name}__f{f}.jpg') for f in frames]))
 def snapshots(item):
  name,v=item;frames=sorted(set(v['snapshot_frames']));d=v['data'];dest=OUT/'snapshots';tmp=dest/name;tmp.mkdir(exist_ok=True)
  expr='+'.join(f'eq(n,{f-d["start"]})' for f in frames)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-i',str(OUT/v['media']),'-vf',f'select={expr.replace(",",chr(92)+",")},scale=640:460','-fps_mode','vfr','-q:v','2',str(tmp/'%04d.jpg')],check=True)
  images=sorted(tmp.glob('*.jpg'));assert len(images)==len(frames)
  for f,img in zip(frames,images):img.replace(dest/f'{name}__f{f}.jpg')
  tmp.rmdir();v['snapshot_frames']=frames
  print('Snapshots:',name,len(frames),flush=True)
 with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(snapshots,videos.items()))
 data=dict(schema='dyadic-comment-review-set-v1',version='1.0.0',source_sha256=sha(SOURCE),source_filename=SOURCE.name,frame_basis='global review HTML frames; 0 start comment mapped explicitly',reported_reviewed_videos=11,csv_distinct_runs=len(videos),source_rows=len(rows),cases=cases,videos=videos,source_url='https://www.dropbox.com/scl/fi/pcxxuuf42itc75f7kt32o/Manual_Review_IDtracker_20261014.xlsx?rlkey=notnljveggluv23xcns53x4lo&st=q6gdzlbv&dl=0',slack_url='https://formica-brodielabs.slack.com/archives/C0BKVPSFL5N/p1791993216662089')
 (OUT/'review_data.json').write_text(json.dumps(data,separators=(',',':')))
 template=(ROOT/'dyadic_comment_review.html').read_text();(OUT/'START_HERE.html').write_text(template.replace('__REVIEW_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/')))
 (OUT/'BUILD_RECEIPT.json').write_text(json.dumps(dict(status='READY_FOR_VINCE_REVIEW',source_rows=len(rows),review_cards=len(cases),distinct_videos=len(videos),snapshot_count=sum(len(v['snapshot_frames']) for v in videos.values()),source_sha256=sha(SOURCE),media_hashes_verified=True,encoded_counts_verified=True,scientific_outputs_changed=False),indent=2))
 print('Built',len(cases),'cards from',len(rows),'rows in',OUT,flush=True)
if __name__=='__main__':main()
