'use strict';
const $=id=>document.getElementById(id), C=IdentityCore, meta=D.identity;
const video=$('video'),canvas=$('overlay'),ctx=canvas.getContext('2d');
let current=D.initial_frame,anchor=current,selected=null,target=null,log=[],redo=[],pending=null,preview=null,corrected=D.raw,seekTarget=null,dirty=false,suggestion=null;
const rawLayer={data:D.raw,source:D.raw.map(row=>row.map(p=>C.valid(p)?'ASSIGNED':'MISSING'))};let acceptedLayer=rawLayer,previewLayer=null;
const colors=['#52b6ff','#ffb858','#76dc84','#ff7373','#dca2ff','#eddf83'];
const draftKey='identity-corrector-v1:'+meta.canonical_sha256+':'+meta.analysis_manifest_sha256;
const rawWarnings=C.warnings(D.raw,meta.frame_start);let warningIndex=-1;
$('title').textContent=D.label+' · identity correction';document.title=D.label+' · identity corrector';video.src=D.video;video.playbackRate=.25;
for(const id of ['slider','frame','first','last']){$(id).min=meta.frame_start;$(id).max=meta.frame_end_inclusive;$(id).value=current}
$('reported').hidden=!(meta.frame_start<=855&&855<=meta.frame_end_inclusive&&D.label==='groupagetrial04_062124_Box01_MIX');
const pscMode=()=>false;
function message(s){$('message').textContent=s}
function discardPreview(){pending=null;preview=null;previewLayer=null;$('accept').disabled=true;$('previewNote').textContent='';}
function choose(a){video.pause();if(seekTarget!==null){message('Wait for the frame to finish seeking.');return}if($('original').checked){message('Turn off Raw IDtracker labels before selecting a beetle.');return}discardPreview();suggestion=null;selected=a;target=null;anchor=current;$('first').value=current;$('last').value=current;updateSelection();render();message(pscMode()?'Choose the pile partner (or click it), then inspect the PSC interval.':'Choose the correct ID, then select or set the interval.')}
function chooseTarget(a){if(selected===null){message('First click the beetle that has the wrong label.');return}discardPreview();target=a;updateSelection();suggestTrack();render()}
for(let a=0;a<meta.animal_count;a++){
 const b=document.createElement('button');b.textContent=a;b.setAttribute('aria-label','Select current ID '+a);b.onclick=()=>choose(a);$('sourceButtons').append(b);
 const t=document.createElement('button');t.textContent=a;t.setAttribute('aria-label','Correct selected beetle to ID '+a);t.style.color=colors[a%colors.length];t.onclick=()=>chooseTarget(a);$('identityButtons').append(t);
}
function updateSelection(){
 $('selection').textContent=selected===null?'Click a beetle in the video.':`${pscMode()?'Pile member':'Selected ID'} ${selected} at frame ${anchor}`;
 [...$('sourceButtons').children].forEach((b,a)=>b.classList.toggle('active',a===selected));
 [...$('identityButtons').children].forEach((b,a)=>{b.classList.toggle('active',a===target);b.disabled=a===selected});
}
function selectedLayer(){return $('original').checked?rawLayer:previewLayer||acceptedLayer}
function render(){
 const t=current-meta.frame_start,layer=selectedLayer(),data=layer.data;ctx.clearRect(0,0,canvas.width,canvas.height);
 $('slider').value=current;$('frame').value=current;
 $('frameInfo').textContent=`Global ${current} · clip frame ${t+1} · ${(t/D.fps).toFixed(2)} s · ${$('original').checked?'ORIGINAL':preview?'PREVIEW':'ACCEPTED LABELS'}`;
 if(!$('hideLabels').checked&&$('trails').checked)for(let a=0;a<meta.animal_count;a++){
  for(let j=Math.max(1,t-59);j<=t;j++){const p=C.project(data[j-1][a],D.geometry),q=C.project(data[j][a],D.geometry);if(!p||!q)continue;
   const jump=C.distance(data[j-1][a],data[j][a])>100;ctx.strokeStyle=jump?'#ff5555':colors[a%colors.length];ctx.globalAlpha=.15+.5*(j-Math.max(1,t-59)+1)/60;ctx.lineWidth=2;ctx.setLineDash(jump?[7,5]:[]);ctx.beginPath();ctx.moveTo(...p);ctx.lineTo(...q);ctx.stroke();
  }
 }
 ctx.globalAlpha=1;ctx.setLineDash([]);
 let missing=[];
 for(let a=0;a<meta.animal_count;a++){
  const p=C.project(data[t][a],D.geometry);if(!p){missing.push(a);continue}if($('hideLabels').checked)continue
  ctx.fillStyle=colors[a%colors.length];ctx.strokeStyle='#101820';ctx.lineWidth=3;ctx.beginPath();ctx.arc(...p,10,0,Math.PI*2);if(layer.source[t][a]!=='HUMAN_PSCP')ctx.fill();else ctx.strokeStyle=colors[a%colors.length];ctx.stroke();
  if(a===selected){ctx.strokeStyle='white';ctx.beginPath();ctx.arc(...p,19,0,Math.PI*2);ctx.stroke()}
  ctx.font='bold 27px system-ui';ctx.lineWidth=5;const label=String(a)+(layer.source[t][a]==='HUMAN_PSCP'?' PSC':'');const offset=layer.source[t][a]==='HUMAN_PSCP'?24*(a+1):0;ctx.strokeText(label,p[0]+17,p[1]-12+offset);ctx.fillText(label,p[0]+17,p[1]-12+offset);
 }
 const now=rawWarnings.filter(w=>w.frame===current).map(w=>`ID ${w.animal}: ${w.distance_px.toFixed(1)} px ${w.kind==='adjacent_jump'?'one-frame jump':`return after ${w.gap_frames} missing frames`}`);
 $('status').textContent=`Missing locations: ${missing.join(', ')||'none'}. ${layer.source[t].map((s,a)=>s==='HUMAN_UNRESOLVED'?'ID '+a+': pile, location unknown':s==='HUMAN_PSCP'?'ID '+a+': human PSC':'').filter(Boolean).join('; ')} ${now.length?'Raw warning — '+now.join('; '):''}`;
 $('play').textContent=video.paused?'Play':'Pause';drawTimeline();
}
function seek(f){const n=Number(f);if(!Number.isFinite(n)){message('Enter a valid global frame.');return}video.pause();current=Math.max(meta.frame_start,Math.min(meta.frame_end_inclusive,Math.round(n)));seekTarget=current;video.currentTime=(current-meta.frame_start+.5)/D.fps;render()}
canvas.onclick=e=>{
 if(pending){message('Accept or cancel the preview before selecting another beetle.');return}
 if(!video.paused||video.seeking||seekTarget!==null){video.pause();message('Paused. Click again once the frame is still.');return}
 if($('original').checked){message('Turn off Raw IDtracker labels to edit.');return}
 const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*canvas.width/r.width,y=(e.clientY-r.top)*canvas.height/r.height;
 const hits=corrected[current-meta.frame_start].map((p,a)=>{const q=C.project(p,D.geometry);return {a,dist:q?Math.hypot(q[0]-x,q[1]-y):Infinity}}).filter(h=>h.dist<28*canvas.width/r.width).sort((a,b)=>a.dist-b.dist);
 if(hits.length>1&&hits[1].dist-hits[0].dist<12*canvas.width/r.width){message('Several labels overlap here. Select the current ID with the numbered buttons.');return}
 if(!hits.length){message('No detected centroid near that point. Select a current ID above, or seek to a clearer frame.');return}if(pscMode()&&selected!==null)chooseTarget(hits[0].a);else choose(hits[0].a);
};
$('single').onclick=()=>{suggestion=null;discardPreview();$('first').value=anchor;$('last').value=anchor;render()};
function suggestTrack(){if(selected===null||target===null)return;discardPreview();suggestion=C.follow(corrected,anchor,selected,target,meta,log);$('first').value=suggestion.lo;$('last').value=suggestion.hi;$('boundsNote').textContent=suggestion.reason;message('Proposed '+suggestion.segments.length+' correction segment(s). Preview to inspect, then save.');render()}
$('suggest').onclick=suggestTrack;
for(const [id,field] of [['markFirst','first'],['markLast','last']])$(id).onclick=()=>{suggestion=null;discardPreview();$(field).value=current;render()};
for(const [id,field] of [['visitFirst','first'],['visitLast','last']])$(id).onclick=()=>seek($(field).value);
for(const id of ['first','last','reviewer','reason'])$(id).oninput=()=>{if(id==='first'||id==='last')suggestion=null;discardPreview();render()};
function makeDecision(){return {id:globalThis.crypto?.randomUUID?.()||Date.now()+'-'+Math.random().toString(16).slice(2),kind:pscMode()?'pscp':'swap',mode:pscMode()?$('pscLocation').value:undefined,animal_a:selected,animal_b:target,anchor_frame:anchor,start_frame:Number($('first').value),end_frame_inclusive:Number($('last').value),reviewer:$('reviewer').value.trim(),reason:$('reason').value.trim(),created_utc:new Date().toISOString()}}
$('preview').onclick=()=>{try{
 const base=makeDecision();C.validate(base,meta);
 const segments=suggestion?suggestion.segments:[{lo:base.start_frame,hi:base.end_frame_inclusive}];
 if(!segments.length)throw Error('No changes proposed. Choose an uncorrected frame or undo the earlier correction.');
 pending=segments.map((r,i)=>({...base,id:base.id+'-'+i,batch_id:base.id,start_frame:r.lo,end_frame_inclusive:r.hi,anchor_frame:Math.max(r.lo,Math.min(anchor,r.hi)),clicked_frame:anchor,proposal:suggestion?'motion-follow-v1':'manual-range'}));
 preview=C.replay(D.raw,[...log,...pending],meta);previewLayer=C.pscLayer(preview,[],meta);$('original').checked=false;$('accept').disabled=false;
 $('previewNote').textContent=`Preview: IDs ${selected} ↔ ${target}; ${pending.length} segment(s), ${pending.reduce((n,d)=>n+d.end_frame_inclusive-d.start_frame+1,0)} changed frames. Dashed amber intervals are unsaved.`;
 message('Scrub to inspect the proposed labels. Save correction applies all shown segments together.');seek(anchor);
}catch(e){discardPreview();render();message(e.message)}};
$('cancel').onclick=()=>{discardPreview();render();message('Preview cancelled.')};
function exportData(){return {...meta,corrector_version:D.version,label:D.label,exported_utc:new Date().toISOString(),decisions:log}}
function persist(){try{localStorage.setItem(draftKey,JSON.stringify(exportData()));$('saveStatus').textContent='Draft saved in this browser. Export JSON to save a portable copy.'}catch(e){$('saveStatus').textContent='Browser draft storage unavailable. Export JSON before closing.'}}
function rebuild(){corrected=C.replay(D.raw,log,meta);acceptedLayer=C.pscLayer(corrected,log,meta);discardPreview();$('history').replaceChildren(...log.map(d=>{const li=document.createElement('li');const b=document.createElement('button');b.textContent=`${d.kind==='swap'?'Swap':'PSC '+(d.mode==='unresolved'?'unknown':'at partner')} ${d.animal_a} ↔ ${d.animal_b} · ${d.start_frame}–${d.end_frame_inclusive}`;b.onclick=()=>seek(d.anchor_frame);li.append(b,document.createTextNode(' · '+d.reviewer+' · '+d.reason));return li}));$('undo').disabled=!log.length;$('redo').disabled=!redo.length;render()}
$('accept').onclick=()=>{if(!pending)return;log.push(...pending);redo=[];dirty=true;suggestion=null;selected=null;target=null;$('original').checked=false;rebuild();updateSelection();persist();message('Saved to this editor. Playback and green timeline intervals now include the correction. Export JSON for reprocessing.')};
$('undo').onclick=()=>{if(log.length){const batch=log.at(-1).batch_id||log.at(-1).id,items=[];do{items.unshift(log.pop())}while(log.length&&(log.at(-1).batch_id||log.at(-1).id)===batch);redo.push(items);dirty=true;suggestion=null;rebuild();persist();message('Last saved correction undone.')}};
$('redo').onclick=()=>{if(redo.length){log.push(...redo.pop());dirty=true;suggestion=null;rebuild();persist();message('Correction restored.')}};
$('export').onclick=()=>{const b=new Blob([JSON.stringify(exportData(),null,2)+'\n'],{type:'application/json'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=D.label+'__identity_corrections.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);dirty=false;message(`Exported ${log.length} accepted correction(s). ${pending?'Preview was not exported. ':''}Return this JSON file to Codex for reprocessing.`)};
function importLog(data){for(const k of Object.keys(meta))if(data[k]!==meta[k])throw Error('This log belongs to a different source bundle ('+k+').');if(!Array.isArray(data.decisions))throw Error('Invalid correction log.');if(data.decisions.some(d=>d.kind!=='swap'))throw Error('This identity-only editor cannot import PSC decisions. Use the earlier PSC editor for that log.');C.replay(D.raw,data.decisions,meta);if(log.length&&!confirm('Replace the current accepted corrections with this log? Export first if you need to keep them.'))return;log=data.decisions;redo=[];suggestion=null;dirty=true;rebuild();persist();message('Imported and replayed '+log.length+' corrections.');}
$('import').onchange=async e=>{try{if(e.target.files.length)importLog(JSON.parse(await e.target.files[0].text()))}catch(error){message(error.message)}finally{e.target.value=''}};
try{const saved=localStorage.getItem(draftKey);if(saved&&JSON.parse(saved).decisions?.length){$('restore').hidden=false;$('restore').onclick=()=>{try{importLog(JSON.parse(saved));$('restore').hidden=true}catch(e){message(e.message)}}}}catch(e){}
const jumps=rawWarnings.filter(w=>w.kind==='adjacent_jump').length;$('warningCount').textContent=`${jumps} raw jumps · ${rawWarnings.length-jumps} distant returns`;
rawWarnings.forEach((w,i)=>$('warningSelect').add(new Option(`${w.frame} · ID ${w.animal} · ${w.distance_px.toFixed(0)} px · ${w.kind==='adjacent_jump'?'jump':`return (${w.gap_frames} missing)`}`,i)));
function goWarning(i){if(!rawWarnings.length)return;warningIndex=(i+rawWarnings.length)%rawWarnings.length;$('warningSelect').value=warningIndex;seek(rawWarnings[warningIndex].frame)}
$('warningSelect').onchange=e=>goWarning(Number(e.target.value));$('nextWarning').onclick=()=>{const i=rawWarnings.findIndex(w=>w.frame>current);goWarning(i<0?0:i)};$('previousWarning').onclick=()=>{let i=rawWarnings.length-1;while(i>=0&&rawWarnings[i].frame>=current)i--;goWarning(i)};
$('reported').onclick=()=>seek(855);$('previous').onclick=()=>seek(current-1);$('next').onclick=()=>seek(current+1);$('go').onclick=()=>seek($('frame').value);$('frame').onkeydown=e=>{if(e.key==='Enter')seek(e.target.value)};$('slider').oninput=e=>seek(e.target.value);
$('play').onclick=()=>{if(video.paused)video.play().catch(e=>message(e.message));else video.pause()};$('speed').onchange=e=>video.playbackRate=Number(e.target.value);$('original').onchange=render;$('hideLabels').onchange=render;$('trails').onchange=render;
video.addEventListener('loadedmetadata',()=>seek(D.initial_frame));video.addEventListener('seeked',()=>{if(seekTarget!==null){const actual=meta.frame_start+Math.floor(video.currentTime*D.fps+1e-5);if(Math.abs(actual-seekTarget)>0)return;current=seekTarget;seekTarget=null}render()});
video.addEventListener('play',render);video.addEventListener('pause',render);video.addEventListener('error',()=>{$('videoError').textContent='Video unavailable. Keep '+D.video+' beside this HTML, or download and unzip the complete package.'});
if(video.requestVideoFrameCallback){const tick=(_,m)=>{if(seekTarget===null&&!video.seeking){current=Math.min(meta.frame_end_inclusive,meta.frame_start+Math.floor(m.mediaTime*D.fps+1e-5));render()}video.requestVideoFrameCallback(tick)};video.requestVideoFrameCallback(tick)}else video.ontimeupdate=()=>{if(seekTarget===null&&!video.seeking){current=Math.min(meta.frame_end_inclusive,meta.frame_start+Math.floor(video.currentTime*D.fps+1e-5));render()}};
document.onkeydown=e=>{if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;if(e.key===' '){e.preventDefault();$('play').click()}else if(e.key==='ArrowLeft'){e.preventDefault();seek(current-1)}else if(e.key==='ArrowRight'){e.preventDefault();seek(current+1)}else if(/^\d$/.test(e.key)&&Number(e.key)<meta.animal_count)chooseTarget(Number(e.key))};
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});
rebuild();updateSelection();

function drawTimeline(){const c=$('timeline'),g=c.getContext('2d'),span=meta.frame_end_inclusive-meta.frame_start+1;g.clearRect(0,0,c.width,c.height);g.fillStyle='#101820';g.fillRect(0,0,c.width,c.height);
 const x=f=>(f-meta.frame_start)/span*c.width;
 for(const d of log){g.fillStyle='#55c89d';g.fillRect(x(d.start_frame),6,Math.max(2,x(d.end_frame_inclusive+1)-x(d.start_frame)),16)}
 for(const d of pending||[]){g.strokeStyle='#ffd06d';g.setLineDash([4,3]);g.strokeRect(x(d.start_frame),26,Math.max(2,x(d.end_frame_inclusive+1)-x(d.start_frame)),12)}
 g.setLineDash([]);g.strokeStyle='white';g.beginPath();g.moveTo(x(current),0);g.lineTo(x(current),44);g.stroke();
 $('timelineSummary').textContent=log.length?`${new Set(log.map(d=>d.batch_id||d.id)).size} saved correction(s) · Green: saved · Amber: preview`:'No saved corrections · Amber: preview';
}
$('timeline').onclick=e=>{const r=e.currentTarget.getBoundingClientRect();seek(meta.frame_start+Math.floor((e.clientX-r.left)/r.width*(meta.frame_end_inclusive-meta.frame_start+1)))};
