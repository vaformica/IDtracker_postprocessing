"""Targeted stationary-scene reacquisition experiment; not a production default."""
import numpy as np
import cv2
RULES=dict(version='0.4.0-stationary-reacquisition-development',stable_frames=5,stable_radius_px=4,cluster_radius_px=15,minimum_anchor_frames=10,minimum_anchor_fraction=.7,search_radius_px=25,template_radius_px=15,ncc_min=.8,unique_margin=.03,template_agreement_px=5,minimum_change_px=20,major_displacement_px=50)
def propose(xy,images,origin,protected=None):
 xy=np.asarray(xy,float);out=xy.copy();n=len(xy);origin=np.array(origin);protected=np.zeros(n,bool)if protected is None else np.asarray(protected,bool)
 anchor=np.zeros(n,bool)
 for i in range(n-4):
  w=xy[i:i+5]
  if np.isfinite(w).all() and np.max(np.linalg.norm(w-w.mean(0),axis=1))<=4:anchor[i:i+5]=True
 ids=np.flatnonzero(anchor);audit=dict(rules=RULES,anchor_frames=len(ids),status='no_supported_stationary_reference',frames=[])
 if len(ids)<10:return out,audit
 support=np.array([np.linalg.norm(xy[ids]-xy[i],axis=1)<=15 for i in ids]);best=ids[support.sum(1).argmax()];cluster=ids[np.linalg.norm(xy[ids]-xy[best],axis=1)<=15]
 if len(cluster)<10 or len(cluster)/len(ids)<.7:return out,audit
 center=np.median(xy[cluster],axis=0);refs=[int(cluster[0]),int(cluster[-1])];r=15;cx,cy=np.rint(center-origin).astype(int)
 def patch(i,p):
  x,y=np.rint(p-origin).astype(int);im=images[i]
  if x-r<0 or y-r<0 or x+r>=im.shape[1] or y+r>=im.shape[0]:return None
  return im[y-r:y+r+1,x-r:x+r+1]
 templates=[patch(i,xy[i])for i in refs]
 if any(t is None or t.std()<3 for t in templates):return out,audit
 audit.update(status='reference_supported',reference_indices=refs,reference_center=center.tolist(),cluster_frames=len(cluster))
 candidates=np.full_like(xy,np.nan)
 for i,im in enumerate(images):
  if protected[i] or not np.isfinite(xy[i]).all():continue
  x0=max(0,cx-25-r);y0=max(0,cy-25-r);x1=min(im.shape[1],cx+25+r+1);y1=min(im.shape[0],cy+25+r+1);search=im[y0:y1,x0:x1]
  found=[];scores=[];margins=[]
  for t in templates:
   if search.shape[0]<t.shape[0] or search.shape[1]<t.shape[1]:break
   m=cv2.matchTemplate(search,t,cv2.TM_CCOEFF_NORMED);_,score,_,loc=cv2.minMaxLoc(m);lx,ly=loc;alt=m.copy();alt[max(0,ly-8):ly+9,max(0,lx-8):lx+9]=-1;margin=score-float(alt.max());found.append(np.array([x0+lx+r,y0+ly+r])+origin);scores.append(score);margins.append(margin)
  accepted=len(found)==2 and min(scores)>=.8 and min(margins)>=.03 and np.linalg.norm(found[0]-found[1])<=5
  if accepted:candidates[i]=np.mean(found,axis=0)
  audit['frames'].append(dict(index=i,accepted=bool(accepted),scores=scores,margins=margins,candidate=candidates[i].tolist()if accepted else None))
 # Require a major deviation in the examined scene; preserve small-offset-only cases.
 delta=np.linalg.norm(candidates-xy,axis=1)
 if not np.any(delta>=50):audit['status']='no_major_displacement';return out,audit
 changed=np.isfinite(candidates).all(1)&(delta>=20);out[changed]=candidates[changed]
 # No new major edges are allowed; keep any failing proposals for audit only.
 old=np.linalg.norm(np.diff(xy,axis=0),axis=1)>100
 for _ in range(n):
  bad=(np.linalg.norm(np.diff(out,axis=0),axis=1)>100)&~old
  reject=changed&(np.r_[bad,False]|np.r_[False,bad])
  if not reject.any():break
  out[reject]=xy[reject];changed[reject]=False
 # A short image-failure bout with a large displacement from the stationary
 # reference is an uncertain observation, not a position to invent.
 from ba_major_jump_recovery import segments
 failed=np.zeros(n,bool)
 for row in audit['frames']:failed[row['index']]=not row['accepted']
 masked=[]
 for a,b in segments(failed):
  if a==0 or b==n or b-a>15 or failed[a-1] or failed[b]:continue
  if np.any(protected[a:b]) or not np.any(np.linalg.norm(xy[a:b]-center,axis=1)>=50):continue
  out[a:b]=np.nan;masked.extend(range(a,b))
 audit['applied_indices']=np.flatnonzero(changed).tolist();audit['proposed_missing_indices']=masked
 return out,audit
