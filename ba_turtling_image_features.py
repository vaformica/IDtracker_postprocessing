"""Image-only BA posture features for a diagnostic experiment, not production.

No run, frame, tracking coordinates, or recording identity is a predictor.
The tracked center only places a fixed crop; all geometry is local to the crop.
"""
import cv2
import numpy as np
VERSION='0.1.0-diagnostic'
NAMES=['area','solidity','extent','axis_ratio','perimeter_ratio','centroid_offset','body_mean','body_std','body_p10','body_p90','edge_mean','edge_p90','dark_fraction','core_dark_fraction','ring_dark_fraction','mask_boundary_fraction','closed_area_ratio']

def extract(gray, center, half=32):
    x,y=map(float,center)
    if not np.isfinite([x,y]).all() or not half<=x<gray.shape[1]-half or not half<=y<gray.shape[0]-half:
        return None,'crop_outside_frame'
    patch=cv2.getRectSubPix(gray,(2*half+1,2*half+1),(x,y)).astype(float)
    yy,xx=np.mgrid[-half:half+1,-half:half+1];rad=np.hypot(xx,yy)
    bg=np.median(patch[rad>26]);contrast=bg-np.percentile(patch[rad<20],10)
    if contrast<15:return None,'low_contrast'
    normalized=np.clip((bg-patch)/max(contrast,1),0,1)
    mask=((patch<bg-max(15,.3*contrast))&(rad<=27)).astype(np.uint8)
    num,labels,stats,centers=cv2.connectedComponentsWithStats(mask,8)
    options=[i for i in range(1,num) if stats[i,cv2.CC_STAT_AREA]>=40 and np.linalg.norm(centers[i]-half)<15]
    if not options:return None,'no_centered_component'
    idx=min(options,key=lambda i:np.linalg.norm(centers[i]-half));body=(labels==idx).astype(np.uint8)
    contours,_=cv2.findContours(body,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);contour=max(contours,key=cv2.contourArea)
    area=float(body.sum());hull=cv2.contourArea(cv2.convexHull(contour));perim=cv2.arcLength(contour,True)
    ys,xs=np.nonzero(body);cov=np.cov(np.c_[xs,ys].T);eigs=np.linalg.eigvalsh(cov)
    vals=normalized[body.astype(bool)];edges=np.hypot(cv2.Sobel(normalized,cv2.CV_64F,1,0),cv2.Sobel(normalized,cv2.CV_64F,0,1))
    closed=cv2.morphologyEx(body,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    boundary=float(np.mean(rad[body.astype(bool)]>=26))
    f=[area,area/max(hull,1),area/float(stats[idx,2]*stats[idx,3]),float(eigs[0]/max(eigs[1],1e-6)),perim/np.sqrt(area),np.linalg.norm(centers[idx]-half),vals.mean(),vals.std(),np.quantile(vals,.1),np.quantile(vals,.9),edges[body.astype(bool)].mean(),np.quantile(edges[body.astype(bool)],.9),mask[rad<27].mean(),mask[rad<12].mean(),mask[(rad>=12)&(rad<27)].mean(),boundary,float(closed.sum()/area)]
    return np.array(f,float),'component_touches_crop_ring' if boundary>.05 else 'ok'
