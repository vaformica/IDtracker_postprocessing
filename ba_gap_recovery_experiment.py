"""BA-only, missing-position recovery experiment. Never a production default.

Coordinates added by this module are inferred, not direct observations. Existing
finite coordinates and protected human exclusions are immutable. Image evidence
uses existing full-resolution spatial crops, but lossy review media; validation
on source video is required before a scientific release.
"""
import cv2
import numpy as np

RULES = dict(version='0.1.0-gap-recovery-development',short_gap_max=15,
             endpoint_distance_max=25.,average_step_max=4.,anchor_frames=5,
             anchor_step_max=15.,image_gap_max=300,template_radius=15,
             search_radius=30,ncc_min=.85,uniqueness_min=.04,
             bidirectional_agreement=5.,image_step_max=8.)

def spans(mask):
    e=np.diff(np.r_[False,np.asarray(mask,bool),False].astype(int))
    return list(zip(np.flatnonzero(e==1),np.flatnonzero(e==-1)))

def in_roi(xy,roi):
    return all(cv2.pointPolygonTest(np.asarray(roi,np.float32),tuple(map(float,p)),False)>=0 for p in xy)

def supported_flanks(xy,a,b,protected):
    k=RULES['anchor_frames']
    if a<k or b+k>len(xy) or protected[a-k:b+k].any():return False
    for w in [xy[a-k:a],xy[b:b+k]]:
        if not np.isfinite(w).all() or np.max(np.linalg.norm(np.diff(w,axis=0),axis=1))>RULES['anchor_step_max']:return False
    return True

def match(image,template,center):
    r=RULES['template_radius'];s=RULES['search_radius'];x,y=np.rint(center).astype(int)
    l=max(0,x-s-r);t=max(0,y-s-r);right=min(image.shape[1],x+s+r+1);bottom=min(image.shape[0],y+s+r+1)
    search=image[t:bottom,l:right]
    if search.shape[0]<template.shape[0] or search.shape[1]<template.shape[1]:return None
    m=cv2.matchTemplate(search,template,cv2.TM_CCOEFF_NORMED);_,score,_,loc=cv2.minMaxLoc(m);xx,yy=loc
    alt=m.copy();alt[max(0,yy-8):yy+9,max(0,xx-8):xx+9]=-1
    if score<RULES['ncc_min'] or score-float(alt.max())<RULES['uniqueness_min']:return None
    return np.array([l+xx+r,t+yy+r],float),float(score)

def image_bridge(xy,images,a,b,origin,roi):
    r=RULES['template_radius'];templates=[]
    for i in [a-1,b]:
        x,y=np.rint(xy[i]-origin).astype(int);im=images[i]
        if x-r<0 or y-r<0 or x+r>=im.shape[1] or y+r>=im.shape[0]:return None,'template_outside_crop'
        template=im[y-r:y+r+1,x-r:x+r+1]
        if template.std()<5:return None,'weak_template'
        templates.append(template)
    paths=[];scores=[]
    for direction,template,seed in [(1,templates[0],xy[a-1]-origin),(-1,templates[1],xy[b]-origin)]:
        path=np.full((b-a,2),np.nan);point=seed.copy();sc=[]
        for i in (range(a,b) if direction==1 else range(b-1,a-1,-1)):
            result=match(images[i],template,point)
            if result is None:return None,'ambiguous_or_weak_image_match'
            q,score=result
            if np.linalg.norm(q-point)>RULES['image_step_max']:return None,'image_step_limit'
            path[i-a]=q+origin;point=q;sc.append(score)
        paths.append(path);scores.extend(sc)
    if np.max(np.linalg.norm(paths[0]-paths[1],axis=1))>RULES['bidirectional_agreement']:return None,'two_flanks_disagree'
    out=(paths[0]+paths[1])/2
    if not in_roi(out,roi):return None,'outside_roi'
    if np.max(np.linalg.norm(np.diff(np.vstack([xy[a-1],out,xy[b]]),axis=0),axis=1))>RULES['image_step_max']:return None,'join_step_limit'
    return out,dict(min_ncc=min(scores),max_bidirectional_difference=float(np.max(np.linalg.norm(paths[0]-paths[1],axis=1))))

def propose(xy,roi,images=None,origin=(0,0),protected=None):
    xy=np.asarray(xy,float);out=xy.copy();protected=np.zeros(len(xy),bool) if protected is None else np.asarray(protected,bool)
    method=np.full(len(xy),'existing',dtype='<U24');method[~np.isfinite(xy).all(1)]='missing';method[protected]='human_exclusion';audit=[]
    for aa,bb in spans(~np.isfinite(xy).all(1)):
        a,b=int(aa),int(bb);rec=dict(start_index=a,end_index=b-1,length=b-a,status='missing')
        if protected[a:b].any():rec['reason']='human_exclusion'
        elif not supported_flanks(xy,a,b,protected):rec['reason']='no_stable_two_sided_anchor'
        elif b-a<=RULES['short_gap_max']:
            dist=np.linalg.norm(xy[b]-xy[a-1]);bridge=np.linspace(xy[a-1],xy[b],b-a+2)[1:-1]
            if dist>RULES['endpoint_distance_max'] or dist/(b-a+1)>RULES['average_step_max']:rec['reason']='implausible_short_bridge'
            elif not in_roi(bridge,roi):rec['reason']='outside_roi'
            else:out[a:b]=bridge;method[a:b]='interpolated';rec['status']='interpolated'
        elif b-a>RULES['image_gap_max']:rec['reason']='gap_exceeds_image_limit'
        elif images is None:rec['reason']='images_not_available'
        else:
            bridge,detail=image_bridge(xy,images,a,b,np.asarray(origin),roi)
            if bridge is None:rec['reason']=detail
            else:out[a:b]=bridge;method[a:b]='image_candidate';rec.update(status='image_candidate',evidence=detail)
        audit.append(rec)
    assert np.array_equal(out[np.isfinite(xy).all(1)],xy[np.isfinite(xy).all(1)])
    assert np.array_equal(out[protected],xy[protected],equal_nan=True)
    return out,method,audit
