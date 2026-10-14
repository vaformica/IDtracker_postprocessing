"""Add display-only controls to supported viewer templates and rendered pages."""
from pathlib import Path
import sys, json, hashlib
MARK='<!-- clear-backs-label-controls-v1 -->'
COMMON='''
function offsetArrow(ctx,x,y,label,color,id=0){
 const w=ctx.canvas.width,h=ctx.canvas.height,s=Math.min(w,h)/920;
 const angle=(-150+(id%6)*60)*Math.PI/180;
 let dx=Math.cos(angle)*110*s,dy=Math.sin(angle)*110*s;
 if(x+dx<50*s||x+dx>w-130*s)dx=-dx;
 if(y+dy<35*s||y+dy>h-30*s)dy=-dy;
 const len=Math.hypot(dx,dy),ux=dx/len,uy=dy/len,tx=x+ux*30*s,ty=y+uy*30*s;
 ctx.save();ctx.strokeStyle=ctx.fillStyle=color;ctx.lineWidth=2*s;ctx.globalAlpha=.7;
 ctx.beginPath();ctx.moveTo(x+dx,y+dy);ctx.lineTo(tx,ty);ctx.moveTo(tx+ux*12*s-uy*5*s,ty+uy*12*s+ux*5*s);ctx.lineTo(tx,ty);ctx.lineTo(tx+ux*12*s+uy*5*s,ty+uy*12*s-ux*5*s);ctx.stroke();
 ctx.globalAlpha=1;ctx.font=`bold ${22*s}px system-ui`;ctx.fillText(label,x+dx-10*s,y+dy-10*s);ctx.restore();
}
const styleMenu=document.createElement('select');styleMenu.id='videoLabelStyle';styleMenu.setAttribute('aria-label','Video labels');
styleMenu.innerHTML='<option value="offset">Offset arrows · clear backs</option><option value="none">No labels / overlays</option><option value="original">Original labels + trails</option>';
'''
def patch(s):
 if MARK in s:return s
 if 'function draw(global)' in s and 'viewComparison' in s:
  body="""
 document.getElementById('rawMode').parentElement.parentElement.append(styleMenu);
 const originalDraw=draw;draw=function(global){originalDraw(global);if(styleMenu.value==='original')return;
 ctx.clearRect(0,0,c.width,c.height);if(styleMenu.value==='none')return;
 const t=Math.max(0,Math.min(D.end-D.start,global-D.start));
 for(let a=0;a<animalCount;a++){const q=point((rawMode()?D.raw:D.held)[t][a]);if(q)offsetArrow(ctx,...q,String(a)+(!rawMode()&&D.inferred[t][a]?' PSC':''),color(a),a)}
 };styleMenu.onchange=()=>draw(+slider.value);draw(+slider.value);
"""
 elif 'function drawOverlay()' in s and 'overlayOn' in s:
  track='shownTrack()[i]' if 'function shownTrack()' in s else 'data.proposed[i]'
  body="""
 document.getElementById('overlayOn').parentElement.parentElement.append(styleMenu);
 const originalOverlay=drawOverlay;drawOverlay=function(){originalOverlay();if(styleMenu.value==='original')return;
 const canvas=$('overlay'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
 if(styleMenu.value==='none'||!data||!$('overlayOn').checked)return;
 const i=frame-run.start,q=TRACK;
 if(q&&q[0]!=null)offsetArrow(ctx,q[0]-data.crop[0],q[1]-data.crop[1],'ID 0','#00bfa5');
 };styleMenu.onchange=drawOverlay;$('overlayOn').onchange=drawOverlay;drawOverlay();
""".replace('TRACK',track)
 elif 'function draw(i)' in s and 'D.geometry' in s and 'D.frames' in s:
  body="""
 document.getElementById('trails').parentElement.parentElement.append(styleMenu);
 const originalDraw=draw;draw=function(i){originalDraw(i);if(styleMenu.value==='original')return;
 ctx.clearRect(0,0,1280,920);if(styleMenu.value==='none')return;
 const f=D.frames[Math.max(0,Math.min(D.frames.length-1,i))];
 if(f.location_known)offsetArrow(ctx,...point(f.x,f.y),'ID 0','#ffce56');
 };styleMenu.onchange=()=>draw(+slider.value);draw(+slider.value);
"""
 else:return s
 # The same script shares the viewer's lexical data bindings without modifying data or scores.
 return s+'\n'+MARK+'\n<script>\n'+COMMON+body+'\n</script>\n'
if __name__=='__main__':
 changed=[]
 for arg in sys.argv[1:]:
  p=Path(arg);s=p.read_text();new=patch(s)
  if new!=s:
   backup=p.with_suffix(p.suffix+'.before_label_controls');backup.write_text(s);p.write_text(new);changed.append(str(p))
 print(json.dumps(changed,indent=2))
