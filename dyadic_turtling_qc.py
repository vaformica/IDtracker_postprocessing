"""Review-only dyadic posture triage. Never emits confirmed posture or durations."""
from pathlib import Path
import hashlib
import html
import json
import math
from collections import Counter
from dyadic_turtling_experiment import screen, PARAMETERS, VERSION as SCREEN_VERSION

VERSION = '0.1.0-candidate-qc'
POLICY = ('Possible turtling only: quiet and looping centroid movement also occur in upright beetles and fighting. '
          'Nearby and unknown partners remain review candidates. No flag does not mean no turtling. '
          'Confirm the beetle ID and posture in the video before measuring behavior.')

def summarize(raw, start, fps):
    if any(len(r)!=2 for r in raw):
        raise ValueError('Dyadic turtling QC requires exactly two identities')
    result=dict(version=VERSION,screen_version=SCREEN_VERSION,parameters=PARAMETERS,
                status='CANDIDATES_UNREVIEWED',policy=POLICY,identity_numbering='raw IDs 0 and 1',
                first_global_frame=int(start),frames=len(raw),fps=float(fps),events=[],per_id=[])
    if not math.isfinite(fps) or abs(fps-30)>1e-6:
        result.update(status='NOT_ASSESSED',reason='Frozen screen supports 30 fps only; no silent frame-threshold rescaling.')
        return result
    for ident in (0,1):
        s=screen(raw,ident)
        mask=[q or l for q,l in zip(s['quiet'],s['loop'])]
        # Missing target positions cannot enter a candidate episode.
        mask=[m and state!='TRACKING_UNKNOWN' for m,state in zip(mask,s['states'])]
        first=None
        for i,flag in enumerate(mask+[False]):
            if flag and first is None:first=i
            if not flag and first is not None:
                result['events'].append(dict(animal_id=ident,first_global_frame=int(start+first),
                    last_global_frame_inclusive=int(start+i-1),candidate_frames=i-first,
                    quiet_support=any(s['quiet'][first:i]),loop_support=any(s['loop'][first:i]),
                    context_frames=dict(Counter(s['context'][first:i])),status='POSSIBLE_TURTLING_REVIEW'))
                first=None
        result['per_id'].append(dict(animal_id=ident,candidate_frames=sum(mask),
            candidate_bouts=sum(e['animal_id']==ident for e in result['events']),
            tracking_unknown_frames=s['states'].count('TRACKING_UNKNOWN'),
            no_candidate_frames=s['states'].count('NO_CANDIDATE_NOT_A_POSTURE_LABEL')))
    result['events'].sort(key=lambda e:(e['first_global_frame'],e['animal_id']))
    return result

def traces(raw,start,events=()):
    """Full-resolution X/Y traces, broken at missing coordinates; jumps retained."""
    esc=html.escape;parts=[];n=len(raw)
    for ident in (0,1):
        paths=[]
        for event in events:
            if event['animal_id'] != ident: continue
            x=10+980*(event['first_global_frame']-start)/max(n-1,1)
            w=max(1,980*event['candidate_frames']/max(n-1,1))
            paths.append(f'<rect x="{x:.2f}" y="5" width="{w:.2f}" height="145" fill="#f4c558" opacity=".3"/>')
        for axis,color in [(0,'#087f9c'),(1,'#ae5716')]:
            vals=[r[ident][axis] for r in raw]
            finite=[v for v in vals if v is not None and math.isfinite(v)]
            lo=min(finite,default=0);span=max(max(finite,default=1)-lo,1)
            seg=[]
            for i,v in enumerate(vals+[None]):
                if v is not None and math.isfinite(v):seg.append(f'{10+980*i/max(n-1,1):.2f},{140-120*(v-lo)/span:.2f}')
                elif seg:
                    paths.append(f'<polyline fill="none" stroke="{color}" stroke-width="1" points="'+ ' '.join(seg)+'"/>');seg=[]
        parts.append(f'<h3>ID {ident}: raw X (blue) and Y (brown)</h3><svg viewBox="0 0 1000 155" style="width:100%;height:155px" aria-label="ID {ident} raw coordinate traces">'+''.join(paths)+'</svg>')
    return ''.join(parts)+f'<p>Global frames {start}–{start+n-1}. Each coordinate is scaled separately. Missing coordinates break the lines; jumps remain visible. Traces show motion, not posture.</p>'

def write_report(output,report,raw,review_link=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name in ['dyadic_turtling_qc.json','dyadic_turtling_qc.html']:
        if (output/name).exists():raise FileExistsError(output/name)
    report=dict(report,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                screen_code_sha256=hashlib.sha256(Path(__file__).with_name('dyadic_turtling_experiment.py').read_bytes()).hexdigest())
    (output/'dyadic_turtling_qc.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    esc=lambda s:html.escape(str(s),quote=True)
    body='<h1>Possible turtling — dyadic QC</h1><p><b>'+esc(report['status'])+'</b></p><p>'+esc(POLICY)+'</p>'
    if review_link:body+='<p><a target="postureVideo" href="'+esc(review_link)+'">Open full synchronized review</a></p>'
    if report.get('reason'):body+='<p>'+esc(report['reason'])+'</p>'
    body+='<p>IDs below are raw IDtracker IDs 0 and 1. Candidate counts are triage workload, not biological measurements.</p>'
    for a in report['per_id']:body+=f"<p>ID {a['animal_id']}: {a['candidate_bouts']} candidate bouts; {a['candidate_frames']} candidate frames; {a['tracking_unknown_frames']} tracking-unknown frames.</p>"
    body+='<p>Gold trace bands mark candidate windows, not confirmed posture.</p>'+traces(raw,report['first_global_frame'],report['events'])
    body+='<h2>Candidate intervals</h2><p>Click a frame interval to inspect the video. Boundaries are screen windows, not measured flip/righting times.</p><table><tr><th>ID</th><th>Global frames</th><th>Support</th><th>Partner context (frames)</th></tr>'
    for e in report['events']:
        bounds=f"{e['first_global_frame']}–{e['last_global_frame_inclusive']}"
        link=(review_link.split('#')[0]+'#frame='+str(e['first_global_frame'])) if review_link else None
        body+='<tr><td>'+str(e['animal_id'])+'</td><td>'+ ('<a target="postureVideo" href="'+esc(link)+'">'+bounds+'</a>' if link else bounds)+'</td><td>'+('quiet ' if e['quiet_support'] else '')+('loop' if e['loop_support'] else '')+'</td><td>'+esc(e['context_frames'])+'</td></tr>'
    body+='</table>'
    if not report['events']:body+='<p>No candidates generated. This does not establish absence of turtling.</p>'
    if review_link:body+='<h2>Video review</h2><iframe title="Synchronized video reviewer" name="postureVideo" src="'+esc(review_link)+'" style="width:100%;height:850px;border:1px solid #abc"></iframe>'
    (output/'dyadic_turtling_qc.html').write_text('<!doctype html><meta charset="utf-8"><title>Dyadic turtling QC</title><style>body{font:16px system-ui;margin:24px;line-height:1.5}td,th{padding:8px;border:1px solid #ccd}table{border-collapse:collapse}svg{background:#f3f7f8}</style>'+body)
    return dict(version=VERSION,status=report['status'],candidate_bouts=len(report['events']),json='dyadic_turtling_qc.json',html='dyadic_turtling_qc.html',
                json_sha256=hashlib.sha256((output/'dyadic_turtling_qc.json').read_bytes()).hexdigest(),
                html_sha256=hashlib.sha256((output/'dyadic_turtling_qc.html').read_bytes()).hexdigest())
