"""Dyadic posture *screen*, 0.1.0-development. No production integration.

Raw coordinates only. Quiet position is a review candidate, never proof of
posture. Close/unknown partner context causes abstention, not a negative label.
All distances are original-image pixels; frame thresholds assume 30 fps.
"""
import math
import statistics

VERSION = '0.1.0-development'
PARAMETERS = dict(window_frames=120, quiet_radius90_px=3.0, quiet_max_step_px=5.0,
                  social_radius_px=60.0, jump_px=20.0)

def finite(p):
    return len(p) == 2 and all(v is not None and math.isfinite(v) for v in p)

def quantile(values, q):
    s=sorted(values); x=(len(s)-1)*q; i=int(x)
    return s[i]+(s[min(i+1,len(s)-1)]-s[i])*(x-i)

def screen(raw, target_id, *, window_frames=120, quiet_radius90_px=3.0,
           quiet_max_step_px=5.0, social_radius_px=60.0, jump_px=20.0):
    if target_id not in (0,1) or any(len(r)!=2 for r in raw):
        raise ValueError('Requires exactly two raw identities and target 0 or 1')
    if window_frames < 3: raise ValueError('window_frames must be >=3')
    xy=[r[target_id] for r in raw]; n=len(xy); valid=[finite(p) for p in xy]
    loop=[False]*n; quiet=[False]*n
    for start in range(n-window_frames+1):
        b=xy[start:start+window_frames]; v=valid[start:start+window_frames]
        if sum(v)/window_frames < .95: continue
        pts=[p for p,ok in zip(b,v) if ok]
        center=[statistics.median(p[k] for p in pts) for k in (0,1)]
        radius=quantile([math.dist(p,center) for p in pts],.9)
        vec=[(b[i+1][0]-b[i][0], b[i+1][1]-b[i][1]) if v[i] and v[i+1] else None for i in range(window_frames-1)]
        steps=[math.hypot(*p) if p else None for p in vec]
        mx=max((d for d in steps if d is not None),default=0)
        # Complete positions, no gaps/jumps: quiet is a hypothesis to review.
        if all(v) and mx<=quiet_max_step_px and radius<=quiet_radius90_px:
            quiet[start:start+window_frames]=[True]*window_frames
        if mx>jump_px or not 5<=radius<=35: continue
        moving=[d is not None and d>=1 for d in steps]
        path=sum(d for d,m in zip(steps,moving) if m)
        if path<120 or math.dist(pts[0],pts[-1])/path>.25: continue
        turn=0
        for i in range(len(vec)-1):
            if moving[i] and moving[i+1]:
                delta=math.atan2(vec[i+1][1],vec[i+1][0])-math.atan2(vec[i][1],vec[i][0])
                turn+=abs(math.atan2(math.sin(delta),math.cos(delta)))
        if turn/(2*math.pi)>=3:
            for i,ok in enumerate(v): loop[start+i] |= ok
    states=[]; context=[]
    for i,r in enumerate(raw):
        partner=r[1-target_id]
        ctx='PARTNER_UNKNOWN' if not finite(partner) else ('NEAR_PARTNER' if valid[i] and math.dist(xy[i],partner)<=social_radius_px else 'SEPARATE')
        context.append(ctx)
        if not valid[i]: state='TRACKING_UNKNOWN'
        elif loop[i] or quiet[i]:
            if ctx!='SEPARATE': state='INTERACTION_AMBIGUOUS'
            elif quiet[i]: state='QUIET_REVIEW_CANDIDATE'
            else: state='LOOP_REVIEW_CANDIDATE'
        else: state='NO_CANDIDATE_NOT_A_POSTURE_LABEL'
        states.append(state)
    return dict(version=VERSION,loop=loop,quiet=quiet,states=states,context=context)
