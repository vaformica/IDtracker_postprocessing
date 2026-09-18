"""Synthetic QA fixture only: never use as biological research data."""
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from six_beetle_processor import main

def make_fixture(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    t=np.arange(7402,dtype=float)
    arr=np.empty((len(t),6,2))
    for i in range(6):
        arr[:,i,0]=500+330*np.cos(t/430+i*.55)
        arr[:,i,1]=400+250*np.sin(t/570+i*.55)
    arr[2200:2220,0]=np.nan
    arr[4300,4]=[2500,2500]
    # Demonstrate concurrent proximity and ambiguous disappearance.
    arr[3100:3200,1]=arr[3100:3200,0]+[15,0]
    arr[3100:3200,2]=arr[3100:3200,0]+[25,0]
    arr[3140:3150,0]=np.nan
    rois=[[[0,0],[1000,0],[1000,800],[0,800]]]
    for x,y in [(220,220),(420,530),(600,240)]:
        rois.append([[x,y],[x+130,y],[x+130,y+100],[x,y+100]])
    (root/'session.json').write_text(json.dumps({'roi_list':rois},indent=2))
    np.save(root/'trajectories.npy',{'trajectories':arr})
    return root

if __name__=='__main__':
    root=make_fixture(sys.argv[1])
    sys.argv=['six_beetle_processor.py','--trajectory',str(root/'trajectories.npy'),'--session',str(root),'--start','1','--window','7200','--video','SYNTHETIC DEMONSTRATION - NOT RESEARCH DATA','--cell-label','DEMO','--output',str(root/'analysis')]
    main()
