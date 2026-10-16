const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');
// Fully synthetic: no private CSV, generated packet, media, or network required.
const start=100,end=130,count=end-start+1;
const frames=fn=>Array.from({length:count},fn);
const data={start,end,fps:30,raw:frames(()=>[[10,20],[40,50]]),held:frames(()=>[[10,20],[40,50]]),inferred:frames(()=>[false,false]),fungus:frames(()=>[0,0]),rawFungus:frames(()=>[0,0]),pairStates:[frames(()=>1)],rois:[],videoGeometry:{crop:[0,0,1280,920],rotation_cw:0,pad_x:0,pad_y:0,content_width:1280,content_height:920}};
const cases=[{reported_frame:110,reported_end:110,target:110,end:110,initial:105},{reported_frame:null,reported_end:null,target:start,end:start,initial:start},{reported_frame:0,reported_end:0,target:start,end:start,initial:start},{reported_frame:115,reported_end:120,target:115,end:120,initial:110}].map((c,i)=>({id:'synthetic_'+i,csv_row:i+2,run:'synthetic_run',reviewer:'TEST',original_frame:c.reported_frame===null?'':String(c.reported_frame),issue:'Synthetic comment',frame_note:'Synthetic frame mapping',beetle0:'A',beetle1:'B',categories:['General review'],snapshots:[],...c}));
const fixture={source_sha256:'synthetic-only',source_filename:'synthetic.csv',frame_basis:'global',source_rows:4,csv_distinct_runs:1,cases,videos:{synthetic_run:{data,media:'synthetic.mp4'}},source_url:'',slack_url:''};
const template=fs.readFileSync(path.join(__dirname,'..','dyadic_comment_review.html'),'utf8');
const html=template.replace('__REVIEW_DATA__',JSON.stringify(fixture));
function boot(saved=null, page=html){const els={};let stored=saved;
const draw=new Proxy({},{get:()=>()=>{}});
class El{constructor(){this.children=[];this.options=[];this.value='';this.checked=false;this.style={};this.paused=true;this.currentTime=0;this.readyState=1;this.classList={toggle(){}}}append(...a){this.children.push(...a);this.options.push(...a)}replaceChildren(){this.children=[];this.options=[]}getContext(){return draw}getAttribute(k){return this[k]}setAttribute(k,v){this[k]=v}pause(){this.paused=true}play(){this.paused=false;return Promise.resolve()}load(){this.onloadedmetadata?.()}click(){this.onclick?.()}}
const document={getElementById:k=>els[k]??=new El(),createElement:()=>new El(),createTextNode:s=>s,querySelectorAll:()=>[],addEventListener(){}};
document.getElementById('filter').value='all';document.getElementById('mode').value='psc';document.getElementById('reviewer').value='VAF';document.getElementById('speed').value='.5';
const ctx=vm.createContext({document,localStorage:{getItem:()=>stored,setItem:(_,v)=>stored=v},console,Date,JSON,Number,Math,Error,Blob,URL:{createObjectURL:()=>'',revokeObjectURL(){}},setTimeout(){},confirm:()=>true});
vm.runInContext(page.split('<script>')[1].split('</script>')[0],ctx);return{els,run:s=>vm.runInContext(s,ctx),saved:()=>stored};}
const t=boot();assert.equal(t.run('SET.cases.length'),4);assert.equal(t.run('SET.source_rows'),4);assert.equal(t.run('SET.csv_distinct_runs'),1);
assert.equal(t.run('shownFrame'),105);t.els.forward.onclick();assert.equal(t.run('shownFrame'),106);t.els.back.onclick();assert.equal(t.run('shownFrame'),105);
t.els.nextCase.onclick();assert.equal(t.run('exportData().annotations[0].complete'),false);
t.run("save({decision:'investigate',notes:'Look again <literal text>'})");assert.equal(t.run('exportData().annotations[1].decision'),'investigate');const r=boot(t.saved());assert.equal(r.run('state.decisions[SET.cases[1].id].notes'),'Look again <literal text>');
t.run('seek(-2)');assert.equal(t.run('shownFrame'),100);t.run('seek(999999)');assert.equal(t.run('shownFrame'),130);
assert.throws(()=>t.run("validate({reviewer:'VAF',decisions:{wrong:{decision:'ignore',notes:'',category:''}}})"));
assert.throws(()=>t.run("validate({reviewer:'VAF',decisions:{[SET.cases[0].id]:{decision:'approved',notes:'',category:''}}})"));
t.els.clear.onclick();assert.equal(t.run('exportData().annotations[1].complete'),false);
assert.equal(t.run('SET.cases.filter(c=>c.reported_frame===null).length'),1);
assert.equal(t.run('SET.cases.find(c=>c.reported_frame===0).target'),100);
assert.equal(t.run('SET.cases.find(c=>c.reported_end>c.reported_frame).end'),120);
console.log('PASS: source coverage, frame mapping, stepping/clamping, draft persistence, explicit decisions, invalid import rejection, blank/start/range cases.');

assert.equal(t.els.source.hidden,true);
const linked=html.replace('\"source_url\":\"\"','\"source_url\":\"https://example.invalid/source\"');
const withLink=boot(null,linked);assert.equal(withLink.els.source.href,'https://example.invalid/source');
