const fs=require('fs'),vm=require('vm'),assert=require('assert');
let page=fs.readFileSync('ba_turtling_scoring_template.html','utf8');
page=page.replace('__SET__',JSON.stringify({id:'test-set',sha:'abc'})).replace('__CLIPS__',JSON.stringify([{id:'clip_01',start:1000,frames:480,fps:30},{id:'clip_02',start:3000,frames:360,fps:30}])).replace('__MEDIA__','{"clip_01":"data:video/mp4;base64,AA==","clip_02":"data:video/mp4;base64,AA=="}');
page=page.replace('__INITIAL_SCORES__','{}');
const elements={};function el(id){return elements[id]??={value:id==='speed'?'1':id==='target'?'posture':'',currentTime:0,paused:true,textContent:'',pause(){this.paused=true},play:async()=>{},click:()=>{}}}
let downloaded;const sandbox={document:{getElementById:el,createElement:()=>({click:()=>{}})},localStorage:{getItem:()=>null,setItem:()=>{}},Date,JSON,console,confirm:()=>true,setTimeout:()=>{},Blob:class{constructor(parts){this.text=parts.join('')}},URL:{createObjectURL:b=>{downloaded=JSON.parse(b.text);return 'blob:test'},revokeObjectURL:()=>{}}};vm.createContext(sandbox);vm.runInContext(page.match(/<script>([\s\S]*?)<\/script>/)[1],sandbox);
assert(el('title').textContent.includes('Clip 1 of 2'));
el('reviewer').value='Test';el('posture').value='intervals';el('posture_ranges').value='1101-1479';el('flailing').value='none';vm.runInContext('save()',sandbox);assert(el('progress').textContent.startsWith('1 / 2 complete'));
el('video').currentTime=101.1/30;el('markStart').onclick();assert(el('rangeStart').value===1101);
el('next').onclick();el('posture').value='throughout';el('flailing').value='uncertain';el('export').onclick();assert(downloaded.completed_clips===2);assert(downloaded.annotations[0].posture_intervals[0].first_global_frame===1101);assert(downloaded.annotations[1].posture_intervals[0].last_global_frame===3359);assert(downloaded.annotations[1].decisions.flailing==='uncertain');
el('posture').value='intervals';el('posture_ranges').value='2999-3359';vm.runInContext('save()',sandbox);assert(el('progress').textContent.startsWith('1 / 2 complete'));
// Last-clip select-change saves immediately; no Next navigation required.
el('posture').value='none';el('posture_ranges').value='';el('flailing').value='none';el('posture').onchange();
assert(el('saveFeedback').textContent.includes('You can download now; Next is not required.'));
assert(el('next').textContent==='Finish & download');assert(!el('next').disabled);
el('next').onclick();assert(downloaded.completed_clips===2);assert(downloaded.annotations[1].decisions.posture==='none');
// A malformed earlier interval must identify the earlier clip, not blame the last clip.
el('prev').onclick();el('posture_ranges').value='1101';el('saveClip').onclick();
assert(el('saveFeedback').textContent.includes('BOTH start and end'));el('next').onclick();
assert(el('progress').textContent.includes('clip 01'));el('downloadTop').onclick();
assert(downloaded.completed_clips===1);assert(downloaded.scores.clip_01.posture_ranges==='1101');
assert(downloaded.annotations[1].complete===true);
console.log('PASS: frame marking, per-clip persistence, interval bounds, uncertainty, export, completion counts.');
