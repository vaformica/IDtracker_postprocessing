"""Frozen BA single-animal interpolation 1.0.0.

Inferred coordinates remain separate from baseline and raw tracking. This module
must not be used to infer posture or applied to dyadic/group recordings.
"""
import numpy as np
import cv2

VERSION = "1.0.0"
RULES = dict(version=VERSION, collection="BA", number_of_animals=1, maximum_missing_frames=30, maximum_mean_step_px=20, support_window_frames=15, maximum_support_step_px=25, total_distance_cap=None)

def spans(mask):
 edges=np.diff(np.r_[False,np.asarray(mask,bool),False].astype(int))
 return list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))

def in_roi(xy,roi):
 return all(cv2.pointPolygonTest(np.asarray(roi,np.float32),tuple(map(float,p)),False)>=0 for p in xy)

def frozen_interpolate(xy,start,protected,cfg,*,collection=None,number_of_animals=None):
 if collection!="BA" or type(number_of_animals) is not int or number_of_animals!=1:raise ValueError("Interpolation is restricted to confirmed one-animal BA runs")
 if np.asarray(xy).ndim!=2 or np.asarray(xy).shape[1]!=2:raise ValueError("Expected one-animal N-by-2 coordinates")
 xy=np.asarray(xy,float);protected=np.asarray(protected,bool)
 if protected.shape!=(len(xy),):raise ValueError("Protected mask must match frame count")
 if np.isfinite(xy[protected]).any():raise ValueError("Human-excluded coordinates must already be missing")
 if not isinstance(start,(int,np.integer)):raise ValueError("Global start must be an integer")
 out=xy.copy();good=np.isfinite(xy).all(1);method=np.where(good,"existing","missing").astype("<U32");method[protected]="human_exclusion";events=[];audit=[]
 for aa,bb in spans(~good):
  a,b=int(aa),int(bb);r=dict(start=start+a,end=start+b-1,length=b-a,status='missing')
  if a==0 or b==len(xy):r['reason']='unbounded_gap'
  elif protected[a:b].any():r['reason']='human_exclusion'
  elif b-a>30:r['reason']='longer_than_30_frames'
  elif np.linalg.norm(xy[b]-xy[a-1])/(b-a+1)>20:r['reason']='endpoint_distance_or_average_step'
  else:
   left=np.flatnonzero(good[max(0,a-16):a-1])+max(0,a-16);right=np.flatnonzero(good[b+1:min(len(xy),b+16)])+b+1
   reason=None
   if not len(left) or not len(right):reason='insufficient_nearby_support'
   else:
    l,rr=int(left[-1]),int(right[0]);dl=float(np.linalg.norm(xy[a-1]-xy[l]));dr=float(np.linalg.norm(xy[rr]-xy[b]));r['support_frames']=[start+l,start+a-1,start+b,start+rr]
    if protected[l:rr+1].any():reason='protected_support_interval'
    elif dl/(a-1-l)>25 or dr/(rr-b)>25:reason='unstable_nearby_support'
   bridge=np.linspace(xy[a-1],xy[b],b-a+2)[1:-1]
   if reason is None and not in_roi(bridge,cfg['roi']):reason='outside_roi'
   if reason:r['reason']=reason
   else:
    out[a:b]=bridge;method[a:b]='interpolated';r.update(status='interpolated',endpoint_distance_px=float(np.linalg.norm(xy[b]-xy[a-1])));r['id']=f'gap_{len(events)+1:03}';events.append(r.copy())
  audit.append(r)
 return out,method,events,audit
