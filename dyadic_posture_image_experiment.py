"""Image-only posture feasibility model; no production integration.

Coordinates place raw-ID crops only. No location, time, ID, interaction state,
fungus status or trajectory feature enters the classifier. Lossy review imagery
is the source; it cannot recover hidden anatomy or resolve identity mistakes.
"""
import numpy as np
from PIL import Image
VERSION='0.1.0-image-development'
HALF_RAW_PX=45
SAMPLE_STRIDE=15

def center_in_review(p,g):
    if not all(v is not None and np.isfinite(v) for v in p): return None
    x,y,w,h=g['crop'];dx,dy=p[0]-x,p[1]-y
    rot=g['rotation_cw']
    if rot==90:dx,dy=h-dy,dx;w,h=h,w
    elif rot==180:dx,dy=w-dx,h-dy
    elif rot==270:dx,dy=dy,w-dx;w,h=h,w
    return g['pad_x']+dx*g['content_width']/w,g['pad_y']+dy*g['content_height']/h

def crop(gray,p,g,patch_size=96):
    center=center_in_review(p,g)
    if center is None:return None,'missing_raw_center'
    x,y=center
    w,h=g['crop'][2:]
    if g['rotation_cw'] in (90,270):w,h=h,w
    hx=HALF_RAW_PX*g['content_width']/w;hy=HALF_RAW_PX*g['content_height']/h
    box=(int(round(x-hx)),int(round(y-hy)),int(round(x+hx)),int(round(y+hy)))
    if box[0]<g['pad_x'] or box[1]<g['pad_y'] or box[2]>g['pad_x']+g['content_width'] or box[3]>g['pad_y']+g['content_height']:
        return None,'crop_crosses_source_arena_view'
    a=np.asarray(Image.fromarray(gray).crop(box).resize((patch_size,patch_size),Image.Resampling.BILINEAR),dtype=float)/255
    return a,'ok'

def features(patches):
    """Appearance + +/-0.5 s image differences in separately centered crops."""
    a,b,c=patches
    size=b.shape[0];yy,xx=np.mgrid[-1:1:complex(size),-1:1:complex(size)];rad=np.hypot(xx,yy)
    bg=np.median(b[rad>.85]);contrast=max(float(bg-np.quantile(b[rad<.6],.1)),.08)
    norm=np.clip((bg-b)/contrast,-1,2)
    grad=np.hypot(*np.gradient(norm))
    f=[]
    for lo,hi in [(0,.25),(.25,.5),(.5,.75),(.75,1)]:
        m=(rad>=lo)&(rad<hi)
        f.extend(np.quantile(norm[m],[.1,.5,.9]).tolist())
        f.extend([float(norm[m].mean()),float(norm[m].std()),float(grad[m].mean()),float((norm[m]>.5).mean())])
    # Coarse local texture and temporal changes; no centroid displacement.
    change=(np.abs(a-b)+np.abs(c-b))/2
    for q in (norm,grad,change):
        for i in range(0,size,size//4):
            for j in range(0,size,size//4):f.append(float(q[i:i+size//4,j:j+size//4].mean()))
    return np.array(f,float)

def fit(X,y,recordings,steps=800):
    """Fixed regularized logistic model, balanced within recording/class cells."""
    X=np.asarray(X,float);y=np.asarray(y,float)
    if len(set(y))!=2:raise ValueError('Both posture classes required')
    mean=X.mean(0);scale=X.std(0);scale[scale<1e-6]=1
    z=np.clip((X-mean)/scale,-8,8);w=np.zeros(z.shape[1]);bias=0.
    cells=[(r,int(v)) for r,v in zip(recordings,y)];counts={c:cells.count(c) for c in set(cells)}
    weights=np.array([1/counts[c] for c in cells]);weights/=weights.sum()
    for _ in range(steps):
        p=1/(1+np.exp(-np.clip(z@w+bias,-30,30)));err=(p-y)*weights
        w-=.1*(z.T@err+.1*w);bias-=.1*err.sum()
    return dict(mean=mean.tolist(),scale=scale.tolist(),weights=w.tolist(),bias=float(bias),regularization=.1,steps=steps)

def predict(model,X):
    z=np.clip((np.asarray(X)-model['mean'])/model['scale'],-8,8)
    return 1/(1+np.exp(-np.clip(z@np.array(model['weights'])+model['bias'],-30,30)))
