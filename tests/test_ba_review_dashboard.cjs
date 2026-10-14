// Exercise actual delivered scripts against a minimal DOM; not a browser rendering test.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const page=fs.readFileSync(process.argv[2],'utf8'),scripts=[...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]);
class Element{constructor(){this.value='';this.textContent='';this.children=[];this.checked=false;this.nodes={}}append(x){this.children.push(x)}replaceChildren(){this.children=[]}addEventListener(name,fn){this['on'+name]=fn}click(){if(this.onclick)this.onclick()}querySelector(s){if(!this.nodes[s])this.nodes[s]=new Element();return this.nodes[s]}}
const ids=Object.fromEntries(['summary','reviewer','message','rules','filter','sort','count','rows','search','download','import'].map(k=>[k,new Element()]));ids.filter.value='all';ids.sort.value='priority';ids.reviewer.value='VAF';let blobText='';const storage=new Map();
const context={console,structuredClone,document:{getElementById:id=>ids[id],createElement:()=>new Element()},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},Blob:class{constructor(parts){blobText=parts.join('')}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},setTimeout:()=>{},confirm:()=>true};vm.createContext(context);for(const s of scripts)vm.runInContext(s,context);
assert.equal(ids.rows.children.length,121);assert.match(ids.summary.textContent,/29 high priority/);
ids.filter.value='high';ids.filter.onchange();assert.equal(ids.rows.children.length,29);
ids.filter.value='MISSING_TRACKING';ids.filter.onchange();assert.equal(ids.rows.children.length,36);
ids.filter.value='all';ids.search.value='fresh_06';ids.search.oninput();assert.equal(ids.rows.children.length,1);
let row=ids.rows.children[0];row.querySelector('.request').checked=true;row.querySelector('.reasonSelect').value='injury';row.querySelector('.notes').value='Review gait <do not treat as markup>';row.querySelector('.request').onchange();
ids.search.value='';ids.filter.value='manual';ids.filter.onchange();assert.equal(ids.rows.children.length,1);assert.match(ids.rows.children[0].innerHTML,/&lt;do not treat as markup&gt;/);
ids.download.onclick();let data=JSON.parse(blobText);assert.equal(data.flags.length,1);assert.equal(data.flags[0].run_id,'fresh_06');assert.equal(data.flags[0].reason,'injury');assert.equal(data.flags[0].requested,true);assert.equal(data.reviewer,'VAF');assert.match(data.scope,/no approval/);
ids.filter.value='all';ids.sort.value='missing';ids.sort.onchange();assert.equal(ids.rows.children.length,121);assert(storage.size===1);
console.log('Dashboard script checks passed: 121 rows, priority/reason filters, search, manual flag, escaped notes, export and sort. Browser rendering not exercised.');
