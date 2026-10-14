const assert=require('assert'),Q=require('../ba_human_qc.js');const index={hash:'abc',runs:[{id:'r1',start:100,end:200}]};
const good=()=>({schema:'ba-human-qc-v1',dataset_sha256:'abc',reviewer:'VAF',decisions:[{run_id:'r1',status:'needs_review',errors:['missing_gaps'],notes:'Check corner',scope:'trace_skim',intervals:[[110,120]],reviewer:'VAF',at:'2026-10-13T00:00:00Z'}]});
Q.validate(good(),index);
for(const change of [d=>d.dataset_sha256='wrong',d=>d.decisions.push(d.decisions[0]),d=>d.decisions[0].intervals=[[90,120]],d=>d.decisions[0].errors=['unknown'],d=>d.decisions[0].reviewer='',d=>{d.decisions[0].errors=[];d.decisions[0].notes=''},d=>d.decisions[0].status='usable_skim']){const d=good();change(d);assert.throws(()=>Q.validate(d,index))}
const d=good();d.decisions[0].status='recommend_exclusion';Q.validate(d,index);d.decisions[0].notes='comma, quote " and\nnewline';assert(Q.csv(d).includes('"comma, quote "" and\nnewline"'));assert.equal(Q.validate({...good(),decisions:[]},index).decisions.length,0);
console.log('10 schema and export checks passed. Empty decisions remain unreviewed; exclusions remain recommendations.');
