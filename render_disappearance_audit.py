"""Add explicitly separated inference annotations to a native IDtracker video."""
import hashlib
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'groupagetrial01_062024_Box01_OLD_IDtracker_closeup_IDtracker_native.avi'
FFMPEG = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'


def render():
    data = np.load(ROOT/'audit_states.npz')
    xy, inferred, anchors = (data[k] for k in ('xy', 'inferred', 'anchors'))
    valid = np.isfinite(xy).all(axis=2)
    cap = cv2.VideoCapture(str(SOURCE))
    assert cap.isOpened()
    output = ROOT/'OLD_disappearance_audit.mp4'
    assert not output.exists()
    command=[FFMPEG,'-v','error','-nostdin','-n','-f','rawvideo','-pix_fmt','bgr24',
        '-s','1740x920','-r',str(cap.get(cv2.CAP_PROP_FPS)),'-i','pipe:0',
        '-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',
        '-movflags','+faststart',str(output)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE)
    last=np.full((6,2),np.nan); counts={}; samples=set()
    missing_frames=np.flatnonzero((~valid[250:]).any(axis=1))+250
    if len(missing_frames):
        samples.update([int(missing_frames[0]), int(missing_frames[len(missing_frames)//2])])
    for category, mask in [('presumed',inferred),('unresolved',~valid&~inferred)]:
        choices=np.flatnonzero(mask[250:].any(axis=1))+250
        if len(choices): samples.add(int(choices[len(choices)//2]))
    samples.update([250,5000,16997])
    for frame in range(250,16998):
        ok,img=cap.read(); assert ok, frame
        last[valid[frame]]=xy[frame,valid[frame]]
        arena=cv2.resize(img[90:550,750:1390],(1280,920))
        canvas=np.full((920,1740,3),24,dtype=np.uint8); canvas[:,:1280]=arena
        def label(text,y,color=(235,235,235),scale=.65):
            cv2.putText(canvas,text,(1300,y),cv2.FONT_HERSHEY_SIMPLEX,scale,color,1,cv2.LINE_AA)
        label('OLD | Frame '+str(frame),40,scale=.85)
        label('Native IDtracker dots / trails',80)
        label('120-frame movement history',110)
        for animal in range(6):
            y=175+animal*90
            if valid[frame,animal]:
                group_members=np.flatnonzero((anchors[frame]==animal)&inferred[frame])
                state='ASSIGNED'; color=(230,180,70)
                detail='Anchor for '+','.join(map(str,group_members)) if len(group_members) else 'Coordinate present'
            elif inferred[frame,animal]:
                state='PRESUMED SOCIAL'; color=(20,200,245)
                anchor=int(anchors[frame,animal]); detail='With visible ID '+str(anchor)
                pt=np.rint((xy[frame,anchor]*.46875-[750,90])*2).astype(int)
                cv2.circle(canvas,tuple(pt),18,color,2,cv2.LINE_AA)
            else:
                state='UNRESOLVED LOSS'; color=(50,90,255); detail='X = last assigned position'
                if np.isfinite(last[animal]).all():
                    pt=np.rint((last[animal]*.46875-[750,90])*2).astype(int)
                    cv2.drawMarker(canvas,tuple(pt),color,cv2.MARKER_TILTED_CROSS,22,2)
                    cv2.putText(canvas,'lost '+str(animal),tuple(pt+[12,-12]),cv2.FONT_HERSHEY_SIMPLEX,.7,color,2)
            label('ID '+str(animal)+'  '+state,y,color)
            label(detail,y+28,color,.55)
        label('Amber ring = presumed position',755,(20,200,245))
        label('Red X = last assigned, not current',785,(50,90,255),.58)
        label('60 px proximity rule; groups allowed',825,scale=.56)
        label('Presumed contact is not confirmed.',858,scale=.56)
        label('Unresolved is not proven tracker error.',888,scale=.54)
        encoder.stdin.write(canvas.tobytes())
        if frame in samples: cv2.imwrite(str(ROOT/f'audit_frame_{frame}.png'),canvas)
        if frame%1000==0: print('Rendered frame',frame,flush=True)
    encoder.stdin.close(); assert encoder.wait()==0
    cap.release()
    (ROOT/'audit_status.json').write_text(json.dumps(dict(stage='COMPLETE_UNREVIEWED',
        video=str(output),frames=16748,sha256=hashlib.sha256(output.read_bytes()).hexdigest()),indent=2))


if __name__=='__main__': render()
