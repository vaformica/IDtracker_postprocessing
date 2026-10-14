"""Add a verified rerun packet and explicit lineage; never copy human approvals."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import ba_review_registry as registry
dbpath,packet,snapshot_path=sys.argv[1:]
db=registry.connect(dbpath)
before=db.execute('SELECT count(*) FROM reviews').fetchone()[0]
result=registry.register(db,packet)
cross=json.loads((Path(packet)/'RERUN_CROSSWALK.json').read_text())
assert result['dataset']==cross['new_dataset']
for r in cross['runs']:
 parents={v['dataset_sha256'] for v in r['prior_reviews']};assert len(parents)==1
 parent=parents.pop()
 if not db.execute('SELECT 1 FROM lineage WHERE parent_dataset=? AND parent_run=? AND child_dataset=? AND child_run=?',(parent,r['id'],result['dataset'],r['id'])).fetchone():
  registry.link_rerun(db,parent,r['id'],result['dataset'],r['id'],'VAF authorized 2026-10-14 rerun of Savannah revised TOML: '+r['source_toml']+'; source SHA256 '+r['source_sha256']+'; old comments retained, approval not inherited')
assert db.execute('SELECT count(*) FROM reviews').fetchone()[0]==before
assert db.execute('SELECT count(*) FROM reviews WHERE dataset=?',(result['dataset'],)).fetchone()[0]==0
registry.snapshot(db,snapshot_path)
print(json.dumps(dict(registered=result,prior_review_records_preserved=before,new_reviews=0,lineage_links=len(cross['runs'])),indent=2))
