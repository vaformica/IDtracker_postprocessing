/* Attributed screening decisions, separate from posture labels and data exclusions. */
(function(root){'use strict';
const categories=['jumps','missing_gaps','possible_turtling','camera_light','wrong_object','injury','other'];
const statuses=['usable_skim','needs_review','recommend_exclusion'];
function validate(d,index){
 if(!d||d.schema!=='ba-combined-qc-v1'||d.dataset_sha256!==index.hash||typeof d.reviewer!=='string'||!d.reviewer.trim()||!Array.isArray(d.decisions))throw Error('Wrong dataset or missing reviewer.');
 const ids=new Map(index.runs.map(x=>[x.id,x])),seen=new Set();
 for(const r of d.decisions){const x=ids.get(r.run_id);if(!x||seen.has(r.run_id)||!statuses.includes(r.status)||!Array.isArray(r.errors)||r.errors.some(e=>!categories.includes(e))||new Set(r.errors).size!==r.errors.length||typeof r.notes!=='string'||typeof r.reviewer!=='string'||!r.reviewer.trim()||typeof r.at!=='string'||!Array.isArray(r.intervals)||!['trace_skim','trace_and_excerpt','trace_and_full_video'].includes(r.scope))throw Error('Invalid QC decision.');seen.add(r.run_id);
 if(r.rerun_idtracker!==undefined&&typeof r.rerun_idtracker!=='boolean')throw Error('Invalid rerun request.');
 if(r.status==='usable_skim'&&r.rerun_idtracker)throw Error('Rerun requests require closer review.');
 if(r.status!=='usable_skim'&&!r.errors.length&&!r.notes.trim()&&!r.rerun_idtracker)throw Error('Flagged runs need a reason.');
 if(r.status==='usable_skim'&&r.errors.length)throw Error('Resolve checked issues or choose Needs closer review.');
 if(r.turtling_intervals!==undefined&&!Array.isArray(r.turtling_intervals))throw Error('Invalid turtling intervals.');
 for(const t of [...r.intervals,...(r.turtling_intervals||[])])if(!Array.isArray(t)||t.length!==2||!Number.isInteger(t[0])||!Number.isInteger(t[1])||t[0]<x.start||t[1]>x.end||t[0]>t[1])throw Error('Interval outside run.');
 }
 if(d.drafts!==undefined){if(!d.drafts||typeof d.drafts!=='object'||Array.isArray(d.drafts))throw Error('Invalid drafts.');for(const [id,r] of Object.entries(d.drafts)){const x=ids.get(id);if(!x||!r||!Array.isArray(r.errors)||r.errors.some(e=>!categories.includes(e))||typeof r.notes!=='string'||!['trace_skim','trace_and_excerpt','trace_and_full_video'].includes(r.scope)||!Array.isArray(r.intervals)||(r.rerun_idtracker!==undefined&&typeof r.rerun_idtracker!=='boolean'))throw Error('Invalid draft.');for(const t of [...r.intervals,...(r.turtling_intervals||[])])if(!Array.isArray(t)||t.length!==2||!Number.isInteger(t[0])||!Number.isInteger(t[1])||t[0]<x.start||t[1]>x.end||t[0]>t[1])throw Error('Invalid draft interval.');for(const f of [r.pending,r.turtling_pending])if(f!=null&&(!Number.isInteger(f)||f<x.start||f>x.end))throw Error('Invalid draft start.');}}
 return d;
}
function csv(d){const quote=x=>'"'+String(x??'').replace(/"/g,'""')+'"';return [['run_id','source_label','source_video','rerun_idtracker','status','errors','scope','reviewer','at','intervals','turtling_intervals','notes'],...d.decisions.map(x=>[x.run_id,x.source_label,x.source_video,!!x.rerun_idtracker,x.status,x.errors.join(';'),x.scope,x.reviewer,x.at,JSON.stringify(x.intervals),JSON.stringify(x.turtling_intervals||[]),x.notes])].map(a=>a.map(quote).join(',')).join('\n');}
const api={validate,csv,categories,statuses};if(typeof module!=='undefined')module.exports=api;else root.BAHumanQC=api;
})(globalThis);
