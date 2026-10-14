"""Package a frozen BA review selection as a portable, self-contained scorer."""
from pathlib import Path
import argparse,base64,hashlib,json,subprocess

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--ffprobe',default='ffprobe');a=p.parse_args();r=a.root
 key=json.loads((r/'selection_key.json').read_text());public=[];media={};checks=[]
 for c in key['clips']:
  q={k:c[k] for k in ['id','start','end','frames','fps','mode','suggestions']}
  assert q['end']-q['start']+1==q['frames']
  if q['mode']=='blind':assert not q['suggestions']
  for lo,hi in q['suggestions']:assert q['start']<=lo<=hi<=q['end']
  path=r/'clips'/(c['id']+'.mp4');b=path.read_bytes();record=json.loads((r/'encoded'/(c['id']+'.json')).read_text());assert record['clip']==c and record['sha256']==sha(b)
  st=json.loads(subprocess.check_output([a.ffprobe,'-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,avg_frame_rate,codec_name,duration,width,height','-of','json',str(path)]))['streams'][0]
  assert int(st['nb_read_frames'])==c['frames'] and st['avg_frame_rate']=='30/1' and st['codec_name']=='h264'
  assert abs(float(st['duration'])-c['frames']/c['fps'])<.001
  source=next(s for s in key['sources'] if s['id']==c['source_id']);assert [st['width'],st['height']]==source['crop'][2:]
  public.append(q);media[c['id']]='data:video/mp4;base64,'+base64.b64encode(b).decode();checks.append(dict(id=c['id'],sha256=sha(b),bytes=len(b),stream=st))
 serialized=json.dumps(public,separators=(',',':'))
 setting=dict(id=key['plan']['id'],public_clips_sha256=sha(serialized.encode()),export_filename='BA_quick_review_scores_20261006.json')
 template=Path(__file__).with_name('ba_turtling_quick_review_template.html').read_text()
 html=template.replace('__SET__',json.dumps(setting)).replace('__CLIPS__',serialized).replace('__MEDIA__',json.dumps(media,separators=(',',':')))
 assert not any(x in html for x in ['__SET__','__CLIPS__','__MEDIA__'])
 review=r/'review';review.mkdir(exist_ok=True);out=review/'START_HERE.html';out.write_text(html)
 (r/'PUBLIC_CLIPS.json').write_text(serialized+'\n')
 receipt=dict(status='READY_FOR_HUMAN_REVIEW_UNVALIDATED',selection_key_sha256=sha((r/'selection_key.json').read_bytes()),template_sha256=sha(template.encode()),scoring_set=setting,clips=checks,frame_count=sum(c['frames'] for c in public),viewing_seconds=sum(c['frames']/c['fps'] for c in public),html_sha256=sha(out.read_bytes()),html_bytes=out.stat().st_size,encoded_checks='all frame counts, FPS, duration, crop dimensions and file hashes passed',browser_playback_tested=False)
 (r/'PACKAGING_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','frame_count','viewing_seconds','html_bytes','html_sha256']},indent=2))
if __name__=='__main__':main()
