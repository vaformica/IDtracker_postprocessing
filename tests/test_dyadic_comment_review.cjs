const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
function boot(saved=null){const els={};let stored=saved;
const draw=new Proxy({},{get:()=>()=>{}});
class El{constructor(){this.children=[];this.options=[];this.value='';this.checked=false;this.style={};this.paused=true;this.currentTime=0;this.readyState=1;this.classList={toggle(){}}}append(...a){this.children.push(...a);this.options.push(...a)}replaceChildren(){this.children=[];this.options=[]}getContext(){return draw}getAttribute(k){return this[k]}setAttribute(k,v){this[k]=v}pause(){this.paused=true}play(){this.paused=false;return Promise.resolve()}load(){this.onloadedmetadata?.()}click(){this.onclick?.()}}
const document={getElementById:k=>els[k]??=new El(),createElement:()=>new El(),createTextNode:s=>s,querySelectorAll:()=>[],addEventListener(){}};
document.getElementById('filter').value='all';document.getElementById('mode').value='psc';document.getElementById('reviewer').value='VAF';document.getElementById('speed').value='.5';
const ctx=vm.createContext({document,localStorage:{getItem:()=>stored,setItem:(_,v)=>stored=v},console,Date,JSON,Number,Math,Error,Blob,URL:{createObjectURL:()=>'',revokeObjectURL(){}},setTimeout(){},confirm:()=>true});
vm.runInContext(html.split('<script>')[1].split('</script>')[0],ctx);return{els,run:s=>vm.runInContext(s,ctx),saved:()=>stored};}
const t=boot();assert.equal(t.run('SET.cases.length'),49);assert.equal(t.run('SET.source_rows'),48);assert.equal(t.run('SET.csv_distinct_runs'),10);
assert.equal(t.run('shownFrame'),1659);t.els.forward.onclick();assert.equal(t.run('shownFrame'),1660);t.els.back.onclick();assert.equal(t.run('shownFrame'),1659);
t.els.nextCase.onclick();assert.equal(t.run('exportData().annotations[0].complete'),false);
t.run("save({decision:'investigate',notes:'Look again <literal text>'})");assert.equal(t.run('exportData().annotations[1].decision'),'investigate');const r=boot(t.saved());assert.equal(r.run('state.decisions[SET.cases[1].id].notes'),'Look again <literal text>');
t.run('seek(-2)');assert.equal(t.run('shownFrame'),46);t.run('seek(999999)');assert.equal(t.run('shownFrame'),7245);
assert.throws(()=>t.run("validate({reviewer:'VAF',decisions:{wrong:{decision:'ignore',notes:'',category:''}}})"));
assert.throws(()=>t.run("validate({reviewer:'VAF',decisions:{[SET.cases[0].id]:{decision:'approved',notes:'',category:''}}})"));
t.els.clear.onclick();assert.equal(t.run('exportData().annotations[1].complete'),false);
assert.equal(t.run('SET.cases.filter(c=>c.reported_frame===null).length'),3);
assert.equal(t.run('SET.cases.find(c=>c.reported_frame===0).target'),170);
assert.equal(t.run('SET.cases.find(c=>c.reported_end>c.reported_frame).end'),3950);
console.log('PASS: source coverage, frame mapping, stepping/clamping, draft persistence, explicit decisions, invalid import rejection, blank/start/range cases.');
