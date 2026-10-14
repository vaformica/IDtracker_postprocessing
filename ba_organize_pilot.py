#!/usr/bin/env python3
"""Build human-readable BA pilot indexes from inventory and release receipt."""
import csv
from collections import Counter,defaultdict
import html
import json
import random
from pathlib import Path
import sys
from urllib.parse import quote


def write_csv(path,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader();w.writerows(rows)


def organize(root):
    inv=json.loads((root/'inventory.json').read_text());receipt=json.loads((root/'RELEASE_RECEIPT.json').read_text())
    selected={r['toml']:r for r in receipt['runs']}
    all_rows=[];videos=defaultdict(list)
    for r in inv['rows']:
        p=selected.get(r['toml'],{})
        all_rows.append(dict(toml=r['toml'],video=r.get('video',''),toml_sha256=r['toml_sha256'],
            configuration_flags='; '.join(r['flags']),matched_sessions=len(r.get('sessions',[])),
            pilot_status=p.get('status','NOT_SELECTED'),pilot_flags='; '.join(p.get('flags',[]))))
        videos[r.get('video','')].append((r,p))
    write_csv(root/'TOML_INVENTORY.csv',all_rows)
    video_rows=[]
    sections=[]
    for video,items in sorted(videos.items()):
        pilots=[p for r,p in items if p]
        assessed=[p for p in pilots if p['status']=='COMPLETE_UNREVIEWED']
        video_rows.append(dict(video=video,toml_count=len(items),configuration_flagged_tomls=sum(bool(r['flags']) for r,p in items),
            pilot_selected=len(pilots),pilot_complete=len(assessed),pilot_blocked=sum(p['status']=='BLOCKED' for p in pilots),
            pilot_failed=sum(p['status']=='FAILED' for p in pilots),pilot_qc_flagged=sum(bool(p['flags']) for p in assessed)))
        if not pilots:continue
        section='<h2>'+html.escape(Path(video).name)+'</h2><ul>'
        for p in pilots:
            section+='<li><strong>'+html.escape(p['label'])+'</strong> — '+p['status']
            if p['status']=='COMPLETE_UNREVIEWED':
                relative=Path(p['output']).relative_to(root).as_posix()
                for label,target in [('Review',relative+'/review.html'),('PDF',relative+'/'+p['label']+'.pdf'),('QC',relative+'/qc.json'),('ZIP',Path(p['zip']).relative_to(root).as_posix())]:
                    section+=' · <a href="'+quote(target)+'">'+label+'</a>'
            section+='<p>'+html.escape('; '.join(p['flags']) or 'No provisional flags')+'</p>'
            if p.get('reason'):section+='<p>'+html.escape(p['reason'])+'</p>'
            section+='</li>'
        sections.append(section+'</ul>')
    write_csv(root/'VIDEO_INDEX.csv',video_rows)
    queue=[]
    rng=random.Random(inv['seed'])
    for pilot in receipt['runs']:
        if pilot['status']!='COMPLETE_UNREVIEWED':continue
        folder=Path(pilot['output'])
        with (folder/'frame_data.csv').open() as stream:frames=list(csv.DictReader(stream))
        meta=json.loads((folder/'manifest.json').read_text())
        spans=[];begin=None
        for i,row in enumerate(frames+[{'turtling_candidate':'0'}]):
            if row['turtling_candidate']=='1' and begin is None:begin=i
            elif row['turtling_candidate']=='0' and begin is not None:
                spans.append((begin,i-1,'BASELINE_CANDIDATE'));begin=None
        controls=[i for i in range(0,len(frames)-119,120)
                  if not any(r['turtling_candidate']=='1' for r in frames[i:i+120])]
        spans += [(i,i+119,'RANDOM_NONCANDIDATE') for i in rng.sample(controls,min(3,len(controls)))]
        for lo,hi,kind in sorted(spans):
            queue.append(dict(label=pilot['label'],selection=kind,
                start_global_frame=frames[lo]['global_frame'],end_global_frame_inclusive=frames[hi]['global_frame'],
                video_clip=folder.relative_to(root).as_posix()+'/review_video.mp4#t='+str(lo/meta['fps'])+','+str((hi+1)/meta['fps']),
                reviewer='',inverted_posture='',active_flailing='',notes=''))
    if queue:
        write_csv(root/'TURTLING_REVIEW_QUEUE.csv',queue)
        links=''.join('<li>'+html.escape(r['label'])+' — '+r['selection']+' — frames '+str(r['start_global_frame'])+'–'+str(r['end_global_frame_inclusive'])+' · <a href="'+html.escape(r['video_clip'],quote=True)+'">Play passage</a></li>' for r in queue)
        (root/'turtling_review.html').write_text('<!doctype html><meta charset="utf-8"><title>BA turtling review</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto}li{margin:20px 0}</style><h1>Turtling candidate and non-candidate review</h1><p>Baseline detector only. Presence in this queue is not a behavioral label. Record inverted posture and active flailing separately; use unknown when the image does not support a decision. Random controls help find missed events, but this small queue does not estimate full-dataset accuracy.</p><p><a href="TURTLING_REVIEW_QUEUE.csv">Review worksheet</a> · <a href="TURTLING_DETECTOR_REVIEW.md">Detector limitations and proposal</a></p><ul>'+links+'</ul>')
    (root/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>BA pilot</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;color:#173047}li{margin:24px 0}a{color:#076575}</style><h1>BA pilot · 7,200 frames · UNREVIEWED</h1><p>'+str(inv['toml_count'])+' TOMLs across '+str(inv['video_count'])+' source videos. Six videos sampled before QC exclusions; seed '+str(inv['seed'])+'. '+str(receipt['complete'])+' complete, '+str(receipt['blocked'])+' blocked, '+str(receipt['failed'])+' failed.</p><p>Existing tracking reprocessed with prototype BA rules. Flags invite review; they are not automatic exclusions. Old outputs are preserved.</p><p><a href="QC_INDEX.csv">Pilot QC</a> · <a href="TOML_INVENTORY.csv">All TOMLs</a> · <a href="VIDEO_INDEX.csv">Video inventory</a> · <a href="RELEASE_RECEIPT.json">Release receipt</a> · <a href="README.md">Methods and layout</a> · <a href="turtling_review.html">Turtling review queue</a></p>'+''.join(sections))
    print(json.dumps(dict(tomls=len(all_rows),videos=len(video_rows),pilot=Counter(p['status'] for p in selected.values()))))

if __name__=='__main__':organize(Path(sys.argv[1]))
