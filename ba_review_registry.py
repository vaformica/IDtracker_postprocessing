"""Offline BA QC registry: one coordinator, immutable imports, version-bound reviews.

Python standard library only. Keep the live SQLite file on a local disk, not a
shared mount/sync folder. Publish closed SQLite backups and CSV/JSON snapshots.
"""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

VERSION = '1.0.1'
FLAGS = {'jumps','missing_gaps','possible_turtling','camera_light','wrong_object','injury','other'}
SCOPES = {'trace_skim','trace_and_excerpt','trace_and_full_video'}
STATUSES = {'usable_skim','needs_review','recommend_exclusion'}

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(x).hexdigest()
def read_index(packet):
    s=(Path(packet)/'COMBINED_INDEX.js').read_text()
    if not s.startswith('window.COMBINED_INDEX='): raise ValueError('Not a BA packet index')
    return json.loads(s.split('=',1)[1].strip().removesuffix(';'))

def connect(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30);db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS datasets(hash TEXT PRIMARY KEY,id TEXT NOT NULL,index_json TEXT NOT NULL,registered_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS runs(dataset TEXT,run_id TEXT,target_key TEXT NOT NULL,manifest_sha256 TEXT NOT NULL,manifest_json TEXT NOT NULL,PRIMARY KEY(dataset,run_id),FOREIGN KEY(dataset) REFERENCES datasets(hash));
    CREATE TABLE IF NOT EXISTS imports(sha256 TEXT PRIMARY KEY,filename TEXT NOT NULL,received_at TEXT NOT NULL,raw BLOB NOT NULL,dataset TEXT NOT NULL REFERENCES datasets(hash));
    CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,dataset TEXT NOT NULL,run_id TEXT NOT NULL,reviewer TEXT NOT NULL,at TEXT NOT NULL,status TEXT NOT NULL,scope TEXT NOT NULL,notes TEXT NOT NULL,rerun INTEGER NOT NULL,override INTEGER NOT NULL,decision_json TEXT NOT NULL,FOREIGN KEY(dataset,run_id) REFERENCES runs(dataset,run_id));
    CREATE TABLE IF NOT EXISTS review_imports(review_id TEXT REFERENCES reviews(id),import_sha256 TEXT REFERENCES imports(sha256),role TEXT NOT NULL,PRIMARY KEY(review_id,import_sha256,role));
    CREATE TABLE IF NOT EXISTS flags(review_id TEXT REFERENCES reviews(id),flag TEXT NOT NULL,PRIMARY KEY(review_id,flag));
    CREATE TABLE IF NOT EXISTS bouts(review_id TEXT REFERENCES reviews(id),kind TEXT,start INTEGER,end INTEGER,PRIMARY KEY(review_id,kind,start,end));
    CREATE TABLE IF NOT EXISTS supersessions(previous TEXT REFERENCES reviews(id),next TEXT REFERENCES reviews(id),import_sha256 TEXT REFERENCES imports(sha256),PRIMARY KEY(previous,next));
    CREATE TABLE IF NOT EXISTS lineage(parent_dataset TEXT,parent_run TEXT,child_dataset TEXT,child_run TEXT,reason TEXT NOT NULL,recorded_at TEXT NOT NULL,PRIMARY KEY(parent_dataset,parent_run,child_dataset,child_run),FOREIGN KEY(parent_dataset,parent_run) REFERENCES runs(dataset,run_id),FOREIGN KEY(child_dataset,child_run) REFERENCES runs(dataset,run_id));
    CREATE VIEW IF NOT EXISTS current_reviews AS SELECT r.* FROM reviews r WHERE NOT EXISTS (SELECT 1 FROM supersessions s WHERE s.previous=r.id);
    ''')
    return db

def register(db,packet):
    packet=Path(packet);index=read_index(packet);records=[];hashes=[]
    for row in index['runs']:
        rid=row['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+',rid):raise ValueError('Invalid run ID')
        raw=(packet/'runs'/rid/'MANIFEST.json').read_bytes();m=json.loads(raw)
        source=m['source'];rules=m['rules']
        if rules.get('collection')!='BA' or rules.get('number_of_animals')!=1:raise ValueError('BA single animal only')
        # A locator for reconciliation, not proof two different files are one animal.
        target=digest(canonical({'source_toml':source['source_toml'],'video':source['video'],'roi':source['roi']}).encode())
        hashes.append((rid,digest(raw)));records.append((index['hash'],rid,target,digest(raw),canonical(m)))
    if digest(json.dumps(hashes).encode())!=index['hash']:raise ValueError('Packet manifest fingerprint mismatch')
    with db:
        old=db.execute('SELECT index_json FROM datasets WHERE hash=?',(index['hash'],)).fetchone()
        if old and old[0]!=canonical(index):raise ValueError('Dataset identity collision')
        db.execute('INSERT OR IGNORE INTO datasets VALUES(?,?,?,?)',(index['hash'],index['id'],canonical(index),now()))
        db.executemany('INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?)',records)
    return {'dataset':index['hash'],'runs':len(records),'artifact_validation':'manifest fingerprint checked; media bytes not rehashed'}

def validate_decision(d,index):
    runs={r['id']:r for r in index['runs']};r=runs.get(d.get('run_id'))
    if not r or d.get('status') not in STATUSES or d.get('scope') not in SCOPES:raise ValueError('Unknown run/status/scope')
    if not isinstance(d.get('reviewer'),str) or not d['reviewer'].strip() or not isinstance(d.get('notes'),str):raise ValueError('Missing reviewer/notes')
    datetime.fromisoformat(d['at'].replace('Z','+00:00'))
    flags=d.get('errors')
    if not isinstance(flags,list) or any(f not in FLAGS for f in flags) or len(set(flags))!=len(flags):raise ValueError('Invalid concern flags')
    if 'possible_flags' in d and d['possible_flags']!=flags:raise ValueError('Inconsistent possible flags')
    for key in ('rerun_idtracker','movement_override'):
        if key in d and not isinstance(d[key],bool):raise ValueError('Invalid boolean')
    if d.get('movement_override') and (d['status']!='usable_skim' or d.get('rerun_idtracker') or d.get('effective_movement_status')!='HUMAN_OVERRIDE_USE_STRICT_TRACK' or d.get('review_does_not_clear_analysis_hold') is not False):raise ValueError('Conflicting override')
    if d['status']=='usable_skim' and d.get('rerun_idtracker'):raise ValueError('Rerun request requires closer review')
    for key in ('intervals','turtling_intervals'):
        intervals=d.get(key,[])
        if not isinstance(intervals,list):raise ValueError('Invalid intervals')
        for a in intervals:
            if not isinstance(a,list) or len(a)!=2 or any(type(f)!=int for f in a) or not r['start']<=a[0]<=a[1]<=r['end']:raise ValueError('Out of window bout')
    # Percentages are reported estimates; raw JSON preserved, no biological claims.
    t=d.get('turtling_summary')
    if t is not None:
        if not isinstance(t,dict) or t.get('denominator_frames')!=r['end']-r['start']+1:raise ValueError('Wrong percentage denominator')
        for key in ('estimated_percent','human_marked_percent','automatic_candidate_percent'):
            value=t.get(key)
            if value is not None and (type(value) not in (int,float) or not 0<=value<=100):raise ValueError('Invalid percentage')

def review_id(dataset,d):
    # UI summaries/cutoffs may be recalculated in later exports of the same save.
    # Keep both complete payloads, linking them only via explicit same-save identity.
    identity={k:v for k,v in d.items() if k!='turtling_summary'}
    return digest(canonical([dataset,identity]).encode())

def import_scores(db,path):
    raw=Path(path).read_bytes();sha=digest(raw)
    if db.execute('SELECT 1 FROM imports WHERE sha256=?',(sha,)).fetchone():return {'duplicate':True,'sha256':sha}
    doc=json.loads(raw);dataset=doc.get('dataset_sha256')
    row=db.execute('SELECT index_json FROM datasets WHERE hash=?',(dataset,)).fetchone()
    if doc.get('schema')!='ba-combined-qc-v1' or not row:raise ValueError('Unknown dataset/schema; register packet first')
    index=json.loads(row[0]);decisions=doc.get('decisions')
    if not isinstance(decisions,list):raise ValueError('Missing decisions')
    ids=[d.get('run_id') for d in decisions]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate current run decisions')
    entries=[(d,'current') for d in decisions];links=[]
    # Explicit saved previous/next only; import conflicts and drafts are archived,
    # never silently made final reviews. Entire original file is in imports.raw.
    for h in doc.get('history',[]):
        if not isinstance(h,dict) or h.get('kind') or not isinstance(h.get('next'),dict):continue
        entries.append((h['next'],'history'))
        if isinstance(h.get('previous'),dict):entries.append((h['previous'],'history'));links.append((h['previous'],h['next']))
    for d,_ in entries:validate_decision(d,index)
    for a,b in links:
        if a['run_id']!=b['run_id'] or a['reviewer']!=b['reviewer']:
            # Another reviewer is a second opinion, never an implicit supersession.
            continue
        if datetime.fromisoformat(a['at'].replace('Z','+00:00'))>=datetime.fromisoformat(b['at'].replace('Z','+00:00')):raise ValueError('Non-forward review history')
    with db:
        db.execute('INSERT INTO imports VALUES(?,?,?,?,?)',(sha,Path(path).name,now(),raw,dataset))
        for d,role in entries:
            rid=review_id(dataset,d)
            db.execute('INSERT OR IGNORE INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,dataset,d['run_id'],d['reviewer'],d['at'],d['status'],d['scope'],d['notes'],int(d.get('rerun_idtracker',False)),int(d.get('movement_override',False)),canonical(d)))
            db.execute('INSERT OR IGNORE INTO review_imports VALUES(?,?,?)',(rid,sha,role))
            db.executemany('INSERT OR IGNORE INTO flags VALUES(?,?)',[(rid,f) for f in d['errors']])
            for key,kind in [('intervals','issue'),('turtling_intervals','possible_turtling')]:
                db.executemany('INSERT OR IGNORE INTO bouts VALUES(?,?,?,?)',[(rid,kind,*b) for b in d.get(key,[])])
        for a,b in links:
            if a['reviewer']==b['reviewer']:
                db.execute('INSERT OR IGNORE INTO supersessions VALUES(?,?,?)',(review_id(dataset,a),review_id(dataset,b),sha))
    return {'duplicate':False,'sha256':sha,'current_decisions_in_file':len(decisions),'review_records_including_history':len(entries),'drafts_archived_only':len(doc.get('drafts',{}))}

def link_rerun(db,parent_dataset,parent_run,child_dataset,child_run,reason):
    if not reason.strip() or parent_dataset==child_dataset:raise ValueError('Need a new dataset and explicit lineage reason')
    for ds,rid in [(parent_dataset,parent_run),(child_dataset,child_run)]:
        if not db.execute('SELECT 1 FROM runs WHERE dataset=? AND run_id=?',(ds,rid)).fetchone():raise ValueError('Register both versions first')
    # Links never copy approvals. Cross-target links are explicit and justified.
    with db:db.execute('INSERT INTO lineage VALUES(?,?,?,?,?,?)',(parent_dataset,parent_run,child_dataset,child_run,reason,now()))

def snapshot(db,out,cutoff=15):
    if not 0<=cutoff<=100:raise ValueError('Invalid cutoff')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    backup=sqlite3.connect(out/'reviews.sqlite3');db.backup(backup);backup.close()
    rows=[]
    for r in db.execute('SELECT * FROM current_reviews ORDER BY dataset,run_id,reviewer,at'):
        d=json.loads(r['decision_json']);m=json.loads(db.execute('SELECT manifest_json FROM runs WHERE dataset=? AND run_id=?',(r['dataset'],r['run_id'])).fetchone()[0]);t=d.get('turtling_summary') or {};pct=t.get('estimated_percent')
        # Multiple records or reviewer opinions are visible; no automatic consensus.
        peers=db.execute('SELECT count(*) FROM current_reviews WHERE dataset=? AND run_id=?',(r['dataset'],r['run_id'])).fetchone()[0]
        rows.append(dict(review_id=r['id'],dataset_sha256=r['dataset'],run_id=r['run_id'],source_video=m['source']['video'],source_toml=m['source']['source_toml'],reviewer=r['reviewer'],reviewed_at=r['at'],review_scope=r['scope'],review_status=r['status'],analysis_approved=r['status']=='usable_skim',possible_flags=';'.join(d['errors']),review_comments=r['notes'],rerun_requested=bool(r['rerun']),movement_override=bool(r['override']),movement_status=d.get('effective_movement_status',d.get('movement_status','NOT_ASSESSED')),estimated_turtled_percent=pct,human_marked_percent=t.get('human_marked_percent'),possible_turtling_bouts=json.dumps(d.get('turtling_intervals',[])),issue_intervals=json.dumps(d.get('intervals',[])),suggest_removal=pct>cutoff if pct is not None else None,cutoff_percent=cutoff,current_opinions=peers,requires_reconciliation=peers>1))
    fields=['review_id','dataset_sha256','run_id','source_video','source_toml','reviewer','reviewed_at','review_scope','review_status','analysis_approved','possible_flags','review_comments','rerun_requested','movement_override','movement_status','estimated_turtled_percent','human_marked_percent','possible_turtling_bouts','issue_intervals','suggest_removal','cutoff_percent','current_opinions','requires_reconciliation']
    with (out/'review_annotations.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    work=[]
    for r in db.execute('SELECT * FROM runs ORDER BY dataset,run_id'):
        opinions=[x for x in rows if x['dataset_sha256']==r['dataset'] and x['run_id']==r['run_id']]
        work.append({'dataset_sha256':r['dataset'],'run_id':r['run_id'],'target_locator_key':r['target_key'],'source':json.loads(r['manifest_json'])['source'],'review_status':'UNREVIEWED' if not opinions else 'MULTIPLE_OPINIONS' if len(opinions)>1 else {'usable_skim':'HUMAN_APPROVED','needs_review':'NEEDS_REVIEW','recommend_exclusion':'RECOMMEND_EXCLUSION'}[opinions[0]['review_status']],'reviews':opinions,'rerun_requested':any(x['rerun_requested'] for x in opinions),'automatic_submission':False})
    (out/'workflow_reviews.json').write_text(json.dumps({'schema':'ba-qc-workflow-snapshot-v1','created_at':now(),'cutoff_percent':cutoff,'runs':work,'lineage':[dict(r) for r in db.execute('SELECT * FROM lineage')]},indent=2))
    all_reviews=[dict(r) for r in db.execute('SELECT * FROM reviews ORDER BY dataset,run_id,at')]
    (out/'review_history.json').write_text(json.dumps(all_reviews,indent=2))
    context={}
    for run in db.execute('SELECT * FROM runs'):
        prior=[]
        for r in db.execute('SELECT reviews.* FROM reviews JOIN runs USING(dataset,run_id) WHERE runs.target_key=? ORDER BY reviews.at',(run['target_key'],)):
            prior.append({'reviewer':r['reviewer'],'at':r['at'],'status':r['status'],'scope':r['scope'],'notes':r['notes'],'flags':json.loads(r['decision_json']).get('errors',[]),'reviewed_dataset':r['dataset'],'same_dataset':r['dataset']==run['dataset']})
        context[run['dataset']+':'+run['run_id']]=prior
    (out/'REVIEW_HISTORY.js').write_text('window.QC_REGISTRY_HISTORY='+json.dumps(context,separators=(',',':')).replace('<','\\u003c')+';')
    files={p.name:digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}
    receipt={'schema':'ba-qc-registry-snapshot-v1','created_at':now(),'version':VERSION,'counts':{t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['datasets','runs','imports','reviews','bouts','flags','lineage']},'files':files,'scope':'Review annotations only; no metrics regenerated, no reruns submitted'}
    (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',required=True);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('register');s.add_argument('packet')
    s=sub.add_parser('import');s.add_argument('scores',nargs='+')
    s=sub.add_parser('snapshot');s.add_argument('out');s.add_argument('--cutoff',type=float,default=15)
    s=sub.add_parser('link-rerun');s.add_argument('parent_dataset');s.add_argument('parent_run');s.add_argument('child_dataset');s.add_argument('child_run');s.add_argument('--reason',required=True)
    a=p.parse_args();db=connect(a.db)
    try:
        if a.command=='register':result=register(db,a.packet)
        elif a.command=='import':result=[import_scores(db,f) for f in a.scores]
        elif a.command=='snapshot':result=snapshot(db,a.out,a.cutoff)
        else:link_rerun(db,a.parent_dataset,a.parent_run,a.child_dataset,a.child_run,a.reason);result={'linked':True,'approvals_copied':False}
        print(json.dumps(result,indent=2))
    finally:db.close()
if __name__=='__main__':main()
