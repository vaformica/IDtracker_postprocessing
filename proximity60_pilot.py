"""Codex/AI development pilot: local 60-pixel entries/exits, not intent."""
from pathlib import Path
import json, itertools, hashlib, re, shutil
import numpy as np
from encounter_orientation_pilot import clean, bouts
BASE=Path(__file__).resolve().parent
OLD=BASE/'outputs/encounter_orientation_pilot_20261009/review_set'
OUT=BASE/'outputs/proximity60_pilot_20261012/review_set'
CANON=BASE/'outputs/psc_regenerated_51_20261005/review_set/runs'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def episodes(distance, psc, length, fps):
    """Entry <=60 px or PSC; exit confirmed >60 px for .2s; unknown splits."""
    known=np.isfinite(distance)|psc
    close=(distance<=length)|psc
    far=(distance>length)&~psc
    result=[]; start=None; outside=0
    for i in range(len(distance)):
        if start is None:
            if close[i]: start=i
        elif not known[i]:
            result.append((start,i,False));start=None;outside=0
        else:
            outside=outside+1 if far[i] else 0
            if outside>=round(.2*fps):
                end=i-outside+1
                result.append((start,end,True));start=None;outside=0
    if start is not None:result.append((start,len(distance),False))
    return result

def boundary(raw,support,a,b,edge,entry,L,fps):
    """Only adjacent, supported steps in a contiguous local boundary window."""
    n=len(raw); last=edge-1 if entry else edge
    if last<0 or last>=n:return {'label':'Unknown','reason':'Video boundary'}
    dist=np.linalg.norm(raw[:,b]-raw[:,a],axis=1)
    valid=support[:,a]&support[:,b]&np.isfinite(raw[:,[a,b]]).all((1,2))&(dist>0)&(dist<=2*L)
    ids=[]
    for i in range(last,max(-1,last-round(fps)),-1) if entry else range(last,min(n,last+round(fps))):
        if not valid[i]:break
        ids.append(i)
    ids=sorted(ids)
    if len(ids)<7:return {'label':'Unknown','reason':'Less than 0.20 s of separate, uninterrupted detections next to boundary'}
    pts=raw[ids][:,[a,b]]; delta=np.diff(pts,axis=0)
    if (np.linalg.norm(delta,axis=2)>20).any():return {'label':'Unknown','reason':'Abrupt coordinate step in boundary context'}
    r=pts[:-1,1]-pts[:-1,0]; r/=np.linalg.norm(r,axis=1)[:,None]
    c=np.column_stack(((delta[:,0]*r).sum(1),-(delta[:,1]*r).sum(1)))*fps
    sign=1 if entry else -1
    labels=[]; means=[]
    for seconds in (.2,.4,.8):
        count=min(len(c),round(seconds*fps))
        z=c[-count:] if entry else c[:count]
        m=sign*z.mean(0);means.append(m.tolist())
        labels.append('Both' if (m>5).all() and m.sum()>5 else 'A' if m[0]>5 and m.sum()>5 else 'B' if m[1]>5 and m.sum()>5 else 'Unknown')
    label=labels[0] if len(set(labels))==1 else 'Unknown'
    result={'label':label,'reason':'Agreement across available 0.20/0.40/0.80 s contexts' if label in ('A','B','Both') else 'Window-sensitive or no clear net boundary movement',
            'context_frames':[ids[0],ids[-1]],'context_seconds':(len(ids)-1)/fps,'window_labels':labels,'contributions_px_s':means}
    if entry:
        onsets=[]
        for animal in (0,1):
            runs=[(lo,hi) for lo,hi in bouts(c[:,animal]>5) if hi-lo>=3 and hi>=len(c)-3]
            onsets.append(runs[-1][0] if runs else None)
        if any(x==0 for x in onsets if x is not None): first='Unknown: movement already underway at context start'
        elif onsets==[None,None]:first='Unknown: no sustained local onset'
        elif onsets[0] is None:first='B'
        elif onsets[1] is None:first='A'
        elif abs(onsets[0]-onsets[1])<3:first='Both'
        else:first='A' if onsets[0]<onsets[1] else 'B'
        result['first_mover']=first
        result['onset_frames']=[ids[x] if x is not None else None for x in onsets]
    return result

def build_events(raw,support,psc,fps,start,lengths):
    events=[]
    for a,b in itertools.combinations(range(raw.shape[1]),2):
        L=60.0; dist=np.linalg.norm(raw[:,b]-raw[:,a],axis=1)
        mask=psc[(a,b)]
        for lo,hi,exit_observed in episodes(dist,mask,L,fps):
            entry=lo>0 and np.isfinite(dist[lo]) and dist[lo]<=L and np.isfinite(dist[lo-1]) and dist[lo-1]>L and not mask[lo-1]
            ap=boundary(raw,support,a,b,lo,True,L,fps) if entry else {'label':'Unknown','reason':'Entry obscured or already close at video start'}
            dep=boundary(raw,support,a,b,hi,False,L,fps) if exit_observed else {'label':'Unknown','reason':'Exit obscured or video ended'}
            ev=dict(a=a,b=b,first_global_frame=start+lo,last_global_frame=start+hi-1,duration_seconds=(hi-lo)/fps,
                    length_px=L,entry_observed=bool(entry),exit_observed=exit_observed,approach=ap,departure=dep,
                    first_mover=ap.get('first_mover','Unknown: entry movement not resolved'),
                    psc_frames=int(mask[lo:hi].sum()),close_frames=int((dist[lo:hi]<=L).sum()),
                    approach_stable=ap['label'] in ('A','B','Both'),departure_stable=dep['label'] in ('A','B','Both'),
                    estimates={str(w):dict(approach=ap,departure=dep) for w in (7,13,25)})
            events.append(ev)
    events.sort(key=lambda e:(e['first_global_frame'],e['a'],e['b']))
    for i,e in enumerate(events):e['id']=i+1
    return events

def main():
    OUT.mkdir(parents=True,exist_ok=False);summaries=[]
    template=(BASE/'proximity60_review.html').read_text()
    for path in sorted(OLD.glob('*/measurements.npz')):
        src=path.parent;dst=OUT/src.name;dst.mkdir()
        d=json.loads(re.search(r'const D=(.*?);\nconst \$=',(src/'review.html').read_text(),re.S)[1])
        z=np.load(path);raw=z['raw'];support=z['independent_detection_supported'];axes=z['axis_endpoints']
        lengths=np.nanmedian(np.linalg.norm(axes[:,:,2:]-axes[:,:,:2],axis=2),axis=0)
        if not np.isfinite(lengths).all():raise ValueError('No body-length estimate')
        canonical=CANON/src.name/'analysis/canonical_states.npz';c=np.load(canonical)
        assert np.array_equal(c['raw'],raw,equal_nan=True)
        psc={}
        for a,b in d['pairs']:
            psc[(a,b)]=(c['group_ids'][:,a]==c['group_ids'][:,b])&(c['group_ids'][:,a]>=0)&(c['inferred'][:,a]|c['inferred'][:,b])&np.isfinite(c['xy'][:,[a,b]]).all((1,2))
        events=build_events(raw,support,psc,d['fps'],d['start'],lengths)
        d.update(events=events,event_count=len(events),body_lengths=lengths,psc={f'{a},{b}':v.astype(int) for (a,b),v in psc.items()})
        (dst/'review.html').write_text(template.replace('__DATA__',json.dumps(clean(d),allow_nan=False,separators=(',',':')).replace('</','<\\/')))
        shutil.copy2(src/'video.mp4',dst/'video.mp4')
        (dst/'events.json').write_text(json.dumps(clean(events),indent=2,allow_nan=False))
        provenance=dict(author='Codex / AI',status='UNREVIEWED',version='0.3.0-development',
            proximity_threshold_px=60,body_length_method='Not used for proximity in this 60-pixel version',
            body_lengths_px=lengths.tolist(),entry='Centroids <=60 pixels, or existing PSC pair; initiator only attributed for observed 60px crossings',exit='Above 60 pixels for 0.20 s; boundary backdated to first outside frame',
            unknown='Missing distance without PSC splits event; no invented departure',context='At most 1 second within 120 pixels; adjacent uninterrupted independent detections; no inferred positions used for motion',
            first_mover='Local sustained onset >=3 steps ending within 3 steps of entry context end; onset at context start censored; <3-step differences simultaneous',
            inputs={str(path):sha(path),str(canonical):sha(canonical)},video_sha256=sha(dst/'video.mp4'))
        (dst/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2))
        summaries.append(dict(name=src.name,body_lengths=lengths.tolist(),events=len(events),approaches=sum(e['approach_stable'] for e in events),departures=sum(e['departure_stable'] for e in events),psc_events=sum(e['psc_frames']>0 for e in events)))
    (OUT/'SUMMARY.json').write_text(json.dumps(summaries,indent=2))
    links=''.join(f'<li><a href="{s["name"]}/review.html">{s["name"]}</a> — {s["events"]} encounter candidates</li>' for s in summaries)
    (OUT/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>Close encounters</title><style>body{font:18px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:20px}li{margin:24px 0}</style><h1>Who enters—and who leaves—a close encounter?</h1><p>Codex / AI · UNREVIEWED development pilot · 12 October 2026</p><p>Entry: centers within 60 pixels. Existing PSCs are separately marked as inferred contact. Exit requires 0.20 seconds above 60 pixels. Initiator means contribution to entering 60-pixel proximity, not necessarily the first beetle to start moving.</p><ul>'+links+'</ul><p>Initiator and leaver are ID, both, or unknown; first movement onset is reported separately. Unknown means the available evidence cannot decide; it does not mean neither beetle moved.</p>')
    print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
