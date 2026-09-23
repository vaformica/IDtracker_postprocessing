// Portable review layer. Decisions are exported; the source bundle is immutable.
(()=>{
const $=id=>document.getElementById(id), fields=['held','fungus','accepted','inferred','reviewed','pileStatus','pairStates'];
const base=Object.fromEntries(fields.map(k=>[k,structuredClone(D[k])]));
const count=D.held[0].length, log=__INITIAL_DECISIONS__;
const settings=D.modelSettings||{};
$('modelSettings').textContent=`Automatic settings: proximity ${D.proximityThreshold} px; split confirmation ${settings.split_confirmation_frames??'unknown'} frames; gap search growth ${settings.gap_speed_px_per_frame??'unknown'} px/frame, cap ${settings.gap_radius_cap_px??'unknown'} px, maximum gap ${settings.max_reacquire_gap_frames??'unknown'} frames. Frame corrections below preview here; change these model settings in the Firebird post-processing GUI and rerun for a new automatic analysis.`;
const animal=$('reviewAnimal'),partner=$('reviewPartner'),kind=$('reviewKind'),value=$('reviewValue');
for(let a=0;a<count;a++){animal.add(new Option(String(a),String(a)));partner.add(new Option(String(a),String(a)))}
partner.value=count>1?'1':'0';$('reviewStart').value=D.start;$('reviewEnd').value=D.start;
animal.onchange=()=>{if(animal.value===partner.value)partner.value=String((Number(animal.value)+1)%count)};
$('useStart').onclick=()=>$('reviewStart').value=slider.value;
$('useEnd').onclick=()=>$('reviewEnd').value=slider.value;
function values(){
 const entries=kind.value==='pscp'?[['Presumed contact; use partner position when detected','yes'],['No presumed contact','no'],['Pile membership, location unknown','unresolved'],['Automatic result','automatic']]:
 kind.value==='proximity'?[['Visible proximity','yes'],['No proximity','no'],['Automatic result','automatic']]:
 kind.value==='location'?[['Use partner position (reviewed PSCP)','partner'],['Missing location','missing'],['Accept raw IDtracker coordinate','raw'],['Automatic result','automatic']]:
 [['Automatic result','automatic'],['Off fungus','0'],...D.rois.slice(1).map((_,i)=>['On fungus '+(i+1),String(i+1)])];
 value.replaceChildren(...entries.map(([label,key])=>new Option(label,key)));
}
kind.onchange=values;values();
function pairIndex(a,b){return D.pairs.findIndex(p=>p[0]===Math.min(a,b)&&p[1]===Math.max(a,b))}
function valid(p){return p&&p[0]!=null&&p[1]!=null}
function inPolygon(p,poly){let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
 const x=poly[i][0],y=poly[i][1],xx=poly[j][0],yy=poly[j][1];
 if((y>p[1])!==(yy>p[1])&&p[0]<(xx-x)*(p[1]-y)/(yy-y)+x)inside=!inside;
}return inside}
function fungusAt(p){if(!valid(p))return 0;let f=0;D.rois.slice(1).forEach((poly,i)=>{if(inPolygon(p,poly))f=i+1});return f}
function applyOne(d){
 const a=d.animal_id,b=d.partner_id,k=pairIndex(a,b),lo=d.start_frame-D.start,hi=d.end_frame_inclusive-D.start;
 for(let t=lo;t<=hi;t++){
  if(d.kind==='location'||d.kind==='pscp'&&(d.value==='yes'||d.value==='unresolved')){
   const mode=d.kind==='pscp'?(d.value==='unresolved'?'missing':'partner'):d.value;
   let p=mode==='automatic'?base.held[t][a]:mode==='raw'?D.raw[t][a]:mode==='missing'?null:D.held[t][b];
   D.held[t][a]=valid(p)?[...p]:[null,null];
   D.accepted[t][a]=mode==='automatic'?base.accepted[t][a]:mode==='raw'?1:0;
   D.inferred[t][a]=mode==='automatic'?base.inferred[t][a]:mode==='partner'&&valid(p)?1:0;
   D.reviewed[t][a]=mode==='automatic'?base.reviewed[t][a]:1;
   D.pileStatus[t][a]=mode==='automatic'?base.pileStatus[t][a]:mode==='raw'?'HUMAN_RAW':mode==='missing'?(d.kind==='pscp'?'HUMAN_UNRESOLVED':'HUMAN_MISSING'):valid(p)?'HUMAN_PSCP':'HUMAN_UNRESOLVED';
   D.fungus[t][a]=mode==='automatic'?base.fungus[t][a]:fungusAt(D.held[t][a]);
   D.human[t][a]=1;
   if(k>=0&&mode==='partner')D.pairStates[k][t]=valid(p)?3:4;
   if(k>=0&&mode==='missing')D.pairStates[k][t]=base.pairStates[k][t]===2||base.pairStates[k][t]===4?4:0;
   if(k>=0&&mode==='raw')D.pairStates[k][t]=base.pairStates[k][t];
  }
  if(d.kind==='fungus'){D.fungus[t][a]=d.value==='automatic'?base.fungus[t][a]:Number(d.value);D.human[t][a]=1}
  if(k>=0&&d.kind==='proximity')D.pairStates[k][t]=d.value==='automatic'?base.pairStates[k][t]:d.value==='yes'?1:0;
  if(k>=0&&d.kind==='pscp')D.pairStates[k][t]=d.value==='automatic'?base.pairStates[k][t]:d.value==='no'?0:d.value==='unresolved'?4:valid(D.held[t][a])&&valid(D.held[t][b])?3:4;
  if(k>=0&&(d.kind==='pscp'||d.kind==='proximity')){D.human[t][a]=1;D.human[t][b]=1}
 }
}
function rebuild(){
 for(const key of fields)D[key]=structuredClone(base[key]);
 D.human=Array.from({length:D.held.length},()=>Array(count).fill(0));
 for(const d of log)applyOne(d);
 paintTimeline();draw(+slider.value);
 $('reviewHistory').replaceChildren(...log.slice(-40).map(d=>{let li=document.createElement('li');li.textContent=`${d.created_utc} · ${d.reviewer} · ${d.kind} ${d.value} · beetle ${d.animal_id}${d.partner_id==null?'':' with '+d.partner_id} · frames ${d.start_frame}–${d.end_frame_inclusive} · ${d.reason}`;return li}));
 $('reviewMessage').textContent=`${log.length} reviewed decision(s) in memory. Export the log to save them; automatic source data remain unchanged.`;
}
function validate(d){
 if(!d.reviewer||!d.reason||!d.created_utc)throw Error('Reviewer, reason, and timestamp are required for every decision.');
 if(!Number.isInteger(d.start_frame)||!Number.isInteger(d.end_frame_inclusive)||d.start_frame<D.start||d.end_frame_inclusive>D.end||d.end_frame_inclusive<d.start_frame)throw Error('Choose an inclusive frame range inside this video.');
 if(!Number.isInteger(d.animal_id)||d.animal_id<0||d.animal_id>=count)throw Error('Invalid beetle.');
 if(!['pscp','proximity','location','fungus'].includes(d.kind))throw Error('Invalid decision type.');
 if(d.kind!=='fungus'&&(!Number.isInteger(d.partner_id)||d.partner_id<0||d.partner_id>=count||d.partner_id===d.animal_id))throw Error('Choose a different partner.');
 const allowed={pscp:['yes','no','unresolved','automatic'],proximity:['yes','no','automatic'],location:['partner','missing','raw','automatic'],fungus:['automatic','0',...D.rois.slice(1).map((_,i)=>String(i+1))]};
 if(!allowed[d.kind].includes(d.value))throw Error('Invalid decision value.');
 if(d.kind==='location'&&d.value==='raw')for(let f=d.start_frame;f<=d.end_frame_inclusive;f++)if(!valid(D.raw[f-D.start][d.animal_id]))throw Error(`Raw coordinate is absent at frame ${f}.`);
 if(d.kind==='proximity'&&d.value==='yes')for(let f=d.start_frame;f<=d.end_frame_inclusive;f++)if(!valid(D.held[f-D.start][d.animal_id])||!valid(D.held[f-D.start][d.partner_id]))throw Error(`Visible proximity needs both locations at frame ${f}. Review locations first.`);
 if(d.kind==='fungus'&&d.value!=='automatic')for(let f=d.start_frame;f<=d.end_frame_inclusive;f++)if(!valid(D.held[f-D.start][d.animal_id]))throw Error(`Cannot assign fungus without a location at frame ${f}. Review the position first.`);
}
$('applyReview').onclick=()=>{try{
 const d={created_utc:new Date().toISOString(),reviewer:$('reviewer').value.trim(),reason:$('reviewReason').value.trim(),kind:kind.value,value:value.value,animal_id:Number(animal.value),partner_id:kind.value==='fungus'?null:Number(partner.value),start_frame:Number($('reviewStart').value),end_frame_inclusive:Number($('reviewEnd').value)};
 validate(d);log.push(d);rebuild();
}catch(e){$('reviewMessage').textContent=e.message}};
$('undoReview').onclick=()=>{log.pop();rebuild()};
$('exportReview').onclick=()=>{
 const documentData={schema:'beetle-review-v1',analysis_manifest_sha256:D.analysisManifestSha256,canonical_sha256:D.canonicalSha256,frame_start:D.start,frame_end_inclusive:D.end,exported_utc:new Date().toISOString(),decisions:log};
 const blob=new Blob([JSON.stringify(documentData,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='beetle_review_'+D.start+'_'+D.end+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
$('importReview').onchange=async e=>{try{
 const data=JSON.parse(await e.target.files[0].text());
 if(data.schema!=='beetle-review-v1'||data.analysis_manifest_sha256!==D.analysisManifestSha256||data.canonical_sha256!==D.canonicalSha256||data.frame_start!==D.start||data.frame_end_inclusive!==D.end)throw Error('Review log does not match this exact analysis bundle.');
 for(const d of data.decisions)validate(d);
 log.splice(0,log.length,...data.decisions);rebuild();
}catch(error){$('reviewMessage').textContent=error.message}};
rebuild();
})();
