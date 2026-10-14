import json, tempfile, unittest, csv
from pathlib import Path
import ba_review_registry as R

class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=R.connect(self.root/'db.sqlite')
  self.index={'hash':'abc','id':'test','runs':[{'id':'r1','start':100,'end':199}]}
  self.m={'source':{'video':'video','source_toml':'toml'}}
  self.db.execute('INSERT INTO datasets VALUES(?,?,?,?)',('abc','test',R.canonical(self.index),R.now()))
  self.db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',('abc','r1','target','manifest',R.canonical(self.m)));self.db.commit()
  self.d=dict(run_id='r1',reviewer='VAF',at='2026-10-13T10:00:00Z',status='usable_skim',scope='trace_skim',notes='Looks fine with a gap',errors=['missing_gaps'],intervals=[],turtling_intervals=[[110,125]])
 def tearDown(self):self.db.close();self.tmp.cleanup()
 def export(self,ds=None,history=None,hash='abc',drafts=None):
  p=self.root/('scores'+str(len(list(self.root.glob('scores*'))))+'.json');p.write_text(json.dumps(dict(schema='ba-combined-qc-v1',dataset_sha256=hash,decisions=ds if ds is not None else [self.d],history=history or [],drafts=drafts or {})));return p
 def count(self,table):return self.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
 def test_idempotence_flags_bouts_and_original(self):
  p=self.export();R.import_scores(self.db,p);self.assertTrue(R.import_scores(self.db,p)['duplicate']);R.import_scores(self.db,self.export())
  self.assertEqual(self.count('reviews'),1);self.assertEqual(self.count('bouts'),1);self.assertEqual(self.count('flags'),1)
  out=self.root/'snapshot';R.snapshot(self.db,out);rows=list(csv.DictReader((out/'review_annotations.csv').read_text().splitlines()));self.assertEqual(rows[0]['possible_flags'],'missing_gaps');self.assertEqual(rows[0]['analysis_approved'],'True')
 def test_revisions_and_other_reviewer_preserved(self):
  new={**self.d,'at':'2026-10-13T11:00:00Z','notes':'Changed opinion','status':'needs_review'}
  R.import_scores(self.db,self.export([new],[{'previous':self.d,'next':new}]))
  other={**new,'reviewer':'Hannah','status':'usable_skim'};R.import_scores(self.db,self.export([other]))
  self.assertEqual(self.count('reviews'),3);self.assertEqual(self.count('current_reviews'),2)
 def test_wrong_dataset_and_malformed_atomic(self):
  with self.assertRaises(ValueError):R.import_scores(self.db,self.export(hash='wrong'))
  with self.assertRaises(ValueError):R.import_scores(self.db,self.export([{**self.d,'turtling_intervals':[[99,120]]}]))
  self.assertEqual(self.count('imports'),0)
 def test_exclusion_distinct_from_needs_review(self):
  self.d['status']='recommend_exclusion';R.import_scores(self.db,self.export());R.snapshot(self.db,self.root/'snapshot')
  data=json.loads((self.root/'snapshot/workflow_reviews.json').read_text());self.assertEqual(data['runs'][0]['review_status'],'RECOMMEND_EXCLUSION')
 def test_drafts_not_approvals(self):
  R.import_scores(self.db,self.export([],drafts={'r1':self.d}));self.assertEqual(self.count('reviews'),0)
 def test_new_attempt_does_not_inherit_approval(self):
  R.import_scores(self.db,self.export());self.db.execute('INSERT INTO datasets VALUES(?,?,?,?)',('def','new',R.canonical({**self.index,'hash':'def'}),R.now()));self.db.execute('INSERT INTO runs VALUES(?,?,?,?,?)',('def','r1','target','newmanifest',R.canonical(self.m)));self.db.commit()
  R.link_rerun(self.db,'abc','r1','def','r1','IDTracker rerun from attributed request')
  R.snapshot(self.db,self.root/'snapshot');d=json.loads((self.root/'snapshot/workflow_reviews.json').read_text());self.assertEqual(next(r for r in d['runs'] if r['dataset_sha256']=='def')['review_status'],'UNREVIEWED')
 def test_cutoff_exact_fifteen_not_removed_and_changes_repeat_safe(self):
  self.d['turtling_summary']={'denominator_frames':100,'estimated_percent':15,'human_marked_percent':15,'automatic_candidate_percent':0,'cutoff_percent':15}
  R.import_scores(self.db,self.export());self.d['turtling_summary']['cutoff_percent']=20;R.import_scores(self.db,self.export());self.assertEqual(self.count('reviews'),1)
  R.snapshot(self.db,self.root/'snapshot');row=next(csv.DictReader((self.root/'snapshot/review_annotations.csv').read_text().splitlines()));self.assertEqual(row['suggest_removal'],'False')
if __name__=='__main__':unittest.main()
