/* Manual requests remain separate from automatic QC and biological scores. */
(function(root){
'use strict';
const schema='ba-manual-review-flags-v1';
function validate(data,index,hash){
 if(!data||data.schema!==schema||data.dataset_id!==index.id||data.index_sha256!==hash||typeof data.reviewer!=='string'||!data.reviewer.trim()||!Array.isArray(data.flags))throw Error('Wrong dataset or invalid reviewer/export.');
 const ids=new Set(index.runs.map(r=>r.id)),seen=new Set();
 for(const f of data.flags){if(!f||!ids.has(f.run_id)||seen.has(f.run_id)||typeof f.requested!=='boolean'||!['tracking','turtling','injury','other'].includes(f.reason)||typeof f.notes!=='string'||f.notes.length>20000)throw Error('Invalid or duplicate run flag.');seen.add(f.run_id)}
 return structuredClone(data);
}
function exportFlags(index,hash,reviewer,flags){return validate({schema,dataset_id:index.id,index_sha256:hash,reviewer,exported_utc:new Date().toISOString(),scope:'Review requests only; no approval, exclusion or posture edits',flags:Object.entries(flags).map(([run_id,f])=>({run_id,...f}))},index,hash)}
function matches(r,filter,query,flags){
 const text=(r.id+' '+r.label+' '+r.video+' '+r.flags.map(f=>f.code+' '+f.reason).join(' ')).toLowerCase();
 if(query&&!text.includes(query.toLowerCase()))return false;
 if(filter==='manual')return !!flags[r.id]?.requested;
 if(filter==='unscored')return r.human_review.reviewed_frames===0;
 if(filter==='high')return r.priority==='high';
 if(filter==='tracking')return r.flags.some(f=>f.domain.includes('tracking'));
 if(filter==='behavior')return r.flags.some(f=>f.domain.includes('behavior'));
 if(filter==='all')return true;
 return r.flags.some(f=>f.code===filter);
}
const api={validate,exportFlags,matches};if(typeof module!=='undefined')module.exports=api;else root.BAFlags=api;
})(globalThis);
