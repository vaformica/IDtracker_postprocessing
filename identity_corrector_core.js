/* Shared browser/test logic. Original data never mutated. */
(function(root){
'use strict';
const valid=p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite);
const distance=(a,b)=>valid(a)&&valid(b)?Math.hypot(a[0]-b[0],a[1]-b[1]):NaN;
function validate(d,meta){
 if(!d||!['swap','pscp'].includes(d.kind))throw Error('Unsupported correction type.');
 if(d.kind==='pscp'&&!['partner','unresolved'].includes(d.mode))throw Error('Choose a PSC location option.');
 for(const k of ['id','reviewer','reason','created_utc'])if(typeof d[k]!=='string'||!d[k].trim())throw Error('Enter your name and a reason.');
 const [a,b,lo,hi,f]=['animal_a','animal_b','start_frame','end_frame_inclusive','anchor_frame'].map(k=>d[k]);
 if(![a,b,lo,hi,f].every(Number.isInteger)||a<0||b<0||a>=meta.animal_count||b>=meta.animal_count||a===b)throw Error('Choose two different beetle IDs.');
 if(!(meta.frame_start<=lo&&lo<=f&&f<=hi&&hi<=meta.frame_end_inclusive))throw Error('The range must include the clicked frame and stay inside this video.');
}
function replay(raw,log,meta){
 const data=raw.map(row=>row.map(p=>p.slice())),seen=new Set();
 for(const d of log){validate(d,meta);if(seen.has(d.id))throw Error('Duplicate correction ID.');seen.add(d.id);if(d.kind==='pscp')continue;
  for(let t=d.start_frame-meta.frame_start;t<=d.end_frame_inclusive-meta.frame_start;t++)[data[t][d.animal_a],data[t][d.animal_b]]=[data[t][d.animal_b],data[t][d.animal_a]];
 }pscLayer(data,log,meta);return data;
}
function pscLayer(corrected,log,meta){
 const data=corrected.map(row=>row.map(p=>p.slice())),source=corrected.map(row=>row.map(p=>valid(p)?'ASSIGNED':'MISSING'));
 for(const d of log){if(d.kind!=='pscp')continue;
  for(let t=d.start_frame-meta.frame_start;t<=d.end_frame_inclusive-meta.frame_start;t++){
   if(valid(corrected[t][d.animal_a]))throw Error(`ID ${d.animal_a} is detected at frame ${t+meta.frame_start}. Keep its ID; choose a missing-only PSC interval.`);
   if(d.mode==='partner'&&!valid(corrected[t][d.animal_b]))throw Error(`Partner ${d.animal_b} is missing at frame ${t+meta.frame_start}. Shorten the interval or choose location unknown.`);
   data[t][d.animal_a]=d.mode==='partner'?corrected[t][d.animal_b].slice():[null,null];source[t][d.animal_a]=d.mode==='partner'?'HUMAN_PSCP':'HUMAN_UNRESOLVED';
  }
 }return {data,source};
}
function suggestPSC(data,frame,a,b,meta,mode){
 const t=frame-meta.frame_start;let lo=t,hi=t;
 const okay=i=>!valid(data[i][a])&&(mode==='unresolved'||valid(data[i][b]));
 const cross=(x,y)=>okay(y)&&(mode==='unresolved'||distance(data[x][b],data[y][b])<=100);
 if(!okay(t))return {lo:frame,hi:frame,reason:'PSC needs a missing ID; a located pile also needs a detected partner.'};
 while(lo>0&&cross(lo,lo-1))lo--;while(hi<data.length-1&&cross(hi,hi+1))hi++;
 return {lo:lo+meta.frame_start,hi:hi+meta.frame_start,reason:'Candidate missing-ID interval. Inspect the whole interval to confirm it is the same pile; missingness alone is not contact evidence.'};
}
function warnings(raw,start,threshold=100){
 const out=[];
 for(let a=0;a<raw[0].length;a++){let previous=null;
  for(let t=0;t<raw.length;t++){if(!valid(raw[t][a]))continue;
   if(previous!==null){const gap=t-previous,dist=distance(raw[t][a],raw[previous][a]);
    if(dist>threshold)out.push({kind:gap===1?'adjacent_jump':'return_after_gap',frame:start+t,previous_frame:start+previous,animal:a,distance_px:dist,gap_frames:gap-1});
   }previous=t;
  }
 }return out.sort((a,b)=>a.frame-b.frame||a.animal-b.animal);
}
function isolated(data,t,ids,radius){
 for(const a of ids){if(!valid(data[t][a]))return false;
  for(let b=0;b<data[t].length;b++)if(b!==a&&distance(data[t][a],data[t][b])<=radius)return false;
 }return true;
}
function suggest(data,frame,a,b,meta,radius=60,jump=100){
 const t=frame-meta.frame_start,ids=[a,b];let lo=t,hi=t;
 if(!isolated(data,t,ids,radius))return {lo:frame,hi:frame,reason:'At this frame an ID is missing or within 60 px of another beetle. No automatic extension; inspect and set explicit bounds.'};
 function canCross(x,y){return isolated(data,y,ids,radius)&&ids.every(a=>distance(data[x][a],data[y][a])<=jump)}
 while(lo>0&&canCross(lo,lo-1))lo--;
 while(hi<data.length-1&&canCross(hi,hi+1))hi++;
 return {lo:lo+meta.frame_start,hi:hi+meta.frame_start,reason:'Suggested interval stops at a gap, proximity ≤60 px, jump >100 px, or video boundary. This is a coordinate-based proposal, not proven identity.'};
}
// Follow the two physical paths, allowing clear raw-channel reversals.
// Suggestions never invent coordinates or cross a close encounter / uncertain match.
function follow(data,frame,a,b,meta,log=[],radius=60,jump=100,margin=20){
 const t=frame-meta.frame_start, states=new Map([[t,a]]), stops=[];
 const protectedAt=i=>log.some(d=>d.start_frame<=i+meta.frame_start&&i+meta.frame_start<=d.end_frame_inclusive&&[d.animal_a,d.animal_b].some(x=>x===a||x===b));
 const clear=(i,k)=>valid(data[i][k])&&data[i].every((p,j)=>j===k||!valid(p)||distance(data[i][k],p)>radius);
 if(protectedAt(t))return {lo:frame,hi:frame,segments:[],reason:'This frame already has a saved correction for these IDs. Undo it first or use explicit manual bounds.'};
 function walk(dir){let i=t,k=a,other=b,prev=null,prevOther=null;
  while(i+dir>=0&&i+dir<data.length){
   const j=i+dir;if(protectedAt(j)){stops.push('saved correction at '+(j+meta.frame_start));break}
   if(!clear(i,k)||(valid(data[i][other])&&!clear(i,other))){stops.push('close encounter or missing path at '+(i+meta.frame_start));break}
   function match(index,previous){const p=data[i][index];if(!valid(p))return null;
    const pred=previous?[p[0]+p[0]-previous[0],p[1]+p[1]-previous[1]]:p;
    const candidates=data[j].map((q,id)=>({id,step:distance(p,q),score:.65*distance(p,q)+.35*distance(pred,q)})).filter(c=>Number.isFinite(c.score)&&c.step<=jump).sort((x,y)=>x.score-y.score);
    if(!candidates.length||candidates.length>1&&candidates[1].score-candidates[0].score<margin)return null;
    const winner=candidates[0].id;return [a,b].includes(winner)&&clear(j,winner)?winner:null;
   }
   const next=match(k,prev);let nextOther;
   if(next===null){stops.push('gap, competing path, third ID, or >100 px step at '+(j+meta.frame_start));break}
   if(valid(data[i][other])){nextOther=match(other,prevOther);if(nextOther===null||nextOther===next){stops.push('displaced ID is ambiguous at '+(j+meta.frame_start));break}}
   else {nextOther=next===a?b:a;if(valid(data[j][nextOther])){stops.push('other ID reappears at '+(j+meta.frame_start));break}}
   prev=data[i][k];prevOther=valid(data[i][other])?data[i][other]:null;k=next;other=nextOther;i=j;states.set(i,k);
  }
 }
 if(valid(data[t][a])){walk(-1);walk(1)}else stops.push('selected ID is missing');
 const indices=[...states.keys()].sort((x,y)=>x-y),segments=[];
 for(const i of indices){if(states.get(i)!==a)continue;const f=i+meta.frame_start,last=segments.at(-1);if(last&&last.hi===f-1)last.hi=f;else segments.push({lo:f,hi:f})}
 return {lo:indices[0]+meta.frame_start,hi:indices.at(-1)+meta.frame_start,segments,
 reason:'Followed backward and forward using distance and short-term motion. '+(stops.length?stops.join('; '):'Reached video boundaries.')+' Raw labels that already match are left alone. Proposal only; inspect before saving.'};
}
function project(p,g){if(!valid(p))return null;let [x,y,w,h]=g.crop,dx=p[0]-x,dy=p[1]-y;
 if(g.rotation_cw===90){[dx,dy]=[h-dy,dx];[w,h]=[h,w]}else if(g.rotation_cw===180){[dx,dy]=[w-dx,h-dy]}else if(g.rotation_cw===270){[dx,dy]=[dy,w-dx];[w,h]=[h,w]}
 return [g.pad_x+dx*g.content_width/w,g.pad_y+dy*g.content_height/h];}
const api={valid,distance,validate,replay,pscLayer,suggestPSC,warnings,suggest,follow,project};
if(typeof module!=='undefined')module.exports=api;root.IdentityCore=api;
})(globalThis);
