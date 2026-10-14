const fs=require('fs'),vm=require('vm'),assert=require('assert');
const template=fs.readFileSync('ba_turtling_scoring_template.html','utf8');
assert(!/<video[^>]*\scontrols(?:\s|>)/.test(template));
assert(template.indexOf('id="seek"')>template.indexOf('</video>'));
assert(template.indexOf('class="transport"')<template.indexOf('class="card quick"'));
function boot(stored={}) {
 const clips=[{id:'clip_01',start:1000,frames:7200,fps:30},{id:'clip_02',start:9000,frames:7200,fps:30}];
 const page=template.replace('__SET__',JSON.stringify({id:'button-test'})).replace('__CLIPS__',JSON.stringify(clips)).replace('__MEDIA__','{"clip_01":"test1","clip_02":"test2"}').replace('__INITIAL_SCORES__','{}');
 const els={};const el=id=>els[id]??={value:id==='speed'?'1':id==='target'?'posture':'',currentTime:0,textContent:'',pause(){},play:async()=>{},click(){}};
 let downloaded;
 const box={document:{getElementById:el,createElement:()=>({click(){}})},localStorage:{getItem:k=>stored[k]??null,setItem:(k,v)=>stored[k]=v},Date,JSON,console,confirm:()=>true,setTimeout:()=>{},Blob:class{constructor(p){this.text=p.join('')}},URL:{createObjectURL:b=>{downloaded=JSON.parse(b.text);return 'test'},revokeObjectURL(){}}};
 vm.createContext(box);vm.runInContext(page.match(/<script>([\s\S]*?)<\/script>/)[1],box);
 return {el,stored,box,get:()=>downloaded,at:f=>{el('video').currentTime=(f-1000+.1)/30}};
}
(async()=>{
 const a=boot();a.el('reviewer').value='Test';
 assert(a.el('video').controls===false);assert(a.el('seek').max===7199);
 a.el('seek').oninput({target:{value:'7199'}});assert(a.el('video').currentTime>239.96);assert(a.el('time').textContent.includes('8199'));
 assert(a.el('posture_ranges').value==='');assert(a.el('flailing_ranges').value==='');
 a.el('back').onclick();assert(a.el('time').textContent.includes('8198'));
 a.el('seek').oninput({target:{value:'0'}});assert(a.el('time').textContent.includes('1000'));
 a.el('forward').onclick();assert(a.el('time').textContent.includes('1001'));
 a.at(1100);a.el('startBoth').onclick();assert(a.el('postureStart').disabled&&a.el('flailingStart').disabled);
 a.at(1200);a.el('flailingStop').onclick();assert(a.el('flailing_ranges').value==='1100-1200');assert(a.el('posture_ranges').value==='');
 a.at(1050);a.el('postureStop').onclick();assert(a.el('message').textContent.includes('at or after'));assert(a.el('postureStart').disabled);
 a.at(1250);a.el('startBoth').onclick(); // Preserve the already-open posture start.
 a.at(1300);a.el('flailingStop').onclick();assert(a.el('flailing_ranges').value==='1100-1200, 1250-1300');
 a.at(1400);a.el('postureStop').onclick();assert(a.el('posture_ranges').value==='1100-1400');
 a.at(1500);a.el('postureStart').onclick();a.el('postureToEnd').onclick();assert(a.el('posture_ranges').value==='1100-1400, 1500-8199');
 // Closed intervals survive another pending start and cancellation.
 a.at(1600);a.el('flailingStart').onclick();a.el('export').onclick();assert(a.get().annotations[0].complete===false);assert(a.get().scores.clip_01.pending_starts.flailing===1600);assert(a.get().scorer_version==='0.3.1');
 const b=boot(a.stored);assert(b.el('flailingActive').textContent.includes('1600'));b.el('flailingCancel').onclick();assert(b.el('flailing_ranges').value==='1100-1200, 1250-1300');
 b.el('export').onclick();assert(b.get().annotations[0].complete===true);
 // Navigate away and back with an open start; no truncation or auto-ending.
 b.at(1700);b.el('flailingStart').onclick();b.el('next').onclick();b.el('prev').onclick();assert(b.el('flailingActive').textContent.includes('1700'));
 const pendingExport=a.get();const c=boot();await c.el('import').onchange({target:{files:[{text:async()=>JSON.stringify(pendingExport)}]}});assert(c.el('flailingActive').textContent.includes('1600'));
 // Legacy storage migrates into a new namespace without changing the old entries.
 const old=JSON.stringify({reviewer:'Prior',clip_01:{posture:'none',flailing:'none',notes:'Retain me'}});const d=boot({'button-test:scorer-v2':old});
 d.el('prev').onclick();assert(d.el('notes').value==='Retain me');assert(d.stored['button-test:scorer-v2']===old);
 d.at(1800);d.el('startBoth').onclick();d.el('postureStop').onclick();d.el('flailingStop').onclick();d.el('export').onclick();assert(d.get().annotations[0].posture_intervals[0].first_global_frame===1800);assert(d.get().annotations[0].posture_intervals[0].last_global_frame===1800);
 console.log('PASS: combined/separate starts, independent stops, repeated bouts, inclusive endpoints, backwards-seek rejection, through-end, cancel, pending export/import/navigation/reload, legacy score migration.');
})().catch(e=>{console.error(e);process.exitCode=1});
