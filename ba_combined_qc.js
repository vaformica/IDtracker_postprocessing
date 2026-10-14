/* Attributed screening decisions, separate from posture labels and data exclusions. */
(function(root){'use strict';
const categories=['jumps','missing_gaps','possible_turtling','camera_light','wrong_object','injury','other'];
const statuses=['usable_skim','needs_review','recommend_exclusion'];
function turtlingSummary(start,end,intervals,mask,states,cutoff=null){
 const n=end-start+1,human=new Uint8Array(n);
 for(const [a,b] of intervals||[])for(let f=Math.max(start,a);f<=Math.min(end,b);f++)human[f-start]=1;
 const available=Array.isArray(mask)&&mask.length===n;
 let h=0,a=0,u=0,assessed=0;
 for(let i=0;i<n;i++){h+=human[i];const predicted=available&&mask[i]===true;a+=predicted?1:0;u+=(human[i]||predicted)?1:0;if(states?.[i]==='candidate_detected'||states?.[i]==='no_candidate_detected')assessed++;}
 return {denominator_frames:n,human_marked_frames:h,human_marked_percent:100*h/n,automatic_candidate_frames:available?a:null,automatic_candidate_percent:available?100*a/n:null,automatic_assessed_frames:available?assessed:null,combined_flagged_frames:u,estimated_percent:100*u/n,estimate_basis:available?'union_of_automatic_candidates_and_human_marks':'human_marks_only',cutoff_percent:cutoff,cutoff_reached:cutoff==null?null:100*u/n>cutoff};
}
function validate(d,index){
 if(!d||d.schema!=='ba-combined-qc-v1'||d.dataset_sha256!==index.hash||typeof d.reviewer!=='string'||!d.reviewer.trim()||!Array.isArray(d.decisions))throw Error('Wrong dataset or missing reviewer.');
 const ids=new Map(index.runs.map(x=>[x.id,x])),seen=new Set();
 for(const r of d.decisions){const x=ids.get(r.run_id);if(!x||seen.has(r.run_id)||!statuses.includes(r.status)||!Array.isArray(r.errors)||r.errors.some(e=>!categories.includes(e))||new Set(r.errors).size!==r.errors.length||typeof r.notes!=='string'||typeof r.reviewer!=='string'||!r.reviewer.trim()||typeof r.at!=='string'||!Array.isArray(r.intervals)||!['trace_skim','trace_and_excerpt','trace_and_full_video'].includes(r.scope))throw Error('Invalid QC decision.');seen.add(r.run_id);
 if(r.movement_override!==undefined&&typeof r.movement_override!=='boolean')throw Error('Invalid movement override.');
 if(r.movement_override&&(r.status!=='usable_skim'||r.rerun_idtracker||r.effective_movement_status!=='HUMAN_OVERRIDE_USE_STRICT_TRACK'||r.review_does_not_clear_analysis_hold!==false))throw Error('Save a movement override with Looks usable, without a rerun request.');
 if(r.rerun_idtracker!==undefined&&typeof r.rerun_idtracker!=='boolean')throw Error('Invalid rerun request.');
 if(r.status==='usable_skim'&&r.rerun_idtracker)throw Error('Rerun requests require closer review.');
 if(r.status!=='usable_skim'&&!r.errors.length&&!r.notes.trim()&&!r.rerun_idtracker)throw Error('Flagged runs need a reason.');
 if(r.possible_flags!==undefined&&(!Array.isArray(r.possible_flags)||JSON.stringify(r.possible_flags)!==JSON.stringify(r.errors)))throw Error('Possible flags must match selected concerns.');
 if(r.turtling_intervals!==undefined&&!Array.isArray(r.turtling_intervals))throw Error('Invalid turtling intervals.');
 for(const t of [...r.intervals,...(r.turtling_intervals||[])])if(!Array.isArray(t)||t.length!==2||!Number.isInteger(t[0])||!Number.isInteger(t[1])||t[0]<x.start||t[1]>x.end||t[0]>t[1])throw Error('Interval outside run.');
 }
 if(d.drafts!==undefined){if(!d.drafts||typeof d.drafts!=='object'||Array.isArray(d.drafts))throw Error('Invalid drafts.');for(const [id,r] of Object.entries(d.drafts)){const x=ids.get(id);if(!x||!r||!Array.isArray(r.errors)||r.errors.some(e=>!categories.includes(e))||typeof r.notes!=='string'||!['trace_skim','trace_and_excerpt','trace_and_full_video'].includes(r.scope)||!Array.isArray(r.intervals)||(r.rerun_idtracker!==undefined&&typeof r.rerun_idtracker!=='boolean'))throw Error('Invalid draft.');if(r.movement_override!==undefined&&typeof r.movement_override!=='boolean')throw Error('Invalid draft override.');for(const t of [...r.intervals,...(r.turtling_intervals||[])])if(!Array.isArray(t)||t.length!==2||!Number.isInteger(t[0])||!Number.isInteger(t[1])||t[0]<x.start||t[1]>x.end||t[0]>t[1])throw Error('Invalid draft interval.');for(const f of [r.pending,r.turtling_pending])if(f!=null&&(!Number.isInteger(f)||f<x.start||f>x.end))throw Error('Invalid draft start.');}}
 return d;
}
function csv(d){const quote=x=>'"'+String(x??'').replace(/"/g,'""')+'"';return [['run_id','source_label','source_video','rerun_idtracker','status','errors','scope','reviewer','at','intervals','turtling_intervals','notes','movement_status','automatic_jump_pairs','review_does_not_clear_analysis_hold','movement_override','effective_movement_status','analysis_approved','possible_flags','turtling_estimated_percent','turtling_human_percent','turtling_auto_percent','turtling_denominator_frames','turtling_cutoff_percent','turtling_cutoff_reached'],...d.decisions.map(x=>[x.run_id,x.source_label,x.source_video,!!x.rerun_idtracker,x.status,x.errors.join(';'),x.scope,x.reviewer,x.at,JSON.stringify(x.intervals),JSON.stringify(x.turtling_intervals||[]),x.notes,x.movement_status,JSON.stringify(x.automatic_jump_pairs||[]),x.review_does_not_clear_analysis_hold??'',!!x.movement_override,x.effective_movement_status,x.status==='usable_skim',(x.possible_flags||x.errors).join(';'),x.turtling_summary?.estimated_percent,x.turtling_summary?.human_marked_percent,x.turtling_summary?.automatic_candidate_percent,x.turtling_summary?.denominator_frames,x.turtling_summary?.cutoff_percent,x.turtling_summary?.cutoff_reached])].map(a=>a.map(quote).join(',')).join('\n');}
const api={turtlingSummary,validate,csv,categories,statuses};if(typeof module!=='undefined')module.exports=api;else root.BAHumanQC=api;
})(globalThis);
