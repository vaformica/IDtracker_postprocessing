"""Exact full-frame thumbnail paths from the same arrays used by the main plot."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent/'outputs/ba_human_qc_20261013';O=R/'thumbs_v2';O.mkdir(exist_ok=True)
def path(a,c):
 out=[];prev=False
 for x,y in a:
  if x is None or y is None:prev=False;continue
  out.append(('L' if prev else 'M')+f'{(x-c[0])*500/c[2]:.3f},{(y-c[1])*500/c[3]:.3f}');prev=True
 return ' '.join(out)
for row in json.loads((R/'index.json').read_text())['runs']:
 rid=row['id'];d=json.loads((R/row['data']).read_text());q=json.loads((R/'strict_v1'/f'{rid}.json').read_text());t=json.loads((R/'turtling_v1'/f'{rid}.json').read_text())
 for mode in range(8):
  lines=[]
  for bit,a,color in [(1,d['raw'],'#a4a9ad'),(2,d['proposed'],'#008672'),(4,q['analysis'],'#008672')]:
   if mode&bit:lines.append(f'<path d="{path(a,d["crop"])}" stroke="{color}"/>')
  if mode&2:
   for i in range(1,len(d['proposed'])):
    pair=d['proposed'][i-1:i+1]
    if all(v is not None for xy in pair for v in xy) and sum((u-v)**2 for u,v in zip(*pair))>10000:
     lines.append(f'<path d="{path(pair,d["crop"])}" stroke="#d8342a"/>')
  a=q['analysis'] if mode&4 else d['proposed']
  if mode:
   for i in range(1,len(a)):
    if t['candidate_mask'][i] and a[i-1][0] is not None and a[i][0] is not None and sum((u-v)**2 for u,v in zip(a[i-1],a[i]))<10000:
     lines.append(f'<path d="{path(a[i-1:i+1],d["crop"])}" stroke="#a32dc4" stroke-width="3"/>')
  (O/f'{rid}_{mode}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" preserveAspectRatio="none"><g fill="none" stroke-width="1">'+''.join(lines)+'</g></svg>')
print('100 exact-coordinate thumbnails in eight display modes')
