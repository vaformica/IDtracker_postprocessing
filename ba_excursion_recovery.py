"""Development-only excursion proposals. Raw data and prior accepted repairs stay intact."""
import numpy as np
from ba_major_jump_recovery import propose as prior_propose, segments
RULES=dict(version='0.3.0-excursion-development',jump_px=100,major_displacement_px=50,excursion_edge_px=20,maximum_join_step_px=30,maximum_directional_frames=15,appearance_min=.65)

def propose(raw, agreed, forward, backward, statuses, images, origin):
    import cv2
    raw=np.asarray(raw,float);out,old_changed,_=prior_propose(raw,agreed,statuses)
    audits=[];origin=np.asarray(origin);n=len(raw)
    def patch(i,xy):
        x,y=np.rint(xy-origin).astype(int);im=images[i];r=15
        if x-r<0 or y-r<0 or x+r>=im.shape[1] or y+r>=im.shape[0]:return None
        return im[y-r:y+r+1,x-r:x+r+1]
    def similarity(a,b):
        if a is None or b is None or a.std()<3 or b.std()<3:return -1.
        return float(cv2.matchTemplate(a,b,cv2.TM_CCOEFF_NORMED)[0,0])
    def proposals(candidates, name, visual):
        dist=np.linalg.norm(candidates-raw,axis=1)
        eligible=np.isfinite(raw).all(1)&np.isfinite(candidates).all(1)&(dist>=20)
        found=[]
        for a,b in segments(eligible):
            reason=None;scores=[]
            if a==0 or b==n or not np.isfinite(raw[[a-1,b]]).all():reason='unobserved_flank'
            elif np.max(dist[a:b])<50 or not np.any(np.linalg.norm(np.diff(raw[a-1:b+1],axis=0),axis=1)>100):reason='not_major_excursion'
            elif visual and b-a>15:reason='directional_span_too_long'
            elif np.max(np.linalg.norm(np.diff(np.vstack([raw[a-1],candidates[a:b],raw[b]]),axis=0),axis=1))>30:reason='cannot_rejoin'
            elif np.any(old_changed[a:b] & (np.linalg.norm(candidates[a:b]-out[a:b],axis=1)>.01)):reason='would_change_prior_repair'
            if reason is None and visual:
                left=patch(a-1,raw[a-1]);right=patch(b,raw[b])
                for i in range(a,b):scores.append(min(similarity(patch(i,candidates[i]),left),similarity(patch(i,candidates[i]),right)))
                if min(scores)<.65:reason='insufficient_two_flank_appearance'
            audits.append(dict(start_index=a,end_index=b-1,source=name,eligible=reason is None,reason=reason or 'supported_excursion',appearance_scores=scores))
            if reason is None:found.append((a,b,candidates[a:b].copy(),name))
        return found
    # Frozen consensus positions first; a smaller edge includes the lead-in to a major error.
    choices=proposals(agreed,'frozen_bidirectional',False)
    choices+=proposals(forward,'forward_with_two_flank_image_check',True)
    choices+=proposals(backward,'backward_with_two_flank_image_check',True)
    # Disagreeing eligible paths veto an entire patch; no arbitrary directional preference.
    applied=[]
    for a,b,path,name in choices:
        conflict=False
        for c,d,other,_ in choices:
            lo=max(a,c);hi=min(b,d)
            if lo<hi and np.any(np.linalg.norm(path[lo-a:hi-a]-other[lo-c:hi-c],axis=1)>8):conflict=True
        if conflict:continue
        if np.any(np.linalg.norm(out[a:b]-raw[a:b],axis=1)>0):
            if np.any(np.linalg.norm(out[a:b][old_changed[a:b]]-path[old_changed[a:b]],axis=1)>.01):continue
        # Favor frozen consensus coordinates, and do not overwrite already selected additions.
        changed_here=np.linalg.norm(out[a:b]-raw[a:b],axis=1)>.01
        if np.any(changed_here & (np.linalg.norm(out[a:b]-path,axis=1)>.01)):continue
        out[a:b]=path;applied.append(dict(start_index=a,end_index=b-1,source=name))
    assert np.array_equal(out[old_changed],prior_propose(raw,agreed,statuses)[0][old_changed])
    assert np.array_equal(np.isfinite(raw),np.isfinite(out))
    changed=np.isfinite(raw).all(1)&(np.linalg.norm(out-raw,axis=1)>.01)
    return out,changed,dict(candidates=audits,applied=applied,prior_changed=old_changed.tolist())
