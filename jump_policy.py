"""User-selected jump-as-missing rule. Original input remains immutable.

Paired excursions use the unchanged pre-entry/post-return anchors. All other
jump endpoints become unknown. Only gaps of <=15 frames with anchors <=100px
apart are interpolated; long/unbounded gaps remain jump_removed. Human-protected
frames are never replaced, and conflicts are reported rather than hidden.
"""
import math
VERSION = '1.0.0-jump-as-missing'
THRESHOLD_PX = 100.0
MAX_INTERPOLATION_FRAMES = 15

def finite(p):
    return isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in p)

def repair(points, start=0, protected=None, forced=None, threshold=THRESHOLD_PX, max_gap=MAX_INTERPOLATION_FRAMES):
    """Return corrected positions, frame labels, immutable anchor events and QC."""
    if not math.isfinite(threshold) or threshold <= 0 or type(max_gap) is not int or max_gap < 1:
        raise ValueError('Invalid jump settings')
    original=[list(p) if finite(p) else [None,None] for p in points]
    n=len(original);protected=set(protected or []);bad=set(forced or [])-protected
    if any(type(i) is not int or not 0<=i<n for i in protected|bad):raise ValueError('Invalid protected/forced offset')
    jumps=[t for t in range(1,n) if finite(original[t-1]) and finite(original[t]) and math.dist(original[t-1],original[t])>threshold]
    k=0
    while k<len(jumps):
        a=jumps[k];b=jumps[k+1] if k+1<len(jumps) else None
        if b is not None and math.dist(original[a-1],original[b])<=threshold and not any(i in protected for i in range(a,b)):
            bad.update(range(a,b));k+=2
        else:
            bad.update({a-1,a}-protected);k+=1
    xy=[p[:] for p in original];labels=['original' if finite(p) else 'missing' for p in xy]
    for t in bad:xy[t]=[None,None];labels[t]='jump_removed'
    events=[];t=0
    while t<n:
        if finite(xy[t]) or t in protected:t+=1;continue
        lo=t
        while t<n and not finite(xy[t]) and t not in protected:t+=1
        hi=t-1
        if not any(i in bad for i in range(lo,t)):continue
        left=lo-1;right=t
        can=left>=0 and right<n and finite(xy[left]) and finite(xy[right]) and right-lo<=max_gap and math.dist(xy[left],xy[right])<=threshold
        event=dict(start=start+lo,end=start+hi,status='interpolated' if can else 'jump_removed',anchor_frames=[start+left,start+right] if left>=0 and right<n else None,anchor_positions=[xy[left][:],xy[right][:]] if left>=0 and right<n and finite(xy[left]) and finite(xy[right]) else None)
        if can:
            for i in range(lo,right):
                w=(i-left)/(right-left);xy[i]=[xy[left][k]+w*(xy[right][k]-xy[left][k]) for k in (0,1)];labels[i]='interpolated'
        events.append(event)
    residual=[start+t for t in range(1,n) if finite(xy[t-1]) and finite(xy[t]) and math.dist(xy[t-1],xy[t])>threshold]
    return dict(version=VERSION,xy=xy,labels=labels,events=events,jump_destination_frames=[start+t for t in jumps],unresolved_protected_jump_frames=residual,threshold_px=threshold,max_interpolation_frames=max_gap)
